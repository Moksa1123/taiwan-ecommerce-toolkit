#!/usr/bin/env python3
"""
PAYUNi 統一物流 CVS 超商物流 Python 完整範例

依照 taiwan-logistics-skill 最高規範撰寫
支援: 7-11 C2C (常溫/冷凍)、7-11 B2C、T-Cat 宅配 (常溫/冷凍/冷藏)

API 文件: https://www.payuni.com.tw
"""

import base64
import hashlib
import hmac
import urllib.parse
import time
from datetime import datetime
from typing import Dict, Literal, Optional
from dataclasses import dataclass, field

try:
    from Crypto.Cipher import AES
    import requests
    HAS_DEPENDENCIES = True
except ImportError:
    HAS_DEPENDENCIES = False


@dataclass
class CVS711ShipmentData:
    """7-11 C2C 物流訂單資料"""
    mer_trade_no: str
    goods_type: Literal[1, 2]  # 1=常溫, 2=冷凍
    goods_amount: int
    goods_name: str
    sender_name: str
    sender_phone: str
    sender_store_id: str
    receiver_name: str
    receiver_phone: str
    receiver_store_id: str
    notify_url: str


@dataclass
class TCatShipmentData:
    """T-Cat 宅配物流訂單資料"""
    mer_trade_no: str
    goods_type: Literal[1, 2, 3]  # 1=常溫, 2=冷凍, 3=冷藏
    goods_amount: int
    goods_name: str
    goods_weight: Optional[int] = None  # 重量 (克)
    sender_name: str = ''
    sender_phone: str = ''
    sender_zip_code: str = ''
    sender_address: str = ''
    receiver_name: str = ''
    receiver_phone: str = ''
    receiver_zip_code: str = ''
    receiver_address: str = ''
    scheduled_delivery_time: Optional[Literal['01', '02', '03']] = None  # 01=13前, 02=14-18, 03=不指定
    notify_url: str = ''


@dataclass
class ShipmentResponse:
    """物流訂單回應"""
    success: bool
    status: str
    message: str
    mer_trade_no: str
    logistics_id: Optional[str] = None
    cvs_payment_no: Optional[str] = None
    cvs_validation_no: Optional[str] = None
    expire_date: Optional[str] = None
    shipment_no: Optional[str] = None
    booking_note: Optional[str] = None
    raw: Dict = field(default_factory=dict)


@dataclass
class QueryShipmentData:
    """查詢物流狀態資料"""
    mer_trade_no: str


@dataclass
class QueryShipmentResponse:
    """查詢物流狀態回應"""
    success: bool
    logistics_id: str
    mer_trade_no: str
    logistics_type: str
    logistics_status: str
    logistics_status_msg: str
    shipment_no: Optional[str] = None
    receiver_store_id: Optional[str] = None
    update_time: Optional[str] = None
    raw: Dict = field(default_factory=dict)


