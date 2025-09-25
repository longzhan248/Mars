#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re

# 用户提供的实际崩溃日志
crash_log = "[E][2025-09-21 +8.0 16:56:39.129][0, 5453155200][<ERROR><HY-Default>][CrashReportManager.m, attachmentForException, 204][*** Terminating app due to uncaught exception 'NSGenericException', reason: 'Unable to activate constraint with anchors']"

# 测试正则表达式
crash_pattern = r'^\[([IWEDVF])\]\[([^\]]+)\]\[([^\]]+)\]\[<([^>]+)><([^>]+)>\]\[([^\]]+)\](.*)$'
match = re.match(crash_pattern, crash_log)

if match:
    print("✓ 正则表达式匹配成功！")
    print(f"Level: {match.group(1)}")
    print(f"Timestamp: {match.group(2)}")
    print(f"Thread: {match.group(3)}")
    print(f"Tag1: {match.group(4)}")
    print(f"Tag2: {match.group(5)}")
    print(f"Location: {match.group(6)}")
    print(f"Content: {match.group(7)}")

    # 检查崩溃检测条件
    level = 'ERROR' if match.group(1) == 'E' else match.group(1)
    tag2 = match.group(5)
    location = match.group(6)
    content = match.group(7)

    print(f"\n崩溃检测条件:")
    print(f"1. level == 'ERROR': {level == 'ERROR'}")
    print(f"2. tag2 == 'HY-Default': {tag2 == 'HY-Default'}")
    print(f"3. 'CrashReportManager.m' in location: {'CrashReportManager.m' in location}")
    print(f"4. '*** Terminating app due to uncaught exception' in content: {'*** Terminating app due to uncaught exception' in content}")

    is_crash = (level == 'ERROR' and
                tag2 == 'HY-Default' and
                'CrashReportManager.m' in location and
                '*** Terminating app due to uncaught exception' in content)

    print(f"\n最终判断为崩溃日志: {is_crash}")
    if is_crash:
        print("→ Module将被设置为: Crash")
else:
    print("✗ 正则表达式不匹配！")