---
name: taiwan-logistics
description: Taiwan Logistics API integration specialist for ECPay, NewebPay, PAYUNi, SmilePay, PChomePay, PayNow and ezShip aggregators, HCT direct carrier API, and on-demand delivery (Lalamove, pandago). Use when developing shipping flows, implementing CVS pickup (7-11/全家/萊爾富/OK), home delivery (黑貓/中華郵政), cold-chain, store-map selectors, COD orders, or shipment tracking. Handles encryption (MD5, AES-256-CBC, AES-256-GCM, 3DES), store maps, and provider field mappings. 中文觸發：物流串接、超商取貨、店到店、大宗寄倉、取貨付款、電子地圖選店、宅配、冷凍、物流狀態碼、托運單、新竹物流、即時配送。
user-invocable: true
---

# Taiwan Logistics Development Skill

## Sources

| Item | Content |
|---|---|
| Origin | Official vendor API docs, PDF specs and SDKs; every source is registered in the repo's `sources/official-sources.json` (URL, how it is fetched, which files it covers) |
| Providers | `data/providers.csv` has 20 rows: 7 aggregators with a logistics API, 1 direct carrier API (HCT), 2 on-demand services, and 10 rows with no public API (listed so the skill can say so) |
| Rows | **1111 rows** in 5 search domains; per-domain counts come from `python scripts/search.py --stats`, not from this file |
| Provenance | Every row has `doc_url` (official doc) and `trust` (實測 measured / 官方文件 official doc / 推論 inferred); `retrieved_on` is the last date the source was compared |
| Crypto | Expected values are produced by running the vendors' own SDKs or spec samples verbatim (`tests/vectors/`); examples are compared byte for byte |
| Verified | 2026-11-15: self-test passes, `verify-examples.py` passes; known gaps are in `data/pending.csv` |

Rows marked `trust=推論` are inferred from the official docs. Present them as advice, never as an official rule.

## Usage

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

**Single entry point: `scripts/search.py`.** Look everything up there first; the other tools are next steps.

| User-run tools | Purpose |
|---|---|
| `scripts/search.py` | Entry point: query the data (`--stats` for counts) |
| `scripts/recommend.py` | Recommend a provider for a requirement |
| `scripts/generate-logistics-service.py` | Output the verified service implementation (`--output ts` or `py`) |
| `scripts/test_logistics.py` | Signature known-answer test (offline by default; `--live` to reach test environments) |
| `scripts/test_skill.py` | Self-test: number check, provenance columns, routing queries, evals format |
| `scripts/check_numbers.py` | Check every number in this file against the data |
| `examples/*.py` | Runnable per-provider examples to copy into a project |

| Maintainer tools (repo root) | Purpose |
|---|---|
| `scripts/verify-examples.py` | Examples and doc snippets against official test vectors |
| `scripts/validate-data.py` | CSV format, keys, file size |
| `scripts/check-sources.py` | Detect changes in official sources |
| `scripts/add-provenance.py` | Fill CSV provenance columns |

**Dependencies**: `scripts/` uses only the Python standard library, except `test_logistics.py --live`, `--create` and `--query`, which need `requests`.
`examples/` need `pycryptodome` (AES, 3DES) and `requests`: `pip install -r requirements.txt`.

## Routing

**Rule: look it up first, never answer from memory. If the data does not have it, say you could not find it, mark it 待補 (pending) and log it in `data/pending.csv`. Do not guess.**

```bash
python scripts/search.py "<keywords>"                 # auto-detect the domain
python scripts/search.py "<keywords>" --domain <d>    # search one domain
python scripts/search.py "<keywords>" --domain all    # search every domain
python scripts/search.py --stats                      # rows per domain
```

Chinese and colloquial wording works directly (the data has Chinese names and descriptions).

| What the user says | Domain | Command |
|---|---|---|
| "綠界物流狀態 2073 是什麼" / status code meaning | `status` | `search.py "2073" --domain status` |
| "包裹到店了嗎" / delivery states | `status` | `search.py "配達" --domain status` |
| "7-11 取貨付款要帶什麼子類型" / CVS subtype, temperature, COD cap | `logistics_type` | `search.py "7-11 取貨付款" --domain logistics_type` |
| "冷凍可以寄超商嗎" | `logistics_type` | `search.py "冷凍" --domain logistics_type` |
| "建立物流訂單打哪支 API" / map, print, query endpoints | `operation` | `search.py "建立物流訂單" --domain operation` |
| "選店電子地圖" | `operation` | `search.py "電子地圖" --domain operation` |
| "收件門市欄位各家叫什麼" | `field` | `search.py "ReceiverStoreID" --domain field` |
| "Lalamove 有 API 嗎" / which providers, test URLs, encryption | `provider` | `search.py "Lalamove" --domain provider` |
| "黑貓可以直接串嗎" | `provider` | `search.py "tcat" --domain provider`, then `references/carrier-direct-access.md` |
| "該選哪一家物流" | — | `recommend.py "<requirement>"` |

