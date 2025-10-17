"""
提示词模板库

管理各类分析场景的AI提示词模板，包括：
- 崩溃分析
- 性能诊断
- 问题总结
- 交互式问答
- 错误解释
- 相关日志查找
"""

from typing import Dict, Any


class PromptTemplates:
    """提示词模板管理类"""

    # ==================== 崩溃分析模板 ====================
    CRASH_ANALYSIS_PROMPT = """你是一位拥有10年以上经验的移动应用开发专家，精通iOS和Android平台的崩溃分析。

## 任务
分析以下应用崩溃日志，提供详细的诊断报告。

## 崩溃信息
**时间**: {crash_time}
**模块**: {module_name}
**级别**: {log_level}

**崩溃堆栈**:
```
{crash_stack}
```

**崩溃前上下文日志（前10条）**:
```
{context_before}
```

**崩溃后日志（后5条）**:
```
{context_after}
```

## 要求
请按以下结构分析，用中文回答：

### 1. 问题概述（1-2句话）
简洁描述崩溃的直接原因。

### 2. 技术分析
- **崩溃类型**: (如: NullPointerException, EXC_BAD_ACCESS等)
- **崩溃位置**: (具体的类名和方法)
- **触发条件**: (什么操作或状态导致崩溃)

### 3. 根因分析
从崩溃堆栈和上下文日志推断：
- 代码逻辑问题？
- 资源状态异常？(如网络、数据库、文件等)
- 并发竞争条件？
- 外部依赖问题？

### 4. 影响范围评估
- 严重程度: [低/中/高/严重]
- 影响用户: [少数/部分/大量]
- 复现概率: [偶发/频繁/必现]

### 5. 解决方案
提供至少2种可行方案，包括：
- 短期临时方案（快速止血）
- 长期根治方案（彻底解决）
- 示例代码（如适用）

### 6. 预防措施
建议如何避免类似问题再次发生。

## 重要提示
**在分析中引用日志时，请使用以下可点击的格式**：
- 时间戳格式：[2025-09-21 13:09:49] - 用户可以点击跳转到对应日志
- 行号格式：#123 - 用户可以点击跳转到第123行日志
- 模块名格式：@NetworkModule - 用户可以点击跳转到该模块的第一条日志

例如："根据 [2025-09-21 13:09:49] 和 #123 行的日志，@NetworkModule 模块出现了异常..."

## 输出格式
使用Markdown格式，结构清晰，重点突出。
"""

    # ==================== 性能分析模板 ====================
    PERFORMANCE_ANALYSIS_PROMPT = """你是性能优化专家，擅长移动应用性能诊断。

请分析以下性能问题：

## 慢速操作统计
{slow_operations}

## 性能相关日志（最近100条）
```
{perf_logs}
```

## 要求
请分析：

### 1. 主要性能瓶颈
识别最严重的性能问题（按影响程度排序）：
- 网络请求慢？
- 数据库查询慢？
- UI渲染卡顿？
- 内存占用过高？
- CPU使用率高？

### 2. 慢速操作详细分析
对于每个慢速操作：
- 操作位置（模块/方法）
- 耗时多久
- 可能的原因
- 优化方向

### 3. 优化建议（按优先级排序）
- P0（必须立即优化）
- P1（应该尽快优化）
- P2（可以考虑优化）

每个建议包括：
- 问题描述
- 预期收益
- 实施难度
- 具体方案

### 4. 监控建议
建议添加哪些性能监控指标。

## 重要提示
**在分析中引用日志时，请使用以下可点击的格式**：
- 时间戳格式：[2025-09-21 13:09:49] - 用户可以点击跳转到对应日志
- 行号格式：#123 - 用户可以点击跳转到第123行日志
- 模块名格式：@NetworkModule - 用户可以点击跳转到该模块的第一条日志

用中文回答，Markdown格式。
"""

    # ==================== 问题总结模板 ====================
    ISSUE_SUMMARY_PROMPT = """你是日志分析专家，擅长从大量日志中提炼关键问题。

请根据以下统计数据生成问题总结报告：

## 日志统计
- 总日志数: {total}
- 时间范围: {time_range}
- 崩溃数: {crashes}
- 错误数: {errors}
- 警告数: {warnings}

## 主要模块活跃度
{module_activity}

## 高频错误信息（Top 10）
{top_errors}

## 崩溃详情
{crash_details}

## 要求
请生成一份简洁的问题总结报告：

### 1. 整体健康度评估
给出评级：[良好/一般/严重]
并说明理由（基于崩溃率、错误率等）

### 2. 需要优先处理的问题（Top 3）
按严重程度和影响范围排序：
- 问题描述
- 影响范围
- 建议优先级

### 3. 潜在风险点
可能隐藏的问题（如高频警告、异常模式等）

### 4. 行动建议
具体的下一步行动：
- 立即处理：...
- 本周解决：...
- 持续观察：...

## 重要提示
**在分析中引用日志时，请使用以下可点击的格式**：
- 时间戳格式：[2025-09-21 13:09:49] - 用户可以点击跳转到对应日志
- 行号格式：#123 - 用户可以点击跳转到第123行日志
- 模块名格式：@NetworkModule - 用户可以点击跳转到该模块的第一条日志

用中文回答，Markdown格式，重点突出。
"""

    # ==================== 交互式问答模板 ====================
    INTERACTIVE_QA_PROMPT = """你是Mars日志分析助手，专注于帮助开发者理解和诊断应用日志。

## 当前日志上下文
- 文件名: {filename}
- 日志总数: {total_logs}
- 当前显示: {current_logs}条
- 时间范围: {time_range}
- 主要模块: {main_modules}

## 统计信息
- 崩溃数: {crash_count}
- 错误数: {error_count}
- 警告数: {warning_count}

## 日志摘要（根据问题筛选的相关日志）
```
{relevant_logs}
```

## 用户问题
{user_question}

## 回答要求
1. 直接回答用户问题，简洁明了
2. 引用具体的日志作为证据，使用可点击的格式：
   - 时间戳：[2025-10-15 15:23:45]
   - 行号：#123
   - 模块：@NetworkModule
3. 如果日志信息不足，明确说明需要什么额外信息
4. 提供可操作的建议
5. 使用中文回答

请回答：
"""

    # ==================== 错误解释模板 ====================
    ERROR_EXPLANATION_PROMPT = """你是移动应用开发专家，擅长用通俗易懂的语言解释技术问题。

以下是一条错误日志：

```
{error_log}
```

请详细解释：

### 1. 这个错误是什么意思（通俗易懂）
用非技术人员也能理解的语言解释这个错误。

### 2. 通常是什么原因导致的
列举常见场景（至少3个）：
- 场景1: ...
- 场景2: ...
- 场景3: ...

### 3. 如何定位具体原因
提供排查步骤：
1. 第一步：...
2. 第二步：...
3. 第三步：...

### 4. 如何修复
提供具体的修复方案：
- **快速修复**：...
- **彻底修复**：...
- **代码示例**：
```
// 示例代码
```

### 5. 如何预防
提供最佳实践建议。

用中文回答，适合初级开发者理解，避免过于技术化的术语。
"""

    # ==================== 相关日志查找模板 ====================
    RELATED_LOGS_PROMPT = """你是日志分析专家，擅长从海量日志中找出相关联的日志条目。

用户选中了这条日志：

```
{selected_log}
```

当前日志文件信息：
- 总日志数: {total_logs}
- 时间范围: {time_range}

## 任务
帮助用户找到与这条日志相关的其他日志。

## 要求

### 1. 分析这条日志涉及的关键信息
- 模块名称
- 关键操作
- 相关变量/参数
- 时间点

### 2. 建议搜索关键词
提供3-5个搜索关键词，帮助用户在日志中查找相关内容：
- 关键词1: xxx（解释为什么搜索这个）
- 关键词2: xxx（解释为什么搜索这个）
- 关键词3: xxx（解释为什么搜索这个）

### 3. 推荐时间范围
如果这是崩溃或错误日志，建议查看前后多少秒的日志：
- 建议时间范围: 前xx秒 ~ 后xx秒
- 理由: ...

### 4. 推荐日志级别
建议重点查看哪些级别的日志：
- [x] ERROR
- [x] WARNING
- [ ] INFO
- [ ] DEBUG

### 5. 关联模块
可能相关的其他模块：
- 模块1: ...（为什么相关）
- 模块2: ...（为什么相关）

用中文回答，实用性优先。
"""

    # ==================== 智能搜索模板 ====================
    SMART_SEARCH_PROMPT = """你是日志搜索助手，帮助用户快速找到他们需要的日志。

## 用户搜索意图
"{search_query}"

## 当前日志文件信息
- 总日志数: {total_logs}
- 时间范围: {time_range}
- 主要模块: {main_modules}

## 任务
理解用户意图，提供精确的搜索建议。

## 输出格式

### 1. 意图理解
用户想要查找：...

### 2. 搜索建议
**关键词**: xxx
**日志级别**: [ERROR/WARNING/INFO/...]
**模块过滤**: xxx（如果需要）
**时间范围**: xxx（如果相关）

### 3. 正则表达式（高级）
如果需要精确匹配，提供正则表达式：
```
正则表达式
```

### 4. 预期结果
说明搜索后可能找到什么类型的日志。

### 5. 替代搜索方案
如果上述搜索没有结果，可以尝试：
- 方案1: ...
- 方案2: ...

用中文回答。
"""

    # ==================== 格式化方法 ====================

    @classmethod
    def format_crash_analysis(cls, crash_info: Dict[str, Any]) -> str:
        """
        格式化崩溃分析提示词

        Args:
            crash_info: 崩溃信息字典，包含：
                - crash_time: 崩溃时间
                - module_name: 模块名
                - log_level: 日志级别
                - crash_stack: 崩溃堆栈
                - context_before: 上下文前
                - context_after: 上下文后

        Returns:
            格式化的提示词

        Example:
            >>> info = {
            ...     'crash_time': '2025-10-15 15:23:45',
            ...     'module_name': 'NetworkManager',
            ...     'log_level': 'ERROR',
            ...     'crash_stack': '...',
            ...     'context_before': '...',
            ...     'context_after': '...'
            ... }
            >>> prompt = PromptTemplates.format_crash_analysis(info)
        """
        return cls.CRASH_ANALYSIS_PROMPT.format(**crash_info)

    @classmethod
    def format_performance_analysis(cls, perf_info: Dict[str, Any]) -> str:
        """
        格式化性能分析提示词

        Args:
            perf_info: 性能信息字典，包含：
                - slow_operations: 慢速操作统计
                - perf_logs: 性能相关日志

        Returns:
            格式化的提示词
        """
        return cls.PERFORMANCE_ANALYSIS_PROMPT.format(**perf_info)

    @classmethod
    def format_issue_summary(cls, stats: Dict[str, Any]) -> str:
        """
        格式化问题总结提示词

        Args:
            stats: 统计信息字典

        Returns:
            格式化的提示词
        """
        return cls.ISSUE_SUMMARY_PROMPT.format(**stats)

    @classmethod
    def format_interactive_qa(cls, context: Dict[str, Any]) -> str:
        """
        格式化交互式问答提示词

        Args:
            context: 上下文信息字典

        Returns:
            格式化的提示词
        """
        return cls.INTERACTIVE_QA_PROMPT.format(**context)

    @classmethod
    def format_error_explanation(cls, error_log: str) -> str:
        """
        格式化错误解释提示词

        Args:
            error_log: 错误日志内容

        Returns:
            格式化的提示词
        """
        return cls.ERROR_EXPLANATION_PROMPT.format(error_log=error_log)

    @classmethod
    def format_related_logs(cls, log_info: Dict[str, Any]) -> str:
        """
        格式化相关日志查找提示词

        Args:
            log_info: 日志信息字典

        Returns:
            格式化的提示词
        """
        return cls.RELATED_LOGS_PROMPT.format(**log_info)

    @classmethod
    def format_smart_search(cls, search_info: Dict[str, Any]) -> str:
        """
        格式化智能搜索提示词

        Args:
            search_info: 搜索信息字典

        Returns:
            格式化的提示词
        """
        return cls.SMART_SEARCH_PROMPT.format(**search_info)


