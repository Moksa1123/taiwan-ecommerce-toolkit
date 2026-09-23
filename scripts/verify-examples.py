#!/usr/bin/env python3
"""
範例程式的差分驗證（differential testing）

過去只用 `python -m py_compile` 檢查範例，那只驗語法：dataclass 欄位順序錯誤、
加密格式與官方不符這類問題完全抓不到，結果兩支範例連 import 都會失敗、
PAYUNi / 藍新的加解密也與官方實作不一致，卻一直顯示「通過」。

本腳本做兩件事：

1. **實際 import 每一支範例**（執行 class 定義），確保至少載入得了。
2. **以官方實作產生的標準答案比對**：tests/vectors/*.json 由官方外掛原始碼或
   規格書附的 PHP 範例「原封不動」在 php:8.2-cli 執行產生（出處記在每個 JSON 的
   source 欄位），再拿範例程式的類別去算，逐位元組比對。

使用方法:
    pip install -r requirements-dev.txt
    python scripts/verify-examples.py
"""

import glob
import importlib.util
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VECTORS = os.path.join(ROOT, 'tests', 'vectors')

failed = 0


def check(label, condition, detail=''):
    """condition 可傳 callable：執行時拋出的例外視為 FAIL，不會中斷後續檢查"""
    global failed
    if callable(condition):
        try:
            condition = condition()
        except Exception as e:  # noqa: BLE001
            condition, detail = False, f'{type(e).__name__}: {e}'
    print(f'   [{"PASS" if condition else "FAIL"}] {label}')
    if not condition:
        failed += 1
        if detail:
            print(f'          {detail}')


def load_module(rel_path):
    path = os.path.join(ROOT, rel_path)
    name = os.path.splitext(os.path.basename(path))[0].replace('-', '_')
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_vectors(name):
    with open(os.path.join(VECTORS, f'{name}.json'), encoding='utf-8') as f:
        return json.load(f)


def raises(fn):
    try:
        fn()
    except Exception:
        return True
    return False


# ---------------------------------------------------------------------------
# 1. 每支範例都要 import 得了
# ---------------------------------------------------------------------------

def test_imports():
    print('\n1. 範例可實際載入（不只是語法正確）')
    for path in sorted(glob.glob(os.path.join(ROOT, 'taiwan-*', 'examples', '*.py'))):
        rel = os.path.relpath(path, ROOT).replace(os.sep, '/')
        try:
            load_module(rel)
            check(rel, True)
        except BaseException as e:  # noqa: BLE001 - 任何載入錯誤都要回報
            check(rel, False, f'{type(e).__name__}: {e}')


# ---------------------------------------------------------------------------
# 2. PAYUNi
# ---------------------------------------------------------------------------

def test_payuni():
    v = load_vectors('payuni')
    print(f'\n2. PAYUNi（標準答案出處：{v["source"]["name"]} {v["source"]["file"]}）')

    pay = load_module('taiwan-payment/examples/payuni-payment-example.py')
    lgs = load_module('taiwan-logistics/examples/payuni-logistics-cvs-example.py')
    services = {
        'payment': (pay.PAYUNiPaymentService('S01234567', v['hash_key'], v['hash_iv']), 'generate_checksum'),
        'logistics': (lgs.PAYUNiLogistics('S01234567', v['hash_key'], v['hash_iv']), 'generate_hash_info'),
    }

    for label, (svc, hash_fn) in services.items():
        for case in v['cases']:
            check(f'[{label}] {case["name"]}: EncryptInfo 與官方逐位元組相同',
                  lambda: svc.encrypt_data(case['params']) == case['EncryptInfo'])
            check(f'[{label}] {case["name"]}: HashInfo 與官方相同',
                  lambda: getattr(svc, hash_fn)(case['EncryptInfo']) == case['HashInfo'])
            check(f'[{label}] {case["name"]}: 可解密官方密文',
                  lambda: svc.decrypt_data(case['EncryptInfo']) == case['params'])

        # 竄改 tag 必須被拒絕 —— GCM 的意義就在這裡
        good = bytes.fromhex(v['cases'][0]['EncryptInfo'])
        cipher_b64, tag_b64 = good.split(b':::')
        bad_tag = tag_b64[:-3] + (b'AAA' if not tag_b64.endswith(b'AAA') else b'BBB')
        check(f'[{label}] 竄改 tag 會被拒絕',
              raises(lambda: svc.decrypt_data((cipher_b64 + b':::' + bad_tag).hex())))


