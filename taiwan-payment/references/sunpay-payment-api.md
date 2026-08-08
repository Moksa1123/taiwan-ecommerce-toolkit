# 紅陽科技 SunPay 金流 API 參考

> 開發者專區: https://www.sunpay.com.tw/developers/
> 教學手冊站: https://doc.esafe.com.tw/
> 電子發票平台: https://inv.sunpay.com.tw/
> Captured: 2026-08-08 · doc_access: **public**（手冊免登入公開下載）
> Status: **partial** — 服務矩陣、文件現行網址與版本已確認；參數層待補（手冊為 PDF，尚未下載解析）

## 0. 為什麼收錄——含一個競品訊號

紅陽科技（品牌「紅陽支付」／舊稱 esafe）是台灣老牌金流商，同時做**金流 + 電子發票 + 超商代收 + 物流**。

**值得注意的是**：紅陽的開發者專區目前直接列出「**AI 串接指南（Claude Code Skill）**」：

| 項目 | 版本 | 更新日 |
|---|---|---|
| 金流 AI 串接指南（Claude Code Skill） | v1.1.0 | 2026-07-28 |
| 電子發票 AI 串接指南（Claude Code Skill） | v2.3 | 2026-07-28 |

加上綠界官方已釋出 `ECPay/ecpay-api-skill`（見 `_studies/ecpay-skill-reference/`），這是第二家自己出 skill 的供應商。

> **對本專案的策略含意**：單一供應商的 API skill 正在被供應商自己吃掉。本 toolkit 的差異化不能是「把某一家文件抄得更完整」，而必須是**跨供應商的欄位對照、代碼比對與選型決策**（`field-mappings.csv` / `reasoning.csv` / `recommend.py` 這條線）。

## 1. 服務矩陣

依 `doc.esafe.com.tw` 教學手冊站：

### 金流

| 類別 | 服務 |
|---|---|
| 信用卡 | 紅陽PAY(swipy)、實體刷卡、信用卡、網址付、EDC 刷卡機 |
| 現金 | 網路 ATM、台灣PAY |
| 超商代收付 | 代碼付款、條碼付款 |

### 物流 ⭐

| 服務 |
|---|
| 超商便利送 |
| 宅配通 |

> **這一項值得注意**：紅陽同時提供物流，且含**宅配通**——宅配通本身沒有公開 API（見 [../../taiwan-logistics/references/carrier-direct-access.md](../../taiwan-logistics/references/carrier-direct-access.md)），紅陽是目前盤點到少數可經由聚合商取得宅配通的路徑之一。

### 電子發票

獨立平台 https://inv.sunpay.com.tw/，有專屬技術串接手冊 v2.3。

### 後台功能

系統登入、修改密碼、基本資料、服務設定、交易查詢、出貨列印、撥款查詢、電子發票、退貨申請、文件下載。

## 2. 技術文件

### 直連下載網址（2026-08-08 自開發者頁擷取）

> ✅ **上一輪標記的 404 已解決**：紅陽把技術文件從 `www.sunpay.com.tw/wp-content/uploads/…` 搬到 **Google Cloud Storage**（`storage.googleapis.com/joinchill-image/sunpay_techdoc/…`）。舊連結全數失效，以下為現行網址。

| 分類 | 文件 | 版本 | 更新 | 網址 |
|---|---|---|---|---|
| API 金流串接 | **金流技術串接手冊** | **v1.1.0** | 2026-05-25 | `…/202607/紅陽科技金流服務-金流技術串接手冊V1.1.0.pdf` |
| API 金流串接 | AI 串接指南（Claude Code Skill）| v1.1.0 | 2026-07-28 | `…/202607/sunpay-payment-skill-v1.1.0-v1.zip` |
| API 金流串接 | 範例程式碼 PHP | — | — | `…/202603/金流範例程式SampleCode_PHP.zip` |
| API 金流串接 | 範例程式碼 JAVA | — | — | `…/202603/金流範例程式SampleCode_JAVA.zip` |
| 電子發票 | **電子發票技術串接手冊** | **v2.3** | — | `…/202603/紅陽科技電子發票技術串接手冊V2.3.pdf` |
| 電子發票 | AI 串接指南（Claude Code Skill）| v2.3 | 2026-07-28 | `…/202607/sunpay-einvoice-skill-v2.3-v1.zip` |
| 購物車模組 | WooCommerce | 10.1.0 | 2026-01-30 | `…/202603/sunpay_WooCommerce_1.0.2.zip` |
| 購物車模組 | Magento 2 | 2.4.7-p1 | 2025-12-30 | `…/202603/sunpay-Magento2.zip` |
| 購物車模組 | OpenCart | 4.1.0.3 | 2025-12-30 | `…/202603/sunpay_OpenCart.zip` |

前綴皆為 `https://storage.googleapis.com/joinchill-image/sunpay_techdoc/`。

### 測試環境申請

| 用途 | 入口 |
|---|---|
| 金流測試環境 | https://testmerchant.sunpay.com.tw/#/formTabs |
| 電子發票測試帳號 | https://testinv.sunpay.com.tw/sign-up |

> ✅ **版本號疑問已釐清**：開發者頁現行的**金流技術串接手冊就是 v1.1.0**（2026-05-25），AI skill 恰巧同為 v1.1.0。先前看到的「v4.6（2025/10）」是**改版前舊站的檔名**，該連結已失效。以 v1.1.0 為準。

| 其他文件 | 取得 |
|---|---|
| 教學手冊站 | https://doc.esafe.com.tw/ |
| 操作手冊 | https://www.sunpay.com.tw/manual/ |
| 實質受益人聲明書 | `…/202603/產-20230530法人或團體實質受益人聲明書.pdf` |

## 3. 購物車模組

| 平台 | 版本 |
|---|---|
| WooCommerce | v10.1.0 |
| Magento 2 | v2.4.7-p1 |
| OpenCart | v4.1.0.3 |

> 三大自架購物車都有官方模組，對 WordPress/WooCommerce 專案而言這是實用的加分項（本 repo 的使用者情境常涉及 WooCommerce）。

## 4. 串接流程

1. 申請測試帳號
2. 下載串接手冊及 sample code
3. 串接購物車（或自建）

聯絡：(02) 2502-6969

## 5. 待補

**文件取得問題已排除**——現行 PDF 網址如 §2，免登入可下載。以下待補純粹是尚未解析 PDF 內容：

| 項目 | 優先 | 來源 |
|---|---|---|
| 建立訂單端點 URL 與必填參數 | 高 | 金流手冊 v1.1.0 |
| 檢查碼／加密機制 | 高 | 金流手冊 v1.1.0 |
| 付款方式代碼表 | 高 | 金流手冊 v1.1.0 |
| 錯誤碼表（併入 `data/error-codes.csv`） | 中 | 金流手冊 v1.1.0 |
| 電子發票 API 端點與參數 | 中 | 電子發票手冊 v2.3 |
| 物流（超商便利送、宅配通）端點與參數 | 中 | 金流手冊或洽業務 |
| 對照紅陽官方 Claude Code Skill 的涵蓋範圍，決定我們補到什麼程度 | 高 | skill zip |

## 6. 來源

- 開發者專區 — https://www.sunpay.com.tw/developers/
- 教學手冊站 — https://doc.esafe.com.tw/
- 操作手冊 — https://www.sunpay.com.tw/manual/
- 金流串接頁 — https://www.sunpay.com.tw/金流串接/
- 電子發票整合服務 — https://inv.sunpay.com.tw/
