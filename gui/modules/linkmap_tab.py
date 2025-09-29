#!/usr/bin/env python3
"""
LinkMap文件分析标签页
用于分析iOS应用的二进制大小，统计代码使用情况
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import re
from pathlib import Path
import threading
from collections import defaultdict

class LinkMapTab:
    def __init__(self, parent):
        self.parent = parent
        self.frame = ttk.Frame(parent)

        # 数据存储
        self.link_map_path = None
        self.link_map_content = None
        self.app_name = None
        self.symbol_map = {}
        self.dead_symbol_map = {}

        self.setup_ui()

    def setup_ui(self):
        """设置UI界面"""
        # 主框架
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 顶部：文件选择区域
        file_frame = ttk.LabelFrame(main_frame, text="Link Map 文件", padding=10)
        file_frame.pack(fill=tk.X, pady=(0, 10))

        # 文件路径
        path_frame = ttk.Frame(file_frame)
        path_frame.pack(fill=tk.X)

        ttk.Label(path_frame, text="文件路径:").pack(side=tk.LEFT)
        self.file_path_var = tk.StringVar()
        self.file_path_entry = ttk.Entry(path_frame, textvariable=self.file_path_var, state='readonly')
        self.file_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5))

        ttk.Button(path_frame, text="选择文件", command=self.choose_file).pack(side=tk.LEFT)
        ttk.Button(path_frame, text="查找默认位置", command=self.find_default_linkmap).pack(side=tk.LEFT, padx=(5, 0))

        # 选项区域
        option_frame = ttk.Frame(file_frame)
        option_frame.pack(fill=tk.X, pady=(10, 0))

        # 搜索框
        ttk.Label(option_frame, text="搜索关键字:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(option_frame, textvariable=self.search_var, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=(5, 10))

        # 按库分组选项
        self.group_by_library_var = tk.BooleanVar(value=False)
        self.group_checkbox = ttk.Checkbutton(
            option_frame,
            text="按库统计",
            variable=self.group_by_library_var
        )
        self.group_checkbox.pack(side=tk.LEFT, padx=(0, 10))

        # 分析按钮
        ttk.Button(option_frame, text="分析", command=self.analyze).pack(side=tk.LEFT)
        ttk.Button(option_frame, text="格式化输出", command=self.format_output).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Button(option_frame, text="导出文件", command=self.export_file).pack(side=tk.LEFT, padx=(5, 0))

        # 中部：分析结果显示
        # 使用Notebook创建标签页
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 符号统计标签页
        symbol_frame = ttk.Frame(notebook)
        notebook.add(symbol_frame, text="符号统计")

        self.symbol_text = scrolledtext.ScrolledText(symbol_frame, wrap=tk.WORD)
        self.symbol_text.pack(fill=tk.BOTH, expand=True)

        # 未使用代码标签页
        dead_code_frame = ttk.Frame(notebook)
        notebook.add(dead_code_frame, text="未使用代码")

        self.dead_code_text = scrolledtext.ScrolledText(dead_code_frame, wrap=tk.WORD)
        self.dead_code_text.pack(fill=tk.BOTH, expand=True)

        # 底部：状态栏
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X)

        self.status_label = ttk.Label(status_frame, text="就绪")
        self.status_label.pack(side=tk.LEFT)

        self.progress_bar = ttk.Progressbar(status_frame, mode='indeterminate')
        self.progress_bar.pack(side=tk.RIGHT, padx=(10, 0))

        # 显示使用说明
        self.show_instructions()

    def show_instructions(self):
        """显示使用说明"""
        instructions = """使用说明:

1. 在 Xcode 中开启编译选项 Write Link Map File:
   Xcode → Project → Build Settings → Write Link Map File 设为 YES

2. 编译工程后，在以下位置找到 Link Map 文件:
   ~/Library/Developer/Xcode/DerivedData/[项目]/Build/Intermediates.noindex/
   [项目].build/[配置]/[目标].build/[项目]-LinkMap-[变体]-[架构].txt

3. 点击"选择文件"加载 Link Map 文件，或点击"查找默认位置"自动搜索

