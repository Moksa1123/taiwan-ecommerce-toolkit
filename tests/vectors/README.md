# 差分驗證標準答案（test vectors）

`scripts/verify-examples.py` 用這裡的 JSON 檢查 `taiwan-*/examples/*.py` 的加解密與簽章。
每個 JSON 的 `source` 欄位記錄出處，`generator` 記錄產生時的 PHP 與 OpenSSL 版本。

## 標準答案怎麼來的

**不是**拿我們自己的 Python 實作算出來再存檔（那樣只會驗證「程式碼沒變」，驗證不了「程式碼是對的」）。
而是把業者自己的程式原封不動丟進 `php:8.2-cli` 執行：

| 檔案 | 標準答案來源 |
|---|---|
| `payuni.json` | PAYUNi_for_WooCommerce 1.2.8（外掛標頭 Author: 統一金流 PAYUNi）`class-payuni.php` 的 `Encrypt` / `Decrypt` / `HashInfo`；另與 wpbr-payuni-payment 1.7.1、wpbr-payuni-shipping 1.6.4 人工比對一致 |
| `newebpay.json` | 藍新官方外掛 newebpay-payment 1.0.12 `encProcess.php`；規格書 NDNF-1.2.2 的 PHP 範例（加密、4.1.4 解密、4.1.5 CheckCode、4.1.6 CheckValue）與其附的真實伺服器密文；物流規格書 NDNS 1.0.0 附錄的 HashData 範例結果 |
| `ecpay.json` | 綠界官方 PHP SDK `ecpay/sdk`（MIT，由官方 WooCommerce 外掛內附）直接載入執行；SDK 本身另與綠界官方 ecpay-api-skill 的 test-vectors 交叉比對一致 |

`ecpay.json` 的 CheckMacValue 情境刻意涵蓋過去出錯的地方：`( ) ! * ~` 等 .NET URL encode 差異字元、
不分大小寫排序（`CVSStoreID` vs `CustomField1`）、物流用 MD5 而非 SHA256。

## 為什麼 PHP 程式碼不在 repo 裡

產生器（`_studies/harness/*.php`）內含逐字複製的外掛程式碼，那些外掛多為 GPL 授權，
綠界 ecpay-api-skill 則是 All Rights Reserved；因此產生器與原始碼都放在 gitignored 的 `_studies/`，
repo 只提交「以我們自訂輸入執行後的輸出結果」。

## 重新產生

需要 Docker 以及本機的參考原始碼（見 `_studies/INDEX.md`）：

```bash
cd _studies/harness
docker run --rm -v "$PWD:/w" php:8.2-cli php -d display_errors=stderr /w/payuni.php   > ../../tests/vectors/payuni.json
docker run --rm -v "$PWD:/w" php:8.2-cli php -d display_errors=stderr /w/newebpay.php > ../../tests/vectors/newebpay.json
docker run --rm -v "$PWD:/w" \
  -v "<reference>/ecpay-official/ecpay-ecommerce-for-woocommerce:/ref:ro" \
  -v "$PWD/../sources/ecpay-api-skill:/skill:ro" \
  php:8.2-cli php -d display_errors=stderr /w/ecpay.php > ../../tests/vectors/ecpay.json
```

產生器內建自我檢查（官方 roundtrip、與規格書範例結果比對、與綠界官方向量交叉比對），
任一不符會以非零狀態結束，不會寫出錯誤的標準答案。

## 已知且刻意容許的差異

- **URL encode 的 `~`**：PHP `urlencode` 編成 `%7E`，Python `quote_plus` 保留 `~`。
  PAYUNi / 藍新的 AES 內容伺服器會解碼，不影響結果；綠界 CheckMacValue 會直接影響雜湊，
  範例已改為與 PHP 一致。
- **藍新 padding**：官方外掛以 32 bytes 區塊補齊，規格書範例用標準 16 bytes PKCS#7，伺服器兩者皆接受；
  範例加密採規格書的 16 bytes，解密則兩種都必須能處理（padding 1–32）。
