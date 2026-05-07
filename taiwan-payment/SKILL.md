---
name: taiwan-payment
description: Taiwan Payment API integration specialist for ECPay, NewebPay, PAYUNi, SmilePay, PChomePay, ezPay, PayNow, Shopline Payments, LINE Pay v4, and TapPay payment gateways. Use when developing payment systems, implementing credit card, ATM, CVS, e-wallet, LINE Pay, Apple Pay, Google Pay, or BNPL payments, or working with Taiwan payment gateway APIs. Handles encryption (SHA256, AES-256-CBC, AES-256-GCM, dynamic AES-256, JWT, HMAC-SHA256, Basic Auth → token, Prime token), API requests, and service provider differences.
user-invocable: true
---

# Taiwan Payment Development Skill

> 此技能涵蓋台灣金流 API 整合開發，包含綠界 (ECPay)、藍新 (NewebPay)、統一 (PAYUNi)、速買配 (SmilePay)、拍錢包 (PChomePay)、ezPay 簡單付、立吉富 (PayNow)、SHOPLINE Payments、LINE Pay v4、TapPay 共十家服務商。

## 快速導覽

### 相關文件
使用此技能時，請參考專案中的 API 規格文件：
- `references/ecpay-payment-api.md` - 綠界金流 API 規格
- `references/newebpay-payment-api.md` - 藍新金流 API 規格
- `references/payuni-payment-api.md` - 統一金流 API 規格
- `references/smilepay-payment-api.md` - 速買配 API 規格（PHP plugin 反推）
- `references/pchomepay-payment-api.md` - 拍錢包 API 規格（含 Basic Auth → Token 兩階段認證）
- `references/ezpay-payment-api.md` - ezPay 簡單付 API 規格（與藍新 Newebpay 同集團、同加密）
- `references/paynow-payment-api.md` - 立吉富 API 規格（傳統版 cashflow + 現代版 PaymentIntent 雙 API）
- `references/shopline-payment-api.md` - Shopline Payments API 規格（Redirect + Embedded SDK 雙模式）
- `references/linepay-payment-api.md` - LINE Pay v4 API 規格（HMAC-SHA256 + Preapproved Pay）
- `references/tappay-payment-api.md` - TapPay API 規格（Prime 兩段式 / PCI 隔離 / pay-by-token 重複扣款）
- [EXAMPLES.md](EXAMPLES.md) - 程式碼範例集

### 智能工具
- `scripts/search.py` - BM25 搜索引擎（查詢 API、錯誤碼、欄位映射、付款方式）
- `scripts/recommend.py` - 金流服務商推薦系統
- `scripts/test_payment.py` - 付款測試工具
- `data/` - CSV 數據檔（providers, operations, error-codes, field-mappings, payment-methods, troubleshooting, reasoning）

### 何時使用此技能
- 開發線上金流付款功能
- 整合台灣金流服務商 API
- 實作信用卡、ATM、超商、電子錢包等付款方式
- 處理訂單查詢、退款、定期定額扣款
- 處理加密簽章（SHA256、AES-256-CBC、AES-256-GCM）
- 解決金流 API 整合問題

## 智能搜索與推薦

### 搜索引擎 (search.py)

使用 BM25 算法在資料庫中搜索相關資訊：

```bash
# 搜索服務商
python scripts/search.py "ecpay" --domain provider

# 搜索錯誤碼
python scripts/search.py "10100058" --domain error

# 搜索欄位映射
python scripts/search.py "MerchantTradeNo" --domain field

# 搜索付款方式
python scripts/search.py "信用卡" --domain payment_method

# 搜索疑難排解
python scripts/search.py "CheckMacValue 錯誤" --domain troubleshoot

# 全域搜索
python scripts/search.py "金額計算" --domain all

# JSON 輸出
python scripts/search.py "ATM" --format json
```

**搜索域：**
| 域 | 說明 | CSV 檔案 |
|-----|------|----------|
| `provider` | 服務商比較 | providers.csv |
| `operation` | API 操作端點 | operations.csv |
| `error` | 錯誤碼查詢 | error-codes.csv |
| `field` | 欄位映射 | field-mappings.csv |
| `payment_method` | 付款方式 | payment-methods.csv |
| `troubleshoot` | 疑難排解 | troubleshooting.csv |
| `reasoning` | 推薦決策規則 | reasoning.csv |

**域自動偵測：**
搜索引擎會自動偵測查詢內容並選擇最適合的域：
- 錯誤碼格式（如 "10100058"）→ error
- 服務商名稱（如 "ECPay"）→ provider
- 付款方式（如 "信用卡"、"ATM"）→ payment_method
- API 欄位（如 "MerchantID"）→ field

### 推薦系統 (recommend.py)

根據需求自動推薦最適合的金流服務商：

