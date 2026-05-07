#!/usr/bin/env python3
"""
新竹物流 (HCT) 直連 carrier API Python 範例

依 taiwan-logistics-skill 規範撰寫。

⚠️ 重要區分:
    - 本範例描述「直連 HCT 自家 API」(申請後使用)
    - 如僅需透過 ECPay/PayNow/SmilePay 等 aggregator 走 HCT 配送
      (LogisticsType=HCT)，請參考各 aggregator 的物流文件，無需自行串接 HCT API

⚠️ 加密:
    HCT 採自訂加解密；演算法、金鑰、IV、padding **皆於申請後由 HCT 提供 C# Sample Code**。
    本範例的 _encrypt() 為 placeholder，實際串接時須以 HCT 提供之演算法替換。

支援:
- 查貨服務（網頁串接 + XML 批次查詢）
- 出貨服務（傳入託運資料 / 修改重量 / 列印總表 / 查詢貨號 / 逆物流）

API 文件: 參見 references/hct-logistics-api.md

依賴:
    pip install requests
"""

import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional

import requests


@dataclass
class TransData:
    """傳入託運資料 (TransData)"""
    esdate: str  # 出貨日期 YYYY/MM/DD
    epino: str  # 訂單編號 (該日期內唯一)
    epdcl1: str  # 收件人姓名
    epdcl2: str  # 收件人電話
    eaddr1: str  # 收件人地址
    epname: str  # 寄件人姓名
    eptel: str  # 寄件人電話
    eaddr2: str  # 寄件人地址
    eqmny: int  # 件數
    eweight: int = 0  # 重量（kg, 整數）
    epod: Literal['1', '2'] = '1'  # 1=託運單 2=面交收據
    eshipment: str = ''  # 出貨溫層/種類
    eprdcl1: str = ''  # 商品名稱
    epaytype: Literal['0', '1', '2'] = '0'  # 0=月結 1=現付 2=代收貨款
    eamtcod: int = 0  # 代收貨款金額（epaytype=2 時）


@dataclass
class HCTResponse:
    success: bool
    decrypted_xml: str = ''
    error_message: str = ''
    raw_text: str = ''


