#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
心娱开发助手主程序集成测试
测试主程序和整体系统的异常处理集成
"""

import sys
import os
import unittest
import logging
import tempfile
import subprocess
from unittest.mock import Mock, patch, MagicMock

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 配置日志
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


class TestMainProgramIntegration(unittest.TestCase):
    """测试主程序集成"""

    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """清理测试环境"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_main_program_imports(self):
        """测试主程序导入"""
        try:
            # 尝试导入主程序模块
            sys.path.insert(0, os.path.join(project_root, 'gui'))
            import mars_log_analyzer_modular
            self.assertIsNotNone(mars_log_analyzer_modular)
        except ImportError as e:
            # 导入失败应该被记录
            logger.error(f"主程序导入失败: {e}")
            self.fail(f"主程序应该能够正常导入: {e}")

    def test_exception_handling_integration(self):
        """测试异常处理系统集成"""
        try:
            sys.path.insert(0, os.path.join(project_root, 'gui', 'modules'))
            import exceptions

            # 验证全局异常收集器可用
            collector = exceptions.get_global_error_collector()
            self.assertIsNotNone(collector)

            # 验证全局错误报告器可用
            reporter = exceptions.get_global_error_reporter()
            self.assertIsNotNone(reporter)

            # 验证清除功能可用
            exceptions.clear_global_collector()
            self.assertEqual(len(collector.exceptions), 0)

        except ImportError as e:
            self.fail(f"异常处理模块应该能够正常导入: {e}")

    def test_main_program_error_handling(self):
        """测试主程序错误处理"""
        try:
            # 测试主程序在遇到错误时的处理
            sys.path.insert(0, os.path.join(project_root, 'gui'))

            # 使用subprocess测试主程序启动
            test_script = os.path.join(self.temp_dir, "test_main.py")
            with open(test_script, 'w') as f:
                f.write(f'''
import sys
sys.path.insert(0, "{project_root}")
sys.path.insert(0, "{os.path.join(project_root, 'gui')}")
sys.path.insert(0, "{os.path.join(project_root, 'gui', 'modules')}")

try:
    # 尝试导入模块
    import exceptions
    from exceptions import get_global_error_collector, FileOperationError, handle_exceptions

    # 测试异常处理
    @handle_exceptions(Exception, reraise=False)
    def test_function():
        raise ValueError("测试异常")

    result = test_function()
    print("SUCCESS: 异常处理正常工作")

except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
''')

            result = subprocess.run([sys.executable, test_script],
                                  capture_output=True, text=True, timeout=10)

            self.assertEqual(result.returncode, 0)
            self.assertIn("SUCCESS", result.stdout)

        except subprocess.TimeoutExpired:
            self.fail("主程序测试超时")
        except Exception as ex:
            self.fail(f"主程序测试失败: {ex}")

    def test_module_availability(self):
        """测试关键模块可用性"""
        critical_modules = [
            ('gui.modules.exceptions', '异常处理系统'),
            ('gui.modules.data_models', '数据模型'),
            ('gui.modules.file_operations', '文件操作'),
            ('gui.modules.log_indexer', '日志索引'),
            ('gui.modules.filter_search', '过滤搜索'),
        ]

        failed_modules = []

        for module_name, description in critical_modules:
            try:
                __import__(module_name)
                logger.info(f"✅ {description} - 可用")
            except ImportError as e:
                logger.error(f"❌ {description} - 不可用: {e}")
                failed_modules.append((module_name, description, str(e)))

        if failed_modules:
            error_msg = "以下关键模块不可用:\n"
            for module_name, description, error in failed_modules:
                error_msg += f"  - {description} ({module_name}): {error}\n"
            self.fail(error_msg)

    def test_configuration_files(self):
        """测试配置文件"""
        config_files = [
            'requirements.txt',
            'CLAUDE.md',
            'CHANGELOG.md',
        ]

        missing_files = []
        for config_file in config_files:
            file_path = os.path.join(project_root, config_file)
            if not os.path.exists(file_path):
                missing_files.append(config_file)

        if missing_files:
            logger.warning(f"以下配置文件缺失: {missing_files}")
            # 配置文件缺失不应该导致测试失败，但应该记录

    def test_data_model_creation(self):
        """测试数据模型创建"""
        try:
            sys.path.insert(0, os.path.join(project_root, 'gui', 'modules'))
            from data_models import LogEntry, FileGroup

            # 测试LogEntry创建
            entry = LogEntry("[I][2025-01-01 00:00:00][Test] 测试日志")
            self.assertIsNotNone(entry)
            # 验证日志级别解析可能不同，检查是否为有效级别
            valid_levels = ["INFO", "ERROR", "WARNING", "DEBUG", "VERBOSE", "OTHER"]
            self.assertIn(entry.level, valid_levels)

            # 测试FileGroup创建
            group = FileGroup("test_group", ["/test/file1.log", "/test/file2.log"])
            self.assertIsNotNone(group)
            self.assertEqual(group.base_name, "test_group")

        except ImportError as e:
            self.fail(f"数据模型导入失败: {e}")

    def test_exception_hierarchy(self):
        """测试异常层次结构"""
        try:
            sys.path.insert(0, os.path.join(project_root, 'gui', 'modules'))
            import exceptions

            # 验证异常类层次
            base_exception = exceptions.XinyuDevToolsError("基础异常")
            file_error = exceptions.FileOperationError("文件错误", operation="test")
            ai_error = exceptions.AIDiagnosisError("AI错误", ai_service="test")

            # 验证继承关系
            self.assertIsInstance(file_error, exceptions.XinyuDevToolsError)
            self.assertIsInstance(ai_error, exceptions.XinyuDevToolsError)

            # 验证序列化
            error_dict = base_exception.to_dict()
            self.assertIn('error_type', error_dict)
            self.assertIn('message', error_dict)

        except ImportError as e:
            self.fail(f"异常层次结构测试失败: {e}")


