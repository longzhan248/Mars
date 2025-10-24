#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI交互管理器
负责管理AI助手窗口、右键菜单和日志上下文分析功能
"""

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional, Tuple, List, Any


class AIInteractionManager:
    """AI交互管理器 - 处理AI助手的所有交互逻辑"""

    def __init__(self, parent_app):
        """
        初始化AI交互管理器

        Args:
            parent_app: 父应用程序实例(MarsLogAnalyzerPro)
        """
        self.app = parent_app
        self.ai_assistant = None
        self.ai_window = None
        self.log_context_menu = None

    def setup_ai_features(self) -> None:
        """设置AI功能（按钮和右键菜单）"""
        # 延迟执行以确保父类UI已完成创建
        self.app.root.after(100, self._add_button_delayed)
        self.setup_context_menu()

    def _add_button_delayed(self) -> None:
        """延迟添加AI助手按钮到工具栏"""
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
                                    command=self.open_ai_assistant_window
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
                                            command=self.open_ai_assistant_window
                                        )
                                        ai_button.grid(row=1, column=9, padx=2, pady=3, sticky='w')
                                        print("✅ AI助手按钮已添加到工具栏")
                                        return
                                except (tk.TclError, AttributeError):
                                    continue

            print("⚠️  未找到搜索过滤区域，尝试添加到主窗口")
            # 如果找不到，尝试在主菜单添加
            self._add_to_menu()

        except Exception as e:
            print(f"❌ 添加按钮失败: {str(e)}")
            import traceback
            traceback.print_exc()

    def _add_to_menu(self) -> None:
        """作为备选方案，添加到菜单栏"""
        try:
            if hasattr(self.app, 'menu_bar'):
                # 创建AI助手菜单
                ai_menu = tk.Menu(self.app.menu_bar, tearoff=0)
                ai_menu.add_command(
                    label="打开AI助手",
                    command=self.open_ai_assistant_window
                )
                self.app.menu_bar.add_cascade(label="🤖 AI", menu=ai_menu)
                print("✅ AI助手已添加到菜单栏")
        except Exception as e:
            print(f"❌ 添加到菜单失败: {str(e)}")

    def open_ai_assistant_window(self) -> None:
        """打开AI助手窗口"""
        try:
            # 如果窗口已存在，直接显示
            if self.ai_window and self.ai_window.winfo_exists():
                self.ai_window.deiconify()
                self.ai_window.lift()
                return

            # 导入AI助手面板
            try:
                from modules.ai_assistant import AIAssistantPanel
            except ImportError:
                from gui.modules.ai_assistant import AIAssistantPanel

            # 创建新窗口
            self.ai_window = tk.Toplevel(self.app.root)
            self.ai_window.title("AI智能诊断助手")
            self.ai_window.geometry("500x700")

            # 设置窗口图标
            try:
                self.ai_window.iconbitmap(self.app.root.iconbitmap())
            except:
                pass

            # 创建AI助手面板
            self.ai_assistant = AIAssistantPanel(self.ai_window, self.app)

            # 窗口关闭时隐藏而不是销毁
            self.ai_window.protocol("WM_DELETE_WINDOW", self.ai_window.withdraw)

        except Exception as e:
            messagebox.showerror("错误", f"无法打开AI助手窗口: {str(e)}")
            import traceback
            traceback.print_exc()

    def setup_context_menu(self) -> None:
        """设置日志查看器的右键菜单"""
        try:
            # 创建右键菜单
            self.log_context_menu = tk.Menu(self.app.log_text, tearoff=0)

            # 添加AI分析菜单项
            self.log_context_menu.add_command(
                label="🤖 AI分析此日志",
                command=self.ai_analyze_selected_log
            )
            self.log_context_menu.add_command(
                label="🤖 AI解释错误原因",
                command=self.ai_explain_error
            )
            self.log_context_menu.add_command(
                label="🤖 AI查找相关日志",
                command=self.ai_find_related_logs
            )

            self.log_context_menu.add_separator()

            # 添加标准操作
            self.log_context_menu.add_command(
                label="📋 复制",
                command=self.copy_selected_text
            )
            self.log_context_menu.add_command(
                label="🔍 搜索此内容",
                command=self.search_selected_text
            )

            # 绑定右键点击事件
            self.app.log_text.bind("<Button-3>", self.show_context_menu)
            self.app.log_text.bind("<Button-2>", self.show_context_menu)  # macOS
            self.app.log_text.bind("<Control-Button-1>", self.show_context_menu)  # macOS

        except Exception as e:
            print(f"右键菜单设置失败: {str(e)}")

    def show_context_menu(self, event: tk.Event) -> None:
        """显示右键菜单"""
        try:
            self.log_context_menu.post(event.x_root, event.y_root)
        except Exception as e:
            print(f"显示右键菜单失败: {str(e)}")

    def get_selected_log_context(self) -> Tuple[Any, List, List]:
        """
        获取选中日志及其上下文

        Returns:
            (target_entry, context_before, context_after)
        """
        try:
            # 获取选中的文本
            if self.app.log_text.tag_ranges("sel"):
                selected_text = self.app.log_text.get("sel.first", "sel.last")
            else:
                # 如果没有选中，获取当前行
                current_line = self.app.log_text.index("insert").split('.')[0]
                selected_text = self.app.log_text.get(f"{current_line}.0", f"{current_line}.end")

            if not selected_text.strip():
                return None, None, None

            # 从filtered_entries中查找匹配的日志
            entries = getattr(self.app, 'filtered_entries', None) or self.app.log_entries
            matched_entries = [
                entry for entry in entries
                if selected_text.strip() in entry.content or selected_text.strip() in entry.raw_line
            ]

            if not matched_entries:
                return selected_text, [], []

            # 获取第一个匹配的日志和上下文
            target_entry = matched_entries[0]
            all_entries = self.app.log_entries

            try:
                target_idx = all_entries.index(target_entry)
            except ValueError:
                return selected_text, [], []

            # 获取上下文（前后各5条）
            context_before = all_entries[max(0, target_idx-5):target_idx]
            context_after = all_entries[target_idx+1:min(len(all_entries), target_idx+6)]

            return target_entry, context_before, context_after

        except Exception as e:
            print(f"获取日志上下文失败: {str(e)}")
            return None, None, None

    def ai_analyze_selected_log(self, log_text: Optional[str] = None) -> None:
        """
        AI分析选中的日志

        Args:
            log_text: 可选的日志文本。如果提供，直接分析该文本；否则获取选中的日志
        """
        if not self.ai_assistant:
            self.open_ai_assistant_window()
            self.app.root.after(200, lambda: self._do_ai_analyze(log_text))
            return

        self._do_ai_analyze(log_text)

    def _do_ai_analyze(self, log_text: Optional[str] = None) -> None:
        """执行AI分析（内部方法）"""
        if not self.ai_assistant:
            messagebox.showwarning("警告", "AI助手初始化失败，请手动点击'🤖 AI助手'按钮")
            return

        if log_text is not None:
            # 直接分析提供的文本
            question = f"分析以下日志的问题和原因：\n\n{log_text[:500]}"
            self.ai_assistant.chat_panel.question_var.set(question)
            self.ai_assistant.ask_question()
            return

        # 使用上下文获取逻辑
        target, context_before, context_after = self.get_selected_log_context()

        if not target:
            messagebox.showinfo("提示", "请选择要分析的日志")
            return

        # 获取上下文参数配置
        params = self.ai_assistant.get_context_params()
        context_limit = params.get('crash_before', 5)

        # 构建分析问题
        if isinstance(target, str):
            question = f"分析这条日志:\n{target}"
        else:
            context_info = ""
            if context_before:
                context_info += f"\n\n【上下文 - 前{min(len(context_before), context_limit)}条日志】:\n"
                for entry in context_before[-context_limit:]:
                    context_info += f"[{entry.level}] {entry.content[:200]}\n"

            question = f"分析这条{target.level}日志:\n【目标日志】: {target.content}"
            if context_info:
                question += context_info

        self.ai_assistant.chat_panel.question_var.set(question)
        self.ai_assistant.ask_question()

    def ai_explain_error(self, log_text: Optional[str] = None) -> None:
        """
        AI解释错误原因

        Args:
            log_text: 可选的日志文本
        """
        if not self.ai_assistant:
            self.open_ai_assistant_window()
            self.app.root.after(200, lambda: self._do_ai_explain(log_text))
            return

        self._do_ai_explain(log_text)

    def _do_ai_explain(self, log_text: Optional[str] = None) -> None:
        """执行AI错误解释（内部方法）"""
        if not self.ai_assistant:
            messagebox.showwarning("警告", "AI助手初始化失败")
            return

        if log_text is not None:
            question = f"解释以下错误的原因、影响和解决方案：\n\n{log_text[:500]}"
            self.ai_assistant.chat_panel.question_var.set(question)
            self.ai_assistant.ask_question()
            return

        target, context_before, context_after = self.get_selected_log_context()

        if not target:
            messagebox.showinfo("提示", "请选择要解释的错误")
            return

        # 获取上下文参数
        params = self.ai_assistant.get_context_params()
        before_limit = params.get('crash_before', 5)
        after_limit = params.get('crash_after', 3)

        # 构建问题
        if isinstance(target, str):
            question = f"解释这个错误的原因和如何修复:\n{target}"
        else:
            context_info = ""
            if context_before:
                context_info += f"\n\n【上下文 - 前{min(len(context_before), before_limit)}条日志】:\n"
                for entry in context_before[-before_limit:]:
                    context_info += f"[{entry.level}] {entry.content[:200]}\n"

            if context_after:
                context_info += f"\n\n【上下文 - 后{min(len(context_after), after_limit)}条日志】:\n"
                for entry in context_after[:after_limit]:
                    context_info += f"[{entry.level}] {entry.content[:200]}\n"

            question = f"解释这个{target.level}的原因和如何修复:\n【目标日志】: {target.content}"
            if context_info:
                question += context_info

        self.ai_assistant.chat_panel.question_var.set(question)
        self.ai_assistant.ask_question()

    def ai_find_related_logs(self) -> None:
        """AI查找相关日志"""
        if not self.ai_assistant:
            self.open_ai_assistant_window()
            self.app.root.after(200, self._do_ai_find_related)
            return

        self._do_ai_find_related()

    def _do_ai_find_related(self) -> None:
        """执行AI查找相关日志（内部方法）"""
        if not self.ai_assistant:
            messagebox.showwarning("警告", "AI助手初始化失败")
            return

        target, context_before, context_after = self.get_selected_log_context()

        if not target:
            messagebox.showinfo("提示", "请选择参考日志")
            return

        # 获取搜索范围参数
        params = self.ai_assistant.get_context_params()
        search_limit = params.get('search_logs', 500)

        # 构建问题
        if isinstance(target, str):
            question = f"在日志中查找与此相关的其他日志:\n{target}"
        else:
            context_info = ""

            try:
                all_entries = getattr(self.app, 'log_entries', [])
                target_idx = all_entries.index(target)

                # 获取前后日志作为搜索范围
                half = search_limit // 2
                start = max(0, target_idx - half)
                end = min(len(all_entries), target_idx + half)
                sample_logs = all_entries[start:end]

                if sample_logs:
                    context_info += f"\n\n【搜索范围 - 共{len(sample_logs)}条日志】:\n"
                    # 显示前后各10条样本
                    for entry in sample_logs[:10]:
                        context_info += f"[{entry.level}] {entry.content[:150]}\n"

                    if len(sample_logs) > 20:
                        context_info += f"... (中间省略{len(sample_logs) - 20}条)\n"

                    for entry in sample_logs[-10:]:
                        context_info += f"[{entry.level}] {entry.content[:150]}\n"

            except (ValueError, AttributeError):
                pass

            question = f"在日志中查找与此{target.level}相关的其他日志:\n【目标日志】: {target.content}"
            if context_info:
                question += context_info
            else:
                question += "\n\n请在当前加载的所有日志中搜索。"

        self.ai_assistant.chat_panel.question_var.set(question)
        self.ai_assistant.ask_question()

    def copy_selected_text(self) -> None:
        """复制选中的文本"""
        try:
            if self.app.log_text.tag_ranges("sel"):
                selected_text = self.app.log_text.get("sel.first", "sel.last")
                self.app.root.clipboard_clear()
                self.app.root.clipboard_append(selected_text)
        except Exception as e:
            print(f"复制文本失败: {str(e)}")

    def search_selected_text(self) -> None:
        """搜索选中的文本"""
        try:
            if self.app.log_text.tag_ranges("sel"):
                selected_text = self.app.log_text.get("sel.first", "sel.last").strip()
                if selected_text:
                    self.app.search_var.set(selected_text)
                    self.app.search_logs()
        except Exception as e:
            print(f"搜索文本失败: {str(e)}")
