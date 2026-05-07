#!/usr/bin/env python3
"""
SmilePay 速買配 Python 完整範例

依照 taiwan-payment-skill 最高規範撰寫
支援: ATM 虛擬帳號、信用卡 (一次付清/分期)、超商條碼、ibon、FamiPort

API 文件: https://www.smilepay.net/
參考文件: taiwan-payment/references/smilepay-payment-api.md

特色:
    - 一支 SPPayment.asp 端點涵蓋多種非同步取號類付款 (ATM / 條碼 / ibon / FamiPort)
    - 信用卡 / 銀聯卡走另一支 mtmk_utf.asp 結帳頁
    - 回應為 XML 格式 (使用 Python stdlib xml.etree.ElementTree 解析)
    - 通知驗章採 Mid_smilepay 加權校驗碼 (非 SHA256)
    - 部分中文欄位 (Errdesc / Process_time / Address) 可能以 BIG-5 編碼

依賴:
    pip install requests
    (本範例不需 pycryptodome，SmilePay 沒有 AES 加密流程)
"""

import hashlib
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Literal, Optional
from urllib.parse import urlencode
import xml.etree.ElementTree as ET

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


# ----------------------------------------------------------------------------
# Dataclasses (Inputs / Responses)
# ----------------------------------------------------------------------------


@dataclass
class SmilePayBuyer:
    """SmilePay 訂購人 / 付款人資訊 (UTF-8 編碼)"""
    name: str                        # Pur_name 訂購人姓名
    mobile: str                      # Mobile_number 手機
    email: str                       # Email
    tel: Optional[str] = None        # Tel_number 市話 (常以手機帶入)
    address: Optional[str] = None    # Address 收件 / 帳單地址


@dataclass
class SmilePayAtmOrder:
    """SmilePay ATM 虛擬帳號 (Pay_zg=2) 訂單資料"""
    data_id: str                     # 商店訂單編號 (英數，唯一，<=20)
    amount: int                      # 金額 (TWD 整數)
    item_name: str                   # od_sob 商品摘要 (<=45 字)
    buyer: SmilePayBuyer
    deadline_date: Optional[str] = None       # YYYY/MM/DD，預設下單日 +7 天
    roturl: Optional[str] = None              # 付款結果通知網址
    roturl_status: Optional[str] = None       # 通知識別字串
    remark: Optional[str] = None
    invoice_num: Optional[str] = None         # 統編 / 載具


@dataclass
class SmilePayCreditOrder:
    """SmilePay 信用卡 (Pay_zg=1) 一次付清訂單"""
    data_id: str
    amount: int
    item_name: str                            # od_sob (<=49 字)
    buyer: SmilePayBuyer
    roturl: Optional[str] = None
    roturl_status: Optional[str] = None
    remark: Optional[str] = None
    invoice_num: Optional[str] = None


@dataclass
class SmilePayInstallmentOrder:
    """SmilePay 信用卡分期訂單 (Pay_zg=1 + Stage)"""
    data_id: str
    amount: int
    item_name: str
    buyer: SmilePayBuyer
    stage: Literal[3, 6, 12, 18, 24] = 3      # 分期期數
    roturl: Optional[str] = None
    roturl_status: Optional[str] = None
    remark: Optional[str] = None


@dataclass
class SmilePayBarcodeOrder:
    """SmilePay 超商條碼 (Pay_zg=3) 訂單資料"""
    data_id: str
    amount: int
    item_name: str
    buyer: SmilePayBuyer
    deadline_date: Optional[str] = None       # < 50 天
    roturl: Optional[str] = None
    roturl_status: Optional[str] = None
    remark: Optional[str] = None


@dataclass
class SmilePayAtmResponse:
    """ATM 取號成功回應"""
    success: bool
    status: str
    desc: str
    data_id: str
    smilepay_no: str = ''
    atm_bank_no: str = ''                      # 3 碼財金代碼
    atm_no: str = ''                           # 14~16 碼虛擬帳號
    amount: int = 0
    pay_end_date: str = ''
    raw_xml: str = ''


