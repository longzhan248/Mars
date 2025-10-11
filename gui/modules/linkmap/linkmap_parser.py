#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LinkMap文件解析模块
负责解析LinkMap文件格式，提取符号和文件信息
"""

import re


class LinkMapParser:
    """LinkMap文件解析器"""

    def __init__(self):
        """初始化解析器"""
        self.object_files = {}  # 对象文件映射 {索引: 文件路径}

    def check_format(self, content):
        """检查LinkMap文件格式是否有效

        Args:
            content: 文件内容字符串

        Returns:
            bool: 格式是否有效
        """
        if not content:
            return False

        required_sections = ["# Object files:", "# Symbols:"]
        for section in required_sections:
            if section not in content:
                return False

        return True

    def extract_app_name(self, content, file_path):
        """从文件内容或路径中提取应用名称

        Args:
            content: 文件内容字符串
            file_path: 文件路径

        Returns:
            str: 应用名称
        """
        import os

        lines = content.split('\n')
        if lines:
            first_line = lines[0]
            if '.app/' in first_line:
                return first_line.split('.app/')[-1].split('/')[0]

        # 从文件名提取
        return os.path.basename(file_path).replace('-LinkMap', '').replace('.txt', '')

    def parse_object_files(self, content):
        """解析对象文件段

        Args:
            content: 文件内容字符串

        Returns:
            dict: {索引: 文件路径}
        """
        object_files = {}
        lines = content.split('\n')

        in_object_files = False

        for line in lines:
            line = line.strip()

            if line.startswith('# Object files:'):
                in_object_files = True
                continue
            elif line.startswith('# Sections:'):
                break

            if in_object_files and line and not line.startswith('#'):
                # 解析格式: [ 0] /path/to/file.o
                match = re.match(r'\[\s*(\d+)\]\s+(.+)', line)
                if match:
                    index = f"[{match.group(1).strip()}]"
                    file_path = match.group(2).strip()
                    object_files[index] = file_path

        self.object_files = object_files
        return object_files

    def parse_symbols(self, content):
        """解析符号段

        Args:
            content: 文件内容字符串

        Returns:
            dict: {文件路径: 总大小}
        """
        symbol_map = {}
        lines = content.split('\n')

        # 先解析对象文件（如果还没解析）
        if not self.object_files:
            self.parse_object_files(content)

        in_symbols = False

        for line in lines:
            line = line.strip()

            if line.startswith('# Symbols:'):
                in_symbols = True
                continue
            elif line.startswith('# Dead Stripped Symbols:'):
                break

            if in_symbols and line and not line.startswith('#'):
                # 解析格式: 0x1000 0x100 [ 0] _symbol_name
                parts = line.split('\t')
                if len(parts) >= 3:
                    size_hex = parts[1] if len(parts) > 1 else '0x0'
                    size = int(size_hex, 16) if size_hex.startswith('0x') else 0

                    # 提取文件索引
                    file_info = parts[2] if len(parts) > 2 else ''
                    match = re.search(r'(\[\s*\d+\])', file_info)
                    if match:
                        file_index = match.group(1).replace(' ', '')
                        if file_index in self.object_files:
                            file_path = self.object_files[file_index]
                            if file_path not in symbol_map:
                                symbol_map[file_path] = 0
                            symbol_map[file_path] += size

        return symbol_map

    def parse_dead_symbols(self, content):
        """解析死代码段（未使用的符号）

        Args:
            content: 文件内容字符串

        Returns:
            dict: {文件路径: 总大小}
        """
        dead_symbol_map = {}
        lines = content.split('\n')

        # 先解析对象文件（如果还没解析）
        if not self.object_files:
            self.parse_object_files(content)

        in_dead_symbols = False

        for line in lines:
            line = line.strip()

            if line.startswith('# Dead Stripped Symbols:'):
                in_dead_symbols = True
                continue

            if in_dead_symbols and line and not line.startswith('#'):
                # 解析格式: <<dead>> 0x100 [ 0] _symbol_name
                if line.startswith('<<dead>>'):
                    parts = line.split('\t')
                    if len(parts) >= 3:
                        size_hex = parts[1] if len(parts) > 1 else '0x0'
                        size = int(size_hex, 16) if size_hex.startswith('0x') else 0

                        # 提取文件索引
                        file_info = parts[2] if len(parts) > 2 else ''
                        match = re.search(r'(\[\s*\d+\])', file_info)
                        if match:
                            file_index = match.group(1).replace(' ', '')
                            if file_index in self.object_files:
                                file_path = self.object_files[file_index]
                                if file_path not in dead_symbol_map:
                                    dead_symbol_map[file_path] = 0
                                dead_symbol_map[file_path] += size

        return dead_symbol_map

    def parse_all(self, content):
        """一次性解析所有内容

        Args:
            content: 文件内容字符串

        Returns:
            dict: {
                'object_files': 对象文件映射,
                'symbols': 符号映射,
                'dead_symbols': 死代码映射
            }
        """
        self.parse_object_files(content)
        symbols = self.parse_symbols(content)
        dead_symbols = self.parse_dead_symbols(content)

        return {
            'object_files': self.object_files,
            'symbols': symbols,
            'dead_symbols': dead_symbols
        }
