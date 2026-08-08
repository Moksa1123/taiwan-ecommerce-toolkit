#!/usr/bin/env python3
"""
推薦系統回歸測試

鎖住 reasoning.csv 規則比對的行為。之前的比對是「規則中任一詞出現在查詢裡
就給該規則完整權重」，導致「開立」這類高頻短詞讓不相干的規則以同分勝出
（例如查「冪等 重試」時離線發票規則會贏過真正支援冪等的加值中心）。

現行做法見 core.rule_match_score()：以查詢被規則解釋的比例加權，並要求
最低命中詞數。本測試確保該行為不再退化。

使用方法:
    python test_recommend.py
"""

import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from core import rule_match_score, MIN_RULE_MATCH  # noqa: E402
from recommend import recommend  # noqa: E402


# (查詢, 期望推薦的加值中心)
EXPECTED = [
    ('高交易量 電商 穩定', 'ECPay'),
    ('簡單 快速 小型專案', 'SmilePay'),
    ('MIG 4.0 API 標準', 'Amego'),
    ('離線 POS 開立發票', 'OPay'),
    ('B2B 交換模式 存證模式', 'OPay'),
    ('手機條碼驗證 捐贈碼查驗', 'MOF'),
    ('冪等 重試 避免重複開立', 'SunPay'),
    ('蝦皮供應商', 'TradeVAN'),
]


def test_expected_providers():
    """每個代表性查詢都應推薦到正確的加值中心"""
    failures = []

    for query, expected in EXPECTED:
        result = recommend(query)
        actual = result['recommended']
        status = 'PASS' if actual == expected else 'FAIL'
        print(f"   [{status}] {query!r} -> {actual} ({result['score']:.2f})")
        if actual != expected:
            failures.append((query, expected, actual))

    return failures


def test_single_token_noise_rejected():
    """單一高頻短詞命中不應該達到計分門檻

    「開立」幾乎出現在所有發票規則裡。只靠它命中的規則必須被濾掉，
    否則任何含「開立」的查詢都會把不相干的規則拉進推薦。
    """
    failures = []

    # 規則只在「開立」一詞上與查詢重疊，其餘完全不相關
    strength = rule_match_score('冪等 重試 避免重複開立', '離線 POS 開立 批次取號')
    ok = strength < MIN_RULE_MATCH
    print(f"   [{'PASS' if ok else 'FAIL'}] 單詞雜訊被濾掉 (strength={strength:.3f} < {MIN_RULE_MATCH})")
    if not ok:
        failures.append(('single-token noise', f'< {MIN_RULE_MATCH}', strength))

    # 真正相關的規則要明顯高於門檻
    strength = rule_match_score('冪等 重試 避免重複開立', '冪等 重試 重複開立 逾時重送')
    ok = strength >= 0.5
    print(f"   [{'PASS' if ok else 'FAIL'}] 相關規則分數足夠 (strength={strength:.3f} >= 0.5)")
    if not ok:
        failures.append(('relevant rule', '>= 0.5', strength))

    return failures


def test_verbose_rule_not_penalised():
    """規則寫得詳細不該被扣分

    曾用 F1 計分，recall 項會讓 use_cases 詞多的規則吃虧，
    使「離線 POS 開立發票」誤推到 ECPay。
    """
    short_rule = rule_match_score('離線 POS 開立發票', '離線 POS 開立')
    long_rule = rule_match_score('離線 POS 開立發票', '離線 POS 開立 批次取號 實體門市 多台POS 字軌分段')

    ok = abs(short_rule - long_rule) < 1e-9
    print(f"   [{'PASS' if ok else 'FAIL'}] 詞多寡不影響分數 (短={short_rule:.3f} 長={long_rule:.3f})")
    return [] if ok else [('verbose rule', short_rule, long_rule)]


def main():
    print('=' * 60)
    print('推薦系統回歸測試 (taiwan-invoice)')
    print('=' * 60)

    failures = []

    print('\n1. 代表性查詢的推薦結果')
    failures += test_expected_providers()

    print('\n2. 規則比對強度')
    failures += test_single_token_noise_rejected()

    print('\n3. 規則長度中立性')
    failures += test_verbose_rule_not_penalised()

    print('\n' + '=' * 60)
    if failures:
        print(f'[FAIL] {len(failures)} 項未通過')
        for item in failures:
            print(f'   {item}')
        return 1

    print('[DONE] 全部通過')
    return 0


if __name__ == '__main__':
    sys.exit(main())
