#!/usr/bin/env python3
"""
dSYM文件分析标签页
用于解析iOS崩溃日志的符号化，根据错误地址进行代码定位
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import subprocess
import os
import re
import json
from pathlib import Path
import threading

class DSYMTab:
    def __init__(self, parent):
        self.parent = parent
        self.frame = ttk.Frame(parent)

        # 存储文件信息
        self.archive_files = []
        self.selected_archive = None
        self.selected_uuid = None

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
        self.archive_files = []

        # Xcode Archives默认路径
        archives_path = os.path.expanduser("~/Library/Developer/Xcode/Archives/")

        if not os.path.exists(archives_path):
            return

        # 遍历查找所有xcarchive文件
        for root, dirs, files in os.walk(archives_path):
            for dir_name in dirs:
                if dir_name.endswith('.xcarchive'):
                    archive_path = os.path.join(root, dir_name)
                    self.archive_files.append({
                        'path': archive_path,
                        'name': dir_name,
                        'type': 'xcarchive'
                    })
                    self.file_listbox.insert(tk.END, f"📦 {dir_name}")

    def load_file(self):
        """手动加载dSYM或xcarchive文件"""
        # 使用tkinter的标准文件对话框，但提示用户选择包目录
        import platform

        if platform.system() == 'Darwin':
            # macOS: 使用原生对话框选择包文件
            try:
                import subprocess
                # 使用AppleScript选择dSYM或xcarchive文件
                script = '''
                tell application "System Events"
                    activate
                    set theFile to choose file with prompt "选择dSYM或xcarchive文件" ¬
                        of type {"dSYM", "xcarchive", "app.dSYM", "public.folder"} ¬
                        default location (path to home folder)
                    return POSIX path of theFile
                end tell
                '''

                result = subprocess.run(
                    ['osascript', '-e', script],
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0 and result.stdout.strip():
                    file_path = result.stdout.strip()

                    # 检查文件类型并添加
                    if '.dSYM' in file_path:
                        self._add_dsym_file(file_path)
                    elif '.xcarchive' in file_path:
                        self._add_xcarchive_file(file_path)
                    else:
                        # 如果选择的是普通文件夹，检查是否包含dSYM
                        if os.path.isdir(file_path):
                            # 检查是否是dSYM目录
                            if file_path.endswith('.dSYM'):
                                self._add_dsym_file(file_path)
                            # 检查目录内是否有dSYM文件
                            elif os.path.exists(os.path.join(file_path, 'Contents', 'Info.plist')):
                                self._add_dsym_file(file_path)
                            else:
                                messagebox.showinfo("提示", "请选择.dSYM或.xcarchive文件")
                        else:
                            messagebox.showinfo("提示", "请选择.dSYM或.xcarchive文件")

            except Exception as e:
                # 如果AppleScript失败，回退到标准方法
                self._fallback_file_selection()
        else:
            # 非macOS平台使用标准方法
            self._fallback_file_selection()

    def _fallback_file_selection(self):
        """备用文件选择方法"""
        # 提示用户
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
                initialdir=os.path.expanduser("~/")
            )
            if file_path:
                if '.dSYM' in file_path or self._is_dsym_directory(file_path):
                    self._add_dsym_file(file_path)
                else:
                    messagebox.showwarning("提示", "请选择有效的.dSYM文件")
        else:  # 用户选择xcarchive
            file_path = filedialog.askdirectory(
                title="选择xcarchive文件（是一个以.xcarchive结尾的文件夹）",
                initialdir=os.path.expanduser("~/Library/Developer/Xcode/Archives/")
            )
            if file_path:
                if file_path.endswith('.xcarchive'):
                    self._add_xcarchive_file(file_path)
                else:
                    messagebox.showwarning("提示", "请选择有效的.xcarchive文件")

    def _is_dsym_directory(self, path):
        """检查目录是否是有效的dSYM目录"""
        # 检查是否包含dSYM的标准结构
        return os.path.exists(os.path.join(path, 'Contents', 'Info.plist')) or \
               os.path.exists(os.path.join(path, 'Contents', 'Resources', 'DWARF'))

    def _add_dsym_file(self, file_path):
        """添加dSYM文件到列表"""
        file_name = os.path.basename(file_path)
        self.archive_files.append({
            'path': file_path,
            'name': file_name,
            'type': 'dsym'
        })
        self.file_listbox.insert(tk.END, f"🔍 {file_name}")
        self.file_listbox.selection_clear(0, tk.END)
        self.file_listbox.selection_set(tk.END)
        self.on_file_select(None)

    def _add_xcarchive_file(self, file_path):
        """添加xcarchive文件到列表"""
        file_name = os.path.basename(file_path)
        self.archive_files.append({
            'path': file_path,
            'name': file_name,
            'type': 'xcarchive'
        })
        self.file_listbox.insert(tk.END, f"📦 {file_name}")
        self.file_listbox.selection_clear(0, tk.END)
        self.file_listbox.selection_set(tk.END)
        self.on_file_select(None)

    def on_file_select(self, event):
        """文件选择事件"""
        selection = self.file_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        self.selected_archive = self.archive_files[index]

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
            dsym_dir = os.path.join(dsym_path, 'dSYMs')
            if os.path.exists(dsym_dir):
                for item in os.listdir(dsym_dir):
                    if item.endswith('.dSYM'):
                        dsym_path = os.path.join(dsym_dir, item)
                        break

        # 使用dwarfdump获取UUID
        try:
            result = subprocess.run(
                ['dwarfdump', '--uuid', dsym_path],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                self.parse_uuid_output(result.stdout, dsym_path)
            else:
                self.result_text.delete('1.0', tk.END)
                self.result_text.insert('1.0', f"获取UUID失败:\n{result.stderr}")

        except Exception as e:
            self.result_text.delete('1.0', tk.END)
            self.result_text.insert('1.0', f"执行dwarfdump失败:\n{str(e)}")

    def parse_uuid_output(self, output, dsym_path):
        """解析UUID输出"""
        lines = output.strip().split('\n')
        uuids = []

        # 解析UUID信息
        # 格式: UUID: XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX (armv7) path/to/file
        pattern = r'UUID: ([\w-]+) \((\w+)\) (.+)'

        for line in lines:
            match = re.search(pattern, line)
            if match:
                uuid = match.group(1)
                arch = match.group(2)
                path = match.group(3)

                uuids.append({
                    'uuid': uuid,
                    'arch': arch,
                    'path': path
                })

        # 创建架构选择按钮
        for i, uuid_info in enumerate(uuids):
            radio = ttk.Radiobutton(
                self.uuid_buttons_frame,
                text=uuid_info['arch'],
                variable=self.uuid_var,
                value=i,
                command=lambda idx=i: self.select_uuid(uuids[idx])
            )
            radio.pack(side=tk.LEFT, padx=5)

        if uuids:
            # 默认选择第一个
            self.uuid_var.set(0)
            self.select_uuid(uuids[0])

    def select_uuid(self, uuid_info):
        """选择UUID"""
        self.selected_uuid = uuid_info
        self.uuid_label.config(text=uuid_info['uuid'])

        # 获取默认基址（这里使用默认值，实际可能需要从二进制文件获取）
        default_slide = "0x104000000"  # iOS默认值
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

        # 清除之前的结果
        self.result_text.delete('1.0', tk.END)
        self.result_text.insert('1.0', "正在分析...\n")

        # 在线程中执行分析
        threading.Thread(target=self._do_analyze, args=(slide_address, error_address), daemon=True).start()

    def _do_analyze(self, slide_address, error_address):
        """执行符号化分析"""
        try:
            # 构建atos命令
            cmd = [
                'xcrun', 'atos',
                '-arch', self.selected_uuid['arch'],
                '-o', self.selected_uuid['path'],
                '-l', slide_address,
                error_address
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            # 更新结果
            output = result.stdout if result.stdout else result.stderr

            self.parent.after(0, self._update_result, f"""
