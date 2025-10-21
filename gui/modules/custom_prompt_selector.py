"""
自定义Prompt快捷选择器

提供快捷的自定义Prompt选择功能，用于右键菜单和工具栏。
"""

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, List


class CustomPromptSelector:
    """自定义Prompt快捷选择器"""

    def __init__(self, parent, on_prompt_selected: Callable[[str], None]):
        """
        初始化选择器

        Args:
            parent: 父窗口
            on_prompt_selected: 选择Prompt后的回调函数，参数为prompt_id
        """
        self.parent = parent
        self.on_prompt_selected = on_prompt_selected
        self.manager = None

        # 导入管理器
        self._load_manager()

    def _load_manager(self):
        """加载自定义Prompt管理器"""
        try:
            from .ai_diagnosis.custom_prompt_manager import get_custom_prompt_manager
            self.manager = get_custom_prompt_manager()
        except ImportError:
            try:
                from ai_diagnosis.custom_prompt_manager import get_custom_prompt_manager
                self.manager = get_custom_prompt_manager()
            except ImportError:
                try:
                    import os
                    import sys
                    gui_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    if gui_dir not in sys.path:
                        sys.path.insert(0, gui_dir)
                    from modules.ai_diagnosis.custom_prompt_manager import (
                        get_custom_prompt_manager,
                    )
                    self.manager = get_custom_prompt_manager()
                except ImportError as e:
                    print(f"无法加载自定义Prompt管理器: {e}")
                    self.manager = None

    def get_enabled_prompts(self) -> List:
        """
        获取所有已启用的自定义Prompt

        Returns:
            已启用的Prompt列表
        """
        if not self.manager:
            return []

        return self.manager.list_all(enabled_only=True)

    def create_menu(self, parent_menu: tk.Menu):
        """
        创建自定义Prompt子菜单

        Args:
            parent_menu: 父菜单对象
        """
        if not self.manager:
            parent_menu.add_command(
                label="📝 使用自定义Prompt (未初始化)",
                state=tk.DISABLED
            )
            return

        # 获取已启用的Prompt
        prompts = self.get_enabled_prompts()

        if not prompts:
            parent_menu.add_command(
                label="📝 使用自定义Prompt (暂无可用)",
                state=tk.DISABLED
            )
            return

        # 创建子菜单
        custom_menu = tk.Menu(parent_menu, tearoff=0)
        parent_menu.add_cascade(
            label="📝 使用自定义Prompt",
            menu=custom_menu
        )

        # 按分类分组
        prompts_by_category = {}
        for prompt in prompts:
            category = prompt.category
            if category not in prompts_by_category:
                prompts_by_category[category] = []
            prompts_by_category[category].append(prompt)

        # 添加分类和Prompt
        for category, category_prompts in sorted(prompts_by_category.items()):
            if len(prompts_by_category) > 1:
                # 有多个分类时，创建分类子菜单
                category_menu = tk.Menu(custom_menu, tearoff=0)
                custom_menu.add_cascade(label=category, menu=category_menu)

                for prompt in sorted(category_prompts, key=lambda p: p.name):
                    category_menu.add_command(
                        label=prompt.name,
                        command=lambda pid=prompt.id: self.on_prompt_selected(pid)
                    )
            else:
                # 只有一个分类，直接添加Prompt
                for prompt in sorted(category_prompts, key=lambda p: p.name):
                    custom_menu.add_command(
                        label=prompt.name,
                        command=lambda pid=prompt.id: self.on_prompt_selected(pid)
                    )

        # 添加分隔符和管理入口
        custom_menu.add_separator()
        custom_menu.add_command(
            label="⚙️ 管理自定义Prompt...",
            command=self._open_manager
        )

    def create_dropdown_button(self, parent_frame, side=tk.LEFT, padx=2):
        """
        创建下拉按钮（用于工具栏）

        Args:
            parent_frame: 父框架
            side: 放置位置
            padx: 水平间距

        Returns:
            创建的按钮对象
        """
        # 创建按钮
        btn = ttk.Button(
            parent_frame,
            text="📝 自定义Prompt ▼",
            command=self._show_dropdown_menu,
            width=16
        )
        btn.pack(side=side, padx=padx)

        # 保存按钮引用
        self._dropdown_button = btn

        return btn

    def _show_dropdown_menu(self):
        """显示下拉菜单"""
        if not self.manager:
            messagebox.showwarning("提示", "自定义Prompt管理器未初始化")
            return

        # 获取已启用的Prompt
        prompts = self.get_enabled_prompts()

        if not prompts:
            messagebox.showinfo("提示", "暂无可用的自定义Prompt\n请先在管理器中创建并启用模板")
            return

        # 创建下拉菜单
        menu = tk.Menu(self.parent, tearoff=0)

        # 按分类分组
        prompts_by_category = {}
        for prompt in prompts:
            category = prompt.category
            if category not in prompts_by_category:
                prompts_by_category[category] = []
            prompts_by_category[category].append(prompt)

        # 添加分类和Prompt
        for category, category_prompts in sorted(prompts_by_category.items()):
            # 添加分类标题（禁用，仅作分隔）
            if len(prompts_by_category) > 1:
                menu.add_command(
                    label=f"━━ {category} ━━",
                    state=tk.DISABLED,
                    background="#F0F0F0"
                )

            # 添加Prompt
            for prompt in sorted(category_prompts, key=lambda p: p.name):
                menu.add_command(
                    label=f"  {prompt.name}",
                    command=lambda pid=prompt.id: self._on_prompt_click(pid)
                )

            # 分类间添加分隔符
            if len(prompts_by_category) > 1:
                menu.add_separator()

        # 添加管理入口
        menu.add_separator()
        menu.add_command(
            label="⚙️ 管理自定义Prompt...",
            command=self._open_manager
        )

        # 显示菜单（在按钮下方）
        if hasattr(self, '_dropdown_button'):
            btn = self._dropdown_button
            x = btn.winfo_rootx()
            y = btn.winfo_rooty() + btn.winfo_height()
            menu.tk_popup(x, y)
        else:
            # 后备方案：在鼠标位置显示
            menu.tk_popup(
                self.parent.winfo_pointerx(),
                self.parent.winfo_pointery()
            )

    def _on_prompt_click(self, prompt_id: str):
        """处理Prompt点击事件"""
        # 调用回调函数
        self.on_prompt_selected(prompt_id)

    def _open_manager(self):
        """打开Prompt管理器"""
        try:
            from .custom_prompt_dialog import show_custom_prompt_dialog
        except ImportError:
            try:
                from custom_prompt_dialog import show_custom_prompt_dialog
            except ImportError:
                try:
                    from modules.custom_prompt_dialog import show_custom_prompt_dialog
                except ImportError:
                    import os
                    import sys
                    gui_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    if gui_dir not in sys.path:
                        sys.path.insert(0, gui_dir)
                    from modules.custom_prompt_dialog import show_custom_prompt_dialog

        show_custom_prompt_dialog(self.parent)


