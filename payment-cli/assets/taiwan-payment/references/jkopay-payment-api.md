# 街口支付 JKOPAY 商家 API 參考

> 官方開放文件: https://open-doc.jkos.com/
> 公司: 街口電子支付股份有限公司（專營電子支付機構）
> Captured: 2026-08-08 · doc_access: **public**（文件站免登入）
> Status: **五大模組已擷取四個** —— 線上支付（§5）、授權扣款（§6）、線下 POS（§8）、inApp OAuth（§9）；街口幣發放待補
> 擷取方式: 文件站為 SPA，WebFetch 深層連結回 404，本次以瀏覽器逐頁取得

## 0. 為什麼收錄

街口是台灣使用量最大的電子支付之一，而且**它是 10 家專營電支中極少數自己開了公開文件站的**（另一家是歐付寶）。多數電支（全支付、悠遊付、一卡通、icash Pay、橘子支）都要簽約才給文件。

對本 skill 有兩個直接價值：

1. **可直接串**——量體夠大時不必透過聚合商抽成
2. **可用來修正推測碼**——`data/payment-methods.csv` 裡 NewebPay/ezPay 的 `JKOPAY?` 等代碼標記為未驗證，街口官方文件可作為交叉比對基準

## 1. 文件站結構

`open-doc.jkos.com` 分五大模組：

| 模組 | 內容 |
|---|---|
| **授權扣款** | 定期付款／訂閱模式的 API 整合 |
| **線上支付** | 網頁與行動應用的交易處理 |
| **線下交易（POS）** | 實體店面支付 |
| **inApp 第三方服務** | Web SDK 與 OAuth 認證 |
| **街口幣發放** | 虛擬積分／獎勵發放 |

每個模組皆含：

- **API 協議規則**——連線標準與規格
- **加簽加密**——安全驗證機制
- **完整 API 列表**——付款、退款、查詢
- **錯誤代碼表**——文件特別強調「代碼意義」與「統一錯誤代碼表」

版權標示：©2022 Jkopay Co. Ltd.

## 2. 能力範圍（與本 skill 其他 provider 對照）

| 能力 | 街口直連 | 走聚合商（ECPay 等） |
|---|---|---|
| 線上付款 | ✅ | ✅ |
| 退款 | ✅ | ✅ |
| 查詢 | ✅ | ✅ |
| **定期扣款／訂閱** | ✅ 授權扣款模組（定期定額 + 不定期不定額，見 §6）| ⚠️ 多數聚合商的街口不支援定期扣款 |
| **實體店 POS** | ✅ | 部分（多走 TWQR） |
| **App 內第三方登入（OAuth）** | ✅ | ❌ |
| **發放街口幣做行銷** | ✅ | ❌ |

> **這張表是選型關鍵**：如果你只是要在結帳頁多一個「街口」按鈕，走 ECPay 的 `DigitalPayment` umbrella 最省事。如果你要做**訂閱制、實體店、或街口幣行銷**，就非得直連不可——這些能力聚合商給不了。

## 3. TWQR 關係

街口是 TWQR（電支跨機構共用平台）的參與機構之一。實體店若採 TWQR 一碼收全部，可涵蓋街口而不必個別串接。詳見 [twqr-ewallet-landscape.md](twqr-ewallet-landscape.md)。

## 4. 其他取得街口的路徑

| 路徑 | 說明 |
|---|---|
| **TapPay** | 有街口專屬文件站 `docs.tappaysdk.com/jko-pay/`（含 Backend 頁），走 Prime → pay-by-prime 流程。見 [tappay-payment-api.md](tappay-payment-api.md) |
| **ECPay** | `ChoosePayment=DigitalPayment` umbrella，消費者於綠界選擇頁挑街口 |
| **PAYUNi** | `JKoPay` 直送代碼（已驗證） |
| **HiTRUSTpay** | 有街口介接方案 |
| **Link Pay（TapPay）** | 連結收款，支援街口 |

## 5. 線上支付 OnlinePay — 完整規格

### 5.1 協議規則

| 項目 | 值 |
|---|---|
| 通訊協定 | **https** |
| Method | POST / GET（依 API） |
| Content-Type | `application/json` |
| charset | UTF-8 |

網域為 `https://[HOST]/platform/...`，`[HOST]` 由街口於簽約時提供。測試環境的付款網域可見 `test-onlinepay.jkopay.app`。

必要 HTTP Header：

| Header | 說明 |
|---|---|
| `api-key` | 街口核發的 API Key |
| `digest` | 本次 request 的 HMAC-SHA256 簽章（見 5.2）|

