# Shopline Payments API Reference

> 目錄精簡版：只含參考文件與 JSON 資料，不含腳本。文中提到 `scripts/`、`examples/`、`tests/` 的工具在完整版（npm 套件 `taiwan-payment-skill`）。
> 金鑰與商店代號由使用者自行設定、自行提供；文中的測試帳號是服務商官方公開的測試值，不是真實憑證。帳密類欄位以 `<帳密欄位>` 表示，實際欄名見官方文件。

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

特店使用三組金鑰：

| 金鑰 | 用途 | 使用位置 |
|------|------|----------|
| `apiKey` | Server-API 認證 | 後端 HTTP Header |
| `clientKey` | 前端 SDK 初始化（內嵌式） | 前端 JS SDK |
| `signKey` | Webhook 通知簽章驗證 | Webhook 接收端 |

> 沙盒與正式環境金鑰不通用。**每一個 Webhook URL 對應一組 `signKey`**。

### 取得金鑰

1. 透過 SHOPLINE Payments 業務窗口完成特店申請；審核通過後登入 SHOPLINE Payments 後台
2. 在後台「設定 → 開發者管理」自行取得 `apiKey` / `clientKey` / `signKey`，並設定 Webhook URL
3. 沙盒：官方提供共用的沙盒後台帳號（見「沙盒測試」），同樣在「設定 → 開發者管理」取得沙盒金鑰
4. 沙盒驗證完付款、退款、Event 通知後，用正式金鑰上線

（docs.shoplinepayments.com 首頁「串接流程」、/overview/sandboxResource/、/api/event/，2026-11-17 查核）

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
| 結算（Settle，平台） | `POST /api/v1/trade/payment/settle` |

### 退款（Refund）

| 功能 | 路徑 |
|------|------|
| 建立退款 | `POST /api/v1/trade/refund/create` |
| 查詢退款 | `POST /api/v1/trade/refund/get`（body：`refundOrderId`） |

### 會員與付款工具（內嵌式）

| 功能 | 路徑 |
|------|------|
| 建立／查詢／更新／註銷會員 | `POST /api/v1/customer/create`、`/get`、`/update`、`/delete` |
| 會員授權（取得 `customerToken`） | `POST /api/v1/customer/token`（body：`customerId`；回應 `customerToken`、`expireTime` 秒） |
| 查詢／解綁付款工具 | `POST /api/v1/customer/paymentInstrument/query`、`/unbind` |

付款工具沒有建立 API，須透過「建立付款交易」＋ SDK 綁卡（`paymentBehavior=CardBind`／`CardBindPayment`）。

### 平台專用

| 功能 | 路徑 |
|------|------|
| 分帳建立／查詢 | `POST /api/v1/trade/split/create`、`/api/v1/trade/split/query` |
| 轉帳建立／查詢 | `POST /api/v1/trade/transfers/create`、`/api/v1/trade/transfers/query` |
| 子特店 KYC 建立 | `POST /api/v1/kyc/mid/create` |
| KYC 送審／更新／主體查詢 | `POST /api/v1/kyc/merchant/submit`、`/api/v1/kyc/merchant/update`、`/api/v1/kyc/entity/query` |
| 子特店付款方式查詢 | `POST /api/v1/kyc/online-store/payment-method-query` |
| KYC 檔案上傳 | `POST file-api.shoplinepayments.com/api/v1/kyc/file/upload`（沙盒 `file-api-sandbox.shoplinepayments.com`） |
| Apple Pay 網域驗證／查詢 | `POST /api/v1/apple-domain/verify`、`/api/v1/apple-domain/query` |

### Webhook

由 SLP 主動 POST 至特店在後台設定的 Webhook URL，事件清單見「付款通知」章節。另有 Event 查詢 `GET {URI}/v1/api/events/query/{eventId}`（Header `appKey`、`appId`），文件未說明 `{URI}` 與這兩個 Header 的取得方式。

