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

| 功能 | 路徑 | 官方頁 |
|------|------|--------|
| 門市電子地圖 | `/Express/map` | /8795 |
| 取得門市清單 | `/Helper/GetStoreList` | /47496 |
| 建立物流訂單（超商、宅配） | `/Express/Create` | /8809、/7414 |
| 產生測試標籤資料（B2C） | `/Express/CreateTestData` | /7402 |
| 列印託運單：B2C（含測標）、宅配 | `/helper/printTradeDocument` | /8875 |
| 列印託運單：C2C 7-ELEVEN | `/Express/PrintUniMartC2COrderInfo` | /7406 |
| 列印託運單：C2C 全家 | `/Express/PrintFAMIC2COrderInfo` | /8848 |
| 列印託運單：C2C 萊爾富 | `/Express/PrintHILIFEC2COrderInfo` | /8858 |
| 列印託運單：C2C OK | `/Express/PrintOKMARTC2COrderInfo` | 綠界官方 ecpay-api-skill guides/06 |
| 逆物流：B2C 7-ELEVEN／全家／萊爾富 | `/express/ReturnUniMartCVS`、`/express/ReturnCVS`、`/express/ReturnHilifeCVS` | /7408、/8894、/8896 |
| 逆物流：宅配 | `/Express/ReturnHome` | /7416 |
| 異動訂單：B2C 7-ELEVEN | `/Helper/UpdateShipmentInfo` | /7410 |
| 異動門市：C2C 7-ELEVEN | `/Express/UpdateStoreInfo` | /8907 |
| 取消訂單：C2C 7-ELEVEN | `/Express/CancelC2COrder` | /7412 |
| 查詢物流訂單 | `/Helper/QueryLogisticsTradeInfo/V5` | /7418 |

2024-11-25 起查詢 API 版本為 **V5**（/36099 更新歷程）。

---

## 測試環境

### 測試帳號

測試網址：`https://logistics-stage.ecpay.com.tw`（developers.ecpay.com.tw/7398）

| 用途 | MerchantID | HashKey | HashIV |
|------|-----------|---------|--------|
| B2C 及宅配 | `2000132` | `5294y06JbISpM5x9` | `v77hoKGq4kWxNNIS` |
| C2C | `2000933` | `XBERn1YOvpM9nfZc` | `h1ONHk4P4yqbl5LK` |

用錯特店建單會回 `0|找不到加密金鑰，請確認是否有申請開通此物流方式!`。

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
| 7-11 冷凍店取 | `UNIMARTFREEZE` | 統一超商 B2C 冷凍 |
| 7-11 交貨便 | `UNIMARTC2C` | C2C 店到店 |
| 全家超商取貨 | `FAMI` | 全家便利商店 B2C |
| 全家店到店 | `FAMIC2C` | C2C 店到店 |
| 萊爾富超商取貨 | `HILIFE` | 萊爾富 B2C |
| 萊爾富店到店 | `HILIFEC2C` | C2C 店到店 |
| OK 店到店 | `OKMARTC2C` | C2C 店到店（OK 沒有 B2C） |

B2C 合約只能用 `FAMI`、`UNIMART`、`HILIFE`、`UNIMARTFREEZE`；C2C 合約只能用 `FAMIC2C`、`UNIMARTC2C`、`HILIFEC2C`、`OKMARTC2C`。
`GoodsAmount` 範圍 1–20,000，超出回 `10500040`。

### 宅配類型

| 類型 | 代碼 | 說明 |
|------|------|------|
| 黑貓宅急便 | `TCAT` | `Temperature` 0001 常溫／0002 冷藏／0003 冷凍；代收貨款時商品金額上限 20,000 |
| 中華郵政 | `POST` | `Temperature` 只能 0001；不可代收；忽略 `Specification`、`ScheduledPickupTime` |

### LogisticsType 對照

| 值 | 說明 |
|------|------|
| `CVS` | 超商取貨 |
| `HOME` | 宅配 |

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
| `MerchantID` | String(10) | ● | 廠商編號 |
| `MerchantTradeNo` | String(20) | ● | 廠商交易編號，唯一 |
| `MerchantTradeDate` | String(20) | ● | `yyyy/MM/dd HH:mm:ss` |
| `LogisticsType` | String(20) | ● | `CVS`／`HOME` |
| `LogisticsSubType` | String(20) | ● | 見「物流類型」 |
| `GoodsAmount` | Int | ● | 超商 1–20,000；宅配 1 元以上（黑貓代收時上限 20,000） |
| `GoodsName` | String(50) | 條件 | 超商 `UNIMARTC2C`、`HILIFEC2C`、`OKMARTC2C` 必填 |
| `SenderName` | String(10) | ● | 4–10 字元（中文 2–5 字），不可含數字、特殊符號、emoji；C2C 退件須憑證件領取，勿填公司名 |
| `ReceiverName` | String(10) | ● | 同上 |
| `ServerReplyURL` | String(200) | ● | 物流狀態通知網址 |
| `ClientReplyURL` | String(200) | | Client 端回傳網址 |
| `ReceiverEmail` | String(50) | | 收件人 email |
| `TradeDesc` | String(200) | | 交易描述 |
| `Remark` | String(200) | | 備註 |
| `PlatformID` | String(10) | | 平台商代號 |
| `CheckMacValue` | String | ● | 檢查碼（MD5） |