```bash
# 高交易量電商
python scripts/recommend.py "高交易量 穩定 電商"
# → 推薦 ECPay (市佔率高，穩定性佳)

# 多元支付需求
python scripts/recommend.py "多元支付 LINE Pay Apple Pay"
# → 推薦 NewebPay (支援 13 種付款方式)

# API 設計優先
python scripts/recommend.py "API RESTful JSON"
# → 推薦 PAYUNi (RESTful JSON API)

# JSON 輸出
python scripts/recommend.py "新創公司 快速整合" --format json

# 簡單文字輸出
python scripts/recommend.py "會員制 定期扣款" --format simple
```

**推薦關鍵字：**
- **ECPay**: 穩定、市佔、高交易量、電商、ATM、超商、定期、訂閱、分期、發票、物流
- **NewebPay**: 多元、支付方式、電子錢包、LINE、行動、記憶、會員、跨境
- **PAYUNi**: API、JSON、RESTful、統一、新創、AFTEE、iCash
- **SmilePay**: 速買配、簡單、便宜、台灣老牌、PHP、ibon、FamiPort、聯合信用卡
- **PChomePay**: 拍錢包、PChome、P 幣、Basic Auth、Token、虛擬帳號、超商代碼條碼、物流二合一
- **ezPay**: 簡單付、藍新小型、低門檻、跨境、智冠、支付寶、微信
- **PayNow**: 立吉富、Apple Pay、PaymentIntent、Stripe-like、JWT、票券、mPOS、現代+傳統雙 API
- **Shopline**: SHOPLINE 商店、Redirect、Embedded SDK、街口、中租 BNPL、cents、HMAC-SHA256
- **LINE Pay**: LINE、自動扣款、Preapproved、Capture、Void、跨國、Channel Secret、Nonce
- **TapPay**: PCI 隔離、Prime、自製結帳頁、card_secret、CherryTech、Apple Pay、Google Pay

**反模式警告：**
推薦系統會自動提示不建議的場景：
- ECPay: 無技術資源、極簡需求
- NewebPay: 簡單 API、單一支付
- PAYUNi: 大型專案、完整文檔
- SmilePay: 多元電子錢包、現代 RESTful、跨境
- PChomePay: 不在 PChome 生態系
- ezPay: 大型商家、需要分期、需要完整支付方式
- PayNow: 簡單需求（雙 API 學習成本高）
- Shopline: 不在 SHOPLINE 商店生態
- LINE Pay: 主要客戶不用 LINE
- TapPay: 不想自製結帳頁、無前端能力

### 付款測試工具 (test_payment.py)

快速測試金流服務商連線：

```bash
# 測試 ECPay 連線
python scripts/test_payment.py ecpay

# 測試 NewebPay 連線
python scripts/test_payment.py newebpay

# 測試 PAYUNi 連線
python scripts/test_payment.py payuni

# 測試 SmilePay 連線
python scripts/test_payment.py smilepay

# 測試 PChomePay 連線
python scripts/test_payment.py pchomepay

# 測試 ezPay 連線
python scripts/test_payment.py ezpay

# 測試 PayNow 連線
python scripts/test_payment.py paynow

# 測試所有服務商
python scripts/test_payment.py all
```

---

## 付款方式說明

### 信用卡支付
- **一次付清**: 最常用的付款方式，2-3 天到帳
- **信用卡分期**: 3/6/12/18/24/30 期，需最低金額 1000 元
- **信用卡定期**: 週期扣款，適用訂閱制服務
- **信用卡紅利**: 紅利折抵功能
- **銀聯卡**: 需另外申請，支援中國銀聯
- **美國運通卡**: 需另外申請

### 電子錢包
- **Apple Pay**: 需申請，適合 iOS 用戶
- **Google Pay**: 需申請，適合 Android 用戶
- **Samsung Pay**: 需申請，三星手機專用
- **LINE Pay**: 需申請，LINE 生態系整合
- **玉山 Wallet**: 玉山銀行電子錢包
- **台灣 Pay**: 官方行動支付，最高 49,999 元

### ATM 轉帳
- **網路 ATM**: 即時轉帳，最高 49,999 元，1 天到帳
- **ATM 虛擬帳號**: 產生專屬繳費帳號，1-3 天到帳，最高 49,999 元

### 超商支付
- **超商代碼**: 至四大超商繳費，30-20,000 元，1-3 天到帳
- **超商條碼**: 產生繳費條碼，20-40,000 元，1-3 天到帳

### 其他支付方式
- **TWQR**: 台灣 Pay QR Code 掃碼支付
- **BNPL 無卡分期**: 先買後付，50-300,000 元
- **AFTEE**: PAYUNi 專屬先享後付
- **iCash**: PAYUNi 專屬愛金卡支付
- **簡單付支付寶/微信**: 跨境支付（中國市場）

