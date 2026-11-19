---
name: taiwan-payment
description: Taiwan Payment API integration specialist for ECPay, NewebPay, PAYUNi, SmilePay, PChomePay, ezPay, PayNow, Shopline Payments, LINE Pay v4, TapPay, O'Pay, JKOPAY, SunPay and GoMyPay. Use when developing payment systems, implementing credit card, ATM, CVS, e-wallet, LINE Pay, Apple Pay, Google Pay, Click to Pay, TWQR or BNPL payments, or working with Taiwan payment gateway APIs. Handles encryption (SHA256, AES-256-CBC, AES-256-GCM, dynamic AES-256, RSA, JWT, HMAC-SHA256, Basic Auth → token, Prime token), API requests, and service provider differences. Directory edition: reference files and JSON data only; the search tools and runnable examples ship in the npm package taiwan-payment-skill. 中文觸發：金流串接、綠界、藍新、統一金流、信用卡付款、ATM 虛擬帳號、超商代碼、LINE Pay、Apple Pay、街口、CheckMacValue、TradeSha、付款通知、退款、定期定額。
user-invocable: true
---

# 台灣金流開發技能（directory edition）

This is the reference-only edition built for the Claude plugin directory: official-source
references, code examples in Markdown and the data set as JSON, with no scripts. The full
edition adds the search and recommendation tools, runnable examples and known-answer tests:
`npx taiwan-payment-skill@1.5.17 init`, or <https://github.com/Moksa1123/taiwan-ecommerce-toolkit>.

Keys, HashKey/HashIV and merchant IDs are set and provided by the user. Never ask the user to
paste a production key into the chat; use placeholders in code.

## 資料出處

| 項目 | 內容 |
|---|---|
| 來源 | 各服務商官方文件、官方 PDF 規格書、官方 SDK／外掛原始碼；每個來源登記在 repo 的 `sources/official-sources.json`（網址、取得方式、影響哪些檔） |
| 服務商 | 共 14 家（`data/providers.json`，每家附 `doc_url` 與 `doc_verified`） |
| 出處欄 | 每筆都有 `doc_url`（官方文件）與 `trust`（實測／官方文件／推論）；`retrieved_on` 是官方來源最近一次比對的日期 |

`trust` 是「推論」的資料（`reasoning` 選型建議、`troubleshoot` 疑難排解）是依官方文件歸納的，
轉述給使用者時要說「建議」，不可以說成官方規定。`market_share` 欄是推論，不是官方數字。

## When to use

**何時用**

- 串接台灣金流：信用卡（一次、分期、定期定額）、ATM 虛擬帳號、超商代碼／條碼、電子錢包、TWQR、BNPL
- 計算或除錯簽章與加密：CheckMacValue、TradeInfo／TradeSha、EncryptInfo／HashInfo、LINE Pay 簽章
- 付款通知（callback／webhook）處理、查詢訂單、退款、請款
- 選服務商、比較各家差異、查錯誤碼

**何時不用**

| 情況 | 改用 |
|---|---|
| 開立電子發票、折讓、作廢 | `taiwan-invoice` skill |
| 超商取貨、宅配、物流單 | `taiwan-logistics` skill（PChomePay、PAYUNi 的金物流二合一也在那邊查物流段） |
| LINE Messaging API、LINE Login | `line-api` skill |
| 海外金流（Stripe、PayPal 國際版） | 不在資料集內；直接說查不到 |

## How to look things up

**鐵則：先查再答，不憑記憶。查不到就說查不到，標「待補」並記進 `data/pending.json`，不猜。**

There is no search script in this edition. Read the JSON files directly: every file has
`rows`, and every row has `doc_url` (official source) and `trust`. Filter by `provider` and the
key column (code, field name, operation), and cite `doc_url` in the answer.

