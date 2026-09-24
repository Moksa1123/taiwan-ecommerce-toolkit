# ezShip 台灣便利配 物流 API 參考

> 官網: https://www.ezship.com.tw/
> 購物網站串接: https://www.ezship.com.tw/service_doc/service_home_w18v1.jsp?vDocNo=1702
> 文件公開程度：public（文件站免登入；串接需後台申請開通）

## 0. 定位

ezShip 是本 skill 收錄的**唯一非金流商的超商取貨聚合商**。其他六家（ECPay、NewebPay、PAYUNi、SmilePay、PChomePay、PayNow）都是先做金流再擴到物流；ezShip 從 2005 年起就專做店到店。

**歷史地位**：首家與 OK、萊爾富、全家三大通路合作之店到店服務平台。

**為什麼值得收錄**：
1. 對**只要物流不要金流**的商家，不必為了超取去開一個金流帳號
2. 各大開店平台皆有現成模組（WooCommerce、OpenCart、EasyStore、CYBERBIZ、meepShop）
3. C2C 超取的老牌選項，費率結構與金流商不同

## 1. 服務項目

| 服務 | 說明 |
|---|---|
| 超商取貨 | 店到店，買家至指定門市取件 |
| 超商取貨付款 | 貨到付款（COD） |
| B2C 寄件（大宗寄倉）| 包裹依超商分箱送至各超商物流中心再轉運門市，只收店配，見 §2.3 |
| 店到宅 | 門市寄件、宅配到府 |
| 店退店 | 逆物流 |
| 臉書店 | 社群電商賣場 |
| 簡訊團購 | 團購收單 |

**合作通路**：OK、萊爾富、全家三大超商。

> ⚠️ 注意：ezShip **不含 7-ELEVEN**。7-11 超取需另走 ECPay／SmilePay／PayNow 等。若你的客群以 7-11 為主，ezShip 不能單獨滿足需求。這是選型時最關鍵的一點。

## 2. 三種串接方式的差異

三者都是表單導轉，差別在批次能力與商品資料：

| | 參數版 | XML 版 | 簡易版 |
|---|---|---|---|
| 費用 | 免費 | 免費 | 免費 |
| 包裹類別 | 店配（付款/不付款）+ 宅配（貨到付款/純配送）| 同參數版 | **僅店配，無宅配** |
| 串接類型 | 單次單筆 | **單次單筆或批次多筆** | 單次單筆 |
| 電子地圖與取件人資訊 | 獨立串接傳遞 | 獨立串接傳遞 | **同時完成** |
| 串接商品資料 | 無 | **有** | 無 |
| 列印商品明細寄件單 | 無 | **可** | 無 |
| 異常處理 | 提供錯誤狀態碼 | 提供錯誤狀態碼 | **無** |
| 配送狀態 | API 查詢 | API 查詢 | API 查詢 |

> ⚠️ **簡易版官方已凍結**：原文「請使用(參數版)或(XML版)，(簡易版)僅提供系統正常運作，不再開發新功能」。新專案不應採用。
> ⚠️ **代收服務（取貨付款／貨到付款）需 ezShip 商務會員資格**，且須在合約期間內。一般會員只能做「取貨不付款／純配送」。

## 2.1 參數版 — 完整流程與欄位

三個端點依序：**電子地圖 → 傳送訂單 → 貨況查詢**。

### ⚠️ 兩個跨端點的不一致，實作前先知道

1. **參數命名風格不同**：電子地圖用 **camelCase**（`suID`、`rtURL`、`webPara`），傳送訂單與貨況查詢用 **snake_case**（`su_id`、`rtn_url`、`web_para`）。同一次串接要兩種寫法。
2. **編碼方向不對稱**：以 URL 方式送出時中文需 **BIG5** 編碼；但 ezShip **回傳一律 UTF-8**。送 BIG5、收 UTF-8。

### 步驟一：電子地圖（只有超商取貨需要）

`https://map.ezship.com.tw/ezship_map_web.jsp`

| 送出 | 說明 |
|---|---|
| `suID` | 賣家 ezShip 帳號，需開通網站串接 |
| `processID` | 處理序號或訂單編號，自行提供 |
| `stCate` | 取件門市通路代號 |
| `stCode` | 取件門市代號 |
| `rtURL` | 回傳網址（完整路徑）|
| `webPara` | 自訂識別資料，原值回傳 |

