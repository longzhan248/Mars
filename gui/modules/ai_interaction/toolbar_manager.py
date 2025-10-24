#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI工具栏按钮管理器

负责在主窗口工具栏添加AI助手按钮。
"""

import tkinter as tk
from tkinter import ttk


class ToolbarManager:
    """
    工具栏管理器

    使用示例:
        toolbar_mgr = ToolbarManager(app, ai_window_handler)
        toolbar_mgr.setup()
    """

    def __init__(self, app, ai_window_handler):
        """
        初始化工具栏管理器

        Args:
            app: 主应用实例
            ai_window_handler: AI窗口处理器 (包含open_ai_assistant_window方法)
        """
        self.app = app
        self.handler = ai_window_handler

    def setup(self):
        """延迟添加AI助手按钮到工具栏"""
        # 延迟执行以确保父类UI已完成创建
        self.app.root.after(100, self._add_button_delayed)

    def _add_button_delayed(self):
        """延迟添加AI助手按钮"""
        try:
            # 查找search_frame（搜索与过滤的LabelFrame）
            if hasattr(self.app, 'log_frame'):
                for widget in self.app.log_frame.winfo_children():
                    # 第一层：检查是否是Frame或LabelFrame
                    if isinstance(widget, (tk.Frame, ttk.Frame, tk.LabelFrame, ttk.LabelFrame)):
                        # 检查是否是搜索与过滤框
                        try:
                            if widget.cget('text') == '搜索与过滤':
                                # 找到了，添加AI助手按钮
                                ai_button = ttk.Button(
                                    widget,
                                    text="🤖 AI助手",
                                    command=self.handler.open_ai_assistant_window
                                )
                                # 放在第2行第9列
                                ai_button.grid(row=1, column=9, padx=2, pady=3, sticky='w')
                                print("✅ AI助手按钮已添加到工具栏")
                                return
                        except (tk.TclError, AttributeError):
                            pass

                        # 递归检查子控件
                        for child in widget.winfo_children():
                            if isinstance(child, (tk.LabelFrame, ttk.LabelFrame)):
                                try:
                                    if child.cget('text') == '搜索与过滤':
                                        # 添加AI助手按钮
                                        ai_button = ttk.Button(
                                            child,
                                            text="🤖 AI助手",
                                            command=self.handler.open_ai_assistant_window
                                        )
                                        ai_button.grid(row=1, column=9, padx=2, pady=3, sticky='w')
                                        print("✅ AI助手按钮已添加到工具栏")
                                        return
                                except (tk.TclError, AttributeError):
                                    continue

            print("⚠️  未找到搜索过滤区域，尝试添加到菜单")
            # 如果找不到，尝试在主菜单添加
            self._add_to_menu()

        except Exception as e:
            print(f"❌ 添加按钮失败: {str(e)}")
            import traceback
            traceback.print_exc()

    def _add_to_menu(self):
        """作为备选方案，添加到菜单栏"""
        try:
            if hasattr(self.app, 'menu_bar'):
                # 创建AI助手菜单
                ai_menu = tk.Menu(self.app.menu_bar, tearoff=0)
                ai_menu.add_command(
                    label="打开AI助手",
                    command=self.handler.open_ai_assistant_window
                )
                self.app.menu_bar.add_cascade(label="🤖 AI", menu=ai_menu)
                print("✅ AI助手已添加到菜单栏")
        except Exception as e:
            print(f"❌ 添加到菜单失败: {str(e)}")
