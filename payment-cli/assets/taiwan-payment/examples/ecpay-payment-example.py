#!/usr/bin/env python3
"""
ECPay 綠界金流 Python 完整範例

依照 taiwan-payment-skill 最高規範撰寫
支援: 信用卡、ATM 轉帳、超商代碼、超商條碼

API 文件: https://developers.ecpay.com.tw
"""

import hashlib
import hmac
import urllib.parse
import time
from datetime import datetime
from typing import Dict, Literal, Optional, List
from dataclasses import dataclass, field



def ecpay_url_encode(text: str) -> str:
    """
    綠界 CheckMacValue 專用的 URL encode（對應官方 SDK UrlService::ecpayUrlEncode）

    PHP urlencode → 轉小寫 → 把 %2d %5f %2e %21 %2a %28 %29 還原成 - _ . ! * ( )
    （.NET 的 UrlEncode 不編碼這幾個字元，綠界以 .NET 規則驗證）。

    直接用 Python 的 quote_plus 會有兩處不同：
    - quote_plus 會把 ! * ( ) 編碼，綠界不會 → 商品名稱含括號就驗證失敗
    - quote_plus 保留 ~，PHP 會編成 %7e
    """
    encoded = urllib.parse.quote_plus(text, safe='').replace('~', '%7E').lower()
    for src, dst in (('%2d', '-'), ('%5f', '_'), ('%2e', '.'), ('%21', '!'),
                     ('%2a', '*'), ('%28', '('), ('%29', ')')):
        encoded = encoded.replace(src, dst)
    return encoded

@dataclass
class PaymentOrderData:
    """ECPay 付款訂單資料"""
    merchant_trade_no: str
    total_amount: int
    trade_desc: str
    item_name: str
    return_url: str
    choose_payment: Literal['Credit', 'ATM', 'CVS', 'BARCODE', 'ALL']
    merchant_trade_date: Optional[str] = None
    client_back_url: Optional[str] = None
    item_url: Optional[str] = None
    remark: Optional[str] = None
    choose_sub_payment: Optional[str] = None
    order_result_url: Optional[str] = None
    need_extra_paid_info: str = 'N'
    device_source: Optional[str] = None
    ignore_payment: Optional[str] = None
    platform_id: Optional[str] = None
    invoice_mark: str = 'N'
    encrypt_type: int = 1


@dataclass
class PaymentOrderResponse:
    """ECPay 付款訂單回應"""
    success: bool
    merchant_trade_no: str
    form_action: str = ''
    form_data: Dict[str, str] = field(default_factory=dict)
    error_message: str = ''
    raw: Dict[str, str] = field(default_factory=dict)


@dataclass
class PaymentCallbackData:
    """ECPay 付款回傳資料"""
    merchant_trade_no: str
    rtn_code: int
    rtn_msg: str
    trade_no: str
    trade_amt: int
    payment_date: str
    payment_type: str
    payment_type_charge_fee: str
    trade_date: str
    simulate_paid: int
    check_mac_value: str
    raw: Dict[str, str] = field(default_factory=dict)


