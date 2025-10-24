"""
白名单管理面板 - 统一入口
委托给符号白名单管理器和字符串白名单管理器
"""

import os
from .symbol_whitelist_manager import SymbolWhitelistManager
from .string_whitelist_manager import StringWhitelistManager


class WhitelistManager:
    """
    白名单管理器统一入口
    委托给专门的符号和字符串白名单管理器
    """

    def __init__(self, parent, tab_main):
        """
        初始化白名单管理器

        Args:
            parent: 父窗口
            tab_main: ObfuscationTab主控制器实例
        """
        self.parent = parent
        self.tab_main = tab_main

        # 获取白名单文件路径
        self.custom_whitelist_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'custom_whitelist.json'
        )

        # 创建专门的管理器
        self.symbol_manager = SymbolWhitelistManager(
            parent, tab_main, self.custom_whitelist_path
        )
        self.string_manager = StringWhitelistManager(
            parent, tab_main, self.custom_whitelist_path
        )

    def manage_symbol_whitelist(self):
        """管理符号白名单 - 委托给符号白名单管理器"""
        self.symbol_manager.manage_symbol_whitelist()

    def manage_string_whitelist(self):
        """管理字符串白名单 - 委托给字符串白名单管理器"""
        self.string_manager.manage_string_whitelist()
