#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
心娱开发助手异常处理体系

提供分层、结构化的异常处理机制：
- 基础异常类 (XinyuDevToolsError)
- 功能模块异常类 (文件操作、索引构建、UI等)
- 业务逻辑异常类 (日志解析、AI诊断等)
- 异常处理装饰器和工具函数
- 统一的错误报告和日志记录

使用示例：
    from .exceptions import (
        FileOperationError,
        LogParsingError,
        handle_exceptions
    )

    @handle_exceptions(FileOperationError)
    def load_file(filepath):
        # 文件加载逻辑
        pass
"""

import logging
import traceback
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Type, Union
from functools import wraps


class ErrorSeverity(Enum):
    """错误严重程度"""
    LOW = "low"          # 轻微错误，不影响主要功能
    MEDIUM = "medium"    # 中等错误，影响部分功能
    HIGH = "high"        # 严重错误，影响核心功能
    CRITICAL = "critical"  # 致命错误，程序无法继续


class XinyuDevToolsError(Exception):
    """
    心娱开发助手基础异常类

    所有自定义异常的基类，提供统一的错误处理接口：
    - 错误代码标准化
    - 严重程度分级
    - 上下文信息记录
    - 用户友好提示
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        cause: Optional[Exception] = None
    ):
        """
        初始化异常

        Args:
            message: 技术错误信息（用于日志和调试）
            error_code: 标准化错误代码
            severity: 错误严重程度
            context: 错误上下文信息
            user_message: 用户友好的错误提示
            cause: 原始异常（异常链）
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.severity = severity
        self.context = context or {}
        self.user_message = user_message or self._generate_user_message()
        self.cause = cause
        self.timestamp = datetime.now()

    def _generate_user_message(self) -> str:
        """生成用户友好的错误提示"""
        return f"操作失败：{self.message}"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，便于序列化和日志记录"""
        return {
            'error_type': self.__class__.__name__,
            'error_code': self.error_code,
            'message': self.message,
            'user_message': self.user_message,
            'severity': self.severity.value,
            'context': self.context,
            'timestamp': self.timestamp.isoformat(),
            'cause': str(self.cause) if self.cause else None,
            'traceback': traceback.format_exc()
        }

    def __str__(self) -> str:
        return f"[{self.error_code}] {self.message}"


# ============================================================================
# 功能模块异常类
# ============================================================================

