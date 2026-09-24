# ezPay 簡單付 金流 API Reference

> **依官方技術串接手冊撰寫，加解密已與手冊範例逐位元組比對**（`tests/vectors/ezpay-payment.json`，
> CI 執行 `scripts/verify-examples.py`）。
>
> 官方 API 文件頁：<https://www.ezpay.com.tw/info/Service_intro/api_document/member>（2026-09 擷取）
>
> | 手冊 | 版本 | 內容 |
> |------|------|------|
> | `API_E_wallet_ezPay_1.0.0.pdf` 電子支付平台技術串接手冊（標準版） | 程式 1.0.0／文件 W1.0.2（2026-04-20） | 境內收款：7 支 API |
> | `API_Cross_Trans_ezPay_1.0.1.pdf` 跨境網路交易串接手冊 | 1.0.1 | 支付寶／微信 MPG |
> | `API_Cross_Trans_search_ezPay_1.0.1.pdf` 跨境交易單筆查詢 | 1.0.1 | QueryInfo |
> | `API_Cross_Trans_refund_ezPay_1.0.3.pdf` 跨境交易退款 | 1.0.3 | RefundInfo |
> | `API_Cross_Trans_physical_ezPay_1.0.0.pdf` 跨境實體商店串接手冊（標準版） | 檔名 1.0.0／文件 ezPay_2.0.0（2019-11-05） | 門市掃消費者支付寶／微信條碼 |


---

## 目錄

