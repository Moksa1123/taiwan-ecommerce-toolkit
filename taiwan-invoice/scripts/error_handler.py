#!/usr/bin/env python3
"""
Taiwan Invoice Skill - 系統化錯誤處理與自動重試機制

功能:
- 自動重試邏輯 (指數退避)
- 錯誤分類與建議
- 詳細日誌記錄
- 錯誤碼查詢

使用範例:
    from error_handler import InvoiceErrorHandler, retry_on_error

    handler = InvoiceErrorHandler()

    # 使用裝飾器自動重試
    @retry_on_error(max_retries=3, backoff_factor=2)
    def issue_invoice(data):
        # 發票開立邏輯
        pass
"""

import time
import functools
import logging
from typing import Callable, Optional, Dict, List
from dataclasses import dataclass
from enum import Enum


class ErrorCategory(Enum):
    """錯誤類別"""
    VALIDATION = "validation"  # 驗證錯誤
    AUTHENTICATION = "authentication"  # 認證錯誤
    PERMISSION = "permission"  # 權限錯誤
    BUSINESS_LOGIC = "business_logic"  # 業務邏輯錯誤
    NETWORK = "network"  # 網路錯誤
    SERVER = "server"  # 伺服器錯誤
    UNKNOWN = "unknown"  # 未知錯誤


class RetryStrategy(Enum):
    """重試策略"""
    NO_RETRY = "no_retry"  # 不重試
    IMMEDIATE = "immediate"  # 立即重試
    EXPONENTIAL_BACKOFF = "exponential_backoff"  # 指數退避
    LINEAR_BACKOFF = "linear_backoff"  # 線性退避


@dataclass
class ErrorInfo:
    """錯誤資訊"""
    code: str
    message: str
    category: ErrorCategory
    retry_strategy: RetryStrategy
    suggestion: str
    is_retryable: bool = False


