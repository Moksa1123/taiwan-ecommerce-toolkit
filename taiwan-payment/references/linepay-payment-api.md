# LINE Pay Online API v4 Reference

LINE Pay 線上 API v4 完整參考文件（繁體中文）。

LINE Pay 為全球性電子錢包服務，台灣為其主要市場之一。本文件僅涵蓋 LINE Pay 自家錢包整合，不包含 Apple Pay / Google Pay。

---

## 目錄

1. [基本說明](#基本說明)
2. [環境資訊](#環境資訊)
3. [API 端點總覽](#api-端點總覽)
4. [認證方式](#認證方式)
5. [訂單建立（Payment Request）](#訂單建立payment-request)
6. [付款確認（Confirm）](#付款確認confirm)
7. [付款狀態查詢](#付款狀態查詢)
8. [請款（Capture）與取消授權（Void）](#請款capture與取消授權void)
9. [退款（Refund）](#退款refund)
10. [訂單查詢（Payment Details）](#訂單查詢payment-details)
11. [自動扣款 / 一鍵付款（Preapproved Pay）](#自動扣款--一鍵付款preapproved-pay)
12. [付款通知與回調](#付款通知與回調)
13. [錯誤代碼](#錯誤代碼)
14. [支付方式對照表](#支付方式對照表)
15. [常見問題排解](#常見問題排解)

---

## 基本說明

### 什麼是 LINE Pay Online API v4

LINE Pay 是 LINE Corporation 提供的電子支付服務，整合了信用卡、LINE Points、LINE Pay Money 等多種支付來源。v4 為目前推薦的線上 API 版本。

### 整合特性

| 特性 | 說明 |
|------|------|
| **協定** | RESTful HTTPS + JSON |
| **認證** | HMAC-SHA256 簽章（標頭 `X-LINE-Authorization`） |
| **HTTP 狀態碼** | API **永遠回傳 HTTP 200**，實際結果由 JSON 中的 `returnCode` 判斷 |
| **TransactionId** | 19 位數整數，建議以 64 位 `long`/`int64` 儲存（避免 JS `Number` 精度遺失） |
| **語系** | 透過 `Accept-Language` 標頭控制錯誤訊息語系 |

### 商務面前置作業

1. 申請 LINE Pay 商家帳號（Merchant Account）
2. 開通 Online API 服務
3. 自商家後台取得 **Channel ID** 與 **Channel Secret**
4. 設定支付完成回調網址（`confirmUrl`、`cancelUrl`）

> **注意**：本文件中部分簽章字串組合方式（string-to-sign）為依據 LINE Pay v3 慣例「推論」而來，**正式上線前請務必對照官方 LINE Pay v4 PDF 文件再次驗證**。本節將以 ⚠️ 標示需要驗證的內容。

---

## 環境資訊

### Base URL

| 環境 | Host |
|------|------|
| 沙箱（Sandbox） | `https://sandbox-api-pay.line.me` |
| 正式（Production） | `https://api-pay.line.me` |

完整端點格式：

```
https://{host}/{apiPath}?{queryString}
```

### 沙箱測試

- 沙箱環境需向 LINE Pay 申請開通（與正式環境憑證**不同**）
- 沙箱可模擬付款流程，不會實際扣款
- 商家後台網址：`https://pay.line.me/portal/global/auth/login`

### 通訊規格

| 項目 | 規格 |
|------|------|
| 協定 | HTTPS（TLS 1.2 以上） |
| 編碼 | UTF-8 |
| Content-Type | `application/json` |
| HTTP Method | POST / GET（依端點而異） |
| 回應 HTTP Status | 永遠 `200 OK`（即使商務邏輯失敗） |

---

## API 端點總覽

### 一般付款流程

| 功能 | Method | Path |
|------|--------|------|
| **建立付款請求** | POST | `/v4/payments/request` |
| **查詢付款請求狀態** | GET | `/v4/payments/requests/{transactionId}/check` |
| **付款確認（授權）** | POST | `/v4/payments/{transactionId}/confirm` |
| **訂單查詢** | GET | `/v4/payments` |

### 授權後操作

| 功能 | Method | Path |
|------|--------|------|
| **請款（Capture）** | POST | `/v4/payments/authorizations/{transactionId}/capture` |
| **取消授權（Void）** | POST | `/v4/payments/authorizations/{transactionId}/void` |
| **退款（Refund）** | POST | `/v4/payments/{transactionId}/refund` |

### 自動扣款（Preapproved Pay）

| 功能 | Method | Path |
|------|--------|------|
| **檢查 RegKey 狀態** | GET | `/v4/payments/preapprovedPay/{regKey}/check` |
| **扣款** | POST | `/v4/payments/preapprovedPay/{regKey}/payment` |
| **解除（Expire）** | POST | `/v4/payments/preapprovedPay/{regKey}/expire` |

---

## 認證方式

### 必要 HTTP 標頭

所有 API 請求都需要以下標頭：

| 標頭 | 必填 | 說明 |
|------|------|------|
| `Content-Type` | ● | 固定 `application/json` |
| `X-LINE-ChannelId` | ● | 商家 Channel ID |
| `X-LINE-Authorization-Nonce` | ● | UUID v1/v4 或時間戳，每次請求需唯一 |
| `X-LINE-Authorization` | ● | HMAC-SHA256 簽章（Base64 編碼） |
| `X-LINE-MerchantDeviceProfileId` | ○ | 裝置序號（多裝置場景） |
| `X-LINE-MerchantDeviceType` | ○ | 裝置類型代碼 |

### 簽章字串組合（string-to-sign）⚠️

> **以下公式為依據 LINE Pay v3 慣例推論，正式上線前請對照官方 v4 PDF 驗證**。

**POST 請求**：

```
data = ChannelSecret + ApiPath + JsonRequestBody + Nonce
```

**GET 請求**：

```
data = ChannelSecret + ApiPath + QueryString + Nonce
```

簽章計算：

```
signature = Base64( HMAC-SHA256(key=ChannelSecret, message=data) )
```

其中：

- `ApiPath`：URL 中的 path，例如 `/v4/payments/request`（不含 host、不含 query string）
- `JsonRequestBody`：原始 JSON 字串（與實際送出的 body 一致，**不要重新序列化**）
- `QueryString`：GET 請求的 query 字串（不含 `?`），按參數送出順序串接
- `Nonce`：與 `X-LINE-Authorization-Nonce` 標頭值相同

### Python 簽章範例

```python
import hashlib
import hmac
import base64
import uuid
import json
import requests

CHANNEL_ID = "1234567890"
CHANNEL_SECRET = "your_channel_secret"
BASE_URL = "https://sandbox-api-pay.line.me"

def sign_request(api_path: str, body: str, nonce: str, channel_secret: str) -> str:
    """LINE Pay v4 HMAC-SHA256 簽章（POST）

    ⚠️ string-to-sign 組合方式請對照官方 v4 PDF 驗證
    """
    message = (channel_secret + api_path + body + nonce).encode("utf-8")
    secret = channel_secret.encode("utf-8")
    digest = hmac.new(secret, message, hashlib.sha256).digest()
    return base64.b64encode(digest).decode("utf-8")


def line_pay_post(api_path: str, payload: dict) -> dict:
    body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    nonce = str(uuid.uuid4())
    signature = sign_request(api_path, body, nonce, CHANNEL_SECRET)

    headers = {
        "Content-Type": "application/json",
        "X-LINE-ChannelId": CHANNEL_ID,
        "X-LINE-Authorization-Nonce": nonce,
        "X-LINE-Authorization": signature,
    }

    resp = requests.post(BASE_URL + api_path, data=body.encode("utf-8"), headers=headers, timeout=30)
    return resp.json()
```

### Node.js 簽章範例

```javascript
const crypto = require('crypto');
const { v4: uuidv4 } = require('uuid');

function signRequest(apiPath, body, nonce, channelSecret) {
  // ⚠️ string-to-sign 組合請對照官方 v4 PDF 驗證
  const message = channelSecret + apiPath + body + nonce;
  return crypto
    .createHmac('sha256', channelSecret)
    .update(message)
    .digest('base64');
}

async function linePayPost(apiPath, payload, { channelId, channelSecret, baseUrl }) {
  const body = JSON.stringify(payload);
  const nonce = uuidv4();
  const signature = signRequest(apiPath, body, nonce, channelSecret);

  const resp = await fetch(baseUrl + apiPath, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-LINE-ChannelId': channelId,
      'X-LINE-Authorization-Nonce': nonce,
      'X-LINE-Authorization': signature,
    },
    body,
  });
  return resp.json();
}
```

---

## 訂單建立（Payment Request）

### 端點

```
POST /v4/payments/request
Content-Type: application/json
```

### 請求參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `amount` | Integer | ● | 訂單總金額（須等於 `packages[].amount` 加總） |
| `currency` | String(3) | ● | 幣別 ISO-4217，台灣使用 `TWD` |
| `orderId` | String(100) | ● | 商家訂單編號，需唯一 |
| `packages` | Array | ● | 商品包裝陣列，**至少一筆** |
| `packages[].id` | String(50) | ● | 包裝 ID |
| `packages[].amount` | Integer | ● | 該包裝小計 |
| `packages[].name` | String(100) | ○ | 包裝名稱（顯示在 LINE Pay 結帳頁） |
| `packages[].userFee` | Integer | ○ | 該包裝中的手續費 |
| `packages[].products` | Array | ● | 商品陣列 |
| `packages[].products[].name` | String(4000) | ● | 商品名稱 |
| `packages[].products[].quantity` | Integer | ● | 數量 |
| `packages[].products[].price` | Integer | ● | 單價 |
| `packages[].products[].imageUrl` | String(500) | ○ | 商品圖片 URL（建議 84×84） |
| `packages[].products[].id` | String(50) | ○ | 商家自訂商品 ID |
| `redirectUrls.confirmUrl` | String(500) | ● | 付款後導回網址 |
| `redirectUrls.cancelUrl` | String(500) | ● | 取消付款導回網址 |
| `redirectUrls.confirmUrlType` | String(20) | ○ | `CLIENT`（預設）或 `SERVER` |
| `options.payment.capture` | Boolean | ○ | `true`（預設，confirm 時直接請款）；`false` 為先授權後請款 |
| `options.payment.payType` | String(20) | ○ | `NORMAL`（預設）/ `PREAPPROVED`（自動扣款註冊） |
| `options.display.locale` | String(5) | ○ | 介面語系 `zh_TW` / `en` / `ja` / `ko` |
| `options.display.checkConfirmUrlBrowser` | Boolean | ○ | 是否驗證 `confirmUrl` 開啟瀏覽器 |
| `options.shipping.feeAmount` | Integer | ○ | 運費 |
| `options.shipping.feeInquiryUrl` | String | ○ | 運費試算 URL |
| `options.extra.branchName` | String(100) | ○ | 分店名稱 |
| `options.extra.branchId` | String(32) | ○ | 分店 ID |

### 請求範例

```json
{
  "amount": 1000,
  "currency": "TWD",
  "orderId": "ORD20260507123456",
  "packages": [
    {
      "id": "pkg-001",
      "amount": 1000,
      "name": "經典咖啡組合",
      "products": [
        {
          "id": "prod-001",
          "name": "美式咖啡",
          "imageUrl": "https://example.com/products/americano.jpg",
          "quantity": 2,
          "price": 500
        }
      ]
    }
  ],
  "redirectUrls": {
    "confirmUrl": "https://merchant.example.com/payment/confirm",
    "cancelUrl": "https://merchant.example.com/payment/cancel"
  },
  "options": {
    "payment": {
      "capture": true,
      "payType": "NORMAL"
    },
    "display": {
      "locale": "zh_TW"
    }
  }
}
```

### 回應範例（成功）

```json
{
  "returnCode": "0000",
  "returnMessage": "Success.",
  "info": {
    "transactionId": 2026050712345678910,
    "paymentAccessToken": "187b6e9fe61a44e1a9e6a4e7c7a3fae1",
    "paymentUrl": {
      "web": "https://sandbox-pay.line.me/web/payment/wait?transactionReserveId=...",
      "app": "line://pay/payments/..."
    }
  }
}
```

### 處理流程

1. 商家後端呼叫 `POST /v4/payments/request`
2. 取得 `info.paymentUrl.web`（桌面瀏覽器）或 `info.paymentUrl.app`（行動裝置 LINE App）
3. 將消費者導向上述 URL
4. 消費者在 LINE Pay 介面中授權
5. LINE Pay 將消費者導回 `redirectUrls.confirmUrl`，並附上 `transactionId` 與 `orderId` 的 query string
6. 商家後端呼叫 `POST /v4/payments/{transactionId}/confirm` 完成扣款

---

## 付款確認（Confirm）

當消費者於 LINE Pay 完成授權後，LINE Pay 會以 GET 方式將消費者導回 `confirmUrl`，並附上 query 參數：

```
GET https://merchant.example.com/payment/confirm?transactionId=2026050712345678910&orderId=ORD20260507123456
```

商家收到後**必須**呼叫 confirm API 才會真正扣款。

### 端點

```
POST /v4/payments/{transactionId}/confirm
Content-Type: application/json
```

### 請求參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `amount` | Integer | ● | 須與 request 階段相同 |
| `currency` | String(3) | ● | 須與 request 階段相同 |

### 請求範例

```json
{
  "amount": 1000,
  "currency": "TWD"
}
```

### 回應範例（成功）

```json
{
  "returnCode": "0000",
  "returnMessage": "Success.",
  "info": {
    "orderId": "ORD20260507123456",
    "transactionId": 2026050712345678910,
    "authorizationExpireDate": "2026-05-21T14:30:00Z",
    "regKey": null,
    "payInfo": [
      {
        "method": "CREDIT_CARD",
        "amount": 900,
        "creditCardName": "VISA",
        "creditCardNickname": "我的信用卡",
        "maskedCreditCardNumber": "************1234"
      },
      {
        "method": "POINT",
        "amount": 100
      }
    ],
    "packages": [
      {
        "id": "pkg-001",
        "amount": 1000,
        "userFeeAmount": 0
      }
    ]
  }
}
```

### `payInfo[].method` 對照

| 代碼 | 說明 |
|------|------|
| `CREDIT_CARD` | 信用卡 |
| `BALANCE` | LINE Pay 餘額（LINE Pay Money） |
| `POINT` | LINE Points |

### 重要注意事項

- `confirm` 必須在授權有效期間內呼叫，否則會收到 `1133`（授權過期）類別錯誤
- 若 request 時設定 `options.payment.capture = false`，則 confirm 後僅完成「授權」，須再呼叫 capture 才會請款

---

## 付款狀態查詢

用於查詢付款請求的當前狀態（建議在 confirm 前呼叫，避免重複 confirm）。

### 端點

```
GET /v4/payments/requests/{transactionId}/check
```

### Query 參數

無（端點本身已含 `transactionId`）。

### 回應範例

```json
{
  "returnCode": "0123",
  "returnMessage": "Already completed transaction"
}
```

### 常見 returnCode

| 代碼 | 說明 |
|------|------|
| `0000` | 等待付款 / 可進行 confirm |
| `0110` | 已完成驗證，可進行 confirm |
| `0121` | 消費者取消 / 驗證逾時 |
| `0123` | 付款已完成（不可重複 confirm） |

---

## 請款（Capture）與取消授權（Void）

僅適用於「先授權後請款」流程（Request 時 `options.payment.capture = false`）。

### Capture（請款）

```
POST /v4/payments/authorizations/{transactionId}/capture
```

#### 請求參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `amount` | Integer | ● | 須與授權金額相同（不支援部分請款） |
| `currency` | String(3) | ● | 與授權幣別相同 |

#### 請求範例

```json
{
  "amount": 1000,
  "currency": "TWD"
}
```

### Void（取消授權）

```
POST /v4/payments/authorizations/{transactionId}/void
```

授權後尚未請款，可呼叫 void 釋放授權額度。

#### 請求參數

無 body 內容（或可送空 JSON `{}`）。

### 適用場景

| 場景 | 動作 |
|------|------|
| 先授權後請款（如預訂類服務） | request 時 `capture=false` → confirm（授權）→ capture（出貨時請款） |
| 授權後取消訂單 | 呼叫 void |
| 已請款後退款 | 呼叫 refund（見下節） |

---

## 退款（Refund）

### 端點

```
POST /v4/payments/{transactionId}/refund
Content-Type: application/json
```

### 請求參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `refundAmount` | Integer | ○ | 退款金額；不傳則為全額退款 |

### 請求範例

**全額退款**：

```json
{}
```

**部分退款**：

```json
{
  "refundAmount": 500
}
```

### 回應範例（成功）

```json
{
  "returnCode": "0000",
  "returnMessage": "Success.",
  "info": {
    "refundTransactionId": 2026050712345678999,
    "refundTransactionDate": "2026-05-07T15:30:45Z"
  }
}
```

### 退款規則

- 部分退款支援多次，但累積金額不可超過原交易金額
- 退款後會產生新的 `refundTransactionId`，建議於商家系統儲存以便對帳
- 退款不可逆，請於商家後台完整驗證後再呼叫
- 信用卡退款依各發卡行規定，款項通常 1-3 個工作天內返還

---

## 訂單查詢（Payment Details）

查詢一筆或多筆交易的詳細資料，可用於對帳與客服查詢。

### 端點

```
GET /v4/payments?transactionId=xxx&orderId=xxx&fields=ALL
```

### Query 參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `transactionId` | String / Array | ※ | 交易編號，多筆以逗號分隔，最多 100 筆 |
| `orderId` | String / Array | ※ | 商家訂單編號，多筆以逗號分隔，最多 100 筆 |
| `fields` | String | ○ | `TRANSACTION` / `ORDER` / `ALL`（預設 `ALL`） |

> ※：`transactionId` 和 `orderId` 至少需提供一個。

### 回應範例

```json
{
  "returnCode": "0000",
  "returnMessage": "Success.",
  "info": [
    {
      "transactionId": 2026050712345678910,
      "transactionDate": "2026-05-07T14:00:00Z",
      "transactionType": "PAYMENT",
      "payStatus": "CAPTURE",
      "productName": "美式咖啡",
      "merchantName": "範例咖啡店",
      "currency": "TWD",
      "authorizationExpireDate": null,
      "payInfo": [
        { "method": "CREDIT_CARD", "amount": 900 },
        { "method": "POINT", "amount": 100 }
      ],
      "packages": [
        {
          "id": "pkg-001",
          "amount": 1000,
          "userFeeAmount": 0,
          "name": "經典咖啡組合"
        }
      ],
      "refundList": [
        {
          "refundTransactionId": 2026050712345678999,
          "transactionType": "PARTIAL_REFUND",
          "refundAmount": 500,
          "refundTransactionDate": "2026-05-07T15:30:45Z"
        }
      ],
      "originalTransactionId": null
    }
  ]
}
```

### `payStatus` 對照

| 狀態 | 說明 |
|------|------|
| `AUTHORIZATION` | 已授權，尚未請款 |
| `CAPTURE` | 已請款 |
| `VOIDED_AUTHORIZATION` | 授權已取消 |
| `EXPIRED_AUTHORIZATION` | 授權已過期 |

### `transactionType` 對照

| 類型 | 說明 |
|------|------|
| `PAYMENT` | 付款 |
| `PAYMENT_REFUND` | 全額退款 |
| `PARTIAL_REFUND` | 部分退款 |

---

## 自動扣款 / 一鍵付款（Preapproved Pay）

允許消費者於首次付款時授權商家「綁定卡片」，後續可由商家直接扣款（適合訂閱服務）。

### 啟用方式

於 Payment Request 階段加入：

```json
{
  "options": {
    "payment": {
      "payType": "PREAPPROVED"
    }
  }
}
```

confirm 完成後，回應的 `info.regKey` 即為後續扣款用的金鑰，**請妥善儲存**。

### 檢查 RegKey 狀態

```
GET /v4/payments/preapprovedPay/{regKey}/check?creditCardAuth=true
```

| Query 參數 | 必填 | 說明 |
|------------|------|------|
| `creditCardAuth` | ○ | `true` 時會對綁定卡片進行 NTD 1 元授權測試（並立即取消） |

### 執行扣款

```
POST /v4/payments/preapprovedPay/{regKey}/payment
Content-Type: application/json
```

#### 請求範例

```json
{
  "productName": "月訂閱方案",
  "amount": 199,
  "currency": "TWD",
  "orderId": "SUB20260507000001",
  "capture": true
}
```

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `productName` | String | ● | 商品名稱 |
| `amount` | Integer | ● | 扣款金額 |
| `currency` | String(3) | ● | 幣別 |
| `orderId` | String | ● | 訂單編號（需唯一） |
| `capture` | Boolean | ○ | 是否同時請款，預設 `true` |

### 解除綁定

```
POST /v4/payments/preapprovedPay/{regKey}/expire
```

無 body 內容。執行後該 `regKey` 永久失效，無法再扣款。

---

## 付款通知與回調

### 回調流程

```
┌──────────┐     ┌─────────┐     ┌──────────┐
│ 消費者   │────▶│ LINE Pay│────▶│  商家    │
│ 點擊付款 │     │ 授權    │     │confirmUrl│
└──────────┘     └─────────┘     └──────────┘
                                       │
                                       │ 商家後端
                                       │ POST /confirm
                                       ▼
                                 ┌──────────┐
                                 │ LINE Pay │
                                 │ 完成扣款 │
                                 └──────────┘
```

### confirmUrl 接收參數

LINE Pay 將消費者導回時，會以 GET query string 附上：

| 參數 | 說明 |
|------|------|
| `transactionId` | LINE Pay 交易編號（19 位） |
| `orderId` | 商家訂單編號（與 request 階段相同） |

範例：

```
GET https://merchant.example.com/payment/confirm?transactionId=2026050712345678910&orderId=ORD20260507123456
```

### cancelUrl 接收參數

消費者於 LINE Pay 取消付款時，會被導回 `cancelUrl`，同樣帶有 `transactionId` 與 `orderId`。

### Server-side Confirm（confirmUrlType=SERVER）

若於 request 階段設定 `redirectUrls.confirmUrlType = "SERVER"`，則 LINE Pay 會直接 POST 至 confirmUrl（而非由消費者瀏覽器導回）。此模式適用於**完全 server-to-server** 的整合，但消費者體驗上會看到 LINE Pay 自己的成功頁面。

### 回應 LINE Pay

商家於 confirmUrl 收到請求後，**必須**主動呼叫 `POST /v4/payments/{transactionId}/confirm` 才會完成扣款。LINE Pay 不會被動等待商家回應任何內容。

---

## 錯誤代碼

LINE Pay v4 的回應永遠為 HTTP 200，實際結果在 JSON 的 `returnCode`（成功流程）或 `resultCode`（部分錯誤回應）中。

> 以下為來源文件擷取的代碼，**完整代碼表請以官方 v4 PDF 為準**。

### 成功類

| 代碼 | 說明 |
|------|------|
| `0000` | 成功 |
| `0110` | 消費者已驗證，可進行付款授權 |
| `0123` | 付款已完成 |

### 流程相關

| 代碼 | 說明 | 處理建議 |
|------|------|----------|
| `0121` | 消費者取消 / 驗證逾時 | 顯示取消頁，引導重新下單 |
| `1145` | 付款進行中 | 等待數秒後重新查詢狀態 |
| `1198` | 重複 API 請求 | 檢查是否已成功，避免重送 |

### 商家相關

| 代碼 | 說明 | 處理建議 |
|------|------|----------|
| `1101` | 非 LINE Pay 用戶 | 引導消費者改用其他支付方式 |
| `1104` | 商家未註冊 | 確認 ChannelId 與環境（沙箱/正式）是否正確 |
| `1105` | 該商家無法使用 LINE Pay | 聯繫 LINE Pay 客服確認帳號狀態 |
| `1124` | 金額錯誤 | 檢查 amount 與 packages 加總是否一致 |

### 查詢相關

| 代碼 | 說明 |
|------|------|
| `1150` | 查無交易紀錄 |
| `1177` | 超過單次最多可查詢筆數（100 筆） |

### 系統 / 格式相關

| 代碼 | 說明 | 處理建議 |
|------|------|----------|
| `1199` | 內部錯誤 | 等待後重試；持續失敗請聯繫 LINE Pay |
| `2101` | 參數錯誤 | 檢查必填欄位、長度、格式 |
| `2102` | JSON 格式錯誤 | 確認 body 為合法 JSON、編碼為 UTF-8 |

### 簽章 / 認證相關（需驗證）⚠️

> 以下代碼於擷取資料中未明確列出，但實務上常見：

| 代碼 | 推測說明 |
|------|----------|
| `1102` | 認證失敗（簽章錯誤） |
| `1106` | 標頭資訊錯誤 |
| `1133` | 授權過期 / 已 confirm |
| `1141` | 帳號驗證失敗 |
| `1142` | 餘額不足 |
| `1170` | 退款金額錯誤 |
| `1172` | 已退款交易 |
| `1183` | 授權尚未完成，無法 capture |

---

## 支付方式對照表

LINE Pay 內部會自動依消費者選擇與綁定狀態組合金流來源：

| 支付方式 | `payInfo[].method` | 說明 |
|----------|--------------------|------|
| 信用卡 | `CREDIT_CARD` | 消費者於 LINE Pay 內綁定的信用卡 |
| LINE Pay 餘額 | `BALANCE` | LINE Pay Money（一卡通帳戶餘額） |
| LINE Points | `POINT` | LINE Points 點數折抵 |

### 不適用的支付方式

LINE Pay v4 **不直接整合** Apple Pay 或 Google Pay。消費者使用 LINE Pay 時所看到的「信用卡」即為其於 LINE Pay 內綁定的卡片，並非透過 Apple/Google 錢包扣款。

### 各市場差異

- **台灣**：支援信用卡、LINE Pay Money（一卡通）、LINE Points
- **日本**：支援信用卡、LINE Pay 餘額、LINE Points
- **泰國**：支援信用卡、Rabbit LINE Pay 等

本文件以**台灣 TWD** 整合情境為主。

---

## 常見問題排解

### 簽章驗證失敗

**問題**：收到 `1102` 或類似認證錯誤。

**檢查項目**：

1. `X-LINE-ChannelId` 是否與 ChannelSecret 為同一組（沙箱與正式不可混用）
2. `X-LINE-Authorization-Nonce` 是否每次都產生新的 UUID（**不可重複使用**）
3. 簽章時的 body 字串是否與實際 HTTP 送出的 body **完全一致**（不要在簽章後再次 stringify）
4. ApiPath 是否含 query string（GET 不含 `?`，但 query 字串需加在 path 之後）
5. 編碼是否為 UTF-8

### TransactionId 精度遺失

**問題**：JavaScript 收到 `transactionId` 後變成 `2026050712345679000`（末尾被改寫）。

**原因**：JS `Number` 為 64-bit 浮點，安全整數上限為 `Number.MAX_SAFE_INTEGER = 9007199254740991`，而 LINE Pay transactionId 為 19 位整數會超過。

**解法**：

```javascript
// 將 JSON 中的大整數先解析為字串
const text = await response.text();
const data = JSON.parse(text.replace(
  /"transactionId":\s*(\d+)/g,
  '"transactionId":"$1"'
));
// 後續以字串處理
```

或使用 `bigint-json-native` / `json-bigint` 套件。Python 不會有此問題（原生支援任意精度整數）。

### 重複 confirm

**問題**：使用者重整付款結果頁，導致 confirm API 被呼叫多次。

**解法**：

1. 商家於資料庫中記錄 `transactionId` 的處理狀態
2. confirm 前先查詢狀態（GET `/v4/payments/requests/{transactionId}/check`）
3. 若狀態為 `0123`（已完成），改為查詢交易詳情（GET `/v4/payments?transactionId=...`）

### 沙箱與正式環境憑證不通用

**問題**：使用沙箱憑證打到正式環境（或反之），收到 `1104`。

**解法**：

- 沙箱：`https://sandbox-api-pay.line.me`
- 正式：`https://api-pay.line.me`
- 兩組環境的 ChannelId / ChannelSecret **完全不同**，請於程式中以環境變數區分。

### confirmUrl 沒有收到回調

**檢查項目**：

1. `confirmUrl` 是否為 HTTPS（HTTP 不被接受）
2. 是否從外網可存取（不可為 `localhost` 或內網 IP）
3. 域名是否於 LINE Pay 商家後台登錄
4. 防火牆是否阻擋 LINE Pay 來源 IP

### 退款失敗

**常見原因**：

1. 已超過退款期限（信用卡通常 180 天內，依發卡行而異）
2. 退款金額大於剩餘可退金額
3. 已使用 LINE Points 折抵的部分不可退至原 Points 帳戶（會以餘額退回）

---

## 來源資料缺口（Source Gaps）

本文件標示為 ⚠️ 的內容為依據 LINE Pay v3 慣例「推論」而來，**正式上線前須對照官方 v4 PDF 驗證**：

| 項目 | 來源狀態 | 建議動作 |
|------|----------|----------|
| HMAC `string-to-sign` 組合公式 | 推論自 v3 | 對照官方 v4 PDF 第「Authentication」章節 |
| 完整錯誤代碼表 | 來源僅含 15 組 | 取得官方 PDF 完整 result code 表 |
| Capture / Void 完整 schema | 端點路徑確認，schema 為依慣例補上 | 對照官方 PDF |
| Preapproved Pay 詳細欄位 | 端點路徑確認，schema 為依慣例補上 | 對照官方 PDF |
| Server-side confirm 實際 payload 範例 | 未於來源中明確列出 | 對照官方 PDF |
| 簽章類錯誤代碼（1102, 1106 等） | 推論自常見 LINE Pay 文件 | 對照官方 PDF 完整代碼表 |

**官方資源**：

- 開發者中心：https://developers-pay.line.me/zh/online-api-v4
- LINE Pay 商家後台：https://pay.line.me/portal/global/auth/login
- 客服信箱：依各市場為準（台灣為 LINE Pay Taiwan）

---

最後更新：2026/05/07
