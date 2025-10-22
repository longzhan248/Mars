"""
进度显示面板UI组件

提供混淆执行过程的进度显示和日志输出
"""

import os
import tkinter as tk
from tkinter import ttk, scrolledtext


class ProgressPanel(ttk.Frame):
    """进度显示面板组件"""

    def __init__(self, parent, tab):
        """
        初始化进度面板

        Args:
            parent: 父容器
            tab: ObfuscationTab实例（用于回调）
        """
        super().__init__(parent)
        self.tab = tab

        # 创建UI
        self.create_widgets()

    def create_widgets(self):
        """创建进度显示UI"""
        # 进度条区域
        self.create_progress_section()

        # 日志输出区域
        self.create_log_section()

    def create_progress_section(self):
        """创建进度条区域"""
        progress_frame = ttk.LabelFrame(self, text="📊 执行进度", padding=8)
        progress_frame.pack(fill=tk.X, pady=(0, 5))

        # 进度条和百分比
        progress_inner = ttk.Frame(progress_frame)
        progress_inner.pack(fill=tk.X)

        self.tab.progress_var = tk.DoubleVar()
        self.tab.progress_bar = ttk.Progressbar(
            progress_inner,
            variable=self.tab.progress_var,
            maximum=100,
            mode='determinate'
        )
        self.tab.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

        self.tab.progress_label = ttk.Label(
            progress_inner,
            text="0%",
            font=("Arial", 10, "bold"),
            width=5
        )
        self.tab.progress_label.pack(side=tk.LEFT)

        # 状态文本
        self.tab.status_label = ttk.Label(
            progress_frame,
            text="就绪",
            font=("Arial", 8),
            foreground="gray"
        )
        self.tab.status_label.pack(anchor=tk.W, pady=(3, 0))

    def create_log_section(self):
        """创建日志输出区域"""
        log_label_frame = ttk.LabelFrame(self, text="📝 执行日志", padding=5)
        log_label_frame.pack(fill=tk.BOTH, expand=True)

        self.tab.log_text = scrolledtext.ScrolledText(
            log_label_frame,
            height=12,
            wrap=tk.WORD,
            font=("Consolas", 9) if os.name == 'nt' else ("Monaco", 9)
        )
        self.tab.log_text.pack(fill=tk.BOTH, expand=True)

        # 配置日志文本标签（用于颜色高亮）
        self.tab.log_text.tag_config("success", foreground="#28a745")
        self.tab.log_text.tag_config("error", foreground="#dc3545")
        self.tab.log_text.tag_config("warning", foreground="#ffc107")
        self.tab.log_text.tag_config("info", foreground="#17a2b8")
        self.tab.log_text.tag_config("header", foreground="#6c757d",
                                     font=("Consolas", 9, "bold") if os.name == 'nt' else ("Monaco", 9, "bold"))

    def update_progress(self, progress, message=""):
        """
        更新进度显示

        Args:
            progress: 进度值(0-100)
            message: 状态消息
        """
        self.tab.progress_var.set(progress)
        self.tab.progress_label.config(text=f"{int(progress)}%")
        if message:
            self.tab.status_label.config(text=message)

    def log(self, message, tag=None):
        """
        添加日志消息

        Args:
            message: 日志消息
            tag: 文本标签（用于颜色高亮）
        """
        self.tab.log_text.insert(tk.END, message + "\n", tag)
        self.tab.log_text.see(tk.END)

    def clear(self):
        """清空进度和日志"""
        self.tab.progress_var.set(0)
        self.tab.progress_label.config(text="0%")
        self.tab.status_label.config(text="就绪")
        self.tab.log_text.delete('1.0', tk.END)
