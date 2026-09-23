#!/usr/bin/env python3
"""
PAYUNi 統一物流 Python 完整範例

支援: 7-11 店到店（C2C，常溫/冷凍）、7-11 大宗寄倉（B2C）、黑貓宅配（常溫/冷凍/冷藏）

依據（皆已對照原始碼）:
- 加解密：統一金流官方外掛 PAYUNi_for_WooCommerce 1.2.8 與官方 PHP SDK（payuni/PHP_SDK）
- 端點、欄位、版本、通知格式：wpbr-payuni-shipping 1.6.4（WordPress.org 上架的正式外掛）
  src/Api/ShippingRequest.php、ShippingResponse.php、Frontend/StoreSelector.php

端點一覽（皆為 POST，外層欄位 MerID / Version / EncryptInfo / HashInfo）:

| 用途 | 路徑 | Version |
|---|---|---|
| 建立 7-11 物流單 | /api/logistics/trade | 1.1 |
| 建立黑貓物流單 | /api/home_delivery/trade | 1.1 |
| 查詢物流單 | /api/logistics/query | 1.1 |
| 7-11 門市地圖（瀏覽器表單） | /api/logistics/ship_map | 1.1 |
| 列印 7-11 託運單（瀏覽器表單） | /api/logistics/print_label | 1.0 |
| 黑貓託運單號 PDF（瀏覽器表單） | /api/home_delivery/get_obt_number_pdf | — |

API 文件: https://docs.payuni.com.tw/web/
"""

import base64
import hashlib
import hmac
import json
import time
import urllib.parse
from dataclasses import dataclass, field
from typing import Any, Dict, Literal, Optional

try:
    from Crypto.Cipher import AES
    import requests
    HAS_DEPENDENCIES = True
except ImportError:
    HAS_DEPENDENCIES = False


# 代碼定義（同 wpbr-payuni-shipping src/Utils/*.php）
SHIP_TYPE_SEVEN = '1'       # 7-ELEVEN
SHIP_TYPE_TCAT = '2'        # 黑貓
GOODS_TYPE_NORMAL = '1'     # 常溫
GOODS_TYPE_FROZEN = '2'     # 冷凍
GOODS_TYPE_COLD = '3'       # 冷藏（僅黑貓）
SERVICE_TYPE_COD = '1'      # 取貨付款
SERVICE_TYPE_NOT_COD = '3'  # 取貨不付款


@dataclass
class ShipmentData:
    """
    物流訂單資料（對應 build_request_args 的 trade 欄位）

    ship_type 決定走 7-11（/logistics/trade）或黑貓（/home_delivery/trade）。
    """
    mer_trade_no: str
    ship_type: Literal['1', '2']
    lgs_type: Literal['C2C', 'B2C', 'HOME']
    goods_type: Literal['1', '2', '3']
    trade_amt: int                       # 取貨付款＝代收金額；取貨不付款＝報值金額（外掛限制 30–20000）
    consignee: str
    consignee_mobile: str
    consignee_mail: str
    sender_name: str
    sender_mobile: str
    notify_url: str
    service_type: Literal['1', '3'] = SERVICE_TYPE_NOT_COD
    store_id: str = ''                   # 7-11 取貨門市（由門市地圖取得）
    refund_store_id: str = ''
    consignee_address: str = ''          # 黑貓必填
    prod_desc: str = ''                  # 黑貓必填，外掛截斷為 20 字
    delivery_time_tag: str = ''          # 黑貓配達時段


@dataclass
class ShipmentResponse:
    """建立物流單結果（EncryptInfo 解密後內容）"""
    success: bool
    status: str
    message: str
    ship_trade_no: Optional[str] = None  # UNi 物流序號，後續查詢 / 列印 / 通知都以它對應
    trade_amt: Optional[str] = None
    service_type: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)


