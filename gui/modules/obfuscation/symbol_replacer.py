"""
符号替换器 - 负责执行各种符号的替换操作
从 code_transformer.py 中提取，专注于符号替换逻辑
"""

import re
from typing import Tuple

try:
    from .code_parser import Symbol, SymbolType
except ImportError:
    from code_parser import Symbol, SymbolType


class SymbolReplacer:
    """符号替换器 - 处理各种类型符号的替换"""

    def __init__(self, symbol_mappings: dict):
        """
        初始化符号替换器

        Args:
            symbol_mappings: 符号映射字典 {原始名: 混淆名}
        """
        self.symbol_mappings = symbol_mappings

    def replace_class_name(self, content: str, symbol: Symbol) -> Tuple[str, int]:
        """
        替换类名

        Args:
            content: 文件内容
            symbol: 类符号

        Returns:
            (替换后内容, 替换次数)
        """
        if symbol.name not in self.symbol_mappings:
            return content, 0

        obfuscated_name = self.symbol_mappings[symbol.name]
        count = 0

        # 1. @interface/@implementation声明
        patterns = [
            # @interface ClassName : SuperClass
            (rf'(@interface\s+){re.escape(symbol.name)}(\s*[:\(<])',
             rf'\1{obfuscated_name}\2'),
            # @implementation ClassName
            (rf'(@implementation\s+){re.escape(symbol.name)}(\s*[(\n{{])',
             rf'\1{obfuscated_name}\2'),
            # @interface ClassName ()
            (rf'(@interface\s+){re.escape(symbol.name)}(\s*\(\))',
             rf'\1{obfuscated_name}\2'),
        ]

        for pattern, replacement in patterns:
            new_content = re.sub(pattern, replacement, content)
            if new_content != content:
                count += len(re.findall(pattern, content))
                content = new_content

        # 2. 类型声明和变量声明
        # ClassName *variable 或 ClassName<Protocol> *variable
        type_pattern = rf'\b{re.escape(symbol.name)}\b(?=\s*[*<\s])'
        matches = re.findall(type_pattern, content)
        if matches:
            content = re.sub(type_pattern, obfuscated_name, content)
            count += len(matches)

        # 3. alloc/new等类方法调用
        # [ClassName alloc] 或 [ClassName new]
        class_method_pattern = rf'\[{re.escape(symbol.name)}\s+(alloc|new|class|superclass)'
        matches = re.findall(class_method_pattern, content)
        if matches:
            content = re.sub(
                rf'\[{re.escape(symbol.name)}\s+',
                f'[{obfuscated_name} ',
                content
            )
            count += len(matches)

        return content, count

    def replace_protocol_name(self, content: str, symbol: Symbol) -> Tuple[str, int]:
        """
        替换协议名

        Args:
            content: 文件内容
            symbol: 协议符号

        Returns:
            (替换后内容, 替换次数)
        """
        if symbol.name not in self.symbol_mappings:
            return content, 0

        obfuscated_name = self.symbol_mappings[symbol.name]
        count = 0

        # 1. @protocol声明
        protocol_pattern = rf'(@protocol\s+){re.escape(symbol.name)}(\s)'
        matches = re.findall(protocol_pattern, content)
        if matches:
            content = re.sub(protocol_pattern, rf'\1{obfuscated_name}\2', content)
            count += len(matches)

        # 2. 协议遵守声明 <ProtocolName>
        conform_pattern = rf'<([^>]*\b){re.escape(symbol.name)}\b([^>]*)>'
        matches = re.findall(conform_pattern, content)
        if matches:
            content = re.sub(
                rf'\b{re.escape(symbol.name)}\b(?=[^>]*>)',
                obfuscated_name,
                content
            )
            count += len(matches)

        return content, count

    def replace_method_name(self, content: str, symbol: Symbol) -> Tuple[str, int]:
        """
        替换方法名

        Args:
            content: 文件内容
            symbol: 方法符号

        Returns:
            (替换后内容, 替换次数)
        """
        if symbol.name not in self.symbol_mappings:
            return content, 0

        obfuscated_name = self.symbol_mappings[symbol.name]
        count = 0

        # 分析方法签名
        parts = symbol.name.split(':')

        if len(parts) == 1:
            # 无参数方法: doSomething
            # 1. 方法声明/实现
            decl_pattern = rf'([-+]\s*\([^)]+\)\s*){re.escape(symbol.name)}(\s*[;{{])'
            matches = re.findall(decl_pattern, content)
            if matches:
                content = re.sub(decl_pattern, rf'\1{obfuscated_name}\2', content)
                count += len(matches)

            # 2. 方法调用
            call_pattern = rf'(\]\s*){re.escape(symbol.name)}(\s*\])'
            matches = re.findall(call_pattern, content)
            if matches:
                content = re.sub(call_pattern, rf'\1{obfuscated_name}\2', content)
                count += len(matches)

        else:
            # 有参数方法: doSomething:withParam:
            obf_parts = obfuscated_name.split(':')

            # 逐个替换每个参数部分
            for i, part in enumerate(parts[:-1]):  # 最后一个空字符串不处理
                if i < len(obf_parts):
                    obf_part = obf_parts[i]

                    # 方法声明/实现中的参数名
                    decl_pattern = rf'\b{re.escape(part)}:'
                    matches = re.findall(decl_pattern, content)
                    if matches:
                        content = re.sub(decl_pattern, f'{obf_part}:', content)
                        count += len(matches)

        return content, count

    def replace_property_name(self, content: str, symbol: Symbol) -> Tuple[str, int]:
        """
        替换属性名

        Args:
            content: 文件内容
            symbol: 属性符号

        Returns:
            (替换后内容, 替换次数)
        """
        if symbol.name not in self.symbol_mappings:
            return content, 0

        obfuscated_name = self.symbol_mappings[symbol.name]
        count = 0

        # 1. @property声明
        property_pattern = rf'(@property[^;]*\s+){re.escape(symbol.name)}(\s*;)'
        matches = re.findall(property_pattern, content)
        if matches:
            content = re.sub(property_pattern, rf'\1{obfuscated_name}\2', content)
            count += len(matches)

        # 2. @synthesize声明
        synthesize_pattern = rf'(@synthesize\s+){re.escape(symbol.name)}(\s*[;=])'
        matches = re.findall(synthesize_pattern, content)
        if matches:
            content = re.sub(synthesize_pattern, rf'\1{obfuscated_name}\2', content)
            count += len(matches)

        # 3. 属性访问: self.propertyName 或 object.propertyName
        access_pattern = rf'(\.\s*){re.escape(symbol.name)}\b'
        matches = re.findall(access_pattern, content)
        if matches:
            content = re.sub(access_pattern, rf'\1{obfuscated_name}', content)
            count += len(matches)

        # 4. 成员变量声明: 如果有下划线前缀
        if symbol.name.startswith('_'):
            ivar_pattern = rf'\b{re.escape(symbol.name)}\b'
            matches = re.findall(ivar_pattern, content)
            if matches:
                content = re.sub(ivar_pattern, obfuscated_name, content)
                count += len(matches)

        return content, count

    def replace_macro_name(self, content: str, symbol: Symbol) -> Tuple[str, int]:
        """
        替换宏定义名

        Args:
            content: 文件内容
            symbol: 宏符号

        Returns:
            (替换后内容, 替换次数)
        """
        if symbol.name not in self.symbol_mappings:
            return content, 0

        obfuscated_name = self.symbol_mappings[symbol.name]
        count = 0

        # 1. #define声明
        define_pattern = rf'(#define\s+){re.escape(symbol.name)}\b'
        matches = re.findall(define_pattern, content)
        if matches:
            content = re.sub(define_pattern, rf'\1{obfuscated_name}', content)
            count += len(matches)

        # 2. 宏使用
        usage_pattern = rf'\b{re.escape(symbol.name)}\b'
        # 排除#define行
        lines = content.split('\n')
        new_lines = []
        for line in lines:
            if not line.strip().startswith('#define'):
                matches = re.findall(usage_pattern, line)
                if matches:
                    line = re.sub(usage_pattern, obfuscated_name, line)
                    count += len(matches)
            new_lines.append(line)
        content = '\n'.join(new_lines)

        return content, count

    def update_import_statements(self, content: str) -> Tuple[str, int]:
        """
        更新import语句中的类名引用

        Args:
            content: 文件内容

        Returns:
            (更新后内容, 更新次数)
        """
        count = 0

        # #import "ClassName.h" 或 #import <Framework/ClassName.h>
        import_pattern = r'#import\s+[<"]([^>"]+)[>"]'

        def replace_import(match):
            nonlocal count
            import_path = match.group(1)

            # 提取文件名（不含扩展名）
            if '/' in import_path:
                parts = import_path.split('/')
                filename = parts[-1]
                prefix = '/'.join(parts[:-1]) + '/'
            else:
                filename = import_path
                prefix = ''

            # 检查是否有对应的映射
            if '.' in filename:
                name, ext = filename.rsplit('.', 1)
                if name in self.symbol_mappings:
                    new_name = self.symbol_mappings[name]
                    count += 1
                    quote = '"' if match.group(0).count('"') > 0 else '<>'
                    if quote == '<>':
                        return f'#import <{prefix}{new_name}.{ext}>'
                    else:
                        return f'#import "{prefix}{new_name}.{ext}"'

            return match.group(0)

        content = re.sub(import_pattern, replace_import, content)
        return content, count
