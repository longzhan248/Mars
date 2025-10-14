#!/usr/bin/env python3
"""
混淆功能完整测试套件

对混淆模块的核心功能进行全面测试
"""

import sys
import os
from pathlib import Path
import unittest
import tempfile
import shutil
import json

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from gui.modules.obfuscation.config_manager import (
    ConfigManager,
    ObfuscationConfig
)
from gui.modules.obfuscation.whitelist_manager import (
    WhitelistManager,
    SystemAPIWhitelist,
    WhitelistType
)
from gui.modules.obfuscation.name_generator import (
    NameGenerator,
    NamingStrategy
)
from gui.modules.obfuscation.project_analyzer import (
    ProjectAnalyzer,
    ProjectType
)


class TestConfigManager(unittest.TestCase):
    """配置管理器测试"""

    def setUp(self):
        """测试准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = ConfigManager()

    def tearDown(self):
        """清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_templates(self):
        """测试加载内置模板"""
        templates = self.manager.list_templates()
        self.assertEqual(len(templates), 3)

        # templates是字典列表，不是字符串列表
        template_names = [t['name'] for t in templates]
        self.assertIn("minimal", template_names)
        self.assertIn("standard", template_names)
        self.assertIn("aggressive", template_names)

    def test_get_template(self):
        """测试获取模板"""
        config = self.manager.get_template("standard")
        self.assertIsNotNone(config)
        self.assertEqual(config.name, "standard")
        self.assertTrue(config.class_names)
        self.assertTrue(config.method_names)

    def test_validate_config(self):
        """测试配置验证"""
        config = ObfuscationConfig()
        is_valid, errors = self.manager.validate_config(config)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

    def test_save_and_load_config(self):
        """测试保存和加载配置"""
        config = self.manager.get_template("standard")
        config.name = "test_config"

        # 保存（需要指定文件名，而不是目录）
        config_path = os.path.join(self.temp_dir, "test_config.json")
        saved_path = self.manager.save_config(config, config_path)
        self.assertTrue(os.path.exists(saved_path))

        # 加载
        loaded_config = self.manager.load_config(saved_path)
        self.assertEqual(loaded_config.name, "test_config")
        self.assertEqual(loaded_config.class_names, config.class_names)

    def test_create_custom_config(self):
        """测试创建自定义配置"""
        custom = self.manager.create_config_from_template(
            "standard",
            custom_name="my_project",
            overrides={"name_prefix": "MP", "min_name_length": 12}
        )

        self.assertEqual(custom.name, "my_project")
        self.assertEqual(custom.name_prefix, "MP")
        self.assertEqual(custom.min_name_length, 12)


