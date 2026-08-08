# ezShip 台灣便利配 物流 API 參考

> 官網: https://www.ezship.com.tw/
> 購物網站串接: https://www.ezship.com.tw/service_doc/service_home_w18v1.jsp?vDocNo=1702
> Captured: 2026-08-08 · doc_access: **apply**（需後台申請串接；串接文件公開流通但官方直連當下不可達）
> Status: **partial** — 服務矩陣與串接流程已確認，欄位層規格待補

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

## 2. 串接方式

官方提供**三種串接方式**，將金物流服務整合進購物網站。（三者的具體差異待補——推測為：純導轉頁面 / 表單 POST / API 呼叫，需以官方文件確認。）

## 3. 申請流程

1. 進入 ezShip 後台
2. 「我的便利配」→「購物網站串接」→「網站串接申請」
3. 提供購物網站網址送出申請
4. ezShip 於 **1–2 個工作日**內完成審核

客服：(02) 2700-3727，週一至週五 09:00–12:00 / 13:00–18:00

## 4. 技術文件

社群與開店平台文件普遍指向：

```
http://www.ezship.com.tw/file/ezship_WebOrder_HttpRequest.pdf
```

⚠️ **本次驗證時該連結回 404**，官網 `service_doc` 頁面亦回「系統忙碌中」。可能已改版或搬遷。取得方式：登入後台文件區，或洽客服索取。

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

## 7. 待驗證

| 項目 | 內容 |
|---|---|
| 文件本體 | `ezship_WebOrder_HttpRequest.pdf` 的現行有效連結 |
| 三種串接方式 | 各自的技術型態與適用情境 |
| 欄位規格 | 建單、電子地圖、查詢、取消、貨態回傳的完整參數 |
| 驗證機制 | `webPara` token 的產生與驗證規則 |
| 狀態碼 | 貨態代碼表（需併入 `data/status-codes.csv`） |

## 8. 來源

- ezShip 關於便利配 — https://www.ezship.com.tw/staticpage/about.jsp
- 購物網站串接 — https://www.ezship.com.tw/service_doc/service_home_w18v1.jsp?vDocNo=1702
- EasyStore 串接說明 — https://support.easystore.co/zh-tw/article/ezship-1mchswf/
- CYBERBIZ 超商物流教學 — https://www.cyberbiz.io/helpcenter/?p=2524
- 開源 PHP 實作 — https://github.com/recca0120/payum-ezship
