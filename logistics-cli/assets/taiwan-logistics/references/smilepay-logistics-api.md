# SmilePay Logistics API Reference

速買配 (SmilePay) 物流 API 完整參考文件。

> **重要前置觀念**
> SmilePay 物流 API 與金流 API **共用同一個帳號** (`Dcvc` + `Verify_key`)。
> 你不會再看到「物流商代號」之類的東西 — SmilePay 是「金物流整合服務商」，
> 它在背後再串接 7-11、全家、黑貓 (TCAT) 等實際物流業者。
> 對開發者而言，所有物流產品都透過「**SmilePay 同一組 API + 不同的 `Pay_zg` / `Pay_subzg` 編碼**」
> 來路由。掌握這個矩陣是整合 SmilePay 物流的祖傳秘方。

---

## 目錄

1. [基本說明](#基本說明)
2. [環境資訊](#環境資訊)
3. [認證方式](#認證方式)
4. [API 端點總覽](#api-端點總覽)
5. [物流類型分類](#物流類型分類)
6. [Pay_zg / Pay_subzg 編碼矩陣](#pay_zg--pay_subzg-編碼矩陣)
7. [取得物流編號](#取得物流編號)
8. [電子地圖選店](#電子地圖選店)
9. [列印託運單](#列印託運單)
10. [通知與貨況](#通知與貨況)
11. [退貨流程](#退貨流程)
12. [錯誤代碼](#錯誤代碼)
13. [物流類型對照表](#物流類型對照表)
14. [常見問題排解](#常見問題排解)

---

## 基本說明

### 服務範圍

SmilePay 物流 API 支援 **三大物流體系，共 7 種物流產品**：

| 物流體系 | 子類型 | 說明 |
|---------|--------|------|
| 7-11 超商取貨 | C2C 店到店 | 個人/小商家取貨；走 7-11 交貨便系統 |
| 7-11 超商取貨 | B2C 大宗寄倉 | 商家大量寄倉；走大智通配送中心 |
| 全家 超商取貨 | C2C 店到店 | 個人/小商家取貨；走全家店到店系統 |
| 全家 超商取貨 | B2C 大宗寄倉 | 商家大量寄倉 (走全家專屬配送) |
| 黑貓宅急便 | 常溫 | TCAT 室溫宅配 |
| 黑貓宅急便 | 冷藏 | TCAT 0~7°C 冷藏宅配 |
| 黑貓宅急便 | 冷凍 | TCAT -18°C 冷凍宅配 |

### 整合方式

SmilePay 的物流 API 不是「一個物流業者一支 API」，而是**統一進入點 + 編碼分流**：

1. **取號階段**：所有物流產品都先打 `SPPayment.asp`，用 `Pay_zg` 編碼指定要走哪一條路線。
2. **後續操作**：依照取號回應拿到的 `SmilePayNO` (跟金流的同一個 ID)，搭配不同子端點處理。
3. **回呼通知**：所有物流貨況變更都會 POST 到商家設定的 `Logistics_Roturl`，由 `Shipstatus` 數值決定狀態。

### 資料格式

- 請求格式：`application/x-www-form-urlencoded` (POST)
- 回應格式：**XML**（注意：不是 JSON）
- 編碼：請求送出 UTF-8；某些貨況通知會以 BIG5 回傳 (建議偵測並轉碼)

---

## 環境資訊

### 測試環境

SmilePay 提供官方測試帳號，可直接用來打通流程：

```
Dcvc:        107
Rvg2c:       1
Verify_key:  174A02F97A95F72CE301137B3F98D128
Mid:         1111
```

### 正式環境

正式帳號需向 SmilePay 業務窗口申請，會發放：

| 欄位 | 說明 | 範例 |
|------|------|------|
| `Dcvc` | 商家代號 | `12345` |
| `Rvg2c` | 簽章驗證代碼 | `1` |
| `Verify_key` | 共享密鑰 (32 碼 HEX) | `XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX` |
| `Mid` | 商店 ID | `12345` |

> **注意**：`Dcvc` + `Verify_key` 與 SmilePay **金流 API 共用**。同一個 SmilePay 帳號，
> 同時管理金流交易與物流追蹤碼。

### API 主機

| 用途 | Hostname |
|------|----------|
| 全部物流 API | `ssl.smse.com.tw` |
| 電子地圖 (mtmk) | `ssl.smse.com.tw/ezpos/` |

所有端點皆為 HTTPS，唯一例外：`ezcatGetTrackNum.asp` 與 `C2BPayment.asp`
在原始程式碼中是 `http://`，但 `https://` 也可正常運作（建議統一用 HTTPS）。

---

## 認證方式

### 共享密鑰機制

SmilePay 物流 API **沒有計算 CheckMacValue 之類的簽章**，而是透過 `Dcvc` + `Verify_key`
作為「請求 + 帳號識別」雙重密碼。每個請求都必須夾帶這兩個欄位。

| 參數 | 必填 | 說明 |
|------|------|------|
| `Dcvc` | ● | 商家代號 |
| `Verify_key` | ● | 共享密鑰 |
| `Rvg2c` | △ | 部分端點需要（如 `SPPayment.asp`、退貨便、TCAT 列印） |

### PHP 範例

```php
<?php
$post_data = [
    'Dcvc'       => '107',
    'Verify_key' => '174A02F97A95F72CE301137B3F98D128',
    'Rvg2c'      => '1',
    // ... 其他物流參數
];

$body = http_build_query($post_data);
$response = wp_remote_post('https://ssl.smse.com.tw/api/SPPayment.asp', [
    'body' => $body,
]);
$xml = simplexml_load_string(wp_remote_retrieve_body($response));
```

### Python 範例

```python
import requests
import xml.etree.ElementTree as ET

post_data = {
    'Dcvc':       '107',
    'Verify_key': '174A02F97A95F72CE301137B3F98D128',
    'Rvg2c':      '1',
    # ... 其他物流參數
}

resp = requests.post(
    'https://ssl.smse.com.tw/api/SPPayment.asp',
    data=post_data,
    timeout=30,
)
root = ET.fromstring(resp.text)
status = root.findtext('Status')
```

### 安全建議

- `Verify_key` 屬於高敏感憑證，**絕不能**寫死在前端 / 提交到 git。
- 建議用 WordPress option / 環境變數 (`SMILEPAY_VERIFY_KEY`) 集中管理。
- 物流 API 與金流 API 共用密鑰，撤銷會同時影響兩邊 — 異常時聯絡 SmilePay 換鑰。

---

## API 端點總覽

所有端點 base URL 為：`https://ssl.smse.com.tw/api/`

### 取號 / 修改

| 端點 | 方法 | 用途 |
|------|------|------|
| `SPPayment.asp` | POST | **建立物流訂單（取得 SmilePayNO）**；CVS C2C / B2C / TCAT 全部都從這裡開始 |
| `SPPayment_Modify.asp` | POST | 修改 CVS 訂單（換取貨人 / 換門市） |

### 超商 (CVS) 後續流程

| 端點 | 方法 | 用途 |
|------|------|------|
| `C2CPayment.asp` | POST | C2C **取貨付款** 取交貨便號碼 |
| `C2CPaymentU.asp` | POST | C2C **純取貨（不付款）** 取交貨便號碼 |
| `B2CPayment.asp` | POST | B2C 大宗寄倉取交貨便號碼 |
| `B2C_MultiplePrint.asp` | GET | B2C 列印託運單（多單列印） |
| `C2BPayment.asp` | GET | C2B 退貨便列印 |
| `LogisticsEmap.asp` | GET | 電子地圖選店（C2C / B2C 共用） |

### 黑貓 (TCAT) 後續流程

| 端點 | 方法 | 用途 |
|------|------|------|
| `ezcatGetTrackNum.asp` | POST | 取得黑貓託運編號（TrackNum） |
| `ezcatPrintDelivery.asp` | GET | 列印黑貓託運單 |

### 電子地圖 / mtmk

| 端點 | 方法 | 用途 |
|------|------|------|
| `https://ssl.smse.com.tw/ezpos/mtmk_utf.asp` | GET | C2B 退貨便電子地圖（讓消費者選退貨門市） |

---

## 物流類型分類

SmilePay 物流可由「**寄送方式**」與「**金流方式**」兩個維度交叉。

### 寄送方式

| 寄送方式 | 說明 |
|----------|------|
| 7-11 C2C 店到店 | `typesserver = 711C2C` |
| 7-11 B2C 大宗寄倉 | `typesserver = 711B2C` |
| 全家 C2C 店到店 | `typesserver = FAMIC2C` |
| 全家 B2C 大宗寄倉 | `typesserver = FAMIB2C`（部分商家可選用） |
| 黑貓 常溫 | TCAT (溫層 `0001`) |
| 黑貓 冷藏 | TCAT (溫層 `0002`) |
| 黑貓 冷凍 | TCAT (溫層 `0003`) |

### 金流方式

| 金流方式 | 說明 | 影響 |
|----------|------|------|
| 取貨付款（COD） | 消費者取貨時付現給超商 / 黑貓 | 走 `_COD_PAY_ZG` 編碼 |
| 純取貨（PICKUP） | 消費者已預先付款，只需取貨 | 走 `_PICKUP_PAY_ZG` 編碼 |

### WooCommerce 程式中的物流方法 ID

```
WC_SmilePay_CVS_711       // 7-11 (C2C/B2C 由設定切換)
WC_SmilePay_CVS_FAMI      // 全家 (C2C only)
WC_SmilePay_TCAT_NORMAL   // 黑貓常溫
WC_SmilePay_TCAT_REFRIGE  // 黑貓冷藏
WC_SmilePay_TCAT_FREEZE   // 黑貓冷凍
```

---

## Pay_zg / Pay_subzg 編碼矩陣

> **這是 SmilePay 物流的祖傳秘方** — 所有物流產品都從同一支 `SPPayment.asp`
> 進入，靠 `Pay_zg`（主要分類）+ `Pay_subzg`（副分類）來路由到實際物流業者。

### Pay_zg（物流主分類）

| 常數名稱 | 值 | 用途 |
|----------|----|------|
| `C2C_COD_PAY_ZG` | `51` | 超商 C2C **取貨付款** |
| `C2C_PICKUP_PAY_ZG` | `52` | 超商 C2C **純取貨（不付款）** |
| `B2C_COD_PAY_ZG` | `55` | 超商 B2C **取貨付款** |
| `B2C_PICKUP_PAY_ZG` | `56` | 超商 B2C **純取貨** |
| `TCAT_COD_PAY_ZG` | `81` | 黑貓宅配 **取貨付款** |
| `TCAT_PICKUP_PAY_ZG` | `82` | 黑貓宅配 **純取貨** |
| `RETCAT_PAY_ZG` | `83` | 黑貓 **逆物流（退貨）** |
| `c2b_payzg` | (商家自訂) | C2B 退貨便（由商家後台設定，常見值依超商而異） |

### Pay_subzg（物流副分類）

| 常數名稱 | 值 | 用途 |
|----------|----|------|
| `_711_PAY_SUBZG` | `7NET` | 走 7-11 / 大智通系統（C2C 與 B2C 都用這個） |
| `FAMI_PAY_SUBZG` | `FAMI` | 走全家系統 |
| TCAT 固定值 | `TCAT` | 黑貓宅配（含逆物流） |

### 完整編碼對照表

| 寄送方式 | 金流方式 | `Pay_zg` | `Pay_subzg` |
|---------|---------|----------|-------------|
| 7-11 C2C 店到店 | 取貨付款 | `51` | `7NET` |
| 7-11 C2C 店到店 | 純取貨 | `52` | `7NET` |
| 7-11 B2C 大宗寄倉 | 取貨付款 | `55` | `7NET` |
| 7-11 B2C 大宗寄倉 | 純取貨 | `56` | `7NET` |
| 全家 C2C 店到店 | 取貨付款 | `51` | `FAMI` |
| 全家 C2C 店到店 | 純取貨 | `52` | `FAMI` |
| 全家 B2C 大宗寄倉 | 取貨付款 | `55` | `FAMI` |
| 全家 B2C 大宗寄倉 | 純取貨 | `56` | `FAMI` |
| 黑貓常溫 / 冷藏 / 冷凍 | 取貨付款 | `81` | `TCAT` |
| 黑貓常溫 / 冷藏 / 冷凍 | 純取貨 | `82` | `TCAT` |
| 黑貓逆物流（退貨） | — | `83` | `TCAT` |

**注意**：黑貓的「常溫 / 冷藏 / 冷凍」差異**不是**靠 `Pay_zg` 區分，
而是走第二支 API `ezcatGetTrackNum.asp` 時的 `temperature` 參數
（`0001` 常溫 / `0002` 冷藏 / `0003` 冷凍）。

### 路由邏輯（PHP 範例）

```php
// 根據使用者選擇的物流 + 金流，決定 Pay_zg / Pay_subzg
function determine_pay_codes(string $typesserver, string $payment_method): array {
    $is_cod = $payment_method === 'cod';

    // 7-11 與全家走同一組 Pay_zg，差別在 Pay_subzg
    switch ($typesserver) {
        case '711C2C':
            return [
                'pay_zg'    => $is_cod ? 51 : 52,  // C2C_COD or C2C_PICKUP
                'pay_subzg' => '7NET',
            ];
        case '711B2C':
            return [
                'pay_zg'    => $is_cod ? 55 : 56,  // B2C_COD or B2C_PICKUP
                'pay_subzg' => '7NET',
            ];
        case 'FAMIC2C':
            return [
                'pay_zg'    => $is_cod ? 51 : 52,
                'pay_subzg' => 'FAMI',
            ];
        case 'FAMIB2C':
            return [
                'pay_zg'    => $is_cod ? 55 : 56,
                'pay_subzg' => 'FAMI',
            ];
    }
    throw new InvalidArgumentException("Unknown typesserver: {$typesserver}");
}
```

---

## 取得物流編號

物流取號分為兩個階段：

1. **第一階段（共通）**：呼叫 `SPPayment.asp` 取得 `SmilePayNO`
2. **第二階段（依物流產品）**：用 `SmilePayNO` 換取實際的「交貨便號碼」或「TCAT 託運單號」

### 第一階段：取得 SmilePayNO

#### 端點

```
POST https://ssl.smse.com.tw/api/SPPayment.asp
```

#### 共通參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `Dcvc` | String | ● | 商家代號 |
| `Verify_key` | String(32) | ● | 共享密鑰 |
| `Rvg2c` | String | ● | 簽章驗證代碼 |
| `Pay_zg` | Integer | ● | 物流主分類（見上表） |
| `Pay_subzg` | String | ● | 物流副分類（`7NET` / `FAMI` / `TCAT`） |
| `Pur_name` | String | ● | 取貨人姓名 |
| `Tel_number` | String | ● | 取貨人電話 |
| `Mobile_number` | String | △ | 取貨人手機（建議與 Tel_number 同值） |
| `Email` | String | △ | 取貨人 Email |
| `Address` | String | △ | 取貨人地址（CVS 可省略，TCAT 必填） |
| `Data_id` | String | ● | 商家自訂訂單編號（必須唯一） |
| `od_sob` | String(35) / (45) | ● | 商品名稱（CVS 35 字 / TCAT 45 字內） |
| `Amount` | Integer | ● | 訂單總金額（取整） |
| `Logistics_store` | String | △ | CVS 必填，格式：`{store_id}/{store_name}/{store_address}` |
| `Roturl` | String(URL) | △ | 商家通用回傳網址 |
| `Logistics_Roturl` | String(URL) | ● | **物流貨況通知網址** |
| `Roturl_status` | String | △ | 回傳狀態識別碼（如 `woook1.1.23`） |
| `Remark` | String | △ | 備註（取自買家結帳備註） |

#### 回應（XML）

成功：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<SmilePay>
    <Status>1</Status>
    <Desc>交易成功</Desc>
    <SmilePayNO>1234567890</SmilePayNO>
    <Data_id>WC-1024</Data_id>
    <Amount>1500</Amount>
</SmilePay>
```

失敗：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<SmilePay>
    <Status>-2</Status>
    <Desc>驗證失敗</Desc>
</SmilePay>
```

判斷成功的鐵則：
- HTTP body 含 `<SmilePay>`
- `<Status>` 等於 `1`

### 第二階段：取得實際物流編號

依物流產品分為三條路徑：

#### A. 7-11 / 全家 C2C — 取交貨便號碼

```
POST https://ssl.smse.com.tw/api/C2CPayment.asp     # 取貨付款 (COD)
POST https://ssl.smse.com.tw/api/C2CPaymentU.asp    # 純取貨 (PICKUP)
```

| 參數 | 必填 | 說明 |
|------|------|------|
| `Dcvc` | ● | 商家代號 |
| `Verify_key` | ● | 共享密鑰 |
| `smseid` | ● | 第一階段拿到的 `SmilePayNO` |
| `Pay_subzg` | ● | `7NET` 或 `FAMI` |
| `types` | ● | `Xml` (取得 XML 回應) 或 `Web` (取得 HTML 列印頁網址) |

回應（`types=Xml`）：

```xml
<SmilePay>
    <Status>1</Status>
    <paymentno>AB12345</paymentno>
    <validationno>1234</validationno>
    <storeid>131386</storeid>
    <storename>雙子星門市</storename>
</SmilePay>
```

完整交貨便號碼 = `paymentno` + `validationno`（例：`AB123451234`）

#### B. 7-11 B2C — 取大宗寄倉編號

```
POST https://ssl.smse.com.tw/api/B2CPayment.asp
```

| 參數 | 必填 | 說明 |
|------|------|------|
| `Dcvc` | ● | 商家代號 |
| `Verify_key` | ● | 共享密鑰 |
| `smseid` | ● | 第一階段拿到的 `SmilePayNO` |

回應：

```xml
<SmilePay>
    <Status>1</Status>
    <EshopOrderNo>0987654321</EshopOrderNo>
    <Storeid>131386</Storeid>
    <StoreName>雙子星門市</StoreName>
</SmilePay>
```

7-11 B2C 完整查詢碼：`766` + `EshopOrderNo`

#### C. 黑貓 — 取託運單號

```
POST https://ssl.smse.com.tw/api/ezcatGetTrackNum.asp
```

| 參數 | 必填 | 說明 |
|------|------|------|
| `Dcvc` | ● | 商家代號 |
| `Verify_key` | ● | 共享密鑰 |
| `smseid` | ● | 第一階段拿到的 `SmilePayNO` |
| `package_size` | ● | 包裹尺寸（60/90/120/150 cm） |
| `temperature` | ● | 溫層：`0001` 常溫 / `0002` 冷藏 / `0003` 冷凍 |
| `delivery_date` | △ | 預定送達日 (`YYYY/MM/DD`) |
| `delivery_timezone` | △ | 預定送達時段（`1`/`2`/`4`） |
| `is_protect` | △ | 易碎品保護（`1` 啟用；`0` 不送出此參數） |
| `shipment_type` | △ | 出貨類型 |
| `receiver_address` | △ | 收件地址（逆物流時用） |

回應：

```xml
<SmilePay>
    <Status>1</Status>
    <TrackNum>900123456789</TrackNum>
    <Smseid>1234567890</Smseid>
    <Pur_name>王小明</Pur_name>
    <Tel_number>0912345678</Tel_number>
</SmilePay>
```

#### PHP 完整範例（C2C 取貨付款）

```php
<?php
// === 第一階段：取得 SmilePayNO ===
$post_data = [
    'Dcvc'             => '107',
    'Rvg2c'            => '1',
    'Verify_key'       => '174A02F97A95F72CE301137B3F98D128',
    'Pay_zg'           => 51,           // C2C COD
    'Pay_subzg'        => '7NET',       // 7-11
    'Pur_name'         => '王小明',
    'Tel_number'       => '0912345678',
    'Mobile_number'    => '0912345678',
    'Email'            => 'buyer@example.com',
    'Data_id'          => 'WC-' . time(),
    'od_sob'           => '商品A*1｜商品B*2',
    'Amount'           => 1500,
    'Logistics_store'  => '131386/雙子星門市/台北市信義區市府路1號',
    'Roturl'           => 'https://your-site.com/wc-api/roturl',
    'Logistics_Roturl' => 'https://your-site.com/wc-api/smilepay_cvs_logistic_status',
    'Roturl_status'    => 'woook1.1.23',
    'Remark'           => '請小心包裝',
];

$response = wp_remote_post(
    'https://ssl.smse.com.tw/api/SPPayment.asp',
    ['body' => http_build_query($post_data)]
);
$xml = simplexml_load_string(wp_remote_retrieve_body($response));

if ((string)$xml->Status !== '1') {
    throw new Exception("取號失敗：{$xml->Desc}");
}
$smilepay_no = (string)$xml->SmilePayNO;

// === 第二階段：取得交貨便號碼 ===
$post_data2 = [
    'Dcvc'       => '107',
    'Verify_key' => '174A02F97A95F72CE301137B3F98D128',
    'smseid'     => $smilepay_no,
    'Pay_subzg'  => '7NET',
    'types'      => 'Xml',
];
$response2 = wp_remote_post(
    'https://ssl.smse.com.tw/api/C2CPayment.asp',  // 取貨付款用 C2CPayment.asp
    ['body' => $post_data2]
);
$xml2 = simplexml_load_string(wp_remote_retrieve_body($response2));

$payment_no = (string)$xml2->paymentno . (string)$xml2->validationno;
echo "交貨便號碼：{$payment_no}";
```

#### Python 範例（黑貓常溫宅配）

```python
import requests
import xml.etree.ElementTree as ET

# === 第一階段 ===
post_data = {
    'Dcvc':             '107',
    'Rvg2c':            '1',
    'Verify_key':       '174A02F97A95F72CE301137B3F98D128',
    'Pay_zg':           81,        # TCAT COD
    'Pay_subzg':        'TCAT',
    'Pur_name':         '王小明',
    'Tel_number':       '0912345678',
    'Mobile_number':    '0912345678',
    'Email':            'buyer@example.com',
    'Address':          '台北市信義區市府路1號',
    'Data_id':          f'WC-{int(time.time())}',
    'od_sob':           '商品A*1｜商品B*2',
    'Amount':           1500,
    'Logistics_Roturl': 'https://your-site.com/wc-api/smilepay_tcat_logistic_status',
    'Roturl_status':    'woook1.1.23',
}

resp = requests.post('https://ssl.smse.com.tw/api/SPPayment.asp', data=post_data)
xml = ET.fromstring(resp.text)
assert xml.findtext('Status') == '1'
smilepay_no = xml.findtext('SmilePayNO')

# === 第二階段：取得 TCAT 託運單號 ===
post_data2 = {
    'Dcvc':              '107',
    'Verify_key':        '174A02F97A95F72CE301137B3F98D128',
    'smseid':            smilepay_no,
    'package_size':      '60',
    'temperature':       '0001',     # 0001=常溫
    'delivery_date':     '2026/05/15',
    'delivery_timezone': '3',        # 3=不限時
}
resp2 = requests.post('https://ssl.smse.com.tw/api/ezcatGetTrackNum.asp', data=post_data2)
xml2 = ET.fromstring(resp2.text)
track_num = xml2.findtext('TrackNum')
print(f'託運單號：{track_num}')
```

---

## 電子地圖選店

讓消費者在結帳階段選擇取貨門市。

### 端點

```
GET https://ssl.smse.com.tw/api/LogisticsEmap.asp
```

### 參數

| 參數 | 必填 | 說明 |
|------|------|------|
| `method` | ● | 固定 `GET` |
| `TypesServer` | ● | 物流伺服器類型 |
| `TypesInterface` | ● | `MOBILE` 或 `WEB` |
| `tempvar` | ● | 暫存參數（商家自訂的識別碼，會原樣回傳） |
| `url` | ● | 選店完成後 SmilePay 重導回去的網址 |

### TypesServer 對照

| 值 | 說明 |
|------|------|
| `711C2C` | 7-11 C2C 店到店 |
| `711B2C` | 7-11 B2C 大宗寄倉 |
| `FAMIC2C` | 全家 C2C 店到店 |
| `FAMIB2C` | 全家 B2C 大宗寄倉 |

### TypesInterface 對照

| 值 | 用途 |
|----|------|
| `MOBILE` | 手機介面 |
| `WEB` | 桌機介面 |

### 範例網址

```
https://ssl.smse.com.tw/api/LogisticsEmap.asp
    ?method=GET
    &TypesServer=711C2C
    &TypesInterface=MOBILE
    &tempvar=order_123
    &url=https%3A%2F%2Fyour-site.com%2Fwc-api%2Fsmilepay_save_emap
```

### 選店回呼參數

消費者選店完成後，SmilePay 會 POST/GET 以下欄位到 `url`：

| 參數 | 說明 |
|------|------|
| `tempvar` | 你送過去的暫存識別碼 |
| `Storeid` | 門市代號 |
| `Storename` | 門市名稱 |
| `StoreAddress` | 門市地址 |
| `TypesServer` | 物流類型（同送出） |

### PHP 範例（產生選店連結）

```php
<?php
function build_emap_url(string $typesserver, string $interface, string $tempvar, string $callback_url): string {
    $base = 'https://ssl.smse.com.tw/api/LogisticsEmap.asp';
    return sprintf(
        '%s?method=GET&TypesServer=%s&TypesInterface=%s&tempvar=%s&url=%s',
        $base,
        $typesserver,
        $interface,           // MOBILE / WEB
        urlencode($tempvar),
        urlencode($callback_url),
    );
}

// 例：開啟手機版的 7-11 C2C 電子地圖
$emap = build_emap_url(
    '711C2C',
    wp_is_mobile() ? 'MOBILE' : 'WEB',
    'order_' . get_current_user_id(),
    home_url('/wc-api/smilepay_save_emap')
);
header("Location: {$emap}");
exit;
```

---

## 列印託運單

### 7-11 / 全家 C2C 列印

C2C 不需要呼叫額外端點，**直接組成 GET URL** 開啟瀏覽器即可：

```php
$print_url = sprintf(
    'https://ssl.smse.com.tw/api/%s?%s',
    $is_cod ? 'C2CPayment.asp' : 'C2CPaymentU.asp',
    http_build_query([
        'Dcvc'       => $dcvc,
        'Verify_key' => $verify_key,
        'smseid'     => $smilepay_no,
        'Pay_subzg'  => $pay_subzg,
        'types'      => 'Web',  // ← 這個參數讓回應變 HTML 列印頁
    ])
);
// 開新分頁
echo "<a href='{$print_url}' target='_blank'>列印託運單</a>";
```

### 7-11 B2C 列印（多單合併）

```
GET https://ssl.smse.com.tw/api/B2C_MultiplePrint.asp
```

| 參數 | 必填 | 說明 |
|------|------|------|
| `Dcvc` | ● | 商家代號 |
| `Rvg2c` | ● | 固定 `1` |
| `Verify_key` | ● | 共享密鑰 |
| `PaperModel` | ● | 紙張規格（`1` = 標籤紙） |
| `smseid` | ● | SmilePayNO；多筆用 `,` 串接 |

```php
$url = 'https://ssl.smse.com.tw/api/B2C_MultiplePrint.asp?' . http_build_query([
    'Rvg2c'      => '1',
    'Dcvc'       => $dcvc,
    'Verify_key' => $verify_key,
    'PaperModel' => '1',
    'smseid'     => $smilepay_no,         // 或多筆 '111,222,333'
]);
```

### 黑貓列印託運單

```
GET https://ssl.smse.com.tw/api/ezcatPrintDelivery.asp
```

| 參數 | 必填 | 說明 |
|------|------|------|
| `Dcvc` | ● | 商家代號 |
| `Rvg2c` | ● | 簽章驗證代碼 |
| `Verify_key` | ● | 共享密鑰 |
| `Smseid` | ● | SmilePayNO（注意：是大寫 S） |
| `print_format` | ● | 列印格式（依後台設定，常見 `1`/`2`） |

```php
$url = 'https://ssl.smse.com.tw/api/ezcatPrintDelivery.asp?' . http_build_query([
    'Dcvc'         => $dcvc,
    'Rvg2c'        => $rvg2c,
    'Verify_key'   => $verify_key,
    'Smseid'       => $smilepay_no,
    'print_format' => '1',
]);
```

### C2B 退貨便列印

```
GET https://ssl.smse.com.tw/api/C2BPayment.asp
```

| 參數 | 必填 | 說明 |
|------|------|------|
| `Dcvc` | ● | 商家代號 |
| `Verify_key` | ● | 共享密鑰 |
| `smseid` | ● | C2B 取號回呼拿到的 Smseid |
| `types` | ● | `Web`（取得 HTML 列印頁） |

---

## 通知與貨況

物流貨況變更時，SmilePay 會 POST 到取號時提供的 `Logistics_Roturl`。
**CVS 與 TCAT 走不同的 webhook 處理邏輯**。

### CVS 貨況通知

#### 收到的欄位

| 參數 | 說明 |
|------|------|
| `Data_id` | 商家訂單編號（取號時送的 Data_id） |
| `Smseid` | SmilePay 物流追蹤碼 |
| `Shipstatus` | 貨況狀態碼（**整數**） |
| `Payment_no` | C2C：交貨便號碼 |
| `EshopOrderNo` | B2C：大宗寄倉編號 |
| `Storeid` | 門市代號 |
| `Storename` | 門市名稱 (可能 BIG5 編碼) |

#### Shipstatus 對照（C2C 7-11 / 全家）

| 代碼 | 中文意思 | 建議訂單狀態 |
|------|---------|-------------|
| `1` | 已出貨 | shipped |
| `2` | 已到達門市 | cvs-delivered |
| `3` | 消費者已取貨 | cvs-pickedup / completed |
| `4` | 消費者退貨 | cancelled |
| `5` | 已到退貨門市 | (不變更 WC 狀態) |
| `6` | 退貨已取貨 | (不變更 WC 狀態) |
| `7` | 退貨已至物流中心 | (不變更 WC 狀態) |

#### Shipstatus 對照（B2C — 7-11 大智通）

| 代碼 | 中文意思 | 建議訂單狀態 |
|------|---------|-------------|
| `1` | 大智通配送中 | shipped |
| `2` | 已到達門市 | cvs-delivered |
| `3` | 消費者已取貨 | completed |
| `4` | 消費者退貨 | cancelled |
| `5` | 已到退貨門市 | — |
| `6` | 退貨已取貨 | — |
| `7` | 退貨已至物流中心 | — |
| `11` | 已出貨（廠商出貨給大智通） | shipped |

#### 編碼處理（重要！）

CVS 通知中的 `Storename` 等中文欄位**可能以 BIG5 編碼回傳**。處理時必須偵測並轉碼：

```php
foreach ($_REQUEST as $key => $val) {
    if (mb_detect_encoding(urldecode($val), 'BIG5', true)) {
        $_REQUEST[$key] = mb_convert_encoding(urldecode($val), 'UTF-8', 'BIG5');
    }
}
```

#### 回應格式

不論成功失敗，必須以 HTTP 200 回應一段含 `<Roturlstatus>` 的 XML 片段：

```php
// 成功處理
echo '<Roturlstatus>woook1.1.23</Roturlstatus>';
// 找不到訂單
echo "<Roturlstatus>訂單編號:{$id} 速買配追蹤碼:{$smseid} 沒有對應的Order物件</Roturlstatus>";
```

`Roturl_status` 的字串需與取號時送出的 `Roturl_status` 相同（範例為 `woook1.1.23`）。

### TCAT 貨況通知

#### 收到的欄位

| 參數 | 說明 |
|------|------|
| `Data_id` | 商家訂單編號 |
| `Smseid` | SmilePay 物流追蹤碼 |
| `Shipstatus` | 主貨況狀態碼 |
| `DetailStatus` | 配送異常子狀態碼（如有，優先處理） |
| `Payment_no` | TCAT 託運單號 |

#### Shipstatus 對照（黑貓）

| 代碼 | 中文意思 | 建議訂單狀態 |
|------|---------|-------------|
| `1` | 配送中 | shipped |
| `3` | 已配達 | ezcat-delivered |
| `5` | 退貨中 | cancelled |
| `7` | 退完 | cancelled |
| `8` | 集貨失敗 | cancelled |

> 黑貓只回 `1/3/5/7/8` 這幾個狀態，沒有 `2/4/6`。

#### DetailStatus 異常代碼（節錄）

| 代碼 | 異常類型 |
|------|---------|
| `00002` | 不在家 |
| `00007` | 損壞 |
| `00008` | 公司行號休息 |
| `00009` | 地址不明 |
| `00010` | 搬家 |
| `00011` | 拒收 |
| `00014` | 遺失 |
| `00015` | 暫置營業所 |
| `00016` | BASE 列管 |
| `00021` | 超大 |
| `00022` | 超重 |
| `00023` | 地址錯誤 |
| `00025` | 航班延誤 |
| `00219` | 暫置營業所 |
| `001` | 自行寄回 |
| `002` | 不退了 |
| `003` | 尚未收到商品 |
| `004` | 另約取件時間 |
| `005` | 電話錯誤 |
| `006` | 電話空號 |
| `007` | 電話未接 |
| `008` | 電話關機 |
| `009` | 超大 |
| `010` | 人不在 |
| `011` | 已收走 |
| `014` | 商品送達時已拒收退回 |
| `015` | 地址有誤 |
| `017` | PCHOME 通知取消 |
| `024` | 其他 |
| `025` | 已集貨 |
| `999` | 訂單復原 |
| `P26` | 另約時間 |
| `P27` | 電聯不上 |
| `P28` | 資料有誤 |
| `P29` | 無件可退 |
| `P30` | 超大超重 |
| `P31` | 已回收 |
| `P32` | 別家收走 |
| `P33` | 商品未到 |

> **處理順序**：通知進來時先檢查 `DetailStatus`，**有值就優先記錄異常**，
> 然後直接回應 `<Roturlstatus>接收到配送異常XXX</Roturlstatus>` 結束 (不再處理 `Shipstatus`)。

#### 回應格式

```php
// 一般成功
echo '<Roturlstatus>woook1.1.23</Roturlstatus>';
// 異常回報
echo "<Roturlstatus>接收到配送異常{$detailstatus}</Roturlstatus>";
```

### 完整 PHP 通知處理範例

```php
<?php
function smilepay_cvs_logistic_status_handler() {
    $orderid = $_REQUEST['Data_id']  ?? null;
    $smseid  = $_REQUEST['Smseid']   ?? null;
    $order   = wc_get_order($orderid);

    if (!$order || $order->get_meta('_smilepay_logistic_info')['smseid'] !== $smseid) {
        wp_die("<Roturlstatus>訂單{$orderid}追蹤碼{$smseid}不存在</Roturlstatus>", '超商物流狀態', 200);
    }

    // BIG5 -> UTF-8
    $req = $_REQUEST;
    foreach ($req as $k => $v) {
        if (mb_detect_encoding(urldecode($v), 'BIG5', true)) {
            $req[$k] = mb_convert_encoding(urldecode($v), 'UTF-8', 'BIG5');
        }
    }

    $ship_status = (int)($req['Shipstatus'] ?? 0);
    $logistic_info = $order->get_meta('_smilepay_logistic_info');

    // C2C / B2C 走不同分支
    if (str_contains($logistic_info['cvs_service_type'], 'C2C')) {
        switch ($ship_status) {
            case 1: $order->update_status('shipped'); break;
            case 2: $order->update_status('cvs-delivered'); break;
            case 3: $order->update_status('cvs-pickedup'); break;
            case 4: $order->update_status('cancelled'); break;
        }
    } else {  // B2C
        switch ($ship_status) {
            case 1:
            case 11: $order->update_status('shipped'); break;
            case 2:  $order->update_status('cvs-delivered'); break;
            case 3:  $order->update_status('completed'); break;
            case 4:  $order->update_status('cancelled'); break;
        }
    }

    wp_die('<Roturlstatus>woook1.1.23</Roturlstatus>', '超商物流狀態', 200);
}
add_action('woocommerce_api_smilepay_cvs_logistic_status', 'smilepay_cvs_logistic_status_handler');
```

---

## 退貨流程

SmilePay 提供兩種退貨流程：**CVS C2B 退貨便** 與 **TCAT 逆物流**。

### CVS C2B 退貨便（消費者寄回到商家）

讓消費者透過超商把商品寄回給商家。

#### 流程

1. 商家後台對退貨訂單觸發 C2B 退貨便產生。
2. 系統開啟 SmilePay **mtmk 電子地圖頁**，讓消費者選一間退貨門市。
3. 選店完成後，SmilePay 會 POST 退貨便代碼到商家設定的 `MapRoturl`。
4. 商家可以再呼叫 `C2BPayment.asp?types=Web` 取得列印頁。

#### 端點

```
GET https://ssl.smse.com.tw/ezpos/mtmk_utf.asp
```

#### 參數

| 參數 | 必填 | 說明 |
|------|------|------|
| `Dcvc` | ● | 商家代號 |
| `Rvg2c` | ● | 簽章驗證代碼 |
| `Verify_key` | ● | 共享密鑰 |
| `Od_sob` | ● | 訂單編號（會原樣回傳） |
| `Pay_zg` | ● | C2B 退貨便用值（商家後台設定的 `c2b_payzg`，依超商不同） |
| `Pay_subzg` | ● | `7NET` 或 `FAMI` |
| `Data_id` | ● | 訂單編號 |
| `Amount` | ● | 退款金額 |
| `Pur_name` | ● | 退貨人姓名 |
| `Tel_number` | ● | 退貨人電話 |
| `Mobile_number` | △ | 手機 |
| `Email` | △ | Email |
| `Remark` | △ | 備註 |
| `MapRoturl` | ● | **選店完成後 SmilePay 回呼的網址** |
| `Logistics_Roturl` | ● | 物流貨況通知網址 |
| `Roturl_status` | △ | 回傳識別碼 |

#### MapRoturl 回呼欄位

| 參數 | 說明 |
|------|------|
| `Status` | `1` = 成功 |
| `Smseid` | SmilePay 退貨追蹤碼 |
| `Paymentno` | 退貨便代碼前段 |
| `Validationno` | 退貨便驗證碼 |
| `Data_id` | 訂單編號（原樣回傳） |

完整退貨便代碼 = `Paymentno` + `Validationno`

#### PHP 範例

```php
<?php
function trigger_c2b_return($order) {
    $logistic_info = $order->get_meta('_smilepay_logistic_info');

    $params = [
        'Dcvc'             => SMILEPAY_DCVC,
        'Rvg2c'            => SMILEPAY_RVG2C,
        'Verify_key'       => SMILEPAY_VERIFY_KEY,
        'Od_sob'           => $order->get_id(),
        'Pay_zg'           => SMILEPAY_C2B_PAYZG,           // 商家後台設定
        'Pay_subzg'        => $logistic_info['pay_subzg'],   // 7NET / FAMI
        'Data_id'          => $order->get_id(),
        'Amount'           => round($order->get_total()),
        'Pur_name'         => $order->get_billing_last_name() . $order->get_billing_first_name(),
        'Tel_number'       => $order->get_billing_phone(),
        'Mobile_number'    => $order->get_billing_phone(),
        'Email'            => $order->get_billing_email(),
        'Remark'           => $order->get_customer_note(),
        'MapRoturl'        => home_url('/wc-api/smilepay_save_c2b'),
        'Logistics_Roturl' => home_url('/wc-api/smilepay_cvs_logistic_status'),
        'Roturl_status'    => 'woook1.1.23',
    ];

    $url = 'https://ssl.smse.com.tw/ezpos/mtmk_utf.asp?' . http_build_query($params);
    // 在新分頁開啟讓消費者選店
    echo "<script>window.open('{$url}', '_blank')</script>";
}

// MapRoturl callback handler
function smilepay_save_c2b_handler() {
    if ($_REQUEST['Status'] != 1) wp_die('退貨便建立失敗');

    $order_id = $_REQUEST['Data_id'];
    $order = wc_get_order($order_id);

    $code = $_REQUEST['Paymentno'] . $_REQUEST['Validationno'];
    $order->add_order_note("退貨便代碼：{$code}", 1);

    // 開啟列印頁
    $print_url = 'https://ssl.smse.com.tw/api/C2BPayment.asp?' . http_build_query([
        'Dcvc'       => SMILEPAY_DCVC,
        'Verify_key' => SMILEPAY_VERIFY_KEY,
        'smseid'     => $_REQUEST['Smseid'],
        'types'      => 'Web',
    ]);
    wp_redirect($print_url);
    exit;
}
add_action('woocommerce_api_smilepay_save_c2b', 'smilepay_save_c2b_handler');
```

### TCAT 逆物流（黑貓到府收件後寄回）

讓黑貓到消費者府上收件，再寄回商家倉庫。

#### 流程（兩階段呼叫）

1. 第一階段：呼叫 `SPPayment.asp`，`Pay_zg = 83`、`Pay_subzg = TCAT`，取得退貨用 `SmilePayNO`。
2. 第二階段：拿這個 `SmilePayNO` 呼叫 `ezcatGetTrackNum.asp`，取得逆物流 `TrackNum`。

#### 第一階段參數（與正向取號類似）

```php
$post_data = [
    'Dcvc'             => $dcvc,
    'Rvg2c'            => $rvg2c,
    'Verify_key'       => $verify_key,
    'Od_sob'           => $order->get_id(),
    'Pay_zg'           => 83,                    // RETCAT_PAY_ZG
    'Pay_subzg'        => 'TCAT',
    'Data_id'          => $order->get_id(),
    'Address'          => $consumer_address,     // 消費者地址（要去取件的地方）
    'Amount'           => round($order->get_total()),
    'Pur_name'         => $consumer_name,
    'Tel_number'       => $consumer_phone,
    'Mobile_number'    => $consumer_phone,
    'Email'            => $order->get_billing_email(),
    'Remark'           => $order->get_customer_note(),
    'Logistics_Roturl' => home_url('/wc-api/smilepay_tcat_logistic_status'),
    'Roturl_status'    => 'woook1.1.23',
];
$response = wp_remote_post('https://ssl.smse.com.tw/api/SPPayment.asp', ['body' => http_build_query($post_data)]);
$xml = simplexml_load_string(wp_remote_retrieve_body($response));
$retcat_smseid = (string)$xml->SmilePayNO;
```

#### 第二階段：取得逆物流 TrackNum

| 參數 | 必填 | 說明 |
|------|------|------|
| `Dcvc` | ● | 商家代號 |
| `Verify_key` | ● | 共享密鑰 |
| `smseid` | ● | 第一階段拿到的退貨 SmilePayNO |
| `package_size` | ● | 包裹尺寸 |
| `temperature` | ● | 溫層（同正向：`0001`/`0002`/`0003`） |
| `delivery_date` | △ | 預定收件日 |
| `delivery_timezone` | △ | 預定收件時段 |
| `is_protect` | △ | 易碎品保護 |
| `shipment_type` | △ | 出貨類型 |
| `receiver_address` | ● | **收件地址**（這裡指商家的倉庫地址，黑貓送回去的目的地） |

#### 回應

```xml
<SmilePay>
    <Status>1</Status>
    <Smseid>1234567890</Smseid>
    <TrackNum>900987654321</TrackNum>
    <Pur_name>王小明</Pur_name>
    <Tel_number>0912345678</Tel_number>
</SmilePay>
```

---

## 錯誤代碼

### 共用 Status 代碼

| Status | 說明 | 處理方式 |
|--------|------|---------|
| `1` | 成功 | 正常處理 |
| `非 1` | 失敗（具體原因見 `<Desc>`） | 依 `Desc` 處理；常見錯誤見下表 |

### 常見失敗訊息（出現在 `<Desc>` 中）

| Desc | 意思 | 處理 |
|------|------|------|
| 驗證失敗 | `Dcvc` 或 `Verify_key` 錯誤 | 檢查憑證；測試 / 正式不要混用 |
| 必填欄位不完整 | 漏送必填欄位 | 比對請求參數表 |
| Pay_zg 錯誤 | `Pay_zg` 數值與 `Pay_subzg` 不匹配 | 檢查編碼矩陣表 |
| 訂單編號重複 | `Data_id` 已使用過 | 改用獨立的訂單號（建議 prefix + timestamp） |
| 商品名稱過長 | `od_sob` 超過字數上限 | CVS 截 35 字 / TCAT 截 45 字 |
| 金額異常 | `Amount` 超出商品金額限制 | 7-11 / 全家 C2C 最高 19,999；確認商家後台額度 |
| 該物流業者拒收 | 例如 7-11 不收冷凍 | 改用合適的物流產品 |

### 連線錯誤

WordPress / cURL 層級的錯誤（例如 `WP_Error`）：

```php
if (is_wp_error($response)) {
    $msg = $response->get_error_message();
    // 常見：cURL error 28: Operation timed out
    //       cURL error 6:  Could not resolve host
    error_log("SmilePay 物流連線失敗：{$msg}");
}
```

建議重試策略：
- 連線層失敗：可重試（最多 2 次，間隔 30 秒）
- `Status != 1` 且為驗證/參數類錯誤：**不要重試**，直接記錄並讓人工介入。

---

## 物流類型對照表

### 物流方法 ID 與超商代碼

| WC 物流方法 ID | 顯示名稱 | typesserver | store_type | API 入口 |
|---------------|---------|-------------|------------|---------|
| `WC_SmilePay_CVS_711` | 速買配 7-11 超商取貨 | `711C2C` 或 `711B2C` | `711` | `SPPayment.asp` |
| `WC_SmilePay_CVS_FAMI` | 速買配 全家超商取貨 | `FAMIC2C` | `FAMI` | `SPPayment.asp` |
| `WC_SmilePay_TCAT_NORMAL` | 速買配 黑貓常溫宅配 | — | `TCAT` | `SPPayment.asp` |
| `WC_SmilePay_TCAT_REFRIGE` | 速買配 黑貓冷藏宅配 | — | `TCAT` | `SPPayment.asp` |
| `WC_SmilePay_TCAT_FREEZE` | 速買配 黑貓冷凍宅配 | — | `TCAT` | `SPPayment.asp` |

### TCAT 溫層代碼

| WC 物流方法 | temperature | 溫度區間 |
|-------------|-------------|---------|
| `WC_SmilePay_TCAT_NORMAL` | `0001` | 常溫 |
| `WC_SmilePay_TCAT_REFRIGE` | `0002` | 冷藏 0~7°C |
| `WC_SmilePay_TCAT_FREEZE` | `0003` | 冷凍 -18°C |

### 包裹尺寸（TCAT）

| package_size | 尺寸 |
|--------------|------|
| `60` | 60cm |
| `90` | 90cm |
| `120` | 120cm |
| `150` | 150cm |

### 預定送達時段（TCAT）

| delivery_timezone | 時段 |
|-------------------|------|
| `1` | 13:00 前 |
| `2` | 14:00–18:00 |
| `4` | 不限時 |

### CVS 追蹤頁

| 物流類型 | 追蹤網址 |
|---------|---------|
| 7-11 (C2C / B2C) | `https://eservice.7-11.com.tw/E-Tracking/search.aspx` |
| 全家 (C2C) | `https://www.famiport.com.tw/Web_Famiport/page/process.aspx` |
| 黑貓 (TCAT) | `https://www.t-cat.com.tw/inquire/trace.aspx` |

### B2C 7-11 號碼前綴

7-11 B2C 大宗寄倉的查詢碼必須加上 **`766`** 前綴：

```
完整查詢碼 = '766' + EshopOrderNo
```

例：`EshopOrderNo = 0987654321` → 至 7-11 查詢頁輸入 `7660987654321`

---

## 常見問題排解

### Q1：取號時收到 `Status=-2`，但所有欄位都填了？

A：通常是 `Verify_key` 錯誤，或測試 / 正式環境憑證混用。
請確認 `Dcvc` 與 `Verify_key` 配對正確，以及 `testmode_enabled` 切換是否正確。

### Q2：`Pay_zg` 與 `Pay_subzg` 怎麼選錯了會怎樣？

A：常見錯誤情境：
- `Pay_zg=51` (C2C COD) + `Pay_subzg=TCAT` → 編碼矛盾，會回 `Pay_zg 錯誤` 或無聲失敗。
- `Pay_zg=81` (TCAT) + `Pay_subzg=7NET` → 同樣矛盾。
- 一律對著「Pay_zg / Pay_subzg 完整編碼對照表」核對，再送 API。

### Q3：超商取貨地圖選店後資料丟了？

A：檢查 `tempvar` 與 `url` 是否被 URL Encode。SmilePay 是用 GET 把所有資料附在
網址後面，未轉義的特殊字元（`#`、`&`）會截斷參數。請務必 `urlencode()` 包過。

### Q4：CVS 通知亂碼？

A：SmilePay 部分 CVS 通知欄位以 BIG5 編碼回傳（特別是 `Storename`）。
務必加入 BIG5 偵測 + 轉碼邏輯（見「通知與貨況」章節範例）。

### Q5：TCAT 取號成功但 `ezcatGetTrackNum` 失敗？

A：黑貓比超商更嚴格，常見原因：
- `Address` 不完整（少寫縣市），TCAT 會拒絕。
- `temperature` 與 `package_size` 組合違反黑貓規則（例如 150cm 冷凍）。
- `delivery_date` 過去或太遠（建議 T+1 ~ T+7 內）。

### Q6：通知端點要不要驗證簽章？

A：SmilePay 物流通知**不送簽章**，也沒有 IP 白名單可驗。
建議的防護方式：
1. 比對 `Smseid` 是否與訂單記錄的 `_smilepay_logistic_info[smseid]` 一致。
2. URL 帶 secret token (例如 `/wc-api/smilepay_cvs_logistic_status?token=xxx`)，
   server 端驗證 token。
3. 寫入 log 後，再定期對帳。

### Q7：物流訂單成立失敗，要怎麼處理？

A：建議流程（參考 plugin 中 `_sp_logistic_failed` 機制）：
1. 取號失敗時，把訂單狀態設成 `failed`。
2. 在感謝頁顯示「物流訂單成立失敗，請重新下單」。
3. 寫入 `wc-logger` 來源 `smilepay-logistic-info` 留下完整紀錄。
4. 視需要寄通知給商家。

### Q8：能不能只用「純取貨（不付款）」搭超商？

A：可以。`Pay_zg` 改用 `52` (C2C) 或 `56` (B2C) 即可，
WC 端記得**禁用「貨到付款」金流**避免重複扣款。
原始 plugin 用 `cvs_only_cod` filter 控制這個邏輯。

### Q9：B2C 大宗寄倉與 C2C 店到店有什麼差？

| 比較 | C2C 店到店 | B2C 大宗寄倉 |
|------|-----------|-------------|
| 取號 API | `C2CPayment(U).asp` | `B2CPayment.asp` |
| 列印 API | 自帶 (`types=Web`) | `B2C_MultiplePrint.asp` |
| 適合對象 | 個人 / 小批量出貨 | 商家大量出貨 |
| 號碼格式 | `paymentno` + `validationno` | `766` + `EshopOrderNo` |
| 可選店 | 7-11 / 全家 | 7-11（全家 B2C 較少見） |

### Q10：能否 B2C 與 C2C 同時開？

A：可以。`SmilePay_Logistic` plugin 的 `cvs_service_type` 設為 `B2C` 時，
全家 C2C 物流方法會被隱藏（`add_shipping_methods` 邏輯）。
若要兩種同時提供，需要把超商分散至不同的 WC Shipping Zone。

### Q11：黑貓「異常通知」要顯示給消費者嗎？

A：建議不要直接顯示。`DetailStatus` 中的 `00007 損壞`、`00014 遺失`
這類可能造成消費者恐慌。建議：
1. 寫入訂單 meta `_smilepay_logistic_info[logistic_status]`。
2. 商家後台先看到、人工聯絡確認後，再決定要不要更新前台。

### Q12：SmilePay 物流 API 與金流 API 的 `Dcvc` 真的一樣嗎？

A：**是**。原始 plugin 中物流設定有獨立的 `smilepay_logistic_dcvc` option，
但「正式環境」實際使用的就是同一組 SmilePay 帳號。
只是物流端與金流端可能有獨立的「服務權限」（例如某些帳號只開金流不開物流），
申請時要確認兩邊都有開通。

### Q13：取號時 `Logistics_store` 該怎麼填？

A：CVS 必填，格式為 `{store_id}/{store_name}/{store_address}`。
例如：`131386/雙子星門市/台北市信義區市府路1號`。
這份資料來自電子地圖選店的回呼，記得用 `/` 連接，不要用空白。

### Q14：訂單金額有上下限嗎？

A：依物流類型有所不同（plugin 預設值參考）：
- 7-11 / 全家 C2C：13 ~ 19,999 元
- 7-11 B2C：依與大智通的合約
- 黑貓宅配：無硬性上限，但超過一定金額需事先告知 SmilePay

### Q15：能否事先用測試帳號（107 / 1111）跑全流程？

A：可以打 API 取號（會回正常的 `<SmilePay>` XML），
但**實際物流不會執行**。建議的測試方法：
1. 用測試帳號驗 API 流程、回呼處理、訂單狀態切換邏輯。
2. 換正式帳號後，先以小額（10 元）真實下單一筆，驗證號碼可在超商查到。

---

## 官方資源

- **官方網站**：https://www.smilepay.net/
- **物流文件**：請向 SmilePay 業務窗口索取最新版 PDF（不公開於官網）
- **技術客服**：customerservice@smilepay.net
- **服務電話**：(07)559-1828

---

最後更新：2026/05/07
