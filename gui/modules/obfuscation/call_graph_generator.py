"""
调用图生成器 - 为垃圾代码生成真实的调用关系

功能：
1. 构建类之间的调用关系图
2. 生成方法之间的调用代码
3. 支持链式调用、条件调用、循环调用
4. 可配置调用深度和密度
"""

import random
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


class CallDensity(Enum):
    """调用密度"""
    LOW = (0.1, 0.3)      # 低密度：每类调用1-2个其他类
    MEDIUM = (0.3, 0.6)   # 中密度：每类调用3-5个其他类
    HIGH = (0.6, 1.0)     # 高密度：每类调用6-10个其他类


@dataclass
class CallRelationship:
    """调用关系"""
    caller_class: str           # 调用者类名
    caller_method: str          # 调用者方法名
    callee_class: str           # 被调用类名
    callee_method: str          # 被调用方法名
    call_type: str = "direct"   # 调用类型：direct, conditional, loop, chain


class CallGraphGenerator:
    """调用图生成器"""

    def __init__(
        self,
        density: CallDensity = CallDensity.MEDIUM,
        max_depth: int = 3,
        seed: Optional[str] = None
    ):
        """
        初始化调用图生成器

        Args:
            density: 调用密度（LOW/MEDIUM/HIGH）
            max_depth: 最大调用深度
            seed: 随机种子
        """
        self.density = density
        self.max_depth = max_depth
        self.call_relationships: List[CallRelationship] = []
        self.class_instances: Dict[str, str] = {}  # {类名: 实例变量名}

        if seed:
            random.seed(seed)

    def generate_instance_name(self, class_name: str) -> str:
        """
        生成实例变量名

        Args:
            class_name: 类名

        Returns:
            str: 实例变量名
        """
        # 将类名转换为小写开头的实例名
        if class_name and len(class_name) > 0:
            instance_name = class_name[0].lower() + class_name[1:]
            return f"{instance_name}Instance"
        return "instance"

    def build_call_graph(
        self,
        classes: List,  # List[GarbageClass]
        language: str   # "objc" or "swift"
    ) -> Dict[str, List[CallRelationship]]:
        """
        构建调用图

        Args:
            classes: 垃圾类列表
            language: 目标语言

        Returns:
            Dict[str, List[CallRelationship]]: {类名: [调用关系列表]}
        """
        if not classes or len(classes) < 2:
            return {}

        # 为每个类生成实例变量名
        for gc in classes:
            self.class_instances[gc.name] = self.generate_instance_name(gc.name)

        # 计算每个类应该调用多少个其他类
        min_ratio, max_ratio = self.density.value
        num_classes = len(classes)

        call_graph = {}

        for caller_class in classes:
            # 确定这个类要调用多少个其他类
            min_calls = max(1, int(num_classes * min_ratio))
            max_calls = max(min_calls + 1, int(num_classes * max_ratio))
            num_callees = random.randint(min_calls, min(max_calls, num_classes - 1))

            # 随机选择要调用的类（排除自己）
            other_classes = [c for c in classes if c.name != caller_class.name]
            callee_classes = random.sample(other_classes, min(num_callees, len(other_classes)))

            relationships = []

            # 为每个caller的方法添加调用
            for caller_method in caller_class.methods:
                # 随机选择1-2个callee类来调用
                selected_callees = random.sample(callee_classes, min(2, len(callee_classes)))

                for callee_class in selected_callees:
                    if not callee_class.methods:
                        continue

                    # 随机选择被调用的方法
                    callee_method = random.choice(callee_class.methods)

                    # 随机选择调用类型
                    call_type = random.choice(["direct", "conditional", "loop"])

                    relationship = CallRelationship(
                        caller_class=caller_class.name,
                        caller_method=caller_method.name,
                        callee_class=callee_class.name,
                        callee_method=callee_method.name,
                        call_type=call_type
                    )

                    relationships.append(relationship)
                    self.call_relationships.append(relationship)

            call_graph[caller_class.name] = relationships

        return call_graph

    def generate_call_code(
        self,
        relationship: CallRelationship,
        language: str
    ) -> str:
        """
        生成调用代码

        Args:
            relationship: 调用关系
            language: 目标语言（"objc" or "swift"）

        Returns:
            str: 调用代码
        """
        instance_name = self.class_instances.get(relationship.callee_class, "instance")
        callee_method = relationship.callee_method

        if language == "objc":
            return self._generate_objc_call_code(
                instance_name,
                relationship.callee_class,
                callee_method,
                relationship.call_type
            )
        else:
            return self._generate_swift_call_code(
                instance_name,
                relationship.callee_class,
                callee_method,
                relationship.call_type
            )

    def _generate_objc_call_code(
        self,
        instance_name: str,
        class_name: str,
        method_name: str,
        call_type: str
    ) -> str:
        """生成Objective-C调用代码"""
        lines = []

        # 创建实例
        lines.append(f"{class_name} *{instance_name} = [[{class_name} alloc] init];")

        # 根据调用类型生成不同的调用代码
        if call_type == "direct":
            # 直接调用
            lines.append(f"[{instance_name} {method_name}];")

        elif call_type == "conditional":
            # 条件调用
            lines.append(f"if ({instance_name}) {{")
            lines.append(f"    [{instance_name} {method_name}];")
            lines.append("}")

        elif call_type == "loop":
            # 循环调用
            loop_count = random.randint(3, 7)
            lines.append(f"for (int i = 0; i < {loop_count}; i++) {{")
            lines.append(f"    [{instance_name} {method_name}];")
            lines.append("}")

        return "\n".join(lines)

    def _generate_swift_call_code(
        self,
        instance_name: str,
        class_name: str,
        method_name: str,
        call_type: str
    ) -> str:
        """生成Swift调用代码"""
        lines = []

        # 创建实例
        lines.append(f"let {instance_name} = {class_name}()")

        # 根据调用类型生成不同的调用代码
        if call_type == "direct":
            # 直接调用
            lines.append(f"{instance_name}.{method_name}()")

        elif call_type == "conditional":
            # 条件调用
            lines.append(f"if let obj = {instance_name} {{")
            lines.append(f"    obj.{method_name}()")
            lines.append("}")

        elif call_type == "loop":
            # 循环调用
            loop_count = random.randint(3, 7)
            lines.append(f"for _ in 0..<{loop_count} {{")
            lines.append(f"    {instance_name}.{method_name}()")
            lines.append("}")

        return "\n".join(lines)

    def inject_calls_into_methods(
        self,
        classes: List,  # List[GarbageClass]
        call_graph: Dict[str, List[CallRelationship]],
        language: str
    ):
        """
        将调用注入到方法体中

        Args:
            classes: 垃圾类列表
            call_graph: 调用图
            language: 目标语言
        """
        for gc in classes:
            if gc.name not in call_graph:
                continue

            relationships = call_graph[gc.name]

            # 为每个方法查找对应的调用关系
            for method in gc.methods:
                # 找到调用此方法的关系
                method_relationships = [
                    r for r in relationships
                    if r.caller_method == method.name
                ]

                if not method_relationships:
                    continue

                # 生成调用代码
                call_codes = []
                for rel in method_relationships:
                    call_code = self.generate_call_code(rel, language)
                    call_codes.append(call_code)

                # 将调用代码注入到方法体
                if call_codes:
                    # 在方法体开头插入调用
                    injected_code = "\n\n// Generated call relationships\n"
                    injected_code += "\n\n".join(call_codes)
                    injected_code += "\n\n// Original method body\n"

                    method.body = injected_code + method.body

    def get_statistics(self) -> Dict:
        """获取统计信息"""
        call_types = {}
        for rel in self.call_relationships:
            call_types[rel.call_type] = call_types.get(rel.call_type, 0) + 1

        return {
            'total_calls': len(self.call_relationships),
            'call_types': call_types,
            'unique_callers': len(set(r.caller_class for r in self.call_relationships)),
            'unique_callees': len(set(r.callee_class for r in self.call_relationships))
        }


