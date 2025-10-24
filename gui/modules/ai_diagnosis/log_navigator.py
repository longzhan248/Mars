#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI驱动的日志导航器

提供智能的日志跳转和问题追踪功能。

核心功能:
1. AI分析结果 → 日志行号映射
2. 关键日志高亮标记
3. 问题链路追踪 (问题A → 问题B → 根因C)
4. 一键跳转到相关日志位置
5. 导航历史记录 (支持前进/后退)
"""

from typing import List, Dict, Optional, Tuple, Set
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
import re


@dataclass
class LogLocation:
    """日志位置信息"""
    line_number: int        # 行号
    entry_index: int        # 条目索引
    entry: object           # 日志条目对象
    timestamp: str          # 时间戳
    highlight_text: str = "" # 高亮文本
    reason: str = ""        # 跳转原因 (例如: "AI分析:崩溃根因")


@dataclass
class NavigationNode:
    """导航节点 (问题追踪链路中的一个节点)"""
    location: LogLocation           # 日志位置
    problem_type: str = ""          # 问题类型
    description: str = ""           # 问题描述
    related_nodes: List[int] = field(default_factory=list)  # 关联节点ID
    ai_analysis: str = ""           # AI分析结果
    created_at: datetime = field(default_factory=datetime.now)


class LogNavigator:
    """
    日志导航器

    使用示例:
        navigator = LogNavigator(log_text_widget)

        # AI分析后,标记关键日志
        navigator.mark_critical_logs([10, 25, 100])

        # 跳转到指定行
        navigator.jump_to_line(25, reason="AI分析:网络错误")

        # 创建问题追踪链路
        node_id = navigator.add_problem_node(
            line_number=100,
            problem_type="崩溃",
            description="空指针异常",
            ai_analysis="..."
        )

        # 导航历史: 后退/前进
        navigator.go_back()
        navigator.go_forward()
    """

    def __init__(self, log_text_widget, all_entries: List = None):
        """
        初始化导航器

        Args:
            log_text_widget: tkinter Text控件 (日志显示区域)
            all_entries: 所有日志条目列表 (可选)
        """
        self.log_widget = log_text_widget
        self.all_entries = all_entries or []

        # 导航历史 (支持前进/后退)
        self.history = deque(maxlen=50)  # 最多保存50个历史位置
        self.history_index = -1

        # 标记的关键日志
        self.marked_lines: Set[int] = set()

        # 问题追踪图 (节点ID → NavigationNode)
        self.problem_graph: Dict[int, NavigationNode] = {}
        self.next_node_id = 0

        # 高亮标签配置
        self._setup_highlight_tags()

    def _setup_highlight_tags(self):
        """设置高亮标签样式"""
        try:
            # 关键日志高亮 (红色背景)
            self.log_widget.tag_config("critical_log", background="#ffcccc", foreground="#cc0000")

            # AI分析高亮 (黄色背景)
            self.log_widget.tag_config("ai_highlight", background="#ffffcc", foreground="#000000")

            # 当前位置高亮 (蓝色边框)
            self.log_widget.tag_config("current_position", background="#cce5ff", borderwidth=2, relief="raised")

            # 关联日志高亮 (绿色背景)
            self.log_widget.tag_config("related_log", background="#ccffcc", foreground="#006600")
        except:
            pass  # 如果widget未ready,忽略

    def jump_to_line(self, line_number: int, reason: str = "", highlight: bool = True) -> bool:
        """
        跳转到指定行号

        Args:
            line_number: 目标行号 (从1开始)
            reason: 跳转原因 (显示在状态栏)
            highlight: 是否高亮显示

        Returns:
            是否成功跳转
        """
        try:
            # 记录到历史
            current_pos = self.get_current_position()
            if current_pos != line_number:
                # 清理未来的历史 (如果从历史中间跳转)
                while self.history_index < len(self.history) - 1:
                    self.history.pop()

                self.history.append(line_number)
                self.history_index = len(self.history) - 1

            # 跳转
            self.log_widget.see(f"{line_number}.0")
            self.log_widget.mark_set("insert", f"{line_number}.0")

            # 高亮当前行
            if highlight:
                self._highlight_current_line(line_number)

            return True

        except Exception as e:
            print(f"跳转失败: {e}")
            return False

    def jump_to_entry(self, entry_index: int, reason: str = "") -> bool:
        """
        跳转到指定日志条目

        Args:
            entry_index: 条目索引 (在all_entries中的位置)
            reason: 跳转原因

        Returns:
            是否成功跳转
        """
        if not self.all_entries or entry_index >= len(self.all_entries):
            return False

        # 在Text控件中查找对应行 (简化实现,假设行号=索引+1)
        line_number = entry_index + 1
        return self.jump_to_line(line_number, reason)

    def mark_critical_logs(self, line_numbers: List[int], tag: str = "critical_log"):
        """
        标记关键日志 (AI分析的重点行)

        Args:
            line_numbers: 行号列表
            tag: 高亮标签名
        """
        for line_num in line_numbers:
            try:
                start = f"{line_num}.0"
                end = f"{line_num}.end"
                self.log_widget.tag_add(tag, start, end)
                self.marked_lines.add(line_num)
            except:
                pass

    def clear_marks(self):
        """清除所有标记"""
        for line_num in self.marked_lines:
            try:
                start = f"{line_num}.0"
                end = f"{line_num}.end"
                self.log_widget.tag_remove("critical_log", start, end)
                self.log_widget.tag_remove("ai_highlight", start, end)
                self.log_widget.tag_remove("related_log", start, end)
            except:
                pass
        self.marked_lines.clear()

    def add_problem_node(
        self,
        line_number: int,
        problem_type: str,
        description: str,
        ai_analysis: str = "",
        entry_index: int = None
    ) -> int:
        """
        添加问题节点 (用于问题链路追踪)

        Args:
            line_number: 日志行号
            problem_type: 问题类型 (崩溃/内存/网络等)
            description: 问题描述
            ai_analysis: AI分析结果
            entry_index: 条目索引 (可选)

        Returns:
            节点ID
        """
        # 获取日志条目
        entry = None
        if entry_index is not None and self.all_entries:
            entry = self.all_entries[entry_index]
        elif line_number > 0 and self.all_entries:
            entry = self.all_entries[min(line_number - 1, len(self.all_entries) - 1)]

        # 创建位置信息
        location = LogLocation(
            line_number=line_number,
            entry_index=entry_index or (line_number - 1),
            entry=entry,
            timestamp=getattr(entry, 'timestamp', ''),
            reason=f"{problem_type}: {description}"
        )

        # 创建节点
        node = NavigationNode(
            location=location,
            problem_type=problem_type,
            description=description,
            ai_analysis=ai_analysis
        )

        node_id = self.next_node_id
        self.problem_graph[node_id] = node
        self.next_node_id += 1

        return node_id

    def link_problems(self, from_node_id: int, to_node_id: int):
        """
        关联两个问题节点 (建立因果关系)

        Args:
            from_node_id: 源节点ID
            to_node_id: 目标节点ID
        """
        if from_node_id in self.problem_graph:
            self.problem_graph[from_node_id].related_nodes.append(to_node_id)

    def get_problem_chain(self, node_id: int) -> List[NavigationNode]:
        """
        获取问题链路 (从根因到最终问题)

        Args:
            node_id: 起始节点ID

        Returns:
            问题链路列表
        """
        chain = []
        visited = set()

        def dfs(nid):
            if nid in visited or nid not in self.problem_graph:
                return
            visited.add(nid)
            node = self.problem_graph[nid]
            chain.append(node)
            for related_id in node.related_nodes:
                dfs(related_id)

        dfs(node_id)
        return chain

    def navigate_problem_chain(self, node_id: int) -> List[int]:
        """
        导航问题链路 (依次跳转到每个问题节点)

        Args:
            node_id: 起始节点ID

        Returns:
            跳转的行号列表
        """
        chain = self.get_problem_chain(node_id)
        line_numbers = []

        for node in chain:
            line_num = node.location.line_number
            self.jump_to_line(line_num, reason=node.location.reason)
            self.mark_critical_logs([line_num], tag="ai_highlight")
            line_numbers.append(line_num)

        return line_numbers

    def go_back(self) -> bool:
        """
        后退到上一个位置

        Returns:
            是否成功后退
        """
        if self.history_index > 0:
            self.history_index -= 1
            line_num = self.history[self.history_index]
            self.jump_to_line(line_num, reason="后退", highlight=True)
            return True
        return False

    def go_forward(self) -> bool:
        """
        前进到下一个位置

        Returns:
            是否成功前进
        """
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            line_num = self.history[self.history_index]
            self.jump_to_line(line_num, reason="前进", highlight=True)
            return True
        return False

    def get_current_position(self) -> int:
        """
        获取当前光标位置 (行号)

        Returns:
            当前行号
        """
        try:
            return int(self.log_widget.index("insert").split('.')[0])
        except:
            return 1

    def find_logs_by_pattern(self, pattern: str, tag: str = "related_log") -> List[int]:
        """
        根据正则模式查找并标记日志

        Args:
            pattern: 正则表达式模式
            tag: 高亮标签

        Returns:
            匹配的行号列表
        """
        matched_lines = []
        try:
            # 在Text控件中搜索
            start_pos = "1.0"
            while True:
                pos = self.log_widget.search(pattern, start_pos, stopindex="end", regexp=True)
                if not pos:
                    break

                line_num = int(pos.split('.')[0])
                matched_lines.append(line_num)

                # 高亮该行
                self.mark_critical_logs([line_num], tag=tag)

                # 移动到下一行
                start_pos = f"{line_num + 1}.0"

        except Exception as e:
            print(f"搜索失败: {e}")

        return matched_lines

    def _highlight_current_line(self, line_number: int):
        """高亮当前行"""
        try:
            # 清除旧的current_position标签
            self.log_widget.tag_remove("current_position", "1.0", "end")

            # 添加新标签
            start = f"{line_number}.0"
            end = f"{line_number}.end"
            self.log_widget.tag_add("current_position", start, end)

            # 3秒后自动清除
            self.log_widget.after(3000, lambda: self.log_widget.tag_remove("current_position", start, end))
        except:
            pass

    def get_navigation_stats(self) -> Dict:
        """
        获取导航统计信息

        Returns:
            {
                'history_size': 历史记录数量,
                'marked_lines': 标记的行数,
                'problem_nodes': 问题节点数量,
                'current_position': 当前位置,
            }
        """
        return {
            'history_size': len(self.history),
            'marked_lines': len(self.marked_lines),
            'problem_nodes': len(self.problem_graph),
            'current_position': self.get_current_position(),
        }


# AI分析结果解析器
class AIAnalysisParser:
    """
    AI分析结果解析器

    从AI返回的文本中提取:
    1. 关键日志行号
    2. 问题类型
    3. 因果关系链路
    """

    @staticmethod
    def extract_line_numbers(ai_response: str) -> List[int]:
        """
        从AI响应中提取提到的行号

        例如: "第100行出现空指针" → [100]
        """
        pattern = r'第?(\d+)行|line\s*(\d+)|行号[:：]?\s*(\d+)'
        matches = re.findall(pattern, ai_response, re.IGNORECASE)

        line_numbers = []
        for match in matches:
            for group in match:
                if group:
                    line_numbers.append(int(group))

        return sorted(set(line_numbers))

    @staticmethod
    def extract_problem_type(ai_response: str) -> str:
        """
        从AI响应中提取问题类型

        Returns:
            问题类型字符串
        """
        keywords_map = {
            '崩溃': ['崩溃', 'crash', 'exception', 'fatal'],
            '内存': ['内存', 'memory', 'leak', 'oom'],
            '网络': ['网络', 'network', 'http', 'connection'],
            '性能': ['性能', 'performance', 'slow', 'anr'],
        }

        for ptype, keywords in keywords_map.items():
            for keyword in keywords:
                if re.search(keyword, ai_response, re.IGNORECASE):
                    return ptype

        return '未知'

    @staticmethod
    def build_problem_graph(ai_response: str, navigator: LogNavigator) -> int:
        """
        从AI分析结果构建问题图谱

        Args:
            ai_response: AI分析文本
            navigator: 日志导航器实例

        Returns:
            根节点ID
        """
        # 提取行号
        line_numbers = AIAnalysisParser.extract_line_numbers(ai_response)
        if not line_numbers:
            return -1

        # 提取问题类型
        problem_type = AIAnalysisParser.extract_problem_type(ai_response)

        # 创建主节点 (第一个提到的行号)
        root_id = navigator.add_problem_node(
            line_number=line_numbers[0],
            problem_type=problem_type,
            description="AI分析主要问题",
            ai_analysis=ai_response
        )

        # 创建关联节点
        for line_num in line_numbers[1:]:
            related_id = navigator.add_problem_node(
                line_number=line_num,
                problem_type="关联问题",
                description=f"与{problem_type}相关的日志",
                ai_analysis=""
            )
            navigator.link_problems(root_id, related_id)

        return root_id


# 便捷函数
def create_navigator(log_widget, all_entries: List = None) -> LogNavigator:
    """创建日志导航器"""
    return LogNavigator(log_widget, all_entries)
