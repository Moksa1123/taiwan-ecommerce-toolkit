<h1 align="center">Taiwan E-Commerce Integration Toolkit</h1>

<h3 align="center">台灣電商整合開發工具包</h3>

<p align="center">
  <strong>電子發票 · 金流串接 · 物流整合</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/node-%3E%3D18-339933?style=flat-square&logo=node.js&logoColor=white" alt="Node.js">
  <img src="https://img.shields.io/badge/python-3.x-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/typescript-5.x-3178C6?style=flat-square&logo=typescript&logoColor=white" alt="TypeScript">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/providers-9-success?style=flat-square" alt="9 Providers">
  <img src="https://img.shields.io/badge/platforms-14-blue?style=flat-square" alt="14 Platforms">
  <img src="https://img.shields.io/badge/quality-production--ready-green?style=flat-square" alt="Production Ready">
  <a href="LICENSE"><img src="https://img.shields.io/github/license/Moksa1123/claude-skills?style=flat-square" alt="License"></a>
</p>

<p align="center">
  <a href="https://paypal.me/cccsubcom"><img src="https://img.shields.io/badge/PayPal-支持開發-00457C?style=for-the-badge&logo=paypal&logoColor=white" alt="PayPal"></a>
</p>

---

## 專案概覽

本專案提供台灣電商生態系統的企業級整合工具包，涵蓋三大核心領域：

<table>
<tr>
<td width="33%" align="center" style="border: 2px solid #e1e4e8; padding: 20px; border-radius: 8px;">

### 電子發票整合

**taiwan-invoice-skill**

整合 3 家加值中心

ECPay · SmilePay · Amego

<p align="center">
  <a href="https://www.npmjs.com/package/taiwan-invoice-skill"><img src="https://img.shields.io/npm/v/taiwan-invoice-skill?style=flat-square&color=cb3837&logo=npm" alt="npm version"></a>
  <br>
  <a href="https://www.npmjs.com/package/taiwan-invoice-skill"><img src="https://img.shields.io/npm/dm/taiwan-invoice-skill?style=flat-square&color=cb3837" alt="npm downloads"></a>
</p>

[完整文件](taiwan-invoice/README.md)

</td>
<td width="33%" align="center" style="border: 2px solid #e1e4e8; padding: 20px; border-radius: 8px;">

### 金流串接整合

**taiwan-payment-skill**

整合 3 家金流平台

ECPay · NewebPay · PAYUNi

<p align="center">
  <a href="https://www.npmjs.com/package/taiwan-payment-skill"><img src="https://img.shields.io/npm/v/taiwan-payment-skill?style=flat-square&color=cb3837&logo=npm" alt="npm version"></a>
  <br>
  <a href="https://www.npmjs.com/package/taiwan-payment-skill"><img src="https://img.shields.io/npm/dm/taiwan-payment-skill?style=flat-square&color=cb3837" alt="npm downloads"></a>
</p>

[完整文件](taiwan-payment/README.md)

</td>
<td width="33%" align="center" style="border: 2px solid #e1e4e8; padding: 20px; border-radius: 8px;">

### 物流串接整合

**taiwan-logistics-skill**

整合 3 家物流服務

ECPay · NewebPay · PAYUNi

<p align="center">
  <a href="https://www.npmjs.com/package/taiwan-logistics-skill"><img src="https://img.shields.io/npm/v/taiwan-logistics-skill?style=flat-square&color=cb3837&logo=npm" alt="npm version"></a>
  <br>
  <a href="https://www.npmjs.com/package/taiwan-logistics-skill"><img src="https://img.shields.io/npm/dm/taiwan-logistics-skill?style=flat-square&color=cb3837" alt="npm downloads"></a>
</p>

[完整文件](taiwan-logistics/README.md)

</td>
</tr>
</table>

---

## 快速開始

### 安裝套件

```bash
# 安裝電子發票整合工具
npm install -g taiwan-invoice-skill

# 安裝金流串接整合工具
npm install -g taiwan-payment-skill

# 安裝物流串接整合工具
npm install -g taiwan-logistics-skill
```

### 專案初始化

```bash
# 進入專案目錄
cd /path/to/your/project

# 選擇 AI 編碼助手並初始化
taiwan-invoice init --ai claude      # 電子發票
taiwan-payment init --ai claude      # 金流串接
taiwan-logistics init --ai claude    # 物流串接
```

### 使用方式

安裝完成後，直接在 AI 助手中使用自然語言描述需求：

```
使用綠界測試環境產生 B2C 發票開立程式碼，金額 1050 元

建立 ECPay 信用卡付款訂單，交易金額 2500 元

查詢台北市信義區的 7-11 超商取貨點資訊
```