Every result carries `doc_url` and `trust`. Cite `doc_url` in the answer; do not add facts the results do not contain.
Then read the provider's reference:

| Provider | Reference |
|---|---|
| ECPay 綠界 | `references/ecpay-logistics-api.md` |
| NewebPay 藍新 | `references/NEWEBPAY_LOGISTICS_REFERENCE.md` |
| PAYUNi 統一 | `references/payuni-logistics-api.md` |
| SmilePay 速買配 | `references/smilepay-logistics-api.md` |
| PChomePay 拍錢包 | `references/pchomepay-logistics-api.md` |
| PayNow 立吉富 | `references/paynow-logistics-api.md` |
| ezShip 台灣便利配 | `references/ezship-logistics-api.md` |
| HCT 新竹物流 (direct) | `references/hct-logistics-api.md` |
| Lalamove | `references/lalamove-logistics-api.md` |
| pandago and on-demand overview | `references/ondemand-delivery.md` |
| Carriers without a public API | `references/carrier-direct-access.md` |
| Concepts, NewebPay walkthrough, PAYUNi operations, best practices | `references/implementation-guide.md` |

## Tasks

| Task | Steps | Data | Output and evidence of done |
|---|---|---|---|
| Pick a provider | 1. `recommend.py` 2. check `provider` and `logistics_type` | `provider`, `logistics_type` | Recommendation with `doc_url`, labelled as advice |
| CVS pickup order | 1. store map 2. take `StoreID` from the map response 3. create order with the right subtype 4. sign | `operation`, `logistics_type`, `field` | Code; signature matches `verify-examples.py` vectors |
| Home delivery / cold chain | 1. check subtype, temperature and size limits 2. create order | `logistics_type`, `operation` | Code with `doc_url` |
| Status notifications | 1. verify the signature or hash first 2. map codes 3. update idempotently | `status`, reference | Code; unknown codes logged, not guessed |
| Status code lookup | 1. search the code with the provider name | `status` | Meaning with `doc_url`; if not found, say so and log it |
| On-demand delivery | 1. quote 2. order before the quote expires 3. track | `operation`, `ondemand-delivery.md` | Code with `doc_url` |
| Generate a service | `generate-logistics-service.py <Provider> --output ts` or `py` | — | Verified implementation, not a stub |

**Rules when writing code**

1. **Use the store ID from the map response**, not the code shown on the map; FamilyMart and OK can differ.
2. **Signatures differ per provider**: ECPay logistics uses MD5 CheckMacValue (ECPay payment uses SHA256), NewebPay AES-256-CBC + SHA256, PAYUNi AES-256-GCM + SHA256, PayNow logistics 3DES/ECB (not the dynamic AES of PayNow payment). Copy from `examples/`; do not reimplement from memory.
3. **Verify every notification before trusting it**, and keep HashKey and HashIV out of front-end code, repos and logs.
4. **Status codes are provider-specific**: the same number means different things at different providers. Always search with the provider.

## Verify

Run these after producing anything. Every validator exits non-zero on failure, so each one can gate a step.

| Output | Validator | Pass criteria |
|---|---|---|
| Signatures | `python scripts/test_logistics.py` | exit 0 (offline) |
| Examples, doc snippets | `python scripts/verify-examples.py` (repo root, needs `pip install -r requirements-dev.txt`) | FAIL 0, exit 0 |
| Data CSV | `python scripts/validate-data.py` (repo root) | all pass, exit 0 |
| Numbers in this file | `python scripts/check_numbers.py` | exit 0 |
| The skill itself | `python scripts/test_skill.py` | failed 0, exit 0 |
| Answer quality | `python evals/grade.py --with <with-skill answers> --without <without-skill answers>` | with-skill scored accuracy ≥ 90%; results in `evals/RESULTS.md` |

`--live` reaches the providers' test environments; run it only when the user asks.

## Maintenance

- Official source changed: repo root `python scripts/check-sources.py`, update the affected reference and CSV, run the validators above, then `check-sources.py --update`.
- New CSV rows: `python scripts/add-provenance.py`; rows with no official source are marked 推論 and must be logged in `data/pending.csv`.
- Counts changed: `python scripts/check_numbers.py --fix`.
- Status codes rebuild: `_studies/harness/import_logistics_status.py` (source documents stay in `_studies/`, not in the repo).
- After changes, copy the repo's `taiwan-logistics/` over `~/.claude/skills/taiwan-logistics/` without deleting files that exist only in the installed copy.
