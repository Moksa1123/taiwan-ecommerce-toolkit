# 物流業者直連可行性說明——哪些「沒有公開 API」

> Directory edition: reference files and JSON data only, no scripts. Tools under `scripts/`, `examples/` and `tests/` ship in the full edition (npm package `taiwan-logistics-skill`).
> Keys and merchant IDs are set up by the user and passed into the code as parameters; they appear as placeholders such as `<HASH_KEY>`. Published sandbox keys are also shown as placeholders; get them from the provider's official docs. Credential-type field names are shown as `<帳密欄位>`.

> 這份文件的目的是**防止誤判**。`data/providers.csv` 裡列了 7-11、全家、萊爾富、OK、黑貓、宅配通、中華郵政等業者，那代表「**這個通路收得到貨**」，不代表「**你可以直接串它的 API**」。
> 兩者差很多，本文件逐一釐清。

## 0. 一句話結論

| 業者 | 有對外公開 API 嗎 | 你該怎麼做 |
|---|---|---|
| 新竹物流 HCT | 有直連 API，需申請 | 已收錄 [hct-logistics-api.md](hct-logistics-api.md) |
| 黑貓宅急便 t-cat | 無公開規格 | 走聚合商，或簽約後取得 |
| 嘉里大榮 KTJ | 無公開規格 | 走聚合商 |
| 宅配通 Pelican | 無公開規格 | 走聚合商 |
| 中華郵政 | 無：**物流面完全沒有 Open API** | 走聚合商（ECPay 有郵政宅配） |
| 7-ELEVEN 交貨便／賣貨便 | 無：賣家自助平台，無對外 API | 走聚合商 |
| 全家 好賣+ | 無：同上 | 走聚合商 |
| 萊爾富 / OK | 無獨立對外 API | 走聚合商（綠界 OK 店到店已於 2026-07-01 終止） |
| 蝦皮店到店 | 無對外 API | 無替代路徑 |

**「走聚合商」= 用本 skill 已收錄的 ECPay / ezShip / SmilePay / NewebPay / PAYUNi / PChomePay / PayNow。**

## 1. 黑貓宅急便 t-cat

**現況**：官方沒有公開的 API 技術規格。

**官方提供的是**：
- **ezcat 印單軟體**——給與統一速達、統一客樂得簽約的契約客戶使用的託運單列印軟體，提供貨物查詢、託運單號自動配號、收/寄件人資料維護與批次匯入、檢貨單，離線可用。這是**桌面軟體，不是 API**。
  https://www.t-cat.com.tw/contract/ezcat.aspx
- **icat 網路宅急便**——個人會員的網頁／App 預約寄件（單筆、多筆），不是對外 API。官網沒有公開的 API 申請管道或規格，契約客戶要直連需自行洽黑貓業務。

**實務路徑**：
1. 多數開店平台（SHOPLINE、CYBERBIZ、91APP）已內建黑貓串接，可批次匯入訂單、列印託運單
2. 自建系統：走 ECPay（`LogisticsSubType=TCAT`）、SmilePay（`Pay_zg=81/82/83`，含 COD/PICKUP/逆物流）、PayNow 等聚合商
3. 量體夠大再談直連

> 本 skill `smilepay-logistics-api.md` 的黑貓矩陣（`Pay_zg=81` COD、`82` PICKUP、`83` 逆物流）是目前收錄中最完整的黑貓串接路徑。

## 2. 嘉里大榮 KTJ

**現況**：官網 https://www.kerrytj.com/zh/checking 僅提供**貨態查詢網頁**（先選常溫或低溫，一次最多 5 筆託運單號，只查一個月內），未見公開 API 規格。

**替代**：第三方追蹤聚合服務（17TRACK 等）可查貨態，但那是爬取/合作資料，不是官方 API，不建議用於正式出貨流程。

**實務路徑**：走聚合商，或簽約後洽業務取得規格。

## 3. 宅配通 Pelican

**現況**：無公開 API 規格。已列於 `providers.csv` 是因為它是**可用的配送通路**（部分聚合商支援），不是因為可直連。

**已知**：紅陽科技（SunPay）舊文件站 doc.esafe.com.tw 列有「宅配通」，但官網物流頁（sunpay.com.tw/logistics，2026-09-24 查核）已未列，也沒有對應的 API 規格；可用的聚合路徑需向業者確認。紅陽沒有獨立的物流 API；超商物流（7-11／全家／萊爾富，不含宅配通）是併在金流 API 用 `lgs_flag`／`store_type` 開啟（金流手冊 V1.1.2 p.23–24、p.49，詳見 taiwan-payment 的 sunpay-payment-api.md）。

## 4. 中華郵政（常見誤解）

**這是本次盤點最重要的一項更正。**

中華郵政確實有 Open API 合作計畫，但**開放的全部是金融類服務**：

| 階段 | 開放項目 |
|---|---|
| 第一階段（公開資料查詢） | 存款分類產品列表、臺幣活期/定期存款產品資訊、中華郵政 ATM 資訊、外幣幣別列表與外匯匯率 |
| 第二階段（消費者資訊查詢） | 臺幣活存/定存帳戶餘額查詢、活存帳戶交易明細查詢 |

