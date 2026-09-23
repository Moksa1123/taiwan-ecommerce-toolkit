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

> **端點路徑依據**：統一金流官方 PHP SDK（github.com/payuni/PHP_SDK）`PayuniApi::UniversalTrade()` 的對照表，
> 並與 wpbr-payuni-payment 1.7.1 實際呼叫的網址一致。SDK 的操作名稱（如 `trade_query`）**不是**網址路徑，
> 實際路徑是 `trade/query`；舊版本文件曾把兩者混淆。

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
| 交易查詢 | `/trade/query` | 查詢交易狀態 |
| 請退款 | `/trade/close` | 信用卡請款/退款 |
| 取消授權 | `/trade/cancel` | 取消信用卡授權 |
| CVS 取消 | `/cancel_cvs` | 取消超商代碼 |

### 信用卡約定 (Token) 端點

| 功能 | 端點路徑 | 說明 |
|------|----------|------|
| Token 查詢 | `/credit_bind/query` | 查詢約定信用卡 |
| Token 取消 | `/credit_bind/cancel` | 取消約定信用卡 |

### 特殊退款端點

| 功能 | 端點路徑 | 說明 |
|------|----------|------|
| 愛金卡退款 | `/trade/common/refund/icash` | iCash 退款 |
| AFTEE 退款 | `/trade/common/refund/aftee` | AFTEE 退款 |
| AFTEE 確認 | `/trade/common/confirm/aftee` | AFTEE 確認交易 |
| LINE Pay 退款 | `/trade/common/refund/linepay` | LINE Pay 退款 |

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

PayUni 採用 **AES-256-GCM** 加密與 **SHA256** 驗證碼（HashInfo）。

> 以下演算法已與統一金流官方外掛 PAYUNi_for_WooCommerce 1.2.8 `class-payuni.php` 的
> `Encrypt()` / `Decrypt()` / `HashInfo()` 逐位元組比對（repo 的 `tests/vectors/payuni.json`）。

### 格式

```
EncryptInfo = hex( base64(AES-256-GCM 密文) + ":::" + base64(tag) )
HashInfo    = strtoupper( sha256( HashKey + EncryptInfo + HashIV ) )
```

常見錯誤（皆會被 PAYUNi 拒絕）：

| 錯誤寫法 | 問題 |
|---|---|
| `hex(密文 + tag)` | 少了 base64 與 `:::` 分隔 |
| `base64(密文) + ":::" + base64(tag)`（沒有最外層 hex） | 少了最外層 `bin2hex` |
| `sha256(EncryptInfo + HashKey + HashIV)` | HashKey 必須在最前面 |

- IV（HashIV）直接當 GCM nonce 使用，長度 16 bytes（官方外掛即如此），不是 12 bytes
- tag 為 16 bytes，base64 後為 24 字元

### 加密流程

1. **準備參數** - 組合所有請求參數
2. **http_build_query** - 將參數轉為 Query String
3. **AES-256-GCM 加密** - 以 HashKey 為金鑰、HashIV 為 nonce
4. **組合 EncryptInfo** - `bin2hex(base64密文 . ':::' . base64(tag))`
5. **產生 HashInfo** - `sha256(HashKey . EncryptInfo . HashIV)` 轉大寫
6. **發送請求** - 將 `MerID`、`Version`、`EncryptInfo`、`HashInfo` POST 至 API

### PHP 加密範例

與官方外掛相同的寫法（`openssl_encrypt` 的 options 傳 `0`，回傳值即為 base64 密文）：