## 七家服務商特性比較

| 特性 | ECPay | NewebPay | PAYUNi | SmilePay | PChomePay | ezPay | PayNow |
|------|-------|----------|--------|----------|-----------|-------|--------|
| 加密方式 | SHA256 | AES-256-CBC + SHA256 | AES-256-GCM + SHA256 | Verify_key + Mid_smilepay 加權 | HTTP Basic Auth → pcpay-token | 同 NewebPay (AES-256-CBC + SHA256) | 傳統: 動態 AES-256 (GP/GK 鑰); 現代: JWT Bearer |
| API 風格 | Form POST | Form POST + AES | RESTful JSON | Form POST (回 XML) | RESTful JSON | Form POST + AES (相容 NewebPay) | 傳統: Form POST; 現代: RESTful JSON |
| 測試/正式 URL | 不同 URL | 不同 URL | 不同 URL | 同 URL | 不同 URL | 不同 URL | 不同 URL |
| 市佔率 | 最高 | 高 | 中等 | 中（老牌） | 中（PChome 生態） | 中（小型商家） | 中小（多角化） |
| 支付方式 | 11 種 | 13 種 | 8 種 | 7 種（無多數行動支付） | 5 種（信用卡 + ATM + CVS + 拍錢包 + 取貨付款） | 同 NewebPay 但部分受限 | 傳統 7 種 / 現代 8 種（含 LINE Pay 線上+線下、Apple Pay 含延遲扣款） |
| 特色 | 金流發票物流三合一 | MPG 整合、信用卡記憶 | RESTful、AFTEE、iCash | 簡單便宜、ibon、FamiPort | P 幣回饋、超商取貨付款、自帶物流 | 小型商家門檻低、跨境 | 雙 API、Stripe-like 現代設計、Apple Pay 完整、票券系統 |
| 適用 | 高交易量電商 | 多元支付會員制 | 新創、Node.js | 預算有限、傳統 | PChome 生態 / 物流整合 | 個人賣家、月結金額不大 | 新創、Apple Pay、未來導向 |

### ECPay 特性
- **優勢**: 市佔率最高、穩定性最佳、文檔完整、社群資源豐富、測試帳號可用
- **加密**: URL Encode + SHA256（參數排序 + HashKey + HashIV）
- **傳輸**: Form POST，application/x-www-form-urlencoded
- **特色**: 同時支援金流、發票、物流三合一服務

### NewebPay 特性
- **優勢**: 支援最多支付方式（13 種）、MPG 整合、信用卡記憶功能、完整電子錢包
- **加密**: AES-256-CBC 加密 TradeInfo，再計算 SHA256 TradeSha
- **傳輸**: Form POST，雙層加密（AES + SHA256）
- **特色**: LINE Pay、Apple Pay、Google Pay 原生支援

### PAYUNi 特性
- **優勢**: RESTful JSON API、統一集團背景、AES-GCM 現代加密
- **加密**: AES-256-GCM 加密 + SHA256 簽章
- **傳輸**: RESTful JSON，application/json
- **特色**: AFTEE 先享後付、iCash 愛金卡（獨家）

### SmilePay 特性
- **優勢**: 老牌穩定、整合簡單、無 AES 加密門檻、ibon / FamiPort 直接打單
- **認證**: `Dcvc` + `Verify_key` 共享密鑰；通知時用反推的 `Mid_smilepay` 加權檢核碼驗證
- **傳輸**: Form POST，回 XML（部分欄位 BIG-5 編碼）
- **特色**: 七種付款方式（ATM / Barcode / ibon / FamiPort / 信用卡含分期 / 聯合信用卡 / Union），公開文件需向官方索取

### PChomePay 特性
- **優勢**: PChome 生態整合、拍錢包 5% P 幣回饋、金物流二合一、文件公開完整
- **認證**: HTTP Basic Auth 取得 `pcpay-token`（8 小時有效），後續 API 帶 `pcpay-token` header
- **傳輸**: RESTful JSON
- **特色**: 自帶 7-Eleven 取貨付款物流，notify IP 為 `113.196.231.190`（白名單必加）；測試環境用「金額尾數」觸發各種訂單情境

### ezPay 特性
- **優勢**: 藍新金流小型商家品牌、上手門檻低、與 NewebPay MPG 完全相容
- **加密**: 與 NewebPay 完全相同（AES-256-CBC + SHA256，TradeInfo / TradeSha）
- **傳輸**: 與 NewebPay 完全相同（Form POST + AES）
- **特色**: 同集團共用底層；MerchantID 與 HashKey 為 ezPay 獨立簽發；分期與部分電子錢包受限。**新串接通常直接走 NewebPay**，ezPay 只用於符合小型商家門檻的場景

