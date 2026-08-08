#!/usr/bin/env python3
"""
Taiwan Invoice Skill - 加值中心推薦系統
基於使用者需求推薦最適合的電子發票加值中心

無外部依賴，純 Python 實現
"""

import csv
import os
import sys
import argparse
from typing import List, Dict, Any, Optional, Tuple

# 取得 data 目錄路徑
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), 'data')

# 推薦規則定義
RECOMMENDATION_RULES = {
    # 關鍵字 → (provider, weight, reason)
    '穩定': [('ECPay', 3, '市佔率最高，系統穩定性佳')],
    '市佔': [('ECPay', 3, '台灣電子發票市佔率領先')],
    '文檔': [('ECPay', 2, '提供完整 API 文檔與 SDK')],
    'sdk': [('ECPay', 2, '官方 SDK 支援多種語言')],
    '高交易量': [('ECPay', 3, '適合高交易量電商')],
    '電商': [('ECPay', 2, '電商整合經驗豐富')],

    '簡單': [('SmilePay', 3, '整合流程最簡單')],
    '快速': [('SmilePay', 3, '最快速完成整合')],
    '小型': [('SmilePay', 2, '適合小型專案')],
    '測試': [('SmilePay', 2, '測試環境設定簡單')],
    '無加密': [('SmilePay', 3, '無需複雜加密流程')],
    '便宜': [('SmilePay', 2, '費用較低')],
    '純b2c': [('SmilePay', 3, 'SmilePay 專注於 B2C 發票，API 設計簡潔')],
    '48小時': [('SmilePay', 2, 'SmilePay B2C 須在 48 小時內開立')],
    '字軌': [('SmilePay', 2, 'SmilePay 提供完整字軌管理功能')],
    'allamount': [('SmilePay', 2, 'SmilePay 使用 AllAmount 進行金額驗算')],

    'api': [('Amego', 3, 'MIG 4.0 最新 API 標準')],
    '設計': [('Amego', 2, 'API 設計優良')],
    '新': [('Amego', 2, '採用最新技術標準')],
    'mig': [('Amego', 3, '完整支援 MIG 4.0 規範')],
    '標準': [('Amego', 2, 'API 設計符合業界標準')],
    'md5': [('Amego', 3, 'Amego 使用 MD5 簽章驗證，計算簡單')],
    'detailvat': [('Amego', 3, 'Amego 使用 DetailVat 區分含稅/未稅')],
    'json': [('Amego', 3, 'Amego 回應格式為標準 JSON，易於解析')],
    '國際化': [('Amego', 2, 'Amego API 文件提供英文版，適合國際團隊')],

    # B2B/B2C 相關
    'b2b': [('ECPay', 1, 'B2B 發票功能完整'), ('Amego', 1, 'B2B 計算清晰')],
    'b2c': [('ECPay', 1, 'B2C 市佔最高'), ('SmilePay', 1, 'B2C 整合簡單')],
    '統編': [('ECPay', 1, 'B2B 統編發票經驗豐富')],

    # 功能相關
    '列印': [('ECPay', 2, '列印功能完整'), ('SmilePay', 1, '支援列印')],
    '作廢': [('ECPay', 1, '作廢流程完整')],
    '折讓': [('ECPay', 1, '折讓功能完整')],
    '載具': [('ECPay', 1, '載具支援完整'), ('SmilePay', 1, '載具整合簡單')],
    '捐贈': [('ECPay', 1, '捐贈功能完整')],
}

# 反模式警告
ANTI_PATTERNS = {
    'ECPay': [
        ('無技術資源', '加密流程較複雜，需要一定技術能力'),
        ('極簡整合', '如果只需最簡單整合，SmilePay 可能更適合'),
    ],
    'SmilePay': [
        ('高交易量', '大型電商建議使用 ECPay 以確保穩定性'),
        ('複雜需求', 'API 功能相對基本，複雜需求可能受限'),
        ('b2b', 'B2B 發票功能較少文檔'),
    ],
    'Amego': [
        ('市佔', '市佔率相對較低'),
        ('社群', '社群支援與範例相對較少'),
        ('穩定', '如果穩定性是首要考量，ECPay 更保險'),
    ],
}


def load_providers() -> List[Dict[str, str]]:
    """載入加值中心資料"""
    filepath = os.path.join(DATA_DIR, 'providers.csv')
    if not os.path.exists(filepath):
        return []

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)


def load_reasoning_rules() -> List[Dict[str, str]]:
    """載入推理規則"""
    filepath = os.path.join(DATA_DIR, 'reasoning.csv')
    if not os.path.exists(filepath):
        return []

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)


