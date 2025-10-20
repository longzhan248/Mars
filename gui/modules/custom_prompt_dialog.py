"""
自定义Prompt配置对话框

提供图形界面来管理自定义AI提示词模板。

功能：
- 列表显示所有自定义模板
- 创建新模板
- 编辑现有模板
- 删除模板
- 启用/禁用模板
- 导入/导出模板
- 实时预览模板变量
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from typing import Optional
import uuid


class CustomPromptDialog:
    """自定义Prompt配置对话框"""

    def __init__(self, parent):
        """
        初始化对话框

        Args:
            parent: 父窗口
        """
        self.parent = parent
        self.dialog = None
        self.manager = None

        # 导入管理器
        try:
            # 尝试相对导入
            from .ai_diagnosis.custom_prompt_manager import get_custom_prompt_manager
            self.manager = get_custom_prompt_manager()
        except ImportError:
            try:
                from ai_diagnosis.custom_prompt_manager import get_custom_prompt_manager
                self.manager = get_custom_prompt_manager()
            except ImportError:
                try:
                    # 添加路径后导入
                    import sys
                    import os
                    gui_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    if gui_dir not in sys.path:
                        sys.path.insert(0, gui_dir)
                    from modules.ai_diagnosis.custom_prompt_manager import get_custom_prompt_manager
                    self.manager = get_custom_prompt_manager()
                except ImportError as e:
                    messagebox.showerror("错误", f"无法加载自定义Prompt管理器: {e}")
                    return

        # 创建对话框
        self._create_dialog()

    def _create_dialog(self):
        """创建对话框窗口"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("自定义Prompt模板管理")
        self.dialog.geometry("1200x750")

        # 设置模态对话框
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        # 创建主框架
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 创建左右分栏
        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # 左侧：模板列表
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)
        self._create_list_panel(left_frame)

        # 右侧：模板编辑
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=2)
        self._create_edit_panel(right_frame)

        # 底部按钮
        self._create_buttons(main_frame)

        # 加载模板列表
        self._refresh_list()

    def _create_list_panel(self, parent):
        """创建左侧模板列表面板"""
        # 标题和工具栏
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(header_frame, text="模板列表", font=("", 12, "bold")).pack(side=tk.LEFT)

        # 工具按钮
        btn_frame = ttk.Frame(header_frame)
        btn_frame.pack(side=tk.RIGHT)

        ttk.Button(btn_frame, text="➕ 新建", command=self._on_new, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="📋 复制", command=self._on_duplicate, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="🗑️ 删除", command=self._on_delete, width=8).pack(side=tk.LEFT, padx=2)

        # 分类过滤
        filter_frame = ttk.Frame(parent)
        filter_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(filter_frame, text="分类:").pack(side=tk.LEFT, padx=(0, 5))
        self.category_var = tk.StringVar(value="全部")
        self.category_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.category_var,
            values=["全部"] + self.manager.CATEGORIES,
            state="readonly",
            width=15
        )
        self.category_combo.pack(side=tk.LEFT)
        self.category_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh_list())

        # 搜索框
        ttk.Label(filter_frame, text="搜索:").pack(side=tk.LEFT, padx=(10, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace_add('write', lambda *args: self._refresh_list())
        ttk.Entry(filter_frame, textvariable=self.search_var, width=15).pack(side=tk.LEFT)

        # 树形列表
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        # 创建Treeview
        columns = ("名称", "分类", "状态")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='tree headings', height=20)

        # 设置列
        self.tree.column("#0", width=0, stretch=tk.NO)  # 隐藏第一列
        self.tree.column("名称", width=200)
        self.tree.column("分类", width=100)
        self.tree.column("状态", width=60)

        self.tree.heading("名称", text="名称")
        self.tree.heading("分类", text="分类")
        self.tree.heading("状态", text="状态")

        # 滚动条
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 绑定选择事件
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Double-1>", lambda e: self._on_edit())

        # 右键菜单
        self.tree_menu = tk.Menu(self.tree, tearoff=0)
        self.tree_menu.add_command(label="编辑", command=self._on_edit)
        self.tree_menu.add_command(label="复制", command=self._on_duplicate)
        self.tree_menu.add_separator()
        self.tree_menu.add_command(label="启用", command=self._on_enable)
        self.tree_menu.add_command(label="禁用", command=self._on_disable)
        self.tree_menu.add_separator()
        self.tree_menu.add_command(label="删除", command=self._on_delete)

        self.tree.bind("<Button-3>", self._show_tree_menu)

    def _create_edit_panel(self, parent):
        """创建右侧编辑面板"""
        # 标题
        ttk.Label(parent, text="模板详情", font=("", 12, "bold")).pack(anchor=tk.W, pady=(0, 10))

        # 基本信息框架
        info_frame = ttk.LabelFrame(parent, text="基本信息", padding=10)
        info_frame.pack(fill=tk.X, pady=(0, 10))

        # ID（只读）
        row = 0
        ttk.Label(info_frame, text="ID:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.id_var = tk.StringVar()
        id_entry = ttk.Entry(info_frame, textvariable=self.id_var, state="readonly")
        id_entry.grid(row=row, column=1, sticky=tk.EW, pady=2)

        # 名称
        row += 1
        ttk.Label(info_frame, text="名称:*").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.name_var = tk.StringVar()
        ttk.Entry(info_frame, textvariable=self.name_var).grid(row=row, column=1, sticky=tk.EW, pady=2)

        # 分类
        row += 1
        ttk.Label(info_frame, text="分类:*").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.edit_category_var = tk.StringVar()
        ttk.Combobox(
            info_frame,
            textvariable=self.edit_category_var,
            values=self.manager.CATEGORIES,
            state="readonly"
        ).grid(row=row, column=1, sticky=tk.EW, pady=2)

        # 描述
        row += 1
        ttk.Label(info_frame, text="描述:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.description_var = tk.StringVar()
        ttk.Entry(info_frame, textvariable=self.description_var).grid(row=row, column=1, sticky=tk.EW, pady=2)

        # 启用状态
        row += 1
        self.enabled_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(info_frame, text="启用此模板", variable=self.enabled_var).grid(
            row=row, column=0, columnspan=2, sticky=tk.W, pady=2
        )

        info_frame.columnconfigure(1, weight=1)

        # 模板内容框架
        template_frame = ttk.LabelFrame(parent, text="模板内容（支持变量：{variable_name}）", padding=10)
        template_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 文本编辑器
        self.template_text = scrolledtext.ScrolledText(
            template_frame,
            wrap=tk.WORD,
            height=15,
            font=("Courier New", 10)
        )
        self.template_text.pack(fill=tk.BOTH, expand=True)

        # 变量提示
        var_frame = ttk.Frame(template_frame)
        var_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Label(var_frame, text="检测到的变量:", font=("", 9)).pack(side=tk.LEFT)
        self.variables_label = ttk.Label(var_frame, text="", foreground="blue", font=("", 9))
        self.variables_label.pack(side=tk.LEFT, padx=(5, 0))

        # 监听模板内容变化
        self.template_text.bind("<KeyRelease>", self._on_template_change)

        # 操作按钮
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X)

        ttk.Button(btn_frame, text="💾 保存", command=self._on_save, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🔄 重置", command=self._on_reset, width=12).pack(side=tk.LEFT)

        # 初始状态：禁用编辑
        self._set_edit_state(False)

    def _create_buttons(self, parent):
        """创建底部按钮"""
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        # 左侧按钮
        left_btns = ttk.Frame(btn_frame)
        left_btns.pack(side=tk.LEFT)

        ttk.Button(left_btns, text="📥 导入", command=self._on_import, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(left_btns, text="📤 导出", command=self._on_export, width=10).pack(side=tk.LEFT, padx=2)

        # 右侧按钮
        right_btns = ttk.Frame(btn_frame)
        right_btns.pack(side=tk.RIGHT)

        ttk.Button(right_btns, text="关闭", command=self.dialog.destroy, width=10).pack(side=tk.LEFT, padx=2)

    def _refresh_list(self):
        """刷新模板列表"""
        # 清空列表
        for item in self.tree.get_children():
            self.tree.delete(item)

        # 获取过滤条件
        category = self.category_var.get()
        search_text = self.search_var.get().lower()

        # 获取模板列表
        if category == "全部":
            prompts = self.manager.list_all()
        else:
            prompts = self.manager.list_all(category=category)

        # 搜索过滤
        if search_text:
            prompts = [p for p in prompts if search_text in p.name.lower() or search_text in p.description.lower()]

        # 添加到树形列表
        for prompt in prompts:
            status = "✓ 启用" if prompt.enabled else "✗ 禁用"
            self.tree.insert(
                "",
                tk.END,
                iid=prompt.id,
                values=(prompt.name, prompt.category, status)
            )

    def _on_select(self, event):
        """选择模板时的处理"""
        selection = self.tree.selection()
        if not selection:
            self._set_edit_state(False)
            return

        # 获取选中的prompt
        prompt_id = selection[0]
        prompt = self.manager.get(prompt_id)

        if prompt:
            # 填充编辑表单
            self.id_var.set(prompt.id)
            self.name_var.set(prompt.name)
            self.edit_category_var.set(prompt.category)
            self.description_var.set(prompt.description)
            self.enabled_var.set(prompt.enabled)

            self.template_text.delete('1.0', tk.END)
            self.template_text.insert('1.0', prompt.template)

            self._update_variables_display()
            self._set_edit_state(True)

    def _on_new(self):
        """创建新模板"""
        # 清空表单
        new_id = f"custom_{uuid.uuid4().hex[:8]}"
        self.id_var.set(new_id)
        self.name_var.set("新建模板")
        self.edit_category_var.set("自定义分析")
        self.description_var.set("")
        self.enabled_var.set(True)
        self.template_text.delete('1.0', tk.END)
        self.template_text.insert('1.0', "# 在此输入提示词模板\n\n## 变量示例\n{variable_name}\n")

        self._update_variables_display()
        self._set_edit_state(True)

        # 取消选择
        self.tree.selection_remove(self.tree.selection())

    def _on_edit(self):
        """编辑当前选中的模板"""
        # 已经通过_on_select加载了数据，无需额外操作
        pass

    def _on_duplicate(self):
        """复制当前选中的模板"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择要复制的模板")
            return

        prompt_id = selection[0]
        prompt = self.manager.get(prompt_id)

        if prompt:
            # 生成新ID
            new_id = f"{prompt.id}_copy_{uuid.uuid4().hex[:4]}"

            # 创建副本
            from gui.modules.ai_diagnosis.custom_prompt_manager import CustomPrompt
            new_prompt = CustomPrompt(
                id=new_id,
                name=f"{prompt.name} (副本)",
                category=prompt.category,
                description=prompt.description,
                template=prompt.template,
                enabled=prompt.enabled
            )

            if self.manager.add(new_prompt):
                self._refresh_list()
                messagebox.showinfo("成功", "模板已复制")
            else:
                messagebox.showerror("错误", "复制失败")

    def _on_delete(self):
        """删除当前选中的模板"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择要删除的模板")
            return

        if not messagebox.askyesno("确认", "确定要删除选中的模板吗？此操作不可恢复。"):
            return

        prompt_id = selection[0]
        if self.manager.delete(prompt_id):
            self._refresh_list()
            self._set_edit_state(False)
            messagebox.showinfo("成功", "模板已删除")
        else:
            messagebox.showerror("错误", "删除失败")

    def _on_enable(self):
        """启用选中的模板"""
        selection = self.tree.selection()
        if not selection:
            return

        prompt_id = selection[0]
        self.manager.enable(prompt_id)
        self._refresh_list()

    def _on_disable(self):
        """禁用选中的模板"""
        selection = self.tree.selection()
        if not selection:
            return

        prompt_id = selection[0]
        self.manager.disable(prompt_id)
        self._refresh_list()

    def _on_save(self):
        """保存当前编辑的模板"""
        # 验证输入
        prompt_id = self.id_var.get()
        name = self.name_var.get().strip()
        category = self.edit_category_var.get()
        description = self.description_var.get().strip()
        template = self.template_text.get('1.0', tk.END).strip()
        enabled = self.enabled_var.get()

        if not prompt_id:
            messagebox.showerror("错误", "缺少模板ID")
            return

        if not name:
            messagebox.showerror("错误", "请输入模板名称")
            return

        if not category:
            messagebox.showerror("错误", "请选择分类")
            return

        if not template:
            messagebox.showwarning("提示", "请输入模板内容\n\n提示：模板可以包含变量，格式为 {variable_name}")
            # 聚焦到模板文本框
            self.template_text.focus_set()
            return

        # 判断是新建还是更新
        existing = self.manager.get(prompt_id)

        if existing:
            # 更新
            success = self.manager.update(
                prompt_id,
                name=name,
                category=category,
                description=description,
                template=template,
                enabled=enabled
            )
        else:
            # 新建
            from gui.modules.ai_diagnosis.custom_prompt_manager import CustomPrompt
            new_prompt = CustomPrompt(
                id=prompt_id,
                name=name,
                category=category,
                description=description,
                template=template,
                enabled=enabled
            )
            success = self.manager.add(new_prompt)

        if success:
            self._refresh_list()
            messagebox.showinfo("成功", "模板已保存")
        else:
            messagebox.showerror("错误", "保存失败")

    def _on_reset(self):
        """重置编辑表单"""
        selection = self.tree.selection()
        if selection:
            # 重新加载选中的模板
            self._on_select(None)
        else:
            # 清空表单
            self._set_edit_state(False)

    def _on_import(self):
        """从文件导入模板"""
        filepath = filedialog.askopenfilename(
            title="选择导入文件",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )

        if filepath:
            try:
                count = self.manager.import_from_file(filepath)
                self._refresh_list()
                messagebox.showinfo("成功", f"成功导入{count}个模板")
            except Exception as e:
                messagebox.showerror("错误", f"导入失败: {e}")

    def _on_export(self):
        """导出模板到文件"""
        filepath = filedialog.asksaveasfilename(
            title="导出模板",
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )

        if filepath:
            try:
                # 获取选中的模板ID
                selection = self.tree.selection()
                prompt_ids = list(selection) if selection else None

                self.manager.export_to_file(filepath, prompt_ids)
                messagebox.showinfo("成功", "导出成功")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败: {e}")

    def _on_template_change(self, event):
        """模板内容变化时更新变量显示"""
        self._update_variables_display()

    def _update_variables_display(self):
        """更新变量显示"""
        import re
        template = self.template_text.get('1.0', tk.END)
        variables = list(set(re.findall(r'\{(\w+)\}', template)))

        if variables:
            self.variables_label.config(text=", ".join(variables))
        else:
            self.variables_label.config(text="（无）")

    def _set_edit_state(self, enabled: bool):
        """设置编辑面板状态"""
        state = tk.NORMAL if enabled else tk.DISABLED

        # 禁用/启用输入控件
        for widget in [self.name_var, self.edit_category_var, self.description_var]:
            # 这些是StringVar，不需要设置state
            pass

        self.template_text.config(state=state)

        if not enabled:
            # 清空所有字段
            self.id_var.set("")
            self.name_var.set("")
            self.edit_category_var.set("")
            self.description_var.set("")
            self.enabled_var.set(True)
            self.template_text.delete('1.0', tk.END)
            self.variables_label.config(text="")

    def _show_tree_menu(self, event):
        """显示右键菜单"""
        # 选中右键点击的项
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.tree_menu.post(event.x_root, event.y_root)

    def show(self):
        """显示对话框（阻塞）"""
        if self.dialog:
            self.dialog.wait_window()


# 便捷函数
def show_custom_prompt_dialog(parent):
    """显示自定义Prompt配置对话框"""
    dialog = CustomPromptDialog(parent)
    dialog.show()


# 测试代码
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口

    show_custom_prompt_dialog(root)
