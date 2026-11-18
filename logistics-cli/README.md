<h1 align="center">taiwan-logistics-skill</h1>

<h3 align="center">Taiwan Logistics Skill for AI Coding Agents</h3>

<p align="center">
  <strong>Convenience-store pickup, home delivery, store maps, cash on delivery and tracking for Taiwan logistics APIs, based on each provider's official documentation</strong>
</p>

<p align="center">
  ECPay · NewebPay · PAYUNi · SmilePay · PChomePay · PayNow · ezShip · HCT direct · Lalamove · pandago
</p>

<p align="center">
  <a href="https://www.npmjs.com/package/taiwan-logistics-skill"><img src="https://img.shields.io/npm/v/taiwan-logistics-skill?style=flat-square&logo=npm" alt="npm version"></a>
  <a href="https://www.npmjs.com/package/taiwan-logistics-skill"><img src="https://img.shields.io/npm/dm/taiwan-logistics-skill?style=flat-square&label=downloads" alt="npm downloads"></a>
  <img src="https://img.shields.io/node/v/taiwan-logistics-skill?style=flat-square&logo=node.js" alt="Node.js version">
  <img src="https://img.shields.io/badge/python-3-blue?style=flat-square&logo=python&logoColor=white" alt="Python version">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/providers-10-success?style=flat-square" alt="providers">
  <img src="https://img.shields.io/badge/AI_platforms-14-blue?style=flat-square" alt="AI platforms">
  <a href="https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/LICENSE"><img src="https://img.shields.io/github/license/Moksa1123/taiwan-ecommerce-toolkit?style=flat-square" alt="License"></a>
</p>

<p align="center">
  <a href="https://paypal.me/cccsubcom"><img src="https://img.shields.io/badge/PayPal-Support_development-00457C?style=for-the-badge&logo=paypal&logoColor=white" alt="PayPal"></a>
</p>

<p align="center">
  English | <a href="https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/taiwan-logistics/README.zh-TW.md">繁體中文</a>
</p>

This is an unofficial project. It is not affiliated with or endorsed by ECPay, NewebPay, PAYUNi, SmilePay, PChomePay, PayNow, ezShip, HCT, Lalamove, pandago, the convenience-store chains or any other company named here. Brand names are written the way each company writes them and belong to their owners.

---

## What it does

| Area | What you get |
|---|---|
| Providers | Covers 7 aggregators with a logistics API, 1 direct carrier API (HCT) and 2 on-demand delivery services (Lalamove, pandago) |
| Signing and encryption | MD5 CheckMacValue, AES-256-CBC, AES-256-GCM, 3DES, with runnable Python examples |
| Offline data | `scripts/search.py` searches 1126 rows: providers, API operations, logistics types, field mappings, shipment status codes |
| Generators | `scripts/generate-logistics-service.py` prints a service module; `scripts/recommend.py` suggests a provider from plain-language requirements |
| Shipping flows | Convenience-store pickup (7-ELEVEN, FamilyMart, Hi-Life, OK mart), home delivery, cold chain, store-map selectors, cash on delivery, tracking |

### Supported providers

| Provider | Type | Signing / auth | Runnable example | Notes |
|---|---|---|---|---|
| **ECPay** | aggregator | MD5 CheckMacValue | Python | Store pickup, T-cat and Chunghwa Post home delivery |
| **NewebPay** | aggregator | AES-256-CBC + SHA256 | Python | Store pickup only; no home delivery |
| **PAYUNi** | aggregator | AES-256-GCM + SHA256 | Python | 7-ELEVEN ambient and frozen, T-cat; shipments are created with the payment API |
| **SmilePay** | aggregator | Verify_key + Mid_smilepay check code | Python | `Pay_zg` service matrix, reverse logistics |
| **PChomePay 支付連** | aggregator | Basic Auth → pcpay-token | Python | Payment and logistics in one; pickup with payment |
| **PayNow** | aggregator | 3DES / ECB / zero padding | Python | Many product lines, incl. frozen and overseas; differs from its payment-side AES |
| **ezShip** | aggregator | No signature (bound to the `su_id` account) | Python | FamilyMart, Hi-Life, OK mart, home delivery, Hong Kong / Macau stores; no 7-ELEVEN |
| **HCT** | direct carrier API | Key issued after applying | Python | None of the aggregators above offer HCT |
| **Lalamove** | on-demand | HMAC-SHA256 signature | — | Quote first, then place the order |
| **pandago** | on-demand | OAuth 2.0 with an RSA-signed JWT assertion | — | Same-city on-demand delivery |

