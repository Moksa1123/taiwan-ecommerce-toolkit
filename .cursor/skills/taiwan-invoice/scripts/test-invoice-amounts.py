#!/usr/bin/env python3
"""
測試與驗證發票金額計算

使用方法:
    python test-invoice-amounts.py
"""


def calculate_b2c_amounts(total_amount: int):
    """
    B2C (二聯式) 金額計算
    - 金額為含稅價
    - TaxAmount = 0
    """
    return {
        'type': 'B2C',
        'salesAmount': total_amount,
        'taxAmount': 0,
        'totalAmount': total_amount,
    }


def calculate_b2b_amounts(total_amount: int):
    """
    B2B (三聯式) 金額計算
    - 需分拆未稅金額與稅額
    - 稅率 5%
    """
    tax_amount = round(total_amount - (total_amount / 1.05))
    sales_amount = total_amount - tax_amount

    return {
        'type': 'B2B',
        'salesAmount': sales_amount,
        'taxAmount': tax_amount,
        'totalAmount': total_amount,
    }


def verify_calculation(amounts: dict):
    """驗證計算是否正確"""
    calculated_total = amounts['salesAmount'] + amounts['taxAmount']
    is_valid = calculated_total == amounts['totalAmount']

    return is_valid, calculated_total


def test_amounts():
    """測試各種金額"""
    test_cases = [
        1050,   # 標準金額
        100,    # 小金額
        10000,  # 大金額
        9999,   # 奇數金額
        1,      # 最小金額
    ]

    print("=" * 60)
    print("台灣電子發票金額計算測試")
    print("=" * 60)

    for amount in test_cases:
        print(f"\n測試金額: NT$ {amount:,}")
        print("-" * 60)

        # B2C 計算
        b2c = calculate_b2c_amounts(amount)
        b2c_valid, b2c_total = verify_calculation(b2c)

        print(f"\nB2C (二聯式):")
        print(f"   銷售額 (含稅): {b2c['salesAmount']:,}")
        print(f"   稅額:          {b2c['taxAmount']:,}")
        print(f"   總計:          {b2c['totalAmount']:,}")
        print(f"   驗證: {'[PASS]' if b2c_valid else '[FAIL]'}")

        # B2B 計算
        b2b = calculate_b2b_amounts(amount)
        b2b_valid, b2b_total = verify_calculation(b2b)

        print(f"\nB2B (三聯式):")
        print(f"   銷售額 (未稅): {b2b['salesAmount']:,}")
        print(f"   稅額:          {b2b['taxAmount']:,}")
        print(f"   總計:          {b2b['totalAmount']:,}")
        print(f"   驗證: {'[PASS]' if b2b_valid else '[FAIL]'}")

        # 反推稅率
        if b2b['salesAmount'] > 0:
            tax_rate = (b2b['taxAmount'] / b2b['salesAmount']) * 100
            print(f"   實際稅率:      {tax_rate:.2f}%")


def test_product_items():
    """測試商品明細計算"""
    print("\n" + "=" * 60)
    print("商品明細計算測試")
    print("=" * 60)

    # 測試案例：購物車有多個商品
    items = [
        {'name': '商品A', 'price': 100, 'qty': 2},  # 200
        {'name': '商品B', 'price': 150, 'qty': 1},  # 150
        {'name': '商品C', 'price': 500, 'qty': 3},  # 1500
    ]

    print("\n購物車商品:")
    total = 0
    for item in items:
        amount = item['price'] * item['qty']
        total += amount
        print(f"   {item['name']}: NT$ {item['price']:,} x {item['qty']} = NT$ {amount:,}")

    print(f"\n   小計: NT$ {total:,}")

    # B2B 分拆
    b2b = calculate_b2b_amounts(total)
    print(f"\nB2B 三聯式發票:")
    print(f"   未稅金額: NT$ {b2b['salesAmount']:,}")
    print(f"   稅額 (5%): NT$ {b2b['taxAmount']:,}")
    print(f"   總計:     NT$ {b2b['totalAmount']:,}")


if __name__ == "__main__":
    test_amounts()
    test_product_items()

    print("\n" + "=" * 60)
    print("[DONE] 測試完成")
    print("=" * 60)
