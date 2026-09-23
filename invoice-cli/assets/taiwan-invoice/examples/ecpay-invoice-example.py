#!/usr/bin/env python3
"""
ECPay 綠界 B2C 電子發票 Python 完整範例

支援: 開立（個人 / 打統編）、作廢、折讓

依據（皆已對照原始碼 / 官方文件）:
- 加解密、請求格式：綠界官方 PHP SDK ecpay/sdk 1.3.2408190
  （AesService、AesRequest、PostWithAesJsonResponseService），
  由官方 WooCommerce 外掛 ecpay-ecommerce-for-woocommerce 1.1.2603230 內附
- 欄位規則：綠界官方 ecpay-api-skill guides/04-invoice-b2c.md（B2C 發票介接技術文件摘要）

API 文件: https://developers.ecpay.com.tw

注意：本範例是「B2C 發票平台」。開給公司（打統編）一樣走 B2C 平台的 Issue，
金額依 vat 參數決定含稅與否（預設含稅）；另有獨立的 B2B 發票平台（交換 / 存證），
欄位與金額規則都不同，不要混用。
"""

import base64
import json
import re
import time
import urllib.parse
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional

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


def php_urlencode(text: str) -> str:
    """
    與 PHP urlencode() 相同的編碼結果

    Python 的 quote_plus 會保留 "~" 不編碼，PHP 則編成 %7E；其餘規則一致
    （空白 → "+"，英數與 -_. 以外全部 %XX 大寫）。
    """
    return urllib.parse.quote_plus(text, safe='').replace('~', '%7E')


def php_json_encode(data: Any) -> str:
    """
    與 PHP json_encode()（預設旗標）相同的輸出

    PHP 預設：無空白分隔、非 ASCII 轉成 \\uXXXX、"/" 轉成 "\\/"。
    綠界伺服器解得開任何合法 JSON，這裡對齊只是為了能跟官方 SDK 逐位元組比對。
    """
    return json.dumps(data, ensure_ascii=True, separators=(',', ':')).replace('/', '\\/')


@dataclass
class InvoiceIssueData:
    """ECPay B2C 發票開立資料（欄位對應 /B2CInvoice/Issue 的 Data）"""
    relate_number: str                  # 特店自訂編號，每次唯一；英數字，大小寫視為相同
    sales_amount: int                   # 發票總金額；vat='1' 為含稅，須等於 Items 的 ItemAmount 加總
    items: List[Dict[str, Any]]         # ItemName / ItemCount / ItemWord / ItemPrice / ItemAmount（/ ItemTaxType）
    customer_email: str = ''            # CustomerPhone 與 CustomerEmail 至少擇一
    customer_phone: str = ''
    customer_name: str = ''             # Print='1' 時必填；打統編時建議填公司名稱
    customer_addr: str = ''             # Print='1' 時必填
    customer_identifier: str = ''       # 統一編號：空字串（個人）或 8 碼數字
    print_flag: Literal['0', '1'] = '0'
    donation: Literal['0', '1'] = '0'
    love_code: str = ''                 # Donation='1' 時必填
    carrier_type: Literal['', '1', '2', '3', '4', '5'] = ''  # ''=無 1=綠界 2=自然人憑證 3=手機條碼 4=悠遊卡 5=一卡通
    carrier_num: str = ''
    tax_type: Literal['1', '2', '3', '4', '9'] = '1'         # 1=應稅 2=零稅率 3=免稅 4=特種應稅 9=混合
    inv_type: Literal['07', '08'] = '07'                     # 07=一般稅額 08=特種稅額
    vat: Literal['0', '1'] = '1'                              # 商品單價是否含稅：1=含稅（預設）0=未稅
    invoice_remark: str = ''


@dataclass
class InvoiceVoidData:
    """ECPay 發票作廢資料"""
    invoice_no: str        # 發票號碼
    invoice_date: str      # 發票開立日期 (YYYY-MM-DD)
    reason: str            # 作廢原因


