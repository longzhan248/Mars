"""
Claude Code代理客户端

通过Claude Code作为AI服务的代理，实现零成本AI集成。

支持的连接方式：
1. 子进程调用Claude Code CLI
2. HTTP API代理（如果Claude Code提供）
3. MCP协议连接（未来支持）

优先级：HTTP API > CLI调用 > MCP
"""

import os
import shutil
import subprocess
import tempfile
from typing import List, Optional


class ClaudeCodeProxyClient:
    """
    Claude Code代理客户端

    通过现有的Claude Code会话进行AI交互，无需额外API Key。
    """

    def __init__(self, timeout: int = 60, claude_path: str = ""):
        """
        初始化Claude Code代理客户端

        Args:
            timeout: 请求超时时间（秒）
            claude_path: claude命令的完整路径（可选，留空自动检测）

        Example:
            >>> client = ClaudeCodeProxyClient()
            >>> if client.is_available():
            ...     response = client.ask("Hello!")
        """
        self.timeout = timeout
        self.temp_files = []  # 跟踪临时文件，用于清理
        self._claude_cmd = None  # 存储检测到的命令名
        self.custom_claude_path = claude_path  # 用户指定的路径

    def is_available(self) -> bool:
        """
        检查Claude Code是否可用

        Returns:
            是否可用

        Example:
            >>> client = ClaudeCodeProxyClient()
            >>> if client.is_available():
            ...     print("Claude Code可用")
        """
        # 尝试多个可能的路径（用于打包后的app）
        home = os.path.expanduser("~")
        possible_paths = [
            # 用户配置的路径（最高优先级）
            self.custom_claude_path,
            # 用户自定义路径
            os.path.join(home, '.local/bin/claude'),
            os.path.join(home, '.npm/bin/claude'),
            # nvm路径（常见node版本）
            os.path.join(home, '.nvm/versions/node/v20.18.1/bin/claude'),
            os.path.join(home, '.nvm/versions/node/v20.18.0/bin/claude'),
            os.path.join(home, '.nvm/versions/node/v22.0.0/bin/claude'),
            os.path.join(home, '.nvm/versions/node/v21.0.0/bin/claude'),
            os.path.join(home, '.nvm/versions/node/v18.0.0/bin/claude'),
            # 通过which查找（仅在terminal环境有效）
            shutil.which('claude'),
            shutil.which('claude-code'),
            # 系统路径
            '/usr/local/bin/claude',
            '/opt/homebrew/bin/claude',
        ]

        for cmd_path in possible_paths:
            if not cmd_path or not os.path.exists(cmd_path):
                continue

            try:
                # 检查命令是否可用
                result = subprocess.run(
                    [cmd_path, '--version'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    # 找到可用命令，保存完整路径
                    self._claude_cmd = cmd_path
                    print(f"✓ 找到Claude Code: {cmd_path}")
                    return True

            except (FileNotFoundError, subprocess.TimeoutExpired, Exception) as e:
                continue

        # 最后尝试通过shell执行（会使用完整的PATH）
        try:
            result = subprocess.run(
                ['bash', '-l', '-c', 'which claude'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                cmd_path = result.stdout.strip()
                if os.path.exists(cmd_path):
                    self._claude_cmd = cmd_path
                    print(f"✓ 通过shell找到Claude Code: {cmd_path}")
                    return True
        except Exception:
            pass

        return False

    def ask(self, prompt: str, context_files: Optional[List[str]] = None) -> str:
        """
        通过Claude Code发送提问

        Args:
            prompt: 提示词内容
            context_files: 可选的上下文文件路径列表

        Returns:
            Claude的响应文本

        Raises:
            RuntimeError: 当调用失败时
            TimeoutError: 当请求超时时

        Example:
            >>> client = ClaudeCodeProxyClient()
            >>> response = client.ask("分析这个日志文件", context_files=["error.log"])
            >>> print(response)
        """
        # 方式1: 尝试通过CLI调用
        try:
            return self._ask_via_cli(prompt, context_files)
        except Exception as e:
            raise RuntimeError(f"Claude Code调用失败: {str(e)}")

    def _ask_via_cli(self, prompt: str, context_files: Optional[List[str]] = None) -> str:
        """
        通过CLI调用Claude Code

        Args:
            prompt: 提示词
            context_files: 上下文文件列表

        Returns:
            响应文本
        """
        # 确保已检测到可用命令
        if not self._claude_cmd:
            if not self.is_available():
                raise RuntimeError(
                    "找不到claude或claude-code命令。请确保：\n"
                    "1. Claude Code已正确安装\n"
                    "2. claude命令在系统PATH中\n"
                    "3. 您正在Claude Code会话中运行"
                )

        try:
            # 构建完整提示词
            full_prompt = prompt
            if context_files:
                context_content = []
                for file_path in context_files:
                    if os.path.exists(file_path):
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                context_content.append(f"## 文件: {file_path}\n```\n{content}\n```\n")
                        except Exception as e:
                            print(f"警告: 无法读取上下文文件 {file_path}: {e}")

                if context_content:
                    full_prompt = '\n'.join(context_content) + '\n\n' + prompt

            # 构建命令 - 使用 -p/--print 模式
            cmd = [self._claude_cmd, '-p']

            # 获取环境变量（关键:传递完整的PATH）
            env = os.environ.copy()

            # 如果通过nvm安装,确保NODE路径在PATH中
            if '.nvm' in self._claude_cmd:
                nvm_bin = os.path.dirname(self._claude_cmd)
                if 'PATH' in env:
                    env['PATH'] = f"{nvm_bin}:{env['PATH']}"
                else:
                    env['PATH'] = nvm_bin

            # 执行命令，通过stdin传递提示词
            result = subprocess.run(
                cmd,
                input=full_prompt,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env=env  # 传递环境变量
            )

            if result.returncode == 0:
                return result.stdout.strip()
            else:
                raise RuntimeError(
                    f"Claude返回错误码 {result.returncode}\n"
                    f"标准输出: {result.stdout[:200] if result.stdout else '(空)'}\n"
                    f"错误信息: {result.stderr[:200] if result.stderr else '(空)'}"
                )

        except subprocess.TimeoutExpired:
            raise TimeoutError(
                f"Claude响应超时（{self.timeout}秒）。\n"
                "建议：\n"
                "1. 减少日志摘要长度\n"
                "2. 增加timeout配置\n"
                "3. 使用更快的模型"
            )
        except FileNotFoundError:
            raise RuntimeError(
                f"找不到{self._claude_cmd}命令。请确保：\n"
                "1. Claude Code已正确安装\n"
                "2. {self._claude_cmd}在系统PATH中\n"
                "3. 您正在Claude Code会话中运行"
            )

    def _create_temp_file(self, content: str, suffix: str = '.txt') -> str:
        """
        创建临时文件

        Args:
            content: 文件内容
            suffix: 文件后缀

        Returns:
            临时文件路径
        """
        try:
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix=suffix,
                delete=False,
                encoding='utf-8'
            ) as f:
                f.write(content)
                temp_path = f.name

            self.temp_files.append(temp_path)
            return temp_path

        except Exception as e:
            raise RuntimeError(f"创建临时文件失败: {str(e)}")

    def _cleanup_temp_file(self, file_path: str):
        """
        清理临时文件

        Args:
            file_path: 文件路径
        """
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)

            if file_path in self.temp_files:
                self.temp_files.remove(file_path)

        except Exception as e:
            # 清理失败不应该影响主流程
            print(f"警告: 清理临时文件失败: {str(e)}")

    def cleanup_all(self):
        """清理所有临时文件"""
        for file_path in self.temp_files[:]:  # 复制列表避免迭代时修改
            self._cleanup_temp_file(file_path)

    def __del__(self):
        """析构函数，自动清理临时文件"""
        self.cleanup_all()


class ClaudeCodeHTTPClient:
    """
    Claude Code HTTP API客户端（实验性）

    如果Claude Code提供了本地HTTP API，使用此客户端。
    """

    def __init__(self, base_url: str = "http://localhost:52134", timeout: int = 60):
        """
        初始化HTTP客户端

        Args:
            base_url: Claude Code本地API地址
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url
        self.timeout = timeout

    def is_available(self) -> bool:
        """
        检查HTTP API是否可用

        Returns:
            是否可用
        """
        try:
            import requests
            response = requests.get(
                f"{self.base_url}/health",
                timeout=2
            )
            return response.status_code == 200
        except:
            return False

    def ask(self, prompt: str) -> str:
        """
        通过HTTP API发送请求

        Args:
            prompt: 提示词

        Returns:
            响应文本
        """
        try:
            import requests

            response = requests.post(
                f"{self.base_url}/v1/messages",
                json={
                    "model": "claude-3-5-sonnet-20241022",
                    "max_tokens": 4096,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ]
                },
                timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()
            return data['content'][0]['text']

        except ImportError:
            raise RuntimeError("未安装requests库。请运行: pip install requests")
        except Exception as e:
            raise RuntimeError(f"HTTP请求失败: {str(e)}")


# 便捷函数
def create_claude_code_client(timeout: int = 60) -> ClaudeCodeProxyClient:
    """
    创建Claude Code代理客户端（便捷函数）

    Args:
        timeout: 超时时间（秒）

    Returns:
        ClaudeCodeProxyClient实例

    Example:
        >>> client = create_claude_code_client()
        >>> if client.is_available():
        ...     response = client.ask("Hello!")
    """
    return ClaudeCodeProxyClient(timeout=timeout)


def test_claude_code_connection() -> tuple[bool, str]:
    """
    测试Claude Code连接

    Returns:
        (是否可用, 状态消息)

    Example:
        >>> available, message = test_claude_code_connection()
        >>> print(message)
    """
    client = ClaudeCodeProxyClient()

    if not client.is_available():
        return False, (
            "Claude Code不可用。请确保：\n"
            "1. Claude Code已正确安装\n"
            "2. 您当前在Claude Code会话中\n"
            "3. claude-code命令在PATH中"
        )

    # 发送测试请求
    try:
        response = client.ask("测试连接，请回复'OK'")
        if response:
            return True, f"✓ Claude Code连接成功\n响应: {response[:100]}..."
        else:
            return False, "✗ Claude Code未响应"

    except Exception as e:
        return False, f"✗ 测试失败: {str(e)}"


# 示例用法
if __name__ == "__main__":
    print("=== Claude Code代理客户端测试 ===\n")

    # 1. 检查可用性
    print("1. 检查Claude Code可用性:")
    client = ClaudeCodeProxyClient()

    if client.is_available():
        print("   ✓ Claude Code可用\n")

        # 2. 发送测试请求
        print("2. 发送测试请求:")
        try:
            response = client.ask("你好，请用一句话介绍你自己。")
            print(f"   响应: {response[:200]}...")
            print("   ✓ 测试成功\n")
        except Exception as e:
            print(f"   ✗ 测试失败: {str(e)}\n")

        # 3. 测试带上下文的请求
        print("3. 测试上下文文件:")
        try:
            # 创建测试文件
            test_file = tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.log',
                delete=False
            )
            test_file.write("[ERROR] Test error message\n")
            test_file.close()

            response = client.ask(
                "这个日志文件有什么问题？",
                context_files=[test_file.name]
            )
            print(f"   响应: {response[:200]}...")
            print("   ✓ 上下文测试成功\n")

            # 清理测试文件
            os.unlink(test_file.name)

        except Exception as e:
            print(f"   ✗ 上下文测试失败: {str(e)}\n")

    else:
        print("   ✗ Claude Code不可用")
        print("   请确保Claude Code正在运行且您在会话中\n")

    # 4. 测试HTTP API（如果可用）
    print("4. 测试HTTP API:")
    http_client = ClaudeCodeHTTPClient()

    if http_client.is_available():
        print("   ✓ HTTP API可用")
        try:
            response = http_client.ask("Hello!")
            print(f"   响应: {response[:100]}...")
            print("   ✓ HTTP测试成功\n")
        except Exception as e:
            print(f"   ✗ HTTP测试失败: {str(e)}\n")
    else:
        print("   ✗ HTTP API不可用（这是正常的，大多数情况下使用CLI）\n")

    # 5. 综合连接测试
    print("5. 综合连接测试:")
    available, message = test_claude_code_connection()
    print(f"   {message}\n")

    print("=== 测试完成 ===")
