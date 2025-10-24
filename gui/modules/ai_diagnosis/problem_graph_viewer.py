#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
问题链路图可视化查看器

提供图形化的问题关系展示,帮助用户理解问题之间的因果关系。

核心功能:
1. 问题节点可视化 (Canvas绘制)
2. 关系连线 (箭头表示因果)
3. 节点点击跳转
4. 自动布局算法
5. 缩放和拖动
"""

import tkinter as tk
from tkinter import ttk, font as tkfont
from typing import Dict, List, Tuple, Optional
import math


class ProblemGraphViewer(tk.Toplevel):
    """
    问题链路图查看器

    使用示例:
        viewer = ProblemGraphViewer(parent, navigator)
        viewer.show()
    """

    def __init__(self, parent, navigator, **kwargs):
        """
        初始化图形查看器

        Args:
            parent: 父窗口
            navigator: LogNavigator实例
        """
        super().__init__(parent, **kwargs)

        self.navigator = navigator
        self.title("问题链路图 - Problem Graph")
        self.geometry("800x600")

        # 节点位置缓存 {node_id: (x, y)}
        self.node_positions: Dict[int, Tuple[float, float]] = {}

        # 选中的节点
        self.selected_node: Optional[int] = None

        # 缩放级别
        self.zoom_level = 1.0

        # 创建UI
        self._create_widgets()
        self._setup_bindings()

        # 加载数据
        self.refresh()

    def _create_widgets(self):
        """创建UI组件"""
        # 工具栏
        toolbar = ttk.Frame(self)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        ttk.Button(toolbar, text="🔄 刷新", command=self.refresh).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🔍 放大", command=self.zoom_in).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🔍 缩小", command=self.zoom_out).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="⚡ 自动布局", command=self.auto_layout).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🗑️ 清除图谱", command=self.clear_graph).pack(side=tk.LEFT, padx=2)

        # 统计信息
        self.stats_label = ttk.Label(toolbar, text="节点: 0 | 连接: 0")
        self.stats_label.pack(side=tk.RIGHT, padx=10)

        # 画布 (带滚动条)
        canvas_frame = ttk.Frame(self)
        canvas_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 滚动条
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Canvas
        self.canvas = tk.Canvas(
            canvas_frame,
            bg='white',
            scrollregion=(0, 0, 2000, 2000),  # 初始滚动区域
            xscrollcommand=h_scrollbar.set,
            yscrollcommand=v_scrollbar.set
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        h_scrollbar.config(command=self.canvas.xview)
        v_scrollbar.config(command=self.canvas.yview)

        # 详情面板
        detail_frame = ttk.LabelFrame(self, text="节点详情", padding="10")
        detail_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)

        self.detail_text = tk.Text(detail_frame, height=6, wrap=tk.WORD)
        self.detail_text.pack(fill=tk.BOTH, expand=True)

    def _setup_bindings(self):
        """设置事件绑定"""
        # 点击节点
        self.canvas.tag_bind("node", "<Button-1>", self._on_node_click)

        # 双击跳转
        self.canvas.tag_bind("node", "<Double-Button-1>", self._on_node_double_click)

        # 鼠标悬停显示提示
        self.canvas.tag_bind("node", "<Enter>", self._on_node_enter)
        self.canvas.tag_bind("node", "<Leave>", self._on_node_leave)

        # 拖动画布
        self.canvas.bind("<ButtonPress-2>", self._start_pan)  # 中键按下
        self.canvas.bind("<B2-Motion>", self._do_pan)          # 中键拖动

    def refresh(self):
        """刷新图谱"""
        # 清空画布
        self.canvas.delete("all")
        self.node_positions.clear()

        if not self.navigator or not self.navigator.problem_graph:
            self._draw_empty_state()
            return

        # 自动布局
        self.auto_layout()

        # 绘制
        self._draw_graph()

        # 更新统计
        self._update_stats()

    def _draw_empty_state(self):
        """绘制空状态"""
        self.canvas.create_text(
            400, 300,
            text="暂无问题节点\n\nAI分析日志后会自动创建问题链路",
            font=("Arial", 14),
            fill="gray",
            justify=tk.CENTER
        )

    def _draw_graph(self):
        """绘制问题图谱"""
        graph = self.navigator.problem_graph

        # 1. 绘制连线 (先画,这样节点会在上层)
        for node_id, node in graph.items():
            if node_id not in self.node_positions:
                continue

            x1, y1 = self.node_positions[node_id]

            for related_id in node.related_nodes:
                if related_id not in self.node_positions:
                    continue

                x2, y2 = self.node_positions[related_id]

                # 绘制箭头 (从node_id → related_id)
                self._draw_arrow(x1, y1, x2, y2)

        # 2. 绘制节点
        for node_id, node in graph.items():
            if node_id not in self.node_positions:
                continue

            x, y = self.node_positions[node_id]

            # 节点颜色 (根据问题类型)
            color = self._get_node_color(node.problem_type)

            # 绘制节点
            self._draw_node(node_id, x, y, node.problem_type, node.description, color)

    def _draw_node(self, node_id: int, x: float, y: float, problem_type: str, description: str, color: str):
        """绘制单个节点"""
        radius = 40 * self.zoom_level

        # 圆形节点
        circle = self.canvas.create_oval(
            x - radius, y - radius,
            x + radius, y + radius,
            fill=color,
            outline="black",
            width=2,
            tags=("node", f"node_{node_id}")
        )

        # 问题类型标签
        type_text = self.canvas.create_text(
            x, y - 10,
            text=problem_type,
            font=("Arial", int(10 * self.zoom_level), "bold"),
            fill="white",
            tags=("node", f"node_{node_id}")
        )

        # 行号
        line_num = self.navigator.problem_graph[node_id].location.line_number
        line_text = self.canvas.create_text(
            x, y + 10,
            text=f"行{line_num}",
            font=("Arial", int(8 * self.zoom_level)),
            fill="white",
            tags=("node", f"node_{node_id}")
        )

        # 存储节点ID (用于点击事件)
        self.canvas.tag_bind(f"node_{node_id}", "<Button-1>", lambda e, nid=node_id: self._on_node_click_with_id(nid))
        self.canvas.tag_bind(f"node_{node_id}", "<Double-Button-1>", lambda e, nid=node_id: self._on_node_double_click_with_id(nid))

    def _draw_arrow(self, x1: float, y1: float, x2: float, y2: float):
        """绘制箭头 (从点1到点2)"""
        # 计算方向
        dx = x2 - x1
        dy = y2 - y1
        length = math.sqrt(dx**2 + dy**2)

        if length == 0:
            return

        # 单位向量
        ux = dx / length
        uy = dy / length

        # 缩短箭头,不覆盖节点
        radius = 40 * self.zoom_level
        start_x = x1 + ux * radius
        start_y = y1 + uy * radius
        end_x = x2 - ux * radius
        end_y = y2 - uy * radius

        # 绘制箭头
        self.canvas.create_line(
            start_x, start_y,
            end_x, end_y,
            arrow=tk.LAST,
            width=2,
            fill="gray",
            smooth=True
        )

    def _get_node_color(self, problem_type: str) -> str:
        """根据问题类型返回节点颜色"""
        color_map = {
            "崩溃": "#e74c3c",      # 红色
            "内存": "#e67e22",      # 橙色
            "网络": "#3498db",      # 蓝色
            "性能": "#f39c12",      # 黄色
            "错误": "#c0392b",      # 深红
            "警告": "#f1c40f",      # 金黄
            "初始化错误": "#9b59b6", # 紫色
            "关联问题": "#95a5a6",  # 灰色
        }
        return color_map.get(problem_type, "#34495e")  # 默认深灰

    def auto_layout(self):
        """自动布局算法 (简单的分层布局)"""
        if not self.navigator or not self.navigator.problem_graph:
            return

        graph = self.navigator.problem_graph

        # 1. 查找根节点 (没有入边的节点)
        all_nodes = set(graph.keys())
        has_incoming = set()
        for node in graph.values():
            has_incoming.update(node.related_nodes)

        root_nodes = all_nodes - has_incoming

        # 2. 分层 (BFS)
        layers: List[List[int]] = []
        visited = set()
        current_layer = list(root_nodes)

        while current_layer:
            layers.append(current_layer[:])
            visited.update(current_layer)

            # 下一层
            next_layer = []
            for node_id in current_layer:
                if node_id in graph:
                    for related_id in graph[node_id].related_nodes:
                        if related_id not in visited:
                            next_layer.append(related_id)

            current_layer = next_layer

        # 3. 计算位置
        canvas_width = 800
        canvas_height = 600
        layer_height = 120  # 层间距

        for level, layer in enumerate(layers):
            y = 100 + level * layer_height
            num_nodes = len(layer)

            # 水平分布
            if num_nodes == 1:
                x_positions = [canvas_width / 2]
            else:
                spacing = min(canvas_width * 0.8 / (num_nodes - 1), 200)
                start_x = (canvas_width - spacing * (num_nodes - 1)) / 2
                x_positions = [start_x + i * spacing for i in range(num_nodes)]

            for i, node_id in enumerate(layer):
                self.node_positions[node_id] = (x_positions[i], y)

        # 更新滚动区域
        if layers:
            max_y = 100 + len(layers) * layer_height + 100
            self.canvas.config(scrollregion=(0, 0, canvas_width, max_y))

    def zoom_in(self):
        """放大"""
        self.zoom_level = min(self.zoom_level * 1.2, 3.0)
        self.refresh()

    def zoom_out(self):
        """缩小"""
        self.zoom_level = max(self.zoom_level / 1.2, 0.5)
        self.refresh()

    def clear_graph(self):
        """清除图谱"""
        from tkinter import messagebox

        if messagebox.askyesno("确认", "确定要清除所有问题节点吗?"):
            if self.navigator:
                self.navigator.problem_graph.clear()
                self.navigator.next_node_id = 0
            self.refresh()

    def _on_node_click(self, event):
        """节点点击事件"""
        # 由具体节点的binding处理
        pass

    def _on_node_click_with_id(self, node_id: int):
        """点击节点 (带ID)"""
        self.selected_node = node_id

        # 高亮选中节点
        self.canvas.delete("highlight")
        if node_id in self.node_positions:
            x, y = self.node_positions[node_id]
            radius = 45 * self.zoom_level

            self.canvas.create_oval(
                x - radius, y - radius,
                x + radius, y + radius,
                outline="blue",
                width=3,
                tags="highlight"
            )

        # 显示详情
        self._show_node_details(node_id)

    def _on_node_double_click(self, event):
        """节点双击事件"""
        pass

    def _on_node_double_click_with_id(self, node_id: int):
        """双击节点 (带ID) - 跳转到日志"""
        if self.navigator and node_id in self.navigator.problem_graph:
            node = self.navigator.problem_graph[node_id]
            line_num = node.location.line_number

            # 跳转
            self.navigator.jump_to_line(line_num, reason=f"问题链路图: {node.problem_type}")

            # 提示
            self._show_message(f"✓ 已跳转到第 {line_num} 行")

    def _on_node_enter(self, event):
        """鼠标进入节点"""
        self.canvas.config(cursor="hand2")

    def _on_node_leave(self, event):
        """鼠标离开节点"""
        self.canvas.config(cursor="")

    def _show_node_details(self, node_id: int):
        """显示节点详情"""
        if node_id not in self.navigator.problem_graph:
            return

        node = self.navigator.problem_graph[node_id]

        # 清空
        self.detail_text.delete("1.0", tk.END)

        # 显示详情
        details = f"""问题类型: {node.problem_type}
