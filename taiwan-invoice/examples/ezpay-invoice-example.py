#!/usr/bin/env python3
"""
ezPay 簡單付電子發票 Python 完整範例

依照 taiwan-invoice-skill 規範撰寫。
ezPay 屬藍新金流集團，發票端與藍新 Newebpay 金流共用同一套加密邏輯
(AES-256-CBC + Hex + PKCS7 + SHA256 CheckCode)，但金鑰各自獨立。

支援: B2C 二聯式、B2B 三聯式、發票作廢、折讓、查詢、列印觸發

API 文件: https://inv.ezpay.com.tw/Invoice_index/download
測試後台: https://cinv.ezpay.com.tw/

依賴:
    pip install pycryptodome requests
"""

import binascii
import hashlib
import json
import time
import urllib.parse
from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional

import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


# ============================================================================
# Data classes
# ============================================================================

@dataclass
class InvoiceIssueData:
    """ezPay 發票開立資料 (B2C / B2B 共用)"""
    merchant_order_no: str  # 訂單編號 (唯一, 30 字內)
    status: Literal['1', '0', '3'] = '1'  # 1=立即開立, 0=待開立, 3=觸發開立
    category: Literal['B2B', 'B2C'] = 'B2C'  # 字軌類別
    buyer_name: str = ''
    buyer_ubn: str = ''  # 買方統編 (B2B 必填 8 碼; B2C 留空或填 0000000000)
    buyer_address: str = ''
    buyer_email: str = ''
    carrier_type: Optional[Literal['', '0', '1', '2']] = ''  # 0=ezPay 載具, 1=自然人憑證, 2=手機條碼
    carrier_num: str = ''
    love_code: str = ''  # 捐贈愛心碼 (3-7 碼); 與 carrier_type 互斥
    print_flag: Literal['Y', 'N'] = 'N'  # 是否列印 (B2B 強制 Y)
    tax_type: Literal['1', '2', '3', '9'] = '1'
    tax_rate: float = 5.0
    amt: int = 0  # 銷售額 (B2C 含稅; B2B 未稅)
    tax_amt: int = 0  # 稅額 (B2B 必填)
    total_amt: int = 0  # 總額 (含稅)
    item_name: str = ''  # 多項以 | 分隔
    item_count: str = ''  # 多項以 | 分隔
    item_unit: str = ''
    item_price: str = ''
    item_amt: str = ''
    item_tax_type: str = ''  # 混合課稅時必填
    comment: str = ''


@dataclass
class InvoiceIssueResponse:
    """ezPay 發票開立回應"""
    success: bool
    status: str = ''
    message: str = ''
    invoice_number: str = ''
    invoice_date: str = ''
    random_num: str = ''
    total_amt: int = 0
    raw: Dict[str, any] = field(default_factory=dict)


# ============================================================================
# Service
# ============================================================================

