#!/usr/bin/env python3
"""
Taiwan Logistics Service Generator

輸出已驗證的實作，不產生未驗證的樣板：
- py：examples/ 內對應服務商的範例模組（CI 會實際載入，並以官方測試向量驗證加解密／簽章）
- ts：EXAMPLES.md 中標記 <!-- verify: … --> 的 TypeScript 片段（CI 以官方標準答案執行驗證）

端點與欄位見 references/ 下各服務商文件。

用法:
    python generate-logistics-service.py PAYUNi --output py > payuni_logistics.py
    python generate-logistics-service.py ECPay --output ts > ecpay-logistics.ts
    python generate-logistics-service.py --list
"""

import argparse
import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent

PYTHON_EXAMPLES = {
    'ecpay': 'ecpay-logistics-cvs-example.py',
    'newebpay': 'newebpay-logistics-cvs-example.py',
    'payuni': 'payuni-logistics-cvs-example.py',
    'paynow': 'paynow-logistics-cvs-example.py',
    'smilepay': 'smilepay-logistics-cvs-example.py',
    'pchomepay': 'pchomepay-logistics-cvs-example.py',
    'ezship': 'ezship-logistics-example.py',
    'hct': 'hct-logistics-example.py',
}

# EXAMPLES.md 的 verify 名稱
TS_SNIPPETS = {
    'ecpay': 'ecpay-cmv-md5',
    'newebpay': 'newebpay-logistics',
    'payuni': 'payuni',
}

REFERENCES = {
    'ecpay': 'references/ecpay-logistics-api.md',
    'newebpay': 'references/NEWEBPAY_LOGISTICS_REFERENCE.md',
    'payuni': 'references/payuni-logistics-api.md',
}


def python_module(provider: str) -> str:
    return (SKILL_DIR / 'examples' / PYTHON_EXAMPLES[provider]).read_text(encoding='utf-8')


def typescript_module(provider: str) -> str:
    text = (SKILL_DIR / 'EXAMPLES.md').read_text(encoding='utf-8')
    name = re.escape(TS_SNIPPETS[provider])
    m = re.search(r'<!--\s*verify:[^>]*\b' + name + r'\b[^>]*-->\s*```(?:typescript|ts)\n(.*?)```', text, re.S)
    if not m:
        raise SystemExit(f'EXAMPLES.md 找不到 {provider} 的已驗證 TypeScript 片段')
    header = (f'// {provider} 物流：已驗證的加解密／簽章實作（來源 EXAMPLES.md，CI 以官方標準答案驗證）\n'
              f'// 端點與欄位見 {REFERENCES[provider]}\n\n')
    return header + m.group(1)


def main() -> int:
    parser = argparse.ArgumentParser(description='Taiwan Logistics Service Generator',
                                     formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    parser.add_argument('provider', nargs='?', help='服務商名稱，例如 ECPay、NewebPay、PAYUNi')
    parser.add_argument('--output', choices=['ts', 'py'], default='py', help='輸出語言（預設 py）')
    parser.add_argument('--list', action='store_true', help='列出可產生的服務商')
    args = parser.parse_args()

    if args.list or not args.provider:
        print('Python：' + '、'.join(PYTHON_EXAMPLES))
        print('TypeScript：' + '、'.join(TS_SNIPPETS))
        return 0

    provider = args.provider.lower()
    table = PYTHON_EXAMPLES if args.output == 'py' else TS_SNIPPETS
    if provider not in table:
        print(f'不支援 {args.provider} 的 {args.output} 輸出；可用：{"、".join(table)}', file=sys.stderr)
        return 1
    sys.stdout.write(python_module(provider) if args.output == 'py' else typescript_module(provider))
    return 0


if __name__ == '__main__':
    sys.exit(main())