### 5.2 加簽規則（HMAC-SHA256）

```
digest = HMAC-SHA256( request_payload_utf8, secret_key_utf8 ).hexdigest()
```

三步驟：

1. 將 **request payload 字串**以 UTF-8 編碼為 input byte
2. 將街口核發的 **Secret Key** 以 UTF-8 編碼為 secret key byte
3. 以 HMAC-SHA256 雜湊，轉 **16 進位字串**作為 `digest`

> ⚠️ **簽的是原始 payload 字串本身**，不是排序後的參數串，也不做 URL encode——這與 ECPay 的 `CheckMacValue`（排序＋urlencode＋SHA256）**完全不同路數**。從綠界思維遷移過來最容易在這裡卡住。
> POST 簽 JSON body 原文（含空白與順序，必須與實際送出的 bytes 一致）；GET 簽 query string 原文。

#### 官方驗證範例（可直接拿來對你的實作）

共用測試 Secret Key：

```
r0odDC1e9LHXDmxuvmOv9bgaWLf2CXB2c4gMheoFucVKNMi1K0Id9zwRHJF1r-kdtAKriKgb11VDlo7Kb8R-FQ
```

**POST（Entry API）**

輸入：
```json
{"platform_order_id":"demo-order-001","store_id":"35f12dff-1581-11e9-a054-00505684fd45","currency": "TWD","total_price":10,"final_price":10,"unredeem":10,"result_display_url":"https://display.com","result_url":"https://result-callback.xxx/xxx"}
```
digest：`3577609b058ab85c2d0a00a5421a991979ed6b9f549476e9a82476dc1b70d876`

**GET（Inquiry API）**

輸入：`platform_order_ids=test123,demo-order-001`
digest：`7778b95890af17c5b41e8cef957f4769e7bfecc79e9f9ee555923293ebd8e880`

PHP 一行即可：`$sig = hash_hmac('sha256', $string, $secret);`

> 官方文件站另附一個**線上簽章驗證工具**，可直接貼 payload 與 Secret Key 算出結果比對。

### 5.3 訂單創建 Entry API

`POST https://[HOST]/platform/entry`

電商呼叫後取得街口付款 `payment_url`。**同一 `platform_order_id` 在付款完成前重複呼叫會回同一個付款網址**（冪等）。

#### Request

| 參數 | 型態 | 長度 | 必填 | 說明 |
|---|---|---|---|---|
| `platform_order_id` | string | 60 | ✅ | 平台端交易序號，**需唯一** |
| `store_id` | string | 36 | ✅ | 商店編號，測試/正式環境代碼不同 |
| `currency` | string | 3 | ✅ | ISO 4217，可帶 `TWD` / `JPY` / `USD` |
| `total_price` | decimal | 20,0 | ✅ | 訂單原始金額，**必須 > 0** |
| `final_price` | decimal | 20,0 | ✅ | 實際消費金額，**必須 > 0** |
| `unredeem` | decimal | 20,0 | | 不可折抵金額（不可用街口幣／券支付的部分）|
| `valid_time` | string | 19 | | 訂單有效期限，UTC+8，`yyyy-MM-dd HH:mm:ss` |
| `confirm_url` | string | 500 | | 付款前確認 callback（**必須 https**）|
| `result_url` | string | 500 | ✅ | 付款結果 callback（**必須 https**）|
| `result_display_url` | string | 500 | ✅ | 消費者按「完成」後導向的前端頁（http/https 皆可）|
| `payment_type` | string | | | `onetime` 一次性（預設）／ `regular` 定期定額 |
| `escrow` | bool | | | 是否支持價金保管，預設 `false` |
| `products` | array | | | 商品陣列，**一旦使用，除 `img` 外其餘皆必填** |
| `products.name` | string | 60 | | 商品名稱（UTF-8）|
| `products.img` | string | 500 | | 商品圖片網址 |
| `products.unit_count` | int | | | 數量 |
| `products.unit_price` | decimal | 20,0 | | 單價（原價）|
| `products.unit_final_price` | decimal | 20,0 | | 單價（付款價）|

#### Response

| 參數 | 說明 |
|---|---|
| `result` | Response Code（字串，見 5.6）|
| `message` | 結果訊息或失敗理由 |
| `result_object.payment_url` | 付款導向網址。街口 Server 自動判斷裝置：**電腦／平板回 QRCode 網頁；行動裝置直接導向街口 App**。**長度可能超過 255** |
| `result_object.qr_img` | QRCode 圖檔網址，可嵌入自家付款頁。**長度可能超過 255** |
| `result_object.qr_timeout` | 失效時間戳 |