| File | Rows | Search domain (full edition) | First columns |
|---|---|---|---|
| `data/error-codes-1.json` | 488 | error | `provider`, `code`, `message_zh`, `message_en`, `category`, `severity` |
| `data/error-codes-2.json` | 488 | error | `provider`, `code`, `message_zh`, `message_en`, `category`, `severity` |
| `data/error-codes-3.json` | 488 | error | `provider`, `code`, `message_zh`, `message_en`, `category`, `severity` |
| `data/error-codes-4.json` | 39 | error | `provider`, `code`, `message_zh`, `message_en`, `category`, `severity` |
| `data/error-codes-5.json` | 473 | error | `provider`, `code`, `message_zh`, `message_en`, `category`, `severity` |
| `data/error-codes-6.json` | 317 | error | `provider`, `code`, `message_zh`, `message_en`, `category`, `severity` |
| `data/error-codes-7.json` | 451 | error | `provider`, `code`, `message_zh`, `message_en`, `category`, `severity` |
| `data/error-codes-8.json` | 278 | error | `provider`, `code`, `message_zh`, `message_en`, `category`, `severity` |
| `data/field-mappings.json` | 19 | field | `field_name`, `field_zh`, `ecpay_name`, `newebpay_name`, `payuni_name`, `smilepay_name` |
| `data/operations.json` | 25 | operation | `operation`, `operation_zh`, `ecpay_endpoint`, `newebpay_endpoint`, `payuni_endpoint`, `smilepay_endpoint` |
| `data/payment-methods.json` | 42 | payment_method | `method_code`, `method_zh`, `method_en`, `ecpay_code`, `newebpay_code`, `payuni_code` |
| `data/pending.json` | 62 | — | `date`, `question`, `why_not_found`, `asked_by`, `status` |
| `data/providers.json` | 14 | provider | `provider`, `display_name`, `auth_method`, `encryption`, `test_url`, `prod_url` |
| `data/reasoning.json` | 45 | reasoning | `scenario`, `recommended_provider`, `confidence`, `reason`, `anti_patterns`, `use_cases` |
| `data/troubleshooting.json` | 46 | troubleshoot | `issue`, `symptom`, `cause`, `solution`, `provider`, `severity` |

Files with a number suffix (`error-codes-1.json`, …) are one data set split by provider to stay
under the directory's file-size limit; look through all of them.

After the data, read the provider's reference for flows, encryption and field details:

| Topic | Reference |
|---|---|
| 「全支付、悠遊付、TWQR 怎麼收」 | — | 讀 `references/twqr-ewallet-landscape.md` |
| 綠界 ECPay | `references/ecpay-payment-api.md` |
| 藍新 NewebPay | `references/newebpay-payment-api.md` |
| 統一 PAYUNi | `references/payuni-payment-api.md` |
| 速買配 SmilePay | `references/smilepay-payment-api.md` |
| PChomePay 支付連 | `references/pchomepay-payment-api.md` |
| ezPay 簡單付 | `references/ezpay-payment-api.md` |
| 立吉富 PayNow | `references/paynow-payment-api.md` |
| SHOPLINE Payments | `references/shopline-payment-api.md` |
| LINE Pay | `references/linepay-payment-api.md` |
| TapPay | `references/tappay-payment-api.md` |
| 歐付寶 O'Pay | `references/opay-payment-api.md` |
| 街口 JKOPAY | `references/jkopay-payment-api.md` |
| 紅陽 SunPay | `references/sunpay-payment-api.md` |
| GoMyPay | `references/gomypay-payment-api.md`（完整規格要向 GoMyPay 申請） |
| 電子支付生態、TWQR | `references/twqr-ewallet-landscape.md` |
| 加密實作、訂單流程、常見問題、測試帳號、檢查清單 | `references/implementation-guide.md` |
| 官方文件稽核紀錄（各家改了什麼、依據網址） | `references/audit-20261117.md` |

`EXAMPLES.md` holds the code examples (TypeScript / Python) in Markdown.

## Writing code

**寫程式時務必遵守**

1. **綠界 CheckMacValue**：排除 CheckMacValue 本身、參數名稱不分大小寫排序、綠界規則的 URL encode 後轉小寫，金流用 SHA256、國內物流用 MD5。
   直接用 `encodeURIComponent` 或 Python `quote_plus` 會在空白、括號時算錯。
2. **藍新 TradeInfo**：AES-256-CBC 加密 query string 後轉 hex；TradeSha 是 `HashKey=…&TradeInfo&HashIV=…` 的 SHA256 大寫。
   解密時 padding 可能到 32 bytes，`RespondType=JSON` 時明文是 JSON。
3. **PAYUNi EncryptInfo**：AES-256-GCM，`hex(base64(密文) + ":::" + base64(tag))`，最外層 hex 不可省；HashInfo 是 HashKey 在前。
4. **ezPay 不是藍新**：網域、欄位、支付工具都不同，ATM、超商代碼、分期要用藍新。
5. **先驗簽再處理通知**，訂單狀態更新要冪等；HashKey、HashIV、Channel Secret 不進前端、repo、log。
6. 完整程式碼在 `references/implementation-guide.md`，都由 完整版的工具 對官方標準答案驗過，不要憑印象改演算法。

## What it runs and connects to

Nothing. This edition has no scripts, hooks or MCP servers and makes no network requests.
API calls happen only in the user's own code, with keys the user provides.
