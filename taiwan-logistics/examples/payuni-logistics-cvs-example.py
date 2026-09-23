#!/usr/bin/env python3
"""
PAYUNi 統一物流範例：7-ELEVEN 大宗寄倉 (B2C)／店到店 (C2C)、黑貓宅配 (HOME)

依據 PAYUNi 官方文件 https://docs.payuni.com.tw/web/#/7（物流工具、Notify、貨態碼 120、錯誤碼 119）；
加解密與官方外掛 PAYUNi_for_WooCommerce 1.2.8、官方 PHP SDK 逐位元組相同（tests/vectors/payuni.json）。

| 用途 | 路徑 | Version |
|---|---|---|
| 門市地圖（前景） | /api/logistics/ship_map | 1.1 |
| 物流單查詢 | /api/logistics/query | 1.1 |
| 超商出貨單列印（前景） | /api/logistics/print_label | 1.0 |
| 黑貓產編號並下載託運單（前景） | /api/home_delivery/get_obt_number_pdf | 1.0 |
| 黑貓補下載託運單（前景） | /api/home_delivery/download_pdf | 1.0 |

物流單在交易 API（UPP 或幕後交易）一併建立，見 shipment_fields()。
"""

import base64
import hashlib
import hmac
import json
import time
import urllib.parse
from typing import Any, Dict, Literal, Optional

try:
    from Crypto.Cipher import AES
    import requests
    HAS_DEPENDENCIES = True
except ImportError:
    HAS_DEPENDENCIES = False


SHIP_TYPE_SEVEN = '1'
SHIP_TYPE_TCAT = '2'
GOODS_TYPE_NORMAL = '1'     # 常溫
GOODS_TYPE_FROZEN = '2'     # 冷凍
GOODS_TYPE_COLD = '3'       # 冷藏（僅黑貓）

# 物流貨態狀態碼（官方 page 120）
SHIP_STATUS = {
    '91': '未處理', '92': '處理中', '98': '處理中(已接收)', '21': '待出貨', '22': '物流驗收',
    '31': '配送中', '32': '待取貨', '33': '異常訂單', '11': '已取貨', '41': '已取消',
    '43': '賠償訂單', '44': '包裹遺失', '46': '包裹拋棄', '51': '一般退貨', '52': '買家未取',
    '53': '廠退', '55': '賣家未取', '56': '已轉宅配退回', '81': '門市關轉', '82': '待轉宅配退回',
}


def shipment_fields(lgs_type: Literal['B2C', 'C2C', 'HOME'], consignee: str, consignee_mobile: str,
                    goods_type: str = GOODS_TYPE_NORMAL, backend: bool = False, cod: bool = False,
                    store_id: str = '', consignee_address: str = '', delivery_time_tag: str = '04') -> Dict[str, Any]:
    """
    交易 API 的物流欄位，併入 EncryptInfo。

    - UPP（backend=False）：ShipTag=1；cod=True 另帶 Ship=1（取貨付款）。門市由消費者在支付頁選。
    - 幕後交易（backend=True，ATM／CVS／信用卡 Token／LINE Pay／街口／AFTEE）：只支援取貨不付款，
      ServiceType=3；超商須帶 StoreID，黑貓須帶 ConsigneeAddress、DeliveryTimeTag。
    """
    ship_type = SHIP_TYPE_TCAT if lgs_type == 'HOME' else SHIP_TYPE_SEVEN
    fields: Dict[str, Any] = {'LgsType': lgs_type, 'ShipType': ship_type, 'GoodsType': goods_type,
                              'Consignee': consignee, 'ConsigneeMobile': consignee_mobile}
    if not backend:
        fields['ShipTag'] = 1
        if cod:
            fields['Ship'] = 1
        if ship_type == SHIP_TYPE_TCAT and consignee_address:
            fields['ConsigneeAddress'] = consignee_address
        return fields
    if cod:
        raise ValueError('幕後交易 API 只支援取貨不付款')
    fields['ServiceType'] = '3'
    if ship_type == SHIP_TYPE_SEVEN:
        if not store_id:
            raise ValueError('超商取貨需要 StoreID（門市地圖取得）')
        fields['StoreID'] = store_id
    else:
        if not consignee_address:
            raise ValueError('黑貓宅配需要 ConsigneeAddress')
        fields.update({'ConsigneeAddress': consignee_address, 'DeliveryTimeTag': delivery_time_tag})
    return fields


