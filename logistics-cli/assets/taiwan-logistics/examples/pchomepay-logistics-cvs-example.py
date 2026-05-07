#!/usr/bin/env python3
"""
PChomePay 拍錢包物流 Python 範例

依 taiwan-logistics-skill 規範撰寫。
PChomePay 物流走 7-11 / 全家 / 萊爾富 / OK 四大超商，金物流二合一設計。

支援:
- 取號列印交寄單 (/v1/logistic/batch)
- 物流歷程查詢 (/v1/logistic/query/{order_id}/history)
- 未出貨/未取貨查詢 (/v1/logistic/yet, /v1/logistic/store_return/{date})
- 物流手續費對帳 (/v1/logistic/accounting/{date} - NDJSON 格式)
- 賠款入帳查詢 (/v1/logistic/compensation/{date})

⚠️ Notify IP 白名單: 113.196.231.190（必加）

API 文件: 參見 references/pchomepay-logistics-api.md

依賴:
    pip install requests
"""

import json
import time
from base64 import b64encode
from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional

import requests


@dataclass
class LogisticBatchRequest:
    """取號列印交寄單"""
    order_id: str  # 商家訂單編號（與金流訂單關聯）
    store_id: str  # 取貨門市編號
    return_store_id: str = ''  # 退貨門市
    name: str = ''  # 收件人
    phone: str = ''
    address: str = ''
    email: str = ''


@dataclass
class PChomePayResponse:
    success: bool
    code: str = ''
    message: str = ''
    data: Dict[str, any] = field(default_factory=dict)
    raw: Dict[str, any] = field(default_factory=dict)


class PChomePayLogisticService:
    """
    PChomePay 物流服務.

    認證: 兩段式
      1. HTTP Basic Auth (APP_ID + SECRET) → /v1/token
      2. 後續 API 帶 `pcpay-token` header (8 小時有效)

    Logistic types:
        PL711  = 7-11
        PLFMI  = 全家 (FamilyMart)
        PLHIL  = 萊爾富 (Hi-Life)
        PLOK   = OK 超商
    """

    SANDBOX_BASE = 'https://sandbox-api.pchomepay.com.tw'
    PROD_BASE = 'https://api.pchomepay.com.tw'

    NOTIFY_IP = '113.196.231.190'  # 白名單必加

    def __init__(self, app_id: str, secret: str, is_test: bool = True):
        self.app_id = app_id
        self.secret = secret
        self.base_url = self.SANDBOX_BASE if is_test else self.PROD_BASE
        self._token = None
        self._token_expire = 0

    def _get_token(self) -> str:
        """取得 / 刷新 pcpay-token (cache 8h)"""
        if self._token and time.time() < self._token_expire - 60:
            return self._token

        # Basic Auth 取 token
        creds = b64encode(f'{self.app_id}:{self.secret}'.encode()).decode()
        try:
            r = requests.post(
                self.base_url + '/v1/token',
                headers={'Authorization': f'Basic {creds}'},
                timeout=30,
            )
            r.raise_for_status()
            data = r.json()
            self._token = data.get('token', '')
            self._token_expire = time.time() + data.get('expires_in', 28800)
            return self._token
        except Exception as e:
            raise ConnectionError(f'PChomePay token 取得失敗: {e}')

    @property
    def headers(self) -> Dict[str, str]:
        return {
            'pcpay-token': self._get_token(),
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

    # -- Operations -----------------------------------------------------------

    def create_logistic(self, req: LogisticBatchRequest) -> PChomePayResponse:
        """取號列印交寄單"""
        body = {
            'order_id': req.order_id,
            'store_id': req.store_id,
            'return_store_id': req.return_store_id,
            'name': req.name,
            'phone': req.phone,
            'address': req.address,
            'email': req.email,
        }
        return self._submit('POST', '/v1/logistic/batch', body=body)

    def query_history(self, order_id: str) -> PChomePayResponse:
        """查詢物流歷程"""
        return self._submit('GET', f'/v1/logistic/query/{order_id}/history')

    def get_history_page_url(self, order_id: str) -> str:
        """取得物流歷程 HTML 查詢頁 URL（不需 token, 直接給客戶）"""
        return f'{self.base_url}/v1/logistic/query/{order_id}/history-page'

    def query_yet_shipped(self) -> PChomePayResponse:
        """查詢尚未出貨的訂單"""
        return self._submit('GET', '/v1/logistic/yet')

    def query_store_return(self, date_yyyymmdd: str) -> PChomePayResponse:
        """查詢未取貨退倉訂單"""
        return self._submit('GET', f'/v1/logistic/store_return/{date_yyyymmdd}')

    def query_accounting(self, date_yyyymmdd: str) -> List[Dict[str, any]]:
        """
        查詢物流手續費對帳資料（NDJSON 格式）.

        每行為一個獨立 JSON 物件，須逐行 parse。
        """
        url = self.base_url + f'/v1/logistic/accounting/{date_yyyymmdd}'
        try:
            r = requests.get(url, headers=self.headers, timeout=30)
            r.raise_for_status()
            # NDJSON: 每行一個 JSON
            records = []
            for line in r.text.strip().split('\n'):
                if line.strip():
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
            return records
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f'PChomePay 對帳 API 連線失敗: {e}')

    def query_compensation(self, date_yyyymm: str) -> PChomePayResponse:
        """查詢貨物寄丟之賠款入帳資料"""
        return self._submit('GET', f'/v1/logistic/compensation/{date_yyyymm}')

    # -- HTTP submit ----------------------------------------------------------

    def _submit(self, method: str, path: str, body: Optional[Dict[str, any]] = None) -> PChomePayResponse:
        url = self.base_url + path
        try:
            if method == 'GET':
                r = requests.get(url, headers=self.headers, timeout=30)
            else:
                r = requests.post(url, headers=self.headers, json=body, timeout=30)
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f'PChomePay API 連線失敗: {e}')

        try:
            resp = r.json()
        except ValueError:
            return PChomePayResponse(
                success=False,
                code=str(r.status_code),
                message=f'回應非 JSON: {r.text[:200]}',
            )

        is_success = 200 <= r.status_code < 300
        return PChomePayResponse(
            success=is_success,
            code=str(resp.get('code', r.status_code)),
            message=resp.get('message', ''),
            data=resp.get('data', {}),
            raw=resp,
        )


