# 即時／同城配送（On-demand Delivery）在台灣

> 涵蓋: Lalamove、pandago（foodpanda）、Uber Direct
> Lalamove 詳細規格見 [lalamove-logistics-api.md](lalamove-logistics-api.md)

## 0. 這個分類跟其他物流不同在哪

本 skill 收錄的其他物流（超取、宅配）都是**批次型**：建單 → 出貨 → 數日後送達，以「單」為單位。即時配送是**派遣型**：報價 → 立即派車 → 數十分鐘內送達，以「趟」為單位。

差異直接影響串接設計：

| 面向 | 批次物流（超取／宅配）| 即時配送 |
|---|---|---|
| 報價 | 費率表固定，可預先算 | **必須先呼叫 API 取得即時報價**，且報價有效期短 |
| 建單時機 | 出貨當下 | 消費者下單當下或稍後派遣 |
| 取消 | 出貨前可取消 | **司機接單後取消多半要付費**（見 §5） |
| 追蹤 | 貨態代碼（數小時～數日更新）| **司機即時座標** |
| 失敗處理 | 退回寄件人 | 需重新派遣或人工介入 |
| 服務範圍 | 全台 | **限同城／特定半徑** |

> ⚠️ 把即時配送套用批次物流的資料模型（先建單再出貨）會不合用——報價會過期、司機座標無處可放。

## 1. 三家對照

| | Lalamove | pandago | Uber Direct |
|---|---|---|---|
| 母公司 | Lalamove | Delivery Hero（foodpanda）| Uber |
| 台灣可用 | ✅ 官方文件列台灣 | ✅ **官方 API 文件列 `tw`** | ⚠️ 見 §4 |
| 文件公開 | ✅ 免登入 | ✅ 免登入（Delivery Hero ODR）| ✅ 免登入 |
| 認證 | HMAC-SHA256 自簽 | **OAuth 2.0 + RSA 簽的 JWT assertion** | OAuth 2.0 client_credentials |
| 取得憑證 | 開發者後台 | **須洽 ODR 窗口申請** | 商家後台 |
| 報價 | 先報價後下單，效期 5 分鐘 | `POST /orders/fee` 與 `/orders/time` 分開 | `POST .../delivery_quotes`，回傳 `expires` |
| 司機座標 | ✅ | ✅ `GET /orders/{id}/coordinates` | ✅ `courier.location` |
| 尺寸限制 | 依車型 | **保溫箱 34×34×36 cm、前踏板 30×20×27 cm，合計 ≤ 20 kg** | 依方案 |
| 貨到收款 | — | `CASH_ON_DELIVERY`／`CARD_ON_DELIVERY` | — |
| 取消 | 媒合後 6 分鐘寬限期 | **外送夥伴接單後不能用 API 取消** | 隨時可取消，費用依階段 |

## 2. pandago（foodpanda）

pandago 屬 Delivery Hero 的 **On Demand Rider（ODR）API**，同一套 API 也服務 Glovo、Talabat 等品牌。

### 環境

| 環境 | Base URL |
|---|---|
| 台灣正式 | **`https://pandago-api-apse.deliveryhero.io/tw/api/v1`** |
| 台灣 Stage | `https://api-infra-ap-southeast-1.stg.ondemandrider.net/tw/api/v1` |
| 公開 Sandbox | `https://pandago-api-sandbox.deliveryhero.io/sg/api/v1`（新加坡） |

> 公開 Sandbox 只有新加坡，地址、費率、涵蓋範圍都是新加坡的；台灣的服務範圍與計價要在台灣 Stage 或正式環境驗證。

### 認證

1. 自行產生 RSA 2048 金鑰對，公鑰交給 ODR 窗口
2. ODR 窗口提供 `ClientID`、`KeyID`、`Scope`（格式 `pandago.api.{國碼}.*`，台灣為 `pandago.api.tw.*`）
3. 以私鑰簽 JWT（RS256）：header `kid` = KeyID；payload `iss`、`sub` = ClientID，`jti` 隨機 UUID，`exp` 未來時間，`aud` **固定 `https://sts.deliveryhero.io`**（測試與正式皆同）
4. `POST /oauth2/token`：`grant_type=client_credentials`、`client_assertion_type=urn:ietf:params:oauth:client-assertion-type:jwt-bearer`、`client_assertion=<JWT>`