| 回傳 | 說明 |
|---|---|
| `processID` | 原值回傳 |
| `stCate` | **`TOK` OK／`TLF` 萊爾富／`TFM` 全家／`TSF` 店港澳** |
| `stCode` / `stName` / `stAddr` / `stTel` | 門市代號／名稱／地址／電話 |
| `webPara` | 原值回傳 |

> ⚠️ **官方明文禁止把電子地圖嵌入 iframe 或以 CSS 內嵌**。
> ⚠️ **門市代碼可能四碼或五碼**（如 `TFM9771`），且**與門市服務代號不一定相同**。直接回傳 ezShip 給的值即可，不要自行轉換。
> 官方另建議網站啟用 HTTPS——行動裝置對混合內容的限制越來越嚴。

### 步驟二：傳送訂單

`https://www.ezship.com.tw/emap/ezship_request_order_api_ex.jsp`

> 舊端點 `ezship_request_order_api.jsp`（無 `_ex`）**已於 2017 年底停用**。

| 參數 | 說明 |
|---|---|
| `su_id` | 賣家帳號。**用代收服務須為商務會員且在合約期間內** |
| `order_id` | 購物網站自訂訂單編號 |
| `order_status` | 訂單狀態，見下 |
| `order_type` | **`1` 取貨付款（代收）／`3` 取貨不付款** |
| `order_amount` | 代收金額或報值金額 |
| `rv_name` | 取件人姓名 |
| `rv_email` / `rv_mobile` | 取件人信箱／行動電話 |
| `st_code` | 取件門市。**`A01`–`A04`、`A11`、`A12` 必填** |
| `rv_addr` / `rv_zip` | 收件地址與郵遞區號。**`A05`、`A06` 必填**（宅配）|
| `rtn_url` | 回傳網址 |
| `web_para` | 自訂識別資料 |

**`order_status` 分組**：

| 代碼 | 說明（依 `ezship_WebOrder_HttpRequest_v15.pdf`）|
|---|---|
| `A01` | 超商取貨，不需在 ezShip 確認，可直接印單（回 `sn_id`）|
| `A02` | 超商取貨，需在 ezShip 確認後才能印單（預設值，回 `sn_id`）|
| `A03` | 超商取貨，輕鬆袋／迷你袋，不需確認，但須到後台登錄專用編號（**不回** `sn_id`）|
| `A04` | 超商取貨，輕鬆袋／迷你袋，需確認且須登錄專用編號（**不回** `sn_id`）|
| `A05` | 宅配，不需確認，可直接印單 |
| `A06` | 宅配，需確認後才能印單 |
| `A11` | 店港澳（無代收），不需確認 |
| `A12` | 店港澳（無代收），需確認 |

取件通路由電子地圖回傳的 `stCate` 決定：`TFM` 全家、`TLF` 萊爾富、`TOK` OK、`TSF` 店港澳。

**`order_amount` 範圍**：`order_type=1` 代收時，店配 10–10,000、宅配 10–8,000；`order_type=3` 為報值金額（含運費），商務會員 0–4,000、一般會員 0–2,000。

**建單失敗代碼**（回傳於 `order_status`）：`E00` 參數短缺、`E01` 帳號不存在、`E02` 無代收／串接／宅配／店港澳權限、`E03` 無可用輕鬆袋或迷你袋、`E04` 門市有誤、`E05` 金額有誤、`E06` email 格式、`E07` 手機格式、`E08` `order_status` 有誤、`E09` `order_type` 有誤、`E10` `rv_name` 有誤、`E11` `rv_addr` 有誤、`E13` 店港澳無法使用；成功為 `S01`。

> ⚠️ **`rv_name` 超過四個中英文字，超商取貨單會印不完整**，可能導致取貨問題。官方特別提醒。
> 💡 **港澳配送**（`A11`/`A12`）：ezShip 是本 skill 少數支援港澳店配的聚合商；店港澳只能 `order_type=3`，報值金額商務會員 0–2,500（XML 版欄位定義）。

回傳：`order_id`、`sn_id`、`order_status`、`webPara`。

