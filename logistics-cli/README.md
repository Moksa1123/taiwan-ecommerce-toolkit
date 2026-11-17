# taiwan-logistics

A Claude skill for integrating Taiwan logistics APIs: convenience-store pickup, home delivery, store-map selection, cash on delivery and shipment tracking, based on each provider's official documentation.

[![npm version](https://img.shields.io/npm/v/taiwan-logistics-skill)](https://www.npmjs.com/package/taiwan-logistics-skill)
[![License: MIT](https://img.shields.io/github/license/Moksa1123/taiwan-ecommerce-toolkit)](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/LICENSE)

English | [繁體中文](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/taiwan-logistics/README.zh-TW.md)

This is an unofficial project. It is not affiliated with or endorsed by ECPay, NewebPay, PAYUNi, SmilePay, PChomePay, PayNow, ezShip, HCT, Lalamove, pandago, the convenience-store chains or any other company named here. Brand names are written the way each company writes them and belong to their owners.

## What it does

- Covers 7 aggregators with a logistics API (ECPay, NewebPay, PAYUNi, SmilePay, PChomePay, PayNow, ezShip), the HCT direct carrier API, and on-demand delivery (Lalamove, pandago).
- Gives Claude each provider's signing and encryption rules (MD5 CheckMacValue, AES-256-CBC, AES-256-GCM, 3DES) with runnable Python examples.
- Searches 1111 rows of data offline with `scripts/search.py`: providers, API operations, logistics types, field mappings and shipment status codes.
- Generates a service module for a provider (`scripts/generate-logistics-service.py`) and suggests a provider from plain-language requirements (`scripts/recommend.py`).
- Covers convenience-store pickup (7-ELEVEN, FamilyMart, Hi-Life, OK mart), home delivery, cold chain, store-map selectors, cash on delivery and tracking.

## When to use

Use it when you are:

- building a shipping flow with convenience-store pickup or home delivery;
- adding a store-map selector to a checkout;
- creating shipments, printing labels or reading status callbacks;
- looking up what a logistics status code means, or choosing a provider.

Use something else for:

- collecting payment, including the payment side of ECPay, NewebPay or PAYUNi: use [taiwan-payment](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/tree/main/taiwan-payment);
- issuing e-invoices: use [taiwan-invoice](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/tree/main/taiwan-invoice);
- shipping outside Taiwan, or a carrier contract that has no public API: not covered (the skill says so instead of guessing).

## Install

Requirements: Python 3 for the scripts, which use only the standard library. The files in `examples/` and the network options of `scripts/test_logistics.py` also need `pycryptodome` (AES, 3DES) and `requests`; install them with `pip install -r requirements.txt`. Node.js 18 or later is needed only for the npx installer. Works on Windows, macOS and Linux.

Claude Code plugin (installs all three Taiwan skills: invoice, payment, logistics):

```text
/plugin marketplace add Moksa1123/taiwan-ecommerce-toolkit
/plugin install taiwan-ecommerce@taiwan-ecommerce-toolkit
```

npx (copies the skill into the current project; `--ai` also accepts other agents such as `cursor` or `codex`, `--global` installs into your home directory):

```bash
npx taiwan-logistics-skill@1.4.11 init --ai claude
```

Manual copy:

```bash
git clone https://github.com/Moksa1123/taiwan-ecommerce-toolkit.git
cp -r taiwan-ecommerce-toolkit/taiwan-logistics ~/.claude/skills/
```

## Quick start

Ask Claude, for example:

- "Add ECPay convenience-store pickup with a store map to my checkout, in Python."
- "Create a PAYUNi home-delivery shipment and download the label."
- "What does ECPay logistics status 2073 mean?"

Or search the data yourself from the skill folder:

```bash
python3 scripts/search.py "2073" --domain status --max 1
```

Expected output (shortened):

```text
搜索查詢: '2073' (域: status)
[1] 分數: 7.62 | 域: status
  provider: ecpay
  code: 2073
  status_zh: 包裹配達取件門市
  category: at_store
  description: 物流商：UNIMART、UNIMARTC2C、HILIFE、HILIFEC2C
  doc_url: https://developers.ecpay.com.tw/7380/
  trust: 官方文件
```

## Trigger phrases

English: Taiwan logistics, CVS pickup, convenience-store pickup, store-to-store shipping, store map, home delivery, cold chain, cash on delivery, shipment tracking, logistics status code, HCT, Lalamove, on-demand delivery.

中文：物流串接、超商取貨、店到店、大宗寄倉、取貨付款、電子地圖選店、宅配、冷凍、物流狀態碼、托運單、新竹物流、即時配送。

## What it runs and connects to

The skill is Markdown documentation, CSV data and local Python scripts. It never sends data anywhere on its own. Network calls happen only when you run a connectivity option of the test script or run an example file.

| Script | What it does | Network | Files written |
|---|---|---|---|
| `scripts/search.py` | Searches `data/*.csv` | None | None |
| `scripts/recommend.py` | Suggests a provider from `data/*.csv` | None | None |
| `scripts/generate-logistics-service.py` | Prints a Python or TypeScript module for a provider | None | None (writes to standard output) |
| `scripts/test_logistics.py` | Known-answer test of ECPay signing; offline by default | `--live`: HEAD request to the sandbox of ECPay (`logistics-stage.ecpay.com.tw`), NewebPay (`ccore.newebpay.com`) and PAYUNi (`sandbox-api.payuni.com.tw`). `--create` and `--query`: POST to the ECPay logistics sandbox | None |
| `scripts/check_numbers.py` | Checks that every number in `SKILL.md` and these READMEs matches the data | None | With `--fix`, those three files |
| `scripts/test_skill.py` | Self-test; runs the checks above offline | None | None |
| `examples/*.py` | Reference clients for each provider | When run directly, calls the sandbox or production host defined at the top of that file | None |
| `examples/store-map-integration-example.html` | Store-map sample page and server code | None by itself; callback URLs are placeholders | None |

Credentials (merchant ID, HashKey and HashIV, API keys and secrets, carrier account numbers) are supplied by you in your own code or configuration, for example environment variables. The repository stores no real credentials. Test values that appear in the docs and scripts are the providers' published sandbox values.

## How it's verified

- Data source: official provider API documentation, PDF specifications and SDKs. Every source is registered in [`sources/official-sources.json`](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/sources/official-sources.json), and each data row carries `doc_url` and `trust`.
- Self-test: `python3 scripts/test_skill.py` runs 42 checks, 0 failures (run on 2026-11-17).
- Evals: on the 11 scored questions, Claude answered 11 correctly with the skill and 0 without it. See [`evals/RESULTS.md`](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/taiwan-logistics/evals/RESULTS.md).
- CI runs `scripts/verify-examples.py`, which compares the example code byte for byte with expected values produced by the providers' own SDKs and spec samples ([`tests/vectors/`](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/tree/main/tests/vectors)).

## Limits

- Convenience-store chains, T-cat, Chunghwa Post and other carriers without a public API are listed only so Claude can say so; reach them through an aggregator.
- Lalamove and pandago have references but no runnable example. HCT documentation is available only after applying to HCT.
- `test_logistics.py --create` and `--query` work with ECPay only; NewebPay and PAYUNi need your own merchant account.
- Known gaps are tracked in [`data/pending.csv`](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/taiwan-logistics/data/pending.csv).

## Repo layout

```text
taiwan-logistics/
├── SKILL.md         # instructions Claude reads
├── EXAMPLES.md      # longer code examples
├── references/      # one API reference per provider, on-demand overview
├── examples/        # runnable Python clients and a store-map page
├── data/            # CSV data for search.py and recommend.py; pending.csv
├── scripts/         # search, recommend, generator, tests, number check
└── evals/           # eval questions, grader and results
```

## License & author

MIT License. Made by Moksa ([moksaweb.com](https://moksaweb.com)). Part of [Taiwan E-commerce Toolkit](https://github.com/Moksa1123/taiwan-ecommerce-toolkit).
