#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试崩溃日志解析"""

import re
from collections import defaultdict

# 复制LogEntry和FileGroup的核心逻辑
class LogEntry:
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

    def parse(self):
        """解析日志行"""
        # 尝试匹配带有两个模块标签的格式（崩溃日志特殊格式）
        crash_pattern = r'^\[([IWEDVF])\]\[([^\]]+)\]\[([^\]]+)\]\[<([^>]+)><([^>]+)>\]\[([^\]]+)\](.*)$'
        crash_match = re.match(crash_pattern, self.raw_line)

        if crash_match:
            # 这是崩溃日志格式
            level_map = {'I': 'INFO', 'W': 'WARNING', 'E': 'ERROR', 'D': 'DEBUG', 'V': 'VERBOSE', 'F': 'FATAL'}
            self.level = level_map.get(crash_match.group(1), crash_match.group(1))
            self.timestamp = crash_match.group(2)
            self.thread_id = crash_match.group(3)
            tag1 = crash_match.group(4)  # ERROR
            tag2 = crash_match.group(5)  # HY-Default
            location = crash_match.group(6)  # CrashReportManager.m, attachmentForException, 204
            self.content = crash_match.group(7)  # *** Terminating app...

            # 设置模块
            self.module = tag2

            # 检测CrashReportManager崩溃日志
            is_crash_report = (
                self.level == 'ERROR' and
                tag2 == 'HY-Default' and
                'CrashReportManager.m' in location and
                '*** Terminating app due to uncaught exception' in self.content
            )

            if is_crash_report:
                self.is_crash = True
                self.level = 'CRASH'
                self.module = 'Crash'
                self.content = f"[{location}] {self.content}"

            return

        # 标准日志格式
        pattern = r'^\[([IWEDVF])\]\[([^\]]+)\]\[([^\]]+)\]\[([^\]]+)\](.*)$'
        match = re.match(pattern, self.raw_line)

        if match:
            level_map = {'I': 'INFO', 'W': 'WARNING', 'E': 'ERROR', 'D': 'DEBUG', 'V': 'VERBOSE', 'F': 'FATAL'}
            self.level = level_map.get(match.group(1), match.group(1))
            self.timestamp = match.group(2)
            self.thread_id = match.group(3)
            module_str = match.group(4)
            if 'mars::' in module_str:
                self.module = 'mars'
            elif 'HY-Default' in module_str:
                self.module = 'HY-Default'
            elif 'HY-' in module_str:
                self.module = module_str
            else:
                self.module = module_str.strip('<>[]')
            self.content = match.group(5)
        else:
            # 检查特殊的崩溃相关行
            crash_related_patterns = [r'^\*\*\* First throw call stack:']
            ios_stack_pattern = r'^\s*\d+\s+\S+\s+0x[0-9a-fA-F]+(?:\s+0x[0-9a-fA-F]+\s*\+\s*\d+)?'

            if any(re.match(pattern, self.raw_line) for pattern in crash_related_patterns):
                self.is_stacktrace = True
                self.level = 'CRASH'
                self.module = 'Crash'
                self.content = self.raw_line
            elif re.match(ios_stack_pattern, self.raw_line):
                self.is_stacktrace = True
                self.level = 'STACKTRACE'
                self.module = 'Crash-Stack'
                self.content = self.raw_line
            else:
                self.level = 'OTHER'
                self.module = 'Unknown'
                self.content = self.raw_line

class FileGroup:
    def __init__(self, base_name):
        self.base_name = base_name
        self.files = []
        self.entries = []

# 测试崩溃日志
crash_logs = [
    '[E][2025-09-21 +8.0 16:56:39.129][0, 5453155200][<ERROR><HY-Default>][CrashReportManager.m, attachmentForException, 204][*** Terminating app due to uncaught exception \'NSGenericException\', reason: \'Unable to activate constraint\']',
    '[I][2025-09-21 +8.0 16:56:39.130][0, 5453155200][mars]Normal log message',
    '*** First throw call stack:',
    '0  CoreFoundation                 0x000000019124c0c0 0x0000000191132000 + 1155264',
    '1  libobjc.A.dylib                0x000000018e6e5abc objc_exception_throw + 88',
]

print("=" * 50)
print("测试崩溃日志解析")
print("=" * 50)

# 创建文件组
group = FileGroup('test')
group.files = ['test.xlog']

# 解析每行日志
entries = []
for line in crash_logs:
    entry = LogEntry(line, 'test.xlog')
    entries.append(entry)
    print(f"\n行: {line[:80]}...")
    print(f"  级别: {entry.level}")
    print(f"  模块: {entry.module}")
    print(f"  是否崩溃: {entry.is_crash}")

group.entries = entries

# 后处理崩溃日志
print("\n" + "=" * 50)
print("后处理前的模块统计:")
modules_before = defaultdict(list)
for entry in entries:
    modules_before[entry.module].append(entry)
for module, items in modules_before.items():
    print(f"  {module}: {len(items)}条")

# 简化的后处理函数
def post_process_crash_logs(group):
    """后处理崩溃日志"""
    entries = group.entries

    # 找出所有崩溃相关日志的位置（包括CrashReportManager和First throw call stack）
    crash_indices = []
    for i, entry in enumerate(entries):
        # CrashReportManager崩溃日志
        if (entry.is_crash and entry.level == 'CRASH' and
            'CrashReportManager.m' in getattr(entry, 'content', '')):
            crash_indices.append(i)
        # *** First throw call stack: 标记
        elif entry.level == 'CRASH' and '*** First throw call stack' in getattr(entry, 'content', ''):
            crash_indices.append(i)

    print(f"找到崩溃位置: {crash_indices}")

    # 为每个崩溃位置，将后续的堆栈信息归入Crash模块
    for crash_idx in crash_indices:
        print(f"处理崩溃日志 at index {crash_idx}")
        # 向后查找崩溃相关的信息
        i = crash_idx + 1
        while i < len(entries):
            entry = entries[i]
            print(f"  检查 index {i}: module={entry.module}, level={entry.level}")

            # 如果是iOS堆栈格式，归入Crash
            if entry.module == 'Crash-Stack':
                print(f"    -> 转换为Crash模块")
                entry.module = 'Crash'
                entry.level = 'CRASH'
                i += 1
            # 如果是OTHER类型且内容为空或只有少量字符，可能是堆栈的一部分
            elif entry.level == 'OTHER' and len(entry.content.strip()) < 5:
                entry.module = 'Crash'
                entry.level = 'CRASH'
                i += 1
            # 如果遇到下一条格式化的日志（有时间戳的），停止
            elif entry.level in ['ERROR', 'WARNING', 'INFO', 'DEBUG']:
                break
            else:
                i += 1

    # 清理非崩溃上下文的Crash-Stack标记
    for entry in entries:
        if entry.module == 'Crash-Stack':
            # 如果没有被处理为Crash，说明不是真正的崩溃堆栈
            entry.module = 'System'
            entry.level = 'INFO'
            entry.is_stacktrace = False

# 执行后处理
post_process_crash_logs(group)

print("\n后处理后的模块统计:")
modules_after = defaultdict(list)
for entry in group.entries:
    modules_after[entry.module].append(entry)

for module, items in modules_after.items():
    print(f"  {module}: {len(items)}条")
    for item in items:
        print(f"    - {item.level}: {item.content[:50] if item.content else 'N/A'}...")

# 检查Crash模块
if 'Crash' in modules_after:
    print(f"\n✅ Crash模块已创建，包含 {len(modules_after['Crash'])} 条日志")
else:
    print("\n❌ Crash模块未创建")
    print("可用模块:", list(modules_after.keys()))