> ⚠️ 這是 14 家 provider 中**唯一使用 JWT assertion（private_key_jwt）**的。既有的 HMAC 或 API Key 程式碼完全不能沿用。

### 端點

| 操作 | Method | 路徑 |
|---|---|---|
| 建立／更新門市（Outlet） | PUT／PATCH | `/outlets/{client_vendor_id}` |
| 查詢門市 | GET | `/outlets/{client_vendor_id}`、`/outletList` |
| 費用估算 | POST | `/orders/fee` |
| 時間估算 | POST | `/orders/time` |
| 建立訂單 | POST | `/orders` |
| 查詢訂單 | GET | `/orders/{order_id}` |
| 更新訂單 | PUT | `/orders/{order_id}` |
| 取消訂單 | DELETE | `/orders/{order_id}` |
| 司機座標 | GET | `/orders/{order_id}/coordinates` |
| 取件／送達／退回證明 | GET | `/orders/proof_of_pickup/{order_id}`、`proof_of_delivery`、`proof_of_return` |
| 報價後確認 | POST | `/quotes`、`/quotes/{quoteId}` |

> 費用與時間是**兩支獨立端點**，跟 Lalamove 一次回傳報價＋預計時間不同。要同時顯示兩者需呼叫兩次。
> 所有訂單都應從 Outlet 發出：`sender.client_vendor_id` 帶 Outlet ID 為建議做法；同時提供 Outlet 與寄件人明細時以 Outlet 為準。

### 建立訂單 `POST /orders`

| 欄位 | 必填 | 說明 |
|---|:---:|---|
| `client_order_id` | | 商家訂單編號 |
| `sender.client_vendor_id` | | Outlet ID（建議）；或改帶 `sender.name`／`phone_number`／`location` |
| `recipient.name`、`recipient.phone_number` | ● | 電話為 E.164（`+886…`） |
| `recipient.location.address`／`latitude`／`longitude` | ● | 台灣可只用座標或只用地址；地址依郵政格式、不含樓層與店名，例如 `5 Lane 80 Taiyuen Road, Datong District, Taipei City 10349` |
| `recipient.notes`、`sender.notes` | | 給外送夥伴的取件／送件說明 |
| `payment_method` | ● | `PAID` 已付款／`CASH_ON_DELIVERY` 外送夥伴收現金／`CARD_ON_DELIVERY` 送達刷卡 |
| `amount` | | 訂單金額 |
| `description` | ● | 商品描述 |
| `coldbag_needed` | | 是否需要保冷袋 |
| `preordered_for` | | 預約**送達**時間（unix timestamp），45 分鐘～7 天後；立即派送請給 `null`，不要給 `0` |
| `packaging.size`／`weight` | | `small` 鞋盒／`medium` 背包／`large` 汽車；重量公斤 |
| `pickup_tasks.pickup_code` | | 取件時外送夥伴需報出的代碼 |
| `delivery_tasks.age_validation_required` | | 送達時驗年齡（需先與窗口確認開通） |
| `delivery_tasks.handover_confirmation.drop_off` | | `PIN`／`NONE`（Beta，部分國家） |
| `products[]` | | `name`、`external_id`、`price_amount`（貨幣最小單位）；可用於部分退款 |
| `currency_code` | | ISO 4217 |

回應 `201`：`order_id`、`status`、`delivery_fee`、`distance`（公尺）、`timeline.estimated_pickup_time`／`estimated_delivery_time`、`driver`。`GET /orders/{id}` 另有 `tracking_link`、`status_history`、`proof_of_*_url`，取消時有 `cancellation.source`／`reason`。

錯誤：`400` 參數錯誤、`401` 未授權、`404` Outlet 不存在、`422` 違反業務規則。

### 訂單狀態

`NEW` → `RECEIVED` → `WAITING_FOR_TRANSPORT` → `ASSIGNED_TO_TRANSPORT` → `COURIER_ACCEPTED_DELIVERY` → `NEAR_VENDOR` → `PICKED_UP` → `COURIER_LEFT_VENDOR` → `NEAR_CUSTOMER` → `DELIVERED`；另有 `DELAYED`（預計送達時間已更新）、`CANCELLED`、`RETURNED_TO_VENDOR`。

