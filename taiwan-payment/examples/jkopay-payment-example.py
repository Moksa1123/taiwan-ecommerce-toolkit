#!/usr/bin/env python3
"""
街口支付 JKOPAY Python 範例

依照 taiwan-payment-skill 規範撰寫。

⚠️ 街口有三套互不相容的簽章機制，本檔涵蓋的是「線上支付 OnlinePay」與
「授權扣款」共用的那一套（HMAC-SHA256 簽 payload 原文）。
線下 POS 與 inApp OAuth 是另外兩套，不可共用本檔的 sign()。
詳見 references/jkopay-payment-api.md §7。

支援:
- Entry API        建立訂單取得付款網址（冪等）
- Refund API       退款（支援多次部分退款）
- Inquiry API      查詢（一次最多 20 筆）
- Authpay          授權扣款：綁定 / 發動扣款 / 終止

API 文件: 參見 references/jkopay-payment-api.md

依賴:
    pip install requests

直接執行本檔會跑官方測試向量的自我驗證，不會發出任何網路請求:
    python jkopay-payment-example.py
"""

import hashlib
import hmac
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import requests


# ============================================================================
# 簽章
# ============================================================================

def sign(payload: str, secret_key: str) -> str:
    """產生 digest。

    ⚠️ 簽的是 **payload 原始字串本身**——不排序、不做 URL encode。
    這與 ECPay 的 CheckMacValue（排序 + urlencode + SHA256）完全不同路數，
    從綠界遷移過來最容易在這裡卡住。

    ⚠️ 連空白都算數。官方範例的 `"currency": "TWD"` 冒號後有一個空格，
    把它拿掉 digest 就完全不同。因此**送出的 bytes 必須與簽章的 bytes
    逐字元相同**——先組好字串、簽它、然後原封不動送出，
    不要簽完再用另一次 json.dumps() 產生 body。
    """
    return hmac.new(
        secret_key.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256,
    ).hexdigest()


# ============================================================================
# Client
# ============================================================================

@dataclass
class JkopayConfig:
    host: str           # 街口簽約時提供，例：https://onlinepay.jkopay.com
    api_key: str
    secret_key: str
    store_id: str


