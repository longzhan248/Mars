"""
iOS代码混淆模块集成测试

测试整个混淆流程，确保所有组件协同工作正常。
"""

import unittest
import tempfile
import shutil
import os
from pathlib import Path
import json

# 导入需要测试的模块
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from config_manager import ObfuscationConfig, ConfigManager
from whitelist_manager import WhitelistManager, SystemAPIWhitelist
from name_generator import NameGenerator, NamingStrategy
from project_analyzer import ProjectAnalyzer
from code_parser import CodeParser, SymbolType
from code_transformer import CodeTransformer
from resource_handler import ResourceHandler
from obfuscation_engine import ObfuscationEngine


class TestCodeParserIntegration(unittest.TestCase):
    """代码解析器集成测试"""

    def setUp(self):
        """测试前准备"""
        self.test_dir = tempfile.mkdtemp()
        self.whitelist = WhitelistManager(project_path=self.test_dir)

    def tearDown(self):
        """测试后清理"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_parse_objc_file_complete(self):
        """测试解析完整的ObjC文件"""
        # 创建头文件（包含类定义）
        test_file = os.path.join(self.test_dir, "TestClass.h")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("""
// TestClass.h
#import <Foundation/Foundation.h>

@interface TestClass : NSObject

@property (nonatomic, strong) NSString *publicProperty;

- (instancetype)initWithName:(NSString *)name;
- (void)publicMethod;
- (void)internalMethodWithParam:(NSInteger)param;

@end
""")

        # 解析文件
        parser = CodeParser(self.whitelist)
        result = parser.parse_file(test_file)

        # 验证结果
        self.assertIsNotNone(result)
        self.assertEqual(result.file_path, test_file)
        self.assertGreater(len(result.symbols), 0)

        # 验证符号类型
        symbol_types = {s.type for s in result.symbols}
        self.assertIn(SymbolType.CLASS, symbol_types)
        self.assertIn(SymbolType.METHOD, symbol_types)
        self.assertIn(SymbolType.PROPERTY, symbol_types)

    def test_parse_swift_file_complete(self):
        """测试解析完整的Swift文件"""
        test_file = os.path.join(self.test_dir, "TestClass.swift")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("""
// TestClass.swift
import Foundation

class TestClass {
    var publicProperty: String
    private var privateProperty: Int

    init(name: String) {
        self.publicProperty = name
        self.privateProperty = 0
    }

    func publicMethod() {
        print("Public method")
    }

    private func privateMethod() {
        print("Private method")
    }
}

struct TestStruct {
    var field: String
}

enum TestEnum {
    case optionA
    case optionB
}
""")

        # 解析文件
        parser = CodeParser(self.whitelist)
        result = parser.parse_file(test_file)

        # 验证结果
        self.assertIsNotNone(result)
        self.assertGreater(len(result.symbols), 0)

        # 验证符号类型
        symbol_types = {s.type for s in result.symbols}
        self.assertIn(SymbolType.CLASS, symbol_types)
        self.assertIn(SymbolType.METHOD, symbol_types)
        self.assertIn(SymbolType.PROPERTY, symbol_types)
        self.assertIn(SymbolType.STRUCT, symbol_types)
        self.assertIn(SymbolType.ENUM, symbol_types)

    def test_whitelist_filtering(self):
        """测试白名单过滤"""
        test_file = os.path.join(self.test_dir, "Test.m")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("""
@interface UIViewController (Test)
- (void)customMethod;
@end

