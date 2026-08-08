#!/usr/bin/env python3
"""
Taiwan Logistics BM25 搜索引擎

基於 BM25 (Okapi BM25) 演算法的語義搜索系統
支援多個搜索域: provider, operation, logistics_type, field, status

用法:
    from core import search, search_all, detect_domain

    # 單域搜索
    results = search("7-11", domain="logistics_type", max_results=5)

    # 自動偵測域
    results = search("NewebPay API", domain=None, max_results=3)

    # 全域搜索
    all_results = search_all("配送失敗", max_per_domain=3)
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
        'search_cols': ['provider', 'name_zh', 'name_en', 'features'],
        'output_cols': ['provider', 'name_zh', 'type', 'test_merchant_id', 'test_hash_key', 'features', 'coverage']
    },
    'operation': {
        'file': 'operations.csv',
        # 逐一列出所有 provider 端點欄位，與 field 域同理
        'search_cols': ['operation', 'operation_zh', 'ecpay_endpoint', 'newebpay_endpoint', 'payuni_endpoint', 'notes'],
        'output_cols': ['operation', 'operation_zh', 'ecpay_endpoint', 'newebpay_endpoint', 'payuni_endpoint', 'method', 'required_fields', 'optional_fields', 'notes']
    },
    'logistics_type': {
        'file': 'logistics-types.csv',
        'search_cols': ['code', 'name_zh', 'name_en', 'provider', 'notes'],
        'output_cols': ['code', 'name_zh', 'provider', 'category', 'size_limit', 'weight_limit', 'notes']
    },
    'field': {
        'file': 'field-mappings.csv',
        # 逐一列出所有 provider 欄位 —— 原本只涵蓋 3 家，
        # 導致搜尋其餘 provider 的欄位名時完全比對不到
        'search_cols': ['field_name', 'field_zh', 'ecpay_name', 'newebpay_name', 'payuni_name', 'smilepay_name', 'pchomepay_name', 'paynow_name', 'hct_name', 'ezship_name', 'lalamove_name', 'pandago_name', 'uber_direct_name', 'notes'],
        'output_cols': ['field_name', 'field_zh', 'ecpay_name', 'newebpay_name', 'payuni_name', 'smilepay_name', 'pchomepay_name', 'paynow_name', 'hct_name', 'ezship_name', 'lalamove_name', 'pandago_name', 'uber_direct_name', 'type', 'required', 'notes']
    },
    'status': {
        'file': 'status-codes.csv',
        'search_cols': ['provider', 'code', 'status_zh', 'status_en', 'description'],
        'output_cols': ['provider', 'code', 'status_zh', 'category', 'description']
    }
}

# 域偵測關鍵字
DOMAIN_KEYWORDS = {
    'provider': ['ecpay', '綠界', 'newebpay', '藍新', 'payuni', '統一', '物流', '服務商', 'provider'],
    'operation': ['create', 'query', 'print', 'map', '建立', '查詢', '列印', '電子地圖', 'api', 'endpoint'],
    'logistics_type': ['711', '7-11', 'family', '全家', 'hilife', '萊爾富', 'okmart', 'tcat', '黑貓', '超商', '宅配', 'cvs', 'home'],
    'field': ['field', 'parameter', '參數', '欄位', 'merchantid', 'tradeno', 'logistics'],
    'status': ['status', 'code', '狀態', '配送', '取貨', '完成', '失敗', '300', '3001']
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
