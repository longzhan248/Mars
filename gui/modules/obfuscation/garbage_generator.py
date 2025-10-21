"""
垃圾代码生成器 - 生成无用但合法的代码以增加混淆效果

功能：
1. 生成随机类和方法定义
2. 生成复杂但无实际功能的代码逻辑
3. 生成调用关系图以模拟真实代码
4. 保证生成的代码能够编译通过
5. 与真实代码混合，误导静态分析工具

设计目标：
- 生成的代码语法正确，能通过编译
- 代码逻辑复杂但不影响应用功能
- 可配置生成数量和复杂度
- 支持Objective-C和Swift两种语言
"""

import random
import string
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple


class CodeLanguage(Enum):
    """代码语言"""
    OBJC = "objc"
    SWIFT = "swift"


class ComplexityLevel(Enum):
    """复杂度级别"""
    SIMPLE = "simple"        # 简单：基本类和方法
    MODERATE = "moderate"    # 中等：包含属性、条件语句
    COMPLEX = "complex"      # 复杂：包含循环、递归、多层调用


@dataclass
class GarbageMethod:
    """垃圾方法"""
    name: str
    return_type: str
    parameters: List[Tuple[str, str]]  # [(param_name, param_type), ...]
    body: str
    is_static: bool = False
    access_modifier: str = ""  # public, private, etc.


@dataclass
class GarbageProperty:
    """垃圾属性"""
    name: str
    property_type: str
    is_readonly: bool = False
    default_value: Optional[str] = None


