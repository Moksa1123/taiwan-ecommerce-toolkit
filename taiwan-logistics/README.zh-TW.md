# taiwan-logistics

串接台灣物流 API 的 Claude skill：超商取貨、宅配、電子地圖選店、取貨付款與物流追蹤，內容依各家官方文件整理。

[![npm version](https://img.shields.io/npm/v/taiwan-logistics-skill)](https://www.npmjs.com/package/taiwan-logistics-skill)
[![License: MIT](https://img.shields.io/github/license/Moksa1123/taiwan-ecommerce-toolkit)](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/LICENSE)

[English](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/taiwan-logistics/README.md) | 繁體中文

本專案為非官方專案，與綠界（ECPay）、藍新（NewebPay）、統一金流（PAYUNi）、速買配（SmilePay）、拍錢包（PChomePay）、立吉富（PayNow）、ezShip、新竹物流（HCT）、Lalamove、pandago、各超商及文中提到的其他公司都沒有關係，也未獲其背書。品牌名稱依各公司的原寫法，權利屬於各公司。

## 功能

- 涵蓋 7 家有物流 API 的聚合商（ECPay、NewebPay、PAYUNi、SmilePay、PChomePay、PayNow、ezShip）、新竹物流（HCT）直連 API，以及即時配送（Lalamove、pandago）。
- 讓 Claude 知道每一家的簽章與加密規則（MD5 CheckMacValue、AES-256-CBC、AES-256-GCM、3DES），並附可執行的 Python 範例。
- 用 `scripts/search.py` 離線查詢 1126 筆資料：服務商、API 操作、物流類型、欄位對照、物流狀態碼。
- 產生某家的服務模組（`scripts/generate-logistics-service.py`），並依白話需求推薦物流（`scripts/recommend.py`）。
- 涵蓋超商取貨（7-11、全家、萊爾富、OK）、宅配、冷凍冷藏、電子地圖選店、取貨付款與追蹤。

## 適用情境

適合用在：

- 開發超商取貨或宅配的出貨流程；
- 在結帳頁加上電子地圖選店；
- 建立物流單、列印托運單或處理狀態通知；
- 查物流狀態碼的意思，或挑選物流。

不適用時改用：

- 收款，包含綠界、藍新、統一金流的金流部分：用 [taiwan-payment](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/tree/main/taiwan-payment)；
- 開立電子發票：用 [taiwan-invoice](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/tree/main/taiwan-invoice)；
- 台灣以外的物流，或沒有公開 API 的物流合約：不在範圍內（skill 會直接說明，不會亂猜）。

## 安裝

系統需求：腳本用 Python 3，只用標準函式庫。`examples/` 的範例與 `scripts/test_logistics.py` 的連線選項另外需要 `pycryptodome`（AES、3DES）和 `requests`，用 `pip install -r requirements.txt` 安裝。Node.js 18 以上只有 npx 安裝程式需要。Windows、macOS、Linux 都能用。

Claude Code plugin（一次裝好發票、金流、物流三個台灣 skill）：

```text
/plugin marketplace add Moksa1123/taiwan-ecommerce-toolkit
/plugin install taiwan-ecommerce@taiwan-ecommerce-toolkit
```

npx（把 skill 複製到目前的專案；`--ai` 也可以填 `cursor`、`codex` 等其他 AI 工具，`--global` 裝到家目錄）：

```bash
npx taiwan-logistics-skill@1.4.12 init --ai claude
```

手動複製：

```bash
git clone https://github.com/Moksa1123/taiwan-ecommerce-toolkit.git
cp -r taiwan-ecommerce-toolkit/taiwan-logistics ~/.claude/skills/
```

## 快速開始

可以這樣問 Claude：

- 「用 Python 在結帳頁加上綠界超商取貨和電子地圖選店。」
- 「建立統一金流宅配物流單，並下載托運單。」
- 「綠界物流狀態 2073 是什麼意思？」

也可以在 skill 資料夾裡自己查：

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
| `scripts/recommend.py` | 依 `data/*.csv` 推薦物流 | 無 | 無 |
| `scripts/generate-logistics-service.py` | 輸出某家的 Python 或 TypeScript 模組 | 無 | 無（輸出到標準輸出） |
| `scripts/test_logistics.py` | 綠界簽章的已知答案測試；預設離線 | `--live`：對綠界（`logistics-stage.ecpay.com.tw`）、藍新（`ccore.newebpay.com`）、統一金流（`sandbox-api.payuni.com.tw`）的測試環境送 HEAD 請求。`--create` 與 `--query`：對綠界物流測試環境送 POST | 無 |
| `scripts/check_numbers.py` | 核對 `SKILL.md` 和這兩份 README 的每個數字都對得上資料 | 無 | 加 `--fix` 時改這三個檔 |
| `scripts/test_skill.py` | 自我測試；離線執行上面的檢查 | 無 | 無 |
| `examples/*.py` | 各家的參考用戶端 | 直接執行時，連該檔開頭設定的測試或正式環境網址 | 無 |
| `examples/store-map-integration-example.html` | 電子地圖選店的範例頁與伺服器端程式 | 本身不連線；回呼網址是佔位值 | 無 |

金鑰（商店代號、HashKey 與 HashIV、API key 與 secret、物流商客戶代號）由你在自己的程式或設定中提供，例如環境變數。repo 裡沒有任何真實金鑰；文件和腳本裡出現的測試值，是各家公開的測試環境帳號。

## 驗證方式

- 資料出處：各家官方 API 文件、PDF 規格書與 SDK。每個來源都登記在 [`sources/official-sources.json`](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/sources/official-sources.json)，每筆資料都有 `doc_url` 和 `trust`。
- 自我測試：`python3 scripts/test_skill.py` 共 42 項檢查，失敗 0（2026-11-17 執行）。
- evals：計分的 11 題中，有 skill 時 Claude 答對 11 題，沒有 skill 時答對 0 題。見 [`evals/RESULTS.md`](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/taiwan-logistics/evals/RESULTS.md)。
- CI 會跑 `scripts/verify-examples.py`，把範例程式的結果和各家官方 SDK、規格書範例產生的標準答案逐位元組比對（[`tests/vectors/`](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/tree/main/tests/vectors)）。

## 限制

- 超商、黑貓、中華郵政等沒有公開 API 的業者只列出來讓 Claude 說明，要透過聚合商串接。
- Lalamove 和 pandago 有 reference，但沒有可執行範例。新竹物流的文件要向新竹物流申請後才拿得到。
- `test_logistics.py --create` 和 `--query` 只支援綠界；藍新和統一金流要用你自己的商店帳號。
- 已知落差記在 [`data/pending.csv`](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/taiwan-logistics/data/pending.csv)。

## 目錄結構

```text
taiwan-logistics/
├── SKILL.md         # Claude 讀的說明
├── EXAMPLES.md      # 較長的程式範例
├── references/      # 每家一份 API 規格、即時配送總覽
├── examples/        # 可執行的 Python 用戶端與電子地圖範例頁
├── data/            # search.py、recommend.py 用的 CSV；pending.csv
├── scripts/         # 查詢、推薦、產生器、測試、數字核對
└── evals/           # evals 題目、評分程式與結果
```

## 授權與作者

MIT License。作者 Moksa（[moksaweb.com](https://moksaweb.com)）。屬於 [Taiwan E-commerce Toolkit](https://github.com/Moksa1123/taiwan-ecommerce-toolkit)。
