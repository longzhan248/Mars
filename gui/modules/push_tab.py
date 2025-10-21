#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iOS推送测试标签页模块
"""

import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk

from .exceptions import (
    PushNotificationError,
    UIError,
    ErrorSeverity,
    handle_exceptions,
    get_global_error_collector
)

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

    @handle_exceptions(UIError, reraise=False, default_return=None)
    def create_widgets(self):
        """创建iOS推送测试标签页"""
        # 尝试导入推送工具模块
        try:
            from apns_gui import APNSPushGUI

            # 创建推送GUI实例
            self.push_gui = APNSPushGUI(self.parent)
            self.push_gui.pack(fill=tk.BOTH, expand=True)

        except ImportError as e:
            # 如果模块未找到，转换为结构化异常
            push_error = PushNotificationError(
                message=f"推送工具模块导入失败: {str(e)}",
                certificate_status="模块缺失",
                user_message="推送功能模块未找到，请检查安装",
                cause=e
            )
            get_global_error_collector().add_exception(push_error)
            self.show_dependency_error(e)
        except Exception as e:
            # 其他错误转换为UI异常
            ui_error = UIError(
                message=f"创建推送测试界面失败: {str(e)}",
                widget="推送测试标签页",
                action="界面初始化",
                user_message="推送功能初始化失败，请稍后重试",
                cause=e
            )
            get_global_error_collector().add_exception(ui_error)
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

    @handle_exceptions(PushNotificationError, reraise=False, default_return=None)
    def auto_install_dependencies(self):
        """自动安装依赖"""
        import subprocess

        try:
            # 使用pip安装依赖
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install",
                 "cryptography", "httpx", "pyjwt", "h2"],
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )

            if result.returncode == 0:
                messagebox.showinfo("成功", "依赖安装成功！请刷新标签页。")
                self.refresh_tab()
            else:
                # 分析安装失败原因
                error_msg = result.stderr
                if "Permission denied" in error_msg:
                    raise PushNotificationError(
                        message="权限不足，无法安装依赖",
                        certificate_status="安装失败",
                        user_message="权限不足，请以管理员权限运行程序",
                        severity=ErrorSeverity.HIGH
                    )
                elif "Network" in error_msg or "connection" in error_msg.lower():
                    raise PushNotificationError(
                        message="网络连接失败，无法安装依赖",
                        certificate_status="安装失败",
                        user_message="网络连接失败，请检查网络后重试",
                        severity=ErrorSeverity.MEDIUM
                    )
                else:
                    raise PushNotificationError(
                        message=f"依赖安装失败: {error_msg}",
                        certificate_status="安装失败",
                        user_message="依赖安装失败，请手动安装: pip install cryptography httpx pyjwt h2"
                    )

        except subprocess.TimeoutExpired:
            raise PushNotificationError(
                message="依赖安装超时",
                certificate_status="安装超时",
                user_message="安装过程超时，请检查网络连接或手动安装依赖",
                severity=ErrorSeverity.MEDIUM
            )
        except Exception as e:
            raise PushNotificationError(
                message=f"安装过程出错: {str(e)}",
                certificate_status="安装异常",
                user_message="依赖安装过程出现异常，请检查环境配置",
                cause=e
            )

    def refresh_tab(self):
        """刷新标签页"""
        # 清除当前内容
        for widget in self.parent.winfo_children():
            widget.destroy()

        # 重新创建
        self.create_widgets()