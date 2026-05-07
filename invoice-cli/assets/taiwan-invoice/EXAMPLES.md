# 台灣電子發票 Skill - 完整範例集

這份文件包含使用 `taiwan-invoice` skill 的完整實作範例。

## 目錄

1. [基礎範例](#基礎範例)
2. [進階範例](#進階範例)
3. [實戰場景](#實戰場景)
4. [常見錯誤與修正](#常見錯誤與修正)

---

## 基礎範例

### 範例 1: 開立簡單的 B2C 發票

**場景：** 客戶在網站購買商品，金額 1050 元

**Claude 提示詞：**
```
使用綠界測試環境開立 B2C 發票
- 金額: 1050 元
- 買受人: 王小明
- Email: test@example.com
- 商品: 測試商品 x1
```

**生成的程式碼：**

```typescript
import { ECPayInvoiceService } from '@/lib/services/ecpay-invoice-service'

async function issueSimpleInvoice() {
    const service = new ECPayInvoiceService(false) // 測試環境

    try {
        const result = await service.issueInvoice('user-123', {
            OrderId: `ORDER-${Date.now()}`,
            TotalAmount: 1050,
            IsB2B: false,
            BuyerName: '王小明',
            BuyerEmail: 'test@example.com',
            ProductItem: [
                {
                    Description: '測試商品',
                    Quantity: 1,
                    UnitPrice: 1050,
                    Amount: 1050,
                }
            ],
        })

        if (result.success) {
            console.log('[OK] 發票開立成功')
            console.log('發票號碼:', result.invoiceNumber)
            console.log('隨機碼:', result.randomNumber)
        } else {
            console.error('[ERROR] 開立失敗:', result.msg)
        }

        return result
    } catch (error) {
        console.error('發票開立異常:', error)
        throw error
    }
}
```

---

### 範例 2: 開立 B2B 三聯式發票

**場景：** 公司採購，需要打統編

**Claude 提示詞：**
```
開立 B2B 發票
- 買方統編: 12345678
- 買方名稱: 測試公司有限公司
- 金額: 10500 元（含稅）
- 使用綠界
```

**生成的程式碼：**

```typescript
async function issueB2BInvoice() {
    const service = new ECPayInvoiceService(false)

    // 計算 B2B 金額（分拆未稅與稅額）
    const totalAmount = 10500
    const taxAmount = Math.round(totalAmount - (totalAmount / 1.05))
    const salesAmount = totalAmount - taxAmount

    console.log('金額分析:')
    console.log('- 未稅金額:', salesAmount)  // 10000
    console.log('- 稅額 (5%):', taxAmount)    // 500
    console.log('- 總計:', totalAmount)        // 10500

    const result = await service.issueInvoice('user-123', {
        OrderId: `B2B-${Date.now()}`,
        TotalAmount: totalAmount,
        SalesAmount: salesAmount,
        TaxAmount: taxAmount,
        IsB2B: true,
        BuyerIdentifier: '12345678',
        BuyerName: '測試公司有限公司',
        BuyerAddress: '台北市信義區信義路五段7號',
        BuyerEmail: 'invoice@testcompany.com',
        ProductItem: [
            {
                Description: '網站開發服務',
                Quantity: 1,
                UnitPrice: salesAmount,  // B2B 使用未稅價
                Amount: salesAmount,
            }
        ],
    })

    return result
}
```

---

### 範例 3: 發票列印

**Claude 提示詞：**
```
實作發票列印功能，需要處理三種回應格式
```

**生成的程式碼：**

```typescript
// API Route: app/api/v1/invoices/[id]/print/route.ts

import { NextRequest, NextResponse } from 'next/server'
import { InvoiceServiceFactory } from '@/lib/services/invoice-service-factory'
import { getServerSession } from 'next-auth'

export async function POST(
    request: NextRequest,
    { params }: { params: { id: string } }
) {
    const session = await getServerSession()
    if (!session) {
        return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const recordId = params.id

    // 取得發票記錄
    const record = await prisma.financialRecord.findUnique({
        where: { id: recordId },
    })

    if (!record || !record.invoiceNo) {
        return NextResponse.json({ error: '發票不存在' }, { status: 404 })
    }

    // 使用開立時的服務商
    const service = record.invoiceProvider
        ? InvoiceServiceFactory.getService(record.invoiceProvider)
        : await InvoiceServiceFactory.getServiceForUser(session.user.id)

    try {
        const result = await service.printInvoice(
            session.user.id,
            record.invoiceNo
        )

        return NextResponse.json(result)
    } catch (error) {
        console.error('列印發票失敗:', error)
        return NextResponse.json(
            { error: '列印發票失敗' },
            { status: 500 }
        )
    }
}
```

**前端處理：**

```typescript
// components/InvoicePrintButton.tsx

'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'

export function InvoicePrintButton({ invoiceId }: { invoiceId: string }) {
    const [loading, setLoading] = useState(false)

    const handlePrint = async () => {
        setLoading(true)
        try {
            const response = await fetch(`/api/v1/invoices/${invoiceId}/print`, {
                method: 'POST',
            })

            const result = await response.json()

            if (!result.success) {
                alert('列印失敗: ' + result.msg)
                return
            }

            // 根據回應類型處理
            switch (result.type) {
                case 'html':
                    // 綠界：開新視窗顯示 HTML
                    const win = window.open('', '_blank')
                    if (win) {
                        win.document.write(result.htmlContent)
                        win.document.close()
                    }
                    break

                case 'redirect':
                    // 速買配/光貿：跳轉 URL
                    window.open(result.printUrl || result.url, '_blank')
                    break

                case 'form':
                    // 表單提交方式
                    const form = document.createElement('form')
                    form.method = 'POST'
                    form.action = result.formUrl
                    form.target = '_blank'

                    Object.entries(result.formParams || {}).forEach(([key, value]) => {
                        const input = document.createElement('input')
                        input.type = 'hidden'
                        input.name = key
                        input.value = value as string
                        form.appendChild(input)
                    })

                    document.body.appendChild(form)
                    form.submit()
                    document.body.removeChild(form)
                    break
            }
        } catch (error) {
            console.error('列印發票錯誤:', error)
            alert('列印發票失敗')
        } finally {
            setLoading(false)
        }
    }

    return (
        <Button onClick={handlePrint} disabled={loading}>
            {loading ? '處理中...' : '列印發票'}
        </Button>
    )
}
```

---

## 進階範例

### 範例 4: 服務商工廠模式

**Claude 提示詞：**
```
建立發票服務工廠，支援動態切換服務商
```

**生成的程式碼：**

```typescript
// lib/services/invoice-service-factory.ts

import { InvoiceService } from './invoice-provider'
import { ECPayInvoiceService } from './ecpay-invoice-service'
import { SmilePayInvoiceService } from './smilepay-invoice-service'
import { AmegoInvoiceService } from './amego-service'
import { prisma } from '@/lib/prisma'

type InvoiceProvider = 'ECPAY' | 'SMILEPAY' | 'AMEGO'

export class InvoiceServiceFactory {
    /**
     * 根據服務商名稱取得服務實例
     */
    static getService(
        provider: InvoiceProvider,
        isProd: boolean = false
    ): InvoiceService {
        switch (provider) {
            case 'ECPAY':
                return new ECPayInvoiceService(isProd)
            case 'SMILEPAY':
                return new SmilePayInvoiceService(isProd)
            case 'AMEGO':
                return new AmegoInvoiceService(isProd)
            default:
                throw new Error(`不支援的服務商: ${provider}`)
        }
    }

    /**
     * 根據使用者設定取得服務實例
     */
    static async getServiceForUser(userId: string): Promise<InvoiceService> {
        const settings = await prisma.invoiceSettings.findUnique({
            where: { userId },
        })

        if (!settings || !settings.defaultProvider) {
            throw new Error('未設定預設發票服務商')
        }

        return this.getService(
            settings.defaultProvider as InvoiceProvider,
            settings.isProduction
        )
    }

    /**
     * 取得所有可用的服務商
     */
    static getAvailableProviders(): InvoiceProvider[] {
        return ['ECPAY', 'SMILEPAY', 'AMEGO']
    }
}
```

---

### 範例 5: 金額計算輔助函數

**Claude 提示詞：**
```
建立金額計算工具，自動處理 B2C/B2B 差異
```

**生成的程式碼：**

```typescript
// lib/utils/invoice-amounts.ts

export interface InvoiceAmounts {
    salesAmount: number      // 銷售額（B2C=含稅，B2B=未稅）
    taxAmount: number        // 稅額（B2C=0，B2B=5%）
    totalAmount: number      // 總計
}

/**
 * 計算發票金額
 * @param totalAmount 含稅總額
 * @param isB2B 是否為 B2B 發票
 */
export function calculateInvoiceAmounts(
    totalAmount: number,
    isB2B: boolean
): InvoiceAmounts {
    if (isB2B) {
        // B2B: 分拆未稅金額與稅額
        const taxAmount = Math.round(totalAmount - (totalAmount / 1.05))
        const salesAmount = totalAmount - taxAmount

        return {
            salesAmount,
            taxAmount,
            totalAmount,
        }
    } else {
        // B2C: 含稅價，稅額為 0
        return {
            salesAmount: totalAmount,
            taxAmount: 0,
            totalAmount,
        }
    }
}

/**
 * 計算商品明細金額
 */
export function calculateProductAmounts(
    items: Array<{ price: number; quantity: number }>,
    isB2B: boolean
) {
    const total = items.reduce((sum, item) => {
        return sum + (item.price * item.quantity)
    }, 0)

    return calculateInvoiceAmounts(total, isB2B)
}

/**
 * 驗證金額計算是否正確
 */
export function validateAmounts(amounts: InvoiceAmounts): boolean {
    const calculated = amounts.salesAmount + amounts.taxAmount
    return Math.abs(calculated - amounts.totalAmount) < 0.01
}

// 使用範例
const amounts = calculateInvoiceAmounts(1050, true)
console.log(amounts)
// { salesAmount: 1000, taxAmount: 50, totalAmount: 1050 }

const isValid = validateAmounts(amounts)
console.log('金額驗證:', isValid ? '[PASS]' : '[FAIL]')
```

---

## 實戰場景

### 場景 1: 電商結帳流程整合

**需求：** 用戶結帳時自動開立發票

```typescript
// app/api/checkout/route.ts

import { InvoiceServiceFactory } from '@/lib/services/invoice-service-factory'
import { calculateInvoiceAmounts } from '@/lib/utils/invoice-amounts'

export async function POST(request: Request) {
    const data = await request.json()
    const { userId, orderId, cartItems, buyerInfo } = data

    // 1. 計算訂單金額
    const totalAmount = cartItems.reduce((sum, item) => {
        return sum + (item.price * item.quantity)
    }, 0)

    // 2. 判斷是否為 B2B
    const isB2B = Boolean(buyerInfo.taxId)

    // 3. 計算發票金額
    const amounts = calculateInvoiceAmounts(totalAmount, isB2B)

    // 4. 取得發票服務
    const invoiceService = await InvoiceServiceFactory.getServiceForUser(userId)

    // 5. 開立發票
    const invoiceResult = await invoiceService.issueInvoice(userId, {
        OrderId: orderId,
        TotalAmount: amounts.totalAmount,
        SalesAmount: amounts.salesAmount,
        TaxAmount: amounts.taxAmount,
        IsB2B: isB2B,
        BuyerIdentifier: buyerInfo.taxId || '0000000000',
        BuyerName: buyerInfo.name,
        BuyerEmail: buyerInfo.email,
        ProductItem: cartItems.map(item => ({
            Description: item.name,
            Quantity: item.quantity,
            UnitPrice: isB2B ? Math.round(item.price / 1.05) : item.price,
            Amount: isB2B
                ? Math.round((item.price * item.quantity) / 1.05)
                : item.price * item.quantity,
        })),
    })

    // 6. 儲存發票資訊
    if (invoiceResult.success) {
        await prisma.order.update({
            where: { id: orderId },
            data: {
                invoiceNo: invoiceResult.invoiceNumber,
                invoiceRandomNum: invoiceResult.randomNumber,
                invoiceDate: new Date(),
            },
        })
    }

    return Response.json({
        success: invoiceResult.success,
        invoiceNumber: invoiceResult.invoiceNumber,
    })
}
```

---

### 場景 2: 批次開立發票

**需求：** 每天凌晨批次處理未開發票的訂單

```typescript
// scripts/batch-issue-invoices.ts

import { prisma } from '@/lib/prisma'
import { InvoiceServiceFactory } from '@/lib/services/invoice-service-factory'

async function batchIssueInvoices() {
    console.log('開始批次開立發票...')

    // 查詢未開發票的訂單
    const pendingOrders = await prisma.order.findMany({
        where: {
            status: 'PAID',
            invoiceNo: null,
        },
        include: {
            user: true,
            items: true,
        },
    })

    console.log(`找到 ${pendingOrders.length} 筆待開立發票`)

    let successCount = 0
    let failCount = 0

    for (const order of pendingOrders) {
        try {
            const service = await InvoiceServiceFactory.getServiceForUser(
                order.userId
            )

            const result = await service.issueInvoice(order.userId, {
                OrderId: order.id,
                TotalAmount: order.totalAmount,
                IsB2B: Boolean(order.buyerTaxId),
                BuyerIdentifier: order.buyerTaxId || '0000000000',
                BuyerName: order.buyerName,
                BuyerEmail: order.buyerEmail,
                ProductItem: order.items.map(item => ({
                    Description: item.productName,
                    Quantity: item.quantity,
                    UnitPrice: item.price,
                    Amount: item.price * item.quantity,
                })),
            })

            if (result.success) {
                await prisma.order.update({
                    where: { id: order.id },
                    data: {
                        invoiceNo: result.invoiceNumber,
                        invoiceRandomNum: result.randomNumber,
                        invoiceDate: new Date(),
                    },
                })

                successCount++
                console.log(`[OK] ${order.id} 開立成功`)
            } else {
                failCount++
                console.error(`[ERROR] ${order.id} 開立失敗:`, result.msg)
            }
        } catch (error) {
            failCount++
            console.error(`[ERROR] ${order.id} 發生錯誤:`, error)
        }

        // 避免 API 限流，間隔 1 秒
        await new Promise(resolve => setTimeout(resolve, 1000))
    }

    console.log('\n批次開立完成:')
    console.log(`- 成功: ${successCount} 筆`)
    console.log(`- 失敗: ${failCount} 筆`)
}

// 執行
batchIssueInvoices().catch(console.error)
```

---

## 常見錯誤與修正

### 錯誤 1: 金額計算錯誤

**錯誤訊息：** `ECPay 10000016: 金額計算錯誤`

**原因：** B2B 發票使用含稅價

**修正前：**
```typescript
const result = await service.issueInvoice(userId, {
    IsB2B: true,
    TotalAmount: 1050,
    SalesAmount: 1050,  // 錯誤：應為未稅
    TaxAmount: 0,       // 錯誤：應為 50
})
```

**修正後：**
```typescript
const totalAmount = 1050
const taxAmount = Math.round(totalAmount - (totalAmount / 1.05))
const salesAmount = totalAmount - taxAmount

const result = await service.issueInvoice(userId, {
    IsB2B: true,
    TotalAmount: totalAmount,    // 1050
    SalesAmount: salesAmount,    // 1000
    TaxAmount: taxAmount,        // 50
})
```

### 錯誤 2: 列印時查詢不到發票

**錯誤訊息：** `發票不存在`

**原因：** 使用錯誤的服務商查詢

**修正前：**
```typescript
// 使用當前預設服務商
const service = await InvoiceServiceFactory.getServiceForUser(userId)
const result = await service.printInvoice(userId, invoiceNo)
```

**修正後：**
```typescript
// 使用開立時的服務商
const record = await prisma.financialRecord.findUnique({
    where: { invoiceNo }
})

const service = InvoiceServiceFactory.getService(record.invoiceProvider)
const result = await service.printInvoice(userId, invoiceNo)
```

---

## ezPay 簡單付範例

ezPay 是藍新金流集團旗下發票服務，與藍新 Newebpay 金流共用同一套加密邏輯（AES-256-CBC + Hex + PKCS7 Padding + SHA256 CheckCode），但發票端與金流端的 HashKey/HashIV 為**獨立**金鑰。

### 完整 Python 範例
請見 [`examples/ezpay-invoice-example.py`](examples/ezpay-invoice-example.py) — 涵蓋 B2C / B2B 開立、作廢、折讓、查詢、`Api_invoice_touch` 觸發列印。

### 五大踩坑

1. **HashKey 是 32 碼**，與 ECPay 16 碼不同。HashIV 仍是 16 碼。
2. **欄位名稱有 `_`**：`MerchantID_` 與 `PostData_` 後綴底線**不可省略**，否則會被當成缺少參數。
3. **加密輸出是 Hex 不是 Base64**：與 ECPay 的 Base64 不同。Hex 字串小寫即可。
4. **作廢折讓端點是 camelCase**：`/Api_allowanceInvalid`（不是 `/Api_allowance_invalid`）。其他端點都是 snake_case，這是 ezPay 唯一的例外。
5. **沒有 Webhook**：開立成功只能依靠同步回應。如需狀態通知，須自行排程定時呼叫 `/Api_invoice_search`。

### 開立 B2C 發票（最小範例）

```python
from ezpay_invoice_example import EzpayInvoiceService, InvoiceIssueData

svc = EzpayInvoiceService(
    merchant_id='YOUR_MERCHANT_ID',
    hash_key='YOUR_HASH_KEY_32_CHARS',
    hash_iv='YOUR_HASH_IV_16C',
    is_test=True,
)

resp = svc.issue_invoice(InvoiceIssueData(
    merchant_order_no='ORD20260507001',
    category='B2C',
    buyer_name='王小明',
    buyer_email='test@example.com',
    amt=1000, tax_amt=50, total_amt=1050,
    item_name='測試商品', item_count='1',
    item_unit='個', item_price='1050', item_amt='1050',
))
print(resp.invoice_number, resp.random_num)
```

---

## PayNow 立吉富範例 (preliminary)

> ⚠️ PayNow 公開技術文件較稀疏，下方端點與欄位有部分為合理推測。串接前請向 `einvoice@paynow.com.tw` 索取官方 Invoice Management v1.5 PDF。詳見 [`references/PAYNOW_API_REFERENCE.md`](references/PAYNOW_API_REFERENCE.md) 中列出的 12 項待確認項目。

### 完整 Python 範例
請見 [`examples/paynow-invoice-example.py`](examples/paynow-invoice-example.py) — 涵蓋一般串接（External）的開立 / 作廢 / 折讓，以及 POS 機批次取號流程。

### 三大要點

1. **認證用 JWT Bearer Token**：與其他四家發票服務商（ECPay/SmilePay/Amego/ezPay 都用 HashKey/HashIV）完全不同。需向 PayNow 申請商家 JWT-Token。
2. **POS 流程的「次期單數月 5 號自動上傳空白發票」陷阱**：批次取號後若該期未開立完，剩餘號碼會在次期單數月（1/3/5/7/9/11 月之次月）的 5 號被自動上傳為空白發票。商家若需重新使用須事先取消。
3. **金流與發票兩套加密模型**：PayNow 金流端用動態 AES-256（每呼叫透過 GP/GK 檢核碼即時取得 Key/IV），發票端用靜態 JWT。**不要混用**。

### 開立 B2C 發票（最小範例）

```python
from paynow_invoice_example import PayNowInvoiceService, InvoiceIssueData

svc = PayNowInvoiceService(jwt_token='YOUR_JWT', is_test=True)

resp = svc.issue_invoice(InvoiceIssueData(
    merchant_trade_no='ORD20260507001',
    buyer_name='王小明',
    buyer_email='test@example.com',
    sales_amount=1050, total_amount=1050,
    items=[{'ItemName': '測試商品', 'ItemCount': 1, 'ItemPrice': 1050, 'ItemAmount': 1050, 'ItemUnit': '個'}],
))
print(resp.invoice_no, resp.random_number)
```

---

**更多範例持續更新中...**