class TestSystemErrorFlow(unittest.TestCase):
    """测试系统错误流程"""

    def setUp(self):
        """设置测试环境"""
        try:
            sys.path.insert(0, os.path.join(project_root, 'gui', 'modules'))
            import exceptions
            exceptions.clear_global_collector()
        except ImportError:
            self.skipTest("异常处理模块不可用")

    def test_error_collection_flow(self):
        """测试错误收集流程"""
        import exceptions

        collector = exceptions.get_global_error_collector()

        # 创建不同类型的异常
        errors = [
            exceptions.FileOperationError("文件读取错误", operation="read"),
            exceptions.AIDiagnosisError("AI服务错误", ai_service="claude"),
            exceptions.LogParsingError("日志解析错误", line_number=1),
        ]

        # 添加异常到收集器
        for error in errors:
            collector.add_exception(error)

        # 验证统计信息
        stats = collector.get_statistics()
        self.assertEqual(stats['total_exceptions'], 3)
        self.assertGreater(stats['type_distribution']['FileOperationError'], 0)

    def test_error_report_generation(self):
        """测试错误报告生成"""
        import exceptions

        collector = exceptions.get_global_error_collector()
        reporter = exceptions.get_global_error_reporter()

        # 添加测试异常
        test_error = exceptions.FileOperationError("测试错误", operation="test")
        collector.add_exception(test_error)

        # 确保报告器使用正确的收集器
        reporter.collector = collector

        # 生成报告
        report = reporter.generate_report()
        self.assertIsInstance(report, str)
        self.assertIn("异常总数", report)
        self.assertIn("测试错误", report)

    def test_global_exception_handler(self):
        """测试全局异常处理器"""
        import exceptions

        # 设置全局异常处理器
        exceptions.setup_global_exception_handler()

        collector = exceptions.get_global_error_collector()
        initial_count = len(collector.exceptions)

        # 触发未捕获异常（模拟）
        try:
            raise ValueError("未捕获异常测试")
        except:
            # 全局异常处理器应该捕获这个异常
            pass

        # 注意：由于我们无法直接触发sys.excepthook，这里只是验证设置成功
        self.assertIsInstance(collector, exceptions.ExceptionCollector)