class InvoiceErrorHandler:
    """
    電子發票錯誤處理器

    提供系統化的錯誤分類、建議與重試策略
    """

    # ECPay 錯誤碼對照表
    ERROR_CODES: Dict[str, ErrorInfo] = {
        # 成功
        '1': ErrorInfo(
            code='1',
            message='成功',
            category=ErrorCategory.VALIDATION,
            retry_strategy=RetryStrategy.NO_RETRY,
            suggestion='發票開立成功',
            is_retryable=False
        ),

        # 驗證錯誤 (不可重試)
        '10000006': ErrorInfo(
            code='10000006',
            message='RelateNumber 重複',
            category=ErrorCategory.VALIDATION,
            retry_strategy=RetryStrategy.NO_RETRY,
            suggestion='訂單編號已使用，請使用新的 RelateNumber',
            is_retryable=False
        ),
        '10000016': ErrorInfo(
            code='10000016',
            message='金額計算錯誤',
            category=ErrorCategory.VALIDATION,
            retry_strategy=RetryStrategy.NO_RETRY,
            suggestion='檢查 B2C/B2B 金額計算，B2C 使用含稅價，B2B 需分拆未稅金額與稅額',
            is_retryable=False
        ),
        '10000019': ErrorInfo(
            code='10000019',
            message='打統編不可使用載具',
            category=ErrorCategory.BUSINESS_LOGIC,
            retry_strategy=RetryStrategy.NO_RETRY,
            suggestion='B2B 發票請移除 CarrierType 和 LoveCode',
            is_retryable=False
        ),
        '10000005': ErrorInfo(
            code='10000005',
            message='TimeStamp 逾時',
            category=ErrorCategory.VALIDATION,
            retry_strategy=RetryStrategy.IMMEDIATE,
            suggestion='時間戳記超過 10 分鐘，請重新產生當前時間戳',
            is_retryable=True
        ),

        # 認證錯誤 (可重試)
        '10000002': ErrorInfo(
            code='10000002',
            message='加密驗證錯誤',
            category=ErrorCategory.AUTHENTICATION,
            retry_strategy=RetryStrategy.NO_RETRY,
            suggestion='檢查 HashKey 和 HashIV 是否正確',
            is_retryable=False
        ),

        # 網路/伺服器錯誤 (可重試)
        'NETWORK_ERROR': ErrorInfo(
            code='NETWORK_ERROR',
            message='網路連線錯誤',
            category=ErrorCategory.NETWORK,
            retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            suggestion='網路連線失敗，系統將自動重試',
            is_retryable=True
        ),
        'SERVER_ERROR': ErrorInfo(
            code='SERVER_ERROR',
            message='伺服器錯誤',
            category=ErrorCategory.SERVER,
            retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            suggestion='伺服器暫時無法回應，系統將自動重試',
            is_retryable=True
        ),
        'TIMEOUT_ERROR': ErrorInfo(
            code='TIMEOUT_ERROR',
            message='請求逾時',
            category=ErrorCategory.NETWORK,
            retry_strategy=RetryStrategy.LINEAR_BACKOFF,
            suggestion='請求逾時，系統將自動重試',
            is_retryable=True
        ),
    }

    # SmilePay 錯誤碼
    SMILEPAY_ERRORS: Dict[str, ErrorInfo] = {
        '-10066': ErrorInfo(
            code='-10066',
            message='AllAmount 驗算錯誤',
            category=ErrorCategory.VALIDATION,
            retry_strategy=RetryStrategy.NO_RETRY,
            suggestion='檢查是否傳入 TotalAmount，商品金額總和需等於訂單金額',
            is_retryable=False
        ),
        '-10084': ErrorInfo(
            code='-10084',
            message='orderid 格式錯誤',
            category=ErrorCategory.VALIDATION,
            retry_strategy=RetryStrategy.NO_RETRY,
            suggestion='訂單編號限制 30 字元以內',
            is_retryable=False
        ),
        '-10053': ErrorInfo(
            code='-10053',
            message='載具號碼錯誤',
            category=ErrorCategory.VALIDATION,
            retry_strategy=RetryStrategy.NO_RETRY,
            suggestion='驗證手機條碼格式 (/ 開頭 8 碼)',
            is_retryable=False
        ),
    }

    # Amego 錯誤碼
    AMEGO_ERRORS: Dict[str, ErrorInfo] = {
        '1002': ErrorInfo(
            code='1002',
            message='OrderId 已存在',
            category=ErrorCategory.VALIDATION,
            retry_strategy=RetryStrategy.NO_RETRY,
            suggestion='使用唯一訂單編號',
            is_retryable=False
        ),
        '1007': ErrorInfo(
            code='1007',
            message='金額計算錯誤',
            category=ErrorCategory.VALIDATION,
            retry_strategy=RetryStrategy.NO_RETRY,
            suggestion='檢查 DetailVat 設定，B2B 需設為 0',
            is_retryable=False
        ),
        '1012': ErrorInfo(
            code='1012',
            message='打統編發票不可使用載具或捐贈',
            category=ErrorCategory.BUSINESS_LOGIC,
            retry_strategy=RetryStrategy.NO_RETRY,
            suggestion='B2B 發票請移除載具與捐贈設定',
            is_retryable=False
        ),
    }

    def __init__(self, provider: str = 'ecpay', logger: Optional[logging.Logger] = None):
        """
        初始化錯誤處理器

        Args:
            provider: 服務商 ('ecpay', 'smilepay', 'amego')
            logger: 自訂 Logger
        """
        self.provider = provider.lower()
        self.logger = logger or self._setup_logger()

        # 合併錯誤碼對照表
        self.all_errors = {
            **self.ERROR_CODES,
            **self.SMILEPAY_ERRORS,
            **self.AMEGO_ERRORS
        }

    def _setup_logger(self) -> logging.Logger:
        """設定預設 Logger"""
        logger = logging.getLogger('InvoiceErrorHandler')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def get_error_info(self, error_code: str) -> ErrorInfo:
        """
        取得錯誤資訊

        Args:
            error_code: 錯誤碼

        Returns:
            錯誤資訊

        Example:
            >>> handler = InvoiceErrorHandler()
            >>> info = handler.get_error_info('10000016')
            >>> print(info.suggestion)
            檢查 B2C/B2B 金額計算
        """
        return self.all_errors.get(
            error_code,
            ErrorInfo(
                code=error_code,
                message='未知錯誤',
                category=ErrorCategory.UNKNOWN,
                retry_strategy=RetryStrategy.NO_RETRY,
                suggestion=f'錯誤碼 {error_code} 未記錄在系統中，請查閱官方文件',
                is_retryable=False
            )
        )

    def should_retry(self, error_code: str) -> bool:
        """
        判斷是否應該重試

        Args:
            error_code: 錯誤碼

        Returns:
            是否可重試
        """
        error_info = self.get_error_info(error_code)
        return error_info.is_retryable

    def log_error(self, error_code: str, context: Optional[Dict] = None):
        """
        記錄錯誤

        Args:
            error_code: 錯誤碼
            context: 額外上下文資訊
        """
        error_info = self.get_error_info(error_code)

        log_message = f"[{self.provider.upper()}] 錯誤碼: {error_code} | {error_info.message}"

        if context:
            log_message += f" | 上下文: {context}"

        log_message += f" | 建議: {error_info.suggestion}"

        if error_info.category == ErrorCategory.NETWORK or error_info.category == ErrorCategory.SERVER:
            self.logger.warning(log_message)
        elif error_info.is_retryable:
            self.logger.info(log_message)
        else:
            self.logger.error(log_message)


