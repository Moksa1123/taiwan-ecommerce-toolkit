#!/usr/bin/env python3
"""
Shopline Payments Python 範例

SHOPLINE Payments (SLP) 是 SHOPLINE 集團旗下的金流服務，採 RESTful POST + JSON。

支援:
- Redirect 模式 (sessions/create -> sessionUrl)
- Embedded SDK 模式 (payment/create)
- HMAC-SHA256 Webhook 驗證

API 文件: 參見 references/shopline-payment-api.md

依賴:
    pip install requests
"""

import hashlib
import hmac
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional

import requests


# ============================================================================
# Data classes
# ============================================================================

@dataclass
class SessionCreateData:
    """Shopline 建立結帳交易（Redirect 模式）；Webhook URL 在後台設定，不在請求內"""
    reference_id: str  # 特店訂單號 String(32)，唯一
    amount_cents: int  # 金額（分）— NT$1000 = 100000
    return_url: str
    products: List[Dict[str, any]]  # [{id, name, quantity, amount:{value,currency}}]
    shipping: Dict[str, any]  # {shippingMethod, carrier, personalInfo, address}
    customer: Dict[str, any]  # {referenceCustomerId, personalInfo:{lastName, email|phone}}
    billing: Dict[str, any]  # {personalInfo, address:{countryCode, street}}
    client_ip: str
    allow_payment_methods: List[str] = field(default_factory=lambda: ['CreditCard'])  # CreditCard/ApplePay/LinePay/JKOPay/VirtualAccount/ChaileaseBNPL
    currency: str = 'TWD'
    language: str = 'zh-TW'
    expire_minutes: Optional[int] = None  # 預設 360


@dataclass
class ShoplineResponse:
    success: bool
    session_id: str = ''
    session_url: str = ''
    payment_id: str = ''
    status: str = ''
    error_code: str = ''
    error_message: str = ''
    raw: Dict[str, any] = field(default_factory=dict)


# ============================================================================
# Service
# ============================================================================