### Logistics type matrix

From each provider's official specification; exact parameter values are in `data/logistics-types.csv`.

| Provider | 7-ELEVEN | FamilyMart | Hi-Life | OK mart | T-cat / home | Other |
|---|---|---|---|---|---|---|
| ECPay | B2C (incl. frozen) + C2C | B2C + C2C | B2C + C2C | C2C ended 2026-07-01 | T-cat | Chunghwa Post |
| NewebPay | B2C + C2C | C2C | C2C | C2C | — | — |
| PAYUNi | B2C + C2C (ambient / frozen) | — | — | — | T-cat | — |
| SmilePay | B2C + C2C | C2C | — | — | T-cat, incl. reverse | C2B store return |
| PChomePay | Pickup with payment | Pickup with payment | Pickup with payment | — | — | — |
| PayNow | B2C + C2C (incl. frozen) | B2C + C2C (incl. frozen) | C2C | C2C | T-cat home and to-store | 7-ELEVEN overseas |
| ezShip | — | B2C + C2C | B2C + C2C | B2C + C2C | Home delivery | Hong Kong / Macau stores |
| HCT direct | — | — | — | — | HCT | — |

## When to use

| Task | Use |
|---|---|
| Build a shipping flow with convenience-store pickup or home delivery | this skill |
| Add a store-map selector to a checkout | this skill |
| Create shipments, print labels or read status callbacks | this skill |
| Look up a logistics status code, or choose a provider | this skill |
| Collect payment, including the payment side of ECPay, NewebPay or PAYUNi | [taiwan-payment](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/tree/main/taiwan-payment) |
| Issue e-invoices | [taiwan-invoice](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/tree/main/taiwan-invoice) |
| Shipping outside Taiwan, or a carrier contract with no public API | not covered (the skill says so instead of guessing) |

## Install

| Method | Command | Notes |
|---|---|---|
| Claude Code plugin | `/plugin install taiwan-ecommerce@taiwan-ecommerce-toolkit` | Installs all three Taiwan skills: invoice, payment, logistics |
| npx | `npx taiwan-logistics-skill@1.4.12 init --ai claude` | Copies the skill into the current project |
| Manual copy | `cp -r taiwan-logistics ~/.claude/skills/` | From a clone of this repository |

Claude Code plugin:

```text
/plugin marketplace add Moksa1123/taiwan-ecommerce-toolkit
/plugin install taiwan-ecommerce@taiwan-ecommerce-toolkit
```

npx (`--ai` also accepts other agents such as `cursor` or `codex`; `--global` installs into your home directory):

```bash
npx taiwan-logistics-skill@1.4.12 init --ai claude
```

Manual copy:

```bash
git clone https://github.com/Moksa1123/taiwan-ecommerce-toolkit.git
cp -r taiwan-ecommerce-toolkit/taiwan-logistics ~/.claude/skills/
```

| Requirement | Needed for |
|---|---|
| Python 3, standard library only | `scripts/` |
| `pycryptodome` (AES, 3DES), `requests` (`pip install -r requirements.txt`) | `examples/` and the network options of `scripts/test_logistics.py` |
| Node.js 18 or later | the npx installer only |
| Windows, macOS or Linux | all |

### CLI commands