# ============================================================================
# Examples
# ============================================================================

def example_create_logistic():
    print('=== PChomePay 7-11 取貨付款 取號 ===\n')
    svc = PChomePayLogisticService(app_id='YOUR_APP_ID', secret='YOUR_SECRET', is_test=True)
    req = LogisticBatchRequest(
        order_id=f'ORD{int(time.time())}',
        store_id='123456',  # 7-11 門市編號
        return_store_id='123456',
        name='王小明',
        phone='0912345678',
        email='test@example.com',
    )
    try:
        resp = svc.create_logistic(req)
        if resp.success:
            print(f'[OK] 取號成功: {json.dumps(resp.data, ensure_ascii=False)}')
        else:
            print(f'[FAIL] {resp.code}: {resp.message}')
    except Exception as e:
        print(f'[ERROR] {e}')


def example_query_history():
    print('\n=== PChomePay 物流歷程查詢 ===\n')
    svc = PChomePayLogisticService('YOUR_APP_ID', 'YOUR_SECRET', is_test=True)
    try:
        resp = svc.query_history(order_id='ORD123456')
        print(json.dumps(resp.raw, ensure_ascii=False, indent=2)[:500])
    except Exception as e:
        print(f'[ERROR] {e}')


def example_accounting():
    print('\n=== PChomePay 物流手續費對帳（NDJSON）===\n')
    svc = PChomePayLogisticService('YOUR_APP_ID', 'YOUR_SECRET', is_test=True)
    try:
        records = svc.query_accounting(date_yyyymmdd='20260101')
        print(f'共 {len(records)} 筆對帳記錄')
        for record in records[:3]:
            print(f'  - {record}')
    except Exception as e:
        print(f'[ERROR] {e}')


def example_history_page():
    print('\n=== PChomePay HTML 物流歷程頁（給客戶端）===\n')
    svc = PChomePayLogisticService('YOUR_APP_ID', 'YOUR_SECRET', is_test=True)
    url = svc.get_history_page_url('ORD123456')
    print(f'客戶可開啟: {url}')


if __name__ == '__main__':
    example_create_logistic()
    example_query_history()
    example_accounting()
    example_history_page()
