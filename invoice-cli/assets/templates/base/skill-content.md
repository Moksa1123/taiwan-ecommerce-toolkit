
# {{TITLE}}

> {{DESCRIPTION}}

## 快速導覽

### 相關文件
使用此技能時，請參考專案中的 API 規格文件：
- `references/ECPAY_API_REFERENCE.md` - 綠界 API 規格
- `references/SMILEPAY_API_REFERENCE.md` - 速買配 API 規格
- `references/AMEGO_API_REFERENCE.md` - 光貿 API 規格
- `references/EZPAY_API_REFERENCE.md` - ezPay 簡單付 API 規格（藍新金流集團）
- `references/PAYNOW_API_REFERENCE.md` - 立吉富 PayNow API 規格（含 POS 機批次取號流程）
- [EXAMPLES.md](EXAMPLES.md) - 程式碼範例集

### 智能工具
- `scripts/search.py` - BM25 搜索引擎（查詢 API、錯誤碼、欄位映射）
- `scripts/recommend.py` - 加值中心推薦系統
- `scripts/generate-invoice-service.py` - 服務代碼生成器
- `scripts/persist.py` - 持久化配置工具（MASTER.md 生成）
- `data/` - CSV 數據檔（providers, operations, error-codes, field-mappings, tax-rules, troubleshooting, reasoning）

### 何時使用此技能
- 開發電子發票開立功能
- 整合台灣電子發票服務商 API
- 實作 B2C（二聯式）或 B2B（三聯式）發票
- 處理發票列印、作廢、折讓等功能
- 處理加密簽章（AES、MD5）
- 解決發票 API 整合問題

## 智能搜索與推薦

### 搜索引擎 (search.py)

使用 BM25 算法在資料庫中搜索相關資訊：

```bash
# 搜索加值中心
python scripts/search.py "ecpay" --domain provider

# 搜索錯誤碼
python scripts/search.py "10000016" --domain error

# 搜索欄位映射
python scripts/search.py "MerchantID" --domain field

# 搜索稅務規則
python scripts/search.py "B2B 稅額計算" --domain tax

# 搜索疑難排解
python scripts/search.py "列印空白" --domain troubleshoot

# JSON 輸出
python scripts/search.py "折讓" --format json
```

**搜索域：**
| 域 | 說明 | CSV 檔案 |
|-----|------|----------|
| `provider` | 加值中心比較 | providers.csv |
| `operation` | API 操作端點 | operations.csv |
| `error` | 錯誤碼查詢 | error-codes.csv |
| `field` | 欄位映射 | field-mappings.csv |
| `tax` | 稅務計算規則 | tax-rules.csv |
| `troubleshoot` | 疑難排解 | troubleshooting.csv |
| `reasoning` | 推薦決策規則 | reasoning.csv |

### 推薦系統 (recommend.py)

根據需求自動推薦最適合的加值中心：

```bash
# 高交易量電商
python scripts/recommend.py "電商 高交易量 穩定"
# → 推薦 ECPay (市佔率高，穩定性佳)

# 快速整合需求
python scripts/recommend.py "簡單 快速 小型專案"
# → 推薦 SmilePay (整合最簡單)

# API 設計優先
python scripts/recommend.py "API 設計 MIG標準"
# → 推薦 Amego (MIG 4.0 最新標準)

# JSON 輸出
python scripts/recommend.py "穩定 文檔完整" --format json
```

**推薦關鍵字：**
- **ECPay**: 穩定、市佔、文檔、SDK、高交易量、電商
- **SmilePay**: 簡單、快速、小型、測試、無加密、便宜
- **Amego**: API、設計、新、MIG、標準
- **ezPay**: 藍新、簡單付、AES-256、字軌管理、批次開立、與 Newebpay 同集團
- **PayNow**: 立吉富、JWT、金物流發票一站式、POS 批次取號、外帶 POS 機

### 代碼生成器 (generate-invoice-service.py)

自動生成服務商專用代碼：

```bash
# 生成 TypeScript 服務
python scripts/generate-invoice-service.py ECPay --output ts

# 生成 Python 服務
python scripts/generate-invoice-service.py SmilePay --output py

# 輸出到檔案
python scripts/generate-invoice-service.py Amego --output ts > amego-service.ts
```

### 持久化配置 (persist.py)

將發票配置保存為 MASTER.md，供 AI 助手持續參考：

```bash
# 初始化配置
python scripts/persist.py init ECPay
python scripts/persist.py init SmilePay -p "MyProject"

# 顯示當前配置
python scripts/persist.py show

# 列出可用服務商
python scripts/persist.py list

# 強制覆蓋
python scripts/persist.py init Amego --force
```

