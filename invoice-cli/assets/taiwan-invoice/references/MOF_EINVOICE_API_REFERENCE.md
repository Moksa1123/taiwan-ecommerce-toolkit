# 財政部電子發票整合服務平台 應用 API 參考

> Source: 《電子發票應用 API 規格》v1.9（財政部財政資訊中心，中華民國 112 年 8 月）
> Spec PDF: https://www.einvoice.nat.gov.tw/static/ptl/ein_upload/attachments/1693297176294_0.pdf
> Platform: https://www.einvoice.nat.gov.tw/
> Captured: 2026-08-08 · doc_access: **public**（規格書免登入下載；AppID/APIKey 需申請）

## 為什麼這份文件在這裡

本 skill 其餘 provider（ECPay、SmilePay、Amego、ezPay、PayNow、O'Pay）都是**加值中心**——它們把發票開立包裝成自家 API，再批次上傳財政部。但有一整類需求加值中心不見得幫你做，或你想自己做：

- **手機條碼驗證**——使用者在結帳頁輸入 `/ABC.123`，你要當場判斷真偽
- **捐贈碼（愛心碼）查驗**——確認該捐贈碼確實已註冊
- **消費者端載具查詢／歸戶／捐贈**——做發票 App、記帳 App、會員中心
- **中獎號碼**——自動對獎功能

這些走的是財政部這套 API，不是加值中心的 API。加值中心的 `CheckBarcode` / `CheckLoveCode` 端點（ECPay、O'Pay 都有）本質上就是幫你轉呼叫這裡。

**重要區分：本 API 不能用來「開立發票」。** 開立走加值中心 API 或 Turnkey；本 API 是查詢/驗證/消費者端服務。

## 1. 存取方式

| 項目 | 值 |
|---|---|
| Base URL | `https://api.einvoice.nat.gov.tw` |
| HTTP Method | **POST**（v1.7 起已移除 GET） |
| Content-Type | `application/x-www-form-urlencoded` |
| 回應格式 | JSON |
| 參數編碼 | 呼叫前須先做 URL encode |

### 取得 AppID / APIKey

申請路徑：https://einvoice.nat.gov.tw/APCONSUMER/BTC605W/
需先詳讀平台〔快速上手〕→〔文件下載〕→〔營業人〕之《電子發票應用程式介面使用規範》，經財資中心審查通過後核發。

- `appID`：每次呼叫都要帶，用於驗證身分
- `APIKey`：**不進入 request 參數**，只作為 HMAC-SHA256 的祕密金鑰用於加簽。絕不可外流。

## 2. API 方法一覽

| # | API | 方法網址 | version | action | 需簽章 |
|---|---|---|---|---|---|
| 1 | 查詢中獎發票號碼清單 | `/PB2CAPIVAN/invapp/InvApp` | 0.2 | `QryWinningList` | 否 |
| 2 | 查詢發票表頭 | `/PB2CAPIVAN/invapp/InvApp` | 0.5 | `qryInvHeader` | 否 |
| 3 | 查詢發票明細 | `/PB2CAPIVAN/invapp/InvApp` | 0.6 | `qryInvDetail` | 否 |
| 4 | 捐贈碼查詢 | `/PB2CAPIVAN/loveCodeapp/qryLoveCode` | 0.2 | `qryLoveCode` | 否 |
| 5 | 載具發票表頭查詢 | `/PB2CAPIVAN/invServ/InvServ` | 0.5 →（113/1/1 起）0.6 | `carrierInvChk` | 否 |
| 6 | 載具發票明細查詢 | `/PB2CAPIVAN/invServ/InvServ` | 0.5 | `carrierInvDetail` | 否 |
| 7 | 載具發票捐贈 | `/PB2CAPIVAN/CarInv/Donate` | 0.1 | `carrierInvDnt` | **是** |
| 8 | 手機條碼歸戶載具查詢 | `/PB2CAPIVAN/Carrier/Aggregate` | 1.0 | `qryCarrierAgg` | **是** |
| 9 | 已歸戶載具個別化主題 | `/ods-main/ODS371I/query` | 1.0 | — | 否 |

