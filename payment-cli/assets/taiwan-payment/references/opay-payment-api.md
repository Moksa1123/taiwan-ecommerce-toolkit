# 歐付寶 O'Pay 全方位金流 API 參考

> Source:《歐付寶全方位金流介接技術文件》(O_Pay_011.pdf, 56 頁)
> 文件總覽: https://developers.opay.tw/download/document
> Captured: 2026-08-08 · doc_access: **public**（PDF 免登入直連下載）

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
| `HoldTradeAMT` | Int | `0`＝不延遲撥款（預設）；`1`＝延遲撥款，需另呼叫「會員申請撥款/退款」API。**不適用信用卡** |
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

官方文件同時列出兩種編碼結果，**空白字元處理不同**：

| 語言 | 空白編碼為 |
|---|---|
| .NET（`HttpUtility.UrlEncode`） | `+` |
| PHP（`urlencode` / `rawurlencode`） | `%20` |

文件對兩者都給了合法範例，代表**兩種都可被接受**，但**同一支程式必須前後一致**。CheckMacValue 對不上時，這是第一個要查的地方。文件附錄另有完整 URLEncode 轉換表。

### Python 實作

```python
import hashlib
from urllib.parse import quote_plus

def gen_check_mac_value(params: dict, hash_key: str, hash_iv: str) -> str:
    # 1. 排除 CheckMacValue，依 key 升冪排序
    items = sorted((k, v) for k, v in params.items() if k != 'CheckMacValue')
    raw = '&'.join(f'{k}={v}' for k, v in items)
    # 2. 前後夾 HashKey / HashIV
    raw = f'HashKey={hash_key}&{raw}&HashIV={hash_iv}'
    # 3. URL encode（quote_plus → 空白為 '+'，即 .NET 風格）
    # 4. 轉小寫
    encoded = quote_plus(raw).lower()
    # 5. SHA256 → 6. 轉大寫
    return hashlib.sha256(encoded.encode('utf-8')).hexdigest().upper()
```

> 與本 skill `taiwan-payment/CLAUDE.md` 的 ECPay 實作**完全相同**，可共用。

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

## 7. 其他歐付寶文件

| 文件 | 連結 |
|---|---|
| 全方位金流 API（本文件來源） | https://www.opay.tw/Content/files/O_Pay_011.pdf |
| All-In-One API (EN) | https://www.opay.tw/Content/files/O_Pay_043.pdf |
| 信用卡退款與取消授權 | https://www.opay.tw/Content/files/O_Pay_012.pdf |
| 信用卡快速參考 | https://developers.opay.tw/Content/Doc/O_Pay_011_Credit01.pdf |
| 超商代碼 / ATM / WebATM / 儲值消費 | `O_Pay_011_CVS.pdf` / `_ATM.pdf` / `_WEBATM.pdf` / `_TopUpUsed.pdf` |
| POS 行動支付 API | https://www.opay.tw/Content/files/O_Pay_posapi02.pdf |
| 行動支付第三方應用 / 掃碼付動態 QRCode | `O_Pay_appapi01.pdf` / `O_Pay_appapi02.pdf` |
| 微信公眾號支付 API | `O_Pay_wechatapi01.pdf` |
| 會員 Open ID API | https://www.opay.tw/Content/files/O_Pay_041.pdf |
| 電子發票 B2C / B2B / 離線 | 見 [../../taiwan-invoice/references/OPAY_API_REFERENCE.md](../../taiwan-invoice/references/OPAY_API_REFERENCE.md) |

## 8. 待驗證

- POS、微信公眾號文件標註「若要串接使用請洽歐付寶客服」，可能需額外開通
- 歐付寶物流 API 未出現在官方文件總覽頁；社群教學顯示存在，端點與參數待確認
- 「會員申請撥款/退款」API（延遲撥款情境）的完整參數本次未擷取
