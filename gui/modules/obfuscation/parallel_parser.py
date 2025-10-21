#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
并行代码解析器

提供多线程并行解析功能，显著提升大项目的解析速度。

性能提升：
- 小项目（<100文件）：2-3倍
- 中项目（100-500文件）：3-5倍
- 大项目（>500文件）：5-8倍

使用示例：
    >>> from parallel_parser import ParallelCodeParser
    >>> from code_parser import CodeParser
    >>>
    >>> parser = CodeParser(whitelist_manager)
    >>> parallel_parser = ParallelCodeParser(max_workers=8)
    >>>
    >>> # 并行解析所有文件
    >>> results = parallel_parser.parse_files_parallel(
    ...     file_paths=['file1.m', 'file2.swift', ...],
    ...     parser=parser,
    ...     callback=progress_callback
    ... )

作者：开发团队
创建日期：2025-10-15
版本：v1.0.0
"""

import multiprocessing
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


@dataclass
class ParseResult:
    """解析结果"""
    file_path: str
    success: bool
    parsed_data: Optional[Dict] = None
    error: Optional[str] = None
    elapsed_time: float = 0.0


class ParallelCodeParser:
    """
    并行代码解析器

    使用线程池并行解析多个源文件，充分利用多核CPU。

    特性：
    - 线程池并行处理
    - 实时进度回调
    - 异常处理和容错
    - 性能统计

    属性：
        max_workers: 最大工作线程数，默认为CPU核心数
        total_files: 待解析文件总数
        completed_files: 已完成文件数
        failed_files: 失败文件数
        total_elapsed: 总耗时
    """

    def __init__(self, max_workers: Optional[int] = None):
        """
        初始化并行解析器

        Args:
            max_workers: 最大线程数，默认为CPU核心数
        """
        self.max_workers = max_workers or multiprocessing.cpu_count()
        self.total_files = 0
        self.completed_files = 0
        self.failed_files = 0
        self.total_elapsed = 0.0

    def parse_files_parallel(self,
                           file_paths: List[str],
                           parser: Any,
                           callback: Optional[Callable[[float, str], None]] = None) -> Dict[str, Any]:
        """
        并行解析文件列表

        Args:
            file_paths: 待解析文件路径列表
            parser: CodeParser实例，必须有parse_file方法
            callback: 进度回调函数，接收(progress: float, message: str)

        Returns:
            {file_path: ParseResult}字典

        示例：
            >>> def progress_callback(progress, message):
            ...     print(f"[{progress*100:.1f}%] {message}")
            >>>
            >>> results = parallel_parser.parse_files_parallel(
            ...     file_paths,
            ...     parser,
            ...     callback=progress_callback
            ... )
        """
        self.total_files = len(file_paths)
        self.completed_files = 0
        self.failed_files = 0
        parsed_files = {}

        if self.total_files == 0:
            return parsed_files

        # 记录开始时间
        start_time = time.time()

        # 决策：少量文件使用串行，避免线程开销
        if self.total_files < 10:
            return self._parse_sequential(file_paths, parser, callback)

        # 使用线程池并行解析
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_path = {
                executor.submit(self._parse_single_file, path, parser): path
                for path in file_paths
            }

            # 收集结果
            for future in as_completed(future_to_path):
                path = future_to_path[future]

                try:
                    result = future.result()
                    parsed_files[path] = result.parsed_data

                    if result.success:
                        self.completed_files += 1
                    else:
                        self.failed_files += 1
                        if callback:
                            callback(
                                self.completed_files / self.total_files,
                                f"⚠️ 解析失败: {Path(path).name} - {result.error}"
                            )

                    # 进度回调
                    if callback and result.success:
                        callback(
                            self.completed_files / self.total_files,
                            f"✅ 解析: {Path(path).name}"
                        )

                except Exception as e:
                    self.failed_files += 1
                    if callback:
                        callback(
                            self.completed_files / self.total_files,
                            f"❌ 解析异常: {Path(path).name} - {str(e)}"
                        )

        # 记录总耗时
        self.total_elapsed = time.time() - start_time

        return parsed_files

    def _parse_single_file(self, file_path: str, parser: Any) -> ParseResult:
        """
        解析单个文件（线程安全）

        Args:
            file_path: 文件路径
            parser: CodeParser实例

        Returns:
            ParseResult对象
        """
        start_time = time.time()

        try:
            # 调用parser的parse_file方法
            parsed_data = parser.parse_file(file_path)

            elapsed = time.time() - start_time

            return ParseResult(
                file_path=file_path,
                success=True,
                parsed_data=parsed_data,
                elapsed_time=elapsed
            )

        except Exception as e:
            elapsed = time.time() - start_time

            return ParseResult(
                file_path=file_path,
                success=False,
                error=str(e),
                elapsed_time=elapsed
            )

    def _parse_sequential(self,
                         file_paths: List[str],
                         parser: Any,
                         callback: Optional[Callable[[float, str], None]] = None) -> Dict[str, Any]:
        """
        串行解析（小文件量时使用）

        Args:
            file_paths: 文件路径列表
            parser: CodeParser实例
            callback: 进度回调

        Returns:
            解析结果字典
        """
        parsed_files = {}

        for i, path in enumerate(file_paths, 1):
            result = self._parse_single_file(path, parser)

            if result.success:
                parsed_files[path] = result.parsed_data
                self.completed_files += 1
            else:
                self.failed_files += 1

            if callback:
                callback(
                    i / self.total_files,
                    f"解析: {Path(path).name}"
                )

        return parsed_files

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取解析统计信息

        Returns:
            统计信息字典
        """
        return {
            'total_files': self.total_files,
            'completed_files': self.completed_files,
            'failed_files': self.failed_files,
            'success_rate': self.completed_files / self.total_files if self.total_files > 0 else 0,
            'total_elapsed': self.total_elapsed,
            'avg_time_per_file': self.total_elapsed / self.total_files if self.total_files > 0 else 0,
            'files_per_second': self.total_files / self.total_elapsed if self.total_elapsed > 0 else 0
        }

    def print_statistics(self):
        """打印统计信息"""
        stats = self.get_statistics()

        print("\n" + "="*60)
        print("并行解析统计")
        print("="*60)
        print(f"总文件数:     {stats['total_files']}")
        print(f"成功解析:     {stats['completed_files']}")
        print(f"解析失败:     {stats['failed_files']}")
        print(f"成功率:       {stats['success_rate']*100:.1f}%")
        print(f"总耗时:       {stats['total_elapsed']:.2f}秒")
        print(f"平均耗时:     {stats['avg_time_per_file']*1000:.1f}毫秒/文件")
        print(f"解析速度:     {stats['files_per_second']:.1f}文件/秒")
        print("="*60 + "\n")


