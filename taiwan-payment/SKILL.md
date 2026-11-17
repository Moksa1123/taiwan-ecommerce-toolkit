---
name: taiwan-payment
description: Taiwan Payment API integration specialist for ECPay, NewebPay, PAYUNi, SmilePay, PChomePay, ezPay, PayNow, Shopline Payments, LINE Pay v4, TapPay, O'Pay, JKOPAY, SunPay and GoMyPay. Use when developing payment systems, implementing credit card, ATM, CVS, e-wallet, LINE Pay, Apple Pay, Google Pay, TWQR or BNPL payments, or working with Taiwan payment gateway APIs. Handles encryption (SHA256, AES-256-CBC, AES-256-GCM, dynamic AES-256, RSA, JWT, HMAC-SHA256, Basic Auth → token, Prime token), API requests, and service provider differences. 中文觸發：金流串接、綠界、藍新、統一金流、信用卡付款、ATM 虛擬帳號、超商代碼、LINE Pay、Apple Pay、街口、CheckMacValue、TradeSha、付款通知、退款、定期定額。
user-invocable: true
---

# 台灣金流開發技能

## 資料出處

| 項目 | 內容 |
|---|---|
| 來源 | 各服務商官方文件、官方 PDF 規格書、官方 SDK／外掛原始碼；每個來源登記在 repo 的 `sources/official-sources.json`（網址、取得方式、影響哪些檔） |
| 服務商 | 共 14 家（`data/providers.csv`，每家附 `doc_url` 與 `doc_verified`） |
| 筆數 | 共 **3178 筆**，分 7 個搜尋域；各域筆數用 `python scripts/search.py --stats` 看，不在這裡手寫 |
| 出處欄 | 每筆都有 `doc_url`（官方文件）與 `trust`（實測／官方文件／推論）；`retrieved_on` 是官方來源最近一次比對的日期 |
| 加密實作 | 由官方 SDK、外掛或規格書範例原封不動執行產生標準答案（`tests/vectors/`），範例與文件程式碼逐位元組比對 |
| 驗證 | 2026-11-15：自我測試全過、`verify-examples.py` 全過；已知落差記在 `data/pending.csv` |

`trust` 是「推論」的資料（`reasoning` 選型建議、`troubleshoot` 疑難排解）是依官方文件歸納的，
轉述給使用者時要說「建議」，不可以說成官方規定。`market_share` 欄是推論，不是官方數字。

## 用法

**何時用**

- 串接台灣金流：信用卡（一次、分期、定期定額）、ATM 虛擬帳號、超商代碼／條碼、電子錢包、TWQR、BNPL
- 計算或除錯簽章與加密：CheckMacValue、TradeInfo／TradeSha、EncryptInfo／HashInfo、LINE Pay 簽章
- 付款通知（callback／webhook）處理、查詢訂單、退款、請款
- 選服務商、比較各家差異、查錯誤碼

**何時不用**

| 情況 | 改用 |
|---|---|
| 開立電子發票、折讓、作廢 | `taiwan-invoice` skill |
| 超商取貨、宅配、物流單 | `taiwan-logistics` skill（PChomePay、PAYUNi 的金物流二合一也在那邊查物流段） |
| LINE Messaging API、LINE Login | `line-api` skill |
| 海外金流（Stripe、PayPal 國際版） | 不在資料集內；直接說查不到 |

**唯一入口：`scripts/search.py`。** 任何問題先用它查，其他工具都是查完之後的下一步。

| 使用者會跑的 | 用途 |
|---|---|
| `scripts/search.py` | 入口：查資料庫（`--stats` 看筆數） |
| `scripts/recommend.py` | 依需求推薦服務商 |
| `scripts/test_payment.py` | 加密已知答案測試（預設離線；`--live` 才連測試環境） |
| `scripts/test_skill.py` | 自我測試：數字核對、出處欄、路由表、evals 題庫格式 |
| `scripts/check_numbers.py` | 核對 SKILL.md 每個數字與資料一致 |
| `examples/*.py` | 各家可執行範例（複製進專案用） |

