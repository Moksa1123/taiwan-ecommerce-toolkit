#!/usr/bin/env python3
"""
NewebPay 藍新物流 CVS 超商物流 Python 完整範例

支援: C2C 店到店 (7-11, 全家, 萊爾富, OK)、B2C 大宗寄倉

API 文件: https://www.newebpay.com
"""

import json
import hashlib
import hmac
import time
import urllib.parse
from datetime import datetime
from typing import Dict, Literal, Optional
from dataclasses import dataclass, field

try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad
    import requests
    HAS_DEPENDENCIES = True
except ImportError:
    HAS_DEPENDENCIES = False



def strip_padding(data: bytes) -> bytes:
    """
    移除 PKCS#7 padding，容許長度 1–32

    藍新官方 WooCommerce 外掛（newebpay-payment encProcess.php）加密時以 32 bytes
    為區塊補齊（addpadding 的 blocksize=32），因此 padding 值可能是 17–32；
    Crypto.Util.Padding.unpad(data, 16) 遇到這種密文會直接拋錯。
    官方解密端的 strippadding() 以最後一個 byte 為長度移除，此處行為一致，
    另外檢查尾端每個 byte 都等於 padding 長度，金鑰錯誤時才能及早發現。
    """
    if not data:
        raise ValueError('解密結果為空')
    pad_len = data[-1]
    if not 1 <= pad_len <= 32 or pad_len > len(data) or data[-pad_len:] != bytes([pad_len]) * pad_len:
        raise ValueError('padding 格式錯誤（HashKey / HashIV 可能不正確）')
    return data[:-pad_len]

@dataclass
class CVSShipmentData:
    """CVS 超商物流訂單資料"""
    merchant_order_no: str
    lgs_type: Literal['B2C', 'C2C']
    ship_type: Literal['1', '2', '3', '4']  # 1=7-11, 2=FamilyMart, 3=Hi-Life, 4=OK
    receiver_store_code: str
    receiver_name: str
    receiver_cell_phone: str
    receiver_tel: Optional[str] = None
    goods_amount: int = 0
    goods_name: str = ''
    sender_name: Optional[str] = None
    sender_cell_phone: Optional[str] = None
    is_collection: Literal['Y', 'N'] = 'N'
    collection_amount: int = 0
    note: Optional[str] = None


@dataclass
class CVSShipmentResponse:
    """CVS 超商物流訂單回應"""
    success: bool
    status: str
    message: str
    merchant_order_no: str
    logistics_no: Optional[str] = None
    cvs_payment_no: Optional[str] = None
    cvs_validation_no: Optional[str] = None
    booking_note: Optional[str] = None
    raw: Dict = field(default_factory=dict)


@dataclass
class StoreMapData:
    """電子地圖門市查詢資料"""
    merchant_order_no: str
    lgs_type: Literal['B2C', 'C2C']
    ship_type: Literal['1', '2', '3', '4']
    return_url: str
    extra_data: Optional[str] = None


@dataclass
class StoreMapCallback:
    """電子地圖門市選擇回傳"""
    lgs_type: str
    ship_type: str
    merchant_order_no: str
    store_id: str
    store_name: str
    store_addr: str
    store_tel: str
    extra_data: str
    raw: Dict = field(default_factory=dict)


