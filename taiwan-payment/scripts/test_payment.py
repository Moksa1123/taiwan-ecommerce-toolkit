#!/usr/bin/env python3
"""
台灣金流 API 連線測試腳本

支援平台: ECPay, NewebPay, PayUNi

用法:
    python test_payment.py                    # 測試 ECPay 連線
    python test_payment.py --platform newebpay # 測試 NewebPay 連線
    python test_payment.py --platform payuni   # 測試 PayUNi 連線
    python test_payment.py --list             # 列出支援平台
    python test_payment.py --create           # 建立測試訂單
    python test_payment.py --query ORDER123   # 查詢訂單
"""

import base64
import hashlib
import urllib.parse
import time
import sys
import argparse
from datetime import datetime

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False


# 平台設定
PLATFORMS = {
    'ecpay': {
        'name': '綠界科技 ECPay',
        'merchant_id': '3002607',
        'hash_key': 'pwFHCqoQZGmho4w6',
        'hash_iv': 'EkRm7iFT261dpevs',
        'api_url': 'https://payment-stage.ecpay.com.tw/Cashier/AioCheckOut/V5',
        'query_url': 'https://payment-stage.ecpay.com.tw/Cashier/QueryTradeInfo/V5',
        'test_url': 'https://payment-stage.ecpay.com.tw/',
        'auth_method': 'SHA256',
        'test_card': '4311-9522-2222-2222',
    },
    'newebpay': {
        'name': '藍新金流 NewebPay',
        'merchant_id': '請至後台申請',
        'hash_key': '請至後台申請',
        'hash_iv': '請至後台申請',
        'api_url': 'https://ccore.newebpay.com/MPG/mpg_gateway',
        'query_url': 'https://ccore.newebpay.com/API/QueryTradeInfo',
        'test_url': 'https://ccore.newebpay.com/',
        'auth_method': 'AES-256-CBC',
        'test_card': '4000-2211-1111-1111',
    },
    'payuni': {
        'name': '統一金流 PAYUNi',
        'merchant_id': '請至後台申請',
        'hash_key': '請至後台申請',
        'hash_iv': '請至後台申請',
        'api_url': 'https://sandbox-api.payuni.com.tw/api/upp',
        'query_url': 'https://sandbox-api.payuni.com.tw/api/trade/query',
        'test_url': 'https://sandbox-api.payuni.com.tw/',
        'auth_method': 'AES-256-GCM',
        'test_card': '4000-2211-1111-1111',
    },
}


def ecpay_url_encode(text: str) -> str:
    """綠界 .NET 風格 URL encode（對應官方 SDK UrlService::ecpayUrlEncode）"""
    encoded = urllib.parse.quote_plus(text, safe='').replace('~', '%7E').lower()
    for src, dst in (('%2d', '-'), ('%5f', '_'), ('%2e', '.'), ('%21', '!'),
                     ('%2a', '*'), ('%28', '('), ('%29', ')')):
        encoded = encoded.replace(src, dst)
    return encoded


def generate_ecpay_mac(params: dict, hash_key: str, hash_iv: str) -> str:
    """ECPay CheckMacValue (SHA256)：排除 CheckMacValue、不分大小寫排序"""
    items = sorted(((k, v) for k, v in params.items() if k != 'CheckMacValue'), key=lambda kv: kv[0].lower())
    param_str = '&'.join(f'{k}={v}' for k, v in items)
    raw = f'HashKey={hash_key}&{param_str}&HashIV={hash_iv}'
    return hashlib.sha256(ecpay_url_encode(raw).encode('utf-8')).hexdigest().upper()


def generate_newebpay_trade_info(params: dict, hash_key: str, hash_iv: str) -> str:
    """NewebPay TradeInfo (AES-256-CBC, PKCS#7)，與規格書 NDNF 範例一致"""
    if not HAS_CRYPTO:
        return "需要 pycryptodome 套件"
    query_string = urllib.parse.urlencode(params)
    cipher = AES.new(hash_key.encode('utf-8'), AES.MODE_CBC, hash_iv.encode('utf-8'))
    padded = pad(query_string.encode('utf-8'), AES.block_size)
    encrypted = cipher.encrypt(padded)
    return encrypted.hex()


def generate_newebpay_sha(trade_info: str, hash_key: str, hash_iv: str) -> str:
    """NewebPay TradeSha (SHA256)"""
    raw = f'HashKey={hash_key}&{trade_info}&HashIV={hash_iv}'
    return hashlib.sha256(raw.encode('utf-8')).hexdigest().upper()


def generate_payuni_encrypt(params: dict, hash_key: str, hash_iv: str) -> str:
    """PayUNi EncryptInfo = hex( base64(密文) + ":::" + base64(tag) )，與官方外掛一致"""
    if not HAS_CRYPTO:
        return "需要 pycryptodome 套件"
    query_string = urllib.parse.urlencode(params)
    cipher = AES.new(hash_key.encode('utf-8'), AES.MODE_GCM, nonce=hash_iv.encode('utf-8'))
    encrypted, tag = cipher.encrypt_and_digest(query_string.encode('utf-8'))
    return (base64.b64encode(encrypted) + b':::' + base64.b64encode(tag)).hex()


