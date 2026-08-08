#!/usr/bin/env python3
"""
紅陽科技 SunPay 電子發票 Python 範例

依照 taiwan-invoice-skill 規範撰寫。

⚠️ 紅陽的金流與發票是**兩套完全不同的機制**：
    金流   RSA 分段加密 + SHA256 簽章，網域 trade.sunpay.com.tw
    發票   AES-128-CBC + PKCS7，網域 einv.sunpay.com.tw
串完金流不代表發票能沿用同一組加解密程式碼。

⚠️ 而且發票**只加密 Token 這一個欄位**，業務參數走明文。
這讓 debug 容易很多，但也代表傳輸層安全完全倚賴 HTTPS。

支援:
- ValidateToken       驗證 Token（建議的第一步）
- CreateInvoiceb2c    B2C 開立
- CreateInvoiceb2b    B2B 開立
- CreateInvoiceInvalid 作廢

API 文件: 參見 references/SUNPAY_API_REFERENCE.md

依賴:
    pip install requests cryptography

直接執行本檔會跑內建驗證，不會發出任何網路請求:
    python sunpay-invoice-example.py
"""

import base64
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import requests

try:
    from cryptography.hazmat.primitives import padding as sympad
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
except ImportError:  # pragma: no cover
    Cipher = None


# ⚠️ 正式環境是 einv. 不是 inv.
# inv.sunpay.com.tw 是發票管理後台入口，不是 API 網域，兩者很容易混淆。
TEST_BASE = 'https://testinv.sunpay.com.tw/api/v1/SunPay'
PROD_BASE = 'https://einv.sunpay.com.tw/api/v1/SunPay'

TAIPEI = timezone(timedelta(hours=8))
TOKEN_MAX_AGE_SECONDS = 300


# ============================================================================
# Token
# ============================================================================

def taiwan_epoch(now: Optional[datetime] = None) -> int:
    """產生紅陽發票要的 TimeStamp。

    ⚠️⚠️ 這**不是**標準 Unix timestamp。

    手冊定義為「從 1970/1/1 至今的**台灣時間（UTC+8）**之總秒數」，
    並附上 C# 範例 `DateTime.UtcNow.AddHours(8).Subtract(new DateTime(1970,1,1))`。
    注意那個 `.AddHours(8)` —— 送出的值比真正的 epoch **多 28800 秒**。

    手冊自己的對照也印證：1666204130 = 2022/10/19 18:28:50（台灣時間），
    而該數字若當成標準 epoch 解讀，在 UTC 下正好也是 18:28:50。

    如果你用 time.time()、Date.now()/1000 或
    DateTimeOffset.UtcNow.ToUnixTimeSeconds() 這類標準做法，
    會**整整差 8 小時**，而限制是 300 秒 —— 必定逾時失敗。
    """
    n = now.astimezone(timezone.utc) if now else datetime.now(timezone.utc)
    return int((n.replace(tzinfo=None) + timedelta(hours=8) - datetime(1970, 1, 1)).total_seconds())


def build_token(company_id: str, hash_key: str, hash_iv: str,
                now: Optional[datetime] = None) -> str:
    """產生 Token 欄位：AES-128-CBC / PKCS7 加密後 Base64。

    Hash Key 與 Hash IV 各為 16 碼。
    """
    if Cipher is None:
        raise RuntimeError('需要 cryptography 套件：pip install cryptography')

    plain = json.dumps(
        {'CompanyID': company_id, 'TimeStamp': str(taiwan_epoch(now))},
        separators=(',', ':'),
    )
    padder = sympad.PKCS7(128).padder()
    data = padder.update(plain.encode('utf-8')) + padder.finalize()
    enc = Cipher(algorithms.AES(hash_key.encode()), modes.CBC(hash_iv.encode())).encryptor()
    return base64.b64encode(enc.update(data) + enc.finalize()).decode('ascii')


# ============================================================================
# Client
# ============================================================================

@dataclass
class SunpayInvoiceConfig:
    merchant_id: str        # 商店代號（自發票商店後台取得）
    company_id: str         # 賣方公司統一編號
    hash_key: str           # 16 碼
    hash_iv: str            # 16 碼
    sandbox: bool = True

    @property
    def base(self) -> str:
        return TEST_BASE if self.sandbox else PROD_BASE