1. [ezPay 是什麼](#ezpay-是什麼)
2. [加解密（兩組 API 共用）](#加解密兩組-api-共用)
3. [電子支付平台 API（境內）](#電子支付平台-api境內)
4. [跨境網路交易 API](#跨境網路交易-api)
5. [跨境實體商店 API](#跨境實體商店-api)
6. [錯誤代碼](#錯誤代碼)
7. [手冊中的不一致之處](#手冊中的不一致之處)
8. [與藍新 NewebPay 的差異](#與藍新-newebpay-的差異)

---

## ezPay 是什麼

簡單行動支付股份有限公司（藍新金融科技集團）經營的**電子支付機構**。收款方必須是 ezPay 會員並開啟商店；
交易皆為實名、並有價金保管。電子支付平台支援的支付工具（手冊「規格介紹」）：

| PaymentType | 說明 |
|-------------|------|
| `EPACC` | ezPay 電子支付帳戶餘額付款（先扣儲值帳戶，不足再扣收款帳戶） |
| `ACCLINK` | 約定連結存款帳戶付款 |
| `CREDIT` | ezPay 約定本人信用卡付款 |
| `TWQR` | TWQR 整合支付（跨機構：台灣 Pay、街口、全支付、悠遊付、一卡通、icash Pay、全盈+PAY、歐付寶、橘子支付、玉山 Wallet…） |

EPACC / ACCLINK / CREDIT 是**自機構交易**（付款方用 ezPay）；TWQR 是**跨機構交易**（付款方用其他電子錢包掃碼）。

---

## 加解密（兩組 API 共用）

| 步驟 | 內容 |
|------|------|
| 1 | 參數以 `urlencode`（`http_build_query`）組成字串 |
| 2 | AES-256-CBC，Key = HashKey（32 字元）、IV = HashIV（16 字元），**PKCS#7 以 32 bytes 為區塊**（手冊：BlockSize=32） |
| 3 | 密文轉小寫十六進位 → `EncryptData`（跨境為 `TradeInfo` / `QueryInfo` / `RefundInfo`） |
| 4 | `SHA256("HashKey={HashKey}&{密文}&HashIV={HashIV}")` 轉大寫 → `HashData`（跨境為 `TradeSha` / `QuerySha` / `RefundSha`） |

> **32-byte padding 是必要的。** 電子支付平台手冊附件二的範例只有用 32 bytes 補齊才能重現；
> 用 AES 標準的 16 bytes（例如 `Crypto.Util.Padding.pad(data, 16)`）加密出來的密文不同。

<!-- verify: ezpay -->
```python
import hashlib
import urllib.parse
from Crypto.Cipher import AES


def encrypt_data(params, hash_key, hash_iv):
    """params：dict 或 (key, value) list；回傳 hex 密文"""
    data = urllib.parse.urlencode(params).encode('utf-8')
    n = 32 - len(data) % 32                      # 32-byte PKCS#7
    data += bytes([n]) * n
    return AES.new(hash_key.encode(), AES.MODE_CBC, hash_iv.encode()).encrypt(data).hex()


def decrypt_data(cipher_hex, hash_key, hash_iv):
    data = AES.new(hash_key.encode(), AES.MODE_CBC, hash_iv.encode()).decrypt(bytes.fromhex(cipher_hex))
    n = data[-1]
    if not 1 <= n <= 32 or data[-n:] != bytes([n]) * n:
        raise ValueError('padding 錯誤（金鑰或 IV 不正確）')
    return data[:-n].decode('utf-8')


def hash_data(cipher_hex, hash_key, hash_iv):
    raw = f'HashKey={hash_key}&{cipher_hex}&HashIV={hash_iv}'
    return hashlib.sha256(raw.encode('utf-8')).hexdigest().upper()
```

解密後的格式：

- 電子支付平台：**urlencoded 字串**，巢狀欄位攤平成 `Result[TradeNo]=...`（`parse_qsl` 後自行還原成巢狀）
- 跨境：**JSON**（`{"Status":..., "Message":..., "Result":{...}}`）

完整實作（含 Result 還原、驗章、各 API 包裝）見 `examples/ezpay-payment-example.py`。

---

## 電子支付平台 API（境內）

### 環境

| | 測試 | 正式 |
|---|------|------|
| 平台（註冊、取得 Hash Key/IV） | `https://cwww.ezpay.com.tw/` | `https://www.ezpay.com.tw/` |
| API | `https://cpayment.ezpay.com.tw/API/Twqr/{APIID}` | `https://payment.ezpay.com.tw/API/Twqr/{APIID}` |

測試商店建立後自動審核開通；預設只啟用電子帳戶，信用卡需在【管理商店/商店資料設定】→【詳細資料】點「申請啟用」。
正式商店審核約 3–5 個工作天。Hash Key / IV 在【銷售中心】→【管理商店/商店資料設定】→【詳細資料】。

所有請求：`POST`、`Content-Type: application/x-www-form-urlencoded`、UTF-8。回應 `Content-Type: text/html`，內容為 JSON。

### 7 支 API

| # | API | APIID | 方向 |
|---|-----|-------|------|
| 1 | 訂單建立 | `SCreateTWQR` | 商店 → ezPay |
| 2 | 訂單修改及取消 | `SUpdateTWQR` | 商店 → ezPay |
| 3 | 交易結果背景異步通知 | `SPayTWQRNotify` | ezPay → NotifyURL |
| 4 | 交易結果轉導暨前景通知 | `STWQRReturn` | ezPay → ReturnURL（瀏覽器） |
| 5 | 交易退款 | `STWQRRefund` | 商店 → ezPay |
| 6 | 訂單暨交易結果查詢 | `SGetTWQR` | 商店 → ezPay |
| 7 | 退款查詢 | `SGetTWQRRefund` | 商店 → ezPay |

### 外層欄位（每支 API 相同）

| 欄位 | 必填 | 說明 |
|------|------|------|
| `APIID` | V | 如 `SCreateTWQR` |
| `Version` | V | `1.0` |
| `UID` | V | 商店代號（手冊範例 `PG300000725648`） |
| `EncryptData` | V | 加密資料 |
| `HashData` | V | 雜湊資料 |

EncryptData 內**一律**含 `TimeStamp`（Unix 秒）、`APIID`、`Version`、`UID`，再加上各 API 自己的參數。

回應／通知外層：`Status`（`SUCCESS` 或錯誤代碼）、`Message`、`APIID`、`Version`、`UID`、`EncryptData`、`HashData`；
EncryptData 解密後含 `TimeStamp`、`Status`、`Message`、`APIID`、`Version`、`UID`、`Result[...]`、`ResponseType`（如 `R1`）。

> **收到回應或通知一定要先驗 HashData 再解密。** 背景通知（NotifyURL）才是可信的結果來源；
> ReturnURL 是瀏覽器導回，只能用來顯示頁面。

### 1. 訂單建立 `SCreateTWQR`

| 參數 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `Mode` | V | int(1) | 1=商店指定金額＋商店訂單編號；2=商店指定金額、ezPay 產訂單號；3=消費者輸入金額＋商店訂單編號；4=消費者輸入金額、ezPay 產訂單號 |
| `Template` | | String(10) | 支付頁模板，預設 `STANDARD01` |
| `LangType` | | String(5) | 1=中文（預設）、2=英文 |
| `TWQRLifeTime` | | int(7) | QR Code 有效秒數，預設 300；上限 31 天（2678400） |
| `ExpireTime` | | String(19) | `YYYY-MM-DD HH:MM:SS`，有值時優先於 TWQRLifeTime |
| `WebToAppEnabled` | | int(1) | 1=開啟中轉頁（預設）、2=關閉、3=關閉並以 API 回應中轉頁參數（回傳 `WebtoApp`） |
| `MerchantOrderNo` | Mode 1/3 必填；2/4 必須空白 | String(20) | 英數與底線，同商店不可重複 |
| `NotifyURL` / `ReturnURL` / `ClientBackURL` | | String | 背景通知／前景轉導／支付頁「返回商店」 |
| `Currency` | V | String(3) | `TWD` |
| `OrgOrderAmt` | | int(8) | 原始訂單金額，未帶時等於 OrderAmt |
| `OrderAmt` | Mode 1/2 必填；3/4 必須空白 | int(8) | 應付金額，≤ OrgOrderAmt、不得為 0 |
| `ItemDesc` | V | String(50) | 商品資訊 |

成功回應 `Result`：`Ptoken`（訂單 Token，後續修改/取消要用）、`OrderStatus`（1=待付款）、`MerchantID`、
`MerchantOrderNo`、`TradeNo`（亦為 TWQR 訂單編號）、`Currency`、`OrgOrderAmt`、`OrderAmt`、`ItemDesc`、
`RequestTime`、**`PaymentPageURL`**（導向消費者付款）、**`TWQRCode`**（給其他錢包掃描）、`ExpireTime`、
`NotifyURL`、`ReturnURL`、`ClientBackURL`、`WebtoApp`。

### 2. 訂單修改及取消 `SUpdateTWQR`

| 參數 | 必填 | 說明 |
|------|------|------|
| `TradeNo` | V | 交易序號 |
| `Ptoken` | V | 建立訂單時取得 |
| `UpdateAction` | V | 1=刪除訂單；2=更新訂單資訊 |
| `ExpireTime` / `NotifyURL` / `ReturnURL` / `ClientBackURL` | UpdateAction=2 時至少一個 | |

只能修改**待付款**狀態的訂單（否則 `SUTR0203`）。

### 3–4. 交易結果通知 `SPayTWQRNotify`（背景）／`STWQRReturn`（前景）

`Result` 主要欄位：`Ptoken`、`OrderStatus`、`UID`、`MerchantOrderNo`、`TradeNo`、`Currency`、`OrgOrderAmt`、
`OrderAmt`、`AmtPaid`（扣除紅利/折抵後的實付金額）、`PaymentType`、`RequestTime`、`PaymentTime`（待確認時為 `-`）。
依支付工具另有：

- 自機構：`BuyerMemNo`、`BuyerEPANo`
- 信用卡：`RespondCode`、`Auth`、`AuthDate`、`AuthTime`、`AuthBank`、`Card6No`、`Card4No`、`ECI`、`CardIssuer`、`CardBrand`、`CardType`
- 約定連結帳戶：`AccLinkMSGNo`、`AccLinkRTNCode`、`AccLinkRTNMsg`、`AccLinkBank`、`AccLinkNo`
- TWQR：`BuyAccNo`、`BankCode`、`BankName`、`CarrierID`（手機條碼）、`FeeType`、`BusDate`、`FiscSTAN`、`FiscRC`、`QrRefNo`

### 5. 交易退款 `STWQRRefund`

| 參數 | 必填 | 說明 |
|------|------|------|
| `MerchantRefundNo` | V | 商店自訂退款序號，不可重複 |
| `RefundBarCode` / `MerchantOrderNo` / `TradeNo` | 三擇一 | **不可同時帶入**（`STRD0018`） |
| `RefundType` | V | `1`（退款） |
| `Currency` | V | `TWD` |
| `RefundAmt` | V | 當次退款金額 |

回應 `Result`：`OrderStatus`、`RefundStatus`、`RefundType`、`RefundBarCode`、`MerchantOrderNo`、`TradeNo`、
`Currency`、`RefundAmt`、`RefundLimit`（剩餘可退）、`RefundTime`、`MerchantRefundNo`、`Rtoken`（退款 Token）。

### 6. 訂單暨交易結果查詢 `SGetTWQR`

`MerchantOrderNo` 與 `TradeNo` **擇一**（同時帶入回 `SGTR0116`）。回應除交易欄位外另含 `TotalRefundAmt`、
`RefundLimit`、`Mode`（查詢結果多一個 5=立牌模式）、`PaymentPageURL`、`TWQRCode` 等。

### 7. 退款查詢 `SGetTWQRRefund`

`Rtoken` 與 `MerchantRefundNo` 擇一。回應 `Result`：`RefundStatus`、`MerchantOrderNo`、`TradeNo`、
`MerchantRefundNo`、`Rtoken`、`RefundType`、`Currency`、`RefundAmt`、`RefundTime`、`RefundCompleteTime`。

### 狀態代碼

`OrderStatus`（查詢 API 的完整列表）：

| 值 | 說明 |
|----|------|
| 1 | 待付款 |
| 2 | 已付款 |
| 3 | 部分退款 |
| 4、5 | 全額退款（手冊註明兩者皆為全額退款） |
| 6 | 付款失敗 |
| 7 | 等候付款結果中 |
| 8 | 訂單逾時未付款 |
| 9 | 刪除訂單 |
| 10 | 暫時無法確定訂單付款狀態 |

`RefundStatus`：1=退款成功、2=退款失敗、3=退款處理中、9=無法確認退款請求狀態。

> 7、10 不是最終狀態，應以查詢 API 或後續通知確認，不要當成失敗。

---

## 跨境網路交易 API

支付工具只有 **`ALIPAY`（支付寶）** 與 **`WECHAT`（微信支付）**，皆為即時交易；商店屬性需選「跨境網路商店」。
測試交易：支付寶會立刻完成，微信會顯示模擬 QR Code、30 秒後完成。

### 環境

| API | 測試 | 正式 | Version |
|-----|------|------|---------|
| 交易（前景 Form Post） | `https://cpayment.ezpay.com.tw/MPG/mpg_gateway` | `https://payment.ezpay.com.tw/MPG/mpg_gateway` | `1.0` |
| 單筆查詢 | `https://cpayment.ezpay.com.tw/API/merchant_trade/query_trade_info` | `https://payment.ezpay.com.tw/API/merchant_trade/query_trade_info` | `1.0` |
| 退款 | `https://cpayment.ezpay.com.tw/API/merchant_trade/trade_refund` | `https://payment.ezpay.com.tw/API/merchant_trade/trade_refund` | `2.1` |

### 交易

外層：`MerchantID`、`Version`、`TradeInfo`、`TradeSha`。TradeInfo 內：

| 參數 | 必填 | 說明 |
|------|------|------|
| `TimeStamp` | V | Unix 秒 |
| `MerchantID` | V | 商店代號 |
| `Version` | V | `1.0` |
| `MerchantOrderNo` | V | 英數與底線，最長 40，不可重複 |
| `Amt` | V | 新台幣整數 |
| `ItemDesc` | V | 最長 50 |
| `CrossMobile` | | 0=Web（預設）、1=Wap（手機 RWD） |
| `TradeLimit` | | 交易限制秒數 60–900 |
| `ClientBackURL` | | 取消時的返回網址 |

NotifyURL / ReturnURL **在 ezPay 後台設定**（手冊「交易支付系統回傳參數說明」），不是交易參數。

通知：外層 `Status`、`Version`、`MerchantID`、`TradeInfo`、`TradeSha`；TradeInfo 解密為 JSON，
`Result` 含 `MerchantID`、`Amt`、`TradeNo`、`MerchantOrderNo`、`PaymentType`、`PayTime`、`IP`、
`EscrowBank`（價金保管信託銀行，如 `HNCB` 華南銀行）、`CrossID`、`USDAmt`、`CNYAmt`。

### 單筆查詢

外層 `MerchantID`、`Version`、`QueryInfo`、`QuerySha`；QueryInfo 內 `TimeStamp`、`MerchantID`、`Version`、
`TradeNo` 或 `MerchantOrderNo`（擇一，建議 TradeNo）。回應 QueryInfo 為 JSON，含 `LastAmt`（剩餘金額）、
`FeeAmt`、`PaymentStatus`（1=付款成功、2=未付款）、`CreateDT`、`PayDT`、`CloseDT`（實際撥款日）等。

### 退款

外層 `MerchantID`、`Version`（`2.1`）、`RefundInfo`、`RefundSha`；RefundInfo 內 `TimeStamp`、`MerchantID`、
`Version`、`TradeNo` 或 `MerchantOrderNo`、`RefundAmt`、`RefundType`（`1`）、`Currency`（`TWD`）。
回應 JSON 的 `Result` 含 `OrderStatus`（3=部分退款、4=全額退款）、`RefundAmt`、`RefundLimit`、`RefundTime`、`RscNo`（退款單號）。

---

## 跨境實體商店 API

門市以設備或 App 掃描境外消費者出示的支付寶／微信付款條碼（一維或二維）收款，另有查詢、退款與異步通知
（《跨境實體商店串接手冊》ezPay_2.0.0，以下頁碼為 PDF 頁尾頁碼）。商店屬性需選「跨境實體商店」，
須經 ezPay 與跨境機構審核開通（p.12）。

### 與跨境網路交易（MPG）的差異

| 項目 | 跨境網路交易 | 跨境實體商店 |
|------|-------------|-------------|
| 情境 | 消費者在網站付款（前景 Form Post） | 門市掃消費者條碼（幕後 API） |
| 網域 | `(c)payment.ezpay.com.tw` | `(c)o2o.ezpay.com.tw` |
| 外層欄位 | `MerchantID`、`Version`、`TradeInfo`、`TradeSha` | `APIID`、`Version`、`UID`、`EncryptData`、`HashData`（同電子支付平台） |
| Version | 1.0（退款 2.1） | 2.0（退款 3.0） |
| PaymentType | `ALIPAY`、`WECHAT` | `ALIPAY`、`WECHATPAY`、`REROUTE`（自動分流，僅請求） |
| NotifyURL | 後台設定 | 後台設定（「設定 API 應用 URL」，p.9） |
| 通知格式 | Form POST | `Content-Type: application/json`（p.7） |
| 錯誤代碼 | `MPG…` | `CTI…`／`CTQ…`／`CTR…` |

### 環境（p.8、p.11）

| APIID | 用途 | 測試 | 正式 |
|-------|------|------|------|
| `SCBOOTradeInfo` | 跨境交易付款 | `https://co2o.ezpay.com.tw/APIS/Trade` | `https://o2o.ezpay.com.tw/APIS/Trade` |
| `SCBOOTradeInfoNotify` | 交易結果異步通知 | 商店指定 URL | 商店指定 URL |
| `SCBGetTradeInfo` | 交易狀態查詢 | `https://co2o.ezpay.com.tw/APIS/Query` | `https://o2o.ezpay.com.tw/APIS/Query` |
| `SCBRefundTradeInfo` | 跨境交易退款 | `https://co2o.ezpay.com.tw/APIS/Trade` | `https://o2o.ezpay.com.tw/APIS/Trade` |

付款與退款共用 `/APIS/Trade`，以 `APIID` 區分。測試平台 `https://cwww.ezpay.com.tw/` 註冊後建立跨境實體測試商店，
系統自動審核開通；Hash Key／IV 在【銷售中心】→【管理商店】→【詳細資料】→「API 串接金鑰」（p.8–9）。

### 加解密（p.5–6）

- AES-256-CBC，Key = Hash Key（32 字元）、IV = Hash IV（16 字元），PKCS#7，密文以十六進位字串輸出（不轉 Base64）
- 加密前參數先 URL encode 以 `&` 串接；建議 `TimeStamp` 放第一個
- `HashData = SHA256("HashKey={Hash Key}&{密文}&HashIV={Hash IV}")` 轉大寫

外層與電子支付平台相同，演算法見上方「加解密」。本手冊沒有提供範例值，32 bytes padding 是否同樣適用無法以手冊驗證。

請求：`POST`、`application/x-www-form-urlencoded`、UTF-8；回應：`application/json`，外層 `Status`、`APIID`、`Version`、
`UID`、`EncryptData`、`HashData`（p.6–7）。

### 付款 `SCBOOTradeInfo`（p.14–16）

外層 `APIID`、`Version`（`2.0`）、`UID`（商店代號，如 `PG300000000066`）、`EncryptData`、`HashData`。EncryptData 內：

| 參數 | 必填 | 型態 | 說明 |
|------|:---:|------|------|
| `TimeStamp` | V | String(50) | Unix 秒 |
| `APIID` | V | String(20) | `SCBOOTradeInfo` |
| `Version` | V | String(5) | `2.0` |
| `UID` | V | String(15) | 商店代號 |
| `MerchantOrderNo` | V | String(40) | 英數與底線，同商店不可重複 |
| `PaymentType` | V | String(10) | `ALIPAY`、`WECHATPAY`、`REROUTE`（自動分流） |
| `BarCode` | V | String(32) | 境外支付機構的付款條碼內容 |
| `Currency` | V | String(3) | `TWD` |
| `OrderAmt` | V | Int(10) | 告知消費者的訂單金額，不得為 0，須 ≥ `AmtPayable` |
| `AmtPayable` | V | Int(10) | 扣除門市折扣後的應付金額（撥付時未扣手續費的收款金額），不得為 0 |
| `ItemDesc` | V | String(50) | 商品資訊 |
| `SeqNo` | | String(64) | 端末機交易序號 |
| `StoreNo` | | String(64) | 門市代號 |
| `POSNo` | | String(64) | POS 機代號 |
| `TestMode` | | String(2) | 僅測試環境：`0` 模擬立即付款完成、`1` 模擬須等候付款方確認 |

回應外層 `Status`：`SUCCESS`、錯誤代碼，或 **`UNKNOW`**（須等候付款方確認）。EncryptData 解密為 JSON：
`TimeStamp`、`APIID`、`Version`、`UID`、`Status`、`Message`、`Result`、`ResponseType`（如 `R1`）（p.17–18）。

`Result`（p.18–19）：`OrderStatus`（1=待付款、2=已付款、5=取消付款、6=付款失敗）、`PaymentType`、`BarCode`、
`MerchantOrderNo`、`TradeNo`、`CrossID`（境外支付機構交易序號）、`Currency`、`OrderAmt`、`AmtPayable`、
`AmtPaid`（扣除紅利、副支付、優惠後的實付金額）、`CNYAmtPaid`、`USDAmtPaid`、`RequestTime`、
`PaymentTime`（等候確認時為 `-`）、`SeqNo`、`StoreNo`、`POSNo`。

回應為 `UNKNOW` 時，以**間隔 2 秒以上**持續呼叫查詢 API，直到訂單為已付款、取消付款或付款失敗，或收到異步通知（p.10）。

### 異步通知 `SCBOOTradeInfoNotify`（p.20–22）

付款方完成付款後 POST 到後台設定的 Notify URL，`Content-Type: application/json`，外層與付款回應相同（`APIID` 為
`SCBOOTradeInfoNotify`）；`ResponseType` 如 `N1`（第一次通知）。`Result` 欄位同付款回應。
回應非 HTTP 200 時最多重送三次（p.10）。

### 交易狀態查詢 `SCBGetTradeInfo`（p.23–27）

EncryptData 內 `TimeStamp`、`APIID`、`Version`（`2.0`）、`UID`，加上 `MerchantOrderNo` 或 `TradeNo`（**擇一，不可同時帶入**）。

`Result`：`OrderStatus`（1=待付款、2=已付款、3=部分退款、4=全額退款、5=取消付款、6=付款失敗）、`MerchantOrderNo`、
`TradeNo`、`Currency`、`OrderAmt`、`AmtPayable`、`AmtPaid`、`FeeAmt`（交易手續費）、`CNYAmtPaid`、`USDAmtPaid`、
`CrossID`、`PaymentType`、`TotalRefundAmt`、`RefundLimit`（剩餘可退）、`SeqNo`、`StoreNo`、`POSNo`、`RequestTime`、
`PaymentTime`、`CloseDT`（實際撥款日，未撥付為 `-`）。

手冊建議查詢時機（p.10）：付款回應 `SUCCESS` 但未收到通知、回應 `UNKNOW`、退款成功後確認狀態、網路中斷無法取得回應。

### 退款 `SCBRefundTradeInfo`（p.28–31）

外層 `Version` 為 **`3.0`**。EncryptData 內：

| 參數 | 必填 | 說明 |
|------|:---:|------|
| `TimeStamp`、`APIID`、`Version`、`UID` | V | `APIID`=`SCBRefundTradeInfo`、`Version`=`3.0` |
| `MerchantOrderNo` / `TradeNo` | 擇一 | 不可同時帶入 |
| `RefundType` | V | `1`（退款） |
| `Currency` | V | `TWD` |
| `RefundAmt` | V | 本次退款金額（整數） |

`Result`：`OrderStatus`（3=部分退款、4=全額退款等）、`RefundType`、`MerchantOrderNo`、`TradeNo`、`Currency`、
`RefundAmt`、`RefundLimit`、`RefundTime`。

退款限制（p.13）：

- 每日 23:55 至隔日 00:05 結帳期間暫停退款（`CTR08002` 該時段無法退款）
- 未結帳累計金額小於退款金額時拒絕（`CTR08003` 在途金額不足）
- 無法確認付款結果的交易，手冊建議直接發動退款（p.11）

手冊寫「每日 00:00 至隔日 00:05 進行當日結帳作業」，結帳完成的交易依約定日期撥款並自動提領至指定帳戶（p.13）。

---

## 錯誤代碼

電子支付平台每支 API 有自己的前綴，219 個代碼全部收在 `data/error-codes.csv`：

| API | 前綴 | 常見 |
|-----|------|------|
| 訂單建立 | `SCTE` | `SCTE0009` HashData 錯誤、`SCTE0301` TimeStamp 錯誤、`SCTE0602` 商店未啟用簡單付 TWQR 交易、`SCTE0603` 訂單已存在（商店訂單編號重複） |
| 訂單修改及取消 | `SUTR` | `SUTR0202` 訂單 Ptoken 不相符、`SUTR0203` 訂單不為待付款狀態 |
| 背景通知 | `SPTN` | `SPTN0203` 訂單及商店未設定 Notify 網址 |
| 前景通知 | `STRN` | |
| 交易退款 | `STRD` | `STRD0018` 三種單號不能同時帶入、`STRD0027` 退款序號重複、`STRD0203` 退款金額超過可退款金額 |
| 訂單查詢 | `SGTR` | `SGTR0116` TradeNo、MerchantOrderNo 不能同時帶入 |
| 退款查詢 | `SGRD` | |

每個前綴的 `0001`–`0010` 都是外層欄位檢查（Version/APIID/UID/EncryptData/HashData 空白或錯誤、商店未啟用），
`9999` 是系統異常。

跨境 MPG 的錯誤代碼：`MPG01000` 送入參數檢查錯誤、`MPG01010` 程式版本錯誤、`MPG01012` 商店訂單編號錯誤、
`MPG01015` 訂單金額錯誤、`MPG01016` 時間戳記錯誤、`MPG02004` 超過交易限制時間、`MPG03001` 訂單資訊解密失敗、
`MPG03007` 查無此商店代號、`MPG03008` 已存在相同的商店訂單編號、`MPG03009` 交易失敗（完整見 CSV）。

跨境實體商店的錯誤代碼（手冊「十、錯誤代碼」p.32–34）：

| API | 前綴 | 常見 |
|-----|------|------|
| 付款 | `CTI` | `CTI02002` 資料解密失敗、`CTI03001` SHA256 檢查不符、`CTI04002` 商店屬性不符、`CTI05008` 買方跨境條碼不可空白、`CTI05014` 訂單金額不可低於應付金額、`CTI06003` 付款失敗 |
| 查詢 | `CTQ` | `CTQ05006` 交易序號或商店自訂單號擇一填寫、`CTQ06001` 查無符合交易紀錄 |
| 退款 | `CTR` | `CTR07001` 訂單不為已付款狀態、`CTR07002` 退款金額超過可退款金額、`CTR08002` 該時段無法退款、`CTR08003` 在途金額不足 |

---

## 手冊中的不一致之處

照抄手冊會踩到的地方，均已在 `tests/vectors/ezpay-payment.json` 以實際計算確認：

| 位置 | 手冊寫法 | 實際 |
|------|---------|------|
| 電支 附件一 Step5 | 送出欄位寫成 `EncryptData_`、`HashData_` | 各 API 參數表與回應都是 `EncryptData`、`HashData`；錯誤代碼（`SCTE0006 EncryptData 不得為空`）也用無底線名稱。本範例依參數表 |
| 電支 附件三 | 雜湊範例的密文與附件二不同 | 兩者明文不同；附件三的雜湊與它自己的密文一致，公式無誤 |
| 電支 `OrderStatus` 5 | 背景通知（SPayTWQRNotify）的表寫 5=取消付款 | 前景通知、查詢、退款 API 的表都寫 5=全額退款（查詢註明 4、5 皆為全額退款）；以查詢 API 確認 |
| 跨境 八、SHA256 範例 | TradeSha `B5C41ADB…` | 這個值是在 `HashKey=…&` 後**多一個空白**算出來的（PDF 斷行處）；正確公式不含空白 |
| 跨境查詢 七 | QuerySha 只印 63 位 | 前 63 位與正確計算相符 |
| 跨境退款 七 | 範例明文 `Version=1.0`、`RefundAmt=` 空白 | 參數表規定 Version `2.1`、RefundAmt 必填；範例只能當演算法向量 |
| 跨境實體 封面 | 檔名 `1.0.0` | 封面與異動表為文件版本 `ezPay_2.0.0`（2019-11-05，整合所有規格並改用新參數與統一端口） |
| 跨境實體 五、異步通知 | 傳輸表寫「請求方 跨境實體商店、接收方 ezPay」 | 通知是 ezPay 發給商店；方向寫反 |
| 跨境實體 二、(8) | 參考附錄的測試用 QR Code | 手冊沒有附錄 |
| 跨境實體 付款請求 PaymentType | 可帶 `REROUTE`（自動分流） | 回應與通知的 `PaymentType` 只列 `ALIPAY`、`WECHATPAY` |

---

## 與藍新 NewebPay 的差異

同集團，但**不是同一套 API**：

| 項目 | ezPay 電子支付平台 | ezPay 跨境網路 | ezPay 跨境實體 | 藍新 NewebPay MPG |
|------|-------------------|---------------|---------------|-------------------|
| 網域 | `(c)payment.ezpay.com.tw` | `(c)payment.ezpay.com.tw` | `(c)o2o.ezpay.com.tw` | `(c)core.newebpay.com` |
| 路徑 | `/API/Twqr/{APIID}` | `/MPG/mpg_gateway` | `/APIS/Trade`、`/APIS/Query` | `/MPG/mpg_gateway` |
| 外層欄位 | APIID、Version、UID、EncryptData、HashData | MerchantID、Version、TradeInfo、TradeSha | 同電子支付平台 | MerchantID、Version、TradeInfo、TradeSha |
| Version | 1.0 | 1.0（退款 2.1） | 2.0（退款 3.0） | 2.0／2.3 |
| 加密時 padding | 32 bytes | 32 bytes | 手冊只寫 PKCS#7，無範例值 | 規格書範例為 16 bytes（解密須容許 1–32） |
| 回應明文 | urlencoded（`Result[...]`） | JSON | JSON | JSON 或 query string（依 RespondType） |
| 支付工具 | EPACC、ACCLINK、CREDIT、TWQR | ALIPAY、WECHAT | ALIPAY、WECHATPAY（掃消費者條碼） | 信用卡、ATM、超商、各電子錢包… |
| 收款方 | ezPay 會員商店（電子支付機構） | 同左 | 同左（跨境實體商店） | 藍新特約商店 |

需要信用卡收單、ATM、超商代碼等完整金流時用藍新 NewebPay；ezPay 適合要收 ezPay 錢包與 TWQR 的商店。
