#!/usr/bin/env python3
"""
Taiwan Payment BM25 搜索引擎

基於 BM25 (Okapi BM25) 演算法的語義搜索系統
支援多個搜索域: provider, operation, error, field, payment_method, troubleshoot, reasoning

用法:
    from core import search, search_all, detect_domain

    # 單域搜索
    results = search("信用卡", domain="payment_method", max_results=5)

    # 自動偵測域
    results = search("ECPay API", domain=None, max_results=3)

    # 全域搜索
    all_results = search_all("金額錯誤", max_per_domain=3)
"""

import csv
import math
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import json

# 數據文件路徑
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / 'data'

# CSV 配置
CSV_CONFIG = {
    'provider': {
        'file': 'providers.csv',
        'search_cols': ['provider', 'display_name', 'auth_method', 'features', 'api_style'],
        'output_cols': ['provider', 'display_name', 'auth_method', 'encryption', 'test_merchant_id', 'features', 'market_share', 'api_style']
    },
    'operation': {
        'file': 'operations.csv',
        'search_cols': ['operation', 'name_zh', 'name_en', 'description'],
        'output_cols': ['operation', 'name_zh', 'ecpay_endpoint', 'newebpay_endpoint', 'payuni_endpoint', 'required_fields', 'description']
    },
    'error': {
        'file': 'error-codes.csv',
        'search_cols': ['provider', 'code', 'message_zh', 'message_en', 'category', 'solution'],
        'output_cols': ['provider', 'code', 'message_zh', 'category', 'severity', 'solution']
    },
    'field': {
        'file': 'field-mappings.csv',
        # 逐一列出所有 provider 欄位 —— 原本只涵蓋 3 家，
        # 導致搜尋其餘 provider 的欄位名時完全比對不到
        'search_cols': ['field_name', 'field_zh', 'ecpay_name', 'newebpay_name', 'payuni_name', 'smilepay_name', 'pchomepay_name', 'ezpay_name', 'paynow_name', 'shopline_name', 'linepay_name', 'tappay_name', 'opay_name', 'jkopay_name', 'sunpay_name', 'gomypay_name', 'notes'],
        'output_cols': ['field_name', 'field_zh', 'ecpay_name', 'newebpay_name', 'payuni_name', 'smilepay_name', 'pchomepay_name', 'ezpay_name', 'paynow_name', 'shopline_name', 'linepay_name', 'tappay_name', 'opay_name', 'jkopay_name', 'sunpay_name', 'gomypay_name', 'type', 'required', 'notes']
    },
    'payment_method': {
        'file': 'payment-methods.csv',
        'search_cols': ['method_id', 'name_zh', 'name_en', 'ecpay_code', 'newebpay_code', 'payuni_code', 'description', 'features'],
        'output_cols': ['method_id', 'name_zh', 'ecpay_code', 'newebpay_code', 'payuni_code', 'category', 'description', 'features']
    },
    'troubleshoot': {
        'file': 'troubleshooting.csv',
        'search_cols': ['issue', 'symptom', 'cause', 'solution', 'provider'],
        'output_cols': ['issue', 'symptom', 'cause', 'solution', 'provider', 'severity']
    },
    'reasoning': {
        'file': 'reasoning.csv',
        'search_cols': ['scenario', 'recommended_provider', 'reason', 'use_cases', 'anti_patterns'],
        'output_cols': ['scenario', 'recommended_provider', 'confidence', 'reason', 'anti_patterns', 'use_cases']
    }
}

# 域偵測關鍵字
DOMAIN_KEYWORDS = {
    'provider': ['ecpay', '綠界', 'newebpay', '藍新', 'payuni', '統一', '金流', '服務商', 'provider'],
    'operation': ['create', 'query', 'refund', 'void', '建立', '查詢', '退款', '作廢', '請款', 'api', 'endpoint'],
    'error': ['error', 'code', '錯誤', '失敗', 'failed', '10100', '10200', 'TRA'],
    'field': ['field', 'parameter', '參數', '欄位', 'merchantid', 'tradeno', 'amount'],
    'payment_method': ['credit', 'atm', 'cvs', 'barcode', '信用卡', '轉帳', '超商', '支付', '付款方式', 'payment'],
    'troubleshoot': ['troubleshoot', 'issue', 'problem', '問題', '疑難', '排解', '如何', 'how to'],
    'reasoning': ['recommend', 'choose', 'select', '推薦', '選擇', '建議', '適合', '比較', 'why', '為什麼']
}


def tokenize(text: str) -> List[str]:
    """中英文混合分詞"""
    if not text:
        return []

    # 轉小寫
    text = text.lower()

    # 分離中英文
    tokens = []

    # 英文 token (包含數字)
    for match in re.finditer(r'[a-z0-9]+', text):
        tokens.append(match.group())

    # 中文 bigram + unigram
    chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
    for char in chinese_chars:
        tokens.append(char)

    # Bigram for better matching
    for i in range(len(chinese_chars) - 1):
        tokens.append(chinese_chars[i] + chinese_chars[i + 1])

    return tokens


# reasoning.csv 規則比對的最低匹配強度，低於此值視為雜訊不計分
MIN_RULE_MATCH = 0.15


def match_tokens(text: str) -> set:
    """抽出用於規則比對的 token：英數詞 + 中文 bigram。

    與 tokenize() 不同，bigram 只在同一個中文詞塊內組合、不跨空白邊界，
    避免組出跨詞的無意義片段影響規則比對的精確度。
    """
    if not text:
        return set()

    text = text.lower()
    tokens = set(re.findall(r'[a-z0-9]+', text))

    for chunk in re.findall(r'[一-鿿]+', text):
        if len(chunk) == 1:
            tokens.add(chunk)
        else:
            for i in range(len(chunk) - 1):
                tokens.add(chunk[i:i + 2])

    return tokens


