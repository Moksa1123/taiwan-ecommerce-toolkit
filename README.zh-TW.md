# Taiwan E-commerce Toolkit

台灣電子發票、金流、物流 API 串接用的 agent skill，內容依各家服務商的官方文件整理。

[![License: MIT](https://img.shields.io/github/license/Moksa1123/taiwan-ecommerce-toolkit?style=flat-square)](LICENSE)
[![npm taiwan-invoice-skill](https://img.shields.io/npm/v/taiwan-invoice-skill?style=flat-square&label=taiwan-invoice-skill)](https://www.npmjs.com/package/taiwan-invoice-skill)
[![npm taiwan-payment-skill](https://img.shields.io/npm/v/taiwan-payment-skill?style=flat-square&label=taiwan-payment-skill)](https://www.npmjs.com/package/taiwan-payment-skill)
[![npm taiwan-logistics-skill](https://img.shields.io/npm/v/taiwan-logistics-skill?style=flat-square&label=taiwan-logistics-skill)](https://www.npmjs.com/package/taiwan-logistics-skill)

[English](README.md)

> 本專案為非官方的社群專案，與綠界、藍新、統一金流、LINE、TapPay、街口等文中提到的公司均無關聯，也未受其認可或贊助。各產品名稱屬於其所有者。

## 功能

整個 repo 是一個 Claude plugin（`taiwan-ecommerce`），內含三個 skill。每個 skill 讓 AI 助手知道服務商 API 的實際規則，並附可在本機查詢的工具。

- **taiwan-invoice**：台灣電子發票的開立、作廢、折讓（綠界、速買配、光貿、ezPay、PayNow、歐付寶、紅陽），以及財政部大平台的載具、捐贈碼查詢。
- **taiwan-payment**：金流與電子支付（綠界、藍新、統一金流、速買配、PChomePay、ezPay、PayNow、SHOPLINE Payments、LINE Pay、TapPay、歐付寶、街口、紅陽、GoMyPay）的結帳、付款通知、退款、簽章。
- **taiwan-logistics**：超商取貨、宅配、低溫、電子地圖選店、即時配送，經聚合商或物流業者直連 API。
- 每個 skill 都有可搜尋的 CSV 資料（端點、欄位、錯誤碼）、以官方測試向量驗證過的可執行範例，以及待確認事項清單。

## 適用情境

適用：撰寫或除錯與台灣電子發票、金流、物流服務商串接的程式，例如做結帳流程、驗證 `CheckMacValue` 或 `TradeSha`、處理付款通知、開立或作廢發票、建立物流單、查錯誤碼。

不適用：一般會計、報稅，或台灣以外的服務商。本專案不能取代與服務商簽約，正式環境的金鑰要向服務商申請。

## 安裝

Claude plugin（Claude Code；通過審核後也可從 Claude 目錄加入）：

```
/plugin marketplace add Moksa1123/taiwan-ecommerce-toolkit
/plugin install taiwan-ecommerce@taiwan-ecommerce-toolkit
```

npx，用於其他 AI 編碼工具或只裝單一 skill（請指定版本，版本見上方 npm 徽章）：

```bash
npx taiwan-payment-skill@1.5.15 init
```

手動複製：把需要的 skill 資料夾放到 AI 助手讀取 skill 的位置，例如：

```bash
git clone https://github.com/Moksa1123/taiwan-ecommerce-toolkit.git
cp -r taiwan-ecommerce-toolkit/taiwan-payment ~/.claude/skills/
```

系統需求：內附腳本需要 Python 3（只用標準函式庫）；AES 範例需要 `pycryptodome`；Node.js 18 以上只有 npx 安裝程式需要。Windows、macOS、Linux 都可使用。

## 快速開始

可以這樣問 AI 助手：

- 「用 Python 做綠界信用卡結帳，並驗證付款通知。」
- 「藍新回 MPG03009，哪裡錯了？」
- 「要做超商低溫取貨，用哪一家比較適合？」

也可以直接查資料：

```bash
python3 taiwan-payment/scripts/search.py "MPG03009" --domain error
```

各 skill 的 README 有預期輸出與更多指令。

## 觸發詞

English: Taiwan e-invoice, ECPay, NewebPay, PAYUNi, LINE Pay, TapPay, CheckMacValue, payment notification, convenience-store pickup, store map, cold-chain delivery.

中文：電子發票、開立發票、載具、金流串接、綠界、藍新、統一金流、付款通知、超商取貨、電子地圖選店、宅配、物流狀態碼。

## 會執行與連線的內容

- **不會自己執行任何東西。** 本 plugin 沒有 hook、MCP 伺服器或背景程式；腳本只有在你或 AI 助手呼叫時才會執行。
- **離線腳本**（只讀本機 CSV 與範本，不連網）：各 skill 的 `search.py`、`recommend.py`、`check_numbers.py`、`test_skill.py` 與服務程式產生器。`persist.py`（發票）只在你指定的目錄寫入設定檔。
- **可選的連線測試**：`taiwan-payment/scripts/test_payment.py`、`taiwan-logistics/scripts/test_logistics.py` 預設離線（只跑已知答案測試）；只有加 `--live`、`--create` 或 `--query` 時才會送出請求，而且只送到服務商的測試環境：`payment-stage.ecpay.com.tw`、`ccore.newebpay.com`、`sandbox-api.payuni.com.tw`、`logistics-stage.ecpay.com.tw`。
- **範例程式**（`examples/`）在你自己的專案裡執行時，才會呼叫你選用的服務商。
- **金鑰**：商店代號與金鑰（例如 HashKey、HashIV）由你自己透過環境變數或設定檔提供。repo 裡沒有真實憑證；文件中的測試值是服務商公開的測試帳號。
- **維護用工具**（skill 不會用到）：`scripts/check-sources.py` 會下載 `sources/official-sources.json` 登記的官方文件以偵測變動，GitHub Action 每週執行一次。
- 不收集任何資料，也不會傳送任何資料給作者。

## 驗證方式

- 每個端點、欄位、錯誤碼都能追到 [`sources/official-sources.json`](sources/official-sources.json) 登記的官方來源；沒有出處的內容會刪除或列為待確認。
- 每週自動重新下載這些來源，有變動就開 issue。
- 簽章與加解密程式碼由 CI 執行 `scripts/verify-examples.py`，和服務商官方範例（[`tests/vectors/`](tests/vectors/)）逐位元組比對。
- 每個 skill 都有自我測試（`scripts/test_skill.py`）與 evals，結果在 `evals/RESULTS.md`。
- 最近一次金流稽核：[`taiwan-payment/references/audit-20261117.md`](taiwan-payment/references/audit-20261117.md)。

## 限制

- 部分服務商的規格只提供給簽約商店（例如速買配、GoMyPay），這些部分會標示，不做推測。
- 街口的公開文件站目前無法連線，該 reference 依最後一次取得的官方內容。
- 沒有商家 API 的物流業者（例如黑貓、中華郵政）只列出經聚合商的串接方式。
- 各 skill 的待確認事項：[`發票`](taiwan-invoice/data/pending.csv)、[`金流`](taiwan-payment/data/pending.csv)、[`物流`](taiwan-logistics/data/pending.csv)。

更多說明（支援的 AI 工具、CLI 指令、常見問題、加密方式）：[`docs/guide.zh-TW.md`](docs/guide.zh-TW.md)。

## 目錄結構

```
.claude-plugin/       plugin 與 marketplace 設定
taiwan-invoice/       電子發票 skill（SKILL.md、references、data、scripts、examples）
taiwan-payment/       金流 skill
taiwan-logistics/     物流 skill
invoice-cli/ payment-cli/ logistics-cli/   npm 安裝程式
sources/              官方來源清單與變動基準
scripts/              維護用檢查（資料、範例、來源）
tests/vectors/        官方測試向量
docs/                 較長的說明文件
```

## 授權與作者

MIT 授權。作者 Moksa（[moksaweb.com](https://moksaweb.com)）。回報問題或送 PR 請見 [CONTRIBUTING.md](CONTRIBUTING.md)。
