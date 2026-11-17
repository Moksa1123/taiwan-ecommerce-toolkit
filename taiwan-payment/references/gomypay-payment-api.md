# GoMyPay 台灣萬事達金流 API 參考

> 文件下載: https://n.gomypay.asia/MDocuments_downloads.aspx
> 電子發票加值中心: https://einvoice.gomypay.asia/
> 文件公開程度：apply（**完整 API 規格需向 GoMyPay 申請**）

## 0. 定位

GoMyPay（台灣萬事達金流股份有限公司）是台灣合規的第三方支付金融服務機構，同時經營電子發票加值中心。

規模小於 ECPay、NewebPay、PAYUNi。收錄的理由：

1. 有官方購物車模組（WooCommerce、Magento2、OpenCart）
2. 行動支付涵蓋台灣Pay、LINE Pay、悠遊付、一卡通、Apple Pay、Google Pay
3. 自營電子發票加值中心，金流與發票可同一家

## 1. 服務範圍

| 類別 | 服務 |
|---|---|
| 信用卡 | 國內／海外信用卡、分期（3～30 期）、銀聯卡、定期定額 |
| 現金 | Web ATM、虛擬帳號、超商條碼、超商代碼（7-ELEVEN、全家、萊爾富、OK） |
| 行動支付 | 台灣Pay、LINE Pay、悠遊付／悠遊卡、一卡通、Apple Pay、Google Pay |
| 跨境 | 支付寶、微信支付（另有新光微信線上／線下 API） |
| 發票 | 電子發票（自營加值中心） |

> 依官網金流服務頁 https://n.gomypay.asia/MCashFlow.aspx 與費率頁 https://n.gomypay.asia/ServiceRateList.aspx（2026-11-17 查核）。信用卡分期與 Apple Pay／Google Pay 僅開放實體店面與商品類商店申請，部分功能須審核開通。

## 2. 文件取得

文件下載頁 https://n.gomypay.asia/MDocuments_downloads.aspx 列出（2026-11-17 查核）：

| 類別 | 項目 | 版本／更新日 |
|---|---|---|
| 購物車模組 | WooCommerce V2（金流、物流、發票） | v1.7.0，2026-10-16 |
| 購物車模組 | WooCommerce V1 | v1.1.0，2025-07-29 |
| 購物車模組 | Magento2 | v1.0.0，2021-08-26 |
| 購物車模組 | OpenCart（3.0.3.7） | 2020-05-20 |
| 電子發票 API | 電子發票系統串接文件 API | v2.1，2026-08-17 |
| 行動支付手冊 | 台灣PAY、悠遊付、Apple Pay、Google Pay 操作手冊（整合版 2.1） | 2021-09-28 |
| 微信支付 API | 新光微信線上 API v1.1.11、線下 API v2.2.1 | 2019-11-26 |
| 其他 | 物流商家資料表、超商代碼繳費流程 | 2020-07-10、2019-02-18 |

- 下載頁的行動支付手冊是**消費者操作說明**，不含 API 欄位；各行動支付的串接技術文件需由商家後台取得。
- 信用卡、WebATM、虛擬帳號、超商條碼／代碼、定期扣款的 API 規格書**未公開**，需向 GoMyPay 申請。
- 電子發票 API 文件可直接下載，但每頁標示「本文件屬機密文件，未經授權禁止任意形式傳播」；GoMyPay 文件一律不收錄欄位細節。

## 3. 串接建議

- 需要 GoMyPay 時，先向其取得 API 規格書與測試帳號，再依規格實作。
- 只需要悠遊付／台灣PAY 收款、又不想走申請流程時，可改用 TWQR 或其他聚合商，見 [twqr-ewallet-landscape.md](twqr-ewallet-landscape.md)。

## 4. 來源

- 文件下載 — https://n.gomypay.asia/MDocuments_downloads.aspx
- 金流服務 — https://n.gomypay.asia/MCashFlow.aspx
- 費率與服務項目 — https://n.gomypay.asia/ServiceRateList.aspx
- 電子發票加值中心 — https://einvoice.gomypay.asia/
