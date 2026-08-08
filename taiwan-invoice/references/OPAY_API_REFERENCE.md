# 歐付寶 O'Pay 電子發票 API 參考

> Source:《歐付寶電子發票 B2C API》(opay_i100.pdf, 145 頁)、《B2B API》(opay_i200.pdf, 130 頁)、《離線電子發票 API》(opay_i301.pdf, 52 頁)
> 文件總覽: https://developers.opay.tw/download/document
> Captured: 2026-08-08 · doc_access: **public**（PDF 免登入直連下載）
> 涵蓋層級: 信封 ✅ / 加密 ✅（含官方範例）/ B2C `Issue` 逐欄 ✅ / B2B 模式與 `Issue` 逐欄 ✅ / 離線取號 ✅ / 錯誤碼 ⚠️ 官方不公開（見 §8）

## 0. 與 ECPay 綠界發票的關係

歐付寶發票 API 與綠界電子發票 API **結構同源**：同樣的 `MerchantID` + `RqHeader` + `Data` 三層信封、同樣的 AES 加密資料層、同樣的 `/B2CInvoice/Issue` 路徑命名。差別在網域與金鑰。

已熟悉 [ECPAY_API_REFERENCE.md](ECPAY_API_REFERENCE.md) 者，遷移成本很低。

**但歐付寶多了一塊 ECPay 沒有的：完整的 B2B 存證流程與離線 POS 發票。**

## 1. 環境

| 環境 | Base URL |
|---|---|
| 測試 | `https://einvoice-stage.opay.tw` |
| 正式 | `https://einvoice.opay.tw` |
| 廠商後台（測試） | `https://vendor-stage.opay.tw` |
| 廠商後台（正式） | `https://vendor.opay.tw` |

後台操作手冊：https://vendor.opay.tw/Content/themes/new20150706/EinvoiceManual.pdf

## 2. 請求信封格式

所有 API 皆為 `POST`，JSON body，三層結構：

```json
{
  "MerchantID": "2000132",
  "RqHeader": {
    "Timestamp": 1525168923
  },
  "Data": "…（加密後字串）…"
}
```

| 欄位 | 型態 | 必填 | 說明 |
|---|---|---|---|
| `PlatformID` | String(10) | | 特約合作平台商代號。**一般廠商請放空值**；平台商需先向歐付寶申請開通 |
| `MerchantID` | String(10) | ✅ | 特店編號。**平台商使用時，此欄位僅限帶入已綁定的子廠商編號** |
| `RqHeader.Timestamp` | Number | ✅ | Unix timestamp |
| `Data` | String | ✅ | 業務參數，加密後字串 |

> ⚠️ **`Timestamp` 有效區間為 10 分鐘**。超過即拒絕，訂單無法建立。實務上這代表**你的主機必須做時間校正（NTP）**——這是自架環境最常見的「參數都對但一直失敗」原因。

回應同樣為三層：

```json
{
  "MerchantID": "2000132",
  "RqHeader": { "Timestamp": 1525169058 },
  "TransCode": 1,
  "TransMsg": "",
  "Data": "…"
}
```

`TransCode = 1` 代表**傳輸資料（MerchantID, RqHeader, Data）接收成功**，其餘均為失敗。

> ⚠️ `TransCode=1` 只代表**信封收到了**，不代表發票開立成功。業務結果在解密後的 `Data` 裡（`RtnCode`）。這是兩層錯誤處理，常被漏掉。

平台商模式下，`Data` 內另有一層 `MerchantID` 指向實際子廠商。

## 3. `Data` 加密規格

> Source: opay_i100.pdf 附錄 3「參數加密方式說明」

**AES-128-CBC / PaddingMode: PKCS7**，且**先 URL Encode 再加密**：

```
明文 JSON  →  URLEncode  →  AES-128-CBC 加密  →  Base64  →  放入 Data
```