**生成結構：**
```
invoice-config/
└── MASTER.md       # 專案發票配置
    ├── 基本資訊
    ├── 服務商配置
    ├── API 端點
    ├── 發票類型設定
    ├── 環境變數建議
    └── 開發檢查清單
```

---

## 發票類型

### B2C 二聯式發票
- 買受人無統編
- `BuyerIdentifier` = `0000000000`
- 金額為**含稅價**
- 可使用載具或捐贈
- 示例：一般消費者購物

### B2B 三聯式發票
- 買受人有 8 碼統編
- `BuyerIdentifier` = 實際統編（需驗證格式）
- 金額為**未稅價**，需另計稅額
- **不可**使用載具或捐贈
- 示例：公司採購

## 各服務商特性比較

| 特性 | 綠界 ECPay | 速買配 SmilePay | 光貿 Amego | ezPay 簡單付 | PayNow 立吉富 |
|------|-----------|-----------------|------------|--------------|----------------|
| 測試/正式 URL | 不同 URL | 不同 URL | **相同 URL** | 不同 URL (cinv/inv) | 不同 URL (dev/prod) |
| 認證方式 | AES-128-CBC + HashKey/HashIV | Grvc + Verify_key | MD5 簽章 + App Key | AES-256-CBC + 32 碼 HashKey + 16 碼 HashIV + SHA256 CheckCode | JWT Bearer Token |
| 列印方式 | POST 表單提交 | GET URL 參數 | API 取得 PDF URL | API 觸發補開立 (`Api_invoice_touch`) | （需向 PayNow 索取） |
| B2B 金額欄位 | SalesAmount (未稅) | UnitTAX=N | DetailVat=0 | `Category=B2B` + `Amt`/`TaxAmt` 拆分 | `BuyerIdentifier` + `TaxType` 切換 |
| 傳輸格式 | JSON (AES 加密) | URL Parameters | JSON (URL Encode) | Form Post (`MerchantID_`/`PostData_` 後綴底線) | JSON (Bearer Header) |
| 與其他系統共用加密 | 獨立 | 獨立 | 獨立 | **與藍新 Newebpay 金流共用** | 與 PayNow 金流不同（金流端用動態 AES-256） |
| 文件成熟度 | 高 | 高 | 中 | 中（5 本 PDF） | **低**（公開頁面僅約 70 行，多項 API 須索取 PDF） |

## 開發實作步驟

### 1. 服務實作架構

創建服務時遵循以下結構：

```typescript
// lib/services/invoice-provider.ts - 介面定義
export interface InvoiceService {
    issueInvoice(userId: string, data: InvoiceIssueData): Promise<InvoiceIssueResponse>
    voidInvoice(userId: string, invoiceNumber: string, reason: string): Promise<InvoiceVoidResponse>
    printInvoice(userId: string, invoiceNumber: string): Promise<InvoicePrintResponse>
}

// lib/services/{provider}-invoice-service.ts - 各服務商實作
export class ECPayInvoiceService implements InvoiceService {
    private async encryptData(data: any, hashKey: string, hashIV: string): Promise<string> {
        // AES-128-CBC 加密實作
    }

    async issueInvoice(userId: string, data: InvoiceIssueData) {
        // 1. 取得使用者設定
        // 2. 準備 API 資料
        // 3. 加密簽章
        // 4. 發送請求
        // 5. 解密回應
        // 6. 回傳標準格式
    }
}
```

### 2. 金額計算邏輯

**含稅總額 → 未稅金額 + 稅額：**

```typescript
function calculateInvoiceAmounts(totalAmount: number, isB2B: boolean) {
    if (isB2B) {
        // B2B: 需分拆稅額
        const taxAmount = Math.round(totalAmount - (totalAmount / 1.05))
        const salesAmount = totalAmount - taxAmount
        return { salesAmount, taxAmount, totalAmount }
    } else {
        // B2C: 含稅總額
        return { salesAmount: totalAmount, taxAmount: 0, totalAmount }
    }
}

// 範例
const amounts = calculateInvoiceAmounts(1050, true)
// { salesAmount: 1000, taxAmount: 50, totalAmount: 1050 }
```

### 3. 加密實作

**綠界 (ECPay) - AES 加密：**

```typescript
import crypto from 'crypto'

function encryptECPay(data: object, hashKey: string, hashIV: string): string {
    // 1. JSON 轉字串並 URL Encode
    const jsonString = JSON.stringify(data)
    const urlEncoded = encodeURIComponent(jsonString)

    // 2. AES-128-CBC 加密
    const cipher = crypto.createCipheriv('aes-128-cbc', hashKey, hashIV)
    let encrypted = cipher.update(urlEncoded, 'utf8', 'base64')
    encrypted += cipher.final('base64')

    return encrypted
}

function decryptECPay(encryptedData: string, hashKey: string, hashIV: string): object {
    const decipher = crypto.createDecipheriv('aes-128-cbc', hashKey, hashIV)
    let decrypted = decipher.update(encryptedData, 'base64', 'utf8')
    decrypted += decipher.final('utf8')

    const urlDecoded = decodeURIComponent(decrypted)
    return JSON.parse(urlDecoded)
}
```

