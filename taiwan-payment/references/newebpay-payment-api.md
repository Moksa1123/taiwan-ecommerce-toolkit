# NewebPay Payment API Reference

藍新金流 (NewebPay) 金流 API 完整參考文件。

---

## 目錄

1. [API 端點總覽](#api-端點總覽)
2. [測試環境](#測試環境)
3. [加解密機制](#加解密機制)
4. [MPG 交易](#mpg-交易)
5. [單筆交易查詢](#單筆交易查詢)
6. [取消授權](#取消授權)
7. [請退款/取消請退款](#請退款取消請退款)
8. [電子錢包退款](#電子錢包退款)
9. [付款結果通知](#付款結果通知)
10. [錯誤碼對照表](#錯誤碼對照表)

---

## API 端點總覽

### 基礎 API 路徑

| 環境 | 基礎路徑 |
|------|----------|
| **測試環境** | `https://ccore.newebpay.com` |
| **正式環境** | `https://core.newebpay.com` |

### 端點列表

| 功能 | 端點路徑 | 說明 |
|------|----------|------|
| MPG 交易 | `/MPG/mpg_gateway` | 幕前支付頁面 |
| 單筆查詢 | `/API/QueryTradeInfo` | 查詢交易狀態 |
| 取消授權 | `/API/CreditCard/Cancel` | 取消信用卡授權 |
| 請退款 | `/API/CreditCard/Close` | 信用卡請款/退款 |
| 電子錢包退款 | `/API/EWallet/refund` | 錢包類退款 |

---

## 測試環境

### 測試帳號

測試帳號請至藍新金流後台申請：

```
後台網址: https://www.newebpay.com/
路徑: 會員中心 > 商店管理 > 商店資料設定 > 串接設定
```

取得以下資訊：
- **商店代號 (MerchantID)**
- **Hash Key**
- **Hash IV**

### 測試信用卡

| 卡號 | 說明 |
|------|------|
| `4000-2211-1111-1111` | 一般測試卡 |
| `4761-5311-1111-1114` | 美國運通測試卡 |

- **有效期限**: 任意未過期日期 (格式 MMYY)
- **CVV/CVC**: 任意 3 碼

---

## 加解密機制

藍新金流採用 **AES-256-CBC** 加密與 **SHA256** 驗證。

### 加密流程

1. **準備參數** - 組合所有請求參數
2. **URL Encode** - 將參數組成 Query String
3. **AES-256-CBC 加密** - 使用 Hash Key 和 Hash IV
4. **轉十六進制** - 將加密結果轉 Hex
5. **SHA256 雜湊** - 產生 TradeSha 驗證碼

### PHP 加密範例

<!-- verify: newebpay -->
```php
<?php

class NewebPayEncryption
{
    private string $hashKey;
    private string $hashIV;

    public function __construct(string $hashKey, string $hashIV)
    {
        $this->hashKey = $hashKey;
        $this->hashIV = $hashIV;
    }

    /**
     * AES-256-CBC 加密
     */
    public function encrypt(array $params): string
    {
        // 1. 組合 Query String
        $queryString = http_build_query($params);

        // 2. AES-256-CBC 加密
        $encrypted = openssl_encrypt(
            $queryString,
            'AES-256-CBC',
            $this->hashKey,
            OPENSSL_RAW_DATA,
            $this->hashIV
        );

        // 3. 轉十六進制
        return bin2hex($encrypted);
    }

    /**
     * AES-256-CBC 解密（與藍新官方外掛 create_aes_decrypt() 相同）
     *
     * 官方外掛加密時以 32 bytes 區塊補齊，padding 可能是 17–32；
     * 直接用 OPENSSL_RAW_DATA（預設 PKCS#7，只接受 1–16）會解密失敗回傳 false。
     */
    public function decrypt(string $encryptedData): array
    {
        $decrypted = openssl_decrypt(
            hex2bin($encryptedData),
            'AES-256-CBC',
            $this->hashKey,
            OPENSSL_RAW_DATA | OPENSSL_ZERO_PADDING,
            $this->hashIV
        );

        // 以最後一個 byte 為 padding 長度移除，並確認尾端一致
        $pad = ord(substr($decrypted, -1));
        if ($pad < 1 || $pad > 32 || substr($decrypted, -$pad) !== str_repeat(chr($pad), $pad)) {
            throw new RuntimeException('解密失敗：HashKey / HashIV 可能不正確');
        }
        $plain = substr($decrypted, 0, -$pad);

        // RespondType=JSON 時明文是 JSON（交易明細在 Result 內）；String 時是 query string
        $json = json_decode($plain, true);
        if (is_array($json)) {
            return $json;
        }
        parse_str($plain, $result);
        return $result;
    }

    /**
     * 產生 TradeSha (SHA256)
     */
    public function tradeSha(string $tradeInfo): string
    {
        $raw = "HashKey={$this->hashKey}&{$tradeInfo}&HashIV={$this->hashIV}";
        return strtoupper(hash('sha256', $raw));
    }
}
```

### Python 加密範例

> 以下類別由 CI 以藍新官方外掛與規格書產生的標準答案驗證（`tests/vectors/newebpay.json`）。

<!-- verify: newebpay -->
```python
"""NewebPay AES-256-CBC 加密"""

import hashlib
import hmac
import json
from urllib.parse import urlencode, parse_qsl

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad


class NewebPayEncryption:
    def __init__(self, hash_key: str, hash_iv: str):
        self.hash_key = hash_key
        self.hash_iv = hash_iv

    def _cipher(self):
        return AES.new(self.hash_key.encode(), AES.MODE_CBC, self.hash_iv.encode())

    def encrypt(self, params: dict) -> str:
        """標準 PKCS#7（與規格書 NDNF 的 PHP 範例相同）→ hex"""
        return self._cipher().encrypt(pad(urlencode(params).encode('utf-8'), 16)).hex()

    def decrypt(self, trade_info: str) -> dict:
        data = self._cipher().decrypt(bytes.fromhex(trade_info))
        # 官方外掛以 32 bytes 補齊，padding 可能是 1–32；Crypto.Util.Padding.unpad(data, 16) 會失敗
        n = data[-1]
        if not 1 <= n <= 32 or data[-n:] != bytes([n]) * n:
            raise ValueError('padding 錯誤（HashKey / HashIV 可能不正確）')
        text = data[:-n].decode('utf-8')
        # RespondType=JSON 時明文是 JSON；用 parse_qs 會得到空 dict
        return json.loads(text) if text.startswith('{') else dict(parse_qsl(text, keep_blank_values=True))

    def trade_sha(self, trade_info: str) -> str:
        raw = f"HashKey={self.hash_key}&{trade_info}&HashIV={self.hash_iv}"
        return hashlib.sha256(raw.encode('utf-8')).hexdigest().upper()

    def verify_trade_sha(self, trade_info: str, trade_sha: str) -> bool:
        return hmac.compare_digest(self.trade_sha(trade_info), trade_sha.upper())
```

### CheckCode 驗證

驗證回傳結果的 CheckCode（規格書 4.1.5）。此規則已與規格書「單筆交易查詢」回應範例中
**藍新伺服器實際產生**的 CheckCode 比對一致（見 `tests/vectors/newebpay.json` 的 `server_check_code`）：

```php
<?php

function generateCheckCode(array $params, string $hashKey, string $hashIV): string
{
    // 取出四個欄位
    $checkParams = [
        'Amt' => $params['Amt'],
        'MerchantID' => $params['MerchantID'],
        'MerchantOrderNo' => $params['MerchantOrderNo'],
        'TradeNo' => $params['TradeNo'],
    ];

    // 排序 (A-Z)
    ksort($checkParams);

    // 組合字串
    $paramStr = http_build_query($checkParams);

    // 前後加上 HashIV 和 HashKey (注意順序)
    $raw = "HashIV={$hashIV}&{$paramStr}&HashKey={$hashKey}";

    // SHA256 + 轉大寫
    return strtoupper(hash('sha256', $raw));
}
```

---

## MPG 交易

### 端點

```
POST /MPG/mpg_gateway
```

### Post 參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `MerchantID` | String(15) | ● | 商店代號 |
| `TradeInfo` | String | ● | AES 加密後的交易資料 |
| `TradeSha` | String | ● | SHA256 驗證碼 |
| `Version` | String(5) | ● | 串接版本 `2.3` |
| `EncryptType` | Int(1) | 否 | 加密模式 `1`=AES/GCM |

### TradeInfo 參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `MerchantID` | String(15) | ● | 商店代號 |
| `RespondType` | String(6) | ● | 回傳格式 `JSON` 或 `String` |
| `TimeStamp` | String(50) | ● | Unix 時間戳 (容許誤差 120 秒) |
| `Version` | String(5) | ● | 串接版本 `2.3` |
| `MerchantOrderNo` | String(30) | ● | 訂單編號 (唯一) |
| `Amt` | Int(10) | ● | 訂單金額 (新台幣整數) |
| `ItemDesc` | String(50) | ● | 商品資訊 |
| `LangType` | String(5) | 否 | 語系 `zh-tw`/`en`/`jp` |
| `TradeLimit` | Int(3) | 否 | 交易秒數限制 (60-900) |
| `ExpireDate` | String(10) | 否 | 繳費期限 `Ymd`，預設 7 天，最大 180 天 |
| `ReturnURL` | String(200) | 否 | 付款完成返回網址 |
| `NotifyURL` | String(200) | 否 | 背景通知網址 |
| `CustomerURL` | String(200) | 否 | 取號結果網址 |
| `ClientBackURL` | String(200) | 否 | 返回商店按鈕網址 |
| `Email` | String(50) | 否 | 付款人 Email |
| `EmailModify` | Int(1) | 否 | Email 可否修改 `1`=可 `0`=不可 |

### 支付方式參數

| 參數 | 類型 | 說明 |
|------|------|------|
| `CREDIT` | Int(1) | 信用卡一次付清 `1`=啟用 |
| `APPLEPAY` | Int(1) | Apple Pay `1`=啟用 |
| `ANDROIDPAY` | Int(1) | Google Pay `1`=啟用 |
| `SAMSUNGPAY` | Int(1) | Samsung Pay `1`=啟用 |
| `LINEPAY` | Int(1) | LINE Pay `1`=啟用 |
| `InstFlag` | String(18) | 分期 `1`=全部, `3,6,12`=指定期數 |
| `CreditRed` | Int(1) | 紅利折抵 `1`=啟用 |
| `UNIONPAY` | Int(1) | 銀聯卡 `1`=啟用 |
| `CREDITAE` | Int(1) | 美國運通卡 `1`=啟用 |
| `WEBATM` | Int(1) | WebATM `1`=啟用 (限 49,999 元以下) |
| `VACC` | Int(1) | ATM 轉帳 `1`=啟用 (限 49,999 元以下) |
| `BankType` | String(26) | 指定銀行 `BOT`/`HNCB`/`KGI` |
| `CVS` | Int(1) | 超商代碼 `1`=啟用 (30-20,000 元) |
| `BARCODE` | Int(1) | 超商條碼 `1`=啟用 (20-40,000 元) |
| `ESUNWALLET` | Int(1) | 玉山 Wallet `1`=啟用 |
| `TAIWANPAY` | Int(1) | 台灣 Pay `1`=啟用 (限 49,999 元以下) |
| `BITOPAY` | Int(1) | BitoPay `1`=啟用 (100-49,999 元) |
| `CVSCOM` | Int(1) | 超商物流 `1`=取貨不付款 `2`=取貨付款 `3`=兩者 |
| `TWQR` | Int(1) | TWQR/簡單付 `1`=啟用 |
| `EZPWECHAT` | Int(1) | 簡單付微信 `1`=啟用 |
| `EZPALIPAY` | Int(1) | 簡單付支付寶 `1`=啟用 |

### 信用卡記憶卡號

| 參數 | 類型 | 說明 |
|------|------|------|
| `TokenTerm` | String(20) | 付款人綁定資料 (會員編號/Email) |
| `TokenTermDemand` | Int(1) | 必填欄位 `1`=到期日+安全碼 `2`=到期日 `3`=安全碼 `4`=都不必填 |

### PHP 範例

```php
<?php

$encryption = new NewebPayEncryption($hashKey, $hashIV);

$params = [
    'MerchantID' => 'MS12345678',
    'RespondType' => 'JSON',
    'TimeStamp' => time(),
    'Version' => '2.3',
    'MerchantOrderNo' => 'ORDER' . time(),
    'Amt' => 1000,
    'ItemDesc' => '測試商品',
    'Email' => 'test@example.com',
    'CREDIT' => 1,
    'VACC' => 1,
    'NotifyURL' => 'https://your-site.com/notify',
    'ReturnURL' => 'https://your-site.com/return',
];

$tradeInfo = $encryption->encrypt($params);
$tradeSha = $encryption->tradeSha($tradeInfo);

// 產生表單
$html = <<<HTML
<form method="post" action="https://core.newebpay.com/MPG/mpg_gateway">
    <input type="hidden" name="MerchantID" value="{$params['MerchantID']}">
    <input type="hidden" name="TradeInfo" value="{$tradeInfo}">
    <input type="hidden" name="TradeSha" value="{$tradeSha}">
    <input type="hidden" name="Version" value="2.3">
    <button type="submit">前往付款</button>
</form>
HTML;

echo $html;
```

---

## 單筆交易查詢

### 端點

```
POST /API/QueryTradeInfo
```

### 請求參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `MerchantID` | String(15) | ● | 商店代號 |
| `Version` | String(5) | ● | `1.3` |
| `RespondType` | String(6) | ● | `JSON` 或 `String` |
| `CheckValue` | String(255) | ● | 檢查碼 |
| `TimeStamp` | String(50) | ● | Unix 時間戳 |
| `MerchantOrderNo` | String(30) | ● | 商店訂單編號 |
| `Amt` | Int(10) | ● | 訂單金額 |

### CheckValue 產生規則

```php
<?php

function generateCheckValue(string $amt, string $merchantID, string $merchantOrderNo, string $hashKey, string $hashIV): string
{
    // 1. 組合參數 (A-Z 排序)
    $paramStr = "Amt={$amt}&MerchantID={$merchantID}&MerchantOrderNo={$merchantOrderNo}";

    // 2. 前後加上 IV 和 Key
    $raw = "IV={$hashIV}&{$paramStr}&Key={$hashKey}";

    // 3. SHA256 + 轉大寫
    return strtoupper(hash('sha256', $raw));
}
```

### 回應參數

| 參數 | 說明 |
|------|------|
| `Status` | `SUCCESS` 或錯誤碼 |
| `Message` | 訊息說明 |
| `Result` | 交易詳細資訊 |

### Result 欄位

| 參數 | 說明 |
|------|------|
| `MerchantID` | 商店代號 |
| `Amt` | 交易金額 |
| `TradeNo` | 藍新交易序號 |
| `MerchantOrderNo` | 商店訂單編號 |
| `TradeStatus` | 交易狀態 `0`=未付款 `1`=成功 `2`=失敗 `3`=取消 `6`=退款 |
| `PaymentType` | 支付方式 |
| `CreateTime` | 建立時間 |
| `PayTime` | 付款時間 |
| `CheckCode` | 檢核碼 |
| `FundTime` | 預計撥款日 |

### 信用卡專屬欄位

| 參數 | 說明 |
|------|------|
| `RespondCode` | 金融機構回應碼 |
| `Auth` | 授權碼 |
| `ECI` | 3D 驗證值 (`1`,`2`,`5`,`6`=3D 交易) |
| `CloseAmt` | 請款金額 |
| `CloseStatus` | 請款狀態 `0`=未請款 `1`=等待 `2`=處理中 `3`=完成 |
| `BackBalance` | 可退款餘額 |
| `BackStatus` | 退款狀態 `0`=未退款 `1`=等待 `2`=處理中 `3`=完成 |
| `Card6No` | 卡號前六碼 |
| `Card4No` | 卡號後四碼 |
| `Inst` | 分期期別 |
| `InstFirst` | 首期金額 |
| `InstEach` | 每期金額 |
| `AuthBank` | 收單機構 |

---

## 取消授權

### 端點

```
POST /API/CreditCard/Cancel
```

### 請求參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `MerchantID_` | String(10) | ● | 商店代號 |
| `PostData_` | Text | ● | AES 加密資料 |

### PostData_ 內容

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `RespondType` | String(5) | ● | `JSON` 或 `String` |
| `Version` | String(5) | ● | `1.0` |
| `Amt` | Int(10) | ● | 取消金額 (需與授權金額相同) |
| `MerchantOrderNo` | String(30) | + | 訂單編號 (二擇一) |
| `TradeNo` | String(17) | + | 藍新交易序號 (二擇一) |
| `IndexType` | Int(1) | ● | `1`=用訂單編號 `2`=用交易序號 |
| `TimeStamp` | String(30) | ● | Unix 時間戳 |

---

## 請退款/取消請退款

### 端點

```
POST /API/CreditCard/Close
```

### 功能說明

| 功能編號 | 功能 | CloseType | Cancel |
|----------|------|-----------|--------|
| B031 | 請款 | `1` | - |
| B032 | 退款 | `2` | - |
| B033 | 取消請款 | `1` | `1` |
| B034 | 取消退款 | `2` | `1` |

### 請求參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `MerchantID_` | String(15) | ● | 商店代號 |
| `PostData_` | Text | ● | AES 加密資料 |

### PostData_ 內容

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `RespondType` | String(5) | ● | `JSON` 或 `String` |
| `Version` | String(5) | ● | `1.1` |
| `Amt` | Int(10) | ● | 請退款金額 |
| `MerchantOrderNo` | String(30) | ● | 訂單編號 |
| `TimeStamp` | String(30) | ● | Unix 時間戳 |
| `IndexType` | Int(1) | ● | `1`=用訂單編號 `2`=用交易序號 |
| `TradeNo` | String(20) | ● | 藍新交易序號 |
| `CloseType` | Int(1) | ● | `1`=請款 `2`=退款 |
| `Cancel` | Int(1) | 否 | `1`=取消請款/退款 |

### 退款限制

| 交易類型 | 請款 | 退款 |
|----------|------|------|
| 一次付清 | 整筆/部分 | 整筆/部分 |
| 分期付款 | 整筆 | 整筆 |
| 紅利折抵 | 整筆 | 整筆 |
| 銀聯卡 | 整筆 | 整筆/部分 |

---

## 電子錢包退款

### 端點

```
POST /API/EWallet/refund
```

### 各錢包退款規則

| 錢包 | 退款期限 | 部分退款 | 備註 |
|------|----------|----------|------|
| 玉山 Wallet | 89 天 | ● | 交易完成 10 分鐘後 |
| 台灣 Pay | 29 天 | ✗ | 僅全額退款 |
| LINE Pay | 60 天 | ● | |
| TWQR | 89 天 | ● | 從請款日起算 |
| 支付寶/微信 | 89 天 | ● | |

### 請求參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `UID_` | String(15) | ● | 商店代號 |
| `Version_` | String(5) | ● | `1.1` |
| `EncryptData_` | Text | ● | AES 加密資料 |
| `RespondType_` | String(15) | ● | `JSON` |
| `HashData_` | Text | ● | SHA256 雜湊 |

### EncryptData_ 內容

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `MerchantOrderNo` | String(30) | ● | 訂單編號 |
| `Amount` | Int(10) | ● | 退款金額 |
| `TimeStamp` | String(50) | ● | Unix 時間戳 |
| `PaymentType` | String | ● | 付款方式 (見下表) |

### PaymentType 對應

| 錢包 | PaymentType |
|------|-------------|
| 玉山 Wallet | `ESUNWALLET` |
| LINE Pay | `LINEPAY` |
| 台灣 Pay | `TAIWANPAY` |
| TWQR | `TWQR` |
| 支付寶 | `EZPALIPAY` |
| 微信 | `EZPWECHAT` |

---

## 付款結果通知

### 通知流程

藍新會 POST 加密資料到 `NotifyURL` 和 `ReturnURL`。

### 通知參數

| 參數 | 說明 |
|------|------|
| `Status` | `SUCCESS` 或錯誤碼 |
| `MerchantID` | 商店代號 |
| `TradeInfo` | AES 加密的交易結果 |
| `TradeSha` | SHA256 驗證碼 |
| `Version` | 串接版本 |

### TradeInfo 解密後內容

| 參數 | 說明 |
|------|------|
| `Status` | 交易狀態 |
| `Message` | 交易訊息 |
| `MerchantID` | 商店代號 |
| `Amt` | 交易金額 |
| `TradeNo` | 藍新交易序號 |
| `MerchantOrderNo` | 訂單編號 |
| `PaymentType` | 支付方式 |
| `PayTime` | 付款時間 |
| `IP` | 付款人 IP |
| `EscrowBank` | 款項保管銀行 |

### 處理範例

```php
<?php

// 接收通知
$status = $_POST['Status'] ?? '';
$tradeInfo = $_POST['TradeInfo'] ?? '';
$tradeSha = $_POST['TradeSha'] ?? '';

// 驗證 TradeSha
$encryption = new NewebPayEncryption($hashKey, $hashIV);
$calculatedSha = $encryption->tradeSha($tradeInfo);

if ($tradeSha !== $calculatedSha) {
    echo 'TradeSha Error';
    exit;
}

// 解密
$data = $encryption->decrypt($tradeInfo);

// 檢查交易狀態
if ($data['Status'] === 'SUCCESS') {
    // 交易成功，更新訂單狀態
    updateOrderStatus($data['MerchantOrderNo'], 'paid', $data);
}

// 回應 (藍新不要求特定回應)
echo 'OK';
```

---

## 錯誤碼對照表

### 常見錯誤碼

> 依規格書 NDNF-1.2.2 錯誤代碼表；完整清單（99 筆）見 `data/error-codes.csv`。查詢 API 的 CheckValue 錯誤為 `TRA10054`。

| 錯誤碼 | 說明 | 備註 |
|--------|------|------|
| `MPG01002` | 時間戳記不可空白 | TimeStamp |
| `MPG01009` | 商店代號不可空白 | MerchantID |
| `MPG01012` | 訂單編號錯誤 | 限英數字底線，30 字 |
| `MPG01015` | 金額錯誤 | Amt |
| `MPG01023` | TradeInfo 不可空白 | |
| `MPG01024` | TradeSha 不可空白 | |
| `MPG02001` | 檢查碼錯誤 | TradeSha 不符 |
| `MPG02002` | 未啟用金流服務 | |
| `MPG02003` | 支付方式未啟用 | |
| `MPG03004` | 商店已暫停 | |
| `MPG03008` | 訂單編號重複 | |
| `MPG03009` | 交易失敗 | 依 Message 判斷原因 |
| `MPG05002` | 信用卡卡號長度不足 | |
| `MPG05005` | 警示交易 | |

### 交易狀態碼 (TradeStatus)

| 狀態 | 說明 |
|------|------|
| `0` | 未付款 |
| `1` | 付款成功 |
| `2` | 付款失敗 |
| `3` | 取消付款 |
| `6` | 退款 |

> 規格書 NDNF-1.2.2 只定義以上五種狀態。

### 收單機構代碼 (AuthBank)

| 代碼 | 銀行 |
|------|------|
| `Esun` | 玉山銀行 |
| `Taishin` | 台新銀行 |
| `CTBC` | 中國信託 |
| `NCCC` | 聯合信用卡中心 |
| `CathayBK` | 國泰世華 |
| `Citibank` | 花旗銀行 |
| `UBOT` | 聯邦銀行 |
| `SKBank` | 新光銀行 |
| `Fubon` | 富邦銀行 |
| `FirstBank` | 第一銀行 |
| `LINEBank` | 連線商業銀行 |
| `SinoPac` | 永豐銀行 |

---

## 官方資源

- **官方網站**: https://www.newebpay.com/
- **API 文件**: https://www.newebpay.com/website/Page/content/download_api
- **技術客服**: 02-2162-2005