---

## 核心特色

### 企業級程式碼標準

所有 Python 範例程式碼均遵循嚴格的開發規範：

- 使用 Dataclass 結構搭配完整型別提示 (Literal, Optional, Dict)
- 完整的 Docstring 文件 (Args/Returns/Raises/Example)
- 完善的錯誤處理機制與中文錯誤訊息
- 附帶實際使用範例與測試環境憑證

### 智能搜尋引擎

基於 BM25 演算法的語義搜尋系統：

```bash
# 跨領域智能搜尋
python scripts/search.py "10000016" --domain error
python scripts/search.py "CheckMacValue" --domain field
python scripts/search.py "B2B 稅額計算" --domain tax
```

### 資料驅動架構

採用 CSV 檔案管理，易於維護與更新：

- providers.csv - 廠商比較資訊
- operations.csv - API 端點定義
- error-codes.csv - 錯誤碼對照表
- field-mappings.csv - 欄位映射關係
- tax-rules.csv - 稅務計算規則

### 多平台相容

支援 14 種 AI 編碼助手：

| 平台 | 啟動方式 | 平台 | 啟動方式 |
|------|----------|------|----------|
| **Claude Code** | `/taiwan-*` | **Antigravity** | `/taiwan-*` |
| **Cursor** | `/taiwan-*` | **Kiro** | `/taiwan-*` |
| **Windsurf** | 自動載入 | **Codex** | 自動載入 |
| **GitHub Copilot** | `/taiwan-*` | **Qoder** | 自動載入 |
| **RooCode** | `/taiwan-*` | **OpenCode** | 自動載入 |
| **Gemini CLI** | 自動載入 | **Continue** | 自動載入 |
| **Trae** | 自動載入 | **CodeBuddy** | 自動載入 |

---

## 專案結構

```
claude-skills/
├── README.md                      # 本文件 (總覽)
├── LICENSE
│
├── taiwan-invoice/                # 電子發票核心內容 (Source of Truth)
│   ├── README.md                  # 發票專案說明
│   ├── SKILL.md                   # AI 技能文檔
│   ├── EXAMPLES.md                # 程式碼範例
│   ├── references/                # API 文件
│   ├── scripts/                   # Python 智能工具
│   └── data/                      # CSV 數據檔
│
├── taiwan-payment/                # 金流整合核心內容 (Source of Truth)
│   ├── README.md                  # 金流專案說明
│   ├── SKILL.md                   # AI 技能文檔
│   ├── EXAMPLES.md                # 程式碼範例
│   ├── references/                # API 文件
│   ├── examples/                  # 生產級 Python 範例
│   ├── scripts/                   # Python 智能工具
│   └── data/                      # CSV 數據檔
│
├── taiwan-logistics/              # 物流串接核心內容 (Source of Truth)
│   ├── README.md                  # 物流專案說明
│   ├── SKILL.md                   # AI 技能文檔
│   ├── EXAMPLES.md                # 程式碼範例
│   ├── references/                # API 文件
│   ├── examples/                  # 生產級 Python 範例
│   ├── scripts/                   # Python 智能工具
│   └── data/                      # CSV 數據檔
│
├── invoice-cli/                   # 發票 CLI (npm: taiwan-invoice-skill)
│   ├── src/                       # TypeScript 源碼
│   ├── assets/                    # 打包資源
│   └── dist/                      # 編譯輸出
│
├── payment-cli/                   # 金流 CLI (npm: taiwan-payment-skill)
│   ├── src/                       # TypeScript 源碼
│   ├── assets/                    # 打包資源
│   └── dist/                      # 編譯輸出
│
└── logistics-cli/                 # 物流 CLI (npm: taiwan-logistics-skill)
    ├── src/                       # TypeScript 源碼
    ├── assets/                    # 打包資源
    └── dist/                      # 編譯輸出
```

---

## 廠商整合支援

### 電子發票加值中心 (3 家)

| 加值中心 | 加密技術 | 技術特點 |
|----------|----------|----------|
| **ECPay 綠界** | AES-128-CBC | 市場佔有率高，技術文件完整 |
| **SmilePay 速買配** | URL Signature | 支援雙協定，整合流程簡化 |
| **Amego 光貿** | MD5 Signature | RESTful API 設計，架構清晰 |

### 金流串接平台 (3 家)

