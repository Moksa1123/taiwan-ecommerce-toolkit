<h1 align="center">taiwan-payment-skill</h1>

<h3 align="center">台灣金流 AI 開發技能包</h3>

<p align="center">
  <strong>台灣金流的請求簽章、加密、付款通知、退款與錯誤碼，內容依各家官方文件整理</strong>
</p>

<p align="center">
  ECPay · NewebPay · PAYUNi · SmilePay · PChomePay · ezPay · PayNow · Shopline Payments · LINE Pay · TapPay · O'Pay · JKOPAY · SunPay · GoMyPay
</p>

<p align="center">
  <a href="https://www.npmjs.com/package/taiwan-payment-skill"><img src="https://img.shields.io/npm/v/taiwan-payment-skill?style=flat-square&logo=npm" alt="npm version"></a>
  <a href="https://www.npmjs.com/package/taiwan-payment-skill"><img src="https://img.shields.io/npm/dm/taiwan-payment-skill?style=flat-square&label=downloads" alt="npm downloads"></a>
  <img src="https://img.shields.io/node/v/taiwan-payment-skill?style=flat-square&logo=node.js" alt="Node.js version">
  <img src="https://img.shields.io/badge/python-3-blue?style=flat-square&logo=python&logoColor=white" alt="Python version">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/providers-14-success?style=flat-square" alt="providers">
  <img src="https://img.shields.io/badge/AI_platforms-14-blue?style=flat-square" alt="AI platforms">
  <a href="https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/LICENSE"><img src="https://img.shields.io/github/license/Moksa1123/taiwan-ecommerce-toolkit?style=flat-square" alt="License"></a>
</p>

<p align="center">
  <a href="https://paypal.me/cccsubcom"><img src="https://img.shields.io/badge/PayPal-支持開發-00457C?style=for-the-badge&logo=paypal&logoColor=white" alt="PayPal"></a>
</p>

<p align="center">
  <a href="https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/taiwan-payment/README.md">English</a> | 繁體中文
</p>

本專案為非官方專案，與綠界（ECPay）、藍新（NewebPay）、統一金流（PAYUNi）、LINE、TapPay、街口（JKOPAY）及文中提到的其他公司都沒有關係，也未獲其背書。品牌名稱依各公司的原寫法，權利屬於各公司。

---

## 功能

| 項目 | 內容 |
|---|---|
| 服務商 | 涵蓋 14 家台灣金流（見下表） |
| 簽章與加密 | CheckMacValue、TradeSha、AES-256-CBC、AES-256-GCM、RSA、JWT、HMAC-SHA256，附可執行的 Python 範例 |
| 離線資料 | `scripts/search.py` 離線查詢 3212 筆官方資料：錯誤碼、API 操作、欄位對照、付款方式、疑難排解 |
| 選型 | `scripts/recommend.py` 依白話需求推薦金流 |
| 付款流程 | 信用卡、ATM、超商代碼、電子支付、Apple Pay、Google Pay、TWQR、BNPL、定期定額、退款，各自對應到 `references/` 的檔案 |

### 金流服務商

| 服務商 | 簽章／認證 | 可執行範例 | 說明 |
|---|---|---|---|
| **ECPay 綠界** | SHA256 CheckMacValue | Python | 文件最完整 |
| **NewebPay 藍新** | AES-256-CBC + SHA256 | Python | MPG 整合、信用卡記憶 |
| **PAYUNi 統一金流** | AES-256-GCM + SHA256 | Python | JSON 回應；幕後 API 要綁 IP |
| **SmilePay 速買配** | Verify_key + Mid_smilepay 加權檢核碼 | Python | 不用 AES；ibon／FamiPort 繳費單 |
| **PChomePay 支付連** | Basic Auth → pcpay-token | Python | 金物流二合一；「拍錢包」是它的付款方式之一 |
| **ezPay 簡單付** | AES-256-CBC + SHA256 HashData | Python | 電子支付機構；境內 TWQR、ezPay 錢包，跨境支付寶／微信支付 |
| **PayNow 立吉富** | Bearer 私鑰（新版 API）／SHA-1 PassCode + 動態 AES-256（舊版 API） | Python | 新舊兩套 API 並行；Apple Pay |
| **Shopline Payments** | merchantId + apiKey Header，HMAC-SHA256 webhook | Python | 金額以分為單位；Redirect 與內嵌兩種模式 |
| **LINE Pay v4** | Channel ID/Secret + HMAC-SHA256 + Nonce | Python | Request → Confirm 兩段；Preapproved Pay |
| **TapPay** | Partner Key Header，Prime | Python | PCI 隔離；Card Token 重複扣款 |
| **O'Pay 歐付寶** | SHA256 CheckMacValue（與綠界同源） | — | AccountLink 銀行快付、延遲撥款 |
| **JKOPAY 街口** | api-key Header + HMAC-SHA256 digest | Python | 線上支付、POS、授權扣款（定期） |
| **SunPay 紅陽** | RSA 分段加密 + SHA256 check_value | Python | 金流、發票、超商代收 |
| **GoMyPay 萬事達金流** | 規格需向 GoMyPay 申請 | — | 完整 API 規格未公開 |

