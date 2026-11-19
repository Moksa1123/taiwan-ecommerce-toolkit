<h1 align="center">taiwan-payment-skill</h1>

<h3 align="center">Taiwan Payment Gateway Skill for AI Coding Agents</h3>

<p align="center">
  <strong>Request signing, encryption, payment callbacks, refunds and error codes for Taiwan payment gateways, based on each provider's official documentation</strong>
</p>

<p align="center">
  ECPay · NewebPay · PAYUNi · SmilePay · PChomePay · ezPay · PayNow · Shopline Payments · LINE Pay · TapPay · O'Pay · JKOPAY · SunPay · GoMyPay
</p>

<p align="center">
  <a href="https://www.npmjs.com/package/taiwan-payment-skill"><img src="https://img.shields.io/npm/v/taiwan-payment-skill?style=flat-square&logo=npm" alt="npm version"></a>
  <a href="https://www.npmjs.com/package/taiwan-payment-skill"><img src="https://img.shields.io/npm/dm/taiwan-payment-skill?style=flat-square&label=downloads" alt="npm downloads"></a>
  <img src="https://img.shields.io/node/v/taiwan-payment-skill?style=flat-square&logo=node.js" alt="Node.js version">
  <img src="https://img.shields.io/badge/python-3-blue?style=flat-square&logo=python&logoColor=white" alt="Python version">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/providers-14-success?style=flat-square" alt="providers">
  <img src="https://img.shields.io/badge/AI_platforms-14-blue?style=flat-square" alt="AI platforms">
  <a href="https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/LICENSE"><img src="https://img.shields.io/github/license/Moksa1123/taiwan-ecommerce-toolkit?style=flat-square" alt="License"></a>
</p>

<p align="center">
  <a href="https://paypal.me/cccsubcom"><img src="https://img.shields.io/badge/PayPal-Support_development-00457C?style=for-the-badge&logo=paypal&logoColor=white" alt="PayPal"></a>
</p>

<p align="center">
  English | <a href="https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/taiwan-payment/README.zh-TW.md">繁體中文</a>
</p>

This is an unofficial project. It is not affiliated with or endorsed by ECPay, NewebPay, PAYUNi, LINE, TapPay, JKOPAY or any other company named here. Brand names are written the way each company writes them and belong to their owners.

---

## What it does

| Area | What you get |
|---|---|
| Providers | Covers 14 Taiwan payment providers (table below) |
| Signing and encryption | CheckMacValue, TradeSha, AES-256-CBC, AES-256-GCM, RSA, JWT, HMAC-SHA256, with runnable Python examples |
| Offline data | `scripts/search.py` searches 3214 rows of official data: error codes, API operations, field mappings, payment methods, troubleshooting notes |
| Provider choice | `scripts/recommend.py` suggests a provider from plain-language requirements |
| Payment flows | Credit card, ATM, CVS code, e-wallet, Apple Pay, Google Pay, TWQR, BNPL, recurring billing and refunds, each linked to the right file in `references/` |

### Supported providers

| Provider | Signing / auth | Runnable example | Notes |
|---|---|---|---|
| **ECPay** | SHA256 CheckMacValue | Python | Most complete documentation |
| **NewebPay** | AES-256-CBC + SHA256 | Python | MPG checkout, card memory |
| **PAYUNi** | AES-256-GCM + SHA256 | Python | JSON responses; background APIs need a bound IP |
| **SmilePay** | Verify_key + Mid_smilepay check code | Python | No AES; ibon / FamiPort payment slips |
| **PChomePay 支付連** | Basic Auth → pcpay-token | Python | Payment and logistics in one; 拍錢包 is one of its payment methods |
| **ezPay** | AES-256-CBC + SHA256 HashData | Python | Electronic payment institution; TWQR and ezPay wallet, Alipay / WeChat Pay cross-border |
| **PayNow** | Bearer private key (current API) / SHA-1 PassCode + dynamic AES-256 (legacy API) | Python | Two API generations in parallel; Apple Pay |
| **Shopline Payments** | merchantId + apiKey headers, HMAC-SHA256 webhooks | Python | Amounts in cents; redirect and embedded modes |
| **LINE Pay v4** | Channel ID/Secret + HMAC-SHA256 + nonce | Python | Request → Confirm; Preapproved Pay |
| **TapPay** | Partner Key header, Prime token | Python | PCI isolation; card token for repeat charges |
| **O'Pay** | SHA256 CheckMacValue (same design as ECPay) | — | AccountLink bank payment, delayed payout |
| **JKOPAY** | api-key header + HMAC-SHA256 digest | Python | Online payment, POS, authorized (recurring) payment |
| **SunPay** | RSA segmented encryption + SHA256 check_value | Python | Payment, e-invoice and CVS collection |
| **GoMyPay** | Specification on request from GoMyPay | — | Full API specification is not public |

Encryption in the runnable examples is checked against the providers' official test vectors. Error codes are in `data/error-codes*.csv`.

## When to use

| Task | Use |
|---|---|
| Build or debug a checkout that talks to one of the providers above | this skill |
| Verify a payment notification (CheckMacValue, TradeSha, HashInfo, webhook signatures) | this skill |
| Look up a provider's error or status code | this skill |
| Choose between providers for a project | this skill |
| Issue, void or adjust e-invoices | [taiwan-invoice](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/tree/main/taiwan-invoice) |
| Shipping, convenience-store pickup, store maps or tracking, even with ECPay, NewebPay or PAYUNi | [taiwan-logistics](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/tree/main/taiwan-logistics) |
| Payment providers outside Taiwan, or direct bank and card-network integrations | not covered |

## Install