def generate_payuni_hash(encrypt_info: str, hash_key: str, hash_iv: str) -> str:
    """PayUNi HashInfo = SHA256(HashKey + EncryptInfo + HashIV)，Key 在前"""
    raw = hash_key + encrypt_info + hash_iv
    return hashlib.sha256(raw.encode('utf-8')).hexdigest().upper()


# 已知答案測試（known-answer test）：輸入與預期值皆由業者官方程式產生
# （綠界官方 SDK、PAYUNi 官方外掛、藍新規格書 PHP 範例），出處見 repo 的 tests/vectors/。
# 雜湊值涵蓋整段密文，雜湊相符即代表加密結果逐位元組相同。
KNOWN_ANSWERS = {
    'ecpay': {
        'hash_key': 'pwFHCqoQZGmho4w6', 'hash_iv': 'EkRm7iFT261dpevs',
        'params': {'MerchantID': '3002607', 'MerchantTradeNo': 'ORD20260923001', 'MerchantTradeDate': '2026/09/23 12:00:00', 'PaymentType': 'aio', 'TotalAmount': '1280', 'TradeDesc': 'a-b_c.d', 'ItemName': '商品(A)*2 限量!#特價', 'ReturnURL': 'https://shop.example.com/ecpay/notify', 'ChoosePayment': 'ALL', 'EncryptType': '1'},
        'expected': '4C4284BE8276B608A981AB5FF04CD981A9D5C8B54C0F151BC80F012CAA90AAF3',
    },
    'newebpay': {
        'hash_key': '12345678901234567890123456789012', 'hash_iv': '1234567890123456',
        'params': {'MerchantID': 'MS12345678', 'RespondType': 'JSON', 'TimeStamp': '1758600000', 'Version': '2.0', 'MerchantOrderNo': 'ORD20260923001', 'Amt': '1280', 'ItemDesc': '測試商品 A & B', 'Email': 'buyer+tw@example.com'},
        'expected': '67426922975581A2D8367FC990C3DB637B5D17A986CC87D560FE8BF1BD9FFAAE',
    },
    'payuni': {
        'hash_key': '12345678901234567890123456789012', 'hash_iv': '1234567890123456',
        'params': {'MerID': 'S01234567', 'MerTradeNo': 'T20260923002', 'TradeAmt': '1280', 'Timestamp': '1758600000', 'ProdDesc': '測試商品 A & B'},
        'expected': 'B1EA028236FC4D6B5D768E1EAB57EC60465265EF19AEED500F0ECBB79C4DB63D',
    },
}


def run_known_answer_test(platform: str) -> bool:
    """以官方程式產生的標準答案驗證本檔的加密實作"""
    kat = KNOWN_ANSWERS[platform]
    key, iv, params = kat['hash_key'], kat['hash_iv'], kat['params']
    if platform == 'ecpay':
        got = generate_ecpay_mac(params, key, iv)
    elif not HAS_CRYPTO:
        print('  (需要 pycryptodome 套件: pip install pycryptodome)')
        return False
    elif platform == 'newebpay':
        got = generate_newebpay_sha(generate_newebpay_trade_info(params, key, iv), key, iv)
    else:
        got = generate_payuni_hash(generate_payuni_encrypt(params, key, iv), key, iv)
    ok = got == kat['expected']
    print(f'  已知答案測試: {"通過" if ok else "失敗"}（與官方實作{"一致" if ok else "不一致"}）')
    if not ok:
        print(f'    預期 {kat["expected"]}')
        print(f'    實得 {got}')
    return ok


def test_connection(platform: str):
    """測試 API 連線"""
    config = PLATFORMS.get(platform)
    if not config:
        print(f'錯誤: 不支援的平台 "{platform}"')
        print(f'支援的平台: {", ".join(PLATFORMS.keys())}')
        sys.exit(1)

    print('=' * 60)
    print(f'{config["name"]} API 連線測試')
    print('=' * 60)
    print()

    # 測試環境資訊
    print('[測試環境]')
    print(f'  平台: {config["name"]}')
    print(f'  商店代號: {config["merchant_id"]}')
    print(f'  加密方式: {config["auth_method"]}')
    print(f'  測試網址: {config["test_url"]}')
    print()

    # 測試加密計算：以官方實作產生的標準答案比對，而不是只看長度
    print('[加密計算測試]')
    run_known_answer_test(platform)
    print()

    # 測試網路連線
    if HAS_REQUESTS:
        print('[網路連線測試]')
        try:
            response = requests.head(config['test_url'], timeout=5)
            print(f'  狀態碼: {response.status_code}')
            print(f'  連線: {"成功" if response.status_code < 500 else "失敗"}')
        except requests.RequestException as e:
            print(f'  連線失敗: {e}')
    else:
        print('[網路連線測試]')
        print('  (需要 requests 套件: pip install requests)')
    print()

    # 顯示測試信用卡
    print('[測試信用卡]')
    print(f'  卡號: {config["test_card"]}')
    print('  有效期: 任意未過期日期')
    print('  CVV: 任意三碼')
    print()

    print('=' * 60)
    print('測試完成')
    print('=' * 60)


