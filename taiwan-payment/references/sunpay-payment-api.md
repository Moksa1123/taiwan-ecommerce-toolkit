# 紅陽科技 SunPay 金流 API 參考

> 開發者專區: https://www.sunpay.com.tw/developers/
> 教學手冊站: https://doc.esafe.com.tw/
> 電子發票平台: https://inv.sunpay.com.tw/
> Captured: 2026-08-08 · doc_access: **public**（手冊免登入公開下載）
> Status: **金流參數層已完整** — 加解密（RSA+SHA256）、4 支端點、交易全欄位、代碼表皆已擷取自手冊 v1.1.0；電子發票側待補
> Source: 金流技術串接手冊 v1.1.0（2026-05-25，51 頁），原始 PDF 存於 `_studies/sunpay/`

## 0. 為什麼收錄——含一個競品訊號

紅陽科技（品牌「紅陽支付」／舊稱 esafe）是台灣老牌金流商，同時做**金流 + 電子發票 + 超商代收 + 物流**。

**值得注意的是**：紅陽的開發者專區目前直接列出「**AI 串接指南（Claude Code Skill）**」：

| 項目 | 版本 | 更新日 |
|---|---|---|
| 金流 AI 串接指南（Claude Code Skill） | v1.1.0 | 2026-07-28 |
| 電子發票 AI 串接指南（Claude Code Skill） | v2.3 | 2026-07-28 |

加上綠界官方已釋出 `ECPay/ecpay-api-skill`（見 `_studies/ecpay-skill-reference/`），這是第二家自己出 skill 的供應商。

> **對本專案的策略含意**：單一供應商的 API skill 正在被供應商自己吃掉。本 toolkit 的差異化不能是「把某一家文件抄得更完整」，而必須是**跨供應商的欄位對照、代碼比對與選型決策**（`field-mappings.csv` / `reasoning.csv` / `recommend.py` 這條線）。

## 1. 服務矩陣

依 `doc.esafe.com.tw` 教學手冊站：

### 金流

| 類別 | 服務 |
|---|---|
| 信用卡 | 紅陽PAY(swipy)、實體刷卡、信用卡、網址付、EDC 刷卡機 |
| 現金 | 網路 ATM、台灣PAY |
| 超商代收付 | 代碼付款、條碼付款 |

### 物流 ⭐

| 服務 |
|---|
| 超商便利送 |
| 宅配通 |

> **這一項值得注意**：紅陽同時提供物流，且含**宅配通**——宅配通本身沒有公開 API（見 [../../taiwan-logistics/references/carrier-direct-access.md](../../taiwan-logistics/references/carrier-direct-access.md)），紅陽是目前盤點到少數可經由聚合商取得宅配通的路徑之一。

### 電子發票

獨立平台 https://inv.sunpay.com.tw/，有專屬技術串接手冊 v2.3。

### 後台功能

系統登入、修改密碼、基本資料、服務設定、交易查詢、出貨列印、撥款查詢、電子發票、退貨申請、文件下載。

## 2. 技術文件

### 直連下載網址（2026-08-08 自開發者頁擷取）

> ✅ **上一輪標記的 404 已解決**：紅陽把技術文件從 `www.sunpay.com.tw/wp-content/uploads/…` 搬到 **Google Cloud Storage**（`storage.googleapis.com/joinchill-image/sunpay_techdoc/…`）。舊連結全數失效，以下為現行網址。