可執行範例的加解密以各家官方測試向量驗證；錯誤碼見 `data/error-codes*.csv`。

## 適用情境

| 要做的事 | 用哪個 |
|---|---|
| 建置或除錯串接上述任一家的結帳流程 | 本 skill |
| 驗證付款通知（CheckMacValue、TradeSha、HashInfo、webhook 簽章） | 本 skill |
| 查某家錯誤碼或狀態碼的意思 | 本 skill |
| 替專案挑選金流 | 本 skill |
| 開立、作廢、折讓電子發票 | [taiwan-invoice](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/tree/main/taiwan-invoice) |
| 出貨、超商取貨、電子地圖、物流追蹤（就算是綠界、藍新、統一金流的物流也一樣） | [taiwan-logistics](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/tree/main/taiwan-logistics) |
| 台灣以外的金流，或直接串銀行、卡組織 | 不在範圍內 |

## 安裝

| 方式 | 指令 | 說明 |
|---|---|---|
| Claude Code plugin | `/plugin install taiwan-ecommerce@taiwan-ecommerce-toolkit` | 一次裝好發票、金流、物流三個台灣 skill |
| npx | `npx taiwan-payment-skill@1.5.15 init --ai claude` | 把 skill 複製到目前的專案 |
| 手動複製 | `cp -r taiwan-payment ~/.claude/skills/` | 先 clone 本 repo |

Claude Code plugin：

```text
/plugin marketplace add Moksa1123/taiwan-ecommerce-toolkit
/plugin install taiwan-ecommerce@taiwan-ecommerce-toolkit
```

npx（`--ai` 也可以填 `cursor`、`codex` 等其他 AI 工具，`--global` 裝到家目錄）：

```bash
npx taiwan-payment-skill@1.5.15 init --ai claude
```

手動複製：

```bash
git clone https://github.com/Moksa1123/taiwan-ecommerce-toolkit.git
cp -r taiwan-ecommerce-toolkit/taiwan-payment ~/.claude/skills/
```

| 系統需求 | 用途 |
|---|---|
| Python 3，只用標準函式庫 | `scripts/` |
| `pycryptodome`、`requests`（`pip install -r requirements.txt`） | `examples/` 和 `scripts/test_payment.py` 的連線選項 |
| Node.js 18 以上 | 只有 npx 安裝程式需要 |
| Windows、macOS、Linux | 都能用 |

### CLI 指令

| 指令 | 做什麼 |
|---|---|
| `taiwan-payment init` | 安裝到目前的專案；沒給 `--ai` 時會問要裝給哪個 AI 工具 |
| `taiwan-payment init --force` | 覆蓋已安裝的檔案 |
| `taiwan-payment init --global` | 裝到家目錄 |
| `taiwan-payment list` | 列出支援的 AI 平台 |
| `taiwan-payment info` | 顯示技能資訊 |
| `taiwan-payment versions` | 列出可用版本 |
| `taiwan-payment update` | 更新到最新版 |

安裝程式支援 14 個 AI 開發工具：Claude Code · Cursor · Windsurf · Antigravity · GitHub Copilot · Kiro · Codex · Qoder · Cline · Gemini CLI · Trae · OpenCode · Continue · CodeBuddy。

## 快速開始

**Step 1.** 安裝到專案：

```bash
npx taiwan-payment-skill@1.5.15 init --ai claude
```

**Step 2.** 直接問 Claude，例如：

```text
用 Python 建立綠界信用卡訂單，並驗證付款通知。
藍新的 TradeInfo 解不開，padding 哪裡錯了？
要同時用 LINE Pay 和信用卡定期定額，該選哪一家？
```

**Step 3.** 也可以在 skill 資料夾裡自己查：

```bash
python3 scripts/search.py "10100058" --domain error --max 1
```

預期輸出（節錄）：

```text
搜索域: error
找到 1 筆結果
[結果 #1] 評分: 6.04
Provider            : ecpay
Code                : 10100058
Message Zh          : Pay fail（3D 驗證未完成）
Solution            : 請消費者更換瀏覽器或裝置、關閉 VPN、切換網路取得新 IP；...
Doc Url             : https://developers.ecpay.com.tw/
Trust               : 官方文件
```

## 觸發詞

English: Taiwan payment gateway, ECPay, NewebPay, PAYUNi, LINE Pay, TapPay, JKOPAY, credit card payment, ATM virtual account, CVS payment code, Apple Pay, Google Pay, TWQR, BNPL, CheckMacValue, payment notification, refund, recurring payment.

中文：金流串接、綠界、藍新、統一金流、信用卡付款、ATM 虛擬帳號、超商代碼、LINE Pay、Apple Pay、街口、CheckMacValue、TradeSha、付款通知、退款、定期定額。

## 會執行與連線的內容

這個 skill 是 Markdown 文件、CSV 資料和本機 Python 腳本，不會自己把資料送到任何地方。只有在你執行測試腳本的連線選項，或直接執行範例檔時，才會連網。

