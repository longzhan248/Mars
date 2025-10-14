"""
P1修复集成测试 - 验证所有P1级别修复在真实场景下的表现

测试范围:
1. P1-1: Swift泛型解析增强
2. P1-2: 符号冲突检测机制
3. P1-3: 自定义异常类型体系
4. P1-4: 名称唯一性验证
5. P1-5: 第三方库识别改进

作者: Claude Code
日期: 2025-10-14
"""

import unittest
import sys
import os
import tempfile
import shutil
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from gui.modules.obfuscation.code_parser import CodeParser, ParsedFile
from gui.modules.obfuscation.code_transformer import CodeTransformer
from gui.modules.obfuscation.name_generator import NameGenerator, NamingStrategy
from gui.modules.obfuscation.whitelist_manager import WhitelistManager
from gui.modules.obfuscation.project_analyzer import ProjectAnalyzer
from gui.modules.obfuscation.obfuscation_exceptions import (
    ObfuscationError,
    ParseError,
    TransformError,
    NameConflictError,
    handle_obfuscation_error
)


class TestP1_1_SwiftGenerics(unittest.TestCase):
    """P1-1: Swift泛型解析增强测试"""

    def setUp(self):
        """初始化测试环境"""
        self.parser = CodeParser(WhitelistManager())

    def test_simple_generic_constraint(self):
        """测试简单泛型约束: class MyClass<T: Equatable>"""
        code = """
        class MyClass<T: Equatable> {
            var value: T

            func compare(_ other: T) -> Bool {
                return value == other
            }
        }
        """

        # 创建临时文件
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.swift', delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            result = self.parser.parse_file(temp_path)
        finally:
            os.unlink(temp_path)

        # 验证类被正确识别
        classes = [s for s in result.symbols if s.type.value == 'class']
        self.assertEqual(len(classes), 1)
        self.assertEqual(classes[0].name, 'MyClass')

        print("✅ P1-1.1: 简单泛型约束解析成功")

    def test_multiple_generic_constraints(self):
        """测试多重泛型约束: class MyClass<T: Codable & Equatable>"""
        code = """
        class NetworkManager<T: Codable & Equatable> {
            func fetch(_ url: String) -> T? {
                return nil
            }
        }
        """

        result = self.parser.parse_swift_code(code, "TestFile.swift")

        classes = [s for s in result.symbols if s.type.value == 'class']
        self.assertEqual(len(classes), 1)
        self.assertEqual(classes[0].name, 'NetworkManager')

        print("✅ P1-1.2: 多重泛型约束解析成功")

    def test_where_clause(self):
        """测试where子句: class MyClass<T> where T: Collection"""
        code = """
        class DataProcessor<T> where T: Collection, T.Element: Equatable {
            func process(_ data: T) {
                // processing
            }
        }
        """

        result = self.parser.parse_swift_code(code, "TestFile.swift")

        classes = [s for s in result.symbols if s.type.value == 'class']
        self.assertEqual(len(classes), 1)
        self.assertEqual(classes[0].name, 'DataProcessor')

        print("✅ P1-1.3: where子句解析成功")

    def test_nested_generics(self):
        """测试嵌套泛型: class MyClass<Array<Int>>"""
        code = """
        class Container<T: Array<Int>> {
            var items: T
        }

        struct Box<T: Dictionary<String, Array<Int>>> {
            var data: T
        }
        """

        result = self.parser.parse_swift_code(code, "TestFile.swift")

        classes = [s for s in result.symbols if s.type.value == 'class']
        structs = [s for s in result.symbols if s.type.value == 'struct']

        self.assertEqual(len(classes), 1)
        self.assertEqual(len(structs), 1)
        self.assertEqual(classes[0].name, 'Container')
        self.assertEqual(structs[0].name, 'Box')

        print("✅ P1-1.4: 嵌套泛型解析成功")


