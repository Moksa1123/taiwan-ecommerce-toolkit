#!/usr/bin/env python3
"""
build_directory.py — 產生 directory-plugin/（Claude 官方目錄精簡版）。

未認證的發布者在官方目錄只能放 Markdown、文字、JSON、YAML 與圖片，skill 放在
skills/<name>/。這支從主 repo 的原始檔產生那個資料夾，不手動維護兩份：

    taiwan-<skill>/SKILL.md（擷取段落）、references/*.md、EXAMPLES.md、data/*.csv、
    LICENSE、.claude-plugin/plugin.json、icon.png、scripts/directory/*.tmpl

CSV 轉成 JSON（太大的依 provider 拆檔），腳本、範例程式、package.json 都不放。
讀環境變數的寫法改成使用者自行提供的設定；帳密欄名以佔位字表示。只用標準函式庫。

用法:
    python3 scripts/build_directory.py           # 寫入 directory-plugin/
    python3 scripts/build_directory.py --check   # directory-plugin/ 與原始檔不同步就 exit 1
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'directory-plugin'
TMPL = ROOT / 'scripts' / 'directory'
REPO = 'https://github.com/Moksa1123/taiwan-ecommerce-toolkit'
SKILLS = ('invoice', 'payment', 'logistics')

MAX_BYTES = 256 * 1024          # 官方目錄：非圖檔超過就轉人工審
SPLIT_BYTES = 200 * 1024        # JSON 超過就依 provider 拆檔
ALLOWED = {'.md', '.json', '.png', ''}   # '' = LICENSE

# 目錄版不能叫 Claude 登入主機、讀使用者電腦上的帳密。這些寫法不得出現在產出裡。
# 官方目錄 2026-11-19 實測：檔內同時有遠端主機與 key／secret／token 類變數（${X}、$X、config.X、
# <X_KEY> 佔位字、寫死的測試金鑰）就判成「把安裝者的金鑰送到該主機」；官方建議改成 YOUR_API_KEY 這種假值。
FORBIDDEN = re.compile(
    r'\bssh\b|\bscp\b|wp-config|\.env\b|id_rsa|id_ed25519|\.pem\b|password|passwd|'
    r'process\.env|os\.environ|getenv|\$_ENV|SSH_KEY|\bconfig\[|\bcredentials\s*=|'
    r'<[A-Z0-9_]*(?:KEY|SECRET|TOKEN|HASH_IV)[A-Z0-9_]*>|\$secret\b',
    re.I)
# 全大寫的環境變數式寫法；用 re.I 會誤殺 $merchantId，所以分開比
FORBIDDEN_CS = re.compile(r'\bconfig\.[A-Z][A-Z0-9_]+\b|\$\{?[A-Z][A-Z0-9_]{2,}\b|\$\{TradeToken\}')

# 官方公開的測試金鑰：目錄版一律換成佔位字（完整版保留，並有已知答案測試）
EXTRA_SECRETS = [
    # 街口官方文件的共用測試 Secret Key
    'r0odDC1e9LHXDmxuvmOv9bgaWLf2CXB2c4gMheoFucVKNMi1K0Id9zwRHJF1r-kdtAKriKgb11VDlo7Kb8R-FQ',
    'XBERn1YOvpM9nfZc', 'h1ONHk4P4yqbl5LK',     # 綠界物流 C2C 測試特店
    'HwiqPsywG1hLQNuN', 'YqITWD4TyKacYXpn',     # 綠界發票平台商測試
    'bkuAEQufy2bpEng1', 'B0lzARI9ZSdhW9jg',     # 歐付寶平台商測試
    'sk_test_abc123def456',                     # SHOPLINE 文件範例 key
]
# PayNow 傳統版的 Bootstrap Key/IV 是協定常數（實作必需），不是帳號金鑰，保留
SECRET_PLACEHOLDER = 'YOUR_TEST_KEY'

NOTE = {
    'zh': ('> 目錄精簡版：只含參考文件與 JSON 資料，不含腳本。文中提到 `scripts/`、`examples/`、`tests/` '
           '的工具在完整版（npm 套件 `{pkg}`）。\n'
           '> 金鑰與商店代號由使用者在自己的系統設定後，以參數傳入程式；文中以 `YOUR_HASH_KEY` 這類假值表示。'
           '服務商公開的測試金鑰以 `YOUR_TEST_KEY` 表示，請到該服務商官方文件取得。帳密類欄位以 `<帳密欄位>` 表示。\n'),
    'en': ('> Directory edition: reference files and JSON data only, no scripts. Tools under `scripts/`, '
           '`examples/` and `tests/` ship in the full edition (npm package `{pkg}`).\n'
           '> Keys and merchant IDs are set up by the user and passed into the code as parameters; they '
           'appear as fake values such as `YOUR_HASH_KEY`. Published sandbox keys are shown as '
           "`YOUR_TEST_KEY`; get them from the provider's official docs. Credential-type field names are "
           'shown as `<帳密欄位>`.\n'),
}


def test_secrets() -> list[str]:
    """providers.csv 的測試金鑰欄裡看起來像金鑰的值（英數、8 碼以上）。"""
    out = set(EXTRA_SECRETS)
    for skill in SKILLS:
        with open(ROOT / f'taiwan-{skill}' / 'data' / 'providers.csv', encoding='utf-8', newline='') as f:
            for row in csv.DictReader(f):
                for col in ('test_hash_key', 'test_hash_iv'):
                    v = (row.get(col) or '').strip()
                    if re.fullmatch(r'[A-Za-z0-9_-]{8,}', v):
                        out.add(v)
    return sorted(out, key=len, reverse=True)


SECRETS: list[str] = []


def load_core(skill: str):
    """各 skill 都有 scripts/core.py，用不同模組名載入避免互相覆蓋。"""
    path = ROOT / f'taiwan-{skill}' / 'scripts' / 'core.py'
    spec = importlib.util.spec_from_file_location(f'core_{skill}', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def pkg_version(skill: str) -> str:
    return json.loads((ROOT / f'{skill}-cli' / 'package.json').read_text(encoding='utf-8'))['version']


def credential_free(text: str) -> str:
    """不寫「從哪裡讀金鑰」：環境變數、設定物件、shell 變數都改成 YOUR_X 假值（官方建議的寫法），
    網址類改 https://example.com；官方測試金鑰改 YOUR_TEST_KEY；帳密欄名改佔位字；.env 改設定檔。"""
    if not SECRETS:
        SECRETS.extend(test_secrets())

    def fake(name: str, quote: str = "'") -> str:
        if name.endswith('_URL') or name.startswith('NEXT_PUBLIC_BASE'):
            return f'{quote}https://example.com{quote}' if quote else 'https://example.com'
        return f'{quote}YOUR_{name}{quote}'

    # 先處理 process.env 的特殊用法，再處理一般情形
    text = re.sub(r'process\.env\.NODE_ENV\s*===\s*[\'"]production[\'"]', 'isProduction', text)
    text = re.sub(r'\$\{process\.env\.([A-Z][A-Z0-9_]*)\}', lambda m: fake(m.group(1), ''), text)
    text = re.sub(r'process\.env\.([A-Z][A-Z0-9_]*)!?', lambda m: fake(m.group(1)), text)
    text = re.sub(r"os\.environ(?:\.get)?[\[(]['\"]([A-Z0-9_]+)['\"](?:,[^)\]]*)?[\])]",
                  lambda m: fake(m.group(1)), text)
    text = re.sub(r"getenv\(['\"]([A-Z0-9_]+)['\"]\)", lambda m: fake(m.group(1)), text)
    text = re.sub(r"\$_ENV\[['\"]([A-Z0-9_]+)['\"]\]", lambda m: fake(m.group(1)), text)
    text = re.sub(r'\$\{?([A-Z][A-Z0-9_]{2,})\}?\b', lambda m: fake(m.group(1), ''), text)  # shell：$SHOPLINE_API_KEY
    # 原文的 <PARTNER_KEY>、<SECRET> 這類佔位字也會被當成帳密變數
    text = re.sub(r'(?i)<([A-Z0-9_]*(?:KEY|SECRET|TOKEN|HASH_IV)[A-Z0-9_]*)>',
                  lambda m: 'YOUR_' + m.group(1).upper(), text)
    text = re.sub(r'\bcredentials(\s*=|\})', r'encoded\1', text)
    text = re.sub(r'\bbasic_auth\b', 'encoded', text)
    text = re.sub(r'\$secret\b', "'YOUR_SECRET_KEY'", text)          # 街口 PHP 一行範例
    text = re.sub(r'\$\{TradeToken\}', 'TRADE_TOKEN_FROM_API', text)  # 歐付寶 URL Scheme 範例
    text = re.sub(r'`?\.env`? ?檔', '設定檔', text)
    text = re.sub(r'\b\.env\b', '設定檔', text)
    text = re.sub(r'(?i)\b\w*pass(?:word|wd)\w*\b', '<帳密欄位>', text)
    text = re.sub(r'(密碼\s*)`[^`\n]+`', r'\1`YOUR_TEST_LOGIN`', text)
    for s in SECRETS:
        # 簽章範例裡會出現 URL encode 後轉小寫的版本，所以不分大小寫
        text = re.sub(re.escape(s), SECRET_PLACEHOLDER, text, flags=re.I)
    return text


