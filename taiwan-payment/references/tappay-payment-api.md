# TapPay Payment API Reference

TapPay（拍付國際）金流 API 完整參考文件（繁體中文）。

TapPay 為亞太地區的「支付處理商（Payment Processor）」，介於商家系統與收單行（Acquirer）之間。其核心特色為「兩段式 PCI 隔離架構」：前端 SDK 取得 **Prime Token**（一次性、約 90 秒效期），後端使用 Prime 呼叫 `pay-by-prime` 完成扣款，PAN 完整卡號**永不**經過商家伺服器。

> **資料來源**：[Backend](https://docs.tappaysdk.com/tutorial/zh/back.html)、[Advanced](https://docs.tappaysdk.com/tutorial/zh/advanced.html)、[Reference](https://docs.tappaysdk.com/tutorial/zh/reference.html)、[Error](https://docs.tappaysdk.com/tutorial/zh/error.html)、[Web Frontend](https://docs.tappaysdk.com/tutorial/zh/web/front.html)、各錢包 `docs.tappaysdk.com/<錢包>/zh/web/front.html`，以及 [tappay-web-example](https://github.com/TapPay/tappay-web-example)（2026-11-17 核對）。⚠️ 標示官方文件未公開、無法核對的項目。

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
| **協定** | RESTful HTTPS + JSON，所有後端 API 皆為 HTTP POST |
| **認證** | HTTP Header `x-api-key`（攜帶 Partner Key） |
| **編碼** | UTF-8 |
| **PAN 處理** | 卡號全程託管於 TapPay iframe / Tokenization Vault |
| **Prime 效期** | 一次性、90 秒（Apple Pay 延後授權的 Prime 為 30 天） |
| **Timeout** | 官方建議後端呼叫 timeout 設 30 秒 |
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
| Direct Pay | 消費者於商家頁面輸入信用卡號的交易 |
| 電子支付 | 透過電子錢包帳戶完成的交易（LINE Pay、街口、悠遊付等） |
| Token Pay | 僅指 Apple Pay / Google Pay / Samsung Pay 產生 DPAN 完成的交易 |
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
| 協定 | HTTPS |
| 編碼 | UTF-8 |
| Content-Type | `application/json` |
| HTTP Method | POST（所有後端 API） |
| 認證 Header | `x-api-key: <PARTNER_KEY>` |
| 正式環境 | 後端呼叫的伺服器 IP 須在 Portal 正式環境登錄（否則 `status: 4` IP 不符） |

### 測試卡號（[Test Card](https://docs.tappaysdk.com/tutorial/zh/reference.html#test-card)）

僅適用 Direct Pay 沙箱；有效月年填任一未過期日期即可。

| 卡號 | CCV | 結果 |
|------|-----|------|
| `4242 4242 4242 4242` | 123 | 成功（VISA） |
| `3543 9234 8838 2426` | 123 | 成功（JCB） |
| `3454 5465 4604 563` | 1234 | 成功（AMEX） |
| `5451 4178 2523 0575` | 123 | 成功（MasterCard）；3D 驗證直接授權成功 |
| `6234 5774 3859 4899` | 123 | 成功（UnionPay） |
| `4242 4216 0218 4242` | 123 | `10003` Card Error |
| `4242 4222 0418 4242` | 123 | `10005` Bank System Error |
| `4242 4240 1026 4242` | 123 | `10006` Duplicate Transaction |
| `4242 4276 2229 4242` | 123 | `10013` Bank transaction id duplicate |

- Token Pay（Apple / Google / Samsung Pay）沙箱須用真卡測試，不會實際扣款
- 錢包類沙箱測試方式須洽 TapPay Support
- 沙箱可直接用官方[測試 Prime](https://docs.tappaysdk.com/tutorial/zh/reference.html#test-prime)呼叫 `pay-by-prime`，例：Direct Pay `test_3a2fb2b7e892b914a03c95dd4dd5dc7970c908df67a49527c0a648b2bc9`、LINE Pay `ln_test_utigjeyfutj5867uyjhuty47rythfjru485768tigjfheufhtu5i6ojk`
- KYC 測試：身分證字號 `A123456789`、電話 `0912345678`

### Web SDK 版本

最新版 **v5.26.0**（2026-09-09），各版 SRI hash 見 [Releases](https://github.com/TapPay/tappay-web-example/releases)。

| 版本 | 變更 |
|------|------|
| v5.14.0 起 | 載入路徑改為 `https://js.tappaysdk.com/sdk/tpdirect/<version>`；v5.13.1 以前為 `https://js.tappaysdk.com/tpdirect/<version>` |
| v5.12.3+ | iOS／iPadOS 16+ 的 Chrome、Edge、Firefox 可用 Apple Pay |
| v5.19.1 | 新增超商取貨付款（`cashOnDelivery`） |
| v5.19.2 | Virtual Account（ATM）最低版本 |
| v5.20.0 | 全支付（`pxPayPlus`） |
| v5.21.0 | 一卡通 MONEY（`iPassMoney`）；移除 Atome |
| v5.22.0 | AFTEE |
| v5.24.0 | 大哥付你分期（`oppay`）、Direct Pay 可設定 cardholder 欄位、cardholder prime |
| v5.25.0 | 分期趣（`gogoPay`）、Samsung Pay iframe（`samsungPayIframe`） |
| v5.26.0 | 超商取貨移除 OK 超商 |

---

## API 端點總覽

### 後端核心交易 API

| 功能 | Method | Path |
|------|--------|------|
| **以 Prime 付款** | POST | `/tpc/payment/pay-by-prime` |
| **以 Card Token 付款** | POST | `/tpc/payment/pay-by-token` |
| **交易紀錄查詢（Record）** | POST | `/tpc/transaction/query` |
| **單筆交易歷程（Trade History）** | POST | `/tpc/transaction/trade-history` |
| **退款（Refund）** | POST | `/tpc/transaction/refund` |
| **取消退款（Refund Cancel，僅台新銀行）** | POST | `/tpc/transaction/refund/cancel` |
| **當日請款（Cap Today）** | POST | `/tpc/transaction/cap` |
| **取消請款（Cap Cancel）** | POST | `/tpc/transaction/cap/cancel` |

### 卡片管理 API（[Advanced](https://docs.tappaysdk.com/tutorial/zh/advanced.html)）

| 功能 | Method | Path |
|------|--------|------|
| **綁卡（Bind Card）** | POST | `/tpc/card/bind` |
| **解除卡片綁定（Remove Card）** | POST | `/tpc/card/remove` |
| **卡片資料（Card Metadata，需加購 TSP）** | POST | `/tpc/card/metadata` |

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

官方規格的每個後端 API 除了 Header `x-api-key`，Body 也必填 `partner_key`（同一個值）。沒有另外的簽章欄位。範例：

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
  src="https://js.tappaysdk.com/sdk/tpdirect/v5.26.0"
  type="text/javascript"
  integrity="sha256-TUfo5OAhhvSDiUZgLOC+Qkdg9DPh0WAGx9X9tewAKXs="
  crossorigin="anonymous"></script>
```

> hash 對應 v5.26.0（Release Note 公布值，與實際下載檔案的 SHA-256 一致）。換版本時一併換 hash。

### 2. 不使用 SRI

```html
<script src="https://js.tappaysdk.com/sdk/tpdirect/v5.26.0"
        type="text/javascript"></script>
```

> 設定 Content Security Policy 時，`frame-src` 需允許 `js.tappaysdk.com` 與 `fraud.tappaysdk.com`。

### 3. 初始化

```js
TPDirect.setupSDK(
  12345,                    // APP_ID
  "app_xxxxxxxxxxxxxxxx",   // APP_KEY
  "sandbox"                 // 'sandbox' 或 'production'
);
```

### 4. Prime 回應結構

`TPDirect.card.getPrime` 回傳（[Get Prime](https://docs.tappaysdk.com/tutorial/zh/web/front.html#get-prime)）：

| 欄位 | 類型 | 說明 |
|------|------|------|
| `status` | Integer | `0` 表示成功，其他為錯誤 |
| `msg` | String | 訊息 |
| `card.prime` | String | Prime |
| `card.bincode` | String | 卡號前 6 碼（開通 8 碼 BIN 付費功能者可能為 8 碼） |
| `card.lastfour` | String | 卡號末 4 碼 |
| `card.issuer` / `card.issuer_zh_tw` / `card.bank_id` | String | 發卡行英文名 / 中文名 / 代碼 |
| `card.funding` | Integer | `0`:Credit `1`:Debit `2`:Prepaid `-1`:Unknown |
| `card.type` | Integer | `1`:VISA `2`:MasterCard `3`:JCB `4`:UnionPay `5`:AMEX `-1`:Unknown |
| `card.level` / `card.country` / `card.countrycode` | String | 卡片等級 / 發卡國 / 國碼 |
| `clientip` | String | 交易者 IP |
| `card_identifier` | String | 信用卡識別碼（一卡一碼） |

錢包類 `getPrime` 回傳 `{ status, msg, prime, clientip }`，Prime 在 `result.prime`。

---

## Prime 取得流程（Direct Pay iframe）

「Direct Pay iframe」將整張刷卡表單（卡號、到期日、CCV）以單一 iframe（card view）嵌入商家頁面，依 [Direct_Pay_iframe 範例](https://github.com/TapPay/tappay-web-example/tree/master/Direct_Pay_iframe)。

### Step 1：放置容器

```html
<div id="cardview-container"></div>
<button id="submit-btn" type="button" disabled>付款</button>
```

### Step 2：掛載 iframe

`TPDirect.card.setup(selector, style, config)`：第一參數是單一容器，第二參數是 card view 樣式，第三參數選填。

```js
TPDirect.card.setup('#cardview-container', {
  color: 'rgb(0,0,0)',
  fontSize: '15px',
  lineHeight: '24px',
  fontWeight: '300',
  errorColor: 'red',
  placeholderColor: ''
}, {
  isUsedCcv: false,               // 不帶第三參數時 CCV 為必填
  isMaskCreditCardNumber: true,
  maskCreditCardNumberRange: { beginIndex: 6, endIndex: 11 }
});
```

### Step 3：監聽欄位狀態

```js
TPDirect.card.onUpdate(function (update) {
  // update.canGetPrime  → boolean
  // update.hasError     → boolean
  // update.status.number / .expiry / .ccv：
  //   0 已填好且正確 / 1 尚未填寫 / 2 有錯誤 / 3 輸入中
  document.getElementById('submit-btn').disabled = !update.canGetPrime;
});
```

狀態碼見 [Status Code](https://docs.tappaysdk.com/tutorial/zh/reference.html#status-code)。

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

- iframe 內部無法執行商家 JS，自訂錯誤訊息需在外層監聽 `onUpdate`
- 卡號遮罩（`isMaskCreditCardNumber`）僅顯示遮罩，實際卡號仍由 TapPay 處理

---

## Prime 取得流程（TapPay Fields）

官方文件主推的 Direct Pay 整合方式（[TapPay Fields](https://docs.tappaysdk.com/tutorial/zh/web/front.html#tappay-fields)）：卡號、到期日、CCV 各自是獨立 iframe，版型由商家完全控制。

### 範例

```html
<div class="tpfield" id="card-number"></div>
<div class="tpfield" id="card-expiration-date"></div>
<div class="tpfield" id="card-ccv"></div>
```

```js
TPDirect.card.setup({
  fields: {
    number:         { element: '#card-number', placeholder: '**** **** **** ****' },
    expirationDate: { element: document.getElementById('card-expiration-date'), placeholder: 'MM / YY' },
    ccv:            { element: '#card-ccv', placeholder: 'ccv' }   // 選填；不設定就不顯示也不驗證 CCV
  },
  styles: {
    'input':    { 'color': 'gray' },
    ':focus':   { 'color': 'black' },
    '.valid':   { 'color': 'green' },
    '.invalid': { 'color': 'red' }
  },
  isMaskCreditCardNumber: true,
  maskCreditCardNumberRange: { beginIndex: 6, endIndex: 11 }
});
```

- `onUpdate` 的 callback 另含 `cardType`（`mastercard`、`visa`、`jcb`、`amex`、`unionpay`、`unknown`）；狀態碼同上
- `TPDirect.card.getTappayFieldsStatus()` 可主動取得與 `onUpdate` 相同的狀態物件
- 欄位 focus 時容器會加上 `tappay-field-focus` class
- `fields` 另可設定 `cardholder`（`name_en`、`email`、`phone.country_code`、`phone.number`），讓持卡人資料隨 Prime 送出（v5.24.0+）

### 相關前端 API

| API | 用途 |
|-----|------|
| `TPDirect.ccv.setup` / `TPDirect.ccv.setupCardType` / `TPDirect.ccv.getPrime` | 取得 `ccv_prime`，帶入 `pay-by-token` 讓銀行驗 CCV 而不經手明碼（90 秒效期） |
| `TPDirect.cardholder.setup` / `TPDirect.cardholder.getPrime` | 取得持卡人資料 Prime，帶入 `pay-by-token` 的 `cardholderinfo_prime` |
| `TPDirect.getDeviceId()` | 使用 TapPay RBA 風險評估時取得 `device_id` |

> **適用情境**：UI/UX 嚴格要求自訂排版（例如卡號分段顯示、響應式表單）；商家可承擔較複雜的 CSS 維護成本。

---

## Prime 取得流程（Apple Pay）

Apple Pay on the Web 透過 `TPDirect.paymentRequestApi` 整合（[Apple Pay on the Web](https://docs.tappaysdk.com/apple-pay/zh/front.html#apple-pay-on-the-web)）。需 iOS 10+ 或 macOS Sierra (10.12)+。

### 前置作業

1. Apple Developer 取得 **Apple Merchant ID**（如 `merchant.com.example.shop`）；若使用 TapPay 的「Apple Pay on the Web 商家申請服務」，改用 Portal > 支付方式 > Apple Pay > Apple Pay on the Web 顯示的 merchant identifier
2. 上傳 Domain Verification 檔案到網站根目錄 `/.well-known/apple-developer-merchantid-domain-association`
3. 所有含 Apple Pay 的頁面都必須是 **HTTPS**（測試環境亦同）且有合法 SSL 憑證
4. 伺服器須支援 TLS 1.2，並允許 Apple Pay 閘道 IP 經 443 port 連入（清單見官方 Requirements）

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
  if (!result.browserSupportPaymentRequest) return;
  if (!result.canMakePaymentWithActiveCard) return;
  document.getElementById('apple-pay-btn').addEventListener('click', () => {
    TPDirect.paymentRequestApi.getPrime(function (r) {
      if (r.status !== 0) return;
      const prime = r.prime;
      // r.total_amount（含運費）、r.payer、r.shippingAddress、r.billingAddress
      // ➡️ 送到後端 pay-by-prime
    });
  });
});
```

### Apple Pay 限制

- Safari（macOS Sierra+／iOS 10+）皆可；iOS／iPadOS 16+ 搭配 Web SDK v5.12.3+ 時，Chrome、Edge、Firefox 也可用（[Web SDK compatibility](https://docs.tappaysdk.com/tutorial/zh/reference.html#web-sdk-compatibility)）
- 需 HTTPS（本機開發可用 ngrok）
- 後端一樣呼叫 `pay-by-prime`；Apple Pay 屬 Token Pay，不支援 `remember`

---

## Prime 取得流程（Google Pay）

依 [Google Pay on the Web](https://docs.tappaysdk.com/google-pay/zh/front.html#google-pay-on-the-web)。

### Step 1：載入 SDK

```html
<script src="https://pay.google.com/gp/p/js/pay.js"></script>
<script src="https://js.tappaysdk.com/sdk/tpdirect/v5.26.0"></script>
```

### Step 2：初始化

```js
TPDirect.setupSDK(APP_ID, "APP_KEY", "sandbox");

TPDirect.googlePay.setupGooglePay({
  googleMerchantId: 'merchant_id_from_google',   // sandbox 可省略，production 必填
  allowedCardAuthMethods: ['PAN_ONLY', 'CRYPTOGRAM_3DS'],
  merchantName: 'ExampleShop'
  // 選填：emailRequired、shippingAddressRequired、billingAddressRequired、
  //       billingAddressFormat、allowPrepaidCards、allowedCountryCodes、phoneNumberRequired
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

### Step 4：（可選）更新金額

`setupPaymentRequest` 已帶金額時不需要；否則在 getPrime 之前設定：

```js
TPDirect.googlePay.setupTransactionPrice({
  price: '299',
  currency: 'TWD'
});
```

### Step 5：不使用官方按鈕時

```js
TPDirect.googlePay.getPrime(function (err, prime, result) {
  // err: { status, msg, originalError }
  // result: { client_ip, card_info, merchant_reference_info }
});
```

### Google Pay 限制

- 需 HTTPS，並符合 Google 的 [mobile web setup](https://developers.google.com/payments/mobile-web-setup) 要求
- 瀏覽器支援見 [Web SDK compatibility](https://docs.tappaysdk.com/tutorial/zh/reference.html#web-sdk-compatibility)（例：iOS Safari 只支援真實卡號，不支援代碼化卡號）
- 沙箱：代碼化卡號（Token Pay）交易須用真卡測試，不會實際扣款；後端串接可先用測試 Prime `gp_test_...`

---

## Prime 取得流程（LINE Pay / JKO Pay）

各錢包文件在 `docs.tappaysdk.com/<錢包>/zh/web/front.html`。callback 參數有兩種形式，照官方寫法：

```js
// callback(result)：LINE Pay、街口、一卡通 MONEY、全支付、AFTEE、大哥付你分期、分期趣
TPDirect.linePay.getPrime(function (result) {
  // result = { status, msg, prime, clientip }
});
TPDirect.jkoPay.getPrime(function (result) { /* ... */ });
TPDirect.iPassMoney.getPrime(function (result) { /* ... */ });
TPDirect.pxPayPlus.getPrime(function (result) { /* ... */ });   // 注意大小寫：pxPayPlus
TPDirect.aftee.getPrime(function (result) { /* ... */ });
TPDirect.oppay.getPrime(function (result) { /* ... */ });       // 大哥付你分期（OP Pay）
TPDirect.gogoPay.getPrime(function (result) { /* ... */ });     // 分期趣

// callback(error, result)：悠遊付、Pi 拍錢包、全盈支付
TPDirect.easyWallet.getPrime(function (error, result) { /* ... */ });
TPDirect.piWallet.getPrime(function (error, result) { /* ... */ });
TPDirect.plusPay.getPrime(function (error, result) { /* ... */ });
```

後端回傳 `payment_url` 後，前端以 `TPDirect.redirect(payment_url)` 導轉。

### 後端調用差異

電子支付的 `pay-by-prime` 必須提供 `result_url`（前後端各一）；LINE Pay、全支付、AFTEE、大哥付你分期、分期趣的 `details` 為必填（[E-Payment support list](https://docs.tappaysdk.com/tutorial/zh/reference.html#e-payment-support-list)）：

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

`pay-by-prime` 回應會回傳 `payment_url`，商家須將消費者導向該 URL，於錢包完成付款後再回到 `frontend_redirect_url`。

### 錢包功能差異（節錄）

| 錢包 | 綁定扣款（`remember`） | `bank_member_id` |
|------|-----------------------|------------------|
| LINE Pay | 支援 | — |
| 全支付 | 支援 | 綁定交易必填 |
| 一卡通 MONEY | 支援 | 綁定交易必填 |
| 街口、悠遊付、Pi 拍錢包、全盈支付、AFTEE、大哥付你分期、分期趣 | 不支援 | 悠遊付、全盈支付綁定交易必填 |

> 悠遊付、全盈支付雖不支援 `remember`，但官方列為支援「綁定授權」交易類型，流程見各錢包文件。

---

## Prime 取得流程（Virtual Account 虛擬帳號）

ATM 虛擬帳號採非同步入帳。docs.tappaysdk.com 沒有 Virtual Account 專頁，以下依 [Virtual_Account 範例](https://github.com/TapPay/tappay-web-example/tree/master/Virtual_Account)（需 Web SDK v5.19.2+）。

### 前端取 Prime

```html
<script src="https://js.tappaysdk.com/sdk/tpdirect/v5.26.0"></script>
```

```js
TPDirect.setupSDK(APP_ID, "APP_KEY", "sandbox");

TPDirect.virtualAccount.getPrime(function (error, result) {
  if (error || result.status !== 0) {
    console.error(error || result.msg);
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

### 回應 ⚠️

官方未公開 Virtual Account 的回應欄位（虛擬帳號、銀行代碼、繳費期限的欄位名）。`status: 0` 只代表取號成功，實際入帳以 Backend Notify 或 Record API 查詢為準；正式串接前向 TapPay 索取規格。

### 超商取貨付款（Cash On Delivery）

依 [Cash_On_Delivery 範例](https://github.com/TapPay/tappay-web-example/tree/master/Cash_On_Delivery)（v5.19.1+；v5.26.0 移除 OK 超商）：`TPDirect.cashOnDelivery.setShipType(shipType, callback)` 設定物流通路、`TPDirect.cashOnDelivery.getStoreId(callback)` 取門市、`TPDirect.cashOnDelivery.getPrime(callback)` 取 Prime（`cd_` 開頭），再送 `pay-by-prime`。

---

## 訂單建立（Pay by Prime）

最核心的後端 API，用於消費 Prime Token 完成扣款（[Pay by Prime API](https://docs.tappaysdk.com/tutorial/zh/back.html#pay-by-prime-api)）。每個 Prime 只能用一次。

### 端點

```
POST {base_url}/tpc/payment/pay-by-prime
Headers:
  Content-Type: application/json
  x-api-key:    <PARTNER_KEY>
```

### 請求參數

#### 必填欄位

| 欄位 | 類型 | 說明 |
|------|------|------|
| `prime` | String(71) | 前端取得的 Prime |
| `partner_key` | String(64) | Partner Key（與 Header 相同） |
| `merchant_id` | String(50) | 對應該支付方式的 Merchant ID；也可改帶 `merchant_group_id`（兩者不可同時使用） |
| `amount` | int | 金額。TWD 為整數元（1–20,000,000）；HKD／MYR／USD 需乘以 100 後帶入（1.01 → `101`） |
| `cardholder` | Object | 持卡人資料，非必填子欄位可帶空字串 |

`details`（String(100)）官方未標必填，但部分收單行與 LINE Pay、全支付、AFTEE、大哥付你分期、分期趣為必填，未帶會交易失敗；實務上一律帶。

#### `cardholder` 物件

| 欄位 | 必填 | 類型 | 說明 |
|------|------|------|------|
| `phone_number` | ● | String(16) | 符合 E.164；3D 風險驗證欄位 |
| `name` | ● | String(40) | 姓名 |
| `email` | ● | String(40) | 符合 RFC 5322，不符合時轉送預設值；3D 風險驗證欄位 |
| `phone_number_country_code` | ○ | String(3) | 國碼，預設 `886`，不可帶 `+` |
| `name_en` | ○ | String(45) | 英文姓名 |
| `zip_code` | ○ | String(40) | 郵遞區號 |
| `address` | ○ | String(90) | 地址 |
| `national_id` | ○ | String(40) | 身分證字號 |
| `member_id` | ○ | String(64) | 商家會員編號（詐欺檢測用，僅 Direct Pay） |
| `bank_member_id` | ○ | String(50) | 與銀行／錢包約定的消費者編號；電子錢包綁定扣款時必填 |

#### 常用選填欄位

| 欄位 | 類型 | 說明 |
|------|------|------|
| `currency` | String(3) | ISO 4217 幣別（`TWD`、`HKD`、`MYR`、`USD`） |
| `order_number` | String(50) | 商家自訂訂單編號，可重複；有帶就不能是空字串 |
| `bank_transaction_id` | String(40) | 送銀行的訂單編號，不可與之前重複。官方強烈建議自訂：未自訂時若遇 `421` Gateway 逾時就無法反查該筆交易 |
| `three_domain_secure` | Boolean | 3D 驗證，預設 `false`；僅 Direct Pay |
| `result_url` | Object | 電子支付與 Direct Pay 3D 交易必填 |
| `remember` | Boolean | `true` 時回傳 `card_secret`；僅 Direct Pay 與部分電子錢包 |
| `instalment` | int(2) | 分期期數，預設 `0`；僅 Direct Pay |
| `delay_capture_in_days` | int | 授權後幾天請款，預設 `0`（當天），最多 7 天；`-1` 為不自動請款（改用 Cap Today 手動請款） |
| `redeem` | Boolean | 紅利折抵；僅聯合信用卡處理中心、Direct Pay |
| `cardholder_verify` | Object | 身分驗證（KYC）：`{ "phone_number": true, "national_id": true }`；僅 Direct Pay，支援收單見官方表 |
| `kyc_verification_merchant_id` | String | 兩段式身分驗證時，填只做驗證的 merchant ID |
| `additional_data` | JSONString(3000) | 加密保存的自訂資料 |
| `product_image_url` | String(500) | 付款頁顯示的商品／商家圖片 |
| `store_id` / `store_name` | String(10) / String(50) | 特店門市店號／名稱（收單支援時轉送） |
| `jko_pay_insurance_policy` | StringArray | 街口產壽險交易保單明細 |
| `extra_info` | JSONObject | 額外交易資訊；航空業商戶帶 `airline_info`，見下方。僅 Direct Pay、Apple Pay、Google Pay、Samsung Pay |

#### `result_url` 物件

| 欄位 | 說明 |
|------|------|
| `frontend_redirect_url` | String(500)，`https` 開頭；交易完成後導回的前台網址 |
| `backend_notify_url` | String(500)，`https` 開頭且**僅支援 443 port**；交易結果通知網址 |
| `go_back_url` | String(500)，3D 交易中消費者被導到 TapPay 錯誤頁時「Go back」按鈕的網址（玉山、國泰世華、台新），官方強烈建議 3D 交易時設定 |

3D 交易建議：收到 frontend redirect 後、顯示結果頁前，以 `rec_trade_id` 呼叫 Record API 反查狀態。

#### `extra_info.airline_info`（航空交易）

航空業商戶授權時帶入機票交易資訊，TapPay 轉送收單機構；目前只支援聯合信用卡處理中心。Pay by Prime 支援 Direct Pay、Apple Pay、Google Pay、Samsung Pay；Pay by Card Token 只支援 Direct Pay。來源：[Backend](https://docs.tappaysdk.com/tutorial/zh/back.html)、[Reference](https://docs.tappaysdk.com/tutorial/zh/reference.html)。

| 欄位 | 類型 | 說明 |
|------|------|------|
| `is_air_ticket_transaction` | Boolean | `true` 機票交易；`false` 非機票的航空相關交易（行李費、免稅品、升等）；不帶表示非航空業交易 |
| `departure_airport_code` | String(5) | 出發地機場代碼，例 `TPE`；非旅遊類交易帶非旅遊代碼 |
| `destination_airport_code` | String(5) | 目的地機場代碼，例 `NRT`；非旅遊類交易帶與出發地相同的非旅遊代碼 |
| `flight_number` | String(5) | 只填數字、前面補 0 到 5 碼，例 JL96 帶 `00096` |

非旅遊代碼：`XUP` 升等、`XAF` 貴賓室／會費、`XCA` 貨運、`XOT` 旅遊訂單、`XDF` 免稅品、`XAE` 行李費、`XAO` 預付票、`XAA` 雜項費用、`XTD` 遞送、`XPC` 寵物運送、`XPE` 重開票、`777` 周邊商品（`flight_number` 可不帶）。

- TapPay 只檢查型態與長度（錯誤碼 `10062`–`10065`），不檢查代碼是否有效與欄位連動；空字串視為通過並原樣送出。
- 收單機構依業務規則拒絕（例如 NCCC 回 963）時，TapPay 回 `status = 10023`，原始代碼與訊息在 `bank_result_code` / `bank_result_msg`。

```json
"extra_info": {
  "airline_info": {
    "is_air_ticket_transaction": true,
    "departure_airport_code": "TPE",
    "destination_airport_code": "NRT",
    "flight_number": "00096"
  }
}
```

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
| `rec_trade_id` | String(20) | TapPay 交易編號（**重要**，後續退款 / 查詢使用） |
| `bank_transaction_id` | String(40) | 送銀行的訂單編號 |
| `bank_order_number` | String | 收單行授權時回傳的訂單編號 |
| `auth_code` | String(6) | 銀行授權碼（僅 Direct Pay、Token Pay） |
| `card_secret` | Object | `card_token` + `card_key`（`remember=true` 時） |
| `card_info` | Object | 卡片資訊（僅 Direct Pay、Token Pay） |
| `card_identifier` | String | 信用卡識別碼（一卡一碼） |
| `transaction_time_millis` | long | 交易時間（毫秒） |
| `bank_transaction_time` | Object | 銀行處理時間 |
| `bank_result_code` / `bank_result_msg` | String | 銀行回傳的結果代碼／訊息 |
| `payment_url` | String | 付款頁網址，回傳前端跳轉（Apple / Google / Samsung Pay 不回傳） |
| `acquirer` | String | 收單銀行 / 金流處理器 |
| `amount` | int | 金額（非 TWD 為乘以 100 後的值） |
| `currency` | String(3) | 幣別 |
| `order_number` | String(50) | 商家訂單編號 |
| `instalment_info` | Object | 非 3D 分期交易時回傳（期數、首期、每期金額） |
| `redeem_info` | Object | 非 3D 紅利折抵交易時回傳 |
| `transaction_method_details` | Object | 實際以 3D（`THREE_DOMAIN_SECURE`）或一般授權（`FRICTIONLESS`）送銀行 |

### `card_secret` 內容

當 `remember: true` 時：

| 欄位 | 說明 |
|------|------|
| `card_token` | String(67)，卡片識別字串（用於 `pay-by-token`） |
| `card_key` | String(64)，卡片安全金鑰（須一併保存） |

不支援 `remember` 的支付方式：Apple Pay、Google Pay、Samsung Pay、街口、悠遊付、Pi 拍錢包、全盈支付。

> **安全建議**：`card_token` 與 `card_key` 必須加密儲存於商家資料庫，且僅後端可存取。

### `card_info` 內容

| 欄位 | 說明 |
|------|------|
| `bin_code` | 卡號前 6 碼（開通 8 碼 BIN 付費功能者可能為 8 碼） |
| `last_four` | 卡號末 4 碼 |
| `issuer` / `issuer_zh_tw` / `bank_id` | 發卡銀行英文名 / 中文名 / 代碼 |
| `funding` | `0`:Credit `1`:Debit `2`:Prepaid `-1`:Unknown |
| `type` | `1`:VISA `2`:MasterCard `3`:JCB `4`:UnionPay `5`:AMEX `-1`:Unknown |
| `level` | 卡片等級 |
| `country` / `country_code` | 發卡行國家 / 國家碼 |
| `expiry_date` | 卡片到期 `YYYYMM`；僅 Direct Pay 且 `remember=true` 時回傳 |

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
| `partner_key` | ● | String(64) | Partner Key |
| `card_key` | ● | String(64) | 從 `card_secret.card_key` 取得 |
| `card_token` | ● | String(67) | 從 `card_secret.card_token` 取得 |
| `merchant_id` | ● | String(50) | Merchant ID（或改帶 `merchant_group_id`） |
| `amount` | ● | int | 金額（規則同 pay-by-prime） |
| `currency` | ● | String(3) | 幣別，**必填**（如 `TWD`） |
| `details` | ○ | String(100) | 商品描述；部分收單必填，實務上一律帶 |
| `order_number` | ○ | String(50) | 商家訂單編號 |
| `bank_transaction_id` | ○ | String(40) | 送銀行的訂單編號（建議自訂） |
| `cardholder` | ○ | Object | 持卡人資料；有帶時 `phone_number`、`email` 必填 |
| `three_domain_secure` | ○ | Boolean | 3D 驗證；`true` 時須帶 `result_url` |
| `result_url` | ○ | Object | 3D 交易必填 |
| `delay_capture_in_days` | ○ | int | 規則同 pay-by-prime |
| `ccv_prime` / `card_ccv` | ○ | String | 讓銀行驗 CCV；兩者擇一，`ccv_prime` 由 `TPDirect.ccv.getPrime` 取得（90 秒） |
| `is_merchant_initiated_transaction` | ○ | Boolean | `true` = 商店發起（訂閱、定期定額），預設 `false` |
| `cardholderinfo_prime` | ○ | String | `TPDirect.cardholder.getPrime` 取得的持卡人資料 Prime |
| `device_id` | ○ | String(64) | 使用 TapPay RBA 時帶入 `TPDirect.getDeviceId()` 的值 |
| `extra_info` | ○ | JSONObject | 航空交易資訊 `airline_info`，規則同 pay-by-prime；僅 Direct Pay |

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

回應結構與 `pay-by-prime` 大致相同（不含 `card_secret`）；有帶持卡人資料更新時另回 `update_cardholderinfo_result`（遮罩後的持卡人資料）。

### 注意事項

- 卡片過期回 `status: 2013`；token 不存在或不合法回 `2011`；card key 錯誤回 `2012`，須引導使用者重新綁卡
- `card_token` 與 `card_key` 配對使用，遺失任一者都無法扣款
- 不建議將 `pay-by-token` 暴露在前端任何邏輯中

---

## 付款通知（Backend Notify）

電子支付與 Direct Pay 3D 交易完成後，TapPay 以 POST 將結果送至 `result_url.backend_notify_url`（[Backend Notify](https://docs.tappaysdk.com/tutorial/zh/back.html#backend-notify)）。

### 通知特性

| 項目 | 說明 |
|------|------|
| HTTP Method | POST |
| Content-Type | `application/json` |
| 簽章 | 官方文件未定義簽章欄位；真實性以 Record API 反查 |
| 重試機制 | 商家未回 HTTP `200` 時，於 1、2、4、8、16 分鐘後重送，最多 5 次；全部失敗會寄信到聯絡人及技術聯絡人信箱 |

### 通知欄位

| 欄位 | 說明 |
|------|------|
| `status` / `msg` | `0` 為成功 |
| `rec_trade_id` | TapPay 交易編號 |
| `bank_transaction_id` / `bank_order_number` | 送銀行的訂單編號 / 收單回傳的訂單編號 |
| `order_number` | 商家訂單編號 |
| `amount` | 金額 |
| `acquirer` | 收單行 |
| `transaction_time_millis` | 交易時間（毫秒） |
| `transaction_complete_millis` | 交易完成時間（僅玉山、國泰收單） |
| `auth_code` | 授權碼（僅 Direct Pay、Token Pay） |
| `card_identifier` | 信用卡識別碼 |
| `bank_result_code` / `bank_result_msg` | 銀行回應碼 / 訊息 |
| `pay_info` | 電子支付專屬：`method`（`CREDIT_CARD`、`BALANCE`、`POINT`、`DISCOUNT`、`ACCOUNT_LINK`、`CREDIT_BNPL`）、`masked_credit_card_number`、`credit_card`、`balance`、`bank_account`、`point`、`discount` 等 |
| `e_invoice_carrier` | 電子發票載具（僅街口、全盈支付） |
| `instalment_info` / `redeem_info` | 分期 / 紅利資訊（僅 Direct Pay） |

### Frontend Redirect

導回 `frontend_redirect_url` 時以 query string 帶 `rec_trade_id`、`order_number`、`bank_transaction_id`、`status`。這些參數可能被偽造，只能用來顯示，狀態以 Backend Notify 或 Record API 為準。

### 商家應回應

回 HTTP `200` 即可。

### 驗證真實性

1. **以 Record API 反查**：用 `rec_trade_id` 查 `record_status` 與 `amount`，官方建議 notify 失敗或顯示結果前都反查
2. **比對 `amount`**：與訂單金額相符
3. **冪等處理**：以 `rec_trade_id` 作為唯一鍵，避免重複處理

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

[Refund API](https://docs.tappaysdk.com/tutorial/zh/back.html#refund-api) 會同時處理取消授權與取消請款。呼叫後 TapPay 當日向銀行送退款，不代表當日成功；隔天以 Portal 或 Record API 確認。

### 端點

```
POST {base_url}/tpc/transaction/refund
```

### 請求參數

| 欄位 | 必填 | 類型 | 說明 |
|------|------|------|------|
| `partner_key` | ● | String(64) | Partner Key |
| `rec_trade_id` | ● | String(20) | 原交易 `rec_trade_id` |
| `amount` | ○ | int | 退款金額，**省略時全額退款**；外幣乘以 100（`100` 代表 1.00） |
| `bank_refund_id` | ○ | String(20) | 商家自訂退款識別碼（半形英數，不可重複） |
| `additional_data` | ○ | JSONString(3000) | 加密保存的自訂資料 |
| `merchandise_details` | ○ | Object | 不適用回饋的商品金額（部分電子支付） |

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
| `refund_id` | 退款紀錄識別碼 |
| `bank_refund_order_number` | 收單回傳的退款編號 |
| `refund_amount` | 此次退款金額 |
| `refund_info` | 電子支付返還的點數／現金（部分錢包） |
| `is_captured` | 原交易是否已請款 |
| `bank_result_code` / `bank_result_msg` | 銀行回應碼 / 訊息 |
| `currency` | 幣別 |

### 退款規則

- **全額退款**：未請款也可執行
- **部分退款**：須等銀行**請款成功**後才能執行（[Partial Refund](https://docs.tappaysdk.com/tutorial/zh/reference.html#partial-refund)）；分期交易不支援部分退款
- 若收單行在請款中不支援取消授權，需等 TapPay 收到銀行回覆後才能退款；`status: 92` 表示該收單不支援非同日取消授權，須等請款後再退款
- **退款處理時間**：各銀行不同，見 [Each bank refund time](https://docs.tappaysdk.com/tutorial/zh/reference.html#each-bank-refund-time)

### 請款相關 API（[Advanced](https://docs.tappaysdk.com/tutorial/zh/advanced.html)）

| API | 路徑 | 用途 |
|-----|------|------|
| Cap Today | `/tpc/transaction/cap` | 讓延遲請款（或 `delay_capture_in_days: -1`）的交易當天請款；Body：`partner_key`、`rec_trade_id`；回 `cap_millis` |
| Cap Cancel | `/tpc/transaction/cap/cancel` | 在送銀行批次請款前取消請款；Body：`partner_key`、`rec_trade_id` |
| Refund Cancel | `/tpc/transaction/refund/cancel` | 在銀行當天批次前取消退款，**僅台新銀行**；Body：`partner_key`、`rec_trade_id`、`refund_id` |

---

## 訂單查詢（Transaction Query）

### 端點

```
POST {base_url}/tpc/transaction/query
```

### 請求參數

| 欄位 | 必填 | 類型 | 說明 |
|------|------|------|------|
| `partner_key` | ● | String(64) | Partner Key |
| `records_per_page` | ○ | int | 每頁筆數（預設 50，最大 200） |
| `page` | ○ | int | 頁碼，從 `0` 開始 |
| `filters` | ○ | Object | 過濾條件；`time` 為必帶 |
| `order_by` | ○ | Object | 排序，預設 `{ "attribute": "time", "is_descending": true }` |

### `filters` 物件（[filters](https://docs.tappaysdk.com/tutorial/zh/reference.html#filters)）

| 欄位 | 類型 | 說明 |
|------|------|------|
| `time` | Object | **必帶**。`{ "start_time": <ms>, "end_time": <ms> }`，區間最多 90 天 |
| `amount` | Object | `{ "upper_limit": 10000, "lower_limit": 100 }`；外幣乘以 100 |
| `cardholder` | Object | `{ "phone_number", "name", "email" }` |
| `merchant_id` | String array | Merchant ID 列表 |
| `record_status` | int | 交易狀態（見下表） |
| `rec_trade_id` | String(20) | 交易編號 |
| `order_number` | String | 商家訂單編號 |
| `bank_transaction_id` | String | 送銀行的訂單編號 |
| `auth_code` / `currency` / `tsp` / `card_identifier` | — | 其他條件 |

### `order_by` 物件

| 欄位 | 類型 | 說明 |
|------|------|------|
| `attribute` | String | `time` 或 `amount` |
| `is_descending` | Boolean | 是否倒序 |

### 請求範例

```bash
curl -X POST https://sandbox.tappaysdk.com/tpc/transaction/query \
  -H 'content-type: application/json' \
  -H 'x-api-key: <PARTNER_KEY>' \
  -d '{
    "partner_key": "<PARTNER_KEY>",
    "filters": {
      "time": { "start_time": 1777564800000, "end_time": 1778169600000 },
      "order_number": "ORD20260507001"
    }
  }'
```

### 回應結構

| 欄位 | 說明 |
|------|------|
| `status` | `0` 成功；`2` 代表在目前條件下已無更多紀錄 |
| `msg` | 訊息 |
| `records_per_page` / `page` | 每頁筆數 / 頁碼 |
| `total_page_count` | 總頁數（頁碼從 0 起算） |
| `number_of_transactions` | 符合條件總筆數 |
| `trade_records` | 交易陣列 |

#### `trade_records` 中每筆（[trade_records](https://docs.tappaysdk.com/tutorial/zh/reference.html#trade_records)，節錄）

| 欄位 | 說明 |
|------|------|
| `record_status` | 交易狀態（見下表） |
| `rec_trade_id` | TapPay 交易編號 |
| `merchant_id` / `merchant_name` / `app_name` | 商家與 App |
| `time` | 交易時間（毫秒） |
| `amount` | 交易金額（會因退款而減少） |
| `original_amount` | 原始交易金額 |
| `refunded_amount` | 已退款金額 |
| `is_captured` / `cap_millis` | 是否已請款 / 請款時間 |
| `currency` | 幣別 |
| `order_number` | 商家訂單編號 |
| `bank_transaction_id` / `bank_order_number` | 送銀行的訂單編號 / 收單回傳的訂單編號 |
| `auth_code` | 授權碼 |
| `payment_method` | `direct_pay`、`apple_pay`、`google_pay_token`、`google_pay_fpan`、`samsung_pay`、`line_pay`、`tsp_token`、`jko_pay`、`easy_wallet`、`pi_wallet`、`plus_pay`、`px_pay_plus`、`ipass_money`、`aftee`、`op_pay`、`gogo_pay` |
| `partial_card_number` | 卡號前六後四 |
| `cardholder` / `card_info` / `pay_info` | 持卡人 / 卡片 / 電子支付資訊 |
| `three_domain_secure` / `pay_by_instalment` / `pay_by_redeem` | 交易類型旗標 |
| `bank_result_code` / `bank_result_msg` | 銀行回應碼 / 訊息 |

### `record_status` 狀態碼（[record_status](https://docs.tappaysdk.com/tutorial/zh/reference.html#record_status)）

| 代碼 | 狀態 | 說明 |
|------|------|------|
| `-1` | ERROR | 交易錯誤 |
| `0` | AUTH | 銀行已授權，尚未請款 |
| `1` | OK | 交易完成 |
| `2` | PARTIALREFUNDED | 部分退款 |
| `3` | REFUNDED | 完全退款 |
| `4` | PENDING | 待付款 |
| `5` | CANCEL | 取消交易 |

單筆交易的完整歷程（授權、請款、退款各步驟）用 Trade History API：`POST /tpc/transaction/trade-history`，Body `partner_key`、`rec_trade_id`。

---

## 錯誤代碼

TapPay 錯誤訊息分為兩類：

1. **TapPay `status`**：TapPay 平台層級狀態碼
2. **`bank_result_code`**：來自收單行 / 發卡行的轉發碼

### 一般 status（節錄）

> 依 [Error](https://docs.tappaysdk.com/tutorial/zh/error.html#api-error-code) 頁（2026-11-17 核對）。
> 同一代碼在不同 API 可能有不同意義；完整清單見 `data/error-codes-tappay.csv`（473 個代碼）。

| 代碼 | 官方說明 |
|------|----------|
| `0` | 成功 |
| `2` | 查詢結束（Record API 無更多紀錄） |
| `4` | IP 不符（伺服器 IP 未在 Portal 登錄） |
| `5` | JSON 格式錯誤 |
| `80` | 不合法的 x-api-key 或 app key |
| `91` | Prime 過期 |
| `92` | 此收單不支援非同日交易取消授權（須等請款後再退款） |
| `121` | 參數錯誤：prime |
| `421` | Gateway 操作逾時（以自訂的 `bank_transaction_id` 反查） |
| `2011` | 卡片不存在，非法 token |
| `2012` | Card key 錯誤 |
| `2013` | 卡片過期 |
| `10003` | 卡片錯誤，請洽詢發卡行 |
| `10005` | 銀行系統逾時 |
| `10006` | 重複交易 |
| `10013` | Bank transaction id 重複 |

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

### Web SDK 錯誤碼（[Web SDK Error Code](https://docs.tappaysdk.com/tutorial/zh/error.html#web-sdk-error-code)，節錄）

| `result.status` | 說明 |
|-----------------|------|
| `0` | 成功 |
| `-1` | Web SDK 重複載入兩次 |
| `-3` | 網路異常，無法 Get Prime |
| `-5` | 參數缺漏（詳見 `msg`） |
| `-6` / `-7` / `-8` | Apple Pay / Google Pay / LINE Pay 無法取得 Prime |
| `11` / `16` | 無此 App ID / App key 不符 |
| `41` | 卡片格式錯誤 |
| `88001` | SDK 尚未使用 setup 進行啟用 |
| `88003` | 遺失參數 |

---

## 支付方式對照表

| 支付方式 | SDK API | Prime 字首 | 適用情境 |
|----------|---------|------------|----------|
| 信用卡（TapPay Fields） | `TPDirect.card.getPrime` | （測試 `test_`） | 自訂版型刷卡 |
| 信用卡（Direct Pay iframe） | `TPDirect.card.getPrime` | （同上） | 單一 card view |
| Apple Pay | `TPDirect.paymentRequestApi.getPrime` | （測試 `ap_test_`） | Safari；iOS 16+ 其他瀏覽器 |
| Google Pay | `TPDirect.googlePay.getPrime` 或 `setupGooglePayButton` | （測試 `gp_test_`） | Android / Chrome 等 |
| Samsung Pay | `TPDirect.samsungPay.getPrime`；iframe 版 `TPDirect.samsungPayIframe.getPrime`（v5.25.0+） | （測試 `sp_test_`） | Samsung 裝置 |
| LINE Pay | `TPDirect.linePay.getPrime` | （測試 `ln_test_`） | LINE Pay |
| 街口支付 | `TPDirect.jkoPay.getPrime` | （測試 `jk_test_`） | 街口錢包 |
| 悠遊付 | `TPDirect.easyWallet.getPrime` | （測試 `ew_test_`） | 悠遊付 |
| 一卡通 MONEY | `TPDirect.iPassMoney.getPrime` | （測試 `pm_test_`） | 一卡通錢包 |
| Pi 拍錢包 | `TPDirect.piWallet.getPrime` | （測試 `pi_test_`） | Pi 拍錢包 |
| 全盈支付（全盈+PAY） | `TPDirect.plusPay.getPrime` | （測試 `ps_test_pc_` / `ps_test_mobile_`） | 全盈支付 |
| 全支付（PXPay Plus） | `TPDirect.pxPayPlus.getPrime` | （測試 `px_test_`） | 全支付 |
| AFTEE（先享後付） | `TPDirect.aftee.getPrime` | （測試 `af_test_`） | BNPL |
| 大哥付你分期（OP Pay） | `TPDirect.oppay.getPrime` | （測試 `op_test_`） | BNPL |
| 分期趣（GoGoPay） | `TPDirect.gogoPay.getPrime` | （測試 `go_test_`） | BNPL |
| Pay Later | `TPDirect.payLater.getPrime` | `pl_` | 依範例用於 Bind Card，非 `pay-by-prime` ⚠️ |
| 虛擬帳號（ATM） | `TPDirect.virtualAccount.getPrime` | `va_` | ATM / 網銀轉帳 |
| 超商取貨付款 | `TPDirect.cashOnDelivery.getPrime` | `cd_` | 超商取貨付款 |

> 除 Pay Later 外，各支付方式於後端 `pay-by-prime` 共用同一端點，但需配對對應的 `merchant_id`。Pay Later、Virtual Account、超商取貨付款只有 GitHub 範例，docs.tappaysdk.com 無專頁。Atome 已於 v5.21.0 移除。

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
| `-1` | Unknown |

---

## 常見問題排解

### Prime 已過期 / 已被使用

**症狀**：後端 `pay-by-prime` 回 `status: 91`（Prime 過期）或 `121`（參數錯誤：prime）。

**成因**：
- Prime 為**一次性**且效期 **90 秒**
- 重複呼叫、或商家系統延遲送出（如等待人工審核）

**解法**：
1. 前端取 Prime 後立即送至後端
2. 後端立即呼叫 `pay-by-prime`，避免任何同步等待
3. 若需「審核後扣款」，使用 `delay_capture_in_days` 延遲請款而非延後送 Prime

---

### Apple Pay 按鈕不顯示

**症狀**：`canMakePaymentWithActiveCard` 永遠為 `false`。

**檢查清單**：
1. 瀏覽器：Safari 皆可；iOS／iPadOS 16+ 的 Chrome、Edge、Firefox 需 Web SDK v5.12.3+
2. 網站是否為 **HTTPS**？（`localhost` 通常需 ngrok）
3. Apple Developer 端是否完成 Domain Verification？伺服器是否放行 Apple Pay 閘道 IP（443 port）？
4. `merchantIdentifier` 是否正確（使用 TapPay 商家申請服務者要用 Portal 產生的值）？
5. 該 Apple ID 是否有可用卡片？（Token Pay 沙箱須用真卡）

---

### Google Pay 沙箱無法測試

**症狀**：Google Pay 按鈕顯示，但 `getPrime` 回失敗。

**解法**：
- 檢查 `err.status`／`err.msg`（`-7` 為 Google Pay 無法取得 Prime）
- 沙箱 `googleMerchantId` 可省略，正式環境必填
- 代碼化卡號交易沙箱須用真卡；只測後端可改用測試 Prime `gp_test_...`

---

### Backend Notify 收不到

**症狀**：付款完成但商家伺服器未收到 POST。

**檢查清單**：
1. `result_url.backend_notify_url` 是否為公網可達、`https` 開頭且使用 **443 port**？
2. 防火牆 / WAF 是否擋住 TapPay？
3. 商家是否回應 HTTP `200`？（否則於 1、2、4、8、16 分鐘後重送，5 次都失敗改寄通知信）
4. 期間以 Record API（`rec_trade_id`）反查狀態，不要只等 notify

---

### Card Token 失效

**症狀**：`pay-by-token` 回 `status: 2013`（卡片過期）、`2011`（非法 token）或 `2012`（card key 錯誤）。

**解法**：
- 提示使用者重新綁卡（再走一次 `pay-by-prime` + `remember: true`）
- `remember=true` 時回應的 `card_info.expiry_date`（`YYYYMM`）可用來提前通知換卡

---

### 沙箱與正式金額不一致

**症狀**：沙箱可付 1 元，正式被收單行擋。

**解法**：
- TapPay 規格：TWD 單筆 1–20,000,000 元（AFTEE 上限 9,999,999）；HKD／MYR／USD 下限 0.01（[amount](https://docs.tappaysdk.com/tutorial/zh/reference.html#amount)）
- 收單行可能另有最低金額，正式上線前向 TapPay / 收單行確認

---

### Domain not allowed ⚠️

**症狀**：前端 SDK 載入後 `setupSDK` 拋錯。

**解法**：
- 至 TapPay Portal 「應用程式設定」加入正式網域（含 `www.` 與不含的版本）
- 確認 App ID / App Key 與 serverType 一致（錯誤碼 `11` 無此 App ID、`16` App key 不符）

---

### 重複交易（消費者重整頁面）

**解法**：
1. 商家自行產生唯一 `order_number`，記錄到 DB
2. 自訂唯一的 `bank_transaction_id`（重複時銀行回 `10013`，也讓 `421` 逾時可反查）
3. 收到 Notify 時以 `order_number` + `rec_trade_id` 做冪等
4. 前端在送出後立即 disable button + 顯示 loading

---

## 官方資源

- **TapPay Portal**：https://portal.tappaysdk.com
- **API 文件**：https://docs.tappaysdk.com
- **SDK Releases**：https://github.com/TapPay/tappay-web-example/releases
- **Web SDK 範例**：https://github.com/TapPay/tappay-web-example
- **iOS / Android SDK**：https://github.com/TapPay
- **技術支援**：support@cherri.tech（[文件首頁](https://docs.tappaysdk.com/tutorial/zh/home.html)）

