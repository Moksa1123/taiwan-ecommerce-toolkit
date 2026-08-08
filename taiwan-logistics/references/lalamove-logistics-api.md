# Lalamove API v3 參考（即時／同城配送）

> Source: https://developers.lalamove.com/ (v3)
> 範例程式: https://github.com/lalamove/api-examples
> 台灣服務: https://www.lalamove.com/en-tw/business/api-solutions
> Captured: 2026-08-08 · doc_access: **public**

## 0. 為什麼要有這一類

本 skill 原本 7 家 provider 全是**批次型物流**：建立託運單 → 交寄 → 隔日到貨。Lalamove 屬於**即時／同城配送（on-demand delivery）**，模型完全不同：

| 面向 | 批次物流（ECPay/黑貓/超取） | 即時配送（Lalamove） |
|---|---|---|
| 下單前 | 直接建單 | **先報價（quotation），再用報價 ID 下單** |
| 報價效期 | 不適用 | **5 分鐘**內有效 |
| 司機 | 不可見 | 可查詢司機資訊、可更換司機 |
| 修改 | 建單後多半不可改 | 進行中可改一次收件點 |
| 取消 | 需走取消 API | `DELETE /orders/{id}` |
| 時效 | 隔日／指定日 | 數十分鐘 |
| 計價 | 固定運費表 | 動態，含加價（priority fee／小費） |

**適用情境**：餐飲外送、當日到貨、門市取貨後配送、B2B 急件、多點配送。
**不適用**：一般電商包裹（成本高很多）。

`data/logistics-types.csv` 已新增 `ondemand` 類型對應此模式。

## 1. 環境

| 環境 | Base URL |
|---|---|
| Sandbox | `https://rest.sandbox.lalamove.com/v3` |
| Production | `https://rest.lalamove.com/v3` |

## 2. 認證與簽章

HMAC-SHA256。每個請求需三個 header：

| Header | 值 |
|---|---|
| `Authorization` | `hmac <KEY>:<TIMESTAMP>:<SIGNATURE>` |
| `Market` | UN/LOCODE 市場代碼（台灣為 `TW`） |
| `Request-ID` | Nonce（每次請求唯一） |

### 簽章字串

```
HmacSHA256(<TIMESTAMP>\r\n<METHOD>\r\n<PATH>\r\n\r\n<BODY>, <SECRET>)
```

⚠️ 注意是 `\r\n`（CRLF）不是 `\n`，且 PATH 與 BODY 之間是**兩個** CRLF（空行）。這是最常見的簽章對不上原因。

```python
import hmac, hashlib, time, json, uuid

def build_headers(method, path, body_dict, key, secret, market="TW"):
    ts = str(int(time.time() * 1000))
    body = json.dumps(body_dict, separators=(',', ':')) if body_dict else ""
    raw = f"{ts}\r\n{method}\r\n{path}\r\n\r\n{body}"
    sig = hmac.new(secret.encode(), raw.encode(), hashlib.sha256).hexdigest()
    return {
        "Authorization": f"hmac {key}:{ts}:{sig}",
        "Market": market,
        "Request-ID": str(uuid.uuid4()),
        "Content-Type": "application/json",
    }
```

> 簽章用的 `body` 必須與實際送出的 body **逐字元相同**。用 `json.dumps` 產生一次，同時拿去簽章與送出，不要分別序列化兩次。

## 3. 端點總覽

| 端點 | Method | 用途 |
|---|---|---|
| `/v3/quotations` | POST | 取得報價（含價格明細） |
| `/v3/quotations/{id}` | GET | 查詢報價 |
| `/v3/orders` | POST | 用 quotation ID 建立訂單 |
| `/v3/orders/{id}` | GET | 查詢訂單狀態 |
| `/v3/orders/{id}` | PATCH | 修改收件點（**僅限一次**） |
| `/v3/orders/{id}` | DELETE | 取消訂單 |
| `/v3/orders/{id}/drivers/{driverId}` | GET | 查詢司機資訊 |
| `/v3/orders/{id}/drivers/{driverId}` | DELETE | 更換司機（**媒合後 15 分鐘以上**才可） |
| `/v3/orders/{id}/priority-fee` | POST | 追加小費／優先費 |
| `/v3/cities` | GET | 取得市場與服務設定 |
| `/v3/webhook` | PATCH | 設定 webhook URL |

## 4. 標準流程

```
1. GET  /v3/cities                → 取得台灣可用的車型 serviceType、特殊需求 specialRequests
2. POST /v3/quotations            → 傳入取送點，取得 quotationId + 價格明細（5 分鐘有效）
3. POST /v3/orders                → 帶 quotationId 下單
4. webhook / GET /v3/orders/{id}  → 追蹤狀態、取得司機
5. (選) POST …/priority-fee       → 沒司機接單時加價
6. (選) PATCH /v3/orders/{id}     → ON_GOING 期間改一次收件點
7. (選) DELETE /v3/orders/{id}    → 取消
```

> **報價 5 分鐘效期是硬約束。** 若你的結帳流程是「顯示運費 → 使用者慢慢填地址 → 送出」，很容易超時。建議在最終送出前重新報價，或把報價時間戳存起來做過期判斷。

## 5. 重要選項

| 欄位 | 說明 |
|---|---|
| `isRouteOptimized` | `true` 啟用多點路線最佳化 |
| `isPODEnabled` | `true` 啟用 Proof of Delivery（送達證明） |
| `metadata` | 自訂 key-value，可掛你自己的訂單編號 |

`metadata` 是把 Lalamove 訂單對回自家系統的建議做法——不要依賴 Lalamove 的 order ID 當主鍵。

## 6. 市場

v3 支援 14 個市場，**含台灣**：香港、新加坡、泰國、越南、印尼、馬來西亞、菲律賓、巴西、墨西哥、日本、**台灣**、阿聯、沙烏地阿拉伯等。

`Market` header 必須正確，否則報價會落在錯誤的城市。實際可用的 `serviceType`（機車／小貨車／貨van…）與費率請以 `GET /v3/cities` 回傳為準，不要寫死。

## 7. 與本 skill 其他 provider 的搭配

實務上電商常見組合：

| 情境 | 建議 |
|---|---|
| 一般電商包裹 | ECPay / ezShip / SmilePay 等聚合商（超取 or 宅配） |
| 當日／急件 | Lalamove |
| 兩者並存 | 依訂單金額／距離／時效在結帳頁分流；退貨一律走批次物流（Lalamove 逆物流成本不划算） |

## 8. 待驗證

- 台灣市場實際可用的 `serviceType` 清單與費率結構（需以 `GET /v3/cities` 實測）
- Webhook 事件型別與 payload 結構
- 台灣是否需另行申請商業帳號才能取得 production key
- pandago（foodpanda）、Uber Direct 在台灣的商家 API 與文件公開程度——本次未確認，若可用應併入 `ondemand` 類型

## 9. 來源

- API Reference — https://developers.lalamove.com/
- v3 Index — https://developers.lalamove.com/v2/index.html
- 官方範例（多語言） — https://github.com/lalamove/api-examples
- 台灣 API 方案 — https://www.lalamove.com/en-tw/business/api-solutions
