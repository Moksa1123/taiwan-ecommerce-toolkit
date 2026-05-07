#!/usr/bin/env python3
"""
PChomePay 拍錢包 Python 完整範例

依照 taiwan-payment-skill 最高規範撰寫
支援: 信用卡 (一次付清 / 分期)、ATM 虛擬帳號、超商代碼繳費、訂單查詢、退款

API 文件: https://web.pchomepay.com.tw/api-setting/environment-setting
參考文件: taiwan-payment/references/pchomepay-payment-api.md

特色:
    - REST + JSON：所有請求 / 回應皆為 JSON
    - 兩階段認證：HTTP Basic Auth(APP_ID:SECRET) -> /v1/token -> pcpay-token Header
    - Token 預設 8 小時 (28,800 秒)：本範例會自動快取並在到期前自動 refresh
    - 手續費內扣：訂單金額 - 手續費 = 實際入帳

防火牆白名單:
    PChomePay Notify 來源 IP = 113.196.231.190
    請務必加入合作方 firewall 白名單，否則收不到付款 / 退款 / 物流通知。

依賴:
    pip install requests
"""

import base64
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


# ----------------------------------------------------------------------------
# Dataclasses
# ----------------------------------------------------------------------------


PayType = Literal['CARD', 'PI', 'ATM', 'IPL7', 'IPLFM', 'IPLHL', 'BCODE']


@dataclass
class PChomePayItem:
    """商品資訊 (items[*])"""
    name: str
    url: str                                          # 必須以 http:// 或 https:// 開頭


@dataclass
class PChomePayCreditOrder:
    """跳轉付款頁訂單 (POST /v1/payment) — 信用卡情境"""
    order_id: str                                     # <=50, 英數 + - _
    amount: int                                       # CARD: 30 ~ 199,999
    items: List[PChomePayItem]
    return_url: Optional[str] = None
    fail_return_url: Optional[str] = None
    notify_url: Optional[str] = None
    buyer_email: Optional[str] = None
    card_installment: Optional[str] = None            # "1,3,6,12,18,24"
    member_key: Optional[str] = None                  # 平台會員 ID (記憶卡用)
    platform_code: Optional[str] = None
    return_timer: Optional[Literal['Y', 'N']] = None  # Y: 倒數 10 秒；N: 立即跳轉


@dataclass
class PChomePayAtmOrder:
    """幕後取號 ATM 虛擬帳號 (POST /v1/payment/atmva)"""
    order_id: str
    amount: int                                       # 1 ~ 49,999
    item_name: str
    item_url: str
    buyer_name: str
    buyer_mobile: str
    expire_days: int = 5                              # 1 ~ 5
    atm_bank: str = '011'                             # 預設上海商銀
    notify_url: Optional[str] = None
    buyer_email: Optional[str] = None
    platform_code: Optional[str] = None


@dataclass
class PChomePayBarcodeOrder:
    """幕後取號 超商代碼繳費 (POST /v1/payment/barcode)"""
    order_id: str
    amount: int                                       # 25 ~ 20,000
    items: List[PChomePayItem]
    buyer_name: str                                   # <=50
    buyer_mobile: str                                 # 09 開頭 10 碼
    expire_days: int = 7                              # 1 ~ 7
    notify_url: Optional[str] = None
    buyer_email: Optional[str] = None
    platform_code: Optional[str] = None


@dataclass
class PChomePayRefundRequest:
    """退款請求 (POST /v1/refund)"""
    order_id: str
    refund_id: str                                    # <=50, 不可重複
    trade_amount: int


@dataclass
class PChomePayResponse:
    """通用回應 wrapper"""
    success: bool
    status_code: int
    data: Dict[str, Any] = field(default_factory=dict)
    error_type: Optional[str] = None
    error_code: Optional[int] = None
    error_message: Optional[str] = None


# ----------------------------------------------------------------------------
# Service
# ----------------------------------------------------------------------------


