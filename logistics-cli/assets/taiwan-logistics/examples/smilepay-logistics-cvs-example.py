#!/usr/bin/env python3
"""
SmilePay 速買配物流 Python 範例

SmilePay 物流以 Pay_zg + Pay_subzg 編碼涵蓋:
  C2C_COD=51, C2C_PICKUP=52, B2C_COD=55, B2C_PICKUP=56
  TCAT_COD=81, TCAT_PICKUP=82, RETCAT=83
  Pay_subzg=7NET (7-11), FAMI (全家), TCAT (黑貓)

取號一律兩階段:
  1. POST /api/SPPayment.asp 建單，取得 SmilePayNO
  2. 以 smseid=SmilePayNO 呼叫各產品端點取實際物流編號
     C2C: C2CPayment.asp（取貨付款）/ C2CPaymentU.asp（純取貨）
     B2C: B2CPayment.asp
     黑貓: ezcatGetTrackNum.asp
  直接打第二階段端點會回 -1001（ID Error / Input Data Error）。

支援:
- 7-11 C2C+B2C、全家 C2C 取貨付款 / 取貨不付款
- 黑貓宅急便 COD / PICKUP / 逆物流
- 電子地圖選店 (LogisticsEmap)

API 文件: 參見 references/smilepay-logistics-api.md

依賴:
    pip install requests
"""

import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Dict, Literal
from urllib.parse import quote

import requests


@dataclass
class CvsLogisticOrder:
    """7-11 / 全家 取貨訂單"""
    data_id: str  # 訂單編號 (唯一)
    amount: int  # 訂單金額
    pur_name: str  # 取貨人姓名
    pur_telno: str  # 取貨人電話（送 Tel_number / Mobile_number）
    store_id: str  # 電子地圖回傳的 storeid
    store_name: str
    store_address: str
    email: str = ''
    od_sob: str = ''  # 商品名稱（CVS 35 字內）
    logistics_roturl: str = ''  # 貨況通知網址 Logistics_Roturl
    cvs_provider: Literal['7NET', 'FAMI'] = '7NET'  # 全家只有 C2C
    is_b2c: bool = False
    is_cod: bool = True


@dataclass
class TcatLogisticOrder:
    """黑貓宅急便訂單"""
    data_id: str
    amount: int
    pur_name: str
    pur_telno: str
    address: str
    od_sob: str = ''  # 商品名稱（45 字內）
    logistics_roturl: str = ''
    is_cod: bool = True
    temperature: Literal['0001', '0002', '0003'] = '0001'  # 常溫 / 冷藏 / 冷凍
    package_size: Literal['0001', '0002', '0003', '0004'] = '0001'  # 60/90/120/150 cm
    is_reverse: bool = False  # 逆物流 (Pay_zg=83)


@dataclass
class SmilePayLogisticResponse:
    success: bool
    status: str = ''
    desc: str = ''
    smilepay_no: str = ''  # 第一階段 SmilePayNO
    paymentno: str = ''  # C2C 交貨便號碼 = paymentno + validationno
    eshop_order_no: str = ''  # B2C 大宗寄倉編號（查詢碼前加 766）
    track_num: str = ''  # 黑貓託運單號
    storeid: str = ''
    storename: str = ''
    raw: Dict[str, str] = field(default_factory=dict)


