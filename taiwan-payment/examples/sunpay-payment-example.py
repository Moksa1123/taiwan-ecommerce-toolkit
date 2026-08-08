#!/usr/bin/env python3
"""
紅陽科技 SunPay Python 範例

依照 taiwan-payment-skill 規範撰寫。

⚠️ 紅陽是本 skill 收錄的 14 家中**唯一使用非對稱加密**的。
其他家不是 SHA256 檢查碼（ECPay / O'Pay）就是 AES 對稱加密
（NewebPay / PAYUNi / ezPay）。既有的加解密函式一律不能沿用。

送出的 form 只有四個欄位：
    web           特店代號
    send_time     交易時間，格式 fffssmmHHyyyyMMdd（毫秒在最前面）
    rsamsg        業務參數 → urlencode → RSA 分段加密 → base64
    check_value   業務參數 → ASCII 排序 → urlencode → 尾接 SHA2 密鑰 → SHA256

API 文件: 參見 references/sunpay-payment-api.md

依賴:
    pip install requests cryptography

直接執行本檔會跑官方測試向量的自我驗證，不會發出任何網路請求:
    python sunpay-payment-example.py
"""

import base64
import hashlib
import json
import urllib.parse
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

import requests

try:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import padding
except ImportError:  # 自我驗證只用到 SHA256，不強制安裝 cryptography
    serialization = None
    padding = None


# 加密分段 117 byte、解密分段 128 byte —— 兩者不同，很容易誤寫成同一個值。
# 128 是 1024-bit RSA 的密文區塊固定長度；117 = 128 - 11，
# 扣掉的 11 byte 是 PKCS#1 v1.5 的 padding。
RSA_ENCRYPT_CHUNK = 117
RSA_DECRYPT_CHUNK = 128


# ============================================================================
# 簽章與加密
# ============================================================================

def build_send_time(now: Optional[datetime] = None) -> str:
    """組出 send_time。

    ⚠️ 格式是 fffssmmHHyyyyMMdd —— 毫秒在最前面、日期在最後，
    不是一般的 yyyyMMddHHmmssfff。
    ⚠️ 超過 120 秒即視為無效交易，主機需做 NTP 校時。
    """
    n = now or datetime.now()
    return f'{n.microsecond // 1000:03d}{n.second:02d}{n.minute:02d}{n.hour:02d}{n:%Y%m%d}'


def _canonical(payload: Dict[str, Any]) -> str:
    """依 ASCII 升序排序後序列化，不留空白。

    ⚠️ 手冊在兩處重複警告「請務必將 head 與 body 參數進行 ASCII 排序，
    以免加密失敗」。排序要套用到巢狀的 head 與 body 內部。
    """
    ordered = {
        k: (dict(sorted(v.items())) if isinstance(v, dict) else v)
        for k, v in sorted(payload.items())
    }
    return json.dumps(ordered, separators=(',', ':'), ensure_ascii=False)


def make_check_value(payload: Dict[str, Any], sha2_key: str) -> str:
    """產生 check_value。

    排序 → JSON → urlencode → **尾端直接串上 SHA2 密鑰** → SHA256。

    ⚠️ 密鑰是接在字串尾端，不是 ECPay 那種
    `HashKey=...&參數&HashIV=...` 的前後包夾。
    ⚠️ 值為 null 的參數不參與簽名（官方明註），本函式已於 build 階段排除。
    """
    encoded = urllib.parse.quote(_canonical(payload), safe='')
    return hashlib.sha256((encoded + sha2_key).encode('utf-8')).hexdigest()


def make_rsamsg(payload: Dict[str, Any], public_key_pem: str) -> str:
    """產生 rsamsg：urlencode 後以 RSA 分段加密，再 base64。"""
    if serialization is None:
        raise RuntimeError('需要 cryptography 套件：pip install cryptography')

    key = serialization.load_pem_public_key(public_key_pem.encode('utf-8'))
    data = urllib.parse.quote(_canonical(payload), safe='').encode('utf-8')

    out = bytearray()
    for i in range(0, len(data), RSA_ENCRYPT_CHUNK):
        out += key.encrypt(data[i:i + RSA_ENCRYPT_CHUNK], padding.PKCS1v15())
    return base64.b64encode(bytes(out)).decode('ascii')


