#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
性能分析器

提供性能监控和分析功能，帮助识别性能瓶颈和优化机会。

功能特性：
- 函数执行时间追踪
- 内存使用追踪
- 性能报告生成
- 装饰器和上下文管理器支持

使用示例：
    >>> profiler = PerformanceProfiler()
    >>>
    >>> @profiler.profile("函数名称")
    >>> def my_function():
    ...     # 函数代码
    ...     pass
    >>>
    >>> # 或使用上下文管理器
    >>> with profiler.measure("操作名称"):
    ...     # 代码块
    ...     pass
    >>>
    >>> # 打印报告
    >>> profiler.print_report()

作者：开发团队
创建日期：2025-10-15
版本：v1.0.0
"""

import time
import tracemalloc
from functools import wraps
from typing import Dict, List, Optional, Callable, Any
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
import json


@dataclass
class PerformanceMetric:
    """性能指标"""
    name: str                      # 操作名称
    elapsed_time: float            # 耗时（秒）
    memory_current: float          # 当前内存（MB）
    memory_peak: float             # 峰值内存（MB）
    call_count: int = 1            # 调用次数
    total_time: float = 0.0        # 累计时间
    avg_time: float = 0.0          # 平均时间
    min_time: float = float('inf') # 最小时间
    max_time: float = 0.0          # 最大时间

    def __post_init__(self):
        """初始化计算字段"""
        if self.total_time == 0.0:
            self.total_time = self.elapsed_time
        if self.avg_time == 0.0:
            self.avg_time = self.elapsed_time
        if self.min_time == float('inf'):
            self.min_time = self.elapsed_time
        if self.max_time == 0.0:
            self.max_time = self.elapsed_time

    def update(self, elapsed_time: float, memory_current: float, memory_peak: float):
        """更新指标（用于多次调用）"""
        self.call_count += 1
        self.total_time += elapsed_time
        self.avg_time = self.total_time / self.call_count
        self.min_time = min(self.min_time, elapsed_time)
        self.max_time = max(self.max_time, elapsed_time)
        self.elapsed_time = elapsed_time
        self.memory_current = memory_current
        self.memory_peak = max(self.memory_peak, memory_peak)


class PerformanceProfiler:
    """
    性能分析器

    提供性能监控和分析功能。

    特性：
    - 函数执行时间追踪
    - 内存使用追踪
    - 多次调用统计
    - 性能报告生成

    属性：
        metrics: 性能指标字典
        enabled: 是否启用分析
    """

    def __init__(self, enabled: bool = True):
        """
        初始化性能分析器

        Args:
            enabled: 是否启用性能分析
        """
        self.metrics: Dict[str, PerformanceMetric] = {}
        self.enabled = enabled
        self._tracking_started = False

    def start_tracking(self):
        """开始内存追踪"""
        if self.enabled and not self._tracking_started:
            try:
                tracemalloc.start()
                self._tracking_started = True
            except Exception:
                pass  # 可能已经启动

    def stop_tracking(self):
        """停止内存追踪"""
        if self._tracking_started:
            try:
                tracemalloc.stop()
                self._tracking_started = False
            except Exception:
                pass

    def profile(self, name: str):
        """
        性能分析装饰器

        Args:
            name: 操作名称

        Example:
            >>> profiler = PerformanceProfiler()
            >>> @profiler.profile("加载文件")
            >>> def load_file(path):
            ...     # 文件加载代码
            ...     pass
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                if not self.enabled:
                    return func(*args, **kwargs)

                # 开始追踪
                self.start_tracking()
                start_time = time.time()

                try:
                    # 执行函数
                    result = func(*args, **kwargs)

                    # 收集指标
                    elapsed = time.time() - start_time

                    current = peak = 0.0
                    try:
                        if self._tracking_started:
                            current, peak = tracemalloc.get_traced_memory()
                            current = current / 1024 / 1024  # 转换为MB
                            peak = peak / 1024 / 1024
                    except Exception:
                        pass

                    # 更新或创建指标
                    if name in self.metrics:
                        self.metrics[name].update(elapsed, current, peak)
                    else:
                        self.metrics[name] = PerformanceMetric(
                            name=name,
                            elapsed_time=elapsed,
                            memory_current=current,
                            memory_peak=peak
                        )

                    return result

                except Exception as e:
                    # 即使出错也记录时间
                    elapsed = time.time() - start_time
                    if name in self.metrics:
                        self.metrics[name].update(elapsed, 0, 0)
                    raise e

            return wrapper
        return decorator

    @contextmanager
    def measure(self, name: str):
        """
        性能测量上下文管理器

        Args:
            name: 操作名称

        Example:
            >>> profiler = PerformanceProfiler()
            >>> with profiler.measure("数据处理"):
            ...     # 数据处理代码
            ...     process_data()
        """
        if not self.enabled:
            yield
            return

        # 开始追踪
        self.start_tracking()
        start_time = time.time()

        try:
            yield

            # 收集指标
            elapsed = time.time() - start_time

            current = peak = 0.0
            try:
                if self._tracking_started:
                    current, peak = tracemalloc.get_traced_memory()
                    current = current / 1024 / 1024
                    peak = peak / 1024 / 1024
            except Exception:
                pass

            # 更新或创建指标
            if name in self.metrics:
                self.metrics[name].update(elapsed, current, peak)
            else:
                self.metrics[name] = PerformanceMetric(
                    name=name,
                    elapsed_time=elapsed,
                    memory_current=current,
                    memory_peak=peak
                )

        except Exception as e:
            # 即使出错也记录时间
            elapsed = time.time() - start_time
            if name in self.metrics:
                self.metrics[name].update(elapsed, 0, 0)
            raise e

    def get_metric(self, name: str) -> Optional[PerformanceMetric]:
        """获取指定指标"""
        return self.metrics.get(name)

    def get_all_metrics(self) -> Dict[str, PerformanceMetric]:
        """获取所有指标"""
        return self.metrics.copy()

    def get_sorted_metrics(self, by: str = 'total_time', reverse: bool = True) -> List[PerformanceMetric]:
        """
        获取排序后的指标列表

        Args:
            by: 排序字段 ('total_time', 'avg_time', 'memory_peak', 'call_count')
            reverse: 是否降序

        Returns:
            排序后的指标列表
        """
        return sorted(
            self.metrics.values(),
            key=lambda m: getattr(m, by, 0),
            reverse=reverse
        )

    def print_report(self, top_n: int = None, sort_by: str = 'total_time'):
        """
        打印性能报告

        Args:
            top_n: 只显示前N个（None表示全部）
            sort_by: 排序字段
        """
        if not self.metrics:
            print("没有性能数据")
            return

        print("\n" + "="*80)
        print("性能分析报告")
        print("="*80)

        # 获取排序后的指标
        sorted_metrics = self.get_sorted_metrics(by=sort_by, reverse=True)
        if top_n:
            sorted_metrics = sorted_metrics[:top_n]

        # 打印表头
        print(f"\n{'操作名称':<30} {'调用次数':<10} {'总时间':<12} {'平均时间':<12} {'峰值内存':<12}")
        print("-"*80)

        # 打印数据
        for metric in sorted_metrics:
            print(f"{metric.name:<30} "
                  f"{metric.call_count:<10} "
                  f"{metric.total_time:<12.3f}s "
                  f"{metric.avg_time:<12.3f}s "
                  f"{metric.memory_peak:<12.2f}MB")

        # 打印总结
        total_time = sum(m.total_time for m in self.metrics.values())
        total_calls = sum(m.call_count for m in self.metrics.values())

        print("-"*80)
        print(f"总计: {len(self.metrics)} 个操作, {total_calls} 次调用, {total_time:.3f}秒")
        print("="*80 + "\n")

    def print_detailed_report(self):
        """打印详细报告"""
        if not self.metrics:
            print("没有性能数据")
            return

        print("\n" + "="*80)
        print("详细性能分析报告")
        print("="*80)

        for name, metric in self.metrics.items():
            print(f"\n📊 {name}:")
            print(f"  调用次数: {metric.call_count}")
            print(f"  总时间:   {metric.total_time:.3f}秒")
            print(f"  平均时间: {metric.avg_time:.3f}秒")
            print(f"  最小时间: {metric.min_time:.3f}秒")
            print(f"  最大时间: {metric.max_time:.3f}秒")
            print(f"  当前内存: {metric.memory_current:.2f}MB")
            print(f"  峰值内存: {metric.memory_peak:.2f}MB")

        print("\n" + "="*80 + "\n")

    def export_report(self, output_file: str, format: str = 'json'):
        """
        导出性能报告

        Args:
            output_file: 输出文件路径
            format: 导出格式 ('json' 或 'csv')
        """
        if format == 'json':
            self._export_json(output_file)
        elif format == 'csv':
            self._export_csv(output_file)
        else:
            raise ValueError(f"不支持的格式: {format}")

    def _export_json(self, output_file: str):
        """导出为JSON格式"""
        data = {
            'metrics': [
                {
                    'name': m.name,
                    'call_count': m.call_count,
                    'total_time': m.total_time,
                    'avg_time': m.avg_time,
                    'min_time': m.min_time,
                    'max_time': m.max_time,
                    'memory_current': m.memory_current,
                    'memory_peak': m.memory_peak,
                }
                for m in self.metrics.values()
            ],
            'summary': {
                'total_operations': len(self.metrics),
                'total_calls': sum(m.call_count for m in self.metrics.values()),
                'total_time': sum(m.total_time for m in self.metrics.values()),
            }
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"性能报告已导出: {output_file}")

    def _export_csv(self, output_file: str):
        """导出为CSV格式"""
        import csv

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # 写入表头
            writer.writerow([
                '操作名称', '调用次数', '总时间(秒)', '平均时间(秒)',
                '最小时间(秒)', '最大时间(秒)', '当前内存(MB)', '峰值内存(MB)'
            ])

            # 写入数据
            for metric in self.metrics.values():
                writer.writerow([
                    metric.name,
                    metric.call_count,
                    f"{metric.total_time:.3f}",
                    f"{metric.avg_time:.3f}",
                    f"{metric.min_time:.3f}",
                    f"{metric.max_time:.3f}",
                    f"{metric.memory_current:.2f}",
                    f"{metric.memory_peak:.2f}",
                ])

        print(f"性能报告已导出: {output_file}")

    def reset(self):
        """重置所有指标"""
        self.metrics.clear()

    def enable(self):
        """启用性能分析"""
        self.enabled = True

    def disable(self):
        """禁用性能分析"""
        self.enabled = False
        if self._tracking_started:
            self.stop_tracking()


# ============================================================================
# 使用示例和测试
# ============================================================================

def example_usage():
    """使用示例"""
    print("性能分析器使用示例\n")

    profiler = PerformanceProfiler()

    # 示例1: 使用装饰器
    @profiler.profile("计算斐波那契数列")
    def fibonacci(n):
        if n <= 1:
            return n
        return fibonacci(n-1) + fibonacci(n-2)

    # 示例2: 使用上下文管理器
    with profiler.measure("数据处理"):
        data = [i**2 for i in range(10000)]
        result = sum(data)

    # 示例3: 多次调用
    @profiler.profile("列表排序")
    def sort_list(data):
        return sorted(data)

    for i in range(5):
        sort_list(list(range(1000, 0, -1)))

    # 打印报告
    profiler.print_report()
    profiler.print_detailed_report()


if __name__ == '__main__':
    print("性能分析器 v1.0.0")
    print("提供性能监控和分析功能")
    print()

    # 运行示例
    example_usage()
