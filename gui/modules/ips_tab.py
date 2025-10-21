#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IPS崩溃日志解析标签页模块
"""

import json
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

from .exceptions import (
    IPSAnalysisError,
    FileOperationError,
    UIError,
    ErrorSeverity,
    handle_exceptions,
    get_global_error_collector
)


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

    @handle_exceptions(IPSAnalysisError, reraise=False, default_return=None)
    def parse_ips_basic_info(self, filename):
        """解析并显示IPS文件的基本信息"""
        if not filename or not filename.strip():
            raise IPSAnalysisError(
                message="IPS文件路径为空",
                file_path=filename,
                user_message="请选择有效的IPS文件",
                severity=ErrorSeverity.MEDIUM
            )

        try:
            # 检查文件是否存在
            import os
            if not os.path.exists(filename):
                raise IPSAnalysisError(
                    message="IPS文件不存在",
                    file_path=filename,
                    user_message="选择的IPS文件不存在，请检查文件路径",
                    severity=ErrorSeverity.HIGH
                )

            # 检查文件大小
            file_size = os.path.getsize(filename)
            if file_size == 0:
                raise IPSAnalysisError(
                    message="IPS文件为空",
                    file_path=filename,
                    user_message="选择的IPS文件为空，请选择有效的崩溃报告",
                    severity=ErrorSeverity.HIGH
                )
            elif file_size > 50 * 1024 * 1024:  # 50MB限制
                raise IPSAnalysisError(
                    message=f"IPS文件过大 ({file_size/1024/1024:.1f}MB)",
                    file_path=filename,
                    user_message="IPS文件过大，请选择小于50MB的文件",
                    severity=ErrorSeverity.MEDIUM
                )

            with open(filename, 'r', encoding='utf-8') as f:
                self.ips_data = json.load(f)

            # 验证IPS数据结构
            if not isinstance(self.ips_data, dict):
                raise IPSAnalysisError(
                    message="IPS文件格式无效，不是JSON对象",
                    file_path=filename,
                    user_message="IPS文件格式已损坏，请选择有效的崩溃报告",
                    severity=ErrorSeverity.HIGH
                )

            # 检查关键字段
            required_fields = ['incident_id', 'timestamp']
            missing_fields = [field for field in required_fields if field not in self.ips_data]
            if missing_fields:
                raise IPSAnalysisError(
                    message=f"IPS文件缺少关键字段: {', '.join(missing_fields)}",
                    file_path=filename,
                    user_message="IPS文件格式不完整，可能已损坏",
                    severity=ErrorSeverity.MEDIUM
                )

            # 显示基本信息
            info_text = self.extract_basic_info(self.ips_data)
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(tk.END, info_text)

            # 显示原始JSON
            self.raw_text.delete(1.0, tk.END)
            self.raw_text.insert(tk.END, json.dumps(self.ips_data, indent=2, ensure_ascii=False))

            messagebox.showinfo("成功", "IPS文件基本信息解析完成")

        except json.JSONDecodeError as e:
            raise IPSAnalysisError(
                message=f"JSON解析失败: {str(e)}",
                file_path=filename,
                user_message="IPS文件不是有效的JSON格式，可能已损坏",
                cause=e,
                severity=ErrorSeverity.HIGH
            )
        except UnicodeDecodeError as e:
            raise IPSAnalysisError(
                message=f"文件编码错误: {str(e)}",
                file_path=filename,
                user_message="IPS文件编码格式不支持，请确保为UTF-8格式",
                cause=e,
                severity=ErrorSeverity.HIGH
            )
        except PermissionError as e:
            raise IPSAnalysisError(
                message="文件权限不足，无法读取",
                file_path=filename,
                user_message="没有权限读取该文件，请检查文件权限设置",
                cause=e,
                severity=ErrorSeverity.HIGH
            )
        except Exception as e:
            # 重新抛出已经处理的异常
            if isinstance(e, IPSAnalysisError):
                raise e

            # 处理其他未预期的异常
            raise IPSAnalysisError(
                message=f"解析IPS文件时发生未知错误: {str(e)}",
                file_path=filename,
                user_message="解析IPS文件时发生错误，请检查文件是否完整",
                cause=e,
                severity=ErrorSeverity.HIGH
            )

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

    @handle_exceptions(FileOperationError, reraise=False, default_return=None)
    def export_ips_report(self):
        """导出IPS报告"""
        if not self.ips_data:
            raise UIError(
                message="没有可导出的IPS数据",
                widget="导出报告按钮",
                action="导出IPS报告",
                user_message="请先加载IPS文件后再导出报告",
                severity=ErrorSeverity.MEDIUM
            )

        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("JSON文件", "*.json"), ("所有文件", "*.*")]
        )

        if not filename:
            return  # 用户取消了保存

        try:
            # 检查文件路径是否有效
            import os
            output_dir = os.path.dirname(filename)
            if output_dir and not os.path.exists(output_dir):
                raise FileOperationError(
                    message="输出目录不存在",
                    file_path=filename,
                    operation="导出IPS报告",
                    user_message="选择的保存路径不存在，请选择有效的目录",
                    severity=ErrorSeverity.HIGH
                )

            # 检查是否有写入权限
            if output_dir and not os.access(output_dir, os.W_OK):
                raise FileOperationError(
                    message="没有写入权限",
                    file_path=filename,
                    operation="导出IPS报告",
                    user_message="没有权限在该目录写入文件，请选择其他目录",
                    severity=ErrorSeverity.HIGH
                )

            if filename.endswith('.json'):
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.ips_data, f, indent=2, ensure_ascii=False)
            else:
                report_content = self.generate_report_text()
                if not report_content or report_content == "无数据":
                    raise FileOperationError(
                        message="生成的报告内容为空",
                        file_path=filename,
                        operation="导出IPS报告",
                        user_message="IPS数据不完整，无法生成有效报告",
                        severity=ErrorSeverity.MEDIUM
                    )

                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(report_content)

            messagebox.showinfo("成功", f"报告已导出到: {filename}")

        except PermissionError as e:
            raise FileOperationError(
                message="文件权限不足，无法写入",
                file_path=filename,
                operation="导出IPS报告",
                user_message="没有权限写入该文件，请检查文件权限或选择其他路径",
                cause=e,
                severity=ErrorSeverity.HIGH
            )
        except UnicodeEncodeError as e:
            raise FileOperationError(
                message="文件编码错误，无法写入",
                file_path=filename,
                operation="导出IPS报告",
                user_message="文件编码出现问题，请尝试其他保存位置",
                cause=e,
                severity=ErrorSeverity.MEDIUM
            )
        except Exception as e:
            # 重新抛出已处理的异常
            if isinstance(e, (FileOperationError, UIError)):
                raise e

            # 处理其他未预期的异常
            raise FileOperationError(
                message=f"导出IPS报告时发生未知错误: {str(e)}",
                file_path=filename,
                operation="导出IPS报告",
                user_message="导出报告时发生错误，请稍后重试",
                cause=e,
                severity=ErrorSeverity.MEDIUM
            )

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