#!/usr/bin/env python3
"""
NewebPay 藍新金流 Python 完整範例

支援: MPG 整合支付 (信用卡、ATM、超商代碼、LINE Pay、Apple Pay 等)

API 文件: https://www.newebpay.com
"""

import hashlib
import hmac
import urllib.parse
import json
from datetime import datetime
from typing import Dict, Literal, Optional
from dataclasses import dataclass, field

try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False



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


def parse_trade_info_plaintext(text: str) -> Dict:
    """
    解析解密後的 TradeInfo 明文

    明文格式取決於送出時的 RespondType：
    - JSON   → {"Status": ..., "Message": ..., "Result": {...}}
    - String → Status=...&Message=...&MerchantID=...（欄位攤平，無 Result）

    與藍新官方外掛 create_aes_decrypt() 相同，先試 JSON 再退回 query string。
    若一律用 parse_qs，JSON 明文會被解析成空 dict（沒有 "=" 的片段會被丟棄），
    導致所有回傳都被誤判為失敗。
    """
    text = text.strip()
    if text.startswith('{'):
        return json.loads(text)
    params = urllib.parse.parse_qs(text, keep_blank_values=True)
    return {k: v[0] if len(v) == 1 else v for k, v in params.items()}


def extract_result(decrypted: Dict) -> Dict:
    """取出交易明細：JSON 模式在 Result 內，String 模式則是攤平在最外層"""
    result = decrypted.get('Result')
    if isinstance(result, dict):
        return result
    if isinstance(result, str) and result.strip().startswith('{'):
        return json.loads(result)
    return decrypted

@dataclass
class MPGOrderData:
    """NewebPay MPG 付款訂單資料"""
    merchant_order_no: str
    amt: int
    item_desc: str
    email: str
    return_url: str
    notify_url: Optional[str] = None
    client_back_url: Optional[str] = None
    enable_credit: bool = True
    enable_vacc: bool = False
    enable_cvs: bool = False
    enable_barcode: bool = False
    enable_linepay: bool = False
    enable_applepay: bool = False
    login_type: int = 0
    order_comment: Optional[str] = None
    trade_limit: int = 900
    exp_date: Optional[str] = None


@dataclass
class MPGOrderResponse:
    """NewebPay MPG 付款訂單回應"""
    success: bool
    merchant_order_no: str
    form_action: str = ''
    trade_info: str = ''
    trade_sha: str = ''
    merchant_id: str = ''
    version: str = ''
    error_message: str = ''
    raw: Dict[str, str] = field(default_factory=dict)


@dataclass
class MPGCallbackData:
    """NewebPay MPG 付款回傳資料"""
    status: str
    message: str
    merchant_order_no: str
    amt: int
    trade_no: str
    merchant_id: str
    payment_type: str
    pay_time: str
    ip: str
    check_code_valid: bool = False  # CheckCode 驗證結果（防金額竄改）
    escrow_bank: Optional[str] = None
    code_no: Optional[str] = None
    barcode_1: Optional[str] = None
    barcode_2: Optional[str] = None
    barcode_3: Optional[str] = None
    expire_date: Optional[str] = None
    raw: Dict = field(default_factory=dict)


