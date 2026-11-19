# Lalamove API v3 參考（即時／同城配送）

> Directory edition: reference files and JSON data only, no scripts. Tools under `scripts/`, `examples/` and `tests/` ship in the full edition (npm package `taiwan-logistics-skill`).
> Keys and merchant IDs are set up by the user and passed into the code as parameters; they appear as placeholders such as `<HASH_KEY>`. Published sandbox keys are also shown as placeholders; get them from the provider's official docs. Credential-type field names are shown as `<帳密欄位>`.

> Source: https://developers.lalamove.com/ (v3)
> 範例程式: https://github.com/lalamove/api-examples
> 台灣服務: https://www.lalamove.com/en-tw/business/api-solutions
> 文件公開程度：public

## 0. 為什麼要有這一類

本 skill 原本 7 家 provider 全是**批次型物流**：建立託運單 → 交寄 → 隔日到貨。Lalamove 屬於**即時／同城配送（on-demand delivery）**，模型完全不同：

| 面向 | 批次物流（ECPay/黑貓/超取） | 即時配送（Lalamove） |
|---|---|---|
| 下單前 | 直接建單 | **先報價（quotation），再用報價 ID 下單** |
| 報價效期 | 不適用 | **5 分鐘**內有效 |
| 司機 | 不可見 | 可查詢司機資訊、可更換司機 |
| 修改 | 建單後多半不可改 | 進行中可改一次收件點 |
| 取消 | 需走取消 API | `DELETE /orders/{id}`，僅限尚未媒合或媒合後 5 分鐘內 |
| 時效 | 隔日／指定日 | 數十分鐘 |
| 計價 | 固定運費表 | 動態，含加價（priority fee／小費） |

**適用情境**：餐飲外送、當日到貨、門市取貨後配送、B2B 急件、多點配送。
**不適用**：一般電商包裹（成本高很多）。

`data/logistics-types.csv` 已新增 `ondemand` 類型對應此模式。

## 1. 環境

| 環境 | Base URL |
|---|---|
| Sandbox | `https://rest.sandbox.lalamove.com/v3` |
| Production | `https://rest.lalamove.com/v3` |

## 2. 認證與簽章

HMAC-SHA256。每個請求需三個 header：

| Header | 值 |
|---|---|
| `Authorization` | `hmac <KEY>:<TIMESTAMP>:<SIGNATURE>` |
| `Market` | UN/LOCODE 市場代碼（台灣為 `TW`） |
| `Request-ID` | Nonce（每次請求唯一） |

### 簽章字串

```
HmacSHA256(<TIMESTAMP>\r\n<METHOD>\r\n<PATH>\r\n\r\n<BODY>, <SECRET>)
```

⚠️ 注意是 `\r\n`（CRLF）不是 `\n`，且 PATH 與 BODY 之間是**兩個** CRLF（空行）。這是最常見的簽章對不上原因。

- `TIMESTAMP` 為毫秒 Unix 時間，與 `Authorization` 內的值必須相同；`SIGNATURE` 為小寫 hex
- `PATH` 含 `/v3` 前綴（例如 `/v3/quotations`）；GET 等無 body 的請求，BODY 為空字串
- POST／PATCH 的 body 一律包在 `{"data": {...}}` 內；少了這層會回 `422 ERR_INSUFFICIENT_STOPS`

```python
import hmac, hashlib, time, json, uuid

def build_headers(method, path, body_dict, key, secret, market="TW"):
    ts = str(int(time.time() * 1000))
    body = json.dumps(body_dict, separators=(',', ':')) if body_dict else ""
    raw = f"{ts}\r\n{method}\r\n{path}\r\n\r\n{body}"
    sig = hmac.new(secret.encode(), raw.encode(), hashlib.sha256).hexdigest()
    return {
        "Authorization": f"hmac {key}:{ts}:{sig}",
        "Market": market,
        "Request-ID": str(uuid.uuid4()),
        "Content-Type": "application/json",
    }
```

> 簽章用的 `body` 必須與實際送出的 body **逐字元相同**。用 `json.dumps` 產生一次，同時拿去簽章與送出，不要分別序列化兩次。

## 3. 端點總覽

