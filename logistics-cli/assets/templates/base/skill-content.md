# {{TITLE}}

> {{DESCRIPTION}}

**Comprehensive guide for Taiwan Logistics integration (ECPay, NewebPay, PAYUNi, SmilePay, PChomePay, PayNow + HCT direct API)**

---

## Supported Providers

This skill covers **6 logistics aggregators** + **1 direct carrier API**:

| Provider | 類型 | Reference |
|---|---|---|
| **ECPay 綠界** | aggregator | `references/ecpay-logistics-api.md` |
| **NewebPay 藍新** | aggregator | `references/NEWEBPAY_LOGISTICS_REFERENCE.md` |
| **PAYUNi 統一** | aggregator | `references/payuni-logistics-api.md` |
| **SmilePay 速買配** | aggregator (含 7-11/全家 + 黑貓 Pay_zg 矩陣) | `references/smilepay-logistics-api.md` |
| **PChomePay 拍錢包** | aggregator (金物流二合一) | `references/pchomepay-logistics-api.md` |
| **PayNow 立吉富** | aggregator (11 條產品線, 3DES/ECB/Zero-Padding) | `references/paynow-logistics-api.md` |
| **HCT 新竹物流** | **直連 carrier API** | `references/hct-logistics-api.md` |

> 註：選用 `HCT 直連 API` 適合大量出貨企業；一般電商透過 aggregator (`LogisticsType=HCT`) 走 HCT 配送即可，不需自行串接。

---

## Quick Reference

### Core Concepts

**Logistics Types:**
- **B2C (大宗寄倉)**: Bulk warehouse shipping - Merchant ships to logistics center, then distributed to stores
- **C2C (店到店)**: Store-to-store - Merchant ships to convenience store, then delivered to pickup store

**Trade Types:**
- **取貨付款 (Cash on Delivery)**: Customer pays when picking up
- **取貨不付款 (No Payment)**: Customer only picks up (payment already completed)

**Supported Convenience Stores:**
1. 7-ELEVEN
2. FamilyMart (全家)
3. Hi-Life (萊爾富)
4. OK Mart

**Key APIs:**
1. Store Map Query - Select pickup/sender store
2. Create Shipment - Create logistics order
3. Get Shipment Number - Get shipping code
4. Print Label - Print shipping label
5. Query Shipment - Check order status
6. Modify Shipment - Update order details
7. Track Shipment - Track delivery history
8. Status Notification - Real-time status updates

---

## Service Providers

### NewebPay Logistics (藍新物流)

**Encryption**: AES-256-CBC + SHA256 (same as NewebPay payment)

**API Style**: Form POST with AES encryption

**Supported Services:**
- C2C Store-to-Store: 4 convenience stores (7-11, FamilyMart, Hi-Life, OK Mart)
- B2C Bulk Warehouse: 7-ELEVEN only

**Test Environment:**
- Store Map: `https://ccore.newebpay.com/API/Logistic/storeMap`
- Create Shipment: `https://ccore.newebpay.com/API/Logistic/createShipment`
- Get Shipment No: `https://ccore.newebpay.com/API/Logistic/getShipmentNo`
- Print Label: `https://ccore.newebpay.com/API/Logistic/printLabel`
- Query Shipment: `https://ccore.newebpay.com/API/Logistic/queryShipment`
- Modify Shipment: `https://ccore.newebpay.com/API/Logistic/modifyShipment`
- Track Shipment: `https://ccore.newebpay.com/API/Logistic/trace`

**Production Environment:**
- Replace `ccore.newebpay.com` with `core.newebpay.com`

---

### ECPay Logistics (綠界物流)

**Encryption**: MD5 CheckMacValue

**API Style**: Form POST with URL-encoded parameters

**Supported Services:**
- C2C Store-to-Store: 4 convenience stores (7-11, FamilyMart, Hi-Life, OK Mart)
- C2C Frozen: 7-ELEVEN frozen goods
- Home Delivery: T-Cat, HCT, Pelican Express

