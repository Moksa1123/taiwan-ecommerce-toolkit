<h1 align="center">Taiwan Invoice Skill</h1>

<h3 align="center">台灣電子發票 AI 開發技能包</h3>

<p align="center">
  <strong>支援 ECPay 綠界 · SmilePay 速買配 · Amego 光貿</strong>
</p>

<p align="center">
  <a href="https://www.npmjs.com/package/taiwan-invoice-skill"><img src="https://img.shields.io/npm/v/taiwan-invoice-skill?style=flat-square&logo=npm" alt="npm version"></a>
  <a href="https://www.npmjs.com/package/taiwan-invoice-skill"><img src="https://img.shields.io/npm/dm/taiwan-invoice-skill?style=flat-square&label=downloads" alt="npm downloads"></a>
  <img src="https://img.shields.io/badge/node-%3E%3D18-339933?style=flat-square&logo=node.js&logoColor=white" alt="Node.js">
  <img src="https://img.shields.io/badge/python-3.x-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/typescript-5.x-3178C6?style=flat-square&logo=typescript&logoColor=white" alt="TypeScript">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/providers-3-success?style=flat-square" alt="3 Providers">
  <img src="https://img.shields.io/badge/platforms-14-blue?style=flat-square" alt="14 Platforms">
  <img src="https://img.shields.io/badge/examples-9-orange?style=flat-square" alt="9 Examples">
  <a href="https://github.com/Moksa1123/taiwan-invoice/stargazers"><img src="https://img.shields.io/github/stars/Moksa1123/taiwan-invoice?style=flat-square&logo=github" alt="GitHub stars"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/Moksa1123/taiwan-invoice?style=flat-square" alt="License"></a>
</p>

<p align="center">
  <a href="https://paypal.me/cccsubcom"><img src="https://img.shields.io/badge/PayPal-支持開發-00457C?style=for-the-badge&logo=paypal&logoColor=white" alt="PayPal"></a>
</p>

---

## 功能特色

| 項目 | 說明 |
|------|------|
| **3 大電子發票加值中心** | ECPay 綠界、SmilePay 速買配、Amego 光貿 |
| **BM25 智能搜索引擎** | 搜索 API、錯誤碼、欄位映射、稅務規則 |
| **加值中心推薦系統** | 根據需求自動推薦最適合的服務商 |
| **6 個 CSV 數據檔** | 數據驅動架構，易於維護更新 |
| **完整 API 文件** | 欄位定義、錯誤碼、測試帳號 |
| **9 組程式範例** | 涵蓋常見情境與錯誤處理 |
| **14 個 AI 平台** | Claude Code、Cursor、Windsurf、Copilot 等 |

---

## 快速安裝

```bash
# 安裝 CLI
npm install -g taiwan-invoice-skill

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

## 使用方式

### 自動模式

Claude Code、Windsurf、Antigravity 等平台會自動偵測發票相關請求：

```
幫我用綠界測試環境開立一張 1050 元的 B2C 發票
```

```
建立一個發票服務工廠，支援三家加值中心動態切換
```

### 斜線命令

Cursor、Kiro、Copilot、Roo Code 使用斜線命令：

```
/taiwan-invoice 幫我產生 SmilePay B2B 發票開立程式碼
```

---

## 金額計算規則

### B2C 發票 (二聯式 · 含稅價)

```
總金額 = 1050
SalesAmount = 1050  (直接使用)
TaxAmount   = 0     (B2C 固定為 0)
TotalAmount = 1050
```

### B2B 發票 (三聯式 · 稅前 + 稅額)

```
總金額 = 1050
TaxAmount   = round(1050 - 1050/1.05) = 50
SalesAmount = 1050 - 50 = 1000
TotalAmount = 1050

