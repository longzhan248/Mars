#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mars日志分析器专业版 - 模块化重构版本
保持原有功能完全一致，但代码组织更加模块化
"""

import os
import sys
import re
import threading
import queue
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
from collections import Counter, defaultdict

# 添加模块路径
current_dir = os.path.dirname(os.path.abspath(__file__))
modules_path = os.path.join(current_dir, 'modules')
components_path = os.path.join(current_dir, 'components')
parent_dir = os.path.dirname(current_dir)
decoders_path = os.path.join(parent_dir, 'decoders')
tools_path = os.path.join(parent_dir, 'tools')
push_tools_path = os.path.join(parent_dir, 'push_tools')

for path in [modules_path, components_path, decoders_path, tools_path, push_tools_path]:
    if path not in sys.path:
        sys.path.insert(0, path)

# 导入模块化组件
try:
    # 尝试相对导入（从gui目录运行时）
    from modules.data_models import LogEntry, FileGroup
    from modules.file_operations import FileOperations
    from modules.filter_search import FilterSearchManager
    from modules.ips_tab import IPSAnalysisTab
    from modules.push_tab import PushTestTab
    from modules.sandbox_tab import SandboxBrowserTab
    # 阶段二优化模块
    from modules.log_indexer import LogIndexer, IndexedFilterSearchManager
    from modules.stream_loader import StreamLoader, EnhancedFileOperations
except ImportError:
    # 绝对导入（从项目根目录运行时）
    from gui.modules.data_models import LogEntry, FileGroup
    from gui.modules.file_operations import FileOperations
    from gui.modules.filter_search import FilterSearchManager
    from gui.modules.ips_tab import IPSAnalysisTab
    from gui.modules.push_tab import PushTestTab
    from gui.modules.sandbox_tab import SandboxBrowserTab
    # 阶段二优化模块
    from gui.modules.log_indexer import LogIndexer, IndexedFilterSearchManager
    from gui.modules.stream_loader import StreamLoader, EnhancedFileOperations

# 导入原有组件
try:
    from components.improved_lazy_text import ImprovedLazyText
except ImportError:
    try:
        from improved_lazy_text import ImprovedLazyText
    except ImportError:
        from scrolled_text_with_lazy_load import ScrolledTextWithLazyLoad as ImprovedLazyText

# 导入原mars_log_analyzer_pro.py中的MarsLogAnalyzerPro类
# 使用原始文件作为基类，保证功能完全一致
try:
    from mars_log_analyzer_pro import MarsLogAnalyzerPro as OriginalMarsLogAnalyzerPro
except ImportError:
    from gui.mars_log_analyzer_pro import MarsLogAnalyzerPro as OriginalMarsLogAnalyzerPro


class MarsLogAnalyzerPro(OriginalMarsLogAnalyzerPro):
    """
    Mars日志分析器专业版 - 模块化版本
    继承原有类，逐步重构为使用模块化组件
    """

    def __init__(self, root):
        """初始化应用程序"""
        # 初始化模块化组件
        self.file_ops = FileOperations()

        # 阶段二优化：使用索引过滤管理器替代原有过滤管理器
        self.filter_manager = IndexedFilterSearchManager()

        # 阶段二优化：添加流式加载器
        self.stream_loader = StreamLoader()
        self.enhanced_file_ops = EnhancedFileOperations()

        # 索引器状态
        self.indexer_ready = False
        self.index_building = False

        # AI助手面板（延迟初始化）
        self.ai_assistant = None

        # 调用父类初始化
        super().__init__(root)

    def create_widgets(self):
        """重写create_widgets以添加AI助手按钮"""
        # 调用父类方法创建基础UI
        super().create_widgets()

        # 添加AI助手按钮到工具栏
        self.add_ai_assistant_button()

    # 重写使用模块化组件的方法
    def parse_time_string(self, time_str):
        """使用模块化的时间解析"""
        return self.filter_manager.parse_time_string(time_str)

    def compare_log_time(self, log_timestamp, start_time, end_time):
        """使用模块化的时间比较"""
        return self.filter_manager.compare_log_time(log_timestamp, start_time, end_time)

    def build_index_async(self):
        """异步构建索引（阶段二优化）"""
        if not self.log_entries or self.index_building:
            return

        self.index_building = True
        self.indexer_ready = False

        def progress_callback(current, total):
            """索引构建进度回调"""
            if hasattr(self, 'file_stats_var'):
                progress = int((current / total) * 100)
                self.file_stats_var.set(f"正在构建索引: {progress}% ({current}/{total})")

        def complete_callback():
            """索引构建完成回调"""
            self.index_building = False
            self.indexer_ready = True
            if hasattr(self, 'file_stats_var'):
                stats = self.filter_manager.indexer.get_statistics()
                self.file_stats_var.set(
                    f"索引构建完成: {stats['total_entries']}条 | "
                    f"词:{stats['unique_words']} | "
                    f"模块:{stats['modules']} | "
                    f"级别:{stats['levels']}"
                )
            # 索引构建完成后自动应用当前过滤条件
            self.root.after(100, self.apply_global_filter)

        # 异步构建索引
        self.filter_manager.build_index(
            self.log_entries,
            progress_callback=progress_callback,
            complete_callback=complete_callback
        )

    def apply_global_filter(self):
        """使用模块化的过滤功能（阶段二优化：使用索引）"""
        if not self.log_entries:
            return

        # 获取所有过滤条件
        keyword = self.search_var.get()
        search_mode = self.search_mode_var.get()
        level_filter = self.level_var.get()
        module_filter = self.module_var.get()
        start_time = self.global_time_start_var.get()
        end_time = self.global_time_end_var.get()

        # 阶段二优化：使用索引过滤器（如果索引已准备好）
        if self.indexer_ready and self.filter_manager.indexer.is_ready:
            filtered = self.filter_manager.filter_entries_with_index(
                self.log_entries,
                level=level_filter,
                module=module_filter,
                keyword=keyword,
                start_time=start_time,
                end_time=end_time,
                search_mode=search_mode
            )
        else:
            # 降级到原有过滤方式
            from modules.filter_search import FilterSearchManager
            fallback_manager = FilterSearchManager()
            filtered = fallback_manager.filter_entries(
                self.log_entries,
                level=level_filter,
                module=module_filter,
                keyword=keyword,
                start_time=start_time,
                end_time=end_time,
                search_mode=search_mode
            )

        self.filtered_entries = filtered
        self.display_logs(filtered)

        # 更新统计信息
        filter_info = []
        if keyword:
            filter_info.append(f"关键词:{keyword}")
        if level_filter and level_filter != '全部':
            filter_info.append(f"级别:{level_filter}")
        if module_filter and module_filter != '全部':
            filter_info.append(f"模块:{module_filter}")
        if start_time:
            filter_info.append(f"开始:{start_time}")
        if end_time:
            filter_info.append(f"结束:{end_time}")

        # 添加索引状态提示
        index_status = "⚡索引" if self.indexer_ready else "普通"

        if filter_info:
            stats_text = f"{index_status} | 过滤结果: {len(filtered)}/{len(self.log_entries)} | " + " | ".join(filter_info)
        else:
            stats_text = f"{index_status} | 显示: {len(filtered)}/{len(self.log_entries)} 条日志"

        # 更新文件统计标签
        if hasattr(self, 'file_stats_var'):
            self.file_stats_var.set(stats_text)

    def create_ips_analysis_tab(self):
        """创建IPS解析标签页 - 使用模块化组件"""
        ips_frame = ttk.Frame(self.main_notebook, padding="10")
        self.main_notebook.add(ips_frame, text="IPS崩溃解析")

        # 使用模块化的IPS标签页
        self.ips_tab = IPSAnalysisTab(ips_frame, self)

    def create_push_test_tab(self):
        """创建iOS推送测试标签页 - 使用模块化组件"""
        push_frame = ttk.Frame(self.main_notebook, padding="10")
        self.main_notebook.add(push_frame, text="iOS推送测试")

        # 使用模块化的推送标签页
        self.push_tab = PushTestTab(push_frame, self)

    def create_sandbox_browser_tab(self):
        """创建iOS沙盒浏览标签页 - 使用模块化组件"""
        sandbox_frame = ttk.Frame(self.main_notebook, padding="10")
        self.main_notebook.add(sandbox_frame, text="iOS沙盒浏览")

        # 使用模块化的沙盒浏览标签页
        self.sandbox_tab = SandboxBrowserTab(sandbox_frame, self)

    def create_dsym_analysis_tab(self):
        """创建dSYM文件分析标签页"""
        from modules.dsym_tab import DSYMTab

        dsym_frame = ttk.Frame(self.main_notebook, padding="10")
        self.main_notebook.add(dsym_frame, text="dSYM分析")

        # 使用模块化的dSYM标签页
        self.dsym_tab = DSYMTab(dsym_frame)
        self.dsym_tab.frame.pack(fill=tk.BOTH, expand=True)

    def create_linkmap_analysis_tab(self):
        """创建LinkMap文件分析标签页"""
        from modules.linkmap_tab import LinkMapTab

        linkmap_frame = ttk.Frame(self.main_notebook, padding="10")
        self.main_notebook.add(linkmap_frame, text="LinkMap分析")

        # 使用模块化的LinkMap标签页
        self.linkmap_tab = LinkMapTab(linkmap_frame)
        self.linkmap_tab.frame.pack(fill=tk.BOTH, expand=True)

    def create_obfuscation_tab(self):
        """创建iOS代码混淆标签页"""
        from modules.obfuscation_tab import ObfuscationTab

        obfuscation_frame = ttk.Frame(self.main_notebook, padding="10")
        self.main_notebook.add(obfuscation_frame, text="iOS混淆")

        # 使用模块化的混淆标签页
        self.obfuscation_tab = ObfuscationTab(obfuscation_frame, self)
        self.obfuscation_tab.pack(fill=tk.BOTH, expand=True)

    def load_group_logs(self, group):
        """加载文件组的日志 - 阶段二优化：自动构建索引"""
        # 调用父类方法完成基本加载
        super().load_group_logs(group)

        # 阶段二优化：异步构建索引
        if self.log_entries:
            self.root.after(500, self.build_index_async)

    def filter_logs(self, start_time=None, end_time=None):
        """重写filter_logs方法以使用模块化的过滤逻辑

        保持与原始版本相同的接口，但使用apply_global_filter的统一逻辑
        """
        # 如果提供了时间参数，更新全局时间过滤器
        if start_time is not None:
            self.global_time_start_var.set(start_time if start_time else '')
        if end_time is not None:
            self.global_time_end_var.set(end_time if end_time else '')

        # 使用apply_global_filter的统一逻辑
        self.apply_global_filter()

    def export_current_view(self):
        """导出当前视图的日志 - 使用模块化导出"""
        if not self.filtered_entries:
            messagebox.showwarning("警告", "没有可导出的数据")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".log",
            filetypes=[
                ("日志文件", "*.log"),
                ("文本文件", "*.txt"),
                ("JSON文件", "*.json"),
                ("CSV文件", "*.csv"),
                ("所有文件", "*.*")
            ]
        )

        if not filename:
            return

        try:
            # 确定导出格式
            format = 'txt'
            if filename.endswith('.json'):
                format = 'json'
            elif filename.endswith('.csv'):
                format = 'csv'

            # 使用模块化的导出功能
            if self.file_ops.export_to_file(self.filtered_entries, filename, format):
                messagebox.showinfo("成功", f"已导出 {len(self.filtered_entries)} 条日志到:\n{filename}")
            else:
                messagebox.showerror("错误", "导出失败")

        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {str(e)}")

    def add_ai_assistant_button(self):
        """在工具栏添加AI助手按钮"""
        try:
            # 等待一会儿让父类完成UI创建
            def add_button_delayed():
                try:
                    # 查找search_frame（搜索与过滤的LabelFrame）
                    if hasattr(self, 'log_frame'):
                        for widget in self.log_frame.winfo_children():
                            # 找到第一层Frame
                            if isinstance(widget, ttk.Frame):
                                for child in widget.winfo_children():
                                    # 找到LabelFrame，text="搜索与过滤"
                                    if isinstance(child, ttk.LabelFrame):
                                        try:
                                            if child.cget('text') == '搜索与过滤':
                                                # 找到了search_frame，添加AI助手按钮
                                                ai_button = ttk.Button(
                                                    child,
                                                    text="🤖 AI助手",
                                                    command=self.open_ai_assistant_window
                                                )
                                                # 放在第2行第9列（"导出报告"后面）
                                                ai_button.grid(row=1, column=9, padx=2, pady=3)
                                                print("✅ AI助手按钮已添加")
                                                return
                                        except tk.TclError:
                                            continue

                    print("❌ 未找到搜索过滤区域")

                except Exception as e:
                    print(f"❌ 添加按钮失败: {str(e)}")
                    import traceback
                    traceback.print_exc()

            # 延迟100ms执行，确保父类UI已完成创建
            self.root.after(100, add_button_delayed)

            # 添加右键菜单到日志文本组件
            self.setup_context_menu()

        except Exception as e:
            print(f"❌ AI助手按钮初始化失败: {str(e)}")
            import traceback
            traceback.print_exc()

    def open_ai_assistant_window(self):
        """打开AI助手窗口"""
        try:
            # 如果窗口已存在，直接显示
            if hasattr(self, 'ai_window') and self.ai_window.winfo_exists():
                self.ai_window.deiconify()
                self.ai_window.lift()
                return

            # 导入AI助手面板
            try:
                from modules.ai_assistant_panel import AIAssistantPanel
            except ImportError:
                from gui.modules.ai_assistant_panel import AIAssistantPanel

            # 创建新窗口
            self.ai_window = tk.Toplevel(self.root)
            self.ai_window.title("AI智能诊断助手")
            self.ai_window.geometry("500x700")

            # 设置窗口图标（如果有的话）
            try:
                self.ai_window.iconbitmap(self.root.iconbitmap())
            except:
                pass

            # 创建AI助手面板
            self.ai_assistant = AIAssistantPanel(self.ai_window, self)
            # AIAssistantPanel已经在内部pack了self.frame，不需要再次pack

            # 窗口关闭时隐藏而不是销毁
            self.ai_window.protocol("WM_DELETE_WINDOW", self.ai_window.withdraw)

        except Exception as e:
            messagebox.showerror("错误", f"无法打开AI助手窗口:\n{str(e)}")
            import traceback
            traceback.print_exc()

    def setup_context_menu(self):
        """设置日志查看器的右键菜单"""
        try:
            # 创建右键菜单
            self.log_context_menu = tk.Menu(self.log_text, tearoff=0)

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
            self.log_text.bind("<Button-3>", self.show_context_menu)
            # macOS可能使用Button-2或Control-Button-1
            self.log_text.bind("<Button-2>", self.show_context_menu)
            self.log_text.bind("<Control-Button-1>", self.show_context_menu)

        except Exception as e:
            print(f"右键菜单设置失败: {str(e)}")

    def show_context_menu(self, event):
        """显示右键菜单"""
        try:
            # 设置菜单显示位置
            self.log_context_menu.post(event.x_root, event.y_root)
        except Exception as e:
            print(f"显示右键菜单失败: {str(e)}")

    def get_selected_log_context(self):
        """获取选中日志及其上下文"""
        try:
            # 获取选中的文本
            if self.log_text.tag_ranges("sel"):
                selected_text = self.log_text.get("sel.first", "sel.last")
            else:
                # 如果没有选中，获取当前行
                current_line = self.log_text.index("insert").split('.')[0]
                selected_text = self.log_text.get(f"{current_line}.0", f"{current_line}.end")

            if not selected_text.strip():
                return None, None, None

            # 尝试从filtered_entries中查找匹配的日志
            matched_entries = []
            for entry in self.filtered_entries if hasattr(self, 'filtered_entries') else self.log_entries:
                if selected_text.strip() in entry.content or selected_text.strip() in entry.raw_line:
                    matched_entries.append(entry)

            if not matched_entries:
                return selected_text, [], []

            # 获取第一个匹配的日志
            target_entry = matched_entries[0]

            # 从所有日志中找到这条日志的位置
            all_entries = self.log_entries
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

    def ai_analyze_selected_log(self, log_text=None):
        """AI分析选中的日志

        Args:
            log_text: 可选的日志文本。如果提供，直接分析该文本；否则获取选中的日志
        """
        # 如果AI助手未初始化，自动打开窗口并初始化
        if not self.ai_assistant:
            self.open_ai_assistant_window()
            # 给窗口一点时间完成初始化，然后执行分析
            self.root.after(200, lambda: self._do_ai_analyze(log_text))
            return

        self._do_ai_analyze(log_text)

    def _do_ai_analyze(self, log_text=None):
        """执行AI分析（内部方法）"""
        if not self.ai_assistant:
            messagebox.showwarning("警告", "AI助手初始化失败，请手动点击'🤖 AI助手'按钮")
            return

        # 如果提供了log_text参数，使用父类的逻辑
        if log_text is not None:
            # 直接分析提供的文本
            question = f"分析以下日志的问题和原因：\n\n{log_text[:500]}"
            self.ai_assistant.question_var.set(question)
            self.ai_assistant.ask_question()
            return

        # 否则使用原有的上下文获取逻辑
        target, context_before, context_after = self.get_selected_log_context()

        if not target:
            messagebox.showinfo("提示", "请选择要分析的日志")
            return

        # 获取上下文参数配置
        params = self.ai_assistant.get_context_params()
        context_limit = params.get('crash_before', 5)  # 使用crash_before参数作为上下文大小

        # 构建分析问题（包含上下文）
        if isinstance(target, str):
            question = f"分析这条日志:\n{target}"
        else:
            # 包含上下文信息
            context_info = ""
            if context_before:
                context_info += f"\n\n【上下文 - 前{min(len(context_before), context_limit)}条日志】:\n"
                for entry in context_before[-context_limit:]:
                    context_info += f"[{entry.level}] {entry.content[:200]}\n"

            question = f"分析这条{target.level}日志:\n【目标日志】: {target.content}"

            if context_info:
                question += context_info

        # 设置AI助手的输入框并触发提问
        self.ai_assistant.question_var.set(question)
        self.ai_assistant.ask_question()

    def ai_explain_error(self, log_text=None):
        """AI解释错误原因

        Args:
            log_text: 可选的日志文本。如果提供，直接解释该文本；否则获取选中的日志
        """
        # 如果AI助手未初始化，自动打开窗口并初始化
        if not self.ai_assistant:
            self.open_ai_assistant_window()
            # 给窗口一点时间完成初始化，然后执行解释
            self.root.after(200, lambda: self._do_ai_explain(log_text))
            return

        self._do_ai_explain(log_text)

    def _do_ai_explain(self, log_text=None):
        """执行AI错误解释（内部方法）"""
        if not self.ai_assistant:
            messagebox.showwarning("警告", "AI助手初始化失败，请手动点击'🤖 AI助手'按钮")
            return

        # 如果提供了log_text参数，使用简化逻辑
        if log_text is not None:
            question = f"解释以下错误的原因、影响和解决方案：\n\n{log_text[:500]}"
            self.ai_assistant.question_var.set(question)
            self.ai_assistant.ask_question()
            return

        # 否则使用原有的上下文获取逻辑
        target, context_before, context_after = self.get_selected_log_context()

        if not target:
            messagebox.showinfo("提示", "请选择要解释的错误")
            return

        # 获取上下文参数配置
        params = self.ai_assistant.get_context_params()
        context_before_limit = params.get('crash_before', 5)
        context_after_limit = params.get('crash_after', 3)

        # 构建问题（包含上下文）
        if isinstance(target, str):
            question = f"解释这个错误的原因和如何修复:\n{target}"
        else:
            # 包含前后上下文
            context_info = ""
            if context_before:
                context_info += f"\n\n【上下文 - 前{min(len(context_before), context_before_limit)}条日志】:\n"
                for entry in context_before[-context_before_limit:]:
                    context_info += f"[{entry.level}] {entry.content[:200]}\n"

            if context_after:
                context_info += f"\n\n【上下文 - 后{min(len(context_after), context_after_limit)}条日志】:\n"
                for entry in context_after[:context_after_limit]:
                    context_info += f"[{entry.level}] {entry.content[:200]}\n"

            question = f"解释这个{target.level}的原因和如何修复:\n【目标日志】: {target.content}"

            if context_info:
                question += context_info

        self.ai_assistant.question_var.set(question)
        self.ai_assistant.ask_question()

    def ai_find_related_logs(self):
        """AI查找相关日志"""
        # 如果AI助手未初始化，自动打开窗口并初始化
        if not self.ai_assistant:
            self.open_ai_assistant_window()
            # 给窗口一点时间完成初始化，然后执行查找
            self.root.after(200, self._do_ai_find_related)
            return

        self._do_ai_find_related()

    def _do_ai_find_related(self):
        """执行AI查找相关日志（内部方法）"""
        if not self.ai_assistant:
            messagebox.showwarning("警告", "AI助手初始化失败，请手动点击'🤖 AI助手'按钮")
            return

        target, context_before, context_after = self.get_selected_log_context()

        if not target:
            messagebox.showinfo("提示", "请选择参考日志")
            return

        # 获取上下文参数配置
        params = self.ai_assistant.get_context_params()
        search_logs_limit = params.get('search_logs', 500)  # 用于搜索的日志数量

        # 构建问题（包含周围日志样本）
        if isinstance(target, str):
            question = f"在日志中查找与此相关的其他日志:\n{target}"
        else:
            # 提供周围日志作为搜索范围参考
            context_info = ""

            # 获取目标日志在全部日志中的位置
            try:
                all_entries = self.log_entries if hasattr(self, 'log_entries') else []
                target_idx = all_entries.index(target)

                # 获取目标日志前后各一半的日志作为搜索范围
                half_limit = search_logs_limit // 2
                start_idx = max(0, target_idx - half_limit)
                end_idx = min(len(all_entries), target_idx + half_limit)

                sample_logs = all_entries[start_idx:end_idx]

                if sample_logs:
                    context_info += f"\n\n【搜索范围 - 共{len(sample_logs)}条日志】:\n"
                    # 显示前10条和后10条作为样本
                    for i, entry in enumerate(sample_logs[:10]):
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

        self.ai_assistant.question_var.set(question)
        self.ai_assistant.ask_question()

    def copy_selected_text(self):
        """复制选中的文本"""
        try:
            if self.log_text.tag_ranges("sel"):
                selected_text = self.log_text.get("sel.first", "sel.last")
                self.root.clipboard_clear()
                self.root.clipboard_append(selected_text)
        except Exception as e:
            print(f"复制文本失败: {str(e)}")

    def search_selected_text(self):
        """搜索选中的文本"""
        try:
            if self.log_text.tag_ranges("sel"):
                selected_text = self.log_text.get("sel.first", "sel.last").strip()
                if selected_text:
                    self.search_var.set(selected_text)
                    self.search_logs()
        except Exception as e:
            print(f"搜索文本失败: {str(e)}")


def main():
    """主程序入口"""
    root = tk.Tk()
    app = MarsLogAnalyzerPro(root)
    root.mainloop()


if __name__ == "__main__":
    main()