@dataclass
class SmilePayBarcodeResponse:
    """條碼取號成功回應"""
    success: bool
    status: str
    desc: str
    data_id: str
    smilepay_no: str = ''
    barcode1: str = ''
    barcode2: str = ''
    barcode3: str = ''
    amount: int = 0
    pay_end_date: str = ''
    raw_xml: str = ''


@dataclass
class SmilePayCreditRedirect:
    """信用卡 / 銀聯 / 分期：回傳 redirect URL，給前端跳轉"""
    success: bool
    redirect_url: str
    data_id: str
    params: Dict[str, str] = field(default_factory=dict)


@dataclass
class SmilePayNotification:
    """Roturl 通知解析結果 (取號類 / 信用卡共用)"""
    classif: str                               # A/B/C/T/O
    data_id: str
    smseid: str
    amount: int
    process_date: str
    process_time: str
    response_id: Optional[str] = None          # 信用卡有，1=成功
    payment_title: Optional[str] = None
    errdesc: Optional[str] = None
    mid_smilepay: Optional[str] = None
    verified: bool = False                     # Mid_smilepay 是否通過
    raw: Dict[str, str] = field(default_factory=dict)


# ----------------------------------------------------------------------------
# Service
# ----------------------------------------------------------------------------


class SmilePayPaymentService:
    """
    SmilePay 速買配金流服務

    認證方式: 帳號參數三件組 (Dcvc / Rvg2c / Verify_key) + Mid_smilepay 通知驗章
    加密方式: 不使用 AES / SHA256；僅有 Mid_smilepay 加權校驗碼

    支援付款方式:
    - Pay_zg=1  信用卡 (一次付清 / 分期 + Stage)
    - Pay_zg=2  ATM 虛擬帳號
    - Pay_zg=3  超商條碼
    - Pay_zg=4  7-11 ibon
    - Pay_zg=6  全家 FamiPort
    - Pay_zg=11 銀聯 / 國際信用卡

    測試環境 (官方公開測試參數):
        Dcvc:        107
        Rvg2c:       1
        Verify_key:  174A02F97A95F72CE301137B3F98D128
        mid:         1111

    測試 / 正式環境同網域 (ssl.smse.com.tw)；差異僅在帳號參數。
    """

    # 測試帳號 (官方公開)
    TEST_DCVC = '107'
    TEST_RVG2C = '1'
    TEST_VERIFY_KEY = '174A02F97A95F72CE301137B3F98D128'
    TEST_MID = '1111'

    # API 端點
    PAYMENT_URL = 'https://ssl.smse.com.tw/api/SPPayment.asp'           # 取號類
    CHECKOUT_URL = 'https://ssl.smse.com.tw/ezpos/mtmk_utf.asp'         # 信用卡 / 銀聯
    MODIFY_URL = 'https://ssl.smse.com.tw/api/SPPayment_Modify.asp'     # 訂單修改 / 退款

    def __init__(
        self,
        dcvc: str,
        rvg2c: str,
        verify_key: str,
        mid: str = '',
        timeout: int = 30,
    ):
        """
        初始化 SmilePay 金流服務

        Args:
            dcvc:       商店代號
            rvg2c:      收款銀行 / 路由碼 (預設 1)
            verify_key: 驗證金鑰 (32 碼大寫 hex)
            mid:        金流 mid (Mid_smilepay 簽章用，正式環境必填)
            timeout:    HTTP 逾時 (秒)
        """
        if not HAS_REQUESTS:
            raise ImportError('需要安裝 requests: pip install requests')

        self.dcvc = dcvc
        self.rvg2c = rvg2c
        self.verify_key = verify_key
        self.mid = mid
        self.timeout = timeout

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _account_params(self) -> Dict[str, str]:
        """三件組帳號驗證參數"""
        return {
            'Dcvc': self.dcvc,
            'Rvg2c': self.rvg2c,
            'Verify_key': self.verify_key,
        }

    def _buyer_params(self, buyer: SmilePayBuyer) -> Dict[str, str]:
        """訂購人欄位"""
        params = {
            'Pur_name': buyer.name,
            'Mobile_number': buyer.mobile,
            'Email': buyer.email,
        }
        if buyer.tel:
            params['Tel_number'] = buyer.tel
        else:
            params['Tel_number'] = buyer.mobile
        if buyer.address:
            params['Address'] = buyer.address
        return params

    def _post_payment(self, payload: Dict[str, str]) -> ET.Element:
        """POST 至 SPPayment.asp 並解析 XML"""
        resp = requests.post(self.PAYMENT_URL, data=payload, timeout=self.timeout)
        resp.raise_for_status()
        # 速買配回傳的內容通常是 UTF-8；少數欄位 (Errdesc 等) 可能 BIG-5
        # 但根層 XML 本體為 UTF-8，可直接以 fromstring 解析
        try:
            return ET.fromstring(resp.text)
        except ET.ParseError as exc:
            raise RuntimeError(
                f'SmilePay XML 解析失敗: {exc} | body={resp.text[:200]}'
            )

    def _xml_text(self, root: ET.Element, tag: str, default: str = '') -> str:
        node = root.findtext(tag)
        return node if node is not None else default

    @staticmethod
    def _default_deadline(days: int = 7) -> str:
        return (datetime.now() + timedelta(days=days)).strftime('%Y/%m/%d')

    # ------------------------------------------------------------------
    # Order creation
    # ------------------------------------------------------------------

    def create_atm_order(self, order: SmilePayAtmOrder) -> SmilePayAtmResponse:
        """
        建立 ATM 虛擬帳號訂單 (Pay_zg=2)

        Returns:
            SmilePayAtmResponse: 含 atm_bank_no / atm_no / pay_end_date
        """
        if order.amount < 8 or order.amount > 20000:
            raise ValueError('ATM 金額需介於 8 ~ 20,000 元')
        if len(order.data_id) > 20:
            raise ValueError('Data_id 不可超過 20 字元')

        payload = {
            **self._account_params(),
            **self._buyer_params(order.buyer),
            'Pay_zg': '2',
            'Data_id': order.data_id,
            'Amount': str(order.amount),
            'od_sob': order.item_name[:45],
            'Deadline_date': order.deadline_date or self._default_deadline(7),
        }
        if order.roturl:
            payload['Roturl'] = order.roturl
        if order.roturl_status:
            payload['Roturl_status'] = order.roturl_status
        if order.remark:
            payload['Remark'] = order.remark
        if order.invoice_num:
            payload['Invoice_num'] = order.invoice_num

        root = self._post_payment(payload)
        status = self._xml_text(root, 'Status')
        desc = self._xml_text(root, 'Desc')

        return SmilePayAtmResponse(
            success=(status == '1'),
            status=status,
            desc=desc,
            data_id=self._xml_text(root, 'Data_id', order.data_id),
            smilepay_no=self._xml_text(root, 'SmilePayNO'),
            atm_bank_no=self._xml_text(root, 'AtmBankNo'),
            atm_no=self._xml_text(root, 'AtmNo'),
            amount=int(self._xml_text(root, 'Amount', '0') or 0),
            pay_end_date=self._xml_text(root, 'PayEndDate'),
            raw_xml=ET.tostring(root, encoding='unicode'),
        )

    def create_barcode_order(self, order: SmilePayBarcodeOrder) -> SmilePayBarcodeResponse:
        """
        建立超商條碼訂單 (Pay_zg=3)

        Returns:
            SmilePayBarcodeResponse: 含三段條碼 + pay_end_date
        """
        if order.amount < 8 or order.amount > 20000:
            raise ValueError('條碼金額需介於 8 ~ 20,000 元')

        payload = {
            **self._account_params(),
            **self._buyer_params(order.buyer),
            'Pay_zg': '3',
            'Data_id': order.data_id,
            'Amount': str(order.amount),
            'od_sob': order.item_name[:45],
            'Deadline_date': order.deadline_date or self._default_deadline(30),
        }
        if order.roturl:
            payload['Roturl'] = order.roturl
        if order.roturl_status:
            payload['Roturl_status'] = order.roturl_status
        if order.remark:
            payload['Remark'] = order.remark

        root = self._post_payment(payload)
        status = self._xml_text(root, 'Status')

        return SmilePayBarcodeResponse(
            success=(status == '1'),
            status=status,
            desc=self._xml_text(root, 'Desc'),
            data_id=self._xml_text(root, 'Data_id', order.data_id),
            smilepay_no=self._xml_text(root, 'SmilePayNO'),
            barcode1=self._xml_text(root, 'Barcode1'),
            barcode2=self._xml_text(root, 'Barcode2'),
            barcode3=self._xml_text(root, 'Barcode3'),
            amount=int(self._xml_text(root, 'Amount', '0') or 0),
            pay_end_date=self._xml_text(root, 'PayEndDate'),
            raw_xml=ET.tostring(root, encoding='unicode'),
        )

    def create_credit_order(self, order: SmilePayCreditOrder) -> SmilePayCreditRedirect:
        """
        建立信用卡 (一次付清) 結帳頁 redirect URL (Pay_zg=1)

        Note: 此方法不發 HTTP 請求，僅組好 querystring 給商店端 redirect。
              消費者進入結帳頁後輸入卡號、3D 驗證，結束後 SmilePay 以
              querystring 帶結果到 Roturl。
        """
        params = {
            **self._account_params(),
            **self._buyer_params(order.buyer),
            'Pay_zg': '1',
            'Data_id': order.data_id,
            'Amount': str(order.amount),
            'od_sob': order.item_name[:49],
        }
        if order.roturl:
            params['Roturl'] = order.roturl
        if order.roturl_status:
            params['Roturl_status'] = order.roturl_status
        if order.remark:
            params['Remark'] = order.remark
        if order.invoice_num:
            params['Invoice_num'] = order.invoice_num

        return SmilePayCreditRedirect(
            success=True,
            redirect_url=f'{self.CHECKOUT_URL}?{urlencode(params)}',
            data_id=order.data_id,
            params=params,
        )

    def create_credit_installment_order(
        self, order: SmilePayInstallmentOrder
    ) -> SmilePayCreditRedirect:
        """
        建立信用卡分期 (Pay_zg=1 + Stage) 結帳頁 redirect URL

        模組預設支援期數: 3 / 6 / 12 / 18 / 24
        """
        if order.stage not in (3, 6, 12, 18, 24):
            raise ValueError('Stage 僅支援 3 / 6 / 12 / 18 / 24 期')

        params = {
            **self._account_params(),
            **self._buyer_params(order.buyer),
            'Pay_zg': '1',
            'Stage': str(order.stage),
            'Data_id': order.data_id,
            'Amount': str(order.amount),
            'od_sob': order.item_name[:49],
        }
        if order.roturl:
            params['Roturl'] = order.roturl
        if order.roturl_status:
            params['Roturl_status'] = order.roturl_status
        if order.remark:
            params['Remark'] = order.remark

        return SmilePayCreditRedirect(
            success=True,
            redirect_url=f'{self.CHECKOUT_URL}?{urlencode(params)}',
            data_id=order.data_id,
            params=params,
        )

    # ------------------------------------------------------------------
    # Mid_smilepay verification
    # ------------------------------------------------------------------

    @staticmethod
    def calc_mid_smilepay(mid: str, amount: int, smseid: str) -> int:
        """
        計算 Mid_smilepay 通知校驗碼

        演算法 (摘自 WooCommerce 模組推導，見 references/smilepay-payment-api.md)

        步驟:
            1. 取 Smseid 末 4 碼 r1 r2 r3 r4，非數字以 9 取代
            2. Amount 補零至 8 碼 (左補) -> str1
            3. 串接 s = mid + str1 + r1 r2 r3 r4 (16 碼)
            4. even = s 偶數位 (0,2,4...) 加總；odd = 奇數位加總
            5. Mid_smilepay = even * 9 + odd * 3
        """
        r_all = (smseid or '')[-4:].rjust(4, '9')
        r = [c if c.isdigit() else '9' for c in r_all]
        str1 = str(amount).zfill(8)
        s = f'{mid}{str1}{r[0]}{r[1]}{r[2]}{r[3]}'
        if len(s) != 16:
            raise ValueError(
                f'Mid_smilepay 長度錯誤: {len(s)} (應為 16, mid={mid})'
            )
        even = sum(int(s[i]) for i in range(16) if i % 2 == 0)
        odd = sum(int(s[i]) for i in range(16) if i % 2 == 1)
        return even * 9 + odd * 3

    def verify_notification(self, callback: Dict[str, str]) -> SmilePayNotification:
        """
        驗證 SmilePay Roturl 通知

        Args:
            callback: 速買配 POST/GET 進來的所有 querystring 參數

        Returns:
            SmilePayNotification: verified=True 表示 Mid_smilepay 校驗通過

        Raises:
            ValueError: 缺必要欄位 (Data_id / Smseid / Amount / Mid_smilepay)
        """
        for key in ('Data_id', 'Smseid', 'Amount', 'Mid_smilepay'):
            if key not in callback:
                raise ValueError(f'通知缺少必要欄位: {key}')

        amount_str = str(callback.get('Amount', '')).strip()
        if '.' in amount_str:
            raise ValueError(f'Amount 含小數點: {amount_str}')
        try:
            amount = int(amount_str)
        except ValueError as exc:
            raise ValueError(f'Amount 非整數: {amount_str}') from exc

        verified = False
        if self.mid:
            try:
                expected = self.calc_mid_smilepay(
                    self.mid, amount, callback.get('Smseid', '')
                )
                verified = str(expected) == str(callback.get('Mid_smilepay', ''))
            except ValueError:
                verified = False

        return SmilePayNotification(
            classif=callback.get('Classif', ''),
            data_id=callback.get('Data_id', ''),
            smseid=callback.get('Smseid', ''),
            amount=amount,
            process_date=callback.get('Process_date', ''),
            process_time=callback.get('Process_time', ''),
            response_id=callback.get('Response_id'),
            payment_title=callback.get('Payment_title'),
            errdesc=callback.get('Errdesc'),
            mid_smilepay=callback.get('Mid_smilepay'),
            verified=verified,
            raw=dict(callback),
        )

    @staticmethod
    def build_notification_response(roturl_status: str = 'OK') -> str:
        """產生回給 SmilePay 的 Roturlstatus 字串"""
        return f'<Roturlstatus>{roturl_status}</Roturlstatus>'