@dataclass
class GarbageClass:
    """垃圾类"""
    name: str
    language: CodeLanguage
    superclass: Optional[str] = None
    protocols: List[str] = field(default_factory=list)
    properties: List[GarbageProperty] = field(default_factory=list)
    methods: List[GarbageMethod] = field(default_factory=list)
    imports: Set[str] = field(default_factory=set)

    def generate_code(self) -> str:
        """生成代码"""
        if self.language == CodeLanguage.OBJC:
            return self._generate_objc_code()
        else:
            return self._generate_swift_code()

    def _generate_objc_code(self) -> str:
        """生成Objective-C代码"""
        # 头文件
        header = self._generate_objc_header()
        # 实现文件
        implementation = self._generate_objc_implementation()
        return header, implementation

    def _generate_objc_header(self) -> str:
        """生成Objective-C头文件"""
        lines = []

        # 导入
        lines.append("#import <Foundation/Foundation.h>")
        for imp in sorted(self.imports):
            lines.append(f"#import \"{imp}\"")
        lines.append("")

        # 类声明
        inheritance = f" : {self.superclass}" if self.superclass else " : NSObject"
        protocols_str = f" <{', '.join(self.protocols)}>" if self.protocols else ""
        lines.append(f"@interface {self.name}{inheritance}{protocols_str}")
        lines.append("")

        # 属性
        for prop in self.properties:
            attrs = ["nonatomic"]
            if prop.is_readonly:
                attrs.append("readonly")
            else:
                attrs.append("strong")
            attrs_str = ", ".join(attrs)
            lines.append(f"@property ({attrs_str}) {prop.property_type} *{prop.name};")

        if self.properties:
            lines.append("")

        # 方法声明
        for method in self.methods:
            method_decl = self._generate_objc_method_declaration(method)
            lines.append(f"{method_decl};")

        lines.append("")
        lines.append("@end")
        lines.append("")

        return "\n".join(lines)

    def _generate_objc_implementation(self) -> str:
        """生成Objective-C实现文件"""
        lines = []

        # 导入头文件
        lines.append(f"#import \"{self.name}.h\"")
        lines.append("")

        # 实现
        lines.append(f"@implementation {self.name}")
        lines.append("")

        # 方法实现
        for method in self.methods:
            method_impl = self._generate_objc_method_implementation(method)
            lines.append(method_impl)
            lines.append("")

        lines.append("@end")
        lines.append("")

        return "\n".join(lines)

    def _generate_objc_method_declaration(self, method: GarbageMethod) -> str:
        """生成Objective-C方法声明"""
        prefix = "+" if method.is_static else "-"

        if not method.parameters:
            return f"{prefix} ({method.return_type}){method.name}"

        parts = [f"{prefix} ({method.return_type}){method.name}"]
        for i, (param_name, param_type) in enumerate(method.parameters):
            if i == 0:
                parts[0] += f":({param_type}){param_name}"
            else:
                label = param_name if param_name else "param" + str(i)
                parts.append(f"{label}:({param_type}){param_name}")

        return " ".join(parts)

    def _generate_objc_method_implementation(self, method: GarbageMethod) -> str:
        """生成Objective-C方法实现"""
        declaration = self._generate_objc_method_declaration(method)
        lines = [f"{declaration} {{"]

        # 方法体
        body_lines = method.body.split("\n")
        for line in body_lines:
            if line.strip():
                lines.append(f"    {line}")

        lines.append("}")
        return "\n".join(lines)

    def _generate_swift_code(self) -> str:
        """生成Swift代码"""
        lines = []

        # 导入
        lines.append("import Foundation")
        for imp in sorted(self.imports):
            lines.append(f"import {imp}")
        lines.append("")

        # 类声明
        inheritance_parts = []
        if self.superclass:
            inheritance_parts.append(self.superclass)
        inheritance_parts.extend(self.protocols)
        inheritance_str = f": {', '.join(inheritance_parts)}" if inheritance_parts else ""

        lines.append(f"class {self.name}{inheritance_str} {{")
        lines.append("")

        # 属性
        for prop in self.properties:
            let_var = "let" if prop.is_readonly else "var"
            default = f" = {prop.default_value}" if prop.default_value else ""
            lines.append(f"    {let_var} {prop.name}: {prop.property_type}{default}")

        if self.properties:
            lines.append("")

        # 方法
        for method in self.methods:
            method_impl = self._generate_swift_method_implementation(method)
            lines.append(method_impl)
            lines.append("")

        lines.append("}")
        lines.append("")

        return "\n".join(lines)

    def _generate_swift_method_implementation(self, method: GarbageMethod) -> str:
        """生成Swift方法实现"""
        lines = []

        # 方法签名
        access = f"{method.access_modifier} " if method.access_modifier else ""
        static_mod = "static " if method.is_static else ""

        # 参数
        params_str = ""
        if method.parameters:
            params = [f"{name}: {ptype}" for name, ptype in method.parameters]
            params_str = ", ".join(params)

        return_part = f" -> {method.return_type}" if method.return_type != "Void" else ""

        lines.append(f"    {access}{static_mod}func {method.name}({params_str}){return_part} {{")

        # 方法体
        body_lines = method.body.split("\n")
        for line in body_lines:
            if line.strip():
                lines.append(f"        {line}")

        lines.append("    }")

        return "\n".join(lines)


