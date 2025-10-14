"""
iOS混淆工具 - 白名单UI辅助模块

提供白名单管理相关的UI辅助功能，
从obfuscation_tab.py中提取以减少主文件大小。
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import json
from datetime import datetime


class WhitelistUIHelper:
    """白名单UI辅助类"""

    @staticmethod
    def get_whitelist_file_path(base_dir):
        """
        获取白名单文件路径

        Args:
            base_dir: 基础目录（通常是__file__的目录）

        Returns:
            str: 白名单文件的完整路径
        """
        return os.path.join(
            base_dir,
            "obfuscation",
            "custom_whitelist.json"
        )

    @staticmethod
    def load_whitelist(tree, whitelist_file, log_func=None):
        """
        加载白名单到Treeview

        Args:
            tree: ttk.Treeview组件
            whitelist_file: 白名单文件路径
            log_func: 日志函数（可选）
        """
        # 清空现有项
        for item in tree.get_children():
            tree.delete(item)

        if os.path.exists(whitelist_file):
            try:
                with open(whitelist_file, 'r', encoding='utf-8') as f:
                    whitelist_data = json.load(f)

                # 加载白名单项
                for item in whitelist_data.get('items', []):
                    tree.insert('', tk.END, values=(
                        item.get('name', ''),
                        item.get('type', 'custom'),
                        item.get('reason', '')
                    ))

            except Exception as e:
                if log_func:
                    log_func(f"⚠️  加载白名单失败: {str(e)}")

    @staticmethod
    def save_whitelist(tree, whitelist_file, log_func=None):
        """
        保存Treeview中的白名单到文件

        Args:
            tree: ttk.Treeview组件
            whitelist_file: 白名单文件路径
            log_func: 日志函数（可选）

        Returns:
            bool: 是否保存成功
        """
        # 收集所有白名单项
        items = []
        for item_id in tree.get_children():
            values = tree.item(item_id, 'values')
            items.append({
                'name': values[0],
                'type': values[1],
                'reason': values[2]
            })

        whitelist_data = {
            'version': '1.0',
            'updated': datetime.now().isoformat(),
            'items': items
        }

        # 确保目录存在
        whitelist_dir = os.path.dirname(whitelist_file)
        os.makedirs(whitelist_dir, exist_ok=True)

        try:
            with open(whitelist_file, 'w', encoding='utf-8') as f:
                json.dump(whitelist_data, f, indent=2, ensure_ascii=False)

            if log_func:
                log_func(f"✅ 已保存 {len(items)} 个白名单项")
            return True

        except Exception as e:
            messagebox.showerror("错误", f"保存白名单失败:\n{str(e)}")
            return False

    @staticmethod
    def show_add_dialog(parent, tree, save_func, update_stats_func):
        """
        显示添加白名单项对话框

        Args:
            parent: 父窗口
            tree: ttk.Treeview组件
            save_func: 保存函数
            update_stats_func: 更新统计函数
        """
        dialog = tk.Toplevel(parent)
        dialog.title("添加白名单项")
        dialog.geometry("450x250")
        dialog.transient(parent)
        dialog.grab_set()

        # 名称
        name_frame = ttk.Frame(dialog)
        name_frame.pack(fill=tk.X, padx=20, pady=10)

        ttk.Label(name_frame, text="符号名称:", width=10).pack(side=tk.LEFT)
        name_var = tk.StringVar()
        name_entry = ttk.Entry(name_frame, textvariable=name_var)
        name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        name_entry.focus()

        # 类型
        type_frame = ttk.Frame(dialog)
        type_frame.pack(fill=tk.X, padx=20, pady=10)

        ttk.Label(type_frame, text="类型:", width=10).pack(side=tk.LEFT)
        type_var = tk.StringVar(value="class")
        type_combo = ttk.Combobox(
            type_frame,
            textvariable=type_var,
            values=["class", "method", "property", "protocol", "enum", "constant", "custom"],
            state="readonly"
        )
        type_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # 备注
        reason_frame = ttk.Frame(dialog)
        reason_frame.pack(fill=tk.X, padx=20, pady=10)

        ttk.Label(reason_frame, text="备注:", width=10).pack(side=tk.LEFT, anchor=tk.N)
        reason_var = tk.StringVar()
        reason_entry = ttk.Entry(reason_frame, textvariable=reason_var)
        reason_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # 按钮
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=20, pady=20)

        def on_confirm():
            name = name_var.get().strip()
            if not name:
                messagebox.showwarning("提示", "请输入符号名称", parent=dialog)
                return

            # 添加到列表
            tree.insert('', tk.END, values=(
                name,
                type_var.get(),
                reason_var.get()
            ))

            # 保存
            save_func()
            update_stats_func()

            dialog.destroy()

        ttk.Button(
            button_frame,
            text="确定",
            command=on_confirm,
            width=10
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            button_frame,
            text="取消",
            command=dialog.destroy,
            width=10
        ).pack(side=tk.RIGHT)

        # Enter键确认
        dialog.bind('<Return>', lambda e: on_confirm())

    @staticmethod
    def show_edit_dialog(parent, tree, save_func):
        """
        显示编辑白名单项对话框

        Args:
            parent: 父窗口
            tree: ttk.Treeview组件
            save_func: 保存函数
        """
        selection = tree.selection()
        if not selection:
            messagebox.showinfo("提示", "请先选择要编辑的项")
            return

        item_id = selection[0]
        values = tree.item(item_id, 'values')

        dialog = tk.Toplevel(parent)
        dialog.title("编辑白名单项")
        dialog.geometry("450x250")
        dialog.transient(parent)
        dialog.grab_set()

        # 名称
        name_frame = ttk.Frame(dialog)
        name_frame.pack(fill=tk.X, padx=20, pady=10)

        ttk.Label(name_frame, text="符号名称:", width=10).pack(side=tk.LEFT)
        name_var = tk.StringVar(value=values[0])
        name_entry = ttk.Entry(name_frame, textvariable=name_var)
        name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        name_entry.focus()

        # 类型
        type_frame = ttk.Frame(dialog)
        type_frame.pack(fill=tk.X, padx=20, pady=10)

        ttk.Label(type_frame, text="类型:", width=10).pack(side=tk.LEFT)
        type_var = tk.StringVar(value=values[1])
        type_combo = ttk.Combobox(
            type_frame,
            textvariable=type_var,
            values=["class", "method", "property", "protocol", "enum", "constant", "custom"],
            state="readonly"
        )
        type_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # 备注
        reason_frame = ttk.Frame(dialog)
        reason_frame.pack(fill=tk.X, padx=20, pady=10)

        ttk.Label(reason_frame, text="备注:", width=10).pack(side=tk.LEFT, anchor=tk.N)
        reason_var = tk.StringVar(value=values[2])
        reason_entry = ttk.Entry(reason_frame, textvariable=reason_var)
        reason_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # 按钮
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=20, pady=20)

        def on_confirm():
            name = name_var.get().strip()
            if not name:
                messagebox.showwarning("提示", "请输入符号名称", parent=dialog)
                return

            # 更新列表
            tree.item(item_id, values=(
                name,
                type_var.get(),
                reason_var.get()
            ))

            # 保存
            save_func()

            dialog.destroy()

        ttk.Button(
            button_frame,
            text="确定",
            command=on_confirm,
            width=10
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            button_frame,
            text="取消",
            command=dialog.destroy,
            width=10
        ).pack(side=tk.RIGHT)

        # Enter键确认
        dialog.bind('<Return>', lambda e: on_confirm())

    @staticmethod
    def delete_items(tree, save_func, update_stats_func):
        """
        删除选中的白名单项

        Args:
            tree: ttk.Treeview组件
            save_func: 保存函数
            update_stats_func: 更新统计函数
        """
        selection = tree.selection()
        if not selection:
            messagebox.showinfo("提示", "请先选择要删除的项")
            return

        if messagebox.askyesno("确认", "确定要删除选中的白名单项吗？"):
            for item_id in selection:
                tree.delete(item_id)

            # 保存
            save_func()
            update_stats_func()

    @staticmethod
    def import_from_file(tree, save_func, update_stats_func):
        """
        从文件导入白名单

        Args:
            tree: ttk.Treeview组件
            save_func: 保存函数
            update_stats_func: 更新统计函数
        """
        file_path = filedialog.askopenfilename(
            title="导入白名单",
            filetypes=[("JSON文件", "*.json"), ("文本文件", "*.txt"), ("所有文件", "*.*")]
        )

        if not file_path:
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.endswith('.json'):
                    data = json.load(f)
                    items = data.get('items', [])
                else:
                    # 文本文件，每行一个名称
                    items = []
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            items.append({
                                'name': line,
                                'type': 'custom',
                                'reason': '从文件导入'
                            })

            # 添加到列表
            for item in items:
                tree.insert('', tk.END, values=(
                    item.get('name', ''),
                    item.get('type', 'custom'),
                    item.get('reason', '')
                ))

            # 保存
            save_func()
            update_stats_func()

            messagebox.showinfo("成功", f"已导入 {len(items)} 个白名单项")

        except Exception as e:
            messagebox.showerror("错误", f"导入失败:\n{str(e)}")

    @staticmethod
    def export_to_file(tree):
        """
        导出白名单到文件

        Args:
            tree: ttk.Treeview组件
        """
        if not tree.get_children():
            messagebox.showinfo("提示", "白名单为空，无需导出")
            return

        file_path = filedialog.asksaveasfilename(
            title="导出白名单",
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("文本文件", "*.txt"), ("所有文件", "*.*")]
        )

        if not file_path:
            return

        try:
            items = []
            for item_id in tree.get_children():
                values = tree.item(item_id, 'values')
                items.append({
                    'name': values[0],
                    'type': values[1],
                    'reason': values[2]
                })

            with open(file_path, 'w', encoding='utf-8') as f:
                if file_path.endswith('.json'):
                    json.dump({
                        'version': '1.0',
                        'exported': datetime.now().isoformat(),
                        'items': items
                    }, f, indent=2, ensure_ascii=False)
                else:
                    # 文本文件，每行一个名称
                    for item in items:
                        f.write(item['name'] + '\n')

            messagebox.showinfo("成功", f"已导出 {len(items)} 个白名单项")

        except Exception as e:
            messagebox.showerror("错误", f"导出失败:\n{str(e)}")
