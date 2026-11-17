# {{TITLE}}

> {{DESCRIPTION}}

## 資料出處

| 項目 | 內容 |
|---|---|
| 來源 | 各加值中心官方 API 文件與 PDF 規格書、官方 SDK、財政部電子發票整合服務平台規格；每個來源登記在 repo 的 `sources/official-sources.json` |
| 服務商 | `data/providers.csv` 共 9 筆：可開立的加值中心 7 家都有 reference，另有財政部大平台（只查詢）與關貿（只登記，沒有 reference） |
| 筆數 | 共 **409 筆**，分 7 個搜尋域；各域筆數用 `python scripts/search.py --stats` 看，不在這裡手寫 |
| 出處欄 | 每筆都有 `doc_url`（官方文件）與 `trust`（實測／官方文件／推論）；`retrieved_on` 是官方來源最近一次比對的日期 |
| 加密實作 | 由官方 SDK 或規格書範例原封不動執行產生標準答案（`tests/vectors/`），範例逐位元組比對 |
| 驗證 | 2026-11-15：自我測試全過、`verify-examples.py` 全過；已知落差記在 `data/pending.csv` |

`trust` 是「推論」的資料（`reasoning` 選型建議、`troubleshoot` 疑難排解、`tax` 金額公式）是依官方文件歸納的，
轉述給使用者時要說「建議」或「依規格推算」，不可以說成官方規定。

## 用法

**何時用**

- 開立 B2C（二聯式）、B2B（三聯式）電子發票，作廢、折讓、註銷重開
- 載具（手機條碼、自然人憑證）、捐贈碼、統編的驗證
- 發票金額與稅額計算（含稅、未稅、零稅率、免稅）
- 加密與簽章、列印、選加值中心、查錯誤碼
- 財政部大平台查詢（手機條碼驗證、捐贈碼、中獎號碼）

**何時不用**

| 情況 | 改用 |
|---|---|
| 收款、刷卡、退款 | `taiwan-payment` skill |
| 出貨、超取、物流單 | `taiwan-logistics` skill |
| 營業稅申報、會計帳務 | 不在資料集內；直接說查不到 |
| 用財政部大平台開立發票 | 大平台不能開立，要透過加值中心 |

**唯一入口：`scripts/search.py`。** 任何問題先用它查，其他工具都是查完之後的下一步。

| 使用者會跑的 | 用途 |
|---|---|
| `scripts/search.py` | 入口：查資料庫（`--stats` 看筆數） |
| `scripts/recommend.py` | 依需求推薦加值中心 |
| `scripts/generate-invoice-service.py` | 產生服務骨架（未實作的步驟會拋 `NotImplementedError`） |
| `scripts/persist.py` | 把專案的發票設定存成 `MASTER.md` |
| `scripts/test_skill.py` | 自我測試：數字核對、出處欄、路由表、evals 題庫格式、既有測試 |
| `scripts/check_numbers.py` | 核對 SKILL.md 每個數字與資料一致 |
| `examples/*.py` | 各家可執行範例（複製進專案用） |

| 維護者用的（repo 根目錄） | 用途 |
|---|---|
| `scripts/verify-examples.py` | 範例對官方標準答案 |
| `scripts/validate-data.py` | CSV 格式、主鍵、檔案大小 |
| `scripts/check-sources.py` | 比對官方來源有沒有改版 |
| `scripts/add-provenance.py` | 補 CSV 出處欄 |

**依賴**：`scripts/` 全部只用 Python 標準函式庫。`examples/` 的 AES 加解密需要 `pycryptodome`，HTTP 呼叫需要 `requests`：
`pip install -r requirements.txt`。

## 路由

**鐵則：先查再答，不憑記憶。查不到就說查不到，標「待補」並記進 `data/pending.csv`，不猜。**

```bash
python scripts/search.py "<關鍵字>"                 # 自動偵測域
python scripts/search.py "<關鍵字>" --domain <域>   # 只搜那一個域
python scripts/search.py "<關鍵字>" --all           # 每個域都搜
python scripts/search.py --stats                    # 每個域有幾筆
```

| 使用者會怎麼說 | 查哪個域 | 指令 |
|---|---|---|
| 「綠界回 10000009 是什麼」「錯誤碼」 | `error` | `search.py "10000009" --domain error` |
| 「列印出來是空白」「查不到發票」 | `troubleshoot` | `search.py "列印空白" --domain troubleshoot` |
| 「統編、載具欄位各家叫什麼」 | `field` | `search.py "統編" --domain field` |
| 「作廢／折讓要打哪支 API」 | `operation` | `search.py "折讓" --domain operation` |
| 「B2B 稅額怎麼算」「含稅未稅」 | `tax` | `search.py "B2B 稅額" --domain tax` |
| 「哪家用什麼加密」「測試網址」 | `provider` | `search.py "SunPay" --domain provider` |
| 「該選哪一家加值中心」 | `reasoning` | `recommend.py "<需求>"` |
| 「沒收錄的加值中心怎麼辦」 | — | 讀 `references/VAC_LANDSCAPE.md` |

搜尋結果每筆都附 `doc_url` 與 `trust`。回答時附上 `doc_url`；結果裡沒有的事實不要補。
查到後再讀該家的 reference：