| Method | Command | Notes |
|---|---|---|
| Claude Code plugin | `/plugin install taiwan-ecommerce@taiwan-ecommerce-toolkit` | Installs all three Taiwan skills: invoice, payment, logistics |
| npx | `npx taiwan-payment-skill@1.5.17 init --ai claude` | Copies the skill into the current project |
| Manual copy | `cp -r taiwan-payment ~/.claude/skills/` | From a clone of this repository |

Claude Code plugin:

```text
/plugin marketplace add Moksa1123/taiwan-ecommerce-toolkit
/plugin install taiwan-ecommerce@taiwan-ecommerce-toolkit
```

npx (`--ai` also accepts other agents such as `cursor` or `codex`; `--global` installs into your home directory):

```bash
npx taiwan-payment-skill@1.5.17 init --ai claude
```

Manual copy:

```bash
git clone https://github.com/Moksa1123/taiwan-ecommerce-toolkit.git
cp -r taiwan-ecommerce-toolkit/taiwan-payment ~/.claude/skills/
```

| Requirement | Needed for |
|---|---|
| Python 3, standard library only | `scripts/` |
| `pycryptodome`, `requests` (`pip install -r requirements.txt`) | `examples/` and the network options of `scripts/test_payment.py` |
| Node.js 18 or later | the npx installer only |
| Windows, macOS or Linux | all |

### CLI commands

| Command | What it does |
|---|---|
| `taiwan-payment init` | Install into the current project; asks which AI agent if `--ai` is omitted |
| `taiwan-payment init --force` | Overwrite an existing install |
| `taiwan-payment init --global` | Install into your home directory |
| `taiwan-payment list` | List supported AI platforms |
| `taiwan-payment info` | Show skill information |
| `taiwan-payment versions` | List available versions |
| `taiwan-payment update` | Update to the latest version |

The installer supports 14 AI coding agents: Claude Code · Cursor · Windsurf · Antigravity · GitHub Copilot · Kiro · Codex · Qoder · Cline · Gemini CLI · Trae · OpenCode · Continue · CodeBuddy.

## Quick start

**Step 1.** Install into your project:

```bash
npx taiwan-payment-skill@1.5.17 init --ai claude
```

**Step 2.** Ask Claude, for example:

```text
Create an ECPay credit-card order in Python and verify the payment notification.
My NewebPay TradeInfo fails to decrypt. What is wrong with my padding?
Which provider should I use for LINE Pay plus recurring card payments?
```

**Step 3.** Or search the data yourself from the skill folder:

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

English: Taiwan payment gateway, ECPay, NewebPay, PAYUNi, LINE Pay, TapPay, JKOPAY, credit card payment, ATM virtual account, CVS payment code, Apple Pay, Google Pay, Click to Pay, TWQR, BNPL, CheckMacValue, payment notification, refund, recurring payment.

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

| Check | Result |
|---|---|
| Data source | Official provider documentation, PDF specifications and official SDKs or plugins. Every source is registered in [`sources/official-sources.json`](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/sources/official-sources.json); each data row carries `doc_url` and `trust` |
| Official-docs audit | Last run 2026-11-17, recorded in [`references/audit-20261117.md`](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/taiwan-payment/references/audit-20261117.md) |
| Self-test | `python3 scripts/test_skill.py` runs 50 checks, 0 failures (run on 2026-11-17) |
| Evals | On the 10 scored questions, Claude answered 10 correctly with the skill and 0 without it. See [`evals/RESULTS.md`](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/taiwan-payment/evals/RESULTS.md) |
| Example code | CI runs `scripts/verify-examples.py`, which compares the examples byte for byte with expected values from the providers' own SDKs and spec samples ([`tests/vectors/`](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/tree/main/tests/vectors)) |

## Limits

| Limit | Details |
|---|---|
| No runnable example | O'Pay and GoMyPay |
| GoMyPay | The full API specification is not public; you have to request it from GoMyPay |
| JKOPAY | The documentation site did not resolve during the latest audit, so the reference is based on the last saved copy of the official pages |
| Inferred rows | Rows marked `trust=推論` (recommendations, troubleshooting) are inferred from the official docs; treat them as advice, not as provider rules |
| Known gaps | Tracked in [`data/pending.csv`](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/taiwan-payment/data/pending.csv) |

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

| Reference file | Covers |
|---|---|
| `ecpay-`, `newebpay-`, `payuni-`, `smilepay-`, `pchomepay-payment-api.md` | ECPay, NewebPay, PAYUNi, SmilePay, PChomePay |
| `ezpay-`, `paynow-`, `shopline-`, `linepay-`, `tappay-payment-api.md` | ezPay, PayNow, Shopline Payments, LINE Pay, TapPay |
| `opay-`, `jkopay-`, `sunpay-`, `gomypay-payment-api.md` | O'Pay, JKOPAY, SunPay, GoMyPay |
| `twqr-ewallet-landscape.md` | Electronic payment and TWQR landscape |
| `implementation-guide.md` | Cross-provider implementation notes |
| `audit-20261117.md` | Latest official-docs audit |

## License & author

MIT License ([LICENSE](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/LICENSE)). Made by Moksa ([moksaweb.com](https://moksaweb.com)).

This package is part of [Taiwan E-commerce Toolkit](https://github.com/Moksa1123/taiwan-ecommerce-toolkit):

| Package | Covers |
|---|---|
| [taiwan-invoice-skill](https://www.npmjs.com/package/taiwan-invoice-skill) | Taiwan e-invoice providers and MOF platform queries |
| [taiwan-logistics-skill](https://www.npmjs.com/package/taiwan-logistics-skill) | Taiwan logistics aggregators, HCT direct API, on-demand delivery |