class SmilePayLogisticService:
    """
    SmilePay 物流服務.

    認證: Dcvc + Rvg2c + Verify_key（與金流端相同，無簽章）
    端點:
        - 建單:                /api/SPPayment.asp
        - 7-11/全家 C2C 取號:  /api/C2CPayment.asp、/api/C2CPaymentU.asp
        - 7-11 B2C 取號:      /api/B2CPayment.asp
        - 黑貓取號:           /api/ezcatGetTrackNum.asp
        - 電子地圖選店:        /api/LogisticsEmap.asp
        - 修改:               /api/SPPayment_Modify.asp
    """

    BASE_URL = 'https://ssl.smse.com.tw/api'
    EMAP_URL = 'https://ssl.smse.com.tw/api/LogisticsEmap.asp'

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

    def _auth(self) -> Dict[str, str]:
        return {'Dcvc': self.dcvc, 'Rvg2c': self.rvg2c, 'Verify_key': self.verify_key}

    # -- 7-11 / 全家 取號 -----------------------------------------------------

    def create_cvs_order(self, order: CvsLogisticOrder) -> SmilePayLogisticResponse:
        """建立 7-11 / 全家 物流訂單並取交貨便號碼"""
        if order.is_b2c:
            pay_zg = self.B2C_COD_PAY_ZG if order.is_cod else self.B2C_PICKUP_PAY_ZG
        else:
            pay_zg = self.C2C_COD_PAY_ZG if order.is_cod else self.C2C_PICKUP_PAY_ZG

        body = {
            **self._auth(),
            'Pay_zg': str(pay_zg),
            'Pay_subzg': order.cvs_provider,
            'Data_id': order.data_id,
            'Amount': str(order.amount),
            'Pur_name': order.pur_name,
            'Tel_number': order.pur_telno,
            'Mobile_number': order.pur_telno,
            'Email': order.email,
            'od_sob': order.od_sob,
            'Logistics_store': f'{order.store_id}/{order.store_name}/{order.store_address}',
            'Logistics_Roturl': order.logistics_roturl,
        }
        first = self._submit('/SPPayment.asp', body)
        if not first.success:
            return first

        if order.is_b2c:
            second = self._submit('/B2CPayment.asp', {
                'Dcvc': self.dcvc, 'Verify_key': self.verify_key, 'smseid': first.smilepay_no,
            })
        else:
            endpoint = '/C2CPayment.asp' if order.is_cod else '/C2CPaymentU.asp'
            second = self._submit(endpoint, {
                'Dcvc': self.dcvc, 'Verify_key': self.verify_key, 'smseid': first.smilepay_no,
                'Pay_subzg': order.cvs_provider, 'types': 'Xml',
            })
        second.smilepay_no = first.smilepay_no
        return second

    # -- 黑貓宅急便 -----------------------------------------------------------

    def create_tcat_order(self, order: TcatLogisticOrder) -> SmilePayLogisticResponse:
        """建立黑貓宅急便訂單（COD / PICKUP / 逆物流）並取託運單號"""
        if order.is_reverse:
            pay_zg = self.RETCAT_PAY_ZG
        elif order.is_cod:
            pay_zg = self.TCAT_COD_PAY_ZG
        else:
            pay_zg = self.TCAT_PICKUP_PAY_ZG

        body = {
            **self._auth(),
            'Pay_zg': str(pay_zg),
            'Pay_subzg': 'TCAT',
            'Data_id': order.data_id,
            'Amount': str(order.amount),
            'Pur_name': order.pur_name,
            'Tel_number': order.pur_telno,
            'Mobile_number': order.pur_telno,
            'Address': order.address,
            'od_sob': order.od_sob,
            'Logistics_Roturl': order.logistics_roturl,
            'temperature': order.temperature,  # 4.3.3 外掛在第一階段送
        }
        first = self._submit('/SPPayment.asp', body)
        if not first.success:
            return first

        second = self._submit('/ezcatGetTrackNum.asp', {
            'Dcvc': self.dcvc, 'Verify_key': self.verify_key, 'smseid': first.smilepay_no,
            'package_size': order.package_size,
        })
        second.smilepay_no = first.smilepay_no
        return second

    # -- 電子地圖選店 ---------------------------------------------------------

    def get_emap_url(
        self,
        types_server: Literal['711C2C', 'FAMIC2C', '711B2C'],
        return_url: str,
        tempvar: str = '',
        types_interface: Literal['MOBILE', 'WEB'] = 'WEB',
    ) -> str:
        """取得電子地圖選店 URL；選完後以全小寫 storeid/storename/storeaddress/typesserver 回到 return_url"""
        return (f'{self.EMAP_URL}?method=GET&TypesServer={types_server}'
                f'&TypesInterface={types_interface}&tempvar={quote(tempvar)}'
                f'&url={quote(return_url, safe="")}')

    # -- HTTP submit ----------------------------------------------------------

    def _submit(self, path: str, body: Dict[str, str]) -> SmilePayLogisticResponse:
        try:
            r = requests.post(self.BASE_URL + path, data=body, timeout=30)
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f'SmilePay API 連線失敗: {e}')

        # ezcatGetTrackNum.asp、B2C_MultiplePrint.asp 參數錯誤時回 HTTP 500 HTML
        if r.status_code != 200 or not r.text.lstrip().startswith('<?xml'):
            return SmilePayLogisticResponse(success=False, desc=f'HTTP {r.status_code}: {r.text[:200]}')

        try:
            root = ET.fromstring(r.content)
        except ET.ParseError:
            return SmilePayLogisticResponse(success=False, desc=f'XML parse 失敗: {r.text[:200]}')

        def t(tag: str) -> str:
            return (root.findtext(tag) or '').strip()

        status = t('Status')
        return SmilePayLogisticResponse(
            success=(status == '1'),
            status=status,
            desc=t('Desc'),
            smilepay_no=t('SmilePayNO'),
            paymentno=t('paymentno') + t('validationno'),
            eshop_order_no=t('EshopOrderNo'),
            track_num=t('TrackNum'),
            storeid=t('storeid') or t('Storeid'),
            storename=t('storename') or t('StoreName'),
            raw={'root': root.tag, 'text': r.text},
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
        store_id='131386',
        store_name='雙子星門市',
        store_address='台北市信義區',
        email='test@example.com',
        od_sob='測試商品',
        logistics_roturl='https://your-shop.com/api/smilepay/logistics-status',
        cvs_provider='7NET',
        is_b2c=False,
        is_cod=True,
    )
    resp = svc.create_cvs_order(order)
    if resp.success:
        print(f'[OK] SmilePayNO={resp.smilepay_no} 交貨便號碼={resp.paymentno}')
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
        logistics_roturl='https://your-shop.com/api/smilepay/logistics-status',
        is_cod=True,
        temperature='0003',  # 冷凍（冷藏、冷凍尺寸上限 120 cm）
        package_size='0002',
    )
    resp = svc.create_tcat_order(order)
    if resp.success:
        print(f'[OK] SmilePayNO={resp.smilepay_no} 黑貓託運單號={resp.track_num}')
    else:
        print(f'[FAIL] {resp.status}: {resp.desc}')


