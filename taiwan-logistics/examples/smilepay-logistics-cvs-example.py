#!/usr/bin/env python3
"""
SmilePay 速買配物流 Python 範例

依 taiwan-logistics-skill 規範撰寫。
SmilePay 物流以 Pay_zg + Pay_subzg 編碼涵蓋:
  C2C_COD=51, C2C_PICKUP=52, B2C_COD=55, B2C_PICKUP=56
  TCAT_COD=81, TCAT_PICKUP=82, RETCAT=83
  Pay_subzg=7NET (7-11), FAMI (全家)

支援:
- 7-11 / 全家 C2C+B2C 取貨付款 / 取貨不付款
- 黑貓宅急便 COD / PICKUP / 逆物流
- 電子地圖選店 (LogisticsEmap)
- 列印託運單

API 文件: 參見 references/smilepay-logistics-api.md

依賴:
    pip install requests
"""

import time
from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional

import requests


@dataclass
class CvsLogisticOrder:
    """7-11 / 全家 取貨訂單"""
    data_id: str  # 訂單編號 (唯一, 30 字內)
    amount: int  # 金額（COD 才有意義）
    pur_name: str  # 收件人姓名
    pur_telno: str  # 收件人電話
    address: str = ''  # 收件地址
    email: str = ''
    od_sob: str = ''  # 商品名稱
    roturl: str = ''  # 通知 URL
    cvs_provider: Literal['7NET', 'FAMI'] = '7NET'  # 7-11 or FAMI
    is_b2c: bool = False
    is_cod: bool = True


@dataclass
class TcatLogisticOrder:
    """黑貓宅急便訂單"""
    data_id: str
    amount: int  # COD 才有意義
    pur_name: str
    pur_telno: str
    address: str
    od_sob: str = ''
    roturl: str = ''
    is_cod: bool = True
    temperature: Literal['1', '2', '3'] = '1'  # 1=常溫 2=冷藏 3=冷凍
    is_reverse: bool = False  # 逆物流 (Pay_zg=83)


@dataclass
class SmilePayLogisticResponse:
    success: bool
    status: str = ''
    desc: str = ''
    paymentno: str = ''  # SmilePay 內部編號
    smseid: str = ''  # 物流商編號
    storeid: str = ''  # 門市編號
    storename: str = ''
    raw: Dict[str, any] = field(default_factory=dict)


class SmilePayLogisticService:
    """
    SmilePay 物流服務.

    認證: Dcvc + Verify_key（與金流端相同）
    端點:
        - 7-11/全家 C2C 取號:  /api/C2CPayment.asp
        - 7-11/全家 B2C 取號:  /api/B2CPayment.asp
        - 黑貓取號:           /api/ezcatGetTrackNum.asp
        - 黑貓列印:           /api/ezcatPrintDelivery.asp
        - 超商列印 B2C:       /api/B2C_MultiplePrint.asp
        - 超商列印 C2B:       /api/C2BPayment.asp
        - 電子地圖選店:        /api/LogisticsEmap.asp
        - 修改:               /api/SPPayment_Modify.asp

    Pay_zg 矩陣（從 PHP plugin 反推）:
        51 = C2C COD, 52 = C2C PICKUP
        55 = B2C COD, 56 = B2C PICKUP
        81 = TCAT COD, 82 = TCAT PICKUP, 83 = TCAT 逆物流
    """

    BASE_URL = 'https://ssl.smse.com.tw/api'
    EMAP_URL = 'https://ssl.smse.com.tw/api/LogisticsEmap.asp'

    # Pay_zg constants
    C2C_COD_PAY_ZG = 51
    C2C_PICKUP_PAY_ZG = 52
    B2C_COD_PAY_ZG = 55
    B2C_PICKUP_PAY_ZG = 56
    TCAT_COD_PAY_ZG = 81
    TCAT_PICKUP_PAY_ZG = 82
    RETCAT_PAY_ZG = 83

    def __init__(self, dcvc: str, verify_key: str, rvg2c: str = '1'):
        self.dcvc = dcvc
        self.verify_key = verify_key
        self.rvg2c = rvg2c

    # -- 7-11 / 全家 取號 -----------------------------------------------------

    def create_cvs_order(self, order: CvsLogisticOrder) -> SmilePayLogisticResponse:
        """建立 7-11 / 全家 物流訂單"""
        # 決定 Pay_zg
        if order.is_b2c:
            pay_zg = self.B2C_COD_PAY_ZG if order.is_cod else self.B2C_PICKUP_PAY_ZG
            endpoint = '/B2CPayment.asp'
        else:
            pay_zg = self.C2C_COD_PAY_ZG if order.is_cod else self.C2C_PICKUP_PAY_ZG
            endpoint = '/C2CPayment.asp'

        body = {
            'Dcvc': self.dcvc,
            'Rvg2c': self.rvg2c,
            'Verify_key': self.verify_key,
            'Pay_zg': str(pay_zg),
            'Pay_subzg': order.cvs_provider,  # 7NET / FAMI
            'Data_id': order.data_id,
            'Amount': str(order.amount) if order.is_cod else '0',
            'Pur_name': order.pur_name,
            'Pur_telno': order.pur_telno,
            'Address': order.address,
            'Email': order.email,
            'od_sob': order.od_sob,
            'Roturl': order.roturl,
        }
        return self._submit(self.BASE_URL + endpoint, body)

    # -- 黑貓宅急便 -----------------------------------------------------------

    def create_tcat_order(self, order: TcatLogisticOrder) -> SmilePayLogisticResponse:
        """建立黑貓宅急便訂單（COD / PICKUP / 逆物流）"""
        if order.is_reverse:
            pay_zg = self.RETCAT_PAY_ZG
        elif order.is_cod:
            pay_zg = self.TCAT_COD_PAY_ZG
        else:
            pay_zg = self.TCAT_PICKUP_PAY_ZG

        body = {
            'Dcvc': self.dcvc,
            'Rvg2c': self.rvg2c,
            'Verify_key': self.verify_key,
            'Pay_zg': str(pay_zg),
            'Data_id': order.data_id,
            'Amount': str(order.amount) if order.is_cod else '0',
            'Pur_name': order.pur_name,
            'Pur_telno': order.pur_telno,
            'Address': order.address,
            'od_sob': order.od_sob,
            'Roturl': order.roturl,
            'Temperature': order.temperature,  # 1常溫 2冷藏 3冷凍
        }
        return self._submit(self.BASE_URL + '/ezcatGetTrackNum.asp', body)

    # -- 電子地圖選店 ---------------------------------------------------------

    def get_emap_url(
        self,
        types_server: Literal['711C2C', 'FAMIC2C', '711B2C', 'FAMIB2C'],
        return_url: str,
        types_interface: Literal['MOBILE', 'WEB'] = 'WEB',
    ) -> str:
        """取得電子地圖選店 URL（讓客戶於 SmilePay 託管頁選擇取貨門市）"""
        params = f'Dcvc={self.dcvc}&TypesServer={types_server}&TypesInterface={types_interface}&RtURL={return_url}'
        return f'{self.EMAP_URL}?{params}'

    # -- HTTP submit ----------------------------------------------------------

    def _submit(self, url: str, body: Dict[str, any]) -> SmilePayLogisticResponse:
        try:
            r = requests.post(url, data=body, timeout=30)
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f'SmilePay API 連線失敗: {e}')

        # SmilePay 回應為 XML; 簡易 parse
        import xml.etree.ElementTree as ET
        try:
            root = ET.fromstring(r.text)
            status = root.findtext('Status', '')
            desc = root.findtext('Desc', '')
            paymentno = root.findtext('PaymentNo', '')
            smseid = root.findtext('Smseid', '')
            storeid = root.findtext('Storeid', '')
            storename = root.findtext('Storename', '')
            return SmilePayLogisticResponse(
                success=(status == '1'),
                status=status,
                desc=desc,
                paymentno=paymentno,
                smseid=smseid,
                storeid=storeid,
                storename=storename,
                raw={'text': r.text},
            )
        except ET.ParseError:
            return SmilePayLogisticResponse(
                success=False,
                desc=f'XML parse 失敗: {r.text[:200]}',
            )


