#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""测试修正后的崩溃日志识别逻辑"""

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

    # 崩溃关键词 - 必须是确定的崩溃标识
    CRASH_KEYWORDS = [
        '*** Terminating app due to uncaught exception'  # 只有这个才是真正的崩溃
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

        # 只检查内容中是否包含确定的崩溃标识
        for keyword in self.CRASH_KEYWORDS:
            if keyword in content:  # 精确匹配，不转换大小写
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

            # 设置模块
            self.module = tag2

            # 检测是否为崩溃日志 - 必须是ERROR级别且包含特定崩溃信息
            if (self.level == 'ERROR' and
                tag1 == 'ERROR' and
                tag2 == 'HY-Default' and
                'CrashReportManager.m' in location and
                self._is_crash_content(self.content)):
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

            # 标准格式日志一般不是崩溃日志，崩溃日志通常使用特殊格式
            # 除非内容明确包含崩溃标识
            if self.level == 'ERROR' and '*** Terminating app due to uncaught exception' in self.content:
                self._mark_as_crash()
        else:
            # 非标准格式
            self.level = 'OTHER'
            self.module = 'System'
            self.content = self.raw_line

# 测试用例
test_cases = [
    # 真正的崩溃日志
    "[E][2025-09-21 +8.0 16:56:39.129][0, 5453155200][<ERROR><HY-Default>][CrashReportManager.m, attachmentForException, 204][*** Terminating app due to uncaught exception 'NSGenericException']",

    # 非崩溃的INFO日志（即使包含CrashReportManager）
    "[I][2025-09-21 +8.0 16:56:39.135][0, 5453155200][<INFO><HY-Default>][CrashReportManager.m, genCrashInfo, 87][add event traces]",

    # 非崩溃的INFO日志（Bugly设置）
    "[I][2025-09-21 +8.0 16:57:05.416][0, 4580753408*][<INFO><HY-Default>][CrashReportManager.m, setupWithConfig, 150][Bugly has been setup : 521acad469]",

    # 普通ERROR日志（不包含崩溃关键词）
    "[E][2025-09-21 16:56:40][123][Network] Connection failed with error",

    # 包含NSException但不是完整崩溃信息
    "[E][2025-09-21 16:56:41][456][ErrorHandler] NSException caught and handled",

    # 普通INFO日志
    "[I][2025-09-21 16:56:42][789][Room] User joined room successfully",

    # 崩溃日志的后续堆栈（作为多行的一部分）
    "*** First throw call stack:",
    "0  CoreFoundation                 0x000000019124c0c0 0x0000000191132000 + 1155264",
    "1  libobjc.A.dylib                0x000000018e6e5abc objc_exception_throw + 88"
]

# 测试解析
print("===== 测试修正后的崩溃日志识别 =====\n")
results = []
for test_log in test_cases:
    entry = LogEntry(test_log)
    results.append(entry)

    # 缩短显示的日志内容
    display_log = test_log[:100] + "..." if len(test_log) > 100 else test_log

    print(f"日志: {display_log}")
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

# 验证结果
expected_crash_count = 1  # 只有第一条应该被识别为崩溃
if crash_count == expected_crash_count:
    print(f"\n✅ 崩溃识别正确：只识别了 {crash_count} 条真正的崩溃日志")
else:
    print(f"\n❌ 崩溃识别错误：期望 {expected_crash_count} 条，实际识别了 {crash_count} 条")

# 测试多行崩溃日志
print("\n===== 测试多行崩溃日志 =====")
multi_line_crash = """[E][2025-09-21 +8.0 16:56:39.129][0, 5453155200][<ERROR><HY-Default>][CrashReportManager.m, attachmentForException, 204][*** Terminating app due to uncaught exception 'NSGenericException', reason: 'Unable to activate constraint']
*** First throw call stack:
0  CoreFoundation                 0x000000019124c0c0 0x0000000191132000 + 1155264
1  libobjc.A.dylib                0x000000018e6e5abc objc_exception_throw + 88
2  CoreAutoLayout                 0x00000001b5241940 0x00000001b5240000 + 6464"""

entry = LogEntry(multi_line_crash)
print(f"多行崩溃日志是否被识别: {entry.is_crash}")
print(f"模块: {entry.module}")
print(f"内容预览: {entry.content[:100]}..." if entry.content and len(entry.content) > 100 else f"内容: {entry.content}")
print(f"原始内容行数: {len(multi_line_crash.splitlines())}")