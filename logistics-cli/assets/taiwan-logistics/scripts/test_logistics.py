#!/usr/bin/env python3
"""
物流 API 測試工具

簽章／加解密一律沿用 examples/ 內已驗證的實作（CI 以官方測試向量比對），本檔不另寫一份。

用法:
    python test_logistics.py                  # 檢查全部廠商（簽章已知答案 + 測試環境連線）
    python test_logistics.py ecpay            # 只檢查 ECPay
    python test_logistics.py ecpay --create   # 於 ECPay 測試環境建立 C2C 測試訂單
    python test_logistics.py ecpay --query 1234567
"""

import argparse
import importlib.util
import sys
import time
from pathlib import Path

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

EXAMPLES = Path(__file__).resolve().parent.parent / 'examples'

# 綠界官方 SDK（CheckMacValueService）產生的標準答案
ECPAY_KAT = {
    'hash_key': '5294y06JbISpM5x9', 'hash_iv': 'v77hoKGq4kWxNNIS',
    'params': {
        'MerchantID': '2000132', 'MerchantTradeNo': 'LGS20260923001', 'MerchantTradeDate': '2026/09/23 12:00:00',
        'LogisticsType': 'CVS', 'LogisticsSubType': 'UNIMARTC2C', 'GoodsAmount': '100', 'GoodsName': '測試商品(A)',
        'SenderName': '測試商家', 'SenderCellPhone': '0912345678', 'ReceiverName': '王小明',
        'ReceiverCellPhone': '0987654321', 'ReceiverStoreID': '991182',
        'ServerReplyURL': 'https://shop.example.com/logistics/notify', 'IsCollection': 'N',
    },
    'expected': '7362212EB7E6F68F81954D98AFF18CC2',
}

ENDPOINTS = {
    'ecpay': {
        'base': 'https://logistics-stage.ecpay.com.tw',
        'paths': ['/Express/map', '/Express/Create', '/Helper/QueryLogisticsTradeInfo/V5'],
        'ref': 'references/ecpay-logistics-api.md',
    },
    'newebpay': {
        'base': 'https://ccore.newebpay.com/API/Logistic',
        'paths': ['/storeMap', '/createShipment', '/getShipmentNo', '/printLabel', '/queryShipment',
                  '/modifyShipment', '/trace'],
        'ref': 'references/NEWEBPAY_LOGISTICS_REFERENCE.md',
    },
    'payuni': {
        'base': 'https://sandbox-api.payuni.com.tw/api',
        'paths': ['/logistics/ship_map', '/logistics/query', '/logistics/print_label',
                  '/home_delivery/get_obt_number_pdf', '/home_delivery/download_pdf'],
        'ref': 'references/payuni-logistics-api.md（物流單由金流交易建立）',
    },
}


def load_example(filename):
    spec = importlib.util.spec_from_file_location(filename.replace('-', '_')[:-3], EXAMPLES / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def ecpay_client():
    return load_example('ecpay-logistics-cvs-example.py')._test_client()


def check_ecpay_signature():
    client = ecpay_client()
    client.hash_key, client.hash_iv = ECPAY_KAT['hash_key'], ECPAY_KAT['hash_iv']
    got = client.create_check_mac_value(ECPAY_KAT['params'])
    ok = got == ECPAY_KAT['expected']
    print(f'  CheckMacValue (MD5) 已知答案測試: {"通過" if ok else "失敗"}')
    if not ok:
        print(f'    預期 {ECPAY_KAT["expected"]}\n    實得 {got}')
    return ok


def check_reachable(base):
    if not HAS_REQUESTS:
        print('  (略過連線測試：需要 pip install requests)')
        return True
    try:
        status = requests.head(base, timeout=5, allow_redirects=True).status_code
    except requests.RequestException as e:
        print(f'  連線失敗: {e}')
        return False
    print(f'  {base} → HTTP {status}')
    return status < 500


def check_provider(name):
    info = ENDPOINTS[name]
    print(f'=== {name} ===')
    ok = True
    if name == 'ecpay':
        ok &= check_ecpay_signature()
    else:
        print('  簽章與加解密的已知答案測試：python scripts/verify-examples.py（repo 根目錄）')
    ok &= check_reachable(info['base'])
    print('  端點：' + '、'.join(info['paths']))
    print(f'  規格：{info["ref"]}')
    print()
    return ok


def ecpay_post(url, params):
    if not HAS_REQUESTS:
        print('需要 pip install requests')
        return 1
    response = requests.post(url, data=params, timeout=15)
    print(f'HTTP {response.status_code}')
    print(response.text[:500])
    return 0 if response.ok else 1


def main():
    parser = argparse.ArgumentParser(description='物流 API 測試工具')
    parser.add_argument('provider', nargs='?', choices=list(ENDPOINTS), help='指定廠商（預設全部）')
    parser.add_argument('--create', action='store_true', help='於 ECPay 測試環境建立 C2C 測試訂單')
    parser.add_argument('--query', metavar='ALL_PAY_LOGISTICS_ID', help='查詢 ECPay 測試環境物流訂單')
    args = parser.parse_args()

    if args.create or args.query:
        if args.provider not in (None, 'ecpay'):
            parser.error('--create／--query 只支援 ecpay（NewebPay、PAYUNi 需自備商店帳號）')
        client = ecpay_client()
        if args.create:
            # 131386 為綠界測試環境 7-11 門市（references/ecpay-logistics-api.md）
            url, params = client.create_cvs_order('T' + time.strftime('%Y%m%d%H%M%S'),
                                                  '測試商品', 100, '王小明', '0987654321', '131386')
        else:
            url, params = client.query_order(args.query)
        return ecpay_post(url, params)

    results = [check_provider(name) for name in ([args.provider] if args.provider else ENDPOINTS)]
    return 0 if all(results) else 1


if __name__ == '__main__':
    sys.exit(main())
