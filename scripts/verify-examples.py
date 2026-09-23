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
        sc = v['server_check_code']
        svc_sc = type(svc)(sc['params']['MerchantID'], sc['hash_key'], sc['hash_iv'])
        check(f'[{label}] CheckCode 與規格書中「伺服器實際回傳」的值相同',
              lambda: svc_sc.generate_check_code(amt=sc['params']['Amt'], merchant_id=sc['params']['MerchantID'],
                                         merchant_order_no=sc['params']['MerchantOrderNo'],
                                         trade_no=sc['params']['TradeNo']) == sc['expected'])
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

    o = load_vectors('opay')
    oc = o['cases'][0]
    check('[金流] 歐付寶官方文件的 CheckMacValue 計算範例（同源演算法）',
          lambda: pay.ECPayPaymentService('2000132', o['hash_key'], o['hash_iv'])
          .generate_check_mac_value(oc['params']) == oc['expected'])

    a = v['invoice_aes']
    isvc = inv.ECPayInvoiceService('2000132', a['hash_key'], a['hash_iv'])
    check('[發票 AES] 加密結果與官方 SDK 逐位元組相同',
          lambda: isvc.encrypt_data(a['issue_data']) == a['issue_encrypted'])
    check('[發票 AES] 可解密官方 SDK 密文', lambda: isvc.decrypt_data(a['issue_encrypted']) == a['issue_data'])
    check('[發票 AES] 回應含空白時正確還原（須用 unquote_plus）',
          lambda: isvc.decrypt_data(a['response_encrypted']) == a['response_data'])
    req = isvc.build_request({'MerchantID': '2000132'}, timestamp=1758600000)
    check('[發票] 請求帶 RqHeader.Revision=3.0.0', req['RqHeader'].get('Revision') == '3.0.0')


# ---------------------------------------------------------------------------
# 4b. ezPay 電子發票
# ---------------------------------------------------------------------------

def test_ezpay_invoice():
    v = load_vectors('ezpay-invoice')
    print(f'\n4b. ezPay 電子發票（標準答案出處：{v["sources"]["plugin"]}；{v["sources"]["spec"]}）')
    mod = load_module('taiwan-invoice/examples/ezpay-invoice-example.py')
    svc = mod.EzpayInvoiceService('3622183', v['hash_key'], v['hash_iv'])
    for c in v['plugin_encrypt']:
        check(f'[ezPay 發票] {c["name"]}：PostData_ 與 RY 外掛逐位元組相同',
              lambda: svc._encrypt_post_data(c['params']) == c['PostData_'])
    check('[ezPay 發票] 規格書附件一的 32-byte padding 密文可還原為同一組參數（伺服器端等價）',
          lambda: _ezpay_plain(v) == dict(v['spec_encrypt']['params']))
    cc = v['check_code']
    check('[ezPay 發票] CheckCode 與規格書附件二印出值相同', lambda: svc._check_code(cc['params']) == cc['expected'])
    check('[ezPay 發票] verify_check_code 接受正確值、拒絕竄改',
          lambda: svc.verify_check_code(dict(cc['params'], CheckCode=cc['expected']))
          and not svc.verify_check_code(dict(cc['params'], TotalAmt='1', CheckCode=cc['expected'])))


def _ezpay_plain(v):
    import urllib.parse
    from Crypto.Cipher import AES
    data = AES.new(v['hash_key'].encode(), AES.MODE_CBC, v['hash_iv'].encode()).decrypt(
        bytes.fromhex(v['spec_encrypt']['PostData_']))
    return dict(urllib.parse.parse_qsl(data[:-data[-1]].decode(), keep_blank_values=True))


def test_smilepay():
    v = load_vectors('smilepay')
    print(f'\n4c. SmilePay（標準答案出處：{v["source"]["name"]}）')
    mod = load_module('taiwan-payment/examples/smilepay-payment-example.py')
    cls = next(getattr(mod, n) for n in dir(mod) if hasattr(getattr(mod, n), 'calc_mid_smilepay'))
    for c in v['cases']:
        check(f'[SmilePay] {c["name"]}：Mid_smilepay 與官方外掛相同',
              lambda: str(cls.calc_mid_smilepay(c['mid'], int(c['amount']), c['smseid'])) == c['expected'])


