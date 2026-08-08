# 台灣電子支付／行動支付生態地圖與 TWQR

> Captured: 2026-08-08
> 這份文件回答一個高頻問題：**「街口、全支付、全盈+PAY、悠遊付、寶雅 PAY… 這些我要怎麼串？」**
> 短答：**絕大多數不直接串。** 下面說明為什麼，以及該走哪條路。

## 0. 先分清楚四種東西

台灣「XX Pay」特別多，但它們不是同一類東西，串接路徑完全不同：

| 類別 | 是什麼 | 商家怎麼接 | 本 skill 涵蓋 |
|---|---|---|---|
| **A. 專營電子支付機構** | 有金管會電支牌照，可儲值、可轉帳 | 少數有自家商家 API；多數透過聚合商或 TWQR | 代碼對照表（本文件） |
| **B. 收單／聚合商** | 幫你一次接完 A 類 + 信用卡 + ATM + 超商 | **這才是你真正要串的東西** | ✅ 10+ 家完整 reference |
| **C. 零售自有錢包** | 零售商自家 App 內的儲值/會員支付 | **封閉生態，對外沒有商家 API** | 說明限制（本文件） |
| **D. 開店平台 / OMO SaaS** | 91APP、SHOPLINE、CYBERBIZ、meepshop | 有 Open API，但那是**電商後台 API**，不是金流 | 超出本 skill 範圍（本文件簡述） |

**最常見的誤解**：把 C 類（寶雅 PAY、家樂福錢包、SKM Pay）當成可以串的金流。它們不是。

## 1. A 類——專營電子支付機構（10 家）

依金融聯合徵信中心公告之專營電子支付機構名單：