class ShoplinePaymentService:
    """
    Shopline Payments 服務.

    認證: HTTP headers `merchantId` + `apiKey`.
    端點（皆 POST + JSON）:
        - /api/v1/trade/sessions/create  — Redirect 模式建立結帳交易
        - /api/v1/trade/sessions/query   — 查詢結帳交易
        - /api/v1/trade/payment/create   — Embedded SDK 建立付款交易
        - /api/v1/trade/payment/get      — 查詢付款交易
        - /api/v1/trade/refund/create    — 退款
        - /api/v1/trade/payment/capture  — 請款（autoCapture=false 時）
        - /api/v1/trade/payment/cancel   — 取消授權
    """

    SANDBOX_BASE = 'https://api-sandbox.shoplinepayments.com'
    PROD_BASE = 'https://api.shoplinepayments.com'

    def __init__(self, merchant_id: str, api_key: str, webhook_secret: str = '', is_test: bool = True):
        if not merchant_id or not api_key:
            raise ValueError('Shopline 需要 merchantId 與 apiKey')
        self.merchant_id = merchant_id
        self.api_key = api_key
        self.webhook_secret = webhook_secret
        self.base_url = self.SANDBOX_BASE if is_test else self.PROD_BASE
        self.is_test = is_test

    @property
    def headers(self) -> Dict[str, str]:
        return {
            'merchantId': self.merchant_id,
            'apiKey': self.api_key,
            'requestId': uuid.uuid4().hex,  # String(32)，每個請求唯一
            'Content-Type': 'application/json',
        }

    # -- Operations -----------------------------------------------------------

    def create_session(self, data: SessionCreateData) -> ShoplineResponse:
        """Redirect 模式：建立結帳交易"""
        body = {
            'referenceId': data.reference_id,
            'amount': {'value': data.amount_cents, 'currency': data.currency},
            'language': data.language,
            'returnUrl': data.return_url,
            'mode': 'regular',
            'allowPaymentMethodList': data.allow_payment_methods,
            'order': {'products': data.products, 'shipping': data.shipping},
            'customer': data.customer,
            'billing': data.billing,
            'client': {'ip': data.client_ip},
        }
        if data.expire_minutes:
            body['expireTime'] = data.expire_minutes
        return self._submit('/api/v1/trade/sessions/create', body)

    def query_session(self, session_id: str) -> ShoplineResponse:
        """查詢結帳交易"""
        return self._submit('/api/v1/trade/sessions/query', {'sessionId': session_id})

    def query_payment(self, trade_order_id: str) -> ShoplineResponse:
        """查詢付款交易；實付金額在 raw['payment']['paidAmount']"""
        return self._submit('/api/v1/trade/payment/get', {'tradeOrderId': trade_order_id})

    def refund(self, trade_order_id: str, refund_reference_id: str, amount_cents: int,
               reason: str = '') -> ShoplineResponse:
        """退款；refund_reference_id 為特店退款單號（唯一）"""
        body = {
            'referenceOrderId': refund_reference_id,
            'tradeOrderId': trade_order_id,
            'amount': {'value': amount_cents, 'currency': 'TWD'},
        }
        if reason:
            body['reason'] = reason
        return self._submit('/api/v1/trade/refund/create', body)

    def capture(self, trade_order_id: str, reference_order_id: str, amount_cents: int) -> ShoplineResponse:
        """請款（autoCapture=false 的信用卡交易）"""
        body = {
            'referenceOrderId': reference_order_id,
            'tradeOrderId': trade_order_id,
            'amount': {'value': amount_cents, 'currency': 'TWD'},
        }
        return self._submit('/api/v1/trade/payment/capture', body)

    def cancel(self, trade_order_id: str, reference_order_id: str) -> ShoplineResponse:
        """取消授權（請款前）；已請款回 6002，改用退款"""
        return self._submit('/api/v1/trade/payment/cancel',
                            {'referenceOrderId': reference_order_id, 'tradeOrderId': trade_order_id})

    # -- Webhook --------------------------------------------------------------

    def verify_webhook(self, raw_body: bytes, timestamp: str, sign: str,
                       tolerance_ms: int = 5 * 60 * 1000, now_ms: Optional[int] = None) -> bool:
        """
        驗證 SHOPLINE Payments Webhook 簽章（官方「通知電文 → 簽章演算法」）

        Header 帶 `timestamp`（毫秒）與 `sign`；
        sign = HMAC-SHA256(key=signKey, msg=f"{timestamp}.{raw_body}") 的 hex。

        必須使用原始 body 位元組（不可 json.loads 後重新序列化），並檢查 timestamp
        與現在的差距以防重放。
        """
        if not self.webhook_secret:
            raise ValueError('未設定 signKey，無法驗章')
        message = timestamp.encode('utf-8') + b'.' + raw_body
        expected = hmac.new(self.webhook_secret.encode('utf-8'), message, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, sign.lower()):
            return False
        if tolerance_ms is not None:
            current = now_ms if now_ms is not None else int(time.time() * 1000)
            if abs(current - int(timestamp)) > tolerance_ms:
                return False
        return True

    # -- HTTP submit ----------------------------------------------------------

    def _submit(self, path: str, body: Dict[str, any]) -> ShoplineResponse:
        url = self.base_url + path
        try:
            r = requests.post(url, headers=self.headers, json=body, timeout=30)
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f'Shopline API 連線失敗: {e}')

        try:
            resp = r.json()
        except ValueError:
            return ShoplineResponse(
                success=False,
                error_code=str(r.status_code),
                error_message=f'回應非 JSON: {r.text[:200]}',
            )

        # 400/429/500 回 {code, msg}；200 為成功
        is_success = r.status_code == 200
        return ShoplineResponse(
            success=is_success,
            session_id=resp.get('sessionId', ''),
            session_url=resp.get('sessionUrl', ''),
            payment_id=resp.get('tradeOrderId', ''),
            status=resp.get('status', ''),
            error_code='' if is_success else str(resp.get('code', r.status_code)),
            error_message='' if is_success else resp.get('msg', ''),
            raw=resp,
        )