if __name__ == "__main__":
    print("=== 调用图生成器测试 ===\n")

    # 创建模拟的类结构（用于测试）
    from dataclasses import dataclass

    @dataclass
    class MockMethod:
        name: str
        body: str = ""

    @dataclass
    class MockClass:
        name: str
        methods: List[MockMethod]

    # 创建测试类
    classes = [
        MockClass("ClassA", [MockMethod("methodA1"), MockMethod("methodA2")]),
        MockClass("ClassB", [MockMethod("methodB1"), MockMethod("methodB2")]),
        MockClass("ClassC", [MockMethod("methodC1")]),
    ]

    # 测试调用图生成
    print("1. 测试调用图构建:")
    generator = CallGraphGenerator(
        density=CallDensity.MEDIUM,
        max_depth=2,
        seed="test"
    )

    call_graph = generator.build_call_graph(classes, "objc")
    print(f"  生成调用关系数: {len(generator.call_relationships)}")

    print("\n2. 调用关系详情:")
    for class_name, relationships in call_graph.items():
        print(f"  {class_name}:")
        for rel in relationships[:2]:  # 只显示前2个
            print(f"    - {rel.caller_method} -> {rel.callee_class}.{rel.callee_method} ({rel.call_type})")

    print("\n3. 生成调用代码示例:")
    if generator.call_relationships:
        sample_rel = generator.call_relationships[0]
        code = generator.generate_call_code(sample_rel, "objc")
        print(f"  Objective-C调用代码:")
        print("  " + code.replace("\n", "\n  "))

    print("\n4. 统计信息:")
    stats = generator.get_statistics()
    print(f"  总调用数: {stats['total_calls']}")
    print(f"  调用类型: {stats['call_types']}")
    print(f"  涉及类数: {stats['unique_callers']} -> {stats['unique_callees']}")

    print("\n=== 测试完成 ===")
