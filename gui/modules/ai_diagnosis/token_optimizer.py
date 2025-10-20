"""
Token优化器 - 统一的Token管理和优化

整合智能压缩器和精简提示词，提供统一的token优化接口。
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

try:
    from data_models import LogEntry
except ImportError:
    try:
        from modules.data_models import LogEntry
    except ImportError:
        from gui.modules.data_models import LogEntry

try:
    from .smart_compressor import SmartLogCompressor, FocusedCompressor, estimate_tokens
    from .compact_prompts import CompactPromptTemplates
except ImportError:
    from smart_compressor import SmartLogCompressor, FocusedCompressor, estimate_tokens
    from compact_prompts import CompactPromptTemplates


@dataclass
class TokenBudget:
    """Token预算管理"""
    max_total: int  # 总预算（模型限制）
    max_prompt: int  # 提示词预算
    max_logs: int  # 日志内容预算
    reserved: int  # 保留空间（给AI回复）

    def __post_init__(self):
        """验证预算设置"""
        if self.max_prompt + self.max_logs + self.reserved > self.max_total:
            raise ValueError("Token预算分配超过总预算")


@dataclass
class OptimizedPrompt:
    """优化后的提示词"""
    prompt: str  # 完整提示词（模板+日志）
    estimated_tokens: int  # 预估token数
    log_summary: str  # 日志摘要部分
    template_name: str  # 使用的模板名称
    compression_ratio: float  # 日志压缩比


class TokenOptimizer:
    """Token优化器 - 统一管理token使用"""

    # 不同AI服务的token限制
    MODEL_LIMITS = {
        "claude-3-5-sonnet-20241022": 200000,  # Claude 3.5 Sonnet
        "claude-3-opus-20240229": 200000,  # Claude 3 Opus
        "gpt-4": 8192,  # GPT-4
        "gpt-4-32k": 32768,  # GPT-4 32K
        "gpt-3.5-turbo": 4096,  # GPT-3.5 Turbo
        "gpt-3.5-turbo-16k": 16384,  # GPT-3.5 Turbo 16K
        "llama3": 8192,  # Llama 3 (Ollama)
        "qwen2": 32768,  # Qwen 2 (Ollama)
    }

    # 默认token预算分配
    DEFAULT_BUDGETS = {
        "claude": TokenBudget(
            max_total=200000,
            max_prompt=1500,  # 模板部分
            max_logs=3000,  # 日志内容
            reserved=10000  # 保留给回复
        ),
        "gpt-4": TokenBudget(
            max_total=8192,
            max_prompt=800,
            max_logs=2000,
            reserved=2000
        ),
        "gpt-3.5": TokenBudget(
            max_total=4096,
            max_prompt=500,
            max_logs=1500,
            reserved=1000
        ),
        "ollama": TokenBudget(
            max_total=8192,
            max_prompt=800,
            max_logs=2000,
            reserved=2000
        )
    }

    def __init__(self, model: str = "claude-3-5-sonnet-20241022"):
        """
        初始化Token优化器

        Args:
            model: AI模型名称
        """
        self.model = model
        self.budget = self._get_budget_for_model(model)
        self.compressor = SmartLogCompressor(max_tokens=self.budget.max_logs)
        self.focused_compressor = FocusedCompressor(max_tokens=self.budget.max_logs)

    def _get_budget_for_model(self, model: str) -> TokenBudget:
        """根据模型获取token预算"""
        if "claude" in model.lower():
            return self.DEFAULT_BUDGETS["claude"]
        elif "gpt-4-32k" in model.lower() or "gpt-4-turbo" in model.lower():
            return TokenBudget(
                max_total=32768,
                max_prompt=1000,
                max_logs=2500,
                reserved=5000
            )
        elif "gpt-4" in model.lower():
            return self.DEFAULT_BUDGETS["gpt-4"]
        elif "gpt-3.5" in model.lower():
            return self.DEFAULT_BUDGETS["gpt-3.5"]
        else:
            # 默认使用ollama的预算（中等）
            return self.DEFAULT_BUDGETS["ollama"]

    def optimize_for_crash_analysis(self, entries: List[LogEntry]) -> OptimizedPrompt:
        """
        为崩溃分析优化提示词

        Args:
            entries: 日志条目列表

        Returns:
            优化后的提示词
        """
        # 使用聚焦式压缩器
        compressed = self.focused_compressor.compress_for_crash_analysis(entries)

        # 使用精简模板
        prompt = CompactPromptTemplates.format_crash_analysis(compressed.summary)

        return OptimizedPrompt(
            prompt=prompt,
            estimated_tokens=estimate_tokens(prompt),
            log_summary=compressed.summary,
            template_name="crash_analysis_compact",
            compression_ratio=compressed.compression_ratio
        )

    def optimize_for_performance_analysis(self, entries: List[LogEntry]) -> OptimizedPrompt:
        """为性能分析优化提示词"""
        compressed = self.focused_compressor.compress_for_performance_analysis(entries)
        prompt = CompactPromptTemplates.format_performance_analysis(compressed.summary)

        return OptimizedPrompt(
            prompt=prompt,
            estimated_tokens=estimate_tokens(prompt),
            log_summary=compressed.summary,
            template_name="performance_analysis_compact",
            compression_ratio=compressed.compression_ratio
        )

    def optimize_for_issue_summary(self, entries: List[LogEntry]) -> OptimizedPrompt:
        """为问题总结优化提示词"""
        compressed = self.compressor.compress(entries)
        prompt = CompactPromptTemplates.format_issue_summary(compressed.summary)

        return OptimizedPrompt(
            prompt=prompt,
            estimated_tokens=estimate_tokens(prompt),
            log_summary=compressed.summary,
            template_name="issue_summary_compact",
            compression_ratio=compressed.compression_ratio
        )

    def optimize_for_error_explanation(self, log_entry: LogEntry) -> OptimizedPrompt:
        """为单条错误解释优化提示词"""
        # 单条日志，直接格式化
        log_text = f"[{log_entry.timestamp}] {log_entry.level} {log_entry.module}: {log_entry.content}"

        prompt = CompactPromptTemplates.format_error_explanation(log_text)

        return OptimizedPrompt(
            prompt=prompt,
            estimated_tokens=estimate_tokens(prompt),
            log_summary=log_text,
            template_name="error_explanation_compact",
            compression_ratio=1.0
        )

    def optimize_for_interactive_qa(self, entries: List[LogEntry],
                                    user_question: str) -> OptimizedPrompt:
        """为交互式问答优化提示词"""
        # 根据问题类型选择压缩策略
        if "崩溃" in user_question or "crash" in user_question.lower():
            compressed = self.focused_compressor.compress_for_crash_analysis(entries)
        elif "性能" in user_question or "慢" in user_question:
            compressed = self.focused_compressor.compress_for_performance_analysis(entries)
        else:
            compressed = self.compressor.compress(entries)

        prompt = CompactPromptTemplates.format_interactive_qa(
            compressed.summary,
            user_question
        )

        return OptimizedPrompt(
            prompt=prompt,
            estimated_tokens=estimate_tokens(prompt),
            log_summary=compressed.summary,
            template_name="interactive_qa_compact",
            compression_ratio=compressed.compression_ratio
        )

    def optimize_for_module_analysis(self, entries: List[LogEntry],
                                     module: str) -> OptimizedPrompt:
        """为特定模块分析优化提示词"""
        compressed = self.focused_compressor.compress_for_module_analysis(entries, module)

        # 使用问题总结模板（适合模块分析）
        prompt = CompactPromptTemplates.format_issue_summary(compressed.summary)

        return OptimizedPrompt(
            prompt=prompt,
            estimated_tokens=estimate_tokens(prompt),
            log_summary=compressed.summary,
            template_name="module_analysis_compact",
            compression_ratio=compressed.compression_ratio
        )

    def check_budget(self, estimated_tokens: int) -> Tuple[bool, str]:
        """
        检查token预算

        Args:
            estimated_tokens: 预估的token数

        Returns:
            (是否在预算内, 提示信息)
        """
        max_allowed = self.budget.max_prompt + self.budget.max_logs

        if estimated_tokens <= max_allowed:
            usage = estimated_tokens / max_allowed * 100
            return True, f"Token使用: {estimated_tokens}/{max_allowed} ({usage:.1f}%)"
        else:
            over = estimated_tokens - max_allowed
            return False, f"Token超预算 {over} tokens！需要进一步压缩。"

    def get_budget_info(self) -> Dict:
        """获取当前预算信息"""
        return {
            "model": self.model,
            "max_total": self.budget.max_total,
            "max_prompt": self.budget.max_prompt,
            "max_logs": self.budget.max_logs,
            "reserved": self.budget.reserved,
            "max_input": self.budget.max_prompt + self.budget.max_logs
        }


# 便捷函数
def create_optimizer(model: str = "claude-3-5-sonnet-20241022") -> TokenOptimizer:
    """
    创建Token优化器

    Args:
        model: 模型名称

    Returns:
        TokenOptimizer实例
    """
    return TokenOptimizer(model=model)


def get_model_limit(model: str) -> int:
    """
    获取模型的token限制

    Args:
        model: 模型名称

    Returns:
        Token限制数
    """
    return TokenOptimizer.MODEL_LIMITS.get(model, 8192)


# 测试代码
if __name__ == "__main__":
    print("=== Token优化器测试 ===\n")

    # 测试不同模型的预算
    models = ["claude-3-5-sonnet-20241022", "gpt-4", "gpt-3.5-turbo"]

    for model in models:
        optimizer = create_optimizer(model)
        info = optimizer.get_budget_info()

        print(f"模型: {model}")
        print(f"  总预算: {info['max_total']}")
        print(f"  输入预算: {info['max_input']} (模板:{info['max_prompt']} + 日志:{info['max_logs']})")
        print(f"  保留空间: {info['reserved']}")
        print()