@interface MyClass : NSObject
- (void)myMethod;
@end
""")

        parser = CodeParser(self.whitelist)
        result = parser.parse_file(test_file)

        # 验证：UIViewController应该被过滤掉
        class_names = [s.name for s in result.symbols if s.type == SymbolType.CLASS]
        self.assertNotIn("UIViewController", class_names)
        self.assertIn("MyClass", class_names)


class TestCodeTransformerIntegration(unittest.TestCase):
    """代码转换器集成测试"""

    def setUp(self):
        """测试前准备"""
        self.test_dir = tempfile.mkdtemp()
        self.whitelist = WhitelistManager(project_path=self.test_dir)
        self.generator = NameGenerator(
            strategy=NamingStrategy.RANDOM,
            min_length=8,
            max_length=12,
            seed="test_seed_12345"  # 固定种子保证可重复
        )

    def tearDown(self):
        """测试后清理"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_transform_objc_file(self):
        """测试转换ObjC文件"""
        # 创建测试文件
        test_file = os.path.join(self.test_dir, "MyClass.m")
        original_content = """
@interface MyClass : NSObject
@property (nonatomic, strong) NSString *myProperty;
- (void)myMethod;
@end

@implementation MyClass

- (void)myMethod {
    NSLog(@"Method called");
}

@end
"""
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(original_content)

        # 解析
        parser = CodeParser(self.whitelist)
        parsed_file = parser.parse_file(test_file)

        # 转换
        transformer = CodeTransformer(self.generator, self.whitelist)
        result = transformer.transform_file(test_file, parsed_file)

        # 验证结果
        self.assertEqual(len(result.errors), 0, f"转换失败: {result.errors}")
        self.assertGreater(result.replacements, 0)
        self.assertNotEqual(result.transformed_content, original_content)

        # 验证没有替换系统API
        self.assertIn("NSObject", result.transformed_content)
        self.assertIn("NSString", result.transformed_content)
        self.assertIn("NSLog", result.transformed_content)

    def test_transform_swift_file(self):
        """测试转换Swift文件"""
        test_file = os.path.join(self.test_dir, "MyClass.swift")
        original_content = """
class MyClass {
    var myProperty: String

    func myMethod() {
        print("Method called")
    }
}
"""
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(original_content)

        # 解析
        parser = CodeParser(self.whitelist)
        parsed_file = parser.parse_file(test_file)

        # 转换
        transformer = CodeTransformer(self.generator, self.whitelist)
        result = transformer.transform_file(test_file, parsed_file)

        # 验证结果
        self.assertEqual(len(result.errors), 0, f"转换失败: {result.errors}")
        self.assertGreater(result.replacements, 0)
        self.assertNotEqual(result.transformed_content, original_content)

    def test_comment_string_protection(self):
        """测试注释和字符串保护"""
        test_file = os.path.join(self.test_dir, "Test.m")
        original_content = """
// This comment mentions MyClass
@interface MyClass : NSObject
- (void)myMethod;
@end

@implementation MyClass
- (void)myMethod {
    NSString *str = @"This string mentions myMethod";
    /* Multi-line comment
       mentions MyClass
    */
}
@end
"""
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(original_content)

        # 解析和转换
        parser = CodeParser(self.whitelist)
        parsed_file = parser.parse_file(test_file)

        transformer = CodeTransformer(self.generator, self.whitelist)
        result = transformer.transform_file(test_file, parsed_file)

        # 验证：注释和字符串中的内容不应该被替换
        self.assertEqual(len(result.errors), 0, f"转换失败: {result.errors}")
        self.assertIn("// This comment mentions MyClass", result.transformed_content)
        self.assertIn('@"This string mentions myMethod"', result.transformed_content)


