"""
字符串白名单管理器
负责管理不被加密的字符串白名单
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
from typing import Optional


class StringWhitelistManager:
    """字符串白名单管理器 - 管理不被加密的字符串"""

    def __init__(self, parent: tk.Widget, tab_main, custom_whitelist_path: str):
        """
        初始化字符串白名单管理器

        Args:
            parent: 父窗口
            tab_main: ObfuscationTab主控制器实例
            custom_whitelist_path: 自定义白名单文件路径
        """
        self.parent = parent
        self.tab_main = tab_main
        self.custom_whitelist_path = custom_whitelist_path

    def manage_string_whitelist(self) -> None:
        """打开字符串白名单管理窗口"""
        # 创建白名单管理窗口
        whitelist_window = tk.Toplevel(self.parent)
        whitelist_window.title("🔤 字符串白名单管理")
        whitelist_window.geometry("700x550")

        # 说明文本
        desc_frame = ttk.Frame(whitelist_window)
        desc_frame.pack(fill=tk.X, padx=10, pady=10)

        desc_text = ("字符串白名单用于保护不希望被加密的字符串常量。\n"
                    "系统API路径、URL前缀、标准协议头等已自动保护。")
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
            columns=("pattern", "match_type", "description"),
            show="headings",
            yscrollcommand=scrollbar.set
        )
        tree.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=tree.yview)

        # 列标题
        tree.heading("pattern", text="字符串模式")
        tree.heading("match_type", text="匹配类型")
        tree.heading("description", text="描述")

        # 列宽
        tree.column("pattern", width=250)
        tree.column("match_type", width=120)
        tree.column("description", width=300)

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
        """加载字符串白名单到树形列表"""
        # 清空现有项
        for item in tree.get_children():
            tree.delete(item)

        # 从文件加载
        if os.path.exists(self.custom_whitelist_path):
            try:
                with open(self.custom_whitelist_path, 'r', encoding='utf-8') as f:
                    whitelist_data = json.load(f)

                # 显示字符串白名单
                strings = whitelist_data.get('strings', [])
                for string_item in strings:
                    tree.insert('', 'end', values=(
                        string_item.get('pattern', ''),
                        string_item.get('match_type', 'exact'),
                        string_item.get('description', '')
                    ))
            except Exception as e:
                messagebox.showerror("错误", f"加载白名单失败: {str(e)}")

    def _save_whitelist(self, tree: ttk.Treeview, window: tk.Toplevel) -> None:
        """保存字符串白名单到文件"""
        try:
            # 读取现有白名单文件（保留符号白名单）
            existing_data = {}
            if os.path.exists(self.custom_whitelist_path):
                with open(self.custom_whitelist_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)

            # 从树形列表读取字符串白名单
            strings = []
            for item in tree.get_children():
                values = tree.item(item)['values']
                strings.append({
                    'pattern': values[0],
                    'match_type': values[1],
                    'description': values[2]
                })

            # 更新字符串白名单，保留符号白名单
            whitelist_data = {
                'symbols': existing_data.get('symbols', []),
                'strings': strings
            }

            # 保存到文件
            with open(self.custom_whitelist_path, 'w', encoding='utf-8') as f:
                json.dump(whitelist_data, f, ensure_ascii=False, indent=2)

            messagebox.showinfo("成功", "字符串白名单已保存")
            window.destroy()

            # 刷新主界面的白名单显示
            if hasattr(self.tab_main, '_refresh_whitelist_display'):
                self.tab_main._refresh_whitelist_display()

        except Exception as e:
            messagebox.showerror("错误", f"保存白名单失败: {str(e)}")

    def _add_item(self, tree: ttk.Treeview) -> None:
        """添加字符串白名单项"""
        # 创建添加对话框
        dialog = tk.Toplevel(self.parent)
        dialog.title("添加字符串白名单项")
        dialog.geometry("500x300")
        dialog.transient(self.parent)
        dialog.grab_set()

        # 字符串模式输入
        ttk.Label(dialog, text="字符串模式:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        pattern_var = tk.StringVar()
        pattern_entry = ttk.Entry(dialog, textvariable=pattern_var, width=35)
        pattern_entry.grid(row=0, column=1, padx=10, pady=10)

        # 匹配类型选择
        ttk.Label(dialog, text="匹配类型:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        match_type_var = tk.StringVar(value="exact")
        match_combo = ttk.Combobox(
            dialog,
            textvariable=match_type_var,
            values=["exact", "prefix", "suffix", "contains", "regex"],
            state="readonly",
            width=30
        )
        match_combo.grid(row=1, column=1, padx=10, pady=10, sticky=tk.W)

        # 匹配类型说明
        ttk.Label(
            dialog,
            text="exact: 完全匹配 | prefix: 前缀匹配 | suffix: 后缀匹配\n"
                 "contains: 包含匹配 | regex: 正则表达式",
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
                messagebox.showwarning("警告", "请输入字符串模式")
                return

            desc = desc_text.get("1.0", tk.END).strip()
            tree.insert('', 'end', values=(pattern, match_type_var.get(), desc))
            dialog.destroy()

        # 按钮
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)

        ttk.Button(button_frame, text="确定", command=save_item, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=dialog.destroy, width=12).pack(side=tk.LEFT, padx=5)

    def _edit_item(self, tree: ttk.Treeview) -> None:
        """编辑字符串白名单项"""
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择要编辑的项")
            return

        item = selection[0]
        values = tree.item(item)['values']

        # 创建编辑对话框
        dialog = tk.Toplevel(self.parent)
        dialog.title("编辑字符串白名单项")
        dialog.geometry("500x300")
        dialog.transient(self.parent)
        dialog.grab_set()

        # 字符串模式输入
        ttk.Label(dialog, text="字符串模式:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        pattern_var = tk.StringVar(value=values[0])
        pattern_entry = ttk.Entry(dialog, textvariable=pattern_var, width=35)
        pattern_entry.grid(row=0, column=1, padx=10, pady=10)

        # 匹配类型选择
        ttk.Label(dialog, text="匹配类型:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        match_type_var = tk.StringVar(value=values[1])
        match_combo = ttk.Combobox(
            dialog,
            textvariable=match_type_var,
            values=["exact", "prefix", "suffix", "contains", "regex"],
            state="readonly",
            width=30
        )
        match_combo.grid(row=1, column=1, padx=10, pady=10, sticky=tk.W)

        # 描述输入
        ttk.Label(dialog, text="描述:").grid(row=3, column=0, padx=10, pady=10, sticky=tk.NW)
        desc_text = tk.Text(dialog, width=35, height=5)
        desc_text.grid(row=3, column=1, padx=10, pady=10)
        desc_text.insert("1.0", values[2])

        def save_changes():
            """保存修改"""
            pattern = pattern_var.get().strip()
            if not pattern:
                messagebox.showwarning("警告", "请输入字符串模式")
                return

            desc = desc_text.get("1.0", tk.END).strip()
            tree.item(item, values=(pattern, match_type_var.get(), desc))
            dialog.destroy()

        # 按钮
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)

        ttk.Button(button_frame, text="确定", command=save_changes, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=dialog.destroy, width=12).pack(side=tk.LEFT, padx=5)

    def _delete_item(self, tree: ttk.Treeview) -> None:
        """删除字符串白名单项"""
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择要删除的项")
            return

        if messagebox.askyesno("确认", "确定要删除选中的项吗？"):
            tree.delete(selection)

    def _import_whitelist(self, tree: ttk.Treeview) -> None:
        """导入字符串白名单"""
        filepath = filedialog.askopenfilename(
            title="导入字符串白名单",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )

        if not filepath:
            return

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            strings = data.get('strings', [])
            for string_item in strings:
                tree.insert('', 'end', values=(
                    string_item.get('pattern', ''),
                    string_item.get('match_type', 'exact'),
                    string_item.get('description', '')
                ))

            messagebox.showinfo("成功", f"已导入 {len(strings)} 个字符串白名单项")

        except Exception as e:
            messagebox.showerror("错误", f"导入失败: {str(e)}")

    def _export_whitelist(self, tree: ttk.Treeview) -> None:
        """导出字符串白名单"""
        filepath = filedialog.asksaveasfilename(
            title="导出字符串白名单",
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )

        if not filepath:
            return

        try:
            strings = []
            for item in tree.get_children():
                values = tree.item(item)['values']
                strings.append({
                    'pattern': values[0],
                    'match_type': values[1],
                    'description': values[2]
                })

            whitelist_data = {'strings': strings}

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(whitelist_data, f, ensure_ascii=False, indent=2)

            messagebox.showinfo("成功", f"已导出 {len(strings)} 个字符串白名单项到:\n{filepath}")

        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {str(e)}")