> ⚠️ **`payment_url` / `qr_img` 欄位長度會超過 255**——資料庫欄位別開 `VARCHAR(255)`，這是實作時的具體地雷。
> ⚠️ `payment_url` 與 QRCode **僅 20 分鐘有效**。只要還在 `valid_time` 期限內，可用同一 `platform_order_id` 再呼叫 Entry API **展延另一個 20 分鐘**。

### 5.4 `confirm_url` — 付款前確認（選用）

`POST`，由**商家實作**。消費者在街口 App 輸入密碼後，街口 Server 會先打這支確認訂單正確性與存貨。

連線規則：**Connection timeout 5 秒 / Read timeout 10 秒 / Retry 3 次**

| 方向 | 內容 |
|---|---|
| 街口送來 | `{"platform_order_id": "kt12345"}` |
| 你要回 | `{"valid": true}` — `valid` 為 bool，`true` 才會繼續扣款 |

> 這是**扣款前的最後一道自家庫存／金額驗證**。做訂閱或限量商品時值得實作；不實作則街口直接扣款。

### 5.5 `result_url` — 付款結果通知（必填）

`POST`，由**商家實作**。付款流程結束且交易成功時街口 callback 通知。

連線規則：Connection timeout 5 秒 / Read timeout 10 秒 / **Retry 最多 12 次，間隔 2^n 秒（1、2、4、8…），約 2 小時內完成**。

商家需回 **HTTP 200**。

| 參數 | 型態 | 說明 |
|---|---|---|
| `transaction.platform_order_id` | string(60) | 平台端交易序號 |
| `transaction.status` | int | 訂單狀態碼，見 5.6 |
| `transaction.tradeNo` | string(25) | **街口端交易序號** |
| `transaction.trans_time` | string | 交易時間，UTC+8，`yyyy-MM-dd HH:mm:ss` |
| `transaction.currency` | string(3) | 付款貨幣 |
| `transaction.final_price` | string | 實際消費金額 |
| `transaction.redeem_amount` | string | 折抵金額＝街口幣＋官方券＋店家券 |
| `transaction.debit_amount` | string | 付款工具實扣金額（折抵後）|
| `transaction.channel_type` | string | `account` 儲值帳戶／`bank` 銀行帳戶／`creditcard` 信用卡 |
| `transaction.redeem_detail.jko_coin_amount` | decimal | 街口幣折抵 |
| `transaction.redeem_detail.official_coupon_amount` | decimal | 官方街口券折抵 |
| `transaction.redeem_detail.store_coupon_amount` | decimal | 店家街口券折抵 |
| `transaction.invoice_vehicle` | string | **街口帳戶發票載具**（可直接帶去開發票）|
| `transaction.maskNo` | string(16) | 信用卡前六後四，格式 `222222******3333` |

**金額恆等式：`final_price = redeem_amount + debit_amount`**

> 💡 **`invoice_vehicle` 是跨 skill 的接點**：街口回傳的載具號碼可直接餵給發票 API 的 `CarrierType=3`（手機條碼）流程。見 [../../taiwan-invoice/references/](../../taiwan-invoice/references/)。
> ⚠️ **對帳要用 `debit_amount` 而非 `final_price`**——街口幣與券折抵的部分不會進你的撥款，這是自建對帳最常見的差異來源。

### 5.6 Response Code 與訂單狀態

Platform APIs 統一回應格式（**欄位皆小寫**，`result` 為**字串**不是數字）：

```json
{ "result": "string", "message": "string or null", "result_object": "object or null" }
```

#### `POST /platform/entry`

| result | message | 觸發條件 |
|---|---|---|
| `000` | null | 成功建立付款連結 |
| `101` | Order is paid | 訂單已付款 |
| `200` | Bad request | 參數錯誤（message 會動態說明哪個欄位）|
| `200` | Store not found | `store_id` 錯誤 |
| `200` | Using the currency unsupported by the Store | `currency` 該商店不支援 |
| `200` | Entry of this store needs identity verification | 該商店訂單需帶 identities 資料 |
| `200` | Order has been used as entry but they do not match with each others | **同一 `platform_order_id` 重複請求，但 `store_id`/`currency`/`total_price`/`final_price` 不一致** |
| `200` | Invalid number of digits for the order currency amount | 幣別小數位檢核失敗 |
| `200` | Order price below limit for this currency | 低於該幣別最低金額（JPY=5 / USD=0.02 / CNY=0.11 / HKD=0.13）|
| `999` | Internal Error | 街口系統非預期錯誤 |

#### `POST /platform/refund`

