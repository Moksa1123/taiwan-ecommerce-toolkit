# GoMyPay 台灣萬事達金流 API 參考

> 文件下載: https://n.gomypay.asia/MDocuments_downloads.aspx
> 電子發票加值中心: https://einvoice.gomypay.asia/
> 文件公開程度：apply（**完整 API 規格需向 GoMyPay 申請**）

## 0. 定位

GoMyPay（台灣萬事達金流股份有限公司）是台灣合規的第三方支付金融服務機構，同時經營電子發票加值中心。

規模小於 ECPay、NewebPay、PAYUNi。收錄的理由：

1. 有官方購物車模組（WooCommerce、Magento2、OpenCart）
2. 行動支付涵蓋台灣PAY、悠遊付、Apple Pay、Google Pay
3. 自營電子發票加值中心，金流與發票可同一家

## 1. 服務範圍

| 類別 | 服務 |
|---|---|
| 信用卡 | 信用卡（含分期）、銀聯卡、定期扣款 |
| 現金 | WEBATM、虛擬帳號、超商條碼、超商代碼 |
| 行動支付 | 台灣PAY、悠遊付、Apple Pay、Google Pay |
| 微信 | 微信支付（線上／線下） |
| 發票 | 電子發票（自營加值中心） |

## 2. 文件取得

文件下載頁 https://n.gomypay.asia/MDocuments_downloads.aspx 列出：

| 類別 | 項目 |
|---|---|
| 購物車模組 | WooCommerce V2 (v1.6.4)、WooCommerce V1 (v1.1.0)、Magento2、OpenCart |
| 行動支付手冊 | 台灣PAY、悠遊付、Apple Pay、Google Pay |
| 微信支付 API | 線上版、線下版 |
| 其他 | 物流商家資料表、超商代碼繳費流程 |

- 下載頁的行動支付手冊是**消費者操作說明**，不含 API 欄位；各行動支付的串接技術文件需由商家後台取得。
- 信用卡、WebATM、虛擬帳號、超商條碼／代碼、定期扣款的 API 規格書**未公開**，需向 GoMyPay 申請。
- GoMyPay 提供的文件標示為機密、禁止傳播，本 skill 不收錄其欄位細節。

## 3. 串接建議

- 需要 GoMyPay 時，先向其取得 API 規格書與測試帳號，再依規格實作。
- 只需要悠遊付／台灣PAY 收款、又不想走申請流程時，可改用 TWQR 或其他聚合商，見 [twqr-ewallet-landscape.md](twqr-ewallet-landscape.md)。

## 4. 來源

- 文件下載 — https://n.gomypay.asia/MDocuments_downloads.aspx
- 電子發票加值中心 — https://einvoice.gomypay.asia/
