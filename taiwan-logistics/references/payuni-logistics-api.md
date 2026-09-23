# PAYUNi 物流 API

統一金流 (PAYUNi) 物流：7-ELEVEN 大宗寄倉 (B2C)／店到店 (C2C)／退貨便 (C2B)、黑貓宅配 (HOME)。

來源：PAYUNi 官方文件 <https://docs.payuni.com.tw/web/#/7>（物流工具、Notify、物流貨態狀態碼 120、物流錯誤代碼 119）。
加解密另以官方外掛 PAYUNi_for_WooCommerce 1.2.8 與官方 PHP SDK 逐位元組比對（`tests/vectors/payuni.json`）。

---

## 目錄

1. [API 一覽](#api-一覽)
2. [加密機制](#加密機制)
3. [建立物流單](#建立物流單)
4. [門市地圖](#門市地圖)
5. [物流單查詢](#物流單查詢)
6. [列印](#列印)
7. [貨態通知](#貨態通知)
8. [代碼](#代碼)

---

## API 一覽

| 環境 | 基礎網址 |
|------|----------|
| 測試 | `https://sandbox-api.payuni.com.tw/api` |
| 正式 | `https://api.payuni.com.tw/api` |

| 功能 | 路徑 | Version | 方式 |
|------|------|---------|------|
| 超商門市地圖 | `/logistics/ship_map` | `1.1` | 前景 Form Post |
| 物流單查詢 | `/logistics/query` | `1.1` | 幕後 POST（header 帶 `User-Agent: payuni`） |
| 超商出貨單列印 | `/logistics/print_label` | `1.0` | 前景 Form Post |
| 黑貓：產宅配編號並下載託運單 PDF | `/home_delivery/get_obt_number_pdf` | `1.0` | 前景 Form Post |
| 黑貓：補下載託運單 PDF | `/home_delivery/download_pdf` | `1.0` | 前景 Form Post |

外層欄位一律為 `MerID`、`Version`、`EncryptInfo`、`HashInfo`；回應外層含 `Status`、`MerID`、`Version`、`EncryptInfo`、`HashInfo`，
業務結果（內層 `Status`／`Message`）在解密後的 EncryptInfo。

---

## 加密機制

```
EncryptInfo = hex( base64(AES-256-GCM 密文) + ":::" + base64(tag) )
HashInfo    = strtoupper( sha256( HashKey + EncryptInfo + HashIV ) )
```

- 明文為 `http_build_query(參數)`；Key = HashKey、nonce = HashIV（16 bytes）；tag 16 bytes
- 常見錯誤：少了最外層 hex、少了 base64 與 `:::`、HashKey 沒放最前面

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

## 建立物流單

官方文件的建立方式是**在交易 API 一併建立**，成功後回傳 `ShipTradeNo`（UNi 物流序號），後續查詢、列印、通知都用它。

### 整合式支付頁 UPP（Version 2.0）

EncryptInfo 加入：

| 欄位 | 說明 |
|------|------|
| `ShipTag` | `1` = 啟用物流（含取貨不付款與取貨付款） |
| `Ship` | `1` = 取貨付款；只帶 `Ship=1` 不帶 `ShipTag` 時僅有取貨付款 |
| `LgsType` | `B2C` 大宗寄倉、`C2C` 店到店、`HOME` 黑貓宅配 |
| `ShipType` | `1` 7-ELEVEN（B2C／C2C）、`2` 黑貓（HOME） |
| `GoodsType` | `1` 常溫、`2` 冷凍、`3` 冷藏（僅黑貓） |
| `Consignee` | 取件人姓名，2–5 個中文字或至少 4 個英文字，超商取件核對身分 |
| `ConsigneeMobile` | `09` 開頭手機 |
| `ConsigneeAddress` | 黑貓收件地址，最長 120 |
| `ConsigneeFix`／`ConsigneeMobileFix`／`ConsigneeAddressFix` | `1` = 支付頁不可修改 |

啟用物流（`Ship=1` 或 `ShipTag=1`）時 `LgsType`、`ShipType`、`GoodsType`、`Consignee`、`ConsigneeMobile` 必填。
回傳 `PaymentType=5`（超商取貨付款）或純取貨時另含 `ShipTradeNo`、`PartnerId`、`ServiceType`、`ShipAmt`、`StoreID`、`StoreName`、`StoreAddr`。

### 幕後交易 API（取貨不付款）

虛擬帳號、超商代碼、信用卡 Token、LINE Pay、街口、AFTEE 幕後 API 皆可帶：

| 欄位 | 說明 |
|------|------|
| `ServiceType` | 固定 `3`（取貨不付款） |
| `Consignee`／`ConsigneeMobile` | 同上 |
| `LgsType`／`GoodsType`／`ShipType` | 同上 |
| `StoreID` | 超商（`ShipType=1`）取件門市代碼 |
| `ConsigneeAddress`、`DeliveryTimeTag` | 黑貓（`ShipType=2`）必填；配達時段 `01` 13 時前、`02` 14–18 時、`04` 不指定 |
| `ConsigneeTelAreaCode`／`ConsigneeTel` | 黑貓選填 |

有物流時 `UsrMail` 必填（視為收件人信箱）。

> `/logistics/trade`、`/home_delivery/trade` 未列於官方文件，只見於第三方外掛 wpbr-payuni-shipping 1.6.4。

---

## 門市地圖

前景 Form Post 到 `/logistics/ship_map`（Version `1.1`）：

| EncryptInfo 欄位 | 必要 | 說明 |
|------|:---:|------|
| `MerID`／`Timestamp` | Y | |
| `MerKeyNo` | Y | 自訂編號，≤20；`Tag=4`、`5` 時帶 UNi 物流序號 |
| `GoodsType` | Y | `1` 常溫、`2` 冷凍 |
| `LgsType` | Y | `B2C`／`C2C` |
| `ShipType` | Y | `1` |
| `MapType` | Y | `1` 僅本島、`2` 含離島；冷凍固定 `2` |
| `MapReturnURL` | C | 有值時選完門市以前景導回 |
| `Tag` | Y | `2` 回傳門市、`3` 更新商店 C2C 退貨門市、`4` 更新物流單取件門市、`5` 更新單筆 C2C 退貨門市 |
| `MobileTag` | C | `Y` 手機版、`N` PC 版（預設） |

回傳 EncryptInfo 的 `MapJson` 為 JSON：`StoreType`（SEVEN）、`StoreID`、`StoreName`、`Address`、`InsularArea`（`I` 本島／`O` 離島）。

門市關轉（貨態 `81`）後須以 `Tag=4` 重選門市：B2C 期限為通知日 +2 天 23:59，C2C 為 +6 天 23:59。

---

## 物流單查詢

`POST /logistics/query`，Version `1.1`：

| EncryptInfo 欄位 | 說明 |
|------|------|
| `MerID`／`Timestamp` | |
| `LgsType` | `B2C`、`C2C`、`HOME`、`C2B`（退貨便） |
| `ShipTradeNo` | B2C／C2C／HOME 必填 |
| `TradeType` | 黑貓：`1` 正物流（預設）、`2` 逆物流 |
| `ReturnOdno` | C2B 必填，12 碼（8 碼退貨便單號 + 4 碼驗證碼） |

回傳：`PartnerId`、`MerTradeNo`、`TradeNo`、`ShipTradeNo`、`Odno`（超商 8 碼／黑貓 12 碼）、`GoodsType`、`LgsType`、`ShipType`、
`ServiceType`、`ShipAmt`、`Consignee`（隱碼）、`ConsigneeMobile`（隱碼）、`ShipStatus`、`PickupStoreType`（貨態 81 時：`1` 取件、`2` 退件門市）、
`ShipStatusDesc`、`ShipStatusTime`；B2C／C2C 另有 `StoreID`、`StoreName`，C2C 有 `ValidationNo`，黑貓有 `FileNo`（24 小時內有效）、`TradeType`、`ConsigneeAddress`。

7-ELEVEN 配送編號：B2C = `PartnerId`(3) + `Odno`(8)；C2C = `Odno`(8) + `ValidationNo`(4)；C2B = `RefundODNO`(8) + `ValidationNo`(4)。

---

## 列印

### 超商出貨單（`/logistics/print_label`，Version `1.0`）

| EncryptInfo 欄位 | 說明 |
|------|------|
| `MerID`／`Timestamp` | |
| `ShipTradeNo` | 最多 50 筆，半形逗號分隔 |
| `GoodsType`／`LgsType`（B2C／C2C）／`ShipType`（1） | |
| `ShipDate` | `YYYYMMDD`，B2C 不得為當日 |
| `LabelMode` | `1` A4（預設）、`2` 直立式 |

C2C 會跳轉至 7-ELEVEN 列印；B2C 由 PAYUNi 直接顯示。列印成功後以 Notify 回傳 `ApiType=Print`、`PartnerId`、`Odno`、`ValidationNo`。

### 黑貓託運單

`/home_delivery/get_obt_number_pdf`（Version `1.0`）：`ShipTradeNo`（逗號分隔）、`GoodsType`、`LgsType=HOME`、`ShipType=2`、
`ShipDate`、`DeliveryDate`（皆 `YYYYMMDD`，須晚於今日且非週日與國定假日）、`Spec`（`1` 60、`2` 90、`3` 120、`4` 150，低溫不支援 150）、
`HideProdDesc`、`Memo`（≤100 位）。`/home_delivery/download_pdf` 以 `FileNo` 補下載（24 小時內）。

---

## 貨態通知

Notify URL 在 PAYUNi 後台「物流設定」填寫（超商與黑貓各自設定）。**先驗 HashInfo 再解密。**

| 類型 | 解密後欄位 |
|------|-----------|
| 超商 B2C／C2C | `Status`、`Message`、`MerID`、`PartnerId`、`ShipTradeNo`、`LgsType`、`GoodsType`、`ShipType`、`ShipStatus`、`PickupStoreType`（僅 81）、`ShipStatusDesc`、`ShipStatusTime`、`ApiType=ShipStatus` |
| 退貨便 C2B | 同上，以 `RefundODNO`、`ValidationNo` 取代 `ShipTradeNo` |
| 黑貓 | `Status`、`Message`、`MerID`、`TradeType`、`ShipTradeNo`、`OBTNumber`、`GoodsType`、`LgsType=HOME`、`ShipType=2`、`FileNo`、`ShipStatus` |

---

## 代碼

### ShipStatus 物流貨態狀態碼（官方 120）

| 代碼 | 名稱 | 備註 |
|------|------|------|
| `91` | 未處理 | 尚未取得出貨單編號 |
| `92` | 處理中 | 僅超商；出貨單編號傳送至上游確認中 |
| `98` | 處理中（已接收） | 僅超商 B2C；已配出貨單編號，待傳物流中心 |
| `21` | 待出貨 | 等待商店出貨 |
| `22` | 物流驗收 | 僅超商；物流中心驗收中 |
| `31` | 配送中 | 超商可能於此階段門市關轉 |
| `32` | 待取貨 | 僅超商；包裹配達門市 |
| `33` | 異常訂單 | 配送過程異常 |
| `11` | 已取貨 | |
| `41` | 已取消 | 商店取消 |
| `43` | 賠償訂單 | |
| `44` | 包裹遺失 | 協尋 18 天未果，走遺失賠償 |
| `46` | 包裹拋棄 | 僅 C2C；賣家未取且逾期未提供宅配資料 |
| `51` | 一般退貨 | 退貨便／黑貓退貨 |
| `52` | 買家未取 | |
| `53` | 廠退 | 僅超商；退回物流中心／黑貓集貨所 |
| `55` | 賣家未取 | 僅 C2C |
| `56` | 已轉宅配退回 | 僅 C2C |
| `81` | 門市關轉 | 須期限內重選門市 |
| `82` | 待轉宅配退回 | 僅 C2C；須於保管期限內提供宅配資料 |

### 錯誤代碼

物流 API 錯誤代碼（官方 119，`API`、`HOME`、`LAB`… 等前綴共 476 碼）收在 `data/status-codes.csv`（`provider=payuni`、`category=error`）。