# ============================================================================
# Examples
# ============================================================================

def example_711_cvs_cod():
    print('=== SmilePay 7-11 C2C COD ===\n')
    svc = SmilePayLogisticService(dcvc='107', verify_key='174A02F97A95F72CE301137B3F98D128')
    order = CvsLogisticOrder(
        data_id=f'ORD{int(time.time())}',
        amount=1500,
        pur_name='王小明',
        pur_telno='0912345678',
        email='test@example.com',
        od_sob='測試商品',
        roturl='https://your-shop.com/api/smilepay/notify',
        cvs_provider='7NET',
        is_b2c=False,
        is_cod=True,
    )
    resp = svc.create_cvs_order(order)
    if resp.success:
        print(f'[OK] PaymentNo={resp.paymentno} 物流編號={resp.smseid}')
    else:
        print(f'[FAIL] {resp.status}: {resp.desc}')


def example_tcat_frozen_cod():
    print('\n=== SmilePay 黑貓冷凍 COD ===\n')
    svc = SmilePayLogisticService(dcvc='107', verify_key='174A02F97A95F72CE301137B3F98D128')
    order = TcatLogisticOrder(
        data_id=f'ORD{int(time.time())}',
        amount=2000,
        pur_name='王小明',
        pur_telno='0912345678',
        address='台北市信義區信義路五段7號',
        od_sob='生鮮食品',
        roturl='https://your-shop.com/api/smilepay/notify',
        is_cod=True,
        temperature='3',  # 冷凍
    )
    resp = svc.create_tcat_order(order)
    if resp.success:
        print(f'[OK] PaymentNo={resp.paymentno} 黑貓編號={resp.smseid}')
    else:
        print(f'[FAIL] {resp.status}: {resp.desc}')


def example_tcat_reverse():
    print('\n=== SmilePay 黑貓逆物流（退貨）===\n')
    svc = SmilePayLogisticService(dcvc='107', verify_key='174A02F97A95F72CE301137B3F98D128')
    order = TcatLogisticOrder(
        data_id=f'RTN{int(time.time())}',
        amount=0,  # 逆物流不收 COD
        pur_name='王小明',
        pur_telno='0912345678',
        address='台北市信義區信義路五段7號',
        od_sob='退貨商品',
        roturl='https://your-shop.com/api/smilepay/return-notify',
        is_cod=False,
        is_reverse=True,  # Pay_zg=83
    )
    resp = svc.create_tcat_order(order)
    if resp.success:
        print(f'[OK] 逆物流取號成功 PaymentNo={resp.paymentno}')
    else:
        print(f'[FAIL] {resp.status}: {resp.desc}')


def example_emap():
    print('\n=== SmilePay 電子地圖選店 ===\n')
    svc = SmilePayLogisticService(dcvc='107', verify_key='174A02F97A95F72CE301137B3F98D128')
    url = svc.get_emap_url(
        types_server='711C2C',
        return_url='https://your-shop.com/checkout/store-selected',
        types_interface='WEB',
    )
    print(f'導轉至:\n{url}')


if __name__ == '__main__':
    example_711_cvs_cod()
    example_tcat_frozen_cod()
    example_tcat_reverse()
    example_emap()
