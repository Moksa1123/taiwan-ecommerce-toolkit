# taiwan-payment

A Claude skill for integrating Taiwan payment gateways: request signing, encryption, payment callbacks, refunds and error codes, based on each provider's official documentation.

[![npm version](https://img.shields.io/npm/v/taiwan-payment-skill)](https://www.npmjs.com/package/taiwan-payment-skill)
[![License: MIT](https://img.shields.io/github/license/Moksa1123/taiwan-ecommerce-toolkit)](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/LICENSE)

English | [繁體中文](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/taiwan-payment/README.zh-TW.md)

This is an unofficial project. It is not affiliated with or endorsed by ECPay, NewebPay, PAYUNi, LINE, TapPay, JKOPAY or any other company named here. Brand names are written the way each company writes them and belong to their owners.

## What it does

- Covers 14 Taiwan payment providers: ECPay, NewebPay, PAYUNi, SmilePay, PChomePay, ezPay, PayNow, Shopline Payments, LINE Pay v4, TapPay, O'Pay, JKOPAY, SunPay and GoMyPay.
- Gives Claude each provider's signing and encryption rules (CheckMacValue, TradeSha, AES-256-CBC, AES-256-GCM, RSA, JWT, HMAC-SHA256) with runnable Python examples.
- Searches 3212 rows of official data offline with `scripts/search.py`: error codes, API operations, field mappings, payment methods and troubleshooting notes.
- Suggests a provider from plain-language requirements with `scripts/recommend.py`.
- Links each task (credit card, ATM, CVS code, e-wallet, Apple Pay, Google Pay, TWQR, BNPL, recurring billing, refunds) to the right reference file in `references/`.

## When to use

Use it when you are:

- building or debugging a checkout that talks to one of the providers above;
- verifying a payment notification (CheckMacValue, TradeSha, HashInfo, webhook signatures);
- looking up what a provider's error or status code means;
- choosing between providers for a project.

Use something else for:

- issuing, voiding or adjusting e-invoices: use [taiwan-invoice](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/tree/main/taiwan-invoice);
- shipping, convenience-store pickup, store maps or tracking, even with ECPay, NewebPay or PAYUNi: use [taiwan-logistics](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/tree/main/taiwan-logistics);
- payment providers outside Taiwan, or direct bank and card-network integrations: not covered.

## Install

Requirements: Python 3 for the scripts, which use only the standard library. The files in `examples/` and the network options of `scripts/test_payment.py` also need `pycryptodome` (AES) and `requests`; install them with `pip install -r requirements.txt`. Node.js 18 or later is needed only for the npx installer. Works on Windows, macOS and Linux.

Claude Code plugin (installs all three Taiwan skills: invoice, payment, logistics):

```text
/plugin marketplace add Moksa1123/taiwan-ecommerce-toolkit
/plugin install taiwan-ecommerce@taiwan-ecommerce-toolkit
```

npx (copies the skill into the current project; `--ai` also accepts other agents such as `cursor` or `codex`, `--global` installs into your home directory):

```bash
npx taiwan-payment-skill@1.5.15 init --ai claude
```

Manual copy:

```bash
git clone https://github.com/Moksa1123/taiwan-ecommerce-toolkit.git
cp -r taiwan-ecommerce-toolkit/taiwan-payment ~/.claude/skills/
```

## Quick start

Ask Claude, for example:

- "Create an ECPay credit-card order in Python and verify the payment notification."
- "My NewebPay TradeInfo fails to decrypt. What is wrong with my padding?"
- "Which provider should I use for LINE Pay plus recurring card payments?"

Or search the data yourself from the skill folder:

```bash
python3 scripts/search.py "10100058" --domain error --max 1
```

Expected output (shortened):

```text
搜索域: error
找到 1 筆結果
[結果 #1] 評分: 6.04
Provider            : ecpay
Code                : 10100058
Message Zh          : Pay fail（3D 驗證未完成）
Solution            : 請消費者更換瀏覽器或裝置、關閉 VPN、切換網路取得新 IP；...
Doc Url             : https://developers.ecpay.com.tw/
Trust               : 官方文件
```

## Trigger phrases

English: Taiwan payment gateway, ECPay, NewebPay, PAYUNi, LINE Pay, TapPay, JKOPAY, credit card payment, ATM virtual account, CVS payment code, Apple Pay, Google Pay, TWQR, BNPL, CheckMacValue, payment notification, refund, recurring payment.

中文：金流串接、綠界、藍新、統一金流、信用卡付款、ATM 虛擬帳號、超商代碼、LINE Pay、Apple Pay、街口、CheckMacValue、TradeSha、付款通知、退款、定期定額。

## What it runs and connects to

The skill is Markdown documentation, CSV data and local Python scripts. It never sends data anywhere on its own. Network calls happen only when you run a connectivity option of the test script or run an example file.

| Script | What it does | Network | Files written |
|---|---|---|---|
| `scripts/search.py` | Searches `data/*.csv` | None | None |
| `scripts/recommend.py` | Suggests a provider from `data/*.csv` | None | None |
| `scripts/test_payment.py` | Known-answer tests of ECPay, NewebPay and PAYUNi signing; offline by default | `--live`: HEAD request to the sandbox of ECPay (`payment-stage.ecpay.com.tw`), NewebPay (`ccore.newebpay.com`) and PAYUNi (`sandbox-api.payuni.com.tw`). `--query`: POST to the ECPay sandbox order query | `--create`: an `ecpay_test_<order>.html` form in the current folder |
| `scripts/check_numbers.py` | Checks that every number in `SKILL.md` and these READMEs matches the data | None | With `--fix`, those three files |
| `scripts/test_skill.py` | Self-test; runs the checks above offline | None | None |
| `examples/*.py` | Reference clients for each provider | When run directly, calls the sandbox or production host defined at the top of that file | None |

Credentials (merchant ID, HashKey and HashIV, LINE Pay Channel ID and Channel Secret, TapPay Partner Key, API keys) are supplied by you in your own code or configuration, for example environment variables. The repository stores no real credentials. Test values that appear in the docs and scripts are the providers' published sandbox values.

## How it's verified

- Data source: official provider documentation, PDF specifications and official SDKs or plugins. Every source is registered in [`sources/official-sources.json`](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/sources/official-sources.json), and each data row carries `doc_url` and `trust`.
- Last audit against the official docs: 2026-11-17, recorded in [`references/audit-20261117.md`](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/taiwan-payment/references/audit-20261117.md).
- Self-test: `python3 scripts/test_skill.py` runs 50 checks, 0 failures (run on 2026-11-17).
- Evals: on the 10 scored questions, Claude answered 10 correctly with the skill and 0 without it. See [`evals/RESULTS.md`](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/taiwan-payment/evals/RESULTS.md).
- CI runs `scripts/verify-examples.py`, which compares the example code byte for byte with expected values produced by the providers' own SDKs and spec samples ([`tests/vectors/`](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/tree/main/tests/vectors)).

## Limits

- O'Pay and GoMyPay have no runnable example. The full GoMyPay API specification is not public; you have to request it from GoMyPay.
- The JKOPAY documentation site did not resolve during the latest audit, so the JKOPAY reference is based on the last saved copy of the official pages.
- Known gaps and unanswered questions are tracked in [`data/pending.csv`](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/taiwan-payment/data/pending.csv).
- Rows marked `trust=推論` (recommendations, troubleshooting) are inferred from the official docs. Treat them as advice, not as provider rules.

## Repo layout

```text
taiwan-payment/
├── SKILL.md         # instructions Claude reads
├── EXAMPLES.md      # longer code examples
├── references/      # one API reference per provider, plus the audit log
├── examples/        # runnable Python clients
├── data/            # CSV data for search.py and recommend.py; pending.csv
├── scripts/         # search, recommend, tests, number check
└── evals/           # eval questions, grader and results
```

## License & author

MIT License. Made by Moksa ([moksaweb.com](https://moksaweb.com)). Part of [Taiwan E-commerce Toolkit](https://github.com/Moksa1123/taiwan-ecommerce-toolkit).