class GarbageCodeGenerator:
    """垃圾代码生成器"""

    # 常用类型
    OBJC_TYPES = ["NSString", "NSNumber", "NSArray", "NSDictionary", "NSData", "NSDate"]
    SWIFT_TYPES = ["String", "Int", "Double", "Bool", "Array", "Dictionary", "Data", "Date"]

    # 常用方法名前缀
    METHOD_PREFIXES = [
        "calculate", "process", "handle", "update", "fetch", "load",
        "save", "delete", "create", "validate", "transform", "convert"
    ]

    # 常用方法名后缀
    METHOD_SUFFIXES = [
        "Data", "Value", "Info", "Result", "Status", "State",
        "Content", "Item", "List", "Cache", "Config"
    ]

    def __init__(
        self,
        language: CodeLanguage = CodeLanguage.OBJC,
        complexity: ComplexityLevel = ComplexityLevel.MODERATE,
        name_prefix: str = "GC",  # Garbage Code prefix
        seed: Optional[str] = None,
        enable_call_relationships: bool = True,  # 🆕 是否启用调用关系
        call_density: str = "medium",  # 🆕 调用密度（low/medium/high）
        max_call_depth: int = 3  # 🆕 最大调用深度
    ):
        """
        初始化垃圾代码生成器

        Args:
            language: 目标语言
            complexity: 复杂度级别
            name_prefix: 名称前缀
            seed: 随机种子（用于确定性生成）
            enable_call_relationships: 是否启用调用关系生成
            call_density: 调用密度（low/medium/high）
            max_call_depth: 最大调用深度
        """
        self.language = language
        self.complexity = complexity
        self.name_prefix = name_prefix
        self.enable_call_relationships = enable_call_relationships
        self.call_density = call_density
        self.max_call_depth = max_call_depth
        self.generated_classes: List[GarbageClass] = []
        self.class_name_index = 1

        if seed:
            random.seed(seed)

    def generate_random_name(self, prefix: str = "", length: int = 8) -> str:
        """生成随机名称"""
        chars = string.ascii_letters
        random_part = ''.join(random.choices(chars, k=length))
        return f"{prefix}{random_part}" if prefix else random_part

    def generate_class_name(self) -> str:
        """生成类名"""
        name = f"{self.name_prefix}Class{self.class_name_index}"
        self.class_name_index += 1
        return name

    def generate_method_name(self) -> str:
        """生成方法名"""
        prefix = random.choice(self.METHOD_PREFIXES)
        suffix = random.choice(self.METHOD_SUFFIXES)
        return f"{prefix}{suffix}"

    def generate_property_name(self) -> str:
        """生成属性名"""
        suffix = random.choice(self.METHOD_SUFFIXES).lower()
        return f"{suffix}Property"

    def generate_simple_method_body(self, return_type: str) -> str:
        """生成简单方法体"""
        if return_type == "void" or return_type == "Void":
            return "// Simple operation\nNSLog(@\"Method executed\");"
        elif return_type in ["NSString", "String"]:
            return 'return @"result";' if self.language == CodeLanguage.OBJC else 'return "result"'
        elif return_type in ["NSNumber", "Int", "Double"]:
            value = random.randint(1, 100)
            if self.language == CodeLanguage.OBJC:
                return f"return @({value});"
            else:
                return f"return {value}"
        elif return_type in ["BOOL", "Bool"]:
            value = random.choice(["YES", "NO"]) if self.language == CodeLanguage.OBJC else random.choice(["true", "false"])
            return f"return {value};"
        else:
            return "return nil;" if self.language == CodeLanguage.OBJC else "return nil"

    def generate_moderate_method_body(self, return_type: str, params: List[Tuple[str, str]]) -> str:
        """生成中等复杂度方法体"""
        lines = []

        # 添加一些条件判断
        if params:
            param_name = params[0][0]
            lines.append(f"if ({param_name} != nil) {{")
            lines.append(f"    NSLog(@\"Parameter is valid\");")
            lines.append("} else {")
            lines.append(f"    NSLog(@\"Parameter is nil\");")
            lines.append("}")

        # 添加循环
        loop_var = random.randint(5, 10)
        lines.append(f"for (int i = 0; i < {loop_var}; i++) {{")
        lines.append(f"    // Loop iteration")
        lines.append("}")

        # 返回值
        return_stmt = self.generate_simple_method_body(return_type)
        lines.append(return_stmt)

        return "\n".join(lines)

    def generate_complex_method_body(self, return_type: str, params: List[Tuple[str, str]]) -> str:
        """生成复杂方法体"""
        lines = []

        # 创建局部变量
        lines.append("NSMutableArray *tempArray = [NSMutableArray array];")
        lines.append("NSInteger counter = 0;")
        lines.append("")

        # 嵌套循环
        lines.append("for (int i = 0; i < 10; i++) {")
        lines.append("    for (int j = 0; j < 5; j++) {")
        lines.append("        counter += i * j;")
        lines.append("        if (counter % 2 == 0) {")
        lines.append("            [tempArray addObject:@(counter)];")
        lines.append("        }")
        lines.append("    }")
        lines.append("}")
        lines.append("")

        # Switch语句
        lines.append("switch (counter % 3) {")
        lines.append("    case 0:")
        lines.append("        NSLog(@\"Case 0\");")
        lines.append("        break;")
        lines.append("    case 1:")
        lines.append("        NSLog(@\"Case 1\");")
        lines.append("        break;")
        lines.append("    default:")
        lines.append("        NSLog(@\"Default case\");")
        lines.append("        break;")
        lines.append("}")
        lines.append("")

        # 返回值
        return_stmt = self.generate_simple_method_body(return_type)
        lines.append(return_stmt)

        return "\n".join(lines)

    def generate_method(self) -> GarbageMethod:
        """生成垃圾方法"""
        method_name = self.generate_method_name()

        # 确定返回类型
        types = self.OBJC_TYPES if self.language == CodeLanguage.OBJC else self.SWIFT_TYPES
        return_type = random.choice(types + ["void", "BOOL"])

        # 生成参数
        param_count = random.randint(0, 3)
        parameters = []
        for i in range(param_count):
            param_name = f"param{i+1}"
            param_type = random.choice(types)
            parameters.append((param_name, param_type))

        # 生成方法体
        if self.complexity == ComplexityLevel.SIMPLE:
            body = self.generate_simple_method_body(return_type)
        elif self.complexity == ComplexityLevel.MODERATE:
            body = self.generate_moderate_method_body(return_type, parameters)
        else:
            body = self.generate_complex_method_body(return_type, parameters)

        return GarbageMethod(
            name=method_name,
            return_type=return_type,
            parameters=parameters,
            body=body,
            is_static=random.choice([True, False])
        )

    def generate_property(self) -> GarbageProperty:
        """生成垃圾属性"""
        prop_name = self.generate_property_name()
        types = self.OBJC_TYPES if self.language == CodeLanguage.OBJC else self.SWIFT_TYPES
        prop_type = random.choice(types)

        # Swift可以有默认值
        default_value = None
        if self.language == CodeLanguage.SWIFT:
            if prop_type == "String":
                default_value = '""'
            elif prop_type in ["Int", "Double"]:
                default_value = "0"
            elif prop_type == "Bool":
                default_value = "false"

        return GarbageProperty(
            name=prop_name,
            property_type=prop_type,
            is_readonly=random.choice([True, False]),
            default_value=default_value
        )

    def generate_class(
        self,
        num_properties: int = 3,
        num_methods: int = 5
    ) -> GarbageClass:
        """
        生成垃圾类

        Args:
            num_properties: 属性数量
            num_methods: 方法数量

        Returns:
            GarbageClass: 生成的垃圾类
        """
        class_name = self.generate_class_name()

        # 生成属性
        properties = [self.generate_property() for _ in range(num_properties)]

        # 生成方法
        methods = [self.generate_method() for _ in range(num_methods)]

        garbage_class = GarbageClass(
            name=class_name,
            language=self.language,
            properties=properties,
            methods=methods
        )

        self.generated_classes.append(garbage_class)
        return garbage_class

    def generate_classes(
        self,
        count: int = 10,
        min_properties: int = 2,
        max_properties: int = 5,
        min_methods: int = 3,
        max_methods: int = 8
    ) -> List[GarbageClass]:
        """
        批量生成垃圾类

        Args:
            count: 生成数量
            min_properties: 最少属性数
            max_properties: 最多属性数
            min_methods: 最少方法数
            max_methods: 最多方法数

        Returns:
            List[GarbageClass]: 生成的垃圾类列表
        """
        classes = []
        for _ in range(count):
            num_props = random.randint(min_properties, max_properties)
            num_methods = random.randint(min_methods, max_methods)
            gc = self.generate_class(num_props, num_methods)
            classes.append(gc)

        # 🆕 生成调用关系
        if self.enable_call_relationships and len(classes) >= 2:
            from .call_graph_generator import CallDensity, CallGraphGenerator

            # 转换调用密度字符串到枚举
            density_map = {
                "low": CallDensity.LOW,
                "medium": CallDensity.MEDIUM,
                "high": CallDensity.HIGH
            }
            density = density_map.get(self.call_density.lower(), CallDensity.MEDIUM)

            # 创建调用图生成器
            call_gen = CallGraphGenerator(
                density=density,
                max_depth=self.max_call_depth,
                seed=None  # 使用全局随机状态
            )

            # 构建调用图
            language_str = self.language.value
            call_graph = call_gen.build_call_graph(classes, language_str)

            # 将调用注入到方法体中
            call_gen.inject_calls_into_methods(classes, call_graph, language_str)

        return classes

    def export_to_files(self, output_dir: str) -> Dict[str, str]:
        """
        导出到文件

        Args:
            output_dir: 输出目录

        Returns:
            Dict[str, str]: {文件名: 文件路径}
        """
        from pathlib import Path

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        file_map = {}

        for gc in self.generated_classes:
            if self.language == CodeLanguage.OBJC:
                header, implementation = gc.generate_code()

                # 头文件
                h_file = output_path / f"{gc.name}.h"
                h_file.write_text(header, encoding='utf-8')
                file_map[f"{gc.name}.h"] = str(h_file)

                # 实现文件
                m_file = output_path / f"{gc.name}.m"
                m_file.write_text(implementation, encoding='utf-8')
                file_map[f"{gc.name}.m"] = str(m_file)
            else:
                # Swift单文件
                code = gc.generate_code()
                swift_file = output_path / f"{gc.name}.swift"
                swift_file.write_text(code, encoding='utf-8')
                file_map[f"{gc.name}.swift"] = str(swift_file)

        return file_map

    def get_statistics(self) -> Dict:
        """
        获取统计信息

        Returns:
            Dict: 统计数据
        """
        total_properties = sum(len(gc.properties) for gc in self.generated_classes)
        total_methods = sum(len(gc.methods) for gc in self.generated_classes)

        stats = {
            'classes_generated': len(self.generated_classes),
            'properties_generated': total_properties,
            'methods_generated': total_methods,
            'files_exported': len(self.generated_classes) * (2 if self.language == CodeLanguage.OBJC else 1),
            'call_relationships_enabled': self.enable_call_relationships
        }

        return stats