### PayNow 特性
- **優勢**: 雙 API 並行（傳統 + 現代）、現代版 PaymentIntent 設計接近 Stripe、Apple Pay 完整支援（含延遲扣款）、自帶票券系統
- **加密**:
  - **傳統版（cashflow）**: 動態 AES-256（每次以 GP/GK 檢核碼即時取得 Key/IV）+ 自訂 10 位 TimeStr + Bootstrap key `paynowencryptpaynowcomtw28229955` + SHA-1 PassCode
  - **現代版（apidoc）**: JWT Bearer Token + RESTful JSON
- **傳輸**: 傳統用 Form POST；現代用 application/json
- **特色**: 13 種付款方式（含 LINE Pay 線上線下、Apple Pay v1/v2、Apple Pay Deferred 延遲扣款）、Customer / Card Token 會員記憶、`webhookUrl` 推送回呼。**新專案應優先採用現代版 PaymentIntent**

### Shopline Payments 特性
- **優勢**: SHOPLINE 集團官方金流、RESTful JSON 設計、Redirect + Embedded SDK 雙模式
- **認證**: HTTP Header 帶 `merchantId` + `apiKey`；Webhook 用 HMAC-SHA256
- **傳輸**: application/json，金額以**分**為單位 (1 TWD = 100)，僅支援 TWD
- **特色**: Embedded SDK 適合自訂 UI 與 PCI 隔離；Redirect 模式快速上線；6 種主流支付（信用卡/Apple Pay/LINE Pay/街口/ATM/中租 BNPL）

### LINE Pay 特性
- **優勢**: LINE 生態系直連、跨國（TW/JP/TH/TW）、自動扣款（Preapproved Pay）、Capture/Void 雙階段授權
- **認證**: Channel ID + Channel Secret；每次請求需產生 Nonce 並用 HMAC-SHA256 簽章 (`X-LINE-Authorization`)
- **傳輸**: RESTful JSON v4 規格
- **特色**: Request → Confirm 兩段式流程；Capture 可手動請款（autoCapture=false）；19 位 transactionId（JS 需用字串避免精度遺失）；不支援 Apple Pay / Google Pay（這是 LINE Pay 自身就是支付工具）

### TapPay 特性
- **優勢**: PCI 隔離設計（前端 SDK 取 Prime → 後端付款）、支援多元電子錢包（Apple Pay / Google Pay / LINE Pay / 街口）、適合自製結帳頁
- **認證**: Partner Key（後端）+ App Key（前端）+ Merchant ID 三段式金鑰；Prime 60 秒過期
- **傳輸**: RESTful JSON
- **特色**: 兩段式架構 (Prime → pay-by-prime)；`card_secret` 機制可記憶卡片做重複扣款 (pay-by-token)；`result_url` 雙網址回調；無自家結帳頁，UI 完全在商家自管

## 開發實作步驟

### 1. 服務實作架構

創建服務時遵循以下結構：

```typescript
// lib/services/payment-provider.ts - 介面定義
export interface PaymentService {
    createOrder(userId: string, data: PaymentOrderData): Promise<PaymentOrderResponse>
    queryOrder(userId: string, merchantTradeNo: string): Promise<PaymentQueryResponse>
    refundOrder(userId: string, tradeNo: string, amount: number): Promise<PaymentRefundResponse>
    createPeriodic(userId: string, data: PeriodicPaymentData): Promise<PeriodicResponse>
}

// lib/services/{provider}-payment-service.ts - 各服務商實作
export class ECPayPaymentService implements PaymentService {
    private generateCheckMacValue(params: Record<string, any>, hashKey: string, hashIV: string): string {
        // SHA256 簽章實作
    }

    async createOrder(userId: string, data: PaymentOrderData) {
        // 1. 取得使用者設定
        // 2. 準備 API 資料
        // 3. 計算 CheckMacValue
        // 4. 生成表單 HTML
        // 5. 回傳標準格式
    }
}
```

### 2. 加密實作

**綠界 (ECPay) - SHA256 簽章：**

```typescript
import crypto from 'crypto'

function generateECPayCheckMacValue(params: Record<string, any>, hashKey: string, hashIV: string): string {
    // 1. 移除 CheckMacValue 本身
    const { CheckMacValue, ...cleanParams } = params

    // 2. 依照 key 排序（字母順序）
    const sortedKeys = Object.keys(cleanParams).sort()

    // 3. 組合參數字串: key1=value1&key2=value2
    const paramString = sortedKeys
        .map(key => `${key}=${cleanParams[key]}`)
        .join('&')

    // 4. 前後加上 HashKey 和 HashIV
    const rawString = `HashKey=${hashKey}&${paramString}&HashIV=${hashIV}`

    // 5. URL Encode (lowercase)
    const encoded = encodeURIComponent(rawString).toLowerCase()

    // 6. SHA256 雜湊
    const hash = crypto.createHash('sha256').update(encoded).digest('hex')

    // 7. 轉大寫
    return hash.toUpperCase()
}
```