**Test Environment:**
- Base URL: `https://logistics-stage.ecpay.com.tw`
- Create: `POST /Express/Create`
- Query: `POST /Helper/QueryLogisticsTradeInfo/V2`
- Print: `POST /helper/printTradeDocument`
- Map: `POST /Express/map`

**Production Environment:**
- Base URL: `https://logistics.ecpay.com.tw`

**Logistics SubTypes (CVS):**
- `FAMI` - FamilyMart (全家)
- `UNIMART` - 7-ELEVEN (常溫)
- `UNIMARTFREEZE` - 7-ELEVEN (冷凍)
- `HILIFE` - Hi-Life (萊爾富)
- `OKMART` - OK Mart

**Logistics SubTypes (Home Delivery):**
- `TCAT` - T-Cat (黑貓宅急便)
- `ECAN` - HCT (新竹物流)
- `POST` - Pelican Express (宅配通)

**Temperature Control (Home Delivery):**
- `0001` - Normal temperature (常溫)
- `0002` - Refrigerated (冷藏)
- `0003` - Frozen (冷凍)

**Specification (Package Size):**
- `0001` - 60cm
- `0002` - 90cm
- `0003` - 120cm
- `0004` - 150cm

**Distance (Delivery Range):**
- `00` - Same district
- `01` - Same city
- `02` - Cross city
- `03` - Outlying islands

**Test Credentials:**
- MerchantID: `2000132`
- HashKey: `5294y06JbISpM5x9`
- HashIV: `v77hoKGq4kWxNNIS`

---

### PAYUNi Logistics (統一物流)

**Encryption**: AES-256-GCM + SHA256 (same as PAYUNi payment):
`EncryptInfo = hex(base64(ciphertext) + ":::" + base64(tag))`, `HashInfo = SHA256(HashKey + EncryptInfo + HashIV)`

**API Style**: form POST (`MerID`, `Version`, `EncryptInfo`, `HashInfo`), JSON response with an encrypted `EncryptInfo`

> Endpoints, fields and codes below follow the production plugin wpbr-payuni-shipping 1.6.4;
> crypto is verified byte-for-byte against the official PAYUNi plugin and PHP SDK.
> Full details: `references/payuni-logistics-api.md`.

**Supported Services:**
- C2C Store-to-Store: 7-ELEVEN (normal temperature + frozen)
- B2C Bulk Warehouse: 7-ELEVEN only
- Home Delivery: T-Cat (normal temperature, frozen, refrigerated)

**Endpoints** (base `https://sandbox-api.payuni.com.tw/api` / `https://api.payuni.com.tw/api`):

| Purpose | Path | Version |
|---|---|---|
| 7-11 store map (browser form) | `/logistics/ship_map` | 1.1 |
| Create 7-11 shipment | `/logistics/trade` | 1.1 |
| Create T-Cat shipment | `/home_delivery/trade` | 1.1 |
| Query shipment | `/logistics/query` | 1.1 |
| Print 7-11 label (browser form) | `/logistics/print_label` | 1.0 |

**Codes:** `ShipType` 1=7-ELEVEN 2=T-Cat · `LgsType` C2C / B2C / HOME · `GoodsType` 1=normal 2=frozen 3=refrigerated ·
`ServiceType` 1=COD 3=no COD · `DeliveryTimeTag` 01 / 02 / 04(not set)

> Strings like `PAYUNi_Logistic_711` are WooCommerce shipping-method IDs of the official plugin, **not** API values.

---

## Transaction Flows

### 1. B2C Bulk Warehouse - Cash on Delivery

1. **Create Order**: Customer selects store, merchant calls Create Shipment API
2. **Get Shipping Code**: Merchant calls Get Shipment Number API & Print Label API
3. **Merchant Ships**: Merchant delivers goods to logistics center
4. **Logistics Distributes**: Logistics center verifies and distributes to pickup store
5. **Customer Picks Up**: Customer picks up and pays, NewebPay notifies merchant

### 2. C2C Store-to-Store - Cash on Delivery

