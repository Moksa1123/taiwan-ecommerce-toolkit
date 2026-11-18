<h1 align="center">Taiwan E-Commerce Integration Toolkit</h1>

<h3 align="center">台灣電商整合開發工具包</h3>

<p align="center">
  <strong>E-Invoice · Payment Gateways · Logistics</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/node-%3E%3D18-339933?style=flat-square&logo=node.js&logoColor=white" alt="Node.js">
  <img src="https://img.shields.io/badge/python-3.x-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/typescript-5.x-3178C6?style=flat-square&logo=typescript&logoColor=white" alt="TypeScript">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/providers-33-success?style=flat-square" alt="33 Providers">
  <img src="https://img.shields.io/badge/AI%20platforms-14-blue?style=flat-square" alt="14 AI Platforms">
  <a href="LICENSE"><img src="https://img.shields.io/github/license/Moksa1123/taiwan-ecommerce-toolkit?style=flat-square" alt="License"></a>
</p>

<p align="center">
  <a href="https://paypal.me/cccsubcom"><img src="https://img.shields.io/badge/PayPal-Support-00457C?style=for-the-badge&logo=paypal&logoColor=white" alt="PayPal"></a>
</p>

<p align="center"><a href="README.zh-TW.md">正體中文</a></p>

> Unofficial community project. Not affiliated with, endorsed by, or sponsored by ECPay, NewebPay, PAYUNi, LINE, TapPay, JKOPAY or any other company named here. Product names belong to their owners.

---

## Overview

Agent skills for integrating Taiwan e-invoice, payment and logistics APIs, built from each provider's official documentation. The repository is one Claude plugin (`taiwan-ecommerce`) bundling three skills that cover **33 providers** (9 invoice + 14 payment + 10 integrable logistics), plus 10 logistics carriers that have no merchant API, listed with the route to use instead.

<table>
<tr>
<td width="33%" align="center">

### E-Invoice

**taiwan-invoice-skill**

9 providers: 7 value-added centers + MOF platform + TradeVAN

<a href="https://www.npmjs.com/package/taiwan-invoice-skill"><img src="https://img.shields.io/npm/v/taiwan-invoice-skill?style=flat-square&color=cb3837&logo=npm" alt="npm version"></a>
<a href="https://www.npmjs.com/package/taiwan-invoice-skill"><img src="https://img.shields.io/npm/dm/taiwan-invoice-skill?style=flat-square&color=cb3837" alt="npm downloads"></a>

[Docs](taiwan-invoice/README.md)

</td>
<td width="33%" align="center">

### Payment Gateways

**taiwan-payment-skill**

14 payment providers and wallets

<a href="https://www.npmjs.com/package/taiwan-payment-skill"><img src="https://img.shields.io/npm/v/taiwan-payment-skill?style=flat-square&color=cb3837&logo=npm" alt="npm version"></a>
<a href="https://www.npmjs.com/package/taiwan-payment-skill"><img src="https://img.shields.io/npm/dm/taiwan-payment-skill?style=flat-square&color=cb3837" alt="npm downloads"></a>

[Docs](taiwan-payment/README.md)

</td>
<td width="33%" align="center">

### Logistics

**taiwan-logistics-skill**

10 integrable: 7 aggregators + HCT direct + 2 on-demand

<a href="https://www.npmjs.com/package/taiwan-logistics-skill"><img src="https://img.shields.io/npm/v/taiwan-logistics-skill?style=flat-square&color=cb3837&logo=npm" alt="npm version"></a>
<a href="https://www.npmjs.com/package/taiwan-logistics-skill"><img src="https://img.shields.io/npm/dm/taiwan-logistics-skill?style=flat-square&color=cb3837" alt="npm downloads"></a>

[Docs](taiwan-logistics/README.md)

</td>
</tr>
</table>

| Each skill ships | Purpose |
|---|---|
| `SKILL.md` + `references/` | How each provider's API really works: endpoints, fields, signatures, error codes |
| `data/*.csv` + `scripts/search.py` | Searchable endpoints, field mappings and error codes (BM25, offline) |
| `examples/` | Runnable code checked against official test vectors |
| `data/pending.csv` | What still needs confirming with the provider |

**When to use:** writing or debugging code against a Taiwan e-invoice, payment or logistics provider: checkout, `CheckMacValue` / `TradeSha`, payment notifications, issuing or voiding invoices, shipments, store maps, error codes. **Not for:** accounting, tax filing or non-Taiwan providers; it does not replace the merchant contract or production keys you get from the provider.

---

## Quick Start

### Step 1: Install

Claude plugin (Claude Code; also in the Claude directory once approved):

```
/plugin marketplace add Moksa1123/taiwan-ecommerce-toolkit
/plugin install taiwan-ecommerce@taiwan-ecommerce-toolkit
```

Other AI coding tools, or one skill only (npx with a pinned version):

