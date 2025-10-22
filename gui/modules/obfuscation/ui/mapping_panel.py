"""
映射查看面板UI组件

提供混淆映射的查看和导出功能
"""

import json
import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

try:
    from ...exceptions import FileOperationError, UIError, ErrorSeverity
except ImportError:
    try:
        from modules.exceptions import FileOperationError, UIError, ErrorSeverity
    except ImportError:
        from gui.modules.exceptions import FileOperationError, UIError, ErrorSeverity


class MappingViewer:
    """映射查看器（独立窗口）"""

    def __init__(self, parent, mapping_file):
        """
        初始化映射查看器

        Args:
            parent: 父窗口
            mapping_file: 映射文件路径
        """
        self.parent = parent
        self.mapping_file = mapping_file
        self.window = None

    def show(self):
        """显示映射查看窗口"""
        if not os.path.exists(self.mapping_file):
            raise FileOperationError(
                message="映射文件不存在",
                file_path=self.mapping_file,
                operation="查看混淆映射",
                user_message="映射文件不存在，请先执行混淆操作",
                severity=ErrorSeverity.MEDIUM
            )

        try:
            # 检查文件大小
            file_size = os.path.getsize(self.mapping_file)
            if file_size == 0:
                raise FileOperationError(
                    message="映射文件为空",
                    file_path=self.mapping_file,
                    operation="查看混淆映射",
                    user_message="映射文件为空，请重新执行混淆操作",
                    severity=ErrorSeverity.MEDIUM
                )
            elif file_size > 10 * 1024 * 1024:  # 10MB限制
                raise FileOperationError(
                    message=f"映射文件过大 ({file_size/1024/1024:.1f}MB)",
                    file_path=self.mapping_file,
                    operation="查看混淆映射",
                    user_message="映射文件过大，无法在界面中显示",
                    severity=ErrorSeverity.LOW
                )

            # 加载映射数据
            with open(self.mapping_file, 'r', encoding='utf-8') as f:
                mappings = json.load(f)

            # 验证映射数据结构
            if not isinstance(mappings, dict):
                raise FileOperationError(
                    message="映射文件格式无效，不是JSON对象",
                    file_path=self.mapping_file,
                    operation="查看混淆映射",
                    user_message="映射文件格式已损坏",
                    severity=ErrorSeverity.HIGH
                )

            # 创建查看窗口
            self.create_window(mappings)

        except json.JSONDecodeError as e:
            raise FileOperationError(
                message=f"映射文件JSON解析失败: {str(e)}",
                file_path=self.mapping_file,
                operation="查看混淆映射",
                user_message="映射文件格式已损坏，无法解析",
                cause=e,
                severity=ErrorSeverity.HIGH
            )
        except UnicodeDecodeError as e:
            raise FileOperationError(
                message=f"映射文件编码错误: {str(e)}",
                file_path=self.mapping_file,
                operation="查看混淆映射",
                user_message="映射文件编码格式不支持",
                cause=e,
                severity=ErrorSeverity.MEDIUM
            )
        except PermissionError as e:
            raise FileOperationError(
                message="没有权限读取映射文件",
                file_path=self.mapping_file,
                operation="查看混淆映射",
                user_message="没有权限读取映射文件，请检查文件权限",
                cause=e,
                severity=ErrorSeverity.HIGH
            )

    def create_window(self, mappings):
        """创建查看窗口"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("混淆映射")
        self.window.geometry("800x600")

        # 统计信息
        if 'metadata' in mappings:
            self.create_info_section(mappings['metadata'])

        # 映射列表
        self.create_mapping_tree(mappings)

        # 按钮
        button_frame = ttk.Frame(self.window)
        button_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(
            button_frame,
            text="关闭",
            command=self.window.destroy
        ).pack(side=tk.RIGHT)

    def create_info_section(self, metadata):
        """创建统计信息区域"""
        info_frame = ttk.Frame(self.window)
        info_frame.pack(fill=tk.X, padx=10, pady=5)

        info_text = (
            f"策略: {metadata.get('strategy', 'N/A')}  |  "
            f"前缀: {metadata.get('prefix', 'N/A')}  |  "
            f"总映射: {metadata.get('total_mappings', 0)}"
        )
        ttk.Label(info_frame, text=info_text).pack()

    def create_mapping_tree(self, mappings):
        """创建映射列表"""
        tree_frame = ttk.Frame(self.window)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 创建Treeview
        columns = ("原始名称", "混淆名称", "类型", "文件")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings")

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=200)

        # 添加滚动条
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 填充数据
        mappings_count = 0
        if 'mappings' in mappings:
            mappings_list = mappings['mappings']
            if isinstance(mappings_list, list):
                # 限制显示数量，避免界面卡顿
                max_display = 10000
                for i, mapping in enumerate(mappings_list):
                    if i >= max_display:
                        print(f"⚠️  映射数量过多，仅显示前 {max_display} 条")
                        break

                    tree.insert('', tk.END, values=(
                        mapping.get('original', ''),
                        mapping.get('obfuscated', ''),
                        mapping.get('type', ''),
                        os.path.basename(mapping.get('source_file', ''))
                    ))
                    mappings_count += 1

        # 添加计数标签
        count_label = ttk.Label(tree_frame, text=f"显示: {mappings_count} 条映射")
        count_label.pack(anchor=tk.W, padx=5, pady=2)


class MappingExporter:
    """映射导出器"""

    def __init__(self, parent, mapping_file):
        """
        初始化映射导出器

        Args:
            parent: 父窗口
            mapping_file: 源映射文件路径
        """
        self.parent = parent
        self.mapping_file = mapping_file

    def export(self):
        """导出映射文件"""
        if not os.path.exists(self.mapping_file):
            raise FileOperationError(
                message="映射文件不存在",
                file_path=self.mapping_file,
                operation="导出混淆映射",
                user_message="映射文件不存在，请先执行混淆操作",
                severity=ErrorSeverity.MEDIUM
            )

        # 选择保存位置
        save_path = filedialog.asksaveasfilename(
            title="导出映射文件",
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )

        if not save_path:
            return  # 用户取消了保存

        try:
            # 检查目标路径是否有效
            output_dir = os.path.dirname(save_path)
            if output_dir and not os.path.exists(output_dir):
                raise FileOperationError(
                    message="输出目录不存在",
                    file_path=save_path,
                    operation="导出混淆映射",
                    user_message="选择的保存路径不存在，请选择有效的目录",
                    severity=ErrorSeverity.HIGH
                )

            # 检查是否有写入权限
            if output_dir and not os.access(output_dir, os.W_OK):
                raise FileOperationError(
                    message="没有写入权限",
                    file_path=save_path,
                    operation="导出混淆映射",
                    user_message="没有权限在该目录写入文件，请选择其他目录",
                    severity=ErrorSeverity.HIGH
                )

            # 检查源文件是否可读
            if not os.access(self.mapping_file, os.R_OK):
                raise FileOperationError(
                    message="无法读取源映射文件",
                    file_path=self.mapping_file,
                    operation="导出混淆映射",
                    user_message="没有权限读取映射文件，请检查文件权限",
                    severity=ErrorSeverity.HIGH
                )

            # 如果目标文件已存在，确认覆盖
            if os.path.exists(save_path):
                if not messagebox.askyesno(
                    "确认覆盖",
                    f"文件已存在：\n{save_path}\n\n是否覆盖？"
                ):
                    return

            # 复制文件
            shutil.copy2(self.mapping_file, save_path)

            # 验证复制结果
            if not os.path.exists(save_path):
                raise FileOperationError(
                    message="文件复制失败",
                    file_path=save_path,
                    operation="导出混淆映射",
                    user_message="映射文件复制失败，请稍后重试",
                    severity=ErrorSeverity.HIGH
                )

            messagebox.showinfo("成功", f"映射文件已导出到:\n{save_path}")

        except PermissionError as e:
            raise FileOperationError(
                message="文件权限不足，无法写入",
                file_path=save_path,
                operation="导出混淆映射",
                user_message="没有权限写入该文件，请检查文件权限或选择其他路径",
                cause=e,
                severity=ErrorSeverity.HIGH
            )
        except shutil.SameFileError:
            raise FileOperationError(
                message="源文件和目标文件相同",
                file_path=save_path,
                operation="导出混淆映射",
                user_message="请选择不同的保存路径",
                severity=ErrorSeverity.LOW
            )
        except OSError as e:
            raise FileOperationError(
                message=f"文件操作失败: {str(e)}",
                file_path=save_path,
                operation="导出混淆映射",
                user_message="文件操作失败，请检查磁盘空间或文件权限",
                cause=e,
                severity=ErrorSeverity.MEDIUM
            )