解密反向：`Data` → AES 解密 → URLDecode → JSON。

### 官方加密範例（可拿來驗證你的實作）

測試金鑰：`MerchantID=2000132`、`HashKey=ejCk326UnaZWKisg`、`HashIV=q9jcZX8Ib9LM8wYk`

| 階段 | 值 |
|---|---|
| (1) 加密前 | `{"Name":"Test","ID":"A123456789"}` |
| (2) URLEncode 後 | `%7B%22Name%22%3A%22Test%22%2C%22ID%22%3A%22A123456789%22%7D` |
| (3) AES 加密後 | `uvI4yrErM37XNQkXGAgRgJAgHn2t72jahaMZzYhWL1HmvH4WV18VJDP2i9pTbC+tby5nxVExLLFyAkbjbS2Dvg==` |

> 這組 Key/IV 與 **ECPay 綠界發票測試環境完全相同**——再次印證兩者同源。若你已有 ECPay 發票的加解密函式，可直接沿用，只需換網域。

### ⚠️ URLEncode 的 .NET 差異（附錄 2）

歐付寶文件明列一張轉換表，其 .NET 實作與 RFC 3986 標準**不一致**：

| 字元 | 標準編碼 | 歐付寶 .NET 實際 |
|---|---|---|
| `space` | `%20` | **`+`** |
| `~` | `%7e` | **`%7e`**（不還原） |
| `-` `_` `.` `!` `*` `(` `)` | `%2d` `%5f` `%2e` `%21` `%2a` `%28` `%29` | **原字元不編碼** |

PHP 端官方建議用 `str_replace` 把 `%21` 轉回 `!` 等字元再送出。**這一段和 ECPay 的 CheckMacValue urlencode 差異是同一個坑**，跨語言實作時最容易對不起來。

## 4. B2C 發票 API 端點

Base: `https://einvoice.opay.tw/B2CInvoice/`（測試環境 `einvoice-stage`）

### 開立與作廢

| 端點 | 功能 |
|---|---|
| `Issue` | 開立發票 |
| `DelayIssue` | 延遲開立 |
| `CancelDelayIssue` | 取消延遲開立 |
| `TriggerIssue` | 觸發開立（延遲開立的實際觸發） |
| `Invalid` | 作廢發票 |
| `VoidWithReIssue` | 作廢並重開 |
| `GetIssue` | 查詢開立結果 |
| `GetInvalid` | 查詢作廢結果 |

> 延遲開立三兄弟（`DelayIssue` → `TriggerIssue` / `CancelDelayIssue`）與 ezPay 的 `Status=0` 暫存機制解決同一個問題：先建資料、確認出貨後才真正開立。實作上要注意**未觸發的發票永遠不會上傳財政部**。

延遲開立的回應碼與一般開立不同：

| `RtnCode` | 意義 |
|---|---|
| `1` | 成功（一般開立、查詢等） |
| `4000003` | **延後開立成功**（`DelayIssue`） |
| `4000004` | **開立發票成功**（`TriggerIssue` 觸發後） |

非上述值即為失敗。**不要只判斷 `RtnCode == 1`**，延遲開立流程會被誤判成錯誤。

### `Issue` 開立發票 — `Data` 欄位

`*` 為必填。

