# 歐付寶 O'Pay 電子發票 API 參考

> Source:《歐付寶電子發票 B2C API》(opay_i100.pdf, 145 頁)、《B2B API》(opay_i200.pdf, 130 頁)、《離線電子發票 API》(opay_i301.pdf, 52 頁)
> 文件總覽: https://developers.opay.tw/download/document
> 文件公開程度：public（PDF 免登入直連下載）

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

依 opay_i200.pdf（V1.2.0，2025-09-10）章節順序；頁碼為文件頁碼。

| 端點 | 功能 | 頁 |
|---|---|---|
| `MaintainMerchantCustomerData` | **維護交易對象＋設定模式（前置必做）** | 6 |
| `Notify` | 發送通知 | 9 |
| `AddInvoiceWordSetting` / `UpdateInvoiceWordStatus` / `GetInvoiceWordSetting` | 新增字軌 / 設定字軌狀態 / 查詢字軌 | 13 / 16 / 121 |
| `Issue` → `IssueConfirm` | 開立 → 開立確認 | 19 / 27 |
| `Invalid` → `InvalidConfirm` | 作廢 → 作廢確認 | 31 / 36 |
| `Reject` → `RejectConfirm` | 退回 → 退回確認 | 40 / 44 |
| `Allowance` → `AllowanceConfirm` | 開立折讓 → 折讓確認 | 48 / 54 |
| `CancelAllowance` → `CancelAllowanceConfirm` | 作廢折讓 → 作廢折讓確認 | 58 / 63 |
| `VoidWithReIssue` | 註銷重開（發票號碼、開立時間不變） | 66 |
| `GetIssue` / `GetIssueConfirm` | 查詢發票 / 查詢發票確認 | 75 / 82 |
| `GetInvalid` / `GetInvalidConfirm` | 查詢作廢 / 查詢作廢確認 | 87 / 91 |
| `GetReject` / `GetRejectConfirm` | 查詢退回 / 查詢退回確認 | 95 / 99 |
| `GetAllowance` / `GetAllowanceConfirm` | 查詢折讓 / 查詢折讓確認 | 103 / 109 |
| `GetAllowanceInvalid` / `GetAllowanceInvalidConfirm` | 查詢作廢折讓 / 查詢作廢折讓確認 | 113 / 117 |
| `GetCompanyNameByTaxID` | 統一編號驗證（回公司名稱） | 125 |

`*Confirm` 由交易相對人呼叫，僅交換模式需要。作廢、退回、折讓送出後由歐付寶暫存，**隔日**上傳財政部；交換模式要等相對人確認才完成交換。

### `MaintainMerchantCustomerData` 交易對象維護 — `Data` 欄位

| 參數 | 名稱 | 型態 | 說明 |
|---|---|---|---|
| `*MerchantID` | 特店編號 | String(10) | |
| `*Action` | 動作 | String(10) | `Add` 新增 / `Update` 編輯 / `Delete` 刪除 |
| `CustomerNumber` | 公司編號 | String(20) | 可與統編相同 |
| `*Identifier` | 統一編號 | String(8) | 設定後不可變更 |
| `*type` | 交易對象 | String(1) | `1` 買方 / `2` 賣方 / `3` 買賣方 |
| `*CompanyName` | 公司名稱 | String(60) | |
| `PersonInCharge` | 負責人 | String(30) | |
| `Address` / `TelephoneNumber` / `FacsimileNumber` | 地址 / 電話 / 傳真 | String(100) / (30) / (30) | |
| `*TradingSlang` | 交易暗語 | String(20) | |
| `*ExchangeMode` | 開立形式 | String(1) | `0` 存證 / `1` 交換。交換須先至財政部平台設定由歐付寶接收 |
| `*EmailAddress` | 公司信箱 | String(80) | 多組以半形分號區隔 |
| `SalesName` / `ContactAddress` | 業務負責人 / 聯絡地址 | String(30) / (100) | |

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

回應的 `Data` 含 `RtnCode`（`1` 成功）、`RtnMsg`、`InvoiceNumber`（失敗時為空）、`RandomNumber` String(4)。

以下端點回應 `Data` 皆含 `RtnCode`（`1` 成功）與 `RtnMsg` String(200)，另有欄位才列出。

### 確認：`IssueConfirm` / `InvalidConfirm` / `RejectConfirm`