1. **Create Order**: Customer selects store, merchant calls Create Shipment API
2. **Get Shipping Code**: Merchant calls Get Shipment Number API & Print Label API
3. **Merchant Ships**: Merchant delivers goods to sender store
4. **Store Ships**: Sender store ships to logistics center, then to pickup store
5. **Customer Picks Up**: Customer picks up and pays, NewebPay notifies merchant

### 3. B2C Bulk Warehouse - No Payment

1. **Create Order**: Customer selects store (payment already completed)
2. **Get Shipping Code**: Merchant calls Get Shipment Number API & Print Label API
3. **Merchant Ships**: Merchant delivers goods to logistics center
4. **Logistics Distributes**: Logistics center verifies and distributes to pickup store
5. **Customer Picks Up**: Customer picks up, NewebPay notifies merchant

### 4. C2C Store-to-Store - No Payment

1. **Create Order**: Customer selects store (payment already completed)
2. **Get Shipping Code**: Merchant calls Get Shipment Number API & Print Label API
3. **Merchant Ships**: Merchant delivers goods to sender store
4. **Store Ships**: Sender store ships to logistics center, then to pickup store
5. **Customer Picks Up**: Customer picks up, NewebPay notifies merchant

---

## API Operations

### 1. Store Map Query API [NPA-B51]

Query convenience store locations for pickup or sender.

**Endpoint:**
- Test: `https://ccore.newebpay.com/API/Logistic/storeMap`
- Production: `https://core.newebpay.com/API/Logistic/storeMap`

**Request Parameters:**

| Field | Description | Type | Required |
|-------|-------------|------|----------|
| UID_ | Merchant ID | Varchar(15) | V |
| EncryptData_ | Encrypted data | Text | V |
| HashData_ | Hash data | Text | V |
| Version_ | API version | Varchar(5) | V |
| RespondType_ | Response format | Varchar(6) | V |

**EncryptData_ Parameters:**

| Field | Description | Type | Required | Notes |
|-------|-------------|------|----------|-------|
| MerchantOrderNo | Merchant order number | Varchar(30) | V | Unique order ID |
| LgsType | Logistics type | Varchar(15) | V | B2C or C2C |
| ShipType | Logistics provider | Varchar(15) | V | 1=7-11, 2=FamilyMart, 3=Hi-Life, 4=OK Mart |
| ReturnURL | Return URL | Varchar(50) | V | URL after store selection |
| TimeStamp | Unix timestamp | Text | V | Current time in seconds |
| ExtraData | Extra data | Varchar(20) | - | Returned as-is |

**Response EncryptData_ Parameters:**

| Field | Description | Type | Notes |
|-------|-------------|------|-------|
| LgsType | Logistics type | Varchar(15) | B2C or C2C |
| ShipType | Logistics provider | Varchar(15) | 1=7-11, 2=FamilyMart, 3=Hi-Life, 4=OK Mart |
| MerchantOrderNo | Merchant order number | Varchar(30) | Order ID |
| StoreName | Store name | Varchar(10) | Selected store name |
| StoreTel | Store phone | Varchar(12) | Store phone number |
| StoreAddr | Store address | Varchar(100) | Store address |
| StoreID | Store code | Varchar(8) | Store ID (use this for shipment) |
| ExtraData | Extra data | Varchar(20) | Original value returned |

---

### 2. Create Shipment API [NPA-B52]

Create logistics shipment order after payment order is established.

**Endpoint:**
- Test: `https://ccore.newebpay.com/API/Logistic/createShipment`
- Production: `https://core.newebpay.com/API/Logistic/createShipment`

**EncryptData_ Parameters:**

