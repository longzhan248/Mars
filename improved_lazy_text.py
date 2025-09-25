#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
改进的懒加载文本组件 - 解决灰色蒙层问题
"""

import tkinter as tk
from tkinter import ttk


class ImprovedLazyText(tk.Frame):
    """改进的懒加载文本组件"""

    def __init__(self, parent, batch_size=100, max_initial=500, **kwargs):
        super().__init__(parent)

        self.batch_size = batch_size
        self.max_initial = max_initial
        self.current_index = 0
        self.data = []
        self.is_loading = False

        # 创建组件
        self.create_widgets(**kwargs)

    def create_widgets(self, **text_kwargs):
        """创建组件"""
        # 创建Frame容器
        container = tk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True)

        # 直接创建Text组件和滚动条，不使用Canvas
        v_scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL)

        # 创建Text组件 - 使用系统默认背景色
        default_kwargs = {
            'wrap': tk.WORD,  # 自动换行
            'highlightthickness': 0,
            'borderwidth': 0,
            'yscrollcommand': v_scrollbar.set
        }
        default_kwargs.update(text_kwargs)

        self.text = tk.Text(container, **default_kwargs)
        v_scrollbar.config(command=self.text.yview)

        # 布局 - 直接放置Text和滚动条
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 保存组件引用
        self.v_scrollbar = v_scrollbar

        # 绑定滚动检测
        v_scrollbar.bind('<ButtonRelease-1>', self.check_scroll_position)
        self.text.bind('<MouseWheel>', self.on_mousewheel)
        self.text.bind('<Button-4>', self.on_mousewheel)
        self.text.bind('<Button-5>', self.on_mousewheel)

    def on_mousewheel(self, event):
        """鼠标滚轮事件"""
        # 滚动Text widget
        if event.num == 4 or event.delta > 0:
            self.text.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:
            self.text.yview_scroll(1, "units")

        # 检查是否需要加载更多
        self.after(10, self.check_scroll_position)

    def check_scroll_position(self, event=None):
        """检查滚动位置并加载更多数据"""
        if self.is_loading:
            return

        # 获取滚动位置
        if self.v_scrollbar.get()[1] >= 0.95:
            self.load_more()

    def set_data(self, data_list, clear=True):
        """设置数据"""
        self.data = data_list
        self.current_index = 0

        if clear:
            self.text.config(state='normal')
            self.text.delete(1.0, tk.END)
            self.text.config(state='disabled')

        # 加载初始数据（更多）
        initial_load = min(self.max_initial, len(self.data))
        self.current_index = 0
        self.load_batch(initial_load)

        # 更新Canvas视图
        self.after(10, self._update_canvas_view)

    def load_batch(self, count):
        """加载指定数量的数据"""
        if self.current_index >= len(self.data):
            return

        self.is_loading = True

        # 暂时允许编辑
        self.text.config(state='normal')

        # 计算加载范围
        end_index = min(self.current_index + count, len(self.data))

        # 批量插入数据
        for i in range(self.current_index, end_index):
            item = self.data[i]

            if isinstance(item, dict):
                # {'text': ..., 'tag': ..., 'prefix': ...} 格式
                if 'prefix' in item:
                    self.text.insert(tk.END, item['prefix'], item.get('prefix_tag'))
                self.text.insert(tk.END, item['text'], item.get('tag'))
            elif isinstance(item, tuple):
                # (text, tag) 格式
                self.text.insert(tk.END, item[0], item[1])
            else:
                # 纯文本
                self.text.insert(tk.END, str(item))

        self.current_index = end_index

        # 显示加载状态
        remaining = len(self.data) - self.current_index
        if remaining > 0:
            self.text.insert(tk.END, f"\n... 还有 {remaining} 条数据 ...\n", "HINT")

        # 恢复只读
        self.text.config(state='disabled')

        self.is_loading = False

    def load_more(self):
        """加载更多数据"""
        if self.current_index >= len(self.data):
            return

        # 删除加载提示
        content = self.text.get("end-100c", tk.END)
        if "... 还有" in content:
            self.text.config(state='normal')
            # 查找并删除提示行
            lines = self.text.get(1.0, tk.END).split('\n')
            for i in range(len(lines) - 1, max(0, len(lines) - 10), -1):
                if "... 还有" in lines[i]:
                    self.text.delete(f"{i+1}.0", f"{i+2}.0")
                    break
            self.text.config(state='disabled')

        # 加载下一批
        self.load_batch(self.batch_size)

    def tag_config(self, tag_name, **kwargs):
        """配置标签样式"""
        self.text.tag_config(tag_name, **kwargs)

    def _update_canvas_view(self):
        """更新视图（不再需要Canvas特定操作）"""
        # 确保Text widget更新显示
        self.text.update_idletasks()

    def clear(self):
        """清空内容"""
        self.text.config(state='normal')
        self.text.delete(1.0, tk.END)
        self.text.config(state='disabled')
        self.data = []
        self.current_index = 0

    def get(self, start, end):
        """获取文本内容"""
        return self.text.get(start, end)

    def insert(self, index, text, tags=None):
        """插入文本"""
        self.text.config(state='normal')
        self.text.insert(index, text, tags)
        self.text.config(state='disabled')

    def delete(self, start, end):
        """删除文本"""
        self.text.config(state='normal')
        self.text.delete(start, end)
        self.text.config(state='disabled')

    def search(self, pattern, start, stop=None, **kwargs):
        """搜索文本"""
        return self.text.search(pattern, start, stop, **kwargs)

    def tag_add(self, tagname, start, end):
        """添加标签"""
        self.text.tag_add(tagname, start, end)

    def tag_config(self, tagname, **kwargs):
        """配置标签"""
        self.text.tag_config(tagname, **kwargs)

    def tag_remove(self, tagname, start, end):
        """移除标签"""
        self.text.tag_remove(tagname, start, end)

    def tag_delete(self, tagname):
        """删除标签"""
        self.text.tag_delete(tagname)

    def see(self, index):
        """滚动到指定位置"""
        self.text.see(index)

    def mark_set(self, markname, index):
        """设置标记"""
        self.text.mark_set(markname, index)

    def yview(self, *args):
        """纵向滚动"""
        return self.text.yview(*args)

    def xview(self, *args):
        """横向滚动"""
        return self.text.xview(*args)