#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件操作模块
负责文件的导出、打开、删除等操作
"""

import os
import platform
import re
import subprocess
import threading
from tkinter import filedialog, messagebox


class FileOperations:
    """文件操作管理器"""

    def __init__(self, parent_tab):
        """初始化文件操作管理器

        Args:
            parent_tab: 父标签页对象
        """
        self.parent = parent_tab

    def _read_file_with_retry(self, remote_path):
        """读取文件，失败时自动重试

        Args:
            remote_path: 远程文件路径

        Returns:
            bytes: 文件内容

        Raises:
            Exception: 读取失败时抛出异常
        """
        try:
            return self.parent.afc_client.get_file_contents(remote_path)
        except Exception as e:
            # 判断是否需要重新连接
            error_type = type(e).__name__
            error_str = str(e).lower()

            # 需要重连的错误类型：
            # 1. AFC状态错误（magic/parsing）
            # 2. 连接中断错误（ConnectionAbortedError/ConnectionTerminatedError）
            # 3. Const错误（ConstError）
            should_reconnect = (
                "magic" in error_str or
                "parsing" in error_str or
                "connectionaborted" in error_type.lower() or
                "connectionterminated" in error_type.lower() or
                "consterror" in error_type.lower() or
                "connection" in error_str
            )

            if should_reconnect:
                # 连接已断开，重新加载应用（会刷新整个UI）
                from tkinter import messagebox

                info_msg = (
                    "连接已断开，正在自动重新加载...\n\n"
                    "文件树将被刷新（目录会折叠）"
                )
                self.parent.parent.after(0, lambda msg=info_msg:
                    messagebox.showinfo("提示", msg))

                # 重新加载整个沙盒（会重建连接并刷新UI）
                if hasattr(self.parent, 'file_browser'):
                    threading.Thread(target=self.parent.file_browser.load_sandbox_async, daemon=True).start()
                    self.parent.parent.after(0, lambda:
                        self.parent.update_status("已重新加载应用"))

                raise
            raise

    def export_selected(self):
        """导出选中的文件/目录"""
        item = self.parent.tree.selection()
        if not item:
            messagebox.showwarning("提示", "请先选择要导出的文件或目录")
            return

        item_id = item[0]
        tags = self.parent.tree.item(item_id, "tags")

        if "placeholder" in tags:
            messagebox.showwarning("提示", "请先展开目录")
            return

        path = self.parent.tree.set(item_id, "path")
        if not path:
            messagebox.showwarning("提示", "无效的路径")
            return

        # 清理文件名
        name = self._clean_filename(item_id)

        if "directory" in tags:
            save_path = filedialog.askdirectory(title="选择保存目录")
            if save_path:
                dest_path = os.path.join(save_path, name)
                threading.Thread(target=self._export_directory_async,
                                 args=(path, dest_path), daemon=True).start()
        else:
            save_path = filedialog.asksaveasfilename(
                title="保存文件",
                initialfile=name,
                defaultextension=os.path.splitext(name)[1]
            )
            if save_path:
                threading.Thread(target=self._export_file_async,
                                 args=(path, save_path), daemon=True).start()

    def _export_file_async(self, remote_path, local_path):
        """异步导出文件"""
        try:
            self.parent.parent.after(0, lambda path=remote_path:
                                     self.parent.update_status(f"正在导出: {path}"))

            # 使用带重试的方法读取文件
            data = self._read_file_with_retry(remote_path)

            with open(local_path, 'wb') as f:
                f.write(data)

            self.parent.parent.after(0, lambda path=local_path:
                                     self.parent.update_status(f"导出成功: {path}"))
            self.parent.parent.after(0, lambda path=local_path:
                                     messagebox.showinfo("成功", f"文件已导出到: {path}"))

        except Exception as e:
            error_msg = str(e)
            self.parent.parent.after(0, lambda msg=error_msg:
                                     messagebox.showerror("错误", f"导出失败: {msg}"))
            self.parent.parent.after(0, lambda msg=error_msg:
                                     self.parent.update_status(f"导出失败: {msg}"))

    def _export_directory_async(self, remote_path, local_path):
        """异步导出目录"""
        try:
            self.parent.parent.after(0, lambda path=remote_path:
                                     self.parent.update_status(f"正在导出目录: {path}"))

            os.makedirs(local_path, exist_ok=True)

            self._export_directory_recursive(remote_path, local_path)

            self.parent.parent.after(0, lambda path=local_path:
                                     self.parent.update_status(f"导出成功: {path}"))
            self.parent.parent.after(0, lambda path=local_path:
                                     messagebox.showinfo("成功", f"目录已导出到: {path}"))

        except Exception as e:
            error_msg = str(e)
            self.parent.parent.after(0, lambda msg=error_msg:
                                     messagebox.showerror("错误", f"导出失败: {msg}"))
            self.parent.parent.after(0, lambda msg=error_msg:
                                     self.parent.update_status(f"导出失败: {msg}"))

    def _export_directory_recursive(self, remote_path, local_path):
        """递归导出目录"""
        items = self.parent.afc_client.listdir(remote_path)

        for item in items:
            if item in [".", "..", ".com.apple.mobile_container_manager.metadata.plist"]:
                continue

            remote_item = f"{remote_path}/{item}"
            local_item = os.path.join(local_path, item)

            try:
                info = self.parent.afc_client.stat(remote_item)
                is_dir = info['st_ifmt'] == 'S_IFDIR'

                if is_dir:
                    os.makedirs(local_item, exist_ok=True)
                    self._export_directory_recursive(remote_item, local_item)
                else:
                    # 使用带重试的方法读取文件
                    data = self._read_file_with_retry(remote_item)
                    with open(local_item, 'wb') as f:
                        f.write(data)

            except Exception as e:
                print(f"导出失败: {remote_item}, {e}")
                continue

    def open_selected(self):
        """打开选中的文件"""
        item = self.parent.tree.selection()
        if not item:
            messagebox.showwarning("提示", "请先选择要打开的文件")
            return

        item_id = item[0]
        tags = self.parent.tree.item(item_id, "tags")

        if "placeholder" in tags:
            messagebox.showwarning("提示", "请先展开目录")
            return

        if "directory" in tags:
            messagebox.showinfo("提示", "无法直接打开目录,请导出后查看")
            return

        path = self.parent.tree.set(item_id, "path")
        if not path:
            messagebox.showwarning("提示", "无效的文件路径")
            return

        # 清理文件名
        name = self._clean_filename(item_id)

        import tempfile
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, name)

        threading.Thread(target=self._open_file_async,
                         args=(path, temp_path), daemon=True).start()

    def _open_file_async(self, remote_path, local_path):
        """异步打开文件"""
        try:
            self.parent.parent.after(0, lambda path=remote_path:
                                     self.parent.update_status(f"正在下载: {path}"))

            # 使用带重试的方法读取文件
            data = self._read_file_with_retry(remote_path)

            with open(local_path, 'wb') as f:
                f.write(data)

            file_ext = os.path.splitext(local_path)[1].lower()

            # 特殊文件类型处理
            if file_ext in ['.db', '.sqlite', '.sqlite3', '.realm']:
                self.parent.parent.after(0, lambda path=local_path: messagebox.showinfo("提示",
                    f"数据库文件已下载到:\n{path}\n\n"
                    "您可以使用专门的数据库工具（如SQLiteStudio、DB Browser等）打开此文件"))
                self.parent.parent.after(0, lambda: self.parent.update_status("数据库文件已下载"))
                return
            elif file_ext in ['.plist']:
                if platform.system() == 'Darwin':
                    os.system(f'open -a TextEdit "{local_path}"')
                else:
                    self._try_open_file(local_path)
            else:
                self._try_open_file(local_path)

            self.parent.parent.after(0, lambda: self.parent.update_status("文件已打开"))

            # 图片文件打开后可能导致iOS设备断开连接（系统预览程序会保持文件句柄）
            # 其他类型文件（视频、数据库等）通常不会有这个问题
            file_ext = os.path.splitext(local_path)[1].lower()
            if file_ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.heic', '.webp']:
                self._refresh_connection_after_open()

        except Exception as e:
            error_msg = str(e)
            self.parent.parent.after(0, lambda msg=error_msg:
                                     messagebox.showerror("错误", f"打开失败: {msg}"))
            self.parent.parent.after(0, lambda msg=error_msg:
                                     self.parent.update_status(f"打开失败: {msg}"))

    def _refresh_connection_after_open(self):
        """打开文件后重新加载应用（刷新整个UI）"""
        if hasattr(self.parent, 'file_browser'):
            threading.Thread(target=self.parent.file_browser.load_sandbox_async, daemon=True).start()
            self.parent.update_status("已自动重新加载")

    def _try_open_file(self, file_path):
        """尝试打开文件"""
        try:
            if platform.system() == 'Darwin':
                result = subprocess.run(['open', file_path], capture_output=True, text=True)
                if result.returncode != 0:
                    subprocess.run(['open', '-R', file_path])
                    self.parent.parent.after(0, lambda path=file_path: messagebox.showinfo("提示",
                        f"文件已下载到:\n{path}\n\n系统无法自动打开此文件类型"))
            elif platform.system() == 'Windows':
                os.startfile(file_path)
            else:
                subprocess.run(['xdg-open', file_path])
        except Exception as e:
            self.parent.parent.after(0, lambda path=file_path, err=str(e): messagebox.showinfo("提示",
                f"文件已下载到:\n{path}\n\n错误: {err}"))

    def delete_selected(self):
        """删除选中的文件/目录"""
        item = self.parent.tree.selection()
        if not item:
            messagebox.showwarning("提示", "请先选择要删除的文件或目录")
            return

        item_id = item[0]
        tags = self.parent.tree.item(item_id, "tags")

        if "placeholder" in tags:
            messagebox.showwarning("提示", "请先展开目录")
            return

        path = self.parent.tree.set(item_id, "path")
        if not path:
            messagebox.showwarning("提示", "无效的路径")
            return

        name = self.parent.tree.item(item_id, "text")

        result = messagebox.askyesno("确认删除", f"确定要删除 {name} 吗?\n\n此操作不可恢复!")
        if not result:
            return

        threading.Thread(target=self._delete_item_async,
                         args=(path, item_id), daemon=True).start()

    def _delete_item_async(self, remote_path, item_id):
        """异步删除文件/目录"""
        try:
            self.parent.parent.after(0, lambda path=remote_path:
                                     self.parent.update_status(f"正在删除: {path}"))

            self.parent.afc_client.rm(remote_path)

            self.parent.parent.after(0, lambda id=item_id: self.parent.tree.delete(id))
            self.parent.parent.after(0, lambda: self.parent.update_status("删除成功"))
            self.parent.parent.after(0, lambda: messagebox.showinfo("成功", "删除成功"))

        except Exception as e:
            error_msg = str(e)
            self.parent.parent.after(0, lambda msg=error_msg:
                                     messagebox.showerror("错误", f"删除失败: {msg}"))
            self.parent.parent.after(0, lambda msg=error_msg:
                                     self.parent.update_status(f"删除失败: {msg}"))

    def _clean_filename(self, item_id):
        """清理文件名，移除图标和搜索标记

        Args:
            item_id: 树形项ID

        Returns:
            str: 清理后的文件名
        """
        name = self.parent.tree.item(item_id, "text")
        # 移除图标
        name = name.replace("📁 ", "").replace("📄 ", "")
        # 移除搜索标记
        tags = self.parent.tree.item(item_id, "tags")
        if "search_result" in tags:
            name = re.sub(r'\s*\[.*?\]$', '', name)
        return name