| Field | Description | Type | Required | Notes |
|-------|-------------|------|----------|-------|
| MerchantOrderNo | Merchant order number | Varchar(30) | V | Unique order ID |
| TradeType | Trade type | Int(1) | V | 1=COD, 3=No Payment |
| UserName | Recipient name | Varchar(20) | V | Pickup person name |
| UserTel | Recipient phone | Varchar(10) | V | Mobile number |
| UserEmail | Recipient email | Varchar(50) | V | Email address |
| StoreID | Pickup store ID | Varchar(10) | V | From store map query |
| Amt | Transaction amount | Int(10) | V | Order amount |
| NotifyURL | Notification URL | Varchar(100) | - | Pickup completion callback |
| ItemDesc | Product description | Varchar(100) | - | Product name |
| LgsType | Logistics type | Varchar(3) | V | B2C or C2C |
| ShipType | Logistics provider | Varchar(15) | V | 1=7-11, 2=FamilyMart, 3=Hi-Life, 4=OK Mart |
| TimeStamp | Unix timestamp | Varchar(50) | V | Current time in seconds |

**Response EncryptData_ Parameters:**

| Field | Description | Type | Notes |
|-------|-------------|------|-------|
| MerchantID | Merchant ID | Varchar(15) | NewebPay merchant ID |
| Amt | Transaction amount | Int(10) | Order amount |
| MerchantOrderNo | Merchant order number | Varchar(30) | Order ID |
| TradeNo | NewebPay trade number | Varchar(20) | Platform transaction ID |
| LgsType | Logistics type | Varchar(15) | B2C or C2C |
| ShipType | Logistics provider | Varchar(15) | 1=7-11, 2=FamilyMart, 3=Hi-Life, 4=OK Mart |
| StoreID | Pickup store ID | Varchar(10) | Store code |
| TradeType | Trade type | Int(1) | 1=COD, 3=No Payment |

---

### 3. Get Shipment Number API [NPA-B53]

Get shipping code before shipment. Merchants can print labels at convenience store Kiosk.

**Endpoint:**
- Test: `https://ccore.newebpay.com/API/Logistic/getShipmentNo`
- Production: `https://core.newebpay.com/API/Logistic/getShipmentNo`

**EncryptData_ Parameters:**

| Field | Description | Type | Required | Notes |
|-------|-------------|------|----------|-------|
| MerchantOrderNo | Merchant order numbers | Json_array | V | Max 10 orders at once |
| TimeStamp | Unix timestamp | Varchar(50) | V | Current time in seconds |

**Response EncryptData_ Parameters:**

| Field | Description | Type | Notes |
|-------|-------------|------|-------|
| SUCCESS | Success array | Json_array | Multiple records |
| ERROR | Error array | Json_array | Multiple records |
| MerchantOrderNo | Merchant order number | Varchar(30) | Order ID |
| ErrorCode | Error code | Varchar(20) | SUCCESS or error code |
| LgsNo | Shipment number | Varchar(20) | Logistics tracking number |
| StorePrintNo | Store print code | Varchar(20) | Code for Kiosk printing |
| ShipType | Logistics provider | Varchar(15) | 1=7-11, 2=FamilyMart, 3=Hi-Life, 4=OK Mart |
| LgsType | Logistics type | Varchar(15) | B2C or C2C |

---

### 4. Print Label API [NPA-B54]

Print shipping labels to attach to products.

**Endpoint:**
- Test: `https://ccore.newebpay.com/API/Logistic/printLabel`
- Production: `https://core.newebpay.com/API/Logistic/printLabel`

**Important**: Must use Form POST method (not JSON API call)

**EncryptData_ Parameters:**

| Field | Description | Type | Required | Notes |
|-------|-------------|------|----------|-------|
| LgsType | Logistics type | Varchar(15) | V | B2C or C2C |
| ShipType | Logistics provider | Varchar(15) | V | 1=7-11, 2=FamilyMart, 3=Hi-Life, 4=OK Mart |
| MerchantOrderNo | Merchant order numbers | json_array | V | Max: 7-11(18), FamilyMart(8), Hi-Life(18), OK Mart(18) |
| TimeStamp | Unix timestamp | Varchar(50) | V | Current time in seconds |

**Response**: Returns HTML page with printable shipping label

---

### 5. Query Shipment API [NPA-B55]

Query logistics order information and status.

**Endpoint:**
- Test: `https://ccore.newebpay.com/API/Logistic/queryShipment`
- Production: `https://core.newebpay.com/API/Logistic/queryShipment`

