# 歐付寶 O'Pay 全方位金流 API 參考

> Source:《歐付寶全方位金流介接技術文件》(O_Pay_011.pdf, 56 頁)
> 文件總覽: https://developers.opay.tw/download/document
> 文件公開程度：public（PDF 免登入直連下載）

## 0. 與 ECPay 綠界的關係——先讀這段

歐付寶（O'Pay，前身 allPay）與綠界（ECPay）系出同源，**API 結構幾乎相同**：

| 面向 | 相同 | 不同 |
|---|---|---|
| 建立訂單路徑 | `/Cashier/AioCheckOut/V5` | 網域 `payment.opay.tw` vs `payment.ecpay.com.tw` |
| 檢查碼 | CheckMacValue、SHA256、排序→前後夾 HashKey/HashIV→URLEncode→轉小寫 | 演算法完全一致 |
| 主要參數 | `MerchantID` `MerchantTradeNo` `MerchantTradeDate` `PaymentType=aio` `TotalAmount` `TradeDesc` `ItemName` `ReturnURL` `ChoosePayment` `EncryptType=1` | 一致 |
| 付款結果通知 | Server POST，回應 `1|OK` | 一致 |
| **付款方式代碼** | Credit / WebATM / ATM / CVS / ALL | **歐付寶獨有：`AccountLink`（銀行快付）、`TopUpUsed`（儲值消費）、`WeiXinpay`（微信支付）、`TWQR`**；ECPay 獨有 BARCODE / BNPL / DigitalPayment 等 |
| 帳務模型 | | **歐付寶有 `HoldTradeAMT` 延遲撥款**（款項先留在歐付寶，需另呼叫撥款 API） |
| 折抵 | | **歐付寶有 `UseRedeem` 購物金／紅包折抵** |

> 💡 遷移提示：既有 ECPay 串接改接歐付寶，主要工作是換網域、換金鑰、調整 `ChoosePayment` 白名單。CheckMacValue 程式碼可原封不動沿用。
>
> ⚠️ 但**測試金鑰是共用的**——歐付寶測試環境 HashKey `5294y06JbISpM5x9` / HashIV `v77hoKGq4kWxNNIS` 與本 skill `taiwan-logistics/data/providers.csv` 中 ECPay 物流的測試金鑰完全相同。別因為看起來眼熟就以為串錯了。

## 1. 環境與測試資訊

| 項目 | 正式 | 測試 |
|---|---|---|
| 建立訂單 | `https://payment.opay.tw/Cashier/AioCheckOut/V5` | `https://payment-stage.opay.tw/Cashier/AioCheckOut/V5` |
| 訂單查詢 | `https://payment.opay.tw/Cashier/QueryTradeInfo/V5` | `https://payment-stage.opay.tw/Cashier/QueryTradeInfo/V5` |
| 定期定額查詢 | `https://payment.opay.tw/Cashier/QueryCreditCardPeriodInfo` | `https://payment-stage.opay.tw/Cashier/QueryCreditCardPeriodInfo` |
| 通知退款 | `https://payment.opay.tw/Cashier/AioChargeback` | `https://payment-stage.opay.tw/Cashier/AioChargeback` |
| 信用卡關帳/退刷/取消/放棄 | `https://payment.opay.tw/CreditDetail/DoAction` | — |
| 請款 | `https://payment.opay.tw/Cashier/Capture` | `https://payment-stage.opay.tw/Cashier/Capture` |
| 信用卡交易查詢 | `https://payment.opay.tw/CreditDetail/QueryTrade/V2` | — |
| 撥款對帳明細 | `https://payment.opay.tw/CreditDetail/FundingReconDetail` | — |
| 廠商後台 | `https://vendor.opay.tw/` | `https://vendor-stage.opay.tw` |

### 測試金鑰

```
HashKey: 5294y06JbISpM5x9   (另一組 bkuAEQufy2bpEng1)
HashIV:  v77hoKGq4kWxNNIS   (另一組 B0lzARI9ZSdhW9jg)
MerchantID: 2000132
```

測試買家帳號（商務會員）：`stageuser002` / 統編 `04792433` / 密碼 `test1234` / 支付密碼 `121212`
個人會員需以測試環境 App 掃碼登入（Android/iOS 下載連結見文件 §測試資訊）。

> 廠商後台提供「模擬付款並通知會員系統」功能，可在不實際扣款下驗證 `ReturnURL` 流程。

## 2. 建立訂單 `AioCheckOut/V5`

Form POST，`application/x-www-form-urlencoded`。

### 必填參數

| 參數 | 型態 | 說明 |
|---|---|---|
| `MerchantID` | String(10) | 會員編號 |
| `MerchantTradeNo` | String(64) | 唯一值，英數大小寫混合。**`ChoosePayment=WeiXinpay` 時僅支援 32 位元**，超過則無法顯示微信付款 QRCode |
| `MerchantTradeDate` | String(20) | `yyyy/MM/dd HH:mm:ss` |
| `PaymentType` | String(20) | 固定 `aio` |
| `TotalAmount` | Int | 整數、僅新台幣、不可為 0 |
| `TradeDesc` | String(200) | 交易描述 |
| `ItemName` | String(200) | 多筆以 `#` 分隔 |
| `ReturnURL` | String(200) | Server 端付款結果通知網址 |
| `ChoosePayment` | String(20) | 見下表 |
| `EncryptType` | Int | 固定 `1`（SHA256） |
| `CheckMacValue` | String | 見 §4 |