class PAYUNiLogistics:
    """PAYUNi 統一物流服務"""

    TEST_API_URL = 'https://sandbox-api.payuni.com.tw/api'
    PROD_API_URL = 'https://api.payuni.com.tw/api'

    def __init__(self, mer_id: str, hash_key: str, hash_iv: str, is_production: bool = False):
        if not HAS_DEPENDENCIES:
            raise ImportError('需要安裝必要套件: pip install pycryptodome requests')

        self.mer_id = mer_id
        self.hash_key = hash_key.encode('utf-8')
        self.hash_iv = hash_iv.encode('utf-8')
        self.base_url = self.PROD_API_URL if is_production else self.TEST_API_URL

    # ------------------------------------------------------------------
    # 加解密（與官方外掛 / SDK 逐位元組相同）
    # ------------------------------------------------------------------

    def encrypt_data(self, data: Dict[str, Any]) -> str:
        """EncryptInfo = hex( base64(AES-256-GCM 密文) + ":::" + base64(tag) )"""
        query_string = urllib.parse.urlencode(data)
        cipher = AES.new(self.hash_key, AES.MODE_GCM, nonce=self.hash_iv)
        encrypted, tag = cipher.encrypt_and_digest(query_string.encode('utf-8'))
        return (base64.b64encode(encrypted) + b':::' + base64.b64encode(tag)).hex()

    def decrypt_data(self, encrypted_data: str) -> Dict[str, Any]:
        """解密 EncryptInfo；tag 驗證失敗（資料遭竄改 / 金鑰錯誤）時拋出 ValueError"""
        try:
            raw = bytes.fromhex(encrypted_data.strip())
            if b':::' not in raw:
                raise ValueError('格式錯誤: hex 解碼後缺少 ":::" 分隔符')
            encrypted_b64, tag_b64 = raw.split(b':::', 1)

            decipher = AES.new(self.hash_key, AES.MODE_GCM, nonce=self.hash_iv)
            decrypted = decipher.decrypt_and_verify(
                base64.b64decode(encrypted_b64), base64.b64decode(tag_b64))

            params = urllib.parse.parse_qs(decrypted.decode('utf-8'), keep_blank_values=True)
            return {k: v[0] if len(v) == 1 else v for k, v in params.items()}
        except Exception as e:
            raise ValueError(f'解密失敗: {str(e)}')

    def generate_hash_info(self, encrypt_info: str) -> str:
        """HashInfo = SHA256( HashKey + EncryptInfo + HashIV ) 轉大寫"""
        raw = self.hash_key.decode('utf-8') + encrypt_info + self.hash_iv.decode('utf-8')
        return hashlib.sha256(raw.encode('utf-8')).hexdigest().upper()

    def verify_hash_info(self, encrypt_info: str, hash_info: str) -> bool:
        """驗證 HashInfo（常數時間比較）"""
        return hmac.compare_digest(self.generate_hash_info(encrypt_info), hash_info.upper())

    def _envelope(self, data: Dict[str, Any], version: str) -> Dict[str, str]:
        encrypt_info = self.encrypt_data(data)
        return {
            'MerID': self.mer_id,
            'Version': version,
            'EncryptInfo': encrypt_info,
            'HashInfo': self.generate_hash_info(encrypt_info),
        }

    def _post(self, path: str, data: Dict[str, Any], version: str = '1.1') -> Dict[str, Any]:
        """伺服器對伺服器呼叫；回傳解密後的 EncryptInfo（先驗 HashInfo）"""
        response = requests.post(f'{self.base_url}{path}', data=self._envelope(data, version), timeout=45)
        response.raise_for_status()
        result = response.json()

        encrypt_info = result.get('EncryptInfo', '')
        if not encrypt_info:
            # 外層錯誤（例如 API00003 無 API 版本號）不會有 EncryptInfo
            return {'Status': result.get('Status', 'ERROR'), 'Message': result.get('Message', ''), 'raw': result}
        if not self.verify_hash_info(encrypt_info, result.get('HashInfo', '')):
            raise ValueError('HashInfo 驗證失敗')
        return self.decrypt_data(encrypt_info)

    # ------------------------------------------------------------------
    # 業務 API
    # ------------------------------------------------------------------

    def build_shipment_payload(self, data: ShipmentData) -> Dict[str, Any]:
        """組出建立物流單的 EncryptInfo 內容（欄位同官方外掛 build_request_args）"""
        payload = {
            'MerID': self.mer_id,
            'Timestamp': int(time.time()),
            'MerTradeNo': data.mer_trade_no,
            'GoodsType': data.goods_type,
            'LgsType': data.lgs_type,
            'ShipType': data.ship_type,
            'TradeAmt': data.trade_amt,
            'ServiceType': data.service_type,
            'StoreID': data.store_id,
            'Consignee': data.consignee,
            'ConsigneeMail': data.consignee_mail,
            'ConsigneeMobile': data.consignee_mobile,
            'RefundStoreID': data.refund_store_id,
            'SenderName': data.sender_name,
            'SenderMobile': data.sender_mobile,
            'NotifyURL': data.notify_url,
        }
        if data.ship_type == SHIP_TYPE_TCAT:
            if not (data.consignee_address and data.prod_desc):
                raise ValueError('黑貓宅配需要 ConsigneeAddress 與 ProdDesc')
            payload.update({
                'StoreID': '',
                'DeliveryTimeTag': data.delivery_time_tag,
                'ConsigneeAddress': data.consignee_address,
                'ProdDesc': data.prod_desc[:20],
            })
        elif not data.store_id:
            raise ValueError('7-11 取貨需要 StoreID（由門市地圖取得）')
        return payload

    def create_shipment(self, data: ShipmentData) -> ShipmentResponse:
        """建立物流單：7-11 走 /logistics/trade，黑貓走 /home_delivery/trade"""
        path = '/home_delivery/trade' if data.ship_type == SHIP_TYPE_TCAT else '/logistics/trade'
        decrypted = self._post(path, self.build_shipment_payload(data))
        return ShipmentResponse(
            success=decrypted.get('Status') == 'SUCCESS',
            status=decrypted.get('Status', ''),
            message=decrypted.get('Message', ''),
            ship_trade_no=decrypted.get('ShipTradeNo'),
            trade_amt=decrypted.get('TradeAmt'),
            service_type=decrypted.get('ServiceType'),
            raw=decrypted,
        )

    def query_shipment(self, lgs_type: str, ship_trade_no: str) -> Dict[str, Any]:
        """
        查詢物流單（/logistics/query，7-11 與黑貓共用）

        回傳欄位包含 ShipTradeNo、Odno（出貨編號 / 託運單號）、PartnerId、ValidationNo（C2C）、
        ShipStatus、ShipStatusDesc、ShipStatusTime、FileNo（黑貓）等。
        """
        return self._post('/logistics/query', {
            'MerID': self.mer_id,
            'Timestamp': int(time.time()),
            'LgsType': lgs_type,
            'ShipTradeNo': ship_trade_no,
        })

    def store_map_form(self, lgs_type: Literal['C2C', 'B2C'], map_return_url: str,
                       goods_type: str = GOODS_TYPE_NORMAL, mobile: bool = False) -> Dict[str, Any]:
        """
        7-11 門市地圖表單（由消費者瀏覽器 POST）

        選完門市後 PAYUNi 會 POST 回 MapReturnURL：外層 Status=SUCCESS，
        解密 EncryptInfo 後的 MapJson 內含 StoreID / StoreName / Address。
        """
        return {
            'action': f'{self.base_url}/logistics/ship_map',
            'fields': self._envelope({
                'MerID': self.mer_id,
                'Timestamp': int(time.time()),
                'GoodsType': goods_type,
                'LgsType': lgs_type,
                'ShipType': SHIP_TYPE_SEVEN,
                'MapType': '2',
                'MapReturnURL': map_return_url,
                'Tag': '2',
                'MobileTag': 'Y' if mobile else 'N',
            }, '1.1'),
        }

    def parse_store_map_return(self, posted: Dict[str, str]) -> Dict[str, str]:
        """解析門市地圖回傳"""
        if posted.get('Status') != 'SUCCESS':
            raise ValueError(f"門市選擇失敗: {posted.get('Status')}")
        decrypted = self.decrypt_data(posted.get('EncryptInfo', ''))
        store = json.loads(decrypted.get('MapJson', '{}'))
        return {'store_id': store.get('StoreID', ''), 'store_name': store.get('StoreName', ''),
                'address': store.get('Address', '')}

    def print_label_form(self, ship_trade_nos: str, lgs_type: str, goods_type: str,
                         ship_date: str, label_mode: str = '1') -> Dict[str, Any]:
        """
        列印 7-11 託運單（瀏覽器表單 POST 到 /logistics/print_label）

        ship_trade_nos 可用逗號串接多筆；ship_date 格式 YYYYMMDD（外掛在 B2C 時帶隔天）。
        """
        return {
            'action': f'{self.base_url}/logistics/print_label',
            'fields': self._envelope({
                'MerID': self.mer_id,
                'Timestamp': int(time.time()),
                'ShipTradeNo': ship_trade_nos,
                'GoodsType': goods_type,
                'LgsType': lgs_type,
                'ShipType': SHIP_TYPE_SEVEN,
                'ShipDate': ship_date,
                'LabelMode': label_mode,
            }, '1.0'),
        }

    def parse_notify(self, posted: Dict[str, str]) -> Dict[str, Any]:
        """
        解析 NotifyURL 通知

        解密後依 ApiType 區分：
        - ShipStatus：貨態更新，含 ShipTradeNo / ShipStatus / ShipStatusDesc / ShipStatusTime
          （黑貓另含 OBTNumber 託運單號、FileNo）
        - Print：列印結果（7-11 含 Odno / PartnerId / ValidationNo；黑貓在 JsonData 內）

        官方外掛收通知時沒有檢查 HashInfo；這裡有帶就驗，建議保留。
        """
        encrypt_info = posted.get('EncryptInfo', '')
        hash_info = posted.get('HashInfo')
        if hash_info is not None and not self.verify_hash_info(encrypt_info, hash_info):
            raise ValueError('HashInfo 驗證失敗')
        return self.decrypt_data(encrypt_info)