**EncryptData_ Parameters:**

| Field | Description | Type | Required | Notes |
|-------|-------------|------|----------|-------|
| MerchantOrderNo | Merchant order number | Varchar(30) | V | Order ID |
| TimeStamp | Unix timestamp | Varchar(50) | V | Current time in seconds |

**Response EncryptData_ Parameters:**

| Field | Description | Type | Notes |
|-------|-------------|------|-------|
| MerchantID | Merchant ID | Varchar(15) | NewebPay merchant ID |
| LgsType | Logistics type | Varchar(15) | B2C or C2C |
| TradeNo | NewebPay trade number | Varchar(20) | Platform transaction ID |
| MerchantOrderNo | Merchant order number | Varchar(30) | Order ID |
| Amt | Transaction amount | Int(10) | Order amount |
| ItemDesc | Product description | Varchar(100) | Product name |
| NotifyURL | Notification URL | Varchar(50) | Callback URL |
| LgsNo | Shipment number | Varchar(20) | Logistics tracking number |
| StorePrintNo | Store print code | Varchar(20) | Kiosk print code |
| collectionAmt | Collection amount | Int(10) | COD amount |
| TradeType | Trade type | Int(1) | 1=COD, 3=No Payment |
| Type | Order type | Int(1) | 1=Normal, 3=Return |
| ShopDate | Ship date | Date | Shipping date |
| UserName | Recipient name | Varchar(20) | Pickup person |
| UserTel | Recipient phone | Varchar(10) | Mobile number |
| UserEmail | Recipient email | Varchar(50) | Email |
| StoreID | Pickup store ID | Varchar(10) | Store code |
| ShipType | Logistics provider | Varchar(15) | 1=7-11, 2=FamilyMart, 3=Hi-Life, 4=OK Mart |
| StoreName | Store name | Varchar(20) | Store name |
| RetId | Status code | Varchar(10) | See status code table |
| RetString | Status description | Varchar(30) | See status description |

---

### 6. Modify Shipment API [NPA-B56]

Modify shipment order details (only for orders not yet shipped or expired).

**Endpoint:**
- Test: `https://ccore.newebpay.com/API/Logistic/modifyShipment`
- Production: `https://core.newebpay.com/API/Logistic/modifyShipment`

**Modifiable Conditions:**
- Not yet obtained shipping number
- Shipment expired
- Store reselection

**EncryptData_ Parameters:**

| Field | Description | Type | Required | Notes |
|-------|-------------|------|----------|-------|
| MerchantOrderNo | Merchant order number | Varchar(30) | V | Order ID |
| LgsType | Logistics type | Varchar(15) | V | B2C or C2C |
| ShipType | Logistics provider | Varchar(15) | V | 1=7-11, 2=FamilyMart, 3=Hi-Life, 4=OK Mart |
| UserName | Recipient name | Varchar(20) | - | New recipient name |
| UserTel | Recipient phone | Varchar(10) | - | New phone number |
| UserEmail | Recipient email | Varchar(50) | - | New email |
| StoreID | Pickup store ID | Varchar(10) | + | New store ID |
| TimeStamp | Unix timestamp | Varchar(50) | V | Current time in seconds |

**Response EncryptData_ Parameters:**

| Field | Description | Type | Notes |
|-------|-------------|------|-------|
| MerchantID | Merchant ID | Varchar(15) | NewebPay merchant ID |
| MerchantOrderNo | Merchant order number | Varchar(30) | Order ID |
| LgsType | Logistics type | Varchar(15) | B2C or C2C |
| ShipType | Logistics provider | Varchar(15) | 1=7-11, 2=FamilyMart, 3=Hi-Life, 4=OK Mart |

---

### 7. Track Shipment API [NPA-B57]

Track complete logistics delivery history.

**Endpoint:**
- Test: `https://ccore.newebpay.com/API/Logistic/trace`
- Production: `https://core.newebpay.com/API/Logistic/trace`

**EncryptData_ Parameters:**