### 金額限制

- CVS 超商代碼：**最低 27 元、最高 20000 元**
- 信用卡：非特店會員及第三類個人／商務鑽石（議約）者，**金額不可小於 5 元**

### `ChoosePayment` 付款方式代碼

| 代碼 | 付款方式 | 備註 |
|---|---|---|
| `Credit` | 信用卡 | 手機版不支援 |
| `WebATM` | 網路 ATM | 手機版不支援 |
| `ATM` | 自動櫃員機（虛擬帳號） | |
| `CVS` | 超商代碼 | |
| `AccountLink` | 銀行快付 | **歐付寶獨有** |
| `TopUpUsed` | 儲值消費 | **歐付寶獨有** |
| `WeiXinpay` | 微信支付 | **歐付寶獨有**；繳費期限 2 小時；目前無法提供交易測試的回應 |
| `TWQR` | TWQR 行動支付 | 見 [twqr-ewallet-landscape.md](twqr-ewallet-landscape.md) |
| `ALL` | 不指定，顯示歐付寶付款選擇頁 | |

### 常用選填參數

| 參數 | 型態 | 說明 |
|---|---|---|
| `StoreID` | String(20) | 店家代碼 |
| `ClientBackURL` | String(200) | 「返回商店」按鈕連結。**不會帶付款結果**，僅導頁 |
| `OrderResultURL` | String(200) | Client 端回傳付款結果網址。設了此參數會使 `ClientBackURL` **失效**；ATM/CVS 非即時交易不支援 |
| `PaymentInfoURL` | String(200) | ATM/CVS **取號完成**（非付款完成）時 Server 端回傳繳費資訊 |
| `ClientRedirectURL` | String(200) | 同上但 Client 端導頁；會使 `ClientBackURL` 失效 |
| `NeedExtraPaidInfo` | String(1) | `Y`/`N`，預設 N。設 Y 則回傳額外付款資訊 |
| `IgnorePayment` | String(100) | `ChoosePayment=ALL` 時隱藏特定付款方式，多筆以 `#` 分隔 |
| `DeviceSource` | String(10) | 空值＝預設版型；`APP`＝App 版型 |
| `PlatformID` | String(10) | 平台商代號。**有帶此參數時，檢查碼須用平台商的 HashKey/HashIV 計算** |
| `HoldTradeAMT` | Int | `0`＝不延遲撥款（預設）；`1`＝延遲撥款，需另呼叫「會員申請撥款/退款」API（`Cashier/Capture`，見第 5 節）。**不適用信用卡** |
| `UseRedeem` | String(1) | `Y`/`N`，是否可用購物金/紅包折抵 |
| `Remark` / `ItemURL` | String | 備註 / 商品銷售網址 |
| `ChooseSubPayment` | String(20) | 付款子項目（如 `TAISHIN`） |

### ATM 專屬

| 參數 | 說明 |
|---|---|
| `ExpireDate` | 允許繳費有效天數，1～60 天，預設 3 天 |

### CVS 專屬

| 參數 | 說明 |
|---|---|
| `StoreExpireDate` | **值 >100 以分鐘計，值 ≤100 以天計**。上限 43200 分鐘／30 天，超過一律以 30 天計 |
| `Desc_1` ~ `Desc_4` | String(20)，會顯示在超商繳費平台螢幕上 |

> ⚠️ `StoreExpireDate` 的「大於 100 就變成分鐘」是實務上很容易踩的雷。想設 7 天就填 `7`，填 `7200` 會變成 5 天（7200 分鐘）。

## 3. 付款結果通知

歐付寶以 **Server POST** 將結果送到 `ReturnURL`，格式為 `參數=值&參數=值`。

範例：
```
MerchantID=2000132&MerchantTradeNo=TEST8477&PayAmt=300&PaymentDate=2016/11/02 11:41:12
&PaymentType=Credit_CreditCard&PaymentTypeChargeFee=3&RedeemAmt=0&RtnCode=1&RtnMsg=…
&SimulatePaid=0&TradeAmt=300&TradeDate=2016/11/02 11:40:33&TradeNo=1611021140332409&CheckMacValue=…
```

### 處理規則（必讀）

1. **必須驗證 `CheckMacValue`** 後才處理。
2. **必須判斷 `RtnCode` 是否為 `1`**。非 1 時**請勿出貨**，並取得 `RtnMsg`。
3. 處理完成後**回應純文字 `1|OK`** 給歐付寶。
4. `SimulatePaid=1` 表示此筆是**廠商後台按「模擬付款」發出的**，不是真實付款——測試期間必須靠這個欄位排除假交易。
5. 若使用 `UseRedeem`，訂單金額檢查請以 `TradeAmt`（交易金額）為準，不是 `PayAmt`。

### 主要回傳欄位

