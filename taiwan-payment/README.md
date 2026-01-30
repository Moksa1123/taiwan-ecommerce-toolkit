<h1 align="center">Taiwan Payment Skill</h1>

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

## 專案簡介

Taiwan Payment Skill 是專為台灣金流整合設計的 AI 開發工具包，支援三大金流平台 (ECPay、NewebPay、PAYUNi) 的完整 API 整合。本工具包提供企業級程式碼範例、BM25 智能搜尋引擎、服務商推薦系統與代碼生成器，協助開發團隊快速完成金流系統整合。

**版本:** 1.1.2
**狀態:** Production Ready

---

## 核心特色

### 企業級程式碼標準

所有 Python 範例均達到生產環境品質：

- **完整型別定義** - Dataclass 搭配 Literal、Optional、Dict 型別提示
- **專業文件規範** - 詳細的 Docstring (Args/Returns/Raises/Example)
- **嚴謹錯誤處理** - 完整的例外處理與中文錯誤訊息
- **實戰測試憑證** - 包含測試環境憑證，可直接執行驗證

### 生產級 Python 範例 (3 個)

完整的金流整合實作，支援多種付款方式：

- **ecpay-payment-example.py** - ECPay 金流整合
- **newebpay-payment-example.py** - NewebPay MPG 整合
- **payuni-payment-example.py** - PAYUNi 統一金流

### BM25 智能搜尋引擎

採用 BM25 演算法的語義搜尋系統：

```bash
python scripts/search.py "10100058" --domain error
python scripts/search.py "信用卡" --domain payment_method
python scripts/search.py "CheckMacValue" --domain troubleshoot
```

### 智能推薦系統

基於關鍵字權重與 BM25 評分的金流平台推薦引擎：

```bash
python scripts/recommend.py "高交易量 電商 穩定"
python scripts/recommend.py "多元支付 LINE Pay Apple Pay"
```

### 自動化程式碼生成器

支援 TypeScript 與 Python 雙語言輸出：

```bash
python scripts/generate-payment-service.py ECPay --output ts
python scripts/generate-payment-service.py NewebPay --output py
```

---

## 快速開始

### 安裝

```bash
npm install -g taiwan-payment-skill
```

### 初始化

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

### 使用方式

安裝完成後，在 AI 助手中直接使用自然語言描述需求：

```
建立 ECPay 信用卡付款訂單，交易金額 2500 元
使用藍新金流 MPG 整合 LINE Pay 與 Apple Pay
實作 PAYUNi 統一金流 ATM 轉帳功能
```

---

## CLI 指令

```bash
# 列出支援平台
taiwan-payment list

# 顯示技能資訊
taiwan-payment info

# 列出可用版本
taiwan-payment versions

# 檢查更新
taiwan-payment update

# 強制覆蓋安裝
taiwan-payment init --force

# 全域安裝 (所有專案共用)
taiwan-payment init --ai claude --global
```

---

## 支援平台

| 平台 | 說明 | 啟動方式 |
|------|------|----------|
| **Claude Code** | Anthropic 官方 CLI | `/taiwan-payment` |
| **Cursor** | AI 程式編輯器 | `/taiwan-payment` |
| **Windsurf** | Codeium 編輯器 | 自動載入 |
| **Copilot** | GitHub Copilot | `/taiwan-payment` |
| **Antigravity** | Google AI 助手 | `/taiwan-payment` |
| **Kiro** | AWS AI 助手 | `/taiwan-payment` |
| **Codex** | OpenAI CLI | 自動載入 |
| **Qoder** | Qodo AI 助手 | 自動載入 |
| **RooCode** | VSCode 擴充 | `/taiwan-payment` |
| **Gemini CLI** | Google Gemini | 自動載入 |
| **Trae** | ByteDance AI | 自動載入 |
| **OpenCode** | 開源 AI 助手 | 自動載入 |
| **Continue** | 開源 AI 助手 | 自動載入 |
| **CodeBuddy** | Tencent AI | 自動載入 |

---

## 金流平台支援

| 金流平台 | 加密技術 | API 風格 | 支援付款方式 |
|----------|----------|----------|--------------|
| **ECPay 綠界** | SHA256 CheckMacValue | Form POST | 信用卡、ATM、超商代碼、超商條碼 |
| **NewebPay 藍新** | AES-256-CBC + SHA256 | Form POST + AES | 信用卡、ATM、超商、LINE Pay、Apple Pay (13 種) |
| **PAYUNi 統一** | AES-256-GCM + SHA256 | RESTful JSON | 信用卡、ATM、超商、AFTEE、iCash Pay |

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

所有工具皆採用純 Python 實作，無需安裝外部依賴套件。

### BM25 搜尋引擎

```bash
# 錯誤碼查詢
python scripts/search.py "10100058" --domain error

# 付款方式搜尋
python scripts/search.py "信用卡" --domain payment_method

# 疑難排解
python scripts/search.py "CheckMacValue" --domain troubleshoot
```

