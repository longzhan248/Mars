"""
日志预处理模块

将原始日志转换为AI可理解的格式，提供：
- 崩溃日志提取和上下文获取
- 错误模式识别和聚类
- 时间线构建
- 日志摘要（智能压缩，控制Token数量）
- 隐私信息过滤
"""

import re
from collections import Counter
from dataclasses import dataclass
from typing import Dict, List, Optional

# 导入LogEntry数据模型
try:
    from data_models import LogEntry
except ImportError:
    try:
        from modules.data_models import LogEntry
    except ImportError:
        from gui.modules.data_models import LogEntry


@dataclass
class CrashInfo:
    """崩溃信息结构"""
    crash_entry: LogEntry
    context_before: List[LogEntry]
    context_after: List[LogEntry]
    crash_time: str
    module: str


@dataclass
class ErrorPattern:
    """错误模式结构"""
    signature: str  # 错误签名（前50字符）
    count: int
    first_occurrence: str
    last_occurrence: str
    sample_logs: List[LogEntry]


class PrivacyFilter:
    """隐私信息过滤器"""

    # 内置过滤规则（正则表达式, 替换文本）
    PATTERNS = [
        # Token和密钥
        (r'token["\s:=]+([a-zA-Z0-9\-_]{20,})', 'TOKEN_***'),
        (r'api[_\s]?key["\s:=]+([a-zA-Z0-9\-_]{20,})', 'APIKEY_***'),
        (r'secret["\s:=]+([a-zA-Z0-9\-_]{20,})', 'SECRET_***'),
        (r'password["\s:=]+([^\s\'"]+)', 'PASSWORD_***'),
        (r'pwd["\s:=]+([^\s\'"]+)', 'PWD_***'),

        # 用户标识
        (r'user[_\s]?id["\s:=]+(\d+)', 'USER_***'),
        (r'uid["\s:=]+(\d+)', 'UID_***'),
        (r'device[_\s]?id["\s:=]+([a-zA-Z0-9\-]+)', 'DEVICE_***'),
        (r'openid["\s:=]+([a-zA-Z0-9\-_]+)', 'OPENID_***'),

        # 联系信息
        (r'\d{11}', 'PHONE_***'),  # 手机号（11位数字）
        (r'[\w\.-]+@[\w\.-]+\.\w+', 'EMAIL_***'),  # 邮箱

        # 网络信息
        (r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', 'IP_***'),  # IP地址

        # 身份证号
        (r'\b\d{17}[\dXx]\b', 'IDCARD_***'),
    ]

    def __init__(self, enabled: bool = True):
        """
        初始化过滤器

        Args:
            enabled: 是否启用过滤
        """
        self.enabled = enabled
        self.compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE), replacement)
            for pattern, replacement in self.PATTERNS
        ]

    def filter(self, text: str) -> str:
        """过滤文本中的敏感信息"""
        if not self.enabled:
            return text

        filtered_text = text
        for pattern, replacement in self.compiled_patterns:
            filtered_text = pattern.sub(replacement, filtered_text)

        return filtered_text

    def filter_log_entries(self, entries: List[LogEntry]) -> List[LogEntry]:
        """批量过滤日志条目"""
        if not self.enabled:
            return entries

        filtered = []
        for entry in entries:
            filtered_entry = LogEntry(
                timestamp=entry.timestamp,
                level=entry.level,
                module=entry.module,
                content=self.filter(entry.content)
            )
            filtered.append(filtered_entry)

        return filtered


