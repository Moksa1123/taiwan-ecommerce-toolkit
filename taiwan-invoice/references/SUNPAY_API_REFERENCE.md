# 紅陽科技 SunPay 電子發票 API 參考

> Source:《紅陽科技電子發票技術串接手冊》v2.3（70 頁），原始 PDF 存於 `_studies/sunpay/`
> 開發者專區: https://www.sunpay.com.tw/developers/
> Captured: 2026-08-08 · doc_access: **public**（PDF 免登入下載）
> 涵蓋層級: 端點 ✅ / 認證與加密 ✅ / B2C 開立逐欄 ✅ / 回應逐欄 ✅ / B2B 與其餘端點 ⚠️ 待補
> 金流端: [../../taiwan-payment/references/sunpay-payment-api.md](../../taiwan-payment/references/sunpay-payment-api.md)

## 0. 定位

紅陽同時做**金流 + 電子發票**，兩者可搭配「隨交易自動開立發票」。但**兩邊的加密機制完全不同**：

| | 金流 | 電子發票 |
|---|---|---|
| 加密 | **RSA 分段加密 + SHA256 簽章** | **AES-128-CBC + PKCS7** |
| 網域 | `trade.sunpay.com.tw` | `einv.sunpay.com.tw` |
| 金鑰 | RSA 公鑰（PEM）+ SHA2 密鑰 | Hash Key + Hash IV（各 16 碼）|

> ⚠️ **同一家廠商、兩套機制**。串完金流不代表發票能沿用同一組加解密程式碼。

## 1. 環境與網域

| 環境 | API Base | 會員／後台 |
|---|---|---|
| 測試 | `https://testinv.sunpay.com.tw/api/v1/SunPay/` | https://testinv.sunpay.com.tw |
| 正式 | `https://einv.sunpay.com.tw/api/v1/SunPay/` | https://einv.sunpay.com.tw |

> ⚠️ **正式環境是 `einv.` 不是 `inv.`**。`inv.sunpay.com.tw` 是發票管理後台入口，**不是 API 網域**——這兩個很容易混淆。

申請流程：測試環境於 `testinv.sunpay.com.tw` 申請，取得測試用 **Hash Key 與 Hash IV**；正式環境於 `einv.sunpay.com.tw` 申請會員後取得正式金鑰。

## 2. 端點總表

| 端點 | 功能 |
|---|---|
| `CreateInvoiceb2c` | **B2C 開立發票** |
| `CreateInvoiceb2b` | **B2B 開立發票** |
| `CreateInvoiceInvalid` | 作廢發票 |
| `Createallowance` | 開立折讓 |
| `CreateallowanceInvalid` | 作廢折讓 |
| `CreateOfflineInvoiceB2c` | **離線 B2C 開立** |
| `GetInvoiceList` | 查詢發票清單 |
| `GetPrefixList` | 查詢字軌清單 |
| `GetOfflineInvoiceDeviceList` | 查詢離線裝置清單 |
| `UpdateDestroyInvoiceB2b` | B2B 銷毀更新 |
| `ValidateToken` | **驗證 Token**（可先用這支確認加密實作正確）|

> 💡 **先打 `ValidateToken`**。它只驗 Token，不會產生發票資料——是驗證 AES 實作與時間校正最安全的起手式。

## 3. 認證：`Token` 欄位

所有端點都要帶 `Token`（String(200)），內容是一段 AES 加密字串。

### 加密設定

```
KeySize   = 128
CipherMode = CBC
PaddingMode = PKCS7
```

Hash Key 與 Hash IV **各為 16 碼**（手冊範例：`A123456789012345` / `B123456789012345`）。

### 加密前的明文

```json
{"CompanyID":"12345678","TimeStamp":"1666204130"}
```

| 欄位 | 說明 |
|---|---|
| `CompanyID` | 賣方公司統一編號 |
| `TimeStamp` | 見下方 ⚠️ |

### ⚠️ `TimeStamp` 的定義是台灣時間的秒數，不是標準 Unix timestamp

