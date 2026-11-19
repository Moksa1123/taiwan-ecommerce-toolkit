# LINE Pay Online API v4 Reference

> 目錄精簡版：只含參考文件與 JSON 資料，不含腳本。文中提到 `scripts/`、`examples/`、`tests/` 的工具在完整版（npm 套件 `taiwan-payment-skill`）。
> 金鑰與商店代號由使用者在自己的系統設定後，以參數傳入程式；文中以 `<HASH_KEY>` 這類佔位字表示。服務商公開的測試金鑰也以佔位字表示，請到該服務商官方文件取得。帳密類欄位以 `<帳密欄位>` 表示。

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
16. [官方來源](#官方來源)

---

## 基本說明

### 什麼是 LINE Pay Online API v4

LINE Pay 是 LINE Corporation 提供的電子支付服務，整合了信用卡、LINE Points、LINE Pay Money 等多種支付來源。

### 版本

| 版本 | 狀態（官方 API change log，2025-11） |
|------|------|
| Online API v4 | 2025-11 新增，因應台灣電子支付機構（EPI）規範。與 v3 相比：`info.paymentProvider`（`TSP` / `EPI`）加進 confirm、capture、查詢、自動扣款的回應；payment request 新增 `options.regPayRequest` |
| Online API v3 | 仍為現行版本（官方：不需要知道 payment provider 類型可繼續用 v3）；官方文件未公布停用日期 |

兩版端點路徑只差 `/v3` ↔ `/v4` 前綴，簽章方式相同。線上付款的 `paymentProvider` 目前一律為 `"TSP"`（官方：EPI 交易不適用於線上付款情境）。

### 整合特性

| 特性 | 說明 |
|------|------|
| **協定** | RESTful HTTPS + JSON |
| **認證** | HMAC-SHA256 簽章（標頭 `X-LINE-Authorization`） |
| **HTTP 狀態碼** | API **永遠回傳 HTTP 200**，實際結果由 JSON 中的 `returnCode` 判斷 |
| **TransactionId** | 19 位數整數，以 64 位 `long`/`int64` 處理；無法處理 64 位整數的平台改用字串 |
| **幣別** | `USD` / `TWD` / `THB` |

### 商務面前置作業

1. 申請 LINE Pay 商家帳號（Merchant Account）
2. 開通 Online API 服務
3. 自商家後台取得 **Channel ID** 與 **Channel Secret**
4. 準備導回頁面（`confirmUrl`、`cancelUrl`），每次 payment request 時於 `redirectUrls` 帶入

> 簽章公式與 LINE Pay 官方 developers-pay.line.me/online/prerequisites 相同（v3、v4 一致，只有路徑前綴不同），並與 yidas/line-pay-sdk-php、wpbr-linepay-tw 1.3.3 的實際輸出逐字比對（`tests/vectors/linepay.json`）。

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

- 尚未成為 LINE Pay 商家：在 developers-pay.line.me/sandbox 申請沙箱帳號，再到商家後台「Developer Tools > Manage Link Key」取得沙箱用 Channel ID / Channel Secret
- 已是正式商家：**直接用正式的 Channel ID / Channel Secret 打沙箱**，不必另外申請
- 沙箱不支援 `info.paymentUrl.app`（App 跳轉），測試請用 `info.paymentUrl.web`
- 沙箱商品圖片 `imageUrl` 非 HTTPS 可能顯示不出來（正式環境不受影響）
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

read timeout 為官方各端點頁面的建議下限。

### 一般付款流程

| 功能 | Method | Path | read timeout |
|------|--------|------|------|
| **建立付款請求** | POST | `/v4/payments/request` | 10 秒 |
| **查詢付款請求狀態** | GET | `/v4/payments/requests/{transactionId}/check` | 20 秒 |
| **付款確認（授權）** | POST | `/v4/payments/{transactionId}/confirm` | 40 秒 |
| **訂單查詢** | GET | `/v4/payments` | 20 秒 |

### 授權後操作

| 功能 | Method | Path | read timeout |
|------|--------|------|------|
| **請款（Capture）** | POST | `/v4/payments/authorizations/{transactionId}/capture` | 60 秒 |
| **取消授權（Void）** | POST | `/v4/payments/authorizations/{transactionId}/void` | 20 秒 |
| **退款（Refund）** | POST | `/v4/payments/{transactionId}/refund` | 20 秒 |

### 自動扣款（Preapproved Pay）

| 功能 | Method | Path | read timeout |
|------|--------|------|------|
| **檢查 RegKey 狀態** | GET | `/v4/payments/preapprovedPay/{regKey}/check` | 20 秒 |
| **扣款** | POST | `/v4/payments/preapprovedPay/{regKey}/payment` | 20 秒 |
| **解除（Expire）** | POST | `/v4/payments/preapprovedPay/{regKey}/expire` | 20 秒 |

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

### 簽章字串組合（string-to-sign）

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

<!-- verify: linepay-sign -->
```python
import base64
import hashlib
import hmac
import json
import uuid

import requests

CHANNEL_ID = "1234567890"
CHANNEL_SECRET = "<channel_secret>"
BASE_URL = "https://sandbox-api-pay.line.me"


def sign_request(api_path: str, body_or_query: str, nonce: str, channel_secret: str) -> str:
    """Base64(HMAC-SHA256(ChannelSecret, ChannelSecret + ApiPath + (body | query string) + Nonce))"""
    message = (channel_secret + api_path + body_or_query + nonce).encode("utf-8")
    digest = hmac.new(channel_secret.encode("utf-8"), message, hashlib.sha256).digest()
    return base64.b64encode(digest).decode("utf-8")


def line_pay_post(api_path: str, payload: dict) -> dict:
    # 簽章用的字串必須與實際送出的 body 逐字相同，所以只序列化一次
    body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    nonce = str(uuid.uuid4())
    headers = {
        "Content-Type": "application/json",
        "X-LINE-ChannelId": CHANNEL_ID,
        "X-LINE-Authorization-Nonce": nonce,
        "X-LINE-Authorization": sign_request(api_path, body, nonce, CHANNEL_SECRET),
    }
    resp = requests.post(BASE_URL + api_path, data=body.encode("utf-8"), headers=headers, timeout=30)
    return resp.json()
```

### Node.js 簽章範例

<!-- verify: linepay-sign -->
```javascript
import crypto from 'crypto';

function signRequest(apiPath, bodyOrQuery, nonce, channelSecret) {
  const message = channelSecret + apiPath + bodyOrQuery + nonce;
  return crypto.createHmac('sha256', channelSecret).update(message).digest('base64');
}

async function linePayPost(apiPath, payload, { channelId, channelSecret, baseUrl }) {
  const body = JSON.stringify(payload);          // 簽章與送出使用同一個字串
  const nonce = crypto.randomUUID();
  const resp = await fetch(baseUrl + apiPath, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-LINE-ChannelId': channelId,
      'X-LINE-Authorization-Nonce': nonce,
      'X-LINE-Authorization': signRequest(apiPath, body, nonce, channelSecret),
    },
    body,
  });
  // transactionId 為 19 位數，超過 Number.MAX_SAFE_INTEGER；JSON.parse 會失去精度，
  // 需以字串方式讀取（例如先把數字替換成字串再 parse，或使用支援 BigInt 的 JSON 解析器）
  return resp.text();
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
| `amount` | Number | ● | 付款金額（須等於 `packages[].amount` 加總） |
| `currency` | String(3) | ● | 幣別 ISO 4217：`USD` / `TWD` / `THB` |
| `orderId` | String(100) | ● | 商家訂單編號，需唯一（重複會回 `1172`） |
| `packages[]` | Array | ● | 商品包裝陣列（依出貨單位或店家區分） |
| `packages[].id` | String(50) | ● | 包裝 ID |
| `packages[].amount` | Number | ● | 該包裝小計＝Σ `products[].price` × `products[].quantity` |
| `packages[].name` | String(100) | ○ | 包裝名稱或出貨商家名稱 |
| `packages[].products[]` | Array | ● | 商品陣列 |
| `packages[].products[].name` | String(4000) | ● | 商品名稱 |
| `packages[].products[].quantity` | Number | ● | 數量 |
| `packages[].products[].price` | Number | ● | 單價 |
| `packages[].products[].originalPrice` | Number | ○ | 原價 |
| `packages[].products[].imageUrl` | String(500) | ○ | 商品圖片 URL |
| `packages[].products[].id` | String(50) | ○ | 商家自訂商品 ID |
| `redirectUrls` | Object | ● | 導回網址設定 |
| `redirectUrls.confirmUrl` | String(500) | ● | 消費者完成 LINE Pay 認證後的導回網址 |
| `redirectUrls.cancelUrl` | String(500) | ● | 消費者取消付款的導回網址 |
| `redirectUrls.confirmUrlType` | String | ○ | `CLIENT`（預設，由 LINE App／彈出視窗導回）/ `SERVER`（LINE Pay 伺服器直接呼叫 confirmUrl）/ `NONE`（不導回，商家自行輪詢 check API） |
| `redirectUrls.appPackageName` | String(4000) | ○ | Android App 間切換時要返回的 App package name（防釣魚） |
| `options` | Object | ● | 付款請求設定（官方欄位表標為必填） |
| `options.payment.capture` | Boolean | ○ | `true`（預設，confirm 時同時請款）；`false` 為先授權後請款 |
| `options.payment.payType` | String | ○ | `NORMAL`（一般付款）/ `PREAPPROVED`（自動扣款） |
| `options.display.locale` | String | ○ | 付款等待頁語系（BCP-47），預設 `en`；可用 `en` / `ja` / `ko` / `th` / `zh_TW` / `zh_CN` |
| `options.display.checkConfirmUrlBrowser` | Boolean | ○ | 預設 `false`；`true` 時若消費者不在原本發起付款的瀏覽器，會提示回到原瀏覽器 |
| `options.extra.branchName` | String(200) | ○ | 分店名稱（僅英數與特殊字元） |
| `options.extra.branchId` | String(32) | ○ | 分店 ID（超長會被截斷顯示） |
| `options.extra.promotionRestriction.rewardLimit` | Number | ● (物件存在時) | 依法規不能套用回饋的金額（僅台灣） |
| `options.extra.promotionRestriction.useLimit` | Number | ○ | 不能折抵或用點數的金額（僅台灣） |
| `options.events[].code` | String(30) | ○ | 與 LINE Pay 約定的促銷活動代碼 |
| `options.events[].totalAmount` | Number | ○ | 固定比例回饋活動的適用金額 |
| `options.events[].productQuantity` | Number | ○ | 固定金額回饋活動的適用數量 |
| `options.regPayRequest` | Object | ○ | 自動扣款設定（v4 新增），見[自動扣款](#自動扣款--一鍵付款preapproved-pay) |

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
    "paymentUrl": {
      "web": "https://sandbox-web-pay.line.me/web/payment/wait?transactionReserveId=...",
      "app": "line://pay/payment/..."
    },
    "transactionId": 2026050712345678910,
    "paymentAccessToken": "056579816895"
  }
}
```

| 回應欄位 | 說明 |
|------|------|
| `info.paymentUrl.web` | LINE Pay 付款等待頁；以彈出視窗開啟時建議 700 × 546 px |
| `info.paymentUrl.app` | 從商家 App 跳到 LINE Pay App 的 deep link（沙箱不支援） |
| `info.transactionId` | 交易編號（19 位數） |
| `info.paymentAccessToken` | 消費者在 LINE Pay App 改用手動輸入代碼（不掃碼）時的代碼 |

### 處理流程

1. 商家後端呼叫 `POST /v4/payments/request`
2. 取得 `info.paymentUrl.web`（瀏覽器）或 `info.paymentUrl.app`（App 跳轉）
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
| `amount` | Number | ● | 須與 request 階段相同 |
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
    "payInfo": [
      {
        "method": "CREDIT_CARD",
        "amount": 900,
        "creditCardBrand": "VISA",
        "creditCardNickname": "我的信用卡",
        "maskedCreditCardNumber": "**** **** **** 1234"
      },
      {
        "method": "POINT",
        "amount": 100
      }
    ],
    "packages": [
      {
        "id": "pkg-001",
        "amount": 1000
      }
    ],
    "paymentProvider": "TSP"
  }
}
```

### 回應 `info` 欄位

| 欄位 | 說明 |
|------|------|
| `orderId` | 商家訂單編號 |
| `transactionId` | 交易編號（19 位數） |
| `authorizationExpireDate` | 授權到期時間（ISO 8601）；只有先授權後請款時回傳，到期前要 capture |
| `regKey` | 自動扣款金鑰；只有 `payType=PREAPPROVED` 時回傳 |
| `payInfo[].method` | `CREDIT_CARD`（含簽帳金融卡）/ `BALANCE`（LINE Pay Money）/ `POINT`（LINE POINTS） |
| `payInfo[].amount` | 該付款方式金額 |
| `payInfo[].creditCardBrand` | `VISA` / `MASTER` / `AMEX` / `DINERS` / `JCB` |
| `payInfo[].creditCardNickname` | 消費者在 LINE Pay 設定的卡片暱稱；未設定為空字串 |
| `payInfo[].maskedCreditCardNumber` | 遮罩卡號；僅台灣、需另外申請 |
| `packages[].id` / `packages[].amount` | 包裝 ID 與金額 |
| `merchantReference.affiliateCards[]` | 電子發票載具或聯名卡資訊（`cardType="MOBILE_CARRIER"` 時 `cardId` 為手機條碼）；僅台灣、需向 LINE Pay 申請 |
| `paymentProvider` | v4 新增：`TSP` / `EPI`；`null` 視同 `TSP` |

### 重要注意事項

- 若 request 時設定 `options.payment.capture = false`，則 confirm 後僅完成「授權」，須在 `authorizationExpireDate` 前呼叫 capture（或 void）
- 消費者認證後逾時才 confirm 可能收到 `1180`（Payment time expired）

---

## 付款狀態查詢

查詢消費者是否已完成 LINE Pay 認證。主要用於 `confirmUrlType=NONE`（不導回）的流程：每隔至少 1 秒呼叫一次，拿到 `0110` 再 confirm。

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
| `0000` | 消費者尚未完成 LINE Pay 認證 |
| `0110` | 已完成認證，可進行 confirm |
| `0121` | 消費者取消 / 認證等待逾時 |
| `0122` | 付款失敗 |
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
| `amount` | Number | ● | 請款金額（官方：可與 payment request 時的金額不同） |
| `currency` | String(3) | ● | `USD` / `TWD` / `THB` |

#### 請求範例

```json
{
  "amount": 1000,
  "currency": "TWD"
}
```

#### 回應

`info` 含 `orderId`、`transactionId`、`payInfo[]`（`method`、`amount`）、`paymentProvider`（v4 新增）。

回 `1199` 或 `1280`–`1298` 時，該筆付款會**自動取消**，不要再重試 capture。

### Void（取消授權）

```
POST /v4/payments/authorizations/{transactionId}/void
```

授權後尚未請款，可呼叫 void 取消授權。已請款（含自動請款）的交易不能 void，只能退款。

#### 請求參數

無 body。

回 `1900`、`1902`、`1999` 時可重試。

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
| `refundAmount` | Number | ○ | 部分退款金額；不傳則為全額退款 |

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

- 退款會產生新的 `refundTransactionId`，請儲存以便對帳
- 相關代碼：`1163` 已過退款期限、`1164` 超過可退金額、`1165` 已退過款、`2042` 商家退款準備金不足致 EPI 交易無法退款
- 回 `1900`、`1902`、`1999` 時可重試

---

## 訂單查詢（Payment Details）

查詢已 confirm 或已請款交易的詳細資料，可用於對帳與客服查詢。

### 端點

```
GET /v4/payments?transactionId=xxx&orderId=xxx
```

### Query 參數

| 參數 | 必填 | 說明 |
|------|------|------|
| `transactionId[]` | ※ | 一或多個交易編號 |
| `orderId[]` | ※ | 一或多個商家訂單編號 |

> ※：`transactionId` 和 `orderId` 至少需提供一個。一次查詢超過 100 筆回 `1177`。

### 回應範例

```json
{
  "returnCode": "0000",
  "returnMessage": "Success.",
  "info": [
    {
      "transactionId": 2026050712345678910,
      "orderId": "ORD20260507123456",
      "transactionDate": "2026-05-07T14:00:00Z",
      "transactionType": "PAYMENT",
      "payStatus": "CAPTURE",
      "productName": "美式咖啡",
      "merchantName": "範例咖啡店",
      "currency": "TWD",
      "payInfo": [
        { "method": "CREDIT_CARD", "amount": 900 },
        { "method": "POINT", "amount": 100 }
      ],
      "packages": [
        {
          "id": "pkg-001",
          "amount": 1000,
          "name": "經典咖啡組合",
          "products": [
            { "id": "prod-001", "name": "美式咖啡", "quantity": 2, "price": 500 }
          ]
        }
      ],
      "paymentProvider": "TSP",
      "refundList": [
        {
          "refundTransactionId": 2026050712345678999,
          "transactionType": "PARTIAL_REFUND",
          "refundAmount": 500,
          "refundTransactionDate": "2026-05-07T15:30:45Z"
        }
      ]
    }
  ]
}
```

`originalTransactionId`（原付款交易編號）、`payInfo[]`、`refundList[]` 只在查詢有退款紀錄的交易時回傳；`authorizationExpireDate` 為授權到期時間。

### `payStatus` 對照

| 狀態 | 說明 |
|------|------|
| `AUTHORIZATION` | 已 confirm（授權），尚未請款 |
| `CAPTURE` | 已請款 |
| `VOIDED_AUTHORIZATION` | 授權已取消 |
| `EXPIRED_AUTHORIZATION` | 授權已過期（未在期限內請款） |

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

v4 可在 payment request 加上 `options.regPayRequest` 描述扣款方式：

| 欄位 | 類型 | 說明 |
|------|------|------|
| `regPayPeriodType` | String | `RECURRING`（定期）/ `NON_RECURRING`（不定期，一般自動扣款） |
| `productPrice` | Number | 自動扣款金額 |
| `perTransactionLimit` | Number | 不定期扣款的單筆上限（`NON_RECURRING` 時用） |
| `recurringPeriod` | String | 定期扣款週期：`WEEK` / `MONTH` / `YEAR` |
| `recurringDayOfWeek` | String | `WEEK` 時的星期：`SUN`…`SAT`；其他週期須為 `null` |
| `recurringDay` | Number | `MONTH` / `YEAR` 時的日期 1–31；其他週期須為 `null` |
| `recurringMonth` | Number | `YEAR` 時的月份 1–12；其他週期須為 `null` |

### 檢查 RegKey 狀態

```
GET /v4/payments/preapprovedPay/{regKey}/check?creditCardAuth=true
```

| Query 參數 | 必填 | 說明 |
|------------|------|------|
| `creditCardAuth` | ○ | `true`：除 LINE Pay 驗證外，再對信用卡做最低金額授權驗證（需 LINE Pay 核准才能用）；`false`：只做 LINE Pay 驗證 |

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
| `amount` | Number | ● | 扣款金額 |
| `orderId` | String(100) | ● | 訂單編號（需唯一） |
| `productName` | String(4000) | ○ | 商品名稱（官方欄位表標選填，範例有帶） |
| `currency` | String(3) | ○ | `USD` / `TWD` / `THB`（官方欄位表標選填，範例有帶） |
| `capture` | Boolean | ○ | 是否同時請款，預設 `true` |

回應 `info`：`transactionId`、`transactionDate`、`orderId`、`authorizationExpireDate`（`capture=false` 時）、`paymentProvider`（v4 新增）。

回 `1141`、`1282`–`1287`、`1290`–`1295` 表示 regKey 已失效，需請消費者重新綁定。

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

LINE Pay 以 HTTP GET 呼叫 confirmUrl（連線逾時 5 秒、讀取逾時 20 秒），並自動附上 query string：

| 參數 | 說明 |
|------|------|
| `transactionId` | LINE Pay 交易編號（19 位），依平台可能要當字串處理 |
| `orderId` | 商家訂單編號（與 request 階段相同） |

不要自己把這兩個參數寫進 confirmUrl；若網址已含 `orderId`，LINE Pay 只會補上其餘參數。

範例：

```
GET https://merchant.example.com/payment/confirm?transactionId=2026050712345678910&orderId=ORD20260507123456
```

頁面須使用受信任憑證的 HTTPS（官方：建議），支援 TLS 1.2 以上。

### cancelUrl 接收參數

消費者於 LINE Pay 取消付款時，會被導回 `cancelUrl`（GET，逾時同上）；`transactionId` 與 `orderId` 為**視情況**附帶，不保證一定有。

### confirmUrlType=SERVER

由 LINE Pay 伺服器直接呼叫 confirmUrl，而不是從 LINE App／彈出視窗把消費者導回。此模式需在防火牆允許 LINE Pay 的來源 IP：

| 環境 | 來源 IP |
|------|------|
| 沙箱 | `147.92.159.209`、`147.92.159.21`、`147.92.159.68`、`147.92.216.167` |
| 正式 | `211.249.40.1`～`211.249.40.30`、`147.92.220.5`～`147.92.220.8` |

### confirmUrlType=NONE

不導回；LINE Pay 伺服器不會對商家發出任何 HTTP 請求。商家每隔至少 1 秒呼叫 `GET /v4/payments/requests/{transactionId}/check`，拿到 `0110` 再 confirm。

### 回應 LINE Pay

商家於 confirmUrl 收到請求後，**必須**主動呼叫 `POST /v4/payments/{transactionId}/confirm` 才會完成扣款。LINE Pay 不會被動等待商家回應任何內容。

---

## 錯誤代碼

回應永遠是 HTTP 200。正常回應的結果在 `returnCode` / `returnMessage`（失敗時不帶 `info`）；官方另列錯誤回應範例為 `{"resultCode": 1104, "statusMessage": "Merchant not found."}`，解析時兩組欄位都要接。沒有對應訊息時 `returnMessage` 為 `-`。

> 依 LINE Pay Online API v4 官方結果代碼表（developers-pay.line.me/online-api-v4#result-code，2026-11-17 擷取）。完整清單見 `data/error-codes.csv`。

### 狀態類

| 代碼 | 官方說明 |
|------|------|
| `0000` | 成功；用於付款請求狀態查詢時，表示消費者尚未完成 LINE Pay 認證 |
| `0110` | 消費者已完成認證，可進行 confirm |
| `0121` | 消費者取消付款，或認證等待逾時 |
| `0122` | 付款失敗 |
| `0123` | 付款已完成 |

### 認證 / 商家設定

| 代碼 | 官方說明 | 處理建議 |
|------|------|------|
| `1104` | 商家未在商家後台註冊，請確認憑證 | 確認 ChannelId 與環境（沙箱/正式） |
| `1105` | 該商家目前無法使用 LINE Pay | 聯繫 LINE Pay 確認帳號狀態 |
| `1106` | Request header 資訊有誤 | 官方 FAQ：Online API 簽章（MAC）錯誤即回此碼，見[簽章驗證失敗](#簽章驗證失敗) |
| `1178` | 商家不支援該幣別 | |
| `1194` | 該商家不能使用自動扣款 | |
| `2024` | 超過商家單筆、每日或每月收款上限 | 僅英文版代碼表列出 |

### 消費者 / 付款

| 代碼 | 官方說明 |
|------|------|
| `1101` | 消費者不是 LINE Pay 用戶 |
| `1102` | 消費者目前無法以 LINE Pay 交易 |
| `1110` | 信用卡無法使用 |
| `1141` | 帳戶狀態有問題（EPI 交易：商家可能未啟用 EPI 付款方式；自動扣款：消費者可能已解除 regKey，需重新取得） |
| `1142` | 餘額不足 |
| `1169` | 需在 LINE Pay 選擇付款方式並輸入密碼 |
| `1170` | 會員帳戶餘額已變動 |
| `1180` | 付款時間已過期 |
| `1280`–`1298` | 信用卡付款錯誤（暫時錯誤、授權失敗、疑似盜刷、卡片停用、超過額度、CVN 錯誤、黑名單卡等）；capture 時回這些碼，付款會被自動取消 |

### 金額 / 訂單

| 代碼 | 官方說明 | 處理建議 |
|------|------|------|
| `1124` | 金額資訊錯誤 | 檢查 amount 與 packages 加總、confirm 金額是否與 request 一致 |
| `1145` | 付款進行中 | 稍後以 check API 查詢 |
| `1152` | 重複交易 | |
| `1153` | 付款請求金額與請款金額不同 | |
| `1172` | 已存在相同 orderId 的交易 | orderId 需唯一 |
| `1183` | 付款金額須高於設定的最低金額 | |
| `1184` | 付款金額不可超過設定的最高金額 | |

### 查詢 / 交易狀態

| 代碼 | 官方說明 |
|------|------|
| `1150` | 查無交易紀錄 |
| `1155` | 無效的交易編號 |
| `1159` | 查無付款請求資訊 |
| `1177` | 超過單次最多可查詢筆數（100） |

### 退款

| 代碼 | 官方說明 |
|------|------|
| `1163` | 無法退款（已過退款期限） |
| `1164` | 超過可退款金額 |
| `1165` | 該交易已退款 |
| `2042` | 商家退款準備金不足，EPI 交易無法退款（僅中文版代碼表列出；英文版退款端點的相關錯誤也列此碼） |

### 自動扣款

| 代碼 | 官方說明 |
|------|------|
| `1154` | 自動扣款所選付款方式無法使用 |
| `1190` | 沒有該自動扣款金鑰 |
| `1193` | 自動扣款金鑰已過期 |

### 系統 / 格式

| 代碼 | 官方說明 | 處理建議 |
|------|------|------|
| `1179` | 目前無法處理 | 稍後重試 |
| `1198` | 重複的 API 請求 | 先查詢是否已成功，避免重送 |
| `1199` | 請求處理時發生內部錯誤 | 等待後重試；capture 時回此碼付款會被自動取消 |
| `190X` | 暫時錯誤，請稍後重試 | void / refund 回 `1900`、`1902`、`1999` 可重試 |
| `2101` | 參數錯誤 | 檢查必填欄位、長度、格式 |
| `2102` | JSON 格式錯誤 | 確認 body 為合法 JSON、UTF-8 |
| `9000` | 內部錯誤 | |

`1133` 不在 Online API 代碼表中（官方 FAQ 只在 Offline API 沙箱情境提到）。

---

## 支付方式對照表

LINE Pay 內部會自動依消費者選擇與綁定狀態組合金流來源：

| 支付方式 | `payInfo[].method` | 說明 |
|----------|--------------------|------|
| 信用卡 | `CREDIT_CARD` | 消費者於 LINE Pay 內綁定的信用卡（含簽帳金融卡） |
| LINE Pay 餘額 | `BALANCE` | LINE Pay Money |
| LINE POINTS | `POINT` | LINE POINTS 點數折抵 |

### 不適用的支付方式

LINE Pay v4 **不直接整合** Apple Pay 或 Google Pay。消費者使用 LINE Pay 時所看到的「信用卡」即為其於 LINE Pay 內綁定的卡片，並非透過 Apple/Google 錢包扣款。

### 市場

API 幣別只有 `USD` / `TWD` / `THB`。LINE Pay 日本已終止服務（官方 API change log 2025-05），日本專用欄位與 Deposit API 已移除。本文件以**台灣 TWD** 整合情境為主。

---

## 常見問題排解

### 簽章驗證失敗

**問題**：收到 `1106`（官方 FAQ：Online API 的 MAC 不正確時回此碼）。

**檢查項目**：

1. `X-LINE-ChannelId` 是否與 ChannelSecret 為同一組
2. `X-LINE-Authorization-Nonce` 是否每次都產生新的 UUID（v1/v4）或時間戳
3. 簽章時的 body 字串是否與實際 HTTP 送出的 body **完全一致**；序列化時多出的空白或欄位順序不同都會讓 MAC 不同
4. GET 的簽章字串是 `ChannelSecret + ApiPath + QueryString + Nonce`，QueryString 不含 `?`
5. 編碼是否為 UTF-8

### TransactionId 精度遺失

**問題**：JavaScript 收到 `transactionId` 後變成 `2026050712345679000`（末尾被改寫）。

**原因**：JS `Number` 為 64-bit 浮點，安全整數上限為 `Number.MAX_SAFE_INTEGER = 9007199254740991`，而 LINE Pay transactionId 為 19 位整數會超過。`refundTransactionId`、`originalTransactionId` 也一樣。

**解法**（官方 online-api-v4#transaction-id 的做法：先當純文字，把 16 位以上的數字轉成字串再 parse）：

```javascript
function handleBigInteger(text) {
  const largeNumberRegex = /:\s*(\d{16,})\b/g;
  return JSON.parse(text.replace(largeNumberRegex, ': "$1"'));
}

