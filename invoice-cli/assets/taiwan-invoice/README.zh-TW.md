# taiwan-invoice

串接台灣電子發票 API 的 Claude skill：開立、作廢、折讓、列印，以及載具與捐贈碼檢查，內容依各家官方文件整理。

[![npm version](https://img.shields.io/npm/v/taiwan-invoice-skill)](https://www.npmjs.com/package/taiwan-invoice-skill)
[![License: MIT](https://img.shields.io/github/license/Moksa1123/taiwan-ecommerce-toolkit)](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/LICENSE)

[English](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/taiwan-invoice/README.md) | 繁體中文

本專案為非官方專案，與綠界（ECPay）、速買配（SmilePay）、光貿（Amego）、ezPay、立吉富（PayNow）、歐付寶（O'Pay）、紅陽（SunPay）、財政部及文中提到的其他單位都沒有關係，也未獲其背書。品牌名稱依各公司的原寫法，權利屬於各公司。

## 功能

- 涵蓋 7 家可開立發票的加值中心（ECPay、SmilePay、Amego、ezPay、PayNow、O'Pay、SunPay），另含財政部電子發票整合服務平台（大平台）的查詢。
- 讓 Claude 知道每一家的請求格式與加密方式（AES-128-CBC、AES-256-CBC、MD5、JWT），並附可執行的 Python 範例。
- 用 `scripts/search.py` 離線查詢 424 筆資料：錯誤碼、API 操作、欄位對照、稅額規則、疑難排解、選型建議。
- 產生服務骨架（`scripts/generate-invoice-service.py`），並依白話需求推薦加值中心（`scripts/recommend.py`）。
- 涵蓋 B2C 與 B2B 發票、作廢、折讓、列印、手機條碼載具、捐贈碼、POS 機批次取號。

## 適用情境

適合用在：

- 透過上述任一家開立 B2C 或 B2B 電子發票；
- 作廢發票或開立折讓；
- 檢查手機條碼、自然人憑證載具或捐贈碼；
- 查某家錯誤碼的意思，或挑選加值中心。

不適用時改用：

- 收款（信用卡、ATM、超商代碼、LINE Pay）：用 [taiwan-payment](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/tree/main/taiwan-payment)；
- 出貨、超商取貨、物流追蹤：用 [taiwan-logistics](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/tree/main/taiwan-logistics)；
- 台灣以外的發票，或自己當加值中心直接上傳大平台：不在範圍內。

## 安裝

系統需求：腳本用 Python 3，只用標準函式庫。`examples/` 的範例另外需要 `pycryptodome`（AES）和 `requests`，用 `pip install -r requirements.txt` 安裝。Node.js 18 以上只有 npx 安裝程式需要。Windows、macOS、Linux 都能用。

Claude Code plugin（一次裝好發票、金流、物流三個台灣 skill）：

```text
/plugin marketplace add Moksa1123/taiwan-ecommerce-toolkit
/plugin install taiwan-ecommerce@taiwan-ecommerce-toolkit
```

npx（把 skill 複製到目前的專案；`--ai` 也可以填 `cursor`、`codex` 等其他 AI 工具，`--global` 裝到家目錄）：

```bash
npx taiwan-invoice-skill@2.9.11 init --ai claude
```

手動複製：

```bash
git clone https://github.com/Moksa1123/taiwan-ecommerce-toolkit.git
cp -r taiwan-ecommerce-toolkit/taiwan-invoice ~/.claude/skills/
```

## 快速開始

可以這樣問 Claude：

- 「用 Python 在綠界測試環境開一張存手機條碼載具的 B2C 發票。」
- 「在 ezPay 開 B2B 發票，有買方統編，金額是未稅價。」
- 「光貿錯誤碼 3050131 是什麼意思？」

也可以在 skill 資料夾裡自己查：

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

- 資料出處：各家官方 API 文件、PDF 規格書、官方 SDK，以及財政部電子發票整合服務平台規格。每個來源都登記在 [`sources/official-sources.json`](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/sources/official-sources.json)，每筆資料都有 `doc_url` 和 `trust`。
- 自我測試：`python3 scripts/test_skill.py` 共 51 項檢查，失敗 0（2026-11-17 執行）。
- evals：計分的 12 題中，有 skill 時 Claude 答對 12 題，沒有 skill 時答對 0 題。見 [`evals/RESULTS.md`](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/taiwan-invoice/evals/RESULTS.md)。
- CI 會跑 `scripts/verify-examples.py`，把範例程式的結果和各家官方 SDK、規格書範例產生的標準答案逐位元組比對（[`tests/vectors/`](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/tree/main/tests/vectors)）。

## 限制

- SmilePay 和 Amego 沒有可執行範例，請看 `EXAMPLES.md` 和各自的 reference。
- 大平台只能查詢（載具、捐贈碼、中獎號碼），不能開立發票。
- 關貿（TradeVAN）只登記在 `data/providers.csv`，還沒有 reference。
- `data/tax-rules.csv` 的稅額公式和通用疑難排解規則是推論（`trust=推論`），還沒對到官方條文，請當建議看。
- 已知落差記在 [`data/pending.csv`](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/taiwan-invoice/data/pending.csv)。

## 目錄結構

```text
taiwan-invoice/
├── SKILL.md         # Claude 讀的說明
├── EXAMPLES.md      # 較長的程式範例
├── references/      # 每家一份 API 規格、大平台、加值中心生態
├── examples/        # 可執行的 Python 用戶端
├── data/            # search.py、recommend.py 用的 CSV；pending.csv
├── scripts/         # 查詢、推薦、產生器、測試、數字核對
└── evals/           # evals 題目、評分程式與結果
```

## 授權與作者

MIT License。作者 Moksa（[moksaweb.com](https://moksaweb.com)）。屬於 [Taiwan E-commerce Toolkit](https://github.com/Moksa1123/taiwan-ecommerce-toolkit)。
