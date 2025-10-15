#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
解析缓存管理器测试套件

测试ParseCacheManager的所有功能。

运行方式：
    python -m pytest gui/modules/obfuscation/tests/test_parse_cache.py -v -s

或直接运行：
    python gui/modules/obfuscation/tests/test_parse_cache.py
"""

import os
import sys
import time
import tempfile
import shutil
import unittest
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from gui.modules.obfuscation.parse_cache_manager import ParseCacheManager, CacheEntry
from gui.modules.obfuscation.code_parser import CodeParser
from gui.modules.obfuscation.whitelist_manager import WhitelistManager


class MockParser:
    """模拟解析器，用于测试"""

    def __init__(self, parse_delay: float = 0.01):
        """
        初始化模拟解析器

        Args:
            parse_delay: 模拟解析延迟（秒）
        """
        self.parse_delay = parse_delay
        self.parse_count = 0

    def parse_file(self, file_path: str) -> dict:
        """
        模拟解析文件

        Args:
            file_path: 文件路径

        Returns:
            模拟的解析结果
        """
        # 模拟解析延迟
        time.sleep(self.parse_delay)

        self.parse_count += 1

        # 返回模拟的解析结果
        return {
            'classes': ['TestClass1', 'TestClass2'],
            'methods': ['method1', 'method2'],
            'properties': ['prop1', 'prop2'],
            'total_symbols': 6,
            'parse_time': self.parse_delay
        }


class TestParseCacheManager(unittest.TestCase):
    """解析缓存管理器测试套件"""

    @classmethod
    def setUpClass(cls):
        """设置测试环境"""
        print("\n" + "="*80)
        print("解析缓存管理器测试套件")
        print("="*80)

        # 创建临时测试目录
        cls.temp_dir = tempfile.mkdtemp(prefix="cache_test_")
        cls.cache_dir = os.path.join(cls.temp_dir, ".cache")
        print(f"\n临时目录: {cls.temp_dir}")
        print(f"缓存目录: {cls.cache_dir}")

        # 创建测试文件
        cls.test_file = os.path.join(cls.temp_dir, "TestFile.m")
        cls._create_test_file(cls.test_file, "original content")

    @classmethod
    def tearDownClass(cls):
        """清理测试环境"""
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)
        print(f"\n清理临时目录完成")

    @staticmethod
    def _create_test_file(file_path: str, content: str):
        """创建测试文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def test_01_cache_initialization(self):
        """测试1: 缓存初始化"""
        print("\n" + "="*80)
        print("测试1: 缓存初始化")
        print("="*80)

        cache = ParseCacheManager(cache_dir=self.cache_dir)

        # 验证缓存目录创建
        assert os.path.exists(self.cache_dir), "缓存目录应该被创建"
        assert os.path.exists(os.path.join(self.cache_dir, "entries")), "entries目录应该被创建"
        assert os.path.exists(os.path.join(self.cache_dir, "metadata")), "metadata目录应该被创建"

        # 验证初始状态
        assert cache.cache_hits == 0, "初始命中数应为0"
        assert cache.cache_misses == 0, "初始未命中数应为0"
        assert len(cache.memory_cache) == 0, "初始内存缓存应为空"

        print("✅ 缓存初始化测试通过")

    def test_02_first_parse_cache_miss(self):
        """测试2: 首次解析（缓存未命中）"""
        print("\n" + "="*80)
        print("测试2: 首次解析（缓存未命中）")
        print("="*80)

        cache = ParseCacheManager(cache_dir=self.cache_dir)
        parser = MockParser(parse_delay=0.01)

        # 首次解析
        start_time = time.time()
        result = cache.get_or_parse(self.test_file, parser)
        elapsed = time.time() - start_time

        # 验证解析结果
        assert 'classes' in result, "解析结果应包含classes"
        assert 'methods' in result, "解析结果应包含methods"
        assert result['total_symbols'] == 6, "符号总数应为6"

        # 验证缓存统计
        assert cache.cache_misses == 1, "缓存未命中数应为1"
        assert cache.cache_hits == 0, "缓存命中数应为0"
        assert parser.parse_count == 1, "解析器应被调用1次"

        # 验证缓存保存
        assert len(cache.memory_cache) == 1, "内存缓存应有1个条目"
        assert self.test_file in cache.memory_cache, "测试文件应在缓存中"

        print(f"✅ 首次解析: {elapsed*1000:.1f}毫秒")
        print(f"   解析器调用: {parser.parse_count}次")
        print(f"   缓存未命中: {cache.cache_misses}")

    def test_03_second_parse_cache_hit(self):
        """测试3: 第二次解析（缓存命中）"""
        print("\n" + "="*80)
        print("测试3: 第二次解析（缓存命中）")
        print("="*80)

        # 创建新的测试文件以避免与其他测试冲突
        test_file = os.path.join(self.temp_dir, "CacheHitTest.m")
        self._create_test_file(test_file, "cache hit test content")

        cache = ParseCacheManager(cache_dir=self.cache_dir)
        parser = MockParser(parse_delay=0.01)

        # 首次解析
        result1 = cache.get_or_parse(test_file, parser)
        parse1_count = parser.parse_count

        # 第二次解析（应从缓存读取）
        start_time = time.time()
        result2 = cache.get_or_parse(test_file, parser)
        elapsed = time.time() - start_time

        # 验证结果一致
        assert result1 == result2, "两次解析结果应一致"

        # 验证缓存命中
        assert cache.cache_hits == 1, "缓存命中数应为1"
        assert parser.parse_count == parse1_count, "解析器不应被再次调用"

        # 验证速度提升
        speedup = 0.01 / elapsed if elapsed > 0 else float('inf')

        print(f"✅ 第二次解析（缓存）: {elapsed*1000:.3f}毫秒")
        print(f"   解析器调用: {parser.parse_count}次（未增加）")
        print(f"   缓存命中: {cache.cache_hits}")
        print(f"   加速比: {speedup:.1f}x")

        assert speedup > 10, f"缓存应比解析快至少10倍，实际: {speedup:.1f}x"

    def test_04_file_modification_invalidates_cache(self):
        """测试4: 文件修改导致缓存失效"""
        print("\n" + "="*80)
        print("测试4: 文件修改导致缓存失效")
        print("="*80)

        # 创建新的测试文件
        test_file = os.path.join(self.temp_dir, "ModifyTest.m")
        self._create_test_file(test_file, "original content")

        cache = ParseCacheManager(cache_dir=self.cache_dir)
        parser = MockParser(parse_delay=0.01)

        # 首次解析
        result1 = cache.get_or_parse(test_file, parser)
        parse1_count = parser.parse_count

        # 修改文件内容
        time.sleep(0.1)  # 确保修改时间不同
        self._create_test_file(test_file, "modified content")

        # 再次解析（缓存应失效）
        result2 = cache.get_or_parse(test_file, parser)

        # 验证缓存失效
        assert parser.parse_count == parse1_count + 1, "文件修改后应重新解析"
        assert cache.cache_misses == 2, "缓存未命中数应为2"

        print(f"✅ 文件修改检测正常")
        print(f"   第一次解析: {parse1_count}次")
        print(f"   文件修改后重新解析: {parser.parse_count}次")

    def test_05_disk_cache_persistence(self):
        """测试5: 磁盘缓存持久化"""
        print("\n" + "="*80)
        print("测试5: 磁盘缓存持久化")
        print("="*80)

        # 第一个缓存实例
        cache1 = ParseCacheManager(cache_dir=self.cache_dir)
        parser1 = MockParser(parse_delay=0.01)

        result1 = cache1.get_or_parse(self.test_file, parser1)
        parse1_count = parser1.parse_count

        # 销毁第一个实例（清空内存缓存）
        del cache1

        # 创建第二个缓存实例（应从磁盘加载）
        cache2 = ParseCacheManager(cache_dir=self.cache_dir)
        parser2 = MockParser(parse_delay=0.01)

        result2 = cache2.get_or_parse(self.test_file, parser2)

        # 验证从磁盘加载
        assert result1 == result2, "从磁盘加载的结果应一致"
        assert parser2.parse_count == 0, "不应重新解析（从磁盘加载）"
        assert cache2.cache_hits == 1, "应从磁盘缓存命中"

        print(f"✅ 磁盘缓存持久化正常")
        print(f"   第一个实例解析: {parse1_count}次")
        print(f"   第二个实例解析: {parser2.parse_count}次（从磁盘加载）")

    def test_06_batch_parsing(self):
        """测试6: 批量解析"""
        print("\n" + "="*80)
        print("测试6: 批量解析")
        print("="*80)

        # 创建多个测试文件
        test_files = []
        for i in range(10):
            file_path = os.path.join(self.temp_dir, f"TestFile{i}.m")
            self._create_test_file(file_path, f"test content {i}")
            test_files.append(file_path)

        cache = ParseCacheManager(cache_dir=self.cache_dir)
        parser = MockParser(parse_delay=0.01)

        # 批量解析
        def progress_callback(progress, message):
            print(f"  [{progress*100:.0f}%] {message}")

        results = cache.batch_get_or_parse(test_files, parser, callback=progress_callback)

        # 验证结果
        assert len(results) == 10, "应解析10个文件"
        assert cache.cache_misses == 10, "首次解析应全部未命中"
        assert parser.parse_count == 10, "解析器应被调用10次"

        # 第二次批量解析（应全部命中）
        print("\n第二次批量解析（缓存）:")
        results2 = cache.batch_get_or_parse(test_files, parser, callback=progress_callback)

        assert cache.cache_hits == 10, "第二次应全部命中"
        assert parser.parse_count == 10, "解析器不应再被调用"

        print(f"\n✅ 批量解析测试通过")
        print(f"   首次解析: {cache.cache_misses}次")
        print(f"   缓存命中: {cache.cache_hits}次")

    def test_07_cache_statistics(self):
        """测试7: 缓存统计"""
        print("\n" + "="*80)
        print("测试7: 缓存统计")
        print("="*80)

        # 创建新的测试文件
        test_file = os.path.join(self.temp_dir, "StatsTest.m")
        self._create_test_file(test_file, "stats test content")

        cache = ParseCacheManager(cache_dir=self.cache_dir)
        parser = MockParser(parse_delay=0.01)

        # 解析文件多次
        for i in range(5):
            cache.get_or_parse(test_file, parser)

        # 获取统计信息
        stats = cache.get_statistics()

        print(f"\n统计信息:")
        print(f"  缓存命中: {stats['cache_hits']}")
        print(f"  缓存未命中: {stats['cache_misses']}")
        print(f"  命中率: {stats['hit_rate']*100:.1f}%")
        print(f"  内存缓存: {stats['memory_cache_size']}个条目")
        print(f"  解析次数: {stats['parse_count']}")
        print(f"  节省时间: {stats['total_parse_time_saved']:.3f}秒")
        print(f"  有效加速: {stats['effective_speedup']:.1f}x")

        # 验证统计
        assert stats['cache_hits'] == 4, "应有4次缓存命中"
        assert stats['cache_misses'] == 1, "应有1次缓存未命中"
        assert stats['hit_rate'] == 0.8, "命中率应为80%"

        # 打印统计报告
        cache.print_statistics()

        print(f"✅ 缓存统计测试通过")

    def test_08_force_parse(self):
        """测试8: 强制重新解析"""
        print("\n" + "="*80)
        print("测试8: 强制重新解析")
        print("="*80)

        cache = ParseCacheManager(cache_dir=self.cache_dir)
        parser = MockParser(parse_delay=0.01)

        # 首次解析
        result1 = cache.get_or_parse(self.test_file, parser)
        parse1_count = parser.parse_count

        # 强制重新解析
        result2 = cache.get_or_parse(self.test_file, parser, force_parse=True)

        # 验证强制解析
        assert parser.parse_count == parse1_count + 1, "强制解析应调用解析器"
        assert result1 == result2, "结果应一致"

        print(f"✅ 强制重新解析测试通过")
        print(f"   首次解析: 1次")
        print(f"   强制解析: 1次")

    def test_09_cache_invalidation(self):
        """测试9: 缓存失效"""
        print("\n" + "="*80)
        print("测试9: 缓存失效")
        print("="*80)

        cache = ParseCacheManager(cache_dir=self.cache_dir)
        parser = MockParser(parse_delay=0.01)

        # 解析文件
        result1 = cache.get_or_parse(self.test_file, parser)

        # 验证缓存存在
        assert self.test_file in cache.memory_cache, "缓存应存在"

        # 使缓存失效
        cache.invalidate(self.test_file)

        # 验证缓存已删除
        assert self.test_file not in cache.memory_cache, "缓存应被删除"

        # 重新解析（应重新调用解析器）
        parse1_count = parser.parse_count
        result2 = cache.get_or_parse(self.test_file, parser)

        assert parser.parse_count == parse1_count + 1, "应重新解析"

        print(f"✅ 缓存失效测试通过")

    def test_10_memory_cache_eviction(self):
        """测试10: 内存缓存淘汰"""
        print("\n" + "="*80)
        print("测试10: 内存缓存淘汰（LRU）")
        print("="*80)

        # 创建小容量缓存
        cache = ParseCacheManager(
            cache_dir=self.cache_dir,
            max_memory_cache=5  # 最多5个条目
        )
        parser = MockParser(parse_delay=0.01)

        # 创建10个文件
        files = []
        for i in range(10):
            file_path = os.path.join(self.temp_dir, f"EvictTest{i}.m")
            self._create_test_file(file_path, f"content {i}")
            files.append(file_path)

        # 解析所有文件
        for file_path in files:
            cache.get_or_parse(file_path, parser)

        # 验证内存缓存大小
        assert len(cache.memory_cache) <= 5, f"内存缓存应≤5个，实际: {len(cache.memory_cache)}"

        print(f"✅ 内存缓存淘汰测试通过")
        print(f"   解析文件: 10个")
        print(f"   内存缓存: {len(cache.memory_cache)}个（LRU淘汰）")

    def test_11_real_parser_integration(self):
        """测试11: 真实解析器集成测试"""
        print("\n" + "="*80)
        print("测试11: 真实解析器集成测试")
        print("="*80)

        # 创建真实的ObjC文件
        objc_file = os.path.join(self.temp_dir, "RealTest.m")
        objc_content = """//
// RealTest.m
// Test Project
//

#import "RealTest.h"

@implementation RealTest

- (void)testMethod {
    NSLog(@"Test");
}

@end
"""
        self._create_test_file(objc_file, objc_content)

        # 使用真实解析器
        cache = ParseCacheManager(cache_dir=self.cache_dir)
        whitelist = WhitelistManager()
        parser = CodeParser(whitelist)

        # 首次解析
        start_time = time.time()
        result1 = cache.get_or_parse(objc_file, parser)
        time1 = time.time() - start_time

        # 第二次解析（缓存）
        start_time = time.time()
        result2 = cache.get_or_parse(objc_file, parser)
        time2 = time.time() - start_time

        # 验证结果
        assert result1 == result2, "两次解析结果应一致"
        # CodeParser返回的是ParsedFile对象，不是字典
        assert hasattr(result1, 'classes') or isinstance(result1, dict), "应包含解析结果"

        # 计算加速比
        speedup = time1 / time2 if time2 > 0 else float('inf')

        print(f"✅ 真实解析器集成测试通过")
        print(f"   首次解析: {time1*1000:.3f}毫秒")
        print(f"   缓存解析: {time2*1000:.3f}毫秒")
        print(f"   加速比: {speedup:.1f}x")

        assert speedup > 5, f"缓存应至少快5倍，实际: {speedup:.1f}x"


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*80)
    print("运行解析缓存管理器测试套件")
    print("="*80)

    # 运行测试
    suite = unittest.TestLoader().loadTestsFromTestCase(TestParseCacheManager)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 返回退出码
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    exit_code = run_all_tests()
    sys.exit(exit_code)
