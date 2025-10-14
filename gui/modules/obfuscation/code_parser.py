"""
代码解析器 - 负责解析Objective-C和Swift代码，提取符号信息

支持:
1. Objective-C解析（类、方法、属性、协议、枚举、宏定义）
2. Swift解析（class、struct、enum、protocol、property、method）
3. 符号提取和分类
4. 作用域分析
5. 引用关系追踪
"""

import re
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


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


class SymbolType(Enum):
    """符号类型"""
    CLASS = "class"                     # 类
    PROTOCOL = "protocol"               # 协议
    CATEGORY = "category"               # 分类
    EXTENSION = "extension"             # 扩展
    STRUCT = "struct"                   # 结构体
    ENUM = "enum"                       # 枚举
    METHOD = "method"                   # 方法
    PROPERTY = "property"               # 属性
    IVAR = "ivar"                       # 实例变量
    PARAMETER = "parameter"             # 参数
    LOCAL_VAR = "local_var"             # 局部变量
    CONSTANT = "constant"               # 常量
    MACRO = "macro"                     # 宏定义
    TYPEDEF = "typedef"                 # 类型定义


@dataclass
class Symbol:
    """符号信息"""
    name: str                           # 符号名称
    type: SymbolType                    # 符号类型
    file_path: str                      # 所在文件
    line_number: int                    # 行号
    original_line: str = ""             # 原始行内容
    parent: Optional[str] = None        # 父级符号（类名、方法名等）
    access_modifier: str = "public"     # 访问修饰符
    is_static: bool = False             # 是否静态
    return_type: str = ""               # 返回类型（方法）
    parameters: List[str] = field(default_factory=list)  # 参数列表
    references: Set[str] = field(default_factory=set)    # 引用的其他符号


@dataclass
class ParsedFile:
    """解析后的文件信息"""
    file_path: str                      # 文件路径
    language: str                       # 语言（objc/swift）
    symbols: List[Symbol] = field(default_factory=list)
    imports: Set[str] = field(default_factory=set)       # 导入的模块
    forward_declarations: Set[str] = field(default_factory=set)  # 前置声明


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
            protocols = match.group(3) if match.group(3) else None

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


