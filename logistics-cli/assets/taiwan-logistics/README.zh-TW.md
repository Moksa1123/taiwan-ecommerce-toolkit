<h1 align="center">taiwan-logistics-skill</h1>

<h3 align="center">台灣物流 AI 開發技能包</h3>

<p align="center">
  <strong>超商取貨、宅配、電子地圖選店、取貨付款與物流追蹤，內容依各家官方文件整理</strong>
</p>

<p align="center">
  ECPay · NewebPay · PAYUNi · SmilePay · PChomePay · PayNow · ezShip · HCT 直連 · Lalamove · pandago
</p>

<p align="center">
  <a href="https://www.npmjs.com/package/taiwan-logistics-skill"><img src="https://img.shields.io/npm/v/taiwan-logistics-skill?style=flat-square&logo=npm" alt="npm version"></a>
  <a href="https://www.npmjs.com/package/taiwan-logistics-skill"><img src="https://img.shields.io/npm/dm/taiwan-logistics-skill?style=flat-square&label=downloads" alt="npm downloads"></a>
  <img src="https://img.shields.io/node/v/taiwan-logistics-skill?style=flat-square&logo=node.js" alt="Node.js version">
  <img src="https://img.shields.io/badge/python-3-blue?style=flat-square&logo=python&logoColor=white" alt="Python version">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/providers-10-success?style=flat-square" alt="providers">
  <img src="https://img.shields.io/badge/AI_platforms-14-blue?style=flat-square" alt="AI platforms">
  <a href="https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/LICENSE"><img src="https://img.shields.io/github/license/Moksa1123/taiwan-ecommerce-toolkit?style=flat-square" alt="License"></a>
</p>

<p align="center">
  <a href="https://paypal.me/cccsubcom"><img src="https://img.shields.io/badge/PayPal-支持開發-00457C?style=for-the-badge&logo=paypal&logoColor=white" alt="PayPal"></a>
</p>

<p align="center">
  <a href="https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/taiwan-logistics/README.md">English</a> | 繁體中文
</p>

本專案為非官方專案，與綠界（ECPay）、藍新（NewebPay）、統一金流（PAYUNi）、速買配（SmilePay）、PChomePay 支付連、立吉富（PayNow）、台灣便利配（ezShip）、新竹物流（HCT）、Lalamove、pandago、各超商及文中提到的其他公司都沒有關係，也未獲其背書。品牌名稱依各公司的原寫法，權利屬於各公司。

---

## 功能

| 項目 | 內容 |
|---|---|
| 服務商 | 涵蓋 7 家有物流 API 的聚合商、1 家直連物流 API（新竹物流）、2 家即時配送（Lalamove、pandago） |
| 簽章與加密 | MD5 CheckMacValue、AES-256-CBC、AES-256-GCM、3DES，附可執行的 Python 範例 |
| 離線資料 | `scripts/search.py` 離線查詢 1126 筆：服務商、API 操作、物流類型、欄位對照、貨態代碼 |
| 產生器 | `scripts/generate-logistics-service.py` 輸出服務模組；`scripts/recommend.py` 依白話需求推薦物流商 |
| 物流流程 | 超商取貨（7-11、全家、萊爾富、OK）、宅配、冷鏈、電子地圖選店、取貨付款、物流追蹤 |

### 物流服務商