def test_linepay():
    v = load_vectors('linepay')
    print(f'\n4d. LINE Pay（標準答案出處：{v["sources"]["sdk"]}；{v["sources"]["plugin"]}）')
    mod = load_module('taiwan-payment/examples/linepay-payment-example.py')
    cls = next(getattr(mod, n) for n in dir(mod) if hasattr(getattr(mod, n), '_sign'))
    svc = cls('1234567890', v['channel_secret'])
    for c in v['cases']:
        check(f'[LINE Pay] {c["name"]}：X-LINE-Authorization 與 SDK / 外掛相同',
              lambda: svc._sign(c['path'], c['payload'], c['nonce']) == c['expected'])


def test_opay_invoice():
    o = load_vectors('opay')['invoice_aes']
    print('\n4e. 歐付寶電子發票 AES（標準答案出處：' + o['source'] + '）')
    mod = load_module('taiwan-invoice/examples/opay-invoice-example.py')
    check("[O'Pay 發票] 加密結果與官方文件相同",
          lambda: mod.encrypt_data(o['plain'], o['hash_key'], o['hash_iv']) == o['expected'])
    check("[O'Pay 發票] 解密官方文件密文", lambda: mod.decrypt_data(o['expected'], o['hash_key'], o['hash_iv']) == o['plain'])
    inv = load_module('taiwan-invoice/examples/ecpay-invoice-example.py')
    svc = inv.ECPayInvoiceService('2000132', o['hash_key'], o['hash_iv'])
    check("[綠界發票] 同源演算法：加密結果與歐付寶官方文件相同", lambda: svc.encrypt_data(o['plain']) == o['expected'])


def test_paynow_logistics():
    v = load_vectors('paynow')
    print('\n4f. PayNow 物流（標準答案出處：' + v['source']['name'] + '）')
    mod = load_module('taiwan-logistics/examples/paynow-logistics-cvs-example.py')
    t = v['tripledes_appendix']
    svc = mod.PayNowLogisticService('28229955', '12345678', t['password'])
    check('[PayNow 物流] 3DES 與文件附錄一相同（Base64 輸出）',
          lambda: svc.encrypt_3des(t['plain']) == t['expected_base64'])
    sa = v['sha1_appendix']
    check('[PayNow 物流] SHA-1 與文件附錄二相同', lambda: svc.sha1_upper(sa['input']) == sa['expected'])
    o = v['order_example']
    order = json.loads(o['order_json'])
    check('[PayNow 物流] PassCode 與文件範例訂單相同',
          lambda: svc.passcode(order['OrderNo'], order['TotalAmount']) == order['PassCode'])

    def _order_roundtrip():
        oo = mod.LogisticOrder(
            order_no=order['OrderNo'], logistic_service=order['Logistic_service'], deliver_mode=order['DeliverMode'],
            total_amount=int(order['TotalAmount']), receiver_storeid=order['receiver_storeid'],
            receiver_storename=order['receiver_storename'], receiver_name=order['Receiver_Name'],
            receiver_phone=order['Receiver_Phone'], receiver_email=order['Receiver_Email'],
            receiver_address=order['Receiver_address'], sender_name=order['Sender_Name'],
            sender_phone=order['Sender_Phone'], sender_email=order['Sender_Email'],
            sender_address=order['Sender_address'], return_storeid=order['return_storeid'],
            remark=order['Remark'], description=order['Description'])
        return svc.encrypt_3des(svc.build_order_json(oo)) == o['expected_base64']
    check('[PayNow 物流] 以範例訂單產生的 JsonOrder 與文件密文逐字相同', _order_roundtrip)
    check('[PayNow 物流] 可解密文件密文', lambda: svc.decrypt_3des(o['expected_base64']) == o['order_json'])
    iv = v['invoice_tripledes']
    svc2 = mod.PayNowLogisticService('x', 'x', iv['trade_password'])
    check('[PayNow] 密碼補位規則（發票文件附件一：1234 → 12340000）與 3DES 結果相同',
          lambda: svc2.encrypt_3des(iv['plain']) == iv['expected_base64'])
    pv = load_vectors('paynow')['payment_passcode']
    pay = load_module('taiwan-payment/examples/paynow-payment-example.py')
    legacy = next(getattr(pay, n) for n in dir(pay) if hasattr(getattr(pay, n), 'generate_passcode_request'))
    rq, rs = pv['request'], pv['response']
    check('[PayNow 金流] 送出 PassCode 與技術文件 V1.7.1.1 範例相同',
          lambda: legacy.generate_passcode_request(rq['web_no'], rq['order_no'], rq['total_price'], rq['trade_code']) == rq['expected'])
    check('[PayNow 金流] 回傳 PassCode 驗證與技術文件範例相同',
          lambda: legacy.verify_passcode_response(rs['web_no'], rs['order_no'], rs['total_price'], rs['trade_code'],
                                                  rs['tran_status'], rs['expected']))


