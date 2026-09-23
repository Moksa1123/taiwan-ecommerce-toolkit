<h1 align="center">taiwan-payment-skill</h1>

<h3 align="center">台灣金流 AI 開發技能包</h3>

<p align="center">
  <strong>14 家金流平台一次串接</strong>
</p>

<p align="center">
  ECPay · NewebPay · PAYUNi · SmilePay · PChomePay · ezPay · PayNow · Shopline · LINE Pay · TapPay
</p>

<p align="center">
  <a href="https://www.npmjs.com/package/taiwan-payment-skill"><img src="https://img.shields.io/npm/v/taiwan-payment-skill?style=flat-square&logo=npm" alt="npm version"></a>
  <a href="https://www.npmjs.com/package/taiwan-payment-skill"><img src="https://img.shields.io/npm/dm/taiwan-payment-skill?style=flat-square&label=downloads" alt="npm downloads"></a>
  <img src="https://img.shields.io/badge/providers-14-success?style=flat-square" alt="14 Providers">
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

## 14 家金流平台

| 服務商 | 加密 / 認證 | 特色 |
|---|---|---|
| **ECPay 綠界** | SHA256 CheckMacValue | 市佔率最高、文檔最完整 |
| **NewebPay 藍新** | AES-256-CBC + SHA256 | MPG 整合、信用卡記憶、13 種支付 |
| **PAYUNi 統一** | AES-256-GCM + SHA256 | RESTful JSON、AFTEE、iCash |
| **SmilePay 速買配** | Verify_key + 加權檢核碼 | 無 AES、ibon / FamiPort 直接打單 |
| **PChomePay 拍錢包** | Basic Auth → 8h pcpay-token | PChome 生態、5% P 幣回饋、金物流二合一 |
| **ezPay 簡單付** | AES-256-CBC（32-byte padding）+ SHA256 | 電子支付機構；境內 TWQR / ezPay 錢包，跨境支付寶 / 微信 |
| **PayNow 立吉富** | JWT Bearer (現代) / 動態 AES-256 (傳統) | 雙 API、Stripe-like、Apple Pay 完整 |
| **Shopline Payments** | merchantId + apiKey | 金額以分為單位、HMAC-SHA256 webhook |
| **LINE Pay v4** | Channel ID/Secret + HMAC-SHA256 + Nonce | Request→Confirm 兩段、Preapproved Pay |
| **TapPay** | Partner Key (Header) | PCI 隔離、Prime 兩段式、Card Token |
| **O'Pay 歐付寶** | SHA256 CheckMacValue（同 ECPay） | 與 ECPay 同源架構、AccountLink 銀行快付、延遲撥款 |
| **JKOPAY 街口** | api-key Header + HMAC-SHA256 digest | 線上支付 / POS / 授權扣款 |
| **SunPay 紅陽** | RSA 分段加密 + SHA256 check_value | 金流 + 發票 + 超商代收 |
| **GoMyPay** | 需申請文件 | 參數規格待補 |

O'Pay、GoMyPay 以外皆附可執行 Python 範例，加解密以官方測試向量驗證；錯誤碼見 `data/error-codes.csv`。

## 技能包內容

```
taiwan-payment/
├── SKILL.md                              # AI 技能主文檔
├── EXAMPLES.md                           # 實戰範例集
├── references/                           # 各服務商 API 規格
│   ├── ecpay-payment-api.md
│   ├── newebpay-payment-api.md
│   ├── payuni-payment-api.md
│   ├── smilepay-payment-api.md          # Mid_smilepay 加權檢核碼
│   ├── pchomepay-payment-api.md         # 含 8h token 流程
│   ├── ezpay-payment-api.md             # 電子支付平台 + 跨境（依官方手冊）
│   ├── paynow-payment-api.md            # 雙 API 並行
│   ├── shopline-payment-api.md          # Redirect + Embedded
│   ├── linepay-payment-api.md           # HMAC + Preapproved
│   ├── tappay-payment-api.md            # Prime + Token 重複扣款
│   ├── opay-payment-api.md
│   ├── jkopay-payment-api.md
│   ├── sunpay-payment-api.md
│   ├── gomypay-payment-api.md
│   └── twqr-ewallet-landscape.md        # 電子支付／TWQR 生態
├── examples/                             # 可執行 Python 範例
└── data/                                 # search / recommend 使用的 CSV
    ├── providers.csv
    ├── operations.csv
    ├── payment-methods.csv
    ├── error-codes.csv                  # 各家官方錯誤碼
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

- [taiwan-invoice-skill](https://www.npmjs.com/package/taiwan-invoice-skill) — 7 家電子發票加值中心 + 財政部大平台查詢
- [taiwan-logistics-skill](https://www.npmjs.com/package/taiwan-logistics-skill) — 7 家物流 aggregator + HCT 直連 + 3 家即時配送

## 授權

[MIT License](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/LICENSE)

---

<p align="center">
  <sub>Made by <strong>Moksa</strong></sub><br>
  <sub>service@moksaweb.com</sub>
</p>