def lang(skill: str) -> str:
    return 'en' if skill == 'logistics' else 'zh'


def reference(skill: str, path: Path) -> str:
    text = credential_free(path.read_text(encoding='utf-8'))
    first, _, rest = text.partition('\n')
    return f'{first}\n\n{NOTE[lang(skill)].format(pkg=f"taiwan-{skill}-skill")}{rest}'


def section(text: str, start: str, stop: str) -> str:
    m = re.search(start, text, re.M)
    if not m:
        raise SystemExit(f'找不到段落起點：{start}')
    end = re.search(stop, text[m.end():], re.M)
    return text[m.start(): m.end() + end.start() if end else len(text)].strip()


def no_scripts(block: str, lg: str) -> str:
    """擷取的 SKILL.md 段落：拿掉指向腳本的表格列，CSV 檔名改 JSON。"""
    keep = [l for l in block.splitlines()
            if not (l.startswith('|') and re.search(r'scripts/|\.py\b|tests/', l))]
    out = '\n'.join(keep)
    out = re.sub(r'data/([\w*-]+)\.csv', r'data/\1.json', out)
    out = re.sub(r'`?(?:python3? )?(?:scripts/)?[\w-]+\.py(?: [^`]*)?`?', '完整版的工具' if lg == 'zh' else "the full edition's tools", out)
    return credential_free(out)


