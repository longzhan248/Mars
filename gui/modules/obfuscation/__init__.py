"""
iOS代码混淆模块

支持iOS项目的代码混淆，包括类名、方法名、属性名等的自动混淆。
提供GUI和CLI两种使用方式，支持Jenkins等CI/CD集成。
"""

__version__ = '1.0.0'
__author__ = 'Mars Log Analyzer Team'

# 导出重构后的主标签页
from .tab_main import ObfuscationTab

# 导出核心组件（保持向后兼容）
from .config_manager import ConfigManager, ObfuscationConfig
from .name_generator import NameGenerator, NamingStrategy
from .whitelist_manager import SystemAPIWhitelist, WhitelistManager

__all__ = [
    'ObfuscationTab',  # 新增：重构后的主标签页
    'ConfigManager',
    'ObfuscationConfig',
    'WhitelistManager',
    'SystemAPIWhitelist',
    'NameGenerator',
    'NamingStrategy',
]
