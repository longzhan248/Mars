#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from collections import defaultdict, Counter

class LogEntry:
    def __init__(self, line, filename=''):
        self.raw_line = line.rstrip('\n')
        self.filename = filename
        self.level = 'OTHER'
        self.timestamp = None
        self.module = 'System'
        self.content = None
        self.thread_id = None
        self.is_crash = False
        self.is_stacktrace = False
        self.parse()

    def parse(self):
        # 尝试匹配带有两个模块标签的格式（崩溃日志特殊格式）
        crash_pattern = r'^\[([IWEDVF])\]\[([^\]]+)\]\[([^\]]+)\]\[<([^>]+)><([^>]+)>\]\[([^\]]+)\](.*)$'
        crash_match = re.match(crash_pattern, self.raw_line)

        if crash_match:
            level_map = {
                'I': 'INFO',
                'W': 'WARNING',
                'E': 'ERROR',
                'D': 'DEBUG',
                'V': 'VERBOSE',
                'F': 'FATAL'
            }
            self.level = level_map.get(crash_match.group(1), crash_match.group(1))
            self.timestamp = crash_match.group(2)
            self.thread_id = crash_match.group(3)
            tag1 = crash_match.group(4)
            tag2 = crash_match.group(5)
            location = crash_match.group(6)
            self.content = crash_match.group(7)

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

        # 标准日志格式: [级别][时间][线程ID][模块]内容
        pattern = r'^\[([IWEDVF])\]\[([^\]]+)\]\[([^\]]+)\]\[([^\]]+)\](.*)$'
        match = re.match(pattern, self.raw_line)

        if match:
            level_map = {
                'I': 'INFO',
                'W': 'WARNING',
                'E': 'ERROR',
                'D': 'DEBUG',
                'V': 'VERBOSE',
                'F': 'FATAL'
            }
            self.level = level_map.get(match.group(1), match.group(1))
            self.timestamp = match.group(2)
            self.thread_id = match.group(3)

            # 提取模块
            module_str = match.group(4)
            self.module = module_str
            self.content = match.group(5).strip()
        else:
            # 检查特殊的崩溃相关行
            crash_related_patterns = [
                r'^\*\*\* First throw call stack:',
            ]

            ios_stack_pattern = r'^\s*\d+\s+\S+\s+0x[0-9a-fA-F]+(?:\s+0x[0-9a-fA-F]+\s*\+\s*\d+)?'

            if any(re.match(pattern, self.raw_line) for pattern in crash_related_patterns):
                # 崩溃相关的特殊行
                self.is_stacktrace = True
                self.level = 'CRASH'
                self.module = 'Crash'
                self.content = self.raw_line
            elif re.match(ios_stack_pattern, self.raw_line):
                # iOS 堆栈格式（可能是崩溃堆栈，也可能不是）
                self.is_stacktrace = True
                self.level = 'STACKTRACE'
                self.module = 'Crash-Stack'  # 临时标记，后续验证
                self.content = self.raw_line
            else:
                # 非标准格式
                self.level = 'OTHER'
                self.module = 'System'
                self.content = self.raw_line

# 模拟几条日志，包括崩溃日志
logs = [
    "[I][2025-09-21 +8.0 16:56:38.000][0, 1234][Room] Normal log message",
    "[E][2025-09-21 +8.0 16:56:39.129][0, 5453155200][<ERROR><HY-Default>][CrashReportManager.m, attachmentForException, 204][*** Terminating app due to uncaught exception 'NSGenericException', reason: 'Unable to activate constraint']",
    "*** First throw call stack:",
    "0  CoreFoundation                 0x000000019124c0c0 0x0000000191132000 + 1155264",
    "1  libobjc.A.dylib                0x000000018e6e5abc objc_exception_throw + 88",
    "[W][2025-09-21 +8.0 16:56:40.000][0, 1234][Network] Warning message",
]

# 创建LogEntry对象
entries = []
for log in logs:
    entry = LogEntry(log, "test.xlog")
    entries.append(entry)
    print(f"Parsed: Level={entry.level:10s} Module={entry.module:15s} IsCrash={entry.is_crash}")

# 模拟post_process_crash_logs
class MockGroup:
    def __init__(self, entries):
        self.entries = entries

group = MockGroup(entries)

# 后处理崩溃日志
crash_indices = []
for i, entry in enumerate(group.entries):
    if (entry.is_crash and entry.level == 'CRASH' and
        'CrashReportManager.m' in getattr(entry, 'content', '')):
        crash_indices.append(i)
    elif entry.level == 'CRASH' and '*** First throw call stack' in getattr(entry, 'content', ''):
        crash_indices.append(i)

print(f"\nCrash indices found: {crash_indices}")

for crash_idx in crash_indices:
    i = crash_idx + 1
    while i < len(group.entries):
        entry = group.entries[i]
        if entry.module == 'Crash-Stack':
            entry.module = 'Crash'
            entry.level = 'CRASH'
            print(f"Updated stack entry {i} to Crash module")
            i += 1
        elif entry.level == 'OTHER' and len(entry.content.strip()) < 5:
            entry.module = 'Crash'
            entry.level = 'CRASH'
            print(f"Updated OTHER entry {i} to Crash module")
            i += 1
        elif entry.level in ['ERROR', 'WARNING', 'INFO', 'DEBUG']:
            break
        else:
            i += 1

# 清理非崩溃上下文的Crash-Stack标记
for entry in group.entries:
    if entry.module == 'Crash-Stack':
        entry.module = 'System'
        entry.level = 'INFO'
        entry.is_stacktrace = False

# 模拟analyze_logs
modules_data = defaultdict(list)
module_stats = Counter()

for entry in entries:
    module_stats[entry.module] += 1
    modules_data[entry.module].append(entry)

print(f"\n===== Analysis Results =====")
print(f"Modules found: {list(modules_data.keys())}")
for module, count in module_stats.items():
    print(f"  {module}: {count} entries")

# 特别检查Crash模块
crash_entries = modules_data.get('Crash', [])
print(f"\nCrash module has {len(crash_entries)} entries")
if crash_entries:
    for i, entry in enumerate(crash_entries):
        print(f"  Entry {i}: {entry.content[:50] if entry.content else entry.raw_line[:50]}...")