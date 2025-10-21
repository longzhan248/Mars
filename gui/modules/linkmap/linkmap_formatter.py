#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LinkMap文件格式化模块
负责格式化输出、大小转换等显示相关功能
"""

import re


class LinkMapFormatter:
    """LinkMap数据格式化器"""

    def __init__(self):
        """初始化格式化器"""

    def format_size(self, size):
        """格式化文件大小

        Args:
            size: 字节数

        Returns:
            str: 格式化后的大小字符串（如 "1.5M", "256K", "100B"）
        """
        if size >= 1024 * 1024:
            return f"{size / (1024 * 1024):.2f}M"
        elif size >= 1024:
            return f"{size / 1024:.2f}K"
        else:
            return f"{size}B"

    def format_symbol_list(self, symbol_items, show_simplified_path=True):
        """格式化符号列表输出

        Args:
            symbol_items: [(文件路径, 大小), ...]
            show_simplified_path: 是否简化路径显示

        Returns:
            str: 格式化后的文本
        """
        if not symbol_items:
            return "无数据"

        result = []
        result.append(f"{'文件大小':<15} {'文件名称'}")
        result.append("=" * 80)

        total_size = 0
        for file_path, size in symbol_items:
            total_size += size
            size_str = self.format_size(size)

            # 简化路径显示
            if show_simplified_path:
                display_path = self._simplify_path(file_path)
            else:
                display_path = file_path

            result.append(f"{size_str:<15} {display_path}")

        result.append("=" * 80)
        result.append(f"总计: {self.format_size(total_size)} ({len(symbol_items)} 个文件)")

        return '\n'.join(result)

    def format_library_list(self, library_items):
        """格式化库列表输出

        Args:
            library_items: [(库名, 大小), ...]

        Returns:
            str: 格式化后的文本
        """
        if not library_items:
            return "无数据"

        result = []
        result.append(f"{'库大小':<15} {'库名称'}")
        result.append("=" * 80)

        total_size = 0
        for library_name, size in library_items:
            total_size += size
            size_str = self.format_size(size)
            result.append(f"{size_str:<15} {library_name}")

        result.append("=" * 80)
        result.append(f"总计: {self.format_size(total_size)} ({len(library_items)} 个库)")

        return '\n'.join(result)

    def format_analysis_report(self, app_name, file_path, symbol_result, dead_code_result):
        """格式化分析报告

        Args:
            app_name: 应用名称
            file_path: 文件路径
            symbol_result: 符号统计结果文本
            dead_code_result: 死代码统计结果文本

        Returns:
            str: 格式化后的报告
        """
        report = []
        report.append(f"Link Map 分析报告")
        report.append(f"应用名称: {app_name}")
        report.append(f"文件路径: {file_path}")
        report.append("=" * 80 + "\n")

        report.append("符号统计:")
        report.append("-" * 80)
        report.append(symbol_result)

        report.append("\n\n未使用代码:")
        report.append("-" * 80)
        report.append(dead_code_result)

        return '\n'.join(report)

    def format_linkmap_file(self, content):
        """格式化Link Map文件内容

        Args:
            content: 原始文件内容

        Returns:
            str: 格式化后的内容
        """
        lines = content.split('\n')
        formatted_lines = []

        in_object_files = False
        in_sections = False
        in_symbols = False
        in_dead_symbols = False

        for line in lines:
            if line.startswith('# Object files:'):
                in_object_files = True
                formatted_lines.append('\n' + '=' * 80)
                formatted_lines.append('OBJECT FILES')
                formatted_lines.append('=' * 80)

            elif line.startswith('# Sections:'):
                in_object_files = False
                in_sections = True
                formatted_lines.append('\n' + '=' * 80)
                formatted_lines.append('SECTIONS')
                formatted_lines.append('=' * 80)

            elif line.startswith('# Symbols:'):
                in_sections = False
                in_symbols = True
                formatted_lines.append('\n' + '=' * 80)
                formatted_lines.append('SYMBOLS')
                formatted_lines.append('=' * 80)

            elif line.startswith('# Dead Stripped Symbols:'):
                in_symbols = False
                in_dead_symbols = True
                formatted_lines.append('\n' + '=' * 80)
                formatted_lines.append('DEAD STRIPPED SYMBOLS')
                formatted_lines.append('=' * 80)

            else:
                # 格式化各部分内容
                if in_object_files and line.strip() and not line.startswith('#'):
                    # 简化路径
                    formatted_line = self._simplify_path(line)
                    formatted_lines.append(formatted_line)

                elif (in_sections or in_symbols or in_dead_symbols) and line.strip():
                    # 格式化大小
                    parts = line.split('\t')
                    if len(parts) >= 2 and parts[1].startswith('0x'):
                        size = int(parts[1], 16)
                        size_str = self.format_size(size)
                        parts[1] = size_str.rjust(10)
                        formatted_lines.append('\t'.join(parts))
                    else:
                        formatted_lines.append(line)

                else:
                    formatted_lines.append(line)

        return '\n'.join(formatted_lines)

    def _simplify_path(self, path):
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

    def format_distribution_stats(self, stats):
        """格式化分布统计信息

        Args:
            stats: 统计字典 {total_files, total_size, avg_size, max_size, min_size}

        Returns:
            str: 格式化后的统计信息
        """
        result = []
        result.append("=== 分布统计 ===")
        result.append(f"文件总数: {stats['total_files']}")
        result.append(f"总大小:   {self.format_size(stats['total_size'])}")
        result.append(f"平均大小: {self.format_size(stats['avg_size'])}")
        result.append(f"最大文件: {self.format_size(stats['max_size'])}")
        result.append(f"最小文件: {self.format_size(stats['min_size'])}")

        return '\n'.join(result)