分析结果:
=====================================
架构: {self.selected_uuid['arch']}
UUID: {self.selected_uuid['uuid']}
基址: {slide_address}
错误地址: {error_address}
=====================================

符号化结果:
{output}

命令: {' '.join(cmd)}
""")

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
        save_path = filedialog.asksaveasfilename(
            title="保存IPA文件",
            defaultextension=".ipa",
            filetypes=[("IPA files", "*.ipa"), ("All files", "*.*")]
        )

        if not save_path:
            return

        # 执行导出
        self.result_text.delete('1.0', tk.END)
        self.result_text.insert('1.0', "正在导出IPA...\n")

        threading.Thread(target=self._export_ipa, args=(save_path,), daemon=True).start()

    def _export_ipa(self, save_path):
        """执行IPA导出"""
        try:
            # 使用xcodebuild导出
            cmd = [
                '/usr/bin/xcodebuild',
                '-exportArchive',
                '-archivePath', self.selected_archive['path'],
                '-exportPath', os.path.dirname(save_path),
                '-exportOptionsPlist', self._create_export_options()
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                self.parent.after(0, self._update_result, f"IPA导出成功:\n{save_path}")
            else:
                self.parent.after(0, self._update_result, f"IPA导出失败:\n{result.stderr}")

        except Exception as e:
            self.parent.after(0, self._update_result, f"导出失败:\n{str(e)}")

    def _create_export_options(self):
        """创建导出选项plist"""
        # 创建临时的导出选项文件
        import tempfile
        import plistlib

        options = {
            'method': 'development',  # 或 'app-store', 'ad-hoc', 'enterprise'
            'teamID': '',  # 可选
            'compileBitcode': False,
            'uploadBitcode': False,
            'uploadSymbols': False
        }

        fd, path = tempfile.mkstemp(suffix='.plist')
        with open(path, 'wb') as f:
            plistlib.dump(options, f)
        os.close(fd)

        return path