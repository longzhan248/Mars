#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import sys
import glob
import threading
import queue
import re
from datetime import datetime
import json
from collections import Counter, defaultdict
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib import font_manager

# 导入解码模块
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'decoders'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'components'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'push_tools'))

from decode_mars_nocrypt_log_file_py3 import ParseFile, GetLogStartPos, DecodeBuffer
from fast_decoder import FastXLogDecoder
try:
    from improved_lazy_text import ImprovedLazyText as LazyLoadText
except ImportError:
    from scrolled_text_with_lazy_load import LazyLoadText

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'Hiragino Sans GB', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class LogEntry:
    """日志条目类"""

    # 级别映射表
    LEVEL_MAP = {
        'I': 'INFO',
        'W': 'WARNING',
        'E': 'ERROR',
        'D': 'DEBUG',
        'V': 'VERBOSE',
        'F': 'FATAL'
    }

    # 崩溃关键词 - 必须是确定的崩溃标识
    CRASH_KEYWORDS = [
        '*** Terminating app due to uncaught exception'  # 只有这个才是真正的崩溃
    ]

    def __init__(self, raw_line, source_file=""):
        self.raw_line = raw_line
        self.source_file = source_file  # 来源文件
        self.level = None
        self.timestamp = None
        self.module = None
        self.content = None
        self.thread_id = None
        self.is_crash = False  # 是否为崩溃日志
        self.is_stacktrace = False  # 是否为堆栈信息
        self.parse()

    def _is_crash_content(self, content, location=""):
        """检测内容是否包含崩溃信息"""
        if not content:
            return False

        # 只检查内容中是否包含确定的崩溃标识
        for keyword in self.CRASH_KEYWORDS:
            if keyword in content:  # 精确匹配，不转换大小写
                return True

        return False

    def _mark_as_crash(self, location=None):
        """标记为崩溃日志"""
        self.is_crash = True
        self.level = 'CRASH'
        self.module = 'Crash'
        if location and self.content:
            self.content = f"[{location}] {self.content}"

    def parse(self):
        """解析日志行"""
        # 尝试匹配带有两个模块标签的格式（崩溃日志特殊格式）
        # 格式: [级别][时间][线程ID][<标签1><标签2>][位置信息][内容]
        crash_pattern = r'^\[([IWEDVF])\]\[([^\]]+)\]\[([^\]]+)\]\[<([^>]+)><([^>]+)>\]\[([^\]]+)\](.*)$'
        crash_match = re.match(crash_pattern, self.raw_line)

        if crash_match:
            # 这是崩溃日志格式
            self.level = self.LEVEL_MAP.get(crash_match.group(1), crash_match.group(1))
            self.timestamp = crash_match.group(2)
            self.thread_id = crash_match.group(3)
            tag1 = crash_match.group(4)  # ERROR
            tag2 = crash_match.group(5)  # HY-Default
            location = crash_match.group(6)  # CrashReportManager.m, attachmentForException, 204
            self.content = crash_match.group(7)  # *** Terminating app...

            # 设置模块
            self.module = tag2

            # 检测是否为崩溃日志 - 必须是ERROR级别且包含特定崩溃信息
            if (self.level == 'ERROR' and
                tag1 == 'ERROR' and
                tag2 == 'HY-Default' and
                'CrashReportManager.m' in location and
                self._is_crash_content(self.content)):
                self._mark_as_crash(location)

            return

        # 标准日志格式: [级别][时间][线程ID][模块]内容
        pattern = r'^\[([IWEDVF])\]\[([^\]]+)\]\[([^\]]+)\]\[([^\]]+)\](.*)$'
        match = re.match(pattern, self.raw_line)

        if match:
            # 提取基本信息
            self.level = self.LEVEL_MAP.get(match.group(1), match.group(1))
            self.timestamp = match.group(2)
            self.thread_id = match.group(3)

            # 提取模块
            module_str = match.group(4)
            if 'mars::' in module_str:
                self.module = 'mars'
            elif 'HY-Default' in module_str:
                self.module = 'HY-Default'
            elif 'HY-' in module_str:
                self.module = module_str
            else:
                self.module = module_str.strip('<>[]')

            # 提取内容
            self.content = match.group(5)

            # 标准格式日志一般不是崩溃日志，崩溃日志通常使用特殊格式
            # 除非内容明确包含崩溃标识
            if self.level == 'ERROR' and '*** Terminating app due to uncaught exception' in self.content:
                self._mark_as_crash()
        else:
            # 检查特殊的崩溃相关行
            crash_related_patterns = [
                r'^\*\*\* First throw call stack:',  # iOS崩溃堆栈开始标记
            ]

            # 检查iOS崩溃堆栈格式：数字 + 框架名 + 地址 + 偏移等
            # 例如：0  CoreFoundation  0x00000001897c92ec 0x00000001896af000 + 1155820
            ios_stack_pattern = r'^\s*\d+\s+\S+\s+0x[0-9a-fA-F]+(?:\s+0x[0-9a-fA-F]+\s*\+\s*\d+)?'

            if any(re.match(pattern, self.raw_line) for pattern in crash_related_patterns):
                # 崩溃相关的特殊行
                self.is_stacktrace = True
                self.level = 'CRASH'
                self.module = 'Crash'
                self.content = self.raw_line
            elif re.match(ios_stack_pattern, self.raw_line):
                # iOS堆栈格式，标记为可能的崩溃堆栈
                self.is_stacktrace = True
                self.level = 'STACKTRACE'
                self.module = 'Crash-Stack'  # 临时标记，后续验证
                self.content = self.raw_line
            else:
                # 无法解析的行，作为普通内容处理
                self.level = 'OTHER'
                self.module = 'Unknown'
                self.content = self.raw_line

class FileGroup:
    """文件分组类"""
    def __init__(self, base_name):
        self.base_name = base_name
        self.files = []  # 文件路径列表
        self.entries = []  # 合并后的日志条目

    def add_file(self, filepath):
        """添加文件到组"""
        self.files.append(filepath)

    def get_display_name(self):
        """获取显示名称"""
        file_count = len(self.files)
        if file_count == 1:
            return os.path.basename(self.files[0])
        else:
            return f"{self.base_name} ({file_count}个文件)"

