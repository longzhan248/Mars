#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI导航快捷键管理器

负责管理日志导航相关的键盘快捷键。

快捷键列表:
- Ctrl+[ : 后退到上一个浏览位置
- Ctrl+] : 前进到下一个位置
- Ctrl+G : 跳转到指定行号
- Ctrl+M : 清除所有AI标记
"""

import tkinter as tk
from tkinter import simpledialog


class NavigationShortcuts:
    """
    导航快捷键管理器

    使用示例:
        shortcuts = NavigationShortcuts(app, navigator)
        shortcuts.setup()
    """

    def __init__(self, app, navigator):
        """
        初始化快捷键管理器

        Args:
            app: 主应用实例
            navigator: LogNavigator实例
        """
        self.app = app
        self.navigator = navigator

    def setup(self):
        """设置所有导航快捷键"""
        try:
            # Ctrl+[ : 后退
            self.app.root.bind_all("<Control-bracketleft>", self._on_go_back)
            # Ctrl+] : 前进
            self.app.root.bind_all("<Control-bracketright>", self._on_go_forward)
            # Ctrl+G : 跳转到指定行
            self.app.root.bind_all("<Control-g>", self._on_goto_line)
            # Ctrl+M : 清除所有标记
            self.app.root.bind_all("<Control-m>", self._on_clear_marks)

            print("✅ 导航快捷键已设置: Ctrl+[ (后退) | Ctrl+] (前进) | Ctrl+G (跳转) | Ctrl+M (清除标记)")

        except Exception as e:
            print(f"⚠️  设置导航快捷键失败: {e}")

    def _on_go_back(self, event=None) -> str:
        """快捷键: 后退"""
        if self.navigator:
            if self.navigator.go_back():
                self._show_message("⬅️  后退")
            else:
                self._show_message("⚠️  没有更早的历史记录")
        else:
            self._show_message("⚠️  导航器未初始化")
        return "break"

    def _on_go_forward(self, event=None) -> str:
        """快捷键: 前进"""
        if self.navigator:
            if self.navigator.go_forward():
                self._show_message("➡️  前进")
            else:
                self._show_message("⚠️  没有更新的历史记录")
        else:
            self._show_message("⚠️  导航器未初始化")
        return "break"

    def _on_goto_line(self, event=None) -> str:
        """快捷键: 跳转到指定行"""
        line_num = simpledialog.askinteger(
            "跳转到行",
            "请输入行号:",
            parent=self.app.root,
            minvalue=1
        )

        if line_num and self.navigator:
            if self.navigator.jump_to_line(line_num, reason="快捷键跳转"):
                self._show_message(f"✓ 已跳转到第 {line_num} 行")
            else:
                self._show_message(f"✗ 跳转失败")
        return "break"

    def _on_clear_marks(self, event=None) -> str:
        """快捷键: 清除所有标记"""
        if self.navigator:
            self.navigator.clear_marks()
            self._show_message("✓ 已清除所有标记")
        else:
            self._show_message("⚠️  导航器未初始化")
        return "break"

    def _show_message(self, message: str, duration: int = 3000):
        """在状态栏显示消息"""
        try:
            if hasattr(self.app, 'file_stats_var'):
                # 保存原始状态
                original_status = self.app.file_stats_var.get()

                # 显示消息
                self.app.file_stats_var.set(message)

                # 3秒后恢复
                self.app.root.after(duration, lambda: self.app.file_stats_var.set(original_status))
            else:
                print(message)
        except Exception as e:
            print(f"显示状态消息失败: {e}")