### 超商專用參數（/8809）

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `ReceiverStoreID` | String(6) | ● | 收件門市代碼 |
| `ReturnStoreID` | String(6) | | 退貨門市；僅 7-ELEVEN C2C 適用，未帶則退回原寄件門市 |
| `SenderPhone` | String(20) | | 寄件人電話 |
| `SenderCellPhone` | String(10) | 條件 | `UNIMARTC2C`、`HILIFEC2C`、`OKMARTC2C` 必填；09 開頭 10 碼；`FAMIC2C` 空值時帶入後台設定 |
| `ReceiverPhone` | String(20) | | 允許數字與 `()-#` |
| `ReceiverCellPhone` | String(10) | ● | 09 開頭 10 碼 |
| `IsCollection` | String(1) | | `Y` 代收貨款、`N` 不代收（預設） |
| `CollectionAmount` | Int | 條件 | `UNIMARTC2C`、`UNIMART`、`UNIMARTFREEZE` 須等於 `GoodsAmount` |

### 宅配專用參數（/7414）

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `SenderPhone`／`SenderCellPhone` | String(20) | 擇一 | |
| `ReceiverPhone`／`ReceiverCellPhone` | String(20) | 擇一 | |
| `SenderZipCode` | String(6) | ● | 寄件人郵遞區號 |
| `SenderAddress` | String(60) | ● | 6–60 字元；中華郵政僅台灣本島 |
| `ReceiverZipCode` | String(6) | ● | 收件人郵遞區號 |
| `ReceiverAddress` | String(60) | ● | 收件人地址 |
| `IsCollection` | String(1) | | `Y` 代收（僅 `TCAT`，商品金額上限 20,000）；中華郵政勿填 |
| `GoodsWeight` | Number | 條件 | `POST` 必填，公斤，上限 20、小數 3 位 |
| `Temperature` | String(4) | | `0001` 常溫（預設）、`0002` 冷藏、`0003` 冷凍；`POST` 只能 `0001` |
| `Distance` | String(2) | | `00` 同縣市（預設）、`01` 外縣市、`02` 離島；`POST` 忽略 |
| `Specification` | String(4) | | `0001` 60cm（預設）、`0002` 90cm、`0003` 120cm、`0004` 150cm；冷藏冷凍不可用 150cm；`POST` 忽略 |
| `ScheduledPickupTime` | String(1) | | 固定帶 `4`（不限時）；`POST` 忽略 |
| `ScheduledDeliveryTime` | String(2) | | `1` 13 點前、`2` 14–18 點、`4` 不限時（官方表另列 `3` 亦為 14–18 點） |

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

### B2C（含測標）、宅配 `POST /helper/printTradeDocument`（/8875）

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `MerchantID` | String(10) | ● | 廠商編號 |
| `AllPayLogisticsID` | String | ● | 物流交易編號，批次列印以半形逗號分隔 |
| `PlatformID` | String(10) | | 平台商代號 |
| `PrintMode` | Int | | `1` 一般 A4、`2` 熱感應標籤 A6 |
| `CheckMacValue` | String | ● | 檢查碼 |

回傳 HTML 頁面（`Accept: text/html`）。**不可放在 iframe**，導向超商時會被阻擋。

C2C 各超商另有列印端點（見上方端點表），需帶 `CVSPaymentNo`（7-11 另帶 `CVSValidationNo`）。

---

## 物流狀態查詢

### 端點

```
POST /Helper/QueryLogisticsTradeInfo/V5
```

### 參數（/7418）

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `MerchantID` | String(10) | ● | 廠商編號 |
| `AllPayLogisticsID` | String(20) | 擇一 | 綠界物流交易編號 |
| `MerchantTradeNo` | String(20) | 擇一 | 廠商交易編號 |
| `TimeStamp` | Int | ● | Unix 時間，3 分鐘內有效 |
| `PlatformID` | String(10) | | 平台商代號 |
| `CheckMacValue` | String | ● | 檢查碼 |

### 回應參數

`MerchantID`、`MerchantTradeNo`、`AllPayLogisticsID`、`LogisticsType`（如 `CVS_UNIMARTC2C`）、`LogisticsStatus`（代碼見 /7440）、`GoodsAmount`、`GoodsName`、`GoodsWeight`、`ActualWeight`、`HandlingCharge`、`CollectionAmount`、`CollectionChargeFee`、`CollectionAllocateAmount`、`CollectionAllocateDate`、`CVSPaymentNo`、`CVSValidationNo`、`ShipmentNo`、`ShipChargeDate`、`BookingNote`、`TradeDate`、`SenderName`、`SenderPhone`、`SenderCellPhone`、`CheckMacValue`。

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