class MarsLogAnalyzerPro:
    def __init__(self, root):
        self.root = root
        self.root.title("Mars日志分析系统 - 专业版")

        # 获取屏幕尺寸
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # 设置窗口大小为屏幕的85%，但不超过1400x900
        window_width = min(int(screen_width * 0.85), 1400)
        window_height = min(int(screen_height * 0.85), 900)

        # 计算窗口居中位置
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2

        # 设置窗口大小和位置
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # 设置最小窗口大小
        self.root.minsize(1200, 700)

        # 线程安全的队列
        self.log_queue = queue.Queue()

        # 快速解码器
        self.fast_decoder = FastXLogDecoder(max_workers=4)

        # 数据存储
        self.file_groups = {}  # 文件分组 {base_name: FileGroup}
        self.current_group = None  # 当前选中的文件组
        self.log_entries = []  # 当前显示的LogEntry对象列表
        self.filtered_entries = []  # 过滤后的条目
        self.modules_data = defaultdict(list)  # 按模块分组的数据
        self.analysis_results = {}
        self.current_module_entries = []  # 当前模块的日志条目
        self.current_module_name = None  # 当前选中的模块名称
        self.ignore_module_selection = False  # 标记是否忽略模块选择事件
        self.current_module_filtered = []  # 当前模块的过滤结果

        # 文件合并选项
        self.merge_files_var = tk.BooleanVar(value=True)
        self.log_types = {}  # 日志类型 {类型名: [文件列表]}

        # 创建UI
        self.create_widgets()

        # 启动日志队列处理
        self.process_log_queue()

    def create_widgets(self):
        # 创建主框架
        root_frame = ttk.Frame(self.root, padding="10")
        root_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        root_frame.columnconfigure(0, weight=1)
        root_frame.rowconfigure(0, weight=1)

        # 创建顶级标签页（区分Mars日志分析和IPS解析）
        self.main_notebook = ttk.Notebook(root_frame)
        self.main_notebook.pack(fill=tk.BOTH, expand=True)

        # ============ Mars日志分析标签页 ============
        main_frame = ttk.Frame(self.main_notebook, padding="10")
        self.main_notebook.add(main_frame, text="Mars日志分析")

        # 配置Mars框架的网格权重
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)

        # 文件选择区域
        file_frame = ttk.LabelFrame(main_frame, text="文件选择", padding="10")
        file_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        # 第一行：文件/文件夹选择
        self.folder_path_var = tk.StringVar()
        ttk.Label(file_frame, text="路径:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(file_frame, textvariable=self.folder_path_var, width=45).grid(row=0, column=1, padx=5)
        # 创建按钮样式
        btn_style = ttk.Style()
        btn_style.configure('Large.TButton', padding=(10, 5, 10, 5), font=('', 11))

        ttk.Button(file_frame, text="选择文件夹", command=self.select_folder, style='Large.TButton').grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(file_frame, text="选择文件", command=self.select_file, style='Large.TButton').grid(row=0, column=3, padx=5, pady=5)

        # 合并选项
        merge_check = ttk.Checkbutton(file_frame, text="合并相似文件名",
                                      variable=self.merge_files_var,
                                      command=self.on_merge_option_change)
        merge_check.grid(row=0, column=4, padx=10)

        ttk.Button(file_frame, text="开始解析", command=self.start_parsing, style='Large.TButton').grid(row=0, column=5, padx=5, pady=5)

        # 第二行：日志类型和文件组选择
        ttk.Label(file_frame, text="日志类型:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.log_type_var = tk.StringVar()
        self.log_type_combo = ttk.Combobox(file_frame, textvariable=self.log_type_var, width=20, state='readonly')
        self.log_type_combo.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        self.log_type_combo.bind('<<ComboboxSelected>>', self.on_log_type_select)

        ttk.Label(file_frame, text="文件组:").grid(row=1, column=2, sticky=tk.W, pady=5, padx=(20, 5))
        self.file_group_var = tk.StringVar()
        self.file_group_combo = ttk.Combobox(file_frame, textvariable=self.file_group_var, width=30, state='readonly')
        self.file_group_combo.grid(row=1, column=3, padx=5, pady=5)
        self.file_group_combo.bind('<<ComboboxSelected>>', self.on_file_group_select)

        # 文件组信息
        self.file_group_info_var = tk.StringVar(value="请选择文件或文件夹")
        ttk.Label(file_frame, textvariable=self.file_group_info_var).grid(row=1, column=4, columnspan=2, sticky=tk.W, padx=5, pady=5)

        # 进度条
        self.progress_var = tk.StringVar(value="就绪")
        self.progress_label = ttk.Label(file_frame, textvariable=self.progress_var)
        self.progress_label.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)

        self.progress_bar = ttk.Progressbar(file_frame, mode='indeterminate')
        self.progress_bar.grid(row=2, column=1, columnspan=4, sticky=(tk.W, tk.E), pady=5)

        # 创建Notebook（标签页）
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        # 日志查看标签页
        self.log_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.log_frame, text="日志查看")
        self.create_log_viewer()

        # 模块分组标签页
        self.module_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.module_frame, text="模块分组")
        self.create_module_viewer()

        # 搜索过滤区域
        search_frame = ttk.LabelFrame(main_frame, text="搜索与过滤", padding="10")
        search_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        # 第一行：关键词和日志级别
        ttk.Label(search_frame, text="关键词:").grid(row=0, column=0, sticky=tk.W)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=25)
        search_entry.grid(row=0, column=1, padx=5)
        search_entry.bind('<Return>', lambda e: self.search_logs())

        # 搜索模式
        self.search_mode_var = tk.StringVar(value="字符串")
        search_mode = ttk.Combobox(search_frame, textvariable=self.search_mode_var, width=8, state='readonly')
        search_mode['values'] = ('字符串', '正则')
        search_mode.grid(row=0, column=2, padx=5)

        ttk.Label(search_frame, text="日志级别:").grid(row=0, column=3, padx=10)
        self.level_var = tk.StringVar()
        level_combo = ttk.Combobox(search_frame, textvariable=self.level_var, width=15)
        level_combo['values'] = ('全部', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'VERBOSE', 'FATAL')
        level_combo.current(0)
        level_combo.grid(row=0, column=4, padx=5)
        level_combo.bind('<<ComboboxSelected>>', lambda e: self.apply_global_filter())

        # 第二行：时间范围过滤
        ttk.Label(search_frame, text="时间范围:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.global_time_start_var = tk.StringVar(value="")
        self.global_time_end_var = tk.StringVar(value="")

        global_time_start = ttk.Entry(search_frame, textvariable=self.global_time_start_var, width=20)
        global_time_start.grid(row=1, column=1, padx=5, pady=5)
        global_time_start.bind('<FocusIn>', lambda e: self.on_time_focus_in(e, self.global_time_start_var))
        global_time_start.bind('<Return>', lambda e: self.apply_global_filter())

        ttk.Label(search_frame, text="至").grid(row=1, column=2, padx=5, pady=5)

        global_time_end = ttk.Entry(search_frame, textvariable=self.global_time_end_var, width=20)
        global_time_end.grid(row=1, column=3, padx=5, pady=5)
        global_time_end.bind('<FocusIn>', lambda e: self.on_time_focus_in(e, self.global_time_end_var))
        global_time_end.bind('<Return>', lambda e: self.apply_global_filter())

        ttk.Label(search_frame, text="格式: YYYY-MM-DD HH:MM:SS", font=('Arial', 9)).grid(row=1, column=4, padx=5, pady=5)

        # 第三行：模块过滤和操作按钮
        ttk.Label(search_frame, text="模块:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.module_var = tk.StringVar()
        self.module_combo = ttk.Combobox(search_frame, textvariable=self.module_var, width=30)
        self.module_combo['values'] = ('全部',)
        self.module_combo.current(0)
        self.module_combo.grid(row=2, column=1, columnspan=2, padx=5, pady=5)
        self.module_combo.bind('<<ComboboxSelected>>', lambda e: self.apply_global_filter())

        ttk.Button(search_frame, text="搜索", command=self.search_logs).grid(row=0, column=5, padx=5)
        ttk.Button(search_frame, text="清除过滤", command=self.clear_filter).grid(row=0, column=6, padx=5)
        ttk.Button(search_frame, text="应用过滤", command=self.apply_global_filter).grid(row=1, column=5, padx=5, pady=5)

        # 第四行：导出按钮
        ttk.Button(search_frame, text="导出当前视图", command=self.export_current_view).grid(row=3, column=0, padx=5, pady=5)
        ttk.Button(search_frame, text="导出分组报告", command=self.export_grouped_report).grid(row=3, column=1, padx=5, pady=5)
        ttk.Button(search_frame, text="导出完整报告", command=self.export_full_report).grid(row=3, column=2, padx=5, pady=5)

        # ============ IPS崩溃解析标签页 ============
        self.create_ips_analyzer_tab()

        # ============ iOS推送测试标签页 ============
        self.create_push_test_tab()

        # ============ iOS沙盒浏览标签页 ============
        self.create_sandbox_browser_tab()

        # ============ dSYM分析标签页 ============
        self.create_dsym_analysis_tab()

        # ============ LinkMap分析标签页 ============
        self.create_linkmap_analysis_tab()

    def create_log_viewer(self):
        """创建日志查看器"""
        viewer_frame = ttk.Frame(self.log_frame)
        viewer_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 添加统计标签
        self.log_stats_var = tk.StringVar(value="等待加载...")
        stats_label = ttk.Label(viewer_frame, textvariable=self.log_stats_var)
        stats_label.pack(anchor=tk.W, pady=2)

        # 使用懒加载文本组件
        self.log_text = LazyLoadText(viewer_frame, batch_size=100, width=100, height=20)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # 配置文本标签样式 - 增大字体，调整颜色
        self.log_text.tag_config("FATAL", foreground="white", background="#DC143C", font=("Courier", 12, "bold"), lmargin2=20)  # 深红背景
        self.log_text.tag_config("ERROR", foreground="#DC143C", font=("Courier", 12, "bold"), lmargin2=20)  # 深红色
        self.log_text.tag_config("WARNING", foreground="#FF6B35", font=("Courier", 12), lmargin2=20)  # 亮橙色
        self.log_text.tag_config("INFO", foreground="#0066CC", font=("Courier", 12), lmargin2=20)  # 深蓝色
        self.log_text.tag_config("DEBUG", foreground="#00A86B", font=("Courier", 12), lmargin2=20)  # 翡翠绿
        self.log_text.tag_config("VERBOSE", foreground="#8B4789", font=("Courier", 12), lmargin2=20)  # 紫色
        self.log_text.tag_config("CRASH", foreground="white", background="#8B0000", font=("Courier", 12, "bold"), lmargin2=20)  # 崩溃日志：暗红背景
        self.log_text.tag_config("STACKTRACE", foreground="#FFD700", background="#2F4F4F", font=("Courier", 11), lmargin2=40)  # 堆栈信息：金色文字暗灰背景
        self.log_text.tag_config("HIGHLIGHT", background="yellow")
        self.log_text.tag_config("MODULE_MARS", foreground="#2E7D32", font=("Courier", 12, "italic"))  # 深绿色
        self.log_text.tag_config("MODULE_DEFAULT", foreground="#7B1FA2", font=("Courier", 12, "italic"))  # 深紫色

    def create_module_viewer(self):
        """创建模块分组查看器"""
        paned = ttk.PanedWindow(self.module_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 左侧：模块列表
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)

        ttk.Label(left_frame, text="模块列表", font=("Arial", 12, "bold")).pack(pady=5)

        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.module_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, exportselection=False)
        self.module_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.module_listbox.yview)

        self.module_listbox.bind('<<ListboxSelect>>', self.on_module_select)

        # 右侧：模块详情
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=3)

        # 绑定文本选择事件，防止干扰模块选择
        def on_text_focus_in(event):
            # 保存当前模块选择
            selection = self.module_listbox.curselection()
            if selection:
                index = selection[0]
                module_text = self.module_listbox.get(index)
                self.current_module_name = module_text.split(' (')[0]

        ttk.Label(right_frame, text="模块日志详情", font=("Arial", 12, "bold")).pack(pady=5)

        # 模块内搜索框
        module_search_frame = ttk.Frame(right_frame)
        module_search_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(module_search_frame, text="模块内搜索:").pack(side=tk.LEFT)
        self.module_search_var = tk.StringVar()
        module_search_entry = ttk.Entry(module_search_frame, textvariable=self.module_search_var, width=20)
        module_search_entry.pack(side=tk.LEFT, padx=5)
        module_search_entry.bind('<Return>', lambda e: self.search_in_module())

        self.module_search_mode_var = tk.StringVar(value="字符串")
        module_search_mode = ttk.Combobox(module_search_frame, textvariable=self.module_search_mode_var, width=8, state='readonly')
        module_search_mode['values'] = ('字符串', '正则')
        module_search_mode.pack(side=tk.LEFT, padx=5)

        ttk.Button(module_search_frame, text="搜索", command=self.search_in_module).pack(side=tk.LEFT, padx=5)
        ttk.Button(module_search_frame, text="清除", command=self.clear_module_search).pack(side=tk.LEFT)

        # 时间范围过滤框
        module_time_frame = ttk.Frame(right_frame)
        module_time_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(module_time_frame, text="时间范围:").pack(side=tk.LEFT)
        self.module_time_start_var = tk.StringVar(value="")
        self.module_time_end_var = tk.StringVar(value="")

        module_time_start = ttk.Entry(module_time_frame, textvariable=self.module_time_start_var, width=20)
        module_time_start.pack(side=tk.LEFT, padx=5)
        module_time_start.bind('<FocusIn>', lambda e: self.on_time_focus_in(e, self.module_time_start_var))

        ttk.Label(module_time_frame, text="至").pack(side=tk.LEFT, padx=5)

        module_time_end = ttk.Entry(module_time_frame, textvariable=self.module_time_end_var, width=20)
        module_time_end.pack(side=tk.LEFT, padx=5)
        module_time_end.bind('<FocusIn>', lambda e: self.on_time_focus_in(e, self.module_time_end_var))

        ttk.Button(module_time_frame, text="应用过滤", command=self.apply_module_filter).pack(side=tk.LEFT, padx=5)
        ttk.Button(module_time_frame, text="重置", command=self.reset_module_filter).pack(side=tk.LEFT)

        # 导出按钮框架
        export_frame = ttk.Frame(right_frame)
        export_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(export_frame, text="导出当前模块", command=self.export_current_module).pack(side=tk.LEFT, padx=5)
        ttk.Button(export_frame, text="导出过滤结果", command=self.export_filtered_module).pack(side=tk.LEFT, padx=5)
        ttk.Button(export_frame, text="导出所有模块", command=self.export_all_modules).pack(side=tk.LEFT, padx=5)

        # 时间格式提示
        ttk.Label(right_frame, text="时间格式: YYYY-MM-DD HH:MM:SS 或 HH:MM:SS 或 YYYY-MM-DD",
                 font=('Arial', 9), foreground='gray').pack(anchor=tk.W, padx=5)

        self.module_stats_var = tk.StringVar(value="选择一个模块查看详情")
        stats_label = ttk.Label(right_frame, textvariable=self.module_stats_var)
        stats_label.pack(anchor=tk.W, pady=2)

        # 使用懒加载文本组件
        self.module_log_text = LazyLoadText(right_frame, batch_size=100)
        self.module_log_text.pack(fill=tk.BOTH, expand=True)

        # 绑定焦点事件，保护模块选择
        self.module_log_text.text.bind('<FocusIn>', on_text_focus_in)
        self.module_log_text.text.bind('<Button-1>', on_text_focus_in)

        # 配置样式
        self.module_log_text.tag_config("FATAL", foreground="white", background="#DC143C", font=("Arial", 10, "bold"), lmargin2=15)  # 深红背景
        self.module_log_text.tag_config("ERROR", foreground="#DC143C", font=("Arial", 10, "bold"), lmargin2=15)  # 深红色
        self.module_log_text.tag_config("WARNING", foreground="#FF6B35", font=("Arial", 10), lmargin2=15)  # 亮橙色
        self.module_log_text.tag_config("INFO", foreground="#0066CC", font=("Arial", 10), lmargin2=15)  # 深蓝色
        self.module_log_text.tag_config("DEBUG", foreground="#00A86B", font=("Arial", 10), lmargin2=15)  # 翡翠绿
        self.module_log_text.tag_config("VERBOSE", foreground="#8B4789", font=("Arial", 10), lmargin2=15)  # 紫色
        self.module_log_text.tag_config("CRASH", foreground="white", background="#8B0000", font=("Arial", 10, "bold"), lmargin2=15)  # 崩溃日志
        self.module_log_text.tag_config("STACKTRACE", foreground="#FFD700", background="#2F4F4F", font=("Arial", 9), lmargin2=30)  # 堆栈信息

    def extract_file_base_name(self, filename):
        """提取文件基础名称用于分组"""
        # 移除.xlog扩展名
        name = filename.replace('.xlog', '')

        # 尝试匹配各种模式
        patterns = [
            r'^(.+?)_\d{8}(?:_\d+)?$',  # name_20250911 或 name_20250911_1
            r'^(.+?)_\d{8}$',            # name_20250911
            r'^(.+?)(?:_\d+)?$',         # name 或 name_1
        ]

        for pattern in patterns:
            match = re.match(pattern, name)
            if match:
                return match.group(1)

        # 如果没有匹配，返回去掉数字后缀的名称
        return re.sub(r'_\d+$', '', name)

    def extract_log_type(self, filename):
        """提取日志类型（文件名前缀）"""
        # 移除.xlog扩展名
        name = filename.replace('.xlog', '')

        # 提取第一个下划线之前的部分作为类型
        # 例如: mizhua_20250911 -> mizhua, imsdk_C_20250912 -> imsdk
        parts = name.split('_')
        if parts:
            # 如果是imsdk_C这种格式，取前两部分
            if len(parts) > 1 and parts[1] in ['A', 'B', 'C', 'D', 'E', 'F']:
                return f"{parts[0]}_{parts[1]}"
            return parts[0]
        return name

    def group_files(self, xlog_files):
        """将文件分组"""
        self.file_groups.clear()
        self.log_types.clear()

        # 先按日志类型分类
        for filepath in xlog_files:
            filename = os.path.basename(filepath)
            log_type = self.extract_log_type(filename)

            if log_type not in self.log_types:
                self.log_types[log_type] = []
            self.log_types[log_type].append(filepath)

        # 更新日志类型下拉框
        if self.log_types:
            type_names = sorted(self.log_types.keys())
            type_names.insert(0, '全部')
            self.log_type_combo['values'] = type_names
            self.log_type_combo.current(0)
            self.log_type_var.set(type_names[0])

        # 对所有文件进行分组
        if not self.merge_files_var.get():
            # 不合并，每个文件一个组
            for filepath in xlog_files:
                basename = os.path.basename(filepath)
                group = FileGroup(basename)
                group.add_file(filepath)
                self.file_groups[basename] = group
        else:
            # 合并相似文件名
            for filepath in xlog_files:
                filename = os.path.basename(filepath)
                base_name = self.extract_file_base_name(filename)

                if base_name not in self.file_groups:
                    self.file_groups[base_name] = FileGroup(base_name)

                self.file_groups[base_name].add_file(filepath)

        # 更新文件组选择框
        self.update_file_groups_combo()

    def update_file_groups_combo(self, log_type=None):
        """更新文件组下拉框"""
        if log_type is None:
            log_type = self.log_type_var.get()

        # 根据选中的日志类型筛选文件组
        filtered_groups = {}
        if log_type == '全部' or not log_type:
            filtered_groups = self.file_groups
        else:
            # 只显示属于该日志类型的文件组
            for base_name, group in self.file_groups.items():
                # 检查组中是否有属于该日志类型的文件
                for filepath in group.files:
                    filename = os.path.basename(filepath)
                    if self.extract_log_type(filename) == log_type:
                        filtered_groups[base_name] = group
                        break

        if filtered_groups:
            group_names = []
            for base_name, group in sorted(filtered_groups.items()):
                group_names.append(group.get_display_name())

            self.file_group_combo['values'] = group_names
            if group_names:
                self.file_group_combo.current(0)
                self.file_group_var.set(group_names[0])
        else:
            self.file_group_combo['values'] = ()
            self.file_group_var.set("")

    def on_log_type_select(self, event):
        """日志类型选择事件"""
        self.update_file_groups_combo()
        # 如果已经解析，加载第一个可用的文件组
        if self.file_group_combo['values']:
            self.on_file_group_select(None)

    def on_merge_option_change(self):
        """合并选项改变事件"""
        if self.file_groups:
            # 重新分组现有文件
            all_files = []
            for group in self.file_groups.values():
                all_files.extend(group.files)
            self.group_files(all_files)

            # 如果已经解析，重新加载当前组
            if self.current_group:
                self.on_file_group_select(None)

    def on_file_group_select(self, event):
        """文件组选择事件"""
        selected = self.file_group_var.get()
        if not selected:
            return

        # 找到对应的文件组
        for base_name, group in self.file_groups.items():
            if group.get_display_name() == selected:
                self.current_group = group

                # 更新文件组信息
                total_size = sum(os.path.getsize(f) for f in group.files if os.path.exists(f))
                size_mb = total_size / (1024 * 1024)
                info_text = f"包含 {len(group.files)} 个文件，总大小: {size_mb:.2f} MB"
                if len(group.entries) > 0:
                    info_text += f"，{len(group.entries)} 条日志"
                self.file_group_info_var.set(info_text)

                # 如果已解析，加载该组的日志
                if group.entries:
                    self.load_group_logs(group)

                break

    def post_process_crash_logs(self, group):
        """后处理崩溃日志，将相关堆栈信息归入Crash模块"""
        entries = group.entries
        crash_indices = []

        # 找出所有崩溃点
        for i, entry in enumerate(entries):
            if entry.is_crash or (entry.level == 'CRASH' and
                                   ('*** First throw call stack' in getattr(entry, 'content', '') or
                                    'CrashReportManager' in getattr(entry, 'content', ''))):
                crash_indices.append(i)

        # 处理每个崩溃点后的堆栈信息
        processed_indices = set()
        for crash_idx in crash_indices:
            for i in range(crash_idx + 1, len(entries)):
                if i in processed_indices:
                    continue

                entry = entries[i]

                # 判断是否为堆栈信息
                is_stack_entry = (
                    entry.module == 'Crash-Stack' or
                    (entry.level == 'OTHER' and len(entry.content.strip()) < 5) or
                    (entry.is_stacktrace and entry.level in ['STACKTRACE', 'OTHER'])
                )

                if is_stack_entry:
                    entry.module = 'Crash'
                    entry.level = 'CRASH'
                    entry.is_crash = True
                    processed_indices.add(i)
                # 遇到新的格式化日志，停止处理
                elif entry.timestamp and entry.level in ['ERROR', 'WARNING', 'INFO', 'DEBUG']:
                    break

        # 清理未处理的临时标记
        for i, entry in enumerate(entries):
            if i not in processed_indices and entry.module == 'Crash-Stack':
                entry.module = 'System'
                entry.level = 'INFO'
                entry.is_stacktrace = False

    def load_group_logs(self, group):
        """加载文件组的日志"""
        self.progress_var.set(f"正在加载 {len(group.entries)} 条日志...")

        self.log_entries = group.entries.copy()
        self.filtered_entries = self.log_entries.copy()

        # 重新分析
        self.analyze_logs()

        # 更新显示
        self.display_logs(self.filtered_entries)
        self.update_statistics()

        # 异步更新图表（避免阻塞）
        thread = threading.Thread(target=self.update_charts)
        thread.daemon = True
        thread.start()

        self.progress_var.set(f"加载完成: {len(group.entries)} 条日志")

    def select_folder(self):
        """选择文件夹"""
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path_var.set(folder)

            # 查找xlog文件并分组
            xlog_files = glob.glob(os.path.join(folder, "*.xlog"))
            if xlog_files:
                self.group_files(xlog_files)
                self.progress_var.set(f"找到 {len(xlog_files)} 个xlog文件，分为 {len(self.file_groups)} 组")
            else:
                self.progress_var.set("未找到xlog文件")
                self.file_groups.clear()
                self.update_file_groups_combo()

    def select_file(self):
        """选择单个xlog文件"""
        filepath = filedialog.askopenfilename(
            title="选择xlog文件",
            filetypes=[("Mars日志文件", "*.xlog")]
        )
        if filepath:
            # 验证文件扩展名
            if not filepath.lower().endswith('.xlog'):
                messagebox.showwarning("文件格式错误", "只支持.xlog格式的Mars日志文件")
                return

            self.folder_path_var.set(filepath)

            # 单文件也创建一个文件组
            self.group_files([filepath])
            self.progress_var.set(f"已选择文件: {os.path.basename(filepath)}")

    def on_time_focus_in(self, event, var):
        """时间输入框获得焦点时的处理"""
        # 如果是默认提示文本，清空
        if var.get() in ["HH:MM:SS", ""]:
            pass  # 保持空或原值

    def parse_time_string(self, time_str):
        """解析多种格式的时间字符串
        支持格式：
        - YYYY-MM-DD HH:MM:SS
        - YYYY-MM-DD HH:MM:SS.mmm
        - YYYY-MM-DD
        - HH:MM:SS
        - HH:MM:SS.mmm
        - HH:MM
        返回标准化的时间字符串用于比较
        """
        import re
        from datetime import datetime

        if not time_str or time_str.strip() == "":
            return None

        time_str = time_str.strip()

        # 完整格式：YYYY-MM-DD HH:MM:SS 或 YYYY-MM-DD HH:MM:SS.mmm
        full_pattern = r'^(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?$'
        match = re.match(full_pattern, time_str)
        if match:
            return time_str

        # 只有日期：YYYY-MM-DD
        date_only_pattern = r'^(\d{4})-(\d{2})-(\d{2})$'
        match = re.match(date_only_pattern, time_str)
        if match:
            return f"{time_str} 00:00:00"

        # 只有时间：HH:MM:SS 或 HH:MM:SS.mmm
        time_only_pattern = r'^(\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?$'
        match = re.match(time_only_pattern, time_str)
        if match:
            # 对于只有时间的，需要从日志中提取日期部分
            return f"TIME_ONLY:{time_str}"

        # 只有时间：HH:MM（补充秒）
        time_short_pattern = r'^(\d{2}):(\d{2})$'
        match = re.match(time_short_pattern, time_str)
        if match:
            return f"TIME_ONLY:{time_str}:00"

        return None

    def compare_log_time(self, log_timestamp, start_time, end_time):
        """比较日志时间戳是否在指定范围内"""
        import re

        # 从日志时间戳提取时间信息
        # 支持的格式：
        # 1. 2025-09-15 +8.0 11:05:43.995
        # 2. 2025-09-21 +8.0 13:09:49.038
        # 3. 2025-09-21 13:09:49.038 (无时区)

        # 尝试带时区的格式
        log_pattern = r'^(\d{4}-\d{2}-\d{2})\s+[+\-]?\d+\.?\d*\s+(\d{2}:\d{2}:\d{2}(?:\.\d+)?)'
        match = re.match(log_pattern, log_timestamp)

        if not match:
            # 尝试不带时区的格式
            log_pattern_simple = r'^(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2}(?:\.\d+)?)'
            match = re.match(log_pattern_simple, log_timestamp)

        if not match:
            return True  # 无法解析的时间戳，默认包含

        log_date = match.group(1)
        log_time = match.group(2)
        log_full = f"{log_date} {log_time}"

        # 处理开始时间
        if start_time:
            parsed_start = self.parse_time_string(start_time)
            if parsed_start:
                if parsed_start.startswith("TIME_ONLY:"):
                    # 只比较时间部分
                    start_time_only = parsed_start[10:]
                    if log_time < start_time_only:
                        return False
                else:
                    # 完整比较
                    if log_full < parsed_start:
                        return False

        # 处理结束时间
        if end_time:
            parsed_end = self.parse_time_string(end_time)
            if parsed_end:
                if parsed_end.startswith("TIME_ONLY:"):
                    # 只比较时间部分
                    end_time_only = parsed_end[10:]
                    if log_time > end_time_only:
                        return False
                else:
                    # 完整比较
                    # 如果结束时间只有日期，需要调整到当天最后时刻
                    if re.match(r'^\d{4}-\d{2}-\d{2} 00:00:00$', parsed_end):
                        parsed_end = parsed_end[:10] + " 23:59:59.999"
                    if log_full > parsed_end:
                        return False

        return True

    def apply_global_filter(self):
        """应用全局组合过滤（关键词 + 时间范围 + 级别 + 模块）"""
        if not self.log_entries:
            return

        # 获取所有过滤条件
        keyword = self.search_var.get()
        search_mode = self.search_mode_var.get()
        level_filter = self.level_var.get()
        module_filter = self.module_var.get()
        start_time = self.global_time_start_var.get()
        end_time = self.global_time_end_var.get()

        filtered = []

        for entry in self.log_entries:
            # 关键词过滤
            if keyword:
                if search_mode == "正则":
                    import re
                    try:
                        if not re.search(keyword, entry.raw_line, re.IGNORECASE):
                            continue
                    except re.error:
                        messagebox.showerror("错误", "无效的正则表达式")
                        return
                else:
                    if keyword.lower() not in entry.raw_line.lower():
                        continue

            # 级别过滤
            if level_filter and level_filter != '全部':
                if entry.level != level_filter:
                    continue

            # 模块过滤
            if module_filter and module_filter != '全部':
                if entry.module != module_filter:
                    continue

            # 时间范围过滤
            if start_time or end_time:
                # 优先使用entry.timestamp
                if entry.timestamp:
                    if not self.compare_log_time(entry.timestamp, start_time, end_time):
                        continue
                else:
                    # 如果没有timestamp，尝试从raw_line提取
                    import re
                    # 支持格式：[I][2025-09-21 +8.0 13:09:49.038]
                    time_pattern = r'\[(\d{4}-\d{2}-\d{2}\s+[+\-]?\d+\.?\d*\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?)\]'
                    match = re.search(time_pattern, entry.raw_line)
                    if match:
                        timestamp = match.group(1)
                        if not self.compare_log_time(timestamp, start_time, end_time):
                            continue

            filtered.append(entry)

        self.filtered_entries = filtered
        self.display_logs(filtered)

        # 更新统计信息
        filter_info = []
        if keyword:
            filter_info.append(f"关键词:{keyword}")
        if level_filter and level_filter != '全部':
            filter_info.append(f"级别:{level_filter}")
        if module_filter and module_filter != '全部':
            filter_info.append(f"模块:{module_filter}")
        if start_time:
            filter_info.append(f"开始:{start_time}")
        if end_time:
            filter_info.append(f"结束:{end_time}")

        if filter_info:
            stats_text = f"过滤结果: {len(filtered)}/{len(self.log_entries)} | " + " | ".join(filter_info)
        else:
            stats_text = f"显示: {len(filtered)}/{len(self.log_entries)} 条日志"

        self.log_stats_var.set(stats_text)

    def search_in_module(self):
        """在当前选中的模块中搜索"""
        # 直接调用组合过滤方法
        self.apply_module_filter()

    def apply_module_filter(self):
        """应用模块内的组合过滤（搜索+时间）"""
        # 使用保存的模块名称
        if not self.current_module_name:
            selection = self.module_listbox.curselection()
            if not selection:
                messagebox.showwarning("警告", "请先选择一个模块")
                return
            index = selection[0]
            module_text = self.module_listbox.get(index)
            module_name = module_text.split(' (')[0]
            self.current_module_name = module_name
        else:
            module_name = self.current_module_name

        if module_name not in self.modules_data:
            return

        # 获取模块的所有日志
        entries = self.modules_data[module_name]
        filtered_results = []

        # 获取过滤条件
        keyword = self.module_search_var.get()
        start_time = self.module_time_start_var.get()
        end_time = self.module_time_end_var.get()

        # 清理空值
        if not start_time or start_time.strip() == "":
            start_time = None
        if not end_time or end_time.strip() == "":
            end_time = None

        # 应用过滤
        for entry in entries:
            # 时间过滤 - 使用新的时间比较方法
            if (start_time or end_time) and entry.timestamp:
                if not self.compare_log_time(entry.timestamp, start_time, end_time):
                    continue

            # 关键词搜索过滤
            if keyword:
                if self.module_search_mode_var.get() == "正则":
                    try:
                        pattern = re.compile(keyword, re.IGNORECASE)
                        if not pattern.search(entry.raw_line):
                            continue
                    except re.error as e:
                        messagebox.showerror("错误", f"正则表达式错误: {e}")
                        return
                else:
                    # 字符串搜索
                    if keyword.lower() not in entry.raw_line.lower():
                        continue

            filtered_results.append(entry)

        # 保存过滤结果
        self.current_module_filtered = filtered_results

        # 显示结果
        if filtered_results:
            self.module_log_text.clear()
            log_data = [(entry.raw_line + '\n', entry.level) for entry in filtered_results]
            self.module_log_text.set_data(log_data)

            # 更新统计信息
            level_stats = Counter(e.level for e in filtered_results)
            stats_text = f"模块: {module_name} | 过滤结果: {len(filtered_results)}条 | "
            stats_text += " | ".join([f"{level}: {count}" for level, count in level_stats.items()])

            # 添加过滤条件提示
            filter_info = []
            if keyword:
                filter_info.append(f"关键词:{keyword}")
            if start_time:
                filter_info.append(f"开始:{start_time}")
            if end_time:
                filter_info.append(f"结束:{end_time}")
            if filter_info:
                stats_text += " | 过滤: " + ", ".join(filter_info)

            self.module_stats_var.set(stats_text)
        else:
            messagebox.showinfo("过滤结果", "没有符合条件的日志")
            # 保持当前显示不变

    def reset_module_filter(self):
        """重置模块过滤条件"""
        self.module_search_var.set("")
        self.module_time_start_var.set("")
        self.module_time_end_var.set("")
        # 重新显示当前模块的所有日志
        self.on_module_select(None)

    def clear_module_search(self):
        """清除模块搜索（保留时间过滤）"""
        self.module_search_var.set("")
        # 重新应用过滤（只有时间过滤）
        self.apply_module_filter()

    def export_current_module(self):
        """导出当前选中模块的所有日志"""
        if not self.current_module_name:
            messagebox.showwarning("警告", "请先选择一个模块")
            return

        if self.current_module_name not in self.modules_data:
            messagebox.showwarning("警告", "模块数据不存在")
            return

        # 获取文件保存路径
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("日志文件", "*.log"), ("所有文件", "*.*")],
            initialfile=f"module_{self.current_module_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )

        if not filepath:
            return

        try:
            entries = self.modules_data[self.current_module_name]
            with open(filepath, 'w', encoding='utf-8') as f:
                # 写入报告头
                f.write(f"Mars日志分析报告 - 模块: {self.current_module_name}\n")
                f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 80 + "\n\n")

                # 统计信息
                level_stats = Counter(e.level for e in entries)
                f.write("日志级别统计:\n")
                for level, count in sorted(level_stats.items()):
                    f.write(f"  {level}: {count}\n")
                f.write(f"\n总计: {len(entries)} 条日志\n")
                f.write("=" * 80 + "\n\n")

                # 日志内容
                f.write("日志详情:\n")
                f.write("-" * 80 + "\n")
                for entry in entries:
                    f.write(entry.raw_line + "\n")

            messagebox.showinfo("导出成功", f"模块日志已导出到:\n{filepath}")

        except Exception as e:
            messagebox.showerror("导出失败", f"导出时发生错误: {str(e)}")

    def export_filtered_module(self):
        """导出当前模块的过滤结果"""
        if not self.current_module_name:
            messagebox.showwarning("警告", "请先选择一个模块")
            return

        # 获取当前显示的过滤结果
        # 首先检查是否有过滤条件
        keyword = self.module_search_var.get()
        start_time = self.module_time_start_var.get()
        end_time = self.module_time_end_var.get()

        has_filter = False
        if keyword or (start_time and start_time.strip()) or (end_time and end_time.strip()):
            has_filter = True

        if not has_filter:
            # 没有过滤条件，导出全部
            self.export_current_module()
            return

        # 使用保存的过滤结果，如果没有则重新应用过滤
        if self.current_module_filtered:
            filtered_results = self.current_module_filtered
        else:
            # 重新应用过滤
            self.apply_module_filter()
            filtered_results = self.current_module_filtered

        if not filtered_results:
            messagebox.showinfo("提示", "过滤结果为空，没有可导出的内容")
            return

        # 获取文件保存路径
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("日志文件", "*.log"), ("所有文件", "*.*")],
            initialfile=f"module_{self.current_module_name}_filtered_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )

        if not filepath:
            return

        try:
            # 获取模块的总条目数
            total_entries = len(self.modules_data[self.current_module_name])

            with open(filepath, 'w', encoding='utf-8') as f:
                # 写入报告头
                f.write(f"Mars日志分析报告 - 模块: {self.current_module_name} (过滤结果)\n")
                f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 80 + "\n\n")

                # 过滤条件
                f.write("过滤条件:\n")
                if keyword:
                    f.write(f"  关键词: {keyword} (模式: {self.module_search_mode_var.get()})\n")
                if start_time and start_time.strip():
                    f.write(f"  开始时间: {start_time}\n")
                if end_time and end_time.strip():
                    f.write(f"  结束时间: {end_time}\n")
                f.write("\n")

                # 统计信息
                level_stats = Counter(e.level for e in filtered_results)
                f.write("日志级别统计:\n")
                for level, count in sorted(level_stats.items()):
                    f.write(f"  {level}: {count}\n")
                f.write(f"\n过滤结果: {len(filtered_results)} / {total_entries} 条日志\n")
                f.write("=" * 80 + "\n\n")

                # 日志内容
                f.write("日志详情:\n")
                f.write("-" * 80 + "\n")
                for entry in filtered_results:
                    f.write(entry.raw_line + "\n")

            messagebox.showinfo("导出成功", f"过滤结果已导出到:\n{filepath}")

        except Exception as e:
            messagebox.showerror("导出失败", f"导出时发生错误: {str(e)}")

    def export_all_modules(self):
        """导出所有模块的日志到单独文件"""
        if not self.modules_data:
            messagebox.showwarning("警告", "没有模块数据可导出")
            return

        # 选择保存目录
        folder = filedialog.askdirectory(title="选择保存目录")
        if not folder:
            return

        try:
            exported_count = 0
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            for module_name, entries in self.modules_data.items():
                if not entries:
                    continue

                # 清理模块名中的特殊字符，用于文件名
                safe_module_name = module_name.replace('/', '_').replace('\\', '_').replace(':', '_')
                filename = f"module_{safe_module_name}_{timestamp}.txt"
                filepath = os.path.join(folder, filename)

                with open(filepath, 'w', encoding='utf-8') as f:
                    # 写入报告头
                    f.write(f"Mars日志分析报告 - 模块: {module_name}\n")
                    f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 80 + "\n\n")

                    # 统计信息
                    level_stats = Counter(e.level for e in entries)
                    f.write("日志级别统计:\n")
                    for level, count in sorted(level_stats.items()):
                        f.write(f"  {level}: {count}\n")
                    f.write(f"\n总计: {len(entries)} 条日志\n")
                    f.write("=" * 80 + "\n\n")

                    # 日志内容
                    f.write("日志详情:\n")
                    f.write("-" * 80 + "\n")
                    for entry in entries:
                        f.write(entry.raw_line + "\n")

                exported_count += 1

            messagebox.showinfo("导出成功",
                              f"已导出 {exported_count} 个模块的日志到:\n{folder}")

        except Exception as e:
            messagebox.showerror("导出失败", f"导出时发生错误: {str(e)}")

    def start_parsing(self):
        """开始解析"""
        if not self.file_groups:
            messagebox.showwarning("警告", "请先选择包含xlog文件的文件夹")
            return

        # 在新线程中执行解析
        thread = threading.Thread(target=self.parse_all_groups)
        thread.daemon = True
        thread.start()

    def parse_all_groups(self):
        """解析所有文件组 - 使用快速并行解码器"""
        try:
            self.progress_bar.start()

            total_files = sum(len(g.files) for g in self.file_groups.values())
            self.progress_var.set(f"开始解析 {total_files} 个文件...")

            # 收集所有文件路径
            all_files_map = {}  # {filepath: group}
            for base_name, group in self.file_groups.items():
                group.entries.clear()
                for filepath in group.files:
                    all_files_map[filepath] = group

            # 使用快速解码器并行处理所有文件
            def update_progress(progress, msg):
                self.progress_var.set(f"{msg} - {progress:.1f}%")

            results = self.fast_decoder.decode_files_batch(
                list(all_files_map.keys()),
                update_progress
            )

            # 处理解析结果
            for filepath, result in results.items():
                group = all_files_map[filepath]

                if result['error']:
                    self.log_queue.put(("error", f"解析文件 {os.path.basename(filepath)} 失败: {result['error']}"))
                else:
                    # 处理解析后的日志，合并多行日志
                    lines = result['lines']
                    i = 0
                    while i < len(lines):
                        line = lines[i].strip()
                        if not line:
                            i += 1
                            continue

                        # 检查是否为标准日志格式
                        if re.match(r'^\[[IWEDVF]\]\[', line):
                            full_line = line
                            j = i + 1

                            # 判断是否可能是崩溃日志 - 只检查确定的崩溃标识
                            is_potential_crash = '*** Terminating app due to uncaught exception' in line

                            # 收集续行
                            while j < len(lines):
                                next_line = lines[j].strip()
                                if not next_line:
                                    j += 1
                                    continue

                                # 新的日志条目开始
                                if re.match(r'^\[[IWEDVF]\]\[', next_line):
                                    break

                                # 崩溃日志特殊处理
                                if is_potential_crash:
                                    # 崩溃相关内容的模式
                                    is_crash_content = (
                                        '*** First throw call stack' in next_line or
                                        re.match(r'^\s*\d+\s+\S+\s+0x[0-9a-fA-F]+', next_line) or
                                        next_line.startswith('***') or
                                        'Thread' in next_line and 'crashed' in next_line.lower()
                                    )

                                    if is_crash_content:
                                        full_line += '\n' + next_line
                                        j += 1
                                    else:
                                        # 非崩溃内容，但可能是多行日志的一部分
                                        if j == i + 1:  # 紧邻的下一行
                                            full_line += '\n' + next_line
                                            j += 1
                                        else:
                                            break
                                else:
                                    # 普通多行日志
                                    full_line += '\n' + next_line
                                    j += 1

                            entry = LogEntry(full_line, os.path.basename(filepath))
                            group.entries.append(entry)
                            i = j
                        else:
                            # 非标准格式
                            entry = LogEntry(line, os.path.basename(filepath))
                            group.entries.append(entry)
                            i += 1

            # 后处理：优化崩溃日志的识别
            for group in self.file_groups.values():
                self.post_process_crash_logs(group)


            # 加载第一个组
            if self.file_groups:
                first_group = list(self.file_groups.values())[0]
                self.current_group = first_group
                # 在主线程中加载日志
                self.root.after(100, lambda: self.load_group_logs(first_group))

            self.progress_var.set(f"完成！解析了 {total_files} 个文件")
            self.log_queue.put(("info", f"成功解析 {total_files} 个文件"))

        except Exception as e:
            self.log_queue.put(("error", f"解析错误: {str(e)}"))
            import traceback
            traceback.print_exc()
        finally:
            self.progress_bar.stop()

    def analyze_logs(self):
        """分析日志内容"""
        log_levels = Counter()
        time_distribution = defaultdict(int)
        module_stats = Counter()
        module_level_stats = defaultdict(Counter)
        self.modules_data.clear()

        # 遇到崩溃日志自动创建Crash模块
        crash_entries = []

        for entry in self.log_entries:
            # 统计级别
            log_levels[entry.level] += 1

            # 统计模块
            module_stats[entry.module] += 1
            self.modules_data[entry.module].append(entry)

            # 收集崩溃日志
            if entry.is_crash or entry.level == 'CRASH':
                crash_entries.append(entry)

            # 统计模块-级别
            module_level_stats[entry.module][entry.level] += 1

            # 提取时间分布
            if entry.timestamp:
                hour_match = re.search(r'(\d{2}):\d{2}:\d{2}', entry.timestamp)
                if hour_match:
                    hour = hour_match.group(1)
                    time_distribution[f"{hour}:00"] += 1

        # 确保Crash模块存在（如果有崩溃日志）
        if crash_entries and 'Crash' not in self.modules_data:
            self.modules_data['Crash'] = crash_entries
            module_stats['Crash'] = len(crash_entries)
            for entry in crash_entries:
                module_level_stats['Crash'][entry.level] += 1

        self.analysis_results = {
            'total_lines': len(self.log_entries),
            'log_levels': dict(log_levels),
            'time_distribution': dict(time_distribution),
            'module_stats': dict(module_stats),
            'module_level_stats': {k: dict(v) for k, v in module_level_stats.items()},
            'modules': list(self.modules_data.keys()),
            'current_group': self.current_group.base_name if self.current_group else ""
        }

        # 更新模块列表
        self.update_module_list()

    def update_module_list(self):
        """更新模块列表"""
        modules = ['全部'] + sorted(list(self.modules_data.keys()))
        self.module_combo['values'] = modules

        # 更新模块列表框
        self.module_listbox.delete(0, tk.END)
        for module, entries in sorted(self.modules_data.items()):
            # 统计各级别数量
            count_stats = Counter(e.level for e in entries)
            total_count = len(entries)

            # 构建显示文本
            display_text = f"{module} ({total_count}条"

            # 优先显示崩溃数
            if count_stats.get('CRASH', 0) > 0:
                display_text += f", {count_stats['CRASH']}崩溃"
            # 其次是错误数
            elif count_stats.get('ERROR', 0) > 0:
                display_text += f", {count_stats['ERROR']}E"
            # 最后是警告数
            if count_stats.get('WARNING', 0) > 0:
                display_text += f", {count_stats['WARNING']}W"

            display_text += ")"
            self.module_listbox.insert(tk.END, display_text)

        # 恢复之前选中的模块
        if self.current_module_name:
            self.restore_module_selection()

    def restore_module_selection(self):
        """恢复模块选择"""
        if not self.current_module_name:
            return

        # 临时忽略选择事件
        self.ignore_module_selection = True

        # 查找并选中对应的模块
        for i in range(self.module_listbox.size()):
            module_text = self.module_listbox.get(i)
            module_name = module_text.split(' (')[0]
            if module_name == self.current_module_name:
                self.module_listbox.selection_clear(0, tk.END)
                self.module_listbox.selection_set(i)
                self.module_listbox.see(i)  # 确保选中项可见
                break

        # 恢复选择事件处理
        self.ignore_module_selection = False

    def on_module_select(self, event):
        """模块选择事件"""
        # 如果正在忽略选择事件，直接返回
        if self.ignore_module_selection:
            return

        selection = self.module_listbox.curselection()
        if not selection:
            # 如果失去选择，尝试恢复之前的选择
            if self.current_module_name:
                self.restore_module_selection()
            return

        index = selection[0]
        module_text = self.module_listbox.get(index)
        module_name = module_text.split(' (')[0]

        # 保存当前选中的模块
        self.current_module_name = module_name

        if module_name in self.modules_data:
            entries = self.modules_data[module_name]
            self.current_module_entries = entries  # 保存当前模块的所有日志
            self.current_module_filtered = []  # 清空过滤结果

            # 清除过滤条件（重置为初始状态）
            self.module_search_var.set("")
            self.module_time_start_var.set("")
            self.module_time_end_var.set("")

            # 更新统计信息
            level_stats = Counter(e.level for e in entries)
            stats_text = f"模块: {module_name} | 总计: {len(entries)}条 | "
            stats_text += " | ".join([f"{level}: {count}" for level, count in level_stats.items()])
            self.module_stats_var.set(stats_text)

            # 使用懒加载显示模块日志
            self.module_log_text.clear()
            log_data = [(entry.raw_line + '\n', entry.level) for entry in entries]
            self.module_log_text.set_data(log_data)

    def update_displays(self):
        """更新所有显示区域"""
        self.display_logs(self.filtered_entries)
        self.update_statistics()

        # 图表更新在后台线程执行避免卡顿
        thread = threading.Thread(target=self.update_charts)
        thread.daemon = True
        thread.start()

    def display_logs(self, entries):
        """显示日志条目"""
        # 更新统计信息
        if entries:
            level_stats = Counter(e.level for e in entries)
            stats_text = f"当前组: {self.current_group.base_name if self.current_group else '无'} | "
            stats_text += f"显示: {len(entries)}条 | "

            # 特别显示崩溃计数
            crash_count = level_stats.get('CRASH', 0)
            if crash_count > 0:
                stats_text = f"⚠️ 发现 {crash_count} 处崩溃! | " + stats_text

            stats_text += " | ".join([f"{level}: {count}" for level, count in level_stats.items()])
            self.log_stats_var.set(stats_text)
        else:
            self.log_stats_var.set("无日志数据")

        # 使用懒加载显示日志
        self.log_text.clear()
        log_data = []

        # 处理崩溃日志分组
        i = 0
        while i < len(entries):
            entry = entries[i]
            item = {}

            # 如果是崩溃日志，显示完整内容
            if entry.is_crash:
                item['prefix'] = "🔴 [CRASH] "
                item['prefix_tag'] = "CRASH"
                # 崩溃日志可能包含多行，确保完整显示
                if '\n' in entry.raw_line:
                    # 多行崩溃日志，保持格式
                    item['text'] = entry.raw_line + '\n'
                else:
                    item['text'] = entry.raw_line + '\n'
                item['tag'] = 'CRASH'
                log_data.append(item)

                # 查找后续的独立堆栈信息条目
                i += 1
                while i < len(entries) and (entries[i].is_stacktrace or entries[i].module == 'Crash'):
                    if entries[i].level == 'CRASH' or entries[i].is_stacktrace:
                        stack_item = {
                            'prefix': "  ↳ ",
                            'prefix_tag': "STACKTRACE",
                            'text': entries[i].raw_line + '\n',
                            'tag': 'STACKTRACE'
                        }
                        log_data.append(stack_item)
                    i += 1
                continue

            # 添加模块标记
            if entry.module == 'mars':
                item['prefix'] = f"[{entry.module}] "
                item['prefix_tag'] = "MODULE_MARS"
            elif entry.module == 'HY-Default':
                item['prefix'] = f"[{entry.module}] "
                item['prefix_tag'] = "MODULE_DEFAULT"

            # 如果是合并模式，显示来源文件
            if self.merge_files_var.get() and self.current_group and len(self.current_group.files) > 1:
                if 'prefix' in item:
                    item['prefix'] += f"[{entry.source_file}] "
                else:
                    item['prefix'] = f"[{entry.source_file}] "
                    item['prefix_tag'] = "DEBUG"

            item['text'] = entry.raw_line + '\n'
            item['tag'] = entry.level
            log_data.append(item)
            i += 1

        self.log_text.set_data(log_data)

    def update_statistics(self):
        """更新统计信息"""
        # 统计信息已移除，此方法暂时保留为空以避免调用错误
        pass

    def update_charts(self):
        """更新图表"""
        # 图表功能已移除，此方法暂时保留为空以避免调用错误
        pass

    def filter_logs(self, start_time=None, end_time=None):
        """过滤日志（支持时间范围）"""
        level = self.level_var.get()
        module = self.module_var.get()

        self.filtered_entries = []

        for entry in self.log_entries:
            # 级别过滤
            if level != '全部' and entry.level != level:
                continue

            # 模块过滤
            if module != '全部' and entry.module != module:
                continue

            # 时间过滤
            if start_time or end_time:
                # 使用entry.timestamp（如果存在）或从raw_line提取
                if entry.timestamp:
                    # 使用已解析的时间戳
                    if not self.compare_log_time(entry.timestamp, start_time, end_time):
                        continue
                else:
                    # 尝试从原始日志中提取时间戳
                    # 支持格式：[I][2025-09-21 +8.0 13:09:49.038]
                    import re
                    time_pattern = r'\[(\d{4}-\d{2}-\d{2}\s+[+\-]?\d+\.?\d*\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?)\]'
                    match = re.search(time_pattern, entry.raw_line)
                    if match:
                        timestamp = match.group(1)
                        if not self.compare_log_time(timestamp, start_time, end_time):
                            continue

            self.filtered_entries.append(entry)

        self.display_logs(self.filtered_entries)

    def search_logs(self):
        """搜索日志（支持正则表达式）"""
        keyword = self.search_var.get()
        if not keyword:
            self.filter_logs()
            return

        search_results = []

        # 根据搜索模式进行搜索
        if self.search_mode_var.get() == "正则":
            try:
                pattern = re.compile(keyword, re.IGNORECASE)
                for entry in self.filtered_entries:
                    if pattern.search(entry.raw_line):
                        search_results.append(entry)
            except re.error as e:
                messagebox.showerror("错误", f"正则表达式错误: {e}")
                return
        else:
            # 字符串搜索
            keyword_lower = keyword.lower()
            for entry in self.filtered_entries:
                if keyword_lower in entry.raw_line.lower():
                    search_results.append(entry)

        self.display_logs(search_results)

        # 高亮搜索关键词
        if search_results:
            start_idx = "1.0"
            while True:
                pos = self.log_text.search(keyword, start_idx, tk.END, nocase=True)
                if not pos:
                    break
                end_idx = f"{pos}+{len(keyword)}c"
                self.log_text.tag_add("HIGHLIGHT", pos, end_idx)
                start_idx = end_idx

        messagebox.showinfo("搜索结果", f"找到{len(search_results)}条匹配的日志")

    def clear_filter(self):
        """清除过滤条件"""
        self.search_var.set("")
        self.level_var.set("全部")
        self.module_var.set("全部")
        self.global_time_start_var.set("")
        self.global_time_end_var.set("")
        self.filtered_entries = self.log_entries.copy()
        self.display_logs(self.filtered_entries)

    def export_current_view(self):
        """导出当前视图的日志"""
        if not self.filtered_entries:
            messagebox.showwarning("警告", "没有可导出的数据")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".log",
            filetypes=[("日志文件", "*.log"), ("文本文件", "*.txt"), ("所有文件", "*.*")]
        )

        if not filename:
            return

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"# Mars日志导出 - 当前视图\n")
                f.write(f"# 导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                if self.current_group:
                    f.write(f"# 文件组: {self.current_group.base_name}\n")
                    f.write(f"# 包含文件: {', '.join([os.path.basename(f) for f in self.current_group.files])}\n")
                f.write(f"# 总条数: {len(self.filtered_entries)}\n")
                f.write("#" * 60 + "\n\n")

                for entry in self.filtered_entries:
                    f.write(entry.raw_line + '\n')

            messagebox.showinfo("成功", f"当前视图已导出到: {filename}")

        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {str(e)}")

    def export_grouped_report(self):
        """导出分组报告"""
        if not self.modules_data:
            messagebox.showwarning("警告", "没有可导出的数据")
            return

        folder = filedialog.askdirectory(title="选择导出目录")
        if not folder:
            return

        try:
            # 创建导出目录
            export_dir = os.path.join(folder, f"mars_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            os.makedirs(export_dir, exist_ok=True)

            # 导出每个模块的日志
            for module, entries in self.modules_data.items():
                if not entries:
                    continue

                safe_module_name = re.sub(r'[<>:"/\\|?*]', '_', module)
                filename = os.path.join(export_dir, f"{safe_module_name}.log")

                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"# 模块: {module}\n")
                    f.write(f"# 日志条数: {len(entries)}\n")

                    level_stats = Counter(e.level for e in entries)
                    f.write(f"# 级别分布: {dict(level_stats)}\n")
                    f.write("#" * 60 + "\n\n")

                    for entry in entries:
                        f.write(entry.raw_line + '\n')

            # 生成汇总报告
            summary_file = os.path.join(export_dir, "_summary.txt")
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write("Mars日志分组导出汇总\n")
                f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                if self.current_group:
                    f.write(f"文件组: {self.current_group.base_name}\n")
                f.write("=" * 60 + "\n\n")

                f.write(f"总模块数: {len(self.modules_data)}\n")
                f.write(f"总日志数: {sum(len(entries) for entries in self.modules_data.values())}\n\n")

                f.write("模块详情:\n")
                f.write("-" * 40 + "\n")

                for module, entries in sorted(self.modules_data.items(),
                                             key=lambda x: len(x[1]), reverse=True):
                    level_stats = Counter(e.level for e in entries)
                    f.write(f"\n{module}:\n")
                    f.write(f"  总计: {len(entries)}条\n")
                    for level, count in sorted(level_stats.items()):
                        f.write(f"  {level}: {count}条\n")

            messagebox.showinfo("成功", f"分组报告已导出到: {export_dir}")

        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {str(e)}")

    def export_full_report(self):
        """导出完整分析报告"""
        if not self.analysis_results:
            messagebox.showwarning("警告", "没有可导出的数据")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("JSON文件", "*.json"), ("所有文件", "*.*")]
        )

        if not filename:
            return

        try:
            if filename.endswith('.json'):
                # 导出为JSON格式
                export_data = {
                    'export_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'file_groups': {
                        name: {
                            'files': group.files,
                            'entry_count': len(group.entries)
                        } for name, group in self.file_groups.items()
                    },
                    'analysis': self.analysis_results,
                    'modules': {module: len(entries) for module, entries in self.modules_data.items()}
                }
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, ensure_ascii=False, indent=2)
            else:
                # 导出为文本格式
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("=" * 60 + "\n")
                    f.write("Mars日志完整分析报告\n")
                    f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 60 + "\n\n")

                    # 文件组信息
                    f.write("文件组信息:\n")
                    f.write("-" * 40 + "\n")
                    for name, group in sorted(self.file_groups.items()):
                        f.write(f"\n{name}:\n")
                        f.write(f"  文件数: {len(group.files)}\n")
                        f.write(f"  日志数: {len(group.entries)}\n")
                        for filepath in group.files:
                            f.write(f"    - {os.path.basename(filepath)}\n")

                    f.write(f"\n总日志行数: {self.analysis_results.get('total_lines', 0)}\n")
                    f.write(f"模块总数: {len(self.analysis_results.get('modules', []))}\n\n")

                    f.write("日志级别分布:\n")
                    f.write("-" * 40 + "\n")
                    for level, count in sorted(self.analysis_results.get('log_levels', {}).items()):
                        percentage = count / self.analysis_results['total_lines'] * 100 if self.analysis_results['total_lines'] > 0 else 0
                        f.write(f"{level:10s}: {count:6d} ({percentage:.1f}%)\n")

                    f.write("\n模块分布:\n")
                    f.write("-" * 40 + "\n")
                    for module, count in sorted(self.analysis_results.get('module_stats', {}).items(),
                                               key=lambda x: x[1], reverse=True):
                        percentage = count / self.analysis_results['total_lines'] * 100 if self.analysis_results['total_lines'] > 0 else 0
                        f.write(f"{module:30s}: {count:6d} ({percentage:.1f}%)\n")

                    if self.analysis_results.get('time_distribution'):
                        f.write("\n时间分布:\n")
                        f.write("-" * 40 + "\n")
                        for time, count in sorted(self.analysis_results['time_distribution'].items()):
                            f.write(f"{time}: {count}\n")

            messagebox.showinfo("成功", f"完整报告已导出到: {filename}")

        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {str(e)}")

    def process_log_queue(self):
        """处理日志队列中的消息"""
        try:
            while True:
                msg_type, msg = self.log_queue.get_nowait()
                if msg_type == "error":
                    messagebox.showerror("错误", msg)
                elif msg_type == "warning":
                    messagebox.showwarning("警告", msg)
                elif msg_type == "info":
                    messagebox.showinfo("信息", msg)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_log_queue)

    def create_ips_analyzer_tab(self):
        """创建IPS崩溃解析标签页"""
        ips_frame = ttk.Frame(self.main_notebook, padding="10")
        self.main_notebook.add(ips_frame, text="IPS崩溃解析")

        # 配置网格权重
        ips_frame.columnconfigure(1, weight=1)
        ips_frame.rowconfigure(3, weight=1)

        # ========== 文件选择区域 ==========
        file_select_frame = ttk.LabelFrame(ips_frame, text="文件选择", padding="10")
        file_select_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        file_select_frame.columnconfigure(1, weight=1)

        # IPS文件选择
        ttk.Label(file_select_frame, text="IPS文件:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.ips_file_var = tk.StringVar()
        ttk.Entry(file_select_frame, textvariable=self.ips_file_var, width=60).grid(row=0, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))
        ttk.Button(file_select_frame, text="选择IPS", command=self.select_ips_file).grid(row=0, column=2, padx=5, pady=5)

        # dSYM文件选择
        ttk.Label(file_select_frame, text="dSYM文件:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.dsym_file_var = tk.StringVar()
        ttk.Entry(file_select_frame, textvariable=self.dsym_file_var, width=60).grid(row=1, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))
        ttk.Button(file_select_frame, text="选择dSYM", command=self.select_dsym_file).grid(row=1, column=2, padx=5, pady=5)

        # ========== 控制按钮区域 ==========
        control_frame = ttk.Frame(ips_frame)
        control_frame.grid(row=1, column=0, columnspan=2, pady=10)

        # 创建按钮样式（如果还没有）
        try:
            btn_style = ttk.Style()
            btn_style.configure('Large.TButton', padding=(10, 5, 10, 5), font=('', 11))
        except:
            pass

        self.analyze_button = ttk.Button(control_frame, text="解析崩溃日志", command=self.analyze_ips_crash,
                   style='Large.TButton')
        self.analyze_button.pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="清空结果", command=self.clear_ips_result,
                   style='Large.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="导出报告", command=self.export_ips_report,
                   style='Large.TButton').pack(side=tk.LEFT, padx=5)

        # ========== 信息显示区域 ==========
        info_frame = ttk.LabelFrame(ips_frame, text="崩溃信息", padding="5")
        info_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        info_frame.columnconfigure(1, weight=1)

        # 显示基本信息
        self.ips_info_text = tk.Text(info_frame, height=6, wrap=tk.WORD)
        self.ips_info_text.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=5)

        # ========== 结果显示区域 ==========
        result_frame = ttk.LabelFrame(ips_frame, text="解析结果", padding="5")
        result_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)

        # 创建结果显示文本框
        self.ips_result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD, width=100, height=25)
        self.ips_result_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)

        # 配置文本标签样式
        self.ips_result_text.tag_config("header", font=("Courier", 12, "bold"), foreground="#0066CC")
        self.ips_result_text.tag_config("thread", font=("Courier", 11, "bold"), foreground="#009900")
        self.ips_result_text.tag_config("crashed", foreground="#CC0000", font=("Courier", 11, "bold"))
        self.ips_result_text.tag_config("symbol", foreground="#6600CC")
        self.ips_result_text.tag_config("address", foreground="#999999")
        self.ips_result_text.tag_config("info", foreground="#0099CC")
        self.ips_result_text.tag_config("warning", foreground="#FF9900", font=("Courier", 11, "bold"))
        self.ips_result_text.tag_config("success", foreground="#00AA00", font=("Courier", 11, "bold"))
        # 区分应用符号和系统符号
        self.ips_result_text.tag_config("app_symbol", foreground="#0066CC", font=("Courier", 11, "bold"))
        self.ips_result_text.tag_config("system_symbol", foreground="#666666", font=("Courier", 11))

    def select_ips_file(self):
        """选择IPS文件"""
        filename = filedialog.askopenfilename(
            title="选择IPS崩溃日志文件",
            filetypes=[("IPS文件", "*.ips"), ("崩溃日志", "*.crash"), ("所有文件", "*.*")]
        )
        if filename:
            self.ips_file_var.set(filename)
            self.parse_ips_basic_info(filename)

    def select_dsym_file(self):
        """选择dSYM文件"""
        import platform
        import os

        # 在macOS上使用特殊的文件选择方式
        if platform.system() == 'Darwin':  # macOS
            try:
                # 使用subprocess调用osascript来选择文件（支持选择包文件）
                import subprocess

                # AppleScript命令：允许选择任何类型的文件，包括包
                script = '''
                tell application "Finder"
                    activate
                    set selectedFile to choose file with prompt "选择dSYM文件（如：huhuAudio.app.dSYM）" of type {"dSYM"} invisibles false without multiple selections allowed
                    return POSIX path of selectedFile
                end tell
                '''

                # 执行AppleScript
                result = subprocess.run(['osascript', '-e', script],
                                      capture_output=True,
                                      text=True,
                                      timeout=60)

                if result.returncode == 0:
                    filename = result.stdout.strip()
                else:
                    # 如果AppleScript失败，使用备用方案
                    filename = self.select_dsym_fallback()

            except Exception as e:
                print(f"AppleScript选择失败: {e}")
                # 使用备用方案
                filename = self.select_dsym_fallback()

        else:
            # 其他系统使用标准文件选择器
            filename = filedialog.askopenfilename(
                title="选择dSYM符号文件",
                filetypes=[
                    ("dSYM文件", "*.dSYM"),
                    ("所有文件", "*.*")
                ]
            )

        if filename:
            # 去除路径末尾的斜杠（macOS目录选择器会添加）
            filename = filename.rstrip('/')

            # 验证是否是dSYM文件（支持.dSYM和.app.dSYM格式）
            if not (filename.endswith('.dSYM') or filename.endswith('.app.dSYM')):
                # 检查路径中是否包含.dSYM
                if '.dSYM' not in filename:
                    result = messagebox.askyesno(
                        "确认",
                        f"选择的文件名不包含.dSYM:\n{filename}\n\n是否继续？"
                    )
                    if not result:
                        return

            self.dsym_file_var.set(filename)
            # 验证dSYM的有效性
            if self.validate_dsym(filename):
                # 更新按钮文本表示可以符号化
                if hasattr(self, 'analyze_button'):
                    self.analyze_button.config(text="解析并符号化")
            else:
                messagebox.showwarning("警告", "选择的文件可能不是有效的dSYM文件")

    def select_dsym_fallback(self):
        """备用的dSYM选择方法"""
        # 让用户选择包含dSYM的父目录
        parent_dir = filedialog.askdirectory(
            title="选择包含dSYM文件的目录"
        )

        if parent_dir:
            import os
            # 列出目录中的所有.dSYM文件
            dsym_files = []
            for item in os.listdir(parent_dir):
                if '.dSYM' in item:
                    full_path = os.path.join(parent_dir, item)
                    if os.path.isdir(full_path):
                        dsym_files.append(item)

            if dsym_files:
                if len(dsym_files) == 1:
                    # 只有一个dSYM文件，直接使用
                    return os.path.join(parent_dir, dsym_files[0])
                else:
                    # 多个dSYM文件，让用户选择
                    from tkinter import Toplevel, Listbox, Button, Label, SINGLE

                    select_window = Toplevel(self.root)
                    select_window.title("选择dSYM文件")
                    select_window.geometry("500x400")

                    Label(select_window, text="找到以下dSYM文件，请选择：").pack(pady=10)

                    listbox = Listbox(select_window, selectmode=SINGLE, width=60, height=15)
                    listbox.pack(padx=10, pady=10)

                    for dsym in dsym_files:
                        listbox.insert(tk.END, dsym)

                    if dsym_files:  # 默认选中第一个
                        listbox.selection_set(0)

                    selected_file = [None]

                    def on_select():
                        selection = listbox.curselection()
                        if selection:
                            selected_file[0] = dsym_files[selection[0]]
                        select_window.destroy()

                    def on_cancel():
                        select_window.destroy()

                    button_frame = ttk.Frame(select_window)
                    button_frame.pack(pady=5)
                    Button(button_frame, text="选择", command=on_select, width=10).pack(side=tk.LEFT, padx=5)
                    Button(button_frame, text="取消", command=on_cancel, width=10).pack(side=tk.LEFT, padx=5)

                    select_window.wait_window()

                    if selected_file[0]:
                        return os.path.join(parent_dir, selected_file[0])
            else:
                messagebox.showwarning("未找到dSYM", "所选目录中没有找到.dSYM文件")

        return None

    def validate_dsym(self, dsym_path):
        """验证dSYM文件的有效性"""
        import os
        # 检查是否是有效的dSYM目录结构
        if os.path.isdir(dsym_path):
            dwarf_path = os.path.join(dsym_path, "Contents", "Resources", "DWARF")
            if os.path.exists(dwarf_path):
                # 列出DWARF目录中的文件
                try:
                    dwarf_files = os.listdir(dwarf_path)
                    if dwarf_files:
                        print(f"找到DWARF符号文件: {', '.join(dwarf_files)}")
                        return True
                except:
                    pass

            # 也检查Info.plist是否存在
            info_path = os.path.join(dsym_path, "Contents", "Info.plist")
            if os.path.exists(info_path):
                print("找到dSYM Info.plist")
                return True

        # 如果不是标准的dSYM结构，但用户坚持使用，也允许
        if os.path.exists(dsym_path):
            print(f"使用非标准dSYM路径: {dsym_path}")
            return True

        # 完全无效的路径
        messagebox.showwarning("警告", "选择的路径不存在")
        self.dsym_file_var.set("")
        return False

    def parse_ips_basic_info(self, filename):
        """解析并显示IPS文件的基本信息"""
        try:
            # IPS文件通常是UTF-8编码的JSON
            content = None

            # 首先尝试UTF-8
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                # 如果UTF-8失败，尝试带BOM的UTF-8
                try:
                    with open(filename, 'r', encoding='utf-8-sig') as f:
                        content = f.read()
                except:
                    # 最后尝试二进制读取
                    with open(filename, 'rb') as f:
                        raw_content = f.read()
                        # 检查文件开头，判断格式
                        if raw_content.startswith(b'{"'):
                            content = raw_content.decode('utf-8', errors='ignore')
                        else:
                            content = raw_content.decode('latin-1', errors='ignore')

            # 清空信息框
            self.ips_info_text.delete(1.0, tk.END)

            # 提取基本信息
            info_lines = []

            # IPS文件具有特殊格式：第一行是摘要JSON，后面是详细JSON
            import json
            lines = content.strip().split('\n')

            if lines and lines[0].startswith('{'):
                try:
                    # 解析第一行的摘要信息
                    summary = json.loads(lines[0])
                    info_lines.append(f"文件类型: iOS崩溃报告 (IPS)")
                    info_lines.append(f"应用名称: {summary.get('app_name', 'Unknown')}")
                    info_lines.append(f"应用版本: {summary.get('app_version', 'Unknown')}")
                    info_lines.append(f"Build版本: {summary.get('build_version', 'Unknown')}")
                    info_lines.append(f"Bundle ID: {summary.get('bundleID', 'Unknown')}")
                    info_lines.append(f"时间戳: {summary.get('timestamp', 'Unknown')}")
                    info_lines.append(f"系统版本: {summary.get('os_version', 'Unknown')}")
                    info_lines.append(f"Bug类型: {summary.get('bug_type', 'Unknown')}")

                    # 如果有第二个JSON对象（详细信息）
                    if len(lines) > 1:
                        detail_json = '\n'.join(lines[1:])
                        if detail_json.strip().startswith('{'):
                            try:
                                detail = json.loads(detail_json)
                                # 从详细信息中提取额外信息
                                if 'exception' in detail:
                                    exception = detail['exception']
                                    info_lines.append(f"异常类型: {exception.get('type', 'Unknown')}")
                                    info_lines.append(f"异常信号: {exception.get('signal', 'Unknown')}")
                                if 'termination' in detail:
                                    term = detail['termination']
                                    info_lines.append(f"终止原因: {term.get('indicator', 'Unknown')}")
                            except:
                                pass

                except json.JSONDecodeError:
                    # 不是标准IPS格式，尝试作为单个JSON
                    try:
                        data = json.loads(content)
                        info_lines.append(f"文件类型: iOS崩溃报告 (JSON)")
                        info_lines.append(f"进程名称: {data.get('procName', 'Unknown')}")
                        info_lines.append(f"进程ID: {data.get('pid', 'Unknown')}")
                        info_lines.append(f"时间: {data.get('captureTime', 'Unknown')}")
                    except:
                        info_lines.append("文件类型: 非标准格式崩溃文件")

            # 尝试解析为文本格式的崩溃日志
            else:
                # 查找关键信息
                import re

                # 查找进程信息
                process_match = re.search(r'Process:\s*(.+?)[\[\n]', content)
                if process_match:
                    info_lines.append(f"进程: {process_match.group(1).strip()}")

                # 查找崩溃类型
                exception_match = re.search(r'Exception Type:\s*(.+)', content)
                if exception_match:
                    info_lines.append(f"异常类型: {exception_match.group(1).strip()}")

                # 查找崩溃原因
                reason_match = re.search(r'Termination Reason:\s*(.+)', content)
                if reason_match:
                    info_lines.append(f"终止原因: {reason_match.group(1).strip()}")

                # 查找时间
                date_match = re.search(r'Date/Time:\s*(.+)', content)
                if date_match:
                    info_lines.append(f"时间: {date_match.group(1).strip()}")

                if info_lines:
                    info_lines.insert(0, "文件类型: 文本格式崩溃报告")
                else:
                    info_lines.append("文件类型: 未识别的IPS格式")
                    info_lines.append("提示: 文件可能是二进制格式或加密的")

            # 显示信息
            if info_lines:
                self.ips_info_text.insert(tk.END, '\n'.join(info_lines))
            else:
                self.ips_info_text.insert(tk.END, "无法解析IPS文件信息")

        except Exception as e:
            self.ips_info_text.delete(1.0, tk.END)
            self.ips_info_text.insert(tk.END, f"读取文件失败: {str(e)}")

    def analyze_ips_crash(self):
        """解析IPS崩溃日志"""
        ips_file = self.ips_file_var.get()
        if not ips_file:
            messagebox.showwarning("警告", "请先选择IPS文件")
            return

        # 清空之前的结果
        self.ips_result_text.delete(1.0, tk.END)

        # 禁用按钮，防止重复点击
        self.analyze_button.config(state='disabled', text='正在解析...')

        # 显示进度提示
        self.ips_result_text.insert(tk.END, "正在解析崩溃日志，请稍候...\n", "info")
        self.ips_result_text.update()

        # 在后台线程中执行解析
        thread = threading.Thread(target=self._analyze_ips_crash_thread, args=(ips_file,))
        thread.daemon = True
        thread.start()

    def _analyze_ips_crash_thread(self, ips_file):
        """在后台线程中解析IPS崩溃日志"""
        try:
            # 使用新的IPS解析器
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'tools'))
            from ips_parser import IPSParser, IPSSymbolicator

            # 解析IPS文件
            parser = IPSParser()
            if not parser.parse_file(ips_file):
                # 回退到旧方法
                self.root.after(0, self._analyze_ips_crash_fallback_thread, ips_file)
                return

            # 获取信息
            info = parser.get_crash_info()
            dsym_file = self.dsym_file_var.get()

            # 准备显示内容
            result_data = {
                'info': info,
                'parser': parser,
                'dsym_file': dsym_file
            }

            # 如果有dSYM文件，进行符号化
            if dsym_file and os.path.exists(dsym_file):
                symbolicator = IPSSymbolicator(parser)
                if symbolicator.set_dsym(dsym_file):
                    result_data['symbolicated_content'] = symbolicator.symbolicate()
                    result_data['is_symbolicated'] = True
                else:
                    result_data['crash_content'] = parser.to_crash_format(with_tags=True)
                    result_data['is_symbolicated'] = False
            else:
                result_data['crash_content'] = parser.to_crash_format(with_tags=True)
                result_data['is_symbolicated'] = False

            # 在主线程中更新UI
            self.root.after(0, self._update_ips_result_ui, result_data)
            return

        except ImportError:
            # 如果新解析器不可用，回退到原来的方法
            self.root.after(0, self._analyze_ips_crash_fallback_thread, ips_file)
        except Exception as e:
            # 错误处理
            self.root.after(0, self._show_ips_error, str(e))
            self.root.after(0, self._analyze_ips_crash_fallback_thread, ips_file)

    def _update_ips_result_ui(self, result_data):
        """在主线程中更新IPS解析结果UI"""
        # 清空之前的内容
        self.ips_result_text.delete(1.0, tk.END)

        info = result_data['info']

        # 显示基本信息
        self.ips_result_text.insert(tk.END, "\n===== 崩溃信息 =====\n", "header")
        self.ips_result_text.insert(tk.END, f"应用: {info['app_name']} v{info['app_version']}\n")
        self.ips_result_text.insert(tk.END, f"Bundle ID: {info['bundle_id']}\n")
        self.ips_result_text.insert(tk.END, f"时间: {info['timestamp']}\n")
        self.ips_result_text.insert(tk.END, f"系统: {info['os_version']}\n")

        if 'exception_type' in info:
            self.ips_result_text.insert(tk.END, f"异常类型: {info['exception_type']}\n", "crashed")
            self.ips_result_text.insert(tk.END, f"异常代码: {info['exception_codes']}\n")

        if 'termination_reason' in info:
            self.ips_result_text.insert(tk.END, f"终止原因: {info['termination_reason']}\n")

        self.ips_result_text.insert(tk.END, f"崩溃线程: {info['crashed_thread']}\n\n")

        # 显示崩溃报告
        if result_data.get('is_symbolicated'):
            self.ips_result_text.insert(tk.END, "\n===== 符号化后的崩溃报告 =====\n\n", "header")
            self.display_ips_with_colors(result_data['symbolicated_content'], info['bundle_id'])
        else:
            self.ips_result_text.insert(tk.END, "\n===== 崩溃报告 =====\n\n", "header")
            self.display_ips_with_colors(result_data['crash_content'], info['bundle_id'])

        # 恢复按钮状态
        self.analyze_button.config(state='normal', text='解析崩溃日志')

    def _show_ips_error(self, error_msg):
        """显示IPS解析错误"""
        self.ips_result_text.insert(tk.END, f"\n⚠️ 解析出错: {error_msg}\n", "warning")

    def _analyze_ips_crash_fallback_thread(self, ips_file):
        """IPS解析的回退方法（线程版本）"""
        # 在新线程中执行
        thread = threading.Thread(target=self._analyze_ips_crash_fallback_worker, args=(ips_file,))
        thread.daemon = True
        thread.start()

    def _analyze_ips_crash_fallback_worker(self, ips_file):
        """IPS解析的回退方法（工作线程）"""
        try:
            dsym_file = self.dsym_file_var.get()

            # 如果选择了dSYM文件，尝试符号化
            if dsym_file and os.path.exists(dsym_file):
                # 使用MacSymbolicator方法进行符号化
                symbolicated_content = self.symbolicate_crash(ips_file, dsym_file)
                if symbolicated_content:
                    # 在主线程中显示符号化结果
                    self.root.after(0, self._display_symbolicated_result, symbolicated_content)
                    return
                else:
                    # 符号化失败，提示用户
                    self.root.after(0, lambda: self.ips_result_text.insert(tk.END, "\n⚠️ 符号化失败，显示原始内容\n", "warning"))

            # 读取原始内容
            content = None
            encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'gb2312', 'gbk']

            for encoding in encodings:
                try:
                    with open(ips_file, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue

            if content is None:
                # 如果所有编码都失败，尝试二进制读取
                with open(ips_file, 'rb') as f:
                    raw_content = f.read()
                    content = raw_content.decode('utf-8', errors='ignore')

            # 在主线程中显示内容
            self.root.after(0, self._display_fallback_result, content, ips_file)

        except Exception as e:
            # 显示错误
            self.root.after(0, lambda: self.ips_result_text.insert(tk.END, f"\n错误: {str(e)}\n", "error"))
            self.root.after(0, lambda: self.analyze_button.config(state='normal', text='解析崩溃日志'))

    def _display_symbolicated_result(self, symbolicated_content):
        """显示符号化后的结果"""
        self.display_symbolicated_crash(symbolicated_content)
        self.analyze_button.config(state='normal', text='解析崩溃日志')

    def _display_fallback_result(self, content, ips_file):
        """显示回退方法的结果"""
        # 清空之前的内容
        self.ips_result_text.delete(1.0, tk.END)

        # 尝试解析JSON格式的IPS文件
        try:
            ips_data = json.loads(content)
            # 转换为Crash格式
            crash_content = self.translate_ips_to_crash(content)
            if crash_content:
                # 提取Bundle ID用于高亮
                bundle_id = ips_data.get('bundleID', '')
                if not bundle_id and 'identifier' in ips_data:
                    bundle_id = ips_data['identifier']

                # 使用带颜色区分的显示
                self.display_ips_with_colors(crash_content, bundle_id)
            else:
                # 无法转换，显示原始内容
                self.ips_result_text.insert(tk.END, content)

        except json.JSONDecodeError:
            # 不是JSON格式，直接显示
            # 判断是否已经是Crash格式
            if 'Thread' in content and 'Binary Images:' in content:
                # 已经是Crash格式，直接使用颜色显示
                bundle_id = self.extract_bundle_id_from_crash(content)
                self.display_ips_with_colors(content, bundle_id)
            else:
                # 显示原始内容
                self.ips_result_text.insert(tk.END, content)

        # 恢复按钮状态
        self.analyze_button.config(state='normal', text='解析崩溃日志')

    def _analyze_ips_crash_fallback(self, ips_file):
        """IPS解析的回退方法"""
        dsym_file = self.dsym_file_var.get()

        # 如果选择了dSYM文件，尝试符号化
        if dsym_file and os.path.exists(dsym_file):
            # 使用MacSymbolicator方法进行符号化
            symbolicated_content = self.symbolicate_crash(ips_file, dsym_file)
            if symbolicated_content:
                # 如果符号化成功，使用符号化后的内容
                self.display_symbolicated_crash(symbolicated_content)
                return
            else:
                # 符号化失败，提示用户
                self.ips_result_text.insert(tk.END, "\n⚠️ 符号化失败，显示原始内容\n", "warning")

        try:
            # 尝试多种编码读取文件
            content = None
            encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'gb2312', 'gbk']

            for encoding in encodings:
                try:
                    with open(ips_file, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue

            if content is None:
                # 如果所有编码都失败，尝试二进制读取
                with open(ips_file, 'rb') as f:
                    raw_content = f.read()
                    content = raw_content.decode('utf-8', errors='ignore')

            # 清空结果区域
            self.ips_result_text.delete(1.0, tk.END)

            # IPS文件的特殊格式：第一行是摘要，后面是详细JSON
            import json
            lines = content.strip().split('\n')

            if lines and lines[0].startswith('{'):
                try:
                    # 解析第一行摘要
                    summary = json.loads(lines[0])

                    # 解析详细信息（从第二行开始）
                    if len(lines) > 1:
                        detail_json = '\n'.join(lines[1:])
                        if detail_json.strip().startswith('{'):
                            detail = json.loads(detail_json)
                            # 合并摘要和详细信息
                            merged_data = {**summary, **detail}
                            self.display_ips_json_crash(merged_data)
                        else:
                            # 只有摘要信息
                            self.display_ips_json_crash(summary)
                    else:
                        # 只有一行JSON
                        self.display_ips_json_crash(summary)

                except json.JSONDecodeError:
                    # 不是IPS格式，尝试作为单个JSON解析
                    try:
                        data = json.loads(content)
                        self.display_ips_json_crash(data)
                    except:
                        # JSON解析完全失败，作为文本处理
                        self.ips_result_text.insert(tk.END, "警告: 无法解析为IPS格式，显示原始内容\n\n", "header")
                        self.display_text_crash(content)
            else:
                # 尝试解析文本格式的崩溃日志
                self.display_text_crash(content)

        except Exception as e:
            self.ips_result_text.delete(1.0, tk.END)
            self.ips_result_text.insert(tk.END, f"解析错误: {str(e)}\n\n", "crashed")
            self.ips_result_text.insert(tk.END, "请确认文件是有效的IPS崩溃日志文件")

    def display_ips_json_crash(self, data):
        """显示JSON格式的IPS崩溃信息"""
        self.ips_result_text.insert(tk.END, "===== 崩溃摘要 =====\n", "header")

        # 显示基本信息
        app_name = data.get('app_name') or data.get('procName', 'Unknown')
        app_version = data.get('app_version') or data.get('version', 'Unknown')
        build_version = data.get('build_version', '')
        bundle_id = data.get('bundleID', '')

        self.ips_result_text.insert(tk.END, f"应用名称: {app_name}\n")
        self.ips_result_text.insert(tk.END, f"应用版本: {app_version}")
        if build_version:
            self.ips_result_text.insert(tk.END, f" (Build {build_version})")
        self.ips_result_text.insert(tk.END, "\n")
        if bundle_id:
            self.ips_result_text.insert(tk.END, f"Bundle ID: {bundle_id}\n")

        # 时间信息
        timestamp = data.get('timestamp') or data.get('captureTime', 'Unknown')
        self.ips_result_text.insert(tk.END, f"崩溃时间: {timestamp}\n")

        # 系统信息
        os_version = data.get('os_version', '')
        if os_version:
            self.ips_result_text.insert(tk.END, f"系统版本: {os_version}\n")
        elif 'osVersion' in data:
            os_info = data['osVersion']
            if isinstance(os_info, dict):
                self.ips_result_text.insert(tk.END, f"系统版本: {os_info.get('train', '')} ({os_info.get('build', '')})\n")

        # 异常信息
        if 'exception' in data:
            exception = data['exception']
            self.ips_result_text.insert(tk.END, f"\n异常类型: {exception.get('type', 'Unknown')}\n")
            self.ips_result_text.insert(tk.END, f"异常信号: {exception.get('signal', 'Unknown')}\n")
            self.ips_result_text.insert(tk.END, f"异常代码: {exception.get('codes', 'Unknown')}\n")

        # 终止信息
        if 'termination' in data:
            term = data['termination']
            self.ips_result_text.insert(tk.END, f"\n终止指示: {term.get('indicator', 'Unknown')}\n")
            self.ips_result_text.insert(tk.END, f"终止进程: {term.get('byProc', 'Unknown')}\n")

        self.ips_result_text.insert(tk.END, "\n")

        # 查找崩溃的线程
        threads = data.get('threads', [])
        crashed_thread = None
        for thread in threads:
            if thread.get('triggered', False):
                crashed_thread = thread
                break

        if crashed_thread:
            self.ips_result_text.insert(tk.END, "===== 崩溃线程堆栈 =====\n", "header")
            self.ips_result_text.insert(tk.END, f"Thread {crashed_thread.get('index', '?')} (Crashed):\n", "crashed")

            frames = crashed_thread.get('frames', [])
            for i, frame in enumerate(frames):
                image_index = frame.get('imageIndex', '')
                offset = frame.get('imageOffset', '')

                # 获取镜像名称
                images = data.get('usedImages', [])
                image_name = 'Unknown'
                if isinstance(image_index, int) and image_index < len(images):
                    image_name = images[image_index].get('name', 'Unknown').split('/')[-1]

                # 格式化输出
                self.ips_result_text.insert(tk.END, f"{i:3} {image_name:30} ", "address")
                self.ips_result_text.insert(tk.END, f"0x{offset:016x}\n", "address")

        # 显示所有线程摘要
        self.ips_result_text.insert(tk.END, "\n===== 所有线程 =====\n", "header")
        for thread in threads[:10]:  # 只显示前10个线程
            triggered = " (Crashed)" if thread.get('triggered', False) else ""
            name = thread.get('name', '')
            if name:
                name = f" [{name}]"
            self.ips_result_text.insert(tk.END, f"Thread {thread.get('index', '?')}{name}{triggered}\n", "thread")

    def display_text_crash(self, content):
        """显示文本格式的崩溃日志"""
        import re

        # 尝试解析并格式化文本崩溃日志
        lines = content.split('\n')

        # 查找关键部分
        in_thread_section = False
        in_crashed_thread = False
        crashed_thread_num = None

        for line in lines:
            # 检测崩溃线程
            if 'Crashed Thread:' in line:
                match = re.search(r'Crashed Thread:\s*(\d+)', line)
                if match:
                    crashed_thread_num = match.group(1)

            # 检测线程部分
            thread_match = re.match(r'^Thread\s+(\d+)', line)
            if thread_match:
                thread_num = thread_match.group(1)
                if thread_num == crashed_thread_num:
                    self.ips_result_text.insert(tk.END, line + '\n', "crashed")
                    in_crashed_thread = True
                else:
                    self.ips_result_text.insert(tk.END, line + '\n', "thread")
                    in_crashed_thread = False
                in_thread_section = True
                continue

            # 处理堆栈帧
            if in_thread_section and re.match(r'^\d+\s+', line):
                if in_crashed_thread:
                    self.ips_result_text.insert(tk.END, line + '\n', "crashed")
                else:
                    self.ips_result_text.insert(tk.END, line + '\n', "address")
                continue

            # 高亮显示关键信息
            if any(keyword in line for keyword in ['Process:', 'Exception Type:', 'Exception Codes:',
                                                   'Termination Reason:', 'Triggered by Thread:']):
                self.ips_result_text.insert(tk.END, line + '\n', "header")
            else:
                self.ips_result_text.insert(tk.END, line + '\n')

    def symbolicate_crash(self):
        """符号化崩溃日志"""
        ips_file = self.ips_file_var.get()
        dsym_file = self.dsym_file_var.get()

        if not ips_file:
            messagebox.showwarning("警告", "请选择IPS文件")
            return

        if not dsym_file:
            messagebox.showwarning("警告", "请选择dSYM文件")
            return

        messagebox.showinfo("提示", "符号化功能需要使用atos命令行工具，正在开发中...")

    def display_ips_with_colors(self, content, bundle_id):
        """显示带颜色区分的IPS崩溃报告

        Args:
            content: 崩溃报告内容（包含[APP]和[SYS]标记）
            bundle_id: 应用的Bundle ID
        """
        import re

        lines = content.split('\n')
        app_name = bundle_id.split('.')[-1] if bundle_id else ''
        stack_frame_pattern = re.compile(r'^\s*\d+\s+\S+')
        system_libs = ('/System/', '/usr/', 'UIKit', 'Foundation', 'CoreFoundation',
                      'libsystem', 'libdispatch', 'libobjc', 'libswift')

        for line in lines:
            # 快速检查标记
            if line.startswith('[APP]'):
                self.ips_result_text.insert(tk.END, line[5:] + '\n', 'app_symbol')
            elif line.startswith('[SYS]'):
                self.ips_result_text.insert(tk.END, line[5:] + '\n', 'system_symbol')
            # 崩溃相关信息
            elif 'Thread' in line and 'Crashed' in line:
                self.ips_result_text.insert(tk.END, line + '\n', 'crashed')
            elif line.startswith('Exception') or line.startswith('Termination'):
                self.ips_result_text.insert(tk.END, line + '\n', 'crashed')
            # 线程信息
            elif line.startswith('Thread'):
                self.ips_result_text.insert(tk.END, line + '\n', 'thread')
            # 头部信息
            elif '====' in line or line.startswith(('Incident', 'Hardware', 'Process', 'Path',
                                                    'Identifier', 'Version', 'OS Version')):
                self.ips_result_text.insert(tk.END, line + '\n', 'header')
            # 堆栈帧
            elif stack_frame_pattern.match(line):
                if app_name and app_name in line:
                    self.ips_result_text.insert(tk.END, line + '\n', 'app_symbol')
                elif any(sys_lib in line for sys_lib in system_libs):
                    self.ips_result_text.insert(tk.END, line + '\n', 'system_symbol')
                else:
                    self.ips_result_text.insert(tk.END, line + '\n')
            else:
                self.ips_result_text.insert(tk.END, line + '\n')

    def clear_ips_result(self):
        """清空IPS解析结果"""
        self.ips_result_text.delete(1.0, tk.END)
        self.ips_info_text.delete(1.0, tk.END)
        self.ips_file_var.set("")
        self.dsym_file_var.set("")
        # 重置按钮文本
        if hasattr(self, 'analyze_button'):
            self.analyze_button.config(text="解析崩溃日志")

    def translate_ips_to_crash(self, ips_content):
        """将IPS格式转换为传统crash格式（使用OSAnalytics.framework）"""
        import subprocess
        import tempfile

        try:
            # 创建临时文件保存IPS内容
            with tempfile.NamedTemporaryFile(mode='w', suffix='.ips', delete=False, encoding='utf-8') as tmp:
                tmp.write(ips_content)
                tmp_path = tmp.name

            self.ips_result_text.insert(tk.END, f"尝试转换IPS文件: {tmp_path}\n", "info")

            # 使用Python调用OSAnalytics框架进行转换
            python_script = '''
import sys
try:
    import objc
    from Foundation import NSBundle, NSURL, NSDictionary

    # 加载OSAnalytics框架
    bundle_path = "/System/Library/PrivateFrameworks/OSAnalytics.framework"
    bundle = NSBundle.bundleWithPath_(bundle_path)
    if not bundle or not bundle.load():
        print("ERROR: Could not load OSAnalytics.framework")
        sys.exit(1)

    # 获取OSALegacyXform类
    OSALegacyXform = objc.lookUpClass("OSALegacyXform")
    if not OSALegacyXform:
        print("ERROR: Could not find OSALegacyXform class")
        sys.exit(1)

    # 转换IPS文件
    file_url = NSURL.fileURLWithPath_(sys.argv[1])
    options = NSDictionary.dictionary()
    result = OSALegacyXform.transformURL_options_(file_url, options)

    if result and "symbolicated_log" in result:
        print(result["symbolicated_log"])
    else:
        print("ERROR: Transformation returned no result")
except ImportError as e:
    print(f"ERROR: Missing module: {e}")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
'''

            # 执行转换
            result = subprocess.run(
                ['python3', '-c', python_script, tmp_path],
                capture_output=True,
                text=True,
                timeout=10
            )

            # 清理临时文件
            os.unlink(tmp_path)

            if result.returncode == 0 and result.stdout and not result.stdout.startswith("ERROR"):
                self.ips_result_text.insert(tk.END, "✅ IPS转换成功\n", "success")
                return result.stdout
            else:
                # 如果OSAnalytics方法失败，尝试简单转换
                error_msg = result.stderr if result.stderr else result.stdout
                self.ips_result_text.insert(tk.END, f"⚠️ OSAnalytics转换失败: {error_msg}\n", "warning")

                # 尝试简单的IPS到crash转换
                return self.simple_ips_to_crash_conversion(ips_content)

        except subprocess.TimeoutExpired:
            self.ips_result_text.insert(tk.END, "⚠️ IPS转换超时\n", "warning")
            return self.simple_ips_to_crash_conversion(ips_content)
        except Exception as e:
            self.ips_result_text.insert(tk.END, f"⚠️ IPS转换异常: {str(e)}\n", "warning")
            return self.simple_ips_to_crash_conversion(ips_content)

    def simple_ips_to_crash_conversion(self, ips_content):
        """简单的IPS到crash格式转换（不依赖OSAnalytics）"""
        import json

        try:
            lines = ips_content.strip().split('\n')
            if not lines or not lines[0].startswith('{'):
                return None

            # 解析IPS JSON
            summary = json.loads(lines[0]) if lines[0].startswith('{') else {}
            detail = json.loads('\n'.join(lines[1:])) if len(lines) > 1 and lines[1].startswith('{') else {}

            # 构建crash格式输出
            output = []

            # Incident信息
            output.append(f"Incident Identifier: {detail.get('incident', summary.get('incident', 'Unknown'))}")
            output.append(f"CrashReporter Key:   {detail.get('crashReporterKey', summary.get('crashReporterKey', 'Unknown'))}")

            # 硬件和进程信息
            output.append(f"Hardware Model:      {detail.get('modelCode', summary.get('modelCode', 'Unknown'))}")
            output.append(f"Process:             {summary.get('procName', detail.get('procName', 'Unknown'))} [{summary.get('pid', detail.get('pid', '?'))}]")
            output.append(f"Path:                {summary.get('procPath', detail.get('procPath', '/private/var/containers/Bundle/Application/[...]/App.app/App'))}")
            output.append(f"Identifier:          {summary.get('bundleID', detail.get('bundleID', 'Unknown'))}")

            # 版本信息
            app_version = summary.get('app_version') or detail.get('bundleInfo', {}).get('CFBundleShortVersionString', '?')
            build_version = summary.get('build_version') or detail.get('bundleInfo', {}).get('CFBundleVersion', '?')
            output.append(f"Version:             {app_version} ({build_version})")

            # 架构信息
            cpu_type = detail.get('cpuType', 'ARM-64')
            output.append(f"Code Type:           {cpu_type} (Native)")

            # 进程角色和父进程
            output.append(f"Role:                {detail.get('role', 'Foreground')}")
            output.append(f"Parent Process:      {detail.get('parentProc', 'launchd')} [{detail.get('parentPid', '1')}]")
            output.append(f"Coalition:           {detail.get('coalitionName', summary.get('bundleID', 'Unknown'))} [{detail.get('coalitionID', '?')}]")
            output.append("")

            # 时间信息
            capture_time = summary.get('captureTime') or detail.get('captureTime', 'Unknown')
            launch_time = detail.get('launchTime', 'Unknown')
            output.append(f"Date/Time:           {capture_time}")
            output.append(f"Launch Time:         {launch_time}")

            # 系统信息
            os_version = summary.get('osVersion') or detail.get('osVersion', {}).get('train', 'Unknown')
            build_variant = detail.get('osVersion', {}).get('build', 'Unknown')
            output.append(f"OS Version:          {os_version} ({build_variant})")
            output.append(f"Release Type:        {detail.get('osVersion', {}).get('releaseType', 'User')}")
            output.append(f"Baseband Version:    {detail.get('basebandVersion', 'Unknown')}")
            output.append(f"Report Version:      {detail.get('reportVersion', '104')}")
            output.append("")

            # 异常信息
            if 'exception' in detail:
                exc = detail['exception']
                exc_type = exc.get('type', 'Unknown')
                exc_signal = exc.get('signal', 'Unknown')
                exc_codes = exc.get('codes', '0x0000000000000000, 0x0000000000000000')

                # 格式化异常代码
                if isinstance(exc_codes, str):
                    formatted_codes = exc_codes
                else:
                    formatted_codes = ', '.join([f"0x{code:016x}" if isinstance(code, int) else str(code) for code in exc_codes])

                output.append(f"Exception Type:  {exc_type} ({exc_signal})")
                output.append(f"Exception Codes: {formatted_codes}")

                # 终止信息
                termination = detail.get('termination', {})
                term_indicator = termination.get('indicator', '')
                term_reason = termination.get('reason', '')
                term_signal = termination.get('signal', exc_signal)

                if term_indicator:
                    output.append(f"Termination Reason: {term_indicator} {term_reason}")
                else:
                    output.append(f"Termination Reason: SIGNAL {term_signal} {exc_signal}")

                output.append(f"Terminating Process: {summary.get('procName', 'Unknown')} [{summary.get('pid', '?')}]")
                output.append("")

                # 触发线程
                triggered_thread = None
                threads = detail.get('threads', [])
                for i, thread in enumerate(threads):
                    if thread.get('triggered', False):
                        triggered_thread = i
                        break

                if triggered_thread is not None:
                    output.append(f"Triggered by Thread:  {triggered_thread}")
                    output.append("")

                # Application Specific Information
                if exc.get('message'):
                    output.append("Application Specific Information:")
                    output.append(exc.get('message', ''))
                    output.append("")

            # Last Exception Backtrace (如果有)
            legacy_info = detail.get('legacyInfo')
            if legacy_info and legacy_info.get('threadTriggered'):
                thread_triggered = legacy_info.get('threadTriggered', {})
                if thread_triggered.get('queue'):
                    output.append("")
                    output.append("Last Exception Backtrace:")
                    # 这里应该解析backtrace，但现在先跳过
                    output.append("")

            # 线程信息
            threads = detail.get('threads', [])
            for i, thread in enumerate(threads):
                # 线程头部，包含名称和队列信息
                thread_name = thread.get('name', '')
                thread_queue = thread.get('queue', '')

                # 格式化线程头部
                if thread.get('triggered', False):
                    if thread_name:
                        output.append(f"Thread {i} name:  {thread_name}")
                    if thread_queue:
                        output.append(f"Thread {i} Queue:  {thread_queue}")
                    output.append(f"Thread {i} Crashed:")
                else:
                    if thread_name:
                        output.append(f"Thread {i} name:  {thread_name}")
                    if thread_queue:
                        output.append(f"Thread {i} Queue:  {thread_queue}")
                    output.append(f"Thread {i}:")

                frames = thread.get('frames', [])
                used_images = detail.get('usedImages', [])

                for j, frame in enumerate(frames):
                    image_index = frame.get('imageIndex', 0)
                    image_offset = frame.get('imageOffset', 0)
                    symbol = frame.get('symbol')  # 获取符号信息
                    source_line = frame.get('sourceLine')  # 源代码行信息
                    source_file = frame.get('sourceFile')  # 源文件信息

                    if image_index < len(used_images):
                        image = used_images[image_index]
                        image_name = image.get('name', '???').split('/')[-1]
                        load_address = hex(image.get('base', 0))
                        address = hex(image.get('base', 0) + image_offset)

                        # 检查是否是系统库
                        is_system = (
                            '/usr/lib/' in image.get('path', '') or
                            '/System/' in image.get('path', '') or
                            '/Developer/' in image.get('path', '') or
                            image_name.startswith('lib') or
                            image_name in ['dyld', 'CoreFoundation', 'Foundation', 'UIKitCore', 'QuartzCore']
                        )

                        # 格式化输出，确保对齐
                        # MacSymbolicator格式：序号 二进制名称 地址 符号/地址 + 偏移
                        if symbol:
                            # 有符号信息（来自IPS文件）
                            if source_file and source_line:
                                # 包含源代码信息
                                output.append(f"{j:<3} {image_name:<32} {address} {symbol} ({source_file}:{source_line}) + {image_offset}")
                            else:
                                output.append(f"{j:<3} {image_name:<32} {address} {symbol} + {image_offset}")
                        else:
                            # 没有符号，显示加载地址
                            output.append(f"{j:<3} {image_name:<32} {address} {load_address} + {image_offset}")
                    else:
                        # 未知二进制
                        output.append(f"{j:<3} ???                              0x{image_offset:016x} 0x{image_offset:016x}")

                output.append("")

            # Thread State (如果有寄存器信息)
            for i, thread in enumerate(threads):
                if thread.get('triggered', False) and 'threadState' in thread:
                    output.append(f"Thread {i} crashed with ARM Thread State (64-bit):")
                    state = thread['threadState']

                    # 显示通用寄存器
                    if 'x' in state:
                        x_regs = state['x']
                        for j in range(0, len(x_regs), 4):
                            reg_line = []
                            for k in range(j, min(j+4, len(x_regs))):
                                reg_line.append(f"   x{k:2}: 0x{x_regs[k]:016x}")
                            output.append("".join(reg_line))

                    # 显示特殊寄存器
                    if 'fp' in state:
                        output.append(f"    fp: 0x{state['fp']:016x}   lr: 0x{state.get('lr', 0):016x}")
                    if 'sp' in state:
                        output.append(f"    sp: 0x{state['sp']:016x}   pc: 0x{state.get('pc', 0):016x} cpsr: 0x{state.get('cpsr', 0):08x}")

                    # 显示异常状态寄存器
                    if 'esr' in state:
                        output.append(f"   esr: 0x{state['esr']:08x}")
                        # 解析ESR寄存器含义
                        esr_desc = self.parse_esr_description(state['esr'])
                        if esr_desc:
                            output.append(f"  Address size fault: {esr_desc}")

                    output.append("")
                    break

            # Binary Images部分 - 格式化为MacSymbolicator样式
            output.append("Binary Images:")
            for image in detail.get('usedImages', []):
                base = image.get('base', 0)
                size = image.get('size', 0)
                end = base + size - 1
                name = image.get('name', '???').split('/')[-1]
                uuid = image.get('uuid', '').replace('-', '').lower()
                arch = image.get('arch', 'arm64')
                path = image.get('path', image.get('name', '???'))

                # 格式：起始地址 - 结束地址 二进制名称 架构 <UUID> 路径
                # 使用固定宽度确保对齐
                base_str = f"0x{base:x}"
                end_str = f"0x{end:x}"
                output.append(f"{base_str:>18} - {end_str:>18} {name} {arch}  <{uuid}> {path}")

            return '\n'.join(output)

        except Exception as e:
            self.ips_result_text.insert(tk.END, f"简单转换也失败: {str(e)}\n", "warning")
            return None

    def parse_esr_description(self, esr_value):
        """解析ARM Exception Syndrome Register (ESR)的含义"""
        if not esr_value:
            return None

        # ESR寄存器的高6位是Exception Class
        ec = (esr_value >> 26) & 0x3F

        # 常见的异常类型
        exception_classes = {
            0x15: "SVC instruction execution",
            0x21: "Instruction Abort from a lower Exception level",
            0x22: "Instruction Abort without a change in Exception level",
            0x24: "Data Abort from a lower Exception level",
            0x25: "Data Abort without a change in Exception level",
            0x2C: "Trapped floating-point exception",
            0x30: "Breakpoint exception from a lower Exception level",
            0x31: "Breakpoint exception without a change in Exception level",
            0x34: "Software Step exception from a lower Exception level",
            0x35: "Software Step exception without a change in Exception level",
            0x38: "Watchpoint exception from a lower Exception level",
            0x39: "Watchpoint exception without a change in Exception level",
        }

        desc = exception_classes.get(ec)
        if desc:
            # 对于Data Abort，提取更多信息
            if ec in [0x24, 0x25]:
                # ISS字段包含了更多关于数据异常的信息
                iss = esr_value & 0x1FFFFFF
                isv = (iss >> 24) & 0x1  # 指示syndrome信息是否有效
                sas = (iss >> 22) & 0x3  # 访问大小
                sse = (iss >> 21) & 0x1  # 符号扩展
                srt = (iss >> 16) & 0x1F  # 寄存器编号
                sf = (iss >> 15) & 0x1  # 64位寄存器
                ar = (iss >> 14) & 0x1  # Acquire/Release
                dfsc = iss & 0x3F  # 数据错误状态码

                # 解析错误状态码
                fault_status = {
                    0x04: "level 0 translation fault",
                    0x05: "level 1 translation fault",
                    0x06: "level 2 translation fault",
                    0x07: "level 3 translation fault",
                    0x09: "level 1 access flag fault",
                    0x0A: "level 2 access flag fault",
                    0x0B: "level 3 access flag fault",
                    0x0D: "level 1 permission fault",
                    0x0E: "level 2 permission fault",
                    0x0F: "level 3 permission fault",
                    0x10: "synchronous external abort",
                    0x21: "alignment fault",
                }

                fault = fault_status.get(dfsc, f"unknown fault (0x{dfsc:02x})")
                return f"{desc}: {fault}"

        return desc

    def get_common_system_symbol(self, library_name, offset):
        """根据库名和偏移获取常见系统符号"""
        # 常见符号偏移映射（这些是相对稳定的）
        # 注意：这些偏移可能随iOS版本变化，这里提供的是常见值
        common_offsets = {
            'libsystem_kernel.dylib': {
                # 常见系统调用
                264: 'mach_msg2_trap',
                272: 'mach_msg2_internal',
                288: 'mach_msg_trap',
                8008: '__semwait_signal',
                24632: '__psynch_cvwait',
                45532: '__pthread_kill',
                # 其他常见偏移
                29296: '__abort_with_payload',
                31744: '__pthread_sigmask',
            },
            'libsystem_pthread.dylib': {
                # 线程管理
                6736: 'pthread_mutex_lock',
                7384: 'pthread_mutex_unlock',
                13124: '_pthread_start',
                31840: 'pthread_kill',
                25340: '_pthread_wqthread',
                # 条件变量
                15992: '_pthread_cond_wait',
                16496: '_pthread_cond_signal',
            },
            'libsystem_c.dylib': {
                # 标准C库函数
                488144: 'abort',
                487552: 'exit',
                75888: '__stack_chk_fail',
            },
            'libc++abi.dylib': {
                # C++异常处理
                91552: 'abort_message',
                20240: 'demangling_terminate_handler()',
                88244: 'std::__terminate(void (*)())',
                19992: '__cxa_throw',
                72708: '__cxa_rethrow',
            },
            'libobjc.A.dylib': {
                # Objective-C运行时
                211960: '_objc_terminate()',
                203812: 'objc_exception_throw',
                15672: 'objc_msgSend',
                16400: 'objc_msgSend_stret',
                17424: 'objc_msgSendSuper2',
                139280: '_objc_release',
                139264: '_objc_retain',
            },
            'libdispatch.dylib': {
                # Grand Central Dispatch
                6892: '_dispatch_client_callout',
                13828: '_dispatch_lane_serial_drain',
                17476: '_dispatch_lane_invoke',
                79180: '_dispatch_workloop_worker_thread',
                74928: '_dispatch_root_queue_drain',
            },
            'CoreFoundation': {
                # Core Foundation
                543984: '__CFRUNLOOP_IS_SERVICING_THE_MAIN_DISPATCH_QUEUE__',
                537088: '__CFRunLoopRun',
                534236: 'CFRunLoopRunSpecific',
            },
            'Foundation': {
                # Foundation框架
                # 这些偏移更容易变化
                82944: '-[NSObject doesNotRecognizeSelector:]',
                721920: '-[NSThread main]',
                722368: '__NSThread__start__',
            },
            'UIKitCore': {
                # UIKit (iOS)
                # 这些偏移高度依赖于iOS版本
                1146880: '-[UIApplication _run]',
                4423680: 'UIApplicationMain',
            },
        }

        if library_name in common_offsets and offset in common_offsets[library_name]:
            return common_offsets[library_name][offset]

        # 对于未知偏移，返回None
        return None

    def get_dsym_binary_path(self, dsym_path):
        """获取dSYM包内的实际二进制文件路径"""
        # dSYM文件结构: xxx.dSYM/Contents/Resources/DWARF/二进制文件
        dwarf_path = os.path.join(dsym_path, 'Contents', 'Resources', 'DWARF')

        if os.path.exists(dwarf_path):
            files = os.listdir(dwarf_path)
            if files:
                # 返回第一个文件的完整路径
                return os.path.join(dwarf_path, files[0])

        # 如果不是标准dSYM包结构，返回原路径
        return dsym_path

    def get_dsym_uuids(self, dsym_path):
        """使用dwarfdump获取dSYM的UUID信息"""
        import subprocess
        import re

        try:
            binary_path = self.get_dsym_binary_path(dsym_path)
            cmd = f"dwarfdump --uuid '{binary_path}'"

            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)

            if result.returncode == 0 and result.stdout:
                uuids = {}
                # 解析格式: UUID: XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX (arm64) /path/to/binary
                pattern = r'UUID: ([A-F0-9-]+) \((\w+)\)'
                matches = re.findall(pattern, result.stdout, re.IGNORECASE)

                for uuid, arch in matches:
                    uuids[arch] = uuid.replace('-', '').lower()

                return uuids
        except Exception:
            pass

        return {}

    def symbolicate_crash(self, ips_file, dsym_file):
        """符号化崩溃报告（使用MacSymbolicator的方法）"""
        import subprocess
        import re

        try:
            # 读取IPS文件内容
            with open(ips_file, 'r', encoding='utf-8') as f:
                ips_content = f.read()

            # 显示进度提示
            self.ips_result_text.delete(1.0, tk.END)
            self.ips_result_text.insert(tk.END, "正在解析崩溃报告...\n", "header")
            self.root.update()

            # 步骤1: 检测文件格式
            if ips_content.strip().startswith('{'):
                # IPS格式，需要转换
                self.ips_result_text.insert(tk.END, "检测到IPS格式，正在转换...\n", "info")
                crash_content = self.translate_ips_to_crash(ips_content)

                if not crash_content:
                    # OSAnalytics转换失败，使用备用方案
                    self.ips_result_text.insert(tk.END, "OSAnalytics转换失败，使用备用方案...\n", "warning")
                    crash_content = self.simple_ips_to_crash_conversion(ips_content)

                    if not crash_content:
                        self.ips_result_text.insert(tk.END, "❌ 无法转换IPS文件\n", "warning")
                        return None
            else:
                # 已经是crash格式
                crash_content = ips_content

            # 步骤2: 从crash内容中提取信息
            binary_images = self.extract_binary_images(crash_content)
            stack_frames = self.extract_stack_frames(crash_content, binary_images)

            if not stack_frames:
                self.ips_result_text.insert(tk.END, "未找到需要符号化的堆栈帧，显示原始内容\n", "info")
                return crash_content

            # 步骤3: 获取dSYM的UUID信息
            dsym_uuids = self.get_dsym_uuids(dsym_file)
            dsym_binary_path = self.get_dsym_binary_path(dsym_file)

            if not dsym_uuids:
                self.ips_result_text.insert(tk.END, "⚠️ 无法获取dSYM UUID信息\n", "warning")
                return crash_content

            self.ips_result_text.insert(tk.END, f"dSYM UUIDs: {dsym_uuids}\n", "info")
            self.ips_result_text.insert(tk.END, f"找到 {len(binary_images)} 个二进制映像\n", "info")
            self.ips_result_text.insert(tk.END, f"找到 {len(stack_frames)} 个堆栈帧\n", "info")

            # 步骤4: 按加载地址分组堆栈帧（MacSymbolicator的做法）
            frames_by_load_address = {}
            for frame in stack_frames:
                load_addr = frame['load_address']
                if load_addr not in frames_by_load_address:
                    frames_by_load_address[load_addr] = []
                frames_by_load_address[load_addr].append(frame)

            # 步骤5: 符号化每组地址
            symbolicated_content = crash_content
            app_frames_count = 0
            system_frames_count = 0

            for load_address, frames in frames_by_load_address.items():
                # 获取对应的二进制映像
                binary_image = None
                for img in binary_images:
                    if img['load_address'] == load_address:
                        binary_image = img
                        break

                if not binary_image:
                    continue

                # 判断是否是应用程序的二进制文件
                binary_name = binary_image.get('name', '')
                binary_uuid = binary_image.get('uuid', '')

                # 检查是否是系统库（通过路径判断）
                binary_path = binary_image.get('path', '')
                is_system_library = (
                    '/usr/lib/' in binary_path or
                    '/System/' in binary_path or
                    binary_name.startswith('lib') or
                    binary_name in ['dyld', 'CoreFoundation', 'Foundation', 'UIKitCore']
                )

                if is_system_library:
                    # 系统库：保持原样（OSAnalytics应该已经处理了）
                    # 或者如果是简单转换，系统库保留原始格式
                    system_frames_count += len(frames)
                    # 不进行符号化，保留原始显示
                    continue

                # 检查UUID是否匹配dSYM
                arch = binary_image.get('arch', 'arm64')
                dsym_uuid = dsym_uuids.get(arch, '')

                # 比较UUID（去除破折号并转为小写）
                if dsym_uuid and binary_uuid.replace('-', '').lower() == dsym_uuid.replace('-', '').lower():
                    # UUID匹配，进行符号化
                    app_frames_count += len(frames)
                    addresses = [frame['address'] for frame in frames]
                    symbolicated_results = self.symbolicate_addresses(
                        dsym_binary_path, arch, load_address, addresses
                    )

                    # 替换原始内容
                    if symbolicated_results:
                        for frame, symbol in zip(frames, symbolicated_results):
                            symbolicated_content = self.replace_frame(
                                symbolicated_content, frame, symbol
                            )

            self.ips_result_text.insert(tk.END, f"符号化了 {app_frames_count} 个应用堆栈帧\n", "info")
            self.ips_result_text.insert(tk.END, f"保留了 {system_frames_count} 个系统库堆栈帧\n", "info")

            self.ips_result_text.insert(tk.END, "✅ 符号化完成！\n\n", "success")
            self.ips_result_text.insert(tk.END, "="*80 + "\n\n")

            return symbolicated_content

        except Exception as e:
            self.ips_result_text.insert(tk.END, f"❌ 符号化过程出错: {str(e)}\n", "crashed")
            import traceback
            traceback.print_exc()
            return None

    def extract_binary_images(self, crash_content):
        """从crash内容中提取二进制映像信息"""
        import re

        binary_images = []

        # 查找Binary Images部分
        # 格式: 0x100000000 - 0x100003fff App arm64 <uuid> /path/to/binary
        pattern = r'(0x[0-9a-f]+)\s+-\s+0x[0-9a-f]+\s+(\S+)\s+(\S+)\s+<([0-9a-f]+)>\s+(.+)'

        # 首先找到Binary Images:部分
        binary_section_match = re.search(r'Binary Images:.*', crash_content, re.DOTALL)
        if binary_section_match:
            binary_section = binary_section_match.group(0)
            matches = re.finditer(pattern, binary_section, re.IGNORECASE)

            for match in matches:
                binary_images.append({
                    'load_address': match.group(1),
                    'name': match.group(2),
                    'arch': match.group(3),
                    'uuid': match.group(4),
                    'path': match.group(5)
                })

        return binary_images

    def extract_stack_frames(self, crash_content, binary_images):
        """从crash内容中提取需要符号化的堆栈帧"""
        import re

        stack_frames = []

        # 创建二进制映像的查找字典
        image_map = {}
        for img in binary_images:
            image_map[img['name']] = img
            image_map[img['load_address']] = img

        # 查找堆栈帧
        # 格式1: 0 BinaryName 0x0000000100000000 0x100000000 + 123
        # 格式2: 0 BinaryName 0x0000000100000000 BinaryName + 123
        # 格式3: 0 BinaryName 0x0000000100000000 symbol_name + 123
        # 使用更灵活的正则表达式，匹配到最后的 + 数字
        pattern = r'^\s*(\d+)\s+(\S+)\s+(0x[0-9a-f]+)\s+(.+)\s+\+\s+(\d+)$'

        for line in crash_content.split('\n'):
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                frame_index = match.group(1)
                binary_name = match.group(2)
                address = match.group(3)
                load_addr_or_name = match.group(4)
                offset = match.group(5)

                # 确定加载地址
                if load_addr_or_name.startswith('0x'):
                    load_address = load_addr_or_name
                elif load_addr_or_name in image_map:
                    load_address = image_map[load_addr_or_name]['load_address']
                elif binary_name in image_map:
                    load_address = image_map[binary_name]['load_address']
                else:
                    continue

                # 获取binary对应的UUID（如果有）
                binary_uuid = None
                if binary_name in image_map:
                    binary_uuid = image_map[binary_name].get('uuid', '')
                elif load_address in image_map:
                    binary_uuid = image_map[load_address].get('uuid', '')

                stack_frames.append({
                    'original_text': line,
                    'binary_name': binary_name,
                    'address': address,
                    'load_address': load_address,
                    'offset': offset,
                    'uuid': binary_uuid
                })

        return stack_frames

    def symbolicate_addresses(self, dsym_binary_path, arch, load_address, addresses):
        """使用atos批量符号化地址"""
        import subprocess

        try:
            # 构建atos命令
            addresses_str = ' '.join(addresses)
            cmd = f'xcrun atos -o "{dsym_binary_path}" -arch {arch} -l {load_address} {addresses_str}'

            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)

            if result.returncode == 0 and result.stdout:
                # 分割结果，每行对应一个地址
                lines = result.stdout.strip().split('\n')
                return lines

        except Exception:
            pass

        return None

    def symbolicate_system_library(self, library_path, arch, load_address, addresses):
        """符号化系统库地址"""
        import subprocess
        import os

        try:
            # 系统库符号通常在符号缓存中
            # 尝试多种方法

            # 方法1: 直接使用库路径（可能不存在或没有符号）
            if os.path.exists(library_path):
                addresses_str = ' '.join(addresses)
                cmd = f'xcrun atos -o "{library_path}" -arch {arch} -l {load_address} {addresses_str}'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)

                if result.returncode == 0 and result.stdout and '??' not in result.stdout:
                    lines = result.stdout.strip().split('\n')
                    # 过滤有效结果
                    valid_lines = []
                    for line in lines:
                        if line and '??' not in line:
                            valid_lines.append(line)
                        else:
                            valid_lines.append(None)
                    if any(valid_lines):
                        return valid_lines

            # 方法2: 查找符号缓存
            library_name = os.path.basename(library_path)
            symbol_paths = [
                f'/System/Library/Caches/com.apple.dyld/{library_name}.symbols',
                f'/private/var/db/dyld/{library_name}.symbols',
                f'~/Library/Developer/Xcode/iOS DeviceSupport/*/Symbols{library_path}'
            ]

            for symbol_path in symbol_paths:
                expanded_path = os.path.expanduser(symbol_path)
                if '*' in expanded_path:
                    import glob
                    paths = glob.glob(expanded_path)
                    if paths:
                        expanded_path = paths[0]

                if os.path.exists(expanded_path):
                    addresses_str = ' '.join(addresses)
                    cmd = f'xcrun atos -o "{expanded_path}" -arch {arch} -l {load_address} {addresses_str}'
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)

                    if result.returncode == 0 and result.stdout:
                        lines = result.stdout.strip().split('\n')
                        return lines

            # 如果都失败了，返回预定义的系统符号（常见的）
            return self.get_known_system_symbols(library_path, addresses)

        except Exception:
            pass

        return None

    def get_known_system_symbols(self, library_path, addresses):
        """获取已知的系统库符号（硬编码常见符号）"""
        library_name = os.path.basename(library_path)

        # 常见系统库符号映射
        known_symbols = {
            'libsystem_kernel.dylib': {
                '0x1edb9e1dc': '__pthread_kill',
                '0x1edb93ce4': 'mach_msg2_trap',
                '0x1edb99438': '__psynch_cvwait',
            },
            'libsystem_pthread.dylib': {
                '0x22708bc60': 'pthread_kill',
                '0x227087344': '_pthread_start',
            },
            'libsystem_c.dylib': {
                '0x1a49bc2d0': 'abort',
            },
            'libc++abi.dylib': {
                '0x226fb55a0': 'abort_message',
                '0x226fa3f10': 'demangling_terminate_handler()',
                '0x226fb48b4': 'std::__terminate(void (*)())',
            },
            'libobjc.A.dylib': {
                '0x199f2bbf8': '_objc_terminate()',
                '0x199f29c24': 'objc_exception_throw',
            },
        }

        if library_name in known_symbols:
            symbols = known_symbols[library_name]
            results = []
            for addr in addresses:
                if addr in symbols:
                    results.append(symbols[addr])
                else:
                    results.append(None)
            return results

        return None

    def replace_frame(self, content, frame, symbol):
        """替换堆栈帧为符号化后的内容"""
        import re

        original_line = frame['line']
        address = frame['address']
        load_address = frame['load_address']

        # 构建替换模式
        # 将 "0xaddress load_address + offset" 替换为 "0xaddress symbol"
        # 或 "0xaddress binary_name + offset" 替换为 "0xaddress symbol"
        pattern1 = re.escape(f"{address} {load_address}")
        pattern2 = re.escape(f"{address} {frame['binary_name']}")

        # 使用符号替换
        new_content = content
        new_content = re.sub(pattern1, f"{address} {symbol}", new_content)
        new_content = re.sub(pattern2, f"{address} {symbol}", new_content)

        return new_content

    def parse_ips_directly(self, ips_content, dsym_file):
        """直接解析IPS格式（备用方案，当OSAnalytics不可用时）"""
        # 这个函数已经不再需要，因为symbolicate_crash已经处理了所有情况
        # 保留这个函数是为了兼容性
        crash_content = self.simple_ips_to_crash_conversion(ips_content)
        if crash_content:
            return crash_content
        return ips_content


    def display_symbolicated_crash(self, content):
        """显示符号化后的崩溃信息"""
        self.ips_result_text.delete(1.0, tk.END)

        # 直接显示符号化后的完整内容
        lines = content.split('\n')
        in_backtrace = False
        in_crashed_thread = False

        for line in lines:
            # 检测崩溃报告头部信息
            if line.startswith('Incident Identifier:') or line.startswith('Hardware Model:'):
                self.ips_result_text.insert(tk.END, f"{line}\n", "info")
            # 检测异常信息
            elif 'Exception Type:' in line or 'Exception Codes:' in line or 'Termination' in line:
                self.ips_result_text.insert(tk.END, f"{line}\n", "crashed")
            # 检测Last Exception Backtrace
            elif 'Last Exception Backtrace:' in line:
                in_backtrace = True
                self.ips_result_text.insert(tk.END, f"\n{line}\n", "thread_header")
            # 检测崩溃线程
            elif line.startswith('Thread') and 'Crashed:' in line:
                in_crashed_thread = True
                in_backtrace = False
                self.ips_result_text.insert(tk.END, f"\n{line}\n", "crashed")
            # 检测其他线程
            elif line.startswith('Thread') and ':' in line:
                in_crashed_thread = False
                in_backtrace = False
                self.ips_result_text.insert(tk.END, f"\n{line}\n", "thread_header")
            # 处理堆栈行
            elif (in_backtrace or in_crashed_thread) and line.strip() and line[0:1].isdigit():
                # 检查是否已经符号化（包含源文件信息或方法名）
                if ' (in ' in line and ') ' in line:
                    # 已符号化的行，格式如: 14 huhuAudio 0x101ac0698 GasSceneDYCustomGiftBarrageView.returnActivityApplitionAnimation(_:) (in huhuAudio) (/<compiler-generated>:0) + 22513304
                    if '.swift' in line or '.m' in line or '.mm' in line or '.c' in line or '.cpp' in line:
                        # 包含具体源文件
                        self.ips_result_text.insert(tk.END, f"{line}\n", "symbolicated")
                    elif in_crashed_thread:
                        # 崩溃线程的符号化行
                        self.ips_result_text.insert(tk.END, f"{line}\n", "crashed_stack")
                    else:
                        # 普通符号化行
                        self.ips_result_text.insert(tk.END, f"{line}\n", "stack")
                else:
                    # 未符号化的行，只有地址
                    self.ips_result_text.insert(tk.END, f"{line}\n", "unsymbolicated")
            else:
                # 其他行
                self.ips_result_text.insert(tk.END, f"{line}\n")

        # 配置标签样式
        self.ips_result_text.tag_config("header", foreground="#ff6600", font=("Courier", 12, "bold"))
        self.ips_result_text.tag_config("info", foreground="#0066cc", font=("Courier", 10))
        self.ips_result_text.tag_config("crashed", foreground="#ff0000", font=("Courier", 10, "bold"))
        self.ips_result_text.tag_config("thread_header", foreground="#0066cc", font=("Courier", 11, "bold"))
        self.ips_result_text.tag_config("symbolicated", foreground="#00aa00", font=("Courier", 10, "bold"))
        self.ips_result_text.tag_config("stack", foreground="#333333", font=("Courier", 10))
        self.ips_result_text.tag_config("crashed_stack", foreground="#cc0000", font=("Courier", 10))
        self.ips_result_text.tag_config("unsymbolicated", foreground="#999999", font=("Courier", 10))
        self.ips_result_text.tag_config("success", foreground="#00aa00", font=("Courier", 11, "bold"))

    def export_ips_report(self):
        """导出IPS解析报告"""
        content = self.ips_result_text.get(1.0, tk.END)
        if not content.strip():
            messagebox.showwarning("警告", "没有可导出的内容")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )

        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("成功", "报告导出成功")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败: {str(e)}")

    def create_push_test_tab(self):
        """创建iOS推送测试标签页"""
        # 创建标签页框架
        push_frame = ttk.Frame(self.main_notebook, padding="10")
        self.main_notebook.add(push_frame, text="iOS推送测试")

        # 延迟导入，避免启动时依赖检查
        try:
            from apns_gui import APNSPushGUI
            # 创建推送GUI实例（嵌入到标签页中）
            self.push_gui = APNSPushGUI(push_frame)
            self.push_gui.pack(fill=tk.BOTH, expand=True)
        except ImportError as e:
            # 如果导入失败，显示提示信息
            error_frame = ttk.Frame(push_frame)
            error_frame.pack(fill=tk.BOTH, expand=True)

            ttk.Label(error_frame,
                     text="iOS推送测试功能需要安装额外依赖",
                     font=('', 14, 'bold')).pack(pady=20)

            ttk.Label(error_frame,
                     text="请运行以下命令安装依赖：",
                     font=('', 11)).pack(pady=10)

            cmd_frame = ttk.Frame(error_frame)
            cmd_frame.pack(pady=10)

            cmd_text = tk.Text(cmd_frame, height=3, width=60, font=('Courier', 10))
            cmd_text.pack()
            cmd_text.insert('1.0',
                           "source venv/bin/activate\n"
                           "pip install cryptography httpx pyjwt h2")
            cmd_text.config(state='disabled')

            ttk.Label(error_frame,
                     text=f"错误详情: {str(e)}",
                     font=('', 10),
                     foreground='red').pack(pady=20)

            def retry_load():
                """重试加载推送模块"""
                try:
                    # 清除之前的错误界面
                    for widget in push_frame.winfo_children():
                        widget.destroy()

                    # 重新尝试导入
                    from apns_gui import APNSPushGUI
                    self.push_gui = APNSPushGUI(push_frame)
                    self.push_gui.pack(fill=tk.BOTH, expand=True)
                    messagebox.showinfo("成功", "推送模块加载成功！")
                except ImportError as e:
                    messagebox.showerror("错误", f"仍无法加载推送模块：\n{str(e)}")

            ttk.Button(error_frame,
                      text="重试加载",
                      command=retry_load).pack(pady=10)

    def create_sandbox_browser_tab(self):
        """创建iOS沙盒浏览标签页"""
        sandbox_frame = ttk.Frame(self.main_notebook, padding="10")
        self.main_notebook.add(sandbox_frame, text="iOS沙盒浏览")

        try:
            sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'gui', 'modules'))
            from sandbox_tab import SandboxBrowserTab
            self.sandbox_tab = SandboxBrowserTab(sandbox_frame, self)
        except ImportError as e:
            error_frame = ttk.Frame(sandbox_frame)
            error_frame.pack(fill=tk.BOTH, expand=True)

            ttk.Label(error_frame,
                     text="iOS沙盒浏览功能需要安装额外依赖",
                     font=('', 14, 'bold')).pack(pady=20)

            ttk.Label(error_frame,
                     text="请运行以下命令安装依赖：",
                     font=('', 11)).pack(pady=10)

            cmd_frame = ttk.Frame(error_frame)
            cmd_frame.pack(pady=10)

            cmd_text = tk.Text(cmd_frame, height=3, width=60, font=('Courier', 10))
            cmd_text.pack()
            cmd_text.insert('1.0',
                           "source venv/bin/activate\n"
                           "pip install pymobiledevice3")
            cmd_text.config(state='disabled')

            ttk.Label(error_frame,
                     text=f"错误详情: {str(e)}",
                     font=('', 10),
                     foreground='red').pack(pady=20)

            def retry_load():
                """重试加载沙盒浏览模块"""
                try:
                    for widget in sandbox_frame.winfo_children():
                        widget.destroy()

                    from sandbox_tab import SandboxBrowserTab
                    self.sandbox_tab = SandboxBrowserTab(sandbox_frame, self)
                    messagebox.showinfo("成功", "沙盒浏览模块加载成功！")
                except ImportError as e:
                    messagebox.showerror("错误", f"仍无法加载沙盒浏览模块：\n{str(e)}")

            ttk.Button(error_frame,
                      text="重试加载",
                      command=retry_load).pack(pady=10)

    def create_dsym_analysis_tab(self):
        """创建dSYM文件分析标签页"""
        dsym_frame = ttk.Frame(self.main_notebook, padding="10")
        self.main_notebook.add(dsym_frame, text="dSYM分析")

        try:
            sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'gui', 'modules'))
            from dsym_tab import DSYMTab
            self.dsym_tab = DSYMTab(dsym_frame)
            self.dsym_tab.frame.pack(fill=tk.BOTH, expand=True)
        except ImportError as e:
            error_frame = ttk.Frame(dsym_frame)
            error_frame.pack(fill=tk.BOTH, expand=True)

            ttk.Label(error_frame,
                     text="无法加载dSYM分析模块",
                     font=('', 14, 'bold')).pack(pady=20)

            ttk.Label(error_frame,
                     text=f"错误详情: {str(e)}",
                     font=('', 10),
                     foreground='red').pack(pady=20)

            def retry_load():
                """重试加载dSYM分析模块"""
                try:
                    for widget in dsym_frame.winfo_children():
                        widget.destroy()

                    from dsym_tab import DSYMTab
                    self.dsym_tab = DSYMTab(dsym_frame)
                    self.dsym_tab.frame.pack(fill=tk.BOTH, expand=True)
                    messagebox.showinfo("成功", "dSYM分析模块加载成功！")
                except ImportError as e:
                    messagebox.showerror("错误", f"仍无法加载dSYM分析模块：\n{str(e)}")

            ttk.Button(error_frame,
                      text="重试加载",
                      command=retry_load).pack(pady=10)

    def create_linkmap_analysis_tab(self):
        """创建LinkMap文件分析标签页"""
        linkmap_frame = ttk.Frame(self.main_notebook, padding="10")
        self.main_notebook.add(linkmap_frame, text="LinkMap分析")

        try:
            sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'gui', 'modules'))
            from linkmap_tab import LinkMapTab
            self.linkmap_tab = LinkMapTab(linkmap_frame)
            self.linkmap_tab.frame.pack(fill=tk.BOTH, expand=True)
        except ImportError as e:
            error_frame = ttk.Frame(linkmap_frame)
            error_frame.pack(fill=tk.BOTH, expand=True)

            ttk.Label(error_frame,
                     text="无法加载LinkMap分析模块",
                     font=('', 14, 'bold')).pack(pady=20)

            ttk.Label(error_frame,
                     text=f"错误详情: {str(e)}",
                     font=('', 10),
                     foreground='red').pack(pady=20)

            def retry_load():
                """重试加载LinkMap分析模块"""
                try:
                    for widget in linkmap_frame.winfo_children():
                        widget.destroy()

                    from linkmap_tab import LinkMapTab
                    self.linkmap_tab = LinkMapTab(linkmap_frame)
                    self.linkmap_tab.frame.pack(fill=tk.BOTH, expand=True)
                    messagebox.showinfo("成功", "LinkMap分析模块加载成功！")
                except ImportError as e:
                    messagebox.showerror("错误", f"仍无法加载LinkMap分析模块：\n{str(e)}")

            ttk.Button(error_frame,
                      text="重试加载",
                      command=retry_load).pack(pady=10)


def main():
    root = tk.Tk()
    app = MarsLogAnalyzerPro(root)
    root.mainloop()


if __name__ == "__main__":
    main()