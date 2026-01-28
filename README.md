# Taiwan Invoice Skill

<p align="center">
  <a href="https://github.com/Moksa1123/taiwan-invoice/releases"><img src="https://img.shields.io/github/v/release/Moksa1123/taiwan-invoice?style=for-the-badge&color=blue" alt="GitHub Release"></a>
  <img src="https://img.shields.io/badge/providers-3-green?style=for-the-badge" alt="3 Providers">
  <img src="https://img.shields.io/badge/platforms-14-purple?style=for-the-badge" alt="14 Platforms">
  <img src="https://img.shields.io/badge/python-3.x-yellow?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.x">
  <a href="https://github.com/Moksa1123/taiwan-invoice/blob/main/LICENSE"><img src="https://img.shields.io/github/license/Moksa1123/taiwan-invoice?style=for-the-badge&color=green" alt="License"></a>
</p>

<p align="center">
  <a href="https://www.npmjs.com/package/taiwan-invoice-skill"><img src="https://img.shields.io/npm/v/taiwan-invoice-skill?style=flat-square&logo=npm&label=CLI" alt="npm"></a>
  <a href="https://www.npmjs.com/package/taiwan-invoice-skill"><img src="https://img.shields.io/npm/dm/taiwan-invoice-skill?style=flat-square&label=downloads" alt="npm downloads"></a>
  <a href="https://github.com/Moksa1123/taiwan-invoice/stargazers"><img src="https://img.shields.io/github/stars/Moksa1123/taiwan-invoice?style=flat-square&logo=github" alt="GitHub stars"></a>
  <a href="https://paypal.me/cccsubcom"><img src="https://img.shields.io/badge/PayPal-Support%20Development-00457C?style=flat-square&logo=paypal&logoColor=white" alt="PayPal"></a>
</p>

An AI skill that provides Taiwan E-Invoice API integration intelligence for multiple AI coding assistants.

**台灣電子發票 AI 開發技能包** - 支援綠界、速買配、光貿三大加值中心

## Features

- **3 Invoice Providers** - ECPay (綠界), SmilePay (速買配), Amego (光貿)
- **Complete API Specs** - Full documentation with field definitions, error codes, test accounts
- **9 Code Examples** - Practical examples covering common use cases and error handling
- **2 Helper Scripts** - Service generator and amount calculation validator
- **14 AI Platforms** - Claude Code, Cursor, Windsurf, Copilot, and more

### Supported Providers

| Provider | Authentication | Features | Test Environment |
|----------|----------------|----------|------------------|
| **ECPay** | AES-128-CBC encryption | Full documentation, high market share | Yes |
| **SmilePay** | URL parameter signing | Dual protocol support, simple integration | Yes |
| **Amego** | MD5 signature (MIG 4.0) | Clean API design | Yes |

### Invoice Types

| Type | Description | Tax Handling |
|------|-------------|--------------|
| **B2C** | Consumer invoice (二聯式) | Tax-inclusive (TaxAmount = 0) |
| **B2B** | Business invoice (三聯式) | Pre-tax + 5% tax split |

### Operations

Issue, Void, Allowance, Query, Print

## Installation

### Using CLI (Recommended)

```bash
# Install CLI globally
npm install -g taiwan-invoice-skill

# Go to your project
cd /path/to/your/project

# Install for your AI assistant
taiwan-invoice init --ai claude        # Claude Code
taiwan-invoice init --ai cursor        # Cursor
taiwan-invoice init --ai windsurf      # Windsurf
taiwan-invoice init --ai copilot       # GitHub Copilot
taiwan-invoice init --ai antigravity   # Antigravity
taiwan-invoice init --ai kiro          # Kiro
taiwan-invoice init --ai codex         # Codex CLI
taiwan-invoice init --ai qoder         # Qoder
taiwan-invoice init --ai roocode       # Roo Code
taiwan-invoice init --ai gemini        # Gemini CLI
taiwan-invoice init --ai trae          # Trae
taiwan-invoice init --ai opencode      # OpenCode
taiwan-invoice init --ai continue      # Continue
taiwan-invoice init --ai codebuddy     # CodeBuddy
taiwan-invoice init --ai all           # All assistants
```

### Other CLI Commands

```bash
taiwan-invoice list                    # List supported platforms
taiwan-invoice info                    # Show skill information
taiwan-invoice versions                # List available versions
taiwan-invoice update                  # Check for updates
taiwan-invoice init --offline          # Skip GitHub download, use bundled assets
taiwan-invoice init --force            # Overwrite existing files
taiwan-invoice init --global           # Install to global directory
```

### Manual Installation

Copy `taiwan-invoice/` to the appropriate location:

```bash
# Claude Code
cp -r taiwan-invoice ~/.claude/skills/taiwan-invoice

# Cursor
cp -r taiwan-invoice ~/.cursor/skills/taiwan-invoice

# Antigravity
cp -r taiwan-invoice ~/.gemini/antigravity/global_skills/taiwan-invoice
```