**光貿 (Amego) - MD5 簽章：**

```typescript
function generateAmegoSign(data: object, time: number, appKey: string): string {
    const dataString = JSON.stringify(data)
    const signString = dataString + time + appKey
    return crypto.createHash('md5').update(signString).digest('hex')
}
```

### 4. 服務商綁定

**關鍵：開立發票時必須記錄使用的服務商，列印時才能正確調用**

```typescript
// 開立時儲存服務商
await prisma.financialRecord.update({
    where: { id: recordId },
    data: {
        invoiceNo: result.invoiceNumber,
        invoiceProvider: actualProvider,  // 'ECPAY' | 'SMILEPAY' | 'AMEGO'
        invoiceRandomNum: result.randomNumber, // **重要**：列印時需要
        invoiceDate: new Date(),
    }
})

// 列印時使用開立時的服務商
const service = record.invoiceProvider
    ? InvoiceServiceFactory.getService(record.invoiceProvider)
    : await InvoiceServiceFactory.getServiceForUser(userId)
```

### 5. 列印回應處理

前端需根據回應類型處理：

```typescript
// 後端回應格式
interface InvoicePrintResponse {
    success: boolean
    type?: 'html' | 'redirect' | 'form'
    htmlContent?: string      // 綠界
    printUrl?: string          // 速買配/光貿
    formUrl?: string
    formParams?: Record<string, string>
}

// 前端處理範例
if (result.type === 'html') {
    const win = window.open('', '_blank')
    win.document.write(result.htmlContent)
} else if (result.type === 'redirect') {
    window.open(result.url, '_blank')
} else if (result.type === 'form') {
    // 動態建立表單提交
    const form = document.createElement('form')
    form.method = 'POST'
    form.action = result.formUrl
    form.target = '_blank'
    // ... 添加參數
    form.submit()
}
```

## 常見問題排除

### 問題 1: 開立發票失敗，錯誤訊息不明確

**診斷步驟：**
1. 檢查 logger 輸出，查看 `raw` 欄位完整錯誤
2. 確認環境變數（測試/正式）是否正確
3. 驗證必填欄位是否完整

**綠界常見錯誤：**
- `10000006`: RelateNumber 重複 → 訂單編號已使用
- `10000016`: 金額計算錯誤 → 檢查 B2C/B2B 金額計算
- `10000019`: 打統編不可使用載具 → 移除 CarrierType

**速買配常見錯誤：**
- `-10066`: AllAmount 驗算錯誤 → 檢查是否傳入 TotalAmount
- `-10084`: orderid 格式錯誤 → 限制 30 字元
- `-10053`: 載具號碼錯誤 → 驗證手機條碼格式

**光貿常見錯誤：**
- `1002`: OrderId 已存在 → 使用唯一訂單編號
- `1007`: 金額計算錯誤 → 檢查 DetailVat 設定
- `1012`: 打統編發票不可使用載具或捐贈

### 問題 2: 列印時顯示「查詢不到該發票」

**解決方案：**
確認 `invoiceProvider` 欄位有正確儲存，列印時使用開立時的服務商。

```typescript
// 正確：使用發票記錄中的服務商
const service = record.invoiceProvider
    ? InvoiceServiceFactory.getService(record.invoiceProvider)
    : await InvoiceServiceFactory.getServiceForUser(userId)

// 錯誤：使用使用者當前預設服務商
const service = await InvoiceServiceFactory.getServiceForUser(userId)
```

### 問題 3: B2B 發票金額錯誤

**各服務商金額欄位：**

```typescript
// 綠界 ECPay
const b2bData = {
    SalesAmount: 1000,      // 未稅銷售額
    TaxAmount: 50,          // 稅額
    TotalAmount: 1050,      // 總計
    ItemPrice: 100,         // 商品單價（未稅）
    ItemAmount: 1000,       // 商品小計（未稅）
    ItemTax: 50             // 商品稅額
}

// 速買配 SmilePay
const b2bData = {
    AllAmount: '1050',      // 含稅總額
    SalesAmount: '1000',    // 未稅銷售額（選填，但建議填）
    TaxAmount: '50',        // 稅額（選填）
    UnitTAX: 'N',           // **重要**：單價未稅
    UnitPrice: '100',       // 商品單價（未稅）
    Amount: '1000'          // 商品小計（未稅）
}

// 光貿 Amego
const b2bData = {
    DetailVat: 0,           // **重要**：0=未稅
    SalesAmount: 1000,      // 未稅銷售額
    TaxAmount: 50,          // 稅額
    TotalAmount: 1050,      // 總計
    ProductItem: [{
        UnitPrice: 100,     // 商品單價（未稅）
        Amount: 1000        // 商品小計（未稅）
    }]
}
```