> ⚠️ **`sn_id` 回傳八個零（`00000000`）代表訂單建立失敗**，原因看回傳的 `order_status`（`E00`–`E13`，見上）。成功時 `order_status=S01`，**必須把 `sn_id` 存起來**，後續寄件與追蹤貨況都靠它。`A03`（輕鬆袋／迷你袋）成功時 `sn_id` 為空值，不是失敗。

亦可用 CURL 直接 POST（官方提供 Linux／Windows 兩種引號寫法範例）。

### 步驟三：貨況查詢

兩種查法，端點不同：

| 依據 | 端點 |
|---|---|
| ezShip 店到店編號 | `.../emap/ezship_request_order_status_api.jsp` |
| 購物網站訂單編號 | `.../emap/ezship_request_order_status_api_byorder.jsp` |

送出：`su_id`、`sn_id`（依店到店編號）或 `order_no`（依訂單編號，≤25）、`rtn_url`、`web_para`。

回傳：`sn_id`、`order_no`（僅依訂單編號查詢）、`order_status`、`webPara`，另有三個時序欄位：

| 參數 | 說明 |
|---|---|
| `times` | **`1` 第一次配送／`2` 第二次配送／`8` 退還寄件人／`9` 非常規配送** |
| `sdate` | 配送狀態發生日期（`yyyy/mm/dd`），由超商或宅配公司提供 |
| `udate` | ezShip 接收到該狀態的時間（`yyyy/mm/dd hh24:mi`）|

**貨況 `order_status`**（`ezship_status_api.pdf`、`ezship_status_api_byorder.pdf`）：

| 代碼 | 說明 |
|---|---|
| `S01` | 尚未寄件或尚未收到超商總公司提供的寄件訊息 |
| `S02` | 運往取件門市途中 |
| `S03` | 已送達取件門市 |
| `S04` | 已完成取貨 |
| `S05` | 退貨（已退回物流中心／再寄一次給取件人／退回給寄件人）|
| `S06` | 配送異常（刪單／門市閉店／貨故）|
| `E00` | 參數傳遞內容有誤或欄位短缺 |
| `E01` | `su_id` 帳號不存在 |
| `E02` | `su_id` 帳號無網站串接權限 |
| `E03` | `sn_id` 店到店編號有誤 |
| `E04` | `su_id` 與 `sn_id` 無法對應 |
| `E99` | 系統錯誤 |

> ⚠️ `S01` 在建單回傳代表「訂單新增成功」，在貨況查詢代表「尚未寄件」；`E00`–`E04` 兩邊意義也不同，解析時要分開處理。

> ⚠️ **有速率限制且會被停權**：官方明文「若因大量反覆查詢結案資料，導致 ezShip 系統忙碌或運行困難，ezShip 將中斷其網路串接之權利」，**建議每筆查詢間隔 3 秒以上**，已結案貨件勿重複查詢。不要做整批預先輪詢。
> ⚠️ **`order_status` 回傳 `S05`（包裹退貨）或 `S06`（包裹配送異常）時無法呈現最終貨況**，需登入 ezShip 系統查詢。
> ⚠️ 訂單號碼重複時，**以最後一次上傳的訂單資料為準**。
> ⚠️ 以訂單編號查詢**不適用簡易版**串接的訂單。

## 2.2 XML 版 — 傳送訂單

電子地圖與貨況查詢同參數版；傳送訂單改以 HTTP POST 將 XML 放在 **`web_map_xml`** 參數送到
`https://www.ezship.com.tw/emap/ezship_xml_order_api_ex.jsp`（`ezship_xml_order_api.jsp` 已於 2017 年底停用）。
欄位依 `ezship_WebOrder_XML_v15s.pdf`（版本 1.5），標籤為 camelCase。

**訂單 `<ORDER>`**

