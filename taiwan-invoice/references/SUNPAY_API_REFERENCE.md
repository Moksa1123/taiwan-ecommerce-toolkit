# 紅陽科技 SunPay 電子發票 API 參考

> Source:《紅陽科技電子發票技術串接手冊》v2.3（70 頁），原始 PDF 存於 `_studies/sunpay/`
> 開發者專區: https://www.sunpay.com.tw/developers/
> 文件公開程度：public（PDF 免登入下載）
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
| `FetchOfflineSequence` | 離線字軌取號 |
| `GetInvoiceList` | 查詢發票清單 |
| `GetPrefixList` | 查詢字軌清單 |
| `GetOfflineInvoiceDeviceList` | 查詢離線裝置清單 |
| `UpdateDestroyInvoiceB2c` | B2C 註銷重開 |
| `UpdateDestroyInvoiceB2b` | B2B 註銷重開 |
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

### ⚠️ 加密前要先 URLEncode（.NET 風格、小寫 %xx）

```
JSON  →  URLEncode（%7b%22CompanyID%22%3a...，十六進位小寫）  →  AES-128-CBC/PKCS7  →  Base64
```

手冊第 8 章範例：`{"CompanyID":"12345678","TimeStamp":"12345678"}` 先編成
`%7b%22CompanyID%22%3a%2212345678%22%2c%22TimeStamp%22%3a%2212345678%22%7d` 再加密，
結果為 `W4fAhQNA5o+Asgcp21dxov01C+Gn6YvWaaP2tTbGHZutZeVe99PBEQsR+TTNCGBs3LR6hFSyxH7WTRUNw7aTFk1YmOuOgrHNU+4406j8g38=`。

直接加密 JSON、或用大寫 `%7B` 的 URLEncode，都會得到不同的 Token。
（已驗證：`tests/vectors/sunpay.json` 的 `invoice_token`。）

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
| `carrierType` | 載具類型 | ✅ | Integer | `0` 無載具 / `1` 手機條碼 / `2` 自然人憑證 / **`3` 紅陽會員載具** |
| `carrierId1` | 載具號碼 | 條件 | String(64) | `carrierType=0`/`3` 不需傳；`=1` 手機條碼 8 碼（首碼 `/`）；`=2` 自然人憑證 16 碼（前 2 碼 `A-Z` + 後 14 碼數字）|
| `donateMark` | 捐贈 | ✅ | Integer | `0` 不捐贈 / `1` 捐贈 |
| `PaperInvoiceOption` | 發票提供方式 | 條件 | Integer | **`carrierType=0`（無載具）時必填**：`0` 商店提供 / `1` **紅陽代印**。有載具或捐贈時不需傳。代印為加值服務需先申請 |
| `buyerAddress` | 買受人地址 | 條件 | String(100) | **`PaperInvoiceOption=1` 時必填** |
| `invoiceType` | 發票類別 | ✅ | Integer | `7` 一般稅額（配 `taxType` 1/2/3/9）/ `8` 特種稅額（配 `taxType=4`）|
| `taxType` | 課稅別 | ✅ | Integer | `1` 應稅 / `2` 零稅率 / `3` 免稅 / `4` 應稅（特種）/ **`9` 混合應稅與免稅或零稅率** |
| `taxRate` | 稅率 | ✅ | Decimal(10,2) | `taxType=1` 帶 `0.05`；`=2`/`3` 帶 `0`；`=4` 帶規定稅率（如 18% 帶 `0.18`）；**`=9` 不需傳** |
| `taxAmount` | 稅額 | ✅ | Decimal(12,0) | 純數字 |
| `salesAmount` | 應稅銷售額 | ✅ | Decimal(12,0) | 純數字（**未稅**）|
| `zeroTaxSalesAmount` | 零稅率銷售額 | ✅ | Decimal(12,0) | 純數字 |
| `freeTaxSalesAmount` | 免稅銷售額 | ✅ | Decimal(12,0) | 純數字 |
| `totalAmount` | 發票總金額 | ✅ | Decimal(12,0) | 含稅。**銷售額 + 稅額須等於此值** |
| `customsClearanceMark` | 通關方式註記 | ✅ | Integer | `taxType=2` 必填 `1` 非經海關 / `2` 經海關；**`taxType=1/3/4` 請填 `0`**；`=9` 且明細含零稅率時必填 |
| `zeroTaxRateReason` | 零稅率原因 | 條件 | String | `taxType=2` 必填，代碼 `71`–`79`（營業稅法第七條九款）；`=1/3/4` 不需傳 |
| `mem` | 發票備註 | | String(200) | |
| `isprint` | 紙本列印狀態 | ✅ | Integer | `0` 未列印 / `1` 列印 |
| `productItems` | 發票明細 | ✅ | Array | 見下 |
| `Token` | API 交易檢查碼 | ✅ | String(200) | AES 加密字串，見 §3 |

