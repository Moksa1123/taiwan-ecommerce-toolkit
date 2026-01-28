<div align="center">

# Taiwan Invoice Skills

![Version](https://img.shields.io/badge/version-2.0.0-blue?style=flat-square)
![Providers](https://img.shields.io/badge/providers-3-green?style=flat-square)
![Platforms](https://img.shields.io/badge/platforms-3-purple?style=flat-square)
![API Docs](https://img.shields.io/badge/API_docs-3-orange?style=flat-square)
![Examples](https://img.shields.io/badge/examples-9-red?style=flat-square)
![Python](https://img.shields.io/badge/python-3.x-yellow?style=flat-square&logo=python&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-brightgreen?style=flat-square)

[![GitHub](https://img.shields.io/badge/GitHub-Repository-black?style=flat-square&logo=github)](https://github.com/Moksa1123/taiwan-invoice)
[![PayPal](https://img.shields.io/badge/PayPal-Support_Development-blue?style=flat-square&logo=paypal)](https://paypal.me/cccsubcom)

An AI skill that provides Taiwan E-Invoice API integration intelligence for multiple AI coding assistants.

**台灣電子發票 AI 開發技能包**

Works with &nbsp; ![Claude Code](https://img.shields.io/badge/Claude_Code-black?style=flat-square&logo=anthropic&logoColor=white) &nbsp; ![Cursor](https://img.shields.io/badge/Cursor-black?style=flat-square&logo=cursor&logoColor=white) &nbsp; ![Antigravity](https://img.shields.io/badge/Antigravity-black?style=flat-square&logo=google&logoColor=white)

</div>

---

## What's Included

| Category | Count | Description |
|----------|-------|-------------|
| **Providers** | 3 | ECPay (綠界), SmilePay (速買配), Amego (光貿) |
| **Invoice Types** | 2 | B2C 二聯式, B2B 三聯式 |
| **Features** | 5 | 開立、作廢、折讓、查詢、列印 |
| **API References** | 3 | 完整 API 規格文件（含欄位、錯誤碼、測試帳號） |
| **Code Examples** | 9 | 基礎範例 + 實務情境 + 錯誤修正 |
| **Helper Scripts** | 2 | 服務模組生成器、金額計算驗證 |
| **Platforms** | 3 | Claude Code, Cursor, Google Antigravity |

---

## Overview

```
+-----------------------------------------------------------------------------------+
|  TAIWAN INVOICE SKILLS                                                            |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  PROVIDERS:                                                                       |
|     ECPay (綠界)      AES-128-CBC encryption       Full test environment          |
|     SmilePay (速買配)  URL parameter signing        Simple integration             |
|     Amego (光貿)      MD5 signature (MIG 4.0)      Clean API design               |
|                                                                                   |
|  INVOICE TYPES:                                                                   |
|     B2C (二聯式)  Tax-inclusive pricing, TaxAmount = 0                            |
|     B2B (三聯式)  Pre-tax + tax split, 5% tax rate                                |
|                                                                                   |
|  FEATURES:                                                                        |
|     Issue | Void | Allowance | Query | Print                                      |
|                                                                                   |
|  INVOCATION:                                                                      |
|     Claude Code    /taiwan-invoice or auto-activate                               |
|     Cursor         /taiwan-invoice or auto-activate                               |
|     Antigravity    Auto-activate based on description                             |
|                                                                                   |
+-----------------------------------------------------------------------------------+
```

---

## Installation

### Using Install Script (Recommended)

**macOS / Linux:**

```bash
git clone https://github.com/Moksa1123/taiwan-invoice.git
cd taiwan-invoice
bash install.sh
```

**Windows:**

```cmd
git clone https://github.com/Moksa1123/taiwan-invoice.git
cd taiwan-invoice
install.bat
```

The install script provides an interactive menu to select your target platform(s).

### Manual Installation

Copy `taiwan-invoice/` to the appropriate location for your AI assistant:

```bash
# Claude Code
cp -r taiwan-invoice ~/.claude/skills/taiwan-invoice

# Cursor
cp -r taiwan-invoice ~/.cursor/skills/taiwan-invoice

# Google Antigravity
cp -r taiwan-invoice ~/.gemini/antigravity/global_skills/taiwan-invoice
```

### Platform Paths

| Platform | Project Level | Global Level |
|----------|---------------|--------------|
| Claude Code | `.claude/skills/taiwan-invoice/` | `~/.claude/skills/` |
| Cursor | `.cursor/skills/taiwan-invoice/` | `~/.cursor/skills/` |
| Antigravity | `.agent/skills/taiwan-invoice/` | `~/.gemini/antigravity/global_skills/` |

> **Note:** Cursor can also read `.claude/skills/` directory for cross-compatibility.

---

## Usage

### Skill Mode (Auto-activate)

The skill automatically loads when your conversation involves Taiwan E-Invoice topics:

```
幫我用綠界測試環境開立一張 1050 元的 B2C 發票
```

```
我需要串接速買配的 B2B 發票功能，請產生完整的 API 呼叫程式碼
```

```
請幫我寫一個發票作廢的函式，要支援光貿的 MIG 4.0 簽章機制
```

### Slash Command Mode

Manually invoke the skill using `/taiwan-invoice`:

```
/taiwan-invoice 幫我建立一個發票服務工廠，支援三家加值中心切換
```

---

## How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│  1. USER REQUEST                                                │
│     「幫我用綠界測試環境開立一張 1050 元的 B2C 發票」                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. SKILL ACTIVATION                                            │
│     • Detect e-invoice keywords → Load taiwan-invoice skill     │
│     • Read relevant API reference (ECPAY_API_REFERENCE.md)      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. INTELLIGENT CODE GENERATION                                 │
│     • Determine invoice type (B2C → tax-inclusive, TaxAmount=0) │
│     • Select encryption method (ECPay → AES-128-CBC)            │
│     • Apply test environment URL and credentials                │
│     • Generate complete TypeScript service code                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. OUTPUT                                                      │
│     Complete InvoiceService implementation with:                │
│     Encryption + API calls + Error handling + Amount calc       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Amount Calculation Logic

```
B2C (二聯式) Tax-inclusive:
┌──────────────────────────────────────────┐
│  Total = 1050                            │
│  SalesAmount = 1050  (use as-is)         │
│  TaxAmount   = 0     (always 0)          │
│  TotalAmount = 1050                      │
└──────────────────────────────────────────┘

B2B (三聯式) Pre-tax + Tax split:
┌──────────────────────────────────────────┐
│  Total = 1050                            │
│  TaxAmount   = round(1050 - 1050/1.05)   │
│             = round(1050 - 1000) = 50    │
│  SalesAmount = 1050 - 50 = 1000          │
│  TotalAmount = 1050                      │
│                                          │
│  Verify: 1000 + 50 = 1050 ✓              │
└──────────────────────────────────────────┘
```

---

## Supported Providers

| Provider | Authentication | Features | Test Environment |
|----------|----------------|----------|------------------|
| **ECPay (綠界)** | AES-128-CBC encryption | Full documentation, high market share | Yes |
| **SmilePay (速買配)** | URL parameter signing | Dual protocol support, simple integration | Yes |
| **Amego (光貿)** | MD5 signature (MIG 4.0) | Clean API design | Yes |

All three support: B2C/B2B invoice issuance, void, allowance, query, and print.

---

## Helper Scripts

Located in `taiwan-invoice/scripts/`:

**generate-invoice-service.py** — Generate service module template:

```bash
python taiwan-invoice/scripts/generate-invoice-service.py ECPay
# Generates ecpay-invoice-service.ts with complete interface implementation
```

**test-invoice-amounts.py** — Verify B2C/B2B amount calculation:

```bash
python taiwan-invoice/scripts/test-invoice-amounts.py
# Tests various amounts for tax split verification
```

### Prerequisites

Python 3.x required:

```bash
# macOS
brew install python3

# Windows
winget install Python.Python.3.12
```

---

## Project Structure

```
taiwan-invoice/
├── taiwan-invoice/                        # Source of Truth
│   ├── SKILL.md                           # Skill definition (shared across platforms)
│   ├── EXAMPLES.md                        # Code examples (9 examples)
│   ├── references/                        # API documentation
│   │   ├── ECPAY_API_REFERENCE.md         # ECPay full API spec
│   │   ├── SMILEPAY_API_REFERENCE.md      # SmilePay full API spec
│   │   └── AMEGO_API_REFERENCE.md         # Amego full API spec
│   └── scripts/                           # Helper scripts
│       ├── generate-invoice-service.py    # Service module generator
│       └── test-invoice-amounts.py        # Amount calculation tester
│
├── .claude/skills/taiwan-invoice/         # Claude Code (pre-installed)
├── .cursor/skills/taiwan-invoice/         # Cursor (pre-installed)
├── .agent/skills/taiwan-invoice/          # Antigravity (pre-installed)
│
├── install.sh                             # macOS/Linux installer
├── install.bat                            # Windows installer
├── LICENSE                                # MIT License
├── CONTRIBUTING.md                        # Contribution guide
└── CHANGELOG.md                           # Version history
```

---

## FAQ

<details>
<summary><b>Do all three platforms use the same SKILL.md?</b></summary>

Yes. Claude Code, Cursor, and Google Antigravity all follow the [Agent Skills Open Standard](https://agentskills.io), so they share the same SKILL.md file. No need to maintain separate versions.
</details>

<details>
<summary><b>Do I need API credentials from the providers?</b></summary>

Yes. Apply for merchant ID and API keys from your chosen provider before use. All three offer test environments—SKILL.md includes test account information for development.
</details>

<details>
<summary><b>Can I support multiple providers in one project?</b></summary>

Yes. The skill definition includes complete API specs for all three providers. Use the Service Factory Pattern to dynamically switch between them.
</details>

<details>
<summary><b>Cursor already has .claude/skills/. Do I need .cursor/skills/ too?</b></summary>

Not necessarily. Cursor can read `.claude/skills/` automatically. If you only need Claude Code + Cursor support, installing to `.claude/skills/` alone is sufficient.
</details>

<details>
<summary><b>The skill isn't loading. What should I do?</b></summary>

1. Verify SKILL.md exists in the correct directory path
2. Check that YAML frontmatter is valid
3. Restart your AI assistant
4. Try manually invoking with `/taiwan-invoice`
</details>

---

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

```bash
# 1. Fork and clone
git clone https://github.com/your-username/taiwan-invoice.git
cd taiwan-invoice

# 2. Create feature branch
git checkout -b feature/your-feature-name

# 3. Make changes to taiwan-invoice/ (Source of Truth)

# 4. Test
python taiwan-invoice/scripts/test-invoice-amounts.py

# 5. Commit and push
git commit -m "Add: description of your change"
git push -u origin feature/your-feature-name
```

After modifying `taiwan-invoice/`, sync to platform directories (`.claude/skills/`, `.cursor/skills/`, `.agent/skills/`).

---

## License

This project is licensed under the [MIT License](LICENSE).
