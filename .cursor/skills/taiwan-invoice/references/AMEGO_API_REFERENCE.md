# 光貿電子發票 API 完整技術規格 (Amego Invoice API)

> 官方文檔來源：https://invoice-api.amego.tw
> 支援 MIG 4.0 規範 (2025/01/01 起)

---

## 目錄
1. [基本說明](#基本說明)
2. [認證與簽章](#認證與簽章)
3. [發票作業](#發票作業)
4. [折讓作業](#折讓作業)
5. [其他功能](#其他功能)
6. [錯誤代碼](#錯誤代碼)

---

## 基本說明

### API 網址
- **API 網址**：`https://invoice-api.amego.tw`
- **環境**：測試與正式共用同一個網址
- **Content-Type**：`application/x-www-form-urlencoded`

> **重要**：請勿使用 `application/json` 發送請求。`data` 欄位的 JSON 字串需經過 URL Encode。

### 測試環境資料
| 項目 | 測試值 |
|------|--------|
| **統編** | `12345678` |
| **App Key** | `sHeq7t8G1wiQvhAuIM27` |
| **後台網址** | https://invoice.amego.tw/ |
| **測試帳號** | test@amego.tw |
| **測試密碼** | 12345678 |
| **公司名稱** | 測試環境有限公司 |

### 正式環境資料
| 項目 | 說明 |
|------|------|
| **統編** | 貴公司統一編號 |
| **App Key** | 請與光貿客服聯絡取得 |

---

## 認證與簽章

### 基本傳入參數
每支 API 必須帶入以下參數：

| 欄位 | 類型 | 描述 |
|------|------|------|
| `invoice` | String | 統一編號 (8碼) |
| `data` | String | API 的 JSON 格式字串 (需 URL Encode) |
| `time` | Number | Unix Timestamp (誤差容許 ±60 秒) |
| `sign` | String | MD5 加密簽名 |

### MD5 簽章規則
```
md5(data 轉 json 格式字串 + time + APP_KEY)
```

**簽章步驟：**
1. 將 `data` 欄位的 JSON 物件轉為字串
2. 串接 `time` (Unix Timestamp)
3. 串接 `APP_KEY`
4. 對整個字串執行 MD5 加密

**範例：**
```javascript
// JavaScript 範例
const crypto = require('crypto')

const data = JSON.stringify({
    OrderId: "TEST-001",
    BuyerIdentifier: "0000000000",
    // ... 其他欄位
})

const time = Math.floor(Date.now() / 1000) // Unix Timestamp
const appKey = "sHeq7t8G1wiQvhAuIM27"

const signString = data + time + appKey
const sign = crypto.createHash('md5').update(signString).digest('hex')

// POST 參數
const params = new URLSearchParams()
params.append('invoice', '12345678')
params.append('data', encodeURIComponent(data)) // URL Encode
params.append('time', time.toString())
params.append('sign', sign)
```

---

## 2025 年 MIG 4.0 重要異動

財政部公告的電子發票資料交換標準訊息建置指引 (MIG) 3.2.1 版本已於 2025/01/01 停用，光貿已升級為 MIG 4.0。

| 功能 | 舊版路徑 (MIG 3.2.1) | **新版路徑 (MIG 4.0)** |
|------|---------------------|----------------------|
| 開立發票 (自動配號) | `/json/c0401` | `/json/f0401` |
| 作廢發票 | `/json/c0501` | `/json/f0501` |
| 開立折讓 | `/json/d0401` | `/json/g0401` |
| 作廢折讓 | `/json/d0501` | `/json/g0501` |
| 開立發票 (API 配號) | `/json/c0401_custom` | `/json/f0401_custom` |

> 舊版 API 目前尚可繼續使用，但建議盡快升級至新版。

---

## 發票作業

### 1. 開立發票 (自動配號)

**端點：** `POST /json/f0401`

光貿會自動分配發票號碼、開立時間及隨機碼。

#### 請求參數 (data 欄位內容)

| 欄位 | 類型 | 必填 | 描述 |
|------|------|------|------|
| `OrderId` | String | Y | 訂單編號，不可重複，不可超過 40 字 |
| `TrackApiCode` | String | N | 指定字軌開立 (需在後台設定 API 指定代碼) |
| `BuyerIdentifier` | String | Y | 買方統編，無則填 `0000000000` |
| `BuyerName` | String | Y | 買方名稱 (不可填 0/00/000/0000) |
| `BuyerAddress` | String | N | 買方地址 |
| `BuyerTelephoneNumber` | String | N | 買方電話 |
| `BuyerEmailAddress` | String | N | 買方電子信箱 (寄送通知用) |
| `MainRemark` | String | N | 總備註，不可超過 200 字 |
| `CarrierType` | String | N | 載具類別：`3J0002` 手機條碼、`CQ0001` 自然人憑證、`amego` 光貿會員載具 |
| `CarrierId1` | String | N | 載具顯碼 |
| `CarrierId2` | String | N | 載具隱碼 |
| `NPOBAN` | String | N | 捐贈碼 |
| `ProductItem` | Array | Y | 商品陣列，最多 9999 筆 |
| `SalesAmount` | Number | Y | 應稅銷售額合計 |
| `FreeTaxSalesAmount` | Number | Y | 免稅銷售額合計 |
| `ZeroTaxSalesAmount` | Number | Y | 零稅率銷售額合計 |
| `TaxType` | Number | Y | 課稅別：1 應稅、2 零稅率、3 免稅、4 特種稅率、9 混合 |
| `TaxRate` | String | Y | 稅率 (5% 填入 `0.05`) |
| `TaxAmount` | Number | Y | 營業稅額 (打統編才需計算 5%) |
| `TotalAmount` | Number | Y | 總計 |
| `CustomsClearanceMark` | Number | N | 通關方式：1 非經海關出口、2 經海關出口 (零稅率必填) |
| `ZeroTaxRateReason` | Number | N | 零稅率原因 71-79 (零稅率必填) |
| `BrandName` | String | N | 品牌名稱 |
| `DetailVat` | Number | N | 單價含稅或未稅：0 未稅、1 含稅 (預設 1) |
| `DetailAmountRound` | Number | N | 小計處理：0 精準到 7 位、1 四捨五入 (預設 0) |
| `PrinterType` | Number | N | 熱感應機型號代碼 (需列印時填入) |
| `PrinterLang` | Number | N | 熱感應機編碼：1 BIG5、2 GBK、3 UTF-8 |
| `PrintDetail` | Number | N | 是否列印明細：1 列印、0 不列印 (僅 PrinterType=2) |

#### ProductItem 商品陣列欄位

| 欄位 | 類型 | 必填 | 描述 |
|------|------|------|------|
| `Description` | String | Y | 品名，不可超過 256 字 |
| `Quantity` | Number | Y | 數量，小數精準度到 7 位數 |
| `Unit` | String | N | 單位，不可超過 6 字 |
| `UnitPrice` | Number | Y | 單價，小數精準度到 7 位數 |
| `Amount` | Number | Y | 小計，小數精準度到 7 位數 |
| `Remark` | String | N | 備註，不可超過 40 字 |
| `TaxType` | Number | Y | 課稅別：1 應稅、2 零稅率、3 免稅 |

#### 零稅率原因代碼

| 代碼 | 說明 |
|------|------|
| `71` | 第一款 外銷貨物 |
| `72` | 第二款 與外銷有關之勞務，或在國內提供而在國外使用之勞務 |
| `73` | 第三款 依法設立之免稅商店銷售與過境或出境旅客之貨物 |
| `74` | 第四款 銷售與保稅區營業人供營運之貨物或勞務 |
| `75` | 第五款 國際間之運輸 |
| `76` | 第六款 國際運輸用之船舶、航空器及遠洋漁船 |
| `77` | 第七款 銷售與國際運輸用之船舶、航空器及遠洋漁船所使用之貨物或修繕勞務 |
| `78` | 第八款 保稅區營業人銷售與課稅區營業人未輸往課稅區而直接出口之貨物 |
| `79` | 第九款 保稅區營業人銷售與課稅區營業人存入自由港區事業或海關管理之保稅倉庫、物流中心以供外銷之貨物 |

#### 請求範例 (一般開立)

```json
{
    "OrderId": "A20200817101021",
    "BuyerIdentifier": "0000000000",
    "BuyerName": "客人",
    "BuyerAddress": "",
    "BuyerTelephoneNumber": "",
    "BuyerEmailAddress": "",
    "MainRemark": "",
    "CarrierType": "",
    "CarrierId1": "",
    "CarrierId2": "",
    "NPOBAN": "",
    "ProductItem": [
        {
            "Description": "測試商品1",
            "Quantity": 1,
            "UnitPrice": 170,
            "Amount": 170,
            "Remark": "",
            "TaxType": 1
        },
        {
            "Description": "會員折抵",
            "Quantity": 1,
            "UnitPrice": -2,
            "Amount": -2,
            "Remark": "",
            "TaxType": 1
        }
    ],
    "SalesAmount": 168,
    "FreeTaxSalesAmount": 0,
    "ZeroTaxSalesAmount": 0,
    "TaxType": 1,
    "TaxRate": "0.05",
    "TaxAmount": 0,
    "TotalAmount": 168
}
```

#### 回應格式 (Success 200)

| 欄位 | 類型 | 描述 |
|------|------|------|
| `code` | Number | 0 代表成功，其他請參考錯誤代碼 |
| `msg` | String | 錯誤訊息 |
| `invoice_number` | String | 發票號碼 (成功時回傳) |
| `invoice_time` | Number | 發票開立時間 (Unix Timestamp) |
| `random_number` | String | 隨機碼 (成功時回傳) |
| `barcode` | String | 電子發票條碼內容 |
| `qrcode_left` | String | 左側 QRCODE 內容 (0元發票回傳空字串) |
| `qrcode_right` | String | 右側 QRCODE 內容 (0元發票回傳空字串) |
| `base64_data` | String | Base64 編碼的列印格式字串 (需列印時才回傳) |

#### 金額計算邏輯

**含稅商品金額計算 (DetailVat = 1)**

```
SalesAmount = Round(所有 ProductItem TaxType=1 的 Amount 加總)
FreeTaxSalesAmount = Round(所有 ProductItem TaxType=3 的 Amount 加總)
ZeroTaxSalesAmount = Round(所有 ProductItem TaxType=2 的 Amount 加總)

【不打統編 (不須分拆稅額)】
TaxAmount = 0

【打統編 (須分拆稅額)】
TaxAmount = SalesAmount - Round(SalesAmount / 1.05)
SalesAmount = SalesAmount - TaxAmount

【總計】
TotalAmount = SalesAmount + FreeTaxSalesAmount + ZeroTaxSalesAmount + TaxAmount
```

**未稅商品金額計算 (DetailVat = 0)**

```
SalesAmount = Round(所有 ProductItem TaxType=1 的 Amount 加總)
FreeTaxSalesAmount = Round(所有 ProductItem TaxType=3 的 Amount 加總)
ZeroTaxSalesAmount = Round(所有 ProductItem TaxType=2 的 Amount 加總)

【計算稅額】
TaxAmount = Round(SalesAmount * 0.05)

【總計】
TotalAmount = SalesAmount + FreeTaxSalesAmount + ZeroTaxSalesAmount + TaxAmount
```

---

### 2. 作廢發票

**端點：** `POST /json/f0501`

作廢已開立的發票。

#### 請求參數 (data 欄位內容)

```json
[
    {
        "CancelInvoiceNumber": "AB00001111"
    }
]
```

支援單張或多張發票同時作廢。

#### 回應格式

| 欄位 | 類型 | 描述 |
|------|------|------|
| `code` | Number | 0 代表成功 |
| `msg` | String | 錯誤訊息 |

---

### 3. 發票狀態查詢

**端點：** `POST /json/invoice_status`

查詢發票的上傳狀態。

#### 請求參數

```json
[
    {
        "InvoiceNumber": "AB00001111"
    }
]
```

#### 回應格式

| 欄位 | 類型 | 描述 |
|------|------|------|
| `code` | Number | 0 代表成功 |
| `msg` | String | 錯誤訊息 |
| `data` | Array | 發票狀態陣列 |

**data 陣列內容：**

| 欄位 | 類型 | 描述 |
|------|------|------|
| `invoice_number` | String | 發票號碼 |
| `type` | String | 發票類型 (NOT_FOUND/C0401/C0501/C0701/TYPE_ERROR) |
| `status` | Number | 1:待處理 2:上傳中 3:已上傳 31:處理中 32:處理完成 91:錯誤 99:完成 |
| `total_amount` | Number | 發票金額 |

**發票類型說明：**
- `NOT_FOUND`: 查無發票
- `C0401`: 發票開立
- `C0501`: 發票作廢
- `C0701`: 發票註銷
- `TYPE_ERROR`: 類型錯誤

---

### 4. 發票查詢

**端點：** `POST /json/invoice_query`

查詢發票詳細內容 (以發票日期為主，只能查詢 180 天內的發票)。

#### 請求參數

```json
{
    "type": "order",
    "order_id": "P202212010001"
}
```

或

```json
{
    "type": "invoice",
    "invoice_number": "AB00001111"
}
```

#### 回應格式

包含完整的發票資訊：

- 發票號碼、類型、狀態
- 買受人資訊
- 金額明細
- 商品明細 (ProductItem 陣列)
- 載具資訊
- 捐贈碼
- 中獎資訊
- 折讓單陣列 (allowance)
- 未處理的排程 (wait)

---

### 5. 發票列表

**端點：** `POST /json/invoice_list`

取得發票主檔資料列表。

#### 請求參數

```json
{
    "date_select": 1,
    "date_start": "20230101",
    "date_end": "20230228",
    "limit": 20,
    "page": 1
}
```

| 欄位 | 類型 | 描述 |
|------|------|------|
| `date_select` | Number | 1:發票日期 2:建立日期 |
| `date_start` | String | 開始日期 (YYYYMMDD) |
| `date_end` | String | 結束日期 (YYYYMMDD) |
| `limit` | Number | 每頁顯示筆數 (20-500，預設 20) |
| `page` | Number | 目前頁數 (預設 1) |

#### 回應格式

| 欄位 | 類型 | 描述 |
|------|------|------|
| `code` | Number | 0 代表成功 |
| `msg` | String | 錯誤訊息 |
| `page_total` | Number | 總頁數 |
| `page_now` | Number | 目前頁數 |
| `data_total` | Number | 總資料數 |
| `data` | Array | 發票陣列 |

---

### 6. 發票檔案下載

**端點：** `POST /json/invoice_file`

下載發票 PDF 檔案。載具發票中獎後才可下載，非載具發票可無限次下載。

#### 請求參數

```json
{
    "type": "order",
    "order_id": "P202212010001",
    "download_style": 0
}
```

| 欄位 | 類型 | 描述 |
|------|------|------|
| `type` | String | order (訂單編號) 或 invoice (發票號碼) |
| `order_id` | String | 訂單編號 |
| `invoice_number` | String | 發票號碼 |
| `download_style` | Number | 下載樣式 (見下表) |

**下載樣式：**

| 樣式代碼 | 適用範圍 | 說明 |
|---------|---------|------|
| `0` | 有統編 / 無統編 | A4 整張 (無統編需雙面列印) |
| `1` | 有統編 | A4 (地址+A5) |
| `2` | 有統編 | A4 (A5x2) |
| `3` | 有統編 | A5 |

#### 回應格式

```json
{
    "code": 0,
    "msg": "",
    "data": {
        "file_url": "https://invoice.amego.tw/user/invoice_print_type?token=..."
    }
}
```

> 檔案連結僅 10 分鐘有效

---

### 7. 發票列印

**端點：** `POST /json/invoice_print`

產出熱感應機列印格式字串。

> 注意: 0 元發票無法產生 QRCode，所以無法列印發票正本及補印。

#### 請求參數

```json
{
    "type": "order",
    "order_id": "P202212010001",
    "printer_type": 2,
    "print_invoice_type": 1,
    "print_invoice_detail": 1
}
```

| 欄位 | 類型 | 描述 |
|------|------|------|
| `type` | String | order 或 invoice |
| `order_id` | String | 訂單編號 |
| `invoice_number` | String | 發票號碼 |
| `printer_type` | Number | 熱感應機型號代碼 |
| `printer_lang` | Number | 熱感應機編碼 (1:BIG5 2:GBK 3:UTF-8) |
| `print_invoice_type` | Number | 1:發票正本 2:發票補印 3:單印明細 |
| `print_invoice_detail` | Number | 1:列印明細 0:不列印 (打統編一律列印) |

#### 回應格式

```json
{
    "code": 0,
    "msg": "",
    "data": {
        "base64_data": "G0AbQ............."
    }
}
```

---

## 折讓作業

### 1. 開立折讓

**端點：** `POST /json/g0401`

折讓已開立的發票。

#### 請求參數

```json
[
    {
        "AllowanceNumber": "3821061800001",
        "AllowanceDate": "20210618",
        "AllowanceType": 2,
        "BuyerIdentifier": "0000000000",
        "BuyerName": "蕭XX",
        "BuyerAddress": "",
        "BuyerTelephoneNumber": "",
        "BuyerEmailAddress": "",
        "ProductItem": [
            {
                "OriginalInvoiceDate": 20210520,
                "OriginalInvoiceNumber": "NW93016392",
                "OriginalDescription": "超聲波清洗機",
                "Quantity": 2,
                "UnitPrice": 2180,
                "Amount": 4360,
                "Tax": 218,
                "TaxType": 1
            }
        ],
        "TaxAmount": 218,
        "TotalAmount": 4360
    }
]
```

| 欄位 | 類型 | 必填 | 描述 |
|------|------|------|------|
| `AllowanceNumber` | String | Y | 折讓單編號，不可重複，不可超過 16 字 |
| `AllowanceDate` | String | Y | 折讓單日期 (Ymd) |
| `AllowanceType` | Number | Y | 1:買方開立折讓證明單 2:賣方折讓證明通知單 |
| `BuyerIdentifier` | String | Y | 買方統編，無則填 `0000000000` |
| `BuyerName` | String | Y | 買方名稱 |
| `BuyerAddress` | String | N | 買方地址 |
| `BuyerTelephoneNumber` | String | N | 買方電話 |
| `BuyerEmailAddress` | String | N | 買方電子信箱 |
| `ProductItem` | Array | Y | 商品陣列，最多 9999 筆 |
| `TaxAmount` | Number | Y | 營業稅額 |
| `TotalAmount` | Number | Y | 金額合計 (不含稅) |

**ProductItem 欄位：**

| 欄位 | 類型 | 描述 |
|------|------|------|
| `OriginalInvoiceNumber` | String | 原發票號碼 |
| `OriginalInvoiceDate` | Number | 原發票日期 (Ymd) |
| `OriginalDescription` | String | 原品名，不可超過 256 字 |
| `Quantity` | Number | 數量 |
| `UnitPrice` | Number | 單價 (不含稅) |
| `Amount` | Number | 小計 (不含稅) |
| `Tax` | Number | 稅金 |
| `TaxType` | Number | 課稅別：1 應稅、2 零稅率、3 免稅 |

---

### 2. 作廢折讓

**端點：** `POST /json/g0501`

作廢已開立的折讓單。

#### 請求參數

```json
[
    {
        "CancelAllowanceNumber": "3821061800001"
    }
]
```

---

### 3. 折讓狀態查詢

**端點：** `POST /json/allowance_status`

查詢折讓單的上傳狀態。

---

### 4. 折讓查詢

**端點：** `POST /json/allowance_query`

查詢折讓單詳細內容。

---

### 5. 折讓列表

**端點：** `POST /json/allowance_list`

取得折讓單主檔資料列表。

---

### 6. 折讓檔案下載

**端點：** `POST /json/allowance_file`

下載折讓單 PDF 檔案 (可無限次下載)。

---

### 7. 折讓列印

**端點：** `POST /json/allowance_print`

產出折讓單熱感應機列印格式字串。

---

## 其他功能

### 1. 手機條碼查詢

**端點：** `POST /json/barcode`

查詢手機條碼是否正確。

```json
{
    "barCode": "/TRM+O+P"
}
```

---

### 2. 公司名稱查詢

**端點：** `POST /json/ban_query`

查詢統編對應的公司名稱 (資料來源：財政部財政資訊中心)。

```json
[
    {
        "ban": "28080623"
    },
    {
        "ban": "85101991"
    }
]
```

**回應範例：**

```json
{
    "code": 0,
    "msg": "",
    "data": [
        {
            "ban": "28080623",
            "name": "光貿科技股份有限公司"
        },
        {
            "ban": "85101991",
            "name": "紅磚數位有限公司"
        }
    ]
}
```

---

### 3. 所有字軌資料

**端點：** `POST /json/track_all`

取得該公司在加值中心的所有字軌資料 (三層結構)。

---

### 4. 伺服器時間查詢

**端點：** `GET /json/time`

查詢目前伺服器時間 (不需要帶入 invoice、data、time 也不須計算 sign)。

**回應範例：**

```json
{
    "timestamp": 1683776130,
    "text": "2023/05/11 11:35:30",
    "year": 2023,
    "month": 5,
    "day": 11,
    "hour": 11,
    "minute": 35,
    "second": 30
}
}
```

---

### 5. 獎項定義

**端點：** `POST /json/lottery_type`

取得中獎發票類型定義 (data 欄位不需要傳入資料)。

---

### 6. 中獎發票查詢

**端點：** `POST /json/lottery_status`

查詢中獎的發票，建議雙月 1 號才查詢 (例如 9-10 月的發票，11/25 開獎，建議 12/1 再查詢)。

```json
{
    "Year": 2022,
    "Period": 3
}
```

**Period 期別：**
- 0: 01-02 月
- 1: 03-04 月
- 2: 05-06 月
- 3: 07-08 月
- 4: 09-10 月
- 5: 11-12 月

---

## 自行配號專用

### 1. 字軌取號

**端點：** `POST /json/track_get`

取發票字軌，只能取用字軌類型為「API 配號」的字軌 (1 本 = 50 張發票)。

---

### 2. 字軌狀態

**端點：** `POST /json/track_status`

查詢發票字軌配號狀態 (只會回傳「API 配號」類型的字軌)。

---

### 3. 開立發票 (API 配號)

**端點：** `POST /json/f0401_custom`

需自行指定發票號碼、發票日期時間及隨機碼。

> 注意: 若有傳入熱感應機型號代碼，一次只限制上傳一張。

#### 額外必填欄位

| 欄位 | 類型 | 描述 |
|------|------|------|
| `InvoiceNumber` | String | 發票號碼 (英文 2 碼 + 數字 8 碼) |
| `InvoiceDate` | String | 發票日期 (YYYYMMDD) |
| `InvoiceTime` | String | 發票時間 (HH:MM:SS) |
| `RandomNumber` | String | 隨機碼 (4 碼數字) |
| `PrintMark` | String | 列印註記 (Y:列印 N:不列印) |

---

## 錯誤代碼

### 通用錯誤代碼

| 代碼 | 說明 |
|------|------|
| `0` | 成功 |
| `1` | 參數錯誤 |
| `2` | 簽章驗證失敗 |
| `3` | 時間戳記誤差過大 (超過 ±60 秒) |
| `4` | 統一編號不存在 |
| `5` | 訂單編號重複 |
| `100` | 發票號碼不存在 |
| `101` | 發票已作廢 |
| `102` | 發票已註銷 |
| `200` | 折讓單號碼重複 |
| `201` | 折讓金額超過原發票金額 |

### 發票開立錯誤

| 代碼 | 說明 |
|------|------|
| `1001` | OrderId 不可為空 |
| `1002` | OrderId 已存在 |
| `1003` | BuyerIdentifier 格式錯誤 |
| `1004` | BuyerName 不可為空或無效值 (0/00/000/0000) |
| `1005` | ProductItem 不可為空 |
| `1006` | ProductItem 欄位不完整 |
| `1007` | 金額計算錯誤 |
| `1008` | TaxType 與 ProductItem TaxType 不符 |
| `1009` | 零稅率發票缺少必填欄位 (CustomsClearanceMark/ZeroTaxRateReason) |
| `1010` | 載具格式錯誤 |
| `1011` | 捐贈碼格式錯誤 |
| `1012` | 打統編發票不可使用載具或捐贈 |

### 發票作廢錯誤

| 代碼 | 說明 |
|------|------|
| `2001` | 發票號碼不存在 |
| `2002` | 發票已作廢 |
| `2003` | 發票已超過作廢期限 |
| `2004` | B2B 交換發票無法作廢 (需由買方退回) |

### 折讓單錯誤

| 代碼 | 說明 |
|------|------|
| `3001` | AllowanceNumber 不可為空 |
| `3002` | AllowanceNumber 已存在 |
| `3003` | 原發票號碼不存在 |
| `3004` | 折讓金額超過可折讓額度 |
| `3005` | 折讓單商品與原發票不符 |

---

## 補充說明

### 光貿會員載具規則

使用光貿會員載具 (CarrierType = `amego`) 時：

1. **載具顯碼/隱碼格式：**
   - `a` + 手機號碼，例如：`a0912345678`
   - 電子信箱，例如：`test@example.com`

2. **注意事項：**
   - 載具顯碼或隱碼帶入電子信箱，並不會發送信件
   - 若想發送信件，請另外填寫 `BuyerEmailAddress` 欄位

### 統一編號、載具、捐贈碼檢查

**統編檢查邏輯：**
- 參考財政部「營利事業統一編號檢查碼邏輯修正說明」
- 可使用 `/json/ban_query` API 驗證統編與公司名稱

**載具與捐贈互斥規則：**
- 有統編：不可使用載具或捐贈
- 無統編：載具與捐贈二擇一
- 捐贈：不可使用載具
- 載具：不可捐贈

**手機條碼格式：**
- 以 `/` 開頭，共 8 碼
- 可使用 `/json/barcode` API 驗證

**自然人憑證格式：**
- 2 碼英文大寫 + 14 碼數字，共 16 碼

---

## 開立發票與自行配號說明

### 開立發票 (自動配號) `/json/f0401`
- 光貿會自動分配發票號碼、開立時間及隨機碼
- 適合大部分情況使用
- 系統會按照後台「發票字軌列表」的排序開立
- 可透過 `TrackApiCode` 指定特定字軌

### 開立發票 (API 配號) `/json/f0401_custom`
- 需自行指定發票號碼、日期時間、隨機碼
- 適合需要自行管理發票號碼的情況
- 需先透過 `/json/track_get` 取得字軌
- 發票號碼必須在取得的字軌範圍內

---

## 相關文件

- [速買配 API 規格](./SMILEPAY_API_REFERENCE.md)
- [綠界 API 規格](./ECPAY_API_REFERENCE.md)
- [發票開立流程](./INVOICE_FLOW.md)

---

## 聯絡客服

如有任何問題，請聯絡光貿客服：
- **官方網站**：https://www.amego.tw
- **客服信箱**：請至官網查詢
- **測試後台**：https://invoice.amego.tw/

---

## 開發筆記 (踩坑紀錄)

> 以下是實際整合光貿電子發票 API 時遇到的問題與解決方案，供後續開發參考。

### 1. 測試與正式環境共用 URL

**問題描述：**
與綠界、速買配不同，光貿的測試與正式環境使用**同一個 API URL** (`https://invoice-api.amego.tw`)，差別只在於使用的 `統編` 和 `App Key`。

**解決方案：**
```typescript
// 光貿測試與正式共用同一個 API URL，差別在於使用的 key
// isProd 只是標記，不影響 API URL
private API_BASE_URL = 'https://invoice-api.amego.tw'
```

不需要根據環境切換 URL，只需要在設定頁面讓使用者輸入正確的測試/正式金鑰即可。

---

### 2. 必填欄位容易遺漏

**問題描述：**
開立發票時 API 回傳錯誤，原因是遺漏了以下必填欄位：

- `FreeTaxSalesAmount` - 免稅銷售額（即使為 0 也必須填）
- `ZeroTaxSalesAmount` - 零稅率銷售額（即使為 0 也必須填）
- `TaxRate` - 稅率（必須填入字串 "0.05"）
- `ProductItem[].TaxType` - 每個商品的課稅別（必填）

**解決方案：**
```typescript
const amegoData = {
    // ... 其他欄位
    SalesAmount: salesAmount,
    FreeTaxSalesAmount: 0,      // 容易遺漏！即使為 0 也必填
    ZeroTaxSalesAmount: 0,      // 容易遺漏！即使為 0 也必填
    TaxAmount: taxAmount,
    TotalAmount: totalAmount,
    TaxType: 1,
    TaxRate: '0.05',            // 容易遺漏！必填
    ProductItem: data.ProductItem?.map(item => ({
        Description: item.Description,
        Quantity: item.Quantity,
        UnitPrice: item.UnitPrice,
        Amount: item.Amount,
        TaxType: 1,             // 容易遺漏！每個商品都要有 TaxType
    })) || [],
}
```

---

### 3. 隨機碼 (random_number) 必須儲存

**問題描述：**
光貿開立發票成功後會回傳 `random_number`（隨機碼），這個值在列印發票時會用到。如果沒有儲存，可能導致列印時出現問題。

**解決方案：**
1. 在 API 回應中正確取得並回傳 `randomNumber`：
```typescript
return {
    success: result.code === 0,
    code: result.code,
    msg: result.msg,
    invoiceNumber: result.invoice_number,
    randomNumber: result.random_number, // [重要] 記得回傳隨機碼
    raw: result
}
```

2. 在資料庫中儲存隨機碼：
```typescript
await prisma.financialRecord.update({
    where: { id: recordId },
    data: {
        invoiceNo: result.invoiceNumber,
        invoiceDate: new Date(),
        invoiceRandomNum: result.randomNumber, // [重要] 儲存隨機碼
        // ...
    },
})
```

---

### 4. B2B vs B2C 金額計算差異 (DetailVat)

**問題描述：**
光貿使用 `DetailVat` 欄位來區分含稅/未稅價格計算方式：
- `DetailVat = 0` - 未稅價（B2B 三聯式使用）
- `DetailVat = 1` - 含稅價（B2C 二聯式使用，預設值）

**解決方案：**
```typescript
const isB2B = data.IsB2B === true

// B2C: SalesAmount = 含稅總額, TaxAmount = 0, TotalAmount = 含稅總額
// B2B: SalesAmount = 未稅, TaxAmount = 稅額, TotalAmount = 含稅
const salesAmount = isB2B ? (data.SalesAmount || 0) : (data.TotalAmount || data.SalesAmount || 0)
const taxAmount = isB2B ? (data.TaxAmount || 0) : 0
const totalAmount = isB2B ? (data.TotalAmount || salesAmount + taxAmount) : salesAmount

const amegoData = {
    // ...
    DetailVat: isB2B ? 0 : 1,  // [重要] B2B 使用未稅價 (0)，B2C 使用含稅價 (1)
    SalesAmount: salesAmount,
    TaxAmount: taxAmount,
    TotalAmount: totalAmount,
}
```

---

### 5. 發票列印需綁定服務商

**問題描述：**
如果使用者用光貿開立發票，之後將預設服務商切換成其他（如速買配），點選列印時會使用速買配的 API 去查詢光貿開立的發票，導致「查詢不到該發票」錯誤。

**解決方案：**
1. 開立發票時，將使用的服務商記錄到 `FinancialRecord`：
```typescript
// issue-invoice/route.ts
await prisma.financialRecord.update({
    where: { id: recordId },
    data: {
        invoiceNo: result.invoiceNumber,
        invoiceProvider: actualProvider as InvoiceProvider, // [重要] 儲存開立時使用的服務商
        // ...
    },
})
```

2. 列印發票時，優先使用記錄中的服務商：
```typescript
// print-invoice/route.ts
const service = record.invoiceProvider
    ? InvoiceServiceFactory.getService(record.invoiceProvider)  // [重要] 使用開立時的服務商
    : await InvoiceServiceFactory.getServiceForUser(userId)     // 降級：使用使用者預設
```

---

### 6. 列印發票 API 回傳 PDF URL

**問題描述：**
光貿的列印發票是透過 `/json/invoice_file` API 取得 PDF 檔案的臨時 URL，然後前端開啟該 URL。URL 有效期限只有 10 分鐘。

**解決方案：**
```typescript
async printInvoice(userId: string, invoiceNumber: string): Promise<InvoicePrintResponse> {
    const settings = await this.getUserInvoiceSettings(userId)

    const data = {
        type: 'invoice',
        invoice_number: invoiceNumber,
        download_style: 0 // A4 整張
    }

    // ... 簽章計算

    const response = await fetch(`${this.API_BASE_URL}/json/invoice_file`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: params.toString(),
    })

    const result = await response.json()

    if (result.code === 0 && result.data?.file_url) {
        return {
            success: true,
            printUrl: result.data.file_url, // [重要] 回傳 PDF URL 給前端開啟
        }
    }
}
```

前端收到 `type: 'redirect'` 時直接開啟該 URL：
```typescript
if (result.type === 'redirect' && result.url) {
    window.open(result.url, '_blank')
}
```

---

### 7. 實作檔案參考

| 檔案 | 說明 |
|------|------|
| `lib/services/amego-service.ts` | 光貿 API 服務實作 |
| `lib/services/invoice-service-factory.ts` | 發票服務工廠 |
| `app/api/v1/financials/[id]/issue-invoice/route.ts` | 開立發票 API |
| `app/api/v1/financials/[id]/print-invoice/route.ts` | 列印發票 API |

---

最後更新：2026/01/28
文件版本：MIG 4.0
