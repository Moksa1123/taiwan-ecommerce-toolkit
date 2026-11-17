#!/usr/bin/env python3
"""
test_skill.py — skill 自我測試（離線、只用標準函式庫）。

檢查：
  1. SKILL.md：六個固定段落、鐵則在路由段第一行、大小 ≤ 20KB、每個 references/*.md 都有連到
  2. SKILL.md、README.md、README.zh-TW.md 每個數字都登記且與資料一致（check_numbers.py）
  3. data/*.csv 每列都有 trust，官方文件的列要有 doc_url；pending.csv 欄位正確
  4. 路由表與驗證段裡的 search.py 指令都查得到結果
  5. 使用者路徑的腳本只 import 標準函式庫（第三方只能放在 try 區塊裡當選用）
  6. evals/cases.json：至少 10 題有效題，欄位齊全，正規式可編譯
  7. 既有測試（EXTRA_TESTS）全過

三個 taiwan skill 共用同一份；只有 EXTRA_TESTS 不同。
用法：python scripts/test_skill.py      失敗數 > 0 時 exit 1
"""
from __future__ import annotations

import ast
import csv
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
sys.path.insert(0, str(HERE))

import check_numbers  # noqa: E402
import core  # noqa: E402

EXTRA_TESTS = {
    'taiwan-payment': [['test_recommend.py'], ['test_payment.py', '--platform', 'all']],
    'taiwan-invoice': [['test_recommend.py'], ['test_search.py'], ['test-invoice-amounts.py']],
    'taiwan-logistics': [['test_logistics.py']],
}[SKILL.name]

# 中文版或英文版（SOP 6-9；英文寫的 skill 保持英文）
HEADINGS = [('資料出處', 'Sources'), ('用法', 'Usage'), ('路由', 'Routing'),
            ('使用', 'Tasks'), ('驗證', 'Verify'), ('維護', 'Maintenance')]
TRUST = {'實測', '官方文件', '推論', '站內風格'}
PENDING_COLS = ['date', 'question', 'why_not_found', 'asked_by', 'status']
# 使用者會跑的腳本（SOP 6-2：只能用標準函式庫）
USER_SCRIPTS = ['core.py', 'search.py', 'recommend.py', 'check_numbers.py', 'test_skill.py',
                'generate-invoice-service.py', 'generate-logistics-service.py', 'persist.py', 'error_handler.py']

failed = 0
passed = 0


def check(label: str, ok: bool, detail: str = '') -> None:
    global failed, passed
    print(f'  [{"PASS" if ok else "FAIL"}] {label}' + (f'：{detail}' if detail and not ok else ''))
    if ok:
        passed += 1
    else:
        failed += 1


def skill_md() -> str:
    return (SKILL / 'SKILL.md').read_text(encoding='utf-8')


def test_structure() -> None:
    print('1. SKILL.md 結構')
    text = skill_md()
    heads = re.findall(r'^## (.+?)\s*$', text, re.M)
    names = [pair[0 if '資料出處' in heads else 1] for pair in HEADINGS]
    missing = [h for h in names if h not in heads]
    check('六個固定段落標題', not missing, '缺 ' + '、'.join(missing))
    order = [heads.index(h) for h in names if h in heads]
    check('段落順序', order == sorted(order))
    route = text.split('## ' + names[2], 1)[-1].lstrip('\n').split('\n', 1)[0]
    rule = '先查再答' in route or 'look it up first' in route
    check('鐵則在路由段第一行', rule and 'pending.csv' in route, route[:60])
    size = (SKILL / 'SKILL.md').stat().st_size
    check('SKILL.md ≤ 20KB', size <= 20 * 1024, f'{size:,} bytes')
    refs = sorted(p.name for p in (SKILL / 'references').glob('*.md'))
    unlinked = [r for r in refs if f'references/{r}' not in text]
    check(f'references 的 {len(refs)} 個檔都列在 SKILL.md', not unlinked, '、'.join(unlinked))
    examples = SKILL / 'EXAMPLES.md'
    check('EXAMPLES.md 存在', examples.exists())


def test_numbers() -> None:
    print('2. SKILL.md、README 數字（check_numbers.py）')
    for path, problems, n in check_numbers.check_all():
        check(f'{path.name}：{n} 個數字全部登記且一致', not problems, '；'.join(problems[:5]))


