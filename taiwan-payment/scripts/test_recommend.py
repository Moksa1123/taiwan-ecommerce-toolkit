#!/usr/bin/env python3
"""
推薦系統回歸測試

鎖住 reasoning.csv 規則比對的行為。原本的比對有兩個問題：
1. 只比對 scenario，use_cases 整欄被忽略
2. 查詢中任一詞是 scenario 的子字串就給該規則完整權重

現行做法見 core.rule_match_score()：同時比對 scenario 與 use_cases，
以查詢被規則解釋的比例加權，並要求最低命中詞數。

使用方法:
    python test_recommend.py
"""

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from core import rule_match_score, MIN_RULE_MATCH  # noqa: E402
from recommend import analyze_requirements  # noqa: E402


# (查詢, 期望推薦的服務商)
EXPECTED = [
    ('高交易量 穩定 電商', 'ecpay'),
    ('多元支付 電子錢包 LINE Pay', 'newebpay'),
    ('RESTful JSON API 新創', 'payuni'),
    ('街口 按用量計費 儲值', 'jkopay'),
    ('RSA 非對稱加密 金流', 'sunpay'),
    ('延遲撥款 擔保交易', 'opay'),
    ('WooCommerce 官方模組', 'sunpay'),
]


def top_provider(query):
    scores = analyze_requirements(query)
    ranked = sorted(scores.items(), key=lambda x: x[1][0], reverse=True)
    return ranked[0][0], ranked[0][1][0]


def test_expected_providers():
    failures = []

    for query, expected in EXPECTED:
        actual, score = top_provider(query)
        status = 'PASS' if actual == expected else 'FAIL'
        print(f"   [{status}] {query!r} -> {actual} ({score:.2f})")
        if actual != expected:
            failures.append((query, expected, actual))

    return failures


def test_use_cases_is_matched():
    """use_cases 欄必須參與比對

    舊實作只看 scenario，導致只在 use_cases 描述的情境永遠無法命中。
    """
    strength = rule_match_score('按用量計費 儲值加值', '', '按用量計費 儲值加值 變動金額扣款')
    ok = strength >= 0.5
    print(f"   [{'PASS' if ok else 'FAIL'}] use_cases 有參與比對 (strength={strength:.3f})")
    return [] if ok else [('use_cases matched', '>= 0.5', strength)]


def test_single_token_noise_rejected():
    """單一高頻短詞命中不應達到計分門檻"""
    strength = rule_match_score('冪等 重試 避免重複開立', '離線 POS 開立 批次取號')
    ok = strength < MIN_RULE_MATCH
    print(f"   [{'PASS' if ok else 'FAIL'}] 單詞雜訊被濾掉 (strength={strength:.3f} < {MIN_RULE_MATCH})")
    return [] if ok else [('single-token noise', f'< {MIN_RULE_MATCH}', strength)]


def test_verbose_rule_not_penalised():
    """規則寫得詳細不該被扣分"""
    short_rule = rule_match_score('離線 POS 開立發票', '離線 POS 開立')
    long_rule = rule_match_score('離線 POS 開立發票', '離線 POS 開立 批次取號 實體門市 多台POS 字軌分段')
    ok = abs(short_rule - long_rule) < 1e-9
    print(f"   [{'PASS' if ok else 'FAIL'}] 詞多寡不影響分數 (短={short_rule:.3f} 長={long_rule:.3f})")
    return [] if ok else [('verbose rule', short_rule, long_rule)]


def main():
    print('=' * 60)
    print('推薦系統回歸測試 (taiwan-payment)')
    print('=' * 60)

    failures = []

    print('\n1. 代表性查詢的推薦結果')
    failures += test_expected_providers()

    print('\n2. 規則比對強度')
    failures += test_use_cases_is_matched()
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