<!-- verify: payuni -->
```php
<?php

class PayuniEncryption
{
    public function __construct(private string $hashKey, private string $hashIV) {}

    public function encrypt(array $params): string
    {
        $tag = '';
        $encrypted = openssl_encrypt(
            http_build_query($params),
            'aes-256-gcm',
            trim($this->hashKey),
            0,                      // 回傳 base64 密文
            trim($this->hashIV),
            $tag
        );
        return trim(bin2hex($encrypted . ':::' . base64_encode($tag)));
    }

    public function decrypt(string $encryptInfo): array
    {
        [$encryptData, $tag] = explode(':::', hex2bin($encryptInfo), 2);
        $plain = openssl_decrypt(
            $encryptData,
            'aes-256-gcm',
            trim($this->hashKey),
            0,
            trim($this->hashIV),
            base64_decode($tag)
        );
        if ($plain === false) {
            throw new RuntimeException('解密失敗：tag 驗證不通過（資料遭竄改或金鑰錯誤）');
        }
        parse_str($plain, $result);
        return $result;
    }

    public function hashInfo(string $encryptInfo): string
    {
        return strtoupper(hash('sha256', $this->hashKey . $encryptInfo . $this->hashIV));
    }
}
```

### Python 加密範例

<!-- verify: payuni -->
```python
"""PayUni AES-256-GCM 加密（與官方外掛逐位元組相同）"""

import base64
import hashlib
import hmac
from urllib.parse import urlencode, parse_qs

from Crypto.Cipher import AES


class PayuniEncryption:
    def __init__(self, hash_key: str, hash_iv: str):
        self.hash_key = hash_key
        self.hash_iv = hash_iv

    def encrypt(self, params: dict) -> str:
        cipher = AES.new(self.hash_key.encode(), AES.MODE_GCM, nonce=self.hash_iv.encode())
        encrypted, tag = cipher.encrypt_and_digest(urlencode(params).encode('utf-8'))
        return (base64.b64encode(encrypted) + b':::' + base64.b64encode(tag)).hex()

    def decrypt(self, encrypt_info: str) -> dict:
        encrypted_b64, tag_b64 = bytes.fromhex(encrypt_info).split(b':::', 1)
        cipher = AES.new(self.hash_key.encode(), AES.MODE_GCM, nonce=self.hash_iv.encode())
        # tag 不符會拋出 ValueError
        plain = cipher.decrypt_and_verify(base64.b64decode(encrypted_b64), base64.b64decode(tag_b64))
        return {k: v[0] for k, v in parse_qs(plain.decode('utf-8'), keep_blank_values=True).items()}

    def hash_info(self, encrypt_info: str) -> str:
        raw = self.hash_key + encrypt_info + self.hash_iv   # HashKey 在前
        return hashlib.sha256(raw.encode('utf-8')).hexdigest().upper()

    def verify(self, encrypt_info: str, hash_info: str) -> bool:
        return hmac.compare_digest(self.hash_info(encrypt_info), hash_info.upper())
```

完整可執行版本見 `examples/payuni-payment-example.py`。

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
| `ExpireDate` | String | 否 | 繳費期限日期 `YYYY-MM-DD`（官方外掛以「今天 + 後台設定天數」計算），不是天數 |
| `ProdDesc` | String | 否 | 商品描述 |
| `UsrMail` | String | 否 | 消費者 Email |
| `ReturnURL` | String | 否 | 前台返回網址 |
| `NotifyURL` | String | 否 | 背景通知網址 |
| `Lang` | String | 否 | 語系 `zh-tw` / `en` |

| `Credit` / `ATM` / `CVS` / … | Integer | 否 | 付款方式開關，值為 `1`；欄位名稱見文末「UPP 開關欄位」 |

外層表單欄位為 `MerID`、`Version`（`1.0`）、`EncryptInfo`、`HashInfo`，由**消費者瀏覽器**以表單 POST 送出（官方 SDK 的 `HtmlApi()` 即自動送出的表單），不是伺服器端呼叫。

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

### BankType 銀行代碼（回應欄位）

虛擬帳號所屬銀行，以**銀行代碼**回傳（依 wpbr-payuni-payment 1.7.1 `Utils/BankType.php`）：

| 代碼 | 銀行 |
|------|------|
| `004` | 臺灣銀行 |
| `013` | 國泰世華 |
| `822` | 中國信託 |

### Version 與回應格式