| 端點 | Method | 用途 |
|---|---|---|
| `/v3/quotations` | POST | 取得報價（含價格明細） |
| `/v3/quotations/{id}` | GET | 查詢報價 |
| `/v3/orders` | POST | 用 quotation ID 建立訂單 |
| `/v3/orders/{id}` | GET | 查詢訂單狀態 |
| `/v3/orders/{id}` | PATCH | 修改送件點（**僅限一次**，`ON_GOING` 且尚未取件；可改、增、刪送件點，至少留 1 個；取件點須與原單相同） |
| `/v3/orders/{id}` | DELETE | 取消訂單（僅 `ASSIGNING_DRIVER`，或轉為 `ON_GOING` 未滿 5 分鐘；否則 `409 ERR_CANCELLATION_FORBIDDEN`）。成功回 `204` |
| `/v3/orders/{id}/drivers/{driverId}` | GET | 查詢司機資訊與座標（預約單取件前 1 小時或司機抵達取件點起才可查，否則 `403`；座標每 10 秒更新） |
| `/v3/orders/{id}/drivers/{driverId}` | DELETE | 更換司機（**媒合後 15 分鐘以上**、取件前才可；body `reason`：`DRIVER_LATE`／`DRIVER_ASKED_CHANGE`／`DRIVER_UNRESPONSIVE`／`DRIVER_RUDE`） |
| `/v3/orders/{id}/priority-fee` | POST | 追加小費／優先費（僅司機接單前；可多次，金額須大於前次並取代前次） |
| `/v3/cities` | GET | 取得 `Market` 下各城市的車型 `services` 與 `specialRequests` |
| `/v3/webhook` | PATCH | 設定 webhook URL（也可在 Partner Portal 設定） |

### 下單欄位重點

| 端點 | 必填 | 選填 |
|---|---|---|
| `POST /v3/quotations` | `serviceType`、`stops`（2–16 個，第 1 個為取件點）、`language`（台灣 `zh_TW`） | `scheduleAt`（UTC、ISO 8601，最多 30 天後；立即單省略）、`specialRequests`、`isRouteOptimized`、`item`、`pricingTierCode` |
| `POST /v3/orders` | `quotationId`、`sender.name`、`sender.phone`、`recipients[]`（`stopId`、`name`、`phone`） | `recipients[].remarks`（≤ 1500 字）、`isPODEnabled`、`metadata`、`partner` |

- `stops[].coordinates.lat`／`lng` 為**字串**；電話一律 E.164（`+886…`）
- `item`（重量、品類、處理指示）目前僅泰國、越南、香港提供
- 所有時間欄位為 UTC
- Lalamove 訂單編號為 19 位數字，要以字串儲存，不要宣告成整數或固定 12 位
- 立即單 2 小時內無司機接單、預約單 `scheduleAt` 後 2 小時無司機接單即 `EXPIRED`

### 訂單狀態

`ASSIGNING_DRIVER` → `ON_GOING`（司機接單）→ `PICKED_UP` → `COMPLETED`；另有 `CANCELED`、`REJECTED`（司機接單後拒單達上限，視同取消、需重新下單）、`EXPIRED`。司機拒單時狀態會退回 `ASSIGNING_DRIVER` 重新媒合。

啟用 POD 時每個送件點另有 `POD.status`：`PENDING`、`DELIVERED`、`SIGNED`、`FAILED`。

### Webhook 事件

`ORDER_STATUS_CHANGED`、`DRIVER_ASSIGNED`、`ORDER_AMOUNT_CHANGED`、`ORDER_REPLACED`（客服改單後換新 orderId）、`WALLET_BALANCE_CHANGED`、`ORDER_EDITED`、`POD_STATUS_CHANGED`、`POP_STATUS_CHANGED`、`DELIVERY_CODE_STATUS_CHANGED`、`ORDER_CREATED`。Webhook URL 必須回 `200`。

### 錯誤與限流

錯誤格式為 `{"errors": [{"id", "message", "detail"}]}`。常見：`402 ERR_INSUFFICIENT_CREDIT`（錢包餘額不足）、`422 ERR_INVALID_QUOTATION_ID`（報價錯誤或過期）、`ERR_OUT_OF_SERVICE_AREA`、`ERR_INVALID_SERVICE_TYPE`、`ERR_INVALID_PHONE_NUMBER`、`429 ERR_RATE_LIMIT_EXCEEDED`。

