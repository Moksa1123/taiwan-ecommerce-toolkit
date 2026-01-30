<h1 align="center">Taiwan Invoice Skill</h1>

<h3 align="center">台灣電子發票 AI 開發技能包</h3>

<p align="center">
  <strong>支援 ECPay 綠界 · SmilePay 速買配 · Amego 光貿</strong>
</p>

<p align="center">
  <a href="https://www.npmjs.com/package/taiwan-invoice-skill"><img src="https://img.shields.io/npm/v/taiwan-invoice-skill?style=flat-square&logo=npm" alt="npm version"></a>
  <a href="https://www.npmjs.com/package/taiwan-invoice-skill"><img src="https://img.shields.io/npm/dm/taiwan-invoice-skill?style=flat-square&label=downloads" alt="npm downloads"></a>
  <img src="https://img.shields.io/badge/node-%3E%3D18-339933?style=flat-square&logo=node.js&logoColor=white" alt="Node.js">
  <img src="https://img.shields.io/badge/platforms-14-blue?style=flat-square" alt="14 Platforms">
  <a href="https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/LICENSE"><img src="https://img.shields.io/github/license/Moksa1123/taiwan-ecommerce-toolkit?style=flat-square" alt="License"></a>
</p>

<p align="center">
  <a href="https://paypal.me/cccsubcom"><img src="https://img.shields.io/badge/PayPal-支持開發-00457C?style=for-the-badge&logo=paypal&logoColor=white" alt="PayPal"></a>
</p>

---

## 專案簡介

Taiwan Invoice Skill 是專為台灣電子發票整合設計的 AI 開發工具包，支援三大加值中心 (ECPay、SmilePay、Amego) 的完整 API 整合。本工具包提供企業級程式碼範例、智能搜尋引擎、錯誤處理系統與代碼生成器，協助開發團隊快速完成電子發票系統整合。

**版本:** 2.6.2
**狀態:** Production Ready

---

## 核心特色

### 企業級程式碼標準

所有 Python 範例均達到生產環境品質：

- **完整型別定義** - Dataclass 搭配 Literal、Optional、Dict 型別提示
- **專業文件規範** - 詳細的 Docstring (Args/Returns/Raises/Example)
- **嚴謹錯誤處理** - 系統化錯誤分類與自動重試機制
- **實戰測試憑證** - 包含測試環境憑證，可直接執行驗證

### 生產級 Python 範例

**ecpay-invoice-example.py**

完整的 ECPay 發票整合實作：

- B2C 二聯式發票開立 (含稅金額)
- B2B 三聯式發票開立 (未稅金額 + 稅額)
- 發票作廢 (void_invoice)
- 發票折讓 (issue_allowance)
- AES-128-CBC 完整加解密實作
- B2B 金額自動計算 (含稅轉未稅+稅額)

### 系統化錯誤處理

**error_handler.py**

完整的錯誤處理機制與自動重試策略：

- 錯誤分類系統 (6 大類別)
- ECPay/SmilePay/Amego 三家錯誤碼對照
- 自動重試裝飾器 (指數退避策略)
- 4 種重試策略 (NO_RETRY/IMMEDIATE/EXPONENTIAL_BACKOFF/LINEAR_BACKOFF)
- 詳細錯誤建議與解決方案
- 完整日誌記錄系統

### BM25 智能搜尋引擎

採用 BM25 演算法的語義搜尋系統：

```bash
python scripts/search.py "10000016" --domain error
python scripts/search.py "CheckMacValue" --domain field
python scripts/search.py "B2B 稅額計算" --domain tax
```

### 智能推薦系統

基於關鍵字權重與 BM25 評分的加值中心推薦引擎：

```bash
python scripts/recommend.py "電商平台 高交易量 系統穩定"
```

### 自動化程式碼生成器

支援 TypeScript 與 Python 雙語言輸出：

```bash
python scripts/generate-invoice-service.py ECPay --output ts
python scripts/generate-invoice-service.py SmilePay --output py
```

---

## 快速開始

### 安裝

```bash
npm install -g taiwan-invoice-skill
```

### 初始化

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

### 使用方式

安裝完成後，在 AI 助手中直接使用自然語言描述需求：