wpbr-payuni-payment 1.7.1 以 `Version: 2.0` 呼叫本端點，解密後交易資料在 **`Result` 陣列**內
（PHP `parse_str` 解出 `Result[0][MerTradeNo]` 這類巢狀欄位；Python 需自行處理巢狀 key）。
官方 PHP SDK 預設帶 `Version: 1.0`。

### 回應參數 (解密後，`Result[0]` 內)

| 參數 | 說明 |
|------|------|
| `MerTradeNo` | 商店訂單編號 |
| `TradeNo` | UNi 交易序號 |
| `TradeStatus` | 交易狀態（見下表） |
| `PaymentType` | 付款方式代碼（見下表） |
| `CreateDay` | 訂單建立時間 |
| `PaymentDay` | 付款時間 |
| `CloseStatus` | 請款狀態（信用卡才有，見下表） |

### TradeStatus 交易狀態

| 狀態 | 說明 |
|------|------|
| `0` | 取號成功（ATM / 超商代碼）或信用審查正常（AFTEE） |
| `1` | 已付款 |
| `2` | 付款失敗 |
| `3` | 付款取消 |
| `4` | 交易逾期（ATM / 超商代碼 / AFTEE） |
| `8` | 待確認 |
| `9` | 未付款 |

### PaymentType 付款方式代碼

| 代碼 | 說明 |
|------|------|
| `1` | 信用卡 |
| `2` | ATM 轉帳 |
| `3` | 超商代碼 |
| `5` | 超商取貨付款 |
| `6` | 愛金卡 iCash |
| `7` | AFTEE |
| `9` | LINE Pay |
| `10` | 宅配到付 |

### CloseStatus 請款狀態

| 狀態 | 說明 |
|------|------|
| `1` | 請款申請中 |
| `2` | 請款成功（此時才能以 trade/close + `CloseType=2` 退款） |
| `3` | 請款取消 |
| `7` | 請款處理中 |
| `9` | 未申請 |

> 以上代碼表依 wpbr-payuni-payment 1.7.1 `Utils/TradeStatus.php`、`PayType.php`、`CloseStatus.php`。

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

$response = file_get_contents('https://api.payuni.com.tw/api/trade/query', false, stream_context_create([
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
POST /api/trade/close
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
POST /api/trade/cancel
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
POST /api/credit_bind/query
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
POST /api/credit_bind/cancel
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
3. **⚠️ SHA256 計算順序**: 必須是 `SHA256(HashKey + EncryptInfo + HashIV)` 而非 `SHA256(EncryptInfo + HashKey + HashIV)` — **Key 必須在前**
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
3. **⚠️ EncryptInfo 格式**: 必須是 `base64(密文) + ":::" + base64(Tag)` 而非 `hex(密文 + tag)` — 密文和 tag **分別 base64 編碼並用 ":::" 分隔**

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

## PAYUNi 支援的付款方式（UPP 開關欄位）

UPP 以「付款方式名稱 = 1」的旗標啟用付款方式（例如 `Credit=1&ATM=1&CVS=1`），**沒有**單一的 `PayType` 參數。
以下欄位名稱取自統一金流官方外掛 PAYUNi_for_WooCommerce 1.2.8 的 `$paymentArr`，大小寫須完全相同：

| 欄位 | 說明 |
|---|---|
| `Credit` | 信用卡一次付清 |
| `CreditInst` | 信用卡分期 |
| `CreditRed` | 信用卡紅利 |
| `CreditUnionPay` | 銀聯卡 |
| `ApplePay` / `GooglePay` / `SamsungPay` | 行動支付 |
| `ATM` | ATM 虛擬帳號（不是 `VACC`） |
| `CVS` | 超商代碼 |
| `ICash` | 愛金卡 |
| `Aftee` | AFTEE 先享後付 |
| `LinePay` | LINE Pay |
| `JKoPay` | 街口支付 |

另有幕後（伺服器對伺服器）建立交易的獨立端點：`/atm`、`/cvs`、`/credit`、`/linepay`（Version `1.1`）、`/aftee_direct`。

最後更新：2026-09-23
