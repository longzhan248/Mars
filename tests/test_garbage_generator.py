#!/usr/bin/env python3
"""
垃圾代码生成器测试

测试垃圾代码生成器的完整功能
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path
import unittest

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from gui.modules.obfuscation.garbage_generator import (
    GarbageCodeGenerator,
    CodeLanguage,
    ComplexityLevel,
    GarbageClass,
    GarbageMethod,
    GarbageProperty
)


class TestGarbageCodeGenerator(unittest.TestCase):
    """垃圾代码生成器测试"""

    def setUp(self):
        """测试准备"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """清理临时文件"""
        shutil.rmtree(self.temp_dir)

    def test_objc_simple_class_generation(self):
        """测试Objective-C简单类生成"""
        gen = GarbageCodeGenerator(
            language=CodeLanguage.OBJC,
            complexity=ComplexityLevel.SIMPLE,
            name_prefix="Test"
        )

        gc = gen.generate_class(num_properties=2, num_methods=3)

        # 验证基本信息
        self.assertEqual(gc.language, CodeLanguage.OBJC)
        self.assertEqual(len(gc.properties), 2)
        self.assertEqual(len(gc.methods), 3)
        self.assertTrue(gc.name.startswith("Test"))

        # 验证代码生成
        header, impl = gc.generate_code()
        self.assertIn("@interface", header)
        self.assertIn("@property", header)
        self.assertIn("@implementation", impl)

    def test_swift_class_generation(self):
        """测试Swift类生成"""
        gen = GarbageCodeGenerator(
            language=CodeLanguage.SWIFT,
            complexity=ComplexityLevel.MODERATE,
            name_prefix="GC"
        )

        gc = gen.generate_class(num_properties=3, num_methods=4)

        # 验证基本信息
        self.assertEqual(gc.language, CodeLanguage.SWIFT)
        self.assertEqual(len(gc.properties), 3)
        self.assertEqual(len(gc.methods), 4)

        # 验证代码生成
        code = gc.generate_code()
        self.assertIn("class", code)
        self.assertIn("var", code)
        self.assertIn("func", code)

    def test_method_generation_no_parameters(self):
        """测试无参数方法生成"""
        gen = GarbageCodeGenerator(language=CodeLanguage.OBJC)

        method = GarbageMethod(
            name="testMethod",
            return_type="void",
            parameters=[],
            body="NSLog(@\"test\");"
        )

        gc = GarbageClass(
            name="TestClass",
            language=CodeLanguage.OBJC,
            methods=[method]
        )

        header, impl = gc.generate_code()
        self.assertIn("- (void)testMethod;", header)
        self.assertIn("- (void)testMethod {", impl)

    def test_method_generation_with_parameters(self):
        """测试带参数方法生成"""
        gen = GarbageCodeGenerator(language=CodeLanguage.OBJC)

        method = GarbageMethod(
            name="processData",
            return_type="NSString",
            parameters=[("data", "NSData"), ("options", "NSDictionary")],
            body="return @\"result\";"
        )

        gc = GarbageClass(
            name="TestClass",
            language=CodeLanguage.OBJC,
            methods=[method]
        )

        header, impl = gc.generate_code()
        self.assertIn("processData:(NSData)data options:(NSDictionary)options", header)

    def test_property_generation_objc(self):
        """测试Objective-C属性生成"""
        prop = GarbageProperty(
            name="userName",
            property_type="NSString",
            is_readonly=True
        )

        gc = GarbageClass(
            name="TestClass",
            language=CodeLanguage.OBJC,
            properties=[prop]
        )

        header, _ = gc.generate_code()
        self.assertIn("@property (nonatomic, readonly)", header)
        self.assertIn("NSString *userName", header)

    def test_property_generation_swift(self):
        """测试Swift属性生成"""
        prop = GarbageProperty(
            name="userName",
            property_type="String",
            is_readonly=True
        )

        gc = GarbageClass(
            name="TestClass",
            language=CodeLanguage.SWIFT,
            properties=[prop]
        )

        code = gc.generate_code()
        self.assertIn("let userName: String", code)

    def test_batch_generation(self):
        """测试批量生成"""
        gen = GarbageCodeGenerator(
            language=CodeLanguage.OBJC,
            complexity=ComplexityLevel.MODERATE,
            seed="test_seed"
        )

        classes = gen.generate_classes(count=5)

        # 验证生成数量
        self.assertEqual(len(classes), 5)
        self.assertEqual(len(gen.generated_classes), 5)

        # 验证每个类都有属性和方法
        for gc in classes:
            self.assertGreater(len(gc.properties), 0)
            self.assertGreater(len(gc.methods), 0)

    def test_deterministic_generation(self):
        """测试确定性生成（相同种子产生相同结果）"""
        gen1 = GarbageCodeGenerator(seed="fixed_seed")
        gen2 = GarbageCodeGenerator(seed="fixed_seed")

        gc1 = gen1.generate_class(num_properties=3, num_methods=3)
        gc2 = gen2.generate_class(num_properties=3, num_methods=3)

        # 相同种子应该产生相同的类名
        self.assertEqual(gc1.name, gc2.name)

    def test_complexity_levels(self):
        """测试不同复杂度级别"""
        # 简单级别
        simple_gen = GarbageCodeGenerator(complexity=ComplexityLevel.SIMPLE)
        simple_method = simple_gen.generate_method()
        simple_body_lines = len(simple_method.body.split('\n'))

        # 复杂级别
        complex_gen = GarbageCodeGenerator(complexity=ComplexityLevel.COMPLEX)
        complex_method = complex_gen.generate_method()
        complex_body_lines = len(complex_method.body.split('\n'))

        # 复杂方法的代码行数应该更多
        self.assertGreater(complex_body_lines, simple_body_lines)

    def test_export_to_files_objc(self):
        """测试导出Objective-C文件"""
        gen = GarbageCodeGenerator(language=CodeLanguage.OBJC)
        classes = gen.generate_classes(count=3)

        file_map = gen.export_to_files(self.temp_dir)

        # 验证文件数量（每个类2个文件：.h和.m）
        self.assertEqual(len(file_map), 6)

        # 验证文件存在
        for filepath in file_map.values():
            self.assertTrue(Path(filepath).exists())

        # 验证文件内容
        for filename, filepath in file_map.items():
            content = Path(filepath).read_text()
            if filename.endswith('.h'):
                self.assertIn('@interface', content)
            else:
                self.assertIn('@implementation', content)

    def test_export_to_files_swift(self):
        """测试导出Swift文件"""
        gen = GarbageCodeGenerator(language=CodeLanguage.SWIFT)
        classes = gen.generate_classes(count=3)

        file_map = gen.export_to_files(self.temp_dir)

        # 验证文件数量（每个类1个.swift文件）
        self.assertEqual(len(file_map), 3)

        # 验证文件存在
        for filepath in file_map.values():
            self.assertTrue(Path(filepath).exists())

        # 验证文件内容
        for filepath in file_map.values():
            content = Path(filepath).read_text()
            self.assertIn('class', content)
            self.assertIn('import Foundation', content)

    def test_method_name_generation(self):
        """测试方法名生成"""
        gen = GarbageCodeGenerator()

        # 生成多个方法名，验证格式
        for _ in range(10):
            method_name = gen.generate_method_name()
            # 方法名应该是驼峰格式
            self.assertTrue(method_name[0].islower())
            self.assertTrue(any(c.isupper() for c in method_name))

    def test_class_name_generation(self):
        """测试类名生成"""
        gen = GarbageCodeGenerator(name_prefix="Test")

        # 生成多个类名，验证格式和唯一性
        names = set()
        for _ in range(5):
            class_name = gen.generate_class_name()
            self.assertTrue(class_name.startswith("Test"))
            names.add(class_name)

        # 验证唯一性
        self.assertEqual(len(names), 5)

    def test_static_method_generation(self):
        """测试静态方法生成"""
        gen = GarbageCodeGenerator(language=CodeLanguage.OBJC)

        static_method = GarbageMethod(
            name="sharedInstance",
            return_type="instancetype",
            parameters=[],
            body="return [[self alloc] init];",
            is_static=True
        )

        gc = GarbageClass(
            name="TestClass",
            language=CodeLanguage.OBJC,
            methods=[static_method]
        )

        header, impl = gc.generate_code()
        # Objective-C中静态方法用+号
        self.assertIn("+ (instancetype)sharedInstance", header)
        self.assertIn("+ (instancetype)sharedInstance {", impl)


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestGarbageCodeGenerator)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result


if __name__ == '__main__':
    print("=" * 70)
    print("垃圾代码生成器测试")
    print("=" * 70)
    print()

    result = run_tests()

    print()
    print("=" * 70)
    print("测试总结:")
    print("=" * 70)
    print(f"运行测试数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")

    if result.wasSuccessful():
        print("\n🎉 所有测试通过！垃圾代码生成器功能正常")
        sys.exit(0)
    else:
        print(f"\n⚠️  {len(result.failures) + len(result.errors)} 个测试未通过")
        sys.exit(1)