`MerchantID`、`MerchantTradeNo`、`TradeNo`（歐付寶交易編號）、`RtnCode`、`RtnMsg`、`TradeAmt`、`PayAmt`、`RedeemAmt`、`PaymentDate`、`PaymentType`、`PaymentTypeChargeFee`、`TradeDate`、`SimulatePaid`、`CheckMacValue`。

`NeedExtraPaidInfo=Y` 時額外回傳項目包含 `WeiXinpayTradeNo`（微信支付交易編號）等。

## 4. CheckMacValue 檢查碼機制

除 `CheckMacValue` 本身外，**所有**傳遞參數都要納入計算。

1. 參數依名稱**由 A 到 Z 升冪排序**，以 `&` 串接（首字母相同則比第二字母，依此類推）
2. 最前面加 `HashKey=…&`，最後面加 `&HashIV=…`
3. 整串做 **URL encode**
4. **轉為小寫**
5. **SHA256** 雜湊
6. 轉大寫即為 `CheckMacValue`

### 官方範例（逐字）

待加密字串（步驟 1、2 後）：
```
HashKey=5294y06JbISpM5x9&ChoosePayment=ALL&EncryptType=1&ItemName=Apple iphone 7 手機殼&MerchantID=2000132&MerchantTradeDate=2013/03/12 15:30:23&MerchantTradeNo=allpay20130312153023&PaymentType=aio&ReturnURL=https://www.allpay.com.tw/receive.php&TotalAmount=1000&TradeDesc=促銷方案&HashIV=v77hoKGq4kWxNNIS
```

步驟 4 後（小寫）：
```
hashkey%3d5294y06jbispm5x9%26choosepayment%3dall%26encrypttype%3d1%26itemname%3dapple+iphone+7+%e6%89%8b%e6%a9%9f%e6%ae%bc%26merchantid%3d2000132%26merchanttradedate%3d2013%2f03%2f12+15%3a30%3a23%26merchanttradeno%3dallpay20130312153023%26paymenttype%3daio%26returnurl%3dhttps%3a%2f%2fwww.allpay.com.tw%2freceive.php%26totalamount%3d1000%26tradedesc%3d%e4%bf%83%e9%8a%b7%e6%96%b9%e6%a1%88%26hashiv%3dv77hokgq4kwxnnis
```

### ⚠️ .NET vs PHP 的 URL encode 差異