（各 API 頁 docs.shoplinepayments.com/api/…，2026-11-17 查核）

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
| `confirm.autoSettle` | Boolean | 否 | 自動結算，預設 `true`；僅平台特店 |
| `splitInfo.splitMode` | String(16) | 否 | 平台分帳，目前僅 `DELAYED`；未開通分帳權限的請求會被攔截 |
| `order` | Object | ● | 訂單資訊 |
| `customer` | Object | ● | 顧客資訊 |
| `billing` | Object | ● | 帳單資訊 |
| `client` | Object | ● | 客戶端資訊（至少 `ip`） |

#### `paymentMethodOptions` 進階選項

| 付款方式 | 子參數 | 說明 |
|----------|--------|------|
| `CreditCard` | `installmentCounts` | 分期期數陣列，如 `["0","3","6","12"]`；`"0"` 代表一次付清；不帶只開一般交易 |
| `VirtualAccount` | `paymentExpireTime` | ATM 繳費期限（分鐘），1440～86400，預設 4320（3 天），不足整天無條件進位 |
| `JKOPay` | `paymentExpireTime` | 街口付款期限（分鐘），預設 60 |
| `ChaileaseBNPL` | `installmentCounts`、`paymentExpireTime` | 中租 zingla 分期；期限預設 4320 分鐘 |

> `ApplePay` 與 `LinePay` **不支援** `paymentMethodOptions`，傳入會被忽略。

#### `order` 訂單資訊

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `order.purchaseScene` | String(16) | 否 | 消費場景 |
| `order.products[]` | Array | ● | 商品列表（風控必需） |
| `products[].id` | String(64) | ● | 商品 ID |
| `products[].name` | String(128) | ● | 商品名稱 |
| `products[].quantity` | Integer | ● | 數量 |
| `products[].amount.value` | Number(14) | ● | 單品金額（分） |
| `products[].amount.currency` | String | ● | 幣別 |
| `products[].sku` | String(64) | 否 | 商品 SKU |
| `products[].desc` | String(512) | 否 | 商品描述 |
| `products[].url` | String(256) | 否 | 商品頁連結 |
| `order.shipping` | Object | ● | 物流資訊（風控必需） |
| `shipping.shippingMethod` | String(64) | ● | 物流方式，如超商取貨／宅配 |
| `shipping.carrier` | String(64) | ● | 物流通路，如黑貓宅配 |
| `shipping.personalInfo` | Object | ● | 收件人，欄位同下方 `personalInfo` |
| `shipping.address` | Object | ● | 送貨地址，欄位同下方 `address` |

#### `customer` 顧客資訊

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `referenceCustomerId` | String(32) | ● | 特店端顧客唯一識別碼 |
| `type` | String(1) | 否 | 顧客類型 |
| `personalInfo` | Object | ● | 見下 |
| `gender`、`identityType`、`identityNumber` | String | 否 | 特定國家才需要 |

`personalInfo`（`customer`、`billing`、`shipping` 共用）：

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `lastName` | String(128) | ● | 姓；`firstName` + `lastName` 合計不可超過 128 |
| `firstName` | String(128) | 否 | 名 |
| `email` | String(128) | △ | `email` 與 `phone` 至少擇一 |
| `phone` | String(64) | △ | 需帶國碼，如 `+886912345678` |

> 中文姓名拆分慣例：第一個字為 `lastName`（姓），其餘為 `firstName`（名）。

#### `billing` / `address`

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `billing.description` | String(32) | 否 | 帳單描述 |
| `billing.personalInfo` | Object | ● | 同上 `personalInfo` |
| `billing.address` | Object | ● | 見下 |
| `address.countryCode` | String(2) | ● | ISO 國碼，如 `TW` |
| `address.street` | String(128) | ● | 街道地址 |
| `address.stateCode`／`state`／`city`／`district`／`postcode` | String | 否 | 州省代碼／州省／城市／行政區／郵遞區號 |

