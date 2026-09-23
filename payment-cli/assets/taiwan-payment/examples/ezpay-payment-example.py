#!/usr/bin/env python3
"""
ezPay 簡單付 金流 Python 範例（依官方技術串接手冊，已與手冊範例逐位元組比對）

官方 API 文件頁：https://www.ezpay.com.tw/info/Service_intro/api_document/member
參考文件：taiwan-payment/references/ezpay-payment-api.md

ezPay 簡單付是持有電子支付執照的機構（簡單行動支付股份有限公司），官方目前提供兩組金流 API，
演算法相同、欄位與網址完全不同：

1. 電子支付平台（標準版）— API_E_wallet_ezPay 1.0.0（文件 W1.0.2，2026-04-20）
   境內收款：ezPay 電子帳戶、約定連結存款帳戶、ezPay 約定信用卡、TWQR（台灣 Pay、街口、全支付…）。
   POST application/x-www-form-urlencoded 到 https://(c)payment.ezpay.com.tw/API/Twqr/<APIID>
   外層欄位：APIID、Version=1.0、UID（商店代號）、EncryptData、HashData
   EncryptData = hex(AES-256-CBC(urlencode(參數), HashKey, HashIV))，PKCS#7 以 32 bytes 為區塊
   HashData    = SHA256("HashKey={HashKey}&{EncryptData}&HashIV={HashIV}") 轉大寫
   回應／通知的 EncryptData 解密後是 urlencoded 字串，Result 以 Result[欄位] 攤平。

2. 跨境網路交易（支付寶 ALIPAY／微信 WECHAT）— API_Cross_Trans_ezPay 1.0.1、查詢 1.0.1、退款 1.0.3
   MPG 形式：MerchantID、Version、TradeInfo、TradeSha → https://(c)payment.ezpay.com.tw/MPG/mpg_gateway
   查詢 QueryInfo/QuerySha（Version 1.0）、退款 RefundInfo/RefundSha（Version 2.1），回應解密後是 JSON。

依賴：pip install pycryptodome requests
"""

import hashlib
import hmac
import json
import time
import urllib.parse
from typing import Any, Dict, List, Optional, Tuple, Union

try:
    from Crypto.Cipher import AES
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

Params = Union[Dict[str, Any], List[Tuple[str, Any]]]

BLOCK = 32   # 手冊：AES256 CBC、BlockSize=32、PKCS#7 —— 補齊到 32 bytes 的倍數，不是 AES 的 16


# ----------------------------------------------------------------------------
# 共用演算法（兩組 API 相同）
# ----------------------------------------------------------------------------

def _pad(data: bytes) -> bytes:
    n = BLOCK - len(data) % BLOCK
    return data + bytes([n]) * n


def _unpad(data: bytes) -> bytes:
    n = data[-1] if data else 0
    if not 1 <= n <= BLOCK or data[-n:] != bytes([n]) * n:
        raise ValueError('解密失敗：padding 不正確（金鑰錯誤或資料被竄改）')
    return data[:-n]


def encrypt(plain: str, hash_key: str, hash_iv: str) -> str:
    if not HAS_CRYPTO:
        raise ImportError('需要安裝 pycryptodome: pip install pycryptodome')
    cipher = AES.new(hash_key.encode('utf-8'), AES.MODE_CBC, hash_iv.encode('utf-8'))
    return cipher.encrypt(_pad(plain.encode('utf-8'))).hex()


def decrypt(cipher_hex: str, hash_key: str, hash_iv: str) -> str:
    if not HAS_CRYPTO:
        raise ImportError('需要安裝 pycryptodome: pip install pycryptodome')
    cipher = AES.new(hash_key.encode('utf-8'), AES.MODE_CBC, hash_iv.encode('utf-8'))
    return _unpad(cipher.decrypt(bytes.fromhex(cipher_hex.strip()))).decode('utf-8')


def hash_data(cipher_hex: str, hash_key: str, hash_iv: str) -> str:
    """HashData / TradeSha / QuerySha / RefundSha 共用：SHA256("HashKey=..&密文&HashIV=..") 大寫"""
    raw = f'HashKey={hash_key}&{cipher_hex}&HashIV={hash_iv}'
    return hashlib.sha256(raw.encode('utf-8')).hexdigest().upper()


def verify_hash(cipher_hex: str, received: str, hash_key: str, hash_iv: str) -> bool:
    return hmac.compare_digest(hash_data(cipher_hex, hash_key, hash_iv), (received or '').strip().upper())


