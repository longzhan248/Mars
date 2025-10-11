#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iOS沙盒浏览标签页模块（模块化重构版本）
使用子模块实现各项功能，保持代码简洁和职责分离
"""

import tkinter as tk
from tkinter import ttk

# 导入子模块
from .sandbox import (
    DeviceManager,
    AppManager,
    FileBrowser,
    FileOperations,
    FilePreview,
    SearchManager
)


class SandboxBrowserTab:
    """iOS沙盒浏览标签页"""

    def __init__(self, parent, main_app):
        """初始化沙盒浏览标签页

        Args:
            parent: 父容器
            main_app: 主应用程序实例
        """
        self.parent = parent
        self.main_app = main_app
        self.device_id = None
        self.current_app_id = None
        self.afc_client = None

        # 检查依赖
        self.has_dependency = self._check_dependency()

        # 创建UI
        self.create_widgets()

        # 初始化各个功能模块
        if self.has_dependency:
            self._init_modules()

    def _check_dependency(self):
        """检查是否安装了pymobiledevice3依赖"""
        try:
            from pymobiledevice3.lockdown import LockdownClient
            from pymobiledevice3.services.installation_proxy import InstallationProxyService
            from pymobiledevice3.services.afc import AfcService
            return True
        except ImportError:
            return False

    def _init_modules(self):
        """初始化各个功能模块"""
        self.device_mgr = DeviceManager(self)
        self.app_mgr = AppManager(self)
        self.file_browser = FileBrowser(self)
        self.file_ops = FileOperations(self)
        self.file_preview = FilePreview(self)
        self.searcher = SearchManager(self)

        # 刷新设备列表
        self.device_mgr.refresh_devices()

    def create_widgets(self):
        """创建iOS沙盒浏览标签页UI"""
        if not self.has_dependency:
            self.show_dependency_error()
            return

        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 顶部控制区域
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(top_frame, text="设备:").pack(side=tk.LEFT, padx=(0, 5))
        self.device_combo = ttk.Combobox(top_frame, state="readonly", width=30)
        self.device_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.device_combo.bind("<<ComboboxSelected>>", lambda e: self.device_mgr.on_device_selected(e))

        ttk.Button(top_frame, text="刷新设备",
                  command=lambda: self.device_mgr.refresh_devices()).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(top_frame, text="应用:").pack(side=tk.LEFT, padx=(0, 5))
        self.app_combo = ttk.Combobox(top_frame, state="readonly", width=40)
        self.app_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.app_combo.bind("<<ComboboxSelected>>", lambda e: self.app_mgr.on_app_selected(e))

        # 文件树区域
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)

        tree_frame = ttk.Frame(content_frame)
        tree_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        columns = ("size", "date", "path")
        self.tree = ttk.Treeview(tree_frame, columns=columns, yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.tree.yview)

        self.tree.heading("#0", text="名称")
        self.tree.heading("size", text="大小")
        self.tree.heading("date", text="修改日期")

        self.tree.column("#0", width=300)
        self.tree.column("size", width=100)
        self.tree.column("date", width=150)
        self.tree.column("path", width=0, stretch=False)

        self.tree.bind("<Double-Button-1>", lambda e: self.file_browser.on_item_double_click(e))
        self.tree.bind("<Button-3>", self.show_context_menu)
        self.tree.bind("<<TreeviewOpen>>", lambda e: self.file_browser.on_tree_expand(e))

        # 右键菜单
        self.context_menu = tk.Menu(self.tree, tearoff=0)
        self.context_menu.add_command(label="预览", command=lambda: self.file_preview.preview_selected())
        self.context_menu.add_command(label="导出", command=lambda: self.file_ops.export_selected())
        self.context_menu.add_command(label="打开", command=lambda: self.file_ops.open_selected())
        self.context_menu.add_separator()
        self.context_menu.add_command(label="删除", command=lambda: self.file_ops.delete_selected())
        self.context_menu.add_command(label="刷新", command=lambda: self.file_browser.refresh_current_dir())

        # 搜索框区域
        search_frame = ttk.Frame(main_frame)
        search_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Label(search_frame, text="搜索:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.search_entry.bind("<Return>", lambda e: self.searcher.search_files())

        self.search_type_var = tk.StringVar(value="文件名")
        search_type_combo = ttk.Combobox(search_frame, textvariable=self.search_type_var,
                                         values=["文件名", "文件内容", "所有"],
                                         state="readonly", width=10)
        search_type_combo.pack(side=tk.LEFT, padx=(0, 5))

        self.search_button = ttk.Button(search_frame, text="搜索",
                                        command=lambda: self.searcher.search_files())
        self.search_button.pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(search_frame, text="清除",
                  command=lambda: self.searcher.clear_search()).pack(side=tk.LEFT, padx=(0, 5))

        self.search_status = ttk.Label(search_frame, text="")
        self.search_status.pack(side=tk.LEFT, padx=(10, 0))

        # 操作按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(button_frame, text="预览",
                  command=lambda: self.file_preview.preview_selected()).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="导出选中",
                  command=lambda: self.file_ops.export_selected()).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="打开文件",
                  command=lambda: self._open_file_with_check()).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="删除",
                  command=lambda: self.file_ops.delete_selected()).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="刷新",
                  command=lambda: self.file_browser.refresh_current_dir()).pack(side=tk.LEFT)

        # 状态栏
        self.status_label = ttk.Label(main_frame, text="请先选择设备和应用", relief=tk.SUNKEN)
        self.status_label.pack(fill=tk.X, pady=(10, 0))

    def show_dependency_error(self):
        """显示依赖错误提示"""
        error_frame = ttk.Frame(self.parent)
        error_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        icon_label = ttk.Label(error_frame, text="⚠️", font=("Arial", 48))
        icon_label.pack(pady=(20, 10))

        title_label = ttk.Label(
            error_frame,
            text="iOS沙盒浏览功能需要安装额外依赖",
            font=("Arial", 14, "bold")
        )
        title_label.pack(pady=(0, 20))

        info_text = """