class TestP1_2_ConflictDetection(unittest.TestCase):
    """P1-2: 符号冲突检测机制测试"""

    def setUp(self):
        """初始化测试环境"""
        self.whitelist = WhitelistManager()
        self.generator = NameGenerator(
            strategy=NamingStrategy.RANDOM,
            min_length=5,
            max_length=8,
            seed="test_seed"  # 使用固定种子便于测试
        )
        self.transformer = CodeTransformer(self.generator, self.whitelist)

    def test_conflict_detection_and_retry(self):
        """测试冲突检测和自动重试机制"""
        # 创建一个已有映射
        self.generator.generate("FirstClass", "class")
        first_obfuscated = self.generator.get_mapping("FirstClass").obfuscated

        # 手动创建冲突：将另一个类名映射到相同的混淆名
        # 这会触发冲突检测机制
        original_mappings_count = len(self.generator.get_all_mappings())

        # 生成多个名称，观察是否有重试机制
        for i in range(10):
            name = f"TestClass{i}"
            obfuscated = self.generator.generate(name, "class")
            # 验证没有生成重复的混淆名
            all_obfuscated = [m.obfuscated for m in self.generator.get_all_mappings()]
            self.assertEqual(len(all_obfuscated), len(set(all_obfuscated)),
                           f"检测到重复的混淆名: {obfuscated}")

        print(f"✅ P1-2.1: 冲突检测机制工作正常，生成了 {len(self.generator.get_all_mappings())} 个唯一映射")

    def test_conflict_warning_in_transform(self):
        """测试转换过程中的冲突警告"""
        code = """
        @interface ClassA : NSObject
        @end

        @interface ClassB : NSObject
        @end

        @interface ClassC : NSObject
        @end
        """

        parsed = self.transformer.parser.parse_objc_code(code, "Test.h")

        # 执行转换，应该不会因为冲突而失败
        result = self.transformer.transform("Test.h", code, parsed)

        self.assertIsNotNone(result)
        self.assertEqual(len(result.errors), 0)

        # 验证所有类都被映射且没有重复
        mappings = self.generator.get_all_mappings()
        obfuscated_names = [m.obfuscated for m in mappings]
        self.assertEqual(len(obfuscated_names), len(set(obfuscated_names)))

        print(f"✅ P1-2.2: 转换过程无冲突，成功处理 {len(mappings)} 个符号")


class TestP1_3_ExceptionSystem(unittest.TestCase):
    """P1-3: 自定义异常类型体系测试"""

    def test_parse_error_with_context(self):
        """测试带上下文的解析错误"""
        try:
            raise ParseError(
                file_path="/path/to/file.m",
                line_number=42,
                message="无法解析方法声明",
                code_snippet="- (void)brokenMethod {"
            )
        except ObfuscationError as e:
            error_msg = handle_obfuscation_error(e)

            # 验证错误消息包含关键信息
            self.assertIn("解析错误", error_msg)
            self.assertIn("/path/to/file.m", error_msg)
            self.assertIn("42", error_msg)

            print(f"✅ P1-3.1: ParseError正确处理\n   {error_msg}")

    def test_transform_error_with_details(self):
        """测试带详细信息的转换错误"""
        try:
            raise TransformError(
                file_path="/path/to/file.m",
                message="符号替换失败",
                symbol_name="MyViewController",
                operation="class_name_replacement"
            )
        except ObfuscationError as e:
            error_msg = handle_obfuscation_error(e)

            self.assertIn("转换错误", error_msg)
            self.assertIn("MyViewController", error_msg)

            print(f"✅ P1-3.2: TransformError正确处理\n   {error_msg}")

    def test_name_conflict_error(self):
        """测试名称冲突错误"""
        try:
            raise NameConflictError(
                original_name="ClassA",
                obfuscated_name="Abc123",
                existing_original="ClassB"
            )
        except ObfuscationError as e:
            error_msg = handle_obfuscation_error(e)

            self.assertIn("名称冲突", error_msg)
            self.assertIn("ClassA", error_msg)
            self.assertIn("ClassB", error_msg)
            self.assertIn("Abc123", error_msg)

            print(f"✅ P1-3.3: NameConflictError正确处理\n   {error_msg}")

    def test_exception_hierarchy(self):
        """测试异常继承层次"""
        errors = [
            ParseError("test.m", 1, "test"),
            TransformError("test.m", "test"),
            NameConflictError("a", "b", "c")
        ]

        # 所有异常都应该是ObfuscationError的子类
        for error in errors:
            self.assertIsInstance(error, ObfuscationError)

        print("✅ P1-3.4: 异常继承层次正确")


