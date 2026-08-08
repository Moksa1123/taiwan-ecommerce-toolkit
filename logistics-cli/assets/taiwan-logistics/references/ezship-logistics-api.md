# ezShip 台灣便利配 物流 API 參考

> 官網: https://www.ezship.com.tw/
> 購物網站串接: https://www.ezship.com.tw/service_doc/service_home_w18v1.jsp?vDocNo=1702
> Captured: 2026-08-08 · doc_access: **public**（文件站免登入；串接需後台申請開通）
> Status: **參數版三支端點欄位已完整** — 電子地圖、傳送訂單、貨況查詢；XML 版與欄位定義 PDF 待補

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
| 大宗直寄 | 大量出貨直送門市 |
| 店到宅 | 門市寄件、宅配到府 |
| 店退店 | 逆物流 |
| 臉書店 | 社群電商賣場 |
| 簡訊團購 | 團購收單 |

**合作通路**：OK、萊爾富、全家三大超商。

> ⚠️ 注意：ezShip **不含 7-ELEVEN**。7-11 超取需另走 ECPay／SmilePay／PayNow 等。若你的客群以 7-11 為主，ezShip 不能單獨滿足需求。這是選型時最關鍵的一點。

## 2. 三種串接方式的差異

先前推測為「導轉／表單／API」三種，**實際不是**——三者都是表單導轉，差別在批次能力與商品資料：

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
| `stCate` | **`TOK` OK／`TLF` 萊爾富／`TFM` 全家** |
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
| `order_type` | **`1` 代收（取貨付款／貨到付款）／`3` 一般配送（不付款／純配送）** |
| `order_amount` | 代收金額或報值金額 |
| `rv_name` | 取件人姓名 |
| `rv_email` / `rv_mobile` | 取件人信箱／行動電話 |
| `st_code` | 取件門市。**`A01`–`A04`、`A11`、`A12` 必填** |
| `rv_addr` / `rv_zip` | 收件地址與郵遞區號。**`A05`、`A06` 必填**（宅配）|
| `rtn_url` | 回傳網址 |
| `web_para` | 自訂識別資料 |

**`order_status` 分組**：

| 代碼 | 類別 |
|---|---|
| `A01`–`A04` | 超商取貨 |
| `A05`、`A06` | 宅配 |
| `A11`、`A12` | **店港澳**（香港／澳門）|

> ⚠️ **`rv_name` 超過四個中英文字，超商取貨單會印不完整**，可能導致取貨問題。官方特別提醒。
> 💡 **港澳配送**（`A11`/`A12`）是先前未收錄的能力——ezShip 是本 skill 少數支援港澳店配的聚合商。

回傳：`order_id`、`sn_id`、`order_status`、`webPara`。

> ⚠️ **`sn_id` 回傳八個零（`00000000`）代表訂單建立失敗**——這是唯一的失敗訊號，沒有獨立的錯誤碼欄位。非八個零即成功，且**必須把 `sn_id` 存起來**，後續寄件與追蹤貨況都靠它。

亦可用 CURL 直接 POST（官方提供 Linux／Windows 兩種引號寫法範例）。

### 步驟三：貨況查詢

兩種查法，端點不同：

| 依據 | 端點 |
|---|---|
| ezShip 店到店編號 | `.../emap/ezship_request_order_status_api.jsp` |
| 購物網站訂單編號 | `.../emap/ezship_request_order_status_api_byorder.jsp` |

送出：`su_id`、`order_no`、`rtn_url`、`web_para`。

回傳：`sn_id`、`order_no`、`order_status`、`webPara`，另有三個時序欄位：

| 參數 | 說明 |
|---|---|
| `times` | **`1` 第一次配送／`2` 第二次配送／`8` 退還寄件人／`9` 非常規配送** |
| `sdate` | 配送狀態發生日期（`yyyy/mm/dd`），由超商或宅配公司提供 |
| `udate` | ezShip 接收到該狀態的時間（`yyyy/mm/dd hh24:mi`）|

> ⚠️ **有速率限制且會被停權**：官方明文「若因大量反覆查詢結案資料，導致 ezShip 系統忙碌或運行困難，ezShip 將中斷其網路串接之權利」，**建議每筆查詢間隔 3 秒以上**，已結案貨件勿重複查詢。不要做整批預先輪詢。
> ⚠️ **`order_status` 回傳 `S05`（包裹退貨）或 `S06`（包裹配送異常）時無法呈現最終貨況**，需登入 ezShip 系統查詢。
> ⚠️ 訂單號碼重複時，**以最後一次上傳的訂單資料為準**。
> ⚠️ 以訂單編號查詢**不適用簡易版**串接的訂單。