class NewebPayCVSLogistics:
    """
    NewebPay 藍新物流 CVS 超商物流服務

    認證方式: AES-256-CBC + SHA256
    加密方式: JSON + AES-256-CBC 加密 + SHA256 驗證

    支援超商:
    - 1: 7-ELEVEN 統一超商
    - 2: FamilyMart 全家便利商店
    - 3: Hi-Life 萊爾富便利商店
    - 4: OK Mart OK 便利商店

    物流類型:
    - C2C: 店到店 (店取、店寄)
    - B2C: 大宗寄倉 (僅 7-11)

    測試環境:
    - 需至藍新金流申請測試帳號
    - API URL: https://ccore.newebpay.com/API/Logistic
    """

    # 測試環境
    TEST_BASE_URL = 'https://ccore.newebpay.com/API/Logistic'

    # 正式環境
    PROD_BASE_URL = 'https://core.newebpay.com/API/Logistic'

    def __init__(
        self,
        merchant_id: str,
        hash_key: str,
        hash_iv: str,
        is_production: bool = False
    ):
        """
        初始化 NewebPay CVS 物流服務

        Args:
            merchant_id: 商店代號
            hash_key: HashKey (32 字元)
            hash_iv: HashIV (16 字元)
            is_production: 是否為正式環境 (預設 False)

        Raises:
            ImportError: 缺少必要套件
        """
        if not HAS_DEPENDENCIES:
            raise ImportError(
                '需要安裝必要套件:\n'
                '  pip install pycryptodome requests'
            )

        self.merchant_id = merchant_id
        self.hash_key = hash_key.encode('utf-8')
        self.hash_iv = hash_iv.encode('utf-8')
        self.base_url = self.PROD_BASE_URL if is_production else self.TEST_BASE_URL

    def aes_encrypt(self, data: str) -> str:
        """
        AES-256-CBC 加密

        Args:
            data: 明文字串

        Returns:
            str: 加密後的 hex 字串
        """
        cipher = AES.new(self.hash_key, AES.MODE_CBC, self.hash_iv)
        padded_data = pad(data.encode('utf-8'), AES.block_size)
        encrypted = cipher.encrypt(padded_data)
        return encrypted.hex()

    def aes_decrypt(self, encrypted_data: str) -> str:
        """
        AES-256-CBC 解密

        Args:
            encrypted_data: 加密的 hex 字串

        Returns:
            str: 解密後的明文

        Raises:
            ValueError: 解密失敗
        """
        try:
            cipher = AES.new(self.hash_key, AES.MODE_CBC, self.hash_iv)
            decrypted = cipher.decrypt(bytes.fromhex(encrypted_data))
            unpadded = strip_padding(decrypted)
            return unpadded.decode('utf-8')
        except Exception as e:
            raise ValueError(f'解密失敗: {str(e)}')

    def generate_hash_data(self, encrypt_data: str) -> str:
        """
        產生 HashData (SHA256)

        Args:
            encrypt_data: 加密後的資料

        Returns:
            str: SHA256 雜湊值 (大寫)
        """
        # 規格書 NDNS 6.附錄(一)：HashKey={key}&{EncryptData}&HashIV={iv}
        raw = f"HashKey={self.hash_key.decode('utf-8')}&{encrypt_data}&HashIV={self.hash_iv.decode('utf-8')}"
        return hashlib.sha256(raw.encode('utf-8')).hexdigest().upper()

    def verify_hash_data(self, encrypt_data: str, hash_data: str) -> bool:
        """驗證 HashData"""
        return hmac.compare_digest(self.generate_hash_data(encrypt_data), hash_data.upper())

    def query_store_map(
        self,
        data: StoreMapData,
    ) -> Dict[str, any]:
        """
        產生電子地圖（門市選擇）表單

        門市地圖是給「消費者瀏覽器」操作的頁面，必須由瀏覽器以表單 POST 過去；
        伺服器端直接 requests.post 拿不到可用的選店流程。選完門市後，藍新會把
        結果 POST 回 ReturnURL，交由 parse_store_map_callback() 處理。

        Args:
            data: 門市查詢資料 (StoreMapData)

        Returns:
            Dict: {'action': 送出網址, 'fields': 表單欄位}，前端據此產生自動送出的 <form>

        Example:
            >>> store_data = StoreMapData(
            ...     merchant_order_no='ORD123',
            ...     lgs_type='C2C',
            ...     ship_type='1',
            ...     return_url='https://your-site.com/callback',
            ... )
            >>> form = service.query_store_map(store_data)
            >>> form['action']
            'https://ccore.newebpay.com/API/Logistic/storeMap'
        """
        # 準備加密資料
        encrypt_data_obj = {
            'MerchantOrderNo': data.merchant_order_no,
            'LgsType': data.lgs_type,
            'ShipType': data.ship_type,
            'ReturnURL': data.return_url,
            'TimeStamp': str(int(time.time())),
        }

        if data.extra_data:
            encrypt_data_obj['ExtraData'] = data.extra_data

        # JSON 序列化並加密
        json_str = json.dumps(encrypt_data_obj, ensure_ascii=False)
        encrypt_data = self.aes_encrypt(json_str)
        hash_data = self.generate_hash_data(encrypt_data)

        # 送出參數名稱後方都有底線 "_"（規格書 NPA-B51）
        return {
            'action': f'{self.base_url}/storeMap',
            'fields': {
                'UID_': self.merchant_id,
                'EncryptData_': encrypt_data,
                'HashData_': hash_data,
                'Version_': '1.0',
                'RespondType_': 'JSON',
            },
        }

    def parse_store_map_callback(
        self,
        encrypt_data: str,
        hash_data: str,
    ) -> StoreMapCallback:
        """
        解析電子地圖回傳資料

        Args:
            encrypt_data: 加密資料
            hash_data: 雜湊驗證值

        Returns:
            StoreMapCallback: 門市選擇結果

        Raises:
            ValueError: 驗證失敗

        Example:
            >>> callback = service.parse_store_map_callback(
            ...     request.form['EncryptData'],   # 地圖回傳欄位「沒有」底線
            ...     request.form['HashData']
            ... )
            >>> print(f"選擇門市: {callback.store_name}")
        """
        # 驗證 HashData
        if not self.verify_hash_data(encrypt_data, hash_data):
            raise ValueError('HashData 驗證失敗')

        # 解密資料
        decrypted_json = self.aes_decrypt(encrypt_data)
        decrypted = json.loads(decrypted_json)

        return StoreMapCallback(
            lgs_type=decrypted.get('LgsType', ''),
            ship_type=decrypted.get('ShipType', ''),
            merchant_order_no=decrypted.get('MerchantOrderNo', ''),
            store_id=decrypted.get('StoreID', ''),
            store_name=decrypted.get('StoreName', ''),
            store_addr=decrypted.get('StoreAddr', ''),
            store_tel=decrypted.get('StoreTel', ''),
            extra_data=decrypted.get('ExtraData', ''),
            raw=decrypted,
        )

    def create_shipment(
        self,
        data: CVSShipmentData,
    ) -> CVSShipmentResponse:
        """
        建立 CVS 超商物流訂單

        Args:
            data: CVS 物流訂單資料 (CVSShipmentData)

        Returns:
            CVSShipmentResponse: 物流訂單回應

        Raises:
            ValueError: 參數驗證失敗
            Exception: API 請求失敗

        Example:
            >>> shipment_data = CVSShipmentData(
            ...     merchant_order_no='SHIP123',
            ...     lgs_type='C2C',
            ...     ship_type='1',
            ...     receiver_store_code='123456',
            ...     receiver_name='王小明',
            ...     receiver_cell_phone='0912345678',
            ...     goods_amount=500,
            ...     goods_name='測試商品',
            ...     is_collection='N',
            ... )
            >>> result = service.create_shipment(shipment_data)
            >>> print(result.logistics_no)
        """
        # 參數驗證
        if len(data.merchant_order_no) > 30:
            raise ValueError('訂單編號不可超過 30 字元')

        # 準備加密資料
        encrypt_data_obj = {
            'MerchantOrderNo': data.merchant_order_no,
            'LgsType': data.lgs_type,
            'ShipType': data.ship_type,
            'ReceiverStoreCode': data.receiver_store_code,
            'ReceiverName': data.receiver_name,
            'ReceiverCellPhone': data.receiver_cell_phone,
            'TimeStamp': str(int(time.time())),
        }

        # 可選參數
        if data.receiver_tel:
            encrypt_data_obj['ReceiverTel'] = data.receiver_tel
        if data.goods_amount:
            encrypt_data_obj['GoodsAmount'] = data.goods_amount
        if data.goods_name:
            encrypt_data_obj['GoodsName'] = data.goods_name
        if data.sender_name:
            encrypt_data_obj['SenderName'] = data.sender_name
        if data.sender_cell_phone:
            encrypt_data_obj['SenderCellPhone'] = data.sender_cell_phone
        if data.is_collection == 'Y':
            encrypt_data_obj['IsCollection'] = 'Y'
            encrypt_data_obj['CollectionAmount'] = data.collection_amount
        if data.note:
            encrypt_data_obj['Note'] = data.note

        # JSON 序列化並加密
        json_str = json.dumps(encrypt_data_obj, ensure_ascii=False)
        encrypt_data = self.aes_encrypt(json_str)
        hash_data = self.generate_hash_data(encrypt_data)

        # 準備 API 請求
        api_data = {
            'UID_': self.merchant_id,
            'EncryptData_': encrypt_data,
            'HashData_': hash_data,
            'Version_': '1.0',
            'RespondType_': 'JSON',
        }

        # 發送 API 請求
        try:
            response = requests.post(
                f'{self.base_url}/createShipment',
                data=api_data,
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()
        except Exception as e:
            raise Exception(f'API 請求失敗: {str(e)}')

        # 解析回應
        if result.get('Status') != 'SUCCESS':
            return CVSShipmentResponse(
                success=False,
                status=result.get('Status', 'ERROR'),
                message=result.get('Message', '未知錯誤'),
                merchant_order_no=data.merchant_order_no,
                raw=result,
            )

        # 解密回應資料
        # 規格書：只有「送出」的參數帶底線，API 回應欄位是 EncryptData / HashData
        response_encrypt_data = result.get('EncryptData', '')
        response_hash_data = result.get('HashData', '')

        if response_encrypt_data and response_hash_data:
            try:
                if not self.verify_hash_data(response_encrypt_data, response_hash_data):
                    raise ValueError('回應 HashData 驗證失敗')

                decrypted_json = self.aes_decrypt(response_encrypt_data)
                decrypted = json.loads(decrypted_json)
            except Exception as e:
                return CVSShipmentResponse(
                    success=False,
                    status='ERROR',
                    message=f'解密失敗: {str(e)}',
                    merchant_order_no=data.merchant_order_no,
                    raw=result,
                )
        else:
            decrypted = {}

        return CVSShipmentResponse(
            success=True,
            status=result.get('Status', ''),
            message=result.get('Message', ''),
            merchant_order_no=data.merchant_order_no,
            logistics_no=decrypted.get('LogisticsNo'),
            cvs_payment_no=decrypted.get('CVSPaymentNo'),
            cvs_validation_no=decrypted.get('CVSValidationNo'),
            booking_note=decrypted.get('BookingNote'),
            raw=result,
        )


# Usage Example
if __name__ == '__main__':
    print('=' * 60)
    print('NewebPay 藍新物流 CVS - Python 範例')
    print('=' * 60)
    print()

    # 檢查依賴套件
    if not HAS_DEPENDENCIES:
        print('✗ 錯誤: 需要安裝必要套件')
        print('  請執行: pip install pycryptodome requests')
        exit(1)

    print('[注意] 請先至藍新金流申請測試帳號')
    print('並將以下參數替換為您的測試環境資訊')
    print()

    # 初始化服務 (使用測試環境)
    service = NewebPayCVSLogistics(
        merchant_id='YOUR_MERCHANT_ID',
        hash_key='YOUR_HASH_KEY',  # 32 字元
        hash_iv='YOUR_HASH_IV',  # 16 字元
        is_production=False,
    )

    # 範例 1: 查詢電子地圖 (門市選擇)
    print('[範例 1] 查詢電子地圖 (門市選擇)')
    print('-' * 60)

    store_data = StoreMapData(
        merchant_order_no=f'MAP{int(time.time())}',
        lgs_type='C2C',
        ship_type='1',  # 7-ELEVEN
        return_url='https://your-site.com/callback/store-map',
        extra_data='order_id=123',
    )

    try:
        form = service.query_store_map(store_data)
        print(f'✓ 電子地圖表單: POST {form["action"]}（欄位 {", ".join(form["fields"])}）')
        print('前端以此產生自動送出的 <form>，由消費者瀏覽器 POST 到藍新選擇門市')
    except Exception as e:
        print(f'✗ 發生例外: {str(e)}')

    print()
    print('-' * 60)

    # 範例 2: 建立 C2C 物流訂單
    print('[範例 2] 建立 C2C 物流訂單')
    print('-' * 60)

    shipment_data = CVSShipmentData(
        merchant_order_no=f'SHIP{int(time.time())}',
        lgs_type='C2C',
        ship_type='1',  # 7-ELEVEN
        receiver_store_code='123456',  # 收件門市代號 (從電子地圖取得)
        receiver_name='王小明',
        receiver_cell_phone='0912345678',
        goods_amount=500,
        goods_name='測試商品',
        sender_name='賣家',
        sender_cell_phone='0987654321',
        is_collection='N',  # 不代收貨款
    )

    try:
        result = service.create_shipment(shipment_data)

        if result.success:
            print(f'✓ 物流訂單建立成功')
            print(f'  訂單編號: {result.merchant_order_no}')
            print(f'  物流編號: {result.logistics_no}')
            print(f'  寄貨編號: {result.cvs_payment_no}')
            print(f'  驗證碼: {result.cvs_validation_no}')
            print(f'  托運單號: {result.booking_note}')
        else:
            print(f'✗ 物流訂單建立失敗')
            print(f'  狀態: {result.status}')
            print(f'  訊息: {result.message}')
    except Exception as e:
        print(f'✗ 發生例外: {str(e)}')

    print()
    print('=' * 60)
    print('範例執行完成')
    print('=' * 60)