```
使用綠界測試環境產生 B2C 發票開立程式碼，金額 1050 元
建立 SmilePay B2B 發票，未稅金額 1000 元，稅額 50 元
實作 Amego 發票作廢功能，發票號碼 AB12345678
```

---

## CLI 指令

```bash
# 列出支援平台
taiwan-invoice list

# 顯示技能資訊
taiwan-invoice info

# 列出可用版本
taiwan-invoice versions

# 檢查更新
taiwan-invoice update

# 強制覆蓋安裝
taiwan-invoice init --force

# 全域安裝 (所有專案共用)
taiwan-invoice init --ai claude --global
```

---

## 支援平台

| 平台 | 說明 | 啟動方式 |
|------|------|----------|
| **Claude Code** | Anthropic 官方 CLI | `/taiwan-invoice` |
| **Cursor** | AI 程式編輯器 | `/taiwan-invoice` |
| **Windsurf** | Codeium 編輯器 | 自動載入 |
| **Copilot** | GitHub Copilot | `/taiwan-invoice` |
| **Antigravity** | Google AI 助手 | `/taiwan-invoice` |
| **Kiro** | AWS AI 助手 | `/taiwan-invoice` |
| **Codex** | OpenAI CLI | 自動載入 |
| **Qoder** | Qodo AI 助手 | 自動載入 |
| **RooCode** | VSCode 擴充 | `/taiwan-invoice` |
| **Gemini CLI** | Google Gemini | 自動載入 |
| **Trae** | ByteDance AI | 自動載入 |
| **OpenCode** | 開源 AI 助手 | 自動載入 |
| **Continue** | 開源 AI 助手 | 自動載入 |
| **CodeBuddy** | Tencent AI | 自動載入 |

---

## 加值中心支援

| 加值中心 | 加密技術 | API 風格 | 技術特點 |
|----------|----------|----------|----------|
| **ECPay 綠界** | AES-128-CBC | RESTful + Form POST | 市佔率高，文件完整 |
| **SmilePay 速買配** | URL Signature | RESTful JSON | 雙協定支援，整合簡單 |
| **Amego 光貿** | MD5 Signature | RESTful JSON (MIG 4.0) | API 設計清晰，架構現代化 |

---

## 程式碼範例

### ECPay 發票整合

```python
from ecpay_invoice import ECPayInvoiceService

service = ECPayInvoiceService(
    merchant_id='2000132',
    hash_key='ejCk326UnaZWKisg',
    hash_iv='q9jcZX8Ib9LM8wYk',
    is_test=True
)

# B2C 發票開立
response = service.issue_invoice(invoice_data)
print(f"發票號碼: {response.invoice_number}")
```

完整範例: [ecpay-invoice-example.py](examples/ecpay-invoice-example.py)

### 錯誤處理範例

```python
from error_handler import InvoiceErrorHandler, retry_on_error

# 方式 1: 查詢錯誤資訊
handler = InvoiceErrorHandler(provider='ecpay')
info = handler.get_error_info('10000016')
print(info.suggestion)
# 輸出: 檢查 B2C/B2B 金額計算

# 方式 2: 自動重試裝飾器
@retry_on_error(max_retries=3, backoff_factor=2)
def issue_invoice(data):
    # 發票開立邏輯
    # 失敗時自動重試 3 次 (1s, 2s, 4s 間隔)
    pass
```

完整範例: [error_handler.py](scripts/error_handler.py)

---

## 智能工具

所有工具皆採用純 Python 實作，無需安裝外部依賴套件。

### BM25 搜尋引擎

```bash
# 錯誤碼查詢
python scripts/search.py "10000016" --domain error

# 欄位映射搜尋
python scripts/search.py "CheckMacValue" --domain field

# 稅務規則查詢
python scripts/search.py "B2B 稅額計算" --domain tax
```

支援搜尋域:
- `provider` - 加值中心比較
- `operation` - API 操作端點
- `error` - 錯誤碼查詢
- `field` - 欄位映射
- `tax` - 稅務規則
- `troubleshoot` - 疑難排解

### 加值中心推薦系統

