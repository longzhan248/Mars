#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜索管理模块
负责文件和内容的搜索功能
"""

import os
from tkinter import messagebox


class SearchManager:
    """搜索管理器"""

    def __init__(self, parent_tab):
        """初始化搜索管理器

        Args:
            parent_tab: 父标签页对象
        """
        self.parent = parent_tab
        self.search_results = []
        self.current_search_text = ""

    def search_files(self):
        """搜索文件"""
        if not self.parent.afc_client:
            messagebox.showwarning("提示", "请先选择应用")
            return

        search_text = self.parent.search_entry.get().strip()
        if not search_text:
            messagebox.showwarning("提示", "请输入搜索内容")
            return

        search_type = self.parent.search_type_var.get()
        self.search_results = []
        self.parent.search_status.config(text="正在搜索...")

        # 禁用搜索按钮
        self.parent.search_button.config(state='disabled')

        # 在新线程中执行搜索
        import threading
        threading.Thread(target=self._do_search,
                        args=(search_text, search_type),
                        daemon=True).start()

    def _do_search(self, search_text, search_type):
        """执行搜索"""
        try:
            results = []
            total_files = 0
            searched_files = 0

            # 递归搜索所有文件
            def search_directory(path):
                nonlocal total_files, searched_files
                try:
                    items = self.parent.afc_client.listdir(path)

                    for item in items:
                        if item in ['.', '..']:
                            continue

                        # 构建完整路径
                        if path == '.':
                            item_path = item
                        else:
                            item_path = f"{path}/{item}"

                        # 搜索文件名
                        if search_type in ["文件名", "所有"]:
                            if search_text.lower() in item.lower():
                                try:
                                    stat = self.parent.afc_client.stat(item_path)
                                    is_dir = stat.get('st_ifmt') == 'S_IFDIR'
                                    result = {
                                        'path': item_path,
                                        'name': item,
                                        'type': 'directory' if is_dir else 'file',
                                        'size': stat.get('st_size', 0) if not is_dir else 0,
                                        'match_type': '文件名'
                                    }
                                    results.append(result)
                                except Exception:
                                    pass

                        # 检查是否为目录，递归搜索
                        try:
                            stat = self.parent.afc_client.stat(item_path)
                            is_dir = stat.get('st_ifmt') == 'S_IFDIR'
                            if is_dir:
                                search_directory(item_path)
                            elif search_type in ["文件内容", "所有"]:
                                # 搜索文件内容（仅文本文件）
                                file_ext = os.path.splitext(item.lower())[1]
                                if file_ext in ['.txt', '.log', '.json', '.xml', '.plist', '.html',
                                              '.css', '.js', '.py', '.md', '.sh', '.h', '.m',
                                              '.swift', '.c', '.cpp', '.yml', '.yaml', '.ini',
                                              '.cfg', '.conf', '.properties']:
                                    try:
                                        # 读取文件前512KB
                                        with self.parent.afc_client.open(item_path, 'rb') as f:
                                            content = f.read(524288)  # 512KB
                                            text_content = content.decode('utf-8', errors='ignore')
                                            if search_text.lower() in text_content.lower():
                                                results.append({
                                                    'path': item_path,
                                                    'name': item,
                                                    'type': 'file',
                                                    'size': stat.get('st_size', 0),
                                                    'match_type': '文件内容'
                                                })
                                    except Exception:
                                        pass

                            searched_files += 1
                            total_files += 1

                            # 更新搜索状态
                            if searched_files % 20 == 0:
                                self.parent.parent.after(0, lambda count=searched_files:
                                                         self.parent.search_status.config(
                                    text=f"正在搜索... (已搜索 {count} 个文件)"))

                        except Exception:
                            pass

                except Exception:
                    pass

            # 从根目录开始搜索
            search_directory('.')

            # 在主线程中更新结果
            self.parent.parent.after(0, lambda: self._show_search_results(results, search_text))

        except Exception as e:
            self.parent.parent.after(0, lambda msg=str(e):
                                     messagebox.showerror("搜索错误", f"搜索失败: {msg}"))
        finally:
            # 重新启用搜索按钮
            self.parent.parent.after(0, lambda: self.parent.search_button.config(state='normal'))

    def _show_search_results(self, results, search_text):
        """显示搜索结果"""
        # 清空树形控件
        self.parent.tree.delete(*self.parent.tree.get_children())

        if not results:
            self.parent.search_status.config(text=f"未找到 '{search_text}' 相关的文件")
            return

        # 保存搜索结果和原始搜索词
        self.search_results = results
        self.current_search_text = search_text

        # 按路径排序
        results.sort(key=lambda x: x['path'])

        # 添加搜索结果到树形控件
        for result in results:
            icon = "📁" if result['type'] == 'directory' else "📄"
            size = "" if result['type'] == 'directory' else self._format_size(result['size'])

            # 高亮显示匹配类型
            match_info = f" [{result['match_type']}]"

            item = self.parent.tree.insert('', 'end',
                                           text=f"{icon} {result['name']}{match_info}",
                                           values=(size, "", result['path']))

            # 标记搜索结果项和类型
            tags = ['search_result']
            if result['type'] == 'directory':
                tags.append('directory')
            else:
                tags.append('file')
            self.parent.tree.item(item, tags=tuple(tags))

            # 如果是目录，添加占位符（允许展开）
            if result['type'] == 'directory':
                self.parent.tree.insert(item, 'end', text='', values=('', '', ''), tags=('placeholder',))

        # 配置搜索结果标签样式
        self.parent.tree.tag_configure('search_result', foreground='blue')

        self.parent.search_status.config(
            text=f"找到 {len(results)} 个匹配项 (搜索: '{search_text}')")

    def clear_search(self):
        """清除搜索结果"""
        self.parent.search_entry.delete(0, 'end')
        self.search_results = []
        self.current_search_text = ""
        self.parent.search_status.config(text="")

        # 刷新应用内容（恢复正常浏览）
        if self.parent.afc_client:
            # 清空树形控件
            self.parent.tree.delete(*self.parent.tree.get_children())
            # 重新加载根目录
            if hasattr(self.parent, 'file_browser'):
                self.parent.file_browser._list_directory('.', '')

    @staticmethod
    def _format_size(size):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
