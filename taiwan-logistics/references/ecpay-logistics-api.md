# ECPay Logistics API Reference

綠界科技 (ECPay) 物流 API 完整參考文件。

---

## 目錄

1. [API 端點總覽](#api-端點總覽)
2. [測試環境](#測試環境)
3. [物流類型](#物流類型)
4. [CheckMacValue 計算](#checkmacvalue-計算)
5. [建立物流訂單](#建立物流訂單)
6. [超商電子地圖](#超商電子地圖)
7. [列印託運單](#列印託運單)
8. [物流狀態查詢](#物流狀態查詢)
9. [物流狀態通知](#物流狀態通知)
10. [錯誤碼對照表](#錯誤碼對照表)

---

## API 端點總覽

### 基礎 API 路徑

| 環境 | 基礎路徑 |
|------|----------|
| **測試環境** | `https://logistics-stage.ecpay.com.tw` |
| **正式環境** | `https://logistics.ecpay.com.tw` |

### 物流相關端點

| 功能 | 測試環境 | 正式環境 |
|------|----------|----------|
| 建立物流訂單 | `/Express/Create` | `/Express/Create` |
| 超商電子地圖 | `/Express/map` | `/Express/map` |
| 列印託運單 | `/helper/printTradeDocument` | `/helper/printTradeDocument` |
| 查詢訂單 | `/Helper/QueryLogisticsTradeInfo/V2` | `/Helper/QueryLogisticsTradeInfo/V2` |

---

## 測試環境

### 測試帳號

```
測試網址: https://logistics-stage.ecpay.com.tw
商店代號: 2000132
HashKey:  5294y06JbISpM5x9
HashIV:   v77hoKGq4kWxNNIS
```

### 測試用超商門市

| 超商 | 測試門市代號 |
|------|-------------|
| 7-11 | `131386` |
| 全家 | `006598` |
| 萊爾富 | `2001` |
| OK | `1328` |

---

## 物流類型

### 超商取貨類型

| 類型 | 代碼 | 說明 |
|------|------|------|
| 7-11 超商取貨 | `UNIMART` | 統一超商 B2C |
| 7-11 交貨便 | `UNIMARTC2C` | C2C 店到店 |
| 全家超商取貨 | `FAMI` | 全家便利商店 B2C |
| 全家店到店 | `FAMIC2C` | C2C 店到店 |
| 萊爾富超商取貨 | `HILIFE` | 萊爾富 B2C |
| 萊爾富店到店 | `HILIFEC2C` | C2C 店到店 |
| OK 超商取貨 | `OKMART` | OK 便利商店 B2C |
| OK 店到店 | `OKMARTC2C` | C2C 店到店 |

### 宅配類型

| 類型 | 代碼 | 說明 |
|------|------|------|
| 黑貓宅急便 | `TCAT` | 宅配到府 |
| 宅配通 | `ECAN` | 常溫宅配 |

### LogisticsType 對照

| 值 | 說明 |
|------|------|
| `CVS` | 超商取貨 |
| `Home` | 宅配 |

---

## CheckMacValue 計算

### 計算步驟

1. 將參數依照 Key 排序 (A-Z, 不分大小寫)
2. 組合成 `key=value&key=value` 格式
3. 前後加上 `HashKey={HashKey}&` 和 `&HashIV={HashIV}`
4. URL Encode (RFC 1866)
5. 轉小寫
6. 計算 MD5
7. 轉大寫

### PHP 範例

```php
<?php

function generateCheckMacValue(array $params, string $hashKey, string $hashIV): string
{
    // 1. 排序參數 (不分大小寫)
    uksort($params, 'strcasecmp');

    // 2. 組合字串
    $paramStr = urldecode(http_build_query($params));

    // 3. 加上 HashKey 和 HashIV
    $raw = "HashKey={$hashKey}&{$paramStr}&HashIV={$hashIV}";

    // 4. URL Encode
    $encoded = urlencode($raw);

    // 5. 轉小寫
    $lower = strtolower($encoded);

    // 6. MD5
    $md5 = md5($lower);

    // 7. 轉大寫
    return strtoupper($md5);
}
```

### Python 範例

```python
import hashlib
import urllib.parse

def generate_check_mac_value(params: dict, hash_key: str, hash_iv: str) -> str:
    # 1. 排序參數
    sorted_params = sorted(params.items(), key=lambda x: x[0].lower())

    # 2. 組合字串
    param_str = '&'.join(f'{k}={v}' for k, v in sorted_params)

    # 3. 加上 HashKey 和 HashIV
    raw = f'HashKey={hash_key}&{param_str}&HashIV={hash_iv}'

    # 4. URL Encode
    encoded = urllib.parse.quote_plus(raw)

    # 5. 轉小寫
    lower = encoded.lower()

    # 6. MD5
    md5 = hashlib.md5(lower.encode('utf-8')).hexdigest()

    # 7. 轉大寫
    return md5.upper()
```

---

## 建立物流訂單

### 端點

```
POST /Express/Create
```

### 通用參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `MerchantID` | String(10) | ● | 商店代號 |
| `MerchantTradeNo` | String(20) | ● | 訂單編號 (唯一) |
| `MerchantTradeDate` | String(20) | ● | 訂單日期 `yyyy/MM/dd HH:mm:ss` |
| `LogisticsType` | String(20) | ● | 物流類型 `CVS`/`Home` |
| `LogisticsSubType` | String(20) | ● | 物流子類型 |
| `GoodsAmount` | Integer | ● | 商品金額 |
| `GoodsName` | String(50) | ● | 商品名稱 |
| `SenderName` | String(10) | ● | 寄件人姓名 |
| `SenderPhone` | String(20) | ● | 寄件人電話 |
| `SenderCellPhone` | String(20) | 否 | 寄件人手機 |
| `ReceiverName` | String(10) | ● | 收件人姓名 |
| `ReceiverPhone` | String(20) | ● | 收件人電話 |
| `ReceiverCellPhone` | String(20) | 否 | 收件人手機 |
| `ServerReplyURL` | String(200) | ● | 物流狀態通知網址 |
| `CheckMacValue` | String | ● | 檢查碼 |

### 超商取貨專用參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `ReceiverStoreID` | String(6) | ● | 收件門市代號 |
| `ReturnStoreID` | String(6) | 否 | 退貨門市代號 |
| `IsCollection` | String(1) | 否 | 是否代收貨款 `Y`/`N` |
| `CollectionAmount` | Integer | 否 | 代收金額 |

### 宅配專用參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `SenderZipCode` | String(5) | ● | 寄件人郵遞區號 |
| `SenderAddress` | String(200) | ● | 寄件人地址 |
| `ReceiverZipCode` | String(5) | ● | 收件人郵遞區號 |
| `ReceiverAddress` | String(200) | ● | 收件人地址 |
| `Temperature` | String(4) | 否 | 溫層 `0001`常溫 `0002`冷藏 `0003`冷凍 |
| `Distance` | String(2) | 否 | 距離 `00`同縣市 `01`外縣市 `02`離島 |
| `Specification` | String(4) | 否 | 規格 (見下表) |
| `ScheduledDeliveryTime` | String(1) | 否 | 預定送達時段 |
| `ScheduledDeliveryDate` | String(10) | 否 | 預定送達日期 |

### Specification 規格代碼

| 代碼 | 尺寸 |
|------|------|
| `0001` | 60cm |
| `0002` | 90cm |
| `0003` | 120cm |
| `0004` | 150cm |

### ScheduledDeliveryTime 時段代碼

| 代碼 | 時段 |
|------|------|
| `1` | 13:00 前 |
| `2` | 14:00-18:00 |
| `3` | 不限時 |
| `4` | 任何時間 (黑貓夜配) |

### PHP 範例 - 超商取貨

```php
<?php

$params = [
    'MerchantID' => '2000132',
    'MerchantTradeNo' => 'LOG' . time(),
    'MerchantTradeDate' => date('Y/m/d H:i:s'),
    'LogisticsType' => 'CVS',
    'LogisticsSubType' => 'UNIMART',
    'GoodsAmount' => 500,
    'GoodsName' => '測試商品',
    'SenderName' => '寄件人',
    'SenderPhone' => '0912345678',
    'ReceiverName' => '收件人',
    'ReceiverPhone' => '0987654321',
    'ReceiverStoreID' => '131386',
    'ServerReplyURL' => 'https://your-site.com/logistics_notify',
    'IsCollection' => 'N',
];

$params['CheckMacValue'] = generateCheckMacValue($params, $hashKey, $hashIV);

$ch = curl_init();
curl_setopt_array($ch, [
    CURLOPT_URL => 'https://logistics-stage.ecpay.com.tw/Express/Create',
    CURLOPT_POST => true,
    CURLOPT_POSTFIELDS => http_build_query($params),
    CURLOPT_RETURNTRANSFER => true,
]);

$response = curl_exec($ch);
curl_close($ch);

// 解析回應 (格式: 1|OK|MerchantID=xxx|...)
```

### 回應格式

成功回應:
```
1|OK|MerchantID=2000132|MerchantTradeNo=LOG1234567890|RtnCode=300|RtnMsg=交易成功|AllPayLogisticsID=1234567890|CVSPaymentNo=AB12345|CVSValidationNo=1234|LogisticsType=CVS|LogisticsSubType=UNIMART|GoodsAmount=500|UpdateStatusDate=2024/01/15 10:30:00|ReceiverName=收件人|ReceiverPhone=0987654321|ReceiverStoreID=131386|BookingNote=|CheckMacValue=ABC123...
```

失敗回應:
```
0|ErrorCode|ErrorMessage
```

---

## 超商電子地圖

### 端點

```
POST /Express/map
```

### 參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `MerchantID` | String(10) | ● | 商店代號 |
| `LogisticsType` | String(20) | ● | 固定 `CVS` |
| `LogisticsSubType` | String(20) | ● | 超商類型 |
| `IsCollection` | String(1) | ● | 是否代收 `Y`/`N` |
| `ServerReplyURL` | String(200) | ● | 選擇門市後的回傳網址 |
| `ExtraData` | String(200) | 否 | 額外資料 (會原樣回傳) |

### 流程

1. 建立表單 POST 至電子地圖端點
2. 使用者在地圖選擇門市
3. ECPay POST 門市資料至 `ServerReplyURL`

### 回傳參數

| 參數 | 說明 |
|------|------|
| `CVSStoreID` | 門市代號 |
| `CVSStoreName` | 門市名稱 |
| `CVSAddress` | 門市地址 |
| `CVSTelephone` | 門市電話 |
| `ExtraData` | 額外資料 |

### PHP 範例

```php
<?php
// 產生電子地圖表單
$html = <<<HTML
<form id="map-form" method="post" action="https://logistics-stage.ecpay.com.tw/Express/map" target="map-iframe">
    <input type="hidden" name="MerchantID" value="2000132">
    <input type="hidden" name="LogisticsType" value="CVS">
    <input type="hidden" name="LogisticsSubType" value="UNIMART">
    <input type="hidden" name="IsCollection" value="N">
    <input type="hidden" name="ServerReplyURL" value="https://your-site.com/map_callback">
    <input type="hidden" name="ExtraData" value="order_123">
</form>
<iframe name="map-iframe" width="100%" height="600"></iframe>
<script>document.getElementById('map-form').submit();</script>
HTML;
```

---

## 列印託運單

### 端點

```
POST /helper/printTradeDocument
```

### 參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `MerchantID` | String(10) | ● | 商店代號 |
| `AllPayLogisticsID` | String(20) | ● | ECPay 物流編號 |
| `CheckMacValue` | String | ● | 檢查碼 |

### 回應

成功時會回傳 PDF 檔案內容。

---

## 物流狀態查詢

### 端點

```
POST /Helper/QueryLogisticsTradeInfo/V2
```

### 參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `MerchantID` | String(10) | ● | 商店代號 |
| `AllPayLogisticsID` | String(20) | ● | ECPay 物流編號 |
| `CheckMacValue` | String | ● | 檢查碼 |

### 回應參數

| 參數 | 說明 |
|------|------|
| `MerchantID` | 商店代號 |
| `MerchantTradeNo` | 訂單編號 |
| `AllPayLogisticsID` | ECPay 物流編號 |
| `LogisticsType` | 物流類型 |
| `LogisticsSubType` | 物流子類型 |
| `LogisticsStatus` | 物流狀態碼 |
| `GoodsAmount` | 商品金額 |
| `UpdateStatusDate` | 狀態更新時間 |
| `ReceiverName` | 收件人姓名 |
| `ReceiverPhone` | 收件人電話 |
| `ReceiverStoreID` | 收件門市代號 |
| `TradeDate` | 交易時間 |

---

## 物流狀態通知

### 通知流程

ECPay 會在物流狀態變更時 POST 資料至 `ServerReplyURL`。

### 通知參數

| 參數 | 說明 |
|------|------|
| `MerchantID` | 商店代號 |
| `MerchantTradeNo` | 訂單編號 |
| `AllPayLogisticsID` | ECPay 物流編號 |
| `LogisticsType` | 物流類型 |
| `LogisticsSubType` | 物流子類型 |
| `LogisticsStatus` | 物流狀態碼 |
| `GoodsAmount` | 商品金額 |
| `UpdateStatusDate` | 狀態更新時間 |
| `ReceiverName` | 收件人姓名 |
| `ReceiverPhone` | 收件人電話 |
| `ReceiverStoreID` | 收件門市代號 |
| `CheckMacValue` | 檢查碼 |

### 處理範例

```php
<?php

// 接收通知
$postData = $_POST;

// 取出 CheckMacValue
$receivedMac = $postData['CheckMacValue'];
unset($postData['CheckMacValue']);

// 重新計算 CheckMacValue
$calculatedMac = generateCheckMacValue($postData, $hashKey, $hashIV);

// 驗證
if ($receivedMac !== $calculatedMac) {
    echo '0|CheckMacValue Error';
    exit;
}

// 根據物流狀態更新訂單
$logisticsStatus = $postData['LogisticsStatus'];

// 各物流商代碼不同，只列常用節點；完整代碼見 data/status-codes.csv（來源：綠界物流貨態代碼表）
switch ($logisticsStatus) {
    case '300':   // 訂單處理中（綠界已收到訂單資料）
        updateOrderStatus($postData['MerchantTradeNo'], 'created');
        break;
    case '2030':  // 7-11 / 萊爾富：物流中心驗收成功
    case '3024':  // 全家 / 萊爾富：物流中心驗收成功
        updateOrderStatus($postData['MerchantTradeNo'], 'shipped');
        break;
    case '2063':  // 7-11 / 萊爾富：包裹配達取件門市
    case '2073':  // 7-11 / 萊爾富：包裹配達取件門市
    case '3018':  // 全家 / 萊爾富：包裹配達取件門市
        updateOrderStatus($postData['MerchantTradeNo'], 'at_store');
        break;
    case '2067':  // 7-11 / 萊爾富：買家已到店取貨
    case '3022':  // 全家 / 萊爾富：買家已到店取貨
    case '3003':  // 黑貓：配完
        updateOrderStatus($postData['MerchantTradeNo'], 'picked_up');
        break;
    case '2074':  // 7-11 / 萊爾富：買家未取包裹，將退回物流中心
        updateOrderStatus($postData['MerchantTradeNo'], 'returning');
        break;
}

// 回應 OK
echo '1|OK';
```

---

## 錯誤碼對照表

### 物流狀態碼（LogisticsStatus / RtnCode）

> 依綠界「物流貨態代碼表」（附錄 7440 / 10200 的下載檔 developers.ecpay.com.tw/logistics_status/，2026-09 擷取）。
> **同一代碼只在特定物流商出現，不同物流商的「取貨完成」代碼不同**（7-11 是 `2067`、全家是 `3022`）。
> 完整 216 個代碼（含適用物流商）見 `data/status-codes.csv`；綠界註明代碼會不定時更新，以後台「物流貨態代碼查詢」為準。

| 狀態碼 | 說明 | 物流商 |
|--------|------|--------|
| `300` | 訂單處理中（綠界已收到訂單資料） | 超商、黑貓 |
| `310` | 訂單上傳物流中 | 超商、黑貓 |
| `2030` | 物流中心驗收成功 | 7-11、萊爾富 |
| `3024` | 物流中心驗收成功 | 全家、萊爾富 |
| `2063` / `2073` | 包裹配達取件門市 | 7-11、萊爾富 |
| `3018` | 包裹配達取件門市 | 全家、萊爾富 |
| `2067` | 買家已到店取貨 | 7-11、萊爾富 |
| `3022` | 買家已到店取貨 | 全家、萊爾富 |
| `2074` | 買家未取包裹，將退回物流中心 | 7-11、萊爾富 |
| `2068` | 賣家已到門市寄件 | 7-11 交貨便、萊爾富 |
| `3006` | 配送中 | 黑貓 |
| `3003` | 配完 | 黑貓 |

### 交易訊息代碼（建立訂單等 API 的 RtnCode）

> 依綠界附錄「交易訊息代碼一覽表」（developers.ecpay.com.tw/7426）。綠界註明代碼持續新增，完整清單在廠商後台「交易狀態代碼查詢」。

| 代碼 | 說明 |
|------|------|
| `10500001` | 廠商交易時間為Null |
| `10500002` | 物流代碼為Null |
| `10500003` | 商品金額為Null |
| `10500004` | 寄件人姓名為Null |
| `10500005` | 收件人姓名為Null |
| `10500006` | 寄件人郵遞區號為Null |
| `10500007` | 寄件人住址為Null |
| `10500008` | 收件人郵遞區號為Null |
| `10500009` | 收件人住址為Null |
| `10500010` | 取貨門市店代碼為Null |
| `10500011` | 退貨門市店代碼為Null |
| `10500012` | 服務型態代碼有誤 |
| `10500013` | 收件人電話以及手機號碼為Null |
| `10500014` | 寄件人電話以及手機號碼為Null |
| `10500015` | 出貨日期以及取貨門市代碼需擇一必填 |
| `10500016` | 物流代碼為Null |
| `10500017` | 商品名稱為Null |
| `10500018` | 寄貨編號為Null |
| `10500019` | 檢查碼為Null |
| `10500020` | AllPayLogisticsID必須為整數。 |
| `10500021` | 更新門市類型(StoreType)錯誤 |
| `10500022` | 宅配溫層為Null |
| `10500023` | 宅配距離為Null |
| `10500024` | 宅配規格為Null |
| `10500025` | 宅配預計送達時間為Null |
| `10500026` | 無物流查詢訂單網址 |
| `10500027` | 無物流通知網址 |
| `10500028` | 物流回傳網址 |
| `10500029` | 商品金額有誤 |
| `10500030` | 物流類型不符 |
| `10500031` | 物流子類型不符 |
| `10500032` | 物流訂單編號為Null |
| `10500033` | 退貨訂單編號為Null |
| `10500035` | 寄件人姓名請設定為最多10字元(中文5個字, 英文10個字不得含指定特殊符號) |
| `10500036` | 收件人姓名請設定為4~10字元(中文2~5個字, 英文4~10個字不得含指定特殊符號) |
| `10500037` | 物流子類型為Null |
| `10500038` | 商品名稱請設定為最多50字元(中文25個字,英文50個字不得含指定特殊符號) |
| `10500039` | 收件人手機號碼請輸入最少10字元 |
| `10500040` | 商品金額有誤 |
| `10500041` | 收件人手機號碼錯誤 |
| `10500042` | 收件人電話號碼錯誤 |
| `10500043` | 寄件人手機號碼錯誤 |
| `10500044` | 寄件人電話號碼錯誤 |
| `10500045` | 收件人地址錯誤 |
| `10500046` | 寄件人地址錯誤 |
| `10500047` | 寄件人手機號碼欄位未填寫 |
| `10500048` | 收件人手機號碼欄位未填寫 |
| `10500049` | 綠界帳戶可提領餘額為負數或不足以支付物流運費無法建立訂單 |
| `10500050` | 尚未有營業所配送資料，無法建立訂單 |
| `10500051` | 物流服務無法使用，請洽綠界科技客服 |
| `10500052` | 收件人Email(ReceiverEmail)欄位必填 |
| `10500053` | 收件人Email(ReceiverEmail)格式有誤 |
| `10500054` | 請先通過身分驗證 |
| `10500055` | 請先通過銀行驗證及設定銀行預設帳戶 |
| `10500056` | 請先申請物流寄送服務 |
| `10500066` | 商品重量需上限為20公斤且須大於0 |
| `10500067` | 中華郵政退貨處理方式尚未填寫 |

---

## 官方資源

- **官方網站**: https://www.ecpay.com.tw/
- **物流 API 文件**: https://developers.ecpay.com.tw/?p=7421
- **技術客服**: techsupport@ecpay.com.tw