def test_sunpay():
    v = load_vectors('sunpay')
    print('\n4g. 紅陽 SunPay（標準答案出處：' + v['source']['name'] + '）')
    mod = load_module('taiwan-payment/examples/sunpay-payment-example.py')
    r = v['request_check_value']
    check('[SunPay] 送出的 check_value 與手冊相同', lambda: mod.make_check_value(r['payload'], v['sha2_key']) == r['expected'])
    cb = v['callback']
    check('[SunPay] 以公鑰解密手冊的回傳 rsamsg（URL-safe base64）得到未 urldecode 的字串',
          lambda: mod.decrypt_rsamsg(cb['rsamsg'], v['public_key_pem']) == cb['decrypted_encoded'])
    check('[SunPay] 回傳 check_value 驗證通過且解析出手冊明文',
          lambda: mod.parse_rsamsg(cb['rsamsg'], v['public_key_pem'], v['sha2_key'], cb['check_value']) == cb['plain'])
    check('[SunPay] check_value 錯誤時拒絕',
          raises(lambda: mod.parse_rsamsg(cb['rsamsg'], v['public_key_pem'], v['sha2_key'], '0' * 64)))
    t = v['invoice_token']
    inv = load_module('taiwan-invoice/examples/sunpay-invoice-example.py')
    check('[SunPay 發票] URLEncode 結果與手冊相同（.NET 小寫 %xx）',
          lambda: inv.dotnet_url_encode(t['plain']) == t['url_encoded'])
    check('[SunPay 發票] Token 加密與手冊範例相同',
          lambda: inv.encrypt_token(t['plain'], t['hash_key'], t['hash_iv']) == t['expected'])


def test_shopline():
    v = load_vectors('shopline')
    print('\n4h. SHOPLINE Payments（' + v['source']['name'] + '）')
    mod = load_module('taiwan-payment/examples/shopline-payment-example.py')
    svc = mod.ShoplinePaymentService('m', 'k', webhook_secret=v['sign_key'])
    for c in v['cases']:
        check(f'[Shopline] {c["name"]}：webhook sign 驗證通過',
              lambda: svc.verify_webhook(c['body'].encode('utf-8'), c['timestamp'], c['sign'],
                                         now_ms=int(c['timestamp'])))
    c = v['cases'][0]
    check('[Shopline] 竄改 body 被拒絕', lambda: not svc.verify_webhook(
        c['body'].replace('SUCCEEDED', 'FAILED').encode(), c['timestamp'], c['sign'], now_ms=int(c['timestamp'])))
    check('[Shopline] 超過容許時間被拒絕（防重放）', lambda: not svc.verify_webhook(
        c['body'].encode(), c['timestamp'], c['sign'], now_ms=int(c['timestamp']) + 10 * 60 * 1000))


def test_example_self_tests():
    """範例檔自帶的 _self_test()（多半內嵌官方文件的測試向量）必須全數通過"""
    import contextlib
    import io
    print('\n4i. 範例內建的 _self_test()（官方文件測試向量）')
    for path in sorted(glob.glob(os.path.join(ROOT, 'taiwan-*', 'examples', '*.py'))):
        rel = os.path.relpath(path, ROOT).replace(os.sep, '/')
        with open(path, encoding='utf-8') as f:
            if 'def _self_test(' not in f.read():
                continue

        def run(rel=rel):
            mod = load_module(rel)
            with contextlib.redirect_stdout(io.StringIO()):
                return mod._self_test() == 0
        check(f'{rel} _self_test() 通過', run)