| 標籤 | 必要 | 型態／長度 | 說明 |
|---|:---:|---|---|
| `suID` | Y | varchar 100 | 賣家 ezShip 帳號；取貨付款訂單帳號須在合約期間內 |
| `orderID` | Y | varchar 10 | 購物網站訂單編號 |
| `orderStatus` | Y | varchar 3 | `A01`–`A06`、`A11`、`A12`，同參數版 |
| `orderType` | Y | varchar 1 | `1` 取貨付款／`3` 取貨不付款 |
| `orderAmount` | Y | number 5 | 範圍同參數版；店港澳只能 `orderType=3`，報值金額商務會員 0–2,500 |
| `rvName` | Y | varchar 60 | 取件人姓名；`orderType=3` 須為證件上真實姓名 |
| `rvEmail` | Y | varchar 100 | 店到店包裹送達時寄取件通知 |
| `rvMobile` | Y | varchar 10 | 店到店發台灣手機簡訊；店到宅供配送聯絡；店港澳發港澳手機簡訊 |
| `stCode` | 條件 | varchar 9 | **通路別 + 門市代號**（電子地圖回傳的 `stCate` + `stCode`，如 `TFM0038`）；`A01`–`A04`、`A11`、`A12` 必填 |
| `rvAddr` | 條件 | varchar 120 | `A05`、`A06` 必填 |
| `rvZip` | 條件 | varchar 10 | `A05`、`A06` 必填 |
| `rtURL` | Y | varchar 100 | 回傳網址 |
| `webPara` | N | varchar 100 | 原值回傳；勿含 `' : @ % & * $ "` |

**商品明細 `<Detail>`**（可重複，非必要；有傳才可在便利配列印寄件單與撿貨報表）

| 標籤 | 型態／長度 | 說明 |
|---|---|---|
| `prodItem` | number 3 | 商品序號，**必須從 1 開始依序遞增** |
| `prodNo` | varchar 30 | 商品編號 |
| `prodName` | varchar 120 | 商品名稱 |
| `prodPrice` | number 5 | 價格 |
| `prodQty` | number 5 | 數量 |
| `prodSpec` | varchar 120 | 規格 |

有傳 `<Detail>` 時 `prodItem`、`prodName` 必須有值。含特殊符號的欄位以 `<![CDATA[...]]>` 包起來。

```xml
<ORDER>
   <suID>service@ezship.com.tw</suID>
   <orderID>20140318154002</orderID>
   <orderStatus>A01</orderStatus>
   <orderType>1</orderType>
   <orderAmount>1680</orderAmount>
   <rvName><![CDATA[謝無忌]]></rvName>
   <rvEmail>123@ezship.com.tw</rvEmail>
   <rvMobile>0987654321</rvMobile>
   <stCode>TFM0038</stCode>
   <rtURL>http://yourdomain.domain/direct/program.php</rtURL>
   <webPara>20140318154002-xxx</webPara>
   <Detail>
      <prodItem>1</prodItem>
      <prodNo>A2769-1</prodNo>
      <prodName><![CDATA[格子口袋襯衫]]></prodName>
      <prodPrice>860</prodPrice>
      <prodQty>1</prodQty>
      <prodSpec><![CDATA[白]]></prodSpec>
   </Detail>
</ORDER>
```

回傳（snake_case）：`order_id`、`sn_id`、`order_status`、`webPara`；代碼同參數版，另有 `E98` XML 無法載入、`E99` 系統錯誤。

## 2.3 B2C 寄件（大宗寄倉）與寄件單下載 API

來源：服務說明 `service_home_w18v1.jsp?vDocNo=2501`（內容頁 `service_doc/2501NN_doc.jsp`，`NN`＝01–23）。

**服務**：賣家把包裹依取件超商分箱，自行以貨運／宅配／郵局送到該超商物流中心，由物流中心轉運至門市（p.01–02）。只收「店配–取貨付款」與「店配–取貨不付款」（p.02）。

| 超商 | 物流中心 | 收貨時間（當日轉運）| 材積 |
|---|---|---|---|
| 全家 | 日翊物流大溪倉，桃園市大溪區仁善里15鄰新光東路76巷22-2號 | 08:30–14:00；14:01–16:30 隔日；需先在全家「廠商進貨預約平台」預約（7 家指定貨運商免預約）| 長+寬+高 < 105 cm、最長邊 < 45 cm、< 5 kg |
| 萊爾富 | 新北市樹林區味王街1-25號（38號碼頭）| 08:00–14:00；14:01–15:00 隔日 | 同上 |
| OK | 來來物流，桃園市大溪區仁善里9鄰新光東路63巷88號（42-43碼頭）| 08:00–14:00；14:01–17:00 隔日 | 長+寬+高 < 105 cm、最長邊 45 cm、其餘兩邊 ≤ 30 cm、< 5 kg |