> ⚠️ **三個銷售額欄位都是必填**（`salesAmount` / `zeroTaxSalesAmount` / `freeTaxSalesAmount`），即使該類別為 0 也要帶。這與 O'Pay B2C 只帶單一含稅 `SalesAmount` 的設計完全不同。
> ⚠️ **`carrierType=3` 是紅陽自家會員載具**，不是財政部載具體系的一員；跨加值中心遷移時這類發票的載具無法直接對應。

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

## 5. B2B 開立發票

`POST /api/v1/SunPay/CreateInvoiceb2b`

**與 B2C 共用絕大多數欄位**，差異如下：

| 參數 | B2C | B2B |
|---|---|---|
| `buyerIdentifier` 買受人統編 | 選填，String(20) | **✅ 必填，String(10)** |
| `taxType` | 含 `9` 混合 | **不含 `9`**（僅 1/2/3/4）|
| `invoiceType=7` 適用 | `taxType` 1/2/3/9 | `taxType` 1/2/3 |
| `carrierType` / `carrierId1` / `donateMark` | 有 | **無**（B2B 不走載具與捐贈）|
| `buyerEmailAddress` | 僅一組 | **可多組，半形逗號分隔** |
| `IsSendMessage` 簡訊通知 | — | **✅ 必填**，`0` 不寄 / `1` 寄送（需先啟用加值服務）|
| `buyerTelephoneNumber` | — | String(26)，**`IsSendMessage=1` 時必填** |

`buyerName` 在 B2B 另有一句提醒：長度限 60 字元，**若長度不足建議改帶買方統一編號**。

其餘欄位（`PaperInvoiceOption`、`buyerAddress`、`taxRate`、四個金額、`customsClearanceMark`、`zeroTaxRateReason`、`mem`、`productItems`、`Token`）與 B2C 相同。

## 6. 作廢發票

`POST /api/v1/SunPay/CreateInvoiceInvalid`

| 參數 | 必填 | 型態 | 說明 |
|---|---|---|---|
| `merchantID` | ✅ | String(10) | |
| `invoiceNumber` | ✅ | String(10) | 要作廢的發票號碼 |
| `cancelReason` | ✅ | String(20) | **作廢原因，限 20 碼** |
| `Token` | ✅ | String(200) | |

回應 `result`：`merchantID`、`invoiceNumber`、`cancelDateTime`（`yyyy/MM/dd HH:mm:ss`）。

## 7. 開立折讓

`POST /api/v1/SunPay/Createallowance`

| 參數 | 必填 | 型態 | 說明 |
|---|---|---|---|
| `merchantID` | ✅ | String(10) | |
| `invoiceNumber` | ✅ | String(10) | 要折讓的發票號碼 |
| `orderNo` | ✅ | String(60) | 自訂訂單編號 |
| `productItems` | ✅ | Array | 折讓商品明細，見下 |
| `remindEmail` | ✅ | String(200) | **買受人信箱，折讓開立時寄送查詢資訊** |
| `Token` | ✅ | String(200) | |

折讓 `productItems[]`：