# ---------------------------------------------------------------------------
# 5. 隨 skill 發布的工具腳本
# ---------------------------------------------------------------------------

def test_scripts():
    print('\n5. 工具腳本 taiwan-payment/scripts/test_payment.py')
    tp = load_module('taiwan-payment/scripts/test_payment.py')
    for platform in ('ecpay', 'newebpay', 'payuni'):
        check(f'[{platform}] 內建已知答案測試通過', lambda: tp.run_known_answer_test(platform))
    # 內建的標準答案必須就是 tests/vectors 裡官方程式產生的那一筆，避免各自漂移
    ecpay = {c['expected'] for c in load_vectors('ecpay')['payment_checkmacvalue_sha256']['cases']}
    newebpay = {c['TradeSha'] for c in load_vectors('newebpay')['spec_pkcs7_encrypt']}
    payuni = {c['HashInfo'] for c in load_vectors('payuni')['cases']}
    check('內建標準答案皆取自 tests/vectors', tp.KNOWN_ANSWERS['ecpay']['expected'] in ecpay
          and tp.KNOWN_ANSWERS['newebpay']['expected'] in newebpay
          and tp.KNOWN_ANSWERS['payuni']['expected'] in payuni)


# ---------------------------------------------------------------------------
# 6. 文件中的程式碼片段
# ---------------------------------------------------------------------------
#
# 文件裡的片段才是 AI 助理最常直接照抄的東西，過去卻完全沒被驗證（範例修好了、
# 文件仍是錯的）。在 ```python 區塊前加上 <!-- verify: <名稱> --> 即納入檢查：
# 片段會在已匯入常用模組的環境執行，再以同一份官方標準答案比對。

import re  # noqa: E402

SNIPPET_RE = re.compile(
    r'<!-- verify: ([\w -]+?) -->\r?\n```(python|typescript|ts|javascript|js|php)\r?\n(.*?)```', re.S)

# TypeScript / JavaScript 片段交給 Node 執行（Node 22 需 --experimental-strip-types 才能直接跑 TS）。
# 各驗證名稱約定的函式名稱見下方 driver；片段只要定義出這些函式即可。
JS_DRIVERS = {
    'linepay-sign': '''
const v = VECTORS.linepay
for (const c of v.cases) {
  if (signRequest(c.path, c.payload, c.nonce, v.channel_secret) !== c.expected) fail(c.name)
}''',
    'newebpay-logistics': '''
const v = VECTORS.newebpay
const lh = v.logistics_hash_data
const a: any = new NewebPayLogistics({ merchantId: 'MS12345678', hashKey: lh.hash_key, hashIV: lh.hash_iv })
if (a.generateHashData(lh.EncryptData) !== lh.expected) fail('HashData')
const b: any = new NewebPayLogistics({ merchantId: 'MS12345678', hashKey: v.hash_key, hashIV: v.hash_iv })
for (const c of v.plugin_32byte_padding) {
  if (b.aesDecrypt(c.TradeInfo) !== c.plain) fail(`${c.name} decrypt`)
}''',
    'payuni': '''
const v = VECTORS.payuni
for (const c of v.cases) {
  const r = encryptPAYUNi(c.params, v.hash_key, v.hash_iv)
  if (r.EncryptInfo !== c.EncryptInfo) fail(`${c.name} EncryptInfo`)
  if (r.HashInfo !== c.HashInfo) fail(`${c.name} HashInfo`)
  if (JSON.stringify(decryptPAYUNi(c.EncryptInfo, v.hash_key, v.hash_iv)) !== JSON.stringify(c.params)) fail(`${c.name} decrypt`)
}''',
    'newebpay': '''
const v = VECTORS.newebpay
for (const c of v.spec_pkcs7_encrypt) {
  const r = encryptNewebPay(c.params, v.hash_key, v.hash_iv)
  if (r.TradeInfo !== c.TradeInfo) fail(`${c.name} TradeInfo`)
  if (r.TradeSha !== c.TradeSha) fail(`${c.name} TradeSha`)
}
for (const c of v.plugin_32byte_padding) {
  const got = decryptNewebPay(c.TradeInfo, v.hash_key, v.hash_iv)
  if (JSON.stringify(got) !== JSON.stringify(Object.fromEntries(new URLSearchParams(c.plain)))) fail(`${c.name} decrypt`)
}
for (const c of v.server_callbacks) {
  if (decryptNewebPay(c.TradeInfo, v.hash_key, v.hash_iv).Status !== 'SUCCESS') fail(`callback ${c.name}`)
}''',
    'ecpay-cmv-sha256': '''
const v = VECTORS.ecpay.payment_checkmacvalue_sha256
for (const c of v.cases) {
  if (generateECPayCheckMacValue(c.params, v.hash_key, v.hash_iv) !== c.expected) fail(c.name)
}''',
    'ecpay-cmv-md5': '''
const v = VECTORS.ecpay.logistics_checkmacvalue_md5
const gen = typeof ECPayLogistics !== 'undefined'
  ? ((p: any) => new ECPayLogistics({ merchantId: '2000132', hashKey: v.hash_key, hashIV: v.hash_iv }).generateCheckMacValue(p))
  : ((p: any) => generateECPayCheckMacValue(p, v.hash_key, v.hash_iv))
for (const c of v.cases) {
  if (gen(c.params) !== c.expected) fail(c.name)
}''',
}


