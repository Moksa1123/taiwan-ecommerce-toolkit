# 電子發票加值中心生態地圖與選型

> Captured: 2026-08-08
> 財政部核准之電子發票系統／加值服務業者約 **134～168 家**（不同來源統計基準不同）。
> 本文件說明這個生態怎麼分層、我們收錄哪些、以及沒收錄的怎麼辦。

## 0. 三層架構

```
┌──────────────────────────────────────────┐
│ 財政部電子發票整合服務平台（大平台）        │  ← 唯一的上游
│ api.einvoice.nat.gov.tw                  │     MOF_EINVOICE_API_REFERENCE.md
└──────────────────────────────────────────┘
              ▲                    ▲
      批次上傳 │              自建 │ Turnkey
              │                    │
┌─────────────┴────────────┐  ┌────┴─────────┐
│ 加值中心（134~168 家）     │  │ 大型企業自建   │
│ ECPay / O'Pay / ezPay /  │  │ 直接對接大平台 │
│ Amego / SmilePay / …     │  │              │
└─────────────┬────────────┘  └──────────────┘
              │ 自家 API
       ┌──────┴──────┐
       │  你的系統     │
       └─────────────┘
```

**關鍵理解**：加值中心不是「發票的來源」，它是**幫你和財政部之間做批次上傳與格式轉換的中介**。發票號碼（字軌）是財政部配給你的，加值中心只是代管。

這也解釋了幾件事：
- 為什麼作廢有期限（財政部規定當期內）
- 為什麼「已開立但未上傳」的發票不能作廢（ezPay `LIB10009`）
- 為什麼各家的上傳時間都是凌晨批次（ezPay 每日 01:00 上傳、06:00 更新狀態）

## 1. 本 skill 已收錄（6 家）

| 加值中心 | 加密 | 特色 | doc_access | Reference |
|---|---|---|---|---|
| **ECPay 綠界** | AES-128-CBC + 三層信封 | 市佔最高、文件最完整、官方有 AI skill | public | [ECPAY_API_REFERENCE.md](ECPAY_API_REFERENCE.md) |
| **O'Pay 歐付寶** | AES + 三層信封 | **B2B 完整存證流程 + 離線 POS** | public | [OPAY_API_REFERENCE.md](OPAY_API_REFERENCE.md) |
| **ezPay 簡單付** | AES-256-CBC + Hex + CheckCode | 藍新集團、字軌管理、批次開立 | apply | [EZPAY_API_REFERENCE.md](EZPAY_API_REFERENCE.md) |
| **Amego 光貿** | MD5 簽章 | **MIG 4.0**、統編查詢、PDF 下載、測試正式共用 URL | public | [AMEGO_API_REFERENCE.md](AMEGO_API_REFERENCE.md) |
| **SmilePay 速買配** | Verify_key | 雙協定 GET/POST、簡單整合、XML 回應 | public | [SMILEPAY_API_REFERENCE.md](SMILEPAY_API_REFERENCE.md) |
| **PayNow 立吉富** | JWT Bearer | 金物流發票一站式、**POS 批次取號** | apply | [PAYNOW_API_REFERENCE.md](PAYNOW_API_REFERENCE.md) |

## 2. 已知但未收錄的主要加值中心

| 加值中心 | 說明 | doc_access | 為何未收錄 |
|---|---|---|---|
| **關貿網路 TradeVAN** | 最大加值中心之一。蝦皮供應商電子發票平台走它。另有 EzSign 數位簽章平台 | apply/contract | 文件需申請；市佔重要，**列為後續優先** |
| **精誠 Systex 金融科技** | 大型系統整合商體系 | contract | 無公開文件 |
| **中華電信** | invoice.cht.com.tw、einvoice.hisales.hinet.net | contract | 無公開文件 |
| **紅陽科技 SunPay** | inv.sunpay.com.tw，有技術手冊 v2.3 | public | 已在金流端建檔，發票端待補（見 [../../taiwan-payment/references/sunpay-payment-api.md](../../taiwan-payment/references/sunpay-payment-api.md)） |
| **GoMyPay** | einvoice.gomypay.asia | apply | 已在金流端建檔 |
| **訊航科技** | einvoice.net.tw | contract | 無公開文件 |
| **e首發票** | youshop.com.tw，支援多電商平台 API 串接、Email/SMS/LINE 通知 | apply | 小型 |
| 其餘 ~120+ 家 | 長尾，多為區域性或垂直產業 | contract | — |