class ECPayPaymentService:
    """
    ECPay 綠界金流服務

    認證方式: SHA256 CheckMacValue
    加密方式: URL-encoded + SHA256

    支援付款方式:
    - Credit: 信用卡 (一次付清/分期/定期定額)
    - ATM: ATM 轉帳
    - CVS: 超商代碼繳費
    - BARCODE: 超商條碼繳費
    - ALL: 不指定付款方式

    測試環境:
    - 商店代號: 3002607
    - HashKey: pwFHCqoQZGmho4w6
    - HashIV: EkRm7iFT261dpevs
    - 測試卡號: 4311-9522-2222-2222
    """

    # 測試環境
    TEST_MERCHANT_ID = '3002607'
    TEST_HASH_KEY = 'pwFHCqoQZGmho4w6'
    TEST_HASH_IV = 'EkRm7iFT261dpevs'
    TEST_API_URL = 'https://payment-stage.ecpay.com.tw/Cashier/AioCheckOut/V5'
    TEST_QUERY_URL = 'https://payment-stage.ecpay.com.tw/Cashier/QueryTradeInfo/V5'

    # 正式環境
    PROD_API_URL = 'https://payment.ecpay.com.tw/Cashier/AioCheckOut/V5'
    PROD_QUERY_URL = 'https://payment.ecpay.com.tw/Cashier/QueryTradeInfo/V5'

    def __init__(
        self,
        merchant_id: str,
        hash_key: str,
        hash_iv: str,
        is_production: bool = False
    ):
        """
        初始化 ECPay 金流服務

        Args:
            merchant_id: 商店代號
            hash_key: HashKey
            hash_iv: HashIV
            is_production: 是否為正式環境 (預設 False)
        """
        self.merchant_id = merchant_id
        self.hash_key = hash_key
        self.hash_iv = hash_iv
        self.api_url = self.PROD_API_URL if is_production else self.TEST_API_URL
        self.query_url = self.PROD_QUERY_URL if is_production else self.TEST_QUERY_URL

    def generate_check_mac_value(self, params: Dict[str, any]) -> str:
        """
        產生 CheckMacValue (SHA256)

        Args:
            params: API 參數字典

        Returns:
            str: SHA256 雜湊值 (大寫)

        Example:
            >>> params = {'MerchantID': '3002607', 'TotalAmount': 100}
            >>> mac = service.generate_check_mac_value(params)
            >>> len(mac)
            64
        """
        # 步驟 1: 排除 CheckMacValue，依參數名稱「不分大小寫」排序
        #   官方 SDK 用 strcasecmp；Python 預設 sorted 區分大小寫，遇到 CVS* / Custom* 這類
        #   大小寫交錯的欄位名稱順序就會不同
        sorted_params = sorted(
            ((k, v) for k, v in params.items() if k != 'CheckMacValue'),
            key=lambda kv: kv[0].lower(),
        )

        # 步驟 2: 組合查詢字串
        param_str = '&'.join(f'{k}={v}' for k, v in sorted_params)

        # 步驟 3: 加入 HashKey 和 HashIV
        raw = f'HashKey={self.hash_key}&{param_str}&HashIV={self.hash_iv}'

        # 步驟 4: 綠界規則的 URL Encode（含轉小寫與 .NET 字元還原）
        encoded = ecpay_url_encode(raw)

        # 步驟 5: SHA256 雜湊並轉大寫
        return hashlib.sha256(encoded.encode('utf-8')).hexdigest().upper()

    def verify_check_mac_value(self, params: Dict[str, any]) -> bool:
        """
        驗證 CheckMacValue

        Args:
            params: 包含 CheckMacValue 的參數字典

        Returns:
            bool: 驗證是否通過
        """
        # 不修改呼叫端傳入的 dict（原本用 pop 會把 CheckMacValue 從請求資料中刪掉）
        received_mac = params.get('CheckMacValue', '')
        if not received_mac:
            return False

        calculated_mac = self.generate_check_mac_value(params)
        # 常數時間比較，避免以回應時間差逐字元猜出正確雜湊
        return hmac.compare_digest(calculated_mac, received_mac.upper())

    def create_order(
        self,
        data: PaymentOrderData,
    ) -> PaymentOrderResponse:
        """
        建立付款訂單

        Args:
            data: 付款訂單資料 (PaymentOrderData)

        Returns:
            PaymentOrderResponse: 付款訂單回應 (包含表單 HTML)

        Raises:
            ValueError: 參數驗證失敗

        Example:
            >>> order_data = PaymentOrderData(
            ...     merchant_trade_no=f'ORD{int(time.time())}',
            ...     total_amount=1050,
            ...     trade_desc='測試訂單',
            ...     item_name='測試商品 x 1',
            ...     return_url='https://your-site.com/callback',
            ...     choose_payment='Credit',
            ... )
            >>> result = service.create_order(order_data)
            >>> print(result.form_action)
        """
        # 參數驗證
        if data.total_amount < 1:
            raise ValueError('金額必須大於 0')
        if len(data.merchant_trade_no) > 20:
            raise ValueError('訂單編號不可超過 20 字元')

        # 產生交易日期時間 (格式: YYYY/MM/DD HH:MM:SS)
        if not data.merchant_trade_date:
            data.merchant_trade_date = datetime.now().strftime('%Y/%m/%d %H:%M:%S')

        # 準備 API 參數
        api_params = {
            'MerchantID': self.merchant_id,
            'MerchantTradeNo': data.merchant_trade_no,
            'MerchantTradeDate': data.merchant_trade_date,
            'PaymentType': 'aio',
            'TotalAmount': data.total_amount,
            'TradeDesc': data.trade_desc,
            'ItemName': data.item_name,
            'ReturnURL': data.return_url,
            'ChoosePayment': data.choose_payment,
            'EncryptType': data.encrypt_type,
        }

        # 加入可選參數
        if data.client_back_url:
            api_params['ClientBackURL'] = data.client_back_url
        if data.item_url:
            api_params['ItemURL'] = data.item_url
        if data.remark:
            api_params['Remark'] = data.remark
        if data.choose_sub_payment:
            api_params['ChooseSubPayment'] = data.choose_sub_payment
        if data.order_result_url:
            api_params['OrderResultURL'] = data.order_result_url
        if data.need_extra_paid_info:
            api_params['NeedExtraPaidInfo'] = data.need_extra_paid_info
        if data.device_source:
            api_params['DeviceSource'] = data.device_source
        if data.ignore_payment:
            api_params['IgnorePayment'] = data.ignore_payment
        if data.platform_id:
            api_params['PlatformID'] = data.platform_id
        if data.invoice_mark:
            api_params['InvoiceMark'] = data.invoice_mark

        # 產生 CheckMacValue
        api_params['CheckMacValue'] = self.generate_check_mac_value(api_params)

        # 回傳表單資料
        return PaymentOrderResponse(
            success=True,
            merchant_trade_no=data.merchant_trade_no,
            form_action=self.api_url,
            form_data=api_params,
            raw=api_params,
        )

    def parse_callback(self, callback_data: Dict[str, str]) -> PaymentCallbackData:
        """
        解析付款回傳資料

        Args:
            callback_data: POST 回傳的參數字典

        Returns:
            PaymentCallbackData: 解析後的回傳資料

        Raises:
            ValueError: CheckMacValue 驗證失敗

        Example:
            >>> callback = request.form.to_dict()
            >>> result = service.parse_callback(callback)
            >>> if result.rtn_code == 1:
            ...     print(f"付款成功: {result.trade_no}")
        """
        # 驗證 CheckMacValue
        verify_data = callback_data.copy()
        if not self.verify_check_mac_value(verify_data):
            raise ValueError('CheckMacValue 驗證失敗')

        # 解析回傳資料
        return PaymentCallbackData(
            merchant_trade_no=callback_data.get('MerchantTradeNo', ''),
            rtn_code=int(callback_data.get('RtnCode', 0)),
            rtn_msg=callback_data.get('RtnMsg', ''),
            trade_no=callback_data.get('TradeNo', ''),
            trade_amt=int(callback_data.get('TradeAmt', 0)),
            payment_date=callback_data.get('PaymentDate', ''),
            payment_type=callback_data.get('PaymentType', ''),
            payment_type_charge_fee=callback_data.get('PaymentTypeChargeFee', '0'),
            trade_date=callback_data.get('TradeDate', ''),
            simulate_paid=int(callback_data.get('SimulatePaid', 0)),
            check_mac_value=callback_data.get('CheckMacValue', ''),
            raw=callback_data,
        )