def unflatten(fields: Dict[str, str]) -> Dict[str, Any]:
    """{'Result[TradeNo]': 'EP..', 'Status': 'SUCCESS'} -> {'Result': {'TradeNo': 'EP..'}, 'Status': 'SUCCESS'}"""
    out: Dict[str, Any] = {}
    for key, value in fields.items():
        if '[' in key and key.endswith(']'):
            outer, inner = key[:-1].split('[', 1)
            out.setdefault(outer, {})[inner] = value
        else:
            out[key] = value
    return out


# ----------------------------------------------------------------------------
# 1. 電子支付平台（TWQR 等境內收款）
# ----------------------------------------------------------------------------

class EzPayWalletService:
    """
    ezPay 簡單付 電子支付平台（標準版）

    APIID 與用途（手冊「串接方法」）：
        SCreateTWQR     訂單建立           SUpdateTWQR     訂單修改及取消
        SPayTWQRNotify  交易結果背景通知   STWQRReturn     交易結果轉導暨前景通知
        STWQRRefund     交易退款           SGetTWQR        訂單暨交易結果查詢
        SGetTWQRRefund  退款查詢

    UID 為商店代號（手冊範例 PG300000725648）；Hash Key / IV 於 ezPay 後台「管理商店/商店資料設定」取得。
    """

    TEST_BASE = 'https://cpayment.ezpay.com.tw/API/Twqr/'
    PROD_BASE = 'https://payment.ezpay.com.tw/API/Twqr/'
    VERSION = '1.0'

    # Result[OrderStatus]（查詢 API 的完整列表；4、5 皆為全額退款）
    ORDER_STATUS = {
        '1': '待付款', '2': '已付款', '3': '部分退款', '4': '全額退款', '5': '全額退款',
        '6': '付款失敗', '7': '等候付款結果中', '8': '訂單逾時未付款', '9': '刪除訂單',
        '10': '暫時無法確定訂單付款狀態',
    }
    REFUND_STATUS = {'1': '退款成功', '2': '退款失敗', '3': '退款處理中', '9': '無法確認退款請求狀態'}

    def __init__(self, uid: str, hash_key: str, hash_iv: str, is_production: bool = False, timeout: int = 30):
        self.uid = uid
        self.hash_key = hash_key
        self.hash_iv = hash_iv
        self.base_url = self.PROD_BASE if is_production else self.TEST_BASE
        self.timeout = timeout

    # -- 封包 ---------------------------------------------------------------

    def build_request(self, apiid: str, params: Params, timestamp: Optional[int] = None) -> Dict[str, str]:
        """
        組出要 POST 的表單。EncryptData 內含 TimeStamp、APIID、Version、UID 與各 API 參數。

        params 可傳 dict 或 (key, value) list；手冊附件一的密文依賴參數順序，要重現時請傳 list。
        """
        items = list(params.items()) if isinstance(params, dict) else list(params)
        head = [('TimeStamp', str(timestamp or int(time.time()))), ('APIID', apiid),
                ('Version', self.VERSION), ('UID', self.uid)]
        given = {k for k, _ in items}
        body = [kv for kv in head if kv[0] not in given] + [(k, '' if v is None else str(v)) for k, v in items]
        encrypt_data = encrypt(urllib.parse.urlencode(body), self.hash_key, self.hash_iv)
        # 註：手冊附件一 Step5 的範例寫成 EncryptData_ / HashData_，但各 API 的參數表都是 EncryptData / HashData。
        return {
            'APIID': apiid,
            'Version': self.VERSION,
            'UID': self.uid,
            'EncryptData': encrypt_data,
            'HashData': hash_data(encrypt_data, self.hash_key, self.hash_iv),
        }

    def parse_response(self, payload: Dict[str, str]) -> Dict[str, Any]:
        """
        驗證並解開 API 回應或 Notify / Return 通知（外層 Status、Message、EncryptData、HashData）。

        HashData 不符時丟 ValueError —— 未驗章的資料不可用來更新訂單。
        """
        encrypted = payload.get('EncryptData', '')
        if not encrypted:
            # 外層錯誤（例如 SCTE0009 HashData 錯誤）不一定帶 EncryptData
            return {'Status': payload.get('Status'), 'Message': payload.get('Message'), 'Result': {}}
        if not verify_hash(encrypted, payload.get('HashData', ''), self.hash_key, self.hash_iv):
            raise ValueError('HashData 驗證失敗')
        plain = decrypt(encrypted, self.hash_key, self.hash_iv)
        return unflatten(dict(urllib.parse.parse_qsl(plain, keep_blank_values=True)))

    def _post(self, apiid: str, params: Params) -> Dict[str, Any]:
        if not HAS_REQUESTS:
            raise ImportError('需要安裝 requests: pip install requests')
        resp = requests.post(self.base_url + apiid, data=self.build_request(apiid, params), timeout=self.timeout)
        resp.raise_for_status()
        return self.parse_response(resp.json())

    # -- API ----------------------------------------------------------------

    def create_order(self, merchant_order_no: str, amount: int, item_desc: str,
                     notify_url: str = '', return_url: str = '', client_back_url: str = '',
                     mode: int = 1, lifetime_seconds: Optional[int] = None) -> Dict[str, Any]:
        """
        SCreateTWQR：Mode 1 = 商店指定金額並帶唯一商店訂單編號。
        成功時 Result 內有 PaymentPageURL（支付頁）與 TWQRCode（給其他 TWQR 錢包掃描）。
        """
        params: List[Tuple[str, Any]] = [('Mode', mode), ('MerchantOrderNo', merchant_order_no)]
        if lifetime_seconds:
            params.append(('TWQRLifeTime', lifetime_seconds))
        for key, value in (('NotifyURL', notify_url), ('ReturnURL', return_url), ('ClientBackURL', client_back_url)):
            if value:
                params.append((key, value))
        params += [('Currency', 'TWD'), ('OrderAmt', amount), ('ItemDesc', item_desc)]
        return self._post('SCreateTWQR', params)

    def cancel_order(self, trade_no: str, ptoken: str) -> Dict[str, Any]:
        """SUpdateTWQR UpdateAction=1：刪除仍為待付款的訂單"""
        return self._post('SUpdateTWQR', [('TradeNo', trade_no), ('Ptoken', ptoken), ('UpdateAction', 1)])

    def query_order(self, merchant_order_no: str = '', trade_no: str = '') -> Dict[str, Any]:
        """SGetTWQR：MerchantOrderNo 與 TradeNo 擇一（同時帶入會回 SGTR0116）"""
        if bool(merchant_order_no) == bool(trade_no):
            raise ValueError('MerchantOrderNo 與 TradeNo 必須擇一帶入')
        key, value = ('TradeNo', trade_no) if trade_no else ('MerchantOrderNo', merchant_order_no)
        return self._post('SGetTWQR', [(key, value)])

    def refund(self, merchant_refund_no: str, amount: int, merchant_order_no: str = '',
               trade_no: str = '') -> Dict[str, Any]:
        """STWQRRefund：RefundBarCode / MerchantOrderNo / TradeNo 擇一；MerchantRefundNo 不可重複"""
        if bool(merchant_order_no) == bool(trade_no):
            raise ValueError('MerchantOrderNo 與 TradeNo 必須擇一帶入')
        key, value = ('TradeNo', trade_no) if trade_no else ('MerchantOrderNo', merchant_order_no)
        return self._post('STWQRRefund', [('MerchantRefundNo', merchant_refund_no), (key, value),
                                          ('RefundType', 1), ('Currency', 'TWD'), ('RefundAmt', amount)])

    def query_refund(self, merchant_refund_no: str = '', rtoken: str = '') -> Dict[str, Any]:
        """SGetTWQRRefund：Rtoken 與 MerchantRefundNo 擇一"""
        if bool(merchant_refund_no) == bool(rtoken):
            raise ValueError('Rtoken 與 MerchantRefundNo 必須擇一帶入')
        key, value = ('Rtoken', rtoken) if rtoken else ('MerchantRefundNo', merchant_refund_no)
        return self._post('SGetTWQRRefund', [(key, value)])