| 參數 | 名稱 | 型態 | 說明 |
|---|---|---|---|
| `*MerchantID` | 特店編號 | String(10) | |
| `*InvoiceNumber` | 發票號碼 | String(10) | |
| `InvoiceDate` | 發票開立日期 | String(20) | `yyyy-mm-dd`。`IssueConfirm` 選填，另兩支必填 |
| `Remark` | 備註 | String(200) | |

### 作廢 `Invalid` / 退回 `Reject`

| 參數 | 名稱 | 型態 | 說明 |
|---|---|---|---|
| `*MerchantID` | 特店編號 | String(10) | |
| `*InvoiceNumber` | 發票號碼 | String(10) | |
| `*InvoiceDate` | 發票開立日期 | String(20) | `yyyy-mm-dd` |
| `*Reason` | 作廢／退回原因 | String(20) | |
| `Remark` | 備註 | String(200) | |

存證模式須先與交易相對人達成合意再送出。退回用於收到內容錯誤（數量、單價、品名）的發票時拒收。

### `Allowance` 開立折讓 — `Data` 欄位

一張折讓單可同時折讓多張發票。

| 參數 | 名稱 | 型態 | 說明 |
|---|---|---|---|
| `*MerchantID` | 特店編號 | String(10) | |
| `AllowanceDate` | 折讓單時間 | String(20) | `yyyy-mm-dd hh:mm:ss`；有值僅接受 6 天內，未帶為當下 |
| `CustomerEmail` | 買方信箱 | String(80) | 多組以半形分號區隔；未帶自動帶入交易對象設定 |
| `CustomerAddress` | 買方地址 | String(100) | |
| `*TaxAmount` | 營業稅額 | Int | 與「`TotalAmount` × 原發票 `TaxRate`」四捨五入的差距 ≤ 2；僅含特種稅額帶 `0` |
| `*TotalAmount` | 折讓金額總計（未稅） | Int | 不可為 0；須等於 `Details[].ItemAmount` 加總四捨五入 |
| `*Details` | 折讓明細 | Array | |

`Details[]`：

| 參數 | 名稱 | 型態 | 說明 |
|---|---|---|---|
| `*OriginalInvoiceNumber` | 原發票號碼 | String(10) | |
| `*OriginalInvoiceDate` | 原發票日期 | String(20) | `yyyy-mm-dd` |
| `*OriginalSequenceNumber` | 原發票商品序號 | Int | `1`–`999`，須與原發票商品排序相同 |
| `*ItemName` | 商品名稱 | String(256) | 須與原發票對應商品名稱相同 |
| `*ItemCount` | 數量 | Number | 整數 8 位、小數 2 位；不可超過原開立數量 |
| `*ItemPrice` | 價格 | Number | 整數 8 位、小數 7 位；不可超過原開立價格 |
| `*ItemAmount` | 合計 | Number | 整數 12 位、小數 7 位；與 `ItemCount × ItemPrice` 差距 ≤ 1 |
| `Tax` | 商品稅額 | Int | 與「`ItemAmount` × 原發票 `TaxRate`」四捨五入差距 ≤ 1；特種稅額帶 `0` |

回應另含 `AllowanceNo` String(16)（歐付寶折讓編號，失敗為空）、`AllowanceNumber` String(16)（折讓單號碼）。後續折讓相關端點都以 `AllowanceNo` 識別。

### `AllowanceConfirm` / `CancelAllowance` / `CancelAllowanceConfirm`

| 參數 | 名稱 | 型態 | 說明 |
|---|---|---|---|
| `*MerchantID` | 特店編號 | String(10) | |
| `*AllowanceNo` | 歐付寶折讓編號 | String(16) | 固定 16 碼 |
| `*Reason` | 折讓作廢原因 | String(20) | **僅 `CancelAllowance`** |
| `Remark` | 備註 | String(200) | |

### `VoidWithReIssue` 註銷重開

發票號碼與開立時間不可更改。歐付寶先上傳註銷，財政部回覆成功後再上傳開立。`Data` 分兩層：

