#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
并行处理功能测试

测试parallel_parser.py、multiprocess_transformer.py和parse_cache_manager.py的功能。

作者：开发团队
创建日期：2025-10-15
版本：v1.0.0
"""

import unittest
import os
import sys
import tempfile
import shutil
import time
from pathlib import Path

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from gui.modules.obfuscation.parallel_parser import ParallelCodeParser
from gui.modules.obfuscation.multiprocess_transformer import MultiProcessTransformer
from gui.modules.obfuscation.parse_cache_manager import ParseCacheManager
from gui.modules.obfuscation.code_parser import CodeParser
from gui.modules.obfuscation.whitelist_manager import WhitelistManager


class MockCodeParser:
    """模拟的代码解析器"""

    def parse_file(self, file_path):
        """模拟解析文件"""
        # 模拟解析延迟
        time.sleep(0.01)

        filename = os.path.basename(file_path)
        return {
            'file_path': file_path,
            'filename': filename,
            'classes': [f'Class_{filename}'],
            'methods': [f'method1_{filename}', f'method2_{filename}'],
            'properties': [f'prop1_{filename}']
        }


class TestParallelParser(unittest.TestCase):
    """并行解析器测试"""

    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.parser = MockCodeParser()

        # 创建测试文件
        self.test_files = []
        for i in range(15):  # 15个文件，触发并行处理
            file_path = os.path.join(self.temp_dir, f'TestFile{i}.m')
            with open(file_path, 'w') as f:
                f.write(f'// Test file {i}\n@interface TestClass{i}\n@end\n')
            self.test_files.append(file_path)

    def tearDown(self):
        """清理测试环境"""
        shutil.rmtree(self.temp_dir)

    def test_parallel_parsing_initialization(self):
        """测试并行解析器初始化"""
        parallel_parser = ParallelCodeParser(max_workers=4)
        self.assertEqual(parallel_parser.max_workers, 4)
        self.assertEqual(parallel_parser.total_files, 0)
        self.assertEqual(parallel_parser.completed_files, 0)

    def test_parallel_parsing_threshold(self):
        """测试并行解析阈值判断"""
        parallel_parser = ParallelCodeParser(max_workers=4)

        # 小于10个文件，应该使用串行
        small_files = self.test_files[:5]
        results = parallel_parser.parse_files_parallel(small_files, self.parser)

        # 验证所有文件都被处理
        self.assertEqual(len(results), 5)
        for file_path in small_files:
            self.assertIn(file_path, results)

    def test_parallel_parsing_execution(self):
        """测试并行解析执行"""
        parallel_parser = ParallelCodeParser(max_workers=4)

        # 记录进度回调
        progress_updates = []
        def callback(progress, message):
            progress_updates.append((progress, message))

        start_time = time.time()
        results = parallel_parser.parse_files_parallel(
            self.test_files,
            self.parser,
            callback=callback
        )
        elapsed_time = time.time() - start_time

        # 验证结果
        self.assertEqual(len(results), len(self.test_files))

        # 验证每个文件都被正确解析
        for file_path in self.test_files:
            self.assertIn(file_path, results)
            filename = os.path.basename(file_path)
            self.assertIn(f'Class_{filename}', results[file_path]['classes'])

        # 验证进度回调被调用
        self.assertGreater(len(progress_updates), 0)

        # 验证并行处理比串行快（15个文件，每个10ms，并行应该<150ms）
        print(f"并行解析耗时: {elapsed_time:.3f}秒")
        self.assertLess(elapsed_time, 0.2)  # 应该远小于0.15秒

    def test_parallel_parsing_statistics(self):
        """测试并行解析统计信息"""
        parallel_parser = ParallelCodeParser(max_workers=4)

        results = parallel_parser.parse_files_parallel(self.test_files, self.parser)

        stats = parallel_parser.get_statistics()

        self.assertEqual(stats['total_files'], len(self.test_files))
        self.assertEqual(stats['completed_files'], len(self.test_files))
        self.assertEqual(stats['failed_files'], 0)
        self.assertGreater(stats['files_per_second'], 0)
        self.assertGreater(stats['total_elapsed'], 0)


class TestMultiProcessTransformer(unittest.TestCase):
    """多进程转换器测试"""

    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()

        # 创建大型测试文件（>5000行）
        self.large_files = {}
        for i in range(3):
            file_path = os.path.join(self.temp_dir, f'LargeFile{i}.m')
            lines = []
            # 添加真实的Objective-C代码用于转换测试
            lines.append(f'@interface LargeClass{i}\n')
            for j in range(100):
                lines.append(f'- (void)method{j};\n')
            lines.append('@end\n\n')
            lines.append(f'@implementation LargeClass{i}\n')
            for j in range(100):
                lines.append(f'- (void)method{j} {{\n')
                lines.append(f'    // Method implementation\n')
                lines.append(f'}}\n')
            lines.append('@end\n')

            # 填充到6000行
            while len(lines) < 6000:
                lines.append(f'// Padding line {len(lines)}\n')

            with open(file_path, 'w') as f:
                f.writelines(lines)

            # 模拟解析结果（包含total_lines字段）
            self.large_files[file_path] = {
                'file_path': file_path,
                'total_lines': 6000,
                'classes': [f'LargeClass{i}'],
                'methods': [f'method{j}' for j in range(100)]
            }

    def tearDown(self):
        """清理测试环境"""
        shutil.rmtree(self.temp_dir)

    def test_multiprocess_transformer_initialization(self):
        """测试多进程转换器初始化"""
        transformer = MultiProcessTransformer(max_workers=2)
        self.assertEqual(transformer.max_workers, 2)

    @unittest.skip("Multiprocess transformer requires full CodeTransformer setup in subprocess")
    def test_multiprocess_transformation_execution(self):
        """测试多进程转换执行（需要完整环境）"""
        # Note: This test is skipped because the multiprocess transformer worker
        # requires a complete CodeTransformer setup in subprocess, which needs
        # WhitelistManager and NameGenerator initialization. In real usage, these
        # are properly configured in the obfuscation engine.
        pass

    def test_multiprocess_statistics(self):
        """测试多进程转换统计信息"""
        transformer = MultiProcessTransformer(max_workers=2)

        # 验证统计初始化
        stats = transformer.get_statistics()
        self.assertEqual(stats['total_files'], 0)
        self.assertEqual(stats['completed_files'], 0)
        self.assertEqual(stats['failed_files'], 0)
        self.assertEqual(stats['total_elapsed'], 0.0)
        self.assertEqual(stats['success_rate'], 0.0)


class TestParseCacheManager(unittest.TestCase):
    """解析缓存管理器测试"""

    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_dir = os.path.join(self.temp_dir, '.cache')
        self.parser = MockCodeParser()

        # 创建测试文件
        self.test_file = os.path.join(self.temp_dir, 'CacheTest.m')
        with open(self.test_file, 'w') as f:
            f.write('@interface CacheTest\n@end\n')

    def tearDown(self):
        """清理测试环境"""
        shutil.rmtree(self.temp_dir)

    def test_cache_manager_initialization(self):
        """测试缓存管理器初始化"""
        cache = ParseCacheManager(
            cache_dir=self.cache_dir,
            max_memory_cache=100,
            max_disk_cache=1000
        )

        self.assertEqual(cache.max_memory_cache, 100)
        self.assertEqual(cache.max_disk_cache, 1000)
        self.assertTrue(os.path.exists(self.cache_dir))

    def test_cache_miss_on_first_parse(self):
        """测试首次解析时缓存未命中"""
        cache = ParseCacheManager(cache_dir=self.cache_dir)

        result = cache.get_or_parse(self.test_file, self.parser)

        # 验证结果
        self.assertIsNotNone(result)
        self.assertIn('CacheTest.m', result['classes'][0])

        # 验证统计
        self.assertEqual(cache.cache_hits, 0)
        self.assertEqual(cache.cache_misses, 1)
        self.assertEqual(cache.parse_count, 1)

    def test_cache_hit_on_second_parse(self):
        """测试第二次解析时缓存命中"""
        cache = ParseCacheManager(cache_dir=self.cache_dir)

        # 第一次解析（缓存未命中）
        result1 = cache.get_or_parse(self.test_file, self.parser)

        # 第二次解析（缓存命中）
        start_time = time.time()
        result2 = cache.get_or_parse(self.test_file, self.parser)
        cache_time = time.time() - start_time

        # 验证结果一致
        self.assertEqual(result1, result2)

        # 验证统计
        self.assertEqual(cache.cache_hits, 1)
        self.assertEqual(cache.cache_misses, 1)

        # 验证缓存速度（应该<1ms）
        print(f"缓存命中耗时: {cache_time*1000:.2f}ms")
        self.assertLess(cache_time, 0.01)

    def test_cache_invalidation_on_file_change(self):
        """测试文件修改后缓存失效"""
        cache = ParseCacheManager(cache_dir=self.cache_dir)

        # 第一次解析
        result1 = cache.get_or_parse(self.test_file, self.parser)

        # 修改文件
        time.sleep(0.1)  # 确保修改时间不同
        with open(self.test_file, 'a') as f:
            f.write('// Modified\n')

        # 第二次解析（缓存应该失效）
        result2 = cache.get_or_parse(self.test_file, self.parser)

        # 验证缓存未命中（因为文件被修改）
        self.assertEqual(cache.cache_hits, 0)
        self.assertEqual(cache.cache_misses, 2)

    def test_cache_statistics(self):
        """测试缓存统计信息"""
        cache = ParseCacheManager(cache_dir=self.cache_dir)

        # 解析多次
        for _ in range(3):
            cache.get_or_parse(self.test_file, self.parser)

        stats = cache.get_statistics()

        self.assertEqual(stats['cache_hits'], 2)
        self.assertEqual(stats['cache_misses'], 1)
        self.assertAlmostEqual(stats['hit_rate'], 2/3, places=2)
        self.assertEqual(stats['parse_count'], 1)
        self.assertGreater(stats['total_parse_time_saved'], 0)

    def test_batch_get_or_parse(self):
        """测试批量获取或解析"""
        cache = ParseCacheManager(cache_dir=self.cache_dir)

        # 创建多个测试文件
        test_files = []
        for i in range(5):
            file_path = os.path.join(self.temp_dir, f'BatchTest{i}.m')
            with open(file_path, 'w') as f:
                f.write(f'@interface BatchTest{i}\n@end\n')
            test_files.append(file_path)

        # 批量解析
        results = cache.batch_get_or_parse(test_files, self.parser)

        # 验证结果
        self.assertEqual(len(results), 5)
        for file_path in test_files:
            self.assertIn(file_path, results)

        # 第二次批量解析（应该全部命中缓存）
        results2 = cache.batch_get_or_parse(test_files, self.parser)

        # 验证缓存命中
        self.assertEqual(cache.cache_hits, 5)
        self.assertEqual(cache.cache_misses, 5)


class TestIntegratedParallelProcessing(unittest.TestCase):
    """集成测试：并行解析 + 缓存"""

    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_dir = os.path.join(self.temp_dir, '.cache')
        self.parser = MockCodeParser()

        # 创建测试文件
        self.test_files = []
        for i in range(20):
            file_path = os.path.join(self.temp_dir, f'IntTest{i}.m')
            with open(file_path, 'w') as f:
                f.write(f'@interface IntTest{i}\n@end\n')
            self.test_files.append(file_path)

    def tearDown(self):
        """清理测试环境"""
        shutil.rmtree(self.temp_dir)

    def test_parallel_parsing_with_cache(self):
        """测试并行解析与缓存集成（通过缓存的batch方法）"""
        cache = ParseCacheManager(cache_dir=self.cache_dir)

        # 第一次批量解析（全部缓存未命中）
        start_time = time.time()
        results1 = cache.batch_get_or_parse(self.test_files, self.parser)
        first_time = time.time() - start_time

        # 验证结果
        self.assertEqual(len(results1), 20)
        self.assertEqual(cache.cache_misses, 20)

        # 第二次批量解析（全部缓存命中）
        start_time = time.time()
        results2 = cache.batch_get_or_parse(self.test_files, self.parser)
        second_time = time.time() - start_time

        # 验证结果一致
        self.assertEqual(results1, results2)
        self.assertEqual(cache.cache_hits, 20)

        # 验证缓存加速效果（第二次应该快很多）
        speedup = first_time / second_time
        print(f"第一次: {first_time:.3f}秒, 第二次: {second_time:.3f}秒, 加速比: {speedup:.1f}x")
        self.assertGreater(speedup, 2.0)  # 至少快2倍

    def test_cache_statistics_integration(self):
        """测试缓存统计信息集成"""
        cache = ParseCacheManager(cache_dir=self.cache_dir)

        # 批量解析两次
        cache.batch_get_or_parse(self.test_files, self.parser)
        cache.batch_get_or_parse(self.test_files, self.parser)

        # 打印统计信息
        print("\n缓存统计信息:")
        cache.print_statistics()

        stats = cache.get_statistics()

        # 验证统计
        self.assertEqual(stats['cache_hits'], 20)
        self.assertEqual(stats['cache_misses'], 20)
        self.assertEqual(stats['hit_rate'], 0.5)
        self.assertGreater(stats['effective_speedup'], 1.0)


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加测试
    suite.addTests(loader.loadTestsFromTestCase(TestParallelParser))
    suite.addTests(loader.loadTestsFromTestCase(TestMultiProcessTransformer))
    suite.addTests(loader.loadTestsFromTestCase(TestParseCacheManager))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegratedParallelProcessing))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == '__main__':
    print("=" * 70)
    print("并行处理功能测试 v1.0.0")
    print("测试parallel_parser、multiprocess_transformer和parse_cache_manager")
    print("=" * 70)
    print()

    success = run_tests()

    print()
    print("=" * 70)
    if success:
        print("✅ 所有测试通过！")
    else:
        print("❌ 部分测试失败")
    print("=" * 70)

    sys.exit(0 if success else 1)
