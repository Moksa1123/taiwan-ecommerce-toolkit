# PayUni Payment API Reference

統一金流 (PAYUNi) 金流 API 完整參考文件。

---

## 目錄

1. [API 端點總覽](#api-端點總覽)
2. [測試環境](#測試環境)
3. [加密機制](#加密機制)
4. [通用參數](#通用參數)
5. [整合式支付頁 (UPP)](#整合式支付頁-upp)
6. [信用卡幕後](#信用卡幕後)
7. [ATM 虛擬帳號](#atm-虛擬帳號)
8. [超商代碼](#超商代碼)
9. [LINE Pay](#line-pay)
10. [AFTEE 先享後付](#aftee-先享後付)
11. [Apple Pay / Google Pay / Samsung Pay](#apple-pay--google-pay--samsung-pay)
12. [愛金卡 iCash](#愛金卡-icash)
13. [交易查詢](#交易查詢)
14. [交易請退款](#交易請退款)
15. [交易取消授權](#交易取消授權)
16. [信用卡約定 (Token)](#信用卡約定-token)
17. [付款結果通知](#付款結果通知)
18. [錯誤碼對照表](#錯誤碼對照表)
19. [常見問題排解](#常見問題排解)

---

## API 端點總覽

### 基礎 API 路徑

| 環境 | 基礎路徑 |
|------|----------|
| **測試環境** | `https://sandbox-api.payuni.com.tw/api/` |
| **正式環境** | `https://api.payuni.com.tw/api/` |

### 支付相關端點

| 功能 | 端點路徑 | 說明 |
|------|----------|------|
| 整合式支付頁 | `/upp` | 導向 PayUni 支付頁面 |
| ATM 虛擬帳號 | `/atm` | 幕後取得虛擬帳號 |
| 超商代碼 | `/cvs` | 幕後取得繳費代碼 |
| 信用卡幕後 | `/credit` | 信用卡直接扣款 |
| LINE Pay | `/linepay` | LINE Pay 支付 |
| AFTEE 先享後付 | `/aftee_direct` | AFTEE 支付 |

### 交易管理端點

| 功能 | 端點路徑 | 說明 |
|------|----------|------|
| 交易查詢 | `/trade_query` | 查詢交易狀態 |
| 請退款 | `/trade_close` | 信用卡請款/退款 |
| 取消授權 | `/trade_cancel` | 取消信用卡授權 |
| CVS 取消 | `/cancel_cvs` | 取消超商代碼 |

### 信用卡約定 (Token) 端點

| 功能 | 端點路徑 | 說明 |
|------|----------|------|
| Token 查詢 | `/credit_bind_query` | 查詢約定信用卡 |
| Token 取消 | `/credit_bind_cancel` | 取消約定信用卡 |

### 特殊退款端點

| 功能 | 端點路徑 | 說明 |
|------|----------|------|
| 愛金卡退款 | `/trade_refund_icash` | iCash 退款 |
| AFTEE 退款 | `/trade_refund_aftee` | AFTEE 退款 |
| AFTEE 確認 | `/trade_confirm_aftee` | AFTEE 確認交易 |
| LINE Pay 退款 | `/trade_refund_linepay` | LINE Pay 退款 |

---

## 測試環境

### 測試帳號

測試帳號請至 PayUni 後台申請：

```
後台網址: https://www.payuni.com.tw/
路徑: 會員 > 商店清單 > 指定商店名稱 > 串接設定
```

取得以下資訊：
- **商店代號 (MerID)**
- **Hash Key**
- **Hash IV**

### 測試信用卡

| 卡號 | 說明 |
|------|------|
| `4000-2211-1111-1111` | 測試用信用卡 |

- **有效期限**: 任意未過期日期
- **CVV/CVC**: 任意 3 碼

### 測試環境端點

```
https://sandbox-api.payuni.com.tw/api/{endpoint}
```

---

## 加密機制

PayUni 採用 **AES-256-GCM** 加密與 **SHA256 HMAC** 驗證。

### 加密流程

1. **準備參數** - 組合所有請求參數
2. **URL Encode** - 將參數轉為 Query String
3. **AES-256-GCM 加密** - 使用 Hash Key 和 Hash IV 加密
4. **產生 HashInfo** - 使用 SHA256 計算驗證碼
5. **發送請求** - 將加密資料 POST 至 API

### PHP 加密範例

```php
<?php

class PayuniEncryption
{
    private string $merKey;
    private string $merIV;

    public function __construct(string $merKey, string $merIV)
    {
        $this->merKey = $merKey;
        $this->merIV = $merIV;
    }

    /**
     * AES-256-GCM 加密
     */
    public function encrypt(array $params): string
    {
        // 1. 組合 Query String
        $queryString = http_build_query($params);

        // 2. AES-256-GCM 加密
        $tag = '';
        $encrypted = openssl_encrypt(
            $queryString,
            'aes-256-gcm',
            $this->merKey,
            OPENSSL_RAW_DATA,
            $this->merIV,
            $tag,
            '',
            16
        );

        // 3. 組合加密結果 (加密資料 + tag)
        $encryptInfo = bin2hex($encrypted . $tag);

        return $encryptInfo;
    }

    /**
     * AES-256-GCM 解密
     */
    public function decrypt(string $encryptInfo): array
    {
        // 1. Hex 轉 Binary
        $data = hex2bin($encryptInfo);

        // 2. 分離加密資料和 tag
        $encrypted = substr($data, 0, -16);
        $tag = substr($data, -16);

        // 3. AES-256-GCM 解密
        $decrypted = openssl_decrypt(
            $encrypted,
            'aes-256-gcm',
            $this->merKey,
            OPENSSL_RAW_DATA,
            $this->merIV,
            $tag
        );

        // 4. 解析 Query String
        parse_str($decrypted, $result);

        return $result;
    }

    /**
     * 產生 HashInfo (SHA256)
     */
    public function hashInfo(string $encryptInfo): string
    {
        $raw = $encryptInfo . $this->merKey . $this->merIV;
        return strtoupper(hash('sha256', $raw));
    }
}
```

### Python 加密範例

```python
"""PayUni AES-256-GCM 加密"""

from Crypto.Cipher import AES
from urllib.parse import urlencode, parse_qs
import hashlib


class PayuniEncryption:
    def __init__(self, mer_key: str, mer_iv: str):
        self.mer_key = mer_key.encode('utf-8')
        self.mer_iv = mer_iv.encode('utf-8')

    def encrypt(self, params: dict) -> str:
        """AES-256-GCM 加密"""
        # 1. 組合 Query String
        query_string = urlencode(params)

        # 2. AES-256-GCM 加密
        cipher = AES.new(self.mer_key, AES.MODE_GCM, nonce=self.mer_iv)
        encrypted, tag = cipher.encrypt_and_digest(query_string.encode('utf-8'))

        # 3. 組合加密結果
        encrypt_info = (encrypted + tag).hex()

        return encrypt_info

    def decrypt(self, encrypt_info: str) -> dict:
        """AES-256-GCM 解密"""
        # 1. Hex 轉 Binary
        data = bytes.fromhex(encrypt_info)

        # 2. 分離加密資料和 tag
        encrypted = data[:-16]
        tag = data[-16:]

        # 3. AES-256-GCM 解密
        cipher = AES.new(self.mer_key, AES.MODE_GCM, nonce=self.mer_iv)
        decrypted = cipher.decrypt_and_verify(encrypted, tag)

        # 4. 解析 Query String
        result = dict(parse_qs(decrypted.decode('utf-8')))
        return {k: v[0] for k, v in result.items()}

    def hash_info(self, encrypt_info: str) -> str:
        """產生 HashInfo (SHA256)"""
        raw = encrypt_info + self.mer_key.decode() + self.mer_iv.decode()
        return hashlib.sha256(raw.encode('utf-8')).hexdigest().upper()
```

---

## 通用參數

### 請求參數

所有 API 請求都需要以下參數：

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `MerID` | String | ● | 商店代號 |
| `Version` | String | 否 | API 版本，預設 `1.0` (LINE Pay 預設 `1.1`) |
| `EncryptInfo` | String | ● | AES-256-GCM 加密後的參數 |
| `HashInfo` | String | ● | SHA256 驗證碼 |

### EncryptInfo 內容參數

以下參數需加密放入 `EncryptInfo`：

| 參數 | 類型 | 長度 | 必填 | 說明 |
|------|------|------|------|------|
| `MerID` | String | 20 | ● | 商店代號 |
| `MerTradeNo` | String | 50 | ● | 商店訂單編號，需唯一 |
| `TradeAmt` | Integer | - | ● | 交易金額 (整數) |
| `Timestamp` | Integer | - | ● | Unix 時間戳 |
| `ProdDesc` | String | 100 | 否 | 商品描述 |
| `UsrMail` | String | 100 | 否 | 消費者 Email |
| `ReturnURL` | String | 500 | 否 | 前台返回網址 |
| `NotifyURL` | String | 500 | 否 | 背景通知網址 |
| `Lang` | String | 5 | 否 | 語系 `zh-tw` / `en` |

### API 回應格式

```json
{
  "Status": "SUCCESS",
  "Message": "成功",
  "EncryptInfo": "加密後的回應資料",
  "HashInfo": "SHA256 驗證碼"
}
```

### Status 狀態碼

| 狀態 | 說明 |
|------|------|
| `SUCCESS` | 成功 |
| `ERROR` | 失敗 |

---

## 整合式支付頁 (UPP)

導向 PayUni 整合式支付頁面，消費者可選擇付款方式。

### 端點

```
POST /api/upp
```

### EncryptInfo 參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `MerID` | String | ● | 商店代號 |
| `MerTradeNo` | String | ● | 訂單編號 |
| `TradeAmt` | Integer | ● | 交易金額 |
| `Timestamp` | Integer | ● | Unix 時間戳 |
| `ExpireDate` | Integer | 否 | 繳費期限 (天)，`1`~`180`，預設 `7` |
| `ProdDesc` | String | 否 | 商品描述 |
| `UsrMail` | String | 否 | 消費者 Email |
| `ReturnURL` | String | 否 | 前台返回網址 |
| `NotifyURL` | String | 否 | 背景通知網址 |
| `Lang` | String | 否 | 語系 `zh-tw` / `en` |

### 支援的付款方式

整合式支付頁可顯示以下付款方式 (依商店設定)：

- 信用卡 (一次付清、分期、紅利折抵)
- ATM 虛擬帳號
- 超商代碼
- Apple Pay
- Google Pay
- Samsung Pay
- LINE Pay
- AFTEE 先享後付
- 愛金卡 iCash

### PHP 範例

```php
<?php

$encryption = new PayuniEncryption($merKey, $merIV);

$params = [
    'MerID' => 'YOUR_MER_ID',
    'MerTradeNo' => 'ORDER' . time(),
    'TradeAmt' => 1000,
    'Timestamp' => time(),
    'ProdDesc' => '測試商品',
    'ReturnURL' => 'https://your-site.com/return',
    'NotifyURL' => 'https://your-site.com/notify',
];

$encryptInfo = $encryption->encrypt($params);
$hashInfo = $encryption->hashInfo($encryptInfo);

// 產生表單
$html = <<<HTML
<form method="post" action="https://api.payuni.com.tw/api/upp">
    <input type="hidden" name="MerID" value="{$params['MerID']}">
    <input type="hidden" name="Version" value="1.0">
    <input type="hidden" name="EncryptInfo" value="{$encryptInfo}">
    <input type="hidden" name="HashInfo" value="{$hashInfo}">
    <button type="submit">前往付款</button>
</form>
HTML;

echo $html;
```

---

## 信用卡幕後

直接在商店頁面完成信用卡扣款，不需導向 PayUni。

### 端點

```
POST /api/credit
```

### EncryptInfo 參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `MerID` | String | ● | 商店代號 |
| `MerTradeNo` | String | ● | 訂單編號 |
| `TradeAmt` | Integer | ● | 交易金額 |
| `Timestamp` | Integer | ● | Unix 時間戳 |
| `CardNo` | String | ● | 信用卡號 (16 碼) |
| `CardExpiry` | String | ● | 有效期限 `MMYY` |
| `CardCVC` | String | ● | 安全碼 (3 碼) |
| `ProdDesc` | String | 否 | 商品描述 |
| `UsrMail` | String | 否 | 消費者 Email |
| `NotifyURL` | String | 否 | 背景通知網址 |

### 分期付款參數

| 參數 | 類型 | 說明 |
|------|------|------|
| `Inst` | Integer | 分期期數 `3`, `6`, `12`, `18`, `24`, `30` |

### 紅利折抵參數

| 參數 | 類型 | 說明 |
|------|------|------|
| `Red` | String | 啟用紅利折抵 `Y` |

### 銀聯卡參數

| 參數 | 類型 | 說明 |
|------|------|------|
| `UnionPay` | Integer | `1`:使用銀聯 |

### 信用卡約定 (Token) 參數

| 參數 | 類型 | 說明 |
|------|------|------|
| `UseTokenType` | Integer | `1`:建立 Token `2`:使用既有 Token |
| `BindVal` | String | Token 代碼 (UseTokenType=2 時必填) |

---

## ATM 虛擬帳號

取得 ATM 繳費虛擬帳號。

### 端點

```
POST /api/atm
```

### EncryptInfo 參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `MerID` | String | ● | 商店代號 |
| `MerTradeNo` | String | ● | 訂單編號 |
| `TradeAmt` | Integer | ● | 交易金額 |
| `Timestamp` | Integer | ● | Unix 時間戳 |
| `ExpireDate` | Integer | 否 | 繳費期限 (天)，`1`~`60`，預設 `3` |
| `BankType` | String | 否 | 指定銀行 (參見下表) |
| `NotifyURL` | String | 否 | 背景通知網址 |

### BankType 銀行代碼

| 代碼 | 銀行 |
|------|------|
| `FIRST` | 第一銀行 |
| `ESUN` | 玉山銀行 |
| `TAISHIN` | 台新銀行 |
| `CATHAY` | 國泰世華 |
| `CHINATRUST` | 中國信託 |

### 回應參數 (解密後)

| 參數 | 說明 |
|------|------|
| `TradeNo` | PayUni 交易編號 |
| `BankCode` | 銀行代碼 (3 碼) |
| `vAccount` | 虛擬帳號 (14~16 碼) |
| `ExpireDate` | 繳費期限 `yyyy/MM/dd` |

---

## 超商代碼

取得超商繳費代碼。

### 端點

```
POST /api/cvs
```

### EncryptInfo 參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `MerID` | String | ● | 商店代號 |
| `MerTradeNo` | String | ● | 訂單編號 |
| `TradeAmt` | Integer | ● | 交易金額 (`30`~`20000`) |
| `Timestamp` | Integer | ● | Unix 時間戳 |
| `ExpireDate` | Integer | 否 | 繳費期限 (天)，預設 `7` |
| `NotifyURL` | String | 否 | 背景通知網址 |

### 金額限制

| 項目 | 限制 |
|------|------|
| 最低金額 | 30 元 |
| 最高金額 | 20,000 元 |

### 回應參數 (解密後)

| 參數 | 說明 |
|------|------|
| `TradeNo` | PayUni 交易編號 |
| `PayNo` | 繳費代碼 |
| `ExpireDate` | 繳費期限 |

---

## LINE Pay

LINE Pay 支付整合。

### 端點

```
POST /api/linepay
```

### 版本

```
Version: 1.1
```

### EncryptInfo 參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `MerID` | String | ● | 商店代號 |
| `MerTradeNo` | String | ● | 訂單編號 |
| `TradeAmt` | Integer | ● | 交易金額 |
| `Timestamp` | Integer | ● | Unix 時間戳 |
| `ProdDesc` | String | ● | 商品描述 |
| `ReturnURL` | String | ● | 付款完成返回網址 |
| `NotifyURL` | String | 否 | 背景通知網址 |

### LINE Pay 退款

#### 端點

```
POST /api/trade_refund_linepay
```

#### EncryptInfo 參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `MerID` | String | ● | 商店代號 |
| `TradeNo` | String | ● | PayUni 交易編號 |
| `TradeAmt` | Integer | ● | 退款金額 |
| `Timestamp` | Integer | ● | Unix 時間戳 |

---

## AFTEE 先享後付

AFTEE 後支付整合。

### 端點

```
POST /api/aftee_direct
```

### EncryptInfo 參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `MerID` | String | ● | 商店代號 |
| `MerTradeNo` | String | ● | 訂單編號 |
| `TradeAmt` | Integer | ● | 交易金額 |
| `Timestamp` | Integer | ● | Unix 時間戳 |
| `ProdDesc` | String | ● | 商品描述 |
| `UsrMail` | String | ● | 消費者 Email |
| `UsrName` | String | ● | 消費者姓名 |
| `UsrPhone` | String | ● | 消費者手機 |
| `ReturnURL` | String | ● | 付款完成返回網址 |
| `NotifyURL` | String | 否 | 背景通知網址 |

### AFTEE 確認交易

當 AFTEE 交易需要確認時：

```
POST /api/trade_confirm_aftee
```

### AFTEE 退款

```
POST /api/trade_refund_aftee
```

---

## Apple Pay / Google Pay / Samsung Pay

行動支付整合 (需透過整合式支付頁或前端 SDK)。

### 支援說明

| 支付方式 | 說明 |
|----------|------|
| Apple Pay | Safari 瀏覽器、iOS/macOS 裝置 |
| Google Pay | Chrome 瀏覽器、Android 裝置 |
| Samsung Pay | Samsung 裝置 |

### 使用方式

透過整合式支付頁 (UPP) 使用，商店需向 PayUni 申請開通。

---

## 愛金卡 iCash

愛金卡 (iCash) 支付。

### 退款端點

```
POST /api/trade_refund_icash
```

### EncryptInfo 參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `MerID` | String | ● | 商店代號 |
| `TradeNo` | String | ● | PayUni 交易編號 |
| `TradeAmt` | Integer | ● | 退款金額 |
| `Timestamp` | Integer | ● | Unix 時間戳 |

---

## 交易查詢

查詢交易狀態。

### 端點

```
POST /api/trade_query
```

### EncryptInfo 參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `MerID` | String | ● | 商店代號 |
| `MerTradeNo` | String | ● | 商店訂單編號 |
| `Timestamp` | Integer | ● | Unix 時間戳 |

### 回應參數 (解密後)

| 參數 | 說明 |
|------|------|
| `TradeNo` | PayUni 交易編號 |
| `MerTradeNo` | 商店訂單編號 |
| `TradeAmt` | 交易金額 |
| `TradeStatus` | 交易狀態 |
| `PaymentType` | 付款方式 |
| `CreateTime` | 訂單建立時間 |
| `PayTime` | 付款時間 |

### TradeStatus 交易狀態

| 狀態 | 說明 |
|------|------|
| `0` | 未付款 / 處理中 |
| `1` | 已付款 |
| `2` | 付款失敗 |
| `3` | 已退款 |

### PHP 範例

```php
<?php

$encryption = new PayuniEncryption($merKey, $merIV);

$params = [
    'MerID' => 'YOUR_MER_ID',
    'MerTradeNo' => 'ORDER1234567890',
    'Timestamp' => time(),
];

$encryptInfo = $encryption->encrypt($params);
$hashInfo = $encryption->hashInfo($encryptInfo);

$response = file_get_contents('https://api.payuni.com.tw/api/trade_query', false, stream_context_create([
    'http' => [
        'method' => 'POST',
        'header' => 'Content-Type: application/x-www-form-urlencoded',
        'content' => http_build_query([
            'MerID' => $params['MerID'],
            'Version' => '1.0',
            'EncryptInfo' => $encryptInfo,
            'HashInfo' => $hashInfo,
        ]),
    ],
]));

$result = json_decode($response, true);

if ($result['Status'] === 'SUCCESS') {
    $data = $encryption->decrypt($result['EncryptInfo']);
    print_r($data);
}
```

---

## 交易請退款

信用卡請款或退款。

### 端點

```
POST /api/trade_close
```

### EncryptInfo 參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `MerID` | String | ● | 商店代號 |
| `TradeNo` | String | ● | PayUni 交易編號 |
| `CloseType` | Integer | ● | 操作類型 |
| `CloseAmt` | Integer | 否 | 請退款金額 (部分退款時使用) |
| `Timestamp` | Integer | ● | Unix 時間戳 |

### CloseType 操作類型

| 代碼 | 說明 |
|------|------|
| `1` | 請款 (Capture) |
| `2` | 退款 (Refund) |

### 退款限制

- 支援部分退款
- 退款金額需小於等於原交易金額
- 信用卡退款期限：請款後 1 年內

---

## 交易取消授權

取消信用卡授權 (尚未請款)。

### 端點

```
POST /api/trade_cancel
```

### EncryptInfo 參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `MerID` | String | ● | 商店代號 |
| `TradeNo` | String | ● | PayUni 交易編號 |
| `Timestamp` | Integer | ● | Unix 時間戳 |

---

## 信用卡約定 (Token)

### 查詢約定信用卡

#### 端點

```
POST /api/credit_bind_query
```

#### EncryptInfo 參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `MerID` | String | ● | 商店代號 |
| `BindVal` | String | ● | Token 代碼 |
| `Timestamp` | Integer | ● | Unix 時間戳 |

### 取消約定信用卡

#### 端點

```
POST /api/credit_bind_cancel
```

#### EncryptInfo 參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `MerID` | String | ● | 商店代號 |
| `BindVal` | String | ● | Token 代碼 |
| `Timestamp` | Integer | ● | Unix 時間戳 |

---

## 付款結果通知

### 通知流程

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   消費者    │────▶│   PayUni    │────▶│    商店     │
│   付款     │     │    處理     │     │ NotifyURL  │
└─────────────┘     └─────────────┘     └─────────────┘
                          │
                          │ POST (加密資料)
                          ▼
                    ┌─────────────┐
                    │    商店     │
                    │  解密處理   │
                    └─────────────┘
                          │
                          │ 回應 "SUCCESS"
                          ▼
                    ┌─────────────┐
                    │   PayUni    │
                    │  確認收到   │
                    └─────────────┘
```

### 通知參數

PayUni 會 POST 加密資料到 `NotifyURL`：

| 參數 | 說明 |
|------|------|
| `MerID` | 商店代號 |
| `EncryptInfo` | 加密的交易結果 |
| `HashInfo` | SHA256 驗證碼 |

### 解密後的通知內容

| 參數 | 說明 |
|------|------|
| `MerID` | 商店代號 |
| `MerTradeNo` | 商店訂單編號 |
| `TradeNo` | PayUni 交易編號 |
| `TradeAmt` | 交易金額 |
| `TradeStatus` | 交易狀態 (`0`:處理中 `1`:成功) |
| `PaymentType` | 付款方式 |
| `CreateTime` | 訂單建立時間 |
| `PayTime` | 付款時間 |
| `Message` | 交易訊息 |
| `Card4No` | 信用卡末四碼 (信用卡交易) |
| `AuthCode` | 銀行授權碼 (信用卡交易) |

### 處理範例

```php
<?php

// 接收通知
$encryptInfo = $_POST['EncryptInfo'] ?? '';
$hashInfo = $_POST['HashInfo'] ?? '';
$merID = $_POST['MerID'] ?? '';

// 驗證 HashInfo
$encryption = new PayuniEncryption($merKey, $merIV);
$calculatedHash = $encryption->hashInfo($encryptInfo);

if ($hashInfo !== $calculatedHash) {
    echo 'HashInfo Error';
    exit;
}

// 解密
$data = $encryption->decrypt($encryptInfo);

// 檢查交易狀態
if ($data['TradeStatus'] === '1') {
    // 交易成功，更新訂單狀態
    updateOrderStatus($data['MerTradeNo'], 'paid', $data);
}

// 回應 SUCCESS
echo 'SUCCESS';
```

---

## 錯誤碼對照表

### 交易狀態 (TradeStatus)

| 狀態 | 說明 |
|------|------|
| `0` | 未付款 / 處理中 |
| `1` | 已付款 / 成功 |
| `2` | 付款失敗 |
| `3` | 已退款 |

### 常見錯誤訊息

| 錯誤碼 | 說明 | 處理方式 |
|--------|------|----------|
| `參數錯誤` | 必填參數缺失或格式錯誤 | 檢查參數格式 |
| `商店代號錯誤` | MerID 不存在 | 確認商店代號 |
| `訂單編號重複` | MerTradeNo 已使用 | 使用新的訂單編號 |
| `HashInfo 驗證失敗` | 加密資料不正確 | 重新計算 HashInfo |
| `交易金額錯誤` | 金額超出範圍 | 確認金額限制 |
| `卡片授權失敗` | 信用卡交易被拒 | 請客戶聯繫發卡銀行 |
| `餘額不足` | 信用卡額度不足 | 請客戶確認額度 |
| `卡片過期` | 信用卡已過期 | 請客戶使用有效卡片 |

---

## 常見問題排解

### HashInfo 驗證失敗

**問題**: 收到 `HashInfo 驗證失敗`

**檢查項目**:
1. Hash Key 和 Hash IV 是否正確
2. AES-256-GCM 加密是否正確實作
3. SHA256 計算是否正確
4. 測試/正式環境金鑰是否混用

### 訂單編號重複

**問題**: 收到 `訂單編號重複`

**解決**:
```python
import time
import random
order_id = f"ORD{int(time.time())}{random.randint(100, 999)}"
```

### 付款通知未收到

**問題**: 付款成功但沒收到 NotifyURL 通知

**檢查項目**:
1. NotifyURL 是否為 HTTPS
2. 伺服器是否能被外網存取
3. 是否正確回應 `SUCCESS`
4. 防火牆是否阻擋 PayUni IP

### 加密/解密問題

**問題**: 加密資料無法解密

**檢查項目**:
1. AES-256-GCM 參數是否正確 (Key 32 bytes, IV 16 bytes)
2. Tag 長度是否為 16 bytes
3. Hex 編碼/解碼是否正確

---

## SDK 資源

### 官方 SDK

| 語言 | GitHub |
|------|--------|
| PHP | https://github.com/payuni/PHP_SDK |
| .NET | https://github.com/payuni/NET_SDK |

### 安裝方式

#### PHP (Composer)

```bash
composer require payuni/sdk
```

#### .NET (NuGet)

需要安裝以下套件：
- Newtonsoft.Json (13.0.1+)
- Portable.BouncyCastle (1.9.0+)

---

## 官方資源

- **官方網站**: https://www.payuni.com.tw/
- **API 文件**: https://www.payuni.com.tw/docs/web/
- **GitHub**: https://github.com/payuni
- **WooCommerce 外掛**: https://github.com/payuni/PAYUNi_for_WooCommerce

---

## PAYUNi 支援的付款方式 (TYPE 對照表)

從官方文件 docs.payuni.com.tw 確認支援以下付款方式（其他方式請依後台啟用為準）：

| TYPE / API 路徑提示 | 中文名 | 狀態 |
|---|---|---|
| `CREDIT` | 信用卡（含一次/分期/紅利/Token 約定/快速結帳） | ✅ 確認 |
| `VACC` (虛擬帳號) | ATM 虛擬帳號 | ✅ 確認 |
| `CVS` | 超商代碼 | ✅ 確認 |
| `ICASH` | 愛金卡 (iCashPay) | ✅ 獨立 API: 交易建立/退款 |
| `AFTEE` | AFTEE 先享後付 | ✅ 獨立 API: 建立/確認/退款 |
| `LinePay` | LINE Pay | ✅ 獨立 API: 交易建立 |
| `JKoPay` | 街口支付（JKO Pay） | ✅ **獨立 API: 交易建立/退款**（注意 camelCase 不是 JKOPAY） |
| TWQR | TWQR / 台灣 Pay | ✅ 啟用後可用 |

> **注意**：PAYUNi 的「街口支付」TYPE 為 `JKoPay`（駱駝命名），與 NewebPay 的 `JKOPAY` 不同。整合時需注意大小寫。

最後更新：2026/05/07