| 分類 | 文件 | 版本 | 更新 | 網址 |
|---|---|---|---|---|
| API 金流串接 | **金流技術串接手冊** | **v1.1.0** | 2026-05-25 | `…/202607/紅陽科技金流服務-金流技術串接手冊V1.1.0.pdf` |
| API 金流串接 | AI 串接指南（Claude Code Skill）| v1.1.0 | 2026-07-28 | `…/202607/sunpay-payment-skill-v1.1.0-v1.zip` |
| API 金流串接 | 範例程式碼 PHP | — | — | `…/202603/金流範例程式SampleCode_PHP.zip` |
| API 金流串接 | 範例程式碼 JAVA | — | — | `…/202603/金流範例程式SampleCode_JAVA.zip` |
| 電子發票 | **電子發票技術串接手冊** | **v2.3** | — | `…/202603/紅陽科技電子發票技術串接手冊V2.3.pdf` |
| 電子發票 | AI 串接指南（Claude Code Skill）| v2.3 | 2026-07-28 | `…/202607/sunpay-einvoice-skill-v2.3-v1.zip` |
| 購物車模組 | WooCommerce | 10.1.0 | 2026-01-30 | `…/202603/sunpay_WooCommerce_1.0.2.zip` |
| 購物車模組 | Magento 2 | 2.4.7-p1 | 2025-12-30 | `…/202603/sunpay-Magento2.zip` |
| 購物車模組 | OpenCart | 4.1.0.3 | 2025-12-30 | `…/202603/sunpay_OpenCart.zip` |

前綴皆為 `https://storage.googleapis.com/joinchill-image/sunpay_techdoc/`。

### 測試環境申請

| 用途 | 入口 |
|---|---|
| 金流測試環境 | https://testmerchant.sunpay.com.tw/#/formTabs |
| 電子發票測試帳號 | https://testinv.sunpay.com.tw/sign-up |

> ✅ **版本號疑問已釐清**：開發者頁現行的**金流技術串接手冊就是 v1.1.0**（2026-05-25），AI skill 恰巧同為 v1.1.0。先前看到的「v4.6（2025/10）」是**改版前舊站的檔名**，該連結已失效。以 v1.1.0 為準。

| 其他文件 | 取得 |
|---|---|
| 教學手冊站 | https://doc.esafe.com.tw/ |
| 操作手冊 | https://www.sunpay.com.tw/manual/ |
| 實質受益人聲明書 | `…/202603/產-20230530法人或團體實質受益人聲明書.pdf` |

## 3. 加解密機制 — RSA 分段加密 + SHA256 簽章

> Source: 金流技術串接手冊 v1.1.0 §4.2

⚠️ **紅陽是本 skill 收錄的 14 家中唯一使用 RSA 的**。其他家不是 SHA256 檢查碼（ECPay）就是 AES 對稱加密（NewebPay / PAYUNi / ezPay）。**既有的加解密函式一律不能沿用。**

送出的 form 只有四個欄位：

| 欄位 | 說明 |
|---|---|
| `web` | 特店代號 |
| `send_time` | 交易時間，格式 **`fffssmmHHyyyyMMdd`**（毫秒+秒+分+時+年+月+日）|
| `rsamsg` | 業務參數 RSA 加密後結果 |
| `check_value` | SHA256 簽章 |

> ⚠️ **`send_time` 的格式是反的**——毫秒在最前面、日期在最後，不是一般的 `yyyyMMddHHmmssfff`。
> ⚠️ **超過 120 秒即視為無效交易**，主機需校時。

### 3.1 `rsamsg` 加密（§4.2.1）

```
業務 JSON  →  URLEncode  →  RSA 分段加密（每段 117 byte）  →  Base64
```

- 公鑰為 **PEM 格式**，由紅陽提供
- **分段大小 117 byte**（1024-bit RSA 的 PKCS#1 v1.5 上限）
- 業務參數分成 `head` 與 `body` 兩層

解密（§4.2.2，收 callback 時）：

```
rsamsg  →  Base64 decode  →  分段解密（每段 128 byte）  →  URLDecode  →  JSON
```

> 加密分段 **117**、解密分段 **128**，兩者不同——這是 RSA 密文區塊固定 128 byte（1024 bit）而明文區塊需扣掉 11 byte padding 的結果。實作時很容易寫錯成同一個數字。

### 3.2 `check_value` 簽章（§4.2.3）

