#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
心娱开发助手模块集成测试套件
测试各个核心模块的异常处理集成和模块间交互
"""

import sys
import os
import unittest
import logging
import tempfile
import json
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'gui', 'modules'))

# 导入异常处理系统
from exceptions import (
    XinyuDevToolsError,
    FileOperationError,
    LogParsingError,
    ImportError,
    AIDiagnosisError,
    SearchError,
    IPSAnalysisError,
    SandboxAccessError,
    PushNotificationError,
    ObfuscationError,
    ConfigurationError,
    IndexingError,
    UIError,
    ErrorSeverity,
    get_global_error_collector,
    get_global_error_reporter,
    clear_global_collector,
)

# 配置日志
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


class TestFileOperationsModule(unittest.TestCase):
    """测试文件操作模块"""

    def setUp(self):
        """设置测试环境"""
        clear_global_collector()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """清理测试环境"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_nonexistent_file(self):
        """测试加载不存在的文件"""
        from file_operations import FileOperations

        ops = FileOperations()
        result = ops.load_file("/nonexistent/file.log")

        # 应该返回None而不是抛出异常
        self.assertIsNone(result)

        # 验证异常被正确收集
        collector = get_global_error_collector()
        self.assertGreater(len(collector.exceptions), 0)
        error = collector.exceptions[-1]
        self.assertIsInstance(error, (FileOperationError, XinyuDevToolsError))

    def test_decode_invalid_xlog(self):
        """测试解码无效xlog文件"""
        from file_operations import FileOperations

        # 创建无效的xlog文件
        invalid_xlog = os.path.join(self.temp_dir, "invalid.xlog")
        with open(invalid_xlog, 'w') as f:
            f.write("这不是有效的xlog内容")

        ops = FileOperations()
        result = ops.decode_xlog(invalid_xlog)

        # 应该返回空列表而不是抛出异常
        self.assertIsInstance(result, list)

        # 验证异常被正确收集
        collector = get_global_error_collector()
        self.assertGreater(len(collector.exceptions), 0)
        error = collector.exceptions[-1]
        self.assertIsInstance(error, (DecodingError, FileOperationError, XinyuDevToolsError))

    def test_parse_invalid_log_lines(self):
        """测试解析无效日志行"""
        from file_operations import FileOperations

        ops = FileOperations()
        invalid_lines = [
            "这不是有效的日志格式",
            "",
            "[INVALID]不完整的日志"
        ]

        result = ops.parse_log_lines(invalid_lines)

        # 应该返回部分解析结果而不是抛出异常
        self.assertIsInstance(result, list)

    def test_export_to_invalid_path(self):
        """测试导出到无效路径"""
        from file_operations import FileOperations
        from data_models import LogEntry

        ops = FileOperations()
        entries = [LogEntry("[I][2025-01-01 00:00:00][Test] 测试日志")]

        # 尝试导出到无效路径
        result = ops.export_to_file(entries, "/invalid/path/export.txt")

        # 应该返回False而不是抛出异常
        self.assertFalse(result)

        # 验证异常被正确收集
        collector = get_global_error_collector()
        self.assertGreater(len(collector.exceptions), 0)
        error = collector.exceptions[-1]
        self.assertIsInstance(error, (ImportError, FileOperationError, XinyuDevToolsError))


class TestLogIndexerModule(unittest.TestCase):
    """测试日志索引模块"""

    def setUp(self):
        """设置测试环境"""
        clear_global_collector()

    def test_index_empty_entries(self):
        """测试索引空条目列表"""
        from log_indexer import LogIndexer

        indexer = LogIndexer()
        result = indexer.build_index([])

        # 应该返回空索引而不是抛出异常
        self.assertIsInstance(result, dict)

    def test_index_invalid_entries(self):
        """测试索引无效条目"""
        from log_indexer import LogIndexer

        indexer = LogIndexer()
        invalid_entries = [
            None,
            "不是LogEntry对象",
            123
        ]

        # 应该优雅地处理无效条目
        result = indexer.build_index(invalid_entries)
        self.assertIsInstance(result, dict)

    def test_search_with_invalid_pattern(self):
        """测试使用无效模式搜索"""
        from log_indexer import LogIndexer
        from data_models import LogEntry

        indexer = LogIndexer()
        entries = [LogEntry("[I][2025-01-01 00:00:00][Test] 测试日志")]
        indexer.build_index(entries)

        # 使用无效的正则表达式
        result = indexer.search("[invalid regex")

        # 应该返回空列表而不是抛出异常
        self.assertIsInstance(result, list)

    def test_memory_usage_monitoring(self):
        """测试内存使用监控"""
        from log_indexer import LogIndexer

        indexer = LogIndexer()

        # 创建大量条目测试内存监控
        from data_models import LogEntry
        entries = [LogEntry(f"[I][2025-01-01 00:00:0{i:02d}][Test] 测试日志 {i}") for i in range(100)]

        result = indexer.build_index(entries)
        self.assertIsInstance(result, dict)


