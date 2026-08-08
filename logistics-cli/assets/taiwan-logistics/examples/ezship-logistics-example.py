#!/usr/bin/env python3
"""
ezShip 台灣便利配 物流 Python 範例（參數版）

依照 taiwan-logistics-skill 規範撰寫。

ezShip 是本 skill 收錄的**唯一非金流商的超商取貨聚合商**——
對「只要物流不要金流」的商家，不必為了超取去開一個金流帳號。

⚠️ 通路只有 OK、萊爾富、全家，**不含 7-ELEVEN**。
若客群以 7-11 為主，ezShip 不能單獨滿足需求。

流程三步：電子地圖 -> 傳送訂單 -> 貨況查詢

⚠️ 兩個跨端點的不一致，實作前務必知道：
  1. 參數命名風格不同 —— 電子地圖是 camelCase（suID/rtURL/webPara），
     傳送訂單與貨況查詢是 snake_case（su_id/rtn_url/web_para）
  2. 編碼方向不對稱 —— 以 URL 方式送出時中文需 BIG5 編碼，
     但 ezShip 回傳一律 UTF-8

API 文件: 參見 references/ezship-logistics-api.md

依賴:
    pip install requests

直接執行本檔會跑內建驗證，不會發出任何網路請求:
    python ezship-logistics-example.py
"""

import urllib.parse
from dataclasses import dataclass
from typing import Dict, Optional

import requests


MAP_URL = 'https://map.ezship.com.tw/ezship_map_web.jsp'
# 舊端點（無 _ex）已於 2017 年底停用
ORDER_URL = 'https://www.ezship.com.tw/emap/ezship_request_order_api_ex.jsp'
STATUS_BY_SN_URL = 'https://www.ezship.com.tw/emap/ezship_request_order_status_api.jsp'
STATUS_BY_ORDER_URL = 'https://www.ezship.com.tw/emap/ezship_request_order_status_api_byorder.jsp'

# 建單失敗的唯一訊號 —— 沒有獨立的錯誤碼欄位
SN_ID_FAILED = '00000000'

# 電子地圖回傳的通路代號
STORE_CHANNELS = {
    'TOK': 'OK 便利商店',
    'TLF': '萊爾富',
    'TFM': '全家',
}

# order_status 分組
ORDER_STATUS_GROUPS = {
    'cvs':   ['A01', 'A02', 'A03', 'A04'],   # 超商取貨，須帶 st_code
    'home':  ['A05', 'A06'],                 # 宅配，須帶 rv_addr + rv_zip
    'hk_mo': ['A11', 'A12'],                 # 店港澳，須帶 st_code
}

# 貨況查詢的 times 欄位
DELIVERY_TIMES = {
    '1': '第一次配送',
    '2': '第二次配送',
    '8': '退還給寄件人',
    '9': '非常規配送',
}

# 這兩個狀態無法呈現最終貨況，需登入 ezShip 系統查詢
NEEDS_MANUAL_CHECK = {'S05': '包裹退貨', 'S06': '包裹配送異常'}


# ============================================================================
# 編碼
# ============================================================================

def encode_big5_params(params: Dict[str, str]) -> str:
    """以 URL 方式傳遞時，中文需以 **BIG5** 字集做 URL 編碼。

    ⚠️ 這是送出方向。ezShip **回傳一律 UTF-8**，兩邊不對稱。
    ⚠️ 官方建議優先用 FORM SUBMIT（方式一）而非 URL 傳參，
    可避開這個編碼問題；本函式供必須用 URL 時使用。
    """
    parts = []
    for k, v in params.items():
        parts.append(f'{k}={urllib.parse.quote(str(v).encode("big5"), safe="")}')
    return '&'.join(parts)


def check_no_special_chars(value: str, field_name: str) -> None:
    """web_para / webPara 不可含特殊字元（官方明列）。"""
    for ch in "':@%&*$\"":
        if ch in value:
            raise ValueError(f'{field_name} 不可包含特殊字元 {ch!r}')


# ============================================================================
# 步驟一：電子地圖（只有超商取貨需要）
# ============================================================================

def build_map_form(su_id: str, process_id: str, rt_url: str, web_para: str = '') -> Dict[str, str]:
    """組出導向 ezShip 電子地圖的表單欄位。

    ⚠️ 這一支用 **camelCase**（suID / rtURL / webPara），
    與後續兩支的 snake_case 不同。

    ⚠️ 官方明文**禁止把電子地圖嵌入 iframe 或以 CSS 內嵌**。
    """
    if web_para:
        check_no_special_chars(web_para, 'webPara')
    return {
        'suID': su_id,
        'processID': process_id,
        'stCate': '',
        'stCode': '',
        'rtURL': rt_url,
        'webPara': web_para,
    }