**API 空白頁面**（導向財政部代管的 HTML 頁面，非 JSON API）：

| # | 功能 | 方法網址 |
|---|---|---|
| 1 | 手機條碼載具註冊 | `/PB2CAPIVAN/APIService/generalCarrierRegBlank` |
| 2 | 載具歸戶（手機條碼） | `/PB2CAPIVAN/APIService/carrierLinkBlank` |
| 3 | 手機條碼綁定金融帳戶 | `/PB2CAPIVAN/APIService/carrierBankAccBlank` |
| 4 | 載具發票捐贈 | `/PB2CAPIVAN/APIService/carrierInvDntBlank` |

> ⚠️ v1.9 註記：第 9 項「已歸戶載具個別化主題」的**原方法網址自 112 年 10 月 31 日起停用**，須改用上表網址。

## 3. 共通參數機制

### 3.1 時間戳記 `timeStamp` / `expTimeStamp`

`timeStamp` 應為「取得的 Unix timestamp **加 10 至 180 秒**」。取得 1334499000 → 送出值應落在 1334499010～1334499180。

`expTimeStamp` 為開發者預期的有效存續時間戳記。

> 這是防竄改設計。差值不要設太大。使用者裝置時間可能未對時，建議提示使用者以 NTP 校時。

### 3.2 序號 `serial`

10 位數字。第一次傳送帶 `0000000001`，之後每次 +1。

回應會帶 `hashSerial` = `Base64(HMAC-SHA256(UTF8(serial)))`，可用於比對。

### 3.3 簽章 `signature`

1. 將**所有參數**（不含 signature 本身）依參數名稱**升冪 ASCII 排序**，以 `&` 串接，UTF-8 編碼。
   以「載具發票捐贈」為例：
   ```
   action=carrierInvDnt&appID=…&cardEncrypt=…&cardNo=…&cardType=…&expTimeStamp=…&invDate=…&invNum=…&npoBan=…&serial=…&timeStamp=…&uuid=…&version=…
   ```
   注意：**參數名稱大小寫有別**；特殊符號以 **URL 編碼前**的值作為參數。
2. 以 `APIKey` 為祕密金鑰，對上述字串做 **HMAC-SHA256**。
3. 結果做 **Base64** 編碼，即為 `signature`。

> 107/7/2 起演算法已由舊制提升為 HMAC-SHA256。

### 3.4 `uuid`

行動工具 Unique ID，由開發者自行管控。平台僅記錄。若使用者有侵害行為，財資中心得停止該 UUID 或該 AppID 之存取。**責任歸屬於開發者。**

### 3.5 卡別 `cardType`

| 代碼 | 載具 |
|---|---|
| `3J0002` | 手機條碼 |
| `1K0001` | 悠遊卡 |
| `1H0001` | 一卡通 |
| `CQ0001` | 自然人憑證條碼 |

> 對照本 skill `data/carrier-types.csv`：開立發票時的載具類別（`1`/`2`/`3`）與此處的查詢卡別是**兩套不同編碼**，不要混用。

## 4. 訊息回應碼

| code | 含意 |
|---|---|
| 200 | 執行成功 |
| 500 | 系統執行錯誤 |
| 900 | 建立 JSON 物件失敗 |
| 901 | 無此期別資料 |
| 902 | 期別錯誤 |
| 903 | 參數錯誤 |
| 904 | 錯誤的查詢種類 |
| 907 | 捐贈失敗，捐贈碼不存在 |
| 908 | 捐贈失敗，此發票已被捐贈 |
| 913 | 捐贈失敗，此發票開立予營業人或機關團體，不能捐贈 |
| 915 | 查無此發票詳細資料 |
| 919 | 參數驗證碼錯誤 |
| 950 | 超過最大查詢次數 |
| 951 | 連線逾時 |
| 952 | 卡片(QR 碼)有效存續時間已過（過期憑證） |
| 953 | 卡片檢查碼有誤（偽造卡片） |
| 954 | 簽名有誤（偽造之訊息、傳遞不完整） |
| 996 | 查詢發票筆數超過上限，請縮小查詢日期區間或以載具分頁功能接續查詢下一頁 |
| 997 | UUID 不符合規定（黑名單） |
| 998 | AppID 不符合規定（被停權或從未申請） |
| 999 | 未知錯誤 |

