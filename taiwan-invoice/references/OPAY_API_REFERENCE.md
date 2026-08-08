# 歐付寶 O'Pay 電子發票 API 參考

> Source:《歐付寶電子發票 B2C API》(opay_i100.pdf, 149 頁)、《B2B API》(opay_i200.pdf, 134 頁)、《離線電子發票 API》(opay_i301.pdf, 55 頁)
> 文件總覽: https://developers.opay.tw/download/document
> Captured: 2026-08-08 · doc_access: **public**（PDF 免登入直連下載）

## 0. 與 ECPay 綠界發票的關係

歐付寶發票 API 與綠界電子發票 API **結構同源**：同樣的 `MerchantID` + `RqHeader` + `Data` 三層信封、同樣的 AES 加密資料層、同樣的 `/B2CInvoice/Issue` 路徑命名。差別在網域與金鑰。

已熟悉 [ECPAY_API_REFERENCE.md](ECPAY_API_REFERENCE.md) 者，遷移成本很低。

**但歐付寶多了一塊 ECPay 沒有的：完整的 B2B 存證流程與離線 POS 發票。**

## 1. 環境

| 環境 | Base URL |
|---|---|
| 測試 | `https://einvoice-stage.opay.tw` |
| 正式 | `https://einvoice.opay.tw` |
| 廠商後台（測試） | `https://vendor-stage.opay.tw` |
| 廠商後台（正式） | `https://vendor.opay.tw` |

後台操作手冊：https://vendor.opay.tw/Content/themes/new20150706/EinvoiceManual.pdf

## 2. 請求信封格式

所有 API 皆為 `POST`，JSON body，三層結構：

```json
{
  "MerchantID": "2000132",
  "RqHeader": {
    "Timestamp": 1525168923
  },
  "Data": "…（加密後字串）…"
}
```

| 欄位 | 說明 |
|---|---|
| `MerchantID` | 特店編號。**平台商使用時，此欄位僅限帶入已綁定的子廠商編號** |
| `RqHeader.Timestamp` | Unix timestamp |
| `Data` | 業務參數，加密後字串 |

回應同樣為三層：

```json
{
  "MerchantID": "2000132",
  "RqHeader": { "Timestamp": 1525169058 },
  "TransCode": 1,
  "TransMsg": "",
  "Data": "…"
}
```

`TransCode = 1` 代表**傳輸資料（MerchantID, RqHeader, Data）接收成功**，其餘均為失敗。

> ⚠️ `TransCode=1` 只代表**信封收到了**，不代表發票開立成功。業務結果在解密後的 `Data` 裡（`RtnCode`）。這是兩層錯誤處理，常被漏掉。

平台商模式下，`Data` 內另有一層 `MerchantID` 指向實際子廠商。

## 3. B2C 發票 API 端點

Base: `https://einvoice.opay.tw/B2CInvoice/`（測試環境 `einvoice-stage`）

### 開立與作廢

| 端點 | 功能 |
|---|---|
| `Issue` | 開立發票 |
| `DelayIssue` | 延遲開立 |
| `CancelDelayIssue` | 取消延遲開立 |
| `TriggerIssue` | 觸發開立（延遲開立的實際觸發） |
| `Invalid` | 作廢發票 |
| `VoidWithReIssue` | 作廢並重開 |
| `GetIssue` | 查詢開立結果 |
| `GetInvalid` | 查詢作廢結果 |

> 延遲開立三兄弟（`DelayIssue` → `TriggerIssue` / `CancelDelayIssue`）與 ezPay 的 `Status=0` 暫存機制解決同一個問題：先建資料、確認出貨後才真正開立。實作上要注意**未觸發的發票永遠不會上傳財政部**。

### 折讓

| 端點 | 功能 |
|---|---|
| `Allowance` | 開立折讓 |
| `AllowanceByCollegiate` | 協議折讓 |
| `AllowanceInvalid` | 作廢折讓 |
| `AllowanceInvalidByCollegiate` | 作廢協議折讓 |
| `GetAllowanceList` | 查詢折讓清單 |
| `GetAllowanceInvalid` | 查詢作廢折讓 |

> **一般折讓 vs 協議折讓**：一般折讓由賣方單方開立；協議折讓需買賣雙方確認。稅務效果不同，別混用。

### 字軌管理

| 端點 | 功能 |
|---|---|
| `AddInvoiceWordSetting` | 新增字軌設定 |
| `GetInvoiceWordSetting` | 查詢字軌設定 |
| `UpdateInvoiceWordStatus` | 更新字軌狀態（啟用/停用） |
| `GetGovInvoiceWordSetting` | 查詢財政部配號結果 |

### 查驗與工具

| 端點 | 功能 |
|---|---|
| `CheckBarcode` | **手機條碼驗證** |
| `CheckLoveCode` | **捐贈碼（愛心碼）驗證** |
| `GetCompanyNameByTaxID` | 依統編查公司名稱 |
| `InvoicePrint` | 發票列印 |
| `InvoiceNotify` | 發票通知（寄送 Email/SMS） |
| `InvoiceNotifySetting` / `GetInvoiceNotifySetting` | 通知設定 |
| `RemainNotifySetting` / `GetRemainNotifySetting` | 字軌餘量通知設定 |