```
1. head 與 body（含內容）做 ASCII 升序排序
2. 整份 JSON 做 URLEncode，尾端直接串上 SHA2 密鑰
3. SHA256 → check_value
```

> ⚠️ **`null` 值的參數不參與簽名**（官方明註）。
> ⚠️ **ASCII 排序是強制的**，手冊在兩處重複警告「請務必將 head 與 body 參數進行 ASCII 排序，以免加密失敗」。
> ⚠️ SHA2 密鑰是**直接串接在 URLEncode 後字串的尾端**，不是 ECPay 那種 `HashKey=…&…&HashIV=…` 前後包夾。

手冊附錄 3 另附**各程式語言 URL_Encode 編碼表**（Java URLEncoder / RFC 3986 / PHP urlencode / PHP rawurlencode / C# UrlEncode / C# EscapeDataString 六欄對照）——跨語言實作前先查這張表。

## 4. API 端點

| 功能 | 正式 | 測試 |
|---|---|---|
| **交易 Cash** | `https://trade.sunpay.com.tw/v4/cash` | `https://testtrade.sunpay.com.tw/v4/cash` |
| **查詢 Check** | `https://trade.sunpay.com.tw/v4/query/PaymentCheck` | `https://testtrade.sunpay.com.tw/v4/query/PaymentCheck` |
| **請款 Capture** | `https://trade.sunpay.com.tw/v3/Service/CardCapture` | `https://testtrade.sunpay.com.tw/v3/Service/CardCapture` |
| **退款 Refund** | `https://trade.sunpay.com.tw/v3/Service/CardRefund` | `https://testtrade.sunpay.com.tw/v3/Service/CardRefund` |

> 注意 **交易與查詢是 `/v4/`，請款與退款仍是 `/v3/`**——同一份手冊裡版號不一致，不是筆誤。

特店需於**特約商店管理平台 → 系統設定 → 開發者專區 → 特店 URL 設定**設定三個接收網址：

| 設定 | 用途 |
|---|---|
| 交易完成轉導網址 | 前端畫面轉跳 |
| 交易結果通知網址 | **背景 CallBack，應以此為準** |
| 貨態更新接收網址 | 物流狀態更新 |

> **CallBack 補發機制**：30 分鐘內每 5 分鐘補發一次，**超過 30 分鐘不再補發**。
> ⚠️ **回傳網址不可帶 port**（如 `https://example.com:8080/x.php`），紅陽基於資安風險控管會擋。
> 貨態通知為 **HTTP FORM POST key-value，非 JSON**。

## 5. 交易 (Cash) 請求參數

外層 form 四欄如 §3。以下為 `rsamsg` 加密前的內容。

### `head`

| 參數 | 描述 | 長度 | 必填 |
|---|---|---|---|
| `send_time` | 交易時間 `fffssmmHHyyyyMMdd` | 17 | ✅ |
| `web` | 特店代號 | 32 | ✅ |

### `body` — 共同參數

| 參數 | 描述 | 長度 | 必填 | 說明 |
|---|---|---|---|---|
| `td` | 特店訂單編號 | 50 | ✅ | 不可重複，限英數 |
| `mn` | 交易金額 | 8 | ✅ | **正整數，不可有小數點或千位符號** |
| `card_type` | 交易類別 | 2 | | 見下表；不帶則由消費者於支付頁選擇 |
| `country_type` | 支付頁語系 | 3 | | `cht` 繁中（預設）|
| `currency` | 交易幣別 | 4 | | `TWD`（預設）|
| `order_info` | 商品名稱 | 50 | | **有申請隨交易開發票時即為發票品項**；空值預設「商品一批」|
| `email` | 消費者信箱 | 100 | | |
| `sna` | 消費者姓名 | 30 | | 不可有 `*'<>[]"` |
| `sdt` | 消費者電話 | 20 | | 純數字如 `0911123123`；搭配超商取貨時到店會發簡訊 |
| `note1` / `note2` | 備註 | 400 | | 交易完成時原樣回傳；不可有 `*'<>[]"` |
| `lgs_flag` | 物流啟用 | 1 | 條件 | `0`/不帶=不啟用、`1`=啟用。**`card_type=09` 時必須為 1**；**訂單金額 > 2 萬元無法使用物流** |
| `store_type` | 超商類型 | 1 | 條件 | `0`/不帶=四大超商、`1`=7-11、`2`=全家、`3`=OK、`4`=萊爾富 |
| `buyer_cid` | 買方統編 | 8 | | 隨交易開發票用 |
| `carrier_type` | 載具類型 | 1 | | `1` 手機條碼、`2` 自然人憑證 |
| `carrier_id` | 載具號碼 | 16 | 條件 | `carrier_type=1/2` 時必填 |
| `donation_code` | 捐贈碼 | 7 | | |

