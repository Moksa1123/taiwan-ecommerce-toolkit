<h1 align="center">Taiwan Logistics Skill</h1>

<h3 align="center">台灣物流 AI 開發技能包</h3>

<p align="center">
  <strong>支援 ECPay 綠界 · NewebPay 藍新 · PAYUNi 統一</strong>
</p>

<p align="center">
  <a href="https://www.npmjs.com/package/taiwan-logistics-skill"><img src="https://img.shields.io/npm/v/taiwan-logistics-skill?style=flat-square&logo=npm" alt="npm version"></a>
  <a href="https://www.npmjs.com/package/taiwan-logistics-skill"><img src="https://img.shields.io/npm/dm/taiwan-logistics-skill?style=flat-square&label=downloads" alt="npm downloads"></a>
  <img src="https://img.shields.io/badge/node-%3E%3D18-339933?style=flat-square&logo=node.js&logoColor=white" alt="Node.js">
  <img src="https://img.shields.io/badge/platforms-14-blue?style=flat-square" alt="14 Platforms">
  <a href="https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/LICENSE"><img src="https://img.shields.io/github/license/Moksa1123/taiwan-ecommerce-toolkit?style=flat-square" alt="License"></a>
</p>

<p align="center">
  <a href="https://paypal.me/cccsubcom"><img src="https://img.shields.io/badge/PayPal-支持開發-00457C?style=for-the-badge&logo=paypal&logoColor=white" alt="PayPal"></a>
</p>

---

## 專案簡介

Taiwan Logistics Skill 是專為台灣物流整合設計的 AI 開發工具包，支援三大物流服務商 (ECPay、NewebPay、PAYUNi) 的完整 API 整合。本工具包提供企業級程式碼範例、BM25 智能搜尋引擎、服務商推薦系統與代碼生成器，協助開發團隊快速完成物流系統整合。

**版本:** 1.1.2
**狀態:** Production Ready

---

## 核心特色

### 企業級程式碼標準

所有 Python 範例均達到生產環境品質：

- **完整型別定義** - Dataclass 搭配 Literal、Optional、Dict 型別提示
- **專業文件規範** - 詳細的 Docstring (Args/Returns/Raises/Example)
- **嚴謹錯誤處理** - 完整的例外處理與中文錯誤訊息
- **實戰測試憑證** - 包含測試環境憑證，可直接執行驗證

### 生產級 Python 範例

完整的物流整合實作，支援多種物流方式：

- **ecpay-logistics-cvs-example.py** - 綠界 C2C 物流
- **newebpay-logistics-cvs-example.py** - 藍新超商物流
- **payuni-logistics-cvs-example.py** - 統一超商物流
- **store-map-integration-example.html** - 門市地圖整合

### BM25 智能搜尋引擎

採用 BM25 演算法的語義搜尋系統：

```bash
python scripts/search.py "超商取貨" --domain operation
python scripts/search.py "溫控配送" --domain logistics_type
python scripts/search.py "查詢物流狀態" --domain api
```

### 智能推薦系統

基於關鍵字權重與 BM25 評分的物流服務商推薦引擎：

```bash
python scripts/recommend.py "超商取貨 溫控配送 冷凍宅配"
python scripts/recommend.py "穩定 電商 高交易量"
```

### 自動化程式碼生成器

支援 TypeScript 與 Python 雙語言輸出：

```bash
python scripts/generate-logistics-service.py ECPay --output ts
python scripts/generate-logistics-service.py NewebPay --output py
```

---

## 快速開始

### 安裝

```bash
npm install -g taiwan-logistics-skill
```

### 初始化

```bash
# 進入專案目錄
cd /path/to/your/project

# 選擇你的 AI 助手
taiwan-logistics init --ai claude        # Claude Code
taiwan-logistics init --ai cursor        # Cursor
taiwan-logistics init --ai windsurf      # Windsurf
taiwan-logistics init --ai copilot       # GitHub Copilot
taiwan-logistics init --ai antigravity   # Antigravity
taiwan-logistics init --ai all           # 全部安裝
```

### 使用方式

安裝完成後，在 AI 助手中直接使用自然語言描述需求：

```
實作 ECPay 7-11 超商取貨功能，支援取貨付款
建立 NewebPay 全家超商物流訂單
查詢 PAYUNi 黑貓宅配物流狀態
```

---

## CLI 指令