手冊原文定義為「從 1970/1/1 至今的**台灣時間（UTC+8）**之總秒數」，並附上 C# 範例：

```csharp
long timeStamp = Convert.ToInt32(
    DateTime.UtcNow.AddHours(8).Subtract(new DateTime(1970, 1, 1)).TotalSeconds);
```

**注意 `.AddHours(8)`**——這代表送出的值比真正的 Unix epoch **多 28800 秒**。手冊自己的對照也印證：`1666204130 = 2022/10/19 18:28:50`（台灣時間）。

> 如果你用 `time.time()`、`Date.now()/1000`、`DateTimeOffset.UtcNow.ToUnixTimeSeconds()` 這類標準做法，會**整整差 8 小時**而必定逾時失敗。正確做法是取 UTC 後加 8 小時再算 epoch。

**逾時限制：秒數差超過 300 秒交易即失敗。** 主機需校時。

## 4. B2C 開立發票

`POST /api/v1/SunPay/CreateInvoiceb2c`

### 請求參數

| 參數 | 中文 | 必填 | 型態 | 說明 |
|---|---|---|---|---|
| `merchantID` | 商店代號 | ✅ | String(10) | 自發票商店後台取得 |
| `orderNo` | 自訂訂單編號 | ✅ | String(60) | |
| `buyerIdentifier` | 買受人統編 | | String(20) | 純數字 |
| `buyerName` | 買受人名稱 | ✅ | String(60) | |
| `buyerEmailAddress` | 買受人信箱 | 條件 | String(80) | 開立時寄送查詢資訊。**`carrierType=3` 時必填**；**`taxType=9` 且明細含零稅率時必填** |
| `isprint` | 紙本列印狀態 | ✅ | Integer | `0` 未列印 / `1` 列印 |
| `productItems` | 發票明細 | ✅ | Array | 見下 |
| `Token` | API 交易檢查碼 | ✅ | String(200) | AES 加密字串，見 §3 |

### `productItems[]`

| 參數 | 中文 | 必填 | 型態 | 說明 |
|---|---|---|---|---|
| `description` | 商品名稱 | ✅ | String(256) | |
| `quantity` | 商品數量 | ✅ | Integer | **限純整數** |
| `unit` | 商品單位 | | String(6) | **中文 2 字或英數 6 字**（如「個」「件」「本」）|
| `unitPrice` | 商品單價 | ✅ | Decimal(10,2) | 整數 10 位、小數 2 位 |
| `amount` | 商品小計 | ✅ | Decimal(10,2) | **數量 × 單價 = 小計** |
| `remark` | 商品備註 | | String(40) | |
| `taxType` | 商品課稅別 | 條件 | Integer | **發票 `taxType=9` 時為該商品課稅別**：`1` 應稅 / `2` 零稅率 / `3` 免稅 |

> `quantity` 限純整數——若你的系統有「0.5 小時」這類小數數量，需先換算單位。這點與 O'Pay（支援小數 2 位）不同。

## 5. 回應格式

所有端點共用：

| 參數 | 型態 | 說明 |
|---|---|---|
| `status` | String(10) | `SUCCESS` / `ERROR` |
| `message` | String(30) | `status=ERROR` 時的錯誤說明 |
| `result` | JSON | 業務資料 |

### ⚠️ 內建冪等：重複送出相同 PostData 會回 SUCCESS 與**原發票**

手冊明載：**「當該筆開立發票參數 PostData 已重覆且參數資料完全一致，則回傳 SUCCESS」**，且 `result` 回傳**原本那張發票**。

> 這是好事——網路逾時後可安全重送，不會開出兩張發票。但**前提是參數「完全一致」**；只要有一個欄位不同（例如你重試時重算了金額或改了備註），就會被視為新的一張發票而重複開立。**重試務必送出位元組層級相同的 payload。**

### `result` 欄位（B2C 開立）

