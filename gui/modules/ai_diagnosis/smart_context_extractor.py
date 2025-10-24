#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能日志上下文提取器

根据问题类型智能提取相关日志上下文,提升AI诊断准确性。

核心功能:
1. 问题类型自动识别 (崩溃/性能/网络/内存/其他)
2. 智能上下文范围调整 (根据问题类型)
3. 关键日志优先级排序 (错误、警告、关键模块)
4. 跨模块关联分析 (同线程、时间窗口内)
5. Token优化压缩 (保留核心信息)
"""

from typing import List, Tuple, Dict, Optional, Set
from enum import Enum
from collections import defaultdict
import re


class ProblemType(Enum):
    """问题类型枚举"""
    CRASH = "崩溃"              # 崩溃相关
    MEMORY = "内存"             # 内存泄漏、OOM
    NETWORK = "网络"            # 网络请求、连接
    PERFORMANCE = "性能"        # 卡顿、ANR
    ERROR = "错误"              # 一般错误
    WARNING = "警告"            # 警告信息
    UNKNOWN = "未知"            # 未分类


class SmartContextExtractor:
    """
    智能日志上下文提取器

    使用示例:
        extractor = SmartContextExtractor(all_entries, indexer)
        context = extractor.extract_context(target_entry)

        # 获取优化后的上下文
        problem_type = context['problem_type']
        related_logs = context['related_logs']
        summary = context['summary']
    """

    def __init__(self, all_entries: List, indexer=None):
        """
        初始化智能提取器

        Args:
            all_entries: 所有日志条目 (LogEntry列表)
            indexer: 日志索引器实例 (可选,用于快速关联搜索)
        """
        self.all_entries = all_entries
        self.indexer = indexer

        # 问题类型检测规则
        self.problem_patterns = {
            ProblemType.CRASH: [
                r'Terminating app',
                r'Signal \d+',
                r'SIGSEGV',
                r'SIGABRT',
                r'Fatal Exception',
                r'crashed',
                r'abort',
            ],
            ProblemType.MEMORY: [
                r'Memory',
                r'OOM',
                r'Out of memory',
                r'malloc',
                r'leak',
                r'allocation failed',
            ],
            ProblemType.NETWORK: [
                r'HTTP',
                r'Network',
                r'socket',
                r'connection',
                r'timeout',
                r'DNS',
                r'API',
                r'Request',
                r'Response',
            ],
            ProblemType.PERFORMANCE: [
                r'ANR',
                r'slow',
                r'lag',
                r'performance',
                r'frame drop',
                r'stuck',
                r'hang',
            ],
        }

        # 上下文范围配置 (根据问题类型)
        self.context_config = {
            ProblemType.CRASH: {
                'before': 15,      # 崩溃前更多上下文
                'after': 5,
                'same_thread_priority': True,
                'include_all_errors': True,
            },
            ProblemType.MEMORY: {
                'before': 20,      # 内存问题需要长时间跟踪
                'after': 5,
                'filter_keywords': ['Memory', 'malloc', 'alloc'],
            },
            ProblemType.NETWORK: {
                'before': 10,
                'after': 10,       # 网络问题前后都重要
                'filter_keywords': ['HTTP', 'Request', 'Response'],
            },
            ProblemType.PERFORMANCE: {
                'before': 10,
                'after': 5,
                'filter_keywords': ['frame', 'time', 'duration'],
            },
            ProblemType.ERROR: {
                'before': 5,
                'after': 3,
            },
            ProblemType.WARNING: {
                'before': 3,
                'after': 2,
            },
            ProblemType.UNKNOWN: {
                'before': 5,
                'after': 3,
            },
        }

    def extract_context(self, target_entry, max_tokens: int = 8000) -> Dict:
        """
        智能提取日志上下文

        Args:
            target_entry: 目标日志条目 (LogEntry或str)
            max_tokens: 最大Token限制 (粗略估算: 1 token ≈ 0.75个汉字)

        Returns:
            {
                'problem_type': ProblemType,
                'target': 目标日志,
                'context_before': 前置上下文列表,
                'context_after': 后置上下文列表,
                'related_logs': 相关日志列表 (索引关联),
                'summary': 上下文摘要,
                'priority_score': 优先级评分,
            }
        """
        # 1. 识别问题类型
        problem_type = self._detect_problem_type(target_entry)

        # 2. 获取配置
        config = self.context_config.get(problem_type, self.context_config[ProblemType.UNKNOWN])

        # 3. 基础上下文提取
        target_idx = self._find_entry_index(target_entry)
        if target_idx is None:
            return self._create_empty_context(target_entry, problem_type)

        # 4. 智能范围调整
        before_count = config['before']
        after_count = config['after']

        # 基础上下文
        context_before = self.all_entries[max(0, target_idx - before_count):target_idx]
        context_after = self.all_entries[target_idx + 1:min(len(self.all_entries), target_idx + after_count + 1)]

        # 5. 优先级过滤与排序
        context_before = self._prioritize_logs(context_before, config)
        context_after = self._prioritize_logs(context_after, config)

        # 6. 利用索引查找关联日志
        related_logs = []
        if self.indexer and self.indexer.is_ready:
            related_logs = self._find_related_logs(target_entry, target_idx, config)

        # 7. Token优化
        context_data = {
            'problem_type': problem_type,
            'target': target_entry,
            'context_before': context_before,
            'context_after': context_after,
            'related_logs': related_logs,
        }

        optimized = self._optimize_for_tokens(context_data, max_tokens)

        # 8. 生成摘要
        optimized['summary'] = self._generate_summary(optimized)
        optimized['priority_score'] = self._calculate_priority(target_entry)

        return optimized

    def _detect_problem_type(self, entry) -> ProblemType:
        """检测问题类型"""
        content = self._get_entry_content(entry)
        level = self._get_entry_level(entry)

        # 检查是否崩溃
        for pattern in self.problem_patterns[ProblemType.CRASH]:
            if re.search(pattern, content, re.IGNORECASE):
                return ProblemType.CRASH

        # 检查其他类型
        for ptype, patterns in self.problem_patterns.items():
            if ptype == ProblemType.CRASH:
                continue
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    return ptype

        # 根据日志级别判断
        if level in ['ERROR', 'FATAL']:
            return ProblemType.ERROR
        elif level == 'WARNING':
            return ProblemType.WARNING

        return ProblemType.UNKNOWN

    def _prioritize_logs(self, logs: List, config: Dict) -> List:
        """
        对日志进行优先级排序

        优先级规则:
        1. ERROR/FATAL级别 > WARNING > INFO
        2. 包含关键词的日志优先
        3. 同线程日志优先 (如果配置启用)
        """
        if not logs:
            return logs

        scored_logs = []
        for log in logs:
            score = 0

            # 级别分数
            level = self._get_entry_level(log)
            if level in ['ERROR', 'FATAL']:
                score += 100
            elif level == 'WARNING':
                score += 50
            elif level == 'INFO':
                score += 10

            # 关键词分数
            content = self._get_entry_content(log)
            keywords = config.get('filter_keywords', [])
            for keyword in keywords:
                if re.search(keyword, content, re.IGNORECASE):
                    score += 20

            scored_logs.append((score, log))

        # 排序并返回
        scored_logs.sort(key=lambda x: x[0], reverse=True)
        return [log for _, log in scored_logs]

    def _find_related_logs(self, target_entry, target_idx: int, config: Dict) -> List:
        """
        利用索引查找相关日志

        策略:
        1. 提取目标日志的关键词
        2. 使用索引快速查找包含这些关键词的其他日志
        3. 按时间距离和相似度排序
        """
        if not self.indexer or not self.indexer.is_ready:
            return []

        # 提取关键词
        content = self._get_entry_content(target_entry)
        keywords = self._extract_keywords(content)

        if not keywords:
            return []

        # 使用索引搜索
        related_indices = set()
        for keyword in keywords[:5]:  # 限制关键词数量
            indices = self.indexer.search(keyword)
            related_indices.update(indices)

        # 排除目标本身和已在上下文中的日志
        context_range = set(range(max(0, target_idx - 50), min(len(self.all_entries), target_idx + 50)))
        related_indices -= context_range
        related_indices.discard(target_idx)

        # 转换为日志条目并排序
        related_logs = [self.all_entries[i] for i in sorted(related_indices)[:10]]

        return related_logs

    def _extract_keywords(self, content: str) -> List[str]:
        """
        从日志内容中提取关键词

        策略:
        1. 移除常用词 (the, is, a等)
        2. 提取大写开头的词 (可能是类名、常量)
        3. 提取包含数字的词 (错误代码、ID)
        """
        # 简单分词
        words = re.findall(r'\b\w+\b', content)

        # 过滤规则
        keywords = []
        stop_words = {'the', 'is', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of'}

        for word in words:
            if len(word) < 3:  # 太短
                continue
            if word.lower() in stop_words:  # 停用词
                continue
            if word[0].isupper() or re.search(r'\d', word):  # 大写或包含数字
                keywords.append(word)

        return keywords[:10]  # 返回前10个

    def _optimize_for_tokens(self, context_data: Dict, max_tokens: int) -> Dict:
        """
        优化上下文以控制Token数量

        粗略估算: 1 token ≈ 0.75个汉字 ≈ 1个英文词
        """
        # 粗略计算当前Token数
        def estimate_tokens(text):
            return len(text) // 3  # 粗略估算

        current_tokens = sum([
            estimate_tokens(self._get_entry_content(context_data['target'])),
            sum(estimate_tokens(self._get_entry_content(e)) for e in context_data.get('context_before', [])),
            sum(estimate_tokens(self._get_entry_content(e)) for e in context_data.get('context_after', [])),
            sum(estimate_tokens(self._get_entry_content(e)) for e in context_data.get('related_logs', [])),
        ])

        # 如果超出限制,逐步减少
        if current_tokens > max_tokens:
            # 优先减少related_logs
            context_data['related_logs'] = context_data['related_logs'][:5]

            # 再减少context
            context_data['context_before'] = context_data['context_before'][-10:]
            context_data['context_after'] = context_data['context_after'][:5]

        return context_data

    def _generate_summary(self, context_data: Dict) -> str:
        """生成上下文摘要"""
        problem_type = context_data['problem_type']
        before_count = len(context_data.get('context_before', []))
        after_count = len(context_data.get('context_after', []))
        related_count = len(context_data.get('related_logs', []))

        summary = f"问题类型: {problem_type.value}\n"
        summary += f"上下文: 前{before_count}条 | 后{after_count}条\n"
        if related_count > 0:
            summary += f"关联日志: {related_count}条 (索引搜索)\n"

        return summary

    def _calculate_priority(self, entry) -> int:
        """计算日志优先级分数 (0-100)"""
        score = 0

        level = self._get_entry_level(entry)
        if level in ['ERROR', 'FATAL']:
            score += 80
        elif level == 'WARNING':
            score += 50
        elif level == 'INFO':
            score += 20

        # 检查是否包含关键词
        content = self._get_entry_content(entry)
        if re.search(r'crash|exception|fatal', content, re.IGNORECASE):
            score += 20

        return min(100, score)

    # 辅助方法
    def _get_entry_content(self, entry) -> str:
        """获取日志内容"""
        if isinstance(entry, str):
            return entry
        return getattr(entry, 'content', str(entry))

    def _get_entry_level(self, entry) -> str:
        """获取日志级别"""
        if isinstance(entry, str):
            # 尝试从字符串中提取
            match = re.search(r'\[(ERROR|WARNING|INFO|DEBUG|FATAL)\]', entry)
            return match.group(1) if match else 'INFO'
        return getattr(entry, 'level', 'INFO')

    def _find_entry_index(self, target_entry) -> Optional[int]:
        """查找日志在列表中的索引"""
        try:
            return self.all_entries.index(target_entry)
        except ValueError:
            # 如果是字符串,尝试内容匹配
            if isinstance(target_entry, str):
                for i, entry in enumerate(self.all_entries):
                    if target_entry in self._get_entry_content(entry):
                        return i
            return None

    def _create_empty_context(self, target_entry, problem_type: ProblemType) -> Dict:
        """创建空上下文"""
        return {
            'problem_type': problem_type,
            'target': target_entry,
            'context_before': [],
            'context_after': [],
            'related_logs': [],
            'summary': f"问题类型: {problem_type.value}\n无可用上下文",
            'priority_score': 0,
        }


# 便捷函数
def extract_smart_context(all_entries: List, target_entry, indexer=None, max_tokens: int = 8000) -> Dict:
    """
    便捷函数: 智能提取日志上下文

    Args:
        all_entries: 所有日志条目
        target_entry: 目标日志
        indexer: 索引器 (可选)
        max_tokens: 最大Token限制

    Returns:
        上下文字典
    """
    extractor = SmartContextExtractor(all_entries, indexer)
    return extractor.extract_context(target_entry, max_tokens)
