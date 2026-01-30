#!/usr/bin/env python3
"""
Taiwan Logistics Skill - 物流服務商推薦系統

基於 BM25 算法的智能推薦引擎
根據使用者需求自動推薦最適合的物流服務商

使用方式:
    python recommend.py "超商取貨 冷凍配送 高交易量"
    python recommend.py "7-11 B2C 穩定" --format json
    python recommend.py "生鮮電商 溫控" --format simple

作者: Taiwan E-Commerce Toolkit
版本: 1.0.0
"""

import sys
import csv
import json
import math
import argparse
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class LogisticsProvider:
    """物流服務商資料"""
    provider: str
    display_name: str
    auth_method: str
    encryption: str
    test_url: str
    prod_url: str
    content_type: str
    features: List[str]
    market_share: str
    api_style: str
    logistics_types: List[str]


@dataclass
class RecommendResult:
    """推薦結果"""
    provider: str
    display_name: str
    score: float
    match_reasons: List[str]
    features: List[str]
    warnings: List[str]


class BM25:
    """BM25 搜尋算法"""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b

    def score(self, query_terms: List[str], doc_terms: List[str],
              avg_doc_len: float, doc_len: int, total_docs: int,
              doc_freq: Dict[str, int]) -> float:
        """計算 BM25 分數"""
        score = 0.0

        for term in query_terms:
            if term not in doc_terms:
                continue

            tf = doc_terms.count(term)
            df = doc_freq.get(term, 0)

            if df == 0:
                continue

            idf = math.log((total_docs - df + 0.5) / (df + 0.5) + 1)
            score += idf * (tf * (self.k1 + 1)) / \
                     (tf + self.k1 * (1 - self.b + self.b * (doc_len / avg_doc_len)))

        return score


