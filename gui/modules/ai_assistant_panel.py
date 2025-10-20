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
        from ai_diagnosis.token_optimizer import TokenOptimizer
        return AIClientFactory, AIConfig, LogPreprocessor, PromptTemplates, TokenOptimizer
    except ImportError:
        try:
            from modules.ai_diagnosis import AIClientFactory, AIConfig
            from modules.ai_diagnosis.log_preprocessor import LogPreprocessor
            from modules.ai_diagnosis.prompt_templates import PromptTemplates
            from modules.ai_diagnosis.token_optimizer import TokenOptimizer
            return AIClientFactory, AIConfig, LogPreprocessor, PromptTemplates, TokenOptimizer
        except ImportError:
            from gui.modules.ai_diagnosis import AIClientFactory, AIConfig
            from gui.modules.ai_diagnosis.log_preprocessor import LogPreprocessor
            from gui.modules.ai_diagnosis.prompt_templates import PromptTemplates
            from gui.modules.ai_diagnosis.token_optimizer import TokenOptimizer
            return AIClientFactory, AIConfig, LogPreprocessor, PromptTemplates, TokenOptimizer


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

        # Token优化器（延迟初始化）
        self._token_optimizer = None

        # 评分记录（用于收集用户反馈）
        self.ratings = []

        # 跳转历史记录
        self.jump_history = []  # 存储跳转历史 [(log_index, timestamp), ...]
        self.jump_history_index = -1  # 当前位置索引

        # 预览窗口
        self.preview_window = None

        # 创建UI
        self.create_widgets()

    @property
    def ai_client(self):
        """延迟初始化AI客户端"""
        if self._ai_client is None:
            try:
                AIClientFactory, AIConfig, _, _, _ = safe_import_ai_diagnosis()
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

    @property
    def token_optimizer(self):
        """延迟初始化Token优化器"""
        if self._token_optimizer is None:
            try:
                _, AIConfig, _, _, TokenOptimizer = safe_import_ai_diagnosis()
                config = AIConfig.load()
                model = config.get('model', 'claude-3-5-sonnet-20241022')
                self._token_optimizer = TokenOptimizer(model=model)
            except Exception as e:
                print(f"Token优化器初始化失败: {str(e)}")
                # 使用默认配置
                try:
                    _, _, _, _, TokenOptimizer = safe_import_ai_diagnosis()
                    self._token_optimizer = TokenOptimizer()
                except:
                    return None
        return self._token_optimizer

    def get_project_context(self, max_chars: int = 8000) -> str:
        """
        读取项目代码作为上下文

        Args:
            max_chars: 最大字符数

        Returns:
            项目代码内容字符串
        """
        import os

        _, AIConfig, _, _, _ = safe_import_ai_diagnosis()
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

        # 跳转历史按钮（后退和前进）
        self.back_button = ttk.Button(
            title_frame,
            text="◀",
            width=3,
            command=self.jump_back,
            state=tk.DISABLED  # 初始禁用
        )
        self.back_button.pack(side=tk.LEFT, padx=2)

        self.forward_button = ttk.Button(
            title_frame,
            text="▶",
            width=3,
            command=self.jump_forward,
            state=tk.DISABLED  # 初始禁用
        )
        self.forward_button.pack(side=tk.LEFT, padx=2)

        # 自定义Prompt按钮（新增） 🆕
        ttk.Button(
            title_frame,
            text="📝",
            width=3,
            command=self.show_custom_prompts
        ).pack(side=tk.RIGHT, padx=2)

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

        # 定义所有按钮（快捷操作 + 常用问题 + Mars模块分析）
        all_actions = [
            # 第一行
            ("🔍 崩溃", self.analyze_crashes),
            ("📊 性能", self.analyze_performance),
            # 第二行
            ("📝 总结", self.summarize_issues),
            ("🔎 搜索", self.smart_search),
            # 第三行 - Mars模块分析（新增）
            ("🏥 模块健康", self.analyze_module_health),
            ("🔬 问题模块", self.analyze_unhealthy_modules),
            # 第四行 - 常用问题
            ("💡 性能优化", lambda: self.ask_common_question("如何提升应用性能？有哪些优化建议？")),
            ("🐛 错误原因", lambda: self.ask_common_question("这些错误的常见原因有哪些？如何避免？")),
            # 第五行 - 常用问题
            ("📝 最佳实践", lambda: self.ask_common_question("日志记录的最佳实践是什么？")),
            ("🔧 调试技巧", lambda: self.ask_common_question("如何高效地调试这类问题？")),
        ]

        # 创建5x2网格布局（5行2列）
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

        # 自定义Prompt快捷按钮（新增）
        ttk.Button(
            input_frame,
            text="📝▼",
            width=4,
            command=self.show_prompt_selector
        ).pack(side=tk.LEFT, padx=(0, 5))

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
        添加对话到历史（增强版：支持日志跳转）

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

        # 解析消息中的日志引用并创建可点击链接
        if role == "assistant":
            self._insert_message_with_links(message)
        else:
            # 普通消息
            self.chat_text.insert(tk.END, f"{message}\n\n", "content")

        self.chat_text.config(state=tk.DISABLED)
        self.chat_text.see(tk.END)  # 滚动到底部

    def _insert_message_with_links(self, message: str):
        """
        插入带日志跳转链接的消息

        支持的格式：
        - [时间戳]: [2025-09-21 13:09:49]
        - #行号: #123
        - @模块名: @NetworkModule
        """
        import re

        # 定义所有匹配模式（优先级从高到低）
        patterns = [
            # 时间戳格式: [2025-09-21 13:09:49] 或 [2025-09-21 +8.0 13:09:49.038]
            (r'\[([\d\-: +\.]+)\]', 'timestamp'),
            # 行号格式: #123
            (r'#(\d+)', 'line_number'),
            # 模块名格式: @ModuleName (支持中英文、下划线、数字)
            (r'@([\w\u4e00-\u9fa5]+)', 'module_name')
        ]

        # 收集所有匹配项
        all_matches = []
        for pattern, link_type in patterns:
            for match in re.finditer(pattern, message):
                all_matches.append({
                    'start': match.start(),
                    'end': match.end(),
                    'type': link_type,
                    'value': match.group(1),
                    'display': match.group(0)
                })

        # 按位置排序并去重（重叠部分保留第一个）
        all_matches.sort(key=lambda x: x['start'])
        filtered_matches = []
        last_end = 0
        for match in all_matches:
            if match['start'] >= last_end:
                filtered_matches.append(match)
                last_end = match['end']

        # 构建parts列表
        parts = []
        last_end = 0

        for match in filtered_matches:
            # 添加匹配前的文本
            if match['start'] > last_end:
                parts.append(('text', message[last_end:match['start']]))

            # 添加链接
            parts.append(('link', match['type'], match['value'], match['display']))
            last_end = match['end']

        # 添加剩余文本
        if last_end < len(message):
            parts.append(('text', message[last_end:]))

        # 插入到Text组件
        for part in parts:
            if part[0] == 'text':
                self.chat_text.insert(tk.END, part[1], "content")
            elif part[0] == 'link':
                link_type, value, display_text = part[1], part[2], part[3]

                # 创建唯一tag
                tag_name = f"link_{id(part)}"

                # 插入链接文本
                self.chat_text.insert(tk.END, display_text, ("content", "log_link", tag_name))

                # 根据链接类型绑定不同的点击事件
                if link_type == 'timestamp':
                    self.chat_text.tag_bind(
                        tag_name,
                        "<Button-1>",
                        lambda e, ts=value: self._jump_to_log_by_timestamp(ts)
                    )
                elif link_type == 'line_number':
                    self.chat_text.tag_bind(
                        tag_name,
                        "<Button-1>",
                        lambda e, ln=value: self._jump_to_log_by_line_number(ln)
                    )
                elif link_type == 'module_name':
                    self.chat_text.tag_bind(
                        tag_name,
                        "<Button-1>",
                        lambda e, mn=value: self._jump_to_module(mn)
                    )

                # 设置链接样式
                self.chat_text.tag_config(tag_name,
                    foreground="#0066CC",
                    underline=True,
                    font=("Arial", 11, "bold"))

                # 设置鼠标悬停效果
                if link_type == 'timestamp':
                    self.chat_text.tag_bind(tag_name, "<Enter>",
                        lambda e, tag=tag_name, ts=value: self._show_log_preview(e, ts, 'timestamp'))
                elif link_type == 'line_number':
                    self.chat_text.tag_bind(tag_name, "<Enter>",
                        lambda e, tag=tag_name, ln=value: self._show_log_preview(e, ln, 'line_number'))
                elif link_type == 'module_name':
                    self.chat_text.tag_bind(tag_name, "<Enter>",
                        lambda e, tag=tag_name, mn=value: self._show_log_preview(e, mn, 'module_name'))

                self.chat_text.tag_bind(tag_name, "<Leave>",
                    lambda e: self._hide_log_preview())

        self.chat_text.insert(tk.END, "\n\n")

    def _jump_to_log_by_timestamp(self, timestamp: str):
        """
        根据时间戳跳转到日志并高亮

        Args:
            timestamp: 日志时间戳
        """
        try:
            # 在日志列表中查找匹配的时间戳
            log_index = None
            for i, entry in enumerate(self.main_app.log_entries):
                if entry.timestamp == timestamp:
                    log_index = i
                    break

            if log_index is None:
                # 尝试模糊匹配（去除时区、毫秒等）
                timestamp_short = timestamp.split('.')[0].split('+')[0].strip()
                for i, entry in enumerate(self.main_app.log_entries):
                    if entry.timestamp and entry.timestamp.startswith(timestamp_short):
                        log_index = i
                        break

            if log_index is not None:
                self._jump_to_log(log_index)
            else:
                self.set_status(f"未找到时间戳为 {timestamp} 的日志")

        except Exception as e:
            print(f"跳转失败: {str(e)}")
            self.set_status(f"跳转失败: {str(e)}")

    def _jump_to_log(self, log_index: int, add_to_history: bool = True):
        """
        跳转到指定日志并高亮显示

        Args:
            log_index: 日志索引
            add_to_history: 是否添加到历史记录
        """
        try:
            # 添加到跳转历史（如果不是从历史记录跳转）
            if add_to_history:
                # 获取时间戳
                timestamp = None
                if log_index < len(self.main_app.log_entries):
                    timestamp = self.main_app.log_entries[log_index].timestamp

                # 如果当前不在历史末尾，清除后续历史
                if self.jump_history_index < len(self.jump_history) - 1:
                    self.jump_history = self.jump_history[:self.jump_history_index + 1]

                # 添加到历史
                self.jump_history.append((log_index, timestamp))
                self.jump_history_index = len(self.jump_history) - 1

                # 更新按钮状态
                self._update_jump_buttons()

            # 确保日志查看器可见
            if hasattr(self.main_app, 'notebook'):
                # 切换到日志查看标签页
                self.main_app.notebook.select(0)

            # 滚动到目标日志
            # 使用improved_lazy_text的scroll_to_line方法
            if hasattr(self.main_app.log_text, 'scroll_to_line'):
                self.main_app.log_text.scroll_to_line(log_index)
            else:
                # 后备方案：使用see方法
                self.main_app.log_text.see(f"{log_index + 1}.0")

            # 高亮显示（渐变动画）
            if hasattr(self.main_app.log_text, 'text_widget'):
                text_widget = self.main_app.log_text.text_widget
            else:
                text_widget = self.main_app.log_text

            # 使用渐变高亮动画
            self._animate_highlight(text_widget, log_index + 1)

            # 提示用户
            history_info = ""
            if add_to_history and len(self.jump_history) > 1:
                history_info = f" (历史 {self.jump_history_index + 1}/{len(self.jump_history)})"
            self.set_status(f"已跳转到第 {log_index + 1} 行日志{history_info}")

        except Exception as e:
            print(f"跳转到日志失败: {str(e)}")
            self.set_status(f"跳转失败: {str(e)}")

    def _jump_to_log_by_line_number(self, line_number: str):
        """
        根据行号跳转到日志

        Args:
            line_number: 行号字符串（如"123"）
        """
        try:
            # 转换为整数（行号从1开始，索引从0开始）
            log_index = int(line_number) - 1

            # 验证行号范围
            if log_index < 0 or log_index >= len(self.main_app.log_entries):
                self.set_status(f"行号 #{line_number} 超出范围（1-{len(self.main_app.log_entries)}）")
                return

            # 调用通用跳转方法
            self._jump_to_log(log_index)

        except ValueError:
            self.set_status(f"无效的行号: #{line_number}")
        except Exception as e:
            print(f"行号跳转失败: {str(e)}")
            self.set_status(f"行号跳转失败: {str(e)}")

    def _jump_to_module(self, module_name: str):
        """
        根据模块名跳转到该模块的第一条日志

        Args:
            module_name: 模块名（如"NetworkModule"）
        """
        try:
            # 查找该模块的第一条日志
            log_index = None
            for i, entry in enumerate(self.main_app.log_entries):
                if entry.module == module_name:
                    log_index = i
                    break

            if log_index is not None:
                # 切换到模块分组标签页
                if hasattr(self.main_app, 'notebook'):
                    # 假设模块分组是第2个标签页（索引为1）
                    try:
                        self.main_app.notebook.select(1)
                    except:
                        pass

                # 如果有模块列表，尝试选中该模块
                if hasattr(self.main_app, 'module_listbox'):
                    # 查找模块在列表中的位置
                    for idx in range(self.main_app.module_listbox.size()):
                        item_text = self.main_app.module_listbox.get(idx)
                        if module_name in item_text:
                            self.main_app.module_listbox.selection_clear(0, tk.END)
                            self.main_app.module_listbox.selection_set(idx)
                            self.main_app.module_listbox.see(idx)
                            # 触发选择事件
                            if hasattr(self.main_app, 'on_module_select'):
                                self.main_app.on_module_select(None)
                            break

                self.set_status(f"已跳转到模块 @{module_name} 的第一条日志（第 {log_index + 1} 行）")
            else:
                self.set_status(f"未找到模块 @{module_name} 的日志")

        except Exception as e:
            print(f"模块跳转失败: {str(e)}")
            self.set_status(f"模块跳转失败: {str(e)}")

    def _show_log_preview(self, event, value, link_type):
        """
        显示日志预览窗口

        Args:
            event: 鼠标事件
            value: 链接值（时间戳、行号或模块名）
            link_type: 链接类型
        """
        # 设置手型光标
        self.chat_text.config(cursor="hand2")

        # 查找对应的日志
        log_index = None
        preview_lines = []

        if link_type == 'timestamp':
            # 根据时间戳查找
            for i, entry in enumerate(self.main_app.log_entries):
                if entry.timestamp == value or (entry.timestamp and entry.timestamp.startswith(value.split('.')[0].split('+')[0].strip())):
                    log_index = i
                    break
        elif link_type == 'line_number':
            # 直接使用行号
            try:
                log_index = int(value) - 1
            except:
                pass
        elif link_type == 'module_name':
            # 查找模块的第一条日志
            for i, entry in enumerate(self.main_app.log_entries):
                if entry.module == value:
                    log_index = i
                    break

        if log_index is not None and 0 <= log_index < len(self.main_app.log_entries):
            # 获取上下文（前后各2行）
            start = max(0, log_index - 2)
            end = min(len(self.main_app.log_entries), log_index + 3)

            for i in range(start, end):
                entry = self.main_app.log_entries[i]
                prefix = "➤ " if i == log_index else "  "
                preview_lines.append(f"{prefix}#{i+1}: [{entry.level}] {entry.content[:80]}...")

        if preview_lines:
            # 创建预览窗口
            self.preview_window = tk.Toplevel(self.main_app.root)
            self.preview_window.wm_overrideredirect(True)  # 无边框窗口
            self.preview_window.wm_attributes("-topmost", True)  # 置顶

            # 设置窗口位置（鼠标附近）
            x = event.x_root + 10
            y = event.y_root + 10
            self.preview_window.wm_geometry(f"+{x}+{y}")

            # 创建预览内容
            preview_frame = tk.Frame(self.preview_window, bg="#FFFFCC", relief=tk.SOLID, borderwidth=1)
            preview_frame.pack()

            preview_text = tk.Text(
                preview_frame,
                wrap=tk.WORD,
                width=80,
                height=len(preview_lines),
                font=("Monaco", 9),
                bg="#FFFFCC",
                fg="#000000",
                relief=tk.FLAT
            )
            preview_text.pack(padx=5, pady=5)

            # 插入预览内容
            for line in preview_lines:
                if line.startswith("➤"):
                    preview_text.insert(tk.END, line + "\n", "highlight")
                else:
                    preview_text.insert(tk.END, line + "\n")

            # 配置高亮样式
            preview_text.tag_config("highlight", background="#FFFF99", font=("Monaco", 9, "bold"))

            preview_text.config(state=tk.DISABLED)

    def _hide_log_preview(self):
        """隐藏日志预览窗口"""
        # 恢复默认光标
        self.chat_text.config(cursor="")

        # 销毁预览窗口
        if hasattr(self, 'preview_window') and self.preview_window:
            try:
                self.preview_window.destroy()
                self.preview_window = None
            except:
                pass

    def _animate_highlight(self, text_widget, line_num, duration=2000, steps=20):
        """
        渐变高亮动画

        Args:
            text_widget: 文本组件
            line_num: 行号
            duration: 动画总时长（毫秒）
            steps: 动画步数
        """
        # 高亮颜色（从亮黄色渐变到无色）
        colors = [
            "#FFFF00",  # 亮黄色
            "#FFFF33",
            "#FFFF66",
            "#FFFF99",
            "#FFFFCC",
            "#FFFFEE",
            "#FFFFFF",  # 白色（透明）
        ]

        interval = duration // len(colors)

        def apply_color(index):
            if index < len(colors):
                # 配置当前颜色
                text_widget.tag_config("ai_highlight",
                    background=colors[index],
                    foreground="#000000")

                # 添加/更新高亮
                text_widget.tag_remove("ai_highlight", "1.0", "end")
                text_widget.tag_add("ai_highlight", f"{line_num}.0", f"{line_num}.end")

                # 调度下一步
                self.main_app.root.after(interval, lambda: apply_color(index + 1))
            else:
                # 动画结束，移除高亮
                text_widget.tag_remove("ai_highlight", "1.0", "end")

        # 开始动画
        apply_color(0)

    def _update_jump_buttons(self):
        """更新前进/后退按钮的状态"""
        # 更新后退按钮
        if self.jump_history_index > 0:
            self.back_button.config(state=tk.NORMAL)
        else:
            self.back_button.config(state=tk.DISABLED)

        # 更新前进按钮
        if self.jump_history_index < len(self.jump_history) - 1:
            self.forward_button.config(state=tk.NORMAL)
        else:
            self.forward_button.config(state=tk.DISABLED)

    def jump_back(self):
        """后退到上一个跳转位置"""
        if self.jump_history_index > 0:
            self.jump_history_index -= 1
            log_index, timestamp = self.jump_history[self.jump_history_index]

            # 跳转但不添加到历史
            self._jump_to_log(log_index, add_to_history=False)

            # 更新按钮状态
            self._update_jump_buttons()

            # 更新状态
            self.set_status(f"后退到第 {log_index + 1} 行 (历史 {self.jump_history_index + 1}/{len(self.jump_history)})")

    def jump_forward(self):
        """前进到下一个跳转位置"""
        if self.jump_history_index < len(self.jump_history) - 1:
            self.jump_history_index += 1
            log_index, timestamp = self.jump_history[self.jump_history_index]

            # 跳转但不添加到历史
            self._jump_to_log(log_index, add_to_history=False)

            # 更新按钮状态
            self._update_jump_buttons()

            # 更新状态
            self.set_status(f"前进到第 {log_index + 1} 行 (历史 {self.jump_history_index + 1}/{len(self.jump_history)})")

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

        _, AIConfig, _, _, _ = safe_import_ai_diagnosis()
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

                # 使用Token优化器
                optimizer = self.token_optimizer
                if not optimizer:
                    self.main_app.root.after(0, self.append_chat, "system", "Token优化器初始化失败")
                    return

                # 优化崩溃分析提示词
                optimized = optimizer.optimize_for_crash_analysis(self.main_app.log_entries)

                # 检查token预算
                within_budget, message = optimizer.check_budget(optimized.estimated_tokens)
                if not within_budget:
                    self.main_app.root.after(0, self.append_chat, "system", f"⚠️ {message}")
                    return

                # 显示token使用情况
                self.main_app.root.after(0, self.set_status, f"📊 {message} | 压缩比: {optimized.compression_ratio:.1%}")

                # 使用优化后的提示词
                prompt = optimized.prompt

                # 如果有项目代码上下文，添加到提示词末尾
                project_context = self.get_project_context(max_chars=5000)
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

                # 使用Token优化器
                optimizer = self.token_optimizer
                if not optimizer:
                    self.main_app.root.after(0, self.append_chat, "system", "Token优化器初始化失败")
                    return

                # 优化性能分析提示词
                optimized = optimizer.optimize_for_performance_analysis(self.main_app.log_entries)

                # 检查token预算
                within_budget, message = optimizer.check_budget(optimized.estimated_tokens)
                if not within_budget:
                    self.main_app.root.after(0, self.append_chat, "system", f"⚠️ {message}")
                    return

                # 显示token使用情况
                self.main_app.root.after(0, self.set_status, f"📊 {message} | 压缩比: {optimized.compression_ratio:.1%}")

                # 使用优化后的提示词
                prompt = optimized.prompt

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

                # 使用Token优化器
                optimizer = self.token_optimizer
                if not optimizer:
                    self.main_app.root.after(0, self.append_chat, "system", "Token优化器初始化失败")
                    return

                # 优化问题总结提示词
                optimized = optimizer.optimize_for_issue_summary(self.main_app.log_entries)

                # 检查token预算
                within_budget, message = optimizer.check_budget(optimized.estimated_tokens)
                if not within_budget:
                    self.main_app.root.after(0, self.append_chat, "system", f"⚠️ {message}")
                    return

                # 显示token使用情况
                self.main_app.root.after(0, self.set_status, f"📊 {message} | 压缩比: {optimized.compression_ratio:.1%}")

                # 使用优化后的提示词
                prompt = optimized.prompt

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

                    # 使用Token优化器
                    optimizer = self.token_optimizer
                    if not optimizer:
                        self.main_app.root.after(0, self.append_chat, "system", "Token优化器初始化失败")
                        return

                    # 优化智能搜索提示词
                    optimized = optimizer.optimize_for_interactive_qa(
                        self.main_app.log_entries,
                        user_question=description
                    )

                    # 检查token预算
                    within_budget, message = optimizer.check_budget(optimized.estimated_tokens)
                    if not within_budget:
                        self.main_app.root.after(0, self.append_chat, "system", f"⚠️ {message}")
                        return

                    # 显示token使用情况
                    self.main_app.root.after(0, self.set_status, f"📊 {message} | 压缩比: {optimized.compression_ratio:.1%}")

                    # 使用优化后的提示词
                    prompt = optimized.prompt

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

    def analyze_module_health(self):
        """分析各模块健康状况"""
        if not self.main_app.log_entries:
            messagebox.showwarning("警告", "请先加载日志文件")
            return

        if self.is_processing:
            messagebox.showinfo("提示", "AI正在处理中，请稍候")
            return

        self.is_processing = True
        self.stop_flag = False
        self.set_status("正在分析模块健康...")
        self.append_chat("user", "分析各模块健康状况")
        self.main_app.root.after(0, self.show_stop_button)
        self.main_app.root.after(0, self.show_progress)

        def _analyze():
            try:
                if self.stop_flag:
                    return

                _, _, LogPreprocessor, PromptTemplates, _ = safe_import_ai_diagnosis()
                preprocessor = LogPreprocessor()

                # 获取模块健康统计
                health_stats = preprocessor.get_module_health(self.main_app.log_entries)

                if not health_stats:
                    self.main_app.root.after(0, self.append_chat, "system", "未找到模块信息")
                    return

                # 格式化健康报告
                health_report = "=== 模块健康状况 ===\n\n"

                # 按健康分数排序
                sorted_modules = sorted(
                    health_stats.items(),
                    key=lambda x: x[1]['health_score']
                )

                for module, stats in sorted_modules:
                    score = stats['health_score']

                    # 健康状态emoji
                    if score >= 0.8:
                        emoji = "🟢"
                    elif score >= 0.6:
                        emoji = "🟡"
                    else:
                        emoji = "🔴"

                    health_report += f"{emoji} {module}:\n"
                    health_report += f"  健康分数: {score}\n"
                    health_report += f"  总日志: {stats['total']}\n"
                    health_report += f"  崩溃: {stats['crashes']}, 错误: {stats['errors']}, 警告: {stats['warnings']}\n\n"

                # 构建AI提示词
                prompt = f"""基于以下模块健康分析数据，提供详细的诊断报告：

{health_report}

请分析：
1. 整体健康状况评估
2. 高风险模块（健康分数<0.6）的重点问题
3. 中等风险模块（健康分数0.6-0.8）的改进建议
4. 模块间的关联性分析
5. 优先级修复建议
"""

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
                self.main_app.root.after(0, self.hide_stop_button)
                self.main_app.root.after(0, self.hide_progress)
                self.main_app.root.after(0, self.set_status, "就绪")

        threading.Thread(target=_analyze, daemon=True).start()

    def analyze_unhealthy_modules(self):
        """深度分析不健康的模块"""
        if not self.main_app.log_entries:
            messagebox.showwarning("警告", "请先加载日志文件")
            return

        if self.is_processing:
            messagebox.showinfo("提示", "AI正在处理中，请稍候")
            return

        self.is_processing = True
        self.stop_flag = False
        self.set_status("正在深度分析问题模块...")
        self.append_chat("user", "深度分析不健康的模块")
        self.main_app.root.after(0, self.show_stop_button)
        self.main_app.root.after(0, self.show_progress)

        def _analyze():
            try:
                if self.stop_flag:
                    return

                _, _, LogPreprocessor, PromptTemplates, _ = safe_import_ai_diagnosis()
                preprocessor = LogPreprocessor()

                # 获取不健康的模块（健康分数<0.7）
                unhealthy_modules = preprocessor.get_unhealthy_modules(
                    self.main_app.log_entries,
                    threshold=0.7
                )

                if not unhealthy_modules:
                    self.main_app.root.after(0, self.append_chat, "assistant",
                                            "🎉 太棒了！所有模块健康状况良好（健康分数≥0.7）")
                    return

                # 获取模块健康统计
                health_stats = preprocessor.get_module_health(self.main_app.log_entries)

                # 限制分析前3个最不健康的模块
                top_unhealthy = unhealthy_modules[:3]

                # 构建详细报告
                detailed_report = f"=== 发现 {len(unhealthy_modules)} 个不健康模块 ===\n\n"
                detailed_report += f"重点分析前 {len(top_unhealthy)} 个最严重的模块：\n\n"

                for module in top_unhealthy:
                    stats = health_stats[module]
                    detailed_report += f"## {module} (健康分数: {stats['health_score']})\n\n"

                    # 提取该模块的错误和崩溃日志
                    module_logs = preprocessor.extract_module_specific_logs(
                        self.main_app.log_entries,
                        module
                    )

                    # 提取错误和崩溃
                    error_logs = [e for e in module_logs if e.level == "ERROR"][:5]
                    crash_logs = [e for e in module_logs if preprocessor._is_crash_log(e)][:3]

                    if crash_logs:
                        detailed_report += f"### 崩溃日志 ({len(crash_logs)}条):\n"
                        for log in crash_logs:
                            detailed_report += f"- [{log.timestamp}] {log.content[:200]}...\n"
                        detailed_report += "\n"

                    if error_logs:
                        detailed_report += f"### 错误日志 (前5条):\n"
                        for log in error_logs:
                            detailed_report += f"- [{log.timestamp}] {log.content[:200]}...\n"
                        detailed_report += "\n"

                # 构建AI提示词
                prompt = f"""基于以下不健康模块的详细日志，提供深度诊断分析：

{detailed_report}

请针对每个问题模块提供：
1. 问题根本原因分析
2. 问题影响评估（严重性、影响范围）
3. 具体的修复建议和代码示例（如适用）
4. 预防措施和最佳实践
5. 修复优先级排序

请提供可执行的、具体的解决方案。
"""

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
                self.main_app.root.after(0, self.hide_stop_button)
                self.main_app.root.after(0, self.hide_progress)
                self.main_app.root.after(0, self.set_status, "就绪")

        threading.Thread(target=_analyze, daemon=True).start()

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
                _, AIConfig, LogPreprocessor, PromptTemplates, _ = safe_import_ai_diagnosis()
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

                    # 估算token数（粗略估计：中文1字=1token，英文4字符=1token）
                    estimated_tokens = len(prompt.replace(' ', '')) + len(prompt.split()) // 4
                else:
                    # 完整模式：使用Token优化器
                    optimizer = self.token_optimizer
                    if not optimizer:
                        self.main_app.root.after(0, self.append_chat, "system", "Token优化器初始化失败")
                        return

                    # 获取当前日志
                    current_logs = self.main_app.filtered_entries if hasattr(self.main_app, 'filtered_entries') and self.main_app.filtered_entries else self.main_app.log_entries

                    # 优化交互式问答提示词
                    optimized = optimizer.optimize_for_interactive_qa(
                        current_logs,
                        user_question=question
                    )

                    # 检查token预算
                    within_budget, message = optimizer.check_budget(optimized.estimated_tokens)
                    if not within_budget:
                        self.main_app.root.after(0, self.append_chat, "system", f"⚠️ {message}")
                        return

                    # 显示token使用情况（优化后）
                    if show_token_usage:
                        self.main_app.root.after(0, self.set_status, f"📊 {message} | 压缩比: {optimized.compression_ratio:.1%}")

                    # 使用优化后的提示词
                    prompt = optimized.prompt
                    estimated_tokens = optimized.estimated_tokens

                # 显示token使用情况（仅简化模式需要，完整模式已在上面显示）
                if (is_greeting or not has_logs) and show_token_usage:
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

    def show_custom_prompts(self):
        """显示自定义Prompt对话框"""
        try:
            # 尝试相对导入（在gui/modules/目录下运行时）
            from .custom_prompt_dialog import show_custom_prompt_dialog
        except ImportError:
            try:
                # 尝试从modules导入
                from custom_prompt_dialog import show_custom_prompt_dialog
            except ImportError:
                try:
                    from modules.custom_prompt_dialog import show_custom_prompt_dialog
                except ImportError:
                    # 最后尝试完整路径
                    import sys
                    import os
                    # 添加gui目录到路径
                    gui_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    if gui_dir not in sys.path:
                        sys.path.insert(0, gui_dir)
                    from modules.custom_prompt_dialog import show_custom_prompt_dialog

        show_custom_prompt_dialog(self.parent)

    def show_prompt_selector(self):
        """显示自定义Prompt快捷选择器"""
        try:
            from .custom_prompt_selector import create_prompt_selector
        except ImportError:
            try:
                from custom_prompt_selector import create_prompt_selector
            except ImportError:
                try:
                    from modules.custom_prompt_selector import create_prompt_selector
                except ImportError:
                    import sys
                    import os
                    gui_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    if gui_dir not in sys.path:
                        sys.path.insert(0, gui_dir)
                    from modules.custom_prompt_selector import create_prompt_selector

        # 创建选择器并显示
        selector = create_prompt_selector(self.parent, self.use_custom_prompt)
        selector._show_dropdown_menu()

    def use_custom_prompt(self, prompt_id: str, context_log: Optional[str] = None):
        """
        使用自定义Prompt进行分析

        Args:
            prompt_id: 自定义Prompt的ID
            context_log: 可选的日志上下文（如从右键菜单传入的选中日志）
        """
        if not self.main_app.log_entries and not context_log:
            messagebox.showwarning("警告", "请先加载日志文件")
            return

        if self.is_processing:
            messagebox.showinfo("提示", "AI正在处理中，请稍候")
            return

        # 获取自定义prompt管理器
        try:
            # 尝试相对导入
            from .ai_diagnosis.custom_prompt_manager import get_custom_prompt_manager
            manager = get_custom_prompt_manager()
        except ImportError:
            try:
                from ai_diagnosis.custom_prompt_manager import get_custom_prompt_manager
                manager = get_custom_prompt_manager()
            except ImportError:
                try:
                    # 添加路径后导入
                    import sys
                    import os
                    gui_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    if gui_dir not in sys.path:
                        sys.path.insert(0, gui_dir)
                    from modules.ai_diagnosis.custom_prompt_manager import get_custom_prompt_manager
                    manager = get_custom_prompt_manager()
                except ImportError as e:
                    messagebox.showerror("错误", f"无法加载自定义Prompt管理器: {e}")
                    return

        # 获取prompt
        custom_prompt = manager.get(prompt_id)
        if not custom_prompt:
            messagebox.showerror("错误", f"未找到ID为 {prompt_id} 的Prompt")
            return

        if not custom_prompt.enabled:
            result = messagebox.askyesno(
                "提示",
                f"Prompt '{custom_prompt.name}' 当前已禁用。\n是否继续使用？"
            )
            if not result:
                return

        # 检查需要的变量
        required_vars = custom_prompt.variables
        if not required_vars:
            # 没有变量，直接使用模板
            self._execute_custom_prompt(custom_prompt.name, custom_prompt.template)
            return

        # 弹出对话框收集变量值
        var_dialog = tk.Toplevel(self.parent)
        var_dialog.title(f"配置变量 - {custom_prompt.name}")
        var_dialog.geometry("500x400")
        var_dialog.transient(self.parent)
        # 不使用grab_set()以避免阻塞主窗口

        # 描述
        ttk.Label(
            var_dialog,
            text=f"{custom_prompt.description}\n\n请填写以下变量：",
            font=("Arial", 10),
            wraplength=450
        ).pack(pady=10, padx=10)

        # 变量输入框
        var_entries = {}
        input_frame = ttk.Frame(var_dialog)
        input_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        for i, var_name in enumerate(required_vars):
            # 变量名标签
            ttk.Label(input_frame, text=f"{var_name}:").grid(
                row=i, column=0, sticky=tk.W, pady=5, padx=(0, 10)
            )

            # 输入框（多行）
            text_widget = tk.Text(input_frame, height=3, width=40, wrap=tk.WORD)
            text_widget.grid(row=i, column=1, sticky=tk.EW, pady=5)

            # 如果有context_log且变量名是logs或log_content，自动填充
            if context_log and var_name.lower() in ['logs', 'log_content', 'log', 'context']:
                text_widget.insert('1.0', context_log)

            var_entries[var_name] = text_widget

        input_frame.columnconfigure(1, weight=1)

        # 底部按钮
        btn_frame = ttk.Frame(var_dialog)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        def on_submit():
            # 收集变量值
            values = {}
            for var_name, text_widget in var_entries.items():
                value = text_widget.get('1.0', tk.END).strip()
                if not value:
                    messagebox.showwarning(
                        "警告",
                        f"变量 '{var_name}' 不能为空"
                    )
                    return
                values[var_name] = value

            # 如果变量中有 'logs'，自动填充当前日志摘要
            if 'logs' in values and not values['logs']:
                # 生成日志摘要
                from gui.modules.ai_diagnosis.log_preprocessor import LogPreprocessor
                preprocessor = LogPreprocessor()
                log_summary = preprocessor.summarize_logs(
                    self.main_app.log_entries,
                    max_chars=5000
                )
                values['logs'] = log_summary

            # 格式化prompt
            try:
                formatted_prompt = custom_prompt.format(**values)
            except KeyError as e:
                messagebox.showerror("错误", f"变量格式化失败: {e}")
                return

            # 关闭对话框
            var_dialog.destroy()

            # 执行分析
            self._execute_custom_prompt(custom_prompt.name, formatted_prompt)

        ttk.Button(btn_frame, text="开始分析", command=on_submit, width=15).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="取消", command=var_dialog.destroy, width=15).pack(side=tk.RIGHT)

    def _execute_custom_prompt(self, prompt_name: str, formatted_prompt: str):
        """
        执行自定义Prompt分析

        Args:
            prompt_name: Prompt名称
            formatted_prompt: 格式化后的prompt内容
        """
        self.is_processing = True
        self.stop_flag = False
        self.set_status(f"正在使用 '{prompt_name}' 进行分析...")
        self.append_chat("user", f"使用自定义Prompt: {prompt_name}")
        self.main_app.root.after(0, self.show_stop_button)
        self.main_app.root.after(0, self.show_progress)

        def _analyze():
            try:
                if self.stop_flag:
                    return

                # 调用AI
                if not self.ai_client:
                    self.main_app.root.after(0, self.append_chat, "system", "AI服务初始化失败")
                    return

                response = self.ai_client.ask(formatted_prompt)

                # 显示结果
                self.main_app.root.after(0, self.append_chat, "assistant", response)

            except Exception as e:
                error_msg = f"分析失败: {str(e)}"
                self.main_app.root.after(0, self.append_chat, "system", error_msg)

            finally:
                self.is_processing = False
                self.main_app.root.after(0, self.hide_stop_button)
                self.main_app.root.after(0, self.hide_progress)
                self.main_app.root.after(0, self.set_status, "就绪")

        threading.Thread(target=_analyze, daemon=True).start()