class EzpayInvoiceService:
    """
    ezPay 簡單付電子發票服務

    認證方式:
        - AES-256-CBC + Hex + PKCS7 Padding 加密 PostData_
        - SHA256 產生 CheckCode 驗證回傳合法性
        - HashKey: 32 碼; HashIV: 16 碼 (與 ECPay 16/16 不同)

    端點 (測試 cinv / 正式 inv):
        - 開立      : /Api_invoice_issue
        - 觸發開立  : /Api_invoice_touch
        - 作廢      : /Api_invoice_invalid
        - 折讓      : /Api_allowance_issue
        - 折讓觸發  : /Api_allowance_touch
        - 折讓作廢  : /Api_allowanceInvalid   (注意 camelCase)
        - 查詢      : /Api_invoice_search

    請求格式 (Form Post):
        MerchantID_ = 商店代號 (後綴底線不可省)
        PostData_   = AES-256 加密後的 hex 字串

    回傳格式 (JSON 或 String, 由 RespondType 控制):
        Status, Message, Result(JSON 字串)
        Result 內含 CheckCode, MerchantID, OrderNo, InvoiceNumber, ...
    """

    SANDBOX_BASE = 'https://cinv.ezpay.com.tw'
    PROD_BASE = 'https://inv.ezpay.com.tw'

    # 官方範例金鑰 (僅供加密邏輯測試使用; 實際申請後會取得專屬金鑰)
    SAMPLE_HASH_KEY = 'abcdefghijklmnopqrstuvwxyzabcdef'
    SAMPLE_HASH_IV = '1234567891234567'

    def __init__(self, merchant_id: str, hash_key: str, hash_iv: str, is_test: bool = True):
        if len(hash_key) != 32:
            raise ValueError(f'ezPay HashKey 必須為 32 碼 (收到 {len(hash_key)} 碼)')
        if len(hash_iv) != 16:
            raise ValueError(f'ezPay HashIV 必須為 16 碼 (收到 {len(hash_iv)} 碼)')

        self.merchant_id = merchant_id
        self.hash_key = hash_key.encode('utf-8')
        self.hash_iv = hash_iv.encode('utf-8')
        self.base_url = self.SANDBOX_BASE if is_test else self.PROD_BASE
        self.is_test = is_test

    # -- Encryption helpers ---------------------------------------------------

    def _encrypt_post_data(self, post_data: Dict[str, any]) -> str:
        """
        將欲加密的欄位組成 query string 後以 AES-256-CBC + PKCS7 加密, 輸出 hex.

        ezPay 與 Newebpay 金流共用此邏輯。
        """
        # 1. 組成 query string (key1=v1&key2=v2)
        query = urllib.parse.urlencode(post_data)
        # 2. AES-256-CBC + PKCS7
        cipher = AES.new(self.hash_key, AES.MODE_CBC, self.hash_iv)
        encrypted = cipher.encrypt(pad(query.encode('utf-8'), AES.block_size))
        # 3. Hex 字串輸出 (小寫)
        return binascii.hexlify(encrypted).decode('ascii')

    def _decrypt_post_data(self, hex_data: str) -> str:
        """解密 ezPay 回傳的 hex 字串為原始 query string"""
        encrypted = binascii.unhexlify(hex_data)
        cipher = AES.new(self.hash_key, AES.MODE_CBC, self.hash_iv)
        return unpad(cipher.decrypt(encrypted), AES.block_size).decode('utf-8')

    def _check_code(self, payload: Dict[str, any]) -> str:
        """
        計算 SHA256 CheckCode.

        Spec: HashIV={hash_iv}&{sorted_query}&HashKey={hash_key} 後 SHA256 (大寫).
        實作上採用 ezPay 官方 PHP sample 之欄位順序 (固定欄位排序)。
        """
        # 官方 spec 通常以欄位字母順序排列
        ordered = '&'.join(f'{k}={v}' for k, v in sorted(payload.items()))
        raw = f'HashIV={self.hash_iv.decode()}&{ordered}&HashKey={self.hash_key.decode()}'
        return hashlib.sha256(raw.encode('utf-8')).hexdigest().upper()

    # -- Amount calculation ---------------------------------------------------

    def calculate_b2b_amounts(self, total_amount: int, tax_rate: float = 5.0) -> Dict[str, int]:
        """B2B: 含稅總額 -> 未稅金額 + 稅額"""
        tax_amt = round(total_amount - (total_amount / (1 + tax_rate / 100)))
        return {
            'amt': total_amount - tax_amt,
            'tax_amt': tax_amt,
            'total_amt': total_amount,
        }

    # -- Operations -----------------------------------------------------------

    def issue_invoice(self, data: InvoiceIssueData) -> InvoiceIssueResponse:
        """開立電子發票 (B2C / B2B 統一端點, 以 Category 區分)"""
        if data.category == 'B2B':
            if not data.buyer_ubn or len(data.buyer_ubn) != 8 or not data.buyer_ubn.isdigit():
                raise ValueError('B2B 發票需要 8 碼數字統編')
            if data.tax_amt == 0:
                raise ValueError('B2B 發票必須計算稅額')
            if data.carrier_type or data.love_code:
                raise ValueError('B2B 發票不可使用載具或捐贈')
            if data.print_flag != 'Y':
                # 自動修正 — B2B 一律列印
                data.print_flag = 'Y'

        # 組成 PostData_ 欲加密的欄位 (Version 1.5)
        post_data = {
            'RespondType': 'JSON',
            'Version': '1.5',
            'TimeStamp': str(int(time.time())),
            'MerchantOrderNo': data.merchant_order_no,
            'Status': data.status,
            'Category': data.category,
            'BuyerName': data.buyer_name,
            'BuyerUBN': data.buyer_ubn,
            'BuyerAddress': data.buyer_address,
            'BuyerEmail': data.buyer_email,
            'CarrierType': data.carrier_type or '',
            'CarrierNum': data.carrier_num,
            'LoveCode': data.love_code,
            'PrintFlag': data.print_flag,
            'TaxType': data.tax_type,
            'TaxRate': str(data.tax_rate),
            'Amt': str(data.amt),
            'TaxAmt': str(data.tax_amt),
            'TotalAmt': str(data.total_amt),
            'ItemName': data.item_name,
            'ItemCount': data.item_count,
            'ItemUnit': data.item_unit,
            'ItemPrice': data.item_price,
            'ItemAmt': data.item_amt,
            'Comment': data.comment,
        }
        if data.tax_type == '9':
            post_data['ItemTaxType'] = data.item_tax_type

        return self._submit('/Api_invoice_issue', post_data)

    def void_invoice(self, invoice_number: str, invalid_reason: str) -> InvoiceIssueResponse:
        """作廢發票"""
        post_data = {
            'RespondType': 'JSON',
            'Version': '1.0',
            'TimeStamp': str(int(time.time())),
            'InvoiceNumber': invoice_number,
            'InvalidReason': invalid_reason,
        }
        return self._submit('/Api_invoice_invalid', post_data)

    def issue_allowance(
        self,
        invoice_no: str,
        merchant_order_no: str,
        items: List[Dict[str, any]],
        tax_type_for_allowance: str = '1',
    ) -> InvoiceIssueResponse:
        """開立折讓 (對應 /Api_allowance_issue)"""
        post_data = {
            'RespondType': 'JSON',
            'Version': '1.3',
            'TimeStamp': str(int(time.time())),
            'InvoiceNo': invoice_no,
            'MerchantOrderNo': merchant_order_no,
            'TaxTypeForMixed': tax_type_for_allowance,
            'ItemName': '|'.join(str(i.get('name', '')) for i in items),
            'ItemCount': '|'.join(str(i.get('count', 1)) for i in items),
            'ItemUnit': '|'.join(str(i.get('unit', '')) for i in items),
            'ItemPrice': '|'.join(str(i.get('price', 0)) for i in items),
            'ItemAmt': '|'.join(str(i.get('amount', 0)) for i in items),
            'ItemTaxAmt': '|'.join(str(i.get('tax_amt', 0)) for i in items),
            'TotalAmt': sum(i.get('amount', 0) for i in items),
        }
        return self._submit('/Api_allowance_issue', post_data)

    def void_allowance(self, allowance_no: str, invalid_reason: str) -> InvoiceIssueResponse:
        """作廢折讓 (注意端點為 camelCase)"""
        post_data = {
            'RespondType': 'JSON',
            'Version': '1.0',
            'TimeStamp': str(int(time.time())),
            'AllowanceNo': allowance_no,
            'InvalidReason': invalid_reason,
        }
        return self._submit('/Api_allowanceInvalid', post_data)

    def query_invoice(self, search_type: str, merchant_order_no: str = '', invoice_number: str = '') -> InvoiceIssueResponse:
        """
        查詢發票.

        Args:
            search_type: 0=以訂單編號查 (MerchantOrderNo); 1=以發票號碼查 (InvoiceNumber)
        """
        post_data = {
            'RespondType': 'JSON',
            'Version': '1.3',
            'TimeStamp': str(int(time.time())),
            'SearchType': search_type,
            'MerchantOrderNo': merchant_order_no,
            'InvoiceNumber': invoice_number,
        }
        return self._submit('/Api_invoice_search', post_data)

    # -- HTTP submit ----------------------------------------------------------

    def _submit(self, path: str, post_data: Dict[str, any]) -> InvoiceIssueResponse:
        """加密 + 提交 + 解析 ezPay 回應"""
        encrypted = self._encrypt_post_data(post_data)
        body = {
            'MerchantID_': self.merchant_id,
            'PostData_': encrypted,
        }
        url = self.base_url + path
        try:
            r = requests.post(url, data=body, timeout=30)
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f'ezPay API 連線失敗: {e}')

        try:
            resp = r.json()
        except ValueError:
            return InvoiceIssueResponse(success=False, message=f'回應非 JSON: {r.text[:200]}')

        # ezPay 標準回傳: { Status, Message, Result }
        status = resp.get('Status', '')
        message = resp.get('Message', '')
        result_raw = resp.get('Result')

        # Result 可能是字串 (JSON-encoded) 或物件
        if isinstance(result_raw, str):
            try:
                result = json.loads(result_raw)
            except json.JSONDecodeError:
                result = {'_unparsed': result_raw}
        elif isinstance(result_raw, dict):
            result = result_raw
        else:
            result = {}

        return InvoiceIssueResponse(
            success=(status == 'SUCCESS'),
            status=status,
            message=message,
            invoice_number=result.get('InvoiceNumber', ''),
            invoice_date=result.get('CreateTime', ''),
            random_num=result.get('RandomNum', ''),
            total_amt=int(result.get('TotalAmt', 0) or 0),
            raw=resp,
        )


