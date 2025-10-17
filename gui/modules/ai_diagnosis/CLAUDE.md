# AI诊断模块技术文档

**模块路径**: `gui/modules/ai_diagnosis/`
**版本**: v1.0.0
**创建日期**: 2025-10-16

---

## 模块概述

AI诊断模块为Mars日志分析工具提供智能化的问题诊断和分析能力。通过集成多种AI服务（Claude、OpenAI、Ollama），实现崩溃分析、性能诊断、问题总结等功能。

### 核心特性

- 🤖 **多AI服务支持**: Claude Code（推荐）、Claude API、OpenAI、Ollama
- 🔒 **隐私保护**: 自动过滤敏感信息（Token、密钥、用户ID等）
- ⚡ **异步处理**: 不阻塞UI，流畅用户体验
- 💰 **成本可控**: 支持免费本地模型（Ollama）
- 🎯 **上下文感知**: 基于当前日志内容进行分析

---

## 模块结构

```
ai_diagnosis/
├── __init__.py                # 模块导出
├── ai_client.py               # AI客户端抽象层
├── claude_code_client.py      # Claude Code代理客户端
├── config.py                  # 配置管理
├── log_preprocessor.py        # 日志预处理
├── prompt_templates.py        # 提示词模板库
└── CLAUDE.md                  # 本文档
```

---

## 核心组件

### 1. ai_client.py - AI客户端抽象层

#### AIClient（抽象基类）

所有AI客户端的基类，定义统一接口。

```python
from abc import ABC, abstractmethod

class AIClient(ABC):
    """AI客户端抽象基类"""

    @abstractmethod
    def ask(self, prompt: str, **kwargs) -> str:
        """
        发送提示词到AI服务

        Args:
            prompt: 提示词内容
            **kwargs: 其他参数（如temperature、max_tokens等）

        Returns:
            AI的响应文本

        Raises:
            RuntimeError: 当调用失败时
            TimeoutError: 当请求超时时
        """
        pass
```

#### ClaudeClient

通过Anthropic API直接调用Claude。

```python
class ClaudeClient(AIClient):
    """Claude API客户端"""

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        """
        初始化Claude客户端

        Args:
            api_key: Anthropic API Key
            model: 模型名称
        """
        import anthropic
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def ask(self, prompt: str, max_tokens: int = 4096) -> str:
        """发送请求到Claude API"""
        message = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
```

#### OpenAIClient

通过OpenAI API调用GPT模型。

```python
class OpenAIClient(AIClient):
    """OpenAI API客户端"""

    def __init__(self, api_key: str, model: str = "gpt-4"):
        """
        初始化OpenAI客户端

        Args:
            api_key: OpenAI API Key
            model: 模型名称（gpt-4, gpt-3.5-turbo等）
        """
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def ask(self, prompt: str) -> str:
        """发送请求到OpenAI API"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
```

#### OllamaClient

调用本地Ollama模型（完全免费）。

```python
class OllamaClient(AIClient):
    """Ollama本地模型客户端"""

    def __init__(self, model: str = "llama3", base_url: str = "http://localhost:11434"):
        """
        初始化Ollama客户端

        Args:
            model: 模型名称（llama3, qwen2, mistral等）
            base_url: Ollama服务地址
        """
        self.model = model
        self.base_url = base_url

    def is_available(self) -> bool:
        """检查Ollama服务是否可用"""
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False

    def ask(self, prompt: str) -> str:
        """发送请求到Ollama"""
        import requests
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False
            },
            timeout=120
        )
        response.raise_for_status()
        return response.json()['response']
```

#### ClaudeCodeClient

通过Claude Code作为代理（推荐方案）。

```python
class ClaudeCodeClient(AIClient):
    """
    Claude Code代理客户端

    利用现有的Claude Code连接，无需额外API Key。
    """

    def __init__(self):
        """初始化并检测可用的连接方式"""
        self._initialize()

    def _initialize(self):
        """尝试多种连接方式"""
        # 实现见claude_code_client.py
        pass

    def ask(self, prompt: str) -> str:
        """通过Claude Code发送请求"""
        # 实现见claude_code_client.py
        pass
```

#### AIClientFactory

工厂类，根据配置创建合适的客户端。