请运行以下命令安装必要的依赖:

pip install pymobiledevice3

或者使用项目根目录的requirements.txt:

pip install -r requirements.txt

安装完成后重启程序即可使用iOS沙盒浏览功能。
        """

        info_label = ttk.Label(error_frame, text=info_text, justify=tk.LEFT)
        info_label.pack(padx=20)

    def show_context_menu(self, event):
        """显示右键菜单，根据文件类型动态调整"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)

            # 检查是否为图片文件
            is_image = self._is_image_file(item)

            # 根据文件类型显示不同的菜单
            self._update_context_menu(is_image)

            self.context_menu.post(event.x_root, event.y_root)

    def _is_image_file(self, item_id):
        """检查是否为图片文件

        Args:
            item_id: 树形项ID

        Returns:
            bool: 是否为图片文件
        """
        import os
        tags = self.tree.item(item_id, "tags")

        # 目录不是图片
        if "directory" in tags:
            return False

        # 获取文件名
        name = self.tree.item(item_id, "text")
        # 移除图标
        name = name.replace("📁 ", "").replace("📄 ", "")

        # 检查文件扩展名
        file_ext = os.path.splitext(name)[1].lower()
        image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.heic', '.webp']

        return file_ext in image_extensions

    def _update_context_menu(self, is_image):
        """根据文件类型更新右键菜单

        Args:
            is_image: 是否为图片文件
        """
        # 清除现有菜单
        self.context_menu.delete(0, tk.END)

        # 添加通用选项
        self.context_menu.add_command(label="预览", command=lambda: self.file_preview.preview_selected())
        self.context_menu.add_command(label="导出", command=lambda: self.file_ops.export_selected())

        # 只有非图片文件才显示"打开"选项
        if not is_image:
            self.context_menu.add_command(label="打开", command=lambda: self.file_ops.open_selected())

        self.context_menu.add_separator()
        self.context_menu.add_command(label="删除", command=lambda: self.file_ops.delete_selected())
        self.context_menu.add_command(label="刷新", command=lambda: self.file_browser.refresh_current_dir())

    def _open_file_with_check(self):
        """打开文件前检查是否为图片文件"""
        from tkinter import messagebox

        item = self.tree.selection()
        if not item:
            messagebox.showwarning("提示", "请先选择要打开的文件")
            return

        item_id = item[0]

        # 检查是否为图片文件
        if self._is_image_file(item_id):
            messagebox.showinfo("提示",
                "图片文件无法使用\"打开\"功能\n\n"
                "建议使用以下方式查看图片:\n"
                "• 预览: 在程序内查看\n"
                "• 导出: 保存到本地后查看")
            return

        # 非图片文件，正常打开
        self.file_ops.open_selected()

    def update_status(self, message):
        """更新状态栏"""
        self.status_label.config(text=message)
