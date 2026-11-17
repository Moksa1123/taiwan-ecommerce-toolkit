# Taiwan E-commerce Toolkit

Agent skills for integrating Taiwan e-invoice, payment gateway and logistics APIs, built from each provider's official documentation.

[![License: MIT](https://img.shields.io/github/license/Moksa1123/taiwan-ecommerce-toolkit?style=flat-square)](LICENSE)
[![npm taiwan-invoice-skill](https://img.shields.io/npm/v/taiwan-invoice-skill?style=flat-square&label=taiwan-invoice-skill)](https://www.npmjs.com/package/taiwan-invoice-skill)
[![npm taiwan-payment-skill](https://img.shields.io/npm/v/taiwan-payment-skill?style=flat-square&label=taiwan-payment-skill)](https://www.npmjs.com/package/taiwan-payment-skill)
[![npm taiwan-logistics-skill](https://img.shields.io/npm/v/taiwan-logistics-skill?style=flat-square&label=taiwan-logistics-skill)](https://www.npmjs.com/package/taiwan-logistics-skill)

[正體中文](README.zh-TW.md)

> This is an unofficial community project. It is not affiliated with, endorsed by, or sponsored by ECPay, NewebPay, PAYUNi, LINE, TapPay, JKOPAY, or any other company named here. Product names belong to their owners.

## What it does

The repository is one Claude plugin (`taiwan-ecommerce`) that bundles three skills. Each skill teaches the assistant how a provider's API really works and ships local tools to look things up.

- **taiwan-invoice**: issue, void and allowance flows for Taiwan e-invoices (ECPay, SmilePay, Amego, ezPay, PayNow, O'Pay, SunPay), plus Ministry of Finance platform queries for carriers and donation codes.
- **taiwan-payment**: payment gateways and wallets (ECPay, NewebPay, PAYUNi, SmilePay, PChomePay, ezPay, PayNow, SHOPLINE Payments, LINE Pay, TapPay, O'Pay, JKOPAY, SunPay, GoMyPay): checkout, notifications, refunds, signatures.
- **taiwan-logistics**: convenience-store pickup, home delivery, cold chain, store maps and on-demand delivery through aggregators and direct carrier APIs.
- Each skill has searchable CSV data (endpoints, fields, error codes), runnable examples checked against the providers' official test vectors, and a record of what still needs confirming.

## When to use

Use it when you are writing or debugging code that talks to a Taiwan e-invoice, payment or logistics provider: building a checkout, verifying `CheckMacValue` or `TradeSha`, handling payment notifications, issuing or voiding invoices, creating shipments or looking up an error code.

Do not use it for general accounting, tax filing, or providers outside Taiwan. It does not replace the provider's merchant contract or production credentials, which you obtain from the provider.

## Install

Claude plugin (Claude Code; also listed in the Claude directory once approved):

```
/plugin marketplace add Moksa1123/taiwan-ecommerce-toolkit
/plugin install taiwan-ecommerce@taiwan-ecommerce-toolkit
```

npx, for other AI coding tools or a single skill (pin the version you want; see the npm badges above):

```bash
npx taiwan-payment-skill@1.5.14 init
```

Manual copy: put one or more skill folders where your assistant loads skills, for example:

```bash
git clone https://github.com/Moksa1123/taiwan-ecommerce-toolkit.git
cp -r taiwan-ecommerce-toolkit/taiwan-payment ~/.claude/skills/
```

Requirements: Python 3 for the bundled scripts (standard library only). The AES examples need `pycryptodome`. Node.js 18 or later only for the npx installer. Works on Windows, macOS and Linux.

## Quick start

Ask the assistant, for example:

- "Build an ECPay credit-card checkout in Python and verify the payment notification."
- "NewebPay returned MPG03009. What is wrong?"
- "Which provider should I use for cold-chain convenience-store pickup?"

Or search the data directly:

```bash
python3 taiwan-payment/scripts/search.py "MPG03009" --domain error
```

Each skill's README shows the expected output and more commands.

## Trigger phrases

English: Taiwan e-invoice, ECPay, NewebPay, PAYUNi, LINE Pay, TapPay, CheckMacValue, payment notification, convenience-store pickup, store map, cold-chain delivery.

中文：電子發票、開立發票、載具、金流串接、綠界、藍新、統一金流、付款通知、超商取貨、電子地圖選店、宅配、物流狀態碼。

## What it runs and connects to

- **Nothing runs on its own.** The plugin has no hooks, MCP servers or background processes. Scripts run only when you or the assistant call them.
- **Offline scripts** (read local CSV and templates, no network): `search.py`, `recommend.py`, `check_numbers.py`, `test_skill.py` and the service generators in each skill. `persist.py` (invoice) writes a settings file only in the directory you choose.
- **Optional network tests**: `taiwan-payment/scripts/test_payment.py` and `taiwan-logistics/scripts/test_logistics.py` are offline by default (known-answer tests). Only with `--live`, `--create` or `--query` do they send requests, and only to the providers' test environments: `payment-stage.ecpay.com.tw`, `ccore.newebpay.com`, `sandbox-api.payuni.com.tw`, `logistics-stage.ecpay.com.tw`.
- **Examples** in `examples/` call the provider you choose when you run them in your own project.
- **Credentials**: you supply your own merchant ID and keys (for example HashKey and HashIV) through environment variables or your own config. The repository contains no real credentials; the test values in the docs are the providers' public sandbox accounts.
- **Maintainer tooling** (not used by the skills): `scripts/check-sources.py` downloads the official documents listed in `sources/official-sources.json` to detect changes; a weekly GitHub Action runs it.
- No data is collected or sent to the author.

## How it's verified

- Every endpoint, field and error code traces to an official source registered in [`sources/official-sources.json`](sources/official-sources.json); unsourced claims are removed or listed as pending.
- A weekly job re-downloads those sources and opens an issue when one changes.
- Signature and encryption code is checked byte for byte against the providers' official examples ([`tests/vectors/`](tests/vectors/)) by `scripts/verify-examples.py` in CI.
- Each skill has a self-test (`scripts/test_skill.py`) and evals with results in `evals/RESULTS.md`.
- Latest payment audit: [`taiwan-payment/references/audit-20261117.md`](taiwan-payment/references/audit-20261117.md).

## Limits

- Some provider specs are available only to contracted merchants (for example SmilePay and GoMyPay); those parts are marked and not guessed.
- JKOPAY's public documentation site is currently unreachable; that reference reflects the last official copy.
- Logistics carriers without a merchant API (for example Black Cat, Chunghwa Post) are listed only with the aggregator route.
- Open questions per skill: [`invoice`](taiwan-invoice/data/pending.csv), [`payment`](taiwan-payment/data/pending.csv), [`logistics`](taiwan-logistics/data/pending.csv).

More background (supported AI tools, CLI commands, FAQ, algorithms) in Chinese: [`docs/guide.zh-TW.md`](docs/guide.zh-TW.md).

## Repo layout

```
.claude-plugin/       plugin and marketplace manifests
taiwan-invoice/       e-invoice skill (SKILL.md, references, data, scripts, examples)
taiwan-payment/       payment skill
taiwan-logistics/     logistics skill
invoice-cli/ payment-cli/ logistics-cli/   npm installers
sources/              official source registry and change baseline
scripts/              maintainer checks (data, examples, sources)
tests/vectors/        official test vectors
docs/                 longer guides
```

## License & author

MIT License. Made by Moksa ([moksaweb.com](https://moksaweb.com)). Issues and pull requests: see [CONTRIBUTING.md](CONTRIBUTING.md).