完整名單查詢：https://www.einvoice.nat.gov.tw/ptl008w

## 3. 選型決策

### 依需求分流

| 你的情況 | 建議 |
|---|---|
| 已在用某家金流（ECPay/藍新/PAYUNi…） | **用同一家的發票**。金流與發票同源可省掉對帳串接 |
| 純發票需求、要 MIG 4.0 且要統編查詢 | Amego 光貿 |
| 要 **B2B 存證**（開給營業人、需對方確認） | O'Pay 歐付寶（流程最完整）或 Amego |
| 有**實體門市 POS**、需離線開立 | O'Pay（離線 API）或 PayNow（POS 批次取號） |
| 要最完整文件與社群資源 | ECPay 綠界 |
| 要最簡單（不想處理 AES） | SmilePay（Verify_key）或 Amego（MD5） |
| 蝦皮供應商 | 大機率被指定走 TradeVAN |
| 開立量極大（日均萬張以上）、有 IT 團隊 | 評估自建 Turnkey 直連財政部 |

### 加值中心 vs 自建 Turnkey

| 面向 | 加值中心 | 自建 Turnkey |
|---|---|---|
| 開發成本 | 低（串一組 API） | 高（要處理 MIG XML、憑證、上傳排程、錯誤重送） |
| 月費/單價 | 有 | 無（但有系統維運成本） |
| 字軌管理 | 代管 | 自管 |
| 上傳時效 | 依該中心批次時間（多為隔日凌晨） | 自行掌控 |
| 出錯責任 | 中心協助 | 自負 |
| 適用 | 絕大多數電商 | 大型零售、連鎖、日開立量極大者 |

**判斷點**：加值中心的費用通常按張計價。若你的月開立量乘上單價，已經超過一個工程師維護 Turnkey 的成本，才值得自建。多數電商永遠不會到這個點。

## 4. 跨加值中心共通的坑

這些是本 skill `data/troubleshooting.csv` 已收錄的模式，換哪一家都會遇到：

1. **開立 ≠ 上傳**。多數中心是隔日批次上傳財政部。未上傳的發票不能作廢（只能等），跨期就只能開折讓。
2. **暫存狀態**。ezPay 的 `Status=0`、O'Pay 的 `DelayIssue` 都是「先建資料不開立」。若沒呼叫觸發 API，發票**永遠不會存在**。
3. **手機條碼／捐贈碼驗證**。各家都提供 `CheckBarcode` / `CheckLoveCode`，上游都是財政部。**別自己寫格式檢查就當驗證過**——手機條碼格式對不代表存在。
4. **字軌用罄**。要設餘量通知（O'Pay `RemainNotifySetting`、其他家有對應機制），不然月底開不出來。
5. **MIG 版本**。MIG 3.2.1 已於 2025/01/01 停用，全面走 **MIG 4.0**。舊系統若還在 3.2.1 會被退件。

## 5. 相關文件

- 財政部大平台 API（手機條碼、載具、捐贈碼、中獎號碼）：[MOF_EINVOICE_API_REFERENCE.md](MOF_EINVOICE_API_REFERENCE.md)
- 加值中心名單查詢：https://www.einvoice.nat.gov.tw/ptl008w
- 已完成代境外電商上傳雲端發票之加值中心名單：https://www.einvoice.nat.gov.tw/static/ptl/ein_upload/attachments/1570498596353_0.pdf

## 6. 來源

- 財政部加值中心查詢 — https://www.einvoice.nat.gov.tw/ptl008w
- 關貿網路電子發票 — https://services.tradevan.com.tw/e-commerce/e-invoice/ ／ https://neinv.tradevan.com.tw/
- 中華電信電子發票 — https://invoice.cht.com.tw/
- 訊航科技 — https://einvoice.net.tw/
- e首發票 — https://www.youshop.com.tw/pricing.html
- GoMyPay 發票加值中心 — https://einvoice.gomypay.asia/
- 紅陽電子發票 — https://inv.sunpay.com.tw/