正式環境限流（每分鐘）：報價、下單、取消、換司機、加價各 100；查報價、查訂單、查司機、查城市各 300（Sandbox 為 30／50）。下單建議每秒不超過 2 筆。

## 4. 標準流程

```
1. GET  /v3/cities                → 取得台灣可用的車型 serviceType、特殊需求 specialRequests
2. POST /v3/quotations            → 傳入取送點，取得 quotationId + 價格明細（5 分鐘有效）
3. POST /v3/orders                → 帶 quotationId 下單
4. webhook / GET /v3/orders/{id}  → 追蹤狀態、取得司機
5. (選) POST …/priority-fee       → 沒司機接單時加價
6. (選) PATCH /v3/orders/{id}     → ON_GOING 期間改一次收件點
7. (選) DELETE /v3/orders/{id}    → 取消
```

> **報價 5 分鐘效期是硬約束。** 若你的結帳流程是「顯示運費 → 使用者慢慢填地址 → 送出」，很容易超時。建議在最終送出前重新報價，或把報價時間戳存起來做過期判斷。

## 5. 重要選項

| 欄位 | 說明 |
|---|---|
| `isRouteOptimized` | `true` 啟用多點路線最佳化（開發者文件有此欄位，但台灣 API 方案頁 FAQ 寫路線最佳化尚未提供，台灣需實測） |
| `isPODEnabled` | `true` 啟用 Proof of Delivery（送達證明） |
| `metadata` | 自訂 key-value，可掛你自己的訂單編號 |
| `pricingTierCode` | 報價時選填（字串）：`"1"` 一般（預設）、`"2"` Priority Tier（加速媒合、較快送達），回傳價格依所選等級計算。官方文件未列適用市場，台灣是否開放需以報價實測或向 Lalamove 確認 |

`metadata` 是把 Lalamove 訂單對回自家系統的建議做法——不要依賴 Lalamove 的 order ID 當主鍵。

## 6. 市場

v3 支援 13 個市場，**含台灣**：日本 `JP`、巴西 `BR`、香港 `HK`、印尼 `ID`、馬來西亞 `MY`、墨西哥 `MX`、菲律賓 `PH`、新加坡 `SG`、**台灣 `TW`**、泰國 `TH`、越南 `VN`、阿聯 `AE`、沙烏地阿拉伯 `SA`。

台灣：`Market: TW`、地址語言 `zh_TW`，服務城市為台北、台中、台南、高雄。

`Market` header 必須正確，否則報價會落在錯誤的城市（不支援的市場回 `422 ERR_INVALID_MARKET`）。實際可用的 `serviceType`（機車／小貨車／貨van…）與費率請以 `GET /v3/cities` 回傳為準，不要寫死。

## 7. 與本 skill 其他 provider 的搭配

實務上電商常見組合：

| 情境 | 建議 |
|---|---|
| 一般電商包裹 | ECPay / ezShip / SmilePay 等聚合商（超取 or 宅配） |
| 當日／急件 | Lalamove |
| 兩者並存 | 依訂單金額／距離／時效在結帳頁分流；退貨一律走批次物流（Lalamove 逆物流成本不划算） |

## 8. 待驗證

- 台灣市場實際可用的 `serviceType` 清單與費率結構（需以 `GET /v3/cities` 實測）
- Webhook payload 結構（官方只列事件名稱，細節在另附的簡報）
- 台灣是否可用 `pricingTierCode: "2"`（Priority Tier）與 `isRouteOptimized`
- pandago（foodpanda）見 [ondemand-delivery.md](ondemand-delivery.md)

## 9. 取得憑證

在 Partner Portal 註冊為 API Partner，Developers 分頁取得金鑰：Sandbox 為 `pk_test`／`sk_test` 開頭，可直接取得；Production 為 `pk_prod`／`sk_prod` 開頭，**須先儲值錢包**才會產生。

## 10. 來源

- API Reference — https://developers.lalamove.com/
- 官方範例（多語言） — https://github.com/lalamove/api-examples
- 台灣 API 方案 — https://www.lalamove.com/en-tw/business/api-solutions
