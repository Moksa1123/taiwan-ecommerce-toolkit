# taiwan-invoice

A Claude skill for integrating Taiwan e-invoice (電子發票) APIs: issuing, voiding, allowances, printing, and carrier and donation code checks, based on each provider's official documentation.

[![npm version](https://img.shields.io/npm/v/taiwan-invoice-skill)](https://www.npmjs.com/package/taiwan-invoice-skill)
[![License: MIT](https://img.shields.io/github/license/Moksa1123/taiwan-ecommerce-toolkit)](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/LICENSE)

English | [繁體中文](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/taiwan-invoice/README.zh-TW.md)

This is an unofficial project. It is not affiliated with or endorsed by ECPay, SmilePay, Amego, ezPay, PayNow, O'Pay, SunPay, the Ministry of Finance or any other organization named here. Brand names are written the way each company writes them and belong to their owners.

## What it does

- Covers 7 e-invoice value-added service providers that can issue invoices (ECPay, SmilePay, Amego, ezPay, PayNow, O'Pay, SunPay), plus the Ministry of Finance (MOF) E-Invoice platform for queries.
- Gives Claude each provider's request format and encryption (AES-128-CBC, AES-256-CBC, MD5, JWT) with runnable Python examples.
- Searches 424 rows of data offline with `scripts/search.py`: error codes, API operations, field mappings, tax rules, troubleshooting notes and selection advice.
- Generates a service skeleton for a provider (`scripts/generate-invoice-service.py`) and suggests a provider from plain-language requirements (`scripts/recommend.py`).
- Covers B2C and B2B invoices, void, allowance, printing, mobile barcode carriers, donation codes and POS batch number allocation.

## When to use

Use it when you are:

- issuing B2C or B2B e-invoices through one of the providers above;
- voiding an invoice or issuing an allowance;
- validating a mobile barcode, citizen certificate carrier or donation code;
- looking up what a provider's error code means, or choosing a provider.

Use something else for:

- collecting payment (credit card, ATM, CVS code, LINE Pay): use [taiwan-payment](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/tree/main/taiwan-payment);
- shipping, convenience-store pickup or tracking: use [taiwan-logistics](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/tree/main/taiwan-logistics);
- invoices outside Taiwan, or uploading directly to the MOF platform as your own value-added center: not covered.

## Install

Requirements: Python 3 for the scripts, which use only the standard library. The files in `examples/` also need `pycryptodome` (AES) and `requests`; install them with `pip install -r requirements.txt`. Node.js 18 or later is needed only for the npx installer. Works on Windows, macOS and Linux.

Claude Code plugin (installs all three Taiwan skills: invoice, payment, logistics):

```text
/plugin marketplace add Moksa1123/taiwan-ecommerce-toolkit
/plugin install taiwan-ecommerce@taiwan-ecommerce-toolkit
```

npx (copies the skill into the current project; `--ai` also accepts other agents such as `cursor` or `codex`, `--global` installs into your home directory):

```bash
npx taiwan-invoice-skill@2.9.12 init --ai claude
```

Manual copy:

```bash
git clone https://github.com/Moksa1123/taiwan-ecommerce-toolkit.git
cp -r taiwan-ecommerce-toolkit/taiwan-invoice ~/.claude/skills/
```

## Quick start

Ask Claude, for example:

- "Issue a B2C invoice with a mobile barcode carrier through the ECPay sandbox, in Python."
- "Create a B2B invoice on ezPay with a buyer tax ID and tax-exclusive amounts."
- "What does Amego error code 3050131 mean?"

Or search the data yourself from the skill folder:

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

- Data source: official provider API documentation, PDF specifications, official SDKs and the MOF E-Invoice platform specification. Every source is registered in [`sources/official-sources.json`](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/sources/official-sources.json), and each data row carries `doc_url` and `trust`.
- Self-test: `python3 scripts/test_skill.py` runs 51 checks, 0 failures (run on 2026-11-17).
- Evals: on the 12 scored questions, Claude answered 12 correctly with the skill and 0 without it. See [`evals/RESULTS.md`](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/taiwan-invoice/evals/RESULTS.md).
- CI runs `scripts/verify-examples.py`, which compares the example code byte for byte with expected values produced by the providers' own SDKs and spec samples ([`tests/vectors/`](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/tree/main/tests/vectors)).

## Limits

- SmilePay and Amego have no runnable example; see `EXAMPLES.md` and their reference files.
- The MOF platform is query-only (carriers, donation codes, winning numbers). It cannot issue invoices.
- TradeVAN is listed in `data/providers.csv` but has no reference file yet.
- Tax formulas in `data/tax-rules.csv` and the general troubleshooting rules are inferred (`trust=推論`), not yet tied to an official clause. Treat them as advice.
- Known gaps are tracked in [`data/pending.csv`](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/taiwan-invoice/data/pending.csv).

## Repo layout

```text
taiwan-invoice/
├── SKILL.md         # instructions Claude reads
├── EXAMPLES.md      # longer code examples
├── references/      # one API reference per provider, MOF platform, landscape
├── examples/        # runnable Python clients
├── data/            # CSV data for search.py and recommend.py; pending.csv
├── scripts/         # search, recommend, generators, tests, number check
└── evals/           # eval questions, grader and results
```

## License & author

MIT License. Made by Moksa ([moksaweb.com](https://moksaweb.com)). Part of [Taiwan E-commerce Toolkit](https://github.com/Moksa1123/taiwan-ecommerce-toolkit).