const data = handleBigInteger(await response.text());
```

或使用 `json-bigint` 等支援大整數的解析器。Python 不會有此問題（原生支援任意精度整數）。

### 重複 confirm

**問題**：使用者重整付款結果頁，導致 confirm API 被呼叫多次。

**解法**：

1. 商家於資料庫中記錄 `transactionId` 的處理狀態
2. confirm 前先查詢狀態（GET `/v4/payments/requests/{transactionId}/check`）
3. 若狀態為 `0123`（已完成），改為查詢交易詳情（GET `/v4/payments?transactionId=...`）

### 沙箱與正式環境

- 沙箱：`https://sandbox-api-pay.line.me`
- 正式：`https://api-pay.line.me`
- 沙箱帳號申請的 Channel ID / Secret 只能打沙箱；正式商家的 Channel ID / Secret 可同時用於沙箱與正式（官方 FAQ）
- 收到 `1104` 時先確認憑證與環境是否對應

### confirmUrl 沒有收到回調

**檢查項目**：

1. 是否從外網可存取（不可為 `localhost` 或內網 IP）
2. 是否為受信任憑證的 HTTPS、支援 TLS 1.2 以上
3. `confirmUrlType=SERVER` 時，防火牆是否允許 LINE Pay 來源 IP（見[confirmUrlType=SERVER](#confirmurltypeserver)）
4. 是否設成 `confirmUrlType=NONE`（此模式 LINE Pay 不會呼叫任何網址）

### 退款失敗

依 `returnCode` 判斷：`1163` 已過退款期限、`1164` 超過可退金額、`1165` 已退過款、`2042` 退款準備金不足（EPI 交易）。

---

## 官方來源

2026-11-17 對照：

- Online API v4 總覽（端點、標頭、結果代碼、Transaction ID）：https://developers-pay.line.me/online-api-v4
- 各端點欄位：https://developers-pay.line.me/online-api-v4/request-payment （其餘端點同一路徑下：`check-payment-request-status`、`confirm-payment`、`capture`、`void`、`retrieve-payment-details`、`refund`、`check-preapproved-payment-key-status`、`request-preapproved-payment`、`discard-preapproved-payment-key`）
- 導回頁面（confirmUrl / cancelUrl、SERVER 模式來源 IP）：https://developers-pay.line.me/online-api-v4/merchant/redirection-pages
- 簽章：https://developers-pay.line.me/online/prerequisites
- 版本變更：https://developers-pay.line.me/api-change-log
- 沙箱：https://developers-pay.line.me/sandbox
- FAQ（1106 簽章錯誤、沙箱憑證）：https://developers-pay.line.me/faq
- 中文版：https://developers-pay.line.me/zh/online-api-v4