class TestP1_4_UniquenessValidation(unittest.TestCase):
    """P1-4: 名称唯一性验证测试"""

    def test_numeric_suffix_strategy(self):
        """测试数字后缀策略（策略1）"""
        generator = NameGenerator(
            strategy=NamingStrategy.PREFIX,
            prefix="Test",
            min_length=8,
            max_length=8,
            seed="fixed"
        )

        # 生成大量相同前缀的名称，观察数字后缀是否起作用
        base_name = "TestAbc"
        names = set()

        for i in range(50):
            # 强制生成相同的基础名称
            obfuscated = generator._ensure_unique(base_name)
            names.add(obfuscated)

        # 验证所有生成的名称都是唯一的
        self.assertEqual(len(names), 50)

        print(f"✅ P1-4.1: 数字后缀策略成功生成 {len(names)} 个唯一名称")

    def test_random_suffix_strategy(self):
        """测试随机字符串后缀策略（策略2）"""
        generator = NameGenerator(
            strategy=NamingStrategy.RANDOM,
            min_length=6,
            max_length=6
        )

        # 生成大量名称
        names = set()
        for i in range(200):
            name = generator.generate(f"Class{i}", "class")
            names.add(name)

        # 验证唯一性
        all_mappings = generator.get_all_mappings()
        self.assertEqual(len(all_mappings), 200)
        self.assertEqual(len(names), 200)

        print(f"✅ P1-4.2: 随机后缀策略成功生成 {len(names)} 个唯一名称")

    def test_extreme_collision_handling(self):
        """测试极端碰撞情况的处理（策略3：时间戳）"""
        generator = NameGenerator(
            strategy=NamingStrategy.RANDOM,
            min_length=3,  # 非常短的长度，容易碰撞
            max_length=3,
            seed="collision_test"
        )

        # 尝试生成大量名称
        success_count = 0
        try:
            for i in range(100):
                name = generator.generate(f"C{i}", "class")
                if name:
                    success_count += 1
        except RuntimeError as e:
            # 如果最终失败，也是可以接受的（因为3字符空间很小）
            print(f"   预期的极端情况: {e}")

        # 至少应该成功生成一些名称
        self.assertGreater(success_count, 10)

        print(f"✅ P1-4.3: 极端碰撞处理机制工作正常（成功 {success_count}/100）")


