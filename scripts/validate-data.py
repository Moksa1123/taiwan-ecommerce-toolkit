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

4. 檔案大小 —— Claude 外掛目錄對圖片以外的單檔上限 256 KiB，超過會被扣留人工審查；
   大表依 TABLE_PARTS 拆成多檔（如 error-codes*.csv），主鍵唯一性跨檔檢查。

用法:
    python scripts/validate-data.py
"""

import csv
import glob
import os
import re
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 檔案 -> 應唯一的欄位組合
UNIQUE_KEYS = {
    'providers.csv': ('provider',),
    'error-codes.csv': ('provider', 'code'),
    'payment-methods.csv': ('method_code',),
    'logistics-types.csv': ('provider', 'logistics_sub_type'),
}

# 檔案 -> 不可為空的欄位
REQUIRED = {
    'providers.csv': ('provider',),
    'error-codes.csv': ('provider', 'code'),
}

# 拆成多檔的表：error-codes-tappay.csv、error-codes-payuni-1.csv 等都屬 error-codes.csv
TABLE_PARTS = re.compile(r'^(error-codes)(-[a-z0-9-]+)?\.csv$')

# Claude 外掛目錄：圖片與字型以外的單檔上限
MAX_FILE_BYTES = 256 * 1024
BINARY_OK = ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.woff', '.woff2', '.ttf', '.otf')


def table_of(name):
    m = TABLE_PARTS.match(name)
    return m.group(1) + '.csv' if m else name


def check_file(path):
    """回傳這個檔案的問題清單"""
    rel = os.path.relpath(path, ROOT).replace('\\', '/')
    name = table_of(os.path.basename(path))
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
    missing = [k for k in keys or () if k not in header]
    if missing:
        problems.append(f'{rel}: 唯一鍵欄位不存在：{", ".join(missing)}（請同步修正 UNIQUE_KEYS）')
    elif keys:
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


def header_of(path):
    with open(path, encoding='utf-8') as f:
        return next(csv.reader(f))


def check_split_tables(paths):
    """拆成多檔的表，主鍵唯一性要跨檔檢查"""
    problems = []
    groups = {}
    for path in paths:
        name = os.path.basename(path)
        if TABLE_PARTS.match(name) and table_of(name) in UNIQUE_KEYS:
            groups.setdefault((os.path.dirname(path), table_of(name)), []).append(path)
    for (folder, table), files in groups.items():
        if len(files) < 2:
            continue
        keys = UNIQUE_KEYS[table]
        seen = Counter()
        for path in files:
            with open(path, encoding='utf-8') as f:
                for r in csv.DictReader(f):
                    seen[tuple(r.get(k, '') for k in keys)] += 1
        rel = os.path.relpath(os.path.join(folder, table), ROOT).replace('\\', '/')
        for key, count in seen.items():
            if count > 1:
                problems.append(f'{rel}（跨分檔）: {"+".join(keys)} = {key} 重複 {count} 次')
    return problems


def check_file_sizes():
    """skill 內圖片與字型以外的檔案不得超過外掛目錄的 256 KiB 上限"""
    problems = []
    for skill in sorted(glob.glob(os.path.join(ROOT, 'taiwan-*'))):
        for folder, dirs, files in os.walk(skill):
            dirs[:] = [d for d in dirs if d != '__pycache__']
            for f in files:
                if f.lower().endswith(BINARY_OK):
                    continue
                path = os.path.join(folder, f)
                size = os.path.getsize(path)
                if size > MAX_FILE_BYTES:
                    rel = os.path.relpath(path, ROOT).replace('\\', '/')
                    problems.append(f'{rel}: {size:,} bytes，超過外掛目錄單檔上限 256 KiB，請拆檔')
    return problems


def check_search_config():
    """各 skill scripts/core.py 的 CSV_CONFIG 引用的欄位必須存在於對應 CSV，否則該搜尋域永遠查無結果"""
    import importlib.util
    problems = []
    for core in sorted(glob.glob(os.path.join(ROOT, 'taiwan-*', 'scripts', 'core.py'))):
        skill_dir = os.path.dirname(os.path.dirname(core))
        spec = importlib.util.spec_from_file_location('core_' + os.path.basename(skill_dir), core)
        mod = importlib.util.module_from_spec(spec)
        sys.path.insert(0, os.path.dirname(core))
        try:
            spec.loader.exec_module(mod)
        finally:
            sys.path.pop(0)
        for domain, cfg in getattr(mod, 'CSV_CONFIG', {}).items():
            # file 可為 glob（拆成多檔的表），各分檔欄位須一致
            matches = sorted(glob.glob(os.path.join(skill_dir, 'data', cfg['file'])))
            rel = os.path.relpath(core, ROOT).replace('\\', '/')
            if not matches:
                problems.append(f'{rel}: {domain} 的檔案 {cfg["file"]} 不存在')
                continue
            header = header_of(matches[0])
            for other in matches[1:]:
                if header_of(other) != header:
                    problems.append(f'{rel}: {domain} 的分檔 {os.path.basename(other)} 欄位與 {os.path.basename(matches[0])} 不一致')
            for key in ('search_cols', 'output_cols'):
                missing = [c for c in cfg.get(key, []) if c not in header]
                if missing:
                    problems.append(f'{rel}: {domain}.{key} 欄位不存在於 {cfg["file"]}：{missing}')
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

    split_problems = check_split_tables(paths)
    print(f'  {"分檔主鍵跨檔唯一":<48} {"OK" if not split_problems else f"{len(split_problems)} 個問題"}')
    all_problems.extend(split_problems)

    size_problems = check_file_sizes()
    print(f'  {"單檔 256 KiB 上限":<48} {"OK" if not size_problems else f"{len(size_problems)} 個問題"}')
    all_problems.extend(size_problems)

    config_problems = check_search_config()
    print(f'  {"scripts/core.py 搜尋欄位設定":<48} {"OK" if not config_problems else f"{len(config_problems)} 個問題"}')
    all_problems.extend(config_problems)

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
