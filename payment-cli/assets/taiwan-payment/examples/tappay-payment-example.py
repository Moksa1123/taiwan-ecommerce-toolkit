#!/usr/bin/env python3
"""
TapPay Python 範例 (後端部分)

依照 taiwan-payment-skill 規範撰寫。
TapPay 採兩段式架構:
  1. 前端 SDK 取得 Prime (60 秒 TTL，single-use)
  2. 後端用 Prime 呼叫 pay-by-prime

支援:
- pay-by-prime         一般付款
- pay-by-card-token    重複扣款（訂閱、回購快速結帳）
- refund               退款
- query                查詢交易

API 文件: 參見 references/tappay-payment-api.md

依賴:
    pip install requests
"""

import json
import time
from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional

import requests


# ============================================================================
# Data classes
# ============================================================================

@dataclass
class CardholderInfo:
    """TapPay cardholder 資料"""
    phone_number: str
    name: str
    email: str
    zip_code: str = ''
    address: str = ''
    national_id: str = ''


@dataclass
class TapPayResponse:
    success: bool
    status: int = 0  # 0 = 成功
    msg: str = ''
    rec_trade_id: str = ''
    bank_transaction_id: str = ''
    auth_code: str = ''
    card_secret: Optional[Dict[str, str]] = None  # 含 card_key + card_token (記憶卡片時)
    payment_url: str = ''  # 行動錢包付款導轉 URL
    raw: Dict[str, any] = field(default_factory=dict)


# ============================================================================
# Service
# ============================================================================

class TapPayService:
    """
    TapPay (CherryTech) 服務.

    認證金鑰:
        - Partner Key:  後端密鑰，用於認證後端 API 呼叫
        - App Key:      前端 SDK 公鑰，用於取 Prime（不放後端）
        - Merchant ID:  商家識別

    端點:
        - POST /tpc/payment/pay-by-prime         Prime 付款
        - POST /tpc/payment/pay-by-card-token    重複扣款
        - POST /tpc/transaction/refund           退款
        - POST /tpc/transaction/query            查詢
        - POST /tpc/transaction/cap-refund       延遲請款後退款
        - POST /tpc/card/remove                  解除綁卡

    Status code 對照（部分）:
        0      成功
        1      付款失敗
        2      參數錯誤
        3      Prime 錯誤（過期/已用）
        4      卡片資訊錯誤
        5      銀行風控
        7      卡片過期
        10003  Partner Key 錯誤
        10005  Merchant ID 錯誤
        88001  3DS 驗證失敗
    """

    SANDBOX_BASE = 'https://sandbox.tappaysdk.com'
    PROD_BASE = 'https://prod.tappayapis.com'

    def __init__(self, partner_key: str, merchant_id: str, is_test: bool = True):
        if not partner_key or not merchant_id:
            raise ValueError('TapPay 需要 Partner Key 與 Merchant ID')
        self.partner_key = partner_key
        self.merchant_id = merchant_id
        self.base_url = self.SANDBOX_BASE if is_test else self.PROD_BASE
        self.is_test = is_test

    @property
    def headers(self) -> Dict[str, str]:
        return {
            'x-api-key': self.partner_key,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

    # -- Operations -----------------------------------------------------------

    def pay_by_prime(
        self,
        prime: str,
        amount: int,
        order_number: str,
        cardholder: CardholderInfo,
        details: str = '',
        currency: str = 'TWD',
        remember: bool = False,
        result_url: Optional[Dict[str, str]] = None,
        delay_capture_in_days: int = 0,
        three_domain_secure: bool = False,
    ) -> TapPayResponse:
        """
        Prime 付款（單次）.

        Args:
            prime: 前端 SDK 取得的 prime token (60 秒過期)
            amount: 金額（TWD 整數）
            order_number: 商家訂單號（唯一）
            cardholder: 持卡人資料
            remember: True 會在回應內帶 card_secret (card_key + card_token)，可用於 pay-by-token
            result_url: {'frontend_redirect_url': '', 'backend_notify_url': '', 'go_back_url': ''}
            delay_capture_in_days: > 0 表示延遲請款（auth + capture）
            three_domain_secure: True 啟用 3DS
        """
        body = {
            'partner_key': self.partner_key,
            'prime': prime,
            'merchant_id': self.merchant_id,
            'details': details or order_number,
            'amount': amount,
            'currency': currency,
            'order_number': order_number,
            'cardholder': {
                'phone_number': cardholder.phone_number,
                'name': cardholder.name,
                'email': cardholder.email,
                'zip_code': cardholder.zip_code,
                'address': cardholder.address,
                'national_id': cardholder.national_id,
            },
            'remember': remember,
            'three_domain_secure': three_domain_secure,
        }
        if delay_capture_in_days > 0:
            body['delay_capture_in_days'] = delay_capture_in_days
        if result_url:
            body['result_url'] = result_url
        return self._submit('/tpc/payment/pay-by-prime', body)

    def pay_by_token(
        self,
        card_key: str,
        card_token: str,
        amount: int,
        order_number: str,
        details: str = '',
        currency: str = 'TWD',
    ) -> TapPayResponse:
        """重複扣款（訂閱、自動續訂）— 使用 pay-by-prime remember=True 取得的 card_key/card_token"""
        body = {
            'card_key': card_key,
            'card_token': card_token,
            'partner_key': self.partner_key,
            'merchant_id': self.merchant_id,
            'amount': amount,
            'currency': currency,
            'details': details or order_number,
            'order_number': order_number,
        }
        return self._submit('/tpc/payment/pay-by-card-token', body)

    def refund(self, rec_trade_id: str, amount: Optional[int] = None) -> TapPayResponse:
        """退款（amount 為 None 表示全額退）"""
        body = {
            'partner_key': self.partner_key,
            'rec_trade_id': rec_trade_id,
        }
        if amount is not None:
            body['amount'] = amount
        return self._submit('/tpc/transaction/refund', body)

    def query_transaction(
        self,
        rec_trade_id: Optional[str] = None,
        order_number: Optional[str] = None,
        bank_transaction_id: Optional[str] = None,
    ) -> TapPayResponse:
        """查詢交易"""
        filters: Dict[str, any] = {}
        if rec_trade_id:
            filters['rec_trade_id'] = rec_trade_id
        if order_number:
            filters['order_number'] = order_number
        if bank_transaction_id:
            filters['bank_transaction_id'] = bank_transaction_id
        body = {
            'partner_key': self.partner_key,
            'records_per_page': 50,
            'page': 0,
            'filters': filters,
            'order_by': {'attribute': 'time', 'is_descending': True},
        }
        return self._submit('/tpc/transaction/query', body)

    def remove_card(self, card_key: str, card_token: str) -> TapPayResponse:
        """解除綁卡"""
        body = {
            'partner_key': self.partner_key,
            'card_key': card_key,
            'card_token': card_token,
        }
        return self._submit('/tpc/card/remove', body)

    # -- HTTP submit ----------------------------------------------------------

    def _submit(self, path: str, body: Dict[str, any]) -> TapPayResponse:
        url = self.base_url + path
        try:
            r = requests.post(url, headers=self.headers, json=body, timeout=30)
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f'TapPay API 連線失敗: {e}')

        try:
            resp = r.json()
        except ValueError:
            return TapPayResponse(
                success=False,
                status=r.status_code,
                msg=f'回應非 JSON: {r.text[:200]}',
            )

        status = int(resp.get('status', -1))
        is_success = (status == 0) and r.status_code < 400

        return TapPayResponse(
            success=is_success,
            status=status,
            msg=resp.get('msg', ''),
            rec_trade_id=resp.get('rec_trade_id', ''),
            bank_transaction_id=resp.get('bank_transaction_id', ''),
            auth_code=resp.get('auth_code', ''),
            card_secret=resp.get('card_secret') or None,
            payment_url=resp.get('payment_url', ''),
            raw=resp,
        )


