# SmilePay 電子發票 API 完整技術規格

> 來源：SmilePay 官方文件
> 注意：本 API 可接受 **POST** 與 **GET** 兩種傳輸方式
> 編碼：僅提供 UTF-8 編碼

---

## 目錄
1. [測試環境資料](#測試環境資料)
2. [開立發票](#1-開立發票-issue-invoice)
3. [開立折讓單](#2-開立折讓單-issue-allowance)
4. [作廢/註銷功能](#3-作廢註銷功能-voidcancel)
5. [列印發票](#4-列印發票-print-invoice)

---

## 測試環境資料
- **電子發票帳號 (Grvc)**：`SEI1000034`
- **驗證碼 (Verify_key)**：`9D73935693EE0237FABA6AB744E48661`
- **測試統編**：`80129529`

---

## 1. 開立發票 (Issue Invoice)

### 環境資訊
- **正式環境**：`https://ssl.smse.com.tw/api/SPEinvoice_Storage.asp`
- **測試環境**：`https://ssl.smse.com.tw/api_test/SPEinvoice_Storage.asp`

### 欄位參數
> 符號說明：Ｏ：必要、▲：非必要、Ｘ：不用填
> 請注意大小寫
> API主要為四大部分：使用者參數 \ 發票資訊 \ 商品明細 \ 買受人資訊

#### A. 使用者參數
| 參數名稱 | 名稱 | B2C | B2B | 格式 | 說明 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `Grvc` | 電子發票帳號 | Ｏ | Ｏ | 由速買配提供 | SEI1000034 |
| `Verify_key` | 驗證碼 | Ｏ | Ｏ | 由速買配提供 | 9D73935693EE0237FABA6AB744E48661 |

#### B. 發票資訊
| 參數名稱 | 名稱 | B2C | B2B | 格式 | 說明 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `InvoiceNumber` | 發票號碼 | ▲ | ▲ | 英文(2)+數字(8)共10碼<br>不可有符號 | 營業人自行管理字軌時使用<br>如需了解,請與速買配聯繫 |
| `RandomNumber` | 隨機碼 | ▲ | ▲ | 4字元(數字) | 同上 |
| `InvoiceDate` | 開立發票日期 | Ｏ | Ｏ | YYYY/MM/DD | B2C發票僅能開立48小時之內<br>B2B發票僅能開立168小時之內 |
| `InvoiceTime` | 開立發票時間 | Ｏ | Ｏ | HH:MM:SS | |
| `TrackSystemID` | 自訂字軌系統代號 | ▲ | ▲ | 中文/英文/數字 | 營業人在【字軌管理】設定，帶入後可指定使用該組字軌 |
| `Intype` | 發票稅率類型 | Ｏ | Ｏ | 07／08 | **07**：一般稅額計算之電子發票<br>(TaxType允許1/2/3/9)<br>**08**：特種稅額計算之電子發票<br>(TaxType允許2/3/4/9) |
| `TaxType` | 課稅別 | Ｏ | Ｏ | 1／2／3／4／9 | **1**：應稅<br>**2**：零稅率<br>**3**：免稅<br>**4**：應稅(特種稅率)<br>**9**：混合應稅與免稅(限收銀機發票無法分辨時使用) |
| `TaxRate` | 稅率 | ▲ | ▲ | 允許範圍：0.00~1.00 | 必須以小數格式傳入<br>當發票為【特種稅額】時輸入才有效<br>【Intype=08】與【TaxType=4／9】<br>根據行業別，傳入對應的稅率小數值(依國稅局公告為主)：<br>0.25 (特種飲食業，稅率 25%)<br>0.15 (特種飲食業，稅率 15%)<br>0.01 (查定課徵，稅率 1%)<br>0.001 (農產品相關，稅率 0.1%) |
| `BuyerRemark` | 買受人註記 | ▲ | ▲ | 1／2／3／4 | 可保留空白<br>**1**：得抵扣之進貨及費<br>**2**：得抵扣之固定資<br>**3**：不得抵扣之進貨及費用<br>**4**：不得抵扣之固定資口 |
| `CustomsClearanceMark` | 通關方式註記 | ▲ | ▲ | 1／2 | **若為零稅率發票，此為必填欄位**<br>**1**：非經海關出口<br>**2**：經海關出口 |
| `GroupMark` | 彙開註記 | ▲ | ▲ | Y | 可保留空白<br>如為彙開發票再填入 |
| `BondedAreaConfirm` | 買受人簽署適用<br>零稅率註記 | Ｘ | ▲ | 1／2／3／4 | 可保留空白<br>**1**：買受人為保稅區營業人<br>**2**：買受人為遠洋漁業營業人<br>**3**：買受人為自由貿易港區營業人<br>**4**：其他 |
| `ZeroTaxRateReason` | 零稅率原因 | ▲ | ▲ | 71～79 | **若為零稅率發票，此為必填欄位**<br>參照加值型及非加值型營業稅法第 7 條：<br>**71**：第一款 外銷貨物<br>**72**：第二款 與外銷有關之勞務，或在國內提供而在國外使用之勞務<br>**73**：第三款 依法設立之免稅商店銷售與過境或出境旅客之貨物<br>**74**：第四款 銷售與保稅區營業人供營運之貨物或勞務<br>**75**：第五款 國際間之運輸。但外國運輸事業在中華民國境內經營國際運輸業務者，應以各該國對中華民國國際運輸事業予以相等待遇或免徵類似稅捐者為限<br>**76**：第六款 國際運輸用之船舶、航空器及遠洋漁船<br>**77**：第七款 銷售與國際運輸用之船舶、航空器及遠洋漁船所使用之貨物或修繕勞務<br>**78**：第八款 保稅區營業人銷售與課稅區營業人未輸往課稅區而直接出口之貨物<br>**79**：第九款 保稅區營業人銷售與課稅區營業人存入自由港區事業或海關管理之保稅倉庫、物流中心以供外銷之貨物 |
| `MainRemark` | 總備註 | ▲ | ▲ | 200字元 | 呈現在A4、A5紙張格式 |
| `RelateNumber` | 相關號碼 | ▲ | ▲ | 20字元 | |
| `DonateMark` | 捐贈 | Ｏ | Ｏ | 1／0 | **1**：捐贈<br>**0**：不捐贈<br>有Buyer_id時,必須為0<br>捐贈時載具類型(CarrierType)不可填入 |
| `LoveKey` | 愛心碼 | ▲ | Ｘ | | DonateMark為1,此處不可為空 |
| `Visa_Last4` | 信用卡末四碼 | ▲ | ▲ | 4字元 | 如為刷卡交易，請填入卡號末四碼 |
| `data_id` | 自訂發票編號 | ▲ | ▲ | 50字元 | 如該號碼已開立過發票，將無法重複開立，除非發票作廢<br>檢查範圍為相同期別的發票 |
| `orderid` | 自訂號碼 | ▲ | ▲ | 30字元 | 營業人自訂使用 |
| `PosSystemID` | 營業人自定義系統代號 | ▲ | ▲ | 20字元(英文/數字) | 營業人自訂的系統代碼，用以區分不同開立來源 |
| `Certificate_Remark` | 發票證明聯備註 | ▲ | ▲ | 34字元 | 呈現在熱感紙證明聯與A4、A5紙張格式 |

#### C. 商品明細
> **注意**：除總金額(AllAmount)/單價含稅(UnitTAX)參數外均以【 `|` 】(半形)符號區隔，並依照商品明細排列，各項總數必須相同

| 參數名稱 | 名稱 | B2C | B2B | 格式 | 說明 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `Description` | 商品明細 | Ｏ | Ｏ | 商品1\|商品2 | 請勿填入符號，每項品名最多256個字 |
| `Quantity` | 數量明細 | Ｏ | Ｏ | 數量1\|數量2 | 純數字，必須大於0 |
| `UnitPrice` | 單價明細 | Ｏ | Ｏ | 單價1\|單價2 | 純數字，可以小於0<br>透過單價含稅(UnitTAX)指定金額含稅或未稅價 |
| `Unit` | 單位明細 | ▲ | ▲ | 單位1\|單位2 | 請勿填入符號，每項單位最多6個字 |
| `ProductTaxType` | 商品稅率明細 | ▲ | ▲ | 稅率1\|稅率2 | 課稅別(TaxType)【9：混合稅率】時必填<br>**1**：應稅<br>**3**：免稅 |
| `Remark` | 商品備註明細 | ▲ | ▲ | 備註1\|備註2 | 請勿填入符號，每項內容最多40個字 |
| `Amount` | 各明細總額 | Ｏ | Ｏ | 金額1\|金額2 | 由每項【數量*單價】計算<br>純數字，可以小於0 |
| `AllAmount` | 總金額(含稅) | Ｏ | Ｏ | 整數，不可小於0 | 由各明細總額(Amount)合計<br>**金額必須含稅** |
| `SalesAmount` | 應稅銷售額 | ▲ | ▲ | 整數，不可小於0 | 課稅別(TaxType)【9：混合稅率】B2C/B2B發票<br>營業人必須提供含稅銷售額<br>【1：應稅】B2B發票填入未稅銷售額 |
| `FreeTaxSalesAmount` | 免稅銷售額 | ▲ | Ｘ | 整數，不可小於0 | 僅在課稅別(TaxType)為【9：混合稅率】<br>營業人必須提供銷售額金額 |
| `ZeroTaxSalesAmount` | 零稅率銷售額 | ▲ | Ｘ | 整數，不可小於0 | |
| `UnitTAX` | 單價含稅 | Ｘ | ▲ | Y／N | 商品單價是否含稅<br>**Y**：含稅金額(預設)<br>**N**：未稅金額 |
| `TaxAmount` | 稅金 | Ｘ | ▲ | 整數，不可小於0 | 僅在B2B發票時才會生效<br>營業人自行計算發票稅金 |

#### D. 買受人資訊
| 參數名稱 | 名稱 | B2C | B2B | 格式 | 說明 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `Buyer_id` | 買受人統編 | Ｘ | Ｏ | | **有值：開立B2B發票**<br>**空值：開立B2C發票** |
| `CompanyName` | 買受人公司名稱 | Ｘ | ▲ | 30字元 | 請勿填入符號 |
| `Name` | 買受人姓名 | ▲ | Ｘ | 30字元 | 請勿填入符號 |
| `Phone` | 電話 | ▲ | ▲ | 0900123456 | 純數字，請勿填入符號 |
| `Facsimile` | 傳真 | Ｘ | ▲ | | 純數字，請勿填入符號 |
| `Email` | 信箱 | ▲ | ▲ | 80字元 | 多組信箱請用分號(;)分隔 |
| `Address` | 地址 | ▲ | ▲ | 100字元 | |
| `CarrierType` | 載具類型 | ▲ | Ｘ | | 速買配載具: `EJ0113`<br>手機條碼: `3J0002`<br>自然人憑證: `CQ0001` |
| `CarrierID` | 載具ID明碼 | ▲ | Ｘ | | 當載具類型(CarrierType)有值時，此處不可為空<br>使用速買配載具(EJ0113)可透過Email／Phone進行載具註冊，此處能保留空白 |
| `CarrierID2` | 載具ID暗碼 | ▲ | Ｘ | | 當載具類型(CarrierType)有值時，此處不可為空<br>使用速買配載具(EJ0113)可透過Email／Phone進行載具註冊，此處能保留空白 |

#### 開立規則與各欄位規則整理
|  | **買受人** | **個人** | **公司** |
| :--- | :--- | :--- | :--- |
| **捐贈** | 捐贈 | 填1 | Ｘ |
|  | 愛心碼 | Ｏ | Ｘ |
| **載具** | 載具類型 | Ｏ | Ｘ |
|  | 載具ID | Ｏ | Ｘ |
| **統編發票** | 統一編號 | Ｘ | Ｏ |

#### 發票範例 (測試區)

**B2C發票**：
```
https://ssl.smse.com.tw/api_test/SPEinvoice_Storage.asp?Grvc=SEI1000034&Verify_key=9D73935693EE0237FABA6AB744E48661&Name=速買配&Phone=0900000000&Email=Test@testmailserver.net&Intype=07&TaxType=1&LoveKey=&DonateMark=0&Description=商品1|商品2&Quantity=5|8&UnitPrice=10|15&Unit=顆|條&Amount=50|120&ALLAmount=170&InvoiceDate=2026/1/26&InvoiceTime=15:33:33
```

**B2B發票**：
```
https://ssl.smse.com.tw/api_test/SPEinvoice_Storage.asp?Grvc=SEI1000034&Verify_key=9D73935693EE0237FABA6AB744E48661&CompanyName=速買配&Phone=0900000000&Email=Test@testmailserver.net&Intype=07&TaxType=1&LoveKey=&DonateMark=0&Description=商品1|商品2&Quantity=5|8&UnitPrice=10|15&Unit=顆|條&Amount=50|120&ALLAmount=170&InvoiceDate=2026/1/26&InvoiceTime=15:33:33&Buyer_id=80129529
```

**B2G發票** (統編不可空白，商品金額必須含稅 UnitTAX=Y，發票類型必須帶入 B2B Einvoice_Type=B2B)：
```
https://ssl.smse.com.tw/api_test/SPEinvoice_Storage.asp?Grvc=SEI1000034&Verify_key=9D73935693EE0237FABA6AB744E48661&CompanyName=速買配&Phone=0900000000&Email=Test@testmailserver.net&Intype=07&TaxType=1&LoveKey=&DonateMark=0&Description=商品&Quantity=1&UnitPrice=100&Unit=顆&Amount=100&ALLAmount=100&InvoiceDate=2026/1/26&InvoiceTime=15:33:33&Buyer_id=80129529&UnitTAX=Y&Einvoice_Type=B2B
```

### 回應值
格式：XML
```xml
<SmilePayEinvoice>
    <Status>0</Status>
    <Desc></Desc>
    <Grvc>SEI1000002</Grvc>
    <orderno>order20171231</orderno>
    <data_id>inid00001</data_id>
    <InvoiceNumber>YY00000000</InvoiceNumber>
    <RandomNumber>1234</RandomNumber>
    <InvoiceDate>2017/12/31</InvoiceDate>
    <InvoiceTime>23:59:59</InvoiceTime>
    <InvoiceType>B2C</InvoiceType>
    <CarrierID></CarrierID>
</SmilePayEinvoice>
```

#### Xml Tag 說明
| 參數 | 名稱 | 說明 |
| :--- | :--- | :--- |
| `Status` | 狀態碼 | 回應值請參考下表 |
| `Desc` | 詳細原因 | 回應值請參考下表 |
| `orderno` | 自訂號碼 | |
| `data_id` | 自訂發票編號 | |
| `InvoiceNumber` | 發票號碼 | 實際發票開立號碼 |
| `RandomNumber` | 隨機碼 | |
| `InvoiceDate` | 開立日期 | |
| `InvoiceTime` | 開立時間 | |
| `InvoiceType` | 發票類型 | **B2C**：無統編,一般的銷售發票<br>**B2C2B**：有統編,可接受發票作廢<br>**B2B**：有統編,無法註銷<br>當買受人簽署適用零稅率註記(BondedAreaConfirm)有輸入值時給予此 |
| `CarrierID` | 載具ID | 如申請速買配載具則會回應載具號碼 |

#### 回應代號說明 (Status)
| 代號 | 說明 | 代號 | 說明 |
| :--- | :--- | :--- | :--- |
| `0` | 開立成功 | `-1001` | 商家帳號缺少參數 |
| `-10011` | 查無商家帳號 | `-10012` | 尚未開放B2B功能 |
| `-10013` | 尚未開放B2C功能 | `-10021` | 統一編號(Buyer_id)格式錯誤 |
| `-10022` | 統一編號不可捐贈(DonateMark)必須為0 | `-10023` | 統一編號(Buyer_id)內容錯誤 |
| `-10024` | 統一編號(Buyer_id)不可使用其他載具(CarrierType) | `-10025` | 缺少公司名稱(CompanyName) |
| `-10031` | 缺少開立日期(InvoiceDate、InvoiceTime) | `-10032` | 日期格式(InvoiceDate、InvoiceTime)錯誤 |
| `-10033` | B2C開立需再48hr內 | `-10034` | B2B開立需再168hr內 |
| `-10041` | 發票類別(Intype)錯誤 | `-10042` | 買受人註記欄(BuyerRemark)錯誤 |
| `-10043` | 通關方式註記(CustomsClearanceMark) | `-10044` | 捐贈註記(DonateMark)錯誤 |
| `-10045` | 愛心碼(LoveKey)空白 | `-10046` | 愛心碼伺服器異常 |
| `-10047` | 查無此愛心碼(LoveKey) | `-10048` | 課稅別(TaxType)錯誤 |
| `-10049` | 買受人簽署適用零稅率註記(BondedAreaConfirm)錯誤 | `-100410` | 總備註(MainRemark)錯誤 |
| `-100411` | 相關號碼(RelateNumber)錯誤 | `-100412` | 零稅率原因(ZeroTaxRateReason)錯誤 |
| `-10051` | 手機號碼(Phone)格式錯誤 | `-10052` | 載具號碼(CarrierID)錯誤 |
| `-10053` | 查無載具號碼(CarrierID) | `-10054` | 缺少建立載具參數,Email/Phone參數 |
| `-10055` | 建立載具失敗 | `-10056` | 查無手機條碼(CarrierID) |
| `-10057` | 自然人憑證(CarrierID)格式錯誤 | `-10058` | 載具類型(CarrierType)非允許使用的 |
| `-10061` | 商品各項目數量不符 | `-10062` | 內容長度不正確(單一品項)<br>品名(Description)：256個字,不可空白<br>單位(Unit)：6個字,可空白<br>商品備註(Remark)：40個字,可空白 |
| `-10063` | 商品數量(Quantity)內容錯誤 | `-10064` | 商品金額(UnitPrice、Amount)內容錯誤 |
| `-10065` | 商品小計(UnitPrice、Amount)驗算錯誤 | `-10066` | 商品總金額(AllAmount)驗算錯誤 |
| `-10067` | 商品與總金額(ALLAmount)不符合規定 | `-10068` | 混合稅率銷售額明細(SalesAmount、FreeTaxSalesAmount)內容錯誤 |
| `-10069` | 稅金(TaxAmount)與未稅銷售額(SalesAmount)驗算錯誤 | `-100610` | 稅率(TaxRate)內容錯誤 |
| `-100611` | 產品稅率(ProductTaxType)內容誤 | `-10071` | 無可用字軌 |
| `-10072` | 自訂發票編號 (data_id)重複 | `-10073` | 營業人自定義系統代號(PosSystemID)格式錯誤 |
| `-10081` | 信用卡末四碼(Visa_Last4)格式錯誤 | `-10082` | 發票證明聯備註(Certificate_Remark)格式錯誤 |
| `-10083` | 自訂發票編號(data_id)格式錯誤 | `-10084` | 自訂號碼(orderid)格式錯誤 |
| `-2001` | (InvoiceNumber)格式錯誤 | `-2002` | (RandomNumber)格式錯誤 |
| `-2003` | (InvoiceNumber)不可重複 | | |

---

## 2. 開立折讓單 (Issue Allowance)

### 環境資訊
- **正式環境**：`https://ssl.smse.com.tw/api/SPEinvoice_Storage_Allowance.asp`
- **測試環境**：`https://ssl.smse.com.tw/api_test/SPEinvoice_Storage_Allowance.asp`

### 欄位參數
> 符號說明：Ｏ：必要、▲：非必要、Ｘ：不用填

#### A. 使用者參數
| 參數名稱 | 名稱 | 格式 | 說明 |
| :--- | :--- | :--- | :--- |
| `Grvc` | 電子發票帳號 | | 由速買配提供 |
| `Verify_key` | 驗證碼 | | 由速買配提供 |

#### B. 折讓單資訊
| 參數名稱 | 名稱 | 格式 | 說明 |
| :--- | :--- | :--- | :--- |
| `InvoiceNumber` | 發票號碼 | | 需折讓的發票號碼 |
| `InvoiceDate` | 發票日期 | | 發票號碼日期 |
| `AllowanceNumber` | 折讓單號碼 | 15字元(英/數混合)<br>不可填入符號 | 可保留空白<br>速買配會自動產生 |
| `AllowanceDate` | 折讓日期 | YYYY-MM-DD | 可保留空白 |
| `AllowanceType` | 折讓類型 | 1／2 | **1**：買方開立折讓單<br>**2**：賣方開立折讓單(預設) |

#### C. 折讓明細
> 均以【 `|` 】(半形)符號區隔，並依照折讓明細排列，各項總數必須相同

| 參數名稱 | 名稱 | 格式 | 說明 |
| :--- | :--- | :--- | :--- |
| `Description` | 商品明細 | 商品1\|商品2 | 請勿填入符號 |
| `Quantity` | 數量明細 | 數量1\|數量2 | 純數字，必須大於0 |
| `UnitPrice` | 單價明細(未稅) | 單價1\|單價2 | 純數字，可以小於0 |
| `Unit` | 單位明細 | 單位1\|單位2 | 可保留空白<br>請勿填入符號 |
| `Amount` | 各明細總額(未稅) | 金額1\|金額2 | 由每項【數量 * 單價(未稅) 】計算<br>純數字，可以小於0 |
| `Tax` | 稅金 | 稅金1\|稅金2 | 營業人需自行計算稅金<br>純數字 |
| `TaxType` | 課稅別 | 課稅別1\|課稅別2 | **1**：應稅<br>**2**：零稅率<br>**3**：免稅<br>**4**：應稅(特種稅率) |

### 回應值
```xml
<SmilePayEinvoice>
    <Status>0</Status>
    <Desc></Desc>
    <Grvc>SEI1000002</Grvc>
    <InvoiceNumber>YY00000000</InvoiceNumber>
    <AllowanceNumber>YY00000000</AllowanceNumber>
</SmilePayEinvoice>
```

#### Xml Tag 說明
| 參數 | 名稱 | 說明 |
| :--- | :--- | :--- |
| `Status` | 狀態碼 | 回應值請參考下表 |
| `Desc` | 詳細原因 | 回應值請參考下表 |
| `Grvc` | 商家代號 | |
| `InvoiceNumber` | 發票號碼 | |
| `AllowanceNumber` | 折讓單號碼 | |

#### 回應代號說明
| 代號 | 說明 |
| :--- | :--- |
| `-1001` | 商家帳號缺少參數 |
| `-10011` | 查無商家帳號 |
| `-1002` | 發票號碼(InvoiceNumber)錯誤 |
| `-10021` | 商品不可空白 |
| `-10022` | 商品各項目數量不符 |
| `-10023` | 商品明細(Description)參數異常 |
| `-10024` | 數量明細(Quantity)參數異常 |
| `-10025` | 單價明細(UnitPrice)金額異常 |
| `-10026` | 稅金明細(TaxType)參數異常 |
| `-10027` | 稅率明細(Tax)參數異常 |
| `-10028` | 折讓日期(AllowanceDate)參數異常 |
| `-1003` | 查無此筆發票 |
| `-10031` | 超過可折讓金額 |
| `-10032` | 折讓單號碼(AllowanceNumber)不可重複 |

---

## 3. 作廢/註銷功能 (Void/Cancel)

### 環境資訊
- **正式環境**：`https://ssl.smse.com.tw/api/SPEinvoice_Storage_Modify.asp`
- **測試環境**：`https://ssl.smse.com.tw/api_test/SPEinvoice_Storage_Modify.asp`

### 欄位參數
> 符號說明：Ｏ：必要、▲：非必要、Ｘ：無法使用
> API主要為兩大部分：使用者參數 \ 相關欄位

#### A. 使用者參數
| 參數名稱 | 名稱 | 格式 | 說明 |
| :--- | :--- | :--- | :--- |
| `Grvc` | 商家代號 | | 由速買配提供 |
| `Verify_key` | 驗證碼 | | 由速買配提供 |

#### B. 相關欄位
| 參數名稱 | 名稱 | 格式 | 說明 |
| :--- | :--- | :--- | :--- |
| `InvoiceNumber` | 發票號碼 | | 填入需處理的發票號碼 |
| `InvoiceDate` | 發票日期 | | 該筆發票日期 |
| `AllowanceNumber` | 折讓單號碼 | | 填入需處理的折讓單號碼 |
| `AllowanceDate` | 折讓單日期 | | 該筆折讓單日期 |
| `types` | 服務類型 | | **Cancel**：作廢發票<br>**Void**：註銷發票<br>**CancelAllowance**：作廢折讓單<br>**StopProcessing**：取消執行<br>※取消執行說明：<br>停止作廢/註銷作業並返回先前狀態，<br>如果大平台已接收，將無法執行。<br>限發票才能使用 |
| `CancelReason` | 作廢原因 | 20字元 | 作廢發票/折讓單實際原因 |
| `ReturnTaxDocumentNumber` | 專案作廢核准文號 | 60字元 | 可保留空白<br>如有【專案作廢核准文號】請填入 |
| `VoidReason` | 註銷原因 | 20字元 | 註銷發票實際原因 |
| `Remark` | 備註 | 200字元 | |

#### 處理規則與各欄位規則整理
|  | **作廢發票** | **註銷發票** | **作廢折讓單** | **取消執行** |
| :--- | :--- | :--- | :--- | :--- |
| 發票號碼 | Ｏ | Ｏ | Ｘ | Ｏ |
| 發票日期 | Ｏ | Ｏ | Ｘ | Ｏ |
| 折讓單號碼 | Ｘ | Ｘ | Ｏ | Ｘ |
| 折讓單日期 | Ｘ | Ｘ | Ｏ | Ｘ |
| 作廢原因 | Ｏ | Ｘ | Ｏ | Ｘ |
| 專案作廢核准文號 | ▲ | Ｘ | Ｘ | Ｘ |
| 註銷原因 | Ｘ | Ｏ | Ｘ | Ｘ |
| 備註 | ▲ | ▲ | ▲ | Ｘ |

### 回應值
```xml
<SmilePayEinvoice>
    <Status>0</Status>
    <Desc></Desc>
    <Types></Types>
    <Grvc>SEI1000002</Grvc>
    <InvoiceNumber>YY00000000</InvoiceNumber>
    <AllowanceNumber>SMEE000000000000</AllowanceNumber>
    <CancelDate>2017/12/31</CancelDate>
    <CancelTime>23:59:59</CancelTime>
    <VoidDate>2017/12/31</VoidDate>
    <VoidTime>23:59:59</VoidTime>
    <RejectDate>2017/12/31</RejectDate>
    <RejectTime>23:59:59</RejectTime>
</SmilePayEinvoice>
```

#### Xml Tag 說明
| 參數 | 名稱 | 說明 |
| :--- | :--- | :--- |
| `Status` | 狀態碼 | 回應值請參考下表 |
| `Desc` | 詳細原因 | 回應值請參考下表 |
| `Nowstatus` | 物流狀態 | 僅在-2008時，才提供 |
| `Types` | 服務類型 | |
| `Grvc` | 商家代號 | |
| `InvoiceNumber` | 發票號碼 | |
| `AllowanceNumber` | 折讓單號碼 | |
| `CancelDate` | 發票作廢/折讓單作廢日期 | 僅在types=Cancel/CancelAllowance才回應 |
| `CancelTime` | 發票作廢/折讓單作廢時間 | 僅在types=Cancel/CancelAllowance才回應 |
| `VoidDate` | 發票註銷日期 | 僅在types=Void才回應 |
| `VoidTime` | 發票註銷時間 | 僅在types=Void才回應 |

#### 回應代號說明
| 代號 | 說明 |
| :--- | :--- |
| `-1000` | 商家帳號缺少參數 |
| `-1001` | 查無商家帳號 |
| `-1002` | 服務類型錯誤 |
| `-2001` | 缺少發票號碼(InvoiceNumber)或作廢原因(CancelReason) |
| `-2002` | 作廢原因(CancelReason)超過字數 |
| `-2003` | 專案作廢核准文號(ReturnTaxDocumentNumber)超過字數 |
| `-2004` | 備註(Remark)超過字數 |
| `-2005` | 缺少發票號碼(InvoiceNumber)或註銷原因(VoidReason) |
| `-2006` | 註銷原因(VoidReason)超過字數 |
| `-2007` | 缺少折讓單號碼(AllowanceNumber)或作廢原因(CancelReason) |
| `-2008` | 發票目前狀態不允許執行該動作 |
| `-2009` | 發票有折讓紀錄不允許執行該動作 |
| `-2010` | 查無該筆發票/折讓單 |

---

## 4. 列印發票 (Print Invoice)

### API 路徑與使用說明
使用者可以通過 POST 或 GET 方法將請求發送到相應的 API 端點，即可開啟發票列印畫面。

| 說明 | 環境 | API位置 |
| :--- | :--- | :--- |
| **網頁模式**<br>(瀏覽器列印對話框)<br>版型：A4/A5/證明聯 | 正式環境 | `https://einvoice.smilepay.net/einvoice/SmilePayCarrier/InvoiceDetails.php` |
|  | 測試環境 | `https://einvoice.smilepay.net/einvoice_test/SmilePayCarrier/InvoiceDetails.php` |
| **EPSON IP列印**<br>版型：證明聯 | 正式環境 | `https://einvoice.smilepay.net/einvoice/Invoice_Print/Invoice_Print_EPSON.php` |
|  | 測試環境 | `https://einvoice.smilepay.net/einvoice_test/Invoice_Print/Invoice_Print_EPSON.php` |

### 欄位參數
> 請注意大小寫

| 參數 | 名稱 | 格式 | 說明 |
| :--- | :--- | :--- | :--- |
| `Grvc` | 電子發票帳號 | 由速買配提供 | SEI1000034 |
| `Verify_key` | 驗證碼 | 由速買配提供 | 9D73935693EE0237FABA6AB744E48661 |
| `InNumber` | 發票號碼 | 英文(2)+數字(8)共10碼 | |
| `InvoiceDate` | 發票日期 | YYYY/MM/DD | |
| `RaNumber` | 發票認證碼 | 數字 | **B2C發票**：隨機碼<br>**B2B發票**：買受人統編 |
| `DetailPrint` | 呈現交易明細聯 | Y／不帶入 | 是否出現交易明細聯 |
| `AutoPrint` | 自動列印 | Y／不帶入 | 開啟網頁後自動執行列印 |

### 範例 (測試區)

**B2C發票**：
```
https://einvoice.smilepay.net/einvoice_test/SmilePayCarrier/InvoiceDetails.php?Grvc=SEI1000034&Verify_key=9D73935693EE0237FABA6AB744E48661&InNumber=HG00631928&InvoiceDate=2024/11/06&RaNumber=7572
```

**B2B發票**：
```
https://einvoice.smilepay.net/einvoice_test/SmilePayCarrier/InvoiceDetails.php?Grvc=SEI1000034&Verify_key=9D73935693EE0237FABA6AB744E48661&InNumber=HG00631929&InvoiceDate=2024/11/06&RaNumber=80129529
```

---

## 開發筆記 (踩坑紀錄)

> 以下是實際整合過程中遇到的問題與解決方案

### 1. 測試環境 vs 正式環境

**問題**：使用正式環境 URL 時顯示「尚未開放B2C功能」(-10013)

**原因**：需要在設定中啟用沙盒模式 (`isProd: false`)

**URL 對照**：
| 環境 | 開立發票 | 列印發票 |
|------|---------|---------|
| 測試 | `https://ssl.smse.com.tw/api_test/SPEinvoice_Storage.asp` | `https://einvoice.smilepay.net/einvoice_test/SmilePayCarrier/InvoiceDetails.php` |
| 正式 | `https://ssl.smse.com.tw/api/SPEinvoice_Storage.asp` | `https://einvoice.smilepay.net/einvoice/SmilePayCarrier/InvoiceDetails.php` |

### 2. AllAmount 金額驗算錯誤 (-10066)

**問題**：開發票時 `AllAmount: "0"`，但金額應該是 21000

**原因**：程式碼用 `data.TotalAmount`，但 B2C 時 TotalAmount 未設定

**解決**：
```typescript
// B2B: TotalAmount = 含稅總額
// B2C: SalesAmount = 含稅總額
AllAmount: String(data.TotalAmount || data.SalesAmount || '0')
```

### 3. orderid 格式錯誤 (-10084)

**問題**：`orderid` 超過 30 字元限制

**原因**：訂單編號格式 `INV-{recordId}-{timestamp}` 產生 43 字元

**解決**：
```typescript
orderid: data.OrderId.slice(0, 30)  // 限制 30 字元
data_id: data.OrderId               // 50 字元，用來防重複
```

### 4. 列印發票彈窗空白

**問題**：列印發票時彈窗空白

**原因**：SmilePay 用 GET 方法，參數在 URL query string，但系統錯誤地用 POST 表單提交

**解決**：
```typescript
// print-invoice route 判斷 method
if (printData.method === 'GET' && printData.url) {
    return jsonResponse({ type: 'redirect', url: printData.url })
}
```

### 5. 列印 B2C 發票需要隨機碼

**參數 RaNumber**：
- **B2C 發票**：使用 `RandomNumber`（開立時回傳）
- **B2B 發票**：使用買方統編

**重要**：開立發票成功後必須儲存 `randomNumber` 到 `invoiceRandomNum` 欄位

### 6. 金額計算

**B2C (二聯式)**：
- `AllAmount` = 含稅總額 (= SalesAmount)
- `UnitTAX` = 'Y' (單價含稅)

**B2B (三聯式)**：
- `AllAmount` = 含稅總額 (= TotalAmount)
- `SalesAmount` = 未稅金額
- `TaxAmount` = 稅額
- `UnitTAX` = 'N' (單價未稅)

### 7. 實作檔案

- **服務實作**：`lib/services/smilepay-invoice-service.ts`
- **API 路由**：`app/api/v1/financials/[id]/issue-invoice/route.ts`

---

## 相關文件

- [綠界 API 規格](./ECPAY_API_REFERENCE.md)
- [光貿 Amego API 規格](./AMEGO_API_REFERENCE.md)
- [發票開立流程](./INVOICE_FLOW.md)

---

最後更新：2026/01/28 + 實作筆記
