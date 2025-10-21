#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dSYM UUID解析模块
负责使用dwarfdump提取UUID和架构信息
"""

import re
import subprocess


class DSYMUUIDParser:
    """dSYM UUID解析器"""

    def __init__(self):
        """初始化UUID解析器"""

    def get_uuid_info(self, dsym_path):
        """获取dSYM文件的UUID信息

        Args:
            dsym_path: dSYM文件路径

        Returns:
            list: UUID信息列表 [{'uuid': str, 'arch': str, 'path': str}, ...]
            None: 如果执行失败
        """
        try:
            result = subprocess.run(
                ['dwarfdump', '--uuid', dsym_path],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                return self.parse_uuid_output(result.stdout, dsym_path)
            else:
                return None

        except subprocess.TimeoutExpired:
            return None
        except Exception:
            return None

    def parse_uuid_output(self, output, dsym_path):
        """解析dwarfdump的UUID输出

        Args:
            output: dwarfdump输出文本
            dsym_path: dSYM文件路径

        Returns:
            list: UUID信息列表 [{'uuid': str, 'arch': str, 'path': str}, ...]
        """
        lines = output.strip().split('\n')
        uuids = []

        # 解析UUID信息
        # 格式: UUID: XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX (armv7) path/to/file
        pattern = r'UUID: ([\w-]+) \((\w+)\) (.+)'

        for line in lines:
            match = re.search(pattern, line)
            if match:
                uuid = match.group(1)
                arch = match.group(2)
                path = match.group(3)

                uuids.append({
                    'uuid': uuid,
                    'arch': arch,
                    'path': path
                })

        return uuids

    def get_default_slide_address(self, arch=None):
        """获取默认的Slide Address

        Args:
            arch: 架构名称（可选）

        Returns:
            str: 默认基址（十六进制字符串）
        """
        # iOS默认基址
        # 32位: 0x4000
        # 64位: 0x100000000 或 0x104000000（较新版本）
        if arch and ('64' in arch or 'arm64' in arch.lower()):
            return "0x104000000"
        elif arch and ('armv7' in arch.lower() or 'arm' in arch.lower()):
            return "0x4000"
        else:
            # 默认使用64位地址
            return "0x104000000"

    def validate_uuid(self, uuid_string):
        """验证UUID格式

        Args:
            uuid_string: UUID字符串

        Returns:
            bool: 是否为有效的UUID格式
        """
        # 标准UUID格式: XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
        pattern = r'^[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}$'
        return re.match(pattern, uuid_string) is not None

    def get_architecture_list(self, uuid_infos):
        """从UUID信息列表提取架构列表

        Args:
            uuid_infos: UUID信息列表

        Returns:
            list: 架构名称列表
        """
        if not uuid_infos:
            return []

        return [info['arch'] for info in uuid_infos]

    def find_uuid_by_arch(self, uuid_infos, arch):
        """根据架构查找UUID信息

        Args:
            uuid_infos: UUID信息列表
            arch: 架构名称

        Returns:
            dict: UUID信息
            None: 如果未找到
        """
        if not uuid_infos:
            return None

        for info in uuid_infos:
            if info['arch'] == arch:
                return info

        return None

    def check_dwarfdump_available(self):
        """检查dwarfdump工具是否可用

        Returns:
            bool: 是否可用
        """
        try:
            result = subprocess.run(
                ['which', 'dwarfdump'],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False