| Field | Description | Type | Required | Notes |
|-------|-------------|------|----------|-------|
| MerchantOrderNo | Merchant order number | Varchar(30) | V | Order ID |
| TimeStamp | Unix timestamp | Varchar(50) | V | Current time in seconds |

**Response EncryptData_ Parameters:**

| Field | Description | Type | Notes |
|-------|-------------|------|-------|
| LgsType | Logistics type | Varchar(15) | B2C or C2C |
| MerchantOrderNo | Merchant order number | Varchar(30) | Order ID |
| LgsNo | Shipment number | Varchar(20) | Tracking number |
| TradeType | Trade type | Int(1) | 1=COD, 3=No Payment |
| ShipType | Logistics provider | Varchar(15) | 1=7-11, 2=FamilyMart, 3=Hi-Life, 4=OK Mart |
| History | History array | json_array | Tracking history |
| RetId | Status code | Varchar(10) | See status code table |
| RetString | Status description | Varchar(30) | See status description |
| EventTime | Event time | Varchar(20) | Timestamp |

---

### 8. Status Notification [NPA-B58]

Real-time notification when shipment status changes.

**Merchant provides NotifyURL to receive notifications**

**POST Parameters:**

| Field | Description | Type | Notes |
|-------|-------------|------|-------|
| Status | Response status | Varchar(10) | SUCCESS or error code |
| Message | Response message | Varchar(30) | Status description |
| EncryptData_ | Encrypted data | Text | - |
| HashData_ | Hash data | Text | - |
| UID_ | Merchant ID | Varchar(15) | NewebPay merchant ID |
| Version_ | API version | Varchar(5) | Fixed: 1.0 |

**EncryptData_ Parameters:**

| Field | Description | Type | Notes |
|-------|-------------|------|-------|
| LgsType | Logistics type | Varchar(15) | B2C or C2C |
| MerchantOrderNo | Merchant order number | Varchar(30) | Order ID |
| LgsNo | Shipment number | Varchar(20) | Tracking number |
| TradeType | Trade type | Int(1) | 1=COD, 3=No Payment |
| ShipType | Logistics provider | Varchar(15) | 1=7-11, 2=FamilyMart, 3=Hi-Life, 4=OK Mart |
| RetId | Status code | Varchar(10) | See status code table |
| RetString | Status description | Varchar(30) | See status description |
| EventTime | Event time | Varchar(20) | Timestamp |

---

## Encryption Methods

### Hash Data Processing

NewebPay Logistics uses the same encryption method as NewebPay Payment:

1. **AES-256-CBC Encryption**: Encrypt data using merchant's HashKey and HashIV
2. **SHA256 Hash**: `HashKey=` + key + `&` + AES result + `&HashIV=` + iv, then SHA256 and uppercase

**Process:**
```
EncryptData = hex(AES-256-CBC(JSON, HashKey, HashIV))
HashData    = SHA256("HashKey={HashKey}&{EncryptData}&HashIV={HashIV}").toUpperCase()
```

Spec NDNS 1.0.0 appendix (1) gives a worked example:
`SHA256("HashKey=12345678901234567890123456789012&AAAABBBBCCCCDDDD&HashIV=12345678")`
= `5C6C504A2F2B2E3EB5CA80998F626307ACD327AC6DCE4FF84F86B021988B2576`.

Field names: requests use a trailing underscore (`UID_`, `EncryptData_`, `HashData_`, `Version_`, `RespondType_`);
API responses and the store-map callback use `EncryptData` / `HashData` **without** underscore;
the status push (NPA-B58) uses the underscored names.

---

## Status Codes

### RetId Status Codes & RetString Descriptions