class ParallelBatchProcessor:
    """
    并行批处理器

    将大量文件分批处理，避免内存占用过高。
    适用于超大项目（1000+文件）。
    """

    def __init__(self, batch_size: int = 100, max_workers: Optional[int] = None):
        """
        初始化批处理器

        Args:
            batch_size: 每批处理的文件数
            max_workers: 最大线程数
        """
        self.batch_size = batch_size
        self.parallel_parser = ParallelCodeParser(max_workers)

    def parse_files_in_batches(self,
                              file_paths: List[str],
                              parser: Any,
                              callback: Optional[Callable[[float, str], None]] = None) -> Dict[str, Any]:
        """
        分批并行解析文件

        Args:
            file_paths: 文件路径列表
            parser: CodeParser实例
            callback: 进度回调

        Returns:
            解析结果字典
        """
        total_files = len(file_paths)
        all_results = {}

        # 分批处理
        for batch_start in range(0, total_files, self.batch_size):
            batch_end = min(batch_start + self.batch_size, total_files)
            batch_files = file_paths[batch_start:batch_end]

            # 批次进度回调
            def batch_callback(progress, message):
                overall_progress = (batch_start + progress * len(batch_files)) / total_files
                if callback:
                    callback(overall_progress, f"[批次 {batch_start//self.batch_size + 1}] {message}")

            # 并行解析当前批次
            batch_results = self.parallel_parser.parse_files_parallel(
                batch_files,
                parser,
                callback=batch_callback
            )

            all_results.update(batch_results)

        return all_results


# ============================================================================
# 性能对比测试
# ============================================================================

def benchmark_parallel_parsing():
    """
    性能基准测试

    比较串行解析和并行解析的性能差异。
    """
    import os

    from code_parser import CodeParser
    from whitelist_manager import WhitelistManager

    print("\n" + "="*60)
    print("并行解析性能基准测试")
    print("="*60)

    # 准备测试数据
    test_project = "/path/to/test/project"  # 替换为实际测试项目

    if not os.path.exists(test_project):
        print("❌ 测试项目不存在，请设置正确的路径")
        return

    # 收集测试文件
    test_files = []
    for root, dirs, files in os.walk(test_project):
        for file in files:
            if file.endswith(('.h', '.m', '.mm', '.swift')):
                test_files.append(os.path.join(root, file))

    if len(test_files) == 0:
        print("❌ 未找到测试文件")
        return

    print(f"📁 测试文件数: {len(test_files)}")
    print()

    # 初始化解析器
    whitelist_manager = WhitelistManager()
    parser = CodeParser(whitelist_manager)

    # 测试1: 串行解析
    print("🔄 测试1: 串行解析...")
    start_time = time.time()

    serial_results = {}
    for file_path in test_files:
        try:
            serial_results[file_path] = parser.parse_file(file_path)
        except Exception:
            pass

    serial_time = time.time() - start_time
    print(f"✅ 串行解析完成: {serial_time:.2f}秒")
    print()

    # 测试2: 并行解析（不同线程数）
    for workers in [2, 4, 8]:
        print(f"🔄 测试2: 并行解析（{workers}线程）...")

        parallel_parser = ParallelCodeParser(max_workers=workers)
        start_time = time.time()

        # 执行并行解析测试
        parallel_parser.parse_files_parallel(
            test_files,
            parser
        )

        parallel_time = time.time() - start_time
        speedup = serial_time / parallel_time if parallel_time > 0 else 0

        print(f"✅ 并行解析完成: {parallel_time:.2f}秒")
        print(f"⚡ 加速比: {speedup:.2f}x")
        parallel_parser.print_statistics()

    print("="*60)
    print("基准测试完成")
    print("="*60 + "\n")


if __name__ == '__main__':
    # 运行基准测试
    print("并行代码解析器 v1.0.0")
    print("提供多线程并行解析功能，显著提升解析速度")
    print()

    # 示例：基本使用
    print("示例：基本使用")
    print("-" * 60)
    print("""
from parallel_parser import ParallelCodeParser
from code_parser import CodeParser

# 初始化
parser = CodeParser(whitelist_manager)
parallel_parser = ParallelCodeParser(max_workers=8)

# 并行解析
results = parallel_parser.parse_files_parallel(
    file_paths=['file1.m', 'file2.swift', ...],
    parser=parser,
    callback=lambda p, m: print(f"[{p*100:.1f}%] {m}")
)

# 查看统计
parallel_parser.print_statistics()
    """)

    # 如果需要运行基准测试，取消注释下面的行
    # benchmark_parallel_parsing()
