"""
代码转换器 - 负责将解析后的代码进行符号替换和混淆转换

支持:
1. 符号替换（类名、方法名、属性名等）
2. 跨文件引用更新
3. 注释处理
4. 字符串字面量处理
5. 代码格式保持
"""

import re
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field

try:
    from .code_parser import Symbol, SymbolType, ParsedFile
    from .name_generator import NameGenerator, NameMapping
except ImportError:
    from code_parser import Symbol, SymbolType, ParsedFile
    from name_generator import NameGenerator, NameMapping


@dataclass
class TransformResult:
    """转换结果"""
    file_path: str                      # 文件路径
    original_content: str               # 原始内容
    transformed_content: str            # 转换后内容
    replacements: int = 0               # 替换次数
    errors: List[str] = field(default_factory=list)  # 错误信息


class CodeTransformer:
    """代码转换器"""

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

        # 执行转换
        # 步骤1: 提取并保护注释和字符串
        cleaned_content, protected_items = self._extract_comments_and_strings(original_content)

        transformed_content = cleaned_content
        replacements = 0

        # 按符号类型分组处理（避免冲突）
        # 1. 先替换类名（最长的标识符）
        for symbol in parsed.symbols:
            if symbol.type == SymbolType.CLASS:
                transformed_content, count = self._replace_class_name(
                    transformed_content, symbol
                )
                replacements += count

        # 2. 替换协议名
        for symbol in parsed.symbols:
            if symbol.type == SymbolType.PROTOCOL:
                transformed_content, count = self._replace_protocol_name(
                    transformed_content, symbol
                )
                replacements += count

        # 3. 替换方法名
        for symbol in parsed.symbols:
            if symbol.type == SymbolType.METHOD:
                transformed_content, count = self._replace_method_name(
                    transformed_content, symbol
                )
                replacements += count

        # 4. 替换属性名
        for symbol in parsed.symbols:
            if symbol.type == SymbolType.PROPERTY:
                transformed_content, count = self._replace_property_name(
                    transformed_content, symbol
                )
                replacements += count

        # 5. 替换宏定义
        for symbol in parsed.symbols:
            if symbol.type == SymbolType.MACRO:
                transformed_content, count = self._replace_macro_name(
                    transformed_content, symbol
                )
                replacements += count

        # 6. 更新import语句
        transformed_content, import_count = self._update_import_statements(transformed_content)
        replacements += import_count

        # 步骤2: 恢复注释和字符串
        transformed_content = self._restore_comments_and_strings(transformed_content, protected_items)

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
        # @"..." 或 "..."
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

    def _generate_mappings(self, parsed: ParsedFile):
        """
        为解析出的符号生成映射 - P1修复: 添加符号冲突检测

        修复:
        - 添加反向映射检测冲突
        - 自动重试生成避免重复
        - 提供警告信息
        """
        # P1修复: 反向映射用于检测冲突
        # {混淆名: [原始名列表]}
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

                # P1修复: 冲突检测
                if obfuscated_name in reverse_mappings:
                    # 发现冲突
                    existing_symbols = reverse_mappings[obfuscated_name]
                    print(f"⚠️  检测到名称冲突:")
                    print(f"   混淆名: {obfuscated_name}")
                    print(f"   已存在: {existing_symbols}")
                    print(f"   当前符号: {symbol.name} ({symbol.type.value})")
                    print(f"   正在重新生成...")

                    # 重试生成唯一名称
                    retry_count = 0
                    max_retries = 10

                    while obfuscated_name in reverse_mappings and retry_count < max_retries:
                        # 添加后缀强制生成不同名称
                        temp_name = f"{symbol.name}_retry_{retry_count}"
                        obfuscated_name = self.name_generator.generate(
                            temp_name,
                            symbol.type.value
                        )
                        retry_count += 1

                    if retry_count == max_retries:
                        # 达到最大重试次数，使用后缀确保唯一
                        obfuscated_name = f"{obfuscated_name}_{retry_count}"
                        print(f"   ⚠️  达到最大重试次数，使用后缀: {obfuscated_name}")
                    else:
                        print(f"   ✅ 重新生成成功: {obfuscated_name} (重试{retry_count}次)")

                # 保存映射
                self.symbol_mappings[symbol.name] = obfuscated_name

                # 更新反向映射
                if obfuscated_name not in reverse_mappings:
                    reverse_mappings[obfuscated_name] = []
                reverse_mappings[obfuscated_name].append(symbol.name)

    def _replace_class_name(self, content: str, symbol: Symbol) -> Tuple[str, int]:
        """
        替换类名

        Args:
            content: 文件内容
            symbol: 类符号

        Returns:
            Tuple[str, int]: (替换后的内容, 替换次数)
        """
        if symbol.name not in self.symbol_mappings:
            return content, 0

        obfuscated_name = self.symbol_mappings[symbol.name]
        count = 0

        # 替换模式（确保只替换完整的类名，不替换子串）
        # 使用负向前瞻和后顾避免匹配系统类前缀和复合词
        patterns = [
            # @interface ClassName
            (rf'@interface\s+{re.escape(symbol.name)}\b',
             f'@interface {obfuscated_name}'),

            # @implementation ClassName
            (rf'@implementation\s+{re.escape(symbol.name)}\b',
             f'@implementation {obfuscated_name}'),

            # : ClassName (继承) - 确保不匹配NS*/UI*等系统前缀
            (rf'(?<!NS)(?<!UI)(?<!CF)(?<!CG)(?<!CA)(?<!AV):\s*{re.escape(symbol.name)}\b',
             f': {obfuscated_name}'),

            # @class ClassName (前置声明)
            (rf'@class\s+(?<!NS)(?<!UI){re.escape(symbol.name)}\b',
             f'@class {obfuscated_name}'),

            # ClassName * (类型声明) - 确保不是系统类的一部分
            (rf'(?<!NS)(?<!UI)(?<!CF)(?<!CG)\b{re.escape(symbol.name)}\s*\*',
             f'{obfuscated_name} *'),

            # class ClassName (Swift)
            (rf'\bclass\s+{re.escape(symbol.name)}\b',
             f'class {obfuscated_name}'),

            # struct ClassName (Swift)
            (rf'\bstruct\s+{re.escape(symbol.name)}\b',
             f'struct {obfuscated_name}'),

            # ClassName( (方法调用/初始化)
            (rf'(?<!NS)(?<!UI)\b{re.escape(symbol.name)}\s*\(',
             f'{obfuscated_name}('),
        ]

        for pattern, replacement in patterns:
            new_content = re.sub(pattern, replacement, content)
            if new_content != content:
                count += len(re.findall(pattern, content))
                content = new_content

        self.stats['classes_renamed'] += (1 if count > 0 else 0)
        return content, count

    def _replace_protocol_name(self, content: str, symbol: Symbol) -> Tuple[str, int]:
        """替换协议名"""
        if symbol.name not in self.symbol_mappings:
            return content, 0

        obfuscated_name = self.symbol_mappings[symbol.name]
        count = 0

        patterns = [
            # @protocol ProtocolName
            (rf'@protocol\s+{re.escape(symbol.name)}\b',
             f'@protocol {obfuscated_name}'),

            # <ProtocolName>
            (rf'<\s*{re.escape(symbol.name)}\s*>',
             f'<{obfuscated_name}>'),

            # protocol ProtocolName (Swift)
            (rf'\bprotocol\s+{re.escape(symbol.name)}\b',
             f'protocol {obfuscated_name}'),
        ]

        for pattern, replacement in patterns:
            new_content = re.sub(pattern, replacement, content)
            if new_content != content:
                count += len(re.findall(pattern, content))
                content = new_content

        return content, count

    def _replace_method_name(self, content: str, symbol: Symbol) -> Tuple[str, int]:
        """
        替换方法名 - P0修复: 添加边界检查防止前缀匹配

        Note: Objective-C方法名包含冒号，需要精确匹配完整方法签名

        修复:
        - 添加正向预查(?=...)确保方法名后是正确的边界
        - 防止前缀误匹配（例如: load vs loadData）
        """
        if symbol.name not in self.symbol_mappings:
            return content, 0

        obfuscated_name = self.symbol_mappings[symbol.name]
        count = 0

        # Objective-C方法（包含冒号）
        if ':' in symbol.name:
            # ObjC方法名必须作为整体替换，保持完整性
            # 例如: "initWithFrame:style:" 整体替换为 "abc123:xyz456:"

            # P0修复: 添加边界检查，确保完整匹配
            # 使用正向预查(?=\s|;|{|\[)确保方法名后是正确的边界
            patterns = [
                # 方法声明: - (返回类型)方法名
                # 添加边界检查: 后面必须是空格、分号或大括号
                # 例如: - (instancetype)initWithFrame:(CGRect)frame style:(UITableViewStyle)style {
                (rf'([+-]\s*\([^)]+\)\s*){re.escape(symbol.name)}(?=\s|;|{{)',
                 rf'\1{obfuscated_name}'),

                # 方法调用: [对象 方法名]
                # 确保方法名后面是参数或结束
                # 例如: [self initWithFrame:frame style:style]
                (rf'(\[\s*\w+\s+){re.escape(symbol.name)}(?=\w|\s*\])',
                 rf'\1{obfuscated_name}'),

                # 方法调用: [[类 alloc] 方法名]
                # 例如: [[UITableView alloc] initWithFrame:frame style:style]
                (rf'(\]\s*){re.escape(symbol.name)}(?=\w|\s*\])',
                 rf'\1{obfuscated_name}'),
            ]

            for pattern, replacement in patterns:
                new_content = re.sub(pattern, replacement, content)
                if new_content != content:
                    count += len(re.findall(pattern, content))
                    content = new_content

        else:
            # 无参数方法或Swift方法
            # P0修复: 确保无参方法不会误匹配到有参方法的前缀
            patterns = [
                # ObjC无参方法声明: - (void)methodName
                # 确保后面是换行、分号、大括号或空格，不是冒号
                (rf'([+-]\s*\([^)]+\)\s*){re.escape(symbol.name)}(?![:\w])',
                 rf'\1{obfuscated_name}'),

                # ObjC无参方法调用: [obj methodName]
                # 确保后面是]，不是其他字符
                (rf'(\[\s*\w+\s+){re.escape(symbol.name)}(?=\s*\])',
                 rf'\1{obfuscated_name}]'),

                # Swift方法声明: func methodName()
                (rf'\bfunc\s+{re.escape(symbol.name)}(?=\s*\()',
                 f'func {obfuscated_name}'),

                # Swift方法调用: obj.methodName()
                # 确保后面是(，不是其他字符
                (rf'\.{re.escape(symbol.name)}(?=\s*\()',
                 f'.{obfuscated_name}('),
            ]

            for pattern, replacement in patterns:
                new_content = re.sub(pattern, replacement, content)
                if new_content != content:
                    count += len(re.findall(pattern, content))
                    content = new_content

        self.stats['methods_renamed'] += (1 if count > 0 else 0)
        return content, count

    def _replace_property_name(self, content: str, symbol: Symbol) -> Tuple[str, int]:
        """替换属性名"""
        if symbol.name not in self.symbol_mappings:
            return content, 0

        obfuscated_name = self.symbol_mappings[symbol.name]
        count = 0

        patterns = [
            # @property (...) Type propertyName
            (rf'(@property\s*\([^)]*\)\s*[^;]+\s+){re.escape(symbol.name)}\b',
             rf'\1{obfuscated_name}'),

            # self.propertyName
            (rf'\.{re.escape(symbol.name)}\b',
             f'.{obfuscated_name}'),

            # var propertyName (Swift)
            (rf'\b(var|let)\s+{re.escape(symbol.name)}\b',
             rf'\1 {obfuscated_name}'),

            # _propertyName (backing ivar)
            (rf'\b_{re.escape(symbol.name)}\b',
             f'_{obfuscated_name}'),
        ]

        for pattern, replacement in patterns:
            new_content = re.sub(pattern, replacement, content)
            if new_content != content:
                count += len(re.findall(pattern, content))
                content = new_content

        self.stats['properties_renamed'] += (1 if count > 0 else 0)
        return content, count

    def _replace_macro_name(self, content: str, symbol: Symbol) -> Tuple[str, int]:
        """替换宏定义名"""
        if symbol.name not in self.symbol_mappings:
            return content, 0

        obfuscated_name = self.symbol_mappings[symbol.name]
        count = 0

        patterns = [
            # #define MACRO_NAME
            (rf'#define\s+{re.escape(symbol.name)}\b',
             f'#define {obfuscated_name}'),

            # 宏使用
            (rf'\b{re.escape(symbol.name)}\b',
             obfuscated_name),
        ]

        for pattern, replacement in patterns:
            new_content = re.sub(pattern, replacement, content)
            if new_content != content:
                count += len(re.findall(pattern, content))
                content = new_content

        return content, count

    def _update_import_statements(self, content: str) -> Tuple[str, int]:
        """
        更新import语句中的类名引用

        Args:
            content: 文件内容

        Returns:
            Tuple[str, int]: (更新后的内容, 替换次数)
        """
        count = 0

        for original, obfuscated in self.symbol_mappings.items():
            # Objective-C: #import "ClassName.h"
            pattern = rf'#import\s+"({re.escape(original)})\.h"'
            replacement = rf'#import "{obfuscated}.h"'
            new_content = re.sub(pattern, replacement, content)
            if new_content != content:
                count += len(re.findall(pattern, content))
                content = new_content

            # Swift: import ClassName
            pattern = rf'\bimport\s+{re.escape(original)}\b'
            replacement = f'import {obfuscated}'
            new_content = re.sub(pattern, replacement, content)
            if new_content != content:
                count += len(re.findall(pattern, content))
                content = new_content

        return content, count

    def transform_files(self, parsed_files: Dict[str, ParsedFile],
                       callback=None) -> Dict[str, TransformResult]:
        """
        批量转换文件

        Args:
            parsed_files: 解析后的文件字典 {文件路径: ParsedFile}
            callback: 进度回调 callback(progress, file_path)

        Returns:
            Dict[str, TransformResult]: {文件路径: TransformResult}
        """
        results = {}
        total = len(parsed_files)

        # 首先为所有文件生成映射
        for parsed in parsed_files.values():
            self._generate_mappings(parsed)

        # 然后逐个转换文件
        for i, (file_path, parsed) in enumerate(parsed_files.items(), 1):
            try:
                result = self.transform_file(file_path, parsed)
                results[file_path] = result

                if callback:
                    callback(i / total, file_path)

            except Exception as e:
                print(f"转换文件失败 {file_path}: {e}")
                results[file_path] = TransformResult(
                    file_path=file_path,
                    original_content="",
                    transformed_content="",
                    errors=[str(e)]
                )

        return results

    def save_transformed_files(self, results: Dict[str, TransformResult],
                              output_dir: str) -> int:
        """
        保存转换后的文件

        Args:
            results: 转换结果字典
            output_dir: 输出目录

        Returns:
            int: 成功保存的文件数
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        saved_count = 0

        for file_path, result in results.items():
            if result.errors:
                continue

            # 保持原有目录结构
            relative_path = Path(file_path).name
            output_file = output_path / relative_path

            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(result.transformed_content)
                saved_count += 1

            except Exception as e:
                print(f"保存文件失败 {output_file}: {e}")

        return saved_count

    def get_statistics(self) -> Dict:
        """获取转换统计信息"""
        return {
            **self.stats,
            'total_mappings': len(self.symbol_mappings),
            'mapping_details': self.name_generator.get_statistics()
        }

    def export_mapping_report(self, output_path: str):
        """导出映射报告"""
        report = {
            'statistics': self.get_statistics(),
            'mappings': []
        }

        # 获取所有映射
        for original, obfuscated in self.symbol_mappings.items():
            mapping = self.name_generator.get_mapping(original)
            if mapping:
                report['mappings'].append(mapping.to_dict())

        # 保存报告
        import json
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    # 测试代码
    print("=== 代码转换器测试 ===\n")

    try:
        from .name_generator import NameGenerator, NamingStrategy
        from .code_parser import CodeParser
    except ImportError:
        from name_generator import NameGenerator, NamingStrategy
        from code_parser import CodeParser

    # 创建测试文件
    test_code = """