def parse_rsamsg(rsamsg: str, private_key_pem: str) -> Dict[str, Any]:
    """解密紅陽回傳的 rsamsg。

    ⚠️ 解密分段是 128 byte，不是加密時的 117。
    """
    if serialization is None:
        raise RuntimeError('需要 cryptography 套件：pip install cryptography')

    key = serialization.load_pem_private_key(private_key_pem.encode('utf-8'), password=None)
    raw = base64.b64decode(rsamsg)

    out = bytearray()
    for i in range(0, len(raw), RSA_DECRYPT_CHUNK):
        out += key.decrypt(raw[i:i + RSA_DECRYPT_CHUNK], padding.PKCS1v15())
    return json.loads(urllib.parse.unquote(out.decode('utf-8')))


# ============================================================================
# Client
# ============================================================================

TRADE_URL = 'https://trade.sunpay.com.tw/v4/cash'
TEST_TRADE_URL = 'https://testtrade.sunpay.com.tw/v4/cash'
QUERY_URL = 'https://trade.sunpay.com.tw/v4/query/PaymentCheck'
# 注意：交易與查詢是 /v4/，請款與退款仍是 /v3/ —— 同一份手冊裡版號不一致
REFUND_URL = 'https://trade.sunpay.com.tw/v3/Service/CardRefund'


@dataclass
class SunpayConfig:
    web: str                # 特店代號
    public_key_pem: str     # 紅陽提供的 RSA 公鑰
    sha2_key: str           # 紅陽提供的 SHA2 密鑰
    sandbox: bool = True


class SunpayClient:
    def __init__(self, config: SunpayConfig, timeout: int = 15):
        self.config = config
        self.timeout = timeout

    def build_form(self, body: Dict[str, Any]) -> Dict[str, str]:
        """組出要 POST 的四個欄位。回傳 dict，可直接餵給 requests 的 data。"""
        send_time = build_send_time()
        payload = {
            'head': {'send_time': send_time, 'web': self.config.web},
            # null 不參與簽名，先濾掉
            'body': {k: v for k, v in body.items() if v is not None},
        }
        return {
            'web': self.config.web,
            'send_time': send_time,
            'rsamsg': make_rsamsg(payload, self.config.public_key_pem),
            'check_value': make_check_value(payload, self.config.sha2_key),
        }

    def create_payment(
        self,
        td: str,
        mn: int,
        *,
        card_type: Optional[str] = None,
        order_info: Optional[str] = None,
        email: Optional[str] = None,
        note1: Optional[str] = None,
    ) -> requests.Response:
        """建立交易。回傳的是要導轉給消費者的頁面。

        card_type：01 信用卡 / 02 銀聯 / 03 ApplePay 或 GooglePay /
                   06 超商代碼 / 07 超商條碼 / 08 虛擬帳號 /
                   09 超商取貨付款 / 10 街口支付
        不帶則由消費者在紅陽收銀台自行選擇。

        ⚠️ mn 必須是正整數，不可有小數點或千位符號。
        """
        form = self.build_form({
            'td': td,
            'mn': str(mn),
            'card_type': card_type,
            'order_info': order_info,
            'email': email,
            'note1': note1,
        })
        url = TEST_TRADE_URL if self.config.sandbox else TRADE_URL
        return requests.post(url, data=form, timeout=self.timeout)


# ============================================================================
# 回應處理
# ============================================================================

# ⚠️ 同一個欄位名 pay_result，在兩支 API 的語意不同 ——
# 12 在交易通知是「已建立」，在查詢 API 卻是「查無該筆訂單」。
# 因此兩張表必須分開維護，絕不可共用同一份 mapping。

