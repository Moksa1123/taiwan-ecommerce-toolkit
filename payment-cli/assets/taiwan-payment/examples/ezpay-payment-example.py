#!/usr/bin/env python3
"""
ezPay 簡單付 Python 完整範例

依照 taiwan-payment-skill 最高規範撰寫
支援: MPG 整合支付 (信用卡、ATM、超商代碼、TWQR、LINE Pay 等)、訂單查詢、退款

API 文件: https://www.ezpay.com.tw/info/Service_intro/api_document/member
參考文件: taiwan-payment/references/ezpay-payment-api.md

ezPay 與 Newebpay 關係:
    ezPay 簡單付 為藍新金流 Newebpay 集團小型商家品牌；
    金流 API 完全相同 (TradeInfo AES-256-CBC + TradeSha SHA256)，
    主要差異為 MerchantID/HashKey 為 ezPay 獨立簽發、部分付款方式受限
    (例如分期付款、特定電子錢包)，且 URL 改用 spgateway / ezpay 域名。

URL 差異:
    Newebpay 沙箱: https://ccore.newebpay.com/MPG/mpg_gateway
    Newebpay 正式: https://core.newebpay.com/MPG/mpg_gateway
    ezPay   沙箱: https://ccore.spgateway.com/MPG/mpg_gateway   (本範例採用)
    ezPay   正式: https://core.spgateway.com/MPG/mpg_gateway

版本差異:
    Newebpay 主推 Version=2.3 (含 GCM 加密選項)
    ezPay 老商家多數仍維持 Version=2.0 (本範例預設 2.0)

依賴:
    pip install pycryptodome requests
"""

import hashlib
import json
import time
import urllib.parse
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Literal, Optional

try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad, unpad
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


# ----------------------------------------------------------------------------
# Dataclasses
# ----------------------------------------------------------------------------


@dataclass
class EzPayMPGOrder:
    """
    ezPay MPG 付款訂單資料 (送進 mpg_gateway 加密前)

    對應 Newebpay TradeInfo 內含欄位；ezPay 強制 Email 必填。
    """
    merchant_order_no: str           # MerchantOrderNo (<=30，唯一)
    amt: int                         # Amt (TWD 整數)
    item_desc: str                   # ItemDesc (<=50)
    email: str                       # Email (ezPay 強制必填)
    return_url: str                  # ReturnURL 付款完成前景轉跳
    notify_url: Optional[str] = None
    client_back_url: Optional[str] = None
    enable_credit: bool = True
    enable_credit_installment: bool = False
    installment_periods: Optional[str] = None        # InstFlag, e.g. "3,6,12"
    enable_unionpay: bool = False
    enable_webatm: bool = False
    enable_vacc: bool = False
    enable_cvs: bool = False
    enable_barcode: bool = False
    enable_linepay: bool = False
    enable_applepay: bool = False
    enable_androidpay: bool = False
    enable_twqr: bool = False
    enable_esunwallet: bool = False
    enable_taiwanpay: bool = False
    login_type: int = 0
    order_comment: Optional[str] = None
    trade_limit: int = 900
    expire_date: Optional[str] = None                # ATM/CVS 繳費期限 Ymd


@dataclass
class EzPayMPGResponse:
    """ezPay MPG 訂單建立回應 (供前端 form POST)"""
    success: bool
    merchant_order_no: str
    form_action: str = ''
    trade_info: str = ''
    trade_sha: str = ''
    merchant_id: str = ''
    version: str = ''
    error_message: str = ''
    raw: Dict[str, str] = field(default_factory=dict)


@dataclass
class EzPayMPGCallback:
    """ezPay MPG NotifyURL / ReturnURL 解密後資料"""
    status: str                                       # SUCCESS / 失敗碼
    message: str
    merchant_order_no: str
    amt: int
    trade_no: str
    merchant_id: str
    payment_type: str
    pay_time: str
    ip: str
    check_code_valid: bool = False                    # CheckCode 是否通過
    code_no: Optional[str] = None
    barcode_1: Optional[str] = None
    barcode_2: Optional[str] = None
    barcode_3: Optional[str] = None
    expire_date: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EzPayQueryResult:
    """訂單查詢結果 (POST /API/QueryTradeInfo)"""
    success: bool
    trade_status: str                                 # 0/1/2/3/6/9
    payment_type: str = ''
    amt: int = 0
    trade_no: str = ''
    merchant_order_no: str = ''
    create_time: str = ''
    pay_time: str = ''
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EzPayRefundResult:
    """信用卡請款 / 退款結果 (POST /API/CreditCard/Close)"""
    success: bool
    status: str                                       # SUCCESS / 失敗碼
    message: str = ''
    raw: Dict[str, Any] = field(default_factory=dict)


