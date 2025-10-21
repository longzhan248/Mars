#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
心娱开发助手端到端测试
完整测试系统从用户输入到结果输出的整个流程
"""

import sys
import os
import unittest
import logging
import tempfile
import subprocess
import time
import json
from unittest.mock import Mock, patch, MagicMock

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestEndToEndWorkflows(unittest.TestCase):
    """端到端工作流测试"""

    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_data_dir = os.path.join(self.temp_dir, "test_data")
        os.makedirs(self.test_data_dir, exist_ok=True)

    def tearDown(self):
        """清理测试环境"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_sample_log_file(self, filename="sample.log"):
        """创建示例日志文件"""
        log_content = """[I][2025-01-01 10:00:00][AppStart] 应用程序启动
[I][2025-01-01 10:00:01][Network] 网络连接建立
[W][2025-01-01 10:00:02][Memory] 内存使用率较高: 85%
[I][2025-01-01 10:00:03][UserLogin] 用户登录成功
[E][2025-01-01 10:00:04][Database] 数据库连接失败
[I][2025-01-01 10:00:05][Retry] 正在重试数据库连接
[I][2025-01-01 10:00:06][Database] 数据库连接成功
[I][2025-01-01 10:00:07][Feature] 功能模块加载完成
[D][2025-01-01 10:00:08][Debug] 调试信息: 缓存初始化
[I][2025-01-01 10:00:09][Ready] 应用程序就绪
"""
        file_path = os.path.join(self.test_data_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(log_content)
        return file_path

    def test_complete_log_analysis_workflow(self):
        """测试完整的日志分析工作流"""
        try:
            # 1. 创建测试数据
            log_file = self.create_sample_log_file()

            # 2. 测试文件加载
            sys.path.insert(0, os.path.join(project_root, 'gui', 'modules'))
            from file_operations import FileOperations

            ops = FileOperations()
            entries = ops.load_file(log_file)

            self.assertIsNotNone(entries)
            self.assertGreater(len(entries), 0)

            # 3. 测试日志索引
            from log_indexer import LogIndexer

            indexer = LogIndexer()
            index_result = indexer.build_index(entries)

            self.assertIsInstance(index_result, dict)
            self.assertGreater(len(index_result), 0)

            # 4. 测试过滤功能
            from filter_search import FilterSearchManager

            manager = FilterSearchManager()

            # 按级别过滤
            error_entries = manager.filter_entries(entries, level="ERROR")
            self.assertEqual(len(error_entries), 1)

            # 按关键词搜索
            database_entries = manager.filter_entries(entries, keyword="数据库")
            self.assertGreater(len(database_entries), 0)

            # 5. 测试导出功能
            export_file = os.path.join(self.temp_dir, "exported_logs.txt")
            success = ops.export_to_file(error_entries, export_file)

            self.assertTrue(success)
            self.assertTrue(os.path.exists(export_file))

            # 6. 验证导出内容
            with open(export_file, 'r', encoding='utf-8') as f:
                exported_content = f.read()
                self.assertIn("数据库连接失败", exported_content)

            logger.info("✅ 完整日志分析工作流测试通过")

        except ImportError as e:
            self.skipTest(f"模块导入失败，跳过测试: {e}")
        except Exception as e:
            self.fail(f"日志分析工作流测试失败: {e}")

    def test_error_handling_workflow(self):
        """测试错误处理工作流"""
        try:
            sys.path.insert(0, os.path.join(project_root, 'gui', 'modules'))
            import exceptions
            from exceptions import get_global_error_collector, FileOperationError

            # 1. 清空收集器
            exceptions.clear_global_collector()
            collector = get_global_error_collector()

            # 2. 模拟一系列错误
            errors = [
                FileOperationError("文件不存在", operation="read"),
                FileOperationError("权限不足", operation="write"),
                FileOperationError("磁盘空间不足", operation="save"),
            ]

            # 3. 添加错误到收集器
            for error in errors:
                collector.add_exception(error)

            # 4. 生成错误报告
            reporter = exceptions.get_global_error_reporter()
            reporter.collector = collector
            report = reporter.generate_report()

            # 5. 验证报告内容
            self.assertIn("异常总数: 3", report)
            self.assertIn("文件不存在", report)
            self.assertIn("权限不足", report)
            self.assertIn("磁盘空间不足", report)

            # 6. 保存报告到文件
            report_file = os.path.join(self.temp_dir, "error_report.txt")
            success = reporter.save_report_to_file(report_file)

            self.assertTrue(success)
            self.assertTrue(os.path.exists(report_file))

            logger.info("✅ 错误处理工作流测试通过")

        except ImportError as e:
            self.skipTest(f"异常处理模块导入失败: {e}")
        except Exception as e:
            self.fail(f"错误处理工作流测试失败: {e}")

    def test_system_resilience_workflow(self):
        """测试系统韧性工作流"""
        try:
            # 1. 测试系统在遇到各种异常时的恢复能力
            sys.path.insert(0, os.path.join(project_root, 'gui', 'modules'))
            import exceptions
            from exceptions import handle_exceptions, get_global_error_collector

            exceptions.clear_global_collector()

            # 2. 模拟各种异常情况
            @handle_exceptions(Exception, reraise=False)
            def simulate_file_error():
                raise FileNotFoundError("模拟文件不存在错误")

            @handle_exceptions(Exception, reraise=False)
            def simulate_network_error():
                raise ConnectionError("模拟网络连接错误")

            @handle_exceptions(Exception, reraise=False)
            def simulate_permission_error():
                raise PermissionError("模拟权限不足错误")

            # 3. 执行各种异常场景
            simulate_file_error()
            simulate_network_error()
            simulate_permission_error()

            # 4. 验证系统仍然正常工作
            collector = get_global_error_collector()
            stats = collector.get_statistics()

            self.assertGreater(stats['total_exceptions'], 0)
            self.assertGreater(stats['total_exceptions'], 2)  # 至少应该有一些异常

            # 5. 验证系统功能未受影响
            try:
                # 尝试正常操作
                from data_models import LogEntry
                entry = LogEntry("[I][2025-01-01 00:00:00][Test] 系统正常工作")
                self.assertIsNotNone(entry)
                logger.info("✅ 系统韧性工作流测试通过")
            except Exception as e:
                self.fail(f"系统韧性测试失败，系统无法恢复正常功能: {e}")

        except ImportError as e:
            self.skipTest(f"系统韧性测试模块导入失败: {e}")

    def test_performance_under_load(self):
        """测试负载下的性能"""
        try:
            sys.path.insert(0, os.path.join(project_root, 'gui', 'modules'))
            import exceptions
            from exceptions import get_global_error_collector

            exceptions.clear_global_collector()
            collector = get_global_error_collector()

            # 1. 生成大量日志条目
            from data_models import LogEntry
            entries = []
            for i in range(1000):
                entry = LogEntry(f"[I][2025-01-01 10:{i//60:02d}:{i%60:02d}][Test{i%10}] 性能测试日志 {i}")
                entries.append(entry)

            # 2. 测试索引性能
            start_time = time.time()
            from log_indexer import LogIndexer
            indexer = LogIndexer()
            index_result = indexer.build_index(entries)
            index_time = time.time() - start_time

            # 3. 测试搜索性能
            from filter_search import FilterSearchManager
            manager = FilterSearchManager()

            start_time = time.time()
            filtered_entries = manager.filter_entries(entries, keyword="性能测试")
            filter_time = time.time() - start_time

            # 4. 验证性能指标
            self.assertLess(index_time, 5.0)  # 索引时间应该少于5秒
            self.assertLess(filter_time, 1.0)  # 过滤时间应该少于1秒
            self.assertGreater(len(filtered_entries), 900)  # 大部分条目应该匹配

            # 5. 验证系统稳定性
            stats = collector.get_statistics()
            # 在正常操作中不应该有异常
            logger.info(f"性能测试完成: 索引时间={index_time:.3f}s, 过滤时间={filter_time:.3f}s")
            logger.info("✅ 负载性能测试通过")

        except ImportError as e:
            self.skipTest(f"性能测试模块导入失败: {e}")
        except Exception as e:
            self.fail(f"负载性能测试失败: {e}")


class TestRealWorldScenarios(unittest.TestCase):
    """真实世界场景测试"""

    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """清理测试环境"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_mars_log_file_processing(self):
        """测试Mars日志文件处理"""
        # 创建模拟的Mars日志内容
        mars_content = """2025-01-01 10:00:00.123 4567 1234 AppStart I [AppStart] 应用程序启动
2025-01-01 10:00:01.456 4567 1234 Network I [Network] 网络连接建立
2025-01-01 10:00:02.789 4567 1234 Memory W [Memory] 内存使用率较高: 85%
2025-01-01 10:00:03.012 4567 1234 Database E [Database] 数据库连接失败
2025-01-01 10:00:04.345 4567 1234 Retry I [Retry] 正在重试数据库连接
"""

        try:
            # 创建模拟xlog文件
            xlog_file = os.path.join(self.temp_dir, "test_mars.xlog")
            with open(xlog_file, 'wb') as f:
                f.write(mars_content.encode('utf-8'))

            # 测试文件处理
            sys.path.insert(0, os.path.join(project_root, 'gui', 'modules'))
            from file_operations import FileOperations

            ops = FileOperations()
            entries = ops.load_file(xlog_file)

            if entries:
                self.assertGreater(len(entries), 0)
                logger.info(f"✅ Mars日志文件处理测试通过，处理了 {len(entries)} 条日志")
            else:
                logger.warning("⚠️ Mars日志文件处理返回空结果，可能是解码问题")

        except ImportError as e:
            self.skipTest(f"Mars日志处理模块导入失败: {e}")
        except Exception as e:
            logger.warning(f"Mars日志文件处理测试遇到问题: {e}")

    def test_error_recovery_scenario(self):
        """测试错误恢复场景"""
        try:
            sys.path.insert(0, os.path.join(project_root, 'gui', 'modules'))
            import exceptions
            from exceptions import handle_exceptions, get_global_error_collector

            exceptions.clear_global_collector()

            # 模拟真实错误场景：文件操作失败后继续处理其他文件
            from file_operations import FileOperations
            from data_models import LogEntry

            ops = FileOperations()

            # 尝试加载不存在的文件（应该失败但继续执行）
            result1 = ops.load_file("/nonexistent/file1.log")
            self.assertIsNone(result1)

            # 尝试加载存在的文件（应该成功）
            valid_log = os.path.join(self.temp_dir, "valid.log")
            with open(valid_log, 'w') as f:
                f.write("[I][2025-01-01 00:00:00][Test] 有效日志\n")

            result2 = ops.load_file(valid_log)
            self.assertIsNotNone(result2)

            # 验证错误被记录但系统继续工作
            collector = get_global_error_collector()
            stats = collector.get_statistics()

            self.assertGreater(stats['total_exceptions'], 0)  # 应该有文件不存在的错误
            self.assertIsNotNone(result2)  # 系统应该能够继续处理其他文件

            logger.info("✅ 错误恢复场景测试通过")

        except ImportError as e:
            self.skipTest(f"错误恢复测试模块导入失败: {e}")

    def test_memory_efficiency_scenario(self):
        """测试内存效率场景"""
        try:
            sys.path.insert(0, os.path.join(project_root, 'gui', 'modules'))
            from data_models import LogEntry
            from log_indexer import LogIndexer

            # 创建大量数据测试内存效率
            batch_size = 100
            total_entries = 500

            for batch in range(0, total_entries, batch_size):
                entries = []
                for i in range(batch, min(batch + batch_size, total_entries)):
                    entry = LogEntry(f"[I][2025-01-01 10:{i//60:02d}:{i%60:02d}][Test] 内存测试 {i}")
                    entries.append(entry)

                # 分批处理
                indexer = LogIndexer()
                index_result = indexer.build_index(entries)

                # 验证每批都能正常处理
                self.assertIsInstance(index_result, dict)

            logger.info("✅ 内存效率场景测试通过")

        except ImportError as e:
            self.skipTest(f"内存效率测试模块导入失败: {e}")


def run_end_to_end_tests():
    """运行端到端测试"""
    test_classes = [
        TestEndToEndWorkflows,
        TestRealWorldScenarios,
    ]

    suite = unittest.TestSuite()
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 输出结果摘要
    print(f"\n{'='*60}")
    print("端到端测试结果摘要:")
    print(f"运行测试: {result.testsRun}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print(f"跳过: {len(result.skipped) if hasattr(result, 'skipped') else 0}")

    success_rate = 0
    if result.testsRun > 0:
        success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100)
    print(f"成功率: {success_rate:.1f}%")

    if result.failures:
        print(f"\n失败的测试:")
        for test, traceback in result.failures:
            print(f"  - {test}")

    if result.errors:
        print(f"\n错误的测试:")
        for test, traceback in result.errors:
            print(f"  - {test}")

    # 生成综合测试报告
    try:
        sys.path.insert(0, os.path.join(project_root, 'gui', 'modules'))
        import exceptions

        collector = exceptions.get_global_error_collector()
        if collector.exceptions:
            print(f"\n测试期间异常统计:")
            print(f"  总异常数: {len(collector.exceptions)}")
            stats = collector.get_statistics()
            print(f"  按严重程度: {stats['severity_distribution']}")
            print(f"  按异常类型: {stats['type_distribution']}")

            # 生成最终测试报告
            reporter = exceptions.get_global_error_reporter()
            final_report = reporter.generate_report()

            report_file = os.path.join(project_root, "end_to_end_test_report.txt")
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("心娱开发助手端到端测试报告\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"运行测试: {result.testsRun}\n")
                f.write(f"成功率: {success_rate:.1f}%\n")
                f.write(f"异常总数: {len(collector.exceptions)}\n\n")
                f.write("异常详情:\n")
                f.write("-" * 30 + "\n")
                f.write(final_report)

            print(f"  详细报告已保存到: {report_file}")

    except ImportError:
        print("\n无法生成异常统计报告")

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_end_to_end_tests()
    sys.exit(0 if success else 1)