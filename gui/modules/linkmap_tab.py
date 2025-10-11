#!/usr/bin/env python3
"""
LinkMap文件分析标签页（重构版）
用于分析iOS应用的二进制大小，统计代码使用情况
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import threading

# 导入模块化组件
try:
    # 相对导入（作为包导入时）
    from .linkmap import LinkMapParser, LinkMapAnalyzer, LinkMapFormatter
except ImportError:
    # 绝对导入（直接导入时）
    from linkmap import LinkMapParser, LinkMapAnalyzer, LinkMapFormatter


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

        # 模块化组件
        self.parser = LinkMapParser()
        self.analyzer = LinkMapAnalyzer()
        self.formatter = LinkMapFormatter()

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
                    mtime = os.path.getmtime(full_path)
                    linkmap_files.append((full_path, mtime))

        if not linkmap_files:
            messagebox.showinfo("提示", "未找到Link Map文件")
            return

        # 按修改时间排序
        linkmap_files.sort(key=lambda x: x[1], reverse=True)

        # 创建选择对话框
        self._show_file_selection_dialog(linkmap_files)

    def _show_file_selection_dialog(self, linkmap_files):
        """显示文件选择对话框"""
        dialog = tk.Toplevel(self.parent)
        dialog.title("选择 Link Map 文件")
        dialog.geometry("800x400")

        ttk.Label(dialog, text="找到以下Link Map文件 (按修改时间排序):").pack(pady=10)

        listbox_frame = ttk.Frame(dialog)
        listbox_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        listbox = tk.Listbox(listbox_frame)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=listbox.yview)

        from datetime import datetime
        for path, mtime in linkmap_files[:20]:
            dt = datetime.fromtimestamp(mtime)
            display_text = f"{dt.strftime('%Y-%m-%d %H:%M:%S')} - {os.path.basename(path)}"
            listbox.insert(tk.END, display_text)

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
            self.app_name = self.parser.extract_app_name(self.link_map_content, file_path)

            # 验证文件格式
            if not self.parser.check_format(self.link_map_content):
                messagebox.showerror("错误", "无效的Link Map文件格式")
                self.link_map_path = None
                self.link_map_content = None
                return

            self.status_label.config(text=f"已加载: {os.path.basename(file_path)}")
            self.symbol_text.delete('1.0', tk.END)
            self.symbol_text.insert('1.0', f"文件已加载: {file_path}\n应用名称: {self.app_name}\n\n点击'分析'开始解析")

        except Exception as e:
            messagebox.showerror("错误", f"读取文件失败: {str(e)}")

    def analyze(self):
        """分析Link Map文件"""
        if not self.link_map_content:
            messagebox.showwarning("提示", "请先选择Link Map文件")
            return

        self.status_label.config(text="正在分析...")
        self.progress_bar.start()

        threading.Thread(target=self._do_analyze, daemon=True).start()

    def _do_analyze(self):
        """执行分析"""
        try:
            # 使用解析器解析符号
            self.symbol_map = self.parser.parse_symbols(self.link_map_content)
            self.dead_symbol_map = self.parser.parse_dead_symbols(self.link_map_content)

            # 更新UI
            self.parent.after(0, self._update_analysis_result)

        except Exception as e:
            self.parent.after(0, lambda: messagebox.showerror("错误", f"分析失败: {str(e)}"))
        finally:
            self.parent.after(0, self.progress_bar.stop)
            self.parent.after(0, lambda: self.status_label.config(text="分析完成"))

    def _update_analysis_result(self):
        """更新分析结果显示"""
        self.symbol_text.delete('1.0', tk.END)
        self.dead_code_text.delete('1.0', tk.END)

        search_keyword = self.search_var.get().strip()

        # 符号统计
        result = self._build_display_result(self.symbol_map, search_keyword)
        self.symbol_text.insert('1.0', result)

        # 未使用代码统计
        dead_result = self._build_display_result(self.dead_symbol_map, search_keyword)
        self.dead_code_text.insert('1.0', dead_result)

    def _build_display_result(self, symbol_map, search_keyword):
        """构建显示结果"""
        if not symbol_map:
            return "无数据"

        # 过滤
        filtered_map = self.analyzer.filter_by_keyword(symbol_map, search_keyword)

        # 按库分组或直接排序
        if self.group_by_library_var.get():
            grouped = self.analyzer.group_by_library(filtered_map)
            sorted_items = self.analyzer.sort_by_size(grouped, reverse=True)
            return self.formatter.format_library_list(sorted_items)
        else:
            sorted_items = self.analyzer.sort_by_size(filtered_map, reverse=True)
            return self.formatter.format_symbol_list(sorted_items)

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
            formatted_content = self.formatter.format_linkmap_file(self.link_map_content)

            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(formatted_content)

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
            search_keyword = self.search_var.get().strip()

            # 构建符号结果
            filtered_symbols = self.analyzer.filter_by_keyword(self.symbol_map, search_keyword)
            if self.group_by_library_var.get():
                grouped_symbols = self.analyzer.group_by_library(filtered_symbols)
                sorted_symbols = self.analyzer.sort_by_size(grouped_symbols, reverse=True)
                symbol_result = self.formatter.format_library_list(sorted_symbols)
            else:
                sorted_symbols = self.analyzer.sort_by_size(filtered_symbols, reverse=True)
                symbol_result = self.formatter.format_symbol_list(sorted_symbols)

            # 构建死代码结果
            filtered_dead = self.analyzer.filter_by_keyword(self.dead_symbol_map, search_keyword)
            if self.group_by_library_var.get():
                grouped_dead = self.analyzer.group_by_library(filtered_dead)
                sorted_dead = self.analyzer.sort_by_size(grouped_dead, reverse=True)
                dead_result = self.formatter.format_library_list(sorted_dead)
            else:
                sorted_dead = self.analyzer.sort_by_size(filtered_dead, reverse=True)
                dead_result = self.formatter.format_symbol_list(sorted_dead)

            # 生成报告
            report = self.formatter.format_analysis_report(
                self.app_name, self.link_map_path,
                symbol_result, dead_result
            )

            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(report)

            messagebox.showinfo("成功", f"分析结果已导出到:\n{save_path}")

        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {str(e)}")