```bash
npx taiwan-invoice-skill@2.9.13 init     # e-invoice
npx taiwan-payment-skill@1.5.16 init     # payment
npx taiwan-logistics-skill@1.4.13 init   # logistics
```

Manual copy: put a skill folder where your assistant loads skills, e.g. `cp -r taiwan-payment ~/.claude/skills/`.

Requirements: Python 3 for the bundled scripts (standard library only; the AES examples need `pycryptodome`). Node.js 18+ only for the npx installer. Windows, macOS and Linux.

### Step 2: Pick your AI tool

```bash
cd /path/to/your/project
npx taiwan-payment-skill@1.5.16 init --ai claude    # or cursor, windsurf, copilot, codex, gemini, all ...
```

Supported tools and their skill folders: [docs/guide.zh-TW.md](docs/guide.zh-TW.md).

### Step 3: Ask in plain language

```
Build an ECPay credit-card checkout in Python and verify the payment notification.
NewebPay returned MPG03009. What is wrong?
Which provider should I use for cold-chain convenience-store pickup?
```

Or query the data directly:

```bash
python3 taiwan-payment/scripts/search.py "CheckMacValue" --domain field
python3 taiwan-logistics/scripts/recommend.py "超商取貨 溫控配送 冷凍宅配"   # → PAYUNi first
```

**Trigger phrases:** Taiwan e-invoice, ECPay, NewebPay, PAYUNi, LINE Pay, TapPay, CheckMacValue, payment notification, convenience-store pickup, store map, cold-chain delivery · 電子發票、開立發票、載具、金流串接、綠界、藍新、統一金流、付款通知、超商取貨、電子地圖選店、宅配、物流狀態碼。

---

## Provider Support

### E-Invoice

| Provider | Auth / encryption | Notes |
|---|---|---|
| **ECPay** | AES-128-CBC + HashKey/HashIV | B2C and B2B; B2B requests carry `RqID` and `Revision` |
| **SmilePay** | Grvc + Verify_key | URL parameters, no AES |
| **Amego** | MD5 signature + App Key | MIG 4.0; allowances issued by the seller only |
| **ezPay** | AES-256-CBC + SHA256 | Track management, batch issuing, allowance/void queries |
| **PayNow** | JWT Bearer | Payment, logistics and invoice from one provider |
| **O'Pay** | MerchantID + RqHeader + AES Data | Same structure as ECPay, different domain and keys |
| **SunPay** | AES-128-CBC token | Can issue together with SunPay payments |
| **MOF platform** | AppID + APIKey (HMAC-SHA256) | Queries only (carriers, donation codes); cannot issue |
| **TradeVAN** | Contract only | Listed in data; no public spec |

### Payment Gateways

| Provider | Auth / encryption | Payment methods | Notes |
|---|---|---|---|
| **ECPay** | SHA256 CheckMacValue | Card, ATM, CVS code/barcode, Apple Pay, TWQR, BNPL, digital wallets | Most complete docs |
| **NewebPay** | AES-256-CBC + SHA256 | Card, instalments, ATM, CVS, LINE Pay, Apple/Google/Samsung Pay, TWQR, BitoPro | MPG spec NDNF-1.2.6 |
| **PAYUNi** | AES-256-GCM + SHA256 | Card token, Click to Pay, ATM, CVS, JKOPAY, icash Pay, AFTEE, LINE Pay | UPP Version 2.0 |
| **SmilePay** | Verify_key + check code | ATM, barcode, ibon, FamiPort, card, UnionPay | XML responses |
| **PChomePay** | HTTP Basic → token | Card, ATM, CVS code, CVS pickup | API doc 1.7.4 |
| **ezPay** | AES-256-CBC + SHA256 | ezPay account, linked bank/card, TWQR, cross-border | E-payment institution |
| **PayNow** | Bearer private key (modern) / dynamic AES-256 (legacy) | Card, instalments, ATM, CVS, LINE Pay, Apple Pay | Webhook HMAC-SHA256 |
| **SHOPLINE Payments** | merchantId + apiKey headers | Card, Apple Pay, LINE Pay, JKOPAY, ATM, BNPL | Amounts in cents, HMAC webhook |
| **LINE Pay v4** | HMAC-SHA256 + nonce | LINE Pay, preapproved pay | Request → confirm |
| **TapPay** | Partner key + Prime | Card, Apple/Google Pay, LINE Pay, JKOPAY, more | `prod.tappaysdk.com` |
| **O'Pay** | SHA256 CheckMacValue | Card, ATM, CVS, TWQR, stored value | Same structure as ECPay |
| **JKOPAY** | api-key + HMAC-SHA256 | Online, POS, authorized payment | Public doc site offline since 2026-11-17 |
| **SunPay** | RSA + SHA256 check_value | Card, ATM, CVS | Manual V1.1.2 |
| **GoMyPay** | Contract only | Card, UnionPay, WebATM, virtual account, CVS | Spec not public |

