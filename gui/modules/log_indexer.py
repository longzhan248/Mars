#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志索引系统 - 阶段二性能优化

提供倒排索引功能，大幅提升日志搜索速度：
- 词索引：快速定位包含特定词的日志行
- Trigram索引：支持模糊搜索和部分匹配
- 增量更新：支持动态添加日志时更新索引
- 后台构建：不阻塞UI的异步索引构建

性能目标：
- 100万条日志索引构建时间 < 3秒
- 搜索响应时间 < 50ms
- 内存开销 < 原数据的20%
"""

import re
import threading
from collections import defaultdict
from typing import Set, List, Dict, Optional, Callable
import time


class LogIndexer:
    """
    日志倒排索引器

    核心功能：
    1. 构建词索引：每个词 -> 包含该词的日志行号集合
    2. 构建Trigram索引：支持模糊搜索
    3. 异步构建：后台线程构建索引，不阻塞UI
    4. 增量更新：支持动态添加新日志

    使用示例：
        indexer = LogIndexer()
        indexer.build_index_async(entries, callback=progress_callback)
        results = indexer.search("ERROR")
    """

    def __init__(self):
        # 词索引：{词: {行号集合}}
        self.word_index: Dict[str, Set[int]] = defaultdict(set)

        # Trigram索引：{trigram: {行号集合}}
        # 用于模糊搜索，例如搜索"erro"可以找到"error"
        self.trigram_index: Dict[str, Set[int]] = defaultdict(set)

        # 模块索引：{模块名: {行号集合}}
        self.module_index: Dict[str, Set[int]] = defaultdict(set)

        # 级别索引：{日志级别: {行号集合}}
        self.level_index: Dict[str, Set[int]] = defaultdict(set)

        # 时间范围索引（可选，用于时间范围快速过滤）
        self.time_index: Dict[str, Set[int]] = defaultdict(set)  # {日期: {行号}}

        # 索引状态
        self.is_building = False
        self.is_ready = False
        self.total_entries = 0

        # 构建线程
        self._build_thread: Optional[threading.Thread] = None

        # 停止标志
        self._stop_flag = False

    def build_index(self, entries: List, progress_callback: Optional[Callable[[int, int], None]] = None):
        """
        构建索引（同步方法）

        Args:
            entries: LogEntry对象列表
            progress_callback: 进度回调函数 callback(current, total)
        """
        self.is_building = True
        self.is_ready = False
        self._stop_flag = False

        self.total_entries = len(entries)

        # 清空现有索引
        self.word_index.clear()
        self.trigram_index.clear()
        self.module_index.clear()
        self.level_index.clear()
        self.time_index.clear()

        # 批量构建索引
        batch_size = 1000
        for i in range(0, len(entries), batch_size):
            if self._stop_flag:
                break

            batch = entries[i:i+batch_size]
            for idx, entry in enumerate(batch):
                line_number = i + idx
                self._index_entry(entry, line_number)

            # 进度回调
            if progress_callback:
                progress_callback(min(i + batch_size, len(entries)), len(entries))

        self.is_building = False
        self.is_ready = not self._stop_flag

    def build_index_async(self, entries: List, progress_callback: Optional[Callable[[int, int], None]] = None,
                          complete_callback: Optional[Callable[[], None]] = None):
        """
        异步构建索引（后台线程）

        Args:
            entries: LogEntry对象列表
            progress_callback: 进度回调函数
            complete_callback: 完成回调函数
        """
        def _build_worker():
            self.build_index(entries, progress_callback)
            if complete_callback:
                complete_callback()

        self._build_thread = threading.Thread(target=_build_worker, daemon=True)
        self._build_thread.start()

    def _index_entry(self, entry, line_number: int):
        """
        为单个日志条目建立索引

        Args:
            entry: LogEntry对象
            line_number: 日志行号
        """
        # 1. 索引日志内容的词
        content = entry.content or entry.raw_line
        if content:
            words = self._tokenize(content.lower())
            for word in words:
                self.word_index[word].add(line_number)

                # 构建trigram索引（用于模糊搜索）
                if len(word) >= 3:
                    for i in range(len(word) - 2):
                        trigram = word[i:i+3]
                        self.trigram_index[trigram].add(line_number)

        # 2. 索引模块
        if entry.module:
            self.module_index[entry.module].add(line_number)

        # 3. 索引级别
        if entry.level:
            self.level_index[entry.level].add(line_number)

        # 4. 索引时间（按日期）
        if entry.timestamp:
            # 提取日期部分 YYYY-MM-DD
            date_match = re.match(r'(\d{4}-\d{2}-\d{2})', entry.timestamp)
            if date_match:
                date = date_match.group(1)
                self.time_index[date].add(line_number)

    def _tokenize(self, text: str) -> List[str]:
        """
        分词函数

        Args:
            text: 输入文本

        Returns:
            词列表
        """
        # 使用正则分割，保留字母数字和下划线
        words = re.findall(r'[a-zA-Z0-9_]+', text)
        return words

    def search(self, keyword: str, search_mode: str = "普通") -> Set[int]:
        """
        搜索关键词

        Args:
            keyword: 搜索关键词
            search_mode: 搜索模式（"普通" 或 "正则"）

        Returns:
            匹配的行号集合
        """
        if not self.is_ready:
            # 索引未准备好，返回空集合
            return set()

        keyword_lower = keyword.lower()

        if search_mode == "普通":
            # 精确词匹配
            if keyword_lower in self.word_index:
                return self.word_index[keyword_lower].copy()

            # 如果没有精确匹配，尝试使用trigram模糊搜索
            if len(keyword_lower) >= 3:
                candidates = set()
                for i in range(len(keyword_lower) - 2):
                    trigram = keyword_lower[i:i+3]
                    if trigram in self.trigram_index:
                        if not candidates:
                            candidates = self.trigram_index[trigram].copy()
                        else:
                            # 交集：所有trigram都必须匹配
                            candidates &= self.trigram_index[trigram]
                return candidates

            return set()
        else:
            # 正则模式不使用索引，返回空表示需要全量搜索
            return set()

    def search_by_module(self, module: str) -> Set[int]:
        """
        按模块搜索

        Args:
            module: 模块名

        Returns:
            匹配的行号集合
        """
        return self.module_index.get(module, set()).copy()

    def search_by_level(self, level: str) -> Set[int]:
        """
        按级别搜索

        Args:
            level: 日志级别

        Returns:
            匹配的行号集合
        """
        return self.level_index.get(level, set()).copy()

    def search_by_date(self, date: str) -> Set[int]:
        """
        按日期搜索

        Args:
            date: 日期 (YYYY-MM-DD格式)

        Returns:
            匹配的行号集合
        """
        return self.time_index.get(date, set()).copy()

    def add_entry(self, entry, line_number: int):
        """
        增量添加单个日志条目到索引

        Args:
            entry: LogEntry对象
            line_number: 行号
        """
        if self.is_ready:
            self._index_entry(entry, line_number)
            self.total_entries += 1

    def remove_entry(self, line_number: int):
        """
        从索引中移除日志条目（较少使用）

        Args:
            line_number: 要移除的行号
        """
        # 从所有索引中移除该行号
        for index in [self.word_index, self.trigram_index, self.module_index,
                     self.level_index, self.time_index]:
            for key in list(index.keys()):
                index[key].discard(line_number)

        self.total_entries = max(0, self.total_entries - 1)

    def clear(self):
        """清空所有索引"""
        self.word_index.clear()
        self.trigram_index.clear()
        self.module_index.clear()
        self.level_index.clear()
        self.time_index.clear()
        self.is_ready = False
        self.total_entries = 0

    def stop_building(self):
        """停止索引构建"""
        self._stop_flag = True
        if self._build_thread and self._build_thread.is_alive():
            self._build_thread.join(timeout=5.0)

    def get_statistics(self) -> Dict:
        """
        获取索引统计信息

        Returns:
            统计信息字典
        """
        return {
            'total_entries': self.total_entries,
            'unique_words': len(self.word_index),
            'unique_trigrams': len(self.trigram_index),
            'modules': len(self.module_index),
            'levels': len(self.level_index),
            'dates': len(self.time_index),
            'is_ready': self.is_ready,
            'is_building': self.is_building
        }


class IndexedFilterSearchManager:
    """
    使用索引的过滤搜索管理器

    集成索引功能，提升搜索性能：
    - 优先使用索引进行快速搜索
    - 索引未准备时降级到原始搜索
    - 支持组合查询（级别+模块+关键词）
    """

    def __init__(self):
        self.indexer = LogIndexer()

        # 正则表达式缓存（从阶段一保留）
        self._pattern_cache = {}
        self._cache_max_size = 100

    def build_index(self, entries: List, progress_callback=None, complete_callback=None):
        """
        构建索引

        Args:
            entries: LogEntry列表
            progress_callback: 进度回调
            complete_callback: 完成回调
        """
        self.indexer.build_index_async(entries, progress_callback, complete_callback)

    def filter_entries_with_index(self, entries: List, level=None, module=None,
                                  keyword=None, start_time=None, end_time=None,
                                  search_mode='普通') -> List:
        """
        使用索引的过滤方法

        Args:
            entries: LogEntry列表
            level: 日志级别过滤
            module: 模块过滤
            keyword: 关键词搜索
            start_time: 开始时间
            end_time: 结束时间
            search_mode: 搜索模式

        Returns:
            过滤后的LogEntry列表
        """
        # 如果索引未准备好，降级到全量搜索
        if not self.indexer.is_ready:
            return self._filter_entries_fallback(
                entries, level, module, keyword, start_time, end_time, search_mode
            )

        # 使用索引快速过滤
        candidate_indices = None

        # 1. 级别过滤（使用索引）
        if level and level != '全部':
            level_indices = self.indexer.search_by_level(level)
            candidate_indices = level_indices if candidate_indices is None else (candidate_indices & level_indices)

        # 2. 模块过滤（使用索引）
        if module and module != '全部':
            module_indices = self.indexer.search_by_module(module)
            candidate_indices = module_indices if candidate_indices is None else (candidate_indices & module_indices)

        # 3. 关键词搜索（使用索引）
        if keyword and search_mode == "普通":
            keyword_indices = self.indexer.search(keyword, search_mode)
            if keyword_indices:  # 索引搜索成功
                candidate_indices = keyword_indices if candidate_indices is None else (candidate_indices & keyword_indices)

        # 如果没有任何索引过滤条件，返回全部（或根据时间过滤）
        if candidate_indices is None:
            if start_time or end_time or (keyword and search_mode == "正则"):
                # 需要时间过滤或正则搜索，执行全量过滤
                return self._filter_entries_fallback(
                    entries, level, module, keyword, start_time, end_time, search_mode
                )
            else:
                return entries

        # 根据索引结果构建过滤后的列表
        filtered = []
        for idx in sorted(candidate_indices):
            if idx < len(entries):
                entry = entries[idx]

                # 时间过滤（索引不支持时间范围，需要额外检查）
                if start_time or end_time:
                    if not self._check_time_range(entry, start_time, end_time):
                        continue

                # 正则搜索（索引不支持，需要额外检查）
                if keyword and search_mode == "正则":
                    pattern = self._get_compiled_pattern(keyword, re.IGNORECASE)
                    if pattern and not pattern.search(entry.raw_line):
                        continue

                filtered.append(entry)

        return filtered

    def _filter_entries_fallback(self, entries, level, module, keyword,
                                 start_time, end_time, search_mode):
        """
        降级到全量搜索（索引未准备或不适用时）

        这是从原始 FilterSearchManager 继承的逻辑
        """
        from filter_search import FilterSearchManager

        manager = FilterSearchManager()
        return manager.filter_entries(
            entries, level, module, keyword, start_time, end_time, search_mode
        )

    def _get_compiled_pattern(self, pattern, flags=0):
        """获取编译后的正则表达式（带缓存）"""
        cache_key = (pattern, flags)

        if cache_key in self._pattern_cache:
            return self._pattern_cache[cache_key]

        try:
            compiled = re.compile(pattern, flags)

            if len(self._pattern_cache) >= self._cache_max_size:
                first_key = next(iter(self._pattern_cache))
                del self._pattern_cache[first_key]

            self._pattern_cache[cache_key] = compiled
            return compiled
        except re.error:
            return None

    def _check_time_range(self, entry, start_time, end_time):
        """检查时间范围（简化版）"""
        from filter_search import FilterSearchManager

        if entry.timestamp:
            return FilterSearchManager.compare_log_time(entry.timestamp, start_time, end_time)
        return True


# 性能测试辅助函数
def benchmark_indexer():
    """索引器性能基准测试"""
    from data_models import LogEntry
    import random

    # 生成测试数据
    print("生成测试数据...")
    test_entries = []
    levels = ['INFO', 'WARNING', 'ERROR', 'DEBUG']
    modules = ['ModuleA', 'ModuleB', 'ModuleC', 'ModuleD']

    for i in range(100000):
        level = random.choice(levels)
        module = random.choice(modules)
        raw_line = f"[{level}][2025-10-11 10:00:{i%60:02d}][{module}] Test message {i} with some random content"
        entry = LogEntry(raw_line)
        test_entries.append(entry)

    print(f"生成了 {len(test_entries)} 条测试数据")

    # 测试索引构建性能
    print("\n测试索引构建性能...")
    indexer = LogIndexer()

    start_time = time.time()
    indexer.build_index(test_entries)
    build_time = time.time() - start_time

    print(f"✅ 索引构建完成")
    print(f"   耗时: {build_time:.2f}秒")
    print(f"   速度: {len(test_entries)/build_time:.0f} 条/秒")

    # 测试搜索性能
    print("\n测试搜索性能...")

    test_keywords = ['Test', 'message', 'random', 'content']
    for keyword in test_keywords:
        start_time = time.time()
        results = indexer.search(keyword)
        search_time = time.time() - start_time

        print(f"✅ 搜索 '{keyword}'")
        print(f"   找到: {len(results)} 条")
        print(f"   耗时: {search_time*1000:.2f}ms")

    # 统计信息
    print("\n索引统计信息:")
    stats = indexer.get_statistics()
    for key, value in stats.items():
        print(f"   {key}: {value}")


if __name__ == "__main__":
    # 运行性能测试
    benchmark_indexer()