class NewebPayMPGService:
    """
    NewebPay 藍新金流 MPG 整合支付服務

    認證方式: AES-256-CBC + SHA256
    加密方式: 雙層加密 (AES 加密 + SHA256 驗證)

    支援付款方式:
    - CREDIT: 信用卡
    - VACC: ATM 轉帳
    - CVS: 超商代碼
    - BARCODE: 超商條碼
    - LINEPAY: LINE Pay
    - APPLEPAY: Apple Pay

    測試環境說明:
    - 需至藍新金流申請測試帳號
    - 測試網址: https://ccore.newebpay.com
    """

    # 測試環境
    TEST_API_URL = 'https://ccore.newebpay.com/MPG/mpg_gateway'
    TEST_QUERY_URL = 'https://ccore.newebpay.com/API/QueryTradeInfo'

    # 正式環境
    PROD_API_URL = 'https://core.newebpay.com/MPG/mpg_gateway'
    PROD_QUERY_URL = 'https://core.newebpay.com/API/QueryTradeInfo'

    def __init__(
        self,
        merchant_id: str,
        hash_key: str,
        hash_iv: str,
        is_production: bool = False
    ):
        """
        初始化 NewebPay MPG 服務

        Args:
            merchant_id: 商店代號
            hash_key: HashKey (32 字元)
            hash_iv: HashIV (16 字元)
            is_production: 是否為正式環境 (預設 False)

        Raises:
            ImportError: 缺少 pycryptodome 套件
        """
        if not HAS_CRYPTO:
            raise ImportError('需要安裝 pycryptodome: pip install pycryptodome')

        self.merchant_id = merchant_id
        self.hash_key = hash_key.encode('utf-8')
        self.hash_iv = hash_iv.encode('utf-8')
        self.api_url = self.PROD_API_URL if is_production else self.TEST_API_URL
        self.query_url = self.PROD_QUERY_URL if is_production else self.TEST_QUERY_URL

    def encrypt_trade_info(self, data: Dict[str, any]) -> str:
        """
        加密 TradeInfo (AES-256-CBC)

        Args:
            data: 交易資料字典

        Returns:
            str: AES 加密後的 hex 字串

        Example:
            >>> data = {'MerchantID': 'MS123', 'Amt': 100}
            >>> encrypted = service.encrypt_trade_info(data)
            >>> len(encrypted) > 0
            True
        """
        # 步驟 1: 轉換為查詢字串
        query_string = urllib.parse.urlencode(data)

        # 步驟 2: AES-256-CBC 加密
        # 標準 PKCS#7（16 bytes 區塊），與規格書 NDNF 範例 openssl_encrypt(..., OPENSSL_RAW_DATA)
        # 一致。官方外掛改用 32 bytes 區塊補齊，兩者藍新伺服器都接受；
        # 但「解密」必須兩種都能處理，見 strip_padding()。
        cipher = AES.new(self.hash_key, AES.MODE_CBC, self.hash_iv)
        padded = pad(query_string.encode('utf-8'), AES.block_size)
        encrypted = cipher.encrypt(padded)

        # 步驟 3: 轉換為 hex
        return encrypted.hex()

    def decrypt_trade_info(self, encrypted_data: str) -> Dict[str, any]:
        """
        解密 TradeInfo (AES-256-CBC)

        Args:
            encrypted_data: AES 加密的 hex 字串

        Returns:
            Dict: 解密後的資料字典

        Raises:
            ValueError: 解密失敗
        """
        try:
            # 步驟 1: hex 轉 bytes
            encrypted_bytes = bytes.fromhex(encrypted_data)

            # 步驟 2: AES-256-CBC 解密
            decipher = AES.new(self.hash_key, AES.MODE_CBC, self.hash_iv)
            decrypted = decipher.decrypt(encrypted_bytes)
            unpadded = strip_padding(decrypted)

            # 步驟 3: 依 RespondType 解析（JSON 或 query string）
            return parse_trade_info_plaintext(unpadded.decode('utf-8'))
        except Exception as e:
            raise ValueError(f'解密失敗: {str(e)}')

    def generate_trade_sha(self, trade_info: str) -> str:
        """
        產生 TradeSha (SHA256)

        Args:
            trade_info: 加密後的 TradeInfo

        Returns:
            str: SHA256 雜湊值 (大寫)

        Example:
            >>> trade_sha = service.generate_trade_sha('abcd1234')
            >>> len(trade_sha)
            64
        """
        # 組合字串: HashKey=xxx&TradeInfo=xxx&HashIV=xxx
        raw = f"HashKey={self.hash_key.decode('utf-8')}&{trade_info}&HashIV={self.hash_iv.decode('utf-8')}"

        # SHA256 雜湊並轉大寫
        return hashlib.sha256(raw.encode('utf-8')).hexdigest().upper()

    def verify_trade_sha(self, trade_info: str, trade_sha: str) -> bool:
        """
        驗證 TradeSha

        Args:
            trade_info: 加密後的 TradeInfo
            trade_sha: 接收到的 TradeSha

        Returns:
            bool: 驗證是否通過
        """
        calculated_sha = self.generate_trade_sha(trade_info)
        # 常數時間比較，避免以回應時間差逐字元猜出正確雜湊
        return hmac.compare_digest(calculated_sha, trade_sha.upper())

    def generate_check_code(self, amt, merchant_id: str, merchant_order_no: str, trade_no: str) -> str:
        """
        產生 CheckCode（規格書 NDNF 4.1.5，用於驗證回傳結果）

        SHA256("HashIV={iv}&Amt=..&MerchantID=..&MerchantOrderNo=..&TradeNo=..&HashKey={key}").upper()
        四個欄位依字母排序後以 http_build_query 串接。注意 HashIV 在前、HashKey 在後，
        與 TradeSha 相反。
        """
        params = {
            'Amt': amt,
            'MerchantID': merchant_id,
            'MerchantOrderNo': merchant_order_no,
            'TradeNo': trade_no,
        }
        query = urllib.parse.urlencode(sorted(params.items()))
        raw = f"HashIV={self.hash_iv.decode('utf-8')}&{query}&HashKey={self.hash_key.decode('utf-8')}"
        return hashlib.sha256(raw.encode('utf-8')).hexdigest().upper()

    def generate_check_value(self, amt, merchant_order_no: str) -> str:
        """
        產生 CheckValue（規格書 NDNF 4.1.6，單筆交易查詢 QueryTradeInfo 用）

        SHA256("IV={iv}&Amt=..&MerchantID=..&MerchantOrderNo=..&Key={key}").upper()
        前後綴是 IV= / Key=，不是 HashIV= / HashKey=。
        """
        params = {'Amt': amt, 'MerchantID': self.merchant_id, 'MerchantOrderNo': merchant_order_no}
        query = urllib.parse.urlencode(sorted(params.items()))
        raw = f"IV={self.hash_iv.decode('utf-8')}&{query}&Key={self.hash_key.decode('utf-8')}"
        return hashlib.sha256(raw.encode('utf-8')).hexdigest().upper()

    # BNPL 先買後付（AFTEE 先享後付、OPPAY 大哥付你分期），規格書 NDNF-1.2.5 §4.7、§4.8
    BNPL_PATHS = {'refund': '/API/Bnpl/refund', 'settle': '/API/Bnpl/settle'}

    def build_bnpl_request(self, action: Literal['refund', 'settle'], merchant_order_no: str, amt: int,
                           payment_type: Literal['AFTEE', 'OPPAY'], reason: str = '',
                           timestamp: Optional[int] = None, respond_type: str = 'JSON') -> Dict[str, str]:
        """
        組出 BNPL 取消交易／退款（refund，須帶 reason）或請款（settle）的 Post 參數。

        取消金額須等於訂單完成金額；退款金額可小於（可部分、多次）。
        取消／退款：交易成立後一年內。請款：AFTEE 89 天內、大哥付你分期 365 天內，須整筆請款。
        EncryptData_／HashData_ 與 MPG 的 TradeInfo／TradeSha 算法相同。
        """
        data = {
            'MerchantOrderNo': merchant_order_no,
            'Amt': amt,
            'TimeStamp': timestamp if timestamp is not None else int(datetime.now().timestamp()),
            'PaymentType': payment_type,
        }
        if action == 'refund':
            if not reason:
                raise ValueError('取消交易／退款須填 Reason')
            data['Reason'] = reason
        encrypted = self.encrypt_trade_info(data)
        return {
            'UID_': self.merchant_id,
            'Version_': '1.1',
            'EncryptData_': encrypted,
            'RespondType_': respond_type,
            'HashData_': self.generate_trade_sha(encrypted),
        }

    def bnpl_url(self, action: Literal['refund', 'settle']) -> str:
        return self.api_url.split('/MPG/')[0] + self.BNPL_PATHS[action]

    # 信用卡定期定額，規格書 NDNP-1.0.8。Post 參數為 MerchantID_ + PostData_（加密同 TradeInfo，無 SHA 欄位）
    PERIOD_PATHS = {
        'create': '/MPG/period',                # 建立委託 NPA-B05，Version 1.5
        'alter_status': '/MPG/period/AlterStatus',  # 修改委託狀態 NPA-B051，Version 1.0
        'alter_amt': '/MPG/period/AlterAmt',    # 修改委託內容 NPA-B052，Version 1.2
        'query': '/MPG/period/query',           # 委託單查詢 NPA-B053，Version 1.0（1.0.8 新增）
    }
    PERIOD_VERSIONS = {'create': '1.5', 'alter_status': '1.0', 'alter_amt': '1.2', 'query': '1.0'}

    def period_url(self, action: str) -> str:
        return self.api_url.split('/MPG/')[0] + self.PERIOD_PATHS[action]

    def build_period_request(self, action: str, data: Dict[str, any]) -> Dict[str, str]:
        """組出定期定額 API 的 Post 參數；data 未帶 Version 時補上該 API 的版本"""
        data = dict(data)
        data.setdefault('Version', self.PERIOD_VERSIONS[action])
        return {'MerchantID_': self.merchant_id, 'PostData_': self.encrypt_trade_info(data)}

    def parse_period_response(self, period: str) -> Dict:
        """
        解密回傳的 Period（建立完成、每期授權 NPA-N050、修改、查詢皆同）。
        委託單查詢的明文鍵名是小寫 status／message／result，這裡統一成 Status／Message／Result。
        """
        data = self.decrypt_trade_info(period)
        for low, key in (('status', 'Status'), ('message', 'Message'), ('result', 'Result')):
            if low in data and key not in data:
                data[key] = data.pop(low)
        return data

    def parse_bnpl_response(self, response: Dict[str, str]) -> Dict:
        """驗證 HashData 後解密 EncryptData；回應密文可能是 32 bytes 區塊補齊，strip_padding 已處理"""
        if not self.verify_trade_sha(response['EncryptData'], response['HashData']):
            raise ValueError('HashData 驗證失敗')
        result = self.decrypt_trade_info(response['EncryptData'])
        result['Status'] = response.get('Status')
        return result

    def create_order(
        self,
        data: MPGOrderData,
    ) -> MPGOrderResponse:
        """
        建立 MPG 整合支付訂單

        Args:
            data: MPG 訂單資料 (MPGOrderData)

        Returns:
            MPGOrderResponse: MPG 訂單回應

        Raises:
            ValueError: 參數驗證失敗

        Example:
            >>> order_data = MPGOrderData(
            ...     merchant_order_no=f'MPG{int(time.time())}',
            ...     amt=2500,
            ...     item_desc='測試商品',
            ...     email='test@example.com',
            ...     return_url='https://your-site.com/callback',
            ...     enable_credit=True,
            ...     enable_vacc=True,
            ...     enable_cvs=True,
            ... )
            >>> result = service.create_order(order_data)
            >>> print(result.form_action)
        """
        # 參數驗證
        if data.amt < 1:
            raise ValueError('金額必須大於 0')
        if len(data.merchant_order_no) > 30:
            raise ValueError('訂單編號不可超過 30 字元')

        # 準備 API 參數
        trade_info_data = {
            'MerchantID': self.merchant_id,
            'RespondType': 'JSON',
            'TimeStamp': str(int(datetime.now().timestamp())),
            'Version': '2.0',
            'MerchantOrderNo': data.merchant_order_no,
            'Amt': data.amt,
            'ItemDesc': data.item_desc,
            'Email': data.email,
            'ReturnURL': data.return_url,
            'LoginType': data.login_type,
            'TradeLimit': data.trade_limit,
        }

        # 啟用付款方式
        if data.enable_credit:
            trade_info_data['CREDIT'] = 1
        if data.enable_vacc:
            trade_info_data['VACC'] = 1
        if data.enable_cvs:
            trade_info_data['CVS'] = 1
        if data.enable_barcode:
            trade_info_data['BARCODE'] = 1
        if data.enable_linepay:
            trade_info_data['LINEPAY'] = 1
        if data.enable_applepay:
            trade_info_data['APPLEPAY'] = 1

        # 可選參數
        if data.notify_url:
            trade_info_data['NotifyURL'] = data.notify_url
        if data.client_back_url:
            trade_info_data['ClientBackURL'] = data.client_back_url
        if data.order_comment:
            trade_info_data['OrderComment'] = data.order_comment
        if data.exp_date:
            trade_info_data['ExpDate'] = data.exp_date

        # 加密 TradeInfo
        trade_info = self.encrypt_trade_info(trade_info_data)

        # 產生 TradeSha
        trade_sha = self.generate_trade_sha(trade_info)

        # 回傳表單資料
        return MPGOrderResponse(
            success=True,
            merchant_order_no=data.merchant_order_no,
            form_action=self.api_url,
            trade_info=trade_info,
            trade_sha=trade_sha,
            merchant_id=self.merchant_id,
            version='2.0',
            raw={'TradeInfo': trade_info, 'TradeSha': trade_sha},
        )

    def parse_callback(self, callback_data: Dict[str, str]) -> MPGCallbackData:
        """
        解析 MPG 付款回傳資料

        Args:
            callback_data: POST 回傳的參數字典

        Returns:
            MPGCallbackData: 解析後的回傳資料

        Raises:
            ValueError: TradeSha 驗證失敗或解密失敗

        Example:
            >>> callback = request.form.to_dict()
            >>> result = service.parse_callback(callback)
            >>> if result.status == 'SUCCESS':
            ...     print(f"付款成功: {result.trade_no}")
        """
        # 驗證 TradeSha
        trade_info = callback_data.get('TradeInfo', '')
        trade_sha = callback_data.get('TradeSha', '')

        if not self.verify_trade_sha(trade_info, trade_sha):
            raise ValueError('TradeSha 驗證失敗')

        # 解密 TradeInfo
        decrypted = self.decrypt_trade_info(trade_info)

        # 解析回傳資料（JSON 模式在 Result 內；String 模式攤平在最外層）
        result_dict = extract_result(decrypted)

        # 驗證 CheckCode（規格書 4.1.5）。TradeSha 只證明資料來自持有金鑰的一方，
        # CheckCode 另外綁定金額與訂單編號，建議入帳前一併確認。
        check_code_valid = False
        received_check_code = result_dict.get('CheckCode', '')
        if received_check_code and result_dict.get('TradeNo'):
            expected = self.generate_check_code(
                amt=result_dict.get('Amt', ''),
                merchant_id=result_dict.get('MerchantID', ''),
                merchant_order_no=result_dict.get('MerchantOrderNo', ''),
                trade_no=result_dict.get('TradeNo', ''),
            )
            check_code_valid = hmac.compare_digest(expected, str(received_check_code).upper())

        return MPGCallbackData(
            status=decrypted.get('Status', ''),
            message=decrypted.get('Message', ''),
            merchant_order_no=result_dict.get('MerchantOrderNo', ''),
            amt=int(result_dict.get('Amt', 0)),
            trade_no=result_dict.get('TradeNo', ''),
            merchant_id=result_dict.get('MerchantID', ''),
            payment_type=result_dict.get('PaymentType', ''),
            pay_time=result_dict.get('PayTime', ''),
            ip=result_dict.get('IP', ''),
            check_code_valid=check_code_valid,
            escrow_bank=result_dict.get('EscrowBank'),
            code_no=result_dict.get('CodeNo'),
            barcode_1=result_dict.get('Barcode_1'),
            barcode_2=result_dict.get('Barcode_2'),
            barcode_3=result_dict.get('Barcode_3'),
            expire_date=result_dict.get('ExpireDate'),
            raw=decrypted,
        )