def rule_match_score(query: str, *rule_fields: str) -> float:
    """量化查詢與規則文字的匹配強度，回傳 0.0–1.0。

    取代原本「命中任一詞即給滿分」的判斷 —— 舊做法讓「開立」這類高頻
    短詞使不相干的規則也拿到完整權重。

    計分方式為「規則解釋了查詢的多少比例」，即 overlap / 查詢詞數。
    刻意不納入 recall（overlap / 規則詞數）：規則的 use_cases 詞數多寡
    是撰寫風格差異，用它加權會讓寫得詳細的規則反而吃虧。

    另設最低命中詞數，避免單一詞偶然命中就計分；查詢本身很短時放寬，
    否則兩字查詢將永遠無法命中任何規則。
    """
    q = match_tokens(query)
    if not q:
        return 0.0

    min_overlap = 1 if len(q) <= 2 else 2

    best = 0.0
    for field in rule_fields:
        r = match_tokens(field)
        if not r:
            continue
        overlap = len(q & r)
        if overlap < min_overlap:
            continue
        best = max(best, overlap / len(q))

    return best


def compute_idf(documents: List[List[str]]) -> Dict[str, float]:
    """計算 IDF (Inverse Document Frequency)"""
    n = len(documents)
    df = {}

    for doc in documents:
        seen = set()
        for term in doc:
            if term not in seen:
                df[term] = df.get(term, 0) + 1
                seen.add(term)

    idf = {}
    for term, freq in df.items():
        idf[term] = math.log((n - freq + 0.5) / (freq + 0.5) + 1.0)

    return idf


def bm25_score(
    query_tokens: List[str],
    doc_tokens: List[str],
    idf: Dict[str, float],
    avg_dl: float,
    k1: float = 1.5,
    b: float = 0.75
) -> float:
    """計算 BM25 分數"""
    score = 0.0
    dl = len(doc_tokens)

    # Term frequency in document
    tf = {}
    for term in doc_tokens:
        tf[term] = tf.get(term, 0) + 1

    for term in query_tokens:
        if term in tf:
            freq = tf[term]
            idf_score = idf.get(term, 0)
            numerator = freq * (k1 + 1)
            denominator = freq + k1 * (1 - b + b * (dl / avg_dl))
            score += idf_score * (numerator / denominator)

    return score


def load_csv(domain: str) -> Tuple[List[Dict], List[List[str]]]:
    """載入 CSV 並返回行數據和 token 化文檔"""
    config = CSV_CONFIG.get(domain)
    if not config:
        return [], []

    csv_path = DATA_DIR / config['file']
    if not csv_path.exists():
        return [], []

    rows = []
    documents = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

            # 組合搜索欄位
            search_text = ' '.join(
                str(row.get(col, '')) for col in config['search_cols']
            )
            documents.append(tokenize(search_text))

    return rows, documents


def detect_domain(query: str) -> str:
    """自動偵測查詢應該屬於哪個域"""
    query_lower = query.lower()
    scores = {}

    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in query_lower)
        scores[domain] = score

    # 返回最高分的域，如果都是 0 則返回 'provider'
    max_score = max(scores.values())
    if max_score == 0:
        return 'provider'

    return max(scores, key=scores.get)


def search(
    query: str,
    domain: Optional[str] = None,
    max_results: int = 5
) -> List[Dict]:
    """
    主搜索函數

    Args:
        query: 搜索查詢
        domain: 搜索域 (None 表示自動偵測)
        max_results: 最大結果數

    Returns:
        結果列表 (按分數排序)
    """
    if not query:
        return []

    # 自動偵測域
    if domain is None:
        domain = detect_domain(query)

    # 載入數據
    rows, documents = load_csv(domain)
    if not rows:
        return []

    # 計算 IDF
    idf = compute_idf(documents)
    avg_dl = sum(len(doc) for doc in documents) / len(documents)

    # Query tokens
    query_tokens = tokenize(query)

    # 計算每個文檔的分數
    scores = []
    for i, doc_tokens in enumerate(documents):
        score = bm25_score(query_tokens, doc_tokens, idf, avg_dl)
        if score > 0:
            scores.append((score, i))

    # 排序並返回結果
    scores.sort(reverse=True)

    config = CSV_CONFIG[domain]
    results = []

    for score, idx in scores[:max_results]:
        row = rows[idx]
        result = {col: row.get(col, '') for col in config['output_cols']}
        result['_score'] = round(score, 2)
        result['_domain'] = domain
        results.append(result)

    return results


def search_all(query: str, max_per_domain: int = 3) -> Dict[str, List]:
    """全域搜索 (搜索所有域)"""
    all_results = {}

    for domain in CSV_CONFIG.keys():
        results = search(query, domain=domain, max_results=max_per_domain)
        if results:
            all_results[domain] = results

    return all_results


if __name__ == '__main__':
    # 測試
    import sys

    if len(sys.argv) < 2:
        print("用法: python core.py <query> [domain]")
        print(f"可用域: {', '.join(CSV_CONFIG.keys())}")
        sys.exit(1)

    query = sys.argv[1]
    domain = sys.argv[2] if len(sys.argv) > 2 else None

    if domain == 'all':
        results = search_all(query)
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        results = search(query, domain=domain)
        print(json.dumps(results, ensure_ascii=False, indent=2))