| 參數 | 名稱 | 型態 | 說明 |
|---|---|---|---|
| `*MerchantID` | 特店編號 | String(10) | |
| `*RelateNumber` | 特店自訂編號 | String(30) | **需唯一不可重複**。勿用特殊符號；**大小寫視為相同**（`123abc456` = `123ABC456`） |
| `CustomerID` | 客戶編號 | String(20) | 建議英數與底線 |
| `CustomerIdentifier` | 統一編號 | String(8) | 純數字。⚠️ **2023-01-01 起檢查碼邏輯由「可被 10 整除」改為「可被 5 整除」**（財政部公告），舊版檢核程式會誤擋 |
| `CustomerName` | 客戶名稱 | String(60) | `Print=1` 時必填；`CustomerIdentifier` 有值時須填公司名 |
| `CustomerAddr` | 客戶地址 | String(100) | `Print=1` 時必填 |
| `CustomerPhone` | 客戶手機 | String(20) | 與 `CustomerEmail` **至少擇一**，純數字 |
| `CustomerEmail` | 客戶信箱 | String(80) | 與 `CustomerPhone` 至少擇一，僅可填一組。測試環境勿帶真實信箱 |
| `ClearanceMark` | 通關方式 | String(1) | `TaxType=2`（零稅率）時必填。`1`非經海關出口 / `2`經海關出口 |
| `*Print` | 列印註記 | String(1) | `0`不列印 / `1`列印 |
| `*Donation` | 捐贈註記 | String(1) | `0`不捐贈 / `1`捐贈 |
| `LoveCode` | 捐贈碼 | String(7) | `Donation=1` 必填。數字 3–7 碼，首位可為 0。**建議先呼叫 `CheckLoveCode` 驗證** |
| `CarrierType` | 載具類別 | String(1) | 空字串無載具 / `1`歐付寶載具 / `2`自然人憑證 / `3`手機條碼 / `4`悠遊卡 / `5`icash / `6`一卡通 / `7`金融卡 / `8`信用卡 |
| `CarrierNum` | 載具編號 | String(64) | 見下方規則 |
| `*TaxType` | 課稅類別 | String(1) | `1`應稅 / `2`零稅率 / `3`免稅 / `4`應稅特種稅率 / `9`混合（限收銀機發票且需申請核可）|
| `ZeroTaxRateReason` | 零稅率原因 | String(2) | `TaxType=2` 或 `9` 時必填，未帶預設 `71`（外銷貨物）。代碼 `71`–`79` 對應營業稅法第七條九款 |
| `SpecialTaxType` | 特種稅額類別 | Int | `TaxType=1/2/9` 系統自動帶 `0`；`=3` 必填 `8`；`=4` 必填 `1`–`8`（`1`酒家 25% / `2`夜總會 15% / `3`銀行保險專屬本業 2% / `4`再保費 1% / `5`非專屬本業 5% / `6``7`銀行保險本業 5% / `8`免稅或非銷項）|
| `*SalesAmount` | 發票總金額（含稅）| Int | **整數，不可有小數點；限新台幣；不可為 0** |
| `InvoiceRemark` | 發票備註 | String(200) | |
| `*InvType` | 字軌類別 | String(2) | `07`一般稅額 / `08`特種稅額。**`07` 只能配 `TaxType` 1/2/3/9；`08` 只能配 3/4** |
| `vat` | 單價是否含稅 | String(1) | `1`含稅（預設）/ `0`未稅 |
| `Items` | 商品 | Array | **最多 200 項** |

`Items[]` 子欄位：

| 參數 | 名稱 | 型態 | 說明 |
|---|---|---|---|
| `ItemSeq` | 商品序號 | Int | |
| `*ItemName` | 商品名稱 | String(100) | |
| `*ItemCount` | 商品數量 | Number | 整數 8 位、小數 2 位 |
| `*ItemWord` | 商品單位 | String(6) | |
| `*ItemPrice` | 商品單價 | Number | 整數 8 位、小數 7 位。依 `vat` 決定含稅與否 |
| `ItemTaxType` | 商品課稅別 | String(1) | **`TaxType=9` 時不可為空**。`1`應稅 / `2`零稅率 / `3`免稅 |
| `*ItemAmount` | 商品合計 | Number | **一律為含稅小計** |
| `ItemRemark` | 商品備註 | String(40) | |

#### ItemAmount 的計算規則（最常見的開立失敗原因）

各項 `ItemAmount` 加總四捨五入後**必須等於 `SalesAmount`**，且：