#### `client` 客戶端資訊

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `client.ip` | String(32) | ● | 顧客 IP；`paymentBehavior=Recurring` 可填特店辦公室 IP |
| `client.userAgent` | String(128) | 否 | 瀏覽器 UA |
| `client.language` | String(32) | 否 | `navigator.language` |
| `client.screenWidth`／`screenHeight`／`colorDepth`／`timeZoneOffset`／`javaEnabled`／`transactionWebSite`／`accept` | String | 否 | 3DS 與風控用的瀏覽器資訊 |

（/api/trade/session/，2026-11-17 查核）

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
| `EXPIRED` | 已過期（`expireTime` 預設 360 分鐘） |

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
| `language` | String(6) | ● | 語系 |
| `amount.value` | Number(14) | ● | 金額（分） |
| `amount.currency` | String | ● | 幣別 `TWD` |
| `expireTime` | Integer | 否 | 逾時（分鐘），僅部分付款方式（如 ATM）支援 |
| `returnUrl` | String(256) | ● | 完成後導回 URL |
| `paySession` | JSON String | ● | 由前端 SDK 取得，原樣傳入 |
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
| `paymentMethod` | ● 主付款方式（如 `CreditCard`） |
| `subPaymentMethod` | 子付款方式 |
| `autoConfirm` | SDK 自動確認，預設 `false`；`paymentBehavior=Recurring` 時設 `true` |
| `autoCapture` | 是否自動請款，預設 `true`（`false` 為兩段式） |
| `autoSettle` | 自動結算，預設 `true`；僅平台特店 |
| `splitInfo.splitMode` | 平台分帳，目前僅 `DELAYED` |
| `paymentBehavior` | ● 付款場景：`Regular` 一般、`CardBind` 純綁卡（固定以 1 元綁卡）、`CardBindPayment` 付款並綁卡、`QuickPayment` 已綁卡快捷付款、`Recurring` 定期扣款 |
| `paymentCustomerId` | SLP 付款會員 ID；快捷付款、定期扣款必填 |
| `paymentInstrument.paymentInstrumentId` | 付款工具 ID |
| `paymentInstrument.savePaymentInstrument` | `CardBind`／`CardBindPayment` 時必須為 `true` |

### 成功回應

建立付款交易、查詢付款交易（`payment/get`）與 `trade.*` Webhook 的 `data` 結構相同：

```json
{
  "acquirerType": "SDK",
  "referenceOrderId": "ORDER-2026050701",
  "tradeOrderId": "10010061012921418117718876160",
  "sessionId": "",
  "status": "PROCESSING",
  "subStatus": "AUTHORIZED",
  "paymentMsg": null,
  "actionType": "SDK",
  "nextAction": null,
  "order": {
    "amount": { "value": 100000, "currency": "TWD" },
    "referenceOrderId": "ORDER-2026050701",
    "createTime": "1718551768994",
    "customer": { "referenceCustomerId": "CUST-001", "customerId": "12412dr133" }
  },
  "payment": {
    "paymentMethod": "CreditCard",
    "autoCapture": false,
    "paymentBehavior": "Regular",
    "paymentSuccessTime": "",
    "isSettle": false,
    "paidAmount": { "value": 100000, "currency": "TWD" },
    "channelDealId": "",
    "creditCard": { "type": "CREDIT", "bin": "414763", "last4": "8405", "brand": "Visa" },
    "paymentInstrument": { "paymentInstrumentId": "6456462132132", "savePaymentInstrument": true }
  },
  "additionalData": {}
}
```

| 欄位 | 說明 |
|------|------|
| `status`／`subStatus` | 見下表；手動請款要看 `subStatus` |
| `paymentMsg` | 失敗原因 `{code, msg}` |
| `nextAction` | 3DS、跳轉 App 等後續動作，特店不用解析，原樣交給 SDK |
| `order.customer.customerId` | SLP 會員 ID；`referenceCustomerId` 不存在時會新建 |
| `payment.paidAmount` | 實際付款金額 |
| `payment.channelDealId` | 第三方流水號，街口與 LINE Pay 對帳用 |
| `payment.creditCard` | `type`、`bin`、`last4` 必有；`category`、`issuer`、`issuerCountry`、`brand` 選填 |
| `payment.virtualAccount` | `dueDate`、`dueDateDesc`、`recipientAccountNum`、`recipientBankCode`、`paymentAccountNum`、`paymentBankCode` |
| `payment.linePay[]` | `amount`、`currency`、`paymentMethod`，信用卡時另有 `bin`、`last4` |
| `payment.isSettle` | 是否已結算 |
| `payment.paymentMethodOptions.installments` | 分期資訊：`count` 期數、`installDownPay` 首期、`installPay` 每期（皆為分） |