### 取消 `DELETE /orders/{order_id}`

- **外送夥伴接單後就不能取消**，會回 `409 Uncancellable`；成功回 `204`
- body `reason`：`DELIVERY_ETA_TOO_LONG`、`MISTAKE_ERROR`、`REASON_UNKNOWN`

### 狀態回呼

ODR 會 POST 到商家設定的 callback URL，內容含 `order_id`、`status`、`timeline`、`driver`（有外送夥伴時含座標）、取消時的 `cancellation`。可向營運窗口申請簽章：header `X-Signature-SHA256` = hex(HMAC-SHA256(secret, 原始 body))。

## 3. Uber Direct

### 認證

| 項目 | 值 |
|---|---|
| Token 端點 | `https://auth.uber.com/oauth/v2/token` |
| grant_type | `client_credentials` |
| scope | **`eats.deliveries`** |
| API Base | `https://api.uber.com/v1` |

Token 請求用 `application/x-www-form-urlencoded`；後續 API 呼叫用 `application/json`，以 Bearer token 帶入 Authorization header。

> 💡 **Token 有效期 30 天（2,592,000 秒）**，官方明文建議快取而非每次重新產生。這與 Lalamove（每次請求都簽章）、pandago（JWT assertion）的模式都不同——Uber Direct 這邊反而要注意**別把 token 當短期憑證反覆申請**。

### Direct API 端點

`customer_id` 為組織 ID（UUID 或 `cus_` 開頭），`delivery_id` 以 `del_` 開頭。

| 操作 | Method | 路徑 |
|---|---|---|
| 建立報價 | POST | `/customers/{customer_id}/delivery_quotes` |
| 建立配送 | POST | `/customers/{customer_id}/deliveries` |
| 列出配送 | GET | `/customers/{customer_id}/deliveries` |
| 查詢配送 | GET | `/customers/{customer_id}/deliveries/{delivery_id}` |
| 更新配送 | POST | `/customers/{customer_id}/deliveries/{delivery_id}` |
| 取消配送 | POST | `/customers/{customer_id}/deliveries/{delivery_id}/cancel` |
| 送達證明 | POST | `/customers/{customer_id}/deliveries/{delivery_id}/proof-of-delivery` |

### 建立報價

必填 `pickup_address`、`dropoff_address`（**JSON 字串**，例如 `"{\"street_address\":[\"…\"],\"city\":\"…\",\"zip_code\":\"…\",\"country\":\"…\"}"`）；選填座標、`pickup_ready_dt`／`pickup_deadline_dt`／`dropoff_ready_dt`／`dropoff_deadline_dt`（RFC 3339）、電話、`manifest_total_value`（貨幣最小單位）、`external_store_id`。

回應：`id`（`dqt_` 開頭）、`fee`、`currency`、`expires`、`dropoff_eta`、`duration`、`pickup_duration`。

### 建立配送

| 欄位 | 必填 | 說明 |
|---|:---:|---|
| `pickup_name`、`pickup_address`、`pickup_phone_number` | ● | 電話格式 `^\+[0-9]+$` |
| `dropoff_name`、`dropoff_address`、`dropoff_phone_number` | ● | 同上 |
| `manifest_items` | ● | 品項清單，會顯示在外送夥伴 App |
| `quote_id` | | 先前報價的 ID |
| `pickup_latitude`／`longitude`、`dropoff_latitude`／`longitude` | | 建議提供，提高定位精準度 |
| `pickup_notes`、`dropoff_notes`、`dropoff_seller_notes` | | 各 ≤ 280 字 |
| `pickup_verification`、`dropoff_verification`、`return_verification` | | 拍照、掃條碼、簽名、身分驗證等 |
| `deliverable_action` | | `deliverable_action_meet_at_door`（預設）／`deliverable_action_leave_at_door` |
| `undeliverable_action` | | `return`（預設）／`leave_at_door`／`discard` |
| `pickup_ready_dt` | | 須在 30 天內 |
| `pickup_deadline_dt` | | 比 `pickup_ready_dt` 晚至少 10 分鐘，且距現在至少 20 分鐘 |
| `dropoff_ready_dt` | | ≤ `pickup_deadline_dt` |
| `dropoff_deadline_dt` | | 比 `dropoff_ready_dt` 晚至少 20 分鐘，且 ≥ `pickup_deadline_dt` |
| `manifest_reference` | | 與 `external_id` 的組合須唯一 |
| `idempotency_key` | | 防重複建單，預設保留 60 分鐘 |
| `tip` | | 貨幣最小單位；回應的 `fee` 已含小費 |
| `external_store_id` | | 建單有用時，報價也必須帶 |

