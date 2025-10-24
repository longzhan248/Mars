#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI右键菜单管理器

负责管理日志查看器的右键菜单，提供AI分析、导航等功能。
"""

import tkinter as tk
from tkinter import messagebox
from typing import Optional


class ContextMenuManager:
    """
    右键菜单管理器

    使用示例:
        menu_mgr = ContextMenuManager(app, ai_analysis_handler)
        menu_mgr.setup()
    """

    def __init__(self, app, ai_analysis_handler, smart_features_available=False):
        """
        初始化右键菜单管理器

        Args:
            app: 主应用实例
            ai_analysis_handler: AI分析处理器 (包含分析方法的对象)
            smart_features_available: 是否启用智能功能
        """
        self.app = app
        self.handler = ai_analysis_handler
        self.smart_features = smart_features_available
        self.context_menu = None

    def setup(self):
        """设置右键菜单"""
        try:
            # 创建右键菜单
            self.context_menu = tk.Menu(self.app.log_text, tearoff=0)

            # 添加AI分析菜单项
            self.context_menu.add_command(
                label="🤖 AI分析此日志",
                command=self.handler.ai_analyze_selected_log
            )
            self.context_menu.add_command(
                label="🤖 AI解释错误原因",
                command=self.handler.ai_explain_error
            )
            self.context_menu.add_command(
                label="🤖 AI查找相关日志",
                command=self.handler.ai_find_related_logs
            )

            self.context_menu.add_separator()

            # 导航功能 (智能功能)
            if self.smart_features:
                self.context_menu.add_command(
                    label="📊 查看问题链路图",
                    command=self.handler.show_problem_graph
                )
                self.context_menu.add_command(
                    label="📈 查看缓存统计",
                    command=self.handler.show_cache_dashboard
                )
                self.context_menu.add_separator()

            # 标准操作
            self.context_menu.add_command(
                label="📋 复制",
                command=self._copy_selected_text
            )
            self.context_menu.add_command(
                label="🔍 搜索此内容",
                command=self._search_selected_text
            )

            # 绑定右键点击事件
            self.app.log_text.bind("<Button-3>", self._show_menu)
            self.app.log_text.bind("<Button-2>", self._show_menu)  # macOS
            self.app.log_text.bind("<Control-Button-1>", self._show_menu)  # macOS Ctrl+Click

            print("✅ 右键菜单已设置")

        except Exception as e:
            print(f"⚠️  右键菜单设置失败: {str(e)}")

    def _show_menu(self, event):
        """显示右键菜单"""
        try:
            self.context_menu.post(event.x_root, event.y_root)
        except Exception as e:
            print(f"显示右键菜单失败: {str(e)}")

    def _copy_selected_text(self):
        """复制选中的文本"""
        try:
            if self.app.log_text.tag_ranges("sel"):
                selected_text = self.app.log_text.get("sel.first", "sel.last")
                self.app.root.clipboard_clear()
                self.app.root.clipboard_append(selected_text)
        except Exception as e:
            print(f"复制文本失败: {str(e)}")

    def _search_selected_text(self):
        """搜索选中的文本"""
        try:
            if self.app.log_text.tag_ranges("sel"):
                selected_text = self.app.log_text.get("sel.first", "sel.last").strip()
                if selected_text:
                    self.app.search_var.set(selected_text)
                    self.app.search_logs()
        except Exception as e:
            print(f"搜索文本失败: {str(e)}")