### Logistics (10 integrable)

| Provider | Type | Auth / encryption | Coverage |
|---|---|---|---|
| **ECPay** | Aggregator | MD5 CheckMacValue | B2C 7-ELEVEN (incl. frozen), FamilyMart, Hi-Life; C2C 7-ELEVEN, FamilyMart, Hi-Life (OK ended 2026-07-01); home delivery |
| **NewebPay** | Aggregator | AES-256-CBC + SHA256 | CVS pickup; no home delivery |
| **PAYUNi** | Aggregator | AES-256-GCM + SHA256 | 7-ELEVEN (ambient/frozen), T-Cat (ambient/chilled/frozen) |
| **SmilePay** | Aggregator | Verify_key | 7-ELEVEN, FamilyMart, T-Cat; two-step order creation |
| **PChomePay** | Aggregator | HTTP Basic → token | 7-ELEVEN, FamilyMart, Hi-Life (cash on pickup) |
| **PayNow** | Aggregator | 3DES / ECB | Many product lines incl. frozen and bulk |
| **ezShip** | Aggregator | Account binding (`su_id`) | FamilyMart, Hi-Life, OK, home delivery |
| **HCT** | Direct carrier | SOAP with company account | Home delivery; public WSDL |
| **Lalamove** | On-demand | HMAC-SHA256 | Same-city delivery (TW market) |
| **pandago** | On-demand | OAuth 2.0 (STS token) | Same-city delivery; `/quotes` for price and time |

Carriers without a merchant API (Black Cat, Kerry TJ, Pelican, Chunghwa Post, 7-ELEVEN, FamilyMart, Hi-Life, OK, Shopee stores, SunPay logistics) are listed in `taiwan-logistics/references/carrier-direct-access.md` with the aggregator route.

---

## What it runs and connects to

- **Nothing runs on its own.** No hooks, MCP servers or background processes; scripts run only when you or the assistant call them.
- **Offline scripts** (local CSV and templates only): `search.py`, `recommend.py`, `check_numbers.py`, `test_skill.py` and the service generators. `persist.py` (invoice) writes a settings file only in the directory you choose.
- **Optional network tests:** `taiwan-payment/scripts/test_payment.py` and `taiwan-logistics/scripts/test_logistics.py` are offline by default. Only with `--live`, `--create` or `--query` do they call the providers' **test** environments: `payment-stage.ecpay.com.tw`, `ccore.newebpay.com`, `sandbox-api.payuni.com.tw`, `logistics-stage.ecpay.com.tw`.
- **Examples** in `examples/` call the provider you choose when you run them in your own project.
- **Credentials:** you supply your own merchant ID and keys through environment variables or your own config. No real credentials are in the repository; test values in the docs are the providers' public sandbox accounts.
- **Maintainer tooling** (not used by the skills): `scripts/check-sources.py` downloads the official documents in `sources/official-sources.json` to detect changes; a weekly GitHub Action runs it.
- No data is collected or sent to the author.

## How it's verified

| Check | What it does |
|---|---|
| Official sources | Every endpoint, field and error code traces to `sources/official-sources.json`; unsourced claims are removed or listed as pending |
| Weekly source check | Re-downloads those sources and opens an issue on change |
| Official test vectors | `scripts/verify-examples.py` (CI) matches signature/encryption code byte for byte against `tests/vectors/` |
| Self-tests and evals | `scripts/test_skill.py` and `evals/RESULTS.md` in each skill |
| Latest audit (2026-11-17) | [invoice](taiwan-invoice/references/audit-20261117.md) · [payment](taiwan-payment/references/audit-20261117.md) · [logistics](taiwan-logistics/references/audit-20261117.md) |

## Limits

- Some specs are available only to contracted merchants (SmilePay, GoMyPay, TradeVAN); those parts are marked, not guessed.
- JKOPAY's public documentation site is unreachable; that reference reflects the last official copy.
- Open questions: [invoice](taiwan-invoice/data/pending.csv) · [payment](taiwan-payment/data/pending.csv) · [logistics](taiwan-logistics/data/pending.csv). More (AI tools, CLI commands, FAQ, algorithms): [docs/guide.zh-TW.md](docs/guide.zh-TW.md).

## Repo Layout

```
.claude-plugin/        plugin and marketplace manifests
taiwan-invoice/        e-invoice skill (SKILL.md, references, data, scripts, examples)
taiwan-payment/        payment skill
taiwan-logistics/      logistics skill
*-cli/                 npm installers (taiwan-*-skill)
sources/ scripts/      official source registry and maintainer checks
tests/vectors/ docs/   official test vectors, longer guides
```

## License & Author

[MIT License](LICENSE) · Made by **Moksa** · [moksaweb.com](https://moksaweb.com) · [Contributing](CONTRIBUTING.md)