| result | message | 觸發條件 |
|---|---|---|
| `000` | null | 成功建立退款 |
| `100` | Invaid Order ID | 訂單不存在（*官方原文即拼作 Invaid*）|
| `102` | Order has excessed 180 days cannot be refunded | **超過 180 天退款期限** |
| `105` | Inconsistent remain amount | 剩餘金額不一致 |
| `105` | Inconsistent refund amount | 同一 `refund_order_id` 但 `refund_amount` 不同 |
| `111` | Transaction has been closed | 交易已關帳 |
| `113` | Refund reject due to refund amount exceeds total unreimbursed amount. | **商家餘額不足** |
| `116` | JKOPAY coupon reimbursement failed... | 券退款失敗，需聯繫街口 |
| `117` | JKOPAY Coupon is used in this transaction, and we will only accept full refund | **用券的訂單只接受全額退款** |
| `200` | Invalid number of digits for the order currency amount | 幣別小數位檢核失敗 |
| `922` | Refund amount exceeds order final price | 退款金額超過可退款金額 |
| `922` | 動態訊息 | 退款失敗，看 message |
| `978` | Closed account can't use JKOPay's service... | 帳戶已關閉 |
| `999` | Internal Error | 街口系統非預期錯誤 |

> ⚠️ **退款有兩個硬限制常被忽略**：180 天期限，以及**使用街口券的訂單不能部分退款**。做退貨流程時要先判斷 `redeem_detail`。

#### `GET /platform/inquiry`

`result` 一律 `000`（含查無訂單），實際結果看 `transactions[].status`：

| status | 意義 |
|---|---|
| `0` | 交易成功 |
| `100` | 付款失敗 |
| `101` | 訂單尚未付款 |
| `102` | 訂單編號不存在 |

> ⚠️ **查詢 API 不會用 `result` 表達「查無此單」**——`result=000` 但 `status=102`。只判斷 `result` 會把不存在的訂單當成功。

查詢回傳的 `transactions[]` 結構與 `result_url` 的 `transaction` 相同，另含 `refund_history[]`。

### 5.7 其他端點

| 端點 | 用途 |
|---|---|
| `POST /platform/refund` | 訂單退款 |
| `GET /platform/inquiry` | 訂單查詢，參數 `platform_order_ids`（**複數，逗號分隔可批次查**）|
| 交易撥款檔 R File | 對帳用的撥款檔（Reimburse File）|

## 6. 授權扣款 Authorized Payment — 完整規格

**這是聚合商給不了的能力**（見 §2）。整個模組共 7 支端點。

### 6.1 兩種授權型態

| 型態 | 端點 | 適用 |
|---|---|---|
| **定期定額 regular** | `POST /platform/authpay/regular` | 訂閱制、固定金額方案（影音串流、會員訂閱）。按約定週期與金額自動扣款 |
| **不定期不定額 limited** | `POST /platform/authpay/limited` | 單次購買、變動金額（課金儲值、按用量計費）。授權範圍內扣款，時間與金額不固定 |

> **兩者的 Request / Response 規格完全相同**，差別只在端點與 `billing_cycle` 是否必填。

### 6.2 生命週期

```
授權創建 regular|limited  →  消費者在街口 App 授權  →  result_url callback（granted）
                                                          ↓
                              transaction 發動扣款（可重複）→ refund 退款
                                                          ↓
                                    cancel 終止授權 / detail 查授權狀態
```

### 6.3 授權創建 — Request

| 參數 | 型態 | 長度 | 必填 | 說明 |
|---|---|---|---|---|
| `authpay_name` | string | 60 | ✅ | 授權扣款項目名稱 |
| `store_id` | string | 36 | ✅ | 商店編號 |
| `platform_authpay_id` | string | 60 | | 平台授扣編號（留存用）|
| `identities` | string[] | | | 授權綁定人驗證 |
| `billing_amount` | decimal | 20,0 | ✅ | 原始扣款金額 |
| `billing_currency` | string | | | 預設 `TWD` |
| `billing_cycle` | fields | | **定期定額必填** | 扣款週期定義 |
| `billing_cycle.period` | string | | | `week`（週日～週一）/ `month` / `quarter` / `year`，時區 **UTC+8** |
| `billing_cycle.times` | int | | | 每週期扣款次數，預設 1 |
| `result_url` | string | 500 | ✅ | 綁定結果 callback（**必須 https**）|
| `result_display_url` | string | 500 | | 授權後導向的前端頁 |
| `custom_items.name` / `.value` | string | | | 客製化項目 |

**`billing_cycle.times` 上限**：