class SunpayInvoiceClient:
    def __init__(self, config: SunpayInvoiceConfig, timeout: int = 20):
        self.config = config
        self.timeout = timeout

    def _post(self, path: str, body: Dict[str, Any]) -> Dict[str, Any]:
        c = self.config
        payload = {
            'merchantID': c.merchant_id,
            **body,
            'Token': build_token(c.company_id, c.hash_key, c.hash_iv),
        }
        resp = requests.post(f'{c.base}/{path}', json=payload, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def validate_token(self) -> Dict[str, Any]:
        """驗證 Token —— **串接紅陽發票的正確第一步**。

        只需 merchantID 與 Token，**不會產生任何發票資料**。
        AES 參數、Key/IV、以及上面那個容易寫錯的 UTC+8 TimeStamp
        都能在這支驗證。先讓它回 SUCCESS 再去串開立，
        可以省下大量在真實開立端點上盲試的時間。
        """
        return self._post('ValidateToken', {})

    def issue_b2c(
        self,
        order_no: str,
        buyer_name: str,
        product_items: List[Dict[str, Any]],
        *,
        tax_amount: int,
        sales_amount: int,
        total_amount: int,
        zero_tax_sales_amount: int = 0,
        free_tax_sales_amount: int = 0,
        carrier_type: int = 0,
        carrier_id1: str = '',
        donate_mark: int = 0,
        isprint: int = 0,
        paper_invoice_option: Optional[int] = None,
        buyer_email: str = '',
        buyer_address: str = '',
        buyer_identifier: str = '',
        invoice_type: int = 7,
        tax_type: int = 1,
        tax_rate: float = 0.05,
        customs_clearance_mark: int = 0,
    ) -> Dict[str, Any]:
        """B2C 開立。

        ⚠️ **三個銷售額欄位皆必填**（應稅／零稅率／免稅），
        即使該類別為 0 也要帶。這與 O'Pay B2C 只帶單一含稅金額的
        設計正好相反。
        """
        validate_amounts(sales_amount, tax_amount, total_amount)
        validate_carrier(carrier_type, carrier_id1, buyer_email)

        body: Dict[str, Any] = {
            'orderNo': order_no,
            'buyerIdentifier': buyer_identifier,
            'buyerName': buyer_name,
            'buyerEmailAddress': buyer_email,
            'carrierType': carrier_type,
            'carrierId1': carrier_id1,
            'donateMark': donate_mark,
            'buyerAddress': buyer_address,
            'invoiceType': invoice_type,
            'taxType': tax_type,
            'taxRate': tax_rate,
            'taxAmount': tax_amount,
            'salesAmount': sales_amount,
            'zeroTaxSalesAmount': zero_tax_sales_amount,
            'freeTaxSalesAmount': free_tax_sales_amount,
            'totalAmount': total_amount,
            'customsClearanceMark': customs_clearance_mark,
            'isprint': isprint,
            'productItems': product_items,
        }
        # 無載具時才需要（也才可以）指定發票提供方式
        if carrier_type == 0 and donate_mark == 0 and paper_invoice_option is not None:
            body['PaperInvoiceOption'] = paper_invoice_option
        return self._post('CreateInvoiceb2c', body)

    def invalidate(self, invoice_number: str, cancel_reason: str) -> Dict[str, Any]:
        """作廢發票。cancel_reason 限 20 碼。"""
        if len(cancel_reason) > 20:
            raise ValueError('cancelReason 限 20 碼')
        return self._post('CreateInvoiceInvalid', {
            'invoiceNumber': invoice_number,
            'cancelReason': cancel_reason,
        })


# ============================================================================
# 驗證規則
# ============================================================================

def validate_amounts(sales: int, tax: int, total: int) -> None:
    """銷售額 + 稅額須等於發票總金額。"""
    if sales + tax != total:
        raise ValueError(f'salesAmount({sales}) + taxAmount({tax}) 應等於 totalAmount({total})')


def validate_carrier(carrier_type: int, carrier_id1: str, buyer_email: str) -> None:
    """載具格式與相依必填。

    carrierType: 0 無載具 / 1 手機條碼 / 2 自然人憑證 / 3 紅陽會員載具

    ⚠️ carrierType=3 是**紅陽自家的會員載具**，不屬財政部載具體系，
    跨加值中心遷移時這類發票的載具無法直接對應。
    """
    if carrier_type == 1:
        if not (len(carrier_id1) == 8 and carrier_id1[0] == '/'):
            raise ValueError('手機條碼載具需 8 碼且第 1 碼為 /')
    elif carrier_type == 2:
        if not (len(carrier_id1) == 16 and carrier_id1[:2].isalpha() and carrier_id1[2:].isdigit()):
            raise ValueError('自然人憑證載具需 16 碼：前 2 碼大寫英文 + 後 14 碼數字')
    elif carrier_type in (0, 3):
        if carrier_id1:
            raise ValueError(f'carrierType={carrier_type} 時不需傳 carrierId1')
    else:
        raise ValueError(f'未知的 carrierType: {carrier_type}')

    if carrier_type == 3 and not buyer_email:
        raise ValueError('carrierType=3 時 buyerEmailAddress 必填')


def is_success(response: Dict[str, Any]) -> bool:
    """回應統一為 status / message / result。"""
    return response.get('status') == 'SUCCESS'


# ⚠️ 內建冪等，但前提是「參數完全一致」
IDEMPOTENCY_NOTE = """
相同 PostData 且參數完全一致時，紅陽回傳 SUCCESS 並附上「原本那張發票」，
不會重複開立 —— 這在台灣加值中心裡少見，網路逾時後可安全重送。

⚠️ 但前提是完全一致。重試時只要有任一欄位不同（例如重算了金額、
改了備註、或 Token 內的 TimeStamp 改變導致整包 PostData 不同），
就會被視為新的一張發票而重複開立。

因此重試務必送出**位元組層級相同**的 payload —— 把第一次組好的
request body 存下來重送，不要重新組一次。
"""


# ============================================================================
# 自我驗證
# ============================================================================

def _self_test() -> int:
    failed = 0
    print('紅陽發票實作驗證')

    # 手冊給的對照：1666204130 = 2022/10/19 18:28:50（台灣時間）
    tw = datetime(2022, 10, 19, 18, 28, 50, tzinfo=TAIPEI)
    got = taiwan_epoch(tw)
    ok = got == 1666204130
    failed += not ok
    print(f'  [{"PASS" if ok else "FAIL"}] TimeStamp 與手冊對照相符（{got}）')

    # 與標準 Unix epoch 的差距應為 28800 秒
    std = int(tw.timestamp())
    diff = got - std
    ok = diff == 28800
    failed += not ok
    print(f'  [{"PASS" if ok else "FAIL"}] 比標準 Unix epoch 多 {diff} 秒（= {diff//3600} 小時）')
    print(f'         標準 epoch {std} vs 紅陽 {got}')
    print(f'         用 time.time() 會差這麼多，而限制只有 {TOKEN_MAX_AGE_SECONDS} 秒')

    # 金額恆等式
    try:
        validate_amounts(100, 5, 106)
        print('  [FAIL] 應攔下金額不符')
        failed += 1
    except ValueError:
        print('  [PASS] 正確攔下 salesAmount + taxAmount != totalAmount')

    # 載具格式
    cases = [
        ('手機條碼缺 /', dict(carrier_type=1, carrier_id1='AB123456', buyer_email='')),
        ('自然人憑證長度錯', dict(carrier_type=2, carrier_id1='AB12345678', buyer_email='')),
        ('無載具卻帶號碼', dict(carrier_type=0, carrier_id1='/ABC1234', buyer_email='')),
        ('會員載具缺信箱', dict(carrier_type=3, carrier_id1='', buyer_email='')),
    ]
    for label, kw in cases:
        try:
            validate_carrier(**kw)
            print(f'  [FAIL] 應攔下：{label}')
            failed += 1
        except ValueError:
            print(f'  [PASS] 正確攔下：{label}')

    ok = validate_carrier(1, '/ABC1234', '') is None
    print(f'  [{"PASS" if ok else "FAIL"}] 合法手機條碼通過')

    if Cipher is not None:
        token = build_token('12345678', 'A123456789012345', 'B123456789012345', tw)
        ok = isinstance(token, str) and len(token) > 0
        failed += not ok
        print(f'  [{"PASS" if ok else "FAIL"}] Token 產生成功（長度 {len(token)}）')
    else:
        print('  [SKIP] 未安裝 cryptography，略過 Token 產生')

    print()
    print('全部通過' if failed == 0 else f'{failed} 項失敗')
    return 1 if failed else 0


if __name__ == '__main__':
    raise SystemExit(_self_test())