**藍新 (NewebPay) - AES-256-CBC 雙層加密：**

```typescript
function encryptNewebPay(data: Record<string, any>, hashKey: string, hashIV: string): {
    TradeInfo: string,
    TradeSha: string
} {
    // 1. 轉換為查詢字串
    const queryString = new URLSearchParams(data).toString()

    // 2. AES-256-CBC 加密
    const cipher = crypto.createCipheriv('aes-256-cbc', hashKey, hashIV)
    cipher.setAutoPadding(true)
    let encrypted = cipher.update(queryString, 'utf8', 'hex')
    encrypted += cipher.final('hex')

    // 3. 計算 SHA256
    const tradeSha = crypto
        .createHash('sha256')
        .update(`HashKey=${hashKey}&${encrypted}&HashIV=${hashIV}`)
        .digest('hex')
        .toUpperCase()

    return {
        TradeInfo: encrypted,
        TradeSha: tradeSha
    }
}

function decryptNewebPay(encryptedData: string, hashKey: string, hashIV: string): Record<string, any> {
    const decipher = crypto.createDecipheriv('aes-256-cbc', hashKey, hashIV)
    decipher.setAutoPadding(true)
    let decrypted = decipher.update(encryptedData, 'hex', 'utf8')
    decrypted += decipher.final('utf8')

    return Object.fromEntries(new URLSearchParams(decrypted))
}
```

**統一 (PAYUNi) - AES-256-GCM 加密：**

```typescript
function encryptPAYUNi(data: Record<string, any>, hashKey: string, hashIV: string): {
    EncryptInfo: string,
    HashInfo: string
} {
    // 1. JSON 字串化
    const jsonString = JSON.stringify(data)

    // 2. AES-256-GCM 加密
    const cipher = crypto.createCipheriv('aes-256-gcm', hashKey, hashIV)
    let encrypted = cipher.update(jsonString, 'utf8', 'hex')
    encrypted += cipher.final('hex')

    // 3. 取得 Auth Tag (16 bytes)
    const authTag = cipher.getAuthTag().toString('hex')

    // 4. 組合加密資料 (encrypted + tag)
    const encryptInfo = encrypted + authTag

    // 5. SHA256 簽章
    const hashInfo = crypto
        .createHash('sha256')
        .update(`HashKey=${hashKey}&${encryptInfo}&HashIV=${hashIV}`)
        .digest('hex')
        .toUpperCase()

    return {
        EncryptInfo: encryptInfo,
        HashInfo: hashInfo
    }
}

function decryptPAYUNi(encryptedData: string, hashKey: string, hashIV: string): Record<string, any> {
    // 1. 分離加密內容和 Auth Tag (最後 32 個字元 = 16 bytes hex)
    const encryptedContent = encryptedData.slice(0, -32)
    const authTag = Buffer.from(encryptedData.slice(-32), 'hex')

    // 2. AES-256-GCM 解密
    const decipher = crypto.createDecipheriv('aes-256-gcm', hashKey, hashIV)
    decipher.setAuthTag(authTag)
    let decrypted = decipher.update(encryptedContent, 'hex', 'utf8')
    decrypted += decipher.final('utf8')

    return JSON.parse(decrypted)
}
```

### 3. 訂單建立流程

**關鍵：各服務商都使用 Form POST 導向付款頁**

```typescript
// 後端產生付款表單
async function createPaymentOrder(provider: string, orderData: OrderData) {
    const service = PaymentServiceFactory.getService(provider)
    const result = await service.createOrder(userId, orderData)

    // 儲存訂單資訊
    await prisma.order.update({
        where: { id: orderId },
        data: {
            merchantTradeNo: result.merchantTradeNo,
            paymentProvider: provider,  // **重要**：儲存使用的服務商
            paymentMethod: orderData.paymentMethod,
            status: 'PENDING'
        }
    })

    // 回傳表單資料
    return {
        type: 'form',
        action: result.formAction,
        method: result.formMethod,
        params: result.formParams
    }
}

// 前端提交表單
function submitPaymentForm(formData: PaymentFormData) {
    const form = document.createElement('form')
    form.method = formData.method
    form.action = formData.action
    form.target = '_self'  // 整頁跳轉

    // 添加隱藏欄位
    Object.entries(formData.params).forEach(([key, value]) => {
        const input = document.createElement('input')
        input.type = 'hidden'
        input.name = key
        input.value = value
        form.appendChild(input)
    })

    document.body.appendChild(form)
    form.submit()
}
```

### 4. 付款通知處理

**ReturnURL 處理（付款完成後）：**

