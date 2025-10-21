#!/usr/bin/env python3
"""
dSYM文件分析标签页（重构版）
用于解析iOS崩溃日志的符号化，根据错误地址进行代码定位
"""

import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

# 导入模块化组件
try:
    # 相对导入（作为包导入时）
    from .dsym import DSYMFileManager, DSYMSymbolizer, DSYMUUIDParser
except ImportError:
    # 绝对导入（直接导入时）
    from dsym import DSYMFileManager, DSYMSymbolizer, DSYMUUIDParser

class DSYMTab:
    def __init__(self, parent):
        self.parent = parent
        self.frame = ttk.Frame(parent)

        # 数据存储
        self.selected_archive = None
        self.selected_uuid = None
        self.uuid_infos = []

        # 模块化组件
        self.file_manager = DSYMFileManager()
        self.uuid_parser = DSYMUUIDParser()
        self.symbolizer = DSYMSymbolizer()

        self.setup_ui()
        self.load_local_archives()

    def setup_ui(self):
        """设置UI界面"""
        # 主框架
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 左侧：文件列表区域
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 文件列表标题
        ttk.Label(left_frame, text="Archive/dSYM 文件列表:", font=('', 10, 'bold')).pack(anchor=tk.W)

        # 文件列表框架
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 10))

        # 文件列表
        self.file_listbox = tk.Listbox(list_frame, height=10)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.file_listbox.bind('<<ListboxSelect>>', self.on_file_select)

        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.file_listbox.yview)

        # 按钮区域
        button_frame = ttk.Frame(left_frame)
        button_frame.pack(fill=tk.X)

        ttk.Button(button_frame, text="加载文件", command=self.load_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="刷新列表", command=self.load_local_archives).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="导出IPA", command=self.export_ipa).pack(side=tk.LEFT, padx=2)

        # 分隔符
        ttk.Separator(main_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        # 右侧：分析区域
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # UUID选择区域
        uuid_frame = ttk.LabelFrame(right_frame, text="选择架构/UUID", padding=10)
        uuid_frame.pack(fill=tk.X, pady=(0, 10))

        self.uuid_var = tk.StringVar()
        self.uuid_buttons_frame = ttk.Frame(uuid_frame)
        self.uuid_buttons_frame.pack(fill=tk.X)

        # UUID信息显示
        info_frame = ttk.Frame(uuid_frame)
        info_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Label(info_frame, text="UUID:").grid(row=0, column=0, sticky=tk.W)
        self.uuid_label = ttk.Label(info_frame, text="", foreground="blue")
        self.uuid_label.grid(row=0, column=1, sticky=tk.W, padx=(5, 0))

        ttk.Label(info_frame, text="默认基址:").grid(row=1, column=0, sticky=tk.W)
        self.slide_address_label = ttk.Label(info_frame, text="")
        self.slide_address_label.grid(row=1, column=1, sticky=tk.W, padx=(5, 0))

        # 分析参数区域
        param_frame = ttk.LabelFrame(right_frame, text="符号化参数", padding=10)
        param_frame.pack(fill=tk.X, pady=(0, 10))

        # 基址输入
        ttk.Label(param_frame, text="基址 (Slide Address):").grid(row=0, column=0, sticky=tk.W)
        self.slide_address_entry = ttk.Entry(param_frame, width=30)
        self.slide_address_entry.grid(row=0, column=1, sticky=tk.W+tk.E, padx=(5, 0))
        self.slide_address_entry.insert(0, "0x104000000")  # 默认值

        # 错误地址输入
        ttk.Label(param_frame, text="错误内存地址:").grid(row=1, column=0, sticky=tk.W)
        self.error_address_entry = ttk.Entry(param_frame, width=30)
        self.error_address_entry.grid(row=1, column=1, sticky=tk.W+tk.E, padx=(5, 0))

        # 分析按钮
        ttk.Button(param_frame, text="开始分析", command=self.analyze).grid(row=2, column=0, columnspan=2, pady=(10, 0))

        param_frame.columnconfigure(1, weight=1)

        # 结果显示区域
        result_frame = ttk.LabelFrame(right_frame, text="分析结果", padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True)

        self.result_text = scrolledtext.ScrolledText(result_frame, height=10, wrap=tk.WORD)
        self.result_text.pack(fill=tk.BOTH, expand=True)

        # 使用说明
        help_text = """使用说明:
1. 自动加载本地Xcode Archives文件，或手动加载dSYM文件
2. 选择要分析的文件，选择对应的架构(armv7/arm64等)
3. 输入崩溃时的基址和错误内存地址
4. 点击"开始分析"进行符号化，定位崩溃代码位置"""

        self.result_text.insert('1.0', help_text)

    def load_local_archives(self):
        """加载本地的xcarchive文件"""
        self.file_listbox.delete(0, tk.END)

        # 使用文件管理器加载
        archives = self.file_manager.load_local_archives()
        self.file_manager.archive_files = archives

        for archive in archives:
            self.file_listbox.insert(tk.END, f"📦 {archive['name']}")

    def load_file(self):
        """手动加载dSYM或xcarchive文件"""
        import platform

        if platform.system() == 'Darwin':
            # macOS: 尝试使用原生对话框
            file_path = self.file_manager.select_file_with_applescript()

            if file_path:
                self._add_file(file_path)
            else:
                # AppleScript失败，使用备用方法
                self._fallback_file_selection()
        else:
            # 非macOS平台使用标准方法
            self._fallback_file_selection()

    def _add_file(self, file_path):
        """添加文件到列表"""
        file_type = self.file_manager.get_file_type(file_path)

        if file_type == 'dsym':
            file_info = self.file_manager.add_dsym_file(file_path)
            if file_info:
                self.file_listbox.insert(tk.END, f"🔍 {file_info['name']}")
                self.file_listbox.selection_clear(0, tk.END)
                self.file_listbox.selection_set(tk.END)
                self.on_file_select(None)

        elif file_type == 'xcarchive':
            file_info = self.file_manager.add_xcarchive_file(file_path)
            if file_info:
                self.file_listbox.insert(tk.END, f"📦 {file_info['name']}")
                self.file_listbox.selection_clear(0, tk.END)
                self.file_listbox.selection_set(tk.END)
                self.on_file_select(None)
        else:
            messagebox.showinfo("提示", "请选择.dSYM或.xcarchive文件")

    def _fallback_file_selection(self):
        """备用文件选择方法"""
        result = messagebox.askyesnocancel(
            "选择文件类型",
            "您要选择dSYM文件吗？\n\n" +
            "点击'是'选择dSYM文件\n" +
            "点击'否'选择xcarchive文件\n" +
            "点击'取消'退出选择"
        )

        if result is None:  # 用户点击取消
            return
        elif result:  # 用户选择dSYM
            file_path = filedialog.askdirectory(
                title="选择dSYM文件（是一个以.dSYM结尾的文件夹）",
                initialdir="~/"
            )
            if file_path:
                self._add_file(file_path)
        else:  # 用户选择xcarchive
            file_path = filedialog.askdirectory(
                title="选择xcarchive文件（是一个以.xcarchive结尾的文件夹）",
                initialdir="~/Library/Developer/Xcode/Archives/"
            )
            if file_path:
                self._add_file(file_path)

    def on_file_select(self, event):
        """文件选择事件"""
        selection = self.file_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        self.selected_archive = self.file_manager.get_file_by_index(index)

        # 清除之前的UUID选择
        for widget in self.uuid_buttons_frame.winfo_children():
            widget.destroy()

        self.uuid_label.config(text="")
        self.slide_address_label.config(text="")

        # 获取UUID信息
        self.load_uuid_info()

    def load_uuid_info(self):
        """加载选中文件的UUID信息"""
        if not self.selected_archive:
            return

        dsym_path = self.selected_archive['path']

        # 如果是xcarchive，需要找到其中的dSYM
        if self.selected_archive['type'] == 'xcarchive':
            dsym_path = self.file_manager.get_dsym_path_from_xcarchive(dsym_path)
            if not dsym_path:
                self.result_text.delete('1.0', tk.END)
                self.result_text.insert('1.0', "错误: 未找到dSYM文件")
                return

        # 使用UUID解析器获取UUID
        self.uuid_infos = self.uuid_parser.get_uuid_info(dsym_path)

        if not self.uuid_infos:
            self.result_text.delete('1.0', tk.END)
            self.result_text.insert('1.0', "获取UUID失败")
            return

        # 创建架构选择按钮
        for i, uuid_info in enumerate(self.uuid_infos):
            radio = ttk.Radiobutton(
                self.uuid_buttons_frame,
                text=uuid_info['arch'],
                variable=self.uuid_var,
                value=i,
                command=lambda idx=i: self.select_uuid(self.uuid_infos[idx])
            )
            radio.pack(side=tk.LEFT, padx=5)

        if self.uuid_infos:
            # 默认选择第一个
            self.uuid_var.set(0)
            self.select_uuid(self.uuid_infos[0])

    def select_uuid(self, uuid_info):
        """选择UUID"""
        self.selected_uuid = uuid_info
        self.uuid_label.config(text=uuid_info['uuid'])

        # 获取默认基址
        default_slide = self.uuid_parser.get_default_slide_address(uuid_info['arch'])
        self.slide_address_label.config(text=default_slide)
        self.slide_address_entry.delete(0, tk.END)
        self.slide_address_entry.insert(0, default_slide)

    def analyze(self):
        """分析崩溃地址"""
        if not self.selected_archive:
            messagebox.showwarning("提示", "请先选择要分析的文件")
            return

        if not self.selected_uuid:
            messagebox.showwarning("提示", "请先选择架构/UUID")
            return

        slide_address = self.slide_address_entry.get().strip()
        error_address = self.error_address_entry.get().strip()

        if not slide_address:
            messagebox.showwarning("提示", "请输入基址")
            return

        if not error_address:
            messagebox.showwarning("提示", "请输入错误内存地址")
            return

        # 验证地址格式
        if not self.symbolizer.validate_address(slide_address):
            messagebox.showwarning("提示", "基址格式无效，应为0x开头的十六进制")
            return

        if not self.symbolizer.validate_address(error_address):
            messagebox.showwarning("提示", "错误地址格式无效，应为0x开头的十六进制")
            return

        # 清除之前的结果
        self.result_text.delete('1.0', tk.END)
        self.result_text.insert('1.0', "正在分析...\n")

        # 在线程中执行分析
        threading.Thread(target=self._do_analyze, args=(slide_address, error_address), daemon=True).start()

    def _do_analyze(self, slide_address, error_address):
        """执行符号化分析"""
        try:
            # 使用符号化器进行分析
            result = self.symbolizer.symbolicate_address(
                dsym_path=self.selected_uuid['path'],
                arch=self.selected_uuid['arch'],
                slide_address=slide_address,
                error_address=error_address
            )

            # 格式化结果
            if result['success']:
                formatted_result = self.symbolizer.format_symbolication_result(
                    arch=self.selected_uuid['arch'],
                    uuid=self.selected_uuid['uuid'],
                    slide_address=slide_address,
                    error_address=error_address,
                    output=result['output'],
                    command=result['command']
                )
            else:
                formatted_result = f"分析失败:\n{result.get('error', '未知错误')}\n\n命令: {result['command']}"

            self.parent.after(0, self._update_result, formatted_result)

        except Exception as e:
            self.parent.after(0, self._update_result, f"分析失败:\n{str(e)}")

    def _update_result(self, text):
        """更新结果显示"""
        self.result_text.delete('1.0', tk.END)
        self.result_text.insert('1.0', text)

    def export_ipa(self):
        """导出IPA文件"""
        if not self.selected_archive:
            messagebox.showwarning("提示", "请先选择xcarchive文件")
            return

        if self.selected_archive['type'] != 'xcarchive':
            messagebox.showwarning("提示", "只有xcarchive文件才能导出IPA")
            return

        # 选择保存位置
        save_dir = filedialog.askdirectory(title="选择IPA导出目录")

        if not save_dir:
            return

        # 执行导出
        self.result_text.delete('1.0', tk.END)
        self.result_text.insert('1.0', "正在导出IPA...\n")

        threading.Thread(target=self._export_ipa, args=(save_dir,), daemon=True).start()

    def _export_ipa(self, save_dir):
        """执行IPA导出"""
        try:
            result = self.symbolizer.export_ipa(
                xcarchive_path=self.selected_archive['path'],
                output_dir=save_dir
            )

            if result['success']:
                message = f"IPA导出成功:\n{result['output_path']}"
            else:
                message = f"IPA导出失败:\n{result['error']}"

            self.parent.after(0, self._update_result, message)

        except Exception as e:
            self.parent.after(0, self._update_result, f"导出失败:\n{str(e)}")