| 參數 | 型態 | 說明 |
|---|---|---|
| `*MerchantID` | String(10) | |
| `*VoidModel.InvoiceNumber` | String(10) | |
| `*VoidModel.VoidReason` | String(20) | |
| `*IssueModel.RelateNumber` | String(50) | 帶原發票自訂編號；僅限中英數 |
| `*IssueModel.InvoiceTime` | String(20) | 須為原開立時間，`yyyy-MM-dd HH:mm:ss` 或 `yyyy/MM/dd HH:mm:ss` |
| `IssueModel` 其餘欄位 | | 同 `Issue`：`CustomerIdentifier`、`CustomerAddress`、`CustomerTelephoneNumber` String(26)、`CustomerEmail` String(200)、`ClearanceMark`、`InvType`、`TaxType`、`ZeroTaxRateReason`、`SpecialTaxType`、`SalesAmount`、`TaxAmount`、`TotalAmount`、`InvoiceRemark`、`Items[]`（最多 999 項） |

與 `Issue` 的差異：
- `ZeroTaxRateReason`：**自 115 年 1 月 1 日起**零稅率必填，或須在廠商後台設定，否則開立失敗（`Issue` 章節寫未帶預設 `71`）。
- `Items[].ItemPrice` 整數最多 10 位、固定填未稅價；`ItemCount` 小數 7 位；`ItemRemark` String(120)。
- 官方表格 `Items[].ItemName` 標 String(2)，與 `Issue` 的 String(256) 不一致，範例值為 `item01`，以實測為準。

回應另含 `InvoiceNumber`、`RandomNumber`。

### 查詢端點

`GetIssue` / `GetInvalid` / `GetReject` / `GetIssueConfirm` / `GetInvalidConfirm` / `GetRejectConfirm`：

| 參數 | 型態 | 說明 |
|---|---|---|
| `*MerchantID` | String(10) | |
| `*InvoiceCategory` | Int | `0` 銷項（特店開出）/ `1` 進項（相對人開給特店） |
| `InvoiceNumber` | String(10) | 與 `RelateNumber` 擇一（`GetIssue` 必填） |
| `InvoiceDate` | String(20) | `yyyy-mm-dd`；`InvoiceNumber` 有值時必填（`GetIssue` 必填） |
| `RelateNumber` | String(20) | 與 `InvoiceNumber` 擇一 |

`GetIssueConfirm` 另可帶篩選條件：`Seller_Identifier`、`Buyer_Identifier`、`InvoiceDateBegin`／`InvoiceDateEnd`、`InvoiceNumberBegin`／`InvoiceNumberEnd`（8 碼不含字軌）、`Issue_Status`（`1` 開立 / `0` 退回）、`Invalid_Status`、`ExchangeMode`、`ExchangeStatus`、`Upload_Status`（`0` 未上傳 / `1` 已上傳 / `2` 上傳失敗）。

`GetAllowance` / `GetAllowanceConfirm` / `GetAllowanceInvalid` / `GetAllowanceInvalidConfirm`：`*MerchantID`、`*AllowanceNo`。

結果在回應的 `RtnData`：

| 端點 | `RtnData` 主要欄位 |
|---|---|
| `GetIssue` | 買賣方資料（`Buyer_*`／`Seller_*`，銷項時 `Seller_*` 為空）、`InvoiceType`、`TaxType`、`TaxRate`、`SalesAmount`、`TaxAmount`、`TotalAmount`、`Issue_Status`、`Upload_Status`、`Upload_Date`、`ConfirmDate`、`Invalid_Status`、`ExchangeMode`、`ExchangeStatus`、`BalanceAmount`（剩餘可折讓金額）、`RandomNumber`、`Items[]` |
| `GetInvalid` / `GetReject` | `CancelDate`／`RejectDate`、原因、`Upload_Status`、`ConfirmDate`、`ExchangeStatus`、`Remark` |
| `*Confirm` 查詢 | 買賣方統編、日期、`ConfirmDate`、`Upload_Status`、`Upload_Date`、`ConfirmRemark` |
| `GetAllowance` | `AllowanceNo`、`AllowanceNumber`、`AllowanceType`、買賣方資料、`AllowanceDate`、`TotalAmount`、`TaxAmount`、`Upload_Status`、`ConfirmDate`、`Invalid_Status`、`ExchangeStatus`、`Items[]`（原發票號碼／日期／序號、`Quantity`、`UnitPrice`、`Tax`、`Amount`、`BalanceAmount`） |

### 字軌管理

