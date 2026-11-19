---
name: taiwan-logistics
description: Taiwan Logistics API integration specialist for ECPay, NewebPay, PAYUNi, SmilePay, PChomePay, PayNow and ezShip aggregators, HCT direct carrier API, and on-demand delivery (Lalamove, pandago). Use when developing shipping flows, implementing CVS pickup (7-11/全家/萊爾富/OK), home delivery (黑貓/中華郵政), cold-chain, store-map selectors, COD orders, or shipment tracking. Handles encryption (MD5, AES-256-CBC, AES-256-GCM, 3DES), store maps, and provider field mappings. Directory edition: reference files and JSON data only; the search tools and runnable examples ship in the npm package taiwan-logistics-skill. 中文觸發：物流串接、超商取貨、店到店、大宗寄倉、取貨付款、電子地圖選店、宅配、冷凍、物流狀態碼、托運單、新竹物流、即時配送。
user-invocable: true
---

# Taiwan Logistics Development Skill（directory edition）

This is the reference-only edition built for the Claude plugin directory: official-source
references, code examples in Markdown and the data set as JSON, with no scripts. The full
edition adds the search and recommendation tools, runnable examples and known-answer tests:
`npx taiwan-logistics-skill@1.4.13 init`, or <https://github.com/Moksa1123/taiwan-ecommerce-toolkit>.

Keys, HashKey/HashIV and merchant IDs are set and provided by the user. Never ask the user to
paste a production key into the chat; use placeholders in code.

## Sources

| Item | Content |
|---|---|
| Origin | Official vendor API docs, PDF specs and SDKs; every source is registered in the repo's `sources/official-sources.json` (URL, how it is fetched, which files it covers) |
| Providers | `data/providers.json` has 20 rows: 7 aggregators with a logistics API, 1 direct carrier API (HCT), 2 on-demand services, and 10 rows with no public API (listed so the skill can say so) |
| Provenance | Every row has `doc_url` (official doc) and `trust` (實測 measured / 官方文件 official doc / 推論 inferred); `retrieved_on` is the last date the source was compared |

Rows marked `trust=推論` are inferred from the official docs. Present them as advice, never as an official rule.

## When to use

**Use this skill for**

- CVS pickup (7-ELEVEN, FamilyMart, Hi-Life, OK): store-map selection, C2C store-to-store, B2C bulk warehouse, cash on delivery
- Home delivery, cold chain, and the HCT direct carrier API
- On-demand delivery quotes and orders (Lalamove, pandago)
- Shipment status codes, notifications, labels, tracking, and each provider's field names and signatures

**Do not use it for**

| Case | Use instead |
|---|---|
| Taking payment (card, ATM, CVS payment code) | `taiwan-payment` skill |
| Issuing e-invoices | `taiwan-invoice` skill |
| T-Cat, Pelican, Kerry TJ, Chunghwa Post, 7-11 MyShip direct APIs | None are public. Say so and point to `references/carrier-direct-access.md` |

## How to look things up

**Rule: look it up first, never answer from memory. If the data does not have it, say you could not find it, mark it 待補 (pending) and log it in `data/pending.json`. Do not guess.**

There is no search script in this edition. Read the JSON files directly: every file has
`rows`, and every row has `doc_url` (official source) and `trust`. Filter by `provider` and the
key column (code, field name, operation), and cite `doc_url` in the answer.

| File | Rows | Search domain (full edition) | First columns |
|---|---|---|---|
| `data/field-mappings.json` | 22 | field | `field_name`, `field_zh`, `ecpay_name`, `newebpay_name`, `payuni_name`, `smilepay_name` |
| `data/logistics-types.json` | 57 | logistics_type | `logistics_type`, `logistics_sub_type`, `name_zh`, `provider`, `type`, `collection_available` |
| `data/operations.json` | 52 | operation | `operation`, `operation_zh`, `ecpay_endpoint`, `newebpay_endpoint`, `payuni_endpoint`, `method` |
| `data/pending.json` | 33 | — | `date`, `question`, `why_not_found`, `asked_by`, `status` |
| `data/providers.json` | 20 | provider | `provider`, `name_zh`, `name_en`, `type`, `api_available`, `test_merchant_id` |
| `data/status-codes-1.json` | 496 | status | `provider`, `code`, `status_zh`, `status_en`, `category`, `description` |
| `data/status-codes-2.json` | 455 | status | `provider`, `code`, `status_zh`, `status_en`, `category`, `description` |
| `data/status-codes-3.json` | 24 | status | `provider`, `code`, `status_zh`, `status_en`, `category`, `description` |

Files with a number suffix (`error-codes-1.json`, …) are one data set split by provider to stay
under the directory's file-size limit; look through all of them.

After the data, read the provider's reference for flows, encryption and field details:

| Topic | Reference |
|---|---|
| T-Cat, Pelican, Kerry TJ, Chunghwa Post, 7-11 MyShip direct APIs | None are public. Say so and point to `references/carrier-direct-access.md` |
| "黑貓可以直接串嗎" | `provider` | `search.py "tcat" --domain provider`, then `references/carrier-direct-access.md` |
| ECPay 綠界 | `references/ecpay-logistics-api.md` |
| NewebPay 藍新 | `references/NEWEBPAY_LOGISTICS_REFERENCE.md` |
| PAYUNi 統一 | `references/payuni-logistics-api.md` |
| SmilePay 速買配 | `references/smilepay-logistics-api.md` |
| PChomePay支付連 | `references/pchomepay-logistics-api.md` |
| PayNow 立吉富 | `references/paynow-logistics-api.md` |
| ezShip 台灣便利配 | `references/ezship-logistics-api.md` |
| HCT 新竹物流 (direct) | `references/hct-logistics-api.md` |
| Lalamove | `references/lalamove-logistics-api.md` |
| pandago and on-demand overview | `references/ondemand-delivery.md` |
| Carriers without a public API | `references/carrier-direct-access.md` |
| Concepts, NewebPay walkthrough, PAYUNi operations, best practices | `references/implementation-guide.md` |
| 官方文件稽核紀錄（各家改了什麼、依據網址） | `references/audit-20261117.md` |

`EXAMPLES.md` holds the code examples (TypeScript / Python) in Markdown.

## Writing code

**Rules when writing code**

1. **Use the store ID from the map response**, not the code shown on the map; FamilyMart and OK can differ.
2. **Signatures differ per provider**: ECPay logistics uses MD5 CheckMacValue (ECPay payment uses SHA256), NewebPay AES-256-CBC + SHA256, PAYUNi AES-256-GCM + SHA256, PayNow logistics 3DES/ECB (not the dynamic AES of PayNow payment). Copy from `examples/`; do not reimplement from memory.
3. **Verify every notification before trusting it**, and keep HashKey and HashIV out of front-end code, repos and logs.
4. **Status codes are provider-specific**: the same number means different things at different providers. Always search with the provider.

## What it runs and connects to

Nothing. This edition has no scripts, hooks or MCP servers and makes no network requests.
API calls happen only in the user's own code, with keys the user provides.
