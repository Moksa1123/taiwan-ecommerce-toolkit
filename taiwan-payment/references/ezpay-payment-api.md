# ezPay 簡單付 Payment API Reference

ezPay 簡單付 (簡單行動支付股份有限公司) 金流 API 完整參考文件。

> **重要說明**
>
> ezPay 簡單付為藍新金流 Newebpay 集團旗下小型商家品牌，金流端 API 與 Newebpay MPG 完全相同（TradeInfo / TradeSha 加密、相同欄位、相同流程），差異主要在商家身份、URL 與部分付款方式限制。本文件聚焦 ezPay 特有差異；金流主流程請參考 [`newebpay-payment-api.md`](./newebpay-payment-api.md)。

---

## 目錄

1. [基本說明](#基本說明)
2. [環境資訊](#環境資訊)
3. [認證方式](#認證方式)
4. [訂單建立](#訂單建立)
5. [付款通知](#付款通知)
6. [退款](#退款)
7. [訂單查詢](#訂單查詢)
8. [錯誤代碼](#錯誤代碼)
9. [支付方式對照表](#支付方式對照表)
10. [與 Newebpay 差異總表](#與-newebpay-差異總表)

---

## 基本說明

### 品牌定位

| 項目 | 說明 |
|------|------|
| **品牌名稱** | ezPay 簡單付 |
| **公司** | 簡單行動支付股份有限公司 |
| **集團母品牌** | 藍新金流 Newebpay (智冠科技集團) |
| **歷史品牌** | Pay2Go（早期 spgateway 域名沿用至今） |
| **服務對象** | 中小型商家、個人賣家、小規模 e-commerce |
| **金流主管機關** | 金管會核准之第三方支付機構 |

### 與 Newebpay 的關係

ezPay 與 Newebpay **後端為同一套金流系統**，故：

- **API 演算法 100% 相同** — 同樣使用 `TradeInfo` (AES-256-CBC + Hex) + `TradeSha` (SHA256)
- **欄位名稱 100% 相同** — `MerchantID` / `MerchantOrderNo` / `Amt` / `ItemDesc` / `RespondType` / `Version` / `TimeStamp` / `NotifyURL` / `ReturnURL` 等全部相同
- **回傳格式 100% 相同** — Notify/Return 的 TradeInfo 解密後 JSON 結構一致
- **錯誤碼前綴相同** — 共用 `MPG*`, `TRA*`, `VACC*`, `CVS*` 等錯誤碼體系

主要差異：

1. **商家申請門檻** — ezPay 主打小型商家、無需公司行號即可申請
2. **API 域名** — 沿用早期 Pay2Go 的 `spgateway.com` 域名（部分老商家），新版可能使用 `ezpay.com.tw` 域名
3. **MerchantID 命名** — ezPay 開立的 MerchantID 通常以 `EZ` 系列前綴開頭（與 Newebpay 的 `MS` 系列區隔）
4. **支付方式限制** — 部分付款方式（例如分期付款、特定電子錢包）對小型商家有額外限制
5. **手續費結構** — 費率與商家方案綁定（屬於商務面議題，本文不展開）

### 適用情境

選擇 ezPay 的常見原因：

- 個人賣家或無公司行號商家
- 月交易量低（< 一定門檻）
- 需要快速開通（審核時間較短）
- 想要使用 LINE Pay / 街口 / 簡單付錢包等電子錢包但月流水未達 Newebpay 標準

> **如果你已經有 Newebpay 帳號**：直接用 Newebpay，不需要再開 ezPay。兩者 API 同源，但 Newebpay 商家方案費率與功能更完整。

---

## 環境資訊

### API 端點（核心差異）

| 環境 | Newebpay | ezPay 簡單付 |
|------|----------|--------------|
| **正式環境 (Production)** | `https://core.newebpay.com` | `https://core.spgateway.com` 或 `https://www.ezpay.com.tw` |
| **測試環境 (Sandbox)** | `https://ccore.newebpay.com` | `https://ccore.spgateway.com` 或 `https://cwww.ezpay.com.tw` |

> **域名歷史脈絡**：
> - `spgateway.com` = 早期 Pay2Go 時代的域名，目前 ezPay 與 Newebpay 後端都仍可解析此域名（向下相容）
> - `ezpay.com.tw` = 簡單付主品牌域名
> - `newebpay.com` = 藍新金流主品牌域名
>
> 三組域名指向**同一套底層金流系統**，路徑與參數完全相同。實際整合時請以 ezPay 後台「商店資料設定」中提供的 URL 為準。

### 端點列表

| 功能 | 路徑 | 說明 |
|------|------|------|
| MPG 交易 | `/MPG/mpg_gateway` | 幕前支付頁面（form POST） |
| 單筆查詢 | `/API/QueryTradeInfo` | 查詢交易狀態 |
| 取消授權 | `/API/CreditCard/Cancel` | 取消信用卡授權 |
| 請款/退款 | `/API/CreditCard/Close` | 信用卡請款 / 退款 |
| 電子錢包退款 | `/API/EWallet/refund` | 錢包類退款 |

### 後台與帳號開通

```
官方網站: https://www.ezpay.com.tw/
後台路徑: 會員中心 > 商店管理 > 商店資料設定 > 串接設定
```

需取得：

- **商店代號 (MerchantID)** — ezPay 發行
- **Hash Key** — 32 字元
- **Hash IV** — 16 字元

> 沙箱測試帳號需自行於 ezPay 後台申請，無公開共用測試 Merchant。

### 測試信用卡

| 卡號 | 備註 |
|------|------|
| `4000-2211-1111-1111` | 一般測試卡（與 Newebpay 共用） |

- **有效期限**：任意未過期日期 (MMYY)
- **CVV**：任意 3 碼

---

## 認證方式

> **與 Newebpay 完全相同**：AES-256-CBC + SHA256。詳細演算法請參考 [`newebpay-payment-api.md`](./newebpay-payment-api.md#加解密機制)。

### TradeInfo 產生流程

```
1. 組合所有交易參數為 query string (key=value&key=value)
2. 以 HashKey 為 key、HashIV 為 IV，AES-256-CBC + PKCS#7 padding 加密
3. 加密結果轉小寫 Hex 字串 → TradeInfo
```

### TradeSha 產生流程

```
TradeSha = SHA256("HashKey={HashKey}&{TradeInfo}&HashIV={HashIV}")
         .toUpperCase()
```

### PHP 範例（與 Newebpay 完全相同）

```php
<?php

class EzPayEncryption
{
    public function __construct(
        private string $hashKey,
        private string $hashIV
    ) {}

    public function encrypt(array $params): string
    {
        $queryString = http_build_query($params);
        $encrypted = openssl_encrypt(
            $queryString,
            'AES-256-CBC',
            $this->hashKey,
            OPENSSL_RAW_DATA,
            $this->hashIV
        );
        return bin2hex($encrypted);
    }

    public function decrypt(string $encryptedData): array
    {
        $data = hex2bin($encryptedData);
        $decrypted = openssl_decrypt(
            $data,
            'AES-256-CBC',
            $this->hashKey,
            OPENSSL_RAW_DATA,
            $this->hashIV
        );
        parse_str($decrypted, $result);
        return $result;
    }

    public function tradeSha(string $tradeInfo): string
    {
        $raw = "HashKey={$this->hashKey}&{$tradeInfo}&HashIV={$this->hashIV}";
        return strtoupper(hash('sha256', $raw));
    }
}
```

### Python 範例

```python
"""ezPay 簡單付 AES-256-CBC 加密（與 Newebpay 共用實作）"""

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from urllib.parse import urlencode, parse_qs
import hashlib


class EzPayEncryption:
    def __init__(self, hash_key: str, hash_iv: str):
        self.hash_key = hash_key.encode('utf-8')
        self.hash_iv = hash_iv.encode('utf-8')

    def encrypt(self, params: dict) -> str:
        query_string = urlencode(params)
        cipher = AES.new(self.hash_key, AES.MODE_CBC, self.hash_iv)
        padded = pad(query_string.encode('utf-8'), AES.block_size)
        return cipher.encrypt(padded).hex()

    def decrypt(self, encrypted_data: str) -> dict:
        data = bytes.fromhex(encrypted_data)
        cipher = AES.new(self.hash_key, AES.MODE_CBC, self.hash_iv)
        decrypted = unpad(cipher.decrypt(data), AES.block_size)
        result = dict(parse_qs(decrypted.decode('utf-8')))
        return {k: v[0] for k, v in result.items()}

    def trade_sha(self, trade_info: str) -> str:
        raw = f"HashKey={self.hash_key.decode()}&{trade_info}&HashIV={self.hash_iv.decode()}"
        return hashlib.sha256(raw.encode('utf-8')).hexdigest().upper()
```

### CheckCode 驗證

回傳結果中的 `CheckCode` 用於驗證金額/訂單編號未被竄改。**規則與 Newebpay 完全相同**：

```php
<?php

function generateCheckCode(array $params, string $hashKey, string $hashIV): string
{
    $checkParams = [
        'Amt' => $params['Amt'],
        'MerchantID' => $params['MerchantID'],
        'MerchantOrderNo' => $params['MerchantOrderNo'],
        'TradeNo' => $params['TradeNo'],
    ];
    ksort($checkParams);
    $paramStr = http_build_query($checkParams);
    $raw = "HashIV={$hashIV}&{$paramStr}&HashKey={$hashKey}";
    return strtoupper(hash('sha256', $raw));
}
```

---

## 訂單建立

### 端點

```
POST {base_url}/MPG/mpg_gateway
```

例：

```
測試: https://ccore.spgateway.com/MPG/mpg_gateway
正式: https://core.spgateway.com/MPG/mpg_gateway
```

### Form 欄位（與 Newebpay 相同）

| 參數 | 必填 | 說明 |
|------|------|------|
| `MerchantID` | ● | ezPay 商店代號 |
| `TradeInfo` | ● | AES 加密後的交易資料 |
| `TradeSha` | ● | SHA256 驗證碼 |
| `Version` | ● | 串接版本，建議 `2.0`（ezPay 沿用較早版本，Newebpay 已升 `2.3`） |
| `EncryptType` | 否 | `0` = AES-256-CBC（預設） |

> **版本差異**：Newebpay 主推 `Version=2.3`（含 GCM 加密選項），ezPay 老商家可能仍維持 `2.0`。實作時請以後台「串接版本」設定為準。

### TradeInfo 內含欄位

完整欄位請參考 [`newebpay-payment-api.md`](./newebpay-payment-api.md#tradeinfo-參數)。以下列出必填核心：

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `MerchantID` | String(15) | ● | ezPay 商店代號 |
| `RespondType` | String(6) | ● | `JSON` 或 `String` |
| `TimeStamp` | String(50) | ● | Unix 時間戳（容許誤差 120 秒） |
| `Version` | String(5) | ● | `2.0` |
| `MerchantOrderNo` | String(30) | ● | 訂單編號（唯一） |
| `Amt` | Int(10) | ● | 訂單金額（新台幣整數） |
| `ItemDesc` | String(50) | ● | 商品資訊 |
| `Email` | String(50) | ● | 付款人 Email（ezPay 強制必填） |
| `LoginType` | Int(1) | ● | `0` = 不需登入會員 |
| `NotifyURL` | String(200) | 否 | 背景通知網址 |
| `ReturnURL` | String(200) | 否 | 付款完成返回網址 |
| `ClientBackURL` | String(200) | 否 | 返回商店按鈕網址 |
| `ExpireDate` | String(8) | 否 | ATM/CVS 繳費期限 `Ymd` |

> **ezPay 特別注意**：`Email` 在 ezPay 為強制必填（Newebpay 部分版本可選填）；`LoginType` 通常固定 `0`，因為 ezPay 簡單付商家很少串接會員系統。

### PHP 範例

```php
<?php

$encryption = new EzPayEncryption($hashKey, $hashIV);

$params = [
    'MerchantID'      => 'EZxxxxxxxx',           // ezPay 發行的 MerchantID
    'RespondType'     => 'JSON',
    'TimeStamp'       => time(),
    'Version'         => '2.0',                  // ezPay 常用版本
    'MerchantOrderNo' => 'ORDER' . time(),
    'Amt'             => 1000,
    'ItemDesc'        => '測試商品',
    'Email'           => 'buyer@example.com',
    'LoginType'       => 0,
    'NotifyURL'       => 'https://your-site.com/ezpay/notify',
    'ReturnURL'       => 'https://your-site.com/ezpay/return',
    'ClientBackURL'   => 'https://your-site.com/cart',
    'CREDIT'          => 1,
    'VACC'            => 1,
    'CVS'             => 1,
];

$tradeInfo = $encryption->encrypt($params);
$tradeSha  = $encryption->tradeSha($tradeInfo);

$action = 'https://ccore.spgateway.com/MPG/mpg_gateway'; // 測試環境

echo <<<HTML
<form id="ezpay" method="post" action="{$action}">
    <input type="hidden" name="MerchantID" value="{$params['MerchantID']}">
    <input type="hidden" name="TradeInfo"  value="{$tradeInfo}">
    <input type="hidden" name="TradeSha"   value="{$tradeSha}">
    <input type="hidden" name="Version"    value="2.0">
    <button type="submit">前往 ezPay 付款</button>
</form>
HTML;
```

---

## 付款通知

> 通知流程、加密驗證、欄位結構**與 Newebpay 完全相同**。詳情請參考 [`newebpay-payment-api.md`](./newebpay-payment-api.md#付款結果通知)。

### 通知流程概覽

1. 付款人完成付款 → ezPay POST 加密資料到 `NotifyURL`（背景）與 `ReturnURL`（前景）
2. 商家收到 `Status` / `MerchantID` / `TradeInfo` / `TradeSha` / `Version`
3. 商家**先驗證 `TradeSha`**，再 AES 解密 `TradeInfo`，取得 `Result` JSON
4. 比對 `MerchantOrderNo` 與資料庫訂單，更新付款狀態
5. **再次驗證 `Result.CheckCode`**（金額竄改防護）
6. 回應 `1|OK` 或任意 200 回應（ezPay 不強制特定字串）

### TradeInfo 解密後 (`Result`) 重點欄位

| 欄位 | 說明 |
|------|------|
| `Status` | `SUCCESS` 表示成功 |
| `MerchantID` | ezPay 商店代號 |
| `Amt` | 交易金額 |
| `TradeNo` | ezPay 交易序號（系統發號） |
| `MerchantOrderNo` | 商家訂單編號 |
| `PaymentType` | 付款方式（CREDIT / VACC / WEBATM / CVS / BARCODE / LINEPAY 等） |
| `PayTime` | 付款時間 |
| `IP` | 付款人 IP |
| `EscrowBank` | 款項保管銀行 |
| `CheckCode` | 金額/訂單防竄改檢核碼（必驗） |

### 處理範例

```php
<?php

$status    = $_POST['Status']    ?? '';
$tradeInfo = $_POST['TradeInfo'] ?? '';
$tradeSha  = $_POST['TradeSha']  ?? '';

$encryption = new EzPayEncryption($hashKey, $hashIV);

// 1. 驗證 TradeSha
if ($tradeSha !== $encryption->tradeSha($tradeInfo)) {
    http_response_code(400);
    echo 'TradeSha mismatch';
    exit;
}

// 2. 解密
$payload = $encryption->decrypt($tradeInfo);
$result  = json_decode($payload['Result'] ?? '{}', true);

// 3. 驗證 CheckCode（防金額竄改）
$expectedCheckCode = generateCheckCode($result, $hashKey, $hashIV);
if (($result['CheckCode'] ?? '') !== $expectedCheckCode) {
    http_response_code(400);
    echo 'CheckCode mismatch';
    exit;
}

// 4. 更新訂單
if (($payload['Status'] ?? '') === 'SUCCESS') {
    updateOrder($result['MerchantOrderNo'], 'paid', $result);
}

echo '1|OK';
```

---

## 退款

> 規則與 Newebpay 完全相同：信用卡走 `/API/CreditCard/Close`，電子錢包走 `/API/EWallet/refund`。完整參數請參考 [`newebpay-payment-api.md`](./newebpay-payment-api.md#請退款取消請退款)。

### 信用卡請款 / 退款

```
POST {base_url}/API/CreditCard/Close
```

| 功能 | CloseType | Cancel |
|------|-----------|--------|
| 請款 | `1` | `-` |
| 退款 | `2` | `-` |
| 取消請款 | `1` | `1` |
| 取消退款 | `2` | `1` |

請求欄位（`PostData_` 內含，AES 加密）：

| 參數 | 必填 | 說明 |
|------|------|------|
| `RespondType` | ● | `JSON` 或 `String` |
| `Version` | ● | `1.1` |
| `Amt` | ● | 請退款金額 |
| `MerchantOrderNo` | ● | 商店訂單編號 |
| `TimeStamp` | ● | Unix 時間戳 |
| `IndexType` | ● | `1`=訂單編號 `2`=交易序號 |
| `TradeNo` | ● | ezPay 交易序號 |
| `CloseType` | ● | `1`=請款 `2`=退款 |
| `Cancel` | 否 | `1`=取消 |

### 退款限制

| 交易類型 | 請款 | 退款 |
|----------|------|------|
| 一次付清 | 整筆 / 部分 | 整筆 / 部分 |
| 分期付款 | 整筆 | 整筆 |
| 紅利折抵 | 整筆 | 整筆 |
| 銀聯卡 | 整筆 | 整筆 / 部分 |

> **ezPay 特別注意**：分期付款在 ezPay 通常受限（許多 ezPay 小型商家方案不支援分期），實際是否可用以後台啟用狀態為準。

### 電子錢包退款

```
POST {base_url}/API/EWallet/refund
```

各錢包退款規則（與 Newebpay 共用）：

| 錢包 | 退款期限 | 部分退款 |
|------|----------|----------|
| 玉山 Wallet | 89 天 | ● |
| 台灣 Pay | 29 天 | ✗（僅全額） |
| LINE Pay | 60 天 | ● |
| TWQR | 89 天 | ● |
| 支付寶 / 微信（簡單付） | 89 天 | ● |

---

## 訂單查詢

> 規則與 Newebpay 完全相同。

### 端點

```
POST {base_url}/API/QueryTradeInfo
```

### 請求欄位

| 參數 | 必填 | 說明 |
|------|------|------|
| `MerchantID` | ● | ezPay 商店代號 |
| `Version` | ● | `1.3` |
| `RespondType` | ● | `JSON` 或 `String` |
| `CheckValue` | ● | 檢查碼（SHA256） |
| `TimeStamp` | ● | Unix 時間戳 |
| `MerchantOrderNo` | ● | 商店訂單編號 |
| `Amt` | ● | 訂單金額 |

### CheckValue 產生

```php
<?php

function generateCheckValue(
    string $amt,
    string $merchantID,
    string $merchantOrderNo,
    string $hashKey,
    string $hashIV
): string {
    $paramStr = "Amt={$amt}&MerchantID={$merchantID}&MerchantOrderNo={$merchantOrderNo}";
    $raw      = "IV={$hashIV}&{$paramStr}&Key={$hashKey}";
    return strtoupper(hash('sha256', $raw));
}
```

### Result 重點欄位

| 欄位 | 說明 |
|------|------|
| `TradeStatus` | `0`=未付款 `1`=成功 `2`=失敗 `3`=取消 `6`=退款 `9`=付款中 |
| `PaymentType` | 支付方式 |
| `CreateTime` / `PayTime` | 建立 / 付款時間 |
| `FundTime` | 預計撥款日 |
| `RespondCode` | 信用卡：`00`=授權成功 |
| `Auth` | 信用卡授權碼 |
| `Card6No` / `Card4No` | 卡號前六碼 / 後四碼 |
| `CloseAmt` / `CloseStatus` | 請款金額 / 狀態 |
| `BackBalance` / `BackStatus` | 可退款餘額 / 退款狀態 |

---

## 錯誤代碼

> ezPay 與 Newebpay **共用同一套錯誤碼系統**（`MPG*` / `TRA*` / `VACC*` / `CVS*` / `KEY*` 等）。

### 常見錯誤碼

| 錯誤碼 | 說明 |
|--------|------|
| `MPG01002` | TimeStamp 不可空白 |
| `MPG01009` | MerchantID 不可空白 |
| `MPG01012` | 訂單編號錯誤（限英數字底線、最長 30 字） |
| `MPG01015` | 金額錯誤 |
| `MPG01023` | TradeInfo 不可空白 |
| `MPG01024` | TradeSha 不可空白 |
| `MPG02001` | 檢查碼錯誤（CheckValue） |
| `MPG02002` | 未啟用金流服務 |
| `MPG02003` | 支付方式未啟用 |
| `MPG03004` | 商店已暫停 |
| `MPG03008` | 訂單編號重複 |
| `MPG03009` | 交易失敗（SHA256 驗證失敗） |
| `TRA10003` | MerchantID 錯誤 |
| `TRA10039` | TradeSha 簽章錯誤 |
| `MPG01007` | 訂單已存在 |
| `VACC10003` | 虛擬帳號逾期 |
| `MPG05002` | 信用卡卡號錯誤 |
| `MPG05005` | 警示交易（疑似盜刷） |

### 交易狀態 (TradeStatus)

| 狀態 | 說明 |
|------|------|
| `0` | 未付款 |
| `1` | 付款成功 |
| `2` | 付款失敗 |
| `3` | 取消付款 |
| `6` | 已退款 |
| `9` | 付款中（待銀行確認） |

### ezPay 後台錯誤碼差異

ezPay 後台額外可能出現的錯誤碼前綴（部分為 ezPay 簡單付電子發票體系沿用）：

| 前綴 | 範圍 |
|------|------|
| `KEY*` | 加密 / 金鑰相關（例：`KEY10011` PostData 欄位空白） |
| `MEM*` | 商店帳號 / 會員相關 |

> 完整錯誤碼以 ezPay 後台「技術串接手冊 PDF」為準。

---

## 支付方式對照表

| 支付方式 | 參數 | ezPay 限制 / 備註 |
|----------|------|-------------------|
| 信用卡一次付清 | `CREDIT=1` | 標準支援 |
| 信用卡分期 | `InstFlag=3,6,12` | **ezPay 多數方案不支援**，需另申請 |
| 紅利折抵 | `CreditRed=1` | 視收單行支援度 |
| 銀聯卡 | `UNIONPAY=1` | 標準支援 |
| 美國運通 | `CREDITAE=1` | 視商家方案 |
| Apple Pay | `APPLEPAY=1` | 標準支援 |
| Google Pay | `ANDROIDPAY=1` | 標準支援 |
| Samsung Pay | `SAMSUNGPAY=1` | 視商家方案 |
| WebATM | `WEBATM=1` | 限 49,999 元以下 |
| ATM 轉帳 | `VACC=1` | 限 49,999 元以下 |
| 超商代碼 | `CVS=1` | 30 ~ 20,000 元 |
| 超商條碼 | `BARCODE=1` | 20 ~ 40,000 元 |
| LINE Pay | `LINEPAY=1` | 標準支援 |
| 玉山 Wallet | `ESUNWALLET=1` | 標準支援 |
| 台灣 Pay | `TAIWANPAY=1` | 限 49,999 元以下 |
| TWQR / 簡單付錢包 | `TWQR=1` | **ezPay 主打方式之一** |
| 微信支付（跨境） | `EZPWECHAT=1` | 跨境交易 |
| 支付寶（跨境） | `EZPALIPAY=1` | 跨境交易 |

> **跨境交易**：ezPay 的 `EZPWECHAT` / `EZPALIPAY` 走「跨境網路交易」獨立 API，請求欄位與境內 MPG 相似但有額外幣別 / 匯率欄位，完整規格請參考 ezPay 後台下載的「跨境網路交易串接手冊」PDF（程式版本 1.0.1）。

---

## 與 Newebpay 差異總表

| 構面 | Newebpay 藍新金流 | ezPay 簡單付 |
|------|-------------------|--------------|
| **公司** | 藍新金流（智冠科技集團） | 簡單行動支付（同集團子品牌） |
| **目標客群** | 中大型商家 | 小型 / 個人商家 |
| **MerchantID 前綴** | `MS` 系列 | `EZ` 系列（依後台簽發為準） |
| **正式環境域名** | `core.newebpay.com` | `core.spgateway.com` 或 `www.ezpay.com.tw` |
| **沙箱域名** | `ccore.newebpay.com` | `ccore.spgateway.com` 或 `cwww.ezpay.com.tw` |
| **API 路徑** | 完全相同 | 完全相同 |
| **加密演算法** | AES-256-CBC + SHA256 | **完全相同** |
| **欄位名稱** | `MerchantID` / `TradeInfo` / `TradeSha` … | **完全相同** |
| **回傳格式** | JSON / String 雙模式 | **完全相同** |
| **錯誤碼** | `MPG*` / `TRA*` / `VACC*` … | **共用同一套** |
| **建議 Version** | `2.3`（含 GCM 選項） | `2.0`（多數老商家） |
| **常見不支援** | – | 分期、部分電子錢包受方案限制 |
| **手續費** | 較低，需簽約 | 較高，但開通快（細節屬商務面，本文不展開） |
| **撥款週期** | 商家自選（最快 T+1） | 通常較長，依方案 |
| **跨境支付** | 完整支援 | 支援，部分功能需另申請 |

### 程式碼遷移指南

**從 Newebpay → ezPay**：通常只需修改三個地方：

```diff
- $merchantID = 'MS12345678';
+ $merchantID = 'EZxxxxxxxx';

- $hashKey = '<newebpay_key>';
- $hashIV  = '<newebpay_iv>';
+ $hashKey = '<ezpay_key>';
+ $hashIV  = '<ezpay_iv>';

- $action = 'https://ccore.newebpay.com/MPG/mpg_gateway';
+ $action = 'https://ccore.spgateway.com/MPG/mpg_gateway';

- $params['Version'] = '2.3';
+ $params['Version'] = '2.0';
```

**從 ezPay → Newebpay**：反向修改三處同樣可運作（前提是已申請對應商家帳號）。

> 共用程式碼建議：將 `BaseURL` / `MerchantID` / `HashKey` / `HashIV` / `Version` 抽成設定檔，只需切換 profile 即可同時支援兩家。

---

## 官方資源

- **官方網站**：https://www.ezpay.com.tw/
- **API 文件下載**：https://www.ezpay.com.tw/info/Service_intro/api_document/member
  - 技術串接手冊 (`ezPay_1.0.2`, 2018-09-25)
  - 交易狀態查詢 (`ezPay_1.0.0`, 2018-09-25)
  - 跨境網路交易串接手冊 (`ezPay_1.0.1`, 2025-05-28)
  - 跨境交易單筆查詢串接手冊 (`ezPay_1.0.1`, 2025-05-28)
  - 跨境交易退款串接手冊 (`ezPay_1.0.3`, 2025-05-28)
  > 下載按鈕為 JS 渲染，需登入後台或於瀏覽器手動點擊「下載」。
- **集團母品牌（金流主流程文件）**：https://www.newebpay.com/
- **公司全名**：簡單行動支付股份有限公司

---

最後更新：2026/05/07
