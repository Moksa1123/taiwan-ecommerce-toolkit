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

- `ecpay-checkmacvalue` - ECPay: case-insensitive sort, `HashKey=..&k=v..&HashIV=..`, PHP urlencode (space = `+`), lowercase, restore `( ) ! * - _ .`, SHA256 UPPER (logistics uses MD5)
- `newebpay-tradesha` - NewebPay: SHA256(`HashKey={key}&{TradeInfo}&HashIV={iv}`) UPPER; CheckCode is `HashIV=..&..&HashKey=..` (reversed)
- `payuni-hashinfo` - PAYUNi: SHA256(HashKey + EncryptInfo + HashIV) UPPER — HashKey first, no `HashKey=` prefix
- `verify-on-callback` - ALWAYS verify signature before processing notify

### 2. Encryption (CRITICAL)

- `ecpay-aes` - ECPay invoice: base64(AES-128-CBC(urlencode(json))), JSON body with `RqHeader.Revision=3.0.0`; decrypt with urldecode (`+` = space)
- `newebpay-aes-cbc` - NewebPay: AES-256-CBC, hex output; RespondType=JSON callbacks decrypt to JSON, not a query string
- `payuni-aes-gcm` - PAYUNi: EncryptInfo = hex( base64(ciphertext) + `:::` + base64(tag) ), HashIV used as the 16-byte nonce
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
- `tradeinfo-padding` - NewebPay decrypt must accept padding 1–32 (official plugin pads to 32-byte blocks)
- `payuni-encryptinfo` - PAYUNi EncryptInfo is NOT hex(ciphertext + tag); UPP enables methods with flags (`Credit=1`, `ATM=1`), there is no PayType
- `https-callback` - All ReturnURL / NotifyURL must use HTTPS
- `lowercase-encode` - ECPay CheckMacValue: `encodeURIComponent` gives `%20` for spaces and fails every request with MerchantTradeDate

## Test Credentials

| Provider | Key Info |
|----------|----------|
| ECPay | MerchantID `3002607`, HashKey `pwFHCqoQZGmho4w6`, HashIV `EkRm7iFT261dpevs` |
| NewebPay | Apply via merchant backend (sandbox URL: `https://ccore.newebpay.com/MPG/mpg_gateway`) |
| PAYUNi | Apply via merchant backend (sandbox URL: `https://sandbox-api.payuni.com.tw/api/upp`) |

## How to Use

See the full skill documentation for detailed API references and code examples.

---