class SwiftParser:
    """Swift代码解析器"""

    # 正则表达式模式
    # P1修复：增强泛型支持
    # 支持复杂泛型场景:
    # - class MyClass<T: Equatable>
    # - class MyClass<T: Codable & Equatable>
    # - class MyClass<T> where T: Collection, T.Element: Equatable
    # - class MyClass<T: Protocol, U: AnotherProtocol>

    # 泛型参数模式（支持嵌套泛型）
    # <T>, <T: Equatable>, <T, U>, <T: Codable & Equatable>, <Array<Int>>
    GENERIC_PARAM_PATTERN = r'<(?:[^<>]|<[^<>]*>)*>'

    # where子句模式
    # where T: Collection, T.Element: Equatable
    WHERE_CLAUSE_PATTERN = r'where\s+[^{]+'

    # 类/结构体/枚举模式（支持完整泛型约束和where子句）
    CLASS_PATTERN = r'(class|struct|enum)\s+(\w+)' + \
                    r'(?:' + GENERIC_PARAM_PATTERN + r')?' + \
                    r'(?:\s*:\s*([^{]+?))?' + \
                    r'(?:\s+' + WHERE_CLAUSE_PATTERN + r')?'

    # 协议模式（支持关联类型约束）
    # protocol MyProtocol: AnyObject where T: Equatable
    PROTOCOL_PATTERN = r'protocol\s+(\w+)' + \
                       r'(?:' + GENERIC_PARAM_PATTERN + r')?' + \
                       r'(?:\s*:\s*([^{]+?))?' + \
                       r'(?:\s+' + WHERE_CLAUSE_PATTERN + r')?'

    # 扩展模式（支持泛型约束）
    # extension MyClass<T> where T: Equatable
    EXTENSION_PATTERN = r'extension\s+(\w+)' + \
                        r'(?:' + GENERIC_PARAM_PATTERN + r')?' + \
                        r'(?:\s+' + WHERE_CLAUSE_PATTERN + r')?'

    # 属性模式（支持访问修饰符）
    PROPERTY_PATTERN = r'(?:public\s+|private\s+|internal\s+|fileprivate\s+|open\s+)?' + \
                       r'(var|let)\s+(\w+)\s*:\s*([^\n=]+)'

    # 方法模式（支持泛型参数和where子句）
    # func process<T: Codable>(_ value: T) -> Result<T, Error> where T: Equatable
    METHOD_PATTERN = r'(?:public\s+|private\s+|internal\s+|fileprivate\s+|open\s+)?' + \
                     r'(?:static\s+|class\s+)?' + \
                     r'func\s+(\w+)' + \
                     r'(?:' + GENERIC_PARAM_PATTERN + r')?' + \
                     r'\s*(\([^)]*\))' + \
                     r'\s*(?:->\s*([^\n{]+?))?' + \
                     r'(?:\s+' + WHERE_CLAUSE_PATTERN + r')?'

    ENUM_CASE_PATTERN = r'case\s+(\w+)'

    def __init__(self, whitelist_manager=None):
        """
        初始化Swift解析器

        Args:
            whitelist_manager: 白名单管理器
        """
        self.whitelist_manager = whitelist_manager
        self.current_type = None  # 当前类/结构体/枚举
        self.brace_depth = 0  # 花括号深度追踪

    def parse_file(self, file_path: str) -> ParsedFile:
        """
        解析Swift文件

        Args:
            file_path: 文件路径

        Returns:
            ParsedFile: 解析结果
        """
        parsed = ParsedFile(file_path=file_path, language="swift")

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # 字符串字面量保护：提取字符串避免误识别
            protector = StringLiteralProtector()
            protected_content = protector.protect(content, language="swift")

            # 重新分行处理
            lines = protected_content.splitlines(keepends=True)

            self.current_type = None
            self.brace_depth = 0
            in_multiline_comment = False
            in_multiline_string = False  # Swift多行字符串状态

            for i, line in enumerate(lines, 1):
                line_stripped = line.strip()

                # 跳过空行
                if not line_stripped:
                    continue

                # 处理Swift多行字符串 """..."""
                if '"""' in line:
                    if not in_multiline_string:
                        in_multiline_string = True
                        continue
                    else:
                        in_multiline_string = False
                        continue

                # 在多行字符串内部，跳过
                if in_multiline_string:
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
                if line_stripped.startswith('import'):
                    self._parse_import(line_stripped, parsed)
                    continue

                # 解析class/struct/enum
                if any(keyword in line_stripped for keyword in ['class ', 'struct ', 'enum ']):
                    symbol = self._parse_type(line_stripped, file_path, i, line)
                    if symbol:
                        parsed.symbols.append(symbol)
                        self.current_type = symbol.name
                        # 检查这一行是否有开括号
                        if '{' in line:
                            self.brace_depth = 1
                    continue

                # 解析protocol
                if line_stripped.startswith('protocol'):
                    symbol = self._parse_protocol(line_stripped, file_path, i, line)
                    if symbol:
                        parsed.symbols.append(symbol)
                        self.current_type = symbol.name
                        # 检查这一行是否有开括号
                        if '{' in line:
                            self.brace_depth = 1
                    continue

                # 解析extension
                if line_stripped.startswith('extension'):
                    symbol = self._parse_extension(line_stripped, file_path, i, line)
                    if symbol:
                        self.current_type = symbol.name
                        if '{' in line:
                            self.brace_depth = 1
                    continue

                # 在类型定义内部
                if self.current_type and self.brace_depth > 0:
                    # 追踪花括号深度
                    open_braces = line.count('{')
                    close_braces = line.count('}')
                    self.brace_depth += open_braces - close_braces

                    # 解析属性（支持访问修饰符）
                    # 修复：检查包含var或let，而不是startswith
                    if ('var ' in line_stripped or 'let ' in line_stripped):
                        symbol = self._parse_property(line_stripped, file_path, i, line)
                        if symbol:
                            symbol.parent = self.current_type
                            parsed.symbols.append(symbol)

                    # 解析方法（支持访问修饰符）
                    # 修复：检查包含func，而不是startswith
                    elif 'func ' in line_stripped:
                        symbol = self._parse_method(line_stripped, file_path, i, line)
                        if symbol:
                            symbol.parent = self.current_type
                            parsed.symbols.append(symbol)

                    # 解析枚举case
                    elif line_stripped.startswith('case'):
                        symbols = self._parse_enum_case(line_stripped, file_path, i, line)
                        for s in symbols:
                            s.parent = self.current_type
                            parsed.symbols.append(s)

                    # 检测类型定义结束
                    if self.brace_depth == 0:
                        self.current_type = None

        except Exception as e:
            print(f"解析Swift文件失败 {file_path}: {e}")

        return parsed

    def _parse_import(self, line: str, parsed: ParsedFile):
        """解析import语句"""
        match = re.search(r'import\s+(\w+)', line)
        if match:
            parsed.imports.add(match.group(1))

    def _parse_type(self, line: str, file_path: str, line_num: int, original: str) -> Optional[Symbol]:
        """解析class/struct/enum"""
        match = re.search(self.CLASS_PATTERN, line)
        if match:
            type_keyword = match.group(1)  # class, struct, enum
            type_name = match.group(2)

            if self._is_whitelisted(type_name):
                return None

            # 确定符号类型
            if type_keyword == 'class':
                symbol_type = SymbolType.CLASS
            elif type_keyword == 'struct':
                symbol_type = SymbolType.STRUCT
            else:
                symbol_type = SymbolType.ENUM

            return Symbol(
                name=type_name,
                type=symbol_type,
                file_path=file_path,
                line_number=line_num,
                original_line=original.strip()
            )
        return None

    def _parse_protocol(self, line: str, file_path: str, line_num: int, original: str) -> Optional[Symbol]:
        """解析protocol"""
        match = re.search(self.PROTOCOL_PATTERN, line)
        if match:
            protocol_name = match.group(1)

            if self._is_whitelisted(protocol_name):
                return None

            return Symbol(
                name=protocol_name,
                type=SymbolType.PROTOCOL,
                file_path=file_path,
                line_number=line_num,
                original_line=original.strip()
            )
        return None

    def _parse_extension(self, line: str, file_path: str, line_num: int, original: str) -> Optional[Symbol]:
        """解析extension"""
        match = re.search(self.EXTENSION_PATTERN, line)
        if match:
            type_name = match.group(1)

            return Symbol(
                name=type_name,
                type=SymbolType.EXTENSION,
                file_path=file_path,
                line_number=line_num,
                original_line=original.strip()
            )
        return None

    def _parse_property(self, line: str, file_path: str, line_num: int, original: str) -> Optional[Symbol]:
        """解析属性"""
        match = re.search(self.PROPERTY_PATTERN, line)
        if match:
            property_keyword = match.group(1)  # var 或 let
            property_name = match.group(2)
            property_type = match.group(3).strip()

            if self._is_whitelisted(property_name):
                return None

            return Symbol(
                name=property_name,
                type=SymbolType.PROPERTY,
                file_path=file_path,
                line_number=line_num,
                original_line=original.strip(),
                return_type=property_type,
                is_static=(property_keyword == 'let')
            )
        return None

    def _parse_method(self, line: str, file_path: str, line_num: int, original: str) -> Optional[Symbol]:
        """解析方法"""
        match = re.search(self.METHOD_PATTERN, line)
        if match:
            method_name = match.group(1)
            parameters_str = match.group(2)
            return_type = match.group(3).strip() if match.group(3) else "Void"

            if self._is_whitelisted(method_name):
                return None

            # 提取参数名
            parameters = self._extract_parameters(parameters_str)

            return Symbol(
                name=method_name,
                type=SymbolType.METHOD,
                file_path=file_path,
                line_number=line_num,
                original_line=original.strip(),
                return_type=return_type,
                parameters=parameters
            )
        return None

    def _extract_parameters(self, params_str: str) -> List[str]:
        """
        提取参数名列表
        例如: "(name: String, age: Int)" -> ["name", "age"]
        """
        parameters = []
        # 去掉括号
        params_str = params_str.strip('()')

        if params_str:
            # 分割参数
            parts = params_str.split(',')
            for part in parts:
                # 提取参数名（格式: name: Type 或 _ name: Type）
                match = re.match(r'\s*(?:_\s+)?(\w+)\s*:', part)
                if match:
                    parameters.append(match.group(1))

        return parameters

    def _parse_enum_case(self, line: str, file_path: str, line_num: int, original: str) -> List[Symbol]:
        """解析枚举case"""
        symbols = []

        # 匹配: case foo, bar, baz
        match = re.search(r'case\s+(.+)', line)
        if match:
            cases_str = match.group(1)
            # 去掉关联值
            cases_str = re.sub(r'\([^)]*\)', '', cases_str)
            # 分割多个case
            cases = [c.strip() for c in cases_str.split(',')]

            for case_name in cases:
                if case_name and not self._is_whitelisted(case_name):
                    symbols.append(Symbol(
                        name=case_name,
                        type=SymbolType.CONSTANT,
                        file_path=file_path,
                        line_number=line_num,
                        original_line=original.strip()
                    ))

        return symbols

    def _is_whitelisted(self, name: str) -> bool:
        """检查是否在白名单中"""
        if not self.whitelist_manager:
            return False
        return self.whitelist_manager.is_whitelisted(name)


