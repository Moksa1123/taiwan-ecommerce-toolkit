# NewebPay Logistics API Reference

**Complete API specification for NewebPay Logistics Services**

依 NDNS 1.0.0（物流服務技術串接手冊）。

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication & Encryption](#authentication--encryption)
3. [API Endpoints](#api-endpoints)
4. [Data Types & Formats](#data-types--formats)
5. [Error Codes](#error-codes)
6. [Status Codes](#status-codes)
7. [Testing](#testing)

---

## Overview

### Service Types

**B2C (大宗寄倉) - Bulk Warehouse:**
- Merchant ships goods to NewebPay logistics center
- Logistics center distributes to pickup convenience stores
- Only available for 7-ELEVEN

**C2C (店到店) - Store-to-Store:**
- Merchant ships goods to sender convenience store
- Store ships to logistics center, then to pickup store
- Available for: 7-ELEVEN, FamilyMart, Hi-Life, OK Mart

### Trade Types

| Code | Type | Description |
|------|------|-------------|
| 1 | 取貨付款 | Cash on Delivery (COD) |
| 3 | 取貨不付款 | No Payment (payment already completed) |

### Convenience Store Codes

| Code | Store | C2C Support | B2C Support |
|------|-------|-------------|-------------|
| 1 | 7-ELEVEN | ● | ● |
| 2 | FamilyMart (全家) | ● | ✗ |
| 3 | Hi-Life (萊爾富) | ● | ✗ |
| 4 | OK Mart | ● | ✗ |

---

## Authentication & Encryption

### Encryption Method

NewebPay Logistics uses AES-256-CBC + SHA256 encryption (same as NewebPay Payment).

**Required Credentials:**
- Merchant ID (UID)
- HashKey (32 characters)
- HashIV (16 characters)

### Encryption Process

#### 1. Encrypt Data (AES-256-CBC)

```
EncryptData = AES-256-CBC(JSON.stringify(data), HashKey, HashIV)
```

**Parameters:**
- Algorithm: AES-256-CBC
- Key: HashKey (32 bytes)
- IV: HashIV (16 bytes)
- Mode: CBC
- Padding: PKCS7

#### 2. Generate Hash (SHA256)

```
HashData = SHA256(HashKey + EncryptData + HashIV).toUpperCase()
```

### Decryption Process

#### 1. Verify Hash

```
CalculatedHash = SHA256(HashKey + EncryptData + HashIV).toUpperCase()
if (CalculatedHash !== HashData) throw Error('Hash verification failed')
```

#### 2. Decrypt Data

```
DecryptedJSON = AES-256-CBC-Decrypt(EncryptData, HashKey, HashIV)
Data = JSON.parse(DecryptedJSON)
```

---

## API Endpoints

### Base URLs

**Test Environment:**
```
https://ccore.newebpay.com/API/Logistic
```

**Production Environment:**
```
https://core.newebpay.com/API/Logistic
```

### API List

| API | Endpoint | Method | Description |
|-----|----------|--------|-------------|
| Store Map Query | `/storeMap` | POST | Query convenience store locations |
| Create Shipment | `/createShipment` | POST | Create logistics order |
| Get Shipment Number | `/getShipmentNo` | POST | Get shipping code for printing |
| Print Label | `/printLabel` | POST (Form) | Print shipping labels |
| Query Shipment | `/queryShipment` | POST | Query order status |
| Modify Shipment | `/modifyShipment` | POST | Modify order details |
| Track Shipment | `/trace` | POST | Track delivery history |

---

## 1. Store Map Query API [NPA-B51]

Query convenience store locations for customer to select pickup or sender store.

### Request

**URL:** `POST /API/Logistic/storeMap`

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| UID_ | Varchar(15) | ● | Merchant ID |
| EncryptData_ | Text | ● | Encrypted data |
| HashData_ | Text | ● | SHA256 hash |
| Version_ | Varchar(5) | ● | API version (fixed: "1.0") |
| RespondType_ | Varchar(6) | ● | Response format (fixed: "JSON") |

**EncryptData_ Content:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| MerchantOrderNo | Varchar(30) | ● | Unique order ID (alphanumeric + underscore) |
| LgsType | Varchar(15) | ● | "B2C" or "C2C" |
| ShipType | Varchar(15) | ● | "1"=7-11, "2"=FamilyMart, "3"=Hi-Life, "4"=OK Mart |
| ReturnURL | Varchar(50) | ● | Callback URL after store selection |
| TimeStamp | Text | ● | Unix timestamp (tolerance: 120 seconds) |
| ExtraData | Varchar(20) | - | Custom data (returned as-is) |

### Response

**Status Codes:**
- `SUCCESS`: Request successful
- Error codes: See [Error Codes](#error-codes)

**Response Parameters:**

| Field | Type | Description |
|-------|------|-------------|
| Status | Varchar(10) | Response status |
| Message | Varchar(30) | Status message |
| EncryptData | Text | Encrypted response data |
| HashData | Text | SHA256 hash |
| UID | Varchar(15) | Merchant ID |
| Version | Varchar(5) | API version |

**Decrypted EncryptData Content (Callback):**

| Field | Type | Description |
|-------|------|-------------|
| LgsType | Varchar(15) | Logistics type |
| ShipType | Varchar(15) | Store type code |
| MerchantOrderNo | Varchar(30) | Order ID |
| StoreName | Varchar(10) | Selected store name |
| StoreTel | Varchar(12) | Store phone number |
| StoreAddr | Varchar(100) | Store address |
| StoreID | Varchar(8) | Store code (use this for shipment creation) |
| ExtraData | Varchar(20) | Original custom data |

**Important Notes:**
- For FamilyMart and OK Mart, the store code displayed on map may differ from the actual StoreID
- Always use the StoreID returned in the callback, not the displayed code

---

## 2. Create Shipment API [NPA-B52]

Create logistics shipment order after payment order is established.

### Request

**URL:** `POST /API/Logistic/createShipment`

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| UID_ | Varchar(15) | ● | Merchant ID |
| EncryptData_ | Text | ● | Encrypted data |
| HashData_ | Text | ● | SHA256 hash |
| Version_ | Varchar(5) | ● | Fixed: "1.0" |
| RespondType_ | Varchar(6) | ● | Fixed: "JSON" |

**EncryptData_ Content:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| MerchantOrderNo | Varchar(30) | ● | Unique order ID |
| TradeType | Int(1) | ● | 1=COD, 3=No Payment |
| UserName | Varchar(20) | ● | Recipient name |
| UserTel | Varchar(10) | ● | Recipient mobile number |
| UserEmail | Varchar(50) | ● | Recipient email |
| StoreID | Varchar(10) | ● | Pickup store code (from store map) |
| Amt | Int(10) | ● | Transaction amount (max: 20000 NTD) |
| NotifyURL | Varchar(100) | - | Status notification callback URL |
| ItemDesc | Varchar(100) | - | Product description |
| LgsType | Varchar(3) | ● | "B2C" or "C2C" |
| ShipType | Varchar(15) | ● | "1"=7-11, "2"=FamilyMart, "3"=Hi-Life, "4"=OK Mart |
| TimeStamp | Varchar(50) | ● | Unix timestamp (tolerance: 120 seconds) |

**Amount Limits:**
- COD (TradeType=1): Maximum 20,000 NTD
- No Payment (TradeType=3): Maximum 20,000 NTD

### Response

**Decrypted EncryptData Content:**

| Field | Type | Description |
|-------|------|-------------|
| MerchantID | Varchar(15) | NewebPay merchant ID |
| Amt | Int(10) | Transaction amount |
| MerchantOrderNo | Varchar(30) | Order ID |
| TradeNo | Varchar(20) | NewebPay transaction ID (important: save this) |
| LgsType | Varchar(15) | Logistics type |
| ShipType | Varchar(15) | Store type |
| StoreID | Varchar(10) | Pickup store code |
| TradeType | Int(1) | Trade type |

---

## 3. Get Shipment Number API [NPA-B53]

Get shipping code before shipment. Merchants can use this code to print labels at convenience store Kiosk machines.

### Request

**URL:** `POST /API/Logistic/getShipmentNo`

**EncryptData_ Content:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| MerchantOrderNo | Json_array | ● | Array of order IDs (max 10) |
| TimeStamp | Varchar(50) | ● | Unix timestamp |

**Batch Limit:** Maximum 10 orders per request

### Response

**Decrypted EncryptData Content:**

| Field | Type | Description |
|-------|------|-------------|
| SUCCESS | Json_array | Array of successful results |
| ERROR | Json_array | Array of failed results |

**SUCCESS Array Item:**

| Field | Type | Description |
|-------|------|-------------|
| MerchantOrderNo | Varchar(30) | Order ID |
| ErrorCode | Varchar(20) | "SUCCESS" |
| LgsNo | Varchar(20) | Logistics tracking number |
| StorePrintNo | Varchar(20) | Code for Kiosk printing |
| ShipType | Varchar(15) | Store type |
| LgsType | Varchar(15) | Logistics type |

**ERROR Array Item:**

| Field | Type | Description |
|-------|------|-------------|
| MerchantOrderNo | Varchar(30) | Order ID |
| ErrorCode | Varchar(20) | Error code (see error codes section) |

---

## 4. Print Label API [NPA-B54]

Print shipping labels to attach to products.

### Request

**URL:** `POST /API/Logistic/printLabel`

**Important:** This API requires **Form POST** method (not JSON API call). The response is an HTML page for printing.

**EncryptData_ Content:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| LgsType | Varchar(15) | ● | "B2C" or "C2C" |
| ShipType | Varchar(15) | ● | "1"=7-11, "2"=FamilyMart, "3"=Hi-Life, "4"=OK Mart |
| MerchantOrderNo | json_array | ● | Array of order IDs |
| TimeStamp | Varchar(50) | ● | Unix timestamp |

**Batch Limits:**

| Store | Maximum Labels per Request |
|-------|----------------------------|
| 7-ELEVEN (1) | 18 |
| FamilyMart (2) | 8 |
| Hi-Life (3) | 18 |
| OK Mart (4) | 18 |

### Response

Returns HTML page with printable shipping labels.

---

## 5. Query Shipment API [NPA-B55]

Query logistics order information and current status.

### Request

**URL:** `POST /API/Logistic/queryShipment`

**EncryptData_ Content:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| MerchantOrderNo | Varchar(30) | ● | Order ID |
| TimeStamp | Varchar(50) | ● | Unix timestamp |

### Response

**Decrypted EncryptData Content:**

| Field | Type | Description |
|-------|------|-------------|
| MerchantID | Varchar(15) | Merchant ID |
| LgsType | Varchar(15) | Logistics type |
| TradeNo | Varchar(20) | NewebPay transaction ID |
| MerchantOrderNo | Varchar(30) | Order ID |
| Amt | Int(10) | Transaction amount |
| ItemDesc | Varchar(100) | Product description |
| NotifyURL | Varchar(50) | Notification URL |
| LgsNo | Varchar(20) | Logistics tracking number |
| StorePrintNo | Varchar(20) | Store print code |
| collectionAmt | Int(10) | COD collection amount |
| TradeType | Int(1) | 1=COD, 3=No Payment |
| Type | Int(1) | 1=Normal, 3=Return |
| ShopDate | Date | Ship date |
| UserName | Varchar(20) | Recipient name |
| UserTel | Varchar(10) | Recipient phone |
| UserEmail | Varchar(50) | Recipient email |
| StoreID | Varchar(10) | Pickup store code |
| ShipType | Varchar(15) | Store type |
| StoreName | Varchar(20) | Store name |
| Retld | Varchar(10) | Status code (see status codes section) |
| RetString | Varchar(30) | Status description |

---

## 6. Modify Shipment API [NPA-B56]

Modify shipment order details. Only available for orders that have not yet been shipped.

### Request

**URL:** `POST /API/Logistic/modifyShipment`

**Modifiable Conditions:**
- Order has not yet obtained shipping number (RetId: 0_1)
- Shipment expired (RetId: 0_2)
- Store reselection required (RetId: 3, 11, 12)

**EncryptData_ Content:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| MerchantOrderNo | Varchar(30) | ● | Order ID |
| LgsType | Varchar(15) | ● | Logistics type |
| ShipType | Varchar(15) | ● | Store type |
| UserName | Varchar(20) | - | New recipient name |
| UserTel | Varchar(10) | - | New phone number |
| UserEmail | Varchar(50) | - | New email |
| StoreID | Varchar(10) | + | New store code |
| TimeStamp | Varchar(50) | ● | Unix timestamp |

**Note:** When modifying for store reselection (RetId: 3, 11, 12), only StoreID can be changed. UserName, UserTel, and UserEmail cannot be modified.

### Response

**Decrypted EncryptData Content:**

| Field | Type | Description |
|-------|------|-------------|
| MerchantID | Varchar(15) | Merchant ID |
| MerchantOrderNo | Varchar(30) | Order ID |
| LgsType | Varchar(15) | Logistics type |
| ShipType | Varchar(15) | Store type |

---

## 7. Track Shipment API [NPA-B57]

Track complete logistics delivery history with all status changes.

### Request

**URL:** `POST /API/Logistic/trace`

**EncryptData_ Content:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| MerchantOrderNo | Varchar(30) | ● | Order ID |
| TimeStamp | Varchar(50) | ● | Unix timestamp |

### Response

**Decrypted EncryptData Content:**

| Field | Type | Description |
|-------|------|-------------|
| LgsType | Varchar(15) | Logistics type |
| MerchantOrderNo | Varchar(30) | Order ID |
| LgsNo | Varchar(20) | Tracking number |
| TradeType | Int(1) | Trade type |
| ShipType | Varchar(15) | Store type |
| History | json_array | Array of tracking history events |
| Retld | Varchar(10) | Current status code |
| RetString | Varchar(30) | Current status description |

**History Array Item:**

| Field | Type | Description |
|-------|------|-------------|
| Retld | Varchar(10) | Status code at this time |
| RetString | Varchar(30) | Status description |
| EventTime | Varchar(20) | Event timestamp |

---

## 8. Status Notification [NPA-B58]

Real-time notification when shipment status changes. NewebPay will POST to the NotifyURL provided when creating shipment.

### Callback Request

**Method:** POST to merchant's NotifyURL

**Parameters:**

| Field | Type | Description |
|-------|------|-------------|
| Status | Varchar(10) | "SUCCESS" or error code |
| Message | Varchar(30) | Status message |
| EncryptData_ | Text | Encrypted data |
| HashData_ | Text | SHA256 hash |
| UID_ | Varchar(15) | Merchant ID |
| Version_ | Varchar(5) | API version |

**Decrypted EncryptData_ Content:**

| Field | Type | Description |
|-------|------|-------------|
| LgsType | Varchar(15) | Logistics type |
| MerchantOrderNo | Varchar(30) | Order ID |
| LgsNo | Varchar(20) | Tracking number |
| TradeType | Int(1) | Trade type |
| ShipType | Varchar(15) | Store type |
| Retld | Varchar(10) | Status code |
| RetString | Varchar(30) | Status description |
| EventTime | Varchar(20) | Event timestamp |

### Callback Response

Merchant must respond with:
- Success: `1|OK`
- Error: `0|Error` or `0|[Error Message]`

**Important:**
- NotifyURL must be accessible from NewebPay servers (not localhost)
- Must respond within timeout period
- NewebPay will retry if no response received

---

## Data Types & Formats

### TimeStamp Format

Unix timestamp in seconds since 1970-01-01 00:00:00 GMT.

```typescript
// JavaScript
const timestamp = Math.floor(Date.now() / 1000).toString();

// Python
import time
timestamp = str(int(time.time()))
```

**Tolerance:** 120 seconds (±2 minutes)

### Date Format

Date fields use `yyyy-MM-dd` format:
- Example: `2026-01-29`

### MerchantOrderNo Format

- Length: Up to 30 characters
- Allowed characters: Alphanumeric (A-Z, a-z, 0-9) and underscore (_)
- Must be unique across all orders
- Example: `ORD_20260129_001`

### Phone Number Format

- Format: 10 digits starting with 09
- Example: `0912345678`
- No spaces or dashes

### Email Format

- Standard email format
- Max length: 50 characters
- Example: `customer@example.com`

---

## Error Codes

### API Error Codes

| Code | Message | Description | Solution |
|------|---------|-------------|----------|
| SUCCESS | 成功 | Success | - |
| 1101 | 新增物流訂單失敗 | Failed to create logistics order | Check order parameters |
| 1102 | 查無合作商店 | Merchant not found | Verify merchant credentials |
| 1103 | 已存在相同的商店訂單編號 | Duplicate order number | Use unique MerchantOrderNo |
| 1104 | 無啟用對應物流商服務 | Logistics service not enabled | Contact NewebPay to enable service |
| 1105 | 門市資訊有誤或空白 | Invalid or empty store information | Verify StoreID from store map |
| 1106 | 不允許 IP | IP not allowed | Add IP to whitelist |
| 1107 | 查無金流訂單資料 | Payment order not found | Create payment order first |
| 1108 | 系統異常，無法查詢物流訂單資料 | System error, cannot query order | Retry later or contact support |
| 1109 | 查無物流訂單資料 | Logistics order not found | Verify MerchantOrderNo |
| 1110 | 系統異常，無法修改物流訂單資料 | System error, cannot modify order | Retry later or contact support |
| 1111 | 該筆物流單狀態已無法修改內容 | Order status cannot be modified | Check order status first |
| 1112 | 修改物流單失敗 | Failed to modify order | Check modification parameters |
| 1113 | 系統異常，無法查詢物流貨態歷程資料 | System error, cannot query tracking | Retry later or contact support |
| 1114 | 預付費用餘額不足 | Insufficient prepaid balance | Add balance to account |
| 1115 | 取寄貨單號失敗 | Failed to get shipment number | Check order status, retry later |
| 1116 | 該交易已建立寄貨單資訊 | Shipment already created | Use query API to get details |

### Data Format Errors

| Code | Message | Description |
|------|---------|-------------|
| 2100 | 資料格式錯誤 | Data format error |
| 2101 | 版本錯誤 | Version error |
| 2102 | UID_ 不可為空 | UID_ cannot be empty |
| 2103 | 超商取貨付款的金額限 20000 元內 | COD amount limit: 20000 NTD |
| 2104 | 超商取貨不付款的金額限 20000 元內 | No payment amount limit: 20000 NTD |
| 2105 | 一次最多僅能取得 10 筆寄貨單號 | Max 10 shipment numbers per request |
| 2106 | 7-11/全家/萊爾富/OK 最多標籤數限制 | Max labels exceeded for provider |

### Security Errors

| Code | Message | Description |
|------|---------|-------------|
| 4101 | IP 限制使用 | IP restricted |
| 4103 | HashData_ 資料檢查不符合 | Hash verification failed |
| 4104 | 加密資料有誤，請確認 Hash_Key 與 Hash_IV | Encryption error, check credentials |

---

## Status Codes

### RetId & RetString

> 依 NDNS 1.0.0「6. 附錄 (二)」，與 `data/status-codes.csv` 相同（該檔另收附錄 (一) 的 API 回應代碼）。
> 規格書的參數表把欄位寫成 `Retld`（小寫 L），附錄標題寫 `RetId`；PDF 無法判斷實際鍵名，程式請兩種都讀。

| RetId | RetString | Category | Description |
|-------|-----------|----------|-------------|
| 0_1 | 訂單未處理 | Pending | Order not processed |
| 0_2 | 物流單號已過期，請重新取號 | Pending | Shipment number expired |
| 0_3 | 取消出貨 | Pending | Shipment canceled |
| 1 | 訂單處理中 | Processing | Order processing |
| 2 | 超商已收件 | In Transit | Store received shipment |
| 3 | 已重選門市，等待物流重新出貨 | In Transit | Store reselected, waiting for re-shipment |
| 4 | 商品已進物流中心驗收完成 | In Transit | Arrived at logistics center |
| 11 | 取貨門市關店，請重新選取 | In Transit | Pickup store closed, reselect required |
| 5 | 商品送達取貨門市 | Ready for Pickup | Arrived at pickup store |
| 6 | 買家取貨完成 | Completed | Customer picked up (success) |
| -1 | 商品已退回廠商 | Completed | Returned to merchant |
| -6 | 已申請宅配退貨 | Completed | Home delivery return requested |
| -9 | 物流驗收異常等待回覆 | Completed | Logistics inspection error |
| -2 | 商品送達原寄件(指定退貨)門市 | Return/Compensation | Returned to sender store |
| -3 | 商品退回物流中心驗收完成 | Return/Compensation | Returned to logistics center |
| -4 | 商品退往物流中心(買家未取) | Return/Compensation | Returning (customer did not pickup) |
| -5 | 商品即將退回(買家未取) | Return/Compensation | Soon to return (customer did not pickup) |
| -7 | 已同意/申請異常判賠 | Return/Compensation | Compensation approved |
| -10 | 商品已銷毀/拋棄 | Return/Compensation | Product destroyed |
| -11 | 商品已銷毀/拋棄 | Return/Compensation | Product destroyed |
| 10 | 商品即將退回 | Return/Compensation | Soon to be returned |
| 12 | 退貨門市關店，請重新選取 | Return/Compensation | Return store closed |
| 13 | 商品退往物流中心(賣家未取) | Return/Compensation | Returning (merchant did not pickup) |
| 14 | 請申請宅配退貨 | Return/Compensation | Request home delivery return |
| 15 | 商品已銷毀/拋棄 | Return/Compensation | Product destroyed |
| 16 | 請確認匯款帳號 | Return/Compensation | Confirm bank account |

---

## Testing

### Test Credentials

Contact NewebPay to obtain test credentials:
- Test Merchant ID (UID)
- Test HashKey
- Test HashIV

### Test Environment

**Base URL:**
```
https://ccore.newebpay.com/API/Logistic
```

### Testing Checklist

**1. Store Map Query**
- [ ] Test B2C logistics type
- [ ] Test C2C logistics type
- [ ] Test all 4 convenience store types
- [ ] Verify store selection callback
- [ ] Verify StoreID format

**2. Create Shipment**
- [ ] Test COD (TradeType=1)
- [ ] Test No Payment (TradeType=3)
- [ ] Test amount limits (max 20,000)
- [ ] Verify TradeNo generation
- [ ] Test with valid StoreID

**3. Get Shipment Number**
- [ ] Test single order
- [ ] Test multiple orders (up to 10)
- [ ] Test with invalid order IDs
- [ ] Verify LgsNo and StorePrintNo

**4. Print Label**
- [ ] Test batch limits per store type
- [ ] Verify HTML response
- [ ] Test print functionality

**5. Query Shipment**
- [ ] Test with valid order ID
- [ ] Test with invalid order ID
- [ ] Verify all returned fields
- [ ] Check status codes

**6. Modify Shipment**
- [ ] Test modify recipient info
- [ ] Test modify store
- [ ] Test with non-modifiable status
- [ ] Verify error handling

**7. Track Shipment**
- [ ] Test tracking history
- [ ] Verify history array
- [ ] Check timestamp formats

**8. Status Notification**
- [ ] Setup test callback URL
- [ ] Test callback decryption
- [ ] Test response format
- [ ] Verify all status codes

### Common Test Scenarios

**Scenario 1: Complete C2C Flow**
1. Query store map → Get StoreID
2. Create shipment → Get TradeNo
3. Get shipment number → Get LgsNo and StorePrintNo
4. Print label → Generate shipping label
5. Query shipment → Check status
6. Track shipment → View history

**Scenario 2: Modify Recipient**
1. Create shipment
2. Query shipment status
3. Modify recipient information
4. Query shipment again to verify

**Scenario 3: Change Pickup Store**
1. Create shipment
2. Query store map for new store
3. Modify shipment with new StoreID
4. Verify modification

---

## Best Practices

### 1. Order Number Management
- Use unique, sequential order numbers
- Include date/time in order number for tracking
- Keep record of all order numbers
- Don't reuse order numbers even for canceled orders

### 2. Error Handling
- Always verify hash before decrypting
- Implement retry logic for transient errors (1108, 1110, 1113)
- Don't retry for permanent errors (1102, 1103, 1104)
- Log all API requests and responses

### 3. Security
- Store HashKey and HashIV securely (environment variables, secrets manager)
- Never expose credentials in client-side code
- Use HTTPS for all NotifyURL endpoints
- Validate IP whitelist for production

### 4. Status Tracking
- Use status notification webhook instead of polling
- Handle all status codes appropriately
- Send customer notifications for key status changes (5, 6, -1)
- Log all status updates

### 5. Store Selection
- Always use StoreID from API response, not displayed code
- Validate StoreID before creating shipment
- Cache store information for reuse
- Provide clear store selection UI to customers

### 6. Testing
- Test all APIs in test environment before production
- Verify encryption/decryption works correctly
- Test error scenarios
- Validate timestamp handling

---

## Support

### NewebPay Technical Support

**Phone:** 02-2655-8938

**Official Website:** https://www.newebpay.com

### API Documentation

For the latest API documentation and updates, visit NewebPay's developer portal or contact technical support.

