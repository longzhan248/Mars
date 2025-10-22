"""
测试套件运行脚本

运行所有obfuscation模块的单元测试。
"""

import unittest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../..'))


def run_tests():
    """运行所有测试"""
    # 创建测试加载器
    loader = unittest.TestLoader()

    # 发现并加载所有测试
    start_dir = os.path.dirname(__file__)
    suite = loader.discover(start_dir, pattern='test_*.py')

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 返回结果
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
