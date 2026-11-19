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

# 目錄版不能叫 Claude 登入主機、讀使用者電腦上的帳密。這些字不得出現在產出裡。
FORBIDDEN = re.compile(
    r'\bssh\b|\bscp\b|wp-config|\.env\b|id_rsa|id_ed25519|\.pem\b|password|passwd|'
    r'process\.env|os\.environ|getenv|\$_ENV|SSH_KEY|YOUR_[A-Z_]{3,}',
    re.I)

NOTE = {
    'zh': ('> 目錄精簡版：只含參考文件與 JSON 資料，不含腳本。文中提到 `scripts/`、`examples/`、`tests/` '
           '的工具在完整版（npm 套件 `{pkg}`）。\n'
           '> 金鑰與商店代號由使用者自行設定、自行提供；文中的測試帳號是服務商官方公開的測試值，不是真實憑證。'
           '帳密類欄位以 `<帳密欄位>` 表示，實際欄名見官方文件。\n'),
    'en': ('> Directory edition: reference files and JSON data only, no scripts. Tools under `scripts/`, '
           '`examples/` and `tests/` ship in the full edition (npm package `{pkg}`).\n'
           '> You set and provide your own keys and merchant IDs; test accounts in this file are the '
           "providers' published sandbox values, not real credentials. Credential-type field names are "
           'shown as `<帳密欄位>`; see the official docs for the exact name.\n'),
}


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
    """環境變數讀取改成使用者提供的 config；帳密欄名改佔位字；.env 改設定檔。"""
    text = re.sub(r'process\.env\.([A-Z][A-Z0-9_]*)!?', r'config.\1', text)
    text = re.sub(r"os\.environ(?:\.get)?[\[(]['\"]([A-Z0-9_]+)['\"](?:,[^)\]]*)?[\])]", r"config['\1']", text)
    text = re.sub(r"getenv\(['\"]([A-Z0-9_]+)['\"]\)", r"$config['\1']", text)
    text = re.sub(r"\$_ENV\[['\"]([A-Z0-9_]+)['\"]\]", r"$config['\1']", text)
    text = re.sub(r'`?\.env`? ?檔', '設定檔', text)
    text = re.sub(r'\b\.env\b', '設定檔', text)
    text = re.sub(r'(?i)\b\w*pass(?:word|wd)\w*\b', '<帳密欄位>', text)
    text = re.sub(r'(?i)\bYOUR_([A-Z][A-Z0-9_]+)', r'<\1>', text)
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
    fm = re.sub(r'^(description: .*?)(\s*中文觸發：|$)',
                lambda m: m.group(1).rstrip() + f' Directory edition: reference files and JSON data only; '
                f'the search tools and runnable examples ship in the npm package {pkg}.'
                + (' ' + m.group(2).strip() if m.group(2).strip() else ''),
                fm, count=1, flags=re.M)
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
            if FORBIDDEN.search(line):
                problems.append(f'{rel}:{i}: {line.strip()[:100]}')
    if problems:
        raise SystemExit('目錄版不符合規則：\n  ' + '\n  '.join(problems))
    return out


def existing() -> dict[str, bytes]:
    if not OUT.exists():
        return {}
    return {p.relative_to(OUT).as_posix(): p.read_bytes() for p in OUT.rglob('*') if p.is_file()}


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
