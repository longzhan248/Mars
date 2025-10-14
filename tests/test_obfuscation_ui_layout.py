#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iOS混淆界面布局测试

测试非全屏模式下各个组件的可见性
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from tkinter import ttk


def test_layout_non_fullscreen():
    """测试非全屏模式下的布局"""
    from gui.modules.obfuscation_tab import ObfuscationTab

    root = tk.Tk()
    root.title('iOS混淆工具 - 布局测试')

    # 测试多种非全屏尺寸
    test_sizes = [
        (900, 650, "标准小窗口"),
        (1000, 700, "中等窗口"),
        (800, 600, "最小窗口")
    ]

    class MockApp:
        pass

    for width, height, desc in test_sizes:
        print(f"\n{'='*60}")
        print(f"测试: {desc} ({width}x{height})")
        print('='*60)

        root.geometry(f'{width}x{height}')

        # 清空窗口
        for widget in root.winfo_children():
            widget.destroy()

        # 创建标签页
        tab = ObfuscationTab(root, MockApp())
        tab.pack(fill=tk.BOTH, expand=True)

        # 更新窗口
        root.update()

        # 检查关键组件
        checks = {
            "标题": False,
            "快速配置": False,
            "项目配置": False,
            "混淆选项": False,
            "开始按钮": False,
            "停止按钮": False,
            "查看映射": False,
            "导出映射": False,
            "进度条": False,
            "日志区域": False
        }

        def check_widget(widget):
            """递归检查组件"""
            if isinstance(widget, ttk.Button):
                text = widget.cget('text')
                if '开始混淆' in text:
                    checks["开始按钮"] = True
                    # 检查按钮是否在可见区域
                    y = widget.winfo_y()
                    window_height = root.winfo_height()
                    if y < window_height:
                        print(f"  ✅ 开始按钮可见 (y={y}, 窗口高度={window_height})")
                    else:
                        print(f"  ❌ 开始按钮不可见 (y={y}, 窗口高度={window_height})")
                elif '停止' in text:
                    checks["停止按钮"] = True
                elif '查看映射' in text:
                    checks["查看映射"] = True
                elif '导出映射' in text:
                    checks["导出映射"] = True
            elif isinstance(widget, ttk.Label):
                text = widget.cget('text')
                if 'iOS代码混淆' in text:
                    checks["标题"] = True
                elif '快速配置' in text:
                    checks["快速配置"] = True
            elif isinstance(widget, ttk.LabelFrame):
                text = widget.cget('text')
                if '项目配置' in text:
                    checks["项目配置"] = True
                elif '混淆选项' in text:
                    checks["混淆选项"] = True
                elif '执行进度' in text:
                    checks["进度条"] = True
                elif '执行日志' in text:
                    checks["日志区域"] = True

            for child in widget.winfo_children():
                check_widget(child)

        check_widget(tab)

        # 输出检查结果
        print("\n组件可见性检查:")
        all_visible = True
        for name, visible in checks.items():
            status = "✅" if visible else "❌"
            print(f"  {status} {name}")
            if not visible:
                all_visible = False

        if all_visible:
            print(f"\n✅ 所有组件在 {desc} 下均可见")
        else:
            print(f"\n⚠️  部分组件在 {desc} 下不可见")

    root.destroy()
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)


def test_button_visibility_directly():
    """直接测试按钮区域的位置"""
    from gui.modules.obfuscation_tab import ObfuscationTab

    print("\n" + "="*60)
    print("直接测试按钮位置")
    print("="*60)

    root = tk.Tk()
    root.title('按钮位置测试')
    root.geometry('900x650')

    class MockApp:
        pass

    tab = ObfuscationTab(root, MockApp())
    tab.pack(fill=tk.BOTH, expand=True)

    root.update()

    # 获取窗口高度
    window_height = root.winfo_height()
    print(f"\n窗口高度: {window_height}px")

    # 查找按钮并检查位置
    def find_buttons(widget, indent=0):
        if isinstance(widget, ttk.Button):
            text = widget.cget('text')
            y = widget.winfo_y()
            height = widget.winfo_height()
            bottom = y + height

            in_view = bottom < window_height
            status = "✅" if in_view else "❌"

            print(f"  {status} {text:20s} y={y:4d}, height={height:3d}, bottom={bottom:4d}")

        for child in widget.winfo_children():
            find_buttons(child, indent + 2)

    print("\n按钮位置:")
    find_buttons(tab)

    root.destroy()
    print("\n测试完成")


if __name__ == '__main__':
    print("iOS混淆界面布局测试")
    print("="*60)

    # 运行测试
    test_layout_non_fullscreen()
    test_button_visibility_directly()

    print("\n✅ 所有测试完成")
