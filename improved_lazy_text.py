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

        # 创建Canvas和滚动条
        canvas = tk.Canvas(container, highlightthickness=0)
        v_scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=canvas.yview)

        # 创建Text组件
        default_kwargs = {
            'wrap': tk.WORD,  # 自动换行
            'highlightthickness': 0,
            'borderwidth': 0
        }
        default_kwargs.update(text_kwargs)

        self.text = tk.Text(canvas, **default_kwargs)

        # 配置Canvas
        canvas.configure(yscrollcommand=v_scrollbar.set)
        canvas_frame = canvas.create_window(0, 0, anchor=tk.NW, window=self.text)

        # 布局
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 更新Canvas滚动区域
        def configure_scroll_region(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # 设置Canvas窗口宽度
            canvas_width = canvas.winfo_width()
            if canvas_width > 1:
                canvas.itemconfig(canvas_frame, width=canvas_width)

        self.text.bind('<Configure>', configure_scroll_region)
        canvas.bind('<Configure>', lambda e: canvas.itemconfig(canvas_frame, width=e.width))

        # 保存组件引用
        self.canvas = canvas
        self.v_scrollbar = v_scrollbar

        # 绑定滚动检测
        v_scrollbar.bind('<ButtonRelease-1>', self.check_scroll_position)
        canvas.bind('<MouseWheel>', self.on_mousewheel)
        canvas.bind('<Button-4>', self.on_mousewheel)
        canvas.bind('<Button-5>', self.on_mousewheel)

    def on_mousewheel(self, event):
        """鼠标滚轮事件"""
        # 滚动Canvas
        if event.num == 4 or event.delta > 0:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:
            self.canvas.yview_scroll(1, "units")

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
            self.text.delete(1.0, tk.END)

        # 加载初始数据（更多）
        initial_load = min(self.max_initial, len(self.data))
        self.current_index = 0
        self.load_batch(initial_load)

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