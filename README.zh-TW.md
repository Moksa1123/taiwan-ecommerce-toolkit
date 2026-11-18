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
  <img src="https://img.shields.io/badge/providers-33-success?style=flat-square" alt="33 Providers">
  <img src="https://img.shields.io/badge/AI%20platforms-14-blue?style=flat-square" alt="14 AI Platforms">
  <a href="LICENSE"><img src="https://img.shields.io/github/license/Moksa1123/taiwan-ecommerce-toolkit?style=flat-square" alt="License"></a>
</p>

<p align="center">
  <a href="https://paypal.me/cccsubcom"><img src="https://img.shields.io/badge/PayPal-支持開發-00457C?style=for-the-badge&logo=paypal&logoColor=white" alt="PayPal"></a>
</p>

<p align="center"><a href="README.md">English</a></p>

> 本專案為非官方的社群專案，與綠界、藍新、統一金流、LINE、TapPay、街口等文中提到的公司均無關聯，也未受其認可或贊助。各產品名稱屬於其所有者。

---

## 專案概覽

台灣電子發票、金流、物流 API 串接用的 agent skill，內容依各家服務商的官方文件整理。整個 repo 是一個 Claude plugin（`taiwan-ecommerce`），內含三個 skill，共收錄 **33 個服務商**（9 家發票 + 14 家金流 + 10 家可串接物流），另收錄 10 家**沒有商家 API** 的物流業者與替代路徑。

<table>
<tr>
<td width="33%" align="center">

### 電子發票整合

**taiwan-invoice-skill**

9 家：7 家加值中心 + 財政部大平台 + 關貿

<a href="https://www.npmjs.com/package/taiwan-invoice-skill"><img src="https://img.shields.io/npm/v/taiwan-invoice-skill?style=flat-square&color=cb3837&logo=npm" alt="npm version"></a>
<a href="https://www.npmjs.com/package/taiwan-invoice-skill"><img src="https://img.shields.io/npm/dm/taiwan-invoice-skill?style=flat-square&color=cb3837" alt="npm downloads"></a>

[完整文件](taiwan-invoice/README.zh-TW.md)

</td>
<td width="33%" align="center">

### 金流串接整合

**taiwan-payment-skill**

14 家金流與電子支付

<a href="https://www.npmjs.com/package/taiwan-payment-skill"><img src="https://img.shields.io/npm/v/taiwan-payment-skill?style=flat-square&color=cb3837&logo=npm" alt="npm version"></a>
<a href="https://www.npmjs.com/package/taiwan-payment-skill"><img src="https://img.shields.io/npm/dm/taiwan-payment-skill?style=flat-square&color=cb3837" alt="npm downloads"></a>

[完整文件](taiwan-payment/README.zh-TW.md)

</td>
<td width="33%" align="center">

### 物流串接整合

**taiwan-logistics-skill**

10 家可串接：7 家聚合商 + 新竹物流直連 + 2 家即時配送

<a href="https://www.npmjs.com/package/taiwan-logistics-skill"><img src="https://img.shields.io/npm/v/taiwan-logistics-skill?style=flat-square&color=cb3837&logo=npm" alt="npm version"></a>
<a href="https://www.npmjs.com/package/taiwan-logistics-skill"><img src="https://img.shields.io/npm/dm/taiwan-logistics-skill?style=flat-square&color=cb3837" alt="npm downloads"></a>

[完整文件](taiwan-logistics/README.zh-TW.md)

</td>
</tr>
</table>

| 每個 skill 內含 | 用途 |
|---|---|
| `SKILL.md` + `references/` | 各家 API 的實際規則：端點、欄位、簽章、錯誤碼 |
| `data/*.csv` + `scripts/search.py` | 可搜尋的端點、欄位對照、錯誤碼（BM25，離線） |
| `examples/` | 以官方測試向量驗證過的可執行範例 |
| `data/pending.csv` | 還要向服務商確認的事項 |

**適用：** 撰寫或除錯與台灣電子發票、金流、物流服務商串接的程式，例如結帳、`CheckMacValue`／`TradeSha`、付款通知、開立或作廢發票、建立物流單、電子地圖選店、查錯誤碼。**不適用：** 會計、報稅或台灣以外的服務商；也不能取代與服務商簽約，正式環境金鑰要向服務商申請。

---

## 快速開始

### Step 1：安裝

Claude plugin（Claude Code；通過審核後也可從 Claude 目錄加入）：

```
/plugin marketplace add Moksa1123/taiwan-ecommerce-toolkit
/plugin install taiwan-ecommerce@taiwan-ecommerce-toolkit
```

其他 AI 編碼工具，或只裝單一 skill（npx 指定版本）：

```bash
npx taiwan-invoice-skill@2.9.13 init     # 電子發票
npx taiwan-payment-skill@1.5.16 init     # 金流串接
npx taiwan-logistics-skill@1.4.13 init   # 物流整合
```

手動複製：把 skill 資料夾放到 AI 助手讀取 skill 的位置，例如 `cp -r taiwan-payment ~/.claude/skills/`。

