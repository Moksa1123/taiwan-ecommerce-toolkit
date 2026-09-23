#!/usr/bin/env python3
"""
Taiwan Payment 搜索 CLI

命令行搜索工具，支援多種輸出格式

用法:
    python search.py "信用卡"                    # 自動偵測域
    python search.py "10100058" --domain error   # 指定域
    python search.py "金額" --format json        # JSON 輸出
    python search.py "ECPay" --domain all        # 全域搜索
"""

import argparse
import sys
from pathlib import Path
import json
from typing import List, Dict, Tuple

# 添加父目錄到 path
sys.path.insert(0, str(Path(__file__).parent))

from core import search, search_all, CSV_CONFIG


def format_ascii_box(title: str, content: List[str], width: int = 80, style: str = 'double') -> str:
    """繪製 ASCII 邊框"""
    if style == 'double':
        top = '╔' + '═' * (width - 2) + '╗'
        mid = '╠' + '═' * (width - 2) + '╣'
        bot = '╚' + '═' * (width - 2) + '╝'
        side = '║'
    else:
        top = '┌' + '─' * (width - 2) + '┐'
        mid = '├' + '─' * (width - 2) + '┤'
        bot = '└' + '─' * (width - 2) + '┘'
        side = '│'

    lines = [top]
    lines.append(f'{side} {title.center(width - 4)} {side}')
    lines.append(mid)

    for line in content:
        # 分割長行
        if len(line) > width - 4:
            words = line.split()
            current_line = ''
            for word in words:
                if len(current_line) + len(word) + 1 < width - 4:
                    current_line += word + ' '
                else:
                    lines.append(f'{side} {current_line.ljust(width - 4)} {side}')
                    current_line = word + ' '
            if current_line:
                lines.append(f'{side} {current_line.ljust(width - 4)} {side}')
        else:
            lines.append(f'{side} {line.ljust(width - 4)} {side}')

    lines.append(bot)
    return '\n'.join(lines)


def format_result_ascii(results: List[Dict], domain: str) -> str:
    """ASCII 格式輸出"""
    if not results:
        return f'查無結果 (域: {domain})'

    output = []
    output.append('')
    output.append(f'搜索域: {domain}')
    output.append(f'找到 {len(results)} 筆結果')
    output.append('=' * 80)

    for i, result in enumerate(results, 1):
        score = result.pop('_score', 0)
        result.pop('_domain', None)

        output.append(f'\n[結果 #{i}] 評分: {score}')
        output.append('-' * 80)

        for key, value in result.items():
            if value:
                key_display = key.replace('_', ' ').title()
                output.append(f'{key_display:20s}: {value}')

    return '\n'.join(output)


def format_all_results_ascii(all_results: Dict[str, List]) -> str:
    """全域搜索 ASCII 輸出"""
    if not all_results:
        return '查無結果'

    output = []
    output.append('')
    output.append(f'全域搜索 - 找到 {len(all_results)} 個域有結果')
    output.append('=' * 80)

    for domain, results in all_results.items():
        output.append(f'\n【{domain.upper()}】 ({len(results)} 筆)')
        output.append('-' * 80)

        for i, result in enumerate(results, 1):
            score = result.pop('_score', 0)
            result.pop('_domain', None)

            output.append(f'  [{i}] 評分: {score}')

            # 顯示關鍵欄位
            if domain == 'provider':
                output.append(f'      服務商: {result.get("display_name", "")}')
                output.append(f'      加密: {result.get("auth_method", "")}')
            elif domain == 'error':
                output.append(f'      錯誤碼: {result.get("code", "")} - {result.get("message_zh", "")}')
                output.append(f'      解決: {result.get("solution", "")}')
            elif domain == 'payment_method':
                output.append(f'      方式: {result.get("method_zh", "")}（{result.get("method_code", "")}）')
                codes = [f'{k[:-5]}={v}' for k, v in result.items() if k.endswith('_code') and k != 'method_code' and v]
                output.append(f'      代碼: {", ".join(codes)}')
                output.append(f'      說明: {result.get("notes", "")}')
            else:
                # 顯示前 3 個欄位
                for key, value in list(result.items())[:3]:
                    if value:
                        output.append(f'      {key}: {value}')

            output.append('')

    return '\n'.join(output)


def main():
    parser = argparse.ArgumentParser(
        description='台灣金流搜索工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
範例:
  python search.py "信用卡"                    # 自動偵測域
  python search.py "10100058" --domain error   # 搜索錯誤碼
  python search.py "ECPay" --format json       # JSON 輸出
  python search.py "金額" --domain all         # 全域搜索

可用域:
  provider, operation, error, field, payment_method, troubleshoot, reasoning, all
        '''
    )

    parser.add_argument('query', type=str, help='搜索查詢')
    parser.add_argument(
        '--domain', '-d',
        type=str,
        choices=list(CSV_CONFIG.keys()) + ['all'],
        help='搜索域 (不指定則自動偵測)'
    )
    parser.add_argument(
        '--format', '-f',
        choices=['ascii', 'json'],
        default='ascii',
        help='輸出格式'
    )
    parser.add_argument(
        '--max', '-m',
        type=int,
        default=5,
        help='最大結果數'
    )

    args = parser.parse_args()

    # 執行搜索
    if args.domain == 'all':
        results = search_all(args.query, max_per_domain=args.max)
        if args.format == 'json':
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            print(format_all_results_ascii(results))
    else:
        results = search(args.query, domain=args.domain, max_results=args.max)
        if args.format == 'json':
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            domain = results[0]['_domain'] if results else (args.domain or 'unknown')
            print(format_result_ascii(results, domain))


if __name__ == '__main__':
    main()
