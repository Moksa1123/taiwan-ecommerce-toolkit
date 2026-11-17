#!/usr/bin/env python3
"""
新竹物流 (HCT) 直連 carrier API Python 範例

重要區分:
    - 本範例描述「直連 HCT 自家 API」(申請後使用)
    - 本 skill 收錄的聚合商官方規格都沒有新竹物流選項，要用 HCT 只能直連

兩組服務:
    - 查貨服務（hctapiweb.hct.com.tw）：HCT 自訂加解密；演算法、金鑰於申請後由 HCT 提供
      C# Sample Code。本範例的 _encrypt() / _decrypt() 為 placeholder。
    - 出貨服務（EDI Web Service，SOAP）：https://hctrt.hct.com.tw/EDI_WebService2/Service1.asmx
      以 company / password 登入（TransReport 為 sCompany / sPassword），不加密。
      方法名與參數名區分大小寫，以 WSDL 為準（TransData_Xml，不是 _XML）。
      官方測試帳號 test / test1（正式系統，勿上傳真實資料）。

支援:
- 查貨服務（網頁串接 + XML 批次查詢）
- 出貨服務（傳入託運資料 / 修改重量 / 列印總表 / 查詢貨號 / 逆物流）

API 文件: 參見 references/hct-logistics-api.md

依賴:
    pip install requests
"""

import json
import time
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from typing import List, Literal, Tuple
from xml.sax.saxutils import escape

import requests


@dataclass
class TransData:
    """傳入託運資料 (TransData)，欄位依《新竹物流 API 服務說明》ver 2.0 p.10"""
    epino: str  # 訂單編號 Char(30)，同一 esdate 不可重複
    ercsig: str  # 收貨人名稱 Char(40)
    ertel1: str  # 收貨人電話 Char(15)
    eraddr: str  # 收貨人地址 Char(100)
    ejamt: int = 1  # 件數，最小 1
    eqamt: int = 1  # 重量，小數進位到整數
    esdate: str = ''  # 出貨日期 YYYYMMDD，空白為今天
    etcsig: str = ''  # 出貨人名稱（空白用帳號預設值）
    ettel1: str = ''  # 出貨人電話
    etaddr: str = ''  # 出貨地址
    eqmny: int = 0  # 代收貨款
    eprdct: Literal['11', '21', '31'] = '11'  # 傳票類別 11 月結／21 到付／31 現收
    eprdcl2: Literal['001', '003', '008'] = '001'  # 001 一般／003 冷凍／008 冷藏
    emark: str = ''  # 備註


@dataclass
class HCTResponse:
    success: bool
    decrypted_xml: str = ''
    error_message: str = ''
    raw_text: str = ''
    rows: List[dict] = None  # 出貨服務 *_Json 回傳的陣列