# ----------------------------------------------------------------------------
# Service
# ----------------------------------------------------------------------------


class EzPayPaymentService:
    """
    ezPay 簡單付金流服務

    認證方式: AES-256-CBC + SHA256 (與 Newebpay 完全相同)
    加密欄位:
        TradeInfo = AES-256-CBC(query_string(params), key=HashKey, iv=HashIV).hex()
        TradeSha  = SHA256("HashKey={HashKey}&{TradeInfo}&HashIV={HashIV}").upper()
        CheckCode = SHA256("HashIV={IV}&Amt&MerchantID&MerchantOrderNo&TradeNo&HashKey={Key}").upper()
                    (key 順序: Amt -> MerchantID -> MerchantOrderNo -> TradeNo)

    支援付款方式 (依商家方案啟用):
        CREDIT / InstFlag / UNIONPAY / APPLEPAY / ANDROIDPAY / WEBATM / VACC /
        CVS / BARCODE / LINEPAY / ESUNWALLET / TAIWANPAY / TWQR ...

    測試環境:
        商店代號 / HashKey / HashIV 需自行於 ezPay 後台申請；
        ezPay 不公開共用測試 Merchant。
        測試卡號: 4000-2211-1111-1111
    """

    # 沙箱 / 正式環境 (採 spgateway 域名；ezpay.com.tw 域名亦可)
    TEST_API_URL = 'https://ccore.spgateway.com/MPG/mpg_gateway'
    TEST_QUERY_URL = 'https://ccore.spgateway.com/API/QueryTradeInfo'
    TEST_CLOSE_URL = 'https://ccore.spgateway.com/API/CreditCard/Close'
    TEST_EWALLET_REFUND_URL = 'https://ccore.spgateway.com/API/EWallet/refund'

    PROD_API_URL = 'https://core.spgateway.com/MPG/mpg_gateway'
    PROD_QUERY_URL = 'https://core.spgateway.com/API/QueryTradeInfo'
    PROD_CLOSE_URL = 'https://core.spgateway.com/API/CreditCard/Close'
    PROD_EWALLET_REFUND_URL = 'https://core.spgateway.com/API/EWallet/refund'

    # ezPay 慣用版本 (Newebpay 主推 2.3，ezPay 多數老商家仍 2.0)
    DEFAULT_VERSION = '2.0'

    def __init__(
        self,
        merchant_id: str,
        hash_key: str,
        hash_iv: str,
        is_production: bool = False,
        version: Optional[str] = None,
        timeout: int = 30,
    ):
        """
        初始化 ezPay 金流服務

        Args:
            merchant_id:   ezPay 商店代號 (通常以 EZ 系列前綴開頭)
            hash_key:      32 字元 HashKey
            hash_iv:       16 字元 HashIV
            is_production: 是否為正式環境 (預設 False)
            version:       串接版本 (預設 2.0)；可改 2.3 對齊 Newebpay
        """
        if not HAS_CRYPTO:
            raise ImportError('需要安裝 pycryptodome: pip install pycryptodome')

        self.merchant_id = merchant_id
        self.hash_key = hash_key.encode('utf-8')
        self.hash_iv = hash_iv.encode('utf-8')
        self.version = version or self.DEFAULT_VERSION

        if is_production:
            self.api_url = self.PROD_API_URL
            self.query_url = self.PROD_QUERY_URL
            self.close_url = self.PROD_CLOSE_URL
            self.ewallet_refund_url = self.PROD_EWALLET_REFUND_URL
        else:
            self.api_url = self.TEST_API_URL
            self.query_url = self.TEST_QUERY_URL
            self.close_url = self.TEST_CLOSE_URL
            self.ewallet_refund_url = self.TEST_EWALLET_REFUND_URL

        self.timeout = timeout

    # ------------------------------------------------------------------
    # Encryption helpers (與 Newebpay 共用實作)
    # ------------------------------------------------------------------

    def encrypt_trade_info(self, data: Dict[str, Any]) -> str:
        """AES-256-CBC + PKCS#7 padding -> hex 字串"""
        query_string = urllib.parse.urlencode(data)
        cipher = AES.new(self.hash_key, AES.MODE_CBC, self.hash_iv)
        padded = pad(query_string.encode('utf-8'), AES.block_size)
        return cipher.encrypt(padded).hex()

    def decrypt_trade_info(self, encrypted_data: str) -> Dict[str, Any]:
        """AES-256-CBC 解密 -> dict"""
        try:
            encrypted_bytes = bytes.fromhex(encrypted_data)
            cipher = AES.new(self.hash_key, AES.MODE_CBC, self.hash_iv)
            decrypted = unpad(cipher.decrypt(encrypted_bytes), AES.block_size)
            params = urllib.parse.parse_qs(decrypted.decode('utf-8'))
            return {k: v[0] if len(v) == 1 else v for k, v in params.items()}
        except Exception as exc:
            raise ValueError(f'TradeInfo 解密失敗: {exc}')

    def generate_trade_sha(self, trade_info: str) -> str:
        """TradeSha = SHA256("HashKey=...&TradeInfo&HashIV=...").upper()"""
        raw = (
            f'HashKey={self.hash_key.decode("utf-8")}'
            f'&{trade_info}'
            f'&HashIV={self.hash_iv.decode("utf-8")}'
        )
        return hashlib.sha256(raw.encode('utf-8')).hexdigest().upper()

    def verify_trade_sha(self, trade_info: str, trade_sha: str) -> bool:
        return self.generate_trade_sha(trade_info) == trade_sha.upper()

    def generate_check_code(
        self,
        amt: int | str,
        merchant_id: str,
        merchant_order_no: str,
        trade_no: str,
    ) -> str:
        """
        CheckCode (防金額竄改) - 使用「HashIV=...&[排序後 querystring]&HashKey=...」格式

        欄位順序固定為 Amt -> MerchantID -> MerchantOrderNo -> TradeNo (字典序)
        """
        check_params = {
            'Amt': amt,
            'MerchantID': merchant_id,
            'MerchantOrderNo': merchant_order_no,
            'TradeNo': trade_no,
        }
        ordered = {k: check_params[k] for k in sorted(check_params)}
        param_str = urllib.parse.urlencode(ordered)
        raw = (
            f'HashIV={self.hash_iv.decode("utf-8")}'
            f'&{param_str}'
            f'&HashKey={self.hash_key.decode("utf-8")}'
        )
        return hashlib.sha256(raw.encode('utf-8')).hexdigest().upper()

    # ------------------------------------------------------------------
    # MPG order
    # ------------------------------------------------------------------

    def create_order(self, data: EzPayMPGOrder) -> EzPayMPGResponse:
        """
        建立 ezPay MPG 整合支付訂單

        Returns:
            EzPayMPGResponse: 含 trade_info / trade_sha，前端以 form POST 至 form_action
        """
        if data.amt < 1:
            raise ValueError('金額必須大於 0')
        if len(data.merchant_order_no) > 30:
            raise ValueError('訂單編號不可超過 30 字元')
        if not data.email:
            raise ValueError('ezPay 強制需要 Email 欄位')

        params: Dict[str, Any] = {
            'MerchantID': self.merchant_id,
            'RespondType': 'JSON',
            'TimeStamp': str(int(datetime.now().timestamp())),
            'Version': self.version,
            'MerchantOrderNo': data.merchant_order_no,
            'Amt': data.amt,
            'ItemDesc': data.item_desc,
            'Email': data.email,
            'ReturnURL': data.return_url,
            'LoginType': data.login_type,
            'TradeLimit': data.trade_limit,
        }

        # 支付方式啟用旗標 (與 Newebpay 共用，但 ezPay 多數方案不支援分期)
        if data.enable_credit:
            params['CREDIT'] = 1
        if data.enable_credit_installment:
            # ezPay 多數方案不支援；需先在後台啟用
            params['InstFlag'] = data.installment_periods or '3,6,12'
        if data.enable_unionpay:
            params['UNIONPAY'] = 1
        if data.enable_webatm:
            params['WEBATM'] = 1
        if data.enable_vacc:
            params['VACC'] = 1
        if data.enable_cvs:
            params['CVS'] = 1
        if data.enable_barcode:
            params['BARCODE'] = 1
        if data.enable_linepay:
            params['LINEPAY'] = 1
        if data.enable_applepay:
            params['APPLEPAY'] = 1
        if data.enable_androidpay:
            params['ANDROIDPAY'] = 1
        if data.enable_twqr:
            params['TWQR'] = 1                  # ezPay 主打方式之一
        if data.enable_esunwallet:
            params['ESUNWALLET'] = 1
        if data.enable_taiwanpay:
            params['TAIWANPAY'] = 1

        if data.notify_url:
            params['NotifyURL'] = data.notify_url
        if data.client_back_url:
            params['ClientBackURL'] = data.client_back_url
        if data.order_comment:
            params['OrderComment'] = data.order_comment
        if data.expire_date:
            params['ExpireDate'] = data.expire_date

        trade_info = self.encrypt_trade_info(params)
        trade_sha = self.generate_trade_sha(trade_info)

        return EzPayMPGResponse(
            success=True,
            merchant_order_no=data.merchant_order_no,
            form_action=self.api_url,
            trade_info=trade_info,
            trade_sha=trade_sha,
            merchant_id=self.merchant_id,
            version=self.version,
            raw={
                'MerchantID': self.merchant_id,
                'TradeInfo': trade_info,
                'TradeSha': trade_sha,
                'Version': self.version,
            },
        )

    def verify_notification(self, callback_data: Dict[str, str]) -> EzPayMPGCallback:
        """
        驗證並解析 ezPay NotifyURL / ReturnURL POST 進來的資料

        步驟:
            1. 比對 TradeSha
            2. AES 解密 TradeInfo -> { Status, Message, Result }
            3. Result 為 JSON 字串，解析後再驗 CheckCode (防金額竄改)
        """
        trade_info = callback_data.get('TradeInfo', '')
        trade_sha = callback_data.get('TradeSha', '')

        if not self.verify_trade_sha(trade_info, trade_sha):
            raise ValueError('TradeSha 驗證失敗')

        decrypted = self.decrypt_trade_info(trade_info)
        result_field = decrypted.get('Result', '{}')
        try:
            result = json.loads(result_field) if isinstance(result_field, str) else result_field
        except json.JSONDecodeError:
            result = {}

        # 驗 CheckCode (僅成功訂單才會帶)
        check_code_valid = False
        received_check_code = result.get('CheckCode', '')
        if received_check_code and result.get('TradeNo'):
            expected = self.generate_check_code(
                amt=result.get('Amt', 0),
                merchant_id=result.get('MerchantID', ''),
                merchant_order_no=result.get('MerchantOrderNo', ''),
                trade_no=result.get('TradeNo', ''),
            )
            check_code_valid = expected == received_check_code.upper()

        return EzPayMPGCallback(
            status=decrypted.get('Status', ''),
            message=decrypted.get('Message', ''),
            merchant_order_no=result.get('MerchantOrderNo', ''),
            amt=int(result.get('Amt', 0)),
            trade_no=result.get('TradeNo', ''),
            merchant_id=result.get('MerchantID', ''),
            payment_type=result.get('PaymentType', ''),
            pay_time=result.get('PayTime', ''),
            ip=result.get('IP', ''),
            check_code_valid=check_code_valid,
            code_no=result.get('CodeNo'),
            barcode_1=result.get('Barcode_1'),
            barcode_2=result.get('Barcode_2'),
            barcode_3=result.get('Barcode_3'),
            expire_date=result.get('ExpireDate'),
            raw=decrypted,
        )

    # ------------------------------------------------------------------
    # Order query  POST /API/QueryTradeInfo
    # ------------------------------------------------------------------

    def query_order(self, merchant_order_no: str, amt: int) -> EzPayQueryResult:
        """
        訂單查詢 (走 CheckValue 而非 TradeInfo)

        CheckValue = SHA256("IV=xxx&Amt=...&MerchantID=...&MerchantOrderNo=...&Key=xxx").upper()
        """
        if not HAS_REQUESTS:
            raise ImportError('需要安裝 requests: pip install requests')

        param_str = (
            f'Amt={amt}&MerchantID={self.merchant_id}'
            f'&MerchantOrderNo={merchant_order_no}'
        )
        raw = (
            f'IV={self.hash_iv.decode("utf-8")}'
            f'&{param_str}'
            f'&Key={self.hash_key.decode("utf-8")}'
        )
        check_value = hashlib.sha256(raw.encode('utf-8')).hexdigest().upper()

        body = {
            'MerchantID': self.merchant_id,
            'Version': '1.3',
            'RespondType': 'JSON',
            'CheckValue': check_value,
            'TimeStamp': str(int(datetime.now().timestamp())),
            'MerchantOrderNo': merchant_order_no,
            'Amt': amt,
        }

        resp = requests.post(self.query_url, data=body, timeout=self.timeout)
        resp.raise_for_status()
        try:
            data = resp.json()
        except ValueError:
            data = {'raw': resp.text}

        result = data.get('Result', {}) if isinstance(data.get('Result'), dict) else {}
        return EzPayQueryResult(
            success=(data.get('Status') == 'SUCCESS'),
            trade_status=str(result.get('TradeStatus', '')),
            payment_type=result.get('PaymentType', ''),
            amt=int(result.get('Amt', 0)),
            trade_no=result.get('TradeNo', ''),
            merchant_order_no=result.get('MerchantOrderNo', ''),
            create_time=result.get('CreateTime', ''),
            pay_time=result.get('PayTime', ''),
            raw=data,
        )

    # ------------------------------------------------------------------
    # Credit card refund / capture  POST /API/CreditCard/Close
    # ------------------------------------------------------------------

    def refund_credit(
        self,
        merchant_order_no: str,
        trade_no: str,
        amt: int,
        close_type: Literal[1, 2] = 2,            # 1 請款 / 2 退款
        cancel: bool = False,                     # True -> 取消請款 / 取消退款
        index_type: Literal[1, 2] = 1,            # 1 訂單編號 / 2 交易序號
    ) -> EzPayRefundResult:
        """
        信用卡請款 / 退款 / 取消

        ezPay 特別注意:
            - 分期付款在 ezPay 通常受限，許多方案不支援
            - 一次付清 / 銀聯卡 支援部分退款
        """
        if not HAS_REQUESTS:
            raise ImportError('需要安裝 requests: pip install requests')

        post_data: Dict[str, Any] = {
            'RespondType': 'JSON',
            'Version': '1.1',
            'Amt': amt,
            'MerchantOrderNo': merchant_order_no,
            'TimeStamp': str(int(datetime.now().timestamp())),
            'IndexType': index_type,
            'TradeNo': trade_no,
            'CloseType': close_type,
        }
        if cancel:
            post_data['Cancel'] = 1

        # PostData_ = AES 加密後 hex
        post_data_encrypted = self.encrypt_trade_info(post_data)

        body = {
            'MerchantID_': self.merchant_id,
            'PostData_': post_data_encrypted,
        }
        resp = requests.post(self.close_url, data=body, timeout=self.timeout)
        resp.raise_for_status()
        try:
            data = resp.json()
        except ValueError:
            data = {'raw': resp.text}

        return EzPayRefundResult(
            success=(data.get('Status') == 'SUCCESS'),
            status=data.get('Status', ''),
            message=data.get('Message', ''),
            raw=data,
        )