系統需求：內附腳本需要 Python 3（只用標準函式庫；AES 範例需要 `pycryptodome`）；Node.js 18 以上只有 npx 安裝程式需要。Windows、macOS、Linux 都可使用。

### Step 2：選擇 AI 工具

```bash
cd /path/to/your/project
npx taiwan-payment-skill@1.5.16 init --ai claude    # 或 cursor、windsurf、copilot、codex、gemini、all…
```

支援的 AI 工具與 skill 目錄：[docs/guide.zh-TW.md](docs/guide.zh-TW.md)。

### Step 3：用自然語言描述需求

```
用 Python 做綠界信用卡結帳，並驗證付款通知。
藍新回 MPG03009，哪裡錯了？
要做超商低溫取貨，用哪一家比較適合？
```

也可以直接查資料：

```bash
python3 taiwan-payment/scripts/search.py "CheckMacValue" --domain field
python3 taiwan-logistics/scripts/recommend.py "超商取貨 溫控配送 冷凍宅配"   # → 第一名 PAYUNi
```

**觸發詞：** Taiwan e-invoice, ECPay, NewebPay, PAYUNi, LINE Pay, TapPay, CheckMacValue, payment notification, convenience-store pickup, store map, cold-chain delivery · 電子發票、開立發票、載具、金流串接、綠界、藍新、統一金流、付款通知、超商取貨、電子地圖選店、宅配、物流狀態碼。

---

## 廠商整合支援

### 電子發票

| 服務商 | 加密／認證 | 說明 |
|---|---|---|
| **ECPay 綠界** | AES-128-CBC + HashKey/HashIV | B2C 與 B2B；B2B 請求帶 `RqID` 與 `Revision` |
| **SmilePay 速買配** | Grvc + Verify_key | URL 參數，無 AES |
| **Amego 光貿** | MD5 簽章 + App Key | MIG 4.0；折讓只能由賣方開立 |
| **ezPay 簡單付** | AES-256-CBC + SHA256 | 字軌管理、批次開立、折讓與作廢查詢 |
| **PayNow 立吉富** | JWT Bearer | 金物流發票一站式 |
| **O'Pay 歐付寶** | MerchantID + RqHeader + AES Data | 與綠界同源架構，網域與金鑰不同 |
| **SunPay 紅陽** | AES-128-CBC Token | 可與紅陽金流搭配開立 |
| **財政部大平台** | AppID + APIKey（HMAC-SHA256） | 只做查詢（載具、捐贈碼），不能開立 |
| **關貿** | 需簽約 | 已收錄於資料層，規格未公開 |

### 金流串接

| 服務商 | 加密／認證 | 付款方式 | 說明 |
|---|---|---|---|
| **ECPay 綠界** | SHA256 CheckMacValue | 信用卡、ATM、超商代碼／條碼、Apple Pay、TWQR、無卡分期、電子支付 | 文件最完整 |
| **NewebPay 藍新** | AES-256-CBC + SHA256 | 信用卡、分期、ATM、超商、LINE Pay、Apple／Google／Samsung Pay、TWQR、BitoPro | MPG 規格書 NDNF-1.2.6 |
| **PAYUNi 統一金流** | AES-256-GCM + SHA256 | 信用卡 Token、Click to Pay、ATM、超商、街口、icash Pay、AFTEE、LINE Pay | UPP Version 2.0 |
| **SmilePay 速買配** | Verify_key + 檢核碼 | ATM、超商條碼、ibon、FamiPort、信用卡、銀聯卡 | XML 回應 |
| **PChomePay 支付連** | HTTP Basic → token | 信用卡、ATM、超商代碼、超商取貨 | API 文件 1.7.4 |
| **ezPay 簡單付** | AES-256-CBC + SHA256 | ezPay 帳戶、約定帳戶／信用卡、TWQR、跨境 | 電子支付機構 |
| **PayNow 立吉富** | Bearer 私鑰（現代版）／動態 AES-256（傳統版） | 信用卡、分期、ATM、超商、LINE Pay、Apple Pay | Webhook 以 HMAC-SHA256 驗章 |
| **SHOPLINE Payments** | merchantId + apiKey Header | 信用卡、Apple Pay、LINE Pay、街口、ATM、BNPL | 金額以分計、HMAC Webhook |
| **LINE Pay v4** | HMAC-SHA256 + Nonce | LINE Pay、自動扣款 | Request → Confirm 兩段 |
| **TapPay** | Partner Key + Prime | 信用卡、Apple／Google Pay、LINE Pay、街口等 | `prod.tappaysdk.com` |
| **O'Pay 歐付寶** | SHA256 CheckMacValue | 信用卡、ATM、超商、TWQR、儲值 | 與綠界同源架構 |
| **JKOPAY 街口** | api-key + HMAC-SHA256 | 線上支付、POS、授權扣款 | 公開文件站 2026-11-17 起無法連線 |
| **SunPay 紅陽** | RSA + SHA256 check_value | 信用卡、ATM、超商代收 | 手冊 V1.1.2 |
| **GoMyPay** | 需簽約 | 信用卡、銀聯、WebATM、虛擬帳號、超商 | 規格未公開 |

### 物流串接（10 家可串接）

