# {{TITLE}}

> {{DESCRIPTION}}

## Quick Navigation

### Related Documents
When using this skill, refer to the API reference documents in the project:
- `references/ECPAY_API_REFERENCE.md` - ECPay API Specification
- `references/SMILEPAY_API_REFERENCE.md` - SmilePay API Specification
- `references/AMEGO_API_REFERENCE.md` - Amego API Specification
- [EXAMPLES.md](EXAMPLES.md) - Code Examples

### When to Use This Skill
- Developing e-invoice issuance functionality
- Integrating Taiwan E-Invoice provider APIs
- Implementing B2C or B2B invoices
- Handling invoice printing, void, and allowance
- Processing encryption/signatures (AES, MD5)
- Troubleshooting invoice API integration issues

## Invoice Types

### B2C Invoice (Two-Part)
- Buyer without tax ID
- `BuyerIdentifier` = `0000000000`
- Amount is **tax-inclusive**
- Can use carrier or donation
- Example: General consumer purchase

### B2B Invoice (Three-Part)
- Buyer has 8-digit tax ID
- `BuyerIdentifier` = actual tax ID (validate format)
- Amount is **pre-tax**, requires separate tax calculation
- **Cannot** use carrier or donation
- Example: Company purchase

## Provider Comparison

| Feature | ECPay | SmilePay | Amego |
|---------|-------|----------|-------|
| Test/Prod URL | Different URLs | Different URLs | **Same URL** |
| Authentication | AES encryption + HashKey/HashIV | Grvc + Verify_key | MD5 signature + App Key |
| Print Method | POST form submit | GET URL params | API returns PDF URL |
| B2B Amount Field | SalesAmount (pre-tax) | UnitTAX=N | DetailVat=0 |
| Transport Format | JSON (AES encrypted) | URL Parameters | JSON (URL Encoded) |

## Implementation Steps

### 1. Service Architecture

Create services following this structure:

```typescript
// lib/services/invoice-provider.ts - Interface definition
export interface InvoiceService {
    issueInvoice(userId: string, data: InvoiceIssueData): Promise<InvoiceIssueResponse>
    voidInvoice(userId: string, invoiceNumber: string, reason: string): Promise<InvoiceVoidResponse>
    printInvoice(userId: string, invoiceNumber: string): Promise<InvoicePrintResponse>
}

// lib/services/{provider}-invoice-service.ts - Provider implementation
export class ECPayInvoiceService implements InvoiceService {
    private async encryptData(data: any, hashKey: string, hashIV: string): Promise<string> {
        // AES-128-CBC encryption implementation
    }

    async issueInvoice(userId: string, data: InvoiceIssueData) {
        // 1. Get user settings
        // 2. Prepare API data
        // 3. Encrypt and sign
        // 4. Send request
        // 5. Decrypt response
        // 6. Return standard format
    }
}
```

### 2. Amount Calculation

**Tax-inclusive total -> Pre-tax amount + Tax:**

```typescript
function calculateInvoiceAmounts(totalAmount: number, isB2B: boolean) {
    if (isB2B) {
        // B2B: Need to split tax
        const taxAmount = Math.round(totalAmount - (totalAmount / 1.05))
        const salesAmount = totalAmount - taxAmount
        return { salesAmount, taxAmount, totalAmount }
    } else {
        // B2C: Tax-inclusive total
        return { salesAmount: totalAmount, taxAmount: 0, totalAmount }
    }
}

// Example
const amounts = calculateInvoiceAmounts(1050, true)
// { salesAmount: 1000, taxAmount: 50, totalAmount: 1050 }
```

### 3. Encryption Implementation

**ECPay - AES Encryption:**

```typescript
import crypto from 'crypto'

function encryptECPay(data: object, hashKey: string, hashIV: string): string {
    // 1. Convert JSON to string and URL encode
    const jsonString = JSON.stringify(data)
    const urlEncoded = encodeURIComponent(jsonString)

    // 2. AES-128-CBC encryption
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

**Amego - MD5 Signature:**

```typescript
function generateAmegoSign(data: object, time: number, appKey: string): string {
    const dataString = JSON.stringify(data)
    const signString = dataString + time + appKey
    return crypto.createHash('md5').update(signString).digest('hex')
}
```

### 4. Provider Binding

**Key: When issuing invoice, must record the provider used so printing can call the correct one**

```typescript
// Save provider when issuing
await prisma.financialRecord.update({
    where: { id: recordId },
    data: {
        invoiceNo: result.invoiceNumber,
        invoiceProvider: actualProvider,  // 'ECPAY' | 'SMILEPAY' | 'AMEGO'
        invoiceRandomNum: result.randomNumber, // **Important**: needed for printing
        invoiceDate: new Date(),
    }
})

// Use the issuing provider when printing
const service = record.invoiceProvider
    ? InvoiceServiceFactory.getService(record.invoiceProvider)
    : await InvoiceServiceFactory.getServiceForUser(userId)
```

### 5. Print Response Handling

Frontend needs to handle based on response type:

```typescript
// Backend response format
interface InvoicePrintResponse {
    success: boolean
    type?: 'html' | 'redirect' | 'form'
    htmlContent?: string      // ECPay
    printUrl?: string          // SmilePay/Amego
    formUrl?: string
    formParams?: Record<string, string>
}

