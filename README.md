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
  <a href="LICENSE"><img src="https://img.shields.io/github/license/Moksa1123/taiwan-ecommerce-toolkit?style=flat-square" alt="License"></a>
</p>

<p align="center">
  <a href="https://paypal.me/cccsubcom"><img src="https://img.shields.io/badge/PayPal-支持開發-00457C?style=for-the-badge&logo=paypal&logoColor=white" alt="PayPal"></a>
</p>

---

## 專案概覽

Taiwan E-Commerce Toolkit 是專為台灣電商生態系統設計的企業級整合開發工具包，提供完整的電子發票、金流串接、物流整合解決方案。本工具包整合台灣三大領域共 9 家主流服務商，搭配智能開發工具與生產級程式碼範例，協助開發團隊快速完成電商系統整合。

**版本資訊:** v2.0.0 Complete Edition
**發布日期:** 2026-01-30
**狀態:** Production Ready

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

## 核心特色

### 企業級程式碼標準

所有程式碼範例均達到生產環境品質標準：

- **完整型別定義** - Python Dataclass 搭配 Literal、Optional、Dict 型別提示
- **專業文件規範** - 詳細的 Docstring 文件 (Args/Returns/Raises/Example)
- **嚴謹錯誤處理** - 系統化錯誤分類與自動重試機制
- **實戰測試憑證** - 包含測試環境憑證，可直接執行驗證
- **可維護架構** - 遵循 SOLID 原則，易於擴展與維護

### BM25 智能搜尋引擎

採用 BM25 演算法實作的語義搜尋系統，支援跨領域智能查詢：

```bash
# 錯誤碼查詢
python scripts/search.py "10000016" --domain error

# 欄位映射搜尋
python scripts/search.py "CheckMacValue" --domain field

# 稅務規則查詢
python scripts/search.py "B2B 稅額計算" --domain tax
```

### 智能推薦系統

基於關鍵字權重與 BM25 評分的服務商推薦引擎：

```bash
# 發票加值中心推薦
python taiwan-invoice/scripts/recommend.py "電商平台 高交易量 系統穩定"

# 金流平台推薦
python taiwan-payment/scripts/recommend.py "整合簡單 快速上線 多元支付"

# 物流服務推薦
python taiwan-logistics/scripts/recommend.py "超商取貨 溫控配送 冷凍宅配"
```

### 自動化程式碼生成器

支援 TypeScript 與 Python 雙語言輸出的程式碼生成工具：

```bash
# 生成發票服務模組
python taiwan-invoice/scripts/generate-invoice-service.py ECPay --output ts

# 生成金流服務模組
python taiwan-payment/scripts/generate-payment-service.py NewebPay --output py

# 生成物流服務模組
python taiwan-logistics/scripts/generate-logistics-service.py PAYUNi --output ts
```

### 資料驅動架構

採用 CSV 檔案管理核心數據，便於維護與更新：

- **providers.csv** - 服務商比較資訊
- **operations.csv** - API 端點定義
- **error-codes.csv** - 錯誤碼對照表
- **field-mappings.csv** - 欄位映射關係
- **tax-rules.csv** - 稅務計算規則

### 系統化錯誤處理

完整的錯誤處理機制與自動重試策略：

- **錯誤分類** - 6 大類別 (驗證/認證/權限/業務邏輯/網路/伺服器)
- **自動重試** - 4 種重試策略 (NO_RETRY/IMMEDIATE/EXPONENTIAL_BACKOFF/LINEAR_BACKOFF)
- **智能建議** - 針對性錯誤解決方案
- **詳細日誌** - 完整的錯誤追蹤記錄

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

<details>
<summary>完整平台列表</summary>

```bash
# 支援所有 14 個 AI 平台
taiwan-invoice init --ai claude        # Claude Code
taiwan-invoice init --ai cursor        # Cursor
taiwan-invoice init --ai windsurf      # Windsurf
taiwan-invoice init --ai copilot       # GitHub Copilot
taiwan-invoice init --ai antigravity   # Antigravity
taiwan-invoice init --ai kiro          # Kiro (AWS)
taiwan-invoice init --ai codex         # Codex CLI (OpenAI)
taiwan-invoice init --ai qoder         # Qoder
taiwan-invoice init --ai roocode       # Roo Code
taiwan-invoice init --ai gemini        # Gemini CLI
taiwan-invoice init --ai trae          # Trae (ByteDance)
taiwan-invoice init --ai opencode      # OpenCode
taiwan-invoice init --ai continue      # Continue
taiwan-invoice init --ai codebuddy     # CodeBuddy (Tencent)
taiwan-invoice init --ai all           # 全部安裝
```