def test_data() -> None:
    print('3. 資料出處欄')
    for path in sorted((SKILL / 'data').glob('*.csv')):
        with open(path, encoding='utf-8-sig', newline='') as f:
            rows = list(csv.DictReader(f))
            header = list(rows[0].keys()) if rows else []
        if path.name == 'pending.csv':
            check('pending.csv 欄位', header == PENDING_COLS, str(header))
            continue
        bad_trust = [i for i, r in enumerate(rows, 2) if r.get('trust') not in TRUST]
        no_url = [i for i, r in enumerate(rows, 2) if r.get('trust') == '官方文件' and not r.get('doc_url')]
        check(f'{path.name}：{len(rows)} 列 trust 有效', not bad_trust, f'第 {bad_trust[:5]} 列')
        check(f'{path.name}：官方文件的列都有 doc_url', not no_url, f'第 {no_url[:5]} 列')


def test_routing() -> None:
    print('4. SKILL.md 裡的查詢指令')
    cmds = re.findall(r'`search\.py ("[^"`]+"[^`]*)`', skill_md())
    check('至少 5 條查詢指令', len(cmds) >= 5, str(len(cmds)))
    for cmd in cmds:
        args = shlex.split(cmd)
        query, domain = args[0], None
        if '--domain' in args:
            domain = args[args.index('--domain') + 1]
        hits = core.search(query, domain=domain, max_results=5) if domain != 'all' else core.search_all(query)
        check(f'search.py {cmd} 有結果', bool(hits))


def _third_party(path: Path) -> list[str]:
    """回傳不在 try 區塊裡、也不是標準函式庫或本目錄模組的 import"""
    tree = ast.parse(path.read_text(encoding='utf-8'))
    guarded = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Try):
            for sub in ast.walk(node):
                guarded.add(id(sub))
    local = {p.stem for p in HERE.glob('*.py')}
    bad = []
    for node in ast.walk(tree):
        if id(node) in guarded:
            continue
        names = []
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names = [node.module]
        for name in names:
            top = name.split('.')[0]
            if top not in sys.stdlib_module_names and top not in local and top != '__future__':
                bad.append(name)
    return bad


def test_stdlib() -> None:
    print('5. 使用者路徑只用標準函式庫')
    for name in USER_SCRIPTS + [c[0] for c in EXTRA_TESTS]:
        path = HERE / name
        if path.exists():
            bad = _third_party(path)
            check(f'{name}', not bad, '、'.join(bad))
    check('requirements.txt 存在（examples 與 --live 的依賴）', (SKILL / 'requirements.txt').exists())


def test_evals() -> None:
    print('6. evals 題庫')
    path = SKILL / 'evals' / 'cases.json'
    if not path.exists():
        check('evals/cases.json 存在', False)
        return
    cases = json.loads(path.read_text(encoding='utf-8'))['cases']
    active = [c for c in cases if not c.get('retired')]
    check(f'有效題 ≥ 10（{len(active)}）', len(active) >= 10)
    ids = [c['id'] for c in cases]
    check('題目 id 不重複', len(ids) == len(set(ids)))
    for c in cases:
        miss = [k for k in ('id', 'question', 'must', 'source', 'trust') if not c.get(k)]
        try:
            for group in c.get('must', []):
                for p in group:
                    re.compile(p)
            ok_rx = True
        except re.error:
            ok_rx = False
        if miss or not ok_rx or c.get('trust') not in TRUST:
            check(f'{c.get("id")} 欄位齊全', False, '缺 ' + '、'.join(miss) if miss else '正規式或 trust 錯')
    check('RESULTS.md 存在', (SKILL / 'evals' / 'RESULTS.md').exists())


def test_extra() -> None:
    print('7. 既有測試')
    for cmd in EXTRA_TESTS:
        r = subprocess.run([sys.executable, str(HERE / cmd[0]), *cmd[1:]], capture_output=True,
                           text=True, encoding='utf-8', errors='replace', env={**__import__('os').environ,
                                                                              'PYTHONIOENCODING': 'utf-8'})
        tail = (r.stdout.strip().splitlines() or [''])[-1]
        check(f'{" ".join(cmd)}（{tail[:40]}）', r.returncode == 0, r.stderr[-200:])


def main() -> int:
    core.use_utf8_stdout()
    print(f'{SKILL.name} 自我測試')
    for t in (test_structure, test_numbers, test_data, test_routing, test_stdlib, test_evals, test_extra):
        t()
    print(f'\n通過 {passed}、失敗 {failed}')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
