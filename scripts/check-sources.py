#!/usr/bin/env python3
"""
官方來源檢查：抓取 sources/official-sources.json 列出的官方文件，與上次記錄比對，
列出有變動的來源與受影響的 reference / data。

用法:
    python scripts/check-sources.py                   # 檢查全部，印出報告
    python scripts/check-sources.py --provider ecpay  # 只檢查某家
    python scripts/check-sources.py --skill payment   # 只檢查某個 skill 用到的來源
    python scripts/check-sources.py --update          # 檢查後把目前版本記為基準（寫入 sources/state.json）
    python scripts/check-sources.py --validate        # 只檢查清單格式與 covers 路徑（離線，CI 用）
    python scripts/check-sources.py --manual          # 列出需人工取得的來源（後台、需申請）

變動時會把新版本與 diff 存到 _studies/snapshots/<id>/（gitignored），供更新 reference 時對照。
"""

import argparse
import concurrent.futures
import datetime
import difflib
import hashlib
import html
import json
import re
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / 'sources' / 'official-sources.json'
STATE = ROOT / 'sources' / 'state.json'
SNAPSHOTS = ROOT / '_studies' / 'snapshots'

FORMATS = {'html', 'md', 'pdf', 'json', 'js', 'zip', 'xlsx', 'docx', 'txt'}
ACCESS = {'public', 'login', 'apply', 'confidential'}
SKILLS = {'invoice', 'payment', 'logistics'}
BINARY = {'pdf', 'zip', 'xlsx', 'docx'}
# 部分官方站（財政部、藍新、ezPay）的 WAF 會擋非瀏覽器請求
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/json,application/pdf,*/*',
    'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
}


def load_manifest():
    return json.loads(MANIFEST.read_text(encoding='utf-8'))


def load_state():
    return json.loads(STATE.read_text(encoding='utf-8')) if STATE.exists() else {}


def validate(entries):
    """回傳問題清單（離線檢查）"""
    problems = []
    seen = set()
    for i, e in enumerate(entries):
        where = e.get('id') or f'#{i}'
        for key in ('id', 'provider', 'skills', 'title', 'format', 'fetch', 'access', 'covers'):
            if key not in e:
                problems.append(f'{where}: 缺少欄位 {key}')
        if e.get('id') in seen:
            problems.append(f'{where}: id 重複')
        seen.add(e.get('id'))
        if e.get('format') not in FORMATS:
            problems.append(f'{where}: format 不合法 {e.get("format")}')
        if e.get('access') not in ACCESS:
            problems.append(f'{where}: access 不合法 {e.get("access")}')
        if not set(e.get('skills', [])) <= SKILLS:
            problems.append(f'{where}: skills 不合法 {e.get("skills")}')
        fetch = e.get('fetch')
        if not (fetch in ('get', 'browser', 'manual') or (isinstance(fetch, dict) and fetch.get('method') == 'POST')):
            problems.append(f'{where}: fetch 不合法 {fetch}')
        # 人工取得的來源（例如業者私下提供的外掛）可以沒有網址
        if (e.get('url') or fetch != 'manual') and not str(e.get('url', '')).startswith(('http://', 'https://')):
            problems.append(f'{where}: url 缺少或不是 http(s)')
        for path in e.get('covers', []):
            if not (ROOT / path.split('#')[0]).exists():
                problems.append(f'{where}: covers 路徑不存在 {path}')
    return problems


# 每個網站的（並行數, 請求間隔秒數）。綠界過頻會回 403 並封鎖約 30 分鐘
HOST_POLICY = {'developers.ecpay.com.tw': (1, 2.0)}
DEFAULT_POLICY = (2, 0.3)
_host_state = {}
_host_guard = threading.Lock()


class _HostSlot:
    def __init__(self, concurrency, interval):
        self.sem = threading.BoundedSemaphore(concurrency)
        self.interval = interval
        self.last = 0.0
        self.lock = threading.Lock()

    def __enter__(self):
        self.sem.acquire()
        with self.lock:
            wait = self.last + self.interval - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            self.last = time.monotonic()

    def __exit__(self, *exc):
        self.sem.release()


def _host_slot(url):
    host = urllib.parse.urlsplit(url).netloc
    with _host_guard:
        if host not in _host_state:
            _host_state[host] = _HostSlot(*HOST_POLICY.get(host, DEFAULT_POLICY))
        return _host_state[host]


def fetch(e):
    spec = e['fetch']
    data = None
    if isinstance(spec, dict):
        data = urllib.parse.urlencode(spec.get('data', {})).encode()
    req = urllib.request.Request(e['url'], data=data, headers={**HEADERS, **e.get('headers', {})})
    with _host_slot(e['url']):
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=45) as resp:
                    return resp.read(), resp.headers.get_content_charset()
            except urllib.error.HTTPError as exc:
                # 綠界的 403 是封鎖，重試只會延長，直接回報
                if attempt == 2 or exc.code not in (429, 500, 502, 503, 504):
                    raise
                time.sleep(5 * (attempt + 1))


def decode(raw, charset, e):
    for enc in filter(None, (e.get('encoding'), charset, 'utf-8', 'big5', 'cp950')):
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode('utf-8', errors='replace')


def normalize(raw, charset, e):
    """轉成可比對的內容：HTML 只留可見文字，JSON 排序鍵，二進位原樣"""
    fmt = e['format']
    if fmt in BINARY:
        return raw, None
    text = decode(raw, charset, e)
    if fmt == 'html':
        text = re.sub(r'(?is)<(script|style|noscript)\b.*?</\1>', ' ', text)
        text = re.sub(r'(?s)<!--.*?-->', ' ', text)
        text = re.sub(r'(?i)<br\s*/?>|</(p|div|li|tr|h[1-6])>', '\n', text)
        text = html.unescape(re.sub(r'<[^>]+>', ' ', text))
    elif fmt == 'json':
        try:
            obj = json.loads(text)
            for key in filter(None, e.get('json_path', '').split('.')):
                obj = obj[key]  # 只比對內容欄位，避免瀏覽次數等欄位造成誤報
            text = obj if isinstance(obj, str) else json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=True)
        except (ValueError, KeyError, TypeError):
            pass
    for pattern in e.get('ignore', []):
        text = re.sub(pattern, '', text)
    lines = [re.sub(r'[ \t　]+', ' ', ln).strip() for ln in text.splitlines()]
    # 中文字之間的空白常被官網編輯時增刪，不影響內容
    lines = [re.sub(r'(?<=[　-鿿＀-￯]) (?=[　-鿿＀-￯])', '', ln) for ln in lines if ln]
    if e.get('min_line_length'):
        # 導覽列、頁尾多是短字詞，渲染時常缺漏；只比對較長的內文行
        lines = [ln for ln in lines if len(ln) >= e['min_line_length']]
    if e.get('sort_lines'):
        lines = sorted(set(lines))  # 內容順序會隨機變動的頁面（首頁推薦、關鍵字雲）
    text = '\n'.join(lines)
    return text.encode('utf-8'), text


