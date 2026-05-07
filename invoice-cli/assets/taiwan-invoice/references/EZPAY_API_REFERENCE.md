# ezPay 簡單付電子發票 API 完整技術規格 (ezPay Invoice API)

> 官方文檔：https://inv.ezpay.com.tw/Invoice_index/download
> 技術手冊版本：EZP_INVI v1.2.2（標準版）、EZP_Track v1.0.0（字軌管理）、EZP_BDV v1.0.0（手機條碼／捐贈碼驗證）、ezPay_invoice_by_batch_file v1.0.3（批次開立）、EZP_CES v1.0.0（境外電商）
> 平台運營者：簡單行動支付股份有限公司（原 Pay2Go，後更名為 ezPay；目前為藍新金流集團旗下產品）
> 支援 B2C（二聯式）與 B2B（三聯式）電子發票，與藍新 Newebpay 共用同一加密／簽章邏輯

---

## 目錄
1. [基本說明](#基本說明)
2. [參數加密方式 (PostData_)](#參數加密方式-postdata_)
3. [B2C 電子發票](#b2c-電子發票二聯式)
4. [B2B 電子發票](#b2b-電子發票三聯式)
5. [共用功能](#共用功能)
6. [錯誤代碼](#錯誤代碼)
7. [補充說明](#補充說明)
8. [開發筆記](#開發筆記-踩坑紀錄)

---

## 基本說明

ezPay 電子發票加值服務平台（簡稱「本平台」）由簡單行動支付股份有限公司營運，為藍新金流集團（NewebPay）旗下的電子發票服務。發票資料於每日 01:00 起，由 ezPay 將前一日 00:00 至 23:59 的開立、作廢、折讓資料批次上傳至財政部電子發票整合服務平台。

### 環境資訊

| 環境 | 說明 | URL 前綴 |
|------|------|---------|
| **測試環境** | 測試用，獨立環境，不會上傳財政部 | `https://cinv.ezpay.com.tw` |
| **正式環境** | 正式開立，每日批次上傳財政部 | `https://inv.ezpay.com.tw` |

> 註：ezPay 與 Newebpay（藍新金流）共用同一套加密邏輯，但發票端與金流端的 HashKey/HashIV 是獨立簽發的。

### 測試環境資料

| 項目 | 測試值 |
|------|--------|
| **商店代號 (MerchantID_)** | 須於 `cinv.ezpay.com.tw` 申請會員後取得（範例：`3622183`） |
| **HashKey** | 商店申請後於後台「會員管理／基本資料設定／基本資料」取得 |
| **HashIV** | 同上 |
| **官方範例 HashKey** | `abcdefghijklmnopqrstuvwxyzabcdef`（32 碼） |
| **官方範例 HashIV** | `1234567891234567`（16 碼） |

> **重要**：HashKey 為 **32 碼**、HashIV 為 **16 碼**，與綠界（16/16）不同。正式環境的金鑰需向 ezPay 申請取得，且每商店獨立。

### 串接前置作業

1. 於測試平台 `https://cinv.ezpay.com.tw/` 申請會員、建立測試商店並取得 HashKey/HashIV。
2. 進入後台【管理設定 / 發票字軌號碼設定】新增測試發票字軌號碼。
3. 開立後可於【銷項發票作業 / 銷項發票查詢】查看開立結果。

### API 編碼格式

- **Content-Type**：`application/x-www-form-urlencoded`（**標準 Form Post**，非 JSON Body）
- **字元編碼**：`UTF-8`
- **傳輸方式**：`HTTP POST`
- **回應格式**：可指定 `JSON` 或 `String`（由 `RespondType` 參數決定）
- **載具編號等可能含特殊字元的參數**：請於加密前先以 `rawurlencode()` 編碼

### 參數命名規範

ezPay API 將「最外層欄位」與「加密內容欄位」分開命名：

| 層級 | 必含欄位 | 說明 |
|------|---------|------|
| 最外層 (Form Post) | `MerchantID_`、`PostData_` | **後方有底線 `_`** |
| 加密內容 (PostData_ 解密後) | `RespondType`、`Version`、`TimeStamp`、業務參數 | 一般欄位，無底線 |

> **提醒**：`MerchantID_` 與 `PostData_` 後方那個底線 `_` 不可省略，否則會被視為缺少參數。

---

## 參數加密方式 (PostData_)

ezPay 採用 **AES-256-CBC + Hex 編碼 + PKCS7 Padding**，並以 SHA256 產生 `CheckCode` 用於驗證回傳合法性。本套加密邏輯與藍新 Newebpay 金流的 TradeInfo / TradeSha 機制完全相同。

### 加密步驟概覽

```
原始參數陣列
   │
   ▼ http_build_query()
URL Encoded Query String
   │
   ▼ PKCS7 Padding（區塊 32 bytes）
補齊長度的字串
   │
   ▼ AES-256-CBC 加密（HashKey / HashIV）
密文 (binary)
   │
   ▼ bin2hex()
Hex 字串 → 放入 PostData_
```

### 加密設定

| 項目 | 數值 |
|------|------|
| 演算法 | AES-256-CBC |
| 金鑰 (Key) | HashKey（32 bytes） |
| 初始向量 (IV) | HashIV（16 bytes） |
| Padding | PKCS7（亦稱 PKCS#5）|
| 編碼輸出 | 小寫 Hex（不是 Base64）|

### 1. 準備發票參數

```
RespondType=JSON&Version=1.5&TimeStamp=1444963784&MerchantOrderNo=201409170000001
&BuyerName=王大品&BuyerUBN=54352706&Category=B2B&TaxType=1&TaxRate=5
&Amt=490&TaxAmt=10&TotalAmt=500&PrintFlag=Y
&ItemName=商品一|商品二&ItemCount=1|2&ItemUnit=個|個
&ItemPrice=300|100&ItemAmt=300|200&Status=1
```

### 2. URL Encode（http_build_query）

中文與特殊字元會自動編碼為 `%xx` 格式，例：

```
RespondType=JSON&Version=1.5&...&BuyerName=%E7%8E%8B%E5%A4%A7%E5%93%81&...
```

### 3. AES 加密 + Hex

**Node.js 範例：**

```javascript
const crypto = require('crypto')

function encryptPostData(params, hashKey, hashIV) {
    // 1. 組成 query string（URL Encode）
    const queryString = new URLSearchParams(params).toString()

    // 2. PKCS7 Padding（block size = 32 for AES-256）
    const blockSize = 32
    const padLen = blockSize - (Buffer.byteLength(queryString, 'utf8') % blockSize)
    const padded = queryString + String.fromCharCode(padLen).repeat(padLen)

    // 3. AES-256-CBC 加密（自行 padding，所以禁用 OpenSSL 內建）
    const cipher = crypto.createCipheriv('aes-256-cbc', hashKey, hashIV)
    cipher.setAutoPadding(false)
    let encrypted = cipher.update(padded, 'utf8', 'hex')
    encrypted += cipher.final('hex')

    return encrypted  // 小寫 Hex 字串
}

const params = {
    RespondType: 'JSON',
    Version: '1.5',
    TimeStamp: Math.floor(Date.now() / 1000).toString(),
    MerchantOrderNo: 'INV20260507001',
    Category: 'B2C',
    BuyerName: '王小明',
    BuyerEmail: 'test@example.com',
    PrintFlag: 'Y',
    TaxType: '1',
    TaxRate: '5',
    Amt: '952',
    TaxAmt: '48',
    TotalAmt: '1000',
    ItemName: '網站開發服務',
    ItemCount: '1',
    ItemUnit: '式',
    ItemPrice: '1000',
    ItemAmt: '1000',
    Status: '1'
}

const postData = encryptPostData(
    params,
    'abcdefghijklmnopqrstuvwxyzabcdef',  // 32 bytes
    '1234567891234567'                    // 16 bytes
)
```

**PHP 7+ 範例：**

```php
function addPadding($string, $blockSize = 32) {
    $len = strlen($string);
    $pad = $blockSize - ($len % $blockSize);
    return $string . str_repeat(chr($pad), $pad);
}

$queryString = http_build_query($params);
$postData = bin2hex(openssl_encrypt(
    addPadding($queryString),
    'AES-256-CBC',
    $hashKey,
    OPENSSL_RAW_DATA | OPENSSL_ZERO_PADDING,  // 自行 padding，故停用內建
    $hashIV
));
```

### 4. Form Post 送出

```
POST /Api/invoice_issue HTTP/1.1
Host: inv.ezpay.com.tw
Content-Type: application/x-www-form-urlencoded

MerchantID_=3622183&PostData_=70a61189d7dc0f6abefe7643da144af5...
```

### 5. CheckCode 驗證（防偽機制）

每次回傳的 `Result` 均含 `CheckCode`，用 SHA256 驗證資料未被竄改。

**步驟：**

1. 從 `Result` 抽出 5 個指定欄位：`InvoiceTransNo`、`MerchantID`、`MerchantOrderNo`、`RandomNum`、`TotalAmt`
2. 依英文字母 A→Z 排序
3. 串成 query string，前後加上 HashIV 與 HashKey
4. SHA256 → 轉大寫

**範例：**

```
排序後字串：
InvoiceTransNo=14061313541640927&MerchantID=3622183
&MerchantOrderNo=201409170000001&RandomNum=0142&TotalAmt=500

串接 IV/Key：
HashIV=1234567891234567&InvoiceTransNo=14061313541640927&MerchantID=3622183
&MerchantOrderNo=201409170000001&RandomNum=0142&TotalAmt=500
&HashKey=abcdefghijklmnopqrstuvwxyzabcdef

SHA256 大寫：
303AB800650B724733B5D91CBCE075D9EA09E4CDE9CD33461D45F07D5EC7EECB
```

**Node.js 實作：**

```javascript
function generateCheckCode(result, hashKey, hashIV) {
    const fields = {
        InvoiceTransNo: result.InvoiceTransNo,
        MerchantID: result.MerchantID,
        MerchantOrderNo: result.MerchantOrderNo,
        RandomNum: result.RandomNum,
        TotalAmt: result.TotalAmt,
    }
    const sorted = Object.keys(fields).sort().reduce((o, k) => (o[k] = fields[k], o), {})
    const queryStr = new URLSearchParams(sorted).toString()
    const raw = `HashIV=${hashIV}&${queryStr}&HashKey=${hashKey}`
    return crypto.createHash('sha256').update(raw).digest('hex').toUpperCase()
}
```

### 6. 解密回傳資料

部分查詢類 API（如手機條碼／捐贈碼驗證）的 `Result` 也是 AES 加密的 hex 字串，解密邏輯與加密反向：

```javascript
function decryptResult(hexEncrypted, hashKey, hashIV) {
    const decipher = crypto.createDecipheriv('aes-256-cbc', hashKey, hashIV)
    decipher.setAutoPadding(false)
    let decrypted = decipher.update(hexEncrypted, 'hex', 'utf8')
    decrypted += decipher.final('utf8')
    // 移除 PKCS7 padding
    const padLen = decrypted.charCodeAt(decrypted.length - 1)
    return decrypted.slice(0, -padLen)
}
```

---

## B2C 電子發票（二聯式）

ezPay 開立 / 作廢 / 折讓使用**單一端點集合**，B2C 與 B2B 透過 `Category` 欄位區分。

### 1. 開立發票

**端點：**

| 環境 | URL |
|------|-----|
| 測試 | `POST https://cinv.ezpay.com.tw/Api/invoice_issue` |
| 正式 | `POST https://inv.ezpay.com.tw/Api/invoice_issue` |

#### 最外層欄位

| 欄位 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `MerchantID_` | Y | Varchar(15) | ezPay 商店代號（注意末尾底線）|
| `PostData_` | Y | text | AES-256-CBC 加密後的 hex 字串 |

#### PostData_ 內含欄位（B2C）

| 欄位 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `RespondType` | Y | Varchar(5) | `JSON` 或 `String` |
| `Version` | Y | Varchar(5) | 固定 `1.5` |
| `TimeStamp` | Y | Varchar(30) | Unix 時間戳（秒）|
| `TransNum` | N | Varchar(20) | 對應 ezPay 簡單付金流之交易序號（未串金流則留空）|
| `MerchantOrderNo` | Y | Varchar(20) | 商店自訂編號（限英、數字、`_`，同商店不可重複）|
| `Status` | Y | Varchar(1) | `1`=即時開立、`0`=等待觸發、`3`=預約自動開立 |
| `CreateStatusTime` | C | Date | 預計開立日期（`Status=3` 時必填，格式 `YYYY-MM-DD`）|
| `Category` | Y | Varchar(5) | `B2C`（個人）|
| `BuyerName` | Y | Varchar(30) | 買受人名稱（B2C 限 30 字元）|
| `BuyerUBN` | N | Varchar(8) | 買受人統一編號（B2C 非必填）|
| `BuyerAddress` | N | Varchar(100) | 買受人地址 |
| `BuyerEmail` | C | Varchar(50) | 買受人電子信箱（`CarrierType=2` 時必填）|
| `CarrierType` | N | Varchar(2) | 載具類別：`0` 手機條碼、`1` 自然人憑證、`2` ezPay 電子發票載具 |
| `CarrierNum` | C | Varchar(50) | 載具編號（`CarrierType` 有值時必填，須 `rawurlencode`）|
| `LoveCode` | N | Int(7) | 捐贈碼（3~7 碼純數字，與 `CarrierType` 互斥）|
| `PrintFlag` | Y | Varchar(1) | `Y`=索取紙本、`N`=不索取（B2C 若無載具且無捐贈，必填 `Y`）|
| `KioskPrintFlag` | N | Varchar(1) | `1`=中獎後開放至超商 Kiosk 列印（限 `CarrierType=2`）|
| `TaxType` | Y | Varchar(2) | `1`=應稅、`2`=零稅率、`3`=免稅、`9`=混合（限 B2C）|
| `TaxRate` | Y | Float(6,4) | 一般稅率帶 `5`，零稅率／免稅帶 `0`，特種稅率依規定 |
| `CustomsClearance` | C | Varchar(1) | 報關標記（`TaxType=2` 時必填）：`1` 非經海關、`2` 經海關 |
| `Amt` | Y | Int(10) | 銷售額合計（**未稅**；`TaxType=9` 時為三類銷售額加總）|
| `AmtSales` | C | Int(10) | 應稅銷售額（`TaxType=9` 時必填）|
| `AmtZero` | C | Int(10) | 零稅率銷售額（`TaxType=9` 時必填）|
| `AmtFree` | C | Int(10) | 免稅銷售額（`TaxType=9` 時必填）|
| `TaxAmt` | Y | Int(10) | 稅額 |
| `TotalAmt` | Y | Int(10) | 發票金額（含稅；應 = `Amt + TaxAmt`）|
| `ItemName` | Y | Varchar(30) | 商品名稱，多項以 `|` 分隔 |
| `ItemCount` | Y | Int(5) | 商品數量，多項以 `|` 分隔 |
| `ItemUnit` | Y | Varchar(2) | 商品單位（中 2 字 / 英數 6 字），多項以 `|` 分隔 |
| `ItemPrice` | Y | Int(10) | 商品單價（**B2C 含稅**；多項 `|` 分隔）|
| `ItemAmt` | Y | Int(10) | 商品小計（B2C 含稅；= 數量 × 單價；多項 `|` 分隔）|
| `ItemTaxType` | C | Int(2) | 商品課稅別（`TaxType=9` 時必填，多項 `|` 分隔）|
| `Comment` | N | Varchar(200) | 備註（限 200 字元）|

#### 回應參數

##### 最外層

| 欄位 | 型態 | 說明 |
|------|------|------|
| `Status` | Varchar(10) | `SUCCESS` 或錯誤代碼 |
| `Message` | Varchar(30) | 回傳訊息 |
| `Result` | JSON / String | 依 `RespondType` 決定 |

##### Result 內容

| 欄位 | 型態 | 說明 |
|------|------|------|
| `MerchantID` | Varchar(15) | 商店代號 |
| `InvoiceTransNo` | Varchar(20) | ezPay 電子發票開立序號（**用於後續觸發開立**）|
| `MerchantOrderNo` | Varchar(20) | 商店自訂編號 |
| `TotalAmt` | Int(10) | 發票金額 |
| `InvoiceNumber` | Varchar(10) | 發票號碼（僅 `Status=1` 立即開立時回傳）|
| `RandomNum` | Varchar(4) | 防偽隨機碼 |
| `CreateTime` | DateTime | 開立時間（`YYYY-MM-DD HH:MM:SS`）|
| `CheckCode` | Varchar(64) | SHA256 驗證碼 |
| `BarCode` | Varchar(19) | 一維條碼（`PrintFlag=Y` 時提供）|
| `QRcodeL` | Varchar(140) | 左 QRCode（`PrintFlag=Y` 時提供）|
| `QRcodeR` | Varchar(140) | 右 QRCode（`PrintFlag=Y` 時提供）|

#### 請求／回應範例

**請求（最外層）：**

```
MerchantID_=3622183
&PostData_=70a61189d7dc0f6abefe7643da144af543470ddf87b1de14...（hex 加密字串）
```

**PostData_ 解密後（明文）：**

```json
{
    "RespondType": "JSON",
    "Version": "1.5",
    "TimeStamp": "1746576000",
    "MerchantOrderNo": "INV20260507001",
    "Status": "1",
    "Category": "B2C",
    "BuyerName": "王小明",
    "BuyerEmail": "test@example.com",
    "PrintFlag": "Y",
    "TaxType": "1",
    "TaxRate": "5",
    "Amt": "952",
    "TaxAmt": "48",
    "TotalAmt": "1000",
    "ItemName": "網站開發服務",
    "ItemCount": "1",
    "ItemUnit": "式",
    "ItemPrice": "1000",
    "ItemAmt": "1000",
    "Comment": "測試開立"
}
```

**回應 (JSON)：**

```json
{
    "Status": "SUCCESS",
    "Message": "電子發票開立成功",
    "Result": "{\"CheckCode\":\"00E108DF7DE8756AF003312206DA77A4...\",\"MerchantID\":\"3622183\",\"MerchantOrderNo\":\"INV20260507001\",\"InvoiceNumber\":\"DS12223139\",\"TotalAmt\":1000,\"InvoiceTransNo\":\"15110317583641325\",\"RandomNum\":\"4253\",\"CreateTime\":\"2026-05-07 10:00:00\",\"BarCode\":\"11504DS122231394253\",\"QRcodeL\":\"DS12223139115040742530000038000003e8...\",\"QRcodeR\":\"**網站開發服務:1:1000\"}"
}
```

> **重要**：當同一筆 `PostData_` 重複送出且資料完全一致時，平台會回傳 `SUCCESS` 並重送原本的 `Result`（idempotent 設計）。

---

### 2. 觸發開立發票

當 `Status=0`（等待觸發）或 `Status=3`（預約自動開立但欲提前開立）時使用。

**端點：**

| 環境 | URL |
|------|-----|
| 測試 | `POST https://cinv.ezpay.com.tw/Api/invoice_touch_issue` |
| 正式 | `POST https://inv.ezpay.com.tw/Api/invoice_touch_issue` |

#### PostData_ 內含欄位

| 欄位 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `RespondType` | Y | Varchar(5) | `JSON` / `String` |
| `Version` | Y | Varchar(5) | 固定 `1.0` |
| `TimeStamp` | Y | Varchar(30) | Unix 時間戳 |
| `TransNum` | N | Varchar(20) | 對應金流交易序號（選填）|
| `InvoiceTransNo` | Y | Varchar(20) | 開立發票時取得的開立序號 |
| `MerchantOrderNo` | Y | Varchar(20) | 商店自訂編號 |
| `TotalAmt` | Y | Int(10) | 發票金額 |

---

### 3. 作廢發票

可作廢「前兩個月」開立的發票（限奇數月 14 日前，例如 7/14 前可作廢 5/1–6/30 之發票）。

**端點：**

| 環境 | URL |
|------|-----|
| 測試 | `POST https://cinv.ezpay.com.tw/Api/invoice_invalid` |
| 正式 | `POST https://inv.ezpay.com.tw/Api/invoice_invalid` |

#### PostData_ 內含欄位

| 欄位 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `RespondType` | Y | Varchar(5) | `JSON` / `String` |
| `Version` | Y | Varchar(5) | 固定 `1.0` |
| `TimeStamp` | Y | Varchar(30) | Unix 時間戳 |
| `InvoiceNumber` | Y | Varchar(10) | 欲作廢之發票號碼 |
| `InvalidReason` | Y | Varchar(6) | 作廢原因（中 6 字 / 英 20 字內）|

#### Result

| 欄位 | 型態 | 說明 |
|------|------|------|
| `MerchantID` | Varchar(15) | 商店代號 |
| `InvoiceNumber` | Varchar(10) | 作廢之發票號碼 |
| `CreateTime` | DateTime | 作廢時間 |
| `CheckCode` | Varchar(64) | SHA256 驗證碼 |

---

### 4. 開立折讓

**端點：**

| 環境 | URL |
|------|-----|
| 測試 | `POST https://cinv.ezpay.com.tw/Api/allowance_issue` |
| 正式 | `POST https://inv.ezpay.com.tw/Api/allowance_issue` |

#### PostData_ 內含欄位

| 欄位 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `RespondType` | Y | Varchar(5) | `JSON` / `String` |
| `Version` | Y | Varchar(5) | 固定 `1.3` |
| `TimeStamp` | Y | Varchar(30) | Unix 時間戳 |
| `InvoiceNo` | Y | Varchar(10) | 原發票號碼 |
| `MerchantOrderNo` | Y | Varchar(20) | 原發票之商店自訂編號 |
| `ItemName` | Y | Varchar(30) | 折讓商品名稱（多項 `|` 分隔）|
| `ItemCount` | Y | Int(5) | 折讓商品數量 |
| `ItemUnit` | Y | Varchar(2) | 折讓商品單位 |
| `ItemPrice` | Y | Int(10) | 折讓商品單價（含稅或未稅；若帶含稅則 `ItemTaxAmt=0`，無法扣抵營業稅）|
| `ItemAmt` | Y | Int(10) | 折讓商品小計 |
| `ItemTaxAmt` | Y | Int(10) | 折讓商品稅額（多項 `|` 分隔）|
| `TaxTypeForMixed` | C | Int(2) | 混合稅率折讓（`TaxType=9` 時必填）：`1`／`2`／`3` |
| `TotalAmt` | Y | Int(10) | 折讓總金額 |
| `BuyerEmail` | N | Varchar(50) | 買受人電子信箱 |
| `Status` | Y | Varchar(1) | `0`=不立即確認折讓、`1`=立即確認折讓 |

#### Result

| 欄位 | 型態 | 說明 |
|------|------|------|
| `MerchantID` | Varchar(15) | 商店代號 |
| `AllowanceNo` | Varchar(20) | 折讓號（後續觸發、作廢均使用）|
| `InvoiceNumber` | Varchar(10) | 原發票號碼 |
| `MerchantOrderNo` | Varchar(20) | 原發票自訂編號 |
| `AllowanceAmt` | Int(10) | 折讓金額 |
| `RemainAmt` | Int(10) | 折讓後剩餘發票金額 |
| `CheckCode` | Varchar(64) | SHA256 驗證碼 |

---

### 5. 觸發確認 / 取消折讓

當 `Status=0` 開立後，後續可確認或取消折讓。

**端點：**

| 環境 | URL |
|------|-----|
| 測試 | `POST https://cinv.ezpay.com.tw/Api/allowance_touch_issue` |
| 正式 | `POST https://inv.ezpay.com.tw/Api/allowance_touch_issue` |

#### PostData_ 內含欄位

| 欄位 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `RespondType` | Y | Varchar(5) | `JSON` / `String` |
| `Version` | Y | Varchar(5) | 固定 `1.0` |
| `TimeStamp` | Y | Varchar(30) | Unix 時間戳 |
| `AllowanceStatus` | Y | Varchar(1) | `C` 確認折讓、`D` 取消折讓 |
| `AllowanceNo` | Y | Varchar(20) | 折讓號 |
| `MerchantOrderNo` | Y | Varchar(20) | 原發票自訂編號 |
| `TotalAmt` | Y | Int(10) | 折讓總金額 |

> **限制**：已確認折讓後，無法再執行取消折讓；只能改用「作廢折讓」。

---

### 6. 作廢折讓

**端點：**

| 環境 | URL |
|------|-----|
| 測試 | `POST https://cinv.ezpay.com.tw/Api/allowanceInvalid` |
| 正式 | `POST https://inv.ezpay.com.tw/Api/allowanceInvalid` |

> **注意**：路徑為 `allowanceInvalid`（駝峰式），與其他 API 的底線命名不同。

#### PostData_ 內含欄位

| 欄位 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `RespondType` | Y | Varchar(5) | `JSON` / `String` |
| `Version` | Y | Varchar(5) | 固定 `1.0` |
| `TimeStamp` | Y | Varchar(30) | Unix 時間戳 |
| `AllowanceNo` | Y | Varchar(25) | 欲作廢之折讓號 |
| `InvalidReason` | Y | Varchar(6) | 作廢原因（中 6 字 / 英 20 字內）|

---

### 7. 查詢發票

**端點：**

| 環境 | URL |
|------|-----|
| 測試 | `POST https://cinv.ezpay.com.tw/Api/invoice_search` |
| 正式 | `POST https://inv.ezpay.com.tw/Api/invoice_search` |

#### PostData_ 內含欄位

| 欄位 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `RespondType` | Y | Varchar(5) | `JSON` / `String` |
| `Version` | Y | Varchar(5) | 固定 `1.3` |
| `TimeStamp` | Y | Varchar(30) | Unix 時間戳 |
| `SearchType` | N | Varchar(1) | `0`（預設）= 發票號碼+隨機碼；`1`= 訂單編號+發票金額 |
| `MerchantOrderNo` | C | Varchar(20) | 訂單編號（`SearchType=1` 時必填）|
| `TotalAmt` | C | Varchar(10) | 發票金額（`SearchType=1` 時必填）|
| `InvoiceNumber` | C | Varchar(10) | 發票號碼（`SearchType=0` 時必填）|
| `RandomNum` | C | Varchar(4) | 防偽隨機碼（`SearchType=0` 時必填）|
| `DisplayFlag` | N | Varchar(1) | `1`=於 ezPay 網頁顯示查詢結果；`2`=回傳查詢結果網址；不帶=以參數回傳發票資料 |

#### Result（重要欄位）

| 欄位 | 型態 | 說明 |
|------|------|------|
| `MerchantID` | Varchar(15) | 商店代號 |
| `InvoiceTransNo` | Varchar(20) | ezPay 開立序號 |
| `MerchantOrderNo` | Varchar(20) | 商店自訂編號 |
| `InvoiceNumber` | Varchar(10) | 發票號碼 |
| `RandomNum` | Varchar(4) | 防偽隨機碼 |
| `BuyerName` | Varchar(60) | 買受人名稱 |
| `BuyerUBN` | Varchar(10) | 買受人統編 |
| `BuyerEmail` | Varchar(100) | 買受人 Email |
| `InvoiceType` | Varchar(2) | `07` 一般稅額 / `08` 特種稅額 |
| `Category` | Varchar(5) | `B2B` / `B2C` |
| `TaxType` | Varchar(2) | `1` / `2` / `3` / `9` |
| `TaxRate` | Float(6,4) | 稅率 |
| `Amt` | Int(10) | 銷售額合計 |
| `AmtSales` / `AmtZero` / `AmtFree` | Int(10) | 混合稅率三類銷售額（`TaxType=9` 才提供）|
| `TaxAmt` | Int(10) | 稅額 |
| `TotalAmt` | Int(10) | 發票金額 |
| `CarrierType` | Varchar(2) | 載具類別 |
| `CarrierNum` | Varchar(50) | 載具編號 |
| `LoveCode` | Varchar(10) | 捐贈碼 |
| `PrintFlag` | Varchar(1) | `Y` / `N` |
| `KioskPrintFlag` | Varchar(1) | `1` 開放超商 Kiosk 列印 |
| `CreateTime` | DateTime | 開立時間 |
| `ItemDetail` | Text (JSON) | 商品明細（含 `ItemNum`、`ItemName`、`ItemCount`、`ItemWord`、`ItemPrice`、`ItemAmount`、`ItemTaxType`）|
| `InvoiceStatus` | Varchar(1) | `1` 已開立、`2` 已作廢 |
| `UploadStatus` | Varchar(1) | `0` 未上傳、`1` 已上傳成功、`2` 上傳中、`3` 上傳失敗、`4` 上傳逾時 |
| `BarCode` / `QRcodeL` / `QRcodeR` | – | 條碼（僅 `PrintFlag=Y` 時提供）|
| `CheckCode` | Varchar(64) | SHA256 驗證碼 |

---

## B2B 電子發票（三聯式）

ezPay 並無獨立的 B2B 端點，僅在開立發票時將 `Category` 設為 `B2B`，並依下述差異填寫欄位。

### B2B 開立發票

**端點：** 同 B2C（`POST /Api/invoice_issue`）

#### 與 B2C 之主要差異

| 項目 | B2C | B2B |
|------|-----|-----|
| `Category` | `B2C` | `B2B` |
| `BuyerName` | 個人或會員代號（限 30 字元）| **買方營業人名稱（限 60 字元，若不足以使用，可填統編）** |
| `BuyerUBN` | 非必填 | **必填**（純數字 8 碼）|
| `PrintFlag` | 視載具／捐贈而定 | **固定 `Y`（一律可列印紙本）** |
| `CarrierType` | 可填 | **不可使用（須留空）** |
| `LoveCode` | 可填 | **不可使用（須留空）** |
| `TaxType` | 支援 `1`／`2`／`3`／`9` | 支援 `1`／`2`／`3`（**不可用 `9` 混合**）|
| `ItemPrice` | 含稅 | **未稅** |
| `ItemAmt` | 含稅 | **未稅** |
| `Amt` | 未稅銷售額 | 未稅銷售額（同 B2C）|
| `TaxAmt` | 由商店計算填入 | 由商店計算填入 |
| `TotalAmt` | `Amt + TaxAmt` | `Amt + TaxAmt` |

> **注意**：ezPay 的 `Amt` 在 **B2C 與 B2B 都是未稅**，這點與綠界（B2C 是含稅）不同。`ItemPrice` 和 `ItemAmt` 才是 B2C 含稅、B2B 未稅。

#### B2B 範例（PostData_ 解密後）

```json
{
    "RespondType": "JSON",
    "Version": "1.5",
    "TimeStamp": "1746576000",
    "MerchantOrderNo": "B2B20260507001",
    "Status": "1",
    "Category": "B2B",
    "BuyerName": "範例科技股份有限公司",
    "BuyerUBN": "54352706",
    "BuyerAddress": "台北市南港區南港路二段97號8樓",
    "BuyerEmail": "ar@example.com",
    "PrintFlag": "Y",
    "TaxType": "1",
    "TaxRate": "5",
    "Amt": "9524",
    "TaxAmt": "476",
    "TotalAmt": "10000",
    "ItemName": "顧問服務費",
    "ItemCount": "1",
    "ItemUnit": "式",
    "ItemPrice": "9524",
    "ItemAmt": "9524",
    "Comment": "B2B 範例"
}
```

### B2B 作廢／折讓／作廢折讓／查詢

均與 B2C 共用同一端點與參數結構，**無獨立 B2B 路徑**。

| 動作 | 端點 |
|------|------|
| 作廢發票 | `POST /Api/invoice_invalid` |
| 開立折讓 | `POST /Api/allowance_issue` |
| 觸發確認/取消折讓 | `POST /Api/allowance_touch_issue` |
| 作廢折讓 | `POST /Api/allowanceInvalid` |
| 查詢 | `POST /Api/invoice_search` |

---

## 共用功能

### 1. 字軌號碼管理

**官方文檔：** EZP_Track v1.0.0

#### 1.1 新增字軌

**端點：** `POST /Api_number_management/createNumber`

| 欄位 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `CompanyID_` | Y | Varchar(16) | 會員編號（注意是 `CompanyID_` 不是 `MerchantID_`）|
| `PostData_` | Y | text | 加密內容 |

PostData_ 內含：

| 欄位 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `RespondType` | Y | Varchar(5) | `JSON` / `String` |
| `Version` | Y | Varchar(5) | 固定 `1.0` |
| `TimeStamp` | Y | Varchar(10) | Unix 時間戳 |
| `Year` | Y | Varchar(3) | 民國年（例 `115`）|
| `Term` | Y | Varchar(1) | 期別 `1`~`6`（一二月/三四月…十一十二月）|
| `AphabeticLetter` | Y | Varchar(2) | 字軌英文代碼（兩碼大寫英文）|
| `StartNumber` | Y | Varchar(8) | 起始號（如 `00000001`）|
| `EndNumber` | Y | Varchar(8) | 結束號（如 `00009999`）|
| `Type` | Y | Varchar(2) | `07` 一般稅額 / `08` 特種稅額 |

#### 1.2 字軌資料管理（啟用 / 暫停 / 停用）

**端點：** `POST /Api_number_management/[資料管理路徑]`（透過 `ManagementNo` 切換狀態）

| 狀態 | 說明 |
|------|------|
| 啟用 | 目前發票開立使用此組字軌（同期別僅能啟用一組）|
| 暫停 | 字軌待用，可再啟用 |
| 停用 | 永久停用，不可再啟用 |

#### 1.3 字軌資料查詢

**端點：** `POST /Api_number_management/[查詢路徑]`

可查詢字軌建立時間、起訖號碼、剩餘張數、目前狀態。

---

### 2. 手機條碼驗證

**官方文檔：** EZP_BDV v1.0.0

**端點：** `POST /Api_inv_application/checkBarCode`

注意：此 API 多了 `CheckValue` 與 `Version` 等最外層參數，且 `Result` 也是 AES 加密 hex 字串需自行解密。

#### 最外層欄位

| 欄位 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `MerchantID_` | Y | Varchar(15) | 商店代號 |
| `Version` | Y | Varchar(5) | 固定 `1.0` |
| `RespondType` | Y | Varchar(5) | `JSON` / `String` |
| `PostData_` | Y | text | AES 加密內容 |
| `CheckValue` | Y | Varchar(64) | `SHA256(HashKey={key}&{PostData_}&HashIV={iv})` 大寫 |

#### PostData_ 內含

| 欄位 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `TimeStamp` | Y | Varchar(10) | Unix 時間戳 |
| `CellphoneBarcode` | Y | Varchar(8) | 手機條碼（`/` 開頭+7 碼）|

#### 手機條碼格式檢核

第 1 碼必為 `/`，後 7 碼僅可使用：

```
0-9  A-Z  +  -  .
```

共 39 個字元（限大寫英字）。

#### Result（解密後）

| 欄位 | 型態 | 說明 |
|------|------|------|
| `CellphoneBarcode` | Varchar(8) | 驗證的手機條碼 |
| `IsExist` | Varchar(1) | `Y` 存在於財政部、`N` 不存在 |

---

### 3. 捐贈碼驗證

**端點：** `POST /Api_inv_application/checkLoveCode`

最外層欄位與手機條碼驗證相同。

#### PostData_ 內含

| 欄位 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `TimeStamp` | Y | Varchar(10) | Unix 時間戳 |
| `LoveCode` | Y | Int(7) | 捐贈碼（3~7 碼純數字）|

#### Result（解密後）

| 欄位 | 型態 | 說明 |
|------|------|------|
| `Lovecode` | Int(7) | 驗證的捐贈碼 |
| `IsExist` | Varchar(1) | `Y` 存在 / `N` 不存在 |

---

### 4. 自然人憑證條碼格式

雖無獨立驗證 API，開立時須符合：**2 碼大寫英文 + 14 碼數字**（共 16 碼）。

---

### 5. 批次開立發票

**官方文檔：** ezPay_invoice_by_batch_file v1.0.3

不透過 API，改用上傳檔案方式：

| 項目 | 規格 |
|------|------|
| 檔案格式 | `.txt`（半形逗號分隔）或 `.csv`（欄分隔）|
| 檔案大小 | 限 800 KB 以下 |
| 檔案命名 | `{商店代號}_{YYYYMMDD}.txt`（例：`3622183_20260507.txt`）|
| 上傳路徑 | 後台【加值中心】→【電子發票平台】→【開立發票】→【批次開立】|

#### 檔案內容結構

- **首錄 (H)**：每檔僅 1 筆，欄位包含 `H`、執行類別 `INVO`、會員編號、商店代號、執行開立日期。
- **明細錄 (S)**：每張發票 1 筆，包含商店自訂編號、發票種類、買受人資訊、載具、稅別、稅率、銷售額、稅額、發票金額、商品明細、備註等共 17+ 個欄位。

> 批次開立等同即時開立（`Status=1`），無延遲機制。

---

### 6. 境外電商版

**官方文檔：** EZP_CES v1.0.0

針對境外電商（外幣計價）設計，端點與一般版類似但 PostData_ 內額外含「幣別代碼」、「外幣金額」等欄位。請另行參閱 `EZP_CES_1_0_0` 手冊。

---

### 7. 載具類型一覽

| 代碼 | 名稱 | 格式 | 說明 |
|------|------|------|------|
| `''` | 無載具 | – | 一般發票，須索取紙本或捐贈 |
| `0` | 手機條碼載具 | `/` 開頭共 8 碼 | 須先透過 `checkBarCode` 驗證 |
| `1` | 自然人憑證條碼 | 2 碼英文 + 14 碼數字 | 共 16 碼 |
| `2` | ezPay 電子發票會員載具 | 賣方自訂代號 | 不需事先申請；買受人 Email/手機/會員編號等可識別代號；ezPay 以「賣方統編 + 代號」唯一識別 |

> ezPay 與綠界的載具代碼編號**不同**：綠界 `1=綠界載具、2=自然人憑證、3=手機條碼`；ezPay `0=手機條碼、1=自然人憑證、2=ezPay 載具`。串接時請注意對應。

---

### 8. 課稅別說明

| 代碼 | 名稱 | 說明 |
|------|------|------|
| `1` | 應稅 | 一般 5% 或特種稅率 |
| `2` | 零稅率 | 須帶 `CustomsClearance` 報關標記 |
| `3` | 免稅 | 土地、未加工農產品等 |
| `9` | 混合 | **僅限 B2C**；須帶 `AmtSales`、`AmtZero`、`AmtFree`、`ItemTaxType` |

---

## 錯誤代碼

下表整合自 EZP_INVI 第九章與相關手冊：

### 通用 / 加密相關

| 代碼 | 說明 | 處理方式 |
|------|------|---------|
| `KEY10002` | 資料解密錯誤 | 確認 HashKey/HashIV、Padding、加密演算法（AES-256-CBC）|
| `KEY10004` | 資料不齊全 | 確認 `PostData_` 解密後欄位是否完整 |
| `KEY10006` | 商店未申請啟用電子發票 | 後台確認電子發票服務狀態 |
| `KEY10007` | 頁面停留超過 30 分鐘 | 重新整理頁面後再送 |
| `KEY10010` | 商店代號空白 | 確認 `MerchantID_`（含底線）已填 |
| `KEY10011` | PostData_ 欄位空白 | 確認 `PostData_`（含底線）已填 |
| `KEY10012` | 資料傳遞錯誤 | 檢查 Form Post 格式、Content-Type |
| `KEY10013` | 資料空白 | 檢查必填欄位 |
| `KEY10014` | TimeOut | 檢查 `TimeStamp` 是否在合理區間（建議 ±10 分鐘）|
| `KEY10015` | 發票金額格式錯誤 | `Amt`、`TaxAmt`、`TotalAmt` 必須為純數字 |

### 開立發票相關

| 代碼 | 說明 | 處理方式 |
|------|------|---------|
| `INV10003` | 商品資訊格式錯誤或缺少資料 | 檢查 `ItemName`/`ItemCount`/`ItemPrice`/`ItemAmt` 是否齊全且 `|` 分隔正確 |
| `INV10004` | 商品小計計算錯誤 | 確認 `ItemAmt = ItemCount × ItemPrice` |
| `INV10006` | 稅率格式錯誤 | `TaxRate` 應為純數字（一般稅率帶 `5`，零/免稅帶 `0`）|
| `INV10012` | 發票金額、課稅別驗證錯誤 | 確認 `Amt + TaxAmt = TotalAmt`，課稅別欄位一致 |
| `INV10013` | 發票欄位資料不齊全或格式錯誤 | 對照必填欄位逐項檢查 |
| `INV10014` | 自訂編號格式錯誤 | `MerchantOrderNo` 限英、數字、底線 `_` |
| `INV10015` | 無未稅金額 | `Amt` 為空或 `0` |
| `INV10016` | 無稅金 | `TaxAmt` 為空或 `0`（應稅時）|
| `INV10017` | 輸入的版本不支援混合稅率功能 | `Version` 應使用 `1.5` 才支援 `TaxType=9` |
| `INV10019` | 資料含有控制碼 | 移除特殊控制字元 |
| `INV10020` | 暫停使用 | 該服務／字軌已暫停 |
| `INV10021` | 異常終止 | 重試；若持續發生請聯繫客服 |

### 查詢／作廢相關

| 代碼 | 說明 | 處理方式 |
|------|------|---------|
| `INV20006` | 查無發票資料 | 確認 `InvoiceNumber`+`RandomNum` 或 `MerchantOrderNo`+`TotalAmt` 組合 |
| `INV70001` | 欄位資料格式錯誤 | 對照型態長度檢查 |
| `INV70002` | 上傳失敗之發票不得作廢 | 該發票尚未成功上傳財政部，無法作廢；可聯繫客服協助 |
| `INV90005` | 未簽訂合約或合約已到期 | 聯繫 ezPay 業務 |
| `INV90006` | 可開立張數已用罄 | 至後台新增字軌或購買額度 |
| `LIB10003` | 商店自訂編號重覆 | `MerchantOrderNo` 同店不可重複，請改用新編號 |
| `LIB10005` | 發票已作廢過 | 該發票已是作廢狀態 |
| `LIB10007` | 無法作廢 | 該發票已執行折讓，不可作廢；應改用「作廢折讓」 |
| `LIB10008` | 超過可作廢期限 | 已超過奇數月 14 日前的作廢時點，無法作廢 |
| `LIB10009` | 發票已開立但未上傳，無法作廢 | 須等開立資料上傳財政部完成（次日 06:00 後）才可作廢 |
| `NOR10001` | 網路連線異常 | 重試；確認網路與防火牆 |

### 作廢折讓相關（IAI 系列）

| 代碼 | 說明 | 處理方式 |
|------|------|---------|
| `IAI10001` | 缺少參數 | 檢查必填欄位 |
| `IAI10002` | 查詢失敗 | 確認 `AllowanceNo` 正確 |
| `IAI10003` | 更新失敗 | 重試；若持續發生請聯繫客服 |
| `IAI10004` | 參數錯誤 | 對照欄位格式 |
| `IAI10005` | 新增失敗 | 重試 |
| `IAI10006` | 異常終止 | 聯繫客服 |

### 手機條碼／捐贈碼驗證錯誤碼

| 代碼 | 說明 |
|------|------|
| `API10001` | 缺少參數 |
| `API10002` | 查詢失敗 |
| `API10004` | 參數錯誤 |
| `CBC10001` | 手機條碼欄位空白 |
| `CBC10002` | 手機條碼格式錯誤 |
| `CBC10003` | 手機條碼驗證異常終止 |
| `CBC10004` | 財政部大平台連線異常（手機條碼）|
| `CLC10001` | 捐贈碼欄位空白 |
| `CLC10002` | 捐贈碼格式錯誤 |
| `CLC10003` | 捐贈碼驗證異常終止 |
| `CLC10004` | 財政部大平台連線異常（捐贈碼）|

---

## 補充說明

### 金額計算邏輯（重點）

ezPay 在 B2C 與 B2B 的金額處理有微妙差異：

**B2C（二聯式，含稅）：**

```
Amt        = 未稅銷售額（系統會用 TotalAmt 反推或檢核）
TaxAmt     = 稅額
TotalAmt   = 含稅總金額（= Amt + TaxAmt）

ItemPrice  = 含稅單價
ItemAmt    = 含稅小計
```

**B2B（三聯式，未稅）：**

```
Amt        = 未稅銷售額
TaxAmt     = 稅額（須自行計算）
TotalAmt   = 含稅總金額（= Amt + TaxAmt）

ItemPrice  = 未稅單價
ItemAmt    = 未稅小計
```

**檢核公式：**

1. 商品小計 = 商品數量 × 商品單價
2. 發票金額 = 銷售額 + 稅額（`TotalAmt = Amt + TaxAmt`）
3. 折讓總金額 = 折讓商品小計 + 折讓商品稅額

> **建議**：實作時務必由前端先依 `Category` 切換含稅／未稅模式，再算 `Amt`、`TaxAmt`、`TotalAmt`，避免反推誤差。

### 發票上傳排程

| 時間 | 動作 |
|------|------|
| 每日 01:00 | ezPay 將前一日（00:00–23:59）的開立、作廢、折讓資料上傳財政部 |
| 每日 06:00 | 依財政部回傳結果更新 `UploadStatus` |

### 通知機制

ezPay 平台會於發票開立、作廢、折讓時自動寄送 Email 通知至 `BuyerEmail`（若有提供）。**目前並無 Server-side Webhook 通知機制**——若需即時通知，需要：

1. 商家自行儲存 `RespondType=JSON` 的同步回應結果，或
2. 定時呼叫查詢 API 比對狀態。

### 常用 Version 數值速查

| API | Version |
|-----|---------|
| 開立發票 (`invoice_issue`) | `1.5` |
| 觸發開立 (`invoice_touch_issue`) | `1.0` |
| 作廢發票 (`invoice_invalid`) | `1.0` |
| 開立折讓 (`allowance_issue`) | `1.3` |
| 觸發折讓 (`allowance_touch_issue`) | `1.0` |
| 作廢折讓 (`allowanceInvalid`) | `1.0` |
| 查詢發票 (`invoice_search`) | `1.3` |
| 字軌新增 / 管理 / 查詢 | `1.0` |
| 手機條碼 / 捐贈碼驗證 | `1.0` |

---

## 開發筆記 (踩坑紀錄)

### 1. AES 是 256-CBC，不是 128-CBC

ezPay 使用 **AES-256-CBC**（Key 32 bytes），而綠界 ECPay 使用 **AES-128-CBC**（Key 16 bytes）。共用元件時別忘了切換。

### 2. PKCS7 Padding 需自行處理

PHP 範例中使用 `OPENSSL_RAW_DATA | OPENSSL_ZERO_PADDING` 是因為先以 `addpadding()` 自行補齊 32 bytes 區塊；Node.js 須 `cipher.setAutoPadding(false)`，否則會雙重 padding 導致解密失敗。

### 3. 加密輸出是 Hex 不是 Base64

ezPay 的 `PostData_` 是小寫 hex，與綠界（Base64）不同。`bin2hex()`（PHP）或 `digest('hex')`（Node.js）即可。

### 4. 路徑大小寫陷阱：`allowanceInvalid`

開立、查詢、作廢發票 API 均為小寫底線（`invoice_issue`、`invoice_invalid`），但「作廢折讓」是駝峰：`allowanceInvalid`。串接時需特別處理 URL。

### 5. B2B 與 B2C 共用端點

ezPay 沒有獨立的 B2B 路徑（不像綠界 `/B2BInvoice/Issue`），改用 `Category=B2B` 區分，且要把 `PrintFlag` 強制 `Y`、清空 `CarrierType`/`LoveCode`。

### 6. `Amt` 一律是未稅

無論 `Category` 為 B2C 或 B2B，`Amt` 都是未稅銷售額。但 `ItemPrice`/`ItemAmt` 在 B2C 是含稅、B2B 是未稅。這個不對稱很容易踩坑。

### 7. 多項商品以 `|` 分隔

`ItemName`、`ItemCount`、`ItemUnit`、`ItemPrice`、`ItemAmt`、`ItemTaxType` 都是字串型欄位，多項商品以 ASCII `|` 分隔，且各欄位數量必須一致。

### 8. `MerchantOrderNo` 同店不可重複

`MerchantOrderNo` 是商店端的唯一鍵；同筆完全相同的 `PostData_` 會回傳 `SUCCESS`（idempotent），但若編號相同、其他欄位不同，會擲 `LIB10003`。建議使用 UUID 或時間戳組合。

### 9. CarrierNum 需先 rawurlencode

載具編號可能含特殊字元（如手機條碼的 `/`），加密前應先 `rawurlencode($carrierNum)`，否則對方可能濾除。

### 10. CheckCode 驗證僅針對 5 個指定欄位

回傳的 `CheckCode` 只用 `InvoiceTransNo`、`MerchantID`、`MerchantOrderNo`、`RandomNum`、`TotalAmt` 計算（A→Z 排序）。其他欄位（如 `BuyerName`、`InvoiceNumber`）**不在驗證範圍**，這是平台設計，需注意。

### 11. 載具代碼編號與綠界相反

ezPay：`0`=手機條碼、`1`=自然人憑證、`2`=ezPay 會員載具
綠界：`1`=綠界會員載具、`2`=自然人憑證、`3`=手機條碼

抽象化載具邏輯時務必做映射層。

### 12. 沒有獨立 Webhook

目前 ezPay 不主動向商家伺服器發出 callback，需以同步回應為準或自行排程查詢。

### 13. `Status=0`（等待觸發）需後續呼叫 `invoice_touch_issue`

很多串接者誤以為 `Status=0` 是「不開立」，實際上是「先暫存，待觸發」。若沒呼叫 `invoice_touch_issue`，發票永不上傳財政部，須注意流程設計。

### 14. 作廢期限：奇數月 14 日

只能作廢「前兩個月」開立的發票，且要在「奇數月 14 日前」執行（例 7/14 前可作廢 5/1–6/30 的發票）。超過期限只能改用折讓。

---

## 相關文件

- [綠界 ECPay API 規格](./ECPAY_API_REFERENCE.md)
- [速買配 SmilePay API 規格](./SMILEPAY_API_REFERENCE.md)
- [光貿 Amego API 規格](./AMEGO_API_REFERENCE.md)
- [發票開立流程](./INVOICE_FLOW.md)

---

## 聯絡客服

- **官方網站**：https://www.ezpay.com.tw/
- **電子發票平台（測試）**：https://cinv.ezpay.com.tw/
- **電子發票平台（正式）**：https://inv.ezpay.com.tw/
- **官方文件下載**：https://inv.ezpay.com.tw/Invoice_index/download
- **客服信箱**：請至官網查詢

---

最後更新：2026/05/07
文件版本：基於 EZP_INVI v1.2.2、EZP_Track v1.0.0、EZP_BDV v1.0.0、批次開立 v1.0.3 之官方文件整理 + 實作筆記