```typescript
// app/api/payment/callback/route.ts
export async function POST(request: Request) {
    const formData = await request.formData()
    const params = Object.fromEntries(formData)

    // 1. 偵測服務商（根據欄位判斷）
    const provider = detectProvider(params)
    const service = PaymentServiceFactory.getService(provider)

    // 2. 驗證簽章
    const isValid = service.verifyCallback(params)
    if (!isValid) {
        return new Response('0|CheckMacValue Error', { status: 400 })
    }

    // 3. 更新訂單狀態
    const merchantTradeNo = params.MerchantTradeNo || params.MerchantOrderNo
    await prisma.order.update({
        where: { merchantTradeNo },
        data: {
            status: params.RtnCode === '1' ? 'PAID' : 'FAILED',
            paidAt: new Date(),
            tradeNo: params.TradeNo,  // **重要**：儲存金流商訂單號（退款時需要）
            paymentDetails: params
        }
    })

    // 4. 回應固定格式
    return new Response('1|OK')  // ECPay/NewebPay 要求
}
```

### 5. 查詢訂單

```typescript
async function queryPaymentOrder(merchantTradeNo: string) {
    // 1. 查詢訂單取得服務商
    const order = await prisma.order.findUnique({
        where: { merchantTradeNo }
    })

    // 2. 使用訂單記錄的服務商查詢
    const service = PaymentServiceFactory.getService(order.paymentProvider)
    const result = await service.queryOrder(order.userId, merchantTradeNo)

    return result
}
```

### 6. 退款處理

```typescript
async function refundPaymentOrder(merchantTradeNo: string, refundAmount: number) {
    const order = await prisma.order.findUnique({
        where: { merchantTradeNo }
    })

    // **重要**：使用開立時的服務商和 TradeNo
    const service = PaymentServiceFactory.getService(order.paymentProvider)
    const result = await service.refundOrder(
        order.userId,
        order.tradeNo,  // 金流商訂單號
        refundAmount
    )

    // 更新訂單狀態
    await prisma.order.update({
        where: { merchantTradeNo },
        data: {
            status: 'REFUNDED',
            refundAmount,
            refundedAt: new Date()
        }
    })

    return result
}
```

## 常見問題排除

### 問題 1: CheckMacValue 驗證失敗

**錯誤訊息：** ECPay 回傳 `10100058`，NewebPay 回傳 `CheckValue Error`

**常見原因：**
1. 參數排序錯誤（必須按照字母順序）
2. URL Encode 不正確（ECPay 需要 lowercase）
3. 編碼問題（UTF-8）
4. 忘記移除 CheckMacValue 本身

**解決方案：**
```typescript
// * 正確
function generateCheckMacValue(params: Record<string, any>, hashKey: string, hashIV: string) {
    // 1. 移除 CheckMacValue
    const { CheckMacValue, ...cleanParams } = params

    // 2. 排序
    const sortedKeys = Object.keys(cleanParams).sort()

    // 3. 組合字串
    const paramString = sortedKeys.map(k => `${k}=${cleanParams[k]}`).join('&')

    // 4. 加上 HashKey/HashIV
    const rawString = `HashKey=${hashKey}&${paramString}&HashIV=${hashIV}`

    // 5. URL Encode (lowercase for ECPay)
    const encoded = encodeURIComponent(rawString).toLowerCase()

    // 6. SHA256
    return crypto.createHash('sha256').update(encoded).digest('hex').toUpperCase()
}

// * 錯誤：未排序
const paramString = Object.entries(params).map(([k, v]) => `${k}=${v}`).join('&')

// * 錯誤：URL Encode 使用 uppercase
const encoded = encodeURIComponent(rawString)  // 應該用 toLowerCase()
```

### 問題 2: 訂單編號重複

**錯誤訊息：** ECPay `10100003`，NewebPay/PAYUNi 訂單已存在

**原因：** 使用相同的 MerchantTradeNo

**解決方案：**
```typescript
// * 建議：加入時間戳保證唯一性
function generateMerchantTradeNo(prefix: string = 'ORD') {
    const timestamp = Date.now()
    const random = Math.random().toString(36).substring(2, 8).toUpperCase()
    return `${prefix}${timestamp}${random}`.substring(0, 20)  // ECPay 限制 20 字元
}

// 範例輸出: ORD1706512345A7B2
```

### 問題 3: 金額計算錯誤

**錯誤訊息：** 回傳金額驗算錯誤

**常見原因：**
1. 金額包含小數
2. 金額為負數或 0
3. 商品金額總和不等於訂單金額

