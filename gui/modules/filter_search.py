#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
过滤和搜索功能模块
处理日志的过滤、搜索和时间比较等功能
"""

import re
from datetime import datetime


class FilterSearchManager:
    """过滤和搜索管理器

    性能优化：
    - 正则表达式预编译和缓存
    - 减少重复编译开销
    """

    def __init__(self):
        # 正则表达式缓存 {(pattern, flags): compiled_pattern}
        self._pattern_cache = {}
        self._cache_max_size = 100  # 最多缓存100个正则表达式

    def _get_compiled_pattern(self, pattern, flags=0):
        """获取编译后的正则表达式（带缓存）

        Args:
            pattern: 正则表达式字符串
            flags: 正则标志（如re.IGNORECASE）

        Returns:
            编译后的正则表达式对象
        """
        cache_key = (pattern, flags)

        # 尝试从缓存获取
        if cache_key in self._pattern_cache:
            return self._pattern_cache[cache_key]

        # 缓存未命中，编译并缓存
        try:
            compiled = re.compile(pattern, flags)

            # 如果缓存已满，移除最旧的项（FIFO）
            if len(self._pattern_cache) >= self._cache_max_size:
                # 移除第一个添加的项
                first_key = next(iter(self._pattern_cache))
                del self._pattern_cache[first_key]

            self._pattern_cache[cache_key] = compiled
            return compiled
        except re.error:
            # 正则表达式无效，返回None
            return None

    @staticmethod
    def parse_time_string(time_str):
        """解析多种格式的时间字符串
        支持格式：
        - YYYY-MM-DD HH:MM:SS
        - YYYY-MM-DD HH:MM:SS.mmm
        - YYYY-MM-DD
        - HH:MM:SS
        - HH:MM:SS.mmm
        - HH:MM
        返回标准化的时间字符串用于比较
        """
        if not time_str or time_str.strip() == "":
            return None

        time_str = time_str.strip()

        # 完整格式：YYYY-MM-DD HH:MM:SS 或 YYYY-MM-DD HH:MM:SS.mmm
        full_pattern = r'^(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?$'
        match = re.match(full_pattern, time_str)
        if match:
            return time_str

        # 只有日期：YYYY-MM-DD
        date_only_pattern = r'^(\d{4})-(\d{2})-(\d{2})$'
        match = re.match(date_only_pattern, time_str)
        if match:
            return f"{time_str} 00:00:00"

        # 只有时间：HH:MM:SS 或 HH:MM:SS.mmm
        time_only_pattern = r'^(\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?$'
        match = re.match(time_only_pattern, time_str)
        if match:
            # 对于只有时间的，需要从日志中提取日期部分
            return f"TIME_ONLY:{time_str}"

        # 只有时间：HH:MM（补充秒）
        time_short_pattern = r'^(\d{2}):(\d{2})$'
        match = re.match(time_short_pattern, time_str)
        if match:
            return f"TIME_ONLY:{time_str}:00"

        return None

    @staticmethod
    def compare_log_time(log_timestamp, start_time, end_time):
        """比较日志时间戳是否在指定范围内"""
        # 从日志时间戳提取时间信息
        # 支持的格式：
        # 1. 2025-09-15 +8.0 11:05:43.995
        # 2. 2025-09-21 +8.0 13:09:49.038
        # 3. 2025-09-21 13:09:49.038 (无时区)

        # 尝试带时区的格式
        log_pattern = r'^(\d{4}-\d{2}-\d{2})\s+[+\-]?\d+\.?\d*\s+(\d{2}:\d{2}:\d{2}(?:\.\d+)?)'
        match = re.match(log_pattern, log_timestamp)

        if not match:
            # 尝试不带时区的格式
            log_pattern_simple = r'^(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2}(?:\.\d+)?)'
            match = re.match(log_pattern_simple, log_timestamp)

        if not match:
            return True  # 无法解析的时间戳，默认包含

        log_date = match.group(1)
        log_time = match.group(2)
        log_full = f"{log_date} {log_time}"

        # 处理开始时间
        if start_time:
            parsed_start = FilterSearchManager.parse_time_string(start_time)
            if parsed_start:
                if parsed_start.startswith("TIME_ONLY:"):
                    # 只比较时间部分
                    start_time_only = parsed_start[10:]
                    if log_time < start_time_only:
                        return False
                else:
                    # 完整比较
                    if log_full < parsed_start:
                        return False

        # 处理结束时间
        if end_time:
            parsed_end = FilterSearchManager.parse_time_string(end_time)
            if parsed_end:
                if parsed_end.startswith("TIME_ONLY:"):
                    # 只比较时间部分
                    end_time_only = parsed_end[10:]
                    if log_time > end_time_only:
                        return False
                else:
                    # 完整比较
                    # 如果结束时间只有日期，需要调整到当天最后时刻
                    if re.match(r'^\d{4}-\d{2}-\d{2} 00:00:00$', parsed_end):
                        parsed_end = parsed_end[:10] + " 23:59:59.999"
                    if log_full > parsed_end:
                        return False

        return True

    def filter_entries(self, entries, level=None, module=None, keyword=None,
                       start_time=None, end_time=None, search_mode='普通'):
        """过滤日志条目（优化版：使用正则缓存）

        Args:
            entries: 日志条目列表
            level: 日志级别过滤
            module: 模块过滤
            keyword: 关键词搜索
            start_time: 开始时间
            end_time: 结束时间
            search_mode: 搜索模式（普通/正则）

        Returns:
            过滤后的日志条目列表
        """
        filtered = []

        # 预编译正则表达式（如果是正则模式）
        pattern = None
        keyword_lower = None

        if keyword:
            if search_mode == "正则":
                pattern = self._get_compiled_pattern(keyword, re.IGNORECASE)
                if pattern is None:
                    # 正则表达式无效，返回空结果
                    return filtered
            else:
                # 预处理关键词（普通模式）
                keyword_lower = keyword.lower()

        for entry in entries:
            # 关键词过滤（优化：预编译的正则）
            if keyword:
                if search_mode == "正则":
                    if not pattern.search(entry.raw_line):
                        continue
                else:
                    # 普通模式：预处理的小写关键词
                    if keyword_lower and keyword_lower not in entry.raw_line.lower():
                        continue

            # 级别过滤
            if level and level != '全部':
                if entry.level != level:
                    continue

            # 模块过滤
            if module and module != '全部':
                if entry.module != module:
                    continue

            # 时间范围过滤
            if start_time or end_time:
                # 优先使用entry.timestamp
                if entry.timestamp:
                    if not FilterSearchManager.compare_log_time(entry.timestamp, start_time, end_time):
                        continue
                else:
                    # 如果没有timestamp，尝试从raw_line提取
                    # 支持格式：[I][2025-09-21 +8.0 13:09:49.038]
                    time_pattern = r'\[(\d{4}-\d{2}-\d{2}\s+[+\-]?\d+\.?\d*\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?)\]'
                    match = re.search(time_pattern, entry.raw_line)
                    if match:
                        timestamp = match.group(1)
                        if not FilterSearchManager.compare_log_time(timestamp, start_time, end_time):
                            continue

            filtered.append(entry)

        return filtered