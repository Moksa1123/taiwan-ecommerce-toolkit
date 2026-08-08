# 街口支付 JKOPAY 商家 API 參考

> 官方開放文件: https://open-doc.jkos.com/
> 公司: 街口電子支付股份有限公司（專營電子支付機構）
> Captured: 2026-08-08 · doc_access: **public**（文件站免登入）
> Status: **線上支付 OnlinePay 已完整擷取**（協議／加簽／Entry／雙 callback／全 Response Code）；授權扣款、POS、inApp、街口幣仍待補
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
| **定期扣款／訂閱** | ✅ 授權扣款模組 | ⚠️ 多數聚合商的街口不支援定期扣款 |
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

## 6. 仍待補

| 待補項目 | 優先 | 備註 |
|---|---|---|
| 退款 / 查詢 API 的 request 逐欄 | 中 | Response Code 已完整，request 欄位待擷取 |
| 授權扣款（定期定額）流程與參數 | 中 | Entry API 已可用 `payment_type=regular` 起手 |
| inApp OAuth 流程 | 中 | |
| 線下 POS API | 低 | |
| 街口幣發放 API | 低 | |
| R File 欄位格式 | 低 | |

`data/payment-methods.csv` 中 NewebPay/ezPay 的 `JKOPAY?` 推測碼**仍未驗證**——街口官方文件只描述直連，不涉及各聚合商如何命名自家代碼，需由各聚合商文件確認。

## 7. 來源

- 街口開放文件 — https://open-doc.jkos.com/
- 線上支付 OnlinePay — https://open-doc.jkos.com/?docs=線上支付onlinepay
- API 協議規則 — `…/線上支付onlinepay/串接說明/api-協議規則`
- 加簽加密說明 — `…/線上支付onlinepay/串接說明/加簽加密說明`
- 訂單創建 Entry API — `…/線上支付onlinepay/api列表/訂單創建-api`
- 代碼意義 API Response Code — `…/線上支付onlinepay/api列表/代碼意義`
- 街口店家收款 — https://www.jkopay.com/application/store
- TapPay 街口 Backend 文件 — https://docs.tappaysdk.com/jko-pay/zh/back.html
- TapPay 街口支付服務頁 — https://www.tappaysdk.com/taiwan-zhtw/service/payments/jko-pay
- HiTRUSTpay 街口介紹 — https://www.hitrustpay.com.tw/page_jkopay.html