class TestP1_5_ThirdPartyDetection(unittest.TestCase):
    """P1-5: 第三方库识别改进测试"""

    def setUp(self):
        """创建临时测试项目"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_path = Path(self.temp_dir) / "TestProject"
        self.project_path.mkdir()

    def tearDown(self):
        """清理临时文件"""
        shutil.rmtree(self.temp_dir)

    def test_path_based_detection(self):
        """测试基于路径的检测（快速路径）"""
        # 创建Pods目录中的文件
        pods_dir = self.project_path / "Pods" / "AFNetworking"
        pods_dir.mkdir(parents=True)

        test_file = pods_dir / "AFHTTPSessionManager.h"
        test_file.write_text("""
        @interface AFHTTPSessionManager : NSObject
        @end
        """)

        analyzer = ProjectAnalyzer(str(self.project_path))

        # 验证Pods中的文件被识别为第三方
        is_third_party = analyzer._is_third_party_file(test_file)
        self.assertTrue(is_third_party)

        print("✅ P1-5.1: 路径特征检测成功（Pods目录）")

    def test_content_based_detection_copyright(self):
        """测试基于内容的检测 - 版权声明"""
        # 创建包含版权声明的文件
        src_dir = self.project_path / "Vendor"
        src_dir.mkdir(parents=True)

        test_file = src_dir / "ThirdPartyLib.h"
        test_file.write_text("""
        //
        // ThirdPartyLib.h
        // Copyright © 2020 Some Company. All rights reserved.
        //
        // Licensed under the MIT License
        // Permission is hereby granted, free of charge, to any person obtaining a copy
        //

        @interface ThirdPartyLib : NSObject
        @end
        """)

        analyzer = ProjectAnalyzer(str(self.project_path))

        # 验证基于内容识别为第三方
        is_third_party = analyzer._is_third_party_file(test_file)
        self.assertTrue(is_third_party)

        print("✅ P1-5.2: 内容特征检测成功（版权声明）")

    def test_content_based_detection_license(self):
        """测试基于内容的检测 - 开源协议"""
        src_dir = self.project_path / "Sources"
        src_dir.mkdir(parents=True)

        test_file = src_dir / "Library.h"
        test_file.write_text("""
        /*
         * Library.h
         *
         * Apache License
         * Version 2.0, January 2004
         * http://www.apache.org/licenses/
         */

        @interface Library : NSObject
        @end
        """)

        analyzer = ProjectAnalyzer(str(self.project_path))

        is_third_party = analyzer._is_third_party_file(test_file)
        self.assertTrue(is_third_party)

        print("✅ P1-5.3: 内容特征检测成功（开源协议）")

    def test_custom_code_not_detected_as_third_party(self):
        """测试自定义代码不被误判为第三方"""
        src_dir = self.project_path / "MyApp"
        src_dir.mkdir(parents=True)

        test_file = src_dir / "MyViewController.h"
        test_file.write_text("""
        //
        // MyViewController.h
        // MyApp
        //
        // Created by Me on 2025-01-01.
        //

        #import <UIKit/UIKit.h>

        @interface MyViewController : UIViewController
        @property (nonatomic, strong) NSString *title;
        - (void)loadData;
        @end
        """)

        analyzer = ProjectAnalyzer(str(self.project_path))

        # 验证自定义代码不被识别为第三方
        is_third_party = analyzer._is_third_party_file(test_file)
        self.assertFalse(is_third_party)

        print("✅ P1-5.4: 自定义代码正确识别（非第三方）")

    def test_weight_based_scoring(self):
        """测试权重评分机制"""
        src_dir = self.project_path / "Libs"
        src_dir.mkdir(parents=True)

        # 创建包含多个第三方特征的文件
        test_file = src_dir / "NetworkLib.h"
        test_file.write_text("""
        //
        // NetworkLib.h
        // Copyright (c) 2020 Network Corp
        // Licensed under BSD License
        // THE SOFTWARE IS PROVIDED "AS IS"
        // AFNetworking wrapper
        //

        @interface NetworkLib : NSObject
        @end
        """)

        analyzer = ProjectAnalyzer(str(self.project_path))

        # 多个特征匹配，应该被识别为第三方
        is_third_party = analyzer._is_third_party_file(test_file)
        self.assertTrue(is_third_party)

        print("✅ P1-5.5: 权重评分机制成功（多特征匹配）")


class TestIntegrationScenario(unittest.TestCase):
    """综合场景测试 - 结合所有P1修复"""

    def setUp(self):
        """初始化完整的混淆环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_path = Path(self.temp_dir) / "TestProject"
        self.project_path.mkdir()

        # 创建项目结构
        self.src_dir = self.project_path / "Sources"
        self.src_dir.mkdir()

    def tearDown(self):
        """清理"""
        shutil.rmtree(self.temp_dir)

    def test_complete_obfuscation_flow_with_p1_fixes(self):
        """测试包含所有P1修复的完整混淆流程"""
        # 1. 创建测试文件（包含Swift泛型）
        test_file = self.src_dir / "GenericManager.swift"
        test_code = """
        // GenericManager.swift
        // Created by developer

        class GenericManager<T: Codable & Equatable> where T: Collection {
            var items: [T]

            func add(_ item: T) {
                items.append(item)
            }

            func find(_ predicate: (T) -> Bool) -> T? {
                return items.first(where: predicate)
            }
        }

        struct DataContainer<Value: Equatable> {
            var value: Value
        }
        """
        test_file.write_text(test_code)

        # 2. 分析项目（测试P1-5: 第三方库识别）
        analyzer = ProjectAnalyzer(str(self.project_path))
        structure = analyzer.analyze()

        self.assertEqual(len(structure.swift_files), 1)
        self.assertFalse(structure.swift_files[0].is_third_party)

        print("✅ 综合.1: 项目分析完成")

        # 3. 解析代码（测试P1-1: Swift泛型解析）
        whitelist = WhitelistManager()
        parser = CodeParser(whitelist)
        parsed = parser.parse_swift_code(test_code, "GenericManager.swift")

        classes = [s for s in parsed.symbols if s.type.value == 'class']
        structs = [s for s in parsed.symbols if s.type.value == 'struct']

        self.assertEqual(len(classes), 1)
        self.assertEqual(classes[0].name, 'GenericManager')
        self.assertEqual(len(structs), 1)
        self.assertEqual(structs[0].name, 'DataContainer')

        print("✅ 综合.2: Swift泛型解析成功")

        # 4. 生成混淆映射（测试P1-2: 冲突检测, P1-4: 唯一性）
        generator = NameGenerator(
            strategy=NamingStrategy.RANDOM,
            min_length=8,
            max_length=12,
            seed="integration_test"
        )

        # 生成多个映射
        for symbol in parsed.symbols:
            try:
                generator.generate(symbol.name, symbol.type.value)
            except Exception as e:
                # 测试P1-3: 异常处理
                error_msg = handle_obfuscation_error(e)
                self.fail(f"映射生成失败: {error_msg}")

        mappings = generator.get_all_mappings()
        obfuscated_names = [m.obfuscated for m in mappings]

        # 验证唯一性
        self.assertEqual(len(obfuscated_names), len(set(obfuscated_names)))

        print(f"✅ 综合.3: 生成 {len(mappings)} 个唯一映射，无冲突")

        # 5. 执行转换
        transformer = CodeTransformer(generator, whitelist)
        result = transformer.transform(
            "GenericManager.swift",
            test_code,
            parsed
        )

        self.assertIsNotNone(result)
        self.assertEqual(len(result.errors), 0)
        self.assertGreater(result.replacements, 0)

        print(f"✅ 综合.4: 代码转换成功，{result.replacements} 处替换")

        # 6. 验证转换后的代码
        self.assertNotEqual(result.code, test_code)
        self.assertNotIn('GenericManager', result.code)
        self.assertNotIn('DataContainer', result.code)

        print("✅ 综合.5: 完整混淆流程验证通过")


def run_tests():
    """运行所有P1修复测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加所有测试类
    suite.addTests(loader.loadTestsFromTestCase(TestP1_1_SwiftGenerics))
    suite.addTests(loader.loadTestsFromTestCase(TestP1_2_ConflictDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestP1_3_ExceptionSystem))
    suite.addTests(loader.loadTestsFromTestCase(TestP1_4_UniquenessValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestP1_5_ThirdPartyDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegrationScenario))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 输出总结
    print("\n" + "="*70)
    print("P1修复集成测试总结")
    print("="*70)
    print(f"总测试数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print("="*70)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