```python
class AIClientFactory:
    """AI客户端工厂"""

    @staticmethod
    def create(service: str = "ClaudeCode",
               api_key: str = None,
               model: str = None) -> AIClient:
        """
        创建AI客户端实例

        Args:
            service: 服务类型（"ClaudeCode", "Claude", "OpenAI", "Ollama"）
            api_key: API密钥（部分服务需要）
            model: 模型名称

        Returns:
            AIClient实例

        Raises:
            ValueError: 当服务类型未知或缺少必要参数时

        Example:
            >>> # 使用Claude Code（推荐）
            >>> client = AIClientFactory.create("ClaudeCode")
            >>>
            >>> # 使用Claude API
            >>> client = AIClientFactory.create("Claude", api_key="sk-xxx")
            >>>
            >>> # 使用Ollama本地模型
            >>> client = AIClientFactory.create("Ollama", model="llama3")
        """
        if service == "ClaudeCode":
            return ClaudeCodeClient()
        elif service == "Claude":
            if not api_key:
                # 尝试从环境变量获取
                api_key = os.getenv('ANTHROPIC_API_KEY')
                if not api_key:
                    raise ValueError("Claude服务需要API Key")
            return ClaudeClient(api_key, model or "claude-3-5-sonnet-20241022")
        elif service == "OpenAI":
            if not api_key:
                api_key = os.getenv('OPENAI_API_KEY')
                if not api_key:
                    raise ValueError("OpenAI服务需要API Key")
            return OpenAIClient(api_key, model or "gpt-4")
        elif service == "Ollama":
            client = OllamaClient(model or "llama3")
            if not client.is_available():
                raise RuntimeError("Ollama服务不可用，请确保已安装并启动")
            return client
        else:
            raise ValueError(f"未知的AI服务: {service}")

    @staticmethod
    def auto_detect() -> AIClient:
        """
        自动检测并返回最佳可用客户端

        优先级: ClaudeCode > Ollama > Claude > OpenAI
        """
        # 1. 尝试Claude Code
        try:
            client = ClaudeCodeClient()
            print("✓ 使用Claude Code代理")
            return client
        except:
            pass

        # 2. 尝试Ollama
        try:
            client = OllamaClient()
            if client.is_available():
                print("✓ 使用Ollama本地模型")
                return client
        except:
            pass

        # 3. 检查Claude API Key
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if api_key:
            print("✓ 使用Claude API")
            return ClaudeClient(api_key)

        # 4. 检查OpenAI API Key
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            print("✓ 使用OpenAI API")
            return OpenAIClient(api_key)

        # 都不可用
        raise RuntimeError(
            "未找到可用的AI服务。请配置以下任一选项：\n"
            "1. 确保Claude Code正在运行\n"
            "2. 安装并启动Ollama（brew install ollama && ollama serve）\n"
            "3. 设置环境变量 ANTHROPIC_API_KEY\n"
            "4. 设置环境变量 OPENAI_API_KEY"
        )
```

---

### 2. config.py - 配置管理

管理AI服务的配置，支持持久化和环境变量。

```python
class AIConfig:
    """AI配置管理"""

    CONFIG_FILE = "gui/ai_config.json"

    DEFAULT_CONFIG = {
        "ai_service": "ClaudeCode",
        "api_key": "",
        "model": "claude-3-5-sonnet-20241022",
        "auto_detect": True,
        "auto_summary": False,
        "privacy_filter": True,
        "max_tokens": 10000,
        "timeout": 60
    }

    @classmethod
    def load(cls) -> dict:
        """加载配置文件"""
        if os.path.exists(cls.CONFIG_FILE):
            with open(cls.CONFIG_FILE, 'r') as f:
                config = json.load(f)
                # 合并默认配置（处理新增字段）
                return {**cls.DEFAULT_CONFIG, **config}
        return cls.DEFAULT_CONFIG.copy()

    @classmethod
    def save(cls, config: dict):
        """保存配置文件"""
        with open(cls.CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)

    @classmethod
    def get_api_key(cls, service: str) -> str:
        """
        获取API Key（优先环境变量）

        Args:
            service: 服务类型（"Claude", "OpenAI"）

        Returns:
            API Key字符串
        """
        # 环境变量名映射
        env_vars = {
            "Claude": "ANTHROPIC_API_KEY",
            "OpenAI": "OPENAI_API_KEY"
        }

        # 优先从环境变量读取
        env_key = os.getenv(env_vars.get(service, ""))
        if env_key:
            return env_key

        # 其次从配置文件读取
        config = cls.load()
        return config.get('api_key', '')
```

