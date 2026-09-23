<h1 align="center">taiwan-invoice-skill</h1>

<h3 align="center">台灣電子發票 AI 開發技能包</h3>

<p align="center">
  <strong>支援 ECPay 綠界 · SmilePay 速買配 · Amego 光貿 · ezPay 簡單付 · PayNow 立吉富 · O'Pay 歐付寶 · SunPay 紅陽 · 財政部大平台</strong>
</p>

<p align="center">
  <a href="https://www.npmjs.com/package/taiwan-invoice-skill"><img src="https://img.shields.io/npm/v/taiwan-invoice-skill?style=flat-square&logo=npm" alt="npm version"></a>
  <a href="https://www.npmjs.com/package/taiwan-invoice-skill"><img src="https://img.shields.io/npm/dm/taiwan-invoice-skill?style=flat-square&label=downloads" alt="npm downloads"></a>
  <img src="https://img.shields.io/badge/providers-9-success?style=flat-square" alt="9 Providers">
  <img src="https://img.shields.io/badge/AI%20platforms-14-blue?style=flat-square" alt="14 AI Platforms">
  <a href="https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/LICENSE"><img src="https://img.shields.io/github/license/Moksa1123/taiwan-ecommerce-toolkit?style=flat-square" alt="License"></a>
</p>

<p align="center">
  <a href="https://paypal.me/cccsubcom"><img src="https://img.shields.io/badge/PayPal-支持開發-00457C?style=for-the-badge&logo=paypal&logoColor=white" alt="PayPal"></a>
</p>

---

## 安裝

```bash
npm install -g taiwan-invoice-skill
```

## 快速開始

```bash
cd /path/to/your/project

taiwan-invoice init                    # 互動式選擇 AI 助手
taiwan-invoice init --ai claude        # Claude Code
taiwan-invoice init --ai cursor        # Cursor
taiwan-invoice init --ai windsurf      # Windsurf
taiwan-invoice init --ai all           # 全部安裝
```

安裝完後，直接在 AI 助手用自然語言：

```
使用 ECPay 測試環境開立 B2C 發票，金額 1050 元
建立 ezPay B2B 發票，買方統編 12345678，未稅 1000、稅 50
為 PayNow POS 機批次取 100 個發票號碼
```

---

## 發票服務商

| 服務商 | 加密 / 認證 | 適用場景 |
|---|---|---|
| **ECPay 綠界** | AES-128-CBC + HashKey/HashIV | 市佔率最高、SDK 完整、傳統電商首選 |
| **SmilePay 速買配** | Grvc + Verify_key | 老牌穩定、整合最簡單、無 AES 門檻 |
| **Amego 光貿** | MD5 簽章 + App Key | MIG 4.0 標準、現代 RESTful |
| **ezPay 簡單付** | AES-256-CBC + 32 碼 HashKey + SHA256 | 藍新金流集團小型品牌、字軌管理、批次開立 |
| **PayNow 立吉富** | JWT Bearer Token | 金物流發票一站式、POS 機批次取號流程 |
| **O'Pay 歐付寶** | MerchantID + RqHeader + AES 加密 Data | 與綠界發票 API 同源架構 |
| **SunPay 紅陽** | Token 欄位 AES-128-CBC | 可與紅陽金流搭配隨交易自動開立 |
| **財政部大平台** | AppID + APIKey（HMAC-SHA256 加簽）| 只做查詢／驗證（手機條碼、捐贈碼、中獎號碼），不能開立 |

另列關貿（TradeVAN）於 `data/providers.csv`，尚未收錄 reference。

ECPay、ezPay、O'Pay、PayNow、SunPay 附可執行 Python 範例，加解密以官方測試向量驗證；SmilePay、Amego 見 EXAMPLES.md 與 references。

## 技能包內容

```
taiwan-invoice/
├── SKILL.md                          # AI 技能主文檔
├── EXAMPLES.md                       # 完整範例集
├── references/                       # 各服務商 API 規格
│   ├── ECPAY_API_REFERENCE.md
│   ├── SMILEPAY_API_REFERENCE.md
│   ├── AMEGO_API_REFERENCE.md
│   ├── EZPAY_API_REFERENCE.md
│   ├── PAYNOW_API_REFERENCE.md
│   ├── OPAY_API_REFERENCE.md
│   ├── SUNPAY_API_REFERENCE.md
│   ├── MOF_EINVOICE_API_REFERENCE.md # 財政部大平台（查詢）
│   └── VAC_LANDSCAPE.md             # 加值中心生態
├── examples/                         # 可執行 Python 範例
└── data/                             # search / recommend 使用的 CSV
    ├── providers.csv
    ├── operations.csv
    ├── error-codes.csv              # 各家官方錯誤碼
    └── ...
```

## CLI 指令

```bash
taiwan-invoice list                # 列出 AI 平台
taiwan-invoice info                # 技能資訊
taiwan-invoice update              # 檢查更新
taiwan-invoice init --force        # 覆蓋安裝
taiwan-invoice init --global       # 全域安裝
```

## 14 個 AI 平台支援

Claude Code · Cursor · Windsurf · Antigravity · GitHub Copilot · Kiro · Codex · Qoder · Cline · Gemini · Trae · OpenCode · Continue · CodeBuddy

## 相關套件

本套件是 **[Taiwan E-Commerce Toolkit](https://github.com/Moksa1123/taiwan-ecommerce-toolkit)** 的一部分：

- [taiwan-payment-skill](https://www.npmjs.com/package/taiwan-payment-skill) — 14 家金流
- [taiwan-logistics-skill](https://www.npmjs.com/package/taiwan-logistics-skill) — 7 家物流 aggregator + HCT 直連 + 3 家即時配送

## 授權

[MIT License](https://github.com/Moksa1123/taiwan-ecommerce-toolkit/blob/main/LICENSE)

---

<p align="center">
  <sub>Made by <strong>Moksa</strong></sub><br>
  <sub>service@moksaweb.com</sub>
</p>