def retry_on_error(
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    retryable_errors: Optional[List[str]] = None,
    logger: Optional[logging.Logger] = None
) -> Callable:
    """
    自動重試裝飾器 (指數退避)

    Args:
        max_retries: 最大重試次數
        backoff_factor: 退避倍數 (每次重試等待時間 = backoff_factor ** retry_count)
        retryable_errors: 可重試的錯誤碼清單
        logger: 自訂 Logger

    Returns:
        裝飾器函數

    Example:
        >>> @retry_on_error(max_retries=3, backoff_factor=2)
        ... def issue_invoice(data):
        ...     # 發票開立邏輯
        ...     pass
    """
    if retryable_errors is None:
        retryable_errors = ['10000005', 'NETWORK_ERROR', 'SERVER_ERROR', 'TIMEOUT_ERROR']

    if logger is None:
        logger = logging.getLogger('retry_decorator')
        logger.setLevel(logging.INFO)

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for retry_count in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)

                except Exception as e:
                    last_exception = e

                    # 檢查是否可重試
                    error_code = getattr(e, 'error_code', 'UNKNOWN')

                    if error_code not in retryable_errors:
                        logger.error(f"錯誤不可重試: {error_code} - {str(e)}")
                        raise

                    # 已達最大重試次數
                    if retry_count >= max_retries:
                        logger.error(f"已達最大重試次數 ({max_retries})，放棄重試")
                        raise

                    # 計算等待時間 (指數退避)
                    wait_time = backoff_factor ** retry_count

                    logger.warning(
                        f"第 {retry_count + 1}/{max_retries} 次重試失敗 ({error_code}), "
                        f"{wait_time:.1f} 秒後重試..."
                    )

                    time.sleep(wait_time)

            # 如果所有重試都失敗
            raise last_exception

        return wrapper
    return decorator


# ============================================================================
# 使用範例
# ============================================================================

if __name__ == '__main__':
    # 範例 1: 查詢錯誤資訊
    print("=== 範例 1: 查詢錯誤資訊 ===\n")

    handler = InvoiceErrorHandler(provider='ecpay')

    error_codes = ['10000006', '10000016', '10000019', 'NETWORK_ERROR']

    for code in error_codes:
        info = handler.get_error_info(code)
        print(f"錯誤碼: {info.code}")
        print(f"  訊息: {info.message}")
        print(f"  類別: {info.category.value}")
        print(f"  可重試: {'是' if info.is_retryable else '否'}")
        print(f"  建議: {info.suggestion}")
        print()

    # 範例 2: 記錄錯誤
    print("=== 範例 2: 記錄錯誤 ===\n")

    handler.log_error('10000016', context={'relate_number': 'ORD123', 'amount': 1050})
    handler.log_error('NETWORK_ERROR', context={'url': 'https://einvoice-stage.ecpay.com.tw'})

    # 範例 3: 自動重試
    print("\n=== 範例 3: 自動重試 ===\n")

    attempt = 0

    @retry_on_error(max_retries=3, backoff_factor=1.5)
    def flaky_api_call():
        """模擬不穩定的 API 呼叫"""
        nonlocal attempt
        attempt += 1

        print(f"第 {attempt} 次呼叫...")

        if attempt < 3:
            # 模擬網路錯誤
            error = Exception("網路連線失敗")
            error.error_code = 'NETWORK_ERROR'
            raise error

        return {"status": "success", "invoice_no": "AA12345678"}

    try:
        result = flaky_api_call()
        print(f"\n✓ API 呼叫成功: {result}")
    except Exception as e:
        print(f"\n✗ API 呼叫失敗: {str(e)}")

    print("\n" + "="*60)
    print("範例執行完畢!")
    print("="*60)