# Usage Example
if __name__ == '__main__':
    print('=' * 60)
    print('NewebPay 藍新金流 MPG - Python 範例')
    print('=' * 60)
    print()

    # 檢查是否有 pycryptodome
    if not HAS_CRYPTO:
        print('✗ 錯誤: 需要安裝 pycryptodome 套件')
        print('  請執行: pip install pycryptodome')
        exit(1)

    # 注意: 需要替換為您的測試帳號
    print('[注意] 請先至藍新金流申請測試帳號')
    print('並將以下參數替換為您的測試環境資訊')
    print()

    # 初始化服務 (使用測試環境)
    service = NewebPayMPGService(
        merchant_id='YOUR_MERCHANT_ID',  # 請替換為您的商店代號
        hash_key='YOUR_HASH_KEY',  # 請替換為您的 HashKey (32字元)
        hash_iv='YOUR_HASH_IV',  # 請替換為您的 HashIV (16字元)
        is_production=False,
    )

    # 範例: 建立 MPG 整合支付訂單
    print('[範例] 建立 MPG 整合支付訂單')
    print('-' * 60)

    order_data = MPGOrderData(
        merchant_order_no=f'MPG{int(datetime.now().timestamp())}',
        amt=2500,
        item_desc='測試商品購買',
        email='test@example.com',
        return_url='https://your-site.com/api/payment/callback',
        notify_url='https://your-site.com/api/payment/notify',
        client_back_url='https://your-site.com/order/complete',
        enable_credit=True,  # 啟用信用卡
        enable_vacc=True,  # 啟用 ATM
        enable_cvs=True,  # 啟用超商代碼
    )

    try:
        result = service.create_order(order_data)

        if result.success:
            print(f'✓ 訂單建立成功')
            print(f'  訂單編號: {result.merchant_order_no}')
            print(f'  表單網址: {result.form_action}')
            print(f'  TradeInfo: {result.trade_info[:50]}...')
            print(f'  TradeSha: {result.trade_sha[:32]}...')
            print()
            print('請將以下參數 POST 到表單網址:')
            print(f'  MerchantID: {result.merchant_id}')
            print(f'  TradeInfo: {result.trade_info}')
            print(f'  TradeSha: {result.trade_sha}')
            print(f'  Version: {result.version}')
        else:
            print(f'✗ 訂單建立失敗: {result.error_message}')
    except Exception as e:
        print(f'✗ 發生例外: {str(e)}')

    print()
    print('=' * 60)
    print('範例執行完成')
    print('=' * 60)