| 參數 | 必填 | 型態 | 說明 |
|---|---|---|---|
| `description` | ✅ | String(256) | 商品名稱 |
| `quantity` | ✅ | Integer | 純整數 |
| `unit` | | String(6) | 中文 2 字或英數 6 字 |
| `unitPrice` | ✅ | Decimal(10,2) | 見下方 ⚠️ |
| `amount` | ✅ | Decimal(10,2) | **小計，不含稅之進貨額**；數量 × 單價 |
| `Tax` | ✅ | Decimal(12,0) | 商品營業稅額（⚠️ **大寫 `T`**）|
| `taxType` | ✅ | Integer | 商品課稅別 |

> ⚠️ **稅務陷阱**：折讓的 `unitPrice` 可帶未稅或含稅金額。**若帶含稅金額則 `taxAmount=0`，申報時將無法扣抵該項營業稅額。** 手冊明文要求「請自行與會計人員確認採何種金額」。這是會實際影響公司稅務的選擇，不是純技術決定。

折讓的金額檢核只有一條：`折讓總金額 = 折讓商品小計 + 折讓商品稅額`。

作廢折讓為 `POST /api/v1/SunPay/CreateallowanceInvalid`。

## 8. 離線發票

`POST /api/v1/SunPay/CreateOfflineInvoiceB2c`

用於離線字軌發票**需要開立統一編號**的情境。與一般 B2C 的差別是**發票號碼由你提供**，而非平台配號：

| 參數 | 必填 | 型態 | 說明 |
|---|---|---|---|
| `merchantID` | ✅ | String(10) | |
| `orderNo` | ✅ | String(60) | |
| `DeviceIdCode` | ✅ | String(10) | **發票機台代碼** |
| `InvoiceNumber` | ✅ | String(10) | **自行帶入的發票號碼** |
| `RandomNumber` | ✅ | String(4) | **自行帶入的隨機碼** |
| `CreationDate` | ✅ | DateTime | `yyyy/MM/dd HH:mm:ss` |
| `buyerIdentifier` | | String(20) | 買受人統編 |
| `buyerName` | ✅ | String(60) | |
| `IsSendMessage` | ✅ | Integer | ⚠️ **離線發票固定帶 `0`（不寄簡訊）** |

其餘欄位比照 B2C。可用 `GetOfflineInvoiceDeviceList` 查詢已登記的機台清單。

## 9. `ValidateToken` — 先驗加密實作

`POST /api/v1/SunPay/ValidateToken`

只需 `merchantID` 與 `Token` 兩個欄位，回應同樣是 `status` / `message` / `result`。

> 💡 **這是串接紅陽發票的正確第一步**。AES 參數、Key/IV、以及那個容易寫錯的 UTC+8 `TimeStamp`（見 §3）都能在這支驗證，而且**不會產生任何發票資料**。先讓這支回 `SUCCESS` 再去串開立，可以省下大量在真實開立端點上盲試的時間。

## 10. 回應格式

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

## 11. 與其他加值中心對照

| 面向 | SunPay | O'Pay | ECPay | ezPay | Amego |
|---|---|---|---|---|---|
| 加密 | **AES-128-CBC + PKCS7**（Token 欄位）| AES-128-CBC（整包 Data）| AES-128-CBC（整包 Data）| AES-256-CBC + Hex | MD5 簽章 |
| 加密範圍 | **僅 `Token` 一欄**，其餘明文 | **整包業務參數** | **整包業務參數** | 整包 | 全參數簽章 |
| 時間戳 | ⚠️ **UTC+8 的 epoch**，300 秒 | 標準 Unix，600 秒 | 標準 Unix | — | — |
| 冪等 | ✅ **相同 PostData 回原發票** | 靠 `RelateNumber` 唯一性 | 靠 `RelateNumber` | 靠訂單編號 | — |
| 離線 POS | ✅ `CreateOfflineInvoiceB2c` | ✅ 批次取號 + 自動分段 | — | — | — |

> **紅陽最特別的兩點**：一是**只加密 `Token` 一個欄位**，業務參數走明文——這讓 debug 容易很多，但也代表傳輸層安全完全靠 HTTPS；二是**內建冪等**，這在台灣加值中心裡少見。