驗算: SalesAmount + TaxAmount = TotalAmount ✓
```

---

## 支援平台

| 平台 | 說明 | 啟動方式 |
|------|------|----------|
| **Claude Code** | Anthropic 官方 CLI | 自動 |
| **Cursor** | AI 程式編輯器 | `/taiwan-invoice` |
| **Windsurf** | Codeium 編輯器 | 自動 |
| **Copilot** | GitHub Copilot | `/taiwan-invoice` |
| **Antigravity** | Google AI 助手 | 自動 |
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

## 加值中心比較

| 加值中心 | 驗證方式 | 特點 |
|----------|----------|------|
| **ECPay 綠界** | AES-128-CBC 加密 | 市佔率高，文件完整 |
| **SmilePay 速買配** | URL 參數簽章 | 雙協定支援，整合簡單 |
| **Amego 光貿** | MD5 簽章 (MIG 4.0) | API 設計乾淨 |

---

## 智能工具

### 搜索引擎

```bash
# 搜索錯誤碼
python taiwan-invoice/scripts/search.py "10000016" --domain error

# 搜索欄位映射
python taiwan-invoice/scripts/search.py "MerchantID" --domain field

# 搜索稅務規則
python taiwan-invoice/scripts/search.py "B2B 稅額" --domain tax
```

### 推薦系統

```bash
# 根據需求推薦加值中心
python taiwan-invoice/scripts/recommend.py "電商 高交易量 穩定"
# → 推薦 ECPay (市佔率高，穩定性佳)

python taiwan-invoice/scripts/recommend.py "簡單 快速"
# → 推薦 SmilePay (整合最簡單)
```

### 代碼生成器

```bash
# 產生 TypeScript 服務模組
python taiwan-invoice/scripts/generate-invoice-service.py ECPay --output ts

# 產生 Python 服務模組
python taiwan-invoice/scripts/generate-invoice-service.py SmilePay --output py
```

> 純 Python 實現，無需外部依賴

---

## CLI 指令

```bash
taiwan-invoice list         # 列出支援平台
taiwan-invoice info         # 顯示技能資訊
taiwan-invoice versions     # 列出可用版本
taiwan-invoice update       # 檢查更新
taiwan-invoice init --force # 覆蓋現有檔案
```

---

## 專案結構

```
taiwan-invoice/
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── cli/                           # CLI 安裝器 (npm 套件)
│   ├── src/
│   └── assets/
└── taiwan-invoice/                # Source of Truth
    ├── SKILL.md                   # 主文件
    ├── EXAMPLES.md                # 程式範例
    ├── references/                # API 文件
    ├── data/                      # CSV 數據檔
    │   ├── providers.csv          # 加值中心比較
    │   ├── operations.csv         # API 操作端點
    │   ├── error-codes.csv        # 錯誤碼對照
    │   ├── field-mappings.csv     # 欄位映射
    │   ├── tax-rules.csv          # 稅務規則
    │   └── troubleshooting.csv    # 疑難排解
    └── scripts/                   # 智能工具
        ├── search.py              # BM25 搜索引擎
        ├── recommend.py           # 推薦系統
        └── generate-invoice-service.py
```

---

## 常見問題

<details>
<summary><b>需要 API 憑證嗎？</b></summary>

需要。請向選定的加值中心申請商店代號和 API 金鑰。三家都有提供測試環境和測試帳號。

</details>

<details>
<summary><b>可以同時支援多家加值中心嗎？</b></summary>

可以。使用 Service Factory Pattern 可動態切換不同加值中心。

</details>

<details>
<summary><b>技能沒有載入？</b></summary>

1. 確認 SKILL.md 存在於正確目錄
2. 檢查 YAML frontmatter 格式正確
3. 重啟 AI 助手
4. 嘗試 `/taiwan-invoice` 斜線命令

</details>

---

## 貢獻

```bash
# 1. Clone
git clone https://github.com/Moksa1123/taiwan-invoice.git

# 2. 建立分支
git checkout -b feat/your-feature

# 3. 修改 taiwan-invoice/ 內的檔案

# 4. 提交
git commit -m "feat: description"
git push -u origin feat/your-feature
```

---

## 授權

[MIT License](LICENSE)

---

<p align="center">
  <sub>Made by <strong>Moksa</strong></sub><br>
  <sub>service@moksaweb.com</sub>
</p>
