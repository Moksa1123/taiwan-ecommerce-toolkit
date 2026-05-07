#!/usr/bin/env python3
"""
PayNow 立吉富物流 Python 範例

依 taiwan-logistics-skill 規範撰寫。

⚠️ 加密: PayNow 物流使用 3DES (TripleDES) / ECB / Zero-Padding
   24-byte Key + 8-byte IV，**不同於金流端的動態 AES-256 (GP/GK)**

支援 11 條產品線:
- 7-11 大宗 (B2C) / 冷凍大宗 (B2C) / 冷凍 C2C / 海外配送
- 全家 大宗 (B2C) / 冷凍大宗 (B2C) / 冷凍 C2C
- 4 大超商常溫 C2C (7-11/全家/萊爾富/OK)
- 黑貓宅配 / 黑貓店到店

API 文件: 參見 references/paynow-logistics-api.md

依賴:
    pip install pycryptodome requests
"""

import json
import time
from dataclasses import dataclass, field
from typing import Dict, Literal, Optional

import requests
from Crypto.Cipher import DES3
from Crypto.Util.Padding import pad


@dataclass
class LogisticOrder:
    """PayNow 物流訂單"""
    service_id: str  # 物流商品線 ID（依產品線不同, 見下方常數）
    goods_name: str
    amount: int  # COD 金額
    sender_name: str
    sender_phone: str
    sender_address: str = ''
    receiver_name: str = ''
    receiver_phone: str = ''
    receiver_address: str = ''
    receiver_store_id: str = ''  # 取貨門市（CVS）
    return_url: str = ''  # 通知 URL
    is_cod: bool = True


@dataclass
class PayNowLogisticResponse:
    success: bool
    status: str = ''
    message: str = ''
    logistic_trade_no: str = ''
    raw: Dict[str, any] = field(default_factory=dict)


class PayNowLogisticService:
    """
    PayNow 物流服務.

    認證:
        - 商家代號 (merID) + 賣場交易密碼 (apicode)
        - 加密: 3DES / ECB / Zero-Padding
        - 24-byte Key + 8-byte IV (示範值, 真實值需向 PayNow 申請)

    11 條產品線 ServiceID（部分代碼）:
        20 = 7-11 大宗 B2C 常溫
        21 = 7-11 大宗 B2C 冷凍
        22 = 7-11 冷凍 C2C
        23 = 7-11 海外配送
        30 = 全家 大宗 B2C
        31 = 全家 冷凍大宗
        32 = 全家 冷凍 C2C
        40 = 4 大超商常溫 C2C (7-11/全家/萊爾富/OK)
        50 = 黑貓宅配
        51 = 黑貓店到店
        ...
    """

    TEST_BASE = 'https://test.paynow.com.tw'
    PROD_BASE = 'https://www.paynow.com.tw'

    # 官方範例金鑰（僅供加密邏輯測試使用）
    SAMPLE_KEY = '123456789070828783123456'  # 24 bytes
    SAMPLE_IV = '12345678'  # 8 bytes

    def __init__(self, mer_id: str, apicode: str, key_3des: str, iv_3des: str, is_test: bool = True):
        if len(key_3des) != 24:
            raise ValueError(f'PayNow 物流 3DES Key 必須 24 bytes (收到 {len(key_3des)})')
        if len(iv_3des) != 8:
            raise ValueError(f'PayNow 物流 3DES IV 必須 8 bytes (收到 {len(iv_3des)})')

        self.mer_id = mer_id
        self.apicode = apicode
        self.key = key_3des.encode('utf-8')
        self.iv = iv_3des.encode('utf-8')
        self.base_url = self.TEST_BASE if is_test else self.PROD_BASE

    # -- 3DES 加密 ------------------------------------------------------------

    def _encrypt_3des(self, plaintext: str) -> str:
        """
        3DES / ECB / Zero-Padding 加密.

        ⚠️ ECB 模式不使用 IV; PayNow 文件雖列 IV 但實際邏輯為 ECB。
        若實際串接時用 CBC, 則替換 mode=DES3.MODE_CBC 並附 IV。
        """
        # Zero-padding (補 \x00 至 8 byte 倍數)
        block_size = 8
        pad_len = block_size - (len(plaintext.encode('utf-8')) % block_size)
        if pad_len == block_size:
            pad_len = 0
        padded = plaintext.encode('utf-8') + b'\x00' * pad_len

        cipher = DES3.new(self.key, DES3.MODE_ECB)
        encrypted = cipher.encrypt(padded)
        return encrypted.hex().upper()

    # -- Operations -----------------------------------------------------------

    def create_logistic(self, order: LogisticOrder) -> PayNowLogisticResponse:
        """建立物流訂單"""
        # 組成欲加密的 query string
        body_dict = {
            'merID': self.mer_id,
            'LogisticServiceID': order.service_id,
            'GoodsName': order.goods_name,
            'Amount': str(order.amount) if order.is_cod else '0',
            'SenderName': order.sender_name,
            'SenderPhone': order.sender_phone,
            'SenderAddress': order.sender_address,
            'ReceiverName': order.receiver_name,
            'ReceiverPhone': order.receiver_phone,
            'ReceiverAddress': order.receiver_address,
            'ReceiverStoreID': order.receiver_store_id,
            'ReturnURL': order.return_url,
            'IsCOD': 'Y' if order.is_cod else 'N',
            'TimeStr': str(int(time.time())),
        }
        query = '&'.join(f'{k}={v}' for k, v in body_dict.items())
        encrypted = self._encrypt_3des(query)

        # POST 至 PayNow
        url = self.base_url + '/service/sevp_logistic.aspx'
        try:
            r = requests.post(
                url,
                data={
                    'merID': self.mer_id,
                    'EncStr': encrypted,
                    'apicode': self.apicode,
                },
                timeout=30,
            )
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f'PayNow API 連線失敗: {e}')

        # PayNow 物流回應通常為 form-data string 或簡易 JSON
        try:
            resp = r.json() if 'application/json' in r.headers.get('Content-Type', '') else self._parse_form(r.text)
        except (ValueError, AttributeError):
            return PayNowLogisticResponse(success=False, message=r.text[:200])

        status = str(resp.get('status', resp.get('Status', '')))
        return PayNowLogisticResponse(
            success=(status in ('1', 'SUCCESS', '0')),
            status=status,
            message=resp.get('message', resp.get('Message', '')),
            logistic_trade_no=resp.get('LogisticTradeNo', resp.get('logistic_trade_no', '')),
            raw=resp,
        )

    @staticmethod
    def _parse_form(text: str) -> Dict[str, any]:
        """簡易 form-data parser"""
        return {k: v for k, v in (kv.split('=', 1) for kv in text.split('&') if '=' in kv)}

    # -- Emap 選店 URL --------------------------------------------------------

    def get_emap_url(self, service_id: str, return_url: str) -> str:
        """取得電子地圖選店頁 URL"""
        return f'{self.base_url}/service/sevp_estore.aspx?merID={self.mer_id}&LogisticServiceID={service_id}&ReturnURL={return_url}'