def parse_map_result(query: Dict[str, str]) -> Dict[str, str]:
    """解析電子地圖導回的參數（UTF-8）。

    ⚠️ 門市代碼可能四碼或五碼（如 TFM9771），
    且**與門市服務代號不一定相同**。
    直接把 ezShip 給的值原封回傳即可，不要自行轉換。
    """
    return {
        'process_id': query.get('processID', ''),
        'st_cate': query.get('stCate', ''),
        'st_cate_name': STORE_CHANNELS.get(query.get('stCate', ''), '未知通路'),
        'st_code': query.get('stCode', ''),
        'st_name': query.get('stName', ''),
        'st_addr': query.get('stAddr', ''),
        'st_tel': query.get('stTel', ''),
        'web_para': query.get('webPara', ''),
    }


# ============================================================================
# 步驟二：傳送訂單
# ============================================================================

@dataclass
class EzshipConfig:
    su_id: str              # 賣家 ezShip 帳號，需開通網站串接
    rtn_url: str            # 回傳網址


def build_order_form(
    config: EzshipConfig,
    order_id: str,
    order_status: str,
    order_type: str,
    order_amount: int,
    rv_name: str,
    rv_mobile: str,
    *,
    rv_email: str = '',
    st_code: str = '',
    rv_addr: str = '',
    rv_zip: str = '',
    web_para: str = '',
) -> Dict[str, str]:
    """組出建單表單。

    order_status: A01-A04 超商取貨 / A05-A06 宅配 / A11-A12 店港澳
    order_type:   1 代收（取貨付款/貨到付款）/ 3 一般配送

    ⚠️ 代收服務需 ezShip **商務會員**資格且在合約期間內，
    一般會員只能做「取貨不付款／純配送」。
    """
    validate_order(order_status, st_code, rv_addr, rv_zip, rv_name)
    if order_type not in ('1', '3'):
        raise ValueError('order_type 只能是 1（代收）或 3（一般配送）')
    if web_para:
        check_no_special_chars(web_para, 'web_para')

    return {
        'su_id': config.su_id,
        'order_id': order_id,
        'order_status': order_status,
        'order_type': order_type,
        'order_amount': str(order_amount),
        'rv_name': rv_name,
        'rv_email': rv_email,
        'rv_mobile': rv_mobile,
        'st_code': st_code,
        'rv_addr': rv_addr,
        'rv_zip': rv_zip,
        'rtn_url': config.rtn_url,
        'web_para': web_para,
    }


def validate_order(order_status: str, st_code: str, rv_addr: str, rv_zip: str, rv_name: str) -> None:
    """依 order_status 檢查必填欄位。"""
    if order_status in ORDER_STATUS_GROUPS['cvs'] + ORDER_STATUS_GROUPS['hk_mo']:
        if not st_code:
            raise ValueError(f'{order_status} 為門市取貨，st_code 必填')
    elif order_status in ORDER_STATUS_GROUPS['home']:
        if not rv_addr or not rv_zip:
            raise ValueError(f'{order_status} 為宅配，rv_addr 與 rv_zip 皆必填')
    else:
        raise ValueError(f'未知的 order_status: {order_status}')

    # ⚠️ 超商取貨單的姓名欄位長度有限，超過四個中英文字會印不完整，
    # 可能造成取貨問題。官方特別提醒。
    if len(rv_name) > 4:
        raise ValueError(
            f'rv_name「{rv_name}」超過四個字，超商取貨單會印不完整而可能無法取貨'
        )


def parse_order_result(query: Dict[str, str]) -> Dict[str, str]:
    """解析建單導回的參數。

    ⚠️ **sn_id 回傳八個零代表建單失敗**——這是唯一的失敗訊號，
    沒有獨立的錯誤碼欄位。非八個零即成功，
    且**必須把 sn_id 存起來**，後續寄件與追蹤貨況都靠它。
    """
    sn_id = query.get('sn_id', '')
    return {
        'order_id': query.get('order_id', ''),
        'sn_id': sn_id,
        'order_status': query.get('order_status', ''),
        'web_para': query.get('webPara', ''),
        'success': sn_id != '' and sn_id != SN_ID_FAILED,
    }