| period | 上限 |
|---|---|
| `week` | ≤ 7 次 |
| `month` | ≤ 7 次 |
| `quarter` | ≤ 7 次 |
| `year` | ≤ 12 次 |

> ⚠️ `month` 的上限是 **7 次而非 30 次**——想做「每月多次小額扣款」要先確認撞不撞這個上限。

Response 與 OnlinePay 的 Entry 同構：`result_object` 含 `auth_no`（街口端授權編號）、`authpay_url`、`qr_img`、`qr_timeout`（同樣 **20 分鐘**有效）。

> 冪等行為與 Entry 一致：**綁定未完成前重複呼叫回同一個綁定網址**；`platform_authpay_id` 需唯一。

### 6.4 綁定結果 callback（`result_url`）

`POST`，商家實作。街口以 **HTTP 200 視為成功、HTTP 500 視為失敗並重試**。

連線規則同 OnlinePay：timeout 5/10 秒，**2^n 秒退避重試最多 12 次，約 2 小時**。

Body 為 `{ "authpay": { …GrantedAuthPay… } }`：

| 參數 | 型態 | 必填 | 說明 |
|---|---|---|---|
| `type` | string(30) | ✅ | `regular` / `limited` |
| `status` | string(30) | ✅ | **`ungranted` 未授權 / `granted` 已授權 / `cancel` 已取消** |
| `auth_no` | string(30) | ✅ | 街口端授權編號，**後續扣款都靠它** |
| `platform_authpay_id` | string(60) | ✅ | 平台授扣編號 |
| `jkos_account` | string(100) | ✅ | 街口帳號 |
| `billing_currency` / `billing_amount` | | | 原始扣款幣別與金額 |
| `billing_cycle[]` | | 定期定額必填 | 週期與次數 |

### 6.5 發動扣款 `POST /platform/authpay/transaction`

| 參數 | 型態 | 長度 | 必填 | 說明 |
|---|---|---|---|---|
| `auth_no` | string | 30 | ✅ | 街口端授權編號 |
| `order.platform_order_id` | string | 60 | ✅ | 平台交易序號，需唯一 |
| `order.trade_name` | string | 30 | ✅ | **交易名稱，會顯示在消費者 App 的授權交易記錄頁** |
| `order.currency` | string | 3 | ✅ | 帶 `TWD` |
| `order.total_price` | decimal | 20,0 | ✅ | 訂單價格 |
| `order.final_price` | decimal | 20,0 | ✅ | 應付價格 |
| `order.unredeem` | decimal | 20,0 | | 不可折抵金額，預設 0 |
| `order.remark` | string | 500 | | 備註 |
| `order.products[]` | fields | | | 同 OnlinePay，另多 `category_path` string[] |

Response 的 `result_object` 與 OnlinePay 的 `result_url` 同構（`tradeNo`、`debit_amount`、`redeem_detail`、`invoice_vehicle`、`maskNo`、`channel_type`）。

> `status` 非 0 時，其餘欄位一律不回傳——別預期拿得到 `tradeNo`。

### 6.6 ⚠️ 授權扣款的六個硬限制

這些是設計訂閱系統時**必須先知道**的，全部來自 `/authpay/transaction` 的回應碼：

| result | 限制 |
|---|---|
| `306` | **扣款只能在 08:00–20:00（UTC+8）發動**。半夜跑 batch 一定失敗——排程要避開 |
| `307` | **同一 `auth_no` 同時只允許一筆付款**，不能併發 |
| `303` | 金額超過**用戶自己在 App 設定的最高額度**（不是你設的）|
| `304` | 訂單 `final_price` 與授權時的 `billing_amount` 不一致 |
| `305` | 超過當前計費週期的扣款次數（見 6.3 上限表）|
| `104` | 超過**月限額**（電支法規的個人限額）|

> 前兩項是排程設計的直接約束：**扣款 job 要排在白天，而且同一授權要序列化**。

### 6.7 端點總表與回應碼

| 端點 | Method | 功能 |
|---|---|---|
| `/platform/authpay/regular` | POST | 授權創建（定期定額）|
| `/platform/authpay/limited` | POST | 授權創建（不定期不定額）|
| `/platform/authpay/transaction` | POST | 發動扣款 |
| `/platform/authpay/refund` | POST | 退款 |
| `/platform/authpay/inquiry` | GET | 訂單查詢（`transactions[]`，status 同 OnlinePay 0/100/101/102）|
| `/platform/authpay/detail` | GET | **查授權狀態**，回 `{authpay:{type,auth_no,status,platform_authpay_id}}` |
| `/platform/authpay/cancel` | POST | 終止授權 |

