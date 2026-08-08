<h1 align="center">taiwan-logistics-skill</h1>

<h3 align="center">台灣物流 AI 開發技能包</h3>

<p align="center">
  <strong>6 家物流 aggregator + HCT 新竹物流直連 carrier API</strong>
</p>

<p align="center">
  ECPay · NewebPay · PAYUNi · SmilePay · PChomePay · PayNow · HCT 直連
</p>

<p align="center">
  <a href="https://www.npmjs.com/package/taiwan-logistics-skill"><img src="https://img.shields.io/npm/v/taiwan-logistics-skill?style=flat-square&logo=npm" alt="npm version"></a>
  <a href="https://www.npmjs.com/package/taiwan-logistics-skill"><img src="https://img.shields.io/npm/dm/taiwan-logistics-skill?style=flat-square&label=downloads" alt="npm downloads"></a>
  <img src="https://img.shields.io/badge/providers-7-success?style=flat-square" alt="7 Providers">
  <img src="https://img.shields.io/badge/AI%20platforms-14-blue?style=flat-square" alt="14 AI Platforms">
  <a href="https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/LICENSE"><img src="https://img.shields.io/github/license/Moksa1123/taiwan-ecommerce-toolkit?style=flat-square" alt="License"></a>
</p>

<p align="center">
  <a href="https://paypal.me/cccsubcom"><img src="https://img.shields.io/badge/PayPal-支持開發-00457C?style=for-the-badge&logo=paypal&logoColor=white" alt="PayPal"></a>
</p>

---

## 安裝

```bash
npm install -g taiwan-logistics-skill
```

## 快速開始

```bash
cd /path/to/your/project

taiwan-logistics init                    # 互動式
taiwan-logistics init --ai claude        # Claude Code
taiwan-logistics init --ai all           # 全部安裝
```

安裝完後，在 AI 助手用自然語言：

```
查詢台北市信義區的 7-11 取貨點，整合 ECPay 物流
建立 SmilePay 黑貓宅急便冷凍 C2C 訂單，COD 1000 元
PChomePay 7-11 取貨付款，金額 1500 元，notify URL 設好
PayNow 7-11 大宗寄倉，使用 3DES 加密
HCT 直連 API 傳入託運資料，逆物流單獨處理
```

---

## 7 家物流服務商

| 服務商 | 類型 | 加密 / 認證 | 特色 |
|---|---|---|---|
| **ECPay 綠界** | aggregator | MD5 CheckMacValue | 市佔率最高、SDK 完整、7-11/全家/萊爾富/OK/黑貓/宅配通/HCT |
| **NewebPay 藍新** | aggregator | AES-256-CBC + SHA256 | 7-11/全家/萊爾富/OK/黑貓 |
| **PAYUNi 統一** | aggregator | AES-256-GCM + SHA256 | 7-11 常溫/冷凍 + T-Cat 常溫/冷藏/冷凍（溫控配送最完整） |
| **SmilePay 速買配** | aggregator | Verify_key + 加權檢核碼 | Pay_zg 矩陣 51/52/55/56/81/82/83，含逆物流 |
| **PChomePay 拍錢包** | aggregator | HTTP Basic Auth → token | 金物流二合一、Notify IP 113.196.231.190、4 大超商 |
| **PayNow 立吉富** | aggregator | **3DES/ECB/Zero-Padding** | 11 條產品線（含海外配送）；不同於金流端 AES |
| **HCT 新竹物流** | **direct carrier API** | 申請後提供金鑰 | 直連 carrier API（vs 透過 aggregator） |

## 技能包內容

```
taiwan-logistics/
├── SKILL.md                              # AI 技能主文檔
├── EXAMPLES.md                           # 實戰範例集
├── references/                           # 7 份 API 規格 (~10,300 行)
│   ├── ecpay-logistics-api.md
│   ├── NEWEBPAY_LOGISTICS_REFERENCE.md
│   ├── payuni-logistics-api.md
│   ├── smilepay-logistics-api.md         # 1,332 行 / Pay_zg 矩陣
│   ├── pchomepay-logistics-api.md        # 1,154 行 / NDJSON 對帳 parser
│   ├── paynow-logistics-api.md           # 1,670 行 / 11 產品線
│   └── hct-logistics-api.md              # 1,102 行 / 直連 HCT
├── examples/                             # Python 範例
└── data/                                 # 5 份 CSV
    ├── providers.csv                    # 7 服務商
    ├── operations.csv                   # 30+ API 操作
    ├── logistics-types.csv              # CVS / Home / 溫控
    ├── status-codes.csv                 # 跨服務商狀態碼
    └── field-mappings.csv               # 欄位對照
```

## CLI 指令

```bash
taiwan-logistics list                  # 列出 AI 平台
taiwan-logistics info                  # 技能資訊
taiwan-logistics update                # 檢查更新
taiwan-logistics init --force          # 覆蓋安裝
taiwan-logistics init --global         # 全域安裝
```

## 14 個 AI 平台支援

Claude Code · Cursor · Windsurf · Antigravity · GitHub Copilot · Kiro · Codex · Qoder · Cline · Gemini · Trae · OpenCode · Continue · CodeBuddy

## 物流類型支援矩陣

| 取貨方式 | 7-11 | 全家 | 萊爾富 | OK | 黑貓 | 海外 | HCT |
|---|---|---|---|---|---|---|---|
| ECPay | ✅ | ✅ | ✅ | ✅ | ✅（常溫） | — | ✅ |
| NewebPay | ✅ | ✅ | ✅ | ✅ | ✅ | — | — |
| PAYUNi | ✅ | — | — | — | ✅（常溫/冷凍/冷藏） | — | — |
| SmilePay | ✅ C2C+B2C | ✅ C2C+B2C | — | — | ✅（COD/PICKUP/逆物流） | — | — |
| PChomePay | ✅ | ✅ | ✅ | ✅ | — | — | — |
| PayNow | ✅（含冷凍） | ✅（含冷凍） | ✅ | ✅ | ✅（宅配 + 店到店） | ✅（7-11） | — |
| HCT 直連 | — | — | — | — | — | — | ✅（直連） |

## 相關套件

本套件是 **[Taiwan E-Commerce Toolkit](https://github.com/Moksa1123/taiwan-ecommerce-toolkit)** 的一部分：

- [taiwan-invoice-skill](https://www.npmjs.com/package/taiwan-invoice-skill) — 5 家電子發票
- [taiwan-payment-skill](https://www.npmjs.com/package/taiwan-payment-skill) — 10 家金流

## 授權

[MIT License](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/LICENSE)

---

<p align="center">
  <sub>Made by <strong>Moksa</strong></sub><br>
  <sub>service@moksaweb.com</sub>
</p>