def analyze_requirements(query: str) -> Dict[str, Tuple[int, List[str]]]:
    """
    分析使用者需求，計算各加值中心分數

    Returns:
        Dict[provider, (score, reasons)]
    """
    query_lower = query.lower()

    # 由 providers.csv 動態建立，避免新增加值中心後推薦規則被靜默丟棄
    scores = {p['provider']: (0, []) for p in load_providers()}

    # 從 reasoning.csv 載入規則
    reasoning_rules = load_reasoning_rules()
    confidence_weights = {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}

    for rule in reasoning_rules:
        scenario = rule.get('scenario', '').lower()
        use_cases = rule.get('use_cases', '').lower()

        # 檢查場景或使用案例是否匹配查詢
        scenario_words = scenario.replace(' ', '')
        if any(word in query_lower for word in scenario.split()) or \
           any(word in query_lower for word in use_cases.split()):
            provider = rule.get('recommended_provider', '')
            confidence = rule.get('confidence', 'LOW')
            reason = rule.get('reason', '')

            if provider in scores:
                weight = confidence_weights.get(confidence, 1)
                current_score, reasons = scores[provider]
                if reason and reason not in reasons:
                    scores[provider] = (current_score + weight, reasons + [reason])

    # 根據關鍵字累計分數 (fallback)
    for keyword, rules in RECOMMENDATION_RULES.items():
        if keyword.lower() in query_lower:
            for provider, weight, reason in rules:
                current_score, reasons = scores[provider]
                if reason not in reasons:
                    scores[provider] = (current_score + weight, reasons + [reason])

    return scores


def get_anti_pattern_warnings(query: str, recommended: str) -> List[str]:
    """取得反模式警告"""
    query_lower = query.lower()
    warnings = []

    if recommended in ANTI_PATTERNS:
        for keyword, warning in ANTI_PATTERNS[recommended]:
            if keyword.lower() in query_lower:
                warnings.append(warning)

    return warnings


def recommend(query: str, verbose: bool = False) -> Dict[str, Any]:
    """
    推薦加值中心

    Args:
        query: 使用者需求描述
        verbose: 是否輸出詳細資訊

    Returns:
        推薦結果
    """
    providers = load_providers()
    scores = analyze_requirements(query)

    # 排序取得推薦順序
    sorted_providers = sorted(
        scores.items(),
        key=lambda x: x[1][0],
        reverse=True
    )

    # 建立結果
    recommended = sorted_providers[0][0]
    recommended_score, recommended_reasons = sorted_providers[0][1]

    # 如果沒有匹配任何關鍵字，給預設推薦
    if recommended_score == 0:
        recommended = 'ECPay'
        recommended_reasons = ['市佔率最高，適合大多數場景', '文檔完整，社群支援豐富']
        recommended_score = 1

    # 取得加值中心詳細資訊
    provider_info = None
    for p in providers:
        if p.get('provider') == recommended:
            provider_info = p
            break

    # 取得警告
    warnings = get_anti_pattern_warnings(query, recommended)

    result = {
        'query': query,
        'recommended': recommended,
        'score': recommended_score,
        'reasons': recommended_reasons,
        'warnings': warnings,
        'alternatives': [],
        'provider_info': provider_info,
    }

    # 加入替代方案
    for provider, (score, reasons) in sorted_providers[1:]:
        if score > 0:
            result['alternatives'].append({
                'provider': provider,
                'score': score,
                'reasons': reasons,
            })

    return result