class LogisticsRecommender:
    """物流服務商推薦引擎"""

    # 關鍵字權重
    KEYWORD_WEIGHTS = {
        # ECPay 綠界
        'ecpay': 3.0, '綠界': 3.0, '穩定': 2.5, '市佔': 2.0, '高交易量': 2.0,
        '電商': 1.8, '文檔': 2.0, 'sdk': 2.0, '完整': 1.5, '超商': 1.5,
        '7-11': 1.5, '全家': 1.5, '萊爾富': 1.5, 'ok': 1.5, '黑貓': 1.5,
        '宅配': 1.5, 'c2c': 1.5, 'b2c': 1.5, '取貨付款': 1.5,

        # NewebPay 藍新
        'newebpay': 3.0, '藍新': 3.0, '多元': 2.0, '會員': 1.8, '整合': 2.0,
        '記憶': 1.5, '便利': 1.5, '簡單': 1.8, '快速': 1.8, '小型': 1.5,

        # PAYUNi 統一
        'payuni': 3.0, '統一': 3.0, '溫控': 3.5, '冷凍': 3.0, '冷藏': 3.0,
        '生鮮': 3.0, 'api': 2.0, 'json': 2.0, 'restful': 2.0, '新創': 1.8,
        '現代': 1.5, '設計': 1.5,

        # 通用關鍵字
        '物流': 1.0, '配送': 1.0, '取貨': 1.0, '超商': 1.2, '宅配': 1.2,
    }

    # 反模式 (不建議使用的場景)
    ANTI_PATTERNS = {
        'ecpay': ['無技術資源', '極簡需求', 'api優先', '現代化'],
        'newebpay': ['簡單api', '單一支付', '極簡', '最小化'],
        'payuni': ['大型專案', '完整文檔', '傳統', 'php']
    }

    def __init__(self, data_dir: Path = None):
        """初始化推薦引擎"""
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / 'data'

        self.data_dir = data_dir
        self.providers: List[LogisticsProvider] = []
        self.bm25 = BM25(k1=1.5, b=0.75)
        self.load_data()

    def load_data(self):
        """載入服務商資料"""
        providers_file = self.data_dir / 'providers.csv'

        if not providers_file.exists():
            raise FileNotFoundError(f"找不到資料檔案: {providers_file}")

        with open(providers_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.providers.append(
                    LogisticsProvider(
                        provider=row['provider'],
                        display_name=row['display_name'],
                        auth_method=row['auth_method'],
                        encryption=row['encryption'],
                        test_url=row['test_url'],
                        prod_url=row['prod_url'],
                        content_type=row['content_type'],
                        features=row['features'].split(' | '),
                        market_share=row['market_share'],
                        api_style=row['api_style'],
                        logistics_types=row['logistics_types'].split(' | ')
                    )
                )

    def tokenize(self, text: str) -> List[str]:
        """分詞"""
        text = text.lower()
        return text.split()

    def build_document(self, provider: LogisticsProvider) -> str:
        """建立服務商文件 (用於搜尋)"""
        parts = [
            provider.provider,
            provider.display_name,
            provider.auth_method,
            provider.api_style,
            provider.market_share,
            ' '.join(provider.features),
            ' '.join(provider.logistics_types)
        ]
        return ' '.join(parts)

    def calculate_weighted_score(self, query: str, provider: LogisticsProvider) -> Tuple[float, List[str]]:
        """計算加權分數"""
        query_terms = self.tokenize(query)
        doc_text = self.build_document(provider)
        doc_terms = self.tokenize(doc_text)

        # 計算 BM25 基礎分數
        total_docs = len(self.providers)
        avg_doc_len = sum(len(self.tokenize(self.build_document(p))) for p in self.providers) / total_docs
        doc_len = len(doc_terms)

        doc_freq = {}
        for term in set(query_terms):
            doc_freq[term] = sum(1 for p in self.providers if term in self.tokenize(self.build_document(p)))

        base_score = self.bm25.score(query_terms, doc_terms, avg_doc_len, doc_len, total_docs, doc_freq)

        # 應用關鍵字權重
        weighted_score = base_score
        match_reasons = []

        for term in query_terms:
            if term in doc_terms:
                weight = self.KEYWORD_WEIGHTS.get(term, 1.0)
                if weight > 1.0:
                    weighted_score += base_score * (weight - 1.0) * 0.1
                    match_reasons.append(f"關鍵字匹配: {term} (權重 {weight:.1f})")

        return weighted_score, match_reasons

    def check_anti_patterns(self, query: str, provider_key: str) -> List[str]:
        """檢查反模式"""
        warnings = []
        query_lower = query.lower()

        if provider_key in self.ANTI_PATTERNS:
            for pattern in self.ANTI_PATTERNS[provider_key]:
                if pattern in query_lower:
                    warnings.append(f"注意: {provider_key.upper()} 可能不適合「{pattern}」場景")

        return warnings

    def recommend(self, query: str, top_k: int = 3) -> List[RecommendResult]:
        """
        推薦物流服務商

        Args:
            query: 需求描述
            top_k: 回傳前 K 個推薦結果

        Returns:
            推薦結果清單
        """
        results = []

        for provider in self.providers:
            score, match_reasons = self.calculate_weighted_score(query, provider)
            warnings = self.check_anti_patterns(query, provider.provider.lower())

            results.append(
                RecommendResult(
                    provider=provider.provider,
                    display_name=provider.display_name,
                    score=score,
                    match_reasons=match_reasons,
                    features=provider.features,
                    warnings=warnings
                )
            )

        # 依分數排序
        results.sort(key=lambda x: x.score, reverse=True)

        return results[:top_k]

    def format_output(self, results: List[RecommendResult], format_type: str = 'detailed') -> str:
        """
        格式化輸出

        Args:
            results: 推薦結果
            format_type: 輸出格式 ('detailed', 'simple', 'json')

        Returns:
            格式化的推薦結果
        """
        if format_type == 'json':
            return json.dumps(
                [
                    {
                        'provider': r.provider,
                        'display_name': r.display_name,
                        'score': round(r.score, 2),
                        'match_reasons': r.match_reasons,
                        'features': r.features,
                        'warnings': r.warnings
                    }
                    for r in results
                ],
                ensure_ascii=False,
                indent=2
            )

        elif format_type == 'simple':
            lines = []
            for i, result in enumerate(results, 1):
                lines.append(f"{i}. {result.display_name} ({result.provider.upper()}) - 分數: {result.score:.2f}")
            return '\n'.join(lines)

        else:  # detailed
            lines = []
            lines.append("=" * 70)
            lines.append("物流服務商推薦結果")
            lines.append("=" * 70)
            lines.append("")

            for i, result in enumerate(results, 1):
                lines.append(f"推薦 #{i}: {result.display_name} ({result.provider.upper()})")
                lines.append(f"  匹配分數: {result.score:.2f}")
                lines.append("")
                lines.append("  特色功能:")
                for feature in result.features:
                    lines.append(f"    • {feature}")
                lines.append("")

                if result.match_reasons:
                    lines.append("  匹配原因:")
                    for reason in result.match_reasons[:5]:  # 只顯示前 5 個
                        lines.append(f"    • {reason}")
                    lines.append("")

                if result.warnings:
                    lines.append("  ⚠️  注意事項:")
                    for warning in result.warnings:
                        lines.append(f"    • {warning}")
                    lines.append("")

                lines.append("-" * 70)
                lines.append("")

            return '\n'.join(lines)


# ============================================================================
# CLI 介面
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Taiwan Logistics Skill - 物流服務商推薦系統',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  python recommend.py "超商取貨 冷凍配送"
  python recommend.py "7-11 B2C 大量訂單" --format json
  python recommend.py "生鮮電商 溫控 穩定" --format simple
  python recommend.py "新創公司 API 設計" --top 2

關鍵字建議:
  ECPay:    穩定、市佔、高交易量、電商、文檔、SDK、超商、宅配
  NewebPay: 多元、會員、整合、簡單、快速、便利
  PAYUNi:   溫控、冷凍、冷藏、生鮮、API、JSON、RESTful、新創
        """
    )

    parser.add_argument('query', type=str, help='需求描述 (關鍵字以空格分隔)')
    parser.add_argument('--format', type=str, choices=['detailed', 'simple', 'json'],
                        default='detailed', help='輸出格式 (預設: detailed)')
    parser.add_argument('--top', type=int, default=3, help='回傳前 K 個推薦 (預設: 3)')

    args = parser.parse_args()

    try:
        # 初始化推薦引擎
        recommender = LogisticsRecommender()

        # 執行推薦
        results = recommender.recommend(args.query, top_k=args.top)

        # 輸出結果
        output = recommender.format_output(results, format_type=args.format)
        print(output)

        return 0

    except FileNotFoundError as e:
        print(f"錯誤: {e}", file=sys.stderr)
        return 1

    except Exception as e:
        print(f"執行錯誤: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