# Usage Example
if __name__ == '__main__':
    print('=' * 60)
    print('PAYUNi 統一物流 - Python 範例')
    print('=' * 60)

    if not HAS_DEPENDENCIES:
        print('✗ 需要安裝: pip install pycryptodome requests')
        raise SystemExit(1)

    service = PAYUNiLogistics(
        mer_id='YOUR_MERCHANT_ID',
        hash_key='YOUR_HASH_KEY_32_BYTES_LONG_XXXX',
        hash_iv='YOUR_HASH_IV_16B',
    )

    # 1. 門市地圖（前端自動送出表單）
    form = service.store_map_form('C2C', 'https://your-site.com/payuni/store-return')
    print(f'[門市地圖] POST {form["action"]}，欄位 {list(form["fields"])}')

    # 2. 建立 7-11 C2C 取貨不付款物流單（StoreID 來自門市地圖回傳）
    payload = service.build_shipment_payload(ShipmentData(
        mer_trade_no=f'LOG{int(time.time())}',
        ship_type=SHIP_TYPE_SEVEN,
        lgs_type='C2C',
        goods_type=GOODS_TYPE_NORMAL,
        trade_amt=500,
        consignee='王小明',
        consignee_mobile='0987654321',
        consignee_mail='buyer@example.com',
        sender_name='測試商家',
        sender_mobile='0912345678',
        notify_url='https://your-site.com/payuni/shipping-notify',
        store_id='123456',
    ))
    print(f'[建立物流單] POST {service.base_url}/logistics/trade，EncryptInfo 內容欄位 {list(payload)}')