> `CheckBarcode` / `CheckLoveCode` 上游就是財政部平台，見 [MOF_EINVOICE_API_REFERENCE.md](MOF_EINVOICE_API_REFERENCE.md)。若你已經在用歐付寶開發票，用這兩支就好，不必自己去申請財政部 AppID。

### 空白發票

| 端點 | 功能 |
|---|---|
| `QueryBlankInvoiceList` | 查詢空白發票清單 |
| `DownLoadBlankInvList` | 下載空白發票清單 |
| `BlankInvAutoUploadSetting` | 空白發票自動上傳設定 |

## 4. B2B 發票 API 端點

Base: `https://einvoice.opay.tw/B2BInvoice/`

B2B 走**存證**流程，每個動作都有「開立」與「確認」兩階段：

| 端點 | 功能 |
|---|---|
| `Issue` → `IssueConfirm` | 開立 → 確認 |
| `Invalid` → `InvalidConfirm` | 作廢 → 確認 |
| `Reject` → `RejectConfirm` | 退回 → 確認 |
| `Allowance` → `AllowanceConfirm` | 折讓 → 確認 |
| `CancelAllowance` → `CancelAllowanceConfirm` | 取消折讓 → 確認 |
| `VoidWithReIssue` | 作廢重開 |
| `GetIssue` | 查詢開立 |
| `AddInvoiceWordSetting` / `UpdateInvoiceWordStatus` | 字軌管理 |
| `MaintainMerchantCustomerData` | 維護客戶（買方營業人）資料 |
| `Notify` | 通知 |

> **B2B 與 B2C 最大差異**：B2B 有買方，所以每個動作都需要對方確認；且必須先用 `MaintainMerchantCustomerData` 建立買方資料。B2C 沒有這一層。

## 5. 離線電子發票 API

Base: `https://einvoice.opay.tw/B2CInvoice/`（與 B2C 共用網域，端點名有 `Offline` 前綴）

| 端點 | 功能 |
|---|---|
| `OfflineIssue` | 離線開立 |
| `OfflineInvalid` | 離線作廢 |
| `GetOfflineInvoiceWordSetting` | 查詢離線字軌設定 |
| `GetOfflineInvoiceWordSettingNumber` | 取得離線字軌號碼 |
| `GetOfflineInvoiceWordSettingWithAutoSplit` | 取得離線字軌（自動分段） |
| `GetOfflineMerchantInfo` | 查詢離線商家資訊 |
| `OfflineMerchantPosSetting` | POS 設定 |
| `QueryOfflineMerchantPosSetting` | 查詢 POS 設定 |

**應用場景**：實體門市 POS 在網路中斷時仍需開立發票。做法是**預先向平台批次取號**（`GetOfflineInvoiceWordSettingNumber`），本地端配號開立，恢復連線後再上傳。

`WithAutoSplit` 版本會自動把字軌區間切分給多台 POS，避免號碼衝突。

> 本 skill 已收錄的 provider 中，**PayNow 也有 POS 批次取號**（見 [PAYNOW_API_REFERENCE.md](PAYNOW_API_REFERENCE.md)）。若需求是實體門市，這兩家是目前有離線方案的選項。

## 6. 與其他加值中心的定位比較

| 面向 | O'Pay 歐付寶 | ECPay 綠界 | ezPay | Amego | SmilePay | PayNow |
|---|---|---|---|---|---|---|
| B2C | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| B2B 存證（含確認流程） | ✅ 完整 | 部分 | 部分 | ✅ | — | — |
| 離線 / POS 批次取號 | ✅ | — | — | — | — | ✅ |
| 文件公開 | ✅ 免登入 PDF | ✅ | 需帳號 | ✅ | ✅ | 部分 |
| 加密 | AES + 三層信封 | AES-128-CBC + 三層信封 | AES-256-CBC + Hex | MD5 簽章 | Verify_key | JWT |

## 7. 待驗證

本次以端點清單與信封結構為主，以下尚未逐欄擷取：

- `Data` 層的加密演算法與金鑰長度（推測與 ECPay 同為 AES-128-CBC + PKCS7，**須以 PDF §加密說明確認**）
- `Issue` 各業務欄位（`RelateNumber`、`CustomerID`、`TaxType`、`CarrierType`、`Items[]` 等）的完整定義
- 錯誤碼表
- B2B 各 `Confirm` 端點的必填欄位

原始 PDF 已下載可再解析；三份文件合計 338 頁。

## 8. 來源

- B2C 電子發票 API — https://developers.opay.tw/Content/Doc/opay_i100.pdf
- B2B 電子發票 API — https://developers.opay.tw/Content/Doc/opay_i200.pdf
- 離線電子發票 API — https://developers.opay.tw/Content/Doc/opay_i301.pdf
- 文件總覽 — https://developers.opay.tw/download/document
- 金流端 — [../../taiwan-payment/references/opay-payment-api.md](../../taiwan-payment/references/opay-payment-api.md)