</details>

### 使用方式

安裝完成後，在 AI 助手中使用自然語言描述需求：

```
使用綠界測試環境產生 B2C 發票開立程式碼，金額 1050 元

建立 ECPay 信用卡付款訂單，交易金額 2500 元

查詢台北市信義區的 7-11 超商取貨點資訊
```

---

## 專案結構

```
taiwan-ecommerce-toolkit/
├── README.md                      # 本文件 (總覽)
├── LICENSE                        # MIT 授權
├── CLAUDE.md                      # Claude Code 專案指引
│
├── taiwan-invoice/                # 電子發票核心內容 (Source of Truth)
│   ├── README.md                  # 發票專案說明
│   ├── SKILL.md                   # AI 技能文檔
│   ├── EXAMPLES.md                # 程式碼範例
│   ├── references/                # API 文件
│   ├── examples/                  # 生產級 Python 範例
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

| 加值中心 | 加密技術 | 技術特點 | API 風格 |
|----------|----------|----------|----------|
| **ECPay 綠界** | AES-128-CBC | 市場佔有率高，技術文件完整 | RESTful + Form POST |
| **SmilePay 速買配** | URL Signature | 支援雙協定，整合流程簡化 | RESTful JSON |
| **Amego 光貿** | MD5 Signature | API 設計清晰，架構現代化 | RESTful JSON (MIG 4.0) |

### 金流串接平台 (3 家)

| 金流平台 | 加密技術 | 支援付款方式 | 技術特點 |
|----------|----------|--------------|----------|
| **ECPay 綠界** | SHA256 CheckMacValue | 信用卡、ATM、超商代碼、超商條碼 | 市佔率最高，穩定性佳 |
| **NewebPay 藍新** | AES-256-CBC + SHA256 | 信用卡、ATM、超商、LINE Pay、Apple Pay | 支援付款方式最多 (13 種) |
| **PAYUNi 統一** | AES-256-GCM + SHA256 | 信用卡、ATM、超商、AFTEE、iCash Pay | RESTful 設計，API 現代化 |

### 物流串接服務 (3 家)

| 物流服務 | 加密技術 | 支援物流類型 | 技術特點 |
|----------|----------|--------------|----------|
| **ECPay 綠界** | MD5 CheckMacValue | 7-11、全家、萊爾富、OK、黑貓、新竹貨運 | 市佔率最高，穩定性佳 |
| **NewebPay 藍新** | AES-256-CBC + SHA256 | 7-11、全家、萊爾富、OK、黑貓宅急便 | 整合流程完整 |
| **PAYUNi 統一** | AES-256-GCM + SHA256 | 7-11 (常溫/冷凍)、黑貓 (常溫/冷凍/冷藏) | 支援溫控配送，適合生鮮電商 |

---

## 多平台支援

支援 14 種 AI 編碼助手平台，涵蓋主流開發工具：

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

---

## Python 範例程式

### 電子發票範例

生產級 ECPay 發票整合實作：

- **ecpay-invoice-example.py**
  - B2C 二聯式發票開立
  - B2B 三聯式發票開立
  - 發票作廢 (void_invoice)
  - 發票折讓 (issue_allowance)
  - AES-128-CBC 完整加解密
  - B2B 金額自動計算 (含稅轉未稅+稅額)

### 金流串接範例

完整的金流整合實作，遵循企業級開發規範：

- **ecpay-payment-example.py** - ECPay 金流整合 (信用卡、ATM、超商代碼)
- **newebpay-payment-example.py** - NewebPay MPG 整合 (多元支付)
- **payuni-payment-example.py** - PAYUNi 統一金流 (RESTful API)

### 物流串接範例

完整的超商物流 (CVS) 與宅配整合實作：

- **ecpay-logistics-cvs-example.py** - 綠界 C2C 物流
- **newebpay-logistics-cvs-example.py** - 藍新超商物流
- **payuni-logistics-cvs-example.py** - 統一超商物流
- **store-map-integration-example.html** - 門市地圖整合

### 程式碼規範

所有範例皆包含：

- 完整的 Dataclass 資料結構定義
- 詳細的型別提示 (Literal, Optional, Dict[str, any])
- 專業的 Docstring 說明文件
- 完善的錯誤處理機制與中文錯誤訊息
- 測試環境憑證與使用範例
- 可直接用於生產環境的程式碼品質

---

## 智能開發工具

所有工具皆採用純 Python 實作，無需安裝外部依賴套件。

### BM25 搜尋引擎

```bash
# 電子發票錯誤碼查詢
python taiwan-invoice/scripts/search.py "10000016" --domain error

