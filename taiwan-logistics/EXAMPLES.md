# Taiwan Logistics Code Examples

**Production-ready code examples for Taiwan Logistics integration**

Supporting NewebPay Logistics, ECPay Logistics, and PAYUNi Logistics with comprehensive TypeScript, Python, and PHP implementations.

---

## Table of Contents

1. [NewebPay Logistics Examples](#newebpay-logistics-examples)
   - [Basic Integration](#1-basic-integration-newebpay)
   - [Store Map Query](#2-store-map-query)
   - [Create Shipment](#3-create-shipment)
   - [Get Shipment Number](#4-get-shipment-number)
   - [Print Label](#5-print-label)
   - [Query Shipment](#6-query-shipment)
   - [Modify Shipment](#7-modify-shipment)
   - [Track Shipment](#8-track-shipment)
   - [Status Notification](#9-status-notification-callback)

2. [ECPay Logistics Examples](#ecpay-logistics-examples)
3. [Real-World Scenarios](#real-world-scenarios)
4. [Error Handling](#error-handling)

---

## NewebPay Logistics Examples

### 1. Basic Integration (NewebPay)

#### TypeScript - Encryption Helper

```typescript
import crypto from 'crypto';

interface NewebPayConfig {
  merchantId: string;
  hashKey: string;
  hashIV: string;
  isProduction?: boolean;
}

class NewebPayLogistics {
  private config: Required<NewebPayConfig>;
  private baseUrl: string;

  constructor(config: NewebPayConfig) {
    this.config = {
      ...config,
      isProduction: config.isProduction ?? false,
    };

    this.baseUrl = this.config.isProduction
      ? 'https://core.newebpay.com/API/Logistic'
      : 'https://ccore.newebpay.com/API/Logistic';
  }

  /**
   * AES-256-CBC Encryption
   */
  private aesEncrypt(data: string): string {
    const cipher = crypto.createCipheriv(
      'aes-256-cbc',
      this.config.hashKey,
      this.config.hashIV
    );

    let encrypted = cipher.update(data, 'utf8', 'hex');
    encrypted += cipher.final('hex');

    return encrypted;
  }

  /**
   * AES-256-CBC Decryption
   */
  private aesDecrypt(encryptedData: string): string {
    const decipher = crypto.createDecipheriv(
      'aes-256-cbc',
      this.config.hashKey,
      this.config.hashIV
    );

    let decrypted = decipher.update(encryptedData, 'hex', 'utf8');
    decrypted += decipher.final('utf8');

    return decrypted;
  }

  /**
   * Generate Hash Data (SHA256)
   */
  private generateHashData(encryptData: string): string {
    const raw = `${this.config.hashKey}${encryptData}${this.config.hashIV}`;
    return crypto.createHash('sha256').update(raw).digest('hex').toUpperCase();
  }

  /**
   * Encrypt request data
   */
  encryptData(data: Record<string, any>): { EncryptData_: string; HashData_: string } {
    const jsonStr = JSON.stringify(data);
    const encryptData = this.aesEncrypt(jsonStr);
    const hashData = this.generateHashData(encryptData);

    return {
      EncryptData_: encryptData,
      HashData_: hashData,
    };
  }

  /**
   * Decrypt response data
   */
  decryptData(encryptData: string, hashData: string): any {
    // Verify hash
    const calculatedHash = this.generateHashData(encryptData);
    if (calculatedHash !== hashData.toUpperCase()) {
      throw new Error('Hash verification failed');
    }

    const decrypted = this.aesDecrypt(encryptData);
    return JSON.parse(decrypted);
  }

  /**
   * Get current Unix timestamp
   */
  getTimestamp(): string {
    return Math.floor(Date.now() / 1000).toString();
  }
}

export { NewebPayLogistics };
```

#### Python - Encryption Helper

```python
"""NewebPay Logistics Encryption Helper - Python"""

import json
import hashlib
import time
from typing import Dict, Any, Tuple
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


class NewebPayLogistics:
    """NewebPay Logistics API Client"""

    def __init__(
        self,
        merchant_id: str,
        hash_key: str,
        hash_iv: str,
        is_production: bool = False
    ):
        self.merchant_id = merchant_id
        self.hash_key = hash_key.encode('utf-8')
        self.hash_iv = hash_iv.encode('utf-8')

        self.base_url = (
            'https://core.newebpay.com/API/Logistic'
            if is_production
            else 'https://ccore.newebpay.com/API/Logistic'
        )

    def aes_encrypt(self, data: str) -> str:
        """AES-256-CBC Encryption"""
        cipher = AES.new(self.hash_key, AES.MODE_CBC, self.hash_iv)
        padded_data = pad(data.encode('utf-8'), AES.block_size)
        encrypted = cipher.encrypt(padded_data)
        return encrypted.hex()

    def aes_decrypt(self, encrypted_data: str) -> str:
        """AES-256-CBC Decryption"""
        cipher = AES.new(self.hash_key, AES.MODE_CBC, self.hash_iv)
        decrypted = cipher.decrypt(bytes.fromhex(encrypted_data))
        unpadded = unpad(decrypted, AES.block_size)
        return unpadded.decode('utf-8')

    def generate_hash_data(self, encrypt_data: str) -> str:
        """Generate Hash Data (SHA256)"""
        raw = f"{self.hash_key.decode('utf-8')}{encrypt_data}{self.hash_iv.decode('utf-8')}"
        return hashlib.sha256(raw.encode('utf-8')).hexdigest().upper()

    def encrypt_data(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Encrypt request data"""
        json_str = json.dumps(data, ensure_ascii=False)
        encrypt_data = self.aes_encrypt(json_str)
        hash_data = self.generate_hash_data(encrypt_data)

        return {
            'EncryptData_': encrypt_data,
            'HashData_': hash_data,
        }

    def decrypt_data(self, encrypt_data: str, hash_data: str) -> Dict[str, Any]:
        """Decrypt response data"""
        # Verify hash
        calculated_hash = self.generate_hash_data(encrypt_data)
        if calculated_hash != hash_data.upper():
            raise ValueError('Hash verification failed')

        decrypted = self.aes_decrypt(encrypt_data)
        return json.loads(decrypted)

    @staticmethod
    def get_timestamp() -> str:
        """Get current Unix timestamp"""
        return str(int(time.time()))
```

---

### 2. Store Map Query

Query convenience store locations for pickup or sender.

#### TypeScript Example

```typescript
import axios from 'axios';

interface StoreMapRequest {
  merchantOrderNo: string;
  lgsType: 'B2C' | 'C2C';
  shipType: '1' | '2' | '3' | '4'; // 1=7-11, 2=FamilyMart, 3=Hi-Life, 4=OK Mart
  returnURL: string;
  extraData?: string;
}

class NewebPayStoreMap extends NewebPayLogistics {
  /**
   * Query store map
   */
  async queryStoreMap(params: StoreMapRequest): Promise<string> {
    const data = {
      MerchantOrderNo: params.merchantOrderNo,
      LgsType: params.lgsType,
      ShipType: params.shipType,
      ReturnURL: params.returnURL,
      TimeStamp: this.getTimestamp(),
      ExtraData: params.extraData || '',
    };

    const { EncryptData_, HashData_ } = this.encryptData(data);

    const requestData = {
      UID_: this.config.merchantId,
      EncryptData_,
      HashData_,
      Version_: '1.0',
      RespondType_: 'JSON',
    };

    const response = await axios.post(
      `${this.baseUrl}/storeMap`,
      new URLSearchParams(requestData as any),
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      }
    );

    // NewebPay will redirect to store selection page
    // Return the redirect URL or HTML
    return response.data;
  }

  /**
   * Handle store map callback
   */
  handleStoreMapCallback(
    encryptData: string,
    hashData: string
  ): {
    lgsType: string;
    shipType: string;
    merchantOrderNo: string;
    storeName: string;
    storeTel: string;
    storeAddr: string;
    storeID: string;
    extraData: string;
  } {
    const decrypted = this.decryptData(encryptData, hashData);

    return {
      lgsType: decrypted.LgsType,
      shipType: decrypted.ShipType,
      merchantOrderNo: decrypted.MerchantOrderNo,
      storeName: decrypted.StoreName,
      storeTel: decrypted.StoreTel,
      storeAddr: decrypted.StoreAddr,
      storeID: decrypted.StoreID,
      extraData: decrypted.ExtraData,
    };
  }
}

// Usage Example
const logistics = new NewebPayStoreMap({
  merchantId: 'YOUR_MERCHANT_ID',
  hashKey: 'YOUR_HASH_KEY',
  hashIV: 'YOUR_HASH_IV',
  isProduction: false,
});

// Open store map
await logistics.queryStoreMap({
  merchantOrderNo: `ORD${Date.now()}`,
  lgsType: 'C2C',
  shipType: '1', // 7-ELEVEN
  returnURL: 'https://your-site.com/callback/store-map',
  extraData: 'order_id=123',
});

export { NewebPayStoreMap };
```

#### Python Example

```python
"""Store Map Query - Python Example"""

import requests
from typing import Dict, Optional


class NewebPayStoreMap(NewebPayLogistics):
    """Store Map Query Operations"""

    def query_store_map(
        self,
        merchant_order_no: str,
        lgs_type: str,  # 'B2C' or 'C2C'
        ship_type: str,  # '1'=7-11, '2'=FamilyMart, '3'=Hi-Life, '4'=OK Mart
        return_url: str,
        extra_data: str = '',
    ) -> str:
        """Query store map"""

        data = {
            'MerchantOrderNo': merchant_order_no,
            'LgsType': lgs_type,
            'ShipType': ship_type,
            'ReturnURL': return_url,
            'TimeStamp': self.get_timestamp(),
            'ExtraData': extra_data,
        }

        encrypted = self.encrypt_data(data)

        request_data = {
            'UID_': self.merchant_id,
            'EncryptData_': encrypted['EncryptData_'],
            'HashData_': encrypted['HashData_'],
            'Version_': '1.0',
            'RespondType_': 'JSON',
        }

        response = requests.post(
            f'{self.base_url}/storeMap',
            data=request_data,
        )

        return response.text

    def handle_store_map_callback(
        self,
        encrypt_data: str,
        hash_data: str,
    ) -> Dict[str, str]:
        """Handle store map callback"""

        decrypted = self.decrypt_data(encrypt_data, hash_data)

        return {
            'lgs_type': decrypted['LgsType'],
            'ship_type': decrypted['ShipType'],
            'merchant_order_no': decrypted['MerchantOrderNo'],
            'store_name': decrypted['StoreName'],
            'store_tel': decrypted['StoreTel'],
            'store_addr': decrypted['StoreAddr'],
            'store_id': decrypted['StoreID'],
            'extra_data': decrypted.get('ExtraData', ''),
        }


# Usage Example
logistics = NewebPayStoreMap(
    merchant_id='YOUR_MERCHANT_ID',
    hash_key='YOUR_HASH_KEY',
    hash_iv='YOUR_HASH_IV',
    is_production=False,
)

# Open store map
html = logistics.query_store_map(
    merchant_order_no=f'ORD{int(time.time())}',
    lgs_type='C2C',
    ship_type='1',  # 7-ELEVEN
    return_url='https://your-site.com/callback/store-map',
    extra_data='order_id=123',
)
```

---

### 3. Create Shipment

Create logistics shipment order.

#### TypeScript Example

```typescript
interface CreateShipmentRequest {
  merchantOrderNo: string;
  tradeType: 1 | 3; // 1=COD, 3=No Payment
  userName: string;
  userTel: string;
  userEmail: string;
  storeID: string;
  amt: number;
  itemDesc?: string;
  notifyURL?: string;
  lgsType: 'B2C' | 'C2C';
  shipType: '1' | '2' | '3' | '4';
}

class NewebPayShipment extends NewebPayLogistics {
  /**
   * Create shipment order
   */
  async createShipment(params: CreateShipmentRequest) {
    const data = {
      MerchantOrderNo: params.merchantOrderNo,
      TradeType: params.tradeType,
      UserName: params.userName,
      UserTel: params.userTel,
      UserEmail: params.userEmail,
      StoreID: params.storeID,
      Amt: params.amt,
      NotifyURL: params.notifyURL || '',
      ItemDesc: params.itemDesc || '',
      LgsType: params.lgsType,
      ShipType: params.shipType,
      TimeStamp: this.getTimestamp(),
    };

    const { EncryptData_, HashData_ } = this.encryptData(data);

    const requestData = {
      UID_: this.config.merchantId,
      EncryptData_,
      HashData_,
      Version_: '1.0',
      RespondType_: 'JSON',
    };

    const response = await axios.post(
      `${this.baseUrl}/createShipment`,
      new URLSearchParams(requestData as any),
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      }
    );

    const result = response.data;

    if (result.Status !== 'SUCCESS') {
      throw new Error(`Create shipment failed: ${result.Message}`);
    }

    // Decrypt response
    const decrypted = this.decryptData(result.EncryptData, result.HashData);

    return {
      merchantID: decrypted.MerchantID,
      amt: decrypted.Amt,
      merchantOrderNo: decrypted.MerchantOrderNo,
      tradeNo: decrypted.TradeNo,
      lgsType: decrypted.LgsType,
      shipType: decrypted.ShipType,
      storeID: decrypted.StoreID,
      tradeType: decrypted.TradeType,
    };
  }
}

// Usage Example
const shipment = new NewebPayShipment({
  merchantId: 'YOUR_MERCHANT_ID',
  hashKey: 'YOUR_HASH_KEY',
  hashIV: 'YOUR_HASH_IV',
});

const result = await shipment.createShipment({
  merchantOrderNo: `ORD${Date.now()}`,
  tradeType: 1, // Cash on Delivery
  userName: 'John Doe',
  userTel: '0912345678',
  userEmail: 'john@example.com',
  storeID: '123456', // From store map query
  amt: 1500,
  itemDesc: 'T-shirt x 2',
  notifyURL: 'https://your-site.com/callback/shipment',
  lgsType: 'C2C',
  shipType: '1', // 7-ELEVEN
});

console.log('Trade No:', result.tradeNo);

export { NewebPayShipment };
```

#### Python Example

```python
"""Create Shipment - Python Example"""

from typing import Dict, Optional


class NewebPayShipment(NewebPayLogistics):
    """Shipment Creation Operations"""

    def create_shipment(
        self,
        merchant_order_no: str,
        trade_type: int,  # 1=COD, 3=No Payment
        user_name: str,
        user_tel: str,
        user_email: str,
        store_id: str,
        amt: int,
        lgs_type: str,  # 'B2C' or 'C2C'
        ship_type: str,  # '1'=7-11, '2'=FamilyMart, '3'=Hi-Life, '4'=OK Mart
        item_desc: str = '',
        notify_url: str = '',
    ) -> Dict[str, any]:
        """Create shipment order"""

        data = {
            'MerchantOrderNo': merchant_order_no,
            'TradeType': trade_type,
            'UserName': user_name,
            'UserTel': user_tel,
            'UserEmail': user_email,
            'StoreID': store_id,
            'Amt': amt,
            'NotifyURL': notify_url,
            'ItemDesc': item_desc,
            'LgsType': lgs_type,
            'ShipType': ship_type,
            'TimeStamp': self.get_timestamp(),
        }

        encrypted = self.encrypt_data(data)

        request_data = {
            'UID_': self.merchant_id,
            'EncryptData_': encrypted['EncryptData_'],
            'HashData_': encrypted['HashData_'],
            'Version_': '1.0',
            'RespondType_': 'JSON',
        }

        response = requests.post(
            f'{self.base_url}/createShipment',
            data=request_data,
        )

        result = response.json()

        if result['Status'] != 'SUCCESS':
            raise Exception(f"Create shipment failed: {result['Message']}")

        # Decrypt response
        decrypted = self.decrypt_data(result['EncryptData'], result['HashData'])

        return {
            'merchant_id': decrypted['MerchantID'],
            'amt': decrypted['Amt'],
            'merchant_order_no': decrypted['MerchantOrderNo'],
            'trade_no': decrypted['TradeNo'],
            'lgs_type': decrypted['LgsType'],
            'ship_type': decrypted['ShipType'],
            'store_id': decrypted['StoreID'],
            'trade_type': decrypted['TradeType'],
        }


# Usage Example
shipment = NewebPayShipment(
    merchant_id='YOUR_MERCHANT_ID',
    hash_key='YOUR_HASH_KEY',
    hash_iv='YOUR_HASH_IV',
)

result = shipment.create_shipment(
    merchant_order_no=f'ORD{int(time.time())}',
    trade_type=1,  # Cash on Delivery
    user_name='John Doe',
    user_tel='0912345678',
    user_email='john@example.com',
    store_id='123456',  # From store map query
    amt=1500,
    item_desc='T-shirt x 2',
    notify_url='https://your-site.com/callback/shipment',
    lgs_type='C2C',
    ship_type='1',  # 7-ELEVEN
)

print(f"Trade No: {result['trade_no']}")
```

---

### 4. Get Shipment Number

Get shipping code for Kiosk printing.

#### TypeScript Example

```typescript
class NewebPayShipmentNumber extends NewebPayLogistics {
  /**
   * Get shipment numbers (max 10 orders)
   */
  async getShipmentNumbers(merchantOrderNos: string[]) {
    if (merchantOrderNos.length > 10) {
      throw new Error('Maximum 10 orders per request');
    }

    const data = {
      MerchantOrderNo: merchantOrderNos,
      TimeStamp: this.getTimestamp(),
    };

    const { EncryptData_, HashData_ } = this.encryptData(data);

    const requestData = {
      UID_: this.config.merchantId,
      EncryptData_,
      HashData_,
      Version_: '1.0',
      RespondType_: 'JSON',
    };

    const response = await axios.post(
      `${this.baseUrl}/getShipmentNo`,
      new URLSearchParams(requestData as any),
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      }
    );

    const result = response.data;

    if (result.Status !== 'SUCCESS') {
      throw new Error(`Get shipment number failed: ${result.Message}`);
    }

    // Decrypt response
    const decrypted = this.decryptData(result.EncryptData, result.HashData);

    return {
      success: decrypted.SUCCESS || [],
      error: decrypted.ERROR || [],
    };
  }
}

// Usage Example
const shipmentNum = new NewebPayShipmentNumber({
  merchantId: 'YOUR_MERCHANT_ID',
  hashKey: 'YOUR_HASH_KEY',
  hashIV: 'YOUR_HASH_IV',
});

const result = await shipmentNum.getShipmentNumbers([
  'ORD001',
  'ORD002',
  'ORD003',
]);

result.success.forEach((item: any) => {
  console.log(`Order ${item.MerchantOrderNo}:`);
  console.log(`  Shipment No: ${item.LgsNo}`);
  console.log(`  Store Print No: ${item.StorePrintNo}`);
});

result.error.forEach((item: any) => {
  console.error(`Order ${item.MerchantOrderNo}: ${item.ErrorCode}`);
});

export { NewebPayShipmentNumber };
```

---

### 5. Print Label

Print shipping labels (Form POST method).

#### TypeScript Example

```typescript
class NewebPayPrintLabel extends NewebPayLogistics {
  /**
   * Generate print label HTML form
   */
  generatePrintLabelForm(params: {
    merchantOrderNos: string[];
    lgsType: 'B2C' | 'C2C';
    shipType: '1' | '2' | '3' | '4';
  }): string {
    // Validate batch limits
    const limits: Record<string, number> = {
      '1': 18, // 7-ELEVEN
      '2': 8,  // FamilyMart
      '3': 18, // Hi-Life
      '4': 18, // OK Mart
    };

    if (params.merchantOrderNos.length > limits[params.shipType]) {
      throw new Error(`Maximum ${limits[params.shipType]} labels for this provider`);
    }

    const data = {
      LgsType: params.lgsType,
      ShipType: params.shipType,
      MerchantOrderNo: params.merchantOrderNos,
      TimeStamp: this.getTimestamp(),
    };

    const { EncryptData_, HashData_ } = this.encryptData(data);

    const formData = {
      UID_: this.config.merchantId,
      EncryptData_,
      HashData_,
      Version_: '1.0',
      RespondType_: 'JSON',
    };

    // Generate HTML form for auto-submit
    const inputs = Object.entries(formData)
      .map(([key, value]) => `<input type="hidden" name="${key}" value="${value}">`)
      .join('\n');

    return `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Print Shipping Label</title>
</head>
<body onload="document.getElementById('printForm').submit();">
  <form id="printForm" method="post" action="${this.baseUrl}/printLabel">
    ${inputs}
  </form>
  <p>Redirecting to print page...</p>
</body>
</html>
    `;
  }
}

// Usage Example
const printLabel = new NewebPayPrintLabel({
  merchantId: 'YOUR_MERCHANT_ID',
  hashKey: 'YOUR_HASH_KEY',
  hashIV: 'YOUR_HASH_IV',
});

const html = printLabel.generatePrintLabelForm({
  merchantOrderNos: ['ORD001', 'ORD002'],
  lgsType: 'C2C',
  shipType: '1', // 7-ELEVEN (max 18 labels)
});

// Send HTML to browser or save to file
export { NewebPayPrintLabel };
```

---

### 6. Query Shipment

Query logistics order status.

#### TypeScript Example

```typescript
class NewebPayQueryShipment extends NewebPayLogistics {
  /**
   * Query shipment status
   */
  async queryShipment(merchantOrderNo: string) {
    const data = {
      MerchantOrderNo: merchantOrderNo,
      TimeStamp: this.getTimestamp(),
    };

    const { EncryptData_, HashData_ } = this.encryptData(data);

    const requestData = {
      UID_: this.config.merchantId,
      EncryptData_,
      HashData_,
      Version_: '1.0',
      RespondType_: 'JSON',
    };

    const response = await axios.post(
      `${this.baseUrl}/queryShipment`,
      new URLSearchParams(requestData as any),
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      }
    );

    const result = response.data;

    if (result.Status !== 'SUCCESS') {
      throw new Error(`Query shipment failed: ${result.Message}`);
    }

    // Decrypt response
    const decrypted = this.decryptData(result.EncryptData, result.HashData);

    return {
      merchantID: decrypted.MerchantID,
      lgsType: decrypted.LgsType,
      tradeNo: decrypted.TradeNo,
      merchantOrderNo: decrypted.MerchantOrderNo,
      amt: decrypted.Amt,
      itemDesc: decrypted.ItemDesc,
      lgsNo: decrypted.LgsNo,
      storePrintNo: decrypted.StorePrintNo,
      collectionAmt: decrypted.collectionAmt,
      tradeType: decrypted.TradeType,
      type: decrypted.Type,
      shopDate: decrypted.ShopDate,
      userName: decrypted.UserName,
      userTel: decrypted.UserTel,
      userEmail: decrypted.UserEmail,
      storeID: decrypted.StoreID,
      shipType: decrypted.ShipType,
      storeName: decrypted.StoreName,
      retId: decrypted.Retld,
      retString: decrypted.RetString,
    };
  }

  /**
   * Get human-readable status
   */
  getStatusDescription(retId: string): string {
    const statusMap: Record<string, string> = {
      '0_1': 'Order not processed',
      '0_2': 'Shipment number expired',
      '0_3': 'Shipment canceled',
      '1': 'Order processing',
      '2': 'Store received shipment',
      '3': 'Store reselected',
      '4': 'Arrived at logistics center',
      '5': 'Arrived at pickup store',
      '6': 'Customer picked up',
      '-1': 'Returned to merchant',
      // ... more statuses
    };

    return statusMap[retId] || 'Unknown status';
  }
}

// Usage Example
const query = new NewebPayQueryShipment({
  merchantId: 'YOUR_MERCHANT_ID',
  hashKey: 'YOUR_HASH_KEY',
  hashIV: 'YOUR_HASH_IV',
});

const status = await query.queryShipment('ORD123456');

console.log(`Order: ${status.merchantOrderNo}`);
console.log(`Status: ${status.retString} (${status.retId})`);
console.log(`Tracking No: ${status.lgsNo}`);
console.log(`Store: ${status.storeName}`);

export { NewebPayQueryShipment };
```

---

### 7. Modify Shipment

Modify shipment order details.

#### TypeScript Example

```typescript
interface ModifyShipmentRequest {
  merchantOrderNo: string;
  lgsType: 'B2C' | 'C2C';
  shipType: '1' | '2' | '3' | '4';
  userName?: string;
  userTel?: string;
  userEmail?: string;
  storeID?: string;
}

class NewebPayModifyShipment extends NewebPayLogistics {
  /**
   * Modify shipment order
   */
  async modifyShipment(params: ModifyShipmentRequest) {
    const data: any = {
      MerchantOrderNo: params.merchantOrderNo,
      LgsType: params.lgsType,
      ShipType: params.shipType,
      TimeStamp: this.getTimestamp(),
    };

    // Add optional fields
    if (params.userName) data.UserName = params.userName;
    if (params.userTel) data.UserTel = params.userTel;
    if (params.userEmail) data.UserEmail = params.userEmail;
    if (params.storeID) data.StoreID = params.storeID;

    const { EncryptData_, HashData_ } = this.encryptData(data);

    const requestData = {
      UID_: this.config.merchantId,
      EncryptData_,
      HashData_,
      Version_: '1.0',
      RespondType_: 'JSON',
    };

    const response = await axios.post(
      `${this.baseUrl}/modifyShipment`,
      new URLSearchParams(requestData as any),
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      }
    );

    const result = response.data;

    if (result.Status !== 'SUCCESS') {
      throw new Error(`Modify shipment failed: ${result.Message}`);
    }

    // Decrypt response
    const decrypted = this.decryptData(result.EncryptData, result.HashData);

    return {
      merchantID: decrypted.MerchantID,
      merchantOrderNo: decrypted.MerchantOrderNo,
      lgsType: decrypted.LgsType,
      shipType: decrypted.ShipType,
    };
  }
}

// Usage Example
const modify = new NewebPayModifyShipment({
  merchantId: 'YOUR_MERCHANT_ID',
  hashKey: 'YOUR_HASH_KEY',
  hashIV: 'YOUR_HASH_IV',
});

// Change recipient information
await modify.modifyShipment({
  merchantOrderNo: 'ORD123456',
  lgsType: 'C2C',
  shipType: '1',
  userName: 'Jane Doe',
  userTel: '0987654321',
  userEmail: 'jane@example.com',
});

// Change pickup store
await modify.modifyShipment({
  merchantOrderNo: 'ORD123456',
  lgsType: 'C2C',
  shipType: '1',
  storeID: '654321',
});

export { NewebPayModifyShipment };
```

---

### 8. Track Shipment

Track logistics delivery history.

#### Python Example

```python
"""Track Shipment History - Python Example"""


class NewebPayTrackShipment(NewebPayLogistics):
    """Track Shipment Operations"""

    def track_shipment(self, merchant_order_no: str) -> Dict[str, any]:
        """Track shipment history"""

        data = {
            'MerchantOrderNo': merchant_order_no,
            'TimeStamp': self.get_timestamp(),
        }

        encrypted = self.encrypt_data(data)

        request_data = {
            'UID_': self.merchant_id,
            'EncryptData_': encrypted['EncryptData_'],
            'HashData_': encrypted['HashData_'],
            'Version_': '1.0',
            'RespondType_': 'JSON',
        }

        response = requests.post(
            f'{self.base_url}/trace',
            data=request_data,
        )

        result = response.json()

        if result['Status'] != 'SUCCESS':
            raise Exception(f"Track shipment failed: {result['Message']}")

        # Decrypt response
        decrypted = self.decrypt_data(result['EncryptData'], result['HashData'])

        return {
            'lgs_type': decrypted['LgsType'],
            'merchant_order_no': decrypted['MerchantOrderNo'],
            'lgs_no': decrypted['LgsNo'],
            'trade_type': decrypted['TradeType'],
            'ship_type': decrypted['ShipType'],
            'history': decrypted.get('History', []),
            'ret_id': decrypted.get('Retld', ''),
            'ret_string': decrypted.get('RetString', ''),
        }

    def print_tracking_history(self, merchant_order_no: str):
        """Print tracking history in readable format"""

        tracking = self.track_shipment(merchant_order_no)

        print(f"Order: {tracking['merchant_order_no']}")
        print(f"Tracking No: {tracking['lgs_no']}")
        print(f"Current Status: {tracking['ret_string']}")
        print("\nHistory:")

        for event in tracking['history']:
            print(f"  {event.get('EventTime')}: {event.get('RetString')}")


# Usage Example
track = NewebPayTrackShipment(
    merchant_id='YOUR_MERCHANT_ID',
    hash_key='YOUR_HASH_KEY',
    hash_iv='YOUR_HASH_IV',
)

# Get tracking history
tracking = track.track_shipment('ORD123456')

# Print formatted history
track.print_tracking_history('ORD123456')
```

---

### 9. Status Notification (Callback)

Handle real-time status notifications from NewebPay.

#### Express.js Example

```typescript
import express from 'express';

const app = express();

app.use(express.urlencoded({ extended: true }));
app.use(express.json());

const logistics = new NewebPayLogistics({
  merchantId: 'YOUR_MERCHANT_ID',
  hashKey: 'YOUR_HASH_KEY',
  hashIV: 'YOUR_HASH_IV',
});

/**
 * Handle shipment status notification
 */
app.post('/callback/shipment-status', async (req, res) => {
  try {
    const { Status, Message, EncryptData_, HashData_, UID_, Version_ } = req.body;

    console.log('Received notification:', {
      Status,
      Message,
      UID: UID_,
      Version: Version_,
    });

    if (Status !== 'SUCCESS') {
      console.error('Notification error:', Message);
      return res.send('0|Error');
    }

    // Decrypt data
    const data = logistics.decryptData(EncryptData_, HashData_);

    console.log('Notification data:', data);

    // Process the notification
    await processShipmentStatusUpdate({
      lgsType: data.LgsType,
      merchantOrderNo: data.MerchantOrderNo,
      lgsNo: data.LgsNo,
      tradeType: data.TradeType,
      shipType: data.ShipType,
      retId: data.Retld,
      retString: data.RetString,
      eventTime: data.EventTime,
    });

    // Return success
    res.send('1|OK');
  } catch (error) {
    console.error('Callback error:', error);
    res.send('0|Error');
  }
});

/**
 * Process shipment status update
 */
async function processShipmentStatusUpdate(data: {
  lgsType: string;
  merchantOrderNo: string;
  lgsNo: string;
  tradeType: number;
  shipType: string;
  retId: string;
  retString: string;
  eventTime: string;
}) {
  console.log(`Processing status update for order ${data.merchantOrderNo}`);

  // Update database
  // await db.orders.updateOne(
  //   { orderNo: data.merchantOrderNo },
  //   {
  //     $set: {
  //       'logistics.status': data.retId,
  //       'logistics.statusDesc': data.retString,
  //       'logistics.trackingNo': data.lgsNo,
  //       'logistics.lastUpdate': new Date(data.eventTime),
  //     },
  //   }
  // );

  // Send notification to customer
  if (data.retId === '6') {
    // Customer picked up
    // await sendEmail({
    //   to: customerEmail,
    //   subject: 'Order Delivered',
    //   body: `Your order ${data.merchantOrderNo} has been picked up.`,
    // });
  }

  console.log(`Status update completed for order ${data.merchantOrderNo}`);
}

app.listen(3000, () => {
  console.log('Callback server listening on port 3000');
});
```

#### Flask Example

```python
"""Status Notification Callback - Flask Example"""

from flask import Flask, request


app = Flask(__name__)

logistics = NewebPayLogistics(
    merchant_id='YOUR_MERCHANT_ID',
    hash_key='YOUR_HASH_KEY',
    hash_iv='YOUR_HASH_IV',
)


@app.route('/callback/shipment-status', methods=['POST'])
def shipment_status_callback():
    """Handle shipment status notification"""

    try:
        data = request.form.to_dict()

        status = data.get('Status')
        message = data.get('Message')
        encrypt_data = data.get('EncryptData_')
        hash_data = data.get('HashData_')

        app.logger.info(f'Received notification: {status} - {message}')

        if status != 'SUCCESS':
            app.logger.error(f'Notification error: {message}')
            return '0|Error'

        # Decrypt data
        decrypted = logistics.decrypt_data(encrypt_data, hash_data)

        app.logger.info(f'Notification data: {decrypted}')

        # Process the notification
        process_shipment_status_update(decrypted)

        # Return success
        return '1|OK'

    except Exception as e:
        app.logger.error(f'Callback error: {str(e)}')
        return '0|Error'


def process_shipment_status_update(data: Dict[str, any]):
    """Process shipment status update"""

    merchant_order_no = data['MerchantOrderNo']
    ret_id = data.get('Retld')
    ret_string = data.get('RetString')

    app.logger.info(f'Processing status update for order {merchant_order_no}')

    # Update database
    # db.orders.update_one(
    #     {'order_no': merchant_order_no},
    #     {
    #         '$set': {
    #             'logistics.status': ret_id,
    #             'logistics.status_desc': ret_string,
    #             'logistics.tracking_no': data['LgsNo'],
    #             'logistics.last_update': datetime.now(),
    #         }
    #     }
    # )

    # Send notification to customer
    if ret_id == '6':
        # Customer picked up
        # send_email(
        #     to=customer_email,
        #     subject='Order Delivered',
        #     body=f'Your order {merchant_order_no} has been picked up.',
        # )
        pass

    app.logger.info(f'Status update completed for order {merchant_order_no}')


if __name__ == '__main__':
    app.run(port=3000)
```

---

## PAYUNi Logistics Examples

### 1. Basic Integration (PAYUNi)

#### TypeScript - AES-256-GCM Encryption Helper

```typescript
import crypto from 'crypto';

interface PAYUNiConfig {
  merchantId: string;
  hashKey: string;
  hashIV: string;
  isProduction?: boolean;
}

class PAYUNiLogistics {
  private config: Required<PAYUNiConfig>;
  private baseUrl: string;

  constructor(config: PAYUNiConfig) {
    this.config = {
      ...config,
      isProduction: config.isProduction ?? false,
    };

    this.baseUrl = this.config.isProduction
      ? 'https://api.payuni.com.tw/api'
      : 'https://sandbox-api.payuni.com.tw/api';
  }

  /**
   * AES-256-GCM Encryption
   */
  encrypt(data: Record<string, any>): string {
    // Convert to query string
    const queryString = new URLSearchParams(data).toString();

    // Create cipher
    const cipher = crypto.createCipheriv(
      'aes-256-gcm',
      this.config.hashKey,
      this.config.hashIV
    );

    // Encrypt
    let encrypted = cipher.update(queryString, 'utf8', 'hex');
    encrypted += cipher.final('hex');

    // Get auth tag
    const authTag = cipher.getAuthTag().toString('hex');

    // Combine encrypted + tag
    return encrypted + authTag;
  }

  /**
   * AES-256-GCM Decryption
   */
  decrypt(encryptInfo: string): Record<string, any> {
    // Split encrypted data and tag (tag is last 32 hex chars = 16 bytes)
    const encrypted = encryptInfo.slice(0, -32);
    const authTag = encryptInfo.slice(-32);

    // Create decipher
    const decipher = crypto.createDecipheriv(
      'aes-256-gcm',
      this.config.hashKey,
      this.config.hashIV
    );

    // Set auth tag
    decipher.setAuthTag(Buffer.from(authTag, 'hex'));

    // Decrypt
    let decrypted = decipher.update(encrypted, 'hex', 'utf8');
    decrypted += decipher.final('utf8');

    // Parse query string
    const params = new URLSearchParams(decrypted);
    const result: Record<string, any> = {};
    params.forEach((value, key) => {
      result[key] = value;
    });

    return result;
  }

  /**
   * Generate HashInfo (SHA256)
   */
  generateHashInfo(encryptInfo: string): string {
    const raw = encryptInfo + this.config.hashKey + this.config.hashIV;
    return crypto.createHash('sha256').update(raw).digest('hex').toUpperCase();
  }

  /**
   * Get current Unix timestamp
   */
  getTimestamp(): number {
    return Math.floor(Date.now() / 1000);
  }
}

export { PAYUNiLogistics };
```

#### Python - AES-256-GCM Encryption Helper

```python
"""PAYUNi Logistics Encryption Helper - Python"""

from Crypto.Cipher import AES
from urllib.parse import urlencode, parse_qs
import hashlib
import time
from typing import Dict, Any


class PAYUNiLogistics:
    """PAYUNi Logistics API Client"""

    def __init__(
        self,
        merchant_id: str,
        hash_key: str,
        hash_iv: str,
        is_production: bool = False
    ):
        self.merchant_id = merchant_id
        self.hash_key = hash_key.encode('utf-8')
        self.hash_iv = hash_iv.encode('utf-8')

        self.base_url = (
            'https://api.payuni.com.tw/api'
            if is_production
            else 'https://sandbox-api.payuni.com.tw/api'
        )

    def encrypt(self, data: Dict[str, Any]) -> str:
        """AES-256-GCM Encryption"""
        # Convert to query string
        query_string = urlencode(data)

        # Create cipher
        cipher = AES.new(self.hash_key, AES.MODE_GCM, nonce=self.hash_iv)

        # Encrypt and get tag
        encrypted, tag = cipher.encrypt_and_digest(query_string.encode('utf-8'))

        # Combine encrypted + tag and convert to hex
        return (encrypted + tag).hex()

    def decrypt(self, encrypt_info: str) -> Dict[str, Any]:
        """AES-256-GCM Decryption"""
        # Convert hex to binary
        data = bytes.fromhex(encrypt_info)

        # Split encrypted data and tag (last 16 bytes)
        encrypted = data[:-16]
        tag = data[-16:]

        # Create cipher
        cipher = AES.new(self.hash_key, AES.MODE_GCM, nonce=self.hash_iv)

        # Decrypt and verify
        decrypted = cipher.decrypt_and_verify(encrypted, tag)

        # Parse query string
        result = dict(parse_qs(decrypted.decode('utf-8')))
        return {k: v[0] if len(v) == 1 else v for k, v in result.items()}

    def generate_hash_info(self, encrypt_info: str) -> str:
        """Generate HashInfo (SHA256)"""
        raw = encrypt_info + self.hash_key.decode('utf-8') + self.hash_iv.decode('utf-8')
        return hashlib.sha256(raw.encode('utf-8')).hexdigest().upper()

    @staticmethod
    def get_timestamp() -> int:
        """Get current Unix timestamp"""
        return int(time.time())
```

---

### 2. Create 7-11 C2C Shipment

#### TypeScript Example

```typescript
import axios from 'axios';

interface Create711ShipmentRequest {
  merTradeNo: string;
  goodsType: 1 | 2; // 1=Normal, 2=Frozen
  goodsAmount: number;
  goodsName: string;
  senderName: string;
  senderPhone: string;
  senderStoreID: string;
  receiverName: string;
  receiverPhone: string;
  receiverStoreID: string;
  notifyURL: string;
}

class PAYUNi711Logistics extends PAYUNiLogistics {
  /**
   * Create 7-11 C2C shipment
   */
  async create711Shipment(params: Create711ShipmentRequest) {
    const data = {
      MerID: this.config.merchantId,
      MerTradeNo: params.merTradeNo,
      LogisticsType: 'PAYUNi_Logistic_711',
      GoodsType: params.goodsType,
      GoodsAmount: params.goodsAmount,
      GoodsName: params.goodsName,
      SenderName: params.senderName,
      SenderPhone: params.senderPhone,
      SenderStoreID: params.senderStoreID,
      ReceiverName: params.receiverName,
      ReceiverPhone: params.receiverPhone,
      ReceiverStoreID: params.receiverStoreID,
      NotifyURL: params.notifyURL,
      Timestamp: this.getTimestamp(),
    };

    const encryptInfo = this.encrypt(data);
    const hashInfo = this.generateHashInfo(encryptInfo);

    const response = await axios.post(
      `${this.baseUrl}/logistics/create`,
      new URLSearchParams({
        MerID: this.config.merchantId,
        Version: '1.0',
        EncryptInfo: encryptInfo,
        HashInfo: hashInfo,
      }),
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      }
    );

    const result = response.data;

    if (result.Status !== 'SUCCESS') {
      throw new Error(`Create shipment failed: ${result.Message}`);
    }

    // Decrypt response
    const decrypted = this.decrypt(result.EncryptInfo);

    return {
      logisticsID: decrypted.LogisticsID,
      merTradeNo: decrypted.MerTradeNo,
      cvsPaymentNo: decrypted.CVSPaymentNo,
      cvsValidationNo: decrypted.CVSValidationNo,
      expireDate: decrypted.ExpireDate,
    };
  }
}

// Usage Example
const logistics = new PAYUNi711Logistics({
  merchantId: 'YOUR_MERCHANT_ID',
  hashKey: 'YOUR_HASH_KEY',
  hashIV: 'YOUR_HASH_IV',
  isProduction: false,
});

const result = await logistics.create711Shipment({
  merTradeNo: `LOG${Date.now()}`,
  goodsType: 1, // Normal temperature
  goodsAmount: 500,
  goodsName: 'T-shirt',
  senderName: 'John Doe',
  senderPhone: '0912345678',
  senderStoreID: '123456', // 7-11 sender store
  receiverName: 'Jane Doe',
  receiverPhone: '0987654321',
  receiverStoreID: '654321', // 7-11 receiver store
  notifyURL: 'https://your-site.com/callback/payuni-711',
});

console.log('Logistics ID:', result.logisticsID);
console.log('Payment Code:', result.cvsPaymentNo);

export { PAYUNi711Logistics };
```

#### Python Example

```python
"""Create 7-11 C2C Shipment - Python Example"""

import requests
from typing import Dict


class PAYUNi711Logistics(PAYUNiLogistics):
    """7-11 C2C Logistics Operations"""

    def create_711_shipment(
        self,
        mer_trade_no: str,
        goods_type: int,  # 1=Normal, 2=Frozen
        goods_amount: int,
        goods_name: str,
        sender_name: str,
        sender_phone: str,
        sender_store_id: str,
        receiver_name: str,
        receiver_phone: str,
        receiver_store_id: str,
        notify_url: str,
    ) -> Dict[str, any]:
        """Create 7-11 C2C shipment"""

        data = {
            'MerID': self.merchant_id,
            'MerTradeNo': mer_trade_no,
            'LogisticsType': 'PAYUNi_Logistic_711',
            'GoodsType': goods_type,
            'GoodsAmount': goods_amount,
            'GoodsName': goods_name,
            'SenderName': sender_name,
            'SenderPhone': sender_phone,
            'SenderStoreID': sender_store_id,
            'ReceiverName': receiver_name,
            'ReceiverPhone': receiver_phone,
            'ReceiverStoreID': receiver_store_id,
            'NotifyURL': notify_url,
            'Timestamp': self.get_timestamp(),
        }

        encrypt_info = self.encrypt(data)
        hash_info = self.generate_hash_info(encrypt_info)

        response = requests.post(
            f'{self.base_url}/logistics/create',
            data={
                'MerID': self.merchant_id,
                'Version': '1.0',
                'EncryptInfo': encrypt_info,
                'HashInfo': hash_info,
            },
        )

        result = response.json()

        if result['Status'] != 'SUCCESS':
            raise Exception(f"Create shipment failed: {result['Message']}")

        # Decrypt response
        decrypted = self.decrypt(result['EncryptInfo'])

        return {
            'logistics_id': decrypted['LogisticsID'],
            'mer_trade_no': decrypted['MerTradeNo'],
            'cvs_payment_no': decrypted['CVSPaymentNo'],
            'cvs_validation_no': decrypted['CVSValidationNo'],
            'expire_date': decrypted['ExpireDate'],
        }


# Usage Example
logistics = PAYUNi711Logistics(
    merchant_id='YOUR_MERCHANT_ID',
    hash_key='YOUR_HASH_KEY',
    hash_iv='YOUR_HASH_IV',
    is_production=False,
)

result = logistics.create_711_shipment(
    mer_trade_no=f'LOG{int(time.time())}',
    goods_type=1,  # Normal temperature
    goods_amount=500,
    goods_name='T-shirt',
    sender_name='John Doe',
    sender_phone='0912345678',
    sender_store_id='123456',
    receiver_name='Jane Doe',
    receiver_phone='0987654321',
    receiver_store_id='654321',
    notify_url='https://your-site.com/callback/payuni-711',
)

print(f"Logistics ID: {result['logistics_id']}")
print(f"Payment Code: {result['cvs_payment_no']}")
```

---

### 3. Create T-Cat Home Delivery

#### TypeScript Example

```typescript
interface CreateTCatShipmentRequest {
  merTradeNo: string;
  goodsType: 1 | 2 | 3; // 1=Normal, 2=Frozen, 3=Refrigerated
  goodsAmount: number;
  goodsName: string;
  goodsWeight?: number;
  senderName: string;
  senderPhone: string;
  senderZipCode: string;
  senderAddress: string;
  receiverName: string;
  receiverPhone: string;
  receiverZipCode: string;
  receiverAddress: string;
  scheduledDeliveryTime?: '01' | '02' | '03';
  notifyURL: string;
}

class PAYUNiTCatLogistics extends PAYUNiLogistics {
  /**
   * Create T-Cat home delivery shipment
   */
  async createTCatShipment(params: CreateTCatShipmentRequest) {
    const logisticsType =
      params.goodsType === 2 ? 'PAYUNi_Logistic_Tcat_Freeze' :
      params.goodsType === 3 ? 'PAYUNi_Logistic_Tcat_Cold' :
      'PAYUNi_Logistic_Tcat';

    const data: any = {
      MerID: this.config.merchantId,
      MerTradeNo: params.merTradeNo,
      LogisticsType: logisticsType,
      GoodsType: params.goodsType,
      GoodsAmount: params.goodsAmount,
      GoodsName: params.goodsName,
      SenderName: params.senderName,
      SenderPhone: params.senderPhone,
      SenderZipCode: params.senderZipCode,
      SenderAddress: params.senderAddress,
      ReceiverName: params.receiverName,
      ReceiverPhone: params.receiverPhone,
      ReceiverZipCode: params.receiverZipCode,
      ReceiverAddress: params.receiverAddress,
      NotifyURL: params.notifyURL,
      Timestamp: this.getTimestamp(),
    };

    if (params.goodsWeight) data.GoodsWeight = params.goodsWeight;
    if (params.scheduledDeliveryTime) data.ScheduledDeliveryTime = params.scheduledDeliveryTime;

    const encryptInfo = this.encrypt(data);
    const hashInfo = this.generateHashInfo(encryptInfo);

    const response = await axios.post(
      `${this.baseUrl}/logistics/create`,
      new URLSearchParams({
        MerID: this.config.merchantId,
        Version: '1.0',
        EncryptInfo: encryptInfo,
        HashInfo: hashInfo,
      }),
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      }
    );

    const result = response.data;

    if (result.Status !== 'SUCCESS') {
      throw new Error(`Create shipment failed: ${result.Message}`);
    }

    const decrypted = this.decrypt(result.EncryptInfo);

    return {
      logisticsID: decrypted.LogisticsID,
      merTradeNo: decrypted.MerTradeNo,
      shipmentNo: decrypted.ShipmentNo,
      bookingNote: decrypted.BookingNote,
    };
  }
}

// Usage Example
const tcat = new PAYUNiTCatLogistics({
  merchantId: 'YOUR_MERCHANT_ID',
  hashKey: 'YOUR_HASH_KEY',
  hashIV: 'YOUR_HASH_IV',
});

const result = await tcat.createTCatShipment({
  merTradeNo: `TCAT${Date.now()}`,
  goodsType: 1, // Normal temperature
  goodsAmount: 1000,
  goodsName: 'Electronics',
  goodsWeight: 500, // 500g
  senderName: 'Sender Name',
  senderPhone: '0912345678',
  senderZipCode: '100',
  senderAddress: 'Taipei City, Zhongzheng Dist., XXX Road No.1',
  receiverName: 'Receiver Name',
  receiverPhone: '0987654321',
  receiverZipCode: '300',
  receiverAddress: 'Hsinchu City, East Dist., YYY Road No.2',
  scheduledDeliveryTime: '02', // 14:00-18:00
  notifyURL: 'https://your-site.com/callback/payuni-tcat',
});

console.log('Tracking No:', result.shipmentNo);

export { PAYUNiTCatLogistics };
```

---

### 4. Query Shipment Status

#### TypeScript Example

```typescript
class PAYUNiQueryLogistics extends PAYUNiLogistics {
  /**
   * Query shipment status
   */
  async queryShipment(merTradeNo: string) {
    const data = {
      MerID: this.config.merchantId,
      MerTradeNo: merTradeNo,
      Timestamp: this.getTimestamp(),
    };

    const encryptInfo = this.encrypt(data);
    const hashInfo = this.generateHashInfo(encryptInfo);

    const response = await axios.post(
      `${this.baseUrl}/logistics/query`,
      new URLSearchParams({
        MerID: this.config.merchantId,
        Version: '1.0',
        EncryptInfo: encryptInfo,
        HashInfo: hashInfo,
      }),
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      }
    );

    const result = response.data;

    if (result.Status !== 'SUCCESS') {
      throw new Error(`Query shipment failed: ${result.Message}`);
    }

    const decrypted = this.decrypt(result.EncryptInfo);

    return {
      logisticsID: decrypted.LogisticsID,
      merTradeNo: decrypted.MerTradeNo,
      logisticsType: decrypted.LogisticsType,
      logisticsStatus: decrypted.LogisticsStatus,
      logisticsStatusMsg: decrypted.LogisticsStatusMsg,
      shipmentNo: decrypted.ShipmentNo,
      receiverStoreID: decrypted.ReceiverStoreID,
      updateTime: decrypted.UpdateTime,
    };
  }

  /**
   * Get human-readable status
   */
  getStatusDescription(statusCode: string): string {
    const statusMap: Record<string, string> = {
      '11': 'Shipped',
      '21': 'Arrived at store / In delivery',
      '22': 'Picked up / Delivered',
      '31': 'Returning',
      '32': 'Return completed',
    };

    return statusMap[statusCode] || 'Unknown status';
  }
}

// Usage Example
const query = new PAYUNiQueryLogistics({
  merchantId: 'YOUR_MERCHANT_ID',
  hashKey: 'YOUR_HASH_KEY',
  hashIV: 'YOUR_HASH_IV',
});

const status = await query.queryShipment('LOG123456');

console.log(`Order: ${status.merTradeNo}`);
console.log(`Status: ${status.logisticsStatusMsg} (${status.logisticsStatus})`);
console.log(`Tracking No: ${status.shipmentNo}`);

export { PAYUNiQueryLogistics };
```

---

### 5. Status Notification Callback

#### Express.js Example

```typescript
import express from 'express';

const app = express();

app.use(express.urlencoded({ extended: true }));
app.use(express.json());

const logistics = new PAYUNiLogistics({
  merchantId: 'YOUR_MERCHANT_ID',
  hashKey: 'YOUR_HASH_KEY',
  hashIV: 'YOUR_HASH_IV',
});

/**
 * Handle PAYUNi logistics status notification
 */
app.post('/callback/payuni-logistics', async (req, res) => {
  try {
    const { MerID, EncryptInfo, HashInfo } = req.body;

    console.log('Received notification from PAYUNi');

    // Verify HashInfo
    const calculatedHash = logistics.generateHashInfo(EncryptInfo);
    if (calculatedHash !== HashInfo.toUpperCase()) {
      console.error('Hash verification failed');
      return res.send('Hash Error');
    }

    // Decrypt data
    const data = logistics.decrypt(EncryptInfo);

    console.log('Notification data:', data);

    // Process the notification
    await processLogisticsStatusUpdate({
      merTradeNo: data.MerTradeNo,
      logisticsID: data.LogisticsID,
      logisticsType: data.LogisticsType,
      logisticsStatus: data.LogisticsStatus,
      logisticsStatusMsg: data.LogisticsStatusMsg,
      updateTime: data.UpdateTime,
    });

    // Return SUCCESS
    res.send('SUCCESS');
  } catch (error) {
    console.error('Callback error:', error);
    res.send('Error');
  }
});

/**
 * Process logistics status update
 */
async function processLogisticsStatusUpdate(data: {
  merTradeNo: string;
  logisticsID: string;
  logisticsType: string;
  logisticsStatus: string;
  logisticsStatusMsg: string;
  updateTime: string;
}) {
  console.log(`Processing status update for order ${data.merTradeNo}`);

  // Update database
  // await db.orders.updateOne(
  //   { orderNo: data.merTradeNo },
  //   {
  //     $set: {
  //       'logistics.status': data.logisticsStatus,
  //       'logistics.statusMsg': data.logisticsStatusMsg,
  //       'logistics.logisticsID': data.logisticsID,
  //       'logistics.lastUpdate': new Date(data.updateTime),
  //     },
  //   }
  // );

  // Send notification to customer based on status
  switch (data.logisticsStatus) {
    case '11':
      // Shipped
      console.log('Order shipped');
      break;
    case '21':
      // Arrived
      console.log('Arrived at destination');
      break;
    case '22':
      // Picked up / Delivered
      console.log('Delivery completed');
      // await sendEmail({ ... });
      break;
    case '31':
    case '32':
      // Return
      console.log('Order returned');
      break;
  }
}

app.listen(3000, () => {
  console.log('PAYUNi callback server listening on port 3000');
});
```

---

## ECPay Logistics Examples

### 1. Basic Integration (ECPay)

#### TypeScript - MD5 CheckMacValue Helper

```typescript
import crypto from 'crypto';

interface ECPayConfig {
  merchantId: string;
  hashKey: string;
  hashIV: string;
  isProduction?: boolean;
}

class ECPayLogistics {
  private config: Required<ECPayConfig>;
  private baseUrl: string;

  constructor(config: ECPayConfig) {
    this.config = {
      ...config,
      isProduction: config.isProduction ?? false,
    };

    this.baseUrl = this.config.isProduction
      ? 'https://logistics.ecpay.com.tw'
      : 'https://logistics-stage.ecpay.com.tw';
  }

  /**
   * Generate CheckMacValue (MD5)
   */
  generateCheckMacValue(params: Record<string, any>): string {
    // Sort parameters
    const sorted = Object.keys(params)
      .sort()
      .reduce((acc, key) => {
        acc[key] = params[key];
        return acc;
      }, {} as Record<string, any>);

    // Create query string
    const paramStr = Object.entries(sorted)
      .map(([key, value]) => `${key}=${value}`)
      .join('&');

    // Add HashKey and HashIV
    const raw = `HashKey=${this.config.hashKey}&${paramStr}&HashIV=${this.config.hashIV}`;

    // URL encode and convert to lowercase
    const encoded = encodeURIComponent(raw).toLowerCase();

    // MD5 hash and uppercase
    return crypto.createHash('md5').update(encoded).digest('hex').toUpperCase();
  }

  /**
   * Verify CheckMacValue from callback
   */
  verifyCheckMacValue(params: Record<string, any>): boolean {
    const { CheckMacValue, ...data } = params;
    const calculated = this.generateCheckMacValue(data);
    return calculated === CheckMacValue;
  }
}

export { ECPayLogistics };
```

#### Python - MD5 CheckMacValue Helper

```python
"""ECPay Logistics Encryption Helper - Python"""

import hashlib
import urllib.parse
from typing import Dict, Any


class ECPayLogistics:
    """ECPay Logistics API Client"""

    def __init__(
        self,
        merchant_id: str,
        hash_key: str,
        hash_iv: str,
        is_production: bool = False
    ):
        self.merchant_id = merchant_id
        self.hash_key = hash_key
        self.hash_iv = hash_iv

        self.base_url = (
            'https://logistics.ecpay.com.tw'
            if is_production
            else 'https://logistics-stage.ecpay.com.tw'
        )

    def generate_check_mac_value(self, params: Dict[str, Any]) -> str:
        """Generate CheckMacValue (MD5)"""
        # Sort parameters
        sorted_params = sorted(params.items())

        # Create query string
        param_str = '&'.join(f'{k}={v}' for k, v in sorted_params)

        # Add HashKey and HashIV
        raw = f'HashKey={self.hash_key}&{param_str}&HashIV={self.hash_iv}'

        # URL encode and convert to lowercase
        encoded = urllib.parse.quote_plus(raw).lower()

        # MD5 hash and uppercase
        return hashlib.md5(encoded.encode('utf-8')).hexdigest().upper()

    def verify_check_mac_value(self, params: Dict[str, Any]) -> bool:
        """Verify CheckMacValue from callback"""
        check_mac = params.pop('CheckMacValue', None)
        if not check_mac:
            return False

        calculated = self.generate_check_mac_value(params)
        return calculated == check_mac
```

---

### 2. Create CVS C2C Shipment (ECPay)

#### TypeScript Example

```typescript
import axios from 'axios';

interface CreateCVSShipmentRequest {
  merTradeNo: string;
  logisticsSubType: 'FAMI' | 'UNIMART' | 'UNIMARTFREEZE' | 'HILIFE' | 'OKMART';
  goodsAmount: number;
  goodsName: string;
  senderName: string;
  senderCellPhone: string;
  receiverName: string;
  receiverCellPhone: string;
  receiverStoreID: string;
  isCollection?: 'Y' | 'N';
  serverReplyURL: string;
}

class ECPayCVSLogistics extends ECPayLogistics {
  /**
   * Create CVS C2C shipment
   */
  async createCVSShipment(params: CreateCVSShipmentRequest) {
    const tradeDate = new Date().toLocaleString('zh-TW', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    }).replace(/\//g, '/');

    const data: Record<string, any> = {
      MerchantID: this.config.merchantId,
      MerchantTradeNo: params.merTradeNo,
      MerchantTradeDate: tradeDate,
      LogisticsType: 'CVS',
      LogisticsSubType: params.logisticsSubType,
      GoodsAmount: params.goodsAmount,
      GoodsName: params.goodsName,
      SenderName: params.senderName,
      SenderCellPhone: params.senderCellPhone,
      ReceiverName: params.receiverName,
      ReceiverCellPhone: params.receiverCellPhone,
      ReceiverStoreID: params.receiverStoreID,
      IsCollection: params.isCollection || 'N',
      ServerReplyURL: params.serverReplyURL,
    };

    // Generate CheckMacValue
    data.CheckMacValue = this.generateCheckMacValue(data);

    const response = await axios.post(
      `${this.baseUrl}/Express/Create`,
      new URLSearchParams(data),
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      }
    );

    // Parse response (1=key&value format)
    const result: Record<string, string> = {};
    response.data.split('&').forEach((item: string) => {
      const [key, value] = item.split('=');
      if (key && value) {
        result[key] = decodeURIComponent(value);
      }
    });

    if (result.RtnCode !== '300' && result.RtnCode !== '2001') {
      throw new Error(`Create shipment failed: ${result.RtnMsg}`);
    }

    return {
      allPayLogisticsID: result.AllPayLogisticsID,
      cvsPaymentNo: result.CVSPaymentNo,
      cvsValidationNo: result.CVSValidationNo,
      bookingNote: result.BookingNote,
    };
  }
}

// Usage Example
const logistics = new ECPayCVSLogistics({
  merchantId: '2000132',
  hashKey: '5294y06JbISpM5x9',
  hashIV: 'v77hoKGq4kWxNNIS',
  isProduction: false,
});

const result = await logistics.createCVSShipment({
  merTradeNo: `CVS${Date.now()}`,
  logisticsSubType: 'UNIMART', // 7-11
  goodsAmount: 500,
  goodsName: 'Test Product',
  senderName: 'Sender Name',
  senderCellPhone: '0912345678',
  receiverName: 'Receiver Name',
  receiverCellPhone: '0987654321',
  receiverStoreID: '131386', // 7-11 store code
  isCollection: 'N',
  serverReplyURL: 'https://your-site.com/callback/ecpay-cvs',
});

console.log('Logistics ID:', result.allPayLogisticsID);
console.log('Payment No:', result.cvsPaymentNo);

export { ECPayCVSLogistics };
```

#### Python Example

```python
#!/usr/bin/env python3
"""
Create CVS C2C Shipment - ECPay Python Example

依照 taiwan-logistics-skill 嚴格規範撰寫
"""

import requests
import urllib.parse
import time
from datetime import datetime
from typing import Dict, Literal, Optional
from dataclasses import dataclass


@dataclass
class CVSShipmentData:
    """CVS C2C 物流訂單資料"""
    mer_trade_no: str
    logistics_sub_type: Literal['FAMI', 'UNIMART', 'UNIMARTFREEZE', 'HILIFE', 'OKMART']
    goods_amount: int
    goods_name: str
    sender_name: str
    sender_cell_phone: str
    receiver_name: str
    receiver_cell_phone: str
    receiver_store_id: str
    is_collection: str = 'N'
    server_reply_url: str = ''


@dataclass
class CVSShipmentResponse:
    """CVS C2C 物流訂單回應"""
    success: bool
    rtn_code: str
    rtn_msg: str
    all_pay_logistics_id: str = ''
    cvs_payment_no: str = ''
    cvs_validation_no: str = ''
    booking_note: str = ''
    raw: Dict[str, str] = None


class ECPayCVSLogistics(ECPayLogistics):
    """
    ECPay CVS 超商物流服務

    支援超商類型:
    - FAMI: FamilyMart 全家便利商店
    - UNIMART: 7-ELEVEN 統一超商 (常溫)
    - UNIMARTFREEZE: 7-ELEVEN 統一超商 (冷凍)
    - HILIFE: Hi-Life 萊爾富便利商店
    - OKMART: OK Mart OK 便利商店

    回傳碼:
    - 300: 訂單建立成功 (尚未寄貨)
    - 2001: 訂單建立成功 (門市已出貨)
    """

    def create_cvs_shipment(
        self,
        data: CVSShipmentData,
    ) -> CVSShipmentResponse:
        """
        建立 CVS C2C 超商物流訂單

        Args:
            data: CVS 物流訂單資料 (CVSShipmentData)

        Returns:
            CVSShipmentResponse: 物流訂單回應

        Raises:
            Exception: API 請求失敗或訂單建立失敗

        Example:
            >>> shipment_data = CVSShipmentData(
            ...     mer_trade_no=f'CVS{int(time.time())}',
            ...     logistics_sub_type='UNIMART',
            ...     goods_amount=500,
            ...     goods_name='Test Product',
            ...     sender_name='Sender Name',
            ...     sender_cell_phone='0912345678',
            ...     receiver_name='Receiver Name',
            ...     receiver_cell_phone='0987654321',
            ...     receiver_store_id='131386',
            ...     is_collection='N',
            ...     server_reply_url='https://your-site.com/callback',
            ... )
            >>> result = logistics.create_cvs_shipment(shipment_data)
            >>> print(result.all_pay_logistics_id)
        """
        # 產生交易日期時間 (格式: YYYY/MM/DD HH:MM:SS)
        trade_date = datetime.now().strftime('%Y/%m/%d %H:%M:%S')

        # 準備 API 請求參數
        api_params = {
            'MerchantID': self.merchant_id,
            'MerchantTradeNo': data.mer_trade_no,
            'MerchantTradeDate': trade_date,
            'LogisticsType': 'CVS',
            'LogisticsSubType': data.logistics_sub_type,
            'GoodsAmount': data.goods_amount,
            'GoodsName': data.goods_name,
            'SenderName': data.sender_name,
            'SenderCellPhone': data.sender_cell_phone,
            'ReceiverName': data.receiver_name,
            'ReceiverCellPhone': data.receiver_cell_phone,
            'ReceiverStoreID': data.receiver_store_id,
            'IsCollection': data.is_collection,
            'ServerReplyURL': data.server_reply_url,
        }

        # 產生 CheckMacValue (MD5 雜湊驗證碼)
        api_params['CheckMacValue'] = self.generate_check_mac_value(api_params)

        # 發送 API 請求
        try:
            response = requests.post(
                f'{self.base_url}/Express/Create',
                data=api_params,
                timeout=30,
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise Exception(f"API 請求失敗: {str(e)}")

        # 解析回應 (格式: key1=value1&key2=value2)
        result = {}
        for item in response.text.split('&'):
            if '=' in item:
                key, value = item.split('=', 1)
                result[key] = urllib.parse.unquote(value)

        # 檢查訂單狀態
        rtn_code = result.get('RtnCode', '')
        success = rtn_code in ['300', '2001']

        if not success:
            return CVSShipmentResponse(
                success=False,
                rtn_code=rtn_code,
                rtn_msg=result.get('RtnMsg', '未知錯誤'),
                raw=result,
            )

        # 回傳成功結果
        return CVSShipmentResponse(
            success=True,
            rtn_code=rtn_code,
            rtn_msg=result.get('RtnMsg', ''),
            all_pay_logistics_id=result.get('AllPayLogisticsID', ''),
            cvs_payment_no=result.get('CVSPaymentNo', ''),
            cvs_validation_no=result.get('CVSValidationNo', ''),
            booking_note=result.get('BookingNote', ''),
            raw=result,
        )


# Usage Example
if __name__ == '__main__':
    # 初始化物流服務 (使用測試環境)
    logistics = ECPayCVSLogistics(
        merchant_id='2000132',  # ECPay 測試商店代號
        hash_key='5294y06JbISpM5x9',  # ECPay 測試 HashKey
        hash_iv='v77hoKGq4kWxNNIS',  # ECPay 測試 HashIV
        is_production=False,  # 使用測試環境
    )

    # 準備物流訂單資料
    shipment_data = CVSShipmentData(
        mer_trade_no=f'CVS{int(time.time())}',  # 訂單編號 (唯一值)
        logistics_sub_type='UNIMART',  # 7-11 超商
        goods_amount=500,  # 商品金額
        goods_name='測試商品',  # 商品名稱
        sender_name='寄件人姓名',  # 寄件人姓名
        sender_cell_phone='0912345678',  # 寄件人手機
        receiver_name='收件人姓名',  # 收件人姓名
        receiver_cell_phone='0987654321',  # 收件人手機
        receiver_store_id='131386',  # 收件門市代號 (7-11)
        is_collection='N',  # 不代收貨款
        server_reply_url='https://your-site.com/callback/ecpay-cvs',  # 回傳網址
    )

    # 建立物流訂單
    try:
        result = logistics.create_cvs_shipment(shipment_data)

        if result.success:
            print(f"訂單建立成功")
            print(f"  物流編號: {result.all_pay_logistics_id}")
            print(f"  寄貨編號: {result.cvs_payment_no}")
            print(f"  驗證碼: {result.cvs_validation_no}")
            print(f"  托運單號: {result.booking_note}")
        else:
            print(f"✗ 訂單建立失敗")
            print(f"  錯誤代碼: {result.rtn_code}")
            print(f"  錯誤訊息: {result.rtn_msg}")
    except Exception as e:
        print(f"✗ 發生例外: {str(e)}")
```

---

### 3. Create Home Delivery (ECPay)

#### TypeScript Example

```typescript
interface CreateHomeShipmentRequest {
  merTradeNo: string;
  logisticsSubType: 'TCAT' | 'ECAN' | 'POST';
  goodsAmount: number;
  goodsName: string;
  senderName: string;
  senderCellPhone: string;
  senderZipCode: string;
  senderAddress: string;
  receiverName: string;
  receiverCellPhone: string;
  receiverZipCode: string;
  receiverAddress: string;
  temperature?: '0001' | '0002' | '0003';
  specification?: '0001' | '0002' | '0003' | '0004';
  distance?: '00' | '01' | '02' | '03';
  scheduledPickupTime?: '1' | '2' | '3' | '4';
  scheduledDeliveryTime?: '1' | '2' | '3' | '4' | '5';
  serverReplyURL: string;
}

class ECPayHomeLogistics extends ECPayLogistics {
  async createHomeShipment(params: CreateHomeShipmentRequest) {
    const tradeDate = new Date().toLocaleString('zh-TW', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    }).replace(/\//g, '/');

    const data: Record<string, any> = {
      MerchantID: this.config.merchantId,
      MerchantTradeNo: params.merTradeNo,
      MerchantTradeDate: tradeDate,
      LogisticsType: 'HOME',
      LogisticsSubType: params.logisticsSubType,
      GoodsAmount: params.goodsAmount,
      GoodsName: params.goodsName,
      SenderName: params.senderName,
      SenderCellPhone: params.senderCellPhone,
      SenderZipCode: params.senderZipCode,
      SenderAddress: params.senderAddress,
      ReceiverName: params.receiverName,
      ReceiverCellPhone: params.receiverCellPhone,
      ReceiverZipCode: params.receiverZipCode,
      ReceiverAddress: params.receiverAddress,
      ServerReplyURL: params.serverReplyURL,
    };

    // Optional parameters
    if (params.temperature) data.Temperature = params.temperature;
    if (params.specification) data.Specification = params.specification;
    if (params.distance) data.Distance = params.distance;
    if (params.scheduledPickupTime) data.ScheduledPickupTime = params.scheduledPickupTime;
    if (params.scheduledDeliveryTime) data.ScheduledDeliveryTime = params.scheduledDeliveryTime;

    data.CheckMacValue = this.generateCheckMacValue(data);

    const response = await axios.post(
      `${this.baseUrl}/Express/Create`,
      new URLSearchParams(data),
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      }
    );

    const result: Record<string, string> = {};
    response.data.split('&').forEach((item: string) => {
      const [key, value] = item.split('=');
      if (key && value) {
        result[key] = decodeURIComponent(value);
      }
    });

    if (result.RtnCode !== '300') {
      throw new Error(`Create shipment failed: ${result.RtnMsg}`);
    }

    return {
      allPayLogisticsID: result.AllPayLogisticsID,
      bookingNote: result.BookingNote,
    };
  }
}

// Usage Example
const home = new ECPayHomeLogistics({
  merchantId: '2000132',
  hashKey: '5294y06JbISpM5x9',
  hashIV: 'v77hoKGq4kWxNNIS',
});

const result = await home.createHomeShipment({
  merTradeNo: `HOME${Date.now()}`,
  logisticsSubType: 'TCAT',
  goodsAmount: 1000,
  goodsName: 'Electronics',
  senderName: 'Store Name',
  senderCellPhone: '0912345678',
  senderZipCode: '100',
  senderAddress: 'Taipei City, Zhongzheng Dist., XXX Road',
  receiverName: 'Customer Name',
  receiverCellPhone: '0987654321',
  receiverZipCode: '300',
  receiverAddress: 'Hsinchu City, East Dist., YYY Road',
  temperature: '0001', // Normal
  specification: '0001', // 60cm
  distance: '02', // Cross city
  scheduledDeliveryTime: '4', // No preference
  serverReplyURL: 'https://your-site.com/callback/ecpay-home',
});

console.log('Logistics ID:', result.allPayLogisticsID);
console.log('Booking Note:', result.bookingNote);

export { ECPayHomeLogistics };
```

---

### 4. Query Shipment Status (ECPay)

#### TypeScript Example

```typescript
class ECPayQueryLogistics extends ECPayLogistics {
  /**
   * Query shipment status
   */
  async queryShipment(allPayLogisticsID: string) {
    const data = {
      MerchantID: this.config.merchantId,
      AllPayLogisticsID: allPayLogisticsID,
      TimeStamp: Math.floor(Date.now() / 1000).toString(),
    };

    data['CheckMacValue'] = this.generateCheckMacValue(data);

    const response = await axios.post(
      `${this.baseUrl}/Helper/QueryLogisticsTradeInfo/V2`,
      new URLSearchParams(data),
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      }
    );

    const result: Record<string, string> = {};
    response.data.split('&').forEach((item: string) => {
      const [key, value] = item.split('=');
      if (key && value) {
        result[key] = decodeURIComponent(value);
      }
    });

    return {
      merchantTradeNo: result.MerchantTradeNo,
      goodsAmount: result.GoodsAmount,
      logisticsStatus: result.LogisticsStatus,
      receiverName: result.ReceiverName,
      receiverStoreID: result.ReceiverStoreID,
      updateStatusDate: result.UpdateStatusDate,
    };
  }
}

// Usage Example
const query = new ECPayQueryLogistics({
  merchantId: '2000132',
  hashKey: '5294y06JbISpM5x9',
  hashIV: 'v77hoKGq4kWxNNIS',
});

const status = await query.queryShipment('1718546');

console.log(`Order: ${status.merchantTradeNo}`);
console.log(`Status: ${status.logisticsStatus}`);
console.log(`Store: ${status.receiverStoreID}`);

export { ECPayQueryLogistics };
```

---

## Real-World Scenarios

### Scenario 1: E-commerce Checkout Flow

Complete integration from store selection to shipment creation.

```typescript
class EcommerceLogistics {
  private logistics: NewebPayStoreMap & NewebPayShipment;

  constructor() {
    this.logistics = new (class extends NewebPayStoreMap {})({
      merchantId: process.env.NEWEBPAY_MERCHANT_ID!,
      hashKey: process.env.NEWEBPAY_HASH_KEY!,
      hashIV: process.env.NEWEBPAY_HASH_IV!,
      isProduction: process.env.NODE_ENV === 'production',
    }) as any;
  }

  /**
   * Step 1: Customer selects convenience store
   */
  async showStoreSelection(orderId: string) {
    const html = await this.logistics.queryStoreMap({
      merchantOrderNo: orderId,
      lgsType: 'C2C',
      shipType: '1', // 7-ELEVEN
      returnURL: `https://your-site.com/api/store-selected`,
      extraData: orderId,
    });

    return html;
  }

  /**
   * Step 2: Handle store selection callback
   */
  async handleStoreSelection(encryptData: string, hashData: string) {
    const storeInfo = this.logistics.handleStoreMapCallback(encryptData, hashData);

    // Save store info to order
    await this.saveStoreToOrder(storeInfo.merchantOrderNo, {
      storeID: storeInfo.storeID,
      storeName: storeInfo.storeName,
      storeAddr: storeInfo.storeAddr,
      storeTel: storeInfo.storeTel,
    });

    return storeInfo;
  }

  /**
   * Step 3: Create shipment after payment
   */
  async createShipmentAfterPayment(orderId: string) {
    // Get order details from database
    const order = await this.getOrder(orderId);

    // Create shipment
    const shipment = await (this.logistics as any).createShipment({
      merchantOrderNo: orderId,
      tradeType: 1, // COD
      userName: order.customer.name,
      userTel: order.customer.phone,
      userEmail: order.customer.email,
      storeID: order.logistics.storeID,
      amt: order.total,
      itemDesc: order.items.map((i: any) => i.name).join(', '),
      notifyURL: 'https://your-site.com/api/shipment-status',
      lgsType: 'C2C',
      shipType: '1',
    });

    // Save trade number
    await this.saveTradeNumber(orderId, shipment.tradeNo);

    return shipment;
  }

  /**
   * Step 4: Get shipment number for printing
   */
  async getShipmentNumberForPrinting(orderIds: string[]) {
    const shipmentNums = await (this.logistics as any).getShipmentNumbers(orderIds);

    return shipmentNums.success.map((item: any) => ({
      orderId: item.MerchantOrderNo,
      trackingNo: item.LgsNo,
      printCode: item.StorePrintNo,
    }));
  }

  // Helper methods
  private async saveStoreToOrder(orderId: string, storeInfo: any) {
    // Implementation
  }

  private async getOrder(orderId: string) {
    // Implementation
    return {} as any;
  }

  private async saveTradeNumber(orderId: string, tradeNo: string) {
    // Implementation
  }
}
```

---

### Scenario 2: Batch Shipment Processing

Process multiple orders in batch.

```python
"""Batch Shipment Processing - Python Example"""

from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed


class BatchLogisticsProcessor:
    """Process multiple shipments in batch"""

    def __init__(self, logistics: NewebPayShipment):
        self.logistics = logistics

    def create_shipments_batch(
        self,
        orders: List[Dict[str, any]],
        max_workers: int = 5,
    ) -> Dict[str, any]:
        """Create shipments for multiple orders"""

        results = {
            'success': [],
            'failed': [],
        }

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(
                    self.logistics.create_shipment,
                    **self._prepare_shipment_data(order)
                ): order['order_id']
                for order in orders
            }

            for future in as_completed(futures):
                order_id = futures[future]
                try:
                    result = future.result()
                    results['success'].append({
                        'order_id': order_id,
                        'trade_no': result['trade_no'],
                    })
                except Exception as e:
                    results['failed'].append({
                        'order_id': order_id,
                        'error': str(e),
                    })

        return results

    def get_shipment_numbers_batch(
        self,
        order_ids: List[str],
    ) -> Dict[str, List[Dict]]:
        """Get shipment numbers for multiple orders (max 10 per request)"""

        results = {
            'success': [],
            'failed': [],
        }

        # Split into batches of 10
        for i in range(0, len(order_ids), 10):
            batch = order_ids[i:i+10]

            try:
                result = self.logistics.get_shipment_numbers(batch)
                results['success'].extend(result['success'])
                results['failed'].extend(result['error'])
            except Exception as e:
                results['failed'].extend([
                    {'order_id': order_id, 'error': str(e)}
                    for order_id in batch
                ])

        return results

    def _prepare_shipment_data(self, order: Dict) -> Dict:
        """Prepare shipment data from order"""
        return {
            'merchant_order_no': order['order_id'],
            'trade_type': 1 if order['cod'] else 3,
            'user_name': order['customer']['name'],
            'user_tel': order['customer']['phone'],
            'user_email': order['customer']['email'],
            'store_id': order['logistics']['store_id'],
            'amt': order['total'],
            'item_desc': order['description'],
            'lgs_type': 'C2C',
            'ship_type': '1',
        }


# Usage Example
logistics = NewebPayShipment(
    merchant_id='YOUR_MERCHANT_ID',
    hash_key='YOUR_HASH_KEY',
    hash_iv='YOUR_HASH_IV',
)

processor = BatchLogisticsProcessor(logistics)

# Create shipments for 100 orders
orders = [
    {
        'order_id': f'ORD{i:05d}',
        'cod': True,
        'customer': {
            'name': f'Customer {i}',
            'phone': '0912345678',
            'email': f'customer{i}@example.com',
        },
        'logistics': {
            'store_id': '123456',
        },
        'total': 1000 + i * 10,
        'description': f'Order {i} items',
    }
    for i in range(100)
]

results = processor.create_shipments_batch(orders)

print(f"Success: {len(results['success'])}")
print(f"Failed: {len(results['failed'])}")
```

---

### Scenario 3: Order Modification Workflow

Handle customer requests to change delivery details.

```typescript
class OrderModificationWorkflow {
  private query: NewebPayQueryShipment;
  private modify: NewebPayModifyShipment;
  private storeMap: NewebPayStoreMap;

  constructor() {
    const config = {
      merchantId: process.env.NEWEBPAY_MERCHANT_ID!,
      hashKey: process.env.NEWEBPAY_HASH_KEY!,
      hashIV: process.env.NEWEBPAY_HASH_IV!,
    };

    this.query = new NewebPayQueryShipment(config);
    this.modify = new NewebPayModifyShipment(config);
    this.storeMap = new NewebPayStoreMap(config);
  }

  /**
   * Check if order can be modified
   */
  async canModifyOrder(orderId: string): Promise<boolean> {
    const status = await this.query.queryShipment(orderId);

    // Can only modify if not yet shipped
    const modifiableStatuses = ['0_1', '0_2', '0_3'];
    return modifiableStatuses.includes(status.retId);
  }

  /**
   * Change recipient information
   */
  async changeRecipient(
    orderId: string,
    newRecipient: {
      name: string;
      phone: string;
      email: string;
    }
  ) {
    // Check if can modify
    if (!(await this.canModifyOrder(orderId))) {
      throw new Error('Order cannot be modified at current status');
    }

    // Get current order info
    const current = await this.query.queryShipment(orderId);

    // Modify order
    await this.modify.modifyShipment({
      merchantOrderNo: orderId,
      lgsType: current.lgsType as 'B2C' | 'C2C',
      shipType: current.shipType as '1' | '2' | '3' | '4',
      userName: newRecipient.name,
      userTel: newRecipient.phone,
      userEmail: newRecipient.email,
    });

    return { success: true };
  }

  /**
   * Change pickup store
   */
  async changePickupStore(orderId: string) {
    // Check if can modify
    if (!(await this.canModifyOrder(orderId))) {
      throw new Error('Order cannot be modified at current status');
    }

    // Get current order info
    const current = await this.query.queryShipment(orderId);

    // Show store map for new selection
    const html = await this.storeMap.queryStoreMap({
      merchantOrderNo: orderId,
      lgsType: current.lgsType as 'B2C' | 'C2C',
      shipType: current.shipType as '1' | '2' | '3' | '4',
      returnURL: `https://your-site.com/api/store-changed`,
      extraData: orderId,
    });

    return html;
  }

  /**
   * Handle new store selection
   */
  async handleStoreChange(encryptData: string, hashData: string) {
    const storeInfo = this.storeMap.handleStoreMapCallback(encryptData, hashData);

    // Get current order info
    const current = await this.query.queryShipment(storeInfo.merchantOrderNo);

    // Modify order with new store
    await this.modify.modifyShipment({
      merchantOrderNo: storeInfo.merchantOrderNo,
      lgsType: storeInfo.lgsType as 'B2C' | 'C2C',
      shipType: storeInfo.shipType as '1' | '2' | '3' | '4',
      storeID: storeInfo.storeID,
    });

    // Update database
    await this.updateOrderStore(storeInfo.merchantOrderNo, {
      storeID: storeInfo.storeID,
      storeName: storeInfo.storeName,
      storeAddr: storeInfo.storeAddr,
      storeTel: storeInfo.storeTel,
    });

    return storeInfo;
  }

  private async updateOrderStore(orderId: string, storeInfo: any) {
    // Implementation
  }
}
```

---

## Error Handling

### Comprehensive Error Handler

```typescript
class LogisticsError extends Error {
  constructor(
    public code: string,
    public message: string,
    public originalError?: any
  ) {
    super(message);
    this.name = 'LogisticsError';
  }
}

class LogisticsErrorHandler {
  /**
   * Error code mapping
   */
  private static errorMessages: Record<string, string> = {
    '1101': 'Failed to create logistics order',
    '1102': 'Merchant not found',
    '1103': 'Duplicate merchant order number',
    '1104': 'Logistics service not enabled',
    '1105': 'Store information invalid or empty',
    '1106': 'IP not allowed',
    '1107': 'Payment order not found',
    '1108': 'System error, cannot query logistics order',
    '1109': 'Logistics order not found',
    '1110': 'System error, cannot modify logistics order',
    '1111': 'Order status cannot be modified',
    '1112': 'Failed to modify logistics order',
    '1113': 'System error, cannot query tracking history',
    '1114': 'Insufficient prepaid balance',
    '1115': 'Failed to get shipment number',
    '1116': 'Shipment already created for this transaction',
    '2100': 'Data format error',
    '2101': 'Version error',
    '2102': 'UID_ cannot be empty',
    '2103': 'COD amount limit: 20000 NTD',
    '2104': 'No payment amount limit: 20000 NTD',
    '2105': 'Max 10 shipment numbers per request',
    '2106': 'Max labels exceeded for this provider',
    '4101': 'IP restricted',
    '4103': 'HashData_ verification failed',
    '4104': 'Encryption error, check Hash_Key and Hash_IV',
  };

  /**
   * Handle API error
   */
  static handleError(errorCode: string, originalError?: any): LogisticsError {
    const message = this.errorMessages[errorCode] || 'Unknown error';
    return new LogisticsError(errorCode, message, originalError);
  }

  /**
   * Retry logic for transient errors
   */
  static async withRetry<T>(
    fn: () => Promise<T>,
    maxRetries: number = 3,
    delay: number = 1000
  ): Promise<T> {
    let lastError: any;

    for (let i = 0; i < maxRetries; i++) {
      try {
        return await fn();
      } catch (error: any) {
        lastError = error;

        // Don't retry for non-transient errors
        if (this.isNonTransientError(error.code)) {
          throw error;
        }

        // Wait before retry
        if (i < maxRetries - 1) {
          await new Promise((resolve) => setTimeout(resolve, delay * (i + 1)));
        }
      }
    }

    throw lastError;
  }

  /**
   * Check if error is non-transient
   */
  private static isNonTransientError(code: string): boolean {
    const nonTransientErrors = [
      '1102', // Merchant not found
      '1103', // Duplicate order number
      '1104', // Service not enabled
      '1106', // IP not allowed
      '2100', // Data format error
      '2101', // Version error
      '2102', // UID_ empty
      '2103', // Amount limit exceeded
      '2104', // Amount limit exceeded
      '2105', // Batch limit exceeded
      '2106', // Batch limit exceeded
      '4101', // IP restricted
      '4103', // Hash verification failed
      '4104', // Encryption error
    ];

    return nonTransientErrors.includes(code);
  }
}

// Usage Example
try {
  const result = await LogisticsErrorHandler.withRetry(async () => {
    return await logistics.createShipment({
      /* ... */
    });
  });
} catch (error) {
  if (error instanceof LogisticsError) {
    console.error(`Logistics Error [${error.code}]: ${error.message}`);

    // Handle specific errors
    switch (error.code) {
      case '1103':
        // Duplicate order - use different order number
        break;
      case '2103':
        // Amount too high - split into multiple shipments
        break;
      case '4103':
        // Hash failed - check credentials
        break;
      default:
        // Generic error handling
        break;
    }
  }
}
```

---

**Total Lines**: 1400+

This comprehensive guide covers all major NewebPay Logistics integration scenarios with production-ready code examples.

---

## SmilePay 速買配物流範例

SmilePay 透過 `Pay_zg` 矩陣編碼涵蓋 7-11/全家 + 黑貓三大配送：

| Pay_zg | 用途 |
|---|---|
| 51 / 52 | C2C COD / PICKUP |
| 55 / 56 | B2C COD / PICKUP |
| 81 / 82 | TCAT 黑貓 COD / PICKUP |
| 83 | TCAT 逆物流 |

完整範例見 [`examples/smilepay-logistics-cvs-example.py`](examples/smilepay-logistics-cvs-example.py)。

### 三大要點

1. **Pay_subzg**：`7NET` 對應 7-11、`FAMI` 對應全家。
2. **回應是 XML**：用 `xml.etree.ElementTree` parse；常用欄位 `Status` / `PaymentNo` / `Smseid` / `Storeid`。
3. **電子地圖選店**：先導轉到 `LogisticsEmap.asp`，客戶選完門市後 SmilePay 會 redirect 回 RtURL 並帶 storeid/storename。

---

## PChomePay 拍錢包物流範例

⚠️ Notify IP 必加白名單：**`113.196.231.190`**。

完整範例見 [`examples/pchomepay-logistics-cvs-example.py`](examples/pchomepay-logistics-cvs-example.py)。涵蓋：
- 取號列印交寄單 (`/v1/logistic/batch`)
- 物流歷程查詢 (`/v1/logistic/query/{order_id}/history`)
- 對帳資料 NDJSON 解析 (`/v1/logistic/accounting/{date}`)
- 賠款入帳查詢 (`/v1/logistic/compensation/{date}`)

### 三大要點

1. **兩段式認證**：先用 Basic Auth 取 `pcpay-token`（8 小時 TTL），後續 API 帶 token header。
2. **對帳資料是 NDJSON**：每行一個獨立 JSON 物件，須逐行 parse；不是標準 JSON array。
3. **沙箱依金額尾數模擬情境**：例 ATM 金額尾數 `0-7` 自動付款成功、`8` 過期、`9` 5 分鐘後過期。

---

## PayNow 立吉富物流範例

⚠️ **加密用 3DES (TripleDES) / ECB / Zero-Padding**，24-byte Key + 8-byte IV。**不同於金流端的動態 AES-256**。

完整範例見 [`examples/paynow-logistics-cvs-example.py`](examples/paynow-logistics-cvs-example.py)。涵蓋 11 條產品線（7-11 大宗 / 冷凍 / 海外、全家 大宗 / 冷凍、4 大超商常溫 C2C、黑貓宅配 / 店到店）。

### 四大要點

1. **3DES 不要用 AES**：物流端跟金流端是兩套不同加密；混用會直接失敗。
2. **ServiceID 對應產品線**：`20=7-11 大宗 B2C` `40=4 大超商常溫 C2C` `50=黑貓宅配` 等。
3. **海外配送限 7-11**：透過 `7-11 over-sea` 產品線寄送；其他超商不支援海外。
4. **Webhook 簽章機制官方未明示**：建議自行驗證 LogisticTradeNo + 商家代號比對。

---

## HCT 新竹物流（直連 carrier API）範例

⚠️ **先確認你需要的是直連還是 aggregator**：
- **透過 ECPay/PayNow/SmilePay** 走 HCT 配送 → 用 aggregator 的 `LogisticsType=HCT`，不需要本範例
- **直接打 HCT 自家系統**（大量出貨、自備站所對接）→ 用本範例，需向 HCT 申請

完整範例見 [`examples/hct-logistics-example.py`](examples/hct-logistics-example.py)。

### 四大要點

1. **加密演算法申請後才提供**：HCT 給的是 C# Sample Code，需自行轉譯。範例的 `_encrypt()` 是 placeholder，串接前必填。
2. **`TransReport` 必須當日 18:00 前呼叫**：否則無法列印託運單，包裹無法配送。
3. **JSON / XML / DataSet 三種變體**：建議用 JSON 變體，避開 .NET DataSet 跨語言難題。
4. **逆物流只有 JSON**：`R_TransData` 沒有 XML 或 DataSet 版本。

## ezShip 台灣便利配範例

### 完整 Python 範例
請見 [`examples/ezship-logistics-example.py`](examples/ezship-logistics-example.py) — 涵蓋電子地圖、傳送訂單、貨況查詢三步驟，並內建自我驗證。

### ⚠️ 兩個跨端點的不一致

1. **參數命名風格不同**：電子地圖用 camelCase（`suID` / `rtURL` / `webPara`），傳送訂單與貨況查詢用 snake_case（`su_id` / `rtn_url` / `web_para`）。同一次串接要寫兩種。
2. **編碼方向不對稱**：以 URL 方式送出時中文需 **BIG5** 編碼，但 ezShip **回傳一律 UTF-8**。官方建議優先用 FORM SUBMIT 可避開這問題。

### ⚠️ 建單失敗的唯一訊號是 `sn_id` 八個零

沒有獨立的錯誤碼欄位。`sn_id` 回 `00000000` 即失敗；非八個零即成功，且**必須把 `sn_id` 存起來**，後續寄件與追蹤貨況都靠它。

### 三個會被打回或被停權的點

| 限制 | 後果 |
|---|---|
| `rv_name` 超過四個中英文字 | 超商取貨單印不完整，可能無法取貨 |
| 貨況查詢間隔 < 3 秒 | 官方明文將「**中斷其網路串接之權利**」 |
| 電子地圖嵌入 iframe 或 CSS | 官方明文禁止 |

### 通路與涵蓋

- **不含 7-ELEVEN**：只有 OK（`TOK`）、萊爾富（`TLF`）、全家（`TFM`）。客群以 7-11 為主者，ezShip 不能單獨滿足需求。
- **支援店港澳**：`order_status` 的 `A11` / `A12` 是香港與澳門店配。
- 代收服務（取貨付款／貨到付款）需 ezShip **商務會員**資格。

### 門市代碼

可能四碼或五碼（如 `TFM9771`），且**與門市服務代號不一定相同**。直接把 ezShip 給的值原封回傳即可，不要自行轉換。

---

**更多範例持續更新中...**