錯誤：`402 customer_suspended`、`403 customer_blocked`、`409 duplicate_delivery`、`429 customer_limited`。

### 狀態與查詢

列出配送的 `filter`：`pending`、`pickup`、`pickup_complete`、`dropoff`、`delivered`、`canceled`、`returned`、`ongoing`。查詢結果含 `status`、`courier`（姓名、車種、電話、座標）、`tracking_url`、`undeliverable_action`／`undeliverable_reason`。

### 取消

`POST .../cancel`，選填 `cancelation_reason`（區分大小寫）：`out_of_items`、`store_closed`、`customer_called_to_cancel`、`store_too_busy`、`courier_delayed_en_route_to_pickup`、`too_expensive`、`delivery_vehicle_too_small`、`no_courier_assigned`、`other`（需搭配 `additional_description`）。

### 服務範圍

官方行銷頁只說「available in 2 dozen countries」，未逐一列出。配送半徑約 **10 英里**內，時效可選 2 小時內／當日／最多預約 30 天後。

## 4. ⚠️ Uber Direct 的台灣可用性：有間接證據，無官方確認

**支持的證據：**
- 存在台灣在地化的商家頁 `merchants.ubereats.com/tw/zh-tw/`
- Uber Help 有中文的「Uber Direct 控制台」章節
- 台灣的系統整合商（如 weiby.tw）公開販售「Uber Eats／Uber Direct／foodpanda／pandago」的 API 串接服務

**缺乏的證據：**
- Uber 官方**沒有**逐一列出支援國家的清單，台灣未被點名
- 開發者文件未標示市場代碼或區域端點；範例地址全是美國

**結論**：可用性高度可能，但**本 skill 不將其標為已確認**。與 pandago 不同——pandago 的官方 API 文件直接列出 `tw` 的正式與 Stage 端點，那是明確的一手證據。

實務建議：導入前先向 Uber 業務確認貴公司所在區域是否在服務範圍內，不要依賴行銷頁的在地化路徑判斷。

## 5. 取消規則與費用

### Lalamove（台灣官方 FAQ）

| 情境 | 規則 |
|---|---|
| 尚未媒合司機 | 可直接取消 |
| 即時訂單 | 媒合後 **6 分鐘**內可取消 |
| 預約訂單 | 預定取貨時間前 **45 分鐘**內可取消 |
| 司機已接單並前往、或已抵達 | 收取該訂單**起始價 50%** 作為取消費 |
| 超過寬限期 | 須聯繫客服，可能收取取消費 |

> 以上為 Lalamove 台灣 FAQ 對一般下單的說明；API 下單是否適用同一規則需向 Lalamove 確認。

### pandago（foodpanda 商家專區「責任規範與費用收取／補償」）

API 層面：外送夥伴接單後不能取消（`409`）。依原因的費用：

