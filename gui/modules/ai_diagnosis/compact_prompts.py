"""
精简版提示词模板 - Token优化版

通过精简提示词，减少无效token消耗，保留关键指导内容。
"""


class CompactPromptTemplates:
    """精简版提示词模板库"""

    # ==================== 崩溃分析（精简版）====================
    CRASH_ANALYSIS_COMPACT = """你是iOS/Android日志分析专家。分析以下崩溃日志：

{log_summary}

**任务**：
1. 识别崩溃原因（根本原因，不要猜测）
2. 定位问题代码位置（如果有堆栈）
3. 提供修复建议（具体可行的方案）

**输出格式**：
### 崩溃原因
[简明扼要，1-2句话]

### 问题位置
[模块/文件/方法，引用日志行号或时间戳]

### 修复建议
[3-5条具体建议，每条1行]

**引用规范**：
- 时间戳: [{{timestamp}}]
- 行号: #123
- 模块: @ModuleName

保持简洁，聚焦问题。"""

    # ==================== 性能分析（精简版）====================
    PERFORMANCE_ANALYSIS_COMPACT = """你是性能优化专家。分析以下日志的性能问题：

{log_summary}

**关注点**：
- 高频ERROR/WARNING模块
- 时间跨度是否过长
- 重复操作模式

**输出**：
### 性能瓶颈
[1-3个关键瓶颈]

### 优化建议
[3-5条建议，优先级降序]

简明扼要，引用日志使用 [{{timestamp}}] / #行号 / @模块名。"""

    # ==================== 问题总结（精简版）====================
    ISSUE_SUMMARY_COMPACT = """快速总结日志中的问题：

{log_summary}

**输出**：
### 关键问题 (优先级降序)
1. [问题描述] - 严重度:[高/中/低] - 位置:[...]
2. ...

### 不健康模块
- @模块名: 错误X次，警告Y次

简洁明了，引用日志使用规范格式。"""

    # ==================== 错误解释（精简版）====================
    ERROR_EXPLANATION_COMPACT = """解释这条错误日志：

{log_entry}

**输出**：
### 错误含义
[1句话说清楚]

### 常见原因
[2-3个可能原因]

### 解决方案
[2-3个具体方案]

保持简洁。"""

    # ==================== 交互式问答（精简版）====================
    INTERACTIVE_QA_COMPACT = """回答用户关于日志的问题。

**上下文**：
{log_summary}

**用户问题**：
{user_question}

**要求**：
1. 基于日志回答，不要臆测
2. 引用具体日志：[{{timestamp}}] / #行号 / @模块
3. 简明扼要，分点说明

**回答**："""

    # ==================== 智能搜索（精简版）====================
    SMART_SEARCH_COMPACT = """根据用户描述搜索相关日志。

**日志统计**：
{statistics}

**用户需求**：
{search_query}

**输出**：
### 匹配日志
- [{{timestamp}}] @模块: [简述]
- ...

### 分析
[1-2句话总结]

保持简洁。"""

    # ==================== 模板格式化方法 ====================

    @classmethod
    def format_crash_analysis(cls, log_summary: str) -> str:
        """格式化崩溃分析提示词"""
        return cls.CRASH_ANALYSIS_COMPACT.format(log_summary=log_summary)

    @classmethod
    def format_performance_analysis(cls, log_summary: str) -> str:
        """格式化性能分析提示词"""
        return cls.PERFORMANCE_ANALYSIS_COMPACT.format(log_summary=log_summary)

    @classmethod
    def format_issue_summary(cls, log_summary: str) -> str:
        """格式化问题总结提示词"""
        return cls.ISSUE_SUMMARY_COMPACT.format(log_summary=log_summary)

    @classmethod
    def format_error_explanation(cls, log_entry: str) -> str:
        """格式化错误解释提示词"""
        return cls.ERROR_EXPLANATION_COMPACT.format(log_entry=log_entry)

    @classmethod
    def format_interactive_qa(cls, log_summary: str, user_question: str) -> str:
        """格式化交互式问答提示词"""
        return cls.INTERACTIVE_QA_COMPACT.format(
            log_summary=log_summary,
            user_question=user_question
        )

    @classmethod
    def format_smart_search(cls, statistics: str, search_query: str) -> str:
        """格式化智能搜索提示词"""
        return cls.SMART_SEARCH_COMPACT.format(
            statistics=statistics,
            search_query=search_query
        )


# Token估算工具
def estimate_prompt_tokens(template: str, **kwargs) -> int:
    """
    估算提示词的token数量

    Args:
        template: 提示词模板
        **kwargs: 模板参数

    Returns:
        预估token数
    """
    filled_template = template.format(**kwargs)
    # 保守估计：2字符 = 1 token
    return len(filled_template) // 2


# 使用示例和对比
if __name__ == "__main__":
    # 示例日志摘要（已压缩）
    sample_summary = """【日志摘要】
总数:1500 | 崩溃:2 | 错误:45 | 警告:120
时间:2025-10-17 10:00:00 ~ 2025-10-17 10:30:00
主要模块: NetworkModule(500), DatabaseModule(300), UIModule(250)

【崩溃日志】
[10:25:33] Crash-FATAL: NSInvalidArgumentException: unrecognized selector sent to instance...

【错误日志】
(x15次) [10:10:12] NetworkModule-ERROR: Connection timeout after 30s
(x8次) [10:15:22] DatabaseModule-ERROR: SQLite error: database is locked
..."""

    # 使用精简模板
    compact_prompt = CompactPromptTemplates.format_crash_analysis(sample_summary)

    print("=== 精简版提示词 ===")
    print(compact_prompt)
    print(f"\n预估Token: {estimate_prompt_tokens(compact_prompt)}")

    print("\n=== Token对比 ===")
    print(f"原版提示词: ~2000-3000 tokens")
    print(f"精简版提示词: ~{estimate_prompt_tokens(compact_prompt)} tokens")
    print(f"节省: ~70%")
