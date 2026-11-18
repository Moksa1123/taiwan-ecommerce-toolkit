<h1 align="center">taiwan-invoice-skill</h1>

<h3 align="center">台灣電子發票 AI 開發技能包</h3>

<p align="center">
  <strong>開立、作廢、折讓、列印台灣電子發票，內容依各家官方文件整理</strong>
</p>

<p align="center">
  ECPay 綠界 · SmilePay 速買配 · Amego 光貿 · ezPay 簡單付 · PayNow 立吉富 · O'Pay 歐付寶 · SunPay 紅陽 · 財政部大平台
</p>

<p align="center">
  <a href="https://www.npmjs.com/package/taiwan-invoice-skill"><img src="https://img.shields.io/npm/v/taiwan-invoice-skill?style=flat-square&logo=npm" alt="npm version"></a>
  <a href="https://www.npmjs.com/package/taiwan-invoice-skill"><img src="https://img.shields.io/npm/dm/taiwan-invoice-skill?style=flat-square&label=downloads" alt="npm downloads"></a>
  <img src="https://img.shields.io/node/v/taiwan-invoice-skill?style=flat-square&logo=node.js" alt="Node.js version">
  <img src="https://img.shields.io/badge/python-3-blue?style=flat-square&logo=python&logoColor=white" alt="Python version">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/providers-9-success?style=flat-square" alt="providers">
  <img src="https://img.shields.io/badge/AI_platforms-14-blue?style=flat-square" alt="AI platforms">
  <a href="https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/LICENSE"><img src="https://img.shields.io/github/license/Moksa1123/taiwan-ecommerce-toolkit?style=flat-square" alt="License"></a>
</p>

<p align="center">
  <a href="https://paypal.me/cccsubcom"><img src="https://img.shields.io/badge/PayPal-支持開發-00457C?style=for-the-badge&logo=paypal&logoColor=white" alt="PayPal"></a>
</p>

<p align="center">
  <a href="https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/taiwan-invoice/README.md">English</a> | 繁體中文
</p>

本專案為非官方專案，與綠界（ECPay）、速買配（SmilePay）、光貿（Amego）、ezPay、立吉富（PayNow）、歐付寶（O'Pay）、紅陽（SunPay）、財政部及文中提到的其他單位都沒有關係，也未獲其背書。品牌名稱依各公司的原寫法，權利屬於各公司。

---

## 功能

| 項目 | 內容 |
|---|---|
| 服務商 | 涵蓋 7 家可開立發票的加值中心，另含財政部電子發票整合服務平台（大平台）的查詢 |
| 加密 | 每一家的請求格式與加密方式（AES-128-CBC、AES-256-CBC、MD5、JWT），附可執行的 Python 範例 |
| 離線資料 | `scripts/search.py` 離線查詢 424 筆：錯誤碼、API 操作、欄位對照、稅額規則、疑難排解、選型建議 |
| 產生器 | `scripts/generate-invoice-service.py` 產生服務骨架；`scripts/recommend.py` 依白話需求推薦加值中心 |
| 發票流程 | B2C 與 B2B 發票、作廢、折讓、列印、手機條碼載具、捐贈碼、POS 機批次取號 |

### 發票服務商

| 服務商 | 加密／認證 | 可執行範例 | 說明 |
|---|---|---|---|
| **ECPay 綠界** | AES-128-CBC + HashKey/HashIV | Python | 文件完整、有官方 SDK |
| **SmilePay 速買配** | Grvc + Verify_key | 見 `EXAMPLES.md` | 不用 AES，參數直接送 |
| **Amego 光貿** | MD5 簽章 + App Key | 見 `EXAMPLES.md` | MIG 4.0 格式、REST API |
| **ezPay 簡單付** | AES-256-CBC + SHA256 CheckCode | Python | 字軌管理、批次開立 |
| **PayNow 立吉富** | JWT Bearer Token | Python | POS 機批次取號 |
| **O'Pay 歐付寶** | MerchantID + RqHeader + AES 加密 Data | Python | 與綠界發票 API 同源架構 |
| **SunPay 紅陽** | Token 欄位 AES-128-CBC | Python | 可與紅陽金流搭配隨交易開立 |
| **財政部大平台** | AppID + APIKey，HMAC-SHA256 加簽 | — | 只做查詢／驗證（載具、捐贈碼、中獎號碼），不能開立 |
| **關貿 TradeVAN** | — | — | 只登記在 `data/providers.csv`，還沒有 reference |

可執行範例的加解密以各家官方測試向量驗證。

## 適用情境

