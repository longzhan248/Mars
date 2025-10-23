"""
Swift代码解析器
"""

import re
from typing import List, Optional

from .common import ParsedFile, Symbol, SymbolType
from .string_protector import StringLiteralProtector


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
