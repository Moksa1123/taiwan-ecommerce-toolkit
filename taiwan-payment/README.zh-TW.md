# taiwan-payment

串接台灣金流的 Claude skill：請求簽章、加解密、付款通知、退款與錯誤碼，內容依各家官方文件整理。

[![npm version](https://img.shields.io/npm/v/taiwan-payment-skill)](https://www.npmjs.com/package/taiwan-payment-skill)
[![License: MIT](https://img.shields.io/github/license/Moksa1123/taiwan-ecommerce-toolkit)](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/LICENSE)

[English](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/taiwan-payment/README.md) | 繁體中文

本專案為非官方專案，與綠界（ECPay）、藍新（NewebPay）、統一金流（PAYUNi）、LINE、TapPay、街口（JKOPAY）及文中提到的其他公司都沒有關係，也未獲其背書。品牌名稱依各公司的原寫法，權利屬於各公司。

## 功能

- 涵蓋 14 家台灣金流：ECPay、NewebPay、PAYUNi、SmilePay、PChomePay、ezPay、PayNow、Shopline Payments、LINE Pay v4、TapPay、O'Pay、JKOPAY、SunPay、GoMyPay。
- 讓 Claude 知道每一家的簽章與加密規則（CheckMacValue、TradeSha、AES-256-CBC、AES-256-GCM、RSA、JWT、HMAC-SHA256），並附可執行的 Python 範例。
- 用 `scripts/search.py` 離線查詢 3212 筆官方資料：錯誤碼、API 操作、欄位對照、付款方式、疑難排解。
- 用 `scripts/recommend.py` 依白話需求推薦金流。
- 每種任務（信用卡、ATM、超商代碼、電子錢包、Apple Pay、Google Pay、TWQR、先買後付、定期定額、退款）都對應到 `references/` 裡該讀的檔。

## 適用情境

適合用在：

- 開發或除錯串接上述任一家的結帳流程；
- 驗證付款通知（CheckMacValue、TradeSha、HashInfo、webhook 簽章）；
- 查某家錯誤碼或狀態碼的意思；
- 幫專案挑金流。

不適用時改用：

- 開立、作廢、折讓電子發票：用 [taiwan-invoice](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/tree/main/taiwan-invoice)；
- 出貨、超商取貨、電子地圖選店、物流追蹤，即使是綠界、藍新、統一金流的物流：用 [taiwan-logistics](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/tree/main/taiwan-logistics)；
- 台灣以外的金流，或直接串銀行、卡組織：不在範圍內。

## 安裝

系統需求：腳本用 Python 3，只用標準函式庫。`examples/` 的範例與 `scripts/test_payment.py` 的連線選項另外需要 `pycryptodome`（AES）和 `requests`，用 `pip install -r requirements.txt` 安裝。Node.js 18 以上只有 npx 安裝程式需要。Windows、macOS、Linux 都能用。

Claude Code plugin（一次裝好發票、金流、物流三個台灣 skill）：

```text
/plugin marketplace add Moksa1123/taiwan-ecommerce-toolkit
/plugin install taiwan-ecommerce@taiwan-ecommerce-toolkit
```

npx（把 skill 複製到目前的專案；`--ai` 也可以填 `cursor`、`codex` 等其他 AI 工具，`--global` 裝到家目錄）：

```bash
npx taiwan-payment-skill@1.5.15 init --ai claude
```

手動複製：

```bash
git clone https://github.com/Moksa1123/taiwan-ecommerce-toolkit.git
cp -r taiwan-ecommerce-toolkit/taiwan-payment ~/.claude/skills/
```

## 快速開始

可以這樣問 Claude：

- 「用 Python 建立綠界信用卡訂單，並驗證付款通知。」
- 「藍新 TradeInfo 解不開，我的 padding 哪裡錯？」
- 「要做 LINE Pay 加信用卡定期定額，該選哪一家？」

也可以在 skill 資料夾裡自己查：

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
| `scripts/test_payment.py` | 綠界、藍新、統一金流簽章的已知答案測試；預設離線 | `--live`：對綠界（`payment-stage.ecpay.com.tw`）、藍新（`ccore.newebpay.com`）、統一金流（`sandbox-api.payuni.com.tw`）的測試環境送 HEAD 請求。`--query`：對綠界測試環境的訂單查詢送 POST | `--create`：在目前資料夾產生 `ecpay_test_<order>.html` 付款表單 |
| `scripts/check_numbers.py` | 核對 `SKILL.md` 和這兩份 README 的每個數字都對得上資料 | 無 | 加 `--fix` 時改這三個檔 |
| `scripts/test_skill.py` | 自我測試；離線執行上面的檢查 | 無 | 無 |
| `examples/*.py` | 各家的參考用戶端 | 直接執行時，連該檔開頭設定的測試或正式環境網址 | 無 |

金鑰（商店代號、HashKey 與 HashIV、LINE Pay Channel ID 與 Channel Secret、TapPay Partner Key、API key）由你在自己的程式或設定中提供，例如環境變數。repo 裡沒有任何真實金鑰；文件和腳本裡出現的測試值，是各家公開的測試環境帳號。

## 驗證方式

- 資料出處：各家官方文件、PDF 規格書、官方 SDK 或外掛。每個來源都登記在 [`sources/official-sources.json`](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/sources/official-sources.json)，每筆資料都有 `doc_url` 和 `trust`。
- 最近一次對照官方文件稽核：2026-11-17，紀錄在 [`references/audit-20261117.md`](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/taiwan-payment/references/audit-20261117.md)。
- 自我測試：`python3 scripts/test_skill.py` 共 50 項檢查，失敗 0（2026-11-17 執行）。
- evals：計分的 10 題中，有 skill 時 Claude 答對 10 題，沒有 skill 時答對 0 題。見 [`evals/RESULTS.md`](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/taiwan-payment/evals/RESULTS.md)。
- CI 會跑 `scripts/verify-examples.py`，把範例程式的結果和各家官方 SDK、規格書範例產生的標準答案逐位元組比對（[`tests/vectors/`](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/tree/main/tests/vectors)）。

## 限制

- O'Pay 和 GoMyPay 沒有可執行範例。GoMyPay 的完整 API 規格不公開，要向 GoMyPay 申請。
- 最近一次稽核時街口的文件站連不上，街口的 reference 依最後一次保存的官方頁面整理。
- 已知落差和查不到答案的問題記在 [`data/pending.csv`](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/taiwan-payment/data/pending.csv)。
- 標 `trust=推論` 的資料（選型建議、疑難排解）是依官方文件歸納的，請當建議看，不是業者規定。

## 目錄結構

```text
taiwan-payment/
├── SKILL.md         # Claude 讀的說明
├── EXAMPLES.md      # 較長的程式範例
├── references/      # 每家一份 API 規格，加上稽核紀錄
├── examples/        # 可執行的 Python 用戶端
├── data/            # search.py、recommend.py 用的 CSV；pending.csv
├── scripts/         # 查詢、推薦、測試、數字核對
└── evals/           # evals 題目、評分程式與結果
```

## 授權與作者

MIT License。作者 Moksa（[moksaweb.com](https://moksaweb.com)）。屬於 [Taiwan E-commerce Toolkit](https://github.com/Moksa1123/taiwan-ecommerce-toolkit)。
