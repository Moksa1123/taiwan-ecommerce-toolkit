#!/usr/bin/env python3
"""
ECPay 綠界電子發票 Python 完整範例

依照 taiwan-invoice-skill 最高規範撰寫
支援: B2C 二聯式、B2B 三聯式、發票作廢、折讓、列印

API 文件: https://developers.ecpay.com.tw
"""

import hashlib
import json
import urllib.parse
import base64
import time
import requests
from datetime import datetime
from typing import Dict, Literal, Optional, List
from dataclasses import dataclass, field
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


@dataclass
class InvoiceIssueData:
    """ECPay 發票開立資料"""
    merchant_id: str
    relate_number: str  # 訂單編號 (唯一)
    customer_identifier: str  # 買受人統編 (B2C: 0000000000, B2B: 8碼統編)
    customer_name: str  # 買受人名稱
    customer_addr: str  # 買受人地址
    customer_phone: str  # 買受人電話
    customer_email: str  # 買受人 Email
    sales_amount: int  # 銷售額 (B2C: 含稅, B2B: 未稅)
    tax_type: Literal['1', '2', '3', '9'] = '1'  # 1=應稅, 2=零稅率, 3=免稅, 9=混合
    tax_rate: int = 5  # 稅率 (預設5%)
    tax_amount: int = 0  # 稅額 (B2B 必填)
    total_amount: int = 0  # 總計 (含稅)
    carrier_type: Optional[Literal['', '1', '2', '3']] = ''  # 載具類型 (B2B不可使用)
    carrier_num: Optional[str] = ''  # 載具號碼
    donation: Literal['0', '1'] = '0'  # 是否捐贈
    love_code: Optional[str] = ''  # 捐贈碼
    print: Literal['0', '1'] = '0'  # 是否列印
    items: List[Dict[str, any]] = field(default_factory=list)
    inv_type: Literal['07', '08'] = '07'  # 07=一般稅額, 08=特種稅額
    vat: Literal['1', '2', '3', '4'] = '1'  # 1=課稅, 2=零稅率, 3=免稅, 4=應稅(特種)
    remark: Optional[str] = ''


@dataclass
class InvoiceVoidData:
    """ECPay 發票作廢資料"""
    merchant_id: str
    invoice_no: str  # 發票號碼
    invoice_date: str  # 發票開立日期 (YYYY-MM-DD)
    reason: str  # 作廢原因


@dataclass
class InvoiceAllowanceData:
    """ECPay 發票折讓資料"""
    merchant_id: str
    invoice_no: str  # 發票號碼
    invoice_date: str  # 發票開立日期 (YYYY-MM-DD)
    allowance_notify: Literal['E', 'S', 'N', 'A'] = 'E'  # E=Email, S=簡訊, N=不通知, A=Email+簡訊
    customer_name: str
    notify_mail: Optional[str] = ''
    notify_phone: Optional[str] = ''
    allowance_amount: int = 0  # 折讓金額
    items: List[Dict[str, any]] = field(default_factory=list)


@dataclass
class InvoiceIssueResponse:
    """ECPay 發票開立回應"""
    success: bool
    invoice_number: str = ''
    invoice_date: str = ''
    random_number: str = ''
    rtn_code: int = 0
    rtn_msg: str = ''
    error_message: str = ''
    raw: Dict[str, any] = field(default_factory=dict)