| 維護者用的（repo 根目錄） | 用途 |
|---|---|
| `scripts/verify-examples.py` | 範例與文件程式碼對官方標準答案 |
| `scripts/validate-data.py` | CSV 格式、主鍵、檔案大小 |
| `scripts/check-sources.py` | 比對官方來源有沒有改版 |
| `scripts/add-provenance.py` | 補 CSV 出處欄 |

**依賴**：`search.py`、`recommend.py`、`check_numbers.py`、`test_skill.py` 只用 Python 標準函式庫。
`examples/` 與 `test_payment.py` 的 AES 測試需要 `pycryptodome`，`--live` 需要 `requests`：
`pip install -r requirements.txt`。沒裝時 AES 測試標「略過」，不算通過。

## 路由

**鐵則：先查再答，不憑記憶。查不到就說查不到，標「待補」並記進 `data/pending.csv`，不猜。**

```bash
python scripts/search.py "<關鍵字>"                  # 自動偵測域
python scripts/search.py "<關鍵字>" --domain <域>    # 只搜那一個域
python scripts/search.py "<關鍵字>" --domain all     # 每個域都搜
python scripts/search.py --stats                     # 每個域有幾筆
```

| 使用者會怎麼說 | 查哪個域 | 指令 |
|---|---|---|
| 「綠界回 10200073 是什麼」「錯誤碼」 | `error` | `search.py "10200073" --domain error` |
| 「檢查碼一直錯」「付款通知收不到」 | `troubleshoot` | `search.py "CheckMacValue 錯誤" --domain troubleshoot` |
| 「訂單編號欄位各家叫什麼」 | `field` | `search.py "MerchantTradeNo" --domain field` |
| 「退款／請款要打哪支 API」 | `operation` | `search.py "退款" --domain operation` |
| 「超商代碼上限多少」「可以分幾期」 | `payment_method` | `search.py "超商代碼" --domain payment_method` |
| 「哪家用什麼加密」「測試網址」 | `provider` | `search.py "PAYUNi" --domain provider` |
| 「該選哪一家」「適合訂閱制的金流」 | `reasoning` | `recommend.py "會員制 定期扣款"` |
| 「全支付、悠遊付、TWQR 怎麼收」 | — | 讀 `references/twqr-ewallet-landscape.md` |

搜尋結果每筆都附 `doc_url` 與 `trust`。回答時附上 `doc_url`；結果裡沒有的事實不要補。
加密流程、欄位細節查到後，再讀該家的 reference：

| 服務商 | reference |
|---|---|
| 綠界 ECPay | `references/ecpay-payment-api.md` |
| 藍新 NewebPay | `references/newebpay-payment-api.md` |
| 統一 PAYUNi | `references/payuni-payment-api.md` |
| 速買配 SmilePay | `references/smilepay-payment-api.md` |
| 拍錢包 PChomePay | `references/pchomepay-payment-api.md` |
| ezPay 簡單付 | `references/ezpay-payment-api.md` |
| 立吉富 PayNow | `references/paynow-payment-api.md` |
| SHOPLINE Payments | `references/shopline-payment-api.md` |
| LINE Pay | `references/linepay-payment-api.md` |
| TapPay | `references/tappay-payment-api.md` |
| 歐付寶 O'Pay | `references/opay-payment-api.md` |
| 街口 JKOPAY | `references/jkopay-payment-api.md` |
| 紅陽 SunPay | `references/sunpay-payment-api.md` |
| GoMyPay | `references/gomypay-payment-api.md`（完整規格要向 GoMyPay 申請） |
| 電子支付生態、TWQR | `references/twqr-ewallet-landscape.md` |
| 加密實作、訂單流程、常見問題、測試帳號、檢查清單 | `references/implementation-guide.md` |
| 官方文件稽核紀錄（各家改了什麼、依據網址） | `references/audit-20261117.md` |

## 使用

