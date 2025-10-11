#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件浏览器模块
负责iOS应用沙盒文件系统的树形浏览
"""

import threading


class FileBrowser:
    """文件浏览器"""

    def __init__(self, parent_tab):
        """初始化文件浏览器

        Args:
            parent_tab: 父标签页对象
        """
        self.parent = parent_tab

    def load_sandbox_async(self):
        """异步加载沙盒文件"""
        try:
            from pymobiledevice3.lockdown import create_using_usbmux
            from pymobiledevice3.services.house_arrest import HouseArrestService

            device_id = self.parent.device_id
            app_id = self.parent.current_app_id

            if not device_id or not app_id:
                return

            lockdown = create_using_usbmux(serial=device_id)
            house_arrest = HouseArrestService(lockdown=lockdown, bundle_id=app_id)

            self.parent.afc_client = house_arrest

            self.parent.parent.after(0, lambda: self.parent.tree.delete(*self.parent.tree.get_children()))

            self._list_directory(".", "")

            self.parent.parent.after(0, lambda app_id=app_id:
                                     self.parent.update_status(f"已加载应用沙盒: {app_id}"))

        except Exception as e:
            error_msg = str(e)
            self.parent.parent.after(0, lambda msg=error_msg:
                                     self.parent.update_status(f"错误: {msg}"))
            # 清空文件树
            self.parent.parent.after(0, lambda: self.parent.tree.delete(*self.parent.tree.get_children()))

    def _list_directory(self, path, parent_item):
        """列出目录内容

        Args:
            path: 目录路径
            parent_item: 父节点ID
        """
        try:
            items = self.parent.afc_client.listdir(path)

            items_data = []
            for item in items:
                if item in [".", "..", ".com.apple.mobile_container_manager.metadata.plist"]:
                    continue

                item_path = f"{path}/{item}" if path != "." else item

                try:
                    info = self.parent.afc_client.stat(item_path)
                    is_dir = info['st_ifmt'] == 'S_IFDIR'
                    size = info.get('st_size', 0)
                    mtime = info.get('st_mtime')

                    if mtime and hasattr(mtime, 'strftime'):
                        date_str = mtime.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        date_str = ""

                    size_str = self._format_size(size) if not is_dir else ""

                    items_data.append({
                        'name': item,
                        'path': item_path,
                        'is_dir': is_dir,
                        'size': size_str,
                        'date': date_str
                    })

                except Exception:
                    continue

            self.parent.parent.after(0, self._insert_tree_items, parent_item, items_data)

        except Exception:
            pass

    def _insert_tree_items(self, parent, items_data):
        """批量插入树形项

        Args:
            parent: 父节点ID
            items_data: 项目数据列表
        """
        for item_data in items_data:
            self._insert_tree_item(
                parent,
                item_data['name'],
                item_data['path'],
                item_data['is_dir'],
                item_data['size'],
                item_data['date']
            )

    def _insert_tree_item(self, parent, name, path, is_dir, size, date):
        """插入树形项

        Args:
            parent: 父节点ID
            name: 文件/目录名
            path: 完整路径
            is_dir: 是否为目录
            size: 文件大小字符串
            date: 修改日期字符串
        """
        icon = "📁" if is_dir else "📄"
        display_name = f"{icon} {name}"

        item_id = self.parent.tree.insert(parent, "end", text=display_name,
                                          values=(size, date, path),
                                          tags=("directory" if is_dir else "file",))

        if is_dir:
            # 为目录添加占位符，支持懒加载
            self.parent.tree.insert(item_id, "end", text="", values=("", "", ""), tags=("placeholder",))

    def on_tree_expand(self, event):
        """树形节点展开事件

        Args:
            event: tkinter事件对象
        """
        item_id = self.parent.tree.focus()
        if not item_id:
            return

        tags = self.parent.tree.item(item_id, "tags")

        if "directory" in tags:
            children = self.parent.tree.get_children(item_id)
            if children:
                first_child = children[0]
                first_tags = self.parent.tree.item(first_child, "tags")
                if "placeholder" in first_tags:
                    # 删除占位符，加载实际内容
                    self.parent.tree.delete(first_child)
                    path = self.parent.tree.set(item_id, "path")
                    threading.Thread(target=self._list_directory, args=(path, item_id), daemon=True).start()

    def on_item_double_click(self, event):
        """双击事件处理

        Args:
            event: tkinter事件对象
        """
        item = self.parent.tree.selection()
        if not item:
            return

        item_id = item[0]
        tags = self.parent.tree.item(item_id, "tags")

        if "placeholder" in tags:
            return

        if "file" in tags:
            # 双击文件时触发预览
            if hasattr(self.parent, 'file_preview'):
                self.parent.file_preview.preview_selected()

    def refresh_current_dir(self):
        """刷新当前目录"""
        if not self.parent.current_app_id:
            from tkinter import messagebox
            messagebox.showwarning("提示", "请先选择应用")
            return

        # 重新加载整个沙盒
        threading.Thread(target=self.load_sandbox_async, daemon=True).start()

    @staticmethod
    def _format_size(size):
        """格式化文件大小

        Args:
            size: 文件大小（字节）

        Returns:
            str: 格式化后的大小字符串
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
