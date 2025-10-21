"""
AI客户端抽象层

提供统一的AI服务接口，支持：
- Claude API（直接调用）
- OpenAI API
- Ollama本地模型
- Claude Code代理（推荐）

所有客户端实现统一的ask()接口，便于切换。
"""

import os
from abc import ABC, abstractmethod
from typing import Optional


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


class ClaudeClient(AIClient):
    """Claude API客户端（直接调用）"""

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        """
        初始化Claude客户端

        Args:
            api_key: Anthropic API Key
            model: 模型名称

        Example:
            >>> client = ClaudeClient(api_key="sk-ant-...")
            >>> response = client.ask("Hello!")
        """
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)
            self.model = model
        except ImportError:
            raise RuntimeError(
                "未安装anthropic库。请运行: pip install anthropic"
            )

    def ask(self, prompt: str, max_tokens: int = 4096, temperature: float = 1.0) -> str:
        """
        发送请求到Claude API

        Args:
            prompt: 提示词
            max_tokens: 最大Token数
            temperature: 温度参数（0-1）

        Returns:
            Claude的响应文本
        """
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text
        except Exception as e:
            raise RuntimeError(f"Claude API调用失败: {str(e)}")


class OpenAIClient(AIClient):
    """OpenAI API客户端"""

    def __init__(self, api_key: str, model: str = "gpt-4"):
        """
        初始化OpenAI客户端

        Args:
            api_key: OpenAI API Key
            model: 模型名称（gpt-4, gpt-3.5-turbo等）

        Example:
            >>> client = OpenAIClient(api_key="sk-...")
            >>> response = client.ask("Hello!")
        """
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
            self.model = model
        except ImportError:
            raise RuntimeError(
                "未安装openai库。请运行: pip install openai"
            )

    def ask(self, prompt: str, temperature: float = 1.0) -> str:
        """
        发送请求到OpenAI API

        Args:
            prompt: 提示词
            temperature: 温度参数（0-2）

        Returns:
            GPT的响应文本
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"OpenAI API调用失败: {str(e)}")


class OllamaClient(AIClient):
    """Ollama本地模型客户端（完全免费）"""

    def __init__(self, model: str = "llama3", base_url: str = "http://localhost:11434"):
        """
        初始化Ollama客户端

        Args:
            model: 模型名称（llama3, qwen2, mistral等）
            base_url: Ollama服务地址

        Example:
            >>> client = OllamaClient(model="llama3")
            >>> if client.is_available():
            ...     response = client.ask("Hello!")
        """
        self.model = model
        self.base_url = base_url

    def is_available(self) -> bool:
        """
        检查Ollama服务是否可用

        Returns:
            服务是否可用
        """
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False

    def ask(self, prompt: str, temperature: float = 0.8) -> str:
        """
        发送请求到Ollama

        Args:
            prompt: 提示词
            temperature: 温度参数（0-1）

        Returns:
            模型的响应文本
        """
        try:
            import requests

            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature
                    }
                },
                timeout=120
            )
            response.raise_for_status()
            return response.json()['response']

        except ImportError:
            raise RuntimeError("未安装requests库。请运行: pip install requests")
        except Exception as e:
            raise RuntimeError(f"Ollama调用失败: {str(e)}")


class ClaudeCodeClient(AIClient):
    """
    Claude Code代理客户端（推荐）

    利用现有的Claude Code连接，无需额外API Key。
    """

    def __init__(self):
        """初始化并检测可用的连接方式"""
        # 延迟导入，避免循环依赖
        from .claude_code_client import ClaudeCodeProxyClient

        self.proxy_client = ClaudeCodeProxyClient()

        # 检测可用性
        if not self.proxy_client.is_available():
            raise RuntimeError(
                "Claude Code不可用。请确保：\n"
                "1. Claude Code正在运行\n"
                "2. 您当前在Claude Code会话中"
            )

    def ask(self, prompt: str, **kwargs) -> str:
        """
        通过Claude Code发送请求

        Args:
            prompt: 提示词
            **kwargs: 其他参数

        Returns:
            Claude的响应文本
        """
        try:
            return self.proxy_client.ask(prompt)
        except Exception as e:
            raise RuntimeError(f"Claude Code代理调用失败: {str(e)}")


class AIClientFactory:
    """AI客户端工厂"""

    @staticmethod
    def create(service: str = "ClaudeCode",
               api_key: Optional[str] = None,
               model: Optional[str] = None) -> AIClient:
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
            RuntimeError: 当服务不可用时

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
            # 尝试从环境变量获取API Key
            if not api_key:
                api_key = os.getenv('ANTHROPIC_API_KEY')
                if not api_key:
                    raise ValueError(
                        "Claude服务需要API Key。请设置环境变量 ANTHROPIC_API_KEY "
                        "或在配置中提供 api_key"
                    )
            return ClaudeClient(api_key, model or "claude-3-5-sonnet-20241022")

        elif service == "OpenAI":
            # 尝试从环境变量获取API Key
            if not api_key:
                api_key = os.getenv('OPENAI_API_KEY')
                if not api_key:
                    raise ValueError(
                        "OpenAI服务需要API Key。请设置环境变量 OPENAI_API_KEY "
                        "或在配置中提供 api_key"
                    )
            return OpenAIClient(api_key, model or "gpt-4")

        elif service == "Ollama":
            client = OllamaClient(model or "llama3")
            if not client.is_available():
                raise RuntimeError(
                    "Ollama服务不可用。请确保：\n"
                    "1. 已安装Ollama（brew install ollama）\n"
                    "2. Ollama服务正在运行（ollama serve）\n"
                    "3. 已下载模型（ollama pull llama3）"
                )
            return client

        else:
            raise ValueError(
                f"未知的AI服务: {service}\n"
                f"支持的服务: ClaudeCode, Claude, OpenAI, Ollama"
            )

    @staticmethod
    def auto_detect() -> AIClient:
        """
        自动检测并返回最佳可用客户端

        优先级: ClaudeCode > Ollama > Claude > OpenAI

        Returns:
            可用的AIClient实例

        Raises:
            RuntimeError: 当没有可用服务时

        Example:
            >>> client = AIClientFactory.auto_detect()
            >>> response = client.ask("Hello!")
        """
        # 1. 尝试Claude Code
        try:
            client = ClaudeCodeClient()
            print("✓ 使用Claude Code代理")
            return client
        except Exception as e:
            print(f"  Claude Code不可用: {str(e)}")

        # 2. 尝试Ollama
        try:
            client = OllamaClient()
            if client.is_available():
                print("✓ 使用Ollama本地模型")
                return client
            else:
                print("  Ollama服务未运行")
        except Exception as e:
            print(f"  Ollama不可用: {str(e)}")

        # 3. 检查Claude API Key
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if api_key:
            print("✓ 使用Claude API")
            return ClaudeClient(api_key)
        else:
            print("  未配置ANTHROPIC_API_KEY环境变量")

        # 4. 检查OpenAI API Key
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            print("✓ 使用OpenAI API")
            return OpenAIClient(api_key)
        else:
            print("  未配置OPENAI_API_KEY环境变量")

        # 都不可用
        raise RuntimeError(
            "未找到可用的AI服务。请配置以下任一选项：\n"
            "1. 确保Claude Code正在运行\n"
            "2. 安装并启动Ollama（brew install ollama && ollama serve）\n"
            "3. 设置环境变量 ANTHROPIC_API_KEY\n"
            "4. 设置环境变量 OPENAI_API_KEY\n"
            "\n"
            "或在GUI的AI设置中配置API Key"
        )


# 便捷函数
def create_client(service: str = "ClaudeCode", **kwargs) -> AIClient:
    """创建AI客户端（便捷函数）"""
    return AIClientFactory.create(service, **kwargs)


def auto_detect_client() -> AIClient:
    """自动检测可用客户端（便捷函数）"""
    return AIClientFactory.auto_detect()


# 示例用法
if __name__ == "__main__":
    print("=== AI客户端测试 ===\n")

    # 测试自动检测
    print("1. 自动检测最佳客户端:")
    try:
        client = AIClientFactory.auto_detect()
        print(f"   客户端类型: {type(client).__name__}")

        # 发送测试请求
        response = client.ask("你好，请用一句话介绍你自己。")
        print(f"   响应: {response[:100]}...")
        print("   ✓ 测试成功\n")

    except Exception as e:
        print(f"   ✗ 测试失败: {str(e)}\n")

    # 测试特定服务
    print("2. 测试Claude Code:")
    try:
        client = AIClientFactory.create("ClaudeCode")
        response = client.ask("测试连接")
        print(f"   ✓ Claude Code可用\n")
    except Exception as e:
        print(f"   ✗ Claude Code不可用: {str(e)}\n")

    print("3. 测试Ollama:")
    try:
        client = AIClientFactory.create("Ollama")
        print(f"   ✓ Ollama可用\n")
    except Exception as e:
        print(f"   ✗ Ollama不可用: {str(e)}\n")

    print("4. 检查环境变量:")
    if os.getenv('ANTHROPIC_API_KEY'):
        print("   ✓ ANTHROPIC_API_KEY已设置")
    else:
        print("   ✗ ANTHROPIC_API_KEY未设置")

    if os.getenv('OPENAI_API_KEY'):
        print("   ✓ OPENAI_API_KEY已设置")
    else:
        print("   ✗ OPENAI_API_KEY未设置")
