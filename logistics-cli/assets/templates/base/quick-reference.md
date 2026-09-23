## When to Apply

Reference these guidelines when:
- Developing Taiwan Logistics integration
- Integrating ECPay, NewebPay, or PAYUNi logistics aggregator APIs
- Implementing CVS pickup (7-11 / 全家 / 萊爾富 / OK)
- Implementing home delivery (黑貓宅急便 / 宅配通)
- Embedding store-map (LogisticsMap / LogisticsEmap) selectors
- Handling COD orders, shipment tracking, or return-to-store flows

## Provider Quick Reference

| Priority | Task | Impact | Provider |
|----------|------|--------|----------|
| 1 | Logistics Type Routing (B2C vs C2C) | CRITICAL | All |
| 2 | Store-Map Iframe Integration | CRITICAL | CVS |
| 3 | Signature Verification | CRITICAL | All |
| 4 | Shipment Status Callbacks | HIGH | All |
| 5 | COD Amount Limits | HIGH | CVS |
| 6 | Return-to-Store Flow | MEDIUM | C2C |
| 7 | Cold-Chain Routing | MEDIUM | TCAT/SmilePay |

## Quick Reference

### 1. Logistics Type (CRITICAL)

- `b2c-bulk` - 大宗寄倉: merchant ships to logistics center -> stores
- `c2c-store-to-store` - 店到店: merchant drops at CVS -> pickup CVS
- `home-delivery` - 宅配到府: courier to address (TCAT, 宅配通)
- `tcat-temperatures` - 黑貓: 常溫 / 冷藏 / 冷凍 are separate API channels
- `b2c-amount-cap` - CVS B2C cap: NT$20,000; C2C cap: NT$6,000 (varies)

### 2. Store-Map Selection (CRITICAL)

- `iframe-redirect` - LogisticsMap returns selected store via callback URL
- `temp-var` - Use `tempvar` to round-trip session state through map
- `mobile-vs-web` - Some providers offer separate MOBILE / WEB map endpoints
- `store-id-format` - Each provider uses different store ID format (verify on callback)

### 3. Signature Verification (CRITICAL)

- `ecpay-checkmacvalue` - ECPay logistics: **MD5** CheckMacValue (payment is SHA256); case-insensitive sort, PHP urlencode (space = `+`), lowercase, restore `( ) ! * - _ .`
- `newebpay-hashdata` - NewebPay logistics: HashData = SHA256(`HashKey={key}&{EncryptData}&HashIV={iv}`) UPPER; request fields end with `_`, responses do not
- `payuni-hashinfo` - PAYUNi: EncryptInfo = hex( base64(ciphertext) + `:::` + base64(tag) ); HashInfo = SHA256(HashKey + EncryptInfo + HashIV)
- `verify-on-notify` - ALWAYS verify before updating order state

### 4. Status Callbacks (HIGH)

- `numeric-status-codes` - Status uses numeric codes (e.g., 21 待出貨, 31 配送中, 11 已取貨)
- `payuni-status-codes` - PAYUNi ShipStatus codes defined by the production plugin: 21/22/92/31/32/11 (others: read ShipStatusDesc)
- `idempotent-callback` - Treat duplicate notify as no-op
- `cvs-store-relocation` - Code 81 門市關轉: pickup store closed, customer must re-pick

### 5. Common Pitfalls

- `merchant-trade-no-len` - ECPay MerchantTradeNo and Order IDs have length caps
- `cod-must-set-amount` - COD orders require IsCollection=Y + correct amount field
- `cold-chain-separate` - 冷藏/冷凍 use separate ShipmentMethod codes from 常溫
- `https-callback` - All ServerReplyURL / ServerNotifyURL must use HTTPS
- `tempvar-encoding` - `tempvar` must be URL-safe; some providers truncate at 50 chars

## Test Credentials

| Provider | Key Info |
|----------|----------|
| ECPay | MerchantID `2000132`, sandbox `logistics-stage.ecpay.com.tw` |
| NewebPay | Apply via merchant backend (sandbox: `ccore.newebpay.com/API/Logistic`) |
| PAYUNi | Apply via merchant backend (sandbox: `sandbox-api.payuni.com.tw/api/logistics/trade`, T-Cat `/api/home_delivery/trade`, Version 1.1) |

## How to Use

See the full skill documentation for detailed API references and code examples.

---
