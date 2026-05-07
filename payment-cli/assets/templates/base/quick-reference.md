## When to Apply

Reference these guidelines when:
- Developing Taiwan Payment Gateway integration
- Integrating ECPay, NewebPay, or PAYUNi payment APIs
- Implementing credit card, ATM virtual account, CVS code, or e-wallet payments
- Verifying CheckMacValue / TradeSha / EncryptInfo signatures
- Troubleshooting payment callbacks, refund flows, or 3D Secure

## Provider Quick Reference

| Priority | Task | Impact | Provider |
|----------|------|--------|----------|
| 1 | Signature Verification | CRITICAL | All |
| 2 | Encryption Implementation | CRITICAL | All |
| 3 | Callback Handling | HIGH | All |
| 4 | Idempotent Order IDs | HIGH | All |
| 5 | HTTPS-only Endpoints | HIGH | All |
| 6 | Refund Flow | MEDIUM | All |
| 7 | 3D Secure / SCA | MEDIUM | Credit card |

## Quick Reference

### 1. Signature Verification (CRITICAL)

- `ecpay-checkmacvalue` - ECPay: alphabetical-sort + lowercase URL encode + SHA256, then UPPER
- `newebpay-tradesha` - NewebPay: HashKey + TradeInfo + HashIV, then SHA256 UPPER
- `payuni-hashinfo` - PAYUNi: EncryptInfo + HashKey + HashIV, then SHA256 UPPER
- `verify-on-callback` - ALWAYS verify signature before processing notify

### 2. Encryption (CRITICAL)

- `ecpay-aes` - ECPay: AES-128-CBC for some endpoints + SHA256 for CheckMacValue
- `newebpay-aes-cbc` - NewebPay: AES-256-CBC + PKCS7 padding, hex output
- `payuni-aes-gcm` - PAYUNi: AES-256-GCM + 16-byte auth tag MUST be appended
- `keep-keys-server-side` - HashKey/HashIV NEVER exposed to frontend

### 3. Order Lifecycle (HIGH)

- `unique-order-id` - Order IDs must be unique to prevent duplicate charges
- `expire-deadline` - ATM and CVS code have configurable expiry
- `idempotent-callback` - Use DB transaction; treat duplicate notify as no-op
- `return-1ok-ecpay` - ECPay expects literal `1|OK` response on notify success

### 4. Refund Flow (MEDIUM)

- `partial-refund` - Most providers support partial refund (within original amount)
- `refund-window` - Each provider has a refund window (e.g., 180 days for credit card)
- `refund-status-poll` - Refunds may be async; poll status or wait for callback

### 5. Common Pitfalls

- `merchanttradeno-len` - ECPay MerchantTradeNo limited to 20 chars
- `tradeinfo-padding` - NewebPay TradeInfo MUST use PKCS7 padding
- `payuni-gcm-tag` - PAYUNi MUST append 16-byte GCM auth tag after ciphertext
- `https-callback` - All ReturnURL / NotifyURL must use HTTPS
- `lowercase-encode` - ECPay CheckMacValue uses .NET-style lowercase URL encode

## Test Credentials

| Provider | Key Info |
|----------|----------|
| ECPay | MerchantID `3002607`, HashKey `pwFHCqoQZGmho4w6`, HashIV `EkRm7iFT261dpevs` |
| NewebPay | Apply via merchant backend (sandbox URL: `https://ccore.newebpay.com/MPG/mpg_gateway`) |
| PAYUNi | Apply via merchant backend (sandbox URL: `https://sandbox-api.payuni.com.tw/api/upp`) |

## How to Use

See the full skill documentation for detailed API references and code examples.

---