| 取消原因 | 說明 | 運費收取 | 返送運費收取 | 訂單補償 |
|---|---|:---:|:---:|:---:|
| 商家失誤 | 媒合前商家取消，原因「錯誤的訂單資訊」 | 否 | 否 | 否 |
| 其他原因 | 媒合前商家取消，原因「顧客取消訂單」 | 否 | 否 | 否 |
| 商家認為媒合時間過長 | 媒合前商家取消，原因「有其他交貨方式可用」 | 否 | 否 | 否 |
| 商家已打烊或因任何原因需求取消 | **媒合到外送夥伴後**商家取消 | 是 | 是 | 否 |
| 錯誤收件地址 | 商家輸入地址錯誤或實際地址在範圍外 | 是 | 是 | 否 |
| 聯繫不到客戶 | 抵達後聯繫不到客戶超過 10 分鐘 | 是 | 是 | 否 |
| 客戶問題 | 客戶聯絡商家取消 | 是 | 是 | 否 |
| 客戶無法付款 | 客戶現金不足 | 是 | 是 | 否 |
| 送件錯誤訂單 | 交給外送夥伴的訂單錯誤，客戶拒收 | 是 | 是 | 否 |
| 商家已閉店 | 外送夥伴提供證明 | 是 | 是 | 否 |
| 訂單延遲交付 | 比承諾時間晚 30 分鐘以上，客戶拒收 | 否 | 否 | 否 |
| 外送夥伴失聯 | 接單後失聯，客戶不願等待 | 否 | 否 | 是 |
| 灑餐 | 客戶因溢漏拒收 | 否 | 否 | 是 |
| 遭遇事故 | 外送夥伴途中事故，客戶不願等待 | 否 | 否 | 是 |
| 超出運送範圍 | 外送夥伴接單後拒單 | 否 | 否 | 否 |
| 技術問題／超出營業時間／天氣問題／無法媒合外送夥伴 | | 否 | 否 | 否 |

### Uber Direct（Uber Help「Issues with deliveries: Uber Direct」）

- 可隨時取消（Dashboard 或 API）
- 需要把商品送回的餐廳，必須透過 Uber Direct 支援團隊取消，讓外送夥伴有退回的行程
- 該文章的非台灣版本另列：尚無外送夥伴接單時不收取消或退回費用；取件階段取消不收取消費，但收取件費補償外送夥伴；配送途中取消會收費；配送途中取消並要求退回，收配送費與退回費。**從台灣存取的版本未列費用**，台灣的實際收費需向 Uber 確認

## 6. 選型

| 情境 | 建議 |
|---|---|
| 需要明確的台灣官方端點與文件 | **pandago**（`/tw` 正式與 Stage 端點有官方文件背書）|
| 已有 HMAC 簽章經驗、想快速上線 | **Lalamove**（自簽 HMAC，開發者後台自助取得憑證）|
| 需要多車型／路線最佳化／換司機 | **Lalamove** |
| 小件、標準箱體、需要貨到收款 | **pandago**（≤ 20 kg，`CASH_ON_DELIVERY`）|
| 已在用 Uber Eats 生態 | **Uber Direct**（但先確認台灣服務範圍）|

> 三家都**不是批次物流的替代品**。單日出貨量大、跨縣市、需要超取的情境，仍應走 ECPay／ezShip 等聚合商。即時配送適合的是同城、急件、生鮮這類批次物流做不到的需求。

## 7. 待補

| 項目 | 說明 |
|---|---|
| Uber Direct 台灣可用性與收費 | 官方未列支援國家；台灣版說明頁未列取消費 |
| pandago 台灣運費表 | 官方 API 文件與商家專區皆未列，運費以 `/orders/fee` 即時估算 |

## 8. 來源

- Delivery Hero On Demand Rider API（端點、欄位、狀態、取消、回呼簽章）— https://on-demand-rider-docs.deliveryhero.io/
- foodpanda 商家專區 pandago（尺寸重量、責任規範與費用收取／補償）— https://vendor.foodpanda.com.tw/pandago
- pandago 台灣 — https://pandago.tw/
- Uber Direct API 總覽 — https://developer.uber.com/docs/deliveries/overview
- Uber Direct API Reference（Direct API）— https://developer.uber.com/docs/deliveries/api-reference/daas
- Uber Direct 認證 — https://developer.uber.com/docs/deliveries/guides/authentication
- Uber Help：Issues with deliveries: Uber Direct — https://help.uber.com/en/merchants-and-restaurants/article/issues-with-deliveries-uber-direct-?nodeId=1d5914c7-b638-4d4b-8a18-d2e3cb29217a
- Uber Direct 商家頁（台灣在地化）— https://merchants.ubereats.com/tw/zh-tw/
- Lalamove 台灣 FAQ（取消規則）— https://www.lalamove.com/zh-tw/faq
- Lalamove API — [lalamove-logistics-api.md](lalamove-logistics-api.md)
