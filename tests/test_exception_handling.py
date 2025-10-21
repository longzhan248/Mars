#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
异常处理系统测试套件
完整测试验证异常处理体系的各个组件和功能
"""

import sys
import os
import unittest
import logging
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'gui', 'modules'))

from exceptions import (
    # 异常类
    XinyuDevToolsError,
    FileOperationError,
    DecodingError,
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

    # 辅助类
    ErrorSeverity,
    ExceptionCollector,
    ErrorReporter,

    # 装饰器
    handle_exceptions,
    safe_execute,

    # 函数
    get_global_error_collector,
    get_global_error_reporter,
    clear_global_collector,
)

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TestExceptionClasses(unittest.TestCase):
    """测试异常类层次结构"""

    def test_base_exception(self):
        """测试基础异常类"""
        error = XinyuDevToolsError("Test message")

        self.assertEqual(error.message, "Test message")
        self.assertEqual(error.user_message, "操作失败：Test message")
        self.assertEqual(error.error_code, "XinyuDevToolsError")
        self.assertEqual(error.severity, ErrorSeverity.MEDIUM)
        self.assertEqual(error.context, {})
        self.assertIsNone(error.cause)

        # 测试继承关系
        self.assertIsInstance(error, Exception)
        self.assertEqual(str(error), "[XinyuDevToolsError] Test message")

    def test_file_operation_error(self):
        """测试文件操作异常"""
        error = FileOperationError(
            message="文件读取失败",
            user_message="无法读取文件，请检查文件权限",
            filepath="/test/path/file.txt",
            operation="read"
        )

        self.assertEqual(error.error_code, "FileOperationError")
        self.assertEqual(error.context['filepath'], "/test/path/file.txt")
        self.assertEqual(error.context['operation'], "read")
        self.assertEqual(error.severity, ErrorSeverity.MEDIUM)

    def test_ai_diagnosis_error(self):
        """测试AI诊断异常"""
        error = AIDiagnosisError(
            message="API调用失败",
            user_message="AI诊断服务暂时不可用，请稍后重试",
            ai_service="claude",
            request_type="analyze_logs",
            severity=ErrorSeverity.HIGH
        )

        self.assertEqual(error.error_code, "AIDiagnosisError")
        self.assertEqual(error.context['ai_service'], "claude")
        self.assertEqual(error.context['request_type'], "analyze_logs")
        self.assertEqual(error.severity, ErrorSeverity.HIGH)

    def test_exception_chaining(self):
        """测试异常链"""
        original_error = ValueError("原始错误")

        chained_error = FileOperationError(
            message="包装错误",
            user_message="操作失败",
            filepath="/test/file.txt",
            operation="test",
            cause=original_error
        )

        self.assertEqual(chained_error.cause, original_error)
        self.assertEqual(chained_error.__cause__, original_error)

    def test_to_dict_serialization(self):
        """测试异常序列化"""
        error = AIDiagnosisError(
            message="测试错误",
            ai_service="claude",
            user_message="用户提示"
        )

        error_dict = error.to_dict()
        self.assertIsInstance(error_dict, dict)
        self.assertEqual(error_dict['error_type'], 'AIDiagnosisError')
        self.assertEqual(error_dict['message'], '测试错误')
        self.assertEqual(error_dict['user_message'], '用户提示')
        self.assertEqual(error_dict['severity'], 'medium')
        self.assertIn('context', error_dict)
        self.assertIn('timestamp', error_dict)


class TestExceptionCollector(unittest.TestCase):
    """测试异常收集器"""

    def setUp(self):
        """设置测试环境"""
        clear_global_collector()

    def test_collector_basic_functionality(self):
        """测试收集器基本功能"""
        collector = ExceptionCollector()

        error = FileOperationError(
            message="测试错误",
            operation="test",
            filepath="/test/file.txt"
        )

        collector.add_exception(error)
        self.assertEqual(len(collector.exceptions), 1)
        self.assertEqual(collector.exceptions[0], error)

    def test_collector_max_size_limit(self):
        """测试最大数量限制"""
        collector = ExceptionCollector()
        collector.max_exceptions = 5

        # 添加超过最大数量的异常
        for i in range(10):
            error = FileOperationError(f"错误 {i}", operation="test")
            collector.add_exception(error)

        # 应该只保留最新的5个
        self.assertEqual(len(collector.exceptions), 5)
        self.assertEqual(collector.exceptions[-1].message, "错误 9")

    def test_get_summary(self):
        """测试获取摘要信息"""
        collector = ExceptionCollector()

        # 添加不同严重程度的异常
        high_error = AIDiagnosisError("高级错误", ai_service="claude", severity=ErrorSeverity.HIGH)
        low_error = FileOperationError("低级错误", operation="test", severity=ErrorSeverity.LOW)

        collector.add_exception(high_error)
        collector.add_exception(low_error)

        summary = collector.get_summary()
        self.assertEqual(summary['total'], 2)
        self.assertEqual(summary['by_severity']['high'], 1)
        self.assertEqual(summary['by_severity']['low'], 1)
        self.assertEqual(summary['by_type']['AIDiagnosisError'], 1)
        self.assertEqual(summary['by_type']['FileOperationError'], 1)

    def test_get_statistics(self):
        """测试统计信息（兼容性）"""
        collector = ExceptionCollector()

        error = FileOperationError("测试错误", operation="test")
        collector.add_exception(error)

        stats = collector.get_statistics()
        self.assertEqual(stats['total_exceptions'], 1)
        self.assertEqual(stats['severity_distribution']['medium'], 1)
        self.assertEqual(stats['type_distribution']['FileOperationError'], 1)

    def test_clear_exceptions(self):
        """测试清除异常"""
        collector = ExceptionCollector()
        error = FileOperationError("测试错误", operation="test")
        collector.add_exception(error)

        self.assertEqual(len(collector.exceptions), 1)
        collector.clear()
        self.assertEqual(len(collector.exceptions), 0)

    def test_has_critical_errors(self):
        """测试严重错误检测"""
        collector = ExceptionCollector()

        # 添加非严重错误
        low_error = FileOperationError("低级错误", operation="test", severity=ErrorSeverity.LOW)
        collector.add_exception(low_error)
        self.assertFalse(collector.has_critical_errors())

        # 添加严重错误
        critical_error = AIDiagnosisError("严重错误", ai_service="claude", severity=ErrorSeverity.CRITICAL)
        collector.add_exception(critical_error)
        self.assertTrue(collector.has_critical_errors())

    def test_convert_standard_exception(self):
        """测试标准异常转换"""
        collector = ExceptionCollector()

        # 添加标准异常
        standard_error = ValueError("标准异常")
        collector.add_exception(standard_error)

        self.assertEqual(len(collector.exceptions), 1)
        converted_error = collector.exceptions[0]
        self.assertIsInstance(converted_error, XinyuDevToolsError)
        self.assertEqual(converted_error.cause, standard_error)


class TestErrorReporter(unittest.TestCase):
    """测试错误报告器"""

    def setUp(self):
        """设置测试环境"""
        self.collector = ExceptionCollector()
        self.reporter = ErrorReporter()
        self.reporter.collector = self.collector

    def test_generate_text_report(self):
        """测试生成文本报告"""
        error = AIDiagnosisError(
            message="测试错误",
            ai_service="claude",
            severity=ErrorSeverity.HIGH,
            user_message="用户友好消息"
        )
        self.collector.add_exception(error)

        report = self.reporter.generate_report()
        self.assertIn("心娱开发助手错误报告", report)
        self.assertIn("测试错误", report)
        self.assertIn("high", report)  # 小写的严重程度
        self.assertIn("用户友好消息", report)
        self.assertIn("异常总数: 1", report)

    def test_generate_report_with_output_file(self):
        """测试生成报告并保存到文件"""
        import tempfile

        error = FileOperationError("测试错误", operation="test")
        self.collector.add_exception(error)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            temp_file = f.name

        try:
            report = self.reporter.generate_report(output_file=temp_file)

            # 验证文件被创建
            self.assertTrue(os.path.exists(temp_file))

            # 验证文件内容
            with open(temp_file, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertIn("心娱开发助手错误报告", content)
                self.assertIn("测试错误", content)
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_generate_empty_report(self):
        """测试生成空报告"""
        # 确保收集器是空的
        self.collector.clear()
        report = self.reporter.generate_report()
        self.assertIn("心娱开发助手错误报告", report)
        self.assertIn("异常总数: 0", report)


class TestExceptionDecorators(unittest.TestCase):
    """测试异常装饰器"""

    def setUp(self):
        """设置测试环境"""
        clear_global_collector()

    def test_handle_exceptions_success(self):
        """测试正常执行"""
        @handle_exceptions(ValueError, reraise=False)
        def test_function():
            return "正常结果"

        result = test_function()
        self.assertEqual(result, "正常结果")

    def test_handle_exceptions_catches_exception(self):
        """测试异常捕获"""
        @handle_exceptions(ValueError, reraise=False)
        def test_function():
            raise ValueError("测试异常")

        result = test_function()
        self.assertIsNone(result)

    def test_handle_exceptions_reraise(self):
        """测试重新抛出异常"""
        @handle_exceptions(ValueError, reraise=True)
        def test_function():
            raise ValueError("测试异常")

        # 注意：异常会被转换为XinyuDevToolsError
        with self.assertRaises(XinyuDevToolsError):
            test_function()

    def test_handle_exceptions_with_custom_exception(self):
        """测试自定义异常处理"""
        @handle_exceptions(XinyuDevToolsError, reraise=False)
        def test_function():
            raise FileOperationError("文件操作错误", operation="test")

        result = test_function()
        self.assertIsNone(result)

    def test_handle_exceptions_with_global_collector(self):
        """测试全局异常收集"""
        collector = get_global_error_collector()
        initial_count = len(collector.exceptions)

        @handle_exceptions(ValueError, reraise=False)
        def test_function():
            raise ValueError("测试异常")

        result = test_function()
        self.assertIsNone(result)

        # 验证异常被添加到全局收集器
        self.assertEqual(len(collector.exceptions), initial_count + 1)
        latest_error = collector.exceptions[-1]
        self.assertIsInstance(latest_error, XinyuDevToolsError)

    def test_handle_exceptions_unexpected_exception(self):
        """测试未预期异常处理"""
        @handle_exceptions(ValueError, reraise=False)
        def test_function():
            raise RuntimeError("未预期的异常")

        result = test_function()
        self.assertIsNone(result)

    def test_safe_execute_success(self):
        """测试安全执行成功"""
        def test_function():
            return "成功结果"

        result = safe_execute(test_function)
        self.assertEqual(result, "成功结果")

    def test_safe_execute_with_exception(self):
        """测试安全执行异常"""
        def test_function():
            raise ValueError("测试异常")

        result = safe_execute(test_function, default_return="默认结果")
        self.assertEqual(result, "默认结果")

    def test_safe_execute_with_logging(self):
        """测试安全执行日志记录"""
        def test_function():
            raise ValueError("测试异常")

        with self.assertLogs('xinyu_exceptions', level='ERROR') as log:
            result = safe_execute(test_function, log_error=True)
            self.assertIsNone(result)
            self.assertIn("安全执行失败", log.output[0])


class TestGlobalFunctions(unittest.TestCase):
    """测试全局函数"""

    def setUp(self):
        """设置测试环境"""
        clear_global_collector()

    def test_get_global_error_collector(self):
        """测试全局异常收集器"""
        collector = get_global_error_collector()
        self.assertIsInstance(collector, ExceptionCollector)

        # 再次调用应该返回同一个实例
        same_collector = get_global_error_collector()
        self.assertIs(collector, same_collector)

    def test_get_global_error_reporter(self):
        """测试全局错误报告器"""
        reporter = get_global_error_reporter()
        self.assertIsInstance(reporter, ErrorReporter)

        # 再次调用应该返回同一个实例
        same_reporter = get_global_error_reporter()
        self.assertIs(reporter, same_reporter)

    def test_clear_global_collector(self):
        """测试清除全局收集器"""
        collector = get_global_error_collector()
        error = FileOperationError("测试错误", operation="test")
        collector.add_exception(error)

        self.assertEqual(len(collector.exceptions), 1)
        clear_global_collector()
        self.assertEqual(len(collector.exceptions), 0)


class TestIntegratedScenarios(unittest.TestCase):
    """测试集成场景"""

    def setUp(self):
        """设置测试环境"""
        clear_global_collector()

    def test_file_operation_error_flow(self):
        """测试文件操作错误流程"""
        @handle_exceptions(FileNotFoundError, reraise=False)
        def read_file(file_path):
            with open(file_path, 'r') as f:
                return f.read()

        # 尝试读取不存在的文件
        result = read_file("/nonexistent/file.txt")
        self.assertIsNone(result)

        # 验证异常被正确收集
        collector = get_global_error_collector()
        self.assertGreater(len(collector.exceptions), 0)
        error = collector.exceptions[-1]
        self.assertIsInstance(error, XinyuDevToolsError)

    def test_ai_diagnosis_error_flow(self):
        """测试AI诊断错误流程"""
        @handle_exceptions(ConnectionError, reraise=False)
        def call_ai_api():
            raise ConnectionError("Network unreachable")

        result = call_ai_api()
        self.assertIsNone(result)

        # 验证异常被正确转换和收集
        collector = get_global_error_collector()
        self.assertGreater(len(collector.exceptions), 0)
        error = collector.exceptions[-1]
        self.assertIsInstance(error, XinyuDevToolsError)

    def test_sandbox_access_error_flow(self):
        """测试沙盒访问错误流程"""
        @handle_exceptions(ImportError, reraise=False)
        def check_pymobiledevice3():
            import nonexistent_module
            return True

        result = check_pymobiledevice3()
        self.assertIsNone(result)

        # 验证异常被正确转换
        collector = get_global_error_collector()
        self.assertGreater(len(collector.exceptions), 0)

    def test_multiple_exception_types_flow(self):
        """测试多种异常类型流程"""
        @handle_exceptions(ValueError, TypeError, RuntimeError, reraise=False)
        def complex_function(error_type):
            if error_type == "value":
                raise ValueError("值错误")
            elif error_type == "type":
                raise TypeError("类型错误")
            else:
                raise RuntimeError("运行时错误")

        # 测试不同类型的异常
        for error_type in ["value", "type", "runtime"]:
            result = complex_function(error_type)
            self.assertIsNone(result)

        # 验证所有异常都被收集
        collector = get_global_error_collector()
        self.assertGreaterEqual(len(collector.exceptions), 3)

    def test_exception_report_generation_flow(self):
        """测试异常报告生成流程"""
        # 生成几个异常
        @handle_exceptions(ValueError, reraise=False)
        def function_1():
            raise ValueError("函数1错误")

        @handle_exceptions(TypeError, reraise=False)
        def function_2():
            raise TypeError("函数2错误")

        function_1()
        function_2()

        # 生成报告 - 使用全局收集器
        reporter = get_global_error_reporter()
        # 确保报告器使用全局收集器
        reporter.collector = get_global_error_collector()
        report = reporter.generate_report()

        # 验证报告内容
        self.assertIn("异常总数: 2", report)
        # 报告显示最新异常详情，所以至少有一个函数的错误信息
        self.assertTrue("函数1错误" in report or "函数2错误" in report)
        # 验证异常类型统计
        self.assertIn("XinyuDevToolsError: 2", report)


def run_all_tests():
    """运行所有测试"""
    # 创建测试套件
    test_classes = [
        TestExceptionClasses,
        TestExceptionCollector,
        TestErrorReporter,
        TestExceptionDecorators,
        TestGlobalFunctions,
        TestIntegratedScenarios,
    ]

    suite = unittest.TestSuite()
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 输出结果摘要
    print(f"\n{'='*60}")
    print("测试结果摘要:")
    print(f"运行测试: {result.testsRun}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print(f"成功率: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")

    if result.failures:
        print(f"\n失败的测试:")
        for test, traceback in result.failures:
            print(f"  - {test}")
            # 只显示关键错误信息
            error_line = traceback.split('AssertionError:')[-1].strip() if 'AssertionError:' in traceback else 'Assertion failed'
            print(f"    {error_line}")

    if result.errors:
        print(f"\n错误的测试:")
        for test, traceback in result.errors:
            print(f"  - {test}")
            # 只显示关键错误信息
            error_line = traceback.split('Exception:')[-1].strip() if 'Exception:' in traceback else 'Test error'
            print(f"    {error_line}")

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)