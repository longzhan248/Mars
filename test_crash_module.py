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

# 测试崩溃日志解析
test_log = """[E][2025-09-21 +8.0 16:56:39.129][0, 5453155200][<ERROR><HY-Default>][CrashReportManager.m, attachmentForException, 204][*** Terminating app due to uncaught exception 'NSGenericException', reason: 'Unable to activate constraint with anchors']"""

entry = LogEntry(test_log)
print(f"Level: {entry.level}")
print(f"Module: {entry.module}")
print(f"Is Crash: {entry.is_crash}")
print(f"Content: {entry.content[:50]}...")

# 测试模块数据收集
modules_data = defaultdict(list)
entries = [entry]

for e in entries:
    modules_data[e.module].append(e)

print(f"\nModules found: {list(modules_data.keys())}")
print(f"Crash module entries: {len(modules_data.get('Crash', []))}")