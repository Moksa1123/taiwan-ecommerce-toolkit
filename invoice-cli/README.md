<h1 align="center">taiwan-invoice-skill</h1>

<h3 align="center">Taiwan E-Invoice Skill for AI Coding Agents</h3>

<p align="center">
  <strong>Issue, void, adjust and print Taiwan e-invoices (電子發票), based on each provider's official documentation</strong>
</p>

<p align="center">
  ECPay · SmilePay · Amego · ezPay · PayNow · O'Pay · SunPay · MOF E-Invoice platform
</p>

<p align="center">
  <a href="https://www.npmjs.com/package/taiwan-invoice-skill"><img src="https://img.shields.io/npm/v/taiwan-invoice-skill?style=flat-square&logo=npm" alt="npm version"></a>
  <a href="https://www.npmjs.com/package/taiwan-invoice-skill"><img src="https://img.shields.io/npm/dm/taiwan-invoice-skill?style=flat-square&label=downloads" alt="npm downloads"></a>
  <img src="https://img.shields.io/node/v/taiwan-invoice-skill?style=flat-square&logo=node.js" alt="Node.js version">
  <img src="https://img.shields.io/badge/python-3-blue?style=flat-square&logo=python&logoColor=white" alt="Python version">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/providers-9-success?style=flat-square" alt="providers">
  <img src="https://img.shields.io/badge/AI_platforms-14-blue?style=flat-square" alt="AI platforms">
  <a href="https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/LICENSE"><img src="https://img.shields.io/github/license/Moksa1123/taiwan-ecommerce-toolkit?style=flat-square" alt="License"></a>
</p>

<p align="center">
  <a href="https://paypal.me/cccsubcom"><img src="https://img.shields.io/badge/PayPal-Support_development-00457C?style=for-the-badge&logo=paypal&logoColor=white" alt="PayPal"></a>
</p>

<p align="center">
  English | <a href="https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/taiwan-invoice/README.zh-TW.md">繁體中文</a>
</p>

This is an unofficial project. It is not affiliated with or endorsed by ECPay, SmilePay, Amego, ezPay, PayNow, O'Pay, SunPay, the Ministry of Finance or any other organization named here. Brand names are written the way each company writes them and belong to their owners.

---

## What it does

| Area | What you get |
|---|---|
| Providers | 7 e-invoice value-added service providers that can issue invoices, plus the Ministry of Finance (MOF) E-Invoice platform for queries |
| Encryption | Each provider's request format and encryption (AES-128-CBC, AES-256-CBC, MD5, JWT), with runnable Python examples |
| Offline data | `scripts/search.py` searches 424 rows: error codes, API operations, field mappings, tax rules, troubleshooting notes, selection advice |
| Generators | `scripts/generate-invoice-service.py` writes a service skeleton; `scripts/recommend.py` suggests a provider from plain-language requirements |
| Invoice flows | B2C and B2B invoices, void, allowance, printing, mobile barcode carriers, donation codes, POS batch number allocation |

### Supported providers

| Provider | Auth / encryption | Runnable example | Notes |
|---|---|---|---|
| **ECPay** | AES-128-CBC + HashKey/HashIV | Python | Full documentation and official SDK |
| **SmilePay** | Grvc + Verify_key | See `EXAMPLES.md` | No AES; plain parameters |
| **Amego** | MD5 signature + App Key | See `EXAMPLES.md` | MIG 4.0 format, REST API |
| **ezPay** | AES-256-CBC + SHA256 CheckCode | Python | Invoice number track management, batch issuing |
| **PayNow** | JWT Bearer token | Python | POS batch number allocation |
| **O'Pay** | MerchantID + RqHeader + AES-encrypted Data | Python | Same API design as the ECPay invoice API |
| **SunPay** | AES-128-CBC on the Token field | Python | Can issue together with SunPay payments |
| **MOF E-Invoice platform** | AppID + API key, HMAC-SHA256 signature | — | Query and validation only (carriers, donation codes, winning numbers); cannot issue |
| **TradeVAN** | — | — | Listed in `data/providers.csv` only; no reference file yet |

Encryption in the runnable examples is checked against the providers' official test vectors.

## When to use