class LogPreprocessor:
    """日志预处理器"""

    def __init__(self, privacy_filter: Optional[PrivacyFilter] = None):
        """初始化预处理器"""
        self.privacy_filter = privacy_filter or PrivacyFilter(enabled=True)

    def extract_crash_logs(self, entries: List[LogEntry],
                          before_lines: int = 10,
                          after_lines: int = 5) -> List[CrashInfo]:
        """提取崩溃日志及上下文"""
        crashes = []

        for i, entry in enumerate(entries):
            if self._is_crash_log(entry):
                start_idx = max(0, i - before_lines)
                end_idx = min(len(entries), i + after_lines + 1)

                crash_info = CrashInfo(
                    crash_entry=entry,
                    context_before=entries[start_idx:i],
                    context_after=entries[i+1:end_idx],
                    crash_time=entry.timestamp,
                    module=entry.module
                )
                crashes.append(crash_info)

        return crashes

    def _is_crash_log(self, entry: LogEntry) -> bool:
        """判断是否为崩溃日志"""
        if entry.module == "Crash":
            return True

        crash_keywords = [
            'crash', 'exception', 'signal', 'segmentation fault',
            '崩溃', '异常', 'fatal error', 'abort', 'terminated'
        ]

        content_lower = entry.content.lower()
        return any(keyword in content_lower for keyword in crash_keywords)

    def extract_error_patterns(self, entries: List[LogEntry],
                              top_n: int = 10) -> List[ErrorPattern]:
        """识别高频错误模式"""
        error_logs = [e for e in entries if e.level == "ERROR"]

        if not error_logs:
            return []

        signatures = {}
        for log in error_logs:
            signature = log.content[:50].strip()

            if signature not in signatures:
                signatures[signature] = {
                    'count': 0,
                    'first': log.timestamp,
                    'last': log.timestamp,
                    'samples': []
                }

            signatures[signature]['count'] += 1
            signatures[signature]['last'] = log.timestamp

            if len(signatures[signature]['samples']) < 3:
                signatures[signature]['samples'].append(log)

        patterns = []
        for sig, data in signatures.items():
            pattern = ErrorPattern(
                signature=sig,
                count=data['count'],
                first_occurrence=data['first'],
                last_occurrence=data['last'],
                sample_logs=data['samples']
            )
            patterns.append(pattern)

        patterns.sort(key=lambda p: p.count, reverse=True)
        return patterns[:top_n]

    def summarize_logs(self, entries: List[LogEntry],
                      max_tokens: int = 10000) -> str:
        """日志摘要（智能压缩）"""
        if not entries:
            return "无日志数据"

        error_logs = [e for e in entries if e.level == "ERROR"]
        crash_logs = [e for e in entries if e.module == "Crash"]
        warning_logs = [e for e in entries if e.level == "WARNING"]
        info_logs = [e for e in entries if e.level == "INFO"]
        debug_logs = [e for e in entries if e.level == "DEBUG"]

        char_budget = max_tokens * 4
        summary_parts = []

        summary_parts.append("=== 错误和崩溃日志 ===")
        for log in crash_logs + error_logs:
            summary_parts.append(self._format_log_entry(log))

        if warning_logs:
            sample_size = min(len(warning_logs), 20)
            step = max(1, len(warning_logs) // sample_size)
            sampled_warnings = warning_logs[::step]

            summary_parts.append("\n=== 警告日志（采样） ===")
            for log in sampled_warnings:
                summary_parts.append(self._format_log_entry(log))

        other_logs = info_logs + debug_logs
        if other_logs:
            sample_size = min(len(other_logs), 30)
            step = max(1, len(other_logs) // sample_size)
            sampled_others = other_logs[::step]

            summary_parts.append("\n=== 其他日志（稀疏采样） ===")
            for log in sampled_others:
                summary_parts.append(self._format_log_entry(log))

        summary = '\n'.join(summary_parts)

        if len(summary) > char_budget:
            summary = summary[:char_budget] + "\n...\n[日志已截断以控制长度]"

        return self.privacy_filter.filter(summary)

    def _format_log_entry(self, entry: LogEntry) -> str:
        """格式化单条日志"""
        return f"[{entry.timestamp}] {entry.level} {entry.module}: {entry.content[:200]}"

    def get_statistics(self, entries: List[LogEntry]) -> Dict:
        """获取日志统计信息"""
        if not entries:
            return {
                'total': 0,
                'crashes': 0,
                'errors': 0,
                'warnings': 0,
                'time_range': 'N/A',
                'modules': {},
                'levels': {}
            }

        crashes = sum(1 for e in entries if self._is_crash_log(e))
        errors = sum(1 for e in entries if e.level == "ERROR")
        warnings = sum(1 for e in entries if e.level == "WARNING")

        module_counter = Counter(e.module for e in entries)
        level_counter = Counter(e.level for e in entries)

        time_range = f"{entries[0].timestamp} ~ {entries[-1].timestamp}"

        return {
            'total': len(entries),
            'crashes': crashes,
            'errors': errors,
            'warnings': warnings,
            'time_range': time_range,
            'modules': dict(module_counter.most_common(10)),
            'levels': dict(level_counter)
        }

    # ========== Mars模块感知功能（新增） ==========

    def extract_module_specific_logs(self, entries: List[LogEntry],
                                     module: str) -> List[LogEntry]:
        """
        提取特定模块的日志（支持Mars模块分组）

        Args:
            entries: 日志条目列表
            module: 模块名称

        Returns:
            指定模块的日志列表
        """
        return [e for e in entries if e.module == module]

    def get_module_health(self, entries: List[LogEntry]) -> Dict[str, Dict]:
        """
        分析各模块健康状况（Mars特有）

        计算每个模块的健康分数，基于崩溃、错误、警告数量。

        Returns:
            模块健康统计字典:
            {
                'ModuleName': {
                    'total': 100,           # 总日志数
                    'errors': 5,            # 错误数
                    'warnings': 10,         # 警告数
                    'crashes': 0,           # 崩溃数
                    'health_score': 0.85    # 健康分数(0-1)
                }
            }
        """
        module_stats = {}

        # 获取所有模块
        modules = set(e.module for e in entries)

        for module in modules:
            module_logs = self.extract_module_specific_logs(entries, module)

            error_count = sum(1 for e in module_logs if e.level == "ERROR")
            warning_count = sum(1 for e in module_logs if e.level == "WARNING")
            crash_count = sum(1 for e in module_logs if self._is_crash_log(e))

            # 计算健康分数 (0-1)
            total = len(module_logs)
            if total == 0:
                health_score = 1.0
            else:
                # 崩溃权重最高(10)，错误次之(5)，警告最低(1)
                penalty = (crash_count * 10 + error_count * 5 + warning_count * 1) / total
                health_score = max(0, 1 - penalty / 10)

            module_stats[module] = {
                'total': total,
                'errors': error_count,
                'warnings': warning_count,
                'crashes': crash_count,
                'health_score': round(health_score, 2)
            }

        return module_stats

    def get_unhealthy_modules(self, entries: List[LogEntry],
                             threshold: float = 0.7) -> List[str]:
        """
        获取不健康的模块列表

        Args:
            entries: 日志条目列表
            threshold: 健康分数阈值，低于此值视为不健康

        Returns:
            不健康模块名称列表，按健康分数升序排列（最不健康的在前）
        """
        health_stats = self.get_module_health(entries)

        unhealthy = [
            (module, stats['health_score'])
            for module, stats in health_stats.items()
            if stats['health_score'] < threshold
        ]

        # 按健康分数升序排序（最不健康的在前）
        unhealthy.sort(key=lambda x: x[1])

        return [module for module, score in unhealthy]