```bash
# 列出支援平台
taiwan-logistics list

# 顯示技能資訊
taiwan-logistics info

# 列出可用版本
taiwan-logistics versions

# 檢查更新
taiwan-logistics update

# 強制覆蓋安裝
taiwan-logistics init --force

# 全域安裝 (所有專案共用)
taiwan-logistics init --ai claude --global
```

---

## 支援平台

| 平台 | 說明 | 啟動方式 |
|------|------|----------|
| **Claude Code** | Anthropic 官方 CLI | `/taiwan-logistics` |
| **Cursor** | AI 程式編輯器 | `/taiwan-logistics` |
| **Windsurf** | Codeium 編輯器 | 自動載入 |
| **Copilot** | GitHub Copilot | `/taiwan-logistics` |
| **Antigravity** | Google AI 助手 | `/taiwan-logistics` |
| **Kiro** | AWS AI 助手 | `/taiwan-logistics` |
| **Codex** | OpenAI CLI | 自動載入 |
| **Qoder** | Qodo AI 助手 | 自動載入 |
| **RooCode** | VSCode 擴充 | `/taiwan-logistics` |
| **Gemini CLI** | Google Gemini | 自動載入 |
| **Trae** | ByteDance AI | 自動載入 |
| **OpenCode** | 開源 AI 助手 | 自動載入 |
| **Continue** | 開源 AI 助手 | 自動載入 |
| **CodeBuddy** | Tencent AI | 自動載入 |

---

## 物流服務商支援

| 物流服務 | 加密技術 | API 風格 | 支援物流類型 |
|----------|----------|----------|--------------|
| **ECPay 綠界** | MD5 CheckMacValue | Form POST | 7-11、全家、萊爾富、OK、黑貓、新竹貨運 |
| **NewebPay 藍新** | AES-256-CBC + SHA256 | Form POST + AES | 7-11、全家、萊爾富、OK、黑貓宅急便 |
| **PAYUNi 統一** | AES-256-GCM + SHA256 | RESTful JSON | 7-11 (常溫/冷凍)、黑貓 (常溫/冷凍/冷藏) |

---

## 物流方式支援

### 超商取貨

- 7-11 取貨 (常溫/冷凍)
- 全家取貨
- OK超商取貨
- 萊爾富取貨
- 超商取貨付款

### 宅配服務

- 黑貓宅急便
- 新竹貨運
- 冷凍宅配
- 冷藏宅配

### 其他服務

- C2C 店到店
- B2C 大宗寄倉
- 溫控物流

---

## 智能工具

所有工具皆採用純 Python 實作，無需安裝外部依賴套件。

### BM25 搜尋引擎

```bash
# 物流類型查詢
python scripts/search.py "超商取貨" --domain logistics_type

# API 端點搜尋
python scripts/search.py "查詢物流狀態" --domain operation

# 服務商比較
python scripts/search.py "溫控配送" --domain provider
```

支援搜尋域:
- `provider` - 物流服務商比較
- `operation` - API 操作端點
- `logistics_type` - 物流類型
- `troubleshoot` - 疑難排解

### 物流服務商推薦系統

```bash
# 根據需求推薦物流服務商
python scripts/recommend.py "超商取貨 溫控配送 冷凍宅配"
python scripts/recommend.py "穩定 電商 高交易量"
python scripts/recommend.py "API 設計 現代化"
```

### 程式碼生成器

```bash
# 生成 TypeScript 服務模組
python scripts/generate-logistics-service.py ECPay --output ts > ecpay-service.ts

# 生成 Python 服務模組
python scripts/generate-logistics-service.py NewebPay --output py > newebpay-service.py
```

---

## 程式碼範例

### ECPay 物流整合

```python
from ecpay_logistics import ECPayLogistics

service = ECPayLogistics(
    merchant_id='2000132',
    hash_key='5294y06JbISpM5x9',
    hash_iv='v77hoKGq4kWxNNIS',
    test_mode=True
)

# 建立超商取貨訂單
params = service.create_cvs_order(
    order_id='ORDER001',
    goods_name='測試商品',
    goods_amount=100,
    receiver_name='王小明',
    receiver_phone='0912345678',
    receiver_store_id='991182',  # 7-11 門市代號
    logistics_sub_type='UNIMARTC2C'  # 7-11 店到店
)
```

完整範例: [ecpay-logistics-cvs-example.py](examples/ecpay-logistics-cvs-example.py)