# ----------------------------------------------------------------------------
# 2. 跨境網路交易（支付寶／微信）
# ----------------------------------------------------------------------------

class EzPayCrossBorderService:
    """
    ezPay 跨境網路交易：以前景 Form Post 送到 MPG，NotifyURL 收背景通知。

    支付工具只有 ALIPAY、WECHAT（手冊附件一）；商店屬性需選「跨境網路商店」。
    """

    TEST_HOST = 'https://cpayment.ezpay.com.tw'
    PROD_HOST = 'https://payment.ezpay.com.tw'

    def __init__(self, merchant_id: str, hash_key: str, hash_iv: str, is_production: bool = False,
                 timeout: int = 30):
        self.merchant_id = merchant_id
        self.hash_key = hash_key
        self.hash_iv = hash_iv
        self.host = self.PROD_HOST if is_production else self.TEST_HOST
        self.timeout = timeout

    def build_mpg_form(self, merchant_order_no: str, amt: int, item_desc: str,
                       timestamp: Optional[int] = None, **optional: Any) -> Dict[str, Any]:
        """回傳 {'action': URL, 'fields': {...}}，前端以 <form method=post> 自動送出。optional：CrossMobile、TradeLimit、ClientBackURL"""
        params = [('MerchantID', self.merchant_id), ('TimeStamp', str(timestamp or int(time.time()))),
                  ('Version', '1.0'), ('MerchantOrderNo', merchant_order_no), ('Amt', amt), ('ItemDesc', item_desc)]
        params += [(k, v) for k, v in optional.items() if v not in (None, '')]
        trade_info = encrypt(urllib.parse.urlencode(params), self.hash_key, self.hash_iv)
        return {
            'action': self.host + '/MPG/mpg_gateway',
            'fields': {'MerchantID': self.merchant_id, 'Version': '1.0', 'TradeInfo': trade_info,
                       'TradeSha': hash_data(trade_info, self.hash_key, self.hash_iv)},
        }

    def parse_notify(self, payload: Dict[str, str], info_field: str = 'TradeInfo',
                     sha_field: str = 'TradeSha') -> Dict[str, Any]:
        """驗證 TradeSha 後解密；TradeInfo 為 JSON（Status、Message、Result{...}）"""
        encrypted = payload.get(info_field, '')
        if not verify_hash(encrypted, payload.get(sha_field, ''), self.hash_key, self.hash_iv):
            raise ValueError(f'{sha_field} 驗證失敗')
        return json.loads(decrypt(encrypted, self.hash_key, self.hash_iv))

    def _post(self, path: str, version: str, info_field: str, sha_field: str, params: Params) -> Dict[str, Any]:
        if not HAS_REQUESTS:
            raise ImportError('需要安裝 requests: pip install requests')
        info = encrypt(urllib.parse.urlencode(params), self.hash_key, self.hash_iv)
        form = {'MerchantID': self.merchant_id, 'Version': version, info_field: info,
                sha_field: hash_data(info, self.hash_key, self.hash_iv)}
        resp = requests.post(self.host + path, data=form, timeout=self.timeout)
        resp.raise_for_status()
        return self.parse_notify(resp.json(), info_field, sha_field)

    def query_trade(self, trade_no: str = '', merchant_order_no: str = '') -> Dict[str, Any]:
        """跨境交易單筆查詢（Version 1.0），TradeNo 與 MerchantOrderNo 擇一，建議用 TradeNo"""
        key, value = ('TradeNo', trade_no) if trade_no else ('MerchantOrderNo', merchant_order_no)
        params = [('MerchantID', self.merchant_id), ('TimeStamp', str(int(time.time()))), ('Version', '1.0'),
                  (key, value)]
        return self._post('/API/merchant_trade/query_trade_info', '1.0', 'QueryInfo', 'QuerySha', params)

    def refund(self, amount: int, trade_no: str = '', merchant_order_no: str = '') -> Dict[str, Any]:
        """跨境交易退款（Version 2.1），RefundType=1、Currency=TWD"""
        key, value = ('TradeNo', trade_no) if trade_no else ('MerchantOrderNo', merchant_order_no)
        params = [('MerchantID', self.merchant_id), ('TimeStamp', str(int(time.time()))), ('Version', '2.1'),
                  (key, value), ('RefundAmt', amount), ('RefundType', 1), ('Currency', 'TWD')]
        return self._post('/API/merchant_trade/trade_refund', '2.1', 'RefundInfo', 'RefundSha', params)