4. 功能说明:
   • 分析: 解析文件并统计符号大小
   • 按库统计: 按照库文件分组显示大小
   • 搜索: 过滤包含关键字的文件
   • 格式化输出: 生成易读的格式化文件
   • 导出文件: 导出统计结果到文本文件

5. 分析结果说明:
   • 符号统计: 显示所有符号的大小排序
   • 未使用代码: 显示被标记为 dead stripped 的符号"""

        self.symbol_text.insert('1.0', instructions)

    def choose_file(self):
        """选择Link Map文件"""
        file_path = filedialog.askopenfilename(
            title="选择 Link Map 文件",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialdir=os.path.expanduser("~/Library/Developer/Xcode/DerivedData/")
        )

        if file_path:
            self.load_linkmap_file(file_path)

    def find_default_linkmap(self):
        """查找默认位置的Link Map文件"""
        derived_data_path = os.path.expanduser("~/Library/Developer/Xcode/DerivedData/")

        if not os.path.exists(derived_data_path):
            messagebox.showinfo("提示", "未找到DerivedData目录")
            return

        # 搜索所有Link Map文件
        linkmap_files = []
        for root, dirs, files in os.walk(derived_data_path):
            for file in files:
                if 'LinkMap' in file and file.endswith('.txt'):
                    full_path = os.path.join(root, file)
                    # 获取修改时间
                    mtime = os.path.getmtime(full_path)
                    linkmap_files.append((full_path, mtime))

        if not linkmap_files:
            messagebox.showinfo("提示", "未找到Link Map文件")
            return

        # 按修改时间排序，最新的在前
        linkmap_files.sort(key=lambda x: x[1], reverse=True)

        # 创建选择对话框
        dialog = tk.Toplevel(self.parent)
        dialog.title("选择 Link Map 文件")
        dialog.geometry("800x400")

        ttk.Label(dialog, text="找到以下Link Map文件 (按修改时间排序):").pack(pady=10)

        # 列表框
        listbox_frame = ttk.Frame(dialog)
        listbox_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        listbox = tk.Listbox(listbox_frame)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=listbox.yview)

        # 添加文件到列表
        from datetime import datetime
        for path, mtime in linkmap_files[:20]:  # 最多显示20个
            dt = datetime.fromtimestamp(mtime)
            display_text = f"{dt.strftime('%Y-%m-%d %H:%M:%S')} - {os.path.basename(path)}"
            listbox.insert(tk.END, display_text)

        # 选择按钮
        def on_select():
            selection = listbox.curselection()
            if selection:
                selected_path = linkmap_files[selection[0]][0]
                dialog.destroy()
                self.load_linkmap_file(selected_path)

        ttk.Button(dialog, text="选择", command=on_select).pack(pady=10)

    def load_linkmap_file(self, file_path):
        """加载Link Map文件"""
        self.link_map_path = file_path
        self.file_path_var.set(file_path)

        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                self.link_map_content = f.read()

            # 提取应用名称
            lines = self.link_map_content.split('\n')
            if lines:
                first_line = lines[0]
                if '.app/' in first_line:
                    self.app_name = first_line.split('.app/')[-1].split('/')[0]
                else:
                    self.app_name = os.path.basename(file_path).replace('-LinkMap', '').replace('.txt', '')

            # 验证文件格式
            if not self.check_content():
                messagebox.showerror("错误", "无效的Link Map文件格式")
                self.link_map_path = None
                self.link_map_content = None
                return

            self.status_label.config(text=f"已加载: {os.path.basename(file_path)}")
            self.symbol_text.delete('1.0', tk.END)
            self.symbol_text.insert('1.0', f"文件已加载: {file_path}\n应用名称: {self.app_name}\n\n点击'分析'开始解析")

        except Exception as e:
            messagebox.showerror("错误", f"读取文件失败: {str(e)}")

    def check_content(self):
        """检查Link Map文件格式"""
        if not self.link_map_content:
            return False

        required_sections = ["# Object files:", "# Symbols:"]
        for section in required_sections:
            if section not in self.link_map_content:
                return False

        return True

    def analyze(self):
        """分析Link Map文件"""
        if not self.link_map_content:
            messagebox.showwarning("提示", "请先选择Link Map文件")
            return

        self.status_label.config(text="正在分析...")
        self.progress_bar.start()

        # 在线程中执行分析
        threading.Thread(target=self._do_analyze, daemon=True).start()

    def _do_analyze(self):
        """执行分析"""
        try:
            # 解析符号
            self.symbol_map = self.parse_symbols(self.link_map_content)
            self.dead_symbol_map = self.parse_dead_symbols(self.link_map_content)

            # 更新UI
            self.parent.after(0, self._update_analysis_result)

        except Exception as e:
            self.parent.after(0, lambda: messagebox.showerror("错误", f"分析失败: {str(e)}"))
        finally:
            self.parent.after(0, self.progress_bar.stop)
            self.parent.after(0, lambda: self.status_label.config(text="分析完成"))

    def parse_symbols(self, content):
        """解析符号信息"""
        symbol_map = {}
        lines = content.split('\n')

        in_object_files = False
        in_symbols = False
        object_files = {}

        for line in lines:
            line = line.strip()

            if line.startswith('# Object files:'):
                in_object_files = True
                continue
            elif line.startswith('# Sections:'):
                in_object_files = False
                continue
            elif line.startswith('# Symbols:'):
                in_symbols = True
                continue
            elif line.startswith('# Dead Stripped Symbols:'):
                break

            if in_object_files and line and not line.startswith('#'):
                # 解析对象文件
                # 格式: [ 0] /path/to/file.o
                match = re.match(r'\[\s*(\d+)\]\s+(.+)', line)
                if match:
                    index = f"[{match.group(1).strip()}]"
                    file_path = match.group(2).strip()
                    object_files[index] = file_path

            elif in_symbols and line and not line.startswith('#'):
                # 解析符号
                # 格式: 0x1000 0x100 [ 0] _symbol_name
                parts = line.split('\t')
                if len(parts) >= 3:
                    size_hex = parts[1] if len(parts) > 1 else '0x0'
                    size = int(size_hex, 16) if size_hex.startswith('0x') else 0

                    # 提取文件索引
                    file_info = parts[2] if len(parts) > 2 else ''
                    match = re.search(r'(\[\s*\d+\])', file_info)
                    if match:
                        file_index = match.group(1).replace(' ', '')
                        if file_index in object_files:
                            file_path = object_files[file_index]
                            if file_path not in symbol_map:
                                symbol_map[file_path] = 0
                            symbol_map[file_path] += size

        return symbol_map

    def parse_dead_symbols(self, content):
        """解析未使用的符号"""
        dead_symbol_map = {}
        lines = content.split('\n')

        in_object_files = False
        in_dead_symbols = False
        object_files = {}

        for line in lines:
            line = line.strip()

            if line.startswith('# Object files:'):
                in_object_files = True
                continue
            elif line.startswith('# Sections:'):
                in_object_files = False
                continue
            elif line.startswith('# Dead Stripped Symbols:'):
                in_dead_symbols = True
                continue

            if in_object_files and line and not line.startswith('#'):
                # 解析对象文件
                match = re.match(r'\[\s*(\d+)\]\s+(.+)', line)
                if match:
                    index = f"[{match.group(1).strip()}]"
                    file_path = match.group(2).strip()
                    object_files[index] = file_path

            elif in_dead_symbols and line and not line.startswith('#'):
                # 解析死代码符号
                # 格式: <<dead>> 0x100 [ 0] _symbol_name
                if line.startswith('<<dead>>'):
                    parts = line.split('\t')
                    if len(parts) >= 3:
                        size_hex = parts[1] if len(parts) > 1 else '0x0'
                        size = int(size_hex, 16) if size_hex.startswith('0x') else 0

                        # 提取文件索引
                        file_info = parts[2] if len(parts) > 2 else ''
                        match = re.search(r'(\[\s*\d+\])', file_info)
                        if match:
                            file_index = match.group(1).replace(' ', '')
                            if file_index in object_files:
                                file_path = object_files[file_index]
                                if file_path not in dead_symbol_map:
                                    dead_symbol_map[file_path] = 0
                                dead_symbol_map[file_path] += size

        return dead_symbol_map

    def _update_analysis_result(self):
        """更新分析结果显示"""
        # 清空显示
        self.symbol_text.delete('1.0', tk.END)
        self.dead_code_text.delete('1.0', tk.END)

        # 应用搜索过滤
        search_keyword = self.search_var.get().strip()

        # 符号统计
        if self.group_by_library_var.get():
            result = self._build_grouped_result(self.symbol_map, search_keyword)
        else:
            result = self._build_result(self.symbol_map, search_keyword)

        self.symbol_text.insert('1.0', result)

        # 未使用代码统计
        if self.group_by_library_var.get():
            dead_result = self._build_grouped_result(self.dead_symbol_map, search_keyword)
        else:
            dead_result = self._build_result(self.dead_symbol_map, search_keyword)

        self.dead_code_text.insert('1.0', dead_result)

    def _build_result(self, symbol_map, search_keyword):
        """构建结果字符串"""
        if not symbol_map:
            return "无数据"

        # 过滤和排序
        filtered_symbols = []
        for file_path, size in symbol_map.items():
            if not search_keyword or search_keyword.lower() in file_path.lower():
                filtered_symbols.append((file_path, size))

        # 按大小排序
        filtered_symbols.sort(key=lambda x: x[1], reverse=True)

        # 构建结果
        result = []
        result.append(f"{'文件大小':<15} {'文件名称'}")
        result.append("=" * 80)

        total_size = 0
        for file_path, size in filtered_symbols:
            total_size += size
            size_str = self._format_size(size)
            # 简化路径显示
            display_path = self._simplify_path(file_path)
            result.append(f"{size_str:<15} {display_path}")

        result.append("=" * 80)
        result.append(f"总计: {self._format_size(total_size)} ({len(filtered_symbols)} 个文件)")

        return '\n'.join(result)

    def _build_grouped_result(self, symbol_map, search_keyword):
        """构建按库分组的结果"""
        if not symbol_map:
            return "无数据"

        # 按库分组
        library_map = defaultdict(int)
        for file_path, size in symbol_map.items():
            if not search_keyword or search_keyword.lower() in file_path.lower():
                library_name = self._extract_library_name(file_path)
                library_map[library_name] += size

        # 排序
        sorted_libraries = sorted(library_map.items(), key=lambda x: x[1], reverse=True)

        # 构建结果
        result = []
        result.append(f"{'库大小':<15} {'库名称'}")
        result.append("=" * 80)

        total_size = 0
        for library_name, size in sorted_libraries:
            total_size += size
            size_str = self._format_size(size)
            result.append(f"{size_str:<15} {library_name}")

        result.append("=" * 80)
        result.append(f"总计: {self._format_size(total_size)} ({len(sorted_libraries)} 个库)")

        return '\n'.join(result)

    def _format_size(self, size):
        """格式化文件大小"""
        if size >= 1024 * 1024:
            return f"{size / (1024 * 1024):.2f}M"
        elif size >= 1024:
            return f"{size / 1024:.2f}K"
        else:
            return f"{size}B"

    def _simplify_path(self, path):
        """简化路径显示"""
        # 移除常见的路径前缀
        patterns = [
            r'.*/Build/Intermediates\.noindex/.*?\.build/.*?/',
            r'.*/DerivedData/.*?\.build/.*?/',
            r'.*/Developer/Platforms/.*?\.sdk/',
            r'.*/Xcode\.app/.*?\.sdk/',
        ]

        simplified = path
        for pattern in patterns:
            simplified = re.sub(pattern, '../', simplified)

        return simplified

    def _extract_library_name(self, file_path):
        """提取库名称"""
        # 从路径中提取库名
        if '.framework' in file_path:
            # Framework
            match = re.search(r'([^/]+)\.framework', file_path)
            if match:
                return match.group(1) + '.framework'

        if '.a' in file_path:
            # 静态库
            match = re.search(r'lib([^/]+)\.a', file_path)
            if match:
                return 'lib' + match.group(1) + '.a'

        # 项目文件
        if '.o' in file_path:
            file_name = os.path.basename(file_path)
            return file_name.replace('.o', '')

        return os.path.basename(file_path)

    def format_output(self):
        """格式化输出Link Map文件"""
        if not self.link_map_content:
            messagebox.showwarning("提示", "请先选择Link Map文件")
            return

        save_path = filedialog.asksaveasfilename(
            title="保存格式化文件",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"formatted_linkmap_{self.app_name}.txt"
        )

        if not save_path:
            return

        self.status_label.config(text="正在格式化...")
        self.progress_bar.start()

        threading.Thread(target=self._format_and_save, args=(save_path,), daemon=True).start()

    def _format_and_save(self, save_path):
        """格式化并保存文件"""
        try:
            lines = self.link_map_content.split('\n')
            formatted_lines = []

            in_object_files = False
            in_sections = False
            in_symbols = False
            in_dead_symbols = False

            for line in lines:
                if line.startswith('# Object files:'):
                    in_object_files = True
                    formatted_lines.append('\n' + '=' * 80)
                    formatted_lines.append('OBJECT FILES')
                    formatted_lines.append('=' * 80)
                elif line.startswith('# Sections:'):
                    in_object_files = False
                    in_sections = True
                    formatted_lines.append('\n' + '=' * 80)
                    formatted_lines.append('SECTIONS')
                    formatted_lines.append('=' * 80)
                elif line.startswith('# Symbols:'):
                    in_sections = False
                    in_symbols = True
                    formatted_lines.append('\n' + '=' * 80)
                    formatted_lines.append('SYMBOLS')
                    formatted_lines.append('=' * 80)
                elif line.startswith('# Dead Stripped Symbols:'):
                    in_symbols = False
                    in_dead_symbols = True
                    formatted_lines.append('\n' + '=' * 80)
                    formatted_lines.append('DEAD STRIPPED SYMBOLS')
                    formatted_lines.append('=' * 80)
                else:
                    # 格式化各部分内容
                    if in_object_files and line.strip() and not line.startswith('#'):
                        # 简化路径
                        formatted_line = self._simplify_path(line)
                        formatted_lines.append(formatted_line)
                    elif (in_sections or in_symbols or in_dead_symbols) and line.strip():
                        # 格式化大小
                        parts = line.split('\t')
                        if len(parts) >= 2 and parts[1].startswith('0x'):
                            size = int(parts[1], 16)
                            size_str = self._format_size(size)
                            parts[1] = size_str.rjust(10)
                            formatted_lines.append('\t'.join(parts))
                        else:
                            formatted_lines.append(line)
                    else:
                        formatted_lines.append(line)

            # 写入文件
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(formatted_lines))

            self.parent.after(0, lambda: messagebox.showinfo("成功", f"格式化文件已保存到:\n{save_path}"))

        except Exception as e:
            self.parent.after(0, lambda: messagebox.showerror("错误", f"格式化失败: {str(e)}"))
        finally:
            self.parent.after(0, self.progress_bar.stop)
            self.parent.after(0, lambda: self.status_label.config(text="格式化完成"))

    def export_file(self):
        """导出统计结果"""
        if not self.symbol_map:
            messagebox.showwarning("提示", "请先分析Link Map文件")
            return

        save_path = filedialog.asksaveasfilename(
            title="导出统计结果",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"linkmap_analysis_{self.app_name}.txt"
        )

        if not save_path:
            return

        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(f"Link Map 分析报告\n")
                f.write(f"应用名称: {self.app_name}\n")
                f.write(f"文件路径: {self.link_map_path}\n")
                f.write("=" * 80 + "\n\n")

                # 符号统计
                f.write("符号统计:\n")
                f.write("-" * 80 + "\n")
                search_keyword = self.search_var.get().strip()
                if self.group_by_library_var.get():
                    result = self._build_grouped_result(self.symbol_map, search_keyword)
                else:
                    result = self._build_result(self.symbol_map, search_keyword)
                f.write(result)

                # 未使用代码
                f.write("\n\n未使用代码:\n")
                f.write("-" * 80 + "\n")
                if self.group_by_library_var.get():
                    dead_result = self._build_grouped_result(self.dead_symbol_map, search_keyword)
                else:
                    dead_result = self._build_result(self.dead_symbol_map, search_keyword)
                f.write(dead_result)

            messagebox.showinfo("成功", f"分析结果已导出到:\n{save_path}")

        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {str(e)}")