# ============================================================================
# 步驟三：貨況查詢
# ============================================================================

MIN_QUERY_INTERVAL_SECONDS = 3
"""⚠️ 官方明文：大量反覆查詢結案資料導致系統忙碌者，
ezShip 將「中斷其網路串接之權利」。建議每筆查詢間隔 3 秒以上，
已結案貨件勿重複查詢，也不要做整批預先輪詢。"""


def build_status_form(config: EzshipConfig, order_no: str, web_para: str = '') -> Dict[str, str]:
    """依購物網站訂單編號查詢貨況。

    ⚠️ 此查法**不適用簡易版**串接的訂單。
    ⚠️ 訂單號碼重複時，以**最後一次上傳**的訂單資料為主。
    """
    if web_para:
        check_no_special_chars(web_para, 'web_para')
    return {
        'su_id': config.su_id,
        'order_no': order_no,
        'rtn_url': config.rtn_url,
        'web_para': web_para,
    }


def parse_status_result(query: Dict[str, str]) -> Dict[str, str]:
    """解析貨況回傳。"""
    status = query.get('order_status', '')
    times = query.get('times', '')
    return {
        'sn_id': query.get('sn_id', ''),
        'order_no': query.get('order_no', ''),
        'order_status': status,
        'times': times,
        'times_desc': DELIVERY_TIMES.get(times, f'未知 {times}'),
        # sdate 由超商或宅配公司提供；udate 是 ezShip 收到該狀態的時間
        'sdate': query.get('sdate', ''),
        'udate': query.get('udate', ''),
        'needs_manual_check': status in NEEDS_MANUAL_CHECK,
        'manual_check_reason': NEEDS_MANUAL_CHECK.get(status, ''),
    }


# ============================================================================
# 自我驗證
# ============================================================================

def _self_test() -> int:
    """驗證編碼與欄位規則。ezShip 官方未提供簽章測試向量
    （參數版沒有簽章機制，安全性倚賴 su_id 帳號綁定與 HTTPS）。"""
    failed = 0
    print('ezShip 實作驗證')

    # BIG5 編碼：中文與 UTF-8 的結果不同
    big5 = encode_big5_params({'rv_name': '王小明'})
    utf8 = f"rv_name={urllib.parse.quote('王小明', safe='')}"
    ok = big5 != utf8 and 'rv_name=' in big5
    failed += not ok
    print(f'  [{"PASS" if ok else "FAIL"}] BIG5 編碼與 UTF-8 結果不同')
    print(f'         BIG5 {big5}')
    print(f'         UTF8 {utf8}')

    # 建單失敗訊號
    ok = parse_order_result({'sn_id': SN_ID_FAILED})['success'] is False
    failed += not ok
    print(f'  [{"PASS" if ok else "FAIL"}] sn_id 八個零判定為建單失敗')

    ok = parse_order_result({'sn_id': 'SN12345678'})['success'] is True
    failed += not ok
    print(f'  [{"PASS" if ok else "FAIL"}] sn_id 非八個零判定為成功')

    # 必填欄位規則
    cases = [
        ('A01 缺 st_code', dict(order_status='A01', st_code='', rv_addr='', rv_zip='', rv_name='王小明')),
        ('A05 缺 rv_zip', dict(order_status='A05', st_code='', rv_addr='台北市', rv_zip='', rv_name='王小明')),
        ('姓名超過四字', dict(order_status='A01', st_code='TFM9771', rv_addr='', rv_zip='', rv_name='王小明先生')),
    ]
    for label, kw in cases:
        try:
            validate_order(**kw)
            print(f'  [FAIL] 應攔下：{label}')
            failed += 1
        except ValueError:
            print(f'  [PASS] 正確攔下：{label}')

    # 港澳
    ok = 'A11' in ORDER_STATUS_GROUPS['hk_mo']
    failed += not ok
    print(f'  [{"PASS" if ok else "FAIL"}] A11/A12 歸類為店港澳（ezShip 支援港澳店配）')

    # 特殊字元
    try:
        check_no_special_chars("order'123", 'web_para')
        print('  [FAIL] 應攔下 web_para 的特殊字元')
        failed += 1
    except ValueError:
        print('  [PASS] 正確攔下 web_para 的特殊字元')

    print()
    print('全部通過' if failed == 0 else f'{failed} 項失敗')
    return 1 if failed else 0


if __name__ == '__main__':
    raise SystemExit(_self_test())