# 便捷函数
def get_crash_analysis_prompt(crash_time: str, module: str, stack: str,
                              context_before: str, context_after: str) -> str:
    """获取崩溃分析提示词（便捷函数）"""
    return PromptTemplates.format_crash_analysis({
        'crash_time': crash_time,
        'module_name': module,
        'log_level': 'ERROR',
        'crash_stack': stack,
        'context_before': context_before,
        'context_after': context_after
    })


def get_qa_prompt(user_question: str, logs_summary: str, stats: Dict) -> str:
    """获取问答提示词（便捷函数）"""
    return PromptTemplates.format_interactive_qa({
        'filename': stats.get('filename', 'N/A'),
        'total_logs': stats.get('total', 0),
        'current_logs': stats.get('current', 0),
        'time_range': stats.get('time_range', 'N/A'),
        'main_modules': stats.get('modules', 'N/A'),
        'crash_count': stats.get('crashes', 0),
        'error_count': stats.get('errors', 0),
        'warning_count': stats.get('warnings', 0),
        'relevant_logs': logs_summary,
        'user_question': user_question
    })


# 示例用法
if __name__ == "__main__":
    print("=== 提示词模板测试 ===\n")

    # 1. 测试崩溃分析模板
    print("1. 崩溃分析模板:")
    crash_prompt = PromptTemplates.format_crash_analysis({
        'crash_time': '2025-10-15 15:23:45',
        'module_name': 'NetworkManager',
        'log_level': 'ERROR',
        'crash_stack': 'NullPointerException at line 123',
        'context_before': '[2025-10-15 15:23:40] INFO: 网络请求开始\n[2025-10-15 15:23:42] WARNING: 超时',
        'context_after': '[2025-10-15 15:23:46] INFO: 尝试恢复'
    })
    print(f"   生成提示词长度: {len(crash_prompt)}字符")
    print(f"   预览: {crash_prompt[:200]}...\n")

    # 2. 测试问题总结模板
    print("2. 问题总结模板:")
    summary_prompt = PromptTemplates.format_issue_summary({
        'total': 10000,
        'time_range': '2025-10-15 10:00 ~ 18:00',
        'crashes': 5,
        'errors': 120,
        'warnings': 450,
        'module_activity': 'NetworkManager: 3000条\nUIManager: 2500条',
        'top_errors': '网络超时: 50次\n数据解析失败: 30次',
        'crash_details': '[15:23:45] NullPointerException'
    })
    print(f"   生成提示词长度: {len(summary_prompt)}字符\n")

    # 3. 测试问答模板
    print("3. 交互式问答模板:")
    qa_prompt = PromptTemplates.format_interactive_qa({
        'filename': 'app.log',
        'total_logs': 10000,
        'current_logs': 500,
        'time_range': '10:00 ~ 18:00',
        'main_modules': 'Network, UI, Database',
        'crash_count': 5,
        'error_count': 120,
        'warning_count': 450,
        'relevant_logs': '[15:23:45] ERROR: 网络请求失败',
        'user_question': '为什么应用崩溃了？'
    })
    print(f"   生成提示词长度: {len(qa_prompt)}字符\n")

    # 4. 测试错误解释模板
    print("4. 错误解释模板:")
    error_prompt = PromptTemplates.format_error_explanation(
        "[2025-10-15 15:23:45] ERROR: NullPointerException at NetworkManager.java:123"
    )
    print(f"   生成提示词长度: {len(error_prompt)}字符\n")

    print("=== 测试完成 ===")
    print("\n所有模板功能正常！")
