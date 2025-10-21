"""
AI诊断模块 - Mars日志智能分析

提供基于AI的日志智能诊断功能，支持：
- 崩溃分析
- 性能诊断
- 问题总结
- 智能搜索
- 自由对话

支持多种AI服务：
- Claude Code（推荐，无需API Key）
- Claude API
- OpenAI API
- Ollama本地模型
"""

__version__ = "1.0.0"
__author__ = "Mars Log Analyzer Team"

# 导出核心类
from .ai_client import (
    AIClient,
    AIClientFactory,
    ClaudeClient,
    ClaudeCodeClient,
    OllamaClient,
    OpenAIClient,
)
from .config import AIConfig

__all__ = [
    "AIClient",
    "AIClientFactory",
    "ClaudeClient",
    "OpenAIClient",
    "OllamaClient",
    "ClaudeCodeClient",
    "AIConfig",
]