行号: {node.location.line_number}
描述: {node.description}
时间: {node.created_at.strftime('%Y-%m-%d %H:%M:%S')}
关联节点: {len(node.related_nodes)}个

AI分析:
{node.ai_analysis[:200] if node.ai_analysis else '(无)'}"""

        self.detail_text.insert("1.0", details)

    def _update_stats(self):
        """更新统计信息"""
        if not self.navigator:
            return

        node_count = len(self.navigator.problem_graph)
        edge_count = sum(len(node.related_nodes) for node in self.navigator.problem_graph.values())

        self.stats_label.config(text=f"节点: {node_count} | 连接: {edge_count}")

    def _start_pan(self, event):
        """开始拖动画布"""
        self.canvas.scan_mark(event.x, event.y)

    def _do_pan(self, event):
        """拖动画布"""
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def _show_message(self, message: str):
        """显示临时消息"""
        # 在画布顶部显示消息
        msg_id = self.canvas.create_text(
            400, 20,
            text=message,
            font=("Arial", 12, "bold"),
            fill="green",
            tags="message"
        )

        # 2秒后删除
        self.after(2000, lambda: self.canvas.delete("message"))


# 便捷函数
def show_problem_graph(parent, navigator):
    """显示问题链路图"""
    viewer = ProblemGraphViewer(parent, navigator)
    return viewer


# 测试代码
if __name__ == "__main__":
    # 创建测试窗口
    root = tk.Tk()
    root.title("问题链路图测试")
    root.geometry("900x700")

    # 模拟Navigator
    class MockNavigator:
        def __init__(self):
            from gui.modules.ai_diagnosis.log_navigator import NavigationNode, LogLocation

            self.problem_graph = {}
            self.next_node_id = 0

            # 添加测试节点
            for i in range(5):
                loc = LogLocation(
                    line_number=100 + i * 50,
                    entry_index=i,
                    entry=None,
                    timestamp="2025-10-24 10:00:00"
                )
                from datetime import datetime
                node = NavigationNode(
                    location=loc,
                    problem_type=["崩溃", "内存", "网络", "性能", "错误"][i],
                    description=f"测试问题 {i+1}",
                    related_nodes=[],
                    ai_analysis="这是AI分析结果示例...",
                    created_at=datetime.now()
                )
                self.problem_graph[i] = node

            # 建立关系
            self.problem_graph[0].related_nodes = [1, 2]
            self.problem_graph[1].related_nodes = [3]
            self.problem_graph[2].related_nodes = [4]

        def jump_to_line(self, line_num, reason):
            print(f"跳转到行 {line_num}: {reason}")
            return True

    navigator = MockNavigator()

    # 启动按钮
    btn = ttk.Button(
        root,
        text="打开问题链路图",
        command=lambda: show_problem_graph(root, navigator)
    )
    btn.pack(pady=20)

    root.mainloop()
