#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI交互管理器 (重构版 - 符合500行限制)

职责: 协调AI助手相关的所有交互组件
- 组件初始化和生命周期管理
- 各组件之间的协调
- AI分析逻辑的统一入口

具体功能已模块化到:
- ai_interaction.navigation_shortcuts - 导航快捷键
- ai_interaction.context_menu_manager - 右键菜单
- ai_interaction.toolbar_manager - 工具栏按钮
"""

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional, Tuple, List, Any

# 导入智能功能模块
try:
    from .ai_diagnosis.smart_context_extractor import SmartContextExtractor
    from .ai_diagnosis.log_navigator import LogNavigator, AIAnalysisParser
    from .ai_diagnosis.analysis_cache import get_global_cache
    SMART_FEATURES_AVAILABLE = True
except ImportError:
    SMART_FEATURES_AVAILABLE = False
    print("⚠️  智能AI功能模块未加载")

# 导入UI组件管理器
try:
    from .ai_interaction import NavigationShortcuts, ContextMenuManager, ToolbarManager
except ImportError:
    from ai_interaction import NavigationShortcuts, ContextMenuManager, ToolbarManager


class AIInteractionManager:
    """
    AI交互管理器 (协调器模式)

    职责:
    1. 管理AI助手窗口
    2. 协调各UI组件 (快捷键、菜单、工具栏)
    3. 提供AI分析的统一接口
    4. 管理智能功能 (导航器、缓存、上下文提取)
    """

    def __init__(self, parent_app):
        """初始化管理器"""
        self.app = parent_app

        # AI助手窗口
        self.ai_assistant = None
        self.ai_window = None

        # 智能功能组件
        self.navigator = None
        self.context_extractor = None
        self.analysis_cache = None

        # UI组件管理器
        self.shortcuts_mgr = None
        self.menu_mgr = None
        self.toolbar_mgr = None

        # 初始化智能功能
        if SMART_FEATURES_AVAILABLE:
            self._init_smart_features()

    def _init_smart_features(self):
        """初始化智能功能组件"""
        try:
            # 初始化日志导航器
            if hasattr(self.app, 'log_text'):
                all_entries = getattr(self.app, 'log_entries', [])
                self.navigator = LogNavigator(self.app.log_text, all_entries)
                print("✓ 日志导航器已初始化")

            # 初始化分析缓存
            self.analysis_cache = get_global_cache()
            print("✓ AI分析缓存已初始化")

        except Exception as e:
            print(f"⚠️  智能功能初始化失败: {e}")

    def setup_ai_features(self):
        """设置AI功能（协调所有组件）"""
        # 设置工具栏按钮
        self.toolbar_mgr = ToolbarManager(self.app, self)
        self.toolbar_mgr.setup()

        # 设置右键菜单
        self.menu_mgr = ContextMenuManager(self.app, self, SMART_FEATURES_AVAILABLE)
        self.menu_mgr.setup()

        # 设置导航快捷键
        if SMART_FEATURES_AVAILABLE:
            # 延迟初始化导航器 (等待log_text创建)
            if self.navigator is None:
                self.app.root.after(500, self._init_smart_features)

            # 延迟设置快捷键
            self.app.root.after(600, self._setup_shortcuts)

    def _setup_shortcuts(self):
        """设置导航快捷键"""
        if self.navigator:
            self.shortcuts_mgr = NavigationShortcuts(self.app, self.navigator)
            self.shortcuts_mgr.setup()

    # ========== AI窗口管理 ==========

    def open_ai_assistant_window(self):
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

    # ========== 日志上下文获取 ==========

    def get_selected_log_context(self) -> Tuple[Any, List, List]:
        """获取选中日志及其上下文"""
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

    # ========== AI分析功能 ==========

    def ai_analyze_selected_log(self, log_text: Optional[str] = None):
        """AI分析选中的日志"""
        if not self.ai_assistant:
            self.open_ai_assistant_window()
            self.app.root.after(200, lambda: self._do_ai_analyze(log_text))
            return

        self._do_ai_analyze(log_text)

    def _do_ai_analyze(self, log_text: Optional[str] = None):
        """执行AI分析（内部方法 - 智能版）"""
        if not self.ai_assistant:
            messagebox.showwarning("警告", "AI助手初始化失败")
            return

        if log_text is not None:
            # 直接分析提供的文本
            question = f"分析以下日志的问题和原因：\n\n{log_text[:500]}"

            # 检查缓存
            if self.analysis_cache:
                cached_result = self.analysis_cache.get(question)
                if cached_result:
                    print("✓ AI分析缓存命中!")

            self.ai_assistant.chat_panel.question_var.set(question)
            self.ai_assistant.ask_question()
            return

        # 使用智能上下文提取
        if SMART_FEATURES_AVAILABLE and self.context_extractor is None:
            # 延迟初始化上下文提取器
            all_entries = getattr(self.app, 'log_entries', [])
            indexer = getattr(self.app, 'filter_manager', None)
            if indexer:
                indexer = getattr(indexer, 'indexer', None)

            self.context_extractor = SmartContextExtractor(all_entries, indexer)

        # 获取选中日志
        target, context_before, context_after = self.get_selected_log_context()

        if not target:
            messagebox.showinfo("提示", "请选择要分析的日志")
            return

        # 构建问题
        question = self._build_analysis_question(target, context_before, context_after)

        # 检查缓存
        if self.analysis_cache:
            cached_result = self.analysis_cache.get(question)
            if cached_result:
                print("✓ AI分析缓存命中!")

        self.ai_assistant.chat_panel.question_var.set(question)
        self.ai_assistant.ask_question()

    def _build_analysis_question(self, target, context_before, context_after) -> str:
        """构建分析问题（使用智能上下文或传统方式）"""
        # 使用智能上下文提取
        if self.context_extractor:
            try:
                smart_context = self.context_extractor.extract_context(target, max_tokens=8000)

                question = f"""【问题类型】: {smart_context['problem_type'].value}
