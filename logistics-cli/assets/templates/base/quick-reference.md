## When to Apply

Reference these guidelines when:
- Developing Taiwan Logistics integration
- Integrating ECPay, NewebPay, PAYUNi, SmilePay, PChomePay, PayNow or ezShip logistics APIs, or HCT direct API
- Implementing CVS pickup (7-11 / 全家 / 萊爾富 / OK)
- Implementing home delivery (黑貓宅急便 / 中華郵政)
- Embedding store-map selectors
- Handling COD orders, shipment tracking, or store relocation
- Using on-demand delivery (Lalamove / pandago / Uber Direct)

## Provider Quick Reference

| Priority | Task | Impact | Provider |
|----------|------|--------|----------|
| 1 | Logistics Type Routing (B2C vs C2C) | CRITICAL | All |
| 2 | Signature Verification | CRITICAL | All |
| 3 | Store-Map Integration | CRITICAL | CVS |
| 4 | Shipment Status Callbacks | HIGH | All |
| 5 | COD Amount Limits | HIGH | All |
| 6 | Cold-Chain Parameters | MEDIUM | 7-11 / 全家 / 黑貓 |

## Quick Reference

### 1. Logistics Type (CRITICAL)

- `contract-bound` - B2C（大宗寄倉）與 C2C（店到店）依合約二選一；ECPay B2C 合約只能用 `FAMI`/`UNIMART`/`UNIMARTFREEZE`/`HILIFE`，C2C 只能用 `FAMIC2C`/`UNIMARTC2C`/`HILIFEC2C`/`OKMARTC2C`
- `ok-c2c-only` - ECPay 的 OK 只有 `OKMARTC2C`，沒有 `OKMART`
- `newebpay-b2c-711` - NewebPay `LgsType=B2C` 只有 7-11（`ShipType=1`）；C2C 四大超商 `ShipType` 1–4；沒有宅配
- `ecpay-home` - ECPay `LogisticsType=HOME`（大寫）：`TCAT` 黑貓、`POST` 中華郵政
- `pchomepay-cvs` - PChomePay 只有 `IPL7`/`IPLFM`/`IPLHL`（7-11／全家／萊爾富），無 OK、無宅配
- `ezship-no-711` - ezShip 通路 `TFM`/`TLF`/`TOK`，不含 7-11
- `hct-direct-only` - 收錄的聚合商都沒有新竹物流選項，要用 HCT 只能直連
- 完整對照：`data/logistics-types.csv`（`python scripts/search.py "<關鍵字>" --domain logistics_type`）

### 2. Signature Verification (CRITICAL)

- `ecpay-checkmacvalue` - ECPay logistics: **MD5** CheckMacValue (payment is SHA256); case-insensitive sort, PHP urlencode (space = `+`), lowercase, restore `( ) ! * - _ .`
- `newebpay-hashdata` - NewebPay logistics: HashData = SHA256(`HashKey={key}&{EncryptData}&HashIV={iv}`) UPPER; request fields end with `_`, responses do not
- `payuni-hashinfo` - PAYUNi: EncryptInfo = hex( base64(ciphertext) + `:::` + base64(tag) ); HashInfo = SHA256(HashKey + EncryptInfo + HashIV)
- `paynow-3des` - PayNow logistics: 3DES / ECB / Zero-Padding（不同於 PayNow 金流端）
- `verify-on-notify` - ALWAYS verify before updating order state

### 3. Store-Map (CRITICAL)

- `extra-data` - ECPay / NewebPay 以 `ExtraData` 原值回傳自訂資料（ECPay 200 字、NewebPay 20 字）
- `paynow-frozen-711` - PayNow 7-11 冷凍店到店：地圖用 `Logistic_serviceID=22`，建單固定 `21`

### 4. Status Callbacks (HIGH)

- `provider-specific-codes` - 各家狀態碼不同，查 `data/status-codes.csv`（`--domain status`）
- `payuni-status` - PAYUNi：21 待出貨、92 處理中、22 物流驗收、31 配送中、32 待取貨、11 已取貨、81 門市關轉（需在期限內重選門市）
- `idempotent-callback` - Treat duplicate notify as no-op

### 5. COD Amount Limits (HIGH)

- `ecpay` - 超商 `GoodsAmount` 1–20,000；黑貓代收上限 20,000；中華郵政不可代收
- `newebpay` - 取貨付款／不付款皆 ≤ 20,000
- `pchomepay` - 65–20,000
- `paynow` - 超商 ≤ 20,000、黑貓宅配 ≤ 100,000
- `ezship` - 代收：店配 10–10,000、宅配 10–8,000

### 6. Cold-Chain Parameters (MEDIUM)

- `ecpay` - 超商 `UNIMARTFREEZE`；黑貓 `Temperature` 0001 常溫／0002 冷藏／0003 冷凍（中華郵政只能 0001）
- `payuni` - `GoodsType` 1 常溫／2 冷凍／3 冷藏（冷藏僅黑貓）
- `smilepay` - 黑貓溫層由 `ezcatGetTrackNum.asp` 的 `temperature` 決定
- `paynow` - 冷凍另有產品線 21–24；黑貓 `DeliveryType` 0001–0003

## Test Credentials

| Provider | Key Info |
|----------|----------|
| ECPay | B2C／宅配 `2000132`、C2C `2000933`（金鑰見 SKILL.md），sandbox `logistics-stage.ecpay.com.tw` |
| NewebPay | Apply via merchant backend (sandbox: `ccore.newebpay.com/API/Logistic`) |
| PAYUNi | Apply via merchant backend (sandbox: `sandbox-api.payuni.com.tw/api`) |

## How to Use

See the full skill documentation for detailed API references and code examples.

---
