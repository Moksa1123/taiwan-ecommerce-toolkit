## When to Apply

Reference these guidelines when:
- Developing Taiwan E-Invoice issuance functionality
- Integrating ECPay, SmilePay, Amego, ezPay, PayNow, O'Pay or SunPay invoice APIs
- Querying the MOF E-Invoice platform (mobile barcode / donation code / winning numbers)
- Implementing B2C or B2B invoice logic
- Handling invoice printing, void, and allowance
- Troubleshooting invoice API integration issues

## Provider Quick Reference

| Priority | Task | Impact | Provider |
|----------|------|--------|----------|
| 1 | Amount Calculation | CRITICAL | All |
| 2 | Encryption/Signature | CRITICAL | All |
| 3 | B2B vs B2C Logic | HIGH | All |
| 4 | Print Handling | HIGH | All |
| 5 | Provider Binding | MEDIUM | All |
| 6 | Error Handling | MEDIUM | All |
| 7 | Carrier/Donation | LOW | B2C only |

## Quick Reference

### 1. Amount Calculation (CRITICAL)

- `b2c-tax-inclusive` - B2C uses tax-inclusive total
- `b2b-split-tax` - B2B requires pre-tax + tax split
- `round-tax` - Round tax: `Math.round(total - (total / 1.05))`
- `ecpay-salesamount` - ECPay：B2C `SalesAmount` 是**含稅**總額；B2B `SalesAmount` 是**未稅**，`TotalAmount = SalesAmount + TaxAmount`

### 2. Encryption/Signature (CRITICAL)

- `ecpay-aes` - ECPay: JSON → URL Encode → AES-128-CBC（HashKey/HashIV）→ Base64
- `smilepay-verify` - SmilePay: Grvc + Verify_key params（無加密）
- `amego-md5` - Amego: `md5(data 的 JSON 字串 + time + APP_KEY)`
- `ezpay-aes` - ezPay: AES-256-CBC（32 碼 HashKey）

### 3. B2B vs B2C Logic (HIGH)

- `ecpay-buyer-id` - ECPay B2C：`CustomerIdentifier` 空字串或 8 碼統編，**不是** `0000000000`；B2B 必填
- `amego-buyer-id` - Amego：`BuyerIdentifier` 無統編填 `0000000000`
- `no-carrier-b2b` - B2B: Cannot use carrier or donation
- `validate-taxid` - Validate 8-digit tax ID format

### 4. Print Handling (HIGH)

- `ecpay-print` - ECPay: `/B2CInvoice/InvoicePrint`（AES JSON）回傳 `InvoiceHtml` 網址，1 小時內有效；B2B 用 `/B2BInvoice/InvoicePrint`
- `smilepay-page` - SmilePay: 以 POST／GET 開啟列印頁（網頁模式或 EPSON IP 列印）
- `amego-pdf` - Amego: 回傳 `file_url`（PDF）

### 5. Provider Binding (MEDIUM)

- `save-provider` - Save invoiceProvider when issuing
- `save-random` - Save invoiceRandomNum for printing
- `match-provider` - Use issuing provider for print/void

### 6. Error Handling (MEDIUM)

- `log-raw-response` - Log complete raw response for debugging
- `ecpay-codes` - ECPay: Check RtnCode and RtnMsg
- `smilepay-codes` - SmilePay: Check `Status`
- `amego-codes` - Amego: Check `code` and `msg`
- 錯誤碼對照：`python scripts/search.py "<代碼>" --domain error`

### 7. Carrier/Donation (B2C only)

- `carrier-mobile` - Mobile barcode: /XXXXXXX format
- `carrier-npc` - Natural person certificate
- `donation-code` - Donation: 3-7 digit love code
- `mutual-exclusive` - Carrier and donation are mutually exclusive

## Test Credentials

| Provider | Key Info |
|----------|----------|
| ECPay | MerchantID: 2000132, Stage URL |
| SmilePay | Grvc: SEI1000034, Test Tax ID: 80129529 |
| Amego | Tax ID: 12345678, test@amego.tw |

## How to Use

See the full skill documentation for detailed API references and code examples.

---