class ECPayInvoiceService:
    """
    ECPay 綠界電子發票服務

    認證方式: AES-128-CBC 加密
    加密金鑰: HashKey (16 bytes), HashIV (16 bytes)

    支援功能:
    - 開立發票 (B2C 二聯式 / B2B 三聯式)
    - 作廢發票
    - 折讓發票
    - 列印發票
    - 查詢發票

    測試環境:
    - 商店代號: 2000132
    - HashKey: ejCk326UnaZWKisg
    - HashIV: q9jcZX8Ib9LM8wYk
    - 測試 URL: https://einvoice-stage.ecpay.com.tw

    B2C vs B2B 差異:
    - B2C: CustomerIdentifier = 0000000000, 金額為含稅價, 可用載具/捐贈
    - B2B: CustomerIdentifier = 8碼統編, 金額為未稅價, 需計算稅額, 不可用載具/捐贈
    """

    # 測試環境
    TEST_MERCHANT_ID = '2000132'
    TEST_HASH_KEY = 'ejCk326UnaZWKisg'
    TEST_HASH_IV = 'q9jcZX8Ib9LM8wYk'
    TEST_API_URL = 'https://einvoice-stage.ecpay.com.tw/B2CInvoice/Issue'
    TEST_VOID_URL = 'https://einvoice-stage.ecpay.com.tw/B2CInvoice/Invalid'
    TEST_ALLOWANCE_URL = 'https://einvoice-stage.ecpay.com.tw/B2CInvoice/Allowance'
    TEST_ALLOWANCE_VOID_URL = 'https://einvoice-stage.ecpay.com.tw/B2CInvoice/AllowanceInvalid'
    TEST_QUERY_URL = 'https://einvoice-stage.ecpay.com.tw/B2CInvoice/GetIssue'

    # 正式環境
    PROD_API_URL = 'https://einvoice.ecpay.com.tw/B2CInvoice/Issue'
    PROD_VOID_URL = 'https://einvoice.ecpay.com.tw/B2CInvoice/Invalid'
    PROD_ALLOWANCE_URL = 'https://einvoice.ecpay.com.tw/B2CInvoice/Allowance'
    PROD_ALLOWANCE_VOID_URL = 'https://einvoice.ecpay.com.tw/B2CInvoice/AllowanceInvalid'
    PROD_QUERY_URL = 'https://einvoice.ecpay.com.tw/B2CInvoice/GetIssue'

    def __init__(self, merchant_id: str, hash_key: str, hash_iv: str, is_test: bool = True):
        """
        初始化 ECPay 電子發票服務

        Args:
            merchant_id: 商店代號
            hash_key: HashKey (16 bytes)
            hash_iv: HashIV (16 bytes)
            is_test: 是否為測試環境
        """
        self.merchant_id = merchant_id
        self.hash_key = hash_key.encode('utf-8')
        self.hash_iv = hash_iv.encode('utf-8')
        self.is_test = is_test

        # 設定 API URL
        if is_test:
            self.api_url = self.TEST_API_URL
            self.void_url = self.TEST_VOID_URL
            self.allowance_url = self.TEST_ALLOWANCE_URL
            self.allowance_void_url = self.TEST_ALLOWANCE_VOID_URL
            self.query_url = self.TEST_QUERY_URL
        else:
            self.api_url = self.PROD_API_URL
            self.void_url = self.PROD_VOID_URL
            self.allowance_url = self.PROD_ALLOWANCE_URL
            self.allowance_void_url = self.PROD_ALLOWANCE_VOID_URL
            self.query_url = self.PROD_QUERY_URL

    def _encrypt_aes(self, data: str) -> str:
        """
        AES-128-CBC 加密

        Args:
            data: 要加密的字串

        Returns:
            Base64 編碼的加密字串
        """
        # URL Encode
        url_encoded = urllib.parse.quote(data)

        # AES-128-CBC 加密
        cipher = AES.new(self.hash_key, AES.MODE_CBC, self.hash_iv)
        encrypted = cipher.encrypt(pad(url_encoded.encode('utf-8'), AES.block_size))

        # Base64 編碼
        return base64.b64encode(encrypted).decode('utf-8')

    def _decrypt_aes(self, encrypted_data: str) -> Dict[str, any]:
        """
        AES-128-CBC 解密

        Args:
            encrypted_data: Base64 編碼的加密字串

        Returns:
            解密後的 JSON 物件
        """
        # Base64 解碼
        encrypted = base64.b64decode(encrypted_data)

        # AES-128-CBC 解密
        cipher = AES.new(self.hash_key, AES.MODE_CBC, self.hash_iv)
        decrypted = unpad(cipher.decrypt(encrypted), AES.block_size).decode('utf-8')

        # URL Decode
        url_decoded = urllib.parse.unquote(decrypted)

        # JSON Parse
        return json.loads(url_decoded)

    def calculate_b2b_amounts(self, total_amount: int) -> Dict[str, int]:
        """
        計算 B2B 發票金額 (含稅總額 → 未稅金額 + 稅額)

        Args:
            total_amount: 含稅總額

        Returns:
            { 'sales_amount': 未稅金額, 'tax_amount': 稅額, 'total_amount': 總額 }

        Example:
            >>> svc.calculate_b2b_amounts(1050)
            {'sales_amount': 1000, 'tax_amount': 50, 'total_amount': 1050}
        """
        tax_amount = round(total_amount - (total_amount / 1.05))
        sales_amount = total_amount - tax_amount

        return {
            'sales_amount': sales_amount,
            'tax_amount': tax_amount,
            'total_amount': total_amount
        }

    def issue_invoice(self, data: InvoiceIssueData) -> InvoiceIssueResponse:
        """
        開立電子發票

        Args:
            data: 發票開立資料

        Returns:
            發票開立回應

        Raises:
            ValueError: 資料驗證失敗
            ConnectionError: API 連線失敗

        Example:
            >>> # B2C 二聯式發票
            >>> data = InvoiceIssueData(
            ...     merchant_id='2000132',
            ...     relate_number='ORD20240129001',
            ...     customer_identifier='0000000000',
            ...     customer_name='王小明',
            ...     customer_addr='台北市信義區',
            ...     customer_phone='0912345678',
            ...     customer_email='test@example.com',
            ...     sales_amount=1050,
            ...     total_amount=1050,
            ...     items=[
            ...         {'ItemName': '商品A', 'ItemCount': 1, 'ItemWord': '個', 'ItemPrice': 1000, 'ItemAmount': 1050}
            ...     ]
            ... )
            >>> response = svc.issue_invoice(data)
        """
        # 驗證資料
        if data.customer_identifier != '0000000000':
            # B2B 三聯式
            if len(data.customer_identifier) != 8:
                raise ValueError('B2B 發票統編必須為 8 碼')
            if data.carrier_type or data.love_code:
                raise ValueError('B2B 發票不可使用載具或捐贈')
            if data.tax_amount == 0:
                raise ValueError('B2B 發票必須計算稅額')

        # 準備 API 資料
        api_data = {
            'MerchantID': data.merchant_id,
            'RelateNumber': data.relate_number,
            'CustomerID': '',
            'CustomerIdentifier': data.customer_identifier,
            'CustomerName': data.customer_name,
            'CustomerAddr': data.customer_addr,
            'CustomerPhone': data.customer_phone,
            'CustomerEmail': data.customer_email,
            'ClearanceMark': '',
            'Print': data.print,
            'Donation': data.donation,
            'LoveCode': data.love_code,
            'CarrierType': data.carrier_type,
            'CarrierNum': data.carrier_num,
            'TaxType': data.tax_type,
            'SalesAmount': data.sales_amount,
            'InvType': data.inv_type,
            'vat': data.vat,
            'Items': data.items,
            'InvoiceRemark': data.remark,
            'TimeStamp': int(time.time())
        }

        # 加密資料
        json_string = json.dumps(api_data, ensure_ascii=False)
        encrypted_data = self._encrypt_aes(json_string)

        # 發送請求
        try:
            response = requests.post(
                self.api_url,
                data={'MerchantID': data.merchant_id, 'RqHeader': {'Timestamp': int(time.time())}, 'Data': encrypted_data},
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=30
            )
            response.raise_for_status()

            # 解析回應
            result = response.json()

            if 'Data' in result:
                decrypted = self._decrypt_aes(result['Data'])

                if decrypted.get('RtnCode') == 1:
                    return InvoiceIssueResponse(
                        success=True,
                        invoice_number=decrypted.get('InvoiceNo', ''),
                        invoice_date=decrypted.get('InvoiceDate', ''),
                        random_number=decrypted.get('RandomNumber', ''),
                        rtn_code=decrypted.get('RtnCode', 0),
                        rtn_msg=decrypted.get('RtnMsg', ''),
                        raw=decrypted
                    )
                else:
                    return InvoiceIssueResponse(
                        success=False,
                        rtn_code=decrypted.get('RtnCode', 0),
                        rtn_msg=decrypted.get('RtnMsg', ''),
                        error_message=f"發票開立失敗: {decrypted.get('RtnMsg', '未知錯誤')}",
                        raw=decrypted
                    )
            else:
                return InvoiceIssueResponse(
                    success=False,
                    error_message='API 回應格式錯誤',
                    raw=result
                )

        except requests.exceptions.RequestException as e:
            raise ConnectionError(f'API 連線失敗: {str(e)}')

    def void_invoice(self, data: InvoiceVoidData, reason: str = '訂單取消') -> Dict[str, any]:
        """
        作廢電子發票

        Args:
            data: 發票作廢資料
            reason: 作廢原因

        Returns:
            作廢結果

        Example:
            >>> void_data = InvoiceVoidData(
            ...     merchant_id='2000132',
            ...     invoice_no='AA12345678',
            ...     invoice_date='2024-01-29',
            ...     reason='訂單取消'
            ... )
            >>> result = svc.void_invoice(void_data)
        """
        api_data = {
            'MerchantID': data.merchant_id,
            'InvoiceNo': data.invoice_no,
            'InvoiceDate': data.invoice_date,
            'Reason': reason,
            'TimeStamp': int(time.time())
        }

        json_string = json.dumps(api_data, ensure_ascii=False)
        encrypted_data = self._encrypt_aes(json_string)

        try:
            response = requests.post(
                self.void_url,
                data={'MerchantID': data.merchant_id, 'RqHeader': {'Timestamp': int(time.time())}, 'Data': encrypted_data},
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=30
            )
            response.raise_for_status()

            result = response.json()

            if 'Data' in result:
                return self._decrypt_aes(result['Data'])
            else:
                return result

        except requests.exceptions.RequestException as e:
            raise ConnectionError(f'API 連線失敗: {str(e)}')

    def issue_allowance(self, data: InvoiceAllowanceData) -> Dict[str, any]:
        """
        開立折讓證明單

        Args:
            data: 折讓資料

        Returns:
            折讓結果

        Example:
            >>> allowance_data = InvoiceAllowanceData(
            ...     merchant_id='2000132',
            ...     invoice_no='AA12345678',
            ...     invoice_date='2024-01-29',
            ...     customer_name='王小明',
            ...     notify_mail='test@example.com',
            ...     allowance_amount=100,
            ...     items=[
            ...         {'ItemName': '商品A', 'ItemCount': 1, 'ItemWord': '個', 'ItemPrice': 100, 'ItemAmount': 100}
            ...     ]
            ... )
            >>> result = svc.issue_allowance(allowance_data)
        """
        api_data = {
            'MerchantID': data.merchant_id,
            'InvoiceNo': data.invoice_no,
            'InvoiceDate': data.invoice_date,
            'AllowanceNotify': data.allowance_notify,
            'CustomerName': data.customer_name,
            'NotifyMail': data.notify_mail,
            'NotifyPhone': data.notify_phone,
            'AllowanceAmount': data.allowance_amount,
            'Items': data.items,
            'TimeStamp': int(time.time())
        }

        json_string = json.dumps(api_data, ensure_ascii=False)
        encrypted_data = self._encrypt_aes(json_string)

        try:
            response = requests.post(
                self.allowance_url,
                data={'MerchantID': data.merchant_id, 'RqHeader': {'Timestamp': int(time.time())}, 'Data': encrypted_data},
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=30
            )
            response.raise_for_status()

            result = response.json()

            if 'Data' in result:
                return self._decrypt_aes(result['Data'])
            else:
                return result

        except requests.exceptions.RequestException as e:
            raise ConnectionError(f'API 連線失敗: {str(e)}')