# PHP 片段：GitHub Actions 的 ubuntu-latest 內建 php；本機沒有 php 時改用 Docker php:8.2-cli。
# 片段需定義下列類別（與 references/ 中的寫法一致）。
PHP_DRIVERS = {
    'payuni': r'''
$v = $VECTORS['payuni'];
$e = new PayuniEncryption($v['hash_key'], $v['hash_iv']);
foreach ($v['cases'] as $c) {
    if ($e->encrypt($c['params']) !== $c['EncryptInfo']) fail("{$c['name']} EncryptInfo");
    if ($e->hashInfo($c['EncryptInfo']) !== $c['HashInfo']) fail("{$c['name']} HashInfo");
    if ($e->decrypt($c['EncryptInfo']) != $c['params']) fail("{$c['name']} decrypt");
}''',
    'newebpay': r'''
$v = $VECTORS['newebpay'];
$cls = class_exists('NewebPayEncryption') ? 'NewebPayEncryption' : 'EzPayEncryption';
$e = new $cls($v['hash_key'], $v['hash_iv']);
foreach ($v['spec_pkcs7_encrypt'] as $c) {
    if ($e->encrypt($c['params']) !== $c['TradeInfo']) fail("{$c['name']} TradeInfo");
    if ($e->tradeSha($c['TradeInfo']) !== $c['TradeSha']) fail("{$c['name']} TradeSha");
}
foreach ($v['plugin_32byte_padding'] as $c) {
    parse_str($c['plain'], $want);
    if ($e->decrypt($c['TradeInfo']) != $want) fail("{$c['name']} decrypt");
}
foreach ($v['server_callbacks'] as $c) {
    if (($e->decrypt($c['TradeInfo'])['Status'] ?? null) !== 'SUCCESS') fail("callback {$c['name']}");
}''',
}


def _php_command(path):
    import shutil
    php = shutil.which('php')
    if php:
        return [php, '-d', 'display_errors=stderr', path]
    docker = shutil.which('docker')
    if not docker:
        raise RuntimeError('找不到 php 或 docker，無法驗證 PHP 片段')
    host_dir, name = os.path.split(path)
    return [docker, 'run', '--rm', '-v', f'{host_dir}:/w', 'php:8.2-cli',
            'php', '-d', 'display_errors=stderr', f'/w/{name}']


def _run_php_snippet(name, code, label):
    import subprocess
    import tempfile
    vectors = {n: load_vectors(n) for n in ('payuni', 'newebpay', 'ecpay')}
    body = re.sub(r'^\s*<\?php', '', code, count=1)
    program = ('<?php\n' + body + '\n'
               + "$VECTORS = json_decode(file_get_contents(__DIR__ . '/vectors.json'), true);\n"
               + '$failures = [];\nfunction fail($m) { global $failures; $failures[] = $m; }\n'
               + PHP_DRIVERS[name] + '\n'
               + 'if ($failures) { echo json_encode($failures); exit(1); }\n')
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, 'snippet.php')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(program)
        with open(os.path.join(tmp, 'vectors.json'), 'w', encoding='utf-8') as f:
            json.dump(vectors, f, ensure_ascii=False)
        env = dict(os.environ, MSYS_NO_PATHCONV='1')
        proc = subprocess.run(_php_command(path), capture_output=True, text=True, encoding='utf-8', env=env)
    if proc.returncode != 0:
        raise AssertionError(f'{label}: {(proc.stdout + proc.stderr).strip()[:300]}')
    return True