class TestObfuscationEngineIntegration(unittest.TestCase):
    """混淆引擎集成测试"""

    def setUp(self):
        """测试前准备"""
        self.test_dir = tempfile.mkdtemp()
        self.output_dir = tempfile.mkdtemp()

        # 创建简单的测试项目
        os.makedirs(os.path.join(self.test_dir, "Classes"), exist_ok=True)

        # 创建.m文件
        with open(os.path.join(self.test_dir, "Classes", "AppDelegate.m"), 'w') as f:
            f.write("""
#import "AppDelegate.h"

@implementation AppDelegate

- (BOOL)application:(UIApplication *)application didFinishLaunchingWithOptions:(NSDictionary *)launchOptions {
    return YES;
}

@end
""")

        # 创建.h文件
        with open(os.path.join(self.test_dir, "Classes", "AppDelegate.h"), 'w') as f:
            f.write("""
#import <UIKit/UIKit.h>

@interface AppDelegate : UIResponder <UIApplicationDelegate>
@property (strong, nonatomic) UIWindow *window;
@end
""")

    def tearDown(self):
        """测试后清理"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)

    def test_complete_obfuscation_flow(self):
        """测试完整的混淆流程"""
        # 创建配置
        config_manager = ConfigManager()
        config = config_manager.get_template("standard")
        config.use_fixed_seed = True
        config.fixed_seed = "test_seed"

        # 创建引擎
        engine = ObfuscationEngine(config)

        # 执行混淆
        result = engine.obfuscate(
            project_path=self.test_dir,
            output_dir=self.output_dir
        )

        # 验证结果
        self.assertTrue(result.success, f"混淆失败: {result.errors}")
        self.assertGreater(result.files_processed, 0)
        self.assertEqual(result.files_failed, 0)

        # 验证输出文件存在
        output_files = list(Path(self.output_dir).glob("*.m"))
        self.assertGreater(len(output_files), 0)

        # 验证映射文件
        mapping_file = os.path.join(self.output_dir, "obfuscation_mapping.json")
        self.assertTrue(os.path.exists(mapping_file))

        # 验证映射文件格式
        with open(mapping_file, 'r', encoding='utf-8') as f:
            mapping = json.load(f)
            self.assertIn('metadata', mapping)
            self.assertIn('mappings', mapping)
            self.assertGreater(len(mapping['mappings']), 0)

    def test_incremental_obfuscation(self):
        """测试增量混淆"""
        # 第一次混淆
        config1 = ObfuscationConfig(
            name="test1",
            class_names=True,
            method_names=True,
            use_fixed_seed=True,
            fixed_seed="test_seed_1"
        )

        engine1 = ObfuscationEngine(config1)
        result1 = engine1.obfuscate(self.test_dir, self.output_dir)

        self.assertTrue(result1.success)
        mapping_file1 = result1.mapping_file

        # 第二次混淆（增量）
        output_dir2 = tempfile.mkdtemp()
        try:
            config2 = ObfuscationConfig(
                name="test2",
                class_names=True,
                method_names=True,
                enable_incremental=True,
                mapping_file=mapping_file1
            )

            engine2 = ObfuscationEngine(config2)
            result2 = engine2.obfuscate(self.test_dir, output_dir2)

            self.assertTrue(result2.success)

            # 验证：使用了旧映射
            with open(mapping_file1, 'r') as f1:
                mapping1 = json.load(f1)
            with open(result2.mapping_file, 'r') as f2:
                mapping2 = json.load(f2)

            # 映射数量应该相同或更多（如果有新符号）
            self.assertGreaterEqual(
                len(mapping2['mappings']),
                len(mapping1['mappings'])
            )

        finally:
            if os.path.exists(output_dir2):
                shutil.rmtree(output_dir2)


class TestSystemAPIWhitelist(unittest.TestCase):
    """系统API白名单测试"""

    def test_common_system_classes(self):
        """测试常见系统类"""
        common_classes = [
            'UIViewController', 'UIView', 'UIButton', 'UILabel',
            'NSObject', 'NSString', 'NSArray', 'NSDictionary',
            'NSDate', 'NSData', 'NSURL'
        ]

        for cls in common_classes:
            self.assertTrue(
                SystemAPIWhitelist.is_system_api(cls, 'class'),
                f"{cls} 应该在系统类白名单中"
            )

    def test_common_system_methods(self):
        """测试常见系统方法"""
        common_methods = [
            'init', 'dealloc', 'viewDidLoad', 'viewWillAppear:',
            'alloc', 'copy', 'description'
        ]

        for method in common_methods:
            self.assertTrue(
                SystemAPIWhitelist.is_system_api(method, 'method'),
                f"{method} 应该在系统方法白名单中"
            )

    def test_custom_classes_not_whitelisted(self):
        """测试自定义类不在白名单"""
        custom_classes = [
            'MyViewController', 'CustomView', 'AppDelegate',
            'DataManager', 'NetworkService'
        ]

        for cls in custom_classes:
            self.assertFalse(
                SystemAPIWhitelist.is_system_api(cls, 'class'),
                f"{cls} 不应该在系统类白名单中"
            )


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    suite = unittest.TestSuite()

    # 添加测试
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestCodeParserIntegration))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestCodeTransformerIntegration))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestObfuscationEngineIntegration))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestSystemAPIWhitelist))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