@dataclass
class InvoiceAllowanceData:
    """ECPay 發票折讓資料"""
    invoice_no: str
    invoice_date: str                   # 發票開立日期 (YYYY-MM-DD)
    customer_name: str
    allowance_amount: int               # 折讓總金額（含稅），需 > 0 且 ≤ 剩餘可折讓金額
    items: List[Dict[str, Any]] = field(default_factory=list)
    allowance_notify: Literal['E', 'S', 'A', 'N'] = 'E'  # E=Email S=簡訊 A=全部 N=不通知
    notify_mail: str = ''
    notify_phone: str = ''              # AllowanceNotify=S 時必填


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
    raw: Dict[str, Any] = field(default_factory=dict)


class ECPayInvoiceService:
    """
    ECPay 綠界 B2C 電子發票服務

    請求格式（與官方 SDK PostWithAesJsonResponseService 相同）:
        POST application/json
        {"MerchantID": ..., "RqHeader": {"Timestamp": ..., "Revision": "3.0.0"}, "Data": <AES 密文>}

        Data = base64( AES-128-CBC( urlencode( json_encode(資料) ) ) )，PKCS#7 padding

    回應為三層結構，必須檢查兩次：
        外層 TransCode == 1  → 傳輸成功
        解密 Data 後 RtnCode == 1 → 業務成功

    測試環境（發票專用帳號，與金流 3002607 不同）:
    - 商店代號: 2000132
    - HashKey: ejCk326UnaZWKisg
    - HashIV: q9jcZX8Ib9LM8wYk
    """

    TEST_MERCHANT_ID = '2000132'
    TEST_HASH_KEY = 'ejCk326UnaZWKisg'
    TEST_HASH_IV = 'q9jcZX8Ib9LM8wYk'

    TEST_BASE_URL = 'https://einvoice-stage.ecpay.com.tw/B2CInvoice'
    PROD_BASE_URL = 'https://einvoice.ecpay.com.tw/B2CInvoice'

    # RqHeader.Revision 必填，漏填會導致 TransCode != 1
    REVISION = '3.0.0'

    def __init__(self, merchant_id: str, hash_key: str, hash_iv: str, is_test: bool = True):
        if not HAS_CRYPTO:
            raise ImportError('需要安裝 pycryptodome: pip install pycryptodome')

        self.merchant_id = merchant_id
        self.hash_key = hash_key.encode('utf-8')
        self.hash_iv = hash_iv.encode('utf-8')
        self.base_url = self.TEST_BASE_URL if is_test else self.PROD_BASE_URL

    # ------------------------------------------------------------------
    # 加解密（與官方 SDK AesService 逐位元組相同）
    # ------------------------------------------------------------------

    def encrypt_data(self, data: Dict[str, Any]) -> str:
        """json_encode → urlencode → AES-128-CBC（PKCS#7）→ base64"""
        url_encoded = php_urlencode(php_json_encode(data))
        cipher = AES.new(self.hash_key, AES.MODE_CBC, self.hash_iv)
        encrypted = cipher.encrypt(pad(url_encoded.encode('utf-8'), AES.block_size))
        return base64.b64encode(encrypted).decode('utf-8')

    def decrypt_data(self, encrypted_data: str) -> Dict[str, Any]:
        """
        base64 → AES-128-CBC → urldecode → JSON

        必須用 unquote_plus：綠界以 PHP urlencode 編碼，空白是 "+"。
        用 unquote 的話，含空白的欄位（地址、備註、RtnMsg）會多出 "+"。
        """
        cipher = AES.new(self.hash_key, AES.MODE_CBC, self.hash_iv)
        decrypted = unpad(cipher.decrypt(base64.b64decode(encrypted_data)), AES.block_size)
        return json.loads(urllib.parse.unquote_plus(decrypted.decode('utf-8')))

    def build_request(self, data: Dict[str, Any], timestamp: Optional[int] = None) -> Dict[str, Any]:
        """組出送往綠界的 JSON 請求本體"""
        return {
            'MerchantID': self.merchant_id,
            'RqHeader': {
                'Timestamp': timestamp if timestamp is not None else int(time.time()),
                'Revision': self.REVISION,
            },
            'Data': self.encrypt_data(data),
        }

    def _post(self, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """送出請求並回傳解密後的 Data；TransCode != 1 時拋出例外"""
        if not HAS_REQUESTS:
            raise ImportError('需要安裝 requests: pip install requests')

        try:
            response = requests.post(
                f'{self.base_url}/{action}',
                json=self.build_request(data),   # application/json，不是表單
                timeout=30,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f'API 連線失敗: {e}')

        result = response.json()
        if result.get('TransCode') != 1:
            raise RuntimeError(f"傳輸失敗 TransCode={result.get('TransCode')}: {result.get('TransMsg')}")
        return self.decrypt_data(result['Data'])

    # ------------------------------------------------------------------
    # 業務 API
    # ------------------------------------------------------------------

    @staticmethod
    def validate_issue(data: InvoiceIssueData) -> None:
        """送出前檢查綠界文件列出的欄位互斥與必填規則"""
        if data.customer_identifier and not re.fullmatch(r'\d{8}', data.customer_identifier):
            raise ValueError('CustomerIdentifier 必須為空字串或 8 碼數字')
        if not (data.customer_email or data.customer_phone):
            raise ValueError('CustomerEmail 與 CustomerPhone 至少要填一個')
        if data.print_flag == '1' and not (data.customer_name and data.customer_addr):
            raise ValueError('Print=1 時 CustomerName 與 CustomerAddr 必填')
        if data.donation == '1':
            if data.customer_identifier:
                raise ValueError('打統編的發票不可捐贈')
            if data.carrier_type:
                raise ValueError('捐贈與載具互斥：Donation=1 時 CarrierType 必須為空')
            if not data.love_code:
                raise ValueError('Donation=1 時 LoveCode 必填')
        if data.carrier_type in ('2', '3', '4', '5') and not data.carrier_num:
            raise ValueError('CarrierType 為 2~5 時 CarrierNum 必填')
        if data.carrier_type == '3' and not re.fullmatch(r'/[0-9A-Z.+\-]{7}', data.carrier_num):
            raise ValueError('手機條碼格式為 "/" 加 7 碼（0-9 A-Z . + -）')

        total = round(sum(float(item['ItemAmount']) for item in data.items))
        if total != data.sales_amount:
            raise ValueError(f'SalesAmount({data.sales_amount}) 必須等於 ItemAmount 加總({total})')

    def issue_invoice(self, data: InvoiceIssueData) -> InvoiceIssueResponse:
        """
        開立電子發票（/B2CInvoice/Issue）

        Example:
            >>> data = InvoiceIssueData(
            ...     relate_number='ORD20260923001',
            ...     sales_amount=1050,
            ...     customer_email='test@example.com',
            ...     items=[{'ItemName': '商品A', 'ItemCount': 1, 'ItemWord': '個',
            ...             'ItemPrice': 1050, 'ItemAmount': 1050}],
            ... )
            >>> response = svc.issue_invoice(data)
        """
        self.validate_issue(data)

        payload = {
            'MerchantID': self.merchant_id,        # Data 內也要一份
            'RelateNumber': data.relate_number,
            'CustomerIdentifier': data.customer_identifier,
            'CustomerName': data.customer_name,
            'CustomerAddr': data.customer_addr,
            'CustomerPhone': data.customer_phone,
            'CustomerEmail': data.customer_email,
            'Print': data.print_flag,
            'Donation': data.donation,
            'LoveCode': data.love_code,
            'CarrierType': data.carrier_type,
            'CarrierNum': data.carrier_num,
            'TaxType': data.tax_type,
            'SalesAmount': data.sales_amount,
            'InvoiceRemark': data.invoice_remark,
            'InvType': data.inv_type,
            'vat': data.vat,
            'Items': data.items,
        }

        decrypted = self._post('Issue', payload)
        success = decrypted.get('RtnCode') == 1
        return InvoiceIssueResponse(
            success=success,
            invoice_number=decrypted.get('InvoiceNo', ''),
            invoice_date=decrypted.get('InvoiceDate', ''),
            random_number=decrypted.get('RandomNumber', ''),
            rtn_code=decrypted.get('RtnCode', 0),
            rtn_msg=decrypted.get('RtnMsg', ''),
            error_message='' if success else f"發票開立失敗: {decrypted.get('RtnMsg', '未知錯誤')}",
            raw=decrypted,
        )

    def void_invoice(self, data: InvoiceVoidData) -> Dict[str, Any]:
        """作廢電子發票（/B2CInvoice/Invalid），回傳解密後的 Data"""
        return self._post('Invalid', {
            'MerchantID': self.merchant_id,
            'InvoiceNo': data.invoice_no,
            'InvoiceDate': data.invoice_date,
            'Reason': data.reason,
        })

    def issue_allowance(self, data: InvoiceAllowanceData) -> Dict[str, Any]:
        """開立折讓（/B2CInvoice/Allowance），回傳解密後的 Data"""
        if data.allowance_notify in ('S', 'A') and not data.notify_phone:
            raise ValueError('AllowanceNotify 為 S 或 A 時 NotifyPhone 必填')
        if data.allowance_notify in ('E', 'A') and not data.notify_mail:
            raise ValueError('AllowanceNotify 為 E 或 A 時 NotifyMail 必填')
        return self._post('Allowance', {
            'MerchantID': self.merchant_id,
            'InvoiceNo': data.invoice_no,
            'InvoiceDate': data.invoice_date,
            'AllowanceNotify': data.allowance_notify,
            'CustomerName': data.customer_name,
            'NotifyMail': data.notify_mail,
            'NotifyPhone': data.notify_phone,
            'AllowanceAmount': data.allowance_amount,
            'Items': data.items,
        })


# ============================================================================
# 使用範例
# ============================================================================

def _test_service() -> ECPayInvoiceService:
    return ECPayInvoiceService(
        merchant_id=ECPayInvoiceService.TEST_MERCHANT_ID,
        hash_key=ECPayInvoiceService.TEST_HASH_KEY,
        hash_iv=ECPayInvoiceService.TEST_HASH_IV,
        is_test=True,
    )


def example_personal_invoice():
    """範例: 個人（雲端發票、綠界載具）"""
    print('=== 個人發票開立範例 ===\n')

    invoice_data = InvoiceIssueData(
        relate_number=f'ORD{int(time.time())}',
        sales_amount=1050,              # vat='1'：含稅總額
        customer_email='test@example.com',
        carrier_type='1',               # 綠界載具
        items=[{
            'ItemName': '測試商品A', 'ItemCount': 1, 'ItemWord': '個',
            'ItemPrice': 1050, 'ItemTaxType': '1', 'ItemAmount': 1050,
        }],
    )
    _run_issue(invoice_data)


def example_company_invoice():
    """範例: 打統編（一樣走 B2C 平台，金額依 vat 決定；此處為預設的含稅）"""
    print('\n=== 打統編發票開立範例 ===\n')

    invoice_data = InvoiceIssueData(
        relate_number=f'ORD{int(time.time())}C',
        sales_amount=1050,
        customer_identifier='80129529',
        customer_name='測試公司股份有限公司',
        customer_addr='台北市中正區重慶南路一段122號',
        customer_email='company@example.com',
        print_flag='1',                 # 打統編且無載具時須列印
        items=[{
            'ItemName': '測試商品B', 'ItemCount': 1, 'ItemWord': '個',
            'ItemPrice': 1050, 'ItemTaxType': '1', 'ItemAmount': 1050,
        }],
    )
    _run_issue(invoice_data)


def _run_issue(invoice_data: InvoiceIssueData):
    try:
        response = _test_service().issue_invoice(invoice_data)
        if response.success:
            print('✓ 發票開立成功!')
            print(f'  發票號碼: {response.invoice_number}')
            print(f'  發票日期: {response.invoice_date}')
            print(f'  隨機碼: {response.random_number}')
        else:
            print(f'✗ {response.error_message}（RtnCode={response.rtn_code}）')
    except Exception as e:
        print(f'✗ 發生錯誤: {e}')


def example_void_invoice():
    """範例: 發票作廢"""
    print('\n=== 發票作廢範例 ===\n')
    try:
        result = _test_service().void_invoice(InvoiceVoidData(
            invoice_no='AA12345678',    # 實際發票號碼
            invoice_date='2026-09-23',
            reason='訂單取消',
        ))
        print(f'作廢結果: {result}')
    except Exception as e:
        print(f'✗ 發生錯誤: {e}')


if __name__ == '__main__':
    example_personal_invoice()
    example_company_invoice()
    # example_void_invoice()  # 需要有效的發票號碼

    print('\n' + '=' * 50)
    print('範例執行完畢!')
    print('=' * 50)