# ============================================================================
# Examples
# ============================================================================

def example_b2c():
    print('=== ezPay B2C 二聯式發票範例 ===\n')
    svc = EzpayInvoiceService(
        merchant_id='TEST_MERCHANT_ID',  # 替換為自己的測試 MerchantID
        hash_key=EzpayInvoiceService.SAMPLE_HASH_KEY,
        hash_iv=EzpayInvoiceService.SAMPLE_HASH_IV,
        is_test=True,
    )

    data = InvoiceIssueData(
        merchant_order_no=f'ORD{int(time.time())}',
        status='1',
        category='B2C',
        buyer_name='王小明',
        buyer_email='test@example.com',
        carrier_type='2',  # 手機條碼
        carrier_num='/ABC1234',
        print_flag='N',
        tax_type='1',
        amt=1000,
        tax_amt=50,
        total_amt=1050,
        item_name='測試商品A',
        item_count='1',
        item_unit='個',
        item_price='1050',
        item_amt='1050',
    )
    resp = svc.issue_invoice(data)
    if resp.success:
        print(f'[OK] 發票號碼: {resp.invoice_number}, 隨機碼: {resp.random_num}')
    else:
        print(f'[FAIL] {resp.status}: {resp.message}')


def example_b2b():
    print('\n=== ezPay B2B 三聯式發票範例 ===\n')
    svc = EzpayInvoiceService(
        merchant_id='TEST_MERCHANT_ID',
        hash_key=EzpayInvoiceService.SAMPLE_HASH_KEY,
        hash_iv=EzpayInvoiceService.SAMPLE_HASH_IV,
        is_test=True,
    )

    amounts = svc.calculate_b2b_amounts(1050)
    data = InvoiceIssueData(
        merchant_order_no=f'ORD{int(time.time())}',
        status='1',
        category='B2B',
        buyer_name='測試公司股份有限公司',
        buyer_ubn='80129529',  # 8 碼統編
        buyer_address='台北市信義區',
        buyer_email='company@example.com',
        print_flag='Y',  # B2B 強制列印
        tax_type='1',
        amt=amounts['amt'],
        tax_amt=amounts['tax_amt'],
        total_amt=amounts['total_amt'],
        item_name='測試商品B',
        item_count='1',
        item_unit='個',
        item_price=str(amounts['amt']),
        item_amt=str(amounts['amt']),
    )
    resp = svc.issue_invoice(data)
    if resp.success:
        print(f'[OK] B2B 發票號碼: {resp.invoice_number} (未稅 {amounts["amt"]} + 稅 {amounts["tax_amt"]} = {amounts["total_amt"]})')
    else:
        print(f'[FAIL] {resp.status}: {resp.message}')


if __name__ == '__main__':
    example_b2c()
    example_b2b()