> ⚠️ **`buyer_cid` / `donation_code` / `carrier_type` 三擇一**，不可並存。
> 載具格式：手機條碼第 1 碼必為 `/`，後 7 碼為 `0-9 A-Z + - .`（英文限大寫）共 8 碼；自然人憑證前 2 碼 `A-Z` + 後 14 碼數字共 16 碼。

### `card_type` 交易類別代碼

| 類別 | 代碼 | 支付方式 |
|---|---|---|
| 信用卡類 | `01` | 信用卡 |
| 信用卡類 | `02` | 銀聯卡 |
| 行動支付類 | `03` | **Apple Pay / Google Pay**（同一代碼）|
| 超商代收類 | `06` | 超商代碼 |
| 超商代收類 | `07` | 超商條碼 |
| 銀行轉帳類 | `08` | 虛擬帳號 |
| 超商物流類 | `09` | 超商取貨付款 |
| 電子錢包類 | `10` | **街口支付** |

> 街口是紅陽目前唯一列出的電子錢包代碼。想直接串街口的其他能力（訂閱、街口幣）仍須直連，見 [jkopay-payment-api.md](jkopay-payment-api.md)。

### `body` — 信用卡專屬（`card_type=01`）

| 參數 | 描述 | 長度 | 說明 |
|---|---|---|---|
| `save_card` | 快速付款 | 1 | `0` 不啟用（預設）／ `1` 啟用 |
| `save_card_token` | 快速付款 token | 36 | **`save_card=1` 時必填**，綁定付款人與卡號，限英數 |
| `term` | 分期期數 | 2 | `3`/`6`/`12`/`18`/`24`/`30`；不分期帶空值。**銀聯卡不支援分期** |
| `bank_code_list` | 指定發卡銀行 | 3 | 銀行代碼，如台新 `812`。多組用 Array：`['812','822']`。**街口支付不支援此功能** |

**快速付款的實際行為**：首次交易時消費者在收銀台勾選「記住結帳資訊」，紅陽將 `save_card_token` 對應到該張卡。下次帶同一個 token，收銀台會自動帶出前六後四碼，消費者只需填背面末三碼。**紅陽只保留最近一次成功交易的卡號資料**；消費者取消勾選即清除。

### `body` — 虛擬帳號（`card_type=08`）

| 參數 | 描述 | 長度 | 說明 |
|---|---|---|---|
| `agency_bank` | 轉入銀行別 | 3 | ⚠️ **目前僅支援中國信託，請帶空值** |
| `due_date` | 繳款期限 | 8 | `YYYYMMDD`，可設 **1～180 天**；空值預設交易日 +7 天 |

### `body` — 超商代碼／條碼（`card_type=06` / `07`）

| 參數 | 描述 | 長度 | 說明 |
|---|---|---|---|
| `due_date` | 繳款期限 | 8 | 同上，1～180 天，預設 +7 天 |
| `product` | 商品名稱 | 1000 | Array 格式，**最多 10 項**，每項名稱最多 100 字元 |

`product[]` 子欄位：`no`（序號）、`product_name`、`product_price`（**須 > 0**）、`product_quantity`（**須 > 0**）。