class CodeParser:
    """统一的代码解析器接口"""

    def __init__(self, whitelist_manager=None):
        """
        初始化代码解析器

        Args:
            whitelist_manager: 白名单管理器
        """
        self.objc_parser = ObjCParser(whitelist_manager)
        self.swift_parser = SwiftParser(whitelist_manager)

    def parse_file(self, file_path: str) -> ParsedFile:
        """
        解析代码文件（自动检测语言）

        Args:
            file_path: 文件路径

        Returns:
            ParsedFile: 解析结果
        """
        path = Path(file_path)

        if path.suffix in ['.h', '.m', '.mm']:
            return self.objc_parser.parse_file(file_path)
        elif path.suffix == '.swift':
            return self.swift_parser.parse_file(file_path)
        else:
            raise ValueError(f"不支持的文件类型: {path.suffix}")

    def parse_files(self, file_paths: List[str], callback=None) -> Dict[str, ParsedFile]:
        """
        批量解析文件

        Args:
            file_paths: 文件路径列表
            callback: 进度回调 callback(progress, file_path)

        Returns:
            Dict[str, ParsedFile]: {文件路径: 解析结果}
        """
        results = {}
        total = len(file_paths)

        for i, file_path in enumerate(file_paths, 1):
            try:
                parsed = self.parse_file(file_path)
                results[file_path] = parsed

                if callback:
                    callback(i / total, file_path)

            except Exception as e:
                print(f"解析文件失败 {file_path}: {e}")
                continue

        return results

    def get_all_symbols(self, parsed_files: Dict[str, ParsedFile]) -> List[Symbol]:
        """获取所有符号"""
        all_symbols = []
        for parsed in parsed_files.values():
            all_symbols.extend(parsed.symbols)
        return all_symbols

    def get_symbols_by_type(self, parsed_files: Dict[str, ParsedFile],
                           symbol_type: SymbolType) -> List[Symbol]:
        """按类型获取符号"""
        symbols = []
        for parsed in parsed_files.values():
            symbols.extend([s for s in parsed.symbols if s.type == symbol_type])
        return symbols

    def group_symbols_by_type(self, symbols: List[Symbol]) -> Dict[SymbolType, List[Symbol]]:
        """按类型分组符号"""
        groups = {}
        for symbol in symbols:
            if symbol.type not in groups:
                groups[symbol.type] = []
            groups[symbol.type].append(symbol)
        return groups