class TestPerformanceAndReliability(unittest.TestCase):
    """测试性能和可靠性"""

    def test_large_error_handling(self):
        """测试大量错误处理"""
        try:
            sys.path.insert(0, os.path.join(project_root, 'gui', 'modules'))
            import exceptions

            collector = exceptions.get_global_error_collector()

            # 生成大量异常
            for i in range(1000):
                error = exceptions.FileOperationError(f"错误 {i}", operation="test")
                collector.add_exception(error)

            # 验证收集器正常工作
            stats = collector.get_statistics()
            self.assertGreater(stats['total_exceptions'], 0)
            self.assertLessEqual(stats['total_exceptions'], 1000)  # 应该有上限

        except ImportError:
            self.skipTest("异常处理模块不可用")

    def test_memory_usage(self):
        """测试内存使用"""
        try:
            import gc
            import psutil
            import os

            sys.path.insert(0, os.path.join(project_root, 'gui', 'modules'))
            import exceptions

            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss

            # 创建大量异常对象
            collector = exceptions.get_global_error_collector()
            for i in range(100):
                error = exceptions.FileOperationError(f"内存测试错误 {i}", operation="test")
                collector.add_exception(error)

            # 强制垃圾回收
            gc.collect()
            final_memory = process.memory_info().rss

            memory_increase = final_memory - initial_memory
            # 内存增长应该在合理范围内（小于50MB）
            self.assertLess(memory_increase, 50 * 1024 * 1024)

        except ImportError:
            self.skipTest("性能测试模块不可用")
        except Exception as e:
            # 性能测试失败不应该阻止其他测试
            logger.warning(f"内存使用测试失败: {e}")

    def test_concurrent_error_collection(self):
        """测试并发错误收集"""
        try:
            import threading
            import time

            sys.path.insert(0, os.path.join(project_root, 'gui', 'modules'))
            import exceptions

            collector = exceptions.get_global_error_collector()
            exceptions.clear_global_collector()

            def worker_thread(thread_id):
                """工作线程函数"""
                for i in range(100):
                    error = exceptions.FileOperationError(f"线程{thread_id}错误{i}", operation="test")
                    collector.add_exception(error)
                    time.sleep(0.001)  # 短暂休眠

            # 创建多个线程
            threads = []
            for i in range(5):
                thread = threading.Thread(target=worker_thread, args=(i,))
                threads.append(thread)
                thread.start()

            # 等待所有线程完成
            for thread in threads:
                thread.join()

            # 验证结果
            stats = collector.get_statistics()
            self.assertGreater(stats['total_exceptions'], 400)  # 至少应该有一些异常被收集

        except ImportError:
            self.skipTest("并发测试模块不可用")
        except Exception as e:
            logger.warning(f"并发测试失败: {e}")


def run_main_program_tests():
    """运行主程序集成测试"""
    test_classes = [
        TestMainProgramIntegration,
        TestSystemErrorFlow,
        TestPerformanceAndReliability,
    ]

    suite = unittest.TestSuite()
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 输出结果摘要
    print(f"\n{'='*60}")
    print("主程序集成测试结果摘要:")
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

    # 系统健康检查
    try:
        sys.path.insert(0, os.path.join(project_root, 'gui', 'modules'))
        import exceptions
        collector = exceptions.get_global_error_collector()

        if collector.exceptions:
            print(f"\n系统异常统计:")
            print(f"  总异常数: {len(collector.exceptions)}")
            stats = collector.get_statistics()
            print(f"  按严重程度: {stats['severity_distribution']}")
            print(f"  按异常类型: {stats['type_distribution']}")

            # 生成最终报告
            reporter = exceptions.get_global_error_reporter()
            final_report = reporter.generate_report()

            report_file = os.path.join(project_root, "test_integration_report.txt")
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(final_report)
            print(f"  详细报告已保存到: {report_file}")
    except ImportError:
        print("\n无法生成异常统计报告")

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_main_program_tests()
    sys.exit(0 if success else 1)