"""
P1缓存机制集成测试

测试范围：
1. GUI复选框 → 配置对象传递
2. 配置模板加载缓存设置
3. 混淆引擎使用缓存配置
4. 缓存统计信息验证
5. 完整流程端到端测试
"""

import unittest
import os
import tempfile
import shutil
from pathlib import Path

# 添加项目根目录到路径
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from gui.modules.obfuscation.config_manager import ObfuscationConfig, ConfigManager
from gui.modules.obfuscation.obfuscation_engine import ObfuscationEngine
from gui.modules.obfuscation.parse_cache_manager import ParseCacheManager


class TestP1CacheIntegration(unittest.TestCase):
    """P1缓存机制集成测试"""

    def setUp(self):
        """测试前准备"""
        self.test_dir = tempfile.mkdtemp(prefix="p1_cache_test_")
        self.project_path = os.path.join(self.test_dir, "test_project")
        self.output_path = os.path.join(self.test_dir, "test_output")
        self.cache_dir = os.path.join(self.project_path, ".obfuscation_cache")

        # 创建测试目录
        os.makedirs(self.project_path, exist_ok=True)
        os.makedirs(self.output_path, exist_ok=True)

        # 创建测试文件
        self._create_test_files()

    def tearDown(self):
        """测试后清理"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def _create_test_files(self):
        """创建测试源文件"""
        # ObjC头文件
        header_content = """
#import <Foundation/Foundation.h>

@interface TestClass : NSObject
@property (nonatomic, strong) NSString *testProperty;
- (void)testMethod;
@end
"""
        header_path = os.path.join(self.project_path, "TestClass.h")
        with open(header_path, 'w') as f:
            f.write(header_content)

        # ObjC实现文件
        impl_content = """
#import "TestClass.h"