**解決方案：**
```typescript
// * 確保金額為正整數
function validateAmount(amount: number): number {
    if (amount <= 0) {
        throw new Error('金額必須大於 0')
    }
    return Math.round(amount)  // 移除小數
}

// * 驗證商品金額總和
function validateItemsAmount(items: Item[], totalAmount: number) {
    const itemsSum = items.reduce((sum, item) => sum + (item.price * item.quantity), 0)
    if (Math.round(itemsSum) !== Math.round(totalAmount)) {
        throw new Error(`商品金額總和 ${itemsSum} 不等於訂單金額 ${totalAmount}`)
    }
}
```

### 問題 4: 收不到付款通知

**原因：**
1. ReturnURL 不是 HTTPS
2. 防火牆阻擋
3. 回應格式錯誤

**解決方案：**
```typescript
// * 確認 ReturnURL 使用 HTTPS
const returnURL = 'https://yourdomain.com/api/payment/callback'  // 必須 HTTPS

// * 正確回應格式
export async function POST(request: Request) {
    // ... 處理邏輯

    // ECPay/NewebPay 需要回應 "1|OK"
    return new Response('1|OK', {
        status: 200,
        headers: { 'Content-Type': 'text/plain' }
    })
}

// * 錯誤：JSON 回應
return Response.json({ success: true })  // 不正確
```

### 問題 5: 測試卡無法付款

**原因：** 使用真實卡號或測試卡格式錯誤

**解決方案：**
```
# ECPay 測試卡
卡號: 4311-9522-2222-2222
有效期: 任意未來月年
CVV: 任意 3 碼

# NewebPay 測試卡
卡號: 4000-2211-1111-1111
有效期: 任意未來月年
CVV: 任意 3 碼

# PAYUNi 測試卡
請至後台查詢官方測試卡號
```

### 問題 6: AES 加密失敗

**NewebPay AES-256-CBC 加密錯誤：**

```typescript
// * 確認 Key/IV 長度
const hashKey = 'your32BytesHashKeyHere123456'  // 必須 32 bytes
const hashIV = 'your16BytesIV123'              // 必須 16 bytes

// * 使用正確的 padding
const cipher = crypto.createCipheriv('aes-256-cbc', hashKey, hashIV)
cipher.setAutoPadding(true)  // PKCS7 padding
```

**PAYUNi AES-256-GCM 加密錯誤：**

```typescript
// * 記得附加 Auth Tag
const cipher = crypto.createCipheriv('aes-256-gcm', hashKey, hashIV)
let encrypted = cipher.update(jsonString, 'utf8', 'hex')
encrypted += cipher.final('hex')
const authTag = cipher.getAuthTag().toString('hex')  // **重要**
const encryptInfo = encrypted + authTag  // 總長度 = encrypted + 32 chars (16 bytes hex)
```

### 問題 7: ATM 虛擬帳號未產生

**原因：**
1. 未設定 ChoosePayment=ATM
2. ExpireDate 格式錯誤
3. ExpireDate 超過範圍（3-60 天）

**解決方案：**
```typescript
// * ECPay ATM 設定
const params = {
    ChoosePayment: 'ATM',
    ExpireDate: 3,  // 3-60 天
    PaymentInfoURL: 'https://yourdomain.com/api/payment/atm-info',  // 接收帳號通知
    // ...
}

// * NewebPay ATM 設定
const params = {
    VACC: 1,  // 啟用 ATM
    ExpireDate: '2024-12-31',  // yyyy-MM-dd 格式
    // ...
}
```

### 問題 8: 定期定額建立失敗

**原因：** 週期參數不完整

**解決方案：**
```typescript
// * ECPay 定期定額
const periodicParams = {
    PeriodAmount: 1000,      // 扣款金額
    PeriodType: 'M',         // D=日, M=月, Y=年
    Frequency: 1,            // 頻率（每 1 個週期）
    ExecTimes: 12,           // 執行次數（12 次）
    PeriodReturnURL: 'https://yourdomain.com/api/payment/periodic-callback',
    // ...
}

// * NewebPay 定期定額
const periodicParams = {
    PeriodAmt: 1000,
    PeriodType: 'M',
    PeriodPoint: '01',       // 每月 1 號扣款
    PeriodTimes: 12,
    // ...
}
```

### 問題 9: 跨域問題

**錯誤：** 前端導向付款頁失敗

**原因：** 使用 AJAX 或 Fetch，受 CORS 限制

**解決方案：**
```typescript
// * 錯誤：使用 AJAX
fetch(paymentUrl, { method: 'POST', body: formData })  // 會被 CORS 阻擋

// * 正確：使用 Form POST 整頁跳轉
function submitPaymentForm(action: string, params: Record<string, string>) {
    const form = document.createElement('form')
    form.method = 'POST'
    form.action = action
    form.target = '_self'  // 整頁跳轉

    Object.entries(params).forEach(([key, value]) => {
        const input = document.createElement('input')
        input.type = 'hidden'
        input.name = key
        input.value = value
        form.appendChild(input)
    })

    document.body.appendChild(form)
    form.submit()  // 直接提交
}
```

