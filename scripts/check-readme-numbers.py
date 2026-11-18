#!/usr/bin/env python3
"""
根目錄 README.md / README.zh-TW.md 的徽章與表格數字要和資料一致。

各 skill 自己的 README 由 taiwan-<skill>/scripts/check_numbers.py 檢查；
這支只管根目錄兩份總覽：服務商家數、AI 平台數、npx 指定的版本。

用法:
    python3 scripts/check-readme-numbers.py      # 有不一致 exit 1
"""
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILES = [ROOT / 'README.md', ROOT / 'README.zh-TW.md']


def providers(skill):
    with open(ROOT / f'taiwan-{skill}' / 'data' / 'providers.csv', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def facts():
    inv = providers('invoice')
    pay = providers('payment')
    log = providers('logistics')
    api = [r for r in log if r['api_available'].lower() == 'true']
    upstream = {'mof', 'tradevan'}
    return {
        'invoice': len(inv),
        'invoice_vac': sum(1 for r in inv if r['provider'].lower() not in upstream),
        'payment': len(pay),
        'logistics_api': len(api),
        'logistics_no_api': len(log) - len(api),
        'logistics_aggregator': sum(1 for r in api if 'aggregator' in r['type']),
        'logistics_ondemand': sum(1 for r in api if r['type'] == 'ondemand'),
        'total': len(inv) + len(pay) + len(api),
        'ai_platforms': len(list((ROOT / 'payment-cli' / 'assets' / 'templates' / 'platforms').glob('*.json'))),
        **{f'ver_{s}': json.loads((ROOT / f'{s}-cli' / 'package.json').read_text(encoding='utf-8'))['version']
           for s in ('invoice', 'payment', 'logistics')},
    }


# (正規式, 事實名稱)；第 1 組是要核對的數字。每條規則在每個檔至少要出現一次。
RULES = [
    (r'badge/providers-(\d+)-', 'total'),
    (r'(\d+) Providers"', 'total'),
    (r'badge/AI%20platforms-(\d+)-', 'ai_platforms'),
    (r'(\d+) AI Platforms"', 'ai_platforms'),
    (r'\*\*(\d+) (?:providers|個服務商)\*\*', 'total'),
    (r'\((\d+) invoice|（(\d+) 家發票', 'invoice'),
    (r'(\d+) payment \+|(\d+) 家金流 \+', 'payment'),
    (r'(\d+) integrable logistics|(\d+) 家可串接物流', 'logistics_api'),
    (r'plus (\d+) logistics carriers|另收錄 (\d+) 家', 'logistics_no_api'),
    (r'(\d+) providers: |(\d+) 家：', 'invoice'),
    (r'(\d+) value-added centers|(\d+) 家加值中心', 'invoice_vac'),
    (r'(\d+) payment providers and wallets|(\d+) 家金流與電子支付', 'payment'),
    (r'(\d+) integrable: |(\d+) 家可串接：', 'logistics_api'),
    (r'(\d+) aggregators|(\d+) 家聚合商', 'logistics_aggregator'),
    (r'(\d+) on-demand|(\d+) 家即時配送', 'logistics_ondemand'),
    (r'Logistics \((\d+) integrable\)|物流串接（(\d+) 家可串接）', 'logistics_api'),
    (r'taiwan-invoice-skill@([\d.]+)', 'ver_invoice'),
    (r'taiwan-payment-skill@([\d.]+)', 'ver_payment'),
    (r'taiwan-logistics-skill@([\d.]+)', 'ver_logistics'),
]


def main():
    f = facts()
    problems = []
    checked = 0
    for path in FILES:
        text = path.read_text(encoding='utf-8')
        for pattern, key in RULES:
            hits = list(re.finditer(pattern, text))
            if not hits:
                problems.append(f'{path.name}：規則沒用到（寫法改了？）{pattern}')
            for m in hits:
                got = next(g for g in m.groups() if g is not None)
                checked += 1
                if got != str(f[key]):
                    line = text.count('\n', 0, m.start()) + 1
                    problems.append(f'{path.name} 第 {line} 行：{key} 寫 {got}，實際 {f[key]}')
    if problems:
        print(f'根目錄 README 有 {len(problems)} 個數字問題：')
        for p in problems:
            print('  ✗', p)
        return 1
    print(f'根目錄 README 的 {checked} 個數字與資料一致。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
