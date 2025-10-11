#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
结构化日志配置模块
提供统一的日志记录接口，提升调试和问题追踪效率
"""

import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler


class PerformanceLogger:
    """性能日志记录器"""

    def __init__(self, name='mars_analyzer'):
        self.logger = logging.getLogger(name)
        self._setup_logger()

    def _setup_logger(self):
        """配置日志记录器"""
        # 如果已经配置过，跳过
        if self.logger.handlers:
            return

        self.logger.setLevel(logging.DEBUG)

        # 创建日志目录
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'logs')
        os.makedirs(log_dir, exist_ok=True)

        # 日志文件路径
        log_file = os.path.join(log_dir, 'analyzer.log')

        # 文件处理器（带轮转）- 最多保留5个10MB的文件
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)

        # 控制台处理器（只输出WARNING及以上）
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.WARNING)

        # 日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def debug(self, msg, *args, **kwargs):
        """调试日志"""
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        """信息日志"""
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        """警告日志"""
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        """错误日志"""
        self.logger.error(msg, *args, **kwargs, exc_info=True)

    def critical(self, msg, *args, **kwargs):
        """严重错误日志"""
        self.logger.critical(msg, *args, **kwargs, exc_info=True)

    def performance(self, operation, duration, **metrics):
        """性能日志 - 记录操作耗时和指标"""
        msg = f"Performance: {operation} took {duration:.3f}s"
        if metrics:
            metrics_str = ", ".join(f"{k}={v}" for k, v in metrics.items())
            msg += f" | {metrics_str}"
        self.logger.info(msg)

    def exception(self, msg, *args, **kwargs):
        """异常日志 - 自动包含堆栈信息"""
        self.logger.exception(msg, *args, **kwargs)


# 全局日志实例
_logger = None


def get_logger(name='mars_analyzer'):
    """获取全局日志实例

    Args:
        name: 日志记录器名称

    Returns:
        PerformanceLogger实例
    """
    global _logger
    if _logger is None:
        _logger = PerformanceLogger(name)
    return _logger


def log_performance(func):
    """性能日志装饰器

    自动记录函数执行时间

    Example:
        @log_performance
        def load_file(path):
            ...
    """
    import functools
    import time

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger()
        start_time = time.time()

        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time

            # 记录性能
            func_name = f"{func.__module__}.{func.__name__}"
            logger.performance(func_name, duration)

            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"{func.__name__} failed after {duration:.3f}s: {e}")
            raise

    return wrapper


def log_call(func):
    """调用日志装饰器

    记录函数调用和参数

    Example:
        @log_call
        def process_data(data, mode='fast'):
            ...
    """
    import functools

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger()

        # 构建参数字符串
        args_str = ", ".join(repr(a) for a in args[:3])  # 只记录前3个参数
        if len(args) > 3:
            args_str += f", ... ({len(args)} args total)"

        kwargs_str = ", ".join(f"{k}={repr(v)}" for k, v in list(kwargs.items())[:3])
        if len(kwargs) > 3:
            kwargs_str += f", ... ({len(kwargs)} kwargs total)"

        params = ", ".join(filter(None, [args_str, kwargs_str]))

        logger.debug(f"Calling {func.__name__}({params})")

        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} raised {type(e).__name__}: {e}")
            raise

    return wrapper


class LogContext:
    """日志上下文管理器

    自动记录代码块的执行时间和结果

    Example:
        with LogContext("Loading file") as ctx:
            data = load_file(path)
            ctx.info(f"Loaded {len(data)} entries")
    """

    def __init__(self, operation_name, logger=None):
        self.operation_name = operation_name
        self.logger = logger or get_logger()
        self.start_time = None

    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.debug(f"Starting: {self.operation_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds()

        if exc_type is None:
            self.logger.performance(self.operation_name, duration)
        else:
            self.logger.error(
                f"{self.operation_name} failed after {duration:.3f}s: {exc_val}"
            )
        return False  # 不抑制异常

    def debug(self, msg):
        """在上下文中记录调试信息"""
        self.logger.debug(f"[{self.operation_name}] {msg}")

    def info(self, msg):
        """在上下文中记录信息"""
        self.logger.info(f"[{self.operation_name}] {msg}")

    def warning(self, msg):
        """在上下文中记录警告"""
        self.logger.warning(f"[{self.operation_name}] {msg}")


# 便捷函数
def debug(msg, *args, **kwargs):
    """快捷调试日志"""
    get_logger().debug(msg, *args, **kwargs)


def info(msg, *args, **kwargs):
    """快捷信息日志"""
    get_logger().info(msg, *args, **kwargs)


def warning(msg, *args, **kwargs):
    """快捷警告日志"""
    get_logger().warning(msg, *args, **kwargs)


def error(msg, *args, **kwargs):
    """快捷错误日志"""
    get_logger().error(msg, *args, **kwargs)


def critical(msg, *args, **kwargs):
    """快捷严重错误日志"""
    get_logger().critical(msg, *args, **kwargs)


def performance(operation, duration, **metrics):
    """快捷性能日志"""
    get_logger().performance(operation, duration, **metrics)


# 使用示例
if __name__ == "__main__":
    # 示例1: 基本使用
    logger = get_logger()
    logger.info("Application started")
    logger.debug("Debug information")
    logger.warning("This is a warning")

    # 示例2: 性能日志
    import time

    @log_performance
    def example_function():
        time.sleep(0.1)
        return "Done"

    result = example_function()

    # 示例3: 上下文管理器
    with LogContext("Example operation") as ctx:
        ctx.info("Processing data")
        time.sleep(0.05)
        ctx.info("Data processed")

    # 示例4: 手动性能记录
    start = time.time()
    # ... 执行操作 ...
    time.sleep(0.02)
    duration = time.time() - start
    performance("Manual operation", duration, count=100, size="10MB")

    # 示例5: 异常记录
    try:
        1 / 0
    except Exception as e:
        logger.exception("An error occurred")

    print("\n日志已写入 logs/analyzer.log")