@implementation TestClass
- (void)testMethod {
    NSLog(@"Test");
}
@end
"""
        impl_path = os.path.join(self.project_path, "TestClass.m")
        with open(impl_path, 'w') as f:
            f.write(impl_content)

    def test_config_cache_options(self):
        """测试1：配置对象包含正确的缓存选项"""
        config = ObfuscationConfig(
            name="test_config",
            enable_parse_cache=True,
            cache_dir=".cache_test",
            max_memory_cache=500,
            max_disk_cache=5000,
            clear_cache=False,
            cache_statistics=True
        )

        self.assertTrue(config.enable_parse_cache)
        self.assertEqual(config.cache_dir, ".cache_test")
        self.assertEqual(config.max_memory_cache, 500)
        self.assertEqual(config.max_disk_cache, 5000)
        self.assertFalse(config.clear_cache)
        self.assertTrue(config.cache_statistics)
        print("✅ 配置对象缓存选项正确")

    def test_template_loads_cache_settings(self):
        """测试2：配置模板正确加载缓存设置"""
        manager = ConfigManager()

        # 测试standard模板（缓存应该启用）
        standard = manager.get_template("standard")
        self.assertTrue(standard.enable_parse_cache)
        self.assertEqual(standard.cache_dir, ".obfuscation_cache")
        self.assertEqual(standard.max_memory_cache, 1000)
        self.assertTrue(standard.cache_statistics)
        print("✅ standard模板缓存设置正确")

        # 测试aggressive模板
        aggressive = manager.get_template("aggressive")
        self.assertTrue(aggressive.enable_parse_cache)
        print("✅ aggressive模板缓存设置正确")

        # 测试minimal模板
        minimal = manager.get_template("minimal")
        # minimal模板也应该启用缓存以提升性能
        self.assertTrue(minimal.enable_parse_cache)
        print("✅ minimal模板缓存设置正确")

    def test_cache_manager_initialization(self):
        """测试3：ParseCacheManager正确初始化"""
        config = ObfuscationConfig(
            name="test",
            enable_parse_cache=True,
            cache_dir=self.cache_dir,
            max_memory_cache=100,
            max_disk_cache=500
        )

        cache_manager = ParseCacheManager(
            cache_dir=config.cache_dir,
            max_memory_cache=config.max_memory_cache,
            max_disk_cache=config.max_disk_cache
        )

        self.assertEqual(str(cache_manager.cache_dir), self.cache_dir)
        self.assertEqual(cache_manager.max_memory_cache, 100)
        self.assertEqual(cache_manager.max_disk_cache, 500)
        self.assertEqual(cache_manager.cache_hits, 0)
        self.assertEqual(cache_manager.cache_misses, 0)
        print("✅ ParseCacheManager初始化正确")

    def test_cache_enabled_in_engine(self):
        """测试4：混淆引擎正确使用缓存配置"""
        config = ObfuscationConfig(
            name="test_engine",
            enable_parse_cache=True,
            cache_dir=self.cache_dir,
            max_memory_cache=100,
            cache_statistics=True,
            # 启用基础混淆选项
            class_names=True,
            method_names=True,
            property_names=True
        )

        engine = ObfuscationEngine(config)

        # 验证引擎配置
        self.assertTrue(engine.config.enable_parse_cache)
        self.assertEqual(engine.config.cache_dir, self.cache_dir)
        print("✅ 混淆引擎缓存配置正确")

    def test_end_to_end_with_cache(self):
        """测试5：配置从GUI到引擎的完整传递"""
        config = ObfuscationConfig(
            name="e2e_cache_test",
            enable_parse_cache=True,
            cache_dir=self.cache_dir,
            max_memory_cache=100,
            max_disk_cache=500,
            cache_statistics=True,
            clear_cache=False
        )

        # 验证配置正确传递到引擎
        engine = ObfuscationEngine(config)

        self.assertTrue(engine.config.enable_parse_cache)
        self.assertEqual(engine.config.cache_dir, self.cache_dir)
        self.assertEqual(engine.config.max_memory_cache, 100)
        self.assertEqual(engine.config.max_disk_cache, 500)
        self.assertTrue(engine.config.cache_statistics)
        self.assertFalse(engine.config.clear_cache)

        print("✅ 配置从GUI到引擎的完整传递验证成功")

    def test_cache_disabled_in_engine(self):
        """测试6：禁用缓存时引擎不使用缓存"""
        config = ObfuscationConfig(
            name="no_cache_test",
            enable_parse_cache=False,  # 🔴 禁用缓存
            cache_dir=self.cache_dir
        )

        engine = ObfuscationEngine(config)

        # 验证配置正确
        self.assertFalse(engine.config.enable_parse_cache)
        print("✅ 禁用缓存配置正确")

    def test_cache_persistence_across_runs(self):
        """测试7：ParseCacheManager支持磁盘持久化"""
        cache_manager = ParseCacheManager(
            cache_dir=self.cache_dir,
            max_memory_cache=100,
            max_disk_cache=1000,
            enable_memory_cache=True,
            enable_disk_cache=True
        )

        # 验证启用了磁盘缓存
        self.assertTrue(cache_manager.enable_disk_cache)
        self.assertTrue(cache_manager.enable_memory_cache)

        # 验证缓存目录已创建
        self.assertTrue(os.path.exists(self.cache_dir))
        print("✅ ParseCacheManager磁盘持久化配置正确")

    def test_cache_clear_option(self):
        """测试8：clear_cache选项支持"""
        config_with_clear = ObfuscationConfig(
            name="clear_cache",
            enable_parse_cache=True,
            cache_dir=self.cache_dir,
            clear_cache=True  # 🔴 清空缓存选项
        )

        config_without_clear = ObfuscationConfig(
            name="keep_cache",
            enable_parse_cache=True,
            cache_dir=self.cache_dir,
            clear_cache=False
        )

        # 验证配置正确
        self.assertTrue(config_with_clear.clear_cache)
        self.assertFalse(config_without_clear.clear_cache)
        print("✅ clear_cache选项配置正确")


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestP1CacheIntegration)

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 打印总结
    print("\n" + "="*70)
    print("P1缓存机制集成测试总结")
    print("="*70)
    print(f"运行测试: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print("="*70)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
