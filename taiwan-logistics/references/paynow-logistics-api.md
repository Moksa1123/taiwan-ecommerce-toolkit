# PayNow Logistics API Reference

立吉富 PayNow 物流 API 完整參考文件，涵蓋 7-11、全家、黑貓、海外配送等 11 條產品線。

---

## 目錄

1. [API 端點總覽](#api-端點總覽)
2. [測試環境與認證](#測試環境與認證)
3. [物流服務代碼](#物流服務代碼)
4. [TripleDES 加密](#tripledes-加密)
5. [PassCode 計算 (SHA-1)](#passcode-計算-sha-1)
6. [選擇物流服務 (電子地圖)](#選擇物流服務-電子地圖)
7. [建立物流訂單](#建立物流訂單)
8. [7-11 大宗物流](#7-11-大宗物流)
9. [7-11 冷凍大宗 B2C](#7-11-冷凍大宗-b2c)
10. [7-11 冷凍店到店 (C2C)](#7-11-冷凍店到店-c2c)
11. [7-11 海外配送](#7-11-海外配送)
12. [全家大宗物流](#全家大宗物流)
13. [全家冷凍大宗 B2C](#全家冷凍大宗-b2c)
14. [全家冷凍店到店 (C2C)](#全家冷凍店到店-c2c)
15. [四大超商常溫 C2C](#四大超商常溫-c2c)
16. [黑貓宅配](#黑貓宅配)
17. [黑貓店到店](#黑貓店到店)
18. [查詢物流單](#查詢物流單)
19. [取消物流單](#取消物流單)
20. [重新取號](#重新取號)
21. [門市更新 (關轉)](#門市更新-關轉)
22. [物流貨態回傳 (Callback)](#物流貨態回傳-callback)
23. [貨態代碼對照表](#貨態代碼對照表)

---

## API 端點總覽

### 基礎網址

| 環境 | 網址 |
|------|------|
| **正式環境** | `https://logistic.paynow.com.tw` |
| **測試環境** | `https://testlogistic.paynow.com.tw` |

> 注意：PayNow 物流 API 與金流共用同一網域結構，但物流走 `logistic.paynow.com.tw`，金流走 `www.paynow.com.tw/service/etopm.aspx`，兩者**不可混用**。

### 主要 API 路徑

| 功能 | API URL | 方法 |
|------|---------|------|
| 選擇物流服務 (電子地圖) | `/Member/Order/Choselogistics` | POST |
| 建立物流訂單 | `/api/Orderapi/Add_Order` | POST |
| 7-11 大宗獲取出貨單號 | `/api/Bulk711Order/ShipBulk711paymentno` | POST |
| 7-11 冷凍大宗獲取出貨單號 | `/api/711FreezingB2C/Ship711B2Cpaymentno` | POST |
| 列印 7-11 大宗物流單 | `/Member/Order/Print711bulkLabel` | POST |
| 列印 7-11 冷凍大宗物流單 | `/Member/Order/Print711FreezingB2CLabel` | POST |
| 列印 7-11 冷凍 C2C 物流單 | `/Member/Order/Print711FreezingC2CLabel` | POST |
| 列印 7-11 海外配送物流單 | `/api/OverSeas711Order` | GET |
| 列印 7-11 交貨便物流單 | `/api/Order711` | GET |
| 列印全家 C2C 物流單 | `/api/OrderFamiC2C` | GET |
| 列印萊爾富物流單 | `/api/OrderHiLife` | GET |
| 列印 OK 物流單 | `/api/OKC2C` | GET |
| 列印黑貓宅急便標籤 | `/Member/Order/PrintBlackCatLabel` | POST |
| 查詢物流單 (PayNow 單號) | `/api/Orderapi/Get_Order_Info` | GET |
| 查詢物流單 (商家訂單編號) | `/api/Orderapi/Get_Order_Info_orderno` | GET |
| 取消物流單 | `/api/Orderapi/CancelOrder` | DELETE |
| 重新取號 | `/api/Orderapi/ReNewOrder` | POST |
| 門市更新 (關轉) | `/api/Orderapi/Put` | PUT |
| 更新物流訂單 (7-11 大宗) | `/api/Bulk711Order/UpdateB2C711Order` | PUT |
| 更新物流訂單 (7-11 冷凍 B2C) | `/api/711FreezingB2C/Update711B2COrder` | PUT |
| 建立 7-11 退貨物流單 | `/api/Orderapi/ReturnPaymentno` | PUT |
| 7-11 海外配送-國家代碼 | `/api/OverSeas711Order/SelCountryID` | POST |
| 7-11 海外配送-運費試算 | `/api/Orderapi/SelWeightChart` | POST |
| 7-11 海外配送-費用查詢 (依訂單) | `/api/OverSeas711Order/SelBillDetail` | POST |
| 7-11 海外配送-費用查詢 (依日期) | `/api/OverSeas711Order/SelBillDetailDate` | POST |
| 全家 C2C 店號轉換 | `/api/OrderFamiC2C/GetFamiStoreID` | GET |
| 全家冷凍店鋪空間保留 | `/api/FamiFreezingB2C/UpSpaceConfirm` | POST |

---

## 測試環境與認證

### 認證資料

PayNow 物流 API 使用「商家主帳號 (`user_account`) + API 密碼 (`apicode`)」雙鑰機制，並透過 TripleDES 加密 + SHA-1 PassCode 雙重保護。

| 項目 | 說明 |
|------|------|
| `user_account` | 商家主帳號，10 碼 |
| `apicode` | 商家 API 密碼，30 碼，請以 TripleDES 加密後傳送 |
| `partner_token` | 合作夥伴識別碼 (HTTP Header 帶入)，用於回傭計算，非必填 |

### partner_token (合作夥伴識別)

`partner_token` 為 HTTP Header 參數，用於辨識合作夥伴身份並計算回傭：

```http
POST /api/Orderapi/Add_Order HTTP/1.1
Host: logistic.paynow.com.tw
Content-Type: application/x-www-form-urlencoded
partner_token: YOUR_PARTNER_TOKEN
```

注意事項：

- `partner_token` 為合作夥伴專屬識別碼，請妥善保管，不同合作夥伴的 token 不可共用
- 如 token 遺失或洩漏，請立即聯繫 PayNow 申請更換
- 未提供 `partner_token` 或 token 錯誤時，訂單仍可正常建立，但無法正確計算回傭

### 取得測試帳號

請聯繫 PayNow 客服 (`service@paynow.com.tw`) 申請測試環境帳號，取得：

- 測試 `user_account`
- 測試 `apicode`
- TripleDES 公鑰 (8 bytes)
- TripleDES 私鑰 (24 bytes)

---

## 物流服務代碼

PayNow 物流以 `Logistic_serviceID` (對應建立訂單的 `Logistic_service` 欄位) 區分產品線：

| Service ID | 物流服務 | 類型 |
|------------|----------|------|
| `01` | 7-11 交貨便 | C2C 常溫 |
| `02` | 7-11 大宗物流 | B2C 常溫 |
| `03` | 全家店到店 | C2C 常溫 |
| `04` | 全家大宗物流 | B2C 常溫 |
| `05` | 萊爾富店到店 | C2C 常溫 |
| `06` | 黑貓宅急便 | 宅配 |
| `07` | 7-11 海外配送 (店配) | 跨境店配 |
| `08` | 7-11 海外配送 (宅配) | 跨境宅配 |
| `10` | OK 店到店 | C2C 常溫 |
| `12` | 7-11 大宗退貨便 | 退貨 |
| `21` | 7-11 交貨便 (冷凍) | C2C 冷凍 |
| `22` | 7-11 大宗物流 (冷凍) | B2C 冷凍 |
| `23` | 全家店到店物流 (冷凍) | C2C 冷凍 |
| `24` | 全家大宗物流 (冷凍) | B2C 冷凍 |
| `36` | 黑貓宅急便 (PayNow) | 宅配 (含自動保險) |
| `46` | 黑貓到店 (PayNow) | 店到店 |

---

## TripleDES 加密

PayNow 物流的 `JsonOrder` 與 `apicode` 都需使用 TripleDES 加密後再 URLEncode 傳送，**這是與一般 PayNow 金流動態 AES-256 不同的加密機制**，物流端固定為 3DES/ECB/Zero Padding。

### 加密規格

| 項目 | 值 |
|------|-----|
| 演算法 | 3DES (TripleDES) |
| 模式 | ECB |
| Padding | Zero Padding |
| 公鑰 (IV) | 8 bytes (例：`12345678`) |
| 私鑰 (Key) | 24 bytes (例：`123456789070828783123456`) |
| 編碼輸出 | Base64，並把空白字元 `' '` 換成 `+` |

### 加解密前後範例 (摘自官方附錄)

加密前：

```json
{"mem_type":2,"buysafeno":"8000001910145799460","mem_cid":"13099407","passcode":"2B24518AA4C2536CAF7ADCBC635C0751699BB7CC", ...}
```

加密後 (Base64)：

```
229d7b9b639845a7f12cc8524a3988ce77647ced3cacec907bf5432b2df9f7a68055b05204f29d8e1b0ca4c9...
```

### C# 範例 (官方)

```csharp
public string Encrypt(string content)
{
    TripleDes.IV = Encoding.UTF8.GetBytes("12345678");
    TripleDes.Key = Encoding.UTF8.GetBytes("123456789070828783123456");
    TripleDes.Mode = CipherMode.ECB;
    TripleDes.Padding = PaddingMode.Zeros;

    var data = Encoding.UTF8.GetBytes(content);
    var ict = TripleDes.CreateEncryptor();
    var enc = ict.TransformFinalBlock(data, 0, data.Length);
    var result = Convert.ToBase64String(enc).Replace(' ', '+');

    return result;
}
```

### PHP 範例

```php
<?php

function tripleDesEncrypt(string $content, string $key, string $iv): string
{
    // 補齊 24 bytes 並使用 ECB；OpenSSL 需手動 zero-pad
    $blockSize = 8;
    $padLen = $blockSize - (strlen($content) % $blockSize);
    if ($padLen !== $blockSize) {
        $content .= str_repeat("\0", $padLen);
    }

    $encrypted = openssl_encrypt(
        $content,
        'des-ede3',
        $key,
        OPENSSL_RAW_DATA | OPENSSL_ZERO_PADDING
    );

    return str_replace(' ', '+', base64_encode($encrypted));
}

// 使用
$key = '123456789070828783123456';   // 24 bytes
$iv  = '12345678';                    // 8 bytes (ECB 模式不會用到，但 spec 仍要傳)
$jsonOrder = json_encode($orderData, JSON_UNESCAPED_UNICODE);
$encrypted = tripleDesEncrypt($jsonOrder, $key, $iv);
$postBody  = 'JsonOrder=' . urlencode($encrypted);
```

### Python 範例

```python
from Crypto.Cipher import DES3
import base64

def triple_des_encrypt(content: str, key: str) -> str:
    """PayNow 物流 TripleDES/ECB/Zero Padding"""
    block_size = 8
    data = content.encode('utf-8')
    pad_len = block_size - (len(data) % block_size)
    if pad_len != block_size:
        data += b'\x00' * pad_len

    cipher = DES3.new(key.encode('utf-8'), DES3.MODE_ECB)
    encrypted = cipher.encrypt(data)
    return base64.b64encode(encrypted).decode('ascii').replace(' ', '+')

# 使用
key = '123456789070828783123456'  # 24 bytes
encrypted = triple_des_encrypt(json_str, key)
```

---

## PassCode 計算 (SHA-1)

PassCode 為 PayNow 物流防偽用雜湊值，作法為：將指定欄位依序串接後計算 SHA-1，輸出 40 字元大寫十六進位字串。

### 通用組成方式

| 情境 | PassCode 組成 |
|------|---------------|
| 建立物流訂單 | `user_account + OrderNo + TotalAmount + apicode` |
| 7-11 大宗獲取出貨單號 | `user_account + apicode` |
| 重新取號 | `user_account + OrderNo + TotalAmount + apicode` |
| 取消訂單 | `user_account + OrderNo + TotalAmount + apicode` |
| 門市更新 (關轉) | `user_account + OrderNo + TotalAmount + apicode` |
| 建立退貨物流單 | `user_account + LogisticNumber + apicode` |

> 串接時 **不包含 `+` 符號**，僅是數值連接 (concat)。
> 例：`user_account=28229955`、`OrderNo=211210165125`、`TotalAmount=200`、`apicode=12345678` → `2822995521121016512520012345678` → SHA-1 → `4CF47FD844DF64C5D0FBF8DD134708B55ABE208B`

### C# 範例 (官方)

```csharp
public string SHA1Encrypt(string data)
{
    SHA1CryptoServiceProvider sha1 = new SHA1CryptoServiceProvider();
    var keyBytes = Encoding.Default.GetBytes(data);
    var hash = sha1.ComputeHash(keyBytes);
    return BitConverter.ToString(hash).Replace("-", "");
}
```

### PHP 範例

```php
<?php

function generatePassCode(array $parts): string
{
    return strtoupper(sha1(implode('', $parts)));
}

// 建立物流訂單
$passCode = generatePassCode([
    $userAccount,    // 28229955
    $orderNo,        // 211210165125
    $totalAmount,    // 200
    $apicode,        // 12345678
]);
// → 4CF47FD844DF64C5D0FBF8DD134708B55ABE208B
```

### Python 範例

```python
import hashlib

def generate_pass_code(*parts: str) -> str:
    raw = ''.join(parts)
    return hashlib.sha1(raw.encode('utf-8')).hexdigest().upper()

pass_code = generate_pass_code(user_account, order_no, str(total_amount), apicode)
```

---

## 選擇物流服務 (電子地圖)

### 端點

```
POST /Member/Order/Choselogistics
```

### 通用參數

| 參數 | 名稱 | 型態 | 長度 | 必填 | 說明 |
|------|------|------|------|------|------|
| `user_account` | 商家主帳號 | string | 10 | ● | |
| `orderno` | 訂單編號 | string | 27 | 否 | 帶入後將原樣回傳 |
| `apicode` | 商家 API 密碼 | string | 30 | ● | 須以 TripleDES 加密 |
| `Logistic_serviceID` | 物流服務 ID | string | 2 | ● | 詳見下表 |
| `returnUrl` | 回傳網址 | string | 200 | ● | 使用者選擇門市後 PayNow 會 POST 至此 |

### 各物流的 Logistic_serviceID 對照

| 服務 | Logistic_serviceID |
|------|-------------------|
| 4 大超商常溫 (依輸入導向對應地圖) | `01` / `03` / `05` / `10` |
| 7-11 大宗物流 | `02` (固定) |
| 7-11 大宗物流 (冷凍) | `22` |
| 7-11 交貨便 (冷凍) | `21` 或 `22` |
| 7-11 海外配送 (店配) | `07` (額外帶 `Country`) |
| 全家大宗物流 | `04` |
| 全家店到店 (冷凍) | `23` |
| 全家大宗 (冷凍) | `24` (額外帶 `Length`/`Wide`/`High`/`Weight`/`StartDate`/`EndDate`) |
| 黑貓店到店 | `46` |

### 海外配送專用參數 (Logistic_serviceID=07)

| 參數 | 必填 | 說明 |
|------|------|------|
| `Country` | ● | `SG`/`MY`/`HK`/`MO`/`TH`，全部國家輸入 `ALL` |

### 全家冷凍大宗專用參數 (Logistic_serviceID=24)

| 參數 | 必填 | 說明 |
|------|------|------|
| `Length` | ● | 長 (cm)，依申請材積 S60 (長+寬+高<60) 或 S105 |
| `Wide` | ● | 寬 (cm) |
| `High` | ● | 高 (cm) |
| `Weight` | ● | 重量 (公克)，未填請填空字串 |
| `StartDate` | ● | 出貨日起 `yyyy-MM-dd`，未填請填空字串 |
| `EndDate` | ● | 出貨日迄 `yyyy-MM-dd` |
| `Ecplateform` | ● | EC 平台代碼 |

### 回傳參數

| 參數 | 說明 |
|------|------|
| `orderno` | 商家訂單編號 (如有帶入) |
| `service` | 物流服務代碼 |
| `storeid` | 店 ID |
| `storename` | 店名 |
| `storeaddress` | 店址 |
| `ReservedNo` | 保留編號 (僅冷凍 24/23 服務回傳) |
| `ShipDate` | 出貨日期 `yyyy-MM-dd` (僅冷凍 24/23 服務回傳) |

### PHP 範例 - 開啟電子地圖 (iframe)

```php
<?php

$apicodeEncrypted = tripleDesEncrypt('12345678', $key, $iv);

$html = <<<HTML
<form id="map-form" method="post"
      action="https://testlogistic.paynow.com.tw/Member/Order/Choselogistics"
      target="map-iframe">
    <input type="hidden" name="user_account" value="28229955">
    <input type="hidden" name="orderno" value="ORDER123">
    <input type="hidden" name="apicode" value="{$apicodeEncrypted}">
    <input type="hidden" name="Logistic_serviceID" value="02">
    <input type="hidden" name="returnUrl" value="https://your-site.com/store_callback">
</form>
<iframe name="map-iframe" width="100%" height="600"></iframe>
<script>document.getElementById('map-form').submit();</script>
HTML;
```

---

## 建立物流訂單

所有物流產品線共用同一支 API，由 `Logistic_service` 參數判斷實際服務。

### 端點

```
POST /api/Orderapi/Add_Order
Content-Type: application/x-www-form-urlencoded
```

### Request

| 參數 | 必填 | 說明 |
|------|------|------|
| `JsonOrder` | ● | `JsonOrder Content` 物件 → JSON 字串 → TripleDES 加密 → URLEncode |

### JsonOrder Content (通用欄位)

| 參數 | 名稱 | 型態 | 長度 | 必填 | 說明 |
|------|------|------|------|------|------|
| `user_account` | 商家主帳號 | string | 10 | ● | |
| `apicode` | 商家 API 密碼 | string | 30 | ● | (整個 JsonOrder 會再次加密) |
| `Logistic_service` | 物流服務代碼 | string | 2 | ● | 見 [物流服務代碼](#物流服務代碼) |
| `OrderNo` | 商家訂單編號 | string | 27 | ● | 限英文與數字 |
| `DeliverMode` | 取貨是否付款 | string | 2 | ● | `01`:取貨付款 `02`:取貨不付款 |
| `TotalAmount` | 總金額 | string | 5 | ● | 正整數，超商不可大於 20,000，黑貓不可大於 100,000 |
| `Remark` | 備註 | string | 200 | ● | 不帶值請填空字串 |
| `Description` | 單號描述 | string | 50 | ● | 黑貓另有商品分類代碼 |
| `EC` | EC 平台 | string | 50 | 否 | |
| `receiver_storeid` | 取件店號 | string | 30 | ● (超商) | 宅配填空字串 |
| `receiver_storename` | 取件店名 | string | 100 | ● (超商) | |
| `return_storeid` | 退件店號 | string | 6 | ● | 不帶值請填空字串 |
| `Receiver_Name` | 收件人姓名 | string | 10~30 | ● | 各物流長度限制不同 |
| `Receiver_Phone` | 收件人手機 | string | 10 | ● | |
| `Receiver_Email` | 收件人 EMAIL | string | 100 | ● | |
| `Receiver_address` | 收件人地址 | string | 150 | ● | |
| `Sender_Name` | 寄件人姓名 | string | 10 | ● | 大宗類型可填空字串自動帶入「立吉富」 |
| `Sender_Phone` | 寄件人手機 | string | 10 | ● | 大宗類型可填空字串自動帶入「0900000000」 |
| `Sender_Email` | 寄件人 EMAIL | string | 100 | ● | |
| `Sender_address` | 寄件人地址 | string | 150 | ● | |
| `PassCode` | 傳遞碼 | string | 40 | ● | SHA-1(`user_account + OrderNo + TotalAmount + apicode`) |
| `Deadline` | 預定出貨天數 | int |  | (大宗) | 1~7，預定出貨日 = 建單日 + Deadline |

### Ibon 禁用字元 (7-11 訂單)

7-11 大宗、冷凍、海外配送等系列均不可在欄位中包含以下字元：

```
'  "  %  |  &  `  ^  @  !
.  #  (  )  *  _  +  -  ;  :  ,
```

### 通用 Response 欄位

| 參數 | 說明 |
|------|------|
| `Status` | `S` 成功 / `F` 失敗 |
| `LogisticNumber` | PayNow 物流單號 (主要追蹤鍵) |
| `LogisticService` | 物流服務名稱 |
| `LogisticServiceID` | 物流服務代碼 |
| `paymentno` | 物流商貨運編號 (部分服務在此即回傳) |
| `validationno` | 驗證碼 (7-11 店到店回傳，配合 paymentno 至 Ibon 列印) |
| `orderno` | 商家訂單編號 |
| `ErrorMsg` | 失敗時為錯誤訊息，成功為 `null` |
| `ReturnMsg` | 額外回傳訊息 |

---

## 7-11 大宗物流

服務代碼：`02` / 退貨便：`12` / 文件版本：`711Bulk-API V2.4`

### 流程

1. `/Member/Order/Choselogistics` 開啟電子地圖選擇取件門市
2. `/api/Orderapi/Add_Order` 建立物流訂單，取得 `LogisticNumber`
3. `/api/Bulk711Order/ShipBulk711paymentno` 獲取出貨單號 (`paymentno` / 配送編號)
4. `/Member/Order/Print711bulkLabel` 列印物流標籤
5. 於物流標籤上的「門市進貨日 = 建單日 + Deadline」當天進倉

### 進貨日規則

- `Deadline` 必須是 1~7 之間的整數
- 預定出貨日 = 建立物流單日 + Deadline
  - 例：建單日 `2021/03/14`，`Deadline=3` → 預定出貨日 `2021/03/17`
- 不可提前到貨，提前到貨會被刷退
- 已超過預定出貨日：
  - 未列印過標籤：門市進貨日自動變更為「列印日 + 1 天」
  - 已列印過標籤：必須重新取號再列印新標籤

### 重新取號規則

- 必須等物流驗收後且未取貨才能重新取號
- 配對新出貨單號後仍要回到列印 7-11 大宗物流頁面列印新標籤
- 已是貨態 `1000` (上傳中)、`1050` (上傳成功)、`8000` (已取件) 無法重取

### 獲取出貨單號

```
POST /api/Bulk711Order/ShipBulk711paymentno
```

JsonOrder Content：

```json
{
  "user_account": "28229955",
  "apicode": "12345678",
  "PassCode": "625B528740B1860CA5392E2CA2B577066596A160",
  "ShipList": [
    { "LogisticNumber": "MIJA0027B22112100002", "sno": "1" }
  ]
}
```

> PassCode 此 API 採 `SHA-1(user_account + apicode)`，與一般訂單不同。

Response (Object Array)：

```json
[
  {
    "LogisticNumber": "MIJA0027B22112100002",
    "sno": "1",
    "paymentno": "82900502030",
    "ErrorMsg": null
  }
]
```

### 列印物流單

```
POST /Member/Order/Print711bulkLabel
```

| 參數 | 必填 | 說明 |
|------|------|------|
| `LogisticNumbers` | ● | `Paynow物流單號_物流單子序號`，多筆以 `,` 分隔，例：`ABCD0017B21903001221_1,ABCD0017B21903001270_1` |

### 建立退貨物流單

```
PUT /api/Orderapi/ReturnPaymentno
Content-Type: application/x-www-form-urlencoded
```

JsonOrder Content：

```json
{
  "user_account": "28229955",
  "apicode": "12345678",
  "LogisticNumber": "MIJA0027B22112100002",
  "LogisticServiceID": "02",
  "PassCode": "24BCF048A550B56D74F9C342DCFA3FA01DBD2AFB"
}
```

> 退貨 PassCode 為 `SHA-1(user_account + LogisticNumber + apicode)`。

Response：

```json
{
  "Status": "S",
  "LogisticNumber": "MIJA0027R42112130001",
  "LogisticService": "7-11大宗退貨便",
  "LogisticServiceID": "12",
  "paymentno": "A47058871088",
  "ReturnMsg": "",
  "orderno": "MIJA0027B22112100002",
  "ErrorMsg": null
}
```

消費者持 `paymentno` 至 Ibon 機台輸入即可列印退貨物流單。

### 更新訂單 (尚未出貨)

```
PUT /api/Bulk711Order/UpdateB2C711Order
```

可改：`receiver_storeid`、`receiver_storename`、`Receiver_Name`、`Receiver_Phone`。
PassCode 為 `SHA-1(user_account + Orderno + TotalAmount + apicode)`。

### 完整建立 PHP 範例

```php
<?php

$payload = [
    'user_account'        => '28229955',
    'apicode'             => '12345678',
    'Logistic_service'    => '02',
    'OrderNo'             => '211210165125',
    'DeliverMode'         => '02',
    'TotalAmount'         => '200',
    'Remark'              => '',
    'Description'         => 'test',
    'receiver_storeid'    => '126616',
    'receiver_storename'  => '立行門市',
    'return_storeid'      => '',
    'Receiver_Name'       => '收件測',
    'Receiver_Phone'      => '0912345678',
    'Receiver_Email'      => '123@paynow.com.tw',
    'Receiver_address'    => '新北市三重區力行路二段158號160號',
    'Sender_Name'         => '',
    'Sender_Phone'        => '',
    'Sender_Email'        => 'test@paynow.com.tw',
    'Sender_address'      => '',
    'Deadline'            => 1,
];
$payload['PassCode'] = strtoupper(sha1(
    $payload['user_account'] . $payload['OrderNo'] .
    $payload['TotalAmount'] . $payload['apicode']
));

$json    = json_encode($payload, JSON_UNESCAPED_UNICODE);
$encJson = tripleDesEncrypt($json, '123456789070828783123456', '12345678');

$ch = curl_init();
curl_setopt_array($ch, [
    CURLOPT_URL => 'https://testlogistic.paynow.com.tw/api/Orderapi/Add_Order',
    CURLOPT_POST => true,
    CURLOPT_POSTFIELDS => http_build_query(['JsonOrder' => $encJson]),
    CURLOPT_HTTPHEADER => ['partner_token: YOUR_PARTNER_TOKEN'],
    CURLOPT_RETURNTRANSFER => true,
]);
$response = json_decode(curl_exec($ch), true);
curl_close($ch);
```

---

## 7-11 冷凍大宗 B2C

服務代碼：`22` / 文件版本：`711FreezingBulkB2C V2.4`

流程與 7-11 常溫大宗類似，差異：

- 電子地圖 `Logistic_serviceID=22`
- 建單時 `Logistic_service=22`
- 出貨單號 API：`POST /api/711FreezingB2C/Ship711B2Cpaymentno`
- 列印標籤 API：`POST /Member/Order/Print711FreezingB2CLabel`
- 列印標籤後**隔日進行出貨**，進店日由物流商分配 (不需 `Deadline`)
- 更新訂單 API：`PUT /api/711FreezingB2C/Update711B2COrder`

關轉 (門市更新) 必須在收到 `4036` 貨態代碼後 `D+2 上午 10:50` 前處理，逾期則無法關轉。

範例 Response：

```json
{
  "Status": "S",
  "LogisticNumber": "MIJA0027F22112140001",
  "LogisticService": "7-11大宗物流冷凍",
  "LogisticServiceID": "22",
  "ReturnMsg": "",
  "orderno": "211214141817",
  "ErrorMsg": null
}
```

---

## 7-11 冷凍店到店 (C2C)

服務代碼：`21` / 文件版本：`711FreezingC2C V2.0`

### 流程

1. 電子地圖選店 (`Logistic_serviceID=22`，注意：建單時改用 `21`)
2. 建立物流訂單，回傳 `LogisticNumber` + `paymentno` + `validationno`
3. 列印標籤：`POST /Member/Order/Print711FreezingC2CLabel`
4. 列印後隔日出貨

### 建單範例

Request：

```json
{
  "user_account": "28229955",
  "apicode": "12345678",
  "Logistic_service": "22",
  "OrderNo": "211214141817",
  "DeliverMode": "02",
  "TotalAmount": "200",
  "Remark": "",
  "Description": "test",
  "receiver_storeid": "183413",
  "receiver_storename": "八仙門市",
  "return_storeid": "",
  "Receiver_Name": "收件測",
  "Receiver_Phone": "0912345678",
  "Receiver_Email": "123@paynow.com.tw",
  "Receiver_address": "新北市八里區中華路二段290號292號296號",
  "Sender_Name": "寄件測",
  "Sender_Phone": "0900000000",
  "Sender_Email": "test@paynow.com.tw",
  "Sender_address": "",
  "PassCode": "08D6038DFDA1AF0412CBA925135DC33F31C928A1"
}
```

Response：

```json
{
  "Status": "S",
  "LogisticNumber": "MIJA0027R22203232824",
  "LogisticService": "7-11交貨便冷凍",
  "LogisticServiceID": "21",
  "paymentno": "D8273267",
  "validationno": "9066",
  "ReturnMsg": "",
  "orderno": "220323105411",
  "ErrorMsg": null
}
```

### 列印標籤

```
POST /Member/Order/Print711FreezingC2CLabel
```

| 參數 | 必填 | 說明 |
|------|------|------|
| `orderNumberStr` | ● | PayNow 物流單號，多筆以 `,` 分隔 |
| `user_account` | ● | |

### 關轉時限

收到 `7101`、`7104`、`7201`、`7204` 貨態代碼後 `D+7` 內必須打 `/api/Orderapi/Put` 進行關轉，逾期失效。

---

## 7-11 海外配送

服務代碼：`07` (店配) / `08` (宅配) / 文件版本：`711OverSea V2.7`

### 適用國家與限制

| 國家 | 代碼 | 取貨天數 | 重量/材積限制 | 進口免稅額 | 當地宅配 |
|------|------|----------|----------------|-------------|-----------|
| 香港 | `HK` | 3 天 | 店配 30×50×30 cm 5kg；宅配 85×85×85 cm 20kg | 無關稅 | 1kg=27HKD，2-5kg=37HKD |
| 新加坡 | `SG` | 2 天 | 店配 長+寬+高 80cm 5kg；宅配 85×85×85 cm 20kg | SGD 400 | 首重 7SGD/kg、續重 3SGD/kg |
| 馬來西亞 | `MY` | 4 天 | 店配 40×40×40 cm 4kg；宅配 85×85×85 cm 20kg | MYR 500 | 西馬首重 9MYR/kg；東馬首重 23MYR/kg |
| 澳門 | `MO` | 24 小時內 | 店配 45×31×35 cm 20kg；宅配 120×80×70 cm 20kg | — | 同區一件 10 澳幣，跨區 2kg 內 22 澳幣 |
| 泰國 | `TH` | 3 天 | 店配 60×60×60 cm 5kg；宅配 85×85×85 cm 20kg | 含稅 | 首重 60 NTD/kg、續重 15 NTD/kg |
| 越南 | `VN` | — | 宅配 3kg | 含稅 | — |
| 美國 | `US` | — | 宅配 100×80×70 cm 20kg | USD 800 | — |

材積計算：

- 港/新/馬/澳/泰/越南：`長 × 寬 × 高 / 6000`
- 美國/其他國家：`長 × 寬 × 高 / 5000`

> 重量與材積取較高值計價。中國目前無法配送 (運費分上海/江蘇/浙江/廣東/深圳/福建/廈門 `FeeMode=0` 與其他省 `FeeMode=1`)。

### 禁運物品 (摘錄)

- 香港：活生動物、無煙菸草製品、易燃易爆物質、香水、鋰電池等
- 新加坡：電子香菸、電子菸斗、電子雪茄菸
- 馬來西亞：肉類、海鮮、奶製品、燕窩、菲律賓/印尼水果、鋰電池、武器等

實際規範以各國海關為準。

### 流程

1. (店配) 電子地圖 (`Logistic_serviceID=07`、`Country=ALL`/`HK`/`SG` 等) 選店
2. `/api/Orderapi/Add_Order` 建單 (`Logistic_service=07` 或 `08`)
3. `GET /api/OverSeas711Order` 列印標籤 (5 日內限制)
4. 訂單成立後 5 日內完成寄件 (含當日)

### 海外建單專用欄位

| 參數 | 必填 | 說明 |
|------|------|------|
| `ReceiverCountry` | ● | 國家代碼 (英文)，依「查詢國家代碼 API」CountryId |
| `ReceiverCode` | ● | 收件人宅配郵編，香港帶 `00000`、澳門帶 `999078`，不可含特殊符號 |
| `Weight` | ● | 重量 (kg)，可帶小數點 |
| `Length` | ● | 外箱長 (cm) |
| `Width` | ● | 外箱寬 (cm) |
| `Height` | ● | 外箱高 (cm) |
| `Description` | ● | 包裹英文名稱 (僅英文/數字) |

`Receiver_Phone` 國碼規則：

- 香港：`852` + 純數字手機
- 澳門：`853` + 純數字手機
- 泰國店取：純 10 位數字、`0` 開頭、不含國碼

`Receiver_address`：

- 新馬/中港澳：可中文，長度 ≤ 150
- 其他國家：必填英文，長度 ≤ 135 byte

### 列印標籤

```
GET /api/OverSeas711Order?orderNumberStr=ORDER1,ORDER2,...
```

| 參數 | 必填 | 說明 |
|------|------|------|
| `orderNumberStr` | ● | 商家訂單編號，逗號分隔，一次最多 100 筆 |

回傳格式：

```
S,https://...   (成功，導向列印畫面或下載 Excel)
F,錯誤訊息
```

> 多筆列印會下載 Excel，錯誤訂單放在 `NoShipNo` 工作表。

### 查詢國家代碼

```
POST /api/OverSeas711Order/SelCountryID
```

JsonOrder Content：

```json
{ "user_account": "28229955", "apicode": "12345678" }
```

Response 範例：

```json
{
  "Status": "S",
  "ErrorMsg": "",
  "Detail": [
    { "CountryId": "AD", "ChineseName": "安道爾", "EnglishName": "Andorra" },
    { "CountryId": "AF", "ChineseName": "阿富汗", "EnglishName": "Afghanistan" }
  ]
}
```

### 查詢物流重量費用

```
POST /api/Orderapi/SelWeightChart
```

JsonOrder Content：

```json
{
  "user_account": "28229955",
  "apicode": "12345678",
  "LogisticServiceID": "08",
  "LogisticServiceID2": "",
  "CountryID": "US"
}
```

Response Detail：

| 欄位 | 說明 |
|------|------|
| `Country` | 國家代碼 |
| `Weight` | 包裹重量 (kg)，例：`0.5KG` |
| `Cost` | 費用 (decimal(8,2))，不含 5% 營業稅 |
| `FeeMode` | `0`:正常 / `1`:偏遠 |
| `Pay` | `0`:一般 `1`:經濟 `2`:空運 `3`:運費到付 `4`:其他 |
| `DeliveryMethod` | `0`:店配 `1`:宅配 |

### 查詢寄送包裹費用明細

兩種查法 (擇一)：

```
POST /api/OverSeas711Order/SelBillDetail        (依訂單)
POST /api/OverSeas711Order/SelBillDetailDate    (依日期 yyyy-MM-dd)
```

每週四更新帳務，可查詢至上週整週帳務 (含結束日期當日)。

---

## 全家大宗物流

服務代碼：`04` / 文件版本：`FamilyBulk V2.4`

流程與 7-11 大宗類似，但全家大宗：

- 建單時 `Logistic_service=04`、`Deadline` 為 1~7
- `Sender_Name`、`Sender_Phone` 可填空字串自動帶入「立吉富」/「0900000000」
- 列印 API：`/api/Order711` 之外另有 `/api/OrderFamiC2C` (依產品線)

> 全家大宗的後續取出貨單號流程與 7-11 大宗一致，請依官方 SDK 接續。

---

## 全家冷凍大宗 B2C

服務代碼：`24` / 文件版本：`FamilyFreezingBulkB2C V2.6`

### 與其他物流關鍵差異

1. **店鋪保留機制**：選店後 PayNow 會給予 3 小時暫留，3 小時內必須打 `/api/FamiFreezingB2C/UpSpaceConfirm` 確認，否則取消
2. 訂單需在電子地圖回傳的 `ShipDate` 前一天建立完成並列印
3. 重選店鋪：原訂單若已確認過店鋪空間，需先取消才能重選
4. 電子地圖必須帶入材積 `Length`/`Wide`/`High`/`Weight` 與出貨日 `StartDate`/`EndDate`

### 店鋪空間保留 / 取消

```
POST /api/FamiFreezingB2C/UpSpaceConfirm
```

使用情境：

- 新增訂單前需先保留空間才可成功建單
- 重選店舖若已保留過需先取消再保留新編號
- 最終未出貨訂單需取消保留

電子地圖 (Logistic_serviceID=24) 將回傳 `ReservedNo` 與 `ShipDate`，後續建單必須帶入 `ReservedNo`。

### 材積申請類別

| 類別 | 限制 |
|------|------|
| `S60` | 長+寬+高 < 60 cm |
| `S105` | 長+寬+高 < 105 cm |

---

## 全家冷凍店到店 (C2C)

服務代碼：`23` / 文件版本：`FamilyFreezingC2C V2.2`

### 流程

1. 電子地圖 (`Logistic_serviceID=23`) 選店，回傳 `ReservedNo` + `ShipDate`
2. 建單帶入 `ReservedNo`、`Logistic_service=23`
3. 列印全家店到店冷凍物流單
4. 依電子地圖回傳的 `ShipDate` 進行出貨
5. 寄貨外箱須於全家購買 (My FamiPort APP 預購寄件專用紙箱)

### 建單必填差異

`ReservedNo` 為必填，其他欄位與通用建單一致。回傳會包含 `paymentno`：

```json
{
  "Status": "S",
  "LogisticNumber": "...",
  "LogisticService": "全家店到店冷凍",
  "LogisticServiceID": "23",
  "paymentno": "...",
  "ErrorMsg": null
}
```

---

## 四大超商常溫 C2C

服務代碼：`01` (7-11 交貨便) / `03` (全家店到店) / `05` (萊爾富店到店) / `10` (OK 店到店)
文件版本：`SuperMarketC2C V2.5`

### 寄件期限

| 超商 | 寄件期限 |
|------|----------|
| 7-11 / 全家 | 7 天 |
| 萊爾富 | 5 天 |
| OK | 15 天 |

### 收件人姓名長度限制

| 物流服務 | 長度上限 |
|----------|----------|
| 7-11 交貨便 | 10 |
| 全家店到店 | 30 |
| 萊爾富店到店 | 20 |
| OK 店到店 | 10 |

### 列印標籤端點

```
GET /api/Order711          (7-11)
GET /api/OrderFamiC2C      (全家)
GET /api/OrderHiLife       (萊爾富)
GET /api/OKC2C             (OK)
```

| 參數 | 必填 | 說明 |
|------|------|------|
| `orderNumberStr` | ● | 商家訂單編號 (`OrderNo`)，逗號分隔，一次最多 100 筆 |
| `user_account` | ● | |

回傳：`S,網址` 或 `F,錯誤訊息`。

### 重新取號特別規則

- **萊爾富需在訂單成立 30 分鐘後才能進行重新取號**
- 7-11、全家、OK 在訂單成立後即可重取

### 全家 C2C 店號轉換

```
GET /api/OrderFamiC2C/GetFamiStoreID?storeId=017206&IDtype=1
```

| 參數 | 必填 | 說明 |
|------|------|------|
| `storeId` | ● | 店號 (6 碼) |
| `IDtype` | ● | `1`:轉成現行店號 / `2`:轉成原始店號 |

Response：

```json
{ "storeId": "017206", "IDtype": "1", "Error": "" }
```

### 7-11 交貨便建單回傳範例

```json
{
  "Status": "S",
  "LogisticNumber": "MIJA0027C22112026083",
  "LogisticService": "7-11交貨便",
  "LogisticServiceID": "01",
  "paymentno": "L9991156",
  "validationno": "0497",
  "ReturnMsg": "",
  "orderno": "211202115804",
  "ErrorMsg": null
}
```

`paymentno` + `validationno` 可至 7-11 Ibon 機台輸入列印。

---

## 黑貓宅配

服務代碼：`06` (黑貓宅急便) / `36` (黑貓宅急便 PayNow) / 文件版本：`BlackCat-Home-Delivery V2.1`

### 流程

1. 將訂單資料組成 JSON 字串 POST 到 `/api/Orderapi/Add_Order`
2. 成功後到 `/Member/Order/PrintBlackCatLabel` 列印標籤
3. 出貨日將商品準備好，黑貓上門取貨

### 黑貓宅配專用欄位

| 參數 | 必填 | 說明 |
|------|------|------|
| `Description` | 否 | 商品類別代碼 (見下表)，未填預設 `0015` |
| `DeliverMode` | ● | `01`:取貨付款 `02`:取貨不付款 (保險單須為 `02`) |
| `Logistic_service` | ● | `06`:黑貓宅急便 / `36`:黑貓宅急便 (PayNow 自動保險) |
| `TotalAmount` | ● | 不可大於 100,000 |
| `Deadline` | ● | 0~6；當日出貨帶 `0`，過 16:00 則出貨日為明日；週日/連假順延 |
| `Length` / `Wide` / `High` | ● | 長+寬+高 ≤ 150 cm |
| `Weight` | ● | 商品總重量 (kg) ≤ 20 kg |
| `Sender_Tel` | 否 | 寄件人市話 |
| `Receiver_Tel` | 否 | 收件人市話 |
| `ExpectDeliverTime` | 否 | `1`:13:00 前 / `2`:14:00-18:00 / `4`:不固定 (預設 `4`) |
| `ExpectDeliverDate` | 否 | `yyyy-MM-dd`，最大為建單日 + 6 天，未帶自動為出貨日 D+1 |
| `DeliveryType` | ● | `0001`:常溫 `0002`:冷藏 `0003`:冷凍 |
| `IsInsurance` | 否 | bool；有保險的單填 `true`，預設 `false` |

> 服務代號 `36` 的單**無須帶入 `IsInsurance`**，總金額超過 20,000 會自動投保 (保額為商品金額)。

### Description 商品類別代碼 (黑貓專用)

| 代碼 | 類別 |
|------|------|
| `0001` | 一般食品 |
| `0002` | 名特產/甜產印單 |
| `0003` | 酒/油/醋/醬 |
| `0004` | 穀物蔬果 |
| `0005` | 水產/肉品 |
| `0006` | 3C |
| `0007` | 家電 |
| `0008` | 服飾配件 |
| `0009` | 生活用品 |
| `0010` | 美容彩妝 |
| `0011` | 保健食品 |
| `0012` | 醫療相關用品 |
| `0013` | 寵物用品飼料 |
| `0014` | 印刷品 |
| `0015` | 其他 (預設) |

### 建單範例

```json
{
  "DeliverMode": "01",
  "Description": "0001",
  "Logistic_service": "06",
  "OrderNo": "123456789",
  "Receiver_address": "台北市北投區承德路六段2號",
  "Receiver_Email": "12345678@gmail.com",
  "Receiver_Name": "王O明",
  "Receiver_Phone": "0912345678",
  "Remark": "備註",
  "Sender_address": "台北市中山區松江路207號9樓",
  "Sender_Email": "12345678@gmail.com",
  "Sender_Name": "李O富",
  "Sender_Phone": "0912345678",
  "Sender_Tel": "0225215088",
  "Receiver_Tel": "0225215088",
  "apicode": "12345678",
  "TotalAmount": "100",
  "user_account": "28229955",
  "DeliveryType": "0001",
  "PassCode": "2FC3805A8BEEC525F2EDF74B75E7FCE83C980856",
  "Deadline": "1",
  "Length": "30",
  "Wide": "30",
  "High": "30",
  "Weight": "5"
}
```

Response：

```json
{
  "Status": "S",
  "LogisticNumber": "ABCD123456",
  "LogisticService": "黑貓宅急便",
  "LogisticServiceID": "06",
  "paymentno": "12345678",
  "ReturnMsg": "",
  "orderno": "12345678",
  "ErrorMsg": ""
}
```

### 列印黑貓宅急便標籤

```
POST /Member/Order/PrintBlackCatLabel
```

| 參數 | 必填 | 說明 |
|------|------|------|
| `LogisticNumbers` | ● | `物流單號_序號`，多筆以 `,` 分隔 |

---

## 黑貓店到店

服務代碼：`46` / 文件版本：`BlackCat-Home-Delivery V1.1`

### 流程

1. 選擇物流服務 (`Logistic_serviceID=46`) 取得門市資料
2. 完善訂單資料後組成 JSON 字串 POST 到 `/api/Orderapi/Add_Order`
3. 成功後到列印黑貓店到店標籤
4. 將商品準備好打電話給黑貓上門取貨開始配送流程

### 與宅配的差異

| 項目 | 黑貓宅配 (06/36) | 黑貓店到店 (46) |
|------|-----------------|-----------------|
| 收件方式 | 收件人地址 | 取件門市 (`receiver_storeid`/`receiver_storename`) |
| `TotalAmount` 上限 | 100,000 | 20,000 |
| 長+寬+高上限 | ≤ 150 cm | ≤ 105 cm |
| `Sender_Phone`/`Sender_Tel` | 可填空字串自動帶 `0900000000` | 需明確填值 |
| `Description` | 商品類別代碼 | 自由文字 |

### 必填欄位

`Logistic_service=46`、`receiver_storeid`、`receiver_storename`、`return_storeid` (可填空字串)、`Length`/`Wide`/`High` (≤ 105 cm)、`DeliveryType` (常溫/冷藏/冷凍)。

---

## 查詢物流單

### 依 PayNow 物流單號

```
GET /api/Orderapi/Get_Order_Info?LogisticNumber=...&sno=1
```

### 依商家訂單編號

```
GET /api/Orderapi/Get_Order_Info_orderno?orderno=...&user_account=...&sno=1
```

### Response

| 參數 | 說明 |
|------|------|
| `LogisticNumber` | PayNow 物流單號 |
| `sno` | 物流單序號 (固定 1) |
| `orderno` | 商家訂單編號 |
| `Logistic_Serviece` | 物流服務代碼 (注意官方拼字) |
| `Status` | `0`:成立中 `1`:無效訂單 |
| `Delivery_Status` | 流程狀態文字描述 |
| `PayNowLogisticCode` | 4 位數 PayNow 物流貨態代碼 |
| `Detail_Status_Description` | 貨態詳細描述 |
| `paymentno` | 物流商託運單號 |
| `validationno` | 驗證碼 (7-11 店到店類有值) |
| `ErrorMsg` | 錯誤訊息，成功為 `null` |

### 範例

```json
{
  "LogisticNumber": "MIJA0027R22203232824",
  "orderno": "220323105411",
  "Logistic_Serviece": "21",
  "Status": "0",
  "Delivery_Status": "等待寄件",
  "PayNowLogisticCode": "0000",
  "Detail_Status_Description": "訂單已成立 等待出貨",
  "sno": "1",
  "ErrorMsg": null,
  "paymentno": "D8273267",
  "validationno": "9066"
}
```

---

## 取消物流單

```
DELETE /api/Orderapi/CancelOrder
Content-Type: application/x-www-form-urlencoded
```

| 參數 | 必填 | 說明 |
|------|------|------|
| `LogisticNumber` | ● | PayNow 物流單號 |
| `sno` | ● | 物流單序號 (固定 1) |
| `PassCode` | ● | SHA-1(`user_account + OrderNo + TotalAmount + apicode`) |

### Response (純字串)

```
S,訂單已取消
F,訂單取消失敗 失敗原因: <原因>
```

### 限制

- 出貨中的大宗訂單無法使用此 API

---

## 重新取號

```
POST /api/Orderapi/ReNewOrder
Content-Type: application/x-www-form-urlencoded
```

JsonOrder Content：

| 參數 | 必填 | 說明 |
|------|------|------|
| `user_account` | ● | |
| `LogisticNumber` | ● | 原 PayNow 物流單號 |
| `sno` | ● | 物流單序號 |
| `OrderNo` | ● | 商家原始訂單編號 |
| `TotalAmount` | ● | 訂單總金額 |
| `apicode` | ● | |
| `PassCode` | ● | SHA-1(`user_account + OrderNo + TotalAmount + apicode`) |

### Response

```json
{
  "Status": "S",
  "LogisticNumber": "MIJA0027B22112100002",
  "OrderNo": "211210165125",
  "paynoworderno": "211210165125",
  "sno": "1",
  "paymentno": "82900502031",
  "validationno": "1600",
  "Status": "S",
  "ErrorMsg": null
}
```

> `paynoworderno` 為**新的訂單編號**：超過寄件期限 (7-11=5 天 / 全家=當天 / 萊爾富=5 天) 重取會產生新編號，請以 `paynoworderno` 作為後續批次列印與查詢的訂單編號。

### 各物流重取規則

| 物流 | 規則 |
|------|------|
| 7-11 大宗 (`02`) | 物流驗收後且未取貨；貨態 `1000`/`1050`/`8000` 無法重取 |
| 7-11 冷凍大宗 (`22`) | 同上 |
| 萊爾富店到店 (`05`) | 訂單成立 30 分鐘後才能重取 |
| 全家店到店 (`03`) | 規定日期 = 物流單成立日 + 0 天 (即當天) |
| 7-11 海外配送 | 已獲取出貨單號且訂單成立中、買家尚未取貨 |

---

## 門市更新 (關轉)

```
PUT /api/Orderapi/Put
Content-Type: application/x-www-form-urlencoded
```

「關轉」是指進行出貨後因各種狀況 (門市關店、轉店等) 無法將包裹配達指定門市，需請商家/消費者更換取件門市。

### 各物流關轉時限

| 物流 | 觸發貨態代碼 | 關轉時限 |
|------|-------------|---------|
| 7-11 大宗 (`02`) | `4036` | D+2 上午 11:20 前 |
| 7-11 冷凍大宗 (`22`) | `4036` | D+2 上午 10:50 前 |
| 7-11 冷凍 C2C (`21`) | `7101`/`7104`/`7201`/`7204` | D+7 內 |
| 4 大超商 C2C | `7101`/`7104`/`7201`/`7204` | D+7 內 |

### Request

| 參數 | 必填 | 說明 |
|------|------|------|
| `UpdateOrder` | ● | 物流單資料 (JSON 字串) |
| `LogisticNumber` | ● | PayNow 物流單號 |
| `sno` | ● | 物流單序號 (固定 1) |
| `ChangeType` | ● | `01`:取件門市更新 / `02`:退件門市更新 |
| `NewStoreId` | ● | 新門市店號 |
| `NewStoreName` | ● | 新門市名稱 |
| `PassCode` | ● | SHA-1(`user_account + OrderNo + TotalAmount + apicode`) |

範例：

```json
{
  "LogisticNumber": "MIJA0027B22112100002",
  "sno": "1",
  "ChangeType": "01",
  "NewStoreId": "863698",
  "NewStoreName": "豫銘門市",
  "PassCode": "4CF47FD844DF64C5D0FBF8DD134708B55ABE208B"
}
```

### Response (純字串)

```
S,更新成功
F,失敗原因: <原因>
```

---

## 物流貨態回傳 (Callback)

PayNow 在物流貨態變更時，會以 HTTP POST 將最新狀態送至商家事先設定的回傳網址。

### Request 參數

| 參數 | 名稱 | 型態 | 長度 | 必填 | 說明 |
|------|------|------|------|------|------|
| `orderno` | 商家自訂編號 | string | 30 | ● | 重取後可能與原始不同 |
| `OriginOrderno` | 商家原始自訂單號 | string | 27 | ● | |
| `PayNowLogisticCode` | 物流代碼 | string | 4 | ● | 4 碼，例：`5000`/`8000` |
| `Detail_Status_Description` | 物流狀態描述 | string |  | ● | |
| `paymentno` | 物流商託運單號 | string |  | ● | |
| `StoreDate` | 到店日期 | string |  | 否 | 若代碼為 `5000`/`5001` 則填實際到店日期 |
| `StoreTime` | 到店時間 | string |  | 否 | 同上 |

### 處理範例 (PHP)

```php
<?php

// 接收 PayNow 物流回傳
$logisticCode = $_POST['PayNowLogisticCode'] ?? '';
$orderNo      = $_POST['OriginOrderno'] ?? '';

switch ($logisticCode) {
    case '0000':
        updateOrderStatus($orderNo, 'pending');           // 訂單已成立 等待出貨
        break;
    case '5000':
        updateOrderStatus($orderNo, 'arrived_at_store');  // 取件門市配達
        break;
    case '5001':
        updateOrderStatus($orderNo, 'arrived_at_return'); // 退件門市配達
        break;
    case '8000':
        updateOrderStatus($orderNo, 'picked_up');         // 買家已取件
        break;
    case '8001':
        updateOrderStatus($orderNo, 'returned');          // 退貨成功
        break;
    case '4036':
        notifyMerchantStoreClosure($orderNo);             // 門市關轉，需更新門市
        break;
    case '9411':
        notifyMerchantStuck($orderNo);                    // 貨態停滯
        break;
    default:
        logUnknownStatus($orderNo, $logisticCode);
}

http_response_code(200);
echo 'OK';
```

> 注意：PayNow 文件未明確規範 callback 的應答格式，建議回傳 HTTP 200 + 任意文字，並由商家自行做 PassCode 比對 (官方文件未要求 callback 帶 PassCode)。

---

## 貨態代碼對照表

PayNow 物流貨態代碼為 4 位數字，依物流商有不同涵義；以下為主要代碼匯總。

### 共通代碼

| 代碼 | 說明 |
|------|------|
| `0000` | 訂單已成立 等待出貨 |
| `0001` | 訂單已成立 等待退貨 |
| `0101` | 商品已到寄件門市 |
| `0102` | 門市已更新寄件中 |
| `0103` | 門市已更新退件中 |
| `4000` | 進驗成功 |
| `5000` | 取件門市配達 |
| `5001` | 退件門市配達 |
| `8000` | 買家已取件 |
| `8001` | 退貨成功 |
| `8100` | 賣家已取件 |
| `9411` | 貨態停滯 |

### 7-11 大宗物流 (`02`)

| 代碼 | 說明 |
|------|------|
| `1000` | 訂單檔案上傳中 |
| `1050` | 物流訂單上傳成功 |
| `1071`~`1075` | XML/檔案異常 (請聯繫系統商) |
| `1080` | 門市店號轉換成功 |
| `2001`~`2017` | XML 內容、出貨單號、出貨日期格式問題 |
| `2107` | 母廠商不存在 |
| `2108` | 子廠商不存在 |
| `2110` | 門市已關轉 |
| `2118` | 代收金超過上限 |
| `2120` | XML 格式不符合規定 |
| `3001` | 物流作業驗收中 |
| `3002` | 門市已更新店號 |
| `3101` | 無此門市將進行退貨 |
| `3102` | 六、日門市不配送 |
| `3103` | 門市關轉店 |
| `3104` | 門市尚未開店 |
| `3105` | 曾經重複出貨，無法出貨 |
| `4003` | 商品捆包 |
| `4004` | 商品外帶透明 |
| `4005` | 商品多標籤 |
| `4031` | 商品破損退貨中 |
| `4032` | 商品超才退貨中 |
| `4033` | 違禁品進行罰款退貨中 |
| `4034` | 同一個訂單兩包商品資料重複 |
| `4035` | 已過門市進貨日 |
| `4036` | 門市關轉請更新門市 (D+2 11:20 前關轉) |
| `4037` | 條碼規格錯誤 |
| `4038` | 條碼無法判讀 |
| `4039` | 無標籤 |
| `4060` | 物流中心理貨中 |
| `4061` | 商品遺失 |
| `4062` | 門市不配送 |
| `4063` | 包裹異常不配送 |
| `4099` | 不正常到貨，商品提早到達物流中心 |
| `5011`~`5017` | 配送異常 (作業/車輛/天候/道路/門市) |
| `5102` | 管制品取件門市配達 |
| `5201` | EC 收退 |
| `5202` | 交貨便收件 |
| `5203` | 退貨便收件 |
| `5303` | 取件遺失進行賠償作業 |
| `6001` | 第一次開退 |
| `7001` | 正常一退 |
| `7002` | 正常二退 |
| `7011`~`7022` | 退貨原因細項 (商品瑕疵/門市/廠商/消費者) |
| `8003`~`8005` | 商品異常 (捆包/外帶透明/多標籤) |
| `8011`~`8022` | 退貨成功原因細項 |
| `8031`~`8039` | 商品異常退貨 (破損/超才/違禁/重複/條碼) |
| `8099` | 不正常到貨，商品提早到達物流中心 |
| `8110` | 賣家已取件-代收金額錯誤 |

### 7-11 大宗退貨便 (`12`)

| 代碼 | 說明 |
|------|------|
| `0001` | 訂單已成立 等待退貨 |
| `0101` | 商品已到寄件門市 |
| `7001` | 正常一退 |
| `8001` | 退貨成功 |

### 7-11 冷凍 C2C (`21`)

| 代碼 | 說明 |
|------|------|
| `0` | 訂單已成立 等待寄件中 |
| `101` | 商品已到寄件門市 |
| `102` | 門市已更新寄件中 |
| `103` | 門市已更新退件中 |
| `4034` | 同一個訂單兩包商品資料重複 |
| `4060` | 物流中心理貨中 |
| `4063` | 包裹異常不配送 |
| `4064` | 取消寄件再次寄送 (直接轉 C 店) |
| `4065` | 提早轉 C 店 - 廠商因素 |
| `4066` | 提早轉 C 店 - 超商因素 |
| `4075` | 包裹異常進入判賠程序 |
| `4076` | 包裹已送達物流中心，即將配送至指定門市 |
| `4077` | 無退件門市資料 |
| `4078` | 包裹等待配送中 |
| `4079` | 包裹進行配送中 |
| `5018` | 寄件貨態異常協尋中 |
| `5019` | 取件包裹異常協尋中 |
| `5021` | 物流中心暫報缺 |
| `5022` | 驗收前包裹異常 |
| `5301` | 取消寄件 |
| `5302` | 寄件遺失進行賠償程序 |
| `6002` | 待退貨請盡速取件 |
| `7101` | 取件門市關轉店 |
| `7102` | 取件門市舊店號更新 |
| `7104` | 取件門市臨時關轉店 |
| `7201` | 退件門市關轉店 |
| `7202` | 退件門市舊店號更新 |
| `7203` | 退件門市無取件門市資料 |
| `7204` | 退件門市臨時關轉店 |
| `8077` | 退至 7 總倉 |
| `8305` | 已送宅配 |
| `8306` | 放 7 天後拋棄 |

### 7-11 海外配送 (`07`/`08`)

| 代碼 | 說明 |
|------|------|
| `0000` | 訂單已成立 等待出貨 |
| `5000` | 門市配達 |
| `5401` | 提單成立 |
| `5402` | 已入倉 |
| `5403` | 出口作業中 |
| `5404` | 已出倉 |
| `5405` | 清關中 |
| `5406` | 派送中 |
| `5407` | 取消 |
| `5408` | 問題單 |
| `5409` | 退件包裹 |
| `5410` | 店取未取轉宅配失敗 |
| `5411` | 宅配失敗 |
| `5412` | 台灣海關檢查不通過 |
| `5413` | 標籤異常/包裝異常/訂單異常取消 |
| `5414` | 貨件遺失 |
| `5415` | 包裹異常 (件數不對/超材) |
| `8000` | 買家已取件 |

### 全家代碼 (差異部份)

| 代碼 | 說明 |
|------|------|
| `4067` | 小物流遺失 |
| `4068` | 門市遺失 |
| `4069` | 包裝廠不良 (滲漏) |
| `4070` | 門市反應商品包裝不良 (滲漏) |
| `4071` | 門市關店 |
| `4072` | 條碼資料重複 |
| `4073` | 7 日內未寄件單號失效 |
| `4074` | 貨物進店後發生異常提早退貨 |
| `5200` | 商品運送中 |
| `6004` | 商品退回物流中心 |
| `8002` | 退至全家總倉 |
| `8010` | 買家已取件-代收金額錯誤 |
| `8020` | 買家已取件商品有誤 |

### 萊爾富代碼 (差異部份)

| 代碼 | 說明 |
|------|------|
| `4067` | 小物流遺失 |
| `4068` | 門市遺失 |
| `4069` | 包裝廠不良 (滲漏) |
| `4070` | 門市反應商品包裝不良 (滲漏) |
| `4071` | 門市關店 |
| `4073` | 7 日內未寄件單號失效 |
| `4074` | 貨物進店後發生異常提早退貨 |
| `8079` | 退至萊爾富總倉 |

### OK 代碼 (差異部份)

| 代碼 | 說明 |
|------|------|
| `4030` | 無進貨資料 |
| `4031` | 商品破損退貨中 |
| `4032` | 商品超才退貨中 |
| `4040` | 條碼資料錯誤 |
| `4069` | 包裝廠不良 (滲漏) |
| `4070` | 門市反應商品包裝不良 |
| `4074` | 貨物進店後發生異常提早退貨 |
| `8076` | 退至 OK 總倉 |

### 貨態流轉範例

7-11 大宗 - 一般出貨 (成功取件)：
```
1000 → 1050 → 3001 → 4000 → 5000 → 8000
```

7-11 大宗 - 退貨成功：
```
1000 → 1050 → 3001 → 4000 → 5000 → 6001 → 5201 → 7001 → 8001
```

7-11 大宗 - 門市關轉 (更新後成功)：
```
1000 → 1050 → 3101 → 4036 → 1080 → 5000 → 8000
```

7-11 海外配送 (店配，成功取件)：
```
5401 → 5402 → 5405 → 5406 → 5000 → 8000
```

7-11 海外配送 (宅配，成功取件)：
```
5401 → 5402 → 5405 → 5406 → 8000
```

四大超商 C2C - 一般出貨：
```
0101 → 5202 → 4000 → 5000 → 8000
```

四大超商 C2C - 退貨成功：
```
0101 → 5202 → 4000 → 5000 → 6002 → 5201 → 7001 → 5001 → 8100
```

四大超商 C2C - 二次退貨 (退至總倉)：
```
0101 → 4000 → 5000 → 6002 → 4000 → 5001 → 8079 (萊) / 8077 (7) / 8002 (家)
```

7-11 冷凍 C2C - 門市關轉 (取件成功)：
```
0101 → 7101 / 7104 → 0102 → 4000 → 5000 → 8000
```

7-11 冷凍 C2C - 門市關轉 (退件成功)：
```
0101 → 5202 → 4000 → 5000 → 7201 / 7203 / 7204 → 0103 → 4000 → 5001 → 8100
```

---

## 官方資源

- **官方網站**：https://www.paynow.com.tw/
- **官方文件**：https://docs.paynow.com.tw/developer/docs/apipdf/logistics/
- **API 端點**：
  - 正式：`https://logistic.paynow.com.tw`
  - 測試：`https://testlogistic.paynow.com.tw`
- **客服信箱**：service@paynow.com.tw

---

最後更新：2026/05/07