# ----------------------------------------------------------------------------
# 官方手冊的已知答案（完整向量見 tests/vectors/ezpay-payment.json）
# ----------------------------------------------------------------------------

def _self_test() -> int:
    failed = 0

    def check(name: str, ok: bool) -> None:
        nonlocal failed
        failed += not ok
        print(f'  [{"PASS" if ok else "FAIL"}] {name}')

    # 電子支付平台 附件二：AES256，32-byte PKCS#7
    key, iv = 'Ffp0r8VUgQYr8gwI4h87sDgF7xoJqvT5', 'C5z8QsHpnJ6JH9bP'
    plain = ('TimeStamp=1400137200&APIID=SGetTWQRRefund&Version=1.0&UID=300000000066'
             '&RscNo=12345678901234567890&MerchantRefundNo=12345678901234567890')
    expected = ('1eaab8a6e7614649770ba4888956af8ab3acc7e3775685c912bf5cb24eca1ee7fd310b29ce8b36f0e5f3ac55136c86b3'
                '345a51f86707de37b06119a45f3a3253c495177bfb324c5d1e2b0f814f8b17b1f2bf938c9f93df022b45343a125f3f22'
                '65c5127c483f974086672ab19450da1bd22bf790bf08aa37ce55d7b37a0460b53d795c5e048ed1458d36cb8d652ce6a8'
                'bcd6d532b01918903e6840860f1537c3')
    check('電子支付平台 附件二 AES 範例逐位元組相同', encrypt(plain, key, iv) == expected)
    check('解密還原附件二明文', decrypt(expected, key, iv) == plain)

    # 電子支付平台 附件一：訂單建立請求（參數順序依手冊）
    svc = EzPayWalletService('PG300000725648', key, iv)
    form = svc.build_request('SCreateTWQR', [
        ('Mode', '1'), ('Template', 'STANDARD01'), ('LangType', '1'), ('MerchantOrderNo', 'chris_1761731065'),
        ('NotifyURL', 'https://www.infotensor.com/newebmmpnotifyurl/'),
        ('ReturnURL', 'https://www.hashemian.com/tools/form-post-tester.php/54352706'),
        ('ClientBackURL', 'https://www.infotensor.com/'), ('Currency', 'TWD'), ('OrderAmt', '5'),
        ('ItemDesc', '測試環境交易1761731065')], timestamp=1761731065)
    check('附件一 HashData 與手冊相同',
          form['HashData'] == '9172FC10722F45316601BD11257CF6CA506E77142332BD98E13EEC5A7EFC948C')

    # 跨境網路交易：MPG TradeInfo 範例
    k2, iv2 = '12345678901234567890123456789012', '1234567890123456'
    cross = EzPayCrossBorderService('PG100000004839', k2, iv2)
    mpg = cross.build_mpg_form('L_1537926805', 300, '協助測試Test', timestamp=1537926805)
    check('跨境 MPG TradeInfo 與手冊範例相同', mpg['fields']['TradeInfo'].startswith(
        '1aa5a2068482a0bf4875cab87db3298a3de297950e77d1833ed157fb2d615b0021bdf1f23c9f623e0f010f05c35efe6e'))

    # 跨境退款：RefundSha 範例
    refund_cipher = ('89931dedfbc62460c637791dde28cfa465d13c5141dca0e7c5ab75bc66c9d459c49013fed7c8faeb22e6f3dd'
                     '74df3de4fa65814d4bfe3957c785b277013eda75fa874af40d52298a396eb415db5192031ee54574a1f7fccbe'
                     'c788fedb689b183')
    check('跨境退款 RefundSha 與手冊相同', hash_data(refund_cipher, k2, iv2) ==
          'D2A8955B812C6F7020C416EC51949232EA1D850BEA6804A269FF1AEB5A99CB9C')

    # 金鑰錯誤不可回傳亂碼
    try:
        decrypt(expected, 'x' * 32, iv)
        check('金鑰錯誤時解密失敗', False)
    except (ValueError, UnicodeDecodeError):
        check('金鑰錯誤時解密失敗', True)
    return failed


def main() -> None:
    print('ezPay 簡單付 — 官方手冊已知答案測試')
    failed = _self_test()
    print('全部通過' if not failed else f'{failed} 項失敗')

    svc = EzPayWalletService('YOUR_UID', 'YOUR_32_CHAR_HASH_KEY_0000000000', 'YOUR_16_CHAR_IV_')
    form = svc.build_request('SCreateTWQR', [('Mode', 1), ('MerchantOrderNo', f'ORDER_{int(time.time())}'),
                                             ('Currency', 'TWD'), ('OrderAmt', 100), ('ItemDesc', '測試商品')])
    print('\nSCreateTWQR POST 欄位：', {k: (v[:32] + '…' if len(v) > 32 else v) for k, v in form.items()})


if __name__ == '__main__':
    main()
