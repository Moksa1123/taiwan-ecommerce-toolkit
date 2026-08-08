#!/usr/bin/env python3
"""
驗證三個 skill 的 CSV 資料檔完整性。

這幾項檢查都是實際踩過的坑：

1. 欄位數對齊 —— 最常見的錯誤是 notes 或 solution 欄內含未加引號的逗號
   （例如 "小於 1,000,000,000,000"），CSV 解析後整列欄位往後位移，
   讀到的 min_amount、fee_type 全是錯的，而程式不會報錯。

2. 重複主鍵 —— providers.csv 的 provider、error-codes.csv 的
   (provider, code) 重複時，後載入的會靜默覆蓋前者。

3. 空白必填欄 —— provider 或 code 為空的列等同垃圾資料。

用法:
    python scripts/validate-data.py
"""

import csv
import glob
import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 檔案 -> 應唯一的欄位組合
UNIQUE_KEYS = {
    'providers.csv': ('provider',),
    'error-codes.csv': ('provider', 'code'),
    'payment-methods.csv': ('method_code',),
    'logistics-types.csv': ('type_code', 'provider'),
}

# 檔案 -> 不可為空的欄位
REQUIRED = {
    'providers.csv': ('provider',),
    'error-codes.csv': ('provider', 'code'),
}


def check_file(path):
    """回傳這個檔案的問題清單"""
    rel = os.path.relpath(path, ROOT).replace('\\', '/')
    name = os.path.basename(path)
    problems = []

    with open(path, encoding='utf-8') as f:
        rows = list(csv.reader(f))

    if not rows:
        return [f'{rel}: 檔案為空']

    header = rows[0]
    width = len(header)

    # 1. 欄位數對齊
    for i, row in enumerate(rows[1:], start=2):
        if not row:
            continue
        if len(row) != width:
            problems.append(
                f'{rel}:{i} 欄位數 {len(row)}，應為 {width}'
                '（多半是欄位內有未加引號的逗號）'
            )

    # 只有欄位數正確才值得往下檢查
    if problems:
        return problems

    dict_rows = [dict(zip(header, r)) for r in rows[1:] if r]

    # 2. 重複主鍵
    keys = UNIQUE_KEYS.get(name)
    if keys and all(k in header for k in keys):
        seen = Counter(tuple(r.get(k, '') for k in keys) for r in dict_rows)
        for key, count in seen.items():
            if count > 1:
                problems.append(f'{rel}: {"+".join(keys)} = {key} 重複 {count} 次')

    # 3. 空白必填欄
    for col in REQUIRED.get(name, ()):
        if col not in header:
            continue
        for i, r in enumerate(dict_rows, start=2):
            if not r.get(col, '').strip():
                problems.append(f'{rel}:{i} 欄位 {col} 不可為空')

    return problems


def main():
    paths = sorted(glob.glob(os.path.join(ROOT, 'taiwan-*', 'data', '*.csv')))
    if not paths:
        print('找不到任何 data/*.csv', file=sys.stderr)
        return 1

    all_problems = []
    for path in paths:
        problems = check_file(path)
        rel = os.path.relpath(path, ROOT).replace('\\', '/')
        status = 'OK' if not problems else f'{len(problems)} 個問題'
        print(f'  {rel:<48} {status}')
        all_problems.extend(problems)

    print()
    if all_problems:
        print(f'[FAIL] 共 {len(all_problems)} 個問題：')
        for p in all_problems:
            print(f'   {p}')
        return 1

    print(f'[DONE] {len(paths)} 份 CSV 全數通過')
    return 0


if __name__ == '__main__':
    sys.exit(main())