class PChomePayService:
    """
    PChomePay 拍錢包金流服務 (REST + JSON)

    認證流程:
        1. POST /v1/token  +  Authorization: Basic base64(APP_ID:SECRET)
           -> { "token": "...", "expired_in": 28800, "expired_timestamp": ... }
        2. 後續請求帶 Header: pcpay-token: <token>

    本範例會自動快取 token，在到期前 (預留 60 秒緩衝) 自動 refresh。

    環境:
        sandbox = "https://sandbox-api.pchomepay.com.tw"
        prod    = "https://api.pchomepay.com.tw"

    Notify 來源 IP (firewall 白名單):
        113.196.231.190
    """

    SANDBOX_BASE = 'https://sandbox-api.pchomepay.com.tw'
    PROD_BASE = 'https://api.pchomepay.com.tw'

    NOTIFY_SOURCE_IP = '113.196.231.190'
    TOKEN_REFRESH_BUFFER_SECONDS = 60

    def __init__(
        self,
        app_id: str,
        secret: str,
        is_production: bool = False,
        timeout: int = 30,
    ):
        if not HAS_REQUESTS:
            raise ImportError('需要安裝 requests: pip install requests')

        self.app_id = app_id
        self.secret = secret
        self.base_url = self.PROD_BASE if is_production else self.SANDBOX_BASE
        self.timeout = timeout

        # token cache
        self._token: Optional[str] = None
        self._token_expired_at: float = 0.0

        self._session = requests.Session()

    # ------------------------------------------------------------------
    # Token management
    # ------------------------------------------------------------------

    def _basic_auth_header(self) -> str:
        """Authorization: Basic base64(APP_ID:SECRET)"""
        raw = f'{self.app_id}:{self.secret}'.encode('utf-8')
        return 'Basic ' + base64.b64encode(raw).decode('ascii')

    def get_token(self, force_refresh: bool = False) -> str:
        """
        取得 pcpay-token，會自動 cache。Token 預設 8 小時，到期前
        TOKEN_REFRESH_BUFFER_SECONDS 秒會自動 refresh。

        Args:
            force_refresh: True 則忽略 cache 直接重打 /v1/token

        Returns:
            str: 有效的 pcpay-token
        """
        now = time.time()
        if (
            not force_refresh
            and self._token
            and now < self._token_expired_at - self.TOKEN_REFRESH_BUFFER_SECONDS
        ):
            return self._token

        url = f'{self.base_url}/v1/token'
        headers = {
            'Authorization': self._basic_auth_header(),
            'Content-Type': 'application/json',
        }
        resp = self._session.post(url, headers=headers, timeout=self.timeout)
        resp.raise_for_status()
        body = resp.json()

        token = body.get('token')
        if not token:
            raise RuntimeError(f'PChomePay token 取得失敗: {body}')

        self._token = token
        # 優先用 expired_timestamp，若無再以 expired_in + now 計算
        if body.get('expired_timestamp'):
            self._token_expired_at = float(body['expired_timestamp'])
        else:
            self._token_expired_at = now + float(body.get('expired_in', 28800))

        return token

    def _auth_headers(self) -> Dict[str, str]:
        return {
            'pcpay-token': self.get_token(),
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

    # ------------------------------------------------------------------
    # HTTP wrapper
    # ------------------------------------------------------------------

    def _request(
        self,
        method: Literal['GET', 'POST'],
        path: str,
        json: Optional[Dict[str, Any]] = None,
    ) -> PChomePayResponse:
        url = f'{self.base_url}{path}'
        try:
            resp = self._session.request(
                method,
                url,
                headers=self._auth_headers(),
                json=json,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            return PChomePayResponse(
                success=False,
                status_code=0,
                error_message=str(exc),
            )

        try:
            body = resp.json()
        except ValueError:
            body = {'raw': resp.text}

        if resp.ok and 'error_type' not in body:
            return PChomePayResponse(success=True, status_code=resp.status_code, data=body)

        return PChomePayResponse(
            success=False,
            status_code=resp.status_code,
            data=body,
            error_type=body.get('error_type'),
            error_code=body.get('code'),
            error_message=body.get('message'),
        )

    # ------------------------------------------------------------------
    # Order creation
    # ------------------------------------------------------------------

    def create_credit_order(self, order: PChomePayCreditOrder) -> PChomePayResponse:
        """
        建立信用卡 (跳轉付款頁) 訂單  POST /v1/payment

        Returns:
            PChomePayResponse.data 內含 order_id / payment_url
            -> 將消費者導頁至 payment_url 完成付款
        """
        if order.amount < 30 or order.amount > 199_999:
            raise ValueError('CARD 金額需介於 30 ~ 199,999')

        body: Dict[str, Any] = {
            'order_id': order.order_id,
            'pay_type': ['CARD'],
            'amount': order.amount,
            'items': [{'name': i.name, 'url': i.url} for i in order.items],
        }
        if order.return_url:
            body['return_url'] = order.return_url
        if order.fail_return_url:
            body['fail_return_url'] = order.fail_return_url
        if order.notify_url:
            body['notify_url'] = order.notify_url
        if order.buyer_email:
            body['buyer_email'] = order.buyer_email
        if order.card_installment:
            body['card_installment'] = order.card_installment
        if order.member_key:
            body['member_key'] = order.member_key
        if order.platform_code:
            body['platform_code'] = order.platform_code
        if order.return_timer:
            body['return_timer'] = order.return_timer

        return self._request('POST', '/v1/payment', body)

    def create_atm_order(self, order: PChomePayAtmOrder) -> PChomePayResponse:
        """
        建立 ATM 幕後取號訂單  POST /v1/payment/atmva

        Returns:
            PChomePayResponse.data 內含 order_id / virtual_account / bank_id / expire_date
        """
        if order.amount < 1 or order.amount > 49_999:
            raise ValueError('ATM 金額需介於 1 ~ 49,999')
        if not (1 <= order.expire_days <= 5):
            raise ValueError('expire_days 需介於 1 ~ 5 天')

        body: Dict[str, Any] = {
            'order_id': order.order_id,
            'amount': order.amount,
            'expire_days': order.expire_days,
            'item_name': order.item_name,
            'item_url': order.item_url,
            'atm_bank': order.atm_bank,
            'buyer_name': order.buyer_name,
            'buyer_mobile': order.buyer_mobile,
        }
        if order.notify_url:
            body['notify_url'] = order.notify_url
        if order.buyer_email:
            body['buyer_email'] = order.buyer_email
        if order.platform_code:
            body['platform_code'] = order.platform_code

        return self._request('POST', '/v1/payment/atmva', body)

    def create_barcode_order(self, order: PChomePayBarcodeOrder) -> PChomePayResponse:
        """
        建立超商代碼繳費 幕後取號訂單  POST /v1/payment/barcode

        Returns:
            PChomePayResponse.data 內含 pincode / barcode1~3 / expire_date
        """
        if order.amount < 25 or order.amount > 20_000:
            raise ValueError('BCODE 金額需介於 25 ~ 20,000')
        if not (1 <= order.expire_days <= 7):
            raise ValueError('expire_days 需介於 1 ~ 7 天')

        body: Dict[str, Any] = {
            'order_id': order.order_id,
            'amount': order.amount,
            'expire_days': order.expire_days,
            'items': [{'name': i.name, 'url': i.url} for i in order.items],
            'buyer_name': order.buyer_name,
            'buyer_mobile': order.buyer_mobile,
        }
        if order.notify_url:
            body['notify_url'] = order.notify_url
        if order.buyer_email:
            body['buyer_email'] = order.buyer_email
        if order.platform_code:
            body['platform_code'] = order.platform_code

        return self._request('POST', '/v1/payment/barcode', body)

    # ------------------------------------------------------------------
    # Order query / refund
    # ------------------------------------------------------------------

    def query_order(self, order_id: str) -> PChomePayResponse:
        """訂單查詢  GET /v1/payment/{order_id}"""
        return self._request('GET', f'/v1/payment/{order_id}')

    def refund(self, refund_req: PChomePayRefundRequest) -> PChomePayResponse:
        """
        建立退款  POST /v1/refund

        退款規則摘要:
            - 信用卡分期 / 超商取貨 / 代碼繳費 → 僅支援全額退款
            - 信用卡一次付清 / 拍錢包 / ATM → 支援部分退款
            - 退款手續費: ATM / 超商取貨 / 代碼繳費 每筆 15 元
            - 帳戶餘額需 >= 退款金額 + 退款手續費
        """
        if refund_req.trade_amount <= 0:
            raise ValueError('退款金額需 > 0')

        body = {
            'order_id': refund_req.order_id,
            'refund_id': refund_req.refund_id,
            'trade_amount': refund_req.trade_amount,
        }
        return self._request('POST', '/v1/refund', body)

    def query_refund(self, refund_id: str) -> PChomePayResponse:
        """退款查詢  GET /v1/refund/{refund_id}"""
        return self._request('GET', f'/v1/refund/{refund_id}')

    def query_balance(self) -> PChomePayResponse:
        """帳戶餘額查詢  GET /v1/balance"""
        return self._request('GET', '/v1/balance')

    def list_atm_banks(self) -> PChomePayResponse:
        """ATM 支援銀行清單  GET /v1/payment/atm/banks"""
        return self._request('GET', '/v1/payment/atm/banks')

    def list_card_banks(self) -> PChomePayResponse:
        """信用卡分期支援銀行  GET /v1/payment/card/banks"""
        return self._request('GET', '/v1/payment/card/banks')


# ----------------------------------------------------------------------------
# Examples
# ----------------------------------------------------------------------------


def example_token_refresh(service: PChomePayService) -> None:
    print('[範例 1] Token auto-refresh 機制 (不實際打 API)')
    print('-' * 60)
    print(f'  Base URL: {service.base_url}')
    print(f'  APP_ID:   {service.app_id[:8]}...')
    print(f'  Refresh buffer: {service.TOKEN_REFRESH_BUFFER_SECONDS} 秒')
    print(f'  Notify 來源 IP (記得加 firewall 白名單): {service.NOTIFY_SOURCE_IP}')
    print()


def example_create_credit_order(service: PChomePayService) -> None:
    print('[範例 2] 建立信用卡跳轉付款頁訂單 POST /v1/payment')
    print('-' * 60)
    order = PChomePayCreditOrder(
        order_id=f'B2C{int(time.time())}',
        amount=2675,
        items=[
            PChomePayItem(
                name='Chrome Dino Camp Shirt',
                url='https://shop.example.com/items/chrome-dino-shirt',
            ),
        ],
        return_url='https://shop.example.com/success',
        fail_return_url='https://shop.example.com/failed',
        notify_url='https://shop.example.com/api/pchomepay/notify',
        card_installment='1,3,6,12',
    )
    print(f'  order_id: {order.order_id}')
    print(f'  amount:   {order.amount}')
    print(f'  分期:     {order.card_installment}')
    print('  （示範僅組 payload，未實際呼叫 API；正式 sandbox 需先取得 APP_ID/SECRET）')
    print()


def example_create_atm_order(service: PChomePayService) -> None:
    print('[範例 3] 建立 ATM 幕後取號訂單 POST /v1/payment/atmva')
    print('-' * 60)
    order = PChomePayAtmOrder(
        order_id=f'B2CATM{int(time.time())}',
        amount=500,
        item_name='休閒褲',
        item_url='https://www.example.com.tw',
        buyer_name='王大明',
        buyer_mobile='0912345678',
        expire_days=3,
        atm_bank='812',                  # 台新
        notify_url='https://shop.example.com/api/pchomepay/notify',
    )
    print(f'  order_id: {order.order_id}')
    print(f'  ATM 銀行: {order.atm_bank}')
    print(f'  繳費期限: {order.expire_days} 天')
    print('  （示範僅組 payload，未實際呼叫 API）')
    print()


def example_create_barcode_order(service: PChomePayService) -> None:
    print('[範例 4] 建立超商代碼繳費訂單 POST /v1/payment/barcode')
    print('-' * 60)
    order = PChomePayBarcodeOrder(
        order_id=f'B2CBARCODE{int(time.time())}',
        amount=500,
        items=[
            PChomePayItem(name='Chrome Dino Camp Shirt', url='https://shop.example.com'),
        ],
        buyer_name='John Doe',
        buyer_mobile='0912345678',
        expire_days=7,
        notify_url='https://shop.example.com/api/pchomepay/notify',
    )
    print(f'  order_id: {order.order_id}')
    print(f'  amount:   {order.amount}')
    print(f'  expire:   {order.expire_days} 天')
    print('  （示範僅組 payload，未實際呼叫 API）')
    print()


def example_query_order(service: PChomePayService) -> None:
    print('[範例 5] 訂單查詢 GET /v1/payment/{order_id}')
    print('-' * 60)
    print('  service.query_order("B2C1695210352")')
    print('  -> response.data 含 status (S/W/F) / pay_type / payment_info / amount ...')
    print()


def example_refund(service: PChomePayService) -> None:
    print('[範例 6] 建立退款 POST /v1/refund')
    print('-' * 60)
    refund = PChomePayRefundRequest(
        order_id='B2C1695210352',
        refund_id='B2C1695210352-Refund',
        trade_amount=100,
    )
    print(f'  order_id:     {refund.order_id}')
    print(f'  refund_id:    {refund.refund_id}')
    print(f'  trade_amount: {refund.trade_amount}')
    print('  注意:')
    print('    - 信用卡分期 / 超商取貨 / 代碼繳費 → 僅支援全額退款')
    print('    - ATM / 超商取貨 / 代碼繳費 每筆退款手續費 15 元')
    print('    - 帳戶餘額須 >= 退款金額 + 退款手續費')
    print()


if __name__ == '__main__':
    print('=' * 60)
    print('PChomePay 拍錢包金流 - Python 範例')
    print('=' * 60)
    print()

    if not HAS_REQUESTS:
        print('（缺 requests 套件，僅展示資料結構）')
        print('安裝指令: pip install requests')
        print()

        # 建立 service 物件會 raise ImportError；改示範資料結構
        order = PChomePayCreditOrder(
            order_id='B2C0000000001',
            amount=1000,
            items=[PChomePayItem(name='範例', url='https://example.com')],
        )
        print(f'CreditOrder dataclass: order_id={order.order_id} amount={order.amount}')
        exit(0)

    # 注意: 請替換為您的測試 APP_ID / SECRET
    service = PChomePayService(
        app_id='YOUR_SANDBOX_APP_ID',
        secret='YOUR_SANDBOX_SECRET',
        is_production=False,
    )

    example_token_refresh(service)
    example_create_credit_order(service)
    example_create_atm_order(service)
    example_create_barcode_order(service)
    example_query_order(service)
    example_refund(service)

    print('=' * 60)
    print('範例執行完成')
    print('=' * 60)
