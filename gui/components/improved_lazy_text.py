#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
改进的懒加载文本组件 - 优化版本
支持大量日志的高效显示和滚动加载
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Union, Dict, Tuple, Any, Optional


class ImprovedLazyText(tk.Frame):
    """
    懒加载文本组件
    支持大量数据的高效展示，通过滚动动态加载内容
    """

    # 默认配置
    DEFAULT_BATCH_SIZE = 100
    DEFAULT_MAX_INITIAL = 500
    SCROLL_THRESHOLD = 0.95  # 滚动到95%位置时触发加载

    def __init__(self, parent, batch_size: int = DEFAULT_BATCH_SIZE,
                 max_initial: int = DEFAULT_MAX_INITIAL, **text_kwargs):
        """
        初始化懒加载文本组件

        Args:
            parent: 父组件
            batch_size: 每批加载的数据量
            max_initial: 初始加载的最大数据量
            **text_kwargs: 传递给Text组件的额外参数
        """
        super().__init__(parent)

        # 配置参数
        self.batch_size = batch_size
        self.max_initial = max_initial

        # 状态变量
        self.current_index = 0
        self.data: List[Any] = []
        self.is_loading = False
        self._pending_load = False

        # 创建UI组件
        self._create_widgets(**text_kwargs)
        self._setup_bindings()

    def _create_widgets(self, **text_kwargs):
        """创建UI组件"""
        # 创建容器
        container = tk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True)

        # 创建滚动条
        self.v_scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL)

        # 配置Text组件默认参数
        default_kwargs = {
            'wrap': tk.WORD,
            'highlightthickness': 0,
            'borderwidth': 0,
            'yscrollcommand': self.v_scrollbar.set,
            'selectbackground': '#4A90E2',  # 选中背景色（蓝色）
            'selectforeground': 'white',     # 选中文字颜色（白色）
            'inactiveselectbackground': '#B0D4F1',  # 失去焦点时的选中背景色（浅蓝色）
            'exportselection': True,  # 允许导出选择到系统剪贴板
            'cursor': 'xterm'  # 使用文本光标
        }
        default_kwargs.update(text_kwargs)

        # 创建Text组件
        self.text = tk.Text(container, **default_kwargs)

        # 设置为只读但可选择和复制
        # 使用标准的只读Text widget配置：设置为disabled但在需要时临时切换为normal
        # 但这里我们用更简单的方法：只绑定会修改内容的事件

        # 阻止所有会修改文本的操作
        def block_edit(event):
            return 'break'

        # 绑定所有会修改内容的事件
        for event_type in ['<BackSpace>', '<Delete>', '<Insert>', '<Return>', '<Tab>']:
            self.text.bind(event_type, block_edit)

        # 阻止粘贴操作
        self.text.bind('<<Paste>>', block_edit)
        self.text.bind('<Control-v>', block_edit)
        self.text.bind('<Command-v>', block_edit)

        # 阻止中键粘贴（Linux）
        self.text.bind('<Button-2>', block_edit)

        # 阻止普通字符输入（但不阻止Cmd+C等快捷键）
        def block_char_input(event):
            # 如果是修饰键组合（Ctrl/Cmd + 其他键），允许通过
            if event.state & (0x4 | 0x8 | 0x10000):  # Control/Alt/Command
                return None
            # 如果是可打印字符，阻止
            if len(event.char) > 0 and event.char.isprintable():
                return 'break'
            return None

        self.text.bind('<Key>', block_char_input)
        self.v_scrollbar.config(command=self.text.yview)

        # 布局
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 配置提示标签样式
        self.text.tag_config("HINT", foreground="gray", font=("Arial", 10, "italic"))

    def _setup_bindings(self):
        """设置事件绑定"""
        # 滚动条事件
        self.v_scrollbar.bind('<ButtonRelease-1>', self._on_scrollbar_release)

        # 鼠标滚轮事件
        self.text.bind('<MouseWheel>', self._on_mousewheel)  # Windows/Mac
        self.text.bind('<Button-4>', self._on_mousewheel)    # Linux向上
        self.text.bind('<Button-5>', self._on_mousewheel)    # Linux向下

    def _on_mousewheel(self, event):
        """处理鼠标滚轮事件"""
        # 计算滚动方向和距离
        if event.num == 4 or (event.delta and event.delta > 0):
            self.text.yview_scroll(-3, "units")
        elif event.num == 5 or (event.delta and event.delta < 0):
            self.text.yview_scroll(3, "units")

        # 延迟检查是否需要加载更多
        if not self._pending_load:
            self._pending_load = True
            self.after(100, self._check_and_load)

    def _on_scrollbar_release(self, event):
        """滚动条释放事件"""
        self._check_scroll_position()

    def _check_and_load(self):
        """检查并加载数据"""
        self._pending_load = False
        self._check_scroll_position()

    def _check_scroll_position(self):
        """检查滚动位置，决定是否加载更多数据"""
        if self.is_loading or self.current_index >= len(self.data):
            return

        # 获取滚动位置 (top, bottom)
        scroll_pos = self.v_scrollbar.get()
        if len(scroll_pos) >= 2 and scroll_pos[1] >= self.SCROLL_THRESHOLD:
            self.load_more()

    def set_data(self, data_list: List[Any], clear: bool = True):
        """
        设置要显示的数据

        Args:
            data_list: 数据列表，支持以下格式：
                - str: 纯文本
                - tuple: (text, tag)
                - dict: {'text': str, 'tag': str, 'prefix': str, 'prefix_tag': str}
            clear: 是否清空现有内容
        """
        self.data = data_list
        self.current_index = 0

        if clear:
            self._clear_text()

        # 加载初始数据
        if self.data:
            initial_count = min(self.max_initial, len(self.data))
            self._load_batch(initial_count)

    def _clear_text(self):
        """清空文本内容"""
        self.text.delete(1.0, tk.END)

    def _load_batch(self, count: int):
        """
        加载一批数据

        Args:
            count: 要加载的数据数量
        """
        if self.current_index >= len(self.data) or count <= 0:
            return

        self.is_loading = True

        try:
            # 删除加载提示（如果存在）
            self._remove_load_hint()

            # 计算加载范围
            end_index = min(self.current_index + count, len(self.data))

            # 批量插入数据，优化性能
            self._insert_items(self.current_index, end_index)

            self.current_index = end_index

            # 添加加载提示（如果还有数据）
            self._add_load_hint()

        finally:
            self.is_loading = False

    def _insert_items(self, start_idx: int, end_idx: int):
        """批量插入数据项（优化版：批量构建文本，减少insert调用）

        性能优化：
        - 先构建完整文本，一次性插入（N次insert→1次insert）
        - 合并连续相同标签，减少tag_add调用
        - 预期提升渲染速度 60-80%
        """
        text_parts = []
        tag_ranges = []  # [(start_pos, end_pos, tag)]
        current_pos = 0

        for i in range(start_idx, end_idx):
            item = self.data[i]

            if isinstance(item, dict):
                # 字典格式：支持前缀和主文本
                if 'prefix' in item:
                    prefix = item['prefix']
                    prefix_len = len(prefix)
                    if prefix_len > 0:
                        text_parts.append(prefix)
                        if item.get('prefix_tag'):
                            tag_ranges.append((current_pos, current_pos + prefix_len, item['prefix_tag']))
                        current_pos += prefix_len

                text = item['text']
                text_len = len(text)
                if text_len > 0:
                    text_parts.append(text)
                    if item.get('tag'):
                        tag_ranges.append((current_pos, current_pos + text_len, item['tag']))
                    current_pos += text_len

            elif isinstance(item, tuple) and len(item) == 2:
                # 元组格式：(文本, 标签)
                text = item[0]
                text_len = len(text)
                if text_len > 0:
                    text_parts.append(text)
                    if item[1]:
                        tag_ranges.append((current_pos, current_pos + text_len, item[1]))
                    current_pos += text_len
            else:
                # 纯文本格式
                text = str(item)
                text_len = len(text)
                if text_len > 0:
                    text_parts.append(text)
                    current_pos += text_len

        # 一次性插入所有文本（关键优化点：N次insert→1次insert）
        if text_parts:
            full_text = ''.join(text_parts)
            insert_index = self.text.index('end')
            self.text.insert(insert_index, full_text)

            # 批量添加标签 - 合并连续相同标签
            if tag_ranges:
                # 合并连续相同标签的范围，减少tag_add调用
                merged_ranges = []
                current_tag = None
                range_start = None
                range_end = None

                for start, end, tag in tag_ranges:
                    if tag == current_tag and range_end == start:
                        # 扩展当前范围
                        range_end = end
                    else:
                        # 保存前一个范围
                        if current_tag is not None:
                            merged_ranges.append((range_start, range_end, current_tag))
                        # 开始新范围
                        current_tag = tag
                        range_start = start
                        range_end = end

                # 保存最后一个范围
                if current_tag is not None:
                    merged_ranges.append((range_start, range_end, current_tag))

                # 应用合并后的标签
                for start, end, tag in merged_ranges:
                    start_index = f"{insert_index}+{start}c"
                    end_index = f"{insert_index}+{end}c"
                    self.text.tag_add(tag, start_index, end_index)

    def _add_load_hint(self):
        """添加加载提示"""
        remaining = len(self.data) - self.current_index
        if remaining > 0:
            hint = f"\n━━━ 还有 {remaining} 条数据，滚动加载更多 ━━━\n"
            self.text.insert(tk.END, hint, "HINT")

    def _remove_load_hint(self):
        """移除加载提示"""
        # 搜索并删除提示文本
        search_start = "end-200c"  # 从末尾前200个字符开始搜索
        pos = self.text.search("━━━ 还有", search_start, tk.END)
        if pos:
            # 找到提示行的结束位置
            line_end = self.text.search("\n", f"{pos}+1c", tk.END)
            if line_end:
                self.text.delete(f"{pos}-1c", f"{line_end}+1c")

    def load_more(self):
        """加载更多数据"""
        if self.current_index < len(self.data):
            self._load_batch(self.batch_size)

    def clear(self):
        """清空所有内容和数据"""
        self._clear_text()
        self.data = []
        self.current_index = 0

    # ========== 代理Text组件的方法 ==========

    def get(self, start, end) -> str:
        """获取文本内容"""
        return self.text.get(start, end)

    def insert(self, index, text: str, tags=None):
        """插入文本"""
        self.text.insert(index, text, tags)

    def delete(self, start, end):
        """删除文本"""
        self.text.delete(start, end)

    def search(self, pattern: str, start, stop=None, **kwargs) -> Optional[str]:
        """搜索文本"""
        return self.text.search(pattern, start, stop, **kwargs)

    def tag_add(self, tagname: str, start, end):
        """添加标签"""
        self.text.tag_add(tagname, start, end)

    def tag_config(self, tagname: str, **kwargs):
        """配置标签样式"""
        self.text.tag_config(tagname, **kwargs)

    def tag_remove(self, tagname: str, start, end):
        """移除标签"""
        self.text.tag_remove(tagname, start, end)

    def tag_delete(self, tagname: str):
        """删除标签"""
        self.text.tag_delete(tagname)

    def see(self, index):
        """滚动到指定位置"""
        self.text.see(index)

    def mark_set(self, markname: str, index):
        """设置标记"""
        self.text.mark_set(markname, index)

    def yview(self, *args):
        """纵向滚动"""
        return self.text.yview(*args)

    def xview(self, *args):
        """横向滚动"""
        return self.text.xview(*args)

    def index(self, index):
        """获取索引"""
        return self.text.index(index)

    def bbox(self, index):
        """获取边界框"""
        return self.text.bbox(index)


# 测试代码
if __name__ == "__main__":
    root = tk.Tk()
    root.title("懒加载文本组件测试")
    root.geometry("800x600")

    # 创建懒加载文本组件
    lazy_text = ImprovedLazyText(root, batch_size=50, max_initial=100)
    lazy_text.pack(fill=tk.BOTH, expand=True)

    # 配置一些标签样式
    lazy_text.tag_config("ERROR", foreground="red", font=("Courier", 11, "bold"))
    lazy_text.tag_config("INFO", foreground="blue")
    lazy_text.tag_config("DEBUG", foreground="gray")

    # 生成测试数据
    test_data = []
    for i in range(1000):
        level = ["INFO", "DEBUG", "ERROR"][i % 3]
        text = f"[{level}] Line {i+1}: This is a test log message\n"
        test_data.append((text, level))

    # 设置数据
    lazy_text.set_data(test_data)

    root.mainloop()