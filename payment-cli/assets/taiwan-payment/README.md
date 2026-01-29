<h1 align="center">taiwan-payment-skill</h1>

<h3 align="center">台灣金流 AI 開發技能包</h3>

<p align="center">
  <strong>支援 ECPay 綠界 · NewebPay 藍新 · PAYUNi 統一</strong>
</p>

<p align="center">
  <a href="https://www.npmjs.com/package/taiwan-payment-skill"><img src="https://img.shields.io/npm/v/taiwan-payment-skill?style=flat-square&logo=npm" alt="npm version"></a>
  <a href="https://www.npmjs.com/package/taiwan-payment-skill"><img src="https://img.shields.io/npm/dm/taiwan-payment-skill?style=flat-square&label=downloads" alt="npm downloads"></a>
  <img src="https://img.shields.io/badge/node-%3E%3D18-339933?style=flat-square&logo=node.js&logoColor=white" alt="Node.js">
  <img src="https://img.shields.io/badge/platforms-14-blue?style=flat-square" alt="14 Platforms">
  <a href="https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/LICENSE"><img src="https://img.shields.io/github/license/Moksa1123/taiwan-ecommerce-toolkit?style=flat-square" alt="License"></a>
</p>

<p align="center">
  <a href="https://paypal.me/cccsubcom"><img src="https://img.shields.io/badge/PayPal-支持開發-00457C?style=for-the-badge&logo=paypal&logoColor=white" alt="PayPal"></a>
</p>

---

## 安裝

```bash
npm install -g taiwan-payment-skill
```

---

## 使用方式

```bash
# 進入專案目錄
cd /path/to/your/project

# 選擇你的 AI 助手
taiwan-payment init --ai claude        # Claude Code
taiwan-payment init --ai cursor        # Cursor
taiwan-payment init --ai windsurf      # Windsurf
taiwan-payment init --ai copilot       # GitHub Copilot
taiwan-payment init --ai antigravity   # Antigravity
taiwan-payment init --ai all           # 全部安裝
```

<details>
<summary>完整平台列表</summary>

```bash
taiwan-payment init --ai kiro          # Kiro (AWS)
taiwan-payment init --ai codex         # Codex CLI (OpenAI)
taiwan-payment init --ai qoder         # Qoder
taiwan-payment init --ai roocode       # Roo Code
taiwan-payment init --ai gemini        # Gemini CLI
taiwan-payment init --ai trae          # Trae (ByteDance)
taiwan-payment init --ai opencode      # OpenCode
taiwan-payment init --ai continue      # Continue
taiwan-payment init --ai codebuddy     # CodeBuddy (Tencent)
```

</details>

---

## 其他指令

```bash
taiwan-payment list         # 列出支援平台
taiwan-payment info         # 顯示技能資訊
taiwan-payment versions     # 列出可用版本
taiwan-payment update       # 檢查更新
```

### 選項

```bash
taiwan-payment init --force     # 覆蓋現有檔案
taiwan-payment init --global    # 安裝到全域目錄（所有專案共用）
```

### 全域安裝

使用 `--global` 可將技能安裝到使用者目錄，讓所有專案都能使用：

```bash
taiwan-payment init --ai cursor --global       # ~/.cursor/skills/taiwan-payment/
taiwan-payment init --ai claude --global       # ~/.claude/skills/taiwan-payment/
taiwan-payment init --ai antigravity --global  # ~/.gemini/antigravity/global_skills/taiwan-payment/
```

---

## 支援平台

| 平台 | 說明 | 啟動方式 |
|------|------|----------|
| **Claude Code** | Anthropic 官方 CLI | `/taiwan-payment` |
| **Cursor** | AI 程式編輯器 | `/taiwan-payment` |
| **Windsurf** | Codeium 編輯器 | 自動 |
| **Copilot** | GitHub Copilot | `/taiwan-payment` |
| **Antigravity** | Google AI 助手 | `/taiwan-payment` |
| **Kiro** | AWS AI 助手 | `/taiwan-payment` |
| **Codex** | OpenAI CLI | 自動 |
| **Qoder** | Qodo AI 助手 | 自動 |
| **RooCode** | VSCode 擴充 | `/taiwan-payment` |
| **Gemini CLI** | Google Gemini | 自動 |
| **Trae** | ByteDance AI | 自動 |
| **OpenCode** | 開源 AI 助手 | 自動 |
| **Continue** | 開源 AI 助手 | 自動 |
| **CodeBuddy** | Tencent AI | 自動 |

---

## 金流服務商

| 服務商 | 加密方式 | API 風格 | 特點 |
|--------|---------|---------|------|
| **ECPay 綠界** | URL Encode + SHA256 | Form POST | 市佔率最高，穩定性佳 |
| **NewebPay 藍新** | AES-256-CBC + SHA256 | Form POST + AES | 支援最多支付方式 (13 種) |
| **PAYUNi 統一** | AES-256-GCM + SHA256 | RESTful JSON | RESTful 設計，API 現代化 |

---

## 付款方式支援

### 信用卡支付
- 一次付清、分期付款 (3/6/12/18/24 期)
- 信用卡定期定額、信用卡記憶

### 電子錢包
- Apple Pay、Google Pay、Samsung Pay
- LINE Pay、台灣 Pay

### 轉帳支付
- 網路 ATM、ATM 虛擬帳號

### 超商支付
- 超商代碼、超商條碼

### 其他
- TWQR、BNPL 無卡分期、AFTEE 先享後付

---

## 智能工具

安裝後包含以下 Python 工具（純 Python，無需外部依賴）：

```bash
# BM25 搜索引擎 - 搜索錯誤碼、欄位映射、付款方式
python scripts/search.py "10100058" --domain error
python scripts/search.py "信用卡" --domain payment_method
python scripts/search.py "CheckMacValue" --domain troubleshoot

# 智能推薦系統 - 根據需求推薦金流服務商
python scripts/recommend.py "高交易量 電商 穩定"
python scripts/recommend.py "多元支付 LINE Pay Apple Pay"

# 連線測試工具 - 測試 API 連線
python scripts/test_payment.py ecpay
python scripts/test_payment.py all
```

### 搜索域

- `provider` - 服務商比較
- `operation` - API 操作端點
- `error` - 錯誤碼查詢
- `field` - 欄位映射
- `payment_method` - 付款方式
- `troubleshoot` - 疑難排解
- `reasoning` - 推薦決策規則

---

## 功能特色

- 完整 API 文檔 (ECPay, NewebPay, PAYUNi)
- BM25 搜索引擎
- 智能推薦系統
- 9 組完整代碼範例 (TypeScript/Python)
- 7 個 CSV 數據檔 (易於維護)
- 加密實作指南 (SHA256, AES-CBC, AES-GCM)
- 16 個疑難排解案例

---

## 授權

[MIT License](https://github.com/Moksa1123/taiwan-payment/blob/main/LICENSE)

---

<p align="center">
  <sub>Made by <strong>Moksa</strong></sub><br>
  <sub>service@moksaweb.com</sub>
</p>
