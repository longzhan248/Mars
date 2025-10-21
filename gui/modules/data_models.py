#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据模型模块
包含LogEntry日志条目类和FileGroup文件组类
"""

import re


class LogEntry:
    """日志条目类

    使用__slots__优化内存占用：
    - 减少对象内存占用 40-50%
    - 提升属性访问速度
    - 防止动态添加属性
    """

    # 定义允许的属性，优化内存占用
    __slots__ = [
        'raw_line',      # 原始日志行
        'source_file',   # 来源文件
        'level',         # 日志级别
        'timestamp',     # 时间戳
        'module',        # 模块名
        'content',       # 日志内容
        'thread_id',     # 线程ID
        'is_crash',      # 是否崩溃日志
        'is_stacktrace'  # 是否堆栈信息
    ]

    # 级别映射表
    LEVEL_MAP = {
        'I': 'INFO',
        'W': 'WARNING',
        'E': 'ERROR',
        'D': 'DEBUG',
        'V': 'VERBOSE',
        'F': 'FATAL'
    }

    # 崩溃关键词 - 必须是确定的崩溃标识
    CRASH_KEYWORDS = [
        '*** Terminating app due to uncaught exception'  # 只有这个才是真正的崩溃
    ]

    # 类变量：存储自定义模块规则
    custom_module_rules = []

    @classmethod
    def set_custom_rules(cls, rules):
        """设置自定义模块规则"""
        cls.custom_module_rules = rules

    def __init__(self, raw_line, source_file=""):
        self.raw_line = raw_line
        self.source_file = source_file  # 来源文件
        self.level = None
        self.timestamp = None
        self.module = None
        self.content = None
        self.thread_id = None
        self.is_crash = False  # 是否为崩溃日志
        self.is_stacktrace = False  # 是否为堆栈信息
        self.parse()

    def _is_crash_content(self, content, location=""):
        """检测内容是否包含崩溃信息"""
        if not content:
            return False

        # 只检查内容中是否包含确定的崩溃标识
        for keyword in self.CRASH_KEYWORDS:
            if keyword in content:  # 精确匹配，不转换大小写
                return True

        return False

    def _mark_as_crash(self, location=None):
        """标记为崩溃日志"""
        self.is_crash = True
        self.level = 'CRASH'
        self.module = 'Crash'  # 强制设置为Crash模块
        if location and self.content:
            # 保留位置信息，但不要重复添加
            if not self.content.startswith(f"[{location}]"):
                self.content = f"[{location}] {self.content}"

    def _apply_custom_rules(self, content):
        """应用自定义模块规则"""
        if not content or not self.custom_module_rules:
            return

        for rule in self.custom_module_rules:
            try:
                pattern = rule.get('pattern')
                module_name = rule.get('module')
                rule_type = rule.get('type', '正则')  # 默认为正则，兼容旧数据

                if not pattern or not module_name:
                    continue

                matched = False

                if rule_type == '字符串':
                    # 字符串模式：检查内容中是否包含指定字符串
                    if pattern in content:
                        matched = True
                        # 字符串匹配不修改content
                else:
                    # 正则模式：使用正则表达式匹配
                    match = re.match(pattern, content)
                    if match:
                        matched = True
                        # 如果规则有捕获组，提取清理后的内容
                        if match.groups():
                            self.content = match.group(1) if len(match.groups()) >= 1 else content

                if matched:
                    # 匹配成功，设置模块名
                    self.module = module_name
                    break  # 匹配到第一个规则后停止

            except Exception:
                # 忽略错误
                continue

    def parse(self):
        """解析日志行"""
        # 尝试匹配带有两个模块标签的格式（崩溃日志特殊格式）
        # 格式: [级别][时间][线程ID][<标签1><标签2>][位置信息][内容]
        crash_pattern = r'^\[([IWEDVF])\]\[([^\]]+)\]\[([^\]]+)\]\[<([^>]+)><([^>]+)>\]\[([^\]]+)\](.*)$'
        crash_match = re.match(crash_pattern, self.raw_line)

        if crash_match:
            # 这是崩溃日志格式
            self.level = self.LEVEL_MAP.get(crash_match.group(1), crash_match.group(1))
            self.timestamp = crash_match.group(2)
            self.thread_id = crash_match.group(3)
            _tag1 = crash_match.group(4)  # ERROR (unused, kept for documentation)
            tag2 = crash_match.group(5)  # HY-Default
            location = crash_match.group(6)  # CrashReportManager.m, attachmentForException, 204
            content = crash_match.group(7)  # *** Terminating app...

            # 先临时设置模块为tag2
            self.module = tag2
            self.content = content

            # 检查内容开头是否有额外的模块标识 <Chair> 或 [Plugin]
            # 格式1: [<Chair> 后面跟内容 (注意前面有个[)
            extra_module_pattern1 = r'^\[<([^>]+)>\s*(.*)$'
            # 格式2: [[Plugin] 后面跟内容 (注意有两个[)
            extra_module_pattern2 = r'^\[\[([^\]]+)\]\s*(.*)$'

            extra_match1 = re.match(extra_module_pattern1, content)
            extra_match2 = re.match(extra_module_pattern2, content)

            if extra_match1:
                # 找到 [<Chair> 格式的额外模块标识
                extra_module = extra_match1.group(1)
                self.module = extra_module
                self.content = extra_match1.group(2)
            elif extra_match2:
                # 找到 [[Plugin] 格式的额外模块标识
                extra_module = extra_match2.group(1)
                self.module = extra_module
                self.content = extra_match2.group(2)
            else:
                # 应用自定义模块规则
                self._apply_custom_rules(self.content)

            # 检测是否为崩溃日志（不要覆盖额外模块标识）
            # 条件：ERROR级别 + CrashReportManager + 包含崩溃关键词
            is_crash_log = (
                self.level == 'ERROR' and
                'CrashReportManager' in location and
                self._is_crash_content(self.content)
            )

            if is_crash_log:
                # 标记为崩溃日志，这会将module改为'Crash'
                self._mark_as_crash(location)

            return

        # 标准日志格式: [级别][时间][线程ID][模块]内容
        pattern = r'^\[([IWEDVF])\]\[([^\]]+)\]\[([^\]]+)\]\[([^\]]+)\](.*)$'
        match = re.match(pattern, self.raw_line)

        if match:
            # 提取基本信息
            self.level = self.LEVEL_MAP.get(match.group(1), match.group(1))
            self.timestamp = match.group(2)
            self.thread_id = match.group(3)

            # 提取模块
            module_str = match.group(4)
            if 'mars::' in module_str:
                self.module = 'mars'
            elif 'HY-Default' in module_str:
                self.module = 'HY-Default'
            elif 'HY-' in module_str:
                self.module = module_str
            else:
                self.module = module_str.strip('<>[]')

            # 提取内容
            content = match.group(5)
            self.content = content

            # 检查内容开头是否有额外的模块标识 <Chair> 或 [Plugin]
            # 格式1: [<Chair> 后面跟内容 (注意前面有个[)
            extra_module_pattern1 = r'^\[<([^>]+)>\s*(.*)$'
            # 格式2: [[Plugin] 后面跟内容 (注意有两个[)
            extra_module_pattern2 = r'^\[\[([^\]]+)\]\s*(.*)$'

            extra_match1 = re.match(extra_module_pattern1, content)
            extra_match2 = re.match(extra_module_pattern2, content)

            if extra_match1:
                # 找到 [<Chair> 格式的额外模块标识
                extra_module = extra_match1.group(1)
                self.module = extra_module
                self.content = extra_match1.group(2)
            elif extra_match2:
                # 找到 [[Plugin] 格式的额外模块标识
                extra_module = extra_match2.group(1)
                self.module = extra_module
                self.content = extra_match2.group(2)
            else:
                # 应用自定义模块规则
                self._apply_custom_rules(self.content)

            # 标准格式日志一般不是崩溃日志，崩溃日志通常使用特殊格式
            # 除非内容明确包含崩溃标识
            if self.level == 'ERROR' and '*** Terminating app due to uncaught exception' in self.content:
                self._mark_as_crash()
        else:
            # 检查特殊的崩溃相关行
            crash_related_patterns = [
                r'^\*\*\* First throw call stack:',  # iOS崩溃堆栈开始标记
            ]

            # 检查iOS崩溃堆栈格式：数字 + 框架名 + 地址 + 偏移等
            # 例如：0  CoreFoundation  0x00000001897c92ec 0x00000001896af000 + 1155820
            # 或：0  CoreFoundation                 0x000000019124c0c0 0x0000000191132000 + 1155264
            ios_stack_pattern = r'^\s*\d+\s+\S+.*?\s+0x[0-9a-fA-F]+(?:\s+0x[0-9a-fA-F]+\s*\+\s*\d+)?'

            if any(re.match(pattern, self.raw_line) for pattern in crash_related_patterns):
                # 崩溃相关的特殊行
                self.is_stacktrace = True
                self.level = 'CRASH'
                self.module = 'Crash'
                self.content = self.raw_line
            elif re.match(ios_stack_pattern, self.raw_line):
                # iOS堆栈格式，标记为崩溃堆栈（统一归入Crash模块）
                self.is_stacktrace = True
                self.level = 'CRASH'  # 统一使用CRASH级别
                self.module = 'Crash'  # 统一归入Crash模块
                self.content = self.raw_line
            else:
                # 无法解析的行，作为普通内容处理
                self.level = 'OTHER'
                self.module = 'Unknown'
                self.content = self.raw_line


class FileGroup:
    """文件分组类

    使用__slots__优化内存占用
    """

    __slots__ = ['base_name', 'files', 'entries']

    def __init__(self, base_name):
        self.base_name = base_name
        self.files = []  # 文件路径列表
        self.entries = []  # 合并后的日志条目

    def add_file(self, filepath):
        """添加文件到组"""
        self.files.append(filepath)

    def get_display_name(self):
        """获取显示名称"""
        import os
        file_count = len(self.files)
        if file_count == 1:
            return os.path.basename(self.files[0])
        else:
            return f"{self.base_name} ({file_count}个文件)"