#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IPS崩溃日志解析标签页模块
"""

import os
import sys
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext


class IPSAnalysisTab:
    """IPS崩溃日志解析标签页"""

    def __init__(self, parent, main_app):
        """初始化IPS解析标签页

        Args:
            parent: 父容器
            main_app: 主应用程序实例
        """
        self.parent = parent
        self.main_app = main_app
        self.ips_data = None
        self.create_widgets()

    def create_widgets(self):
        """创建IPS解析标签页的界面"""
        # 主框架
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 顶部控制区
        control_frame = ttk.LabelFrame(main_frame, text="IPS文件操作", padding="10")
        control_frame.pack(fill=tk.X, pady=(0, 10))

        # 文件选择
        ttk.Button(control_frame, text="选择IPS文件",
                   command=self.select_ips_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="选择dSYM文件(可选)",
                   command=self.select_dsym_file).pack(side=tk.LEFT, padx=5)

        # 分隔符
        ttk.Separator(control_frame, orient='vertical').pack(side=tk.LEFT, fill=tk.Y, padx=10)

        # 解析选项
        self.symbolicate_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(control_frame, text="使用dSYM符号化",
                        variable=self.symbolicate_var).pack(side=tk.LEFT, padx=5)

        ttk.Button(control_frame, text="开始解析",
                   command=self.parse_ips_file,
                   style='Accent.TButton').pack(side=tk.LEFT, padx=10)

        # 导出按钮
        ttk.Separator(control_frame, orient='vertical').pack(side=tk.LEFT, fill=tk.Y, padx=10)
        ttk.Button(control_frame, text="导出报告",
                   command=self.export_ips_report).pack(side=tk.LEFT, padx=5)

        # 文件路径显示
        path_frame = ttk.Frame(main_frame)
        path_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(path_frame, text="IPS文件:").pack(side=tk.LEFT)
        self.ips_path_var = tk.StringVar(value="未选择")
        ttk.Label(path_frame, textvariable=self.ips_path_var,
                  foreground='blue').pack(side=tk.LEFT, padx=10)

        ttk.Label(path_frame, text="dSYM文件:").pack(side=tk.LEFT, padx=(20, 0))
        self.dsym_path_var = tk.StringVar(value="未选择")
        ttk.Label(path_frame, textvariable=self.dsym_path_var,
                  foreground='blue').pack(side=tk.LEFT, padx=10)

        # 创建标签页
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # 基本信息标签页
        self.info_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.info_frame, text="基本信息")
        self.create_info_tab()

        # 崩溃堆栈标签页
        self.stack_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.stack_frame, text="崩溃堆栈")
        self.create_stack_tab()

        # 线程信息标签页
        self.threads_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.threads_frame, text="所有线程")
        self.create_threads_tab()

        # 二进制镜像标签页
        self.images_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.images_frame, text="二进制镜像")
        self.create_images_tab()

        # 原始JSON标签页
        self.raw_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.raw_frame, text="原始数据")
        self.create_raw_tab()

    def create_info_tab(self):
        """创建基本信息标签页"""
        # 使用ScrolledText显示基本信息
        self.info_text = scrolledtext.ScrolledText(self.info_frame, wrap=tk.WORD, height=20)
        self.info_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def create_stack_tab(self):
        """创建崩溃堆栈标签页"""
        # 使用ScrolledText显示崩溃堆栈
        self.stack_text = scrolledtext.ScrolledText(self.stack_frame, wrap=tk.NONE, height=20)
        self.stack_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 配置标签样式
        self.stack_text.tag_configure("crashed", background="#ffcccc", font=("Courier", 10, "bold"))
        self.stack_text.tag_configure("address", foreground="#0066cc")
        self.stack_text.tag_configure("symbol", foreground="#006600", font=("Courier", 10, "bold"))

    def create_threads_tab(self):
        """创建线程信息标签页"""
        # 使用ScrolledText显示所有线程
        self.threads_text = scrolledtext.ScrolledText(self.threads_frame, wrap=tk.NONE, height=20)
        self.threads_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def create_images_tab(self):
        """创建二进制镜像标签页"""
        # 使用ScrolledText显示二进制镜像
        self.images_text = scrolledtext.ScrolledText(self.images_frame, wrap=tk.NONE, height=20)
        self.images_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def create_raw_tab(self):
        """创建原始数据标签页"""
        # 使用ScrolledText显示原始JSON
        self.raw_text = scrolledtext.ScrolledText(self.raw_frame, wrap=tk.NONE, height=20)
        self.raw_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def select_ips_file(self):
        """选择IPS文件"""
        filename = filedialog.askopenfilename(
            title="选择IPS崩溃日志文件",
            filetypes=[("IPS文件", "*.ips"), ("所有文件", "*.*")]
        )
        if filename:
            self.ips_path_var.set(filename)
            # 自动开始基本解析
            self.parse_ips_basic_info(filename)

    def select_dsym_file(self):
        """选择dSYM文件"""
        filename = filedialog.askopenfilename(
            title="选择dSYM符号文件",
            filetypes=[("dSYM文件", "*.dSYM"), ("所有文件", "*.*")]
        )
        if filename:
            self.dsym_path_var.set(filename)

    def parse_ips_basic_info(self, filename):
        """解析并显示IPS文件的基本信息"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                self.ips_data = json.load(f)

            # 显示基本信息
            info_text = self.extract_basic_info(self.ips_data)
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(tk.END, info_text)

            # 显示原始JSON
            self.raw_text.delete(1.0, tk.END)
            self.raw_text.insert(tk.END, json.dumps(self.ips_data, indent=2, ensure_ascii=False))

            messagebox.showinfo("成功", "IPS文件基本信息解析完成")
        except Exception as e:
            messagebox.showerror("错误", f"解析IPS文件失败: {str(e)}")

    def parse_ips_file(self):
        """完整解析IPS文件"""
        if not self.ips_path_var.get() or self.ips_path_var.get() == "未选择":
            messagebox.showwarning("警告", "请先选择IPS文件")
            return

        # 这里调用主应用的IPS解析功能
        if hasattr(self.main_app, 'parse_ips_with_osanalytics'):
            self.main_app.parse_ips_with_osanalytics(
                self.ips_path_var.get(),
                self.dsym_path_var.get() if self.dsym_path_var.get() != "未选择" else None
            )

    def export_ips_report(self):
        """导出IPS报告"""
        if not self.ips_data:
            messagebox.showwarning("警告", "没有可导出的IPS数据")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("JSON文件", "*.json"), ("所有文件", "*.*")]
        )

        if filename:
            try:
                if filename.endswith('.json'):
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(self.ips_data, f, indent=2, ensure_ascii=False)
                else:
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(self.generate_report_text())

                messagebox.showinfo("成功", f"报告已导出到: {filename}")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败: {str(e)}")

    def extract_basic_info(self, ips_data):
        """从IPS数据中提取基本信息"""
        info = []
        info.append("=" * 60)
        info.append("IPS崩溃日志基本信息")
        info.append("=" * 60)

        # 提取各种信息
        if 'app_name' in ips_data:
            info.append(f"应用名称: {ips_data['app_name']}")
        if 'app_version' in ips_data:
            info.append(f"应用版本: {ips_data['app_version']}")
        if 'bundleID' in ips_data:
            info.append(f"Bundle ID: {ips_data['bundleID']}")
        if 'incident_id' in ips_data:
            info.append(f"事件ID: {ips_data['incident_id']}")
        if 'timestamp' in ips_data:
            info.append(f"崩溃时间: {ips_data['timestamp']}")
        if 'bug_type' in ips_data:
            info.append(f"崩溃类型: {ips_data['bug_type']}")
        if 'os_version' in ips_data:
            info.append(f"系统版本: {ips_data['os_version']}")

        # 设备信息
        if 'device_model' in ips_data:
            info.append(f"设备型号: {ips_data['device_model']}")
        if 'platform' in ips_data:
            info.append(f"平台: {ips_data['platform']}")

        # 崩溃原因
        if 'termination_reason' in ips_data:
            info.append(f"\n终止原因: {ips_data['termination_reason']}")
        if 'exception_type' in ips_data:
            info.append(f"异常类型: {ips_data['exception_type']}")
        if 'exception_subtype' in ips_data:
            info.append(f"异常子类型: {ips_data['exception_subtype']}")

        return "\n".join(info)

    def generate_report_text(self):
        """生成文本格式的报告"""
        if not self.ips_data:
            return "无数据"

        report = []
        report.append("=" * 80)
        report.append("iOS崩溃报告分析")
        report.append("=" * 80)
        report.append("")

        # 基本信息
        report.append(self.extract_basic_info(self.ips_data))
        report.append("")

        # 崩溃堆栈
        if 'crashed_thread' in self.ips_data:
            report.append("=" * 60)
            report.append("崩溃线程堆栈")
            report.append("=" * 60)
            # 这里可以添加更详细的堆栈信息

        return "\n".join(report)