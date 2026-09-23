#!/usr/bin/env python3
"""
ECPay 超商取貨範例
示範如何使用 ECPay 物流 API 建立、查詢、列印超商取貨（C2C）訂單，以及驗證物流狀態通知

依據（皆已對照原始碼 / 官方文件）:
- CheckMacValue：綠界官方 PHP SDK ecpay/sdk 1.3.2408190 CheckMacValueService / UrlService，
  由官方 WooCommerce 外掛 ecpay-ecommerce-for-woocommerce 1.1.2603230 內附；
  外掛所有物流呼叫皆以 hashMethod=md5 建立
- 參數與端點：同外掛 ecpay-logistic-helper.php / class-wooecpay-order.php，
  以及綠界官方 ecpay-api-skill guides/06-logistics-domestic.md

國內物流的 CheckMacValue 是 MD5，金流 AIO 才是 SHA256。
"""

import hashlib
import hmac
import urllib.parse
from datetime import datetime


def ecpay_url_encode(text: str) -> str:
    """
    綠界 CheckMacValue 專用的 URL encode（對應 SDK UrlService::ecpayUrlEncode）

    PHP urlencode → 轉小寫 → 把 %2d %5f %2e %21 %2a %28 %29 還原成 - _ . ! * ( )
    （.NET 的 UrlEncode 不編碼這幾個字元，綠界以 .NET 規則驗證）。

    直接用 Python 的 quote_plus 會有兩處不同：
    - quote_plus 會把 ! * ( ) 編碼，綠界不會 → 商品名稱含括號就驗證失敗
    - quote_plus 保留 ~，PHP 會編成 %7e
    """
    encoded = urllib.parse.quote_plus(text, safe='').replace('~', '%7E').lower()
    for src, dst in (('%2d', '-'), ('%5f', '_'), ('%2e', '.'), ('%21', '!'),
                     ('%2a', '*'), ('%28', '('), ('%29', ')')):
        encoded = encoded.replace(src, dst)
    return encoded


class ECPayLogistics:
    """ECPay 物流 API 封裝"""

    TEST_BASE_URL = "https://logistics-stage.ecpay.com.tw"
    PROD_BASE_URL = "https://logistics.ecpay.com.tw"

    # C2C 列印託運單端點依超商不同
    PRINT_C2C_PATHS = {
        "UNIMARTC2C": "/Express/PrintUniMartC2COrderInfo",
        "FAMIC2C": "/Express/PrintFAMIC2COrderInfo",
        "HILIFEC2C": "/Express/PrintHILIFEC2COrderInfo",
        "OKMARTC2C": "/Express/PrintOKMARTC2COrderInfo",
    }

    def __init__(self, merchant_id, hash_key, hash_iv, test_mode=True):
        self.merchant_id = merchant_id
        self.hash_key = hash_key
        self.hash_iv = hash_iv
        self.api_url = self.TEST_BASE_URL if test_mode else self.PROD_BASE_URL

    def create_check_mac_value(self, params):
        """
        產生 CheckMacValue（MD5，與官方 SDK CheckMacValueService 相同）

        1. 排除 CheckMacValue 本身
        2. 依參數名稱排序，不分大小寫（SDK 用 strcasecmp；Python 預設 sorted 會區分大小寫，
           例如 CVSPaymentNo 與 CollectionAmount 的先後就會不同）
        3. 組成 HashKey=...&k=v&...&HashIV=...
        4. ecpay_url_encode
        5. MD5 → 轉大寫
        """
        items = sorted(
            ((k, v) for k, v in params.items() if k != "CheckMacValue"),
            key=lambda kv: kv[0].lower(),
        )
        param_str = "&".join(f"{k}={v}" for k, v in items)
        raw_str = f"HashKey={self.hash_key}&{param_str}&HashIV={self.hash_iv}"
        return hashlib.md5(ecpay_url_encode(raw_str).encode("utf-8")).hexdigest().upper()

    def verify_check_mac_value(self, params):
        """驗證綠界 POST 過來的資料（ServerReplyURL 物流狀態通知、Create 回應等）"""
        received = params.get("CheckMacValue", "")
        if not received:
            return False
        return hmac.compare_digest(self.create_check_mac_value(params), received.upper())

    def create_cvs_order(self, order_id, goods_name, goods_amount, receiver_name,
                         receiver_phone, receiver_store_id, logistics_sub_type="UNIMARTC2C"):
        """
        建立超商取貨訂單（POST /Express/Create）

        回傳 (url, params)。Temperature / Distance / Specification 是「宅配」專用欄位，
        超商取貨不需要帶。
        """
        params = {
            "MerchantID": self.merchant_id,
            "MerchantTradeNo": order_id,
            "MerchantTradeDate": datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
            "LogisticsType": "CVS",
            "LogisticsSubType": logistics_sub_type,  # UNIMARTC2C, FAMIC2C, HILIFEC2C, OKMARTC2C
            "GoodsAmount": goods_amount,
            "GoodsName": goods_name,
            "SenderName": "測試商家",
            "SenderCellPhone": "0912345678",
            "ReceiverName": receiver_name,
            "ReceiverCellPhone": receiver_phone,
            "ReceiverStoreID": receiver_store_id,
            "ServerReplyURL": "https://yourdomain.com/logistics/callback",
            "IsCollection": "N",  # 是否代收貨款
        }
        params["CheckMacValue"] = self.create_check_mac_value(params)
        return f"{self.api_url}/Express/Create", params

    def query_order(self, logistics_id):
        """
        查詢物流訂單

        綠界官方 guides/06 端點表列為 /Helper/QueryLogisticsTradeInfo/V5；
        SDK 內附範例仍使用 /V2。
        """
        params = {
            "MerchantID": self.merchant_id,
            "AllPayLogisticsID": logistics_id,
            "TimeStamp": str(int(datetime.now().timestamp())),
        }
        params["CheckMacValue"] = self.create_check_mac_value(params)
        return f"{self.api_url}/Helper/QueryLogisticsTradeInfo/V5", params

    def print_order(self, logistics_id, logistics_sub_type, cvs_payment_no, cvs_validation_no=""):
        """
        列印 C2C 託運單（以表單 POST 開新視窗）

        欄位與官方外掛一致：7-ELEVEN 需 CVSPaymentNo + CVSValidationNo；
        全家 / 萊爾富 / OK 只需 CVSPaymentNo。兩者皆為建立訂單時綠界回傳的值。
        """
        if logistics_sub_type not in self.PRINT_C2C_PATHS:
            raise ValueError(f"不支援的 C2C 物流子類型: {logistics_sub_type}")
        params = {
            "MerchantID": self.merchant_id,
            "AllPayLogisticsID": logistics_id,
            "CVSPaymentNo": cvs_payment_no,
        }
        if logistics_sub_type == "UNIMARTC2C":
            if not cvs_validation_no:
                raise ValueError("7-ELEVEN C2C 列印需要 CVSValidationNo")
            params["CVSValidationNo"] = cvs_validation_no
        params["CheckMacValue"] = self.create_check_mac_value(params)
        return f"{self.api_url}{self.PRINT_C2C_PATHS[logistics_sub_type]}", params