### 問題 10: 商店代號錯誤

**錯誤訊息：** 回傳商店不存在

**原因：**
1. MerchantID 錯誤
2. 測試/正式環境混用

**解決方案：**
```typescript
// * 使用環境變數區分
const config = {
    merchantID: process.env.NODE_ENV === 'production'
        ? process.env.ECPAY_MERCHANT_ID_PROD
        : process.env.ECPAY_MERCHANT_ID_TEST,
    apiUrl: process.env.NODE_ENV === 'production'
        ? 'https://payment.ecpay.com.tw/Cashier/AioCheckOut/V5'
        : 'https://payment-stage.ecpay.com.tw/Cashier/AioCheckOut/V5'
}
```

## 測試帳號

### 綠界測試環境
```
MerchantID: 3002607
HashKey: pwFHCqoQZGmho4w6
HashIV: EkRm7iFT261dpevs
測試 URL: https://payment-stage.ecpay.com.tw/Cashier/AioCheckOut/V5
測試卡號: 4311-9522-2222-2222
後台: https://vendor-stage.ecpay.com.tw/
```

### 藍新測試環境
```
MerchantID: 請至後台申請
HashKey: 請至後台申請（32 bytes）
HashIV: 請至後台申請（16 bytes）
測試 URL: https://ccore.newebpay.com/MPG/mpg_gateway
測試卡號: 4000-2211-1111-1111
後台: https://cwww.newebpay.com/
```

### 統一測試環境
```
MerchantID: 請至後台申請
HashKey: 請至後台申請
HashIV: 請至後台申請
測試 URL: https://sandbox-api.payuni.com.tw/api/upp
後台: https://sandbox.payuni.com.tw/
```

## 開發檢查清單

使用此清單確保實作完整：

### 基礎設定
- [ ] 實作 `PaymentService` 介面
- [ ] 實作各服務商加密機制（SHA256 / AES-CBC / AES-GCM）
- [ ] 設定環境變數（測試/正式）
- [ ] 配置 ReturnURL（HTTPS）
- [ ] 配置 OrderResultURL（付款完成導向頁）

### 訂單處理
- [ ] 儲存 `paymentProvider` 欄位（查詢/退款時需要）
- [ ] 儲存 `merchantTradeNo`（唯一訂單編號）
- [ ] 儲存 `tradeNo`（金流商訂單號，退款時需要）
- [ ] 金額驗證（正整數、最小金額）
- [ ] 商品金額總和驗證

### 付款方式
- [ ] 支援信用卡一次付清
- [ ] 支援 ATM 虛擬帳號（可選）
- [ ] 支援超商代碼/條碼（可選）
- [ ] 支援電子錢包（可選）
- [ ] 支援信用卡分期（可選）
- [ ] 支援定期定額（可選）

### 回呼處理
- [ ] 驗證 CheckMacValue / TradeSha / HashInfo
- [ ] 更新訂單狀態
- [ ] 回應 "1|OK" 格式
- [ ] 防止重複通知處理（冪等性）

### 查詢退款
- [ ] 實作訂單查詢 API
- [ ] 實作退款 API
- [ ] 處理部分退款邏輯
- [ ] 檢查退款期限

### 錯誤處理
- [ ] 實作錯誤處理與 logger
- [ ] 記錄完整請求/回應（除敏感資訊）
- [ ] 處理加密錯誤
- [ ] 處理網路逾時

### 測試驗證
- [ ] 測試環境驗證
- [ ] 使用官方測試卡測試
- [ ] 測試付款通知接收
- [ ] 測試查詢功能
- [ ] 測試退款功能

## 新增服務商步驟

1. 在 `lib/services/` 建立 `{provider}-payment-service.ts`
2. 實作 `PaymentService` 介面的所有方法
3. 在 `PaymentServiceFactory` 註冊新服務商
4. 在 `prisma/schema.prisma` 的 `PaymentProvider` enum 新增選項
5. 執行 `prisma migrate` 或 `prisma db push`
6. 更新前端設定頁面
7. 撰寫單元測試
8. 更新文檔

## 參考資料

詳細 API 規格請查看 `references/` 目錄：
- [綠界 ECPay Payment API 規格](./references/ECPAY_PAYMENT_REFERENCE.md)
- [藍新 NewebPay Payment API 規格](./references/NEWEBPAY_PAYMENT_REFERENCE.md)
- [統一 PAYUNi Payment API 規格](./references/PAYUNI_PAYMENT_REFERENCE.md)

官方文檔：
- ECPay: https://developers.ecpay.com.tw/
- NewebPay: https://www.newebpay.com/website/Page/content/download_api
- PAYUNi: https://www.payuni.com.tw/docs/

---

最後更新：2026/01/29
