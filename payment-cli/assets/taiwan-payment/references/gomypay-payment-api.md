# GoMyPay 台灣萬事達金流 API 參考

> 文件下載: https://n.gomypay.asia/MDocuments_downloads.aspx
> 電子發票加值中心: https://einvoice.gomypay.asia/
> Captured: 2026-08-08 · doc_access: **apply**（部分文件公開，完整 API 須洽客服）
> Status: **partial** — 服務範圍已確認，參數層待補

## 0. 定位

GoMyPay（台灣萬事達金流股份有限公司）是台灣合規的第三方支付金融服務機構，同時經營電子發票加值中心。

**規模上小於前段班**（ECPay、NewebPay、PAYUNi），收錄的理由是：

1. 有部分公開文件與購物車模組
2. **行動支付覆蓋較完整**——台灣PAY、悠遊付、Apple Pay、Google Pay 都有專屬手冊
3. 自營電子發票加值中心，可金流＋發票一家搞定

## 1. 服務範圍

| 類別 | 服務 |
|---|---|
| 信用卡 | 信用卡交易、銀聯卡交易、定期扣款 |
| 現金 | WEBATM、虛擬帳號、超商條碼 |
| 行動支付 | 台灣PAY、悠遊付、Apple Pay、Google Pay |
| 微信 | 微信支付（線上／線下） |
| 物流 | 商家資料表、超商代碼繳費流程 |
| 發票 | 電子發票（自營加值中心） |

## 2. 公開文件

文件下載頁 https://n.gomypay.asia/MDocuments_downloads.aspx 列出：

| 類別 | 項目 |
|---|---|
| 購物車模組 | WooCommerce V2 (v1.6.4)、WooCommerce V1 (v1.1.0)、Magento2、OpenCart |
| 行動支付手冊 | 台灣PAY、悠遊付、Apple Pay、Google Pay |
| 微信支付 API | 線上版、線下版 |
| 物流相關 | 商家資料表、超商代碼繳費流程 |

⚠️ **未公開列出**：信用卡、WebATM、虛擬帳號、超商條碼、定期扣款的獨立 API 文件。頁面僅提供「完整 API 文件」的概括指引，須「前往完整下載專區」或聯絡技術團隊取得。

## 3. 值得注意的一點

GoMyPay 是少數把**悠遊付**列為獨立手冊的聚合商。悠遊付（悠遊卡股份有限公司）本身不公開商家文件（見 [twqr-ewallet-landscape.md](twqr-ewallet-landscape.md) §1），因此 GoMyPay 的悠遊付手冊是目前盤點到取得該錢包串接規格的可行路徑之一。

同理，台灣PAY 手冊對理解 TWQR／台灣Pay 的實際欄位也有參考價值。

## 4. 待補

| 項目 | 優先 |
|---|---|
| 信用卡建單端點與參數 | 高 |
| 檢查碼／加密機制 | 高 |
| 定期扣款流程 | 中 |
| 行動支付各手冊的欄位（台灣PAY／悠遊付） | 中 — 有跨 provider 對照價值 |
| 錯誤碼表 | 中 |
| 電子發票 API（einvoice.gomypay.asia） | 中 |

## 5. 來源

- 文件下載 — https://n.gomypay.asia/MDocuments_downloads.aspx
- 電子發票加值中心 — https://einvoice.gomypay.asia/