| 任務 | 步驟 | 查的資料 | 產出與完成的證據 |
|---|---|---|---|
| 選服務商 | 1. `recommend.py` 2. 查 `provider` 比對加密與付款方式 | `reasoning`、`provider`、`payment_method` | 推薦理由＋`doc_url`；標明是建議 |
| 建立訂單 | 1. 查該家 reference 的必填欄位 2. 從 `examples/` 複製實作 3. 計算簽章 | `operation`、`field`、reference | 程式碼；用到的加密與 `verify-examples.py` 驗過的實作一致 |
| 計算簽章／加解密 | 1. 讀 `implementation-guide.md` 的加密實作 2. 照抄，不改演算法 | reference、`tests/vectors/` | 對官方標準答案相同（`test_payment.py --platform all` 通過） |
| 付款通知 | 1. 先驗簽再更新訂單 2. 冪等處理 3. 依各家格式回應 | `troubleshoot`、reference | 程式碼；驗簽失敗時不更新訂單 |
| 查詢、退款、請款 | 1. 查端點 2. 查必填欄位與期限 | `operation`、`field` | 程式碼＋`doc_url` |
| 錯誤碼除錯 | 1. 查錯誤碼 2. 查疑難排解 3. 對照使用者程式碼 | `error`、`troubleshoot` | 原因＋`doc_url` |
| 付款方式限制 | 查金額上下限、到帳天數 | `payment_method` | 數字＋`doc_url`；查不到就說查不到 |

**寫程式時務必遵守**

1. **綠界 CheckMacValue**：排除 CheckMacValue 本身、參數名稱不分大小寫排序、綠界規則的 URL encode 後轉小寫，金流用 SHA256、國內物流用 MD5。
   直接用 `encodeURIComponent` 或 Python `quote_plus` 會在空白、括號時算錯。
2. **藍新 TradeInfo**：AES-256-CBC 加密 query string 後轉 hex；TradeSha 是 `HashKey=…&TradeInfo&HashIV=…` 的 SHA256 大寫。
   解密時 padding 可能到 32 bytes，`RespondType=JSON` 時明文是 JSON。
3. **PAYUNi EncryptInfo**：AES-256-GCM，`hex(base64(密文) + ":::" + base64(tag))`，最外層 hex 不可省；HashInfo 是 HashKey 在前。
4. **ezPay 不是藍新**：網域、欄位、支付工具都不同，ATM、超商代碼、分期要用藍新。
5. **先驗簽再處理通知**，訂單狀態更新要冪等；HashKey、HashIV、Channel Secret 不進前端、repo、log。
6. 完整程式碼在 `references/implementation-guide.md`，都由 `verify-examples.py` 對官方標準答案驗過，不要憑印象改演算法。

## 驗證

產出後一定要跑。全部驗證器有錯都回非 0 的 exit code，可以直接當關卡。

| 產出 | 驗證器 | 通過標準 |
|---|---|---|
| 加密實作 | `python scripts/test_payment.py --platform all` | 失敗 0；裝了 `pycryptodome` 時略過也要是 0 |
| 範例、文件程式碼 | `python scripts/verify-examples.py`（repo 根目錄，需 `pip install -r requirements-dev.txt`） | FAIL 0，exit 0 |
| 資料 CSV | `python scripts/validate-data.py`（repo 根目錄） | 全數通過，exit 0 |
| SKILL.md 數字 | `python scripts/check_numbers.py` | exit 0 |
| skill 本身 | `python scripts/test_skill.py` | 失敗 0，exit 0 |
| 回答品質 | `python evals/grade.py --with <有 skill 答案> --without <沒 skill 答案>` | 有 skill 計分題答對率 ≥ 90%；結果記在 `evals/RESULTS.md` |

`--live` 會連服務商測試環境，只在使用者要求時跑。

## 維護

- 官方來源改版：repo 根目錄 `python scripts/check-sources.py` → 改受影響的 reference／CSV → 跑上面的驗證 → `check-sources.py --update`。
- CSV 新增列後補出處：`python scripts/add-provenance.py`；找不到官方來源的列會標推論，要記進 `data/pending.csv`。
- 筆數變了：`python scripts/check_numbers.py --fix`。
- 錯誤碼重建：`_studies/harness/import_error_codes.py`（原始文件在 `_studies/`，不進 repo）。
- 改完同步安裝版：repo 的 `taiwan-payment/` 蓋到 `~/.claude/skills/taiwan-payment/`，不刪安裝版獨有的檔。