# ----------------------------------------------------------------------------
# Examples
# ----------------------------------------------------------------------------


def example_create_atm_order(service: SmilePayPaymentService) -> None:
    print('[範例 1] 建立 ATM 虛擬帳號訂單 (Pay_zg=2)')
    print('-' * 60)
    order = SmilePayAtmOrder(
        data_id=f'ORD{int(time.time())}',
        amount=1500,
        item_name='測試商品 A * 1',
        buyer=SmilePayBuyer(
            name='王小明',
            mobile='0912345678',
            email='test@example.com',
        ),
        roturl='https://shop.example.com/api/smilepay/roturl',
        roturl_status='ok',
    )
    print(f'訂單編號: {order.data_id}')
    print(f'金額: {order.amount}')
    print('（範例不實際 POST，避免在 sandbox 留下測試訂單；如要真打，移除 demo guard）')
    print()


def example_create_credit_redirect(service: SmilePayPaymentService) -> None:
    print('[範例 2] 信用卡一次付清結帳頁 redirect URL (Pay_zg=1)')
    print('-' * 60)
    order = SmilePayCreditOrder(
        data_id=f'ORDCC{int(time.time())}',
        amount=2500,
        item_name='測試商品 B * 1',
        buyer=SmilePayBuyer(
            name='李小華',
            mobile='0922333444',
            email='hua@example.com',
        ),
        roturl='https://shop.example.com/api/smilepay/credit_roturl?Payment_title=信用卡',
        roturl_status='ok',
    )
    result = service.create_credit_order(order)
    print(f'訂單編號: {result.data_id}')
    print(f'Redirect URL: {result.redirect_url[:120]}...')
    print(f'參數數: {len(result.params)}')
    print()


