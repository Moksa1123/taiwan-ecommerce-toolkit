# PChomePay Logistics API Reference

拍錢包 (PChomePay) 物流 API 完整參考文件。

---

## 目錄

1. [基本說明](#基本說明)
2. [環境資訊](#環境資訊)
3. [認證方式](#認證方式)
4. [API 端點總覽](#api-端點總覽)
5. [物流類型分類](#物流類型分類)
6. [取號列印交寄單](#取號列印交寄單)
7. [查詢物流歷程](#查詢物流歷程)
8. [物流歷程查詢頁](#物流歷程查詢頁)
9. [未出貨/未取貨查詢](#未出貨未取貨查詢)
10. [物流手續費對帳](#物流手續費對帳)
11. [賠款查詢](#賠款查詢)
12. [物流狀態通知](#物流狀態通知)
13. [錯誤代碼](#錯誤代碼)
14. [常見問題排解](#常見問題排解)

---

## 基本說明

### PChomePay 物流定位

拍錢包 (PChomePay) 與 ECPay、PayUni 等純物流串接平台不同，主打**金流 + 物流二合一**的整合服務：

- **金流為主軸**：所有物流訂單均由 PChomePay 金流訂單派生，需先以 `pay_type` 為超商取貨類型 (`IPL7` / `IPLFM` / `IPLHL`) 建立金流訂單
- **超商取貨付款**：核心場景為 7-11 / 全家 / 萊爾富之 C2C 店到店服務，買家在付款頁面選擇取件門市
- **無獨立物流單建立 API**：`POST /v1/payment` 建立金流訂單後，物流訂單會自動產生；商家只需呼叫「取號列印交寄單」即可完成取號
- **與信用卡 / ATM 等其他付款方式可共用同套金流流程**：但僅超商取貨類型訂單會觸發物流相關 API

### 物流流程概覽

```
1. 建立金流訂單 (pay_type = IPL7/IPLFM/IPLHL)
   └─ 用戶在付款頁面選擇超商取件門市
2. 取得用戶選擇門市資訊 (notify: payment_info_set)
3. 取號列印交寄單 (POST /v1/logistic/batch)
4. 將商品交寄至超商
5. 透過通知 / 查詢 API 監控物流狀態
6. 用戶取貨完成 → 款項撥付
```

### 交寄期限規定

超商取貨訂單須在 **30 天內**完成取號交寄單列印。完成取號列印後（當日為 T），各超商有不同的交寄截止日：

| 超商 | 交寄期限 | 範例（6/10 取號） |
|------|----------|------------------|
| 7-11 (統一超商) | T + 10 日 | 須在 6/20 23:59 前交寄 |
| 全家 (FamilyMart) | T + 6 日 | 須在 6/16 23:59 前交寄 |
| 萊爾富 (Hi-Life) | T + 7 日 | 須在 6/17 23:59 前交寄 |

> ⚠ 一旦逾期未交寄，該訂單之物流單將自動失效，需重新處理。

---

## 環境資訊

### Domain Name

| 環境 | Base URL |
|------|----------|
| **正式環境 (Production)** | `https://api.pchomepay.com.tw` |
| **測試環境 (Sandbox)** | `https://sandbox-api.pchomepay.com.tw` |

### 來源 IP 白名單

正式與測試環境會透過以下 IP 發送 API Notify：

```
113.196.231.190
```

> 商家若有防火牆設定，請將此 IP 加入白名單，否則無法接收物流狀態通知。

### Sandbox 測試規則（超商取貨）

Sandbox 測試環境會根據訂單金額尾數模擬不同物流狀態：

| 金額尾數 | 模擬狀態 |
|---------|---------|
| 0 / 6 / 7 / 8 / 9 | 已建立 |
| 1 | 已交寄 |
| 2 | 配送中 |
| 3 | 已到店 |
| 4 | 已收款 |
| 5 | 已退件 |

### Sandbox 測試門市

```
7-11 測試門市：桃園市桃園區中埔六街 36 號 1 樓 維瀚門市
```

---

## 認證方式

PChomePay 物流 API 與金流 API 共用同一套認證機制。

### 認證流程

```
[1] APP_ID + SECRET (Basic Auth)
        ↓
[2] POST /v1/token → 取得 pcpay-token
        ↓
[3] 呼叫物流 API (header: pcpay-token)
        ↓
[4] token 8 小時失效 → 重新取得
```

### 步驟 1: 取得 Token

**端點**

```
POST https://api.pchomepay.com.tw/v1/token
```

**請求 Header**

| 欄位 | 必填 | 說明 |
|------|------|------|
| `Authorization` | ● | `Basic base64({APP_ID}:{SECRET})` |
| `Content-Type` | ● | `application/json` |

**請求 Body**

無

**回應欄位**

| 欄位 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `token` | ● | String(50) | 取得之 token，後續需放在 header `pcpay-token` |
| `expired_in` | ● | Int | token 失效秒數，預設 28,800 秒 (8 小時) |
| `expired_timestamp` | ● | Int | token 失效之 unix timestamp |

### cURL 範例

```bash
curl --location --request POST 'https://api.pchomepay.com.tw/v1/token' \
  --header 'Authorization: Basic RTIzNjc5QkY2NEFFNDU0RjRDQjY3MTFGQUMzNjp4UGdWTmdXb2I4YkdnRVQyZUJSc25pX3lYRW10cXV0bHhVa19VVXVo' \
  --header 'Content-Type: application/json'
```

### PHP 範例

```php
<?php

function getPcpayToken(string $appId, string $secret): array
{
    $auth = base64_encode("{$appId}:{$secret}");

    $ch = curl_init();
    curl_setopt_array($ch, [
        CURLOPT_URL => 'https://api.pchomepay.com.tw/v1/token',
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => '',
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_HTTPHEADER => [
            "Authorization: Basic {$auth}",
            'Content-Type: application/json',
        ],
    ]);

    $response = curl_exec($ch);
    curl_close($ch);

    return json_decode($response, true);
}

// 範例回應
// {
//   "token": "zHm67sQRuPSO__eiuy2h_lEgtPlS12aVqrcVz3Kc",
//   "expired_in": 28800,
//   "expired_timestamp": 1474470110
// }
```

### Python 範例

```python
import base64
import requests

def get_pcpay_token(app_id: str, secret: str) -> dict:
    credentials = base64.b64encode(f"{app_id}:{secret}".encode()).decode()
    headers = {
        "Authorization": f"Basic {credentials}",
        "Content-Type": "application/json",
    }
    response = requests.post(
        "https://api.pchomepay.com.tw/v1/token",
        headers=headers,
    )
    response.raise_for_status()
    return response.json()
```

### Token 使用注意事項

1. **不要每次請求都呼叫 `/v1/token`**：請暫存 token 到 8 小時失效再重新取得
2. **失效時間判斷**：`expired_timestamp - 60` 秒前重新取得（預留緩衝）
3. **Token 在所有請求 header 帶 `pcpay-token`**，不再使用 Basic Auth

---

## API 端點總覽

### 物流相關 API

| 功能 | Method | 端點 | 說明 |
|------|--------|------|------|
| 取號列印交寄單 | POST | `/v1/logistic/batch` | 批次為超商取貨訂單取號並產生交寄單 |
| 查詢物流歷程 | GET | `/v1/logistic/query/{order_id}/history` | 取得指定訂單之物流狀態歷程 (JSON) |
| 物流歷程查詢頁 | GET | `/v1/logistic/query/{order_id}/history-page` | 取得物流歷程查詢頁 URL (HTML 頁面) |
| 查詢未出貨訂單 | GET | `/v1/logistic/yet` | 列出尚未交寄之超商取貨訂單 |
| 查詢未取貨訂單 | GET | `/v1/logistic/store_return/{date}` | 查詢買家未至超商取貨之物流編號 |
| 物流手續費對帳 | GET | `/v1/logistic/accounting/{date}` | 指定日期之物流手續費對帳資料 |
| 賠款入帳查詢 | GET | `/v1/logistic/compensation/{date}` | 指定月份貨物寄丟之賠款入帳資料 |

### 共用 Headers

所有物流 API 均需以下 header：

| Header | 必填 | 說明 |
|--------|------|------|
| `Content-Type` | ● | `application/json` |
| `pcpay-token` | ● | 由 `/v1/token` 取得之 token |

---

## 物流類型分類

### 付款方式 (pay_type) 對照

PChomePay 物流訂單由金流訂單之 `pay_type` 決定。在 `POST /v1/payment` 建立訂單時填入：

| pay_type | 物流類型 | 說明 |
|----------|---------|------|
| `IPL7` | 7-11 超商取貨付款 | 統一超商交貨便 (C2C) |
| `IPLFM` | 全家超商取貨付款 | 全家便利商店 (C2C) |
| `IPLHL` | 萊爾富超商取貨付款 | 萊爾富 (C2C) |

> ⚠ PChomePay 目前不提供宅配 / 黑貓 / OK 超商等物流類型；OK (PLOK) 僅出現在對帳資料中作為歷史延續。

### 訂單金額限制

超商取貨付款訂單之金額限制：

```
65 ≦ amount ≦ 20,000 (新台幣)
```

### logistic_type (對帳資料用)

對帳 / 賠款 API 回傳之 `logistic_type` 對應如下：

| logistic_type | 物流類型 |
|--------------|---------|
| `PL711` | 7-11 統一超商 |
| `PLFMI` | 全家 (FamilyMart) |
| `PLHIL` | 萊爾富 (Hi-Life) |
| `PLOK` | OK 超商 |

### logistic_status (Notify 通知用)

物流狀態通知中之 `logistic_status` 對應如下：

| logistic_status | 說明 |
|----------------|------|
| `SSND` | 商品已至「寄件門店」 |
| `SATB` | 商品已至「取件門店」 |
| `RATC` | 商品已至「退件門店」 |

### 未出貨狀態 (status)

`/v1/logistic/yet` 回傳之狀態：

| status | 說明 |
|--------|------|
| `LINT` | 訂單建立 (尚未取號) |
| `LGNO` | 已取號 (尚未交寄) |

---

## 取號列印交寄單

為超商取貨訂單批次取號並產生交寄單列印頁面 URL。

### 端點

```
POST https://api.pchomepay.com.tw/v1/logistic/batch
```

### 請求欄位

| 欄位 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `order_id` | ● | Array | 欲列印交寄單之訂單編號陣列 |

### cURL 範例

```bash
curl --location 'https://api.pchomepay.com.tw/v1/logistic/batch' \
  --header 'Content-Type: application/json' \
  --header 'pcpay-token: __kJw1OMKTkwwssWPsAnGNtIzMYFIZ5ymmkq8nCd' \
  --data '{
    "order_id": ["B2C1702640091"]
  }'
```

### 回應欄位

| 欄位 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `print_no` | ● | String | 取號成功之交貨便服務代碼 |
| `error_order_id` | ● | String | 取號失敗之訂單編號 (成功時為 `null`) |
| `print_url` | ● | String | 交寄單頁面連結 |

### 回應範例

```json
{
  "print_no": "N63399396760",
  "error_order_id": null,
  "print_url": "https://pay.pchomepay.com.tw/apipay/ppwf?_pwfkey_=TnR3Z3AzY20xbk1wZFE0cGEsdU00aFNGcGNwNjVzcVkzVEwxZ1JPeGR3YUc5QWkwMk5yakEwSFlvdk5ZWHFoaQ=="
}
```

### PHP 範例

```php
<?php

function batchPrintShippingLabel(string $token, array $orderIds): array
{
    $body = json_encode(['order_id' => $orderIds]);

    $ch = curl_init();
    curl_setopt_array($ch, [
        CURLOPT_URL => 'https://api.pchomepay.com.tw/v1/logistic/batch',
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => $body,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_HTTPHEADER => [
            'Content-Type: application/json',
            "pcpay-token: {$token}",
        ],
    ]);

    $response = curl_exec($ch);
    curl_close($ch);

    return json_decode($response, true);
}

// 使用範例
$result = batchPrintShippingLabel($token, [
    'B2C1702640091',
    'B2C1702640092',
]);

if ($result['error_order_id']) {
    error_log("取號失敗：{$result['error_order_id']}");
} else {
    // 將 print_url 開啟以列印交寄單
    header("Location: {$result['print_url']}");
}
```

### Python 範例

```python
import requests

def batch_print_shipping_label(token: str, order_ids: list) -> dict:
    headers = {
        "Content-Type": "application/json",
        "pcpay-token": token,
    }
    payload = {"order_id": order_ids}
    response = requests.post(
        "https://api.pchomepay.com.tw/v1/logistic/batch",
        headers=headers,
        json=payload,
    )
    response.raise_for_status()
    return response.json()


# 使用範例
result = batch_print_shipping_label(token, ["B2C1702640091"])
if result.get("error_order_id"):
    print(f"取號失敗：{result['error_order_id']}")
else:
    print(f"交寄單 URL：{result['print_url']}")
```

### 注意事項

1. **必須在 30 天內完成取號**：超過則訂單失效
2. **批次取號**：`order_id` 為陣列可一次處理多筆，但若任一筆失敗會回傳於 `error_order_id`
3. **`print_url` 開啟即可列印**：頁面為 HTML，內含適合熱感印表機的格式
4. **同訂單重複取號**：會回傳同一個 `print_no`，不會重複扣費

---

## 查詢物流歷程

查詢指定訂單之物流狀態歷程 (JSON 格式)。

### 端點

```
GET https://api.pchomepay.com.tw/v1/logistic/query/{order_id}/history
```

### 路徑參數

| 參數 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `order_id` | ● | String(50) | 合作方訂單編號 |

### cURL 範例

```bash
curl --location 'https://api.pchomepay.com.tw/v1/logistic/query/B2C1723815435/history' \
  --header 'Content-Type: application/json' \
  --header 'pcpay-token: 0BZyFozlvqFtlwJoL5HQstTbNW_gNrNmsPQ4upc7'
```

### 回應欄位

| 欄位 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `order_id` | ● | String(50) | 合作方訂單編號 |
| `history` | ● | Array | 歷程紀錄陣列 |

### history 物件

| 欄位 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `logistic_id` | ● | String(50) | 超商物流代號 |
| `status` | ● | String(50) | 訂單與物流狀態（中文） |
| `status_date` | ● | String | 該狀態日期 (YYYY/MM/DD) |
| `status_time` | ● | String | 該狀態時間 (HH:MM:SS) |

### status 狀態值

| status (中文) | 說明 |
|--------------|------|
| `訂單建立` | 訂單已成功建立但尚未取號 |
| `已交寄` | 商家已將商品交寄至物流 |
| `配送中` | 商品於物流配送中 |
| `已到店` | 商品已送達取件門市 |
| `已付款` | 用戶已至門市完成付款取貨 |
| `已撥付` | 款項已轉至商家可提領餘額 |

### 回應範例

```json
{
  "order_id": "B2C1723815435",
  "history": [
    {
      "logistic_id": "L24081201043969",
      "status": "訂單建立",
      "status_date": "2024/08/16",
      "status_time": "21:37:15"
    },
    {
      "logistic_id": "L24081201043969",
      "status": "已交寄",
      "status_date": "2024/08/16",
      "status_time": "21:39:02"
    }
  ]
}
```

### Python 範例

```python
import requests

def query_logistic_history(token: str, order_id: str) -> dict:
    url = f"https://api.pchomepay.com.tw/v1/logistic/query/{order_id}/history"
    headers = {
        "Content-Type": "application/json",
        "pcpay-token": token,
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


# 取出最新狀態
history = query_logistic_history(token, "B2C1723815435")
latest = history["history"][-1] if history["history"] else None
if latest:
    print(f"目前狀態：{latest['status']} ({latest['status_date']} {latest['status_time']})")
```

---

## 物流歷程查詢頁

取得可直接呈現給用戶的物流歷程查詢頁 URL（HTML 頁面）。

### 端點

```
GET https://api.pchomepay.com.tw/v1/logistic/query/{order_id}/history-page
```

### 路徑參數

| 參數 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `order_id` | ● | String(50) | 合作方訂單編號 |

### cURL 範例

```bash
curl --location 'https://api.pchomepay.com.tw/v1/logistic/query/B2C1723815435/history-page' \
  --header 'Content-Type: application/json' \
  --header 'pcpay-token: e0A_XRsPMDgCKvRnrikpdMTfEJzvIGuveJsn_695'
```

### 回應欄位

| 欄位 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `order_id` | ● | String(50) | 合作方訂單編號 |
| `history_url` | ● | String | 物流歷程查詢頁 URL |

### 回應範例

```json
{
  "logistic_id": "L24041201043748",
  "history_url": "https://pchomepay.com.tw/apipay/ppwf?_pwfkey_=UjdkdVlreEV5cjlKRlRZeHdlUSxRUVVkVk0ta09uZGlINCxoRSxicEs2ZVB0UnhkcDBkY0RkZE84R0dSU3hFcA=="
}
```

### 應用情境

1. **顧客自助查詢**：將 `history_url` 嵌入訂單頁面，顧客點擊即可查看完整物流歷程
2. **客服 / 後台**：直接連結至 PChomePay 提供之 UI 頁面，省去自行渲染歷程的成本
3. **與 `/history` 差異**：`/history` 回傳 JSON 由商家自行渲染；`/history-page` 直接提供完整 UI 頁面

---

## 未出貨/未取貨查詢

### 查詢未出貨訂單

列出已建立但尚未交寄至物流之超商取貨訂單。

#### 端點

```
GET https://api.pchomepay.com.tw/v1/logistic/yet
```

#### 請求欄位

無

#### cURL 範例

```bash
curl --location 'https://api.pchomepay.com.tw/v1/logistic/yet' \
  --header 'Content-Type: application/json' \
  --header 'pcpay-token: F6uG0pXXTPTHDMRkIj_HGnzrWJvom_m_HhPxf296'
```

#### 回應欄位 (Array)

| 欄位 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `order_id` | ● | String(50) | 合作方訂單編號 |
| `status` | ● | String | 商品目前物流狀態 |

#### status 值

| status | 說明 |
|--------|------|
| `LINT` | 訂單建立 (尚未取號) |
| `LGNO` | 已取號 (尚未交寄) |

#### 回應範例

```json
[
  {
    "order_id": "B2C1744189821",
    "status": "LGNO"
  },
  {
    "order_id": "B2C1744189822",
    "status": "LINT"
  }
]
```

#### 應用情境

- **每日交寄提醒**：每天透過此 API 撈出 `LGNO` 訂單，發送 reminder 給倉管人員
- **截止日警示**：搭配建單日期計算 T + N 天，於即將逾期時優先處理

---

### 查詢未取貨訂單

查詢買家未至超商取貨之物流編號（指定日期已到店但尚未取貨）。

#### 端點

```
GET https://api.pchomepay.com.tw/v1/logistic/store_return/{date}
```

#### 路徑參數

| 參數 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `date` | ● | String(8) | 欲查詢日期，格式 `YYYYMMDD` |

#### cURL 範例

```bash
curl --location 'https://api.pchomepay.com.tw/v1/logistic/store_return/20250409' \
  --header 'pcpay-token: F6uG0pXXTPTHDMRkIj_HGnzrWJvom_m_HhPxf296'
```

#### 回應欄位 (Array)

| 欄位 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `order_id` | ● | String(50) | 合作方訂單編號 |
| `logistic_id` | ● | String(50) | 訂單物流編號 |
| `status` | ● | String | 商品目前物流狀態 (僅 `SATB`) |

#### 回應範例

```json
[
  {
    "order_id": "B2C1744192674",
    "logistic_id": "L25041201044206",
    "status": "SATB"
  }
]
```

> 此 API 僅回傳狀態為 `SATB` (商品已到取件門市) 但用戶尚未取走的訂單。

#### 應用情境

- **退件預警**：到店未取超過超商保留期限將自動退件（產生退件物流費）
- **客戶提醒**：撈出此清單，主動以 SMS / Email 提醒買家取貨

---

## 物流手續費對帳

查詢指定日期之物流手續費對帳資料。

### 端點

```
GET https://api.pchomepay.com.tw/v1/logistic/accounting/{date}
```

### 路徑參數

| 參數 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `date` | ● | String(8) | 對帳日期，格式 `YYYYMMDD`，僅能查詢 30 天前資料 |

### cURL 範例

```bash
curl --location 'https://api.pchomepay.com.tw/v1/logistic/accounting/20240816' \
  --header 'pcpay-token: fGVWZrMrYEVLHbj1joxn7CpdjsygFYYN8vLaygGM'
```

### 回應格式

> ⚠ 此 API 為**特規 JSON 串接格式**：第一行為摘要 JSON，後續每筆訂單為獨立 JSON object（換行分隔，非標準 JSON Array）。

#### 第一行 (摘要)

| 欄位 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `total_recs` | ● | String(5) | 該日對帳資料筆數 |

#### 明細欄位 (每行一筆)

| 欄位 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `order_id` | ● | String(50) | 合作方訂單編號 |
| `logistic_type` | ● | String | 物流類型 (`PL711` / `PLFMI` / `PLHIL` / `PLOK`) |
| `logistic_amount` | ● | Int | 物流手續費 (新台幣) |
| `accounting_date` | ● | String(14) | 帳務日期，格式 `YYYYMMDDhh24MiSS` |

### 回應範例

```
{"total_recs": 1}
{"order_id": "B2C1723809155", "logistic_type": "PL711", "logistic_amount": 65, "accounting_date": "20240816195407"}
{"order_id": "B2C1723808237", "logistic_type": "PLFMI", "logistic_amount": 65, "accounting_date": "20240818201412"}
```

### Python 解析範例

```python
import requests
import json

def fetch_logistic_accounting(token: str, date: str) -> dict:
    url = f"https://api.pchomepay.com.tw/v1/logistic/accounting/{date}"
    headers = {"pcpay-token": token}
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    # 特規 JSON：以換行分隔每行為一個 JSON
    lines = response.text.strip().splitlines()
    summary = json.loads(lines[0])
    records = [json.loads(line) for line in lines[1:] if line.strip()]
    return {"summary": summary, "records": records}


result = fetch_logistic_accounting(token, "20240816")
print(f"共 {result['summary']['total_recs']} 筆")
for rec in result["records"]:
    print(f"{rec['order_id']} - {rec['logistic_type']} - NT${rec['logistic_amount']}")
```

### 物流手續費注意事項

1. **無論是否取貨成功，皆會收取物流手續費**：商品從交寄起就計算手續費
2. **手續費為內扣**：訂單清算時自動從訂單金額中扣除，不另外請款
3. **PChomePay 後台**：可至會員中心 > 對帳資料下載完整對帳檔
4. **30 天保留期**：超過 30 天則無法查詢，請定期下載備份

---

## 賠款查詢

查詢指定月份貨物寄丟之賠款入帳資料。

### 端點

```
GET https://api.pchomepay.com.tw/v1/logistic/compensation/{date}
```

### 路徑參數

| 參數 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `date` | ● | String(6) | 入帳年月，格式 `YYYYMM` |

### cURL 範例

```bash
curl --location 'https://api.pchomepay.com.tw/v1/logistic/compensation/202408' \
  --header 'pcpay-token: fGVWZrMrYEVLHbj1joxn7CpdjsygFYYN8vLaygGM'
```

### 回應格式

與「物流手續費對帳」相同採特規 JSON：

#### 第一行 (摘要)

| 欄位 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `total_recs` | ● | String(5) | 該月賠款筆數 |

#### 明細欄位

| 欄位 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `order_id` | ● | String(50) | 合作方訂單編號 |
| `logistic_type` | ● | String | 物流類型 (`PL711` / `PLFMI` / `PLHIL` / `PLOK`) |
| `logistic_amount` | ● | Int | 賠款金額 (新台幣) |
| `accounting_date` | ● | String(14) | 帳務日期，格式 `YYYYMMDDhh24MiSS` |

### 回應範例

```
{"total_recs": 1}
{"order_id": "B2C1723809155", "logistic_type": "PL711", "logistic_amount": 200, "accounting_date": "20240816195407"}
{"order_id": "B2C1723808237", "logistic_type": "PLFMI", "logistic_amount": 565, "accounting_date": "20240818201412"}
```

### 賠款說明

1. **觸發條件**：商品於物流運送過程中遺失或損毀，由超商物流方核定後賠付
2. **賠款金額**：依物流商賠付規範決定（通常為訂單金額之一定比例，最高有上限）
3. **入帳方式**：直接撥付至 PChomePay 商家餘額
4. **查詢範圍**：以月份為單位 (`YYYYMM`)，可累積查詢

---

## 物流狀態通知

PChomePay 會在物流狀態變更時透過 `notify_url` 主動推送通知。

### 通知格式

```
Method: POST
Content-Type: application/x-www-form-urlencoded
```

### 通用參數

| 參數 | 說明 |
|------|------|
| `notify_type` | 通知類型 (`seller_dispatched` / `pickup_shipped` / `return_shipped`) |
| `notify_message` | JSON 格式之通知內容 (字串) |

### notify_message 結構

| 欄位 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `order_id` | ● | String(50) | 合作方訂單編號 |
| `pay_type` | ● | String(5) | 付款方式 (`IPL7` / `IPLFM` / `IPLHL`) |
| `logistic_info` | ● | Object | 物流資訊（見下） |

### logistic_info 物件

| 欄位 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `logistic_id` | ● | String(11) | 超商物流代號 |
| `logistic_status` | ● | String | 物流狀態 (`SSND` / `SATB` / `RATC`) |
| `logistic_type` | ● | String | 物流類型 (`C2C` 店到店, `B2C` 大宗寄倉，目前未提供) |
| `status_date` | ● | String(14) | 該狀態日期 (`YYYYMMDDhh24MiSS`) |

### 通知類型

#### seller_dispatched (商品已至寄件門店)

當商家將商品交寄至超商寄件門市時觸發。

```bash
curl --location 'https://your-site.com/notify' \
  --header 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode 'notify_type=seller_dispatched' \
  --data-urlencode 'notify_message={
      "order_id":"B2C_Uni_1769857427",
      "pay_type":"IPL7",
      "logistic_info":{
        "logistic_id":"M22216559430",
        "logistic_status":"SSND",
        "logistic_type":"C2C",
        "status_date":"20250924183250"
      }
  }'
```

#### pickup_shipped (商品已至取件門店)

當商品送達買家指定的取件門市時觸發 → 商家可發送通知請買家前往取貨。

```bash
curl --location 'https://your-site.com/notify' \
  --header 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode 'notify_type=pickup_shipped' \
  --data-urlencode 'notify_message={
      "order_id":"B2C_Uni_1769850289",
      "pay_type":"IPL7",
      "logistic_info":{
        "logistic_id":"M22216568132",
        "logistic_status":"SATB",
        "logistic_type":"C2C",
        "status_date":"20250925212043"
      }
  }'
```

#### return_shipped (商品已至退件門店)

當買家未取貨或主動退貨，商品送達退件門市時觸發。

```bash
curl --location 'https://your-site.com/notify' \
  --header 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode 'notify_type=return_shipped' \
  --data-urlencode 'notify_message={
      "order_id":"B2C_Uni_1769853160",
      "pay_type":"IPL7",
      "logistic_info":{
        "logistic_id":"M22216577821",
        "logistic_status":"RATC",
        "logistic_type":"C2C",
        "status_date":"20250927090822"
      }
  }'
```

### PHP 接收範例

```php
<?php

// 接收 PChomePay 物流狀態通知
$notifyType = $_POST['notify_type'] ?? '';
$notifyMessage = json_decode($_POST['notify_message'] ?? '{}', true);

if (!$notifyMessage) {
    http_response_code(400);
    exit('invalid notify_message');
}

$orderId = $notifyMessage['order_id'];
$status = $notifyMessage['logistic_info']['logistic_status'];

switch ($notifyType) {
    case 'seller_dispatched':
        // 商品已交寄
        updateOrderStatus($orderId, 'shipped');
        break;
    case 'pickup_shipped':
        // 商品已到店，可發送取貨通知
        updateOrderStatus($orderId, 'arrived_at_store');
        sendPickupReminder($orderId);
        break;
    case 'return_shipped':
        // 商品退件
        updateOrderStatus($orderId, 'returned');
        break;
}

// PChomePay 不要求特定回應，回 200 即可
http_response_code(200);
echo 'OK';
```

### Python 接收範例 (Flask)

```python
import json
from flask import Flask, request

app = Flask(__name__)

@app.route('/pchomepay-notify', methods=['POST'])
def pchomepay_notify():
    notify_type = request.form.get('notify_type')
    notify_message = request.form.get('notify_message', '{}')

    try:
        message = json.loads(notify_message)
    except json.JSONDecodeError:
        return 'invalid notify_message', 400

    order_id = message['order_id']
    logistic_status = message['logistic_info']['logistic_status']

    if notify_type == 'seller_dispatched':
        update_order(order_id, 'shipped')
    elif notify_type == 'pickup_shipped':
        update_order(order_id, 'arrived_at_store')
    elif notify_type == 'return_shipped':
        update_order(order_id, 'returned')

    return 'OK', 200
```

### 通知處理注意事項

1. **重試機制**：PChomePay 若收到非 200 回應，會自動重試多次
2. **驗證來源 IP**：建議白名單檢查 `113.196.231.190` 為唯一允許來源
3. **冪等處理**：同一狀態變更可能收到多次通知，需以 `order_id + logistic_status + status_date` 去重
4. **非阻塞處理**：建議以 queue / async 處理通知內容，避免回應延遲

---

## 錯誤代碼

### 物流相關錯誤代碼

| 代碼 | 英文描述 | 中文描述 |
|------|---------|---------|
| `90001` | invalid status | 物流狀態錯誤 |
| `90002` | logistic status history not found | 物流狀態歷程不存在 |
| `90004` | Print delivery note fail. | 列印交寄單失敗 |

### 認證 / 通用錯誤代碼

| 代碼 | 英文描述 | 中文描述 |
|------|---------|---------|
| `10001` | invalid user password | APPID 和 Secret 錯誤 |
| `10002` | Server IP not allow | 不被允許的 IP 位址 |
| `10003` | invalid token | token 錯誤 |
| `10004` | token expired | token 逾期 |
| `10006` | api client has not set notifyURL or returnURL yet | 未設定 notifyURL 或 returnURL |
| `10007` | function unavailable | 會員帳號暫時無法使用功能服務 |

### 訂單相關錯誤代碼

| 代碼 | 英文描述 | 中文描述 |
|------|---------|---------|
| `20001` | order id duplicate | 訂單編號不可重複 |
| `20002` | order not exists | 訂單不存在 |
| `20003` | pay type not support | 付款類別錯誤 |
| `20005` | params is not valid | 參數錯誤 |
| `20007` | It not allow to check today's data | 目前無法查詢當日資料 |
| `20009` | Request data is not a json structure data | 請求格式不是 JSON |
| `20014` | cvs setting error. | 未設定超商退貨門市 |

### 錯誤回應格式

```json
{
  "error_type": "invalid_request_error",
  "code": 90004,
  "message": "Print delivery note fail."
}
```

---

## 常見問題排解

### Q1: 取號失敗 (90004) 該如何處理？

**可能原因**：

1. 訂單付款方式不是超商取貨 (`IPL7` / `IPLFM` / `IPLHL`)
2. 用戶尚未在付款頁面選擇取件門市
3. 訂單已超過 30 天取號期限
4. 訂單狀態異常 (失敗 / 退款)

**處理方式**：

- 先呼叫 `GET /v1/payment/{order_id}` 查詢訂單狀態
- 確認 `payment_info.store_id` 是否已存在 (代表用戶已選門市)
- 若超過 30 天，需請用戶重新下單

### Q2: 為何收不到物流通知？

**檢查清單**：

1. **`notify_url` 設定**：在 PChomePay 後台 > 環境設定 > Notify URL 是否設定正確
2. **IP 白名單**：是否將 `113.196.231.190` 加入防火牆白名單
3. **HTTPS 憑證**：notify URL 須為有效的 HTTPS 端點 (建議使用 Let's Encrypt 等正式憑證)
4. **回應狀態碼**：notify 接收端需回應 200，否則 PChomePay 會持續重試
5. **建立訂單時 `notify_url`**：可於 `POST /v1/payment` 個別覆蓋預設值

### Q3: 物流訂單可以重新取號嗎？

**答**：

- **同一筆訂單可重複呼叫 `/v1/logistic/batch`**：會回傳同一個 `print_no`，不會重複扣費
- **若要更換門市**：無法透過 API，需請買家重新下單

### Q4: 如何處理「已到店但用戶未取貨」？

**SOP**：

```
1. 透過 GET /v1/logistic/store_return/{date} 撈出 SATB 但未付款訂單
2. 主動以 SMS / Email 通知買家取貨
3. 超過 7 天後（超商保留期限），商品會自動退件
4. 收到 return_shipped 通知後，自動標記訂單為「退件」狀態
5. 商家從退件門市領回商品
```

### Q5: 物流手續費何時收取？

**答**：

- **時機**：商品從寄件門店交寄起即收取
- **金額**：依各超商之合約價（一般 7-11 / 全家為 NT$65 / 件，實際以後台公告為準）
- **無論取貨成敗皆收取**：包括買家未取貨退件
- **退款不退手續費**：退款時手續費不會退還，且會額外收取 NT$15 退款手續費

### Q6: 是否支援自有物流？

**答**：

- PChomePay **僅支援自家整合的超商取貨服務**
- 若需使用其他物流（黑貓、新竹貨運、自取等），需自行另外串接 ECPay / PayUni / 物流商 API
- PChomePay 會專注於「金流 + 超商取貨」一站式服務的整合

### Q7: 與 ECPay / PayUni 物流的差異？

| 比較項目 | PChomePay | ECPay | PayUni |
|---------|-----------|-------|--------|
| 物流獨立串接 | ❌ 必須先建金流訂單 | ✅ 物流可獨立串接 | ✅ 物流可獨立串接 |
| 支援超商 | 7-11 / 全家 / 萊爾富 | 4 大超商 + 黑貓 + 宅配通 | 7-11 + 黑貓 |
| 認證方式 | OAuth-like (Basic Auth → token) | CheckMacValue (MD5) | AES-256-GCM + HMAC |
| 物流類型 | C2C 店到店 | C2C / B2C | C2C |
| Notify 格式 | x-www-form-urlencoded + JSON | x-www-form-urlencoded | JSON / 加密 |

### Q8: 如何測試 Sandbox 環境？

**測試步驟**：

1. 申請正式及測試 APP_ID / SECRET（聯絡 PChomePay 業務）
2. 使用 sandbox URL：`https://sandbox-api.pchomepay.com.tw`
3. 建立超商取貨訂單，金額尾數依[測試規則](#sandbox-測試規則超商取貨)模擬不同狀態
4. 在 sandbox 後台查看訂單與物流狀態

### Q9: 訂單狀態 WD 是什麼意思？

**答**：

- `WD` = **超商取貨等待商品交寄**
- 此狀態出現在 `GET /v1/payment/{order_id}` 之 `status_code`
- 代表用戶已成功下單並選擇門市，但商家尚未取號交寄
- 此時應呼叫 `POST /v1/logistic/batch` 取號 → 列印交寄單 → 交寄

### Q10: 對帳 / 賠款 API 為何回應不是標準 JSON？

**答**：

- 文件明確說明：「API 除對帳為特規 JSON 外，其他所有請求以及回應都以 JSON 做為標準請求或回傳格式」
- 對帳 / 賠款 API 採**逐行 JSON (NDJSON / JSONL) 格式**：
  - 第一行：摘要（`total_recs`）
  - 後續每行：一筆訂單之 JSON object
- 不可使用 `json.loads(response.text)` 直接解析，需逐行解析（[參考解析範例](#python-解析範例)）

---

## 官方資源

- **官方網站**: https://www.pchomepay.com.tw/
- **API 文件**: https://docs.google.com/document/d/1dPIPJc4xfyjkJ1i2yxaja4OP0G-iGFRXM08NDMuttZE/
- **後台管理**: https://web.pchomepay.com.tw/
- **WooCommerce 模組**: [PChomePay WooCommerce User Guide](https://docs.google.com/document/d/1ItCUQvY0A4VeVAlOdAMbt48lKB-xlNVZCu7E6L9d0Mg/)
- **舊版購物車模組**: https://github.com/PChomePayPlugin
- **技術服務信箱**: tech_support@pchomepay.com.tw

---

最後更新：2026/05/07