| 端點 | `Data` 欄位 | 回應 |
|---|---|---|
| `AddInvoiceWordSetting` | `*InvoiceTerm` Int（`1`–`6` 對應 1-2 月…11-12 月）、`*InvoiceYear` String(3)（民國年，僅當年與明年）、`*InvType`（`07`/`08`）、`*InvoiceCategory` 固定 `2`、`*InvoiceHeader` String(2)、`*InvoiceStart` String(8)（尾數 `00`/`50`）、`*InvoiceEnd` String(8)（尾數 `49`/`99`） | `TrackID` String(10)，設定狀態時要用 |
| `UpdateInvoiceWordStatus` | `*TrackID`、`*InvoiceStatus` Int（`0` 停用 / `1` 暫停 / `2` 啟用；停用後該區間無法上傳發票） | |
| `GetInvoiceWordSetting` | `*InvoiceYear`（去年～明年）、`*InvoiceTerm`（`0` 全部）、`*UseStatus`（`0` 全部 / `1` 未啟用 / `2` 使用中 / `3` 已停用 / `4` 暫停中 / `5` 待審核 / `6` 審核不通過）、`*InvoiceCategory` 固定 `2`、`InvType`、`InvoiceHeader` | `InvoiceInfo[]`：`TrackID`、起訖號碼、`InvoiceNo`（目前已使用號碼）、`UseStatus`、`InvoiceLastDate` |

### `GetCompanyNameByTaxID` 統一編號驗證

`Data`：`*MerchantID`、`*UnifiedBusinessNo` String(8)（僅數字）。回應另含 `CompanyName` String(60)。

## 6. 離線電子發票 API

依 opay_i301.pdf（V1.3.0，2025-09-10）；頁碼為文件頁碼。

Base: `https://einvoice.opay.tw/B2CInvoice/`（與 B2C 共用網域）

適用於有實體發票機台、無法隨時連線的特店：特店自行開立，再上傳歐付寶代傳財政部。

### 流程

1. `OfflineMerchantPosSetting` 設定發票機台 ID（或在廠商後台設定）
2. `GetGovInvoiceWordSetting` 查財政部配號結果 → `AddInvoiceWordSetting` 設定字軌區間並綁機台 → `UpdateInvoiceWordStatus` 啟用
3. 取號（三擇一，見下）
4. 自行開立，`OfflineIssue` 上傳；作廢以 `OfflineInvalid` 上傳

**上傳期限**：發票開立時間不可超過下一期的 15 號（例：9-10 月的發票須在 11 月 15 日前上傳）。

### 端點

| 端點 | 功能 | 頁 |
|---|---|---|
| `GetOfflineMerchantInfo` | 查詢特店基本資料 | 5 |
| `GetGovInvoiceWordSetting` | 查詢財政部配號結果 | 8 |
| `OfflineMerchantPosSetting` / `QueryOfflineMerchantPosSetting` | 管理 / 查詢發票機台 | 11 / 14 |
| `AddInvoiceWordSetting` / `UpdateInvoiceWordStatus` / `GetInvoiceWordSetting` | 新增字軌 / 設定字軌狀態 / 查詢字軌 | 17 / 20 / 44 |
| `GetOfflineInvoiceWordSettingWithAutoSplit` | 取得自動配發的字軌號碼區間 | 23 |
| `GetOfflineInvoiceWordSetting` | 取得字軌號碼區間 | 26 |
| `GetOfflineInvoiceWordSettingNumber` | 取得字軌號碼清單（含隨機碼、加密資料） | 29 |
| `OfflineIssue` | 上傳開立發票 | 32 |
| `OfflineInvalid` | 上傳作廢發票 | 41 |

回應 `Data` 皆含 `RtnCode`（`1` 成功）與 `RtnMsg`，另有欄位才列出。

### 特店、配號、機台

| 端點 | `Data` 欄位 | 回應 |
|---|---|---|
| `GetOfflineMerchantInfo` | `*MerchantID` | `MerchantName`、`MerchantIdentifier` |
| `GetGovInvoiceWordSetting` | `*MerchantID`、`*InvoiceYear` String(3)（民國年，去年～明年） | `InvoiceInfo[]`：`InvoiceTerm`、`InvType`、`InvoiceHeader`、`InvoiceStart`、`InvoiceEnd`、`Number`（本數，一本 50 號）。查無資料可能是取字軌時未授權於歐付寶，或字軌尚未取號完成 |
| `OfflineMerchantPosSetting` | `*ActionType` Int（`1` 新增 / `2` 修改 / `3` 刪除）、`*MachineID` String(10)（勿用特殊符號；已設定字軌的機台不可改 ID 或刪除）、`Remark` String(100) | |
| `QueryOfflineMerchantPosSetting` | `*MerchantID` | `MachineIDList[]`：`MachineID`、`CreateTime`、`Remark` |