| 條件 | 公式 | 範例 |
|---|---|---|
| `vat=1` 且 `TaxType=1` 或 `4` | `ItemPrice(含稅) × ItemCount = ItemAmount` | `500 × 5 = 2500` |
| `vat=0` 且 `TaxType=1`（稅率 5%）| `ItemPrice(未稅) × ItemCount × 1.05 = ItemAmount` | `500 × 5 × 1.05 = 2625` |

> `TaxType=9`（混合）時，商品課稅別**只能是「應稅+免稅」或「應稅+零稅率」**——免稅與零稅率不能同時出現在一張發票。

#### CarrierNum 依 CarrierType 的填法

| `CarrierType` | `CarrierNum` |
|---|---|
| `""` | 空字串 |
| `1` 歐付寶載具 | **空字串**，系統自動帶入（客戶信箱）|
| `2` 自然人憑證 | 固定 16 碼：2 碼大寫英文 + 14 碼數字 |
| `3` 手機條碼 | 固定 8 碼，第 1 碼為 `/` |
| `4`–`8` | 必填**隱碼 id**；`8` 為信用卡加密卡號 |

另有 `CarrierNum2`（顯碼）：`CarrierType=4`–`7` 必填實體卡片顯碼；`=8` 必填刷卡日期（民國年月日 7 碼）。

> ⚠️ `CarrierType=1/2/3` 時**請勿填 `CarrierNum`**，否則會被系統阻擋。
> ⚠️ 查詢發票 API 在 `CarrierType=4`–`8` 時**基於資安不回傳載具號碼**。

#### Print / Donation / CarrierType / CustomerIdentifier 的交互約束

這四個欄位彼此牽制，是 B2C 開立最容易踩的地方：

| 情境 | 約束 |
|---|---|
| `Donation=1`（要捐贈）| `Print` **必須** `0` |
| `CustomerIdentifier` 有值 | `Donation` **必須** `0` |
| `CustomerIdentifier` 有值 + `CarrierType=""` | `Print` 帶 `1` |
| `CustomerIdentifier` 有值 + `CarrierType=1` 或 `2` | `Print` 帶 `0` |
| `CustomerIdentifier` 有值 + `CarrierType=3` | `Print` 可帶 `0` 或 `1` |
| `Print=1`（要列印）| `CarrierType` 帶空字串 |
| `Print=0` 且 `CustomerIdentifier` 有值 | `CarrierType` **不可**帶空字串 |

**超商 KIOSK 列印**（需另向業務申請開通）：

| 需求 | 參數組合 | 限制 |
|---|---|---|
| 列印消費發票（ibon）| `Print=1`, `CarrierType=""`, `CustomerIdentifier=""`, `Donation=0` | 只能印一次，之後中獎也無法再印 |
| 列印中獎發票（ibon / FamiPort）| `Print=0`, `CarrierType=1`, `CustomerIdentifier=""`, `Donation=0` | 只能印一次 |
| 折讓後金額為 0 | — | **不可列印** |

### 折讓

| 端點 | 功能 |
|---|---|
| `Allowance` | 開立折讓 |
| `AllowanceByCollegiate` | 協議折讓 |
| `AllowanceInvalid` | 作廢折讓 |
| `AllowanceInvalidByCollegiate` | 作廢協議折讓 |
| `GetAllowanceList` | 查詢折讓清單 |
| `GetAllowanceInvalid` | 查詢作廢折讓 |

> **一般折讓 vs 協議折讓**：一般折讓由賣方單方開立；協議折讓需買賣雙方確認。稅務效果不同，別混用。

### 字軌管理

| 端點 | 功能 |
|---|---|
| `AddInvoiceWordSetting` | 新增字軌設定 |
| `GetInvoiceWordSetting` | 查詢字軌設定 |
| `UpdateInvoiceWordStatus` | 更新字軌狀態（啟用/停用） |
| `GetGovInvoiceWordSetting` | 查詢財政部配號結果 |

