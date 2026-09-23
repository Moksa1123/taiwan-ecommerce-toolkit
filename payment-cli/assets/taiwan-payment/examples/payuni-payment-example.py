#!/usr/bin/env python3
"""
PAYUNi 統一金流 Python 完整範例

支援: 整合式支付頁 UPP（信用卡、ATM、超商代碼、AFTEE、愛金卡、LINE Pay、街口…）、
      付款結果通知、交易查詢、信用卡退款

依據（皆已對照原始碼）:
- 加解密：統一金流官方外掛 PAYUNi_for_WooCommerce 1.2.8、官方 PHP SDK（github.com/payuni/PHP_SDK），
  並以 tests/vectors/payuni.json 逐位元組驗證
- UPP 欄位與付款方式開關：官方外掛 uppOnePointHandler()、$paymentArr
- 端點路徑：官方 PHP SDK UniversalTrade() 對照表（例如操作名 trade_query → 路徑 trade/query）
- 通知 / 查詢欄位與代碼：wpbr-payuni-payment 1.7.1

API 文件: https://docs.payuni.com.tw/web/
"""

import base64
import hashlib
import hmac
import re
import time
import urllib.parse
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

try:
    from Crypto.Cipher import AES
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False


# UPP 付款方式開關欄位（官方外掛 $paymentArr，大小寫須完全相同）
UPP_PAYMENT_FLAGS = (
    'Credit', 'CreditInst', 'CreditRed', 'CreditUnionPay',
    'ApplePay', 'GooglePay', 'SamsungPay',
    'ATM', 'CVS', 'ICash', 'Aftee', 'LinePay', 'JKoPay',
)

# 交易狀態（wpbr-payuni-payment Utils/TradeStatus.php）
TRADE_STATUS = {
    '0': '取號成功 / 信用審查正常', '1': '已付款', '2': '付款失敗', '3': '付款取消',
    '4': '交易逾期', '8': '待確認', '9': '未付款',
}


@dataclass
class PaymentOrderData:
    """PAYUNi UPP 訂單資料"""
    mer_trade_no: str
    trade_amt: int
    prod_desc: str
    return_url: str                      # 前景：消費者付款後導回
    notify_url: str                      # 背景：伺服器對伺服器通知
    payment_methods: List[str] = field(default_factory=lambda: ['Credit'])
    usr_mail: Optional[str] = None
    expire_date: Optional[str] = None    # 繳費期限 YYYY-MM-DD（ATM / 超商代碼）
    lang: Optional[str] = None


@dataclass
class PaymentCallbackData:
    """付款結果通知（EncryptInfo 解密後）"""
    status: str                          # SUCCESS；AFTEE 審核通過時為 OK
    message: str
    mer_trade_no: str
    trade_no: str                        # UNi 序號，退款 / 查詢用
    trade_amt: int
    trade_status: str                    # 見 TRADE_STATUS
    payment_type: str                    # 1=信用卡 2=ATM 3=超商代碼 6=愛金卡 7=AFTEE 9=LINE Pay …
    raw: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_paid(self) -> bool:
        return self.status == 'SUCCESS' and self.trade_status == '1'