## 3. 申請流程

1. 進入 ezShip 後台
2. 「我的便利配」→「購物網站串接」→「網站串接申請」
3. 提供購物網站網址送出申請
4. ezShip 於 **1–2 個工作日**內完成審核

客服：(02) 2700-3727，週一至週五 09:00–12:00 / 13:00–18:00

## 4. 技術文件

> ✅ **上一輪標記的 404 已查明**：社群流傳的是**無版號檔名** `ezship_WebOrder_HttpRequest.pdf`，實際檔名帶版本後綴。官網 `service_doc` 當時回「系統忙碌中」是暫時性的，現已可正常存取。

| 文件 | 網址 |
|---|---|
| 欄位定義（參數版）| `http://www.ezship.com.tw/file/ezship_WebOrder_HttpRequest_v15.pdf` |
| 欄位定義（XML 版）| `http://www.ezship.com.tw/file/ezship_WebOrder_XML_v15s.pdf` |
| 文件站首頁 | `https://www.ezship.com.tw/service_doc/service_home_w18v1.jsp?vDocNo=1702` |

文件站以 `vDefPage` 參數分頁（`04`–`09` 參數版、`10`–`16` XML 版、`17`–`18` 簡易版、`19`–`23` 貨況串接）。

官方另提供 PHP／JSP 的 BIG5 與 UTF-8 兩種版本程式碼範例。

### 已知欄位線索

- 傳遞參數中有預留的 **`webPara`** 欄位，用於**令牌驗證（token）**功能——這是把 ezShip 回傳對回自家訂單的關鍵欄位，設計上類似其他 provider 的 `MerchantTradeNo` 或 `ExtraData`
- 開源實作可參考：https://github.com/recca0120/payum-ezship（PHP，`src/Api.php`）

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

參數版三支端點（電子地圖／傳送訂單／貨況查詢）的欄位已完整。

| 項目 | 狀態 |
|---|---|
| `order_status` 完整代碼表 | 已知分組 `A01`–`A04` 超商取貨、`A05`/`A06` 宅配、`A11`/`A12` 店港澳，以及貨況的 `S05`/`S06`；**完整對照需解析欄位定義 PDF**，之後併入 `data/status-codes.csv` |
| XML 版欄位 | 端點與能力差異已確認，欄位定義在 `ezship_WebOrder_XML_v15s.pdf` |
| 商品資料結構 | XML 版獨有（可列印含商品明細寄件單），欄位待補 |
| 大宗直寄／店退店的串接方式 | 服務存在，是否走同一組 API 未確認 |

> `webPara` 先前被記為「token 驗證欄位」，**這是誤解**。官方定義為「網站所需額外判別資料，ezShip 將原值回傳」——它是**原值透傳的識別欄位**（類似其他 provider 的 `ExtraData`／`CustomField`），沒有任何驗證或簽章語意。ezShip 的參數版**沒有簽章機制**，安全性倚賴 `su_id` 帳號綁定與 HTTPS。

## 8. 來源

- ezShip 關於便利配 — https://www.ezship.com.tw/staticpage/about.jsp
- 購物網站串接 — https://www.ezship.com.tw/service_doc/service_home_w18v1.jsp?vDocNo=1702
- EasyStore 串接說明 — https://support.easystore.co/zh-tw/article/ezship-1mchswf/
- CYBERBIZ 超商物流教學 — https://www.cyberbiz.io/helpcenter/?p=2524
- 程式碼說明：連結電子地圖 — `…/2017_service_doc_home.jsp?vDocNo=1702&vDefPage=07`
- 程式碼說明：傳送訂單 — `…&vDefPage=08`
- 貨況串接（依訂單編號查詢）— `…&vDefPage=22`
- 欄位定義 PDF（參數版）— http://www.ezship.com.tw/file/ezship_WebOrder_HttpRequest_v15.pdf
- 欄位定義 PDF（XML 版）— http://www.ezship.com.tw/file/ezship_WebOrder_XML_v15s.pdf
- 開源 PHP 實作 — https://github.com/recca0120/payum-ezship
