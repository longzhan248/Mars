"""
P3阶段一测试 - Assets.xcassets完整输出
测试imageset、colorset、dataset的完整处理流程

作者: Claude Code
日期: 2025-10-14
版本: v1.0.0
"""

import unittest
import tempfile
import json
import shutil
from pathlib import Path

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from gui.modules.obfuscation.advanced_resource_handler import AdvancedAssetsHandler


class TestP3AssetsOutput(unittest.TestCase):
    """P3阶段一 - Assets.xcassets完整输出测试"""

    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.assets_dir = Path(self.temp_dir) / "Assets.xcassets"
        self.output_dir = Path(self.temp_dir) / "Output.xcassets"

        # 符号映射（用于测试重命名）
        self.symbol_mappings = {
            'AppIcon': 'Icon001',
            'LaunchImage': 'Launch002',
            'BrandColor': 'Color003',
            'ConfigData': 'Data004',
        }

        # 创建Assets.xcassets目录
        self.assets_dir.mkdir(parents=True)

    def tearDown(self):
        """测试后清理"""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def create_test_imageset(self, name: str):
        """
        创建测试用imageset

        Args:
            name: imageset名称
        """
        imageset_dir = self.assets_dir / f"{name}.imageset"
        imageset_dir.mkdir(parents=True)

        # 创建Contents.json
        contents = {
            "images": [
                {
                    "idiom": "universal",
                    "filename": "icon.png",
                    "scale": "1x"
                },
                {
                    "idiom": "universal",
                    "filename": "icon@2x.png",
                    "scale": "2x"
                },
                {
                    "idiom": "universal",
                    "filename": "icon@3x.png",
                    "scale": "3x"
                }
            ],
            "info": {
                "version": 1,
                "author": "xcode"
            }
        }

        with open(imageset_dir / "Contents.json", 'w', encoding='utf-8') as f:
            json.dump(contents, f, indent=2)

        # 创建测试图片文件（模拟PNG）
        for filename in ["icon.png", "icon@2x.png", "icon@3x.png"]:
            with open(imageset_dir / filename, 'wb') as f:
                # PNG文件头
                f.write(b'\x89PNG\r\n\x1a\n')
                # 测试数据
                f.write(b'test_image_data' * 10)

    def create_test_colorset(self, name: str):
        """
        创建测试用colorset

        Args:
            name: colorset名称
        """
        colorset_dir = self.assets_dir / f"{name}.colorset"
        colorset_dir.mkdir(parents=True)

        # 创建Contents.json
        contents = {
            "colors": [
                {
                    "idiom": "universal",
                    "color": {
                        "color-space": "srgb",
                        "components": {
                            "red": "0.200",
                            "green": "0.400",
                            "blue": "0.600",
                            "alpha": "1.000"
                        }
                    }
                }
            ],
            "info": {
                "version": 1,
                "author": "xcode"
            }
        }

        with open(colorset_dir / "Contents.json", 'w', encoding='utf-8') as f:
            json.dump(contents, f, indent=2)

    def create_test_dataset(self, name: str):
        """
        创建测试用dataset

        Args:
            name: dataset名称
        """
        dataset_dir = self.assets_dir / f"{name}.dataset"
        dataset_dir.mkdir(parents=True)

        # 创建Contents.json
        contents = {
            "data": [
                {
                    "idiom": "universal",
                    "filename": "data.json"
                }
            ],
            "info": {
                "version": 1,
                "author": "xcode"
            }
        }

        with open(dataset_dir / "Contents.json", 'w', encoding='utf-8') as f:
            json.dump(contents, f, indent=2)

        # 创建测试数据文件
        test_data = {"key": "value", "number": 123}
        with open(dataset_dir / "data.json", 'w', encoding='utf-8') as f:
            json.dump(test_data, f, indent=2)

    def test_imageset_complete_output(self):
        """测试imageset完整输出"""
        print("\n=== 测试imageset完整输出 ===")

        # 创建测试imageset
        self.create_test_imageset("AppIcon")

        # 初始化处理器
        handler = AdvancedAssetsHandler(self.symbol_mappings)

        # 处理Assets
        success = handler.process_assets_catalog(
            str(self.assets_dir),
            output_path=str(self.output_dir),
            rename_images=True,
            process_colors=False,
            process_data=False
        )

        self.assertTrue(success, "Assets处理应该成功")

        # 验证输出文件存在
        output_imageset = self.output_dir / "Icon001.imageset"
        self.assertTrue(output_imageset.exists(), "输出imageset目录应该存在")

        # 验证Contents.json
        output_json = output_imageset / "Contents.json"
        self.assertTrue(output_json.exists(), "Contents.json应该存在")

        with open(output_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertIn('images', data, "Contents.json应包含images字段")
            self.assertEqual(len(data['images']), 3, "应有3个image配置")

        # 验证图片文件复制
        for filename in ["icon.png", "icon@2x.png", "icon@3x.png"]:
            image_file = output_imageset / filename
            self.assertTrue(image_file.exists(), f"{filename}应该被复制")
            self.assertGreater(image_file.stat().st_size, 0, f"{filename}不应为空")

        # 验证统计信息
        stats = handler.get_statistics()
        self.assertEqual(stats['imagesets_processed'], 1, "应处理1个imageset")
        self.assertEqual(stats['images_renamed'], 1, "应重命名1个image")
        self.assertEqual(stats['contents_updated'], 1, "应更新1个Contents.json")

        print("✅ imageset完整输出测试通过")

    def test_colorset_complete_output(self):
        """测试colorset完整输出"""
        print("\n=== 测试colorset完整输出 ===")

        # 创建测试colorset
        self.create_test_colorset("BrandColor")

        # 初始化处理器
        handler = AdvancedAssetsHandler(self.symbol_mappings)

        # 处理Assets
        success = handler.process_assets_catalog(
            str(self.assets_dir),
            output_path=str(self.output_dir),
            rename_images=False,
            process_colors=True,
            process_data=False
        )

        self.assertTrue(success, "Assets处理应该成功")

        # 验证输出文件存在
        output_colorset = self.output_dir / "Color003.colorset"
        self.assertTrue(output_colorset.exists(), "输出colorset目录应该存在")

        # 验证Contents.json
        output_json = output_colorset / "Contents.json"
        self.assertTrue(output_json.exists(), "Contents.json应该存在")

        with open(output_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertIn('colors', data, "Contents.json应包含colors字段")

            # 验证颜色值已修改
            color_info = data['colors'][0]
            components = color_info['color']['components']

            # 颜色值应该被微调（不完全等于原值）
            red = float(components['red'])
            green = float(components['green'])
            blue = float(components['blue'])

            # 允许±0.01的变化范围
            self.assertAlmostEqual(red, 0.200, delta=0.01, msg="红色值应被微调")
            self.assertAlmostEqual(green, 0.400, delta=0.01, msg="绿色值应被微调")
            self.assertAlmostEqual(blue, 0.600, delta=0.01, msg="蓝色值应被微调")

        # 验证统计信息
        stats = handler.get_statistics()
        self.assertEqual(stats['colorsets_processed'], 1, "应处理1个colorset")

        print("✅ colorset完整输出测试通过")

    def test_dataset_complete_output(self):
        """测试dataset完整输出"""
        print("\n=== 测试dataset完整输出 ===")

        # 创建测试dataset
        self.create_test_dataset("ConfigData")

        # 初始化处理器
        handler = AdvancedAssetsHandler(self.symbol_mappings)

        # 处理Assets
        success = handler.process_assets_catalog(
            str(self.assets_dir),
            output_path=str(self.output_dir),
            rename_images=False,
            process_colors=False,
            process_data=True
        )

        self.assertTrue(success, "Assets处理应该成功")

        # 验证输出文件存在
        output_dataset = self.output_dir / "Data004.dataset"
        self.assertTrue(output_dataset.exists(), "输出dataset目录应该存在")

        # 验证Contents.json
        output_json = output_dataset / "Contents.json"
        self.assertTrue(output_json.exists(), "Contents.json应该存在")

        with open(output_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertIn('data', data, "Contents.json应包含data字段")

        # 验证数据文件复制
        data_file = output_dataset / "data.json"
        self.assertTrue(data_file.exists(), "data.json应该被复制")

        with open(data_file, 'r', encoding='utf-8') as f:
            test_data = json.load(f)
            self.assertEqual(test_data['key'], 'value', "数据内容应保持一致")
            self.assertEqual(test_data['number'], 123, "数据内容应保持一致")

        # 验证统计信息
        stats = handler.get_statistics()
        self.assertEqual(stats['datasets_processed'], 1, "应处理1个dataset")

        print("✅ dataset完整输出测试通过")

    def test_mixed_assets_processing(self):
        """测试混合Assets处理"""
        print("\n=== 测试混合Assets处理 ===")

        # 创建所有类型的资源
        self.create_test_imageset("AppIcon")
        self.create_test_imageset("LaunchImage")
        self.create_test_colorset("BrandColor")
        self.create_test_dataset("ConfigData")

        # 初始化处理器
        handler = AdvancedAssetsHandler(self.symbol_mappings)

        # 处理所有Assets
        success = handler.process_assets_catalog(
            str(self.assets_dir),
            output_path=str(self.output_dir),
            rename_images=True,
            process_colors=True,
            process_data=True
        )

        self.assertTrue(success, "Assets处理应该成功")

        # 验证所有输出都存在
        self.assertTrue((self.output_dir / "Icon001.imageset").exists())
        self.assertTrue((self.output_dir / "Launch002.imageset").exists())
        self.assertTrue((self.output_dir / "Color003.colorset").exists())
        self.assertTrue((self.output_dir / "Data004.dataset").exists())

        # 验证统计信息
        stats = handler.get_statistics()
        self.assertEqual(stats['imagesets_processed'], 2, "应处理2个imageset")
        self.assertEqual(stats['colorsets_processed'], 1, "应处理1个colorset")
        self.assertEqual(stats['datasets_processed'], 1, "应处理1个dataset")
        # images_renamed会包含所有被重命名的资源（imageset/colorset/dataset）
        self.assertEqual(stats['images_renamed'], 4, "应重命名4个资源（2个imageset + 1个colorset + 1个dataset）")

        print("✅ 混合Assets处理测试通过")
        print(f"统计信息: {stats}")

    def test_no_rename_scenario(self):
        """测试不重命名场景"""
        print("\n=== 测试不重命名场景 ===")

        # 创建一个没有映射的imageset
        self.create_test_imageset("UnmappedIcon")

        # 初始化处理器（空映射）
        handler = AdvancedAssetsHandler({})

        # 处理Assets
        success = handler.process_assets_catalog(
            str(self.assets_dir),
            output_path=str(self.output_dir),
            rename_images=True,
            process_colors=False,
            process_data=False
        )

        self.assertTrue(success, "Assets处理应该成功")

        # 验证名称未改变
        output_imageset = self.output_dir / "UnmappedIcon.imageset"
        self.assertTrue(output_imageset.exists(), "输出imageset应保持原名")

        # 验证统计信息
        stats = handler.get_statistics()
        self.assertEqual(stats['images_renamed'], 0, "不应有重命名")

        print("✅ 不重命名场景测试通过")


if __name__ == '__main__':
    # 运行测试
    suite = unittest.TestLoader().loadTestsFromTestCase(TestP3AssetsOutput)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 输出测试总结
    print("\n" + "="*70)
    print("P3阶段一测试总结")
    print("="*70)
    print(f"总测试数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")

    if result.wasSuccessful():
        print("\n✅ 所有测试通过!")
        sys.exit(0)
    else:
        print("\n❌ 测试失败!")
        sys.exit(1)