| 服務商 | 類型 | 簽章／認證 | 可執行範例 | 說明 |
|---|---|---|---|---|
| **ECPay 綠界** | 聚合商 | MD5 CheckMacValue | Python | 超商取貨、黑貓與中華郵政宅配 |
| **NewebPay 藍新** | 聚合商 | AES-256-CBC + SHA256 | Python | 只有超商取貨，沒有宅配 |
| **PAYUNi 統一金流** | 聚合商 | AES-256-GCM + SHA256 | Python | 7-11 常溫／冷凍、黑貓；物流單要在金流交易 API 一起建立 |
| **SmilePay 速買配** | 聚合商 | Verify_key + Mid_smilepay 加權檢核碼 | Python | `Pay_zg` 服務矩陣，含逆物流 |
| **PChomePay 支付連** | 聚合商 | Basic Auth → pcpay-token | Python | 金物流二合一，超商取貨付款 |
| **PayNow 立吉富** | 聚合商 | 3DES／ECB／Zero-Padding | Python | 產品線多，含冷凍與海外；與金流端的 AES 不同 |
| **ezShip 台灣便利配** | 聚合商 | 無簽章（綁 `su_id` 帳號） | Python | 全家、萊爾富、OK、宅配、店港澳；不含 7-11 |
| **HCT 新竹物流** | 直連物流 API | 申請後提供金鑰 | Python | 上面的聚合商都沒有新竹物流選項 |
| **Lalamove** | 即時配送 | HMAC-SHA256 簽章 | — | 先報價後下單 |
| **pandago** | 即時配送 | OAuth 2.0，以 RSA 簽 JWT assertion | — | 同城即時配送 |

### 物流類型支援矩陣

依各家官方規格整理，實際參數值見 `data/logistics-types.csv`。

| 服務商 | 7-11 | 全家 | 萊爾富 | OK | 黑貓／宅配 | 其他 |
|---|---|---|---|---|---|---|
| ECPay | B2C（含冷凍）+ C2C | B2C + C2C | B2C + C2C | C2C 已於 2026-07-01 終止 | 黑貓 | 中華郵政 |
| NewebPay | B2C + C2C | C2C | C2C | C2C | — | — |
| PAYUNi | B2C + C2C（常溫／冷凍） | — | — | — | 黑貓 | — |
| SmilePay | B2C + C2C | C2C | — | — | 黑貓，含逆物流 | C2B 超商退貨便 |
| PChomePay | 取貨付款 | 取貨付款 | 取貨付款 | — | — | — |
| PayNow | B2C + C2C（含冷凍） | B2C + C2C（含冷凍） | C2C | C2C | 黑貓宅配、到店 | 7-11 海外 |
| ezShip | — | B2C + C2C | B2C + C2C | B2C + C2C | 宅配 | 店港澳 |
| HCT 直連 | — | — | — | — | 新竹物流 | — |

## 適用情境

| 要做的事 | 用哪個 |
|---|---|
| 建置超商取貨或宅配的出貨流程 | 本 skill |
| 在結帳頁加上電子地圖選店 | 本 skill |
| 建立物流單、列印託運單、接收貨態通知 | 本 skill |
| 查物流狀態碼的意思，或挑選物流商 | 本 skill |
| 收款（包含綠界、藍新、統一金流的金流端） | [taiwan-payment](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/tree/main/taiwan-payment) |
| 開立電子發票 | [taiwan-invoice](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/tree/main/taiwan-invoice) |
| 台灣以外的物流，或沒有公開 API 的物流合約 | 不在範圍內（skill 會直接說明，不會亂猜） |

## 安裝

| 方式 | 指令 | 說明 |
|---|---|---|
| Claude Code plugin | `/plugin install taiwan-ecommerce@taiwan-ecommerce-toolkit` | 一次裝好發票、金流、物流三個台灣 skill |
| npx | `npx taiwan-logistics-skill@1.4.12 init --ai claude` | 把 skill 複製到目前的專案 |
| 手動複製 | `cp -r taiwan-logistics ~/.claude/skills/` | 先 clone 本 repo |

Claude Code plugin：

```text
/plugin marketplace add Moksa1123/taiwan-ecommerce-toolkit
/plugin install taiwan-ecommerce@taiwan-ecommerce-toolkit
```

npx（`--ai` 也可以填 `cursor`、`codex` 等其他 AI 工具，`--global` 裝到家目錄）：

```bash
npx taiwan-logistics-skill@1.4.12 init --ai claude
```

手動複製：

```bash
git clone https://github.com/Moksa1123/taiwan-ecommerce-toolkit.git
cp -r taiwan-ecommerce-toolkit/taiwan-logistics ~/.claude/skills/
```