```bash
# 根據需求推薦加值中心
python scripts/recommend.py "電商平台 高交易量 系統穩定"
python scripts/recommend.py "整合簡單 快速上線"
python scripts/recommend.py "API 設計 現代化"
```

### 程式碼生成器

```bash
# 生成 TypeScript 服務模組
python scripts/generate-invoice-service.py ECPay --output ts > ecpay-service.ts

# 生成 Python 服務模組
python scripts/generate-invoice-service.py SmilePay --output py > smilepay-service.py
```

---

## 功能列表

### 發票開立

- B2C 二聯式發票 (一般稅額、特種稅額)
- B2B 三聯式發票 (未稅金額 + 稅額)
- 捐贈發票 (愛心碼)
- 載具發票 (手機條碼、自然人憑證)

### 發票管理

- 發票作廢 (Issue Date 當日)
- 發票折讓 (Issue Allowance)
- 發票查詢 (Query Invoice)
- 發票通知 (Notification)

### 支援項目類型

- 一般商品
- 組合商品
- 服務項目
- 贈品 (零元項目)

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

- **AES-128-CBC** - ECPay 電子發票
- **URL Signature** - SmilePay 參數簽章
- **MD5 Signature** - Amego MIG 4.0

---

## 專案結構

```
taiwan-invoice/
├── README.md                      # 本文件
├── SKILL.md                       # AI 技能文檔
├── EXAMPLES.md                    # 程式碼範例集
│
├── references/                    # API 文件
│   ├── ecpay-api.md              # ECPay API 規格
│   ├── smilepay-api.md           # SmilePay API 規格
│   └── amego-api.md              # Amego API 規格
│
├── examples/                      # 生產級 Python 範例
│   └── ecpay-invoice-example.py  # ECPay 完整範例 (500+ 行)
│
├── scripts/                       # Python 智能工具
│   ├── search.py                 # BM25 搜尋引擎
│   ├── recommend.py              # 加值中心推薦系統
│   ├── generate-invoice-service.py  # 代碼生成器
│   └── error_handler.py          # 錯誤處理系統 (300+ 行)
│
└── data/                          # CSV 數據檔
    ├── providers.csv             # 加值中心比較
    ├── operations.csv            # API 端點定義
    ├── error-codes.csv           # 錯誤碼對照表
    ├── field-mappings.csv        # 欄位映射關係
    └── tax-rules.csv             # 稅務計算規則
```

---

## 常見問題

<details>
<summary><b>是否需要申請加值中心憑證？</b></summary>

是的。需向選定的加值中心申請商店代號 (Merchant ID) 與 API 金鑰 (Hash Key/IV)。三家加值中心皆提供測試環境與測試帳號供開發使用。

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
<summary><b>如何選擇合適的加值中心？</b></summary>

**加值中心選擇建議：**

- **ECPay 綠界**: 市佔率最高，技術文件最完整，適合需要穩定性的專案
- **SmilePay 速買配**: 支援雙協定，整合流程簡化，適合需要快速上線的專案
- **Amego 光貿**: API 設計現代化，RESTful 架構清晰，適合追求技術美感的專案

可使用本工具包提供的智能推薦系統，根據專案需求自動分析推薦。

</details>

<details>
<summary><b>AI 助手無法載入技能檔案？</b></summary>

**疑難排解步驟：**

1. 確認 SKILL.md 檔案存在於正確的目錄路徑
2. 檢查檔案開頭的 YAML frontmatter 格式是否正確
3. 重新啟動 AI 編碼助手應用程式
4. 嘗試使用 `/taiwan-invoice` 斜線命令手動觸發
5. 確認 AI 助手版本支援 Skills 功能

</details>

---

## 授權

[MIT License](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/LICENSE)

---

## 相關連結

- [Taiwan Payment Skill](../taiwan-payment/README.md) - 金流整合
- [Taiwan Logistics Skill](../taiwan-logistics/README.md) - 物流串接
- [NPM Package](https://www.npmjs.com/package/taiwan-invoice-skill)
- [GitHub Repository](https://github.com/Moksa1123/taiwan-ecommerce-toolkit)

---

<p align="center">
  <sub>Made by <strong>Moksa</strong></sub><br>
  <sub>service@moksaweb.com</sub>
</p>