（/api/trade/create/、/api/trade/query/，2026-11-17 查核）

### 交易狀態（`status`）

| 狀態 | 說明 |
|------|------|
| `CREATED` | 已建立（訂單、風控、特店狀態檢核中） |
| `CUSTOMER_ACTION` | 顧客處理中（3DS、指紋／臉部驗證、掃 QR Code） |
| `PROCESSING` | SLP 處理中；信用卡授權成功、尚未請款也在此狀態 |
| `SUCCEEDED` | 成功（信用卡為請款成功） |
| `FAILED` | 失敗（授權失敗、請款失敗、3DS 失敗、風控攔截等） |
| `CANCELLED` | 已取消 |
| `EXPIRED` | 已逾期（未付款訂單 6 小時逾期、3DS 或 QR Code 逾期） |

### `subStatus` 子狀態

| `status` | `subStatus` | 說明 |
|----------|-------------|------|
| `PROCESSING` | `AUTHORIZED` | 已授權，待請款或取消 |
| `PROCESSING` | `PENDING_REVIEW` | 人工審核中 |
| `PROCESSING` | `RISK_PENDING` | 風控審核中 |
| `FAILED` | `RISK_REJECTED` | 風控拒絕 |
| `FAILED` | `CONFIRM_FAILED` | 授權失敗 |
| `FAILED` | `CAPTURE_FAILED` | 請款失敗 |
| `FAILED` | `FAILED` | 交易失敗 |

退款狀態不在 `subStatus`，改查 `refund/get` 或 `trade.refund.*` 事件。（/appendix/orderStatus/，2026-11-17 查核）

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
| `referenceOrderId` | String(32) | △ | 特店訂單號（與 `tradeOrderId` 至少帶一個） |
| `tradeOrderId` | String(32) | △ | SLP 交易訂單編號 |
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
  "additionalData": {}
}
```

> 回應 `status` 為付款交易狀態（見「交易狀態」）。最終結果以 `payment/get` 或請款事件為準：請款成功後 `status=SUCCEEDED`，請款失敗為 `FAILED` + `subStatus=CAPTURE_FAILED`。

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
CREATED ─▶ (CUSTOMER_ACTION：3DS) ─▶ PROCESSING / subStatus=AUTHORIZED
                                         │
                     ┌─ capture ─────────┴───────── cancel ─┐
                     ▼                                       ▼
                 SUCCEEDED ─▶ refund/create              CANCELLED
```

`autoCapture=true`（預設）時授權後直接請款，交易會直接到 `SUCCEEDED`。

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
| `merchantId` | ● | SLP 特店 ID |
| `platformId` | | 平台特店才有 |
| `apiVersion` | ● | API 版本，如 `V1.2`；不同版本報文結構不同 |
| `requestId` | ● | 請求流水號 |
| `timestamp` | ● | 通知產生時間（毫秒時間戳） |
| `sign` | ● | HMAC-SHA256 簽章值（hex） |
| `idempotentKey` | | 冪等鍵 |

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
| `dispute.chargeback.*` | 拒付：`created`、`evidence_required`、`evidence_under_review`、`evidence_returned`、`resolved`、`cancelled`、`lost`、`won`、`expired`、`accepted` |
| `dispute.pre-chargeback.*` | 預爭議：`created`、`in_accept`、`in_reject`、`in_expire`、`accepted`、`merchant_rejected` |
| `dispute.fraud.finished` | 欺詐預警 |
| `dispute.retrieval.*` | 調單：`created`、`finished`、`cancelled` |
| `trade.settled` | 子特店結算（平台） |
| `merchant.kyc.audit` | 子特店 KYC 審核結果（平台） |
| `trade.split.*` | 分帳：`created`、`processing`、`cancelled`、`succeeded`、`failed`（平台） |