class FileOperationError(XinyuDevToolsError):
    """文件操作相关异常"""

    def __init__(
        self,
        message: str,
        filepath: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        context = kwargs.get('context', {})
        if filepath:
            context['filepath'] = filepath
        if operation:
            context['operation'] = operation
        kwargs['context'] = context

        super().__init__(message, **kwargs)


class LogParsingError(XinyuDevToolsError):
    """日志解析相关异常"""

    def __init__(
        self,
        message: str,
        line_number: Optional[int] = None,
        line_content: Optional[str] = None,
        parsing_format: Optional[str] = None,
        **kwargs
    ):
        context = kwargs.get('context', {})
        if line_number is not None:
            context['line_number'] = line_number
        if line_content:
            context['line_content'] = line_content[:200] + "..." if len(line_content) > 200 else line_content
        if parsing_format:
            context['parsing_format'] = parsing_format
        kwargs['context'] = context

        super().__init__(message, **kwargs)


class IndexingError(XinyuDevToolsError):
    """索引构建相关异常"""

    def __init__(
        self,
        message: str,
        entry_count: Optional[int] = None,
        batch_size: Optional[int] = None,
        **kwargs
    ):
        context = kwargs.get('context', {})
        if entry_count is not None:
            context['entry_count'] = entry_count
        if batch_size is not None:
            context['batch_size'] = batch_size
        kwargs['context'] = context

        super().__init__(message, **kwargs)


class UIError(XinyuDevToolsError):
    """用户界面相关异常"""

    def __init__(
        self,
        message: str,
        widget: Optional[str] = None,
        action: Optional[str] = None,
        **kwargs
    ):
        context = kwargs.get('context', {})
        if widget:
            context['widget'] = widget
        if action:
            context['action'] = action
        kwargs['context'] = context

        super().__init__(message, **kwargs)


# ============================================================================
# 业务逻辑异常类
# ============================================================================

class DecodingError(FileOperationError):
    """解码异常"""

    def __init__(self, message: str, decoder_type: Optional[str] = None, **kwargs):
        context = kwargs.get('context', {})
        if decoder_type:
            context['decoder_type'] = decoder_type
        kwargs['context'] = context
        kwargs.setdefault('severity', ErrorSeverity.HIGH)

        super().__init__(message, **kwargs)


class ImportError(FileOperationError):
    """导入/导出异常"""

    def __init__(self, message: str, format_type: Optional[str] = None, **kwargs):
        context = kwargs.get('context', {})
        if format_type:
            context['format_type'] = format_type
        kwargs['context'] = context

        super().__init__(message, **kwargs)


class SearchError(XinyuDevToolsError):
    """搜索功能异常"""

    def __init__(
        self,
        message: str,
        search_term: Optional[str] = None,
        search_mode: Optional[str] = None,
        **kwargs
    ):
        context = kwargs.get('context', {})
        if search_term:
            context['search_term'] = search_term
        if search_mode:
            context['search_mode'] = search_mode
        kwargs['context'] = context

        super().__init__(message, **kwargs)


class AIDiagnosisError(XinyuDevToolsError):
    """AI诊断异常"""

    def __init__(
        self,
        message: str,
        ai_service: Optional[str] = None,
        request_type: Optional[str] = None,
        **kwargs
    ):
        context = kwargs.get('context', {})
        if ai_service:
            context['ai_service'] = ai_service
        if request_type:
            context['request_type'] = request_type
        kwargs['context'] = context
        kwargs.setdefault('severity', ErrorSeverity.MEDIUM)

        super().__init__(message, **kwargs)


class ConfigurationError(XinyuDevToolsError):
    """配置异常"""

    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        config_file: Optional[str] = None,
        **kwargs
    ):
        context = kwargs.get('context', {})
        if config_key:
            context['config_key'] = config_key
        if config_file:
            context['config_file'] = config_file
        kwargs['context'] = context

        super().__init__(message, **kwargs)


# ============================================================================
# iOS工具专用异常
# ============================================================================

class IPSAnalysisError(XinyuDevToolsError):
    """IPS崩溃分析异常"""

    def __init__(
        self,
        message: str,
        ips_file: Optional[str] = None,
        crash_type: Optional[str] = None,
        **kwargs
    ):
        context = kwargs.get('context', {})
        if ips_file:
            context['ips_file'] = ips_file
        if crash_type:
            context['crash_type'] = crash_type
        kwargs['context'] = context

        super().__init__(message, **kwargs)


class PushNotificationError(XinyuDevToolsError):
    """推送通知异常"""

    def __init__(
        self,
        message: str,
        device_token: Optional[str] = None,
        certificate_status: Optional[str] = None,
        **kwargs
    ):
        context = kwargs.get('context', {})
        if device_token:
            context['device_token'] = device_token[:20] + "..." if len(device_token) > 20 else device_token
        if certificate_status:
            context['certificate_status'] = certificate_status
        kwargs['context'] = context

        super().__init__(message, **kwargs)


class SandboxAccessError(XinyuDevToolsError):
    """iOS沙盒访问异常"""

    def __init__(
        self,
        message: str,
        device_id: Optional[str] = None,
        bundle_id: Optional[str] = None,
        **kwargs
    ):
        context = kwargs.get('context', {})
        if device_id:
            context['device_id'] = device_id
        if bundle_id:
            context['bundle_id'] = bundle_id
        kwargs['context'] = context

        super().__init__(message, **kwargs)


