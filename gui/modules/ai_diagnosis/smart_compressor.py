"""
智能日志压缩器 - Token优化版

通过智能压缩算法，将日志内容压缩到AI模型可接受的大小，同时保留关键信息。
目标：将任意大小的日志压缩到2000-4000 tokens以内。
"""

import re
from typing import List, Dict, Tuple
from collections import Counter, defaultdict
from dataclasses import dataclass

try:
    from data_models import LogEntry
except ImportError:
    try:
        from modules.data_models import LogEntry
    except ImportError:
        from gui.modules.data_models import LogEntry


@dataclass
class CompressedLog:
    """压缩后的日志结构"""
    summary: str  # 摘要文本
    estimated_tokens: int  # 预估token数
    compression_ratio: float  # 压缩比
    statistics: Dict  # 统计信息


class SmartLogCompressor:
    """智能日志压缩器"""

    # Token预估: 1 token ≈ 4个英文字符 ≈ 1.5个中文字符
    # 保守估计: 1 token ≈ 2个字符（混合中英文）
    CHARS_PER_TOKEN = 2

    def __init__(self, max_tokens: int = 3000):
        """
        初始化压缩器

        Args:
            max_tokens: 目标最大token数（默认3000，留有余地）
        """
        self.max_tokens = max_tokens
        self.max_chars = max_tokens * self.CHARS_PER_TOKEN

    def compress(self, entries: List[LogEntry]) -> CompressedLog:
        """
        智能压缩日志

        策略：
        1. 保留所有崩溃日志（完整）
        2. 保留所有错误日志（压缩内容）
        3. 采样警告日志（保留代表性样本）
        4. 极度稀疏采样INFO/DEBUG（只保留统计）
        5. 去重复内容
        6. 截断过长的单行日志
        """
        if not entries:
            return CompressedLog(
                summary="无日志数据",
                estimated_tokens=5,
                compression_ratio=1.0,
                statistics={}
            )

        # 第一步：分类日志
        categorized = self._categorize_logs(entries)

        # 第二步：获取统计信息（用于摘要头部）
        stats = self._compute_statistics(entries, categorized)

        # 第三步：构建压缩摘要
        summary_parts = []

        # 添加统计摘要头部（极简）
        summary_parts.append(self._format_statistics_header(stats))

        # 添加崩溃日志（完整，最高优先级）
        if categorized['crashes']:
            summary_parts.append("\n【崩溃日志】")
            for log in categorized['crashes'][:5]:  # 最多5条崩溃
                summary_parts.append(self._format_log_compact(log, full=True))

        # 添加错误日志（压缩，高优先级）
        if categorized['errors']:
            summary_parts.append("\n【错误日志】")
            # 去重+采样
            unique_errors = self._deduplicate_logs(categorized['errors'], max_samples=10)
            for log, count in unique_errors:
                # 如果重复多次，添加计数前缀
                if count > 1:
                    formatted = self._format_log_compact(log, full=False)
                    summary_parts.append(f"(x{count}次) {formatted}")
                else:
                    summary_parts.append(self._format_log_compact(log, full=False))

        # 添加警告日志（稀疏采样）
        if categorized['warnings']:
            summary_parts.append("\n【警告日志(采样)】")
            sampled = self._sample_logs(categorized['warnings'], max_samples=5)
            for log in sampled:
                summary_parts.append(self._format_log_compact(log, full=False))

        # INFO/DEBUG 只保留统计，不输出具体日志
        # （已在统计头部包含）

        # 合并摘要
        summary = '\n'.join(summary_parts)

        # 第四步：检查长度，必要时进一步截断
        if len(summary) > self.max_chars:
            summary = self._truncate_summary(summary, self.max_chars)

        # 计算压缩比和预估token
        original_size = sum(len(e.content) for e in entries)
        compressed_size = len(summary)
        compression_ratio = compressed_size / original_size if original_size > 0 else 1.0
        estimated_tokens = compressed_size // self.CHARS_PER_TOKEN

        return CompressedLog(
            summary=summary,
            estimated_tokens=estimated_tokens,
            compression_ratio=compression_ratio,
            statistics=stats
        )

    def _categorize_logs(self, entries: List[LogEntry]) -> Dict[str, List[LogEntry]]:
        """分类日志"""
        categorized = {
            'crashes': [],
            'errors': [],
            'warnings': [],
            'others': []
        }

        for entry in entries:
            if entry.module == "Crash" or "crash" in entry.content.lower():
                categorized['crashes'].append(entry)
            elif entry.level == "ERROR":
                categorized['errors'].append(entry)
            elif entry.level == "WARNING":
                categorized['warnings'].append(entry)
            else:
                categorized['others'].append(entry)

        return categorized

    def _compute_statistics(self, entries: List[LogEntry],
                           categorized: Dict[str, List[LogEntry]]) -> Dict:
        """计算统计信息"""
        # 模块统计
        module_counter = Counter(e.module for e in entries)
        top_modules = module_counter.most_common(5)

        # 级别统计
        level_counter = Counter(e.level for e in entries)

        # 时间范围
        time_range = f"{entries[0].timestamp} ~ {entries[-1].timestamp}" if len(entries) > 1 else entries[0].timestamp

        return {
            'total': len(entries),
            'crashes': len(categorized['crashes']),
            'errors': len(categorized['errors']),
            'warnings': len(categorized['warnings']),
            'others': len(categorized['others']),
            'time_range': time_range,
            'top_modules': top_modules,
            'levels': dict(level_counter)
        }

    def _format_statistics_header(self, stats: Dict) -> str:
        """格式化统计头部（极简）"""
        lines = [
            "【日志摘要】",
            f"总数:{stats['total']} | 崩溃:{stats['crashes']} | 错误:{stats['errors']} | 警告:{stats['warnings']}",
            f"时间:{stats['time_range']}"
        ]

        # 只显示前3个模块
        if stats['top_modules']:
            top3 = ', '.join([f"{m}({c})" for m, c in stats['top_modules'][:3]])
            lines.append(f"主要模块: {top3}")

        return '\n'.join(lines)

    def _format_log_compact(self, entry: LogEntry, full: bool = False) -> str:
        """
        格式化单条日志（紧凑格式）

        Args:
            entry: 日志条目
            full: 是否输出完整内容
        """
        # 时间戳简化：只保留时分秒
        timestamp = entry.timestamp.split()[-1] if entry.timestamp else "N/A"

        # 内容截断
        max_len = 300 if full else 150
        content = entry.content[:max_len]
        if len(entry.content) > max_len:
            content += "..."

        # 极简格式: [时间] 模块-级别: 内容
        return f"[{timestamp}] {entry.module}-{entry.level}: {content}"

    def _deduplicate_logs(self, logs: List[LogEntry], max_samples: int = 10) -> List:
        """
        去重日志（基于内容签名）

        相同错误只保留一个样本，但记录出现次数
        返回: List of (log, count) tuples
        """
        # 使用前50个字符作为签名
        signature_map = {}

        for log in logs:
            signature = log.content[:50].strip()
            if signature not in signature_map:
                signature_map[signature] = {
                    'log': log,
                    'count': 0
                }
            signature_map[signature]['count'] += 1

        # 按出现次数排序，保留最高频的
        sorted_items = sorted(signature_map.items(),
                             key=lambda x: x[1]['count'],
                             reverse=True)

        # 返回(log, count)元组列表
        result = []
        for i, (sig, data) in enumerate(sorted_items[:max_samples]):
            result.append((data['log'], data['count']))

        return result

    def _sample_logs(self, logs: List[LogEntry], max_samples: int = 5) -> List[LogEntry]:
        """均匀采样日志"""
        if len(logs) <= max_samples:
            return logs

        step = len(logs) // max_samples
        return logs[::step][:max_samples]

    def _truncate_summary(self, summary: str, max_chars: int) -> str:
        """截断摘要到指定长度"""
        if len(summary) <= max_chars:
            return summary

        truncated = summary[:max_chars]

        # 尝试在最后一个换行处截断，保持完整性
        last_newline = truncated.rfind('\n')
        if last_newline > max_chars * 0.8:  # 至少保留80%
            truncated = truncated[:last_newline]

        return truncated + "\n...\n[摘要已截断以控制长度]"


