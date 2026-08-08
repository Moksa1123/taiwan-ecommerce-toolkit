#!/usr/bin/env python3
"""
Taiwan Payment 推薦系統

基於關鍵字加權評分的智能推薦引擎
根據需求場景推薦最適合的金流服務商

用法:
    python recommend.py "高交易量電商"
    python recommend.py "快速整合 LINE Pay" --format json
    python recommend.py "新創公司 API" --format simple
"""

from typing import List, Dict, Tuple, Optional
import argparse
import csv
from pathlib import Path
from typing import Dict, List, Tuple
import json

# 路徑設定
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / 'data'

# 推薦規則 (關鍵字 -> [(provider, 權重, 理由)])
RECOMMENDATION_RULES = {
    '穩定': [('ecpay', 3, '市佔率最高，穩定性最佳')],
    '高交易': [('ecpay', 3, '適合高交易量場景')],
    '快速': [('ecpay', 2, '文檔完整，整合快速')],
    '簡單': [('ecpay', 2, '範例豐富，容易上手')],
    '整合': [('ecpay', 2, '社群資源豐富')],
    '多元': [('newebpay', 3, '支援最多支付方式')],
    '支付方式': [('newebpay', 3, '13 種付款方式')],
    '電子錢包': [('newebpay', 3, 'LINE Pay / Apple Pay / Google Pay')],
    'line': [('newebpay', 3, '原生支援 LINE Pay')],
    '行動': [('newebpay', 3, '行動支付完整')],
    '記憶': [('newebpay', 3, '信用卡記憶功能')],
    '會員': [('newebpay', 2, '適合會員制電商')],
    'api': [('payuni', 3, 'RESTful JSON API')],
    'json': [('payuni', 3, 'JSON 格式友好')],
    'restful': [('payuni', 3, 'RESTful 設計')],
    '統一': [('payuni', 2, '統一集團背景')],
    '新創': [('payuni', 2, 'API 設計優先')],
    'aes-gcm': [('payuni', 3, 'AES-256-GCM 加密提供更高安全性')],
    'gcm': [('payuni', 3, '使用 GCM 認證加密')],
    '銀聯': [('payuni', 3, '支援銀聯卡等國際支付')],
    'unionpay': [('payuni', 3, '支援銀聯卡')],
    'apple pay': [('payuni', 3, '整合 Apple Pay 和 Google Pay')],
    'google pay': [('payuni', 3, '整合 Apple Pay 和 Google Pay')],
    'icash': [('payuni', 3, '整合 icash Pay 電子支付')],
    '電子支付': [('payuni', 2, '支援 icash Pay')],
    'atm': [('ecpay', 2, 'ATM 虛擬帳號')],
    '超商': [('ecpay', 2, '四大超商支援')],
    '定期': [('ecpay', 3, '定期定額扣款')],
    '訂閱': [('ecpay', 3, '訂閱制服務')],
    '分期': [('ecpay', 3, '信用卡分期')],
    'bnpl': [('ecpay', 2, '先買後付')],
    '測試': [('ecpay', 2, '測試帳號完整')],
    'php': [('ecpay', 2, 'PHP SDK 完整')],
    'node': [('payuni', 2, 'JSON API 友好')],
    'python': [('ecpay', 2, 'Python 範例完整')],
    'app': [('newebpay', 3, '行動支付完整')],
    '跨境': [('newebpay', 2, '支援國際卡')],
    '發票': [('ecpay', 2, '同時支援金流發票')],
    '物流': [('ecpay', 2, '同時支援金流物流')],
}

# 反模式 (不建議的場景)
ANTI_PATTERNS = {
    'ecpay': [
        ('無技術資源', 'SHA256 加密流程較複雜，建議有技術人員'),
        ('極簡需求', '若只需基礎支付，可能功能過多'),
    ],
    'newebpay': [
        ('簡單 API', 'AES 雙層加密較複雜'),
        ('單一支付', '若只需單一支付方式，不需選擇此平台'),
    ],
    'payuni': [
        ('大型專案', '社群資源較少，大型專案建議選 ECPay'),
        ('完整文檔', '文檔完整度不如 ECPay'),
    ]
}


