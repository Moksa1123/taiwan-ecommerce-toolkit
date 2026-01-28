#!/usr/bin/env python3
"""
Taiwan Invoice Skill - BM25 Search Engine
基於 UIUX Pro Max 架構，針對電子發票數據優化

無外部依賴，純 Python 實現 BM25 搜索算法
"""

import csv
import math
import re
import os
from typing import List, Dict, Any, Optional, Tuple

# 取得 data 目錄路徑
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), 'data')

# CSV 設定：定義各域的搜索欄位和輸出欄位
CSV_CONFIG = {
    'provider': {
        'file': 'providers.csv',
        'search_cols': ['provider', 'display_name', 'auth_method', 'features'],
        'output_cols': ['provider', 'display_name', 'auth_method', 'encryption', 'test_merchant_id', 'features']
    },
    'operation': {
        'file': 'operations.csv',
        'search_cols': ['operation', 'operation_zh', 'notes'],
        'output_cols': ['operation', 'operation_zh', 'ecpay_b2c_endpoint', 'smilepay_endpoint', 'amego_endpoint', 'required_fields', 'notes']
    },
    'error': {
        'file': 'error-codes.csv',
        'search_cols': ['provider', 'code', 'message_zh', 'message_en', 'category', 'solution'],
        'output_cols': ['provider', 'code', 'message_zh', 'category', 'solution']
    },
    'field': {
        'file': 'field-mappings.csv',
        'search_cols': ['field_name', 'description', 'ecpay_name', 'smilepay_name', 'amego_name', 'notes'],
        'output_cols': ['field_name', 'description', 'ecpay_name', 'smilepay_name', 'amego_name', 'type', 'required_b2c', 'required_b2b']
    },
    'tax': {
        'file': 'tax-rules.csv',
        'search_cols': ['invoice_type', 'tax_type', 'notes'],
        'output_cols': ['invoice_type', 'tax_type', 'tax_rate', 'sales_amount_formula', 'tax_amount_formula', 'example_total', 'example_sales', 'example_tax']
    },
    'troubleshoot': {
        'file': 'troubleshooting.csv',
        'search_cols': ['issue', 'symptom', 'cause', 'solution', 'provider', 'category'],
        'output_cols': ['issue', 'symptom', 'cause', 'solution', 'provider', 'severity']
    }
}

# 域名自動偵測關鍵字
DOMAIN_KEYWORDS = {
    'provider': ['ecpay', '綠界', 'smilepay', '速買配', 'amego', '光貿', 'provider', '加值中心', '服務商'],
    'operation': ['issue', 'void', 'allowance', '開立', '作廢', '折讓', '列印', 'print', 'query', '查詢', 'endpoint', 'api'],
    'error': ['error', 'code', '錯誤', '代碼', '失敗', 'fail', '-', '10000', '1001', '2001'],
    'field': ['field', 'param', '欄位', '參數', 'mapping', '映射', 'merchantid', 'orderid', 'buyername'],
    'tax': ['tax', 'b2c', 'b2b', '稅', '應稅', '免稅', '零稅率', 'salesamount', 'taxamount', '計算'],
    'troubleshoot': ['問題', 'issue', 'error', 'fix', '解決', '失敗', '空白', 'troubleshoot', '踩坑']
}


def tokenize(text: str) -> List[str]:
    """
    將文字分詞為 token 列表
    支援中英文混合
    """
    if not text:
        return []

    text = text.lower()
    # 移除標點符號，保留中文、英文、數字
    text = re.sub(r'[^\w\u4e00-\u9fff\s-]', ' ', text)
    # 分割並過濾長度 < 2 的 token (英文)
    tokens = text.split()
    return [t for t in tokens if len(t) >= 1]


def compute_idf(documents: List[List[str]]) -> Dict[str, float]:
    """
    計算 IDF (Inverse Document Frequency)
    """
    N = len(documents)
    if N == 0:
        return {}

    df = {}  # document frequency
    for doc in documents:
        unique_terms = set(doc)
        for term in unique_terms:
            df[term] = df.get(term, 0) + 1

    idf = {}
    for term, freq in df.items():
        idf[term] = math.log((N - freq + 0.5) / (freq + 0.5) + 1)

    return idf


