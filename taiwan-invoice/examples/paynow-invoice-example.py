#!/usr/bin/env python3
"""
立吉富 PayNow 電子發票 Python 範例 (preliminary)

依照 taiwan-invoice-skill 規範撰寫。

⚠️ DISCLAIMER ⚠️
PayNow 公開技術文件較稀疏 (官方頁面 https://docs.paynow.com.tw/developer/docs/invoice/
僅約 70 行)。下方端點路徑、欄位名稱與錯誤碼有部分為依社群慣例與
PayNow 金流端 callback 欄位推測而成 — 實際串接前請向 PayNow 索取官方
"Invoice Management v1.5" PDF 並比對欄位細節。

需與 PayNow 確認的事項 (見 references/PAYNOW_API_REFERENCE.md):
  1. 發票端的精確 endpoint 路徑 (/invoice/issue 等為合理推測)
  2. B2C 與 B2B 路由方式 (是否單一端點 + Category 切換)
  3. 完整 Request / Response schema
  4. 錯誤碼總表
  5. 載具 / 愛心碼驗證 endpoint
  6. JWT-Token 申請、發行、過期、輪替流程
  7. POS 批次取號額度
  8. webhook / callback 簽章機制 (若有)

支援:
  - 一般串接 (External): API 即時開立 / 作廢 / 折讓
  - POS 機: 批次取號 (商家自管未使用發票號碼)

聯繫: einvoice@paynow.com.tw

API 文件: https://docs.paynow.com.tw/developer/docs/invoice/
主站: https://gateway.paynow.com.tw/

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
class InvoiceIssueData:
    """PayNow 發票開立資料 (B2C / B2B 共用 — 以 BuyerIdentifier 區分)"""
    merchant_trade_no: str  # 商家訂單編號 (唯一)
    buyer_name: str
    buyer_identifier: str = ''  # B2C: 留空; B2B: 8 碼統編
    buyer_email: str = ''
    buyer_telephone: str = ''
    buyer_address: str = ''
    sales_amount: int = 0  # 銷售額 (B2C 含稅; B2B 未稅)
    tax_amount: int = 0  # 稅額 (B2B 必填)
    total_amount: int = 0  # 總額 (含稅)
    tax_type: Literal['1', '2', '3', '9'] = '1'  # 1=應稅 2=零稅率 3=免稅 9=混合
    inv_type: Literal['07', '08'] = '07'  # 07=一般 08=特種
    carrier_type: Optional[str] = ''  # 載具類型 (B2B 不可使用)
    carrier_num: str = ''
    donate_mark: Literal['0', '1'] = '0'  # 0=不捐贈, 1=捐贈
    love_code: str = ''
    print_flag: Literal['Y', 'N'] = 'N'  # B2B 強制 Y
    items: List[Dict[str, any]] = field(default_factory=list)
    remark: str = ''


@dataclass
class InvoiceIssueResponse:
    """PayNow 發票開立回應"""
    success: bool
    invoice_no: str = ''
    invoice_date: str = ''
    random_number: str = ''
    error_code: str = ''
    error_message: str = ''
    raw: Dict[str, any] = field(default_factory=dict)


# ============================================================================
# Service
# ============================================================================

class PayNowInvoiceService:
    """
    PayNow 立吉富電子發票服務 (preliminary).

    認證方式: JWT Bearer Token
        Authorization: Bearer <merchant-jwt-token>
        Content-Type:  application/json

    端點 (測試 dev / 正式 prod):
        - 開立發票       : /invoice/issue           (推測; 待官方確認)
        - 作廢發票       : /invoice/invalid
        - 開立折讓       : /invoice/allowance
        - 作廢折讓       : /invoice/allowance/invalid
        - POS 批次取號   : /invoice/pos/batch
        - (查詢 / 列印 / 載具驗證 / 對獎通知 endpoint 公開文件未列, 待索取)

    POS 流程特殊規則:
        未使用發票號碼會於次期單數月 5 號自動上傳空白發票
        (即 1, 3, 5, 7, 9, 11 月對應次期之 5 號)
    """

    SANDBOX_BASE = 'https://invoiceapi-dev.paynow.com.tw'
    PROD_BASE = 'https://invoiceapi-prod.paynow.com.tw'

    def __init__(self, jwt_token: str, is_test: bool = True):
        if not jwt_token:
            raise ValueError('PayNow 發票 API 需要 JWT Bearer Token; 請向 einvoice@paynow.com.tw 申請')
        self.jwt_token = jwt_token
        self.base_url = self.SANDBOX_BASE if is_test else self.PROD_BASE
        self.is_test = is_test

    @property
    def headers(self) -> Dict[str, str]:
        return {
            'Authorization': f'Bearer {self.jwt_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

    # -- Amount helpers -------------------------------------------------------

    def calculate_b2b_amounts(self, total_amount: int, tax_rate: float = 5.0) -> Dict[str, int]:
        tax_amount = round(total_amount - (total_amount / (1 + tax_rate / 100)))
        return {
            'sales_amount': total_amount - tax_amount,
            'tax_amount': tax_amount,
            'total_amount': total_amount,
        }

    # -- Operations -----------------------------------------------------------

    def issue_invoice(self, data: InvoiceIssueData) -> InvoiceIssueResponse:
        """開立電子發票 (一般串接 external 流程)"""
        is_b2b = bool(data.buyer_identifier and data.buyer_identifier != '0000000000')
        if is_b2b:
            if len(data.buyer_identifier) != 8 or not data.buyer_identifier.isdigit():
                raise ValueError('B2B 發票需要 8 碼數字統編')
            if data.tax_amount == 0:
                raise ValueError('B2B 發票必須計算稅額')
            if data.carrier_type or data.donate_mark == '1':
                raise ValueError('B2B 發票不可使用載具或捐贈')
            if data.print_flag != 'Y':
                data.print_flag = 'Y'  # B2B 強制列印

        body = {
            'MerchantTradeNo': data.merchant_trade_no,
            'BuyerName': data.buyer_name,
            'BuyerIdentifier': data.buyer_identifier or '0000000000',
            'BuyerEmail': data.buyer_email,
            'BuyerTelephone': data.buyer_telephone,
            'BuyerAddress': data.buyer_address,
            'SalesAmount': data.sales_amount,
            'TaxAmount': data.tax_amount,
            'TotalAmount': data.total_amount,
            'TaxType': data.tax_type,
            'InvType': data.inv_type,
            'CarrierType': data.carrier_type or '',
            'CarrierNum': data.carrier_num,
            'DonateMark': data.donate_mark,
            'LoveCode': data.love_code,
            'PrintFlag': data.print_flag,
            'Items': data.items,
            'ItemRemark': data.remark,
        }
        return self._submit('/invoice/issue', body)

    def void_invoice(self, invoice_no: str, invoice_date: str, reason: str) -> InvoiceIssueResponse:
        body = {
            'InvoiceNo': invoice_no,
            'InvoiceDate': invoice_date,
            'Reason': reason,
        }
        return self._submit('/invoice/invalid', body)

    def issue_allowance(
        self,
        invoice_no: str,
        invoice_date: str,
        allowance_amount: int,
        items: List[Dict[str, any]],
    ) -> InvoiceIssueResponse:
        body = {
            'InvoiceNo': invoice_no,
            'InvoiceDate': invoice_date,
            'AllowanceAmount': allowance_amount,
            'Items': items,
        }
        return self._submit('/invoice/allowance', body)

    def void_allowance(self, allowance_no: str, reason: str) -> InvoiceIssueResponse:
        body = {
            'AllowanceNo': allowance_no,
            'Reason': reason,
        }
        return self._submit('/invoice/allowance/invalid', body)

    def pos_batch_get_numbers(self, quantity: int) -> InvoiceIssueResponse:
        """
        POS 機批次取號.

        商家事先批次取得未使用之發票號碼, 後續由 POS 機自管 (含隨機碼)。
        未使用之號碼於次期單數月 5 號被 PayNow 自動上傳為空白發票。
        """
        if quantity <= 0:
            raise ValueError('quantity 必須大於 0')
        body = {'Quantity': quantity}
        return self._submit('/invoice/pos/batch', body)

    # -- HTTP submit ----------------------------------------------------------

    def _submit(self, path: str, body: Dict[str, any]) -> InvoiceIssueResponse:
        url = self.base_url + path
        try:
            r = requests.post(url, json=body, headers=self.headers, timeout=30)
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f'PayNow API 連線失敗: {e}')

        try:
            resp = r.json()
        except ValueError:
            return InvoiceIssueResponse(
                success=False,
                error_code=str(r.status_code),
                error_message=f'回應非 JSON: {r.text[:200]}',
            )

        # 推測之回傳格式 (待官方確認):
        # 成功:  { code: 0, data: { invoiceNo, invoiceDate, randomNumber, ... } }
        # 失敗:  { code: <非0>, message: '...', data: null }
        code = resp.get('code', resp.get('Code', resp.get('Status', '')))
        is_success = (str(code) in ('0', '00', 'SUCCESS')) and r.status_code < 400

        data = resp.get('data') or resp.get('Data') or {}
        return InvoiceIssueResponse(
            success=is_success,
            invoice_no=data.get('invoiceNo', data.get('InvoiceNo', '')),
            invoice_date=data.get('invoiceDate', data.get('InvoiceDate', '')),
            random_number=data.get('randomNumber', data.get('RandomNumber', '')),
            error_code=str(code) if not is_success else '',
            error_message=resp.get('message', resp.get('Message', '')),
            raw=resp,
        )


# ============================================================================
# Examples
# ============================================================================

def example_b2c():
    print('=== PayNow B2C 二聯式發票範例 (preliminary) ===\n')
    print('⚠️  端點與欄位有部分為推測, 串接前請向 PayNow 索取官方 PDF 確認\n')

    svc = PayNowInvoiceService(
        jwt_token='YOUR_JWT_TOKEN_HERE',  # 向 einvoice@paynow.com.tw 申請
        is_test=True,
    )

    data = InvoiceIssueData(
        merchant_trade_no=f'ORD{int(time.time())}',
        buyer_name='王小明',
        buyer_email='test@example.com',
        sales_amount=1050,
        total_amount=1050,
        carrier_type='3',  # 手機條碼
        carrier_num='/ABC1234',
        items=[
            {'ItemName': '測試商品A', 'ItemCount': 1, 'ItemPrice': 1050, 'ItemAmount': 1050, 'ItemUnit': '個'}
        ],
    )
    try:
        resp = svc.issue_invoice(data)
        if resp.success:
            print(f'[OK] 發票號碼: {resp.invoice_no}, 隨機碼: {resp.random_number}')
        else:
            print(f'[FAIL] code={resp.error_code} msg={resp.error_message}')
    except Exception as e:
        print(f'[ERROR] {e}')


def example_b2b():
    print('\n=== PayNow B2B 三聯式發票範例 (preliminary) ===\n')

    svc = PayNowInvoiceService(jwt_token='YOUR_JWT_TOKEN_HERE', is_test=True)
    amounts = svc.calculate_b2b_amounts(1050)
    data = InvoiceIssueData(
        merchant_trade_no=f'ORD{int(time.time())}',
        buyer_name='測試公司股份有限公司',
        buyer_identifier='80129529',
        buyer_address='台北市信義區',
        buyer_email='company@example.com',
        sales_amount=amounts['sales_amount'],
        tax_amount=amounts['tax_amount'],
        total_amount=amounts['total_amount'],
        print_flag='Y',
        items=[
            {'ItemName': '測試商品B', 'ItemCount': 1, 'ItemPrice': amounts['sales_amount'], 'ItemAmount': amounts['sales_amount'], 'ItemUnit': '個'}
        ],
    )
    try:
        resp = svc.issue_invoice(data)
        if resp.success:
            print(f'[OK] B2B 發票號碼: {resp.invoice_no}')
        else:
            print(f'[FAIL] {resp.error_code}: {resp.error_message}')
    except Exception as e:
        print(f'[ERROR] {e}')


def example_pos_batch():
    print('\n=== PayNow POS 批次取號範例 (preliminary) ===\n')
    print('注意: 未使用之發票號碼於次期單數月 5 號自動上傳為空白發票\n')

    svc = PayNowInvoiceService(jwt_token='YOUR_JWT_TOKEN_HERE', is_test=True)
    try:
        resp = svc.pos_batch_get_numbers(quantity=10)
        print(f'回應: {json.dumps(resp.raw, ensure_ascii=False, indent=2)}')
    except Exception as e:
        print(f'[ERROR] {e}')


if __name__ == '__main__':
    example_b2c()
    example_b2b()
    example_pos_batch()