| 金流平台 | 加密技術 | 支援付款方式 |
|----------|----------|--------------|
| **ECPay 綠界** | SHA256 CheckMacValue | 信用卡、ATM 轉帳、超商代碼、超商條碼 |
| **NewebPay 藍新** | AES-256-CBC + SHA256 | 信用卡、ATM、超商代碼、LINE Pay、Apple Pay |
| **PAYUNi 統一** | AES-256-GCM + SHA256 | 信用卡、ATM、超商代碼、AFTEE、iCash Pay |

### 物流串接服務 (3 家)

| 物流服務 | 加密技術 | 支援物流類型 |
|----------|----------|--------------|
| **ECPay 綠界** | MD5 CheckMacValue | 7-11、全家、萊爾富、OK、黑貓宅急便、新竹貨運 |
| **NewebPay 藍新** | AES-256-CBC + SHA256 | 7-11、全家、萊爾富、OK、黑貓宅急便 |
| **PAYUNi 統一** | AES-256-GCM + SHA256 | 7-11 (常溫/冷凍)、黑貓宅急便 (常溫/冷凍/冷藏) |

---

## CLI 指令

### 共通指令

```bash
# 列出支援平台
taiwan-invoice list
taiwan-payment list
taiwan-logistics list

# 顯示技能資訊
taiwan-invoice info
taiwan-payment info
taiwan-logistics info

# 檢查更新
taiwan-invoice update
taiwan-payment update
taiwan-logistics update

# 覆蓋安裝
taiwan-invoice init --force
taiwan-payment init --force
taiwan-logistics init --force
```

### 完整平台列表

```bash
# 支援所有 14 個 AI 平台
taiwan-invoice init --ai claude        # Claude Code
taiwan-invoice init --ai cursor        # Cursor
taiwan-invoice init --ai windsurf      # Windsurf
taiwan-invoice init --ai copilot       # GitHub Copilot
taiwan-invoice init --ai antigravity   # Antigravity
taiwan-invoice init --ai kiro          # Kiro (AWS)
taiwan-invoice init --ai codex         # Codex CLI
taiwan-invoice init --ai qoder         # Qoder
taiwan-invoice init --ai roocode       # Roo Code
taiwan-invoice init --ai gemini        # Gemini CLI
taiwan-invoice init --ai trae          # Trae
taiwan-invoice init --ai opencode      # OpenCode
taiwan-invoice init --ai continue      # Continue
taiwan-invoice init --ai codebuddy     # CodeBuddy
taiwan-invoice init --ai all           # 全部安裝
```

---

## Python 範例程式

### 金流串接範例

企業級程式碼實作，遵循嚴格開發規範：

- [ecpay-payment-example.py](taiwan-payment/examples/ecpay-payment-example.py) - ECPay 金流整合
- [newebpay-payment-example.py](taiwan-payment/examples/newebpay-payment-example.py) - NewebPay MPG 整合
- [payuni-payment-example.py](taiwan-payment/examples/payuni-payment-example.py) - PAYUNi 統一金流

### 物流串接範例

完整的超商物流 (CVS) 整合實作：

