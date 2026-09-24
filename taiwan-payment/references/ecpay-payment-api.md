# ECPay Payment API Reference

綠界全方位金流（AIO）API 參考。依 developers.ecpay.com.tw《全方位金流API技術文件》整理，`/數字` 為官方頁面編號（`https://developers.ecpay.com.tw/數字.md`）。

---

## 目錄

1. [API 端點總覽](#api-端點總覽)
2. [測試環境](#測試環境)
3. [產生訂單參數](#產生訂單參數)
4. [ChoosePayment 付款方式](#choosepayment-付款方式)
5. [信用卡付款](#信用卡付款)
6. [ATM 虛擬帳號](#atm-虛擬帳號)
7. [超商代碼](#超商代碼)
8. [超商條碼](#超商條碼)
9. [TWQR、微信支付、電子支付](#twqr微信支付電子支付)
10. [BNPL 無卡分期](#bnpl-無卡分期)
11. [Apple Pay](#apple-pay)
12. [付款結果通知](#付款結果通知)
13. [訂單查詢](#訂單查詢)
14. [信用卡請退款](#信用卡請退款)
15. [定期定額](#定期定額)
16. [CheckMacValue 計算](#checkmacvalue-計算)
17. [錯誤碼](#錯誤碼)
18. [銀行代碼對照表](#銀行代碼對照表)
19. [常見問題排解](#常見問題排解)

---

## API 端點總覽

| 功能 | 測試環境 | 正式環境 | 官方頁 |
|------|----------|----------|--------|
| 產生訂單 | `https://payment-stage.ecpay.com.tw/Cashier/AioCheckOut/V5` | `https://payment.ecpay.com.tw/Cashier/AioCheckOut/V5` | /2862 |
| 查詢訂單 | `https://payment-stage.ecpay.com.tw/Cashier/QueryTradeInfo/V5` | `https://payment.ecpay.com.tw/Cashier/QueryTradeInfo/V5` | /2890 |
| 查詢 ATM/CVS/BARCODE 取號結果 | `https://payment-stage.ecpay.com.tw/Cashier/QueryPaymentInfo` | `https://payment.ecpay.com.tw/Cashier/QueryPaymentInfo` | /5615 |
| 信用卡定期定額訂單查詢 | `https://payment-stage.ecpay.com.tw/Cashier/QueryCreditCardPeriodInfo` | `https://payment.ecpay.com.tw/Cashier/QueryCreditCardPeriodInfo` | /2892 |
| 信用卡定期定額訂單作業 | `https://payment-stage.ecpay.com.tw/Cashier/CreditCardPeriodAction` | `https://payment.ecpay.com.tw/Cashier/CreditCardPeriodAction` | /2900 |
| 信用卡請退款 | **無**（測試環境無實際授權） | `https://payment.ecpay.com.tw/CreditDetail/DoAction` | /2885 |
| 查詢信用卡單筆明細 | **無** | `https://payment.ecpay.com.tw/CreditDetail/QueryTrade/V2` | /2894 |
| 下載特店對帳媒體檔 | `https://vendor-stage.ecpay.com.tw/PaymentMedia/TradeNoAio` | `https://vendor.ecpay.com.tw/PaymentMedia/TradeNoAio` | /2896 |
| 下載信用卡撥款對帳檔 | **無** | `https://payment.ecpay.com.tw/CreditDetail/FundingReconDetail` | /2898 |

產生訂單須由前端頁面 Submit（Form POST）到綠界；其他 API 為 Server POST，`Content-Type: application/x-www-form-urlencoded`。
僅支援 TLS 1.2；API 呼叫過快（不含產生訂單）會收到 HTTP 403，需降速並等 30 分鐘（/2858）。

---

## 測試環境

來源：/2856。

| 用途 | MerchantID | HashKey | HashIV | 後台帳號／密碼 |
|------|-----------|---------|--------|---------------|
| 一般特店（模擬 3D、中租無卡分期） | `3002607` | `pwFHCqoQZGmho4w6` | `EkRm7iFT261dpevs` | `stagetest3`／`test1234` |
| 平台商（PlatformID） | `3002599` | `spPjZn66i0OhqJsQ` | `hT5OJckN45isQTTs` | `stagetest2`／`test1234` |
| 閘道商（美國運通、國旅卡） | `3365120` | `oyQPlLVKop9xuwxw` | `rljcW843laE9esfI` | `stageae001`／`qwer123` |

測試後台：`https://vendor-stage.ecpay.com.tw/`，可查詢訂單與「模擬付款」（一般訂單查詢 → 全方位金流訂單）。

| 測試卡 | 卡號 |
|--------|------|
| 一般信用卡 | `4311-9511-1111-1111`、`4311-9522-2222-2222` |
| 海外信用卡 | `4000-2011-1111-1111` |
| 美國運通（限閘道商） | 國內 `3403-532780-80900`、國外 `3712-222222-22222` |
| 永豐 30 期 | `4938-1777-7777-7777` |
| 金融卡 | `4831-3888-8888-8888` |
| 銀聯卡 | `6213-1111-1111-1`、`6216-1111-1111-1111`、`6219-1111-1111-1111-111` 等 |

- 安全碼任意三碼；有效月年須晚於當月
- 3D 驗證簡訊碼固定 `1234`

---

## 產生訂單參數

`POST /Cashier/AioCheckOut/V5`（/2862）。

### 必填

| 參數 | 型別 | 說明 |
|------|------|------|
| `MerchantID` | String(10) | 特店編號 |
| `MerchantTradeNo` | String(20) | 特店訂單編號，唯一值，英數字 |
| `MerchantTradeDate` | String(20) | `yyyy/MM/dd HH:mm:ss` |
| `PaymentType` | String(20) | 固定 `aio` |
| `TotalAmount` | Int | 整數，新台幣 |
| `TradeDesc` | String(200) | 交易描述，勿帶特殊字元 |
| `ItemName` | String(400) | 商品名稱，多筆以 `#` 分隔；超過 400 字元會被截斷而導致檢查碼錯誤 |
| `ReturnURL` | String(200) | 付款結果 Server 端通知網址 |
| `ChoosePayment` | String(20) | 見下節 |
| `CheckMacValue` | String | 檢查碼 |
| `EncryptType` | Int | 固定 `1`（SHA256） |

### 選填

| 參數 | 型別 | 說明 |
|------|------|------|
| `StoreID` | String(10) | 特店旗下店鋪代號 |
| `ClientBackURL` | String(200) | 付款頁「返回特店」按鈕網址 |
| `Remark` | String(100) | 備註 |
| `ChooseSubPayment` | String(20) | 付款子項目，設定後無法選其他子項目 |
| `OrderResultURL` | String(200) | 付款完成後 Client 端導回並 POST 結果的網址 |
| `NeedExtraPaidInfo` | String(1) | `Y` 回傳額外付款資訊（/5675） |
| `IgnorePayment` | String(100) | `ChoosePayment=ALL` 時隱藏的付款方式，多筆以 `#` 分隔 |
| `PlatformID` | String(10) | 特約合作平台商代號，一般特店放空值 |
| `CustomField1`～`4` | String(50) | 自訂欄位，原值回傳 |
| `Language` | String(3) | `CHT`（預設）、`ENG`、`KOR`、`JPN`、`CHI` |

**ReturnURL 注意（/2858）**：只支援 80／443 port，勿指定 port；不支援中文網址（改用 punycode）。

---

## ChoosePayment 付款方式

來源：/2862、/5679。

| 值 | 說明 | 金額限制（官方有寫的） |
|----|------|------------------------|
| `Credit` | 信用卡及銀聯卡（銀聯需申請）；閘道商可刷美國運通、國旅卡 | |
| `TWQR` | 歐付寶 TWQR 行動支付（需申請） | 6～49,999（/36991） |
| `WebATM` | 網路 ATM；**手機版不支援** | |
| `ATM` | ATM 虛擬帳號 | |
| `CVS` | 超商代碼 | |
| `BARCODE` | 超商條碼 | |
| `ApplePay` | Apple Pay | |
| `BNPL` | 無卡分期：裕富 `URICH`、中租 `ZINGALA`（需申請） | 裕富 1,000～500,000；中租 50～500,000（/36659） |
| `WeiXin` | 微信支付 | 6～500,000（/56448） |
| `DigitalPayment` | 電子支付：`ChooseSubPayment` 可指定 `Jkopay`（街口）、`iPASS`（一卡通 iPASS MONEY） | |
| `ALL` | 由綠界顯示付款選擇頁 | |

- ATM、CVS、BARCODE 的金額上下限依特店申請的費率方案，官方 API 文件未列固定值；超出時回 `5100070`（/5740）
- 測試環境 1 元訂單只開 ATM 會回 `5100070`，改用 2 元（/5740）
- 綠界 PAY APP 付款：`DeviceSource=gwpay`，支援 Credit、ATM、CVS、BARCODE、BNPL（/53379）
- 要不經綠界畫面取得 ATM／CVS／BARCODE 繳費代碼，改用「非信用卡幕後取號 API」

---

## 信用卡付款

### 一次付清（/2866）

| 參數 | 型別 | 說明 |
|------|------|------|
| `Redeem` | String(1) | `Y` 使用紅利折抵 |
| `UnionPay` | Int | `0` 消費者可選銀聯、`1` 只用銀聯（直接導向銀聯網站）、`2` 不可用銀聯 |
| `BindingCard` | Int | 記憶卡號：`1` 使用、`0` 不使用 |
| `MerchantMemberID` | String(30) | 記憶卡號識別碼（特店代號 + 會員編號） |

### 分期付款（/2870）

| 參數 | 型別 | 說明 |
|------|------|------|
| `CreditInstallment` | String(20) | 一般分期 `3,6,12,18,24`；永豐 30 期 `30N`（須達最低金額，後台可查）；閘道商另支援 `5,8,9,10` |

- 期數須先申請開通
- 不可與定期定額、紅利折抵一起設定
- 帶訂單總金額即可，除不盡的金額由第一期收取

消費者自費分期：消費金額 1,000 元以上可用（/41284）。

### 額外付款資訊（`NeedExtraPaidInfo=Y`，/5675）

| 參數 | 說明 |
|------|------|
| `gwsr` | 授權交易單號 |
| `process_date` | 處理時間 |
| `auth_code` | 授權碼 |
| `amount` | 金額 |
| `stage` | 分期期數 |
| `stast` | 頭期金額（永豐 30 期為第一階段各期金額） |
| `staed` | 各期金額（永豐 30 期為第二階段各期金額） |
| `eci` | 3D 驗證值；`5`、`6`、`2`、`1` 代表 3D 交易 |
| `card4no`／`card6no` | 卡號末 4／前 6 碼；銀聯卡不回傳，Apple Pay 回傳裝置綁定號碼 |
| `red_dan`／`red_de_amt`／`red_ok_amt`／`red_yet` | 紅利扣點、折抵金額、實際扣款金額、剩餘點數 |
| `ATMAccBank`／`ATMAccNo` | ATM 付款人銀行代碼、帳號 |
| `WebATMAccBank`／`WebATMAccNo`／`WebATMBankName` | WebATM 付款人資訊 |
| `PaymentNo`／`PayFrom` | 超商繳費代碼、繳費超商（`family`／`hilife`／`okmart`／`ibon`） |
| `TWQRTradeNo` | 行動支付交易編號 |

---

## ATM 虛擬帳號

`ChoosePayment=ATM`（/2872）。

| 參數 | 型別 | 說明 |
|------|------|------|
| `ExpireDate` | Int | 繳費有效天數 1～60，預設 3；到期日當天 23:59 截止 |
| `PaymentInfoURL` | String(200) | 取號完成後 Server 端回傳繳費資訊 |
| `ClientRedirectURL` | String(200) | 取號完成後 Client 端回傳；設定後 `ClientBackURL` 失效 |
| `ChooseSubPayment` | String(20) | 指定銀行，見下表 |

**可用銀行（/5679）**：`BOT` 台灣銀行、`CHINATRUST` 中國信託、`FIRST` 第一銀行、`LAND` 土地銀行、`CATHAY` 國泰世華、`PANHSIN` 板信銀行、`KGI` 凱基銀行（即將開放）。
`TAISHIN`、`ESUN`、`FUBON`、`TACHONG` 暫不提供。板信銀行每月例行維護期間建立訂單會失敗（/2872）。

**取號結果（/2881）**：`RtnCode=2` 為 ATM 取號成功，其餘失敗。回傳 `BankCode`、`vAccount`、`ExpireDate` 等。

---

## 超商代碼

`ChoosePayment=CVS`（/2874）。

| 參數 | 型別 | 說明 |
|------|------|------|
| `StoreExpireDate` | Int | 繳費截止時間（**分鐘**），預設 10080，上限 43200（30 天） |
| `PaymentInfoURL` | String(200) | 取號完成後 Server 端回傳 |
| `ClientRedirectURL` | String(200) | 取號完成後 Client 端回傳 |
| `Desc_1`～`Desc_4` | String(20) | 交易描述；繳費超商為全家或 7-11 時顯示在超商繳費平台螢幕 |
| `ChooseSubPayment` | String(20) | `CVS` 不指定、`OK`、`FAMILY`、`HILIFE`、`IBON` |

**取號結果（/2881）**：`RtnCode=10100073` 為取號成功，其餘失敗。回傳 `PaymentNo`、`ExpireDate`。

---

## 超商條碼

`ChoosePayment=BARCODE`（/2876）。

| 參數 | 型別 | 說明 |
|------|------|------|
| `StoreExpireDate` | Int | 繳費期限（**天**），預設 7，1～30 |
| `PaymentInfoURL`／`ClientRedirectURL`／`Desc_1`～`4` | | 同超商代碼 |

取號成功同為 `RtnCode=10100073`，回傳 `Barcode1`～`3` 三段號碼（不含條碼圖，須自行轉成 Code39）。

---

## TWQR、微信支付、電子支付

- **TWQR**（/36991）：需透過綠界向歐付寶申請開通；6～49,999 元。消費者用 APP 付款後會以原生瀏覽器返回，可能遺失登入狀態。交易在歐付寶廠商後台或歐付寶 APP 查帳、退款。
- **微信支付**（/56448）：6～500,000 元。
- **電子支付**：`ChoosePayment=DigitalPayment`，`ChooseSubPayment` 可指定 `Jkopay` 或 `iPASS`（/5679）。

---

## BNPL 無卡分期

`ChoosePayment=BNPL`（/36659）。

| 參數 | 說明 |
|------|------|
| `ChooseSubPayment` | `URICH` 裕富、`ZINGALA` 中租 |
| `PaymentInfoURL` | 訂單建立（非付款完成）後 Server 端通知；官方要求務必設定以接收無卡分期訂單狀態 |
| `OrderResultURL` | Client 端付款結果 |

- 金額：裕富 1,000～500,000；中租 50～500,000
- 付款結果只透過 `ReturnURL` 通知（/2890）；申請結果通知見 /37517
- 未指定 `ChooseSubPayment` 時，付款畫面依後台「無卡分期切換設定」顯示

---

## Apple Pay

`ChoosePayment=ApplePay`（/7328）。

- iOS 16 以上任何瀏覽器可用；iOS 16 以下與 macOS 僅 Safari
- 非 Safari 時付款頁不顯示 Apple Pay（/2862）
- 回傳的卡號前六後四為裝置綁定號碼
- 測試環境模擬付款不向銀行授權

---

## 付款結果通知

綠界以 Server POST 送到 `ReturnURL`（/2878）。

| 參數 | 型別 | 說明 |
|------|------|------|
| `MerchantID` | String(10) | |
| `MerchantTradeNo` | String(20) | |
| `StoreID` | String(20) | |
| `RtnCode` | Int | `1` 付款成功 |
| `RtnMsg` | String(200) | |
| `TradeNo` | String(20) | 綠界交易編號 |
| `TradeAmt` | Int | |
| `PaymentDate` | String(20) | |
| `PaymentType` | String(50) | 見下表 |
| `PaymentTypeChargeFee` | Number | 手續費 |
| `TradeDate` | String(20) | |
| `PlatformID` | String(10) | |
| `SimulatePaid` | Int | `1` 為後台模擬付款，**不可出貨** |
| `CustomField1`～`4` | String(50) | |
| `CheckMacValue` | String | 必須驗證 |

**回應**：收到後回純文字 `1|OK`。未正確回應時，綠界隔 5～15 分鐘重送，當天共重送 4 次。常見錯誤回應：`"1|OK"`（含引號）、`1|ok`、`_OK`、`1OK`、空白。`1|OK` 只代表已收到，不改變付款狀態。

### PaymentType 回傳值（/5686）

| 回傳值 | 說明 |
|--------|------|
| `Credit_CreditCard` | 信用卡 |
| `Flexible_Installment` | 永豐 30 期 |
| `ATM_BOT`、`ATM_CHINATRUST`、`ATM_FIRST`、`ATM_LAND`、`ATM_CATHAY`、`ATM_PANHSIN`、`ATM_KGI` | ATM |
| `WebATM_BOT`、`WebATM_CHINATRUST`、`WebATM_FIRST`、`WebATM_LAND` | WebATM |
| `CVS_CVS`、`CVS_OK`、`CVS_FAMILY`、`CVS_HILIFE`、`CVS_IBON` | 超商代碼 |
| `BARCODE_BARCODE` | 超商條碼 |
| `TWQR_OPAY` | 歐付寶 TWQR |
| `WeiXin_OPAY` | 微信支付 |
| `BNPL_URICH`、`BNPL_ZINGALA` | 無卡分期 |
| `DigitalPayment_Jkopay`、`DigitalPayment_IPASS` | 電子支付 |

### 防火牆（/2858）

綠界主機 IP 不固定，以 FQDN 放行：
- 特店連到綠界：`payment.ecpay.com.tw`、`payment-stage.ecpay.com.tw`（TCP 443）；需固定 IP 須線上申請「主機 IP 鎖定」
- 綠界連入特店：`postgate.ecpay.com.tw`、`postgate-stage.ecpay.com.tw`（TCP 443）

---

## 訂單查詢

`POST /Cashier/QueryTradeInfo/V5`（/2890）。收到付款通知後應以此 API 再確認。

| 參數 | 型別 | 說明 |
|------|------|------|
| `MerchantID` | String(10) | |
| `MerchantTradeNo` | String(20) | |
| `TimeStamp` | Int | Unix 時間，**3 分鐘**內有效 |
| `CheckMacValue` | String | |
| `PlatformID` | String(10) | |

回應：`MerchantID`、`MerchantTradeNo`、`StoreID`、`TradeNo`、`TradeAmt`、`PaymentDate`、`PaymentType`、`HandlingCharge`、`PaymentTypeChargeFee`、`TradeDate`、`TradeStatus`、`ItemName`、`CustomField1`～`4`、`CheckMacValue`。

| TradeStatus | 說明 |
|-------------|------|
| `0` | 訂單成立未付款 |
| `1` | 訂單成立已付款 |
| `10200095` | 訂單未成立，消費者未完成付款，交易失敗 |

---

## 信用卡請退款

`POST /CreditDetail/DoAction`，**僅正式環境**（/2885）。先用 `QueryTrade/V2` 取得交易狀態再決定動作。

| 參數 | 型別 | 說明 |
|------|------|------|
| `MerchantID` | String(10) | |
| `MerchantTradeNo` | String(20) | |
| `TradeNo` | String(20) | 綠界交易編號 |
| `Action` | String(1) | 見下表 |
| `TotalAmount` | Int | 金額 |
| `CheckMacValue` | String | |
| `PlatformID` | String(10) | |

| Action | 說明 |
|--------|------|
| `C` | 關帳：依關帳後金額向銀行請／退款 |
| `R` | 退刷：關帳後修改訂單金額（部分或全額退款） |
| `E` | 取消：取消關帳，訂單回到前一狀態 |
| `N` | 放棄：關帳前放棄交易，以全額退款 |

注意事項（/2885）：
- 開啟「每日自動關帳」時，20:15～20:30 勿呼叫
- 關閉自動關帳後，訂單須在 21 天內關帳，逾期無法以 API 處理
- 退刷上限為訂單金額；**分期與紅利折抵交易只能全額退刷**
- 綠界帳戶餘額低於退刷金額時無法退刷
- 銀聯卡授權完成即自動關帳，「要關帳」狀態不可取消關帳
- 系統自動關帳的訂單，取消請在授權隔日 06:00 後操作
- 不支援停用定期定額，改用 `CreditCardPeriodAction`

---

## 定期定額

### 建立參數（`ChoosePayment=Credit`，/2868）

| 參數 | 型別 | 說明 |
|------|------|------|
| `PeriodAmount` | Int | 每次授權金額 |
| `PeriodType` | String(1) | `D` 天、`M` 月、`Y` 年 |
| `Frequency` | Int | `D`：1～365；`M`：1～12；`Y`：只能 1 |
| `ExecTimes` | Int | 至少 2 次；`D`、`M` 最多 999，`Y` 最多 99 |
| `PeriodReturnURL` | String(200) | 每次授權結果通知網址（格式同 /5631），請用網域名稱勿用 IP |
| `BindingCard`／`MerchantMemberID` | | 記憶卡號 |

### 查詢 `QueryCreditCardPeriodInfo`（/2892）

回應含 `PeriodType`、`Frequency`、`ExecTimes`、`PeriodAmount`、`TotalSuccessTimes`、`TotalSuccessAmount`、`ExecLog`，以及：

| ExecStatus | 說明 |
|------------|------|
| `0` | 已終止 |
| `1` | 執行中 |
| `2` | 執行完成 |

### 作業 `CreditCardPeriodAction`（/2900）

欄位：`MerchantID`、`MerchantTradeNo`、`Action`、`TimeStamp`、`CheckMacValue`、`PlatformID`。

| Action | 說明 |
|--------|------|
| `ReAuth` | 最新一筆授權失敗時補授權（測試環境無法測試） |
| `Cancel` | 終止後續授權 |

---

## CheckMacValue 計算

官方步驟（/2902）：參數依名稱排序 → 前加 `HashKey=`、後加 `HashIV=` → URL Encode → 轉小寫 → SHA256 → 轉大寫。
實作細節（與綠界官方 SDK 逐位元組比對，見 repo `tests/vectors/ecpay.json`）：

- 排序**不分大小寫**（官方 SDK 用 `strcasecmp`）
- URL Encode 依 PHP `urlencode`（空白為 `+`），再把 .NET 不編碼的 `- _ . ! * ( )` 還原（轉換表 /2904）
- `CheckMacValue` 本身不參與計算

```python
import hashlib
import urllib.parse


def ecpay_url_encode(text):
    encoded = urllib.parse.quote_plus(text, safe='').replace('~', '%7E').lower()
    for src, dst in (('%2d', '-'), ('%5f', '_'), ('%2e', '.'), ('%21', '!'),
                     ('%2a', '*'), ('%28', '('), ('%29', ')')):
        encoded = encoded.replace(src, dst)
    return encoded


def generate_check_mac_value(params, hash_key, hash_iv):
    items = sorted(((k, v) for k, v in params.items() if k != 'CheckMacValue'),
                   key=lambda kv: kv[0].lower())
    raw = f"HashKey={hash_key}&{'&'.join(f'{k}={v}' for k, v in items)}&HashIV={hash_iv}"
    return hashlib.sha256(ecpay_url_encode(raw).encode('utf-8')).hexdigest().upper()
```

物流 API 同一套規則，但雜湊為 **MD5**。

---

## 錯誤碼

官方附錄「交易狀態代碼表」（/5740）說明：錯誤代碼持續新增，完整清單在廠商後台「系統設定 → 交易狀態代碼查詢」。以下只列官方文件寫明的代碼。

| 代碼 | 說明 | 出處 |
|------|------|------|
| `1` | 付款成功 | /2878 |
| `2` | ATM 取號成功 | /2881 |
| `10100073` | CVS／BARCODE 取號成功 | /2881 |
| `10200095` | 訂單未成立，消費者未完成付款（`TradeStatus`） | /2890 |
| `10100058` | Pay fail：3D 驗證未完成，常見於瀏覽器版本、VPN、IP 不符銀行規範；定期定額時手機號碼與銀行資料不一致也會失敗 | /5740 |
| `10800001` | 觸發綠界風控（連續刷卡、可疑電話等） | /5740 |
| `10100248` | 信用卡被銀行拒絕，請消費者洽發卡行 | /5740 |
| `10200141` | 商店未開啟收款服務（測試／正式環境金鑰混用，或未完成申請） | /5740 |
| `10200146` | 商店不支援信用卡分期 | /5740 |
| `10300023` | 本次交易未提供任何付款方式（MerchantID 錯誤或服務未開通） | /5740 |
| `10300024` | 資料驗證錯誤（簡訊驗證時返回上一頁再送出） | /5740 |
| `5100070` | 金額超出上下限或無可用付款方式 | /5740 |
| `5100071` | 無權限使用（服務未開通） | /5740 |

---

## 銀行代碼對照表

官方附錄「銀行代碼表」（/44089）：

| 代碼 | 銀行 |
|------|------|
| `004` | 台灣銀行 |
| `005` | 土地銀行 |
| `007` | 第一銀行 |
| `013` | 國泰世華銀行 |
| `118` | 板信銀行 |
| `822` | 中國信託 |
| `808` | 玉山銀行（暫不提供） |
| `813` | 台北富邦銀行（暫不提供） |
| `814` | 大眾銀行（暫不提供） |

各銀行虛擬帳號的檢核能力見 /59297；臺灣銀行、土地銀行、第一銀行、國泰世華無法完全阻擋錯誤繳費。

---

## 常見問題排解

### CheckMacValue 錯誤

1. HashKey／HashIV 是否與環境一致（測試與正式不同）
2. 排序是否不分大小寫
3. URL Encode 是否依 PHP `urlencode` 並還原 `- _ . ! * ( )`（`encodeURIComponent` 會把空白編成 `%20`）
4. 參數是否超過長度被截斷（如 `ItemName` 400 字元）

### 付款通知未收到

1. `ReturnURL` 是否對外開放、未指定 port、非中文網址
2. 防火牆是否放行 `postgate.ecpay.com.tw`
3. 是否正確回應 `1|OK`
4. 測試環境可用後台「模擬付款」觸發通知（`SimulatePaid=1`，不可出貨）

### 綠界 CDN 攔截

`ItemName`、`TradeDesc` 含系統指令類關鍵字會被綠界 CDN 阻擋（/2858）。

---

## 官方資源

- 開發者文件：https://developers.ecpay.com.tw/
- 測試後台：https://vendor-stage.ecpay.com.tw/
- 正式後台：https://vendor.ecpay.com.tw/
