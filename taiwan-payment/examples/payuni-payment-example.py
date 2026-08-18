#!/usr/bin/env python3
"""
PAYUNi 統一金流 Python 完整範例

依照 taiwan-payment-skill 最高規範撰寫
支援: 信用卡、ATM、超商代碼、AFTEE、iCash Pay

API 文件: https://www.payuni.com.tw
"""

import hashlib
import urllib.parse
import time
from datetime import datetime
from typing import Dict, Literal, Optional
from dataclasses import dataclass, field

try:
    from Crypto.Cipher import AES
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False


@dataclass
class PaymentOrderData:
    """PAYUNi 付款訂單資料"""
    mer_trade_no: str
    trade_amt: int
    prod_desc: str
    return_url: str
    notify_url: str
    pay_type: Literal['Credit', 'VACC', 'CVS', 'AFTEE', 'iCashPay']
    trade_limit_date: Optional[str] = None
    unified_id: Optional[str] = None
    buyer_name: Optional[str] = None
    buyer_tel: Optional[str] = None
    buyer_email: Optional[str] = None


@dataclass
class PaymentOrderResponse:
    """PAYUNi 付款訂單回應"""
    success: bool
    status: str
    message: str
    mer_trade_no: str
    trade_no: Optional[str] = None
    payment_url: Optional[str] = None
    atm_bank_code: Optional[str] = None
    atm_account: Optional[str] = None
    atm_expire_date: Optional[str] = None
    cvs_code: Optional[str] = None
    cvs_expire_date: Optional[str] = None
    error_code: Optional[str] = None
    raw: Dict = field(default_factory=dict)


@dataclass
class PaymentCallbackData:
    """PAYUNi 付款回傳資料"""
    status: str
    message: str
    mer_id: str
    mer_trade_no: str
    trade_no: str
    trade_amt: int
    trade_status: str
    pay_type: str
    pay_date: str
    settle_date: Optional[str] = None
    checksum: str
    raw: Dict = field(default_factory=dict)