| Task | Use |
|---|---|
| Issue B2C or B2B e-invoices through one of the providers above | this skill |
| Void an invoice or issue an allowance | this skill |
| Validate a mobile barcode, citizen certificate carrier or donation code | this skill |
| Look up a provider's error code, or choose a provider | this skill |
| Collect payment (credit card, ATM, CVS code, LINE Pay) | [taiwan-payment](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/tree/main/taiwan-payment) |
| Shipping, convenience-store pickup, tracking | [taiwan-logistics](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/tree/main/taiwan-logistics) |
| Invoices outside Taiwan, or uploading to the MOF platform as your own value-added center | not covered |

## Install

| Method | Command | Notes |
|---|---|---|
| Claude Code plugin | `/plugin install taiwan-ecommerce@taiwan-ecommerce-toolkit` | Installs all three Taiwan skills: invoice, payment, logistics |
| npx | `npx taiwan-invoice-skill@2.9.12 init --ai claude` | Copies the skill into the current project |
| Manual copy | `cp -r taiwan-invoice ~/.claude/skills/` | From a clone of this repository |

Claude Code plugin:

```text
/plugin marketplace add Moksa1123/taiwan-ecommerce-toolkit
/plugin install taiwan-ecommerce@taiwan-ecommerce-toolkit
```

npx (`--ai` also accepts other agents such as `cursor` or `codex`; `--global` installs into your home directory):

```bash
npx taiwan-invoice-skill@2.9.12 init --ai claude
```

Manual copy:

```bash
git clone https://github.com/Moksa1123/taiwan-ecommerce-toolkit.git
cp -r taiwan-ecommerce-toolkit/taiwan-invoice ~/.claude/skills/
```

| Requirement | Needed for |
|---|---|
| Python 3, standard library only | `scripts/` |
| `pycryptodome`, `requests` (`pip install -r requirements.txt`) | `examples/` |
| Node.js 18 or later | the npx installer only |
| Windows, macOS or Linux | all |

### CLI commands

| Command | What it does |
|---|---|
| `taiwan-invoice init` | Install into the current project; asks which AI agent if `--ai` is omitted |
| `taiwan-invoice init --force` | Overwrite an existing install |
| `taiwan-invoice init --global` | Install into your home directory |
| `taiwan-invoice list` | List supported AI platforms |
| `taiwan-invoice info` | Show skill information |
| `taiwan-invoice versions` | List available versions |
| `taiwan-invoice update` | Update to the latest version |

The installer supports 14 AI coding agents: Claude Code · Cursor · Windsurf · Antigravity · GitHub Copilot · Kiro · Codex · Qoder · Cline · Gemini CLI · Trae · OpenCode · Continue · CodeBuddy.

## Quick start

**Step 1.** Install into your project:

```bash
npx taiwan-invoice-skill@2.9.12 init --ai claude
```

**Step 2.** Ask Claude, for example:

```text
Issue a B2C invoice with a mobile barcode carrier through the ECPay sandbox, in Python.
Create a B2B invoice on ezPay with a buyer tax ID and tax-exclusive amounts.
What does Amego error code 3050131 mean?
```

**Step 3.** Or search the data yourself from the skill folder:

```bash
python3 scripts/search.py "4000004" --domain error -n 1 -f simple
```

Expected output (shortened):

```text
[1] Score: 7.1404
  provider: ECPay
  code: 4000004
  message_zh: 開立發票成功（觸發開立，DelayDay=0）
  category: 延後開立
  solution: 觸發開立 API 的成功碼不是 1：DelayDay>0 回 4000003、DelayDay=0 回 4000004，...
  doc_url: https://developers.ecpay.com.tw/
  trust: 官方文件
```

## Trigger phrases

English: Taiwan e-invoice, ECPay invoice, B2C invoice, B2B invoice, issue invoice, void invoice, allowance, mobile barcode carrier, donation code, buyer tax ID, MOF e-invoice platform, invoice printing.

中文：電子發票串接、開立發票、作廢、折讓、載具、手機條碼、捐贈碼、統編、B2B 三聯式、B2C 二聯式、加值中心、財政部大平台、發票列印。

## What it runs and connects to

The skill is Markdown documentation, CSV data and local Python scripts. It never sends data anywhere on its own. Network calls happen only when you run an example file.