## 5. 各 API 詳述

### 5.1 查詢中獎發票號碼清單

`POST /PB2CAPIVAN/invapp/InvApp`

| 參數 | 必填 | 格式 | 說明 | 範例 |
|---|---|---|---|---|
| `version` | ✔ | 字串 | 固定 | `0.2` |
| `action` | ✔ | 字串 | 固定 | `QryWinningList` |
| `invTerm` | ✔ | `yyyMM` | 開獎期別，**民國年**，月份必為雙數月 | `10106` |
| `UUID` | — | 字串 | 行動工具 Unique ID | |
| `appID` | ✔ | 字串 | 申請取得 | |

回傳（節錄）：`invoYm`、`superPrizeNo`（千萬特獎）、`spcPrizeNo`~`spcPrizeNo3`（特獎）、`firstPrizeNo1`~`firstPrizeNo10`（頭獎）、`sixthPrizeNo1`~`sixthPrizeNo6`（六獎）、各獎金額 `superPrizeAmt`/`spcPrizeAmt`/`firstPrizeAmt`/`secondPrizeAmt`/`thirdPrizeAmt`/`fourthPrizeAmt`/`fifthPrizeAmt`/`sixthPrizeAmt`。

> 金額為**補零字串**（`00200000` = 20 萬），不是整數，別直接拿去算。

### 5.2 查詢發票表頭

`POST /PB2CAPIVAN/invapp/InvApp`

| 參數 | 必填 | 格式 | 說明 | 範例 |
|---|---|---|---|---|
| `version` | ✔ | | | `0.5` |
| `type` | ✔ | `QRCode` / `Barcode` | **大小寫有別** | `Barcode` |
| `invNum` | ✔ | 字串 | 發票號碼 | `AB12345678` |
| `action` | ✔ | | | `qryInvHeader` |
| `generation` | ✔ | | 固定 | `V2` |
| `invDate` | ✔ | `yyyy/MM/dd` | 發票日期 | `2012/07/11` |
| `UUID` | ✔ | | | |
| `appID` | ✔ | | | |

回傳：`invNum`、`invDate`(yyyyMMdd)、`sellerName`、`invStatus`、`invPeriod`、`sellerBan`、`sellerAddress`、`invoiceTime`(HH:mm:ss)、`buyerBan`、`currency`。

### 5.3 查詢發票明細

`POST /PB2CAPIVAN/invapp/InvApp`，`version=0.6`，`action=qryInvDetail`，`generation=V2`

依 `type` 不同，必填欄位不同：

| 參數 | 條件 | 說明 |
|---|---|---|
| `invTerm` | `type=Barcode` 時必填 | `yyyMM` 民國年雙數月 |
| `encrypt` | `type=QRCode` 時必填 | 發票檢驗碼 |
| `sellerID` | `type=QRCode` 時必填 | 商家統編 |
| `randomNumber` | ✔ | 4 位隨機碼 |
| `invNum` `invDate` `UUID` `appID` | ✔ | 同表頭查詢 |

回傳除表頭欄位外，多了 `amount`（總金額）與 `details[]`：`rowNum`、`description`、`quantity`、`unitPrice`、`amount`。

> **限制：至多查詢 99 次。**

### 5.4 捐贈碼查詢

`POST /PB2CAPIVAN/loveCodeapp/qryLoveCode`

| 參數 | 必填 | 說明 | 範例 |
|---|---|---|---|
| `version` | ✔ | | `0.2` |
| `qKey` | ✔ | 要查詢的捐贈碼／統編關鍵字 | |
| `action` | ✔ | | `qryLoveCode` |
| `UUID` `appID` | ✔ | | |

