#!/usr/bin/env python3
"""
搜尋引擎回歸測試

鎖住兩件事：

1. **中文分詞**。此處原本只做 text.split()，中文必須整個詞完全相同才命中 ——
   搜尋「折讓」找不到「折讓的」。中文沒有空白分隔，以空白切詞在本專案的
   資料上幾乎等同關鍵字全等比對。已改為「單字 + bigram」，與
   taiwan-payment / taiwan-logistics 一致。

2. **各域的欄位涵蓋**。field 與 operation 兩域的 search_cols 原本只列出
   前三家 provider，導致其餘 provider 的資料寫進 CSV 卻搜尋不到。

使用方法:
    python test_search.py
"""

import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from core import CSV_CONFIG, search, tokenize  # noqa: E402


def check(label, condition, detail=''):
    print(f'   [{"PASS" if condition else "FAIL"}] {label}')
    if not condition and detail:
        print(f'          {detail}')
    return 0 if condition else 1


def test_tokenize():
    """中文子字串必須能命中"""
    failed = 0
    toks = tokenize('紅陽 SunPay 折讓的 unitPrice')

    failed += check('「折讓」命中「折讓的」', '折讓' in toks, f'tokens={toks}')
    failed += check('英數 token 轉小寫', 'sunpay' in toks and 'unitprice' in toks)
    failed += check('保留中文單字', '紅' in toks and '陽' in toks)
    failed += check('產生中文 bigram', '紅陽' in toks)
    failed += check('空字串回傳空列表', tokenize('') == [])
    return failed


def test_domain_coverage():
    """field 與 operation 兩域必須涵蓋所有 provider 欄位"""
    failed = 0
    for domain, suffix in [('field', '_name'), ('operation', '_endpoint')]:
        cfg = CSV_CONFIG[domain]
        path = os.path.join(os.path.dirname(SCRIPT_DIR), 'data', cfg['file'])
        with open(path, encoding='utf-8') as f:
            header = f.readline().strip().split(',')
        provider_cols = [c for c in header if c.endswith(suffix)]
        missing_search = [c for c in provider_cols if c not in cfg['search_cols']]
        missing_output = [c for c in provider_cols if c not in cfg['output_cols']]

        failed += check(
            f'{domain} 域的 search_cols 涵蓋全部 {len(provider_cols)} 個 provider 欄位',
            not missing_search, f'缺 {missing_search}')
        failed += check(
            f'{domain} 域的 output_cols 涵蓋全部 provider 欄位',
            not missing_output, f'缺 {missing_output}')
    return failed


def test_config_columns_exist():
    """設定裡列出的欄位必須真的存在於 CSV，否則是死設定"""
    failed = 0
    data_dir = os.path.join(os.path.dirname(SCRIPT_DIR), 'data')
    for domain, cfg in CSV_CONFIG.items():
        path = os.path.join(data_dir, cfg['file'])
        if not os.path.exists(path):
            continue
        with open(path, encoding='utf-8') as f:
            header = f.readline().strip().split(',')
        ghosts = [c for c in cfg['search_cols'] + cfg['output_cols'] if c not in header]
        failed += check(f'{domain} 域無不存在的欄位', not ghosts, f'{cfg["file"]} 沒有 {ghosts}')
    return failed


def test_search_finds_new_providers():
    """新收錄的 provider 必須搜得到"""
    failed = 0
    cases = [
        ('OPay', 'provider', 'opay'),
        ('SunPay', 'provider', 'sunpay'),
        ('MOF', 'provider', 'mof'),
    ]
    for query, domain, expect in cases:
        results = search(query, domain=domain, max_results=5)
        hit = any(expect in str(r).lower() for r in results)
        failed += check(f'搜尋 {query!r} 於 {domain} 域可命中', hit)
    return failed


def main():
    print('=' * 60)
    print('搜尋引擎回歸測試 (taiwan-invoice)')
    print('=' * 60)

    failed = 0
    print('\n1. 中文分詞')
    failed += test_tokenize()

    print('\n2. 各域欄位涵蓋')
    failed += test_domain_coverage()

    print('\n3. 設定欄位有效性')
    failed += test_config_columns_exist()

    print('\n4. 新 provider 可搜尋')
    failed += test_search_finds_new_providers()

    print('\n' + '=' * 60)
    if failed:
        print(f'[FAIL] {failed} 項未通過')
        return 1
    print('[DONE] 全部通過')
    return 0


if __name__ == '__main__':
    sys.exit(main())
