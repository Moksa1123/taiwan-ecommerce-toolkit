# 即時／同城配送（On-demand Delivery）在台灣

> Captured: 2026-08-08
> 涵蓋: Lalamove、pandago（foodpanda）、Uber Direct
> Lalamove 詳細規格見 [lalamove-logistics-api.md](lalamove-logistics-api.md)

## 0. 這個分類跟其他物流不同在哪

本 skill 收錄的其他物流（超取、宅配）都是**批次型**：建單 → 出貨 → 數日後送達，以「單」為單位。即時配送是**派遣型**：報價 → 立即派車 → 數十分鐘內送達，以「趟」為單位。

差異直接影響串接設計：

| 面向 | 批次物流（超取／宅配）| 即時配送 |
|---|---|---|
| 報價 | 費率表固定，可預先算 | **必須先呼叫 API 取得即時報價**，且報價有效期短 |
| 建單時機 | 出貨當下 | 消費者下單當下或稍後派遣 |
| 取消 | 出貨前可取消 | **司機接單後取消多半要付費** |
| 追蹤 | 貨態代碼（數小時～數日更新）| **司機即時座標** |
| 失敗處理 | 退回寄件人 | 需重新派遣或人工介入 |
| 服務範圍 | 全台 | **限同城／特定半徑** |

> ⚠️ 把即時配送套用批次物流的資料模型（先建單再出貨）會不合用——報價會過期、司機座標無處可放。

## 1. 三家對照

| | Lalamove | pandago | Uber Direct |
|---|---|---|---|
| 母公司 | Lalamove | Delivery Hero（foodpanda）| Uber |
| 台灣可用 | ✅ 官方文件列台灣 | ✅ **官方 API 文件列 `tw`** | ⚠️ 見 §4 |
| 文件公開 | ✅ 免登入 | ✅ 免登入（Delivery Hero ODR）| ✅ 免登入 |
| 認證 | HMAC-SHA256 自簽 | **OAuth 2.0 + RSA 簽的 JWT assertion** | OAuth 2.0 client_credentials |
| 取得憑證 | 開發者後台 | **須洽 account manager 申請** | 商家後台 |
| 報價 | 先報價後下單，效期 5 分鐘 | `POST /orders/fee` 與 `/orders/time` 分開 | quote 端點 |
| 司機座標 | ✅ | ✅ `GET /orders/{id}/coordinates` | ✅ |
| 尺寸限制 | 依車型 | **34×34×36 cm、20 kg**（foodpanda 外送箱）| 依方案 |

## 2. pandago（foodpanda）

pandago 屬 Delivery Hero 的 **On Demand Rider（ODR）API**，同一套 API 也服務 Glovo、Talabat 等品牌。

### 環境

| 環境 | Base URL |
|---|---|
| 台灣正式 | **`https://pandago-api-apse.deliveryhero.io/tw`** |
| Sandbox | `https://pandago-api-sandbox.deliveryhero.io/sg` |

> ⚠️ **Sandbox 只有 `sg`（新加坡）**，沒有台灣沙箱。測試時的地址、費率、涵蓋範圍都是新加坡的，**不能用來驗證台灣的服務範圍或計價**。

### 認證

OAuth 2.0，但不是常見的 client_secret 模式：

```
1. 產生 RSA 金鑰對
2. 以私鑰簽出 JWT assertion
3. POST /oauth2/token
   grant_type            = client_credentials
   client_assertion_type = urn:ietf:params:oauth:client-assertion-type:jwt-bearer
   client_assertion      = <簽好的 JWT>
```

需向 pandago account manager 索取 **Client ID、Key ID、Scope**；私鑰自行產生。

> ⚠️ 這是 14 家 provider 中**唯一使用 JWT assertion（private_key_jwt）**的。既有的 HMAC 或 API Key 程式碼完全不能沿用。

### 端點

| 操作 | Method | 路徑 |
|---|---|---|
| 建立訂單 | POST | `/orders` |
| 查詢訂單 | GET | `/orders/{order_id}` |
| 取消訂單 | DELETE | `/orders/{order_id}` |
| 費用估算 | POST | `/orders/fee` |
| 時間估算 | POST | `/orders/time` |
| 司機座標 | GET | `/orders/{order_id}/coordinates` |