| # | 公司全名 | 品牌 | 我們的 `payment-methods.csv` 代碼 | 自家公開商家文件 |
|---|---|---|---|---|
| 1 | 街口電子支付股份有限公司 | 街口支付 JKOPAY | `jkopay` | ✅ [open-doc.jkos.com](https://open-doc.jkos.com/)（見 [jkopay-payment-api.md](jkopay-payment-api.md)） |
| 2 | 全支付電子支付股份有限公司 | 全支付 PX Pay Plus | `pxpay_plus` | ❌ 需簽約；文件由聚合商提供 |
| 3 | 全盈支付金融科技股份有限公司 | 全盈+PAY | `plus_pay` | ⚠️ 部分公開：[TapPay Plus Pay Docs](https://docs.tappaysdk.com/plus-pay/zh/home.html) |
| 4 | 悠遊卡股份有限公司 | 悠遊付 EasyWallet | `easywallet` | ❌ 需簽約 |
| 5 | 一卡通票證股份有限公司 | iPASS MONEY | `ipass_money` | ❌ 需簽約 |
| 6 | 愛金卡股份有限公司 | icash Pay | `icash_pay` / `icash` | ❌ 需簽約 |
| 7 | 橘子支行動支付股份有限公司 | 橘子支付 GAMA PAY | *（尚未收錄）* | ❌ 需簽約 |
| 8 | 歐付寶電子支付股份有限公司 | 歐付寶 O'Pay | — | ✅ [developers.opay.tw](https://developers.opay.tw/download/document)（見 [opay-payment-api.md](opay-payment-api.md)） |
| 9 | 簡單行動支付股份有限公司 | ezPay 簡單付 | — | ⚠️ 需帳號（已收錄 [ezpay-payment-api.md](ezpay-payment-api.md)） |
| 10 | 連加電子支付股份有限公司 | LINE Pay Money | `linepay` 相關 | ✅ LINE Pay v4（已收錄 [linepay-payment-api.md](linepay-payment-api.md)） |

**注意**：
- 8、9、10 同時是 A 類（電支機構）**也是** B 類（聚合商／可直接串的金流），所以我們有完整 reference。
- PChomePay 拍錢包（國際連）不在現行專營電支名單中，但仍以聚合商身分提供金流+物流 API，見 [pchomepay-payment-api.md](pchomepay-payment-api.md)。
- 另有多家**兼營**電支的銀行（台灣Pay 體系），不在此表。

### 為什麼 2～7 沒有公開文件

這幾家的商業模式是「先簽約再給文件」。實務上商家有三條路：

1. **走聚合商**（推薦）——ECPay / NewebPay / PAYUNi / TapPay 等已經幫你接好，你只要送一個付款方式代碼
2. **走 TWQR**——簽一家電支，收全部（見 §3）
3. **直接簽約**——量體夠大才划算，且每家一套 API

## 2. 各聚合商的電支代碼對照

⚠️ **本表部分代碼標為推測，尚未由官方文件驗證**——已在 `data/payment-methods.csv` 用 `?` 標記。串接前務必以該聚合商的官方 PDF 確認。

| 錢包 | ECPay | PAYUNi | NewebPay / ezPay | PayNow | TapPay |
|---|---|---|---|---|---|
| 街口 | `DigitalPayment` umbrella | `JKoPay` ✅ | `JKOPAY?` 未驗證 | `JKOPAY?` 未驗證 | ✅ 有專屬文件 |
| 全支付 | `DigitalPayment` umbrella ✅ | — | `PXPAY?` 未驗證 | — | ✅ 支援 |
| 全盈+PAY | `DigitalPayment` umbrella ✅ | — | `PLUSPAY?` 未驗證 | — | ✅ 有專屬文件 |
| 一卡通 | `DigitalPayment` umbrella ✅ | — | `IPASSPAY?` 未驗證 | — | ✅ 支援 |
| 悠遊付 | `DigitalPayment` umbrella ✅ | — | `EASYCARD?` 未驗證 | — | ✅ 支援 |
| icash Pay | `DigitalPayment` umbrella | `ICASH` ✅ | `ICASHPAY?` 未驗證 | 現代版 enum 不含 | ✅ 支援 |
| LINE Pay | ✅ | ✅ | ✅ | ✅ | ✅ |
| AFTEE | `BNPL` umbrella | `AFTEE` ✅ | — | — | ✅ 支援 |

### ECPay 的 umbrella 模式

ECPay 不讓你指定「就要街口」，而是給一個 `DigitalPayment` 傘型代碼，消費者在綠界的付款選擇頁自己挑街口／全盈+PAY／全支付／一卡通／悠遊付／icash pay。

**設計含意**：你的訂單資料裡不會事先知道消費者用哪個錢包，要等付款結果通知回來才知道。若業務邏輯需要「依錢包給不同優惠」，ECPay umbrella 模式做不到，得改用 PAYUNi 的直送代碼或 TapPay。

BNPL 同理：ECPay 用 `BNPL` umbrella 承接 `BNPL_URICH`（裕富無卡分期）與 `BNPL_ZINGALA`（中租銀角零卡）。

## 3. TWQR——電支跨機構共用平台

**是什麼**：財金資訊公司推出的國家級共通 QR Code 支付標準，把 EMV 國際掃碼規格整合進來。一個 QR Code 收所有電支。

**涵蓋**：街口支付、全盈+PAY、全支付、icash pay、iPASS MONEY、橘子支付、歐付寶、悠遊付、簡單付 ezPAY，以及參與台灣Pay 的銀行業者（金融卡／帳戶、Visa、Mastercard、JCB、銀聯掃碼）。

**對商家的意義**：只需和**一家**電子支付機構簽約，就能收受多種付款方式，且以單一系統對帳。

**規格取得**：`doc_access: contract`。TWQR 技術規格不完全公開，須經收單機構／電支機構取得。公開資訊：
- https://www.twqr.com.tw/
- 財金公司〈邁向多元發展之 QR Code 共用平台及技術規格〉：https://www.fisc.com.tw/Upload/d42ce73b-1b82-4f05-899a-f8435b74b9c7/TC/9102.pdf

**線上金流怎麼用**：不必自己接 TWQR。各聚合商已包裝成付款方式代碼：
- ECPay：`TWQR`（另有「歐付寶 TWQR」品項）
- O'Pay 歐付寶：`ChoosePayment=TWQR` ✅ 官方文件已確認
- 見 `data/payment-methods.csv` 的 `twqr` 列

> **TWQR ≠ 台灣Pay。** 台灣Pay 是銀行體系的品牌；TWQR 是把台灣Pay 和各家電支統一起來的**共通標準**。兩者常被混用。

## 4. C 類——零售自有錢包（沒有商家 API）

這些是零售商在自家 App 內建的儲值／會員支付，**封閉生態，只在該品牌通路使用，不對外開放商家串接**：

| 品牌 | 所屬 | 可用範圍 |
|---|---|---|
| POYA PAY | 寶雅 | 寶雅、寶家 |
| 家樂福錢包 Carrefour Wallet | 家樂福 | 家樂福通路（台灣為全球首發市場） |
| SKM Pay | 新光三越 | 新光三越各館（百貨業首家自有行動支付） |
| HAPPY GO Pay | 遠東集團 | 遠東 SOGO、大遠百、Big City、遠企、c!ty'super、愛買、遠傳門市等 |
| friDay 錢包 | 遠傳 | 遠傳生態圈 |

**若你是這些零售商的供應商／要在它們通路上架**：走的是該通路的採購與 POS 系統整合，不是本 skill 的金流 API 範疇。

**若你只是想「也支援寶雅 PAY」**：做不到，也不需要。這類錢包不在第三方電商可收款的清單裡。

> 判斷通則：**這個 Pay 能不能在別人家的店用？** 不能 → C 類 → 沒有商家 API。

## 5. D 類——開店平台 / OMO SaaS

| 平台 | Open API | 性質 |
|---|---|---|
| 91APP | [開發者專區](https://blog.91app.com/developer-api/)，需洽平台取得 API Key + 商店代號 | 訂單／庫存／會員資料整合 |
| SHOPLINE | 需安裝擴充並帳號授權 | 同上（其 SHOPLINE Payments 是獨立金流，已收錄） |
| CYBERBIZ | 可直接授權 | 同上 |
| meepshop | 有 API 服務 | 同上 |

**這些是電商後台 API，不是金流 API。** 它們自己在後台接了 ECPay/NewebPay 等聚合商。若你在做 ERP／OMS 要串訂單，走這裡；若你在做收款，走 B 類。

本 skill 專注 B 類（金流／物流／發票），D 類不納入 provider 清單。

## 6. 決策樹

```
我要收「街口 / 全支付 / 悠遊付 / 一卡通 / icash / 全盈」
├─ 只想接一次，不在乎消費者選哪個錢包
│  └─ ECPay ChoosePayment=ALL 或 DigitalPayment umbrella   ← 最省事
├─ 要能指定特定錢包（例如做錢包別的行銷）
│  ├─ PAYUNi 直送代碼（JKoPay / ICASH …）
│  └─ TapPay（每個錢包有獨立文件與 Prime 流程）
├─ 實體店 / POS，想一碼收全部
│  └─ TWQR（簽一家電支機構，規格經收單機構取得）
└─ 量體很大、要談費率
   └─ 直接簽該電支機構（街口有公開文件，其餘需簽約）

我要收「寶雅 PAY / 家樂福錢包 / SKM Pay / HAPPY GO Pay」
└─ 做不到。封閉生態，無對外商家 API。
```

## 7. 待驗證

| 項目 | 內容 |
|---|---|
| NewebPay / ezPay 電支代碼 | `JKOPAY?` `PXPAY?` `PLUSPAY?` `IPASSPAY?` `EASYCARD?` `ICASHPAY?` 皆為推測，不在已知 MPG channel-key 表中，須以官方 PDF 確認 |
| 悠遊付代碼 | 悠遊付（wallet 產品）vs 悠遊卡（實體卡）可能是不同代碼，實際值可能為 `EASYWALLET` |
| 橘子支付 GAMA PAY | 尚未加入 `payment-methods.csv`，需確認各聚合商是否支援及代碼 |
| TapPay 錢包文件清單 | `docs.tappaysdk.com` 下各錢包子站（`/jko-pay/`、`/plus-pay/` 已確認存在）的完整列表 |
| 街口官方代碼 | 可用 open-doc.jkos.com 反推並修正上表推測碼 |

## 8. 來源

- 專營電子支付機構名單 — https://member.jcic.org.tw/main_member/epayList.aspx
- TWQR 官網 — https://www.twqr.com.tw/
- 財金公司 QR Code 共用平台技術規格 — https://www.fisc.com.tw/Upload/d42ce73b-1b82-4f05-899a-f8435b74b9c7/TC/9102.pdf
- 街口開放文件 — https://open-doc.jkos.com/
- TapPay 全盈+PAY 文件 — https://docs.tappaysdk.com/plus-pay/zh/home.html
- 歐付寶技術文件 — https://developers.opay.tw/download/document
- ECPay BNPL 無卡分期 — https://developers.ecpay.com.tw/36659/
- 91APP 開發者專區 — https://blog.91app.com/developer-api/