| RetId | RetString | Category |
|-------|-----------|----------|
| 0_1 | Order not processed | Pending |
| 0_2 | Shipment number expired, please get new number | Pending |
| 0_3 | Shipment canceled | Pending |
| 1 | Order processing | Processing |
| 2 | Store received shipment | In Transit |
| 3 | Store reselected, waiting for re-shipment | In Transit |
| 4 | Arrived at logistics center | In Transit |
| 11 | Pickup store closed, please reselect | In Transit |
| 5 | Arrived at pickup store | Ready for Pickup |
| 6 | Customer picked up | Completed |
| -1 | Returned to merchant | Completed |
| -6 | Home delivery return requested | Completed |
| -9 | Logistics inspection error | Completed |
| -2 | Returned to sender/designated return store | Return/Compensation |
| -3 | Returned to logistics center | Return/Compensation |
| -4 | Returning to logistics center (customer did not pickup) | Return/Compensation |
| -5 | Soon to be returned (customer did not pickup) | Return/Compensation |
| -7 | Error compensation approved | Return/Compensation |
| -10 | Product destroyed/discarded | Return/Compensation |
| -11 | Product destroyed/discarded | Return/Compensation |
| 10 | Soon to be returned | Return/Compensation |
| 12 | Return store closed, please reselect | Return/Compensation |
| 13 | Returning to logistics center (merchant did not pickup) | Return/Compensation |
| 14 | Please request home delivery return | Return/Compensation |
| 15 | Product destroyed/discarded | Return/Compensation |
| 16 | Please confirm bank account | Return/Compensation |

---

## Error Codes

### Common Error Codes

| Code | Message | Notes |
|------|---------|-------|
| SUCCESS | Success | - |
| 1101 | Failed to create logistics order | - |
| 1102 | Merchant not found | - |
| 1103 | Duplicate merchant order number | - |
| 1104 | Logistics service not enabled | - |
| 1105 | Store information invalid or empty | - |
| 1106 | IP not allowed | - |
| 1107 | Payment order not found | - |
| 1108 | System error, cannot query logistics order | - |
| 1109 | Logistics order not found | - |
| 1110 | System error, cannot modify logistics order | - |
| 1111 | Order status cannot be modified | - |
| 1112 | Failed to modify logistics order | - |
| 1113 | System error, cannot query tracking history | - |
| 1114 | Insufficient prepaid balance | - |
| 1115 | Failed to get shipment number | - |
| 1116 | Shipment already created for this transaction | - |
| 2100 | Data format error | - |
| 2101 | Version error | - |
| 2102 | UID_ cannot be empty | - |
| 2103 | COD amount limit: 20000 NTD | - |
| 2104 | No payment amount limit: 20000 NTD | - |
| 2105 | Max 10 shipment numbers per request | - |
| 2106 | Max labels per request: 7-11(18), FamilyMart(8), Hi-Life(18), OK Mart(18) | - |
| 4101 | IP restricted | - |
| 4103 | HashData_ verification failed | - |
| 4104 | Encryption error, check Hash_Key and Hash_IV | - |

---

## Important Notes

### Amount Limits
- **COD (Cash on Delivery)**: Maximum 20,000 NTD
- **No Payment**: Maximum 20,000 NTD

### Batch Limits
- **Get Shipment Number**: Maximum 10 orders per request
- **Print Label**:
  - 7-ELEVEN: Maximum 18 labels
  - FamilyMart: Maximum 8 labels
  - Hi-Life: Maximum 18 labels
  - OK Mart: Maximum 18 labels

### Store Code Notes
- For FamilyMart and OK Mart, the store code displayed on the map may not be the real code
- Always use the store code returned in the API response (StoreID field)

### Timestamp
- Must use Unix timestamp (seconds since 1970-01-01 00:00:00 GMT)
- Tolerance: 120 seconds
- Incorrect timestamp will cause transaction failure

---

## PAYUNi API Operations

All requests: form POST `MerID`, `Version`, `EncryptInfo`, `HashInfo`. Verify `HashInfo` on every
response and notification before decrypting.

### 1. Create shipment

`POST /api/logistics/trade` (7-11) or `POST /api/home_delivery/trade` (T-Cat), Version `1.1`.

