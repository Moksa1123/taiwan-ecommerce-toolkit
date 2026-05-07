#!/usr/bin/env python3
"""
LINE Pay v4 Online API Python 範例

依照 taiwan-payment-skill 規範撰寫。
LINE Pay 兩段式流程: Request -> Confirm。

支援:
- Request / Confirm
- Capture / Void (autoCapture=false 模式)
- Refund
- Preapproved Pay (自動扣款)

⚠️ HMAC string-to-sign 公式為依 v3 慣例推測
   (POST: ChannelSecret + ApiPath + Body + Nonce
    GET:  ChannelSecret + ApiPath + QueryString + Nonce)
   串接前請以官方 v4 PDF 驗證。

API 文件: 參見 references/linepay-payment-api.md

依賴:
    pip install requests
"""

import base64
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
class PaymentRequestData:
    """LINE Pay 建立交易資料"""
    amount: int  # 金額（整數，TWD 不含小數）
    currency: str = 'TWD'  # TWD / JPY / USD / THB
    order_id: str = ''  # 商家訂單編號（唯一）
    packages: List[Dict[str, any]] = field(default_factory=list)
    redirect_confirm_url: str = ''
    redirect_cancel_url: str = ''
    capture: bool = True  # False = 授權 + 後續手動 Capture
    product_name: str = ''
    options_extra: Optional[Dict[str, any]] = None


@dataclass
class LinePayResponse:
    success: bool
    return_code: str = ''
    return_message: str = ''
    transaction_id: str = ''  # 19 digits — 用字串避免 JS 精度遺失
    payment_url_web: str = ''
    payment_url_app: str = ''
    raw: Dict[str, any] = field(default_factory=dict)


# ============================================================================
# Service
# ============================================================================

class LinePayService:
    """
    LINE Pay v4 Online API.

    認證:
        - Channel ID + Channel Secret (LINE Pay Merchant Center 申請)
        - 每次請求需產生 Nonce (UUID4)
        - HMAC-SHA256 簽章放在 X-LINE-Authorization header
        - X-LINE-ChannelId / X-LINE-Authorization-Nonce 也是必帶

    端點:
        - POST /v3/payments/request                              建立交易
        - POST /v3/payments/{transactionId}/confirm              確認付款
        - POST /v3/payments/authorizations/{transactionId}/capture  手動請款
        - POST /v3/payments/authorizations/{transactionId}/void    取消授權
        - POST /v3/payments/{transactionId}/refund                 退款
        - GET  /v3/payments?transactionId=xxx                     查詢交易
        - POST /v3/payments/preapprovedPay/{regKey}/payment       自動扣款
    """

    SANDBOX_BASE = 'https://sandbox-api-pay.line.me'
    PROD_BASE = 'https://api-pay.line.me'

    def __init__(self, channel_id: str, channel_secret: str, is_test: bool = True):
        if not channel_id or not channel_secret:
            raise ValueError('LINE Pay 需要 ChannelId 與 ChannelSecret')
        self.channel_id = channel_id
        self.channel_secret = channel_secret
        self.base_url = self.SANDBOX_BASE if is_test else self.PROD_BASE
        self.is_test = is_test

    # -- Signing --------------------------------------------------------------

    def _sign(self, api_path: str, body_or_query: str, nonce: str) -> str:
        """
        HMAC-SHA256 簽章.

        ⚠️ 公式依 v3 慣例推測:
          - POST: ChannelSecret + ApiPath + RequestBody + Nonce
          - GET:  ChannelSecret + ApiPath + QueryString + Nonce
        輸出 base64.
        """
        message = self.channel_secret + api_path + body_or_query + nonce
        digest = hmac.new(
            self.channel_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256,
        ).digest()
        return base64.b64encode(digest).decode('utf-8')

    def _headers(self, signature: str, nonce: str) -> Dict[str, str]:
        return {
            'Content-Type': 'application/json',
            'X-LINE-ChannelId': self.channel_id,
            'X-LINE-Authorization-Nonce': nonce,
            'X-LINE-Authorization': signature,
        }

    # -- Operations -----------------------------------------------------------

    def request_payment(self, data: PaymentRequestData) -> LinePayResponse:
        """建立 LINE Pay 交易"""
        api_path = '/v3/payments/request'
        body = {
            'amount': data.amount,
            'currency': data.currency,
            'orderId': data.order_id or f'ORD{int(time.time())}',
            'packages': data.packages or [{
                'id': 'package-1',
                'amount': data.amount,
                'name': data.product_name or 'Order',
                'products': [{
                    'name': data.product_name or 'Item',
                    'quantity': 1,
                    'price': data.amount,
                }],
            }],
            'redirectUrls': {
                'confirmUrl': data.redirect_confirm_url,
                'cancelUrl': data.redirect_cancel_url,
            },
            'options': {
                'payment': {'capture': data.capture},
                **(data.options_extra or {}),
            },
        }
        return self._post(api_path, body)

    def confirm_payment(self, transaction_id: str, amount: int, currency: str = 'TWD') -> LinePayResponse:
        """確認付款 (Confirm) — amount/currency 必須與 Request 一致"""
        api_path = f'/v3/payments/{transaction_id}/confirm'
        body = {'amount': amount, 'currency': currency}
        return self._post(api_path, body)

    def capture(self, transaction_id: str, amount: int, currency: str = 'TWD') -> LinePayResponse:
        """手動請款 (autoCapture=false 模式)"""
        api_path = f'/v3/payments/authorizations/{transaction_id}/capture'
        body = {'amount': amount, 'currency': currency}
        return self._post(api_path, body)

    def void_auth(self, transaction_id: str) -> LinePayResponse:
        """取消授權"""
        api_path = f'/v3/payments/authorizations/{transaction_id}/void'
        return self._post(api_path, {})

    def refund(self, transaction_id: str, refund_amount: Optional[int] = None) -> LinePayResponse:
        """退款 (refund_amount 不填則全額退)"""
        api_path = f'/v3/payments/{transaction_id}/refund'
        body = {}
        if refund_amount is not None:
            body['refundAmount'] = refund_amount
        return self._post(api_path, body)

    def query_transaction(self, transaction_id: str) -> LinePayResponse:
        """查詢交易狀態"""
        api_path = '/v3/payments'
        query_string = f'transactionId={transaction_id}'
        return self._get(api_path, query_string)

    def preapproved_pay(self, reg_key: str, product_name: str, amount: int, order_id: str = '') -> LinePayResponse:
        """自動扣款 (Preapproved Pay)"""
        api_path = f'/v3/payments/preapprovedPay/{reg_key}/payment'
        body = {
            'amount': amount,
            'currency': 'TWD',
            'orderId': order_id or f'AUTO{int(time.time())}',
            'productName': product_name,
        }
        return self._post(api_path, body)

    # -- HTTP submit ----------------------------------------------------------

    def _post(self, api_path: str, body: Dict[str, any]) -> LinePayResponse:
        nonce = str(uuid.uuid4())
        body_str = json.dumps(body, ensure_ascii=False, separators=(',', ':'))
        signature = self._sign(api_path, body_str, nonce)
        url = self.base_url + api_path
        try:
            r = requests.post(url, headers=self._headers(signature, nonce), data=body_str.encode('utf-8'), timeout=30)
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f'LINE Pay API 連線失敗: {e}')
        return self._parse_response(r)

    def _get(self, api_path: str, query_string: str) -> LinePayResponse:
        nonce = str(uuid.uuid4())
        signature = self._sign(api_path, query_string, nonce)
        url = self.base_url + api_path + '?' + query_string
        try:
            r = requests.get(url, headers=self._headers(signature, nonce), timeout=30)
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f'LINE Pay API 連線失敗: {e}')
        return self._parse_response(r)

    def _parse_response(self, r: requests.Response) -> LinePayResponse:
        try:
            resp = r.json()
        except ValueError:
            return LinePayResponse(success=False, return_code=str(r.status_code), return_message=r.text[:200])

        return_code = resp.get('returnCode', '')
        is_success = (return_code == '0000') and r.status_code < 400

        info = resp.get('info', {}) or {}
        payment_url = info.get('paymentUrl', {}) or {}

        return LinePayResponse(
            success=is_success,
            return_code=return_code,
            return_message=resp.get('returnMessage', ''),
            transaction_id=str(info.get('transactionId', '')),  # 19-digit, keep as string
            payment_url_web=payment_url.get('web', ''),
            payment_url_app=payment_url.get('app', ''),
            raw=resp,
        )


