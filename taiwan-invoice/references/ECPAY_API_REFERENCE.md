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
5. [共用功能](#共用功能)
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

> **重要**：正式環境的 HashKey 和 HashIV 需向綠界申請取得

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

### 1. 開立發票

**端點：** `POST /B2CInvoice/Issue`

#### 請求參數（最外層）

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `MerchantID` | String(10) | Y | 特店編號 |
| `RqHeader` | Object | Y | 傳輸資料容器 |
| `RqHeader.Timestamp` | Number(10) | Y | Unix 時間戳（驗證區間 10 分鐘） |
| `Data` | String | Y | AES 加密後的 JSON 字串 |

#### Data 欄位內容（加密前）

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `MerchantID` | String(10) | Y | 特店編號 |
| `RelateNumber` | String(50) | Y | 廠商自訂編號（唯一值，不可重複） |
| `CustomerID` | String(50) | N | 客戶編號 |
| `CustomerIdentifier` | String(8) | N | 買方統編（有值=B2B，空值=B2C） |
| `CustomerName` | String(60) | N | 買方名稱 |
| `CustomerAddr` | String(100) | N | 買方地址 |
| `CustomerPhone` | String(20) | N | 買方電話 |
| `CustomerEmail` | String(200) | N | 買方電子信箱（多組用分號`;`區隔） |
| `ClearanceMark` | String(1) | N | 通關方式：1 非經海關出口、2 經海關出口（零稅率必填） |
| `Print` | String(1) | Y | 列印註記：0 不列印、1 列印 |
| `Donation` | String(1) | Y | 捐贈註記：0 不捐贈、1 捐贈 |
| `LoveCode` | String(7) | N | 愛心碼（捐贈=1 時必填） |
| `CarrierType` | String(1) | N | 載具類別：'' 無、1 綠界電子發票載具、2 自然人憑證、3 手機條碼 |
| `CarrierNum` | String(64) | N | 載具編號（CarrierType 有值時必填） |
| `TaxType` | String(1) | Y | 課稅別：1 應稅、2 零稅率、3 免稅、9 混合應稅與免稅 |
| `SpecialTaxType` | String(1) | N | 特種稅額類別（免稅或應稅時填） |
| `InvType` | String(2) | Y | 字軌類別：07 一般稅額、08 特種稅額 |
| `SalesAmount` | Number | Y | 銷售額合計（含稅，整數） |
| `InvoiceRemark` | String(200) | N | 發票備註 |
| `Items` | Array | Y | 商品明細陣列 |
| `ItemName` | String(100) | Y | 商品名稱 |
| `ItemCount` | Number | Y | 商品數量 |
| `ItemWord` | String(6) | N | 商品單位 |
| `ItemPrice` | Number | Y | 商品單價（含稅） |
| `ItemTaxType` | String(1) | N | 商品課稅別（混合稅率時必填） |
| `ItemAmount` | Number | Y | 商品小計（含稅） |
| `ItemRemark` | String(40) | N | 商品備註 |
| `InvCreateDate` | String(20) | N | 發票開立日期（YYYY-MM-DD，過去 6 天內） |
| `DelayFlag` | String(1) | N | 延遲註記：0 即時開立、1 延遲開立 |
| `DelayDay` | Number | N | 延遲天數（1-15 天） |
| `Tsr` | String(30) | N | 交易單號（選填） |
| `PayType` | String(2) | N | 付款方式：01 現金、02 刷卡、03 支票、04 匯款 |
| `PayAct` | String(1) | N | 付款行為：1 付款、0 未付款 |
| `NotifyURL` | String(200) | N | 開立通知 URL |

#### 回應參數

**最外層：**

| 欄位 | 型別 | 說明 |
|------|------|------|
| `MerchantID` | String(10) | 特店編號 |
| `RpHeader` | Object | 回傳資料容器 |
| `RpHeader.Timestamp` | Number(10) | Unix 時間戳 |
| `TransCode` | Number | 1 傳輸成功、其他失敗 |
| `TransMsg` | String(200) | 回傳訊息 |
| `Data` | String | AES 加密的回應資料 |

**Data 解密後：**

| 欄位 | 型別 | 說明 |
|------|------|------|
| `RtnCode` | Number | 1 成功、其他失敗 |
| `RtnMsg` | String(200) | 回應訊息 |
| `InvoiceNo` | String(10) | 發票號碼（成功時回傳） |
| `InvoiceDate` | String(20) | 發票開立日期時間 |
| `RandomNumber` | String(4) | 隨機碼 |

#### 請求範例

```json
{
    "MerchantID": "2000132",
    "RqHeader": {
        "Timestamp": 1640000000
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

### 2. 作廢發票

**端點：** `POST /B2CInvoice/Invalid`

#### Data 欄位內容

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `MerchantID` | String(10) | Y | 特店編號 |
| `InvoiceNo` | String(10) | Y | 發票號碼 |
| `InvoiceDate` | String(20) | Y | 發票開立日期時間（YYYY-MM-DD HH:MM:SS） |
| `Reason` | String(20) | Y | 作廢原因 |

---

### 3. 開立折讓

**端點：** `POST /B2CInvoice/Allowance`

#### Data 欄位內容

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `MerchantID` | String(10) | Y | 特店編號 |
| `InvoiceNo` | String(10) | Y | 發票號碼 |
| `InvoiceDate` | String(20) | Y | 發票開立日期時間 |
| `AllowanceNotify` | String(1) | Y | 通知類別：S 簡訊、E 電子郵件、A 皆通知、N 皆不通知 |
| `CustomerName` | String(60) | N | 客戶名稱 |
| `NotifyMail` | String(100) | N | 通知信箱 |
| `NotifyPhone` | String(20) | N | 通知手機 |
| `AllowanceAmount` | Number | Y | 折讓單總金額（含稅） |
| `Items` | Array | Y | 折讓商品明細 |
| `ItemName` | String(100) | Y | 商品名稱 |
| `ItemCount` | Number | Y | 商品數量 |
| `ItemWord` | String(6) | N | 商品單位 |
| `ItemPrice` | Number | Y | 商品單價（含稅） |
| `ItemTaxType` | String(1) | N | 商品課稅別 |
| `ItemAmount` | Number | Y | 商品小計（含稅） |

---

### 4. 作廢折讓

**端點：** `POST /B2CInvoice/AllowanceInvalid`

#### Data 欄位內容

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `MerchantID` | String(10) | Y | 特店編號 |
| `InvoiceNo` | String(10) | Y | 發票號碼 |
| `AllowanceNo` | String(16) | Y | 折讓單號碼 |
| `Reason` | String(20) | Y | 作廢原因 |

---

### 5. 查詢發票

**端點：** `POST /B2CInvoice/GetIssue`

#### Data 欄位內容

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `MerchantID` | String(10) | Y | 特店編號 |
| `RelateNumber` | String(50) | Y | 廠商自訂編號 |

---

### 6. 延遲開立發票

**端點：** `POST /B2CInvoice/DelayIssue`

延遲開立發票申請（需先用 `Issue` API 設定 `DelayFlag=1`）。

---

### 7. 觸發開立

**端點：** `POST /B2CInvoice/TriggerIssue`

觸發延遲開立的發票正式開立。

---

### 8. 取消延遲開立

**端點：** `POST /B2CInvoice/CancelDelayIssue`

取消延遲開立的發票申請。

---

### 9. 查詢手機條碼

**端點：** `POST /B2CInvoice/CheckBarcode`

驗證手機條碼是否有效。

---

### 10. 查詢愛心碼

**端點：** `POST /B2CInvoice/CheckLoveCode`

驗證愛心碼是否有效。

---

### 11. 發票通知

**端點：** `POST /B2CInvoice/InvoiceNotify`

補寄發票開立通知信/簡訊。

---

### 12. 字軌設定查詢

**端點：** `POST /B2CInvoice/GetInvoiceWordSetting`

查詢發票字軌設定。

---

## B2B 電子發票（三聯式）

### 1. 開立發票

**端點：** `POST /B2BInvoice/Issue`

#### Data 欄位內容（與 B2C 差異）

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `CustomerIdentifier` | String(8) | Y | 買方統編（**B2B 必填**） |
| `CustomerName` | String(60) | Y | 買方名稱（**B2B 必填**） |
| `CustomerAddress` | String(100) | N | 買方地址 |
| `CustomerEmail` | String(200) | N | 買方電子信箱 |
| `Print` | String(1) | - | **B2B 一律列印（固定=1）** |
| `Donation` | String(1) | - | **B2B 不可捐贈（固定=0）** |
| `CarrierType` | String(1) | - | **B2B 不可使用載具（固定=空值）** |
| `SalesAmount` | Number | Y | 銷售額合計（**未稅**） |
| `TaxAmount` | Number | Y | 稅額合計 |
| `TotalAmount` | Number | Y | 發票金額合計（SalesAmount + TaxAmount） |
| `ItemPrice` | Number | Y | 商品單價（**未稅**） |
| `ItemAmount` | Number | Y | 商品小計（**未稅**） |
| `ItemTax` | Number | N | 商品稅額 |

**B2B 與 B2C 主要差異：**

| 項目 | B2C | B2B |
|------|-----|-----|
| 統編 | 選填 | **必填** |
| 列印 | 可選 0/1 | **固定=1（一律列印）** |
| 捐贈 | 可選 0/1 | **固定=0（不可捐贈）** |
| 載具 | 可填 | **不可使用** |
| 金額 | 含稅 | **未稅** |
| 稅額 | 系統計算 | **必填** |

---

### 2. 作廢發票

**端點：** `POST /B2BInvoice/Invalid`

參數與 B2C 相同。

---

### 3. 開立折讓

**端點：** `POST /B2BInvoice/Allowance`

參數與 B2C 相同。

---

### 4. 作廢折讓

**端點：** `POST /B2BInvoice/AllowanceInvalid`

參數與 B2C 相同。

---

## 共用功能

### 1. 發票列印

**端點：** `POST /Invoice/Print`

開啟發票列印頁面（使用 POST 表單跳轉）。

#### 表單參數

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `MerchantID` | String(10) | Y | 特店編號 |
| `InvoiceNo` | String(10) | Y | 發票號碼 |
| `InvoiceDate` | String(20) | Y | 發票開立日期時間 |
| `PrintStyle` | String(1) | N | 列印樣式：1 一般格式、2 簡易格式 |

**使用方式：**
```html
<form method="POST" action="https://einvoice-stage.ecpay.com.tw/Invoice/Print" target="_blank">
    <input type="hidden" name="MerchantID" value="2000132">
    <input type="hidden" name="InvoiceNo" value="AB12345678">
    <input type="hidden" name="InvoiceDate" value="2024-01-01 10:00:00">
    <button type="submit">列印發票</button>
</form>
```

---

## 錯誤代碼

### 通用錯誤

| 代碼 | 說明 |
|------|------|
| `10000001` | 參數錯誤 |
| `10000002` | 發票號碼重複 |
| `10000003` | 特店編號錯誤 |
| `10000004` | 加密驗證失敗 |
| `10000005` | 時間戳記逾時（超過 10 分鐘） |
| `10000006` | RelateNumber 重複 |
| `10000007` | 發票不存在 |
| `10000008` | 發票已作廢 |
| `10000009` | 發票已折讓 |
| `10000010` | 折讓金額超過發票金額 |

### 開立發票錯誤

| 代碼 | 說明 |
|------|------|
| `10000011` | 買方統編格式錯誤 |
| `10000012` | 愛心碼格式錯誤 |
| `10000013` | 手機條碼格式錯誤 |
| `10000014` | 自然人憑證條碼格式錯誤 |
| `10000015` | 商品明細錯誤 |
| `10000016` | 金額計算錯誤 |
| `10000017` | 發票日期超過限制（6 天） |
| `10000018` | 載具與捐贈不可同時存在 |
| `10000019` | 打統編不可使用載具 |
| `10000020` | 打統編不可捐贈 |

### 作廢發票錯誤

| 代碼 | 說明 |
|------|------|
| `10000021` | 發票不可作廢（已超過期限） |
| `10000022` | 發票已有折讓不可作廢 |

### 折讓錯誤

| 代碼 | 說明 |
|------|------|
| `10000031` | 折讓單不存在 |
| `10000032` | 折讓單已作廢 |
| `10000033` | 折讓金額錯誤 |

---

## 補充說明

### 載具類型說明

| 代碼 | 名稱 | 格式 | 說明 |
|------|------|------|------|
| `''` | 無載具 | - | 一般發票 |
| `1` | 綠界電子發票載具 | Email | 綠界會員載具 |
| `2` | 自然人憑證 | 2 碼英文 + 14 碼數字 | 總長度 16 碼 |
| `3` | 手機條碼 | `/` 開頭共 8 碼 | 需先驗證 |

### 課稅別說明

| 代碼 | 名稱 | 說明 |
|------|------|------|
| `1` | 應稅 | 一般商品（5% 稅率） |
| `2` | 零稅率 | 外銷、國際運輸等（需填 ClearanceMark） |
| `3` | 免稅 | 土地、未經加工農產品等 |
| `9` | 混合 | 混合應稅與免稅商品 |

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

**B2C 發票（含稅）：**
```
SalesAmount = 含稅總金額
TaxAmount = 0 (系統自動計算)
TotalAmount = SalesAmount

ItemPrice = 含稅單價
ItemAmount = 含稅小計
```

**B2B 發票（未稅）：**
```
SalesAmount = 未稅銷售額
TaxAmount = 稅額 (需自行計算，通常為 SalesAmount × 0.05)
TotalAmount = SalesAmount + TaxAmount

ItemPrice = 未稅單價
ItemAmount = 未稅小計
ItemTax = 商品稅額
```

**計算範例（B2B）：**
```
商品單價：9524 元（未稅）
稅額：9524 × 0.05 = 476 元
總計：9524 + 476 = 10000 元
```

---

## 開發筆記 (踩坑紀錄)

> 以下是實際整合過程中遇到的問題與解決方案

### 1. B2B 發票需使用不同 Endpoint

**問題**：B2B 發票使用 `/B2CInvoice/Issue` 會失敗

**解決**：
- B2C 發票：`/B2CInvoice/Issue`
- B2B 發票：`/B2BInvoice/Issue`

```typescript
const endpoint = isB2B ? '/B2BInvoice/Issue' : '/B2CInvoice/Issue'
```

### 2. 測試環境 B2B 限制

**問題**：測試環境開 B2B 發票顯示「買方識別碼(統編)資料不存在」(RtnCode 6000015)

**原因**：ECPay 測試環境的 B2B 需要預先註冊買方統編，一般測試無法使用

**解決**：B2B 功能需在正式環境測試，或使用 B2C API 加上統編（ECPay 文件有提到這種方式）

### 3. 列印發票

**方法**：使用 `printInvoice` 方法呼叫 `/B2CInvoice/Print`

**回傳**：ECPay 會回傳 HTML 內容，前端開新視窗顯示並觸發列印

```typescript
// 回傳格式
{
    success: true,
    htmlContent: '<html>...</html>'  // 直接顯示在新視窗
}
```

### 4. 金額計算

**B2C (二聯式)**：
- `SalesAmount` = 含稅總額
- `TaxAmount` = 0（不需計算）

**B2B (三聯式)**：
- `SalesAmount` = 未稅金額
- `TaxAmount` = 稅額
- `TotalAmount` = 含稅金額

### 5. 實作檔案

- **服務實作**：`lib/services/ecpay-invoice-service.ts`
- **API 路由**：`app/api/v1/financials/[id]/issue-invoice/route.ts`

---

## 相關文件

- [速買配 API 規格](./SMILEPAY_API_REFERENCE.md)
- [光貿 Amego API 規格](./AMEGO_API_REFERENCE.md)
- [發票開立流程](./INVOICE_FLOW.md)

---

## 聯絡客服

如有任何問題，請聯絡綠界客服：
- **官方網站**：https://www.ecpay.com.tw
- **開發者文件**：https://developers.ecpay.com.tw/
- **技術支援**：請至官網查詢

---

最後更新：2026/01/28
文件版本：基於綠界官方文件整理 + 實作筆記