class JkopayClient:
    def __init__(self, config: JkopayConfig, timeout: int = 15):
        self.config = config
        self.timeout = timeout

    # ---- 內部 ----

    def _post(self, path: str, body: Dict[str, Any]) -> Dict[str, Any]:
        # 先序列化成字串並固定下來，簽它、送它 —— 全程只有這一份 bytes
        payload = json.dumps(body, ensure_ascii=False, separators=(',', ':'))
        resp = requests.post(
            f'{self.config.host}{path}',
            data=payload.encode('utf-8'),
            headers={
                'Content-Type': 'application/json',
                'api-key': self.config.api_key,
                'digest': sign(payload, self.config.secret_key),
            },
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()

    def _get(self, path: str, query: str) -> Dict[str, Any]:
        # GET 簽的是 query string 原文（不含 ?）
        resp = requests.get(
            f'{self.config.host}{path}?{query}',
            headers={
                'api-key': self.config.api_key,
                'digest': sign(query, self.config.secret_key),
            },
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()

    # ---- 線上支付 ----

    def create_order(
        self,
        platform_order_id: str,
        total_price: int,
        final_price: int,
        result_url: str,
        result_display_url: str,
        *,
        currency: str = 'TWD',
        unredeem: int = 0,
        valid_time: Optional[str] = None,
        confirm_url: Optional[str] = None,
        payment_type: str = 'onetime',
    ) -> Dict[str, Any]:
        """建立訂單，取得付款網址。

        冪等：同一個 platform_order_id 在付款完成前重複呼叫，
        會回同一個付款網址，不會產生第二筆訂單。

        ⚠️ result_object.payment_url 與 qr_img 的長度會超過 255，
        資料庫欄位不要開 VARCHAR(255)。
        ⚠️ 付款網址僅 20 分鐘有效；只要還在 valid_time 內，
        可用同一單號再呼叫本方法展延另一個 20 分鐘。
        """
        body: Dict[str, Any] = {
            'platform_order_id': platform_order_id,
            'store_id': self.config.store_id,
            'currency': currency,
            'total_price': total_price,
            'final_price': final_price,
            'unredeem': unredeem,
            'result_url': result_url,
            'result_display_url': result_display_url,
            'payment_type': payment_type,
        }
        if valid_time:
            body['valid_time'] = valid_time
        if confirm_url:
            body['confirm_url'] = confirm_url
        return self._post('/platform/entry', body)

    def refund(self, platform_order_id: str, refund_order_id: str, refund_amount: int) -> Dict[str, Any]:
        """退款。支援全額與多次部分退款，累積不可超過實際消費金額。

        ⚠️ refund_order_id 一筆只能退一次。重送同一個號碼**不是重試**，
        會被視為已使用。網路逾時後要確認結果請改用 inquiry() 查，
        **不要換號重送**——換號會變成第二筆退款。
        """
        return self._post('/platform/refund', {
            'platform_order_id': platform_order_id,
            'refund_order_id': refund_order_id,
            'refund_amount': refund_amount,
        })

    def inquiry(self, platform_order_ids: List[str]) -> Dict[str, Any]:
        """查詢訂單與退款歷程。一次最多 20 筆。

        ⚠️ 查無訂單時 result 仍為 '000'，實際結果在
        transactions[].status（102 = 訂單編號不存在）。
        只判斷 result 會把不存在的訂單當成功。
        """
        if len(platform_order_ids) > 20:
            raise ValueError('Inquiry API 一次最多查 20 筆')
        return self._get('/platform/inquiry', f'platform_order_ids={",".join(platform_order_ids)}')

    # ---- 授權扣款（訂閱）----

    def create_authpay(
        self,
        authpay_name: str,
        billing_amount: int,
        result_url: str,
        *,
        regular: bool = True,
        period: str = 'month',
        times: int = 1,
        platform_authpay_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """建立授權綁定，取得 authpay_url 供消費者授權。

        regular=True  定期定額（需帶 billing_cycle）
        regular=False 不定期不定額（授權範圍內隨時扣款）

        ⚠️ times 上限：week / month / quarter 皆為 7，year 為 12。
        「每月多次小額扣款」很容易撞上 month <= 7 這個限制。
        """
        if period in ('week', 'month', 'quarter') and times > 7:
            raise ValueError(f'{period} 的扣款次數上限為 7 次')
        if period == 'year' and times > 12:
            raise ValueError('year 的扣款次數上限為 12 次')

        body: Dict[str, Any] = {
            'authpay_name': authpay_name,
            'store_id': self.config.store_id,
            'billing_amount': billing_amount,
            'billing_currency': 'TWD',
            'result_url': result_url,
        }
        if platform_authpay_id:
            body['platform_authpay_id'] = platform_authpay_id
        if regular:
            body['billing_cycle'] = {'period': period, 'times': times}

        path = '/platform/authpay/regular' if regular else '/platform/authpay/limited'
        return self._post(path, body)

    def charge_authpay(
        self,
        auth_no: str,
        platform_order_id: str,
        trade_name: str,
        total_price: int,
        final_price: int,
    ) -> Dict[str, Any]:
        """以既有授權發動扣款。

        ⚠️ 六個硬限制，設計排程前務必知道（回應碼見 reference §6.6）：
          306  扣款只能在 08:00–20:00 (UTC+8) 發動 —— 夜間 batch 必失敗
          307  同一 auth_no 同時只允許一筆付款 —— 扣款必須序列化
          303  金額超過「消費者自己在 App 設定的額度」，商家不可控
          304  final_price 必須等於授權時的 billing_amount
          305  超過當期扣款次數上限
          104  超過電支法規的個人月限額

        trade_name 會顯示在消費者 App 的授權交易記錄頁，
        寫得讓對方看得懂，否則容易被誤認為盜刷而取消授權。
        """
        return self._post('/platform/authpay/transaction', {
            'auth_no': auth_no,
            'order': {
                'platform_order_id': platform_order_id,
                'trade_name': trade_name,
                'currency': 'TWD',
                'total_price': total_price,
                'final_price': final_price,
            },
        })

    def cancel_authpay(self, auth_no: str) -> Dict[str, Any]:
        """終止授權。重複取消會回 302 Canceled auth_no。"""
        return self._post('/platform/authpay/cancel', {'auth_no': auth_no})


# ============================================================================
# 對帳
# ============================================================================

def settled_amount(transaction: Dict[str, Any]) -> int:
    """取得實際會進撥款的金額。

    ⚠️ 對帳要用 debit_amount 而不是 final_price。
    街口幣與券折抵的部分（redeem_amount）不會進你的撥款帳，
    直接用 final_price 對帳會長期短差。

    恆等式：final_price = redeem_amount + debit_amount
    """
    return int(transaction['debit_amount'])


# ============================================================================
# 自我驗證（官方測試向量）
# ============================================================================

def _self_test() -> int:
    """用街口官方文件的測試向量驗證 sign() 實作。

    這兩組值直接取自官方「加簽加密說明」頁，可確認你的環境
    （字元編碼、HMAC 實作）產生的 digest 與街口一致。
    """
    secret = ('r0odDC1e9LHXDmxuvmOv9bgaWLf2CXB2c4gMheoFucVKNMi1K0Id9zwRHJF1r'
              '-kdtAKriKgb11VDlo7Kb8R-FQ')

    post_payload = (
        '{"platform_order_id":"demo-order-001",'
        '"store_id":"35f12dff-1581-11e9-a054-00505684fd45",'
        '"currency": "TWD","total_price":10,"final_price":10,"unredeem":10,'
        '"result_display_url":"https://display.com",'
        '"result_url":"https://result-callback.xxx/xxx"}'
    )
    cases = [
        ('POST (Entry API)', post_payload,
         '3577609b058ab85c2d0a00a5421a991979ed6b9f549476e9a82476dc1b70d876'),
        ('GET (Inquiry API)', 'platform_order_ids=test123,demo-order-001',
         '7778b95890af17c5b41e8cef957f4769e7bfecc79e9f9ee555923293ebd8e880'),
    ]

    failed = 0
    print('街口官方測試向量驗證')
    for label, payload, expected in cases:
        got = sign(payload, secret)
        ok = got == expected
        failed += not ok
        print(f'  [{"PASS" if ok else "FAIL"}] {label}')
        if not ok:
            print(f'         期望 {expected}')
            print(f'         實得 {got}')

    # 示範空白的影響：把 `"currency": "TWD"` 的空格拿掉，digest 就變了
    no_space = post_payload.replace('"currency": "TWD"', '"currency":"TWD"')
    changed = sign(no_space, secret) != cases[0][2]
    failed += not changed
    print(f'  [{"PASS" if changed else "FAIL"}] 移除一個空白後 digest 確實改變'
          f'（證明必須逐字元一致）')

    print()
    print('全部通過' if failed == 0 else f'{failed} 項失敗')
    return 1 if failed else 0


if __name__ == '__main__':
    raise SystemExit(_self_test())
