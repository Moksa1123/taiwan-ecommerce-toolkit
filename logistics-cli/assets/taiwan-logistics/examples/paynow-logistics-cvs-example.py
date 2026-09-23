#!/usr/bin/env python3
"""
PayNow 立吉富物流 Python 範例

依據：PayNow 物流技術文件（PayNow_Logistic_v2.5_C2C 等各產品線 PDF，本機 _studies 參考資料）
加密與 PassCode 已以文件附錄與「建立物流單」範例的密文驗證（tests/vectors/paynow.json）。

⚠️ 加密：3DES (TripleDES) / ECB / Zero-Padding，輸出 **Base64**
   Key = "1234567890" + Password + "123456"（24 bytes；Password 為 PayNow 核發的加密密碼，
   與 JSON 內的 apicode 是不同的值）

端點（測試 https://testlogistic.paynow.com.tw／正式 https://logistic.paynow.com.tw）：

| 用途 | 方法 | 路徑 |
|---|---|---|
| 選擇取貨門市（瀏覽器表單） | POST | /Member/Order/Choselogistics |
| 建立物流單 | POST form | /api/Orderapi/Add_Order |
| 依商家訂單編號查詢 | GET | /api/Orderapi/Get_Order_Info_orderno |
| 取消物流單 | DELETE form | /api/Orderapi/CancelOrder |
"""

import base64
import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Dict

try:
    from Crypto.Cipher import DES3
    import requests
    HAS_DEPENDENCIES = True
except ImportError:
    HAS_DEPENDENCIES = False


# Logistic_service（各產品線文件）
SERVICE_711_C2C = '01'            # 7-11 交貨便
SERVICE_711_BULK = '02'           # 7-11 大宗物流
SERVICE_FAMI_C2C = '03'           # 全家店到店
SERVICE_FAMI_BULK = '04'          # 全家大宗物流
SERVICE_HILIFE_C2C = '05'         # 萊爾富店到店
SERVICE_TCAT = '06'               # 黑貓宅急便
SERVICE_711_OVERSEAS_STORE = '07'  # 7-11 海外配送（店配）
SERVICE_711_OVERSEAS_HOME = '08'   # 7-11 海外配送（宅配）
SERVICE_OK_C2C = '10'             # OK 店到店
SERVICE_711_C2C_FROZEN = '21'     # 7-11 交貨便（冷凍）
SERVICE_711_BULK_FROZEN = '22'    # 7-11 大宗物流（冷凍）
SERVICE_FAMI_C2C_FROZEN = '23'    # 全家店到店（冷凍）
SERVICE_FAMI_BULK_FROZEN = '24'   # 全家大宗物流（冷凍）

DELIVER_MODE_COD = '01'           # 取貨付款
DELIVER_MODE_NO_COD = '02'        # 取貨不付款


@dataclass
class LogisticOrder:
    """建立物流單的 Obj_Order（欄位名稱與大小寫依文件）"""
    order_no: str                  # 限英文與數字
    logistic_service: str          # 見上方 SERVICE_* 常數
    deliver_mode: str              # 01 取貨付款 / 02 取貨不付款
    total_amount: int              # 正整數，不可大於 20000
    receiver_storeid: str
    receiver_storename: str
    receiver_name: str             # 勿帶標點；7-11 限 10 字
    receiver_phone: str
    receiver_email: str
    receiver_address: str          # 請輸入取件店址
    sender_name: str
    sender_phone: str
    sender_email: str
    sender_address: str = ''
    return_storeid: str = ''
    remark: str = ''
    description: str = ''


@dataclass
class PayNowLogisticResponse:
    success: bool
    status: str = ''
    error_msg: str = ''
    logistic_number: str = ''      # PayNow 物流單號
    paymentno: str = ''            # 物流商貨運編號
    validationno: str = ''         # 物流商驗證碼（7-11 店到店）
    raw: Dict[str, Any] = field(default_factory=dict)


