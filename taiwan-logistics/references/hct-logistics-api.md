# HCT Logistics API Reference

新竹物流 (HCT, Hsinchu Transportation) **直連 API** 完整參考文件。

> **重要說明**
> 本文件描述**直連 HCT 自家 API** 的整合方式 (申請後使用)。如僅需透過 ECPay/PayNow/SmilePay 等 aggregator 打 HCT 配送 (`LogisticsType=HCT` / `LogisticsSubType=TCAT`)，請參考各 aggregator 的物流文件。
>
> HCT 與本工具包中的其他物流業者不同 — 它**本身就是配送公司 (carrier)**，並非 aggregator。本參考適用於需要直接對接新竹物流系統的中大型出貨企業。

---

## 目錄

1. [文件版本與適用情境](#文件版本與適用情境)
2. [API 服務分類](#api-服務分類)
3. [申請流程](#申請流程)
4. [環境與測試帳號](#環境與測試帳號)
5. [加解密機制](#加解密機制)
6. [查貨服務 (Track Shipment)](#查貨服務-track-shipment)
   - 網頁串接模式 (單筆)
   - 多筆貨號 XML 查詢
   - 貨況對應表
7. [出貨/託運單服務 (EDI Web Service)](#出貨託運單服務-edi-web-service)
   - TransData — 傳入託運資料
   - UpdData — 修改重量
   - TransReport — 列印總表
   - QueryEDELNO — 查詢貨號
   - R_TransData — 逆物流託運資料
8. [錯誤原因明細](#錯誤原因明細)
9. [整合最佳實務](#整合最佳實務)
10. [aggregator vs 直連對照](#aggregator-vs-直連對照)

---

## 文件版本與適用情境

| 項目 | 內容 |
|------|------|
| **官方文件版本** | API 服務說明 V1 (2022/12/30 ver 2.0) |
| **發行單位** | 新竹物流股份有限公司 / HCT Information Integration Services |
| **聯絡電話** | 02-2837-1122 #5123 (許先生) |
| **適用情境** | 大量出貨企業；自有 ERP/WMS 需直接對接 HCT；不透過 aggregator 中介 |
| **不適用情境** | 一般電商小量出貨 (建議走 ECPay/PayNow 等 aggregator 較快) |

### 與 aggregator 的差異

```
┌──────────────────┐                    ┌──────────────────┐
│  aggregator 模式  │                    │   HCT 直連模式    │
├──────────────────┤                    ├──────────────────┤
│  Your System     │                    │  Your System     │
│       ↓          │                    │       ↓          │
│  ECPay/PayNow    │                    │  HCT 自家 API    │
│       ↓          │                    │       ↓          │
│  HCT (carrier)   │                    │  HCT (carrier)   │
└──────────────────┘                    └──────────────────┘
LogisticsSubType=TCAT                   直接呼叫 hct.com.tw
單一商店代號跨多家物流                    需與 HCT 站所申請帳密
不需 HCT 帳號                            適合大量出貨
```

---

## API 服務分類

HCT 直連 API 共分為**兩大類**：

| 服務類別 | 用途 | 串接方式 |
|---------|------|---------|
| **查貨服務** | 給客戶/收件人查貨況 | URL 嵌入 / XML POST |
| **出貨/託運單服務** | 上傳託運資料、列印託運單 | SOAP / JSON / XML Web Service |

### 出貨服務主要 SOAP 方法

| SOAP 方法 | 用途 | 說明 |
|----------|------|------|
| `TransData()` | 上傳託運資料 (列印託運單) | 傳入託運資料、取得貨號、到著站、標籤圖片 |
| `TransData_Json()` | 同上 (JSON 格式) | |
| `TransData_XML()` | 同上 (XML 格式) | |
| `UpdData()` | 修改重量 | 傳入新竹貨號 + 訂單編號修改重量 |
| `UpdData_Json()` | 同上 (JSON) | |
| `UpdData_Xml()` | 同上 (XML) | |
| `TransReport()` | 列印託運總表 | 當日確認出貨 (18:00 前上傳) |
| `TransReport_Json()` | 同上 (JSON) | |
| `TransReport_XML()` | 同上 (XML) | |
| `QueryEDELNO()` | 查詢貨號 | 由訂單編號反查新竹貨號 |
| `QueryEDELNO_Json()` | 同上 (JSON) | |
| `QueryEDELNO_Xml()` | 同上 (XML) | |
| `R_TransData_Json()` | 逆物流託運資料 | 退貨/取件 |

---

## 申請流程

HCT 與多數 aggregator 不同，**沒有自助開發者後台**；服務必須透過配合的營業站所申請。

### 1. 申請查貨服務

> API 查貨服務可與**配合站所電腦負責人**申請，將會提供串接申請表單 & 串接說明文件給您填寫。

申請後會取得：

- 加 / 解密金鑰 (`v` 參數值)
- 加密 Sample Code (C#)
- 查貨用「特約客戶帳號」與「客戶代號」(若選擇用訂單編號查詢)

### 2. 申請出貨 / 託運單列印服務

> API 出貨/託運單列印服務可與**配合站所電腦負責人**申請，將會提供串接申請表單 & 串接說明文件給您填寫。

申請後會取得：

- 公司名稱 (`Company`)
- 密碼 (`password`)
- 客代 (`escsno`，11 碼)
- 出貨站代號 (`esstno`，4 碼)
- 新竹貨號區間及規則 (若需自行配號)

> 申請時需選擇查貨基準鍵：**訂單編號** 或 **十碼貨號**，僅能擇一，**不可動態切換**。若日後要更改需聯繫原申請營業所。

---

## 環境與測試帳號

### 服務端點

| 服務 | URL |
|------|-----|
| 查貨 (網頁) | `https://hctapiweb.hct.com.tw/phone/searchGoods_Main.aspx` |
| 查貨 (XML 多筆) | `https://hctapiweb.hct.com.tw/phone/searchGoods_Main_Xml.ashx` |
| 出貨 EDI Web Service | `https://Hctrt.hct.com.tw/EDI_WebService2/Service1.asmx` |

### 測試帳號 (出貨 API)

| 欄位 | 值 |
|------|-----|
| Company | `test` |
| password | `test1` |

> ⚠️ **注意**：HCT **沒有獨立 sandbox 環境**。所有 API 端點都是**正式系統**，僅以測試帳號 `test/test1` 隔離測試資料。實作時請務必區分 production / staging 帳號，避免污染真實貨況。

### 系統維護時間

> 我司系統於每日凌晨 **03:40 - 04:30** 進行查貨系統維護，期間不會有相關貨況更新。

---

## 加解密機制

### 重要提示

> ※ **加 / 解密方式、相關金鑰參數將於申請後提供**。
>
> ※ **加密 Sample Code (C#) 於申請後會提供**。

公開文件中**未揭露具體的加解密演算法**，只說明：

1. 採 HCT **自訂加解密**機制
2. 加密後字串作為 `no` 參數附加於查貨網址或 POST body
3. `v` 參數為金鑰版本號 (公開範例顯示 `v=xxxxxx`)
4. 申請後 HCT 會提供 C# Sample Code 作為實作參考

### 加密應用位置

| 位置 | 加密目標 |
|------|---------|
| 查貨網頁 URL | 訂單編號 / 貨號 → `no` 參數 |
| 多筆 XML 查詢請求 | 整段 XML body → `no` 參數 |
| 多筆 XML 查詢回應 | 整段 XML body 加密回傳，需自行解密 |

### 跨語言實作建議

由於官方僅提供 C# Sample Code，若需以 PHP / Python / Node.js / Go 實作，建議：

1. **先取得 C# Sample**：申請完成後請求 HCT 技術窗口提供 C# 範例
2. **解析演算法**：常見為 AES-CBC / DES / TripleDES + Base64 (URL-safe) 或 Hex 編碼，依 Sample 為準
3. **以單元測試驗證**：將 C# Sample 的「明文 → 密文」對應抓出，於目標語言重現相同輸出
4. **將 `v` 視為設定**：金鑰版本可能定期輪替，避免硬編碼

---

## 查貨服務 (Track Shipment)

### 網頁串接模式 (單筆訂單)

提供**單筆**訂單編號 / 貨號查詢，可直接連至新竹物流網頁顯示貨況。

#### URL 格式

```
https://hctapiweb.hct.com.tw/phone/searchGoods_Main.aspx?no=加密字串&v=xxxxxx
```

| 參數 | 說明 |
|------|------|
| `no` | 加密後的訂單編號或貨號 |
| `v` | 金鑰版本 (申請時提供) |

#### 使用情境

> 產生的網址可放置於貴司網頁供客戶點擊查詢。

範例 (PHP，加密函式 `encryptHct()` 為申請後 HCT 提供之演算法)：

```php
<?php
$orderId = 'A00001';
$encrypted = encryptHct($orderId);          // HCT 自訂加密
$keyVersion = 'abcdef';

$trackUrl = sprintf(
    'https://hctapiweb.hct.com.tw/phone/searchGoods_Main.aspx?no=%s&v=%s',
    urlencode($encrypted),
    $keyVersion
);

echo "<a href=\"{$trackUrl}\" target=\"_blank\">查詢貨況</a>";
```

---

### 多筆貨號查詢 (XML POST)

提供**多筆**訂單編號 / 貨號查詢，回傳 XML 加密後字串，解密後即可使用。

#### 端點

```
POST https://hctapiweb.hct.com.tw/phone/searchGoods_Main_Xml.ashx?no=加密後XML&v=xx
```

> ※ 請求類型請使用 **POST**

#### 加密前傳出格式 (XML)

```xml
<?xml version="1.0" encoding="utf-8"?>
<qrylist>
  <order orderid="1234567890"></order>
  <order orderid="1234567891"></order>
</qrylist>
```

#### 解密後返回格式 — 有貨況

```xml
<?xml version="1.0" encoding="utf-8"?>
<rlist>
  <orders ordersid="1234567890">
    <order orderid="1234567890" wrktime="YYYY/MM/DD HH24:MM"
           category="狀態分類" status="貨物狀況" />
    <order orderid="1234567890" wrktime="YYYY/MM/DD HH24:MM"
           category="狀態分類" status="貨物狀況 2" />
  </orders>
  <orders ordersid="1234567891">
    <order orderid="1234567891" wrktime="YYYY/MM/DD HH24:MM"
           category="狀態分類" status="貨物狀況" />
  </orders>
</rlist>
```

#### 解密後返回格式 — 無貨況

```xml
<?xml version="1.0" encoding="UTF-8"?>
<rlist />
```

#### 注意事項

| # | 規則 |
|---|------|
| 1 | 一般貨況**僅供查詢 30 天內資料**；歷史查詢需聯繫原申請營業所 |
| 2 | 訂單編號與十碼貨號**只能擇一**進行查詢，申請時即決定 |
| 3 | 若使用訂單編號查詢，**需綁定特約客戶帳號 + 客戶代號** |
| 4 | XML 多筆查詢**單次上限 100 筆**，且需等前次回傳後才可再次提交 |
| 5 | 系統每日凌晨 **03:40 - 04:30** 維護，期間無貨況更新 |
| 6 | 異常請聯繫 02-2837-1122 #5123 許先生 |

---

### 貨況對應表

HCT 中文貨況分類，以 `category` (狀態分類) + `status` (詳細描述) 兩層結構回傳。下表為**附件 - 貨況對應表**完整摘錄。

#### 集貨類

| category (狀態分類) | status (貨物狀況) |
|---------|------|
| 集貨 | 已由 xx 取件完成 |
| 卸集貨 | 貨件已達 xx，貨件整理中。貨物件數共 N 件 |
| 發送 | 貨件已抵達 xx，前往配送站途中 |
| 到著 | 貨件已抵達 xx，分貨中 |
| 配達 | 貨件由 xx 人員配送中 |
| 持回 | 貨件由 xx 保管中 |

#### 派遣類

| category | status |
|---------|------|
| 派遣 | 取貨通知處理中 |
| 支援 | xx 取件中 |
| 客戶不在 | 寄貨人外出無法收件 |
| 已取 | xx 已至客戶端取回貨件 |
| 誤派 | xx 取件中 |
| 址誤 | 取件異常地址錯誤，xx 處理中 |
| 同業收取 | 取件異常，貨件由其他同業取走 |
| 無貨可退 | 取件異常，無貨件可收 |
| 其他 | 取件異常，專人處理中 |

#### 預計到件時段

| category | status |
|---------|------|
| 預計 12 點前 | 到客戶端 xx 取件中 |
| 預計 15 點前 | 到客戶端 xx 取件中 |
| 預計 17 點前 | 到客戶端 xx 取件中 |
| 預計 17 點後 | 到客戶端 xx 取件中 |

#### 取件異常

| category | status |
|---------|------|
| 查無此人 | 該地址查無此人，確認中 |
| 電聯異常 | 已電話聯繫，無人接聽 |
| 商品保留不退 | 收件人確定保留商品，取消退貨 |
| 約定收件 | 寄貨人外出，另約時間再次取件 |
| 公司行號休息 | 收件地址為公司行號，本日休假 |
| 派遣取消 | 廠商通知取消取件 |
| 派遣確認 | xx 已派遣人員取件中 |

#### 配交完成 / 異常

| category | status |
|---------|------|
| 正常配交 | 貨件已由 xx 送達。貨物件數共 N 件 |
| 缺件配達 | xx 缺件配交 |
| 破損配達 | xx 破損配交 |
| 客戶不在 | 送達客戶不在，xx 保管中 |
| 地址錯誤 | 收貨人地址異常，xx 處理中 |
| 查無此人 | 該地址查無此人，xx 處理中 |
| 電聯異常 | 已電話聯繫，無人接聽 |
| 到站自領 | 與客戶另約時間到站自領，xx 保管中 |
| 拒收退回 | 貨件已退回，退貨號碼為 xx |

#### 委外配送

| category | status |
|---------|------|
| 委外配送中 | 貨件由 xx 委外金門協力商人員配送中 |
| 委外配送中 | 貨件由 xx 委外澎湖協力商人員配送中 |
| 委外配送中 | 貨件由 xx 種外協力商人員配送中 |
| 委外配送中 | 貨件由 xx 轉運中 |

> 本工具包未提供完整 `category → 內部訂單狀態` 的對應表；建議依電商系統自行規劃 `delivered` / `in_transit` / `failed` 等內部狀態的映射。

---

## 出貨/託運單服務 (EDI Web Service)

### 端點

```
https://Hctrt.hct.com.tw/EDI_WebService2/Service1.asmx
```

> 此端點為 **SOAP Web Service**，亦提供 JSON / XML 變體方法。可透過 `?wsdl` 取得 SOAP 描述檔 (`Service1.asmx?wsdl`)。

### 重要規則

| 規則 | 說明 |
|------|------|
| **客戶可選擇是否上傳新竹貨號** | 一併上傳新竹貨號 (區間及規則洽 HCT 資訊人員)；或留空，由回傳值取得系統配號 |
| **新竹貨號 + 訂單編號** | 當日重複上傳，視同**更正**資料內容 |
| **訂單編號** | 同一個 `ESDATE` (出貨日期) **不可重複** |
| **新竹貨號** | **100 天內不可重複** |
| **總表列印** | 除標籤外仍需列印**出貨總表 (一式二份)**，供現場交接貨件使用 |

---

### TransData — 傳入託運資料

#### SOAP 方法簽章

```csharp
DataSet TransData(string Company, string password, DataSet data)
string  TransData_Json(string Company, string password, string json)
string  TransData_XML(string Company, string password, string xml)
```

#### 傳入欄位 (Data 欄位、說明、長度)

> PS：「預設值」欄位若有傳入值，**優先使用 DataTable 欄位內資料**

| 欄位名稱 | 欄位說明 | 欄位長度 | 備註 |
|---------|---------|---------|------|
| `epino` | 訂單編號 | Char(30) | **必要欄位** |
| `ercsig` | 收貨人名稱 | Char(40) | **必要欄位** |
| `ertel1` | 收貨人電話 1 | Char(15) | **必要欄位** |
| `ertel2` | 收貨人電話 2 | Char(15) | |
| `eraddr` | 收貨人地址 | Char(100) | **必要欄位** |
| `ejamt` | 件數 | Char(4) | **必要欄位** (最小為 1) |
| `eqamt` | 重量 | Char(5) | **必要欄位** (小數進位到整數) |
| `esdate` | 出貨日期 | Char(8) | 預設今天 (`YYYYMMDD`) |
| `escsno` | 客代 | Char(11) | 預設值 |
| `esstno` | 出貨站 | Char(4) | 預設值 |
| `edelno` | 新竹貨號 | Char(10) | 預設值 (如無提供系統自行配號) |
| `etcsig` | 出貨人名稱 | Char(40) | 預設值 |
| `ettel1` | 出貨人電話 1 | Char(15) | 預設值 |
| `ettel2` | 出貨人電話 2 | Char(15) | 預設值 |
| `etaddr` | 出貨地址 | Char(100) | 預設值 |
| `eddate` | 指定日期 | Char(8) | 預設空白 (小於今日代空白) |
| `eqmny` | 代收貨款 | Char(5) / Char(8) | 預設值 0；JSON/XML 變體為 Char(8) |
| `eprdct` | 傳票類別 | Char(2) | 月結 `11` (預設) / 到付 `21` / 現收 `31` |
| `emark` | 備註 | Char(100) | |
| `eprdcl2` | 商品種類 | Char(3) | 一般 `001` (預設) / 冷凍 `003` / 冷藏 `008` |
| `egamt` | 報值金額 | Char(5) | 保值貨物應報值，加收所報值金額 1% 為報值費 |

#### 回傳欄位

| 欄位名稱 | 欄位說明 |
|---------|---------|
| `Num` | 傳送序號 |
| `success` | 結果 (新增 `Y` / 修改 `R` / 失敗 `N`) |
| `edelno` | 新竹貨號 |
| `epino` | 訂單編號 |
| `erstno` | 到著站號碼 |
| `eqamt` | 重量 |
| `image` | 標籤圖片字串 (Hex 字串，需轉 byte → Bitmap) |
| `ErrMsg` | 異常錯誤訊息 |

#### JSON 範例

**傳入值：**

```json
[
  {
    "epino": "A00001",
    "ercsig": "Mary",
    "ertel1": "0911123456",
    "eraddr": "台中市大雅區中清路三段 513 號",
    "ejamt": "1",
    "eqamt": "10"
  },
  {
    "epino": "A00002",
    "ercsig": "Mary",
    "ertel1": "0911123456",
    "eraddr": "台中市大雅區中清路三段 513 號",
    "ejamt": "1",
    "eqamt": "5"
  }
]
```

**回傳值：**

```json
[
  {
    "Num": "1",
    "success": "Y",
    "edelno": "0000000001",
    "epino": "A00001",
    "erstno": "4004",
    "eqamt": "10",
    "image": "…(Hex 字串)…",
    "ErrMsg": null
  },
  {
    "Num": "2",
    "success": "Y",
    "edelno": "0000000002",
    "epino": "A00002",
    "erstno": "4004",
    "eqamt": "5",
    "image": "…(Hex 字串)…",
    "ErrMsg": null
  }
]
```

#### XML 範例

**傳入值：**

```xml
<info>
  <DataRow>
    <epino>A00001</epino>
    <ercsig>Mary</ercsig>
    <ertel1>0911123456</ertel1>
    <eraddr>台中市大雅區中清路三段 513 號</eraddr>
    <ejamt>1</ejamt>
    <eqamt>10</eqamt>
  </DataRow>
  <DataRow>
    <epino>A00002</epino>
    <ercsig>Mary</ercsig>
    <ertel1>0911123456</ertel1>
    <eraddr>台中市大雅區中清路三段 513 號</eraddr>
    <ejamt>1</ejamt>
    <eqamt>5</eqamt>
  </DataRow>
</info>
```

**回傳值：**

```xml
<info>
  <DataRow>
    <Num>1</Num>
    <success>Y</success>
    <edelno>0000000001</edelno>
    <epino>A00001</epino>
    <erstno>4004</erstno>
    <eqamt>10</eqamt>
    <image>…</image>
    <ErrMsg></ErrMsg>
  </DataRow>
  <DataRow>
    <Num>2</Num>
    <success>Y</success>
    <edelno>0000000002</edelno>
    <epino>A00002</epino>
    <erstno>4004</erstno>
    <eqamt>5</eqamt>
    <image>…</image>
    <ErrMsg></ErrMsg>
  </DataRow>
</info>
```

#### 圖片字串轉換 (C# 官方範例)

回傳的 `image` 欄位為 **Hex 字串**，需轉換為 byte 後再轉成 Bitmap：

```csharp
// 字串轉 byte
byte[] GetBytes(string HexString)
{
    int byteLength = HexString.Length / 2;
    byte[] bytes = new byte[byteLength];
    string hex;
    int j = 0;
    for (int i = 0; i < bytes.Length; i++)
    {
        hex = new String(new Char[] { HexString[j], HexString[j + 1] });
        bytes[i] = HexToByte(hex);
        j = j + 2;
    }
    return bytes;
}

byte HexToByte(string hex)
{
    if (hex.Length > 2 || hex.Length <= 0)
        throw new ArgumentException("hex must be 1 or 2 characters in length");
    return byte.Parse(hex, System.Globalization.NumberStyles.HexNumber);
}

// byte 轉成圖片 (1bit 黑白)
Bitmap image(byte[] b)
{
    MemoryStream ms = new MemoryStream(b);
    Bitmap bmp = (Bitmap)Bitmap.FromStream(ms);
    BitmapData bmpData = bmp.LockBits(
        new Rectangle(0, 0, bmp.Width, bmp.Height),
        ImageLockMode.ReadOnly,
        PixelFormat.Format1bppIndexed);
    bmp = new Bitmap(bmp.Width, bmp.Height, bmpData.Stride,
        PixelFormat.Format1bppIndexed, bmpData.Scan0);
    return bmp;
}
```

#### 設定檔注意事項 (官方提示)

##### TransData (SOAP)

> 如果需要一次接收 2 張以上圖片，需要將 config 裡的
> `maxBufferSize="65536"` `maxReceivedMessageSize="65536"`
> **65536 的數字改成大一點**，因為 1 張圖片轉成 string 大約就 2 萬多。

##### TransData_JSON

> 使用 JSON 接收圖檔字串，需要將 config 裡的
> `readerQuotas` `maxStringContentLength="8192"`
> **8192 數字改成大一點**，因為 1 張圖片轉成 string 大約就 2 萬多。

##### 批次大小

> **PS：傳送一批資料請不要超過 30 筆，若使用回傳圖檔，一次上限為 5 筆。**

---

### UpdData — 修改重量

#### SOAP 方法簽章

```csharp
DataSet UpdData(string Company, string password, DataSet data)
string  UpdData_Json(string Company, string password, string json)
string  UpdData_XML(string Company, string password, string xml)
```

#### 傳入欄位

| 欄位名稱 | 欄位說明 | 欄位長度 | 備註 |
|---------|---------|---------|------|
| `epino` | 訂單編號 | Char(30) | **必要欄位** |
| `edelno` | 新竹貨號 | Char(10) | **必要欄位** |
| `eqamt` | 重量 | Char(5) | **必要欄位** |

#### 回傳欄位

| 欄位名稱 | 欄位說明 |
|---------|---------|
| `Num` | 傳送序號 |
| `success` | 結果 (修改 `R` / 失敗 `N`) |
| `edelno` | 新竹貨號 |
| `epino` | 訂單編號 |
| `eqamt` | 重量 |
| `ErrMsg` | 異常錯誤訊息 |

---

### TransReport — 列印總表

當日確認出貨時呼叫 (**18:00 前上傳**)，產出**出貨總表 (一式二份)**，供現場交接貨件使用。

#### SOAP 方法簽章

```csharp
DataSet TransReport(string Company, string password, DataSet dsCus)
string  TransReport_Json(string Company, string password, string dsCusJson)
string  TransReport_XML(string Company, string password, string dsCusXML)
```

#### 傳入欄位

| 欄位名稱 | 欄位說明 | 欄位長度 | 備註 |
|---------|---------|---------|------|
| `epino` | 訂單編號 | Char(30) | **必要欄位** |
| `edelno` | 新竹貨號 | Char(10) | **必要欄位** |

#### 回傳欄位

| 欄位名稱 | 欄位說明 |
|---------|---------|
| `Num` | 序號 |
| `success` | 結果 (成功 `Y` / 失敗 `N`) |
| `edelno` | 新竹貨號 |
| `epino` | 訂單編號 |
| `ErrMsg` | 異常錯誤訊息 |

#### XML 範例

**傳入值：**

```xml
<info>
  <DataRow>
    <epino>A00001</epino>
    <edelno>1234567890</edelno>
  </DataRow>
  <DataRow>
    <epino>A00002</epino>
    <edelno>1234567894</edelno>
  </DataRow>
</info>
```

**回傳值：**

```xml
<info>
  <DataRow>
    <Num>1</Num>
    <success>Y</success>
    <edelno>0000000001</edelno>
    <epino>A00001</epino>
    <erstno>4004</erstno>
    <eqamt>10</eqamt>
    <ErrMsg></ErrMsg>
  </DataRow>
  <DataRow>
    <Num>2</Num>
    <success>Y</success>
    <edelno>0000000002</edelno>
    <epino>A00002</epino>
    <erstno>4004</erstno>
    <eqamt>5</eqamt>
    <ErrMsg></ErrMsg>
  </DataRow>
</info>
```

#### JSON 範例

**傳入值：**

```json
[
  { "epino": "A00001", "edelno": "1234567890" },
  { "epino": "A00002", "edelno": "1234567894" }
]
```

**回傳值：**

```json
[
  {
    "Num": "1",
    "success": "Y",
    "edelno": "0000000001",
    "epino": "A00001",
    "erstno": "4004",
    "eqamt": "10",
    "ErrMsg": null
  },
  {
    "Num": "2",
    "success": "Y",
    "edelno": "0000000002",
    "epino": "A00002",
    "erstno": "4004",
    "eqamt": "5",
    "ErrMsg": null
  }
]
```

---

### QueryEDELNO — 查詢貨號

由**訂單編號**反查已配發的**新竹貨號**。

#### SOAP 方法簽章

```csharp
DataSet QueryEDELNO(string company, string password, DataSet data)
string  QueryEDELNO_Json(string company, string password, string json)
string  QueryEDELNO_Xml(string company, string password, string xml)
```

#### 輸入規則

> `data` / `json` / `xml`：欲查詢貨號的訂單編號 (多筆可用 **`,` 逗號分隔**，**訂單編號中不能有逗號**)

範例輸入：`P002,S444` 或 `A001,P003,S444,P001`

#### 回傳欄位

| 欄位名稱 | 型別 | 欄位說明 |
|---------|------|---------|
| `success` | String | 結果 (成功 `Y` / 失敗 `N`) |
| `edelno` | String | 新竹貨號 |
| `epino` | String | 訂單編號 |
| `ErrMsg` | String | 異常錯誤訊息 |

#### JSON 回傳範例

傳入 `epino` 值為 `"P002,S444"`：

```json
[
  {
    "success": "Y",
    "edelno": "2000001054",
    "epino": "P002",
    "ErrMsg": ""
  },
  {
    "success": "N",
    "edelno": "",
    "epino": "S444",
    "ErrMsg": "查無資料"
  }
]
```

#### XML 回傳範例

傳入 `epino` 值為 `"A001,P003,S444,P001"`：

```xml
<info>
  <DataRow>
    <success>Y</success>
    <edelno>2000001080</edelno>
    <epino>A001</epino>
    <ErrMsg></ErrMsg>
  </DataRow>
  <DataRow>
    <success>Y</success>
    <edelno>2000001065</edelno>
    <epino>P003</epino>
    <ErrMsg></ErrMsg>
  </DataRow>
  <DataRow>
    <success>N</success>
    <edelno></edelno>
    <epino>S444</epino>
    <ErrMsg>查無資料</ErrMsg>
  </DataRow>
  <DataRow>
    <success>Y</success>
    <edelno>2000001091</edelno>
    <epino>P001</epino>
    <ErrMsg></ErrMsg>
  </DataRow>
</info>
```

---

### R_TransData — 逆物流託運資料

逆物流 (退貨/取件) 上傳資料。**目前僅提供 JSON 格式**。

#### SOAP 方法簽章

```csharp
string R_TransData_Json(string Company, string password, string json)
```

#### 傳入欄位

| 欄位名稱 | 欄位說明 | 欄位長度 | 備註 |
|---------|---------|---------|------|
| `epino` | 訂單編號 | Char(30) | **必要欄位**，**不可重複** |
| `ercsig` | 退貨人名稱 | Char(40) | **必要欄位**，逆物流跟誰收 |
| `ertel1` | 退貨人電話 1 | Char(15) | **必要欄位**，逆物流跟誰收的電話 |
| `ertel2` | 退貨人電話 2 | Char(15) | |
| `eraddr` | 退貨人地址 | Char(100) | **必要欄位**，逆物流跟誰收的地址 |
| `ejamt` | 件數 | Char(4) | **必要欄位** (總長運費的件數**只能輸入 1**) |
| `eqamt` | 重量 | Char(5) | 總長重量只能 `60` / `90` / `120` / `150` / `151~999` (如無提供抓系統預設值) |
| `esdate` | 出貨日期 | Char(8) | 預設今天 (`YYYYMMDD`) |
| `escsno` | 客代 | Char(11) | 預設值 |
| `edelno` | 新竹貨號 | Char(10) | 預設值 (如無提供系統自行配號) |
| `etcsig` | 收貨人名稱 | Char(40) | 預設值 |
| `ettel1` | 收貨人電話 1 | Char(15) | 預設值 |
| `etaddr` | 收貨地址 | Char(100) | 預設值 |
| `emark` | 備註 | Char(100) | |
| `eprdcl2` | 商品種類 | Char(3) | 一般 `001` (預設) / 冷凍 `003` / 冷藏 `008` |
| `edelno2` | **原查貨號碼** | Char(10) | **原正物流出貨查貨號碼** |

#### 回傳欄位

| 欄位名稱 | 欄位說明 |
|---------|---------|
| `Num` | 傳送序號 |
| `success` | 結果 (新增 `Y` / 失敗 `N`) |
| `edelno` | 新竹查貨貨號 |
| `epino` | 訂單編號 |
| `erstno` | 退貨人到著站號碼 (逆物流跟誰收的站所代號) |
| `eqamt` | 重量 |
| `ErrMsg` | 異常錯誤訊息 |

#### JSON 範例

**傳入值：**

```json
[
  {
    "epino": "101000000012345",
    "ercsig": "張三",
    "ertel1": "0255927298",
    "ertel2": "",
    "eraddr": "台北市士林區中山北路六段 88 號",
    "ejamt": "1",
    "eqamt": "60",
    "esdate": "",
    "escsno": "12345678900",
    "edelno": "",
    "etcsig": "大大消防",
    "ettel1": "0911123456",
    "ettel2": "",
    "etaddr": "台中市大雅區中清路三段 513 號",
    "emark": "",
    "eprdcl2": "001",
    "edelno2": "8812213345"
  },
  {
    "epino": "101000000012346",
    "ercsig": "李四",
    "ertel1": "035218811",
    "ertel2": "",
    "eraddr": "新竹縣新豐鄉建興路 100 號",
    "ejamt": "1",
    "eqamt": "",
    "esdate": "",
    "escsno": "12345678900",
    "edelno": "",
    "etcsig": "大大消防",
    "ettel1": "0911123456",
    "ettel2": "",
    "etaddr": "台中市大雅區中清路三段 513 號",
    "emark": "",
    "eprdcl2": "001"
  }
]
```

**回傳值：**

```json
[
  {
    "Num": "1",
    "Success": "N",
    "Edelno": "",
    "Epino": "101000000012345",
    "Erstno": "1247",
    "Eqamt": "60",
    "ErrMsg": "原貨號檢查碼錯誤"
  },
  {
    "Num": "2",
    "Success": "Y",
    "Edelno": "2250446752",
    "Epino": "101000000012346",
    "Erstno": "2060",
    "Eqamt": "9",
    "ErrMsg": ""
  }
]
```

---

## 錯誤原因明細

### TransData 錯誤訊息

| 錯誤訊息 | 錯誤原因 |
|---------|---------|
| 公司名稱或密碼錯誤 | Company / password 驗證失敗 |
| 貨號重複 | 一個月內貨號重複 |
| 貨號錯誤 | 沒新竹貨號 or 新竹貨號沒有 10 碼 |
| 貨號檢查碼錯誤 | 貨號最後一碼規則 |
| 訂單編號錯誤 | 訂單編號空白 |
| 客代錯誤 | 客代沒有 11 碼 |
| 件數錯誤 | 件數 0 |
| 重量錯誤 | 重量 0 |
| 收貨人名稱錯誤 | 收貨人空白 |
| 收貨人電話錯誤 | 收貨人電話空白 |
| 收貨人地址錯誤 | 收貨人地址空白 |
| 出貨站錯誤 | 出貨站沒有 4 碼 |
| 代收貨款錯誤 | TYPE = 41 但是沒有代收 |
| 一個月內貨號重複 | 同一貨號 30 天內重複 |
| 訂單編號重複 | 同一 ESDATE 內訂單編號重複 |

### UpdData 錯誤訊息

| 錯誤訊息 | 錯誤原因 |
|---------|---------|
| 公司名稱或密碼錯誤 | 帳密失敗 |
| 重量錯誤 | 重量 0 或非法 |
| 查無貨號和訂單編號 | 找不到對應託運單 |

### TransReport 錯誤訊息

| 錯誤訊息 | 錯誤原因 |
|---------|---------|
| 查無貨號 | DB 沒貨號 |
| 已經上傳過此筆 | `ISMASTER = 1` (已上傳過總表) |

### R_TransData_Json 錯誤訊息

| 錯誤訊息 | 錯誤原因 |
|---------|---------|
| 貨號重複 | 三個月內貨號重複 |
| 貨號錯誤 | 貨號格式錯誤 |
| 貨號檢查碼錯誤 | 貨號最後一碼規則錯誤 |
| 貨號錯誤必須是 2 開頭 | 逆物流貨號需以 `2` 開頭 |
| 原貨號錯誤 | `edelno2` 原查貨號碼錯誤 |
| 訂單編號錯誤 | 訂單編號空白 |
| 客代錯誤 | 客代格式錯誤 |
| 件數錯誤 | 件數非法 |
| 重量錯誤 | 重量非法 |
| 退貨人名稱錯誤 | 退貨人空白 |
| 退貨人電話錯誤 | 退貨人電話空白 |
| 退貨人地址錯誤 | 退貨人地址空白 |
| 退貨站錯誤 | 退貨站代號錯誤 |
| 收貨人名稱錯誤 | 收貨人空白 |
| 收貨人電話錯誤 | 收貨人電話空白 |
| 收貨人地址錯誤 | 收貨人地址空白 |
| 收貨站錯誤 | 收貨站代號錯誤 |
| 總長請輸入重量 60、90、120、150、151~999 | 逆物流總長重量不在允許值內 |
| 總長件數只能為 1 件 | 逆物流件數限制 |
| 未建收退貨貨號區間 | HCT 端尚未建立逆物流貨號區間 |
| 三個月內貨號重複 | 逆物流貨號 90 天唯一 |
| 訂單編號重複 | 訂單編號於系統內已存在 |

---

## 整合最佳實務

### 1. 帳密與金鑰管理

- `Company` / `password` 與加解密金鑰請統一存放於後端 secrets 管理 (Vault / KMS / 環境變數)
- 切勿將測試帳號 `test/test1` 上線
- 加解密金鑰版本 `v` 視為設定，避免硬編碼

### 2. 託運單建立流程

```
1. 建立訂單 → 預先保留訂單編號 (epino)
2. 出貨日 → 呼叫 TransData 上傳託運資料
3. 取得回應 → 儲存 edelno (新竹貨號)、erstno (到著站)、image (標籤)
4. 列印標籤 → 將 image Hex 字串轉 Bitmap 印出
5. 18:00 前 → 呼叫 TransReport 確認當日出貨 (重要!)
6. 列印總表一式二份 → 現場交接貨件使用
```

> **TransReport 必呼叫**：未呼叫 TransReport 即視為**未確認出貨**，HCT 不會排車收件。

### 3. 重量更新時機

當實際過磅重量與預估不同時，**在 TransReport 之前**呼叫 `UpdData` 修改重量；TransReport 後重量即固化。

### 4. 貨況查詢策略

| 場景 | 建議 API |
|------|---------|
| 客戶端「查詢貨況」按鈕 | 網頁串接模式 (URL 嵌入) |
| 後端排程同步多筆貨況 | XML 多筆查詢 (每次 ≤ 100 筆) |
| 訂單列表顯示「目前狀態」 | XML 多筆查詢 + 內部狀態映射 |

> 貨況僅保留 30 天，請於後端 DB 持久化關鍵狀態 (集貨 / 配達 / 異常)。

### 5. 批次大小

| API | 批次上限 |
|-----|---------|
| TransData (純資料) | 30 筆 / 批 |
| TransData (含 image 回傳) | **5 筆 / 批** |
| 多筆貨號 XML 查詢 | 100 筆 / 批 |

### 6. 重複保護

| 鍵 | 重複窗口 |
|---|---------|
| `epino` (訂單編號) | 同一 `esdate` 內唯一 |
| `edelno` (新竹貨號) | 100 天唯一 |
| 逆物流 `edelno` | 90 天唯一 (錯誤訊息為「三個月內貨號重複」) |

### 7. 重試策略

- HCT 系統每日 **03:40 - 04:30** 維護，建議排程避開此時段
- 對暫時性 5xx 錯誤可重試 (建議指數退避，最多 3 次)
- 對「貨號重複」「貨號檢查碼錯誤」等業務型錯誤**不可盲目重試**，需人工檢核

### 8. 跨語言實作建議

由於官方僅提供 .NET / C# Sample (`DataSet` 為 .NET 特有型別)，建議：

- **Java / Kotlin / Go / Python / Node.js**：直接使用 `*_Json` / `*_XML` 變體方法，避免處理 .NET DataSet 序列化
- **PHP**：可用 SOAP Extension 或直接 HTTP POST 至 `?wsdl` 端點
- **WSDL 取得**：`https://Hctrt.hct.com.tw/EDI_WebService2/Service1.asmx?wsdl`

---

## aggregator vs 直連對照

| 構面 | 透過 aggregator (ECPay/PayNow/SmilePay) | 直連 HCT API |
|------|----------------------------------------|-------------|
| **申請門檻** | 低 (註冊網路會員即可) | 中高 (需與營業所簽約) |
| **適合規模** | 個人/中小型電商 | 中大型企業 / ERP 整合 |
| **費率** | aggregator 抽成 + 物流費 | 直接費率 (依量級議價) |
| **物流業者切換** | 改 `LogisticsSubType` 即可 | 僅限 HCT |
| **託運單編號** | aggregator 包裝後的 ID | 原生新竹貨號 (10 碼) |
| **貨況同步** | aggregator webhook | 自行排程查詢 (XML 多筆) |
| **逆物流** | 透過 aggregator 建立 | `R_TransData` 直接送 HCT |
| **代碼對照** | `LogisticsSubType=TCAT` (黑貓) / `HCT` (新竹) | 不適用，直接是 HCT 系統 |
| **WSDL / SOAP** | 由 aggregator 抽象掉 | 需自行處理 SOAP / JSON / XML |

> 提醒：在 ECPay 物流文件中常出現的 `LogisticsSubType=TCAT` 是「黑貓宅急便」，並非新竹物流；新竹物流在 aggregator 中通常以獨立的子類型代碼表示，請以該 aggregator 文件為準。

---

## 官方資源

- **官方網站**：https://www.hct.com.tw/
- **API 端點 (查貨)**：https://hctapiweb.hct.com.tw/phone/searchGoods_Main.aspx
- **API 端點 (查貨 XML)**：https://hctapiweb.hct.com.tw/phone/searchGoods_Main_Xml.ashx
- **API 端點 (出貨 SOAP)**：https://Hctrt.hct.com.tw/EDI_WebService2/Service1.asmx
- **WSDL**：https://Hctrt.hct.com.tw/EDI_WebService2/Service1.asmx?wsdl
- **技術窗口**：02-2837-1122 #5123 (許先生)
- **官方文件**：申請後由 HCT 站所電腦負責人提供 PDF (`API服務說明_V1.pdf`，27 頁)
- **加密 Sample Code**：申請後由 HCT 提供 (C# 版本)

---

最後更新：2026/05/07