class BrowserFetcher:
    """網頁應用（Docusaurus、SPA）用無頭瀏覽器渲染後取可見文字；需要 pip install playwright 與 playwright install chromium"""

    NOT_FOUND = ('Page Not Found', '找不到頁面')
    BLOCKED = ("You don't have permission to access", 'Access Denied')

    def __enter__(self):
        from playwright.sync_api import sync_playwright
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch()
        self._page = self._browser.new_page(user_agent=HEADERS['User-Agent'], locale='zh-TW')
        return self

    def __exit__(self, *exc):
        self._browser.close()
        self._pw.stop()

    def __call__(self, e):
        with _host_slot(e['url']):
            try:
                self._page.goto(e['url'], wait_until='networkidle', timeout=45000)
            except Exception:
                # 有長連線的頁面（Uber Help）永遠不會 networkidle，改取已載入的內容
                self._page.wait_for_load_state('load', timeout=30000)
                self._page.wait_for_timeout(3000)
            text = self._page.inner_text('body')
        if any(marker in text for marker in self.NOT_FOUND):
            raise OSError('頁面不存在（Page Not Found）')
        if any(marker in text for marker in self.BLOCKED):
            raise OSError('被網站防火牆阻擋')
        return text.encode('utf-8'), 'utf-8'


def browser_available():
    try:
        import playwright.sync_api  # noqa: F401
        return True
    except ImportError:
        return False


def check(e, state, fetcher=fetch):
    try:
        raw, charset = fetcher(e)
    except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as exc:
        return {'id': e['id'], 'status': 'error', 'detail': str(exc)[:160]}
    except Exception as exc:  # 瀏覽器逾時等
        return {'id': e['id'], 'status': 'error', 'detail': f'{type(exc).__name__}: {str(exc)[:140]}'}
    if fetcher is not fetch:
        e = {**e, 'format': 'txt'}  # 已是渲染後的可見文字
    body, text = normalize(raw, charset, e)
    digest = hashlib.sha256(body).hexdigest()
    prev = state.get(e['id'], {})
    status = 'new' if not prev else ('unchanged' if prev.get('sha256') == digest else 'changed')
    result = {'id': e['id'], 'status': status, 'sha256': digest, 'size': len(raw)}
    if status != 'unchanged':
        folder = SNAPSHOTS / e['id']
        folder.mkdir(parents=True, exist_ok=True)
        today = datetime.date.today().isoformat()
        (folder / f'{today}.{e["format"]}').write_bytes(raw)
        if text is not None:
            latest = folder / 'latest.txt'
            if latest.exists() and status == 'changed':
                diff = difflib.unified_diff(latest.read_text(encoding='utf-8').splitlines(), text.splitlines(),
                                            'before', 'after', n=1, lineterm='')
                (folder / f'{today}.diff').write_text('\n'.join(diff), encoding='utf-8')
                result['diff'] = str((folder / f'{today}.diff').relative_to(ROOT))
            latest.write_text(text, encoding='utf-8')
    return result


