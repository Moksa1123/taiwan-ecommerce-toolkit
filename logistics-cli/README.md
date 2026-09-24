<h1 align="center">taiwan-logistics-skill</h1>

<h3 align="center">台灣物流 AI 開發技能包</h3>

<p align="center">
  <strong>7 家物流 aggregator + HCT 新竹物流直連 + 3 家即時配送</strong>
</p>

<p align="center">
  ECPay · NewebPay · PAYUNi · SmilePay · PChomePay · PayNow · ezShip · HCT 直連 · Lalamove · pandago · Uber Direct
</p>

<p align="center">
  <a href="https://www.npmjs.com/package/taiwan-logistics-skill"><img src="https://img.shields.io/npm/v/taiwan-logistics-skill?style=flat-square&logo=npm" alt="npm version"></a>
  <a href="https://www.npmjs.com/package/taiwan-logistics-skill"><img src="https://img.shields.io/npm/dm/taiwan-logistics-skill?style=flat-square&label=downloads" alt="npm downloads"></a>
  <img src="https://img.shields.io/badge/providers-11-success?style=flat-square" alt="11 Providers">
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

## 物流服務商

| 服務商 | 類型 | 加密 / 認證 | 特色 |
|---|---|---|---|
| **ECPay 綠界** | aggregator | MD5 CheckMacValue | B2C 7-11（含冷凍）/全家/萊爾富；C2C 四大超商；宅配黑貓/中華郵政 |
| **NewebPay 藍新** | aggregator | AES-256-CBC + SHA256 | B2C 僅 7-11；C2C 四大超商；無宅配 |
| **PAYUNi 統一** | aggregator | AES-256-GCM + SHA256 | 7-11 常溫/冷凍 + T-Cat 常溫/冷藏/冷凍（溫控配送最完整） |
| **SmilePay 速買配** | aggregator | Verify_key + 加權檢核碼 | Pay_zg 矩陣 51/52/55/56/81/82/83，含逆物流 |
| **PChomePay 拍錢包** | aggregator | HTTP Basic Auth → token | 金物流二合一、7-11／全家／萊爾富取貨付款 |
| **PayNow 立吉富** | aggregator | **3DES/ECB/Zero-Padding** | 11 條產品線（含海外配送）；不同於金流端 AES |
| **ezShip 台灣便利配** | aggregator | 無簽章（`su_id` 帳號綁定） | 全家/萊爾富/OK、宅配、店港澳；不含 7-11 |
| **HCT 新竹物流** | **direct carrier API** | 申請後提供金鑰 | 收錄的聚合商都沒有新竹物流選項，只能直連 |
| **Lalamove** | 即時配送 | HMAC-SHA256 自簽 | 先報價後下單（報價 5 分鐘效期） |
| **pandago** | 即時配送 | OAuth 2.0 + RSA 簽 JWT assertion | 同城即時配送 |
| **Uber Direct** | 即時配送 | OAuth 2.0 client_credentials | 台灣可用性未經官方確認 |

## 技能包內容

```
taiwan-logistics/
├── SKILL.md                              # AI 技能主文檔
├── EXAMPLES.md                           # 實戰範例集
├── references/                           # 各服務商 API 規格
│   ├── ecpay-logistics-api.md
│   ├── NEWEBPAY_LOGISTICS_REFERENCE.md
│   ├── payuni-logistics-api.md
│   ├── smilepay-logistics-api.md         # Pay_zg 矩陣
│   ├── pchomepay-logistics-api.md        # NDJSON 對帳 parser
│   ├── paynow-logistics-api.md           # Logistic_service 產品線
│   ├── ezship-logistics-api.md
│   ├── hct-logistics-api.md              # 直連 HCT
│   ├── lalamove-logistics-api.md
│   ├── ondemand-delivery.md              # Lalamove / pandago / Uber Direct
│   └── carrier-direct-access.md          # 無公開 API 的物流業者與替代路徑
├── examples/                             # Python 範例
└── data/                                 # search / recommend 使用的 CSV
    ├── providers.csv                    # 可串接 + 僅供查詢
    ├── operations.csv
    ├── logistics-types.csv              # 各家實際參數值（子類型／溫層／代收上限）
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

依各家官方規格整理，實際參數值見 `data/logistics-types.csv`。

| 服務商 | 7-11 | 全家 | 萊爾富 | OK | 黑貓 | 其他 |
|---|---|---|---|---|---|---|
| ECPay | B2C（含冷凍）+ C2C | B2C + C2C | B2C + C2C | C2C | 常溫／冷藏／冷凍 | 中華郵政 |
| NewebPay | B2C + C2C | C2C | C2C | C2C | — | — |
| PAYUNi | B2C + C2C（常溫／冷凍） | — | — | — | 常溫／冷凍／冷藏 | — |
| SmilePay | B2C + C2C | C2C | — | — | 含逆物流 | — |
| PChomePay | 取貨付款 | 取貨付款 | 取貨付款 | — | — | — |
| PayNow | B2C + C2C（含冷凍） | B2C + C2C（含冷凍） | C2C | C2C | 宅配、到店 | 7-11 海外 |
| ezShip | — | C2C | C2C | C2C | — | 宅配、店港澳 |
| HCT 直連 | — | — | — | — | — | 新竹物流 |

## 相關套件

本套件是 **[Taiwan E-Commerce Toolkit](https://github.com/Moksa1123/taiwan-ecommerce-toolkit)** 的一部分：

- [taiwan-invoice-skill](https://www.npmjs.com/package/taiwan-invoice-skill) — 7 家電子發票加值中心 + 財政部大平台查詢
- [taiwan-payment-skill](https://www.npmjs.com/package/taiwan-payment-skill) — 14 家金流

## 授權

[MIT License](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/LICENSE)

---

<p align="center">
  <sub>Made by <strong>Moksa</strong></sub><br>
  <sub>service@moksaweb.com</sub>
</p>
