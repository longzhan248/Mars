"""
测试垃圾代码调用关系生成功能

验证：
1. 调用关系能否正确生成
2. 调用代码能否注入到方法体中
3. 生成的代码格式是否正确
4. 调用密度配置是否生效
"""

import unittest
import sys
import os
import tempfile
from pathlib import Path

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from gui.modules.obfuscation.garbage_generator import (
    GarbageCodeGenerator,
    CodeLanguage,
    ComplexityLevel
)
from gui.modules.obfuscation.call_graph_generator import (
    CallGraphGenerator,
    CallDensity,
    CallRelationship
)


class TestCallRelationships(unittest.TestCase):
    """测试调用关系生成"""

    def test_call_graph_generator_initialization(self):
        """测试调用图生成器初始化"""
        generator = CallGraphGenerator(
            density=CallDensity.MEDIUM,
            max_depth=3,
            seed="test"
        )

        self.assertEqual(generator.density, CallDensity.MEDIUM)
        self.assertEqual(generator.max_depth, 3)
        self.assertEqual(len(generator.call_relationships), 0)

    def test_instance_name_generation(self):
        """测试实例名称生成"""
        generator = CallGraphGenerator()

        name1 = generator.generate_instance_name("MyClass")
        self.assertEqual(name1, "myClassInstance")

        name2 = generator.generate_instance_name("TestViewController")
        self.assertEqual(name2, "testViewControllerInstance")

    def test_build_call_graph_objc(self):
        """测试构建Objective-C调用图"""
        # 生成垃圾类
        gen = GarbageCodeGenerator(
            language=CodeLanguage.OBJC,
            complexity=ComplexityLevel.SIMPLE,
            name_prefix="Test",
            seed="test"
        )
        classes = [gen.generate_class(num_properties=1, num_methods=2) for _ in range(3)]

        # 构建调用图
        call_gen = CallGraphGenerator(
            density=CallDensity.MEDIUM,
            seed="test"
        )
        call_graph = call_gen.build_call_graph(classes, "objc")

        # 验证调用图
        self.assertGreater(len(call_gen.call_relationships), 0, "应该生成调用关系")
        self.assertEqual(len(call_graph), len(classes), "每个类都应该有调用关系")

        # 验证调用关系结构
        for class_name, relationships in call_graph.items():
            self.assertIsInstance(relationships, list)
            for rel in relationships:
                self.assertIsInstance(rel, CallRelationship)
                self.assertIn(rel.call_type, ["direct", "conditional", "loop"])

    def test_build_call_graph_swift(self):
        """测试构建Swift调用图"""
        # 生成垃圾类
        gen = GarbageCodeGenerator(
            language=CodeLanguage.SWIFT,
            complexity=ComplexityLevel.SIMPLE,
            name_prefix="Test",
            seed="test"
        )
        classes = [gen.generate_class(num_properties=1, num_methods=2) for _ in range(3)]

        # 构建调用图
        call_gen = CallGraphGenerator(
            density=CallDensity.MEDIUM,
            seed="test"
        )
        call_graph = call_gen.build_call_graph(classes, "swift")

        # 验证调用图
        self.assertGreater(len(call_gen.call_relationships), 0, "应该生成调用关系")

    def test_generate_objc_call_code(self):
        """测试生成Objective-C调用代码"""
        call_gen = CallGraphGenerator()

        rel = CallRelationship(
            caller_class="ClassA",
            caller_method="methodA",
            callee_class="ClassB",
            callee_method="methodB",
            call_type="direct"
        )

        code = call_gen.generate_call_code(rel, "objc")

        # 验证生成的代码包含关键元素
        self.assertIn("ClassB", code)
        self.assertIn("alloc", code)
        self.assertIn("init", code)
        self.assertIn("methodB", code)

    def test_generate_swift_call_code(self):
        """测试生成Swift调用代码"""
        call_gen = CallGraphGenerator()

        rel = CallRelationship(
            caller_class="ClassA",
            caller_method="methodA",
            callee_class="ClassB",
            callee_method="methodB",
            call_type="direct"
        )

        code = call_gen.generate_call_code(rel, "swift")

        # 验证生成的代码包含关键元素
        self.assertIn("ClassB", code)
        self.assertIn("let", code)
        self.assertIn("methodB", code)

    def test_inject_calls_into_methods(self):
        """测试将调用注入到方法体"""
        # 生成垃圾类
        gen = GarbageCodeGenerator(
            language=CodeLanguage.OBJC,
            complexity=ComplexityLevel.SIMPLE,
            name_prefix="Test",
            seed="test"
        )
        classes = [gen.generate_class(num_properties=1, num_methods=2) for _ in range(3)]

        # 记录原始方法体
        original_bodies = {}
        for gc in classes:
            for method in gc.methods:
                original_bodies[f"{gc.name}.{method.name}"] = method.body

        # 构建并注入调用
        call_gen = CallGraphGenerator(density=CallDensity.LOW, seed="test")
        call_graph = call_gen.build_call_graph(classes, "objc")
        call_gen.inject_calls_into_methods(classes, call_graph, "objc")

        # 验证方法体被修改
        modified_count = 0
        for gc in classes:
            for method in gc.methods:
                key = f"{gc.name}.{method.name}"
                if method.body != original_bodies[key]:
                    modified_count += 1
                    # 验证注入了调用代码
                    self.assertIn("// Generated call relationships", method.body)

        self.assertGreater(modified_count, 0, "至少应该有一些方法被修改")

    def test_garbage_generator_with_call_relationships(self):
        """测试垃圾代码生成器集成调用关系"""
        gen = GarbageCodeGenerator(
            language=CodeLanguage.OBJC,
            complexity=ComplexityLevel.MODERATE,
            name_prefix="GC",
            seed="test",
            enable_call_relationships=True,
            call_density="medium",
            max_call_depth=2
        )

        # 生成类
        classes = gen.generate_classes(count=5)

        # 验证生成了类
        self.assertEqual(len(classes), 5)

        # 验证至少有一些方法包含调用关系
        has_call_relationships = False
        for gc in classes:
            for method in gc.methods:
                if "// Generated call relationships" in method.body:
                    has_call_relationships = True
                    # 验证包含alloc/init模式
                    self.assertIn("alloc", method.body)
                    break
            if has_call_relationships:
                break

        self.assertTrue(has_call_relationships, "应该生成调用关系")

    def test_garbage_generator_without_call_relationships(self):
        """测试禁用调用关系的垃圾代码生成"""
        gen = GarbageCodeGenerator(
            language=CodeLanguage.OBJC,
            complexity=ComplexityLevel.SIMPLE,
            name_prefix="GC",
            seed="test",
            enable_call_relationships=False
        )

        # 生成类
        classes = gen.generate_classes(count=3)

        # 验证没有注入调用关系
        for gc in classes:
            for method in gc.methods:
                self.assertNotIn("// Generated call relationships", method.body)

    def test_call_density_configuration(self):
        """测试不同调用密度配置"""
        densities = ["low", "medium", "high"]

        for density_str in densities:
            with self.subTest(density=density_str):
                gen = GarbageCodeGenerator(
                    language=CodeLanguage.OBJC,
                    complexity=ComplexityLevel.SIMPLE,
                    name_prefix="Test",
                    seed="test",
                    enable_call_relationships=True,
                    call_density=density_str
                )

                classes = gen.generate_classes(count=10)
                self.assertEqual(len(classes), 10)

    def test_call_relationships_statistics(self):
        """测试调用关系统计"""
        gen = GarbageCodeGenerator(
            language=CodeLanguage.OBJC,
            enable_call_relationships=True
        )

        gen.generate_classes(count=5)
        stats = gen.get_statistics()

        # 验证统计信息包含调用关系字段
        self.assertIn('call_relationships_enabled', stats)
        self.assertTrue(stats['call_relationships_enabled'])

    def test_export_with_call_relationships(self):
        """测试导出包含调用关系的代码"""
        gen = GarbageCodeGenerator(
            language=CodeLanguage.OBJC,
            complexity=ComplexityLevel.MODERATE,
            name_prefix="Test",
            seed="test",
            enable_call_relationships=True,
            call_density="medium"
        )

        classes = gen.generate_classes(count=3)

        # 导出到临时目录
        with tempfile.TemporaryDirectory() as tmpdir:
            file_map = gen.export_to_files(tmpdir)

            # 验证文件生成
            self.assertGreater(len(file_map), 0)

            # 检查至少一个文件包含调用关系
            has_calls = False
            for filepath in file_map.values():
                if filepath.endswith('.m'):
                    content = Path(filepath).read_text()
                    if "// Generated call relationships" in content:
                        has_calls = True
                        # 验证包含alloc/init
                        self.assertIn("alloc", content)
                        break

            self.assertTrue(has_calls, "导出的文件应该包含调用关系")


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)