# ============================================================================
# Examples
# ============================================================================

def example_711_b2c():
    print('=== PayNow 7-11 大宗 B2C 取貨付款 ===\n')
    svc = PayNowLogisticService(
        mer_id='YOUR_MER_ID',
        apicode='YOUR_APICODE',
        key_3des=PayNowLogisticService.SAMPLE_KEY,
        iv_3des=PayNowLogisticService.SAMPLE_IV,
        is_test=True,
    )
    order = LogisticOrder(
        service_id='20',  # 7-11 大宗 B2C 常溫
        goods_name='測試商品',
        amount=1500,
        sender_name='店家',
        sender_phone='0227000000',
        sender_address='台北市信義區信義路五段7號',
        receiver_name='王小明',
        receiver_phone='0912345678',
        receiver_store_id='123456',
        return_url='https://your-shop.com/api/paynow/notify',
        is_cod=True,
    )
    try:
        resp = svc.create_logistic(order)
        if resp.success:
            print(f'[OK] LogisticTradeNo={resp.logistic_trade_no}')
        else:
            print(f'[FAIL] {resp.status}: {resp.message}')
    except Exception as e:
        print(f'[ERROR] {e}')


def example_tcat_home():
    print('\n=== PayNow 黑貓宅配 ===\n')
    svc = PayNowLogisticService('YOUR_MER_ID', 'YOUR_APICODE',
                                 PayNowLogisticService.SAMPLE_KEY,
                                 PayNowLogisticService.SAMPLE_IV, is_test=True)
    order = LogisticOrder(
        service_id='50',  # 黑貓宅配
        goods_name='生鮮食品',
        amount=2000,
        sender_name='店家',
        sender_phone='0227000000',
        sender_address='台北市信義區',
        receiver_name='王小明',
        receiver_phone='0912345678',
        receiver_address='台北市大安區忠孝東路四段1號',
        return_url='https://your-shop.com/api/paynow/notify',
        is_cod=True,
    )
    try:
        resp = svc.create_logistic(order)
        if resp.success:
            print(f'[OK] LogisticTradeNo={resp.logistic_trade_no}')
        else:
            print(f'[FAIL] {resp.message}')
    except Exception as e:
        print(f'[ERROR] {e}')


def example_emap():
    print('\n=== PayNow 電子地圖選店 ===\n')
    svc = PayNowLogisticService('YOUR_MER_ID', 'YOUR_APICODE',
                                 PayNowLogisticService.SAMPLE_KEY,
                                 PayNowLogisticService.SAMPLE_IV, is_test=True)
    url = svc.get_emap_url(service_id='40', return_url='https://your-shop.com/checkout/store-selected')
    print(f'導轉至: {url}')


if __name__ == '__main__':
    example_711_b2c()
    example_tcat_home()
    example_emap()