---

### 3. log_preprocessor.py - 日志预处理

将原始日志转换为AI可理解的格式，并进行隐私保护。

#### LogPreprocessor

```python
class LogPreprocessor:
    """日志预处理器"""

    def extract_crash_logs(self, entries: List[LogEntry]) -> List[dict]:
        """
        提取崩溃日志及上下文

        Args:
            entries: 日志条目列表

        Returns:
            崩溃信息列表，每项包含：
            - crash_entry: 崩溃日志
            - context_before: 崩溃前N条日志
            - context_after: 崩溃后N条日志
        """
        pass

    def extract_error_patterns(self, entries: List[LogEntry]) -> List[dict]:
        """识别高频错误模式"""
        pass

    def build_timeline(self, entries: List[LogEntry],
                      center_time: datetime,
                      window: int = 60) -> List[LogEntry]:
        """
        构建时间线（中心时间前后N秒的日志）

        Args:
            entries: 日志条目列表
            center_time: 中心时间点
            window: 时间窗口（秒）

        Returns:
            时间窗口内的日志列表
        """
        pass

    def summarize_logs(self, entries: List[LogEntry],
                      max_tokens: int = 10000) -> str:
        """
        日志摘要（智能压缩，控制Token数量）

        策略：
        - 保留所有ERROR和Crash日志
        - WARNING按重要性采样
        - INFO和DEBUG稀疏采样

        Args:
            entries: 日志条目列表
            max_tokens: 最大Token数量

        Returns:
            格式化的日志摘要字符串
        """
        pass
```

#### PrivacyFilter

```python
class PrivacyFilter:
    """隐私信息过滤器"""

    # 内置过滤规则
    PATTERNS = [
        (r'token["\s:=]+([a-zA-Z0-9\-_]{20,})', 'TOKEN_***'),
        (r'api[_\s]?key["\s:=]+([a-zA-Z0-9\-_]{20,})', 'APIKEY_***'),
        (r'secret["\s:=]+([a-zA-Z0-9\-_]{20,})', 'SECRET_***'),
        (r'user[_\s]?id["\s:=]+(\d+)', 'USER_***'),
        (r'device[_\s]?id["\s:=]+([a-zA-Z0-9\-]+)', 'DEVICE_***'),
        (r'\d{11}', 'PHONE_***'),  # 手机号
        (r'[\w\.-]+@[\w\.-]+\.\w+', 'EMAIL_***'),  # 邮箱
        (r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', 'IP_***'),  # IP地址
        (r'\b\d{17}[\dXx]\b', 'IDCARD_***'),  # 身份证号
    ]

    def filter(self, text: str) -> str:
        """应用所有过滤规则"""
        for pattern, replacement in self.PATTERNS:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        return text

    def filter_log_entries(self, entries: List[LogEntry]) -> List[LogEntry]:
        """批量过滤日志条目"""
        pass
```

---

### 4. prompt_templates.py - 提示词模板库

管理各类分析场景的提示词。

```python
class PromptTemplates:
    """提示词模板库"""

    # 崩溃分析模板
    CRASH_ANALYSIS_PROMPT = """..."""

    # 性能分析模板
    PERFORMANCE_ANALYSIS_PROMPT = """..."""

    # 问题总结模板
    ISSUE_SUMMARY_PROMPT = """..."""

    # 交互式问答模板
    INTERACTIVE_QA_PROMPT = """..."""

    # 错误解释模板
    ERROR_EXPLANATION_PROMPT = """..."""

    @classmethod
    def format_crash_analysis(cls, crash_info: dict) -> str:
        """格式化崩溃分析提示词"""
        return cls.CRASH_ANALYSIS_PROMPT.format(**crash_info)

    # ... 其他格式化方法
```

---

## 使用示例

### 基础使用

```python
from gui.modules.ai_diagnosis import AIClientFactory, AIConfig

# 方式1: 使用配置
config = AIConfig.load()
client = AIClientFactory.create(
    service=config['ai_service'],
    api_key=config['api_key'],
    model=config['model']
)

# 方式2: 自动检测
client = AIClientFactory.auto_detect()

# 发送请求
response = client.ask("分析这条崩溃日志...")
print(response)
```

