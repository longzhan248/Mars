#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
支持懒加载的滚动文本组件
"""

import tkinter as tk
from tkinter import ttk, scrolledtext

class LazyLoadText(tk.Frame):
    """支持懒加载的文本组件"""

    def __init__(self, parent, batch_size=200, **kwargs):
        super().__init__(parent)

        self.batch_size = batch_size
        self.current_index = 0
        self.data = []
        self.tags_config = {}
        self.is_loading = False
        self.refresh_pending = False

        # 创建文本组件和滚动条
        self.create_widgets(**kwargs)

    def create_widgets(self, **text_kwargs):
        """创建组件"""
        # 垂直滚动条
        v_scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 文本组件
        default_kwargs = {
            'wrap': tk.WORD,
            'yscrollcommand': v_scrollbar.set,
            'selectbackground': '#4A90E2',  # 选中背景色（蓝色）
            'selectforeground': 'white',     # 选中文字颜色（白色）
            'inactiveselectbackground': '#B0D4F1',  # 失去焦点时的选中背景色（浅蓝色）
            'exportselection': True,  # 允许导出选择到系统剪贴板
            'cursor': 'xterm'  # 使用文本光标
        }
        default_kwargs.update(text_kwargs)

        self.text = tk.Text(self, **default_kwargs)
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 设置为只读但可选择（通过绑定阻止输入）
        self.text.bind('<Key>', lambda e: 'break')  # 阻止键盘输入
        self.text.bind('<Button-2>', lambda e: 'break')  # 阻止中键粘贴（Linux）
        self.text.bind('<Button-3>', lambda e: None)  # 允许右键（可用于复制菜单）

        v_scrollbar.config(command=self.on_scroll)

        # 绑定滚动事件
        self.text.bind('<MouseWheel>', self.on_mousewheel)
        self.text.bind('<Button-4>', self.on_mousewheel)
        self.text.bind('<Button-5>', self.on_mousewheel)

        # 绑定配置改变事件以触发重绘
        self.text.bind('<Configure>', self.on_configure)
        self.text.bind('<Expose>', self.on_expose)
        self.text.bind('<Visibility>', self.on_visibility)

    def on_scroll(self, *args):
        """滚动条事件"""
        self.text.yview(*args)

        # 检查是否需要加载更多
        if args[0] == 'moveto':
            position = float(args[1])
            if position > 0.85 and not self.is_loading:  # 滚动到85%位置时提前加载
                # 使用after确保不阻塞滚动
                self.after(10, self.load_more)

        # 滚动后刷新显示
        self.after(1, self.refresh_display)

    def on_mousewheel(self, event):
        """鼠标滚轮事件"""
        # 获取当前滚动位置
        bottom = self.text.yview()[1]
        if bottom >= 0.90 and not self.is_loading:  # 接近底部时提前加载
            # 使用after确保不阻塞滚动
            self.after(10, self.load_more)

        # 强制重绘文本组件
        self.refresh_display()

    def on_configure(self, event=None):
        """配置改变事件"""
        self.refresh_display()

    def on_expose(self, event=None):
        """暴露事件"""
        self.refresh_display()

    def on_visibility(self, event=None):
        """可见性改变事件"""
        if event.state == 'VisibilityUnobscured':
            self.refresh_display()

    def refresh_display(self):
        """强制刷新显示以避免灰色蒙层"""
        if self.refresh_pending:
            return

        self.refresh_pending = True

        def do_refresh():
            try:
                # 保存当前滚动位置
                pos = self.text.yview()

                # 获取可见范围
                first_visible = self.text.index('@0,0')
                last_visible = self.text.index(f'@0,{self.text.winfo_height()}')

                # 强制重绘：通过修改和恢复状态
                # 插入并立即删除一个不可见字符
                self.text.insert(first_visible, '\u200b')  # 零宽空格
                self.text.delete(first_visible)

                # 强制更新所有待处理的事件
                self.text.update()
                self.text.update_idletasks()

                # 恢复滚动位置
                self.text.yview_moveto(pos[0])

            finally:
                self.refresh_pending = False

        # 延迟执行刷新
        self.after(5, do_refresh)

    def set_data(self, data_list, clear=True):
        """设置数据"""
        self.data = data_list
        self.current_index = 0

        if clear:
            self.text.delete(1.0, tk.END)

        # 加载第一批数据
        self.load_more()

    def load_more(self):
        """加载更多数据"""
        if self.current_index >= len(self.data):
            return

        self.is_loading = True

        # 保存当前滚动位置
        current_pos = self.text.yview()

        # 加载下一批数据
        end_index = min(self.current_index + self.batch_size, len(self.data))

        for i in range(self.current_index, end_index):
            item = self.data[i]

            if isinstance(item, tuple):
                # (text, tag) 格式
                text, tag = item
                self.text.insert(tk.END, text, tag)
            elif isinstance(item, dict):
                # {'text': ..., 'tag': ..., 'prefix': ...} 格式
                if 'prefix' in item:
                    self.text.insert(tk.END, item['prefix'], item.get('prefix_tag'))
                self.text.insert(tk.END, item['text'], item.get('tag'))
            else:
                # 纯文本
                self.text.insert(tk.END, str(item))

        self.current_index = end_index

        # 如果还有更多数据，显示提示
        remaining = len(self.data) - self.current_index
        if remaining > 0:
            self.text.insert(tk.END, f"\n... 向下滚动加载更多 ({remaining} 条) ...\n", "HINT")
            # 删除之前的提示
            self.remove_old_hint()
        else:
            self.text.insert(tk.END, f"\n--- 已加载全部 {len(self.data)} 条 ---\n", "HINT")
            self.remove_old_hint()

        # 强制刷新显示
        self.text.update_idletasks()
        self.update()

        self.is_loading = False

    def remove_old_hint(self):
        """删除旧的加载提示"""
        # 查找并删除之前的提示文本
        content = self.text.get(1.0, tk.END)
        lines = content.split('\n')

        for i, line in enumerate(lines[:-3], 1):  # 不检查最后几行
            if '... 向下滚动加载更多' in line or '--- 已加载全部' in line:
                # 删除这一行
                self.text.delete(f"{i}.0", f"{i+1}.0")
                break

    def tag_config(self, tag_name, **kwargs):
        """配置标签样式"""
        self.text.tag_config(tag_name, **kwargs)
        self.tags_config[tag_name] = kwargs

    def clear(self):
        """清空内容"""
        self.text.delete(1.0, tk.END)
        self.data = []
        self.current_index = 0

    def get(self, start, end):
        """获取文本内容"""
        return self.text.get(start, end)

    def insert(self, index, text, tags=None):
        """插入文本"""
        self.text.insert(index, text, tags)

    def delete(self, start, end):
        """删除文本"""
        self.text.delete(start, end)

    def search(self, pattern, start, stop=None, **kwargs):
        """搜索文本"""
        return self.text.search(pattern, start, stop, **kwargs)

    def tag_add(self, tag_name, start, end):
        """添加标签"""
        self.text.tag_add(tag_name, start, end)