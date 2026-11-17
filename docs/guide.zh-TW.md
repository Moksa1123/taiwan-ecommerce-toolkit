# Taiwan E-commerce Toolkit 使用說明

README 的補充：支援的 AI 工具、CLI 指令、常見問題與技術規格。功能與安裝見 [README.zh-TW.md](../README.zh-TW.md)。

## 多平台支援

支援 14 種 AI 編碼助手平台，涵蓋主流開發工具：

| 平台 | 啟動方式 | 平台 | 啟動方式 |
|------|----------|------|----------|
| **Claude Code** | `/taiwan-*` | **Antigravity** | `/taiwan-*` |
| **Cursor** | `/taiwan-*` | **Kiro** | `/taiwan-*` |
| **Windsurf** | 自動載入 | **Codex** | 自動載入 |
| **GitHub Copilot** | `/taiwan-*` | **Qoder** | 自動載入 |
| **Cline** | 自動載入 | **OpenCode** | 自動載入 |
| **Gemini CLI** | 自動載入 | **Continue** | 自動載入 |
| **Trae** | 自動載入 | **CodeBuddy** | 自動載入 |

---

## CLI 指令

### 共通指令

```bash
# 列出支援平台
taiwan-invoice list
taiwan-payment list
taiwan-logistics list

# 顯示技能資訊
taiwan-invoice info
taiwan-payment info
taiwan-logistics info

# 檢查更新
taiwan-invoice update
taiwan-payment update
taiwan-logistics update

# 覆蓋安裝
taiwan-invoice init --force
taiwan-payment init --force
taiwan-logistics init --force
```

---

## 常見問題

<details>
<summary><b>是否需要申請 API 憑證？</b></summary>

是的。需向選定的服務商申請商店代號 (Merchant ID) 與 API 金鑰 (Hash Key/IV)。多數服務商提供測試環境；綠界等有公開測試帳號，其餘需向服務商申請（見各 reference 的測試環境段落）。

</details>

<details>
<summary><b>是否支援多家服務商同時整合？</b></summary>

支援。建議採用 Service Factory Pattern 設計模式，可在執行階段動態切換不同服務商服務，提高系統彈性。

</details>

<details>
<summary><b>如何選擇合適的整合服務商？</b></summary>

**服務商選擇建議：**

- **ECPay 綠界科技**: 三個領域全面支援，整合流程最為簡便，適合需要一站式解決方案的專案
- **NewebPay 藍新金流**: 金流功能最為完整，支援多元付款方式，適合需要豐富支付選項的電商平台
- **PAYUNi 統一金流**: 物流溫控服務最完整，支援冷凍/冷藏配送，適合生鮮電商與需要溫控的產業

可使用本專案提供的智能推薦系統，根據專案需求自動分析推薦最適合的服務商。

</details>

<details>
<summary><b>AI 助手無法載入技能檔案？</b></summary>

**疑難排解步驟：**

1. 確認 SKILL.md 檔案存在於正確的目錄路徑
2. 檢查檔案開頭的 YAML frontmatter 格式是否正確
3. 重新啟動 AI 編碼助手應用程式
4. 嘗試使用 `/taiwan-*` 斜線命令手動觸發
5. 確認 AI 助手版本支援 Skills 功能

</details>

<details>
<summary><b>Python 範例程式可以直接用在正式環境嗎？</b></summary>

範例程式以官方測試向量驗證過簽章與加解密，用在正式環境前要：

1. 安裝必要依賴套件：`pip install pycryptodome requests`
2. 將測試環境憑證替換為正式環境憑證
3. 依需求調整業務邏輯與錯誤處理機制
4. 進行完整的單元測試與整合測試

範例只示範串接流程，正式上線前請依你的系統補齊錯誤處理、重試與記錄。

</details>

---

## 技術規格

### 系統需求

- **Node.js**: >= 18.0.0 (CLI 工具)
- **Python**: >= 3.8 (範例程式與智能工具)
- **TypeScript**: >= 5.0 (程式碼生成器輸出)

### Python 依賴

```bash
# 範例程式所需依賴
pip install pycryptodome requests

# 智能工具無需外部依賴 (純 Python 標準庫)
```

### 支援的加密方式

| 演算法 | 應用 |
|---|---|
| **AES-128-CBC** | ECPay 電子發票 |
| **AES-256-CBC** | NewebPay 金流、ezPay 金流（電子支付平台 / 跨境 MPG，32-byte padding）、ezPay 發票、NewebPay 物流 |
| **AES-256-GCM** | PAYUNi 金流 / 物流（EncryptInfo = hex(base64(密文) + `:::` + base64(tag))） |
| **動態 AES-256 (GP/GK)** | PayNow 傳統 cashflow（每次以 GP/GK 檢核碼取 Key/IV） |
| **3DES / ECB / Zero-Padding** | **PayNow 物流**（24-byte Key + 8-byte IV，不同於金流端 AES-256） |
| **Bearer 私鑰** | PayNow 現代 PaymentIntent（Webhook 以私鑰 HMAC-SHA256 驗章） |
| **JWT Bearer Token** | PayNow 發票 |
| **HTTP Basic → Token** | PChomePay（取得 8 小時 pcpay-token） |
| **Verify_key + 加權檢核碼** | SmilePay（無 AES，反推 Mid_smilepay 算法） |
| **HMAC-SHA256 + Nonce** | LINE Pay v4 |
| **HMAC-SHA256 (Webhook)** | Shopline Payments |
| **Partner Key + Prime 兩段式** | TapPay（PCI 隔離） |
| **SHA256** | ECPay/NewebPay/PAYUNi/ezPay 多家用作 CheckMacValue / TradeSha / HashInfo / HashData / CheckCode |
| **MD5** | Amego 發票、ECPay 物流 |