手動請款／取消授權另有事件，`type` 如 `manual.trade.capture.succeeded`、`manual.trade.cancel.succeeded`，`data` 含 `tradeCaptureOrderId`／`tradeCancelOrderId`、`status`、`paymentMsg`（/api/event/model/capture/、/cancel/；這兩類不在事件總表內）。

> 預設訂閱全部事件；要調整訂閱清單須聯絡串接窗口。SLP 可能隨時新增事件類型，特店實作應對未知事件「忽略並回應 200」。（/api/event/model/，2026-11-17 查核）

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
  const a = Buffer.from(expected, 'hex');
  const b = Buffer.from(String(sign || ''), 'hex');
  // 長度不同時 timingSafeEqual 會直接丟例外，先檢查
  return a.length === b.length && crypto.timingSafeEqual(a, b);
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
    if (!verifyShoplineSignature(timestamp, rawBody, sign, config.SHOPLINE_SIGN_KEY)) {
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

if (!verifyShoplineSignature($timestamp, $body, $sign, $config['SHOPLINE_SIGN_KEY'])) {
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

1. **回應 HTTP 200** — 非 200 視為失敗，共通知 16 次，間隔 15s/15s/30s/3m/10m/20m/30m/1h/1h/2h/3h/6h/6h/6h/12h/12h
2. **冪等去重** — 以事件 `id` 作為唯一鍵，避免重複入帳
3. **非同步處理** — 建議先回 200，再以 Queue 處理業務邏輯
4. **必須驗證簽章** — 不可省略
5. **驗證 timestamp** — 防止重放攻擊
6. **HTTPS 必填** — Webhook URL 必須為 HTTPS
7. **未知事件忽略** — 對 `default` 分支回傳 200

### Webhook 設定

在 SHOPLINE Payments 後台「設定 → 開發者管理」自行設定 Webhook URL（HTTPS），每個 URL 有自己的 `signKey`。訂閱清單預設為全部事件，要改才需聯絡串接窗口。

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
| `additionalData` | Map | 否 | 附加資料 |

退款沒有回呼網址參數，結果以 `trade.refund.*` 事件或 `refund/get` 為準。

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
  "refundOrderId": "45668468546465",
  "referenceOrderId": "REFUND-2026050701",
  "tradeOrderId": "10010061012921418117718876160",
  "amount": { "value": 50000, "currency": "TWD" },
  "status": "PROCESSING",
  "refundMsg": null,
  "destinationDetails": null
}
```

- `refundMsg`：失敗原因 `{code, msg}`
- `destinationDetails.linePay[]`：LINE Pay 退款退回明細（`amount`、`currency`、`paymentMethod`，信用卡另有 `bin`、`last4`）

### 查詢退款

`POST /api/v1/trade/refund/get`，body `{ "refundOrderId": "45668468546465" }`，回應欄位同上。（/api/trade/refundQuery/）

### 退款規則

- **退款時效**：原交易完成後 **180 天**內可退款
- **部分退款**：支援，金額 ≤ 可退餘額
- **多筆退款**：支援，總金額 ≤ 原交易金額
- **同一筆只能有一個處理中的退款**：上一筆退款處理中時無法發起新退款
- **線下退款**：通路不支援線上退款 API 時回 `1202`，只能線下退款

### 退款狀態

| 狀態 | 說明 |
|------|------|
| `CREATED` | 退款請求已受理，待 SLP 處理 |
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

結構同「內嵌式付款建立 → 成功回應」：頂層 `referenceOrderId`、`tradeOrderId`、`sessionId`、`status`、`subStatus`、`paymentMsg`、`actionType`、`nextAction`，訂單在 `order`，付款明細（`paidAmount`、`creditCard`、`virtualAccount`、`linePay`、`channelDealId` 等）在 `payment`。（/api/trade/query/）

### 使用時機

1. **顧客自 returnUrl 返回時** — 主動查詢確認付款狀態
2. **Webhook 補充驗證** — 收到通知後雙重確認
3. **訂單對帳** — 定期同步付款狀態
4. **客服查詢** — 客服查詢交易詳情
5. **失敗重試後** — 確認最終結果

---

## 錯誤代碼

> 依官方「Server 錯誤碼」附錄（docs.shoplinepayments.com/appendix/errorCode/，2026-11-17 核對無變動）；SDK 前端錯誤碼另見 /appendix/sdkErrorCode/。下表為節錄，
> 通用、Connect、下單、付款、退款、Onboarding 六個場景共 143 個代碼全部收在 `data/error-codes.csv`。
> 同一代碼可能出現在多個場景（例如 `1004` 在下單與 Onboarding 意義不同），判讀時要搭配呼叫的 API。

SHOPLINE Payments 錯誤碼以「字串」形式回傳：

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
| `1901`、`1902`、`1904` | 系統連線失敗／內部格式錯誤／請求過於頻繁 | 退避重試 |
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
| `"9"` | 9 期分期 |
| `"12"` | 12 期分期 |
| `"18"` | 18 期分期 |
| `"24"` | 24 期分期 |

> 分期限 Visa／MasterCard／JCB（一般交易另支援 UnionPay），各期數支援的銀行不同（如 9 期沒有玉山、永豐；18、24 期沒有永豐），完整銀行表見 /overview/supportedPaymentMethod/CreditCard/。中租 zingla（`ChaileaseBNPL`）支援一次付清與 3/6/12/18/24/30/36 期。（2026-11-17 查核）

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

官方提供共用沙盒後台帳號，登入後在「設定 → 開發者管理」取得 `apiKey`／`clientKey`／`signKey`（/overview/sandboxResource/）：

| 用途 | 登入帳號 | Merchant ID |
|------|----------|-------------|
| 一般特店 | `slpsandbox2@shopline.com` | `2652289079513847808` |
| 一般特店（另有 `+003`、`+004`、`+005` 共 5 組） | `slpsandbox2+001@shopline.com` | `2875079337371111424` |
| 平台特店（Connect 與交易） | `slpsandbox1@shopline.com` | `2652270930693330944`（同時是 Platform ID） |
| 子特店（KYC 未通過／通過） | `slpsandbox3@`、`slpsandbox4@`、`slpsandbox5@shopline.com` | 見官方頁 |

密碼皆為 `shoplinePayments123.`，官方要求不要修改。

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
帳號：slpsandbox2+001@shopline.com
密碼：Aa123456!
```

> 請勿修改密碼，也不要設定雙重驗證；由所有 SLP 沙盒測試共用。

#### 設定步驟

1. 準備 macOS 10.14.1+ 或 iOS 12.1+ 裝置（正式環境自 2025 年 5 月起，非 Apple 裝置會顯示 QR Code，供 iOS 18 以上 iPhone 掃碼付款）
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

1. Webhook URL 是否已在後台「設定 → 開發者管理」設定，且用的是該 URL 對應的 `signKey`
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
const refundable = trade.payment.paidAmount.value - alreadyRefunded;
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
- **付款／退款／結帳狀態碼**：https://docs.shoplinepayments.com/appendix/orderStatus/、/appendix/refundStatus/、/appendix/sessionStatus/
- **沙盒資源**：https://docs.shoplinepayments.com/overview/sandboxResource/
- **SDK 錯誤碼**：https://docs.shoplinepayments.com/appendix/sdkErrorCode/
- **AI 輔助串接（官方 MCP）**：https://docs.shoplinepayments.com/overview/intergrationGuide/AiToolMcp/（npm `@shoplinepayments/slpayment-developer-mcp`）
- **串接申請**：透過 SHOPLINE Payments 業務窗口