if __name__ == "__main__":
    print("=== 垃圾代码生成器测试 ===\n")

    # 测试Objective-C生成
    print("1. 测试Objective-C简单类生成:")
    objc_gen = GarbageCodeGenerator(
        language=CodeLanguage.OBJC,
        complexity=ComplexityLevel.SIMPLE,
        name_prefix="Test"
    )
    objc_class = objc_gen.generate_class(num_properties=2, num_methods=3)
    header, impl = objc_class.generate_code()
    print(f"生成类: {objc_class.name}")
    print(f"属性数: {len(objc_class.properties)}")
    print(f"方法数: {len(objc_class.methods)}")
    print("\n头文件预览（前10行）:")
    print("\n".join(header.split("\n")[:10]))

    # 测试Swift生成
    print("\n2. 测试Swift中等复杂度类生成:")
    swift_gen = GarbageCodeGenerator(
        language=CodeLanguage.SWIFT,
        complexity=ComplexityLevel.MODERATE,
        name_prefix="GC"
    )
    swift_class = swift_gen.generate_class(num_properties=3, num_methods=4)
    code = swift_class.generate_code()
    print(f"生成类: {swift_class.name}")
    print(f"属性数: {len(swift_class.properties)}")
    print(f"方法数: {len(swift_class.methods)}")
    print("\n代码预览（前15行）:")
    print("\n".join(code.split("\n")[:15]))

    # 测试批量生成
    print("\n3. 测试批量生成:")
    batch_gen = GarbageCodeGenerator(
        language=CodeLanguage.OBJC,
        complexity=ComplexityLevel.COMPLEX,
        name_prefix="GC",
        seed="test_seed"
    )
    classes = batch_gen.generate_classes(count=5)
    print(f"生成 {len(classes)} 个类:")
    for gc in classes:
        print(f"  - {gc.name}: {len(gc.properties)} 属性, {len(gc.methods)} 方法")

    # 测试导出
    print("\n4. 测试导出到文件:")
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        file_map = batch_gen.export_to_files(tmpdir)
        print(f"导出 {len(file_map)} 个文件到 {tmpdir}")
        for filename in list(file_map.keys())[:3]:
            print(f"  - {filename}")

    print("\n=== 测试完成 ===")