class PAYUNiLogistics:
    """
    PAYUNi 統一物流服務

    認證方式: AES-256-GCM + SHA256
    加密方式: AES-GCM 加密 + SHA256 驗證

    支援物流類型:
    - PAYUNi_Logistic_711: 7-11 C2C (常溫)
    - PAYUNi_Logistic_711_Freeze: 7-11 C2C (冷凍)
    - PAYUNi_Logistic_711_B2C: 7-11 B2C (大宗寄倉)
    - PAYUNi_Logistic_Tcat: T-Cat 宅配 (常溫)
    - PAYUNi_Logistic_Tcat_Freeze: T-Cat 冷凍
    - PAYUNi_Logistic_Tcat_Cold: T-Cat 冷藏

    溫度類型:
    - 1: 常溫
    - 2: 冷凍
    - 3: 冷藏 (僅 T-Cat)

    尺寸重量限制:
    - 常溫: 150cm 材積, 20kg
    - 冷凍/冷藏: 120cm 材積, 15kg
    - 材積計算: 長 + 寬 + 高 ≤ 限制

    測試環境:
    - API URL: https://sandbox-api.payuni.com.tw/api
    """

    # 測試環境
    TEST_API_URL = 'https://sandbox-api.payuni.com.tw/api'

    # 正式環境
    PROD_API_URL = 'https://api.payuni.com.tw/api'

    def __init__(
        self,
        mer_id: str,
        hash_key: str,
        hash_iv: str,
        is_production: bool = False
    ):
        """
        初始化 PAYUNi 物流服務

        Args:
            mer_id: 商店代號
            hash_key: HashKey
            hash_iv: HashIV (16 bytes)
            is_production: 是否為正式環境 (預設 False)

        Raises:
            ImportError: 缺少必要套件
        """
        if not HAS_DEPENDENCIES:
            raise ImportError(
                '需要安裝必要套件:\n'
                '  pip install pycryptodome requests'
            )

        self.mer_id = mer_id
        self.hash_key = hash_key.encode('utf-8')
        self.hash_iv = hash_iv.encode('utf-8')
        self.base_url = self.PROD_API_URL if is_production else self.TEST_API_URL

    def encrypt_data(self, data: Dict[str, any]) -> str:
        """
        加密資料 (AES-256-GCM)

        格式與 PAYUNi 官方外掛（wpbr-payuni-shipping PayuniShipping.php）逐位元組相同：

            hex( base64(密文) + ":::" + base64(tag) )

        Args:
            data: 交易資料字典

        Returns:
            str: EncryptInfo（小寫 hex 字串）
        """
        # 轉換為查詢字串（對應 PHP http_build_query）
        query_string = urllib.parse.urlencode(data)

        # AES-256-GCM 加密，IV 即 nonce（16 bytes，與官方一致）
        cipher = AES.new(self.hash_key, AES.MODE_GCM, nonce=self.hash_iv)
        encrypted, tag = cipher.encrypt_and_digest(query_string.encode('utf-8'))

        # base64(密文) + ":::" + base64(tag)，整段再轉 hex
        return (base64.b64encode(encrypted) + b':::' + base64.b64encode(tag)).hex()

    def decrypt_data(self, encrypted_data: str) -> Dict[str, any]:
        """
        解密資料 (AES-256-GCM)

        Args:
            encrypted_data: EncryptInfo（hex 字串）

        Returns:
            Dict: 解密後的資料字典

        Raises:
            ValueError: 格式錯誤，或 tag 驗證失敗（資料遭竄改 / 金鑰錯誤）
        """
        try:
            # hex 解碼後以 ":::" 分離 base64 密文與 base64 tag
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
        """
        產生 HashInfo (SHA256)

        順序為 HashKey + EncryptInfo + HashIV（Key 在前），與官方外掛一致。

        Args:
            encrypt_info: 加密後的資料

        Returns:
            str: SHA256 雜湊值 (大寫)
        """
        raw = self.hash_key.decode('utf-8') + encrypt_info + self.hash_iv.decode('utf-8')
        return hashlib.sha256(raw.encode('utf-8')).hexdigest().upper()

    def verify_hash_info(self, encrypt_info: str, hash_info: str) -> bool:
        """驗證 HashInfo（常數時間比較）"""
        return hmac.compare_digest(self.generate_hash_info(encrypt_info), hash_info.upper())

    def create_711_shipment(
        self,
        data: CVS711ShipmentData,
    ) -> ShipmentResponse:
        """
        建立 7-11 C2C 物流訂單

        Args:
            data: 7-11 C2C 物流訂單資料

        Returns:
            ShipmentResponse: 物流訂單回應

        Raises:
            ValueError: 參數驗證失敗
            Exception: API 請求失敗

        Example:
            >>> shipment_data = CVS711ShipmentData(
            ...     mer_trade_no='LOG123',
            ...     goods_type=1,
            ...     goods_amount=500,
            ...     goods_name='T-shirt',
            ...     sender_name='Sender',
            ...     sender_phone='0912345678',
            ...     sender_store_id='123456',
            ...     receiver_name='Receiver',
            ...     receiver_phone='0987654321',
            ...     receiver_store_id='654321',
            ...     notify_url='https://your-site.com/notify',
            ... )
            >>> result = service.create_711_shipment(shipment_data)
            >>> print(result.logistics_id)
        """
        # 決定物流類型
        logistics_type = 'PAYUNi_Logistic_711_Freeze' if data.goods_type == 2 else 'PAYUNi_Logistic_711'

        # 準備加密資料
        encrypt_data_obj = {
            'MerID': self.mer_id,
            'MerTradeNo': data.mer_trade_no,
            'LogisticsType': logistics_type,
            'GoodsType': data.goods_type,
            'GoodsAmount': data.goods_amount,
            'GoodsName': data.goods_name,
            'SenderName': data.sender_name,
            'SenderPhone': data.sender_phone,
            'SenderStoreID': data.sender_store_id,
            'ReceiverName': data.receiver_name,
            'ReceiverPhone': data.receiver_phone,
            'ReceiverStoreID': data.receiver_store_id,
            'NotifyURL': data.notify_url,
            'Timestamp': int(time.time()),
        }

        # 加密資料
        encrypt_info = self.encrypt_data(encrypt_data_obj)
        hash_info = self.generate_hash_info(encrypt_info)

        # 準備 API 請求
        api_data = {
            'MerID': self.mer_id,
            'Version': '1.0',
            'EncryptInfo': encrypt_info,
            'HashInfo': hash_info,
        }

        # 發送 API 請求
        try:
            response = requests.post(
                f'{self.base_url}/logistics/create',
                data=api_data,
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()
        except Exception as e:
            raise Exception(f'API 請求失敗: {str(e)}')

        # 解析回應
        if result.get('Status') != 'SUCCESS':
            return ShipmentResponse(
                success=False,
                status=result.get('Status', 'ERROR'),
                message=result.get('Message', '未知錯誤'),
                mer_trade_no=data.mer_trade_no,
                raw=result,
            )

        # 解密回應資料
        response_encrypt_info = result.get('EncryptInfo', '')
        if response_encrypt_info:
            try:
                decrypted = self.decrypt_data(response_encrypt_info)
            except:
                decrypted = {}
        else:
            decrypted = {}

        return ShipmentResponse(
            success=True,
            status=result.get('Status', ''),
            message=result.get('Message', ''),
            mer_trade_no=data.mer_trade_no,
            logistics_id=decrypted.get('LogisticsID'),
            cvs_payment_no=decrypted.get('CVSPaymentNo'),
            cvs_validation_no=decrypted.get('CVSValidationNo'),
            expire_date=decrypted.get('ExpireDate'),
            raw=result,
        )

    def create_tcat_shipment(
        self,
        data: TCatShipmentData,
    ) -> ShipmentResponse:
        """
        建立 T-Cat 宅配物流訂單

        Args:
            data: T-Cat 宅配物流訂單資料

        Returns:
            ShipmentResponse: 物流訂單回應

        Example:
            >>> shipment_data = TCatShipmentData(
            ...     mer_trade_no='TCAT123',
            ...     goods_type=2,  # 冷凍
            ...     goods_amount=1000,
            ...     goods_name='Frozen Food',
            ...     sender_name='Store',
            ...     sender_phone='0912345678',
            ...     sender_zip_code='100',
            ...     sender_address='Taipei XXX',
            ...     receiver_name='Customer',
            ...     receiver_phone='0987654321',
            ...     receiver_zip_code='300',
            ...     receiver_address='Hsinchu YYY',
            ...     notify_url='https://your-site.com/notify',
            ... )
            >>> result = service.create_tcat_shipment(shipment_data)
        """
        # 決定物流類型
        if data.goods_type == 2:
            logistics_type = 'PAYUNi_Logistic_Tcat_Freeze'
        elif data.goods_type == 3:
            logistics_type = 'PAYUNi_Logistic_Tcat_Cold'
        else:
            logistics_type = 'PAYUNi_Logistic_Tcat'

        # 準備加密資料
        encrypt_data_obj = {
            'MerID': self.mer_id,
            'MerTradeNo': data.mer_trade_no,
            'LogisticsType': logistics_type,
            'GoodsType': data.goods_type,
            'GoodsAmount': data.goods_amount,
            'GoodsName': data.goods_name,
            'SenderName': data.sender_name,
            'SenderPhone': data.sender_phone,
            'SenderZipCode': data.sender_zip_code,
            'SenderAddress': data.sender_address,
            'ReceiverName': data.receiver_name,
            'ReceiverPhone': data.receiver_phone,
            'ReceiverZipCode': data.receiver_zip_code,
            'ReceiverAddress': data.receiver_address,
            'NotifyURL': data.notify_url,
            'Timestamp': int(time.time()),
        }

        if data.goods_weight:
            encrypt_data_obj['GoodsWeight'] = data.goods_weight
        if data.scheduled_delivery_time:
            encrypt_data_obj['ScheduledDeliveryTime'] = data.scheduled_delivery_time

        # 加密資料
        encrypt_info = self.encrypt_data(encrypt_data_obj)
        hash_info = self.generate_hash_info(encrypt_info)

        # 準備 API 請求
        api_data = {
            'MerID': self.mer_id,
            'Version': '1.0',
            'EncryptInfo': encrypt_info,
            'HashInfo': hash_info,
        }

        # 發送 API 請求
        try:
            response = requests.post(
                f'{self.base_url}/logistics/create',
                data=api_data,
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()
        except Exception as e:
            raise Exception(f'API 請求失敗: {str(e)}')

        # 解析回應
        if result.get('Status') != 'SUCCESS':
            return ShipmentResponse(
                success=False,
                status=result.get('Status', 'ERROR'),
                message=result.get('Message', '未知錯誤'),
                mer_trade_no=data.mer_trade_no,
                raw=result,
            )

        # 解密回應資料
        response_encrypt_info = result.get('EncryptInfo', '')
        if response_encrypt_info:
            decrypted = self.decrypt_data(response_encrypt_info)
        else:
            decrypted = {}

        return ShipmentResponse(
            success=True,
            status=result.get('Status', ''),
            message=result.get('Message', ''),
            mer_trade_no=data.mer_trade_no,
            logistics_id=decrypted.get('LogisticsID'),
            shipment_no=decrypted.get('ShipmentNo'),
            booking_note=decrypted.get('BookingNote'),
            raw=result,
        )

    def query_shipment(
        self,
        data: QueryShipmentData,
    ) -> QueryShipmentResponse:
        """
        查詢物流狀態

        Args:
            data: 查詢物流狀態資料

        Returns:
            QueryShipmentResponse: 物流狀態回應

        Example:
            >>> query_data = QueryShipmentData(mer_trade_no='LOG123')
            >>> result = service.query_shipment(query_data)
            >>> print(f"狀態: {result.logistics_status_msg}")
        """
        # 準備加密資料
        encrypt_data_obj = {
            'MerID': self.mer_id,
            'MerTradeNo': data.mer_trade_no,
            'Timestamp': int(time.time()),
        }

        # 加密資料
        encrypt_info = self.encrypt_data(encrypt_data_obj)
        hash_info = self.generate_hash_info(encrypt_info)

        # 準備 API 請求
        api_data = {
            'MerID': self.mer_id,
            'Version': '1.0',
            'EncryptInfo': encrypt_info,
            'HashInfo': hash_info,
        }

        # 發送 API 請求
        try:
            response = requests.post(
                f'{self.base_url}/logistics/query',
                data=api_data,
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()
        except Exception as e:
            raise Exception(f'API 請求失敗: {str(e)}')

        # 解析回應
        if result.get('Status') != 'SUCCESS':
            return QueryShipmentResponse(
                success=False,
                logistics_id='',
                mer_trade_no=data.mer_trade_no,
                logistics_type='',
                logistics_status='',
                logistics_status_msg=result.get('Message', ''),
                raw=result,
            )

        # 解密回應資料
        response_encrypt_info = result.get('EncryptInfo', '')
        decrypted = self.decrypt_data(response_encrypt_info)

        return QueryShipmentResponse(
            success=True,
            logistics_id=decrypted.get('LogisticsID', ''),
            mer_trade_no=decrypted.get('MerTradeNo', ''),
            logistics_type=decrypted.get('LogisticsType', ''),
            logistics_status=decrypted.get('LogisticsStatus', ''),
            logistics_status_msg=decrypted.get('LogisticsStatusMsg', ''),
            shipment_no=decrypted.get('ShipmentNo'),
            receiver_store_id=decrypted.get('ReceiverStoreID'),
            update_time=decrypted.get('UpdateTime'),
            raw=decrypted,
        )


# Usage Example
if __name__ == '__main__':
    print('=' * 60)
    print('PAYUNi 統一物流 - Python 範例')
    print('=' * 60)
    print()

    # 檢查依賴套件
    if not HAS_DEPENDENCIES:
        print('✗ 錯誤: 需要安裝必要套件')
        print('  請執行: pip install pycryptodome requests')
        exit(1)

    print('[注意] 請先至 PAYUNi 申請測試帳號')
    print()

    # 初始化服務
    service = PAYUNiLogistics(
        mer_id='YOUR_MERCHANT_ID',
        hash_key='YOUR_HASH_KEY',
        hash_iv='YOUR_HASH_IV',
        is_production=False,
    )

    # 範例: 建立 7-11 C2C 物流訂單
    print('[範例] 建立 7-11 C2C 物流訂單')
    print('-' * 60)

    shipment_data = CVS711ShipmentData(
        mer_trade_no=f'LOG{int(time.time())}',
        goods_type=1,  # 常溫
        goods_amount=500,
        goods_name='測試商品',
        sender_name='寄件人',
        sender_phone='0912345678',
        sender_store_id='123456',
        receiver_name='收件人',
        receiver_phone='0987654321',
        receiver_store_id='654321',
        notify_url='https://your-site.com/notify',
    )

    try:
        result = service.create_711_shipment(shipment_data)

        if result.success:
            print(f'✓ 物流訂單建立成功')
            print(f'  訂單編號: {result.mer_trade_no}')
            print(f'  物流編號: {result.logistics_id}')
            print(f'  寄貨編號: {result.cvs_payment_no}')
            print(f'  驗證碼: {result.cvs_validation_no}')
            print(f'  有效期限: {result.expire_date}')
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