授權模組專屬回應碼（其餘與 OnlinePay 共用，見 5.6）：

| result | message | 說明 |
|---|---|---|
| `201` | Validation error | 驗證錯誤 |
| `301` | Invalid auth_no | 無效授權編號 |
| `302` | Canceled auth_no | 授權已取消（`cancel` 重複呼叫也回這個）|
| `303` | FinalPrice exceeded the max amount quota set by the user | 超過用戶設定額度 |
| `304` | Order finalPrice is not consistent with authpay billing amount | 金額與授權不符 |
| `305` | Authpay payment exceeds current billing cycle times | 超過週期次數 |
| `306` | Authpay payment transaction time invalid.(Available at 08:00 - 20:00 UTC+8) | **時段限制** |
| `307` | Payment with the same auth_no is allowed one at a time | 同授權不可併發 |
| `110` | Store not found | 查無商店 |
| `115` | Payment failed | 付款失敗 |
| `121` | Insufficient bank account balance. | 銀行帳戶餘額不足 |
| `103` | Error in refund amount | 退款金額錯誤（refund）|

## 7. ⚠️ 街口有三套不同的簽章機制

**這是串接街口最容易踩的整體性陷阱**。三個模組各用各的，程式碼完全不能共用：

| 模組 | 演算法 | 簽什麼 | 排序 | 輸出 |
|---|---|---|---|---|
| **線上支付 / 授權扣款**（§5、§6）| **HMAC-SHA256** | payload **原文字串** | ❌ 不排序 | 小寫 hex，放 `digest` header |
| **線下 POS**（§8）| **SHA256**（非 HMAC）| 排序後 JSON **＋ MerchantKey** | ✅ 依 Key 字母排序 | **全小寫** hex，放 `Sign` 欄位 |
| **inApp OAuth / JOP Gateway**（§9）| **SHA256**（非 HMAC）| `secret` ＋ jsonBody ＋ **`timestamp/1000/86400`** | ✅ 業務參數依 ASCII 排序 | 先 `toLowerCase()` 再 **`toUpperCase()`** |

> 三者連「密鑰放哪」都不同：線上支付當 HMAC 的 key、POS 接在 JSON 尾端、OAuth 放在最前面。
> OAuth 那個 `timestamp/1000/86400` 是**天數**（毫秒→秒→天），意思是簽章的這一段**一天只變一次**。

## 8. 線下交易 POS

`POST https://pos.jkopay.com/{系統方名稱}/Payment`

端點：付款 / 取消 / 退款 / 查詢 / 店家撥款檔（R 檔）。

### 簽章（與線上支付完全不同）

1. 除 `Sign` 外所有 Request 欄位序列化為 JSON，**依 Key 字母排序**
2. **不可含空白與換行**（`\r\n`）；字串欄位無值時塞**空字串**
3. JSON 尾端接上 `MerchantKey`，UTF-8 編碼後 **SHA256**，轉 16 進位
4. ⚠️ **`Sign` 須為全小寫**

### 付款 Request

| 參數 | 型態 | 長度 | 說明 |
|---|---|---|---|
| `MerchantID` | String | 10 | 特店代碼 |
| `StoreID` / `StoreName` | String | 20 / 100 | **`StoreName` 需為半形字元** |
| `GatewayTradeNo` | String | 20 | 銀行端交易序號，無則空字串 |
| `MerchantTradeNo` | String | 60 | 商店端付款流水號，**需唯一** |
| `PosID` | String | 20 | POS 機號 |
| `PosTradeTime` | String | 19 | `yyyy/MM/dd HH:mm:ss` |
| `CardToken` | String | 18 | **支付條碼：固定 2 碼 `22` + 16 碼亂數** |
| `TradeAmount` / `UnRedeem` | int | | 消費金額 / 不可折抵金額 |
| `Remark` / `Extra1` / `Extra2` / `Extra3` | String | 1000 / 512 | **全部必填**，無值請帶空字串 |
| `SendTime` | String | 14 | `yyyyMMddHHmmss`（⚠️ **與 `PosTradeTime` 格式不同**）|
| `Sign` | String | 64 | 全小寫 |

> ⚠️ 幾乎所有欄位都標 **Y（必要）**，包含保留欄位 `Extra1`–`Extra3`——「無值」的意思是**帶空字串**而非省略。少帶欄位會導致排序後的 JSON 與街口端不一致而驗簽失敗。

### 付款 Response