# ============================================================================
# Examples
# ============================================================================

def example_payment_request():
    print('=== LINE Pay 建立交易 ===\n')
    svc = LinePayService(channel_id='YOUR_CHANNEL_ID', channel_secret='YOUR_CHANNEL_SECRET', is_test=True)
    resp = svc.request_payment(PaymentRequestData(
        amount=1050,
        currency='TWD',
        order_id=f'ORD{int(time.time())}',
        product_name='測試商品',
        redirect_confirm_url='https://your-shop.com/linepay/confirm',
        redirect_cancel_url='https://your-shop.com/linepay/cancel',
    ))
    if resp.success:
        print(f'[OK] transactionId: {resp.transaction_id}')
        print(f'web URL: {resp.payment_url_web}')
        print(f'app URL: {resp.payment_url_app}')
    else:
        print(f'[FAIL] {resp.return_code}: {resp.return_message}')


def example_payment_confirm():
    print('\n=== LINE Pay 確認交易 ===\n')
    svc = LinePayService('YOUR_CHANNEL_ID', 'YOUR_CHANNEL_SECRET', is_test=True)
    # transactionId 來自 redirectUrls.confirmUrl 的 query param
    resp = svc.confirm_payment(transaction_id='2024010100000000001', amount=1050, currency='TWD')
    if resp.success:
        print(f'[OK] 付款成功: {json.dumps(resp.raw, ensure_ascii=False)}')
    else:
        print(f'[FAIL] {resp.return_code}: {resp.return_message}')


def example_refund():
    print('\n=== LINE Pay 退款 ===\n')
    svc = LinePayService('YOUR_CHANNEL_ID', 'YOUR_CHANNEL_SECRET', is_test=True)
    resp = svc.refund(transaction_id='2024010100000000001', refund_amount=500)  # 部分退款 NT$500
    if resp.success:
        print('[OK] 退款成功')
    else:
        print(f'[FAIL] {resp.return_code}: {resp.return_message}')


def example_preapproved_pay():
    print('\n=== LINE Pay 自動扣款 ===\n')
    svc = LinePayService('YOUR_CHANNEL_ID', 'YOUR_CHANNEL_SECRET', is_test=True)
    # regKey 是當初 Request 時帶 options.payment.payType=PREAPPROVED 取得
    resp = svc.preapproved_pay(reg_key='regkey-abc', product_name='月費訂閱', amount=199)
    if resp.success:
        print(f'[OK] 自動扣款成功: transactionId={resp.transaction_id}')
    else:
        print(f'[FAIL] {resp.return_code}: {resp.return_message}')


if __name__ == '__main__':
    example_payment_request()
    example_payment_confirm()
    example_refund()
    example_preapproved_pay()
