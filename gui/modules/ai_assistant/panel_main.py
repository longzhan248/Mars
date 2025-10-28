#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI助手面板主控制器
为Mars日志分析器提供AI辅助分析功能
"""

import threading
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk
from typing import Optional


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
    """AI助手面板主控制器"""

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

        # UI组件（在create_widgets中初始化）
        self.frame = None
        self.toolbar = None
        self.chat_panel = None
        self.navigation = None
        self.prompt_panel = None
        self.status_var = None
        self.stop_button = None
        self.progress = None

        # 创建UI
        self.create_widgets()

    @property
    def ai_client(self):
        """延迟初始化AI客户端（仅使用Claude Code）"""
        if self._ai_client is None:
            try:
                AIClientFactory, AIConfig, _, _, _ = safe_import_ai_diagnosis()

                # 固定使用Claude Code
                self._ai_client = AIClientFactory.create(service='ClaudeCode')
            except Exception as e:
                messagebox.showerror(
                    "Claude Code初始化失败",
                    f"无法连接到Claude Code:\n{str(e)}\n\n"
                    f"请确保Claude Code正在运行。"
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

    def create_widgets(self):
        """创建并组装UI组件"""
        from .ui.toolbar_panel import ToolbarPanel
        from .ui.chat_panel import ChatPanel
        from .ui.navigation_helper import NavigationHelper
        from .ui.prompt_panel import PromptPanel

        self.frame = ttk.Frame(self.parent)
        self.frame.pack(fill=tk.BOTH, expand=True)

        # 先创建辅助组件（不依赖UI的）
        self.navigation = NavigationHelper(self)
        self.prompt_panel = PromptPanel(self)

        # 创建聊天面板
        self.chat_panel = ChatPanel(self.frame, self)
        self.chat_panel.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        # 最后创建工具栏（依赖chat_panel和navigation）
        self.toolbar = ToolbarPanel(self.frame, self)
        self.toolbar.pack(fill=tk.X, before=self.chat_panel)

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

        # 进度条（初始隐藏）
        self.progress = ttk.Progressbar(
            self.frame,
            mode='indeterminate',
            length=200
        )

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
        self.chat_panel.append_chat("system", "用户已取消操作")

    def show_prompt_selector(self):
        """显示Prompt选择器（委托给PromptPanel）"""
        self.prompt_panel.show_selector()

    def use_custom_prompt(self, prompt_id: str, context_log: Optional[str] = None):
        """使用自定义Prompt（委托给PromptPanel）"""
        self.prompt_panel.use_prompt(prompt_id, context_log)

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

    def ask_question(self):
        """自由提问"""
        question = self.chat_panel.question_var.get().strip()
        if not question:
            return

        # 清空输入框
        self.chat_panel.question_var.set("")

        if self.is_processing:
            messagebox.showinfo("提示", "AI正在处理中，请稍候")
            return

        self.is_processing = True
        self.stop_flag = False
        self.set_status("正在思考...")
        self.chat_panel.append_chat("user", question)
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
                        self.main_app.root.after(0, self.chat_panel.append_chat, "system", "Token优化器初始化失败")
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
                        self.main_app.root.after(0, self.chat_panel.append_chat, "system", f"⚠️ {message}")
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
                    self.main_app.root.after(0, self.chat_panel.append_chat, "system", "AI服务初始化失败")
                    return

                response = self.ai_client.ask(prompt)

                # 估算响应token数
                response_tokens = len(response.replace(' ', '')) + len(response.split()) // 4
                total_tokens = estimated_tokens + response_tokens

                # 累加Token统计
                self.total_input_tokens += estimated_tokens
                self.total_output_tokens += response_tokens

                # 显示结果
                self.main_app.root.after(0, self.chat_panel.append_chat, "assistant", response)

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
                self.main_app.root.after(0, self.chat_panel.append_chat, "system", error_msg)

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