### 在GUI中使用

```python
class MarsLogAnalyzerPro:
    def analyze_crashes(self):
        """分析崩溃日志"""
        # 1. 获取AI客户端
        from gui.modules.ai_diagnosis import AIClientFactory, AIConfig
        config = AIConfig.load()
        client = AIClientFactory.create(config['ai_service'], config['api_key'])

        # 2. 预处理日志
        from gui.modules.ai_diagnosis.log_preprocessor import LogPreprocessor
        preprocessor = LogPreprocessor()
        crash_logs = preprocessor.extract_crash_logs(self.all_log_entries)

        # 3. 构建提示词
        from gui.modules.ai_diagnosis.prompt_templates import PromptTemplates
        prompt = PromptTemplates.format_crash_analysis({
            'crash_time': crash_logs[0]['crash_entry'].timestamp,
            'crash_stack': crash_logs[0]['crash_entry'].content,
            'context_before': preprocessor.summarize_logs(crash_logs[0]['context_before'])
        })

        # 4. 异步调用AI
        def _analyze():
            try:
                response = client.ask(prompt)
                self.after(0, self.append_chat, "AI助手", response)
            except Exception as e:
                self.after(0, self.append_chat, "系统", f"分析失败: {str(e)}")

        threading.Thread(target=_analyze, daemon=True).start()
```

---

## 配置文件格式

`gui/ai_config.json`:

```json
{
  "ai_service": "ClaudeCode",
  "api_key": "",
  "model": "claude-3-5-sonnet-20241022",
  "auto_detect": true,
  "auto_summary": false,
  "privacy_filter": true,
  "max_tokens": 10000,
  "timeout": 60
}
```

---

## 依赖管理

### 必需依赖

```txt
anthropic>=0.18.0    # Claude API
openai>=1.12.0       # OpenAI API（可选）
requests>=2.31.0     # HTTP请求（Ollama）
```

### 可选依赖

```txt
ollama>=0.1.0        # Ollama客户端库（可选）
```

### 安装命令

```bash
# 最小安装（仅Claude Code）
pip install anthropic

# 完整安装（所有AI服务）
pip install anthropic openai requests

# 本地模型支持
brew install ollama
ollama pull llama3
```

---

## 测试

### 单元测试

```bash
# 运行所有测试
python -m pytest gui/modules/ai_diagnosis/tests/

# 运行特定测试
python -m pytest gui/modules/ai_diagnosis/tests/test_ai_client.py
python -m pytest gui/modules/ai_diagnosis/tests/test_preprocessor.py
```

### 测试覆盖率

```bash
pytest --cov=gui/modules/ai_diagnosis --cov-report=html
```

---

## 故障排查

### 问题：Claude Code连接失败

**症状**: `ClaudeCodeClient`初始化失败

**解决方案**:
1. 确保Claude Code正在运行
2. 检查Claude Code版本是否支持MCP
3. 尝试手动运行`claude-code --version`

### 问题：API请求超时

**症状**: 请求等待很久后超时

**解决方案**:
1. 检查网络连接
2. 增加timeout配置（默认60秒）
3. 减少日志摘要长度（减少Token数量）

### 问题：隐私过滤误伤

**症状**: 正常内容被过滤掉

**解决方案**:
1. 调整`PrivacyFilter.PATTERNS`规则
2. 添加白名单机制
3. 禁用特定过滤规则

---

## 最佳实践

1. **优先使用Claude Code**: 无需API Key，成本为零
2. **启用隐私过滤**: 保护敏感信息
3. **控制Token使用**: 日志摘要保持在10k tokens以内
4. **异步处理**: 避免阻塞UI
5. **错误处理**: 优雅降级，友好提示

---

## 未来计划

- [ ] 支持流式响应（实时显示AI输出）
- [ ] 缓存机制（相似问题复用结果）
- [ ] 多轮对话历史管理
- [ ] 自定义提示词模板
- [ ] AI响应质量评分
- [ ] 团队协作和结果分享

---

## 变更日志

### [1.0.0] - 2025-10-16

**新增**:
- 初始版本发布
- 支持4种AI服务
- 基础日志预处理
- 隐私信息过滤
- 5类提示词模板

---

**最后更新**: 2025-10-16
**维护者**: Mars Log Analyzer Team
