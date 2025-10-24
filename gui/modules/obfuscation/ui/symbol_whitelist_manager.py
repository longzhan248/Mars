"""
符号白名单管理器
负责管理混淆白名单中的符号（类名、方法名、属性名等）
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
from typing import Optional


class SymbolWhitelistManager:
    """符号白名单管理器 - 管理类名、方法名、属性名等不被混淆的符号"""

    def __init__(self, parent: tk.Widget, tab_main, custom_whitelist_path: str):
        """
        初始化符号白名单管理器

        Args:
            parent: 父窗口
            tab_main: ObfuscationTab主控制器实例
            custom_whitelist_path: 自定义白名单文件路径
        """
        self.parent = parent
        self.tab_main = tab_main
        self.custom_whitelist_path = custom_whitelist_path

    def manage_symbol_whitelist(self) -> None:
        """打开符号白名单管理窗口"""
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

        # 创建树形控件
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
            command=lambda: self._add_item(tree),
            width=10
        ).pack(side=tk.LEFT, padx=3)

        ttk.Button(
            toolbar,
            text="✏️ 编辑",
            command=lambda: self._edit_item(tree),
            width=10
        ).pack(side=tk.LEFT, padx=3)

        ttk.Button(
            toolbar,
            text="🗑️ 删除",
            command=lambda: self._delete_item(tree),
            width=10
        ).pack(side=tk.LEFT, padx=3)

        ttk.Button(
            toolbar,
            text="📥 导入",
            command=lambda: self._import_whitelist(tree),
            width=10
        ).pack(side=tk.LEFT, padx=3)

        ttk.Button(
            toolbar,
            text="📤 导出",
            command=lambda: self._export_whitelist(tree),
            width=10
        ).pack(side=tk.LEFT, padx=3)

        # 底部按钮栏
        button_frame = ttk.Frame(whitelist_window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(
            button_frame,
            text="💾 保存",
            command=lambda: self._save_whitelist(tree, whitelist_window),
            width=12
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            button_frame,
            text="❌ 取消",
            command=whitelist_window.destroy,
            width=12
        ).pack(side=tk.RIGHT)

        # 加载现有白名单
        self._load_whitelist(tree)

    def _load_whitelist(self, tree: ttk.Treeview) -> None:
        """加载符号白名单到树形列表"""
        # 清空现有项
        for item in tree.get_children():
            tree.delete(item)

        # 从文件加载
        if os.path.exists(self.custom_whitelist_path):
            try:
                with open(self.custom_whitelist_path, 'r', encoding='utf-8') as f:
                    whitelist_data = json.load(f)

                # 显示符号白名单
                symbols = whitelist_data.get('symbols', [])
                for symbol in symbols:
                    tree.insert('', 'end', values=(
                        symbol.get('type', ''),
                        symbol.get('pattern', ''),
                        symbol.get('description', '')
                    ))
            except Exception as e:
                messagebox.showerror("错误", f"加载白名单失败: {str(e)}")

    def _save_whitelist(self, tree: ttk.Treeview, window: tk.Toplevel) -> None:
        """保存符号白名单到文件"""
        try:
            # 读取现有白名单文件（保留字符串白名单）
            existing_data = {}
            if os.path.exists(self.custom_whitelist_path):
                with open(self.custom_whitelist_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)

            # 从树形列表读取符号白名单
            symbols = []
            for item in tree.get_children():
                values = tree.item(item)['values']
                symbols.append({
                    'type': values[0],
                    'pattern': values[1],
                    'description': values[2]
                })

            # 更新符号白名单，保留字符串白名单
            whitelist_data = {
                'symbols': symbols,
                'strings': existing_data.get('strings', [])
            }

            # 保存到文件
            with open(self.custom_whitelist_path, 'w', encoding='utf-8') as f:
                json.dump(whitelist_data, f, ensure_ascii=False, indent=2)

            messagebox.showinfo("成功", "符号白名单已保存")
            window.destroy()

            # 刷新主界面的白名单显示
            if hasattr(self.tab_main, '_refresh_whitelist_display'):
                self.tab_main._refresh_whitelist_display()

        except Exception as e:
            messagebox.showerror("错误", f"保存白名单失败: {str(e)}")

    def _add_item(self, tree: ttk.Treeview) -> None:
        """添加符号白名单项"""
        # 创建添加对话框
        dialog = tk.Toplevel(self.parent)
        dialog.title("添加符号白名单项")
        dialog.geometry("500x300")
        dialog.transient(self.parent)
        dialog.grab_set()

        # 类型选择
        ttk.Label(dialog, text="类型:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        type_var = tk.StringVar(value="class")
        type_combo = ttk.Combobox(
            dialog,
            textvariable=type_var,
            values=["class", "method", "property", "protocol"],
            state="readonly",
            width=30
        )
        type_combo.grid(row=0, column=1, padx=10, pady=10, sticky=tk.W)

        # 模式输入
        ttk.Label(dialog, text="模式:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        pattern_var = tk.StringVar()
        pattern_entry = ttk.Entry(dialog, textvariable=pattern_var, width=35)
        pattern_entry.grid(row=1, column=1, padx=10, pady=10)

        # 模式提示
        ttk.Label(
            dialog,
            text="支持通配符: * (任意字符) 和 ? (单个字符)\n例如: MyClass* 或 set*Method",
            font=("Arial", 9),
            foreground="gray"
        ).grid(row=2, column=0, columnspan=2, padx=10, pady=5)

        # 描述输入
        ttk.Label(dialog, text="描述:").grid(row=3, column=0, padx=10, pady=10, sticky=tk.NW)
        desc_text = tk.Text(dialog, width=35, height=5)
        desc_text.grid(row=3, column=1, padx=10, pady=10)

        def save_item():
            """保存新增项"""
            pattern = pattern_var.get().strip()
            if not pattern:
                messagebox.showwarning("警告", "请输入模式")
                return

            desc = desc_text.get("1.0", tk.END).strip()
            tree.insert('', 'end', values=(type_var.get(), pattern, desc))
            dialog.destroy()

        # 按钮
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)

        ttk.Button(button_frame, text="确定", command=save_item, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=dialog.destroy, width=12).pack(side=tk.LEFT, padx=5)

    def _edit_item(self, tree: ttk.Treeview) -> None:
        """编辑符号白名单项"""
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择要编辑的项")
            return

        item = selection[0]
        values = tree.item(item)['values']

        # 创建编辑对话框
        dialog = tk.Toplevel(self.parent)
        dialog.title("编辑符号白名单项")
        dialog.geometry("500x300")
        dialog.transient(self.parent)
        dialog.grab_set()

        # 类型选择
        ttk.Label(dialog, text="类型:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        type_var = tk.StringVar(value=values[0])
        type_combo = ttk.Combobox(
            dialog,
            textvariable=type_var,
            values=["class", "method", "property", "protocol"],
            state="readonly",
            width=30
        )
        type_combo.grid(row=0, column=1, padx=10, pady=10, sticky=tk.W)

        # 模式输入
        ttk.Label(dialog, text="模式:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        pattern_var = tk.StringVar(value=values[1])
        pattern_entry = ttk.Entry(dialog, textvariable=pattern_var, width=35)
        pattern_entry.grid(row=1, column=1, padx=10, pady=10)

        # 描述输入
        ttk.Label(dialog, text="描述:").grid(row=3, column=0, padx=10, pady=10, sticky=tk.NW)
        desc_text = tk.Text(dialog, width=35, height=5)
        desc_text.grid(row=3, column=1, padx=10, pady=10)
        desc_text.insert("1.0", values[2])

        def save_changes():
            """保存修改"""
            pattern = pattern_var.get().strip()
            if not pattern:
                messagebox.showwarning("警告", "请输入模式")
                return

            desc = desc_text.get("1.0", tk.END).strip()
            tree.item(item, values=(type_var.get(), pattern, desc))
            dialog.destroy()

        # 按钮
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)

        ttk.Button(button_frame, text="确定", command=save_changes, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=dialog.destroy, width=12).pack(side=tk.LEFT, padx=5)

    def _delete_item(self, tree: ttk.Treeview) -> None:
        """删除符号白名单项"""
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择要删除的项")
            return

        if messagebox.askyesno("确认", "确定要删除选中的项吗？"):
            tree.delete(selection)

    def _import_whitelist(self, tree: ttk.Treeview) -> None:
        """导入符号白名单"""
        filepath = filedialog.askopenfilename(
            title="导入符号白名单",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )

        if not filepath:
            return

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            symbols = data.get('symbols', [])
            for symbol in symbols:
                tree.insert('', 'end', values=(
                    symbol.get('type', ''),
                    symbol.get('pattern', ''),
                    symbol.get('description', '')
                ))

            messagebox.showinfo("成功", f"已导入 {len(symbols)} 个符号白名单项")

        except Exception as e:
            messagebox.showerror("错误", f"导入失败: {str(e)}")

    def _export_whitelist(self, tree: ttk.Treeview) -> None:
        """导出符号白名单"""
        filepath = filedialog.asksaveasfilename(
            title="导出符号白名单",
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )

        if not filepath:
            return

        try:
            symbols = []
            for item in tree.get_children():
                values = tree.item(item)['values']
                symbols.append({
                    'type': values[0],
                    'pattern': values[1],
                    'description': values[2]
                })

            whitelist_data = {'symbols': symbols}

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(whitelist_data, f, ensure_ascii=False, indent=2)

            messagebox.showinfo("成功", f"已导出 {len(symbols)} 个符号白名单项到:\n{filepath}")

        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {str(e)}")