| 參數 | 說明 |
|---|---|
| `StatusCode` | `000` 成功，見 §10 |
| `TradeNo` | 街口端交易序號 |
| `IsRep` | **是否為重複交易**：`0` 否 / `1` 是 |
| `PaymentType` | `1` 儲值帳戶 / `3` **銀行帳戶（Account Link）** / `4` 信用卡 |
| `DebitAmount` | 折抵後實扣金額 |
| `RedeemName` | 折抵方式：`Coin` 街口折抵 / `Store` 店家折抵 / `Coin, Store` 兩者 |
| `RedeemAmount` | 街口折抵金額，**此欄位為負值** |
| `StoreRedeemAmount` | 店家折抵金額，**負值**；有店家折抵才回傳 |
| `AvailableAmount` | 儲值帳戶餘額，**目前固定回 0** |
| `InvoiceVehicle` | **手機條碼發票載具** |
| `MerMemToken` | 第三方合作廠商會員識別 |
| `Extra3` | `PaymentType=4` 時以 JSON 字串回傳卡名與前六後四：`{"CardName":"XX卡","CardNo":"222222******3333"}` |

> ⚠️ **折抵金額是負值**，跟線上支付的 `redeem_detail`（正值）相反。對帳時直接相加會算錯。
> ⚠️ `IsRep=1` 代表街口判定為重複交易——POS 端斷線重送時必須看這個欄位，否則會誤認為兩筆成功交易。

## 9. inApp 第三方服務 — OAuth / JOP Gateway

給 ISV 業者取得街口使用者授權資料用，**網域與支付 API 完全不同**：

| 環境 | BaseURL |
|---|---|
| UAT | `https://uat-gw-jop.jkos.app` |
| 正式 | `https://gw-jop.jkos.com` |

`POST https://{BaseUrl}/api`，`Content-Type: application/x-www-form-urlencoded`。

### 公共參數（每支 API 都要帶）

| 參數 | 必填 | 說明 |
|---|---|---|
| `client_id` | ✅ | 開放平台取得的 Credential |
| `method` | ✅ | 欲呼叫的 API 名稱，如 `jkopay.system.oauth.token` |
| `sign` | ✅ | 簽章，規則見 §7 |
| `sign_method` | ✅ | 固定 `JKOS_SIGN` |
| `timestamp` | ✅ | Unix timestamp（**毫秒**）。⚠️ **允許最大誤差一小時** |
| `access_token` | | 訪問令牌 |

### 簽章步驟

1. 建立有序 map（`signBody`），依序放入：`client_id` → `access_token`（需要時）→ **業務參數依名稱 ASCII 排序** → `timestamp`
2. 轉為 JSON 字串 `jsonBody`
3. 依 `{secret}{jsonBody}{timestamp/1000/86400}` 順序組裝
4. `SHA256(body.toLowerCase()).toUpperCase()`

### 兩支 API

**`jkopay.system.oauth.token`** — 以 auth code 或 refresh token 換 access token

| 業務參數 | 說明 |
|---|---|
| `grant_type` | `authorization_code` 或 `refresh_token` |
| `code` | 授權碼；帶 `refresh_token` 時免帶 |
| `refresh_token` | 刷新用；帶 `code` 時免帶 |

回應 `result`：`user_id`、`access_token`、`expires_in`（範例 **2592000 秒 = 30 天**）、`refresh_token`、`refresh_expires_in`（範例 **7776000 秒 = 90 天**）。

**`jkopay.user.profile`** — 取得使用者資料

回應 `result`：`user_id`、`phone`、`email`、**`phone_barcode`（手機載具）**、`name`（範例另含 `id_number`、`birthday`、`gender`、`avatar`、`nickname`、`jkos_account`）。

> 💡 **`phone_barcode` 又是一個跨 skill 接點**：OAuth 拿到的手機載具可直接用於發票 `CarrierType=3` 流程。街口在三個地方都會回載具（OnlinePay 的 `invoice_vehicle`、POS 的 `InvoiceVehicle`、OAuth 的 `phone_barcode`），**欄位名各不相同**。

OAuth 專屬錯誤碼：`OA-001` 成功、`OA-205` Auth Code 已被使用、`OA-360` Auth Code 過期、`OA-999` 系統異常；`UP-001` 成功、`UP-360` Auth Code 過期、`UP-460` **Access Token 過期**、`UP-999`；通用 `205` 參數錯誤、`405` 權限不足、`999` 網關異常。

## 10. 統一錯誤代碼表（線下 POS）

`StatusCode`，共 33 個代碼。**這是街口唯一一份「統一」錯誤碼表**，掛在 POS 模組下。