# ============================================================================
# 使用範例
# ============================================================================

def example_b2c_invoice():
    """範例: B2C 二聯式發票開立"""
    print("=== B2C 二聯式發票開立範例 ===\n")

    # 初始化服務 (測試環境)
    service = ECPayInvoiceService(
        merchant_id=ECPayInvoiceService.TEST_MERCHANT_ID,
        hash_key=ECPayInvoiceService.TEST_HASH_KEY,
        hash_iv=ECPayInvoiceService.TEST_HASH_IV,
        is_test=True
    )

    # 準備發票資料
    invoice_data = InvoiceIssueData(
        merchant_id=ECPayInvoiceService.TEST_MERCHANT_ID,
        relate_number=f'ORD{int(time.time())}',  # 唯一訂單編號
        customer_identifier='0000000000',  # B2C 固定值
        customer_name='王小明',
        customer_addr='台北市信義區信義路五段7號',
        customer_phone='0912345678',
        customer_email='test@example.com',
        sales_amount=1050,  # B2C 含稅金額
        total_amount=1050,
        print='0',  # 不列印
        donation='0',  # 不捐贈
        carrier_type='',  # 不使用載具
        items=[
            {
                'ItemName': '測試商品A',
                'ItemCount': 1,
                'ItemWord': '個',
                'ItemPrice': 1000,
                'ItemTaxType': '1',
                'ItemAmount': 1050
            }
        ]
    )

    # 開立發票
    try:
        response = service.issue_invoice(invoice_data)

        if response.success:
            print(f"✓ 發票開立成功!")
            print(f"  發票號碼: {response.invoice_number}")
            print(f"  發票日期: {response.invoice_date}")
            print(f"  隨機碼: {response.random_number}")
        else:
            print(f"✗ 發票開立失敗: {response.error_message}")
            print(f"  錯誤碼: {response.rtn_code}")
            print(f"  錯誤訊息: {response.rtn_msg}")

    except Exception as e:
        print(f"✗ 發生錯誤: {str(e)}")


