# 加密實作與測試帳號

從 `taiwan-payment/CLAUDE.md` 移出的原文；規則摘要留在 CLAUDE.md。

## Encryption Methods

> 以下三段皆與業者官方實作逐位元組比對過（`tests/vectors/`，CI 執行 `scripts/verify-examples.py`）。
> 修改前請先跑該腳本；不要憑印象改演算法。

### ECPay - SHA256 CheckMacValue（物流用 MD5）

<!-- verify: ecpay-cmv-sha256 -->
```python
def ecpay_url_encode(text):
    # PHP urlencode → 小寫 → .NET 不編碼的 - _ . ! * ( ) 還原
    encoded = urllib.parse.quote_plus(text, safe='').replace('~', '%7E').lower()
    for src, dst in (('%2d', '-'), ('%5f', '_'), ('%2e', '.'), ('%21', '!'),
                     ('%2a', '*'), ('%28', '('), ('%29', ')')):
        encoded = encoded.replace(src, dst)
    return encoded

def generate_check_mac_value(params, hash_key, hash_iv):
    items = sorted(((k, v) for k, v in params.items() if k != 'CheckMacValue'),
                   key=lambda kv: kv[0].lower())          # 不分大小寫排序（SDK 用 strcasecmp）
    raw = f"HashKey={hash_key}&{'&'.join(f'{k}={v}' for k, v in items)}&HashIV={hash_iv}"
    return hashlib.sha256(ecpay_url_encode(raw).encode('utf-8')).hexdigest().upper()
```

### NewebPay - AES-256-CBC + SHA256

<!-- verify: newebpay -->
```python
def generate_trade_info(params, hash_key, hash_iv):
    cipher = AES.new(hash_key.encode(), AES.MODE_CBC, hash_iv.encode())
    return cipher.encrypt(pad(urllib.parse.urlencode(params).encode(), 16)).hex()

def decrypt_trade_info(trade_info, hash_key, hash_iv):
    data = AES.new(hash_key.encode(), AES.MODE_CBC, hash_iv.encode()).decrypt(bytes.fromhex(trade_info))
    # 官方外掛以 32 bytes 區塊補齊，padding 可能是 1–32；unpad(data, 16) 會失敗
    n = data[-1]
    if not 1 <= n <= 32 or data[-n:] != bytes([n]) * n:
        raise ValueError('padding 錯誤（金鑰或 IV 不正確）')
    text = data[:-n].decode()
    # RespondType=JSON 時明文是 JSON，不是 query string
    return json.loads(text) if text.startswith('{') else dict(urllib.parse.parse_qsl(text, keep_blank_values=True))

def generate_trade_sha(trade_info, hash_key, hash_iv):
    raw = f'HashKey={hash_key}&{trade_info}&HashIV={hash_iv}'
    return hashlib.sha256(raw.encode()).hexdigest().upper()
```

### PAYUNi - AES-256-GCM + SHA256

<!-- verify: payuni -->
```python
def generate_encrypt_info(params, hash_key, hash_iv):
    cipher = AES.new(hash_key.encode(), AES.MODE_GCM, nonce=hash_iv.encode())
    encrypted, tag = cipher.encrypt_and_digest(urllib.parse.urlencode(params).encode())
    # hex( base64(密文) + ":::" + base64(tag) ) —— 最外層的 hex 不可省略
    return (base64.b64encode(encrypted) + b':::' + base64.b64encode(tag)).hex()

def generate_hash_info(encrypt_info, hash_key, hash_iv):
    raw = hash_key + encrypt_info + hash_iv   # HashKey 在前
    return hashlib.sha256(raw.encode()).hexdigest().upper()
```

## Test Accounts

### ECPay
```
商店代號: 3002607
HashKey:  pwFHCqoQZGmho4w6
HashIV:   EkRm7iFT261dpevs
測試網址: https://payment-stage.ecpay.com.tw/Cashier/AioCheckOut/V5
測試卡號: 4311-9522-2222-2222
```

### NewebPay
```
商店代號: 請至後台申請
HashKey:  請至後台申請
HashIV:   請至後台申請
測試網址: https://ccore.newebpay.com/MPG/mpg_gateway
測試卡號: 4000-2211-1111-1111
```

### PAYUNi
```
商店代號: 請至後台申請
HashKey:  請至後台申請
HashIV:   請至後台申請
測試網址: https://sandbox-api.payuni.com.tw/api/upp
測試卡號: 4147631000000001（官方 page 374）
```
