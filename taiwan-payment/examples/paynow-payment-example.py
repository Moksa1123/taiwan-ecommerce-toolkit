#!/usr/bin/env python3
"""
PayNow 立吉富 Python 完整範例 (現代版 PaymentIntent API)

依照 taiwan-payment-skill 最高規範撰寫
聚焦現代版 PaymentIntent / Customer / Refund REST API；
傳統版 (cashflow) 提供 stub 供既有商家對照。

API 文件: https://docs.paynow.com.tw/
參考文件: taiwan-payment/references/paynow-payment-api.md

⚠ 重要提醒 (請於上線前確認):
    PayNow 現代版 API 文件聚焦於 request schemas，部分回應的 result 欄位
    僅以 "依場景變化" 描述，並未列出完整鍵名。本檔 dataclass / 解析邏輯
    中的 result_xxx 欄位係依文件示意推導 (例如 auth_code / last4 /
    payment_code / virtual_account / redirect_url / tokenized_card_id /
    deferred_payment_id 等)，**正式上線前請以 PayNow 業務窗口提供之
    完整回應規格為準，並依需要調整本範例的欄位名稱。**

API Base URL:
    PayNow 現代版的實際 API 主機由 PayNow 業務窗口提供 (常見候選網域:
    https://api.paynow.com.tw 或 https://gateway.paynow.com.tw)；
    PayNow 文件範例顯示為 docs.paynow.com.tw，那是文件站，非實際 API host。
    本範例採用 https://api.paynow.com.tw 作為預設，**請依實際開通信件確認**。

依賴:
    pip install requests
"""

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


# ----------------------------------------------------------------------------
# Dataclasses (PaymentIntent API)
# ----------------------------------------------------------------------------


PayMethod = Literal[
    'CreditCard',
    'CreditCardInstallment',
    'ATM',
    'ConvenienceStore',
    'LINEPayOnline',
    'LINEPayOffline',
    'ApplePay',
    'ApplePayDeferred',
]


@dataclass
class PayNowAddress:
    country: str = 'TW'
    locality: str = ''
    address1: str = ''
    address2: str = ''
    administrative_area: str = ''
    postal_code: str = ''