class PAYUNiLogistics:
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
            # 外層錯誤不帶 EncryptInfo
            return {'Status': result.get('Status', ''), 'Message': result.get('Message', ''), 'raw': result}
        if not self.verify_hash_info(encrypt_info, result.get('HashInfo', '')):
            raise ValueError('HashInfo 驗證失敗')
        return self.decrypt_data(encrypt_info)

    # ------------------------------------------------------------------
    # 業務 API
    # ------------------------------------------------------------------

    def query_shipment(self, lgs_type: Literal['B2C', 'C2C', 'HOME', 'C2B'], ship_trade_no: str = '',
                       trade_type: Optional[int] = None, return_odno: str = '') -> Dict[str, Any]:
        """/logistics/query：ShipTradeNo 與 ReturnOdno（C2B 退貨便，12 碼）二擇一"""
        if bool(ship_trade_no) == bool(return_odno):
            raise ValueError('ShipTradeNo 與 ReturnOdno 必須二擇一')
        data: Dict[str, Any] = {'MerID': self.mer_id, 'Timestamp': int(time.time()), 'LgsType': lgs_type}
        if ship_trade_no:
            data['ShipTradeNo'] = ship_trade_no
        else:
            data['ReturnOdno'] = return_odno
        if trade_type:
            data['TradeType'] = trade_type
        return self._post('/logistics/query', data)

    def store_map_form(self, lgs_type: Literal['C2C', 'B2C'], mer_key_no: str, map_return_url: str = '',
                       goods_type: str = GOODS_TYPE_NORMAL, tag: int = 2, include_islands: bool = True,
                       mobile: bool = False) -> Dict[str, Any]:
        """
        /logistics/ship_map 前景表單。

        tag：2 回傳門市、3 更新商店 C2C 退貨門市、4 更新物流單取件門市、5 更新單筆 C2C 退貨門市；
        tag 為 4、5 時 mer_key_no 帶 UNi 物流序號。冷凍（GoodsType=2）MapType 固定 2。
        """
        map_type = 2 if include_islands or goods_type == GOODS_TYPE_FROZEN else 1
        return {
            'action': f'{self.base_url}/logistics/ship_map',
            'fields': self._envelope({
                'MerID': self.mer_id, 'Timestamp': int(time.time()), 'MerKeyNo': mer_key_no,
                'GoodsType': goods_type, 'LgsType': lgs_type, 'ShipType': SHIP_TYPE_SEVEN,
                'MapType': map_type, 'MapReturnURL': map_return_url, 'Tag': tag,
                'MobileTag': 'Y' if mobile else 'N',
            }, '1.1'),
        }

    def parse_store_map_return(self, posted: Dict[str, str]) -> Dict[str, str]:
        """解析門市地圖回傳的 MapJson（StoreID、StoreName、Address、InsularArea）"""
        if not self.verify_hash_info(posted.get('EncryptInfo', ''), posted.get('HashInfo', '')):
            raise ValueError('HashInfo 驗證失敗')
        decrypted = self.decrypt_data(posted['EncryptInfo'])
        if decrypted.get('Status') != 'SUCCESS':
            raise ValueError(f"門市選擇失敗: {decrypted.get('Status')} {decrypted.get('Message', '')}")
        return json.loads(decrypted.get('MapJson', '{}'))

    def print_label_form(self, ship_trade_nos: str, lgs_type: Literal['C2C', 'B2C'], ship_date: str,
                         goods_type: str = GOODS_TYPE_NORMAL, label_mode: int = 1) -> Dict[str, Any]:
        """/logistics/print_label：最多 50 筆（逗號分隔）；ship_date 為 YYYYMMDD，B2C 不得為當日"""
        return {
            'action': f'{self.base_url}/logistics/print_label',
            'fields': self._envelope({
                'MerID': self.mer_id, 'Timestamp': int(time.time()), 'ShipTradeNo': ship_trade_nos,
                'GoodsType': goods_type, 'LgsType': lgs_type, 'ShipType': SHIP_TYPE_SEVEN,
                'ShipDate': ship_date, 'LabelMode': label_mode,
            }, '1.0'),
        }

    def tcat_label_form(self, ship_trade_nos: str, ship_date: str, delivery_date: str, spec: int,
                        goods_type: str = GOODS_TYPE_NORMAL, memo: str = '') -> Dict[str, Any]:
        """/home_delivery/get_obt_number_pdf：spec 1=60、2=90、3=120、4=150（低溫不支援 150）"""
        return {
            'action': f'{self.base_url}/home_delivery/get_obt_number_pdf',
            'fields': self._envelope({
                'MerID': self.mer_id, 'Timestamp': int(time.time()), 'ShipTradeNo': ship_trade_nos,
                'GoodsType': goods_type, 'LgsType': 'HOME', 'ShipType': SHIP_TYPE_TCAT,
                'ShipDate': ship_date, 'DeliveryDate': delivery_date, 'Spec': spec, 'Memo': memo,
            }, '1.0'),
        }

    def parse_notify(self, posted: Dict[str, str]) -> Dict[str, Any]:
        """
        貨態通知（URL 於 PAYUNi 後台物流設定）：先驗 HashInfo 再解密。
        ApiType=ShipStatus 為貨態，ApiType=Print 為列印結果。
        """
        encrypt_info = posted.get('EncryptInfo', '')
        if not self.verify_hash_info(encrypt_info, posted.get('HashInfo', '')):
            raise ValueError('HashInfo 驗證失敗')
        return self.decrypt_data(encrypt_info)


if __name__ == '__main__':
    if not HAS_DEPENDENCIES:
        print('需要安裝: pip install pycryptodome requests')
        raise SystemExit(1)

    service = PAYUNiLogistics('YOUR_MERCHANT_ID', 'YOUR_HASH_KEY_32_BYTES_LONG_XXXX', 'YOUR_HASH_IV_16B')

    form = service.store_map_form('C2C', mer_key_no=f'MAP{int(time.time())}',
                                  map_return_url='https://your-site.com/payuni/store-return')
    print(f'[門市地圖] POST {form["action"]}，欄位 {list(form["fields"])}')

    fields = shipment_fields('C2C', '王小明', '0987654321', backend=True, store_id='916712')
    print(f'[建立物流] 併入交易 API EncryptInfo 的欄位：{fields}')
