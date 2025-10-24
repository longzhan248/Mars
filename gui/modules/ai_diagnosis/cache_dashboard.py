#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI分析缓存统计仪表板

可视化展示缓存效果、命中率、热门查询等统计信息。

核心功能:
1. 实时统计显示 (总查询数、命中率、缓存大小)
2. 命中率趋势图
3. 热门查询Top 10
4. 缓存管理操作 (清空、导出、导入)
5. 自动刷新
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Dict, List
import time


class CacheDashboard(tk.Toplevel):
    """
    缓存统计仪表板

    使用示例:
        dashboard = CacheDashboard(parent, cache)
        dashboard.show()
    """

    def __init__(self, parent, analysis_cache, **kwargs):
        """
        初始化仪表板

        Args:
            parent: 父窗口
            analysis_cache: AnalysisCache实例
        """
        super().__init__(parent, **kwargs)

        self.cache = analysis_cache
        self.title("AI分析缓存统计 - Cache Dashboard")
        self.geometry("900x650")

        # 自动刷新定时器
        self.auto_refresh_id = None
        self.auto_refresh_enabled = tk.BooleanVar(value=True)

        # 创建UI
        self._create_widgets()

        # 首次刷新
        self.refresh()

        # 启动自动刷新
        self._start_auto_refresh()

    def _create_widgets(self):
        """创建UI组件"""
        # 工具栏
        toolbar = ttk.Frame(self)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        ttk.Button(toolbar, text="🔄 刷新", command=self.refresh).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🗑️ 清空缓存", command=self.clear_cache).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="💾 导出缓存", command=self.export_cache).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="📥 导入缓存", command=self.import_cache).pack(side=tk.LEFT, padx=2)

        # 自动刷新选项
        ttk.Checkbutton(
            toolbar,
            text="自动刷新 (5秒)",
            variable=self.auto_refresh_enabled,
            command=self._toggle_auto_refresh
        ).pack(side=tk.LEFT, padx=10)

        # 主容器
        main_frame = ttk.Frame(self)
        main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 左侧: 统计卡片
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        # 统计卡片区域
        self._create_stat_cards(left_frame)

        # 热门查询列表
        self._create_top_queries_section(left_frame)

        # 右侧: 详细信息
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)

        # 缓存详情
        self._create_cache_details_section(right_frame)

        # 性能建议
        self._create_performance_tips_section(right_frame)

    def _create_stat_cards(self, parent):
        """创建统计卡片"""
        cards_frame = ttk.Frame(parent)
        cards_frame.pack(side=tk.TOP, fill=tk.X, pady=5)

        # 卡片样式
        card_style = {"relief": "groove", "borderwidth": 2, "padding": "10"}

        # 总查询数
        card1 = ttk.LabelFrame(cards_frame, text="总查询数", **card_style)
        card1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)

        self.total_queries_label = ttk.Label(
            card1,
            text="0",
            font=("Arial", 24, "bold"),
            foreground="#3498db"
        )
        self.total_queries_label.pack()

        # 缓存命中率
        card2 = ttk.LabelFrame(cards_frame, text="缓存命中率", **card_style)
        card2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)

        self.hit_rate_label = ttk.Label(
            card2,
            text="0%",
            font=("Arial", 24, "bold"),
            foreground="#27ae60"
        )
        self.hit_rate_label.pack()

        # 缓存大小
        card3 = ttk.LabelFrame(cards_frame, text="缓存大小", **card_style)
        card3.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)

        self.cache_size_label = ttk.Label(
            card3,
            text="0",
            font=("Arial", 24, "bold"),
            foreground="#e67e22"
        )
        self.cache_size_label.pack()

        # 第二行卡片
        cards_frame2 = ttk.Frame(parent)
        cards_frame2.pack(side=tk.TOP, fill=tk.X, pady=5)

        # 缓存命中次数
        card4 = ttk.LabelFrame(cards_frame2, text="缓存命中", **card_style)
        card4.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)

        self.cache_hits_label = ttk.Label(
            card4,
            text="0",
            font=("Arial", 18, "bold"),
            foreground="#2ecc71"
        )
        self.cache_hits_label.pack()

        # 缓存未命中
        card5 = ttk.LabelFrame(cards_frame2, text="缓存未命中", **card_style)
        card5.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)

        self.cache_misses_label = ttk.Label(
            card5,
            text="0",
            font=("Arial", 18, "bold"),
            foreground="#e74c3c"
        )
        self.cache_misses_label.pack()

        # 淘汰次数
        card6 = ttk.LabelFrame(cards_frame2, text="淘汰次数", **card_style)
        card6.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)

        self.evictions_label = ttk.Label(
            card6,
            text="0",
            font=("Arial", 18, "bold"),
            foreground="#95a5a6"
        )
        self.evictions_label.pack()

    def _create_top_queries_section(self, parent):
        """创建热门查询区域"""
        frame = ttk.LabelFrame(parent, text="🔥 热门查询 Top 10", padding="10")
        frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=10)

        # 树形列表
        columns = ("问题类型", "命中次数", "最后访问")
        self.top_queries_tree = ttk.Treeview(
            frame,
            columns=columns,
            show="tree headings",
            height=8
        )

        # 设置列
        self.top_queries_tree.heading("#0", text="查询内容")
        self.top_queries_tree.column("#0", width=300)

        for col in columns:
            self.top_queries_tree.heading(col, text=col)
            self.top_queries_tree.column(col, width=100, anchor="center")

        # 滚动条
        scrollbar = ttk.Scrollbar(
            frame,
            orient=tk.VERTICAL,
            command=self.top_queries_tree.yview
        )
        self.top_queries_tree.config(yscrollcommand=scrollbar.set)

        self.top_queries_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_cache_details_section(self, parent):
        """创建缓存详情区域"""
        frame = ttk.LabelFrame(parent, text="📊 缓存详情", padding="10")
        frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=5)

        self.details_text = tk.Text(
            frame,
            height=15,
            wrap=tk.WORD,
            font=("Courier", 10)
        )
        self.details_text.pack(fill=tk.BOTH, expand=True)

    def _create_performance_tips_section(self, parent):
        """创建性能建议区域"""
        frame = ttk.LabelFrame(parent, text="💡 性能建议", padding="10")
        frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=5)

        self.tips_text = tk.Text(
            frame,
            height=10,
            wrap=tk.WORD,
            font=("Arial", 10)
        )
        self.tips_text.pack(fill=tk.BOTH, expand=True)

    def refresh(self):
        """刷新统计数据"""
        if not self.cache:
            return

        # 获取统计信息
        stats = self.cache.get_stats()

        # 更新卡片
        self.total_queries_label.config(text=str(stats['total_queries']))
        self.hit_rate_label.config(text=stats['hit_rate'])
        self.cache_size_label.config(text=str(stats['size']))
        self.cache_hits_label.config(text=str(stats['cache_hits']))
        self.cache_misses_label.config(text=str(stats['cache_misses']))
        self.evictions_label.config(text=str(stats['evictions']))

        # 命中率颜色 (根据百分比)
        hit_rate_value = float(stats['hit_rate'].rstrip('%'))
        if hit_rate_value >= 70:
            color = "#27ae60"  # 绿色
        elif hit_rate_value >= 50:
            color = "#f39c12"  # 橙色
        else:
            color = "#e74c3c"  # 红色
        self.hit_rate_label.config(foreground=color)

        # 更新热门查询
        self._refresh_top_queries()

        # 更新详情
        self._refresh_details(stats)

        # 更新建议
        self._refresh_tips(stats)

    def _refresh_top_queries(self):
        """刷新热门查询列表"""
        # 清空
        for item in self.top_queries_tree.get_children():
            self.top_queries_tree.delete(item)

        # 获取Top 10
        top_queries = self.cache.get_top_queries(limit=10)

        for i, item in enumerate(top_queries, 1):
            query = item['query']
            problem_type = item['problem_type'] or "未知"
            hit_count = item['hit_count']
            last_accessed = item['last_accessed'].split('T')[1].split('.')[0]  # 只显示时间

            # 插入行
            self.top_queries_tree.insert(
                "",
                tk.END,
                text=f"{i}. {query[:50]}...",
                values=(problem_type, hit_count, last_accessed)
            )

    def _refresh_details(self, stats: Dict):
        """刷新缓存详情"""
        self.details_text.delete("1.0", tk.END)

        details = f"""=== 缓存统计详情 ===

总查询数: {stats['total_queries']}
缓存命中: {stats['cache_hits']}
缓存未命中: {stats['cache_misses']}
命中率: {stats['hit_rate']}

当前缓存大小: {stats['size']}
淘汰次数: {stats['evictions']}

=== 性能指标 ===

平均响应时间:
  - 命中: ~0.1秒 ⚡
  - 未命中: ~10秒

预估节省时间:
  - {stats['cache_hits']} × 10秒 = {stats['cache_hits'] * 10}秒
  - ≈ {stats['cache_hits'] * 10 // 60}分钟

API成本节省:
  - 命中率: {stats['hit_rate']}
  - 节省比例: ~{stats['hit_rate']}
"""

        self.details_text.insert("1.0", details)

    def _refresh_tips(self, stats: Dict):
        """刷新性能建议"""
        self.tips_text.delete("1.0", tk.END)

        tips = []

        # 根据命中率给建议
        hit_rate_value = float(stats['hit_rate'].rstrip('%'))

        if hit_rate_value < 50:
            tips.append("⚠️  命中率较低 (<50%)\n   建议: 查询内容差异较大,考虑增加缓存大小")
        elif hit_rate_value < 70:
            tips.append("💡 命中率中等 (50-70%)\n   建议: 继续积累缓存,效果会逐步提升")
        else:
            tips.append("✅ 命中率良好 (>70%)\n   缓存工作正常,继续保持!")

        # 缓存大小建议
        if stats['size'] >= 180:  # 接近上限200
            tips.append("\n⚠️  缓存接近上限\n   建议: 考虑增加max_size或清理旧缓存")

        # 淘汰建议
        if stats['evictions'] > stats['size']:
            tips.append("\n⚠️  淘汰次数较多\n   建议: 增加缓存容量,减少频繁淘汰")

        # 使用建议
        tips.append("\n\n📖 使用建议:")
        tips.append("• 定期导出缓存,避免数据丢失")
        tips.append("• 清理超过24小时的旧缓存")
        tips.append("• 相似问题会自动命中缓存")

        self.tips_text.insert("1.0", "\n".join(tips))

    def clear_cache(self):
        """清空缓存"""
        if messagebox.askyesno("确认", "确定要清空所有缓存吗?\n\n此操作不可恢复!"):
            self.cache.clear()
            self.refresh()
            messagebox.showinfo("成功", "缓存已清空")

    def export_cache(self):
        """导出缓存"""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )

        if filepath:
            self.cache.save_to_file(filepath)
            messagebox.showinfo("成功", f"缓存已导出到:\n{filepath}")

    def import_cache(self):
        """导入缓存"""
        filepath = filedialog.askopenfilename(
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )

        if filepath:
            try:
                self.cache.load_from_file(filepath)
                self.refresh()
                messagebox.showinfo("成功", f"缓存已导入:\n{len(self.cache.cache)}条")
            except Exception as e:
                messagebox.showerror("错误", f"导入失败:\n{str(e)}")

    def _start_auto_refresh(self):
        """启动自动刷新"""
        if self.auto_refresh_enabled.get():
            self.refresh()
            self.auto_refresh_id = self.after(5000, self._start_auto_refresh)  # 5秒刷新

    def _toggle_auto_refresh(self):
        """切换自动刷新"""
        if self.auto_refresh_id:
            self.after_cancel(self.auto_refresh_id)
            self.auto_refresh_id = None

        if self.auto_refresh_enabled.get():
            self._start_auto_refresh()

    def destroy(self):
        """销毁窗口时取消定时器"""
        if self.auto_refresh_id:
            self.after_cancel(self.auto_refresh_id)
        super().destroy()


# 便捷函数
def show_cache_dashboard(parent, analysis_cache):
    """显示缓存统计仪表板"""
    dashboard = CacheDashboard(parent, analysis_cache)
    return dashboard


# 测试代码
if __name__ == "__main__":
    from gui.modules.ai_diagnosis.analysis_cache import AnalysisCache

    # 创建测试窗口
    root = tk.Tk()
    root.title("缓存仪表板测试")
    root.geometry("300x200")

    # 创建测试缓存
    cache = AnalysisCache(max_size=200)

    # 添加测试数据
    for i in range(50):
        query = f"分析崩溃日志 {i}"
        response = f"这是分析结果 {i}"
        cache.put(query, response, problem_type="崩溃")

    # 模拟一些查询
    for i in range(30):
        cache.get(f"分析崩溃日志 {i % 10}")  # 重复查询前10条

    # 启动按钮
    btn = ttk.Button(
        root,
        text="打开缓存统计仪表板",
        command=lambda: show_cache_dashboard(root, cache)
    )
    btn.pack(pady=20)

    root.mainloop()
