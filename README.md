# Taiwan Invoice Skills

**Taiwan E-Invoice** | **3 Providers** | **3 AI Platforms** | **Agent Skills Standard** | **MIT License**

An AI skill that provides Taiwan E-Invoice API integration intelligence for Claude Code, Cursor, and Google Antigravity.

Taiwan Invoice Skills -- 台灣電子發票 AI 開發技能包

支援綠界 (ECPay)、速買配 (SmilePay)、光貿 (Amego) 三大發票加值中心。
涵蓋 B2C/B2B 開立、作廢、折讓、查詢及列印完整功能。
三個平台共用同一份 SKILL.md，遵循 [Agent Skills 開放標準](https://agentskills.io)。

## 概覽

```
+-----------------------------------------------------------------------------------+
|  TAIWAN INVOICE SKILLS                                                            |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  PROVIDERS:                                                                       |
|     ECPay (綠界)     AES-128-CBC 加密      完整測試環境                            |
|     SmilePay (速買配) GET/POST 參數簽章     串接流程簡易                            |
|     Amego (光貿)     MD5 簽章 (MIG 4.0)    API 設計簡潔                            |
|                                                                                   |
|  INVOICE TYPES:                                                                   |
|     B2C (二聯式)  含稅價，TaxAmount = 0                                            |
|     B2B (三聯式)  未稅 + 稅額分拆，稅率 5%                                          |
|                                                                                   |
|  FEATURES:                                                                        |
|     發票開立 | 發票作廢 | 折讓單 | 發票查詢 | 發票列印                             |
|                                                                                   |
|  PLATFORMS:                                                                       |
|     Claude Code    /taiwan-invoice 或自動啟用                                      |
|     Cursor         /taiwan-invoice 或自動啟用                                      |
|     Antigravity    依描述自動啟用                                                   |
|                                                                                   |
|  ENCRYPTION:                                                                      |
|     ECPay    AES-128-CBC (encrypt + URL encode + Base64)                          |
|     SmilePay URL parameter signing (GET/POST)                                     |
|     Amego    MD5 hash signature (MIG 4.0 protocol)                                |
|                                                                                   |
+-----------------------------------------------------------------------------------+
```

## 運作流程

```
┌─────────────────────────────────────────────────────────────────┐
│  1. 使用者提問                                                    │
│     「幫我用綠界測試環境開立一張 1050 元的 B2C 發票」                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. AI 自動載入 SKILL.md                                         │
│     偵測到電子發票相關主題 → 載入 taiwan-invoice skill               │
│     讀取對應的 API 參考文件 (ECPAY_API_REFERENCE.md)                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. 智慧程式碼生成                                                 │
│     - 判斷發票類型 (B2C → 含稅價，TaxAmount = 0)                    │
│     - 選擇正確的加密方式 (ECPay → AES-128-CBC)                      │
│     - 套用測試環境 URL 與測試帳號                                    │
│     - 生成完整 TypeScript service 程式碼                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. 輸出結果                                                      │
│     完整的 InvoiceService 實作，包含：                               │
│     加密邏輯 + API 呼叫 + 錯誤處理 + 金額計算 + 型別定義              │
└─────────────────────────────────────────────────────────────────┘
```

## 功能特色

| 類別 | 內容 |
|------|------|
| 加值中心 | ECPay（綠界）、SmilePay（速買配）、Amego（光貿） |
| 發票類型 | B2C 二聯式、B2B 三聯式 |
| 發票功能 | 開立、作廢、折讓、查詢、列印 |
| 加密方式 | AES-128-CBC、MD5 簽章、URL 參數簽章 |
| AI 平台 | Claude Code、Cursor、Google Antigravity |
| 技能標準 | [Agent Skills Open Standard](https://agentskills.io) (SKILL.md) |
| 輔助腳本 | 服務模組生成器、金額計算驗證 |
| API 文件 | 3 份完整 API 參考規格（含欄位、錯誤碼、測試帳號） |
| 程式碼範例 | 5 個基礎範例 + 2 個實務情境 + 2 個錯誤修正範例 |

## 支援的發票加值中心

| 加值中心 | 英文名稱 | 驗證方式 | 特色 | 測試環境 |
|----------|----------|----------|------|----------|
| 綠界 | ECPay | AES-128-CBC 加密 | 文檔豐富，市佔率高 | Y |
| 速買配 | SmilePay | GET/POST 參數簽章 | 雙協定支援，整合簡單 | Y |
| 光貿 | Amego | MD5 簽章（MIG 4.0） | API 設計清晰 | Y |

三家皆支援：B2C/B2B 發票開立、作廢、折讓、查詢、列印。

## 安裝方式

### 使用安裝腳本（推薦）

**macOS / Linux：**

```bash
git clone https://github.com/Moksa1123/taiwan-invoice.git
cd taiwan-invoice
bash install.sh
```

**Windows：**

```cmd
git clone https://github.com/Moksa1123/taiwan-invoice.git
cd taiwan-invoice
install.bat
```

安裝腳本支援互動選擇安裝目標平台，包含單一平台或全部安裝。

### 手動安裝

依據目標平台，將 `taiwan-invoice/` 目錄複製到對應位置：

```bash
# Claude Code - 專案層級
cp -r taiwan-invoice .claude/skills/taiwan-invoice

# Claude Code - 全域（所有專案可用）
cp -r taiwan-invoice ~/.claude/skills/taiwan-invoice

# Cursor - 專案層級
cp -r taiwan-invoice .cursor/skills/taiwan-invoice

# Cursor - 全域
cp -r taiwan-invoice ~/.cursor/skills/taiwan-invoice

# Google Antigravity - 工作區層級
cp -r taiwan-invoice .agent/skills/taiwan-invoice

# Google Antigravity - 全域
cp -r taiwan-invoice ~/.gemini/antigravity/global_skills/taiwan-invoice
```

### 各平台技能路徑

| 平台 | 專案層級 | 全域層級 | 呼叫方式 |
|------|----------|----------|----------|
| Claude Code | `.claude/skills/taiwan-invoice/` | `~/.claude/skills/` | `/taiwan-invoice` 或自動啟用 |
| Cursor | `.cursor/skills/taiwan-invoice/` | `~/.cursor/skills/` | `/taiwan-invoice` 或自動啟用 |
| Antigravity | `.agent/skills/taiwan-invoice/` | `~/.gemini/antigravity/global_skills/` | 依描述自動啟用 |

Cursor 亦可讀取 `.claude/skills/` 目錄，兩個平台共用同一份即可。

## 使用方式

### Skill 模式（自動啟用）

**適用：** Claude Code、Cursor、Google Antigravity

Skill 會在對話內容涉及電子發票時自動載入，直接用自然語言描述需求即可：

```
幫我用綠界測試環境開立一張 1050 元的 B2C 發票
```

```
我需要串接速買配的 B2B 發票功能，請產生完整的 API 呼叫程式碼
```

```
請幫我寫一個發票作廢的函式，要支援光貿的 MIG 4.0 簽章機制
```

```
B2C 和 B2B 發票有什麼差別？請提供程式碼範例
```

```
幫我建立發票模組的單元測試，涵蓋開立與折讓兩個情境
```

### 斜線指令模式（手動呼叫）

**適用：** Claude Code、Cursor

```
/taiwan-invoice 幫我建立一個發票服務工廠，支援三家加值中心切換
```

## 金額計算邏輯

```
B2C（二聯式）含稅價處理：
┌──────────────────────────────────────────┐
│  總額 = 1050                              │
│  SalesAmount = 1050  (含稅價直接帶入)      │
│  TaxAmount   = 0     (固定為 0)           │
│  TotalAmount = 1050                       │
└──────────────────────────────────────────┘

B2B（三聯式）未稅/稅額分拆：
┌──────────────────────────────────────────┐
│  總額 = 1050                              │
│  TaxAmount   = round(1050 - 1050/1.05)   │
│             = round(1050 - 1000) = 50     │
│  SalesAmount = 1050 - 50 = 1000          │
│  TotalAmount = 1050                       │
│                                          │
│  驗證: 1000 + 50 = 1050                   │
└──────────────────────────────────────────┘
```

## 輔助腳本

位於 `taiwan-invoice/scripts/` 目錄：

**generate-invoice-service.py** -- 快速生成新服務商的實作模板：

```bash
python taiwan-invoice/scripts/generate-invoice-service.py ECPay
# 生成 ecpay-invoice-service.ts，包含完整介面實作骨架
```

**test-invoice-amounts.py** -- 驗證 B2C/B2B 金額計算邏輯：

```bash
python taiwan-invoice/scripts/test-invoice-amounts.py
# 測試多種金額的稅額分拆與驗證
```

### 必要條件

Python 3.x

```bash
# 確認 Python 已安裝
python3 --version

# macOS
brew install python3

# Windows
winget install Python.Python.3.12
```

## 專案結構

```
claude-skills/
├── taiwan-invoice/                        # 技能原始碼（Source of Truth）
│   ├── SKILL.md                           # 技能定義檔（所有平台共用）
│   ├── EXAMPLES.md                        # 程式碼範例（9 個範例）
│   ├── references/                        # API 參考文件
│   │   ├── ECPAY_API_REFERENCE.md         #   綠界完整 API 規格
│   │   ├── SMILEPAY_API_REFERENCE.md      #   速買配完整 API 規格
│   │   └── AMEGO_API_REFERENCE.md         #   光貿完整 API 規格
│   └── scripts/                           # 輔助腳本
│       ├── generate-invoice-service.py    #   服務模組生成器
│       └── test-invoice-amounts.py        #   金額計算測試
│
├── .claude/skills/taiwan-invoice/         # Claude Code（預先安裝）
├── .cursor/skills/taiwan-invoice/         # Cursor（預先安裝）
├── .agent/skills/taiwan-invoice/          # Antigravity（預先安裝）
│
├── install.sh                             # macOS/Linux 安裝腳本
├── install.bat                            # Windows 安裝腳本
├── LICENSE                                # MIT 授權條款
├── CONTRIBUTING.md                        # 貢獻指南
└── CHANGELOG.md                           # 版本紀錄
```

## 常見問題

**問：三個平台使用的 SKILL.md 內容是否相同？**

是的。Claude Code、Cursor 與 Google Antigravity 皆採用相同的 [Agent Skills 開放標準](https://agentskills.io)格式，共用同一份 SKILL.md，無需針對不同平台維護多個版本。

**問：是否需要事先申請各加值中心的 API 帳號？**

是的。使用前請先向對應的加值中心申請商店代號及 API 金鑰。各加值中心皆提供測試環境，建議先以測試帳號進行開發與驗證。SKILL.md 中已包含各家的測試帳號資訊。

**問：可以同時支援多個加值中心嗎？**

可以。技能定義檔包含三家加值中心的完整 API 規格，可在同一個專案中依需求選擇使用其中一家或多家。建議搭配 Service Factory Pattern 實現動態切換。

**問：Cursor 已有 `.claude/skills/` 目錄，還需要 `.cursor/skills/` 嗎？**

不一定。Cursor 能自動讀取 `.claude/skills/` 目錄。如果只需要支援 Claude Code + Cursor，只安裝 `.claude/skills/` 即可。`.cursor/skills/` 是給只使用 Cursor 的專案。

**問：Skill 沒有被載入怎麼辦？**

確認 SKILL.md 檔案存在於正確的目錄路徑，且 YAML frontmatter 格式正確。嘗試重新啟動 AI 工具。也可以透過 `/taiwan-invoice` 手動呼叫。

## 貢獻

歡迎提交 Issue 與 Pull Request。詳細的貢獻流程與規範請參閱 [CONTRIBUTING.md](CONTRIBUTING.md)。

```bash
# 1. Fork 並 clone
git clone https://github.com/your-username/claude-skills.git
cd claude-skills

# 2. 建立功能分支
git checkout -b feature/your-feature-name

# 3. 修改 taiwan-invoice/ 目錄（Source of Truth）

# 4. 測試
python taiwan-invoice/scripts/test-invoice-amounts.py

# 5. 提交
git commit -m "Add: description of your change"

# 6. 推送並建立 PR
git push -u origin feature/your-feature-name
```

修改 `taiwan-invoice/` 後，記得同步到三個平台目錄（`.claude/skills/`、`.cursor/skills/`、`.agent/skills/`）。

## 授權條款

本專案採用 [MIT License](LICENSE) 授權。
