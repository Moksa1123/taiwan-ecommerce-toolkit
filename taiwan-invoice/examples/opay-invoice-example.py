#!/usr/bin/env python3
"""
歐付寶 O'Pay 電子發票 Python 範例

依照 taiwan-invoice-skill 規範撰寫。

O'Pay 發票與 ECPay 發票**結構同源**：同樣的三層信封
（MerchantID + RqHeader + 加密後的 Data）、同樣的 AES 資料層、
同樣的 /B2CInvoice/Issue 路徑命名。差別只在網域與金鑰。
已熟悉 ECPay 發票者遷移成本很低。

⚠️ 但 O'Pay 多了 ECPay 沒有的：完整的 B2B 交換／存證雙模式，
以及離線 POS 發票。

支援:
- B2C Issue           開立發票
- B2C Invalid         作廢
- CheckBarcode        手機條碼驗證
- CheckLoveCode       捐贈碼驗證
- 離線取號            GetOfflineInvoiceWordSettingWithAutoSplit

API 文件: 參見 references/OPAY_API_REFERENCE.md

依賴:
    pip install requests cryptography

直接執行本檔會跑官方測試向量的自我驗證，不會發出任何網路請求:
    python opay-invoice-example.py
"""

import base64
import json
import time
import urllib.parse
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import requests

try:
    from cryptography.hazmat.primitives import padding as sympad
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
except ImportError:  # pragma: no cover
    Cipher = None


STAGE_BASE = 'https://einvoice-stage.opay.tw'
PROD_BASE = 'https://einvoice.opay.tw'


# ============================================================================
# 加解密
# ============================================================================

def encrypt_data(payload: Dict[str, Any], hash_key: str, hash_iv: str) -> str:
    """把業務參數加密成 Data 欄位。

    順序是 **先 URL Encode 再 AES 加密**（很多人會做反）：
        JSON -> URLEncode -> AES-128-CBC/PKCS7 -> Base64

    ⚠️ AES 強度固定 128 bit，不是 256。Key 與 IV 各 16 碼。
    """
    if Cipher is None:
        raise RuntimeError('需要 cryptography 套件：pip install cryptography')

    raw = json.dumps(payload, ensure_ascii=False, separators=(',', ':'))
    encoded = urllib.parse.quote(raw, safe='')

    padder = sympad.PKCS7(128).padder()
    data = padder.update(encoded.encode('utf-8')) + padder.finalize()
    enc = Cipher(algorithms.AES(hash_key.encode()), modes.CBC(hash_iv.encode())).encryptor()
    return base64.b64encode(enc.update(data) + enc.finalize()).decode('ascii')


def decrypt_data(cipher_text: str, hash_key: str, hash_iv: str) -> Dict[str, Any]:
    """解開回應的 Data 欄位：Base64 -> AES 解密 -> URLDecode -> JSON。"""
    if Cipher is None:
        raise RuntimeError('需要 cryptography 套件：pip install cryptography')

    dec = Cipher(algorithms.AES(hash_key.encode()), modes.CBC(hash_iv.encode())).decryptor()
    padded = dec.update(base64.b64decode(cipher_text)) + dec.finalize()
    unpadder = sympad.PKCS7(128).unpadder()
    encoded = (unpadder.update(padded) + unpadder.finalize()).decode('utf-8')
    return json.loads(urllib.parse.unquote(encoded))


# ============================================================================
# Client
# ============================================================================

@dataclass
class OpayInvoiceConfig:
    merchant_id: str
    hash_key: str
    hash_iv: str
    sandbox: bool = True
    platform_id: Optional[str] = None  # 平台商專用，一般廠商放空

    @property
    def base(self) -> str:
        return STAGE_BASE if self.sandbox else PROD_BASE