### 字軌

| 端點 | `Data` 欄位 | 回應 |
|---|---|---|
| `AddInvoiceWordSetting` | 同 B2B 版，但 `*InvoiceCategory` 固定 `4`（離線），另加 `*MachineID` | `TrackID` |
| `UpdateInvoiceWordStatus` | `*TrackID`、`*InvoiceStatus`（`0` 停用 / `1` 暫停 / `2` 啟用） | |
| `GetInvoiceWordSetting` | 同 B2B 版，`*InvoiceCategory` 固定 `4` | `InvoiceInfo[]`，另含 `MachineID` |

### 取號：三支擇一

| 端點 | `Data` 欄位 | 回傳 | 適用 |
|---|---|---|---|
| `GetOfflineInvoiceWordSettingWithAutoSplit` | `*MerchantID`、`*InvoiceYear`、`*InvoiceTerm`、`*MachineID`、`*InvType` | `InvoiceHeader`、`InvoiceStart`、`InvoiceEnd` | 取廠商後台設定之自動配號後的區間 |
| `GetOfflineInvoiceWordSetting` | `*MerchantID`、`*InvoiceYear`、`*InvoiceTerm`、`*InvoiceStatus`（`1` 啟用 / `2` 備用字軌）、`*MachineID` | `InvoiceHeader`、`InvoiceStart`、`InvoiceEnd`、`InvoiceStatus`、`Times`（同字軌已取次數） | 只需要可開立區間，發票內容自行組成 |
| `GetOfflineInvoiceWordSettingNumber` | 同上 | `InvoiceInfo[]`：`InvoiceNo` String(10)、`RandomNumber` String(4)、`EncryptData` String(24)、`Times` | 開立裝置**無法自行產生 QRCode 所需 AES 加密資料**時 |

- `EncryptData`：發票號碼 10 碼 + 隨機碼 4 碼合併後 AES 加密，再 Base64。
- 同一字軌重複取號，回傳的隨機碼不同。
- 上傳時的 `RandomNumber` 要用實際開立的隨機碼；取號 API 給的隨機碼僅供參考。

### `OfflineIssue` 上傳開立發票 — `Data` 欄位

