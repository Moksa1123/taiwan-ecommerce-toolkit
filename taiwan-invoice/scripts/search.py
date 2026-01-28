#!/usr/bin/env python3
"""
Taiwan Invoice Skill - Search CLI
電子發票智能搜索命令行工具

用法:
    python search.py "ecpay B2C" --domain operation
    python search.py "1999 error" --domain error
    python search.py "稅額計算" --domain tax
    python search.py "綠界" --all
"""

import argparse
import sys
from typing import Dict, List, Any

from core import (
    search,
    search_all,
    detect_domain,
    get_available_domains,
    get_domain_info
)


def format_ascii_box(title: str, content: List[str], width: int = 80) -> str:
    """
    格式化 ASCII Box 輸出
    """
    lines = []
    lines.append('┌' + '─' * (width - 2) + '┐')
    lines.append('│' + f' {title}'.ljust(width - 2) + '│')
    lines.append('├' + '─' * (width - 2) + '┤')

    for line in content:
        # 處理過長的行
        if len(line) > width - 4:
            line = line[:width - 7] + '...'
        lines.append('│ ' + line.ljust(width - 4) + ' │')

    lines.append('└' + '─' * (width - 2) + '┘')
    return '\n'.join(lines)


def format_result(result: Dict[str, Any], domain: str) -> List[str]:
    """
    格式化單個搜索結果
    """
    lines = []
    score = result.get('_score', 0)
    lines.append(f'Score: {score}')
    lines.append('')

    for key, value in result.items():
        if key == '_score' or not value:
            continue

        # 截斷過長的值
        value_str = str(value)
        if len(value_str) > 60:
            value_str = value_str[:57] + '...'

        lines.append(f'{key}: {value_str}')

    return lines


def format_domain_results(results: List[Dict[str, Any]], domain: str, query: str) -> str:
    """
    格式化整個域的搜索結果
    """
    if not results:
        return f"No results found in '{domain}' for query: {query}"

    output = []
    output.append(f"\n{'='*60}")
    output.append(f"Domain: {domain.upper()} | Query: {query} | Results: {len(results)}")
    output.append('='*60)

    for i, result in enumerate(results, 1):
        lines = format_result(result, domain)
        box = format_ascii_box(f'Result {i}', lines, width=60)
        output.append(box)
        output.append('')

    return '\n'.join(output)


def format_all_results(results: Dict[str, List[Dict[str, Any]]], query: str) -> str:
    """
    格式化所有域的搜索結果
    """
    if not results:
        return f"No results found for query: {query}"

    output = []
    output.append(f"\n{'#'*60}")
    output.append(f"# SEARCH ALL DOMAINS: {query}")
    output.append('#'*60)

    for domain, domain_results in results.items():
        output.append(format_domain_results(domain_results, domain, query))

    return '\n'.join(output)


def list_domains():
    """
    列出所有可用的搜索域
    """
    print("\n可用的搜索域 (Available Domains):")
    print("="*50)

    for domain in get_available_domains():
        info = get_domain_info(domain)
        if info:
            print(f"\n  {domain}")
            print(f"    檔案: {info['file']}")
            print(f"    記錄數: {info['total_records']}")
            print(f"    搜索欄位: {', '.join(info['search_cols'])}")

    print()


def main():
    parser = argparse.ArgumentParser(
        description='Taiwan Invoice Skill - BM25 Search Engine',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python search.py "ecpay B2C"                    # Auto-detect domain
  python search.py "開立發票" --domain operation  # Search operations
  python search.py "10000016" --domain error      # Search error codes
  python search.py "統編" --domain field          # Search field mappings
  python search.py "B2B 稅額" --domain tax        # Search tax rules
  python search.py "列印空白" --domain troubleshoot  # Search troubleshooting
  python search.py "ECPay" --all                  # Search all domains
  python search.py --list                         # List available domains
        """
    )

    parser.add_argument('query', nargs='?', help='Search query')
    parser.add_argument('-d', '--domain', choices=get_available_domains(),
                        help='Search domain (auto-detect if not specified)')
    parser.add_argument('-n', '--max-results', type=int, default=5,
                        help='Maximum results per domain (default: 5)')
    parser.add_argument('-a', '--all', action='store_true',
                        help='Search all domains')
    parser.add_argument('-l', '--list', action='store_true',
                        help='List available domains')
    parser.add_argument('-f', '--format', choices=['ascii', 'simple', 'json'],
                        default='ascii', help='Output format (default: ascii)')

    args = parser.parse_args()

    # 列出域
    if args.list:
        list_domains()
        return

    # 檢查查詢
    if not args.query:
        parser.print_help()
        return

    query = args.query

    # 搜索所有域
    if args.all:
        results = search_all(query, args.max_results)

        if args.format == 'json':
            import json
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            print(format_all_results(results, query))
        return

    # 單域搜索
    domain = args.domain
    if not domain:
        domain = detect_domain(query)
        print(f"[Auto-detected domain: {domain}]")

    results = search(query, domain, args.max_results)

    if args.format == 'json':
        import json
        print(json.dumps(results, ensure_ascii=False, indent=2))
    elif args.format == 'simple':
        for i, result in enumerate(results, 1):
            print(f"\n[{i}] Score: {result.get('_score', 0)}")
            for key, value in result.items():
                if key != '_score' and value:
                    print(f"  {key}: {value}")
    else:
        print(format_domain_results(results, domain, query))


if __name__ == '__main__':
    main()