def _run_js_snippet(name, code, label):
    import shutil
    import subprocess
    import tempfile
    node = shutil.which('node')
    if not node:
        raise RuntimeError('找不到 node，無法驗證 TypeScript / JavaScript 片段')
    vectors = {n: load_vectors(n) for n in ('payuni', 'newebpay', 'ecpay', 'linepay')}
    prelude = '' if re.search(r"^import crypto\b", code, re.M) else "import crypto from 'crypto'\n"
    program = (prelude + code + '\n'
               + 'const VECTORS = ' + json.dumps(vectors, ensure_ascii=False) + '\n'
               + 'const failures = []\nfunction fail(m) { failures.push(m) }\n'
               + JS_DRIVERS[name] + '\n'
               + 'if (failures.length) { console.log(JSON.stringify(failures)); process.exit(1) }\n')
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, 'snippet.mts')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(program)
        proc = subprocess.run([node, '--experimental-strip-types', '--no-warnings', path],
                              capture_output=True, text=True, encoding='utf-8')
    if proc.returncode != 0:
        raise AssertionError(f'{label}: {(proc.stdout + proc.stderr).strip()[:300]}')
    return True


def _snippet_namespace():
    import base64, hashlib, hmac, json as _json, urllib.parse  # noqa: E401
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad, unpad
    return {'base64': base64, 'hashlib': hashlib, 'hmac': hmac, 'json': _json,
            'urllib': urllib, 'AES': AES, 'pad': pad, 'unpad': unpad}


def _check_snippet_payuni(ns):
    v = load_vectors('payuni')
    key, iv = v['hash_key'], v['hash_iv']
    if 'PayuniEncryption' in ns:
        e = ns['PayuniEncryption'](key, iv)
        enc, hsh, dec = e.encrypt, e.hash_info, getattr(e, 'decrypt', None)
    else:
        enc = lambda p: ns['generate_encrypt_info'](p, key, iv)  # noqa: E731
        hsh = lambda x: ns['generate_hash_info'](x, key, iv)  # noqa: E731
        dec = None
    return all(enc(c['params']) == c['EncryptInfo'] and hsh(c['EncryptInfo']) == c['HashInfo']
               and (dec is None or dec(c['EncryptInfo']) == c['params']) for c in v['cases'])


def _check_snippet_newebpay(ns):
    v = load_vectors('newebpay')
    key, iv = v['hash_key'], v['hash_iv']
    cls = ns.get('NewebPayEncryption') or ns.get('EzPayEncryption')
    if cls:
        # 類別寫法：NewebPayEncryption / EzPayEncryption(key, iv).encrypt / decrypt / trade_sha
        e = cls(key, iv)
        ns = dict(ns,
                  generate_trade_info=lambda p, k, i: e.encrypt(p),
                  generate_trade_sha=lambda t, k, i: e.trade_sha(t),
                  decrypt_trade_info=lambda t, k, i: e.decrypt(t))
    ok = all(ns['generate_trade_info'](c['params'], key, iv) == c['TradeInfo'] and
             ns['generate_trade_sha'](c['TradeInfo'], key, iv) == c['TradeSha']
             for c in v['spec_pkcs7_encrypt'])
    if 'decrypt_trade_info' in ns:
        import urllib.parse
        ok = ok and all(
            ns['decrypt_trade_info'](c['TradeInfo'], key, iv) ==
            dict(urllib.parse.parse_qsl(c['plain'], keep_blank_values=True))
            for c in v['plugin_32byte_padding'])
        ok = ok and all(ns['decrypt_trade_info'](c['TradeInfo'], key, iv).get('Status') == 'SUCCESS'
                        for c in v['server_callbacks'])
    return ok


