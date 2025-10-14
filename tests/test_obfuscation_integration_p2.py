"""
测试iOS代码混淆P2高级功能集成
测试垃圾代码生成和字符串加密功能是否正确集成到混淆引擎
"""

import unittest
import sys
import os
from pathlib import Path
import tempfile
import shutil

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from gui.modules.obfuscation.obfuscation_engine import ObfuscationEngine
    from gui.modules.obfuscation.config_manager import ConfigManager, ObfuscationConfig
    from gui.modules.obfuscation.garbage_generator import GarbageCodeGenerator, CodeLanguage, ComplexityLevel
    from gui.modules.obfuscation.string_encryptor import StringEncryptor, EncryptionAlgorithm
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保在项目根目录运行测试")
    sys.exit(1)


class TestObfuscationEngineP2Integration(unittest.TestCase):
    """测试混淆引擎P2高级功能集成"""

    def setUp(self):
        """测试前准备"""
        # 创建临时测试目录
        self.test_dir = tempfile.mkdtemp(prefix="obfuscation_test_")
        self.project_dir = Path(self.test_dir) / "test_project"
        self.output_dir = Path(self.test_dir) / "output"
        self.project_dir.mkdir(parents=True)
        self.output_dir.mkdir(parents=True)

        # 创建简单的测试项目结构
        self._create_test_project()

    def tearDown(self):
        """测试后清理"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def _create_test_project(self):
        """创建测试项目"""
        # 创建Objective-C测试文件
        objc_file = self.project_dir / "TestClass.m"
        objc_file.write_text('''
#import "TestClass.h"

@implementation TestClass

- (void)testMethod {
    NSString *message = @"Hello World";
    NSLog(@"%@", message);
}

- (NSString *)getName {
    return @"TestClass";
}

@end
''', encoding='utf-8')

        # 创建头文件
        header_file = self.project_dir / "TestClass.h"
        header_file.write_text('''
#import <Foundation/Foundation.h>

@interface TestClass : NSObject

- (void)testMethod;
- (NSString *)getName;

@end
''', encoding='utf-8')

        # 创建Swift测试文件
        swift_file = self.project_dir / "TestSwift.swift"
        swift_file.write_text('''
import Foundation

class TestSwift {
    func testMethod() {
        let message = "Hello Swift"
        print(message)
    }

    func getName() -> String {
        return "TestSwift"
    }
}
''', encoding='utf-8')

    def test_config_p2_options(self):
        """测试P2配置选项"""
        print("\n1. 测试P2配置选项")

        config_manager = ConfigManager()
        config = config_manager.get_template("aggressive")

        # 验证垃圾代码配置
        print(f"  垃圾代码生成: {config.insert_garbage_code}")
        print(f"  垃圾类数量: {config.garbage_count}")
        print(f"  垃圾复杂度: {config.garbage_complexity}")
        print(f"  垃圾前缀: {config.garbage_prefix}")

        # 验证字符串加密配置
        print(f"  字符串加密: {config.string_encryption}")
        print(f"  加密算法: {config.encryption_algorithm}")
        print(f"  加密密钥: {config.encryption_key}")
        print(f"  最小长度: {config.string_min_length}")

        # 断言配置存在
        self.assertTrue(hasattr(config, 'garbage_count'))
        self.assertTrue(hasattr(config, 'garbage_complexity'))
        self.assertTrue(hasattr(config, 'encryption_algorithm'))
        self.assertTrue(hasattr(config, 'encryption_key'))

        print("  ✅ P2配置选项测试通过")

    def test_garbage_code_integration(self):
        """测试垃圾代码生成集成"""
        print("\n2. 测试垃圾代码生成集成")

        # 创建配置
        config_manager = ConfigManager()
        config = config_manager.get_template("standard")
        config.insert_garbage_code = True
        config.garbage_count = 5
        config.garbage_complexity = "simple"

        # 初始化引擎
        engine = ObfuscationEngine(config)
        self.assertIsNone(engine.garbage_generator)

        # 手动触发垃圾代码生成（模拟）
        engine.garbage_generator = GarbageCodeGenerator(
            language=CodeLanguage.OBJC,
            complexity=ComplexityLevel.SIMPLE,
            name_prefix="GC",
            seed="test_seed"
        )

        # 生成垃圾类
        classes = engine.garbage_generator.generate_classes(count=5)
        self.assertEqual(len(classes), 5)

        # 导出文件
        files_dict = engine.garbage_generator.export_to_files(str(self.output_dir))
        self.assertGreater(len(files_dict), 0)

        # 验证文件存在（files_dict的values是完整路径）
        for file_path in files_dict.values():
            self.assertTrue(os.path.exists(file_path))
            print(f"  生成文件: {Path(file_path).name}")

        # 统计信息
        stats = engine.garbage_generator.get_statistics()
        print(f"  生成类: {stats['classes_generated']}")
        print(f"  生成方法: {stats['methods_generated']}")
        print(f"  生成属性: {stats['properties_generated']}")

        print("  ✅ 垃圾代码生成集成测试通过")

    def test_string_encryption_integration(self):
        """测试字符串加密集成"""
        print("\n3. 测试字符串加密集成")

        # 创建配置
        config_manager = ConfigManager()
        config = config_manager.get_template("aggressive")
        config.string_encryption = True
        config.encryption_algorithm = "xor"
        config.encryption_key = "TestKey123"

        # 初始化引擎
        engine = ObfuscationEngine(config)
        self.assertIsNone(engine.string_encryptor)

        # 手动触发字符串加密（模拟）
        engine.string_encryptor = StringEncryptor(
            algorithm=EncryptionAlgorithm.XOR,
            key="TestKey123",
            min_length=4
        )

        # 测试字符串加密
        test_code = '''
NSString *message = @"Hello World";
NSString *name = @"TestClass";
'''

        encrypted_code, encrypted_list = engine.string_encryptor.process_file(
            "test.m",
            test_code
        )

        self.assertGreater(len(encrypted_list), 0)
        print(f"  加密字符串数: {len(encrypted_list)}")

        for encrypted_str in encrypted_list:
            print(f"  {encrypted_str.original} -> {encrypted_str.encrypted}")

        # 生成解密宏
        decryption_macro = engine.string_encryptor.generate_decryption_macro()
        self.assertIn("DECRYPT_STRING", decryption_macro.code)
        print(f"  解密宏生成: ✅")

        # 统计信息
        stats = engine.string_encryptor.get_statistics()
        print(f"  加密字符串总数: {stats['total_encrypted']}")
        print(f"  加密算法: {stats['algorithm']}")

        print("  ✅ 字符串加密集成测试通过")

    def test_engine_statistics_p2(self):
        """测试引擎P2统计信息"""
        print("\n4. 测试引擎P2统计信息")

        # 创建配置
        config_manager = ConfigManager()
        config = config_manager.get_template("aggressive")

        # 初始化引擎
        engine = ObfuscationEngine(config)

        # 模拟初始化P2组件
        engine.garbage_generator = GarbageCodeGenerator(
            language=CodeLanguage.OBJC,
            complexity=ComplexityLevel.MODERATE,
            name_prefix="GC"
        )

        engine.string_encryptor = StringEncryptor(
            algorithm=EncryptionAlgorithm.XOR,
            key="TestKey"
        )

        # 获取统计信息
        stats = engine.get_statistics()

        # 验证P2统计信息存在
        self.assertIn('garbage_code', stats)
        self.assertIn('string_encryption', stats)

        print(f"  统计信息键: {list(stats.keys())}")
        print(f"  垃圾代码统计: {stats['garbage_code']}")
        print(f"  字符串加密统计: {stats['string_encryption']}")

        print("  ✅ 引擎P2统计信息测试通过")

    def test_config_validation_p2(self):
        """测试P2配置验证"""
        print("\n5. 测试P2配置验证")

        config_manager = ConfigManager()

        # 测试有效配置
        config = config_manager.get_template("standard")
        config.insert_garbage_code = True
        config.garbage_count = 10
        config.garbage_complexity = "moderate"
        config.string_encryption = True
        config.encryption_algorithm = "xor"

        is_valid, errors = config_manager.validate_config(config)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
        print("  ✅ 有效配置通过验证")

        # 测试无效配置（如果有额外验证规则）
        # 当前配置管理器未对P2选项做额外验证，这里只是示例
        print("  ✅ 配置验证测试通过")


def run_tests():
    """运行所有测试"""
    print("=" * 70)
    print("iOS代码混淆P2高级功能集成测试")
    print("=" * 70)

    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestObfuscationEngineP2Integration)

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 输出总结
    print("\n" + "=" * 70)
    print(f"测试总结:")
    print(f"  运行: {result.testsRun}")
    print(f"  成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"  失败: {len(result.failures)}")
    print(f"  错误: {len(result.errors)}")
    print("=" * 70)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