### 問題 4: 速買配列印空白

**原因：** 回傳 `method: 'GET'` 時錯誤使用 `type: 'form'`

**解決：**
```typescript
// 正確
if (printData.method === 'GET' && printData.url) {
    return { type: 'redirect', url: printData.url }
}

// 錯誤
return { type: 'form', url: printData.url, params: printData.params }
```

### 問題 5: 時間戳記逾時

**綠界錯誤 10000005：** 時間戳記超過 10 分鐘

**解決：**
```typescript
// 確保使用當前時間戳
const timestamp = Math.floor(Date.now() / 1000)

// 光貿：誤差容許 ±60 秒
const time = Math.floor(Date.now() / 1000)
```

## 測試帳號

### 綠界測試環境
```
MerchantID: 2000132
HashKey: ejCk326UnaZWKisg
HashIV: q9jcZX8Ib9LM8wYk
URL: https://einvoice-stage.ecpay.com.tw
```

### 速買配測試環境
```
Grvc: SEI1000034
Verify_key: 9D73935693EE0237FABA6AB744E48661
測試統編: 80129529
URL: https://ssl.smse.com.tw/api_test/SPEinvoice_Storage.asp
```

### 光貿測試環境
```
統編: 12345678
App Key: sHeq7t8G1wiQvhAuIM27
後台: https://invoice.amego.tw/
測試帳號: test@amego.tw
測試密碼: 12345678
```

### ezPay 簡單付測試環境
```
測試後台: https://cinv.ezpay.com.tw/
申請流程: 自行註冊測試會員 → 取得 MerchantID + HashKey + HashIV
官方範例 HashKey: abcdefghijklmnopqrstuvwxyzabcdef (32 碼)
官方範例 HashIV: 1234567891234567 (16 碼)
正式環境: https://inv.ezpay.com.tw/
```

> **重要**：ezPay HashKey 為 **32 碼**、HashIV **16 碼**（與 ECPay 16/16 不同）。
> ezPay 與藍新 Newebpay 金流共用同一套加密邏輯（TradeInfo / TradeSha 機制），但發票端與金流端的金鑰各自獨立。

### PayNow 立吉富測試環境
```
測試環境 URL: https://invoiceapi-dev.paynow.com.tw/
正式環境 URL: https://invoiceapi-prod.paynow.com.tw/
認證方式: JWT Bearer Token (向 einvoice@paynow.com.tw 申請)
主站: https://gateway.paynow.com.tw/
```

> **注意**：PayNow 公開技術文件較稀疏，多數請求／回應 schema 與錯誤碼需向 PayNow 索取官方 Invoice Management v1.5 PDF 才能取得完整規格。POS 機流程有「未使用發票號碼於次期單數月 5 號自動上傳空白發票」的特殊規則，務必注意。

## 開發檢查清單

使用此清單確保實作完整：

- [ ] 實作 `InvoiceService` 介面
- [ ] 處理 B2C / B2B 金額計算差異
- [ ] 實作加密/簽章機制（AES 或 MD5）
- [ ] 儲存 `invoiceProvider` 欄位
- [ ] 儲存 `invoiceRandomNum`（列印時需要）
- [ ] 處理列印回應類型（html/redirect/form）
- [ ] 實作錯誤處理與 logger
- [ ] 測試環境驗證
- [ ] 處理載具與捐贈互斥邏輯
- [ ] 驗證統編格式（8 碼數字）

## 新增服務商步驟

1. 在 `lib/services/` 建立 `{provider}-invoice-service.ts`
2. 實作 `InvoiceService` 介面的所有方法
3. 在 `InvoiceServiceFactory` 註冊新服務商
4. 在 `prisma/schema.prisma` 的 `InvoiceProvider` enum 新增選項
5. 執行 `prisma migrate` 或 `prisma db push`
6. 更新前端設定頁面（`app/settings/invoice/page.tsx`）
7. 撰寫單元測試

## 參考資料

詳細 API 規格請查看 `references/` 目錄：
- [綠界 ECPay API 規格](./references/ECPAY_API_REFERENCE.md)
- [速買配 SmilePay API 規格](./references/SMILEPAY_API_REFERENCE.md)
- [光貿 Amego API 規格](./references/AMEGO_API_REFERENCE.md)

---

最後更新：2026/01/29