官方文件在步驟 (3)(4) 另外列出「若使用 PHP 進行 URL encode」的中間結果（空白為 `%20`），
但那只是中間值：步驟 (5) 要求**依 URLEncode 轉換表換成「.NET 編碼(O'Pay)」**，最終字串的空白是 `+`，
且 `%21 %2a %28 %29`（以及 `%2d %5f %2e`）要還原成 `! * ( ) - _ .`。

**只有 .NET 形式算得出文件的預期值 `96FEF7B0…`**；用 `%20` 計算會得到不同的雜湊。
這與綠界 CheckMacValue 的規則完全相同（兩家同源）。

### Python 實作

> 由 CI 以上方官方範例（`tests/vectors/opay.json`）驗證。

<!-- verify: opay-cmv -->
```python
import hashlib
from urllib.parse import quote_plus


def dotnet_url_encode(text: str) -> str:
    # PHP urlencode 等價（~ 也要編碼）→ 小寫 → 還原 .NET 不編碼的字元
    encoded = quote_plus(text, safe='').replace('~', '%7E').lower()
    for src, dst in (('%2d', '-'), ('%5f', '_'), ('%2e', '.'), ('%21', '!'),
                     ('%2a', '*'), ('%28', '('), ('%29', ')')):
        encoded = encoded.replace(src, dst)
    return encoded


def gen_check_mac_value(params: dict, hash_key: str, hash_iv: str) -> str:
    # 1. 排除 CheckMacValue，依 key 排序（不分大小寫）
    items = sorted(((k, v) for k, v in params.items() if k != 'CheckMacValue'),
                   key=lambda kv: kv[0].lower())
    # 2. 前後夾 HashKey / HashIV
    raw = f"HashKey={hash_key}&{'&'.join(f'{k}={v}' for k, v in items)}&HashIV={hash_iv}"
    # 3–5. .NET 風格 URL encode（含轉小寫）→ 6. SHA256 → 7. 轉大寫
    return hashlib.sha256(dotnet_url_encode(raw).encode('utf-8')).hexdigest().upper()
```

> 與綠界 CheckMacValue 相同，可共用。

## 5. 其他 API

### 訂單查詢 `QueryTradeInfo/V5`

必填：`MerchantID`、`MerchantTradeNo`、`TimeStamp`（Unix timestamp）、`CheckMacValue`。

### 會員通知退款 `AioChargeback`

必填：`MerchantID`、`MerchantTradeNo`、`TradeNo`、`ChargeBackTotalAmount`、`CheckMacValue`。選填 `Remark`（目前請留空白）、`PlatformID`。

**回應為純字串無參數名稱**：第一碼 `1` 成功；`0` 失敗，格式 `0|ErrorMessage`（錯誤代碼－錯誤訊息）。

適用限制：
- `HoldTradeAMT=1`（延遲撥款）的交易**不適用**，請改呼叫「會員申請撥款/退款」API
- 已關帳的信用卡訂單**不適用**，請用「信用卡關帳/退刷/取消/放棄」
- 微信支付已撥款者無法用 API 退款，僅能人工處理（洽客服 02-2655-0115）

### 會員申請撥款／退款 `Cashier/Capture`

延遲撥款（`HoldTradeAMT=1`）的交易付款後，呼叫此 API 讓歐付寶撥款到會員帳戶，並可同時退款給買方（《全方位金流介接技術文件》第 13 章，p.41–42）。
非延遲撥款的交易改用 `AioChargeback`；**信用卡交易不適用**。

- 正式：`https://payment.opay.tw/Cashier/Capture`
- 測試：`https://payment-stage.opay.tw/Cashier/Capture`
- Server POST，CheckMacValue 同第 4 節

| 參數 | 型態 | 必填 | 說明 |
|------|------|:---:|------|
| `MerchantID` | String(10) | ● | 會員編號 |
| `MerchantTradeNo` | String(64) | ● | 建立訂單時的會員交易編號 |
| `CheckMacValue` | String | ● | |
| `CaptureAMT` | Int | ● | 申請撥款金額 |
| `UserRefundAMT` | Int | ● | 退款給買方的金額，不退款帶 `0`；範圍 0～訂單金額。**`CaptureAMT + UserRefundAMT` 須等於訂單金額** |
| `PlatformID` | String(10) | | 專案合作平台商代號；一般會員帶空值 |
| `UpdatePlatformChargeFee` | String(1) | | `Y` 更改訂單的平台商手續費，預設 `N`；僅平台商使用 |
| `PlatformChargeFee` | Int | | `UpdatePlatformChargeFee=Y` 時帶，範圍 0～原手續費 |
| `Remark` | String(30) | | 備註 |

實際撥款金額 = 訂單金額 − `UserRefundAMT` − 必要手續費。

回應以 `參數=值&…` 直接回傳：`MerchantID`、`MerchantTradeNo`、`TradeNo`（String(20)）、`RtnCode`（`1` 成功，其餘失敗）、`RtnMsg`、`AllocationDate`（預計撥款日 `yyyy-MM-dd`）。

### 其他端點

| 功能 | 路徑 |
|---|---|
| 信用卡關帳/退刷/取消/放棄 | `/CreditDetail/DoAction` |
| 請款 | `/Cashier/Capture` |
| 信用卡交易查詢 | `/CreditDetail/QueryTrade/V2` |
| 撥款對帳明細 | `/CreditDetail/FundingReconDetail` |
| 取號 | `/PaymentMedia/TradeNoAio`（vendor 網域） |
| 定期定額查詢 | `/Cashier/QueryCreditCardPeriodInfo` |

### 快速測試表單

歐付寶提供免登入的測試建單頁：
- `https://developers.opay.tw/AioAll/CreateOrder`（不指定付款方式）
- `https://developers.opay.tw/AioCreditCard/CreateOrder`（信用卡）
- `https://developers.opay.tw/AioCreditCard/PeriodCreateOrder`（定期定額）
- `https://developers.opay.tw/AioCvs/CreateOrder`（超商代碼）
- `https://developers.opay.tw/AioAtm/CreateOrder`（ATM）
- `https://developers.opay.tw/AioWebAtm/CreateOrder`（網路 ATM）

## 6. 版本相容性

`AioCheckOut/V5` 為現行版本（V5 新增微信支付）。歐付寶所有版本規格**向下相容**，已串 V4 且不需微信支付者可繼續用 V4。

## 7. APP 第三方應用（交易）`AppCashier/CreateTrade`

> Source:《歐付寶行動支付 APP 第三方應用(交易)介接技術文件》V1.0.8（O_Pay_appapi01.pdf，2019/05/09，35 頁）

廠商後端建單取得 `TradeToken`，再以 URL Scheme 或 SDK 喚起歐付寶 APP 原生付款頁（p.4、p.10）。付款類型：歐付寶帳戶、信用卡、銀行快付（p.7）。

- 需 `APPID` 與交易模組 HashKey／HashIV：白金以上會員於廠商後台「系統開發管理」查詢（p.5）
- 「廠商 Web 嵌入於行動支付 APP」須先填《第三方應用服務申請書》交業務申請（p.7）
- SDK 需洽業務提供（p.10）

### 建立交易（p.11–13）

- 測試：`https://payment-stage.opay.tw/AppCashier/CreateTrade/`
- 正式：`https://payment.opay.tw/AppCashier/CreateTrade/`

外層 POST 參數：

| 參數 | 型態 | 必填 | 說明 |
|---|---|:---:|---|
| `PlatformID` | String(10) | | 平台商才帶 |
| `MerchantID` | String(10) | ● | |
| `APPID` | String(10) | | 廠商服務編號 |
| `Version` | Int | ● | 帶 `4` |
| `Encryption` | Int | ● | `1` AES、`2` TripleDES |
| `Format` | Int | ● | `1` XML、`2` JSON |
| `HashType` | Int | ● | CheckMacValue 雜湊：`0` MD5、`1` SHA256（預設 1） |
| `Data` | | ● | 加密後的 XML／JSON，見下方「加解密與檢查碼」 |

`Data` 內容：

| 參數 | 型態 | 必填 | 說明 |
|---|---|:---:|---|
| `PlatformID` | String(10) | | |
| `MerchantID` | String(10) | ● | |
| `APPID` | String(10) | | |
| `MerchantTradeNo` | String(64) | ● | 同一廠商不可重複，英數字 |
| `StoreID` | String(20) | ● | 店號 |
| `PayerSID` | String(10) | | 指定付款人身分證號；與付款會員不符則建單失敗 |
| `ChoosePayment` | String(30) | ● | `Credit`、`TopUpUsed`、`AccountLink`、`ALL`；多個以 `#` 分隔，如 `Credit#TopUpUsed` |
| `MerchantTradeDate` | String(20) | ● | `yyyy/MM/dd HH:mm:ss` |
| `TotalAmount` | Int | ● | |
| `TradeDesc` | String(200) | ● | |
| `ItemName` | String(200) | ● | 多品項以 `#` 分隔 |
| `ReturnURL` | String(200) | ● | 付款完成通知網址，須回應 `1\|OK` |
| `Description` | String(200) | | 顯示於付款完成頁的交易提醒，依附錄 XML／JSON 格式傳入 |
| `CustomField1`～`3` | String(50) | | 顯示於廠商後台報表 |
| `CheckMacValue` | String | ● | |
| `TradeType` | | | 預設 `mobile`；票券特約廠商帶 `ticket` |
| `StoreName` | String(20) | | 票券特約廠商用 |

文件以黃底標示「送出前需各自 UrlEncode 一次」的參數值；PDF 文字層無法辨識是哪幾個，範例中的中文欄位（`CustomerName`、`CustomerAddr` 等）為已編碼的值（p.23）。

回傳：外層 `PlatformID`、`MerchantID`、`Encryption`、`Format`、`RtnCode`（`1` 成功）、`RtnMsg`、`Data`；`Data` 內含 `RtnCode`、`RtnMsg`、`PlatformID`、`MerchantID`、`APPID`、`MerchantTradeNo`、`StoreID`、`CheckMacValue`，`RtnCode=1` 時另有 `TradeToken`（String(20)）與 `ExpiredTime`（Token 有效時間）。

### 喚起付款（p.17–22）

URL Scheme：`opay://checkout?MerchantID=${MerchantID}&TradeToken=${TradeToken}&Version=${Version}`，另帶 `redirectURL`；Web 嵌入模式加 `inAppWebView`，App 呼叫 App 模式加 `native`。

付款後無論成功與否都導回 `redirectURL`，以 query string 帶回：`rtnCode`（`1` 付款完成、`99999999` 取消付款、其他失敗）、`rtnMsg`、`TradeToken`、`Data`（內含 `RtnCode`、`RtnMsg`、`MerchantID`、`APPID`、`MerchantTradeNo`、`StoreID`、`CheckMacValue`）。

| SDK | 用法 |
|---|---|
| JS（Web 嵌入） | 載入 `https://payment-stage.opay.tw/Scripts/ThirdParty/omobipay-thirdparty.min.js`（正式為 `payment.opay.tw` 同路徑），`OMobiPay.checkoutWithTradeToken({TradeToken, redirectURL})` |
| iOS | CocoaPods `pod 'OPaySDK'`；`LSApplicationQueriesSchemes` 加 `opay`；自訂 URL Scheme `ap${MerchantID}` |
| Android | `new OMobiPay(MID, APPID).checkoutWithTradeToken(TradeToken, redirectURL)` |
| PHP | `Omobipay_Thirdparty.php`，洽業務取得 |

⚠️ 文件的 PHP SDK 範例 `Version` 帶 `'2'`、JS SDK 初始化 `version : '2'`，與 API 參數表「主版號帶 4」不一致（p.11、p.15、p.19）。

### 付款結果通知（p.14–15）

Server POST 到 `ReturnURL`：`MerchantID`、`MerchantTradeNo`、`StoreID`、`RtnCode`、`RtnMsg`、`TradeNo`（String(20)）、`TradeAmt`、`PaymentDate`、`PaymentType`（見下表）、`PaymentTypeChargeFee`（通路費）、`TradeDate`、`SimulatePaid`（固定 `0`）、`CheckMacValue`。成功回應 `1|OK`；失敗回 `0|錯誤代碼－錯誤訊息`。

### 加解密與檢查碼（p.23–33）

- **CheckMacValue**：參數依名稱 A→Z 排序 → 前加 `HashKey=`、後加 `&HashIV=` → 整串 URL Encode（空白為 `+`）→ 轉小寫 → 依 `HashType` 做 MD5 或 SHA256，大寫輸出。以 p.23–24 的範例驗證：Python `hashlib.sha256(quote_plus(s, safe='').lower().encode())` 重現 SHA256 `ED781A2D…D860A5AB`，MD5 重現 `D5E4A5D4…C073A70736`。範例不含 `( ) ! * - _` 等字元，是否要依第 4 節的 .NET 規則還原，文件未說明。
- CheckMacValue 放進 `Data`（XML 的 `<CheckMacValue>` 或 JSON 欄位）後整段加密，結果再 UrlEncode：
  - AES-128-CBC／PKCS7：Key = HashKey、IV = HashIV
  - TripleDES-CBC／PKCS7：Key = HashKey（16 bytes），IV = **HashIV 前 8 碼**（p.28）
- ⚠️ 文件的 AES、TripleDES 範例密文都經過兩次加密：以範例金鑰解一次得到的是另一段 AES 密文，再解一次才是 XML（TripleDES 範例解一次也得到同一段 AES 密文）。不能直接當單層加密的測試向量。
- 附錄 4「授權資料格式」（`AuthData`：`AccountID`、`MID`、`Name`、`Cellphone`、`IDCardNumber`、`Email`）以 AES 加密（p.33），文件未說明用於哪支 API。

回覆付款方式 `PaymentType`（p.34）：`WebATM_TAISHIN`、`WebATM_MEGA`、`WebATM_SHINKONG`、`WebATM_FIRST`、`ATM_ESUN`、`ATM_FIRST`、`ATM_CHINATRUST`、`ATM_TAISHIN`、`CVS_CVS`、`CVS_OK`、`CVS_FAMILY`、`CVS_HILIFE`、`CVS_IBON`、`AccountLink_TAISHIN`、`Credit_CreditCard`、`TopUpUsed_AllPay`。

### 交易訊息代碼（appapi01 p.35、appapi02 p.27）

| 代碼 | 說明 |
|---|---|
| `1` | 交易成功 |
| `10100001` | IP 拒絕存取 |
| `10100002` | 交易發生錯誤 |
| `10100010` | 超過扣款金額上限 |
| `10100012` | 付款帳戶金額不足 |
| `10100020` | 信用卡授權失敗 |
| `10100022` | 使用非指定的發卡銀行信用卡 |
| `10100050` | 參數錯誤 |
| `10100051` | XML 參數錯誤 |
| `10100052` | 廠商編號錯誤 |
| `10100053` | 廠商狀態錯誤 |
| `10100054` | 廠商交易序號重複 |
| `10100055` | 新增交易失敗 |
| `10100056` | 歐付寶交易序號有誤 |
| `10100060` | 廠商編號空白 |
| `10100063` | 廠商交易序號空白 |
| `10100064` | 交易日期格式錯誤 |
| `10100065` | 交易金額格式錯誤 |
| `99999901` | In App WebView 才可使用此模式（僅 appapi01） |
| `99999910` | 缺少必要參數（僅 appapi01） |
| `99999999` | 使用者取消付款（僅 appapi01） |

---

## 8. 掃碼付（動態 QRCode）`QRCodeCashier`

> Source:《歐付寶掃碼付(動態 QRCode)介接技術文件》V1.6.3（O_Pay_appapi02.pdf，2024-08-06，29 頁）

廠商機台或網頁顯示 QRCode，消費者用歐付寶 APP 掃碼付款；付款類型為歐付寶帳戶、信用卡、銀行快付（p.5）。可由廠商 Server 串接，或由機台直接呼叫（p.8–13）。

- QRCode 預設 10 分鐘有效，可用 `TradeEffectiveTime` 設 90～600 秒；逾時需重新建單並換新 `MerchantTradeNo`（p.9、p.15）
- 顯示 QRCode 後，可在有效期內每 5 秒輪詢一次查詢 API（p.10）
- 測試：`MerchantID` `2000132`，HashKey／HashIV 同全方位金流測試金鑰；測試版 APP 登入：手機 `0920123456`、身分證後 4 碼 `3123`、安全密碼 `121212`（p.6）

### 建立訂單（p.14–16）

- 測試：`https://corpintra-stage.opay.tw/QRCodeCashier/CreateTrade`
- 正式：`https://corpintra.opay.tw/QRCodeCashier/CreateTrade`
- `Content-Type: application/json`，POST。V1.6.3 起網域由 `corp.opay.tw` 改為 `corpintra.opay.tw`

外層：`PlatformID`●、`MerchantID`●、`Version`●（帶 `3`）、`Encryption`●（`1` AES、`2` TripleDES）、`Format`●（`1` XML、`2` JSON）、`Data`●。

`Data` 內容：

| 參數 | 型態 | 必填 | 說明 |
|---|---|:---:|---|
| `PlatformID` | String(10) | ● | |
| `MerchantID` | String(10) | ● | |
| `StoreID` | String(20) | | 廠商商店代碼 |
| `MerchantTradeNo` | String(20) | ● | 不可重複；重新取 QRCode 須換新編號 |
| `MerchantTradeTime` | String(19) | ● | `yyyy/MM/dd HH:mm:ss` |
| `TradeAmount` | int | ● | |
| `TradeDesc` | String(200) | ● | |
| `ItemName` | String(200) | ● | 多品項以 `#` 分隔 |
| `ReturnURL` | String(200) | | 付款完成通知，格式同全方位金流「付款結果通知」（第 3 節） |
| `CustomFieldJSON` | String(500) | | `[{"FieldName":"車牌號碼","FieldValue":"048-8D"}]` |
| `UseRedeem` | String(1) | | 購物金折抵，目前不提供 |
| `TradeEffectiveTime` | int | | 90～600 秒，預設 600 |
| `CheckMacValue` | String | ● | |

回傳 `Data`：`RtnCode`（`1` 成功）、`RtnMsg`、`PlatformID`、`MerchantID`、`StoreID`、`MerchantTradeNo`、`CustomFieldJSON`、`CheckMacValue`；`RtnCode=1` 時另有：

| 參數 | 說明 |
|---|---|
| `AllPayTradeNo` | 歐付寶交易序號 String(20) |
| `TradeAmount` | 交易金額 |
| `AllPayTinyUrl` | QRCode 內容，自行產生 QRCode 顯示 |
| `AllPayQRCodeImg` | QRCode 圖片網址，暫不提供 |
| `ExpireTime` | QRCode 有效時間 |
| `CarrierNo`／`MembershipCardNo` | 功能尚未開啟 |

文件以黃底標示送出前需各自 UrlEncode、接收後需各自 UrlDecode 的參數值（p.15–16）。

### 交易查詢（p.17–19）

- 測試：`https://corpintra-stage.opay.tw/QRCodeCashier/QueryTrade`
- 正式：`https://corpintra.opay.tw/QRCodeCashier/QueryTrade`

外層同建立訂單，`Version` 帶 `2`；`Data`：`PlatformID`●、`MerchantID`●、`AllPayTradeNo`●、`CheckMacValue`●。

回傳 `Data`：`RtnCode`（`1` 查詢成功；文件建議以加密後的交易狀態判斷）、`RtnMsg`、`PlatformID`、`MerchantID`、`StoreID`、`AllPayTradeNo`、`CheckMacValue`；`RtnCode=1` 時另有：

| 參數 | 說明 |
|---|---|
| `MerchantTradeNo` | |
| `AllpayTradeTime` | 付款時間 |
| `TradeAmount` | 交易金額 |
| `PayAmount` | 實付金額 = `TradeAmount` − `RedeemAmount` |
| `RedeemAmount` | 紅利折抵金額 |
| `PaymentType` | `1` 歐付寶帳戶、`3` 信用卡、`4` 銀行快付 |
| `TradeStatus` | `1` 付款成功、`0` 訂單建立成功（尚未付款） |
| `RefundTime`／`RefundAmount` | 退款時間／金額 |
| `CustomFieldJSON` | |
| `ExpireTime` | QRCode 有效時間 |
| `CarrierNo`／`MembershipCardNo`／`FeedbackAmount` | 尚未開啟或不提供 |

### 取消／退款（p.20）

沒有 API。全方位金流的退款 API 與信用卡 API 都不支援掃碼付訂單：

- 歐付寶帳戶付款：廠商後台「一般訂單查詢 → 全方位金流訂單」退款
- 信用卡：廠商後台「信用卡收單 → 交易明細查詢」放棄請款

### JS SDK（p.21）

`ScanCodePay.js`：`directOpenApp(qrCodeTinyUrl, environment)` 以 `AllPayTinyUrl` 開啟 APP 付款頁（測試環境 `environment` 帶 `stage`）；`directDownloadApp()` 導向 APP 下載頁。文件只給相對路徑 `ScanCodePay.js?t=202202071711`，未提供完整網址。

### 檢查碼與加密（p.22–26）

- **CheckMacValue**：只納入 `Data` 內實際傳送的參數（未傳的選填欄位不計），排序 → 前後夾 HashKey／HashIV → URL Encode → 轉小寫 → SHA256 → 大寫。以 p.22 範例驗證：`quote_plus(s, safe='').lower()` 後 SHA256 重現 `B00807D8…C511A58E`。範例 `TradeDesc` 為 `POS行動支付`（無空白；PDF 排版顯示的空白若照打會得到不同值）。
- AES-128-CBC／PKCS7：Key = HashKey、IV = HashIV；TripleDES-CBC：Key = HashKey（16 bytes）、IV = HashIV 前 8 碼（文件寫 PKCS5）。p.23–24 的 JSON 範例密文皆可用測試金鑰解回原 JSON。加密結果再 UrlEncode。

交易訊息代碼同第 7 節（不含 `999999xx`）。

---

## 9. 直播主收款網址 付款結果通知

> Source:《歐付寶直播主收款網址 API 技術文件》V1.0.0（O_Pay_broadcaster.pdf，2025/09/25，14 頁）

沒有建單 API：廠商在歐付寶官網「收款工具 → 實況主收款」設定收款資料與付款完成通知網址，消費者付款後歐付寶以 Server POST 通知（p.4–5）。

測試資訊（p.6）：

| | 一般商家 | 平台商 |
|---|---|---|
| `MerchantID` | `2000132` | `2012441` |
| 廠商後台帳號／密碼 | `StageTest` / `test1234` | `stagetest2` / `test1234` |
| HashKey | `5294y06JbISpM5x9` | `bkuAEQufy2bpEng1` |
| HashIV | `v77hoKGq4kWxNNIS` | `B0lzARI9ZSdhW9jg` |

測試卡 `4311-9522-2222-2222`、安全碼 `222`；廠商後台 `https://vendor-stage.opay.tw` 可模擬付款。防火牆請綁定 `postgate.opay.tw`，不要綁 IP。

### 通知格式（p.8–10）

JSON：

| 參數 | 型態 | 說明 |
|---|---|---|
| `MerchantID` | String(10) | |
| `RpHeader.Timestamp` | Number | Unix timestamp |
| `TransCode` | Int | `1` 表示傳輸成功；交易結果看 `Data.RtnCode` |
| `TransMsg` | String(200) | |
| `Data` | String | 加密 JSON |
| `CheckMacValue` | String | |

`Data` 解密後：

| 參數 | 型態 | 說明 |
|---|---|---|
| `RtnCode` | Int | `1` 成功，其餘失敗；非 `1` 勿出貨 |
| `RtnMsg` | String(200) | |
| `MerchantID` | String(10) | |
| `DonateURL` | String(200) | 直播主收款網址 |
| `SimulatePaid` | Int | 模擬付款時才回傳；`1` 為後台模擬，不會撥款，勿出貨 |
| `OrderInfo.MerchantTradeNo` | String(20) | |
| `OrderInfo.TradeNo` | String(20) | 歐付寶交易編號 |
| `OrderInfo.TradeAmt` | Int | |
| `OrderInfo.TradeDate` | String(20) | `yyyy/MM/dd HH:mm:ss` |
| `OrderInfo.PaymentType` | String(20) | 見下方 |
| `OrderInfo.PaymentDate` | String(20) | ATM／超商以銀行或超商銷帳時間為準 |
| `OrderInfo.ChargeFee` | Number | 手續費 |
| `OrderInfo.TradeStatus` | String(8) | `0` 成立未付款、`1` 已付款 |
| `PatronName` | String(100) | 贊助者名稱 |
| `PatronNote` | String(100) | 贊助者留言 |
| `LivestreamURL` | String(200) | 直播頻道網址，未設定時為空字串 |

回應 `1|OK`；未正確回應時隔 5～15 分鐘重送，當天共四次（p.10）。

`PaymentType`（p.14）：`WebATM_TAISHIN`、`WebATM_MEGA`、`ATM_TAISHIN`、`CVS_CVS`、`CVS_OK`、`CVS_FAMILY`、`CVS_HILIFE`、`CVS_IBON`、`Tenpay_Tenpay`、`Credit_CreditCard`、`TopUpUsed_AllPay`。

### 解密與檢查碼（p.11–13）

- `Data`：明文先 URL Encode 再以 AES-128-CBC／PKCS7 加密、Base64 輸出；解密後需再 URL Decode。文件範例（Key `ejCk326UnaZWKisg`、IV `q9jcZX8Ib9LM8wYk`）與電子發票 API 相同，已由 `taiwan-invoice/examples/opay-invoice-example.py` 的自測涵蓋。文件未說明通知使用哪組 Key／IV。
- CheckMacValue：附錄 1 沿用第 4 節的全方位金流算法（SHA256、.NET URL encode 還原），但範例是 `AioCheckOut` 表單參數；JSON 通知要以哪些欄位計算，文件未說明。

---

## 10. 其他歐付寶文件

| 文件 | 連結 |
|---|---|
| 全方位金流 API（本文件來源） | https://www.opay.tw/Content/files/O_Pay_011.pdf |
| All-In-One API (EN) | https://www.opay.tw/Content/files/O_Pay_043.pdf |
| 信用卡退款與取消授權 | https://www.opay.tw/Content/files/O_Pay_012.pdf |
| 信用卡快速參考 | https://developers.opay.tw/Content/Doc/O_Pay_011_Credit01.pdf |
| 超商代碼 / ATM / WebATM / 儲值消費 | `O_Pay_011_CVS.pdf` / `_ATM.pdf` / `_WEBATM.pdf` / `_TopUpUsed.pdf` |
| POS 行動支付 API | https://www.opay.tw/Content/files/O_Pay_posapi02.pdf |
| 行動支付 APP 第三方應用（交易）V1.0.8 | https://developers.opay.tw/Content/Doc/O_Pay_appapi01.pdf（第 7 節） |
| 掃碼付（動態 QRCode）V1.6.3 | https://developers.opay.tw/Content/Doc/O_Pay_appapi02.pdf（第 8 節） |
| 直播主收款網址 V1.0.0 | https://developers.opay.tw/Content/Doc/O_Pay_broadcaster.pdf（第 9 節） |
| 微信公眾號支付 API | `O_Pay_wechatapi01.pdf` |
| 會員 Open ID API | https://www.opay.tw/Content/files/O_Pay_041.pdf |
| 電子發票 B2C / B2B / 離線 | 見 [../../taiwan-invoice/references/OPAY_API_REFERENCE.md](../../taiwan-invoice/references/OPAY_API_REFERENCE.md) |

## 11. 備註與待驗證

- POS、微信公眾號文件標註「若要串接使用請洽歐付寶客服」，可能需額外開通
- 歐付寶沒有公開物流 API：官方文件總覽（2026-09-21 修訂版，2026-09-24 查核）只列金流、電子發票、Open ID、平台綁定、直播主收款網址