class TestWhitelistManager(unittest.TestCase):
    """白名单管理器测试"""

    def setUp(self):
        """测试准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = WhitelistManager(self.temp_dir)

    def tearDown(self):
        """清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_system_api_detection(self):
        """测试系统API检测"""
        # UIKit类
        self.assertTrue(self.manager.is_whitelisted("UIViewController"))
        self.assertTrue(self.manager.is_whitelisted("UIView"))
        self.assertTrue(self.manager.is_whitelisted("UITableView"))

        # Foundation类
        self.assertTrue(self.manager.is_whitelisted("NSString"))
        self.assertTrue(self.manager.is_whitelisted("NSArray"))
        self.assertTrue(self.manager.is_whitelisted("NSDictionary"))

        # 系统方法
        self.assertTrue(self.manager.is_whitelisted("viewDidLoad"))
        self.assertTrue(self.manager.is_whitelisted("init"))
        self.assertTrue(self.manager.is_whitelisted("dealloc"))

        # 自定义类不应该在白名单
        self.assertFalse(self.manager.is_whitelisted("MyCustomClass"))
        self.assertFalse(self.manager.is_whitelisted("myCustomMethod"))

    def test_add_custom_whitelist(self):
        """测试添加自定义白名单"""
        # 添加前不在
        self.assertFalse(self.manager.is_whitelisted("MyUtil"))

        # 添加
        self.manager.add_custom("MyUtil", WhitelistType.CUSTOM, "工具类")

        # 添加后在
        self.assertTrue(self.manager.is_whitelisted("MyUtil"))

    def test_remove_custom_whitelist(self):
        """测试删除自定义白名单"""
        # 添加
        self.manager.add_custom("TempClass", WhitelistType.CUSTOM)

        # 确认存在
        self.assertTrue(self.manager.is_whitelisted("TempClass"))

        # 删除
        self.manager.remove_custom("TempClass")

        # 确认已删除
        self.assertFalse(self.manager.is_whitelisted("TempClass"))

    def test_cannot_remove_system_api(self):
        """测试不能删除系统API"""
        # 尝试删除系统类（应该失败）
        result = self.manager.remove_custom("UIViewController")
        self.assertFalse(result)

        # 确认仍在白名单
        self.assertTrue(self.manager.is_whitelisted("UIViewController"))

    def test_export_and_import_whitelist(self):
        """测试导出导入白名单"""
        # 添加自定义项
        self.manager.add_custom("CustomClass1", WhitelistType.CUSTOM)
        self.manager.add_custom("CustomClass2", WhitelistType.CUSTOM)

        # 导出
        export_path = os.path.join(self.temp_dir, "whitelist.json")
        self.manager.export_whitelist(export_path)

        # 创建新管理器并导入
        new_manager = WhitelistManager(self.temp_dir)
        new_manager.import_whitelist(export_path)

        # 验证导入的自定义项
        self.assertTrue(new_manager.is_whitelisted("CustomClass1"))
        self.assertTrue(new_manager.is_whitelisted("CustomClass2"))


class TestNameGenerator(unittest.TestCase):
    """名称生成器测试"""

    def test_random_strategy(self):
        """测试随机策略"""
        generator = NameGenerator(
            strategy=NamingStrategy.RANDOM,
            min_length=8,
            max_length=12
        )

        # 对相同输入，同一个generator会返回相同的映射（这是正确的行为）
        name1 = generator.generate("MyClass", "class")
        name2 = generator.generate("MyClass", "class")
        self.assertEqual(name1, name2)  # 相同输入应该相同输出

        # 对不同输入，应该产生不同名称
        name3 = generator.generate("AnotherClass", "class")
        self.assertNotEqual(name1, name3)

        # 长度应该在范围内
        self.assertGreaterEqual(len(name1), 8)
        self.assertLessEqual(len(name1), 12)

    def test_prefix_strategy(self):
        """测试前缀策略"""
        generator = NameGenerator(
            strategy=NamingStrategy.PREFIX,
            prefix="TEST"
        )

        name = generator.generate("MyClass", "class")

        # 应该有前缀
        self.assertTrue(name.startswith("TEST"))

    def test_deterministic_generation(self):
        """测试确定性生成"""
        gen1 = NameGenerator(
            strategy=NamingStrategy.RANDOM,
            seed="fixed_seed"
        )
        gen2 = NameGenerator(
            strategy=NamingStrategy.RANDOM,
            seed="fixed_seed"
        )

        # 相同种子应该产生相同结果
        name1 = gen1.generate("MyClass", "class")
        name2 = gen2.generate("MyClass", "class")

        self.assertEqual(name1, name2)

    def test_unique_names(self):
        """测试名称唯一性"""
        generator = NameGenerator()

        names = set()
        for i in range(100):
            name = generator.generate(f"Class{i}", "class")
            names.add(name)

        # 100个不同的原始名应该生成100个不同的混淆名
        self.assertEqual(len(names), 100)

    def test_same_input_same_output(self):
        """测试相同输入产生相同输出"""
        generator = NameGenerator(seed="test")

        name1 = generator.generate("MyClass", "class")
        name2 = generator.generate("MyClass", "class")

        # 同一个generator对相同输入应该返回相同的映射
        self.assertEqual(name1, name2)

    def test_export_import_mappings(self):
        """测试导出导入映射"""
        generator = NameGenerator(seed="test")

        # 生成一些映射
        generator.generate("Class1", "class")
        generator.generate("Class2", "class")
        generator.generate("method1", "method")

        # 导出
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        temp_file.close()

        try:
            generator.export_mappings(temp_file.name)

            # 验证文件存在
            self.assertTrue(os.path.exists(temp_file.name))

            # 读取验证
            with open(temp_file.name, 'r') as f:
                data = json.load(f)

            self.assertIn("mappings", data)
            self.assertEqual(len(data["mappings"]), 3)

        finally:
            os.unlink(temp_file.name)

    def test_reverse_lookup(self):
        """测试反向查找"""
        generator = NameGenerator()

        original = "MyClass"
        obfuscated = generator.generate(original, "class")

        # 反向查找
        found = generator.reverse_lookup(obfuscated)

        self.assertEqual(found, original)