### 查驗與工具

| 端點 | 功能 |
|---|---|
| `CheckBarcode` | **手機條碼驗證** |
| `CheckLoveCode` | **捐贈碼（愛心碼）驗證** |
| `GetCompanyNameByTaxID` | 依統編查公司名稱 |
| `InvoicePrint` | 發票列印 |
| `InvoiceNotify` | 發票通知（寄送 Email/SMS） |
| `InvoiceNotifySetting` / `GetInvoiceNotifySetting` | 通知設定 |
| `RemainNotifySetting` / `GetRemainNotifySetting` | 字軌餘量通知設定 |

> `CheckBarcode` / `CheckLoveCode` 上游就是財政部平台，見 [MOF_EINVOICE_API_REFERENCE.md](MOF_EINVOICE_API_REFERENCE.md)。若你已經在用歐付寶開發票，用這兩支就好，不必自己去申請財政部 AppID。

### 空白發票

| 端點 | 功能 |
|---|---|
| `QueryBlankInvoiceList` | 查詢空白發票清單 |
| `DownLoadBlankInvList` | 下載空白發票清單 |
| `BlankInvAutoUploadSetting` | 空白發票自動上傳設定 |

## 5. B2B 發票 API 端點

Base: `https://einvoice.opay.tw/B2BInvoice/`

### ⚠️ B2B 有兩種模式，不是一種

這是 B2B 串接最關鍵的前提，先選模式再談端點：

| 模式 | 定義（官方原文語意）| 流程 |
|---|---|---|
| **存證模式** | 類似傳統發票的電子化，將發票資料**存證至財政部** | 單向，開立方送出即可 |
| **交換模式** | 仿照目前**交付紙本發票**的流程，轉換成電子資料交換 | 雙向，需交易相對人**確認** |

**「開立 → 確認」的兩階段只存在於交換模式**；存證模式沒有 `*Confirm` 這一層。歐付寶支援 7 天內將 B2B 發票上傳財政部。

> 存證模式下，依財政部規定**只允許買方開立作廢折讓**。若以賣方角度呼叫「作廢折讓通知」會收到買/賣方錯誤，實際意義是「無須另行通知給作廢折讓開立方」——這不是 bug。

### 前置：交易對象維護

**串接任何 B2B 端點前，必須先呼叫 `MaintainMerchantCustomerData`**，設定：

| 參數 | 作用 |
|---|---|
| `type` | 交易對象為買方 / 賣方 / 買賣方 |
| `ExchangeMode` | **開立形式：交換 或 存證** |
| — | 以及交易對象的相關資訊 |

模式是綁在「交易對象」上的，不是每張發票各自指定。

### 端點

| 端點 | 功能 | 模式 |
|---|---|---|
| `Issue` → `IssueConfirm` | 開立 → 確認 | 確認僅交換模式 |
| `Invalid` → `InvalidConfirm` | 作廢 → 確認 | 確認僅交換模式 |
| `Reject` → `RejectConfirm` | 退回 → 確認 | 確認僅交換模式 |
| `Allowance` → `AllowanceConfirm` | 折讓 → 確認 | 確認僅交換模式 |
| `CancelAllowance` → `CancelAllowanceConfirm` | 取消折讓 → 確認 | 確認僅交換模式 |
| `VoidWithReIssue` | 作廢重開 | 共用 |
| `GetIssue` | 查詢開立 | 共用 |
| `AddInvoiceWordSetting` / `UpdateInvoiceWordStatus` | 字軌管理 | 共用 |
| `MaintainMerchantCustomerData` | **維護交易對象＋設定模式（前置必做）** | 共用 |
| `Notify` | 發送通知 | 共用 |

另有對應的查詢端點：查詢發票確認 / 作廢發票確認 / 退回發票確認 / 折讓發票確認 / 作廢折讓發票確認。