def main():
    ap = argparse.ArgumentParser(description='官方來源檢查')
    ap.add_argument('--provider')
    ap.add_argument('--skill', choices=sorted(SKILLS))
    ap.add_argument('--id')
    ap.add_argument('--update', action='store_true', help='把本次抓到的版本記為基準')
    ap.add_argument('--validate', action='store_true', help='只做離線格式檢查')
    ap.add_argument('--manual', action='store_true', help='列出需人工取得的來源')
    ap.add_argument('--fail-on-change', action='store_true', help='有變動時 exit 1（排程檢查用）')
    ap.add_argument('--json-out', help='把結果寫成 JSON（排程開 issue 用）')
    ap.add_argument('--no-browser', action='store_true', help='略過需瀏覽器渲染的來源')
    args = ap.parse_args()

    entries = load_manifest()
    problems = validate(entries)
    if args.validate:
        for p in problems:
            print(f'[FAIL] {p}')
        print(f'{len(entries)} 筆來源，{len(problems)} 個問題')
        return 1 if problems else 0
    if problems:
        print('清單有問題，先修正：\n  ' + '\n  '.join(problems))
        return 1

    selected = [e for e in entries
                if (not args.provider or e['provider'] == args.provider)
                and (not args.skill or args.skill in e['skills'])
                and (not args.id or e['id'] == args.id)]

    if args.manual:
        for e in selected:
            if e['fetch'] == 'manual':
                print(f'- [{e["fetch"]}] {e["provider"]}: {e["title"]} — {e.get("url", "（無公開網址）")}' + (f'（{e["notes"]}）' if e.get('notes') else ''))
        return 0

    use_browser = not args.no_browser and browser_available()
    kinds = ('manual',) if use_browser else ('manual', 'browser')
    auto = [e for e in selected if e['fetch'] not in kinds]
    state = load_state()
    by_id = {e['id']: e for e in selected}
    plain = [e for e in auto if e['fetch'] != 'browser']
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda e: check(e, state), plain))
    rendered = [e for e in auto if e['fetch'] == 'browser']
    if rendered:
        with BrowserFetcher() as browser:
            results += [check(e, state, browser) for e in rendered]
    if not use_browser and any(e['fetch'] == 'browser' for e in selected):
        print('（未安裝 playwright，略過需瀏覽器的來源：pip install playwright && playwright install chromium）')

    groups = {}
    for r in results:
        groups.setdefault(r['status'], []).append(r)

    print(f'檢查 {len(auto)} 筆（另有 {len(selected) - len(auto)} 筆需瀏覽器或人工，用 --manual 列出）')
    for status, label in (('changed', '有變動'), ('new', '新加入（尚無基準）'), ('error', '抓取失敗'), ('unchanged', '未變動')):
        items = groups.get(status, [])
        print(f'\n## {label}：{len(items)}')
        if status == 'unchanged':
            continue
        for r in items:
            e = by_id[r['id']]
            print(f'- {r["id"]} — {e["title"]}')
            print(f'  {e["url"]}')
            if r.get('detail'):
                print(f'  錯誤：{r["detail"]}')
            if r.get('diff'):
                print(f'  diff：{r["diff"]}')
            if status == 'changed' and e['covers']:
                print('  影響：' + '、'.join(e['covers']))

    if args.update:
        today = datetime.date.today().isoformat()
        for r in results:
            if r['status'] != 'error':
                state[r['id']] = {'sha256': r['sha256'], 'size': r['size'], 'checked': today}
        known = {e['id'] for e in entries}
        state = {k: v for k, v in sorted(state.items()) if k in known}
        STATE.write_text(json.dumps(state, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
        print(f'\n已更新基準：{STATE.relative_to(ROOT)}')

    if args.json_out:
        out = {status: [{'id': r['id'], 'title': by_id[r['id']]['title'], 'url': by_id[r['id']]['url'],
                         'covers': by_id[r['id']]['covers'], 'detail': r.get('detail', '')}
                        for r in groups.get(status, [])]
               for status in ('changed', 'new', 'error')}
        Path(args.json_out).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')

    return 1 if args.fail_on_change and groups.get('changed') else 0


if __name__ == '__main__':
    sys.exit(main())