> 費用與時間是**兩支獨立端點**，跟 Lalamove 一次回傳報價＋預計時間不同。要同時顯示兩者需呼叫兩次。

### 服務限制

- 包裹須放得進 foodpanda 外送箱：**34 × 34 × 36 cm**
- **上限 20 公斤**
- 零售商家**不需成為 foodpanda 餐廳夥伴**即可使用，可直接填單叫車

## 3. Uber Direct

### 認證

| 項目 | 值 |
|---|---|
| Token 端點 | `https://auth.uber.com/oauth/v2/token` |
| grant_type | `client_credentials` |
| scope | **`eats.deliveries`** |
| API Base | `https://api.uber.com/` |

Token 請求用 `application/x-www-form-urlencoded`；後續 API 呼叫用 `application/json`，以 Bearer token 帶入 Authorization header。

> 💡 **Token 有效期 30 天（2,592,000 秒）**，官方明文建議快取而非每次重新產生。這與 Lalamove（每次請求都簽章）、pandago（JWT assertion）的模式都不同——Uber Direct 這邊反而要注意**別把 token 當短期憑證反覆申請**。

### API 家族

Direct API、Organizations API、Courier Pick & Pack API、Refund API、Business Location Management API。

### 服務範圍

官方行銷頁只說「available in 2 dozen countries」，未逐一列出。配送半徑約 **10 英里**內，時效可選 2 小時內／當日／最多預約 30 天後。

## 4. ⚠️ Uber Direct 的台灣可用性：有間接證據，無官方確認

**支持的證據：**
- 存在台灣在地化的商家頁 `merchants.ubereats.com/tw/zh-tw/`
- Uber Help 有中文的「Uber Direct 控制台」章節
- 台灣的系統整合商（如 weiby.tw）公開販售「Uber Eats／Uber Direct／foodpanda／pandago」的 API 串接服務

**缺乏的證據：**
- Uber 官方**沒有**逐一列出支援國家的清單，台灣未被點名
- 開發者文件未標示市場代碼或區域端點

**結論**：可用性高度可能，但**本 skill 不將其標為已確認**。與 pandago 不同——pandago 的官方 API 文件直接列出 `tw` 的正式端點，那是明確的一手證據。

實務建議：導入前先向 Uber 業務確認貴公司所在區域是否在服務範圍內，不要依賴行銷頁的在地化路徑判斷。

## 5. 選型

| 情境 | 建議 |
|---|---|
| 需要明確的台灣官方端點與文件 | **pandago**（`/tw` 正式端點有官方文件背書）|
| 已有 HMAC 簽章經驗、想快速上線 | **Lalamove**（自簽 HMAC，開發者後台自助取得憑證）|
| 需要多車型／路線最佳化／換司機 | **Lalamove** |
| 小件、標準箱體、不需成為餐飲夥伴 | **pandago**（34×34×36 cm / 20 kg 內）|
| 已在用 Uber Eats 生態 | **Uber Direct**（但先確認台灣服務範圍）|

> 三家都**不是批次物流的替代品**。單日出貨量大、跨縣市、需要超取或貨到付款的情境，仍應走 ECPay／ezShip 等聚合商。即時配送適合的是同城、急件、生鮮這類批次物流做不到的需求。

## 6. 待補

| 項目 | 說明 |
|---|---|
| pandago `/orders` 逐欄 | 端點與認證已確認，request/response 欄位待擷取 |
| Uber Direct 端點逐欄 | 認證已確認；API reference 為 SPA，需以瀏覽器取得 |
| 三家的取消政策與費用 | 即時配送的取消多半收費，各家規則未確認 |

## 7. 來源

- Delivery Hero On Demand Rider API — https://on-demand-rider-docs.deliveryhero.io/
- pandago 台灣 — https://pandago.tw/
- foodpanda pandago 介紹 — https://www.foodpanda.com.tw/contents/pandago
- Uber Direct API 總覽 — https://developer.uber.com/docs/deliveries/overview
- Uber Direct 認證 — https://developer.uber.com/docs/deliveries/guides/authentication
- Uber Direct 商家頁（台灣在地化）— https://merchants.ubereats.com/tw/zh-tw/
- Lalamove — [lalamove-logistics-api.md](lalamove-logistics-api.md)
