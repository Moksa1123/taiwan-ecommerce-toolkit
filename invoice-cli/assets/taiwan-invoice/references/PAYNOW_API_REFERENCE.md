# 立吉富 PayNow 電子發票 API

PayNow 有兩套發票 API：

| | REST（新版） | SOAP（舊版） |
|---|---|---|
| 來源 | <https://docs.paynow.com.tw/developer/docs/invoice/>（2026-09 擷取） | 《PayNow_EInvoice 串接文件 V1.5》（2022-04-06） |
| 網址 | 測試 `https://invoiceapi-dev.paynow.com.tw`／正式 `https://invoiceapi-prod.paynow.com.tw` | 測試 `https://testinvoice.paynow.com.tw/PayNowEInvoice.asmx`／正式 `https://invoice.paynow.com.tw/PayNowEInvoice.asmx` |
| 認證 | `Authorization: Bearer <商家 JWT-Token>` | `mem_cid` + `mem_password` |
| 格式 | JSON（`application/json`） | SOAP 1.1／1.2 或 HTTP POST |

兩套都**沒有錯誤代碼表**：REST 回應帶 `status`、`type`、`message`；SOAP 回 `S`／`F_錯誤訊息` 或 `ErrorMsg` 文字。

---

## REST API

### 端點

| 功能 | 方法與路徑 |
|------|-----------|
| 單張發票開立 | `POST /api/invoices/issue` |
| 發票作廢 | `POST /api/invoices/cancel` |
| 發票折讓 | `POST /api/invoices/allowance` |
| 折讓作廢 | `POST /api/invoices/cancel-allowance` |
| 取得發票資料 | `GET /api/invoices` |
| POS 機取得發票號碼 | `POST /api/invoices/pos/invoice-numbers` |
| POS 機發票開立 | `POST /api/invoices/pos/issue` |

回應（皆為 200）：

```json
{ "status": 0, "type": "string", "message": "string", "result": {}, "request_id": "string" }
```

### 單張發票開立 `POST /api/invoices/issue`

| 欄位 | 型別 | 說明 |
|------|------|------|
| `order_no` | string | 訂單編號 |
| `send_paper` | boolean | `true` 寄送紙本到買方地址（依合約額外扣點） |
| `send_sms` | boolean | `true` 寄送簡訊到買方手機（依合約額外扣點） |
| `carrier_type` | string | `None`（實體列印）、`PhoneBarCodeCarrier` 手機條碼、`EasyCardCarrier` 悠遊卡、`CitizenDigitalCardNo` 自然人憑證、`BuyerSno` PayNow 會員載具；捐贈發票可帶空 |
| `carrier_id1` | string | 載具明碼；`BuyerSno`、`None` 帶空值 |
| `carrier_id2` | string | 載具隱碼（值同明碼）；`BuyerSno`、`None` 帶空值 |
| `npoban` | string | 愛心碼 |
| `total_amount` | int | 發票總金額 |
| `tax_amount` | int | 稅額：非統編發票帶 `0`（由國稅局算稅），統編發票帶稅額 |
| `tax_type` | string | `SaleTax` 應稅、`FreeTax` 免稅、`ZeroTax` 零稅率、`MixTax` 混合（僅應稅+免稅或應稅+零稅率） |
| `main_remark` | string | 總備註 |
| `is_pass_customs` | boolean | 是否經海關（零稅率必填） |
| `zero_tax_rate_reason` | string | `None`、`ExportGoods`、`ExportLabor`、`FreeTaxGoods`、`OperatingGoodsOrLabor`、`InterNationsTransPort`、`InterNationsShip`、`SalesInterNationsShip`、`Eight`、`Nine` |
| `buyer` | object | `name`、`identifier`（統編）、`address`、`phone`、`email` |
| `items` | object[] | `quantity`、`unit_price`、`amount`、`tax_type`、`tax_amount`、`description` |

有買方手機且 `carrier_type=BuyerSno` 時，PayNow 依手機帶入會員載具號碼。

```json
{
  "order_no": "ORD20260924001",
  "send_paper": false,
  "send_sms": false,
  "carrier_type": "PhoneBarCodeCarrier",
  "carrier_id1": "/ABC1234",
  "carrier_id2": "/ABC1234",
  "npoban": "",
  "total_amount": 1050,
  "tax_amount": 0,
  "tax_type": "SaleTax",
  "main_remark": "",
  "zero_tax_rate_reason": "None",
  "buyer": { "name": "王小明", "identifier": "", "address": "", "phone": "0912345678", "email": "buyer@example.com" },
  "items": [
    { "quantity": 1, "unit_price": 1050, "amount": 1050, "tax_type": "SaleTax", "tax_amount": 0, "description": "商品A" }
  ]
}
```

### 發票作廢 `POST /api/invoices/cancel`

`{ "invoice_number": "AB12345678" }`

### 發票折讓 `POST /api/invoices/allowance`

| 欄位 | 說明 |
|------|------|
| `invoice_number` | 發票號碼 |
| `remark` | 備註（僅供標註，不上傳財政部） |
| `items[]` | `quantity`、`unit_price`、`amount`、`tax`、`tax_type`、`invoice_body_sequence_number`（原發票明細序號） |

