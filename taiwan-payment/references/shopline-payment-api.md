# Shopline Payments API Reference

SHOPLINE Payments（SLP）金流 API 完整參考文件，涵蓋導轉式（Redirect）與內嵌式（Embedded SDK）兩種串接模式。

---

## 目錄

1. [基本說明](#基本說明)
2. [環境資訊](#環境資訊)
3. [認證方式](#認證方式)
4. [API 端點總覽](#api-端點總覽)
5. [訂單建立](#訂單建立)
6. [內嵌式付款建立](#內嵌式付款建立)
7. [請款與取消授權](#請款與取消授權)
8. [付款通知](#付款通知)
9. [退款](#退款)
10. [訂單查詢](#訂單查詢)
11. [錯誤代碼](#錯誤代碼)
12. [支付方式對照表](#支付方式對照表)
13. [沙盒測試](#沙盒測試)
14. [常見問題排解](#常見問題排解)

---

## 基本說明

SHOPLINE Payments 是 SHOPLINE 集團旗下的金流服務，主要支援台灣本地常見支付方式（信用卡、Apple Pay、LINE Pay、街口支付、ATM、中租 BNPL）。所有 API 採 RESTful POST + JSON 設計，以 HTTP Header 帶入 `merchantId` / `apiKey` 完成認證。

### 串接模式

| 模式 | 特性 | 適用場景 |
|------|------|----------|
| **Redirect（導轉式）** | 後端呼叫 `sessions/create` 取得 `sessionUrl`，前端導轉至 SLP 託管的結帳頁完成付款 | 快速串接、無 PCI 範圍考量 |
| **Embedded（內嵌式 SDK）** | 前端嵌入 JS SDK 自行繪製結帳元件，後端呼叫 `payment/create` 提交交易 | 自訂 UI、卡片綁定、定期付款 |

### 串接流程（導轉式）

```
1. 特店後端呼叫「建立結帳交易」(sessions/create)
2. 取得 sessionId 與 sessionUrl
3. 前端將顧客導轉至 sessionUrl
4. 顧客在 SLP 結帳頁完成付款
5. 顧客被導回 returnUrl
6. SLP 發送 Webhook 通知特店付款結果
7. （建議）特店主動查詢交易狀態做雙重確認
```

### 金流特色

- 所有金額以 **分（cents）** 為單位：1 TWD = 100，例如 NT$1,000 → `value: 100000`
- 目前僅支援 **TWD** 幣別
- Webhook 採用 **HMAC-SHA256** 簽章驗證
- 所有 API 走 HTTPS，Webhook URL 必須使用 HTTPS
- 平台模式特店可額外傳入 `platformId`

---

## 環境資訊

### 環境網域

| 環境 | Base URL |
|------|----------|
| 沙盒（Sandbox） | `https://api-sandbox.shoplinepayments.com` |
| 正式（Production） | `https://api.shoplinepayments.com` |

### 開通資訊

特店申請完成後會取得三組金鑰：

| 金鑰 | 用途 | 使用位置 |
|------|------|----------|
| `apiKey` | Server-API 認證 | 後端 HTTP Header |
| `clientKey` | 前端 SDK 初始化（內嵌式） | 前端 JS SDK |
| `signKey` | Webhook 通知簽章驗證 | Webhook 接收端 |

> 沙盒與正式環境金鑰不通用；切換正式環境前需聯繫 SHOPLINE Payments 串接窗口取得正式金鑰。

### 取得金鑰

1. 透過 SHOPLINE Payments 業務窗口完成特店申請
2. 收到沙盒環境帳號 + `apiKey` / `clientKey` / `signKey`
3. 完成沙盒測試後，申請正式環境
4. 設定正式環境 Webhook URL，等待開通

---

## 認證方式

SHOPLINE Payments **不使用 OAuth、不使用 JWT**，所有 Server-API 透過 HTTP Header 傳遞金鑰完成驗證。

### 必填 Header

| 參數 | 類型 | 說明 |
|------|------|------|
| `Content-Type` | String | 固定 `application/json` |
| `merchantId` | String | 特店 ID（由 SLP 配發） |
| `apiKey` | String | API 金鑰 |
| `requestId` | String(32) | 請求流水號，每次請求需唯一 |

### 選填 Header

| 參數 | 類型 | 說明 |
|------|------|------|
| `platformId` | String | 平台特店 ID（平台模式必填） |
| `idempotentKey` | String(32) | 冪等鍵，建議用於 `sessions/create`、`refund/create`，避免網路重試造成重複建立 |

### Header 範例

```
POST /api/v1/trade/sessions/create HTTP/1.1
Host: api-sandbox.shoplinepayments.com
Content-Type: application/json
merchantId: 12345678
apiKey: sk_test_abc123def456
requestId: req_20260507120000_abc
idempotentKey: idem_ORDER-2026050701
```

### 簽章方式

- **Server-API 入向請求**：僅靠 Header 內的 `apiKey` 驗證，**請求 Body 不需簽章**。
- **Webhook 出向通知**：SLP 以 `signKey` 對 `timestamp.body` 計算 HMAC-SHA256，特店端必須驗證（見「付款通知」章節）。

---

## API 端點總覽

### 結帳交易（Sessions）

| 功能 | 路徑 |
|------|------|
| 建立結帳交易 | `POST /api/v1/trade/sessions/create` |
| 查詢結帳交易 | `POST /api/v1/trade/sessions/query` |

### 付款交易（Payment / Trade）

| 功能 | 路徑 |
|------|------|
| 建立付款交易（內嵌式） | `POST /api/v1/trade/payment/create` |
| 查詢付款交易 | `POST /api/v1/trade/payment/get` |
| 請款（Capture） | `POST /api/v1/trade/payment/capture` |
| 取消授權（Cancel） | `POST /api/v1/trade/payment/cancel` |
| 結算（Settle，平台模式） | `POST /api/v1/trade/settle/...` |

### 退款（Refund）

| 功能 | 路徑 |
|------|------|
| 建立退款 | `POST /api/v1/trade/refund/create` |

### 顧客與付款工具（內嵌式）

| 功能 | 路徑 |
|------|------|
| 取得綁卡 Token | `POST /api/v1/customer-paymentInstrument/customer/getToken/` |

### 平台與驗證

| 功能 | 路徑 |
|------|------|
| 平台 KYC | `POST /api/v1/kyc/create/` |
| Apple Pay 網域驗證 | `POST /api/v1/kyc/applePayVerify/` |

### Webhook

由 SLP 主動 POST 至特店事先登錄的 Webhook URL，事件清單見「付款通知」章節。

---

## 訂單建立

### 端點

```
POST /api/v1/trade/sessions/create
```

| 環境 | 完整 URL |
|------|---------|
| 沙盒 | `https://api-sandbox.shoplinepayments.com/api/v1/trade/sessions/create` |
| 正式 | `https://api.shoplinepayments.com/api/v1/trade/sessions/create` |

### 請求參數（Body）

#### 基本欄位

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `referenceId` | String(32) | ● | 特店訂單號，需唯一不可重複 |
| `amount.value` | Number(14) | ● | 金額（**單位為分**，1 TWD = 100） |
| `amount.currency` | String | ● | 幣別，目前僅支援 `TWD` |
| `returnUrl` | String(256) | ● | 付款完成後導回特店的 URL |
| `mode` | String | ● | 固定值 `regular` |
| `allowPaymentMethodList` | Array | ● | 允許的付款方式（見對照表） |
| `expireTime` | Integer | 否 | 結帳逾時（分鐘），預設 `360` |
| `language` | String(6) | 否 | 語系，如 `zh-TW`、`en-US` |
| `passthrough` | String(256) | 否 | 透傳資料，原值回傳 |
| `paymentMethodOptions` | Object | 否 | 付款方式進階選項（見下） |
| `order` | Object | ● | 訂單資訊 |
| `customer` | Object | ● | 顧客資訊 |
| `billing` | Object | ● | 帳單資訊 |
| `client` | Object | ● | 客戶端資訊（至少 `ip`） |

#### `paymentMethodOptions` 進階選項

| 付款方式 | 子參數 | 說明 |
|----------|--------|------|
| `CreditCard` | `installmentCounts` | 分期期數陣列，如 `["0","3","6","12"]`；`"0"` 代表一次付清 |
| `VirtualAccount` | `paymentExpireTime` | ATM 繳費期限（分鐘） |
| `JKOPay` | `paymentExpireTime` | 街口支付期限（分鐘） |
| `ChaileaseBNPL` | `installmentCounts`、`paymentExpireTime` | 中租 zingla 分期 |

> `ApplePay` 與 `LinePay` **不支援** `paymentMethodOptions`，傳入會被忽略。

#### `order` 訂單資訊

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `order.products[]` | Array | ● | 商品列表 |
| `products[].id` | String | ● | 商品 ID |
| `products[].name` | String | ● | 商品名稱 |
| `products[].quantity` | Integer | ● | 數量 |
| `products[].amount.value` | Number | ● | 單品金額（分） |
| `products[].amount.currency` | String | ● | 幣別 |
| `products[].sku` | String | 否 | 商品 SKU |
| `products[].desc` | String | 否 | 商品描述 |
| `products[].url` | String | 否 | 商品頁連結 |
| `order.shipping` | Object | 否 | 寄送資訊（含收件人 `personalInfo`、`address`） |

#### `customer` 顧客資訊

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `referenceCustomerId` | String | 否 | 特店端顧客 ID |
| `type` | String | 否 | 顧客類型（`0` 個人 等） |
| `personalInfo.firstName` | String | ● | 名 |
| `personalInfo.lastName` | String | ● | 姓 |
| `personalInfo.email` | String | ● | E-mail |
| `personalInfo.phone` | String | ● | 電話（國際格式，如 `+886912345678`） |

> 中文姓名拆分慣例：第一個字為 `lastName`（姓），其餘為 `firstName`（名）。

#### `billing` / `address`

| 參數 | 類型 | 說明 |
|------|------|------|
| `billing.personalInfo` | Object | 同 `customer.personalInfo` |
| `billing.address.countryCode` | String | ISO 國碼，如 `TW` |
| `billing.address.city` | String | 城市 |
| `billing.address.district` | String | 行政區 |
| `billing.address.street` | String | 街道地址 |
| `billing.address.postcode` | String | 郵遞區號 |

#### `client` 客戶端資訊

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `client.ip` | String | ● | 顧客 IP |
| `client.userAgent` | String | 否 | 瀏覽器 UA |
| `client.language` | String | 否 | 瀏覽器語系 |

### 完整請求範例

```json
{
  "referenceId": "ORDER-2026050701",
  "language": "zh-TW",
  "amount": {
    "value": 100000,
    "currency": "TWD"
  },
  "expireTime": 60,
  "returnUrl": "https://shop.example.com/payment/return",
  "mode": "regular",
  "allowPaymentMethodList": ["CreditCard", "LinePay", "VirtualAccount", "JKOPay"],
  "paymentMethodOptions": {
    "CreditCard": {
      "installmentCounts": ["0", "3", "6", "12"]
    },
    "VirtualAccount": {
      "paymentExpireTime": 1440
    }
  },
  "order": {
    "products": [{
      "id": "PROD-001",
      "name": "示範商品",
      "quantity": 1,
      "amount": { "value": 100000, "currency": "TWD" }
    }],
    "shipping": {
      "shippingMethod": "宅配",
      "carrier": "黑貓宅配",
      "personalInfo": {
        "firstName": "明",
        "lastName": "王",
        "email": "buyer@example.com",
        "phone": "+886912345678"
      },
      "address": {
        "countryCode": "TW",
        "city": "台北市",
        "district": "松山區",
        "street": "敦化北路 170 號 10 樓",
        "postcode": "105"
      }
    }
  },
  "customer": {
    "referenceCustomerId": "CUST-001",
    "type": "0",
    "personalInfo": {
      "firstName": "明",
      "lastName": "王",
      "email": "buyer@example.com",
      "phone": "+886912345678"
    }
  },
  "billing": {
    "personalInfo": {
      "firstName": "明",
      "lastName": "王",
      "email": "buyer@example.com",
      "phone": "+886912345678"
    },
    "address": {
      "countryCode": "TW",
      "city": "台北市",
      "district": "松山區",
      "street": "敦化北路 170 號 10 樓",
      "postcode": "105"
    }
  },
  "client": {
    "ip": "203.0.113.1",
    "userAgent": "Mozilla/5.0",
    "language": "zh-TW"
  }
}
```

### 成功回應（HTTP 200）

```json
{
  "sessionId": "se_01022502286885089464780754095",
  "referenceId": "ORDER-2026050701",
  "status": "CREATED",
  "amount": { "value": 100000, "currency": "TWD" },
  "sessionUrl": "https://api-sandbox.shoplinepayments.com/checkout/session?sessionToken=xxxx",
  "createTime": "1740711420842",
  "paymentDetails": []
}
```

### 回應欄位

| 參數 | 說明 |
|------|------|
| `sessionId` | SLP 結帳交易編號（`se_` 開頭） |
| `referenceId` | 特店訂單號（原值回傳） |
| `status` | 結帳交易狀態（見下表） |
| `sessionUrl` | 結帳頁 URL，將顧客導轉至此 |
| `createTime` | 建立時間（毫秒時間戳） |
| `paymentDetails[]` | 該 Session 下的付款明細，剛建立時為空陣列 |

### Session 狀態

| 狀態 | 說明 |
|------|------|
| `CREATED` | 已建立，等待付款 |
| `PENDING` | 處理中 |
| `SUCCEEDED` | 付款成功 |
| `EXPIRED` | 已過期 |

### 錯誤回應

```json
{ "code": "1004", "msg": "Param error" }
```

---

## 內嵌式付款建立

### 端點

```
POST /api/v1/trade/payment/create
```

### 主要欄位

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `acquirerType` | String | ● | 固定 `SDK` |
| `referenceOrderId` | String(32) | ● | 特店訂單號 |
| `language` | String(6) | 否 | 語系 |
| `amount.value` | Number(14) | ● | 金額（分） |
| `amount.currency` | String | ● | 幣別 `TWD` |
| `expireTime` | Integer | 否 | 逾時（分鐘） |
| `returnUrl` | String(256) | ● | 完成後導回 URL |
| `paySession` | String | ● | 由前端 SDK 回傳的 paySession 字串 |
| `passthrough` | String(256) | 否 | 透傳資料 |
| `purchaseScene` | String(16) | 否 | 購買場景 |
| `confirm` | Object | ● | 付款確認設定 |
| `order` | Object | ● | 訂單資訊 |
| `customer` | Object | ● | 顧客資訊 |
| `billing` | Object | ● | 帳單資訊 |
| `client` | Object | ● | 客戶端資訊（含螢幕、時區、UA、JS、語系等風控欄位） |

### `confirm` 設定

| 參數 | 說明 |
|------|------|
| `paymentMethod` | 主付款方式（如 `CreditCard`） |
| `subPaymentMethod` | 子付款方式 |
| `autoConfirm` | 是否自動確認 |
| `autoCapture` | 是否自動請款（一段式 vs 兩段式） |
| `autoSettle` | 是否自動結算（平台模式） |
| `paymentBehavior` | 付款行為，如 `Regular`、`Recurring` |
| `paymentCustomerId` | 顧客付款 ID（綁卡用） |
| `paymentInstrument` | 已綁付款工具資訊 |

### 成功回應

```json
{
  "tradeOrderId": "10010061012921418117718876160",
  "channelDealId": "CHANNEL_123",
  "status": "SUCCEEDED",
  "subStatus": "AUTHORIZED",
  "amount": { "value": 100000, "currency": "TWD" },
  "paidAmount": { "value": 100000, "currency": "TWD" },
  "nextAction": {
    "type": "Redirect",
    "url": "https://payment.example.com/3ds",
    "method": "GET",
    "data": ""
  },
  "lastPayment": {
    "brand": "Visa",
    "last4": "1234",
    "paymentMethod": "CreditCard",
    "paymentInstrument": {
      "paymentInstrumentId": "6456462132132",
      "savePaymentInstrument": true
    }
  },
  "customer": {
    "referenceCustomerId": "CUST-001",
    "CustomerId": "12412dr133"
  }
}
```

### `nextAction` 後續動作

當交易需要 3D 驗證、跳轉錢包 App 或顯示繳款資訊時，回應會帶 `nextAction`：

| 欄位 | 說明 |
|------|------|
| `type` | 動作類型，如 `Redirect`、`Display` |
| `url` | 導轉 URL |
| `method` | HTTP 方法 |
| `data` | 附加資料 |

前端 SDK 透過 `payment.pay(nextAction)` 呼叫即可。

### 交易狀態

| 狀態 | 說明 |
|------|------|
| `CREATED` | 已建立 |
| `PROCESSING` | 處理中 |
| `SUCCEEDED` | 成功 |
| `FAILED` | 失敗 |
| `CANCELLED` | 已取消 |
| `EXPIRED` | 已過期 |

### subStatus 子狀態

| 子狀態 | 說明 |
|--------|------|
| `AUTHORIZED` | 已授權，未請款（兩段式） |
| `CAPTURED` | 已請款 |
| `REFUNDED` | 已退款 |
| `PARTIAL_REFUNDED` | 部分退款 |

---

## 請款與取消授權

兩段式信用卡交易先授權、再請款；請款前可取消授權釋放額度。

### 請款（Capture）

#### 端點

```
POST /api/v1/trade/payment/capture
```

#### 請求參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `referenceOrderId` | String(32) | △ | 特店訂單號（與 `tradeOrderId` 二擇一） |
| `tradeOrderId` | String(32) | △ | SLP 交易訂單編號（二擇一） |
| `amount.value` | Number | ● | 請款金額（分） |
| `amount.currency` | String | ● | 幣別 `TWD` |
| `additionalData` | Map | 否 | 附加資料 |

#### 請求範例

```json
{
  "referenceOrderId": "ORDER-2026050701",
  "tradeOrderId": "10010061012921418117718876160",
  "amount": { "value": 100000, "currency": "TWD" }
}
```

#### 成功回應

```json
{
  "tradeOrderId": "10010061012921418117718876160",
  "status": "PROCESSING",
  "amount": { "value": 100000, "currency": "TWD" }
}
```

> 請款 API 同步回應通常為 `PROCESSING`，最終結果需以 Webhook 或主動查詢為準。

#### 請款狀態

| 狀態 | 說明 |
|------|------|
| `PROCESSING` | 處理中 |
| `SUCCEEDED` | 請款成功 |
| `FAILED` | 請款失敗 |

### 取消授權（Cancel）

#### 端點

```
POST /api/v1/trade/payment/cancel
```

#### 請求參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `referenceOrderId` | String(32) | ● | 特店訂單號 |
| `tradeOrderId` | String(48) | ● | SLP 交易訂單編號 |
| `additionalData` | Map | 否 | 附加資料 |

#### 成功回應

```json
{
  "tradeOrderId": "10010061012921418117718876160",
  "status": "PROCESSING"
}
```

> 已請款的交易**無法取消**，僅能透過退款 API 處理。

### 交易狀態流程

```
┌─────────────┐
│   CREATED   │
└──────┬──────┘
       ▼
┌─────────────┐
│ PROCESSING  │
└──────┬──────┘
       ▼
┌─────────────┐
│ AUTHORIZED  │ ── Capture ──▶ ┌──────────┐
└──────┬──────┘                │ CAPTURED │
       │                       └────┬─────┘
       │                            ▼
       └── Cancel ──▶ CANCELLED   REFUND
```

### 使用場景

- **自動請款（預設）** — `autoCapture=true`，下單即自動請款。
- **手動請款** — 需先確認庫存或人工審核時使用。
- **取消授權** — 在請款前若訂單作廢，可即時釋放顧客額度。

### 注意事項

1. 信用卡授權有效期通常為 7 ~ 30 天，依發卡行而定
2. 請款金額可小於或等於授權金額（部分請款）
3. 請款後若需退款，請改用退款 API
4. `tradeOrderId` 為 SLP 端付款交易識別碼，請妥善保存

---

## 付款通知

### Webhook 通知流程

```
┌──────────┐  Payment   ┌──────────┐  POST     ┌──────────┐
│ 顧客付款 │ ─────────▶ │   SLP    │ ────────▶│  特店    │
└──────────┘            │  處理    │  Webhook  │  Webhook │
                        └──────────┘           └────┬─────┘
                                                    │
                                                    │ 驗證簽章
                                                    │ 處理事件
                                                    ▼
                                              回應 HTTP 200
```

### Webhook Header

| 參數 | 必填 | 說明 |
|------|------|------|
| `Content-Type` | ● | `application/json` |
| `apiVersion` | ● | API 版本，如 `V1.2` |
| `timestamp` | ● | 通知產生時間（毫秒時間戳） |
| `sign` | ● | HMAC-SHA256 簽章值（hex） |

### Webhook Body 結構

```json
{
  "id": "000100698482394232932302030234328327",
  "type": "trade.succeeded",
  "created": 1718551769058,
  "data": {
    /* 依事件類型而異 */
  }
}
```

| 參數 | 說明 |
|------|------|
| `id` | 通知唯一 ID（用於冪等去重） |
| `type` | 事件類型 |
| `created` | 通知產生時間（毫秒） |
| `data` | 事件主體資料 |

### 事件類型

#### 結帳交易事件

| 事件 | 說明 |
|------|------|
| `session.created` | 結帳交易已建立 |
| `session.pending` | 結帳交易處理中 |
| `session.succeeded` | 結帳交易成功 |
| `session.expired` | 結帳交易逾時 |

#### 付款交易事件

| 事件 | 說明 |
|------|------|
| `trade.succeeded` | 付款成功 |
| `trade.failed` | 付款失敗 |
| `trade.expired` | 付款逾時 |
| `trade.processing` | 付款處理中 |
| `trade.cancelled` | 付款取消 |
| `trade.customer_action` | 等待顧客行動（3DS、跳轉 App） |

#### 退款事件

| 事件 | 說明 |
|------|------|
| `trade.refund.succeeded` | 退款成功 |
| `trade.refund.failed` | 退款失敗 |

#### 會員與付款工具事件（內嵌式）

| 事件 | 說明 |
|------|------|
| `customer.created` | 會員建立 |
| `customer.updated` | 會員資訊更新 |
| `customer.deleted` | 會員註銷 |
| `customer.instrument.binded` | 綁定付款工具 |
| `customer.instrument.updated` | 更新付款工具 |
| `customer.instrument.unbinded` | 解除綁定 |

#### 爭議與平台事件

| 事件 | 說明 |
|------|------|
| `dispute.chargeback.*` | 拒付通知 |
| `dispute.pre-chargeback.*` | 預拒付 |
| `dispute.fraud.*` | 詐欺爭議 |
| `dispute.retrieval.*` | 證據調閱 |
| `trade.settled` | 交易結算（平台模式） |
| `merchant.kyc.audit` | KYC 審核結果 |

> SLP 保留隨時新增事件類型的權利，特店實作應對未知事件「忽略並回應 200」。

### 簽章驗證

SLP 使用 **HMAC-SHA256** 對 `timestamp.body` 計算簽章。

#### 計算公式

```
payload  = timestamp + "." + rawJsonBody     // 必須使用原始 body 字串，不可重新序列化
expected = HMAC_SHA256(payload, signKey)     // 結果為 hex 字串
比對：    expected == header["sign"]
```

#### Node.js 範例

```javascript
const crypto = require('crypto');
const express = require('express');

const app = express();

function verifyShoplineSignature(timestamp, rawBody, sign, signKey) {
  const payload = `${timestamp}.${rawBody}`;
  const expected = crypto
    .createHmac('sha256', signKey)
    .update(payload, 'utf8')
    .digest('hex');
  return crypto.timingSafeEqual(
    Buffer.from(expected, 'hex'),
    Buffer.from(sign, 'hex')
  );
}

// 必須使用 raw body
app.post(
  '/webhook/shopline',
  express.raw({ type: 'application/json' }),
  (req, res) => {
    const timestamp = req.headers['timestamp'];
    const sign      = req.headers['sign'];
    const rawBody   = req.body.toString('utf8');

    // 1. 驗證簽章
    if (!verifyShoplineSignature(timestamp, rawBody, sign, process.env.SHOPLINE_SIGN_KEY)) {
      return res.status(401).send('Invalid signature');
    }

    // 2. 驗證時間戳，防重放（容許 5 分鐘）
    const now = Date.now();
    if (Math.abs(now - parseInt(timestamp, 10)) > 5 * 60 * 1000) {
      return res.status(401).send('Timestamp expired');
    }

    // 3. 解析事件
    const event = JSON.parse(rawBody);
    switch (event.type) {
      case 'trade.succeeded':
        handlePaymentSuccess(event.data);
        break;
      case 'trade.failed':
        handlePaymentFailed(event.data);
        break;
      case 'trade.refund.succeeded':
        handleRefundSuccess(event.data);
        break;
      default:
        console.log('Unhandled event:', event.type);
    }

    // 4. 回應 200
    res.status(200).send('OK');
  }
);
```

#### PHP 範例

```php
<?php
function verifyShoplineSignature($timestamp, $body, $sign, $signKey) {
    $payload  = $timestamp . '.' . $body;
    $expected = hash_hmac('sha256', $payload, $signKey);
    return hash_equals($expected, $sign);
}

$timestamp = $_SERVER['HTTP_TIMESTAMP'] ?? '';
$sign      = $_SERVER['HTTP_SIGN']      ?? '';
$body      = file_get_contents('php://input');

if (!verifyShoplineSignature($timestamp, $body, $sign, getenv('SHOPLINE_SIGN_KEY'))) {
    http_response_code(401); exit('Invalid signature');
}
http_response_code(200); echo 'OK';
```

#### Python 範例

```python
import hmac, hashlib

def verify_shopline_signature(timestamp, raw_body, sign, sign_key):
    payload  = f"{timestamp}.{raw_body}"
    expected = hmac.new(sign_key.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sign)
```

### 付款成功事件範例

```json
{
  "id": "000100698482394232932302030234328327",
  "type": "trade.succeeded",
  "created": 1718551769058,
  "data": {
    "actionType": "SDK",
    "referenceOrderId": "ORDER-2026050701",
    "tradeOrderId": "1001001084733463323223973",
    "paymentMsg": null,
    "payment": {
      "paymentSuccessTime": "1718551768922",
      "autoCapture": true,
      "paymentBehavior": "Regular",
      "channelDealId": "17185517455610128070000",
      "paymentMethod": "CreditCard",
      "creditCard": {
        "issuerCountry": "TW",
        "last4": "1234",
        "bin": "12345678",
        "type": "CREDIT",
        "category": "BUSINESS SIGNATURE",
        "brand": "Visa",
        "issuer": "HSBC"
      },
      "paidAmount": { "currency": "TWD", "value": 10000 }
    },
    "status": "SUCCEEDED",
    "subStatus": "",
    "order": {
      "amount": { "currency": "TWD", "value": 10000 },
      "referenceOrderId": "ORDER-2026050701",
      "merchantId": "12345678",
      "createTime": 1718551768994,
      "customer": {
        "customerId": "",
        "referenceCustomerId": "CUST-001"
      }
    }
  }
}
```

### Webhook 接收要點

1. **回應 HTTP 200** — 否則 SLP 會持續重試
2. **冪等去重** — 以事件 `id` 作為唯一鍵，避免重複入帳
3. **非同步處理** — 建議先回 200，再以 Queue 處理業務邏輯
4. **必須驗證簽章** — 不可省略
5. **驗證 timestamp** — 防止重放攻擊
6. **HTTPS 必填** — Webhook URL 必須為 HTTPS
7. **未知事件忽略** — 對 `default` 分支回傳 200

### Webhook 申請開通

寫信給 SHOPLINE Payments 串接窗口，提供：

- 訂閱事件清單
- 對應環境（沙盒 / 正式）的特店帳號
- Webhook URL（必須 HTTPS）

---

## 退款

### 端點

```
POST /api/v1/trade/refund/create
```

| 環境 | 完整 URL |
|------|---------|
| 沙盒 | `https://api-sandbox.shoplinepayments.com/api/v1/trade/refund/create` |
| 正式 | `https://api.shoplinepayments.com/api/v1/trade/refund/create` |

### 請求參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `referenceOrderId` | String(32) | ● | 特店退款單號（特店端唯一） |
| `tradeOrderId` | String(32) | ● | 原 SLP 付款交易編號 |
| `amount.value` | Number(14) | ● | 退款金額（分） |
| `amount.currency` | String | ● | 幣別 `TWD` |
| `reason` | String(256) | 否 | 退款原因 |
| `callbackUrl` | String(256) | 否 | 退款結果回呼 URL（如未設定，仍會走 Webhook） |
| `additionalData` | Map | 否 | 附加資料 |

### 請求範例

```json
{
  "referenceOrderId": "REFUND-2026050701",
  "tradeOrderId": "10010061012921418117718876160",
  "amount": { "value": 50000, "currency": "TWD" },
  "reason": "顧客申請部分退款"
}
```

### 成功回應

```json
{
  "referenceRefundOrderId": "ref_refund_REFUND-2026050701",
  "tradeOrderId": "10010061012921418117718876160",
  "refundOrderId": "45668468546465",
  "amount": { "value": 50000, "currency": "TWD" },
  "status": "SUCCEEDED"
}
```

### 退款規則

- **退款時效**：原交易完成後 **180 天**內可退款
- **部分退款**：支援，金額 ≤ 可退餘額
- **多筆退款**：支援，總金額 ≤ 原交易金額
- **同一筆只能有一個處理中的退款**：上一筆退款處理中時無法發起新退款
- **線下通路退款**：部分通路（4502/1202）不支援線上退款，需聯繫 SLP

### 退款狀態

| 狀態 | 說明 |
|------|------|
| `PROCESSING` | 處理中 |
| `SUCCEEDED` | 退款成功 |
| `FAILED` | 退款失敗 |

### 常見退款錯誤碼

| 錯誤碼 | 說明 |
|--------|------|
| `1010` | 退款權限已停用 |
| `1013` | 退款請求已存在 |
| `1014` | 無可退款金額 |
| `1020` | 超過退款時效（180 天） |
| `1021` | 交易不存在或狀態異常 |
| `1022` | 商戶餘額不足 |
| `1202` | 通路不支援線上退款 |
| `4701` | 退款金額超過可退金額 |
| `4703` | 已超過可退款時效 |
| `4706` | 上次退款仍在處理中 |
| `4707` | 該交易不支援部分退款 |

---

## 訂單查詢

### 查詢結帳交易（Session）

#### 端點

```
POST /api/v1/trade/sessions/query
```

#### 請求

```json
{ "sessionId": "se_01022502286885089464780754095" }
```

#### 回應

```json
{
  "sessionId": "se_01022502286885089464780754095",
  "referenceId": "ORDER-2026050701",
  "status": "SUCCEEDED",
  "amount": { "value": 100000, "currency": "TWD" },
  "sessionUrl": "https://api-sandbox.shoplinepayments.com/checkout/session?sessionToken=xxxx",
  "createTime": "1740711420842",
  "paymentDetails": [
    {
      "tradeOrderId": "10010102714941391738628956160",
      "status": "SUCCEEDED",
      "paymentSuccessTime": 1740711500000,
      "paymentMethod": "CreditCard",
      "autoSettle": false
    }
  ]
}
```

### 查詢付款交易（Trade）

#### 端點

```
POST /api/v1/trade/payment/get
```

#### 請求

```json
{ "tradeOrderId": "10010061012921418117718876160" }
```

#### 回應

```json
{
  "tradeOrderId": "10010061012921418117718876160",
  "referenceOrderId": "ORDER-2026050701",
  "channelDealId": "CHANNEL_123",
  "status": "SUCCEEDED",
  "subStatus": "CAPTURED",
  "amount": { "value": 100000, "currency": "TWD" },
  "paidAmount": { "value": 100000, "currency": "TWD" },
  "lastPayment": {
    "brand": "Visa",
    "last4": "1234",
    "paymentMethod": "CreditCard",
    "paymentInstrument": {
      "paymentInstrumentId": "6456462132132",
      "savePaymentInstrument": true
    }
  },
  "nextAction": null
}
```

### 使用時機

1. **顧客自 returnUrl 返回時** — 主動查詢確認付款狀態
2. **Webhook 補充驗證** — 收到通知後雙重確認
3. **訂單對帳** — 定期同步付款狀態
4. **客服查詢** — 客服查詢交易詳情
5. **失敗重試後** — 確認最終結果

---

## 錯誤代碼

SHOPLINE Payments 錯誤碼以「字串」形式回傳，HTTP 狀態通常為 `400` / `429` / `500`：

```json
{ "code": "1004", "msg": "Param error" }
```

### 通用錯誤碼

| 錯誤碼 | 說明 | 處理方式 |
|--------|------|----------|
| `1005` | 校驗錯誤 | 檢查欄位格式與必填 |
| `1006` | 紀錄已存在 | 改用查詢 API |
| `1008` | 狀態錯誤 | 確認交易狀態流程 |
| `1016` | 無交易紀錄 | 確認 `tradeOrderId` |
| `1018` | 業務錯誤（付款失敗/取消/逾期） | 查 `paymentMsg` 細節 |
| `1901` ~ `1904` | 系統連線/格式/限流錯誤 | 退避重試 |
| `1997` ~ `1999` | 資料庫/配置/系統異常 | 聯繫 SLP 或重試 |
| `2001` | APPID 不存在 | 確認 `merchantId` |
| `2002` | 簽名錯誤 | 檢查 Webhook 簽章 |
| `2003` | 請求 URL 錯誤 | 檢查端點 |
| `2004` ~ `2008` | 系統錯誤、訪問拒絕、錯誤請求、無法訪問 | 檢查 `apiKey` 與環境 |
| `2009` ~ `2010` | Token 逾期/被篡改 | 重新取得 Token |
| `2011` | 付款工具狀態禁止修改 | 檢查綁卡狀態 |
| `2013` | 商戶未與平台 Connect | 完成平台串接 |

### 連線/認證錯誤碼

| 錯誤碼 | 說明 |
|--------|------|
| `URL_NOT_FOUND` | URL 不存在 |
| `ACCESS_DENIED` | apiKey/clientKey 不正確、與商家或平台 ID 不符 |
| `MERCHANT_NOT_EXISTS` | 特店 ID 不存在 |
| `UNAUTHORIZED_CLIENT` | 客戶端 ID 錯誤 |
| `SERVER_ERROR` | 系統異常 |
| `KEY_INCORRECT` | apiKey 格式錯誤 |
| `INVALID_SCOPE` | 授權範圍錯誤 |

### 下單錯誤碼

| 錯誤碼 | 說明 |
|--------|------|
| `1001` | 重複下單，交易已存在 |
| `1003` | 參數缺失 |
| `1004` | 參數錯誤（最常見：金額未 × 100） |
| `1025` | 超過最大或不足最低付款限額 |
| `4001` | 通路連線失敗 |
| `4002` | 通路錯誤 |
| `4003` | 通路回應逾時 |
| `4101` | 付款金額不在限額之間 |
| `4102` | 交易異常，下單失敗 |
| `4103` | 未知原因下單失敗 |
| `4104` | 特店帳戶狀態異常 |
| `4105` | 顧客帳戶狀態異常 |
| `4106` | IP 未加入白名單 |
| `4107` | 交易幣種通路不支援 |
| `4108` | 喚起付款表單失敗 |
| `4109` | 網站網域未設定 |

### 風控錯誤碼

| 錯誤碼 | 說明 |
|--------|------|
| `3000` | 命中 SLP 風控（使用者行為異常） |
| `3001` | 命中 SLP 風控（交易卡異常） |
| `3002` | 命中 SLP 風控（收貨人異常） |
| `3003` | 命中 SLP 風控（高風險交易） |
| `3004` | 命中 SLP 風控（交易資訊異常） |
| `4350` | 命中通路/銀行風控 |

### 銀行/通路錯誤碼

| 錯誤碼 | 說明 |
|--------|------|
| `4400` | 通路系統異常 |
| `4401` | 通路交易逾期 |
| `4402` | ATM 繳款金額與訂單金額不一致 |
| `4403` | 系統繁忙 |
| `4404` ~ `4409` | Token 相關錯誤（金額不符、非法、公私鑰錯誤、簽名錯誤、逾期） |
| `4410` | 重複付款 |
| `4411` | 鑑權失敗 |
| `4412` | 通路介面回應 not found |

### 信用卡錯誤碼

| 錯誤碼 | 說明 |
|--------|------|
| `4450` | 3DS 驗證流程逾時 |
| `4451` | 發卡行交易失敗 |
| `4452` | 3DS 驗證不通過 |
| `4453` | CVV 驗證不通過 |
| `4454` | 餘額不足 |
| `4455` | 卡號無效 |
| `4456` | 通路系統異常 |
| `4457` | 發卡行識別高風險交易 |
| `4458` | 交易仍在處理中 |
| `4459` | 信用卡已過期 |
| `4460` ~ `4462` | PIN 輸入超限 / 金額超限 / PIN 驗證不通過 |
| `4463` ~ `4464` | 被竊或遺失卡 / 卡被凍結 |
| `4465` ~ `4467` | 需輸入 PIN / 金融卡受限 / 已超交易次數 |
| `4468` | 付款碼或收款碼已逾期或無效 |

### 顧客行為錯誤碼

| 錯誤碼 | 說明 |
|--------|------|
| `4550` | 顧客自主取消交易 |
| `4551` | 顧客發起拒付 |
| `4552` | 顧客付款帳號異常 |
| `4600` | 未知原因 |

### 退款錯誤碼

| 錯誤碼 | 說明 |
|--------|------|
| `1010` | 退款權限已停用 |
| `1013` | 退款請求已存在 |
| `1014` | 無可退款金額 |
| `1015` | 特店帳戶未完成高級認證 |
| `1020` | 超過退款時效（180 天） |
| `1021` | 交易不存在或狀態異常 |
| `1022` | 商戶餘額不足 |
| `1023` | 未知原因退款失敗 |
| `1202` | 通路不支援線上退款 |
| `4502` | 交易不存在或狀態異常 |
| `4700` | 交易不存在 |
| `4701` | 退款金額超過可退金額 |
| `4702` | 商戶餘額不足 |
| `4703` | 已超過退款時效 |
| `4704` | 未知原因退款失敗 |
| `4705` | 傳輸金額不正確 |
| `4706` | 上次退款尚在處理中 |
| `4707` | 該交易不支援部分退款 |

### 取消授權錯誤碼

| 錯誤碼 | 說明 |
|--------|------|
| `6001` | 交易處理中，無法取消 |
| `6002` | 交易已請款，無法取消（請改用退款） |
| `6003` | 交易已取消，無法再取消 |
| `6400` | 交易狀態異常，無法取消 |
| `6401` | 通路系統原因導致無法取消 |

### 請款錯誤碼

| 錯誤碼 | 說明 |
|--------|------|
| `7001` | 請款金額超過可請款金額 |
| `7002` | 交易狀態異常，無法請款 |
| `7400` | 交易狀態異常 |
| `7401` | 通路系統原因導致無法請款 |
| `7402` | 請款金額超過可請款金額 |
| `7403` | 因授權額度問題請款失敗 |

### 綁卡錯誤碼

| 錯誤碼 | 說明 |
|--------|------|
| `1200` | 暫不支援綁卡 |
| `1201` | 系統正在處理綁卡 |
| `1203` | 卡片驗證失敗 |
| `4800` | 未知原因綁卡失敗 |
| `4801` | 使用者拒絕授權 |
| `4802` | 通路參數錯誤 |

### 定期付款錯誤碼

| 錯誤碼 | 說明 |
|--------|------|
| `4900` | 需 3DS，但顧客不在場 |
| `4901` | 需 CVS 認證，但顧客不在場 |
| `4902` | 其他原因無法完成定期付款 |

### SDK 錯誤碼（內嵌式）

#### Server 端

| 錯誤碼 | 說明 |
|--------|------|
| `1009` | 特店 SLP 收款權限已停用 |
| `4200` | 特店暫未綁定該付款通路 |
| `4201` | 特店無使用權限 |
| `4202` | 通路或付款方式不支援該幣種 |
| `4203` | 特店收款帳戶狀態異常 |
| `4204` | 暫不支援該付款方式 |

#### Client 端（SDK）

| 錯誤碼 | 說明 |
|--------|------|
| `1026` ~ `1029` | 瀏覽器不支援、SDK 內部錯誤、初始化失敗 |
| `1100` ~ `1112` | 設備不支援、載入 JS 失敗、HTTPS 必填、網路錯誤、輸入錯誤 |
| `4110`、`4111` | 建立通道實例失敗、nextAction 入參錯誤 |
| `4205` ~ `4208` | 交易異常、API 不支援該付款方式、dom 不存在、SDK 入參錯誤 |

#### 信用卡 SDK 驗證

| 錯誤碼 | 說明 |
|--------|------|
| `43000` ~ `43005` | 卡組／發卡銀行／卡類型／國家／等級／BIN 不支援 |
| `43006` ~ `43009` | 分期期數、特店、金額、付款方式維護中 |
| `43010`、`43011` | 身分資訊驗證異常、超出驗證次數 |

---

## 支付方式對照表

`allowPaymentMethodList` 接受以下值：

| 代碼 | 名稱 | 描述 | 支援 `paymentMethodOptions` |
|------|------|------|---------------------------|
| `CreditCard` | 信用卡 | 一次付清 + 分期 | ✓（`installmentCounts`） |
| `ApplePay` | Apple Pay | Apple 錢包 Touch/Face ID | ✗ |
| `LinePay` | LINE Pay | LINE 錢包 | ✗ |
| `JKOPay` | 街口支付 | 街口 App 掃碼 | ✓（`paymentExpireTime`） |
| `VirtualAccount` | ATM 虛擬帳號 | ATM 銀行轉帳 | ✓（`paymentExpireTime`） |
| `ChaileaseBNPL` | 中租 zingla 銀角零卡 | BNPL 無卡分期 | ✓（`installmentCounts` + `paymentExpireTime`） |

### 支援幣別

目前僅支援 **TWD**。

### 信用卡分期期數

`installmentCounts` 接受字串陣列，例如 `["0", "3", "6", "12"]`：

| 值 | 說明 |
|----|------|
| `"0"` | 一次付清 |
| `"3"` | 3 期分期 |
| `"6"` | 6 期分期 |
| `"12"` | 12 期分期 |
| `"18"` | 18 期分期（依發卡行） |
| `"24"` | 24 期分期（依發卡行） |

> 實際支援期數依發卡行與 SLP 通路設定而定。

### 付款方式狀態流程

```
建立 session
    │
    ▼
顧客選付款方式
    │
    ├── CreditCard ─▶ 3DS（如需）─▶ 授權 ─▶ (autoCapture) ─▶ 請款完成
    ├── ApplePay   ─▶ Touch/Face ID ─▶ 完成
    ├── LinePay    ─▶ 跳轉 LINE App ─▶ 完成
    ├── JKOPay     ─▶ 跳轉街口 App  ─▶ 完成
    ├── VirtualAccount ─▶ 顯示虛擬帳號 ─▶ 顧客 ATM 繳款 ─▶ 完成
    └── ChaileaseBNPL ─▶ 中租審核 ─▶ 完成
```

---

## 沙盒測試

### 沙盒環境

```
Base URL: https://api-sandbox.shoplinepayments.com
```

### 取得測試金鑰

聯繫 SHOPLINE Payments 串接窗口取得沙盒環境的：

- `apiKey`
- `clientKey`（內嵌式使用）
- `signKey`

### 信用卡測試卡號

| 卡組織 | 卡號 | 有效期限 | CVC |
|--------|------|----------|-----|
| Visa | `4147633700198405` | `03/30` | `638` |
| MasterCard | `5149147700000300` | `03/30` | `231` |
| JCB | `3565586700000200` | `03/30` | `484` |

### 沙盒交易結果規則

沙盒環境**根據交易金額決定結果**：

#### 3D 驗證觸發

金額為 **3 的倍數** 會進入 3D 驗證流程：

| 金額（TWD） | `amount.value` | 是否 3D | 結果 |
|------------|---------------|--------|------|
| 300 | 30000 | ✓ | 模擬頁可選成功/失敗 |
| 600 | 60000 | ✓ | 模擬頁可選成功/失敗 |
| 301 | 30100 | ✗ | 非 3D |

#### 非 3D 交易

金額**非 3 的倍數**時，去掉最小單位（取整百數）後：

| 金額（TWD） | 去掉 00 | 奇偶 | 結果 |
|------------|---------|------|------|
| 101 | 1 | 奇數 | ✓ 成功 |
| 501 | 5 | 奇數 | ✓ 成功 |
| 200 | 2 | 偶數 | ✗ 失敗 |
| 400 | 4 | 偶數 | ✗ 失敗 |

**簡易記法**：
- 奇數結尾金額（101、301、501）→ 成功
- 偶數結尾金額（200、400、600）→ 失敗

### Apple Pay 沙盒

#### 沙盒帳號

```
帳號：slpsandbox2@shopline.com
密碼：Aa123456!
```

> 請勿修改密碼，由所有 SLP 沙盒測試共用。

#### 設定步驟

1. 準備 macOS 10.14.1+ 或 iOS 12.1+ 裝置
2. 登入沙盒 Apple ID
3. 在 Wallet 加入 [Apple 沙盒測試卡](https://developer.apple.com/apple-pay/sandbox-testing/)
4. 交易金額遵循同樣的「奇數成功 / 偶數失敗」規則

### LINE Pay / 街口 / ATM 沙盒

跳轉至 SHOPLINE 模擬頁面，可在頁面選擇模擬結果（成功 / 失敗 / 取消）。

### 測試清單

- 建立結帳 session，取得 sessionUrl
- 使用奇數金額完成付款；偶數金額測試失敗
- 使用 3 的倍數金額測試 3D 驗證
- 測試各付款方式（CreditCard / LinePay / JKOPay / VirtualAccount）
- 測試分期（`installmentCounts: ["3", "6"]`）
- 全額 + 部分退款
- 請款前取消授權；請款後嘗試取消（應失敗 6002）
- Webhook 簽章驗證 + 重複事件冪等處理

---

## 常見問題排解

### 1. `1004 Param error`

**最常見原因**：金額未乘 100。

```javascript
// ✗ 錯誤
amount: { value: 1000, currency: 'TWD' }   // 變成 NT$10

// ✓ 正確
amount: { value: 1000 * 100, currency: 'TWD' }   // NT$1,000
```

### 2. `1001 Order exist`

**原因**：`referenceId` 重複。

```javascript
// ✓ 使用時間戳 + 隨機數
const orderId = `ORDER-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
```

### 3. `ACCESS_DENIED`

**原因**：

- `apiKey` 與環境不符（沙盒/正式）
- `apiKey` 與 `merchantId` 不符
- 商戶尚未開通對應功能
- 平台特店缺 `platformId` Header

**檢查項**：

```bash
# 檢查環境
echo $SHOPLINE_BASE_URL
# 沙盒：https://api-sandbox.shoplinepayments.com
# 正式：https://api.shoplinepayments.com

echo $SHOPLINE_API_KEY  # 不能用沙盒 key 打正式環境
```

### 4. Webhook 沒收到通知

**檢查順序**：

1. Webhook URL 是否已向 SLP 申請開通
2. URL 是否為 HTTPS（HTTP 不行）
3. URL 是否能被外網存取（內網/防火牆）
4. 是否正確回應 HTTP 200
5. 是否被 Cloudflare/WAF 擋掉

### 5. Webhook 簽章驗證失敗

**常見原因**：

- 用了錯誤的 `signKey`（沙盒/正式不同）
- **將 body JSON 重新序列化** 後再驗章 — 必須使用「原始 raw body」
- payload 拼接錯誤 — 應為 `timestamp + "." + body`，**不是**用空格或冒號
- `timestamp` 取錯（取了 `created` 而非 Header `timestamp`）

```javascript
// ✗ 錯誤：解析後再序列化
const body = JSON.parse(req.body);
const expected = HMAC(timestamp + '.' + JSON.stringify(body), key);

// ✓ 正確：使用原始 body 字串
const expected = HMAC(timestamp + '.' + rawBodyString, key);
```

### 6. 沙盒一直交易失敗

**檢查金額**：沙盒環境根據金額決定結果。

```
金額結尾為奇數 → 成功（如 101, 301, 501）
金額結尾為偶數 → 失敗（如 200, 400, 600）
3 的倍數      → 進入 3D 驗證
```

### 7. 退款失敗 `1014` / `4701`

**原因**：

- 該筆交易已全額退款
- 多次部分退款累計超過原金額

**正確做法**：先呼叫 `payment/get` 查詢可退餘額。

```javascript
const trade = await queryTrade(tradeOrderId);
const refundable = trade.paidAmount.value - alreadyRefunded;
if (refundAmount > refundable) throw new Error('退款金額超過可退餘額');
```

### 8. 取消授權失敗 `6002`

**原因**：交易已請款，授權無法再取消。

**處理**：改用退款 API。捕捉 `6002` 後 fallback 至 `refund/create`。

### 9. 顧客 returnUrl 返回但訂單未付款

`returnUrl` 不代表付款成功，僅代表顧客「離開了結帳頁」。**以 Webhook 為準**，或在 `returnUrl` 主動呼叫 `sessions/query` 確認。

### 10. 平台特店錯誤 `2013`

平台特店尚未完成 Connect 綁定。聯繫 SLP 完成綁定，並在所有 API Header 加上 `platformId`。

### 11. Idempotent 重複防呆

對 `sessions/create`、`refund/create` 建議帶入 `idempotentKey`，網路重試時 SLP 會回傳第一次的結果而非建立第二筆。

### 12. 金額限額相關（`1025` / `4101`）

不同付款方式有不同金額上下限，依特店風控設定不同：

1. 確認金額為正整數
2. 確認金額已乘 100
3. 聯繫 SLP 確認該付款方式的金額限額

---

## 官方資源

- **API 文件**：https://docs.shoplinepayments.com/
- **建立 Session API**：https://docs.shoplinepayments.com/api/trade/session/
- **退款 API**：https://docs.shoplinepayments.com/api/trade/refund/
- **Webhook 事件**：https://docs.shoplinepayments.com/api/event/
- **支援付款方式**：https://docs.shoplinepayments.com/appendix/paymentMethod/
- **串接申請**：透過 SHOPLINE Payments 業務窗口

---

最後更新：2026/05/07
