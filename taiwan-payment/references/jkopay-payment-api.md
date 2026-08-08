# 街口支付 JKOPAY 商家 API 參考

> 官方開放文件: https://open-doc.jkos.com/
> 公司: 街口電子支付股份有限公司（專營電子支付機構）
> Captured: 2026-08-08 · doc_access: **public**（文件站免登入）
> Status: **partial** — 文件站結構與模組已確認；文件站為 SPA，參數層需以瀏覽器取得

## 0. 為什麼收錄

街口是台灣使用量最大的電子支付之一，而且**它是 10 家專營電支中極少數自己開了公開文件站的**（另一家是歐付寶）。多數電支（全支付、悠遊付、一卡通、icash Pay、橘子支）都要簽約才給文件。

對本 skill 有兩個直接價值：

1. **可直接串**——量體夠大時不必透過聚合商抽成
2. **可用來修正推測碼**——`data/payment-methods.csv` 裡 NewebPay/ezPay 的 `JKOPAY?` 等代碼標記為未驗證，街口官方文件可作為交叉比對基準

## 1. 文件站結構

`open-doc.jkos.com` 分五大模組：

| 模組 | 內容 |
|---|---|
| **授權扣款** | 定期付款／訂閱模式的 API 整合 |
| **線上支付** | 網頁與行動應用的交易處理 |
| **線下交易（POS）** | 實體店面支付 |
| **inApp 第三方服務** | Web SDK 與 OAuth 認證 |
| **街口幣發放** | 虛擬積分／獎勵發放 |

每個模組皆含：

- **API 協議規則**——連線標準與規格
- **加簽加密**——安全驗證機制
- **完整 API 列表**——付款、退款、查詢
- **錯誤代碼表**——文件特別強調「代碼意義」與「統一錯誤代碼表」

版權標示：©2022 Jkopay Co. Ltd.

## 2. 能力範圍（與本 skill 其他 provider 對照）

| 能力 | 街口直連 | 走聚合商（ECPay 等） |
|---|---|---|
| 線上付款 | ✅ | ✅ |
| 退款 | ✅ | ✅ |
| 查詢 | ✅ | ✅ |
| **定期扣款／訂閱** | ✅ 授權扣款模組 | ⚠️ 多數聚合商的街口不支援定期扣款 |
| **實體店 POS** | ✅ | 部分（多走 TWQR） |
| **App 內第三方登入（OAuth）** | ✅ | ❌ |
| **發放街口幣做行銷** | ✅ | ❌ |

> **這張表是選型關鍵**：如果你只是要在結帳頁多一個「街口」按鈕，走 ECPay 的 `DigitalPayment` umbrella 最省事。如果你要做**訂閱制、實體店、或街口幣行銷**，就非得直連不可——這些能力聚合商給不了。

## 3. TWQR 關係

街口是 TWQR（電支跨機構共用平台）的參與機構之一。實體店若採 TWQR 一碼收全部，可涵蓋街口而不必個別串接。詳見 [twqr-ewallet-landscape.md](twqr-ewallet-landscape.md)。

## 4. 其他取得街口的路徑

| 路徑 | 說明 |
|---|---|
| **TapPay** | 有街口專屬文件站 `docs.tappaysdk.com/jko-pay/`（含 Backend 頁），走 Prime → pay-by-prime 流程。見 [tappay-payment-api.md](tappay-payment-api.md) |
| **ECPay** | `ChoosePayment=DigitalPayment` umbrella，消費者於綠界選擇頁挑街口 |
| **PAYUNi** | `JKoPay` 直送代碼（已驗證） |
| **HiTRUSTpay** | 有街口介接方案 |
| **Link Pay（TapPay）** | 連結收款，支援街口 |

## 5. 待補

文件站為 SPA（前端路由），WebFetch 取得的深層連結回 404，本次無法擷取參數層。需以瀏覽器（或 headless browser）逐頁取得後補齊：

| 待補項目 | 優先 |
|---|---|
| 線上支付：建立訂單／付款／退款／查詢的端點 URL 與參數 | 高 |
| 加簽加密演算法（digest / signature 產生方式） | 高 |
| 統一錯誤代碼表（併入 `data/error-codes.csv`） | 高 |
| 授權扣款（定期）流程與參數 | 中 |
| inApp OAuth 流程 | 中 |
| 線下 POS API | 低 |
| 街口幣發放 API | 低 |

補齊後應可將 `data/payment-methods.csv` 中 `jkopay` 列的推測碼註記更新為已驗證。

## 6. 來源

- 街口開放文件 — https://open-doc.jkos.com/
- 街口店家收款 — https://www.jkopay.com/application/store
- TapPay 街口 Backend 文件 — https://docs.tappaysdk.com/jko-pay/zh/back.html
- TapPay 街口支付服務頁 — https://www.tappaysdk.com/taiwan-zhtw/service/payments/jko-pay
- HiTRUSTpay 街口介紹 — https://www.hitrustpay.com.tw/page_jkopay.html
