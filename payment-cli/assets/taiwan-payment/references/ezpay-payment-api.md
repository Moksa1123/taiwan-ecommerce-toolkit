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

> ⚠️ **舊版本的本文件是錯的。** 它把 ezPay 寫成「與藍新 NewebPay MPG 完全相同」，網址用藍新舊網域
> `ccore.spgateway.com`、Version 2.0、付款方式列信用卡/ATM/超商…。ezPay 官方手冊實際上是：
> 境內走全新的**電子支付平台 API**（`/API/Twqr/*`、APIID + UID + EncryptData + HashData），
> 只有**跨境（支付寶/微信）**才是 MPG 形式，且網域是 `payment.ezpay.com.tw`、Version 1.0。

---

## 目錄

1. [ezPay 是什麼](#ezpay-是什麼)
2. [加解密（兩組 API 共用）](#加解密兩組-api-共用)
3. [電子支付平台 API（境內）](#電子支付平台-api境內)
4. [跨境網路交易 API](#跨境網路交易-api)
5. [錯誤代碼](#錯誤代碼)
6. [手冊中的不一致之處](#手冊中的不一致之處)
7. [與藍新 NewebPay 的差異](#與藍新-newebpay-的差異)

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

---

## 與藍新 NewebPay 的差異

同集團，但**不是同一套 API**：

| 項目 | ezPay 電子支付平台 | ezPay 跨境 | 藍新 NewebPay MPG |
|------|-------------------|-----------|-------------------|
| 網域 | `(c)payment.ezpay.com.tw` | `(c)payment.ezpay.com.tw` | `(c)core.newebpay.com` |
| 路徑 | `/API/Twqr/{APIID}` | `/MPG/mpg_gateway` | `/MPG/mpg_gateway` |
| 外層欄位 | APIID、Version、UID、EncryptData、HashData | MerchantID、Version、TradeInfo、TradeSha | MerchantID、Version、TradeInfo、TradeSha |
| Version | 1.0 | 1.0（退款 2.1） | 2.0／2.3 |
| 加密時 padding | 32 bytes | 32 bytes | 規格書範例為 16 bytes（解密須容許 1–32） |
| 回應明文 | urlencoded（`Result[...]`） | JSON | JSON 或 query string（依 RespondType） |
| 支付工具 | EPACC、ACCLINK、CREDIT、TWQR | ALIPAY、WECHAT | 信用卡、ATM、超商、各電子錢包… |
| 收款方 | ezPay 會員商店（電子支付機構） | 同左 | 藍新特約商店 |

需要信用卡收單、ATM、超商代碼等完整金流時用藍新 NewebPay；ezPay 適合要收 ezPay 錢包與 TWQR 的商店。
