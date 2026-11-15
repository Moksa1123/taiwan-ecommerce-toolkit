#!/usr/bin/env python3
"""
Taiwan Logistics 搜索命令行工具

用法:
    python search.py "7-11"                     # 自動偵測域
    python search.py "建立訂單" --domain operation  # 指定域
    python search.py "配送狀態" --format json    # JSON 輸出
    python search.py "NewebPay" --max 10        # 限制結果數量
"""

import argparse
import json
import sys
from pathlib import Path

# Add parent directory to path
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from core import search, search_all, detect_domain, CSV_CONFIG, dataset_stats, use_utf8_stdout


def format_text(results: list) -> str:
    """格式化為文本輸出"""
    if not results:
        return "沒有找到結果"

    output = []
    for i, result in enumerate(results, 1):
        domain = result.pop('_domain', 'unknown')
        score = result.pop('_score', 0)

        output.append(f"\n[{i}] 分數: {score:.2f} | 域: {domain}")
        output.append("-" * 60)

        for key, value in result.items():
            if value:
                output.append(f"  {key}: {value}")

    return "\n".join(output)


def format_json(results: list) -> str:
    """格式化為 JSON 輸出"""
    return json.dumps(results, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description='Taiwan Logistics 搜索工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  %(prog)s "7-11 取貨"                    # 搜索 7-11 相關
  %(prog)s "NewebPay" --domain provider  # 搜索服務商
  %(prog)s "建立訂單" --domain operation  # 搜索 API 操作
  %(prog)s "配送中" --domain status      # 搜索配送狀態
  %(prog)s "重量" --domain field         # 搜索欄位說明
  %(prog)s "黑貓" --format json          # JSON 輸出

可用域 (domains):
  provider       - 物流服務商 (ECPay, NewebPay, PAYUNi)
  operation      - API 操作 (建立、查詢、列印)
  logistics_type - 物流類型 (7-11, 全家, 黑貓)
  field          - 欄位對照表
  status         - 配送狀態碼
  all            - 全域搜索
        """
    )

    parser.add_argument(
        'query', nargs='?',
        help='搜索關鍵字'
    )
    parser.add_argument(
        '--domain', '-d',
        choices=list(CSV_CONFIG.keys()) + ['all'],
        help='搜索域 (不指定則自動偵測)'
    )
    parser.add_argument(
        '--max', '-m',
        type=int,
        default=5,
        metavar='N',
        help='最大結果數量 (預設: 5)'
    )
    parser.add_argument(
        '--format', '-f',
        choices=['text', 'json'],
        default='text',
        help='輸出格式 (預設: text)'
    )

    parser.add_argument('--stats', action='store_true', help='列出每個搜尋域的筆數')

    args = parser.parse_args()
    use_utf8_stdout()
    if args.stats:
        import json as _json
        stats = dataset_stats()
        if args.format == 'json':
            print(_json.dumps(stats, ensure_ascii=False, indent=2))
        else:
            for name, count in stats.items():
                print(f'{name:16s} {count}')
            print(f"{'total':16s} {sum(stats.values())}")
        return
    if not args.query:
        parser.error('要給搜索關鍵字，或用 --stats')

    # 執行搜索
    if args.domain == 'all':
        results = search_all(args.query, max_per_domain=args.max)

        if args.format == 'json':
            print(format_json(results))
        else:
            print(f"\n搜索查詢: '{args.query}'")
            print("=" * 60)
            for domain, domain_results in results.items():
                print(f"\n[域: {domain}]")
                print(format_text(domain_results))
    else:
        # 自動偵測或指定域
        domain = args.domain
        if domain is None:
            domain = detect_domain(args.query)
            print(f"自動偵測域: {domain}\n", file=sys.stderr)

        results = search(args.query, domain=domain, max_results=args.max)

        if args.format == 'json':
            print(format_json(results))
        else:
            print(f"搜索查詢: '{args.query}' (域: {domain})")
            print("=" * 60)
            print(format_text(results))


if __name__ == '__main__':
    main()
