# 紅陽科技 SunPay 金流 API 參考

> 開發者專區: https://www.sunpay.com.tw/developers/
> 教學手冊站: https://doc.esafe.com.tw/
> 電子發票平台: https://inv.sunpay.com.tw/
> Captured: 2026-08-08 · doc_access: **public**（手冊公開；本次直連下載 404，須自開發者頁取得）
> Status: **partial** — 服務矩陣已確認，參數層待補

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

| 文件 | 版本 | 取得 |
|---|---|---|
| 金流技術串接手冊 | v4.6（2025/10）／開發者頁另標 v1.1.0 | https://www.sunpay.com.tw/developers/ |
| 電子發票技術串接手冊 | v2.3 | 同上 |
| 範例程式碼 | PHP、JAVA | 同上 |
| 操作手冊 | — | https://www.sunpay.com.tw/manual/ |

⚠️ **本次直連下載 PDF 回 404**（`www.sunpay.com.tw/wp-content/uploads/2025/10/…v4.6.pdf` 與 `forms_download/…v4.1.1.pdf` 皆是）。可能有 referer 檢查或已改版。請自開發者專區頁面取得。

⚠️ **版本號待釐清**：開發者頁顯示金流手冊 v1.1.0，但 PDF 檔名為 v4.6。推測 v1.1.0 是 AI skill 版本、v4.6 是 API 手冊版本，需確認。

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

| 項目 | 優先 |
|---|---|
| 建立訂單端點 URL 與必填參數 | 高 |
| 檢查碼／加密機制（本次未取得） | 高 |
| 付款方式代碼表 | 高 |
| 錯誤碼表（併入 `data/error-codes.csv`） | 中 |
| 物流（超商便利送、宅配通）端點與參數 | 中 |
| 電子發票 API 端點與參數 | 中 |
| 對照紅陽官方 Claude Code Skill 的涵蓋範圍，決定我們補到什麼程度 | 高 |

## 6. 來源

- 開發者專區 — https://www.sunpay.com.tw/developers/
- 教學手冊站 — https://doc.esafe.com.tw/
- 操作手冊 — https://www.sunpay.com.tw/manual/
- 金流串接頁 — https://www.sunpay.com.tw/金流串接/
- 電子發票整合服務 — https://inv.sunpay.com.tw/