class ObfuscationError(XinyuDevToolsError):
    """代码混淆异常"""

    def __init__(
        self,
        message: str,
        project_path: Optional[str] = None,
        obfuscation_step: Optional[str] = None,
        **kwargs
    ):
        context = kwargs.get('context', {})
        if project_path:
            context['project_path'] = project_path
        if obfuscation_step:
            context['obfuscation_step'] = obfuscation_step
        kwargs['context'] = context

        super().__init__(message, **kwargs)


# ============================================================================
# 异常处理装饰器和工具函数
# ============================================================================

def get_logger() -> logging.Logger:
    """获取异常处理专用日志器"""
    return logging.getLogger('xinyu_exceptions')


def handle_exceptions(
    *exception_types: Type[Exception],
    reraise: bool = True,
    default_return: Any = None,
    log_level: int = logging.ERROR,
    show_user_message: bool = True
):
    """
    异常处理装饰器

    Args:
        exception_types: 要捕获的异常类型
        reraise: 是否重新抛出异常
        default_return: 异常时的默认返回值
        log_level: 日志级别
        show_user_message: 是否显示用户友好消息

    Usage:
        @handle_exceptions(FileOperationError, reraise=False, default_return=[])
        def load_files(file_list):
            # 文件加载逻辑
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger()

            try:
                return func(*args, **kwargs)
            except exception_types as e:
                # 如果是我们自定义的异常，直接使用
                if isinstance(e, XinyuDevToolsError):
                    logger.log(log_level, f"自定义异常: {e.to_dict()}")
                    if show_user_message:
                        logger.info(f"用户提示: {e.user_message}")
                    # 添加到全局收集器
                    _global_error_collector.add_exception(e)
                else:
                    # 将标准异常转换为我们的异常
                    custom_error = XinyuDevToolsError(
                        message=str(e),
                        context={'function': func.__name__, 'args': str(args)[:200]},
                        cause=e
                    )
                    logger.log(log_level, f"标准异常转换: {custom_error.to_dict()}")
                    # 添加到全局收集器
                    _global_error_collector.add_exception(custom_error)
                    e = custom_error

                if reraise:
                    raise e
                else:
                    return default_return
            except Exception as e:
                # 处理未预期的异常
                unexpected_error = XinyuDevToolsError(
                    message=f"未预期的异常: {str(e)}",
                    error_code="UNEXPECTED_ERROR",
                    severity=ErrorSeverity.HIGH,
                    context={'function': func.__name__, 'args': str(args)[:200]},
                    cause=e
                )
                logger.log(log_level, f"未预期异常: {unexpected_error.to_dict()}")
                # 添加到全局收集器
                _global_error_collector.add_exception(unexpected_error)

                if reraise:
                    raise unexpected_error
                else:
                    return default_return

        return wrapper
    return decorator


def safe_execute(
    func,
    *args,
    exception_types: tuple = (Exception,),
    default_return: Any = None,
    log_error: bool = True,
    **kwargs
) -> Any:
    """
    安全执行函数

    Args:
        func: 要执行的函数
        args: 位置参数
        exception_types: 要捕获的异常类型
        default_return: 异常时的默认返回值
        log_error: 是否记录错误日志
        kwargs: 关键字参数

    Returns:
        函数执行结果或默认返回值
    """
    try:
        return func(*args, **kwargs)
    except exception_types as e:
        if log_error:
            logger = get_logger()
            logger.error(f"安全执行失败: {func.__name__}, 错误: {str(e)}")
        return default_return


class ExceptionCollector:
    """异常收集器，用于批量处理异常"""

    def __init__(self):
        self.exceptions: List[XinyuDevToolsError] = []
        self.max_exceptions = 100  # 最大收集数量

    def add_exception(self, exception: Union[Exception, XinyuDevToolsError], context: Optional[Dict] = None):
        """添加异常到收集器"""
        if not isinstance(exception, XinyuDevToolsError):
            # 转换为自定义异常
            exception = XinyuDevToolsError(
                message=str(exception),
                context=context or {},
                cause=exception
            )

        self.exceptions.append(exception)

        # 限制异常数量
        if len(self.exceptions) > self.max_exceptions:
            self.exceptions = self.exceptions[-self.max_exceptions:]

    def get_summary(self) -> Dict[str, Any]:
        """获取异常汇总信息"""
        if not self.exceptions:
            return {'total': 0, 'by_severity': {}, 'by_type': {}}

        by_severity = {}
        by_type = {}

        for exc in self.exceptions:
            # 按严重程度统计
            severity = exc.severity.value
            by_severity[severity] = by_severity.get(severity, 0) + 1

            # 按类型统计
            exc_type = exc.__class__.__name__
            by_type[exc_type] = by_type.get(exc_type, 0) + 1

        return {
            'total': len(self.exceptions),
            'by_severity': by_severity,
            'by_type': by_type,
            'latest': self.exceptions[-1].to_dict() if self.exceptions else None
        }

    def get_statistics(self) -> Dict[str, Any]:
        """获取异常统计信息（兼容旧版本）"""
        return {
            'total_exceptions': len(self.exceptions),
            'severity_distribution': self.get_summary().get('by_severity', {}),
            'type_distribution': self.get_summary().get('by_type', {})
        }

    def get_exceptions(self) -> List[XinyuDevToolsError]:
        """获取所有异常"""
        return self.exceptions.copy()

    def clear(self):
        """清空异常收集器"""
        self.exceptions.clear()

    def has_critical_errors(self) -> bool:
        """是否有严重错误"""
        return any(exc.severity == ErrorSeverity.CRITICAL for exc in self.exceptions)


# ============================================================================
# 错误报告生成器
# ============================================================================

class ErrorReporter:
    """错误报告生成器"""

    def __init__(self):
        self.collector = ExceptionCollector()

    def generate_report(self, output_file: Optional[str] = None) -> str:
        """生成错误报告"""
        summary = self.collector.get_summary()

        report_lines = [
            "=" * 80,
            "心娱开发助手错误报告",
            "=" * 80,
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"异常总数: {summary['total']}",
            "",
            "按严重程度统计:",
        ]

        for severity, count in summary['by_severity'].items():
            report_lines.append(f"  {severity}: {count}")

        report_lines.extend([
            "",
            "按异常类型统计:",
        ])

        for exc_type, count in summary['by_type'].items():
            report_lines.append(f"  {exc_type}: {count}")

        if summary['latest']:
            report_lines.extend([
                "",
                "最新异常详情:",
                "-" * 40,
            ])
            latest = summary['latest']
            for key, value in latest.items():
                if key != 'traceback':  # 追踪信息太长，单独显示
                    report_lines.append(f"{key}: {value}")

        report_text = "\n".join(report_lines)

        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(report_text)
            except Exception as e:
                get_logger().error(f"保存错误报告失败: {e}")

        return report_text


# ============================================================================
# 全局异常处理器
# ============================================================================

_global_error_collector = ExceptionCollector()
_global_error_reporter = ErrorReporter()


def get_global_error_collector() -> ExceptionCollector:
    """获取全局异常收集器"""
    return _global_error_collector


def get_global_error_reporter() -> ErrorReporter:
    """获取全局错误报告生成器"""
    return _global_error_reporter


def clear_global_collector():
    """清空全局异常收集器"""
    _global_error_collector.clear()


def setup_global_exception_handler():
    """设置全局异常处理器"""
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            # 键盘中断，正常退出
            return

        # 转换为自定义异常
        error = XinyuDevToolsError(
            message=f"全局未处理异常: {exc_value}",
            error_code="GLOBAL_UNHANDLED",
            severity=ErrorSeverity.CRITICAL,
            context={
                'exception_type': exc_type.__name__,
                'function': exc_traceback.tb_frame.f_code.co_name if exc_traceback else None
            },
            cause=exc_value
        )

        _global_error_collector.add_exception(error)

        logger = get_logger()
        logger.critical(f"全局异常: {error.to_dict()}")

    # 设置全局异常处理器
    import sys
    sys.excepthook = handle_exception