def example_create_installment(service: SmilePayPaymentService) -> None:
    print('[範例 3] 信用卡分期 (Pay_zg=1, Stage=6) 結帳頁 redirect URL')
    print('-' * 60)
    order = SmilePayInstallmentOrder(
        data_id=f'ORDINST{int(time.time())}',
        amount=12000,
        item_name='高單價商品 * 1',
        buyer=SmilePayBuyer(
            name='陳大文',
            mobile='0933555777',
            email='dawen@example.com',
        ),
        stage=6,
        roturl='https://shop.example.com/api/smilepay/credit_roturl',
        roturl_status='ok',
    )
    result = service.create_credit_installment_order(order)
    print(f'訂單編號: {result.data_id}')
    print(f'Stage: 6 期')
    print(f'Redirect URL: {result.redirect_url[:120]}...')
    print()


def example_create_barcode_order(service: SmilePayPaymentService) -> None:
    print('[範例 4] 建立超商條碼訂單 (Pay_zg=3)')
    print('-' * 60)
    order = SmilePayBarcodeOrder(
        data_id=f'ORDBAR{int(time.time())}',
        amount=600,
        item_name='測試商品 C * 1',
        buyer=SmilePayBuyer(
            name='張小美',
            mobile='0955666888',
            email='mei@example.com',
        ),
    )
    print(f'訂單編號: {order.data_id}')
    print('（範例不實際 POST，避免在 sandbox 留下測試訂單；如要真打，移除 demo guard）')
    print()