#import <UIKit/UIKit.h>

@interface MyViewController : UIViewController

@property (nonatomic, strong) NSString *userName;
@property (nonatomic, assign) NSInteger userId;

- (instancetype)initWithFrame:(CGRect)frame;
- (void)loadData;
+ (instancetype)sharedInstance;

@end

@implementation MyViewController

- (instancetype)initWithFrame:(CGRect)frame {
    self = [super initWithFrame:frame];
    if (self) {
        self.userName = @"Test";
        [self loadData];
    }
    return self;
}

- (void)loadData {
    NSLog(@"Loading data for user: %@", self.userName);
}

+ (instancetype)sharedInstance {
    static MyViewController *instance = nil;
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{
        instance = [[MyViewController alloc] init];
    });
    return instance;
}

@end
"""

    import tempfile
    import os

    with tempfile.TemporaryDirectory() as tmpdir:
        # 保存测试文件
        test_file = os.path.join(tmpdir, "MyViewController.m")
        with open(test_file, 'w') as f:
            f.write(test_code)

        # 1. 解析代码
        print("1. 解析代码:")
        parser = CodeParser()
        parsed = parser.parse_file(test_file)
        print(f"  找到 {len(parsed.symbols)} 个符号")

        # 2. 创建转换器
        print("\n2. 创建转换器:")
        generator = NameGenerator(
            strategy=NamingStrategy.PREFIX,
            prefix="ABC",
            seed="test_seed"
        )
        transformer = CodeTransformer(generator)

        # 3. 转换文件
        print("\n3. 转换文件:")
        result = transformer.transform_file(test_file, parsed)
        print(f"  文件: {Path(result.file_path).name}")
        print(f"  替换次数: {result.replacements}")
        print(f"  错误: {len(result.errors)}")

        # 4. 显示部分转换结果
        print("\n4. 转换后的代码片段:")
        lines = result.transformed_content.split('\n')
        for i, line in enumerate(lines[:15], 1):
            print(f"  {i:2d}: {line}")

        # 5. 显示符号映射
        print("\n5. 符号映射:")
        for i, (original, obfuscated) in enumerate(list(transformer.symbol_mappings.items())[:5], 1):
            print(f"  {i}. {original:20s} -> {obfuscated}")

        # 6. 统计信息
        print("\n6. 统计信息:")
        stats = transformer.get_statistics()
        print(f"  转换文件数: {stats['files_transformed']}")
        print(f"  总替换次数: {stats['total_replacements']}")
        print(f"  类重命名: {stats['classes_renamed']}")
        print(f"  方法重命名: {stats['methods_renamed']}")
        print(f"  属性重命名: {stats['properties_renamed']}")
        print(f"  映射总数: {stats['total_mappings']}")

    print("\n=== 测试完成 ===")
