<h1 align="center">Taiwan E-Commerce Integration Toolkit</h1>

<h3 align="center">台灣電商整合開發工具包 · Claude directory edition</h3>

<p align="center">
  <strong>E-Invoice · Payment Gateways · Logistics</strong>
</p>

> Unofficial community project. Not affiliated with, endorsed by, or sponsored by ECPay, NewebPay,
> PAYUNi, LINE, TapPay, JKOPAY or any other company named here. Product names belong to their owners.

This folder is the reference-only edition of
[taiwan-ecommerce-toolkit](https://github.com/Moksa1123/taiwan-ecommerce-toolkit) for the Claude plugin
directory. It is generated from the main repository by `scripts/build_directory.py`; do not edit it by hand.

## What it does

Three skills that teach Claude how Taiwan e-invoice, payment and logistics APIs really work, built from
each provider's official documentation:

| Skill | Covers | Data rows (JSON) |
|---|---|---|
| `taiwan-invoice` | Issue, void and allowance flows for Taiwan e-invoices; MOF platform queries | 450 |
| `taiwan-payment` | Checkout, notifications, refunds and signatures for Taiwan payment gateways and wallets | 3275 |
| `taiwan-logistics` | Convenience-store pickup, home delivery, cold chain, store maps, on-demand delivery | 1159 |

Each skill ships its `SKILL.md`, provider references, code examples in Markdown and the data set as JSON
(endpoints, field mappings, error and status codes, each row with its official `doc_url`).

## Directory edition vs full edition

| | Directory edition (this folder) | Full edition |
|---|---|---|
| References, examples in Markdown, data | Yes (data as JSON) | Yes (data as CSV) |
| Search and recommendation tools | No: Claude reads the JSON directly | `scripts/search.py`, `scripts/recommend.py` |
| Runnable examples, known-answer tests | No | `examples/`, `scripts/test_*.py` |
| Install | Claude plugin directory | `npx taiwan-invoice-skill@2.9.13 init`, `npx taiwan-payment-skill@1.5.17 init`, `npx taiwan-logistics-skill@1.4.13 init` |

## What it runs and connects to

Nothing. This edition contains only Markdown, JSON and an icon: no scripts, hooks, MCP servers or
network requests. Merchant IDs and keys are set and provided by the user in their own code; test
accounts mentioned in the references are the providers' published sandbox values, not real credentials.

## How it's verified

Every endpoint, field and error code traces to an official source (provider developer sites, official
PDF specs, official SDKs). The full repository re-checks those sources weekly, verifies signature and
encryption code against the providers' official test vectors in CI, and records the latest audit in
each skill's `references/audit-20261117.md`. Open questions are in each skill's `data/pending.json`.

## License & author

MIT License. Made by Moksa.
