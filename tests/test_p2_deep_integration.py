"""
测试P2深度集成功能
测试字符串加密和垃圾代码生成完全集成到混淆引擎主流程
"""

import unittest
import sys
import os
from pathlib import Path
import tempfile
import shutil
import json

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from gui.modules.obfuscation.obfuscation_engine import ObfuscationEngine
    from gui.modules.obfuscation.config_manager import ConfigManager, ObfuscationConfig
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保在项目根目录运行测试")
    sys.exit(1)


class TestP2DeepIntegration(unittest.TestCase):
    """测试P2深度集成功能"""

    def setUp(self):
        """测试前准备"""
        # 创建临时测试目录
        self.test_dir = tempfile.mkdtemp(prefix="p2_deep_integration_test_")
        self.project_dir = Path(self.test_dir) / "test_project"
        self.output_dir = Path(self.test_dir) / "output"
        self.project_dir.mkdir(parents=True)
        self.output_dir.mkdir(parents=True)

        # 创建简单的测试项目
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
    NSString *name = @"TestClass";
    NSLog(@"%@ from %@", message, name);
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

        # 创建Swift测试文件（使用较长的字符串确保被加密）
        swift_file = self.project_dir / "TestSwift.swift"
        swift_file.write_text('''
import Foundation

class TestSwift {
    func testMethod() {
        let message = "Hello Swift World"
        let name = "TestSwiftClass"
        let description = "This is a test string"
        print("\\(message) from \\(name) - \\(description)")
    }

    func getName() -> String {
        return "TestSwiftClass"
    }
}
''', encoding='utf-8')

    def test_string_encryption_deep_integration(self):
        """测试字符串加密深度集成"""
        print("\n1. 测试字符串加密深度集成")

        # 创建启用字符串加密的配置（禁用垃圾代码避免干扰）
        config_manager = ConfigManager()
        config = config_manager.get_template("standard")
        config.string_encryption = True
        config.encryption_algorithm = "xor"
        config.encryption_key = "TestKey123"
        config.string_min_length = 4
        config.insert_garbage_code = False  # 禁用垃圾代码

        # 初始化引擎并执行混淆
        engine = ObfuscationEngine(config)
        result = engine.obfuscate(
            str(self.project_dir),
            str(self.output_dir)
        )

        # 验证混淆成功
        self.assertTrue(result.success, "混淆应该成功")
        print(f"  ✅ 混淆执行成功")

        # 验证ObjC解密头文件生成
        objc_header = self.output_dir / "StringDecryption.h"
        self.assertTrue(objc_header.exists(), "应该生成ObjC解密头文件")
        print(f"  ✅ ObjC解密头文件已生成: {objc_header.name}")

        # 验证头文件内容
        with open(objc_header, 'r', encoding='utf-8') as f:
            header_content = f.read()
            self.assertIn("StringDecryption_h", header_content)
            self.assertIn("DECRYPT_STRING", header_content)
        print(f"  ✅ 头文件内容验证通过")

        # 验证Swift解密文件生成
        swift_file = self.output_dir / "StringDecryption.swift"
        self.assertTrue(swift_file.exists(), "应该生成Swift解密文件")
        print(f"  ✅ Swift解密文件已生成: {swift_file.name}")

        # 验证Swift文件内容
        with open(swift_file, 'r', encoding='utf-8') as f:
            swift_content = f.read()
            self.assertIn("func decryptString", swift_content)
            self.assertIn("import Foundation", swift_content)
        print(f"  ✅ Swift文件内容验证通过")

        # 验证ObjC文件添加了导入
        objc_output = self.output_dir / "TestClass.m"
        if objc_output.exists():
            with open(objc_output, 'r', encoding='utf-8') as f:
                objc_content = f.read()
                self.assertIn('#import "StringDecryption.h"', objc_content)
            print(f"  ✅ ObjC文件已添加导入")

        # 验证映射文件包含P2统计信息
        mapping_file = self.output_dir / "obfuscation_mapping.json"
        self.assertTrue(mapping_file.exists(), "应该生成映射文件")

        with open(mapping_file, 'r', encoding='utf-8') as f:
            mapping_data = json.load(f)
            self.assertIn('metadata', mapping_data)
            self.assertIn('string_encryption', mapping_data['metadata'])

            encryption_info = mapping_data['metadata']['string_encryption']
            self.assertTrue(encryption_info['enabled'])
            self.assertEqual(encryption_info['algorithm'], 'xor')
            self.assertGreater(encryption_info['total_encrypted'], 0)
            self.assertIsNotNone(encryption_info['decryption_header_objc'])
            self.assertIsNotNone(encryption_info['decryption_file_swift'])

        print(f"  ✅ 映射文件包含字符串加密统计信息")
        print(f"  加密字符串数: {encryption_info['total_encrypted']}")
        print(f"  ObjC文件数: {encryption_info['objc_files']}")
        print(f"  Swift文件数: {encryption_info['swift_files']}")

    def test_garbage_code_deep_integration(self):
        """测试垃圾代码深度集成"""
        print("\n2. 测试垃圾代码深度集成")

        # 创建启用垃圾代码的配置
        config_manager = ConfigManager()
        config = config_manager.get_template("standard")
        config.insert_garbage_code = True
        config.garbage_count = 10
        config.garbage_complexity = "moderate"
        config.garbage_prefix = "GC"

        # 初始化引擎并执行混淆
        engine = ObfuscationEngine(config)
        result = engine.obfuscate(
            str(self.project_dir),
            str(self.output_dir)
        )

        # 验证混淆成功
        self.assertTrue(result.success, "混淆应该成功")
        print(f"  ✅ 混淆执行成功")

        # 验证垃圾代码文件生成
        garbage_objc_files = list(self.output_dir.glob("GCClass*.h")) + list(self.output_dir.glob("GCClass*.m"))
        garbage_swift_files = list(self.output_dir.glob("GCClass*.swift"))

        self.assertGreater(len(garbage_objc_files) + len(garbage_swift_files), 0, "应该生成垃圾代码文件")
        print(f"  ✅ 垃圾代码文件已生成:")
        print(f"    - ObjC文件: {len(garbage_objc_files)} 个")
        print(f"    - Swift文件: {len(garbage_swift_files)} 个")

        # 验证垃圾文件内容
        if garbage_objc_files:
            sample_file = [f for f in garbage_objc_files if f.suffix == '.m'][0]
            with open(sample_file, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertIn('@implementation', content)
                print(f"  ✅ ObjC垃圾文件内容验证通过: {sample_file.name}")

        if garbage_swift_files:
            sample_file = garbage_swift_files[0]
            with open(sample_file, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertIn('class', content)
                print(f"  ✅ Swift垃圾文件内容验证通过: {sample_file.name}")

        # 验证映射文件包含P2统计信息
        mapping_file = self.output_dir / "obfuscation_mapping.json"
        self.assertTrue(mapping_file.exists(), "应该生成映射文件")

        with open(mapping_file, 'r', encoding='utf-8') as f:
            mapping_data = json.load(f)
            self.assertIn('metadata', mapping_data)
            self.assertIn('garbage_code', mapping_data['metadata'])

            garbage_info = mapping_data['metadata']['garbage_code']
            self.assertTrue(garbage_info['enabled'])
            self.assertEqual(garbage_info['complexity'], 'moderate')
            self.assertGreater(garbage_info['classes_generated'], 0)
            self.assertGreater(len(garbage_info['file_list']['objc']) + len(garbage_info['file_list']['swift']), 0)

        print(f"  ✅ 映射文件包含垃圾代码统计信息")
        print(f"  生成类数: {garbage_info['classes_generated']}")
        print(f"  生成方法数: {garbage_info['methods_generated']}")
        print(f"  生成属性数: {garbage_info['properties_generated']}")

    def test_combined_p2_deep_integration(self):
        """测试字符串加密和垃圾代码同时启用的深度集成"""
        print("\n3. 测试字符串加密和垃圾代码组合深度集成")

        # 创建同时启用两个P2功能的配置
        config_manager = ConfigManager()
        config = config_manager.get_template("aggressive")  # aggressive模板默认启用两个功能

        # 初始化引擎并执行混淆
        engine = ObfuscationEngine(config)
        result = engine.obfuscate(
            str(self.project_dir),
            str(self.output_dir)
        )

        # 验证混淆成功
        self.assertTrue(result.success, "混淆应该成功")
        print(f"  ✅ 混淆执行成功")

        # 验证所有P2文件都生成了
        objc_header = self.output_dir / "StringDecryption.h"
        swift_file = self.output_dir / "StringDecryption.swift"
        garbage_files = list(self.output_dir.glob("GCClass*.*"))

        self.assertTrue(objc_header.exists(), "应该生成ObjC解密头文件")
        self.assertTrue(swift_file.exists(), "应该生成Swift解密文件")
        self.assertGreater(len(garbage_files), 0, "应该生成垃圾代码文件")

        print(f"  ✅ 所有P2文件已生成:")
        print(f"    - 解密头文件: {objc_header.name}")
        print(f"    - 解密Swift文件: {swift_file.name}")
        print(f"    - 垃圾文件: {len(garbage_files)} 个")

        # 验证映射文件包含完整的P2统计信息
        mapping_file = self.output_dir / "obfuscation_mapping.json"
        with open(mapping_file, 'r', encoding='utf-8') as f:
            mapping_data = json.load(f)
            self.assertIn('string_encryption', mapping_data['metadata'])
            self.assertIn('garbage_code', mapping_data['metadata'])

        print(f"  ✅ 映射文件包含完整的P2统计信息")

        # 输出详细统计
        encryption_info = mapping_data['metadata']['string_encryption']
        garbage_info = mapping_data['metadata']['garbage_code']

        print(f"\n  字符串加密统计:")
        print(f"    - 算法: {encryption_info['algorithm']}")
        print(f"    - 加密字符串数: {encryption_info['total_encrypted']}")

        print(f"\n  垃圾代码统计:")
        print(f"    - 复杂度: {garbage_info['complexity']}")
        print(f"    - 生成类数: {garbage_info['classes_generated']}")


def run_tests():
    """运行所有测试"""
    print("=" * 70)
    print("P2深度集成功能测试")
    print("=" * 70)

    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestP2DeepIntegration)

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