class TestFilterSearchModule(unittest.TestCase):
    """测试过滤搜索模块"""

    def setUp(self):
        """设置测试环境"""
        clear_global_collector()

    def test_filter_with_invalid_criteria(self):
        """测试使用无效条件过滤"""
        from filter_search import FilterSearchManager
        from data_models import LogEntry

        manager = FilterSearchManager()
        entries = [LogEntry("[I][2025-01-01 00:00:00][Test] 测试日志")]

        # 测试各种无效条件
        result = manager.filter_entries(entries, level="INVALID_LEVEL")
        self.assertIsInstance(result, list)

        result = manager.filter_entries(entries, start_time="invalid_time")
        self.assertIsInstance(result, list)

    def test_search_with_special_characters(self):
        """测试包含特殊字符的搜索"""
        from filter_search import FilterSearchManager
        from data_models import LogEntry

        manager = FilterSearchManager()
        entries = [LogEntry("[I][2025-01-01 00:00:00][Test] 特殊字符: !@#$%^&*()")]

        result = manager.filter_entries(entries, keyword="!@#$%^&*()")
        self.assertIsInstance(result, list)

    def test_time_parsing_edge_cases(self):
        """测试时间解析边界情况"""
        from filter_search import FilterSearchManager

        manager = FilterSearchManager()

        # 测试各种时间格式
        time_formats = [
            "2025-01-01 00:00:00",
            "2025-01-01T00:00:00",
            "invalid_time",
            "",
            None
        ]

        for time_str in time_formats:
            try:
                result = manager.parse_time_string(time_str)
                # 应该返回None或有效时间戳
                self.assertTrue(result is None or isinstance(result, (int, float)))
            except Exception:
                # 异常应该被处理而不是抛出
                self.fail(f"时间解析应该优雅处理: {time_str}")


class TestAIDiagnosisModule(unittest.TestCase):
    """测试AI诊断模块"""

    def setUp(self):
        """设置测试环境"""
        clear_global_collector()

    @patch('requests.post')
    def test_ai_api_network_error(self, mock_post):
        """测试AI API网络错误"""
        mock_post.side_effect = ConnectionError("Network unreachable")

        try:
            from ai_diagnosis.ai_client import AIDiagnosisClient

            client = AIDiagnosisClient()
            result = client.ask("测试问题", [])

            # 应该返回错误响应而不是抛出异常
            self.assertIsNotNone(result)
        except ImportError:
            # 如果模块不存在，跳过测试
            self.skipTest("AI诊断模块未找到")

    def test_ai_client_invalid_response(self):
        """测试AI客户端无效响应处理"""
        try:
            from ai_diagnosis.ai_client import AIDiagnosisClient

            client = AIDiagnosisClient()

            # 测试各种无效响应
            invalid_responses = [
                None,
                "",
                "invalid_json",
                "{}",
                {"error": "API error"}
            ]

            for response in invalid_responses:
                # 应该优雅处理无效响应
                result = client._parse_response(response)
                self.assertIsInstance(result, (str, dict))
        except ImportError:
            self.skipTest("AI诊断模块未找到")

    def test_diagnosis_settings_invalid_config(self):
        """测试诊断设置无效配置"""
        try:
            from ai_diagnosis.ai_diagnosis_settings import AIDiagnosisSettings

            settings = AIDiagnosisSettings()

            # 测试无效配置
            invalid_configs = [
                None,
                "",
                "invalid_json",
                {"invalid_key": "value"}
            ]

            for config in invalid_configs:
                # 应该优雅处理无效配置
                result = settings.load_config(config)
                self.assertIsInstance(result, bool)
        except ImportError:
            self.skipTest("AI诊断设置模块未找到")


class TestIOSToolsModules(unittest.TestCase):
    """测试iOS工具模块"""

    def setUp(self):
        """设置测试环境"""
        clear_global_collector()

    def test_ips_tab_invalid_file(self):
        """测试IPS标签页无效文件处理"""
        try:
            # 模拟IPS标签页环境
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()  # 隐藏窗口

            from ips_tab import IPSAnalysisTab

            # 创建mock主应用
            mock_app = Mock()
            tab = IPSAnalysisTab(root, mock_app)

            # 测试加载无效IPS文件
            invalid_ips = os.path.join(tempfile.gettempdir(), "invalid.ips")
            with open(invalid_ips, 'w') as f:
                f.write("这不是有效的IPS文件")

            # 应该优雅处理无效文件
            result = tab.load_ips_file(invalid_ips)

            root.destroy()
        except (ImportError, tk.TclError):
            self.skipTest("IPS模块或GUI环境不可用")

    def test_push_tab_certificate_error(self):
        """测试推送标签页证书错误"""
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()

            from push_tab import PushTestTab

            mock_app = Mock()
            tab = PushTestTab(root, mock_app)

            # 测试加载无效证书
            result = tab.load_certificate("/nonexistent/certificate.p12")

            # 应该优雅处理证书错误
            self.assertIsInstance(result, bool)

            root.destroy()
        except (ImportError, tk.TclError):
            self.skipTest("推送模块或GUI环境不可用")

    def test_sandbox_tab_dependency_error(self):
        """测试沙盒标签页依赖错误"""
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()

            from sandbox_tab import SandboxBrowserTab

            mock_app = Mock()
            tab = SandboxBrowserTab(root, mock_app)

            # 依赖检查应该在初始化时完成
            self.assertIsInstance(tab, SandboxBrowserTab)

            root.destroy()
        except (ImportError, tk.TclError):
            self.skipTest("沙盒模块或GUI环境不可用")

    def test_obfuscation_tab_invalid_project(self):
        """测试混淆标签页无效项目"""
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()

            from obfuscation_tab import ObfuscationTab

            mock_app = Mock()
            tab = ObfuscationTab(root, mock_app)

            # 测试选择无效项目路径
            result = tab.select_project("/nonexistent/project")

            # 应该优雅处理无效项目
            self.assertIsInstance(result, bool)

            root.destroy()
        except (ImportError, tk.TclError):
            self.skipTest("混淆模块或GUI环境不可用")