| 腳本 | 做什麼 | 連線 | 寫入的檔案 |
|---|---|---|---|
| `scripts/search.py` | 查詢 `data/*.csv` | 無 | 無 |
| `scripts/recommend.py` | 依 `data/*.csv` 推薦金流 | 無 | 無 |
| `scripts/test_payment.py` | 綠界、藍新、統一金流簽章的已知答案測試；預設離線 | `--live`：對綠界（`payment-stage.ecpay.com.tw`）、藍新（`ccore.newebpay.com`）、統一金流（`sandbox-api.payuni.com.tw`）測試環境送 HEAD 請求。`--query`：POST 到綠界測試環境的訂單查詢 | `--create`：在目前資料夾產生 `ecpay_test_<order>.html` 表單 |
| `scripts/check_numbers.py` | 核對 `SKILL.md` 和這兩份 README 的每個數字都對得上資料 | 無 | 加 `--fix` 時改這三個檔 |
| `scripts/test_skill.py` | 自我測試，離線執行上面的檢查 | 無 | 無 |
| `examples/*.py` | 各家的參考用戶端 | 直接執行時，連該檔開頭設定的測試或正式環境網址 | 無 |

金鑰（商店代號、HashKey 與 HashIV、LINE Pay Channel ID 與 Channel Secret、TapPay Partner Key、API key）由你在自己的程式或設定中提供，例如環境變數。repo 裡沒有任何真實金鑰；文件和腳本裡出現的測試值，是各家公開的測試環境帳號。

## 驗證方式

| 檢查 | 結果 |
|---|---|
| 資料出處 | 各家官方文件、PDF 規格書、官方 SDK 或外掛。每個來源都登記在 [`sources/official-sources.json`](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/sources/official-sources.json)，每筆資料都有 `doc_url` 和 `trust` |
| 官方文件稽核 | 最近一次 2026-11-17，紀錄在 [`references/audit-20261117.md`](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/taiwan-payment/references/audit-20261117.md) |
| 自我測試 | `python3 scripts/test_skill.py` 共 50 項檢查，失敗 0（2026-11-17 執行） |
| evals | 計分的 10 題中，有 skill 時 Claude 答對 10 題，沒有 skill 時答對 0 題。見 [`evals/RESULTS.md`](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/taiwan-payment/evals/RESULTS.md) |
| 範例程式 | CI 會跑 `scripts/verify-examples.py`，把範例程式的結果和各家官方 SDK、規格書範例產生的標準答案逐位元組比對（[`tests/vectors/`](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/tree/main/tests/vectors)） |

## 限制

| 限制 | 說明 |
|---|---|
| 沒有可執行範例 | O'Pay 和 GoMyPay |
| GoMyPay | 完整 API 規格未公開，要向 GoMyPay 申請 |
| JKOPAY | 最近一次稽核時文件站網域無法解析，reference 依最後保存的官方頁面整理 |
| 推論資料 | 標 `trust=推論` 的資料（推薦、疑難排解）是從官方文件推論的，請當建議看，不是業者規定 |
| 已知落差 | 記在 [`data/pending.csv`](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/taiwan-payment/data/pending.csv) |

## 目錄結構

```text
taiwan-payment/
├── SKILL.md         # Claude 讀的說明
├── EXAMPLES.md      # 較長的程式範例
├── references/      # 每家一份 API 規格，另有稽核紀錄
├── examples/        # 可執行的 Python 用戶端
├── data/            # search.py、recommend.py 用的 CSV；pending.csv
├── scripts/         # 查詢、推薦、測試、數字核對
└── evals/           # evals 題目、評分程式與結果
```

| reference 檔 | 內容 |
|---|---|
| `ecpay-`、`newebpay-`、`payuni-`、`smilepay-`、`pchomepay-payment-api.md` | 綠界、藍新、統一金流、速買配、PChomePay 支付連 |
| `ezpay-`、`paynow-`、`shopline-`、`linepay-`、`tappay-payment-api.md` | ezPay、立吉富、Shopline Payments、LINE Pay、TapPay |
| `opay-`、`jkopay-`、`sunpay-`、`gomypay-payment-api.md` | 歐付寶、街口、紅陽、GoMyPay |
| `twqr-ewallet-landscape.md` | 電子支付與 TWQR 生態 |
| `implementation-guide.md` | 跨服務商實作筆記 |
| `audit-20261117.md` | 最近一次官方文件稽核 |

## 授權與作者

MIT License（[LICENSE](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/LICENSE)）。作者 Moksa（[moksaweb.com](https://moksaweb.com)）。

本套件是 [Taiwan E-commerce Toolkit](https://github.com/Moksa1123/taiwan-ecommerce-toolkit) 的一部分：

| 套件 | 內容 |
|---|---|
| [taiwan-invoice-skill](https://www.npmjs.com/package/taiwan-invoice-skill) | 台灣電子發票加值中心與財政部大平台查詢 |
| [taiwan-logistics-skill](https://www.npmjs.com/package/taiwan-logistics-skill) | 台灣物流聚合商、新竹物流直連、即時配送 |