| 代碼 | 說明 |
|---|---|
| `000` | 交易成功 |
| `301` | 交易失敗（網路或系統異常）|
| `601` | 查無綁定會員 |
| `801` | Gateway 連線異常 |
| `802` | 交易失敗 — 銀行端交易失敗 |
| `804` | 缺少必要參數 |
| `812` | 此筆訂單已轉退款 |
| `901` | 未明確定義錯誤 |
| `904` | **加簽或驗簽失敗** |
| `905` | 解析資料失敗 |
| `906` | **條碼已失效** |
| `907` | 非街口合作店鋪 |
| `909` | 寫入資料失敗 |
| `911` | 停權用戶 |
| `912` | 查無會員 |
| `916` | 查無此訂單 |
| `922` | 退款總金額已超過原付款金額（含多次退款）|
| `927` | 條碼錯誤 |
| `928` | 消費者街口帳戶餘額不足 |
| `929` | 交易類型不支援此付款方式 |
| `931` | 交易金額已達限額 |
| `932` | 店家收款金額已達限額 |
| `934` | 訂單狀態異常，無法退款 |
| `935` | 已達每日店鋪限額 |
| `939` | 學生儲值卡餘額不足 |
| `940` | 支付金額不可 ≤ 0 |
| `951` | 退款造成街口帳戶支出，拒絕退款 |
| `961` | 退款需收回街口幣或現金回饋，信用卡退刷金額異常 |
| `962` | 儲值卡退款失敗 |
| `968` | **此筆交易使用街口券，無法部分退款** |
| `975` | 退款金額大於店家累計未請款金額 |
| `977` | 逾一年未使用，需先聯繫客服身分驗證 |
| `978` | 此用戶無法使用街口服務 |
| `980` | 此店鋪已下線 |

> ⚠️ **`906` 條碼已失效與 `927` 條碼錯誤是 POS 最常見的兩個**——街口付款條碼有時效，收銀台掃碼到送出 API 之間不能拖太久。

## 11. 仍待補

| 待補項目 | 優先 | 備註 |
|---|---|---|
| OnlinePay 退款 / 查詢 API 的 request 逐欄 | 中 | Response Code 已完整，request 欄位待擷取 |
| POS 取消 / 退款 / 查詢 API 的欄位 | 中 | 付款 API 與統一錯誤碼已完成 |
| 街口幣發放 API | 低 | 五大模組中唯一未觸及 |
| R File（店家撥款檔）欄位格式 | 低 | OnlinePay 與 POS 皆有 |
| Web SDK | 低 | 版本多（v2.0.2–v2.0.8 + Next），需先確認採用版本 |

已完成：**線上支付**（§5）、**授權扣款**（§6）、**線下 POS**（§8）、**inApp OAuth**（§9）、**統一錯誤碼表**（§10）。

`data/payment-methods.csv` 中 NewebPay/ezPay 的 `JKOPAY?` 推測碼**仍未驗證**——街口官方文件只描述直連，不涉及各聚合商如何命名自家代碼，需由各聚合商文件確認。

## 12. 來源

- 街口開放文件 — https://open-doc.jkos.com/
- 線上支付 OnlinePay — https://open-doc.jkos.com/?docs=線上支付onlinepay
- API 協議規則 — `…/線上支付onlinepay/串接說明/api-協議規則`
- 加簽加密說明 — `…/線上支付onlinepay/串接說明/加簽加密說明`
- 訂單創建 Entry API — `…/線上支付onlinepay/api列表/訂單創建-api`
- 代碼意義 API Response Code — `…/線上支付onlinepay/api列表/代碼意義`
- 授權扣款 Authorized Payment — https://open-doc.jkos.com/?docs=授權扣款-authorized-payment
- 授權創建 Binding — `…/授權扣款-authorized-payment/api列表-api-lists/授權綁定創建-authorization-binding`
- 授權綁定結果通知 CallBack — `…/api列表-api-lists/授權綁定結果通知-authorization-callback`
- 授權扣款發動 — `…/api列表-api-lists/授權扣款發動-merchant-platform-authorization-request`
- 授權模組代碼意義 — `…/授權扣款-authorized-payment/api列表-api-lists/代碼意義-api-response-code`
- 街口店家收款 — https://www.jkopay.com/application/store
- TapPay 街口 Backend 文件 — https://docs.tappaysdk.com/jko-pay/zh/back.html
- TapPay 街口支付服務頁 — https://www.tappaysdk.com/taiwan-zhtw/service/payments/jko-pay
- HiTRUSTpay 街口介紹 — https://www.hitrustpay.com.tw/page_jkopay.html
