# PayUni Logistics API Reference

統一金流 (PAYUNi) 物流 API 參考文件。

> **資料來源與可信度**（2026-09 重新查核）
>
> 統一金流的官方文件站 docs.payuni.com.tw 為需登入的 SPA，無法直接擷取。本文件改以**原始碼**為準：
>
> | 項目 | 依據 |
> |---|---|
> | 加解密 | 統一金流官方外掛 PAYUNi_for_WooCommerce 1.2.8、官方 PHP SDK（github.com/payuni/PHP_SDK），並以 `tests/vectors/payuni.json` 逐位元組驗證 |
> | 端點、Version、欄位、代碼、通知格式 | wpbr-payuni-shipping 1.6.4（WordPress.org 上架外掛，實際於正式環境運作）|
>
> 舊版本文件中的 `/logistics/create`、`LogisticsType`、`GoodsAmount`、`Receiver*`、`LogisticsID` 等
> **均不存在於 PAYUNi 物流 API**（其中 `PAYUNi_Logistic_711` 之類的字串其實是 WooCommerce 外掛的運送方式 ID）。

---

## 目錄

1. [API 端點總覽](#api-端點總覽)
2. [加密機制](#加密機制)
3. [代碼定義](#代碼定義)
4. [門市地圖](#門市地圖)
5. [建立物流單](#建立物流單)
6. [查詢物流單](#查詢物流單)
7. [列印託運單](#列印託運單)
8. [NotifyURL 通知](#notifyurl-通知)
9. [尚未查證的項目](#尚未查證的項目)

---

## API 端點總覽

| 環境 | 基礎路徑 |
|------|----------|
| 測試環境 | `https://sandbox-api.payuni.com.tw/api` |
| 正式環境 | `https://api.payuni.com.tw/api` |

| 功能 | 路徑 | Version | 呼叫方式 |
|------|------|---------|----------|
| 7-11 門市地圖 | `/logistics/ship_map` | `1.1` | 瀏覽器表單 POST |
| 建立 7-11 物流單（C2C / B2C） | `/logistics/trade` | `1.1` | 伺服器 POST |
| 建立黑貓宅配物流單 | `/home_delivery/trade` | `1.1` | 伺服器 POST |
| 查詢物流單（7-11 與黑貓共用） | `/logistics/query` | `1.1` | 伺服器 POST |
| 列印 7-11 託運單 | `/logistics/print_label` | `1.0` | 瀏覽器表單 POST |
| 黑貓託運單號 PDF | `/home_delivery/get_obt_number_pdf` | — | 瀏覽器表單 POST |
| 黑貓託運單下載 | `/home_delivery/download_pdf` | — | 瀏覽器表單 POST |

所有請求外層皆為 `application/x-www-form-urlencoded`，只有四個欄位：

| 欄位 | 說明 |
|------|------|
| `MerID` | 商店代號 |
| `Version` | 見上表 |
| `EncryptInfo` | 業務欄位加密後的字串（見加密機制） |
| `HashInfo` | EncryptInfo 的 SHA256 驗證碼 |

回應為 JSON，外層含 `Status`、`EncryptInfo`、`HashInfo`；業務結果（含內層 `Status` / `Message`）在解密後的 EncryptInfo 內。

> 除了獨立的物流 API，PAYUNi 也可在 **UPP 付款時一併建立物流**（在 UPP 的 EncryptInfo 帶
> `Ship`、`ShipTag`、`ShipType`、`LgsType`、`GoodsType`、`Consignee` 等欄位），
> 統一金流官方外掛採用的就是這種方式。見 `taiwan-payment` 的 payuni-payment-api.md。

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

- 物流與金流共用同一組演算法（官方外掛的物流模組直接呼叫同一個類別）
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

完整可執行版本見 `examples/payuni-logistics-cvs-example.py`。

---

## 代碼定義

以下代碼取自 wpbr-payuni-shipping `src/Utils/*.php`。

### ShipType 物流廠商

| 代碼 | 說明 |
|------|------|
| `1` | 7-ELEVEN |
| `2` | 黑貓宅配 |

### LgsType 運送方式

| 代碼 | 說明 |
|------|------|
| `C2C` | 7-11 店到店 |
| `B2C` | 7-11 大宗寄倉 |
| `HOME` | 黑貓宅配 |

### GoodsType 溫層

| 代碼 | 說明 |
|------|------|
| `1` | 常溫 |
| `2` | 冷凍 |
| `3` | 冷藏（黑貓） |

### ServiceType 代收

| 代碼 | 說明 |
|------|------|
| `1` | 取貨付款 |
| `3` | 取貨不付款 |

### DeliveryTimeTag 黑貓配達時段

| 代碼 | 說明 |
|------|------|
| `01` | 13:00 前 |
| `02` | 14:00–18:00 |
| `04` | 不指定（外掛預設） |

### ShipStatus 貨態

| 代碼 | 說明 |
|------|------|
| `21` | 待出貨（已產生單號，等待商店出貨） |
| `22` | 物流中心驗收中（僅超商物流） |
| `92` | 待出貨處理中 / 寄件門市已收件（僅超商物流，C2C） |
| `31` | 配送中 |
| `32` | 待取貨（已配達取件門市） |
| `11` | 已取貨 |

> 退貨、逾期未取等貨態代碼外掛未定義，未列入；實際值以通知中的 `ShipStatus` / `ShipStatusDesc` 為準。

---

## 門市地圖

瀏覽器表單 POST 到 `/logistics/ship_map`（Version `1.1`），EncryptInfo 內容：

| 欄位 | 範例 | 說明 |
|------|------|------|
| `MerID` | | 商店代號 |
| `Timestamp` | `time()` | Unix 時間戳 |
| `GoodsType` | `1` | 溫層 |
| `LgsType` | `C2C` / `B2C` | |
| `ShipType` | `1` | 7-ELEVEN |
| `MapType` | `2` | |
| `MapReturnURL` | | 選完門市後 POST 回的網址 |
| `Tag` | `2` | |
| `MobileTag` | `Y` / `N` | 是否行動裝置版 |

回傳：PAYUNi POST 到 `MapReturnURL`，外層 `Status=SUCCESS`；解密 `EncryptInfo` 後的 `MapJson`
是 JSON 字串，內含 `StoreID`、`StoreName`、`Address`。

---

## 建立物流單

7-11：`POST /logistics/trade`；黑貓：`POST /home_delivery/trade`。Version 皆為 `1.1`。

### EncryptInfo 內容

| 欄位 | 7-11 | 黑貓 | 說明 |
|------|:----:|:----:|------|
| `MerID` | ● | ● | 商店代號 |
| `Timestamp` | ● | ● | Unix 時間戳 |
| `MerTradeNo` | ● | ● | 商店訂單編號 |
| `GoodsType` | ● | ● | 溫層 |
| `LgsType` | ● | ● | `C2C` / `B2C` / `HOME` |
| `ShipType` | ● | ● | `1` / `2` |
| `TradeAmt` | ● | ● | 取貨付款＝代收金額；取貨不付款＝報值金額（外掛限制 30–20000） |
| `ServiceType` | ● | ● | `1` 取貨付款 / `3` 取貨不付款 |
| `StoreID` | ● | 空字串 | 取貨門市（門市地圖回傳） |
| `Consignee` | ● | ● | 收件人姓名 |
| `ConsigneeMail` | ● | ● | 收件人 Email |
| `ConsigneeMobile` | ● | ● | 收件人手機 |
| `RefundStoreID` | ○ | ○ | 退貨門市 |
| `SenderName` | ● | ● | 寄件人姓名 |
| `SenderMobile` | ● | ● | 寄件人手機 |
| `NotifyURL` | ● | ● | 貨態 / 列印結果通知網址 |
| `ConsigneeAddress` | | ● | 收件地址 |
| `ProdDesc` | | ● | 商品描述（外掛截斷為 20 字） |
| `DeliveryTimeTag` | | ● | 配達時段 |

● = 外掛一律帶入　○ = 外掛帶空字串

### 回應（EncryptInfo 解密後）

| 欄位 | 說明 |
|------|------|
| `Status` / `Message` | 業務結果，`SUCCESS` 為成功 |
| `ShipTradeNo` | **UNi 物流序號**，後續查詢、列印、通知都用它對應訂單 |
| `TradeAmt` | 金額 |
| `ServiceType` | 代收類型 |

---

## 查詢物流單

`POST /logistics/query`，Version `1.1`（7-11 與黑貓共用）。

| EncryptInfo 欄位 | 說明 |
|------|------|
| `MerID` | 商店代號 |
| `Timestamp` | Unix 時間戳 |
| `LgsType` | `C2C` / `B2C` / `HOME` |
| `ShipTradeNo` | 建立時取得的 UNi 物流序號 |

回應解密後常見欄位：`ShipTradeNo`、`LgsType`、`ShipType`、`Odno`（出貨編號 / 黑貓託運單號）、
`PartnerId`、`ValidationNo`（C2C）、`FileNo`（黑貓）、`ShipStatus`、`ShipStatusDesc`、`ShipStatusTime`。
值為 `-` 代表尚未產生。

寄件代碼組法（外掛 `build_ship_no`）：C2C 為 `Odno + ValidationNo`；B2C 為 `PartnerId + Odno`；黑貓為 `Odno`。

---

## 列印託運單

### 7-11

瀏覽器表單 POST 到 `/logistics/print_label`，Version `1.0`：

| EncryptInfo 欄位 | 說明 |
|------|------|
| `MerID` / `Timestamp` | |
| `ShipTradeNo` | 可用逗號串接多筆 |
| `GoodsType` / `LgsType` | |
| `ShipType` | `1` |
| `ShipDate` | `YYYYMMDD`；外掛在 B2C 時帶隔天 |
| `LabelMode` | `1` = A4 版型 |

列印結果另以 NotifyURL 通知（`ApiType=Print`）。

### 黑貓

`/home_delivery/get_obt_number_pdf`（取得託運單號）與 `/home_delivery/download_pdf`（下載託運單）。

---

## NotifyURL 通知

PAYUNi 以表單 POST 到建立物流單時帶的 `NotifyURL`，外層含 `EncryptInfo`（與 `HashInfo`）。
**先驗 HashInfo 再解密**（官方外掛收通知時沒有驗，這是外掛的疏漏，不要照抄）。

解密後依 `ApiType` 區分：

| ApiType | 內容 |
|---------|------|
| `ShipStatus` | 貨態更新：`ShipTradeNo`、`ShipStatus`、`ShipStatusDesc`、`ShipStatusTime`；黑貓另含 `OBTNumber`（託運單號）、`FileNo` |
| `Print` | 列印結果：7-11 含 `Odno`、`PartnerId`、`ValidationNo`、`LgsType`；黑貓結果在 `JsonData`（JSON 陣列字串，元素含 `Status`、`ShipTradeNo`） |

內層 `Status` 不是 `SUCCESS` 時代表通知內容為失敗結果。以 `ShipTradeNo` 對應訂單，並比對是否與已存的值相同。

---

## 尚未查證的項目

以下資訊在可取得的原始碼中找不到依據，**不要當成規格使用**，請以統一金流後台提供的正式文件為準：

- NotifyURL 需要回應的內容（外掛未輸出任何特定字串）
- 退貨、逾期未取等貨態代碼
- 各溫層的材積與重量限制、撥款天數
- 取消物流單的 API（外掛未實作）