class PAYUNiPaymentService:
    """
    PAYUNi 統一金流服務

    認證方式: AES-256-GCM + SHA256
    加密方式: AES-GCM 加密 + SHA256 驗證

    支援付款方式:
    - Credit: 信用卡
    - VACC: ATM 轉帳
    - CVS: 超商代碼
    - AFTEE: AFTEE 先享後付
    - iCashPay: iCash Pay

    測試環境:
    - API URL: https://sandbox-api.payuni.com.tw/api/upp
    - 需至 PAYUNi 申請測試帳號
    """

    # 測試環境
    TEST_API_URL = 'https://sandbox-api.payuni.com.tw/api/upp'
    TEST_QUERY_URL = 'https://sandbox-api.payuni.com.tw/api/trade_query'

    # 正式環境
    PROD_API_URL = 'https://api.payuni.com.tw/api/upp'
    PROD_QUERY_URL = 'https://api.payuni.com.tw/api/trade_query'

    def __init__(
        self,
        mer_id: str,
        hash_key: str,
        hash_iv: str,
        is_production: bool = False
    ):
        """
        初始化 PAYUNi 金流服務

        Args:
            mer_id: 商店代號
            hash_key: HashKey
            hash_iv: HashIV (16 bytes)
            is_production: 是否為正式環境 (預設 False)

        Raises:
            ImportError: 缺少 pycryptodome 套件
        """
        if not HAS_CRYPTO:
            raise ImportError('需要安裝 pycryptodome: pip install pycryptodome')

        self.mer_id = mer_id
        self.hash_key = hash_key.encode('utf-8')
        self.hash_iv = hash_iv.encode('utf-8')
        self.api_url = self.PROD_API_URL if is_production else self.TEST_API_URL
        self.query_url = self.PROD_QUERY_URL if is_production else self.TEST_QUERY_URL

    def encrypt_data(self, data: Dict[str, any]) -> str:
        """
        加密資料 (AES-256-GCM)

        Args:
            data: 交易資料字典

        Returns:
            str: AES-GCM 加密後的 hex 字串 (base64(密文) + ":::" + base64(tag))

        Example:
            >>> data = {'MerID': 'MS123', 'TradeAmt': 100}
            >>> encrypted = service.encrypt_data(data)
            >>> len(encrypted) > 0
            True
        """
        import base64
        # 步驟 1: 轉換為查詢字串
        query_string = urllib.parse.urlencode(data)

        # 步驟 2: AES-256-GCM 加密
        cipher = AES.new(self.hash_key, AES.MODE_GCM, nonce=self.hash_iv)
        encrypted, tag = cipher.encrypt_and_digest(query_string.encode('utf-8'))

        # 步驟 3: 分別 base64 編碼，用 ":::" 分隔
        encrypted_b64 = base64.b64encode(encrypted).decode('utf-8')
        tag_b64 = base64.b64encode(tag).decode('utf-8')
        return encrypted_b64 + ':::' + tag_b64

    def decrypt_data(self, encrypted_data: str) -> Dict[str, any]:
        """
        解密資料 (AES-256-GCM)

        Args:
            encrypted_data: AES-GCM 加密的字串 (base64(密文) + ":::" + base64(tag))

        Returns:
            Dict: 解密後的資料字典

        Raises:
            ValueError: 解密失敗或驗證失敗
        """
        try:
            import base64
            # 步驟 1: 分離 base64 編碼的密文和 tag
            parts = encrypted_data.split(':::')
            if len(parts) != 2:
                raise ValueError('格式錯誤: 缺少 ":::" 分隔符')

            encrypted_b64, tag_b64 = parts

            # 步驟 2: Base64 解碼
            encrypted = base64.b64decode(encrypted_b64)
            tag = base64.b64decode(tag_b64)

            # 步驟 3: AES-256-GCM 解密並驗證
            decipher = AES.new(self.hash_key, AES.MODE_GCM, nonce=self.hash_iv)
            decrypted = decipher.decrypt_and_verify(encrypted, tag)

            # 步驟 4: 解析查詢字串
            query_string = decrypted.decode('utf-8')
            params = urllib.parse.parse_qs(query_string)

            # 步驟 5: 轉換為單值字典
            result = {k: v[0] if len(v) == 1 else v for k, v in params.items()}
            return result
        except Exception as e:
            raise ValueError(f'解密失敗: {str(e)}')

    def generate_checksum(self, encrypt_info: str) -> str:
        """
        產生 Checksum (SHA256)

        Args:
            encrypt_info: 加密後的資料

        Returns:
            str: SHA256 雜湊值 (大寫)

        Example:
            >>> checksum = service.generate_checksum('abcd1234')
            >>> len(checksum)
            64
        """
        # 組合字串: HashKey + EncryptInfo + HashIV (Key 在前)
        raw = self.hash_key.decode('utf-8') + encrypt_info + self.hash_iv.decode('utf-8')

        # SHA256 雜湊並轉大寫
        return hashlib.sha256(raw.encode('utf-8')).hexdigest().upper()

    def verify_checksum(self, encrypt_info: str, checksum: str) -> bool:
        """
        驗證 Checksum

        Args:
            encrypt_info: 加密後的資料
            checksum: 接收到的 Checksum

        Returns:
            bool: 驗證是否通過
        """
        calculated_checksum = self.generate_checksum(encrypt_info)
        return calculated_checksum == checksum.upper()

    def create_order(
        self,
        data: PaymentOrderData,
    ) -> PaymentOrderResponse:
        """
        建立付款訂單

        Args:
            data: 付款訂單資料 (PaymentOrderData)

        Returns:
            PaymentOrderResponse: 付款訂單回應

        Raises:
            ValueError: 參數驗證失敗
            Exception: API 請求失敗

        Example:
            >>> order_data = PaymentOrderData(
            ...     mer_trade_no=f'UNI{int(time.time())}',
            ...     trade_amt=3000,
            ...     prod_desc='測試商品',
            ...     return_url='https://your-site.com/return',
            ...     notify_url='https://your-site.com/notify',
            ...     pay_type='Credit',
            ... )
            >>> result = service.create_order(order_data)
            >>> print(result.payment_url)
        """
        # 參數驗證
        if data.trade_amt < 1:
            raise ValueError('金額必須大於 0')
        if len(data.mer_trade_no) > 30:
            raise ValueError('訂單編號不可超過 30 字元')

        # 準備 API 參數
        trade_data = {
            'MerID': self.mer_id,
            'MerTradeNo': data.mer_trade_no,
            'TradeAmt': data.trade_amt,
            'ProdDesc': data.prod_desc,
            'ReturnURL': data.return_url,
            'NotifyURL': data.notify_url,
            'PayType': data.pay_type,
            'Timestamp': int(time.time()),
        }

        # 可選參數
        if data.trade_limit_date:
            trade_data['TradeLimitDate'] = data.trade_limit_date
        if data.unified_id:
            trade_data['UnifiedID'] = data.unified_id
        if data.buyer_name:
            trade_data['BuyerName'] = data.buyer_name
        if data.buyer_tel:
            trade_data['BuyerTel'] = data.buyer_tel
        if data.buyer_email:
            trade_data['BuyerEmail'] = data.buyer_email

        # 加密資料
        encrypt_info = self.encrypt_data(trade_data)

        # 產生 Checksum
        checksum = self.generate_checksum(encrypt_info)

        # 準備 API 請求
        api_data = {
            'MerID': self.mer_id,
            'Version': '1.0',
            'EncryptInfo': encrypt_info,
            'HashInfo': checksum,
        }

        # 發送 API 請求
        try:
            import requests
            response = requests.post(
                self.api_url,
                data=api_data,
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()
        except Exception as e:
            raise Exception(f'API 請求失敗: {str(e)}')

        # 解析回應
        if result.get('Status') != 'SUCCESS':
            return PaymentOrderResponse(
                success=False,
                status=result.get('Status', 'ERROR'),
                message=result.get('Message', '未知錯誤'),
                mer_trade_no=data.mer_trade_no,
                error_code=result.get('ErrCode'),
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

        return PaymentOrderResponse(
            success=True,
            status=result.get('Status', ''),
            message=result.get('Message', ''),
            mer_trade_no=data.mer_trade_no,
            trade_no=decrypted.get('TradeNo'),
            payment_url=decrypted.get('PaymentURL'),
            atm_bank_code=decrypted.get('ATMBankCode'),
            atm_account=decrypted.get('ATMAcct'),
            atm_expire_date=decrypted.get('ATMExpireDate'),
            cvs_code=decrypted.get('CVSCode'),
            cvs_expire_date=decrypted.get('CVSExpireDate'),
            raw=result,
        )

    def parse_callback(self, callback_data: Dict[str, str]) -> PaymentCallbackData:
        """
        解析付款回傳資料

        Args:
            callback_data: POST 回傳的參數字典

        Returns:
            PaymentCallbackData: 解析後的回傳資料

        Raises:
            ValueError: Checksum 驗證失敗或解密失敗

        Example:
            >>> callback = request.form.to_dict()
            >>> result = service.parse_callback(callback)
            >>> if result.status == 'SUCCESS':
            ...     print(f"付款成功: {result.trade_no}")
        """
        # 驗證 Checksum
        encrypt_info = callback_data.get('EncryptInfo', '')
        hash_info = callback_data.get('HashInfo', '')

        if not self.verify_checksum(encrypt_info, hash_info):
            raise ValueError('Checksum 驗證失敗')

        # 解密資料
        decrypted = self.decrypt_data(encrypt_info)

        return PaymentCallbackData(
            status=decrypted.get('Status', ''),
            message=decrypted.get('Message', ''),
            mer_id=decrypted.get('MerID', ''),
            mer_trade_no=decrypted.get('MerTradeNo', ''),
            trade_no=decrypted.get('TradeNo', ''),
            trade_amt=int(decrypted.get('TradeAmt', 0)),
            trade_status=decrypted.get('TradeStatus', ''),
            pay_type=decrypted.get('PayType', ''),
            pay_date=decrypted.get('PayDate', ''),
            settle_date=decrypted.get('SettleDate'),
            checksum=hash_info,
            raw=decrypted,
        )


# Usage Example
if __name__ == '__main__':
    print('=' * 60)
    print('PAYUNi 統一金流 - Python 範例')
    print('=' * 60)
    print()

    # 檢查是否有 pycryptodome
    if not HAS_CRYPTO:
        print('✗ 錯誤: 需要安裝 pycryptodome 套件')
        print('  請執行: pip install pycryptodome')
        exit(1)

    # 注意: 需要替換為您的測試帳號
    print('[注意] 請先至 PAYUNi 申請測試帳號')
    print('並將以下參數替換為您的測試環境資訊')
    print()

    # 初始化服務 (使用測試環境)
    service = PAYUNiPaymentService(
        mer_id='YOUR_MERCHANT_ID',  # 請替換為您的商店代號
        hash_key='YOUR_HASH_KEY',  # 請替換為您的 HashKey
        hash_iv='YOUR_HASH_IV',  # 請替換為您的 HashIV (16 bytes)
        is_production=False,
    )

    # 範例: 建立信用卡付款訂單
    print('[範例] 建立信用卡付款訂單')
    print('-' * 60)

    order_data = PaymentOrderData(
        mer_trade_no=f'UNI{int(time.time())}',
        trade_amt=3000,
        prod_desc='測試商品購買',
        return_url='https://your-site.com/payment/return',
        notify_url='https://your-site.com/payment/notify',
        pay_type='Credit',
        buyer_name='測試買家',
        buyer_email='test@example.com',
    )

    try:
        result = service.create_order(order_data)

        if result.success:
            print(f'✓ 訂單建立成功')
            print(f'  訂單編號: {result.mer_trade_no}')
            print(f'  交易編號: {result.trade_no}')
            print(f'  付款網址: {result.payment_url}')
            print()
            print('請將買家導向付款網址完成付款')
        else:
            print(f'✗ 訂單建立失敗')
            print(f'  狀態: {result.status}')
            print(f'  訊息: {result.message}')
            if result.error_code:
                print(f'  錯誤碼: {result.error_code}')
    except Exception as e:
        print(f'✗ 發生例外: {str(e)}')

    print()
    print('=' * 60)
    print('範例執行完成')
    print('=' * 60)
