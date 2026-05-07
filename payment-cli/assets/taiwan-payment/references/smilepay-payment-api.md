# SmilePay Payment API Reference

速買配 (SmilePay) 金流 API 完整參考文件。

> 本文件以速買配 WooCommerce 模組為主要分析來源，整理出常用的 `SPPayment.asp` (虛擬帳號 / 超商代碼 / 條碼) 與 `mtmk_utf.asp` (信用卡 / 銀聯) 兩條主要金流通道。實際上線時，建議再向速買配技術窗口確認最新版本的參數欄位。

---

## 目錄

1. [基本說明](#基本說明)
2. [API 端點總覽](#api-端點總覽)
3. [環境資訊](#環境資訊)
4. [認證方式](#認證方式)
5. [通用參數](#通用參數)
6. [訂單建立 (取號類)](#訂單建立-取號類)
7. [ATM 虛擬帳號](#atm-虛擬帳號)
8. [超商條碼 (Barcode)](#超商條碼-barcode)
9. [7-11 ibon 代碼繳費](#7-11-ibon-代碼繳費)
10. [全家 FamiPort 代碼繳費](#全家-famiport-代碼繳費)
11. [信用卡 (一次付清)](#信用卡-一次付清)
12. [信用卡分期](#信用卡分期)
13. [銀聯/國際信用卡 (Union)](#銀聯國際信用卡-union)
14. [付款結果通知 (Roturl)](#付款結果通知-roturl)
15. [Mid_smilepay 簽章驗證](#mid_smilepay-簽章驗證)
16. [訂單查詢與退款](#訂單查詢與退款)
17. [錯誤代碼](#錯誤代碼)
18. [支付方式對照表](#支付方式對照表)
19. [常見問題排解](#常見問題排解)

---

## 基本說明

**速買配 (SmilePay)** 是台灣老牌金流服務商，提供整合型的收款平台，主要特色：

- 一支 API (`SPPayment.asp`) 涵蓋多種非同步付款方式 (ATM、超商代碼、條碼、ibon、FamiPort)
- 信用卡 / 銀聯卡走另一支 `mtmk_utf.asp` 結帳頁端點
- 回應格式為 **XML** (非 JSON)，需以 `simplexml_load_string` 或同等方式解析
- 通知 (Roturl) 採 **明碼欄位 + Mid_smilepay 數值簽章** 驗證身分
- 部分中文欄位 (`Errdesc`、`Process_time`、`Address`) 可能以 **BIG-5** 編碼回傳，需做轉碼

### 與其他金流的差異

| 特性 | SmilePay | ECPay | NewebPay |
|------|----------|-------|----------|
| 編碼 | UTF-8 (送出) / BIG-5 (部分通知欄位) | UTF-8 | UTF-8 |
| 回應格式 | XML | application/x-www-form-urlencoded | JSON |
| 簽章 | Verify_key + Mid_smilepay 校驗碼 | SHA256 CheckMacValue | AES + SHA256 |
| 端點分離 | 取號/結帳分兩支 API | 統一 AioCheckOut | 統一 MPG |

---

## API 端點總覽

### 取號 / 訂單建立

| 功能 | 端點 |
|------|------|
| 訂單建立 (ATM/條碼/ibon/FamiPort) | `https://ssl.smse.com.tw/api/SPPayment.asp` |
| 信用卡 / 銀聯 結帳頁 (GET / Form) | `https://ssl.smse.com.tw/ezpos/mtmk_utf.asp` |
| 訂單修改 / 取消 (官方文件提供) | `https://ssl.smse.com.tw/api/SPPayment_Modify.asp` |

### 通知端點 (由商店實作，速買配回呼)

| 用途 | 商店端範例路徑 |
|------|----------------|
| 一般取號類付款結果 | `?wc-api=roturl` (WooCommerce 範例) |
| 信用卡 / 銀聯付款結果 | `?wc-api=credit_roturl` |

> **重要**：所有 API 均為 HTTPS。`SPPayment.asp` 採 `application/x-www-form-urlencoded` POST，`mtmk_utf.asp` 同時支援 GET querystring (常用) 與 POST。

---

## 環境資訊

### 測試環境帳號 (官方公開測試參數)

```
Dcvc        : 107
Rvg2c       : 1
Verify_key  : 174A02F97A95F72CE301137B3F98D128
mid         : 1111
```

> 此組測試參數常見於開發測試，正式上線時請改用商店後台核發的 `Dcvc` / `Rvg2c` / `Verify_key` / `mid`。

### 正式環境

正式環境 URL 與測試環境相同 (`ssl.smse.com.tw`)，差異只在於使用的 `Dcvc` / `Verify_key` 等帳號參數。
申請正式帳號後，請至速買配商店後台 → 金流設定取得實際參數。

### 測試卡號

信用卡 / 銀聯走 `mtmk_utf.asp` 模擬結帳頁，速買配會引導使用內部測試卡片，正式上線前向其客服索取最新測試卡號。

---

## 認證方式

SmilePay 並不採用 ECPay 的 SHA256 摘要驗證；而是以「**帳號參數三件組 + 服務端校驗**」進行。

### 1. 帳號驗證 (送出時)

每次呼叫 `SPPayment.asp` / `mtmk_utf.asp` 都需要帶上：

| 欄位 | 說明 | 必填 |
|------|------|------|
| `Dcvc` | 商店代號 | ● |
| `Rvg2c` | 收款銀行代號 / 路由碼 (`1` 為預設) | ● |
| `Verify_key` | 商店驗證金鑰 (32 碼大寫 hex) | ● |

> 三項擇一錯誤即會在 XML 回應的 `Status` 收到非 `1` 的錯誤代碼。

### 2. 通知驗章 (回呼時)

速買配在 Roturl 回呼會額外帶 `Mid_smilepay` 與 `Smseid`，商家需依下方[Mid_smilepay 簽章驗證](#mid_smilepay-簽章驗證) 演算法重算後比對，避免假通知。

### 安全性建議

- `Verify_key`、`Dcvc` 僅可保存於後端，**不要寫進前端 JS**
- Roturl 必須 HTTPS、Mid_smilepay 一律驗證
- 訂單金額需以「成立訂單時保存的金額」為準，不可信賴回呼裡的 `Amount`

---

## 通用參數

以下為 `SPPayment.asp` 取號類請求共用的欄位。所有金額為整數新台幣 (TWD)，不可有小數。

### 必填欄位

| 參數 | 類型 | 長度 | 說明 |
|------|------|------|------|
| `Dcvc` | String | 7 | 商店代號 |
| `Rvg2c` | String | 1 | 收款銀行 / 路由 |
| `Verify_key` | String | 32 | 驗證金鑰 |
| `Pay_zg` | String | 2 | 付款方式代碼 (見[支付方式對照表](#支付方式對照表)) |
| `Data_id` | String | 20 | 商店訂單編號 (需唯一) |
| `Amount` | Integer | - | 訂單金額 (整數) |
| `Pur_name` | String | 20 | 訂購人姓名 (UTF-8) |
| `Mobile_number` | String | 15 | 訂購人手機 |
| `Email` | String | 60 | 訂購人 Email |

### 選填 / 條件必填

| 參數 | 類型 | 長度 | 說明 |
|------|------|------|------|
| `Tel_number` | String | 15 | 市話 (常以手機帶入) |
| `Address` | String | 100 | 收件地址 (UTF-8) |
| `od_sob` | String | 49 | 商品名稱 / 品項摘要 (`product*qty｜...`) |
| `Deadline_date` | String | 10 | 繳費期限 `YYYY/MM/DD` (條碼/ATM/ibon/FamiPort 必填) |
| `Roturl` | String | 200 | 付款結果通知網址 (商家端) |
| `Roturl_status` | String | 30 | 通知狀態識別字串 (商家自訂，例如 `woook1.1.23`) |
| `Remark` | String | 100 | 訂單備註 |
| `Invoice_num` | String | 20 | 發票買受人統編 / 載具 (報表匯出用) |

### 訂單編號 (`Data_id`) 注意事項

- 僅允許英數字
- 同一個 Dcvc 下不可重複
- 當前訂單若取號失敗，可使用同一筆 `Data_id` 重打；若已成功取號則需換新編號

### 商品名稱 (`od_sob`) 注意事項

- WooCommerce 模組以 `品名*數量｜品名*數量` 串接，超出長度截斷
- 取號類 (`SPPayment.asp`) 限制 **45 個字元**
- 結帳頁 (`mtmk_utf.asp`) 限制 **49 個字元**
- 中文以 UTF-8 計算，建議事先 `mb_substr` 截斷避免亂碼

---

## 訂單建立 (取號類)

### 流程

```
┌─────────┐  POST application/x-www-form-urlencoded  ┌─────────┐
│  商店   │ ───────────────────────────────────────▶ │ SmilePay│
│         │           Verify_key + Pay_zg            │         │
└─────────┘                                          └─────────┘
     ▲                                                    │
     │              XML <SmilePay>...</SmilePay>          │
     └────────────────────────────────────────────────────┘
```

### 共用回應 (XML)

成功時 HTTP 200，body 為 XML：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<SmilePay>
  <Status>1</Status>
  <Desc>OK</Desc>
  <Data_id>20260507001</Data_id>
  <SmilePayNO>2401234567</SmilePayNO>
  <Amount>1500</Amount>
  <PayEndDate>2026/05/14</PayEndDate>
  <!-- 依 Pay_zg 不同還會有：AtmBankNo / AtmNo / Barcode1~3 / IbonNo / FamiNO -->
</SmilePay>
```

### 共用回應欄位

| 欄位 | 說明 |
|------|------|
| `Status` | `1` = 成功；其他為錯誤碼 |
| `Desc` | 處理結果描述 (錯誤時為錯誤訊息) |
| `Data_id` | 商店訂單編號 (原值回傳) |
| `SmilePayNO` | 速買配金流追蹤碼 (10 碼) |
| `Amount` | 訂單金額 |
| `PayEndDate` | 繳費期限 |

### 失敗時的處理

當 `Status != 1` 時，建議：

1. 將該訂單標記為 `failed`
2. 訂單備註寫入 `Status` + `Desc`
3. 不要重發 (避免重複扣 API 配額)

```python
import requests
import xml.etree.ElementTree as ET

resp = requests.post(
    "https://ssl.smse.com.tw/api/SPPayment.asp",
    data=post_data,
    timeout=30,
)
root = ET.fromstring(resp.text)
status = root.findtext("Status")
desc = root.findtext("Desc")

if status != "1":
    raise RuntimeError(f"SmilePay 取號失敗：{status} / {desc}")
```

---

## ATM 虛擬帳號

### Pay_zg 設定

```
Pay_zg = 2
```

### 額外欄位

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `Deadline_date` | String | ● | 繳費期限 `YYYY/MM/DD`，最大 720 天 |

> 模組預設：未指定時為「下單日 + 7 天」。

### ATM 回應欄位

| 欄位 | 說明 |
|------|------|
| `AtmBankNo` | 銀行代碼 (3 碼) |
| `AtmNo` | 虛擬帳號 (14~16 碼) |
| `Amount` | 應繳金額 |
| `PayEndDate` | 繳費期限 |
| `SmilePayNO` | 金流追蹤碼 |

### 範例 Request

```
POST /api/SPPayment.asp HTTP/1.1
Host: ssl.smse.com.tw
Content-Type: application/x-www-form-urlencoded

Dcvc=107&Rvg2c=1&Verify_key=174A02F97A95F72CE301137B3F98D128
&Pay_zg=2&Pur_name=%E7%8E%8B%E5%B0%8F%E6%98%8E
&Mobile_number=0912345678&Email=test%40example.com
&Data_id=ORD20260507001&od_sob=%E5%95%86%E5%93%81A*1
&Amount=1500&Deadline_date=2026/05/14
&Roturl=https%3A%2F%2Fshop.example.com%2Fcallback%2Froturl
&Roturl_status=woook1.1.23
```

### 範例 Response

```xml
<SmilePay>
  <Status>1</Status>
  <Desc>OK</Desc>
  <Data_id>ORD20260507001</Data_id>
  <SmilePayNO>2410287654</SmilePayNO>
  <AtmBankNo>012</AtmBankNo>
  <AtmNo>9221234567890123</AtmNo>
  <Amount>1500</Amount>
  <PayEndDate>2026/05/14</PayEndDate>
</SmilePay>
```

### 金額限制 (一般商家設定)

- 最低：8 元 (模組預設)
- 最高：20,000 元 (模組預設)
- 實際上限請依速買配後台、收款銀行規範

---

## 超商條碼 (Barcode)

### Pay_zg 設定

```
Pay_zg = 3
```

可至 7-11、全家、萊爾富、OK 四大超商列印條碼繳費。

### 額外欄位

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `Deadline_date` | String | ● | 繳費期限 `YYYY/MM/DD`，模組限制 < 50 天 |

### Barcode 回應欄位

| 欄位 | 說明 |
|------|------|
| `Barcode1` | 第 1 段條碼 |
| `Barcode2` | 第 2 段條碼 |
| `Barcode3` | 第 3 段條碼 |
| `Amount` | 應繳金額 |
| `PayEndDate` | 繳費期限 |
| `SmilePayNO` | 金流追蹤碼 |

### 顯示繳費單

商家通常會以三段條碼產出可列印的繳費單頁面，必填欄位：

- `barcode1` / `barcode2` / `barcode3`
- `pay_end_date` (`YYYY/MM/DD`)
- `customer_hotline` (商家客服電話，貼條碼用)
- `amount`、`order_id`、`products`

### 金額限制

- 最低：8 元
- 最高：20,000 元 (各大超商限制)

---

## 7-11 ibon 代碼繳費

### Pay_zg 設定

```
Pay_zg = 4
```

於 7-11 ibon 機台或 LifeET 輸入代碼繳費。

### 額外欄位

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `Deadline_date` | String | ● | 繳費期限 `YYYY/MM/DD`，模組限制 < 7 天 |

### ibon 回應欄位

| 欄位 | 說明 |
|------|------|
| `IbonNo` | ibon 繳費代碼 |
| `Amount` | 應繳金額 |
| `PayEndDate` | 繳費期限 |
| `SmilePayNO` | 金流追蹤碼 |

### 金額限制

- 最低：8 元
- 最高：20,000 元

---

## 全家 FamiPort 代碼繳費

### Pay_zg 設定

```
Pay_zg = 6
```

於全家 FamiPort 機台 (亦可在 LifeET) 輸入代碼繳費。

### 額外欄位

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `Deadline_date` | String | ● | 繳費期限 `YYYY/MM/DD`，模組限制 < 7 天 |

### FamiPort 回應欄位

| 欄位 | 說明 |
|------|------|
| `FamiNO` | FamiPort 繳費代碼 |
| `Amount` | 應繳金額 |
| `PayEndDate` | 繳費期限 |
| `SmilePayNO` | 金流追蹤碼 |

### 金額限制

- 最低：8 元
- 最高：20,000 元

---

## 信用卡 (一次付清)

### 端點與流程

信用卡並非 API 取號，而是 **將消費者導向 SmilePay 結帳頁**：

```
GET https://ssl.smse.com.tw/ezpos/mtmk_utf.asp?Dcvc=...&Pay_zg=1&Data_id=...
```

商店端流程：

1. 後端組好參數 → `http_build_query` 產生 querystring
2. 將 querystring 接到 `mtmk_utf.asp?` 後
3. 把網址當成 redirect URL 回傳給前端 (例如 WooCommerce `process_payment` 回 `redirect`)
4. 消費者於 SmilePay 頁面輸入卡號、3D 驗證
5. 結束後 SmilePay 以 querystring 帶結果到 `Roturl`

### Pay_zg 設定

```
Pay_zg = 1
```

### 必填欄位 (mtmk_utf.asp)

| 欄位 | 說明 |
|------|------|
| `Dcvc` / `Rvg2c` / `Verify_key` | 帳號驗證 |
| `Pay_zg` | `1` |
| `Pur_name` | 持卡人姓名 (UTF-8) |
| `Mobile_number` / `Tel_number` | 聯絡電話 |
| `Email` | Email |
| `Address` | 帳單地址 (建議帶) |
| `Data_id` | 商店訂單編號 |
| `od_sob` | 商品名稱 (49 字內) |
| `Amount` | 整數金額 |
| `Roturl` | 付款結果 URL，可附 querystring (如 `?Payment_title=...`) |
| `Roturl_status` | 通知識別字串 |
| `Remark` | 備註 |
| `Invoice_num` | 發票統編 / 載具 |

### 結帳頁 redirect 範例

```python
from urllib.parse import urlencode

base = "https://ssl.smse.com.tw/ezpos/mtmk_utf.asp"
params = {
    "Dcvc": "107",
    "Rvg2c": "1",
    "Verify_key": "174A02F97A95F72CE301137B3F98D128",
    "Pay_zg": "1",
    "Pur_name": "王小明",
    "Mobile_number": "0912345678",
    "Email": "test@example.com",
    "Data_id": "ORD20260507002",
    "od_sob": "商品A*1",
    "Amount": 1500,
    "Roturl": "https://shop.example.com/wc-api/credit_roturl?Payment_title=信用卡",
    "Roturl_status": "woook1.1.23",
}
redirect_url = f"{base}?{urlencode(params)}"
```

### 信用卡通知 (`credit_roturl`) 額外欄位

| 欄位 | 說明 |
|------|------|
| `Classif` | `A` = 授權；`O`/`T` = 完成 |
| `Response_id` | `1` = 成功；其他為失敗 |
| `Smseid` | 速買配金流追蹤碼 |
| `Amount` | 授權金額 |
| `Process_date` | 授權日期 |
| `Process_time` | 授權時間 (可能是 BIG-5) |
| `Address` | 帳單地址 (BIG-5) |
| `Errdesc` | 失敗原因 (BIG-5) |
| `Payment_title` | 付款方式名稱 (商店帶入後再回傳) |
| `Mid_smilepay` | 校驗碼 (見[Mid_smilepay 簽章驗證](#mid_smilepay-簽章驗證)) |

### 成功判斷

```python
if classif == "A" and response_id == "1" and amount == order.total:
    order.status = "processing"  # 授權成功
else:
    order.status = "failed"
```

> 模組以 `Amount == 訂單金額` 為通過條件，金額若不符會落入失敗分支，避免被改價攻擊。

---

## 信用卡分期

### Pay_zg 設定

```
Pay_zg = 1   ← 與一次付清相同
Stage  = 3   ← 額外帶入分期數
```

### 額外欄位

| 欄位 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `Stage` | Integer | ● | 分期期數，常見 `3 / 6 / 12 / 18 / 24` |

### 分期支援

模組預設提供：

- 3 期
- 6 期
- 12 期
- 18 期
- 24 期

> 實際支援期數視速買配與發卡銀行協議；若送出未開通的期數，速買配結帳頁會擋下並回失敗 `Errdesc`。

### 範例

```python
params = {
    # 與信用卡相同
    "Dcvc": "107", "Rvg2c": "1", "Verify_key": "...",
    "Pay_zg": "1",
    "Stage": 6,                # ← 6 期
    "Data_id": "ORD20260507003",
    "Amount": 12000,
    # ...
}
redirect_url = "https://ssl.smse.com.tw/ezpos/mtmk_utf.asp?" + urlencode(params)
```

### 注意事項

- 分期下單建議設最低消費金額 (模組預設 8，但實務上多為 1,000 元以上才符合銀行政策)
- 銀聯卡不支援分期
- 同一筆訂單僅能擇一：一次付清 / 分期

---

## 銀聯/國際信用卡 (Union)

### Pay_zg 設定

```
Pay_zg = 11
```

### 端點

走 `mtmk_utf.asp` (與信用卡相同)，差別只在 `Pay_zg=11`。

### 欄位

與[信用卡 (一次付清)](#信用卡-一次付清) 相同，**不支援 `Stage` 分期**。

### 注意事項

- 銀聯卡需向 SmilePay 申請開通
- 部分銀聯卡會走國際 3D Secure 驗證，回傳時間較長
- `Errdesc` 可能以 BIG-5 編碼，務必轉碼後才寫入訂單備註

---

## 付款結果通知 (Roturl)

SmilePay 在消費者完成付款 (取號類) 或刷卡 (信用卡 / 銀聯) 後，會以 **GET / POST** 帶 querystring 通知商家。

### 通知通道

| 付款方式 | 觸發時機 | 推薦對應 endpoint |
|----------|----------|-------------------|
| ATM | 入帳成功後 | `?wc-api=roturl` |
| 條碼 / ibon / FamiPort | 超商繳費後 | `?wc-api=roturl` |
| 信用卡 / 分期 | 結帳頁授權結束後 | `?wc-api=credit_roturl` |
| 銀聯 | 結帳頁授權結束後 | `?wc-api=credit_roturl` |

### 取號類通知 (`roturl`) 欄位

| 欄位 | 說明 |
|------|------|
| `Classif` | 通知類型 (見下表) |
| `Data_id` | 商店訂單編號 |
| `Smseid` | 速買配金流追蹤碼 |
| `Amount` | 入帳金額 |
| `Process_date` | 入帳日期 `YYYY/MM/DD` |
| `Process_time` | 入帳時間 `HH:MM:SS` (可能 BIG-5) |
| `Mid_smilepay` | 校驗碼 |

### Classif 通知類型

| 值 | 說明 |
|----|------|
| `A` | 信用卡 / 銀聯授權通知 |
| `B` | ATM 虛擬帳號入帳 |
| `C` | 超商代碼 / 條碼 入帳 |
| `T` | 配合貨到付款結案 |
| `O` | 其他完成狀態 |

> 註：以上來自 WooCommerce 模組對 `Classif` 的處理邏輯 (T/O 直接 completed，其餘 processing)。完整官方對照請以速買配規格書為準。

### 商店回應格式

成功處理後須回應一個指定字串，例如：

```
HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8

<Roturlstatus>woook1.1.23</Roturlstatus>
```

回應的字串需與商家在送出訂單時填的 `Roturl_status` 一致；速買配收到對應字串後即視為通知成功，否則會重送。

### 失敗訊息範例

```
<Roturlstatus>無Classif!!</Roturlstatus>           ← 缺欄位
<Roturlstatus>金額有小數點!!</Roturlstatus>         ← 金額異常
<Roturlstatus>未付款或金額為0</Roturlstatus>        ← 金額為空
<Roturlstatus>查無訂單!!</Roturlstatus>             ← Data_id 找不到
<Roturlstatus>Mid_smilepay不符合!!</Roturlstatus>   ← 簽章驗證失敗
```

### 通知處理檢查清單

- [ ] 必要欄位都存在 (`Classif` / `Data_id` / `Amount` / `Smseid` / `Mid_smilepay`)
- [ ] `Amount` 是整數 (沒有小數)
- [ ] 訂單存在且尚未進入「處理中 / 已完成」
- [ ] `Mid_smilepay` 重新計算後相符
- [ ] 入帳金額 = 原訂單金額 (信用卡分支特別重要)
- [ ] BIG-5 欄位轉成 UTF-8 後再儲存

---

## Mid_smilepay 簽章驗證

`Mid_smilepay` 是 SmilePay 防止假通知的數值校驗碼，演算法可從 WooCommerce 模組推導：

### 演算法

1. 取 `Smseid` 末 4 碼 → `r1 r2 r3 r4`，若非數字以 `9` 取代
2. `Amount` 補零至 8 碼 (左補) → `str1`
3. 串接：`str = mid + str1 + r1 + r2 + r3 + r4` (16 碼)
4. 將 16 碼依索引切：偶數位 (0,2,4...14) 加總為 `even`，奇數位 (1,3,5...15) 加總為 `odd`
5. `Mid_smilepay = even * 9 + odd * 3`

### Python 實作

```python
def calc_mid_smilepay(mid: str, amount: int, smseid: str) -> int:
    """計算 SmilePay Mid_smilepay 校驗碼"""
    r_all = smseid[-4:]
    r = []
    for ch in r_all:
        r.append(ch if ch.isdigit() else "9")
    r1, r2, r3, r4 = r

    str1 = str(amount).zfill(8)
    s = f"{mid}{str1}{r1}{r2}{r3}{r4}"
    assert len(s) == 16, "mid 長度需確保 mid+str1+rcode=16"

    even = sum(int(s[i]) for i in range(16) if i % 2 == 0)
    odd  = sum(int(s[i]) for i in range(16) if i % 2 == 1)
    return even * 9 + odd * 3


# 驗證範例
def verify_callback(mid, amount, smseid, mid_smilepay_received):
    return str(calc_mid_smilepay(mid, amount, smseid)) == str(mid_smilepay_received)
```

### 注意

- `mid` 為商家的「金流 mid」，由 SmilePay 後台核發；測試模式為 `1111`
- 若商店尚未設定 `mid`，模組會跳過驗章 → 上線前**務必填入**
- 一旦驗章失敗，回應 `<Roturlstatus>Mid_smilepay不符合!!</Roturlstatus>` 並結束處理

---

## 訂單查詢與退款

### 訂單修改 / 退款

SmilePay 提供 `SPPayment_Modify.asp` 端點 (官方規格書) 用於：

- 取消尚未授權的信用卡訂單
- 信用卡退款 / 退刷
- 修改 ATM 期限 / 金額

```
POST https://ssl.smse.com.tw/api/SPPayment_Modify.asp
Content-Type: application/x-www-form-urlencoded
```

### 通用必填

| 欄位 | 說明 |
|------|------|
| `Dcvc` / `Rvg2c` / `Verify_key` | 帳號驗證 |
| `Smseid` | 速買配金流追蹤碼 (對應 `SmilePayNO`) |
| `Modify_type` | 動作代碼 (依官方規格設定) |
| `Amount` | 退款 / 修改後金額 |

> WooCommerce 模組未直接整合此 API，建議參考速買配最新版規格書 (`SmilePay_API_v*.pdf`) 取得完整 `Modify_type` 對照表。

### 訂單查詢

實務上 SmilePay 的後續通知為主要狀態來源；商家如需主動查詢 (對帳)：

- 透過商店後台「交易查詢」匯出
- 或使用速買配提供的對帳 API (需另行開通)

### 退款限制 (一般慣例)

- 信用卡：請款後 6 個月內 (依發卡銀行)
- 部分退款：信用卡支援；ATM / 超商需走「退匯款」程序
- 取號類訂單未付款者：可由商家直接標記為作廢，無需通知 SmilePay

---

## 錯誤代碼

XML 回應的 `Status` 欄位常見值：

### 成功

| 代碼 | 說明 |
|------|------|
| `1` | 取號 / 建立成功 |

### 帳號 / 驗章類

| 代碼 | 說明 | 處理方式 |
|------|------|----------|
| `-1` | 必要參數缺漏 | 檢查 Dcvc / Verify_key / Pay_zg / Data_id / Amount |
| `-2` | 帳號驗證失敗 | 確認 Dcvc / Rvg2c / Verify_key 是否一致 |
| `-3` | 商店狀態異常 | 聯繫 SmilePay 客服啟用商店 |
| `-4` | 路由 / 收款銀行錯誤 | 確認 Rvg2c |

### 訂單 / 金額類

| 代碼 | 說明 | 處理方式 |
|------|------|----------|
| `-10` | Data_id 重複 | 換新訂單編號 |
| `-11` | Data_id 格式錯誤 | 僅英數 20 碼內 |
| `-12` | 金額錯誤 | 整數 + 在限額內 |
| `-13` | 商品名稱 (`od_sob`) 過長 | 取號類 ≤ 45 字、結帳頁 ≤ 49 字 |
| `-14` | 繳費期限格式錯誤 | `YYYY/MM/DD` |

### 付款方式類

| 代碼 | 說明 |
|------|------|
| `-20` | Pay_zg 不支援 |
| `-21` | 該付款方式商店未開通 |
| `-22` | 分期 (Stage) 未開通或金額不符 |
| `-23` | 銀聯卡未開通 |

> 上述代碼依 SmilePay 官方規格書整理；實際以最新規格書為準，若收到未列代碼，以 `Desc` 為主。

### Roturl 自訂錯誤訊息 (商家回給 SmilePay)

| 訊息 | 觸發條件 |
|------|----------|
| `<Roturlstatus>無Classif!!</Roturlstatus>` | 通知缺欄位 |
| `<Roturlstatus>金額有小數點!!</Roturlstatus>` | Amount 非整數 |
| `<Roturlstatus>未付款或金額為0</Roturlstatus>` | Amount 為空或 0 |
| `<Roturlstatus>查無訂單!!</Roturlstatus>` | Data_id 不存在 |
| `<Roturlstatus>Mid_smilepay不符合!!</Roturlstatus>` | 簽章驗證失敗 |

---

## 支付方式對照表

### Pay_zg 一覽

| Pay_zg | 名稱 | 端點 | 備註 |
|--------|------|------|------|
| `1` | 信用卡 (一次付清) | `mtmk_utf.asp` | 走結帳頁 |
| `1` + `Stage` | 信用卡分期 | `mtmk_utf.asp` | `Stage=3/6/12/18/24` |
| `2` | ATM 虛擬帳號 | `SPPayment.asp` | 取號類 |
| `3` | 超商條碼 | `SPPayment.asp` | 4 大超商 |
| `4` | 7-11 ibon | `SPPayment.asp` | LifeET 通用 |
| `6` | 全家 FamiPort | `SPPayment.asp` | LifeET 通用 |
| `11` | 銀聯 / 國際信用卡 | `mtmk_utf.asp` | 不支援分期 |

> 速買配尚有其他 Pay_zg (如 LINE Pay、行動支付等)；WooCommerce 模組僅實作上述 7 種。

### 付款回應欄位對照

| Pay_zg | 顯示給消費者的欄位 |
|--------|---------------------|
| `1` (信用卡) | 結帳頁授權即完成；通知含 `Smseid` / `Amount` / `Process_date` |
| `2` (ATM) | `AtmBankNo` + `AtmNo` |
| `3` (條碼) | `Barcode1` / `Barcode2` / `Barcode3` |
| `4` (ibon) | `IbonNo` |
| `6` (FamiPort) | `FamiNO` |
| `11` (銀聯) | 結帳頁授權即完成 |

### 銀行代碼 (`AtmBankNo`)

ATM 虛擬帳號的 `AtmBankNo` 為 3 碼財金代碼，常見：

| 代碼 | 銀行 |
|------|------|
| `004` | 臺灣銀行 |
| `005` | 土地銀行 |
| `007` | 第一銀行 |
| `008` | 華南銀行 |
| `009` | 彰化銀行 |
| `012` | 台北富邦 |
| `013` | 國泰世華 |
| `017` | 兆豐銀行 |
| `806` | 元大銀行 |
| `807` | 永豐銀行 |
| `808` | 玉山銀行 |
| `812` | 台新銀行 |
| `822` | 中國信託 |

> 速買配的 ATM 代收銀行由 `Rvg2c` 決定；發給消費者的虛擬帳號其銀行代碼會在 `AtmBankNo` 回傳。

---

## 常見問題排解

### 1. 取號回 `Status=-2` 帳號驗證失敗

**檢查**：
- `Dcvc` / `Rvg2c` / `Verify_key` 是否與後台核發一致
- 是否誤用測試 / 正式環境參數
- `Verify_key` 是否大寫 hex (32 碼)

### 2. 取號回 `Status=-10` Data_id 重複

**檢查**：
- 同一商店是否曾經以該 `Data_id` 成功取號
- 訂單編號產生器是否包含時間戳 + 隨機字串

```python
import secrets, time
order_id = f"ORD{int(time.time())}{secrets.token_hex(2).upper()}"  # 例如 ORD17150000001A2B
```

### 3. Roturl 收到通知，但 `Mid_smilepay` 對不上

**檢查**：
- `mid` 是否為「金流 mid」，不是「商店 Dcvc」
- `Amount` 是否從 `$_REQUEST` 帶入整數，沒有經過格式化
- `Smseid` 末 4 碼是否含字母 (需替換為 `9`)

### 4. 中文亂碼 (`Errdesc` / `Process_time` / `Address`)

**原因**：SmilePay 部分通知欄位以 BIG-5 編碼。

**處理**：

```python
def big5_to_utf8(text: str | bytes) -> str:
    if isinstance(text, str):
        text = text.encode("latin1", errors="ignore")
    return text.decode("big5", errors="ignore")
```

### 5. 信用卡通知 `Classif=A` 但 `Response_id != 1`

**原因**：授權失敗。

**處理**：將 `Errdesc` BIG-5 轉碼後寫入訂單備註，提示消費者重新下單或更換卡片。

### 6. 條碼 / ibon / FamiPort 已成功取號但顯示「失敗」

**檢查**：
- 是否誤把「**取號成功**」當成「**消費者已付款**」
- 取號回應 `Status=1` 只代表「**繳費單已開立**」，實際入帳要等 `Roturl` 通知

### 7. 信用卡結帳頁長時間沒跳轉回來

**原因**：消費者中斷流程 / 銀行 3D 驗證逾時。

**處理**：
- 給予「重新刷卡」按鈕，重新組 `mtmk_utf.asp` redirect
- 不要在前端顯示「付款成功」，必須等 `Roturl` 通知再標記完成

### 8. 已上線後，金額限制與後台設定不一致

**檢查**：
- WooCommerce 模組以「設定值」+「速買配規範」雙重限制
- 雙方擇嚴：例如商家設 50,000，但 ATM 後台僅 20,000，仍會被速買配端擋下

---

## 官方資源

- **官方網站**：https://www.smilepay.net/
- **金流系統**：https://www.smse.com.tw/
- **API 規格書**：商店後台「下載專區」(需登入)
- **客服電話**：(02) 8751-1898
- **技術窗口**：service@smilepay.com.tw

---

最後更新：2026/05/07
