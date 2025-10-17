#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI诊断功能集成测试
测试所有AI相关功能的正确性
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock
import json

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 导入AI模块
try:
    from gui.modules.ai_diagnosis import AIClientFactory, AIConfig
    from gui.modules.ai_diagnosis.privacy_filter import PrivacyFilter
    from gui.modules.ai_diagnosis.log_preprocessor import LogPreprocessor
    from gui.modules.ai_diagnosis.prompt_templates import PromptTemplates
except ImportError:
    print("警告: 无法导入AI模块，部分测试将跳过")
    AIClientFactory = None
    AIConfig = None
    PrivacyFilter = None
    LogPreprocessor = None
    PromptTemplates = None


class TestAIConfig(unittest.TestCase):
    """测试AI配置管理"""

    def setUp(self):
        """测试前准备"""
        if AIConfig is None:
            self.skipTest("AI模块未安装")
        self.config_file = '/tmp/test_ai_config.json'

    def tearDown(self):
        """测试后清理"""
        if os.path.exists(self.config_file):
            os.remove(self.config_file)

    def test_default_config(self):
        """测试默认配置"""
        config = AIConfig.get_default_config()

        self.assertEqual(config['ai_service'], 'ClaudeCode')
        self.assertEqual(config['auto_detect'], True)
        self.assertEqual(config['privacy_filter'], True)
        self.assertIn('max_tokens', config)
        self.assertIn('timeout', config)

    def test_save_and_load_config(self):
        """测试配置保存和加载"""
        test_config = {
            'ai_service': 'Claude',
            'api_key': 'test-key-123',
            'model': 'claude-3-opus',
            'auto_detect': False,
            'privacy_filter': True
        }

        # 保存配置
        with patch.object(AIConfig, '_get_config_path', return_value=self.config_file):
            AIConfig.save(test_config)

        # 加载配置
        self.assertTrue(os.path.exists(self.config_file))
        with open(self.config_file, 'r') as f:
            loaded_config = json.load(f)

        self.assertEqual(loaded_config['ai_service'], 'Claude')
        self.assertEqual(loaded_config['api_key'], 'test-key-123')
        self.assertEqual(loaded_config['model'], 'claude-3-opus')

    def test_env_var_override(self):
        """测试环境变量覆盖"""
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'env-key-456'}):
            config = AIConfig.load()
            # 环境变量应该优先
            self.assertEqual(config.get('api_key'), 'env-key-456')


class TestPrivacyFilter(unittest.TestCase):
    """测试隐私过滤器"""

    def setUp(self):
        """测试前准备"""
        if PrivacyFilter is None:
            self.skipTest("AI模块未安装")
        self.filter = PrivacyFilter()

    def test_phone_filter(self):
        """测试手机号脱敏"""
        text = "联系电话: 13812345678"
        filtered = self.filter.filter_text(text)

        self.assertNotIn("13812345678", filtered)
        self.assertIn("138****5678", filtered)

    def test_id_card_filter(self):
        """测试身份证号脱敏"""
        text = "身份证: 110101199001011234"
        filtered = self.filter.filter_text(text)

        self.assertNotIn("199001011234", filtered)
        self.assertIn("110101", filtered)  # 前6位保留
        self.assertIn("1234", filtered)    # 后4位保留

    def test_email_filter(self):
        """测试邮箱脱敏"""
        text = "邮箱: user@example.com"
        filtered = self.filter.filter_text(text)

        self.assertNotIn("user@example.com", filtered)
        self.assertIn("@example.com", filtered)  # 域名保留

    def test_ip_filter(self):
        """测试IP地址脱敏"""
        text = "服务器IP: 192.168.1.100"
        filtered = self.filter.filter_text(text)

        self.assertNotIn("192.168.1.100", filtered)
        self.assertIn("192.168.*.*", filtered)

    def test_multiple_filters(self):
        """测试多种信息同时脱敏"""
        text = "用户13812345678的邮箱是user@example.com，IP是192.168.1.100"
        filtered = self.filter.filter_text(text)

        # 验证所有敏感信息都被过滤
        self.assertNotIn("13812345678", filtered)
        self.assertNotIn("user@example.com", filtered)
        self.assertNotIn("192.168.1.100", filtered)

        # 验证脱敏格式正确
        self.assertIn("138****5678", filtered)
        self.assertIn("@example.com", filtered)
        self.assertIn("192.168.*.*", filtered)