## Prerequisites

Python 3.x is required for the helper scripts.

```bash
# Check if Python is installed
python3 --version

# macOS
brew install python3

# Ubuntu/Debian
sudo apt update && sudo apt install python3

# Windows
winget install Python.Python.3.12
```

## Usage

### Skill Mode (Auto-activate)

**Supported:** Claude Code, Windsurf, Antigravity, Codex CLI, Continue, Gemini CLI, OpenCode, Qoder, CodeBuddy

The skill activates automatically when you request invoice-related work:

```
幫我用綠界測試環境開立一張 1050 元的 B2C 發票
```

```
I need to integrate SmilePay B2B invoice API, generate the complete service code
```

### Slash Command Mode

**Supported:** Cursor, Kiro, GitHub Copilot, Roo Code

Use the slash command to invoke the skill:

```
/taiwan-invoice 幫我建立一個發票服務工廠，支援三家加值中心切換
```

### How It Works

1. **You ask** - Request any invoice-related task
2. **Skill activates** - Detects e-invoice keywords, loads relevant API reference
3. **Code generation** - Generates TypeScript code with proper encryption
4. **Validation** - Applies correct tax calculation and API parameters

## Amount Calculation

### B2C (Tax-inclusive)

```
Total = 1050
SalesAmount = 1050  (use as-is)
TaxAmount   = 0     (always 0 for B2C)
TotalAmount = 1050
```

### B2B (Pre-tax + Tax)

```
Total = 1050
TaxAmount   = round(1050 - 1050/1.05) = 50
SalesAmount = 1050 - 50 = 1000
TotalAmount = 1050

Verify: SalesAmount + TaxAmount = TotalAmount
```

## Helper Scripts

### Generate Service Module

```bash
python taiwan-invoice/scripts/generate-invoice-service.py ECPay
# Generates ecpay-invoice-service.ts with complete implementation
```

### Test Amount Calculation

```bash
python taiwan-invoice/scripts/test-invoice-amounts.py
# Tests B2C/B2B tax calculation for various amounts
```

## Supported Platforms

| Platform | Description |
|----------|-------------|
| **Claude Code** | Anthropic's official AI coding assistant |
| **Cursor** | AI-powered code editor |
| **Windsurf** | Codeium's AI code editor |
| **Copilot** | GitHub Copilot Chat |
| **Antigravity** | Google's AI coding assistant |
| **Kiro** | AWS AI coding assistant |
| **Codex** | OpenAI Codex CLI |
| **Qoder** | Qodo AI coding assistant |
| **RooCode** | VSCode AI extension |
| **Gemini CLI** | Google Gemini CLI tool |
| **Trae** | ByteDance AI coding assistant |
| **OpenCode** | Open-source AI assistant |
| **Continue** | Open-source AI assistant |
| **CodeBuddy** | Tencent AI coding assistant |

## Project Structure

```
taiwan-invoice/
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── cli/                                   # CLI installer (npm package)
│   ├── src/
│   ├── assets/
│   └── package.json
└── taiwan-invoice/                        # Source of Truth
    ├── SKILL.md
    ├── EXAMPLES.md
    ├── references/
    │   ├── ECPAY_API_REFERENCE.md
    │   ├── SMILEPAY_API_REFERENCE.md
    │   └── AMEGO_API_REFERENCE.md
    └── scripts/
        ├── generate-invoice-service.py
        └── test-invoice-amounts.py
```

## FAQ

<details>
<summary><b>Do all platforms use the same SKILL.md?</b></summary>

Yes. All 14 supported platforms follow the Agent Skills standard, sharing the same SKILL.md file.
</details>

<details>
<summary><b>Do I need API credentials?</b></summary>

Yes. Apply for merchant ID and API keys from your chosen provider. All three offer test environments with test accounts included in the documentation.
</details>

<details>
<summary><b>Can I support multiple providers?</b></summary>

Yes. Use the Service Factory Pattern to switch between providers dynamically.
</details>

<details>
<summary><b>The skill isn't loading?</b></summary>

1. Verify SKILL.md exists in the correct directory
2. Check YAML frontmatter is valid
3. Restart your AI assistant
4. Try `/taiwan-invoice` command directly
</details>

## Contributing

```bash
# 1. Clone the repository
git clone https://github.com/Moksa1123/taiwan-invoice.git
cd taiwan-invoice

# 2. Create feature branch
git checkout -b feature/your-feature-name

# 3. Make changes in taiwan-invoice/ (Source of Truth)

# 4. Test
python taiwan-invoice/scripts/test-invoice-amounts.py

# 5. Commit and push
git commit -m "feat: description"
git push -u origin feature/your-feature-name
```

The CLI automatically bundles content from `taiwan-invoice/` during build.

## License

This project is licensed under the [MIT License](LICENSE).
