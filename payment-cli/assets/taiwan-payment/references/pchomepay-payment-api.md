# PChomePay (拍錢包) Payment API Reference

拍錢包 (PChomePay) 金流 API 完整參考文件。本文件僅涵蓋金流 (建立訂單、付款通知、退款、餘額、提領、對帳)；超商取貨物流 (`/v1/logistic/*`) 屬於物流範疇，請參閱 taiwan-logistics 對應文件。

---

## 目錄

1. [基本說明](#基本說明)
2. [環境資訊](#環境資訊)
3. [認證方式](#認證方式)
4. [API 端點總覽](#api-端點總覽)
5. [取得 Token](#取得-token)
6. [建立訂單 (跳轉付款頁)](#建立訂單-跳轉付款頁)
7. [建立 ATM 虛擬帳號訂單](#建立-atm-虛擬帳號訂單)
8. [建立超商代碼繳費訂單](#建立超商代碼繳費訂單)
9. [查詢支援銀行清單](#查詢支援銀行清單)
10. [訂單查詢](#訂單查詢)
11. [付款通知 (Notify)](#付款通知-notify)
12. [建立退款](#建立退款)
13. [查詢退款](#查詢退款)
14. [查詢帳戶餘額](#查詢帳戶餘額)
15. [提領款項](#提領款項)
16. [查詢對帳資料](#查詢對帳資料)
17. [會員記憶信用卡](#會員記憶信用卡)
18. [錯誤代碼](#錯誤代碼)
19. [支付方式對照表](#支付方式對照表)
20. [測試說明](#測試說明)
21. [常見問題排解](#常見問題排解)

---

## 基本說明

### 服務簡介

PChomePay (拍錢包) 是 PChome 集團推出的第三方支付服務，提供下列特色：

- **採 REST + JSON 規格**：請求／回應皆為 JSON，串接門檻低
- **手續費內扣制**：交易成功後，金額扣除手續費再進入合作方代收帳戶
- **同筆訂單支援多次退款** (信用卡分期付款除外)
- **整合 PChome 拍錢包用戶優惠**：聯名卡享 5% P 幣回饋

### 申請流程

1. 合作方需向 PChomePay 申請正式及測試環境之 **APP ID** 與 **SECRET**
2. 開通後可至會員中心設定請求來源 IP 白名單
3. 合作方若有防火牆，請先放行 PChomePay 對外發送通知所使用的 IP

### 費用模式

- **手續費內扣**：訂單金額 − 手續費 = 實際入帳金額
- **手續費僅向合作方收取**，買家不負擔
- **退款啟動條件**：帳戶餘額需 ≥ 退款金額 + 退款手續費

### 支援付款方式總覽

| 付款方式 | pay_type 代碼 | 金額範圍 | 退款支援 |
|---------|--------------|---------|---------|
| 信用卡 (一次付清 / 分期 0 利率) | `CARD` | 30 ~ 199,999 | 全額 / 部分 (分期僅全額) |
| 拍錢包 (PChomePay 錢包) | `PI` | 1 ~ 199,999 | 全額 / 部分 |
| ATM 虛擬帳號 | `ATM` | 1 ~ 49,999 | 全額 / 部分 (退款手續費 15 元) |
| 超商取貨付款 (7-11) | `IPL7` | 65 ~ 20,000 | 僅全額 (退款手續費 15 元) |
| 超商取貨付款 (全家) | `IPLFM` | 65 ~ 20,000 | 僅全額 (退款手續費 15 元) |
| 超商取貨付款 (萊爾富) | `IPLHL` | 65 ~ 20,000 | 僅全額 (退款手續費 15 元) |
| 超商代碼繳費 | `BCODE` | 25 ~ 20,000 | 僅全額 (退款手續費 15 元) |

> **信用卡國外卡**：合作方需於後台開啟 VISA / Mastercard / JCB 國外卡功能。國外卡僅支援一次付清。
> **拍錢包付款**：用戶須為拍錢包會員，並於 5 分鐘內完成付款。

---

## 環境資訊

### Domain Name

| 環境 | Base URL |
|------|---------|
| 正式環境 | `https://api.pchomepay.com.tw` |
| 測試環境 (Sandbox) | `https://sandbox-api.pchomepay.com.tw` |

### Notify 來源 IP (白名單)

PChomePay 後台會以下列 IP 發送 Notify 通知至合作方：

```
113.196.231.190
```

請將此 IP 加入合作方防火牆白名單，否則無法收到付款／退款／物流狀態通知。

### 通訊規格

| 項目 | 規格 |
|------|------|
| 通訊協定 | HTTPS |
| 請求格式 | JSON (`Content-Type: application/json`) |
| 回應格式 | JSON (對帳 API 為特規多筆 JSON) |
| 字元編碼 | UTF-8 |
| 認證 Header | `pcpay-token: <token>` (取得 token 後使用) |

---

## 認證方式

### 認證概觀

PChomePay 採 **兩階段認證**：

1. **HTTP Basic Auth (APP ID + SECRET)** → 呼叫 `POST /v1/token` 取得 `pcpay-token`
2. **後續所有 API**：在 Header 帶入 `pcpay-token`

### 步驟 1 — 產生 Authorization Header

將 `APP_ID:SECRET` 以 base64 encode 後放入 `Authorization: Basic` 標頭：

```python
import base64

app_id = "0F46D58D576A09BD96E4F22339A5"
secret = "8gKryfZEcY3tWKWJIlc0QLq9pvJ_XQaj1s7ktfva"

raw = f"{app_id}:{secret}"
auth = "Basic " + base64.b64encode(raw.encode()).decode()
# Authorization: Basic MEY0NkQ1OEQ1NzZBMD...
```

### 步驟 2 — 取得 Token

```bash
curl -X POST "https://api.pchomepay.com.tw/v1/token" \
  -H "Authorization: Basic MEY0NkQ1OEQ1NzZBMD..." \
  -H "Content-Type: application/json"
```

回應：

```json
{
  "token": "zHm67sQRuPSO__eiuy2h_lEgtPlS12aVqrcVz3Kc",
  "expired_in": 28800,
  "expired_timestamp": 1474470110
}
```

### 步驟 3 — 使用 Token 呼叫其他 API

將 `token` 放入 `pcpay-token` Header：

```bash
curl -X POST "https://api.pchomepay.com.tw/v1/payment" \
  -H "pcpay-token: zHm67sQRuPSO__eiuy2h_lEgtPlS12aVqrcVz3Kc" \
  -H "Content-Type: application/json" \
  -d '{...}'
```

### Token 注意事項

- **預設有效期限 28,800 秒 (8 小時)**
- 在有效期內請勿重複申請 token，建議快取後重複使用
- 過期可改用 `expired_timestamp` 判斷是否需要重新申請
- Token 無效時 API 會回應錯誤碼 `10003 invalid token`，逾期則為 `10004 token expired`

---

## API 端點總覽

| 功能 | Method | Path |
|------|--------|------|
| 取得 Token | POST | `/v1/token` |
| 建立訂單 (跳轉付款頁) | POST | `/v1/payment` |
| 建立 ATM 虛擬帳號訂單 | POST | `/v1/payment/atmva` |
| 建立超商代碼繳費訂單 | POST | `/v1/payment/barcode` |
| 查詢 ATM 支援銀行 | GET | `/v1/payment/atm/banks` |
| 查詢信用卡分期支援銀行 | GET | `/v1/payment/card/banks` |
| 查詢訂單 | GET | `/v1/payment/{order_id}` |
| 建立退款 | POST | `/v1/refund` |
| 查詢退款 | GET | `/v1/refund/{refund_id}` |
| 查詢帳戶餘額 | GET | `/v1/balance` |
| 提領款項 | POST | `/v1/withdraw` |
| 查詢對帳資料 | GET | `/v1/checking/{date}/{type}` |
| 查詢會員記憶信用卡 | GET | `/v1/payment/card/cardinfo/{member_key}` |
| 刪除會員記憶信用卡 | POST | `/v1/payment/card/cardinfo/delete` |

---

## 取得 Token

### 端點

```
POST /v1/token
Authorization: Basic <base64(APP_ID:SECRET)>
```

### 請求參數

無 body，僅需 `Authorization` 標頭。

### 回應參數

| 欄位 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `token` | ● | String(50) | 後續 API 所需之 token 值 |
| `expired_in` | ● | Int | token 失效秒數，預設 28,800 (8 小時) |
| `expired_timestamp` | ● | Int | token 失效之 Unix timestamp |

### 範例回應

```json
{
  "token": "zHm67sQRuPSO__eiuy2h_lEgtPlS12aVqrcVz3Kc",
  "expired_in": 28800,
  "expired_timestamp": 1474470110
}
```

---

## 建立訂單 (跳轉付款頁)

當訂單建立成功後，會回應一組 `payment_url`，將消費者導頁至該頁面完成付款。適用於信用卡、拍錢包、ATM、超商取貨、超商代碼繳費所有付款方式。

### 端點

```
POST /v1/payment
Content-Type: application/json
pcpay-token: <token>
```

### 請求參數

| 欄位 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `order_id` | ● | String(50) | 合作方訂單編號 (不可重複，限英數、`-`、`_`) |
| `pay_type` | ● | Array | 付款方式陣列，可同時帶多種，見 [pay_type 代碼](#pay_type-代碼對照) |
| `amount` | ● | Int | 訂單金額 (依 pay_type 各有上下限) |
| `items` | ● | Array | 商品資訊陣列，可帶多筆 |
| `return_url` |  | String(200) | 付款成功後導頁 URL，預設為後台環境設定值 |
| `fail_return_url` |  | String(300) | 付款失敗後導頁 URL，預設為後台環境設定值 |
| `notify_url` |  | String(255) | 訂單狀態變更通知 URL，預設為後台環境設定值 |
| `buyer_email` |  | String(50) | 付款人電子郵件 |
| `atm_info` |  | Object | ATM 訂單進階設定，見下方說明 |
| `bcode_info` |  | Object | 超商代碼訂單進階設定，見下方說明 |
| `card_installment` |  | String | 信用卡分期期數 (`1,3,6,12,18,24` 以逗號分隔) |
| `return_timer` |  | String(1) | 訂單成功 / 失敗自動跳轉設定。`Y`：倒數 10 秒後跳轉 (預設) / `N`：立即跳轉。對 ATM 不生效 |
| `member_key` |  | String(30) | 平台會員 ID，用於記憶信用卡或超商收件資訊 |
| `platform_code` |  | String(64) | 平台代碼 (區分多平台來源) |

#### items

| 欄位 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `name` | ● | String | 商品名稱 |
| `url` | ● | String | 商品連結 (須以 `http://` 或 `https://` 開頭) |

#### atm_info

| 欄位 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `expire_days` |  | Int | 付款期限 (天)：`1 ≤ D ≤ 5`，預設 `5` |

#### bcode_info

| 欄位 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `expire_days` |  | Int | 付款期限 (天)：`1 ≤ D ≤ 7`，預設 `7` |

#### pay_type 代碼對照

| 代碼 | 付款方式 | 備註 |
|------|---------|------|
| `CARD` | 信用卡 | 一次付清或分期，搭配 `card_installment` |
| `PI` | 拍錢包 | 用戶須在 5 分鐘內完成付款 |
| `ATM` | ATM 轉帳 | 預設上海商銀 (011)，可由 `atm_info` 控制效期 |
| `IPL7` | 7-11 取貨付款 | 須先於後台設置退件聯繫資訊 |
| `IPLFM` | 全家取貨付款 | 同上 |
| `IPLHL` | 萊爾富取貨付款 | 同上 |
| `BCODE` | 超商代碼繳費 | 預設效期 7 天，可由 `bcode_info` 控制 |

### 請求範例

```bash
curl -X POST "https://api.pchomepay.com.tw/v1/payment" \
  -H "Content-Type: application/json" \
  -H "pcpay-token: DDjz2xrCdCvBRPSFGaoNedVrGHvED8JbAAcU17WT" \
  -d '{
    "order_id": "B2C1703247199",
    "pay_type": ["CARD"],
    "amount": 2675,
    "return_url": "https://shop.example.com/success",
    "fail_return_url": "https://shop.example.com/failed",
    "items": [
      {
        "name": "Chrome Dino Camp Shirt",
        "url": "https://shop.example.com/items/chrome-dino-shirt"
      }
    ],
    "card_installment": "1,3,6,12"
  }'
```

### 回應參數

| 欄位 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `order_id` | ● | String(50) | 合作方訂單編號 |
| `payment_url` | ● | String | 付款頁面 URL，將買家導頁至此完成付款 |

### 範例回應

```json
{
  "order_id": "B2C1703247193",
  "payment_url": "https://pchomepay.com.tw/apipay/ppwf?_pwfkey_=TElVd0FkRzFCY2NCLVE3MlNvRHBSZkdCeixMdFBoU1doNkhJaUVGR3hXejExbG1EN0Zra1phUUdqRjdVT1A0RA=="
}
```

### 失敗回應範例

```json
{
  "error_type": "invalid_request_error",
  "code": 20001,
  "message": "order id duplicate"
}
```

---

## 建立 ATM 虛擬帳號訂單

「幕後取號」服務：直接取得虛擬帳號資訊顯示於合作方頁面，不需將買家導頁至 PChomePay 付款頁。

### 端點

```
POST /v1/payment/atmva
Content-Type: application/json
pcpay-token: <token>
```

### 請求參數

| 欄位 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `order_id` | ● | String(50) | 合作方訂單編號 |
| `amount` | ● | Int | 訂單金額 (1 ~ 49,999) |
| `expire_days` |  | Int | 付款期限：`1 ≤ D ≤ 5`，預設 `5` 天 |
| `item_name` | ● | String(200) | 商品名稱 |
| `item_url` | ● | String(200) | 商品頁面 (須以 `http://` 或 `https://` 開頭) |
| `atm_bank` |  | String(3) | 指定虛擬帳號銀行代碼，預設上海商銀 `011` |
| `notify_url` |  | String(255) | 通知 URL |
| `buyer_name` | ● | String | 付款人姓名 |
| `buyer_mobile` | ● | String | 付款人電話 |
| `buyer_email` |  | String(50) | 付款人 Email |
| `platform_code` |  | String(64) | 平台代碼 |

### 請求範例

```bash
curl -X POST "https://api.pchomepay.com.tw/v1/payment/atmva" \
  -H "Content-Type: application/json" \
  -H "pcpay-token: <token>" \
  -d '{
    "order_id": "B2CATM1735808899",
    "amount": 500,
    "expire_days": 3,
    "item_name": "休閒褲",
    "item_url": "https://www.example.com.tw",
    "atm_bank": "812",
    "notify_url": "https://merchant.example.com/notify",
    "buyer_name": "王大明",
    "buyer_mobile": "0912345678",
    "buyer_email": "ming@example.com"
  }'
```

### 回應參數

| 欄位 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `order_id` | ● | String(50) | 合作方訂單編號 |
| `virtual_account` | ● | String(20) | ATM 虛擬帳號 |
| `bank_id` | ● | String(3) | 銀行代碼 |
| `expire_date` | ● | String(14) | 有效期限，`YYYYMMDDHH24MISS` |

### 範例回應

```json
{
  "order_id": "B2CATM1696393715",
  "virtual_account": "8766824148422803",
  "bank_id": "812",
  "expire_date": "20231007235959"
}
```

---

## 建立超商代碼繳費訂單

「幕後取號」服務：取得 3 段條碼及付款代碼，可自行產生 code39 條碼或繳費 QR Code。

### 端點

```
POST /v1/payment/barcode
Content-Type: application/json
pcpay-token: <token>
```

### 請求參數

| 欄位 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `order_id` | ● | String(50) | 合作方訂單編號 |
| `amount` | ● | Int | 訂單金額 (25 ~ 20,000) |
| `items` | ● | Array | 商品資訊 (同前述 `items` 結構) |
| `expire_days` |  | Int | 付款期限：`1 ≤ D ≤ 7`，預設 `7` 天 |
| `notify_url` |  | String(255) | 通知 URL |
| `buyer_name` | ● | String(50) | 付款人姓名 |
| `buyer_mobile` | ● | String | 付款人電話，須為 `09` 開頭 10 碼數字 |
| `buyer_email` |  | String(50) | 付款人 Email |
| `platform_code` |  | String(64) | 平台代碼 |

### 請求範例

```bash
curl -X POST "https://api.pchomepay.com.tw/v1/payment/barcode" \
  -H "Content-Type: application/json" \
  -H "pcpay-token: <token>" \
  -d '{
    "order_id": "B2CBARCODE1732620171",
    "amount": 500,
    "items": [
      {
        "name": "Chrome Dino Camp Shirt",
        "url": "https://shop.example.com/dino-shirt"
      }
    ],
    "notify_url": "https://merchant.example.com/notify",
    "buyer_name": "John Doe",
    "buyer_mobile": "0912345678",
    "buyer_email": "buyer@example.com"
  }'
```

### 回應參數

| 欄位 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `order_id` | ● | String(50) | 合作方訂單編號 |
| `pincode` | ● | String | 付款代碼 (可至 ibon 機台輸入) |
| `barcode1` | ● | String | 第 1 段條碼 |
| `barcode2` | ● | String | 第 2 段條碼 |
| `barcode3` | ● | String | 第 3 段條碼 |
| `expire_date` | ● | String(14) | 有效期限，`YYYYMMDDHH24MISS` |

### 範例回應

```json
{
  "order_id": "B2CBARCODE1732620171",
  "pincode": "251264755740",
  "barcode1": "130912968",
  "barcode2": "2512647520801218",
  "barcode3": "682359650000100",
  "expire_date": "20241130235959"
}
```

### 條碼／QR Code 提供方式

合作方可以下列任一方式提供給買家：

1. **3 段 code39 條碼**：直接列印 3 段條碼，買家至超商櫃檯掃描繳費
2. **繳費 QR Code**：將 3 段條碼依序放入 `Code1` / `Code2` / `Code3` 後產生 QR Code

   ```json
   {"Utility":[{"Ordinary":[{"Device":"POS","Code1":"140520980","Code2":"0478631620040001","Code3":"842359540000100"}]}]}
   ```

3. **繳費代碼 (pincode)**：買家至 ibon 機台手動輸入，列印繳費單後至超商櫃檯掃描繳費

---

## 查詢支援銀行清單

### 查詢 ATM 支援虛擬帳號之銀行

```
GET /v1/payment/atm/banks
pcpay-token: <token>
```

#### 回應範例

```json
{
  "banks": [
    {"bank_id": "812", "bank_name": "台新銀行"},
    {"bank_id": "011", "bank_name": "上海商銀"}
  ]
}
```

### 查詢支援信用卡分期銀行

```
GET /v1/payment/card/banks
pcpay-token: <token>
```

#### 回應範例

```json
{
  "banks": [
    {
      "bank_id": "011",
      "bank_name": "上海商業儲蓄銀行",
      "installment": "3,6,12,18,24"
    },
    {
      "bank_id": "812",
      "bank_name": "台新國際商業銀行",
      "installment": "3,6,12,18,24"
    }
  ]
}
```

`installment` 為該銀行可用之分期期數，以逗號分隔。

---

## 訂單查詢

### 端點

```
GET /v1/payment/{order_id}
pcpay-token: <token>
```

### 請求路徑參數

| 欄位 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `order_id` | ● | String(50) | 合作方訂單編號 |

### 回應參數

| 欄位 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `order_id` | ● | String(50) | 合作方訂單編號 |
| `amount` | ● | String | 訂單金額 |
| `pay_type` | ● | String(5) | 付款方式 (`CARD` / `PI` / `ATM` / `IPL7` / `IPLFM` / `IPLHL` / `BCODE`) |
| `trade_amount` | ● | Int | 實際交易金額 |
| `platform_amount` | ● | Int | 合作方實際入帳金額 (= 實際交易金額 − 手續費) |
| `pp_fee` | ● | Int | 手續費 |
| `create_date` | ● | String(14) | 訂單建立時間 (`YYYYMMDDHH24MISS`) |
| `pay_date` | ● | String(14) | 訂單確認時間 |
| `actual_pay_date` | ● | String(14) | 實際付款時間 |
| `fail_date` | ● | String(14) | 交易失敗時間 (逾期、付款失敗時才有值) |
| `status` | ● | String(1) | 訂單狀態：`S` 完成 / `W` 等待中 / `F` 失敗 |
| `status_code` | ● | String | 訂單狀態代碼，見下表 |
| `payment_info` | ● | Object | 訂單付款資訊，依付款方式不同 |
| `available_date` | ● | String(14) | 訂單款項轉可提領時間 |
| `items` | ● | Array | 商品資訊 |

### status_code 對照表

| status_code | 說明 |
|-------------|------|
| `FE` | 訂單逾時 |
| `FT` | 連線失敗 |
| `WO` | 信用卡等待 OTP 驗證 |
| `FF` / `FA` | 信用卡授權失敗 |
| `FF-1` | 請與發卡銀行聯絡 (Call Bank) |
| `FF-2` | 拒絕交易 (Decline) |
| `FF-3` | 異常卡片 (Pickup) |
| `FF-4` | 卡片過期 (Expire card) |
| `FF-5` | 交易日期錯誤 |
| `FF-6` | 信用卡交易逾時 |
| `FX` | ATM 虛擬帳號失效 |
| `WP` | ATM 待繳款 |
| `WB` | 尚未選擇銀行 |
| `WAP` | 審單中 |
| `FP` | 審單拒絕 |
| `WAC` | 合作方自行審單中 |
| `FC` | 合作方審單拒絕 |
| `FB` | 支付連餘額不足 |
| `WD` | 超商取貨等待商品交寄 |

### payment_info 物件

`payment_info` 內容依 `pay_type` 動態變化，所有可能欄位如下：

| 欄位 | 型態 | 說明 |
|------|------|------|
| `virtual_account` | String(20) | ATM 虛擬帳號 |
| `bank_code` | String(3) | ATM 虛擬帳號之銀行代號 |
| `expire_date` | String(14) | ATM 或代碼付款之有效期限 |
| `buyer_bank_code` | String(3) | 用戶轉出帳戶銀行代碼 (ATM) |
| `buyer_account_last5` | String(5) | 用戶轉出帳戶之帳號末 5 碼 (ATM) |
| `installment` | String | 信用卡分期期數 |
| `rate` | Float | 信用卡金流手續費率 |
| `card_last_number` | String | 信用卡卡號末 4 碼 |
| `pp_fee` | Int | 信用卡金流手續費 |
| `logistic_id` | String(11) | 超商物流代號 |
| `receiver_name` | String | 取件人姓名 |
| `receiver_mobile` | String | 取件人電話 |
| `store_id` | String | 取件門市代號 |
| `store_name` | String | 取件門市名稱 |
| `pincode` | String | 代碼付款之付款代碼 |
| `barcode1` | String | 代碼付款第 1 段條碼 |
| `barcode2` | String | 代碼付款第 2 段條碼 |
| `barcode3` | String | 代碼付款第 3 段條碼 |

### 範例回應

```json
{
  "order_id": "B2C1695210352",
  "amount": "500",
  "pay_type": "ATM",
  "trade_amount": 500,
  "platform_amount": 490,
  "pp_fee": 10,
  "create_date": "20230920194551",
  "pay_date": "20230920194616",
  "actual_pay_date": "20230920194616",
  "fail_date": null,
  "status": "S",
  "status_code": null,
  "payment_info": {
    "virtual_account": "2606092510742523",
    "bank_code": "013",
    "expire_date": "20230925235959"
  },
  "available_date": "20230922163311",
  "items": [
    {"name": "休閒上衣", "url": "https://shop.example.com/"}
  ]
}
```

---

## 付款通知 (Notify)

### 通知流程

訂單狀態變更 (建立、付款成功、逾期、失敗、退款、物流) 時，PChomePay 會以 `application/x-www-form-urlencoded` POST 至合作方 `notify_url`。

```
┌─────────┐  訂單事件  ┌────────────┐   POST notify_url   ┌─────────┐
│ 消費者  │ ─────────▶│ PChomePay  │ ───────────────────▶│  商店   │
└─────────┘           └────────────┘                     └─────────┘
                                                              │
                                                              │ 回應 "success"
                                                              ▼
                                                       ┌────────────┐
                                                       │ PChomePay  │
                                                       │ 確認收到   │
                                                       └────────────┘
```

**重試規則**：

- 合作方須於 **3 秒內** 回傳 `success` 純文字
- 未回應或回傳非 `success` 時，PChomePay 會於 5 分鐘後重送
- 之後每 5 分鐘重試一次，**最多送 5 次**

### 通知欄位 (共通)

`Content-Type: application/x-www-form-urlencoded`

| 欄位 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `notify_type` | ● | String | 通知種類 (見下表) |
| `notify_message` | ● | String | 通知訊息 (JSON 字串)，內容依 notify_type 而異 |

### notify_type 對照表

| notify_type | 觸發時機 |
|-------------|---------|
| `order_audit` | ATM 取號成功、代碼取號成功、超商取貨已選好門市 |
| `order_confirm` | 訂單付款成功 (款項已入合作方代收帳戶) |
| `order_expired` | 訂單未在時效內完成付款 |
| `order_failed` | 訂單付款失敗 |
| `refund_success` | 退款成功 (款項已從代收帳戶扣除) |
| `seller_dispatched` | 商品已至「寄件門店」(超商取貨) |
| `pickup_shipped` | 商品已至「取件門店」(超商取貨) |
| `return_shipped` | 商品已至「退件門店」(超商取貨) |

> **注意**：超商代碼繳費的 `pay_type` 在通知中為 `BCODE`。

### 通知範例 — order_confirm (信用卡付款成功)

```bash
POST https://merchant.example.com/notify
Content-Type: application/x-www-form-urlencoded

notify_type=order_confirm
notify_message={
  "order_id": "20170518225853-1",
  "amount": "1000",
  "pay_type": "CARD",
  "trade_amount": 1000,
  "platform_amount": 980,
  "pp_fee": 20,
  "create_date": "20170518230249",
  "pay_date": "20170803162239",
  "fail_date": null,
  "status": "S",
  "status_code": null,
  "payment_info": {
    "installment": "1",
    "rate": 0.02,
    "card_last_number": "0527",
    "pp_fee": 20
  },
  "available_date": "20170809000000",
  "items": [{"name": "...", "url": "..."}]
}
```

### 通知範例 — order_audit (ATM 取號成功)

```
notify_type=order_audit
notify_message={
  "order_id": "20170518225853-2",
  "amount": "3492",
  "pay_type": "ATM",
  "status": "W",
  "status_code": "WP",
  "payment_info": {
    "virtual_account": "0702405595386988",
    "bank_code": "011",
    "expire_date": "20240224235959"
  },
  "items": [...]
}
```

### 通知範例 — order_expired

```
notify_type=order_expired
notify_message={
  "order_id": "20240729164002-3",
  "pay_type": "CARD",
  "status": "F",
  "status_code": "FE",
  "fail_date": "20240729170002",
  ...
}
```

### 通知範例 — refund_success

```
notify_type=refund_success
notify_message={
  "refund_id": "R230830000100_312100",
  "status": "S",
  "amount": "200",
  "fee": 4,
  "transfer_fee": 0,
  "refund_date": "20230830232759",
  "cover_transfee": "Y",
  "actual_refund_date": "20230830232759"
}
```

### 商店回應格式

**成功**：以 HTTP 200 回應純文字 `success`

```http
HTTP/1.1 200 OK
Content-Type: text/plain

success
```

**失敗**：回應其他內容，PChomePay 將重試最多 5 次 (每 5 分鐘一次)。

---

## 建立退款

### 退款規則

1. **退款方式**
   - 信用卡：退刷至原信用卡
   - ATM：退款至原匯款帳戶
   - 超商取貨付款 / 代碼繳費：退款至指定銀行帳戶 (需於後台設置)
   - 拍錢包：依 [拍錢包交易退款規則](https://web.piapp.com.tw/faq/bs18122107/)

2. **退款限制**
   - **僅支援一次性全額退款**：信用卡分期、超商取貨、代碼繳費
   - **支援部分退款**：其他付款方式 (信用卡一次付清、拍錢包、ATM)
   - 同一筆訂單可多次退款 (信用卡分期除外)，欲退款金額 ≤ 訂單剩餘可退金額
   - 帳戶餘額 ≥ 退款金額 + 退款手續費 才能成功退款
   - 超商取貨：須待款項清算完成才能退款

3. **退款手續費**：以下方式每筆收 **15 元** 退款手續費
   - ATM 虛擬帳號
   - 超商取貨付款
   - 代碼繳費

4. **手續費返還規則 (信用卡)**
   - **全額退款**：返還原訂單收取之全部手續費
   - **部分退款**：依「退款金額 / 原訂單金額」之比例返還手續費

   範例：訂單 1,500 元、手續費率 2% (=30 元)
   - 第 1 次退款 500 元 → 返還 `30 × (500 / 1500)` = 10 元手續費
   - 第 2 次退款 1,000 元 → 返還剩餘 20 元手續費

### 端點

```
POST /v1/refund
Content-Type: application/json
pcpay-token: <token>
```

### 請求參數

| 欄位 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `order_id` | ● | String(50) | 合作方訂單編號 |
| `refund_id` | ● | String(50) | 合作方退款編號 (不可重複) |
| `trade_amount` | ● | Int | 退款金額 |

### 請求範例

```bash
curl -X POST "https://api.pchomepay.com.tw/v1/refund" \
  -H "Content-Type: application/json" \
  -H "pcpay-token: <token>" \
  -d '{
    "order_id": "B2C1695210352",
    "refund_id": "B2C1695210352-Refund",
    "trade_amount": 100
  }'
```

### 回應參數

| 欄位 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `order_id` | ● | String(50) | 合作方訂單編號 |
| `refund_id` | ● | String(50) | 合作方退款編號 |
| `pay_type` | ● | String(10) | 退款方式 (依原訂單付款方式處理) |
| `trade_amount` | ● | Int | 退款金額 |
| `fee` | ● | Int | 退還的手續費 (依比例返還) |
| `transfer_fee` | ● | Int | 退款手續費 (ATM / 超商取貨 / 代碼繳費 為 15 元) |
| `cover_transfee` |  | String(1) | 是否收取退款手續費 (`Y`/`N`) |

### 範例回應

```json
{
  "order_id": "B2C1695210352",
  "refund_id": "B2C1695210352-Refund",
  "pay_type": "ATM",
  "trade_amount": 100,
  "fee": 2,
  "transfer_fee": 15,
  "cover_transfee": "Y"
}
```

---

## 查詢退款

### 端點

```
GET /v1/refund/{refund_id}
pcpay-token: <token>
```

### 請求路徑參數

| 欄位 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `refund_id` | ● | String(50) | 合作方退款編號 |

### 回應參數

| 欄位 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `refund_id` | ● | String(50) | 合作方退款編號 |
| `status` | ● | String(5) | 退款狀態：`INIT` 已建立 / `WAIT` 處理中 / `SUCC` 退款成功 / `FAIL` 退款失敗 |
| `amount` | ● | String | 退款金額 |
| `fee` | ● | String | 退還的手續費 |
| `transfer_fee` | ● | String | 退款手續費 |
| `refund_date` | ● | String(14) | 退款建立時間 (`YYYYMMDDHH24MISS`) |
| `cover_transfee` | ● | String(1) | 是否收取退款手續費 (`Y`/`N`) |
| `actual_refund_date` | ● | String(8) | 實際退款時間 (`YYYYMMDD`) |

### 範例回應

```json
{
  "refund_id": "B2C1695210352-Refund",
  "status": "SUCC",
  "amount": "100",
  "fee": "2",
  "transfer_fee": "15",
  "refund_date": "20231004134645",
  "cover_transfee": "Y",
  "actual_refund_date": "20231004"
}
```

---

## 查詢帳戶餘額

### 端點

```
GET /v1/balance
pcpay-token: <token>
```

### 回應參數

| 欄位 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `all` | ● | Int | 帳戶總餘額 |
| `available` | ● | Int | 可提領餘額 |
| `processing` | ● | Int | 處理中餘額 (提領中或清算中) |

### 範例回應

```json
{
  "all": 1030519,
  "available": 1010347,
  "processing": 20172
}
```

---

## 提領款項

提領可用餘額至綁定認證之銀行帳戶；若有多筆綁定帳戶，預設使用第 1 組。

### 端點

```
POST /v1/withdraw
Content-Type: application/json
pcpay-token: <token>
```

### 請求參數

| 欄位 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `amount` | ● | Int | 提領金額 (本行 > 1 元；他行 ≥ 11 元) |

### 回應參數

| 欄位 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `withdraw_amount` | ● | Int | 實際提領金額 |
| `transfer_fee` | ● | Int | 跨行提領手續費 |
| `bank_id` | ● | String(3) | 入帳銀行代碼 |
| `bank_account` | ● | String | 入帳銀行帳號 |

### 範例回應

```json
{
  "withdraw_amount": 500,
  "transfer_fee": 10,
  "bank_id": "822",
  "bank_account": "170923402112"
}
```

---

## 查詢對帳資料

查詢指定日期之訂單／退款明細帳務資料，可用於合作方自動對帳。

### 端點

```
GET /v1/checking/{date}/{type}
pcpay-token: <token>
```

### 請求路徑參數

| 欄位 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `date` | ● | String(8) | 對帳日期 (`YYYYMMDD`)，僅能查詢 120 天以前 (不含當日) |
| `type` | ● | String(10) | `orders`：訂單；`refunds`：退款 |

### 回應格式

對帳 API 回應為 **多筆 JSON 物件並列** (非標準 JSON 陣列)，第一個物件為總筆數，後續每行為一筆訂單／退款資料。

```json
{"total_recs": "2"}
{"order_id": "B2C1696581256", "amount": "500", "pay_type": "ATM", ...}
{"order_id": "B2C1699956990", "amount": "100", "pay_type": "PI", ...}
```

每筆資料的內容與 [訂單查詢](#訂單查詢) 或 [查詢退款](#查詢退款) 相同欄位。

### 解析建議 (Python)

```python
import json

def parse_checking_response(text: str):
    objs = []
    decoder = json.JSONDecoder()
    idx = 0
    text = text.strip()
    while idx < len(text):
        obj, end = decoder.raw_decode(text, idx)
        objs.append(obj)
        idx = end
        while idx < len(text) and text[idx] in ' \r\n\t':
            idx += 1
    total = objs[0].get("total_recs")
    records = objs[1:]
    return total, records
```

---

## 會員記憶信用卡

### 查詢會員記憶信用卡

```
GET /v1/payment/card/cardinfo/{member_key}
pcpay-token: <token>
```

#### 請求路徑參數

| 欄位 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `member_key` | ● | String(30) | 平台會員 ID (建立訂單時所傳遞) |

#### 回應參數

| 欄位 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `status` | ● | String | 查詢結果 (`success` / 其他) |
| `message` | ● | String | 查詢結果訊息 |
| `cardList` | ● | Array | 已記錄之信用卡列表 |

`cardList[*]`：

| 欄位 | 型態 | 說明 |
|------|------|------|
| `no` | String(100) | 加密過的信用卡卡號 (用於後續刪除) |
| `alias` | String(50) | 銀行名稱 |
| `last4` | String(4) | 信用卡末 4 碼 |

#### 範例回應

```json
{
  "status": "success",
  "message": "Successfully retrieved the stored card number.",
  "cardList": [
    {
      "no": "TnBBeWViQUlET3FTTkt5MWhNWnh...",
      "alias": "上海銀行",
      "last4": "3014"
    }
  ]
}
```

### 刪除會員記憶信用卡

```
POST /v1/payment/card/cardinfo/delete
Content-Type: application/json
pcpay-token: <token>
```

#### 請求參數

| 欄位 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `member_key` | ● | String(30) | 平台會員 ID |
| `card_no` | ● | String(100) | 欲刪除之 (加密) 信用卡卡號 (即查詢回傳之 `no`) |

#### 範例回應

```json
{
  "status": "success",
  "message": "Successfully removed the stored card number."
}
```

---

## 錯誤代碼

PChomePay 失敗時會回傳：

```json
{
  "error_type": "invalid_request_error",
  "code": 20001,
  "message": "order id duplicate"
}
```

### 認證 / Token 類 (10xxx)

| 代碼 | 英文描述 | 中文描述 |
|------|----------|---------|
| `10001` | invalid user password | APP ID 或 SECRET 錯誤 |
| `10002` | Server IP not allow | 不被允許的 IP 位址 |
| `10003` | invalid token | token 錯誤 |
| `10004` | token expired | token 逾期 |
| `10006` | api client has not set notifyURL or returnURL yet | 未設定 notifyURL 或 returnURL |
| `10007` | function not available | 會員帳號暫時無法使用此功能 |

### 訂單類 (20xxx)

| 代碼 | 英文描述 | 中文描述 |
|------|----------|---------|
| `20001` | order id duplicate | 訂單編號不可重複 |
| `20002` | order not exists | 訂單不存在 |
| `20003` | pay type not support | 付款類別錯誤 |
| `20005` | params is not valid | 參數錯誤 |
| `20006` | credit installment amount must >= 30 | 信用卡分期商品金額須 ≥ 30 元 |
| `20007` | not allow to check today's data | 目前無法查詢當日資料 |
| `20008` | order items string too long | 商品名稱超過字數限制 |
| `20009` | not a JSON structure | 請求格式不是 JSON |
| `20011` | bank code or bank account not exists | 銀行代號或銀行帳戶不存在 |
| `20013` | ATM bank code invalid | ATM 銀行代碼錯誤 |
| `20014` | cvs setting error | 未設定超商退貨門市 |
| `20019` | create pi payment fail | 建立拍錢包訂單失敗 |
| `20020` | pi payment is disable | 拍錢包收款尚未啟用 |
| `20022` | order amount is exceeds the pi setting | 拍錢包訂單金額超過上限 |
| `20023` | function lock | 會員帳號暫時無法使用此收款功能 |
| `20025` | remove card info fail | 移除記憶信用卡失敗 |
| `20030` | platform code not accept | 平台代碼錯誤 |
| `20031` | currently unable to create installment payment orders | 暫時無法建立信用卡分期付款訂單 |

### ATM 類 (40xxx)

| 代碼 | 英文描述 | 中文描述 |
|------|----------|---------|
| `40001` | invalid atm expire date | ATM 逾期錯誤 |
| `40003` | function lock | 會員帳號暫時無法使用 |
| `40005` | member balance not enough | 餘額不足 |

### 退款類 (50xxx)

| 代碼 | 英文描述 | 中文描述 |
|------|----------|---------|
| `50001` | refund id is duplicate | 退款編號不可重複 |
| `50002` | order is not confirm yet | 訂單未成功付款，無法退款 |
| `50003` | order not found | 訂單編號不存在 |
| `50004` | refund amount must bigger than 0 | 退款金額需大於 0 |
| `50005` | balance not enough to refund | 帳戶餘額不足以退款 |
| `50006` | can not find the refund id | 查無此退款編號 |
| `50007` | installment can only full refund | 信用卡分期僅能全額退款 |
| `50009` | atm refund data is not ready | ATM 退款資訊未備齊，請隔日再試 |
| `50010` | order is failed, refund can't be execute | 訂單已失敗，不可退款 |
| `50011` | refund amount must equal to order amount | 退款金額必須與訂單金額相同 |
| `50012` | order is already refund | 訂單已退款 |
| `50013` | order is not allow to refund | 訂單目前不能退款 |
| `50014` | pay type is not allow to refund | 訂單不支援此退款方式 |
| `50015` | call Pi refund API error | 建立拍錢包退款失敗 |
| `50016` | bank code not support atm refund | 原付款行不支援退回原帳戶 |

### 提領類 (70xxx)

| 代碼 | 英文描述 | 中文描述 |
|------|----------|---------|
| `70001` | withdraw must be bigger than 10 dollars | 本行提領 > 1 元、他行提領 ≥ 11 元 |
| `70003` | withdraw amount over available balance | 提領金額超過可提領餘額 |
| `70004` | over daily limit | 提領金額超過本日提領額度上限 |
| `70005` | bank to withdraw is not set yet | 提領銀行尚未設定 |
| `70006` | function lock | 會員帳號暫時無法使用提領功能 |

### 物流類 (90xxx，超商取貨僅供參考)

| 代碼 | 英文描述 | 中文描述 |
|------|----------|---------|
| `90001` | invalid status | 物流狀態錯誤 |
| `90002` | logistic status history not found | 物流狀態歷程不存在 |
| `90004` | print delivery note fail | 列印交寄單失敗 |

---

## 支付方式對照表

### pay_type ↔ 付款方式

| pay_type | 中文名稱 | 通道類型 | 取號方式 |
|----------|---------|---------|---------|
| `CARD` | 信用卡 | 線上即時授權 | 跳轉付款頁 |
| `PI` | 拍錢包 | 第三方錢包 | 跳轉付款頁 (5 分鐘內完成) |
| `ATM` | ATM 虛擬帳號 | 銀行轉帳 | 可跳轉或幕後取號 |
| `IPL7` | 7-11 取貨付款 | 物流代收 | 跳轉付款頁 |
| `IPLFM` | 全家取貨付款 | 物流代收 | 跳轉付款頁 |
| `IPLHL` | 萊爾富取貨付款 | 物流代收 | 跳轉付款頁 |
| `BCODE` | 超商代碼繳費 | 條碼／代碼 | 可跳轉或幕後取號 (3 段條碼) |

### ATM 銀行代碼 (常用)

| 代碼 | 銀行名稱 |
|------|---------|
| `004` | 臺灣銀行 |
| `005` | 土地銀行 |
| `007` | 第一銀行 |
| `008` | 華南銀行 |
| `011` | 上海商業儲蓄銀行 (預設) |
| `013` | 國泰世華 |
| `017` | 兆豐銀行 |
| `808` | 玉山銀行 |
| `812` | 台新國際商業銀行 |
| `822` | 中國信託 |

> 完整支援銀行清單請呼叫 `GET /v1/payment/atm/banks` 動態查詢。

### 信用卡分期支援期數

PChomePay 支援的分期期數為 `1`、`3`、`6`、`12`、`18`、`24` 期 (各銀行支援的期數可能不同)。
請以 `GET /v1/payment/card/banks` 取得各銀行 `installment` 動態清單。

### 各通道金額限制 (再整理)

| pay_type | 最低 | 最高 | 預設效期 |
|----------|------|------|---------|
| `CARD` | 30 | 199,999 | 即時 |
| `PI` | 1 | 199,999 | 5 分鐘 |
| `ATM` | 1 | 49,999 | 5 天 (`atm_info.expire_days` 1 ~ 5) |
| `IPL7` / `IPLFM` / `IPLHL` | 65 | 20,000 | 依超商規範 |
| `BCODE` | 25 | 20,000 | 7 天 (`bcode_info.expire_days` 1 ~ 7) |

---

## 測試說明

以下規則 **僅限於 Sandbox 測試環境**，正式環境不會生效。合作方可透過調整訂單金額尾數或卡號，模擬不同的訂單情境。

### 信用卡測試卡號

#### 成功訂單

| 卡別 | 卡號 | 有效期限 | 安全碼 |
|------|------|---------|--------|
| VISA | `4013-5243-8125-0527` | 12/30 | 999 |
| JCB | `3534-0332-8368-6434` | 12/30 | 999 |
| Mastercard | `5172-0254-1302-0031` | 12/30 | 999 |

#### 失敗訂單

| 卡別 | 卡號 | 有效期限 | 安全碼 |
|------|------|---------|--------|
| VISA | `4802-7166-5544-3326` | 12/30 | 999 |
| JCB | `3560-5259-8380-4800` | 12/30 | 999 |
| Mastercard | `5155-2800-1234-5674` | 12/30 | 999 |

### ATM 測試規則 (依訂單金額尾數)

| 訂單金額尾數 | 結果 |
|------------|------|
| `0` ~ `7` | 自動付款完成 |
| `8` | 依 `expire_days` 參數過期訂單 |
| `9` | 5 分鐘後虛擬帳號過期 |

### 超商取貨測試規則 (依訂單金額尾數)

測試門市：7-11 桃園市桃園區中埔六街 36 號 1 樓 維瀚門市

| 訂單金額尾數 | 物流狀態 |
|------------|---------|
| `0` 或 `6` ~ `9` | 已建立 |
| `1` | 已交寄 |
| `2` | 配送中 |
| `3` | 已到店 |
| `4` | 已收款 |
| `5` | 已退件 |

### 超商代碼繳費測試規則 (依訂單金額尾數)

| 訂單金額尾數 | 結果 |
|------------|------|
| `0` ~ `5` | 3 分鐘後自動付款完成 |
| `6` | 3 分鐘後逾期付款失敗 |
| `7` ~ `9` | 依正常流程處理訂單狀態 |

---

## 常見問題排解

### 取得 token 失敗

**問題**：`10001 invalid user password`

**檢查項目**：

1. APP ID 與 SECRET 是否來自正確的環境 (測試／正式)
2. base64 編碼是否正確 (應為 `APP_ID:SECRET` 之 base64)
3. `Authorization` Header 是否前綴 `Basic `

### 不被允許的 IP

**問題**：`10002 Server IP not allow`

**解決**：

- 至 PChomePay 會員中心將請求發出之伺服器 IP 加入 IP 白名單
- 同時將 PChomePay Notify 來源 IP `113.196.231.190` 加入合作方防火牆放行清單

### 訂單編號重複

**問題**：`20001 order id duplicate`

**原因**：

- `order_id` 與既有訂單重複
- 限英數、`-`、`_`，最長 50 字元

**建議產生方式**：

```python
import time, random
order_id = f"B2C{int(time.time())}{random.randint(100,999)}"
```

### Notify 沒收到 / 重複處理

**問題**：付款成功但沒收到 Notify、或同一筆收到多次

**檢查項目**：

1. `notify_url` 為 HTTPS 且能被外網存取
2. 防火牆放行 `113.196.231.190`
3. 收到通知後須於 3 秒內回應 `success` 純文字
4. 處理 Notify 時請使用「資料庫交易 + 訂單狀態檢查」避免重複入帳

```python
# Pseudo-code
def handle_notify(notify_type, notify_message):
    payload = json.loads(notify_message)
    order = get_order(payload["order_id"])

    # idempotency check
    if order.status == "PAID" and notify_type == "order_confirm":
        return "success"

    # ... update order ...
    return "success"
```

### 退款失敗

**常見錯誤**：

- `50005 balance not enough` → 帳戶須有 `退款金額 + 退款手續費`
- `50007 installment can only full refund` → 信用卡分期僅能全額退款
- `50009 atm refund data is not ready` → ATM 退款資料尚未備齊，隔日再試
- `50016 bank code not support atm refund` → 原匯款銀行不支援退回原帳戶

### 對帳 API 回應解析錯誤

**問題**：`json.loads` 解析 `/v1/checking/{date}/{type}` 回應時失敗

**原因**：對帳 API 為「多個 JSON 物件並列」的特殊格式，非標準 JSON 陣列。請使用 `json.JSONDecoder().raw_decode()` 逐一解析 (參考 [查詢對帳資料](#查詢對帳資料) 章節範例)。

### 金額限制錯誤

**問題**：`20005 params is not valid` (金額相關)

**檢查**：

| pay_type | 最低 | 最高 |
|----------|------|------|
| `CARD` | 30 | 199,999 |
| `PI` | 1 | 199,999 |
| `ATM` | 1 | 49,999 |
| 超商取貨 | 65 | 20,000 |
| `BCODE` | 25 | 20,000 |

### 拍錢包訂單建立失敗

**問題**：`20019 create pi payment fail` 或 `20020 pi payment is disable`

**解決**：

- `20020`：合作方尚未啟用拍錢包收款，請於後台開啟並送審
- `20022`：拍錢包訂單金額超過後台設定的單筆上限，請至後台調整

---

## 官方資源

- **API 申請與後台**：https://web.pchomepay.com.tw/api-setting/environment-setting
- **WooCommerce 模組**：[PChomePay WooCommerce User Guide](https://docs.google.com/document/d/1ItCUQvY0A4VeVAlOdAMbt48lKB-xlNVZCu7E6L9d0Mg/edit)
- **舊版購物車模組原始碼**：https://github.com/PChomePayPlugin
- **拍錢包退款規則**：https://web.piapp.com.tw/faq/bs18122107/
- **聯名卡 5% P 幣回饋**：https://www.esunbank.com/zh-tw/personal/credit-card/intro/co-branded-card/pi-card
- **技術服務信箱**：tech_support@pchomepay.com.tw

---

最後更新：2026/05/07
