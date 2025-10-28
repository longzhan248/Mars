#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI诊断设置对话框
配置AI服务、模型、隐私等选项
"""

import tkinter as tk
from tkinter import messagebox, ttk


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

        # Claude Code说明
        info_label = ttk.Label(
            service_frame,
            text="✓ 使用 Claude Code (无需API Key)\n"
                 "✓ 完全免费\n"
                 "✓ 利用现有Claude Code连接\n"
                 "• 需要Claude Code正在运行",
            font=("Arial", 10),
            foreground="#2E7D32",
            justify=tk.LEFT
        )
        info_label.pack(fill=tk.X, pady=5)

        # Claude命令路径配置（可选）
        path_frame = ttk.Frame(service_frame)
        path_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Label(
            path_frame,
            text="Claude命令路径（可选）:",
            font=("Arial", 9)
        ).pack(side=tk.LEFT)

        self.claude_path_var = tk.StringVar(value=self.config.get('claude_path', ''))
        claude_path_entry = ttk.Entry(path_frame, textvariable=self.claude_path_var, width=35)
        claude_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5))

        ttk.Button(
            path_frame,
            text="浏览",
            width=6,
            command=self.browse_claude_path
        ).pack(side=tk.LEFT)

        # 路径说明
        path_info = ttk.Label(
            service_frame,
            text="留空则自动检测。如果打包后的app无法连接Claude Code，请手动指定路径",
            font=("Arial", 8),
            foreground="#666666"
        )
        path_info.pack(fill=tk.X, pady=(2, 0))

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


    def browse_claude_path(self):
        """浏览选择claude命令路径"""
        from tkinter import filedialog

        file_path = filedialog.askopenfilename(
            title="选择claude命令",
            initialdir=os.path.expanduser("~"),
            filetypes=[
                ("可执行文件", "*"),
                ("所有文件", "*.*")
            ]
        )

        if file_path:
            self.claude_path_var.set(file_path)

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


    def test_connection(self):
        """测试AI连接"""
        AIClientFactory, _ = safe_import_ai_diagnosis()

        try:
            # 创建Claude Code客户端
            client = AIClientFactory.create("ClaudeCode")

            # 简单测试
            response = client.ask("你好")

            messagebox.showinfo(
                "测试成功",
                f"✓ Claude Code连接成功\n\n"
                f"响应: {response[:100]}..."
            )

        except Exception as e:
            messagebox.showerror(
                "测试失败",
                f"无法连接到Claude Code:\n\n{str(e)}\n\n"
                f"请确保Claude Code正在运行。"
            )

    def reset_to_default(self):
        """重置为默认配置"""
        if messagebox.askyesno("确认", "确定要重置为默认配置吗?"):
            _, AIConfig = safe_import_ai_diagnosis()

            default_config = AIConfig.DEFAULT_CONFIG

            self.auto_summary_var.set(default_config['auto_summary'])
            self.claude_path_var.set(default_config['claude_path'])
            self.privacy_filter_var.set(default_config['privacy_filter'])
            self.max_tokens_var.set(default_config['max_tokens'])
            self.timeout_var.set(default_config['timeout'])
            self.context_size_var.set(default_config['context_size'])

    def save_settings(self):
        """保存设置"""
        # 获取项目目录列表
        project_dirs = list(self.project_listbox.get(0, tk.END))

        # 构建配置（固定使用Claude Code）
        new_config = {
            'ai_service': 'ClaudeCode',
            'claude_path': self.claude_path_var.get().strip(),
            'auto_detect': False,
            'auto_summary': self.auto_summary_var.get(),
            'privacy_filter': self.privacy_filter_var.get(),
            'max_tokens': self.max_tokens_var.get(),
            'timeout': self.timeout_var.get(),
            'context_size': self.context_size_var.get(),
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