# ----------------------------------------------------------------------------
# Examples
# ----------------------------------------------------------------------------


def example_create_order(service: EzPayPaymentService) -> None:
    print('[範例 1] 建立 ezPay MPG 整合支付訂單')
    print('-' * 60)

    order_data = EzPayMPGOrder(
        merchant_order_no=f'EZ{int(time.time())}',
        amt=1500,
        item_desc='ezPay 測試商品 * 1',
        email='buyer@example.com',
        return_url='https://shop.example.com/api/ezpay/return',
        notify_url='https://shop.example.com/api/ezpay/notify',
        client_back_url='https://shop.example.com/cart',
        enable_credit=True,
        enable_vacc=True,
        enable_cvs=True,
        enable_twqr=True,                  # ezPay 主打 TWQR
    )

    try:
        result = service.create_order(order_data)
        if result.success:
            print(f'  訂單編號: {result.merchant_order_no}')
            print(f'  Form Action: {result.form_action}')
            print(f'  Version: {result.version}')
            print(f'  TradeInfo: {result.trade_info[:60]}...')
            print(f'  TradeSha:  {result.trade_sha[:32]}...')
            print()
            print('  將以下欄位 form POST 至 form_action:')
            for key in ('MerchantID', 'TradeInfo', 'TradeSha', 'Version'):
                value = result.raw.get(key, '')
                preview = value if len(str(value)) < 40 else f'{str(value)[:40]}...'
                print(f'    {key}: {preview}')
    except Exception as exc:
        print(f'  ✗ 例外: {exc}')
    print()