class HCTDirectLogisticService:
    """
    HCT 新竹物流直連 API 服務.

    端點:
        - 網頁查貨:    /phone/searchGoods_Main.aspx?no=加密字串&v=xx
        - XML 批次查貨: /phone/searchGoods_Main_Xml.ashx (POST)
        - 傳入託運資料: TransData (DataSet/JSON/XML 變體)
        - 修改重量:    UpdData
        - 列印總表:    TransReport (18:00 前 must call)
        - 查詢貨號:    QueryEDELNO
        - 逆物流:      R_TransData (JSON only)

    加密金鑰: 申請後由 HCT 提供; 維護於後台「站所電腦負責人」流程。
    """

    BASE_URL = 'https://hctapiweb.hct.com.tw'
    SEARCH_BASE = 'https://hctapiweb.hct.com.tw/phone'

    def __init__(self, customer_no: str, encrypt_version: str, encryption_key: str = ''):
        """
        Args:
            customer_no: HCT 配發的客戶編號（站所提供）
            encrypt_version: URL `v=` 參數值（站所提供, e.g. 'V001'）
            encryption_key: HCT 加密金鑰（申請後提供）
        """
        self.customer_no = customer_no
        self.encrypt_version = encrypt_version
        self.encryption_key = encryption_key

    # -- 加密 / 解密（申請後依 HCT 提供之 C# Sample 替換） ----------------------

    def _encrypt(self, plaintext: str) -> str:
        """
        HCT 自訂加密.

        ⚠️ Placeholder: 申請後請依 HCT 提供之 C# Sample Code 替換。
        通常為 DES/3DES + 自訂 padding + Hex 編碼。
        """
        if not self.encryption_key:
            raise NotImplementedError(
                '請先取得 HCT 提供之加密 sample code 並替換 _encrypt() 實作'
            )
        # 真正實作會像：
        # cipher = DES.new(self.encryption_key, DES.MODE_ECB)
        # padded = pad(plaintext.encode(), 8)
        # return cipher.encrypt(padded).hex().upper()
        raise NotImplementedError('Placeholder; replace with HCT-provided algorithm')

    def _decrypt(self, ciphertext: str) -> str:
        """HCT 自訂解密（同上, placeholder）"""
        if not self.encryption_key:
            raise NotImplementedError('請先取得 HCT 提供之解密實作')
        raise NotImplementedError('Placeholder; replace with HCT-provided algorithm')

    # -- 查貨服務 -------------------------------------------------------------

    def get_search_goods_url(self, order_id: str) -> str:
        """
        產生網頁查貨 URL（單筆）.

        客戶可點此 URL 直接看到 HCT 系統內的貨況頁面。
        """
        encrypted = self._encrypt(order_id)
        return f'{self.SEARCH_BASE}/searchGoods_Main.aspx?no={encrypted}&v={self.encrypt_version}'

    def search_goods_batch(self, order_ids: List[str]) -> HCTResponse:
        """
        XML 批次查貨.

        請求 XML:
            <qrylist>
              <order orderid="1234567890"/>
              <order orderid="1234567891"/>
            </qrylist>
        """
        # 組 XML
        root = ET.Element('qrylist')
        for oid in order_ids:
            ET.SubElement(root, 'order', {'orderid': oid})
        xml_str = ET.tostring(root, encoding='unicode')

        # 加密
        encrypted = self._encrypt(xml_str)
        url = f'{self.SEARCH_BASE}/searchGoods_Main_Xml.ashx?no={encrypted}&v={self.encrypt_version}'

        try:
            r = requests.post(url, timeout=30)
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f'HCT 查貨 API 連線失敗: {e}')

        # 解密回應
        try:
            decrypted = self._decrypt(r.text)
            return HCTResponse(
                success=True,
                decrypted_xml=decrypted,
                raw_text=r.text,
            )
        except Exception as e:
            return HCTResponse(success=False, error_message=str(e), raw_text=r.text)

    # -- 出貨服務 -------------------------------------------------------------

    def trans_data(self, orders: List[TransData]) -> HCTResponse:
        """
        TransData: 傳入託運資料.

        每次最多 30 筆（含圖片時 5 筆）。
        建立後須於當日 18:00 前呼叫 TransReport 否則無法列印託運單。
        """
        # 組成 XML 或 JSON（HCT 支援 DataSet/XML/JSON 三種變體）
        # 以 JSON 變體為例：
        body = {
            'CustomerNo': self.customer_no,
            'TransData': [
                {
                    'esdate': o.esdate,
                    'epino': o.epino,
                    'epdcl1': o.epdcl1,
                    'epdcl2': o.epdcl2,
                    'eaddr1': o.eaddr1,
                    'epname': o.epname,
                    'eptel': o.eptel,
                    'eaddr2': o.eaddr2,
                    'eqmny': o.eqmny,
                    'eweight': o.eweight,
                    'epod': o.epod,
                    'eshipment': o.eshipment,
                    'eprdcl1': o.eprdcl1,
                    'epaytype': o.epaytype,
                    'eamtcod': o.eamtcod,
                } for o in orders
            ],
        }
        # 加密 + POST（端點/路徑申請後由 HCT 提供）
        # url = self.BASE_URL + '/api/TransData'
        # encrypted = self._encrypt(json.dumps(body))
        # r = requests.post(url, data={'data': encrypted, 'v': self.encrypt_version})
        # 此處僅展示架構，實際端點/欄位以 HCT 文件為準
        return HCTResponse(success=False, error_message='HCT TransData endpoint 申請後提供')

    def trans_report(self, esdate: str, epinos: List[str]) -> HCTResponse:
        """
        TransReport: 列印託運單總表.

        ⚠️ 必須於出貨日當日 18:00 前呼叫，否則包裹無法配送。
        """
        return HCTResponse(success=False, error_message='HCT TransReport endpoint 申請後提供')

    def upd_data(self, esdate: str, epino: str, new_weight: int) -> HCTResponse:
        """UpdData: 修改重量"""
        return HCTResponse(success=False, error_message='HCT UpdData endpoint 申請後提供')

    def query_edelno(self, esdate: str, epino: str) -> HCTResponse:
        """QueryEDELNO: 查詢貨號"""
        return HCTResponse(success=False, error_message='HCT QueryEDELNO endpoint 申請後提供')

    def r_trans_data(self, orders: List[TransData]) -> HCTResponse:
        """
        R_TransData: 逆物流託運（JSON only, 沒有 XML/DataSet 變體）.
        """
        return HCTResponse(success=False, error_message='HCT R_TransData endpoint 申請後提供')


# ============================================================================
# Examples
# ============================================================================

def example_search_url():
    print('=== HCT 網頁查貨 URL ===\n')
    print('注意: 此範例需要 HCT 提供加密 sample code 才能跑。\n')
    svc = HCTDirectLogisticService(
        customer_no='YOUR_CUSTOMER_NO',
        encrypt_version='V001',
        encryption_key='YOUR_HCT_KEY',  # 申請後取得
    )
    try:
        url = svc.get_search_goods_url(order_id='1234567890')
        print(f'查貨 URL: {url}')
    except NotImplementedError as e:
        print(f'[expected] {e}')


def example_batch_search():
    print('\n=== HCT XML 批次查貨 ===\n')
    svc = HCTDirectLogisticService('YOUR_CUSTOMER_NO', 'V001', 'YOUR_HCT_KEY')
    try:
        resp = svc.search_goods_batch(['1234567890', '1234567891'])
        if resp.success:
            print(f'解密 XML:\n{resp.decrypted_xml[:500]}')
        else:
            print(f'[FAIL] {resp.error_message}')
    except NotImplementedError as e:
        print(f'[expected] {e}')


def example_trans_data():
    print('\n=== HCT TransData 傳入託運資料 ===\n')
    svc = HCTDirectLogisticService('YOUR_CUSTOMER_NO', 'V001', 'YOUR_HCT_KEY')
    orders = [
        TransData(
            esdate='2026/05/07',
            epino=f'ORD{int(time.time())}',
            epdcl1='王小明',
            epdcl2='0912345678',
            eaddr1='台北市信義區信義路五段7號',
            epname='店家',
            eptel='02-27000000',
            eaddr2='台北市大安區忠孝東路四段1號',
            eqmny=1,
            eweight=2,
            eshipment='常溫',
            eprdcl1='測試商品',
            epaytype='2',  # 代收貨款
            eamtcod=1500,
        )
    ]
    resp = svc.trans_data(orders)
    print(f'結果: success={resp.success} message={resp.error_message}')


if __name__ == '__main__':
    example_search_url()
    example_batch_search()
    example_trans_data()
