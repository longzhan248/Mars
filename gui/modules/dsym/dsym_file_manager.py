#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dSYM文件管理模块
负责加载和管理xcarchive/dSYM文件
"""

import os
import subprocess
from pathlib import Path


class DSYMFileManager:
    """dSYM/xcarchive文件管理器"""

    def __init__(self):
        """初始化文件管理器"""
        self.archive_files = []

    def load_local_archives(self):
        """加载本地的xcarchive文件

        Returns:
            list: 文件信息列表 [{'path': str, 'name': str, 'type': str}, ...]
        """
        archives = []

        # Xcode Archives默认路径
        archives_path = os.path.expanduser("~/Library/Developer/Xcode/Archives/")

        if not os.path.exists(archives_path):
            return archives

        # 遍历查找所有xcarchive文件
        for root, dirs, files in os.walk(archives_path):
            for dir_name in dirs:
                if dir_name.endswith('.xcarchive'):
                    archive_path = os.path.join(root, dir_name)
                    archives.append({
                        'path': archive_path,
                        'name': dir_name,
                        'type': 'xcarchive'
                    })

        return archives

    def add_dsym_file(self, file_path):
        """添加dSYM文件

        Args:
            file_path: dSYM文件路径

        Returns:
            dict: 文件信息 {'path': str, 'name': str, 'type': str}
            None: 如果文件无效
        """
        if not self._is_valid_dsym(file_path):
            return None

        file_name = os.path.basename(file_path)
        file_info = {
            'path': file_path,
            'name': file_name,
            'type': 'dsym'
        }

        self.archive_files.append(file_info)
        return file_info

    def add_xcarchive_file(self, file_path):
        """添加xcarchive文件

        Args:
            file_path: xcarchive文件路径

        Returns:
            dict: 文件信息 {'path': str, 'name': str, 'type': str}
            None: 如果文件无效
        """
        if not file_path.endswith('.xcarchive'):
            return None

        file_name = os.path.basename(file_path)
        file_info = {
            'path': file_path,
            'name': file_name,
            'type': 'xcarchive'
        }

        self.archive_files.append(file_info)
        return file_info

    def get_dsym_path_from_xcarchive(self, xcarchive_path):
        """从xcarchive中提取dSYM路径

        Args:
            xcarchive_path: xcarchive文件路径

        Returns:
            str: dSYM文件路径
            None: 如果未找到
        """
        dsym_dir = os.path.join(xcarchive_path, 'dSYMs')

        if not os.path.exists(dsym_dir):
            return None

        # 查找第一个.dSYM文件
        for item in os.listdir(dsym_dir):
            if item.endswith('.dSYM'):
                return os.path.join(dsym_dir, item)

        return None

    def select_file_with_applescript(self):
        """使用AppleScript选择文件（macOS原生对话框）

        Returns:
            str: 选中的文件路径
            None: 如果取消选择
        """
        script = '''
        tell application "System Events"
            activate
            set theFile to choose file with prompt "选择dSYM或xcarchive文件" ¬
                of type {"dSYM", "xcarchive", "app.dSYM", "public.folder"} ¬
                default location (path to home folder)
            return POSIX path of theFile
        end tell
        '''

        try:
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True
            )

            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except Exception:
            pass

        return None

    def _is_valid_dsym(self, path):
        """检查是否是有效的dSYM目录

        Args:
            path: 文件路径

        Returns:
            bool: 是否有效
        """
        if not os.path.isdir(path):
            return False

        # 检查dSYM标准结构
        if path.endswith('.dSYM'):
            return True

        # 检查是否包含dSYM的内部结构
        contents_path = os.path.join(path, 'Contents')
        if os.path.exists(contents_path):
            # 检查Info.plist或DWARF目录
            if os.path.exists(os.path.join(contents_path, 'Info.plist')):
                return True
            if os.path.exists(os.path.join(contents_path, 'Resources', 'DWARF')):
                return True

        return False

    def get_file_type(self, file_path):
        """判断文件类型

        Args:
            file_path: 文件路径

        Returns:
            str: 'dsym' 或 'xcarchive' 或 None
        """
        if '.dSYM' in file_path or self._is_valid_dsym(file_path):
            return 'dsym'
        elif file_path.endswith('.xcarchive'):
            return 'xcarchive'
        return None

    def clear_files(self):
        """清空文件列表"""
        self.archive_files = []

    def get_all_files(self):
        """获取所有已加载的文件

        Returns:
            list: 文件信息列表
        """
        return self.archive_files

    def get_file_by_index(self, index):
        """根据索引获取文件

        Args:
            index: 文件索引

        Returns:
            dict: 文件信息
            None: 如果索引无效
        """
        if 0 <= index < len(self.archive_files):
            return self.archive_files[index]
        return None