| 參數 | 名稱 | 型態 | 說明 |
|---|---|---|---|
| `*MerchantID` | 特店編號 | String(10) | |
| `*MachineID` | 發票機台 ID | String(10) | |
| `*InvoiceNo` | 發票號碼 | String(10) | 2 碼字軌 + 8 碼數字 |
| `*InvoiceDate` | 開立時間 | String(20) | `yyyy-MM-dd HH:mm:ss`，不可晚於上傳當下 |
| `*RelateNumber` | 特店自訂編號 | String(30) | 唯一，不可用特殊符號 |
| `*TaxType` | 課稅類別 | String(1) | `1` 應稅 / `2` 零稅率 / `3` 免稅 / `4` 特種應稅 / `9` 混合（限收銀機無法分辨且經申請核可） |
| `ZeroTaxRateReason` | 零稅率原因 | String(2) | 自 115 年 1 月 1 日起，`TaxType=2` 或 `9` 時必填或須在廠商後台設定；`71`–`79`，預設 `71` |
| `*SalesAmount` | 發票總金額（含稅） | Int | |
| `*InvType` | 字軌類別 | String(2) | `07` / `08` |
| `*RandomNumber` | 隨機碼 | String(4) | 僅數字、不可用流水號；建議每一萬張不重複 |
| `*Items` | 商品 | Array | 最多 200 項 |
| `CustomerIdentifier` | 統編 | String(8) | |
| `CustomerID` / `CustomerName` | 客戶編號 / 名稱 | String(20) / (60) | |
| `CustomerAddr` / `CustomerPhone` / `CustomerEmail` | 地址 / 手機 / 信箱 | String(100) / (20) / (80) | |
| `ClearanceMark` | 通關方式 | String(1) | `TaxType=2` 必填：`1` 非經海關 / `2` 經海關 |
| `SpecialTaxType` | 特種稅額類別 | String(1) | `TaxType` 為 `1`/`2`/`9` 帶 `0`；`3` 帶 `8`；`4` 帶 `1`–`8` |
| `vat` | 商品單價是否含稅 | String(1) | 文件未列值 |
| `InvoiceRemark` | 發票備註 | String(200) | |
| `*Print` | 列印註記 | String(1) | `0` 不列印（捐贈或有載具時）/ `1` 列印（有統編時） |
| `*Donation` | 捐贈註記 | String(1) | `0` 不捐贈（有統編或載具時）/ `1` 捐贈 |
| `LoveCode` | 捐贈碼 | String(7) | 捐贈時必填，3–7 碼數字 |
| `CarrierType` | 載具類別 | String(1) | 空字串無載具；`1` 歐付寶載具 / `2` 自然人憑證 / `3` 手機條碼 / `4` 悠遊卡 / `5` icash / `6` 一卡通 / `7` 金融卡 / `8` 信用卡 |
| `CarrierNum` | 載具編號 | String(64) | `1` 帶空字串（系統帶客戶信箱或手機）；`2` 2 碼大寫英文 + 14 碼數字；`3` `/` + 7 碼；`4`–`7` 卡片隱碼（內碼）；`8` 信用卡加密卡號 |
| `CarrierNum2` | 第二載具編號 | String(64) | `4`–`7` 必填卡片顯碼；`8` 必填刷卡日期（民國年月日 7 碼）+ 金額（10 碼左補 0）；`1`–`3` 勿帶（會被系統阻擋） |

`Items[]`：`ItemSeq` Int、`*ItemName` String(100)、`*ItemCount` Number、`*ItemWord` String(6)、`*ItemPrice` Number、`ItemTaxType` String(1)、`*ItemAmount` Number、`ItemRemark` String(40)。

回應另含 `InvoiceNo`、`RelateNumber`。

### `OfflineInvalid` 上傳作廢發票 — `Data` 欄位

| 參數 | 型態 | 說明 |
|---|---|---|
| `*MerchantID` | String(10) | |
| `*InvoiceNo` | String(10) | 字軌 + 號碼 |
| `*InvoiceDate` | String(20) | 開立日期 `yyyy-MM-dd` |
| `*Reason` | String(20) | 作廢原因 |
| `*CancelDate` | String(20) | 作廢時間 `yyyy-MM-dd HH:mm:ss` |

回應另含 `InvoiceNo`（成功時回傳，失敗為空）。

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

亦即**必須有商家帳號才拿得到完整錯誤碼**。B2B（opay_i200.pdf 附錄 1）與離線（opay_i301.pdf 附錄 1）同樣只指向廠商後台。本文件已收錄從各端點章節反推出的 `RtnCode`：`1`（成功）、`4000003`（延後開立成功）、`4000004`（開立成功）。

**沒有物流 API。** 官方文件總覽（修訂於 2026-09-21，2026-09-24 查核）只列金流、電子發票、Open ID、平台綁定、直播主收款網址。

### 仍待補

| 項目 | 狀態 |
|---|---|
| 完整錯誤碼 | **需商家帳號**（廠商後台 → 電子發票後台 → 系統開發管理 → 錯誤代碼查詢） |
| 離線 `OfflineIssue` 的 `vat`、`Items[].ItemTaxType` 取值 | 規格書只列欄位名，未列值 |
| B2B `VoidWithReIssue` 的 `Items[].ItemName` 長度 | 規格書標 String(2)，與 `Issue` 的 String(256) 不一致 |

原始 PDF 已存於 `_studies/opay/`（含抽出的純文字），可直接再解析。

## 9. 來源

- B2C 電子發票 API — https://developers.opay.tw/Content/Doc/opay_i100.pdf
- B2B 電子發票 API — https://developers.opay.tw/Content/Doc/opay_i200.pdf
- 離線電子發票 API — https://developers.opay.tw/Content/Doc/opay_i301.pdf
- 文件總覽 — https://developers.opay.tw/download/document
- 金流端 — [../../taiwan-payment/references/opay-payment-api.md](../../taiwan-payment/references/opay-payment-api.md)
