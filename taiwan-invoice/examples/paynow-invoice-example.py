#!/usr/bin/env python3
"""
立吉富 PayNow 電子發票（REST）範例

依官方文件 https://docs.paynow.com.tw/developer/docs/invoice/ ：
    測試 https://invoiceapi-dev.paynow.com.tw ／ 正式 https://invoiceapi-prod.paynow.com.tw
    Authorization: Bearer <商家 JWT-Token>，JSON 主體

| 功能 | 路徑 |
|---|---|
| 單張發票開立 | POST /api/invoices/issue |
| 發票作廢 | POST /api/invoices/cancel |
| 發票折讓 | POST /api/invoices/allowance |
| 折讓作廢 | POST /api/invoices/cancel-allowance |
| 取得發票資料 | GET /api/invoices |
| POS 機取得發票號碼 | POST /api/invoices/pos/invoice-numbers |
| POS 機發票開立 | POST /api/invoices/pos/issue |

回應為 { status, type, message, result, request_id }；官方未公開錯誤代碼表。

依賴: pip install requests
"""

import time
from typing import Any, Dict, List, Literal, Optional

import requests

CarrierType = Literal['None', 'PhoneBarCodeCarrier', 'EasyCardCarrier', 'CitizenDigitalCardNo', 'BuyerSno']
TaxType = Literal['SaleTax', 'ZeroTax', 'FreeTax', 'MixTax']


def item(description: str, quantity: int, unit_price: int, tax_type: TaxType = 'SaleTax',
         tax_amount: int = 0) -> Dict[str, Any]:
    return {'quantity': quantity, 'unit_price': unit_price, 'amount': quantity * unit_price,
            'tax_type': tax_type, 'tax_amount': tax_amount, 'description': description}


class PayNowInvoiceService:
    SANDBOX_BASE = 'https://invoiceapi-dev.paynow.com.tw'
    PROD_BASE = 'https://invoiceapi-prod.paynow.com.tw'

    def __init__(self, jwt_token: str, is_test: bool = True, timeout: int = 30):
        if not jwt_token:
            raise ValueError('需要商家 JWT-Token')
        self.base_url = self.SANDBOX_BASE if is_test else self.PROD_BASE
        self.headers = {'Authorization': f'Bearer {jwt_token}', 'Content-Type': 'application/json'}
        self.timeout = timeout

    def _request(self, method: str, path: str, body: Optional[Dict[str, Any]] = None,
                 params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        r = requests.request(method, self.base_url + path, json=body, params=params,
                             headers=self.headers, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def issue(self, order_no: str, items: List[Dict[str, Any]], buyer: Dict[str, str],
              carrier_type: CarrierType = 'None', carrier_id: str = '', npoban: str = '',
              tax_type: TaxType = 'SaleTax', tax_amount: int = 0, main_remark: str = '',
              send_paper: bool = False, send_sms: bool = False,
              is_pass_customs: Optional[bool] = None, zero_tax_rate_reason: str = 'None') -> Dict[str, Any]:
        """
        單張發票開立。

        buyer：name、identifier（統編）、address、phone、email。
        tax_amount：非統編發票帶 0（由國稅局算稅），統編發票帶稅額。
        carrier_id：PhoneBarCodeCarrier／EasyCardCarrier／CitizenDigitalCardNo 的明碼（隱碼同值）；BuyerSno、None 留空。
        """
        if tax_type == 'ZeroTax' and is_pass_customs is None:
            raise ValueError('零稅率發票必須帶 is_pass_customs')
        body = {
            'order_no': order_no, 'send_paper': send_paper, 'send_sms': send_sms,
            'carrier_type': carrier_type, 'carrier_id1': carrier_id, 'carrier_id2': carrier_id,
            'npoban': npoban, 'total_amount': sum(i['amount'] for i in items),
            'tax_amount': tax_amount, 'tax_type': tax_type, 'main_remark': main_remark,
            'is_pass_customs': is_pass_customs, 'zero_tax_rate_reason': zero_tax_rate_reason,
            'buyer': buyer, 'items': items,
        }
        return self._request('POST', '/api/invoices/issue', body)

    def cancel(self, invoice_number: str) -> Dict[str, Any]:
        return self._request('POST', '/api/invoices/cancel', {'invoice_number': invoice_number})

    def allowance(self, invoice_number: str, items: List[Dict[str, Any]], remark: str = '') -> Dict[str, Any]:
        """items：quantity、unit_price、amount、tax、tax_type、invoice_body_sequence_number"""
        return self._request('POST', '/api/invoices/allowance',
                             {'invoice_number': invoice_number, 'remark': remark, 'items': items})

    def cancel_allowance(self, allowance_number: str) -> Dict[str, Any]:
        return self._request('POST', '/api/invoices/cancel-allowance', {'allowance_number': allowance_number})

    def query(self, invoice_number: str = '', order_no: str = '', page: int = 1, limit: int = 20) -> Dict[str, Any]:
        params = {'InvoiceNumber': invoice_number, 'OrderNo': order_no, 'Page': page, 'Limit': limit}
        return self._request('GET', '/api/invoices', params={k: v for k, v in params.items() if v})

    def pos_invoice_numbers(self, quantity: int, uuid: str) -> Dict[str, Any]:
        """取得的號碼由商家自行管理；未使用者於次期單數月 5 號上傳空白發票"""
        return self._request('POST', '/api/invoices/pos/invoice-numbers', {'quantity': quantity, 'uuid': uuid})


if __name__ == '__main__':
    svc = PayNowInvoiceService('YOUR_JWT_TOKEN')
    body_items = [item('商品A', 1, 1050)]
    print('POST', svc.base_url + '/api/invoices/issue')
    print({'order_no': f'ORD{int(time.time())}', 'items': body_items, 'carrier_type': 'PhoneBarCodeCarrier'})