class TestLogPreprocessor(unittest.TestCase):
    """测试日志预处理器"""

    def setUp(self):
        """测试前准备"""
        if LogPreprocessor is None:
            self.skipTest("AI模块未安装")
        self.preprocessor = LogPreprocessor()

        # 创建模拟日志条目
        self.mock_entries = [
            Mock(level='ERROR', module='Network', content='Connection timeout',
                 timestamp='2025-10-16 10:00:00', raw_line='[ERROR] Connection timeout'),
            Mock(level='ERROR', module='Database', content='Query failed',
                 timestamp='2025-10-16 10:01:00', raw_line='[ERROR] Query failed'),
            Mock(level='WARNING', module='Cache', content='Cache miss',
                 timestamp='2025-10-16 10:02:00', raw_line='[WARNING] Cache miss'),
            Mock(level='INFO', module='App', content='User logged in',
                 timestamp='2025-10-16 10:03:00', raw_line='[INFO] User logged in'),
        ]

    def test_crash_extraction(self):
        """测试崩溃提取"""
        crash_entry = Mock(
            level='ERROR',
            module='Crash',
            content='*** Terminating app due to uncaught exception',
            timestamp='2025-10-16 10:00:00',
            raw_line='*** Terminating app due to uncaught exception'
        )

        result = self.preprocessor.prepare_for_ai([crash_entry], 'crash')

        self.assertIn('crash', result.lower())
        self.assertIn('exception', result.lower())

    def test_error_pattern_recognition(self):
        """测试错误模式识别"""
        result = self.preprocessor.prepare_for_ai(self.mock_entries, 'summary')

        # 应该识别出ERROR级别的日志
        self.assertIn('ERROR', result)
        self.assertIn('Network', result)
        self.assertIn('Database', result)

    def test_log_summarization(self):
        """测试日志摘要生成"""
        result = self.preprocessor.prepare_for_ai(self.mock_entries, 'summary')

        # 摘要应该包含统计信息
        self.assertIn('2', result)  # 2个ERROR
        self.assertIn('1', result)  # 1个WARNING

    def test_privacy_filtering(self):
        """测试预处理中的隐私过滤"""
        entry_with_phone = Mock(
            level='INFO',
            module='User',
            content='User phone: 13812345678',
            timestamp='2025-10-16 10:00:00',
            raw_line='[INFO] User phone: 13812345678'
        )

        result = self.preprocessor.prepare_for_ai([entry_with_phone], 'summary')

        # 隐私信息应该被过滤
        self.assertNotIn('13812345678', result)
        self.assertIn('138****5678', result)


class TestPromptTemplates(unittest.TestCase):
    """测试提示词模板"""

    def setUp(self):
        """测试前准备"""
        if PromptTemplates is None:
            self.skipTest("AI模块未安装")

    def test_crash_analysis_template(self):
        """测试崩溃分析模板"""
        log_data = "*** Terminating app due to uncaught exception"
        prompt = PromptTemplates.crash_analysis(log_data)

        self.assertIn('崩溃', prompt)
        self.assertIn('分析', prompt)
        self.assertIn(log_data, prompt)

    def test_performance_analysis_template(self):
        """测试性能分析模板"""
        log_data = "Response time: 5000ms"
        prompt = PromptTemplates.performance_analysis(log_data)

        self.assertIn('性能', prompt)
        self.assertIn(log_data, prompt)

    def test_issue_summary_template(self):
        """测试问题总结模板"""
        log_data = "ERROR: Multiple errors occurred"
        prompt = PromptTemplates.issue_summary(log_data)

        self.assertIn('总结', prompt)
        self.assertIn(log_data, prompt)

    def test_smart_search_template(self):
        """测试智能搜索模板"""
        log_data = "Various log entries"
        query = "network error"
        prompt = PromptTemplates.smart_search(log_data, query)

        self.assertIn('搜索', prompt)
        self.assertIn(query, prompt)
        self.assertIn(log_data, prompt)