def example_verify_notification(service: EzPayPaymentService) -> None:
    print('[範例 2] 驗證 NotifyURL 通知 (TradeSha + CheckCode)')
    print('-' * 60)

    # 模擬一筆 ezPay 成功通知 (信用卡)
    result_dict = {
        'Status': 'SUCCESS',
        'Message': '授權成功',
        'MerchantID': service.merchant_id,
        'Amt': 1500,
        'TradeNo': '24050714300012345678',
        'MerchantOrderNo': 'EZ1715000000',
        'PaymentType': 'CREDIT',
        'PayTime': '2026-05-07 14:30:00',
        'IP': '203.0.113.7',
        'EscrowBank': 'KGI',
    }
    # CheckCode 用 service 的 generate_check_code 算出再放回去
    result_dict['CheckCode'] = service.generate_check_code(
        amt=result_dict['Amt'],
        merchant_id=result_dict['MerchantID'],
        merchant_order_no=result_dict['MerchantOrderNo'],
        trade_no=result_dict['TradeNo'],
    )

    plaintext = {
        'Status': 'SUCCESS',
        'Message': '授權成功',
        'Result': json.dumps(result_dict, ensure_ascii=False),
    }
    trade_info = service.encrypt_trade_info(plaintext)
    trade_sha = service.generate_trade_sha(trade_info)

    try:
        callback = service.verify_notification(
            {'TradeInfo': trade_info, 'TradeSha': trade_sha}
        )
        print(f'  Status:       {callback.status}')
        print(f'  TradeNo:      {callback.trade_no}')
        print(f'  MerchantOrder: {callback.merchant_order_no}')
        print(f'  Amt:          {callback.amt}')
        print(f'  PaymentType:  {callback.payment_type}')
        print(f'  CheckCode 通過: {callback.check_code_valid}')
    except ValueError as exc:
        print(f'  ✗ 驗證失敗: {exc}')
    print()