- [ECPay CVS Python](taiwan-logistics/EXAMPLES.md#ecpay-cvs-python) - 綠界 C2C 物流
- [newebpay-logistics-cvs-example.py](taiwan-logistics/examples/newebpay-logistics-cvs-example.py) - 藍新超商物流
- [payuni-logistics-cvs-example.py](taiwan-logistics/examples/payuni-logistics-cvs-example.py) - 統一超商物流

### 程式碼規範

所有範例皆包含：

- 完整的 Dataclass 資料結構定義
- 詳細的型別提示 (Literal, Optional, Dict[str, any])
- 專業的 Docstring 說明文件 (Args/Returns/Raises/Example)
- 完善的錯誤處理機制與中文錯誤訊息
- 測試環境憑證與使用範例
- 可直接用於生產環境的程式碼品質

---

## 開發工具

### BM25 智能搜尋引擎

基於語義搜尋技術的文件查詢系統：

```bash
# 電子發票錯誤碼查詢
python taiwan-invoice/scripts/search.py "10000016" --domain error

# 金流欄位映射查詢
python taiwan-payment/scripts/search.py "CheckMacValue" --domain field

# 物流 API 端點查詢
python taiwan-logistics/scripts/search.py "查詢物流狀態" --domain api
```

### 廠商推薦系統

根據需求自動推薦最適合的整合廠商：

```bash
# 電子發票加值中心推薦
python taiwan-invoice/scripts/recommend.py "電商平台 高交易量 系統穩定"

# 金流平台推薦
python taiwan-payment/scripts/recommend.py "整合簡單 快速上線"

# 物流服務推薦
python taiwan-logistics/scripts/recommend.py "超商取貨 溫控配送"
```

### 程式碼生成器

自動產生整合服務的程式碼模組：

```bash
# 產生發票服務模組
python taiwan-invoice/scripts/generate-invoice-service.py ECPay --output ts

# 產生金流服務模組
python taiwan-payment/scripts/generate-payment-service.py NewebPay --output py

# 產生物流服務模組
python taiwan-logistics/scripts/generate-logistics-service.py PAYUNi --output ts
```

> 所有工具皆採用純 Python 實作，無需安裝外部依賴套件

---

## 常見問題

<details>
<summary><b>是否需要申請 API 憑證？</b></summary>

是的。需向選定的廠商申請商店代號 (Merchant ID) 與 API 金鑰 (Hash Key/IV)。三個領域共 9 家廠商皆提供測試環境與測試帳號供開發使用。

</details>

<details>
<summary><b>是否支援多家廠商同時整合？</b></summary>

支援。建議採用 Service Factory Pattern 設計模式，可在執行階段動態切換不同廠商服務，提高系統彈性。

</details>

<details>
<summary><b>如何選擇合適的整合廠商？</b></summary>

**廠商選擇建議：**

- **ECPay 綠界科技**: 三個領域全面支援，整合流程最為簡便，適合需要一站式解決方案的專案
- **NewebPay 藍新金流**: 金流功能最為完整，支援多元付款方式，適合需要豐富支付選項的電商平台
- **PAYUNi 統一金流**: 物流溫控服務最完整，支援冷凍/冷藏配送，適合生鮮電商與需要溫控的產業

可使用本專案提供的智能推薦系統，根據專案需求自動分析推薦最適合的廠商。

</details>

<details>
<summary><b>AI 助手無法載入技能檔案？</b></summary>

**疑難排解步驟：**

1. 確認 SKILL.md 檔案存在於正確的目錄路徑
2. 檢查檔案開頭的 YAML frontmatter 格式是否正確
3. 重新啟動 AI 編碼助手應用程式
4. 嘗試使用 `/taiwan-*` 斜線命令手動觸發
5. 確認 AI 助手版本支援 Skills 功能

</details>

<details>
<summary><b>Python 範例程式是否可直接用於生產環境？</b></summary>

可以。所有範例程式皆為生產級品質，使用前僅需：

1. 安裝必要依賴套件：`pip install pycryptodome requests`
2. 將測試環境憑證替換為正式環境憑證
3. 依需求調整業務邏輯與錯誤處理機制
4. 進行完整的單元測試與整合測試

程式碼已包含完整的型別提示、錯誤處理與文件說明，可直接整合至專案中使用。

</details>

---

## 開發與貢獻

### Git 工作流程

```bash
# 1. Clone 專案
git clone https://github.com/Moksa1123/claude-skills.git
cd claude-skills

# 2. 建立功能分支
git checkout -b feat/your-feature

# 3. 修改對應的核心內容目錄
# - taiwan-invoice/     (發票相關)
# - taiwan-payment/     (金流相關)
# - taiwan-logistics/   (物流相關)

# 4. 同步到 CLI assets (發布前)
cp -r taiwan-invoice/* invoice-cli/assets/taiwan-invoice/
cp -r taiwan-payment/* payment-cli/assets/taiwan-payment/
cp -r taiwan-logistics/* logistics-cli/assets/taiwan-logistics/

# 5. 提交變更
git add .
git commit -m "feat: description"
git push -u origin feat/your-feature

# 6. 建立 Pull Request
gh pr create
```

### 發布流程

```bash
# 更新版本號
cd invoice-cli && npm version patch  # 或 minor, major
cd ../payment-cli && npm version patch
cd ../logistics-cli && npm version patch

# 建置
npm run build

# 測試
npm test

# 發布到 NPM
npm publish
```

---

## 授權

[MIT License](LICENSE)

---

## 相關連結

- [Taiwan Invoice Skill](taiwan-invoice/README.md) - 電子發票完整文件
- [Taiwan Payment Skill](taiwan-payment/README.md) - 金流整合完整文件
- [Taiwan Logistics Skill](taiwan-logistics/README.md) - 物流串接完整文件
- [NPM: taiwan-invoice-skill](https://www.npmjs.com/package/taiwan-invoice-skill)
- [NPM: taiwan-payment-skill](https://www.npmjs.com/package/taiwan-payment-skill)
- [NPM: taiwan-logistics-skill](https://www.npmjs.com/package/taiwan-logistics-skill)

---

<p align="center">
  <sub>Made by <strong>Moksa</strong></sub><br>
  <sub>service@moksaweb.com</sub>
</p>