【目标日志】: {self._get_entry_content(target)}

{smart_context['summary']}
"""

                # 添加上下文
                if smart_context['context_before']:
                    question += "\n【前置上下文】:\n"
                    for entry in smart_context['context_before'][-5:]:
                        question += f"[{getattr(entry, 'level', 'INFO')}] {self._get_entry_content(entry)[:150]}\n"

                if smart_context['context_after']:
                    question += "\n【后置上下文】:\n"
                    for entry in smart_context['context_after'][:3]:
                        question += f"[{getattr(entry, 'level', 'INFO')}] {self._get_entry_content(entry)[:150]}\n"

                # 添加索引关联的日志
                if smart_context.get('related_logs'):
                    question += f"\n【索引关联 - {len(smart_context['related_logs'])}条相关日志】:\n"
                    for entry in smart_context['related_logs'][:5]:
                        question += f"  • {self._get_entry_content(entry)[:100]}\n"

                print(f"✓ 智能上下文提取完成: {smart_context['problem_type'].value}")
                return question

            except Exception as e:
                print(f"⚠️  智能上下文提取失败,使用传统方式: {e}")

        # 降级到传统方式
        return self._build_traditional_question(target, context_before, context_after)

    def _build_traditional_question(self, target, context_before, context_after) -> str:
        """传统方式构建问题"""
        if isinstance(target, str):
            return f"分析这条日志:\n{target}"

        context_info = ""
        if context_before:
            context_info += f"\n\n【上下文 - 前{len(context_before)}条日志】:\n"
            for entry in context_before[-5:]:
                context_info += f"[{entry.level}] {entry.content[:200]}\n"

        question = f"分析这条{target.level}日志:\n【目标日志】: {target.content}"
        if context_info:
            question += context_info

        return question

    def ai_explain_error(self, log_text: Optional[str] = None):
        """AI解释错误原因"""
        # 实现类似ai_analyze_selected_log，但侧重错误解释
        if not self.ai_assistant:
            self.open_ai_assistant_window()
            self.app.root.after(200, lambda: self._do_ai_explain(log_text))
            return

        self._do_ai_explain(log_text)

    def _do_ai_explain(self, log_text: Optional[str] = None):
        """执行AI错误解释"""
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

        question = f"解释这个错误的原因和如何修复:\n{self._get_entry_content(target)}"
        self.ai_assistant.chat_panel.question_var.set(question)
        self.ai_assistant.ask_question()

    def ai_find_related_logs(self):
        """AI查找相关日志"""
        if not self.ai_assistant:
            self.open_ai_assistant_window()
            self.app.root.after(200, self._do_ai_find_related)
            return

        self._do_ai_find_related()

    def _do_ai_find_related(self):
        """执行AI查找相关日志"""
        if not self.ai_assistant:
            messagebox.showwarning("警告", "AI助手初始化失败")
            return

        target, _, _ = self.get_selected_log_context()

        if not target:
            messagebox.showinfo("提示", "请选择参考日志")
            return

        question = f"在日志中查找与此相关的其他日志:\n{self._get_entry_content(target)}"
        self.ai_assistant.chat_panel.question_var.set(question)
        self.ai_assistant.ask_question()

    # ========== 可视化功能 ==========

    def show_problem_graph(self):
        """显示问题链路图"""
        if not SMART_FEATURES_AVAILABLE:
            messagebox.showinfo("提示", "智能功能未启用")
            return

        if not self.navigator:
            messagebox.showinfo("提示", "导航器未初始化")
            return

        if not self.navigator.problem_graph:
            messagebox.showinfo("提示", "暂无问题节点\n\nAI分析日志后会自动创建问题链路")
            return

        try:
            from .ai_diagnosis.problem_graph_viewer import ProblemGraphViewer
            viewer = ProblemGraphViewer(self.app.root, self.navigator)

        except Exception as e:
            messagebox.showerror("错误", f"无法打开问题链路图: {str(e)}")
            import traceback
            traceback.print_exc()

    def show_cache_dashboard(self):
        """显示缓存统计仪表板"""
        if not SMART_FEATURES_AVAILABLE:
            messagebox.showinfo("提示", "智能功能未启用")
            return

        if not self.analysis_cache:
            messagebox.showinfo("提示", "缓存未初始化")
            return

        try:
            from .ai_diagnosis.cache_dashboard import CacheDashboard
            dashboard = CacheDashboard(self.app.root, self.analysis_cache)

        except Exception as e:
            messagebox.showerror("错误", f"无法打开缓存统计: {str(e)}")
            import traceback
            traceback.print_exc()

    # ========== 辅助方法 ==========

    def _get_entry_content(self, entry) -> str:
        """获取日志条目内容"""
        if isinstance(entry, str):
            return entry
        return getattr(entry, 'content', str(entry))
