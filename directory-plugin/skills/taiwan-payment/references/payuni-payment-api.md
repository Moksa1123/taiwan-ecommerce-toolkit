# PayUni Payment API Reference

> 目錄精簡版：只含參考文件與 JSON 資料，不含腳本。文中提到 `scripts/`、`examples/`、`tests/` 的工具在完整版（npm 套件 `taiwan-payment-skill`）。
> 金鑰與商店代號由使用者自行設定、自行提供；文中的測試帳號是服務商官方公開的測試值，不是真實憑證。帳密類欄位以 `<帳密欄位>` 表示，實際欄名見官方文件。

統一金流 (PAYUNi) 金流 API 參考文件。

> 依據：PAYUNi 官方文件 https://docs.payuni.com.tw/web/#/7 （ShowDoc item 7，各節標註 page id，
> 網頁版為 `https://docs.payuni.com.tw/web/#/7/<page_id>`），以及官方 PHP SDK（github.com/payuni/PHP_SDK）、
> 官方外掛 PAYUNi_for_WooCommerce（github.com/payuni/PAYUNi_for_WooCommerce）。查核日 2026-11-17。

---

## 目錄

1. [API 端點總覽](#api-端點總覽)
2. [測試環境](#測試環境)
3. [加密機制](#加密機制)
4. [通用參數](#通用參數)
5. [整合式支付頁 (UPP)](#整合式支付頁-upp)
6. [信用卡幕後 Token 交易](#信用卡幕後-token-交易)
7. [ATM 虛擬帳號幕後](#atm-虛擬帳號幕後)
8. [超商代碼幕後](#超商代碼幕後)
9. [LINE Pay／AFTEE／街口支付幕後](#line-payaftee街口支付幕後)
10. [交易查詢](#交易查詢)
11. [交易請退款 (信用卡)](#交易請退款-信用卡)
12. [交易取消授權 (信用卡)](#交易取消授權-信用卡)
13. [非信用卡退款、AFTEE 確認、超商代碼取消](#非信用卡退款aftee-確認超商代碼取消)
14. [信用卡約定 (Token)](#信用卡約定-token)
15. [付款結果通知 (Notify)](#付款結果通知-notify)
16. [狀態與錯誤碼](#狀態與錯誤碼)
17. [常見問題排解](#常見問題排解)

---

## API 端點總覽

| 環境 | 基礎路徑 |
|------|----------|
| **測試環境** | `https://sandbox-api.payuni.com.tw/api/` |
| **正式環境** | `https://api.payuni.com.tw/api/` |

- 外層欄位一律為 `MerID`、`Version`、`EncryptInfo`、`HashInfo`（皆必填），`Version` 依各 API 固定值。
- UPP 由消費者瀏覽器表單 POST；其他 API 為伺服器端 HTTP POST，回應為 JSON。官方建議 header 帶 `User-Agent`（建議值 `payuni`），TLS 1.2 以上。
- 幕後 API（信用卡 Token、LINE Pay、AFTEE、街口）須向 PAYUNi 申請開通並綁定 IP。

### 交易建立

| 功能 | 路徑 | Version | 官方 page |
|------|------|---------|-----------|
| 整合式支付頁 UPP | `upp` | `2.0`（`1.0` 仍可用） | 34 |
| 信用卡幕後 Token 交易 | `credit` | `1.3`（`1.2` 仍可用） | 522 |
| ATM 虛擬帳號幕後 | `atm` | `1.3`（`1.2` 仍可用） | 36 |
| 超商代碼幕後 | `cvs` | `1.3`（`1.2` 仍可用） | 37 |
| LINE Pay 幕後 | `linepay` | `1.2`（`1.1` 仍可用） | 326 |
| AFTEE 幕後 | `aftee_direct` | `1.1`（`1.0` 仍可用） | 350 |
| 街口支付幕後 | `jkopay` | `1.1`（`1.0` 仍可用） | 386 |
| 信用卡免跳轉元件 UNi Embed：取得 SDK Token | `iframe/token_get` | `3.0` | 512 |
| 信用卡免跳轉元件 UNi Embed：幕後授權 | `iframe/merchant_trade` | `1.0` | 512 |

「仍可用」的舊版依官方修改記錄（page 25，2026-01-05 優惠券功能升版）；新功能（優惠券、電子發票）只在新版。

### 交易管理

| 功能 | 路徑 | Version | 官方 page |
|------|------|---------|-----------|
| 單筆交易查詢 | `trade/query` | `2.0` | 164 |
| 多筆交易查詢 | `trade/finite_query` | `1.0` | 172 |
| 信用卡請退款 | `trade/close` | `1.0` | 38 |
| 信用卡取消授權 | `trade/cancel` | `1.0` | 39 |
| 超商代碼取消 | `cancel_cvs` | `1.0` | 333 |
| 信用卡 Token 查詢 | `credit_bind/query` | `1.0` | 40 |
| 信用卡 Token 取消 | `credit_bind/cancel` | `1.0` | 41 |
| 愛金卡退款 | `trade/common/refund/icash` | `1.0` | 72 |
| AFTEE 退款 | `trade/common/refund/aftee` | `1.0` | 84 |
| AFTEE 交易確認 | `trade/common/confirm/aftee` | `1.0` | 85 |
| LINE Pay 退款 | `trade/common/refund/linepay` | `1.0` | 300 |
| 街口支付退款 | `trade/common/refund/jkopay` | `1.0` | 377 |

官方 PHP SDK 的 `UniversalTrade()` 以操作名（如 `trade_query`）對應路徑（`trade/query`）；SDK 對照表未收錄 `jkopay`、`trade/common/refund/jkopay`、`trade/finite_query` 與 UNi Embed。

UNi Embed 幕後授權 `iframe/merchant_trade` 的必填欄位：`MerID`、`MerTradeNo`（25 字內，10 分鐘內不可重複）、`Token`（`token_get` 取得）、`TradeAmt`、`Timestamp`、`UsrMail`、`ProdDesc`（page 512，2026-11-18 起 `UsrMail` 改為必填）。

---

## 測試環境

| 項目 | 值 |
|------|------|
| 測試後台 | `https://sandbox.payuni.com.tw` |
| 正式後台 | `https://www.payuni.com.tw` |
| 金鑰 | 登入後台檢視商店串接資訊取得 `MerID`、Hash Key、Hash IV |

### 測試卡號與測試資料（官方 page 374）

| 用途 | 卡號／資料 |
|------|------|
| 一次付清 | `4147631000000001`、`3560511000000001` |
| 一次付清（模擬 3D ECI 不符主動取消授權） | `4147631000000002`、`3560511000000002` |
| 分期付款 | `4147632000000001`（不支援 9 期）、`4741502000000001` |
| 銀聯卡 | `6200000000000001` |
| Apple Pay／Google Pay／Samsung Pay | 不限卡號，測試區皆模擬成功 |
| LINE Pay | Channel ID 與 Channel Secret Key 可填任意數字；不限卡號皆模擬成功 |
| AFTEE | 非會員 `0909999981`；會員 `0909999991`，密碼 `<帳密欄位>` |
| ATM／超商代碼付款完成 | 測試後台「交易動態明細」點「模擬繳費」 |

卡片到期日與背面末三碼可任意填。

---

## 加密機制

PayUni 採用 **AES-256-GCM** 加密與 **SHA256** 驗證碼（HashInfo）。官方說明見 page 29（PHP 範例）、page 56（資料加密陣列）。

> 以下演算法已與統一金流官方外掛 PAYUNi_for_WooCommerce 1.2.8 `class-payuni.php` 的
> `Encrypt()` / `Decrypt()` / `HashInfo()` 逐位元組比對（repo 的 `tests/vectors/payuni.json`）；1.2.9 這三個函式相同。

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

### 外層參數

| 參數 | 必填 | 說明 |
|------|------|------|
| `MerID` | ● | 商店代號，需與 EncryptInfo 內的 `MerID` 一致 |
| `Version` | ● | 各 API 固定值，見[端點總覽](#api-端點總覽) |
| `EncryptInfo` | ● | AES-256-GCM 加密字串 |
| `HashInfo` | ● | SHA256 驗證碼 |

### 交易建立類 API 的共同 EncryptInfo 參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `MerID` | string | ● | 商店代號 |
| `MerTradeNo` | string | ● | 商店訂單編號，長度 25，`[A-Za-z0-9_-]`，10 分鐘內不可重複 |
| `TradeAmt` | int | ● | 訂單金額（整數），各支付工具上下限見下表 |
| `Timestamp` | int | ● | `time()`（Unix 秒） |
| `ProdDesc` | string | ● | 商品說明，長度 550（超出自動截斷），可用半形 `;` 分隔多項 |
| `NotifyURL` | string | 否 | 背景通知網址，完整網址，僅限 80 與 443 port |
| `ReturnURL` | string | 否 | 前景返回網址（Form Post）；交易結果以 NotifyURL 為準 |
| `UsrMail` | string | 條件 | 消費者信箱；開啟物流時必填，電子發票 `CarrierType=amego` 時必填 |

### 訂單金額限制（官方 page 170）

| 支付工具 | 金額範圍 |
|------|------|
| 信用卡 | 1～199,999 元 |
| ATM 轉帳 | 15～49,999 元 |
| 超商代碼 | 30～20,000 元 |
| AFTEE | 20～49,999 元 |
| 超商取貨付款 | 1～20,000 元 |
| 黑貓宅配到付 | 30～20,000 元 |
| icash Pay／LINE Pay／街口支付 | 依各錢包公告 |

### 回應格式

```json
{
  "Status": "SUCCESS",
  "MerID": "商店代號",
  "Version": "版本",
  "EncryptInfo": "加密後的回應資料",
  "HashInfo": "SHA256 驗證碼"
}
```

`Status` 為 `SUCCESS`、`UNKNOWN`、`UNAPPROVED`、`OK`（AFTEE）或錯誤代碼（如 `UPP01007`），見[狀態與錯誤碼](#狀態與錯誤碼)。
EncryptInfo 解密後內另有 `Status`、`Message`。

---

## 整合式支付頁 (UPP)

官方 page 34。導向 PAYUNi 整合式支付頁，消費者選擇付款方式。

### 端點

```
POST https://sandbox-api.payuni.com.tw/api/upp   # 測試
POST https://api.payuni.com.tw/api/upp           # 正式
```

外層 `MerID`、`Version`（`2.0`）、`EncryptInfo`、`HashInfo` 由**消費者瀏覽器**以表單 POST 送出（官方 SDK 的 `HtmlApi()` 即自動送出的表單），不是伺服器端呼叫。

### EncryptInfo 參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `MerID` | string | ● | 商店代號 |
| `MerTradeNo` | string | ● | 長度 25，`[A-Za-z0-9_-]`，10 分鐘內不可重複 |
| `TradeAmt` | int | ● | 訂單金額 |
| `Timestamp` | int | ● | `time()` |
| `ProdDesc` | string | ● | 商品說明，長度 550 |
| `ReturnURL` | string | 否 | 付款完成導回（Form Post）；空值則顯示 PAYUNi 結果頁 |
| `NotifyURL` | string | 否 | 背景通知網址，僅限 80/443 port |
| `BackURL` | string | 否 | 付款頁「返回商店」按鈕網址 |
| `DeepLinkURL` | string | 否 | 有值時不觸發 ReturnURL；僅 icash Pay、LINE Pay、街口、AFTEE 生效；測試環境忽略此欄 |
| `UsrMail` | string | 否 | 付款頁帶入信箱 |
| `UsrMailFix` | int | 否 | `1` = 信箱不可修改 |
| `Cardholder` | int | 否 | `1` = 3D 交易時需輸入持卡人英文名稱 |
| `ExpireDate` | string | 否 | ATM／超商代碼繳費期限 `YYYY-MM-DD`：最少當日；超商代碼最多當日 +7 天，ATM 最多 +180 天；大於 +7 天時付款頁不顯示超商代碼；未帶預設當日 +7 天；設當日須至少留 2 小時繳費時間 |
| `AtmBankType` | string | 否 | 指定 ATM 銀行代碼，逗號分隔（如 `822,004,013`） |
| `TradeLExpireSec` | int | 否 | 付款頁截止秒數 `60`～`600`，預設 `600` |
| `API3D` | int | 否 | `1` = 指定 3D |
| `Union3D` | int | 否 | `1` = 銀聯指定 Unionpay |
| `TradeInvoice` | int | 否 | `1` = 啟用電子發票 |
| `Lang` | string | 否 | `zh-tw`（預設）／`en` |
| 付款方式開關 | int | 否 | 見文末「UPP 開關欄位」；都不帶則依後台商店設定 |

首次信用卡 Token 交易另帶 `CreditToken`（長度 200，`[A-Za-z0-9@.#$%_-+]`）、`UseTokenType`（`1` 約定，消費者可取消／`2` 記憶卡號／`3` 強制約定）、
`CreditShowType`、`CreditTokenType`（`1` 會員（預設）／`2` 商店）、`CreditTokenExpired`（`MMYY`）；買方 Token 帶 `BuyerToken`／`BuyerTokenType`，後續交易帶 `BuyerHash`。
優惠券帶 `Coupon=1`、`CouponNotifyURL`；物流帶 `ShipTag`、`Ship`、`LgsType`、`ShipType`、`GoodsType`、`Consignee`、`ConsigneeMobile` 等（見 `taiwan-logistics`）。

### 回應（ReturnURL／NotifyURL 收到的內容）

外層 `Status`（`SUCCESS`／`UNKNOWN`／`UNAPPROVED` 或錯誤代碼，page 44）、`MerID`、`Version`、`EncryptInfo`、`HashInfo`。EncryptInfo 內：

| 參數 | 說明 |
|------|------|
| `Status` / `Message` | 狀態代碼與說明 |
| `MerTradeNo` / `TradeNo` / `TradeAmt` | 商店訂單編號／UNi 序號／金額 |
| `TradeStatus` | `0` 取號成功、`1` 已付款、`2` 付款失敗、`3` 付款取消、`8` 訂單待確認 |
| `PaymentType` | `1` 信用卡、`2` ATM、`3` 超商代碼、`5` 超商取貨付款、`6` 愛金卡、`7` AFTEE、`9` LINE Pay、`10` 宅配到付、`11` 街口支付 |
| `Gateway` | 固定 `2`（UPP） |
| 信用卡 | `Card6No`、`Card4No`、`CardInst`、`FirstAmt`、`EachAmt`、`ResCode`、`AuthCode`、`AuthBank`、`AuthType`（`1` 一次、`2` 分期、`4` Apple Pay、`5` Google Pay、`6` Samsung Pay、`7` 銀聯、`8` Click to Pay）、`AuthDay`、`AuthTime`、`CreditHash`、`CreditLife`、`CardBank`、`CoBrandCode` |
| ATM | `BankType`、`PayNo`、`PaySet`、`ExpireDate`（`YYYY-MM-DD HH:II:SS`） |
| 超商代碼 | `Store`、`PayNo`、`ExpireDate` |

`UNKNOWN`：60 秒未收到銀行回應；之後有結果會 Notify，或 15 分鐘後以交易查詢確認。

### 支援的付款方式

信用卡（一次付清、分期 3/6/9/12/18/24/30 期、銀聯）、Apple Pay、Google Pay、Samsung Pay、Click to Pay、ATM 虛擬帳號（僅一次性帳號）、超商代碼、icash Pay、AFTEE、LINE Pay、街口支付、超商取貨付款、黑貓宅配到付。
信用卡紅利折抵已於 2025-09-01 下架。

### PHP 範例

```php
<?php

$encryption = new PayuniEncryption($merKey, $merIV);

$params = [
    'MerID' => '<MER_ID>',
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
    <input type="hidden" name="Version" value="2.0">
    <input type="hidden" name="EncryptInfo" value="{$encryptInfo}">
    <input type="hidden" name="HashInfo" value="{$hashInfo}">
    <button type="submit">前往付款</button>
</form>
HTML;

echo $html;
```

---

## 信用卡幕後 Token 交易

> **官方已於 2026-07-01 移除舊版「信用卡幕後(CREDIT)」**（直接帶卡號的幕後授權），改為「信用卡幕後 Token 交易(CREDIT)」
> （官方文件 page 522、修改記錄 page 25）。現行 `/api/credit` **不收卡號**，只能以既有信用卡 Token 授權。

流程：先以整合式支付頁（UPP）或信用卡免跳轉支付元件（UNi Embed）完成首次交易並同意建立 Token，取得 `CreditHash`；
之後以 `CreditHash` 呼叫本 API 進行與持卡人約定的授權。須向 PAYUNi 申請信用卡 Token 機制並綁定幕後授權 IP。

### 端點

```
POST /api/credit          # Version 1.3
```

### EncryptInfo 參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `MerID` | String | ● | 商店代號 |
| `MerTradeNo` | String | ● | 訂單編號，長度 25，`[A-Za-z0-9_-]`，10 分鐘內不可重複 |
| `TradeAmt` | Integer | ● | 訂單金額 |
| `Timestamp` | Integer | ● | `time()` |
| `ProdDesc` | String | ● | 商品說明，長度 550，可用半形 `;` 分隔多項 |
| `UsrMail` | String | 條件 | 開啟物流時必填（視為收件人信箱）；`CarrierType=amego` 時必填 |
| `CreditHash` | String | 否 | 首次 Token 交易回傳的 `CreditHash` |
| `CardInst` | String | 否 | `1` 一次（預設）；`3`,`6`,`9`,`12`,`18`,`24`,`30` 分期 |
| `API3D` | Integer | 否 | `1` = 強制 3D |
| `EnName` | String | 否 | 3D 交易持卡人英文名稱 |
| `ReturnURL` | String | 否 | 僅 `API3D=1` 時使用，3D 完成後導回 |
| `NotifyURL` | String | 否 | 僅補觸發或回覆 `UNKNOWN` 後通知結果使用；限 80/443 port |
| `UserIP` | String | 否 | 消費者 IP（IPv4/IPv6），列入風險管控 |
| `BuyerHash` | String | 條件 | 買方會員 Token Hash；開放交易金額上限且金額超過訂單金額限制時必填 |
| `CarrierType` / `CarrierInfo` / `InvBuyerName` | String | 條件 | 需開立發票時帶入（`3J0002`、`CQ0001`、`amego`、`Donate`、`Company`）；`InvBuyerName` 不可填 `0`、`00`、`000`、`0000` |

優惠碼折抵另帶 `PromoCode`、`DiscountAmt`、`OrderAmt`（皆必填）與 `CouponNotifyURL`。
開啟物流功能時可做取貨不付款（`ServiceType=3`），另帶 `Consignee`、`ConsigneeMobile`、`LgsType`（`B2C`/`C2C`/`HOME`）、
`GoodsType`、`ShipType`（`1` 7-ELEVEN、`2` 黑貓），以及 `StoreID`（超商）或 `ConsigneeAddress`、`DeliveryTimeTag`（黑貓）。

### 回應

`Status`：`SUCCESS`、`UNKNOWN`（60 秒未收到銀行回應，結果之後 Notify 或 15 分鐘後以交易查詢確認）、`UNAPPROVED`。
EncryptInfo 內含 `TradeNo`、`TradeStatus`（`1` 已付款、`2` 失敗、`3` 取消、`8` 待確認）、`AuthCode`、`AuthType`（`1` 一次、`2` 分期、`7` 銀聯）、
`Card6No`、`Card4No`、`CreditHash`、`CreditLife`（`MMYY`）等。`API3D=1` 時回傳 `URL`（3D 導頁網址）。錯誤碼見官方 page 45。

---

## ATM 虛擬帳號幕後

官方 page 36。伺服器端取得 ATM 繳費虛擬帳號。

### 端點

```
POST /api/atm             # Version 1.3
```

### EncryptInfo 參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `MerID` | string | ● | 商店代號 |
| `MerTradeNo` | string | ● | 長度 25，`[A-Za-z0-9_-]`，10 分鐘內不可重複 |
| `TradeAmt` | int | ● | 15～49,999 元 |
| `Timestamp` | int | ● | `time()` |
| `BankType` | string | ● | 銀行代碼：`004` 臺灣銀行、`013` 國泰世華、`822` 中國信託（page 50） |
| `ProdDesc` | string | ● | 商品說明，長度 550 |
| `PaySet` | int | 否 | `1` 單繳帳號（一次性，預設） |
| `ExpireDate` | string | 否 | 繳費截止日 `YYYY-MM-DD`，最少當日、最多當日 +180 天，未帶預設當日 +7 天 |
| `NotifyURL` | string | 否 | 付款完成通知網址，僅限 80/443 port |
| `UsrMail` | string | 條件 | 開啟物流或 `CarrierType=amego` 時必填 |
| `BuyerHash` | string | 條件 | 開放交易金額上限且金額超過限制時必填 |
| `CarrierType` / `CarrierInfo` / `InvBuyerName` | string | 條件 | 需開立發票時帶入 |

另可帶優惠碼參數（`PromoCode`、`DiscountAmt`、`OrderAmt`、`CouponNotifyURL`）與物流取貨不付款參數（同信用卡幕後）。

### 回應參數（EncryptInfo）

| 參數 | 說明 |
|------|------|
| `Status` / `Message` | `SUCCESS`／`(ATM)建立成功`；失敗見錯誤代碼 page 46 |
| `MerTradeNo` / `TradeNo` / `TradeAmt` | 訂單資料 |
| `TradeStatus` | `0` 取號成功 |
| `PaymentType` | `2` |
| `BankType` / `PayNo` | 銀行代碼／繳費虛擬帳號 |
| `PaySet` | `1` 一次性 |
| `ExpireDate` | 繳費截止時間 `YYYY-MM-DD HH:II:SS` |

付款完成後 PAYUNi 送 ATM Notify 到 `NotifyURL`（見[付款結果通知](#付款結果通知-notify)）。

---

## 超商代碼幕後

官方 page 37。伺服器端取得 7-ELEVEN 繳費代碼。

### 端點

```
POST /api/cvs             # Version 1.3
```

### EncryptInfo 參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `MerID` | string | ● | 商店代號 |
| `MerTradeNo` | string | ● | 長度 25，`[A-Za-z0-9_-]`，10 分鐘內不可重複 |
| `TradeAmt` | int | ● | 30～20,000 元 |
| `Timestamp` | int | ● | `time()` |
| `ProdDesc` | string | ● | 商品說明，長度 550 |
| `ExpireDate` | string | 否 | 繳費截止日 `YYYY-MM-DD`，最少當日、最多當日 +7 天；設當日須至少留 2 小時 |
| `NotifyURL` | string | 否 | 僅限 80/443 port |
| `UsrMail` | string | 條件 | 開啟物流或 `CarrierType=amego` 時必填 |
| `CarrierType` / `CarrierInfo` / `InvBuyerName` | string | 條件 | 需開立發票時帶入 |

回應 EncryptInfo 含 `TradeNo`、`TradeStatus`（`0` 取號成功）、`PaymentType`（`3`）、`Store`、`PayNo`、`ExpireDate`。錯誤代碼見 page 47。

---

## LINE Pay／AFTEE／街口支付幕後

皆須向 PAYUNi 申請開通並綁定 IP。共同必填：`MerID`、`MerTradeNo`、`TradeAmt`、`Timestamp`、`ProdDesc`；可帶 `NotifyURL`、`ReturnURL`、`DeepLinkURL`（有值時不觸發 ReturnURL）。

| 支付 | 路徑 | Version | 主要回應欄位 | 錯誤代碼 page |
|------|------|---------|-------------|------|
| LINE Pay（page 326） | `linepay` | `1.2` | `TradeStatus`（`0` 建立、`1` 成功、`2` 失敗）、`PaymentType=9`、`PayNo`、`MethodCode`（`BALANCE`/`CREDIT_CARD`/`POINT`）、`QRToken`（導頁網址）、`QRExpiredTime` | 325 |
| AFTEE（page 350） | `aftee_direct` | `1.1` | `Status`：`SUCCESS` 付款成功、`OK` 審核通過（不代表付款成功）、`UNAPPROVED` 待確認；可帶 `BuyerHash`、`CustName`、`PhoneNo`、`ItemName` 等 | 81 |
| 街口支付（page 386） | `jkopay` | `1.1` | `TradeStatus`（`0`/`1`/`2`）、`PaymentType=11`、`JKoTradeNo`、`JKoStrCupAmt`、`JKoChannel`（`account`/`bank`/`creditcard`） | 387 |

愛金卡（icash Pay）沒有幕後建立 API，經 UPP（`ICash=1`）付款；退款見下節。

---

## 交易查詢

官方 page 164（單筆）、page 172（多筆 `trade/finite_query`）。

### 端點

```
POST /api/trade/query     # Version 2.0（1.0 仍可用）
```

### EncryptInfo 參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `MerID` | string | ● | 商店代號 |
| `MerTradeNo` | string | 二擇一 | 商店訂單編號 |
| `TradeNo` | string | 二擇一 | UNi 序號 |
| `Timestamp` | int | ● | `time()` |

### 回應

可能多筆，解密後資料一律在 **`Result` 陣列**（從 0 開始；PHP `parse_str` 解出 `Result[0][MerTradeNo]`，Python 需自行處理巢狀 key）。

| 參數 | 說明 |
|------|------|
| `MerTradeNo` / `TradeNo` / `TradeAmt` | 訂單資料 |
| `TradeFee` | 手續費；`DataSource=A` 且 `TradeStatus=1` 才正確 |
| `TradeStatus` | 交易狀態（見下表） |
| `PaymentType` | 付款方式代碼（見下表） |
| `CreateDay` / `PaymentDay` | 建立／支付日期 `YYYY-MM-DD HH:II:SS` |
| `Gateway` | `1` 單串、`2` UPP、`3` 一頁式 UOP |
| `DataSource` | `A` 完整資料、`B` 處理中未完整（建議 10 分鐘後再查） |
| 信用卡 | `Card6No`、`Card4No`、`CardExp`、`AuthCode`、`AuthType`、`CloseStatus`、`CloseAmt`、`RefundType`、`RefundStatus`、`RefundAmt`、`RemainAmt` 等 |
| ATM／超商代碼 | `OffChannel`、`OffPayChannel`、`OffPayNo`、`OffExpireTime`、`RefundStatus`（退款轉匯） |

#### TradeStatus 交易狀態

| 狀態 | 說明 |
|------|------|
| `0` | 取號成功 |
| `1` | 已付款 |
| `2` | 付款失敗 |
| `3` | 付款取消 |
| `4` | 交易逾期 |
| `8` | 訂單待確認 |
| `9` | 未付款 |

#### PaymentType 付款方式代碼

| 代碼 | 說明 |
|------|------|
| `1` | 信用卡 |
| `2` | ATM 轉帳 |
| `3` | 超商代碼／條碼 |
| `5` | 超商取貨付款 |
| `6` | 愛金卡 iCash |
| `7` | AFTEE |
| `8` | 退貨代收（C2B 退貨便） |
| `9` | LINE Pay |
| `10` | 宅配到付 |
| `11` | 街口支付 |

#### CloseStatus 請款狀態（信用卡）

| 狀態 | 說明 |
|------|------|
| `1` | 請款申請中 |
| `2` | 請款成功（此時才能以 trade/close + `CloseType=2` 退款） |
| `3` | 請款取消 |
| `7` | 請款處理中 |
| `9` | 未申請 |

`AuthType`：`1` 一次、`2` 分期、`3` 紅利（2025-09-01 起不支援）、`4` Apple Pay、`5` Google Pay、`6` Samsung Pay、`7` 銀聯、`8` Click to Pay。
`RefundStatus`（信用卡）：`1` 退款申請中、`2` 退款成功、`3` 退款取消、`8` 退款處理中；只提供最後一筆退款紀錄。

### PHP 範例

```php
<?php

$encryption = new PayuniEncryption($merKey, $merIV);

$params = [
    'MerID' => '<MER_ID>',
    'MerTradeNo' => 'ORDER1234567890',
    'Timestamp' => time(),
];

$encryptInfo = $encryption->encrypt($params);
$hashInfo = $encryption->hashInfo($encryptInfo);

$response = file_get_contents('https://api.payuni.com.tw/api/trade/query', false, stream_context_create([
    'http' => [
        'method' => 'POST',
        'header' => "Content-Type: application/x-www-form-urlencoded\r\nUser-Agent: payuni",
        'content' => http_build_query([
            'MerID' => $params['MerID'],
            'Version' => '2.0',
            'EncryptInfo' => $encryptInfo,
            'HashInfo' => $hashInfo,
        ]),
    ],
]));

$result = json_decode($response, true);

if ($result['Status'] === 'SUCCESS') {
    $data = $encryption->decrypt($result['EncryptInfo']);
    print_r($data['Result'][0]);
}
```

---

## 交易請退款 (信用卡)

官方 page 38。信用卡請款或退款（平台預設自動請款）。

### 端點

```
POST /api/trade/close     # Version 1.0
```

### EncryptInfo 參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `MerID` | string | ● | 商店代號 |
| `TradeNo` | string | ● | UNi 序號 |
| `Timestamp` | int | ● | `time()` |
| `CloseType` | int | ● | `1` 請款、`2` 退款、`-1` 取消請款、`-2` 取消退款 |
| `TradeAmt` | int | 條件 | 請退款金額；請款、退款時必填 |

回應 EncryptInfo 含 `Status`、`Message`、`MerID`、`TradeNo`、`CloseType`。錯誤代碼見 page 43。

### 限制

- 一次付清、國外卡可全額或部分請退款；分期付款、銀聯卡僅全額
- 授權成功後需於 3 天內請款
- 請款完成後需於 180 天內退款
- 同一筆尚有請款或退款處理中時，新的退款先記為「預計退款」（查詢的 `RefundType=3`）

---

## 交易取消授權 (信用卡)

官方 page 39。已授權、尚未請款的信用卡交易取消授權（一次付清、分期、國外卡）。

### 端點

```
POST /api/trade/cancel    # Version 1.0
```

### EncryptInfo 參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `MerID` | string | ● | 商店代號 |
| `TradeNo` | string | ● | UNi 序號 |
| `Timestamp` | int | ● | `time()` |

錯誤代碼見 page 42。

---

## 非信用卡退款、AFTEE 確認、超商代碼取消

Version 皆為 `1.0`。

| 功能 | 路徑 | EncryptInfo 必填 | 說明 |
|------|------|------|------|
| 愛金卡退款（page 72） | `trade/common/refund/icash` | `MerID`、`TradeNo`、`TradeAmt`、`Timestamp` | 僅全額退款；回 `RefundNo`、`RefundDT` |
| AFTEE 退款（page 84） | `trade/common/refund/aftee` | 同上 | 全額或部分 |
| LINE Pay 退款（page 300） | `trade/common/refund/linepay` | 同上 | 全額或部分 |
| 街口支付退款（page 377） | `trade/common/refund/jkopay` | 同上 | 全額或部分 |
| AFTEE 交易確認（page 85） | `trade/common/confirm/aftee` | `MerID`、`TradeNo`、`Timestamp` | 回 `ConfirmDT` |
| 超商代碼取消（page 333） | `cancel_cvs` | `MerID`、`Timestamp`、`PayNo`（8 或 12 碼） | 消費者已列印繳費單則仍可繳費成功 |

---

## 信用卡約定 (Token)

### 查詢約定信用卡

官方 page 40。

#### 端點

```
POST /api/credit_bind/query
```

#### EncryptInfo 參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `MerID` | String | ● | 商店代號 |
| `CreditToken` | String | 二擇一 | 信用卡 Token（如會員編號、Email），長度 200 |
| `CreditTokenType` | Integer | 否 | `1` 會員（預設）、`2` 商店；用 `CreditHash` 查詢時不用帶 |
| `CreditHash` | String | 二擇一 | 信用卡 Token Hash，長度 64 |
| `Timestamp` | Integer | ● | Unix 時間戳 |

Version 固定 `1.0`。可能有多筆，解密後資料在 `Result` 陣列（`CreditHash`、`CreditTokenStatus` `1` 正常／`3` 刪除／`4` 逾期、`Card6No`、`Card4No` 等）。

### 取消約定信用卡

官方 page 41。

#### 端點

```
POST /api/credit_bind/cancel
```

#### EncryptInfo 參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `MerID` | String | ● | 商店代號 |
| `UseTokenType` | Integer | ● | `1` 綁定（`BindVal` 帶 `CreditHash`）、`2` 記憶卡號（`BindVal` 帶 `CreditToken`） |
| `BindVal` | String | ● | 依 `UseTokenType` 帶 `CreditHash` 或 `CreditToken` |
| `CreditTokenType` | Integer | 否 | `1` 會員（預設）、`2` 商店 |
| `Timestamp` | Integer | ● | Unix 時間戳 |

---

## 付款結果通知 (Notify)

PAYUNi 以 **Form Post** 將結果送到 `NotifyURL`（僅限 80/443 port）。外層欄位：`Status`、`MerID`、`Version`、`EncryptInfo`、`HashInfo`；先驗 HashInfo 再解密。

| 通知 | 官方 page | Version | EncryptInfo 重點欄位 |
|------|------|------|------|
| UPP Notify | 80 | 同交易 | 同 UPP 回應欄位（依 `PaymentType`） |
| ATM 付款完成 | 73 | 依交易版本號 | `TradeNo`、`MerTradeNo`、`NewMerTradeNo`（錯帳或金額不符產生的新單號）、`TradeAmt`、`PayNo`、`PayBank`、`Account5No`、`Gateway`、`TradeStatus`（固定 `1`）、`PayTime` |
| 超商代碼付款完成 | 74 | 依交易版本號 | `TradeNo`、`MerTradeNo`、`NewMerTradeNo`、`TradeAmt`、`PayNo`、`PayStore`、`Gateway`、`TradeStatus`（固定 `1`）、`PayTime` |
| 訂單失效 | 75 | 依交易版本號 | `PaymentType`（`2`/`3`/`6`/`7`/`11`）、`TradeStatus`（固定 `4`）、`PayNo`、`CreateTime` |
| LINE Pay 幕後 | 520 | `1.1` | 同 LINE Pay 幕後回應 |
| 街口支付幕後 | 521 | `1.1` | 同街口支付幕後回應 |
| UNi Embed 3D 交易結果 | 514 | — | 信用卡欄位同信用卡幕後回應 |

- ATM／超商代碼在取號成功時（UPP `TradeStatus=0`）尚未付款；入帳以 `TradeStatus=1` 為準，並比對金額與訂單。
- 官方文件未規定商店回應內容；官方 WooCommerce 外掛處理完直接結束、不輸出特定字串。

### 處理範例

```php
<?php

$encryptInfo = $_POST['EncryptInfo'] ?? '';
$hashInfo = $_POST['HashInfo'] ?? '';

$encryption = new PayuniEncryption($merKey, $merIV);

if (!hash_equals($encryption->hashInfo($encryptInfo), strtoupper($hashInfo))) {
    http_response_code(400);
    exit;
}

$data = $encryption->decrypt($encryptInfo);

if (($_POST['Status'] ?? '') === 'SUCCESS' && ($data['TradeStatus'] ?? '') === '1') {
    // 比對金額後入帳
    updateOrderStatus($data['MerTradeNo'], 'paid', $data);
}
```

---

## 狀態與錯誤碼

完整錯誤代碼見 `data/error-codes-payuni-*.csv`（`search.py "<代碼>" --domain error`），來源為官方「錯誤代碼」各頁（page 156 為所有 API 通用）。

### Status 值

| 值 | 說明 |
|------|------|
| `SUCCESS` | 成功 |
| `UNKNOWN` | 等待授權結果逾期（信用卡、LINE Pay、街口） |
| `UNAPPROVED` | 訂單待確認，買家會員資格審查中 |
| `OK` | AFTEE 審核通過（不代表付款成功） |
| 其他 | 錯誤代碼，如 `UPP01007` |

### 常見錯誤代碼

| 代碼 | 說明 | 處理方式 |
|------|------|----------|
| `DEF01002` | 資料解密失敗 | 檢查 HashKey/HashIV 與 EncryptInfo 格式 |
| `DEF01005` | 商店不存在 | 確認 MerID 與測試／正式環境 |
| `DEF01007` | Hash 比對不符合 | 重新計算 HashInfo（HashKey 在前） |
| `API00002` | 無 API 版本號 | 外層帶 `Version` |
| `API00010` / `API00011` | EncryptInfo／HashInfo 格式錯誤 | 檢查 hex 與 `:::` 格式 |
| `UPP01007` | 已存在相同商店訂單編號 | 使用新的 `MerTradeNo` |
| `UPP02003` / `UPP02004` | 商店訂單編號超過長度／格式錯誤 | 長度 25，`[A-Za-z0-9_-]` |
| `UPP02010` | 時間戳記已過期 | `Timestamp` 用當下 `time()` |

---

## 常見問題排解

### HashInfo 驗證失敗（`DEF01007`）

1. Hash Key 和 Hash IV 是否正確
2. AES-256-GCM 加密是否正確實作
3. **SHA256 計算順序**：必須是 `SHA256(HashKey + EncryptInfo + HashIV)` 而非 `SHA256(EncryptInfo + HashKey + HashIV)`，**Key 必須在前**
4. 測試／正式環境金鑰是否混用

### 訂單編號重複（`UPP01007`）

`MerTradeNo` 長度上限 25，10 分鐘內不可重複：

```python
import time
import random
order_id = f"ORD{int(time.time())}{random.randint(100, 999)}"
```

### 付款通知未收到

1. `NotifyURL` 是否為完整網址且使用 80 或 443 port
2. 伺服器是否能被外網存取、防火牆是否阻擋
3. 信用卡幕後 Token 交易的 `NotifyURL` 只在補觸發或 `UNKNOWN` 後使用，正常結果直接在 API 回應

### 加密／解密問題

1. AES-256-GCM 參數是否正確（Key 32 bytes、IV 16 bytes）
2. Tag 長度是否為 16 bytes
3. **EncryptInfo 格式**：必須是 `hex( base64(密文) + ":::" + base64(Tag) )`，不是 `hex(密文 + tag)`

---

## SDK 資源

| 語言 | GitHub | 備註 |
|------|--------|------|
| PHP | https://github.com/payuni/PHP_SDK | `composer require payuni/sdk`，PHP 7.1+ |
| .NET | https://github.com/payuni/NET_SDK | .NET Framework 4.7.2；NuGet 安裝 Newtonsoft.Json 13.0.1、Portable.BouncyCastle 1.9.0 |
| WooCommerce | https://github.com/payuni/PAYUNi_for_WooCommerce | 官方外掛 |

官方網站 https://www.payuni.com.tw/ ，API 文件 https://docs.payuni.com.tw/web/#/7 ，修改記錄 https://docs.payuni.com.tw/web/#/7/25 。

---

## PAYUNi 支援的付款方式（UPP 開關欄位）

UPP 以「付款方式名稱 = 1」的旗標啟用付款方式（例如 `Credit=1&ATM=1&CVS=1`），**沒有**單一的 `PayType` 參數。
欄位名稱依官方 page 34，大小寫須完全相同：

| 欄位 | 說明 |
|---|---|
| `Credit` | 信用卡一次付清 |
| `CreditInst` | 信用卡分期，值為期數字串（如 `3,6,9,12`），不是 `1` |
| `CreditUnionPay` | 銀聯卡 |
| `ApplePay` / `GooglePay` / `SamsungPay` | 行動支付 |
| `ClickToPay` | Click to Pay（見下方說明） |
| `ATM` | ATM 虛擬帳號（不是 `VACC`） |
| `CVS` | 超商代碼 |
| `ICash` | 愛金卡 |
| `Aftee` | AFTEE 先享後付 |
| `LinePay` | LINE Pay |
| `JKoPay` | 街口支付 |
| `Ship` | 超商取貨付款（搭配物流參數） |

信用卡紅利（`CreditRed`）已於 2025-09-01 下架，官方 page 34 已不列此欄（官方外掛 1.2.9 的 `$paymentArr` 仍保留）。

#### Click to Pay（2026-11-18 起）

- 只在整合式支付頁（UPP）：帶 `ClickToPay=1` 指定開啟；未帶任何指定支付工具參數時依商店後台預設（page 34）。
- 卡別：國內卡、國外卡，不支援銀聯與 JCB（page 34）；官網說明目前支援 Mastercard 與 Visa。
- 回傳與查詢：`AuthType=8`（UPP 回應、單筆／多筆交易查詢 page 164、172、一頁收款 UOP Notify page 53）。
- 幕後信用卡 Token 交易（page 522）與 UNi Embed 免跳轉元件（page 512、513）的文件沒有 Click to Pay。

來源：https://docs.payuni.com.tw/web/#/7/34 、https://docs.payuni.com.tw/web/#/7/25 （修改記錄 2026-11-18）、https://www.payuni.com.tw/click-to-pay （查證 2026-11-18）
