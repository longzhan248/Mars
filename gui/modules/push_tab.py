#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iOS推送测试标签页模块
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox

# 添加push_tools路径
push_tools_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'push_tools')
if push_tools_path not in sys.path:
    sys.path.insert(0, push_tools_path)


class PushTestTab:
    """iOS推送测试标签页"""

    def __init__(self, parent, main_app):
        """初始化推送测试标签页

        Args:
            parent: 父容器
            main_app: 主应用程序实例
        """
        self.parent = parent
        self.main_app = main_app
        self.push_gui = None
        self.create_widgets()

    def create_widgets(self):
        """创建iOS推送测试标签页"""
        # 尝试导入推送工具模块
        try:
            from apns_gui import APNSPushGUI

            # 创建推送GUI实例
            self.push_gui = APNSPushGUI(self.parent)
            self.push_gui.pack(fill=tk.BOTH, expand=True)

        except ImportError as e:
            # 如果模块未找到，显示安装提示
            self.show_dependency_error(e)
        except Exception as e:
            # 其他错误
            self.show_general_error(e)

    def show_dependency_error(self, error):
        """显示依赖错误信息"""
        error_frame = ttk.Frame(self.parent)
        error_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 错误信息
        error_text = f"""
iOS推送功能无法加载

缺少必要的依赖包: {str(error)}

请按照以下步骤安装依赖：

1. 确保在项目根目录下
2. 运行以下命令：

   # macOS/Linux:
   ./scripts/run_analyzer.sh

   # 或手动安装:
   pip install cryptography httpx pyjwt h2

3. 重新启动程序

如果问题持续，请检查：
- Python版本是否为3.6+
- 虚拟环境是否正确激活
- requirements.txt中的依赖是否完整
"""

        # 创建文本显示
        text_widget = tk.Text(error_frame, wrap=tk.WORD, height=20)
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert(tk.END, error_text)
        text_widget.config(state=tk.DISABLED)

        # 按钮框架
        button_frame = ttk.Frame(error_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        # 安装依赖按钮
        ttk.Button(
            button_frame,
            text="自动安装依赖",
            command=self.auto_install_dependencies
        ).pack(side=tk.LEFT, padx=5)

        # 刷新按钮
        ttk.Button(
            button_frame,
            text="刷新",
            command=self.refresh_tab
        ).pack(side=tk.LEFT, padx=5)

    def show_general_error(self, error):
        """显示一般错误信息"""
        error_frame = ttk.Frame(self.parent)
        error_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        error_text = f"""
iOS推送功能加载失败

错误信息：{str(error)}

请尝试：
1. 重新启动程序
2. 检查push_tools目录是否存在
3. 查看控制台输出获取更多信息
"""

        # 创建文本显示
        text_widget = tk.Text(error_frame, wrap=tk.WORD, height=10)
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert(tk.END, error_text)
        text_widget.config(state=tk.DISABLED)

        # 刷新按钮
        ttk.Button(
            error_frame,
            text="刷新",
            command=self.refresh_tab
        ).pack(pady=10)

    def auto_install_dependencies(self):
        """自动安装依赖"""
        import subprocess

        try:
            # 使用pip安装依赖
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install",
                 "cryptography", "httpx", "pyjwt", "h2"],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                messagebox.showinfo("成功", "依赖安装成功！请刷新标签页。")
                self.refresh_tab()
            else:
                messagebox.showerror(
                    "错误",
                    f"依赖安装失败:\n{result.stderr}"
                )
        except Exception as e:
            messagebox.showerror("错误", f"安装过程出错: {str(e)}")

    def refresh_tab(self):
        """刷新标签页"""
        # 清除当前内容
        for widget in self.parent.winfo_children():
            widget.destroy()

        # 重新创建
        self.create_widgets()