class TestAIClientFactory(unittest.TestCase):
    """测试AI客户端工厂"""

    def setUp(self):
        """测试前准备"""
        if AIClientFactory is None:
            self.skipTest("AI模块未安装")

    def test_create_claudecode_client(self):
        """测试创建ClaudeCode客户端"""
        with patch('gui.modules.ai_diagnosis.ai_client_factory.ClaudeCodeClient') as MockClient:
            client = AIClientFactory.create('ClaudeCode')
            MockClient.assert_called_once()

    def test_create_claude_client(self):
        """测试创建Claude客户端"""
        with patch('gui.modules.ai_diagnosis.ai_client_factory.ClaudeClient') as MockClient:
            client = AIClientFactory.create('Claude', api_key='test-key')
            MockClient.assert_called_once_with('test-key', None)

    def test_create_openai_client(self):
        """测试创建OpenAI客户端"""
        with patch('gui.modules.ai_diagnosis.ai_client_factory.OpenAIClient') as MockClient:
            client = AIClientFactory.create('OpenAI', api_key='test-key')
            MockClient.assert_called_once_with('test-key', None)

    def test_create_ollama_client(self):
        """测试创建Ollama客户端"""
        with patch('gui.modules.ai_diagnosis.ai_client_factory.OllamaClient') as MockClient:
            client = AIClientFactory.create('Ollama', model='llama3')
            MockClient.assert_called_once_with('llama3')

    def test_auto_detect(self):
        """测试自动检测功能"""
        with patch('gui.modules.ai_diagnosis.ai_client_factory.ClaudeCodeClient') as MockClient:
            # 模拟ClaudeCode可用
            MockClient.return_value.test_connection.return_value = True

            client = AIClientFactory.auto_detect()
            self.assertIsNotNone(client)

    def test_invalid_service(self):
        """测试无效服务类型"""
        with self.assertRaises(ValueError):
            AIClientFactory.create('InvalidService')


class TestUIIntegration(unittest.TestCase):
    """测试UI集成"""

    def setUp(self):
        """测试前准备"""
        # 这里需要模拟tkinter环境
        pass

    def test_ai_assistant_panel_creation(self):
        """测试AI助手面板创建"""
        # TODO: 需要tkinter mock环境
        pass

    def test_settings_dialog_creation(self):
        """测试设置对话框创建"""
        # TODO: 需要tkinter mock环境
        pass

    def test_context_menu_binding(self):
        """测试右键菜单绑定"""
        # TODO: 需要tkinter mock环境
        pass


class TestPerformance(unittest.TestCase):
    """性能测试"""

    def test_privacy_filter_performance(self):
        """测试隐私过滤器性能"""
        if PrivacyFilter is None:
            self.skipTest("AI模块未安装")

        import time

        filter = PrivacyFilter()

        # 生成大量测试数据
        text = "手机号13812345678，邮箱user@example.com，IP192.168.1.100\n" * 1000

        start_time = time.time()
        filtered = filter.filter_text(text)
        elapsed_time = time.time() - start_time

        # 过滤1000行应该在1秒内完成
        self.assertLess(elapsed_time, 1.0)
        print(f"隐私过滤性能: {elapsed_time:.3f}秒 (1000行)")

    def test_log_preprocessing_performance(self):
        """测试日志预处理性能"""
        if LogPreprocessor is None:
            self.skipTest("AI模块未安装")

        import time

        preprocessor = LogPreprocessor()

        # 生成大量模拟日志
        mock_entries = []
        for i in range(1000):
            entry = Mock(
                level='ERROR' if i % 10 == 0 else 'INFO',
                module=f'Module{i % 10}',
                content=f'Log content {i}',
                timestamp=f'2025-10-16 10:{i:02d}:00',
                raw_line=f'[INFO] Log content {i}'
            )
            mock_entries.append(entry)

        start_time = time.time()
        result = preprocessor.prepare_for_ai(mock_entries, 'summary')
        elapsed_time = time.time() - start_time

        # 预处理1000条日志应该在2秒内完成
        self.assertLess(elapsed_time, 2.0)
        print(f"日志预处理性能: {elapsed_time:.3f}秒 (1000条)")


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加所有测试类
    suite.addTests(loader.loadTestsFromTestCase(TestAIConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestPrivacyFilter))
    suite.addTests(loader.loadTestsFromTestCase(TestLogPreprocessor))
    suite.addTests(loader.loadTestsFromTestCase(TestPromptTemplates))
    suite.addTests(loader.loadTestsFromTestCase(TestAIClientFactory))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformance))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 打印测试结果摘要
    print("\n" + "="*70)
    print("测试结果摘要")
    print("="*70)
    print(f"总测试数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print(f"跳过: {len(result.skipped)}")
    print("="*70)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