（p.05–07）當日轉運者次日中午前送達門市。取貨付款每筆代收上限 10,000 元（p.08）。

**啟用**（p.03、p.19）：限 ezShip 商務會員且合約有效。後台「我的便利配 → 設定 → 配送服務 → B2C寄件設定」：

- **自動要號**：開啟後，以網站串接（§2.1／§2.2 的建單 API）建立的寄件資料**一律視為 B2C 寄件**並自動取號。若部分訂單仍要門市寄件（店到店），不可開啟
- **來源 IP**：登錄呼叫寄件單 API 的對外 IP

也就是**建單沒有另一組 API**，B2C 與店到店的差別由帳號設定決定。

### 單筆寄件單下載（p.20）

`https://www.ezship.com.tw/emap/ezship_request_order_label_api.jsp`，Form submit 或 URL 參數。

| 參數 | 說明 |
|---|---|
| `suID` | ezShip 帳號（需開通網站串接）|
| `sn_id` | 店到店編號 |

成功直接輸出寄件單 PDF。錯誤以文字輸出：

| 訊息 | 原因 |
|---|---|
| `Error: The requested header does not contain a valid source IP address.` | 來源 IP 未設定 |
| `Error: The requested file with sn_id : … was not found.` | `sn_id` 不存在 |
| `Error: The requested file was not found.` | `suID` 錯誤或未開自動要號 |

### 多筆寄件單下載（p.21）

兩步驟，皆 `POST` JSON（UTF-8），需先設定來源 IP。

**步驟一** `https://www.ezship.com.tw/myezship_label/myezship_order_print_api.jsp` — 建立批次表單

| 欄位 | 說明 |
|---|---|
| `ezship_id` | ezShip 帳號 |
| `label_for` | 固定 `4` |
| `label_printer` | `A` A4 四格；`B` 標籤機 10×15 |
| `label_printtype` | `A` 只印寄件單；`B` 寄件單＋明細 |
| `label_merge` | `A` 三家超商合併；`B` 各超商分開檔案 |
| `sn_list[].sn_id` | 店到店編號 |

回應：`errorCode`、`ezship_id`、`file_id`（步驟二使用）、`success_count`、`fail_count`、`fail_list[].sn_id`、`total`、`request_id`。

**步驟二** `https://www.ezship.com.tw/myezship_label/myezship_order_label_api.jsp` — 取得 PDF 網址

請求 `ezship_id`、`file_id`；回應 `errorCode`、`file_list[].file_url`、`file_count`、`request_id`。每 100 筆切一個檔案，製作約 1 分鐘／百筆。

| `errorCode` | 意義 |
|---|---|
| `000` | 成功 |
| `001` | 新增失敗 |
| `002` | JSON 格式有誤 |
| `003` | 會員權限異常 |
| `004` | 製作中（步驟二）|
| `005` | 製作失敗（步驟二）|
| `006` | 尚未製作（步驟二）|
| `007` | 非允許 IP |
| `008` | 禁止一分鐘內多次傳送（步驟一）|
| `999` | 傳送失敗 |

> ⚠️ 步驟一一分鐘內不可重送（`008`）；步驟二回 `004` 時稍後再查，不要重跑步驟一。

**逾期未領**（p.10）：貨到門市 7 天未取即退回超商物流中心，依「B2C寄件設定」的退貨週期整箱待領，**由寄件人自行委託物流業者取回**，超過 30 日未處理將捐贈或回收。沒有退貨 API。

## 3. 申請流程

1. 進入 ezShip 後台
2. 「我的便利配」→「購物網站串接」→「網站串接申請」
3. 提供購物網站網址送出申請
4. ezShip 於 **1–2 個工作日**內完成審核

客服：(02) 2700-3727，週一至週五 09:00–12:00 / 13:00–18:00

## 4. 技術文件

| 文件 | 網址 |
|---|---|
| 欄位定義（參數版）| `http://www.ezship.com.tw/file/ezship_WebOrder_HttpRequest_v15.pdf` |
| 欄位定義（XML 版）| `http://www.ezship.com.tw/file/ezship_WebOrder_XML_v15s.pdf` |
| 貨況（依店到店編號）| `http://www.ezship.com.tw/file/ezship_status_api.pdf` |
| 貨況（依訂單編號）| `http://www.ezship.com.tw/file/ezship_status_api_byorder.pdf` |
| 文件站首頁 | `https://www.ezship.com.tw/service_doc/service_home_w18v1.jsp?vDocNo=1702` |

