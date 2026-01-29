<h1 align="center">taiwan-invoice-skill</h1>

<h3 align="center">台灣電子發票 AI 開發技能包</h3>

<p align="center">
  <strong>支援 ECPay 綠界 · SmilePay 速買配 · Amego 光貿</strong>
</p>

<p align="center">
  <a href="https://www.npmjs.com/package/taiwan-invoice-skill"><img src="https://img.shields.io/npm/v/taiwan-invoice-skill?style=flat-square&logo=npm" alt="npm version"></a>
  <a href="https://www.npmjs.com/package/taiwan-invoice-skill"><img src="https://img.shields.io/npm/dm/taiwan-invoice-skill?style=flat-square&label=downloads" alt="npm downloads"></a>
  <img src="https://img.shields.io/badge/node-%3E%3D18-339933?style=flat-square&logo=node.js&logoColor=white" alt="Node.js">
  <img src="https://img.shields.io/badge/platforms-14-blue?style=flat-square" alt="14 Platforms">
  <a href="https://github.com/Moksa1123/taiwan-invoice/blob/main/LICENSE"><img src="https://img.shields.io/github/license/Moksa1123/taiwan-invoice?style=flat-square" alt="License"></a>
</p>

<p align="center">
  <a href="https://paypal.me/cccsubcom"><img src="https://img.shields.io/badge/PayPal-支持開發-00457C?style=for-the-badge&logo=paypal&logoColor=white" alt="PayPal"></a>
</p>

---

## 安裝

```bash
npm install -g taiwan-invoice-skill
```

---

## 使用方式

```bash
# 進入專案目錄
cd /path/to/your/project

# 選擇你的 AI 助手
taiwan-invoice init --ai claude        # Claude Code
taiwan-invoice init --ai cursor        # Cursor
taiwan-invoice init --ai windsurf      # Windsurf
taiwan-invoice init --ai copilot       # GitHub Copilot
taiwan-invoice init --ai antigravity   # Antigravity
taiwan-invoice init --ai all           # 全部安裝
```

<details>
<summary>完整平台列表</summary>

```bash
taiwan-invoice init --ai kiro          # Kiro (AWS)
taiwan-invoice init --ai codex         # Codex CLI (OpenAI)
taiwan-invoice init --ai qoder         # Qoder
taiwan-invoice init --ai roocode       # Roo Code
taiwan-invoice init --ai gemini        # Gemini CLI
taiwan-invoice init --ai trae          # Trae (ByteDance)
taiwan-invoice init --ai opencode      # OpenCode
taiwan-invoice init --ai continue      # Continue
taiwan-invoice init --ai codebuddy     # CodeBuddy (Tencent)
```

</details>

---

## 其他指令

```bash
taiwan-invoice list         # 列出支援平台
taiwan-invoice info         # 顯示技能資訊
taiwan-invoice versions     # 列出可用版本
taiwan-invoice update       # 檢查更新
```

### 選項

```bash
taiwan-invoice init --offline   # 跳過 GitHub 下載，使用內建資源
taiwan-invoice init --force     # 覆蓋現有檔案
taiwan-invoice init --global    # 安裝到全域目錄（所有專案共用）
```

### 全域安裝

使用 `--global` 可將技能安裝到使用者目錄，讓所有專案都能使用：

```bash
taiwan-invoice init --ai cursor --global       # ~/.cursor/skills/taiwan-invoice/
taiwan-invoice init --ai claude --global       # ~/.claude/skills/taiwan-invoice/
taiwan-invoice init --ai antigravity --global  # ~/.gemini/antigravity/global_skills/taiwan-invoice/
```

---

## 運作原理

`taiwan-invoice init` 預設會從 GitHub 下載最新版本。如果下載失敗（網路錯誤、速率限制），會自動使用 CLI 內建的資源。

使用 `--offline` 可跳過 GitHub 下載，直接使用內建資源。

---

## 支援平台

| 平台 | 說明 | 啟動方式 |
|------|------|----------|
| **Claude Code** | Anthropic 官方 CLI | `/taiwan-invoice` |
| **Cursor** | AI 程式編輯器 | `/taiwan-invoice` |
| **Windsurf** | Codeium 編輯器 | 自動 |
| **Copilot** | GitHub Copilot | `/taiwan-invoice` |
| **Antigravity** | Google AI 助手 | `/taiwan-invoice` |
| **Kiro** | AWS AI 助手 | `/taiwan-invoice` |
| **Codex** | OpenAI CLI | 自動 |
| **Qoder** | Qodo AI 助手 | 自動 |
| **RooCode** | VSCode 擴充 | `/taiwan-invoice` |
| **Gemini CLI** | Google Gemini | 自動 |
| **Trae** | ByteDance AI | 自動 |
| **OpenCode** | 開源 AI 助手 | 自動 |
| **Continue** | 開源 AI 助手 | 自動 |
| **CodeBuddy** | Tencent AI | 自動 |

---

## 加值中心

| 加值中心 | 驗證方式 | 特點 |
|----------|----------|------|
| **ECPay 綠界** | AES-128-CBC 加密 | 市佔率高，文件完整 |
| **SmilePay 速買配** | URL 參數簽章 | 雙協定支援，整合簡單 |
| **Amego 光貿** | MD5 簽章 (MIG 4.0) | API 設計乾淨 |

---

## 智能工具

安裝後包含以下 Python 工具（純 Python，無需外部依賴）：

```bash
# BM25 搜索引擎 - 搜索錯誤碼、欄位映射、稅務規則
python scripts/search.py "10000016" --domain error

# 加值中心推薦系統 - 根據需求推薦服務商
python scripts/recommend.py "電商 高交易量 穩定"

# 代碼生成器 - 生成 TypeScript/Python 服務模組
python scripts/generate-invoice-service.py ECPay --output ts
```

---

## 授權

[MIT License](https://github.com/Moksa1123/taiwan-invoice/blob/main/LICENSE)

---

<p align="center">
  <sub>Made by <strong>Moksa</strong></sub><br>
  <sub>service@moksaweb.com</sub>
</p>