## 12. 查詢與字軌 API

以下各支都帶 `merchantID`、`Token` 與各自的條件，回應外層同 §10。

### `GetInvoiceList` 查詢發票（手冊 §7，p.29–36）

| 參數 | 必填 | 型態 | 說明 |
|---|---|---|---|
| `merchantID` | ✅ | String(10) | |
| `invoiceNumbers` | 擇一 | String(16) 陣列 | 發票號碼，例 `["AB12345678","AB12345679"]` |
| `orderNo` | 擇一 | String(60) | 自訂訂單編號；與 `invoiceNumbers` 擇一 |
| `Token` | ✅ | String(200) | 見 §3 |

`result` 為陣列，每筆欄位：

| 欄位 | 型態 | 說明 |
|---|---|---|
| `merchantID` / `orderNo` / `invoiceNumber` / `randomNumber` | | |
| `b2B` | String(3) | `1` B2B / `2` B2C |
| `buyerIdentifier` / `buyerName` / `buyerEmailAddress` / `buyerTelephoneNumber` / `buyerAddress` | | 買受人資料 |
| `invoiceType` | Integer | `7` 一般 / `8` 特種 |
| `printFlag` | String(1) | `Y` 索取紙本 / `N` 不索取（表格誤植為 `orintFlag`，範例為 `printFlag`）|
| `isPrint` / `printCount` | Integer | 是否已列印（`0`/`1`）、已列印次數 |
| `donateMark` / `poban` | | 捐贈與捐贈碼 |
| `carrierType` / `carrierId1` | | `0` 無載具 / `1` 手機條碼 / `2` 自然人憑證 / `3` 紅陽會員載具 |
| `taxType` / `taxRate` / `taxAmount` / `salesAmount` / `zeroTaxSalesAmount` / `freeTaxSalesAmount` / `totalAmount` | | `taxType` 含 `9` 混合 |
| `productItems` | 陣列 | `sequenceNumber`、`description`、`quantity`、`unit`、`unitPrice`、`amount`、`remark`、`taxType` |
| `hasAllowance` / `allowanceBalance` | Boolean / Integer | 是否有折讓、可開折讓餘額 |
| `flagA` | String(1) | 上傳財政部狀態：`1` 待轉 / `2` 已轉 / `3` 上傳成功 / `4` 上傳失敗 / `5` 完成 / `6` 失敗 |
| `flagCancel` | Integer | `0` 未作廢 / `1` 已作廢 |
| `CRT_DAT` | DateTime | 開立時間（表格寫 `yyyy/MM/dd HH:mm:ss`，範例為 ISO `2022-07-22T16:38:02`）|
| `barcode` / `leftQrCode` / `rightQrCode` | | **僅 `isPrint=1`** |

範例另有表格未列的 `tradeNumber`、`CRT_USR`、`cancelDateTime`、`mem`、`flagA_DATE`。

### `GetPrefixList` 查詢字軌（手冊 §8，p.37–38）

| 參數 | 必填 | 型態 | 說明 |
|---|---|---|---|
| `merchantID` / `Token` | ✅ | | |
| `RocYear` | | Integer | 民國年 |
| `IsOffline` | | Integer | `0` 否 / `1` 離線字軌 |
| `PeriodType` | | Integer | `1`–`6` 對應 01–02 月 … 11–12 月 |

`result` 欄位：`invoiceType`、`onf`（`1` 啟用 / `2` 暫停 / `3` 停用）、`InvoiceTrack`（字軌 2 碼）、`PeriodType`、
`Start_NO`、`End_NO`、`Now_NO`（`0` 尚未使用）、`IsOffline`、`IdCode`（發票機台代碼）。

### `GetOfflineInvoiceDeviceList` 查詢發票機台（手冊 §9，p.39–40）

只帶 `merchantID`、`Token`。`result` 欄位：`IdCode` String(10)、`Note` String(200)、`CRT_DAT`。

### `FetchOfflineSequence` 離線字軌取號（手冊 §10，p.41–42）