class HCTDirectLogisticService:
    """
    HCT 新竹物流直連 API 服務.

    端點:
        - 網頁查貨:    /phone/searchGoods_Main.aspx?no=加密字串&v=xx
        - XML 批次查貨: /phone/searchGoods_Main_Xml.ashx (POST)
        - 出貨 SOAP:   https://hctrt.hct.com.tw/EDI_WebService2/Service1.asmx
            TransData_Json / UpdData_Json / TransReport_Json（18:00 前）/
            QueryEDELNO_Json / R_TransData_Json

    查貨加密金鑰: 申請後由 HCT 提供。
    """

    SEARCH_BASE = 'https://hctapiweb.hct.com.tw/phone'
    EDI_URL = 'https://hctrt.hct.com.tw/EDI_WebService2/Service1.asmx'
    SOAP_NS = 'http://tempuri.org/'

    def __init__(self, company: str, password: str, encrypt_version: str = '', encryption_key: str = ''):
        """
        Args:
            company / password: 出貨 API 帳密（站所提供；測試 test / test1）
            encrypt_version: 查貨 URL `v=` 參數值（申請後提供）
            encryption_key: 查貨加密金鑰（申請後提供）
        """
        self.company = company
        self.password = password
        self.encrypt_version = encrypt_version
        self.encryption_key = encryption_key

    # -- 加密 / 解密（申請後依 HCT 提供之 C# Sample 替換） ----------------------

    def _encrypt(self, plaintext: str) -> str:
        """
        HCT 自訂加密.

        Placeholder: 申請後請依 HCT 提供之 C# Sample Code 替換。
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

    # -- 出貨服務（SOAP）-------------------------------------------------------

    def _soap(self, method: str, params: List[Tuple[str, str]]) -> HCTResponse:
        """呼叫 Service1.asmx 的 *_Json 方法；參數名區分大小寫"""
        inner = ''.join(f'<{k}>{escape(v)}</{k}>' for k, v in params)
        envelope = (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">'
            f'<soap:Body><{method} xmlns="{self.SOAP_NS}">{inner}</{method}></soap:Body>'
            '</soap:Envelope>'
        )
        headers = {
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': f'"{self.SOAP_NS}{method}"',
        }
        try:
            r = requests.post(self.EDI_URL, data=envelope.encode('utf-8'), headers=headers, timeout=60)
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f'HCT 出貨 API 連線失敗: {e}')
        if r.status_code != 200:
            # 方法名寫錯：HTTP 500 SOAP Fault「伺服器無法辨認 HTTP 標頭 SOAPAction 的值」
            return HCTResponse(success=False, error_message=f'HTTP {r.status_code}', raw_text=r.text)
        result = ET.fromstring(r.content).find(f'.//{{{self.SOAP_NS}}}{method}Result')
        rows = json.loads(result.text) if result is not None and result.text else []
        ok = bool(rows) and all(str(row.get('success') or row.get('Success')) in ('Y', 'R') for row in rows)
        errors = '; '.join(str(row.get('ErrMsg')) for row in rows if row.get('ErrMsg'))
        return HCTResponse(success=ok, error_message=errors, raw_text=r.text, rows=rows)

    def trans_data(self, orders: List[TransData]) -> HCTResponse:
        """
        TransData_Json: 傳入託運資料，回傳新竹貨號 edelno 與到著站 erstno.

        每次最多 30 筆（含圖片時 5 筆）。當日出貨須於 18:00 前呼叫 TransReport。
        """
        payload = []
        for o in orders:
            row = {k: str(v) for k, v in asdict(o).items() if v not in ('', None)}
            payload.append(row)
        return self._soap('TransData_Json', [
            ('company', self.company), ('password', self.password),
            ('json', json.dumps(payload, ensure_ascii=False)),
        ])

    def trans_report(self, rows: List[Tuple[str, str]]) -> HCTResponse:
        """TransReport_Json: 確認當日出貨（列印總表）。rows = [(epino, edelno), ...]"""
        payload = [{'epino': epino, 'edelno': edelno} for epino, edelno in rows]
        return self._soap('TransReport_Json', [
            ('sCompany', self.company), ('sPassword', self.password),
            ('dsCusJson', json.dumps(payload)),
        ])

    def upd_data(self, epino: str, edelno: str, eqamt: int) -> HCTResponse:
        """UpdData_Json: 修改重量"""
        payload = [{'epino': epino, 'edelno': edelno, 'eqamt': str(eqamt)}]
        return self._soap('UpdData_Json', [
            ('company', self.company), ('password', self.password),
            ('json', json.dumps(payload)),
        ])

    def query_edelno(self, epinos: List[str]) -> HCTResponse:
        """QueryEDELNO_Json: 以訂單編號查新竹貨號（裸字串會回「資料錯誤請確認」）"""
        payload = [{'epino': ','.join(epinos)}]
        return self._soap('QueryEDELNO_Json', [
            ('company', self.company), ('password', self.password),
            ('json', json.dumps(payload)),
        ])

    def r_trans_data(self, rows: List[dict]) -> HCTResponse:
        """
        R_TransData_Json: 逆物流託運（JSON only）.

        rows 欄位: epino, ercsig（退貨人）, ertel1, eraddr, ejamt=1, eqamt, edelno2（原貨號）…
        """
        return self._soap('R_TransData_Json', [
            ('company', self.company), ('password', self.password),
            ('json', json.dumps(rows, ensure_ascii=False)),
        ])


# ============================================================================
# Examples
# ============================================================================

def example_search_url():
    print('=== HCT 網頁查貨 URL ===\n')
    print('注意: 此範例需要 HCT 提供加密 sample code 才能跑。\n')
    svc = HCTDirectLogisticService(
        company='test',
        password='test1',
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
    svc = HCTDirectLogisticService('test', 'test1', 'V001', 'YOUR_HCT_KEY')
    try:
        resp = svc.search_goods_batch(['1234567890', '1234567891'])
        if resp.success:
            print(f'解密 XML:\n{resp.decrypted_xml[:500]}')
        else:
            print(f'[FAIL] {resp.error_message}')
    except NotImplementedError as e:
        print(f'[expected] {e}')


def example_trans_data():
    print('\n=== HCT TransData 傳入託運資料（建立的是測試帳號資料）===\n')
    svc = HCTDirectLogisticService('test', 'test1')
    orders = [
        TransData(
            epino=f'ORD{int(time.time())}',
            ercsig='王小明',
            ertel1='0912345678',
            eraddr='台北市信義區信義路五段7號',
            ejamt=1,
            eqamt=2,
            eqmny=1500,  # 代收貨款
            eprdcl2='001',
        )
    ]
    resp = svc.trans_data(orders)
    print(f'結果: success={resp.success} rows={resp.rows} message={resp.error_message}')


if __name__ == '__main__':
    example_search_url()
    example_batch_search()
    example_trans_data()