# ============================================================================
# Examples
# ============================================================================

def example_pay_by_prime():
    print('=== TapPay Prime 付款 ===\n')
    svc = TapPayService(
        partner_key='YOUR_PARTNER_KEY',  # 後端密鑰
        merchant_id='YOUR_MERCHANT_ID',
        is_test=True,
    )
    # prime 是前端 SDK (Direct Pay / TapPay Fields / Apple Pay 等) 取得的 token
    prime = 'PRIME_FROM_FRONTEND_SDK'  # 60 秒過期
    cardholder = CardholderInfo(
        phone_number='+886912345678',
        name='王小明',
        email='test@example.com',
    )
    resp = svc.pay_by_prime(
        prime=prime,
        amount=1050,
        order_number=f'ORD{int(time.time())}',
        cardholder=cardholder,
        details='測試訂單',
        remember=True,  # 拿 card_key + card_token 用於後續 pay-by-token
    )
    if resp.success:
        print(f'[OK] 付款成功')
        print(f'  rec_trade_id: {resp.rec_trade_id}')
        print(f'  auth_code:    {resp.auth_code}')
        if resp.card_secret:
            print(f'  card_key:     {resp.card_secret.get("card_key")}')
            print(f'  card_token:   {resp.card_secret.get("card_token")}')
    else:
        print(f'[FAIL] status={resp.status} msg={resp.msg}')


def example_pay_by_token():
    print('\n=== TapPay 重複扣款 (Token) ===\n')
    svc = TapPayService('YOUR_PARTNER_KEY', 'YOUR_MERCHANT_ID', is_test=True)
    # card_key / card_token 來自先前 pay_by_prime(remember=True) 的回應
    resp = svc.pay_by_token(
        card_key='SAVED_CARD_KEY',
        card_token='SAVED_CARD_TOKEN',
        amount=199,
        order_number=f'SUB{int(time.time())}',
        details='月費訂閱',
    )
    if resp.success:
        print(f'[OK] 訂閱扣款成功: rec_trade_id={resp.rec_trade_id}')
    else:
        print(f'[FAIL] status={resp.status} msg={resp.msg}')


def example_refund():
    print('\n=== TapPay 退款 ===\n')
    svc = TapPayService('YOUR_PARTNER_KEY', 'YOUR_MERCHANT_ID', is_test=True)
    resp = svc.refund(rec_trade_id='ABC123', amount=500)  # 部分退款 NT$500
    if resp.success:
        print('[OK] 退款成功')
    else:
        print(f'[FAIL] status={resp.status} msg={resp.msg}')


def example_query_transaction():
    print('\n=== TapPay 查詢交易 ===\n')
    svc = TapPayService('YOUR_PARTNER_KEY', 'YOUR_MERCHANT_ID', is_test=True)
    resp = svc.query_transaction(order_number='ORD123456')
    print(json.dumps(resp.raw, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    example_pay_by_prime()
    example_pay_by_token()
    example_refund()
    example_query_transaction()