# ---------------------------------------------------------------------------
# 3. 藍新 NewebPay / ezPay（ezPay 金流與藍新共用同一套 MPG 加密）
# ---------------------------------------------------------------------------

def test_newebpay():
    v = load_vectors('newebpay')
    print(f'\n3. 藍新 / ezPay 金流（標準答案出處：{v["sources"]["plugin"]}；{v["sources"]["spec"]}）')

    neweb = load_module('taiwan-payment/examples/newebpay-payment-example.py')
    ezpay = load_module('taiwan-payment/examples/ezpay-payment-example.py')
    services = {
        'newebpay': neweb.NewebPayMPGService('MS12345678', v['hash_key'], v['hash_iv']),
        'ezpay': ezpay.EzPayPaymentService('MS12345678', v['hash_key'], v['hash_iv']),
    }

    for label, svc in services.items():
        # 官方外掛以 32 bytes 區塊補齊，padding 值 1..32 全部要能解
        bad = [c['name'] for c in v['plugin_32byte_padding']
               if not _plain_matches(svc, c['TradeInfo'], c['plain'])]
        check(f'[{label}] 解密官方外掛密文（padding 1..32 共 {len(v["plugin_32byte_padding"])} 組）',
              not bad, f'失敗：{bad[:5]}')
        check(f'[{label}] TradeSha 與官方外掛相同', lambda: all(
            svc.generate_trade_sha(c['TradeInfo']) == c['TradeSha'] for c in v['plugin_32byte_padding']))

        # 規格書 Step 2：標準 PKCS#7，加密結果須逐位元組相同
        for c in v['spec_pkcs7_encrypt']:
            check(f'[{label}] 規格書加密範例 {c["name"]}：TradeInfo 逐位元組相同',
                  lambda: svc.encrypt_trade_info(c['params']) == c['TradeInfo'])

        # 伺服器回傳：JSON 與 String 兩種 RespondType 都要解析出 Status
        for c in v['server_callbacks']:
            check(f'[{label}] 回傳明文為 {c["name"]} 格式時能取出 Status',
                  lambda: svc.decrypt_trade_info(c['TradeInfo']).get('Status') == 'SUCCESS')

        # 規格書 4.1.4 附的真實伺服器密文
        s = v['spec_server_sample']
        svc_s = type(svc)('MS127874575', s['hash_key'], s['hash_iv'])
        check(f'[{label}] 解密規格書 4.1.4 伺服器回傳範例',
              lambda: svc_s.decrypt_trade_info(s['TradeInfo']) == s['fields'])

        # 金鑰錯誤必須失敗，而不是回傳亂碼
        wrong = type(svc)('MS12345678', 'x' * 32, v['hash_iv'])
        check(f'[{label}] 金鑰錯誤時解密失敗',
              raises(lambda: wrong.decrypt_trade_info(v['server_callbacks'][0]['TradeInfo'])))

        cc = v['check_code']
        check(f'[{label}] CheckCode 與規格書 4.1.5 相同',
              lambda: svc.generate_check_code(amt=cc['params']['Amt'], merchant_id=cc['params']['MerchantID'],
                                      merchant_order_no=cc['params']['MerchantOrderNo'],
                                      trade_no=cc['params']['TradeNo']) == cc['expected'])
        cv = v['check_value']
        svc_cv = type(svc)(cv['MerchantID'], v['hash_key'], v['hash_iv'])
        check(f'[{label}] CheckValue 與規格書 4.1.6 相同',
              lambda: svc_cv.generate_check_value(cv['Amt'], cv['MerchantOrderNo']) == cv['expected'])

    # 完整回呼流程：JSON 模式的 NotifyURL 必須解析出成功狀態
    svc = services['newebpay']
    cb = next(c for c in v['server_callbacks'] if c['name'] == 'json')
    def _callback_ok():
        parsed = svc.parse_callback({'TradeInfo': cb['TradeInfo'], 'TradeSha': cb['TradeSha']})
        return parsed.status == 'SUCCESS' and parsed.amt == 100 and parsed.trade_no == '26092312000012345'
    check('[newebpay] parse_callback 解析 JSON 回傳', _callback_ok)

    lh = v['logistics_hash_data']
    lgs = load_module('taiwan-logistics/examples/newebpay-logistics-cvs-example.py')
    svc = lgs.NewebPayCVSLogistics('MS12345678', lh['hash_key'], lh['hash_iv'])
    check('[newebpay 物流] HashData 與規格書 NDNS 範例結果相同',
          lambda: svc.generate_hash_data(lh['EncryptData']) == lh['expected'])
    plain = v['plugin_32byte_padding'][-1]
    svc2 = lgs.NewebPayCVSLogistics('MS12345678', v['hash_key'], v['hash_iv'])
    check('[newebpay 物流] 解密可處理 32-byte padding（pad=32）',
          lambda: svc2.aes_decrypt(plain['TradeInfo']) == plain['plain'])


