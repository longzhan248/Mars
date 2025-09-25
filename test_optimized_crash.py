#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""测试优化后的崩溃日志识别逻辑"""

import re
from collections import Counter

class LogEntry:
    """日志条目类"""

    # 级别映射表
    LEVEL_MAP = {
        'I': 'INFO',
        'W': 'WARNING',
        'E': 'ERROR',
        'D': 'DEBUG',
        'V': 'VERBOSE',
        'F': 'FATAL'
    }

    # 崩溃关键词
    CRASH_KEYWORDS = [
        '*** Terminating app',
        'NSException',
        'Fatal Exception',
        'SIGABRT',
        'SIGSEGV',
        'crashed',
        'CrashReportManager'
    ]

    def __init__(self, raw_line, source_file=""):
        self.raw_line = raw_line
        self.source_file = source_file
        self.level = None
        self.timestamp = None
        self.module = None
        self.content = None
        self.thread_id = None
        self.is_crash = False
        self.is_stacktrace = False
        self.parse()

    def _is_crash_content(self, content, location=""):
        """检测内容是否包含崩溃信息"""
        if not content:
            return False

        content_lower = content.lower()
        location_lower = location.lower() if location else ""

        # 检查崩溃关键词
        for keyword in self.CRASH_KEYWORDS:
            if keyword.lower() in content_lower or keyword.lower() in location_lower:
                return True

        return False

    def _mark_as_crash(self, location=None):
        """标记为崩溃日志"""
        self.is_crash = True
        self.level = 'CRASH'
        self.module = 'Crash'
        if location and self.content:
            self.content = f"[{location}] {self.content}"

    def parse(self):
        """解析日志行"""
        # 尝试匹配带有两个模块标签的格式（崩溃日志特殊格式）
        crash_pattern = r'^\[([IWEDVF])\]\[([^\]]+)\]\[([^\]]+)\]\[<([^>]+)><([^>]+)>\]\[([^\]]+)\](.*)$'
        crash_match = re.match(crash_pattern, self.raw_line)

        if crash_match:
            self.level = self.LEVEL_MAP.get(crash_match.group(1), crash_match.group(1))
            self.timestamp = crash_match.group(2)
            self.thread_id = crash_match.group(3)
            tag1 = crash_match.group(4)
            tag2 = crash_match.group(5)
            location = crash_match.group(6)
            self.content = crash_match.group(7)

            self.module = tag2

            # 检测是否为崩溃日志
            if self._is_crash_content(self.content, location):
                self._mark_as_crash(location)

            return

        # 标准日志格式
        pattern = r'^\[([IWEDVF])\]\[([^\]]+)\]\[([^\]]+)\]\[([^\]]+)\](.*)$'
        match = re.match(pattern, self.raw_line)

        if match:
            self.level = self.LEVEL_MAP.get(match.group(1), match.group(1))
            self.timestamp = match.group(2)
            self.thread_id = match.group(3)
            module_str = match.group(4)
            self.module = module_str.strip('<>[]')
            self.content = match.group(5)

            # 检查是否为崩溃相关日志
            if self.level == 'ERROR' and self._is_crash_content(self.content):
                self._mark_as_crash()
        else:
            # 非标准格式
            self.level = 'OTHER'
            self.module = 'System'
            self.content = self.raw_line

# 测试用例
test_cases = [
    # 标准崩溃日志
    "[E][2025-09-21 +8.0 16:56:39.129][0, 5453155200][<ERROR><HY-Default>][CrashReportManager.m, attachmentForException, 204][*** Terminating app due to uncaught exception 'NSGenericException']",
    # 包含NSException的错误
    "[E][2025-09-21 16:56:40][123][ErrorHandler] NSException caught in main thread",
    # SIGABRT信号
    "[E][2025-09-21 16:56:41][456][System] Process terminated with SIGABRT",
    # 普通错误日志
    "[E][2025-09-21 16:56:42][789][Network] Connection failed",
    # 普通INFO日志
    "[I][2025-09-21 16:56:43][111][Room] User joined room",
    # Fatal Exception
    "[E][2025-09-21 16:56:44][222][Handler] Fatal Exception occurred",
    # Crashed关键词
    "[E][2025-09-21 16:56:45][333][Monitor] App crashed unexpectedly",
]

# 测试解析
print("===== 测试优化后的崩溃日志识别 =====\n")
results = []
for test_log in test_cases:
    entry = LogEntry(test_log)
    results.append(entry)

    print(f"日志: {test_log[:80]}...")
    print(f"  级别: {entry.level}")
    print(f"  模块: {entry.module}")
    print(f"  是否崩溃: {entry.is_crash}")
    print()

# 统计结果
crash_count = sum(1 for e in results if e.is_crash)
module_counts = Counter(e.module for e in results)

print("===== 统计结果 =====")
print(f"总日志数: {len(results)}")
print(f"崩溃日志数: {crash_count}")
print(f"模块分布: {dict(module_counts)}")

# 验证Crash模块
if 'Crash' in module_counts:
    print(f"\n✅ Crash模块成功识别，包含 {module_counts['Crash']} 条日志")
else:
    print("\n❌ 没有识别到Crash模块")