| Command | What it does |
|---|---|
| `taiwan-logistics init` | Install into the current project; asks which AI agent if `--ai` is omitted |
| `taiwan-logistics init --force` | Overwrite an existing install |
| `taiwan-logistics init --global` | Install into your home directory |
| `taiwan-logistics list` | List supported AI platforms |
| `taiwan-logistics info` | Show skill information |
| `taiwan-logistics versions` | List available versions |
| `taiwan-logistics update` | Update to the latest version |

The installer supports 14 AI coding agents: Claude Code · Cursor · Windsurf · Antigravity · GitHub Copilot · Kiro · Codex · Qoder · Cline · Gemini CLI · Trae · OpenCode · Continue · CodeBuddy.

## Quick start

**Step 1.** Install into your project:

```bash
npx taiwan-logistics-skill@1.4.12 init --ai claude
```

**Step 2.** Ask Claude, for example:

```text
Add ECPay convenience-store pickup with a store map to my checkout, in Python.
Create a PAYUNi home-delivery shipment and download the label.
What does ECPay logistics status 2073 mean?
```

**Step 3.** Or search the data yourself from the skill folder:

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

| Check | Result |
|---|---|
| Data source | Official provider API documentation, PDF specifications and SDKs. Every source is registered in [`sources/official-sources.json`](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/sources/official-sources.json); each data row carries `doc_url` and `trust` |
| Official-docs audit | Last run 2026-11-17, recorded in [`references/audit-20261117.md`](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/taiwan-logistics/references/audit-20261117.md) |
| Self-test | `python3 scripts/test_skill.py` runs 42 checks, 0 failures (run on 2026-11-17) |
| Evals | On the 11 scored questions, Claude answered 11 correctly with the skill and 0 without it. See [`evals/RESULTS.md`](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/taiwan-logistics/evals/RESULTS.md) |
| Example code | CI runs `scripts/verify-examples.py`, which compares the examples byte for byte with expected values from the providers' own SDKs and spec samples ([`tests/vectors/`](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/tree/main/tests/vectors)) |

## Limits

| Limit | Details |
|---|---|
| Carriers without a public API | Convenience-store chains, T-cat, Chunghwa Post and others are listed only so Claude can say so; reach them through an aggregator |
| No runnable example | Lalamove and pandago have references only |
| HCT | Documentation is available only after applying to HCT |
| Test script | `test_logistics.py --create` and `--query` work with ECPay only; NewebPay and PAYUNi need your own merchant account |
| Known gaps | Tracked in [`data/pending.csv`](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/taiwan-logistics/data/pending.csv) |

## Repo layout

```text
taiwan-logistics/
├── SKILL.md         # instructions Claude reads
├── EXAMPLES.md      # longer code examples
├── references/      # one API reference per provider, on-demand overview, audit log
├── examples/        # runnable Python clients and a store-map page
├── data/            # CSV data for search.py and recommend.py; pending.csv
├── scripts/         # search, recommend, generator, tests, number check
└── evals/           # eval questions, grader and results
```

| Reference file | Covers |
|---|---|
| `ecpay-`, `payuni-`, `smilepay-`, `pchomepay-`, `paynow-`, `ezship-logistics-api.md`, `NEWEBPAY_LOGISTICS_REFERENCE.md` | The aggregators |
| `hct-logistics-api.md` | HCT direct carrier API |
| `lalamove-logistics-api.md`, `ondemand-delivery.md` | Lalamove and pandago |
| `carrier-direct-access.md` | Carriers with no public API, and the alternatives |
| `implementation-guide.md` | Cross-provider implementation notes |
| `audit-20261117.md` | Latest official-docs audit |

## License & author

MIT License ([LICENSE](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/LICENSE)). Made by Moksa ([moksaweb.com](https://moksaweb.com)).

This package is part of [Taiwan E-commerce Toolkit](https://github.com/Moksa1123/taiwan-ecommerce-toolkit):

| Package | Covers |
|---|---|
| [taiwan-invoice-skill](https://www.npmjs.com/package/taiwan-invoice-skill) | Taiwan e-invoice providers and MOF platform queries |
| [taiwan-payment-skill](https://www.npmjs.com/package/taiwan-payment-skill) | Taiwan payment gateways |
