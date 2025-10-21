# CLAUDE.md - AI诊断模块

## 模块概述
为Mars日志分析工具提供智能化的问题诊断和分析能力，支持多种AI服务。

## 核心功能
- **多AI服务支持**: Claude Code（推荐）、Claude API、OpenAI、Ollama
- **智能分析**: 崩溃分析、性能诊断、问题总结
- **隐私保护**: 自动过滤敏感信息
- **异步处理**: 不阻塞UI，流畅用户体验
- **上下文感知**: 基于当前日志内容分析

## 模块结构
```
ai_diagnosis/
├── ai_client.py               # AI客户端抽象层
├── claude_code_client.py      # Claude Code代理客户端
├── config.py                  # 配置管理
├── log_preprocessor.py        # 日志预处理
└── prompt_templates.py        # 提示词模板库
```

## 核心组件

### AIClient - AI客户端抽象层
支持多种AI服务的统一接口：
- **ClaudeCodeClient**: 通过Claude Code代理（推荐，无需API Key）
- **ClaudeClient**: 通过Anthropic API
- **OpenAIClient**: 通过OpenAI API
- **OllamaClient**: 本地模型服务

### 配置管理
```python
# 配置文件示例
{
  "ai_service": "ClaudeCode",
  "api_key": "",
  "model": "claude-3-5-sonnet-20241022",
  "auto_detect": true,
  "privacy_filter": true,
  "max_tokens": 10000
}
```

### 日志预处理
- **崩溃提取**: 自动提取崩溃堆栈和上下文
- **错误模式识别**: 识别10种常见错误模式
- **日志摘要**: 智能压缩，控制Token数量
- **隐私过滤**: 自动过滤敏感信息

### 提示词模板
- 崩溃分析模板
- 性能诊断模板
- 问题总结模板
- 错误解释模板
- 交互式问答模板

## 使用方法

### 基础使用
```python
from gui.modules.ai_diagnosis import AIClientFactory

# 自动检测最佳可用客户端
client = AIClientFactory.auto_detect()

# 或指定特定服务
client = AIClientFactory.create("ClaudeCode")

# 发送请求
response = client.ask("分析这条崩溃日志...")
```

### 配置选项
- **ai_service**: AI服务类型
- **api_key**: API密钥（部分服务需要）
- **auto_detect**: 自动检测最佳服务
- **privacy_filter**: 启用隐私过滤
- **max_tokens**: 最大Token数量

## 隐私保护

### 内置过滤规则
- Token、API Key、用户ID
- 手机号、邮箱、IP地址
- 身份证号等敏感信息

### 白名单机制
支持自定义白名单，避免误伤重要信息。

## 性能优化

### 异步处理
所有AI请求异步执行，不阻塞UI。

### Token管理
- 智能日志摘要，控制在合理范围
- 实时显示Token使用情况
- 支持中断长时间请求

## 依赖管理

### 必需依赖
```bash
pip install anthropic requests
```

### 可选依赖
```bash
pip install openai ollama
```

## 常见问题

### 连接失败
1. 确保网络连接正常
2. 检查API Key配置
3. 验证服务可用性

### 性能问题
1. 减少日志摘要长度
2. 启用缓存机制
3. 选择快速响应模型

## 最佳实践

1. **优先使用Claude Code**: 无需API Key，成本为零
2. **启用隐私过滤**: 保护敏感信息
3. **控制Token使用**: 保持10k tokens以内
4. **异步处理**: 避免阻塞UI
5. **错误处理**: 优雅降级，友好提示

---

*详细实现请参考源码注释。*