### `Notify` 發送通知 — `Data` 欄位

| 參數 | 名稱 | 型態 | 說明 |
|---|---|---|---|
| `*MerchantID` | 特店編號 | String(10) | |
| `*InvoiceDate` | 發票開立日期 | String(20) | `yyyy-mm-dd` |
| `*InvoiceNumber` | 發票號碼 | String(10) | |
| `AllowanceNo` | 折讓單編號 | String(16) | 固定 16 碼 |
| `*NotifyMail` | 發送信箱 | String(80) | 可多組，以**半形分號 `;`** 區隔 |
| `*InvoiceTag` | 發送內容類型 | String(1) | 見下表 |
| `*Notified` | 發送對象 | String(1) | `C`客戶 / `M`合作特店 / `A`皆發送 |

`InvoiceTag` **兩種模式取值範圍不同**：

| 模式 | 可用值 |
|---|---|
| 交換模式 | `1`發票開立 `2`發票作廢 `3`發票退回 `4`開立折讓 `5`作廢折讓 `6`開立發票確認 `7`作廢發票確認 `8`退回發票確認 `9`折讓確認 `10`作廢折讓確認 |
| 存證模式 | **僅** `1`發票開立 `2`發票作廢 `3`發票退回 `4`開立折讓 |

> ⚠️ **測試環境不會主動發送任何通知**。需登入廠商後台使用「補發通知」才會寄信到指定信箱。

### `Issue` 開立發票 — `Data` 欄位（B2B）

**B2B 的欄位與 B2C 差異很大，不能沿用**。最關鍵的差別是：B2B **必須自己算稅**（`SalesAmount` / `TaxAmount` / `TotalAmount` 三個金額分開帶），B2C 只帶一個含稅 `SalesAmount`。

| 參數 | 名稱 | 型態 | 說明 |
|---|---|---|---|
| `*MerchantID` | 特店編號 | String(10) | |
| `*RelateNumber` | 廠商自訂編號 | **String(20)** | 唯一不可重複。⚠️ **比 B2C 的 String(30) 短** |
| `InvoiceTime` | 發票開立時間 | String(20) | `yyyy-mm-dd hh:mm:ss`。**有值時僅接受過去 6 天內日期，且須順時順號**；建議不帶，由系統帶當下時間 |
| `*CustomerIdentifier` | 買方統編 | String(8) | **B2B 必填**（B2C 選填）|
| `CustomerEmail` | 買方信箱 | String(80) | 多組以半形分號區隔；未帶值自動帶入交易對象維護 API 設定的資料 |
| `CustomerAddress` | 買方公司地址 | String(100) | |
| `CustomerTelephoneNumber` | 買方電話 | String(30) | |
| `ClearanceMark` | 通關方式 | String(1) | `TaxType=2` 時必填，`1` 非經海關 / `2` 經海關 |
| `*InvType` | 字軌類別 | String(2) | `07` 一般稅額 / `08` 特種稅額 |
| `*TaxType` | 課稅別 | String(1) | `InvType=07` → `1`/`2`/`3`；`InvType=08` → `3`/`4`。**注意 B2B 沒有 B2C 的 `9`（混合）** |
| `ZeroTaxRateReason` | 零稅率原因 | String(2) | `TaxType=2` 必填，未帶預設 `71`。代碼同 B2C |
| `TaxRate` | 稅率 | Number | 非必填，系統自動：`TaxType=1`→`0.05`、`=2`→`0`、`=3`→`0`；**`=4` 不可填**（改設 `SpecialTaxType`）|
| `SpecialTaxType` | 特種稅額類別 | String(1) | `TaxType=3` 必填 `8`；`=4` 必填 `1`–`8`（稅率對應同 B2C）|
| `*Items` | 商品 | Array | |
| `*SalesAmount` | **銷售額合計** | Int | 整數，不可為 0。**須等於 `ItemAmount` 加總四捨五入至整數** |
| `*TaxAmount` | **稅額合計** | Int | 整數。**與「`SalesAmount` × `TaxRate` 四捨五入」的差距不可大於 2** |
| `*TotalAmount` | **發票金額** | Int | 整數，不可為 0。**須等於 `SalesAmount` + `TaxAmount`** |
| `InvoiceRemark` | 發票備註 | String(200) | |