> ⚠️ **`Σ(單價 × 數量)` 必須等於 `mn` 交易金額，不符者不允許交易**。
> 商品數量過多或金額為負數時，官方建議整合成單一商品名稱（如「百貨商品」）送出。

### `body` — 超商取貨付款（`card_type=09`）

| 參數 | 描述 | 長度 | 必填 | 說明 |
|---|---|---|---|---|
| `recevier_name` | 收件人姓名 | 30 | ✅ | 中英文皆可，不可有 `*'<>[]"` |
| `recevier_phone` | 收件人電話 | 20 | ✅ | 純數字；**貨到門市會發取貨通知簡訊** |
| `recevier_mail` | 收件人信箱 | 100 | | 貨到門市會發通知信 |

> ⚠️ **參數名是 `recevier_*` 不是 `receiver_*`**——官方拼字如此（`i` 與 `e` 顛倒）。但**回應**參數卻是正確拼法 `receiver_name` / `receiver_phone`。送出與接收兩邊拼法不同，很容易寫錯。

## 6. 回應與狀態代碼

### `pay_result` — 交易 CallBack

| 值 | 意義 |
|---|---|
| `10` | 交易成功 |
| `11` | 交易失敗 |
| `12` | 已建立 |

### `pay_result` — 查詢 (Check) API

**查詢的代碼集比交易 CallBack 大，且 `12` 的意義完全不同**：

| 值 | 意義 |
|---|---|
| `06` | 紅陽交易編號或特店訂單編號必須擇一 |
| `10` | 交易成功 |
| `11` | 交易失敗 |
| `12` | **查無該筆訂單**（交易 CallBack 的 `12` 是「已建立」）|
| `13` | 交易未完成 |
| `14` | 訂單退款 |
| `15` | 交易取消 |

> ⚠️ **這是紅陽最容易踩的坑**：同一個欄位名 `pay_result`、同一個值 `12`，在交易通知裡是「已建立」，在查詢 API 裡是「查無訂單」。**兩邊的判斷邏輯必須分開寫。**

### `refund_status` — 退款狀態

| 值 | 意義 |
|---|---|
| `0` | 未退款 |
| `1` | 退款處理中 |
| `2` | 退款完成 |
| `3` | 退款失敗 |
| `4` | 取消退款 |

### 各支付方式的專屬回應欄位

**虛擬帳號**（取號完成時回傳）：`account_id`（虛擬帳號，**共 14 碼**）、`account_name`、`bank_code`、`bank_name`、`due_date`。
付款完成時另回：`pay_agency`（消費者轉出銀行代碼，如 `812` 台新）、`pay_agency_memo`（轉出帳號，部分隱碼；**臨櫃或無摺轉帳則不回傳**）。

**超商代碼／條碼**（取號完成時回傳）：`due_date`、`pay_code`（繳費代碼）、`barcodeA` / `barcodeB` / `barcodeC`（三段條碼）。
付款完成時另回：`pay_agency`（門市代碼）、`pay_agency_name`（門市名稱）。

**超商取貨付款**（取號完成時回傳）：`delivery_type`（`2`=超商取貨付款）、`store_id`、`store_name`、`lgs_type`（`C2C`=超商店到店）、`receiver_name`（⚠️ **因個資法部分字元轉為隱碼，如「王○明」**）、`receiver_phone`。

### 物流狀態通知（`4.7`）

超商物流中心 → 紅陽 → 特店設定的「物流狀態接受網址」。

⚠️ **格式與交易 CallBack 不同**：`HTTP FORM POST` key-value，**非 JSON**；且**所有資料皆經 URL Encode**，需先 URL Decode 再處理（UTF-8）。

欄位：`trade_no`、`web`、`Td`（⚠️ **大寫 T**，與請求端的 `td` 不同）、`note1`、`note2`、`SendType`（`1`=背景傳送）、`CargoNo`（寄件代碼）、`StoreType`（物流狀態代碼）、`StoreMsg`（狀態文字說明）、`ChkValue`（檢查碼）。