# Usage Example
if __name__ == '__main__':
    # 初始化金流服務 (使用測試環境)
    service = ECPayPaymentService(
        merchant_id=ECPayPaymentService.TEST_MERCHANT_ID,
        hash_key=ECPayPaymentService.TEST_HASH_KEY,
        hash_iv=ECPayPaymentService.TEST_HASH_IV,
        is_production=False,
    )

    print('=' * 60)
    print('ECPay 綠界金流 - Python 範例')
    print('=' * 60)
    print()

    # 範例 1: 建立信用卡付款訂單
    print('[範例 1] 建立信用卡付款訂單')
    print('-' * 60)

    order_data = PaymentOrderData(
        merchant_trade_no=f'ORD{int(time.time())}',  # 訂單編號 (唯一值)
        total_amount=1050,  # 金額 (新台幣)
        trade_desc='測試商品購買',  # 交易描述
        item_name='測試商品 x 1',  # 商品名稱
        return_url='https://your-site.com/api/payment/callback',  # 付款結果通知網址
        choose_payment='Credit',  # 付款方式: 信用卡
        client_back_url='https://your-site.com/order/complete',  # 付款完成返回網址
    )

    try:
        result = service.create_order(order_data)

        if result.success:
            print(f'✓ 訂單建立成功')
            print(f'  訂單編號: {result.merchant_trade_no}')
            print(f'  表單網址: {result.form_action}')
            print(f'  CheckMacValue: {result.form_data["CheckMacValue"][:32]}...')
            print()
            print('請將以下表單資料 POST 到表單網址:')
            for key, value in list(result.form_data.items())[:5]:
                print(f'  {key}: {value}')
            print(f'  ... (共 {len(result.form_data)} 個參數)')
        else:
            print(f'✗ 訂單建立失敗: {result.error_message}')
    except Exception as e:
        print(f'✗ 發生例外: {str(e)}')

    print()
    print('-' * 60)

    # 範例 2: 驗證付款回傳
    print('[範例 2] 驗證付款回傳資料')
    print('-' * 60)

    # 模擬 ECPay 回傳資料
    mock_callback = {
        'MerchantID': service.merchant_id,
        'MerchantTradeNo': 'ORD1738123456',
        'RtnCode': '1',
        'RtnMsg': '交易成功',
        'TradeNo': '2401291234567890',
        'TradeAmt': '1050',
        'PaymentDate': '2024/01/29 14:30:00',
        'PaymentType': 'Credit_CreditCard',
        'PaymentTypeChargeFee': '30',
        'TradeDate': '2024/01/29 14:25:00',
        'SimulatePaid': '0',
    }

    # 計算正確的 CheckMacValue
    mock_callback['CheckMacValue'] = service.generate_check_mac_value(mock_callback)

    try:
        callback_result = service.parse_callback(mock_callback)

        if callback_result.rtn_code == 1:
            print(f'✓ 付款成功')
            print(f'  訂單編號: {callback_result.merchant_trade_no}')
            print(f'  ECPay 交易編號: {callback_result.trade_no}')
            print(f'  付款金額: {callback_result.trade_amt} 元')
            print(f'  付款時間: {callback_result.payment_date}')
            print(f'  付款方式: {callback_result.payment_type}')
            print(f'  手續費: {callback_result.payment_type_charge_fee} 元')
        else:
            print(f'✗ 付款失敗: {callback_result.rtn_msg}')
    except ValueError as e:
        print(f'✗ 驗證失敗: {str(e)}')

    print()
    print('=' * 60)
    print('範例執行完成')
    print('=' * 60)