| 要做的事 | 用哪個 |
|---|---|
| 透過上述任一家開立 B2C 或 B2B 電子發票 | 本 skill |
| 作廢發票或開立折讓 | 本 skill |
| 檢查手機條碼、自然人憑證載具或捐贈碼 | 本 skill |
| 查某家錯誤碼的意思，或挑選加值中心 | 本 skill |
| 收款（信用卡、ATM、超商代碼、LINE Pay） | [taiwan-payment](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/tree/main/taiwan-payment) |
| 出貨、超商取貨、物流追蹤 | [taiwan-logistics](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/tree/main/taiwan-logistics) |
| 台灣以外的發票，或自己當加值中心直接上傳大平台 | 不在範圍內 |

## 安裝

| 方式 | 指令 | 說明 |
|---|---|---|
| Claude Code plugin | `/plugin install taiwan-ecommerce@taiwan-ecommerce-toolkit` | 一次裝好發票、金流、物流三個台灣 skill |
| npx | `npx taiwan-invoice-skill@2.9.13 init --ai claude` | 把 skill 複製到目前的專案 |
| 手動複製 | `cp -r taiwan-invoice ~/.claude/skills/` | 先 clone 本 repo |

Claude Code plugin：

```text
/plugin marketplace add Moksa1123/taiwan-ecommerce-toolkit
/plugin install taiwan-ecommerce@taiwan-ecommerce-toolkit
```

npx（`--ai` 也可以填 `cursor`、`codex` 等其他 AI 工具，`--global` 裝到家目錄）：

```bash
npx taiwan-invoice-skill@2.9.13 init --ai claude
```

手動複製：

```bash
git clone https://github.com/Moksa1123/taiwan-ecommerce-toolkit.git
cp -r taiwan-ecommerce-toolkit/taiwan-invoice ~/.claude/skills/
```

| 系統需求 | 用途 |
|---|---|
| Python 3，只用標準函式庫 | `scripts/` |
| `pycryptodome`、`requests`（`pip install -r requirements.txt`） | `examples/` |
| Node.js 18 以上 | 只有 npx 安裝程式需要 |
| Windows、macOS、Linux | 都能用 |

### CLI 指令

| 指令 | 做什麼 |
|---|---|
| `taiwan-invoice init` | 安裝到目前的專案；沒給 `--ai` 時會問要裝給哪個 AI 工具 |
| `taiwan-invoice init --force` | 覆蓋已安裝的檔案 |
| `taiwan-invoice init --global` | 裝到家目錄 |
| `taiwan-invoice list` | 列出支援的 AI 平台 |
| `taiwan-invoice info` | 顯示技能資訊 |
| `taiwan-invoice versions` | 列出可用版本 |
| `taiwan-invoice update` | 更新到最新版 |

安裝程式支援 14 個 AI 開發工具：Claude Code · Cursor · Windsurf · Antigravity · GitHub Copilot · Kiro · Codex · Qoder · Cline · Gemini CLI · Trae · OpenCode · Continue · CodeBuddy。

## 快速開始

**Step 1.** 安裝到專案：

```bash
npx taiwan-invoice-skill@2.9.13 init --ai claude
```

**Step 2.** 直接問 Claude，例如：

```text
用 Python 在綠界測試環境開一張存手機條碼載具的 B2C 發票。
在 ezPay 開 B2B 發票，有買方統編，金額是未稅價。
光貿錯誤碼 3050131 是什麼意思？
```

**Step 3.** 也可以在 skill 資料夾裡自己查：

```bash
python3 scripts/search.py "4000004" --domain error -n 1 -f simple
```

預期輸出（節錄）：

```text
[1] Score: 7.1404
  provider: ECPay
  code: 4000004
  message_zh: 開立發票成功（觸發開立，DelayDay=0）
  category: 延後開立
  solution: 觸發開立 API 的成功碼不是 1：DelayDay>0 回 4000003、DelayDay=0 回 4000004，...
  doc_url: https://developers.ecpay.com.tw/
  trust: 官方文件
```

## 觸發詞

English: Taiwan e-invoice, ECPay invoice, B2C invoice, B2B invoice, issue invoice, void invoice, allowance, mobile barcode carrier, donation code, buyer tax ID, MOF e-invoice platform, invoice printing.

中文：電子發票串接、開立發票、作廢、折讓、載具、手機條碼、捐贈碼、統編、B2B 三聯式、B2C 二聯式、加值中心、財政部大平台、發票列印。

## 會執行與連線的內容

這個 skill 是 Markdown 文件、CSV 資料和本機 Python 腳本，不會自己把資料送到任何地方。只有在你直接執行範例檔時，才會連網。