@dataclass
class PayNowCustomerData:
    """POST /api/v1/customers"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone_code: Optional[str] = None              # 例: "886"
    phone_number: Optional[str] = None
    address: Optional[PayNowAddress] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class PayNowPaymentIntentData:
    """POST /api/v1/payment-intents"""
    amount: float                                  # < 1_000_000_000_000
    currency: str = 'TWD'
    payment_no: Optional[str] = None              # 不指定則系統自動產生
    description: Optional[str] = None
    result_url: Optional[str] = None              # 前景轉跳
    webhook_url: Optional[str] = None             # 後端通知
    allowed_payment_methods: Optional[List[PayMethod]] = None
    allow_installments: Optional[List[int]] = None  # subset of [3,6,9,12,18,24]
    expire_days: Optional[int] = None             # 僅 ATM / ConvenienceStore 有效
    customer: Optional[str] = None                # customer_uuid
    line_pay_online_info: Optional[Dict[str, Any]] = None
    line_pay_offline_info: Optional[Dict[str, Any]] = None
    apple_pay_deferred_info: Optional[Dict[str, Any]] = None


@dataclass
class PayNowCheckoutData:
    """POST /api/v1/payment-intents/{id}/checkout"""
    payment_intent_id: str
    key: str                                      # 公鑰
    secret: str                                   # PaymentIntent secret
    payment_method_type: PayMethod
    payment_method_data: Dict[str, Any] = field(default_factory=dict)
    use_paynow_sdk: bool = False
    payment_no: Optional[str] = None
    session_id: Optional[str] = None
    otp_flag: Optional[bool] = None
    meta: Optional[Dict[str, Any]] = None


@dataclass
class PayNowRefundData:
    """POST /api/v1/payment-intents/{id}/refunds"""
    payment_intent_id: str
    amount: float
    reason: str                                   # <=255
    bank_code: Optional[str] = None              # ATM 退款必填
    bank_branch_code: Optional[str] = None
    bank_account: Optional[str] = None


@dataclass
class PayNowApplePaySessionData:
    """POST /api/v2/apple-pay-session"""
    merchant_identifier: str                      # merchant.xxx.xxx
    display_name: str                             # <=64 UTF-8
    initiative: str = 'web'
    initiative_context: str = ''


@dataclass
class PayNowApplePayConfirmData:
    """POST /api/v1/apple-pay-session"""
    merchant_identifier: str
    validation_url: str                           # event.validationURL
    domain_name: str
    display_name: str


@dataclass
class PayNowAPIResponse:
    """
    PaymentIntent API 通用 wrapper

    依文件範例:
        {
          "status": 200,
          "type": "success",
          "message": "Success",
          "result": { ... },
          "requestId": "uuid",
          "paginate": null
        }
    """
    success: bool
    status: int
    type_: str = ''
    message: str = ''
    result: Any = None
    request_id: str = ''
    paginate: Any = None
    error: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)


# ----------------------------------------------------------------------------
# Modern Service
# ----------------------------------------------------------------------------


class PayNowModernService:
    """
    PayNow 現代版 PaymentIntent / Customer / Refund REST API

    認證: Authorization: Bearer <API_KEY>
    請求 / 回應均為 JSON，UTF-8。

    支援付款方式 (透過 allowedPaymentMethods 或 paymentMethodType):
        CreditCard / CreditCardInstallment / ATM / ConvenienceStore /
        LINEPayOnline / LINEPayOffline / ApplePay / ApplePayDeferred

    ⚠ Apple Pay session 端點: 新整合請優先使用 v2 (request_apple_pay_session)；
        v1 (confirm_apple_pay) 用於 ApplePaySession.onvalidatemerchant 階段。

    ⚠ 文件 caveat:
        PayNow 提供完整 request schema，但 result 欄位以 "依場景變化" 描述。
        本範例對 result 採 raw dict 透傳，請依實測回應再封裝專屬 dataclass。
    """

    # PayNow 業務窗口會提供實際 production base URL；以下為文件展示用網域。
    # 文件 base URL 為 https://docs.paynow.com.tw/api/v1，那是文件站。
    DEFAULT_BASE_URL = 'https://api.paynow.com.tw'              # 待 PayNow 確認
    ALTERNATE_BASE_URL = 'https://gateway.paynow.com.tw'         # 傳統版 cashflow 主域

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        timeout: int = 30,
    ):
        if not HAS_REQUESTS:
            raise ImportError('需要安裝 requests: pip install requests')

        self.api_key = api_key
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip('/')
        self.timeout = timeout
        self._session = requests.Session()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _headers(self) -> Dict[str, str]:
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

    def _request(
        self,
        method: Literal['GET', 'POST', 'DELETE'],
        path: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> PayNowAPIResponse:
        url = f'{self.base_url}{path}'
        try:
            resp = self._session.request(
                method,
                url,
                headers=self._headers(),
                json=json,
                params=params,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            return PayNowAPIResponse(success=False, status=0, error=str(exc))

        try:
            body = resp.json()
        except ValueError:
            return PayNowAPIResponse(
                success=False,
                status=resp.status_code,
                error='Non-JSON response',
                raw={'text': resp.text},
            )

        type_ = body.get('type', '')
        success = resp.ok and type_ != 'error'

        return PayNowAPIResponse(
            success=success,
            status=body.get('status', resp.status_code),
            type_=type_,
            message=body.get('message', ''),
            result=body.get('result'),
            request_id=body.get('requestId', ''),
            paginate=body.get('paginate'),
            error=body.get('message') if not success else None,
            raw=body,
        )

    # ------------------------------------------------------------------
    # PaymentIntent
    # ------------------------------------------------------------------

    def create_payment_intent(
        self, data: PayNowPaymentIntentData
    ) -> PayNowAPIResponse:
        """
        建立 PaymentIntent  POST /api/v1/payment-intents

        result 預期含 (依文件示意):
            id, paymentNo, status, checkout_url, ...
        """
        if data.amount <= 0:
            raise ValueError('amount 需大於 0')
        if data.amount >= 1_000_000_000_000:
            raise ValueError('amount 限制 < 1,000,000,000,000')

        body: Dict[str, Any] = {
            'amount': data.amount,
            'currency': data.currency,
        }
        if data.payment_no is not None:
            body['paymentNo'] = data.payment_no
        if data.description:
            body['description'] = data.description
        if data.result_url:
            body['resultUrl'] = data.result_url
        if data.webhook_url:
            body['webhookUrl'] = data.webhook_url
        if data.allowed_payment_methods:
            body['allowedPaymentMethods'] = data.allowed_payment_methods
        if data.allow_installments:
            body['allowInstallments'] = data.allow_installments
        if data.expire_days is not None:
            body['expireDays'] = data.expire_days
        if data.customer:
            body['customer'] = data.customer
        if data.line_pay_online_info:
            body['linePayOnlineInfo'] = data.line_pay_online_info
        if data.line_pay_offline_info:
            body['linePayOfflineInfo'] = data.line_pay_offline_info
        if data.apple_pay_deferred_info:
            body['applePayDeferredInfo'] = data.apple_pay_deferred_info

        return self._request('POST', '/api/v1/payment-intents', body)

    def checkout(self, data: PayNowCheckoutData) -> PayNowAPIResponse:
        """
        付款執行  POST /api/v1/payment-intents/{id}/checkout

        ⚠ 此 API 需另行向 PayNow 業務申請開通；通常用於商家自建表單流程。

        result 依 paymentMethodType 不同會帶不同欄位 (依文件示意):
            CreditCard 成功:        result.auth_code, result.last4
            CreditCard With Token:  result.tokenized_card_id (後續可重複使用)
            CreditCard 3D Secure:   result.redirect_url (需轉址完成 3DS)
            ATM Pending Review:     result.bank_code, result.virtual_account, result.expire_at
            ConvenienceStore Ibon:  result.payment_code, result.expire_at
            LINE Pay Online:        result.redirect_url
            ApplePay 成功:           result.auth_code, result.last4
            ApplePay Deferred:      result.deferred_payment_id
        """
        body: Dict[str, Any] = {
            'key': data.key,
            'secret': data.secret,
            'paymentMethodType': data.payment_method_type,
            'paymentMethodData': data.payment_method_data,
            'usePayNowSdk': data.use_paynow_sdk,
        }
        if data.payment_no is not None:
            body['paymentNo'] = data.payment_no
        if data.session_id:
            body['sessionId'] = data.session_id
        if data.otp_flag is not None:
            body['otpFlag'] = data.otp_flag
        if data.meta:
            body['meta'] = data.meta

        return self._request(
            'POST',
            f'/api/v1/payment-intents/{data.payment_intent_id}/checkout',
            body,
        )

    def retrieve_payment_intent(self, payment_intent_id: str) -> PayNowAPIResponse:
        """訂單查詢  GET /api/v1/payment-intents/{id}"""
        return self._request('GET', f'/api/v1/payment-intents/{payment_intent_id}')

    # ------------------------------------------------------------------
    # Refund
    # ------------------------------------------------------------------

    def refund(self, data: PayNowRefundData) -> PayNowAPIResponse:
        """
        建立退款  POST /api/v1/payment-intents/{id}/refunds

        ATM 退款需帶 bank_code / bank_branch_code / bank_account；
        信用卡 / Apple Pay / LINE Pay 直接走原通路退款，免帶銀行欄位。

        result.status 可能值: success / failed / rejected / processing / validation_error
        """
        if data.amount <= 0:
            raise ValueError('退款金額需 > 0')
        if len(data.reason) > 255:
            raise ValueError('reason 限 255 字元')

        body: Dict[str, Any] = {
            'amount': data.amount,
            'reason': data.reason,
        }
        if data.bank_code:
            body['bankCode'] = data.bank_code
        if data.bank_branch_code:
            body['bankBranchCode'] = data.bank_branch_code
        if data.bank_account:
            body['bankAccount'] = data.bank_account

        return self._request(
            'POST',
            f'/api/v1/payment-intents/{data.payment_intent_id}/refunds',
            body,
        )

    def list_refunds(
        self, page: int = 1, limit: int = 10
    ) -> PayNowAPIResponse:
        """退款列表  GET /api/v1/refunds"""
        return self._request(
            'GET', '/api/v1/refunds', params={'Page': page, 'Limit': limit}
        )

    def retrieve_refund(self, refund_uuid: str) -> PayNowAPIResponse:
        """退款查詢  GET /api/v1/refunds/{uuid}"""
        return self._request('GET', f'/api/v1/refunds/{refund_uuid}')

    # ------------------------------------------------------------------
    # Apple Pay
    # ------------------------------------------------------------------

    def request_apple_pay_session(
        self, data: PayNowApplePaySessionData
    ) -> PayNowAPIResponse:
        """
        Request Apple Pay session (v2)  POST /api/v2/apple-pay-session

        新整合請優先使用 v2。
        """
        body = {
            'merchant_identifier': data.merchant_identifier,
            'display_name': data.display_name,
            'initiative': data.initiative,
            'initiative_context': data.initiative_context,
        }
        return self._request('POST', '/api/v2/apple-pay-session', body)

    def confirm_apple_pay(
        self, data: PayNowApplePayConfirmData
    ) -> PayNowAPIResponse:
        """
        Confirm Apple Pay session (v1)  POST /api/v1/apple-pay-session

        於 ApplePaySession.onvalidatemerchant 收到 event.validationURL 時呼叫。
        """
        body = {
            'merchant_identifier': data.merchant_identifier,
            'validation_url': data.validation_url,
            'domain_name': data.domain_name,
            'display_name': data.display_name,
        }
        return self._request('POST', '/api/v1/apple-pay-session', body)

    def cancel_apple_pay_deferred(
        self, payment_intent_uuid: str, reason: str
    ) -> PayNowAPIResponse:
        """
        Apple Pay Deferred Cancel
        POST /api/v1/payment-intents/apple-pay-deferreds/{uuid}/cancel
        """
        if len(reason) > 500:
            raise ValueError('reason 限 500 字元')
        return self._request(
            'POST',
            f'/api/v1/payment-intents/apple-pay-deferreds/{payment_intent_uuid}/cancel',
            {'reason': reason},
        )

    # ------------------------------------------------------------------
    # Customer / Card Token
    # ------------------------------------------------------------------

    def create_customer(self, data: PayNowCustomerData) -> PayNowAPIResponse:
        """建立 Customer  POST /api/v1/customers"""
        body: Dict[str, Any] = {}
        if data.first_name:
            body['first_name'] = data.first_name
        if data.last_name:
            body['last_name'] = data.last_name
        if data.email:
            body['email'] = data.email
        if data.phone_code:
            body['phone_code'] = data.phone_code
        if data.phone_number:
            body['phone_number'] = data.phone_number
        if data.address:
            body['address'] = {
                'country': data.address.country,
                'locality': data.address.locality,
                'address1': data.address.address1,
                'address2': data.address.address2,
                'administrative_area': data.address.administrative_area,
                'postal_code': data.address.postal_code,
            }
        if data.metadata:
            body['metadata'] = data.metadata

        return self._request('POST', '/api/v1/customers', body)

    def retrieve_customer(self, customer_uuid: str) -> PayNowAPIResponse:
        """Customer 查詢  GET /api/v1/customers/{customer_uuid}"""
        return self._request('GET', f'/api/v1/customers/{customer_uuid}')

    def retrieve_card_token(self, customer_uuid: str) -> PayNowAPIResponse:
        """
        查詢 Customer 名下的記憶卡片  GET /api/v1/customers/{uuid}/card-tokens

        result 為 array，每個元素含 id / last4 / bin / brand / expire_month / expire_year
        """
        return self._request(
            'GET', f'/api/v1/customers/{customer_uuid}/card-tokens'
        )


# ----------------------------------------------------------------------------
# Legacy Service (stub for existing 商家)
# ----------------------------------------------------------------------------


class PayNowLegacyService:
    """
    PayNow 傳統版 (cashflow / etopm.aspx) 簡要 stub

    ⚠ 新接商家請改用 PayNowModernService；此 class 僅供既有整合維護參考。
    傳統版採:
        - SHA-1 PassCode + 動態 AES-256 (Bootstrap Key/IV → GP/GK 取單次 Key/IV)
        - TimeStr 10 碼自訂格式
        - Form POST + URL Encoded
    完整實作建議直接參考 references/paynow-payment-api.md 中的演算法章節。
    """

    LEGACY_PROD_URL = 'https://www.paynow.com.tw/service/etopm.aspx'
    LEGACY_TEST_URL = 'https://test.paynow.com.tw/service/etopm.aspx'

    BOOTSTRAP_KEY = 'paynowencryptpaynowcomtw28229955'   # 32 bytes
    BOOTSTRAP_IV = 'encrypt282299550'                    # 16 bytes

    def __init__(self, web_no: str, apicode: str, merchant_password: str,
                 is_production: bool = False) -> None:
        self.web_no = web_no
        self.apicode = apicode
        self.merchant_password = merchant_password
        self.url = self.LEGACY_PROD_URL if is_production else self.LEGACY_TEST_URL

    @staticmethod
    def generate_passcode_request(
        web_no: str, order_no: str, total_price: int, apicode: str
    ) -> str:
        """訂單建立 PassCode = SHA1(WebNo + OrderNo + TotalPrice + apicode)"""
        import hashlib as _hashlib
        raw = f'{web_no}{order_no}{total_price}{apicode}'
        return _hashlib.sha1(raw.encode('utf-8')).hexdigest().upper()

    @staticmethod
    def verify_passcode_response(
        web_no: str,
        order_no: str,
        total_price: int,
        merchant_password: str,
        tran_status: str,
        received: str,
    ) -> bool:
        """付款回傳 PassCode = SHA1(WebNo+OrderNo+TotalPrice+賣場交易密碼+TranStatus)"""
        import hashlib as _hashlib
        raw = f'{web_no}{order_no}{total_price}{merchant_password}{tran_status}'
        expected = _hashlib.sha1(raw.encode('utf-8')).hexdigest().upper()
        return expected == received.upper()

    @staticmethod
    def generate_timestr(now=None) -> str:
        """
        TimeStr = (西元年最後 1 碼) + (一年中第幾天 3 碼 zfill) + HH + MM + SS
        範例: 2019-11-24 00:50:18 -> 9328005018
        """
        from datetime import datetime as _dt
        now = now or _dt.now()
        year_last = str(now.year)[-1]
        day_of_year = str(now.timetuple().tm_yday).zfill(3)
        return (
            f'{year_last}{day_of_year}'
            f'{now.hour:02d}{now.minute:02d}{now.second:02d}'
        )


# ----------------------------------------------------------------------------
# Examples
# ----------------------------------------------------------------------------


def example_create_payment_intent(service: PayNowModernService) -> None:
    print('[範例 1] 建立 PaymentIntent (信用卡 + 分期)')
    print('-' * 60)
    intent = PayNowPaymentIntentData(
        payment_no=f'ORD{int(time.time())}',
        amount=12000,
        currency='TWD',
        description='Premium membership',
        result_url='https://shop.example.com/pay/result',
        webhook_url='https://shop.example.com/pay/webhook',
        allowed_payment_methods=['CreditCard', 'CreditCardInstallment'],
        allow_installments=[3, 6, 12],
    )
    print(f'  paymentNo: {intent.payment_no}')
    print(f'  amount:    {intent.amount}')
    print(f'  methods:   {intent.allowed_payment_methods}')
    print(f'  installments: {intent.allow_installments}')
    print('  -> service.create_payment_intent(intent)')
    print('     回應 result 含 id (PaymentIntent UUID) / paymentNo / checkout_url')
    print()


def example_checkout(service: PayNowModernService) -> None:
    print('[範例 2] PaymentIntent Checkout (信用卡 + PayNow SDK token + 3DS)')
    print('-' * 60)
    checkout = PayNowCheckoutData(
        payment_intent_id='pi_01h8hxxxxxxxxxxxxxxxxx',
        key='pk_live_xxxxxxxx',
        secret='pi_secret_xxxxxxxxxxxxxxxx',
        payment_method_type='CreditCard',
        use_paynow_sdk=True,                       # 由 PayNow Component 蒐集卡號
        otp_flag=True,
        payment_method_data={
            # 卡片資料若 usePayNowSdk=True 由 SDK 回填，這裡示範 billTo
            'billTo': {
                'firstName': 'Hello',
                'lastName': 'World',
                'email': 'buyer@example.com',
            },
        },
        meta={
            'client': {'height': 768, 'width': 1024},
            'iframe': {'height': 600, 'width': 480},
        },
    )
    print(f'  payment_intent_id: {checkout.payment_intent_id}')
    print(f'  paymentMethodType: {checkout.payment_method_type}')
    print(f'  usePayNowSdk: {checkout.use_paynow_sdk}')
    print('  -> service.checkout(checkout)')
    print('     回應 result.auth_code / .last4 (一次扣款成功) 或')
    print('              result.redirect_url (3DS 轉址) 或')
    print('              result.tokenized_card_id (有開啟 tokenize)')
    print()


def example_retrieve_payment_intent(service: PayNowModernService) -> None:
    print('[範例 3] PaymentIntent Retrieve')
    print('-' * 60)
    print('  service.retrieve_payment_intent("pi_01h8hxxxxxxxxxxxxxxxxx")')
    print('  -> 用於確認消費者是否完成 ATM / 超商 / LINE Pay 取號 -> 繳費的轉態')
    print('  -> Webhook 失敗的補單作業也用此 API')
    print()


def example_refund(service: PayNowModernService) -> None:
    print('[範例 4] Refund (信用卡部分退款 + ATM 退款)')
    print('-' * 60)
    cc_refund = PayNowRefundData(
        payment_intent_id='pi_01h8hxxxxxxxxxxxxxxxxx',
        amount=500,
        reason='Customer requested partial refund',
    )
    print('  Credit Card partial refund:')
    print(f'    amount={cc_refund.amount}  reason={cc_refund.reason!r}')
    print()
    atm_refund = PayNowRefundData(
        payment_intent_id='pi_01h8hyyyyyyyyyyyyyyyyy',
        amount=1500,
        reason='Out of stock',
        bank_code='812',
        bank_branch_code='0017',
        bank_account='12345678901234',
    )
    print('  ATM refund (需帶銀行資訊):')
    print(f'    amount={atm_refund.amount}  bank_code={atm_refund.bank_code}')
    print(f'    branch={atm_refund.bank_branch_code}  account={atm_refund.bank_account}')
    print()


def example_apple_pay_session(service: PayNowModernService) -> None:
    print('[範例 5] Apple Pay session (v2 request + v1 confirm)')
    print('-' * 60)
    v2 = PayNowApplePaySessionData(
        merchant_identifier='merchant.com.example.shop',
        display_name='Example Shop',
        initiative='web',
        initiative_context='shop.example.com',
    )
    print('  v2 Request (新整合優先):')
    print(f'    merchant_identifier={v2.merchant_identifier}')
    print(f'    display_name={v2.display_name}')
    print()
    v1 = PayNowApplePayConfirmData(
        merchant_identifier='merchant.com.example.shop',
        validation_url='https://apple-pay-gateway.apple.com/paymentservices/startSession',
        domain_name='shop.example.com',
        display_name='Example Shop',
    )
    print('  v1 Confirm (ApplePaySession.onvalidatemerchant 階段):')
    print(f'    validation_url={v1.validation_url}')
    print()


def example_customer_and_card_token(service: PayNowModernService) -> None:
    print('[範例 6] Customer + Card Token')
    print('-' * 60)
    customer = PayNowCustomerData(
        first_name='Hello',
        last_name='World',
        email='buyer@example.com',
        phone_code='886',
        phone_number='0912345678',
        address=PayNowAddress(
            country='TW',
            locality='Taipei',
            address1='中山區民生東路三段 19 號',
            administrative_area='Taipei City',
            postal_code='10478',
        ),
    )
    print('  create_customer(customer)')
    print(f'    name: {customer.first_name} {customer.last_name}')
    print(f'    address: {customer.address.address1}')
    print()
    print('  retrieve_card_token("cus_01h8hxxxxxxxxxxxxxxxxx")')
    print('  -> result 為 array，每個元素含 id / last4 / brand / expire_month/year')
    print('  -> 將 Card Token id 放到 paymentMethodData 中即可重複扣款')
    print()


def example_legacy_passcode() -> None:
    print('[範例 7] 傳統版 (legacy) PassCode 計算 (僅供既有商家維護)')
    print('-' * 60)
    passcode = PayNowLegacyService.generate_passcode_request(
        web_no='28229955',
        order_no='ORD20260507001',
        total_price=1500,
        apicode='YOUR_API_CODE',
    )
    print(f'  PassCode (送出): {passcode[:40]}...')
    timestr = PayNowLegacyService.generate_timestr()
    print(f'  TimeStr (10 碼自訂格式): {timestr}')
    print('  傳統版完整流程 (GP/GK 取動態 AES Key/IV) 請見 references/paynow-payment-api.md')
    print()


if __name__ == '__main__':
    print('=' * 60)
    print('PayNow 立吉富金流 - Python 範例 (現代版 PaymentIntent)')
    print('=' * 60)
    print()
    print('[注意] PayNow 不公開固定測試金鑰；')
    print('       請至 https://test.paynow.com.tw 註冊取得 API Key (現代版)')
    print('       或賣場交易密碼 (傳統版)。')
    print()
    print('[Caveat] result 欄位名稱 (auth_code / last4 / virtual_account / ...) 為')
    print('         依文件示意推導，正式上線前請以 PayNow 提供之完整回應規格為準。')
    print()

    if not HAS_REQUESTS:
        print('（缺 requests 套件，僅執行不需 HTTP 的範例）')
        print('安裝指令: pip install requests')
        print()
        example_legacy_passcode()
        exit(0)

    # 替換為 PayNow 業務窗口提供之 API Key 與 base URL
    service = PayNowModernService(
        api_key='YOUR_PAYNOW_API_KEY',
        base_url='https://api.paynow.com.tw',     # 上線前向 PayNow 確認
    )

    example_create_payment_intent(service)
    example_checkout(service)
    example_retrieve_payment_intent(service)
    example_refund(service)
    example_apple_pay_session(service)
    example_customer_and_card_token(service)
    example_legacy_passcode()

    print('=' * 60)
    print('範例執行完成')
    print('=' * 60)