def example_verify_notification(service: SmilePayPaymentService) -> None:
    print('[範例 5] 驗證 Roturl 通知 (Mid_smilepay 校驗)')
    print('-' * 60)

    # 模擬一筆 ATM 入帳通知。先依 mid=1111 計算 Mid_smilepay 再放回去
    amount = 1500
    smseid = '2410287654'
    mid_value = service.calc_mid_smilepay(service.mid, amount, smseid)

    callback = {
        'Classif': 'B',                       # B = ATM 入帳
        'Data_id': 'ORD20260507001',
        'Smseid': smseid,
        'Amount': str(amount),
        'Process_date': '2026/05/07',
        'Process_time': '14:30:00',
        'Mid_smilepay': str(mid_value),
    }

    try:
        result = service.verify_notification(callback)
        print(f'Classif: {result.classif} (B=ATM 入帳)')
        print(f'Data_id: {result.data_id}')
        print(f'Smseid: {result.smseid}')
        print(f'Amount: {result.amount}')
        print(f'Mid_smilepay: {result.mid_smilepay}')
        print(f'驗章結果: {"通過" if result.verified else "失敗"}')
        print()
        print('回給 SmilePay:', service.build_notification_response('ok'))
    except ValueError as exc:
        print(f'通知格式錯誤: {exc}')
    print()


if __name__ == '__main__':
    print('=' * 60)
    print('SmilePay 速買配金流 - Python 範例')
    print('=' * 60)
    print()

    if not HAS_REQUESTS:
        print('（缺 requests 套件，僅執行不需 HTTP 的範例）')
        print('安裝指令: pip install requests')
        print()

    service = SmilePayPaymentService(
        dcvc=SmilePayPaymentService.TEST_DCVC,
        rvg2c=SmilePayPaymentService.TEST_RVG2C,
        verify_key=SmilePayPaymentService.TEST_VERIFY_KEY,
        mid=SmilePayPaymentService.TEST_MID,
    )

    example_create_atm_order(service)
    example_create_credit_redirect(service)
    example_create_installment(service)
    example_create_barcode_order(service)
    example_verify_notification(service)

    print('=' * 60)
    print('範例執行完成')
    print('=' * 60)