// Frontend handling example
if (result.type === 'html') {
    const win = window.open('', '_blank')
    win.document.write(result.htmlContent)
} else if (result.type === 'redirect') {
    window.open(result.url, '_blank')
} else if (result.type === 'form') {
    // Dynamically create form submission
    const form = document.createElement('form')
    form.method = 'POST'
    form.action = result.formUrl
    form.target = '_blank'
    // ... add parameters
    form.submit()
}
```

## Common Issues

### Issue 1: Invoice issuance failed with unclear error

**Diagnostic steps:**
1. Check logger output for complete error in `raw` field
2. Confirm environment variables (test/prod) are correct
3. Verify required fields are complete

**ECPay common errors:**
- `10000006`: RelateNumber duplicate -> Order number already used
- `10000016`: Amount calculation error -> Check B2C/B2B calculation
- `10000019`: Cannot use carrier with tax ID -> Remove CarrierType

**SmilePay common errors:**
- `-10066`: AllAmount validation error -> Check if TotalAmount was sent
- `-10084`: orderid format error -> Limit to 30 characters
- `-10053`: Carrier number error -> Validate mobile barcode format

**Amego common errors:**
- `1002`: OrderId already exists -> Use unique order number
- `1007`: Amount calculation error -> Check DetailVat setting
- `1012`: B2B invoice cannot use carrier or donation

### Issue 2: Print shows "Invoice not found"

**Solution:**
Confirm `invoiceProvider` field is saved correctly, use the issuing provider when printing.

```typescript
// Correct: Use provider from invoice record
const service = record.invoiceProvider
    ? InvoiceServiceFactory.getService(record.invoiceProvider)
    : await InvoiceServiceFactory.getServiceForUser(userId)

// Incorrect: Use user's current default provider
const service = await InvoiceServiceFactory.getServiceForUser(userId)
```

### Issue 3: B2B invoice amount error

**Amount fields by provider:**

```typescript
// ECPay
const b2bData = {
    SalesAmount: 1000,      // Pre-tax sales
    TaxAmount: 50,          // Tax
    TotalAmount: 1050,      // Total
    ItemPrice: 100,         // Item unit price (pre-tax)
    ItemAmount: 1000,       // Item subtotal (pre-tax)
    ItemTax: 50             // Item tax
}

// SmilePay
const b2bData = {
    AllAmount: '1050',      // Tax-inclusive total
    SalesAmount: '1000',    // Pre-tax sales (optional but recommended)
    TaxAmount: '50',        // Tax (optional)
    UnitTAX: 'N',           // **Important**: Unit price is pre-tax
    UnitPrice: '100',       // Item unit price (pre-tax)
    Amount: '1000'          // Item subtotal (pre-tax)
}

// Amego
const b2bData = {
    DetailVat: 0,           // **Important**: 0=pre-tax
    SalesAmount: 1000,      // Pre-tax sales
    TaxAmount: 50,          // Tax
    TotalAmount: 1050,      // Total
    ProductItem: [{
        UnitPrice: 100,     // Item unit price (pre-tax)
        Amount: 1000        // Item subtotal (pre-tax)
    }]
}
```

### Issue 4: SmilePay print blank

**Cause:** Using `type: 'form'` when response has `method: 'GET'`

**Solution:**
```typescript
// Correct
if (printData.method === 'GET' && printData.url) {
    return { type: 'redirect', url: printData.url }
}

// Incorrect
return { type: 'form', url: printData.url, params: printData.params }
```

### Issue 5: Timestamp expired

**ECPay error 10000005:** Timestamp exceeds 10 minutes

**Solution:**
```typescript
// Ensure using current timestamp
const timestamp = Math.floor(Date.now() / 1000)

// Amego: tolerance is +/- 60 seconds
const time = Math.floor(Date.now() / 1000)
```

## Test Accounts

### ECPay Test Environment
```
MerchantID: 2000132
HashKey: ejCk326UnaZWKisg
HashIV: q9jcZX8Ib9LM8wYk
URL: https://einvoice-stage.ecpay.com.tw
```

### SmilePay Test Environment
```
Grvc: SEI1000034
Verify_key: 9D73935693EE0237FABA6AB744E48661
Test Tax ID: 80129529
URL: https://ssl.smse.com.tw/api_test/SPEinvoice_Storage.asp
```

### Amego Test Environment
```
Tax ID: 12345678
App Key: sHeq7t8G1wiQvhAuIM27
Admin: https://invoice.amego.tw/
Test Account: test@amego.tw
Test Password: 12345678
```

## Development Checklist

Use this checklist to ensure complete implementation:

- [ ] Implement `InvoiceService` interface
- [ ] Handle B2C / B2B amount calculation differences
- [ ] Implement encryption/signature mechanism (AES or MD5)
- [ ] Save `invoiceProvider` field
- [ ] Save `invoiceRandomNum` (needed for printing)
- [ ] Handle print response types (html/redirect/form)
- [ ] Implement error handling and logging
- [ ] Test environment verification
- [ ] Handle carrier and donation mutual exclusion
- [ ] Validate tax ID format (8-digit number)

## Adding New Provider

1. Create `{provider}-invoice-service.ts` in `lib/services/`
2. Implement all methods of `InvoiceService` interface
3. Register new provider in `InvoiceServiceFactory`
4. Add option to `InvoiceProvider` enum in `prisma/schema.prisma`
5. Run `prisma migrate` or `prisma db push`
6. Update frontend settings page (`app/settings/invoice/page.tsx`)
7. Write unit tests

## References

For detailed API specifications, see the `references/` directory:
- [ECPay API Specification](./references/ECPAY_API_REFERENCE.md)
- [SmilePay API Specification](./references/SMILEPAY_API_REFERENCE.md)
- [Amego API Specification](./references/AMEGO_API_REFERENCE.md)

---

Last updated: 2026/01/28