def format_ascii_box(result: Dict[str, Any]) -> str:
    """格式化為 ASCII Box 輸出"""
    width = 70
    lines = []

    # 頂部邊框
    lines.append('╔' + '═' * (width - 2) + '╗')
    lines.append('║' + ' 🎯 加值中心推薦結果 '.center(width - 2) + '║')
    lines.append('╠' + '═' * (width - 2) + '╣')

    # 查詢內容
    query_line = f' 需求: {result["query"]}'
    if len(query_line) > width - 4:
        query_line = query_line[:width - 7] + '...'
    lines.append('║' + query_line.ljust(width - 2) + '║')
    lines.append('╠' + '─' * (width - 2) + '╣')

    # 推薦結果
    recommended = result['recommended']
    score = result['score']
    lines.append('║' + f' ⭐ 推薦: {recommended} (信心分數: {score})'.ljust(width - 2) + '║')
    lines.append('║' + ' '.ljust(width - 2) + '║')

    # 推薦原因
    lines.append('║' + ' 📋 推薦原因:'.ljust(width - 2) + '║')
    for reason in result['reasons']:
        reason_line = f'    • {reason}'
        if len(reason_line) > width - 4:
            reason_line = reason_line[:width - 7] + '...'
        lines.append('║' + reason_line.ljust(width - 2) + '║')

    # 警告
    if result['warnings']:
        lines.append('║' + ' '.ljust(width - 2) + '║')
        lines.append('║' + ' ⚠️  注意事項:'.ljust(width - 2) + '║')
        for warning in result['warnings']:
            warning_line = f'    • {warning}'
            if len(warning_line) > width - 4:
                warning_line = warning_line[:width - 7] + '...'
            lines.append('║' + warning_line.ljust(width - 2) + '║')

    # 替代方案
    if result['alternatives']:
        lines.append('║' + ' '.ljust(width - 2) + '║')
        lines.append('╠' + '─' * (width - 2) + '╣')
        lines.append('║' + ' 🔄 替代方案:'.ljust(width - 2) + '║')
        for alt in result['alternatives']:
            alt_line = f'    • {alt["provider"]} (分數: {alt["score"]})'
            lines.append('║' + alt_line.ljust(width - 2) + '║')
            for reason in alt['reasons'][:2]:  # 只顯示前 2 個原因
                reason_line = f'      - {reason}'
                if len(reason_line) > width - 4:
                    reason_line = reason_line[:width - 7] + '...'
                lines.append('║' + reason_line.ljust(width - 2) + '║')

    # 加值中心資訊
    if result['provider_info']:
        info = result['provider_info']
        lines.append('║' + ' '.ljust(width - 2) + '║')
        lines.append('╠' + '─' * (width - 2) + '╣')
        lines.append('║' + f' 📦 {info.get("display_name", recommended)} 資訊:'.ljust(width - 2) + '║')
        lines.append('║' + f'    認證方式: {info.get("auth_method", "N/A")}'.ljust(width - 2) + '║')
        lines.append('║' + f'    測試網址: {info.get("test_url", "N/A")}'.ljust(width - 2) + '║')
        features = info.get('features', '')
        if features:
            feat_line = f'    特色: {features}'
            if len(feat_line) > width - 4:
                feat_line = feat_line[:width - 7] + '...'
            lines.append('║' + feat_line.ljust(width - 2) + '║')

    # 底部邊框
    lines.append('╚' + '═' * (width - 2) + '╝')

    return '\n'.join(lines)


def format_json(result: Dict[str, Any]) -> str:
    """格式化為 JSON 輸出"""
    import json
    return json.dumps(result, ensure_ascii=False, indent=2)


def format_simple(result: Dict[str, Any]) -> str:
    """格式化為簡單文字輸出"""
    lines = []
    lines.append(f"推薦加值中心: {result['recommended']}")
    lines.append(f"信心分數: {result['score']}")
    lines.append("")
    lines.append("推薦原因:")
    for reason in result['reasons']:
        lines.append(f"  - {reason}")

    if result['warnings']:
        lines.append("")
        lines.append("注意事項:")
        for warning in result['warnings']:
            lines.append(f"  - {warning}")

    if result['alternatives']:
        lines.append("")
        lines.append("替代方案:")
        for alt in result['alternatives']:
            lines.append(f"  - {alt['provider']} (分數: {alt['score']})")

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='Taiwan Invoice 加值中心推薦系統',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  python recommend.py "電商 高交易量 穩定"
  python recommend.py "簡單整合 快速上線" --format json
  python recommend.py "API設計優先 MIG標準" --format simple

關鍵字範例:
  穩定性: 穩定, 市佔, 高交易量, 電商
  簡易性: 簡單, 快速, 小型, 測試
  API品質: api, 設計, 新, mig, 標準
  功能: b2b, b2c, 列印, 作廢, 折讓, 載具, 捐贈
"""
    )

    parser.add_argument('query', help='需求描述 (關鍵字以空格分隔)')
    parser.add_argument(
        '-f', '--format',
        choices=['ascii', 'json', 'simple'],
        default='ascii',
        help='輸出格式 (預設: ascii)'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='顯示詳細資訊'
    )

    args = parser.parse_args()

    # 執行推薦
    result = recommend(args.query, args.verbose)

    # 輸出結果
    if args.format == 'json':
        print(format_json(result))
    elif args.format == 'simple':
        print(format_simple(result))
    else:
        print(format_ascii_box(result))


if __name__ == '__main__':
    main()