if __name__ == "__main__":
    # 测试代码
    print("=== 代码解析器测试 ===\n")

    # 创建测试文件
    test_objc_header = """
#import <UIKit/UIKit.h>
#import "MyProtocol.h"

@class MyDelegate;

@protocol MyProtocolDelegate <NSObject>
- (void)didFinish;
@end

@interface MyViewController : UIViewController <MyProtocolDelegate>

@property (nonatomic, strong) NSString *userName;
@property (nonatomic, assign) NSInteger userId;

- (instancetype)initWithFrame:(CGRect)frame;
- (void)loadDataWithCompletion:(void (^)(BOOL success))completion;
+ (instancetype)sharedInstance;

@end

@interface MyViewController (Private)
- (void)privateMethod;
@end

typedef enum {
    StatusIdle,
    StatusRunning,
    StatusFinished
} MyStatus;

#define kMaxRetryCount 3
#define kAPIBaseURL @"https://api.example.com"
"""

    test_swift_file = """
import UIKit
import Foundation

protocol MyDelegate {
    func didFinish()
}

class MyViewController: UIViewController, MyDelegate {

    var userName: String = ""
    let userId: Int = 0

    func loadData() {
        // Implementation
    }

    func didFinish() {
        // Protocol implementation
    }
}

extension MyViewController {
    func extensionMethod() {
        // Extension method
    }
}

enum NetworkStatus {
    case idle
    case loading
    case success
    case failure
}

struct User {
    var name: String
    var age: Int
}
"""

    # 保存测试文件
    import tempfile
    import os

    with tempfile.TemporaryDirectory() as tmpdir:
        objc_path = os.path.join(tmpdir, "test.h")
        swift_path = os.path.join(tmpdir, "test.swift")

        with open(objc_path, 'w') as f:
            f.write(test_objc_header)

        with open(swift_path, 'w') as f:
            f.write(test_swift_file)

        # 测试Objective-C解析
        print("1. Objective-C解析测试:")
        parser = CodeParser()
        objc_result = parser.parse_file(objc_path)

        print(f"  文件: {objc_result.file_path}")
        print(f"  语言: {objc_result.language}")
        print(f"  导入: {len(objc_result.imports)} 个")
        print(f"  符号: {len(objc_result.symbols)} 个")

        # 按类型统计
        groups = parser.group_symbols_by_type(objc_result.symbols)
        for symbol_type, symbols in groups.items():
            print(f"    {symbol_type.value}: {len(symbols)} 个")
            for s in symbols[:2]:  # 只显示前2个
                print(f"      - {s.name} (行{s.line_number})")

        # 测试Swift解析
        print("\n2. Swift解析测试:")
        swift_result = parser.parse_file(swift_path)

        print(f"  文件: {swift_result.file_path}")
        print(f"  语言: {swift_result.language}")
        print(f"  导入: {len(swift_result.imports)} 个")
        print(f"  符号: {len(swift_result.symbols)} 个")

        groups = parser.group_symbols_by_type(swift_result.symbols)
        for symbol_type, symbols in groups.items():
            print(f"    {symbol_type.value}: {len(symbols)} 个")
            for s in symbols[:2]:
                print(f"      - {s.name} (行{s.line_number})")

    print("\n=== 测试完成 ===")
