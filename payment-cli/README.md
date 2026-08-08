<h1 align="center">taiwan-payment-skill</h1>

<h3 align="center">台灣金流 AI 開發技能包</h3>

<p align="center">
  <strong>10 大金流平台一次串接</strong>
</p>

<p align="center">
  ECPay · NewebPay · PAYUNi · SmilePay · PChomePay · ezPay · PayNow · Shopline · LINE Pay · TapPay
</p>

<p align="center">
  <a href="https://www.npmjs.com/package/taiwan-payment-skill"><img src="https://img.shields.io/npm/v/taiwan-payment-skill?style=flat-square&logo=npm" alt="npm version"></a>
  <a href="https://www.npmjs.com/package/taiwan-payment-skill"><img src="https://img.shields.io/npm/dm/taiwan-payment-skill?style=flat-square&label=downloads" alt="npm downloads"></a>
  <img src="https://img.shields.io/badge/providers-10-success?style=flat-square" alt="10 Providers">
  <img src="https://img.shields.io/badge/AI%20platforms-14-blue?style=flat-square" alt="14 AI Platforms">
  <a href="https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/LICENSE"><img src="https://img.shields.io/github/license/Moksa1123/taiwan-ecommerce-toolkit?style=flat-square" alt="License"></a>
</p>

<p align="center">
  <a href="https://paypal.me/cccsubcom"><img src="https://img.shields.io/badge/PayPal-支持開發-00457C?style=for-the-badge&logo=paypal&logoColor=white" alt="PayPal"></a>
</p>

---

## 安裝

```bash
npm install -g taiwan-payment-skill
```

## 快速開始

```bash
cd /path/to/your/project

taiwan-payment init                    # 互動式
taiwan-payment init --ai claude        # Claude Code
taiwan-payment init --ai cursor        # Cursor
taiwan-payment init --ai windsurf      # Windsurf
taiwan-payment init --ai all           # 全部安裝
```

安裝完後，AI 助手裡用自然語言：

```
建立 ECPay 信用卡付款訂單，金額 2500 元
NewebPay MPG 整合 LINE Pay + Apple Pay
PChomePay 拍錢包訂單，5% P 幣回饋
PayNow PaymentIntent，啟用 LINE Pay 線上+線下扣款
TapPay 用 Prime 一次付清，remember=true 存成 card_token 供下次自動扣款
```

---

## 10 家金流平台

| 服務商 | 加密 / 認證 | 特色 |
|---|---|---|
| **ECPay 綠界** | SHA256 CheckMacValue | 市佔率最高、文檔最完整 |
| **NewebPay 藍新** | AES-256-CBC + SHA256 | MPG 整合、信用卡記憶、13 種支付 |
| **PAYUNi 統一** | AES-256-GCM + SHA256 | RESTful JSON、AFTEE、iCash |
| **SmilePay 速買配** | Verify_key + 加權檢核碼 | 無 AES、ibon / FamiPort 直接打單 |
| **PChomePay 拍錢包** | Basic Auth → 8h pcpay-token | PChome 生態、5% P 幣回饋、金物流二合一 |
| **ezPay 簡單付** | 同 NewebPay (AES-256-CBC) | 藍新小型商家品牌、低門檻 |
| **PayNow 立吉富** | JWT Bearer (現代) / 動態 AES-256 (傳統) | 雙 API、Stripe-like、Apple Pay 完整 |
| **Shopline Payments** | merchantId + apiKey | 金額以分為單位、HMAC-SHA256 webhook |
| **LINE Pay v4** | Channel ID/Secret + HMAC-SHA256 + Nonce | Request→Confirm 兩段、Preapproved Pay |
| **TapPay** | Partner Key (Header) | PCI 隔離、Prime 兩段式、Card Token |

每家附完整 Python 範例 + 反推的加密實作 + 錯誤碼對照 + 測試帳號。

## 技能包內容

```
taiwan-payment/
├── SKILL.md                              # AI 技能主文檔
├── EXAMPLES.md                           # 實戰範例集
├── references/                           # 10 份 API 規格 (~9,200 行)
│   ├── ecpay-payment-api.md
│   ├── newebpay-payment-api.md
│   ├── payuni-payment-api.md
│   ├── smilepay-payment-api.md          # 反推 Mid_smilepay 加權檢核碼
│   ├── pchomepay-payment-api.md         # 含 8h token 流程
│   ├── ezpay-payment-api.md             # diff vs Newebpay
│   ├── paynow-payment-api.md            # 雙 API 並行
│   ├── shopline-payment-api.md          # Redirect + Embedded
│   ├── linepay-payment-api.md           # HMAC + Preapproved
│   └── tappay-payment-api.md            # Prime + Token 重複扣款
├── examples/                             # 10 個生產級 Python 範例
└── data/                                 # 7 份 CSV
    ├── providers.csv                    # 10 服務商完整比較
    ├── operations.csv                   # 26 個 API 操作
    ├── payment-methods.csv              # 25+ 支付方式對照
    ├── error-codes.csv                  # 130+ 錯誤碼
    └── ...
```

## CLI 指令

```bash
taiwan-payment list                # 列出 AI 平台
taiwan-payment info                # 技能資訊
taiwan-payment update              # 檢查更新
taiwan-payment init --force        # 覆蓋安裝
taiwan-payment init --global       # 全域安裝
```

## 14 個 AI 平台支援

Claude Code · Cursor · Windsurf · Antigravity · GitHub Copilot · Kiro · Codex · Qoder · Cline · Gemini · Trae · OpenCode · Continue · CodeBuddy

## 相關套件

本套件是 **[Taiwan E-Commerce Toolkit](https://github.com/Moksa1123/taiwan-ecommerce-toolkit)** 的一部分：

- [taiwan-invoice-skill](https://www.npmjs.com/package/taiwan-invoice-skill) — 5 家電子發票
- [taiwan-logistics-skill](https://www.npmjs.com/package/taiwan-logistics-skill) — 7 家物流（含 HCT 直連）

## 授權

[MIT License](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/LICENSE)

---

<p align="center">
  <sub>Made by <strong>Moksa</strong></sub><br>
  <sub>service@moksaweb.com</sub>
</p>
