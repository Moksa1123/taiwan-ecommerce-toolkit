# 綠界科技電子發票 API 完整技術規格 (ECPay Invoice API)

> 官方文檔來源：https://developers.ecpay.com.tw/
> GitHub SDK：https://github.com/ECPay/SDK_PHP
> 支援 B2C (二聯式) 與 B2B (三聯式) 電子發票

---

## 目錄
1. [基本說明](#基本說明)
2. [參數加密方式](#參數加密方式-checkmacvalue)
3. [B2C 電子發票](#b2c-電子發票二聯式)
4. [B2B 電子發票](#b2b-電子發票三聯式)
5. [發票列印](#發票列印)
6. [錯誤代碼](#錯誤代碼)

---

## 基本說明

### 環境資訊
| 環境 | 說明 | URL 前綴 |
|------|------|---------|
| **測試環境** | 測試用，不會上傳財政部 | `https://einvoice-stage.ecpay.com.tw` |
| **正式環境** | 正式開立，上傳財政部 | `https://einvoice.ecpay.com.tw` |

### 測試環境資料
| 項目 | 測試值 |
|------|--------|
| **特店編號 (MerchantID)** | `2000132` |
| **HashKey** | `ejCk326UnaZWKisg` |
| **HashIV** | `q9jcZX8Ib9LM8wYk` |
| **廠商後台** | `https://vendor-stage.ecpay.com.tw`（帳號 `Stagetest1234`／密碼 `test1234`／統編 `53538851`） |
| **平台商 PlatformID** | `3085340`（HashKey `HwiqPsywG1hLQNuN`、HashIV `YqITWD4TyKacYXpn`；已綁定子廠商 `2000132`） |

測試環境開立並經綠界檢核成功後，發票狀態直接壓為「已上傳」，不實際上傳財政部（/7849）。
正式環境金鑰在正式廠商後台「系統設定 → 系統介接設定 → 介接資訊」取得。

### API 編碼格式
- **Content-Type**：`application/json`
- **字元編碼**：`UTF-8`
- **傳輸方式**：`POST`（JSON 格式）

---

## 參數加密方式 (CheckMacValue)

綠界採用 **AES 加密** + **URL Encode** 的方式保護傳輸資料。

### 加密步驟

#### 1. 準備 Data JSON 資料
```json
{
    "MerchantID": "2000132",
    "RelateNumber": "TEST20240101001",
    "CustomerIdentifier": "12345678",
    "InvType": "07",
    "TaxType": "1",
    "SalesAmount": 9524,
    "TaxAmount": 476,
    "TotalAmount": 10000,
    "Items": [
        {
            "ItemSeq": 1,
            "ItemName": "測試商品",
            "ItemCount": 1,
            "ItemPrice": 9524,
            "ItemAmount": 9524,
            "ItemTax": 476
        }
    ]
}
```

#### 2. URL Encode
將 JSON 字串進行 URL Encode（大寫格式）：
```
%7B%22MerchantID%22%3A%222000132%22%2C...
```

#### 3. AES 加密
**加密設定：**
- **演算法**：AES-128-CBC
- **金鑰**：HashKey (`ejCk326UnaZWKisg`)
- **IV**：HashIV (`q9jcZX8Ib9LM8wYk`)
- **Padding**：PKCS7

**加密範例（Node.js）：**
```javascript
const crypto = require('crypto')

function encryptData(data, hashKey, hashIV) {
    // 1. JSON 轉字串並 URL Encode
    const jsonString = JSON.stringify(data)
    const urlEncoded = encodeURIComponent(jsonString)

    // 2. AES 加密
    const cipher = crypto.createCipheriv('aes-128-cbc', hashKey, hashIV)
    let encrypted = cipher.update(urlEncoded, 'utf8', 'base64')
    encrypted += cipher.final('base64')

    return encrypted
}

// 範例
const hashKey = 'ejCk326UnaZWKisg'
const hashIV = 'q9jcZX8Ib9LM8wYk'
const data = { MerchantID: '2000132', RelateNumber: 'TEST001' }
const encryptedData = encryptData(data, hashKey, hashIV)
```

#### 4. 解密步驟
```javascript
function decryptData(encryptedData, hashKey, hashIV) {
    // 1. AES 解密
    const decipher = crypto.createDecipheriv('aes-128-cbc', hashKey, hashIV)
    let decrypted = decipher.update(encryptedData, 'base64', 'utf8')
    decrypted += decipher.final('utf8')

    // 2. URL Decode
    const urlDecoded = decodeURIComponent(decrypted)

    // 3. 解析 JSON
    return JSON.parse(urlDecoded)
}
```

---

## B2C 電子發票（二聯式）

端點前綴 `https://einvoice(-stage).ecpay.com.tw/B2CInvoice/`；請求外層 `MerchantID` + `RqHeader` + `Data`（AES 加密）。
開立對象是營業人（打統編）也走 B2C API，不需另接 B2B（/24230 注意事項）。

### API 一覽

| 功能 | 端點 | 官方頁 |
|------|------|--------|
| 查詢財政部配號結果 | `GetGovInvoiceWordSetting` | /7859 |
| 字軌與配號設定 | `AddInvoiceWordSetting` | /7870 |
| 設定字軌號碼狀態 | `UpdateInvoiceWordStatus` | /7875 |
| 查詢字軌 | `GetInvoiceWordSetting` | /7881 |
| 手機條碼驗證 | `CheckBarcode` | /7886 |
| 捐贈碼驗證 | `CheckLoveCode` | /7891 |
| 統一編號驗證 | `GetCompanyNameByTaxID` | /32089 |
| 開立發票 | `Issue` | /7896 |
| 延遲開立（預約開立） | `DelayIssue` | /15369 |
| 編輯延遲開立 | `EditDelayIssue` | /47979 |
| 觸發開立 | `TriggerIssue` | /15371 |
| 取消延遲開立 | `CancelDelayIssue` | /15382 |
| 開立折讓（紙本） | `Allowance` | /7901 |
| 線上開立折讓（通知開立） | `AllowanceByCollegiate` | /15391 |
| 作廢發票 | `Invalid` | /7906 |
| 作廢折讓 | `AllowanceInvalid` | /7911 |
| 取消線上折讓 | `AllowanceInvalidByCollegiate` | /7913 |
| 註銷重開 | `VoidWithReIssue` | /7918 |
| 查詢發票明細 | `GetIssue` | /7923 |
| 查詢特定多筆發票 | `GetIssueList` | /17229 |
| 查詢折讓明細 | `GetAllowanceList` | /7928 |
| 查詢作廢發票明細 | `GetInvalid` | /7933 |
| 查詢作廢折讓明細 | `GetAllowanceInvalid` | /7943 |
| 發送發票通知 | `InvoiceNotify` | /7938 |
| 發票列印 | `InvoicePrint` | /7949 |

### 1. 開立發票 `Issue`

#### 請求參數（最外層）

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `PlatformID` | String(10) | | 特約合作平台商代號，一般廠商放空值 |
| `MerchantID` | String(10) | Y | 特店編號 |
| `RqHeader.Timestamp` | Number | Y | Unix 時間戳，10 分鐘內有效 |
| `RqHeader.Revision` | String | | 官方參數頁只列 `Timestamp`；官方 SDK 與外掛帶 `3.0.0` |
| `Data` | String | Y | JSON → URL Encode → AES 加密 |

#### Data 欄位（/7896）

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `MerchantID` | String(10) | Y | 特店編號 |
| `RelateNumber` | String(50) | Y | 特店自訂編號，不可重複；勿用特殊符號；英文不分大小寫 |
| `ChannelPartner` | String(1) | | 通路商編號：`1` 蝦皮 |
| `CustomerID` | String(20) | | 客戶編號 |
| `ProductServiceID` | String(10) | | 產品服務別代號；需先啟用「B2C 系統多組字軌」，否則忽略 |
| `CustomerIdentifier` | String(8) | | 統一編號，8 碼數字；一般消費者放空字串（**不是** `0000000000`） |
| `CustomerName` | String(60) | 條件 | `Print=1` 時必填；有統編時帶營業人名稱 |
| `CustomerAddr` | String(100) | 條件 | `Print=1` 時必填 |
| `CustomerPhone` | String(20) | 條件 | 與 `CustomerEmail` 擇一必填 |
| `CustomerEmail` | String(80) | 條件 | 與 `CustomerPhone` 擇一必填；**僅限一組** |
| `ClearanceMark` | String(1) | 條件 | `TaxType` 為 2 或 9（含零稅率）時必填：`1` 非經海關出口、`2` 經海關出口 |
| `Print` | String(1) | Y | `0` 不列印、`1` 列印；捐贈時帶 `0`；有統編且無載具帶 `1`，載具 1/2 帶 `0`，載具 3 可 0 或 1 |
| `Donation` | String(1) | Y | `0` 不捐贈、`1` 捐贈；有統編時帶 `0` |
| `LoveCode` | String(7) | 條件 | 捐贈時必填，3–7 碼數字 |
| `CarrierType` | String(1) | | `1` 綠界載具、`2` 自然人憑證、`3` 手機條碼、`4` 悠遊卡、`5` 一卡通；空字串為無載具 |
| `CarrierNum` | String(64) | 條件 | 載具 1 帶空字串（系統自動帶入）；2 為 2 碼大寫英文 + 14 碼數字；3 為 `/` + 7 碼；4、5 帶卡片隱碼 |
| `CarrierNum2` | String(64) | 條件 | 載具 4、5 必填，帶卡片顯碼；其他載具不可帶 |
| `TaxType` | String(1) | Y | `InvType=07`：`1` 應稅、`2` 零稅率、`3` 免稅、`9` 混合（需申請）；`InvType=08`：`3`、`4` 特種應稅 |
| `ZeroTaxRateReason` | String(2) | 條件 | 自 115 年 1 月 1 日起，零稅率（2 或 9）必填或於後台設定，值見下方代碼表 |
| `SpecialTaxType` | Number | 條件 | `TaxType=3` 帶 `8`；`TaxType=4` 帶 `1`–`8`；1/2/9 系統自動帶 `0` |
| `SalesAmount` | Number | Y | **發票總金額（含稅）**，整數最多 12 位，須等於 `ItemAmount` 加總四捨五入 |
| `TaxAmount` | Number | | 稅額合計；未填由綠界計算，自行帶入時差距不得超過 1 元；特種稅額帶 `0` |
| `InvoiceRemark` | String(200) | | 發票備註 |
| `Items[]` | Array | Y | 最多 999 項 |
| `Items[].ItemSeq` | Int | | 商品序號 |
| `Items[].ItemName` | String(500) | Y | 商品名稱 |
| `Items[].ItemCount` | Number | Y | 商品數量 |
| `Items[].ItemWord` | String(6) | Y | 商品單位 |
| `Items[].ItemPrice` | Number | Y | 單價；`vat=1` 為含稅、`vat=0` 為未稅 |
| `Items[].ItemTaxType` | String(1) | 條件 | 僅 `TaxType=9` 時填：`1` 應稅、`2` 零稅率、`3` 免稅；只能「應稅+免稅」或「應稅+零稅率」 |
| `Items[].ItemAmount` | Number | Y | **含稅**小計；`vat=0` 時 = 未稅單價 × 數量 × 1.05 |
| `Items[].ItemRemark` | String(120) | | 商品備註 |
| `InvType` | String(2) | Y | `07` 一般稅額、`08` 特種稅額 |
| `vat` | String(1) | | 商品單價是否含稅：`1` 含稅（預設）、`0` 未稅。只影響 `ItemPrice`，`SalesAmount` 與 `ItemAmount` 一律含稅 |

綠界稅額算法：一般發票 `(發票金額 / 1.05) × 0.05` 四捨五入；混稅發票以應稅品項小計總和計算（/7896）。

#### 回應

外層：`MerchantID`、`RpHeader.Timestamp`、`TransCode`（`1` 為傳輸成功）、`TransMsg`、`Data`（AES 加密）。
`Data` 解密後：`RtnCode`（`1` 成功）、`RtnMsg`、`InvoiceNo`、`InvoiceDate`、`RandomNumber`。

#### 請求範例

```json
{
    "MerchantID": "2000132",
    "RqHeader": {
        "Timestamp": 1640000000,
        "Revision": "3.0.0"
    },
    "Data": "uvI4yrErM37XNQkXGAgRgJAgHn2t72jahaMZzYhWL1HmvH4WV18VJDP2i9pTbC+t..."
}
```

**Data 解密內容：**
```json
{
    "MerchantID": "2000132",
    "RelateNumber": "INV-20240101-001",
    "CustomerName": "王小明",
    "CustomerEmail": "test@example.com",
    "Print": "0",
    "Donation": "0",
    "TaxType": "1",
    "InvType": "07",
    "SalesAmount": 10000,
    "Items": [
        {
            "ItemName": "網站開發服務",
            "ItemCount": 1,
            "ItemWord": "式",
            "ItemPrice": 10000,
            "ItemAmount": 10000
        }
    ]
}
```

---

### 2. 作廢發票 `Invalid`（/7906）

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `MerchantID` | String(10) | Y | 特店編號 |
| `InvoiceNo` | String(10) | Y | 發票號碼 |
| `InvoiceDate` | String(10) | Y | 發票開立日期 `yyyy-MM-dd` 或 `yyyy/MM/dd` |
| `Reason` | String(20) | Y | 作廢原因 |

---

### 3. 開立折讓 `Allowance`（紙本開立，/7901）

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `MerchantID` | String(10) | Y | 特店編號 |
| `InvoiceNo` | String(10) | Y | 發票號碼 |
| `InvoiceDate` | String(10) | Y | 發票開立日期 `yyyy-MM-dd` 或 `yyyy/MM/dd` |
| `AllowanceNotify` | String(1) | Y | `S` 簡訊、`E` 電子郵件、`A` 皆通知、`N` 皆不通知 |
| `CustomerName` | String(60) | | 客戶名稱 |
| `NotifyMail` | String(100) | | 通知信箱 |
| `NotifyPhone` | String(20) | | 通知手機 |
| `AllowanceAmount` | Number | Y | 折讓單總金額（含稅） |
| `Reason` | String(50) | | 折讓原因 |
| `Items[].ItemSeq` | Int | Y | 商品序號 |
| `Items[].ItemName` | String(500) | Y | 商品名稱 |
| `Items[].ItemCount` | Number | Y | 商品數量 |
| `Items[].ItemWord` | String(6) | Y | 商品單位 |
| `Items[].ItemPrice` | Number | Y | 商品單價 |
| `Items[].ItemTaxType` | String(1) | | 商品課稅別 |
| `Items[].ItemAmount` | Number | Y | 商品合計 |

線上折讓 `AllowanceByCollegiate`（/15391）欄位大致相同（無 `NotifyPhone`、`ItemSeq` 非必填），另帶 `ReturnURL`；消費者同意後綠界回傳結果，回傳參數含 `CheckMacValue`（檢查碼機制見 /38242）。

---

### 4. 作廢折讓 `AllowanceInvalid`（/7911）

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `MerchantID` | String(10) | Y | 特店編號 |
| `InvoiceNo` | String(10) | Y | 發票號碼 |
| `AllowanceNo` | String(16) | Y | 折讓編號 |
| `Reason` | String(20) | Y | 作廢原因 |

---

### 5. 查詢發票 `GetIssue`（/7923）

兩種查法擇一：
- `MerchantID` + `RelateNumber`
- `MerchantID` + `InvoiceNo` + `InvoiceDate`（`yyyy-MM-dd` 或 `yyyy/MM/dd`）

---

### 6. 延遲開立 `DelayIssue`（/15369）

獨立 API，欄位同 `Issue`，另加：

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `DelayFlag` | String(1) | Y | `1` 延遲開立、`2` 觸發開立 |
| `DelayDay` | Int | Y | 延遲開立 1–15 天；觸發開立 0–15 天 |
| `Tsr` | String(30) | Y | 交易單號，唯一值；之後觸發或取消都靠它 |
| `PayType` | String(1) | Y | 固定 `2` |
| `PayAct` | String(6) | Y | 固定 `ECPAY` |
| `NotifyURL` | String(200) | | 開立完成通知網址，收到後回 `1|OK`；**測試環境不發通知** |

`EditDelayIssue`（/47979）修改尚未開立的延遲發票。

### 7. 觸發開立 `TriggerIssue`（/15371）

欄位：`MerchantID`、`Tsr`、`PayType`（固定 `2`）。
**成功碼不是 1**：`DelayDay>0` 回 `4000003`（延後開立成功），`DelayDay=0` 回 `4000004`（開立成功），其餘為失敗。

### 8. 取消延遲開立 `CancelDelayIssue`（/15382）

欄位：`MerchantID`、`Tsr`。

---

### 9. 手機條碼驗證 `CheckBarcode`（/7886）

欄位：`MerchantID`、`BarCode`（String(8)）。回傳 `IsExist`（`Y`/`N`）；`RtnCode=1` 只代表呼叫成功，是否存在看 `IsExist`。`9000001` 表示財政部維護中，稍後再試。

### 10. 捐贈碼驗證 `CheckLoveCode`（/7891）

欄位：`MerchantID`、`LoveCode`（String(7)）。回傳 `IsExist`、`OrganName`。

### 11. 統一編號驗證 `GetCompanyNameByTaxID`（/32089）

回傳 `CompanyName`；回應代碼 `1` 成功、`7` 查無資料、`1200125` 檢查碼錯誤、`2027000` 長度錯誤、`9000001` 財政部 API 失敗。`7` 與 `9000001` 不影響開立。

### 12. 發送發票通知 `InvoiceNotify`（/7938）

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `MerchantID` | String(10) | Y | 特店編號 |
| `InvoiceNo` | String(10) | Y | 發票號碼 |
| `AllowanceNo` | String(16) | 條件 | `InvoiceTag` 為 `A`、`AI`、`OA` 時必填 |
| `Phone` | String(20) | 條件 | 與 `NotifyMail` 擇一 |
| `NotifyMail` | String(200) | 條件 | 與 `Phone` 擇一，多組以分號分隔 |
| `Notify` | String(1) | Y | `S` 簡訊、`E` 電子郵件、`A` 皆通知 |
| `InvoiceTag` | String(2) | Y | `I` 開立、`II` 作廢、`A` 折讓開立、`AI` 折讓作廢、`AW` 中獎、`OA` 線上折讓 |
| `Notified` | String(1) | Y | `C` 客戶、`M` 特店、`A` 皆發送；`OA` 只能 `C` |

---

## B2B 電子發票（三聯式）

B2B 分**存證**（/24230 起）與**交換**（/14850 起）兩種模式，端點前綴都是 `/B2BInvoice/`。
開立前須先用 `MaintainMerchantCustomerData`（/24201、/14830）建立交易對象並設定模式。
請求外層與 B2C 相同，官方參數頁的 `RqHeader` 只列 `Timestamp`。

| 功能 | 端點 | 存證 | 交換 |
|------|------|------|------|
| 交易對象維護 | `MaintainMerchantCustomerData` | /24201 | /14830 |
| 開立發票 | `Issue` | /24230 | /14850 |
| 開立發票確認 | `IssueConfirm` | — | /14855 |
| 作廢發票 | `Invalid` | /24235 | /14860 |
| 賣方開立折讓 | `Allowance` | /24245 | /14923 |
| 作廢折讓 | `CancelAllowance` | /24253 | /14889 |
| 查詢發票 | `GetIssue` | /24271 | /14935 |
| 發送發票通知 | `Notify` | /24306 | /14988 |
| 發票列印 | `InvoicePrint` | /24311 | /14993 |
| 發票 PDF | `DownloadB2BPdf` | /52123 | /53383 |

交換模式另有退回、各項確認與對應查詢 API（/14865–/14983）。

### 1. 開立發票 `Issue`（/24230）

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `MerchantID` | String(10) | Y | 特店編號 |
| `RelateNumber` | String(50) | Y | 廠商自訂編號 |
| `InvoiceTime` | String(20) | | 發票開立時間 `yyyy-mm-dd hh:mm:ss` |
| `CustomerIdentifier` | String(8) | Y | 買方統編 |
| `CustomerEmail` | String(200) | | 未帶時使用交易對象維護的設定，多組以分號分隔 |
| `CustomerAddress` | String(100) | | 買方地址 |
| `CustomerTelephoneNumber` | String(26) | | 買方電話 |
| `ClearanceMark` | Number | 條件 | 零稅率時帶 `1` 非經海關出口或 `2` 經海關出口 |
| `InvType` | String(2) | Y | `07` 一般稅額、`08` 特種稅額 |
| `TaxType` | String(1) | Y | `07`：`1` 應稅、`2` 零稅率、`3` 免稅；`08`：`3`、`4` |
| `TaxRate` | Number | | 稅率 |
| `ZeroTaxRateReason` | String(2) | 條件 | 自 115 年 1 月 1 日起零稅率必填或後台設定 |
| `SpecialTaxType` | Number | 條件 | 免稅帶 `8`；特種應稅帶 `1`–`8` |
| `Items[].ItemSeq` | Int | Y | 明細排列序號 |
| `Items[].ItemName` | String(500) | Y | 商品名稱 |
| `Items[].ItemCount` | Number | Y | 商品數量 |
| `Items[].ItemWord` | String(6) | | 商品單位 |
| `Items[].ItemPrice` | Number | Y | **未稅**單價 |
| `Items[].ItemAmount` | Number | Y | 商品合計，與 數量 × 單價 差距不可大於 1 |
| `Items[].ItemTax` | Number | | 商品稅額，與 ItemAmount × TaxRate 差距不可大於 1 |
| `Items[].ItemRemark` | String(120) | | 商品備註 |
| `SalesAmount` | Number | Y | 銷售額合計（未稅），= ItemAmount 加總四捨五入，不可為 0 |
| `TaxAmount` | Number | Y | 稅額合計，與 SalesAmount × TaxRate 四捨五入差距不可大於 2；特種稅額帶 `0` |
| `TotalAmount` | Number | Y | = SalesAmount + TaxAmount |
| `InvoiceRemark` | String(200) | | 發票備註 |

B2B 沒有列印註記、捐贈、載具欄位。回傳 `InvoiceNumber`、`RandomNumber`。
存證模式的發票由綠界暫存，**隔日**開立並上傳財政部（/24230）。

### 2. 作廢發票 `Invalid`（/24235）

欄位：`MerchantID`、`InvoiceNumber`（注意不是 `InvoiceNo`）、`InvoiceDate`（String(10)）、`Reason`（String(20)）、`Remark`（String(200)）。

### 3. 賣方開立折讓 `Allowance`（/24245）

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `MerchantID` | String(10) | Y | 特店編號 |
| `AllowanceDate` | String(20) | | `yyyy-mm-dd hh:mm:ss`，僅接受 6 天內；空值為當下 |
| `CustomerEmail` | String(200) | | 未帶時使用交易對象維護的設定 |
| `CustomerAddress` | String(100) | | |
| `TaxAmount` | Number | Y | 營業稅額，與 TotalAmount × TaxRate 四捨五入差距不可大於 2 |
| `TotalAmount` | Number | Y | 折讓金額總計（**未稅**），不可為 0 |
| `Details[].OriginalInvoiceNumber` | String(10) | Y | 原發票號碼 |
| `Details[].OriginalInvoiceDate` | String(20) | Y | 原發票日期 |
| `Details[].OriginalSequenceNumber` | Int | Y | 原發票商品排序 1–999，須與原發票相同 |
| `Details[].ItemName` | String(500) | Y | 商品名稱 |
| `Details[].ItemCount` | Number | Y | 不可超過原發票數量 |
| `Details[].ItemPrice` | Number | Y | 不可超過原發票價格 |
| `Details[].ItemAmount` | Number | Y | 與 數量 × 價格 差距不可大於 1 |
| `Details[].Tax` | Number | | 商品稅額 |

回傳 `AllowanceNo`、`AllowanceNumber`。

### 4. 作廢折讓 `CancelAllowance`（/24253）

欄位：`MerchantID`、`AllowanceNo`（String(16)）、`Reason`（String(20)）、`Remark`（String(200)）。

---

## 發票列印

### B2C `InvoicePrint`（/7949）

AES JSON API，不是表單跳轉。

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `MerchantID` | String(10) | Y | 特店編號 |
| `InvoiceNo` | String(10) | Y | 發票號碼 |
| `InvoiceDate` | String(20) | Y | `yyyy-MM-dd` 或 `yyyy/MM/dd` |
| `PrintStyle` | Int | | `1` 一般單面（預設）、`2` 一般雙面、`3` 熱感應紙、`4` B2B A4、`5` B2B A5（4、5 限有統編的發票） |
| `IsReprintInvoice` | String(1) | | `Y` 顯示「電子發票證明聯補印」；僅 `PrintStyle` 1–3 有效 |
| `IsShowingDetail` | Int | | `1` 顯示明細、`2` 隱藏；有統編或 B2B 格式一律顯示 |

回傳 `InvoiceHtml`：列印頁網址，**自呼叫起 1 小時內有效**，前端開新視窗載入即可。

### B2B `InvoicePrint`（/24311）與 `DownloadB2BPdf`（/52123）

B2B 列印端點為 `/B2BInvoice/InvoicePrint`；PDF 下載為 `/B2BInvoice/DownloadB2BPdf`。

---

## 錯誤代碼

> **綠界沒有公開完整的發票錯誤碼表。** 官方附錄「錯誤代碼一覽表」（developers.ecpay.com.tw/7954）只寫：
> 錯誤代碼持續新增，請到「廠商後台 → 電子發票 → 系統設定 → 錯誤代碼查詢」查詢。
> 因此程式應以 `RtnCode == 1` 判斷成功，其他一律視為失敗並完整記錄 `RtnMsg`，不要依代碼寫死分支。

### 官方文件中出現過的代碼

| 代碼 | 說明 | 出處 |
|------|------|------|
| `1` | 成功 | 各 API 回應說明 |
| `4000003` | 延後開立成功（觸發開立且 `DelayDay>0`） | 觸發開立（/15371） |
| `4000004` | 開立成功（觸發開立且 `DelayDay=0`） | 觸發開立（/15371） |
| `7` | 統一編號查無資料（不影響開立） | 統一編號驗證（/32089） |
| `10100058` | 發票作業逾時（AIO 金流同代碼為 ATM 繳費逾期） | 綠界官方 ecpay-api-skill `guides/20-error-codes-reference.md` |
| `10000002` | 必填欄位遺漏（Phone/Email 皆未填，或 Items 格式錯誤） | 綠界官方 ecpay-api-skill `guides/04-invoice-b2c.md` |
| `10000009` | RelateNumber 重複（同一帳號不可重用） | 同上 |
| `1500047`、`5070350` | 當期字軌未新增、未啟用或號碼已用罄 → 後台「字軌與配號設定」 | 附錄 錯誤代碼一覽表（/7954） |
| `1200125` | 統一編號檢查碼驗證失敗 | 檢查統一編號 API（/32089） |
| `2027000` | 統一編號格式錯誤（長度非 8 碼） | 同上 |
| `9000001` | 呼叫財政部 API 失敗；統編驗證不影響開立，手機條碼請稍後再驗 | /32089、/7886 |

---

## 補充說明

### 載具類型說明

| 代碼 | 名稱 | 格式 | 說明 |
|------|------|------|------|
| `''` | 無載具 | - | 一般發票 |
| `1` | 綠界電子發票載具 | Email | 綠界會員載具 |
| `2` | 自然人憑證 | 2 碼英文 + 14 碼數字 | 總長度 16 碼 |
| `3` | 手機條碼 | `/` 開頭共 8 碼 | 需先驗證 |
| `4` | 悠遊卡 | 卡片隱碼（`CarrierNum`）+ 顯碼（`CarrierNum2`） | 查詢 API 不回傳隱碼 |
| `5` | 一卡通 | 同上 | 同上 |

### 課稅別說明

| 代碼 | 名稱 | 說明 |
|------|------|------|
| `1` | 應稅 | 一般商品（5% 稅率） |
| `2` | 零稅率 | 外銷、國際運輸等（需填 ClearanceMark） |
| `3` | 免稅 | 土地、未經加工農產品等 |
| `4` | 應稅（特種稅率） | `InvType=08` 時使用，搭配 `SpecialTaxType` 1–8 |
| `9` | 混合 | 混合應稅與免稅或零稅率，需申請核可 |

### 零稅率原因代碼（自 115 年起必填）

| 代碼 | 說明 |
|------|------|
| `71` | 外銷貨物 |
| `72` | 與外銷有關之勞務，或在國內提供而在國外使用之勞務 |
| `73` | 依法設立之免稅商店銷售與過境或出境旅客之貨物 |
| `74` | 銷售與保稅區營業人供營運之貨物或勞務 |
| `75` | 國際間之運輸 |
| `76` | 國際運輸用之船舶、航空器及遠洋漁船 |
| `77` | 銷售與國際運輸用之船舶、航空器及遠洋漁船所使用之貨物或修繕勞務 |
| `78` | 保稅區營業人銷售與課稅區營業人未輸往課稅區而直接出口之貨物 |
| `79` | 保稅區營業人銷售與課稅區營業人存入自由港區事業或海關管理之保稅倉庫、物流中心以供外銷之貨物 |

### 金額計算邏輯

**B2C（/7896）：**
```
SalesAmount = 含稅總金額（= ItemAmount 加總四捨五入）
TaxAmount   = 選填，未填由綠界計算
ItemAmount  = 含稅小計
ItemPrice   = vat=1 時含稅、vat=0 時未稅
```

**B2B（/24230）：**
```
SalesAmount = 未稅銷售額（= ItemAmount 加總四捨五入）
TaxAmount   = 稅額（與 SalesAmount × TaxRate 四捨五入差距 ≤ 2）
TotalAmount = SalesAmount + TaxAmount
ItemPrice   = 未稅單價
```

**計算範例（B2B）：**
```
商品單價：9524 元（未稅）
稅額：9524 × 0.05 = 476 元
總計：9524 + 476 = 10000 元
```

---

## 常見問題

- **打統編不一定要接 B2B**：B2C `Issue` 帶 `CustomerIdentifier` 即可（/24230 注意事項）。B2B API 是給需要存證／交換流程的營業人。
- **B2B 開立前要建交易對象**：官方要求串接前先用 `MaintainMerchantCustomerData` 設定交易對象與存證／交換模式（/24201）。
- **列印**：用 `InvoicePrint` 取得 `InvoiceHtml` 網址（1 小時有效），不是表單 POST 到 `/Invoice/Print`。

---

## 相關文件

- [速買配 API 規格](./SMILEPAY_API_REFERENCE.md)
- [光貿 Amego API 規格](./AMEGO_API_REFERENCE.md)

---

## 聯絡客服

如有任何問題，請聯絡綠界客服：
- **官方網站**：https://www.ecpay.com.tw
- **開發者文件**：https://developers.ecpay.com.tw/
- **技術支援**：請至官網查詢