class PAYUNiPaymentService:
    """PAYUNi 統一金流服務（AES-256-GCM + SHA256）"""

    TEST_BASE_URL = 'https://sandbox-api.payuni.com.tw/api'
    PROD_BASE_URL = 'https://api.payuni.com.tw/api'

    def __init__(self, mer_id: str, hash_key: str, hash_iv: str, is_production: bool = False):
        if not HAS_CRYPTO:
            raise ImportError('需要安裝 pycryptodome: pip install pycryptodome')

        self.mer_id = mer_id
        self.hash_key = hash_key.encode('utf-8')
        self.hash_iv = hash_iv.encode('utf-8')
        self.base_url = self.PROD_BASE_URL if is_production else self.TEST_BASE_URL

    # ------------------------------------------------------------------
    # 加解密（與官方外掛 / SDK 逐位元組相同）
    # ------------------------------------------------------------------

    def encrypt_data(self, data: Dict[str, Any]) -> str:
        """
        EncryptInfo = hex( base64(AES-256-GCM 密文) + ":::" + base64(tag) )

        官方以 openssl_encrypt(..., options=0) 取得 base64 密文，再與 base64 tag 以
        ":::" 串接後整段 bin2hex。只做到 base64 + ":::" 而少了最外層 hex 的版本會被拒絕。
        """
        query_string = urllib.parse.urlencode(data)
        cipher = AES.new(self.hash_key, AES.MODE_GCM, nonce=self.hash_iv)   # HashIV 即 nonce（16 bytes）
        encrypted, tag = cipher.encrypt_and_digest(query_string.encode('utf-8'))
        return (base64.b64encode(encrypted) + b':::' + base64.b64encode(tag)).hex()

    def decrypt_data(self, encrypted_data: str) -> Dict[str, Any]:
        """解密 EncryptInfo；tag 驗證失敗（資料遭竄改 / 金鑰錯誤）時拋出 ValueError"""
        try:
            raw = bytes.fromhex(encrypted_data.strip())
            if b':::' not in raw:
                raise ValueError('格式錯誤: hex 解碼後缺少 ":::" 分隔符')
            encrypted_b64, tag_b64 = raw.split(b':::', 1)

            decipher = AES.new(self.hash_key, AES.MODE_GCM, nonce=self.hash_iv)
            decrypted = decipher.decrypt_and_verify(
                base64.b64decode(encrypted_b64), base64.b64decode(tag_b64))

            params = urllib.parse.parse_qs(decrypted.decode('utf-8'), keep_blank_values=True)
            return {k: v[0] if len(v) == 1 else v for k, v in params.items()}
        except Exception as e:
            raise ValueError(f'解密失敗: {str(e)}')

    def generate_checksum(self, encrypt_info: str) -> str:
        """HashInfo = SHA256( HashKey + EncryptInfo + HashIV ) 轉大寫（Key 在前）"""
        raw = self.hash_key.decode('utf-8') + encrypt_info + self.hash_iv.decode('utf-8')
        return hashlib.sha256(raw.encode('utf-8')).hexdigest().upper()

    def verify_checksum(self, encrypt_info: str, checksum: str) -> bool:
        """驗證 HashInfo（常數時間比較，避免以回應時間差逐字元猜出正確雜湊）"""
        return hmac.compare_digest(self.generate_checksum(encrypt_info), checksum.upper())

    def _envelope(self, data: Dict[str, Any], version: str) -> Dict[str, str]:
        encrypt_info = self.encrypt_data(data)
        return {
            'MerID': self.mer_id,
            'Version': version,
            'EncryptInfo': encrypt_info,
            'HashInfo': self.generate_checksum(encrypt_info),
        }

    # ------------------------------------------------------------------
    # UPP 整合式支付頁
    # ------------------------------------------------------------------

    def build_upp_form(self, data: PaymentOrderData) -> Dict[str, Any]:
        """
        產生 UPP 表單

        UPP 是消費者瀏覽器以表單 POST 到 /api/upp 的付款頁（官方 SDK 的 HtmlApi()
        就是輸出一個自動送出的 <form>），不是伺服器端呼叫的 JSON API。

        付款方式以「欄位名 = 1」的旗標啟用，沒有 PayType 參數。

        Returns:
            {'action': 送出網址, 'fields': {'MerID', 'Version', 'EncryptInfo', 'HashInfo'}}
        """
        if data.trade_amt < 1:
            raise ValueError('金額必須大於 0')
        unknown = [m for m in data.payment_methods if m not in UPP_PAYMENT_FLAGS]
        if unknown:
            raise ValueError(f'未知的付款方式欄位 {unknown}（可用：{", ".join(UPP_PAYMENT_FLAGS)}）')

        encrypt_info: Dict[str, Any] = {
            'MerID': self.mer_id,
            'MerTradeNo': data.mer_trade_no,
            'TradeAmt': data.trade_amt,
            'ProdDesc': data.prod_desc,
            'ReturnURL': data.return_url,
            'NotifyURL': data.notify_url,
            'Timestamp': int(time.time()),
        }
        if data.usr_mail:
            encrypt_info['UsrMail'] = data.usr_mail
        if data.expire_date:
            encrypt_info['ExpireDate'] = data.expire_date
        if data.lang:
            encrypt_info['Lang'] = data.lang
        for method in data.payment_methods:
            encrypt_info[method] = 1

        return {'action': f'{self.base_url}/upp', 'fields': self._envelope(encrypt_info, '1.0')}

    def parse_callback(self, callback_data: Dict[str, str]) -> PaymentCallbackData:
        """
        解析 NotifyURL / ReturnURL 的付款結果（先驗 HashInfo 再解密）

        入帳前務必確認 is_paid（Status=SUCCESS 且 TradeStatus=1），並比對金額與訂單。
        ATM / 超商代碼在「取號成功」時也會通知，此時 TradeStatus=0，尚未付款。
        """
        encrypt_info = callback_data.get('EncryptInfo', '')
        hash_info = callback_data.get('HashInfo', '')
        if not self.verify_checksum(encrypt_info, hash_info):
            raise ValueError('HashInfo 驗證失敗')

        decrypted = self.decrypt_data(encrypt_info)
        return PaymentCallbackData(
            status=decrypted.get('Status', ''),
            message=decrypted.get('Message', ''),
            mer_trade_no=decrypted.get('MerTradeNo', ''),
            trade_no=decrypted.get('TradeNo', ''),
            trade_amt=int(decrypted.get('TradeAmt') or 0),
            trade_status=decrypted.get('TradeStatus', ''),
            payment_type=decrypted.get('PaymentType', ''),
            raw=decrypted,
        )

    # ------------------------------------------------------------------
    # 幕後 API（伺服器對伺服器）
    # ------------------------------------------------------------------

    def _post(self, path: str, data: Dict[str, Any], version: str) -> Dict[str, Any]:
        import requests

        response = requests.post(f'{self.base_url}/{path}', data=self._envelope(data, version), timeout=30)
        response.raise_for_status()
        result = response.json()
        encrypt_info = result.get('EncryptInfo', '')
        if not encrypt_info:
            # 外層錯誤不帶 EncryptInfo
            return {'Status': result.get('Status', 'ERROR'), 'raw': result}
        if not self.verify_checksum(encrypt_info, result.get('HashInfo', '')):
            raise ValueError('HashInfo 驗證失敗')
        return self.decrypt_data(encrypt_info)

    @staticmethod
    def extract_results(decrypted: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        把 parse_qs 攤平的巢狀欄位 Result[0][TradeNo] 還原成 [{'TradeNo': ...}, ...]

        PHP 的 parse_str 會自動組成巢狀陣列，Python 的 parse_qs 不會。
        """
        rows: Dict[int, Dict[str, Any]] = {}
        for key, value in decrypted.items():
            m = re.fullmatch(r'Result\[(\d+)\]\[(\w+)\]', key)
            if m:
                rows.setdefault(int(m.group(1)), {})[m.group(2)] = value
        return [rows[i] for i in sorted(rows)]

    def query_trade(self, mer_trade_no: str) -> List[Dict[str, Any]]:
        """
        交易查詢（POST /api/trade/query）

        以 Version 2.0 呼叫（同 wpbr-payuni-payment），結果在 Result 陣列內，
        每筆含 MerTradeNo / TradeNo / TradeStatus / PaymentType / CreateDay / PaymentDay /
        CloseStatus（信用卡）。
        """
        decrypted = self._post('trade/query', {
            'MerID': self.mer_id,
            'MerTradeNo': mer_trade_no,
            'Timestamp': int(time.time()),
        }, version='2.0')
        return self.extract_results(decrypted)

    def refund_credit(self, trade_no: str, amount: int) -> Dict[str, Any]:
        """
        信用卡退款（POST /api/trade/close，CloseType=2）

        只有請款成功（CloseStatus=2）的交易可退款；尚未請款的授權請改用
        trade/cancel 取消授權。
        """
        return self._post('trade/close', {
            'MerID': self.mer_id,
            'TradeNo': trade_no,
            'TradeAmt': amount,
            'CloseType': 2,
            'Timestamp': int(time.time()),
        }, version='1.0')


# Usage Example
if __name__ == '__main__':
    print('=' * 60)
    print('PAYUNi 統一金流 - Python 範例')
    print('=' * 60)

    if not HAS_CRYPTO:
        print('✗ 需要安裝 pycryptodome: pip install pycryptodome')
        raise SystemExit(1)

    service = PAYUNiPaymentService(
        mer_id='YOUR_MERCHANT_ID',
        hash_key='YOUR_HASH_KEY_32_BYTES_LONG_XXXX',   # 32 bytes
        hash_iv='YOUR_HASH_IV_16B',                     # 16 bytes
    )

    form = service.build_upp_form(PaymentOrderData(
        mer_trade_no=f'UNI{int(time.time())}',
        trade_amt=3000,
        prod_desc='測試商品購買',
        return_url='https://your-site.com/payment/return',
        notify_url='https://your-site.com/payment/notify',
        payment_methods=['Credit', 'ATM', 'CVS'],
        usr_mail='test@example.com',
    ))
    print(f'✓ UPP 表單：POST {form["action"]}')
    print(f'  欄位：{list(form["fields"])}')
    print('  由前端產生自動送出的 <form>，導向統一金流付款頁')
