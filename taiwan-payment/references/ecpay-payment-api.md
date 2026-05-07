# ECPay Payment API Reference

綠界科技金流 API 完整參考文件。

---

## 目錄

1. [API 端點總覽](#api-端點總覽)
2. [測試環境](#測試環境)
3. [通用參數](#通用參數)
4. [信用卡付款](#信用卡付款)
5. [ATM 虛擬帳號](#atm-虛擬帳號)
6. [超商代碼](#超商代碼)
7. [超商條碼](#超商條碼)
8. [TWQR 行動支付](#twqr-行動支付)
9. [BNPL 無卡分期](#bnpl-無卡分期)
10. [Apple Pay](#apple-pay)
11. [付款結果通知](#付款結果通知)
12. [訂單查詢](#訂單查詢)
13. [信用卡請退款](#信用卡請退款)
14. [定期定額](#定期定額)
15. [CheckMacValue 計算](#checkmacvalue-計算)
16. [錯誤碼大全](#錯誤碼大全)
17. [銀行代碼對照表](#銀行代碼對照表)
18. [常見問題排解](#常見問題排解)

---

## API 端點總覽

### 訂單相關

| 功能 | 測試環境 | 正式環境 |
|------|----------|----------|
| **訂單建立** | `https://payment-stage.ecpay.com.tw/Cashier/AioCheckOut/V5` | `https://payment.ecpay.com.tw/Cashier/AioCheckOut/V5` |
| **訂單查詢** | `https://payment-stage.ecpay.com.tw/Cashier/QueryTradeInfo/V5` | `https://payment.ecpay.com.tw/Cashier/QueryTradeInfo/V5` |
| **付款資訊查詢** | `https://payment-stage.ecpay.com.tw/Cashier/QueryPaymentInfo` | `https://payment.ecpay.com.tw/Cashier/QueryPaymentInfo` |

### 信用卡相關

| 功能 | 測試環境 | 正式環境 |
|------|----------|----------|
| **請退款** | `https://payment-stage.ecpay.com.tw/CreditDetail/DoAction` | `https://payment.ecpay.com.tw/CreditDetail/DoAction` |
| **信用卡查詢** | `https://payment-stage.ecpay.com.tw/CreditDetail/QueryTrade/V2` | `https://payment.ecpay.com.tw/CreditDetail/QueryTrade/V2` |
| **定期定額查詢** | `https://payment-stage.ecpay.com.tw/Cashier/QueryCreditCardPeriodInfo` | `https://payment.ecpay.com.tw/Cashier/QueryCreditCardPeriodInfo` |
| **定期定額操作** | `https://payment-stage.ecpay.com.tw/CreditDetail/CreditCardPeriodAction` | `https://payment.ecpay.com.tw/CreditDetail/CreditCardPeriodAction` |

### 對帳相關

| 功能 | 測試環境 | 正式環境 |
|------|----------|----------|
| **對帳媒體檔** | `https://payment-stage.ecpay.com.tw/CreditDetail/FundingReconDetail` | `https://payment.ecpay.com.tw/CreditDetail/FundingReconDetail` |
| **信用卡對帳** | `https://payment-stage.ecpay.com.tw/CreditDetail/TradeNoAio` | `https://payment.ecpay.com.tw/CreditDetail/TradeNoAio` |

---

## 測試環境

### 測試帳號

```
商店代號 (MerchantID):  3002607
HashKey:               pwFHCqoQZGmho4w6
HashIV:                EkRm7iFT261dpevs
```

### 測試信用卡

| 卡號 | 說明 | 備註 |
|------|------|------|
| `4311-9522-2222-2222` | 一般測試卡 | 無 3D 驗證 |
| `4000-2211-1111-1111` | 3D 驗證測試卡 | 需輸入驗證碼 |

- **有效期限**: 任意未過期日期 (如 `12/30`)
- **CVV/CVC**: 任意 3 碼 (如 `222`)
- **3D 驗證密碼**: `12345` (僅 3D 卡)

### 測試環境限制

- 每日交易筆數限制: 100 筆
- 單筆交易金額上限: 49,999 元
- 不會實際扣款

---

## 通用參數

### 基本必填參數

所有付款方式都需要以下參數：

| 參數 | 類型 | 長度 | 必填 | 說明 |
|------|------|------|------|------|
| `MerchantID` | String | 10 | ● | 商店代號 |
| `MerchantTradeNo` | String | 20 | ● | 訂單編號，需唯一，僅英數字 |
| `MerchantTradeDate` | String | 20 | ● | 交易時間 `yyyy/MM/dd HH:mm:ss` |
| `PaymentType` | String | 20 | ● | 固定值 `aio` |
| `TotalAmount` | Integer | - | ● | 金額，整數，無小數點 |
| `TradeDesc` | String | 200 | ● | 交易描述，需 URL Encode |
| `ItemName` | String | 400 | ● | 商品名稱，多項用 `#` 分隔 |
| `ReturnURL` | String | 200 | ● | 付款結果背景通知網址 |
| `ChoosePayment` | String | 20 | ● | 付款方式代碼 |
| `CheckMacValue` | String | - | ● | SHA256 檢查碼 |
| `EncryptType` | Integer | - | ● | 固定值 `1` (SHA256) |

### 通用選填參數

| 參數 | 類型 | 長度 | 說明 |
|------|------|------|------|
| `StoreID` | String | 20 | 分店代號 |
| `ClientBackURL` | String | 200 | 前台返回商店網址 |
| `ItemURL` | String | 200 | 商品銷售網址 |
| `Remark` | String | 100 | 交易備註 |
| `OrderResultURL` | String | 200 | 前台付款結果通知網址 |
| `NeedExtraPaidInfo` | String | 1 | 是否回傳額外資訊 `Y`/`N` |
| `Language` | String | 3 | 語系 `ENG`/`KOR`/`JPN`/`CHI` |
| `CustomField1` | String | 50 | 自訂欄位 1 (原值回傳) |
| `CustomField2` | String | 50 | 自訂欄位 2 (原值回傳) |
| `CustomField3` | String | 50 | 自訂欄位 3 (原值回傳) |
| `CustomField4` | String | 50 | 自訂欄位 4 (原值回傳) |
| `PlatformID` | String | 10 | 特約合作平台商代號 |
| `InvoiceMark` | String | 1 | 是否開立發票 `Y`/`N` |

### ChoosePayment 付款方式代碼

| 代碼 | 說明 | 金額限制 |
|------|------|----------|
| `Credit` | 信用卡 | 無限制 |
| `WebATM` | 網路 ATM | 1 ~ 5,000,000 |
| `ATM` | ATM 虛擬帳號 | 1 ~ 5,000,000 |
| `CVS` | 超商代碼 | 27 ~ 20,000 |
| `BARCODE` | 超商條碼 | 1 ~ 20,000 |
| `ApplePay` | Apple Pay | 需申請 |
| `TWQR` | 台灣Pay QR Code | 6 ~ 49,999 |
| `BNPL` | 無卡分期 | 依方案 |
| `ALL` | 全部 | 顯示所有可用方式 |

---

## 信用卡付款

### ChoosePayment 設定

```
ChoosePayment=Credit
```

### 一次付清參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `Redeem` | String(1) | 否 | 紅利折抵 `Y`/`N` |
| `UnionPay` | Integer | 否 | `0`:可選銀聯 `1`:僅銀聯 `2`:不使用銀聯 |
| `BindingCard` | Integer | 否 | 記憶卡號 `0`:否 `1`:是 |
| `MerchantMemberID` | String(30) | 否 | 記憶卡號會員 ID (需與 BindingCard=1 配合) |

### 分期付款參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `CreditInstallment` | String(20) | ● | 分期期數，如 `3,6,12,18,24` |
| `InstallmentAmount` | Integer | 否 | 每期金額 (系統自動計算) |

**支援期數**: 3, 6, 12, 18, 24 期 (部分銀行支援 5, 8, 9, 10, 30N)

**注意事項**:
- 銀聯卡不支援分期付款
- 分期金額需符合銀行規定 (通常 1,000 元以上)
- 分期、一次付清、定期定額不可同時設定

### 信用卡通知額外參數

當 `NeedExtraPaidInfo=Y` 時，付款通知會額外包含：

| 參數 | 說明 |
|------|------|
| `card4no` | 卡號末四碼 |
| `card6no` | 卡號前六碼 (BIN 碼) |
| `eci` | 3D 驗證結果代碼 |
| `auth_code` | 銀行授權碼 |
| `gwsr` | 閘道授權碼 |
| `process_date` | 處理時間 |
| `amount` | 授權金額 |
| `stage` | 分期期數 (分期時) |
| `stast` | 首期金額 (分期時) |
| `staession` | 各期金額 (分期時) |

### ECI 碼說明

| ECI | 說明 |
|-----|------|
| `5` | 3D 驗證成功 (Visa) |
| `6` | 3D 驗證成功 (MasterCard/JCB) |
| `2` | 3D 驗證失敗，但仍可交易 (Visa) |
| `1` | 3D 驗證失敗，但仍可交易 (MasterCard/JCB) |
| `7` | 非 3D 交易 (Visa) |
| `0` | 非 3D 交易 (MasterCard/JCB) |

---

## ATM 虛擬帳號

### ChoosePayment 設定

```
ChoosePayment=ATM
```

### ATM 專用參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `ExpireDate` | Integer | 否 | 繳費期限 (天)，`1`~`60`，預設 `3` |
| `PaymentInfoURL` | String(200) | 否 | 取號結果背景通知網址 |
| `ClientRedirectURL` | String(200) | 否 | 取號結果前台導向網址 |
| `ChooseSubPayment` | String(20) | 否 | 指定銀行 |

### ChooseSubPayment 銀行代碼

| 代碼 | 銀行 | 備註 |
|------|------|------|
| `FIRST` | 第一銀行 | 可取得付款人帳號 |
| `CATHAY` | 國泰世華 | 可取得付款人帳號 |
| `PANHSIN` | 板信銀行 | 可取得付款人帳號 |
| `KGI` | 凱基銀行 | 可取得付款人帳號 |
| `ESUN` | 玉山銀行 | - |
| `TAISHIN` | 台新銀行 | - |
| `CHINATRUST` | 中國信託 | - |
| `BOT` | 臺灣銀行 | - |
| `LAND` | 土地銀行 | - |

### ATM 取號結果通知參數

ECPay 會 POST 到 `PaymentInfoURL`:

| 參數 | 說明 |
|------|------|
| `MerchantID` | 商店代號 |
| `MerchantTradeNo` | 訂單編號 |
| `StoreID` | 分店代號 |
| `RtnCode` | `1`:取號成功 `2`:取號失敗 |
| `RtnMsg` | 訊息 |
| `TradeNo` | ECPay 交易編號 |
| `TradeAmt` | 交易金額 |
| `PaymentType` | `ATM_銀行代碼` |
| `TradeDate` | 訂單成立時間 |
| `ExpireDate` | 繳費期限 `yyyy/MM/dd` |
| `BankCode` | 銀行代碼 |
| `vAccount` | 虛擬帳號 (14~16 碼) |
| `CheckMacValue` | 檢查碼 |

---

## 超商代碼

### ChoosePayment 設定

```
ChoosePayment=CVS
```

### CVS 專用參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `StoreExpireDate` | Integer | 否 | 繳費期限 (分鐘)，預設 `10080` (7天)，最大 `43200` (30天) |
| `PaymentInfoURL` | String(200) | 否 | 取號結果背景通知網址 |
| `ClientRedirectURL` | String(200) | 否 | 取號結果前台導向網址 |
| `Desc_1` | String(20) | 否 | 繳費單描述 1 |
| `Desc_2` | String(20) | 否 | 繳費單描述 2 |
| `Desc_3` | String(20) | 否 | 繳費單描述 3 |
| `Desc_4` | String(20) | 否 | 繳費單描述 4 |
| `ChooseSubPayment` | String(20) | 否 | 指定超商 |

### ChooseSubPayment 超商代碼

| 代碼 | 超商 |
|------|------|
| `CVS` | 不指定 (顯示所有) |
| `FAMILY` | 全家 |
| `HILIFE` | 萊爾富 |
| `IBON` | 7-11 (ibon) |
| `OK` | OK 便利商店 |

### CVS 金額限制

- 最低: 27 元
- 最高: 20,000 元
- 7-11 單筆上限: 20,000 元
- 全家/萊爾富/OK 單筆上限: 20,000 元

### CVS 取號結果通知參數

| 參數 | 說明 |
|------|------|
| `MerchantID` | 商店代號 |
| `MerchantTradeNo` | 訂單編號 |
| `RtnCode` | `10100073`:取號成功 |
| `PaymentNo` | 繳費代碼 (14 碼) |
| `ExpireDate` | 繳費期限 `yyyy/MM/dd HH:mm:ss` |
| `CheckMacValue` | 檢查碼 |

---

## 超商條碼

### ChoosePayment 設定

```
ChoosePayment=BARCODE
```

### BARCODE 專用參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `StoreExpireDate` | Integer | 否 | 繳費期限 (天)，預設 `7`，最大 `30` |
| `PaymentInfoURL` | String(200) | 否 | 取號結果背景通知網址 |
| `ClientRedirectURL` | String(200) | 否 | 取號結果前台導向網址 |
| `Desc_1` | String(20) | 否 | 繳費單描述 1 |
| `Desc_2` | String(20) | 否 | 繳費單描述 2 |
| `Desc_3` | String(20) | 否 | 繳費單描述 3 |
| `Desc_4` | String(20) | 否 | 繳費單描述 4 |

### BARCODE 金額限制

- 最低: 1 元
- 最高: 20,000 元

### BARCODE 取號結果通知參數

| 參數 | 說明 |
|------|------|
| `Barcode1` | 條碼 1 (7 碼) |
| `Barcode2` | 條碼 2 (13 碼) |
| `Barcode3` | 條碼 3 (16 碼) |
| `ExpireDate` | 繳費期限 |

---

## TWQR 行動支付

### ChoosePayment 設定

```
ChoosePayment=TWQR
```

### TWQR 限制

| 項目 | 說明 |
|------|------|
| 金額下限 | 6 元 |
| 金額上限 | 49,999 元 |
| 支援支付 | 台灣 Pay、歐付寶、各銀行 App |

### TWQR 注意事項

1. 需向 ECPay 申請開通 O-Pay (歐付寶) 功能
2. 透過 App 付款後，會開啟原生瀏覽器，可能導致登入狀態遺失
3. 建議使用 `OrderResultURL` 作為付款結果頁面

---

## BNPL 無卡分期

### ChoosePayment 設定

```
ChoosePayment=BNPL
```

### BNPL 方案

| 方案 | 金額限制 | 審核時間 |
|------|----------|----------|
| 裕富無卡分期 | 1,000 ~ 300,000 元 | 1-3 工作天 |
| 中租銀角零卡 | 50 ~ 300,000 元 | 即時 ~ 1 工作天 |

### BNPL 專用參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `PaymentInfoURL` | String(200) | ● | 訂單建立通知 (需審核) |
| `ClientRedirectURL` | String(200) | 否 | 裕富方案前台導向 |
| `OrderResultURL` | String(200) | 否 | 中租方案前台導向 |

### BNPL 注意事項

1. 交易需經過審核，通知時間較長
2. 裕富方案退款需聯繫裕富處理
3. 中租方案可在 ECPay 後台操作退款

---

## Apple Pay

### ChoosePayment 設定

```
ChoosePayment=ApplePay
```

### Apple Pay 前置作業

1. 向 ECPay 申請開通 Apple Pay
2. 設定 Domain Verification
3. 上傳 Apple 驗證檔案

### Apple Pay 限制

- 僅支援 Safari 瀏覽器
- 僅支援 iOS/macOS 裝置
- 需要 HTTPS

---

## 付款結果通知

### 通知流程

```
┌─────────┐     ┌─────────┐     ┌─────────┐
│  消費者  │────▶│  ECPay  │────▶│  商店   │
│  付款   │     │  處理   │     │ ReturnURL│
└─────────┘     └─────────┘     └─────────┘
                     │
                     │ POST 付款結果
                     ▼
               ┌─────────┐
               │  商店   │
               │ 處理結果 │
               └─────────┘
                     │
                     │ 回應 "1|OK"
                     ▼
               ┌─────────┐
               │  ECPay  │
               │ 確認收到 │
               └─────────┘
```

### 通知參數

| 參數 | 類型 | 說明 |
|------|------|------|
| `MerchantID` | String | 商店代號 |
| `MerchantTradeNo` | String | 訂單編號 |
| `StoreID` | String | 分店代號 |
| `RtnCode` | Integer | 交易狀態碼 (`1`=成功) |
| `RtnMsg` | String | 交易訊息 |
| `TradeNo` | String | ECPay 交易編號 |
| `TradeAmt` | Integer | 交易金額 |
| `PaymentDate` | String | 付款時間 `yyyy/MM/dd HH:mm:ss` |
| `PaymentType` | String | 付款方式 |
| `PaymentTypeCharge` | Integer | 支付方式手續費 |
| `TradeDate` | String | 訂單成立時間 |
| `SimulatePaid` | Integer | `0`:一般 `1`:模擬付款 |
| `CheckMacValue` | String | 檢查碼 |
| `CustomField1~4` | String | 自訂欄位 (原值回傳) |

### PaymentType 回傳值對照

| 回傳值 | 說明 |
|--------|------|
| `Credit_CreditCard` | 信用卡 |
| `ATM_ESUN` | ATM 玉山銀行 |
| `ATM_TAISHIN` | ATM 台新銀行 |
| `CVS_CVS` | 超商代碼 |
| `CVS_FAMILY` | 超商代碼 - 全家 |
| `CVS_IBON` | 超商代碼 - 7-11 |
| `BARCODE_BARCODE` | 超商條碼 |
| `ApplePay` | Apple Pay |
| `TWQR_TWQR` | 台灣 Pay |

### 商店回應格式

**成功**: 回應 `1|OK`

```
HTTP/1.1 200 OK
Content-Type: text/plain

1|OK
```

**失敗**: 回應其他內容，ECPay 會在 24 小時內重新發送通知 (最多 10 次)

---

## 訂單查詢

### 端點

```
POST /Cashier/QueryTradeInfo/V5
Content-Type: application/x-www-form-urlencoded
```

### 請求參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `MerchantID` | String(10) | ● | 商店代號 |
| `MerchantTradeNo` | String(20) | ● | 訂單編號 |
| `TimeStamp` | Integer | ● | Unix 時間戳 (3 分鐘內有效) |
| `CheckMacValue` | String | ● | 檢查碼 |
| `PlatformID` | String(10) | 否 | 特約合作平台商代號 |

### 回應參數

| 參數 | 說明 |
|------|------|
| `MerchantID` | 商店代號 |
| `MerchantTradeNo` | 訂單編號 |
| `StoreID` | 分店代號 |
| `TradeNo` | ECPay 交易編號 |
| `TradeAmt` | 交易金額 |
| `PaymentDate` | 付款時間 |
| `PaymentType` | 付款方式 |
| `HandlingCharge` | ECPay 手續費 |
| `PaymentTypeChargeFee` | 支付方式手續費 |
| `TradeDate` | 訂單成立時間 |
| `TradeStatus` | 交易狀態 |
| `ItemName` | 商品名稱 |
| `CheckMacValue` | 檢查碼 |

### TradeStatus 交易狀態

| 狀態 | 說明 |
|------|------|
| `0` | 未付款 |
| `1` | 已付款 |
| `10200095` | 退款完成 |

---

## 信用卡請退款

### 端點

```
POST /CreditDetail/DoAction
Content-Type: application/x-www-form-urlencoded
```

### 請求參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `MerchantID` | String(10) | ● | 商店代號 |
| `MerchantTradeNo` | String(20) | ● | 訂單編號 |
| `TradeNo` | String(20) | ● | ECPay 交易編號 |
| `Action` | String(1) | ● | 動作代碼 |
| `TotalAmount` | Integer | ● | 操作金額 |
| `CheckMacValue` | String | ● | 檢查碼 |

### Action 動作代碼

| 代碼 | 說明 | 使用時機 |
|------|------|----------|
| `C` | 關帳 (請款) | 授權成功後請款 |
| `R` | 退刷 | 已請款後退款 |
| `E` | 取消 | 授權成功尚未請款時取消 |
| `N` | 放棄 | 分期交易放棄 |

### 退款限制

- 信用卡退款: 請款後 1 年內
- 部分退款: 支援 (金額需小於等於原交易金額)
- 多次退款: 支援 (總金額需小於等於原交易金額)

---

## 定期定額

### 建立定期定額訂單參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `PeriodAmount` | Integer | ● | 每次授權金額 |
| `PeriodType` | String(1) | ● | 週期類型 |
| `Frequency` | Integer | ● | 執行頻率 |
| `ExecTimes` | Integer | ● | 總執行次數 |
| `PeriodReturnURL` | String(200) | 否 | 定期定額通知網址 |

### PeriodType 週期類型

| 代碼 | 說明 | Frequency 範圍 |
|------|------|----------------|
| `D` | 日 | 1 ~ 365 |
| `M` | 月 | 1 ~ 12 |
| `Y` | 年 | 1 |

### 定期定額範例

**每月扣款一次，共 12 次**:
```
PeriodAmount=500
PeriodType=M
Frequency=1
ExecTimes=12
```

**每 3 天扣款一次，共 30 次**:
```
PeriodAmount=100
PeriodType=D
Frequency=3
ExecTimes=30
```

### 定期定額查詢

#### 端點

```
POST /Cashier/QueryCreditCardPeriodInfo
Content-Type: application/x-www-form-urlencoded
```

#### 回應參數

| 參數 | 說明 |
|------|------|
| `ExecStatus` | 執行狀態 `1`:終止 `2`:執行中 `3`:完成 |
| `TotalSuccessTimes` | 成功執行次數 |
| `TotalSuccessAmount` | 成功授權總金額 |
| `ExecLog` | 執行記錄陣列 (JSON) |

### 定期定額操作

#### 端點

```
POST /CreditDetail/CreditCardPeriodAction
Content-Type: application/x-www-form-urlencoded
```

#### Action 動作代碼

| 代碼 | 說明 |
|------|------|
| `Cancel` | 取消授權 (終止定期定額) |
| `ReAuth` | 重新授權 |
| `UpdateAmt` | 更新授權金額 |
| `UpdateTimes` | 更新執行次數 |

---

## CheckMacValue 計算

### 計算步驟

1. **排序參數** - 將所有參數依照 Key 字母順序排序 (A-Z, 區分大小寫)
2. **組合字串** - 格式 `key1=value1&key2=value2&...`
3. **加上金鑰** - `HashKey={HashKey}&{參數字串}&HashIV={HashIV}`
4. **URL Encode** - 使用 URL Encode 編碼
5. **轉小寫** - 將編碼後的字串轉為小寫
6. **計算 SHA256** - 計算 SHA256 雜湊值
7. **轉大寫** - 將雜湊值轉為大寫

### URL Encode 特殊字元還原

ECPay 要求部分字元需還原：

| 編碼後 | 還原為 |
|--------|--------|
| `%2d` | `-` |
| `%5f` | `_` |
| `%2e` | `.` |
| `%21` | `!` |
| `%2a` | `*` |
| `%28` | `(` |
| `%29` | `)` |

### Python 實作

```python
import hashlib
import urllib.parse

def generate_check_mac_value(params: dict, hash_key: str, hash_iv: str) -> str:
    """計算 ECPay CheckMacValue"""

    # 1. 排序
    sorted_params = sorted(params.items())

    # 2. 組合
    param_str = '&'.join(f'{k}={v}' for k, v in sorted_params)

    # 3. 加上 HashKey 和 HashIV
    raw = f'HashKey={hash_key}&{param_str}&HashIV={hash_iv}'

    # 4. URL Encode
    encoded = urllib.parse.quote_plus(raw)

    # 5. 轉小寫
    encoded = encoded.lower()

    # 6. SHA256
    sha256 = hashlib.sha256(encoded.encode('utf-8')).hexdigest()

    # 7. 轉大寫
    return sha256.upper()
```

---

## 錯誤碼大全

### 交易狀態碼 (RtnCode)

#### 成功

| 代碼 | 說明 |
|------|------|
| `1` | 交易成功 |

#### 信用卡相關

| 代碼 | 說明 | 處理方式 |
|------|------|----------|
| `10100001` | 參數格式錯誤 | 檢查參數格式 |
| `10100002` | 商店代號不存在 | 確認 MerchantID |
| `10100003` | 訂單編號重複 | 使用新的訂單編號 |
| `10100004` | 訂單編號格式錯誤 | 僅英數字，20 字內 |
| `10100050` | 交易金額錯誤 | 確認金額為正整數 |
| `10100058` | CheckMacValue 錯誤 | 重新計算檢查碼 |
| `10100248` | 交易被拒絕 | 請客戶聯繫發卡銀行 |
| `10100249` | 交易失敗 | 系統錯誤，稍後重試 |
| `10100251` | 卡片過期 | 請客戶確認卡片效期 |
| `10100252` | 餘額不足 | 請客戶確認額度或餘額 |
| `10100253` | 超過交易限額 | 請客戶分筆交易或聯繫發卡銀行 |
| `10100254` | 交易受限 | 請客戶聯繫發卡銀行 |
| `10100255` | 掛失卡 | 請客戶使用其他卡片 |
| `10100256` | 偽卡 | 請客戶使用其他卡片 |
| `10100257` | 安控失敗 | 3D 驗證失敗，請重試 |
| `10300066` | 交易結果待確認 | 至後台確認後再出貨 |

#### ATM 相關

| 代碼 | 說明 |
|------|------|
| `2` | ATM 取號失敗 |
| `10100073` | CVS/BARCODE 取號成功 |
| `10100074` | CVS/BARCODE 取號失敗 |

#### 系統相關

| 代碼 | 說明 |
|------|------|
| `10200047` | 訂單已關帳 |
| `10200048` | 訂單已取消 |
| `10200095` | 退款完成 |

### CheckMacValue 錯誤

| 錯誤訊息 | 原因 | 解決方式 |
|----------|------|----------|
| `CheckMacValue verification failed` | 檢查碼計算錯誤 | 確認 HashKey/HashIV、排序、編碼 |
| `HashKey 或 HashIV 錯誤` | 金鑰錯誤 | 確認測試/正式環境金鑰 |

---

## 銀行代碼對照表

### ATM 銀行代碼

| 代碼 | 銀行名稱 |
|------|----------|
| `004` | 臺灣銀行 |
| `005` | 土地銀行 |
| `006` | 合作金庫 |
| `007` | 第一銀行 |
| `008` | 華南銀行 |
| `009` | 彰化銀行 |
| `011` | 上海銀行 |
| `012` | 台北富邦 |
| `013` | 國泰世華 |
| `017` | 兆豐銀行 |
| `021` | 花旗銀行 |
| `048` | 王道銀行 |
| `050` | 臺灣企銀 |
| `052` | 渣打銀行 |
| `053` | 台中銀行 |
| `054` | 京城銀行 |
| `081` | 滙豐銀行 |
| `102` | 華泰銀行 |
| `103` | 新光銀行 |
| `108` | 陽信銀行 |
| `118` | 板信銀行 |
| `147` | 三信銀行 |
| `803` | 聯邦銀行 |
| `805` | 遠東銀行 |
| `806` | 元大銀行 |
| `807` | 永豐銀行 |
| `808` | 玉山銀行 |
| `809` | 凱基銀行 |
| `810` | 星展銀行 |
| `812` | 台新銀行 |
| `816` | 安泰銀行 |
| `822` | 中國信託 |

---

## 常見問題排解

### CheckMacValue 錯誤

**問題**: 收到 `CheckMacValue verification failed`

**檢查項目**:
1. HashKey 和 HashIV 是否正確 (測試/正式環境不同)
2. 參數排序是否依照字母順序 (區分大小寫)
3. URL Encode 是否正確 (特殊字元需還原)
4. 是否轉小寫後再計算 SHA256
5. 最後是否轉大寫

### 訂單編號重複

**問題**: 收到 `10100003` 訂單編號重複

**解決**:
- 使用時間戳 + 隨機數產生唯一編號
- 訂單編號最長 20 字元，僅英數字

```python
import time
import random
order_id = f"ORD{int(time.time())}{random.randint(100, 999)}"
```

### 付款通知未收到

**問題**: 付款成功但沒收到 ReturnURL 通知

**檢查項目**:
1. ReturnURL 是否為 HTTPS
2. 伺服器是否能被外網存取
3. 防火牆是否阻擋 ECPay IP
4. 是否正確回應 `1|OK`

**ECPay 通知 IP 白名單**:
```
211.23.128.0/24
220.130.179.0/24
210.200.216.0/24
```

### 模擬付款

**問題**: SimulatePaid = 1

**說明**: 測試環境的模擬付款，正式環境不會有此情況

### 金額限制

**問題**: 交易金額錯誤

**各付款方式限制**:
| 付款方式 | 最低 | 最高 |
|----------|------|------|
| 信用卡 | 1 | 無限制 |
| ATM | 1 | 5,000,000 |
| CVS | 27 | 20,000 |
| BARCODE | 1 | 20,000 |
| TWQR | 6 | 49,999 |

---

## 官方資源

- **開發者中心**: https://developers.ecpay.com.tw/
- **API 文件下載**: https://www.ecpay.com.tw/Service/API_Dwnld
- **商店後台 (測試)**: https://vendor-stage.ecpay.com.tw/
- **商店後台 (正式)**: https://vendor.ecpay.com.tw/
- **技術客服**: techsupport@ecpay.com.tw
- **客服電話**: (02) 2655-1775

---

## ChoosePayment 完整對照表 (2024+)

ECPay AIO 支援的所有 `ChoosePayment` 參數值：

| ChoosePayment 值 | 中文名 | 類別 | 說明 |
|---|---|---|---|
| `Credit` | 信用卡 (含銀聯/AMEX) | 信用卡 | 一次付清 / 分期 / 紅利 / 定期定額 |
| `WebATM` | 網路 ATM | ATM | 即時轉帳，最高 NT$49,999 |
| `ATM` | ATM 虛擬帳號 | ATM | 產生繳費帳號，最高 NT$49,999 |
| `CVS` | 超商代碼 | 超商 | 至四大超商繳費，30-20,000 元 |
| `BARCODE` | 超商條碼 | 超商 | 產生繳費條碼，20-40,000 元 |
| `ApplePay` | Apple Pay | 行動支付 | 需向 ECPay 申請 |
| `TWQR` | 歐付寶 TWQR | 行動支付 | 台灣 Pay QR Code |
| `BNPL` | 無卡分期 | 分期 | 含裕富、中租、Atome 等 |
| `WeiXin` | 微信支付 | 跨境 | **較新**，提供陸客掃碼支付 |
| `DigitalPayment` | 電子支付 / 電子錢包 umbrella | 行動支付 | **較新**，客戶於 ECPay 收銀頁挑選具體方式 |
| `EcpayPay` | 綠界Pay | 行動支付 | **較新**，ECPay 自家錢包 |
| `ALL` | 不指定 (顯示選擇頁) | 全部 | 由 ECPay 統一收銀台讓客戶挑 |

### `DigitalPayment` umbrella 涵蓋範圍

當設定 `ChoosePayment=DigitalPayment` 時，ECPay 收銀頁會列出以下電子支付選項供客戶挑選：

- **街口支付** (JKO Pay)
- **全盈+PAY** (玉山金控)
- **全支付** (PX Pay Plus, 全聯系)
- **一卡通 MONEY** (iPASS Money)
- **悠遊付** (Easy Wallet)
- **icash Pay** (愛金卡)
- **OPENPOINT** (7-11/統一集團)

> ⚠️ DigitalPayment 為**統一收銀頁**設計：商家無法透過 API 直接指定具體方式，只能讓客戶於 ECPay 託管頁面自行選擇。如需指定特定電子支付（例如僅開放街口），請使用 NewebPay / PAYUNi（它們以個別參數開放各方式）。

### 新方式速查

| 方式 | ECPay 直連 | NewebPay 直連 |
|---|---|---|
| 街口支付 (JKO Pay) | DigitalPayment umbrella | `JKOPAY` |
| 全盈+PAY | DigitalPayment umbrella | `PLUSPAY` |
| 全支付 (PXPay+) | DigitalPayment umbrella | `PXPAY` |
| 一卡通 MONEY | DigitalPayment umbrella | `IPASSPAY` |
| 悠遊付 (Easy Wallet) | DigitalPayment umbrella | `EASYCARD` |
| icash Pay | DigitalPayment umbrella | `ICASHPAY` |
| OPENPOINT | DigitalPayment umbrella | — |
| Atome BNPL | `BNPL` umbrella | — |
| 微信支付 | `WeiXin` 直連 | `EZPWECHAT` |

> NewebPay / PAYUNi 通常以個別 channel/method 參數開放每種方式；ECPay 採 umbrella 設計，整合較簡單但選擇權交給消費者。

最後更新：2026/05/07
