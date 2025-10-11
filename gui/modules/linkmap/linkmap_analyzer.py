#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LinkMap文件分析模块
负责统计、分组、排序等数据分析功能
"""

import os
import re
from collections import defaultdict


class LinkMapAnalyzer:
    """LinkMap数据分析器"""

    def __init__(self):
        """初始化分析器"""
        pass

    def filter_by_keyword(self, symbol_map, keyword):
        """按关键词过滤符号

        Args:
            symbol_map: 符号映射 {文件路径: 大小}
            keyword: 搜索关键词

        Returns:
            dict: 过滤后的符号映射
        """
        if not keyword:
            return symbol_map

        filtered = {}
        keyword_lower = keyword.lower()
        for file_path, size in symbol_map.items():
            if keyword_lower in file_path.lower():
                filtered[file_path] = size

        return filtered

    def sort_by_size(self, symbol_map, reverse=True):
        """按大小排序

        Args:
            symbol_map: 符号映射 {文件路径: 大小}
            reverse: 是否降序排列

        Returns:
            list: [(文件路径, 大小), ...]
        """
        return sorted(symbol_map.items(), key=lambda x: x[1], reverse=reverse)

    def group_by_library(self, symbol_map):
        """按库分组统计

        Args:
            symbol_map: 符号映射 {文件路径: 大小}

        Returns:
            dict: {库名: 总大小}
        """
        library_map = defaultdict(int)

        for file_path, size in symbol_map.items():
            library_name = self._extract_library_name(file_path)
            library_map[library_name] += size

        return dict(library_map)

    def _extract_library_name(self, file_path):
        """从文件路径提取库名称

        Args:
            file_path: 文件路径

        Returns:
            str: 库名称
        """
        # Framework
        if '.framework' in file_path:
            match = re.search(r'([^/]+)\.framework', file_path)
            if match:
                return match.group(1) + '.framework'

        # 静态库
        if '.a' in file_path:
            match = re.search(r'lib([^/]+)\.a', file_path)
            if match:
                return 'lib' + match.group(1) + '.a'

        # 项目文件
        if '.o' in file_path:
            file_name = os.path.basename(file_path)
            return file_name.replace('.o', '')

        return os.path.basename(file_path)

    def calculate_total_size(self, symbol_map):
        """计算总大小

        Args:
            symbol_map: 符号映射 {文件路径/库名: 大小}

        Returns:
            int: 总大小（字节）
        """
        return sum(symbol_map.values())

    def get_top_n(self, symbol_map, n=10):
        """获取前N大的符号

        Args:
            symbol_map: 符号映射 {文件路径: 大小}
            n: 数量

        Returns:
            list: [(文件路径, 大小), ...]
        """
        sorted_items = self.sort_by_size(symbol_map, reverse=True)
        return sorted_items[:n]

    def calculate_percentage(self, size, total_size):
        """计算百分比

        Args:
            size: 当前大小
            total_size: 总大小

        Returns:
            float: 百分比（0-100）
        """
        if total_size == 0:
            return 0.0
        return (size / total_size) * 100

    def analyze_distribution(self, symbol_map):
        """分析大小分布

        Args:
            symbol_map: 符号映射 {文件路径: 大小}

        Returns:
            dict: 分布统计信息
        """
        if not symbol_map:
            return {
                'total_files': 0,
                'total_size': 0,
                'avg_size': 0,
                'max_size': 0,
                'min_size': 0
            }

        sizes = list(symbol_map.values())
        total_size = sum(sizes)
        total_files = len(sizes)

        return {
            'total_files': total_files,
            'total_size': total_size,
            'avg_size': total_size // total_files if total_files > 0 else 0,
            'max_size': max(sizes) if sizes else 0,
            'min_size': min(sizes) if sizes else 0
        }

    def find_duplicates(self, symbol_map):
        """查找可能重复的符号

        Args:
            symbol_map: 符号映射 {文件路径: 大小}

        Returns:
            dict: {文件名: [完整路径列表]}
        """
        duplicates = defaultdict(list)

        for file_path in symbol_map.keys():
            file_name = os.path.basename(file_path)
            duplicates[file_name].append(file_path)

        # 只保留真正重复的（出现次数>1）
        return {name: paths for name, paths in duplicates.items() if len(paths) > 1}

    def simplify_path(self, path):
        """简化路径显示

        Args:
            path: 完整路径

        Returns:
            str: 简化后的路径
        """
        patterns = [
            r'.*/Build/Intermediates\.noindex/.*?\.build/.*?/',
            r'.*/DerivedData/.*?\.build/.*?/',
            r'.*/Developer/Platforms/.*?\.sdk/',
            r'.*/Xcode\.app/.*?\.sdk/',
        ]

        simplified = path
        for pattern in patterns:
            simplified = re.sub(pattern, '../', simplified)

        return simplified
