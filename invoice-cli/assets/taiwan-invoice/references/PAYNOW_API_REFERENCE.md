# 立吉富 PayNow 電子發票 API 完整技術規格 (PayNow Invoice API)

> 官方文檔：https://docs.paynow.com.tw/developer/docs/invoice/
> 服務商：立吉富線上金流股份有限公司 (PayNow)
> 主站：https://gateway.paynow.com.tw/
> 支援 B2C／B2B 電子發票及 POS 機開立流程
> 版本：Invoice Management v1.5（依官方 API Reference 索引）

---

## 目錄
1. [基本說明](#基本說明)
2. [加密方式](#加密方式)
3. [B2C 電子發票](#b2c-電子發票)
4. [B2B 電子發票](#b2b-電子發票)
5. [POS 機開立流程](#pos-機開立流程)
6. [共用功能](#共用功能)
7. [錯誤代碼](#錯誤代碼)
8. [補充說明](#補充說明)

---

## 基本說明

### 服務簡介

PayNow（立吉富線上金流）是台灣全功能電商整合金流服務商，同時提供金流、物流、發票三大模組。發票服務支援一般串接（External）以及 POS 機批次取號開立兩種模式：

- **一般串接（external）**：以 API 由系統取得發票號碼並即時開立、作廢、折讓。
- **POS 機（pos）**：先批次配發未使用的發票號碼給商家自行管理，由商家自行帶隨機碼後上傳開立資料。未使用之號碼會於次期單數月 5 號自動上傳空白發票。

### 環境資訊

| 環境 | 說明 | URL 前綴 |
|------|------|---------|
| **測試環境（Sandbox）** | 開發、整合測試使用 | `https://invoiceapi-dev.paynow.com.tw/` |
| **正式環境（Production）** | 正式開立並上傳財政部 | `https://invoiceapi-prod.paynow.com.tw/` |

> 測試環境與正式環境為獨立空間，憑證與發票字軌不通用。

### 認證方式

PayNow 發票 API 採用 **JWT Bearer Token** 機制：

| 項目 | 說明 |
|------|------|
| **Authentication** | API Key (Bearer) |
| **Header 名稱** | `Authorization` |
| **Header 內容** | `Bearer <商家 JWT-Token>` |
| **取得方式** | 串接前需先向 PayNow 申請商家 JWT-Token；測試／正式 Token 為兩組獨立金鑰 |

呼叫範例：

```http
POST /invoice/issue HTTP/1.1
Host: invoiceapi-dev.paynow.com.tw
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
```

> ⚠️ Source did not document this operation; cross-reference official PDF when adding.
> 各操作端點（如 `/invoice/issue`、`/invoice/void`...）、Request/Response Schema 之欄位細節皆未在公開頁面揭露，需依商家後台下載之「Invoice Management v1.5」PDF 取得。本檔以官方流程說明所列出的 API 名稱為骨架，欄位部分以 TODO 標示。

### API 編碼格式

| 項目 | 值 |
|------|-----|
| **Content-Type** | `application/json` |
| **字元編碼** | `UTF-8` |
| **傳輸方式** | `POST`（JSON 主體 + Bearer Token） |
| **回應格式** | JSON |

### 流程總覽

```
[一般流程]
取得 JWT-Token → 開立發票 → (作廢發票) → (開立折讓) → (作廢折讓)

[POS 流程]
取得 JWT-Token → POS 取得發票號碼（批次） → 商家自行管理 → POS 開立發票（帶隨機碼）
```

---

## 加密方式

### Token 鑑權

PayNow 發票 API 主要使用 **JWT Bearer Token** 進行身份驗證，**不**像綠界使用 AES + URL Encode 雙層加密。Request body 直接使用明文 JSON 傳送，於 HTTPS 通道下進行。

```javascript
// Node.js 呼叫範例
const fetch = require('node-fetch')

async function callPayNowInvoice(endpoint, body, jwtToken) {
  const res = await fetch(`https://invoiceapi-dev.paynow.com.tw${endpoint}`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${jwtToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(body)
  })
  return res.json()
}
```

### 與金流端 AES-256 加密的關係

PayNow 金流 API（`paynowapi_js.aspx` 等舊式服務）使用 **AES-256-CBC** + 動態 Key/IV（透過 `GP`/`GK` 檢核碼系統取得）。如果整合方案是「金流交易 + 同時開立發票」（例如 `cashflow-online-shopping-car` 一頁式購物車回傳 `InvoiceStatus`、`InvoiceNo`、`batchNo` 三欄），則金流端仍需依下列方式處理：

| 項目 | 值／規則 |
|------|---------|
| **演算法** | AES-256-CBC |
| **Padding** | Zeros |
| **Key 長度** | 32 bytes（UTF-8） |
| **IV 長度** | 16 bytes（UTF-8） |
| **Key／IV 取得** | 透過檢核碼服務 `GK` 動態取得 `EncryptionKey` / `EncryptionIV` |
| **檢核碼用 Key** | `paynowencryptpaynowcomtw28229955` |
| **檢核碼用 IV** | `encrypt282299550` |

**檢核碼系統（GP/GK）端點：**

```
正式：https://www.paynow.com.tw/service/paynowapi_js.aspx
測試：https://test.paynow.com.tw/service/paynowapi_js.aspx
```

> 發票 API 端點（`invoiceapi-prod.paynow.com.tw`）與檢核碼系統為不同子網域；發票串接本身僅需 JWT，**不需要**金流端的 AES-256 流程。本節僅供「金流回拋附帶發票資料」的整合場景參考。

### AES-256-CBC 加解密範例（C#）

> 引自 PayNow 金流附錄，供需要在金流回拋中解密發票欄位的整合方使用。

```csharp
private string AES256_Encrypt(string Content, string Key, string IV)
{
    byte[] byteString = Encoding.UTF8.GetBytes(Content);
    byte[] ByteIVString  = Encoding.UTF8.GetBytes(IV);
    byte[] ByteKeyString = Encoding.UTF8.GetBytes(Key);
    RijndaelManaged rDel = new RijndaelManaged
    {
        Key = ByteKeyString,
        IV = ByteIVString,
        Mode = CipherMode.CBC,
        Padding = PaddingMode.Zeros
    };
    ICryptoTransform cTransform = rDel.CreateEncryptor();
    byte[] ResultArray = cTransform.TransformFinalBlock(byteString, 0, byteString.Length);
    return Convert.ToBase64String(ResultArray, 0, ResultArray.Length);
}
```

### TimeStr 時間戳格式（金流附帶發票時使用）

PayNow 金流 API 自訂 10 碼時間戳格式：

```
[西元年最後 1 碼][一年中第幾天 3 碼][時 2 碼][分 2 碼][秒 2 碼]
```

範例：`2019-11-24 00:50:18` → `9328005018`

```csharp
string TimeStr =
    StrRight(DateTime.Now.Year.ToString(), 1) +
    DateTime.Now.DayOfYear.ToString() +
    StrRight("0" + DateTime.Now.Hour.ToString(), 2) +
    StrRight("0" + DateTime.Now.Minute.ToString(), 2) +
    StrRight("0" + DateTime.Now.Second.ToString(), 2);
```

---

## B2C 電子發票

> 官方文件僅描述操作流程與 API 名稱，**詳細 Request／Response Schema 必須以 PayNow 提供之「Invoice Management v1.5」PDF 為準**。

### 1. 開立發票

**端點：** `POST /invoice/issue`（路徑名稱以官方 PDF 為主）

依官方流程說明：「使用 PayNow 的 開立發票 API 來開立發票，會根據未開立的訂單編號配一個未使用的發票號碼開立發票。」

#### 請求參數（依台灣電子發票通用欄位推估）

> ⚠️ Source did not document this operation; cross-reference official PDF when adding.

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `OrderNo` | String | Y | 商家自訂訂單編號（不可重複） |
| `BuyerName` | String | N | 買方名稱 |
| `BuyerIdentifier` | String(8) | N | 買方統編（B2B 必填） |
| `BuyerEmail` | String | N | 買方電子信箱 |
| `BuyerPhone` | String | N | 買方電話 |
| `BuyerAddress` | String | N | 買方地址 |
| `CarrierType` | String | N | 載具類別（手機條碼／自然人憑證／會員載具） |
| `CarrierNum` | String | N | 載具號碼 |
| `Donation` | Boolean | N | 是否捐贈 |
| `LoveCode` | String(7) | N | 愛心碼（捐贈時必填） |
| `Print` | Boolean | N | 是否列印 |
| `TaxType` | String | Y | 課稅別（應稅／零稅率／免稅／混合） |
| `Amount` | Number | Y | 發票金額合計 |
| `Items` | Array | Y | 商品明細 |

> 上述欄位名稱為依台灣電子發票通用慣例擬定，實際 PayNow 採用的欄位名稱（例如 `mem_cid`、`buyersafeno`、`InvoiceNo` 等）以官方 PDF 為主。請於整合時向 einvoice@paynow.com.tw 索取最新版規格。

#### 回應欄位（推估）

| 欄位 | 型別 | 說明 |
|------|------|------|
| `Status` | String | 開立結果：`success` / `fail` |
| `InvoiceNo` | String(10) | 發票號碼（例如 `AB12345678`） |
| `InvoiceDate` | String | 發票開立時間 |
| `RandomNumber` | String(4) | 隨機碼 |
| `Message` | String | 訊息描述 |

#### 請求範例（推估骨架）

```http
POST /invoice/issue HTTP/1.1
Host: invoiceapi-dev.paynow.com.tw
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json

{
  "OrderNo": "INV-20260507-001",
  "BuyerName": "王小明",
  "BuyerEmail": "buyer@example.com",
  "CarrierType": "3",
  "CarrierNum": "/ABC1234",
  "Donation": false,
  "Print": false,
  "TaxType": "1",
  "Amount": 10000,
  "Items": [
    {
      "ItemName": "網站開發服務",
      "ItemCount": 1,
      "ItemUnit": "式",
      "ItemPrice": 10000,
      "ItemAmount": 10000
    }
  ]
}
```

#### 回應範例（推估骨架）

```json
{
  "Status": "success",
  "InvoiceNo": "AB12345678",
  "InvoiceDate": "2026-05-07 10:00:00",
  "RandomNumber": "1234",
  "Message": "OK"
}
```

---

### 2. 作廢發票

**端點：** `POST /invoice/void`

官方說明：「使用 PayNow 的 作廢發票 API 來作廢已開立發票。」

> ⚠️ Source did not document this operation; cross-reference official PDF when adding.

#### 請求參數（推估）

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `InvoiceNo` | String(10) | Y | 發票號碼 |
| `InvoiceDate` | String | Y | 發票開立日期 |
| `Reason` | String | Y | 作廢原因 |

> 作廢限制（依財政部規定，需向 PayNow 確認）：發票須於開立當期內作廢；逾當期僅能改開折讓單。

---

### 3. 開立折讓單

**端點：** `POST /invoice/allowance`

官方說明：「使用 PayNow 的 開立折讓 API 建立對該發票號碼對票對應的折讓單。」

> ⚠️ Source did not document this operation; cross-reference official PDF when adding.

#### 請求參數（推估）

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `InvoiceNo` | String(10) | Y | 原發票號碼 |
| `InvoiceDate` | String | Y | 原發票開立日期 |
| `AllowanceAmount` | Number | Y | 折讓金額 |
| `AllowanceItems` | Array | Y | 折讓商品明細 |
| `NotifyMail` | String | N | 通知買方信箱 |
| `NotifyPhone` | String | N | 通知買方手機 |

---

### 4. 作廢折讓單

**端點：** `POST /invoice/allowance/void`

官方說明：「使用 PayNow 的 作廢折讓 API 來作廢已開立的折讓單。」

> ⚠️ Source did not document this operation; cross-reference official PDF when adding.

#### 請求參數（推估）

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `InvoiceNo` | String(10) | Y | 原發票號碼 |
| `AllowanceNo` | String(16) | Y | 折讓單號碼 |
| `Reason` | String | Y | 作廢原因 |

---

### 5. 查詢發票

> ⚠️ Source did not document this operation; cross-reference official PDF when adding.
> 官方公開頁面僅列出 開立／作廢／開立折讓／作廢折讓 4 個 API。發票查詢、列印、補寄通知等功能須以 PDF 規格為準。

**推估端點：** `POST /invoice/query`

可能可查詢條件：
- 依發票號碼（`InvoiceNo`）
- 依商家自訂訂單編號（`OrderNo`）
- 依日期區間（`StartDate` / `EndDate`）

---

## B2B 電子發票

> ⚠️ Source did not document this operation; cross-reference official PDF when adding.
> 官方流程圖未明確區分 B2C 與 B2B；推估 PayNow 採「同一個 `/invoice/issue` 端點，依 `BuyerIdentifier`（買方統編）是否帶值切換 B2C／B2B」的常見設計（與綠界、ezPay 一致）。

### B2B 與 B2C 主要差異（依台灣電子發票通用慣例）

| 項目 | B2C（二聯式） | B2B（三聯式） |
|------|--------------|--------------|
| 買方統編 | 選填 | **必填** |
| 列印註記 | 可選 | **強制列印** |
| 載具 | 可使用 | **不可使用** |
| 捐贈 | 可選 | **不可捐贈** |
| 金額計算 | 含稅 | 銷售額（未稅）+ 稅額 |
| 稅額欄位 | 系統計算 | **必填明列** |

### B2B 額外必填欄位（推估）

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `BuyerIdentifier` | String(8) | Y | 買方統編 |
| `BuyerName` | String | Y | 買方公司名稱 |
| `BuyerAddress` | String | N | 買方地址 |
| `SalesAmount` | Number | Y | 銷售額（未稅） |
| `TaxAmount` | Number | Y | 稅額 |
| `TotalAmount` | Number | Y | 總計（含稅） |

> 實作建議：以 `BuyerIdentifier` 是否帶值來判斷 B2C／B2B，避免維護兩條呼叫路徑。

---

## POS 機開立流程

PayNow 提供 POS 機獨立的取號／開立流程，適用於實體門市批次列印發票之場景。POS 流程不會走一般發票的「自動配號」邏輯，商家需自行管理已配發但未使用的號碼。

### 1. POS 取得發票號碼

**用途：** 由 PayNow 一次性配發一批未使用的發票號碼給商家。

> ⚠️ Source did not document this operation; cross-reference official PDF when adding.

**重要規則（官方原文）：**

- 為防止重複開立，取號後請自行管理該批發票號碼。
- 該批號碼**不會進入一般流程的發票上傳流程**內。
- **未使用的發票號碼會於次期單數月 5 號上傳空白發票。**

#### 推估請求參數

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `Quantity` | Number | Y | 要配發的發票號碼數量 |
| `InvoiceType` | String | N | 字軌類別（07 一般、08 特種） |

#### 推估回應

| 欄位 | 型別 | 說明 |
|------|------|------|
| `InvoiceNumbers` | Array<String> | 配發的發票號碼陣列 |
| `Period` | String | 對應之發票期別（例如 `11502`） |

---

### 2. POS 機開立發票

**用途：** 使用前一步取得的發票號碼，搭配商家自行產生的隨機碼，正式開立發票。

> ⚠️ Source did not document this operation; cross-reference official PDF when adding.

**重要規則：**

- **發票號碼**：必須是步驟 1 取得且尚未使用的號碼。
- **隨機碼**：必須由商家自行產生 4 碼數字，不可由 PayNow 配發。
- **重複開立**：因號碼由商家管理，請務必確保不重複使用。

#### 推估請求參數

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `InvoiceNo` | String(10) | Y | 步驟 1 取得的發票號碼 |
| `RandomNumber` | String(4) | Y | 商家自行產生之 4 碼隨機碼 |
| `OrderNo` | String | Y | 商家自訂訂單編號 |
| `InvoiceDate` | String | Y | 發票開立日期時間 |
| `BuyerName` | String | N | 買方名稱 |
| `BuyerIdentifier` | String(8) | N | 買方統編 |
| `Amount` | Number | Y | 發票金額 |
| `Items` | Array | Y | 商品明細 |

---

## 共用功能

### 1. 載具驗證

> ⚠️ Source did not document this operation; cross-reference official PDF when adding.

台灣常見三種載具，PayNow 推估亦支援：

| 載具類別 | 代碼（推估） | 格式 | 驗證方式 |
|---------|-------------|------|---------|
| 手機條碼 | `3` | `/` 開頭共 8 碼，[A-Z0-9.+-/]{7} | 由財政部驗證；多數平台會提供 `/carrier/check` 端點 |
| 自然人憑證 | `2` | 2 碼英文 + 14 碼數字（共 16 碼） | 同上 |
| 會員載具 | `1` | 視服務商定義（通常為 Email） | 平台內部驗證 |

### 2. 愛心碼驗證

> ⚠️ Source did not document this operation; cross-reference official PDF when adding.

愛心碼為 3-7 碼數字，由財政部公告。串接時通常需以 `/lovecode/check` 等端點先確認有效性。

### 3. 發票列印

> ⚠️ Source did not document this operation; cross-reference official PDF when adding.

PayNow 公開文件未揭露列印 API。常見作法：

- **POS 流程**：直接由商家 POS 系統列印（PayNow 僅負責配號與資料上傳）。
- **一般流程**：透過 PayNow 商家後台（invoice-admin 模組）列印或補寄。

### 4. 中獎通知

> ⚠️ Source did not document this operation; cross-reference official PDF when adding.

PayNow 站台提及「對獎 app」服務。中獎通知的 API（如 Webhook、推播）細節未在公開頁面揭露，需向客服確認。

### 5. 通知 Webhook

> ⚠️ Source did not document this operation; cross-reference official PDF when adding.

PayNow 公開頁面未揭露 Webhook 規格。建議向 einvoice@paynow.com.tw 索取「商家回拋網址設定」與「通知簽章驗證」說明。

---

## 錯誤代碼

> ⚠️ PayNow 發票 API 公開頁面**未提供**完整錯誤代碼表，**需向 PayNow 索取完整錯誤碼表**（einvoice@paynow.com.tw）。
> 以下表格列出依金流端錯誤代碼模式（M/A/C/B/R 字母前綴）推估之發票常見錯誤。

### 推估錯誤代碼分類

| 前綴 | 類別（依 PayNow 金流命名慣例推估） |
|------|----------------------------------|
| `I0xx` | 發票一般錯誤 |
| `I1xx` | 開立發票錯誤 |
| `I2xx` | 作廢發票錯誤 |
| `I3xx` | 折讓相關錯誤 |
| `I9xx` | 系統／通訊錯誤 |

### 通用錯誤（推估骨架）

| 代碼 | 說明 |
|------|------|
| `I000` | 參數錯誤 |
| `I001` | JWT-Token 無效或過期 |
| `I002` | 商家未授權使用發票服務 |
| `I003` | OrderNo 重複 |
| `I004` | 發票號碼不存在 |
| `I005` | 發票已作廢 |
| `I006` | 發票已開立過折讓 |

### 開立發票錯誤（推估）

| 代碼 | 說明 |
|------|------|
| `I101` | 買方統編格式錯誤 |
| `I102` | 載具格式錯誤 |
| `I103` | 愛心碼格式錯誤 |
| `I104` | 商品明細錯誤 |
| `I105` | 金額計算錯誤 |
| `I106` | 已無可用發票字軌 |
| `I107` | 載具與捐贈不可同時存在 |
| `I108` | B2B 不可使用載具或捐贈 |

### 作廢／折讓錯誤（推估）

| 代碼 | 說明 |
|------|------|
| `I201` | 發票不可作廢（已超過期限） |
| `I202` | 發票已有折讓不可作廢 |
| `I301` | 折讓金額超過發票金額 |
| `I302` | 折讓單不存在 |
| `I303` | 折讓單已作廢 |

> ⚠️ 上述代碼為推估，**正式錯誤碼編號需以 PayNow 官方文件為準**。

---

## 補充說明

### 課稅別說明（台灣電子發票通用）

| 代碼 | 名稱 | 說明 |
|------|------|------|
| `1` | 應稅 | 一般商品（5% 稅率） |
| `2` | 零稅率 | 外銷、國際運輸（需加註通關方式） |
| `3` | 免稅 | 土地、未經加工農產品等 |
| `9` | 混合 | 混合應稅與免稅 |

### 金額計算邏輯

**B2C（含稅顯示）：**

```
Amount = 含稅總額
TaxAmount = 系統自動計算（Amount / 21）
```

**B2B（未稅顯示）：**

```
SalesAmount = 未稅銷售額
TaxAmount = SalesAmount × 0.05
TotalAmount = SalesAmount + TaxAmount
```

**範例：**

```
商品未稅單價：9524 元
稅額：9524 × 0.05 = 476 元
含稅總計：9524 + 476 = 10000 元
```

### 發票號碼格式

依財政部規範：`[2 碼英文][8 碼數字]`，例如 `AB12345678`。
PayNow 一般流程由系統自動配號；POS 流程由 API 批次配發後商家自行管理。

### 隨機碼

4 碼數字。一般流程由 PayNow 自動產生；**POS 流程必須由商家自行產生**。

---

## 開發筆記（PayNow 整合提醒）

### 1. JWT-Token 與其他流程的差異

PayNow 發票 API 採用 JWT Bearer Token，流程上比綠界（AES + URL Encode + HashKey/HashIV）、ezPay（PostData_ 加密）簡單。但對應的代價是：

- Token 過期需重新申請（時效需向 PayNow 確認）
- 無法像綠界那樣直接以 HashKey 加解密驗證測試環境

### 2. 一般流程與 POS 流程不可混用

```
一般流程：PayNow 配號 + PayNow 自動上傳
POS 流程：商家批次取號 + 商家自行管理 + 未使用號碼於次期單數月 5 號自動上空白發票
```

請於專案啟動前明確選定流程；混用會導致發票號碼管理混亂。

### 3. 與 PayNow 金流整合時的發票欄位

若使用 PayNow 一頁式購物車（`cashflow-online-shopping-car`），交易回拋會帶下列三欄發票相關資訊：

| 欄位 | 說明 |
|------|------|
| `InvoiceStatus` | 發票開立結果（若有開立） |
| `InvoiceNo` | 發票號碼（若有開立） |
| `batchNo` | 發票隨機碼（若有開立） |

此情境下不需另外呼叫發票 API；PayNow 金流端已整合。

### 4. 公開文件揭露程度

PayNow 發票公開頁面僅有「流程圖 + API 名稱」，**所有欄位細節需向 PayNow 業務索取「Invoice Management v1.5」PDF**。本檔已將官方有揭露的部分（環境 URL、認證方式、API 名稱、POS 流程、空白發票上傳規則）盡量保留為事實陳述，未揭露之欄位以 TODO 標示。

### 5. 服務商聯絡管道

| 用途 | 聯絡方式 |
|------|---------|
| 客服總機 | service@paynow.com.tw / +886-2-2521-5088 |
| **發票業務** | einvoice@paynow.com.tw |
| 物流業務 | etracking@paynow.com.tw |
| 開發者文件 | https://docs.paynow.com.tw/developer/docs/invoice/ |
| API Reference 索引 | https://paynow-co.github.io/paynow-guideline/docs/api-reference/ |

---

## 相關文件

- [綠界 ECPay API 規格](./ECPAY_API_REFERENCE.md)
- [速買配 SmilePay API 規格](./SMILEPAY_API_REFERENCE.md)
- [光貿 Amego API 規格](./AMEGO_API_REFERENCE.md)

---

## 已知缺漏（Source Gaps）

下列項目於公開頁面未揭露，整合時必須以 PayNow PDF 規格或客服回覆補齊：

1. **完整端點路徑**：本檔以 `/invoice/issue`、`/invoice/void`、`/invoice/allowance`、`/invoice/allowance/void` 為推估值；正式路徑需以 PDF 為準。
2. **Request／Response Schema 完整欄位**：所有 API 的欄位名稱、型別、長度、必填規則。
3. **B2C／B2B 切換機制**：是否為單一端點 + `BuyerIdentifier` 切換，或分為兩個端點。
4. **錯誤代碼完整表**：本檔列出之 `I0xx`/`I1xx`/`I2xx`/`I3xx` 為推估分類，正式代碼需向 PayNow 索取。
5. **發票查詢／列印／補寄通知**：公開頁面未揭露相關 API。
6. **載具驗證 API**：手機條碼／愛心碼即時驗證端點。
7. **Webhook／回拋通知**：開立完成、作廢結果、折讓結果之通知簽章與重試規則。
8. **JWT-Token 申請與更新流程**：Token 有效期、撤銷、輪替方式。
9. **POS 取號的批次量上限**：單次最多可取多少組號碼、配額管理。
10. **空白發票自動上傳的時序**：「次期單數月 5 號」之具體時區與上傳結果通知方式。
11. **中獎通知 API**：對獎 app 與 API 整合方式。
12. **附錄資料**：營業項目代碼、字軌類別、特種稅額類別之 PayNow 內部編碼。

> 補齊建議：寄信至 **einvoice@paynow.com.tw** 索取「Invoice Management v1.5 技術規格 PDF」，或透過商家後台 → API Reference 區下載最新版 PDF。

---

最後更新：2026/05/07
文件版本：基於 PayNow 公開頁面（docs.paynow.com.tw/developer/docs/invoice/）+ 金流附錄整理；欄位細節需以官方 PDF 為準
