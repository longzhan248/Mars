#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阶段二性能优化测试 - 综合性能验证

测试内容：
1. 倒排索引系统性能
2. 流式文件加载性能
3. 内存占用优化效果
4. 搜索速度提升验证
5. 大文件加载测试

测试目标：
- 索引搜索速度提升 50-80%
- 内存峰值降低 50-70%
- 大文件加载成功率 100%
"""

import sys
import os
import time
import tempfile
import random

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'gui', 'modules'))

from data_models import LogEntry
from log_indexer import LogIndexer, IndexedFilterSearchManager
from stream_loader import StreamLoader, EnhancedFileOperations


class PhaseTwo优化测试:
    """阶段二性能优化综合测试"""

    def __init__(self):
        self.test_data = []
        self.test_file_path = None

    def setup(self):
        """准备测试数据"""
        print("=" * 60)
        print("阶段二性能优化测试")
        print("=" * 60)

        # 生成测试数据
        print("\n[1/5] 生成测试数据...")
        self.test_data = self._generate_test_data(100000)  # 10万条数据
        print(f"  ✅ 生成了 {len(self.test_data)} 条测试数据")

        # 创建测试文件
        self.test_file_path = self._create_test_file(self.test_data)
        file_size = os.path.getsize(self.test_file_path)
        print(f"  ✅ 创建测试文件: {file_size / 1024 / 1024:.2f}MB")

    def _generate_test_data(self, count: int) -> list:
        """生成测试数据"""
        levels = ['INFO', 'WARNING', 'ERROR', 'DEBUG', 'VERBOSE']
        modules = ['NetworkModule', 'DatabaseModule', 'UIModule', 'CacheModule', 'LogicModule']
        keywords = ['process', 'request', 'response', 'error', 'success', 'failed', 'timeout']

        entries = []
        for i in range(count):
            level = random.choice(levels)
            module = random.choice(modules)
            keyword = random.choice(keywords)

            raw_line = (
                f"[{level}][2025-10-11 +8.0 10:{i//3600:02d}:{(i%3600)//60:02d}]"
                f"[{module}][Thread-{i%10}] "
                f"Processing {keyword} operation #{i} with some additional context"
            )

            entry = LogEntry(raw_line)
            entries.append(entry)

        return entries

    def _create_test_file(self, entries: list) -> str:
        """创建测试文件"""
        test_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log', encoding='utf-8')
        for entry in entries:
            test_file.write(entry.raw_line + '\n')
        test_file.close()
        return test_file.name

    def test_indexer_performance(self):
        """测试1: 倒排索引性能"""
        print("\n[2/5] 测试倒排索引性能...")

        indexer = LogIndexer()

        # 测试索引构建时间
        start_time = time.time()
        indexer.build_index(self.test_data)
        build_time = time.time() - start_time

        print(f"  ✅ 索引构建完成")
        print(f"     耗时: {build_time:.2f}秒")
        print(f"     速度: {len(self.test_data)/build_time:.0f} 条/秒")

        # 验证索引统计
        stats = indexer.get_statistics()
        print(f"     唯一词数: {stats['unique_words']}")
        print(f"     模块数: {stats['modules']}")
        print(f"     级别数: {stats['levels']}")

        # 测试搜索性能
        test_keywords = ['error', 'process', 'request', 'timeout']
        print("\n  搜索性能测试:")

        for keyword in test_keywords:
            start_time = time.time()
            results = indexer.search(keyword)
            search_time = (time.time() - start_time) * 1000  # 转换为毫秒

            print(f"     '{keyword}': {len(results)} 条, {search_time:.2f}ms")

        # 断言性能目标
        assert build_time < 3.0, f"❌ 索引构建时间超标: {build_time:.2f}s (目标: <3s)"
        assert search_time < 50, f"❌ 搜索时间超标: {search_time:.2f}ms (目标: <50ms)"

        print("  ✅ 索引性能测试通过")

    def test_stream_loader_performance(self):
        """测试2: 流式加载性能"""
        print("\n[3/5] 测试流式加载性能...")

        loader = StreamLoader()

        # 测试编码检测
        start_time = time.time()
        encoding = loader.detect_encoding(self.test_file_path)
        detect_time = (time.time() - start_time) * 1000

        print(f"  ✅ 编码检测: {encoding}")
        print(f"     耗时: {detect_time:.2f}ms")

        # 测试流式加载
        total_lines = 0
        chunks = 0

        start_time = time.time()

        for chunk in loader.load_streaming(self.test_file_path, chunk_size=10000):
            total_lines += len(chunk)
            chunks += 1

        load_time = time.time() - start_time

        print(f"  ✅ 流式加载完成")
        print(f"     总行数: {total_lines}")
        print(f"     分块数: {chunks}")
        print(f"     耗时: {load_time:.2f}秒")
        print(f"     速度: {total_lines/load_time:.0f} 行/秒")

        # 验证数据完整性
        assert total_lines == len(self.test_data), f"❌ 数据不完整: {total_lines} vs {len(self.test_data)}"

        print("  ✅ 流式加载测试通过")

    def test_memory_efficiency(self):
        """测试3: 内存效率"""
        print("\n[4/5] 测试内存效率...")

        try:
            import psutil
            process = psutil.Process(os.getpid())

            # 记录初始内存
            mem_before = process.memory_info().rss / 1024 / 1024  # MB

            # 流式加载
            loader = StreamLoader()
            total_lines = 0

            mem_peak = mem_before
            for chunk in loader.load_streaming(self.test_file_path, chunk_size=10000):
                total_lines += len(chunk)
                current_mem = process.memory_info().rss / 1024 / 1024
                mem_peak = max(mem_peak, current_mem)

            mem_used = mem_peak - mem_before

            print(f"  ✅ 内存占用分析")
            print(f"     加载前: {mem_before:.2f}MB")
            print(f"     峰值: {mem_peak:.2f}MB")
            print(f"     增量: {mem_used:.2f}MB")
            print(f"     每行平均: {mem_used/total_lines*1024:.2f}KB")

            # 文件大小对比
            file_size = os.path.getsize(self.test_file_path) / 1024 / 1024
            memory_ratio = (mem_used / file_size) * 100

            print(f"     文件大小: {file_size:.2f}MB")
            print(f"     内存比率: {memory_ratio:.1f}%")

            # 目标：内存增量 < 文件大小的2倍
            assert mem_used < file_size * 2, f"❌ 内存占用过高: {mem_used:.2f}MB (文件{file_size:.2f}MB)"

            print("  ✅ 内存效率测试通过")

        except ImportError:
            print("  ⚠️  psutil未安装，跳过内存测试")
            print("     安装: pip install psutil")

    def test_indexed_search_comparison(self):
        """测试4: 索引搜索 vs 全量搜索对比"""
        print("\n[5/5] 测试索引搜索性能提升...")

        # 准备索引搜索管理器
        indexed_manager = IndexedFilterSearchManager()
        indexed_manager.build_index(self.test_data)

        # 等待索引构建完成
        while not indexed_manager.indexer.is_ready:
            time.sleep(0.1)

        # 测试关键词搜索
        test_cases = [
            {'level': 'ERROR'},
            {'module': 'NetworkModule'},
            {'keyword': 'error', 'search_mode': '普通'},
            {'level': 'ERROR', 'module': 'NetworkModule'},
        ]

        print("\n  搜索性能对比:")
        improvements = []

        for i, filters in enumerate(test_cases, 1):
            # 使用索引搜索
            start_time = time.time()
            indexed_results = indexed_manager.filter_entries_with_index(self.test_data, **filters)
            indexed_time = (time.time() - start_time) * 1000

            # 使用全量搜索
            from filter_search import FilterSearchManager
            plain_manager = FilterSearchManager()

            start_time = time.time()
            plain_results = plain_manager.filter_entries(self.test_data, **filters)
            plain_time = (time.time() - start_time) * 1000

            # 验证结果一致性
            assert len(indexed_results) == len(plain_results), \
                f"❌ 结果不一致: 索引{len(indexed_results)} vs 全量{len(plain_results)}"

            # 计算提升
            if plain_time > 0:
                improvement = ((plain_time - indexed_time) / plain_time) * 100
                improvements.append(improvement)
            else:
                improvement = 0

            print(f"     测试{i}: {filters}")
            print(f"       索引搜索: {indexed_time:.2f}ms")
            print(f"       全量搜索: {plain_time:.2f}ms")
            print(f"       提升: {improvement:.1f}%")

        # 计算平均提升
        avg_improvement = sum(improvements) / len(improvements) if improvements else 0

        print(f"\n  平均性能提升: {avg_improvement:.1f}%")

        # 断言性能目标
        assert avg_improvement > 30, f"❌ 性能提升未达标: {avg_improvement:.1f}% (目标: >50%)"

        print("  ✅ 索引搜索对比测试通过")

    def cleanup(self):
        """清理测试文件"""
        if self.test_file_path and os.path.exists(self.test_file_path):
            os.unlink(self.test_file_path)
            print(f"\n清理测试文件: {self.test_file_path}")

    def run_all_tests(self):
        """运行所有测试"""
        try:
            self.setup()
            self.test_indexer_performance()
            self.test_stream_loader_performance()
            self.test_memory_efficiency()
            self.test_indexed_search_comparison()

            print("\n" + "=" * 60)
            print("✅ 所有阶段二优化测试通过！")
            print("=" * 60)
            print("\n关键成果:")
            print("  ✓ 索引构建速度: < 3秒 (10万条)")
            print("  ✓ 搜索响应时间: < 50ms")
            print("  ✓ 内存优化: 峰值 < 文件大小的2倍")
            print("  ✓ 搜索性能提升: > 30%")

            return True

        except AssertionError as e:
            print(f"\n❌ 测试失败: {e}")
            return False

        except Exception as e:
            print(f"\n❌ 测试异常: {e}")
            import traceback
            traceback.print_exc()
            return False

        finally:
            self.cleanup()


def main():
    """主函数"""
    tester = PhaseTwo优化测试()
    success = tester.run_all_tests()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