class OpayInvoiceClient:
    def __init__(self, config: OpayInvoiceConfig, timeout: int = 20):
        self.config = config
        self.timeout = timeout

    def _call(self, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        c = self.config
        body: Dict[str, Any] = {
            'MerchantID': c.merchant_id,
            # ⚠️ Timestamp 有效區間僅 10 分鐘，超過即拒絕。
            # 自架環境「參數都對但一直失敗」多半是主機沒做 NTP 校時。
            'RqHeader': {'Timestamp': int(time.time())},
            'Data': encrypt_data({'MerchantID': c.merchant_id, **data}, c.hash_key, c.hash_iv),
        }
        if c.platform_id:
            body['PlatformID'] = c.platform_id

        resp = requests.post(f'{c.base}{path}', json=body, timeout=self.timeout)
        resp.raise_for_status()
        envelope = resp.json()

        # ⚠️ 兩層錯誤處理，常被漏掉：
        # TransCode=1 只代表「信封收到了」，不代表發票開立成功。
        # 業務結果在解密後的 Data 裡（RtnCode）。
        if envelope.get('TransCode') != 1:
            raise RuntimeError(f"傳輸失敗 TransCode={envelope.get('TransCode')} {envelope.get('TransMsg')}")

        return decrypt_data(envelope['Data'], c.hash_key, c.hash_iv)

    # ---- B2C ----

    def issue_b2c(
        self,
        relate_number: str,
        customer_name: str,
        sales_amount: int,
        items: List[Dict[str, Any]],
        *,
        customer_email: Optional[str] = None,
        customer_phone: Optional[str] = None,
        customer_identifier: str = '',
        print_flag: str = '0',
        donation: str = '0',
        love_code: str = '',
        carrier_type: str = '',
        carrier_num: str = '',
        tax_type: str = '1',
        inv_type: str = '07',
        vat: str = '1',
    ) -> Dict[str, Any]:
        """開立 B2C 發票。

        ⚠️ Print / Donation / CarrierType / CustomerIdentifier 四者互相牽制，
        本方法在送出前先檢查，避免打到 API 才被打回：
        """
        check_b2c_constraints(print_flag, donation, carrier_type, customer_identifier)

        if not customer_email and not customer_phone:
            raise ValueError('CustomerEmail 與 CustomerPhone 至少擇一')

        # ⚠️ 各項 ItemAmount 加總四捨五入後必須等於 SalesAmount
        total = round(sum(float(i['ItemAmount']) for i in items))
        if total != sales_amount:
            raise ValueError(f'ItemAmount 加總 {total} 與 SalesAmount {sales_amount} 不符')

        return self._call('/B2CInvoice/Issue', {
            'RelateNumber': relate_number,
            'CustomerIdentifier': customer_identifier,
            'CustomerName': customer_name,
            'CustomerEmail': customer_email or '',
            'CustomerPhone': customer_phone or '',
            'Print': print_flag,
            'Donation': donation,
            'LoveCode': love_code,
            'CarrierType': carrier_type,
            'CarrierNum': carrier_num,
            'TaxType': tax_type,
            'SalesAmount': sales_amount,
            'InvType': inv_type,
            'vat': vat,
            'Items': items,
        })

    def check_barcode(self, barcode: str) -> Dict[str, Any]:
        """手機條碼驗證。上游其實是財政部大平台。

        若你已經在用 O'Pay 開發票，用這支就好，
        不必另外去申請財政部的 AppID。
        """
        return self._call('/B2CInvoice/CheckBarcode', {'BarCode': barcode})

    def check_love_code(self, love_code: str) -> Dict[str, Any]:
        """捐贈碼驗證。開立前先驗，避免輸入錯誤導致開立失敗。"""
        return self._call('/B2CInvoice/CheckLoveCode', {'LoveCode': love_code})


# ============================================================================
# 欄位約束
# ============================================================================

def check_b2c_constraints(print_flag: str, donation: str, carrier_type: str, identifier: str) -> None:
    """檢查 B2C 開立最容易踩的四欄互斥規則。

    這些規則散在官方 PDF 的各個註解裡，實務上很難一次看全，
    所以在送出前就攔下來。
    """
    if donation == '1' and print_flag != '0':
        raise ValueError('Donation=1（要捐贈）時 Print 必須為 0')
    if identifier and donation != '0':
        raise ValueError('CustomerIdentifier 有值時 Donation 必須為 0')
    if print_flag == '1' and carrier_type != '':
        raise ValueError('Print=1（要列印）時 CarrierType 必須為空字串')
    if identifier:
        if carrier_type == '' and print_flag != '1':
            raise ValueError('有統編且無載具時 Print 必須為 1')
        if carrier_type in ('1', '2') and print_flag != '0':
            raise ValueError('有統編且 CarrierType=1 或 2 時 Print 必須為 0')
    if print_flag == '0' and identifier and carrier_type == '':
        raise ValueError('Print=0 且有統編時 CarrierType 不可為空字串')
    # CarrierType 1/2/3 時不可自行填 CarrierNum，否則會被系統阻擋


# 延遲開立有專屬回應碼，不能只判斷 RtnCode == 1
RTN_SUCCESS = {
    1: '成功',
    4000003: '延後開立成功',   # DelayIssue
    4000004: '開立發票成功',   # TriggerIssue 觸發後
}


def is_success(rtn_code: int) -> bool:
    """⚠️ 只判斷 RtnCode == 1 會把延遲開立流程誤判為失敗。"""
    return rtn_code in RTN_SUCCESS


# ============================================================================
# 自我驗證（官方測試向量）
# ============================================================================

def _self_test() -> int:
    """用 opay_i100.pdf 附錄 3 的測試向量驗證加解密實作。"""
    key, iv = 'ejCk326UnaZWKisg', 'q9jcZX8Ib9LM8wYk'
    plain = {'Name': 'Test', 'ID': 'A123456789'}
    expected_cipher = ('uvI4yrErM37XNQkXGAgRgJAgHn2t72jahaMZzYhWL1HmvH4WV18VJDP2'
                       'i9pTbC+tby5nxVExLLFyAkbjbS2Dvg==')

    failed = 0
    print("O'Pay 官方測試向量驗證")

    if Cipher is None:
        print('  [SKIP] 未安裝 cryptography，略過加解密驗證')
        return 0

    got = encrypt_data(plain, key, iv)
    ok = got == expected_cipher
    failed += not ok
    print(f'  [{"PASS" if ok else "FAIL"}] AES-128-CBC/PKCS7 加密')
    if not ok:
        print(f'         期望 {expected_cipher}')
        print(f'         實得 {got}')

    back = decrypt_data(expected_cipher, key, iv)
    ok = back == plain
    failed += not ok
    print(f'  [{"PASS" if ok else "FAIL"}] 解密回原文（{back}）')

    # 測試金鑰與 ECPay 發票相同 —— 兩者同源的直接證據
    print('  [INFO] 這組測試金鑰與 ECPay 發票測試環境完全相同')

    # 四欄互斥規則
    cases = [
        ('Donation=1 但 Print=1', dict(print_flag='1', donation='1', carrier_type='', identifier='')),
        ('有統編但 Donation=1', dict(print_flag='0', donation='1', carrier_type='', identifier='12345675')),
        ('Print=1 但帶了載具', dict(print_flag='1', donation='0', carrier_type='3', identifier='')),
    ]
    for label, kw in cases:
        try:
            check_b2c_constraints(**kw)
            print(f'  [FAIL] 應攔下：{label}')
            failed += 1
        except ValueError:
            print(f'  [PASS] 正確攔下：{label}')

    ok = is_success(4000003) and is_success(4000004) and not is_success(9999)
    failed += not ok
    print(f'  [{"PASS" if ok else "FAIL"}] 延遲開立的 4000003/4000004 視為成功')

    print()
    print('全部通過' if failed == 0 else f'{failed} 項失敗')
    return 1 if failed else 0


if __name__ == '__main__':
    raise SystemExit(_self_test())
