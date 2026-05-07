# PayNow Payment API Reference

立吉富線上金流（PayNow）金流 API 完整參考文件。

> ⚠ **重要說明**：PayNow 同時維運兩套金流 API。新接商家請優先採用「現代版 PaymentIntent API」，舊版 (一般網路商店購物車) 僅供既有整合參考。

---

## 目錄

1. [基本說明](#基本說明)
2. [兩套 API 比較總覽](#兩套-api-比較總覽)
3. [環境資訊](#環境資訊)
4. [認證方式](#認證方式)
5. [現代版 PaymentIntent API](#現代版-paymentintent-api)
   - [訂單建立 (PaymentIntent Create)](#訂單建立-paymentintent-create)
   - [付款執行 (PaymentIntent Checkout)](#付款執行-paymentintent-checkout)
   - [訂單查詢 (PaymentIntent Retrieve)](#訂單查詢-paymentintent-retrieve)
   - [Customer / 卡片代碼](#customer--卡片代碼)
   - [Apple Pay 系列](#apple-pay-系列)
   - [退款 (Refund)](#退款-refund)
6. [傳統版 一般網路商店購物車 API](#傳統版-一般網路商店購物車-api)
   - [訂單建立](#訂單建立-傳統版)
   - [付款結果通知](#付款結果通知-傳統版)
   - [檢核碼 GP/GK 服務](#檢核碼-gpgk-服務)
   - [背景交易 API (PayNowAPI_JS)](#背景交易-api-paynowapi_js)
   - [請款 / 退款 / 取消授權 / 訂單查詢](#請款--退款--取消授權--訂單查詢)
   - [Apple Pay (傳統版)](#apple-pay-傳統版)
7. [自動扣款 / 預存授權 (傳統版)](#自動扣款--預存授權-傳統版)
8. [SFTP 對帳檔](#sftp-對帳檔)
9. [錯誤代碼](#錯誤代碼)
10. [支付方式對照表](#支付方式對照表)
11. [常見問題排解](#常見問題排解)

---

## 基本說明

PayNow（立吉富）為臺灣本土的全方位電商金流／物流／發票整合服務商，運作生產流量網域為 `gateway.paynow.com.tw` 與 `www.paynow.com.tw`。OwlPay 為其姊妹品牌（B2B 跨境匯款），這也是部分 PayNow 文件鏡像出現在 `owlting.github.io/paynow-guideline` 的原因。

### 服務範疇

- **金流**：信用卡（國內 / 國外 / 銀聯）、ATM 虛擬帳號、超商代碼、條碼、Apple Pay、icash Pay、LINE Pay（線上 / 實體）、信用卡分期、預存授權（Token）、Apple Pay 延遲付款、mPOS / 分期富 EDC。
- **物流**：7-11 / 全家店到店、冷凍店到店、海外、黑貓宅急便。
- **發票**：電子發票開立、對獎 App。

### 兩個世代的 API

PayNow 並存兩個技術世代的金流 API，且短期內兩者皆會繼續運作：

| 世代 | 名稱 | 特性 | 推薦對象 |
|------|------|------|----------|
| 傳統版 | 一般網路商店購物車（apipdf/cashflow） | Form POST、SHA-1 PassCode、動態 AES-256 Key/IV、TimeStr 10 碼自訂格式 | 既有商家維護 |
| 現代版 | PaymentIntent / Customer / Refund REST API（apidoc） | RESTful JSON、Bearer Token、類似 Stripe 物件導向 | **新接商家請優先採用** |

**新專案建議**：直接採用現代版 PaymentIntent API。具備：
- 統一 JSON request / response
- Bearer Token 認證（透過後台申請 API Key）
- Customer / Card Token 物件，原生支援卡片代碼化（saved card）
- Apple Pay 流程整合在 PaymentIntent 內，免另行串接 SOAP WSDL
- 對應 PayNow Component（站內金流元件）的 `usePayNowSdk` 模式

舊版 API 僅在以下情境保留：
- 已上線商家的既有串接維護
- 票券核銷、預存授權（CIFID/CIFPW）等仍未在現代版 API 提供的服務
- 商家仍透過 PayNow 後台「賣場交易密碼」操作的工作流

---

## 兩套 API 比較總覽

| 項目 | 傳統版 (cashflow) | 現代版 (PaymentIntent) |
|------|-------------------|------------------------|
| 主要端點 | `POST https://www.paynow.com.tw/service/etopm.aspx` | `POST https://docs.paynow.com.tw/api/v1/payment-intents` |
| 通訊方式 | HTTP Form POST + URL Encode | HTTP JSON REST |
| 認證 | 商家代號 (`WebNo`) + 賣場交易密碼 + SHA-1 PassCode | `Authorization: Bearer <API_KEY>` |
| 資料加密 | 動態 AES-256-CBC（Key/IV 每次呼叫 GP/GK 取得）+ Zeros padding | TLS 即可，欄位明文 |
| 訂單編號 | `OrderNo` (商家自訂) + `BuysafeNo` (PayNow 19 碼) | `paymentNo` (商家自訂) + `id` (PayNow UUID) |
| 卡片代碼化 | 透過 `CIFID` / `CIFPW` 的「預存授權」 | 透過 `Customer` + `card-tokens` |
| Apple Pay | 自行串 ApplePaySession + `mpay.paynow.com.tw/api/ApplePay/GetTransactionSession` | `POST /api/v1/apple-pay-session` 或 `paymentMethodType=ApplePay` |
| 退款 | `OP=R_gp`，需 GP/GK 取 Key/IV + AES 加密 | `POST /api/v1/payment-intents/:id/refunds` |
| 訂單查詢 | `OP=PQS_gp` | `GET /api/v1/payment-intents/:id` |
| 對帳 | SFTP XML 檔（每日 01:00） | API + 商家後台（仍可保留 SFTP） |
| 發票通知 | 隨 PassCode/PassCode2 回傳 | 由 webhook 推送 |
| 推薦使用 | 維護用 | **新接、新功能** |

---

## 環境資訊

### 傳統版 (cashflow)

| 用途 | 測試 | 正式 |
|------|------|------|
| 一般購物車 | `https://test.paynow.com.tw/service/etopm.aspx` | `https://www.paynow.com.tw/service/etopm.aspx` |
| 背景 API | `https://test.paynow.com.tw/service/PayNowAPI_JS.aspx` | `https://www.paynow.com.tw/service/PayNowAPI_JS.aspx` |
| 預存授權服務 | `https://test.paynow.com.tw/service/paynowapi_js.aspx` | `https://www.paynow.com.tw/service/paynowapi_js.aspx` |
| 信用卡授權（Apple Pay）| `https://test.paynow.com.tw/WS_CardAuthorise_JS.asmx` | `https://www.paynow.com.tw/WS_CardAuthorise_JS.asmx` |
| Apple Pay 商家驗證 | （測試 / 正式皆使用同一網址） | `https://mpay.paynow.com.tw/api/ApplePay/GetTransactionSession` |
| SFTP 對帳檔 | （無獨立測試 SFTP） | `SFTP://61.216.8.41/`（每日 01:00 推送） |

> ⚠ 測試環境與正式環境完全獨立，帳號需個別申請。測試平台所有交易（除虛擬帳號取號流程外）皆會回傳 **F (失敗)**，無實際扣款。請勿在正式平台執行測試交易。

### 現代版 (apidoc / PaymentIntent)

| 用途 | 端點 |
|------|------|
| API Base | `https://docs.paynow.com.tw/api/v1/` ※ 文件展示用網域，實際以 PayNow 配發為準 |
| 編碼 | `application/json`，UTF-8 |
| 通訊協定 | HTTPS / TLS 1.2 以上 |

> 📌 上線時實際的 API 主機網域請以 PayNow 業務開通信件為準，並非 `docs.paynow.com.tw`（該網域為文件站，cURL 範例顯示為文件 base path）。

### 測試帳號

PayNow 不公開像 ECPay 那樣的固定測試金鑰，所有測試帳號需至 [https://test.paynow.com.tw](https://test.paynow.com.tw) 註冊取得：
- **賣家登入帳號**（`WebNo`）：身分證 / 統一編號（個人帳號 ID 開頭請大寫）
- **賣場交易密碼**（傳統版）：後台「商家專區」自行設定
- **API Key**（現代版）：聯繫業務取得 Bearer Token

### 測試卡號（傳統版 / 現代版皆適用）

| 卡號 | 用途 |
|------|------|
| `4311-9522-2222-2222` | 一般非 3D 測試卡 |
| `4000-2211-1111-1111` | 3D 驗證測試卡 |

- 有效期限：任意未過期月份（例 `12/30`）
- CVV：任意 3 碼
- 3D 密碼：`12345`

### 測試環境限制

- 測試平台所有交易（除虛擬帳號取號）皆強制回傳失敗
- WebATM：安泰銀行不提供測試交易，能正常顯示 WebATM 頁面即視為串接成功
- 虛擬帳號 / 超商代收：只需確認頁面金額、姓名、交易內容是否正確，**請勿實際繳費**

---

## 認證方式

### 傳統版 — SHA-1 PassCode + 動態 AES-256

傳統版採三段式安全機制：

1. **PassCode（SHA-1 雜湊）**：用於 Form POST 訂單建立時的「身分驗證」。
2. **GP/GK 動態 Key/IV**：所有背景 API（請款、退款、查詢）需先呼叫 GP 取得 `CheckNum`，再呼叫 GK 取得單次有效的 `EncryptionKey` / `EncryptionIV`，後續業務 payload 才以此 Key/IV 做 AES-256-CBC 加密。
3. **AES-256 Bootstrap Key（固定值）**：呼叫 GP/GK 階段使用固定 Bootstrap Key/IV：
   - Key：`paynowencryptpaynowcomtw28229955`
   - IV：`encrypt282299550`

#### Form POST 訂單建立的 PassCode 計算

**訂單建立 (送出時)**：

```
PassCode_raw = WebNo + OrderNo + TotalPrice + apicode
PassCode     = SHA-1(PassCode_raw).hex().upper()
```

說明：`apicode` 為 PayNow 後台核發的「API code」（非賣場交易密碼）。串接組合不含任何分隔符號（`+` 僅為文字描述）。

**訂單回傳驗證 (收到回呼時)**：

```
PassCode_raw = WebNo + OrderNo + TotalPrice + 賣場交易密碼 + TranStatus
PassCode     = SHA-1(PassCode_raw).hex().upper()
```

部分超商代碼回傳並含 `PassCode2`：

```
PassCode2 = SHA-1(PassCode + ReceiverEmail).hex().upper()
```

#### Python 實作 (傳統版 PassCode)

```python
import hashlib

def generate_paynow_passcode_request(web_no, order_no, total_price, apicode):
    """訂單建立 PassCode（送出方向）"""
    raw = f"{web_no}{order_no}{total_price}{apicode}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest().upper()


def verify_paynow_passcode_response(web_no, order_no, total_price,
                                    merchant_password, tran_status, received):
    """付款回傳 PassCode 驗證"""
    raw = f"{web_no}{order_no}{total_price}{merchant_password}{tran_status}"
    expected = hashlib.sha1(raw.encode("utf-8")).hexdigest().upper()
    return expected == received.upper()
```

#### TimeStr (10 碼自訂格式)

PayNow 的 TimeStr **不是** Unix Timestamp，而是 10 碼字串，用於背景 API 加密：

```
TimeStr = (西元年最後 1 碼) + (一年中第幾天，3 碼，左補 0) + (HH, 2 碼) + (MM, 2 碼) + (SS, 2 碼)
```

範例：2019-11-24 00:50:18
- 西元年最後 1 碼：`9`（2019）
- 一年第 328 天：`328`
- 時分秒：`00`、`50`、`18`
- TimeStr = `9328005018`

**Python 實作**：

```python
from datetime import datetime

def generate_paynow_timestr(now=None):
    now = now or datetime.now()
    year_last = str(now.year)[-1]
    day_of_year = str(now.timetuple().tm_yday).zfill(3)
    return f"{year_last}{day_of_year}{now.hour:02d}{now.minute:02d}{now.second:02d}"
```

#### 加權檢核碼（GP / GK 規則）

呼叫 GP 與 GK 時所組成的「加權檢核碼」16 碼是 SHA256 之前的字串骨幹，計算規則：

- 加權基數（固定 23 碼）：`93193193193193193193193`
- 加權權數 (23 碼) — **GP 規則**：`商家帳號前 5 碼` + `TimeStr (10 碼)` + `TimeStr 前 4 碼` + `商家帳號後 4 碼`
- 加權權數 (23 碼) — **GK 規則**：`商家帳號後 5 碼` + `TimeStr (10 碼)` + `TimeStr 前 4 碼` + `商家帳號前 4 碼`

接著：
1. 將 23 組基數 × 權數，逐位取「個位數字」相加得總和。
2. 計算 `10 - (總和 mod 10)`；若結果為 10，則取 0。此即「加權檢查碼」(1 碼)。
3. 加權權數前 15 碼 + 加權檢查碼 1 碼 = 「加權檢核碼」16 碼。

**範例 (GP)**：
- `mem_cid = 028229955`，`TimeStr = 9328005018`
- 加權權數 = `029955932800501893280282`
- 個位相加 = 104，10 − (104 mod 10) = 10 − 4 = 6
- 加權檢核碼 = `0282293280050186`

#### PassCode 組成 (GP / GK)

- **GP 送出**：`SHA256(mem_cid + 加權檢核碼GP).hex().upper()`
- **GP 回覆**：`HMACSHA256(mem_cid + 加權檢核碼GK, key=CheckNum).hex().upper()`
- **GK 送出**：`HMACSHA256(mem_cid + 加權檢核碼GK, key=CheckNum).hex().upper()`
- **GK 回覆**：`SHA256(mem_cid + 加權檢核碼GP).hex().upper()`

#### AES-256 加解密 (CBC + Zeros padding)

**Bootstrap Key/IV**（GP / GK 呼叫時）：
- Key: `paynowencryptpaynowcomtw28229955`（32 bytes）
- IV: `encrypt282299550`（16 bytes）

**動態 Key/IV**（業務 API 呼叫時，由 GK 回傳）：
- 每次 GK 呼叫取得 `EncryptionKey` (32 bytes hex 字串) 與 `EncryptionIV` (16 bytes hex 字串)
- 兩者皆為 ASCII 字串，加密時直接以該字串做 UTF-8 bytes 餵入 AES。

```python
from Crypto.Cipher import AES

def aes256_encrypt(plain_text, key, iv):
    """AES-256-CBC + Zeros padding，回傳 base64 字串"""
    raw = plain_text.encode("utf-8")
    pad_len = (16 - len(raw) % 16) % 16
    padded = raw + b"\x00" * pad_len
    cipher = AES.new(key.encode("utf-8"), AES.MODE_CBC, iv.encode("utf-8"))
    return cipher.encrypt(padded).hex()  # 部分 SDK 回傳 base64，請對應 PayNow 規範
```

> ⚠ PayNow 的 AES 範例使用 `Convert.ToBase64String` 回傳 base64，但部分背景 API 採 hex 拆分後再 URL Encode。實作前請以 PayNow 提供之 SDK / 範例為準。

### 現代版 — Bearer Token

現代版採用標準的 OAuth-style Bearer Token：

```
POST /api/v1/payment-intents HTTP/1.1
Authorization: Bearer <YOUR_API_KEY>
Content-Type: application/json
Accept: application/json
```

API Key 由 PayNow 業務窗口提供。所有 `Path Parameters`、`Query Parameters`、Request Body 均為標準 JSON / URL 樣式，**無需** 自行加密。

> 📝 **與 PayNow 發票 API 的差異**：PayNow 發票 API 使用 JWT 簽章，而本金流現代版使用單純 Bearer Token。請勿混用。

---

## 現代版 PaymentIntent API

### 訂單建立 (PaymentIntent Create)

#### 端點

```
POST /api/v1/payment-intents
Authorization: Bearer <API_KEY>
Content-Type: application/json
```

#### 請求參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `paymentNo` | string | 否 | 付款單號；不指定時系統自動產生 |
| `amount` | double | ● | 付款金額。限制 `< 1000000000000` |
| `currency` | string | ● | 固定為 `TWD` |
| `description` | string | 否 | 描述。≤ 255 字元 |
| `resultUrl` | string | 否 | 付款完成後消費者前台轉跳網址 |
| `webhookUrl` | string | 否 | 後端 Webhook 網址（付款結果通知） |
| `allowedPaymentMethods` | string[] | 否 | 限制可用付款方式；不傳則為「全開」 |
| `allowInstallments` | int32[] | 否 | 限定可分期數，需為 `[3,6,9,12,18,24]` 子集 |
| `isBillToRequiredMethods` | object | 否 | 強制要求填寫帳單地址的付款方式集合 |
| `expireDays` | int32 | 否 | 繳款天數（含當天）。僅 ATM、ConvenienceStore 有效 |
| `customer` | string | 否 | 指定付款人（傳入 customer_uuid） |
| `linePayOnlineInfo` | object | 否 | LINE Pay 線上付款資訊 |
| `linePayOfflineInfo` | object | 否 | LINE Pay 實體付款資訊 |
| `applePayDeferredInfo` | object | 否 | Apple Pay 延遲付款資訊 |

#### `allowedPaymentMethods` 可用值

| 代碼 | 說明 |
|------|------|
| `CreditCard` | 信用卡一次付清 |
| `CreditCardInstallment` | 信用卡分期 |
| `ATM` | ATM 虛擬帳號 |
| `ConvenienceStore` | 超商代碼（ibon / FamiPort） |
| `LINEPayOnline` | LINE Pay 線上付款 |
| `LINEPayOffline` | LINE Pay 實體付款 |
| `ApplePay` | Apple Pay 即時付款 |
| `ApplePayDeferred` | Apple Pay 延遲付款 |

> ⚠ `ApplePayDeferred` 不可與其他付款方式並列。

#### `linePayOnlineInfo` 結構

```json
{
  "channelId": "string",
  "options": {
    "displayLocale": "string",
    "extraBranchID": "string",
    "extraBranchName": "string"
  },
  "packages": [
    {
      "id": "string",
      "name": "string",
      "amount": 0,
      "products": [
        {
          "id": "string",
          "imageUrl": "string",
          "name": "string",
          "originalPrice": 0,
          "price": 0,
          "quantity": 0
        }
      ],
      "userFee": 0
    }
  ],
  "redirectUrlAppPackageName": "string"
}
```

#### `linePayOfflineInfo` 結構

```json
{
  "channelId": "string",
  "extras": {
    "addFriends": [{"idList": ["string"]}],
    "branchName": "string"
  },
  "productName": "string"
}
```

#### `applePayDeferredInfo` 結構

```json
{
  "billingAgreement": "string",
  "paymentDescription": "string",
  "deferredPaymentDate": "string",
  "freeCancellationDate": "string",
  "managementUrl": "string"
}
```

#### 回應結構

```json
{
  "status": 200,
  "type": "success",
  "message": "Success",
  "result": { /* PaymentIntent 物件 */ },
  "requestId": "uuid",
  "paginate": null
}
```

`result` 內含本次建立的 PaymentIntent 編號（`id`）、`paymentNo`、付款連結（`checkout_url`，由 PayNow 提供之 hosted page）等欄位。

#### 範例：信用卡分期 PaymentIntent

```bash
curl -X POST 'https://docs.paynow.com.tw/api/v1/payment-intents' \
  -H 'Authorization: Bearer <API_KEY>' \
  -H 'Content-Type: application/json' \
  --data-raw '{
    "paymentNo": "ORD20260507001",
    "amount": 12000,
    "currency": "TWD",
    "description": "Premium membership",
    "resultUrl": "https://shop.example.com/pay/result",
    "webhookUrl": "https://shop.example.com/pay/webhook",
    "allowedPaymentMethods": ["CreditCard", "CreditCardInstallment"],
    "allowInstallments": [3, 6, 12]
  }'
```

#### 範例：指定 Customer + ATM

```bash
curl -X POST 'https://docs.paynow.com.tw/api/v1/payment-intents' \
  -H 'Authorization: Bearer <API_KEY>' \
  -H 'Content-Type: application/json' \
  --data-raw '{
    "paymentNo": "ORD20260507002",
    "amount": 1500,
    "currency": "TWD",
    "allowedPaymentMethods": ["ATM"],
    "expireDays": 7,
    "customer": "cus_01h8hxxxxxxxxxxxxxxxxx"
  }'
```

---

### 付款執行 (PaymentIntent Checkout)

> 📌 此 API 需另行向 PayNow 業務申請開通；通常用於商家自建 Hosted Form / SDK 流程，非透過 PayNow Checkout 頁面時。

#### 端點

```
POST /api/v1/payment-intents/{id}/checkout
Authorization: Bearer <API_KEY>
Content-Type: application/json
```

| Path Parameter | 說明 |
|----------------|------|
| `id` | 由 [Payment Intent Create](#訂單建立-paymentintent-create) 取得的 PaymentIntent 編號 |

#### Body

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `paymentNo` | string | 否 | 自訂付款編號 |
| `usePayNowSdk` | boolean | 否 | 是否使用 PayNow Component / JS SDK 蒐集敏感資料（如卡號） |
| `key` | string | ● | 公鑰 |
| `secret` | string | ● | PaymentIntent secret |
| `paymentMethodType` | string | ● | 付款方式（值同 `allowedPaymentMethods`） |
| `paymentMethodData` | object | 視情況 | 付款資料；隨 `paymentMethodType` 不同而異 |
| `sessionId` | string | 否 | Session ID |
| `otpFlag` | boolean | 否 | 是否走 3DS / OTP 流程 |
| `meta` | object | 否 | 客戶端尺寸（client / iframe height、width） |
| `owlpay_session` | string | 否 | OwlPay Session（B2B 跨境用） |

#### `paymentMethodData` 必要欄位 (依 `paymentMethodType`)

| `paymentMethodType` | 必要 `paymentMethodData` 欄位 |
|---------------------|------------------------------|
| `CreditCard` | `card`, `billTo` |
| `CreditCardInstallment` | `card`, `installments`, `billTo` |
| `ConvenienceStore` | `codeType`（`ibon` 或 `fami_port`） |
| `LINEPayOffline` | `oneTimeKey` |
| `ApplePay` | `applePayPayload` |
| `ApplePayDeferred` | `applePayDeferredPayload` |

> 🔒 **PCI-DSS 注意**：當 `paymentMethodType=CreditCard` 並走自建表單時，建議搭配 `usePayNowSdk: true`，由 PayNow Component 接手卡號 / CVV 蒐集，避免商家伺服器接觸到原始 PAN（卡號），降低合規負擔。

#### 範例 (信用卡 + PayNow SDK token)

```bash
curl -X POST 'https://docs.paynow.com.tw/api/v1/payment-intents/{id}/checkout' \
  -H 'Authorization: Bearer <API_KEY>' \
  -H 'Content-Type: application/json' \
  --data-raw '{
    "usePayNowSdk": true,
    "key": "pk_live_xxxxxxxx",
    "secret": "pi_secret_xxxxxxxxxxxxxxxx",
    "paymentMethodType": "CreditCard",
    "otpFlag": true,
    "meta": {
      "client": {"height": 768, "width": 1024},
      "iframe": {"height": 600, "width": 480}
    }
  }'
```

#### Checkout 回應狀態

`result` 物件依付款方式不同會帶不同欄位，以下列舉常見場景：

| 場景 | result 重點欄位 |
|------|------------------|
| `CreditCard Default Success` | `status=success`、`auth_code`、`last4` |
| `CreditCard With Token` | `tokenized_card_id`（後續可重複使用） |
| `CreditCard Default 3D Secure` | `redirect_url`（需轉址完成 3DS） |
| `ConvenienceStore Ibon Pending Review` | `payment_code`、`expire_at` |
| `ATM Pending Review` | `bank_code`、`virtual_account`、`expire_at` |
| `LINE Pay Online Pending Review` | `redirect_url`（轉至 LINE Pay 完成扣款）|
| `Apple Pay Success` | `auth_code`、`last4` |
| `Apple Pay Deferred Pending Review` | `deferred_payment_id` |

---

### 訂單查詢 (PaymentIntent Retrieve)

#### 端點

```
GET /api/v1/payment-intents/{id}
Authorization: Bearer <API_KEY>
```

| Path Parameter | 說明 |
|----------------|------|
| `id` | PaymentIntent 編號 |

回傳 PaymentIntent 物件，欄位內容與 Checkout 回傳一致；可用於：
- 確認消費者是否已完成 ATM / 超商 / LINE Pay 取號 → 繳費的轉態
- 對帳腳本：以 PaymentIntent ID 拉取最新狀態
- 處理 Webhook 失敗的補單作業

```bash
curl -X GET 'https://docs.paynow.com.tw/api/v1/payment-intents/pi_01h8hxxxxxxxxxxxx' \
  -H 'Authorization: Bearer <API_KEY>'
```

---

### Customer / 卡片代碼

PayNow 現代版以「Customer」物件管理可重複扣款的消費者實體。透過 Customer + Card Token 的組合即可實現「綁卡定期扣款」、「一鍵下單」等場景。

#### Customer Create

```
POST /api/v1/customers
Authorization: Bearer <API_KEY>
```

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `first_name` | string | 否 | 名 |
| `last_name` | string | 否 | 姓 |
| `email` | string | 否 | 電子郵件 |
| `phone_code` | string | 否 | 電話國碼（如 `886`）|
| `phone_number` | string | 否 | 電話號碼 |
| `address` | object | 否 | 地址 |
| `metadata` | object | 否 | 商家自訂中繼資料 |

`address` 物件：

```json
{
  "country": "TW",
  "locality": "Taipei",
  "address1": "中山區民生東路三段 19 號",
  "address2": "12F",
  "administrative_area": "Taipei City",
  "postal_code": "10478"
}
```

回應的 `result` 中包含 `customer_uuid`，後續可帶入 PaymentIntent 的 `customer` 欄位。

#### Customer Retrieve

```
GET /api/v1/customers/{customer_uuid}
Authorization: Bearer <API_KEY>
```

#### Customer Card Token Retrieve

```
GET /api/v1/customers/{customer_uuid}/card-tokens
Authorization: Bearer <API_KEY>
```

回傳該 Customer 名下已 Tokenize 的卡片清單；`result` 為陣列，每個元素含：

| 欄位 | 說明 |
|------|------|
| `id` | Card Token ID（用於後續扣款） |
| `last4` | 卡號末四碼 |
| `bin` | 卡號前六碼 |
| `brand` | 卡別（VISA / Mastercard / JCB...） |
| `expire_month` / `expire_year` | 卡片效期 |

> 💡 **卡片代碼建立流程**：在 PaymentIntent Checkout 階段，於 `paymentMethodData.card` 加入 `tokenize: true`（或對應旗標）即可在交易成功後同步建立 Card Token，並關聯至指定 Customer。

---

### Apple Pay 系列

PayNow 現代版提供 **兩個版本** 的 Apple Pay session 端點，新整合請優先使用 v2：

#### Request Apple Pay session (v2)

```
POST /api/v2/apple-pay-session
Authorization: Bearer <API_KEY>
Content-Type: application/json
```

| 參數 | 說明 |
|------|------|
| `merchant_identifier` | Apple Pay Merchant ID（`merchant.xxx.xxx`）。若是經由 Web Merchant Registration API 註冊的 Payment Platform，則填 `partnerInternalMerchantIdentifier` |
| `display_name` | 顯示在 Apple Pay sheet 的商店名稱（≤ 64 UTF-8 字元，不可動態變化） |
| `initiative` | 標識電商應用的預設值（如 `web`） |
| `initiative_context` | 視 `initiative` 而定（通常為 domain）|

#### Confirm Apple Pay session (v1)

```
POST /api/v1/apple-pay-session
Authorization: Bearer <API_KEY>
Content-Type: application/json
```

| 參數 | 說明 |
|------|------|
| `merchant_identifier` | Apple Pay Merchant ID |
| `validation_url` | 由 ApplePaySession.onvalidatemerchant 取得的 `event.validationURL` |
| `domain_name` | 商店 Domain |
| `display_name` | 顯示名稱 |

#### Apple Pay Deferred Cancel

```
POST /api/v1/payment-intents/apple-pay-deferreds/{uuid}/cancel
Authorization: Bearer <API_KEY>
```

| 參數 | 必填 | 說明 |
|------|------|------|
| `uuid` (path) | ● | 要取消的 PaymentIntent 唯一識別碼 |
| `reason` (body) | ● | 取消原因，≤ 500 字元 |

#### Apple Pay Deferred Retrieve (列表)

```
GET /api/v1/payment-intents/apple-pay-deferreds?Status=<status>&Page=<n>&Limit=<n>
Authorization: Bearer <API_KEY>
```

| Query | 必填 | 說明 |
|-------|------|------|
| `Status` | ● | `Pending` / `Paid` / `Canceled` / `Failed` |
| `Page` | 否 | 頁碼，預設 `1` |
| `Limit` | 否 | 每頁數量，預設 `10` |

| Status | 中文 |
|--------|------|
| `Pending` | 待扣款 |
| `Paid` | 已扣款 |
| `Canceled` | 已取消 |
| `Failed` | 扣款失敗 |

---

### 退款 (Refund)

#### PaymentIntent Refund

```
POST /api/v1/payment-intents/{id}/refunds
Authorization: Bearer <API_KEY>
Content-Type: application/json
```

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `amount` | double | ● | 退款金額（可部分退款） |
| `reason` | string | ● | 退款原因（≤ 255 字元） |
| `bankCode` | string | 視情況 | ATM 退款必填（銀行代碼） |
| `bankBranchCode` | string | 視情況 | ATM 退款必填（分行代碼） |
| `bankAccount` | string | 視情況 | ATM 退款必填（銀行帳號） |

回應狀態：

| 狀態 | 說明 |
|------|------|
| `success` | 退款成功 |
| `failed` | 退款失敗 |
| `rejected` | 拒絕（拒絕原因在 `rejectReason` 欄位） |
| `processing` | 退款處理中 |
| `validation_error` | request 驗證資料錯誤 |

#### 範例：信用卡部分退款

```bash
curl -X POST 'https://docs.paynow.com.tw/api/v1/payment-intents/pi_01h8h.../refunds' \
  -H 'Authorization: Bearer <API_KEY>' \
  -H 'Content-Type: application/json' \
  --data-raw '{
    "amount": 500,
    "reason": "Customer requested partial refund"
  }'
```

#### 範例：ATM 退款

```bash
curl -X POST 'https://docs.paynow.com.tw/api/v1/payment-intents/pi_01h8h.../refunds' \
  -H 'Authorization: Bearer <API_KEY>' \
  -H 'Content-Type: application/json' \
  --data-raw '{
    "amount": 1500,
    "reason": "Out of stock",
    "bankCode": "812",
    "bankBranchCode": "0017",
    "bankAccount": "12345678901234"
  }'
```

#### Refund List

```
GET /api/v1/refunds?Page=<n>&Limit=<n>
Authorization: Bearer <API_KEY>
```

#### Refund Retrieve

```
GET /api/v1/refunds/{uuid}
Authorization: Bearer <API_KEY>
```

回傳指定 Refund 的詳細狀態，欄位包含 `status`、`amount`、`reason`、`rejectReason` 等。

---

## 傳統版 一般網路商店購物車 API

> ⚠ 傳統版適用於既有商家維護；新接商家請優先採用 PaymentIntent。

### 訂單建立 (傳統版)

#### 端點

```
POST https://www.paynow.com.tw/service/etopm.aspx     (正式)
POST https://test.paynow.com.tw/service/etopm.aspx    (測試)
Content-Type: application/x-www-form-urlencoded
```

#### 請求參數（信用卡 / WebATM / 虛擬帳號 / 超商代收 / 銀聯）

| 參數 | 類型 | 長度 | 必填 | 說明 |
|------|------|------|------|------|
| `WebNo` | string | 10 | ● | 賣家登入帳號 (統編 / 身分證；身分證開頭請大寫) |
| `PassCode` | string | - | ● | `SHA1(WebNo + OrderNo + TotalPrice + apicode)`，hex upper |
| `ReceiverName` | string | 20 | ● | 消費者姓名（不可為純數字）|
| `ReceiverID` | string | 50 | ● | 消費者身分證 / Email / 手機 |
| `ReceiverTel` | string | 20 | ● | 消費者電話 |
| `ReceiverEmail` | string | - | ● | 消費者 Email（需符合 Email 規格） |
| `OrderNo` | string | 50 | ● | 商家自訂訂單編號（不可為中文） |
| `ECPlatform` | string | 100 | ● | EC 平台名稱 |
| `TotalPrice` | string | - | ● | 整數；最低 30 元，最高 999,999,999 元 |
| `OrderInfo` | string | 200 | ● | 交易內容（5–200 字元） |
| `Note1` / `Note2` | string | 200 | ● | 商家自訂備註 |
| `PayType` | string | 2 | ● | 付款方式代碼（見下方對照） |
| `AtmRespost` | string | 1 | 否 | `0` / `1`，是否需要導頁回傳；預設 `0` |
| `DeadLine` | string | 1 | 否 | 繳款期限（限數字） |
| `PayEN` | string | 1 | 否 | `0` 中文 / `1` 英文 |
| `CodeType` | string | 1 | ● if 05 | 代碼繳費類別：`0` ibon / `1` FamiPort / `2` icash |
| `EPT` | string | 1 | ● | 固定 `1` |

#### `PayType` 對照表 (傳統版)

| 代碼 | 付款方式 |
|------|----------|
| `01` | 信用卡 |
| `02` | WebATM |
| `03` | 虛擬帳號 |
| `05` | 代碼繳費（ibon / FamiPort / icash，需配合 `CodeType`） |
| `09` | 銀聯卡 |
| `10` | 超商條碼 |
| `11` | 信用卡分期 |
| `13` | 自動扣款 / 預存授權 |

> 📌 服務設定後，請至「商家專區」更改每一個服務對應的「交易成功回傳網址」與「交易失敗回傳網址」，PayNow 將依照不同服務分別回傳到對應網址。

---

### 付款結果通知 (傳統版)

#### 1.1 信用卡 / WebATM / 銀聯 / 分期

PayNow POST 至商家設定之回呼網址（URL Encoded、UTF-8）：

| 參數 | 說明 |
|------|------|
| `WebNo` | 統編 / 身分證（信用卡交易才回傳） |
| `BuysafeNo` | PayNow 訂單編號（19 碼） |
| `PassCode` | `SHA1(WebNo + OrderNo + TotalPrice + 賣場交易密碼 + TranStatus)` |
| `OrderNo` | 商家訂單編號 |
| `TranStatus` | `S`：成功；`F`：失敗 |
| `ErrDesc` | 失敗原因（成功時無此欄位）|
| `TotalPrice` | 交易金額 |
| `Note1` / `Note2` | 商家備註 |
| `PayType` | `01`/`02`/`09`/`11` |
| `pan_no4` | 卡號末四碼（信用卡） |
| `Card_Foreign` | `0` 國內卡 / `1` 國外卡 |
| `installment` | 分期期數（非分期為空或 `1`） |

#### 1.2 虛擬帳號取號回傳 (離線)

| 參數 | 說明 |
|------|------|
| `BuysafeNo` | PayNow 訂單編號 |
| `OrderNo` | 商家訂單編號 |
| `PassCode` | `SHA1(WebNo + OrderNo + TotalPrice + 賣場交易密碼)` |
| `TotalPrice` | 交易金額 |
| `PayType` | `03` |
| `ATMNo` | 虛擬帳號號碼（繳款唯一編號）|
| `NewDate` | 產生日期（`yyyy/mm/dd hh:mm:ss`）|
| `DueDate` | 繳款期限（`yyyy/mm/dd`）|
| `TranStatus` | `S`：繳款成功；`F`：未繳款 |
| `BankCode` / `BranchCode` | 銀行 / 分行代碼 |

> ℹ 預設為「離線回傳」（消費者實際繳費後才通知）。如希望取號當下立即通知，請於送出時帶 `AtmRespost=1`。

#### 1.3 超商條碼回傳

| 參數 | 說明 |
|------|------|
| `BuysafeNo` | PayNow 訂單編號 |
| `OrderNo` | 商家訂單編號 |
| `PassCode` | `SHA1(WebNo + OrderNo + TotalPrice + 賣場交易密碼 + TranStatus)` |
| `TotalPrice` | 交易金額 |
| `PayType` | `10` |
| `BarCode1` / `BarCode2` / `BarCode3` | Code39 三段條碼 |
| `NewDate` | 產生日期 |
| `DueDate` | 繳款期限 |
| `TranStatus` | `S` / `F` |

#### 1.4 ibon / FamiPort / iCash 代碼回傳

含「交易產生時」與「交易成功時」兩階段：

| 參數 | 說明 |
|------|------|
| `BuysafeNo` | PayNow 訂單編號 |
| `OrderNo` | 商家訂單編號 |
| `TotalPrice` | 交易金額 |
| `PayType` | `05` |
| `icashpayno` / `IBONNO` / `FamiPortNo` | 對應通路繳費代碼 |
| `icashpayurl` | iCash 付款連結（`CodeType=2` 才有） |
| `NewDate` / `DueDate` | 產生日 / 繳款期限 |
| `IdKey` | EC 廠商使用，一般串接可忽略 |
| `TranStatus` | `S` / `F` |
| `PassCode` | 取號階段：`SHA1(WebNo + OrderNo + TotalPrice + 賣場交易密碼)`；繳款成功階段加上 `TranStatus` |
| `PassCode2` | `SHA1(PassCode + ReceiverEmail).hex().upper()`（僅成功時回傳） |
| `Note1` / `Note2` | 商家備註 |
| `ErrDesc` | 失敗時帶錯誤訊息 |

#### 商家回應格式

PayNow 不要求像 ECPay 一樣回應 `1|OK`。一旦 HTTP 200 即視為通知收訖。建議實作：

1. 解析 URL Encoded 參數 → URL Decode
2. 重新計算 `PassCode` 並比對
3. 將 `BuysafeNo` 對應至 `OrderNo` 完成入帳 / 出貨流程
4. 回應 HTTP 200（任意內容）

---

### 檢核碼 GP/GK 服務

#### 端點

```
POST https://www.paynow.com.tw/service/paynowapi_js.aspx     (正式)
POST https://test.paynow.com.tw/service/paynowapi_js.aspx    (測試)
Content-Type: application/x-www-form-urlencoded
```

#### Bootstrap Key/IV

```
Key: paynowencryptpaynowcomtw28229955
IV : encrypt282299550
```

#### 請求參數

| 參數 | 必填 | 說明 |
|------|------|------|
| `OP` | ● | `GP` 取得隨機檢查碼 / `GK` 取得業務 Key+IV |
| `JStr` | ● | JSON 字串（內容如下），先以 Bootstrap Key/IV 做 AES-256-CBC + URL Encode |

`JStr`（GP 模式）內容：

```json
{
  "mem_cid": "<商家統編/身分證>",
  "PassCode": "<GP PassCode>",
  "TimeStr": "<TimeStr 10 碼>"
}
```

`JStr`（GK 模式）內容：

```json
{
  "mem_cid": "<商家統編/身分證>",
  "PassCode": "<GK PassCode>",
  "TimeStr": "<TimeStr 10 碼>",
  "CheckNum": "<8 碼隨機檢查碼，由 GP 回傳>"
}
```

#### 回應

`Json字串` → URL Decode → AES-256 解密 (Bootstrap Key/IV) → 解析 JSON。

GP 回傳：

```json
{
  "mem_cid": "28229955",
  "PassCode": "CCE089C41567EFB631A3E82AA20D54B3F3D1BE841806C748AA9E39B57F301D73",
  "TimeStr": "2321163000",
  "CheckNum": "65813612"
}
```

GK 回傳：

```json
{
  "PassCode": "D35792712EBE651B297B4CD543086D47A68CCBB1338F19B19AD0EE8AA49F1355",
  "EncryptionKey": "9a704b9059f14ea18103ac874a8d42c3",
  "EncryptionIV": "adb710074b47cfc6"
}
```

> 🔁 取得 `EncryptionKey` / `EncryptionIV` 後即可呼叫業務 API（請款 / 退款 / 查詢 / 取消授權 / 預存授權）。Key/IV 與 `TimeStr` / `CheckNum` 為單次有效，每次業務呼叫皆需重新走 GP → GK 流程。

---

### 背景交易 API (PayNowAPI_JS)

#### 端點

```
POST https://www.paynow.com.tw/service/PayNowAPI_JS.aspx
POST https://test.paynow.com.tw/service/PayNowAPI_JS.aspx
```

#### 通用流程 (適用請款 / 退款 / 取消自動授權 / 訂單查詢)

```
1. POST OP=GP, JStr (Bootstrap AES) → 取得 PassCode + CheckNum
2. POST OP=GK, JStr (Bootstrap AES) → 取得 EncryptionKey + EncryptionIV
3. 將業務 JSON 以 EncryptionKey/IV 做 AES-256-CBC 加密 → 拆對半成 JStr1 / JStr2 → URL Encode
4. POST OP=<業務代號>, JStr1, JStr2, mem_cid, TimeStr, CheckNum
5. 解析回傳純字串 (S_xxx 成功 / F_xxx 失敗)
```

業務代號對照：

| OP | 服務 |
|----|------|
| `CP_gp` | 請款 |
| `R_gp` | 退款 |
| `CPA_gp` | 取消自動授權 |
| `PQS_gp` | 交易狀態查詢 |
| `WSC_DLP` | 取得預存卡號授權 |
| `T_S` | 票券核銷碼查詢（TripleDES，Key 固定 `28229955`）|
| `T_G` | 票券核銷（TripleDES，Key 固定 `28229955`）|

---

### 請款 / 退款 / 取消授權 / 訂單查詢

#### 請款 (`OP=CP_gp`)

`JStr1/JStr2` 加密前 JSON：

```json
{
  "UserID": "28229955",
  "Buysafeno": "8000002211114594530",
  "PassCode": "<SHA1('2822' + UserID + 賣場交易密碼 + '9955').upper()>"
}
```

回傳：`S_<urlencode 成功訊息>` 或 `F_<urlencode 錯誤訊息>`。

> 多筆訂單可於 `Buysafeno` 用逗號分隔（`8000...,8000...,8000...`）。

#### 退款 (`OP=R_gp`)

`JStr1/JStr2` 加密前 JSON：

```json
{
  "mem_type": "2",
  "buysafeno": "5000001111146998321",
  "mem_cid": "28229955",
  "passcode": "<SHA1('2822' + UserID + 賣場交易密碼 + '9955').upper()>",
  "mem_bankaccno": "12345678901234",
  "accountbankno": "812",
  "mem_bankaccount": "台新銀行 民生分行",
  "refundvalue": "客戶要求退款",
  "refundmode": "<退款型態>",
  "buyerid": "",
  "buyername": "",
  "buyeremail": "",
  "refundprice": "1500"
}
```

| 欄位 | 必填 | 說明 |
|------|------|------|
| `mem_type` | ● | `1` 買家 / `2` 賣家 |
| `buysafeno` | ● | PayNow 訂單編號 |
| `mem_cid` | ● | 商家帳號 |
| `passcode` | ● | 同上格式（`2822 + UserID + 賣場交易密碼 + 9955` SHA-1）|
| `mem_bankaccno` / `accountbankno` / `mem_bankaccount` | ● | 退款入帳帳號 / 銀行代碼 / 分行名稱 |
| `refundvalue` | ● | 退款原因 |
| `refundmode` | ● | 退款模式 |
| `refundprice` | ● | 退款金額 |
| `buyerid` / `buyername` / `buyeremail` | 否 | 與原交易消費者不同時才需填入 |

> ⚠ **退款須知**：請慎用退款機制。連續退款、異常退款等行為可能被銀行視為信用 / 異常交易，PayNow 將會停止帳號服務。請勿在正式平台執行測試退款，違者將被停用。

#### 取消自動授權 (`OP=CPA_gp`)

`JStr1/JStr2` 加密前 JSON：

```json
{
  "mem_cid": "28229955",
  "passcode": "<SHA1('2822' + mem_cid + OrderNo + 賣場交易密碼 + '9955').upper()>",
  "OrderNO": "<商家自訂訂單編號>"
}
```

#### 交易狀態查詢 (`OP=PQS_gp`)

請求 `JStr1/JStr2` 加密前 JSON：

```json
{
  "mem_cid": "28229955",
  "passcode": "<SHA1('2822' + mem_cid + OrderNo + 賣場交易密碼 + '9955').upper()>",
  "OrderNO": "<商家自訂訂單編號>"
}
```

回傳純字串（URL Encode）規則：

| 起始字元 | 意義 | 範例 |
|----------|------|------|
| `1,` | 交易成功 | `1,5000001111146998321_3211_1` (信用卡分期 1 期) |
| `1,` | 交易成功 (虛擬帳號) | `1,5000001111146998321_95533725300857` |
| `2,` | 交易失敗 / 未完成 | `2,5000001111146998321_3211_05` |
| `02,`/`03,`/... | 重覆交易 (兩筆 / 三筆) | `02,5000001111146998321_3211_1,5000001111146699323_4322_3` |
| `3,0` | 退貨：買家申請 |
| `3,1` | 退貨：買賣家確認 |
| `3,2` | 退貨：銀行退款 |
| `3,3` | 退貨：賣家申請 |
| `4` | 無交易訂單（消費者可能未送出授權）|

底線分隔：`{BuysafeNo}_{卡號末四碼或虛擬帳號}_{分期期數}`，分期期數於非分期交易固定為 `1`。

#### 票券核銷碼查詢 (`OP=T_S`) / 票券核銷 (`OP=T_G`)

兩者皆為 TripleDES + 固定 Key `28229955`：
- 公鑰：`12345678` (8 碼，作為 IV)
- 私鑰：`123456789028229955123456` (24 碼，最後 8 碼為 mem_cid)
- 模式：`ECB` + Zeros padding

JSON 內容：

```json
{
  "buysafeno": "<PayNow 訂單編號>",
  "checkno":   "<7 碼核銷碼，T_G 才需要>",
  "passcode":  "<SHA1(商家帳號 + 商家自訂編號 + 票券訂單金額 + 商家交易密碼).hex().upper()>"
}
```

---

### Apple Pay (傳統版)

傳統版 Apple Pay 串接需自行整合 ApplePaySession + 下列兩支 PayNow 端點：

#### 商家驗證

```
POST https://mpay.paynow.com.tw/api/ApplePay/GetTransactionSession
Content-Type: application/x-www-form-urlencoded
```

| 參數 | 說明 |
|------|------|
| `DisplayName` | 顯示的商店名稱（如 `PayNow`） |
| `DomainName` | 註冊的 Domain（如 `mpay.paynow.com.tw`） |
| `MemCid` | PayNow 商家帳號 |
| `MerchantIdentifier` | Apple Pay Merchant ID（`merchant.xxx.xxx`）|
| `ValidationURL` | 由 `ApplePaySession.onvalidatemerchant` 取得 |
| `Signature` | 商家驗證檢查碼（見下方）|

`Signature` 計算：

```
1. 將參數依 A-Z 排序，串成 「key1value1key2value2...」（不含 ValidationURL 與 Signature）
   範例：DisplayNamePayNowDomainNamempay.paynow.com.twMemCid28229955MerchantIdentifiermerchant.tw.com.paynow.pay
2. 全部轉小寫 + URL Encode
3. SHA-256 + 以「賣場交易密碼」為 Key (HMAC-SHA-256 形式)
4. 加密後字串再轉成全部小寫，放入 Signature 參數
```

回傳：

| 參數 | 說明 |
|------|------|
| `MemCid` | 商家帳號 |
| `MerchantIdentifier` | Apple Pay Merchant ID |
| `ErrMsg` | 錯誤描述 |
| `TradeStatus` | `S` / `F` |
| `TransactionSession` | 將整段物件 pass 給 `session.completeMerchantValidation()` |
| `Signature` | 同前算法重新計算（不含 TransactionSession 與 Signature 自身）|

#### 信用卡授權 (Apple Pay)

```
POST https://www.paynow.com.tw/WS_CardAuthorise_JS.asmx
POST https://test.paynow.com.tw/WS_CardAuthorise_JS.asmx
```

引用函式：`CardAuthorise_P`

請求參數：

| 參數 | 說明 |
|------|------|
| `JStr` / `JStr2` | 信用卡交易 JSON 內容；先 AES-256 加密（GP/GK 取得的動態 Key/IV）後對半拆成兩段，再 URL Encode |
| `mem_cid` | 商家帳號 |
| `TimeStr` | 取得 Key/IV 時的 TimeStr |
| `CheckNum` | GP 取得的隨機檢查碼 |

`JStr` 加密前 JSON：

```json
{
  "mem_cid": "28229955",
  "mem_checkpw": "<賣場交易密碼>",
  "OrderNo": "<商家自訂編號>",
  "OrderInfo": "<消費資訊>",
  "ECPlatform": "<EC 平台名稱>",
  "ReceiverID": "<消費者帳號>",
  "ReceiverEmail": "<email>",
  "ReceiverName": "<姓名>",
  "ReceiverTel": "<電話>",
  "TotalPrice": "<金額>",
  "PassCode": "<SHA1(mem_cid + OrderNo + TotalPrice + mem_checkpw).hex().upper()>"
}
```

回傳 (AES-256 解密後 JSON)：

| 欄位 | 說明 |
|------|------|
| `WebNo` | 商家帳號 |
| `BuysafeNo` | PayNow 訂單編號 |
| `OrderNo` | 商家自訂編號 |
| `RespCode` | 授權回覆代碼 |
| `TotalPrice` | 交易總金額 |
| `TranStatus` | `S` / `F` |
| `ResponseMSG` | 授權訊息 |
| `ApproveCode` | 信用卡授權碼 |
| `PassCode` | `SHA1(WebNo + mem_checkpw + BuysafeNo + TotalPrice + RespCode).hex().upper()` |
| `last4CardNo` | 卡號末四碼 |
| `CIFID_SN` | 預存授權帳號流水號 |
| `ErrorMessage` | 錯誤描述（如有） |

---

## 自動扣款 / 預存授權 (傳統版)

### 自動扣款 (PayType=13)

於 etopm.aspx 訂單建立時帶入：

| 參數 | 必填 | 說明 |
|------|------|------|
| `PayType` | ● | `13` |
| `Installment` | ● | 預備繳款期數（限數字 1–36） |
| `PayDay` | ● | 授權日（`01` ~ `31`） |
| `CIFID` | ● | UserID（最少 6 碼，大小寫有別）|
| `CIFPW` | ● | UserPW（最少 6 碼，大小寫有別）|
| `CIFID_SN` | 否 | 預存卡號流水號（系統預設 `1`） |

> ℹ 若 `CIFID_SN` 既存且不同卡號，會以本次內容覆蓋；若該流水號原儲存卡片已過期，亦會被覆蓋。

### 取得預存卡號授權 (`OP=WSC_DLP`)

`JStr1/JStr2` 加密前 JSON：

```json
{
  "mem_cid": "<商家帳號>",
  "mem_checkpw": "<賣場交易密碼>",
  "OrderNo": "<商家自訂編號>",
  "ECPlatform": "<EC 名稱>",
  "TotalPrice": "<總金額>",
  "CIFID": "<預存使用者帳號>",
  "CIFPW": "<預存使用者密碼>",
  "PassCode": "<SHA1(mem_cid + OrderNo + TotalPrice + mem_checkpw).hex().upper()>",
  "UserIp": "<使用者 IP>"
}
```

回傳 (AES-256 解密後 JSON)：

| 欄位 | 說明 |
|------|------|
| `WebNo` | 商家帳號 |
| `BuySafeNo` | PayNow 訂單編號 |
| `OrderNo` | 商家自訂編號 |
| `TotalPrice` | 總金額 |
| `RespCode` | 授權回覆代碼 |
| `TranStatus` | `S` / `F` |
| `InvoiceStatus` / `InvoiceNo` / `batchNo` | 發票相關（若有開立）|
| `ResponseMSG` | 授權訊息 |
| `ApproveCode` | 信用卡授權碼 |
| `PassCode` | `SHA1(WebNo + mem_checkpw + BuysafeNo + TotalPrice + RespCode).hex().upper()` |
| `last4CardNo` | 卡號末四碼 |
| `Result3D` | 3D 驗證結果 |
| `CIFID_SN` | 預存授權帳號流水號 |
| `ErrorMessage` | 錯誤描述 |

> 💡 特約商家可進行「1 元交易授權驗證」：系統授權確認後會自動取消授權，不會向消費者刷卡銀行請款。

---

## SFTP 對帳檔

PayNow 每日 01:00 透過 SFTP 推送對帳 XML 至商家：

- **位址**：`SFTP://61.216.8.41/`
- **編碼**：UTF-8
- **檔案類型**：

| 檔名 | 內容 |
|------|------|
| `YYYYMMDD_NN.xml` | 會員可請款資料 |
| `memYYYYMMDD_NN.xml` | 會員銀行帳號變更資料 |
| `BANKYYYYMMDD.xml` | 銀行代碼資料（手動更新時推送）|
| `BRANCHYYYYMMDD.xml` | 分行代碼資料（手動更新時推送）|
| `INSYYYYMMDD_NN.xml` | 銀行已撥款交易資料 |
| `NCCC_MCCCODEYYYYMMDD.xml` | MCC 代碼表 |

#### 範例：`PAYDOC.xml` (請款資料)

```xml
<PAYDOC>
  <DOCHEAD>
    <DOCDATE>20260507</DOCDATE>
    <TOTALRECORDS>2</TOTALRECORDS>
  </DOCHEAD>
  <CONTENT>
    <WEBNO>50208965</WEBNO>
    <BUYSAFENO>0602421630000078</BUYSAFENO>
    <CAPTUREPRICE>49</CAPTUREPRICE>
  </CONTENT>
  <CONTENT>
    <WEBNO>50208963</WEBNO>
    <BUYSAFENO>0602241030000054</BUYSAFENO>
    <CAPTUREPRICE>49</CAPTUREPRICE>
  </CONTENT>
</PAYDOC>
```

#### MCC_CODE 對照表 (摘錄)

| 代碼 | MCC 類別 |
|------|----------|
| `01` | 百貨 |
| `02` | 婦幼用品 |
| `03` | 男女服飾、鞋包、寢具、衣料毛線 |
| `04` | 食品與特產（含茶葉、水果） |
| `05` | 餐飲 |
| `06` | 住宿 |
| `07` | 傢俱、廚具、家飾、裝潢 |
| `08` | 家電、音響、影音 |
| `09` | 通訊 |
| `10` | 電腦（含軟體、硬體、週邊及耗材） |
| `11` | 機車買賣、汽機車修護保養、零件百貨 |
| `12` | 旅行社 |
| `13` | 圖書、報紙、雜誌、文具 |
| `14` | 體育用品 |
| `15` | 藝品 |
| `16` | 寵物用品 |
| `17` | 珠寶、鐘錶、眼鏡、銀器 |
| `18` | 照相器材 |
| `19` | 美妝 |
| `20` | 禮品、玩具、嗜好品 |
| `31` | 線上影音下載 |
| `32` | 線上軟體下載 |
| `33` | 線上電子書下載 |
| `34` | 線上遊戲（含點數、寶物、虛擬貨幣） |
| `99` | 拍賣 |

---

## 錯誤代碼

### 傳統版錯誤代碼分類

PayNow 傳統版使用首字母區分模組：

#### 會員資料新增 (`M*`)

| 代碼 | 說明 |
|------|------|
| `M000` | 參數錯誤 (Contract_check) PayNow 合約認可 |
| `M001` | 參數錯誤 (mem_kind) 會員類別 |
| `M002` | 參數錯誤 (mem_namebrain) 公司名稱或申請人姓名 |
| `M003` | 參數錯誤 (mem_cid) 公司統編或個人身分證 |
| `M004` | 參數錯誤 (mem_tax) 公司稅籍編號 |
| `M005` | 參數錯誤 (mem_nameregist) 負責人姓名 |
| `M006` | 參數錯誤 (mem_idregist) 負責人身分證 |
| `M007` | 參數錯誤 (mem_tel) 公司代表號 |
| `M008` | 參數錯誤 (mem_zipcode) 郵遞區號 |
| `M009` | 參數錯誤 (mem_add) 公司地址 |
| `M025` | 已有註冊相同帳號但未開通 |
| `M026` | 參數錯誤 (mem_fax) 傳真號碼錯誤 |
| `M027` | 會員加入系統錯誤 |
| `M028` | 會員驗證開通錯誤 |
| `M029` | 公司名稱 / 申請人 / 負責人不可輸入英數字 |
| `M030` | 此帳號可能已被註冊為賣家 |
| `M031` | 參數錯誤 (upmem) 是否買家升級賣家 |
| `M032` | 買家升級賣家錯誤 |
| `M033` | 此帳號可能已被註冊為買家 |
| `M034` | 此帳號未通過驗證 |
| `M035` | MCC_CODE 格式錯誤 |
| `M036` | 非使用中 MCC_CODE 代碼 |
| `M037` | 手續費率設定錯誤 |

#### 升級商務資格 (`A*`)

| 代碼 | 說明 |
|------|------|
| `A000` | 額度查詢錯誤 |
| `A001` | 商務升級會員帳號錯誤 |
| `A002` | 未使用信用卡認證 |
| `A003` | 您已使用過信用卡認證 |
| `A004` | 信用卡認證碼錯誤 |
| `A005` | 額度提升系統程式錯誤 |

#### 會員請款 (`C*`)

| 代碼 | 說明 |
|------|------|
| `C000` | 非 PayNow 會員 |
| `C001` | 無可請款資料 |
| `C002` | 無訂單編號資料 |
| `C003` | 可請款筆數與欲請款筆數不符 |
| `C004` | 訂單編號請款程式錯誤 |
| `C005` | 全數請款程式錯誤 |
| `C006` | 無對應驗證碼 ID |
| `C007` | 驗證碼錯誤 |
| `C008` | 無此 EC 廠商 |
| `C009` | 此會員無 EC 廠商 |

#### 銀行帳號變更 (`B*`)

| 代碼 | 說明 |
|------|------|
| `B000` | 更新會員銀行帳戶失敗 |
| `B001` | 驗證碼錯誤 |
| `B002` | 變更會員銀行帳戶系統錯誤 |

#### 交易退款 (`R*`)

| 代碼 | 說明 |
|------|------|
| `R000` | 退款系統程式錯誤 |
| `R001` | 申請人類別無填寫 |
| `R002` | 參數錯誤 (buysafeno) 訂單編號 |
| `R003` | 參數錯誤 (WebNo) 賣家會員帳號 |
| `R004` | 參數錯誤 (id) 買家會員帳號 |
| `R005` | 參數錯誤 (refundvalue) 退貨原因 |
| `R006` | 參數錯誤 (refunddate) 退貨日期 |
| `R007` | 參數錯誤 (ECPlatform) EC 廠商名稱 |
| `R008` | 參數錯誤 (IDKey) IDKey 檢驗識別碼 |
| `R009` | 參數錯誤 (PassCode) 檢驗識別碼 |
| `R010` | 參數錯誤 (refundmode) 退貨型態 |
| `R011` | 今日交易不可當日退款 |
| `R012` | 此交易賣家與申請退貨賣家不符 |
| `R013` | 查無此交易 |
| `R014` | 參數錯誤 (mem_bankaccno) 銀行帳號 |
| `R015` | 參數錯誤 (accountbankno) 銀行代碼 |
| `R016` | 參數錯誤 (mem_bankaccount) 撥款銀行分行名稱 |
| `R017` | 由賣家取消信用卡交易，系統自動通知發卡行退還額度 |
| `R018` | 非成功交易不得退款 |
| `R019` | 此貨品已配送不得退款 |
| `R020` | 此交易超過保管天數不得退款 |
| `R021` | 此交易小於 30 元不得退款 |
| `R022` | 此交易買家與申請退貨買家不符 |
| `R023` | 此交易已請款不得退款 |
| `R024` | 參數錯誤 (idRegist) 消費者身分證字號錯誤 |
| `R025` | 退貨取消錯誤 |
| `R026` | 此買家無可退貨交易 |
| `R027` | 交易已報送發卡行待回覆，目前不得退款 |
| `R028` | 只能是商家發動退款 |
| `R029` | 只能是確認退款狀態 |
| `R030` | 只能是信用卡交易 |
| `R031` | 退款金額錯誤 |
| `R032` | 此交易不支援部分退款 |
| `R033` | 今日請款金額（+30）須大於退款金額 |
| `R035` | 退款無法取消 |
| `R036` | 票券訂單已核銷，無法退款 |
| `R037` | 已撥款超過 180 天，退款作業需 2-3 工作天 |

#### 會員資料修改 (`N*`)

| 代碼 | 說明 |
|------|------|
| `N000` | 會員資料修改程式錯誤 |
| `N001` | 參數錯誤 (WebNo) 賣家會員帳號 |
| `N002` | 參數錯誤 (PassCode) 檢驗識別碼 |
| `N003` | 參數錯誤 (IDKey) IDKey 檢驗識別碼 |
| `N004` | 參數錯誤 (ECPlatform) EC 廠商名稱 |
| `N005`–`N013` | 參數錯誤（webtel / fax / memtel / zipcode / add / namecontect / emailcontect / telcontect / telpcontect） |
| `N014` | 參數錯誤 (mem_checkpw) 網站交易密碼 |
| `N015` | 地址不接受郵政信箱 |
| `N016`–`N017` | 地址 / 郵遞區號錯誤 |
| `N018` | 該賣家非 PayNow 會員 |
| `N019`–`N025` | 不可輸入全形字（賣家帳號 / 公司代表號 / 聯絡人 / 客服等） |
| `N026` | 身分證 / 統一編號驗證錯誤 |
| `N027` | 參數錯誤 (mem_type) 會員類型 |
| `N028` | 參數錯誤 (mem_webname) 網站名稱 |

#### 交易查詢 (`P*`)

| 代碼 | 說明 |
|------|------|
| `P000` | 交易查詢系統錯誤 |

#### 會員查詢 (`Q*`)

| 代碼 | 說明 |
|------|------|
| `Q000` | 系統錯誤 |
| `Q001` | 會員身分不符 |
| `Q002` | 查無此會員 |
| `Q003` | 未開通會員 |
| `Q004` | 單純買家會員，請轉換成賣家會員 |

#### 票券交易核銷 (`T*`)

| 代碼 | 說明 |
|------|------|
| `T000` | 系統錯誤 |
| `T001` | 票券未開通 |
| `T002` | 核銷碼格式錯誤（須 7 碼數字） |
| `T003` | 非票券交易 |
| `T004` | 核銷碼檢核錯誤 |
| `T005` | 統編驗證錯誤（非公司戶會員） |
| `T006` | 此會員已為票券使用者 |
| `T007` | 此會員非 EC 票券使用者 |
| `T008` | 非成功交易不可核銷 |
| `T009` | 訂單所屬賣家與商家帳號不合 |
| `T010` | 該票券已使用不可重複核銷 |

### 現代版 — Refund 狀態值

| 狀態 | 中文 |
|------|------|
| `success` | 退款成功 |
| `failed` | 退款失敗 |
| `rejected` | 拒絕（原因在 `rejectReason` 欄位） |
| `processing` | 退款處理中 |
| `validation_error` | 請求驗證資料有誤 |

### 現代版 — Apple Pay Deferred 狀態值

| 狀態 | 中文 |
|------|------|
| `Pending` | 待扣款 |
| `Paid` | 已扣款 |
| `Canceled` | 已取消 |
| `Failed` | 扣款失敗 |

### HTTP 層級錯誤（現代版）

| 狀態碼 | 說明 |
|--------|------|
| `200` | 成功 |
| `400` | Bad Request（參數驗證失敗） |
| `401` | Unauthorized（API Key 失效或未提供） |
| `404` | 資源不存在 |
| `422` | Unprocessable Entity（業務規則拒絕） |
| `500` | 伺服器錯誤 |

---

## 支付方式對照表

### 跨世代支付方式對照

| 支付方式 | 傳統版 `PayType` | 現代版 `paymentMethodType` | 備註 |
|----------|------------------|----------------------------|------|
| 信用卡（一次付清） | `01` | `CreditCard` | |
| WebATM | `02` | （無對應，由消費者於 hosted page 選擇）| |
| ATM 虛擬帳號 | `03` | `ATM` | 現代版以 `expireDays` 設定繳款期 |
| 代碼繳費 (ibon) | `05` + `CodeType=0` | `ConvenienceStore`，`codeType=ibon` | |
| 代碼繳費 (FamiPort) | `05` + `CodeType=1` | `ConvenienceStore`，`codeType=fami_port` | |
| icash 錢包 | `05` + `CodeType=2` | （無原生對應） | |
| 銀聯卡 | `09` | （需另行詢問業務） | |
| 超商條碼 | `10` | （現代版不直接提供，建議改用 `ConvenienceStore`）| |
| 信用卡分期 | `11` | `CreditCardInstallment` | 現代版 `allowInstallments` 限 [3,6,9,12,18,24] |
| 自動扣款 / 預存授權 | `13`（`CIFID/CIFPW`）| `Customer` + Card Token | 現代版以 Customer 物件管理 |
| Apple Pay | （需 SOAP / WS_CardAuthorise）| `ApplePay` | 現代版整合於 PaymentIntent |
| Apple Pay 延遲付款 | （傳統版未支援） | `ApplePayDeferred` | 商家 / 用戶可中途取消 |
| LINE Pay 線上 | （傳統版未支援） | `LINEPayOnline` | 需設定 `linePayOnlineInfo` |
| LINE Pay 實體 | （傳統版未支援） | `LINEPayOffline` | 需設定 `linePayOfflineInfo` |

### 金額限制 (傳統版)

| 付款方式 | 最低 | 最高 |
|----------|------|------|
| 信用卡 | NT$30 | NT$999,999,999 |
| WebATM | NT$30 | 一般帳戶單日 30,000；建議金額 > 20,000 改用信用卡 |
| 虛擬帳號 | NT$30 | NT$999,999,999 |
| 超商代碼 / 條碼 | NT$30 | 依超商規範 |

### 金額限制 (現代版)

- `amount` 上限：`< 1,000,000,000,000`（即 < 1 兆）
- 幣別：限 `TWD`

---

## 常見問題排解

### PassCode 驗證失敗 (傳統版)

**症狀**：訂單建立或回呼時收到 `R009` / `N002` / `P000`，或回呼 PassCode 不匹配。

**檢查項目**：
1. **WebNo 是否大寫**：身分證開頭字母請以大寫傳送（例 `A123456789`）
2. **金額型態**：`TotalPrice` 串接時直接以整數字串拼接（不能含小數點）
3. **賣場交易密碼 / apicode**：訂單建立時用 `apicode`，回呼驗證用「賣場交易密碼」，兩者不同
4. **SHA-1 hex 大小寫**：PayNow 期望大寫 (`hex.upper()`)
5. **特殊字元**：`OrderNo` 不可為中文

### AES 加解密失敗 (傳統版)

**症狀**：呼叫 `OP=GP` 或 `OP=GK` 收到 `F_xxx` 或無法解密回傳值。

**檢查項目**：
1. **Bootstrap Key/IV 是否正確**：`paynowencryptpaynowcomtw28229955` / `encrypt282299550`
2. **Padding 模式**：必須為 `Zeros`（不是 PKCS7）
3. **編碼**：JSON 字串以 UTF-8 bytes 餵入；Key/IV 也以 UTF-8 bytes 取
4. **回傳格式**：先做 URL Decode，再 Base64 → AES 解密
5. **TimeStr 是否同步**：TimeStr 為 10 碼自訂格式，非 Unix Timestamp，需精確按 PayNow 規則組裝

### 訂單編號重複

**症狀**：交易回傳「訂單編號重複」。

**解決**：
- `OrderNo` 在同一商家帳號下不可重複
- 建議用 `f"ORD{int(time.time())}{random.randint(100, 999)}"` 等格式產生
- 不可包含中文，最長 50 字元

### Apple Pay 「無法初始化」

**症狀**：`ApplePaySession.canMakePayments()` 回傳 false。

**檢查項目**：
1. 必須使用 Safari 瀏覽器（macOS / iOS）
2. 商家 Domain 需完成 Apple Pay 驗證（放置 `apple-developer-merchantid-domain-association.txt`）
3. 商店網站需 HTTPS 且 TLS 1.2 以上
4. Apple Pay Merchant ID 需先寄至 `service@paynow.com.tw`，並由 PayNow 發放憑證檔

### PaymentIntent Webhook 沒收到 (現代版)

**檢查項目**：
1. `webhookUrl` 是否為 HTTPS 公網可達
2. 是否有正確回應 `2xx` HTTP 狀態
3. 防火牆是否允許 PayNow 出口 IP
4. 可改用 `GET /api/v1/payment-intents/{id}` 主動輪詢

### 退款失敗

**常見原因**：
- `R011`：今日交易不可當日退款（請隔日再試）
- `R023`：訂單已請款（信用卡需走 `R_gp` 退款流程）
- `R032`：此交易不支援部分退款
- `R033`：今日請款金額（+30）必須大於退款金額（避免請款金額過小）
- `R037`：已撥款超過 180 天，退款需 2-3 個工作天

> ⚠ **重要警告**：請慎用退款機制。連續退款、異常退款等行為可能被銀行視為信用 / 異常交易，PayNow 可能停用您的帳號服務。**請勿在正式平台執行測試退款交易**。

### 從傳統版遷移到現代版

**建議遷移步驟**：

1. 向 PayNow 業務申請 API Key（現代版 Bearer Token）
2. 評估現有付款方式是否在現代版皆有對應（請參考[支付方式對照表](#支付方式對照表)）
3. 建立 Customer 物件，將既有預存授權 (CIFID/CIFPW) 用戶映射為 Customer + Card Token
4. 訂單建立改為 `POST /api/v1/payment-intents`
5. 支付頁面改用 PayNow 提供的 Hosted Checkout Page，或自建 + `usePayNowSdk: true` 的 PayNow Component
6. Webhook 處理改為解析 JSON（無 PassCode 驗證，但仍建議檢查 `requestId` 與後台對帳）
7. 退款改為 `POST /api/v1/payment-intents/{id}/refunds`
8. 並行運作期間同時處理兩套訂單，逐步切換流量

---

## 官方資源

- **技術文件首頁**：https://paynow-co.github.io/paynow-guideline/docs/
- **API Reference**：https://paynow-co.github.io/paynow-guideline/docs/api-reference/
- **測試平台**：https://test.paynow.com.tw
- **正式平台**：https://www.paynow.com.tw
- **Gateway 主機**：https://gateway.paynow.com.tw
- **物流服務**：https://logistic.paynow.com.tw
- **金流客服**：service@paynow.com.tw
- **發票客服**：einvoice@paynow.com.tw
- **物流客服**：etracking@paynow.com.tw
- **客服電話**：+886-2-2521-5088

---

最後更新：2026/05/07
