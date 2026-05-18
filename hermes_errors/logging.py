"""Hermes Agent 统一日志系统

版本：1.0
创建日期：2026-04-22
"""

import logging
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Optional


class HermesLogFormatter(logging.Formatter):
    """自定义日志格式器 - 支持结构化日志"""
    
    # 颜色代码
    COLORS = {
        'DEBUG': '\033[36m',     # 青色
        'INFO': '\033[32m',      # 绿色
        'WARNING': '\033[33m',   # 黄色
        'ERROR': '\033[31m',     # 红色
        'CRITICAL': '\033[35m',  # 紫色
        'RESET': '\033[0m'       # 重置
    }
    
    # Emoji 前缀
    EMOJIS = {
        'DEBUG': '🔍',
        'INFO': 'ℹ️',
        'WARNING': '⚠️',
        'ERROR': '❌',
        'CRITICAL': '🔥'
    }
    
    def __init__(self, use_color: bool = True, include_details: bool = True):
        super().__init__()
        self.use_color = use_color
        self.include_details = include_details
    
    def format(self, record: logging.LogRecord) -> str:
        # 基础格式
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        level = record.levelname
        name = record.name
        message = record.getMessage()
        
        # 颜色
        if self.use_color:
            color = self.COLORS.get(level, self.COLORS['RESET'])
            reset = self.COLORS['RESET']
            level_display = f"{color}[{level}]{reset}"
            emoji = self.EMOJIS.get(level, '')
        else:
            level_display = f"[{level}]"
            emoji = ''
        
        # 构建日志行
        log_line = f"{timestamp} {level_display} {emoji} {name}: {message}"
        
        # 附加详细信息
        if self.include_details and hasattr(record, 'details'):
            try:
                details_json = json.dumps(record.details, ensure_ascii=False)
                log_line += f" | {details_json}"
            except (TypeError, ValueError):
                pass
        
        # 异常堆栈
        if record.exc_info:
            exc_text = self.formatException(record.exc_info)
            log_line += f"\n{exc_text}"
        
        return log_line


class StructuredLogger(logging.Logger):
    """支持结构化日志的 Logger"""
    
    def debug(self, msg, *args, details=None, **kwargs):
        if details:
            extra = kwargs.get('extra', {})
            extra['details'] = details
            kwargs['extra'] = extra
        super().debug(msg, *args, **kwargs)
    
    def info(self, msg, *args, details=None, **kwargs):
        if details:
            extra = kwargs.get('extra', {})
            extra['details'] = details
            kwargs['extra'] = extra
        super().info(msg, *args, **kwargs)
    
    def warning(self, msg, *args, details=None, **kwargs):
        if details:
            extra = kwargs.get('extra', {})
            extra['details'] = details
            kwargs['extra'] = extra
        super().warning(msg, *args, **kwargs)
    
    def error(self, msg, *args, details=None, **kwargs):
        if details:
            extra = kwargs.get('extra', {})
            extra['details'] = details
            kwargs['extra'] = extra
        super().error(msg, *args, **kwargs)
    
    def critical(self, msg, *args, details=None, **kwargs):
        if details:
            extra = kwargs.get('extra', {})
            extra['details'] = details
            kwargs['extra'] = extra
        super().critical(msg, *args, **kwargs)


def get_hermes_logger(
    name: str = 'hermes',
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    use_color: bool = True,
    include_details: bool = True
) -> StructuredLogger:
    """获取配置好的 Hermes logger
    
    Args:
        name: logger 名称
        level: 日志级别
        log_file: 日志文件路径（可选）
        use_color: 是否使用彩色输出
        include_details: 是否包含详细 JSON 信息
    
    Returns:
        配置好的 StructuredLogger 实例
    """
    # 设置 logger 类
    logging.setLoggerClass(StructuredLogger)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 避免重复添加 handler
    if logger.handlers:
        return logger
    
    # 控制台 handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = HermesLogFormatter(
        use_color=use_color,
        include_details=include_details
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # 文件 handler（可选）
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_formatter = HermesLogFormatter(
            use_color=False,
            include_details=include_details
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


# 错误恢复策略
class RecoveryStrategy:
    """错误恢复策略"""
    
    @staticmethod
    def exponential_backoff(
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0
    ):
        """指数退避重试装饰器
        
        Usage:
            @RecoveryStrategy.exponential_backoff()
            def api_call():
                ...
        """
        import time
        import functools
        
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                last_exception = None
                for attempt in range(max_retries):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        last_exception = e
                        if attempt == max_retries - 1:
                            break
                        
                        delay = min(base_delay * (2 ** attempt), max_delay)
                        logger = logging.getLogger('hermes.recovery')
                        logger.warning(
                            f"重试 {func.__name__} ({attempt + 1}/{max_retries}), "
                            f"等待 {delay:.1f}秒",
                            details={"function": func.__name__, "attempt": attempt + 1}
                        )
                        time.sleep(delay)
                
                raise last_exception
            return wrapper
        return decorator
    
    @staticmethod
    def fallback(fallback_func):
        """降级处理装饰器
        
        Usage:
            @RecoveryStrategy.fallback(lambda: cached_data)
            def fetch_data():
                ...
        """
        import functools
        
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logger = logging.getLogger('hermes.recovery')
                    logger.warning(
                        f"{func.__name__} 失败，使用降级方案",
                        details={"error": str(e)}
                    )
                    return fallback_func(*args, **kwargs)
            return wrapper
        return decorator


# 全局 logger 实例
logger = get_hermes_logger()

__all__ = [
    'HermesLogFormatter',
    'StructuredLogger',
    'get_hermes_logger',
    'RecoveryStrategy',
    'logger'
]
