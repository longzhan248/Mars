#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mars日志分析器专业版 - 模块化重构版本
保持原有功能完全一致，但代码组织更加模块化
"""

import os
import sys
import re
import threading
import queue
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
from collections import Counter, defaultdict

# 添加模块路径
current_dir = os.path.dirname(os.path.abspath(__file__))
modules_path = os.path.join(current_dir, 'modules')
components_path = os.path.join(current_dir, 'components')
parent_dir = os.path.dirname(current_dir)
decoders_path = os.path.join(parent_dir, 'decoders')
tools_path = os.path.join(parent_dir, 'tools')
push_tools_path = os.path.join(parent_dir, 'push_tools')

for path in [modules_path, components_path, decoders_path, tools_path, push_tools_path]:
    if path not in sys.path:
        sys.path.insert(0, path)

# 导入模块化组件
try:
    # 尝试相对导入（从gui目录运行时）
    from modules.data_models import LogEntry, FileGroup
    from modules.file_operations import FileOperations
    from modules.filter_search import FilterSearchManager
    from modules.ips_tab import IPSAnalysisTab
    from modules.push_tab import PushTestTab
    from modules.sandbox_tab import SandboxBrowserTab
except ImportError:
    # 绝对导入（从项目根目录运行时）
    from gui.modules.data_models import LogEntry, FileGroup
    from gui.modules.file_operations import FileOperations
    from gui.modules.filter_search import FilterSearchManager
    from gui.modules.ips_tab import IPSAnalysisTab
    from gui.modules.push_tab import PushTestTab
    from gui.modules.sandbox_tab import SandboxBrowserTab

# 导入原有组件
try:
    from components.improved_lazy_text import ImprovedLazyText
except ImportError:
    try:
        from improved_lazy_text import ImprovedLazyText
    except ImportError:
        from scrolled_text_with_lazy_load import ScrolledTextWithLazyLoad as ImprovedLazyText

# 导入原mars_log_analyzer_pro.py中的MarsLogAnalyzerPro类
# 使用原始文件作为基类，保证功能完全一致
try:
    from mars_log_analyzer_pro import MarsLogAnalyzerPro as OriginalMarsLogAnalyzerPro
except ImportError:
    from gui.mars_log_analyzer_pro import MarsLogAnalyzerPro as OriginalMarsLogAnalyzerPro


class MarsLogAnalyzerPro(OriginalMarsLogAnalyzerPro):
    """
    Mars日志分析器专业版 - 模块化版本
    继承原有类，逐步重构为使用模块化组件
    """

    def __init__(self, root):
        """初始化应用程序"""
        # 初始化模块化组件
        self.file_ops = FileOperations()
        self.filter_manager = FilterSearchManager()

        # 调用父类初始化
        super().__init__(root)

    # 重写使用模块化组件的方法
    def parse_time_string(self, time_str):
        """使用模块化的时间解析"""
        return self.filter_manager.parse_time_string(time_str)

    def compare_log_time(self, log_timestamp, start_time, end_time):
        """使用模块化的时间比较"""
        return self.filter_manager.compare_log_time(log_timestamp, start_time, end_time)

    def apply_global_filter(self):
        """使用模块化的过滤功能"""
        if not self.log_entries:
            return

        # 获取所有过滤条件
        keyword = self.search_var.get()
        search_mode = self.search_mode_var.get()
        level_filter = self.level_var.get()
        module_filter = self.module_var.get()
        start_time = self.global_time_start_var.get()
        end_time = self.global_time_end_var.get()

        # 使用模块化的过滤器
        filtered = self.filter_manager.filter_entries(
            self.log_entries,
            level=level_filter,
            module=module_filter,
            keyword=keyword,
            start_time=start_time,
            end_time=end_time,
            search_mode=search_mode
        )

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

        # 更新文件统计标签
        if hasattr(self, 'file_stats_var'):
            self.file_stats_var.set(stats_text)

    def create_ips_analysis_tab(self):
        """创建IPS解析标签页 - 使用模块化组件"""
        ips_frame = ttk.Frame(self.main_notebook, padding="10")
        self.main_notebook.add(ips_frame, text="IPS崩溃解析")

        # 使用模块化的IPS标签页
        self.ips_tab = IPSAnalysisTab(ips_frame, self)

    def create_push_test_tab(self):
        """创建iOS推送测试标签页 - 使用模块化组件"""
        push_frame = ttk.Frame(self.main_notebook, padding="10")
        self.main_notebook.add(push_frame, text="iOS推送测试")

        # 使用模块化的推送标签页
        self.push_tab = PushTestTab(push_frame, self)

    def create_sandbox_browser_tab(self):
        """创建iOS沙盒浏览标签页 - 使用模块化组件"""
        sandbox_frame = ttk.Frame(self.main_notebook, padding="10")
        self.main_notebook.add(sandbox_frame, text="iOS沙盒浏览")

        # 使用模块化的沙盒浏览标签页
        self.sandbox_tab = SandboxBrowserTab(sandbox_frame, self)

    def create_dsym_analysis_tab(self):
        """创建dSYM文件分析标签页"""
        from modules.dsym_tab import DSYMTab

        dsym_frame = ttk.Frame(self.main_notebook, padding="10")
        self.main_notebook.add(dsym_frame, text="dSYM分析")

        # 使用模块化的dSYM标签页
        self.dsym_tab = DSYMTab(dsym_frame)
        self.dsym_tab.frame.pack(fill=tk.BOTH, expand=True)

    def create_linkmap_analysis_tab(self):
        """创建LinkMap文件分析标签页"""
        from modules.linkmap_tab import LinkMapTab

        linkmap_frame = ttk.Frame(self.main_notebook, padding="10")
        self.main_notebook.add(linkmap_frame, text="LinkMap分析")

        # 使用模块化的LinkMap标签页
        self.linkmap_tab = LinkMapTab(linkmap_frame)
        self.linkmap_tab.frame.pack(fill=tk.BOTH, expand=True)

    def filter_logs(self, start_time=None, end_time=None):
        """重写filter_logs方法以使用模块化的过滤逻辑

        保持与原始版本相同的接口，但使用apply_global_filter的统一逻辑
        """
        # 如果提供了时间参数，更新全局时间过滤器
        if start_time is not None:
            self.global_time_start_var.set(start_time if start_time else '')
        if end_time is not None:
            self.global_time_end_var.set(end_time if end_time else '')

        # 使用apply_global_filter的统一逻辑
        self.apply_global_filter()

    def export_current_view(self):
        """导出当前视图的日志 - 使用模块化导出"""
        if not self.filtered_entries:
            messagebox.showwarning("警告", "没有可导出的数据")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".log",
            filetypes=[
                ("日志文件", "*.log"),
                ("文本文件", "*.txt"),
                ("JSON文件", "*.json"),
                ("CSV文件", "*.csv"),
                ("所有文件", "*.*")
            ]
        )

        if not filename:
            return

        try:
            # 确定导出格式
            format = 'txt'
            if filename.endswith('.json'):
                format = 'json'
            elif filename.endswith('.csv'):
                format = 'csv'

            # 使用模块化的导出功能
            if self.file_ops.export_to_file(self.filtered_entries, filename, format):
                messagebox.showinfo("成功", f"已导出 {len(self.filtered_entries)} 条日志到:\n{filename}")
            else:
                messagebox.showerror("错误", "导出失败")

        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {str(e)}")


def main():
    """主程序入口"""
    root = tk.Tk()
    app = MarsLogAnalyzerPro(root)
    root.mainloop()


if __name__ == "__main__":
    main()