輔助配號並標記離線字軌取號狀態；不用這支、改用 `GetPrefixList` 自行管理配號也能開立離線發票。

| 參數 | 必填 | 型態 | 說明 |
|---|---|---|---|
| `merchantID` / `Token` | ✅ | | |
| `IdCode` | ✅ | String(10) | 發票機台代碼 |
| `InvoiceType` | | Integer | `7` 一般 / `8` 特種；未帶預設一般 |
| `RocYear` | ✅ | Integer | 民國年 |
| `PeriodType` | ✅ | Integer | `1`–`6` |
| `FetchCount` | ✅ | Integer | 取號本數，每本 50 張 |

`result` 欄位：`InvoiceTrack`、`Start_NO`、`End_NO`。

## 13. 註銷重開（手冊 §12，p.50–64）

以新內容重開同一張發票：`UpdateDestroyInvoiceB2c`、`UpdateDestroyInvoiceB2b`。

請求欄位與對應的開立端點（§4、§5）相同，差異：

| 參數 | 說明 |
|---|---|
| `invoiceNumber` | ✅ String(10)，要註銷重開的發票號碼 |
| `reSend_Reason` | ✅ String(20)，註銷重開原因 |
| `orderNo` | **不帶** |
| `IsSendMessage` | ✅ `0` 不寄 / `1` 寄簡訊（B2C 開立沒有這欄，註銷重開兩版都有）；`=1` 時 `buyerTelephoneNumber` 必填 |

回應同開立（B2C p.56–57、B2B p.63–64）。B2B 回應表格寫 `randomNum`，範例為 `randomNumber`。

## 14. 與官方 Claude Code Skill 的差異

紅陽開發者專區提供「電子發票 AI 串接指南（Claude Code Skill）v2.3」（`sunpay-einvoice-skill-v2.3-v1.zip`，165 行）。

| 項目 | 官方 skill | 手冊 v2.3（本文件依據）|
|---|---|---|
| `TimeStamp` | Unix epoch 秒 | 第 8 章 C# 範例 `DateTime.UtcNow.AddHours(8)`，比 Unix 多 28800 秒（§3）|
| 欄位命名 | PascalCase（`InvoiceType`、`BuyerIdentifier`…）| camelCase（`invoiceType`、`buyerIdentifier`…）|
| 紙本／捐贈 | `PrintMark`、`NPOBAN`、請求帶 `RandomNumber` | `isprint`、`PaperInvoiceOption`、`poban`；請求沒有隨機碼欄位 |
| 涵蓋端點 | B2C 開立、作廢；其餘寫「見手冊」| 全部 13 支 |

Token 的 AES 流程兩者一致，官方 skill 附的自檢向量已用 `examples/sunpay-invoice-example.py` 驗證相符。
`TimeStamp` 的兩種定義互相矛盾，需在測試環境實測確認。

## 15. 待補

| 項目 | 備註 |
|---|---|
| `TimeStamp` 定義 | 手冊與官方 skill 矛盾（§14），需測試帳號實測 |
| 錯誤訊息清單 | 手冊未提供統一錯誤碼表，僅 `message` String(30) 動態說明，無法整理成 `error-codes.csv` |

## 16. 來源

- 電子發票技術串接手冊 v2.3 — `https://storage.googleapis.com/joinchill-image/sunpay_techdoc/202603/紅陽科技電子發票技術串接手冊V2.3.pdf`
- 開發者專區 — https://www.sunpay.com.tw/developers/
- 電子發票 AI 串接指南（Claude Code Skill）v2.3 — `https://storage.googleapis.com/joinchill-image/sunpay_techdoc/202607/sunpay-einvoice-skill-v2.3-v1.zip`
- 測試環境申請 — https://testinv.sunpay.com.tw/sign-up
- 正式環境會員 — https://einv.sunpay.com.tw
- 發票管理後台 — https://inv.sunpay.com.tw/
- 金流端 reference — [../../taiwan-payment/references/sunpay-payment-api.md](../../taiwan-payment/references/sunpay-payment-api.md)