支援搜尋域:
- `provider` - 金流平台比較
- `operation` - API 操作端點
- `error` - 錯誤碼查詢
- `field` - 欄位映射
- `payment_method` - 付款方式
- `troubleshoot` - 疑難排解
- `reasoning` - 推薦決策規則

### 金流平台推薦系統

```bash
# 根據需求推薦金流平台
python scripts/recommend.py "高交易量 電商 穩定"
python scripts/recommend.py "多元支付 LINE Pay Apple Pay"
python scripts/recommend.py "整合簡單 快速上線"
```

### 程式碼生成器

```bash
# 生成 TypeScript 服務模組
python scripts/generate-payment-service.py ECPay --output ts > ecpay-service.ts

# 生成 Python 服務模組
python scripts/generate-payment-service.py NewebPay --output py > newebpay-service.py
```

### 連線測試工具

```bash
# 測試 API 連線
python scripts/test_payment.py ecpay
python scripts/test_payment.py all
```

---

## 技術規格

### 系統需求

- **Node.js**: >= 18.0.0 (CLI 工具)
- **Python**: >= 3.8 (範例程式與智能工具)

### Python 依賴

```bash
# 範例程式所需依賴
pip install pycryptodome requests

# 智能工具無需外部依賴 (純 Python 標準庫)
```

### 支援的加密方式

- **SHA256 CheckMacValue** - ECPay 金流
- **AES-256-CBC + SHA256** - NewebPay 金流
- **AES-256-GCM + SHA256** - PAYUNi 金流

---

## 專案結構

```
taiwan-payment/
├── README.md                      # 本文件
├── SKILL.md                       # AI 技能文檔
├── EXAMPLES.md                    # 程式碼範例集
│
├── references/                    # API 文件
│   ├── ecpay-api.md              # ECPay API 規格
│   ├── newebpay-api.md           # NewebPay API 規格
│   └── payuni-api.md             # PAYUNi API 規格
│
├── examples/                      # 生產級 Python 範例
│   ├── ecpay-payment-example.py
│   ├── newebpay-payment-example.py
│   └── payuni-payment-example.py
│
├── scripts/                       # Python 智能工具
│   ├── search.py                 # BM25 搜尋引擎
│   ├── recommend.py              # 金流平台推薦系統
│   ├── generate-payment-service.py  # 代碼生成器
│   └── test_payment.py           # 連線測試工具
│
└── data/                          # CSV 數據檔
    ├── providers.csv             # 金流平台比較
    ├── operations.csv            # API 端點定義
    ├── error-codes.csv           # 錯誤碼對照表
    ├── field-mappings.csv        # 欄位映射關係
    ├── payment-methods.csv       # 付款方式支援
    ├── troubleshoot.csv          # 疑難排解案例
    └── reasoning.csv             # 推薦決策規則
```

---

## 常見問題

<details>
<summary><b>是否需要申請金流平台憑證？</b></summary>

是的。需向選定的金流平台申請商店代號 (Merchant ID) 與 API 金鑰 (Hash Key/IV)。三家金流平台皆提供測試環境與測試帳號供開發使用。

</details>

<details>
<summary><b>Python 範例程式是否可直接用於生產環境？</b></summary>

可以。所有範例程式皆為生產級品質，使用前僅需：

1. 安裝必要依賴套件：`pip install pycryptodome requests`
2. 將測試環境憑證替換為正式環境憑證
3. 依需求調整業務邏輯與錯誤處理機制
4. 進行完整的單元測試與整合測試

</details>

<details>
<summary><b>如何選擇合適的金流平台？</b></summary>

**金流平台選擇建議：**

- **ECPay 綠界**: 市佔率最高，穩定性最佳，適合需要可靠性的專案
- **NewebPay 藍新**: 支援付款方式最多 (13 種)，適合需要多元支付的電商平台
- **PAYUNi 統一**: RESTful API 設計現代化，適合追求技術架構清晰的專案

可使用本工具包提供的智能推薦系統，根據專案需求自動分析推薦。

</details>

<details>
<summary><b>AI 助手無法載入技能檔案？</b></summary>

**疑難排解步驟：**

1. 確認 SKILL.md 檔案存在於正確的目錄路徑
2. 檢查檔案開頭的 YAML frontmatter 格式是否正確
3. 重新啟動 AI 編碼助手應用程式
4. 嘗試使用 `/taiwan-payment` 斜線命令手動觸發
5. 確認 AI 助手版本支援 Skills 功能

</details>

---

## 授權

[MIT License](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/LICENSE)

---

## 相關連結

- [Taiwan Invoice Skill](../taiwan-invoice/README.md) - 電子發票整合
- [Taiwan Logistics Skill](../taiwan-logistics/README.md) - 物流串接
- [NPM Package](https://www.npmjs.com/package/taiwan-payment-skill)
- [GitHub Repository](https://github.com/Moksa1123/taiwan-ecommerce-toolkit)

---

<p align="center">
  <sub>Made by <strong>Moksa</strong></sub><br>
  <sub>service@moksaweb.com</sub>
</p>
