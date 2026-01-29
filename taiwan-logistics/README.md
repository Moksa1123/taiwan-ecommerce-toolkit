<h1 align="center">taiwan-logistics-skill</h1>

<p align="center">台灣物流 AI 開發技能包 - 支援綠界 ECPay、藍新 NewebPay、統一 PAYUNi</p>

<p align="center">
  <a href="https://www.npmjs.com/package/taiwan-logistics-skill"><img src="https://img.shields.io/npm/v/taiwan-logistics-skill.svg" alt="npm version" /></a>
  <a href="https://www.npmjs.com/package/taiwan-logistics-skill"><img src="https://img.shields.io/npm/dm/taiwan-logistics-skill.svg" alt="npm downloads" /></a>
  <a href="https://nodejs.org"><img src="https://img.shields.io/badge/node-%3E%3D18.0.0-brightgreen.svg" alt="node version" /></a>
  <a href="#支援平台"><img src="https://img.shields.io/badge/platforms-14-blue.svg" alt="platforms" /></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT" /></a>
</p>

<p align="center">
  <a href="https://paypal.me/cccsubcom"><img src="https://img.shields.io/badge/PayPal-支持開發-00457C?style=for-the-badge&logo=paypal&logoColor=white" alt="PayPal"></a>
</p>

---

## 安裝

```bash
npm install -g taiwan-logistics-skill
```

---

## 使用方式

### 基本安裝

```bash
# 自動偵測 AI 助手
taiwan-logistics init

# 指定 AI 助手類型
taiwan-logistics init --ai claude
taiwan-logistics init --ai cursor
taiwan-logistics init --ai windsurf
```

<details>
<summary><b>完整平台列表</b></summary>

```bash
# 主流平台
taiwan-logistics init --ai claude      # Claude Code
taiwan-logistics init --ai cursor      # Cursor
taiwan-logistics init --ai windsurf    # Windsurf (Codeium)
taiwan-logistics init --ai copilot     # GitHub Copilot
taiwan-logistics init --ai antigravity # Google Antigravity

# 其他支援平台
taiwan-logistics init --ai kiro        # AWS Kiro
taiwan-logistics init --ai codex       # OpenAI Codex
taiwan-logistics init --ai qoder       # Qodo
taiwan-logistics init --ai roocode     # Roo Code
taiwan-logistics init --ai gemini      # Google Gemini CLI
taiwan-logistics init --ai trae        # ByteDance Trae
taiwan-logistics init --ai opencode    # OpenCode
taiwan-logistics init --ai continue    # Continue.dev
taiwan-logistics init --ai codebuddy   # Tencent CodeBuddy

# 安裝到所有平台
taiwan-logistics init --ai all
```

</details>

---

## 其他指令

```bash
# 列出支援的平台
taiwan-logistics list

# 顯示技能資訊
taiwan-logistics info

# 列出可用版本
taiwan-logistics versions

# 檢查更新
taiwan-logistics update
```

### 選項

- `--ai <type>` - 指定 AI 助手類型
- `--force` - 強制覆蓋現有檔案
- `--global` - 安裝到使用者全域目錄 (`~/.claude`, `~/.cursor` 等)

---

## 全域安裝

安裝到使用者目錄，所有專案共用：

```bash
taiwan-logistics init --ai claude --global
```

全域技能路徑：
- Claude Code: `~/.claude/skills/taiwan-logistics/`
- Cursor: `~/.cursor/skills/taiwan-logistics/`
- Windsurf: 不支援全域安裝

---

## 支援平台

| 平台 | 資料夾 | 啟動方式 |
|-----|-------|---------|
| **Claude Code** | `.claude` | `claude` 或瀏覽器開啟 [claude.ai/code](https://claude.ai/code) |
| **Cursor** | `.cursor` | `cursor` |
| **Windsurf** | `.windsurf` | `windsurf` |
| **GitHub Copilot** | `.github` | VS Code 擴充功能 |
| **Antigravity** | `.agent` | Google AI Studio |
| **Kiro** | `.kiro` | AWS Kiro CLI |
| **Codex** | `.codex` | OpenAI Codex |
| **Qoder** | `.qoder` | Qodo CLI |
| **Roo Code** | `.roo` | Roo Code Editor |
| **Gemini CLI** | `.gemini` | Google Gemini CLI |
| **Trae** | `.trae` | ByteDance Trae |
| **OpenCode** | `.opencode` | OpenCode Editor |
| **Continue** | `.continue` | Continue.dev VS Code 擴充功能 |
| **CodeBuddy** | `.codebuddy` | Tencent CodeBuddy |

---

## 物流服務商

| 服務商 | 加密方式 | API 風格 | 特色 |
|--------|---------|---------|------|
| **綠界 ECPay** | SHA256 | Form POST | 市佔率最高，穩定性佳，完整文檔 |
| **藍新 NewebPay** | AES-256-CBC + SHA256 | Form POST + AES | 支援多種物流方式 |
| **統一 PAYUNi** | AES-256-GCM + SHA256 | RESTful JSON | 統一集團，RESTful 設計 |

---

## 功能特色

- ✅ **完整 API 文檔** - ECPay、NewebPay、PAYUNi 詳細規格
- ✅ **代碼範例** - TypeScript/Python 完整可執行範例
- ✅ **加密實作指南** - SHA256、AES-256-CBC、AES-256-GCM
- ✅ **14 個 AI 平台** - 支援主流 AI 編程助手

---

## 物流方式支援

### 宅配
- 宅配到府、宅配貨到付款

### 超商取貨
- 7-ELEVEN 取貨、全家取貨、OK超商取貨、萊爾富取貨
- 超商取貨付款

### 其他
- 冷鏈宅配、國際物流

---

## 開發要求

- **Node.js** >= 18.0.0 (CLI 工具)
- **Python** >= 3.x (智能腳本，無外部依賴)

---

## 授權

本專案採用 [MIT License](https://opensource.org/licenses/MIT) 授權。

---

## 作者

由 [Moksa](https://github.com/Moksa1123) 開發維護。

---

## 相關專案

- [taiwan-invoice-skill](https://github.com/Moksa1123/taiwan-invoice) - 台灣電子發票整合
- [taiwan-payment-skill](https://github.com/Moksa1123/taiwan-payment) - 台灣金流整合

---

<p align="center">Made with ❤️ for Taiwan developers</p>