`Items[]` 子欄位（與 B2C 不同）：

| 參數 | 名稱 | 型態 | 說明 |
|---|---|---|---|
| `*ItemSeq` | 明細排列序號 | Int | **`1`–`999`，且不可重複**（B2C 的 `ItemSeq` 非必填）|
| `*ItemName` | 商品名稱 | **String(256)** | B2C 為 String(100) |
| `*ItemCount` | 商品數量 | Number | 整數 8 位、小數 2 位 |
| `ItemWord` | 商品單位 | String(6) | **B2B 選填**（B2C 必填）|
| `*ItemPrice` | 商品價格 | Number | 整數 8 位、小數 7 位 |
| `*ItemAmount` | 商品合計 | Number | 整數 **12** 位、小數 7 位。與「`ItemCount` × `ItemPrice`」四捨五入的差距**不可大於 1** |
| `ItemTax` | 商品稅額 | Int | 與「`ItemAmount` × `TaxRate`」四捨五入的差距不可大於 1。**財政部無此欄位，僅供營業人自行檢核 `TaxAmount`，不會上傳**。特種稅額發票直接帶 `0` |
| `ItemRemark` | 商品備註 | String(200) | B2C 為 String(40) |

#### B2B 三個金額的容差規則（最容易被打回的地方）

| 檢核 | 容差 |
|---|---|
| `ItemAmount` vs `ItemCount × ItemPrice` | **≤ 1** |
| `ItemTax` vs `ItemAmount × TaxRate` | **≤ 1** |
| `SalesAmount` vs `Σ ItemAmount` 四捨五入 | 須相等 |
| `TaxAmount` vs `SalesAmount × TaxRate` 四捨五入 | **≤ 2** |
| `TotalAmount` vs `SalesAmount + TaxAmount` | 須相等 |

> 這套容差設計是為了容納各家系統的浮點捨入差異。實作時**不要**直接用浮點結果送出，先四捨五入成整數再比對這五條。

回應的 `Data` 含 `RtnCode`（`1` 成功）、`RtnMsg`、`InvoiceNumber`。

## 6. 離線電子發票 API

Base: `https://einvoice.opay.tw/B2CInvoice/`（與 B2C 共用網域，端點名有 `Offline` 前綴）

| 端點 | 功能 |
|---|---|
| `OfflineIssue` | 離線開立 |
| `OfflineInvalid` | 離線作廢 |
| `GetOfflineInvoiceWordSetting` | 查詢離線字軌設定 |
| `GetOfflineInvoiceWordSettingNumber` | 取得離線字軌號碼 |
| `GetOfflineInvoiceWordSettingWithAutoSplit` | 取得離線字軌（自動分段） |
| `GetOfflineMerchantInfo` | 查詢離線商家資訊 |
| `OfflineMerchantPosSetting` | POS 設定 |
| `QueryOfflineMerchantPosSetting` | 查詢 POS 設定 |

**應用場景**：實體門市 POS 在網路中斷時仍需開立發票。做法是**預先向平台批次取號**（`GetOfflineInvoiceWordSettingNumber`），本地端配號開立，恢復連線後再上傳。

### 兩種取號方式的差別

| 端點 | 回傳 | 適用 |
|---|---|---|
| `GetOfflineInvoiceWordSettingNumber` | **單一發票號碼**（含隨機碼與驗證資料）| 一次要一張 |
| `GetOfflineInvoiceWordSettingWithAutoSplit` | **一組號碼區間**（字軌 + 起訖號碼）| POS 端自行組成發票內容，**多台 POS 分段避免衝突** |

