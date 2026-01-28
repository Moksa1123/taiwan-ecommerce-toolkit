## When to Apply

Reference these guidelines when:
- Developing Taiwan E-Invoice issuance functionality
- Integrating ECPay, SmilePay, or Amego APIs
- Implementing B2C or B2B invoice logic
- Handling invoice printing, void, and allowance
- Troubleshooting invoice API integration issues

## Provider Quick Reference

| Priority | Task | Impact | Provider |
|----------|------|--------|----------|
| 1 | Amount Calculation | CRITICAL | All |
| 2 | Encryption/Signature | CRITICAL | All |
| 3 | B2B vs B2C Logic | HIGH | All |
| 4 | Print Response Handling | HIGH | All |
| 5 | Provider Binding | MEDIUM | All |
| 6 | Error Handling | MEDIUM | All |
| 7 | Carrier/Donation | LOW | B2C only |

## Quick Reference

### 1. Amount Calculation (CRITICAL)

- `b2c-tax-inclusive` - B2C uses tax-inclusive total
- `b2b-split-tax` - B2B requires pre-tax + tax split
- `round-tax` - Round tax: `Math.round(total - (total / 1.05))`
- `salesamount` - ECPay/Amego: Use SalesAmount for pre-tax

### 2. Encryption/Signature (CRITICAL)

- `ecpay-aes` - ECPay: AES-128-CBC with HashKey/HashIV
- `smilepay-verify` - SmilePay: Grvc + Verify_key params
- `amego-md5` - Amego: MD5(data + time + appKey)
- `url-encode` - Always URL encode before encryption

### 3. B2B vs B2C Logic (HIGH)

- `buyer-id-b2c` - B2C: BuyerIdentifier = "0000000000"
- `buyer-id-b2b` - B2B: BuyerIdentifier = actual 8-digit tax ID
- `no-carrier-b2b` - B2B: Cannot use carrier or donation
- `validate-taxid` - Validate 8-digit tax ID format

### 4. Print Response Handling (HIGH)

- `ecpay-html` - ECPay: Returns HTML, use window.document.write
- `smilepay-redirect` - SmilePay: Returns URL, use window.open
- `amego-pdf` - Amego: Returns PDF URL, use window.open
- `form-submit` - Some APIs require form POST submission

### 5. Provider Binding (MEDIUM)

- `save-provider` - Save invoiceProvider when issuing
- `save-random` - Save invoiceRandomNum for printing
- `match-provider` - Use issuing provider for print/void

### 6. Error Handling (MEDIUM)

- `log-raw-response` - Log complete raw response for debugging
- `ecpay-codes` - ECPay: Check RtnCode and RtnMsg
- `smilepay-codes` - SmilePay: Check Status field
- `amego-codes` - Amego: Check Code and Message

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