| Script | What it does | Network | Files written |
|---|---|---|---|
| `scripts/search.py` | Searches `data/*.csv` | None | None |
| `scripts/recommend.py` | Suggests a provider from `data/*.csv` | None | None |
| `scripts/generate-invoice-service.py` | Writes a TypeScript or Python service skeleton for a provider | None | One source file in the `--output` folder (default: current folder) |
| `scripts/persist.py` | Saves the project's invoice settings for later sessions | None | `invoice-config/MASTER.md` under `--dir` (default: current folder) |
| `scripts/error_handler.py` | Retry and error-classification helpers to import in your code | None | None |
| `scripts/check_numbers.py` | Checks that every number in `SKILL.md` and these READMEs matches the data | None | With `--fix`, those three files |
| `scripts/test_skill.py` and other `test_*.py` | Self-tests, offline | None | None |
| `examples/*.py` | Reference clients for each provider | When run directly, calls the sandbox or production host defined at the top of that file | None |

Credentials (merchant ID, HashKey and HashIV, App Key, API tokens, MOF AppID and API key) are supplied by you in your own code or configuration, for example environment variables. The repository stores no real credentials. Test values that appear in the docs and scripts are the providers' published sandbox values.

## How it's verified

| Check | Result |
|---|---|
| Data source | Official provider API documentation, PDF specifications, official SDKs and the MOF E-Invoice platform specification. Every source is registered in [`sources/official-sources.json`](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/sources/official-sources.json); each data row carries `doc_url` and `trust` |
| Official-docs audit | Last run 2026-11-17, recorded in [`references/audit-20261117.md`](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/taiwan-invoice/references/audit-20261117.md) |
| Self-test | `python3 scripts/test_skill.py` runs 51 checks, 0 failures (run on 2026-11-17) |
| Evals | On the 12 scored questions, Claude answered 12 correctly with the skill and 0 without it. See [`evals/RESULTS.md`](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/taiwan-invoice/evals/RESULTS.md) |
| Example code | CI runs `scripts/verify-examples.py`, which compares the examples byte for byte with expected values from the providers' own SDKs and spec samples ([`tests/vectors/`](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/tree/main/tests/vectors)) |

## Limits

| Limit | Details |
|---|---|
| No runnable example | SmilePay and Amego; see `EXAMPLES.md` and their reference files |
| MOF platform | Query only (carriers, donation codes, winning numbers); it cannot issue invoices |
| TradeVAN | Listed in `data/providers.csv`, no reference file yet |
| Inferred rows | Tax formulas in `data/tax-rules.csv` and the general troubleshooting rules are inferred (`trust=推論`), not yet tied to an official clause; treat them as advice |
| Known gaps | Tracked in [`data/pending.csv`](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/taiwan-invoice/data/pending.csv) |

## Repo layout

```text
taiwan-invoice/
├── SKILL.md         # instructions Claude reads
├── EXAMPLES.md      # longer code examples
├── references/      # one API reference per provider, MOF platform, landscape, audit log
├── examples/        # runnable Python clients
├── data/            # CSV data for search.py and recommend.py; pending.csv
├── scripts/         # search, recommend, generators, tests, number check
└── evals/           # eval questions, grader and results
```

| Reference file | Covers |
|---|---|
| `ECPAY_API_REFERENCE.md`, `SMILEPAY_API_REFERENCE.md`, `AMEGO_API_REFERENCE.md`, `EZPAY_API_REFERENCE.md` | ECPay, SmilePay, Amego, ezPay |
| `PAYNOW_API_REFERENCE.md`, `OPAY_API_REFERENCE.md`, `SUNPAY_API_REFERENCE.md` | PayNow, O'Pay, SunPay |
| `MOF_EINVOICE_API_REFERENCE.md` | MOF E-Invoice platform (queries) |
| `VAC_LANDSCAPE.md` | Value-added center landscape |
| `audit-20261117.md` | Latest official-docs audit |

## License & author

MIT License ([LICENSE](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/LICENSE)). Made by Moksa ([moksaweb.com](https://moksaweb.com)).

This package is part of [Taiwan E-commerce Toolkit](https://github.com/Moksa1123/taiwan-ecommerce-toolkit):

| Package | Covers |
|---|---|
| [taiwan-payment-skill](https://www.npmjs.com/package/taiwan-payment-skill) | Taiwan payment gateways |
| [taiwan-logistics-skill](https://www.npmjs.com/package/taiwan-logistics-skill) | Taiwan logistics aggregators, HCT direct API, on-demand delivery |