文件站內容由 `service_doc/1702NN_doc.jsp` 載入（`04`–`09` 參數版、`10`–`16` XML 版、`17`–`18` 簡易版、`19`–`22` 貨況串接）。

官方另提供 PHP／JSP 的 BIG5 與 UTF-8 兩種版本程式碼範例。

`webPara` 官方定義為「網站所需額外判別資料，ezShip 將原值回傳」，是原值透傳的識別欄位（類似其他 provider 的 `ExtraData`），沒有驗證或簽章語意。ezShip **沒有簽章機制**，安全性倚賴 `su_id` 帳號綁定與 HTTPS。

開源實作可參考：https://github.com/recca0120/payum-ezship（PHP，`src/Api.php`）

> 已知的踩雷點：OpenCart 等平台串 ezShip 時會遇到 **SameSite cookie** 問題（導轉回站時 session 遺失）。若採導轉式串接，須設定 `SameSite=None; Secure`。

## 5. 現成模組

| 平台 | 支援 |
|---|---|
| WooCommerce | 社群模組（超商取貨） |
| OpenCart | 社群模組（注意 SameSite） |
| EasyStore | 官方 App |
| CYBERBIZ | 內建（超商取貨 C2C） |
| meepShop | 內建 |

**建議**：若你的專案是上述平台之一，直接用現成模組；自建系統才需要自己串。

## 6. 與其他 provider 的取捨

| 需求 | 建議 |
|---|---|
| 要 7-11 | ECPay / SmilePay / PayNow / PChomePay |
| 只要 OK+萊爾富+全家，且不想開金流帳號 | **ezShip** |
| 金物流一次搞定 | PChomePay（二合一）/ ECPay |
| 要黑貓宅配含逆物流 | SmilePay（`Pay_zg=81/82/83`） |
| 要即時配送 | Lalamove（見 [lalamove-logistics-api.md](lalamove-logistics-api.md)） |

## 7. 待補

| 項目 | 狀態 |
|---|---|
| 店退店（逆物流） | 串接文件與 B2C 寄件說明都未提供 API；B2C 逾期件由寄件人自行至物流中心取回。是否有 API 需洽 ezShip |
| XML 版批次多筆 | 比較表標示 XML 版可「批次多筆」，但欄位定義與範例只有單一 `<ORDER>`，批次格式未載明 |

## 8. 來源

- ezShip 關於便利配 — https://www.ezship.com.tw/staticpage/about.jsp
- 購物網站串接 — https://www.ezship.com.tw/service_doc/service_home_w18v1.jsp?vDocNo=1702
- EasyStore 串接說明 — https://support.easystore.co/zh-tw/article/ezship-1mchswf/
- CYBERBIZ 超商物流教學 — https://www.cyberbiz.io/helpcenter/?p=2524
- 程式碼說明：連結電子地圖 — `…/2017_service_doc_home.jsp?vDocNo=1702&vDefPage=07`
- 程式碼說明：傳送訂單 — `…&vDefPage=08`
- 貨況串接（依訂單編號查詢）— `…&vDefPage=22`
- B2C 寄件服務說明 — https://www.ezship.com.tw/service_doc/service_home_w18v1.jsp?vDocNo=2501&vDefPage=19（內容頁 `service_doc/250101_doc.jsp`–`250123_doc.jsp`，2026-09-24 查核）
- 欄位定義 PDF — `ezship_WebOrder_HttpRequest_v15.pdf`、`ezship_WebOrder_XML_v15s.pdf`、`ezship_status_api.pdf`、`ezship_status_api_byorder.pdf`（見 §4）
- 欄位定義 PDF（參數版）— http://www.ezship.com.tw/file/ezship_WebOrder_HttpRequest_v15.pdf
- 欄位定義 PDF（XML 版）— http://www.ezship.com.tw/file/ezship_WebOrder_XML_v15s.pdf
- 開源 PHP 實作 — https://github.com/recca0120/payum-ezship