# ---------------------------------------------------------------------------
# 4. 綠界 ECPay
# ---------------------------------------------------------------------------

def test_ecpay():
    v = load_vectors('ecpay')
    print(f'\n4. 綠界 ECPay（標準答案出處：{v["source"]["name"]}；{v["source"]["cross_checked"]}）')

    pay = load_module('taiwan-payment/examples/ecpay-payment-example.py')
    lgs = load_module('taiwan-logistics/examples/ecpay-logistics-cvs-example.py')
    inv = load_module('taiwan-invoice/examples/ecpay-invoice-example.py')

    p = v['payment_checkmacvalue_sha256']
    svc = pay.ECPayPaymentService('3002607', p['hash_key'], p['hash_iv'])
    for c in p['cases']:
        check(f'[金流 SHA256] {c["name"]}：CheckMacValue 與官方 SDK 相同',
              lambda: svc.generate_check_mac_value(c['params']) == c['expected'])
    cb = next(c for c in p['cases'] if c['name'] == 'callback')
    posted = dict(cb['params'], CheckMacValue=cb['expected'])
    check('[金流] 驗證回呼：正確值通過', lambda: svc.verify_check_mac_value(dict(posted)))
    check('[金流] 驗證回呼：竄改金額被拒絕',
          lambda: not svc.verify_check_mac_value(dict(posted, TradeAmt='1')))
    check('[金流] 驗證回呼不會修改呼叫端的 dict',
          lambda: (svc.verify_check_mac_value(posted), 'CheckMacValue' in posted)[1])

    l = v['logistics_checkmacvalue_md5']
    client = lgs.ECPayLogistics('2000132', l['hash_key'], l['hash_iv'])
    for c in l['cases']:
        check(f'[物流 MD5] {c["name"]}：CheckMacValue 與官方 SDK 相同',
              lambda: client.create_check_mac_value(c['params']) == c['expected'])
    sc = next(c for c in l['cases'] if c['name'] == 'status_callback')
    check('[物流] 驗證狀態通知', lambda: client.verify_check_mac_value(dict(sc['params'], CheckMacValue=sc['expected'])))

    a = v['invoice_aes']
    isvc = inv.ECPayInvoiceService('2000132', a['hash_key'], a['hash_iv'])
    check('[發票 AES] 加密結果與官方 SDK 逐位元組相同',
          lambda: isvc.encrypt_data(a['issue_data']) == a['issue_encrypted'])
    check('[發票 AES] 可解密官方 SDK 密文', lambda: isvc.decrypt_data(a['issue_encrypted']) == a['issue_data'])
    check('[發票 AES] 回應含空白時正確還原（須用 unquote_plus）',
          lambda: isvc.decrypt_data(a['response_encrypted']) == a['response_data'])
    req = isvc.build_request({'MerchantID': '2000132'}, timestamp=1758600000)
    check('[發票] 請求帶 RqHeader.Revision=3.0.0', req['RqHeader'].get('Revision') == '3.0.0')


def _plain_matches(svc, trade_info, plain):
    """decrypt_trade_info 會解析成 dict，這裡比對解析結果與原始明文解析結果"""
    import urllib.parse
    expected = {k: v[0] for k, v in urllib.parse.parse_qs(plain, keep_blank_values=True).items()}
    try:
        return svc.decrypt_trade_info(trade_info) == expected
    except Exception:
        return False


def main():
    print('=' * 60)
    print('範例程式差分驗證')
    print('=' * 60)

    try:
        import Crypto  # noqa: F401
    except ImportError:
        print('缺少 pycryptodome：pip install -r requirements-dev.txt')
        return 1

    test_imports()
    for section in (test_payuni, test_newebpay, test_ecpay):
        try:
            section()
        except Exception as e:  # noqa: BLE001 - 單一區段炸掉不能讓其餘區段不跑
            import traceback
            check(f'{section.__name__} 執行中斷', False, ''.join(
                traceback.format_exception_only(type(e), e)).strip())

    print('\n' + '=' * 60)
    if failed:
        print(f'[FAIL] {failed} 項未通過')
        return 1
    print('[DONE] 全部通過')
    return 0


if __name__ == '__main__':
    sys.exit(main())
