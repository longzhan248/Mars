"""
iOS代码混淆模块

支持iOS项目的代码混淆，包括类名、方法名、属性名等的自动混淆。
提供GUI和CLI两种使用方式，支持Jenkins等CI/CD集成。
"""

__version__ = '1.0.0'
__author__ = 'Mars Log Analyzer Team'

from .config_manager import ConfigManager, ObfuscationConfig
from .name_generator import NameGenerator, NamingStrategy
from .whitelist_manager import SystemAPIWhitelist, WhitelistManager

__all__ = [
    'ConfigManager',
    'ObfuscationConfig',
    'WhitelistManager',
    'SystemAPIWhitelist',
    'NameGenerator',
    'NamingStrategy',
]