def bm25_score(query_tokens: List[str], doc_tokens: List[str],
               idf: Dict[str, float], avg_dl: float,
               k1: float = 1.5, b: float = 0.75) -> float:
    """
    計算 BM25 分數
    """
    if not doc_tokens or not query_tokens:
        return 0.0

    doc_len = len(doc_tokens)
    score = 0.0

    # 計算詞頻
    tf = {}
    for token in doc_tokens:
        tf[token] = tf.get(token, 0) + 1

    for term in query_tokens:
        if term not in tf:
            continue

        freq = tf[term]
        term_idf = idf.get(term, 0)

        # BM25 公式
        numerator = freq * (k1 + 1)
        denominator = freq + k1 * (1 - b + b * doc_len / avg_dl) if avg_dl > 0 else freq + k1
        score += term_idf * (numerator / denominator)

    return score


def _load_csv(filepath: str) -> List[Dict[str, str]]:
    """
    載入 CSV 檔案
    """
    if not os.path.exists(filepath):
        return []

    rows = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def _search_csv(query: str, domain: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    對指定域的 CSV 進行 BM25 搜索
    """
    if domain not in CSV_CONFIG:
        return []

    config = CSV_CONFIG[domain]
    filepath = os.path.join(DATA_DIR, config['file'])
    rows = _load_csv(filepath)

    if not rows:
        return []

    # 建立文檔
    documents = []
    for row in rows:
        doc_text = ' '.join(str(row.get(col, '')) for col in config['search_cols'])
        documents.append(tokenize(doc_text))

    # 計算 IDF 和平均文檔長度
    idf = compute_idf(documents)
    avg_dl = sum(len(doc) for doc in documents) / len(documents) if documents else 1

    # 計算每個文檔的分數
    query_tokens = tokenize(query)
    scored_results = []

    for i, (row, doc_tokens) in enumerate(zip(rows, documents)):
        score = bm25_score(query_tokens, doc_tokens, idf, avg_dl)
        if score > 0:
            result = {col: row.get(col, '') for col in config['output_cols']}
            result['_score'] = round(score, 4)
            scored_results.append(result)

    # 按分數排序
    scored_results.sort(key=lambda x: x['_score'], reverse=True)

    return scored_results[:max_results]


def detect_domain(query: str) -> str:
    """
    自動偵測查詢屬於哪個域
    """
    query_lower = query.lower()

    scores = {domain: 0 for domain in DOMAIN_KEYWORDS}

    for domain, keywords in DOMAIN_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in query_lower:
                scores[domain] += 1

    # 找出最高分的域
    best_domain = max(scores, key=scores.get)

    # 如果沒有匹配，預設為 troubleshoot
    if scores[best_domain] == 0:
        return 'troubleshoot'

    return best_domain


def search(query: str, domain: Optional[str] = None, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    主搜索函數

    Args:
        query: 搜索查詢
        domain: 指定域 (provider, operation, error, field, tax, troubleshoot)
                如果不指定，會自動偵測
        max_results: 最大結果數

    Returns:
        搜索結果列表
    """
    if not domain:
        domain = detect_domain(query)

    return _search_csv(query, domain, max_results)


def search_all(query: str, max_per_domain: int = 3) -> Dict[str, List[Dict[str, Any]]]:
    """
    在所有域中搜索

    Args:
        query: 搜索查詢
        max_per_domain: 每個域的最大結果數

    Returns:
        按域分類的搜索結果
    """
    results = {}
    for domain in CSV_CONFIG.keys():
        domain_results = _search_csv(query, domain, max_per_domain)
        if domain_results:
            results[domain] = domain_results
    return results


def get_available_domains() -> List[str]:
    """
    取得可用的搜索域列表
    """
    return list(CSV_CONFIG.keys())


def get_domain_info(domain: str) -> Optional[Dict[str, Any]]:
    """
    取得域的設定資訊
    """
    if domain not in CSV_CONFIG:
        return None

    config = CSV_CONFIG[domain]
    filepath = os.path.join(DATA_DIR, config['file'])
    rows = _load_csv(filepath)

    return {
        'domain': domain,
        'file': config['file'],
        'search_cols': config['search_cols'],
        'output_cols': config['output_cols'],
        'total_records': len(rows)
    }


# CLI 測試
if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python core.py <query> [domain]")
        print("\nAvailable domains:", ', '.join(get_available_domains()))
        sys.exit(1)

    query = sys.argv[1]
    domain = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"Query: {query}")
    if domain:
        print(f"Domain: {domain}")
    else:
        detected = detect_domain(query)
        print(f"Auto-detected domain: {detected}")

    print()

    results = search(query, domain)
    for i, result in enumerate(results, 1):
        print(f"[{i}] Score: {result.get('_score', 0)}")
        for key, value in result.items():
            if key != '_score' and value:
                print(f"    {key}: {value}")
        print()