class TestModuleInteractions(unittest.TestCase):
    """测试模块间交互"""

    def setUp(self):
        """设置测试环境"""
        clear_global_collector()

    def test_file_operations_to_indexer(self):
        """测试文件操作到索引器的数据流"""
        from file_operations import FileOperations
        from log_indexer import LogIndexer
        from data_models import LogEntry

        # 模拟文件操作产生的数据
        entries = [
            LogEntry("[I][2025-01-01 00:00:00][Module1] 日志1"),
            LogEntry("[E][2025-01-01 00:00:01][Module2] 错误日志"),
            LogEntry("[W][2025-01-01 00:00:02][Module1] 警告日志")
        ]

        # 传递给索引器
        indexer = LogIndexer()
        result = indexer.build_index(entries)

        # 验证结果
        self.assertIsInstance(result, dict)
        self.assertGreater(len(result), 0)

    def test_indexer_to_filter_search(self):
        """测试索引器到过滤搜索器的数据流"""
        from log_indexer import LogIndexer
        from filter_search import FilterSearchManager
        from data_models import LogEntry

        # 创建数据
        entries = [
            LogEntry("[I][2025-01-01 00:00:00][Module1] 测试日志"),
            LogEntry("[E][2025-01-01 00:01:00][Module2] 错误日志")
        ]

        # 索引化
        indexer = LogIndexer()
        index_result = indexer.build_index(entries)

        # 过滤搜索
        manager = FilterSearchManager()
        filter_result = manager.filter_entries(entries, level="ERROR")

        # 验证结果
        self.assertIsInstance(filter_result, list)
        self.assertEqual(len(filter_result), 1)

    def test_error_propagation_between_modules(self):
        """测试模块间错误传播"""
        from file_operations import FileOperations

        ops = FileOperations()

        # 触发文件操作错误
        ops.load_file("/nonexistent/file.log")

        # 验证错误被全局收集器捕获
        collector = get_global_error_collector()
        self.assertGreater(len(collector.exceptions), 0)

        # 其他模块应该能够访问这些错误
        reporter = get_global_error_reporter()
        report = reporter.generate_report()

        self.assertIn("异常总数", report)

    def test_concurrent_module_operations(self):
        """测试并发模块操作"""
        import threading
        from file_operations import FileOperations
        from log_indexer import LogIndexer

        results = []
        errors = []

        def file_operation():
            try:
                ops = FileOperations()
                result = ops.load_file("/nonexistent/file.log")
                results.append(result)
            except Exception as e:
                errors.append(e)

        def indexing_operation():
            try:
                indexer = LogIndexer()
                result = indexer.build_index([])
                results.append(result)
            except Exception as e:
                errors.append(e)

        # 并发执行
        threads = [
            threading.Thread(target=file_operation),
            threading.Thread(target=indexing_operation)
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # 验证结果
        self.assertEqual(len(results), 2)
        self.assertEqual(len(errors), 0)  # 异常应该被处理，不传播


def run_module_integration_tests():
    """运行模块集成测试"""
    test_classes = [
        TestFileOperationsModule,
        TestLogIndexerModule,
        TestFilterSearchModule,
        TestAIDiagnosisModule,
        TestIOSToolsModules,
        TestModuleInteractions,
    ]

    suite = unittest.TestSuite()
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 输出结果摘要
    print(f"\n{'='*60}")
    print("模块集成测试结果摘要:")
    print(f"运行测试: {result.testsRun}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print(f"跳过: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0
    print(f"成功率: {success_rate:.1f}%")

    if result.failures:
        print(f"\n失败的测试:")
        for test, traceback in result.failures:
            print(f"  - {test}")

    if result.errors:
        print(f"\n错误的测试:")
        for test, traceback in result.errors:
            print(f"  - {test}")

    # 收集异常统计
    collector = get_global_error_collector()
    if collector.exceptions:
        print(f"\n异常统计:")
        print(f"  总异常数: {len(collector.exceptions)}")
        stats = collector.get_statistics()
        print(f"  按严重程度: {stats['severity_distribution']}")
        print(f"  按异常类型: {stats['type_distribution']}")

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_module_integration_tests()
    sys.exit(0 if success else 1)