| 系統需求 | 用途 |
|---|---|
| Python 3，只用標準函式庫 | `scripts/` |
| `pycryptodome`（AES、3DES）、`requests`（`pip install -r requirements.txt`） | `examples/` 和 `scripts/test_logistics.py` 的連線選項 |
| Node.js 18 以上 | 只有 npx 安裝程式需要 |
| Windows、macOS、Linux | 都能用 |

### CLI 指令

| 指令 | 做什麼 |
|---|---|
| `taiwan-logistics init` | 安裝到目前的專案；沒給 `--ai` 時會問要裝給哪個 AI 工具 |
| `taiwan-logistics init --force` | 覆蓋已安裝的檔案 |
| `taiwan-logistics init --global` | 裝到家目錄 |
| `taiwan-logistics list` | 列出支援的 AI 平台 |
| `taiwan-logistics info` | 顯示技能資訊 |
| `taiwan-logistics versions` | 列出可用版本 |
| `taiwan-logistics update` | 更新到最新版 |

安裝程式支援 14 個 AI 開發工具：Claude Code · Cursor · Windsurf · Antigravity · GitHub Copilot · Kiro · Codex · Qoder · Cline · Gemini CLI · Trae · OpenCode · Continue · CodeBuddy。

## 快速開始

**Step 1.** 安裝到專案：

```bash
npx taiwan-logistics-skill@1.4.12 init --ai claude
```

**Step 2.** 直接問 Claude，例如：

```text
用 Python 在結帳頁加上綠界超商取貨和電子地圖選店。
建立一筆統一金流宅配物流單，並下載託運單。
綠界物流狀態 2073 是什麼意思？
```

**Step 3.** 也可以在 skill 資料夾裡自己查：

```bash
python3 scripts/search.py "2073" --domain status --max 1
```

預期輸出（節錄）：

```text
搜索查詢: '2073' (域: status)
[1] 分數: 7.62 | 域: status
  provider: ecpay
  code: 2073
  status_zh: 包裹配達取件門市
  category: at_store
  description: 物流商：UNIMART、UNIMARTC2C、HILIFE、HILIFEC2C
  doc_url: https://developers.ecpay.com.tw/7380/
  trust: 官方文件
```

## 觸發詞

English: Taiwan logistics, CVS pickup, convenience-store pickup, store-to-store shipping, store map, home delivery, cold chain, cash on delivery, shipment tracking, logistics status code, HCT, Lalamove, on-demand delivery.

中文：物流串接、超商取貨、店到店、大宗寄倉、取貨付款、電子地圖選店、宅配、冷凍、物流狀態碼、托運單、新竹物流、即時配送。

## 會執行與連線的內容

這個 skill 是 Markdown 文件、CSV 資料和本機 Python 腳本，不會自己把資料送到任何地方。只有在你執行測試腳本的連線選項，或直接執行範例檔時，才會連網。

| 腳本 | 做什麼 | 連線 | 寫入的檔案 |
|---|---|---|---|
| `scripts/search.py` | 查詢 `data/*.csv` | 無 | 無 |
| `scripts/recommend.py` | 依 `data/*.csv` 推薦物流商 | 無 | 無 |
| `scripts/generate-logistics-service.py` | 印出某家的 Python 或 TypeScript 模組 | 無 | 無（輸出到標準輸出） |
| `scripts/test_logistics.py` | 綠界簽章的已知答案測試；預設離線 | `--live`：對綠界（`logistics-stage.ecpay.com.tw`）、藍新（`ccore.newebpay.com`）、統一金流（`sandbox-api.payuni.com.tw`）測試環境送 HEAD 請求。`--create` 與 `--query`：POST 到綠界物流測試環境 | 無 |
| `scripts/check_numbers.py` | 核對 `SKILL.md` 和這兩份 README 的每個數字都對得上資料 | 無 | 加 `--fix` 時改這三個檔 |
| `scripts/test_skill.py` | 自我測試，離線執行上面的檢查 | 無 | 無 |
| `examples/*.py` | 各家的參考用戶端 | 直接執行時，連該檔開頭設定的測試或正式環境網址 | 無 |
| `examples/store-map-integration-example.html` | 電子地圖範例頁與伺服器端程式 | 本身不連線；回呼網址是佔位字 | 無 |