CALLBACK_RESULT = {
    '10': '交易成功',
    '11': '交易失敗',
    '12': '已建立',          # ← 與查詢 API 的 12 意義不同
}

QUERY_RESULT = {
    '06': '交易編號或訂單編號須擇一',
    '10': '交易成功',
    '11': '交易失敗',
    '12': '查無該筆訂單',     # ← 與交易通知的 12 意義不同
    '13': '交易未完成',
    '14': '訂單退款',
    '15': '交易取消',
}


def describe_callback(pay_result: str) -> str:
    return CALLBACK_RESULT.get(pay_result, f'未知代碼 {pay_result}')


def describe_query(pay_result: str) -> str:
    return QUERY_RESULT.get(pay_result, f'未知代碼 {pay_result}')


def parse_logistics_notify(form: Dict[str, str]) -> Dict[str, str]:
    """解析物流狀態通知。

    ⚠️ 與交易 CallBack 的格式不同：這支是 HTTP FORM POST key-value
    （非 JSON），且**所有欄位都經過 URL Encode**，需先解碼（UTF-8）。
    ⚠️ 訂單編號欄位是大寫的 Td，與請求端的小寫 td 不同。
    """
    return {k: urllib.parse.unquote_plus(v) for k, v in form.items()}


# ============================================================================
# 自我驗證（官方測試向量）
# ============================================================================

def _self_test() -> int:
    """用紅陽金流手冊 v1.1.0 的測試向量驗證 check_value 實作。

    同時驗證我們自行組出的 urlencode 字串與手冊逐字相同 ——
    這是最容易出錯的一步（排序、空白、safe 字元集）。
    """
    sha2_key = 'D2AE96E5528531CFCDE90591695F973D23846ABD01A639AB1D3E0322D56E0ED9'
    expected_encoded = (
        '%7B%22body%22%3A%7B%22country_type%22%3A%22cht%22%2C%22mn%22%3A%22200%22%2C'
        '%22td%22%3A%22TT1695802894%22%7D%2C%22head%22%3A%7B%22send_time%22%3A'
        '%2258534211620230927%22%2C%22web%22%3A%22MC31793850%22%7D%7D'
    )
    expected_check = '3df3acb3c4c3de1cb352a31bea3df6341e7c24b53aec8c695c32e3aa417cad26'

    payload = {
        'body': {'country_type': 'cht', 'mn': '200', 'td': 'TT1695802894'},
        'head': {'send_time': '58534211620230927', 'web': 'MC31793850'},
    }

    failed = 0
    print('紅陽官方測試向量驗證')

    encoded = urllib.parse.quote(_canonical(payload), safe='')
    ok = encoded == expected_encoded
    failed += not ok
    print(f'  [{"PASS" if ok else "FAIL"}] urlencode 結果與手冊逐字相同')
    if not ok:
        print(f'         期望 {expected_encoded[:60]}...')
        print(f'         實得 {encoded[:60]}...')

    got = make_check_value(payload, sha2_key)
    ok = got == expected_check
    failed += not ok
    print(f'  [{"PASS" if ok else "FAIL"}] check_value')
    if not ok:
        print(f'         期望 {expected_check}')
        print(f'         實得 {got}')

    # send_time 格式：毫秒在最前面、日期在最後
    st = build_send_time(datetime(2023, 9, 27, 16, 21, 34, 585_000))
    ok = st == '585342116' + '20230927'
    failed += not ok
    print(f'  [{"PASS" if ok else "FAIL"}] send_time 格式 fffssmmHHyyyyMMdd（實得 {st}）')

    # 兩張代碼表的 12 必須不同義
    ok = describe_callback('12') != describe_query('12')
    failed += not ok
    print(f'  [{"PASS" if ok else "FAIL"}] pay_result=12 在交易通知與查詢 API 語意不同'
          f'（{describe_callback("12")} vs {describe_query("12")}）')

    print()
    print('全部通過' if failed == 0 else f'{failed} 項失敗')
    return 1 if failed else 0


if __name__ == '__main__':
    raise SystemExit(_self_test())