| 服務商 | reference |
|---|---|
| 綠界 ECPay | `references/ECPAY_API_REFERENCE.md` |
| 速買配 SmilePay | `references/SMILEPAY_API_REFERENCE.md` |
| 光貿 Amego | `references/AMEGO_API_REFERENCE.md` |
| ezPay 簡單付 | `references/EZPAY_API_REFERENCE.md` |
| 立吉富 PayNow | `references/PAYNOW_API_REFERENCE.md` |
| 歐付寶 O'Pay | `references/OPAY_API_REFERENCE.md` |
| 紅陽 SunPay | `references/SUNPAY_API_REFERENCE.md` |
| 財政部大平台（只查詢） | `references/MOF_EINVOICE_API_REFERENCE.md` |
| 加值中心生態與選型 | `references/VAC_LANDSCAPE.md` |
| 工具用法、各家比較表、金額計算、加密、列印、常見問題、測試帳號 | `references/implementation-guide.md` |
| 官方文件稽核紀錄（各家改了什麼、依據網址） | `references/audit-20261117.md` |

## 使用

| 任務 | 步驟 | 查的資料 | 產出與完成的證據 |
|---|---|---|---|
| 選加值中心 | 1. `recommend.py` 2. 讀 `implementation-guide.md` 的比較表 | `reasoning`、`provider` | 推薦理由＋`doc_url`；標明是建議 |
| 開立 B2C／B2B | 1. 查必填欄位 2. 算金額與稅額 3. 從 `examples/` 複製加密 | `operation`、`field`、`tax` | 程式碼；金額公式與 `test-invoice-amounts.py` 的算法一致 |
| 作廢、折讓、註銷重開 | 1. 查端點 2. 查限制（期限、金額上限） | `operation`、`troubleshoot` | 程式碼＋`doc_url` |
| 載具、捐贈碼、統編 | 1. 查格式 2. 需要時打大平台驗證 | `field`、`troubleshoot`、MOF reference | 驗證規則＋`doc_url` |
| 列印 | 1. 查該家列印方式（各家不同） 2. 依 reference 實作 | reference、`troubleshoot` | 程式碼 |
| 錯誤碼除錯 | 1. 查錯誤碼 2. 查疑難排解 | `error`、`troubleshoot` | 原因＋`doc_url` |
| 新專案設定 | 1. `persist.py init <服務商>` 2. `generate-invoice-service.py` | — | `MASTER.md` 與服務骨架 |

**寫程式時務必遵守**

1. **B2C 金額含稅、B2B 金額未稅另計稅額**；B2B 不可用載具或捐贈。各家欄位名稱不同，一律先查 `field`。
2. **捐贈、載具、列印三者互斥規則**各家寫法不同（例：O'Pay 捐贈時 `Print` 必須是 `0`），照 reference 做。
3. **加密各家不同**：綠界、O'Pay、SunPay 用 AES-128-CBC，ezPay 用 AES-256-CBC，PayNow 用 JWT，SmilePay 用共享金鑰；同一家的金流與發票常常也不同。
4. **加密前要先 URL Encode，但各家規則不同**：綠界是 JSON 字串 URL Encode 後再 AES；O'Pay 有自己的 .NET 字元轉換表（與 RFC 3986 不同），SunPay 要 .NET 風格且 `%xx` 小寫。照該家 reference 與 `examples/` 做，不要直接套語言內建函式。
5. **時間戳記有效區間短**，主機要校時；HashKey、HashIV 不進前端、repo、log。

## 驗證

產出後一定要跑。全部驗證器有錯都回非 0 的 exit code，可以直接當關卡。

| 產出 | 驗證器 | 通過標準 |
|---|---|---|
| 範例、加密實作 | `python scripts/verify-examples.py`（repo 根目錄，需 `pip install -r requirements-dev.txt`） | FAIL 0，exit 0 |
| 金額計算 | `python scripts/test-invoice-amounts.py` | exit 0 |
| 資料 CSV | `python scripts/validate-data.py`（repo 根目錄） | 全數通過，exit 0 |
| SKILL.md 數字 | `python scripts/check_numbers.py` | exit 0 |
| skill 本身 | `python scripts/test_skill.py` | 失敗 0，exit 0 |
| 回答品質 | `python evals/grade.py --with <有 skill 答案> --without <沒 skill 答案>` | 有 skill 計分題答對率 ≥ 90%；結果記在 `evals/RESULTS.md` |

## 維護

- 官方來源改版：repo 根目錄 `python scripts/check-sources.py` → 改受影響的 reference／CSV → 跑上面的驗證 → `check-sources.py --update`。
- CSV 新增列後補出處：`python scripts/add-provenance.py`；找不到官方來源的列會標推論，要記進 `data/pending.csv`。
- 筆數變了：`python scripts/check_numbers.py --fix`。
- 錯誤碼重建：`_studies/harness/import_invoice_error_codes.py`（原始文件在 `_studies/`，不進 repo）。
- 改完同步安裝版：repo 的 `taiwan-invoice/` 蓋到 `~/.claude/skills/taiwan-invoice/`，不刪安裝版獨有的檔。
