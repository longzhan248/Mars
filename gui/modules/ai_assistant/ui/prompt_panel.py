"""
Prompt管理面板
提供自定义Prompt的选择、配置和执行功能
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional
import os
import sys
import threading


class PromptPanel:
    """Prompt管理面板"""

    def __init__(self, panel):
        self.panel = panel
        self.prompt_templates = None  # 延迟初始化

    def show_selector(self):
        """显示自定义Prompt快捷选择器"""
        try:
            from ..custom_prompt_selector import create_prompt_selector
        except ImportError:
            try:
                from custom_prompt_selector import create_prompt_selector
            except ImportError:
                try:
                    from modules.custom_prompt_selector import create_prompt_selector
                except ImportError:
                    gui_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                    if gui_dir not in sys.path:
                        sys.path.insert(0, gui_dir)
                    from modules.custom_prompt_selector import create_prompt_selector

        # 创建选择器并显示
        selector = create_prompt_selector(self.panel.parent, self.use_prompt)
        selector._show_dropdown_menu()

    def use_prompt(self, prompt_id: str, context_log: Optional[str] = None):
        """
        使用自定义Prompt进行分析

        Args:
            prompt_id: 自定义Prompt的ID
            context_log: 可选的日志上下文（如从右键菜单传入的选中日志）
        """
        if not self.panel.main_app.log_entries and not context_log:
            messagebox.showwarning("警告", "请先加载日志文件")
            return

        if self.panel.is_processing:
            messagebox.showinfo("提示", "AI正在处理中，请稍候")
            return

        # 获取自定义prompt管理器
        try:
            # 尝试相对导入
            from ..ai_diagnosis.custom_prompt_manager import get_custom_prompt_manager
            manager = get_custom_prompt_manager()
        except ImportError:
            try:
                from ai_diagnosis.custom_prompt_manager import get_custom_prompt_manager
                manager = get_custom_prompt_manager()
            except ImportError:
                try:
                    # 添加路径后导入
                    gui_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                    if gui_dir not in sys.path:
                        sys.path.insert(0, gui_dir)
                    from modules.ai_diagnosis.custom_prompt_manager import (
                        get_custom_prompt_manager,
                    )
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
            self._execute_prompt(custom_prompt.name, custom_prompt.template)
            return

        # 弹出对话框收集变量值
        var_dialog = tk.Toplevel(self.panel.parent)
        var_dialog.title(f"配置变量 - {custom_prompt.name}")
        var_dialog.geometry("500x400")
        var_dialog.transient(self.panel.parent)
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
            """提交自定义Prompt变量配置"""
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
                try:
                    from ...ai_diagnosis.log_preprocessor import LogPreprocessor
                    preprocessor = LogPreprocessor()
                    log_summary = preprocessor.summarize_logs(
                        self.panel.main_app.log_entries,
                        max_chars=5000
                    )
                    values['logs'] = log_summary
                except ImportError:
                    pass

            # 格式化prompt
            try:
                formatted_prompt = custom_prompt.format(**values)
            except KeyError as e:
                messagebox.showerror("错误", f"变量格式化失败: {e}")
                return

            # 关闭对话框
            var_dialog.destroy()

            # 执行分析
            self._execute_prompt(custom_prompt.name, formatted_prompt)

        ttk.Button(btn_frame, text="开始分析", command=on_submit, width=15).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="取消", command=var_dialog.destroy, width=15).pack(side=tk.RIGHT)

    def _execute_prompt(self, prompt_name: str, formatted_prompt: str):
        """
        执行自定义Prompt分析

        Args:
            prompt_name: Prompt名称
            formatted_prompt: 格式化后的prompt内容
        """
        self.panel.is_processing = True
        self.panel.stop_flag = False
        self.panel.set_status(f"正在使用 '{prompt_name}' 进行分析...")
        self.panel.chat_panel.append_chat("user", f"使用自定义Prompt: {prompt_name}")
        self.panel.main_app.root.after(0, self.panel.show_stop_button)
        self.panel.main_app.root.after(0, self.panel.show_progress)

        def _analyze():
            try:
                if self.panel.stop_flag:
                    return

                # 调用AI
                if not self.panel.ai_client:
                    self.panel.main_app.root.after(0, self.panel.chat_panel.append_chat, "system", "AI服务初始化失败")
                    return

                response = self.panel.ai_client.ask(formatted_prompt)

                # 显示结果
                self.panel.main_app.root.after(0, self.panel.chat_panel.append_chat, "assistant", response)

            except Exception as e:
                error_msg = f"分析失败: {str(e)}"
                self.panel.main_app.root.after(0, self.panel.chat_panel.append_chat, "system", error_msg)

            finally:
                self.panel.is_processing = False
                self.panel.main_app.root.after(0, self.panel.hide_stop_button)
                self.panel.main_app.root.after(0, self.panel.hide_progress)
                self.panel.main_app.root.after(0, self.panel.set_status, "就绪")

        threading.Thread(target=_analyze, daemon=True).start()