class MultiPromptSelector:
    """多Prompt组合选择器"""

    def __init__(self, parent, on_prompts_selected: Callable[[List[str]], None]):
        """
        初始化多Prompt选择器

        Args:
            parent: 父窗口
            on_prompts_selected: 选择Prompt后的回调函数，参数为prompt_id列表
        """
        self.parent = parent
        self.on_prompts_selected = on_prompts_selected
        self.manager = None

        # 导入管理器
        self._load_manager()

    def _load_manager(self):
        """加载自定义Prompt管理器"""
        try:
            from .ai_diagnosis.custom_prompt_manager import get_custom_prompt_manager
            self.manager = get_custom_prompt_manager()
        except ImportError:
            try:
                from ai_diagnosis.custom_prompt_manager import get_custom_prompt_manager
                self.manager = get_custom_prompt_manager()
            except ImportError:
                try:
                    import os
                    import sys
                    gui_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    if gui_dir not in sys.path:
                        sys.path.insert(0, gui_dir)
                    from modules.ai_diagnosis.custom_prompt_manager import (
                        get_custom_prompt_manager,
                    )
                    self.manager = get_custom_prompt_manager()
                except ImportError as e:
                    print(f"无法加载自定义Prompt管理器: {e}")
                    self.manager = None

    def show_dialog(self):
        """显示多Prompt选择对话框"""
        if not self.manager:
            messagebox.showwarning("提示", "自定义Prompt管理器未初始化")
            return

        # 获取已启用的Prompt
        prompts = self.manager.list_all(enabled_only=True)

        if not prompts:
            messagebox.showinfo("提示", "暂无可用的自定义Prompt\n请先在管理器中创建并启用模板")
            return

        # 创建对话框
        dialog = tk.Toplevel(self.parent)
        dialog.title("选择多个Prompt")
        dialog.geometry("500x600")
        dialog.transient(self.parent)
        dialog.grab_set()

        # 说明
        ttk.Label(
            dialog,
            text="选择一个或多个Prompt进行组合分析：",
            font=("Arial", 11)
        ).pack(pady=10, padx=10, anchor=tk.W)

        # 创建列表框（支持多选）
        list_frame = ttk.Frame(dialog)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # 树形列表
        columns = ("名称", "分类", "描述")
        tree = ttk.Treeview(list_frame, columns=columns, show='tree headings', selectmode='extended')

        tree.column("#0", width=0, stretch=tk.NO)
        tree.column("名称", width=150)
        tree.column("分类", width=100)
        tree.column("描述", width=200)

        tree.heading("名称", text="名称")
        tree.heading("分类", text="分类")
        tree.heading("描述", text="描述")

        # 添加Prompt到列表
        for prompt in prompts:
            tree.insert(
                "",
                tk.END,
                iid=prompt.id,
                values=(prompt.name, prompt.category, prompt.description[:50])
            )

        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 提示
        ttk.Label(
            dialog,
            text="提示：按住Ctrl/Cmd点击可选择多个Prompt",
            font=("Arial", 9),
            foreground="#666666"
        ).pack(pady=(0, 10))

        # 底部按钮
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        def on_confirm():
            # 获取选中的Prompt ID
            selected_ids = tree.selection()
            if not selected_ids:
                messagebox.showwarning("提示", "请至少选择一个Prompt")
                return

            # 关闭对话框
            dialog.destroy()

            # 调用回调函数
            self.on_prompts_selected(list(selected_ids))

        ttk.Button(btn_frame, text="确定", command=on_confirm, width=12).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="取消", command=dialog.destroy, width=12).pack(side=tk.RIGHT)


# 便捷函数
def create_prompt_selector(parent, on_selected: Callable[[str], None]) -> CustomPromptSelector:
    """
    创建自定义Prompt选择器

    Args:
        parent: 父窗口
        on_selected: 选择回调函数

    Returns:
        选择器对象
    """
    return CustomPromptSelector(parent, on_selected)


def create_multi_prompt_selector(parent, on_selected: Callable[[List[str]], None]) -> MultiPromptSelector:
    """
    创建多Prompt选择器

    Args:
        parent: 父窗口
        on_selected: 选择回调函数

    Returns:
        选择器对象
    """
    return MultiPromptSelector(parent, on_selected)
