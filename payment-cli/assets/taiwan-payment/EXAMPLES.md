# 台灣金流 Skill - 完整範例集

這份文件包含使用 `taiwan-payment` skill 的完整實作範例。

## 目錄

1. [基礎範例](#基礎範例)
2. [進階範例](#進階範例)
3. [實戰場景](#實戰場景)
4. [常見錯誤與修正](#常見錯誤與修正)

---

## 基礎範例

### 範例 1: ECPay 信用卡一次付清

**場景：** 客戶購買商品，金額 1050 元，使用綠界信用卡付款

**Claude 提示詞：**
```
使用 ECPay 測試環境建立信用卡付款
- 訂單金額: 1050 元
- 付款方式: 信用卡一次付清
- 商品名稱: 測試商品
```

**生成的程式碼：**

```typescript
import { ECPayPaymentService } from '@/lib/services/ecpay-payment-service'
import crypto from 'crypto'

async function createECPayOrder() {
    const service = new ECPayPaymentService(false) // 測試環境

    // 產生唯一訂單編號
    const merchantTradeNo = `ORD${Date.now()}${Math.random().toString(36).substring(2, 8).toUpperCase()}`

    const orderData = {
        MerchantTradeNo: merchantTradeNo,
        MerchantTradeDate: new Date().toLocaleString('zh-TW', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        }).replace(/\//g, '/'),
        TotalAmount: 1050,
        TradeDesc: '測試商品購買',
        ItemName: '測試商品 x1',
        ReturnURL: 'https://yourdomain.com/api/payment/callback',
        ChoosePayment: 'Credit',
        EncryptType: 1,
    }

    try {
        const result = await service.createOrder('user-123', orderData)

        if (result.success) {
            console.log('[OK] 訂單建立成功')
            console.log('訂單編號:', result.merchantTradeNo)
            console.log('請導向付款頁:', result.formAction)

            // 儲存訂單
            await prisma.order.create({
                data: {
                    userId: 'user-123',
                    merchantTradeNo: result.merchantTradeNo,
                    amount: 1050,
                    status: 'PENDING',
                    paymentProvider: 'ECPAY',
                    paymentMethod: 'Credit',
                }
            })

            return result
        } else {
            console.error('[ERROR] 建立失敗:', result.msg)
        }
    } catch (error) {
        console.error('付款建立異常:', error)
        throw error
    }
}

// 前端提交表單
function submitToECPay(formData: { action: string, params: Record<string, string> }) {
    const form = document.createElement('form')
    form.method = 'POST'
    form.action = formData.action
    form.target = '_self'

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

**預期輸出：**
```
[OK] 訂單建立成功
訂單編號: ORD1738123456ABC7
請導向付款頁: https://payment-stage.ecpay.com.tw/Cashier/AioCheckOut/V5
```

---

### 範例 2: NewebPay MPG 整合支付

**場景：** 使用藍新金流整合支付頁，支援信用卡、ATM、超商代碼

**Claude 提示詞：**
```
使用 NewebPay MPG 建立整合付款
- 金額: 2500 元
- 付款方式: 信用卡、ATM、超商代碼
- 使用 AES 加密
```

**生成的程式碼：**

```typescript
import crypto from 'crypto'

class NewebPayService {
    private merchantID: string
    private hashKey: string
    private hashIV: string
    private apiUrl: string

    constructor(isProd: boolean = false) {
        this.merchantID = isProd
            ? process.env.NEWEBPAY_MERCHANT_ID_PROD!
            : process.env.NEWEBPAY_MERCHANT_ID_TEST!
        this.hashKey = isProd
            ? process.env.NEWEBPAY_HASH_KEY_PROD!
            : process.env.NEWEBPAY_HASH_KEY_TEST!
        this.hashIV = isProd
            ? process.env.NEWEBPAY_HASH_IV_PROD!
            : process.env.NEWEBPAY_HASH_IV_TEST!
        this.apiUrl = isProd
            ? 'https://core.newebpay.com/MPG/mpg_gateway'
            : 'https://ccore.newebpay.com/MPG/mpg_gateway'
    }

    private encrypt(data: Record<string, any>): { TradeInfo: string, TradeSha: string } {
        // 1. 轉換為查詢字串
        const queryString = new URLSearchParams(data).toString()

        // 2. AES-256-CBC 加密
        const cipher = crypto.createCipheriv('aes-256-cbc', this.hashKey, this.hashIV)
        cipher.setAutoPadding(true)
        let encrypted = cipher.update(queryString, 'utf8', 'hex')
        encrypted += cipher.final('hex')

        // 3. 計算 SHA256
        const tradeSha = crypto
            .createHash('sha256')
            .update(`HashKey=${this.hashKey}&${encrypted}&HashIV=${this.hashIV}`)
            .digest('hex')
            .toUpperCase()

        return {
            TradeInfo: encrypted,
            TradeSha: tradeSha
        }
    }

    async createMPGOrder(userId: string, orderData: any) {
        const merchantOrderNo = `MPG${Date.now()}`

        const tradeInfo = {
            MerchantID: this.merchantID,
            RespondType: 'JSON',
            TimeStamp: Math.floor(Date.now() / 1000).toString(),
            Version: '2.0',
            MerchantOrderNo: merchantOrderNo,
            Amt: orderData.amount,
            ItemDesc: orderData.itemDesc || '商品購買',
            ReturnURL: orderData.returnURL,
            NotifyURL: orderData.notifyURL,
            Email: orderData.email,
            // 啟用付款方式
            CREDIT: 1,      // 信用卡
            VACC: 1,        // ATM
            CVS: 1,         // 超商代碼
        }

        // 加密
        const { TradeInfo, TradeSha } = this.encrypt(tradeInfo)

        console.log('[OK] NewebPay MPG 訂單建立')
        console.log('訂單編號:', merchantOrderNo)
        console.log('加密 TradeInfo 長度:', TradeInfo.length)

        return {
            success: true,
            formAction: this.apiUrl,
            formMethod: 'POST',
            formParams: {
                MerchantID: this.merchantID,
                TradeInfo: TradeInfo,
                TradeSha: TradeSha,
                Version: '2.0'
            }
        }
    }
}

// 使用範例
async function createNewebPayMPG() {
    const service = new NewebPayService(false) // 測試環境

    const result = await service.createMPGOrder('user-123', {
        amount: 2500,
        itemDesc: '網站年費方案',
        returnURL: 'https://yourdomain.com/payment/return',
        notifyURL: 'https://yourdomain.com/api/payment/callback',
        email: 'test@example.com'
    })

    return result
}
```

**重要說明：**
- NewebPay 使用 AES-256-CBC 雙層加密（TradeInfo + TradeSha）
- HashKey 必須 32 bytes，HashIV 必須 16 bytes
- MPG 整合支付頁會根據啟用的付款方式顯示選項

**預期輸出：**
```
[OK] NewebPay MPG 訂單建立
訂單編號: MPG1738123456789
加密 TradeInfo 長度: 384
```

---

### 範例 3: PAYUNi RESTful API

**場景：** 使用統一金流 RESTful JSON API 建立付款

**Claude 提示詞：**
```
使用 PAYUNi RESTful API 建立信用卡付款
- 金額: 3000 元
- JSON 格式
- AES-256-GCM 加密
```

**生成的程式碼：**

```typescript
import crypto from 'crypto'
import axios from 'axios'

class PAYUNiService {
    private merchantID: string
    private hashKey: string
    private hashIV: string
    private apiUrl: string

    constructor(isProd: boolean = false) {
        this.merchantID = isProd
            ? process.env.PAYUNI_MERCHANT_ID_PROD!
            : process.env.PAYUNI_MERCHANT_ID_TEST!
        this.hashKey = isProd
            ? process.env.PAYUNI_HASH_KEY_PROD!
            : process.env.PAYUNI_HASH_KEY_TEST!
        this.hashIV = isProd
            ? process.env.PAYUNI_HASH_IV_PROD!
            : process.env.PAYUNI_HASH_IV_TEST!
        this.apiUrl = isProd
            ? 'https://api.payuni.com.tw/api/upp'
            : 'https://sandbox-api.payuni.com.tw/api/upp'
    }

    private encrypt(data: Record<string, any>): { EncryptInfo: string, HashInfo: string } {
        // 1. JSON 字串化
        const jsonString = JSON.stringify(data)

        // 2. AES-256-GCM 加密
        const cipher = crypto.createCipheriv('aes-256-gcm', this.hashKey, this.hashIV)
        let encrypted = cipher.update(jsonString, 'utf8', 'hex')
        encrypted += cipher.final('hex')

        // 3. 取得 Auth Tag
        const authTag = cipher.getAuthTag().toString('hex')

        // 4. 組合加密資料
        const encryptInfo = encrypted + authTag

        // 5. SHA256 簽章
        const hashInfo = crypto
            .createHash('sha256')
            .update(`HashKey=${this.hashKey}&${encryptInfo}&HashIV=${this.hashIV}`)
            .digest('hex')
            .toUpperCase()

        return {
            EncryptInfo: encryptInfo,
            HashInfo: hashInfo
        }
    }

    async createOrder(userId: string, orderData: any) {
        const merchantOrderNo = `UNI${Date.now()}`

        const tradeData = {
            MerchantID: this.merchantID,
            MerchantOrderNo: merchantOrderNo,
            Amount: orderData.amount,
            ItemDescription: orderData.itemDesc || '商品購買',
            ReturnURL: orderData.returnURL,
            NotifyURL: orderData.notifyURL,
            Email: orderData.email,
            PaymentMethod: 'CREDIT',  // 信用卡
            TimeStamp: Math.floor(Date.now() / 1000)
        }

        // 加密
        const { EncryptInfo, HashInfo } = this.encrypt(tradeData)

        try {
            // RESTful POST 請求
            const response = await axios.post(this.apiUrl, {
                MerchantID: this.merchantID,
                EncryptInfo: EncryptInfo,
                HashInfo: HashInfo
            }, {
                headers: {
                    'Content-Type': 'application/json'
                }
            })

            console.log('[OK] PAYUNi 訂單建立')
            console.log('訂單編號:', merchantOrderNo)
            console.log('回應狀態:', response.data.Status)

            return {
                success: response.data.Status === 'SUCCESS',
                merchantTradeNo: merchantOrderNo,
                paymentUrl: response.data.Data?.PaymentURL,
                message: response.data.Message
            }
        } catch (error) {
            console.error('[ERROR] PAYUNi 請求失敗:', error)
            throw error
        }
    }
}

// 使用範例
async function createPAYUNiOrder() {
    const service = new PAYUNiService(false)

    const result = await service.createOrder('user-123', {
        amount: 3000,
        itemDesc: '會員升級方案',
        returnURL: 'https://yourdomain.com/payment/return',
        notifyURL: 'https://yourdomain.com/api/payment/callback',
        email: 'test@example.com'
    })

    if (result.success) {
        console.log('請導向:', result.paymentUrl)
    }

    return result
}
```

**重要說明：**
- PAYUNi 使用 RESTful JSON API（與 ECPay/NewebPay 的 Form POST 不同）
- AES-256-GCM 加密需要附加 Auth Tag（最後 32 字元）
- 回應為 JSON 格式，包含 PaymentURL 導向連結

**預期輸出：**
```
[OK] PAYUNi 訂單建立
訂單編號: UNI1738123456789
回應狀態: SUCCESS
請導向: https://sandbox-api.payuni.com.tw/trade/payment?token=xxx
```

---

## 進階範例

### 範例 4: 服務工廠模式

**場景：** 建立金流服務工廠，動態切換三家服務商

**Claude 提示詞：**
```
建立金流服務工廠，支援 ECPay、NewebPay、PAYUNi 動態切換
```

**生成的程式碼：**

```typescript
// lib/services/payment-provider.ts - 介面定義

export interface PaymentService {
    createOrder(userId: string, data: PaymentOrderData): Promise<PaymentOrderResponse>
    queryOrder(userId: string, merchantTradeNo: string): Promise<PaymentQueryResponse>
    refundOrder(userId: string, tradeNo: string, amount: number): Promise<PaymentRefundResponse>
    verifyCallback(params: Record<string, any>): boolean
}

export interface PaymentOrderData {
    merchantTradeNo: string
    totalAmount: number
    itemName: string
    returnURL: string
    notifyURL?: string
    email?: string
    paymentMethod?: string
}

export interface PaymentOrderResponse {
    success: boolean
    merchantTradeNo: string
    formAction: string
    formMethod: string
    formParams: Record<string, string>
    msg?: string
}

// lib/services/payment-service-factory.ts - 工廠類別

import { PaymentService } from './payment-provider'
import { ECPayPaymentService } from './ecpay-payment-service'
import { NewebPayPaymentService } from './newebpay-payment-service'
import { PAYUNiPaymentService } from './payuni-payment-service'
import { prisma } from '@/lib/prisma'

type PaymentProvider = 'ECPAY' | 'NEWEBPAY' | 'PAYUNI'

export class PaymentServiceFactory {
    /**
     * 根據服務商名稱取得服務實例
     */
    static getService(
        provider: PaymentProvider,
        isProd: boolean = false
    ): PaymentService {
        switch (provider) {
            case 'ECPAY':
                return new ECPayPaymentService(isProd)
            case 'NEWEBPAY':
                return new NewebPayPaymentService(isProd)
            case 'PAYUNI':
                return new PAYUNiPaymentService(isProd)
            default:
                throw new Error(`不支援的金流服務商: ${provider}`)
        }
    }

    /**
     * 根據使用者設定取得服務實例
     */
    static async getServiceForUser(userId: string): Promise<PaymentService> {
        const settings = await prisma.paymentSettings.findUnique({
            where: { userId },
        })

        if (!settings || !settings.defaultProvider) {
            throw new Error('未設定預設金流服務商')
        }

        return this.getService(
            settings.defaultProvider as PaymentProvider,
            settings.isProduction
        )
    }

    /**
     * 根據訂單取得服務實例（用於查詢/退款）
     */
    static async getServiceForOrder(merchantTradeNo: string): Promise<PaymentService> {
        const order = await prisma.order.findUnique({
            where: { merchantTradeNo },
        })

        if (!order || !order.paymentProvider) {
            throw new Error('訂單不存在或未記錄金流服務商')
        }

        return this.getService(
            order.paymentProvider as PaymentProvider,
            order.isProduction
        )
    }

    /**
     * 取得所有可用的服務商
     */
    static getAvailableProviders(): PaymentProvider[] {
        return ['ECPAY', 'NEWEBPAY', 'PAYUNI']
    }

    /**
     * 自動偵測服務商（根據回呼參數）
     */
    static detectProvider(params: Record<string, any>): PaymentProvider {
        if (params.CheckMacValue && params.MerchantTradeNo) {
            return 'ECPAY'
        }
        if (params.TradeInfo && params.TradeSha) {
            return 'NEWEBPAY'
        }
        if (params.EncryptInfo && params.HashInfo) {
            return 'PAYUNI'
        }
        throw new Error('無法識別金流服務商')
    }
}
```

**使用範例：**

```typescript
// API Route: app/api/payment/create/route.ts

import { PaymentServiceFactory } from '@/lib/services/payment-service-factory'

export async function POST(request: Request) {
    const { userId, amount, itemName, provider } = await request.json()

    // 方式 1: 使用指定服務商
    const service = PaymentServiceFactory.getService(provider || 'ECPAY')

    // 方式 2: 使用使用者預設服務商
    // const service = await PaymentServiceFactory.getServiceForUser(userId)

    const result = await service.createOrder(userId, {
        merchantTradeNo: `ORD${Date.now()}`,
        totalAmount: amount,
        itemName: itemName,
        returnURL: 'https://yourdomain.com/payment/return',
        notifyURL: 'https://yourdomain.com/api/payment/callback',
    })

    return Response.json(result)
}
```

---

### 範例 5: 加密輔助函數

**場景：** 建立三種加密方式的 helper functions

**Claude 提示詞：**
```
建立加密工具，包含 ECPay SHA256、NewebPay AES-CBC、PAYUNi AES-GCM
```

**生成的程式碼：**

```typescript
// lib/utils/payment-encryption.ts

import crypto from 'crypto'

/**
 * ECPay CheckMacValue 計算（SHA256）
 */
export function generateECPayCheckMacValue(
    params: Record<string, any>,
    hashKey: string,
    hashIV: string
): string {
    // 1. 移除 CheckMacValue 本身
    const { CheckMacValue, ...cleanParams } = params

    // 2. 依照 key 排序（字母順序）
    const sortedKeys = Object.keys(cleanParams).sort()

    // 3. 組合參數字串
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

/**
 * NewebPay AES-256-CBC 加密
 */
export function encryptNewebPay(
    data: Record<string, any>,
    hashKey: string,
    hashIV: string
): { TradeInfo: string; TradeSha: string } {
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
        TradeSha: tradeSha,
    }
}

/**
 * NewebPay AES-256-CBC 解密
 */
export function decryptNewebPay(
    encryptedData: string,
    hashKey: string,
    hashIV: string
): Record<string, any> {
    const decipher = crypto.createDecipheriv('aes-256-cbc', hashKey, hashIV)
    decipher.setAutoPadding(true)
    let decrypted = decipher.update(encryptedData, 'hex', 'utf8')
    decrypted += decipher.final('utf8')

    return Object.fromEntries(new URLSearchParams(decrypted))
}

/**
 * PAYUNi AES-256-GCM 加密
 */
export function encryptPAYUNi(
    data: Record<string, any>,
    hashKey: string,
    hashIV: string
): { EncryptInfo: string; HashInfo: string } {
    // 1. JSON 字串化
    const jsonString = JSON.stringify(data)

    // 2. AES-256-GCM 加密
    const cipher = crypto.createCipheriv('aes-256-gcm', hashKey, hashIV)
    let encrypted = cipher.update(jsonString, 'utf8', 'hex')
    encrypted += cipher.final('hex')

    // 3. 取得 Auth Tag (16 bytes)
    const authTag = cipher.getAuthTag().toString('hex')

    // 4. 組合加密資料
    const encryptInfo = encrypted + authTag

    // 5. SHA256 簽章
    const hashInfo = crypto
        .createHash('sha256')
        .update(`HashKey=${hashKey}&${encryptInfo}&HashIV=${hashIV}`)
        .digest('hex')
        .toUpperCase()

    return {
        EncryptInfo: encryptInfo,
        HashInfo: hashInfo,
    }
}

/**
 * PAYUNi AES-256-GCM 解密
 */
export function decryptPAYUNi(
    encryptedData: string,
    hashKey: string,
    hashIV: string
): Record<string, any> {
    // 1. 分離加密內容和 Auth Tag（最後 32 個字元）
    const encryptedContent = encryptedData.slice(0, -32)
    const authTag = Buffer.from(encryptedData.slice(-32), 'hex')

    // 2. AES-256-GCM 解密
    const decipher = crypto.createDecipheriv('aes-256-gcm', hashKey, hashIV)
    decipher.setAuthTag(authTag)
    let decrypted = decipher.update(encryptedContent, 'hex', 'utf8')
    decrypted += decipher.final('utf8')

    return JSON.parse(decrypted)
}

/**
 * 驗證簽章
 */
export function verifySignature(
    params: Record<string, any>,
    signature: string,
    hashKey: string,
    hashIV: string,
    provider: 'ECPAY' | 'NEWEBPAY' | 'PAYUNI'
): boolean {
    switch (provider) {
        case 'ECPAY':
            const calculatedECPay = generateECPayCheckMacValue(params, hashKey, hashIV)
            return calculatedECPay === signature
        case 'NEWEBPAY':
            const { TradeSha } = encryptNewebPay(params, hashKey, hashIV)
            return TradeSha === signature
        case 'PAYUNI':
            const { HashInfo } = encryptPAYUNi(params, hashKey, hashIV)
            return HashInfo === signature
        default:
            return false
    }
}
```

**使用範例：**

```typescript
import { generateECPayCheckMacValue, encryptNewebPay, encryptPAYUNi } from '@/lib/utils/payment-encryption'

// ECPay 簽章
const ecpayParams = {
    MerchantID: '3002607',
    MerchantTradeNo: 'ORD123456',
    TotalAmount: 1050,
}
const checkMacValue = generateECPayCheckMacValue(
    ecpayParams,
    'pwFHCqoQZGmho4w6',
    'EkRm7iFT261dpevs'
)
console.log('ECPay CheckMacValue:', checkMacValue)

// NewebPay 加密
const newebpayData = {
    MerchantID: 'MS12345678',
    MerchantOrderNo: 'MPG123456',
    Amt: 2500,
}
const { TradeInfo, TradeSha } = encryptNewebPay(
    newebpayData,
    'your32BytesHashKeyHere123456',
    'your16BytesIV123'
)
console.log('NewebPay TradeInfo:', TradeInfo.substring(0, 50) + '...')
console.log('NewebPay TradeSha:', TradeSha)

// PAYUNi 加密
const payuniData = {
    MerchantID: 'UNI12345',
    MerchantOrderNo: 'UNI123456',
    Amount: 3000,
}
const { EncryptInfo, HashInfo } = encryptPAYUNi(
    payuniData,
    'your32BytesHashKey',
    'your16BytesIV'
)
console.log('PAYUNi EncryptInfo:', EncryptInfo.substring(0, 50) + '...')
console.log('PAYUNi HashInfo:', HashInfo)
```

---

## 實戰場景

### 場景 1: 電商結帳流程整合

**需求：** 完整的訂單建立 → 金流付款 → 付款通知 → 訂單查詢流程

**步驟 1: 建立訂單並導向付款**

```typescript
// app/api/checkout/route.ts

import { PaymentServiceFactory } from '@/lib/services/payment-service-factory'
import { prisma } from '@/lib/prisma'

export async function POST(request: Request) {
    const { userId, cartItems, shippingInfo } = await request.json()

    // 1. 計算訂單金額
    const totalAmount = cartItems.reduce((sum, item) => {
        return sum + (item.price * item.quantity)
    }, 0)

    // 2. 產生訂單編號
    const merchantTradeNo = `ORD${Date.now()}${Math.random().toString(36).substring(2, 6).toUpperCase()}`

    // 3. 建立資料庫訂單
    const order = await prisma.order.create({
        data: {
            userId: userId,
            merchantTradeNo: merchantTradeNo,
            totalAmount: totalAmount,
            status: 'PENDING',
            shippingName: shippingInfo.name,
            shippingAddress: shippingInfo.address,
            shippingPhone: shippingInfo.phone,
            items: {
                create: cartItems.map(item => ({
                    productId: item.productId,
                    productName: item.name,
                    quantity: item.quantity,
                    price: item.price,
                }))
            }
        },
        include: { items: true }
    })

    // 4. 取得金流服務（使用者預設或指定）
    const service = await PaymentServiceFactory.getServiceForUser(userId)

    // 5. 建立付款訂單
    const itemNames = order.items.map(item => `${item.productName} x${item.quantity}`).join('|')

    const paymentResult = await service.createOrder(userId, {
        merchantTradeNo: merchantTradeNo,
        totalAmount: totalAmount,
        itemName: itemNames.substring(0, 200), // 限制長度
        returnURL: `${process.env.NEXT_PUBLIC_BASE_URL}/payment/return`,
        notifyURL: `${process.env.NEXT_PUBLIC_BASE_URL}/api/payment/callback`,
        email: shippingInfo.email,
    })

    // 6. 更新訂單記錄金流服務商
    await prisma.order.update({
        where: { id: order.id },
        data: {
            paymentProvider: paymentResult.provider || 'ECPAY',
        }
    })

    // 7. 回傳付款表單資料
    return Response.json({
        success: true,
        orderId: order.id,
        merchantTradeNo: merchantTradeNo,
        paymentForm: {
            action: paymentResult.formAction,
            method: paymentResult.formMethod,
            params: paymentResult.formParams,
        }
    })
}
```

**步驟 2: 處理付款通知回呼**

```typescript
// app/api/payment/callback/route.ts

import { PaymentServiceFactory } from '@/lib/services/payment-service-factory'
import { prisma } from '@/lib/prisma'

export async function POST(request: Request) {
    const formData = await request.formData()
    const params = Object.fromEntries(formData)

    console.log('[INFO] 收到付款通知:', params)

    try {
        // 1. 自動偵測服務商
        const provider = PaymentServiceFactory.detectProvider(params)
        const service = PaymentServiceFactory.getService(provider)

        // 2. 驗證簽章
        const isValid = service.verifyCallback(params)
        if (!isValid) {
            console.error('[ERROR] 簽章驗證失敗')
            return new Response('0|CheckMacValue Error', { status: 400 })
        }

        // 3. 取得訂單編號（各服務商欄位不同）
        const merchantTradeNo = params.MerchantTradeNo || params.MerchantOrderNo

        // 4. 更新訂單狀態
        const isPaid = params.RtnCode === '1' || params.Status === 'SUCCESS'

        await prisma.order.update({
            where: { merchantTradeNo },
            data: {
                status: isPaid ? 'PAID' : 'FAILED',
                paidAt: isPaid ? new Date() : null,
                tradeNo: params.TradeNo || params.TradeID, // 金流商訂單號
                paymentMethod: params.PaymentType || params.PaymentMethod,
                paymentDetails: JSON.stringify(params),
                failureReason: isPaid ? null : params.RtnMsg || params.Message,
            }
        })

        console.log(`[OK] 訂單 ${merchantTradeNo} 狀態更新為 ${isPaid ? 'PAID' : 'FAILED'}`)

        // 5. 付款成功後續處理
        if (isPaid) {
            // 發送通知郵件、扣減庫存、開立發票等
            // await sendOrderConfirmationEmail(merchantTradeNo)
            // await reduceInventory(merchantTradeNo)
        }

        // 6. 回應固定格式
        return new Response('1|OK', {
            status: 200,
            headers: { 'Content-Type': 'text/plain' }
        })

    } catch (error) {
        console.error('[ERROR] 付款通知處理失敗:', error)
        return new Response('0|Error', { status: 500 })
    }
}
```

**步驟 3: 查詢訂單狀態**

```typescript
// app/api/payment/query/route.ts

import { PaymentServiceFactory } from '@/lib/services/payment-service-factory'
import { prisma } from '@/lib/prisma'

export async function GET(request: Request) {
    const { searchParams } = new URL(request.url)
    const merchantTradeNo = searchParams.get('merchantTradeNo')

    if (!merchantTradeNo) {
        return Response.json({ error: '缺少訂單編號' }, { status: 400 })
    }

    try {
        // 1. 從資料庫取得訂單
        const order = await prisma.order.findUnique({
            where: { merchantTradeNo }
        })

        if (!order) {
            return Response.json({ error: '訂單不存在' }, { status: 404 })
        }

        // 2. 使用訂單記錄的服務商查詢
        const service = await PaymentServiceFactory.getServiceForOrder(merchantTradeNo)
        const queryResult = await service.queryOrder(order.userId, merchantTradeNo)

        // 3. 同步訂單狀態
        if (queryResult.success && queryResult.status !== order.status) {
            await prisma.order.update({
                where: { merchantTradeNo },
                data: {
                    status: queryResult.status,
                    paidAt: queryResult.paidAt,
                }
            })
        }

        return Response.json({
            success: true,
            order: {
                merchantTradeNo: order.merchantTradeNo,
                amount: order.totalAmount,
                status: queryResult.status || order.status,
                paidAt: queryResult.paidAt || order.paidAt,
                provider: order.paymentProvider,
            }
        })

    } catch (error) {
        console.error('[ERROR] 查詢訂單失敗:', error)
        return Response.json({ error: '查詢失敗' }, { status: 500 })
    }
}
```

**步驟 4: 前端整合**

```typescript
// components/CheckoutButton.tsx

'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'

export function CheckoutButton({ cartItems, shippingInfo }) {
    const [loading, setLoading] = useState(false)

    const handleCheckout = async () => {
        setLoading(true)
        try {
            // 1. 建立訂單
            const response = await fetch('/api/checkout', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    userId: 'user-123',
                    cartItems,
                    shippingInfo,
                })
            })

            const result = await response.json()

            if (!result.success) {
                alert('結帳失敗')
                return
            }

            // 2. 提交付款表單
            const form = document.createElement('form')
            form.method = result.paymentForm.method
            form.action = result.paymentForm.action
            form.target = '_self'

            Object.entries(result.paymentForm.params).forEach(([key, value]) => {
                const input = document.createElement('input')
                input.type = 'hidden'
                input.name = key
                input.value = value as string
                form.appendChild(input)
            })

            document.body.appendChild(form)
            form.submit()

        } catch (error) {
            console.error('結帳失敗:', error)
            alert('結帳失敗')
        } finally {
            setLoading(false)
        }
    }

    return (
        <Button onClick={handleCheckout} disabled={loading} size="lg">
            {loading ? '處理中...' : '前往付款'}
        </Button>
    )
}
```

---

### 場景 2: 定期定額訂閱

**需求：** 實作週期扣款功能（會員訂閱制）

**步驟 1: 建立定期定額訂單**

```typescript
// app/api/subscription/create/route.ts

import { ECPayPaymentService } from '@/lib/services/ecpay-payment-service'
import { prisma } from '@/lib/prisma'

export async function POST(request: Request) {
    const { userId, planId, email } = await request.json()

    // 1. 取得訂閱方案
    const plan = await prisma.subscriptionPlan.findUnique({
        where: { id: planId }
    })

    if (!plan) {
        return Response.json({ error: '方案不存在' }, { status: 404 })
    }

    // 2. 產生訂閱編號
    const merchantTradeNo = `SUB${Date.now()}`

    // 3. 建立訂閱記錄
    const subscription = await prisma.subscription.create({
        data: {
            userId: userId,
            planId: planId,
            merchantTradeNo: merchantTradeNo,
            status: 'PENDING',
            amount: plan.price,
            frequency: plan.frequency, // 'M' = 月, 'Y' = 年
            totalTimes: plan.totalTimes || 999, // 999 = 無限次
        }
    })

    // 4. 建立 ECPay 定期定額訂單
    const service = new ECPayPaymentService(false) // 測試環境

    const periodicData = {
        MerchantTradeNo: merchantTradeNo,
        MerchantTradeDate: new Date().toLocaleString('zh-TW', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        }).replace(/\//g, '/'),
        TotalAmount: plan.price,
        TradeDesc: `訂閱方案：${plan.name}`,
        ItemName: plan.name,
        ReturnURL: `${process.env.NEXT_PUBLIC_BASE_URL}/api/subscription/callback`,
        PeriodAmount: plan.price,       // 每期金額
        PeriodType: plan.frequency,     // 'M' = 月, 'Y' = 年
        Frequency: 1,                   // 每 1 個週期
        ExecTimes: plan.totalTimes,     // 執行次數
        PeriodReturnURL: `${process.env.NEXT_PUBLIC_BASE_URL}/api/subscription/periodic-callback`,
    }

    const result = await service.createPeriodicOrder(userId, periodicData)

    return Response.json({
        success: result.success,
        subscriptionId: subscription.id,
        paymentForm: {
            action: result.formAction,
            method: result.formMethod,
            params: result.formParams,
        }
    })
}
```

**步驟 2: 處理首次授權回呼**

```typescript
// app/api/subscription/callback/route.ts

import { prisma } from '@/lib/prisma'

export async function POST(request: Request) {
    const formData = await request.formData()
    const params = Object.fromEntries(formData)

    console.log('[INFO] 收到訂閱授權通知:', params)

    const merchantTradeNo = params.MerchantTradeNo
    const isPaid = params.RtnCode === '1'

    // 更新訂閱狀態
    await prisma.subscription.update({
        where: { merchantTradeNo },
        data: {
            status: isPaid ? 'ACTIVE' : 'FAILED',
            gwsr: params.gwsr, // 綠界週期編號（重要：後續扣款需要）
            firstPaidAt: isPaid ? new Date() : null,
        }
    })

    console.log(`[OK] 訂閱 ${merchantTradeNo} 授權${isPaid ? '成功' : '失敗'}`)

    return new Response('1|OK')
}
```

**步驟 3: 處理週期扣款通知**

```typescript
// app/api/subscription/periodic-callback/route.ts

import { prisma } from '@/lib/prisma'

export async function POST(request: Request) {
    const formData = await request.formData()
    const params = Object.fromEntries(formData)

    console.log('[INFO] 收到週期扣款通知:', params)

    const gwsr = params.gwsr // 綠界週期編號
    const isPaid = params.RtnCode === '1'
    const execTimes = parseInt(params.ExecTimes) // 當前第幾次扣款

    // 1. 更新訂閱記錄
    const subscription = await prisma.subscription.findFirst({
        where: { gwsr }
    })

    if (subscription) {
        // 2. 建立扣款記錄
        await prisma.subscriptionPayment.create({
            data: {
                subscriptionId: subscription.id,
                merchantTradeNo: params.MerchantTradeNo,
                tradeNo: params.TradeNo,
                amount: parseInt(params.amount),
                execTimes: execTimes,
                status: isPaid ? 'PAID' : 'FAILED',
                paidAt: isPaid ? new Date() : null,
                failureReason: isPaid ? null : params.RtnMsg,
            }
        })

        // 3. 更新訂閱狀態
        await prisma.subscription.update({
            where: { id: subscription.id },
            data: {
                currentExecTimes: execTimes,
                lastPaidAt: isPaid ? new Date() : subscription.lastPaidAt,
            }
        })

        console.log(`[OK] 訂閱 ${subscription.merchantTradeNo} 第 ${execTimes} 次扣款${isPaid ? '成功' : '失敗'}`)

        // 4. 扣款成功後續處理
        if (isPaid) {
            // 延長會員期限、發送通知等
            // await extendMembershipPeriod(subscription.userId)
        }
    }

    return new Response('1|OK')
}
```

---

## 常見錯誤與修正

### 錯誤 1: CheckMacValue 計算錯誤

**錯誤訊息：** ECPay 回傳 `10100058: 請確認檢查碼是否正確`

**原因：** 參數排序錯誤或 URL Encode 不正確

**修正前：**
```typescript
// * 錯誤：未排序參數
function generateCheckMacValue(params: Record<string, any>, hashKey: string, hashIV: string) {
    const paramString = Object.entries(params)
        .map(([k, v]) => `${k}=${v}`)
        .join('&')

    const rawString = `HashKey=${hashKey}&${paramString}&HashIV=${hashIV}`
    const hash = crypto.createHash('sha256').update(rawString).digest('hex')
    return hash.toUpperCase()
}
```

**修正後：**
```typescript
// *! 正確：排序 + URL Encode (lowercase)
function generateCheckMacValue(params: Record<string, any>, hashKey: string, hashIV: string) {
    // 1. 移除 CheckMacValue 本身
    const { CheckMacValue, ...cleanParams } = params

    // 2. 排序 keys
    const sortedKeys = Object.keys(cleanParams).sort()

    // 3. 組合參數字串
    const paramString = sortedKeys
        .map(key => `${key}=${cleanParams[key]}`)
        .join('&')

    // 4. 前後加上 HashKey/HashIV
    const rawString = `HashKey=${hashKey}&${paramString}&HashIV=${hashIV}`

    // 5. URL Encode (lowercase)
    const encoded = encodeURIComponent(rawString).toLowerCase()

    // 6. SHA256 + 大寫
    const hash = crypto.createHash('sha256').update(encoded).digest('hex')
    return hash.toUpperCase()
}
```

**驗證方法：**
```typescript
// 測試範例
const params = {
    MerchantID: '3002607',
    MerchantTradeNo: 'ORD123456',
    MerchantTradeDate: '2024/01/29 12:00:00',
    TotalAmount: 1050,
}

const checkMacValue = generateCheckMacValue(
    params,
    'pwFHCqoQZGmho4w6',
    'EkRm7iFT261dpevs'
)

console.log('計算結果:', checkMacValue)
// 應該與 ECPay 要求的值一致
```

---

### 錯誤 2: AES 加密錯誤

**錯誤訊息：** NewebPay 回傳 `TradeSha 錯誤` 或 PAYUNi 回傳 `HashInfo 錯誤`

**原因：** Key/IV 長度錯誤或未附加 Auth Tag

**修正前 (NewebPay)：**
```typescript
// * 錯誤：Key/IV 長度不正確
function encryptNewebPay(data: Record<string, any>, hashKey: string, hashIV: string) {
    const queryString = new URLSearchParams(data).toString()

    // 錯誤：未檢查 Key/IV 長度
    const cipher = crypto.createCipheriv('aes-256-cbc', hashKey, hashIV)
    let encrypted = cipher.update(queryString, 'utf8', 'hex')
    encrypted += cipher.final('hex')

    return encrypted
}
```

**修正後 (NewebPay)：**
```typescript
// *! 正確：確認 Key/IV 長度 + 計算 TradeSha
function encryptNewebPay(data: Record<string, any>, hashKey: string, hashIV: string) {
    // 確認長度
    if (hashKey.length !== 32) throw new Error('HashKey 必須 32 bytes')
    if (hashIV.length !== 16) throw new Error('HashIV 必須 16 bytes')

    const queryString = new URLSearchParams(data).toString()

    // AES-256-CBC 加密
    const cipher = crypto.createCipheriv('aes-256-cbc', hashKey, hashIV)
    cipher.setAutoPadding(true)
    let encrypted = cipher.update(queryString, 'utf8', 'hex')
    encrypted += cipher.final('hex')

    // 計算 TradeSha
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
```

**修正前 (PAYUNi)：**
```typescript
// * 錯誤：忘記附加 Auth Tag
function encryptPAYUNi(data: Record<string, any>, hashKey: string, hashIV: string) {
    const jsonString = JSON.stringify(data)

    const cipher = crypto.createCipheriv('aes-256-gcm', hashKey, hashIV)
    let encrypted = cipher.update(jsonString, 'utf8', 'hex')
    encrypted += cipher.final('hex')

    // 錯誤：忘記取得 Auth Tag
    return encrypted
}
```

**修正後 (PAYUNi)：**
```typescript
// *! 正確：附加 Auth Tag
function encryptPAYUNi(data: Record<string, any>, hashKey: string, hashIV: string) {
    const jsonString = JSON.stringify(data)

    // AES-256-GCM 加密
    const cipher = crypto.createCipheriv('aes-256-gcm', hashKey, hashIV)
    let encrypted = cipher.update(jsonString, 'utf8', 'hex')
    encrypted += cipher.final('hex')

    // 取得 Auth Tag（16 bytes = 32 hex chars）
    const authTag = cipher.getAuthTag().toString('hex')

    // 組合：encrypted + authTag
    const encryptInfo = encrypted + authTag

    // 計算 HashInfo
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
```

**測試工具：**
```typescript
// 測試 NewebPay 加密/解密
const testData = { test: 'hello', amount: 1000 }
const { TradeInfo, TradeSha } = encryptNewebPay(testData, hashKey, hashIV)
const decrypted = decryptNewebPay(TradeInfo, hashKey, hashIV)
console.log('原始:', testData)
console.log('解密:', decrypted)
console.log('一致:', JSON.stringify(testData) === JSON.stringify(decrypted))

// 測試 PAYUNi 加密/解密
const { EncryptInfo, HashInfo } = encryptPAYUNi(testData, hashKey, hashIV)
const decryptedPAYUNi = decryptPAYUNi(EncryptInfo, hashKey, hashIV)
console.log('原始:', testData)
console.log('解密:', decryptedPAYUNi)
console.log('一致:', JSON.stringify(testData) === JSON.stringify(decryptedPAYUNi))
```

---

## SmilePay 速買配範例

SmilePay 採用 `Verify_key` + `mid` 共享密鑰機制，無 AES 加密，整合最簡單。回應為 XML（部分欄位可能是 BIG-5 編碼，需轉 UTF-8）。

### 完整 Python 範例
請見 [`examples/smilepay-payment-example.py`](examples/smilepay-payment-example.py) — 涵蓋 ATM (Pay_zg=2) / Barcode (Pay_zg=3) / ibon (Pay_zg=4) / FamiPort (Pay_zg=6) / 信用卡 (Pay_zg=1) / 信用卡分期 / 聯合信用卡 (Pay_zg=11) 七種付款方式。

### 五大踩坑

1. **Pay_zg 是核心參數**：每種付款方式對應不同的 Pay_zg 值；分期是 `Pay_zg=1` + `Stage` 額外欄位。
2. **回應是 XML，不是 JSON**：用 `xml.etree.ElementTree` 解析；常用欄位 `Status`、`Desc`、`Smseid`、`PaymentNo`。
3. **通知時要驗證 `Mid_smilepay` 加權檢核碼**：這是 SmilePay 防偽機制；演算法在 `smilepay-payment-api.md` 文件中（從 plugin 反推）。
4. **部分通知欄位為 BIG-5 編碼**：`Process_time` / `Address` / `Errdesc` 需 BIG-5→UTF-8。
5. **沒有正式查詢端點**：靠通知 + `mtmk_utf.asp` 補；通知會重試但無公開重試 SLA。

---

## PChomePay 拍錢包範例

PChomePay 採用 **HTTP Basic Auth → pcpay-token** 兩階段認證：先用 APP_ID + SECRET 取得 token（8 小時有效），後續 API 帶 `pcpay-token` header。

### 完整 Python 範例
請見 [`examples/pchomepay-payment-example.py`](examples/pchomepay-payment-example.py) — 涵蓋 token 自動刷新、信用卡、ATM、超商代碼、訂單查詢、退款。

### 四大要點

1. **白名單 IP**：PChomePay notify 的來源 IP 是 `113.196.231.190`，**必須加入後台白名單**。
2. **Token 機制**：開立 token 預設 28800 秒（8h）有效；要在程式自行 cache 並避免逾期重發。
3. **沙箱測試靠金額尾數**：例如 ATM 訂單金額尾數 `0-7` 自動付款成功、`8` 過期、`9` 5 分鐘後過期。
4. **退款手續費**：除信用卡免手續費外，ATM/超商等需「退款金額 + 退款手續費」共同從餘額扣除；退款手續費為 NT$15（依官方）。

---

## ezPay 簡單付範例

ezPay 是藍新 NewebPay 集團的小型商家品牌，金流 API **與 NewebPay MPG 完全相同**（TradeInfo / TradeSha / AES-256-CBC + SHA256），只在 MerchantID、HashKey、URL 與部分付款方式上有差異。

### 完整 Python 範例
請見 [`examples/ezpay-payment-example.py`](examples/ezpay-payment-example.py) — 由 `newebpay-payment-example.py` 衍生，凸顯差異點。

### 三大要點

1. **加密邏輯完全照抄 NewebPay**：可直接複用同一份加解密 helper。
2. **URL 不同**：ezPay 沙箱 `https://ccore.spgateway.com/MPG/mpg_gateway`（spgateway.com 是舊網域，仍可用）。
3. **付款方式受限**：分期、部分電子錢包在 ezPay 計劃下不可用；以後台啟用為準。

---

## PayNow 立吉富範例

PayNow 有**兩代 API 並行**：
- **傳統版（cashflow）**：form-post，動態 AES-256（每次以 GP/GK 檢核碼即時取得 Key/IV）
- **現代版（apidoc）**：JWT Bearer + RESTful JSON + PaymentIntent / Customer / Card Token（接近 Stripe）

新專案應優先採用現代版。

### 完整 Python 範例
請見 [`examples/paynow-payment-example.py`](examples/paynow-payment-example.py) — 涵蓋 PaymentIntent 建立 / Checkout / Refund / Apple Pay session / Customer / Card Token，搭配傳統版的 form-post 範例 stub。

### 五大要點

1. **新專案走現代版**：傳統版的 GP/GK 動態金鑰機制學習成本高、易出錯；只有舊系統相容才需要。
2. **Apple Pay 完整支援**：含 v1 / v2 一般流程 + Deferred 延遲扣款（PayNow 獨家）。
3. **Card Token 可跨訂單記憶**：透過 Customer + Card Token 機制做訂閱、回購快速結帳。
4. **`webhookUrl` 是現代版的 callback 機制**：不同於傳統版的 `Roturl`。
5. **`channelId` 對 LINE Pay 必須額外設定**：`paymentMethodType=LINEPayOnline` 時需提供 PayNow 簽發的 channelId。

---

## Shopline Payments 範例

Shopline Payments (SLP) 採 **HTTP Header `merchantId` + `apiKey`** 認證，所有金額以**分**為單位（NT$1000 = 100000）。提供 Redirect 與 Embedded SDK 雙模式，Webhook 用 HMAC-SHA256 驗章。

### 完整 Python 範例
請見 [`examples/shopline-payment-example.py`](examples/shopline-payment-example.py) — 涵蓋 sessions/create / sessionQuery / refund / Webhook 驗章。

### 三大要點

1. **金額是分（cents）**：NT$1,050 要傳 `value: 105000`，弄錯會差 100 倍。
2. **僅支援 TWD**：`currency` 固定為 `TWD`；其他幣別不支援。
3. **Webhook 驗章**：`x-slp-signature: sha256=<hex>` header，HMAC-SHA256 用 `webhookSecret` 對 raw body 簽。**用 raw bytes，不要 parse JSON 後再 stringify**（會差換行/空白）。

---

## LINE Pay v4 範例

LINE Pay 採 **兩段式流程**：`Request → Confirm`。每次請求需產生 Nonce + HMAC-SHA256 簽章。

### 完整 Python 範例
請見 [`examples/linepay-payment-example.py`](examples/linepay-payment-example.py) — 涵蓋 Request / Confirm / Capture / Void / Refund / Preapproved Pay (自動扣款)。

### 五大要點

1. **HMAC string-to-sign 公式（v3 慣例）**：`ChannelSecret + ApiPath + Body + Nonce` (POST) / `ChannelSecret + ApiPath + QueryString + Nonce` (GET)。⚠️ v4 公式與 v3 是否完全一致需以官方 PDF 驗證。
2. **transactionId 是 19 位數字**：在 JS 直接用 number 會被 IEEE-754 截斷，**永遠用字串處理**。
3. **Confirm 的 amount/currency 必須與 Request 完全一致**：差一塊錢就 1183 錯誤。
4. **Capture 兩階段授權**：建立時 `options.payment.capture=false` 只授權；之後手動呼叫 `/capture` 請款，可分批請款多次。
5. **Preapproved Pay 自動扣款**：建立時帶 `payType=PREAPPROVED` 取得 `regKey`，之後用 `/preapprovedPay/{regKey}/payment` 直接扣款，免使用者再次確認。

---

## TapPay 範例

TapPay 是 **PCI 隔離設計**：前端 SDK 取 Prime（60 秒 TTL）→ 後端用 Prime 呼叫 pay-by-prime。商家從不接觸卡號。

### 完整 Python 範例
請見 [`examples/tappay-payment-example.py`](examples/tappay-payment-example.py) — 涵蓋 pay-by-prime / pay-by-card-token (重複扣款) / refund / query / remove-card。

### 四大要點

1. **三段式金鑰**：`Partner Key` (後端密鑰) / `App Key` (前端 SDK 公鑰) / `Merchant ID`。**Partner Key 絕對不可放前端**。
2. **Prime 是 60 秒一次性 token**：前端取 Prime 後要立刻送後端付款；過期或重用會 status=3。
3. **重複扣款**：`pay-by-prime` 帶 `remember=true` 後，回應內 `card_secret` 含 `card_key + card_token`，存起來下次直接 `pay-by-card-token`，免再過 SDK。適合訂閱與快速結帳。
4. **status=0 才是成功**：別只看 HTTP 200；TapPay HTTP 200 但 status≠0 是業務失敗。

## O'Pay 歐付寶範例

**與 ECPay 同源**——`MerchantID` + 排序後 urlencode + SHA256 的 `CheckMacValue`，欄位名幾乎完全一致。已有 ECPay 實作者，**換網域即可**：

```python
# ECPay
https://payment-stage.ecpay.com.tw/Cashier/AioCheckOut/V5
# O'Pay：只換網域，CheckMacValue 演算法與參數名不變
https://payment-stage.opay.tw/Cashier/AioCheckOut/V5
```

實作直接沿用 [`examples/ecpay-payment-example.py`](examples/ecpay-payment-example.py)，把 base URL 與金鑰換掉即可。

### O'Pay 獨有、ECPay 沒有的

| 能力 | 說明 |
|---|---|
| `AccountLink` | 銀行快付 |
| `TopUpUsed` | 儲值消費 |
| `WeiXinpay` | 微信支付（線上線下）|
| `HoldTradeAMT=1` | **延遲撥款**，款項先留在歐付寶，確認出貨後再申請撥款——做代收代付或擔保交易時很有用 |

## 街口支付 JKOPAY 範例

### 完整 Python 範例
請見 [`examples/jkopay-payment-example.py`](examples/jkopay-payment-example.py) — 涵蓋 Entry / Refund / Inquiry / 授權扣款（綁定、發動、終止），並內建**官方測試向量的自我驗證**（直接執行即可確認你的環境算出的 digest 與街口一致，不會發網路請求）。

### 五大要點

1. **簽的是 payload 原始字串**，不排序、不 urlencode。這與 ECPay 的 `CheckMacValue` 完全不同路數，從綠界遷移最容易卡在這。
2. **連空白都算數**。官方範例 `"currency": "TWD"` 冒號後有空格，拿掉 digest 就變。**先組好字串、簽它、原封不動送出**，不要簽完再用另一次 `json.dumps()` 產生 body。
3. **街口有三套簽章**（線上支付／POS／OAuth），程式碼不可共用。見 [reference §7](references/jkopay-payment-api.md)。
4. **對帳用 `debit_amount` 不是 `final_price`**。街口幣與券折抵不進撥款，用 `final_price` 對帳會長期短差。
5. **授權扣款有六個硬限制**，其中兩個直接約束排程設計：`306` 扣款只能在 **08:00–20:00** 發動（夜間 batch 必失敗）、`307` 同一 `auth_no` **不可併發**（扣款必須序列化）。

### 一個資料庫層的地雷

`payment_url` 與 `qr_img` 的**長度會超過 255**，欄位不要開 `VARCHAR(255)`。

## 紅陽科技 SunPay 範例

### 完整 Python 範例
請見 [`examples/sunpay-payment-example.py`](examples/sunpay-payment-example.py) — 涵蓋 `rsamsg` 加解密、`check_value` 簽章、`send_time` 組法、兩張 `pay_result` 對照表、物流通知解析，並內建**官方測試向量的自我驗證**。

### 四大要點

1. **14 家中唯一使用非對稱加密**。RSA 分段加密 + SHA256 簽章，既有的 SHA256 檢查碼或 AES 程式碼一律不能沿用。
2. **加密分段 117、解密分段 128**——兩者不同。128 是 1024-bit RSA 的密文區塊長度，117 = 128 − 11（PKCS#1 v1.5 padding）。誤寫成同一個值是最常見的錯。
3. **`send_time` 格式是反的**：`fffssmmHHyyyyMMdd`，毫秒在最前面、日期在最後。且**超過 120 秒即無效**，主機要 NTP 校時。
4. **SHA2 密鑰接在字串尾端**，不是 ECPay 那種 `HashKey=...&參數&HashIV=...` 前後包夾。且 `null` 值的參數不參與簽名。

### ⚠️ 最容易踩的一致性陷阱

同一個欄位名 `pay_result`、同一個值 `12`：

| API | `12` 的意思 |
|---|---|
| 交易 CallBack | **已建立** |
| 查詢 API | **查無該筆訂單** |

**兩張代碼表必須分開維護，絕不可共用同一份 mapping。** 範例檔中已拆成 `CALLBACK_RESULT` 與 `QUERY_RESULT` 兩個字典並附自我驗證。

### 其他

- 交易與查詢是 `/v4/`，但**請款與退款仍是 `/v3/`**——同一份手冊裡版號不一致，不是筆誤
- 物流狀態通知是 **HTTP FORM POST key-value（非 JSON）**且全欄位經 URL Encode，另訂單編號欄位是**大寫 `Td`**
- 回傳網址**不可帶 port**，會被資安風控擋掉；CallBack **僅補發 30 分鐘**（每 5 分鐘一次），需另實作查詢對帳

## GoMyPay 範例

尚無範例——目前只取得服務層資訊，參數層需洽客服取得完整 API 文件。見 [reference](references/gomypay-payment-api.md)。

---

**更多範例持續更新中...**
