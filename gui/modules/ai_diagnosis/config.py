"""
AI配置管理模块

提供AI服务的配置管理，支持：
- 配置文件持久化（JSON格式）
- 环境变量支持（API Key）
- 默认配置管理
- 配置验证
"""

import json
import os
from typing import Dict, Optional


class AIConfig:
    """AI配置管理类"""

    # 配置文件路径（相对于项目根目录）
    CONFIG_FILE = "gui/ai_config.json"

    # 默认配置（仅支持Claude Code）
    DEFAULT_CONFIG = {
        # AI服务配置 - 固定使用Claude Code
        "ai_service": "ClaudeCode",  # 仅支持ClaudeCode
        "claude_path": "",            # claude命令路径（可选，留空自动检测）

        # 功能开关
        "auto_detect": False,         # 关闭自动检测（只有一个选项）
        "auto_summary": False,        # 加载日志后自动生成摘要
        "privacy_filter": True,       # 启用隐私信息过滤

        # 性能配置
        "max_tokens": 10000,          # 日志摘要最大Token数
        "timeout": 60,                # 请求超时时间（秒）
        "context_size": "标准",       # 上下文大小：简化/标准/详细

        # UI配置
        "show_ai_panel": True,        # 显示AI助手面板
        "ai_panel_width": 350,        # AI面板宽度（像素）
        "show_token_usage": True,     # 显示Token使用情况

        # 项目代码配置
        "project_dirs": [],           # 项目代码目录列表
    }

    # Claude Code不需要环境变量
    ENV_VARS = {}

    @classmethod
    def load(cls) -> Dict:
        """
        加载配置文件

        Returns:
            配置字典

        Example:
            >>> config = AIConfig.load()
            >>> print(config['ai_service'])
            'ClaudeCode'
        """
        config_path = cls._get_config_path()

        # 如果配置文件存在，读取并合并
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    # 合并默认配置（处理新增字段）
                    config = cls.DEFAULT_CONFIG.copy()
                    config.update(user_config)
                    return config
            except Exception as e:
                print(f"警告: 读取配置文件失败: {e}")
                print("使用默认配置")

        # 返回默认配置的副本
        return cls.DEFAULT_CONFIG.copy()

    @classmethod
    def save(cls, config: Dict) -> bool:
        """
        保存配置文件

        Args:
            config: 配置字典

        Returns:
            保存是否成功

        Example:
            >>> config = AIConfig.load()
            >>> config['ai_service'] = 'Claude'
            >>> AIConfig.save(config)
            True
        """
        config_path = cls._get_config_path()

        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(config_path), exist_ok=True)

            # 写入JSON文件
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            return True
        except Exception as e:
            print(f"错误: 保存配置文件失败: {e}")
            return False

    @classmethod
    def get_api_key(cls, service: str, config: Optional[Dict] = None) -> str:
        """
        获取API Key（优先环境变量，其次配置文件）

        Args:
            service: 服务类型（"Claude", "OpenAI"）
            config: 配置字典（可选，不提供则自动加载）

        Returns:
            API Key字符串，如果未找到返回空字符串

        Example:
            >>> api_key = AIConfig.get_api_key("Claude")
            >>> if api_key:
            ...     print("API Key已配置")
        """
        # 1. 优先从环境变量读取
        env_var_name = cls.ENV_VARS.get(service)
        if env_var_name:
            env_key = os.getenv(env_var_name)
            if env_key:
                return env_key

        # 2. 从配置文件读取
        if config is None:
            config = cls.load()

        return config.get('api_key', '')

    @classmethod
    def validate(cls, config: Dict) -> tuple[bool, str]:
        """
        验证配置的有效性

        Args:
            config: 配置字典

        Returns:
            (是否有效, 错误信息)

        Example:
            >>> config = {'ai_service': 'Unknown'}
            >>> valid, error = AIConfig.validate(config)
            >>> if not valid:
            ...     print(f"配置错误: {error}")
        """
        # 检查必需字段
        required_fields = ['ai_service', 'model', 'timeout']
        for field in required_fields:
            if field not in config:
                return False, f"缺少必需字段: {field}"

        # 只支持ClaudeCode
        if config['ai_service'] != 'ClaudeCode':
            return False, f"仅支持Claude Code服务"

        # 检查timeout范围
        timeout = config.get('timeout', 60)
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            return False, "timeout必须为正数"

        # 检查max_tokens范围
        max_tokens = config.get('max_tokens', 10000)
        if not isinstance(max_tokens, int) or max_tokens <= 0:
            return False, "max_tokens必须为正整数"

        # Claude Code不需要API Key
        return True, ""

    @classmethod
    def reset_to_default(cls) -> Dict:
        """
        重置为默认配置

        Returns:
            默认配置字典

        Example:
            >>> config = AIConfig.reset_to_default()
            >>> AIConfig.save(config)
        """
        config = cls.DEFAULT_CONFIG.copy()
        cls.save(config)
        return config

    @classmethod
    def _get_config_path(cls) -> str:
        """
        获取配置文件的绝对路径

        Returns:
            配置文件绝对路径
        """
        # 获取项目根目录
        current_dir = os.path.dirname(os.path.abspath(__file__))  # gui/modules/ai_diagnosis/
        modules_dir = os.path.dirname(current_dir)  # gui/modules/
        gui_dir = os.path.dirname(modules_dir)  # gui/
        project_root = os.path.dirname(gui_dir)  # 项目根目录

        return os.path.join(project_root, cls.CONFIG_FILE)

    @classmethod
    def get_model_list(cls, service: str) -> list:
        """
        获取指定服务支持的模型列表

        Args:
            service: 服务类型

        Returns:
            模型名称列表
        """
        # 只支持Claude Code
        return ["claude-3-5-sonnet-20241022"]

    @classmethod
    def get_display_name(cls, service: str) -> str:
        """
        获取服务的显示名称

        Args:
            service: 服务类型

        Returns:
            显示名称
        """
        return "Claude Code"


# 便捷函数
def load_config() -> Dict:
    """加载配置（便捷函数）"""
    return AIConfig.load()


def save_config(config: Dict) -> bool:
    """保存配置（便捷函数）"""
    return AIConfig.save(config)


def get_api_key(service: str) -> str:
    """获取API Key（便捷函数）"""
    return AIConfig.get_api_key(service)


# 示例用法
if __name__ == "__main__":
    # 1. 加载配置
    config = AIConfig.load()
    print(f"当前AI服务: {config['ai_service']}")
    print(f"当前模型: {config['model']}")

    # 2. 修改配置
    config['ai_service'] = 'Claude'
    config['model'] = 'claude-3-5-sonnet-20241022'

    # 3. 验证配置
    valid, error = AIConfig.validate(config)
    if valid:
        print("✓ 配置有效")
        # 4. 保存配置
        if AIConfig.save(config):
            print("✓ 配置已保存")
    else:
        print(f"✗ 配置无效: {error}")

    # 5. 获取API Key
    api_key = AIConfig.get_api_key('Claude')
    if api_key:
        print(f"✓ API Key已配置: {api_key[:8]}...")
    else:
        print("✗ 未配置API Key")

    # 6. 获取模型列表
    models = AIConfig.get_model_list('Claude')
    print(f"可用模型: {models}")
