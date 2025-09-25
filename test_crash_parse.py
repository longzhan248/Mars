#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试崩溃日志解析"""

import sys
import re

# 模拟 LogEntry 类
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
        # 简化的解析逻辑
        mars_pattern = r'^\[([A-Z])\]\[([^\]]+)\]\[([^\]]+)\]\[<([^>]+)><([^>]+)>\]\[([^\]]+)\](.*)$'
        match = re.match(mars_pattern, self.raw_line)

        print(f"尝试匹配: {self.raw_line[:100]}...")
        print(f"匹配结果: {match is not None}")

        if match:
            print(f"匹配组数: {len(match.groups())}")
            for i, g in enumerate(match.groups(), 1):
                print(f"  组{i}: {g[:50] if g and len(g) > 50 else g}")
            self.level = self._map_level(match.group(1))
            self.timestamp = match.group(2)
            self.thread_id = match.group(3)
            tag1 = match.group(4)
            self.module = match.group(5)
            location = match.group(6)
            self.content = match.group(7) if len(match.groups()) >= 7 else ""

            print(f"  解析后 - level:{self.level}, module:{self.module}")
            print(f"  location: {location}")
            print(f"  content: {self.content[:100]}")

            # 检测CrashReportManager崩溃日志
            # 注意：CrashReportManager.m 在 location 中，不是 content 中
            is_crash_report = (
                self.level == 'ERROR' and
                self.module == 'HY-Default' and
                'CrashReportManager.m' in location and
                '*** Terminating app due to uncaught exception' in self.content
            )

            if is_crash_report:
                self.is_crash = True
                self.level = 'CRASH'
                self.module = 'Crash'
                print(f"✅ 检测到崩溃日志: module={self.module}, level={self.level}")
        else:
            print(f"❌ 无法解析: {self.raw_line[:100]}")
            self.level = 'OTHER'
            self.module = 'Unknown'
            self.content = self.raw_line

    def _map_level(self, level_char):
        level_map = {
            'D': 'DEBUG',
            'I': 'INFO',
            'W': 'WARNING',
            'E': 'ERROR',
            'F': 'FATAL'
        }
        return level_map.get(level_char.upper(), 'OTHER')


# 测试崩溃日志
crash_log = """[E][2025-09-21 +8.0 16:56:39.129][0, 5453155200][<ERROR><HY-Default>][CrashReportManager.m, attachmentForException, 204][*** Terminating app due to uncaught exception 'NSGenericException', reason: 'Unable to activate constraint with anchors <NSLayoutYAxisAnchor:0x161aa3ec0 "SVGAPlayer:0x173bb7480.bottom"> and <NSLayoutYAxisAnchor:0x161ba27c0 "huhuAudio.PerhapsCenturyDYInteractiveGameWatchTrueWordsView:0x16a715800.bottom"> because they have no common ancestor.  Does the constraint or its anchors reference items in different view hierarchies?  That's illegal.'"""

print("=" * 50)
print("测试崩溃日志解析")
print("=" * 50)

# 解析崩溃日志
entry = LogEntry(crash_log)

print(f"\n解析结果:")
print(f"  原始级别: ERROR -> {entry.level}")
print(f"  原始模块: HY-Default -> {entry.module}")
print(f"  是否崩溃: {entry.is_crash}")
print(f"  内容片段: {entry.content[:100]}...")

# 模拟模块数据收集
modules_data = {}
if entry.module not in modules_data:
    modules_data[entry.module] = []
modules_data[entry.module].append(entry)

print(f"\n模块列表: {list(modules_data.keys())}")
print(f"Crash模块条目数: {len(modules_data.get('Crash', []))}")