### 門市地圖整合

提供完整的前端整合範例，支援三家服務商門市地圖選擇功能：

- 響應式設計 (RWD)
- 三家服務商即時切換
- 門市資訊即時顯示
- 後端程式碼範例內嵌

完整範例: [store-map-integration-example.html](examples/store-map-integration-example.html)

---

## 技術規格

### 系統需求

- **Node.js**: >= 18.0.0 (CLI 工具)
- **Python**: >= 3.8 (範例程式與智能工具)

### Python 依賴

```bash
# 範例程式所需依賴
pip install pycryptodome requests

# 智能工具無需外部依賴 (純 Python 標準庫)
```

### 支援的加密方式

- **MD5 CheckMacValue** - ECPay 物流
- **AES-256-CBC + SHA256** - NewebPay 物流
- **AES-256-GCM + SHA256** - PAYUNi 物流

---

## 專案結構

```
taiwan-logistics/
├── README.md                      # 本文件
├── SKILL.md                       # AI 技能文檔
├── EXAMPLES.md                    # 程式碼範例集
│
├── references/                    # API 文件
│   ├── ecpay-api.md              # ECPay API 規格
│   ├── newebpay-api.md           # NewebPay API 規格
│   └── payuni-api.md             # PAYUNi API 規格
│
├── examples/                      # 生產級 Python 範例
│   ├── ecpay-logistics-cvs-example.py
│   ├── newebpay-logistics-cvs-example.py
│   ├── payuni-logistics-cvs-example.py
│   └── store-map-integration-example.html
│
├── scripts/                       # Python 智能工具
│   ├── search.py                 # BM25 搜尋引擎
│   ├── recommend.py              # 物流服務商推薦系統
│   └── generate-logistics-service.py  # 代碼生成器
│
└── data/                          # CSV 數據檔
    ├── providers.csv             # 物流服務商比較
    ├── operations.csv            # API 端點定義
    ├── logistics-types.csv       # 物流類型支援
    └── troubleshoot.csv          # 疑難排解案例
```

---

## 常見問題

<details>
<summary><b>是否需要申請物流服務商憑證？</b></summary>

是的。需向選定的物流服務商申請商店代號 (Merchant ID) 與 API 金鑰 (Hash Key/IV)。三家物流服務商皆提供測試環境與測試帳號供開發使用。

</details>

<details>
<summary><b>Python 範例程式是否可直接用於生產環境？</b></summary>

可以。所有範例程式皆為生產級品質，使用前僅需：

1. 安裝必要依賴套件：`pip install pycryptodome requests`
2. 將測試環境憑證替換為正式環境憑證
3. 依需求調整業務邏輯與錯誤處理機制
4. 進行完整的單元測試與整合測試

</details>

<details>
<summary><b>如何選擇合適的物流服務商？</b></summary>

**物流服務商選擇建議：**

- **ECPay 綠界**: 市佔率最高，穩定性最佳，適合需要可靠性的專案
- **NewebPay 藍新**: 整合流程完整，適合需要多元物流選擇的電商平台
- **PAYUNi 統一**: 支援溫控配送 (冷凍/冷藏)，適合生鮮電商與需要溫控的產業

可使用本工具包提供的智能推薦系統，根據專案需求自動分析推薦。

</details>

<details>
<summary><b>AI 助手無法載入技能檔案？</b></summary>

**疑難排解步驟：**

1. 確認 SKILL.md 檔案存在於正確的目錄路徑
2. 檢查檔案開頭的 YAML frontmatter 格式是否正確
3. 重新啟動 AI 編碼助手應用程式
4. 嘗試使用 `/taiwan-logistics` 斜線命令手動觸發
5. 確認 AI 助手版本支援 Skills 功能

</details>

---

## 授權

[MIT License](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/LICENSE)

---

## 相關連結

- [Taiwan Invoice Skill](../taiwan-invoice/README.md) - 電子發票整合
- [Taiwan Payment Skill](../taiwan-payment/README.md) - 金流整合
- [NPM Package](https://www.npmjs.com/package/taiwan-logistics-skill)
- [GitHub Repository](https://github.com/Moksa1123/taiwan-ecommerce-toolkit)

---

<p align="center">
  <sub>Made by <strong>Moksa</strong></sub><br>
  <sub>service@moksaweb.com</sub>
</p>