### 折讓作廢 `POST /api/invoices/cancel-allowance`

`{ "allowance_number": "string" }`

### 取得發票資料 `GET /api/invoices`

Query：`InvoiceNumber`、`OrderNo`、`Limit`（每頁筆數）、`Page`。回應另含 `paginate`。

### POS 機

1. `POST /api/invoices/pos/invoice-numbers`：`{ "quantity": 10, "uuid": "辨識用" }` 取得一批號碼。
   取得的號碼不進入一般開立流程，由商家自行管理；未使用的號碼於次期單數月 5 號上傳空白發票。
2. `POST /api/invoices/pos/issue`：欄位同單張開立，另加 `invoice_number`、`invoice_date`、`random_number`（商家自行產生）、`is_printed`（消費者不印時為 `false`，仍可帶載具）。

---

## SOAP API（V1.5）

| 函式 | 用途 | 參數 | 回應 |
|------|------|------|------|
| `Invoice_PatchData_Check` | 批次發票驗證（只檢查訂單編號是否已開立） | `mem_cid`、`mem_password`、`csvStr` | `S_資料驗證成功` 或錯誤訊息 |
| `UploadInvoice_Patch` | 批次發票上傳 | 同上 | `S_2,訂單編號_發票號碼,...` 或錯誤訊息 |
| `CancelInvoice` | 作廢（.NET 物件） | `ObjInvoice` | 物件，失敗看 `ErrorMsg` |
| `CancelInvoice_I` | 作廢（字串） | `mem_cid`、`InvoiceNo` | `S` 或 `F_錯誤訊息` |
| `Check_invoice`／`Check_invoiceOrder` | 查詢開立狀態（發票號碼／訂單編號） | `mem_cid`、`InvoiceNo`／`orderno` | `S,發票號碼` 或 `F` |
| `Invoice_Info`／`Invoice_Info_orderno` | 查詢狀態、金額、折讓 | `mem_cid`、`InvoiceNo`／`OrderNo` | 例：`開立,800`、`作廢`、`折讓,300,100,200` |
| `Get_InvoiceURL_I`／`Get_InvoiceURL_O` | 取得發票連結 | `mem_cid`、`InvoiceNo`／`orderno` | 網址 |
| `Sel_Allowance`／`Sel_Allowance_body` | 折讓查詢／折讓明細 | | `Status` 0 開立、1 作廢 |

### csvStr

`base64(CSV)` 後再 urlencode。每個值前加單引號 `'`，逗號分隔，每列一個明細，列間以 `chr(10)` 分隔（最後一列不加）；
相同 `orderno` 視為同一張發票。欄位順序：

```
orderno, buyer_id, buyer_name, buyer_add, buyer_phone, buyer_email, CarrierType, CarrierID_1, CarrierID_2,
LoveCode, Description, Quantity, UnitPrice, Amount, Remark, ItemTaxtype, IsPassCustoms
```

| 欄位 | 規則 |
|------|------|
| `orderno` | ≤30 |
| `buyer_id` | 統編，無則空 |
| `buyer_name` | ≤50，不可空 |
| `buyer_add` | ≤100；填入代表寄送紙本，`BRING` 開頭則保留地址但不寄送 |
| `buyer_phone` | `09xxxxxxxx`，可空；無手機的發票無法歸戶 |
| `buyer_email` | ≤80；填入代表寄送 Email |
| `CarrierType` | `1K0001` 悠遊卡、`3J0002` 手機條碼、`CQ0001` 自然人憑證；統編發票只能用手機條碼 |
| `CarrierID_1`／`CarrierID_2` | 載具明碼／隱碼（悠遊卡明碼免填、隱碼 9 碼數字） |
| `LoveCode` | 3–8 碼數字 |
| `Description` | ≤200 |
| `Quantity`／`UnitPrice`（≤9 碼）／`Amount`（≤7 碼） | |
| `Remark` | ≤25；信用卡消費帶卡號末 4 碼 |
| `ItemTaxtype` | `1` 應稅、`2` 零稅率、`3` 免稅 |
| `IsPassCustoms` | 零稅率必填：`1` 未經海關出口、`2` 經海關出口 |

每日 03:50–05:00 為系統維護時間，暫停所有服務。

### TripleDES（附件一）

3DES／ECB／Zero-Padding → Base64（空白以 `+` 取代）；Key = `1234567890` + Password + `123456`（共 24 碼），
Password 為交易密碼不足 8 碼右補 `0`、超過取前 8 碼。文件未指明套用於哪個欄位。
例：交易密碼 `1234` → `12340000`，`402595001111222299912/12` → `PTKLMe29fUC33H8drlRUJhYkLRp9vXy6`
（`tests/vectors/paynow.json` 驗證；與 PayNow 物流 API 規則相同）。

---

## 相關文件

- [綠界 ECPay](./ECPAY_API_REFERENCE.md)
- [速買配 SmilePay](./SMILEPAY_API_REFERENCE.md)
- [光貿 Amego](./AMEGO_API_REFERENCE.md)
