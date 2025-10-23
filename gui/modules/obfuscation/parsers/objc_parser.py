"""
Objective-C代码解析器
"""

import re
from pathlib import Path
from typing import List, Optional

from .common import ParsedFile, Symbol, SymbolType
from .string_protector import StringLiteralProtector


class ObjCParser:
    """Objective-C代码解析器"""

    # 正则表达式模式
    INTERFACE_PATTERN = r'@interface\s+(\w+)\s*(?::\s*(\w+))?\s*(?:<([^>]+)>)?'
    IMPLEMENTATION_PATTERN = r'@implementation\s+(\w+)\s*(?:\((\w+)\))?'
    PROTOCOL_PATTERN = r'@protocol\s+(\w+)'
    CATEGORY_PATTERN = r'@interface\s+(\w+)\s*\((\w+)\)'
    # 修复：支持有attributes和无attributes两种property格式
    # 1. @property (nonatomic, strong) NSString *name;
    # 2. @property NSString *name;
    PROPERTY_PATTERN = r'@property\s*(?:\([^)]*\))?\s*([^;]+);'
    METHOD_PATTERN = r'^[\s]*([+-])\s*\(([^)]+)\)\s*([^;{]+)'
    # 修复：支持两种enum格式
    # 1. typedef enum { ... } Name;
    # 2. typedef NS_ENUM(Type, Name) { ... };
    ENUM_PATTERN_OLD = r'typedef\s+enum\s+\w*\s*{[^}]+}\s*(\w+);'
    ENUM_PATTERN_NS = r'typedef\s+NS_ENUM\s*\([^,]+,\s*(\w+)\s*\)'
    MACRO_PATTERN = r'#define\s+(\w+)(?:\(([^)]*)\))?\s+(.+)'
    TYPEDEF_PATTERN = r'typedef\s+(.+)\s+(\w+);'
    IVAR_PATTERN = r'^\s*([^@/\n]+)\s+(\w+);'

    def __init__(self, whitelist_manager=None):
        """
        初始化Objective-C解析器

        Args:
            whitelist_manager: 白名单管理器（用于过滤系统API）
        """
        self.whitelist_manager = whitelist_manager
        self.current_class = None
        self.in_interface = False
        self.in_implementation = False
        self.in_protocol = False  # 追踪是否在protocol定义内

    def parse_file(self, file_path: str) -> ParsedFile:
        """
        解析Objective-C文件

        Args:
            file_path: 文件路径

        Returns:
            ParsedFile: 解析结果
        """
        parsed = ParsedFile(file_path=file_path, language="objc")

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # 字符串字面量保护：提取字符串避免误识别
            protector = StringLiteralProtector()
            protected_content = protector.protect(content, language="objc")

            # 重新分行处理
            lines = protected_content.splitlines(keepends=True)

            self._reset_state()

            # 多行注释状态追踪
            in_multiline_comment = False
            # Objective-C反斜杠续行状态追踪
            in_continuation = False
            continuation_buffer = ""

            for i, line in enumerate(lines, 1):
                line_stripped = line.strip()

                # 跳过空行
                if not line_stripped:
                    continue

                # 处理Objective-C反斜杠续行 (字符串或宏定义)
                if in_continuation:
                    continuation_buffer += line_stripped
                    if not line.rstrip().endswith('\\'):
                        # 续行结束，跳过整个续行内容
                        in_continuation = False
                        continuation_buffer = ""
                    continue

                if line.rstrip().endswith('\\'):
                    # 开始续行
                    in_continuation = True
                    continuation_buffer = line_stripped
                    continue

                # 处理多行注释
                if '/*' in line and '*/' not in line:
                    in_multiline_comment = True
                    continue
                if in_multiline_comment:
                    if '*/' in line:
                        in_multiline_comment = False
                    continue

                # 跳过单行注释
                if line_stripped.startswith('//'):
                    continue

                # 解析import
                if line_stripped.startswith('#import') or line_stripped.startswith('#include'):
                    self._parse_import(line_stripped, parsed)
                    continue

                # 解析@class前置声明
                if line_stripped.startswith('@class'):
                    self._parse_forward_declaration(line_stripped, parsed)
                    continue

                # 解析@interface
                if '@interface' in line_stripped:
                    symbol = self._parse_interface(line_stripped, file_path, i, line)
                    if symbol:
                        parsed.symbols.append(symbol)
                        self.current_class = symbol.name
                        self.in_interface = True
                    continue

                # 解析@implementation
                if '@implementation' in line_stripped:
                    symbol = self._parse_implementation(line_stripped, file_path, i, line)
                    if symbol:
                        self.current_class = symbol.name
                        self.in_implementation = True
                    continue

                # 解析@protocol
                if '@protocol' in line_stripped:
                    symbol = self._parse_protocol(line_stripped, file_path, i, line)
                    if symbol:
                        parsed.symbols.append(symbol)
                        self.current_class = symbol.name
                        self.in_protocol = True
                    continue

                # 解析@end
                if '@end' in line_stripped:
                    self.current_class = None
                    self.in_interface = False
                    self.in_implementation = False
                    self.in_protocol = False
                    continue

                # 在interface、implementation或protocol块内
                if self.current_class:
                    # 解析@property
                    if '@property' in line_stripped:
                        symbol = self._parse_property(line_stripped, file_path, i, line)
                        if symbol:
                            symbol.parent = self.current_class
                            parsed.symbols.append(symbol)
                        continue

                    # 解析方法声明
                    if line_stripped.startswith(('+', '-')):
                        symbol = self._parse_method(line_stripped, file_path, i, line)
                        if symbol:
                            symbol.parent = self.current_class
                            parsed.symbols.append(symbol)
                        continue

                # 解析typedef enum (支持 typedef enum 和 typedef NS_ENUM)
                if 'typedef' in line_stripped and ('enum' in line_stripped or 'NS_ENUM' in line_stripped):
                    symbols = self._parse_enum(line_stripped, file_path, i, line)
                    parsed.symbols.extend(symbols)
                    continue

                # 解析#define宏
                if line_stripped.startswith('#define'):
                    symbol = self._parse_macro(line_stripped, file_path, i, line)
                    if symbol:
                        parsed.symbols.append(symbol)
                    continue

                # 解析typedef
                if line_stripped.startswith('typedef') and 'enum' not in line_stripped:
                    symbol = self._parse_typedef(line_stripped, file_path, i, line)
                    if symbol:
                        parsed.symbols.append(symbol)
                    continue

        except Exception as e:
            print(f"解析文件失败 {file_path}: {e}")

        return parsed

    def _reset_state(self):
        """重置解析器状态"""
        self.current_class = None
        self.in_interface = False
        self.in_implementation = False
        self.in_protocol = False

    def _parse_import(self, line: str, parsed: ParsedFile):
        """解析import语句"""
        # #import <UIKit/UIKit.h> 或 #import "MyClass.h"
        match = re.search(r'#import\s+[<"]([^>"]+)[>"]', line)
        if match:
            import_name = match.group(1)
            # 去掉路径，只保留文件名
            import_name = import_name.split('/')[-1].replace('.h', '')
            parsed.imports.add(import_name)

    def _parse_forward_declaration(self, line: str, parsed: ParsedFile):
        """解析前置声明 @class Foo, Bar;"""
        match = re.search(r'@class\s+([^;]+);', line)
        if match:
            classes = match.group(1).split(',')
            for cls in classes:
                parsed.forward_declarations.add(cls.strip())

    def _parse_interface(self, line: str, file_path: str, line_num: int, original: str) -> Optional[Symbol]:
        """解析@interface"""
        match = re.search(self.INTERFACE_PATTERN, line)
        if match:
            class_name = match.group(1)

            # 检查是否是Category
            if '(' in line and ')' in line:
                return self._parse_category(line, file_path, line_num, original)

            # 检查白名单
            if self._is_whitelisted(class_name, SymbolType.CLASS):
                return None

            parent_class = match.group(2) if match.group(2) else None
            # protocols = match.group(3) if match.group(3) else None  # TODO: 支持协议信息

            return Symbol(
                name=class_name,
                type=SymbolType.CLASS,
                file_path=file_path,
                line_number=line_num,
                original_line=original.strip(),
                parent=parent_class
            )
        return None

    def _parse_category(self, line: str, file_path: str, line_num: int, original: str) -> Optional[Symbol]:
        """解析Category"""
        match = re.search(self.CATEGORY_PATTERN, line)
        if match:
            class_name = match.group(1)
            category_name = match.group(2)

            # Category符号名称: ClassName+CategoryName
            symbol_name = f"{class_name}+{category_name}"

            return Symbol(
                name=symbol_name,
                type=SymbolType.CATEGORY,
                file_path=file_path,
                line_number=line_num,
                original_line=original.strip(),
                parent=class_name
            )
        return None

    def _parse_implementation(self, line: str, file_path: str, line_num: int, original: str) -> Optional[Symbol]:
        """解析@implementation"""
        match = re.search(self.IMPLEMENTATION_PATTERN, line)
        if match:
            class_name = match.group(1)
            category_name = match.group(2) if match.group(2) else None

            if category_name:
                # Category implementation
                return Symbol(
                    name=f"{class_name}+{category_name}",
                    type=SymbolType.CATEGORY,
                    file_path=file_path,
                    line_number=line_num,
                    original_line=original.strip()
                )
            else:
                # 普通类implementation（不需要加入symbols，因为interface已经定义）
                return Symbol(
                    name=class_name,
                    type=SymbolType.CLASS,
                    file_path=file_path,
                    line_number=line_num,
                    original_line=original.strip()
                )
        return None

    def _parse_protocol(self, line: str, file_path: str, line_num: int, original: str) -> Optional[Symbol]:
        """解析@protocol"""
        match = re.search(self.PROTOCOL_PATTERN, line)
        if match:
            protocol_name = match.group(1)

            if self._is_whitelisted(protocol_name, SymbolType.PROTOCOL):
                return None

            return Symbol(
                name=protocol_name,
                type=SymbolType.PROTOCOL,
                file_path=file_path,
                line_number=line_num,
                original_line=original.strip()
            )
        return None

    def _parse_property(self, line: str, file_path: str, line_num: int, original: str) -> Optional[Symbol]:
        """解析@property"""
        match = re.search(self.PROPERTY_PATTERN, line)
        if match:
            # 解析属性类型和名称
            declaration = match.group(1).strip()

            # P1修复增强: 使用正则表达式精确提取属性名
            # 支持多种格式:
            # 1. 普通类型: NSString *name, NSString* name, NSString * name, NSString*name
            # 2. Block类型: void (^completion)(BOOL)

            property_name = None
            property_type = None

            # 先检查是否是Block类型 (^blockName)
            block_match = re.search(r'\(\^(\w+)\)', declaration)
            if block_match:
                property_name = block_match.group(1)
                property_type = declaration
            else:
                # 普通类型: 匹配最后一个单词（不包含*号）
                prop_match = re.search(r'\*?\s*(\w+)\s*$', declaration)
                if prop_match:
                    property_name = prop_match.group(1)
                    property_type = declaration[:prop_match.start()].strip()

            if property_name:
                if self._is_whitelisted(property_name, SymbolType.PROPERTY):
                    return None

                return Symbol(
                    name=property_name,
                    type=SymbolType.PROPERTY,
                    file_path=file_path,
                    line_number=line_num,
                    original_line=original.strip(),
                    return_type=property_type or ""
                )
        return None

    def _parse_method(self, line: str, file_path: str, line_num: int, original: str) -> Optional[Symbol]:
        """解析方法声明"""
        match = re.search(self.METHOD_PATTERN, line, re.MULTILINE)
        if match:
            method_type = match.group(1)  # + 或 -
            return_type = match.group(2).strip()
            method_signature = match.group(3).strip()

            # 提取方法名和参数
            method_name = self._extract_method_name(method_signature)

            if self._is_whitelisted(method_name, SymbolType.METHOD):
                return None

            # 提取参数名
            parameters = self._extract_parameters(method_signature)

            return Symbol(
                name=method_name,
                type=SymbolType.METHOD,
                file_path=file_path,
                line_number=line_num,
                original_line=original.strip(),
                return_type=return_type,
                parameters=parameters,
                is_static=(method_type == '+')
            )
        return None

    def _extract_method_name(self, signature: str) -> str:
        """
        提取方法名
        例如: "initWithFrame:(CGRect)frame" -> "initWithFrame:"
              "method:(Type1)arg1 with:(Type2)arg2 and:(Type3)arg3" -> "method:with:and:"
              "doSomething" -> "doSomething"
        """
        # 方法1: 如果没有冒号，就是无参方法
        if ':' not in signature:
            # 无参方法: 直接返回第一个单词
            match = re.match(r'(\w+)', signature)
            return match.group(1) if match else signature.strip()

        # 方法2: 有参数的方法，提取所有方法名部分（冒号前的单词）
        # 匹配模式: 单词+冒号+参数类型+参数名
        # 例如: "initWithFrame:(CGRect)frame" -> "initWithFrame:"
        #      "with:(NSString*)title" -> "with:"
        method_parts = []

        # 提取所有 "word:" 模式（方法名的各个部分）
        # 使用非贪婪匹配，确保只提取冒号前的单词
        parts = re.findall(r'(\w+):\s*(?:\([^)]*\)\s*)?(?:\w+)?', signature)

        for part in parts:
            method_parts.append(f"{part}:")

        return ''.join(method_parts) if method_parts else signature.strip()

    def _extract_parameters(self, signature: str) -> List[str]:
        """
        提取参数名列表
        例如: "initWithFrame:(CGRect)frame style:(UITableViewStyle)style"
              -> ["frame", "style"]
        """
        parameters = []
        # 匹配 :(...) paramName 模式
        matches = re.findall(r':\([^)]+\)\s*(\w+)', signature)
        parameters.extend(matches)
        return parameters

    def _parse_enum(self, line: str, file_path: str, line_num: int, original: str) -> List[Symbol]:
        """
        解析typedef enum
        支持两种格式:
        1. typedef enum { ... } Name;
        2. typedef NS_ENUM(Type, Name) { ... };
        """
        symbols = []

        # 先尝试NS_ENUM格式
        match = re.search(self.ENUM_PATTERN_NS, line)
        if match:
            enum_name = match.group(1)
            if not self._is_whitelisted(enum_name, SymbolType.ENUM):
                symbols.append(Symbol(
                    name=enum_name,
                    type=SymbolType.ENUM,
                    file_path=file_path,
                    line_number=line_num,
                    original_line=original.strip()
                ))
            return symbols

        # 再尝试旧式enum格式
        match = re.search(self.ENUM_PATTERN_OLD, line)
        if match:
            enum_name = match.group(1)
            if not self._is_whitelisted(enum_name, SymbolType.ENUM):
                symbols.append(Symbol(
                    name=enum_name,
                    type=SymbolType.ENUM,
                    file_path=file_path,
                    line_number=line_num,
                    original_line=original.strip()
                ))

        return symbols

    def _parse_macro(self, line: str, file_path: str, line_num: int, original: str) -> Optional[Symbol]:
        """解析#define宏定义"""
        match = re.search(self.MACRO_PATTERN, line)
        if match:
            macro_name = match.group(1)

            # 跳过常见的系统宏
            if macro_name.startswith(('NS_', 'UI_', 'CF_', '__')):
                return None

            if self._is_whitelisted(macro_name, SymbolType.MACRO):
                return None

            return Symbol(
                name=macro_name,
                type=SymbolType.MACRO,
                file_path=file_path,
                line_number=line_num,
                original_line=original.strip()
            )
        return None

    def _parse_typedef(self, line: str, file_path: str, line_num: int, original: str) -> Optional[Symbol]:
        """解析typedef"""
        match = re.search(self.TYPEDEF_PATTERN, line)
        if match:
            typedef_name = match.group(2)

            if not self._is_whitelisted(typedef_name, SymbolType.TYPEDEF):
                return Symbol(
                    name=typedef_name,
                    type=SymbolType.TYPEDEF,
                    file_path=file_path,
                    line_number=line_num,
                    original_line=original.strip(),
                    return_type=match.group(1).strip()
                )
        return None

    def _is_whitelisted(self, name: str, symbol_type: SymbolType) -> bool:
        """检查是否在白名单中"""
        if not self.whitelist_manager:
            return False

        # 根据符号类型判断
        if symbol_type == SymbolType.CLASS:
            return self.whitelist_manager.is_whitelisted(name)
        elif symbol_type == SymbolType.METHOD:
            return self.whitelist_manager.is_whitelisted(name)
        elif symbol_type == SymbolType.PROPERTY:
            return self.whitelist_manager.is_whitelisted(name)
        else:
            return False
