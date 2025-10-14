#!/usr/bin/env python3
"""
增量编译集成测试

测试增量编译功能在完整混淆流程中的应用
"""

import sys
import os
import tempfile
import shutil
import time
from pathlib import Path
import unittest

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from gui.modules.obfuscation.incremental_manager import IncrementalManager, FileChangeType
from gui.modules.obfuscation.config_manager import ConfigManager


class TestIncrementalBuild(unittest.TestCase):
    """增量编译测试"""

    def setUp(self):
        """测试准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.temp_dir) / "TestProject"
        self.project_dir.mkdir()

    def tearDown(self):
        """清理临时文件"""
        shutil.rmtree(self.temp_dir)

    def test_first_build_all_files(self):
        """测试首次构建处理所有文件"""
        # 创建测试文件
        file1 = self.project_dir / "File1.swift"
        file2 = self.project_dir / "File2.swift"
        file1.write_text("class MyClass {}")
        file2.write_text("struct MyStruct {}")

        manager = IncrementalManager(str(self.project_dir))

        # 首次构建应该处理所有文件
        files_to_process, changes = manager.get_files_to_process([str(file1), str(file2)])

        self.assertEqual(len(files_to_process), 2, "首次构建应该处理所有文件")
        self.assertEqual(len(changes[FileChangeType.ADDED]), 2)

    def test_no_changes_skip_all(self):
        """测试无变化时跳过所有文件"""
        # 创建文件
        file1 = self.project_dir / "File1.swift"
        file1.write_text("class MyClass {}")

        manager1 = IncrementalManager(str(self.project_dir))

        # 首次构建
        files_to_process, _ = manager1.get_files_to_process([str(file1)])
        manager1.finalize(files_to_process)

        # 第二次构建（无变化）
        manager2 = IncrementalManager(str(self.project_dir))
        files_to_process, changes = manager2.get_files_to_process([str(file1)])

        self.assertEqual(len(files_to_process), 0, "无变化时不应处理任何文件")
        self.assertEqual(len(changes[FileChangeType.UNCHANGED]), 1)

    def test_detect_file_modification(self):
        """测试检测文件修改"""
        # 创建文件
        file1 = self.project_dir / "File1.swift"
        file1.write_text("class MyClass {}")

        manager1 = IncrementalManager(str(self.project_dir))

        # 首次构建
        files_to_process, _ = manager1.get_files_to_process([str(file1)])
        manager1.finalize(files_to_process)

        # 修改文件
        time.sleep(0.01)  # 确保修改时间不同
        file1.write_text("class MyClass { func newMethod() {} }")

        # 第二次构建（检测修改）
        manager2 = IncrementalManager(str(self.project_dir))
        files_to_process, changes = manager2.get_files_to_process([str(file1)])

        self.assertEqual(len(files_to_process), 1, "应该处理修改的文件")
        self.assertEqual(len(changes[FileChangeType.MODIFIED]), 1)
        self.assertIn(str(file1), changes[FileChangeType.MODIFIED])

    def test_detect_new_file(self):
        """测试检测新增文件"""
        # 首次构建：1个文件
        file1 = self.project_dir / "File1.swift"
        file1.write_text("class MyClass {}")

        manager1 = IncrementalManager(str(self.project_dir))
        files_to_process, _ = manager1.get_files_to_process([str(file1)])
        manager1.finalize(files_to_process)

        # 新增文件
        file2 = self.project_dir / "File2.swift"
        file2.write_text("struct MyStruct {}")

        # 第二次构建：2个文件
        manager2 = IncrementalManager(str(self.project_dir))
        files_to_process, changes = manager2.get_files_to_process([str(file1), str(file2)])

        self.assertEqual(len(changes[FileChangeType.ADDED]), 1, "应该检测到新增文件")
        self.assertIn(str(file2), changes[FileChangeType.ADDED])
        self.assertEqual(len(changes[FileChangeType.UNCHANGED]), 1, "旧文件应该未变化")

    def test_detect_deleted_file(self):
        """测试检测删除文件"""
        # 首次构建：2个文件
        file1 = self.project_dir / "File1.swift"
        file2 = self.project_dir / "File2.swift"
        file1.write_text("class MyClass {}")
        file2.write_text("struct MyStruct {}")

        manager1 = IncrementalManager(str(self.project_dir))
        files_to_process, _ = manager1.get_files_to_process([str(file1), str(file2)])
        manager1.finalize(files_to_process)

        # 第二次构建：只有1个文件（file2被删除）
        manager2 = IncrementalManager(str(self.project_dir))
        files_to_process, changes = manager2.get_files_to_process([str(file1)])

        self.assertEqual(len(changes[FileChangeType.DELETED]), 1, "应该检测到删除的文件")
        self.assertIn(str(file2), changes[FileChangeType.DELETED])

    def test_cache_persistence(self):
        """测试缓存持久化"""
        file1 = self.project_dir / "File1.swift"
        file1.write_text("class MyClass {}")

        # 第一个manager：构建并保存缓存
        manager1 = IncrementalManager(str(self.project_dir))
        files_to_process, _ = manager1.get_files_to_process([str(file1)])
        manager1.finalize(files_to_process)

        # 验证缓存文件已创建
        cache_file = self.project_dir / ".obfuscation_cache.json"
        self.assertTrue(cache_file.exists(), "缓存文件应该被创建")

        # 第二个manager：加载缓存
        manager2 = IncrementalManager(str(self.project_dir))
        loaded = manager2.load_cache()
        self.assertTrue(loaded, "应该成功加载缓存")

        # 验证缓存内容
        stats = manager2.get_statistics()
        self.assertTrue(stats['has_cache'])
        self.assertEqual(stats['total_files'], 1)

    def test_force_rebuild(self):
        """测试强制重新构建"""
        file1 = self.project_dir / "File1.swift"
        file1.write_text("class MyClass {}")

        # 首次构建
        manager1 = IncrementalManager(str(self.project_dir))
        files_to_process, _ = manager1.get_files_to_process([str(file1)])
        manager1.finalize(files_to_process)

        # 强制重新构建
        manager2 = IncrementalManager(str(self.project_dir))
        files_to_process, changes = manager2.get_files_to_process([str(file1)], force=True)

        self.assertEqual(len(files_to_process), 1, "强制构建应该处理所有文件")
        self.assertEqual(len(changes[FileChangeType.ADDED]), 1)

    def test_config_enable_incremental(self):
        """测试配置启用增量编译"""
        config_manager = ConfigManager()
        config = config_manager.get_template("standard")

        # 默认应该禁用增量编译
        self.assertFalse(config.enable_incremental, "默认应该禁用增量编译")

        # 启用增量编译
        config.enable_incremental = True
        self.assertTrue(config.enable_incremental)


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestIncrementalBuild)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result


if __name__ == '__main__':
    print("=" * 70)
    print("增量编译集成测试")
    print("=" * 70)
    print()

    result = run_tests()

    print()
    print("=" * 70)
    print("测试总结:")
    print("=" * 70)
    print(f"运行测试数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")

    if result.wasSuccessful():
        print("\n🎉 所有测试通过！增量编译功能正常")
        sys.exit(0)
    else:
        print(f"\n⚠️  {len(result.failures) + len(result.errors)} 个测试未通过")
        sys.exit(1)