def example_tcat_reverse():
    print('\n=== SmilePay 黑貓逆物流（退貨）===\n')
    svc = SmilePayLogisticService(dcvc='107', verify_key='174A02F97A95F72CE301137B3F98D128')
    order = TcatLogisticOrder(
        data_id=f'RTN{int(time.time())}',
        amount=0,
        pur_name='王小明',
        pur_telno='0912345678',
        address='台北市信義區信義路五段7號',
        od_sob='退貨商品',
        logistics_roturl='https://your-shop.com/api/smilepay/return-status',
        is_cod=False,
        is_reverse=True,  # Pay_zg=83
    )
    resp = svc.create_tcat_order(order)
    if resp.success:
        print(f'[OK] 逆物流取號成功 TrackNum={resp.track_num}')
    else:
        print(f'[FAIL] {resp.status}: {resp.desc}')


def example_emap():
    print('\n=== SmilePay 電子地圖選店 ===\n')
    svc = SmilePayLogisticService(dcvc='107', verify_key='174A02F97A95F72CE301137B3F98D128')
    url = svc.get_emap_url(
        types_server='711C2C',
        return_url='https://your-shop.com/checkout/store-selected',
        tempvar='order_123',
        types_interface='WEB',
    )
    print(f'導轉至:\n{url}')


if __name__ == '__main__':
    example_711_cvs_cod()
    example_tcat_frozen_cod()
    example_tcat_reverse()
    example_emap()