| EncryptInfo field | 7-11 | T-Cat | Notes |
|---|:-:|:-:|---|
| MerID, Timestamp | ● | ● | |
| MerTradeNo | ● | ● | |
| GoodsType / LgsType / ShipType | ● | ● | see codes above |
| TradeAmt | ● | ● | COD amount, or declared value when not COD |
| ServiceType | ● | ● | 1 = COD, 3 = no COD |
| StoreID | ● | empty | from the store map |
| Consignee / ConsigneeMail / ConsigneeMobile | ● | ● | |
| SenderName / SenderMobile | ● | ● | |
| NotifyURL | ● | ● | status / print notifications |
| ConsigneeAddress / ProdDesc / DeliveryTimeTag | | ● | ProdDesc ≤ 20 chars |

Response (decrypted): `Status`, `Message`, **`ShipTradeNo`** (used for query / print / notifications), `TradeAmt`, `ServiceType`.

### 2. Query shipment

`POST /api/logistics/query`, Version `1.1`, EncryptInfo: `MerID`, `Timestamp`, `LgsType`, `ShipTradeNo`.
Response includes `Odno`, `PartnerId`, `ValidationNo` (C2C), `FileNo` (T-Cat), `ShipStatus`,
`ShipStatusDesc`, `ShipStatusTime` (`-` = not yet available).

**ShipStatus codes** (plugin `Utils/ShippingStatus.php`):

| Code | Meaning |
|---|---|
| 21 | Waiting for shipment |
| 22 | Checked in at logistics center (CVS only) |
| 92 | Processing / received at sender store (C2C) |
| 31 | In delivery |
| 32 | Arrived at pickup store |
| 11 | Picked up |

### 3. Notifications

PAYUNi POSTs `EncryptInfo` (+ `HashInfo`) to `NotifyURL`. Decrypted `ApiType` is `ShipStatus`
(status update: `ShipTradeNo`, `ShipStatus`, `ShipStatusDesc`, `ShipStatusTime`; T-Cat adds `OBTNumber`, `FileNo`)
or `Print` (label result). Match orders by `ShipTradeNo`.

---

## Best Practices

1. **Store Selection**: Always use the StoreID from the Store Map API response, not the displayed code
2. **Error Handling**: Implement proper error handling for all API calls with retry logic
3. **Status Tracking**: Use Status Notification webhook for real-time updates instead of polling
4. **Encryption**: Securely store HashKey and HashIV, never expose in client-side code
5. **Order Numbers**: Ensure MerchantOrderNo is unique across all orders
6. **Timestamp**: Always generate fresh timestamp for each API call
7. **Testing**: Use test environment extensively before going to production
8. **Validation**: Validate all user input (name, phone, email) before API calls
9. **Logging**: Log all API requests and responses for debugging and auditing
10. **Notification URL**: Ensure NotifyURL is accessible from NewebPay servers (not localhost)

---

## Use Cases

### E-commerce Platform
- Integrate store map for customers to select pickup location
- Create shipment automatically after order confirmation
- Send tracking updates to customers via email/SMS
- Handle returns and exchanges through modify shipment API

### Marketplace
- Support multiple vendors shipping to convenience stores
- Provide unified logistics tracking interface
- Automate shipment number retrieval and label printing
- Handle COD payment collection and settlement

### Subscription Service
- Schedule recurring shipments to same pickup store
- Automatic label generation for regular deliveries
- Batch shipment creation for multiple orders
- Track delivery success rate and optimize logistics

---

## Related Resources

- [EXAMPLES.md](./EXAMPLES.md) - Complete code examples (TypeScript, Python, PHP)
- [references/NEWEBPAY_LOGISTICS_REFERENCE.md](./references/NEWEBPAY_LOGISTICS_REFERENCE.md) - NewebPay Logistics API full specification
- [scripts/search.py](./scripts/search.py) - BM25 search engine for error codes and fields
- [scripts/test_logistics.py](./scripts/test_logistics.py) - Connection testing tool

---

## Support

### NewebPay Technical Support
- Phone: 02-2655-8938
- Official Documentation: https://www.newebpay.com

### API Version
Current Version: 1.0

### Last Updated
2026-01-29

---

**Total Lines**: 750+
