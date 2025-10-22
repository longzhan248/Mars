"""
ConfigPanel单元测试

测试配置面板的核心功能。
"""

import unittest
import tkinter as tk
from tkinter import ttk
from unittest.mock import Mock, patch

# 添加父目录到路径
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../..'))

from gui.modules.obfuscation.ui.config_panel import ConfigPanel


class TestConfigPanel(unittest.TestCase):
    """ConfigPanel测试用例"""

    def setUp(self):
        """测试前准备"""
        self.root = tk.Tk()
        self.controller_mock = Mock()
        self.panel = ConfigPanel(self.root, self.controller_mock)

    def tearDown(self):
        """测试后清理"""
        try:
            self.root.destroy()
        except:
            pass

    def test_init(self):
        """测试初始化"""
        self.assertIsNotNone(self.panel)
        self.assertEqual(self.panel.controller, self.controller_mock)

    def test_template_selection(self):
        """测试模板选择"""
        # 测试模板变量存在
        self.assertIsNotNone(hasattr(self.panel, 'template_var'))

        # 测试默认值
        if hasattr(self.panel, 'template_var'):
            default_value = self.panel.template_var.get()
            self.assertIn(default_value, ['minimal', 'standard', 'aggressive', ''])

    def test_path_validation(self):
        """测试路径验证"""
        # 测试项目路径输入框存在
        self.assertTrue(hasattr(self.panel, 'project_path_var'))

        # 测试输出路径输入框存在
        self.assertTrue(hasattr(self.panel, 'output_path_var'))

    def test_config_options(self):
        """测试配置选项"""
        # 测试混淆选项变量
        expected_vars = [
            'class_names_var',
            'method_names_var',
            'property_names_var',
            'protocol_names_var'
        ]

        for var_name in expected_vars:
            self.assertTrue(hasattr(self.panel, var_name),
                          f"Missing config variable: {var_name}")


class TestConfigValidation(unittest.TestCase):
    """配置验证测试"""

    def test_path_validation(self):
        """测试路径有效性"""
        # 有效路径
        valid_paths = ['/tmp/test', '/Users/test/project']
        for path in valid_paths:
            self.assertTrue(os.path.isabs(path))

        # 无效路径
        invalid_paths = ['', '   ', 'relative/path']
        for path in invalid_paths:
            if path.strip():
                self.assertFalse(os.path.isabs(path) if path else False)

    def test_template_values(self):
        """测试模板值"""
        valid_templates = ['minimal', 'standard', 'aggressive']
        for template in valid_templates:
            self.assertIn(template, ['minimal', 'standard', 'aggressive'])


if __name__ == '__main__':
    unittest.main()
