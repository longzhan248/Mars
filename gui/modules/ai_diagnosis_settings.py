#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI诊断设置对话框
配置AI服务、模型、隐私等选项
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os


def safe_import_ai_diagnosis():
    """安全导入AI诊断模块"""
    try:
        from ai_diagnosis import AIClientFactory, AIConfig
        return AIClientFactory, AIConfig
    except ImportError:
        try:
            from modules.ai_diagnosis import AIClientFactory, AIConfig
            return AIClientFactory, AIConfig
        except ImportError:
            from gui.modules.ai_diagnosis import AIClientFactory, AIConfig
            return AIClientFactory, AIConfig


class AISettingsDialog:
    """AI设置对话框"""

    def __init__(self, parent, main_app):
        """
        初始化设置对话框

        Args:
            parent: 父窗口
            main_app: 主应用程序实例
        """
        self.parent = parent
        self.main_app = main_app
        self.settings_changed = False

        # 加载当前配置
        _, AIConfig = safe_import_ai_diagnosis()
        self.config = AIConfig.load()

        # 创建对话框
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("AI设置")
        self.dialog.geometry("580x900")  # 增加高度以显示所有内容
        self.dialog.resizable(True, True)  # 允许调整大小

        # 模态对话框
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.create_widgets()

        # 居中显示
        self.center_window()

        # 等待对话框关闭
        self.dialog.wait_window()

    def center_window(self):
        """窗口居中"""
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f'{width}x{height}+{x}+{y}')

    def create_widgets(self):
        """创建UI组件"""
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ========== AI服务配置 ==========
        service_frame = ttk.LabelFrame(main_frame, text="AI服务配置", padding="10")
        service_frame.pack(fill=tk.X, pady=(0, 10))

        # 自动检测
        self.auto_detect_var = tk.BooleanVar(value=self.config.get('auto_detect', True))
        auto_detect_check = ttk.Checkbutton(
            service_frame,
            text="自动检测最佳服务（推荐）",
            variable=self.auto_detect_var,
            command=self.on_auto_detect_changed
        )
        auto_detect_check.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=5)

        # 服务类型
        ttk.Label(service_frame, text="AI服务:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.service_var = tk.StringVar(value=self.config.get('ai_service', 'ClaudeCode'))
        service_combo = ttk.Combobox(
            service_frame,
            textvariable=self.service_var,
            values=['ClaudeCode', 'Claude', 'OpenAI', 'Ollama'],
            state='readonly',
            width=30
        )
        service_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 0))
        service_combo.bind('<<ComboboxSelected>>', self.on_service_changed)

        # API Key
        ttk.Label(service_frame, text="API Key:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.api_key_var = tk.StringVar(value=self.config.get('api_key', ''))
        self.api_key_entry = ttk.Entry(service_frame, textvariable=self.api_key_var, width=32, show="*")
        self.api_key_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 0))

        # 显示/隐藏API Key按钮
        self.show_key_btn = ttk.Button(
            service_frame,
            text="👁",
            width=3,
            command=self.toggle_api_key_visibility
        )
        self.show_key_btn.grid(row=2, column=2, padx=5)

        # 模型
        ttk.Label(service_frame, text="模型:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.model_var = tk.StringVar(value=self.config.get('model', 'claude-3-5-sonnet-20241022'))
        self.model_entry = ttk.Entry(service_frame, textvariable=self.model_var, width=32)
        self.model_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 0))

        service_frame.columnconfigure(1, weight=1)

        # 服务说明
        info_text = tk.Text(service_frame, height=6, width=50, wrap=tk.WORD, font=("Arial", 9))
        info_text.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        info_text.insert('1.0', self.get_service_info())
        info_text.config(state=tk.DISABLED, background="#f0f0f0")

        # ========== 功能配置 ==========
        feature_frame = ttk.LabelFrame(main_frame, text="功能配置", padding="10")
        feature_frame.pack(fill=tk.X, pady=(0, 10))

        # 自动摘要
        self.auto_summary_var = tk.BooleanVar(value=self.config.get('auto_summary', False))
        ttk.Checkbutton(
            feature_frame,
            text="加载日志后自动生成摘要",
            variable=self.auto_summary_var
        ).grid(row=0, column=0, sticky=tk.W, pady=3)

        # 隐私过滤
        self.privacy_filter_var = tk.BooleanVar(value=self.config.get('privacy_filter', True))
        ttk.Checkbutton(
            feature_frame,
            text="启用隐私信息过滤（推荐）",
            variable=self.privacy_filter_var
        ).grid(row=1, column=0, sticky=tk.W, pady=3)

        # Max Tokens
        ttk.Label(feature_frame, text="最大Token数:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.max_tokens_var = tk.IntVar(value=self.config.get('max_tokens', 10000))
        max_tokens_spinbox = ttk.Spinbox(
            feature_frame,
            from_=1000,
            to=100000,
            increment=1000,
            textvariable=self.max_tokens_var,
            width=10
        )
        max_tokens_spinbox.grid(row=2, column=1, sticky=tk.W, pady=5, padx=(5, 0))

        # Timeout
        ttk.Label(feature_frame, text="超时时间(秒):").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.timeout_var = tk.IntVar(value=self.config.get('timeout', 60))
        timeout_spinbox = ttk.Spinbox(
            feature_frame,
            from_=10,
            to=300,
            increment=10,
            textvariable=self.timeout_var,
            width=10
        )
        timeout_spinbox.grid(row=3, column=1, sticky=tk.W, pady=5, padx=(5, 0))

        # 上下文大小（新增）
        ttk.Label(feature_frame, text="上下文大小:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.context_size_var = tk.StringVar(value=self.config.get('context_size', '标准'))
        context_combo = ttk.Combobox(
            feature_frame,
            textvariable=self.context_size_var,
            values=['简化', '标准', '详细'],
            state='readonly',
            width=10
        )
        context_combo.grid(row=4, column=1, sticky=tk.W, pady=5, padx=(5, 0))

        # 上下文大小说明
        context_info_label = ttk.Label(
            feature_frame,
            text="简化=快速响应/少token | 标准=平衡 | 详细=完整上下文/多token",
            font=("Arial", 8),
            foreground="#666666"
        )
        context_info_label.grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))

        feature_frame.columnconfigure(0, weight=1)

        # ========== 项目代码配置 ==========
        project_frame = ttk.LabelFrame(main_frame, text="项目代码配置", padding="10")
        project_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(
            project_frame,
            text="添加项目源码目录，AI可分析代码结构进行更精准的诊断",
            font=("Arial", 9),
            foreground="#666666"
        ).pack(fill=tk.X, pady=(0, 5))

        # 项目目录列表
        project_list_frame = ttk.Frame(project_frame)
        project_list_frame.pack(fill=tk.BOTH, expand=True)

        # 创建Listbox显示已添加的目录
        self.project_listbox = tk.Listbox(project_list_frame, height=4)
        self.project_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 滚动条
        project_scrollbar = ttk.Scrollbar(project_list_frame, orient=tk.VERTICAL, command=self.project_listbox.yview)
        project_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.project_listbox.config(yscrollcommand=project_scrollbar.set)

        # 加载已配置的项目目录
        project_dirs = self.config.get('project_dirs', [])
        for project_dir in project_dirs:
            self.project_listbox.insert(tk.END, project_dir)

        # 按钮区域
        project_btn_frame = ttk.Frame(project_frame)
        project_btn_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Button(
            project_btn_frame,
            text="➕ 添加目录",
            command=self.add_project_dir
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            project_btn_frame,
            text="➖ 删除选中",
            command=self.remove_project_dir
        ).pack(side=tk.LEFT, padx=2)

        # ========== 环境变量提示 ==========
        env_frame = ttk.LabelFrame(main_frame, text="环境变量（可选）", padding="10")
        env_frame.pack(fill=tk.X, pady=(0, 10))

        env_text = (
            "您可以通过环境变量设置API Key:\n"
            "• Claude: export ANTHROPIC_API_KEY=sk-xxx\n"
            "• OpenAI: export OPENAI_API_KEY=sk-xxx\n\n"
            "环境变量优先级高于配置文件。"
        )

        # 使用Text组件代替Label，支持自动换行
        env_text_widget = tk.Text(
            env_frame,
            height=5,
            width=50,
            wrap=tk.WORD,
            font=("Arial", 9),
            background="#f0f0f0",
            foreground="#666666",
            relief=tk.FLAT,
            borderwidth=0
        )
        env_text_widget.insert('1.0', env_text)
        env_text_widget.config(state=tk.DISABLED)
        env_text_widget.pack(fill=tk.X)

        # ========== 按钮区域 ==========
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(
            btn_frame,
            text="测试连接",
            command=self.test_connection
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="重置为默认",
            command=self.reset_to_default
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="取消",
            command=self.dialog.destroy
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            btn_frame,
            text="保存",
            command=self.save_settings
        ).pack(side=tk.RIGHT, padx=5)

        # 初始化状态
        self.on_auto_detect_changed()
        self.on_service_changed()

    def on_auto_detect_changed(self):
        """自动检测选项改变"""
        auto_detect = self.auto_detect_var.get()
        # 如果启用自动检测,禁用手动选择
        state = 'disabled' if auto_detect else 'readonly'
        # 注意: ttk.Combobox不能直接用config设置state,需要重新配置

    def on_service_changed(self, event=None):
        """服务类型改变"""
        service = self.service_var.get()

        # 根据服务类型启用/禁用API Key输入
        if service in ['Claude', 'OpenAI']:
            self.api_key_entry.config(state='normal')
            self.show_key_btn.config(state='normal')
        else:
            self.api_key_entry.config(state='disabled')
            self.show_key_btn.config(state='disabled')

        # 根据服务类型提供默认模型
        default_models = {
            'Claude': 'claude-3-5-sonnet-20241022',
            'OpenAI': 'gpt-4',
            'Ollama': 'llama3',
            'ClaudeCode': 'claude-3-5-sonnet-20241022'
        }
        if not self.model_var.get():
            self.model_var.set(default_models.get(service, ''))

    def toggle_api_key_visibility(self):
        """切换API Key显示/隐藏"""
        current_show = self.api_key_entry.cget('show')
        if current_show == '*':
            self.api_key_entry.config(show='')
            self.show_key_btn.config(text='🙈')
        else:
            self.api_key_entry.config(show='*')
            self.show_key_btn.config(text='👁')

    def add_project_dir(self):
        """添加项目目录"""
        from tkinter import filedialog

        dir_path = filedialog.askdirectory(
            title="选择项目源码目录",
            mustexist=True
        )

        if dir_path:
            # 检查是否已存在
            existing_dirs = self.project_listbox.get(0, tk.END)
            if dir_path not in existing_dirs:
                self.project_listbox.insert(tk.END, dir_path)
            else:
                messagebox.showinfo("提示", "该目录已添加")

    def remove_project_dir(self):
        """删除选中的项目目录"""
        selection = self.project_listbox.curselection()
        if selection:
            self.project_listbox.delete(selection[0])
        else:
            messagebox.showinfo("提示", "请先选择要删除的目录")

    def get_service_info(self) -> str:
        """获取服务说明文本"""
        service = self.service_var.get()

        info_map = {
            'ClaudeCode': (
                "✓ 推荐使用\n"
                "✓ 无需API Key\n"
                "✓ 利用现有Claude Code连接\n"
                "✓ 完全免费\n"
                "• 需要Claude Code正在运行"
            ),
            'Claude': (
                "• 需要Anthropic API Key\n"
                "• 支持Claude 3.5 Sonnet等模型\n"
                "• 按Token计费\n"
                "• 响应速度快，质量高"
            ),
            'OpenAI': (
                "• 需要OpenAI API Key\n"
                "• 支持GPT-4/GPT-3.5等模型\n"
                "• 按Token计费\n"
                "• 广泛使用，功能强大"
            ),
            'Ollama': (
                "✓ 完全免费\n"
                "✓ 本地运行，数据不出机器\n"
                "• 需要先安装Ollama\n"
                "• 命令: brew install ollama\n"
                "• 启动: ollama serve"
            )
        }

        return info_map.get(service, "")

    def test_connection(self):
        """测试AI连接"""
        AIClientFactory, _ = safe_import_ai_diagnosis()

        service = self.service_var.get()
        api_key = self.api_key_var.get()
        model = self.model_var.get()

        try:
            # 创建客户端
            if self.auto_detect_var.get():
                client = AIClientFactory.auto_detect()
                service_name = "自动检测"
            else:
                client = AIClientFactory.create(service, api_key, model)
                service_name = service

            # 简单测试
            response = client.ask("你好")

            messagebox.showinfo(
                "测试成功",
                f"✓ {service_name}连接成功\n\n"
                f"响应: {response[:100]}..."
            )

        except Exception as e:
            messagebox.showerror(
                "测试失败",
                f"无法连接到AI服务:\n\n{str(e)}"
            )

    def reset_to_default(self):
        """重置为默认配置"""
        if messagebox.askyesno("确认", "确定要重置为默认配置吗?"):
            _, AIConfig = safe_import_ai_diagnosis()

            default_config = AIConfig.DEFAULT_CONFIG

            self.auto_detect_var.set(default_config['auto_detect'])
            self.service_var.set(default_config['ai_service'])
            self.api_key_var.set(default_config['api_key'])
            self.model_var.set(default_config['model'])
            self.auto_summary_var.set(default_config['auto_summary'])
            self.privacy_filter_var.set(default_config['privacy_filter'])
            self.max_tokens_var.set(default_config['max_tokens'])
            self.timeout_var.set(default_config['timeout'])

            self.on_service_changed()

    def save_settings(self):
        """保存设置"""
        # 验证输入
        if not self.auto_detect_var.get():
            service = self.service_var.get()
            if service in ['Claude', 'OpenAI']:
                if not self.api_key_var.get():
                    messagebox.showwarning(
                        "警告",
                        f"{service}服务需要API Key"
                    )
                    return

        # 获取项目目录列表
        project_dirs = list(self.project_listbox.get(0, tk.END))

        # 构建配置
        new_config = {
            'ai_service': self.service_var.get(),
            'api_key': self.api_key_var.get(),
            'model': self.model_var.get(),
            'auto_detect': self.auto_detect_var.get(),
            'auto_summary': self.auto_summary_var.get(),
            'privacy_filter': self.privacy_filter_var.get(),
            'max_tokens': self.max_tokens_var.get(),
            'timeout': self.timeout_var.get(),
            'context_size': self.context_size_var.get(),  # 新增
            'project_dirs': project_dirs
        }

        # 保存配置
        _, AIConfig = safe_import_ai_diagnosis()

        if AIConfig.save(new_config):
            self.settings_changed = True
            messagebox.showinfo("成功", "设置已保存")
            self.dialog.destroy()
        else:
            messagebox.showerror("错误", "保存配置失败")
