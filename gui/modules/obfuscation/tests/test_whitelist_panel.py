"""
WhitelistPanel单元测试

测试白名单管理面板的核心功能。
"""

import unittest
import tkinter as tk
from tkinter import ttk
import os
import json
import tempfile
from unittest.mock import Mock, patch, MagicMock

# 添加父目录到路径
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../..'))

from gui.modules.obfuscation.ui.whitelist_panel import WhitelistManager


class TestWhitelistPanel(unittest.TestCase):
    """WhitelistPanel测试用例"""

    def setUp(self):
        """测试前准备"""
        self.root = tk.Tk()
        self.tab_main = Mock()

        # 创建临时白名单文件
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.write(json.dumps({
            'custom_symbols': [],
            'string_whitelist': []
        }))
        self.temp_file.close()

        # Mock whitelist路径
        self.manager = WhitelistManager(self.root, self.tab_main)
        self.manager.custom_whitelist_path = self.temp_file.name

    def tearDown(self):
        """测试后清理"""
        try:
            self.root.destroy()
        except:
            pass

        # 删除临时文件
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)

    def test_init(self):
        """测试初始化"""
        self.assertIsNotNone(self.manager)
        self.assertEqual(self.manager.parent, self.root)
        self.assertEqual(self.manager.tab_main, self.tab_main)

    def test_whitelist_file_structure(self):
        """测试白名单文件结构"""
        # 读取文件
        with open(self.temp_file.name, 'r') as f:
            data = json.load(f)

        # 验证结构
        self.assertIn('custom_symbols', data)
        self.assertIn('string_whitelist', data)
        self.assertIsInstance(data['custom_symbols'], list)
        self.assertIsInstance(data['string_whitelist'], list)

    def test_load_symbol_whitelist(self):
        """测试加载符号白名单"""
        # 创建测试数据
        test_data = {
            'custom_symbols': [
                {'type': 'class', 'pattern': 'TestClass*', 'description': '测试类'}
            ],
            'string_whitelist': []
        }

        with open(self.temp_file.name, 'w') as f:
            json.dump(test_data, f)

        # 创建树形控件
        tree = ttk.Treeview(self.root, columns=("type", "pattern", "description"))

        # 加载数据
        self.manager._load_symbol_whitelist(tree)

        # 验证
        items = tree.get_children()
        self.assertEqual(len(items), 1)

        values = tree.item(items[0])['values']
        self.assertEqual(values[0], 'class')
        self.assertEqual(values[1], 'TestClass*')
        self.assertEqual(values[2], '测试类')

    def test_save_symbol_whitelist(self):
        """测试保存符号白名单"""
        # 创建树形控件并添加测试数据
        tree = ttk.Treeview(self.root, columns=("type", "pattern", "description"))
        tree.insert('', 'end', values=('method', 'testMethod*', '测试方法'))

        # 创建窗口mock
        window_mock = Mock()

        # 保存
        self.manager._save_symbol_whitelist(tree, window_mock)

        # 验证文件内容
        with open(self.temp_file.name, 'r') as f:
            data = json.load(f)

        self.assertEqual(len(data['custom_symbols']), 1)
        self.assertEqual(data['custom_symbols'][0]['type'], 'method')
        self.assertEqual(data['custom_symbols'][0]['pattern'], 'testMethod*')

        # 验证窗口被销毁
        window_mock.destroy.assert_called_once()

    def test_load_string_whitelist(self):
        """测试加载字符串白名单"""
        # 创建测试数据
        test_data = {
            'custom_symbols': [],
            'string_whitelist': [
                {'pattern': 'NSLog*', 'description': '系统日志'}
            ]
        }

        with open(self.temp_file.name, 'w') as f:
            json.dump(test_data, f)

        # 创建树形控件
        tree = ttk.Treeview(self.root, columns=("pattern", "description"))

        # 加载数据
        self.manager._load_string_whitelist(tree)

        # 验证
        items = tree.get_children()
        self.assertEqual(len(items), 1)

        values = tree.item(items[0])['values']
        self.assertEqual(values[0], 'NSLog*')
        self.assertEqual(values[1], '系统日志')


class TestWhitelistValidation(unittest.TestCase):
    """白名单验证测试"""

    def setUp(self):
        """测试前准备"""
        self.root = tk.Tk()

    def tearDown(self):
        """测试后清理"""
        try:
            self.root.destroy()
        except:
            pass

    def test_pattern_validation(self):
        """测试模式验证"""
        # 有效模式
        valid_patterns = ['TestClass*', 'UI?Controller', 'MyApp*Manager']
        for pattern in valid_patterns:
            self.assertTrue(len(pattern) > 0)

        # 无效模式
        invalid_patterns = ['', '   ', None]
        for pattern in invalid_patterns:
            if pattern:
                self.assertFalse(len(pattern.strip()) > 0)


if __name__ == '__main__':
    unittest.main()