金鑰（商店代號、HashKey 與 HashIV、API key 與 secret、物流商帳號）由你在自己的程式或設定中提供，例如環境變數。repo 裡沒有任何真實金鑰；文件和腳本裡出現的測試值，是各家公開的測試環境帳號。

## 驗證方式

| 檢查 | 結果 |
|---|---|
| 資料出處 | 各家官方 API 文件、PDF 規格書與 SDK。每個來源都登記在 [`sources/official-sources.json`](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/sources/official-sources.json)，每筆資料都有 `doc_url` 和 `trust` |
| 官方文件稽核 | 最近一次 2026-11-17，紀錄在 [`references/audit-20261117.md`](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/taiwan-logistics/references/audit-20261117.md) |
| 自我測試 | `python3 scripts/test_skill.py` 共 42 項檢查，失敗 0（2026-11-17 執行） |
| evals | 計分的 11 題中，有 skill 時 Claude 答對 11 題，沒有 skill 時答對 0 題。見 [`evals/RESULTS.md`](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/taiwan-logistics/evals/RESULTS.md) |
| 範例程式 | CI 會跑 `scripts/verify-examples.py`，把範例程式的結果和各家官方 SDK、規格書範例產生的標準答案逐位元組比對（[`tests/vectors/`](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/tree/main/tests/vectors)） |

## 限制

| 限制 | 說明 |
|---|---|
| 沒有公開 API 的物流業者 | 超商、黑貓、中華郵政等只登記在資料裡，讓 Claude 能直接說明；請經聚合商串接 |
| 沒有可執行範例 | Lalamove 和 pandago 只有 reference |
| 新竹物流 | 文件要向新竹物流申請後才拿得到 |
| 測試腳本 | `test_logistics.py --create` 與 `--query` 只支援綠界；藍新和統一金流要用你自己的商店帳號 |
| 已知落差 | 記在 [`data/pending.csv`](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/taiwan-logistics/data/pending.csv) |

## 目錄結構

```text
taiwan-logistics/
├── SKILL.md         # Claude 讀的說明
├── EXAMPLES.md      # 較長的程式範例
├── references/      # 每家一份 API 規格、即時配送總覽、稽核紀錄
├── examples/        # 可執行的 Python 用戶端與電子地圖範例頁
├── data/            # search.py、recommend.py 用的 CSV；pending.csv
├── scripts/         # 查詢、推薦、產生器、測試、數字核對
└── evals/           # evals 題目、評分程式與結果
```

| reference 檔 | 內容 |
|---|---|
| `ecpay-`、`payuni-`、`smilepay-`、`pchomepay-`、`paynow-`、`ezship-logistics-api.md`、`NEWEBPAY_LOGISTICS_REFERENCE.md` | 各聚合商 |
| `hct-logistics-api.md` | 新竹物流直連 API |
| `lalamove-logistics-api.md`、`ondemand-delivery.md` | Lalamove 與 pandago |
| `carrier-direct-access.md` | 沒有公開 API 的物流業者與替代路徑 |
| `implementation-guide.md` | 跨服務商實作筆記 |
| `audit-20261117.md` | 最近一次官方文件稽核 |

## 授權與作者

MIT License（[LICENSE](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/LICENSE)）。作者 Moksa（[moksaweb.com](https://moksaweb.com)）。

本套件是 [Taiwan E-commerce Toolkit](https://github.com/Moksa1123/taiwan-ecommerce-toolkit) 的一部分：

| 套件 | 內容 |
|---|---|
| [taiwan-invoice-skill](https://www.npmjs.com/package/taiwan-invoice-skill) | 台灣電子發票加值中心與財政部大平台查詢 |
| [taiwan-payment-skill](https://www.npmjs.com/package/taiwan-payment-skill) | 台灣金流 |
