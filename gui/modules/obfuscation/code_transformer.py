"""
代码转换器 - 负责将解析后的代码进行符号替换和混淆转换

支持:
1. 符号替换（类名、方法名、属性名等）
2. 跨文件引用更新
3. 注释处理
4. 字符串字面量处理
5. 代码格式保持

重构说明: 替换逻辑已提取到 symbol_replacer.py
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple

try:
    from .code_parser import ParsedFile, Symbol, SymbolType
    from .name_generator import NameGenerator
    from .symbol_replacer import SymbolReplacer
except ImportError:
    from code_parser import ParsedFile, Symbol, SymbolType
    from name_generator import NameGenerator
    from symbol_replacer import SymbolReplacer


@dataclass
class TransformResult:
    """转换结果"""
    file_path: str                      # 文件路径
    original_content: str               # 原始内容
    transformed_content: str            # 转换后内容
    replacements: int = 0               # 替换次数
    errors: List[str] = field(default_factory=list)  # 错误信息


class CodeTransformer:
    """代码转换器 - 协调符号映射生成和代码替换"""

    def __init__(self, name_generator: NameGenerator, whitelist_manager=None):
        """
        初始化代码转换器

        Args:
            name_generator: 名称生成器
            whitelist_manager: 白名单管理器
        """
        self.name_generator = name_generator
        self.whitelist_manager = whitelist_manager

        # 符号映射缓存
        self.symbol_mappings: Dict[str, str] = {}  # {原始名: 混淆名}

        # 符号替换器（延迟初始化）
        self.replacer = None

        # 统计信息
        self.stats = {
            'files_transformed': 0,
            'total_replacements': 0,
            'classes_renamed': 0,
            'methods_renamed': 0,
            'properties_renamed': 0,
        }

    def transform_file(self, file_path: str, parsed: ParsedFile) -> TransformResult:
        """
        转换单个文件

        Args:
            file_path: 文件路径
            parsed: 解析后的文件信息

        Returns:
            TransformResult: 转换结果
        """
        # 读取原始文件内容
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                original_content = f.read()
        except Exception as e:
            return TransformResult(
                file_path=file_path,
                original_content="",
                transformed_content="",
                errors=[f"读取文件失败: {e}"]
            )

        # 生成符号映射
        self._generate_mappings(parsed)

        # 初始化替换器
        if not self.replacer:
            self.replacer = SymbolReplacer(self.symbol_mappings)

        # 执行转换
        # 步骤1: 提取并保护注释和字符串
        cleaned_content, protected_items = self._extract_comments_and_strings(original_content)

        transformed_content = cleaned_content
        replacements = 0

        # 按符号类型分组处理（避免冲突）
        # 1. 先替换类名（最长的标识符）
        for symbol in parsed.symbols:
            if symbol.type == SymbolType.CLASS:
                transformed_content, count = self.replacer.replace_class_name(
                    transformed_content, symbol
                )
                replacements += count

        # 2. 替换协议名
        for symbol in parsed.symbols:
            if symbol.type == SymbolType.PROTOCOL:
                transformed_content, count = self.replacer.replace_protocol_name(
                    transformed_content, symbol
                )
                replacements += count

        # 3. 替换方法名
        for symbol in parsed.symbols:
            if symbol.type == SymbolType.METHOD:
                transformed_content, count = self.replacer.replace_method_name(
                    transformed_content, symbol
                )
                replacements += count

        # 4. 替换属性名
        for symbol in parsed.symbols:
            if symbol.type == SymbolType.PROPERTY:
                transformed_content, count = self.replacer.replace_property_name(
                    transformed_content, symbol
                )
                replacements += count

        # 5. 替换宏定义
        for symbol in parsed.symbols:
            if symbol.type == SymbolType.MACRO:
                transformed_content, count = self.replacer.replace_macro_name(
                    transformed_content, symbol
                )
                replacements += count

        # 6. 更新import语句
        transformed_content, import_count = self.replacer.update_import_statements(
            transformed_content
        )
        replacements += import_count

        # 步骤2: 恢复注释和字符串
        transformed_content = self._restore_comments_and_strings(
            transformed_content, protected_items
        )

        # 更新统计
        self.stats['files_transformed'] += 1
        self.stats['total_replacements'] += replacements

        return TransformResult(
            file_path=file_path,
            original_content=original_content,
            transformed_content=transformed_content,
            replacements=replacements
        )

    def _extract_comments_and_strings(self, content: str) -> Tuple[str, Dict[str, str]]:
        """
        提取并替换注释和字符串为占位符

        Args:
            content: 原始代码内容

        Returns:
            Tuple[str, Dict[str, str]]: (清理后的内容, {占位符: 原始内容})
        """
        protected_items = {}
        placeholder_counter = [0]  # 使用列表以便在闭包中修改

        def create_placeholder(original: str) -> str:
            """创建占位符"""
            placeholder = f"__PROTECTED_{placeholder_counter[0]}__"
            protected_items[placeholder] = original
            placeholder_counter[0] += 1
            return placeholder

        # 按顺序提取（重要：字符串可能包含注释符号，需先处理字符串）

        # 1. 提取字符串字面量
        def replace_string(match):
            return create_placeholder(match.group(0))

        # ObjC字符串: @"..."
        content = re.sub(r'@"(?:[^"\\]|\\.)*"', replace_string, content)
        # 普通字符串: "..."
        content = re.sub(r'"(?:[^"\\]|\\.)*"', replace_string, content)
        # 字符: '.'
        content = re.sub(r"'(?:[^'\\]|\\.)'", replace_string, content)

        # 2. 提取单行注释 //...
        content = re.sub(r'//[^\n]*', replace_string, content)

        # 3. 提取多行注释 /* ... */
        content = re.sub(r'/\*.*?\*/', replace_string, content, flags=re.DOTALL)

        return content, protected_items

    def _restore_comments_and_strings(self, content: str, protected_items: Dict[str, str]) -> str:
        """
        恢复注释和字符串

        Args:
            content: 转换后的内容
            protected_items: 占位符映射

        Returns:
            str: 恢复后的内容
        """
        for placeholder, original in protected_items.items():
            content = content.replace(placeholder, original)

        return content

    def _generate_mappings(self, parsed: ParsedFile) -> None:
        """
        为解析出的符号生成映射 - 包含符号冲突检测

        修复:
        - 添加反向映射检测冲突
        - 自动重试生成避免重复
        - 提供警告信息
        """
        # 反向映射用于检测冲突 {混淆名: [原始名列表]}
        reverse_mappings: Dict[str, List[str]] = {}

        # 预先构建已有的反向映射
        for original, obfuscated in self.symbol_mappings.items():
            if obfuscated not in reverse_mappings:
                reverse_mappings[obfuscated] = []
            reverse_mappings[obfuscated].append(original)

        for symbol in parsed.symbols:
            if symbol.name not in self.symbol_mappings:
                # 检查白名单
                if self.whitelist_manager and self.whitelist_manager.is_whitelisted(symbol.name):
                    continue

                # 生成混淆名
                obfuscated_name = self.name_generator.generate(
                    symbol.name,
                    symbol.type.value
                )

                # 冲突检测
                max_retries = 5
                retry_count = 0

                while obfuscated_name in reverse_mappings and retry_count < max_retries:
                    # 发现冲突，重新生成
                    print(f"⚠️  名称冲突 '{obfuscated_name}'，重新生成...")
                    obfuscated_name = self.name_generator.generate(
                        symbol.name,
                        symbol.type.value
                    )
                    retry_count += 1

                if retry_count >= max_retries:
                    print(f"❌ 警告: 无法为 '{symbol.name}' 生成唯一名称，保留原名")
                    continue

                # 保存映射
                self.symbol_mappings[symbol.name] = obfuscated_name

                # 更新反向映射
                if obfuscated_name not in reverse_mappings:
                    reverse_mappings[obfuscated_name] = []
                reverse_mappings[obfuscated_name].append(symbol.name)

                # 更新统计
                if symbol.type == SymbolType.CLASS:
                    self.stats['classes_renamed'] += 1
                elif symbol.type == SymbolType.METHOD:
                    self.stats['methods_renamed'] += 1
                elif symbol.type == SymbolType.PROPERTY:
                    self.stats['properties_renamed'] += 1

    def transform_files(self, parsed_files: Dict[str, ParsedFile],
                       progress_callback=None) -> Dict[str, TransformResult]:
        """
        批量转换文件

        Args:
            parsed_files: {文件路径: 解析结果}
            progress_callback: 进度回调函数

        Returns:
            Dict[str, TransformResult]: {文件路径: 转换结果}
        """
        results = {}
        total = len(parsed_files)

        for i, (file_path, parsed) in enumerate(parsed_files.items()):
            if progress_callback:
                progress_callback(i + 1, total, f"转换: {Path(file_path).name}")

            result = self.transform_file(file_path, parsed)
            results[file_path] = result

        return results

    def save_transformed_files(self, results: Dict[str, TransformResult],
                              output_dir: str) -> None:
        """
        保存转换后的文件

        Args:
            results: 转换结果
            output_dir: 输出目录
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        for file_path, result in results.items():
            if result.errors:
                print(f"跳过错误文件: {file_path}")
                continue

            # 计算相对路径
            rel_path = Path(file_path).name
            output_file = output_path / rel_path

            # 保存转换后的内容
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(result.transformed_content)
            except Exception as e:
                print(f"保存文件失败 {output_file}: {e}")

    def get_statistics(self) -> Dict:
        """获取转换统计信息"""
        return self.stats.copy()

    def export_mapping_report(self, output_path: str) -> None:
        """
        导出符号映射报告

        Args:
            output_path: 输出文件路径
        """
        import json

        report = {
            'statistics': self.get_statistics(),
            'mappings': self.symbol_mappings
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
