# TapPay Payment API Reference

TapPay（拍付國際）金流 API 完整參考文件（繁體中文）。

TapPay 為亞太地區的「支付處理商（Payment Processor）」，介於商家系統與收單行（Acquirer）之間。其核心特色為「兩段式 PCI 隔離架構」：前端 SDK 取得 **Prime Token**（一次性、約 90 秒效期），後端使用 Prime 呼叫 `pay-by-prime` 完成扣款，PAN 完整卡號**永不**經過商家伺服器。

> **資料來源說明**：本文件之 SDK 操作與 `pay-by-prime` 請求格式參考自 TapPay 官方 Web Example Repo（`github.com/TapPay/tappay-web-example`）。完整 API 規格仍以 `docs.tappaysdk.com` 為準，部分欄位（特別是各支付方式延伸欄位、查詢 / 退款回應細節）以 ⚠️ 標示，正式上線前請對照官方文件驗證。

---

## 目錄

1. [基本說明](#基本說明)
2. [環境資訊](#環境資訊)
3. [API 端點總覽](#api-端點總覽)
4. [認證方式](#認證方式)
5. [前端 SDK 載入與初始化](#前端-sdk-載入與初始化)
6. [Prime 取得流程（Direct Pay iframe）](#prime-取得流程direct-pay-iframe)
7. [Prime 取得流程（TapPay Fields）](#prime-取得流程tappay-fields)
8. [Prime 取得流程（Apple Pay）](#prime-取得流程apple-pay)
9. [Prime 取得流程（Google Pay）](#prime-取得流程google-pay)
10. [Prime 取得流程（LINE Pay / JKO Pay）](#prime-取得流程line-pay--jko-pay)
11. [Prime 取得流程（Virtual Account 虛擬帳號）](#prime-取得流程virtual-account-虛擬帳號)
12. [訂單建立（Pay by Prime）](#訂單建立pay-by-prime)
13. [Card Token 重複扣款（Pay by Token）](#card-token-重複扣款pay-by-token)
14. [付款通知（Backend Notify）](#付款通知backend-notify)
15. [退款（Refund）](#退款refund)
16. [訂單查詢（Transaction Query）](#訂單查詢transaction-query)
17. [錯誤代碼](#錯誤代碼)
18. [支付方式對照表](#支付方式對照表)
19. [常見問題排解](#常見問題排解)

---

## 基本說明

### 什麼是 TapPay

TapPay 為「拍付國際資訊股份有限公司」旗下支付處理服務，定位介於商家與收單銀行之間。台灣多數電商與 SaaS 業者採用 TapPay 作為信用卡 + 行動錢包的整合層，原因包括：

- 透過 iframe / Tokenization，PAN 不落地，**降低 PCI-DSS 合規等級**
- 一次串接即可使用信用卡、Apple Pay、Google Pay、Samsung Pay、LINE Pay、JKO Pay 等多種支付
- 提供 Card Token 機制供「綁定卡片再扣款」、「定期定額」場景使用

### 整合特性

| 特性 | 說明 |
|------|------|
| **架構模式** | 兩段式（Two-stage）：前端取 Prime → 後端 Pay by Prime |
| **協定** | RESTful HTTPS + JSON |
| **認證** | HTTP Header `x-api-key`（攜帶 Partner Key） |
| **編碼** | UTF-8 |
| **PAN 處理** | 卡號全程託管於 TapPay iframe / Tokenization Vault |
| **Prime 效期** | 一次性、約 90 秒 |
| **HTTP 狀態碼** | 業務結果由 JSON 內 `status` 判定（`0` = 成功） |

### 兩段式架構流程

```
┌────────────┐  ① 卡號輸入       ┌──────────────┐
│  消費者    │ ────────────────▶ │ TapPay iframe │
│ 瀏覽器     │                   │ (前端 SDK)    │
└────────────┘                   └──────┬───────┘
       │                                │
       │ ② 取得 Prime Token             │
       │ ◀──────────────────────────────┘
       │
       │ ③ 將 Prime + 訂單資料送到商家後端
       ▼
┌────────────┐  ④ pay-by-prime  ┌──────────────┐
│  商家      │ ────────────────▶ │   TapPay     │
│ 後端伺服器 │                   │ Payment Core │
└────────────┘  ⑤ 交易結果     └──────┬───────┘
       │       ◀────────────────────────┘
       │                                │
       │                                │ ⑥ 收單行授權
       ▼                                ▼
┌────────────┐                  ┌──────────────┐
│  商家 DB   │                  │  收單行 / 發卡行 │
└────────────┘                  └──────────────┘
```

### 商務面前置作業

1. 註冊 [TapPay Portal](https://portal.tappaysdk.com) 商家帳號
2. 完成商家審核（需提供統編、營業項目、網域）
3. 取得三組金鑰：
   - **App ID**（前端使用，數字）
   - **App Key**（前端使用，字串）
   - **Partner Key**（後端使用，敏感資料，**禁止**外洩到瀏覽器）
4. 取得 **Merchant ID**（每種支付方式各有獨立 Merchant ID）
5. 設定回調網域（Backend Notify URL、Frontend Redirect URL）

### 名詞對照

| TapPay 用詞 | 等效概念 |
|-------------|----------|
| Prime | 一次性付款憑證（90 秒效期） |
| Card Token | 長效卡片憑證（綁卡後重複使用） |
| Partner Key | 後端 API Key（敏感） |
| App Key | 前端 SDK Key（公開） |
| Merchant ID | 各支付方式獨立的商店代碼 |

---

## 環境資訊

### Base URL

| 環境 | 後端 API Host | 前端 SDK Host |
|------|---------------|----------------|
| 沙箱（Sandbox） | `https://sandbox.tappaysdk.com` | `https://js.tappaysdk.com` |
| 正式（Production） | `https://prod.tappaysdk.com` | `https://js.tappaysdk.com` |

> **注意**：前端 SDK 不分環境，沙箱 / 正式以 `TPDirect.setupSDK()` 第三個參數 `'sandbox'` 或 `'production'` 切換。

### 通訊規格

| 項目 | 規格 |
|------|------|
| 協定 | HTTPS（TLS 1.2 以上） |
| 編碼 | UTF-8 |
| Content-Type | `application/json` |
| HTTP Method | POST（除少數查詢端點外） |
| 認證 Header | `x-api-key: <PARTNER_KEY>` |

### 測試卡號

```
卡號:        4242 4242 4242 4242
CVC:         123
有效月年:    任意未過期日期（如 12/30）
3D 驗證 OTP: 任意 6 碼
```

> **沙箱限制**：沙箱不會實際扣款，但仍需通過 3D 驗證流程；部分支付方式（如 LINE Pay、JKO Pay）需向 TapPay 申請沙箱測試帳號。

### Web SDK 版本對照（節錄）⚠️

| SDK 版本 | 主要支援 |
|----------|----------|
| `v3+` | Apple Pay 透過 Payment Request API |
| `v4+` | Google Pay |
| `v5+` | TapPay Fields、Direct Pay iframe（最新） |

> 版本須對照 [TapPay GitHub Releases](https://github.com/TapPay/tappay-web-example/releases) 公布的 SRI Hash。

---

## API 端點總覽

### 後端核心交易 API

| 功能 | Method | Path |
|------|--------|------|
| **以 Prime 付款** | POST | `/tpc/payment/pay-by-prime` |
| **以 Card Token 付款** | POST | `/tpc/payment/pay-by-token` |
| **訂單查詢** | POST | `/tpc/transaction/query` |
| **退款** | POST | `/tpc/transaction/refund` |
| **取消授權（Cap Refund）** | POST | `/tpc/transaction/cap-refund` |
| **請款（Capture）** | POST | `/tpc/transaction/capture` |

### 卡片管理 API ⚠️

| 功能 | Method | Path |
|------|--------|------|
| **解除卡片綁定** | POST | `/tpc/card/remove` |
| **查詢綁定卡片** | POST | `/tpc/card/query` |

### 完整 URL 範例

```
POST https://sandbox.tappaysdk.com/tpc/payment/pay-by-prime
POST https://prod.tappaysdk.com/tpc/payment/pay-by-prime
```

---

## 認證方式

### Header 規格

所有後端 API 都需要以下 Header：

| Header | 必填 | 說明 |
|--------|------|------|
| `Content-Type` | ● | 固定 `application/json` |
| `x-api-key` | ● | Partner Key（後端專用，**勿外洩**） |

### Body 內 Partner Key 重複帶入

TapPay 多數端點的 Body 內也需要再帶一次 `partner_key` 欄位（非 Header），這是為了向下相容舊版簽章機制。範例：

```json
{
  "partner_key": "partner_xxxxxxxxxxxxxxxxxxxxx",
  "prime": "...",
  "amount": 100
}
```

### Partner Key 安全準則

- **僅用於伺服器端**，不可放在 HTML / JS / APP 端
- 建議放置於環境變數（如 `TAPPAY_PARTNER_KEY`）
- Git 倉庫加入 `.gitignore` 排除 `.env` 檔
- 如疑似外洩，立即至 Portal 重新產生

### 前端 SDK 認證

前端 SDK 採用 App ID + App Key 設定，並由 TapPay 後台校驗網域：

```js
TPDirect.setupSDK(APP_ID, "APP_KEY", "sandbox");
//   APP_ID      number    - TapPay Portal 取得（數字 ID）
//   APP_KEY     string    - TapPay Portal 取得
//   SERVER_TYPE string    - "sandbox" 或 "production"
```

> **注意**：App Key 雖在前端公開，仍受網域白名單保護，須於 Portal 設定允許的 `Domain`，否則 SDK 會拒絕初始化。

---

## 前端 SDK 載入與初始化

### 1. 透過 SRI（推薦）

```html
<script
  src="https://js.tappaysdk.com/sdk/tpdirect/v5.19.2"
  type="text/javascript"
  integrity="sha256-<hash_key_from_release_notes>"
  crossorigin="anonymous"></script>
```

### 2. 不使用 SRI

```html
<script src="https://js.tappaysdk.com/sdk/tpdirect/v5.19.2"
        type="text/javascript"></script>
```

### 3. 初始化

```js
TPDirect.setupSDK(
  12345,                    // APP_ID
  "app_xxxxxxxxxxxxxxxx",   // APP_KEY
  "sandbox"                 // 'sandbox' 或 'production'
);
```

### 4. 通用 Prime 回應結構

所有 `getPrime` 回呼皆會收到下列基本欄位（依支付方式可能延伸）：

| 欄位 | 類型 | 說明 |
|------|------|------|
| `status` | Integer | `0` 表示成功，其他為錯誤 |
| `msg` | String | 訊息 |
| `card.prime` | String | Prime Token（信用卡類） |
| `prime` | String | Prime Token（行動錢包類） |
| `clientip` | String | 偵測到的客戶端 IP |
| `card.bin` | String | 卡號前 6 碼（部分支付方式） |
| `card.lastfour` | String | 卡號末 4 碼（部分支付方式） |
| `card.funding` | Integer | `0`:Credit `1`:Debit `2`:Prepaid `-1`:Unknown |
| `card.type` | Integer | `1`:VISA `2`:Master `3`:JCB `4`:UnionPay `5`:AMEX |

---

## Prime 取得流程（Direct Pay iframe）

「Direct Pay iframe」為 TapPay 預設整合方式：將整張刷卡表單以單一 iframe 嵌入商家頁面，商家僅控制外框 CSS。

### Step 1：放置容器

```html
<form id="pay-form">
  <div id="card-number"></div>
  <div id="card-expiration-date"></div>
  <div id="card-ccv"></div>
  <button id="submit-btn" type="button" disabled>付款</button>
</form>
```

### Step 2：掛載 iframe

```js
TPDirect.card.setup({
  fields: {
    number:         { element: '#card-number',          placeholder: '**** **** **** ****' },
    expirationDate: { element: '#card-expiration-date', placeholder: 'MM / YY' },
    ccv:            { element: '#card-ccv',             placeholder: 'CCV' }
  },
  styles: {
    'input': { 'color': '#333', 'font-size': '16px' },
    'input.ccv': { 'font-size': '14px' }
  },
  isMaskCreditCardNumber: true,
  maskCreditCardNumberRange: { beginIndex: 6, endIndex: 11 }
});
```

### Step 3：監聽欄位狀態

```js
TPDirect.card.onUpdate(function (update) {
  // update.canGetPrime  → boolean
  // update.hasError     → boolean
  // update.status.number / .expiry / .ccv → 0(valid) / 1(error) / 2(empty)
  document.getElementById('submit-btn').disabled = !update.canGetPrime;
});
```

### Step 4：取得 Prime

```js
document.getElementById('submit-btn').addEventListener('click', function () {
  TPDirect.card.getPrime(function (result) {
    if (result.status !== 0) {
      console.error('getPrime failed:', result.msg);
      return;
    }
    const prime = result.card.prime;
    // ➡️ 送到商家後端
    fetch('/api/pay', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prime: prime, amount: 1500 })
    });
  });
});
```

### Direct Pay 注意事項

- iframe 限制無法在內部執行 JS hook，欲自訂錯誤訊息需在外層元件監聽 `onUpdate`
- 卡號遮罩（`isMaskCreditCardNumber`）僅顯示遮罩，實際卡號仍由 TapPay 處理
- 部分瀏覽器（特別是 iframe 跨來源 cookie）可能阻擋，需檢查 SameSite 設定

---

## Prime 取得流程（TapPay Fields）

當商家需要「完全自訂」每個欄位的版型（不接受單一 iframe），可改用 TapPay Fields。三個欄位（卡號、月年、CCV）各自為獨立 iframe，呈現上與一般 input 無異。

### 範例

```js
TPDirect.card.setup({
  fields: {
    number:         { element: document.getElementById('card-number'),         placeholder: '**** **** **** ****' },
    expirationDate: { element: document.getElementById('card-expiration-date'), placeholder: 'MM / YY' },
    ccv:            { element: document.getElementById('card-ccv'),             placeholder: 'CCV' }
  },
  styles: {
    'input':       { 'color': 'gray' },
    ':focus':      { 'color': 'black' },
    '.valid':      { 'color': 'green' },
    '.invalid':    { 'color': 'red' }
  }
});
```

`getPrime` 與 `onUpdate` 用法與 Direct Pay 相同。

> **適用情境**：UI/UX 嚴格要求自訂排版（例如卡號分段顯示、響應式表單）；商家可承擔較複雜的 CSS 維護成本。

---

## Prime 取得流程（Apple Pay）

Apple Pay 透過 W3C Payment Request API 整合（SDK v3+）。需於 Apple Developer 註冊 Merchant ID 並完成 Domain Verification。

### 前置作業

1. Apple Developer 取得 **Apple Merchant ID**（如 `merchant.com.example.shop`）
2. 上傳 Domain Verification 檔案到網站根目錄 `/.well-known/apple-developer-merchantid-domain-association`
3. 於 TapPay Portal 開通 Apple Pay 並輸入 Apple Merchant ID
4. 網站必須使用 **HTTPS**

### Step 1：偵測支援

```js
TPDirect.setupSDK(APP_ID, "APP_KEY", "sandbox");

const isAvailable = TPDirect.paymentRequestApi.checkAvailability();
if (!isAvailable) {
  // 該瀏覽器不支援 Apple Pay
}
```

### Step 2：組裝 Payment Request

```js
const data = {
  supportedNetworks: ['MASTERCARD', 'VISA', 'AMEX'],
  supportedMethods: ['apple_pay'],
  displayItems: [
    { label: 'iPhone8', amount: { currency: 'TWD', value: '30000.00' } }
  ],
  total: {
    label: '付給 ExampleShop',
    amount: { currency: 'TWD', value: '30000.00' }
  },
  shippingOptions: [
    { id: 'standard', label: '標準配送（2 天）', detail: '貨到付款',
      amount: { currency: 'TWD', value: '60.00' } }
  ],
  options: {
    requestPayerEmail: false,
    requestPayerName:  false,
    requestPayerPhone: false,
    requestShipping:   false,
    shippingType:      'shipping'
  }
};
```

### Step 3：設定 Apple Pay 商家識別

```js
TPDirect.paymentRequestApi.setupApplePay({
  merchantIdentifier: 'merchant.com.example.shop',
  countryCode:        'TW'
});
```

### Step 4：建立 Request 並綁定按鈕

```js
TPDirect.paymentRequestApi.setupPaymentRequest(data, function (result) {
  if (!result.canMakePaymentWithActiveCard) {
    return;
  }
  document.getElementById('apple-pay-btn').addEventListener('click', () => {
    TPDirect.paymentRequestApi.getPrime(function (r) {
      if (r.status !== 0) return;
      const prime = r.prime;
      // r.apple_pay 內含 Apple Pay 專屬欄位（billingContact 等）
      // ➡️ 送到後端
    });
  });
});
```

### Apple Pay 限制

- 僅支援 Safari（macOS / iOS）；其他瀏覽器無法呼叫
- 需 HTTPS（含本機開發，可使用 ngrok）
- TapPay 仍會將授權結果寫回 `pay-by-prime` 流程，等同於信用卡交易

---

## Prime 取得流程（Google Pay）

需 SDK v4+，並向 Google Pay & Wallet Console 註冊 Merchant Profile。

### Step 1：載入 SDK

```html
<script src="https://pay.google.com/gp/p/js/pay.js"></script>
<script src="https://js.tappaysdk.com/sdk/tpdirect/v5.19.2"></script>
```

### Step 2：初始化

```js
TPDirect.setupSDK(APP_ID, "APP_KEY", "sandbox");

TPDirect.googlePay.setupGooglePay({
  googleMerchantId: 'merchant_id_from_google',
  allowedCardAuthMethods: ['PAN_ONLY', 'CRYPTOGRAM_3DS'],
  merchantName: 'ExampleShop'
});
```

### Step 3：設定 Payment Request

```js
TPDirect.googlePay.setupPaymentRequest({
  allowedNetworks: ['AMEX', 'JCB', 'MASTERCARD', 'VISA'],
  price: '100',
  currency: 'TWD'
}, function (err, result) {
  if (result.canUseGooglePay) {
    TPDirect.googlePay.setupGooglePayButton({
      el: '#google-pay-btn',
      color: 'black',
      type: 'long',
      getPrimeCallback: function (err, prime) {
        if (err) return;
        // ➡️ 送到後端 pay-by-prime
      }
    });
  }
});
```

### Step 4：（可選）動態更新金額

```js
TPDirect.googlePay.setupTransactionInfo({
  totalPriceStatus: 'FINAL',
  totalPrice: '299',
  currencyCode: 'TWD'
});
```

### Google Pay 限制

- Android 5.0+ / iOS 7+
- 需 HTTPS
- 沙箱環境僅可使用測試卡

---

## Prime 取得流程（LINE Pay / JKO Pay）

行動錢包類支付的 SDK 介面非常統一：

```js
// LINE Pay
TPDirect.linePay.getPrime(function (result) {
  // result = { status, msg, prime, clientip }
});

// 街口支付
TPDirect.jkoPay.getPrime(function (result) {
  // 同上結構
});

// 悠遊付
TPDirect.easyWallet.getPrime(function (result) { /* ... */ });

// 一卡通 Money
TPDirect.iPassMoney.getPrime(function (result) { /* ... */ });

// PXPay Plus
TPDirect.pxpayplus.getPrime(function (result) { /* ... */ });
```

### 後端調用差異

行動錢包類 `pay-by-prime` 必須提供 `result_url`（前後端各一）：

```json
{
  "partner_key": "...",
  "prime":       "<prime>",
  "amount":      199,
  "merchant_id": "<LINEPAY_MERCHANT_ID>",
  "details":     "Order #1024",
  "cardholder":  { ... },
  "result_url": {
    "frontend_redirect_url": "https://shop.example.com/pay/result",
    "backend_notify_url":    "https://shop.example.com/api/notify"
  }
}
```

`pay-by-prime` 回應會回傳 `payment_url`，商家須將消費者重新導向至該 URL，由 LINE Pay / JKO Pay 完成驗證後再回到 `frontend_redirect_url`。

---

## Prime 取得流程（Virtual Account 虛擬帳號）

ATM 虛擬帳號採非同步入帳：消費者取得帳號後到 ATM / 網銀轉帳，TapPay 收到入帳後再以 Webhook 通知。

### 前端取 Prime

```html
<script src="https://js.tappaysdk.com/sdk/tpdirect/v5.19.2"></script>
```

```js
TPDirect.setupSDK(APP_ID, "APP_KEY", "sandbox");

TPDirect.virtualAccount.getPrime(function (error, result) {
  if (error || result.status !== 0) {
    console.error(result.msg);
    return;
  }
  const prime = result.prime;   // 以 "va_" 開頭
  // ➡️ 送到後端
});
```

### 後端 Pay by Prime 範例

```bash
curl -X POST https://sandbox.tappaysdk.com/tpc/payment/pay-by-prime \
  -H 'content-type: application/json' \
  -H 'x-api-key: <PARTNER_KEY>' \
  -d '{
    "partner_key": "<PARTNER_KEY>",
    "prime":       "va_xxxxxxxxxxxxxxx",
    "amount":      16,
    "merchant_id": "GlobalTesting_VIRTUAL_ACCOUNT",
    "details":     "Some item",
    "cardholder": {
      "phone_number": "+886923456789",
      "name":         "王小明",
      "email":        "littleming@wang.com",
      "zip_code":     "100",
      "address":      "台北市天龍區芝麻街1號1樓",
      "national_id":  "A190902632",
      "member_id":    "0123498765"
    },
    "result_url": {
      "frontend_redirect_url": "https://shop.example.com/pay/result",
      "backend_notify_url":    "https://shop.example.com/api/notify"
    }
  }'
```

### 回應重點

| 欄位 | 說明 |
|------|------|
| `status` | `0` 表示「取號成功」（非「已付款」） |
| `payment_url` | 顯示繳費資訊頁面（含虛擬帳號 / 銀行代碼 / 期限） |
| `bank_account_number` | 虛擬帳號（部分情境直接於 Webhook 回傳） |
| `bank_code` | 銀行代碼 |
| `expire_date` | 繳費期限 |

實際付款狀態須等 `backend_notify_url` 收到 TapPay POST 通知。

---

## 訂單建立（Pay by Prime）

最核心的後端 API，用於消費 Prime Token 完成扣款。

### 端點

```
POST {base_url}/tpc/payment/pay-by-prime
Headers:
  Content-Type: application/json
  x-api-key:    <PARTNER_KEY>
```

### 請求參數

#### 必填欄位

| 欄位 | 類型 | 長度 | 說明 |
|------|------|------|------|
| `partner_key` | String | - | Partner Key（與 Header 重複） |
| `prime` | String | - | 前端取得的 Prime Token |
| `merchant_id` | String | - | 對應該支付方式的 Merchant ID |
| `amount` | Integer | - | 金額（整數，**不含**小數） |
| `details` | String | 100 | 商品描述 |
| `cardholder` | Object | - | 持卡人資料（部分支付必填） |

#### `cardholder` 物件

| 欄位 | 必填 | 類型 | 說明 |
|------|------|------|------|
| `phone_number` | ● | String | 手機，建議 E.164 格式（`+886...`） |
| `name` | ● | String | 姓名 |
| `email` | ● | String | E-mail |
| `zip_code` | ○ | String | 郵遞區號 |
| `address` | ○ | String | 地址 |
| `national_id` | ○ | String | 身分證字號（虛擬帳號 / 部分電子錢包必填） |
| `member_id` | ○ | String | 商家會員 ID（風控用） |

#### 常用選填欄位

| 欄位 | 類型 | 說明 |
|------|------|------|
| `currency` | String | 幣別代碼（如 `TWD`、`USD`），預設 `TWD` |
| `order_number` | String | 商家自訂訂單編號（建議唯一） |
| `bank_transaction_id` | String | 收單行交易 ID（覆寫用，少用） |
| `three_domain_secure` | Boolean | 是否開啟 3D 驗證，預設 `false` |
| `result_url` | Object | 行動錢包 / 虛擬帳號類必填 |
| `remember` | Boolean | 是否回傳 Card Token（綁卡） |
| `instalment` | Integer | 分期期數（`0` = 不分期） |
| `delay_capture_in_days` | Integer | 延遲請款天數（`0`–`90`，預設 `0` 即時請款） |
| `redeem` | Boolean | 是否使用紅利點數（依收單行支援） |
| `kyc_verification` | Boolean | 是否啟用 KYC（部分支付） |

#### `result_url` 物件

| 欄位 | 必填 | 說明 |
|------|------|------|
| `frontend_redirect_url` | ● | 前台導回網址（消費者瀏覽器） |
| `backend_notify_url` | ● | 後台通知網址（TapPay 伺服器 → 商家伺服器） |

### 請求範例（信用卡）

```bash
curl -X POST https://sandbox.tappaysdk.com/tpc/payment/pay-by-prime \
  -H 'content-type: application/json' \
  -H 'x-api-key: <PARTNER_KEY>' \
  -d '{
    "partner_key": "<PARTNER_KEY>",
    "prime":       "test_prime_xxxxxxxxxxxxxxxxxxx",
    "amount":      1500,
    "merchant_id": "GlobalTesting_CTBC",
    "details":     "iPhone 15 Pro 256GB",
    "currency":    "TWD",
    "order_number":"ORD20260507001",
    "cardholder": {
      "phone_number": "+886923456789",
      "name":         "王小明",
      "email":        "test@example.com"
    },
    "remember":             false,
    "three_domain_secure":  false
  }'
```

### 回應參數

| 欄位 | 類型 | 說明 |
|------|------|------|
| `status` | Integer | `0`:成功 其他:失敗，詳見錯誤代碼 |
| `msg` | String | 訊息 |
| `rec_trade_id` | String | TapPay 交易編號（**重要**，後續退款 / 查詢使用） |
| `bank_transaction_id` | String | 收單行交易編號 |
| `auth_code` | String | 銀行授權碼（6 碼） |
| `card_secret` | Object | 包含 Card Token 與 Card Key（`remember=true` 時） |
| `card_info` | Object | 卡片資訊（bin / lastfour / type 等） |
| `transaction_time_millis` | Long | 交易時間（毫秒） |
| `payment_url` | String | （行動錢包 / 虛擬帳號）導向網址 |
| `acquirer` | String | 收單行代碼 |
| `amount` | Integer | 確認金額 |
| `currency` | String | 幣別 |
| `order_number` | String | 商家訂單編號（原值回傳） |

### `card_secret` 內容

當 `remember: true` 時：

| 欄位 | 說明 |
|------|------|
| `card_token` | 長效卡片代碼（用於 `pay-by-token`） |
| `card_key` | 對應 Token 的金鑰（須一併保存） |

> **安全建議**：`card_token` 與 `card_key` 必須加密儲存於商家資料庫，且僅後端可存取。

### `card_info` 內容

| 欄位 | 說明 |
|------|------|
| `bin_code` | 卡號前 6 碼 |
| `last_four` | 卡號末 4 碼 |
| `issuer` | 發卡銀行 |
| `funding` | `0`:Credit `1`:Debit `2`:Prepaid `-1`:Unknown |
| `type` | `1`:VISA `2`:MasterCard `3`:JCB `4`:UnionPay `5`:AMEX |
| `level` | 卡片等級（如 `classic` / `gold` / `platinum`） |
| `country` | 發卡國 |
| `country_code` | 國家代碼（ISO 3166-1） |

---

## Card Token 重複扣款（Pay by Token）

當商家需「免再次輸入卡片」即扣款（訂閱、自動續費、一鍵購買），於首次 `pay-by-prime` 時帶 `remember: true` 取得 `card_token` + `card_key`，之後改呼叫 `pay-by-token`。

### 端點

```
POST {base_url}/tpc/payment/pay-by-token
```

### 請求參數

| 欄位 | 必填 | 類型 | 說明 |
|------|------|------|------|
| `partner_key` | ● | String | Partner Key |
| `card_key` | ● | String | 從 `card_secret.card_key` 取得 |
| `card_token` | ● | String | 從 `card_secret.card_token` 取得 |
| `merchant_id` | ● | String | Merchant ID |
| `amount` | ● | Integer | 金額 |
| `currency` | ○ | String | 幣別，預設 `TWD` |
| `details` | ○ | String | 商品描述 |
| `order_number` | ○ | String | 商家訂單編號 |
| `three_domain_secure` | ○ | Boolean | 是否 3D 驗證 |
| `delay_capture_in_days` | ○ | Integer | 延遲請款天數 |

### 請求範例

```bash
curl -X POST https://sandbox.tappaysdk.com/tpc/payment/pay-by-token \
  -H 'content-type: application/json' \
  -H 'x-api-key: <PARTNER_KEY>' \
  -d '{
    "partner_key": "<PARTNER_KEY>",
    "card_key":    "<CARD_KEY>",
    "card_token":  "<CARD_TOKEN>",
    "merchant_id": "GlobalTesting_CTBC",
    "amount":      299,
    "currency":    "TWD",
    "details":     "Monthly Subscription",
    "order_number":"SUB20260507001"
  }'
```

### 回應

回應結構與 `pay-by-prime` 大致相同，但通常**不會**再回傳 `card_secret`（已綁定）。

### 注意事項

- 若卡片已過期 / 掛失，會回應 `card_token expired`，商家須引導使用者重新綁卡
- `card_token` 與 `card_key` 配對使用，遺失任一者都無法扣款
- 不建議將 `pay-by-token` 暴露在前端任何邏輯中

---

## 付款通知（Backend Notify）

`pay-by-prime` 包含 `result_url.backend_notify_url` 時，TapPay 會於交易確認後（如行動錢包付款完成、虛擬帳號入帳）以 POST 將結果送至該網址。

### 通知特性

| 項目 | 說明 |
|------|------|
| HTTP Method | POST |
| Content-Type | `application/json` |
| 重試機制 | 商家未回應 `200` 時，TapPay 會重送（次數依官方文件） |
| 來源 IP | 建議向 TapPay 索取最新白名單 |

### 通知欄位（節錄）⚠️

| 欄位 | 說明 |
|------|------|
| `status` | `0`:成功 其他:失敗 |
| `rec_trade_id` | TapPay 交易編號 |
| `bank_transaction_id` | 收單行交易編號 |
| `order_number` | 商家訂單編號 |
| `amount` | 金額 |
| `currency` | 幣別 |
| `acquirer` | 收單行 |
| `transaction_time_millis` | 交易時間（毫秒） |
| `auth_code` | 授權碼 |
| `card_info` | 卡片資訊 |
| `bank_result_code` | 銀行回應碼 |
| `bank_result_msg` | 銀行回應訊息 |

### 商家應回應

回 HTTP `200 OK` 即可，內容不限（可為空字串或 JSON `{"status":"ok"}`）。若回非 2xx，TapPay 會重送。

### 驗證真實性

1. **比對 `rec_trade_id`**：與商家先前 `pay-by-prime` 取得的編號一致
2. **比對 `amount`**：與訂單金額相符
3. **核對來源 IP**：是否在 TapPay 白名單
4. **冪等處理**：以 `rec_trade_id` 作為唯一鍵，避免重複處理

### 處理範例（Express）

```js
app.post('/api/tappay/notify', express.json(), async (req, res) => {
  const { rec_trade_id, order_number, amount, status } = req.body;

  // 1. 找對應訂單
  const order = await db.orders.findOne({ order_number });
  if (!order) return res.status(200).end();

  // 2. 驗證金額
  if (order.amount !== amount) {
    return res.status(200).end(); // 金額不符，丟棄
  }

  // 3. 冪等檢查
  if (order.tappay_trade_id === rec_trade_id && order.status === 'paid') {
    return res.status(200).end();
  }

  // 4. 更新狀態
  await db.orders.update({ order_number }, {
    tappay_trade_id: rec_trade_id,
    status: status === 0 ? 'paid' : 'failed',
    paid_at: new Date()
  });

  res.status(200).json({ status: 'ok' });
});
```

---

## 退款（Refund）

### 端點

```
POST {base_url}/tpc/transaction/refund
```

### 請求參數

| 欄位 | 必填 | 類型 | 說明 |
|------|------|------|------|
| `partner_key` | ● | String | Partner Key |
| `rec_trade_id` | ● | String | 原交易 `rec_trade_id` |
| `amount` | ○ | Integer | 退款金額。**省略時**全額退款 |

### 請求範例（部分退款）

```bash
curl -X POST https://sandbox.tappaysdk.com/tpc/transaction/refund \
  -H 'content-type: application/json' \
  -H 'x-api-key: <PARTNER_KEY>' \
  -d '{
    "partner_key":  "<PARTNER_KEY>",
    "rec_trade_id": "D20260507abcdefg123",
    "amount":       500
  }'
```

### 回應參數

| 欄位 | 說明 |
|------|------|
| `status` | `0`:成功 |
| `msg` | 訊息 |
| `refund_id` | 退款編號 |
| `refund_amount` | 此次退款金額 |
| `is_captured` | 原交易是否已請款（`true` 為退款，`false` 為取消授權） |

### 退款規則

- **未請款**（`is_captured: false`）：執行的是「取消授權」（Void），消費者帳單上不會出現該筆
- **已請款**（`is_captured: true`）：執行真正的退款（Refund），會於信用卡帳單顯示退款項目
- **部分退款**：支援，可多次執行直到累計等於原金額
- **退款期限**：依收單行而異，通常請款後 180 天內

### 取消授權（Cap Refund）⚠️

部分情境（如延遲請款交易）需呼叫專用端點：

```
POST {base_url}/tpc/transaction/cap-refund
```

請求結構同 `refund`。

---

## 訂單查詢（Transaction Query）

### 端點

```
POST {base_url}/tpc/transaction/query
```

### 請求參數

| 欄位 | 必填 | 類型 | 說明 |
|------|------|------|------|
| `partner_key` | ● | String | Partner Key |
| `records_per_page` | ○ | Integer | 每頁筆數（預設 50，最大 200） |
| `page` | ○ | Integer | 頁碼，從 `0` 開始 |
| `filters` | ○ | Object | 過濾條件 |
| `order_by` | ○ | Object | 排序方式 |

### `filters` 物件（節錄）

| 欄位 | 類型 | 說明 |
|------|------|------|
| `time` | Object | `{ "start_time": <ms>, "end_time": <ms> }` |
| `amount` | Object | `{ "lower_bound": 100, "upper_bound": 10000 }` |
| `cardholder` | Object | 篩選持卡人（如 `{ "email": "..." }`） |
| `merchant_id` | Array | Merchant ID 列表 |
| `record_status` | Integer | 交易狀態 |
| `rec_trade_id` | String | 直接以交易編號查詢 |
| `bank_transaction_id` | String | 收單行交易編號 |
| `order_number` | String | 商家訂單編號 |

### `order_by` 物件

| 欄位 | 類型 | 說明 |
|------|------|------|
| `attribute` | String | 排序欄位（如 `time`） |
| `is_descending` | Boolean | 是否倒序 |

### 請求範例

```bash
curl -X POST https://sandbox.tappaysdk.com/tpc/transaction/query \
  -H 'content-type: application/json' \
  -H 'x-api-key: <PARTNER_KEY>' \
  -d '{
    "partner_key": "<PARTNER_KEY>",
    "filters": {
      "order_number": "ORD20260507001"
    }
  }'
```

### 回應結構（節錄）⚠️

| 欄位 | 說明 |
|------|------|
| `status` | `0`:成功 |
| `msg` | 訊息 |
| `number_of_transactions` | 符合條件總筆數 |
| `trade_records` | 交易陣列 |

#### `trade_records` 中每筆

| 欄位 | 說明 |
|------|------|
| `record_status` | 交易狀態（見下表） |
| `rec_trade_id` | TapPay 交易編號 |
| `amount` | 金額 |
| `currency` | 幣別 |
| `order_number` | 商家訂單編號 |
| `acquirer` | 收單行 |
| `transaction_time_millis` | 交易時間（毫秒） |
| `bank_transaction_id` | 收單行交易編號 |
| `auth_code` | 授權碼 |
| `cardholder` | 持卡人物件 |
| `card_info` | 卡片資訊 |
| `refunded_amount` | 已退款金額 |

### `record_status` 狀態碼 ⚠️

| 代碼 | 說明 |
|------|------|
| `0` | 已授權 / 已請款 |
| `1` | 已取消授權 |
| `2` | 已退款（含部分退款） |
| `-1` | 失敗 |

> 部分狀態碼依支付方式 / 收單行而異，正式上線前請對照官方文件。

---

## 錯誤代碼

TapPay 錯誤訊息分為兩類：

1. **TapPay `status`**：TapPay 平台層級狀態碼
2. **`bank_result_code`**：來自收單行 / 發卡行的轉發碼

### 一般 status（節錄）⚠️

| 代碼 | 說明 | 處理建議 |
|------|------|----------|
| `0` | 成功 | - |
| `1` | 請求參數錯誤 | 檢查欄位 |
| `2` | Partner Key 錯誤 | 確認 Header 與 Body 的 `partner_key` |
| `3` | Prime 已被使用 | 重新取 Prime（用過即作廢） |
| `4` | Prime 已過期 | 重新取 Prime（90 秒效期） |
| `5` | Merchant ID 錯誤 | 確認該支付方式對應的 ID |
| `6` | 金額錯誤 | 檢查整數、最低 / 最高限制 |
| `7` | 幣別錯誤 | 檢查 `currency` |
| `10003` | 銀行授權失敗 | 詳見 `bank_result_code` |
| `10005` | 信用卡資料不正確 | 引導使用者重新輸入 |
| `88001` | 系統錯誤 | 稍後重試或聯繫 TapPay |

> 正式錯誤碼以 [TapPay 官方文件](https://docs.tappaysdk.com) 為準。本表為實務最常見項目。

### 銀行回應碼（節錄）⚠️

| `bank_result_code` | 說明 |
|--------------------|------|
| `0`、`00` | 授權成功 |
| `01` | 連繫發卡銀行 |
| `04` | 沒收卡片（不退還） |
| `05` | 拒絕交易 |
| `12` | 無效交易 |
| `14` | 無效卡號 |
| `41` | 掛失卡 |
| `43` | 偽冒卡 |
| `51` | 餘額不足 |
| `54` | 卡片過期 |
| `55` | 密碼錯誤 |
| `57` | 不允許此交易類型 |
| `58` | 不允許此商家類型 |
| `61` | 超過提款限額 |
| `62` | 受限制卡片 |
| `91` | 發卡行無回應 |

> 銀行回應碼為 ISO 8583 標準，發卡行各自實作可能有差異。

### Prime 錯誤碼（前端 SDK）⚠️

| `result.status` | 說明 |
|-----------------|------|
| `0` | 成功 |
| `-1` | 卡片資料無效 |
| `88` | 系統錯誤 |

---

## 支付方式對照表

| 支付方式 | SDK API | Prime 字首 | 適用情境 |
|----------|---------|------------|----------|
| 信用卡（Direct Pay） | `TPDirect.card.getPrime` | （無固定字首） | Web 標準刷卡 |
| TapPay Fields | `TPDirect.card.getPrime` | （無固定字首） | 自訂版型刷卡 |
| Apple Pay | `TPDirect.paymentRequestApi.getPrime` | （Apple Pay tokenization） | iOS / macOS Safari |
| Google Pay | `TPDirect.googlePay.getPrime` | （Google Pay tokenization） | Android / Chrome |
| Samsung Pay | `TPDirect.samsungPay.getPrime` | - | Samsung 裝置 |
| LINE Pay | `TPDirect.linePay.getPrime` | - | LINE 帳號錢包 |
| 街口支付 | `TPDirect.jkoPay.getPrime` | - | 街口錢包 |
| 悠遊付 | `TPDirect.easyWallet.getPrime` | - | 悠遊卡服務 |
| 一卡通 Money | `TPDirect.iPassMoney.getPrime` | - | 一卡通錢包 |
| Pi 拍錢包 | `TPDirect.piWallet.getPrime` | - | Pi 拍錢包 |
| Plus Pay | `TPDirect.plusPay.getPrime` | - | 中華電信 Hami |
| PXPay Plus | `TPDirect.pxpayplus.getPrime` | - | 全聯 PXPay Plus |
| GoGo Pay | `TPDirect.gogoPay.getPrime` | - | GoGo Pay |
| OPPay | `TPDirect.opPay.getPrime` | - | 中油 OPPay |
| Pay Later（後支付） | `TPDirect.payLater.getPrime` | - | 後支付服務 |
| AFTEE（BNPL） | `TPDirect.aftee.getPrime` | - | 先享後付 |
| 虛擬帳號（ATM） | `TPDirect.virtualAccount.getPrime` | `va_` | ATM / 網銀轉帳 |
| 超商貨到付款 | `TPDirect.cashOnDelivery.getPrime` | `cod_` ⚠️ | COD 物流 |

> 各支付方式於後端 `pay-by-prime` 共用同一端點，但需配對對應的 `merchant_id`。

### Card Funding 對照

| `card_info.funding` | 說明 |
|---------------------|------|
| `0` | Credit 信用卡 |
| `1` | Debit 簽帳金融卡 |
| `2` | Prepaid 預付卡 |
| `-1` | Unknown |

### Card Type 對照

| `card_info.type` | 說明 |
|------------------|------|
| `1` | VISA |
| `2` | MasterCard |
| `3` | JCB |
| `4` | UnionPay |
| `5` | AMEX |

---

## 常見問題排解

### Prime 已過期 / 已被使用

**症狀**：後端 `pay-by-prime` 回 `status: 3` 或 `status: 4`。

**成因**：
- Prime 為**一次性**且效期約 **90 秒**
- 重複呼叫、或商家系統延遲送出（如等待人工審核）

**解法**：
1. 前端取 Prime 後立即送至後端
2. 後端立即呼叫 `pay-by-prime`，避免任何同步等待
3. 若需「審核後扣款」，使用 `delay_capture_in_days` 延遲請款而非延後送 Prime

---

### Apple Pay 按鈕不顯示

**症狀**：`canMakePaymentWithActiveCard` 永遠為 `false`。

**檢查清單**：
1. 是否使用 **Safari**（含 macOS 與 iOS）？
2. 網站是否為 **HTTPS**？（`localhost` 通常需 ngrok）
3. Apple Developer 端是否完成 Domain Verification？
4. TapPay Portal 是否已輸入正確 Apple Merchant ID？
5. 該 Apple ID 是否有可用卡片？（沙箱需綁測試卡）

---

### Google Pay 沙箱無法測試

**症狀**：Google Pay 按鈕顯示，但 `getPrime` 回失敗。

**解法**：
- 沙箱需於 [Google Pay & Wallet Console](https://pay.google.com/business/console) 申請 **Test 環境** Merchant ID
- 帳號須加入 Google Pay Test Card Suite

---

### Backend Notify 收不到

**症狀**：付款完成但商家伺服器未收到 POST。

**檢查清單**：
1. `result_url.backend_notify_url` 是否為 **公網可達** 的 HTTPS？
2. 防火牆 / WAF 是否擋住 TapPay IP？
3. 商家是否回應 `200`？（非 2xx 會讓 TapPay 重送，但若一直失敗會放棄）
4. URL 是否解析錯誤（Trailing slash / 路徑）？

---

### Card Token 失效

**症狀**：`pay-by-token` 回 `status: 10005` 或 `card expired`。

**解法**：
- 提示使用者重新綁卡（再走一次 `pay-by-prime` + `remember: true`）
- 商家應主動偵測信用卡到期日（可從 `card_info` 推算），提前通知換卡

---

### 沙箱與正式金額不一致

**症狀**：沙箱可付 1 元，正式被收單行擋。

**解法**：
- 多數收單行設「最低交易金額」（常見 1–10 元）
- 部分支付方式（如 LINE Pay）有最低 1 元的限制
- 正式上線前向 TapPay / 收單行確認金額區間

---

### Domain not allowed

**症狀**：前端 SDK 載入後 `setupSDK` 拋錯。

**解法**：
- 至 TapPay Portal 「應用程式設定」加入正式網域（含 `www.` 與不含的版本）
- 沙箱不會強制白名單，但仍建議設定

---

### 重複交易（消費者重整頁面）

**解法**：
1. 商家自行產生唯一 `order_number`，記錄到 DB
2. 收到 Notify 時以 `order_number` + `rec_trade_id` 做冪等
3. 前端在送出後立即 disable button + 顯示 loading
4. 嚴格場景使用 Idempotency Key 機制

---

## 官方資源

- **TapPay Portal**：https://portal.tappaysdk.com
- **API 文件**：https://docs.tappaysdk.com
- **SDK Releases**：https://github.com/TapPay/tappay-web-example/releases
- **Web SDK 範例**：https://github.com/TapPay/tappay-web-example
- **iOS / Android SDK**：https://github.com/TapPay
- **技術支援**：support@cherri.tech ⚠️（請以 Portal 公告為準）

---

最後更新：2026/05/07
