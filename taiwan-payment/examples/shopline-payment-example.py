#!/usr/bin/env python3
"""
Shopline Payments Python 範例

依照 taiwan-payment-skill 規範撰寫。
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
    """Shopline 建立結帳會話（Redirect 模式）"""
    reference_number: str  # 商家訂單編號 (唯一)
    amount_cents: int  # 金額（分）— NT$1000 = 100000
    currency: str = 'TWD'
    return_url: str = ''  # 完成後導回網址
    cancel_url: str = ''  # 取消後導回網址
    webhook_url: str = ''  # 通知 URL (HTTPS only)
    description: str = ''
    customer_email: str = ''
    customer_phone: str = ''
    items: List[Dict[str, any]] = field(default_factory=list)
    payment_methods: Optional[List[str]] = None  # CARD/APPLEPAY/LINEPAY/JKOPAY/ATM/BNPL


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
    端點:
        - POST /sessions/create        — Redirect 模式建立會話
        - GET  /sessions/{sessionId}   — 查詢會話
        - POST /payment/create         — Embedded SDK 提交付款
        - POST /refund/create          — 退款
        - POST /capture                — 請款（auth + capture 模式）
        - POST /void                   — 取消授權
    """

    SANDBOX_BASE = 'https://sandbox-payments-api.shoplineapp.com'
    PROD_BASE = 'https://payments-api.shoplineapp.com'

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
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

    # -- Operations -----------------------------------------------------------

    def create_session(self, data: SessionCreateData) -> ShoplineResponse:
        """Redirect 模式：建立結帳會話"""
        body = {
            'merchantId': self.merchant_id,
            'referenceNumber': data.reference_number,
            'amount': {
                'value': data.amount_cents,  # 已是分
                'currency': data.currency,
            },
            'returnUrl': data.return_url,
            'cancelUrl': data.cancel_url,
            'webhookUrl': data.webhook_url,
            'description': data.description,
            'customer': {
                'email': data.customer_email,
                'phone': data.customer_phone,
            },
            'items': data.items,
        }
        if data.payment_methods:
            body['paymentMethods'] = data.payment_methods
        return self._submit('POST', '/sessions/create', body)

    def query_session(self, session_id: str) -> ShoplineResponse:
        """查詢結帳會話狀態"""
        return self._submit('GET', f'/sessions/{session_id}', None)

    def refund(self, payment_id: str, amount_cents: int, reason: str = '') -> ShoplineResponse:
        """退款"""
        body = {
            'paymentId': payment_id,
            'amount': {
                'value': amount_cents,
                'currency': 'TWD',
            },
            'reason': reason,
        }
        return self._submit('POST', '/refund/create', body)

    def capture(self, payment_id: str, amount_cents: int) -> ShoplineResponse:
        """請款 (auth + capture 模式專用)"""
        body = {
            'paymentId': payment_id,
            'amount': {'value': amount_cents, 'currency': 'TWD'},
        }
        return self._submit('POST', '/capture', body)

    def void(self, payment_id: str) -> ShoplineResponse:
        """取消授權"""
        return self._submit('POST', '/void', {'paymentId': payment_id})

    # -- Webhook --------------------------------------------------------------

    def verify_webhook(self, payload: bytes, signature_header: str) -> bool:
        """
        驗證 Shopline Webhook 簽章 (HMAC-SHA256).

        Shopline 通知時會在 header 帶 `x-slp-signature: sha256=<hex>`，
        其值為 HMAC-SHA256(secret=webhookSecret, message=raw_body) 的 hex 表示。
        """
        if not self.webhook_secret:
            raise ValueError('未設定 webhookSecret，無法驗章')

        # 提取 signature header 中的 hex 值
        if signature_header.startswith('sha256='):
            sig_hex = signature_header[7:]
        else:
            sig_hex = signature_header

        expected = hmac.new(
            self.webhook_secret.encode('utf-8'),
            payload,
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(expected.lower(), sig_hex.lower())

    # -- HTTP submit ----------------------------------------------------------

    def _submit(self, method: str, path: str, body: Optional[Dict[str, any]]) -> ShoplineResponse:
        url = self.base_url + path
        try:
            if method == 'GET':
                r = requests.get(url, headers=self.headers, timeout=30)
            else:
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

        is_success = 200 <= r.status_code < 300

        return ShoplineResponse(
            success=is_success,
            session_id=resp.get('sessionId', ''),
            session_url=resp.get('sessionUrl', ''),
            payment_id=resp.get('paymentId', resp.get('id', '')),
            status=resp.get('status', ''),
            error_code=str(r.status_code) if not is_success else '',
            error_message=resp.get('message', resp.get('error', '')),
            raw=resp,
        )


# ============================================================================
# Examples
# ============================================================================

def example_redirect_create():
    print('=== Shopline Redirect 模式建立會話 ===\n')
    svc = ShoplinePaymentService(
        merchant_id='YOUR_MERCHANT_ID',
        api_key='YOUR_API_KEY',
        is_test=True,
    )
    data = SessionCreateData(
        reference_number=f'ORD{int(time.time())}',
        amount_cents=105000,  # NT$1050 -> 105000 分
        currency='TWD',
        return_url='https://your-shop.com/order/success',
        cancel_url='https://your-shop.com/order/cancel',
        webhook_url='https://your-shop.com/api/shopline/webhook',
        description='測試訂單',
        customer_email='test@example.com',
        customer_phone='0912345678',
        items=[
            {'name': '測試商品 A', 'quantity': 1, 'unitPrice': {'value': 105000, 'currency': 'TWD'}},
        ],
        payment_methods=['CARD', 'APPLEPAY', 'LINEPAY'],
    )
    resp = svc.create_session(data)
    if resp.success:
        print(f'[OK] sessionId: {resp.session_id}')
        print(f'導轉至: {resp.session_url}')
    else:
        print(f'[FAIL] {resp.error_code}: {resp.error_message}')


def example_query_session():
    print('\n=== Shopline 查詢會話 ===\n')
    svc = ShoplinePaymentService('YOUR_MERCHANT_ID', 'YOUR_API_KEY', is_test=True)
    resp = svc.query_session('session_xxxxxxxx')
    print(json.dumps(resp.raw, ensure_ascii=False, indent=2))


def example_refund():
    print('\n=== Shopline 退款 ===\n')
    svc = ShoplinePaymentService('YOUR_MERCHANT_ID', 'YOUR_API_KEY', is_test=True)
    resp = svc.refund(payment_id='pay_xxxxxxxx', amount_cents=50000, reason='客戶要求退貨')
    if resp.success:
        print(f'[OK] 退款 paymentId: {resp.payment_id}')
    else:
        print(f'[FAIL] {resp.error_code}: {resp.error_message}')


def example_verify_webhook():
    """範例: 驗證 Shopline Webhook"""
    print('\n=== Shopline Webhook 驗章 ===\n')
    svc = ShoplinePaymentService(
        merchant_id='YOUR_MERCHANT_ID',
        api_key='YOUR_API_KEY',
        webhook_secret='YOUR_WEBHOOK_SECRET',  # 後台取得
        is_test=True,
    )
    # 模擬收到的 Webhook
    raw_body = b'{"event":"payment.completed","paymentId":"pay_abc123","amount":{"value":105000,"currency":"TWD"}}'
    signature_header = 'sha256=abcdef123456'  # 實務上由 Shopline 提供於 x-slp-signature header

    is_valid = svc.verify_webhook(raw_body, signature_header)
    if is_valid:
        evt = json.loads(raw_body)
        print(f'[OK] Webhook 驗章通過: event={evt["event"]} paymentId={evt["paymentId"]}')
    else:
        print('[FAIL] Webhook 簽章無效，可能是仿冒請求')


if __name__ == '__main__':
    example_redirect_create()
    example_query_session()
    example_refund()
    example_verify_webhook()