class TestProjectAnalyzer(unittest.TestCase):
    """项目分析器测试"""

    def setUp(self):
        """测试准备"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_test_project(self):
        """创建测试项目结构"""
        # 创建基本结构
        os.makedirs(os.path.join(self.temp_dir, "MyApp"))
        os.makedirs(os.path.join(self.temp_dir, "MyApp", "Controllers"))
        os.makedirs(os.path.join(self.temp_dir, "MyApp", "Models"))

        # 创建一些文件
        with open(os.path.join(self.temp_dir, "MyApp", "Controllers", "ViewController.h"), 'w') as f:
            f.write("@interface ViewController : UIViewController\n@end\n")

        with open(os.path.join(self.temp_dir, "MyApp", "Controllers", "ViewController.m"), 'w') as f:
            f.write("@implementation ViewController\n@end\n")

        with open(os.path.join(self.temp_dir, "MyApp", "Models", "User.swift"), 'w') as f:
            f.write("class User { var name: String = \"\" }\n")

        return os.path.join(self.temp_dir, "MyApp")

    def test_analyze_project(self):
        """测试分析项目"""
        project_path = self._create_test_project()
        analyzer = ProjectAnalyzer(project_path)

        structure = analyzer.analyze()

        # 验证基本信息
        self.assertEqual(structure.project_name, "MyApp")
        self.assertEqual(structure.root_path, project_path)

        # 验证文件统计
        self.assertGreater(structure.total_files, 0)

    def test_get_source_files(self):
        """测试获取源文件"""
        project_path = self._create_test_project()
        analyzer = ProjectAnalyzer(project_path)

        analyzer.analyze()

        # 获取ObjC文件
        objc_files = analyzer.get_source_files(include_objc=True, include_swift=False)
        self.assertGreater(len(objc_files), 0)

        # 获取Swift文件
        swift_files = analyzer.get_source_files(include_objc=False, include_swift=True)
        self.assertGreater(len(swift_files), 0)

    def test_export_report(self):
        """测试导出报告"""
        project_path = self._create_test_project()
        analyzer = ProjectAnalyzer(project_path)

        analyzer.analyze()

        # 导出报告
        report_path = os.path.join(self.temp_dir, "report.json")
        analyzer.export_report(report_path)

        # 验证报告存在
        self.assertTrue(os.path.exists(report_path))

        # 读取验证
        with open(report_path, 'r') as f:
            data = json.load(f)

        self.assertIn("project_name", data)
        self.assertIn("files", data)


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加所有测试类
    suite.addTests(loader.loadTestsFromTestCase(TestConfigManager))
    suite.addTests(loader.loadTestsFromTestCase(TestWhitelistManager))
    suite.addTests(loader.loadTestsFromTestCase(TestNameGenerator))
    suite.addTests(loader.loadTestsFromTestCase(TestProjectAnalyzer))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result


if __name__ == '__main__':
    print("=" * 70)
    print("混淆功能完整测试")
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
        print("\n✅ 所有测试通过！混淆功能正常")
        sys.exit(0)
    else:
        print(f"\n❌ {len(result.failures) + len(result.errors)} 个测试未通过")
        sys.exit(1)