def _test_client():
    return ECPayLogistics(
        merchant_id="2000132",          # 測試商店代號
        hash_key="5294y06JbISpM5x9",    # 測試 HashKey
        hash_iv="v77hoKGq4kWxNNIS",     # 測試 HashIV
        test_mode=True,
    )


def _show(title, url, params):
    print(f"{title}: POST {url}")
    for key, value in params.items():
        print(f"  {key}: {value}")


def example_create_order():
    """範例1: 建立超商取貨訂單"""
    print("\n=== 範例1: 建立超商取貨訂單 ===\n")
    url, params = _test_client().create_cvs_order(
        order_id=f"ORDER{int(datetime.now().timestamp())}",
        goods_name="測試商品(A)",       # 括號會觸發 .NET URL encode 規則，是常見的驗證失敗來源
        goods_amount=100,
        receiver_name="王小明",
        receiver_phone="0912345678",
        receiver_store_id="991182",     # 7-11 門市代號
        logistics_sub_type="UNIMARTC2C",
    )
    _show("訂單參數", url, params)


def example_query_order():
    """範例2: 查詢物流訂單"""
    print("\n=== 範例2: 查詢物流訂單 ===\n")
    url, params = _test_client().query_order("10001234567")
    _show("查詢參數", url, params)


def example_print_order():
    """範例3: 列印 7-ELEVEN C2C 託運單"""
    print("\n=== 範例3: 列印託運單 ===\n")
    url, params = _test_client().print_order(
        "10001234567", "UNIMARTC2C", cvs_payment_no="F0012345", cvs_validation_no="1234")
    _show("列印參數", url, params)


def example_verify_callback():
    """範例4: 驗證 ServerReplyURL 物流狀態通知，成功後回應純文字 1|OK"""
    print("\n=== 範例4: 驗證物流狀態通知 ===\n")
    client = _test_client()
    posted = {
        "MerchantID": "2000132", "MerchantTradeNo": "ORDER1758600000",
        "RtnCode": "300", "RtnMsg": "訂單處理中(已收到訂單資料)",
        "AllPayLogisticsID": "10001234567", "LogisticsType": "CVS",
        "LogisticsSubType": "UNIMARTC2C", "GoodsAmount": "100",
        "UpdateStatusDate": "2026/09/23 12:00:00",
        "CVSPaymentNo": "F0012345", "CVSValidationNo": "1234",
    }
    posted["CheckMacValue"] = client.create_check_mac_value(posted)  # 模擬綠界送來的值
    print("驗證結果:", "通過，回應 1|OK" if client.verify_check_mac_value(posted) else "失敗，不回應 1|OK")


if __name__ == "__main__":
    print("ECPay 物流 API 範例")
    print("=" * 50)

    example_create_order()
    example_query_order()
    example_print_order()
    example_verify_callback()

    print("\n" + "=" * 50)
    print("範例執行完成")