def create_test_order(platform: str):
    """建立測試訂單"""
    config = PLATFORMS.get(platform)
    if not config:
        print(f'錯誤: 不支援的平台 "{platform}"')
        sys.exit(1)

    if config['merchant_id'] == '請至後台申請':
        print(f'錯誤: 請先設定 {config["name"]} 的測試帳號')
        print('請編輯此腳本，填入您的測試商店資訊')
        sys.exit(1)

    order_id = f'TEST{int(time.time())}'
    trade_date = datetime.now().strftime('%Y/%m/%d %H:%M:%S')

    print('=' * 60)
    print(f'建立 {config["name"]} 測試訂單')
    print('=' * 60)
    print()
    print(f'訂單編號: {order_id}')
    print(f'交易時間: {trade_date}')
    print(f'金額: 100 TWD')
    print()

    if platform == 'ecpay':
        params = {
            'MerchantID': config['merchant_id'],
            'MerchantTradeNo': order_id,
            'MerchantTradeDate': trade_date,
            'PaymentType': 'aio',
            'TotalAmount': 100,
            'TradeDesc': urllib.parse.quote('測試訂單'),
            'ItemName': '測試商品 x 1',
            'ReturnURL': 'https://example.com/callback',
            'ChoosePayment': 'Credit',
            'EncryptType': 1,
        }
        params['CheckMacValue'] = generate_ecpay_mac(params, config['hash_key'], config['hash_iv'])

        html = f'''<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>ECPay 測試</title></head>
<body>
<h1>ECPay 測試訂單 {order_id}</h1>
<form method="post" action="{config['api_url']}">
'''
        for k, v in params.items():
            html += f'<input type="hidden" name="{k}" value="{v}">\n'
        html += '<button type="submit">前往付款</button>\n</form>\n</body></html>'

        filename = f'ecpay_test_{order_id}.html'
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f'已產生測試頁面: {filename}')
        print('請在瀏覽器中開啟此檔案進行付款測試')
        print()
        print(f'測試信用卡: {config["test_card"]}')

    else:
        print(f'{platform} 的測試訂單建立功能需要 pycryptodome 套件')
        print('請執行: pip install pycryptodome')


def query_order(platform: str, order_id: str):
    """查詢訂單狀態"""
    if not HAS_REQUESTS:
        print('錯誤: 需要 requests 套件')
        sys.exit(1)

    config = PLATFORMS.get(platform)
    if not config:
        print(f'錯誤: 不支援的平台 "{platform}"')
        sys.exit(1)

    print('=' * 60)
    print(f'查詢 {config["name"]} 訂單: {order_id}')
    print('=' * 60)
    print()

    if platform == 'ecpay':
        params = {
            'MerchantID': config['merchant_id'],
            'MerchantTradeNo': order_id,
            'TimeStamp': int(time.time()),
        }
        params['CheckMacValue'] = generate_ecpay_mac(params, config['hash_key'], config['hash_iv'])

        try:
            response = requests.post(config['query_url'], data=params, timeout=10)
            print(f'HTTP 狀態碼: {response.status_code}')
            print('回應內容:')
            print(response.text)
        except requests.RequestException as e:
            print(f'查詢失敗: {e}')
    else:
        print(f'{platform} 的查詢功能需要額外設定')


def list_platforms():
    """列出支援的平台"""
    print('=' * 60)
    print('支援的金流平台')
    print('=' * 60)
    print()
    for key, config in PLATFORMS.items():
        print(f'  {key:12} - {config["name"]}')
        print(f'                 加密: {config["auth_method"]}')
        print(f'                 測試: {config["test_url"]}')
        print()


def main():
    parser = argparse.ArgumentParser(
        description='台灣金流 API 測試工具 (支援 ECPay/NewebPay/PayUNi)'
    )
    parser.add_argument(
        '--platform', '-p',
        type=str,
        default='ecpay',
        help='金流平台 (ecpay/newebpay/payuni)'
    )
    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='列出支援的平台'
    )
    parser.add_argument(
        '--create',
        action='store_true',
        help='建立測試訂單'
    )
    parser.add_argument(
        '--query',
        type=str,
        metavar='ORDER_ID',
        help='查詢訂單狀態'
    )

    args = parser.parse_args()

    if args.list:
        list_platforms()
    elif args.create:
        create_test_order(args.platform)
    elif args.query:
        query_order(args.platform, args.query)
    else:
        test_connection(args.platform)


if __name__ == '__main__':
    main()