def example_query_order(service: EzPayPaymentService) -> None:
    print('[範例 3] 訂單查詢 POST /API/QueryTradeInfo')
    print('-' * 60)
    print('  service.query_order(merchant_order_no="EZ1715000000", amt=1500)')
    print('  -> 回傳 trade_status: 0 未付款 / 1 成功 / 2 失敗 / 3 取消 / 6 退款 / 9 付款中')
    print('  （示範僅展示 API 呼叫；正式呼叫需要實際 sandbox 帳號）')
    print()


def example_refund_credit(service: EzPayPaymentService) -> None:
    print('[範例 4] 信用卡退款 POST /API/CreditCard/Close')
    print('-' * 60)
    print('  service.refund_credit(')
    print('      merchant_order_no="EZ1715000000",')
    print('      trade_no="24050714300012345678",')
    print('      amt=1500,')
    print('      close_type=2,    # 1 請款 / 2 退款')
    print('      cancel=False,    # True 則為取消請款/取消退款')
    print('  )')
    print('  注意:')
    print('    - 分期付款在 ezPay 多數方案不支援，需後台另行啟用')
    print('    - 一次付清 / 銀聯卡 支援整筆 / 部分退款')
    print()


if __name__ == '__main__':
    print('=' * 60)
    print('ezPay 簡單付金流 - Python 範例')
    print('=' * 60)
    print()

    if not HAS_CRYPTO:
        print('✗ 缺少 pycryptodome，請執行: pip install pycryptodome')
        exit(1)

    print('[注意] ezPay 不公開共用測試 Merchant，請先至 ezPay 後台申請測試帳號')
    print('       將以下 MerchantID / HashKey / HashIV 替換為您的測試環境參數')
    print()

    # ⚠ 測試 / Demo 用：請替換為實際 ezPay 後台核發之 sandbox 參數
    service = EzPayPaymentService(
        merchant_id='YOUR_EZPAY_MERCHANT_ID',          # ezPay 商店代號 (通常 EZ 開頭)
        hash_key='YOUR_EZPAY_HASH_KEY_32_CHARACTERS_',  # 32 字元
        hash_iv='YOUR_EZPAY_HIV_',                     # 16 字元
        is_production=False,
        version='2.0',                                  # ezPay 慣用版本
    )

    example_create_order(service)
    example_verify_notification(service)
    example_query_order(service)
    example_refund_credit(service)

    print('=' * 60)
    print('範例執行完成')
    print('=' * 60)