# ============================================================================
# Examples
# ============================================================================

def example_redirect_create():
    print('=== Shopline Redirect 模式建立結帳交易 ===\n')
    svc = ShoplinePaymentService(merchant_id='YOUR_MERCHANT_ID', api_key='YOUR_API_KEY', is_test=True)
    person = {'lastName': '王', 'firstName': '小明', 'email': 'test@example.com', 'phone': '+886912345678'}
    address = {'countryCode': 'TW', 'city': '台北市', 'street': '敦化北路 170 號'}
    data = SessionCreateData(
        reference_id=f'ORD{int(time.time())}',
        amount_cents=105000,  # NT$1050 -> 105000 分
        return_url='https://your-shop.com/order/return',
        products=[{'id': 'P001', 'name': '測試商品 A', 'quantity': 1,
                   'amount': {'value': 105000, 'currency': 'TWD'}}],
        shipping={'shippingMethod': '宅配', 'carrier': '黑貓宅配', 'personalInfo': person, 'address': address},
        customer={'referenceCustomerId': 'CUST001', 'personalInfo': person},
        billing={'personalInfo': person, 'address': address},
        client_ip='203.0.113.1',
        allow_payment_methods=['CreditCard', 'ApplePay', 'LinePay'],
    )
    resp = svc.create_session(data)
    if resp.success:
        print(f'[OK] sessionId: {resp.session_id}')
        print(f'導轉至: {resp.session_url}')
    else:
        print(f'[FAIL] {resp.error_code}: {resp.error_message}')


def example_query_session():
    print('\n=== Shopline 查詢結帳交易 ===\n')
    svc = ShoplinePaymentService('YOUR_MERCHANT_ID', 'YOUR_API_KEY', is_test=True)
    resp = svc.query_session('se_xxxxxxxx')
    print(json.dumps(resp.raw, ensure_ascii=False, indent=2))


def example_refund():
    print('\n=== Shopline 退款 ===\n')
    svc = ShoplinePaymentService('YOUR_MERCHANT_ID', 'YOUR_API_KEY', is_test=True)
    resp = svc.refund(trade_order_id='1001xxxxxxxx', refund_reference_id=f'RF{int(time.time())}',
                      amount_cents=50000, reason='客戶要求退貨')
    if resp.success:
        print(f'[OK] 退款狀態: {resp.status}（最終結果看 trade.refund.* 事件或 refund/get）')
    else:
        print(f'[FAIL] {resp.error_code}: {resp.error_message}')


def example_verify_webhook():
    """範例: 驗證 Shopline Webhook"""
    print('\n=== Shopline Webhook 驗章 ===\n')
    svc = ShoplinePaymentService(
        merchant_id='YOUR_MERCHANT_ID',
        api_key='YOUR_API_KEY',
        webhook_secret='YOUR_WEBHOOK_SECRET',  # signKey：後台「設定-開發者管理」，每個 Webhook URL 一組
        is_test=True,
    )
    # 模擬收到的 Webhook（header: timestamp、sign；body 為原始位元組）
    raw_body = b'{"id":"1000","type":"trade.succeeded","created":1695795621307,"data":{}}'
    timestamp = str(int(time.time() * 1000))
    sign = hmac.new(b'YOUR_WEBHOOK_SECRET', timestamp.encode() + b'.' + raw_body, hashlib.sha256).hexdigest()

    is_valid = svc.verify_webhook(raw_body, timestamp, sign)
    if is_valid:
        evt = json.loads(raw_body)
        print(f'[OK] Webhook 驗章通過: type={evt["type"]} id={evt["id"]}')
    else:
        print('[FAIL] Webhook 簽章無效，可能是仿冒請求')


if __name__ == '__main__':
    example_redirect_create()
    example_query_session()
    example_refund()
    example_verify_webhook()
