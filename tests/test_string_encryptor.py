#!/usr/bin/env python3
"""
字符串加密器测试

测试字符串加密器的完整功能
"""

import sys
import os
from pathlib import Path
import unittest

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from gui.modules.obfuscation.string_encryptor import (
    StringEncryptor,
    EncryptionAlgorithm,
    CodeLanguage,
    EncryptedString,
    DecryptionMacro
)


class TestStringEncryptor(unittest.TestCase):
    """字符串加密器测试"""

    def test_base64_encryption(self):
        """测试Base64加密"""
        encryptor = StringEncryptor(
            algorithm=EncryptionAlgorithm.BASE64,
            language=CodeLanguage.OBJC
        )

        original = "Hello World"
        encrypted = encryptor.encrypt_string(original)

        # 验证是Base64格式
        import base64
        try:
            decoded = base64.b64decode(encrypted).decode('utf-8')
            self.assertEqual(decoded, original)
        except Exception:
            self.fail("Base64解密失败")

    def test_xor_encryption(self):
        """测试XOR加密"""
        encryptor = StringEncryptor(
            algorithm=EncryptionAlgorithm.XOR,
            language=CodeLanguage.OBJC,
            key="TestKey"
        )

        original = "Hello World"
        encrypted = encryptor.encrypt_string(original)

        # 验证加密后是十六进制字符串
        self.assertTrue(all(c in '0123456789abcdef' for c in encrypted))
        # 验证长度（每个字符2个十六进制位）
        self.assertEqual(len(encrypted), len(original.encode('utf-8')) * 2)

    def test_shift_encryption(self):
        """测试位移加密"""
        encryptor = StringEncryptor(
            algorithm=EncryptionAlgorithm.SIMPLE_SHIFT,
            language=CodeLanguage.OBJC,
            key="AB"
        )

        original = "Test"
        encrypted = encryptor.encrypt_string(original)

        # 验证是十六进制格式（每个字符4位）
        self.assertTrue(all(c in '0123456789abcdef' for c in encrypted))
        self.assertEqual(len(encrypted), len(original) * 4)

    def test_rot13_encryption(self):
        """测试ROT13加密"""
        encryptor = StringEncryptor(
            algorithm=EncryptionAlgorithm.ROT13,
            language=CodeLanguage.OBJC
        )

        original = "Hello"
        encrypted = encryptor.encrypt_string(original)

        # ROT13结果应该是Base64编码的
        import base64
        try:
            base64.b64decode(encrypted)
        except Exception:
            self.fail("ROT13加密结果不是Base64格式")

    def test_objc_string_detection(self):
        """测试Objective-C字符串检测"""
        code = '''
@implementation MyClass
- (void)test {
    NSString *str1 = @"Hello";
    NSString *str2 = @"World";
}
@end
'''

        encryptor = StringEncryptor(
            algorithm=EncryptionAlgorithm.BASE64,
            language=CodeLanguage.OBJC
        )

        processed, encrypted_list = encryptor.process_file("test.m", code)

        # 应该检测到2个字符串
        self.assertEqual(len(encrypted_list), 2)

        # 验证字符串内容
        originals = {e.original for e in encrypted_list}
        self.assertIn("Hello", originals)
        self.assertIn("World", originals)

    def test_swift_string_detection(self):
        """测试Swift字符串检测"""
        code = '''
class MyClass {
    func test() {
        let str1 = "Hello"
        let str2 = "Swift"
    }
}
'''

        encryptor = StringEncryptor(
            algorithm=EncryptionAlgorithm.BASE64,
            language=CodeLanguage.SWIFT
        )

        processed, encrypted_list = encryptor.process_file("test.swift", code)

        # 应该检测到2个字符串
        self.assertEqual(len(encrypted_list), 2)

        # 验证字符串内容
        originals = {e.original for e in encrypted_list}
        self.assertIn("Hello", originals)
        self.assertIn("Swift", originals)

    def test_whitelist_filtering(self):
        """测试白名单过滤"""
        code = '@"System" @"Custom" @"API"'

        encryptor = StringEncryptor(
            algorithm=EncryptionAlgorithm.XOR,
            language=CodeLanguage.OBJC,
            whitelist={"System", "API"}
        )

        processed, encrypted_list = encryptor.process_file("test.m", code)

        # 只有Custom应该被加密
        self.assertEqual(len(encrypted_list), 1)
        self.assertEqual(encrypted_list[0].original, "Custom")

    def test_min_length_filtering(self):
        """测试最小长度过滤"""
        code = '@"ab" @"abc" @"abcd"'

        encryptor = StringEncryptor(
            algorithm=EncryptionAlgorithm.XOR,
            language=CodeLanguage.OBJC,
            min_length=3,
            skip_short_strings=True
        )

        processed, encrypted_list = encryptor.process_file("test.m", code)

        # 只有长度>=3的应该被加密
        self.assertEqual(len(encrypted_list), 2)
        originals = {e.original for e in encrypted_list}
        self.assertIn("abc", originals)
        self.assertIn("abcd", originals)
        self.assertNotIn("ab", originals)

    def test_skip_pattern_filtering(self):
        """测试跳过模式过滤"""
        code = '''
@"UIViewController"
@"MyCustomClass"
@"http://example.com"
@"NormalString"
@".png"
@"/path/to/file"
'''

        encryptor = StringEncryptor(
            algorithm=EncryptionAlgorithm.XOR,
            language=CodeLanguage.OBJC
        )

        processed, encrypted_list = encryptor.process_file("test.m", code)

        # 验证跳过了系统类名、URL、文件扩展名、路径
        originals = {e.original for e in encrypted_list}

        # 这些应该被跳过
        self.assertNotIn("UIViewController", originals)  # 大写开头（可能是类名）
        self.assertNotIn("http://example.com", originals)  # URL scheme
        self.assertNotIn(".png", originals)  # 文件扩展名
        self.assertNotIn("/path/to/file", originals)  # 路径

        # 这些应该被加密
        self.assertIn("MyCustomClass", originals)
        self.assertIn("NormalString", originals)

    def test_string_replacement_objc(self):
        """测试Objective-C字符串替换"""
        code = 'NSString *str = @"Original";'

        encryptor = StringEncryptor(
            algorithm=EncryptionAlgorithm.BASE64,
            language=CodeLanguage.OBJC
        )

        processed, _ = encryptor.process_file("test.m", code)

        # 验证替换为解密宏调用
        self.assertIn("DECRYPT_STRING_B64", processed)
        self.assertNotIn('@"Original"', processed)

    def test_string_replacement_swift(self):
        """测试Swift字符串替换"""
        code = 'let str = "Original"'

        encryptor = StringEncryptor(
            algorithm=EncryptionAlgorithm.XOR,
            language=CodeLanguage.SWIFT
        )

        processed, _ = encryptor.process_file("test.swift", code)

        # 验证替换为解密函数调用
        self.assertIn("decryptStringXOR", processed)
        self.assertNotIn('"Original"', processed)

    def test_decryption_macro_generation_objc(self):
        """测试Objective-C解密宏生成"""
        encryptor = StringEncryptor(
            algorithm=EncryptionAlgorithm.XOR,
            language=CodeLanguage.OBJC,
            key="TestKey"
        )

        macro = encryptor.generate_decryption_macro()

        # 验证宏名称
        self.assertEqual(macro.name, "DECRYPT_STRING_XOR")
        self.assertEqual(macro.language, CodeLanguage.OBJC)

        # 验证包含必要的代码元素
        self.assertIn("#define", macro.code)
        self.assertIn("XOR_KEY", macro.code)
        self.assertIn("decryptStringXOR", macro.code)

    def test_decryption_macro_generation_swift(self):
        """测试Swift解密函数生成"""
        encryptor = StringEncryptor(
            algorithm=EncryptionAlgorithm.BASE64,
            language=CodeLanguage.SWIFT
        )

        macro = encryptor.generate_decryption_macro()

        # 验证函数名称
        self.assertEqual(macro.name, "decryptStringB64")
        self.assertEqual(macro.language, CodeLanguage.SWIFT)

        # 验证包含必要的代码元素
        self.assertIn("func", macro.code)
        self.assertIn("decryptStringB64", macro.code)
        self.assertIn("Data(base64Encoded:", macro.code)

    def test_deterministic_encryption_with_key(self):
        """测试使用相同密钥的确定性加密"""
        enc1 = StringEncryptor(
            algorithm=EncryptionAlgorithm.XOR,
            language=CodeLanguage.OBJC,
            key="FixedKey"
        )

        enc2 = StringEncryptor(
            algorithm=EncryptionAlgorithm.XOR,
            language=CodeLanguage.OBJC,
            key="FixedKey"
        )

        text = "Test String"
        encrypted1 = enc1.encrypt_string(text)
        encrypted2 = enc2.encrypt_string(text)

        # 相同密钥应该产生相同的加密结果
        self.assertEqual(encrypted1, encrypted2)

    def test_unicode_string_encryption(self):
        """测试Unicode字符串加密（中文、emoji）"""
        encryptor = StringEncryptor(
            algorithm=EncryptionAlgorithm.XOR,
            language=CodeLanguage.OBJC,
            key="TestKey"
        )

        # 测试中文
        chinese = "你好世界"
        encrypted_chinese = encryptor.encrypt_string(chinese)
        self.assertIsNotNone(encrypted_chinese)
        self.assertTrue(len(encrypted_chinese) > 0)

        # 测试emoji
        emoji = "Hello 😀 World"
        encrypted_emoji = encryptor.encrypt_string(emoji)
        self.assertIsNotNone(encrypted_emoji)
        self.assertTrue(len(encrypted_emoji) > 0)

    def test_statistics(self):
        """测试统计信息"""
        code = '@"String1" @"String2" @"String3"'

        encryptor = StringEncryptor(
            algorithm=EncryptionAlgorithm.XOR,
            language=CodeLanguage.OBJC,
            key="TestKey"
        )

        encryptor.process_file("test1.m", code)
        encryptor.process_file("test2.m", code)

        stats = encryptor.get_statistics()

        # 验证统计信息
        self.assertEqual(stats['total_encrypted'], 6)  # 2个文件，每个3个字符串
        self.assertEqual(stats['algorithm'], 'xor')
        self.assertEqual(stats['language'], 'objc')
        self.assertEqual(stats['key'], 'TestKey')
        self.assertEqual(stats['files'], 2)

    def test_escaped_strings(self):
        """测试转义字符串"""
        code = r'NSString *str = @"Hello \"World\"";'

        encryptor = StringEncryptor(
            algorithm=EncryptionAlgorithm.BASE64,
            language=CodeLanguage.OBJC
        )

        processed, encrypted_list = encryptor.process_file("test.m", code)

        # 应该正确处理转义字符
        self.assertEqual(len(encrypted_list), 1)
        self.assertIn('Hello \\"World\\"', encrypted_list[0].original)


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestStringEncryptor)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result


if __name__ == '__main__':
    print("=" * 70)
    print("字符串加密器测试")
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
        print("\n🎉 所有测试通过！字符串加密器功能正常")
        sys.exit(0)
    else:
        print(f"\n⚠️  {len(result.failures) + len(result.errors)} 个测试未通过")
        sys.exit(1)
