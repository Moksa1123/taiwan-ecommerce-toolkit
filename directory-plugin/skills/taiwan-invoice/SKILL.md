---
name: taiwan-invoice
description: Taiwan E-Invoice API integration specialist for ECPay, SmilePay, Amego, ezPay, PayNow, O'Pay and SunPay, plus MOF E-Invoice platform queries. Use when developing invoice systems, implementing B2C/B2B invoice issuance, void, allowance, invoice printing, carrier/donation code validation, or working with Taiwan E-Invoice APIs. Handles encryption (AES-128-CBC, AES-256-CBC, MD5, JWT), API requests, and service provider differences. Directory edition: reference files and JSON data only; the search tools and runnable examples ship in the npm package taiwan-invoice-skill. 中文觸發：電子發票串接、開立發票、作廢、折讓、載具、手機條碼、捐贈碼、統編、B2B 三聯式、B2C 二聯式、加值中心、財政部大平台、發票列印。
user-invocable: true
---

# 台灣電子發票開發技能（directory edition）

This is the reference-only edition built for the Claude plugin directory: official-source
references, code examples in Markdown and the data set as JSON, with no scripts. The full
edition adds the search and recommendation tools, runnable examples and known-answer tests:
`npx taiwan-invoice-skill@2.9.13 init`, or <https://github.com/Moksa1123/taiwan-ecommerce-toolkit>.

Keys, HashKey/HashIV and merchant IDs are set and provided by the user. Never ask the user to
paste a production key into the chat; use placeholders in code.

## 資料出處

| 項目 | 內容 |
|---|---|
| 來源 | 各加值中心官方 API 文件與 PDF 規格書、官方 SDK、財政部電子發票整合服務平台規格；每個來源登記在 repo 的 `sources/official-sources.json` |
| 服務商 | `data/providers.json` 共 9 筆：可開立的加值中心 7 家都有 reference，另有財政部大平台（只查詢）與關貿（只登記，沒有 reference） |
| 出處欄 | 每筆都有 `doc_url`（官方文件）與 `trust`（實測／官方文件／推論）；`retrieved_on` 是官方來源最近一次比對的日期 |

`trust` 是「推論」的資料（`reasoning` 選型建議、`troubleshoot` 疑難排解、`tax` 金額公式）是依官方文件歸納的，
轉述給使用者時要說「建議」或「依規格推算」，不可以說成官方規定。

## When to use

**何時用**

- 開立 B2C（二聯式）、B2B（三聯式）電子發票，作廢、折讓、註銷重開
- 載具（手機條碼、自然人憑證）、捐贈碼、統編的驗證
- 發票金額與稅額計算（含稅、未稅、零稅率、免稅）
- 加密與簽章、列印、選加值中心、查錯誤碼
- 財政部大平台查詢（手機條碼驗證、捐贈碼、中獎號碼）

**何時不用**

| 情況 | 改用 |
|---|---|
| 收款、刷卡、退款 | `taiwan-payment` skill |
| 出貨、超取、物流單 | `taiwan-logistics` skill |
| 營業稅申報、會計帳務 | 不在資料集內；直接說查不到 |
| 用財政部大平台開立發票 | 大平台不能開立，要透過加值中心 |

## How to look things up

**鐵則：先查再答，不憑記憶。查不到就說查不到，標「待補」並記進 `data/pending.json`，不猜。**

There is no search script in this edition. Read the JSON files directly: every file has
`rows`, and every row has `doc_url` (official source) and `trust`. Filter by `provider` and the
key column (code, field name, operation), and cite `doc_url` in the answer.

| File | Rows | Search domain (full edition) | First columns |
|---|---|---|---|
| `data/carrier-types.json` | 4 | — | `carrier_type`, `carrier_type_zh`, `code`, `format`, `example`, `validation_regex` |
| `data/error-codes.json` | 294 | error | `provider`, `code`, `message_zh`, `message_en`, `category`, `solution` |
| `data/field-mappings.json` | 26 | field | `field_name`, `description`, `ecpay_name`, `smilepay_name`, `amego_name`, `ezpay_name` |
| `data/operations.json` | 13 | operation | `operation`, `operation_zh`, `ecpay_b2c_endpoint`, `ecpay_b2b_endpoint`, `smilepay_endpoint`, `amego_endpoint` |
| `data/pending.json` | 22 | — | `date`, `question`, `why_not_found`, `asked_by`, `status` |
| `data/providers.json` | 9 | provider | `provider`, `display_name`, `auth_method`, `encryption`, `test_url`, `prod_url` |
| `data/reasoning.json` | 41 | reasoning | `scenario`, `recommended_provider`, `confidence`, `reason`, `decision_rules`, `anti_patterns` |
| `data/tax-rules.json` | 8 | tax | `invoice_type`, `tax_type`, `tax_rate`, `sales_amount_formula`, `tax_amount_formula`, `total_amount_formula` |
| `data/troubleshooting.json` | 33 | troubleshoot | `issue`, `symptom`, `cause`, `solution`, `provider`, `category` |

Files with a number suffix (`error-codes-1.json`, …) are one data set split by provider to stay
under the directory's file-size limit; look through all of them.

After the data, read the provider's reference for flows, encryption and field details:

| Topic | Reference |
|---|---|
| 「沒收錄的加值中心怎麼辦」 | — | 讀 `references/VAC_LANDSCAPE.md` |
| 綠界 ECPay | `references/ECPAY_API_REFERENCE.md` |
| 速買配 SmilePay | `references/SMILEPAY_API_REFERENCE.md` |
| 光貿 Amego | `references/AMEGO_API_REFERENCE.md` |
| ezPay 簡單付 | `references/EZPAY_API_REFERENCE.md` |
| 立吉富 PayNow | `references/PAYNOW_API_REFERENCE.md` |
| 歐付寶 O'Pay | `references/OPAY_API_REFERENCE.md` |
| 紅陽 SunPay | `references/SUNPAY_API_REFERENCE.md` |
| 財政部大平台（只查詢） | `references/MOF_EINVOICE_API_REFERENCE.md` |
| 加值中心生態與選型 | `references/VAC_LANDSCAPE.md` |
| 工具用法、各家比較表、金額計算、加密、列印、常見問題、測試帳號 | `references/implementation-guide.md` |
| 官方文件稽核紀錄（各家改了什麼、依據網址） | `references/audit-20261117.md` |

`EXAMPLES.md` holds the code examples (TypeScript / Python) in Markdown.

## Writing code

**寫程式時務必遵守**

1. **B2C 金額含稅、B2B 金額未稅另計稅額**；B2B 不可用載具或捐贈。各家欄位名稱不同，一律先查 `field`。
2. **捐贈、載具、列印三者互斥規則**各家寫法不同（例：O'Pay 捐贈時 `Print` 必須是 `0`），照 reference 做。
3. **加密各家不同**：綠界、O'Pay、SunPay 用 AES-128-CBC，ezPay 用 AES-256-CBC，PayNow 用 JWT，SmilePay 用共享金鑰；同一家的金流與發票常常也不同。
4. **加密前要先 URL Encode，但各家規則不同**：綠界是 JSON 字串 URL Encode 後再 AES；O'Pay 有自己的 .NET 字元轉換表（與 RFC 3986 不同），SunPay 要 .NET 風格且 `%xx` 小寫。照該家 reference 與 `examples/` 做，不要直接套語言內建函式。
5. **時間戳記有效區間短**，主機要校時；HashKey、HashIV 不進前端、repo、log。

## What it runs and connects to

Nothing. This edition has no scripts, hooks or MCP servers and makes no network requests.
API calls happen only in the user's own code, with keys the user provides.