def _check_snippet_ecpay_cmv(section):
    def run(ns):
        p = load_vectors('ecpay')[section]
        if 'ECPayLogistics' in ns:   # 類別寫法
            client = ns['ECPayLogistics']('2000132', p['hash_key'], p['hash_iv'])
            fn = lambda params, k, i: client.generate_check_mac_value(params)  # noqa: E731
        else:
            fn = ns['generate_check_mac_value']
        return all(fn(c['params'], p['hash_key'], p['hash_iv']) == c['expected'] for c in p['cases'])
    return run


def _check_snippet_opay_cmv(ns):
    v = load_vectors('opay')
    fn = ns.get('gen_check_mac_value') or ns['generate_check_mac_value']
    return all(fn(c['params'], v['hash_key'], v['hash_iv']) == c['expected'] for c in v['cases'])


def _check_snippet_newebpay_logistics(ns):
    v = load_vectors('newebpay')
    lh = v['logistics_hash_data']
    c = ns['NewebPayLogistics']('MS12345678', lh['hash_key'], lh['hash_iv'])
    if c.generate_hash_data(lh['EncryptData']) != lh['expected']:
        return False
    c = ns['NewebPayLogistics']('MS12345678', v['hash_key'], v['hash_iv'])
    return all(c.aes_decrypt(x['TradeInfo']) == x['plain'] for x in v['plugin_32byte_padding'])


def _check_snippet_smilepay_mid(ns):
    v = load_vectors('smilepay')
    return all(str(ns['calc_mid_smilepay'](c['mid'], int(c['amount']), c['smseid'])) == c['expected']
               for c in v['cases'])


def _check_snippet_linepay(ns):
    v = load_vectors('linepay')
    return all(ns['sign_request'](c['path'], c['payload'], c['nonce'], v['channel_secret']) == c['expected']
               for c in v['cases'])


def _check_snippet_paynow_3des(ns):
    v = load_vectors('paynow')
    t, o = v['tripledes_appendix'], v['order_example']
    key = '1234567890' + o['password'] + '123456'
    return (ns['triple_des_encrypt'](t['plain'], t['key']) == t['expected_base64']
            and ns['triple_des_encrypt'](o['order_json'], key) == o['expected_base64'])


def _check_snippet_paynow_passcode(ns):
    v = load_vectors('paynow')
    order = json.loads(v['order_example']['order_json'])
    return (ns['generate_pass_code'](v['sha1_appendix']['input']) == v['sha1_appendix']['expected']
            and ns['generate_pass_code'](order['user_account'], order['OrderNo'], order['TotalAmount'],
                                         order['apicode']) == order['PassCode'])


SNIPPET_CHECKERS = {
    'paynow-3des': _check_snippet_paynow_3des,
    'paynow-passcode': _check_snippet_paynow_passcode,
    'linepay-sign': _check_snippet_linepay,
    'smilepay-mid': _check_snippet_smilepay_mid,
    'newebpay-logistics': _check_snippet_newebpay_logistics,
    'opay-cmv': _check_snippet_opay_cmv,
    'payuni': _check_snippet_payuni,
    'newebpay': _check_snippet_newebpay,
    'ecpay-cmv-sha256': _check_snippet_ecpay_cmv('payment_checkmacvalue_sha256'),
    'ecpay-cmv-md5': _check_snippet_ecpay_cmv('logistics_checkmacvalue_md5'),
}


def test_doc_snippets():
    print('\n6. 文件中標記 <!-- verify --> 的程式碼片段')
    found = 0
    for path in sorted(glob.glob(os.path.join(ROOT, 'taiwan-*', '**', '*.md'), recursive=True)):
        rel = os.path.relpath(path, ROOT).replace(os.sep, '/')
        with open(path, encoding='utf-8') as f:
            text = f.read()
        for m in SNIPPET_RE.finditer(text):
            found += 1
            names, lang, code = m.group(1).split(), m.group(2), m.group(3)
            line = text[:m.start()].count('\n') + 1
            is_js = lang in ('typescript', 'ts', 'javascript', 'js')
            is_php = lang == 'php'
            registry = JS_DRIVERS if is_js else PHP_DRIVERS if is_php else SNIPPET_CHECKERS
            # 一個片段可同時標記多個驗證名稱，例如 <!-- verify: ecpay-cmv-sha256 newebpay payuni -->
            for name in names:
                label = f'{rel}:{line} [{name}/{lang}]'
                if name not in registry:
                    check(f'{label} 未知的驗證名稱', False)
                    continue

                if is_php:
                    check(label, lambda code=code, name=name, label=label: _run_php_snippet(name, code, label))
                    continue
                if is_js:
                    check(label, lambda code=code, name=name, label=label: _run_js_snippet(name, code, label))
                    continue

                def run(code=code, name=name, line=line):
                    ns = _snippet_namespace()
                    exec(compile(code, f'{rel}:{line}', 'exec'), ns)  # noqa: S102 - 執行 repo 內自有文件
                    return SNIPPET_CHECKERS[name](ns)
                check(label, run)
    check(f'共找到 {found} 個受驗證片段（應大於 0）', found > 0)