def example_b2b_invoice():
    """範例: B2B 三聯式發票開立"""
    print("\n=== B2B 三聯式發票開立範例 ===\n")

    service = ECPayInvoiceService(
        merchant_id=ECPayInvoiceService.TEST_MERCHANT_ID,
        hash_key=ECPayInvoiceService.TEST_HASH_KEY,
        hash_iv=ECPayInvoiceService.TEST_HASH_IV,
        is_test=True
    )

    # 計算 B2B 金額 (含稅 1050 → 未稅 1000 + 稅額 50)
    amounts = service.calculate_b2b_amounts(1050)

    invoice_data = InvoiceIssueData(
        merchant_id=ECPayInvoiceService.TEST_MERCHANT_ID,
        relate_number=f'ORD{int(time.time())}',
        customer_identifier='80129529',  # 8 碼統編
        customer_name='測試公司股份有限公司',
        customer_addr='台北市中正區重慶南路一段122號',
        customer_phone='02-23113456',
        customer_email='company@example.com',
        sales_amount=amounts['sales_amount'],  # 未稅金額
        tax_amount=amounts['tax_amount'],  # 稅額
        total_amount=amounts['total_amount'],  # 總額
        print='0',
        donation='0',
        carrier_type='',  # B2B 不可使用載具
        items=[
            {
                'ItemName': '測試商品B',
                'ItemCount': 1,
                'ItemWord': '個',
                'ItemPrice': 1000,  # 未稅單價
                'ItemTaxType': '1',
                'ItemAmount': 1000  # 未稅小計
            }
        ]
    )

    try:
        response = service.issue_invoice(invoice_data)

        if response.success:
            print(f"✓ B2B 發票開立成功!")
            print(f"  發票號碼: {response.invoice_number}")
            print(f"  未稅金額: {amounts['sales_amount']}")
            print(f"  稅額: {amounts['tax_amount']}")
            print(f"  總額: {amounts['total_amount']}")
        else:
            print(f"✗ B2B 發票開立失敗: {response.error_message}")

    except Exception as e:
        print(f"✗ 發生錯誤: {str(e)}")


def example_void_invoice():
    """範例: 發票作廢"""
    print("\n=== 發票作廢範例 ===\n")

    service = ECPayInvoiceService(
        merchant_id=ECPayInvoiceService.TEST_MERCHANT_ID,
        hash_key=ECPayInvoiceService.TEST_HASH_KEY,
        hash_iv=ECPayInvoiceService.TEST_HASH_IV,
        is_test=True
    )

    void_data = InvoiceVoidData(
        merchant_id=ECPayInvoiceService.TEST_MERCHANT_ID,
        invoice_no='AA12345678',  # 實際發票號碼
        invoice_date='2024/01/29',
        reason='訂單取消'
    )

    try:
        result = service.void_invoice(void_data)
        print(f"作廢結果: {result}")

    except Exception as e:
        print(f"✗ 發生錯誤: {str(e)}")


if __name__ == '__main__':
    # 執行範例
    example_b2c_invoice()
    example_b2b_invoice()
    # example_void_invoice()  # 需要有效的發票號碼

    print("\n" + "="*50)
    print("範例執行完畢!")
    print("="*50)
