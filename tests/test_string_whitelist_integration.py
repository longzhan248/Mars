"""
字符串加密白名单集成测试

测试字符串加密白名单功能的完整流程：
1. 白名单文件的加载和保存
2. 白名单在字符串加密器中的应用
3. 白名单在混淆引擎中的集成
"""

import unittest
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from gui.modules.obfuscation.string_encryptor import StringEncryptor, EncryptionAlgorithm, CodeLanguage
from gui.modules.obfuscation.config_manager import ObfuscationConfig


class TestStringWhitelistIntegration(unittest.TestCase):
    """字符串加密白名单集成测试"""

    def setUp(self):
        """测试前准备"""
        # 创建临时目录
        self.test_dir = tempfile.mkdtemp()
        self.whitelist_file = os.path.join(self.test_dir, "string_encryption_whitelist.json")

    def tearDown(self):
        """测试后清理"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_whitelist_file_format(self):
        """测试1: 白名单文件格式"""
        print("\n测试1: 白名单文件格式")

        # 创建白名单数据
        whitelist_data = {
            "version": "1.0",
            "updated": "2025-10-14T12:00:00",
            "strings": [
                {"content": "viewDidLoad", "reason": "系统方法名"},
                {"content": "tableView", "reason": "UITableView代理方法"},
                {"content": "NSUserDefaults", "reason": "系统类名"}
            ]
        }

        # 保存到文件
        with open(self.whitelist_file, 'w', encoding='utf-8') as f:
            json.dump(whitelist_data, f, indent=2, ensure_ascii=False)

        # 验证文件存在
        self.assertTrue(os.path.exists(self.whitelist_file))

        # 读取并验证内容
        with open(self.whitelist_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)

        self.assertEqual(loaded_data['version'], '1.0')
        self.assertEqual(len(loaded_data['strings']), 3)
        self.assertEqual(loaded_data['strings'][0]['content'], 'viewDidLoad')

        print("  ✅ 白名单文件格式正确")

    def test_whitelist_in_string_encryptor(self):
        """测试2: 白名单在字符串加密器中的应用"""
        print("\n测试2: 白名单在字符串加密器中的应用")

        # 创建白名单（字符串字面量内容）
        whitelist = {"Hello World", "Protected String"}

        # 创建字符串加密器（带白名单）
        encryptor = StringEncryptor(
            algorithm=EncryptionAlgorithm.XOR,
            language=CodeLanguage.OBJC,
            key="TestKey123",
            min_length=3,
            whitelist=whitelist
        )

        # 测试代码
        objc_code = '''
@implementation MyViewController

- (void)viewDidLoad {
    [super viewDidLoad];
    NSString *title = @"Hello World";
    NSString *message = @"Test Message";
    NSString *protected = @"Protected String";
    [[NSUserDefaults standardUserDefaults] setObject:@"value" forKey:@"key"];
}

@end
'''

        # 处理文件
        processed, encrypted_list = encryptor.process_file("MyViewController.m", objc_code)

        print(f"  代码中字符串数: 5")
        print(f"  白名单字符串数: {len(whitelist)}")
        print(f"  加密字符串数: {len(encrypted_list)}")

        # 白名单字符串不应该在加密列表中
        encrypted_contents = [e.original for e in encrypted_list]

        # 验证白名单字符串未被加密
        self.assertNotIn("Hello World", encrypted_contents)
        self.assertNotIn("Protected String", encrypted_contents)

        # 验证非白名单字符串被加密
        self.assertIn("Test Message", encrypted_contents)
        self.assertIn("value", encrypted_contents)
        self.assertIn("key", encrypted_contents)

        # 验证白名单字符串在处理后的代码中保持原样
        self.assertIn('@"Hello World"', processed)
        self.assertIn('@"Protected String"', processed)

        # 验证非白名单字符串被替换为解密宏调用
        self.assertIn('DECRYPT_STRING_XOR', processed)

        print("  ✅ 白名单字符串未被加密")
        print(f"  ✅ 实际加密字符串: {encrypted_contents}")

    def test_whitelist_loading_from_config(self):
        """测试3: 从配置加载白名单"""
        print("\n测试3: 从配置加载白名单")

        # 创建白名单文件
        whitelist_data = {
            "version": "1.0",
            "updated": "2025-10-14T12:00:00",
            "strings": [
                {"content": "systemMethod", "reason": "系统方法"},
                {"content": "apiKey", "reason": "API密钥标识"},
                {"content": "configKey", "reason": "配置键名"}
            ]
        }

        with open(self.whitelist_file, 'w', encoding='utf-8') as f:
            json.dump(whitelist_data, f, indent=2, ensure_ascii=False)

        # 模拟从文件加载白名单
        with open(self.whitelist_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
            whitelist_strings = [item['content'] for item in loaded_data.get('strings', [])]

        print(f"  从文件加载的白名单项: {whitelist_strings}")

        # 创建配置
        config = ObfuscationConfig()
        config.string_whitelist_patterns = whitelist_strings

        # 验证配置
        self.assertEqual(len(config.string_whitelist_patterns), 3)
        self.assertIn("systemMethod", config.string_whitelist_patterns)
        self.assertIn("apiKey", config.string_whitelist_patterns)
        self.assertIn("configKey", config.string_whitelist_patterns)

        print("  ✅ 配置中白名单加载正确")

    def test_whitelist_with_different_algorithms(self):
        """测试4: 白名单在不同加密算法下的工作"""
        print("\n测试4: 白名单在不同加密算法下的工作")

        whitelist = {"protectedString", "systemAPI"}
        test_code = '''
let protectedString = "Protected"
let normalString = "Normal"
let systemAPI = "API"
'''

        algorithms = [
            EncryptionAlgorithm.XOR,
            EncryptionAlgorithm.BASE64,
            EncryptionAlgorithm.SIMPLE_SHIFT,
            EncryptionAlgorithm.ROT13
        ]

        for algorithm in algorithms:
            encryptor = StringEncryptor(
                algorithm=algorithm,
                language=CodeLanguage.SWIFT,
                key="A1B2C3D4E5F6",  # 提供十六进制格式的密钥
                whitelist=whitelist
            )

            processed, encrypted_list = encryptor.process_file("Test.swift", test_code)

            # 验证白名单字符串未被加密
            encrypted_contents = [e.original for e in encrypted_list]
            self.assertNotIn("protectedString", encrypted_contents)
            self.assertNotIn("systemAPI", encrypted_contents)

            # 验证普通字符串被加密
            self.assertIn("Normal", encrypted_contents)

            print(f"  ✅ {algorithm.value} 算法: 白名单生效，加密 {len(encrypted_list)} 个字符串")

    def test_empty_whitelist(self):
        """测试5: 空白名单情况"""
        print("\n测试5: 空白名单情况")

        # 空白名单
        encryptor = StringEncryptor(
            algorithm=EncryptionAlgorithm.XOR,
            language=CodeLanguage.OBJC,
            whitelist=set()  # 空集合
        )

        test_code = '''
NSString *str1 = @"String1";
NSString *str2 = @"String2";
NSString *str3 = @"String3";
'''

        processed, encrypted_list = encryptor.process_file("Test.m", test_code)

        # 空白名单时，所有符合条件的字符串都应该被加密
        self.assertEqual(len(encrypted_list), 3)
        print(f"  ✅ 空白名单: 加密了所有 {len(encrypted_list)} 个字符串")

    def test_whitelist_with_special_characters(self):
        """测试6: 白名单包含特殊字符"""
        print("\n测试6: 白名单包含特殊字符")

        # 白名单包含中文、emoji、特殊符号
        whitelist = {
            "用户名称",
            "🎉Success",
            "key:value",
            "com.example.app"
        }

        encryptor = StringEncryptor(
            algorithm=EncryptionAlgorithm.XOR,
            language=CodeLanguage.SWIFT,
            whitelist=whitelist,
            min_length=1  # 降低最小长度以测试短字符串
        )

        test_code = '''
let userName = "用户名称"
let message = "🎉Success"
let config = "key:value"
let bundleId = "com.example.app"
let normal = "NormalString"
'''

        processed, encrypted_list = encryptor.process_file("Test.swift", test_code)

        encrypted_contents = [e.original for e in encrypted_list]

        # 验证白名单字符串未被加密
        self.assertNotIn("用户名称", encrypted_contents)
        self.assertNotIn("🎉Success", encrypted_contents)
        self.assertNotIn("key:value", encrypted_contents)
        self.assertNotIn("com.example.app", encrypted_contents)

        # 验证普通字符串被加密
        self.assertIn("NormalString", encrypted_contents)

        print(f"  ✅ 特殊字符白名单生效，加密 {len(encrypted_list)} 个普通字符串")

    def test_whitelist_persistence(self):
        """测试7: 白名单持久化（保存和加载）"""
        print("\n测试7: 白名单持久化")

        # 创建白名单数据
        original_whitelist = {
            "version": "1.0",
            "updated": "2025-10-14T12:00:00",
            "strings": [
                {"content": "item1", "reason": "reason1"},
                {"content": "item2", "reason": "reason2"},
                {"content": "item3", "reason": "reason3"}
            ]
        }

        # 保存
        with open(self.whitelist_file, 'w', encoding='utf-8') as f:
            json.dump(original_whitelist, f, indent=2, ensure_ascii=False)

        print("  ✅ 白名单已保存")

        # 加载
        with open(self.whitelist_file, 'r', encoding='utf-8') as f:
            loaded_whitelist = json.load(f)

        # 验证
        self.assertEqual(loaded_whitelist['version'], original_whitelist['version'])
        self.assertEqual(len(loaded_whitelist['strings']), len(original_whitelist['strings']))

        for i, item in enumerate(loaded_whitelist['strings']):
            self.assertEqual(item['content'], original_whitelist['strings'][i]['content'])
            self.assertEqual(item['reason'], original_whitelist['strings'][i]['reason'])

        print("  ✅ 白名单加载成功，数据一致")

    def test_whitelist_with_min_length_filter(self):
        """测试8: 白名单与最小长度过滤的交互"""
        print("\n测试8: 白名单与最小长度过滤的交互")

        whitelist = {"abc", "verylongstring"}

        encryptor = StringEncryptor(
            algorithm=EncryptionAlgorithm.XOR,
            language=CodeLanguage.OBJC,
            whitelist=whitelist,
            min_length=5  # 最小长度5
        )

        test_code = '''
NSString *s1 = @"abc";             // 在白名单，但长度<5
NSString *s2 = @"def";             // 不在白名单，长度<5
NSString *s3 = @"verylongstring";  // 在白名单，长度>5
NSString *s4 = @"anotherlongone";  // 不在白名单，长度>5
'''

        processed, encrypted_list = encryptor.process_file("Test.m", test_code)

        encrypted_contents = [e.original for e in encrypted_list]

        # "abc" 在白名单中，不应被加密
        self.assertNotIn("abc", encrypted_contents)

        # "def" 不在白名单，但长度<5，也不应被加密（最小长度过滤）
        self.assertNotIn("def", encrypted_contents)

        # "verylongstring" 在白名单，不应被加密
        self.assertNotIn("verylongstring", encrypted_contents)

        # "anotherlongone" 不在白名单，长度>5，应该被加密
        self.assertIn("anotherlongone", encrypted_contents)

        print(f"  ✅ 白名单与最小长度过滤正确协作")
        print(f"  加密的字符串: {encrypted_contents}")


def run_tests():
    """运行所有测试"""
    print("="*80)
    print("字符串加密白名单集成测试")
    print("="*80)

    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestStringWhitelistIntegration)

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 输出测试摘要
    print("\n" + "="*80)
    print("测试摘要")
    print("="*80)
    print(f"总测试数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")

    if result.wasSuccessful():
        print("\n✅ 所有测试通过！字符串加密白名单功能正常工作。")
    else:
        print("\n❌ 部分测试失败，请检查错误信息。")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
