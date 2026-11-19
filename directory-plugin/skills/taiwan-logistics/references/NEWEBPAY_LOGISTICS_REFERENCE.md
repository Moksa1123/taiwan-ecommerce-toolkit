# NewebPay Logistics API Reference

> Directory edition: reference files and JSON data only, no scripts. Tools under `scripts/`, `examples/` and `tests/` ship in the full edition (npm package `taiwan-logistics-skill`).
> Keys and merchant IDs are set up by the user and passed into the code as parameters; they appear as fake values such as `YOUR_HASH_KEY`. Published sandbox keys are shown as `YOUR_TEST_KEY`; get them from the provider's official docs. Credential-type field names are shown as `<帳密欄位>`.

**Complete API specification for NewebPay Logistics Services**

依 NDNS 1.0.0（物流服務技術串接手冊，下載頁標示 2024-05-16，2026-11-17 仍是最新版）與官方程式範例 v1。

- 規格書：https://www.newebpay.com/website/Page/download_file?name=%E7%89%A9%E6%B5%81%E6%9C%8D%E5%8B%99%E6%8A%80%E8%A1%93%E4%B8%B2%E6%8E%A5%E6%89%8B%E5%86%8A_NDNSv1.0.0.pdf
- 程式範例：https://www.newebpay.com/website/Page/download_file?name=%E7%89%A9%E6%B5%81%E6%9C%8D%E5%8B%99%E6%8A%80%E8%A1%93%E4%B8%B2%E6%8E%A5%E6%89%8B%E5%86%8A_%E7%A8%8B%E5%BC%8F%E7%AF%84%E4%BE%8Bv1.zip
- 下載頁：https://www.newebpay.com/website/Page/content/download_api

藍新物流只有超商（C2C 四大超商、B2C 7-ELEVEN），沒有宅配（官網「宅配」選單為「敬請期待」）。

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

| 項目 | C2C 店到店（四大超商） | B2C 大宗寄倉（7-ELEVEN） |
|------|------------------------|--------------------------|
| 啟用審核 | 不需要 | 需要 |
| 測標 | 不需要 | 需要 |
| 列印方式 | 商店直接列印／超商 Kiosk 列印 | 商店直接列印黏貼後出貨 |
| 寄送地點 | 商店到四大超商門市寄件 | 商店直接送貨到物流倉庫驗收 |
| 運費 | 從商店預付費用扣款，買家不需付運費 | 同左 |
| 退貨 | 退至原寄件門市 | 物流中心宅配退貨 |

（NDNS 1.0.0 p.4「1. 簡介」）

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

### Data Exchange

- 以標準 Form Post（`application/x-www-form-urlencoded`）送出，UTF-8（NDNS p.8「(四) 資料交換方式」）。
- 送出的外層參數名稱後方有底線：`UID_`、`EncryptData_`、`HashData_`、`Version_`、`RespondType_`。
- API 回應為 JSON：`Status`、`Message`、`EncryptData`、`HashData`、`UID`、`Version`、`Encoding`（保留欄位，固定空值），回應欄位不帶底線。
- 門市地圖（storeMap）與列印寄貨單（printLabel）是瀏覽器前景 Form Post；其餘為伺服器端 POST。

### Encryption Process

#### 1. Encrypt Data (AES-256-CBC)

```
EncryptData_ = hex( AES-256-CBC( json_encode(data), HashKey, HashIV ) )
```

**Parameters:**
- Plaintext: EncryptData_ 內含參數組成的 JSON（官方範例 `json_encode($_POST)`）
- Algorithm: AES-256-CBC，PKCS7 padding
- Key: HashKey (32 bytes)
- IV: HashIV (16 bytes)
- Output: 密文轉小寫 hex（官方範例 `bin2hex(openssl_encrypt(..., OPENSSL_RAW_DATA, $iv))`）

#### 2. Generate Hash (SHA256)

```
HashData_ = SHA256("HashKey=" + HashKey + "&" + EncryptData_ + "&HashIV=" + HashIV).toUpperCase()
```

規格書範例（NDNS p.13「Hash Data 處理方式」）：

```
SHA256("HashKey=12345678901234567890123456789012&AAAABBBBCCCCDDDD&HashIV=12345678")
= 5C6C504A2F2B2E3EB5CA80998F626307ACD327AC6DCE4FF84F86B021988B2576
```

### Decryption Process

#### 1. Verify Hash

```
CalculatedHash = SHA256("HashKey=" + HashKey + "&" + EncryptData + "&HashIV=" + HashIV).toUpperCase()
if (!timingSafeEqual(CalculatedHash, HashData)) throw Error('Hash verification failed')
```

#### 2. Decrypt Data

```
DecryptedJSON = AES-256-CBC-Decrypt( hex2bin(EncryptData), HashKey, HashIV )  // 移除 PKCS7 padding
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

**URL:** `POST /API/Logistic/storeMap`（瀏覽器前景 Form Post，導向超商地圖；選店後藍新以 Form Post 把結果送到 `ReturnURL`）

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

官方範例 `return_url.php` 讀 `$_POST['EncryptData']`（不帶底線）。

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
| NotifyURL | Varchar(100) | - | 取貨完成／貨態更新通知網址 |
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

**Important:** 限使用前景表單方式送出（Form Post，由瀏覽器送出），回應是可列印的 HTML 寄貨單頁面。

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

規格書此表欄位帶底線，但官方範例 `notify_url.php` 讀 `$_POST['EncryptData']`（不帶底線）；兩種都要能讀。

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

NDNS 1.0.0 未規定商店的回應內容與重送機制；官方範例 `notify_url.php` 只寫 log、不輸出任何內容。回 HTTP 200 即可，不要依賴特定回應字串。

**Important:**
- NotifyURL 必須能從藍新伺服器連線（不能是 localhost）
- 先驗 HashData 再解密（官方範例未驗章，正式環境應補上）

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

`ShopDate` 型態為 Date；規格書未給格式範例，解析時不要寫死格式。

### MerchantOrderNo Format

- Length: Up to 30 characters
- Allowed characters: Alphanumeric (A-Z, a-z, 0-9) and underscore (_)
- 同一商店中不可重覆
- Example: `ORD_20260129_001`

### Phone Number Format

- `UserTel` 為取件人手機號碼，Varchar(10)
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

自行在測試平台申請（NDNS p.6–7「3. 使用規則」）：
1. 到 https://cwww.newebpay.com/ 註冊測試區會員並建立測試商店
2. 會員中心 → 商店管理／商店資料設定 → 詳細資料：取得 HashKey、HashIV
3. 商店資料設定／物流設定：啟用物流服務、勾選服務型態並填寫退貨門市資訊
4. 帳務中心 → 預付費用／預付費用異動紀錄：按「模擬存入」存入預付費用（物流費從預付費用扣，餘額不足回 `1114`）

正式環境在 https://www.newebpay.com/ 註冊，金鑰、物流設定路徑相同；正式區預付費用需轉帳到專屬帳號。

### Test Environment

**Base URL:**
```
https://ccore.newebpay.com/API/Logistic
```

測試環境只能測建立物流訂單、取得寄件代碼、列印寄貨單等，無法完整測試貨態（NDNS p.7「(二) 環境說明」）。

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

**客服電話：** 02-2786-3655（每日 08:00–23:00）
**客服信箱：** cs@newebpay.com

**Official Website:** https://www.newebpay.com

### API Documentation

API 文件下載頁：https://www.newebpay.com/website/Page/content/download_api （「物流服務技術串接手冊」與程式範例）