**沒有**：包裹查詢、郵資試算、i 郵箱、託運單建立、貨態回傳。

且需透過第三方服務提供者（TSP 業者）申請使用，現行合作 TSP 為睿元國際（麻布記帳）、臺灣集中保管結算所。

公告：https://www.post.gov.tw/post/internet/Message/index.jsp?ID=1584329354372

官網「招標資訊 > API 規格書」（https://www.post.gov.tw/post/internet/Message/index.jsp?ID=15021202）是郵儲窗口周邊設備的硬體介面規格，供採購測試用，與包裹或物流無關。

**流傳的「中華郵政包裹查詢 API」**（GitHub gist 等）是**非官方逆向**，無 SLA、隨時可能失效，不應用於正式系統。

**實務路徑**：郵政宅配走 ECPay 物流（其宅配服務含中華郵政）。

## 5. 7-ELEVEN 交貨便 / 賣貨便、全家 好賣+

**性質**：這是**賣家自助平台**，不是可串接的物流服務。

- 7-ELEVEN 交貨便 https://myship.7-11.com.tw/ ／賣貨便：結合統一超商既有交貨便，建構下單→出貨→付款→取貨一條龍。免手續費、**無須自行開發系統**——因為它本來就不打算讓你開發。
- 全家 好賣+：同性質。

**含意**：它們的目標客群是微型賣家（社群電商、個人賣家），商業模式是「你來我的後台操作」，不是「你來串我的 API」。

**實務路徑**：程式串接 7-11／全家店到店，一律走聚合商：
- ECPay：B2C `UNIMART` / `UNIMARTFREEZE` / `FAMI` / `HILIFE`；C2C `UNIMARTC2C` / `FAMIC2C` / `HILIFEC2C`（`OKMARTC2C` 已於 2026-07-01 終止，https://developers.ecpay.com.tw/36099/）
- ezShip：OK／萊爾富／全家三通路（首家串接三通路者）
- SmilePay：`Pay_zg` 矩陣 51/52/55/56
- PayNow：`Logistic_service` 01–05、10、21–24 涵蓋四大超商（含冷凍）
- PChomePay：金物流二合一

## 6. 蝦皮店到店

**現況**：無對外商家 API。蝦皮店到店是蝦皮生態內的服務，非蝦皮賣家無法使用。

**無替代路徑**——這是唯一一個「連聚合商也接不到」的通路。

## 7. 萊爾富 / OK 便利商店

兩家皆無獨立對外 API。`providers.csv` 中的 `hilife`、`okmart` 條目代表**取貨通路可用性**，串接一律經聚合商。

綠界的 OK 店到店（`OKMARTC2C`）已於 2026-07-01 終止（https://developers.ecpay.com.tw/36099/）；要收 OK 取貨，先向其他聚合商確認仍有提供。萊爾富官網（hilife.com.tw）會擋自動化存取，無法定期查核。

## 8. 有直連 API 的：新竹物流 HCT

目前本 skill 唯一收錄的直連 carrier。

- 端點：`https://hctapiweb.hct.com.tw`
- 支援 XML / JSON / DataSet 三種變體
- 加密金鑰申請後由 HCT 提供（官方僅給 C# sample code）
- 需注意 `TransReport`（列印託運總表）**必須在 18:00 前呼叫**

詳見 [hct-logistics-api.md](hct-logistics-api.md)。

## 9. 為什麼 `providers.csv` 要改欄位

原本 `taiwan-logistics/data/providers.csv` 用 `api_available` 布林值，把上述所有業者都標成 `true`——這在語意上是錯的，會讓 AI 助理回答「黑貓有 API，你可以直接串」。

已改為：

| 欄位 | 值域 | 意義 |
|---|---|---|
| `api_available` | true/false | **是否可透過本 skill 直接串接**（即有 reference + 可取得規格） |
| `doc_access` | `public` / `apply` / `contract` / `none` | 文件公開程度 |
| `doc_url` | URL | 文件入口 |
| `doc_verified` | YYYY-MM-DD | 最後查證日期 |

`doc_access=contract`（黑貓、嘉里、宅配通：規格不公開，須簽約洽業務）與 `doc_access=none`（中華郵政物流、超商賣家平台）者一律 `api_available=false`，並在 `features` 欄註明替代路徑。

## 10. 來源

- 黑貓 ezcat — https://www.t-cat.com.tw/contract/ezcat.aspx
- 嘉里大榮貨態查詢 — https://www.kerrytj.com/zh/checking
- 中華郵政 Open API 合作公告 — https://www.post.gov.tw/post/internet/Message/index.jsp?ID=1584329354372
- 中華郵政 API 規格書（郵儲窗口周邊設備，非物流）— https://www.post.gov.tw/post/internet/Message/index.jsp?ID=15021202
- 綠界物流更新歷程（OK 店到店終止）— https://developers.ecpay.com.tw/36099/
- 7-ELEVEN 交貨便 — https://myship.7-11.com.tw/MyShip/Index
- ECPay 物流 API — https://developers.ecpay.com.tw/7380/ ／全方位物流 — https://developers.ecpay.com.tw/10075/
