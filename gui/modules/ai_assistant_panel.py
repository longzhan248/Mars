#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI助手侧边栏面板
为Mars日志分析器提供AI辅助分析功能
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
from typing import Callable, Optional, List
from datetime import datetime


def safe_import_ai_diagnosis():
    """安全导入AI诊断模块"""
    try:
        from ai_diagnosis import AIClientFactory, AIConfig
        from ai_diagnosis.log_preprocessor import LogPreprocessor
        from ai_diagnosis.prompt_templates import PromptTemplates
        return AIClientFactory, AIConfig, LogPreprocessor, PromptTemplates
    except ImportError:
        try:
            from modules.ai_diagnosis import AIClientFactory, AIConfig
            from modules.ai_diagnosis.log_preprocessor import LogPreprocessor
            from modules.ai_diagnosis.prompt_templates import PromptTemplates
            return AIClientFactory, AIConfig, LogPreprocessor, PromptTemplates
        except ImportError:
            from gui.modules.ai_diagnosis import AIClientFactory, AIConfig
            from gui.modules.ai_diagnosis.log_preprocessor import LogPreprocessor
            from gui.modules.ai_diagnosis.prompt_templates import PromptTemplates
            return AIClientFactory, AIConfig, LogPreprocessor, PromptTemplates


class AIAssistantPanel:
    """AI助手侧边栏面板"""

    def __init__(self, parent, main_app):
        """
        初始化AI助手面板

        Args:
            parent: 父容器
            main_app: 主应用程序实例
        """
        self.parent = parent
        self.main_app = main_app

        # 对话历史
        self.chat_history = []

        # 是否正在处理AI请求
        self.is_processing = False

        # 停止标志
        self.stop_flag = False

        # Token累计统计
        self.total_input_tokens = 0
        self.total_output_tokens = 0

        # AI客户端（延迟初始化）
        self._ai_client = None

        # 评分记录（用于收集用户反馈）
        self.ratings = []

        # 创建UI
        self.create_widgets()

    @property
    def ai_client(self):
        """延迟初始化AI客户端"""
        if self._ai_client is None:
            try:
                AIClientFactory, AIConfig, _, _ = safe_import_ai_diagnosis()
                config = AIConfig.load()

                # 如果启用自动检测,使用auto_detect
                if config.get('auto_detect', True):
                    self._ai_client = AIClientFactory.auto_detect()
                else:
                    # 否则使用配置中的服务
                    self._ai_client = AIClientFactory.create(
                        service=config.get('ai_service', 'ClaudeCode'),
                        api_key=config.get('api_key'),
                        model=config.get('model')
                    )
            except Exception as e:
                messagebox.showerror(
                    "AI服务初始化失败",
                    f"无法初始化AI服务:\n{str(e)}\n\n"
                    f"请在设置中配置AI服务或确保Claude Code正在运行。"
                )
                return None
        return self._ai_client

    def get_project_context(self, max_chars: int = 8000) -> str:
        """
        读取项目代码作为上下文

        Args:
            max_chars: 最大字符数

        Returns:
            项目代码内容字符串
        """
        import os

        _, AIConfig, _, _ = safe_import_ai_diagnosis()
        config = AIConfig.load()
        project_dirs = config.get('project_dirs', [])

        if not project_dirs:
            return ""

        code_content = []
        char_count = 0

        # 支持的代码文件扩展名
        code_extensions = (
            # iOS/macOS
            '.h', '.m', '.mm', '.swift',
            # Android
            '.java', '.kt',
            # 通用
            '.py', '.js', '.ts', '.cpp', '.c',
            # 配置文件
            '.json', '.xml', '.plist', '.yml', '.yaml'
        )

        for project_dir in project_dirs:
            if not os.path.exists(project_dir):
                continue

            # 遍历项目目录
            for root, dirs, files in os.walk(project_dir):
                # 跳过一些常见的无关目录
                dirs[:] = [d for d in dirs if d not in [
                    '.git', 'node_modules', 'build', 'dist',
                    'Pods', 'DerivedData', '__pycache__', '.idea'
                ]]

                for file in files:
                    # 只读取代码文件
                    if file.endswith(code_extensions):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                # 添加文件头，包含相对路径
                                rel_path = os.path.relpath(file_path, project_dir)
                                code_section = f"\n## 文件: {rel_path}\n```\n{content}\n```\n"

                                if char_count + len(code_section) > max_chars:
                                    # 超过限制，截断
                                    remaining = max_chars - char_count
                                    code_content.append(code_section[:remaining])
                                    break

                                code_content.append(code_section)
                                char_count += len(code_section)
                        except Exception as e:
                            continue

                if char_count >= max_chars:
                    break

            if char_count >= max_chars:
                break

        if code_content:
            return "\n# 项目代码参考\n" + "".join(code_content)
        else:
            return ""

    def create_widgets(self):
        """创建UI组件"""
        # 主框架
        self.frame = ttk.Frame(self.parent)
        self.frame.pack(fill=tk.BOTH, expand=True)

        # 标题栏
        title_frame = ttk.Frame(self.frame)
        title_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(
            title_frame,
            text="🤖 AI助手",
            font=("Arial", 14, "bold")
        ).pack(side=tk.LEFT)

        # 设置按钮
        ttk.Button(
            title_frame,
            text="⚙️",
            width=3,
            command=self.show_settings
        ).pack(side=tk.RIGHT, padx=2)

        # 清空对话按钮
        ttk.Button(
            title_frame,
            text="🗑️",
            width=3,
            command=self.confirm_clear_chat
        ).pack(side=tk.RIGHT, padx=2)

        # 导出对话按钮
        ttk.Button(
            title_frame,
            text="💾",
            width=3,
            command=self.export_chat
        ).pack(side=tk.RIGHT, padx=2)

        # 快捷操作区域（合并快捷操作和常用问题，使用2列布局）
        quick_frame = ttk.LabelFrame(self.frame, text="快捷操作", padding="5")
        quick_frame.pack(fill=tk.X, pady=(0, 5))

        # 定义所有按钮（快捷操作 + 常用问题）
        all_actions = [
            # 第一行
            ("🔍 崩溃", self.analyze_crashes),
            ("📊 性能", self.analyze_performance),
            # 第二行
            ("📝 总结", self.summarize_issues),
            ("🔎 搜索", self.smart_search),
            # 第三行 - 常用问题
            ("💡 性能优化", lambda: self.ask_common_question("如何提升应用性能？有哪些优化建议？")),
            ("🐛 错误原因", lambda: self.ask_common_question("这些错误的常见原因有哪些？如何避免？")),
            # 第四行 - 常用问题
            ("📝 最佳实践", lambda: self.ask_common_question("日志记录的最佳实践是什么？")),
            ("🔧 调试技巧", lambda: self.ask_common_question("如何高效地调试这类问题？")),
        ]

        # 创建4x2网格布局（4行2列）
        for i, (label, command) in enumerate(all_actions):
            row = i // 2
            col = i % 2
            btn = ttk.Button(
                quick_frame,
                text=label,
                command=command
            )
            btn.grid(row=row, column=col, padx=2, pady=2, sticky="ew")

        # 配置列权重，使按钮均分空间
        quick_frame.columnconfigure(0, weight=1)
        quick_frame.columnconfigure(1, weight=1)

        # 对话历史区域
        chat_frame = ttk.LabelFrame(self.frame, text="对话历史", padding="5")
        chat_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        # 搜索框区域
        search_frame = ttk.Frame(chat_frame)
        search_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(search_frame, text="🔍").pack(side=tk.LEFT, padx=(0, 2))

        self.search_var = tk.StringVar()
        self.search_var.trace_add('write', lambda *args: self.search_chat())
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))

        # 清除搜索按钮
        ttk.Button(
            search_frame,
            text="×",
            width=3,
            command=self.clear_search
        ).pack(side=tk.LEFT, padx=(0, 2))

        # 搜索结果计数
        self.search_result_var = tk.StringVar(value="")
        ttk.Label(
            search_frame,
            textvariable=self.search_result_var,
            font=("Arial", 9),
            foreground="#666666"
        ).pack(side=tk.LEFT)

        # 对话显示区域（使用ScrolledText）
        self.chat_text = scrolledtext.ScrolledText(
            chat_frame,
            wrap=tk.WORD,
            width=50,
            height=20,
            state=tk.DISABLED,
            font=("Arial", 11)
        )
        self.chat_text.pack(fill=tk.BOTH, expand=True)

        # 配置文本标签
        self.chat_text.tag_config("user", foreground="#0066CC", font=("Arial", 11, "bold"))
        self.chat_text.tag_config("assistant", foreground="#2E7D32", font=("Arial", 11, "bold"))
        self.chat_text.tag_config("system", foreground="#FF6B35", font=("Arial", 11, "italic"))
        self.chat_text.tag_config("timestamp", foreground="#666666", font=("Arial", 9))
        self.chat_text.tag_config("content", foreground="#000000", font=("Arial", 11))
        self.chat_text.tag_config("search_highlight", background="#FFFF00")  # 黄色高亮

        # 问题输入区域
        input_frame = ttk.Frame(self.frame)
        input_frame.pack(fill=tk.X)

        ttk.Label(input_frame, text="问题:").pack(side=tk.LEFT, padx=(0, 5))

        self.question_var = tk.StringVar()
        question_entry = ttk.Entry(input_frame, textvariable=self.question_var)
        question_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        question_entry.bind('<Return>', lambda e: self.ask_question())

        ttk.Button(
            input_frame,
            text="发送",
            command=self.ask_question
        ).pack(side=tk.LEFT)

        # 状态栏和停止按钮
        status_frame = ttk.Frame(self.frame)
        status_frame.pack(fill=tk.X, pady=(5, 0))

        self.status_var = tk.StringVar(value="就绪")
        status_label = ttk.Label(
            status_frame,
            textvariable=self.status_var,
            font=("Arial", 9),
            foreground="#666666"
        )
        status_label.pack(side=tk.LEFT, expand=True)

        # 停止按钮（初始隐藏）
        self.stop_button = ttk.Button(
            status_frame,
            text="⏹️ 停止",
            width=8,
            command=self.stop_processing
        )
        # 初始不显示

        # 进度条（初始隐藏）
        self.progress = ttk.Progressbar(
            self.frame,
            mode='indeterminate',
            length=200
        )
        # 初始不显示

    def append_chat(self, role: str, message: str):
        """
        添加对话到历史

        Args:
            role: 角色（"user", "assistant", "system"）
            message: 消息内容
        """
        timestamp = datetime.now().strftime("%H:%M:%S")

        self.chat_history.append({
            'role': role,
            'message': message,
            'timestamp': timestamp
        })

        # 更新UI
        self.chat_text.config(state=tk.NORMAL)

        # 添加时间戳
        self.chat_text.insert(tk.END, f"[{timestamp}] ", "timestamp")

        # 添加角色标签
        role_labels = {
            "user": "用户",
            "assistant": "AI助手",
            "system": "系统"
        }
        label = role_labels.get(role, role)
        self.chat_text.insert(tk.END, f"{label}: ", role)

        # 添加消息内容
        self.chat_text.insert(tk.END, f"{message}\n\n", "content")

        self.chat_text.config(state=tk.DISABLED)
        self.chat_text.see(tk.END)  # 滚动到底部

    def clear_chat(self):
        """清空对话历史"""
        self.chat_history = []
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.delete('1.0', tk.END)
        self.chat_text.config(state=tk.DISABLED)

        # 重置Token统计
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def confirm_clear_chat(self):
        """确认并清空对话历史"""
        if not self.chat_history:
            messagebox.showinfo("提示", "对话历史已经是空的")
            return

        # 弹出确认对话框
        result = messagebox.askyesno(
            "确认清空",
            "确定要清空所有对话历史吗？\n此操作不可恢复。"
        )

        if result:
            self.clear_chat()
            self.append_chat("system", "对话历史已清空")

    def export_chat(self):
        """导出对话历史"""
        if not self.chat_history:
            messagebox.showinfo("提示", "对话历史为空，无需导出")
            return

        from tkinter import filedialog

        # 弹出文件保存对话框
        filename = filedialog.asksaveasfilename(
            title="导出对话历史",
            defaultextension=".md",
            filetypes=[
                ("Markdown文件", "*.md"),
                ("文本文件", "*.txt"),
                ("所有文件", "*.*")
            ]
        )

        if not filename:
            return

        try:
            # 判断文件格式
            is_markdown = filename.endswith('.md')

            if is_markdown:
                content = self._export_as_markdown()
            else:
                content = self._export_as_text()

            # 写入文件
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)

            messagebox.showinfo("成功", f"对话历史已导出到:\n{filename}")

        except Exception as e:
            messagebox.showerror("导出失败", f"无法导出对话历史:\n{str(e)}")

    def _export_as_markdown(self) -> str:
        """导出为Markdown格式"""
        lines = []
        lines.append("# AI助手对话历史\n")
        lines.append(f"## 导出时间\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        lines.append("## 对话记录\n")

        role_names = {
            "user": "用户",
            "assistant": "AI助手",
            "system": "系统"
        }

        for chat in self.chat_history:
            role = role_names.get(chat['role'], chat['role'])
            lines.append(f"### [{chat['timestamp']}] {role}\n")
            lines.append(f"{chat['message']}\n")

        return '\n'.join(lines)

    def _export_as_text(self) -> str:
        """导出为纯文本格式"""
        lines = []
        lines.append("AI助手对话历史")
        lines.append(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 50)
        lines.append("")

        role_names = {
            "user": "用户",
            "assistant": "AI助手",
            "system": "系统"
        }

        for chat in self.chat_history:
            role = role_names.get(chat['role'], chat['role'])
            lines.append(f"[{chat['timestamp']}] {role}: {chat['message']}")
            lines.append("")

        return '\n'.join(lines)

    def set_status(self, message: str):
        """设置状态文本"""
        self.status_var.set(message)

    def show_stop_button(self):
        """显示停止按钮"""
        self.stop_button.pack(side=tk.RIGHT, padx=5)

    def hide_stop_button(self):
        """隐藏停止按钮"""
        self.stop_button.pack_forget()

    def show_progress(self):
        """显示进度条并开始滚动动画"""
        self.progress.pack(fill=tk.X, pady=(2, 0))
        self.progress.start(10)  # 10ms间隔的滚动动画

    def hide_progress(self):
        """隐藏进度条并停止动画"""
        self.progress.stop()
        self.progress.pack_forget()

    def stop_processing(self):
        """停止AI处理"""
        self.stop_flag = True
        self.set_status("正在取消...")
        self.append_chat("system", "用户已取消操作")

    def get_context_params(self):
        """
        获取当前上下文参数配置

        Returns:
            根据context_size返回对应的参数字典
        """
        # 上下文参数映射
        CONTEXT_PARAMS = {
            '简化': {
                'crash_before': 10, 'crash_after': 5,
                'perf_logs': 50,
                'error_patterns': 5,
                'search_logs': 500, 'search_tokens': 4000
            },
            '标准': {
                'crash_before': 20, 'crash_after': 10,
                'perf_logs': 100,
                'error_patterns': 10,
                'search_logs': 1000, 'search_tokens': 8000
            },
            '详细': {
                'crash_before': 40, 'crash_after': 20,
                'perf_logs': 200,
                'error_patterns': 20,
                'search_logs': 2000, 'search_tokens': 16000
            }
        }

        _, AIConfig, _, _ = safe_import_ai_diagnosis()
        config = AIConfig.load()
        context_size = config.get('context_size', '标准')
        return CONTEXT_PARAMS.get(context_size, CONTEXT_PARAMS['标准'])

    def analyze_crashes(self):
        """分析崩溃日志"""
        if not self.main_app.log_entries:
            messagebox.showwarning("警告", "请先加载日志文件")
            return

        if self.is_processing:
            messagebox.showinfo("提示", "AI正在处理中，请稍候")
            return

        self.is_processing = True
        self.stop_flag = False  # 重置停止标志
        self.set_status("正在分析崩溃日志...")
        self.append_chat("user", "分析崩溃日志")
        self.main_app.root.after(0, self.show_stop_button)  # 显示停止按钮
        self.main_app.root.after(0, self.show_progress)  # 显示进度条

        def _analyze():
            try:
                # 检查停止标志
                if self.stop_flag:
                    return
                # 导入模块
                _, _, LogPreprocessor, PromptTemplates = safe_import_ai_diagnosis()

                # 获取上下文参数
                params = self.get_context_params()

                # 预处理日志
                preprocessor = LogPreprocessor()
                crash_logs = preprocessor.extract_crash_logs(self.main_app.log_entries)

                if not crash_logs:
                    self.main_app.root.after(0, self.append_chat, "system", "未发现崩溃日志")
                    return

                # 取第一个崩溃
                crash = crash_logs[0]

                # 获取项目代码上下文
                project_context = self.get_project_context(max_chars=5000)

                # 构建提示词（使用上下文参数）
                crash_info = {
                    'crash_time': crash.crash_time,
                    'crash_exception': crash.crash_entry.content,
                    'crash_stack': crash.crash_entry.content,  # 崩溃堆栈就是内容本身
                    'context_before': preprocessor.summarize_logs(crash.context_before[:params['crash_before']] if crash.context_before else []),
                    'context_after': preprocessor.summarize_logs(crash.context_after[:params['crash_after']] if crash.context_after else [])
                }

                prompt = PromptTemplates.format_crash_analysis(crash_info)

                # 如果有项目代码上下文，添加到提示词末尾
                if project_context:
                    prompt += f"\n\n{project_context}\n\n请结合以上项目代码进行分析，找出崩溃可能涉及的具体代码位置和原因。"

                # 调用AI
                if not self.ai_client:
                    self.main_app.root.after(0, self.append_chat, "system", "AI服务初始化失败")
                    return

                response = self.ai_client.ask(prompt)

                # 显示结果
                self.main_app.root.after(0, self.append_chat, "assistant", response)

            except Exception as e:
                error_msg = f"分析失败: {str(e)}"
                self.main_app.root.after(0, self.append_chat, "system", error_msg)

            finally:
                self.is_processing = False
                self.main_app.root.after(0, self.hide_stop_button)  # 隐藏停止按钮
                self.main_app.root.after(0, self.hide_progress)  # 隐藏进度条
                self.main_app.root.after(0, self.set_status, "就绪")

        # 异步执行
        threading.Thread(target=_analyze, daemon=True).start()

    def analyze_performance(self):
        """性能诊断"""
        if not self.main_app.log_entries:
            messagebox.showwarning("警告", "请先加载日志文件")
            return

        if self.is_processing:
            messagebox.showinfo("提示", "AI正在处理中，请稍候")
            return

        self.is_processing = True
        self.stop_flag = False
        self.set_status("正在诊断性能问题...")
        self.append_chat("user", "诊断性能问题")
        self.main_app.root.after(0, self.show_stop_button)
        self.main_app.root.after(0, self.show_progress)

        def _analyze():
            try:
                if self.stop_flag:
                    return
                _, _, LogPreprocessor, PromptTemplates = safe_import_ai_diagnosis()

                # 获取上下文参数
                params = self.get_context_params()

                preprocessor = LogPreprocessor()

                # 提取性能相关日志（ERROR和WARNING），使用上下文参数
                perf_logs = [
                    e for e in self.main_app.log_entries
                    if e.level in ['ERROR', 'WARNING']
                ][:params['perf_logs']]

                if not perf_logs:
                    self.main_app.root.after(0, self.append_chat, "system", "未发现性能相关问题")
                    return

                # 统计信息
                stats = preprocessor.get_statistics(self.main_app.log_entries)

                # 构建提示词
                perf_info = {
                    'total_logs': len(self.main_app.log_entries),
                    'error_count': stats.get('ERROR', 0),
                    'warning_count': stats.get('WARNING', 0),
                    'top_modules': ', '.join([f"{k}({v})" for k, v in stats.get('modules', {}).items()][:5]),
                    'sample_logs': preprocessor.summarize_logs(perf_logs)
                }

                prompt = PromptTemplates.format_performance_analysis(perf_info)

                # 调用AI
                if not self.ai_client:
                    self.main_app.root.after(0, self.append_chat, "system", "AI服务初始化失败")
                    return

                response = self.ai_client.ask(prompt)

                # 显示结果
                self.main_app.root.after(0, self.append_chat, "assistant", response)

            except Exception as e:
                error_msg = f"诊断失败: {str(e)}"
                self.main_app.root.after(0, self.append_chat, "system", error_msg)

            finally:
                self.is_processing = False
                self.main_app.root.after(0, self.hide_stop_button)
                self.main_app.root.after(0, self.hide_progress)
                self.main_app.root.after(0, self.set_status, "就绪")

        threading.Thread(target=_analyze, daemon=True).start()

    def summarize_issues(self):
        """问题总结"""
        if not self.main_app.log_entries:
            messagebox.showwarning("警告", "请先加载日志文件")
            return

        if self.is_processing:
            messagebox.showinfo("提示", "AI正在处理中，请稍候")
            return

        self.is_processing = True
        self.stop_flag = False
        self.set_status("正在生成问题总结...")
        self.append_chat("user", "生成问题总结")
        self.main_app.root.after(0, self.show_stop_button)
        self.main_app.root.after(0, self.show_progress)

        def _analyze():
            try:
                if self.stop_flag:
                    return
                _, _, LogPreprocessor, PromptTemplates = safe_import_ai_diagnosis()

                # 获取上下文参数
                params = self.get_context_params()

                preprocessor = LogPreprocessor()

                # 提取错误模式（使用上下文参数）
                error_patterns = preprocessor.extract_error_patterns(self.main_app.log_entries)

                # 统计信息
                stats = preprocessor.get_statistics(self.main_app.log_entries)

                # 构建提示词（使用上下文参数限制错误模式数量）
                issue_info = {
                    'total_logs': len(self.main_app.log_entries),
                    'error_count': stats.get('ERROR', 0),
                    'warning_count': stats.get('WARNING', 0),
                    'crash_count': len([e for e in self.main_app.log_entries if e.is_crash]),
                    'error_patterns': '\n'.join([
                        f"- {p.signature} (出现{p.count}次)"
                        for p in error_patterns[:params['error_patterns']]
                    ]),
                    'top_modules': ', '.join([f"{k}({v})" for k, v in stats.get('modules', {}).items()][:5])
                }

                prompt = PromptTemplates.format_issue_summary(issue_info)

                # 调用AI
                if not self.ai_client:
                    self.main_app.root.after(0, self.append_chat, "system", "AI服务初始化失败")
                    return

                response = self.ai_client.ask(prompt)

                # 显示结果
                self.main_app.root.after(0, self.append_chat, "assistant", response)

            except Exception as e:
                error_msg = f"总结失败: {str(e)}"
                self.main_app.root.after(0, self.append_chat, "system", error_msg)

            finally:
                self.is_processing = False
                self.main_app.root.after(0, self.hide_stop_button)
                self.main_app.root.after(0, self.hide_progress)
                self.main_app.root.after(0, self.set_status, "就绪")

        threading.Thread(target=_analyze, daemon=True).start()

    def smart_search(self):
        """智能搜索"""
        # 弹出对话框输入搜索描述
        search_dialog = tk.Toplevel(self.parent)
        search_dialog.title("智能搜索")
        search_dialog.geometry("400x150")

        ttk.Label(
            search_dialog,
            text="描述你要搜索的内容:",
            font=("Arial", 11)
        ).pack(pady=10)

        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_dialog, textvariable=search_var, width=50)
        search_entry.pack(pady=5)
        search_entry.focus()

        def do_search():
            description = search_var.get().strip()
            if not description:
                return

            search_dialog.destroy()

            if not self.main_app.log_entries:
                messagebox.showwarning("警告", "请先加载日志文件")
                return

            if self.is_processing:
                messagebox.showinfo("提示", "AI正在处理中，请稍候")
                return

            self.is_processing = True
            self.stop_flag = False
            self.set_status("正在智能搜索...")
            self.append_chat("user", f"搜索: {description}")
            self.main_app.root.after(0, self.show_stop_button)
            self.main_app.root.after(0, self.show_progress)

            def _search():
                try:
                    if self.stop_flag:
                        return
                    _, _, LogPreprocessor, PromptTemplates = safe_import_ai_diagnosis()

                    # 获取上下文参数
                    params = self.get_context_params()

                    preprocessor = LogPreprocessor()

                    # 摘要日志（使用上下文参数）
                    summary = preprocessor.summarize_logs(
                        self.main_app.log_entries[:params['search_logs']],
                        max_tokens=params['search_tokens']
                    )

                    # 构建提示词
                    search_info = {
                        'search_description': description,
                        'log_summary': summary
                    }

                    prompt = PromptTemplates.format_smart_search(search_info)

                    # 调用AI
                    if not self.ai_client:
                        self.main_app.root.after(0, self.append_chat, "system", "AI服务初始化失败")
                        return

                    response = self.ai_client.ask(prompt)

                    # 显示结果
                    self.main_app.root.after(0, self.append_chat, "assistant", response)

                except Exception as e:
                    error_msg = f"搜索失败: {str(e)}"
                    self.main_app.root.after(0, self.append_chat, "system", error_msg)

                finally:
                    self.is_processing = False
                    self.main_app.root.after(0, self.hide_stop_button)
                    self.main_app.root.after(0, self.hide_progress)
                    self.main_app.root.after(0, self.set_status, "就绪")

            threading.Thread(target=_search, daemon=True).start()

        ttk.Button(
            search_dialog,
            text="搜索",
            command=do_search
        ).pack(pady=10)

        search_entry.bind('<Return>', lambda e: do_search())

    def ask_common_question(self, question: str):
        """
        提问常用问题

        Args:
            question: 预设的问题文本
        """
        # 设置输入框内容
        self.question_var.set(question)

        # 触发提问
        self.ask_question()

    def ask_question(self):
        """自由提问"""
        question = self.question_var.get().strip()
        if not question:
            return

        # 清空输入框
        self.question_var.set("")

        if self.is_processing:
            messagebox.showinfo("提示", "AI正在处理中，请稍候")
            return

        self.is_processing = True
        self.stop_flag = False
        self.set_status("正在思考...")
        self.append_chat("user", question)
        self.main_app.root.after(0, self.show_stop_button)
        self.main_app.root.after(0, self.show_progress)

        def _ask():
            try:
                if self.stop_flag:
                    return
                # 加载配置
                _, AIConfig, LogPreprocessor, PromptTemplates = safe_import_ai_diagnosis()
                config = AIConfig.load()
                context_size = config.get('context_size', '标准')
                show_token_usage = config.get('show_token_usage', True)

                # 检查是否有日志
                has_logs = hasattr(self.main_app, 'log_entries') and self.main_app.log_entries

                # 简单问候或没有日志时，使用简化提示词
                simple_greetings = ['你好', 'hello', 'hi', '嗨', '您好']
                is_greeting = question.lower().strip() in simple_greetings

                if is_greeting or not has_logs:
                    # 简化模式：不包含日志上下文
                    prompt = f"用户问题：{question}\n\n"
                    if not has_logs:
                        prompt += "注意：用户还没有加载日志文件。"
                    else:
                        prompt += "这是一个简单的问候，请友好地回复并简要介绍你可以提供的帮助。"
                else:
                    # 根据配置的上下文大小调整参数
                    context_params = {
                        '简化': {'log_count': 50, 'max_tokens': 1000, 'history_rounds': 2, 'module_count': 2},
                        '标准': {'log_count': 100, 'max_tokens': 2000, 'history_rounds': 3, 'module_count': 3},
                        '详细': {'log_count': 200, 'max_tokens': 4000, 'history_rounds': 5, 'module_count': 5}
                    }
                    params = context_params.get(context_size, context_params['标准'])

                    # 完整模式：包含日志上下文
                    preprocessor = LogPreprocessor()

                    # 摘要当前日志
                    current_logs = self.main_app.filtered_entries if hasattr(self.main_app, 'filtered_entries') and self.main_app.filtered_entries else self.main_app.log_entries

                    summary = preprocessor.summarize_logs(
                        current_logs[:params['log_count']],
                        max_tokens=params['max_tokens']
                    )

                    # 获取统计信息
                    stats = preprocessor.get_statistics(current_logs)

                    # 构建提示词
                    qa_info = {
                        'filename': getattr(self.main_app, 'current_file', 'N/A'),
                        'total_logs': len(self.main_app.log_entries),
                        'current_logs': len(current_logs),
                        'time_range': stats.get('time_range', 'N/A'),
                        'main_modules': ', '.join([f"{k}({v})" for k, v in stats.get('modules', {}).items()][:params['module_count']]),
                        'crash_count': stats.get('crashes', 0),
                        'error_count': stats.get('errors', 0),
                        'warning_count': stats.get('warnings', 0),
                        'relevant_logs': summary[:5000],
                        'user_question': question,
                        'chat_history': '\n'.join([
                            f"{h['role']}: {h['message'][:100]}"
                            for h in self.chat_history[-params['history_rounds']:]
                        ])
                    }

                    prompt = PromptTemplates.format_interactive_qa(qa_info)

                # 估算token数（粗略估计：中文1字=1token，英文4字符=1token）
                estimated_tokens = len(prompt.replace(' ', '')) + len(prompt.split()) // 4

                # 显示token使用情况
                if show_token_usage:
                    token_info = f"📊 Token使用: 输入~{estimated_tokens}"
                    self.main_app.root.after(0, self.set_status, token_info)

                # 调用AI
                if not self.ai_client:
                    self.main_app.root.after(0, self.append_chat, "system", "AI服务初始化失败")
                    return

                response = self.ai_client.ask(prompt)

                # 估算响应token数
                response_tokens = len(response.replace(' ', '')) + len(response.split()) // 4
                total_tokens = estimated_tokens + response_tokens

                # 累加Token统计
                self.total_input_tokens += estimated_tokens
                self.total_output_tokens += response_tokens

                # 显示结果
                self.main_app.root.after(0, self.append_chat, "assistant", response)

                # 更新token统计
                if show_token_usage:
                    session_total = self.total_input_tokens + self.total_output_tokens
                    token_summary = (
                        f"📊 本次: 输入~{estimated_tokens} + 输出~{response_tokens} = {total_tokens} | "
                        f"会话: 输入~{self.total_input_tokens} + 输出~{self.total_output_tokens} = {session_total}"
                    )
                    self.main_app.root.after(0, self.set_status, token_summary)

            except Exception as e:
                error_msg = f"提问失败: {str(e)}"
                self.main_app.root.after(0, self.append_chat, "system", error_msg)

            finally:
                self.is_processing = False
                self.main_app.root.after(0, self.hide_stop_button)
                self.main_app.root.after(0, self.hide_progress)
                # 不覆盖token统计，延迟3秒后恢复"就绪"状态
                if not show_token_usage or 'error_msg' in locals():
                    self.main_app.root.after(0, self.set_status, "就绪")
                else:
                    self.main_app.root.after(3000, self.set_status, "就绪")

        threading.Thread(target=_ask, daemon=True).start()

    def show_settings(self):
        """显示AI设置对话框"""
        try:
            from ai_diagnosis_settings import AISettingsDialog
        except ImportError:
            try:
                from modules.ai_diagnosis_settings import AISettingsDialog
            except ImportError:
                from gui.modules.ai_diagnosis_settings import AISettingsDialog

        dialog = AISettingsDialog(self.parent, self.main_app)

        # 如果设置被修改,重置AI客户端
        if dialog.settings_changed:
            self._ai_client = None
            self.append_chat("system", "AI设置已更新")

    def search_chat(self):
        """搜索对话历史"""
        keyword = self.search_var.get().strip()

        # 移除之前的高亮
        self.chat_text.tag_remove("search_highlight", "1.0", tk.END)

        if not keyword:
            self.search_result_var.set("")
            return

        # 搜索并高亮
        match_count = 0
        start_pos = "1.0"

        while True:
            # 不区分大小写搜索
            pos = self.chat_text.search(
                keyword,
                start_pos,
                tk.END,
                nocase=True
            )

            if not pos:
                break

            # 计算匹配文本的结束位置
            end_pos = f"{pos}+{len(keyword)}c"

            # 添加高亮标签
            self.chat_text.tag_add("search_highlight", pos, end_pos)

            match_count += 1
            start_pos = end_pos

        # 更新搜索结果计数
        if match_count > 0:
            self.search_result_var.set(f"找到 {match_count} 处")

            # 滚动到第一个匹配位置
            first_match = self.chat_text.search(
                keyword,
                "1.0",
                tk.END,
                nocase=True
            )
            if first_match:
                self.chat_text.see(first_match)
        else:
            self.search_result_var.set("无匹配")

    def clear_search(self):
        """清除搜索"""
        self.search_var.set("")
        self.chat_text.tag_remove("search_highlight", "1.0", tk.END)
        self.search_result_var.set("")