| 參數 | 中文 | 型態 | 說明 |
|---|---|---|---|
| `tradeNumber` | 電子發票開立序號 | String(16) | |
| `orderNo` | 自訂訂單編號 | String(60) | |
| `totalAmount` | 發票總金額 | Integer | |
| `invoiceNumber` | 發票號碼 | String(10) | |
| `randomNumber` | 防偽隨機碼 | String(4) | **僅 `isprint=1` 時提供** |
| `CRT_DAT` | 開立時間 | DateTime | `yyyy/MM/dd HH:mm:ss` |
| `barcode` | 發票條碼 | String(20) | **僅 `isprint=1`**；含發票期別、字軌號碼、隨機碼，兌獎輸入用 |
| `leftQrCode` | 發票 QRCode（左）| String(200) | **僅 `isprint=1`** |
| `rightQrCode` | 發票 QRCode（右）| String(500) | **僅 `isprint=1`** |

> ⚠️ **`isprint=0` 時拿不到 `randomNumber` / `barcode` / `leftQrCode` / `rightQrCode`**。如果你要自行產生發票證明聯，`isprint` 必須帶 `1`。

## 6. 折讓的金額檢核

手冊明載本服務只檢核一條：

```
折讓總金額 = 折讓商品小計 + 折讓商品稅額
```

> 手冊同時附上一句提醒：「發票計算方式，請串接人員務必與公司財會人員進行確認，發票資料關係到公司稅務」。平台端檢核寬鬆**不等於**稅務上正確。

## 7. 與其他加值中心對照

| 面向 | SunPay | O'Pay | ECPay | ezPay | Amego |
|---|---|---|---|---|---|
| 加密 | **AES-128-CBC + PKCS7**（Token 欄位）| AES-128-CBC（整包 Data）| AES-128-CBC（整包 Data）| AES-256-CBC + Hex | MD5 簽章 |
| 加密範圍 | **僅 `Token` 一欄**，其餘明文 | **整包業務參數** | **整包業務參數** | 整包 | 全參數簽章 |
| 時間戳 | ⚠️ **UTC+8 的 epoch**，300 秒 | 標準 Unix，600 秒 | 標準 Unix | — | — |
| 冪等 | ✅ **相同 PostData 回原發票** | 靠 `RelateNumber` 唯一性 | 靠 `RelateNumber` | 靠訂單編號 | — |
| 離線 POS | ✅ `CreateOfflineInvoiceB2c` | ✅ 批次取號 + 自動分段 | — | — | — |

> **紅陽最特別的兩點**：一是**只加密 `Token` 一個欄位**，業務參數走明文——這讓 debug 容易很多，但也代表傳輸層安全完全靠 HTTPS；二是**內建冪等**，這在台灣加值中心裡少見。

## 8. 待補

| 項目 | 備註 |
|---|---|
| B2B 開立逐欄 | 端點與回應格式已確認，請求欄位待擷取 |
| 作廢 / 折讓 / 作廢折讓 的請求欄位 | 端點已確認 |
| 離線 B2C 開立與裝置清單 | 端點已確認 |
| `GetInvoiceList` / `GetPrefixList` 查詢參數 | 端點已確認 |
| 錯誤訊息清單 | 手冊未提供統一錯誤碼表，僅 `message` String(30) 動態說明 |
| 發票課稅別 `taxType` 主欄位取值 | 已知 `9` 為混合，其餘待確認 |

原始 PDF 與抽出文字存於 `_studies/sunpay/`，可直接再解析。

## 9. 來源

- 電子發票技術串接手冊 v2.3 — `https://storage.googleapis.com/joinchill-image/sunpay_techdoc/202603/紅陽科技電子發票技術串接手冊V2.3.pdf`
- 開發者專區 — https://www.sunpay.com.tw/developers/
- 測試環境申請 — https://testinv.sunpay.com.tw/sign-up
- 正式環境會員 — https://einv.sunpay.com.tw
- 發票管理後台 — https://inv.sunpay.com.tw/
- 金流端 reference — [../../taiwan-payment/references/sunpay-payment-api.md](../../taiwan-payment/references/sunpay-payment-api.md)
