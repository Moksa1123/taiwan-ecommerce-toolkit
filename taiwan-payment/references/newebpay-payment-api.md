# NewebPay Payment API Reference

藍新金流 (NewebPay) 金流 API 完整參考文件。

依據：《線上交易─幕前支付技術串接手冊》NDNF-1.2.5（2026-09-01）、《信用卡定期定額串接技術手冊》NDNP-1.0.8（2026-08-19），官方下載頁 https://www.newebpay.com/website/Page/content/download_api

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
9. [BNPL 先買後付](#bnpl-先買後付)
10. [信用卡定期定額](#信用卡定期定額)
11. [付款結果通知](#付款結果通知)
12. [錯誤碼對照表](#錯誤碼對照表)

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
| BNPL 取消／退款 | `/API/Bnpl/refund` | AFTEE、大哥付你分期（NDNF 4.7） |
| BNPL 請款 | `/API/Bnpl/settle` | AFTEE、大哥付你分期（NDNF 4.8） |
| 定期定額建立委託 | `/MPG/period` | NDNP 4.3 |
| 定期定額修改狀態 | `/MPG/period/AlterStatus` | 暫停／終止／啟用（NDNP 4.4） |
| 定期定額修改內容 | `/MPG/period/AlterAmt` | 金額／週期／期數／到期日（NDNP 4.5） |
| 定期定額委託單查詢 | `/MPG/period/query` | NDNP-1.0.8 新增（NDNP 4.6） |

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
| `ExpireTime` | String(6) | 否 | 繳費截止時間 `His`，預設 `235959`；僅超商代碼（≥ 1 小時）與凱基銀行 ATM（≥ 5 分鐘） |
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
| `BITOPAY` | Int(1) | BitoPay `1`=啟用 (100-49,999 元)；回傳 `CryptoCurrency` 為 `USDT` 或 `USDC`（1.2.3 起移除 BTC、ETH） |
| `AFTEE` | Int(1) | AFTEE 先享後付 `1`=一般支付 `2`=一般支付+分期（申請制） |
| `AFTEE_Inst` | String(21) | `AFTEE=2` 時指定期數：空或 `1`=全部，`3,6,9,12,15,18,21,24` |
| `AFTEE_ExpireTime` | DateTime | 結帳模組失效時間 `YYYY-MM-DD HH:MM:SS`，1–24 小時 |
| `OPPAY` | Int(1) | 大哥付你分期 `1`=消費者負擔手續費 `2`=商店負擔（1.2.5 新增） |
| `BNPL_Capture` | Int(1) | BNPL 請款方式 `0`／未帶=依後台設定 `1`=自動 `2`=手動；API 設定優先 |
| `CVSCOM` | Int(1) | 超商物流 `1`=取貨不付款 `2`=取貨付款 `3`=兩者 |
| `TWQR` | Int(1) | TWQR/簡單付 `1`=啟用 |
| `EZPWECHAT` | Int(1) | 簡單付微信 `1`=啟用 |
| `EZPALIPAY` | Int(1) | 簡單付支付寶 `1`=啟用 |

### 信用卡記憶卡號

| 參數 | 類型 | 說明 |
|------|------|------|
| `TokenTerm` | String(20) | 付款人綁定資料（會員編號、Email），綁定卡號與付款人信箱；限英數與 `.` `_` `@` `-` |
| `TokenTermDemand` | Int(1) | 必填欄位 `1`=到期日+安全碼（預設）`2`=到期日 `3`=安全碼 `4`=都不必填 |

記憶付款人電子信箱（NDNF-1.2.4 起，4.2.1）：須帶 `TokenTerm`，且 `EmailModify=1` 或未帶；付款頁才顯示「記憶付款人電子信箱」。
信箱屬記憶卡號的附屬資料，不能單獨啟用；`EmailModify=0` 或未帶 `TokenTerm` 時不新增、更新或刪除已記憶的信箱。

### 訂單細項 OrderDetail

JSON 陣列，程式版本 2.2 以上。啟用 `AFTEE` 或 `OPPAY` 時必填：

| 欄位 | 類型 | 說明 |
|------|------|------|
| `ItemName` | String(20) | 品名（可用於運費、折扣） |
| `ItemAmt` | Int(10) | 品項金額，可為負（折扣）；**加總須等於 `Amt`**，否則 `MPG01029` |
| `ItemType` | Int(1) | `1` 一般商品 `2` 票券 `3` 儲值金 `4` 折扣 |
| `ItemOrderNo` | String(20) | 品項編號，同訂單不可重複（`MPG01030`） |

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
| `PaymentType` | 支付方式：`CREDIT` `VACC` `WEBATM` `BARCODE` `CVS` `LINEPAY` `ESUNWALLET` `TAIWANPAY` `CVSCOM` `AFTEE` `OPPAY` `TWQR` `EZPALIPAY` `EZPWECHAT` |
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

### 電子錢包專屬欄位（LINE Pay、玉山 Wallet、台灣 Pay、TWQR）

`RespondCode`、`CloseAmt`、`CloseStatus`（`0`–`4`，`4`=請款失敗）、`BackBalance`（不支援 LINE Pay）、`BackStatus`（`0`–`4`）、`RespondMsg`、
`PaymentMethod`（`LINEPAY` `ESUNWALLET` `TAIWANPAY` `TWQR` `EZALIPAY` `EZWECHAT`）、`AuthBank`（`Linepay` `Esun` `EZPAY`=簡單行動支付）。

### BNPL 專屬欄位（AFTEE、大哥付你分期）

`RespondCode`、`RespondMsg`、`CloseAmt`、`CloseStatus`（`0` 未請款 `1` 處理中 `2` 完成 `3` 失敗）、`BackBalance`、
`BackStatus`（`0` 未退款 `2` 處理中 `3` 完成 `4` 失敗）、`Inst`（啟用值 `1` 固定 `0`；`2` 為實際期數，一次付清 `0`）、`PaymentMethod`（`AFTEE` `OPPAY`）。

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

## BNPL 先買後付

AFTEE 先享後付、大哥付你分期（`OPPAY`）。規格書 NDNF-1.2.5 4.7、4.8。

| 功能 | 端點 | 期限 |
|------|------|------|
| 取消交易／退款 [NPA-B07] | `POST /API/Bnpl/refund` | 交易成立後一年內；取消須整筆，退款可部分、多次 |
| 請款 [NPA-B62] | `POST /API/Bnpl/settle` | 整筆請款；AFTEE 89 天內、大哥付你分期 365 天內 |

Post 參數：`UID_`、`Version_`=`1.1`、`EncryptData_`、`RespondType_`（`JSON`／`String`）、`HashData_`。
`EncryptData_`／`HashData_` 與 MPG 的 TradeInfo／TradeSha 算法相同。

| EncryptData_ 欄位 | 類型 | 必填 | 說明 |
|------|------|:---:|------|
| `MerchantOrderNo` | String(30) | ● | 商店訂單編號 |
| `Amt` | Int(10) | ● | 取消金額須等於訂單完成金額；退款金額 ≤ 訂單完成金額；請款金額須等於訂單完成金額 |
| `TimeStamp` | String(50) | ● | Unix 秒數，容許誤差 120 秒 |
| `PaymentType` | String(10) | ● | `AFTEE` 或 `OPPAY` |
| `Reason` | String(100) | 退款● | 取消／退款原因（請款不需要） |

回應：`Status`、`Message`、`EncryptData`、`HashData`、`UID`、`Version`。
解密後：退款為 `MerchantOrderNo`、`TradeNo`、`RefundAmount`、`RefundDate`、`RefundType`（`cancel`／`refund`）；
請款為 `MerchantOrderNo`、`TradeNo`、`Amount`、`CloseDate`。

> 4.8 請款範例的請求密文與其明文、金鑰不符（規格書誤植）；4.7 的請求與兩個回應範例皆可重現，已收進 `tests/vectors/newebpay.json`。
> 回應密文以 32 bytes 區塊補齊，解密須容許 1–32 的 padding。

---

## 信用卡定期定額

規格書 NDNP-1.0.8。Post 參數為 `MerchantID_` + `PostData_`（AES 加密同 TradeInfo，**沒有** SHA 欄位）；回傳欄位 `Period`（AES 加密）。

| 功能 | 端點 | Version |
|------|------|---------|
| 建立委託 [NPA-B05] | `POST /MPG/period`（前景 Form Post） | `1.5` |
| 修改委託狀態 [NPA-B051] | `POST /MPG/period/AlterStatus` | `1.0` |
| 修改委託內容 [NPA-B052] | `POST /MPG/period/AlterAmt` | `1.2` |
| 委託單查詢 [NPA-B053] | `POST /MPG/period/query` | `1.0`（1.0.8 新增） |

### 建立委託 PostData_

| 參數 | 類型 | 必填 | 說明 |
|------|------|:---:|------|
| `RespondType` | String(5) | ● | `JSON`／`String` |
| `TimeStamp` | String(30) | ● | Unix 秒數，容許誤差 120 秒 |
| `Version` | String(5) | ● | `1.5` |
| `LangType` | String(5) | | `en`／`zh-Tw`（預設） |
| `MerOrderNo` | String(30) | ● | 商店訂單編號，英數與 `_`，不可重複 |
| `ProdDesc` | String(100) | ● | 僅中英數、空格、底線 |
| `PeriodAmt` | Int(6) | ● | 每期金額，> 0 |
| `PeriodType` | String(1) | ● | `D` 固定天期（2–999 天）`W` 每週 `M` 每月 `Y` 每年；每期只授權一次 |
| `PeriodPoint` | String(4) | ● | `D`：2–999；`W`：1–7；`M`：`01`–`31`（無該日則月底）；`Y`：`MMDD` |
| `PeriodStartType` | Int(1) | ● | `1` 立即 10 元授權 `2` 立即委託金額授權 `3` 不檢查、不授權 |
| `PeriodTimes` | String(2) | ● | 授權期數；超過卡片到期日時以到期日為最終期。啟用 CAU 且為 `NE` 時視為無限期 |
| `PeriodFirstdate` | String(10) | | 首期授權日 `YYYY/mm/dd`，僅 `PeriodType=D` 且 `PeriodStartType=3`；首期執行後才可修改委託 |
| `ReturnURL` | String(100) | | 首次授權完成後 Form Post 導回 |
| `PeriodMemo` | String(255) | | 備註 |
| `PayerEmail` | String(50) | ● | 付款人信箱 |
| `EmailModify` | Int(1) | | `1` 可修改（預設）`0` 不可 |
| `PaymentInfo` | String(1) | | 顯示付款人資訊欄位 `Y`（預設）／`N` |
| `OrderInfo` | String(1) | | 顯示收件人資訊欄位 `Y`（預設）／`N` |
| `NotifyURL` | String(100) | | 每期授權結果幕後通知；空值則不通知 |
| `BackURL` | String(100) | | 取消交易時返回商店 |

1.0.7 起定期定額不再支援銀聯卡（移除 `UNIONPAY`，`PaymentMethod` 只回 `CREDIT`）。

### 回傳

- **建立完成**（4.3.2）：`Result` 含 `MerchantID`、`MerchantOrderNo`、`PeriodType`、`AuthTimes`、`DateArray`（全部授權日期）、`PeriodAmt`、`PeriodNo`；
  `PeriodStartType` 為 `1`／`2` 時另有 `AuthTime`、`TradeNo`、`CardNo`、`AuthCode`、`RespondCode`（`00` 成功）、`EscrowBank`、`AuthBank`、`PaymentMethod`
- **每期授權完成** [NPA-N050]（4.3.3，送到 `NotifyURL`）：`RespondCode`、`MerchantID`、`MerchantOrderNo`、`OrderNo`（`訂單編號_期數`）、`TradeNo`、`AuthDate`、
  `TotalTimes`、`AlreadyTimes`（含失敗期數）、`AuthAmt`、`AuthCode`、`EscrowBank`、`AuthBank`、`NextAuthDate`、`PeriodNo`
- `AuthBank` 新增 `SinoPac`（1.0.5）；官方建立完成範例回傳 `KGI`，但不在代碼表內

### 修改委託

- **狀態**（`AlterStatus`）：`MerOrderNo`、`PeriodNo`、`AlterType`（小寫：`suspend` 暫停、`terminate` 終止、`restart` 啟用）、`TimeStamp`。
  終止後無法再啟用；暫停後啟用從最近一期開始授權，總期數不變、扣款時間往後展延。回傳 `MerOrderNo`、`PeriodNo`、`AlterType`、`NewNextTime`
- **內容**（`AlterAmt`）：`MerOrderNo`、`PeriodNo`，以及要改的 `AlterAmt`、`PeriodType`＋`PeriodPoint`（須同時帶）、`PeriodTimes`、`Extday`（信用卡到期日 `YYMM`，下一期生效）、`NotifyURL`。
  回傳含 `NewNextAmt`、`NewNextTime`，`NotifyURL` 為 `-` 表示未修改

### 委託單查詢（1.0.8 新增）

PostData_：`RespondType`、`Version`=`1.0`、`TimeStamp`、`MerOrderNo`、`PeriodNo`。
回傳 `Result`：`MerchantID`、`MerOrderNo`、`PeriodNo`、`PeriodAmt`、`PeriodType`、`PeriodPoint`、`CreateDate`、`TotalTimes`、`AlreadyTimes`、`NextAuthDate`，
以及委託狀態 `Status`：`0` 驗證未完成 `1` 扣款中 `2` 驗證失敗（首期或十元驗證失敗）`3` 終止 `4` 已到期 `5` 暫停。

> 官方查詢回傳範例的外層鍵名是小寫 `status`／`message`／`result`（其他 API 為大寫），`Result` 內也是 `MerchantOrderNo` 而非表格寫的 `MerOrderNo`。解析時兩種都要能處理。

### 卡號更新服務 CAU（1.0.7 新增）

Visa、Mastercard。續卡時系統自動更新效期；換卡、掛失等卡號變更則通知商店暫停扣款、請持卡人重新綁卡。
通知送到申請 CAU 時提供的固定 Notify URL（4.3.4），`Result` 含 `MerchantID`、`MerchantOrderNo`、`remainingTimes`、`AuthAmt`、`NextAuthDate`、
`scheduleDates`、`PeriodNo`、`AlterType`、`cardStatus`（`ACTIVE` 可正常扣款；`CARD_NOT_ALLOWED` 已停扣，委託轉為終止）、`newExpiry`（例 `2030-05`，僅效期變更時）。
收到非 `ACTIVE` 應暫停扣款並請持卡人重新綁卡。

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

> 依規格書 NDNF-1.2.5 與 NDNP-1.0.8 錯誤代碼表；完整清單見 `data/error-codes.csv`（`PER` 開頭為定期定額錯誤代碼表）。查詢 API 的 CheckValue 錯誤為 `TRA10054`。

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

> 規格書 NDNF-1.2.5 只定義以上五種狀態。

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