回傳 `details[]`：`rowNum`、`SocialWelfareBAN`（受捐贈機關統編）、`LoveCode`（捐贈碼）、`SocialWelfareName`、`SocialWelfareAbbrev`。

> 注意回傳欄位是**大寫開頭**（`LoveCode` 而非 `loveCode`），與其他 API 的命名慣例不一致。

### 5.5 載具發票表頭查詢

`POST /PB2CAPIVAN/invServ/InvServ`

| 參數 | 必填 | 說明 | 範例 |
|---|---|---|---|
| `version` | ✔ | 0.5；**113/1/1 起 0.6** | `0.6` |
| `cardType` | ✔ | 卡別 | `3J0002` |
| `cardNo` | ✔ | 手機條碼／載具隱碼 | `/AB56P5Q` |
| `cardEncrypt` | ✔ | 手機條碼驗證碼／載具驗證碼 | |
| `expTimeStamp` | ✔ | 有效存續時間戳記 | `2147483647` |
| `timeStamp` | ✔ | 時間戳記 | `1344102065` |
| `action` | ✔ | | `carrierInvChk` |
| `startDate` | ✔ | `yyyy/MM/dd`，**起訖須同月份** | `2012/07/01` |
| `endDate` | ✔ | `yyyy/MM/dd` | `2012/07/31` |
| `onlyWinningInv` | ✔ | `Y`/`N` 僅回傳中獎 | `Y` |
| `page` | — | 分頁頁數，預設 1 | `1` |
| `uuid` `appID` | ✔ | | |

**查詢區間限制**：單月可查 9 個月、雙月可查 8 個月（以 112/7 為例：111/11～112/7）。

**分頁**：113/1/1 起新增。若 `code=996`，調整 `page` 續查下一頁。

回傳 `details[]` 每筆含 `invNum`、`cardType`、`cardNo`、`sellerName`、`invStatus`、`invDonatable`(true/false)、`amount`、`invPeriod`、`donateMark`(`0` 未捐贈 / `1` 已捐贈)、`sellerBan`、`sellerAddress`、`invoiceTime`、`buyerBan`、`currency`、`invDate{year,month,date,day,hours,minutes,seconds,time,timezoneOffset}`。

> ⚠️ 合規要求：`donateMark=1` 的發票，**字軌號碼後 3 碼須予以隱蔽，且不宜通知使用者該發票的中獎資訊**。這是規格書明列的規定，不是建議。
>
> ⚠️ `invDate` 是**物件不是字串**，與其他 API 不同，解析時要注意。

### 5.6 載具發票明細查詢

`POST /PB2CAPIVAN/invServ/InvServ`，`action=carrierInvDetail`，`version=0.5`

參數同上，另需 `invNum`、`invDate`(`yyyy/MM/dd`)、`sellerName`、`amount`。
回傳結構同 5.3（含 `details[]` 明細）。

### 5.7 載具發票捐贈 ⚠️ 需簽章

`POST /PB2CAPIVAN/CarInv/Donate`，`action=carrierInvDnt`，`version=0.1`

| 參數 | 必填 | 說明 |
|---|---|---|
| `serial` | ✔ | 10 位數字序號 |
| `cardType` `cardNo` `cardEncrypt` | ✔ | 載具三件組 |
| `expTimeStamp` `timeStamp` | ✔ | 時間戳記 |
| `invDate` | ✔ | `yyyy/MM/dd` |
| `invNum` | ✔ | 發票號碼 |
| `npoBan` | ✔ | 受捐贈機關統編**或**捐贈碼 |
| `uuid` `appID` | ✔ | |
| `signature` | ✔ | 見 3.3 |

回傳：`hashSerial`、`invNum`、`invDate`、`NPOBan`、`invStatus`、`invDntTimeStamp`。

> 只能捐贈**尚未開獎**的雲端發票。錯誤碼 907/908/913 分別對應捐贈碼不存在、已被捐贈、開立予營業人不可捐贈。

### 5.8 手機條碼歸戶載具查詢 ⚠️ 需簽章

