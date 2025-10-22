"""
白名单管理面板

提供符号白名单和字符串白名单的管理功能,包括:
- 添加、编辑、删除白名单项
- 导入/导出白名单文件
- 白名单列表显示和搜索

Classes:
    WhitelistManager: 白名单管理对话框主类
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os


class WhitelistManager:
    """白名单管理器 - 统一管理符号白名单和字符串白名单"""

    def __init__(self, parent, tab_main):
        """
        初始化白名单管理器

        Args:
            parent: 父窗口
            tab_main: ObfuscationTab主控制器实例
        """
        self.parent = parent
        self.tab_main = tab_main
        self.custom_whitelist_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'custom_whitelist.json'
        )

    def manage_symbol_whitelist(self):
        """管理符号白名单 (类名、方法名、属性名等)"""
        # 创建白名单管理窗口
        whitelist_window = tk.Toplevel(self.parent)
        whitelist_window.title("🛡️ 自定义白名单管理")
        whitelist_window.geometry("700x550")

        # 说明文本
        desc_frame = ttk.Frame(whitelist_window)
        desc_frame.pack(fill=tk.X, padx=10, pady=10)

        desc_text = ("自定义白名单用于保护不希望被混淆的符号（类名、方法名、属性名等）。\n"
                    "系统API和第三方库已自动保护，无需手动添加。")
        ttk.Label(
            desc_frame,
            text=desc_text,
            font=("Arial", 9),
            foreground="gray",
            justify=tk.LEFT
        ).pack(anchor=tk.W)

        # 工具栏
        toolbar = ttk.Frame(whitelist_window)
        toolbar.pack(fill=tk.X, padx=10, pady=5)

        # 创建树形控件(后续定义)
        tree_frame = ttk.Frame(whitelist_window)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 滚动条
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 树形列表
        tree = ttk.Treeview(
            tree_frame,
            columns=("type", "pattern", "description"),
            show="headings",
            yscrollcommand=scrollbar.set
        )
        tree.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=tree.yview)

        # 列标题
        tree.heading("type", text="类型")
        tree.heading("pattern", text="模式")
        tree.heading("description", text="描述")

        # 列宽
        tree.column("type", width=100)
        tree.column("pattern", width=200)
        tree.column("description", width=350)

        # 工具栏按钮
        ttk.Button(
            toolbar,
            text="➕ 添加",
            command=lambda: self._add_symbol_whitelist_item(tree),
            width=10
        ).pack(side=tk.LEFT, padx=3)

        ttk.Button(
            toolbar,
            text="✏️ 编辑",
            command=lambda: self._edit_symbol_whitelist_item(tree),
            width=10
        ).pack(side=tk.LEFT, padx=3)

        ttk.Button(
            toolbar,
            text="🗑️ 删除",
            command=lambda: self._delete_symbol_whitelist_item(tree),
            width=10
        ).pack(side=tk.LEFT, padx=3)

        ttk.Button(
            toolbar,
            text="📂 导入",
            command=lambda: self._import_symbol_whitelist(tree),
            width=10
        ).pack(side=tk.LEFT, padx=3)

        ttk.Button(
            toolbar,
            text="💾 导出",
            command=lambda: self._export_symbol_whitelist(tree),
            width=10
        ).pack(side=tk.LEFT, padx=3)

        # 底部按钮
        bottom_frame = ttk.Frame(whitelist_window)
        bottom_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(
            bottom_frame,
            text="保存",
            command=lambda: self._save_symbol_whitelist(tree, whitelist_window),
            width=10
        ).pack(side=tk.RIGHT, padx=3)

        ttk.Button(
            bottom_frame,
            text="取消",
            command=whitelist_window.destroy,
            width=10
        ).pack(side=tk.RIGHT, padx=3)

        # 加载现有白名单
        self._load_symbol_whitelist(tree)

    def manage_string_whitelist(self):
        """管理字符串白名单 (加密字符串白名单)"""
        # 创建字符串白名单管理窗口
        whitelist_window = tk.Toplevel(self.parent)
        whitelist_window.title("🔐 字符串白名单管理")
        whitelist_window.geometry("700x550")

        # 说明文本
        desc_frame = ttk.Frame(whitelist_window)
        desc_frame.pack(fill=tk.X, padx=10, pady=10)

        desc_text = ("字符串白名单用于保护不希望被加密的字符串。\n"
                    "例如: 系统API、第三方库的字符串常量等。")
        ttk.Label(
            desc_frame,
            text=desc_text,
            font=("Arial", 9),
            foreground="gray",
            justify=tk.LEFT
        ).pack(anchor=tk.W)

        # 工具栏
        toolbar = ttk.Frame(whitelist_window)
        toolbar.pack(fill=tk.X, padx=10, pady=5)

        # 创建树形控件
        tree_frame = ttk.Frame(whitelist_window)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 滚动条
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 树形列表
        tree = ttk.Treeview(
            tree_frame,
            columns=("pattern", "description"),
            show="headings",
            yscrollcommand=scrollbar.set
        )
        tree.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=tree.yview)

        # 列标题
        tree.heading("pattern", text="字符串模式")
        tree.heading("description", text="描述")

        # 列宽
        tree.column("pattern", width=250)
        tree.column("description", width=400)

        # 工具栏按钮
        ttk.Button(
            toolbar,
            text="➕ 添加",
            command=lambda: self._add_string_whitelist_item(tree),
            width=10
        ).pack(side=tk.LEFT, padx=3)

        ttk.Button(
            toolbar,
            text="✏️ 编辑",
            command=lambda: self._edit_string_whitelist_item(tree),
            width=10
        ).pack(side=tk.LEFT, padx=3)

        ttk.Button(
            toolbar,
            text="🗑️ 删除",
            command=lambda: self._delete_string_whitelist_item(tree),
            width=10
        ).pack(side=tk.LEFT, padx=3)

        ttk.Button(
            toolbar,
            text="📂 导入",
            command=lambda: self._import_string_whitelist(tree),
            width=10
        ).pack(side=tk.LEFT, padx=3)

        ttk.Button(
            toolbar,
            text="💾 导出",
            command=lambda: self._export_string_whitelist(tree),
            width=10
        ).pack(side=tk.LEFT, padx=3)

        # 底部按钮
        bottom_frame = ttk.Frame(whitelist_window)
        bottom_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(
            bottom_frame,
            text="保存",
            command=lambda: self._save_string_whitelist(tree, whitelist_window),
            width=10
        ).pack(side=tk.RIGHT, padx=3)

        ttk.Button(
            bottom_frame,
            text="取消",
            command=whitelist_window.destroy,
            width=10
        ).pack(side=tk.RIGHT, padx=3)

        # 加载现有字符串白名单
        self._load_string_whitelist(tree)

    # ========== 符号白名单管理方法 ==========

    def _load_symbol_whitelist(self, tree):
        """加载符号白名单到树形控件"""
        # 清空现有项
        for item in tree.get_children():
            tree.delete(item)

        # 加载自定义白名单文件
        if os.path.exists(self.custom_whitelist_path):
            try:
                with open(self.custom_whitelist_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    custom_items = data.get('custom_symbols', [])

                    for item in custom_items:
                        tree.insert('', 'end', values=(
                            item.get('type', ''),
                            item.get('pattern', ''),
                            item.get('description', '')
                        ))
            except Exception as e:
                messagebox.showerror("错误", f"加载白名单失败: {str(e)}")

    def _save_symbol_whitelist(self, tree, window):
        """保存符号白名单"""
        try:
            # 收集所有项
            items = []
            for child in tree.get_children():
                values = tree.item(child)['values']
                items.append({
                    'type': values[0],
                    'pattern': values[1],
                    'description': values[2]
                })

            # 读取现有文件(保留字符串白名单)
            existing_data = {}
            if os.path.exists(self.custom_whitelist_path):
                with open(self.custom_whitelist_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)

            # 更新符号白名单
            existing_data['custom_symbols'] = items

            # 写入文件
            with open(self.custom_whitelist_path, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)

            messagebox.showinfo("成功", "白名单已保存")
            window.destroy()

        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {str(e)}")

    def _add_symbol_whitelist_item(self, tree):
        """添加符号白名单项"""
        # 创建添加对话框
        dialog = tk.Toplevel(self.parent)
        dialog.title("添加白名单项")
        dialog.geometry("400x250")
        dialog.transient(self.parent)
        dialog.grab_set()

        # 类型选择
        ttk.Label(dialog, text="类型:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        type_var = tk.StringVar(value="class")
        type_combo = ttk.Combobox(
            dialog,
            textvariable=type_var,
            values=["class", "method", "property", "protocol", "all"],
            state="readonly",
            width=30
        )
        type_combo.grid(row=0, column=1, sticky=tk.EW, padx=10, pady=5)

        # 模式输入
        ttk.Label(dialog, text="模式:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        pattern_var = tk.StringVar()
        pattern_entry = ttk.Entry(dialog, textvariable=pattern_var, width=33)
        pattern_entry.grid(row=1, column=1, sticky=tk.EW, padx=10, pady=5)

        # 提示文本
        hint_text = "支持通配符: * (任意字符) ? (单个字符)\n例如: MyClass*, UI*Controller"
        ttk.Label(
            dialog,
            text=hint_text,
            font=("Arial", 8),
            foreground="gray"
        ).grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=10, pady=5)

        # 描述输入
        ttk.Label(dialog, text="描述:").grid(row=3, column=0, sticky=tk.W, padx=10, pady=5)
        desc_var = tk.StringVar()
        desc_entry = ttk.Entry(dialog, textvariable=desc_var, width=33)
        desc_entry.grid(row=3, column=1, sticky=tk.EW, padx=10, pady=5)

        # 按钮
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=4, column=0, columnspan=2, pady=15)

        def on_add():
            pattern = pattern_var.get().strip()
            if not pattern:
                messagebox.showwarning("警告", "请输入模式")
                return

            tree.insert('', 'end', values=(
                type_var.get(),
                pattern,
                desc_var.get()
            ))
            dialog.destroy()

        ttk.Button(button_frame, text="添加", command=on_add, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=dialog.destroy, width=10).pack(side=tk.LEFT, padx=5)

        # 聚焦到模式输入框
        pattern_entry.focus()

    def _edit_symbol_whitelist_item(self, tree):
        """编辑符号白名单项"""
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要编辑的项")
            return

        item = selection[0]
        values = tree.item(item)['values']

        # 创建编辑对话框
        dialog = tk.Toplevel(self.parent)
        dialog.title("编辑白名单项")
        dialog.geometry("400x250")
        dialog.transient(self.parent)
        dialog.grab_set()

        # 类型选择
        ttk.Label(dialog, text="类型:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        type_var = tk.StringVar(value=values[0])
        type_combo = ttk.Combobox(
            dialog,
            textvariable=type_var,
            values=["class", "method", "property", "protocol", "all"],
            state="readonly",
            width=30
        )
        type_combo.grid(row=0, column=1, sticky=tk.EW, padx=10, pady=5)

        # 模式输入
        ttk.Label(dialog, text="模式:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        pattern_var = tk.StringVar(value=values[1])
        pattern_entry = ttk.Entry(dialog, textvariable=pattern_var, width=33)
        pattern_entry.grid(row=1, column=1, sticky=tk.EW, padx=10, pady=5)

        # 提示文本
        hint_text = "支持通配符: * (任意字符) ? (单个字符)\n例如: MyClass*, UI*Controller"
        ttk.Label(
            dialog,
            text=hint_text,
            font=("Arial", 8),
            foreground="gray"
        ).grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=10, pady=5)

        # 描述输入
        ttk.Label(dialog, text="描述:").grid(row=3, column=0, sticky=tk.W, padx=10, pady=5)
        desc_var = tk.StringVar(value=values[2])
        desc_entry = ttk.Entry(dialog, textvariable=desc_var, width=33)
        desc_entry.grid(row=3, column=1, sticky=tk.EW, padx=10, pady=5)

        # 按钮
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=4, column=0, columnspan=2, pady=15)

        def on_save():
            pattern = pattern_var.get().strip()
            if not pattern:
                messagebox.showwarning("警告", "请输入模式")
                return

            tree.item(item, values=(
                type_var.get(),
                pattern,
                desc_var.get()
            ))
            dialog.destroy()

        ttk.Button(button_frame, text="保存", command=on_save, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=dialog.destroy, width=10).pack(side=tk.LEFT, padx=5)

    def _delete_symbol_whitelist_item(self, tree):
        """删除符号白名单项"""
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要删除的项")
            return

        if messagebox.askyesno("确认", "确定要删除选中的项吗?"):
            for item in selection:
                tree.delete(item)

    def _import_symbol_whitelist(self, tree):
        """导入符号白名单"""
        filepath = filedialog.askopenfilename(
            title="导入白名单",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if not filepath:
            return

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                items = data.get('custom_symbols', [])

                # 清空现有项
                for child in tree.get_children():
                    tree.delete(child)

                # 导入新项
                for item in items:
                    tree.insert('', 'end', values=(
                        item.get('type', ''),
                        item.get('pattern', ''),
                        item.get('description', '')
                    ))

                messagebox.showinfo("成功", f"成功导入 {len(items)} 个白名单项")

        except Exception as e:
            messagebox.showerror("错误", f"导入失败: {str(e)}")

    def _export_symbol_whitelist(self, tree):
        """导出符号白名单"""
        filepath = filedialog.asksaveasfilename(
            title="导出白名单",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if not filepath:
            return

        try:
            # 收集所有项
            items = []
            for child in tree.get_children():
                values = tree.item(child)['values']
                items.append({
                    'type': values[0],
                    'pattern': values[1],
                    'description': values[2]
                })

            # 写入文件
            data = {'custom_symbols': items}
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            messagebox.showinfo("成功", f"成功导出 {len(items)} 个白名单项")

        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {str(e)}")

    # ========== 字符串白名单管理方法 ==========

    def _load_string_whitelist(self, tree):
        """加载字符串白名单到树形控件"""
        # 清空现有项
        for item in tree.get_children():
            tree.delete(item)

        # 加载自定义白名单文件
        if os.path.exists(self.custom_whitelist_path):
            try:
                with open(self.custom_whitelist_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    custom_items = data.get('string_whitelist', [])

                    for item in custom_items:
                        tree.insert('', 'end', values=(
                            item.get('pattern', ''),
                            item.get('description', '')
                        ))
            except Exception as e:
                messagebox.showerror("错误", f"加载字符串白名单失败: {str(e)}")

    def _save_string_whitelist(self, tree, window):
        """保存字符串白名单"""
        try:
            # 收集所有项
            items = []
            for child in tree.get_children():
                values = tree.item(child)['values']
                items.append({
                    'pattern': values[0],
                    'description': values[1]
                })

            # 读取现有文件(保留符号白名单)
            existing_data = {}
            if os.path.exists(self.custom_whitelist_path):
                with open(self.custom_whitelist_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)

            # 更新字符串白名单
            existing_data['string_whitelist'] = items

            # 写入文件
            with open(self.custom_whitelist_path, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)

            messagebox.showinfo("成功", "字符串白名单已保存")
            window.destroy()

        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {str(e)}")

    def _add_string_whitelist_item(self, tree):
        """添加字符串白名单项"""
        # 创建添加对话框
        dialog = tk.Toplevel(self.parent)
        dialog.title("添加字符串白名单")
        dialog.geometry("400x200")
        dialog.transient(self.parent)
        dialog.grab_set()

        # 模式输入
        ttk.Label(dialog, text="字符串模式:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        pattern_var = tk.StringVar()
        pattern_entry = ttk.Entry(dialog, textvariable=pattern_var, width=33)
        pattern_entry.grid(row=0, column=1, sticky=tk.EW, padx=10, pady=5)

        # 提示文本
        hint_text = "支持通配符: * (任意字符)\n例如: NSLog*, UI*"
        ttk.Label(
            dialog,
            text=hint_text,
            font=("Arial", 8),
            foreground="gray"
        ).grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=10, pady=5)

        # 描述输入
        ttk.Label(dialog, text="描述:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        desc_var = tk.StringVar()
        desc_entry = ttk.Entry(dialog, textvariable=desc_var, width=33)
        desc_entry.grid(row=2, column=1, sticky=tk.EW, padx=10, pady=5)

        # 按钮
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=3, column=0, columnspan=2, pady=15)

        def on_add():
            pattern = pattern_var.get().strip()
            if not pattern:
                messagebox.showwarning("警告", "请输入字符串模式")
                return

            tree.insert('', 'end', values=(
                pattern,
                desc_var.get()
            ))
            dialog.destroy()

        ttk.Button(button_frame, text="添加", command=on_add, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=dialog.destroy, width=10).pack(side=tk.LEFT, padx=5)

        # 聚焦到模式输入框
        pattern_entry.focus()

    def _edit_string_whitelist_item(self, tree):
        """编辑字符串白名单项"""
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要编辑的项")
            return

        item = selection[0]
        values = tree.item(item)['values']

        # 创建编辑对话框
        dialog = tk.Toplevel(self.parent)
        dialog.title("编辑字符串白名单")
        dialog.geometry("400x200")
        dialog.transient(self.parent)
        dialog.grab_set()

        # 模式输入
        ttk.Label(dialog, text="字符串模式:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        pattern_var = tk.StringVar(value=values[0])
        pattern_entry = ttk.Entry(dialog, textvariable=pattern_var, width=33)
        pattern_entry.grid(row=0, column=1, sticky=tk.EW, padx=10, pady=5)

        # 提示文本
        hint_text = "支持通配符: * (任意字符)\n例如: NSLog*, UI*"
        ttk.Label(
            dialog,
            text=hint_text,
            font=("Arial", 8),
            foreground="gray"
        ).grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=10, pady=5)

        # 描述输入
        ttk.Label(dialog, text="描述:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        desc_var = tk.StringVar(value=values[1])
        desc_entry = ttk.Entry(dialog, textvariable=desc_var, width=33)
        desc_entry.grid(row=2, column=1, sticky=tk.EW, padx=10, pady=5)

        # 按钮
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=3, column=0, columnspan=2, pady=15)

        def on_save():
            pattern = pattern_var.get().strip()
            if not pattern:
                messagebox.showwarning("警告", "请输入字符串模式")
                return

            tree.item(item, values=(
                pattern,
                desc_var.get()
            ))
            dialog.destroy()

        ttk.Button(button_frame, text="保存", command=on_save, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=dialog.destroy, width=10).pack(side=tk.LEFT, padx=5)

    def _delete_string_whitelist_item(self, tree):
        """删除字符串白名单项"""
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要删除的项")
            return

        if messagebox.askyesno("确认", "确定要删除选中的项吗?"):
            for item in selection:
                tree.delete(item)

    def _import_string_whitelist(self, tree):
        """导入字符串白名单"""
        filepath = filedialog.askopenfilename(
            title="导入字符串白名单",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if not filepath:
            return

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                items = data.get('string_whitelist', [])

                # 清空现有项
                for child in tree.get_children():
                    tree.delete(child)

                # 导入新项
                for item in items:
                    tree.insert('', 'end', values=(
                        item.get('pattern', ''),
                        item.get('description', '')
                    ))

                messagebox.showinfo("成功", f"成功导入 {len(items)} 个字符串白名单项")

        except Exception as e:
            messagebox.showerror("错误", f"导入失败: {str(e)}")

    def _export_string_whitelist(self, tree):
        """导出字符串白名单"""
        filepath = filedialog.asksaveasfilename(
            title="导出字符串白名单",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if not filepath:
            return

        try:
            # 收集所有项
            items = []
            for child in tree.get_children():
                values = tree.item(child)['values']
                items.append({
                    'pattern': values[0],
                    'description': values[1]
                })

            # 写入文件
            data = {'string_whitelist': items}
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            messagebox.showinfo("成功", f"成功导出 {len(items)} 个字符串白名单项")

        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {str(e)}")
