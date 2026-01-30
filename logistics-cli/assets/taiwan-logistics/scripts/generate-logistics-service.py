#!/usr/bin/env python3
"""
Taiwan Logistics Service Generator
根據 CSV 數據生成完整的物流服務實作

用法:
    python generate-logistics-service.py ECPay              # 生成 ECPay 服務 (TypeScript)
    python generate-logistics-service.py NewebPay --output py  # 生成 NewebPay 服務 (Python)
    python generate-logistics-service.py PAYUNi --output ./lib/   # 指定輸出目錄
"""

import sys
import os
import csv
import argparse
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# 取得腳本目錄
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / 'data'


def load_csv(filename: str) -> List[Dict[str, str]]:
    """載入 CSV 檔案"""
    filepath = DATA_DIR / filename
    if not filepath.exists():
        return []

    with open(filepath, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def get_provider_info(provider: str) -> Optional[Dict[str, str]]:
    """取得服務商資訊"""
    providers = load_csv('providers.csv')
    for p in providers:
        if p['provider'].lower() == provider.lower():
            return p
    return None


# TypeScript 模板
TS_TEMPLATE = '''import crypto from 'crypto'
import FormData from 'form-data'

/**
 * {display_name} 物流服務
 *
 * 類型: {provider_type}
 * 加密方式: {encryption}
 * 支援物流: {logistics_types}
 *
 * 自動生成 by taiwan-logistics-skill
 * 生成時間: {timestamp}
 */

// ============================================================================
// 介面定義
// ============================================================================

interface StoreMapData {{
    MerchantOrderNo: string
    LogisticsType: 'B2C' | 'C2C'
    StoreType: '1' | '2' | '3' | '4'  // 1=7-11, 2=全家, 3=萊爾富, 4=OK
    ReturnURL: string
}}

interface ShipmentData {{
    MerchantOrderNo: string
    LogisticsType: 'B2C' | 'C2C'
    StoreType: '1' | '2' | '3' | '4'
    ReceiverName: string
    ReceiverPhone: string
    ReceiverStoreID: string
    Amount: number
    CollectionAmount?: number
    NotifyURL?: string
    Remark?: string
}}

interface ShipmentResponse {{
    success: boolean
    shipmentNo?: string
    storePrintNo?: string
    errorCode?: string
    errorMessage?: string
    raw?: any
}}

interface PrintLabelData {{
    LogisticsType: 'B2C' | 'C2C'
    StoreType: '1' | '2' | '3' | '4'
    MerchantOrderNos: string[]
}}

interface TrackingInfo {{
    status: string
    statusDescription: string
    updateTime: string
    history?: Array<{{
        status: string
        description: string
        time: string
    }}>
}}

// ============================================================================
// 主服務類別
// ============================================================================

export class {class_name}LogisticsService {{
    private readonly TEST_URL = '{test_url}'
    private readonly PROD_URL = '{prod_url}'
    private readonly API_BASE_URL: string

    // 測試憑證
{test_credentials}

    constructor(
        private readonly merchantId: string,
        private readonly hashKey: string,
        private readonly hashIV: string,
        isProd: boolean = false
    ) {{
        this.API_BASE_URL = isProd ? this.PROD_URL : this.TEST_URL
    }}

    // ========================================================================
    // 加密/簽章方法
    // ========================================================================

{encryption_methods}

    // ========================================================================
    // API 方法
    // ========================================================================

    /**
     * 門市地圖查詢 (Store Map API)
     * 用於讓使用者選擇超商門市
     */
    async getStoreMap(data: StoreMapData): Promise<string> {{
        const apiData = {{
            MerchantID: this.merchantId,
            MerchantOrderNo: data.MerchantOrderNo,
            LogisticsType: data.LogisticsType,
            StoreType: data.StoreType,
            ReturnURL: data.ReturnURL,
            TimeStamp: Math.floor(Date.now() / 1000)
        }}

        // 加密資料
        const encrypted = this.encrypt(JSON.stringify(apiData))

        // 回傳表單 HTML (需在前端提交)
        return this.generateFormHTML(
            `${{this.API_BASE_URL}}/storeMap`,
            {{
                MerchantID: this.merchantId,
                EncryptData: encrypted,
                HashData: this.generateHash(encrypted)
            }}
        )
    }}

    /**
     * 建立物流訂單 (Create Shipment)
     * 在訂單成立後建立物流單
     */
    async createShipment(data: ShipmentData): Promise<ShipmentResponse> {{
        const apiData = {{
            MerchantID: this.merchantId,
            MerchantOrderNo: data.MerchantOrderNo,
            LogisticsType: data.LogisticsType,
            StoreType: data.StoreType,
            ReceiverName: data.ReceiverName,
            ReceiverPhone: data.ReceiverPhone,
            ReceiverStoreID: data.ReceiverStoreID,
            Amount: data.Amount,
            CollectionAmount: data.CollectionAmount || 0,
            NotifyURL: data.NotifyURL || '',
            Remark: data.Remark || '',
            TimeStamp: Math.floor(Date.now() / 1000)
        }}

        try {{
            const encrypted = this.encrypt(JSON.stringify(apiData))
            const hash = this.generateHash(encrypted)

            const response = await fetch(`${{this.API_BASE_URL}}/createShipment`, {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/x-www-form-urlencoded'
                }},
                body: new URLSearchParams({{
                    MerchantID: this.merchantId,
                    EncryptData: encrypted,
                    HashData: hash
                }})
            }})

            const result = await response.json()

            if (result.Status === 'SUCCESS' && result.Data) {{
                const decrypted = this.decrypt(result.Data)

                return {{
                    success: true,
                    shipmentNo: decrypted.ShipmentNo,
                    storePrintNo: decrypted.StorePrintNo,
                    raw: decrypted
                }}
            }} else {{
                return {{
                    success: false,
                    errorCode: result.Status,
                    errorMessage: result.Message || '建立物流訂單失敗',
                    raw: result
                }}
            }}

        }} catch (error) {{
            return {{
                success: false,
                errorMessage: `API 呼叫錯誤: ${{error.message}}`,
                raw: error
            }}
        }}
    }}

    /**
     * 取得物流單號 (Get Shipment No)
     * 在出貨前取得物流編號
     */
    async getShipmentNo(orderNos: string[]): Promise<ShipmentResponse[]> {{
        const apiData = {{
            MerchantID: this.merchantId,
            MerchantOrderNo: orderNos,
            TimeStamp: Math.floor(Date.now() / 1000)
        }}

        try {{
            const encrypted = this.encrypt(JSON.stringify(apiData))
            const hash = this.generateHash(encrypted)

            const response = await fetch(`${{this.API_BASE_URL}}/getShipmentNo`, {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/x-www-form-urlencoded'
                }},
                body: new URLSearchParams({{
                    MerchantID: this.merchantId,
                    EncryptData: encrypted,
                    HashData: hash
                }})
            }})

            const result = await response.json()

            if (result.Data) {{
                const decrypted = this.decrypt(result.Data)
                const successItems = decrypted.SUCCESS || []

                return successItems.map((item: any) => ({{
                    success: true,
                    shipmentNo: item.LgsNo,
                    storePrintNo: item.StorePrintNo,
                    raw: item
                }}))
            }}

            return []

        }} catch (error) {{
            console.error('取得物流單號錯誤:', error)
            return []
        }}
    }}

    /**
     * 列印物流標籤 (Print Label)
     * 生成可列印的物流標籤
     */
    async printLabel(data: PrintLabelData): Promise<string> {{
        const apiData = {{
            MerchantID: this.merchantId,
            LogisticsType: data.LogisticsType,
            StoreType: data.StoreType,
            MerchantOrderNo: data.MerchantOrderNos,
            TimeStamp: Math.floor(Date.now() / 1000)
        }}

        const encrypted = this.encrypt(JSON.stringify(apiData))
        const hash = this.generateHash(encrypted)

        // 回傳表單 HTML (需在前端提交以開啟新視窗列印)
        return this.generateFormHTML(
            `${{this.API_BASE_URL}}/printLabel`,
            {{
                MerchantID: this.merchantId,
                EncryptData: encrypted,
                HashData: hash
            }},
            '_blank'
        )
    }}

    /**
     * 查詢物流訂單 (Query Shipment)
     * 查詢物流訂單的詳細資訊
     */
    async queryShipment(merchantOrderNo: string): Promise<any> {{
        const apiData = {{
            MerchantID: this.merchantId,
            MerchantOrderNo: merchantOrderNo,
            TimeStamp: Math.floor(Date.now() / 1000)
        }}

        try {{
            const encrypted = this.encrypt(JSON.stringify(apiData))
            const hash = this.generateHash(encrypted)

            const response = await fetch(`${{this.API_BASE_URL}}/queryShipment`, {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/x-www-form-urlencoded'
                }},
                body: new URLSearchParams({{
                    MerchantID: this.merchantId,
                    EncryptData: encrypted,
                    HashData: hash
                }})
            }})

            const result = await response.json()

            if (result.Data) {{
                return this.decrypt(result.Data)
            }}

            return null

        }} catch (error) {{
            console.error('查詢物流訂單錯誤:', error)
            return null
        }}
    }}

    /**
     * 追蹤物流軌跡 (Track Shipment)
     * 取得完整的物流配送歷程
     */
    async trackShipment(merchantOrderNo: string): Promise<TrackingInfo | null> {{
        const apiData = {{
            MerchantID: this.merchantId,
            MerchantOrderNo: merchantOrderNo,
            TimeStamp: Math.floor(Date.now() / 1000)
        }}

        try {{
            const encrypted = this.encrypt(JSON.stringify(apiData))
            const hash = this.generateHash(encrypted)

            const response = await fetch(`${{this.API_BASE_URL}}/trace`, {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/x-www-form-urlencoded'
                }},
                body: new URLSearchParams({{
                    MerchantID: this.merchantId,
                    EncryptData: encrypted,
                    HashData: hash
                }})
            }})

            const result = await response.json()

            if (result.Data) {{
                const decrypted = this.decrypt(result.Data)

                return {{
                    status: decrypted.RetId,
                    statusDescription: decrypted.RetString,
                    updateTime: decrypted.EventTime,
                    history: decrypted.History || []
                }}
            }}

            return null

        }} catch (error) {{
            console.error('追蹤物流軌跡錯誤:', error)
            return null
        }}
    }}

    // ========================================================================
    // 工具方法
    // ========================================================================

    /**
     * 生成表單 HTML
     * 用於需要 POST 表單提交的 API (如門市地圖、列印標籤)
     */
    private generateFormHTML(action: string, params: Record<string, string>, target: string = '_self'): string {{
        const inputs = Object.entries(params)
            .map(([key, value]) => `<input type="hidden" name="${{key}}" value="${{value}}">`)
            .join('\\n    ')

        return `
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>物流服務</title>
</head>
<body>
    <form id="logisticsForm" method="POST" action="${{action}}" target="${{target}}">
        ${{inputs}}
    </form>
    <script>
        document.getElementById('logisticsForm').submit();
    </script>
</body>
</html>
        `.trim()
    }}

    /**
     * 驗證回呼資料
     * 用於處理物流狀態通知
     */
    verifyCallback(encryptData: string, hashData: string): any {{
        // 驗證 Hash
        const expectedHash = this.generateHash(encryptData)
        if (hashData !== expectedHash) {{
            throw new Error('Hash 驗證失敗')
        }}

        // 解密資料
        return this.decrypt(encryptData)
    }}
}}

// ============================================================================
// 使用範例
// ============================================================================

/**
 * 範例 1: 門市地圖查詢
 */
async function example1_storeMap() {{
    const service = new {class_name}LogisticsService(
        'YOUR_MERCHANT_ID',
        'YOUR_HASH_KEY',
        'YOUR_HASH_IV',
        false  // 測試環境
    )

    const formHTML = await service.getStoreMap({{
        MerchantOrderNo: 'ORD20240130001',
        LogisticsType: 'C2C',
        StoreType: '1',  // 7-11
        ReturnURL: 'https://your-domain.com/api/logistics/store-callback'
    }})

    console.log('門市地圖表單:', formHTML)
    // 將 formHTML 回傳給前端,前端自動提交表單開啟門市地圖
}}

/**
 * 範例 2: 建立物流訂單
 */
async function example2_createShipment() {{
    const service = new {class_name}LogisticsService(
        'YOUR_MERCHANT_ID',
        'YOUR_HASH_KEY',
        'YOUR_HASH_IV',
        false
    )

    const result = await service.createShipment({{
        MerchantOrderNo: 'ORD20240130001',
        LogisticsType: 'C2C',
        StoreType: '1',
        ReceiverName: '王小明',
        ReceiverPhone: '0912345678',
        ReceiverStoreID: '991182',  // 從門市地圖取得
        Amount: 1200,
        CollectionAmount: 1200,  // 取貨付款金額
        NotifyURL: 'https://your-domain.com/api/logistics/notify'
    }})

    if (result.success) {{
        console.log('物流訂單建立成功!')
        console.log('物流單號:', result.shipmentNo)
        console.log('取貨碼:', result.storePrintNo)
    }} else {{
        console.error('物流訂單建立失敗:', result.errorMessage)
    }}
}}

/**
 * 範例 3: 列印物流標籤
 */
async function example3_printLabel() {{
    const service = new {class_name}LogisticsService(
        'YOUR_MERCHANT_ID',
        'YOUR_HASH_KEY',
        'YOUR_HASH_IV',
        false
    )

    const formHTML = await service.printLabel({{
        LogisticsType: 'C2C',
        StoreType: '1',
        MerchantOrderNos: ['ORD20240130001', 'ORD20240130002']
    }})

    console.log('列印標籤表單:', formHTML)
    // 將 formHTML 回傳給前端,開啟新視窗列印標籤
}}

// 匯出服務
export default {class_name}LogisticsService
'''

# Python 模板
PY_TEMPLATE = '''#!/usr/bin/env python3
"""
{display_name} 物流服務

類型: {provider_type}
加密方式: {encryption}
支援物流: {logistics_types}

自動生成 by taiwan-logistics-skill
生成時間: {timestamp}
"""

import hashlib
import base64
import json
import time
import requests
from typing import Dict, List, Optional, Literal
from dataclasses import dataclass, field
{crypto_imports}


# ============================================================================
# 資料結構
# ============================================================================

@dataclass
class StoreMapData:
    """門市地圖查詢資料"""
    merchant_order_no: str
    logistics_type: Literal['B2C', 'C2C']
    store_type: Literal['1', '2', '3', '4']  # 1=7-11, 2=全家, 3=萊爾富, 4=OK
    return_url: str


@dataclass
class ShipmentData:
    """物流訂單資料"""
    merchant_order_no: str
    logistics_type: Literal['B2C', 'C2C']
    store_type: Literal['1', '2', '3', '4']
    receiver_name: str
    receiver_phone: str
    receiver_store_id: str
    amount: int
    collection_amount: int = 0
    notify_url: str = ''
    remark: str = ''


@dataclass
class ShipmentResponse:
    """物流訂單回應"""
    success: bool
    shipment_no: str = ''
    store_print_no: str = ''
    error_code: str = ''
    error_message: str = ''
    raw: Dict = field(default_factory=dict)


@dataclass
class TrackingInfo:
    """物流追蹤資訊"""
    status: str
    status_description: str
    update_time: str
    history: List[Dict] = field(default_factory=list)


# ============================================================================
# 主服務類別
# ============================================================================

class {class_name}LogisticsService:
    """
    {display_name} 物流服務

    支援功能:
    - 門市地圖查詢
    - 建立物流訂單
    - 取得物流單號
    - 列印物流標籤
    - 查詢物流訂單
    - 追蹤物流軌跡

    測試環境:
{test_credentials_py}
    """

    TEST_URL = '{test_url}'
    PROD_URL = '{prod_url}'

    def __init__(self, merchant_id: str, hash_key: str, hash_iv: str, is_prod: bool = False):
        """
        初始化物流服務

        Args:
            merchant_id: 商店代號
            hash_key: Hash Key
            hash_iv: Hash IV
            is_prod: 是否為正式環境
        """
        self.merchant_id = merchant_id
        self.hash_key = hash_key{hash_key_encode}
        self.hash_iv = hash_iv{hash_iv_encode}
        self.api_base_url = self.PROD_URL if is_prod else self.TEST_URL

    # ========================================================================
    # 加密/簽章方法
    # ========================================================================

{encryption_methods_py}

    # ========================================================================
    # API 方法
    # ========================================================================

    def get_store_map(self, data: StoreMapData) -> str:
        """
        門市地圖查詢

        Args:
            data: 門市地圖查詢資料

        Returns:
            表單 HTML (需在前端提交)

        Example:
            >>> service = {class_name}LogisticsService('MID', 'KEY', 'IV')
            >>> html = service.get_store_map(StoreMapData(
            ...     merchant_order_no='ORD001',
            ...     logistics_type='C2C',
            ...     store_type='1',
            ...     return_url='https://your-domain.com/callback'
            ... ))
        """
        api_data = {{
            'MerchantID': self.merchant_id,
            'MerchantOrderNo': data.merchant_order_no,
            'LogisticsType': data.logistics_type,
            'StoreType': data.store_type,
            'ReturnURL': data.return_url,
            'TimeStamp': int(time.time())
        }}

        encrypted = self._encrypt(json.dumps(api_data, ensure_ascii=False))
        hash_data = self._generate_hash(encrypted)

        return self._generate_form_html(
            f'{{self.api_base_url}}/storeMap',
            {{
                'MerchantID': self.merchant_id,
                'EncryptData': encrypted,
                'HashData': hash_data
            }}
        )

    def create_shipment(self, data: ShipmentData) -> ShipmentResponse:
        """
        建立物流訂單

        Args:
            data: 物流訂單資料

        Returns:
            物流訂單回應

        Example:
            >>> result = service.create_shipment(ShipmentData(
            ...     merchant_order_no='ORD001',
            ...     logistics_type='C2C',
            ...     store_type='1',
            ...     receiver_name='王小明',
            ...     receiver_phone='0912345678',
            ...     receiver_store_id='991182',
            ...     amount=1200,
            ...     collection_amount=1200
            ... ))
        """
        api_data = {{
            'MerchantID': self.merchant_id,
            'MerchantOrderNo': data.merchant_order_no,
            'LogisticsType': data.logistics_type,
            'StoreType': data.store_type,
            'ReceiverName': data.receiver_name,
            'ReceiverPhone': data.receiver_phone,
            'ReceiverStoreID': data.receiver_store_id,
            'Amount': data.amount,
            'CollectionAmount': data.collection_amount,
            'NotifyURL': data.notify_url,
            'Remark': data.remark,
            'TimeStamp': int(time.time())
        }}

        try:
            encrypted = self._encrypt(json.dumps(api_data, ensure_ascii=False))
            hash_data = self._generate_hash(encrypted)

            response = requests.post(
                f'{{self.api_base_url}}/createShipment',
                data={{
                    'MerchantID': self.merchant_id,
                    'EncryptData': encrypted,
                    'HashData': hash_data
                }},
                headers={{'Content-Type': 'application/x-www-form-urlencoded'}},
                timeout=30
            )

            result = response.json()

            if result.get('Status') == 'SUCCESS' and result.get('Data'):
                decrypted = self._decrypt(result['Data'])

                return ShipmentResponse(
                    success=True,
                    shipment_no=decrypted.get('ShipmentNo', ''),
                    store_print_no=decrypted.get('StorePrintNo', ''),
                    raw=decrypted
                )
            else:
                return ShipmentResponse(
                    success=False,
                    error_code=result.get('Status', ''),
                    error_message=result.get('Message', '建立物流訂單失敗'),
                    raw=result
                )

        except Exception as e:
            return ShipmentResponse(
                success=False,
                error_message=f'API 呼叫錯誤: {{str(e)}}'
            )

    def get_shipment_no(self, order_nos: List[str]) -> List[ShipmentResponse]:
        """
        取得物流單號

        Args:
            order_nos: 訂單編號清單

        Returns:
            物流單號回應清單
        """
        api_data = {{
            'MerchantID': self.merchant_id,
            'MerchantOrderNo': order_nos,
            'TimeStamp': int(time.time())
        }}

        try:
            encrypted = self._encrypt(json.dumps(api_data, ensure_ascii=False))
            hash_data = self._generate_hash(encrypted)

            response = requests.post(
                f'{{self.api_base_url}}/getShipmentNo',
                data={{
                    'MerchantID': self.merchant_id,
                    'EncryptData': encrypted,
                    'HashData': hash_data
                }},
                timeout=30
            )

            result = response.json()

            if result.get('Data'):
                decrypted = self._decrypt(result['Data'])
                success_items = decrypted.get('SUCCESS', [])

                return [
                    ShipmentResponse(
                        success=True,
                        shipment_no=item.get('LgsNo', ''),
                        store_print_no=item.get('StorePrintNo', ''),
                        raw=item
                    )
                    for item in success_items
                ]

            return []

        except Exception as e:
            print(f'取得物流單號錯誤: {{e}}')
            return []

    def print_label(self, logistics_type: Literal['B2C', 'C2C'],
                   store_type: Literal['1', '2', '3', '4'],
                   order_nos: List[str]) -> str:
        """
        列印物流標籤

        Args:
            logistics_type: 物流類型
            store_type: 超商類型
            order_nos: 訂單編號清單

        Returns:
            表單 HTML
        """
        api_data = {{
            'MerchantID': self.merchant_id,
            'LogisticsType': logistics_type,
            'StoreType': store_type,
            'MerchantOrderNo': order_nos,
            'TimeStamp': int(time.time())
        }}

        encrypted = self._encrypt(json.dumps(api_data, ensure_ascii=False))
        hash_data = self._generate_hash(encrypted)

        return self._generate_form_html(
            f'{{self.api_base_url}}/printLabel',
            {{
                'MerchantID': self.merchant_id,
                'EncryptData': encrypted,
                'HashData': hash_data
            }},
            target='_blank'
        )

    def query_shipment(self, merchant_order_no: str) -> Optional[Dict]:
        """查詢物流訂單"""
        api_data = {{
            'MerchantID': self.merchant_id,
            'MerchantOrderNo': merchant_order_no,
            'TimeStamp': int(time.time())
        }}

        try:
            encrypted = self._encrypt(json.dumps(api_data, ensure_ascii=False))
            hash_data = self._generate_hash(encrypted)

            response = requests.post(
                f'{{self.api_base_url}}/queryShipment',
                data={{
                    'MerchantID': self.merchant_id,
                    'EncryptData': encrypted,
                    'HashData': hash_data
                }},
                timeout=30
            )

            result = response.json()

            if result.get('Data'):
                return self._decrypt(result['Data'])

            return None

        except Exception as e:
            print(f'查詢物流訂單錯誤: {{e}}')
            return None

    def track_shipment(self, merchant_order_no: str) -> Optional[TrackingInfo]:
        """追蹤物流軌跡"""
        api_data = {{
            'MerchantID': self.merchant_id,
            'MerchantOrderNo': merchant_order_no,
            'TimeStamp': int(time.time())
        }}

        try:
            encrypted = self._encrypt(json.dumps(api_data, ensure_ascii=False))
            hash_data = self._generate_hash(encrypted)

            response = requests.post(
                f'{{self.api_base_url}}/trace',
                data={{
                    'MerchantID': self.merchant_id,
                    'EncryptData': encrypted,
                    'HashData': hash_data
                }},
                timeout=30
            )

            result = response.json()

            if result.get('Data'):
                decrypted = self._decrypt(result['Data'])

                return TrackingInfo(
                    status=decrypted.get('RetId', ''),
                    status_description=decrypted.get('RetString', ''),
                    update_time=decrypted.get('EventTime', ''),
                    history=decrypted.get('History', [])
                )

            return None

        except Exception as e:
            print(f'追蹤物流軌跡錯誤: {{e}}')
            return None

    # ========================================================================
    # 工具方法
    # ========================================================================

    def _generate_form_html(self, action: str, params: Dict[str, str], target: str = '_self') -> str:
        """生成表單 HTML"""
        inputs = '\\n    '.join([
            f'<input type="hidden" name="{{k}}" value="{{v}}">'
            for k, v in params.items()
        ])

        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>物流服務</title>
</head>
<body>
    <form id="logisticsForm" method="POST" action="{{action}}" target="{{target}}">
        {{inputs}}
    </form>
    <script>
        document.getElementById('logisticsForm').submit();
    </script>
</body>
</html>
        """.strip()

    def verify_callback(self, encrypt_data: str, hash_data: str) -> Dict:
        """驗證回呼資料"""
        expected_hash = self._generate_hash(encrypt_data)
        if hash_data != expected_hash:
            raise ValueError('Hash 驗證失敗')

        return self._decrypt(encrypt_data)


# ============================================================================
# 使用範例
# ============================================================================

if __name__ == '__main__':
    # 初始化服務 (測試環境)
    service = {class_name}LogisticsService(
        merchant_id='YOUR_MERCHANT_ID',
        hash_key='YOUR_HASH_KEY',
        hash_iv='YOUR_HASH_IV',
        is_prod=False
    )

    # 範例 1: 建立物流訂單
    print("=== 建立物流訂單 ===\\n")

    shipment_data = ShipmentData(
        merchant_order_no=f'ORD{{int(time.time())}}',
        logistics_type='C2C',
        store_type='1',  # 7-11
        receiver_name='王小明',
        receiver_phone='0912345678',
        receiver_store_id='991182',
        amount=1200,
        collection_amount=1200
    )

    result = service.create_shipment(shipment_data)

    if result.success:
        print(f"✓ 物流訂單建立成功!")
        print(f"  物流單號: {{result.shipment_no}}")
        print(f"  取貨碼: {{result.store_print_no}}")
    else:
        print(f"✗ 物流訂單建立失敗: {{result.error_message}}")

    print("\\n" + "="*60)
'''


def generate_encryption_methods_ts(provider: str, encryption: str) -> str:
    """生成 TypeScript 加密方法"""
    if 'AES-256-CBC' in encryption:
        return '''    /**
     * AES-256-CBC 加密
     */
    private encrypt(data: string): string {
        const cipher = crypto.createCipheriv('aes-256-cbc', this.hashKey, this.hashIV)
        cipher.setAutoPadding(true)
        let encrypted = cipher.update(data, 'utf8', 'hex')
        encrypted += cipher.final('hex')
        return encrypted
    }

    /**
     * AES-256-CBC 解密
     */
    private decrypt(encryptedData: string): any {
        const decipher = crypto.createDecipheriv('aes-256-cbc', this.hashKey, this.hashIV)
        decipher.setAutoPadding(true)
        let decrypted = decipher.update(encryptedData, 'hex', 'utf8')
        decrypted += decipher.final('utf8')
        return JSON.parse(decrypted)
    }

    /**
     * SHA256 雜湊
     */
    private generateHash(encryptedData: string): string {
        const hashString = `HashKey=${this.hashKey}&${encryptedData}&HashIV=${this.hashIV}`
        return crypto.createHash('sha256').update(hashString).digest('hex').toUpperCase()
    }'''

    elif 'MD5' in encryption:
        return '''    /**
     * MD5 CheckMacValue 生成
     */
    private generateCheckMacValue(params: Record<string, any>): string {
        // 移除 CheckMacValue
        const { CheckMacValue, ...cleanParams } = params

        // 依照 key 排序
        const sortedKeys = Object.keys(cleanParams).sort()

        // 組合參數字串
        const paramString = sortedKeys
            .map(key => `${key}=${cleanParams[key]}`)
            .join('&')

        // 前後加上 HashKey 和 HashIV
        const rawString = `HashKey=${this.hashKey}&${paramString}&HashIV=${this.hashIV}`

        // URL Encode (lowercase)
        const encoded = encodeURIComponent(rawString).toLowerCase()

        // MD5 雜湊
        return crypto.createHash('md5').update(encoded).digest('hex').toUpperCase()
    }

    private encrypt(data: string): string {
        return data  // ECPay Logistics 使用 MD5, 不加密資料
    }

    private decrypt(data: string): any {
        return JSON.parse(data)
    }

    private generateHash(data: string): string {
        return this.generateCheckMacValue(JSON.parse(data))
    }'''

    else:
        return '''    private encrypt(data: string): string {
        // TODO: 實作加密方法
        return data
    }

    private decrypt(data: string): any {
        return JSON.parse(data)
    }

    private generateHash(data: string): string {
        // TODO: 實作雜湊方法
        return ''
    }'''


def generate_encryption_methods_py(provider: str, encryption: str) -> str:
    """生成 Python 加密方法"""
    if 'AES-256-CBC' in encryption:
        return '''    def _encrypt(self, data: str) -> str:
        """AES-256-CBC 加密"""
        cipher = AES.new(self.hash_key, AES.MODE_CBC, self.hash_iv)
        encrypted = cipher.encrypt(pad(data.encode('utf-8'), AES.block_size))
        return encrypted.hex()

    def _decrypt(self, encrypted_data: str) -> Dict:
        """AES-256-CBC 解密"""
        encrypted = bytes.fromhex(encrypted_data)
        cipher = AES.new(self.hash_key, AES.MODE_CBC, self.hash_iv)
        decrypted = unpad(cipher.decrypt(encrypted), AES.block_size).decode('utf-8')
        return json.loads(decrypted)

    def _generate_hash(self, encrypted_data: str) -> str:
        """SHA256 雜湊"""
        hash_string = f'HashKey={self.hash_key.decode()}&{encrypted_data}&HashIV={self.hash_iv.decode()}'
        return hashlib.sha256(hash_string.encode()).hexdigest().upper()'''

    elif 'MD5' in encryption:
        return '''    def _generate_check_mac_value(self, params: Dict) -> str:
        """MD5 CheckMacValue 生成"""
        clean_params = {k: v for k, v in params.items() if k != 'CheckMacValue'}
        sorted_keys = sorted(clean_params.keys())
        param_string = '&'.join([f'{k}={clean_params[k]}' for k in sorted_keys])
        raw_string = f'HashKey={self.hash_key}&{param_string}&HashIV={self.hash_iv}'
        encoded = urllib.parse.quote(raw_string).lower()
        return hashlib.md5(encoded.encode()).hexdigest().upper()

    def _encrypt(self, data: str) -> str:
        """ECPay Logistics 使用 MD5, 不加密資料"""
        return data

    def _decrypt(self, data: str) -> Dict:
        """解析資料"""
        return json.loads(data)

    def _generate_hash(self, data: str) -> str:
        """生成 Hash"""
        return self._generate_check_mac_value(json.loads(data))'''

    else:
        return '''    def _encrypt(self, data: str) -> str:
        """TODO: 實作加密方法"""
        return data

    def _decrypt(self, data: str) -> Dict:
        """TODO: 實作解密方法"""
        return json.loads(data)

    def _generate_hash(self, data: str) -> str:
        """TODO: 實作雜湊方法"""
        return ""'''


def generate_service(provider: str, output_format: str = 'ts') -> str:
    """生成服務代碼"""
    info = get_provider_info(provider)

    if not info:
        return f"錯誤: 找不到服務商 '{provider}'"

    class_name = provider.capitalize()
    display_name = info.get('name_zh', provider)
    provider_type = info.get('type', 'unknown')
    encryption = info.get('features', '')
    test_url = info.get('test_url', '')
    prod_url = info.get('prod_url', '')
    logistics_types = info.get('features', '').replace(',', ' | ')

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if output_format == 'ts':
        # TypeScript 測試憑證
        test_creds = ''
        if info.get('test_merchant_id'):
            test_creds = f'''    private readonly TEST_MERCHANT_ID = '{info.get('test_merchant_id', '')}'
    private readonly TEST_HASH_KEY = '{info.get('test_hash_key', '')}'
    private readonly TEST_HASH_IV = '{info.get('test_hash_iv', '')}'
'''

        encryption_methods = generate_encryption_methods_ts(provider, encryption)

        return TS_TEMPLATE.format(
            display_name=display_name,
            provider_type=provider_type,
            encryption=encryption,
            logistics_types=logistics_types,
            timestamp=timestamp,
            class_name=class_name,
            test_url=test_url,
            prod_url=prod_url,
            test_credentials=test_creds,
            encryption_methods=encryption_methods
        )

    else:  # Python
        # Python 測試憑證
        test_creds_py = ''
        if info.get('test_merchant_id'):
            test_creds_py = f'''    - 商店代號: {info.get('test_merchant_id', '')}
    - HashKey: {info.get('test_hash_key', '')}
    - HashIV: {info.get('test_hash_iv', '')}'''

        # 判斷是否需要 Crypto
        crypto_imports = ''
        hash_key_encode = ''
        hash_iv_encode = ''

        if 'AES' in encryption:
            crypto_imports = '\nfrom Crypto.Cipher import AES\nfrom Crypto.Util.Padding import pad, unpad'
            hash_key_encode = '.encode(\'utf-8\')'
            hash_iv_encode = '.encode(\'utf-8\')'

        encryption_methods_py = generate_encryption_methods_py(provider, encryption)

        return PY_TEMPLATE.format(
            display_name=display_name,
            provider_type=provider_type,
            encryption=encryption,
            logistics_types=logistics_types,
            timestamp=timestamp,
            class_name=class_name,
            test_url=test_url,
            prod_url=prod_url,
            test_credentials_py=test_creds_py,
            crypto_imports=crypto_imports,
            hash_key_encode=hash_key_encode,
            hash_iv_encode=hash_iv_encode,
            encryption_methods_py=encryption_methods_py
        )


def main():
    parser = argparse.ArgumentParser(
        description='Taiwan Logistics Service Generator',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('provider', type=str, help='服務商名稱 (ECPay, NewebPay, PAYUNi)')
    parser.add_argument('--output', type=str, choices=['ts', 'py'], default='ts',
                        help='輸出格式 (ts=TypeScript, py=Python)')

    args = parser.parse_args()

    # 生成服務代碼
    code = generate_service(args.provider, args.output)

    # 輸出
    print(code)

    return 0


if __name__ == '__main__':
    sys.exit(main())
