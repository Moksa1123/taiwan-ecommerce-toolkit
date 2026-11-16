#!/usr/bin/env python3
"""
為三個 skill 的 data/*.csv 每一列補上出處欄：doc_url、retrieved_on、trust（維護者用）。

出處的決定方式（不猜，只用登記過的官方來源）：
1. 列的服務商：有 provider 欄就用它；寬表（<服務商>_name／_endpoint／_code 欄）取有填值的服務商。
2. doc_url：sources/official-sources.json 裡「服務商相同且 covers 包含這個 CSV」的來源剛好一筆就用它；
   零筆或多筆時用該 skill providers.csv 的 doc_url（服務商官方文件入口）。
3. retrieved_on：來源在 sources/state.json 的 checked 日期；退回 providers.csv 的 doc_verified。
4. trust：reasoning、troubleshooting 是依官方文件歸納的建議 → 推論；其餘來自廠商文件 → 官方文件；
   找不到任何官方來源的列 → 推論，doc_url 留空，並列在輸出最後（要記進 data/pending.csv）。

providers.csv 本身已有 doc_url／doc_verified，只補 trust。
已有 trust 欄的列不覆寫（人工判定優先）。

用法：
    python scripts/add-provenance.py            # 改寫 CSV
    python scripts/add-provenance.py --check    # 只檢查每列都有出處欄，有缺 exit 1
"""
import argparse
import csv
import glob
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS = {'payment': 'taiwan-payment', 'invoice': 'taiwan-invoice', 'logistics': 'taiwan-logistics'}
INFERRED_FILES = {'reasoning.csv', 'troubleshooting.csv'}
# 沒有 provider 欄、也不是寬表的檔：整檔指定來源（source id 或 None＝推論）
FILE_SOURCE = {
    ('invoice', 'carrier-types.csv'): 'mof-einvoice-api-spec-v1-9',
    ('invoice', 'tax-rules.csv'): None,
}
# 物流 operations.csv 的列沒有服務商欄位，靠 operation 前綴辨認
OP_PREFIX = {'sp_': 'smilepay', 'pcp_': 'pchomepay', 'pn_': 'paynow', 'hct_': 'hct', 'ez_': 'ezship',
             'llm_': 'lalamove', 'pdg_': 'pandago'}
# providers.csv 名稱與 official-sources.json provider 的對應（大小寫、別名）
ALIAS = {'hct_direct': 'hct'}

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, 'reconfigure'):
        _s.reconfigure(encoding='utf-8', errors='replace')


def load_json(rel):
    with open(os.path.join(ROOT, rel), encoding='utf-8') as f:
        return json.load(f)


def read_csv(path):
    with open(path, encoding='utf-8', newline='') as f:
        text = f.read()
    bom = text.startswith('﻿')
    rows = list(csv.reader(io.StringIO(text.lstrip('﻿'))))
    return bom, rows


def write_csv(path, bom, rows):
    buf = io.StringIO()
    csv.writer(buf, lineterminator='\n').writerows(rows)
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(('﻿' if bom else '') + buf.getvalue())


def norm(p):
    p = (p or '').strip().lower()
    return ALIAS.get(p, p)


def providers_of(header, row, known):
    d = dict(zip(header, row))
    for col in ('provider', 'recommended_provider'):
        if col in d:
            return [norm(x) for x in re.split(r'[/,、;+]\s*', d[col]) if x.strip()]
    out = []
    op = d.get('operation', '')
    for pre, p in OP_PREFIX.items():
        if op.startswith(pre):
            out.append(p)
    m = re.search(r'(\w+)專用', d.get('notes', ''))
    if m and norm(m.group(1)) in known:
        out.append(norm(m.group(1)))
    for col, val in d.items():
        m = re.match(r'([a-z]+?)(?:_legacy|_modern|_b2c|_b2b)?_(name|endpoint|code)$', col)
        if m and val.strip() and m.group(1) in known and m.group(1) not in out:
            out.append(m.group(1))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()

    sources = load_json('sources/official-sources.json')
    state = load_json('sources/state.json')
    by_id = {s['id']: s for s in sources}
    unresolved, missing, total = [], [], 0

    for skill, folder in SKILLS.items():
        with open(os.path.join(ROOT, folder, 'data', 'providers.csv'), encoding='utf-8') as f:
            prov = {norm(r['provider']): r for r in csv.DictReader(f)}
        for path in sorted(glob.glob(os.path.join(ROOT, folder, 'data', '*.csv'))):
            name = os.path.basename(path)
            if name == 'pending.csv':
                continue
            rel = f'{folder}/data/{name}'
            bom, rows = read_csv(path)
            header, body = rows[0], [r for r in rows[1:] if r]
            is_prov = name == 'providers.csv'
            need = ['trust'] if is_prov else ['doc_url', 'retrieved_on', 'trust']
            if args.check:
                for i, r in enumerate(body, 2):
                    d = dict(zip(header, r))
                    if any(c not in header for c in need) or not d.get('trust'):
                        missing.append(f'{rel}:{i}')
                total += len(body)
                continue
            for c in need:
                if c not in header:
                    header.append(c)
            idx = {c: header.index(c) for c in header}
            covering = {}
            for s in sources:
                # fetch 是 dict 的來源是 POST API（例：PAYUNi ShowDoc），網址不能直接開，改用文件入口
                if rel in s.get('covers', []) and not isinstance(s.get('fetch'), dict):
                    covering.setdefault(norm(s['provider']), []).append(s)
            for n, r in enumerate(body, 2):
                r.extend([''] * (len(header) - len(r)))
                if r[idx['trust']]:
                    continue
                if is_prov:
                    r[idx['trust']] = '官方文件' if r[idx['doc_url']] else '推論'
                    if not r[idx['doc_url']]:
                        unresolved.append(f'{rel}:{n}（{r[0]}）')
                    continue
                urls, dates = [], []
                if (skill, name) in FILE_SOURCE:
                    sid = FILE_SOURCE[(skill, name)]
                    if sid:
                        urls.append(by_id[sid]['url'])
                        dates.append(state.get(sid, {}).get('checked', ''))
                else:
                    for p in providers_of(header, r, prov):
                        cand = covering.get(p, [])
                        if len(cand) == 1:
                            urls.append(cand[0]['url'])
                            dates.append(state.get(cand[0]['id'], {}).get('checked', ''))
                        elif p in prov and prov[p]['doc_url']:
                            urls.append(prov[p]['doc_url'])
                            dates.append(prov[p]['doc_verified'])
                if urls:
                    r[idx['doc_url']] = ' '.join(dict.fromkeys(urls))
                    r[idx['retrieved_on']] = max(d for d in dates if d) if any(dates) else ''
                    r[idx['trust']] = '推論' if name in INFERRED_FILES else '官方文件'
                else:
                    r[idx['trust']] = '推論'
                    unresolved.append(f'{rel}:{n}（{r[0][:30]}）')
            write_csv(path, bom, [header] + body)
            total += len(body)

    if args.check:
        print(f'{total} 列；缺出處欄 {len(missing)} 列')
        for m in missing[:20]:
            print('  ✗', m)
        return 1 if missing else 0
    print(f'{total} 列已補出處欄；找不到官方來源（標推論、doc_url 空）{len(unresolved)} 列')
    for u in unresolved:
        print('  ?', u)
    return 0


if __name__ == '__main__':
    sys.exit(main())