| 腳本 | 做什麼 | 連線 | 寫入的檔案 |
|---|---|---|---|
| `scripts/search.py` | 查詢 `data/*.csv` | 無 | 無 |
| `scripts/recommend.py` | 依 `data/*.csv` 推薦加值中心 | 無 | 無 |
| `scripts/generate-invoice-service.py` | 產生某家的 TypeScript 或 Python 服務骨架 | 無 | `--output` 資料夾裡的一個程式檔（預設目前資料夾） |
| `scripts/persist.py` | 把專案的發票設定存起來，供之後的對話參考 | 無 | `--dir` 底下的 `invoice-config/MASTER.md`（預設目前資料夾） |
| `scripts/error_handler.py` | 給你的程式 import 的重試與錯誤分類工具 | 無 | 無 |
| `scripts/check_numbers.py` | 核對 `SKILL.md` 和這兩份 README 的每個數字都對得上資料 | 無 | 加 `--fix` 時改這三個檔 |
| `scripts/test_skill.py` 與其他 `test_*.py` | 自我測試，離線執行 | 無 | 無 |
| `examples/*.py` | 各家的參考用戶端 | 直接執行時，連該檔開頭設定的測試或正式環境網址 | 無 |

金鑰（商店代號、HashKey 與 HashIV、App Key、API token、大平台的 AppID 與 API key）由你在自己的程式或設定中提供，例如環境變數。repo 裡沒有任何真實金鑰；文件和腳本裡出現的測試值，是各家公開的測試環境帳號。

## 驗證方式

| 檢查 | 結果 |
|---|---|
| 資料出處 | 各家官方 API 文件、PDF 規格書、官方 SDK，以及財政部電子發票整合服務平台規格。每個來源都登記在 [`sources/official-sources.json`](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/sources/official-sources.json)，每筆資料都有 `doc_url` 和 `trust` |
| 官方文件稽核 | 最近一次 2026-11-17，紀錄在 [`references/audit-20261117.md`](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/taiwan-invoice/references/audit-20261117.md) |
| 自我測試 | `python3 scripts/test_skill.py` 共 51 項檢查，失敗 0（2026-11-17 執行） |
| evals | 計分的 12 題中，有 skill 時 Claude 答對 12 題，沒有 skill 時答對 0 題。見 [`evals/RESULTS.md`](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/taiwan-invoice/evals/RESULTS.md) |
| 範例程式 | CI 會跑 `scripts/verify-examples.py`，把範例程式的結果和各家官方 SDK、規格書範例產生的標準答案逐位元組比對（[`tests/vectors/`](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/tree/main/tests/vectors)） |

## 限制

| 限制 | 說明 |
|---|---|
| 沒有可執行範例 | SmilePay 和 Amego，請看 `EXAMPLES.md` 和各自的 reference |
| 大平台 | 只能查詢（載具、捐贈碼、中獎號碼），不能開立發票 |
| 關貿 TradeVAN | 只登記在 `data/providers.csv`，還沒有 reference |
| 推論資料 | `data/tax-rules.csv` 的稅額公式和通用疑難排解規則是推論（`trust=推論`），還沒對到官方條文，請當建議看 |
| 已知落差 | 記在 [`data/pending.csv`](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/taiwan-invoice/data/pending.csv) |

## 目錄結構

```text
taiwan-invoice/
├── SKILL.md         # Claude 讀的說明
├── EXAMPLES.md      # 較長的程式範例
├── references/      # 每家一份 API 規格、大平台、加值中心生態、稽核紀錄
├── examples/        # 可執行的 Python 用戶端
├── data/            # search.py、recommend.py 用的 CSV；pending.csv
├── scripts/         # 查詢、推薦、產生器、測試、數字核對
└── evals/           # evals 題目、評分程式與結果
```

| reference 檔 | 內容 |
|---|---|
| `ECPAY_API_REFERENCE.md`、`SMILEPAY_API_REFERENCE.md`、`AMEGO_API_REFERENCE.md`、`EZPAY_API_REFERENCE.md` | 綠界、速買配、光貿、ezPay |
| `PAYNOW_API_REFERENCE.md`、`OPAY_API_REFERENCE.md`、`SUNPAY_API_REFERENCE.md` | 立吉富、歐付寶、紅陽 |
| `MOF_EINVOICE_API_REFERENCE.md` | 財政部大平台（查詢） |
| `VAC_LANDSCAPE.md` | 加值中心生態 |
| `audit-20261117.md` | 最近一次官方文件稽核 |

## 授權與作者

MIT License（[LICENSE](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/LICENSE)）。作者 Moksa（[moksaweb.com](https://moksaweb.com)）。

本套件是 [Taiwan E-commerce Toolkit](https://github.com/Moksa1123/taiwan-ecommerce-toolkit) 的一部分：

| 套件 | 內容 |
|---|---|
| [taiwan-payment-skill](https://www.npmjs.com/package/taiwan-payment-skill) | 台灣金流 |
| [taiwan-logistics-skill](https://www.npmjs.com/package/taiwan-logistics-skill) | 台灣物流聚合商、新竹物流直連、即時配送 |
