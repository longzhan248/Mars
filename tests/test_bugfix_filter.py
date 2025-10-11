#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
过滤功能回归测试 - 修复keyword_lower为None的Bug
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'gui', 'modules'))

from data_models import LogEntry
from filter_search import FilterSearchManager


def test_filter_without_keyword():
    """测试没有关键词的过滤（Bug修复验证）"""
    print("=" * 60)
    print("过滤功能回归测试")
    print("=" * 60)

    # 创建测试数据
    entries = [
        LogEntry("[I][2025-09-21 +8.0 13:09:49][Thread-1][Module] INFO message 1", "test.log"),
        LogEntry("[E][2025-09-21 +8.0 13:09:50][Thread-2][Module] ERROR message 2", "test.log"),
        LogEntry("[W][2025-09-21 +8.0 13:09:51][Thread-3][Module] WARNING message 3", "test.log"),
    ]

    filter_manager = FilterSearchManager()

    # 测试1: 没有任何过滤条件
    print("\n测试1: 没有任何过滤条件")
    result = filter_manager.filter_entries(entries)
    print(f"  结果: {len(result)} 条 (预期: 3)")
    assert len(result) == 3, "❌ 失败：应返回所有条目"
    print("  ✅ 通过")

    # 测试2: 只有级别过滤
    print("\n测试2: 只有级别过滤")
    result = filter_manager.filter_entries(entries, level="ERROR")
    print(f"  结果: {len(result)} 条 (预期: 1)")
    assert len(result) == 1, "❌ 失败：应只返回ERROR"
    print("  ✅ 通过")

    # 测试3: 级别 + 模块过滤（无关键词）
    print("\n测试3: 级别 + 模块过滤")
    result = filter_manager.filter_entries(entries, level="ERROR", module="Module")
    print(f"  结果: {len(result)} 条 (预期: 1)")
    assert len(result) == 1, "❌ 失败"
    print("  ✅ 通过")

    # 测试4: 空关键词（edge case）
    print("\n测试4: 空关键词")
    result = filter_manager.filter_entries(entries, keyword="", search_mode="普通")
    print(f"  结果: {len(result)} 条 (预期: 3)")
    assert len(result) == 3, "❌ 失败：空关键词应返回全部"
    print("  ✅ 通过")

    # 测试5: 正常关键词搜索
    print("\n测试5: 正常关键词搜索")
    result = filter_manager.filter_entries(entries, keyword="ERROR", search_mode="普通")
    print(f"  结果: {len(result)} 条 (预期: 1)")
    assert len(result) == 1, "❌ 失败"
    print("  ✅ 通过")

    # 测试6: 正则搜索
    print("\n测试6: 正则搜索")
    result = filter_manager.filter_entries(entries, keyword="message [12]", search_mode="正则")
    print(f"  结果: {len(result)} 条 (预期: 2)")
    assert len(result) == 2, "❌ 失败"
    print("  ✅ 通过")

    # 测试7: 组合过滤
    print("\n测试7: 组合过滤（级别+关键词）")
    result = filter_manager.filter_entries(
        entries,
        level="INFO",
        keyword="message",
        search_mode="普通"
    )
    print(f"  结果: {len(result)} 条 (预期: 1)")
    assert len(result) == 1, "❌ 失败"
    print("  ✅ 通过")

    print("\n" + "=" * 60)
    print("✅ 所有测试通过！Bug已修复！")
    print("=" * 60)
    print("\n修复内容:")
    print("  - 问题: keyword_lower 可能为 None")
    print("  - 原因: 优化时没有正确初始化变量")
    print("  - 修复: 添加 None 检查和正确初始化")
    print("  - 影响: 无关键词的过滤现在正常工作")


if __name__ == "__main__":
    try:
        test_filter_without_keyword()
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