`POST /PB2CAPIVAN/Carrier/Aggregate`，`action=qryCarrierAgg`，`version=1.0`

參數：`serial`、`cardType`、`cardNo`、`cardEncrypt`、`appID`、`timeStamp`、`uuid`、`signature`。

回傳 `carriers[]`：`carrierType`、`carrierId2`（載具隱碼）、`carrierName`。

> 這是「一個手機條碼底下歸戶了哪些載具」的查詢。拿到 `carrierId2` 後，才能用 5.5/5.6 去查那張載具的發票。

### 5.9 已歸戶載具個別化主題

`POST /ods-main/ODS371I/query`，`version=1.0`

參數：`appID`、`barcode`（手機條碼）、`verifyCode`、`invoiceDateS`、`invoiceDateE`、選填 `hsnNm`（縣市）、`townNm`（鄉鎮市區）、`busiChiNm`（商店種類）、`cardTypeNm`（載具別）、`cardCodeNm`（載具名稱）。

> **含中文的參數須對整個 URL（包括查詢字串值）做 URLEncode。**

回傳 `details[]`：`invoiceDate`、`invoiceCount`、`invoiceAmount`、`dntCount`、`dntAmount`、`prizeCount`、`prizeAmount` 等統計數字。

## 6. API 空白頁面

這四支不是 JSON API，而是導向財政部代管的 HTML 頁面，由使用者在該頁面自行完成操作。只有**傳入參數錯誤時**才回 JSON `{v, code, msg}`。

| 功能 | 需求參數 |
|---|---|
| 手機條碼載具註冊 | `uuid`, `appID` |
| 載具歸戶（手機條碼） | `uuid`, `appID`, `cardCode`, `cardNo`, `verifyCode` |
| 手機條碼綁定金融帳戶 | `uuid`, `appID` |
| 載具發票捐贈（手機條碼） | `uuid`, `appID`, `cardCode`, `cardNo`, `verifyCode`, `dntNo`, `qryYM`(`yyyymm`) |

> 注意欄位名不一致：空白頁面用 `cardCode` + `verifyCode`，JSON API 用 `cardType` + `cardEncrypt`。同一個東西，兩套名字。
>
> 「手機條碼綁定金融帳戶」自 111/8/15 起改為導向平台由使用者自行登入後設定，**已刪除手機條碼與驗證碼參數**。

### 手機條碼驗證碼規則（註冊頁面）

- 長度 8～16 碼
- 自「英文大寫、英文小寫、數字、特殊符號」4 類中至少取 3 類組成
- 特殊符號僅允許 `` !#$%&*,-.:;@[]^_`{|}~ ``

## 7. 與加值中心的分工

| 需求 | 走哪裡 |
|---|---|
| 開立／作廢／折讓發票 | 加值中心 API（ECPay、O'Pay、ezPay、Amego、SmilePay、PayNow…）或自建 Turnkey |
| 上傳財政部 | 加值中心代勞（多為每日批次），或 Turnkey |
| 結帳頁驗證手機條碼真偽 | 本 API 5.5（載具查詢會因無效載具而失敗）／或加值中心的 `CheckBarcode` 端點 |
| 驗證捐贈碼 | 本 API 5.4 ／或加值中心的 `CheckLoveCode` |
| 消費者端發票 App、記帳、自動對獎 | **只有本 API** |
| 中獎號碼清單 | 本 API 5.1 |

實務建議：**單純電商開發票不需要申請 AppID**，用加值中心的 `CheckBarcode`/`CheckLoveCode` 即可（它們是同一個上游）。要做消費者端功能才需要走這裡。

## 8. 相關文件

- 加值中心生態與選型：[VAC_LANDSCAPE.md](VAC_LANDSCAPE.md)
- 電子發票證明聯一維／二維條碼規格：平台〔快速上手〕→〔文件下載〕→〔營業人〕常用功能
- 開放資料 Open API（非本規格）：https://www.einvoice.nat.gov.tw/portal/ods/ODS318E
