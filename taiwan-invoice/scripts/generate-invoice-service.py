#!/usr/bin/env python3
"""
Taiwan Invoice Service Generator
根據 CSV 數據生成完整的發票服務實作

用法:
    python generate-invoice-service.py ECPay              # 生成 ECPay 服務 (TypeScript)
    python generate-invoice-service.py SmilePay --lang python  # 生成 SmilePay 服務 (Python)
    python generate-invoice-service.py Amego --output ./lib/   # 指定輸出目錄
    python generate-invoice-service.py NewProvider        # 生成新服務商模板
"""

import sys
import os
import csv
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any

# 取得腳本目錄
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / 'data'


def load_csv(filename: str) -> List[Dict[str, str]]:
    """載入 CSV 檔案"""
    filepath = DATA_DIR / filename
    if not filepath.exists():
        return []

    with open(filepath, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def get_provider_info(provider: str) -> Optional[Dict[str, str]]:
    """取得服務商資訊"""
    providers = load_csv('providers.csv')
    for p in providers:
        if p['provider'].lower() == provider.lower():
            return p
    return None


def get_operations(provider: str) -> List[Dict[str, str]]:
    """取得服務商的操作端點"""
    operations = load_csv('operations.csv')
    result = []
    for op in operations:
        endpoint_key = f"{provider.lower()}_endpoint" if provider.lower() != 'ecpay' else f"{provider.lower()}_b2c_endpoint"
        if endpoint_key in op or f"{provider.lower()}_b2c_endpoint" in op:
            result.append(op)
    return result


def get_field_mappings(provider: str) -> List[Dict[str, str]]:
    """取得欄位映射"""
    mappings = load_csv('field-mappings.csv')
    provider_col = f"{provider.lower()}_name"
    return [m for m in mappings if m.get(provider_col)]


def get_error_codes(provider: str) -> List[Dict[str, str]]:
    """取得錯誤碼"""
    errors = load_csv('error-codes.csv')
    return [e for e in errors if e['provider'].lower() == provider.lower()]


# TypeScript 模板
TS_TEMPLATE = '''import crypto from 'crypto'

/**
 * {display_name} 電子發票服務
 *
 * 認證方式: {auth_method}
 * 加密方式: {encryption}
 *
 * 自動生成 by taiwan-invoice-skill
 */

interface InvoiceIssueData {{
    OrderId: string
    BuyerIdentifier?: string
    BuyerName?: string
    BuyerEmail?: string
    IsB2B?: boolean
    SalesAmount?: number
    TaxAmount?: number
    TotalAmount?: number
    ProductItem?: Array<{{
        Description: string
        Quantity: number
        UnitPrice: number
        Amount: number
    }}>
}}

interface InvoiceIssueResponse {{
    success: boolean
    code: number | string
    msg: string
    invoiceNumber?: string
    randomNumber?: string
    raw?: any
}}

interface InvoiceVoidResponse {{
    success: boolean
    msg: string
}}

interface InvoicePrintResponse {{
    success: boolean
    type: 'html' | 'redirect' | 'form'
    printUrl?: string
    htmlContent?: string
    formData?: Record<string, string>
}}

export class {class_name}InvoiceService {{
    private TEST_URL = '{test_url}'
    private PROD_URL = '{prod_url}'
    private API_BASE_URL: string

    // 測試帳號
    private TEST_MERCHANT_ID = '{test_merchant_id}'
{test_credentials}

    constructor(isProd: boolean = false) {{
        this.API_BASE_URL = isProd ? this.PROD_URL : this.TEST_URL
    }}

    /**
     * 開立發票
     * 端點: {issue_endpoint}
     */
    async issueInvoice(merchantId: string, hashKey: string, hashIV: string, data: InvoiceIssueData): Promise<InvoiceIssueResponse> {{
        const isB2B = data.IsB2B === true

        // 金額計算
        const amounts = this.calculateAmounts(data.TotalAmount || data.SalesAmount || 0, isB2B)

        // 準備 API 資料
        const apiData = {{
{issue_fields}
        }}

        // TODO: 實作加密/簽章
        // {auth_method}

        const response = await fetch(`${{this.API_BASE_URL}}{issue_endpoint}`, {{
            method: 'POST',
            headers: {{
                'Content-Type': '{content_type}',
            }},
            body: {request_body},
        }})

        const result = await response.json()

        return {{
            success: {success_condition},
            code: result.{code_field},
            msg: result.{msg_field},
            invoiceNumber: result.{invoice_field},
            randomNumber: result.{random_field},
            raw: result,
        }}
    }}

    /**
     * 作廢發票
     * 端點: {void_endpoint}
     */
    async voidInvoice(merchantId: string, hashKey: string, hashIV: string, invoiceNumber: string, reason: string): Promise<InvoiceVoidResponse> {{
        const apiData = {{
            InvoiceNumber: invoiceNumber,
            Reason: reason,
        }}

        // TODO: 實作 API 請求

        return {{
            success: true,
            msg: '發票作廢成功',
        }}
    }}

    /**
     * 列印發票
     * 端點: {print_endpoint}
     */
    async printInvoice(merchantId: string, hashKey: string, invoiceNumber: string, invoiceDate: string, randomNumber: string): Promise<InvoicePrintResponse> {{
        // {print_method}
        return {{
            success: true,
            type: '{print_type}',
            printUrl: `${{this.API_BASE_URL}}{print_endpoint}?InvoiceNo=${{invoiceNumber}}`,
        }}
    }}

    /**
     * 金額計算
     * B2C: TaxAmount = 0, SalesAmount = 含稅總額
     * B2B: TaxAmount = 稅額, SalesAmount = 未稅
     */
    private calculateAmounts(totalAmount: number, isB2B: boolean) {{
        if (isB2B) {{
            const taxAmount = Math.round(totalAmount - (totalAmount / 1.05))
            const salesAmount = totalAmount - taxAmount
            return {{ salesAmount, taxAmount, totalAmount }}
        }} else {{
            return {{ salesAmount: totalAmount, taxAmount: 0, totalAmount }}
        }}
    }}

{encryption_method}
}}

/**
 * 錯誤碼參考
{error_codes}
 */
'''

# Python 模板
PY_TEMPLATE = '''#!/usr/bin/env python3
"""
{display_name} 電子發票服務

認證方式: {auth_method}
加密方式: {encryption}

自動生成 by taiwan-invoice-skill
"""

import hashlib
import json
import urllib.parse
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

@dataclass
class InvoiceIssueData:
    order_id: str
    buyer_identifier: str = ""
    buyer_name: str = ""
    buyer_email: str = ""
    is_b2b: bool = False
    sales_amount: int = 0
    tax_amount: int = 0
    total_amount: int = 0
    product_items: List[Dict[str, Any]] = None

@dataclass
class InvoiceIssueResponse:
    success: bool
    code: str
    msg: str
    invoice_number: str = ""
    random_number: str = ""
    raw: Dict = None

class {class_name}InvoiceService:
    """
    {display_name} 電子發票服務
    """

    TEST_URL = '{test_url}'
    PROD_URL = '{prod_url}'

    # 測試帳號
    TEST_MERCHANT_ID = '{test_merchant_id}'
{test_credentials_py}

    def __init__(self, is_prod: bool = False):
        self.api_base_url = self.PROD_URL if is_prod else self.TEST_URL

    def issue_invoice(self, merchant_id: str, hash_key: str, hash_iv: str,
                      data: InvoiceIssueData) -> InvoiceIssueResponse:
        """
        開立發票
        端點: {issue_endpoint}
        """
        is_b2b = data.is_b2b

        # 金額計算
        amounts = self._calculate_amounts(data.total_amount or data.sales_amount or 0, is_b2b)

        # 準備 API 資料
        api_data = {{
{issue_fields_py}
        }}

        # TODO: 實作加密/簽章和 API 請求
        # {auth_method}

        return InvoiceIssueResponse(
            success=True,
            code="0",
            msg="",
            invoice_number="",
            random_number="",
            raw={{}}
        )

    def void_invoice(self, merchant_id: str, hash_key: str, hash_iv: str,
                     invoice_number: str, reason: str) -> Dict[str, Any]:
        """
        作廢發票
        端點: {void_endpoint}
        """
        api_data = {{
            "InvoiceNumber": invoice_number,
            "Reason": reason,
        }}

        # TODO: 實作 API 請求

        return {{"success": True, "msg": "發票作廢成功"}}

    def print_invoice(self, merchant_id: str, invoice_number: str,
                      invoice_date: str, random_number: str) -> Dict[str, Any]:
        """
        列印發票
        端點: {print_endpoint}
        """
        return {{
            "success": True,
            "type": "{print_type}",
            "print_url": f"{{self.api_base_url}}{print_endpoint}?InvoiceNo={{invoice_number}}"
        }}

    def _calculate_amounts(self, total_amount: int, is_b2b: bool) -> Dict[str, int]:
        """
        金額計算
        B2C: TaxAmount = 0, SalesAmount = 含稅總額
        B2B: TaxAmount = 稅額, SalesAmount = 未稅
        """
        if is_b2b:
            tax_amount = round(total_amount - (total_amount / 1.05))
            sales_amount = total_amount - tax_amount
            return {{"sales_amount": sales_amount, "tax_amount": tax_amount, "total_amount": total_amount}}
        else:
            return {{"sales_amount": total_amount, "tax_amount": 0, "total_amount": total_amount}}

{encryption_method_py}

# 錯誤碼參考
ERROR_CODES = {{
{error_codes_py}
}}
'''


def get_ecpay_specifics() -> Dict[str, str]:
    """ECPay 特定配置"""
    return {
        'test_credentials': '    private TEST_HASH_KEY = \'ejCk326UnaZWKisg\'\n    private TEST_HASH_IV = \'q9jcZX8Ib9LM8wYk\'',
        'test_credentials_py': '    TEST_HASH_KEY = "ejCk326UnaZWKisg"\n    TEST_HASH_IV = "q9jcZX8Ib9LM8wYk"',
        'issue_endpoint': '/B2CInvoice/Issue',
        'void_endpoint': '/B2CInvoice/Invalid',
        'print_endpoint': '/Invoice/Print',
        'content_type': 'application/json',
        'request_body': 'JSON.stringify({ MerchantID: merchantId, RqHeader: { Timestamp: Math.floor(Date.now() / 1000) }, Data: encryptedData })',
        'success_condition': 'result.TransCode === 1 && result.Data?.RtnCode === 1',
        'code_field': 'Data?.RtnCode || result.TransCode',
        'msg_field': 'Data?.RtnMsg || result.TransMsg',
        'invoice_field': 'Data?.InvoiceNo',
        'random_field': 'Data?.RandomNumber',
        'print_type': 'form',
        'print_method': 'ECPay 使用 POST 表單跳轉',
        'encryption_method': '''    /**
     * AES-128-CBC 加密
     */
    private encryptData(data: any, hashKey: string, hashIV: string): string {
        const jsonString = JSON.stringify(data)
        const urlEncoded = encodeURIComponent(jsonString)

        const cipher = crypto.createCipheriv('aes-128-cbc', hashKey, hashIV)
        let encrypted = cipher.update(urlEncoded, 'utf8', 'base64')
        encrypted += cipher.final('base64')

        return encrypted
    }

    /**
     * AES-128-CBC 解密
     */
    private decryptData(encryptedData: string, hashKey: string, hashIV: string): any {
        const decipher = crypto.createDecipheriv('aes-128-cbc', hashKey, hashIV)
        let decrypted = decipher.update(encryptedData, 'base64', 'utf8')
        decrypted += decipher.final('utf8')

        const urlDecoded = decodeURIComponent(decrypted)
        return JSON.parse(urlDecoded)
    }''',
        'encryption_method_py': '''    def _encrypt_data(self, data: Dict, hash_key: str, hash_iv: str) -> str:
        """AES-128-CBC 加密"""
        from Crypto.Cipher import AES
        from Crypto.Util.Padding import pad
        import base64

        json_string = json.dumps(data, ensure_ascii=False)
        url_encoded = urllib.parse.quote(json_string)

        cipher = AES.new(hash_key.encode(), AES.MODE_CBC, hash_iv.encode())
        padded = pad(url_encoded.encode(), AES.block_size)
        encrypted = cipher.encrypt(padded)

        return base64.b64encode(encrypted).decode()''',
        'issue_fields': '''            MerchantID: merchantId,
            RelateNumber: data.OrderId,
            CustomerIdentifier: data.BuyerIdentifier || '',
            CustomerName: data.BuyerName || '',
            CustomerEmail: data.BuyerEmail || '',
            Print: isB2B ? '1' : '0',
            Donation: '0',
            TaxType: '1',
            InvType: '07',
            SalesAmount: amounts.salesAmount,
            TaxAmount: amounts.taxAmount,
            TotalAmount: amounts.totalAmount,
            Items: data.ProductItem?.map((item, idx) => ({
                ItemSeq: idx + 1,
                ItemName: item.Description,
                ItemCount: item.Quantity,
                ItemWord: '個',
                ItemPrice: item.UnitPrice,
                ItemAmount: item.Amount,
            })) || [],''',
        'issue_fields_py': '''            "MerchantID": merchant_id,
            "RelateNumber": data.order_id,
            "CustomerIdentifier": data.buyer_identifier or "",
            "CustomerName": data.buyer_name or "",
            "CustomerEmail": data.buyer_email or "",
            "Print": "1" if is_b2b else "0",
            "Donation": "0",
            "TaxType": "1",
            "InvType": "07",
            "SalesAmount": amounts["sales_amount"],
            "TaxAmount": amounts["tax_amount"],
            "TotalAmount": amounts["total_amount"],
            "Items": [
                {
                    "ItemSeq": idx + 1,
                    "ItemName": item["Description"],
                    "ItemCount": item["Quantity"],
                    "ItemWord": "個",
                    "ItemPrice": item["UnitPrice"],
                    "ItemAmount": item["Amount"],
                }
                for idx, item in enumerate(data.product_items or [])
            ],''',
    }


def get_smilepay_specifics() -> Dict[str, str]:
    """SmilePay 特定配置"""
    return {
        'test_credentials': '    private TEST_VERIFY_KEY = \'9D73935693EE0237FABA6AB744E48661\'',
        'test_credentials_py': '    TEST_VERIFY_KEY = "9D73935693EE0237FABA6AB744E48661"',
        'issue_endpoint': '/SPEinvoice_Storage.asp',
        'void_endpoint': '/SPEinvoice_Storage_Modify.asp',
        'print_endpoint': '/SmilePayCarrier/InvoiceDetails.php',
        'content_type': 'application/x-www-form-urlencoded',
        'request_body': 'new URLSearchParams(apiData).toString()',
        'success_condition': 'result.Status === "0"',
        'code_field': 'Status',
        'msg_field': 'Desc',
        'invoice_field': 'InvoiceNumber',
        'random_field': 'RandomNumber',
        'print_type': 'redirect',
        'print_method': 'SmilePay 使用 GET URL 跳轉',
        'encryption_method': '''    // SmilePay 使用 Verify_key 驗證，無需額外加密''',
        'encryption_method_py': '''    # SmilePay 使用 Verify_key 驗證，無需額外加密
    pass''',
        'issue_fields': '''            Grvc: merchantId,
            Verify_key: hashKey,
            InvoiceDate: new Date().toISOString().split('T')[0].replace(/-/g, '/'),
            InvoiceTime: new Date().toTimeString().split(' ')[0],
            Intype: '07',
            TaxType: '1',
            DonateMark: '0',
            Buyer_id: isB2B ? data.BuyerIdentifier : '',
            Name: data.BuyerName || '',
            Email: data.BuyerEmail || '',
            Description: data.ProductItem?.map(i => i.Description).join('|') || '',
            Quantity: data.ProductItem?.map(i => i.Quantity).join('|') || '',
            UnitPrice: data.ProductItem?.map(i => i.UnitPrice).join('|') || '',
            Amount: data.ProductItem?.map(i => i.Amount).join('|') || '',
            AllAmount: String(amounts.totalAmount),
            data_id: data.OrderId,''',
        'issue_fields_py': '''            "Grvc": merchant_id,
            "Verify_key": hash_key,
            "InvoiceDate": datetime.now().strftime("%Y/%m/%d"),
            "InvoiceTime": datetime.now().strftime("%H:%M:%S"),
            "Intype": "07",
            "TaxType": "1",
            "DonateMark": "0",
            "Buyer_id": data.buyer_identifier if is_b2b else "",
            "Name": data.buyer_name or "",
            "Email": data.buyer_email or "",
            "Description": "|".join(i["Description"] for i in (data.product_items or [])),
            "Quantity": "|".join(str(i["Quantity"]) for i in (data.product_items or [])),
            "UnitPrice": "|".join(str(i["UnitPrice"]) for i in (data.product_items or [])),
            "Amount": "|".join(str(i["Amount"]) for i in (data.product_items or [])),
            "AllAmount": str(amounts["total_amount"]),
            "data_id": data.order_id,''',
    }


def get_amego_specifics() -> Dict[str, str]:
    """Amego 特定配置"""
    return {
        'test_credentials': '    private TEST_APP_KEY = \'sHeq7t8G1wiQvhAuIM27\'',
        'test_credentials_py': '    TEST_APP_KEY = "sHeq7t8G1wiQvhAuIM27"',
        'issue_endpoint': '/json/f0401',
        'void_endpoint': '/json/f0501',
        'print_endpoint': '/json/invoice_file',
        'content_type': 'application/x-www-form-urlencoded',
        'request_body': 'new URLSearchParams({ invoice: merchantId, data: encodeURIComponent(JSON.stringify(apiData)), time: String(timestamp), sign: signature }).toString()',
        'success_condition': 'result.code === 0',
        'code_field': 'code',
        'msg_field': 'msg',
        'invoice_field': 'invoice_number',
        'random_field': 'random_number',
        'print_type': 'redirect',
        'print_method': 'Amego 回傳 PDF URL (10分鐘有效)',
        'encryption_method': '''    /**
     * MD5 簽章
     */
    private generateSignature(data: any, time: number, appKey: string): string {
        const signString = JSON.stringify(data) + time + appKey
        return crypto.createHash('md5').update(signString).digest('hex')
    }''',
        'encryption_method_py': '''    def _generate_signature(self, data: Dict, time: int, app_key: str) -> str:
        """MD5 簽章"""
        sign_string = json.dumps(data, ensure_ascii=False) + str(time) + app_key
        return hashlib.md5(sign_string.encode()).hexdigest()''',
        'issue_fields': '''            OrderId: data.OrderId,
            BuyerIdentifier: data.BuyerIdentifier || '0000000000',
            BuyerName: data.BuyerName || '客人',
            BuyerEmailAddress: data.BuyerEmail || '',
            SalesAmount: amounts.salesAmount,
            FreeTaxSalesAmount: 0,
            ZeroTaxSalesAmount: 0,
            TaxType: 1,
            TaxRate: '0.05',
            TaxAmount: amounts.taxAmount,
            TotalAmount: amounts.totalAmount,
            DetailVat: isB2B ? 0 : 1,
            ProductItem: data.ProductItem?.map(item => ({
                Description: item.Description,
                Quantity: item.Quantity,
                UnitPrice: item.UnitPrice,
                Amount: item.Amount,
                TaxType: 1,
            })) || [],''',
        'issue_fields_py': '''            "OrderId": data.order_id,
            "BuyerIdentifier": data.buyer_identifier or "0000000000",
            "BuyerName": data.buyer_name or "客人",
            "BuyerEmailAddress": data.buyer_email or "",
            "SalesAmount": amounts["sales_amount"],
            "FreeTaxSalesAmount": 0,
            "ZeroTaxSalesAmount": 0,
            "TaxType": 1,
            "TaxRate": "0.05",
            "TaxAmount": amounts["tax_amount"],
            "TotalAmount": amounts["total_amount"],
            "DetailVat": 0 if is_b2b else 1,
            "ProductItem": [
                {
                    "Description": item["Description"],
                    "Quantity": item["Quantity"],
                    "UnitPrice": item["UnitPrice"],
                    "Amount": item["Amount"],
                    "TaxType": 1,
                }
                for item in (data.product_items or [])
            ],''',
    }


def generate_service(provider: str, lang: str = 'typescript', output_dir: str = '.'):
    """生成服務檔案"""
    provider_info = get_provider_info(provider)
    error_codes = get_error_codes(provider)

    # 選擇特定配置
    if provider.lower() == 'ecpay':
        specifics = get_ecpay_specifics()
    elif provider.lower() == 'smilepay':
        specifics = get_smilepay_specifics()
    elif provider.lower() == 'amego':
        specifics = get_amego_specifics()
    else:
        # 新服務商使用通用模板
        specifics = {
            'test_credentials': '    // TODO: 填入測試金鑰',
            'test_credentials_py': '    # TODO: 填入測試金鑰',
            'issue_endpoint': '/issue',
            'void_endpoint': '/void',
            'print_endpoint': '/print',
            'content_type': 'application/json',
            'request_body': 'JSON.stringify(apiData)',
            'success_condition': 'result.code === 0',
            'code_field': 'code',
            'msg_field': 'msg',
            'invoice_field': 'invoice_number',
            'random_field': 'random_number',
            'print_type': 'redirect',
            'print_method': 'TODO: 實作列印邏輯',
            'encryption_method': '    // TODO: 實作加密/簽章',
            'encryption_method_py': '    # TODO: 實作加密/簽章\n    pass',
            'issue_fields': '            // TODO: 填入 API 參數',
            'issue_fields_py': '            # TODO: 填入 API 參數',
        }

    # 格式化錯誤碼
    if lang == 'typescript':
        error_codes_str = '\n'.join([f" * {e['code']}: {e['message_zh']}" for e in error_codes[:15]])
    else:
        error_codes_str = '\n'.join([f'    "{e["code"]}": "{e["message_zh"]}",' for e in error_codes[:15]])

    # 準備模板變數
    template_vars = {
        'class_name': provider.capitalize(),
        'display_name': provider_info['display_name'] if provider_info else provider,
        'auth_method': provider_info['auth_method'] if provider_info else 'TODO',
        'encryption': provider_info['encryption'] if provider_info else 'TODO',
        'test_url': provider_info['test_url'] if provider_info else 'https://test.example.com',
        'prod_url': provider_info['prod_url'] if provider_info else 'https://api.example.com',
        'test_merchant_id': provider_info['test_merchant_id'] if provider_info else 'TEST123',
        'error_codes': error_codes_str,
        'error_codes_py': error_codes_str,
        **specifics,
    }

    # 選擇模板
    if lang == 'python':
        template = PY_TEMPLATE
        ext = 'py'
    else:
        template = TS_TEMPLATE
        ext = 'ts'

    # 生成內容
    content = template.format(**template_vars)

    # 輸出檔案
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    filename = f"{provider.lower()}-invoice-service.{ext}"
    filepath = output_path / filename

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"[OK] 已生成服務檔案: {filepath}")
    print(f"\n服務商資訊:")
    if provider_info:
        print(f"  名稱: {provider_info['display_name']}")
        print(f"  認證: {provider_info['auth_method']}")
        print(f"  加密: {provider_info['encryption']}")
    print(f"\n錯誤碼數量: {len(error_codes)}")

    print(f"\n接下來的步驟:")
    print(f"1. 檢查生成的程式碼")
    print(f"2. 完成 TODO 標記的部分")
    print(f"3. 整合到專案中")


def main():
    parser = argparse.ArgumentParser(
        description='Taiwan Invoice Service Generator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python generate-invoice-service.py ECPay
    python generate-invoice-service.py SmilePay --lang python
    python generate-invoice-service.py Amego --output ./lib/services/
    python generate-invoice-service.py NewProvider
        """
    )

    parser.add_argument('provider', help='服務商名稱 (ECPay, SmilePay, Amego, 或新服務商名稱)')
    parser.add_argument('-l', '--lang', choices=['typescript', 'python'], default='typescript',
                        help='輸出語言 (default: typescript)')
    parser.add_argument('-o', '--output', default='.', help='輸出目錄 (default: 當前目錄)')
    parser.add_argument('--list', action='store_true', help='列出支援的服務商')

    args = parser.parse_args()

    if args.list:
        providers = load_csv('providers.csv')
        print("\n支援的服務商:")
        for p in providers:
            print(f"  {p['provider']} - {p['display_name']}")
        return

    generate_service(args.provider, args.lang, args.output)


if __name__ == '__main__':
    main()