class FocusedCompressor(SmartLogCompressor):
    """
    聚焦式压缩器

    针对特定分析任务进行定向压缩，更精准地控制token使用
    """

    def compress_for_crash_analysis(self, entries: List[LogEntry]) -> CompressedLog:
        """
        为崩溃分析压缩日志

        策略：
        - 保留所有崩溃日志（完整）
        - 保留崩溃前后的上下文（各10条）
        - 忽略其他日志，只保留统计
        """
        if not entries:
            return self.compress(entries)

        # 找到所有崩溃日志
        crash_indices = []
        for i, entry in enumerate(entries):
            if entry.module == "Crash" or "crash" in entry.content.lower():
                crash_indices.append(i)

        if not crash_indices:
            return CompressedLog(
                summary="未发现崩溃日志",
                estimated_tokens=10,
                compression_ratio=1.0,
                statistics={'crashes': 0}
            )

        # 收集崩溃及其上下文
        relevant_logs = []
        for crash_idx in crash_indices[:3]:  # 最多分析3个崩溃
            start = max(0, crash_idx - 10)
            end = min(len(entries), crash_idx + 11)
            relevant_logs.extend(entries[start:end])

        # 去重
        seen = set()
        unique_logs = []
        for log in relevant_logs:
            key = (log.timestamp, log.content[:50])
            if key not in seen:
                seen.add(key)
                unique_logs.append(log)

        # 使用标准压缩
        return self.compress(unique_logs)

    def compress_for_performance_analysis(self, entries: List[LogEntry]) -> CompressedLog:
        """
        为性能分析压缩日志

        策略：
        - 关注WARNING和ERROR
        - 寻找高频模块
        - 保留时间跨度信息
        """
        # 过滤出WARNING和ERROR
        important_logs = [e for e in entries if e.level in ["ERROR", "WARNING"]]

        # 如果太多，进一步采样
        if len(important_logs) > 50:
            important_logs = self._sample_logs(important_logs, 50)

        return self.compress(important_logs)

    def compress_for_module_analysis(self, entries: List[LogEntry], module: str) -> CompressedLog:
        """
        为特定模块分析压缩日志

        Args:
            entries: 日志条目
            module: 目标模块名
        """
        # 只保留目标模块的日志
        module_logs = [e for e in entries if e.module == module]

        if not module_logs:
            return CompressedLog(
                summary=f"模块 {module} 无日志",
                estimated_tokens=10,
                compression_ratio=1.0,
                statistics={}
            )

        return self.compress(module_logs)


# 工具函数：估算token数
def estimate_tokens(text: str) -> int:
    """
    估算文本的token数量

    Args:
        text: 文本内容

    Returns:
        预估的token数量
    """
    # 简单估算：2个字符 ≈ 1 token（保守估计）
    return len(text) // 2


def format_token_budget(used_tokens: int, max_tokens: int) -> str:
    """
    格式化token预算显示

    Args:
        used_tokens: 已使用token数
        max_tokens: 最大token数

    Returns:
        格式化的字符串，如 "2500/10000 (25%)"
    """
    percentage = (used_tokens / max_tokens * 100) if max_tokens > 0 else 0
    return f"{used_tokens}/{max_tokens} ({percentage:.1f}%)"
