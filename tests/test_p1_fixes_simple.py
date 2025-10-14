"""
P1修复简化集成测试 - 快速验证所有P1级别修复

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

from gui.modules.obfuscation.code_parser import CodeParser
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


class TestP1Fixes(unittest.TestCase):
    """P1修复综合测试"""

    def test_p1_1_swift_generics(self):
        """P1-1: Swift泛型解析增强"""
        print("\n=== 测试P1-1: Swift泛型解析 ===")

        # 创建测试代码
        swift_code = """
import Foundation

// 简单泛型约束
class SimpleGeneric<T: Equatable> {
    var value: T
}

// 多重约束
class MultiConstraint<T: Codable & Equatable> {
    func process(_ value: T) {}
}

// where子句
class WhereClause<T> where T: Collection, T.Element: Equatable {
    var items: T?
}

// 嵌套泛型
struct Container<T: Array<Int>> {
    var data: T
}
"""

        # 创建临时文件并解析
        with tempfile.NamedTemporaryFile(mode='w', suffix='.swift', delete=False) as f:
            f.write(swift_code)
            temp_path = f.name

        try:
            parser = CodeParser(WhitelistManager())
            result = parser.parse_file(temp_path)

            # 验证解析结果
            classes = [s for s in result.symbols if s.type.value in ['class', 'struct']]

            self.assertGreaterEqual(len(classes), 4, f"应该解析出至少4个类/结构体，实际: {len(classes)}")

            class_names = [c.name for c in classes]
            self.assertIn('SimpleGeneric', class_names, "应该识别SimpleGeneric")
            self.assertIn('MultiConstraint', class_names, "应该识别MultiConstraint")
            self.assertIn('WhereClause', class_names, "应该识别WhereClause")
            self.assertIn('Container', class_names, "应该识别Container")

            print(f"✅ 成功解析 {len(classes)} 个泛型类/结构体:")
            for cls in classes:
                print(f"   - {cls.name}")

        finally:
            os.unlink(temp_path)

    def test_p1_2_conflict_detection(self):
        """P1-2: 符号冲突检测机制"""
        print("\n=== 测试P1-2: 符号冲突检测 ===")

        generator = NameGenerator(
            strategy=NamingStrategy.RANDOM,
            min_length=5,
            max_length=8,
            seed="test_seed"
        )

        # 生成大量名称，观察冲突检测
        names_generated = set()
        for i in range(100):
            name = generator.generate(f"Class{i}", "class")
            names_generated.add(name)

        # 验证所有生成的名称都是唯一的
        all_mappings = generator.get_all_mappings()
        obfuscated_names = [m.obfuscated for m in all_mappings]

        self.assertEqual(len(obfuscated_names), len(set(obfuscated_names)),
                        "检测到重复的混淆名")

        print(f"✅ 成功生成 {len(obfuscated_names)} 个唯一映射，无冲突")

    def test_p1_3_exception_system(self):
        """P1-3: 自定义异常类型体系"""
        print("\n=== 测试P1-3: 自定义异常类型 ===")

        exceptions_tested = []

        # 测试ParseError
        try:
            raise ParseError("/path/to/file.m", 42, "解析失败")
        except ObfuscationError as e:
            self.assertIsInstance(e, ParseError)
            msg = handle_obfuscation_error(e)
            self.assertIn("解析错误", msg)
            exceptions_tested.append("ParseError")

        # 测试TransformError
        try:
            raise TransformError("/path/to/file.m", "转换失败", symbol_name="MyClass")
        except ObfuscationError as e:
            self.assertIsInstance(e, TransformError)
            exceptions_tested.append("TransformError")

        # 测试NameConflictError
        try:
            raise NameConflictError("ClassA", "Abc123", "ClassB")
        except ObfuscationError as e:
            self.assertIsInstance(e, NameConflictError)
            exceptions_tested.append("NameConflictError")

        print(f"✅ 异常类型体系工作正常，测试了 {len(exceptions_tested)} 种异常")
        for ex in exceptions_tested:
            print(f"   - {ex}")

    def test_p1_4_uniqueness_validation(self):
        """P1-4: 名称唯一性验证"""
        print("\n=== 测试P1-4: 名称唯一性验证 ===")

        generator = NameGenerator(
            strategy=NamingStrategy.RANDOM,
            min_length=6,
            max_length=10
        )

        # 测试大量名称生成
        success_count = 0
        for i in range(300):
            try:
                name = generator.generate(f"Symbol{i}", "class")
                if name:
                    success_count += 1
            except Exception as e:
                print(f"   生成失败 (预期): {e}")
                break

        self.assertGreater(success_count, 200, f"应该成功生成至少200个名称，实际: {success_count}")

        # 验证唯一性
        all_mappings = generator.get_all_mappings()
        obfuscated_names = [m.obfuscated for m in all_mappings]
        unique_count = len(set(obfuscated_names))

        self.assertEqual(len(obfuscated_names), unique_count,
                        f"发现 {len(obfuscated_names) - unique_count} 个重复名称")

        print(f"✅ 成功生成 {success_count} 个唯一名称")
        print(f"   验证唯一性: {unique_count}/{len(obfuscated_names)}")

    def test_p1_5_third_party_detection(self):
        """P1-5: 第三方库识别改进"""
        print("\n=== 测试P1-5: 第三方库识别 ===")

        # 创建临时项目结构
        temp_dir = tempfile.mkdtemp()
        project_path = Path(temp_dir) / "TestProject"
        project_path.mkdir()

        try:
            # 1. 创建Pods目录中的文件（路径检测）
            pods_dir = project_path / "Pods" / "AFNetworking"
            pods_dir.mkdir(parents=True)
            pods_file = pods_dir / "AFHTTPSessionManager.h"
            pods_file.write_text("@interface AFHTTPSessionManager : NSObject\n@end")

            # 2. 创建包含版权声明的文件（内容检测）
            vendor_dir = project_path / "Vendor"
            vendor_dir.mkdir()
            vendor_file = vendor_dir / "ThirdPartyLib.h"
            vendor_file.write_text("""