# 金流欄位映射查詢
python taiwan-payment/scripts/search.py "CheckMacValue" --domain field

# 物流 API 端點查詢
python taiwan-logistics/scripts/search.py "查詢物流狀態" --domain api
```

### 服務商推薦系統

```bash
# 電子發票加值中心推薦
python taiwan-invoice/scripts/recommend.py "電商平台 高交易量 系統穩定"

# 金流平台推薦
python taiwan-payment/scripts/recommend.py "整合簡單 快速上線"

# 物流服務推薦
python taiwan-logistics/scripts/recommend.py "超商取貨 溫控配送"
```

### 程式碼生成器

```bash
# 產生發票服務模組
python taiwan-invoice/scripts/generate-invoice-service.py ECPay --output ts

# 產生金流服務模組
python taiwan-payment/scripts/generate-payment-service.py NewebPay --output py

# 產生物流服務模組
python taiwan-logistics/scripts/generate-logistics-service.py PAYUNi --output ts
```

### 系統化錯誤處理

```python
from error_handler import InvoiceErrorHandler, retry_on_error

# 查詢錯誤資訊
handler = InvoiceErrorHandler(provider='ecpay')
info = handler.get_error_info('10000016')
print(info.suggestion)

# 自動重試裝飾器
@retry_on_error(max_retries=3, backoff_factor=2)
def issue_invoice(data):
    # 失敗時自動重試 3 次 (1s, 2s, 4s 間隔)
    pass
```

---

## 常見問題

<details>
<summary><b>是否需要申請 API 憑證？</b></summary>

是的。需向選定的服務商申請商店代號 (Merchant ID) 與 API 金鑰 (Hash Key/IV)。三個領域共 9 家服務商皆提供測試環境與測試帳號供開發使用。

</details>

<details>
<summary><b>是否支援多家服務商同時整合？</b></summary>

支援。建議採用 Service Factory Pattern 設計模式，可在執行階段動態切換不同服務商服務，提高系統彈性。

</details>

<details>
<summary><b>如何選擇合適的整合服務商？</b></summary>

**服務商選擇建議：**

- **ECPay 綠界科技**: 三個領域全面支援，整合流程最為簡便，適合需要一站式解決方案的專案
- **NewebPay 藍新金流**: 金流功能最為完整，支援多元付款方式，適合需要豐富支付選項的電商平台
- **PAYUNi 統一金流**: 物流溫控服務最完整，支援冷凍/冷藏配送，適合生鮮電商與需要溫控的產業

可使用本專案提供的智能推薦系統，根據專案需求自動分析推薦最適合的服務商。

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

## 技術規格

### 系統需求

- **Node.js**: >= 18.0.0 (CLI 工具)
- **Python**: >= 3.8 (範例程式與智能工具)
- **TypeScript**: >= 5.0 (程式碼生成器輸出)

### Python 依賴

```bash
# 範例程式所需依賴
pip install pycryptodome requests

# 智能工具無需外部依賴 (純 Python 標準庫)
```

### 支援的加密方式

- **AES-128-CBC** - ECPay 電子發票
- **AES-256-CBC** - NewebPay 金流/物流
- **AES-256-GCM** - PAYUNi 金流/物流
- **SHA256** - 所有服務商的 CheckMacValue
- **MD5** - Amego 發票、ECPay 物流

---

## 開發與貢獻

### Git 工作流程

```bash
# 1. Clone 專案
git clone https://github.com/Moksa1123/taiwan-ecommerce-toolkit.git
cd taiwan-ecommerce-toolkit

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
- [GitHub Repository](https://github.com/Moksa1123/taiwan-ecommerce-toolkit)

---

<p align="center">
  <sub>Made by <strong>Moksa</strong></sub><br>
  <sub>service@moksaweb.com</sub>
</p>