def load_providers_csv() -> List[Dict]:
    """從 providers.csv 載入服務商清單"""
    csv_path = DATA_DIR / 'providers.csv'
    if not csv_path.exists():
        return []

    with open(csv_path, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def load_reasoning_csv() -> List[Dict]:
    """從 reasoning.csv 載入推薦規則"""
    csv_path = DATA_DIR / 'reasoning.csv'
    if not csv_path.exists():
        return []

    rules = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rules.append(row)

    return rules


def analyze_requirements(query: str) -> Dict[str, Tuple[int, List[str]]]:
    """
    分析需求並計算各服務商的推薦分數

    Returns:
        {provider: (score, [reasons])}
    """
    query_lower = query.lower()
    # 由 providers.csv 動態建立，避免新增服務商後推薦規則被靜默丟棄
    providers = [p['provider'] for p in load_providers_csv()]
    scores = {p: 0 for p in providers}
    reasons = {p: [] for p in providers}

    # 基於關鍵字規則計分
    for keyword, recommendations in RECOMMENDATION_RULES.items():
        if keyword in query_lower:
            for provider, weight, reason in recommendations:
                scores[provider] += weight
                reasons[provider].append(f'✓ {reason} (+{weight})')

    # 從 CSV 載入額外規則
    csv_rules = load_reasoning_csv()
    for rule in csv_rules:
        scenario = rule.get('scenario', '').lower()
        if any(word in scenario for word in query_lower.split()):
            provider = rule.get('recommended_provider', '').lower()
            if provider in scores:
                confidence = rule.get('confidence', 'MEDIUM')
                weight_map = {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}
                weight = weight_map.get(confidence, 1)
                scores[provider] += weight

                reason_text = rule.get('reason', '')
                if reason_text:
                    reasons[provider].append(f'✓ {reason_text} (+{weight})')

    return {p: (s, reasons[p]) for p, s in scores.items()}


def get_anti_patterns(provider: str) -> List[str]:
    """獲取反模式警告"""
    return [f'⚠ {pattern}: {desc}' for pattern, desc in ANTI_PATTERNS.get(provider, [])]


def format_recommendation_ascii(results: Dict[str, Tuple[int, List[str]]], query: str) -> str:
    """格式化輸出 (ASCII Box)"""
    # 排序
    sorted_results = sorted(results.items(), key=lambda x: x[1][0], reverse=True)

    output = []
    output.append('╔' + '═' * 78 + '╗')
    output.append('║' + f' 台灣金流推薦系統 - 分析結果'.center(76) + '║')
    output.append('╠' + '═' * 78 + '╣')
    output.append('║' + f' 查詢: {query}'.ljust(77) + '║')
    output.append('╚' + '═' * 78 + '╝')
    output.append('')

    for rank, (provider, (score, reason_list)) in enumerate(sorted_results, 1):
        if score == 0:
            continue

        # Provider 名稱
        provider_names = {p['provider']: p['display_name']
                          for p in load_providers_csv()}
        display_name = provider_names.get(provider, provider)

        # Emoji
        emoji = '🥇' if rank == 1 else '🥈' if rank == 2 else '🥉'

        output.append(f'{emoji} 推薦 #{rank}: {display_name}')
        output.append(f'   評分: {score} 分')
        output.append('')

        if reason_list:
            output.append('   推薦理由:')
            for reason in reason_list:
                output.append(f'      {reason}')
            output.append('')

        # 反模式警告
        anti = get_anti_patterns(provider)
        if anti:
            output.append('   注意事項:')
            for warning in anti:
                output.append(f'      {warning}')
            output.append('')

        output.append('─' * 80)

    return '\n'.join(output)


def format_recommendation_json(results: Dict[str, Tuple[int, List[str]]], query: str) -> str:
    """格式化輸出 (JSON)"""
    sorted_results = sorted(results.items(), key=lambda x: x[1][0], reverse=True)

    output_data = {
        'query': query,
        'recommendations': []
    }

    for rank, (provider, (score, reason_list)) in enumerate(sorted_results, 1):
        if score == 0:
            continue

        provider_names = {p['provider']: p['display_name']
                          for p in load_providers_csv()}

        rec = {
            'rank': rank,
            'provider': provider,
            'display_name': provider_names.get(provider, provider),
            'score': score,
            'reasons': [r.replace('✓ ', '').split(' (+')[0] for r in reason_list],
            'anti_patterns': [a.replace('⚠ ', '') for a in get_anti_patterns(provider)]
        }
        output_data['recommendations'].append(rec)

    return json.dumps(output_data, ensure_ascii=False, indent=2)


def format_recommendation_simple(results: Dict[str, Tuple[int, List[str]]], query: str) -> str:
    """格式化輸出 (Simple Text)"""
    sorted_results = sorted(results.items(), key=lambda x: x[1][0], reverse=True)

    output = [f'查詢: {query}\n']

    for rank, (provider, (score, reason_list)) in enumerate(sorted_results, 1):
        if score == 0:
            continue

        provider_names = {p['provider']: p['display_name']
                          for p in load_providers_csv()}

        output.append(f'推薦 #{rank}: {provider_names.get(provider, provider)} ({score} 分)')

        if reason_list:
            for reason in reason_list:
                output.append(f'  - {reason.replace("✓ ", "")}')

        anti = get_anti_patterns(provider)
        if anti:
            for warning in anti:
                output.append(f'  ! {warning.replace("⚠ ", "")}')

        output.append('')

    return '\n'.join(output)


def main():
    parser = argparse.ArgumentParser(description='台灣金流推薦系統')
    parser.add_argument('query', type=str, help='需求描述')
    parser.add_argument('--format', choices=['ascii', 'json', 'simple'], default='ascii', help='輸出格式')

    args = parser.parse_args()

    # 分析需求
    results = analyze_requirements(args.query)

    # 格式化輸出
    if args.format == 'json':
        print(format_recommendation_json(results, args.query))
    elif args.format == 'simple':
        print(format_recommendation_simple(results, args.query))
    else:
        print(format_recommendation_ascii(results, args.query))


if __name__ == '__main__':
    main()