# ---------------------------------------------------------------------------
# 7. 發票服務產生器（generate-invoice-service.py）
# ---------------------------------------------------------------------------
#
# 產生器輸出的是骨架。過去骨架的 issue / void 會「什麼都沒做就回傳成功」，
# 照抄的人會以為發票已開立 / 作廢。這裡確認：每個 provider 都產得出來、
# Python 版可載入且未實作的步驟會拋錯、TypeScript 版語法正確、MOF 會被拒絕。

def test_invoice_generator():
    import csv as _csv
    import shutil
    import subprocess
    import tempfile
    print('\n7. 發票服務產生器 taiwan-invoice/scripts/generate-invoice-service.py')
    script = os.path.join(ROOT, 'taiwan-invoice', 'scripts', 'generate-invoice-service.py')
    with open(os.path.join(ROOT, 'taiwan-invoice', 'data', 'providers.csv'), encoding='utf-8') as f:
        providers = [r['provider'] for r in _csv.DictReader(f)]
    node = shutil.which('node')
    env = dict(os.environ, PYTHONIOENCODING='utf-8')
    with tempfile.TemporaryDirectory() as tmp:
        for provider in providers:
            if provider.lower() == 'mof':
                proc = subprocess.run([sys.executable, script, provider, '--output', tmp],
                                      capture_output=True, text=True, encoding='utf-8', env=env)
                check('[MOF] 拒絕產生開立服務（MOF 不能開立發票）', proc.returncode != 0)
                continue
            for lang in ('python', 'typescript'):
                proc = subprocess.run([sys.executable, script, provider, '--lang', lang, '--output', tmp],
                                      capture_output=True, text=True, encoding='utf-8', env=env)
                check(f'[{provider}/{lang}] 可產生', proc.returncode == 0, proc.stderr.strip()[-200:])
            py = os.path.join(tmp, f'{provider.lower()}-invoice-service.py')

            def stub_raises(py=py):
                spec = importlib.util.spec_from_file_location('gen_' + os.path.basename(py)[:-3].replace('-', '_'), py)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                cls = next(getattr(mod, n) for n in dir(mod) if n.endswith('InvoiceService'))
                svc = cls()
                for call in (lambda: svc.issue_invoice('1', 'k' * 16, 'i' * 16, mod.InvoiceIssueData(order_id='A')),
                             lambda: svc.void_invoice('1', 'k' * 16, 'i' * 16, 'AB12345678', 'x')):
                    try:
                        call()
                        return False          # 未實作卻回傳了結果
                    except NotImplementedError:
                        pass
                return True
            check(f'[{provider}/python] 可載入，未實作的開立 / 作廢會拋錯而不是回傳成功', stub_raises)

            ts = os.path.join(tmp, f'{provider.lower()}-invoice-service.ts')
            if node and os.path.exists(ts):
                mts = ts[:-3] + '.mts'
                shutil.copy(ts, mts)
                proc = subprocess.run([node, '--experimental-strip-types', '--no-warnings', mts],
                                      capture_output=True, text=True, encoding='utf-8')
                check(f'[{provider}/typescript] 語法正確可載入', proc.returncode == 0, proc.stderr.strip()[:200])


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
    for section in (test_payuni, test_newebpay, test_ecpay, test_ezpay_invoice, test_smilepay, test_linepay, test_opay_invoice, test_paynow_logistics, test_sunpay, test_shopline, test_example_self_tests, test_scripts, test_doc_snippets, test_invoice_generator):
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
