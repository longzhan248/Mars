"""
字符串字面量保护器

在代码解析前提取字符串字面量，用占位符替换，避免字符串中的代码关键字被误识别。
"""

import re
from typing import Dict


class StringLiteralProtector:
    """
    字符串字面量保护器

    在代码解析前提取字符串字面量，用占位符替换，避免字符串中的代码关键字被误识别。
    解析完成后可以恢复原始字符串。
    """

    def __init__(self):
        """初始化保护器"""
        self.string_map: Dict[str, str] = {}  # {占位符: 原始字符串}
        self.placeholder_counter = 0

    def protect(self, code: str, language: str = "objc") -> str:
        """
        保护代码中的字符串字面量

        Args:
            code: 原始代码
            language: 语言类型 ("objc" 或 "swift")

        Returns:
            str: 字符串被占位符替换后的代码
        """
        self.string_map.clear()
        self.placeholder_counter = 0

        if language == "objc":
            return self._protect_objc_strings(code)
        elif language == "swift":
            return self._protect_swift_strings(code)
        else:
            return code

    def restore(self, code: str) -> str:
        """
        恢复代码中的字符串字面量

        Args:
            code: 包含占位符的代码

        Returns:
            str: 恢复原始字符串后的代码
        """
        restored = code
        for placeholder, original in self.string_map.items():
            restored = restored.replace(placeholder, original)
        return restored

    def _protect_objc_strings(self, code: str) -> str:
        """
        保护Objective-C字符串字面量

        支持格式:
        - @"string"
        - @"string with \"escaped\" quotes"
        """
        # 匹配Objective-C字符串: @"..."
        # 需要处理转义的引号
        pattern = r'@"(?:[^"\\]|\\.)*"'

        def replace_match(match):
            original_string = match.group(0)
            placeholder = f"__STRING_PLACEHOLDER_{self.placeholder_counter}__"
            self.string_map[placeholder] = original_string
            self.placeholder_counter += 1
            return placeholder

        return re.sub(pattern, replace_match, code)

    def _protect_swift_strings(self, code: str) -> str:
        """
        保护Swift字符串字面量

        支持格式:
        - "string"
        - "string with \"escaped\" quotes"
        - 多行字符串需要特殊处理（已在Swift解析器中处理）
        """
        # 匹配Swift字符串: "..."
        # 需要处理转义的引号
        pattern = r'"(?:[^"\\]|\\.)*"'

        def replace_match(match):
            original_string = match.group(0)
            placeholder = f"__STRING_PLACEHOLDER_{self.placeholder_counter}__"
            self.string_map[placeholder] = original_string
            self.placeholder_counter += 1
            return placeholder

        return re.sub(pattern, replace_match, code)