| 服務商 | 類型 | 加密／認證 | 支援範圍 |
|---|---|---|---|
| **ECPay 綠界** | 聚合商 | MD5 CheckMacValue | B2C 7-11（含冷凍）／全家／萊爾富；C2C 7-11／全家／萊爾富（OK 已於 2026-07-01 終止）；宅配 |
| **NewebPay 藍新** | 聚合商 | AES-256-CBC + SHA256 | 超商取貨；無宅配 |
| **PAYUNi 統一** | 聚合商 | AES-256-GCM + SHA256 | 7-11（常溫／冷凍）、黑貓（常溫／冷藏／冷凍） |
| **SmilePay 速買配** | 聚合商 | Verify_key | 7-11、全家、黑貓；兩階段建單 |
| **PChomePay 支付連** | 聚合商 | HTTP Basic → token | 7-11、全家、萊爾富（取貨付款） |
| **PayNow 立吉富** | 聚合商 | 3DES／ECB | 多條產品線，含冷凍與大宗 |
| **ezShip 台灣便利配** | 聚合商 | 帳號綁定（`su_id`） | 全家、萊爾富、OK、宅配 |
| **HCT 新竹物流** | 物流業者直連 | SOAP + 公司帳號 | 宅配；公開 WSDL |
| **Lalamove** | 即時配送 | HMAC-SHA256 | 同城即時配送（台灣市場） |
| **pandago** | 即時配送 | OAuth 2.0（STS token） | 同城即時配送；`/quotes` 一次回費用與時間 |

沒有商家 API 的業者（黑貓、嘉里大榮、宅配通、中華郵政、7-11、全家、萊爾富、OK、蝦皮店到店、紅陽物流）列在 `taiwan-logistics/references/carrier-direct-access.md`，並附經聚合商的串接方式。

---

## 會執行與連線的內容

- **不會自己執行任何東西。** 沒有 hook、MCP 伺服器或背景程式；腳本只有在你或 AI 助手呼叫時才執行。
- **離線腳本**（只讀本機 CSV 與範本）：`search.py`、`recommend.py`、`check_numbers.py`、`test_skill.py` 與服務程式產生器。`persist.py`（發票）只在你指定的目錄寫入設定檔。
- **可選的連線測試：** `taiwan-payment/scripts/test_payment.py`、`taiwan-logistics/scripts/test_logistics.py` 預設離線；只有加 `--live`、`--create` 或 `--query` 時才連服務商的**測試環境**：`payment-stage.ecpay.com.tw`、`ccore.newebpay.com`、`sandbox-api.payuni.com.tw`、`logistics-stage.ecpay.com.tw`。
- **範例程式**（`examples/`）在你自己的專案裡執行時，才會呼叫你選用的服務商。
- **金鑰：** 商店代號與金鑰由你透過環境變數或設定檔提供。repo 沒有真實憑證；文件中的測試值是服務商公開的測試帳號。
- **維護用工具**（skill 不會用到）：`scripts/check-sources.py` 會下載 `sources/official-sources.json` 登記的官方文件以偵測變動，GitHub Action 每週執行。
- 不收集任何資料，也不會傳送資料給作者。

## 驗證方式

| 檢查 | 做法 |
|---|---|
| 官方來源 | 每個端點、欄位、錯誤碼都能追到 `sources/official-sources.json`；沒有出處的刪除或列為待確認 |
| 每週來源檢查 | 重新下載官方文件，有變動就開 issue |
| 官方測試向量 | CI 執行 `scripts/verify-examples.py`，簽章與加解密和 `tests/vectors/` 逐位元組比對 |
| 自我測試與 evals | 各 skill 的 `scripts/test_skill.py` 與 `evals/RESULTS.md` |
| 最近一次稽核（2026-11-17） | [發票](taiwan-invoice/references/audit-20261117.md) · [金流](taiwan-payment/references/audit-20261117.md) · [物流](taiwan-logistics/references/audit-20261117.md) |

## 限制

- 部分規格只提供給簽約商店（速買配、GoMyPay、關貿），這些部分會標示，不做推測。
- 街口公開文件站目前無法連線，該 reference 依最後一次取得的官方內容。
- 待確認事項：[發票](taiwan-invoice/data/pending.csv) · [金流](taiwan-payment/data/pending.csv) · [物流](taiwan-logistics/data/pending.csv)。更多說明（AI 工具、CLI 指令、常見問題、加密方式）：[docs/guide.zh-TW.md](docs/guide.zh-TW.md)。

## 專案結構

```
.claude-plugin/        plugin 與 marketplace 設定
taiwan-invoice/        電子發票 skill（SKILL.md、references、data、scripts、examples）
taiwan-payment/        金流 skill
taiwan-logistics/      物流 skill
*-cli/                 npm 安裝程式（taiwan-*-skill）
sources/ scripts/      官方來源清單與維護用檢查
tests/vectors/ docs/   官方測試向量、較長的說明文件
```

## 授權與作者

[MIT 授權](LICENSE) · 作者 **Moksa** · [moksaweb.com](https://moksaweb.com) · [貢獻指南](CONTRIBUTING.md)