def skill_sections(skill: str) -> dict:
    text = (ROOT / f'taiwan-{skill}' / 'SKILL.md').read_text(encoding='utf-8')
    fm = text.split('---', 2)[1]
    lg = lang(skill)
    return {
        'fm': fm,
        'title': re.search(r'^# (.+)$', text, re.M).group(1),
        'sources': no_scripts(section(text, r'^## (?:資料出處|Sources)', r'^## '), lg),
        'when': no_scripts(section(text, r'^\*\*(?:何時用|Use this skill for)\*\*', r'^\*\*(?:唯一入口|Single entry)'), lg),
        'rule': no_scripts(re.search(r'^\*\*(?:鐵則|Rule: look it up first).*$', text, re.M).group(0), lg),
        'code_rules': no_scripts(section(text, r'^\*\*(?:寫程式時務必遵守|Rules when writing code)\*\*', r'^## '), lg),
        'refs': [l for l in text.splitlines() if l.startswith('|') and '`references/' in l],
    }


def csv_rows(path: Path) -> list[dict]:
    with open(path, encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def data_files(skill: str) -> tuple[dict[str, str], list[tuple[str, int, str, str]]]:
    """data/*.csv → data/*.json；error-codes*.csv 等同域多檔合併後依 provider 拆。
    回傳 (檔案, 說明列[(json 檔名, 筆數, 搜尋域, 欄位)])。"""
    core = load_core(skill)
    domain_of = {}
    for dom, cfg in core.CSV_CONFIG.items():
        for p in (ROOT / f'taiwan-{skill}' / 'data').glob(cfg['file']):
            domain_of[p.name] = dom
    groups: dict[str, list[Path]] = {}
    for p in sorted((ROOT / f'taiwan-{skill}' / 'data').glob('*.csv')):
        stem = re.sub(r'-\d+$', '', p.stem)          # error-codes-payuni-1 → error-codes-payuni
        stem = 'error-codes' if stem.startswith('error-codes') else stem
        groups.setdefault(stem, []).append(p)
    files, table = {}, []
    for stem, paths in groups.items():
        rows = [r for p in paths for r in csv_rows(p)]
        rows = [{k: credential_free(v or '') for k, v in r.items()} for r in rows]
        dom = domain_of.get(paths[0].name, '')
        cols = ', '.join(f'`{c}`' for c in list(rows[0])[:6]) if rows else ''

        def dump(rs, src=stem):
            return json.dumps({'source_files': [f'data/{p.name}' for p in paths], 'domain': dom,
                               'rows': rs}, ensure_ascii=False, indent=1) + '\n'
        whole = dump(rows)
        if len(whole.encode('utf-8')) <= SPLIT_BYTES or 'provider' not in rows[0]:
            files[f'data/{stem}.json'] = whole
            table.append((f'{stem}.json', len(rows), dom, cols))
            continue
        by: dict[str, list[dict]] = {}
        for r in rows:
            by.setdefault(r['provider'] or 'other', []).append(r)
        # 小的服務商併成一檔，大的單獨一檔；每檔都要在 SPLIT_BYTES 內
        bucket, size, n = [], 0, 1
        for prov in sorted(by, key=lambda k: -len(by[k])):
            part = by[prov]
            psize = len(dump(part).encode('utf-8'))
            if bucket and size + psize > SPLIT_BYTES:
                name = f'{stem}-{n}.json'
                files[f'data/{name}'] = dump(bucket)
                table.append((name, len(bucket), dom, cols))
                bucket, size, n = [], 0, n + 1
            if psize > SPLIT_BYTES:          # 單一服務商仍太大就再切
                step = max(1, len(part) * SPLIT_BYTES // psize - 1)
                for i in range(0, len(part), step):
                    name = f'{stem}-{n}.json'
                    files[f'data/{name}'] = dump(part[i:i + step])
                    table.append((name, len(part[i:i + step]), dom, cols))
                    n += 1
                continue
            bucket += part
            size += psize
        if bucket:
            name = f'{stem}-{n}.json'
            files[f'data/{name}'] = dump(bucket)
            table.append((name, len(bucket), dom, cols))
    return files, table


def fill(template: str, values: dict) -> str:
    out = template
    for k, v in values.items():
        out = out.replace('{{' + k + '}}', v)
    left = re.findall(r'\{\{[A-Z_]+\}\}', out)
    if left:
        raise SystemExit(f'範本還有沒填的欄位：{left}')
    return out


def frontmatter(skill: str, fm: str) -> str:
    pkg = f'taiwan-{skill}-skill'
    m = re.search(r'^description: (.*)$', fm, re.M)
    desc = m.group(1).strip()
    if desc[:1] in '"\'|>':
        raise SystemExit(f'{skill} SKILL.md 的 description 格式變了，請更新 frontmatter()')
    head, sep, tail = desc.partition('中文觸發：')
    desc = (head.rstrip() + f' Directory edition: reference files and JSON data only; the search tools and '
            f'runnable examples ship in the npm package {pkg}.' + (f' {sep}{tail}' if sep else ''))
    # 官方目錄提醒：沒加引號的值可能被誤讀（# 被當註解）；用 JSON 字串格式（YAML 相容）加雙引號
    fm = fm[:m.start()] + 'description: ' + json.dumps(desc, ensure_ascii=False) + fm[m.end():]
    return '---' + fm + '---'


def skill_md(skill: str, table) -> str:
    s = skill_sections(skill)
    data_rows = '\n'.join(f'| `data/{n}` | {rows} | {dom or "—"} | {cols} |' for n, rows, dom, cols in table)
    return fill((TMPL / 'SKILL.md.tmpl').read_text(encoding='utf-8'), {
        'FRONTMATTER': frontmatter(skill, s['fm']),
        'TITLE': s['title'],
        'PKG': f'taiwan-{skill}-skill',
        'VERSION': pkg_version(skill),
        'SOURCES': s['sources'],
        'WHEN': s['when'],
        'RULE': s['rule'],
        'DATA_TABLE': data_rows,
        'REFS': '\n'.join(s['refs']),
        'CODE_RULES': s['code_rules'],
    })


def plugin_json() -> str:
    pj = json.loads((ROOT / '.claude-plugin' / 'plugin.json').read_text(encoding='utf-8'))
    pj['displayName'] = 'Taiwan E-commerce Toolkit (unofficial)'
    pj['description'] = (pj['description'].rstrip('.') + '. Directory edition: reference files and JSON data '
                         'only, no scripts. Unofficial: not made by or affiliated with any provider named here.')
    pj['icon'] = './.claude-plugin/icon.png'
    for k in ('homepage', 'documentationUrl'):
        pj[k] = f'{REPO}/tree/main/directory-plugin#readme'
    pj['privacyPolicyUrl'] = f'{REPO}/tree/main/directory-plugin#what-it-runs-and-connects-to'
    pj['skills'] = [f'./skills/taiwan-{s}' for s in SKILLS]
    return json.dumps(pj, ensure_ascii=False, indent=2) + '\n'


def readme(counts: dict) -> str:
    values = {f'VER_{s.upper()}': pkg_version(s) for s in SKILLS}
    values.update({f'ROWS_{s.upper()}': str(counts[s]) for s in SKILLS})
    return fill((TMPL / 'README.md.tmpl').read_text(encoding='utf-8'), values)


def build() -> dict[str, bytes]:
    files: dict[str, str | bytes] = {
        'LICENSE': (ROOT / 'LICENSE').read_text(encoding='utf-8'),
        '.claude-plugin/plugin.json': plugin_json(),
        '.claude-plugin/icon.png': (ROOT / 'icon.png').read_bytes(),
    }
    counts = {}
    for skill in SKILLS:
        base = f'skills/taiwan-{skill}'
        data, table = data_files(skill)
        counts[skill] = sum(r for _, r, _, _ in table)
        for rel, text in data.items():
            files[f'{base}/{rel}'] = text
        files[f'{base}/SKILL.md'] = skill_md(skill, table)
        files[f'{base}/EXAMPLES.md'] = reference(skill, ROOT / f'taiwan-{skill}' / 'EXAMPLES.md')
        for p in sorted((ROOT / f'taiwan-{skill}' / 'references').glob('*.md')):
            files[f'{base}/references/{p.name}'] = reference(skill, p)
    files['README.md'] = readme(counts)
    out = {k: v if isinstance(v, bytes) else v.replace('\r\n', '\n').encode('utf-8') for k, v in files.items()}
    problems = []
    for rel, data in out.items():
        if Path(rel).suffix not in ALLOWED:
            problems.append(f'{rel}: 副檔名不在目錄允許清單')
        if not rel.endswith('.png') and len(data) > MAX_BYTES:
            problems.append(f'{rel}: {len(data)} bytes 超過 256 KiB')
        if rel.endswith('.png'):
            continue
        for i, line in enumerate(data.decode('utf-8').splitlines(), 1):
            low = line.lower()
            if FORBIDDEN.search(line) or FORBIDDEN_CS.search(line) or any(s.lower() in low for s in SECRETS):
                problems.append(f'{rel}:{i}: {line.strip()[:100]}')
    if problems:
        raise SystemExit('目錄版不符合規則：\n  ' + '\n  '.join(problems))
    return out


def existing() -> dict[str, bytes]:
    if not OUT.exists():
        return {}
    # Windows 的 core.autocrlf 會在 checkout 時改成 CRLF；比對時一律看 LF
    return {p.relative_to(OUT).as_posix(): p.read_bytes() if p.suffix == '.png'
            else p.read_bytes().replace(b'\r\n', b'\n') for p in OUT.rglob('*') if p.is_file()}


def differences(want: dict[str, bytes], have: dict[str, bytes]) -> list[str]:
    out = [f'缺少：{k}' for k in sorted(set(want) - set(have))]
    out += [f'多出（不是由原始檔產生）：{k}' for k in sorted(set(have) - set(want))]
    out += [f'過期：{k}' for k in sorted(set(want) & set(have)) if want[k] != have[k]]
    return out


def main() -> int:
    for s in (sys.stdout, sys.stderr):
        if hasattr(s, 'reconfigure'):
            s.reconfigure(encoding='utf-8', errors='replace')
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[1])
    ap.add_argument('--check', action='store_true', help='只比對；不同步就 exit 1')
    args = ap.parse_args()
    want = build()
    diff = differences(want, existing())
    if args.check:
        if diff:
            print('directory-plugin/ 和原始檔不同步（請跑 python3 scripts/build_directory.py）：')
            for d in diff:
                print('  ✗', d)
            return 1
        print(f'directory-plugin/ 與原始檔一致（{len(want)} 個檔）。')
        return 0
    for rel, data in want.items():
        p = OUT / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    extra = [d for d in diff if d.startswith('多出')]
    print(f'已寫入 {len(want)} 個檔到 directory-plugin/')
    for d in extra:
        print('  !', d, '（請手動刪除）')
    return 1 if extra else 0


if __name__ == '__main__':
    raise SystemExit(main())
