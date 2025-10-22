"""
工具栏面板UI组件
提供导航、设置、导出等工具按钮
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys


class ToolbarPanel(ttk.Frame):
    """工具栏面板"""

    def __init__(self, parent, panel):
        super().__init__(parent)
        self.panel = panel
        self.back_button = None
        self.forward_button = None
        self.quick_frame = None

        self.create_widgets()

    def create_widgets(self):
        """创建工具栏UI"""
        # 标题栏
        title_frame = ttk.Frame(self)
        title_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(
            title_frame,
            text="🤖 AI助手",
            font=("Arial", 14, "bold")
        ).pack(side=tk.LEFT)

        # 跳转历史按钮（后退和前进）
        self.back_button = ttk.Button(
            title_frame,
            text="◀",
            width=3,
            command=self.panel.navigation.jump_back,
            state=tk.DISABLED  # 初始禁用
        )
        self.back_button.pack(side=tk.LEFT, padx=2)

        self.forward_button = ttk.Button(
            title_frame,
            text="▶",
            width=3,
            command=self.panel.navigation.jump_forward,
            state=tk.DISABLED  # 初始禁用
        )
        self.forward_button.pack(side=tk.LEFT, padx=2)

        # 自定义Prompt按钮
        ttk.Button(
            title_frame,
            text="📝",
            width=3,
            command=self.show_custom_prompts
        ).pack(side=tk.RIGHT, padx=2)

        # 设置按钮
        ttk.Button(
            title_frame,
            text="⚙️",
            width=3,
            command=self.show_settings
        ).pack(side=tk.RIGHT, padx=2)

        # 清空对话按钮
        ttk.Button(
            title_frame,
            text="🗑️",
            width=3,
            command=self.confirm_clear_chat
        ).pack(side=tk.RIGHT, padx=2)

        # 导出对话按钮
        ttk.Button(
            title_frame,
            text="💾",
            width=3,
            command=self.panel.chat_panel.export_chat
        ).pack(side=tk.RIGHT, padx=2)

        # 快捷操作区域（动态生成自定义Prompt快捷按钮）
        self.quick_frame = ttk.LabelFrame(self, text="快捷操作", padding="5")
        self.quick_frame.pack(fill=tk.X, pady=(0, 5))

        # 动态加载快捷按钮
        self._load_shortcut_buttons()

    def update_navigation_buttons(self, back_enabled, forward_enabled):
        """更新导航按钮状态"""
        if self.back_button:
            self.back_button.config(state=tk.NORMAL if back_enabled else tk.DISABLED)
        if self.forward_button:
            self.forward_button.config(state=tk.NORMAL if forward_enabled else tk.DISABLED)

    def _load_shortcut_buttons(self):
        """动态加载自定义Prompt快捷按钮"""
        # 清空现有按钮
        for widget in self.quick_frame.winfo_children():
            widget.destroy()

        # 获取自定义prompt管理器
        try:
            from ..ai_diagnosis.custom_prompt_manager import get_custom_prompt_manager
            manager = get_custom_prompt_manager()
        except ImportError:
            try:
                from ai_diagnosis.custom_prompt_manager import get_custom_prompt_manager
                manager = get_custom_prompt_manager()
            except ImportError:
                try:
                    gui_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                    if gui_dir not in sys.path:
                        sys.path.insert(0, gui_dir)
                    from modules.ai_diagnosis.custom_prompt_manager import (
                        get_custom_prompt_manager,
                    )
                    manager = get_custom_prompt_manager()
                except ImportError:
                    # 无法加载管理器，显示提示
                    ttk.Label(
                        self.quick_frame,
                        text="无法加载快捷操作。请在自定义Prompt中配置。",
                        foreground="#666666"
                    ).pack(pady=10)
                    return

        # 获取所有快捷按钮Prompt
        shortcuts = manager.get_shortcuts()

        if not shortcuts:
            # 没有快捷按钮，显示提示
            ttk.Label(
                self.quick_frame,
                text="暂无快捷操作。点击右上角📝按钮创建自定义Prompt并设置为快捷按钮。",
                foreground="#666666",
                wraplength=250
            ).pack(pady=10)
            return

        # 创建按钮（2列布局）
        for i, prompt in enumerate(shortcuts):
            row = i // 2
            col = i % 2

            # 创建按钮（使用lambda捕获prompt.id）
            btn = ttk.Button(
                self.quick_frame,
                text=f"{prompt.name[:15]}...",  # 限制按钮文本长度
                command=lambda pid=prompt.id: self.panel.prompt_panel.use_prompt(pid)
            )
            btn.grid(row=row, column=col, padx=2, pady=2, sticky="ew")

            # 设置工具提示（显示完整名称和描述）
            self._create_tooltip(btn, f"{prompt.name}\n{prompt.description}")

        # 配置列权重，使按钮均分空间
        self.quick_frame.columnconfigure(0, weight=1)
        self.quick_frame.columnconfigure(1, weight=1)

    def _create_tooltip(self, widget, text):
        """为widget创建工具提示"""
        def on_enter(event):
            """鼠标进入事件处理函数"""
            # 创建提示窗口
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_attributes("-topmost", True)

            # 设置位置
            x = event.x_root + 10
            y = event.y_root + 10
            tooltip.wm_geometry(f"+{x}+{y}")

            # 创建标签
            label = tk.Label(
                tooltip,
                text=text,
                background="#FFFFCC",
                relief=tk.SOLID,
                borderwidth=1,
                font=("Arial", 9),
                padx=5,
                pady=5
            )
            label.pack()

            # 保存引用
            widget._tooltip = tooltip

        def on_leave(event):
            """鼠标离开事件处理函数"""
            # 销毁提示窗口
            if hasattr(widget, '_tooltip'):
                try:
                    widget._tooltip.destroy()
                    del widget._tooltip
                except:
                    pass

        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    def confirm_clear_chat(self):
        """确认并清空对话历史"""
        if not self.panel.chat_history:
            messagebox.showinfo("提示", "对话历史已经是空的")
            return

        # 弹出确认对话框
        result = messagebox.askyesno(
            "确认清空",
            "确定要清空所有对话历史吗？\n此操作不可恢复。"
        )

        if result:
            self.panel.chat_panel.clear_chat()
            self.panel.chat_panel.append_chat("system", "对话历史已清空")

    def show_settings(self):
        """显示设置对话框"""
        # 导入设置对话框
        try:
            from ai_diagnosis_settings import AISettingsDialog
        except ImportError:
            try:
                from modules.ai_diagnosis_settings import AISettingsDialog
            except ImportError:
                from gui.modules.ai_diagnosis_settings import AISettingsDialog

        # 创建设置对话框
        dialog = AISettingsDialog(self.panel.parent, self.panel.main_app)

        # 如果设置被修改,重置AI客户端
        if hasattr(dialog, 'settings_changed') and dialog.settings_changed:
            self.panel._ai_client = None
            self.panel.chat_panel.append_chat("system", "AI设置已更新")

    def show_custom_prompts(self):
        """显示自定义Prompt对话框"""
        try:
            # 尝试相对导入（在gui/modules/目录下运行时）
            from ..custom_prompt_dialog import show_custom_prompt_dialog
        except ImportError:
            try:
                # 尝试直接导入（在gui/目录下运行时）
                from custom_prompt_dialog import show_custom_prompt_dialog
            except ImportError:
                # 添加路径并导入
                gui_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                if gui_dir not in sys.path:
                    sys.path.insert(0, gui_dir)
                from modules.custom_prompt_dialog import show_custom_prompt_dialog

        # 显示对话框
        show_custom_prompt_dialog(self.panel.parent)

        # 重新加载快捷按钮
        self._load_shortcut_buttons()

    def show_prompt_selector(self):
        """显示Prompt选择器（委托给PromptPanel）"""
        self.panel.prompt_panel.show_selector()