//
// ThirdPartyLib.h
// Copyright © 2020 Some Company
// MIT License
// Permission is hereby granted, free of charge
//
@interface ThirdPartyLib : NSObject
@end
""")

            # 3. 创建自定义代码（不应被识别为第三方）
            src_dir = project_path / "MyApp"
            src_dir.mkdir()
            custom_file = src_dir / "MyViewController.h"
            custom_file.write_text("""
//
// MyViewController.h
// MyApp
//
#import <UIKit/UIKit.h>
@interface MyViewController : UIViewController
@end
""")

            # 分析项目
            analyzer = ProjectAnalyzer(str(project_path))

            # 验证检测结果
            is_pods_third_party = analyzer._is_third_party_file(pods_file)
            is_vendor_third_party = analyzer._is_third_party_file(vendor_file)
            is_custom_third_party = analyzer._is_third_party_file(custom_file)

            self.assertTrue(is_pods_third_party, "Pods文件应被识别为第三方")
            self.assertTrue(is_vendor_third_party, "含版权声明的文件应被识别为第三方")
            self.assertFalse(is_custom_third_party, "自定义代码不应被识别为第三方")

            print("✅ 第三方库识别机制工作正常:")
            print(f"   路径检测: {'✓' if is_pods_third_party else '✗'} Pods/AFNetworking")
            print(f"   内容检测: {'✓' if is_vendor_third_party else '✗'} Vendor/ThirdPartyLib (MIT License)")
            print(f"   自定义代码: {'✓' if not is_custom_third_party else '✗'} MyApp/MyViewController")

        finally:
            shutil.rmtree(temp_dir)

    def test_comprehensive_flow(self):
        """综合测试：完整混淆流程"""
        print("\n=== 综合测试: 完整混淆流程 ===")

        # 创建测试Swift文件
        swift_code = """
import UIKit

class DataManager<T: Codable & Equatable> where T: Collection {
    var items: [T] = []

    func add(_ item: T) {
        items.append(item)
    }

    func find(_ predicate: (T) -> Bool) -> T? {
        return items.first(where: predicate)
    }
}

struct User: Equatable {
    var name: String
    var age: Int
}
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.swift', delete=False) as f:
            f.write(swift_code)
            temp_path = f.name

        try:
            # 1. 解析代码（测试P1-1）
            whitelist = WhitelistManager()
            parser = CodeParser(whitelist)
            parsed = parser.parse_file(temp_path)

            classes = [s for s in parsed.symbols if s.type.value in ['class', 'struct']]
            self.assertGreaterEqual(len(classes), 2)
            print(f"1. 解析完成: 识别 {len(classes)} 个类/结构体")

            # 2. 生成混淆映射（测试P1-2, P1-4）
            generator = NameGenerator(
                strategy=NamingStrategy.RANDOM,
                min_length=8,
                max_length=12,
                seed="comprehensive_test"
            )

            for symbol in parsed.symbols:
                generator.generate(symbol.name, symbol.type.value)

            mappings = generator.get_all_mappings()
            obfuscated_names = [m.obfuscated for m in mappings]
            self.assertEqual(len(obfuscated_names), len(set(obfuscated_names)))
            print(f"2. 映射生成: {len(mappings)} 个唯一映射，无冲突")

            # 3. 执行转换
            transformer = CodeTransformer(generator, whitelist)
            result = transformer.transform_file(temp_path, parsed)

            self.assertIsNotNone(result)
            self.assertEqual(len(result.errors), 0, f"转换错误: {result.errors}")
            print(f"3. 代码转换: {result.replacements} 处替换，无错误")

            # 4. 验证映射已生成
            final_mappings = generator.get_all_mappings()
            self.assertGreater(len(final_mappings), 0, "应该生成符号映射")

            # 验证关键符号都有映射
            mapped_names = [m.original for m in final_mappings]
            self.assertIn('DataManager', mapped_names, "DataManager应被映射")
            self.assertIn('User', mapped_names, "User应被映射")
            print("4. 验证成功: 所有符号已正确映射")

            print("\n✅ 综合测试通过：所有P1修复正常工作！")

        finally:
            os.unlink(temp_path)


def run_tests():
    """运行所有P1修复测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加测试
    suite.addTests(loader.loadTestsFromTestCase(TestP1Fixes))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 输出总结
    print("\n" + "="*70)
    print("P1修复简化集成测试总结")
    print("="*70)
    print(f"总测试数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")

    if result.wasSuccessful():
        print("\n🎉 所有P1修复验证通过！")
    else:
        print("\n⚠️  部分测试失败，请检查详细输出")

    print("="*70)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
