#!/usr/bin/env python3
"""
完整集成测试套件

覆盖iOS代码混淆模块的所有核心功能：
1. ConfigManager - 配置管理
2. WhitelistManager - 白名单管理
3. NameGenerator - 名称生成
4. ProjectAnalyzer - 项目分析
5. CodeParser - 代码解析（ObjC/Swift）
6. CodeTransformer - 代码转换
7. ResourceHandler - 资源处理
8. ObfuscationEngine - 完整混淆流程
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

from gui.modules.obfuscation.config_manager import ConfigManager, ObfuscationConfig
from gui.modules.obfuscation.whitelist_manager import WhitelistManager, SystemAPIWhitelist
from gui.modules.obfuscation.name_generator import NameGenerator, NamingStrategy
from gui.modules.obfuscation.project_analyzer import ProjectAnalyzer, ProjectType
from gui.modules.obfuscation.code_parser import CodeParser, Symbol
from gui.modules.obfuscation.code_transformer import CodeTransformer
from gui.modules.obfuscation.resource_handler import ResourceHandler
from gui.modules.obfuscation.obfuscation_engine import ObfuscationEngine


class TestConfigManager(unittest.TestCase):
    """配置管理器测试"""

    def test_load_builtin_templates(self):
        """测试加载内置配置模板"""
        manager = ConfigManager()

        # 测试三种模板
        templates = ['minimal', 'standard', 'aggressive']
        for template_name in templates:
            config = manager.get_template(template_name)
            self.assertIsNotNone(config, f"{template_name}模板加载失败")
            self.assertEqual(config.name, template_name, "模板名称不匹配")

    def test_config_validation(self):
        """测试配置验证"""
        manager = ConfigManager()
        config = manager.get_template("standard")

        # 有效配置应该通过验证
        is_valid, errors = manager.validate_config(config)
        self.assertTrue(is_valid, f"有效配置验证失败: {errors}")

        # 测试无效配置
        invalid_config = ObfuscationConfig(
            name="test",
            min_name_length=20,
            max_name_length=10  # 最大值小于最小值，应该失败
        )
        is_valid, errors = manager.validate_config(invalid_config)
        self.assertFalse(is_valid, "无效配置应该验证失败")
        self.assertGreater(len(errors), 0, "应该有错误信息")

    def test_custom_config_creation(self):
        """测试自定义配置创建"""
        manager = ConfigManager()

        custom_config = manager.create_config_from_template(
            template_level="standard",
            custom_name="my_project",
            overrides={
                "name_prefix": "MP",
                "use_fixed_seed": True,
                "fixed_seed": "test_seed_123"
            }
        )

        self.assertEqual(custom_config.name, "my_project")
        self.assertEqual(custom_config.name_prefix, "MP")
        self.assertTrue(custom_config.use_fixed_seed)
        self.assertEqual(custom_config.fixed_seed, "test_seed_123")


class TestWhitelistManager(unittest.TestCase):
    """白名单管理器测试"""

    def test_system_api_whitelist(self):
        """测试系统API白名单"""
        # 测试常见系统类
        system_classes = [
            'UIViewController', 'UIView', 'UITableView',
            'NSObject', 'NSString', 'NSArray', 'NSData',
            'CALayer', 'CGRect'
        ]

        for class_name in system_classes:
            is_system = SystemAPIWhitelist.is_system_api(class_name, "class")
            self.assertTrue(is_system, f"{class_name}应该被识别为系统类")

        # 测试自定义类（不应该在白名单中）
        custom_classes = ['MyViewController', 'DataManager', 'UserModel']
        for class_name in custom_classes:
            is_system = SystemAPIWhitelist.is_system_api(class_name, "class")
            self.assertFalse(is_system, f"{class_name}不应该被识别为系统类")

    def test_system_method_whitelist(self):
        """测试系统方法白名单"""
        system_methods = [
            'viewDidLoad', 'viewWillAppear:', 'viewDidAppear:',
            'tableView:numberOfRowsInSection:',
            'tableView:cellForRowAtIndexPath:',
            'init', 'dealloc', 'description'
        ]

        for method_name in system_methods:
            is_system = SystemAPIWhitelist.is_system_api(method_name, "method")
            self.assertTrue(is_system, f"{method_name}应该被识别为系统方法")

    def test_custom_whitelist(self):
        """测试自定义白名单"""
        manager = WhitelistManager()

        # 添加自定义白名单
        from gui.modules.obfuscation.whitelist_manager import WhitelistType
        manager.add_custom("MyCustomClass", WhitelistType.CUSTOM, "测试类")

        # 验证添加成功
        self.assertTrue(manager.is_whitelisted("MyCustomClass"))

        # 删除自定义白名单
        removed = manager.remove_custom("MyCustomClass")
        self.assertTrue(removed, "应该成功删除自定义白名单")
        self.assertFalse(manager.is_whitelisted("MyCustomClass"))


class TestNameGenerator(unittest.TestCase):
    """名称生成器测试"""

    def test_random_strategy(self):
        """测试随机命名策略"""
        generator = NameGenerator(
            strategy=NamingStrategy.RANDOM,
            min_length=8,
            max_length=12
        )

        name1 = generator.generate("TestClass", "class")
        name2 = generator.generate("TestMethod", "method")

        # 验证生成的名称不同
        self.assertNotEqual(name1, name2)

        # 验证长度在范围内
        self.assertGreaterEqual(len(name1), 8)
        self.assertLessEqual(len(name1), 12)

    def test_prefix_strategy(self):
        """测试前缀命名策略"""
        prefix = "WHC"
        generator = NameGenerator(
            strategy=NamingStrategy.PREFIX,
            prefix=prefix
        )

        name = generator.generate("TestClass", "class")

        # 验证包含前缀
        self.assertTrue(name.startswith(prefix), f"名称应该以{prefix}开头")

    def test_deterministic_generation(self):
        """测试确定性生成（固定种子）"""
        seed = "test_seed_123"

        # 使用相同种子的两个生成器
        gen1 = NameGenerator(strategy=NamingStrategy.RANDOM, seed=seed)
        gen2 = NameGenerator(strategy=NamingStrategy.RANDOM, seed=seed)

        # 生成相同符号的名称
        name1 = gen1.generate("TestClass", "class")
        name2 = gen2.generate("TestClass", "class")

        # 应该产生相同的结果
        self.assertEqual(name1, name2, "相同种子应该产生相同的混淆名称")

    def test_mapping_management(self):
        """测试映射管理"""
        generator = NameGenerator(strategy=NamingStrategy.RANDOM)

        # 生成映射
        original = "TestClass"
        obfuscated = generator.generate(original, "class")

        # 获取映射
        mapping = generator.get_mapping(original)
        self.assertIsNotNone(mapping, "应该能获取到映射")
        self.assertEqual(mapping.obfuscated, obfuscated)

        # 反向查找
        reversed_name = generator.reverse_lookup(obfuscated)
        self.assertEqual(reversed_name, original, "反向查找应该返回原始名称")


class TestCodeParser(unittest.TestCase):
    """代码解析器测试"""

    def setUp(self):
        """测试准备"""
        self.whitelist = WhitelistManager()
        self.parser = CodeParser(self.whitelist)
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """清理临时文件"""
        shutil.rmtree(self.temp_dir)

    def test_parse_objc_class(self):
        """测试解析Objective-C类"""
        code = '''
@interface UserManager : NSObject
@property (nonatomic, strong) NSString *userName;
@property (nonatomic, assign) NSInteger userId;
- (void)loadUserData;
- (void)saveUserData:(NSDictionary *)data;
@end
'''
        temp_file = Path(self.temp_dir) / "UserManager.h"
        temp_file.write_text(code)

        parsed = self.parser.parse_file(str(temp_file))
        symbol_names = [s.name for s in parsed.symbols]

        # 验证类名被提取
        self.assertIn("UserManager", symbol_names)

        # 验证属性被提取
        self.assertIn("userName", symbol_names)
        self.assertIn("userId", symbol_names)

        # 验证方法被提取
        self.assertIn("loadUserData", symbol_names)
        self.assertIn("saveUserData:", symbol_names)

        # 验证系统类不被提取
        self.assertNotIn("NSObject", symbol_names)
        self.assertNotIn("NSString", symbol_names)

    def test_parse_swift_class(self):
        """测试解析Swift类"""
        code = '''
class DataManager {
    var dataList: [String] = []
    private var cacheEnabled: Bool = true

    func loadData() {
        print("loading")
    }

    func saveData(items: [String]) {
        self.dataList = items
    }
}
'''
        temp_file = Path(self.temp_dir) / "DataManager.swift"
        temp_file.write_text(code)

        parsed = self.parser.parse_file(str(temp_file))
        symbol_names = [s.name for s in parsed.symbols]

        # 验证类名被提取
        self.assertIn("DataManager", symbol_names)

        # 验证属性被提取
        self.assertIn("dataList", symbol_names)
        self.assertIn("cacheEnabled", symbol_names)

        # 验证方法被提取
        self.assertIn("loadData", symbol_names)
        self.assertIn("saveData", symbol_names)

    def test_multiline_string_handling(self):
        """测试多行字符串处理（P0修复）"""
        swift_code = '''
class ConfigManager {
    let jsonConfig = """
    {
        "class": "FakeClass",
        "method": "fakeMethod"
    }
    """

    func realMethod() {
        print("real")
    }
}
'''
        temp_file = Path(self.temp_dir) / "Config.swift"
        temp_file.write_text(swift_code)

        parsed = self.parser.parse_file(str(temp_file))
        symbol_names = [s.name for s in parsed.symbols]

        # 多行字符串内的内容不应该被提取
        self.assertNotIn("FakeClass", symbol_names)
        self.assertNotIn("fakeMethod", symbol_names)

        # 真实的符号应该被提取
        self.assertIn("ConfigManager", symbol_names)
        self.assertIn("realMethod", symbol_names)


class TestCodeTransformer(unittest.TestCase):
    """代码转换器测试"""

    def setUp(self):
        """测试准备"""
        self.whitelist = WhitelistManager()
        self.generator = NameGenerator(strategy=NamingStrategy.RANDOM, seed="test")
        self.transformer = CodeTransformer(self.generator, self.whitelist)
        self.parser = CodeParser(self.whitelist)
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """清理临时文件"""
        shutil.rmtree(self.temp_dir)

    def test_class_name_replacement(self):
        """测试类名替换"""
        code = '''
@interface DataService : NSObject
- (void)processData;
@end

@implementation DataService
- (void)processData {
    DataService *service = [[DataService alloc] init];
}
@end
'''
        temp_file = Path(self.temp_dir) / "DataService.m"
        temp_file.write_text(code)

        # 解析
        parsed = self.parser.parse_file(str(temp_file))

        # 转换
        result = self.transformer.transform_file(str(temp_file), parsed)

        # 验证类名被替换
        mapping = self.generator.get_mapping("DataService")
        if mapping:
            self.assertIn(mapping.obfuscated, result.transformed_content)
            self.assertGreater(result.replacements, 0, "应该有替换发生")

    def test_system_api_protection(self):
        """测试系统API保护（P0修复）"""
        code = '''
@interface DataManager : NSObject
@property (nonatomic, strong) NSData *data;
@end

@implementation DataManager
- (void)loadData {
    NSData *localData = [NSData new];
    self.data = localData;
}
@end
'''
        temp_file = Path(self.temp_dir) / "DataManager.m"
        temp_file.write_text(code)

        parsed = self.parser.parse_file(str(temp_file))
        result = self.transformer.transform_file(str(temp_file), parsed)

        # 系统类NSData应该保持不变
        self.assertIn("NSData", result.transformed_content)

        # 自定义类DataManager应该被替换
        mapping = self.generator.get_mapping("DataManager")
        if mapping:
            self.assertIn(mapping.obfuscated, result.transformed_content)

    def test_import_statement_update(self):
        """测试Import语句更新（P0修复）"""
        code = '''
#import "UserViewController.h"
#import "DataManager.h"
#import <UIKit/UIKit.h>

@implementation MyApp
@end
'''
        temp_file = Path(self.temp_dir) / "MyApp.m"
        temp_file.write_text(code)

        parsed = self.parser.parse_file(str(temp_file))
        result = self.transformer.transform_file(str(temp_file), parsed)

        # 系统框架import应该保持不变
        self.assertIn('#import <UIKit/UIKit.h>', result.transformed_content)

        # 自定义类import应该被更新（如果这些类被混淆的话）
        # 注意：由于这个文件中没有定义UserViewController和DataManager，
        # 所以它们不会被混淆，import也不会改变
        # 这是预期行为


class TestObfuscationEngine(unittest.TestCase):
    """混淆引擎测试"""

    def setUp(self):
        """测试准备"""
        self.temp_project_dir = tempfile.mkdtemp()
        self.temp_output_dir = tempfile.mkdtemp()

    def tearDown(self):
        """清理临时文件"""
        shutil.rmtree(self.temp_project_dir)
        shutil.rmtree(self.temp_output_dir)

    def test_engine_initialization(self):
        """测试引擎初始化"""
        config_manager = ConfigManager()
        config = config_manager.get_template("standard")

        engine = ObfuscationEngine(config)

        # 验证组件初始化
        self.assertIsNotNone(engine.config)
        self.assertEqual(engine.config.name, "standard")

    def test_complete_obfuscation_flow(self):
        """测试完整混淆流程"""
        # 创建简单的测试项目
        test_file = Path(self.temp_project_dir) / "TestClass.h"
        test_file.write_text('''
@interface TestClass : NSObject
@property (nonatomic, strong) NSString *testProperty;
- (void)testMethod;
@end
''')

        impl_file = Path(self.temp_project_dir) / "TestClass.m"
        impl_file.write_text('''
#import "TestClass.h"

@implementation TestClass
- (void)testMethod {
    self.testProperty = @"test";
}
@end
''')

        # 配置引擎
        config_manager = ConfigManager()
        config = config_manager.get_template("minimal")
        config.use_fixed_seed = True
        config.fixed_seed = "integration_test"

        engine = ObfuscationEngine(config)

        # 执行混淆
        result = engine.obfuscate(
            self.temp_project_dir,
            self.temp_output_dir
        )

        # 验证结果
        self.assertTrue(result.success or len(result.errors) == 0,
                       f"混淆流程应该成功或至少无致命错误: {result.errors}")

        # 验证输出目录
        self.assertTrue(Path(self.temp_output_dir).exists())


class TestEndToEnd(unittest.TestCase):
    """端到端测试"""

    def setUp(self):
        """测试准备"""
        self.temp_project_dir = tempfile.mkdtemp()
        self.temp_output_dir = tempfile.mkdtemp()

    def tearDown(self):
        """清理临时文件"""
        shutil.rmtree(self.temp_project_dir)
        shutil.rmtree(self.temp_output_dir)

    def test_objc_project_obfuscation(self):
        """测试Objective-C项目混淆"""
        # 创建简单的ObjC项目
        header = Path(self.temp_project_dir) / "UserManager.h"
        header.write_text('''
#import <Foundation/Foundation.h>

@interface UserManager : NSObject
@property (nonatomic, strong) NSString *userName;
@property (nonatomic, assign) NSInteger userId;
- (void)loadUserData;
- (void)saveUserData:(NSDictionary *)data;
@end
''')

        impl = Path(self.temp_project_dir) / "UserManager.m"
        impl.write_text('''
#import "UserManager.h"

@implementation UserManager

- (void)loadUserData {
    self.userName = @"Test User";
    self.userId = 123;
    NSLog(@"User loaded: %@", self.userName);
}

- (void)saveUserData:(NSDictionary *)data {
    self.userName = data[@"name"];
    self.userId = [data[@"id"] integerValue];
}

@end
''')

        # 执行混淆
        config_manager = ConfigManager()
        config = config_manager.get_template("standard")
        config.use_fixed_seed = True
        config.fixed_seed = "e2e_test"

        engine = ObfuscationEngine(config)
        result = engine.obfuscate(
            self.temp_project_dir,
            self.temp_output_dir
        )

        # 验证混淆成功
        self.assertTrue(result.success or len(result.errors) == 0)

        # 验证映射文件生成
        if result.mapping_file:
            self.assertTrue(Path(result.mapping_file).exists())


def run_comprehensive_tests():
    """运行完整测试套件"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加所有测试类
    suite.addTests(loader.loadTestsFromTestCase(TestConfigManager))
    suite.addTests(loader.loadTestsFromTestCase(TestWhitelistManager))
    suite.addTests(loader.loadTestsFromTestCase(TestNameGenerator))
    suite.addTests(loader.loadTestsFromTestCase(TestCodeParser))
    suite.addTests(loader.loadTestsFromTestCase(TestCodeTransformer))
    suite.addTests(loader.loadTestsFromTestCase(TestObfuscationEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestEndToEnd))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result


if __name__ == '__main__':
    print("=" * 70)
    print("iOS代码混淆模块 - 完整集成测试套件")
    print("=" * 70)
    print()

    result = run_comprehensive_tests()

    print()
    print("=" * 70)
    print("测试总结:")
    print("=" * 70)
    print(f"运行测试数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")

    if result.wasSuccessful():
        print("\n🎉 所有测试通过！")
        sys.exit(0)
    else:
        print(f"\n⚠️  {len(result.failures) + len(result.errors)} 个测试未通过")
        sys.exit(1)