`WithAutoSplit` 取的是「營業人在廠商後台設定之自動配號」後的區間。若你的 POS 只需要知道可開立的區間、後續自行組裝電子發票內容，用這支即可。

### 取號回傳的關鍵欄位

| 參數 | 型態 | 說明 |
|---|---|---|
| `InvoiceNo` | String(10) | 發票號碼 |
| `RandomNumber` | String(4) | 電子發票證明聯上的 4 碼隨機碼。**同一字軌重複取號會回傳不同隨機碼** |
| `EncryptData` | String(24) | **發票號碼 10 碼 + 隨機碼 4 碼字串合併後 AES 加密再 Base64** |
| `Times` | Int | 同一字軌已取用次數 |
| `InvoiceHeader` | String(2) | 字軌英文字軌（如 `AA`、`KK`、`TW`）|

> `EncryptData` 是印在證明聯上供查驗的欄位，**不是你自己算的**——直接用平台回的值，別重算。
> 查無資料時，官方列出的原因是：**取字軌號碼時未授權於歐付寶，或字軌尚未取號完成**。

> 本 skill 已收錄的 provider 中，**PayNow 也有 POS 批次取號**（見 [PAYNOW_API_REFERENCE.md](PAYNOW_API_REFERENCE.md)）。若需求是實體門市，這兩家是目前有離線方案的選項。

## 7. 與其他加值中心的定位比較

| 面向 | O'Pay 歐付寶 | ECPay 綠界 | ezPay | Amego | SmilePay | PayNow |
|---|---|---|---|---|---|---|
| B2C | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| B2B 存證（含確認流程） | ✅ 完整 | 部分 | 部分 | ✅ | — | — |
| 離線 / POS 批次取號 | ✅ | — | — | — | — | ✅ |
| 文件公開 | ✅ 免登入 PDF | ✅ | 需帳號 | ✅ | ✅ | 部分 |
| 加密 | AES + 三層信封 | AES-128-CBC + 三層信封 | AES-256-CBC + Hex | MD5 簽章 | Verify_key | JWT |

## 8. 已知限制與待補

### 官方不公開的部分

**錯誤碼表無公開版本。** opay_i100.pdf 附錄 1 原文：

> 因錯誤代碼一直在新增，詳細的錯誤代碼，請到廠商後台 → 電子發票後台 → 系統開發管理 → 錯誤代碼查詢。

亦即**必須有商家帳號才拿得到完整錯誤碼**。本文件已收錄從各端點章節反推出的 `RtnCode`：`1`（成功）、`4000003`（延後開立成功）、`4000004`（開立成功）。

### 仍待補

| 項目 | 狀態 |
|---|---|
| B2B 其餘端點（`Invalid`／`Reject`／`Allowance` 與各 `Confirm`）逐欄 | `Issue` 已完成；其餘端點欄位待擷取 |
| 離線 POS 其餘端點（`OfflineIssue`／`OfflineInvalid`／POS 設定）逐欄 | 取號流程已完成；其餘待擷取 |
| 完整錯誤碼 | **需商家帳號**，公開文件不提供 |
| 歐付寶**物流** API | 未出現在官方文件總覽頁，端點待確認 |

原始 PDF 已存於 `_studies/opay/`（含抽出的純文字），可直接再解析。

## 9. 來源

- B2C 電子發票 API — https://developers.opay.tw/Content/Doc/opay_i100.pdf
- B2B 電子發票 API — https://developers.opay.tw/Content/Doc/opay_i200.pdf
- 離線電子發票 API — https://developers.opay.tw/Content/Doc/opay_i301.pdf
- 文件總覽 — https://developers.opay.tw/download/document
- 金流端 — [../../taiwan-payment/references/opay-payment-api.md](../../taiwan-payment/references/opay-payment-api.md)