> ⚠️ **手冊未提供 `StoreType` 的代碼對照表**，只說明「物流狀態之代碼」。實務上需以 `StoreMsg` 的文字說明為主，或洽紅陽索取代碼表。

### 測試環境的模擬方式（附錄 1）

| 支付方式 | 測試方式 |
|---|---|
| 信用卡（一次付清）| 卡號 `4938170188888994`，效期 `12/28`，末三碼 `541` |
| 信用卡（分期）| 卡號 `5430450130000033`，效期 `12/28`，末三碼 `534` |
| Apple Pay / Google Pay / 街口 | 付款畫面點「模擬付款成功／失敗」 |
| 銀聯卡 | 依付款畫面操作，結果即模擬為成功 |
| 超商代碼／條碼／虛擬帳號 | 取號後至**特約商店管理平台 → 訂單查詢**執行「模擬付款」，系統即回傳 CallBack |

> 測試環境的信用卡以**測試授權碼**模擬完成，實際不會發動至收單銀行。

### 隨交易開立發票的規則（附錄 2）

| 項目 | 規則 |
|---|---|
| 申請 | 需另向紅陽申請，**且必須同時串接紅陽電子發票服務** |
| 設定 | 特店專區 → 開發者專區 → 開立發票設定，啟用後至 https://inv.sunpay.com.tw/ 取得商店代號、Hash Key、Hash IV |
| 開立時機 | 消費者**付款成功後**才開立 |
| 退款 | ⚠️ **金流退款不會連動作廢或折讓發票**，須自行登入發票後台處理 |
| 衝突 | ⚠️ 若已自行串接發票系統，**請勿啟用**隨交易自動開立，會重複開立 |

## 7. 購物車模組

| 平台 | 版本 |
|---|---|
| WooCommerce | v10.1.0 |
| Magento 2 | v2.4.7-p1 |
| OpenCart | v4.1.0.3 |

> 三大自架購物車都有官方模組，對 WordPress/WooCommerce 專案而言這是實用的加分項（本 repo 的使用者情境常涉及 WooCommerce）。

## 8. 串接流程

1. 申請測試帳號
2. 下載串接手冊及 sample code
3. 串接購物車（或自建）

聯絡：(02) 2502-6969

## 9. 待補

**金流側已完成**：端點（§4）、加解密（§3）、交易全欄位（§5）、代碼表（§6）。

**金流側已完整**：端點（§4）、加解密（§3）、交易全欄位含五種支付方式的專屬參數（§5）、回應與代碼（§6）。

| 項目 | 優先 | 來源 | 備註 |
|---|---|---|---|
| 請款 / 退款 API 的請求欄位 | 中 | 金流手冊 §4.4–4.5 | 端點與 `refund_status` 已確認 |
| 物流貨態 `StoreType` 代碼表 | 中 | — | ⚠️ **手冊未提供代碼對照**，僅說明是「物流狀態之代碼」，需洽紅陽索取 |
| 統一錯誤碼表 | 中 | — | ⚠️ 手冊無獨立錯誤碼章節，僅有各 API 的 `pay_result`；已全數收錄於 §6 |
| 對照紅陽官方 Claude Code Skill 的涵蓋範圍 | 高 | skill zip | 決定我們補到什麼程度 |

電子發票側見 [../../taiwan-invoice/references/SUNPAY_API_REFERENCE.md](../../taiwan-invoice/references/SUNPAY_API_REFERENCE.md)。

## 10. 來源

- 開發者專區 — https://www.sunpay.com.tw/developers/
- 教學手冊站 — https://doc.esafe.com.tw/
- 操作手冊 — https://www.sunpay.com.tw/manual/
- 金流串接頁 — https://www.sunpay.com.tw/金流串接/
- 電子發票整合服務 — https://inv.sunpay.com.tw/