class PayNowLogisticService:
    """PayNow 物流服務"""

    TEST_BASE = 'https://testlogistic.paynow.com.tw'
    PROD_BASE = 'https://logistic.paynow.com.tw'

    def __init__(self, user_account: str, apicode: str, password: str, is_test: bool = True):
        """
        Args:
            user_account: 商家主帳號
            apicode:      商家 API 密碼（放在 JSON 內、參與 PassCode）
            password:     3DES 加密用密碼（Key = "1234567890" + password + "123456"）
        """
        if not HAS_DEPENDENCIES:
            raise ImportError('需要安裝: pip install pycryptodome requests')
        key = f'1234567890{self.normalize_password(password)}123456'
        self.user_account = user_account
        self.apicode = apicode
        self.key = key.encode('utf-8')
        self.base_url = self.TEST_BASE if is_test else self.PROD_BASE

    @staticmethod
    def normalize_password(password: str) -> str:
        """
        密碼不足 8 碼時靠右補 0、超過 8 碼取前 8 碼

        規則載於 PayNow 電子發票串接文件 V1.5 附件一（同一套 TripleDESEncoding）；
        物流文件的範例密碼剛好 8 碼，未另外說明。
        """
        return password[:8].ljust(8, '0')

    # -- 加密 / 雜湊（文件附錄一、附錄二）--------------------------------------

    def encrypt_3des(self, plaintext: str) -> str:
        """3DES / ECB / Zero-Padding → Base64（文件附錄一）"""
        data = plaintext.encode('utf-8')
        data += b'\x00' * (-len(data) % 8)
        return base64.b64encode(DES3.new(self.key, DES3.MODE_ECB).encrypt(data)).decode('ascii')

    def decrypt_3des(self, b64: str) -> str:
        data = DES3.new(self.key, DES3.MODE_ECB).decrypt(base64.b64decode(b64))
        return data.rstrip(b'\x00').decode('utf-8')

    @staticmethod
    def sha1_upper(text: str) -> str:
        """文件附錄二：SHA-1 → 十六進位大寫"""
        return hashlib.sha1(text.encode('utf-8')).hexdigest().upper()

    def passcode(self, order_no: str, total_amount) -> str:
        """PassCode = SHA1(user_account + OrderNo + TotalAmount + apicode) 大寫"""
        return self.sha1_upper(f'{self.user_account}{order_no}{total_amount}{self.apicode}')

    # -- 業務 API ---------------------------------------------------------------

    def build_order_json(self, order: LogisticOrder) -> str:
        """組出 Obj_Order JSON（緊湊格式、中文不跳脫，與文件範例相同）"""
        total = str(order.total_amount)
        obj = {
            'user_account': self.user_account,
            'apicode': self.apicode,
            'Logistic_service': order.logistic_service,
            'OrderNo': order.order_no,
            'DeliverMode': order.deliver_mode,
            'TotalAmount': total,
            'Remark': order.remark,
            'Description': order.description,
            'receiver_storeid': order.receiver_storeid,
            'receiver_storename': order.receiver_storename,
            'return_storeid': order.return_storeid,
            'Receiver_Name': order.receiver_name,
            'Receiver_Phone': order.receiver_phone,
            'Receiver_Email': order.receiver_email,
            'Receiver_address': order.receiver_address,
            'Sender_Name': order.sender_name,
            'Sender_Phone': order.sender_phone,
            'Sender_Email': order.sender_email,
            'Sender_address': order.sender_address,
            'PassCode': self.passcode(order.order_no, total),
        }
        return json.dumps(obj, ensure_ascii=False, separators=(',', ':'))

    def create_order(self, order: LogisticOrder) -> PayNowLogisticResponse:
        """建立物流單：POST form JsonOrder = 3DES(Obj_Order JSON)（requests 會自動 urlencode）"""
        if not 0 < order.total_amount <= 20000:
            raise ValueError('TotalAmount 須為正整數且不可大於 20000')
        r = requests.post(f'{self.base_url}/api/Orderapi/Add_Order',
                          data={'JsonOrder': self.encrypt_3des(self.build_order_json(order))}, timeout=30)
        r.raise_for_status()
        resp = r.json()
        return PayNowLogisticResponse(
            success=resp.get('Status') == 'S',
            status=resp.get('Status', ''),
            error_msg=resp.get('ErrorMsg') or '',
            logistic_number=resp.get('LogisticNumber', ''),
            paymentno=resp.get('paymentno', ''),
            validationno=resp.get('validationno', ''),
            raw=resp,
        )

    def choose_store_form(self, logistic_service_id: str, return_url: str, order_no: str = '') -> Dict[str, Any]:
        """
        選擇取貨門市：由消費者瀏覽器以表單 POST（apicode 須 3DES 加密後傳送）

        選完後 PayNow POST 回 returnUrl：orderno、service、storeid、storename、storeaddress。
        """
        return {
            'action': f'{self.base_url}/Member/Order/Choselogistics',
            'fields': {
                'user_account': self.user_account,
                'orderno': order_no,
                'apicode': self.encrypt_3des(self.apicode),
                'Logistic_serviceID': logistic_service_id,
                'returnUrl': return_url,
            },
        }

    def query_by_order_no(self, order_no: str) -> Dict[str, Any]:
        """依商家訂單編號查詢（GET，sno 請帶 1）"""
        r = requests.get(f'{self.base_url}/api/Orderapi/Get_Order_Info_orderno',
                         params={'orderno': order_no, 'user_account': self.user_account, 'sno': 1}, timeout=30)
        r.raise_for_status()
        return r.json()

    def cancel_order(self, logistic_number: str, order_no: str, total_amount) -> str:
        """
        取消物流單（HTTP DELETE，form 編碼；全家店到店無法取消）

        回傳字串：「S,訂單已取消」或「F,訂單取消失敗 失敗原因: …」
        """
        r = requests.delete(f'{self.base_url}/api/Orderapi/CancelOrder',
                            data={'LogisticNumber': logistic_number, 'sno': 1,
                                  'PassCode': self.passcode(order_no, total_amount)},
                            timeout=30)
        r.raise_for_status()
        return r.text


if __name__ == '__main__':
    print('=== PayNow 7-11 交貨便（取貨不付款）===\n')
    if not HAS_DEPENDENCIES:
        print('需要安裝: pip install pycryptodome requests')
        raise SystemExit(1)

    svc = PayNowLogisticService('YOUR_ACCOUNT', 'YOUR_APICODE', '12345678', is_test=True)
    form = svc.choose_store_form(SERVICE_711_C2C, 'https://your-shop.com/paynow/store-selected')
    print(f'選店：POST {form["action"]}，欄位 {list(form["fields"])}')

    order = LogisticOrder(
        order_no='ORD20260923001', logistic_service=SERVICE_711_C2C, deliver_mode=DELIVER_MODE_NO_COD,
        total_amount=200, receiver_storeid='993041', receiver_storename='松高門市',
        receiver_name='王小明', receiver_phone='0912345678', receiver_email='buyer@example.com',
        receiver_address='台北市信義區基隆路一段141號1樓', sender_name='寄件人',
        sender_phone='0900000000', sender_email='shop@example.com', description='test',
    )
    print(f'建立物流單：POST {svc.base_url}/api/Orderapi/Add_Order，JsonOrder 長度 '
          f'{len(svc.encrypt_3des(svc.build_order_json(order)))}')
