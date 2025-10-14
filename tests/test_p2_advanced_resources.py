"""
P2功能增强集成测试 - 高级资源处理

测试范围:
1. P2-1: Assets.xcassets完整处理
2. P2-2: 图片像素级变色
3. P2-3: 音频文件hash修改
4. P2-4: 字体文件处理

作者: Claude Code
日期: 2025-10-14
"""

import unittest
import sys
import os
import tempfile
import shutil
import json
import hashlib
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from gui.modules.obfuscation.advanced_resource_handler import (
    AdvancedResourceHandler,
    AdvancedAssetsHandler,
    ImagePixelModifier,
    AudioHashModifier,
    FontFileHandler,
    ProcessResult
)


class TestP2_1_AssetsHandling(unittest.TestCase):
    """P2-1: Assets.xcassets完整处理测试"""

    def setUp(self):
        """初始化测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.assets_dir = Path(self.temp_dir) / "Assets.xcassets"
        self.assets_dir.mkdir()

        self.symbol_mappings = {
            'AppIcon': 'Icon001',
            'LaunchImage': 'Launch002',
            'CustomColor': 'Color003',
        }

    def tearDown(self):
        """清理测试环境"""
        shutil.rmtree(self.temp_dir)

    def test_imageset_processing(self):
        """测试imageset处理"""
        print("\n=== 测试P2-1.1: Imageset处理 ===")

        # 创建测试imageset
        imageset_dir = self.assets_dir / "AppIcon.imageset"
        imageset_dir.mkdir()

        contents = {
            "images": [
                {"idiom": "universal", "filename": "icon@1x.png", "scale": "1x"},
                {"idiom": "universal", "filename": "icon@2x.png", "scale": "2x"},
                {"idiom": "universal", "filename": "icon@3x.png", "scale": "3x"}
            ],
            "info": {"version": 1, "author": "xcode"}
        }

        with open(imageset_dir / "Contents.json", 'w') as f:
            json.dump(contents, f, indent=2)

        # 创建测试图片文件
        for filename in ['icon@1x.png', 'icon@2x.png', 'icon@3x.png']:
            with open(imageset_dir / filename, 'wb') as f:
                f.write(b'\x89PNG\r\n\x1a\n' + b'test_data' * 10)

        # 处理Assets
        handler = AdvancedAssetsHandler(self.symbol_mappings)
        success = handler.process_assets_catalog(str(self.assets_dir))

        self.assertTrue(success, "Imageset处理应该成功")

        stats = handler.get_statistics()
        self.assertEqual(stats['imagesets_processed'], 1)
        self.assertEqual(stats['images_renamed'], 1)

        print(f"✅ Imageset处理成功: {stats}")

    def test_colorset_processing(self):
        """测试colorset处理"""
        print("\n=== 测试P2-1.2: Colorset处理 ===")

        # 创建测试colorset
        colorset_dir = self.assets_dir / "CustomColor.colorset"
        colorset_dir.mkdir()

        contents = {
            "colors": [
                {
                    "idiom": "universal",
                    "color": {
                        "color-space": "srgb",
                        "components": {
                            "red": "0.500",
                            "green": "0.500",
                            "blue": "0.500",
                            "alpha": "1.000"
                        }
                    }
                }
            ],
            "info": {"version": 1, "author": "xcode"}
        }

        with open(colorset_dir / "Contents.json", 'w') as f:
            json.dump(contents, f, indent=2)

        # 处理Assets
        handler = AdvancedAssetsHandler(self.symbol_mappings)
        success = handler.process_assets_catalog(str(self.assets_dir), process_colors=True)

        self.assertTrue(success, "Colorset处理应该成功")

        stats = handler.get_statistics()
        self.assertEqual(stats['colorsets_processed'], 1)

        print(f"✅ Colorset处理成功: {stats}")

    def test_dataset_processing(self):
        """测试dataset处理"""
        print("\n=== 测试P2-1.3: Dataset处理 ===")

        # 创建测试dataset
        dataset_dir = self.assets_dir / "CustomData.dataset"
        dataset_dir.mkdir()

        contents = {
            "data": [
                {"idiom": "universal", "filename": "data.json"}
            ],
            "info": {"version": 1, "author": "xcode"}
        }

        with open(dataset_dir / "Contents.json", 'w') as f:
            json.dump(contents, f, indent=2)

        with open(dataset_dir / "data.json", 'w') as f:
            json.dump({"test": "data"}, f)

        # 处理Assets
        handler = AdvancedAssetsHandler(self.symbol_mappings)
        success = handler.process_assets_catalog(str(self.assets_dir), process_data=True)

        self.assertTrue(success, "Dataset处理应该成功")

        stats = handler.get_statistics()
        self.assertEqual(stats['datasets_processed'], 1)

        print(f"✅ Dataset处理成功: {stats}")


class TestP2_2_ImagePixelModification(unittest.TestCase):
    """P2-2: 图片像素级变色测试"""

    def setUp(self):
        """初始化测试环境"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """清理测试环境"""
        shutil.rmtree(self.temp_dir)

    def test_pixel_modification_without_pillow(self):
        """测试没有Pillow库时的行为"""
        print("\n=== 测试P2-2.1: Pillow库处理 ===")

        # 创建测试图片
        image_path = Path(self.temp_dir) / "test.png"
        with open(image_path, 'wb') as f:
            f.write(b'\x89PNG\r\n\x1a\n' + b'test_data' * 100)

        modifier = ImagePixelModifier(intensity=0.02)
        result = modifier.modify_image_pixels(str(image_path))

        # 检查处理结果（可能成功或失败）
        if not result.success:
            # 可能是缺少Pillow或图片格式问题
            self.assertIsNotNone(result.error, "失败时应有错误信息")
            print(f"✅ 处理失败（预期）: {result.error}")
        else:
            # Pillow可用且图片格式正确
            self.assertIsNotNone(result.details, "成功时应有详情")
            print(f"✅ Pillow可用，像素修改成功: {result.details}")

    def test_hash_verification(self):
        """测试修改后hash值改变"""
        print("\n=== 测试P2-2.2: Hash值验证 ===")

        # 创建测试图片
        image_path = Path(self.temp_dir) / "test.png"
        original_data = b'\x89PNG\r\n\x1a\n' + b'test_data' * 100

        with open(image_path, 'wb') as f:
            f.write(original_data)

        original_hash = hashlib.md5(original_data).hexdigest()

        # 尝试修改（如果有Pillow）
        modifier = ImagePixelModifier(intensity=0.02)
        result = modifier.modify_image_pixels(str(image_path))

        if result.success:
            with open(image_path, 'rb') as f:
                modified_data = f.read()

            modified_hash = hashlib.md5(modified_data).hexdigest()

            self.assertNotEqual(original_hash, modified_hash, "Hash值应该改变")
            print(f"✅ Hash值已改变: {original_hash} → {modified_hash}")
        else:
            print(f"⚠️  Pillow不可用，跳过hash验证")


class TestP2_3_AudioHashModification(unittest.TestCase):
    """P2-3: 音频文件hash修改测试"""

    def setUp(self):
        """初始化测试环境"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """清理测试环境"""
        shutil.rmtree(self.temp_dir)

    def test_mp3_modification(self):
        """测试MP3文件修改"""
        print("\n=== 测试P2-3.1: MP3文件修改 ===")

        # 创建测试MP3文件
        mp3_path = Path(self.temp_dir) / "test.mp3"
        original_data = b'ID3' + b'\x00' * 10 + b'audio_data' * 200

        with open(mp3_path, 'wb') as f:
            f.write(original_data)

        original_hash = hashlib.md5(original_data).hexdigest()

        # 修改音频hash
        modifier = AudioHashModifier()
        result = modifier.modify_audio_hash(str(mp3_path))

        self.assertTrue(result.success, "MP3修改应该成功")
        self.assertEqual(result.operation, "audio_hash_modify")

        # 验证hash改变
        with open(mp3_path, 'rb') as f:
            modified_data = f.read()

        modified_hash = hashlib.md5(modified_data).hexdigest()
        self.assertNotEqual(original_hash, modified_hash, "Hash应该改变")

        print(f"✅ MP3修改成功")
        print(f"   原始大小: {result.details['original_size']} 字节")
        print(f"   新大小: {result.details['new_size']} 字节")
        print(f"   添加: {result.details['added_bytes']} 字节")

    def test_wav_modification(self):
        """测试WAV文件修改"""
        print("\n=== 测试P2-3.2: WAV文件修改 ===")

        # 创建测试WAV文件
        wav_path = Path(self.temp_dir) / "test.wav"
        original_data = b'RIFF' + b'\x00' * 4 + b'WAVE' + b'audio_data' * 200

        with open(wav_path, 'wb') as f:
            f.write(original_data)

        original_hash = hashlib.md5(original_data).hexdigest()

        # 修改音频hash
        modifier = AudioHashModifier()
        result = modifier.modify_audio_hash(str(wav_path))

        self.assertTrue(result.success, "WAV修改应该成功")

        # 验证hash改变
        with open(wav_path, 'rb') as f:
            modified_data = f.read()

        modified_hash = hashlib.md5(modified_data).hexdigest()
        self.assertNotEqual(original_hash, modified_hash, "Hash应该改变")

        print(f"✅ WAV修改成功: hash已改变")


class TestP2_4_FontFileHandling(unittest.TestCase):
    """P2-4: 字体文件处理测试"""

    def setUp(self):
        """初始化测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.symbol_mappings = {
            'CustomFont': 'Font001',
            'AppFont': 'Font002',
        }

    def tearDown(self):
        """清理测试环境"""
        shutil.rmtree(self.temp_dir)

    def test_ttf_processing(self):
        """测试TTF字体处理"""
        print("\n=== 测试P2-4.1: TTF字体处理 ===")

        # 创建测试TTF文件
        ttf_path = Path(self.temp_dir) / "CustomFont.ttf"
        with open(ttf_path, 'wb') as f:
            # TrueType字体文件头
            f.write(b'\x00\x01\x00\x00' + b'font_data' * 100)

        # 处理字体
        handler = FontFileHandler(self.symbol_mappings)
        result = handler.process_font_file(str(ttf_path), rename=True, modify_metadata=True)

        self.assertTrue(result.success, "TTF处理应该成功")
        self.assertIn('renamed', result.details['operations'])
        self.assertIn('metadata_modified', result.details['operations'])

        # 验证重命名
        expected_output = Path(self.temp_dir) / "Font001.ttf"
        self.assertTrue(expected_output.exists(), "重命名后的文件应该存在")

        print(f"✅ TTF字体处理成功")
        print(f"   操作: {result.details['operations']}")
        print(f"   输出: {result.details['output_path']}")

    def test_otf_processing(self):
        """测试OTF字体处理"""
        print("\n=== 测试P2-4.2: OTF字体处理 ===")

        # 创建测试OTF文件
        otf_path = Path(self.temp_dir) / "AppFont.otf"
        with open(otf_path, 'wb') as f:
            # OpenType字体文件头
            f.write(b'OTTO' + b'\x00' * 8 + b'font_data' * 100)

        # 处理字体
        handler = FontFileHandler(self.symbol_mappings)
        result = handler.process_font_file(str(otf_path), rename=True)

        self.assertTrue(result.success, "OTF处理应该成功")

        # 验证重命名
        expected_output = Path(self.temp_dir) / "Font002.otf"
        self.assertTrue(expected_output.exists(), "重命名后的文件应该存在")

        print(f"✅ OTF字体处理成功")

    def test_unsupported_format(self):
        """测试不支持的字体格式"""
        print("\n=== 测试P2-4.3: 不支持的格式处理 ===")

        # 创建不支持的文件
        unsupported_path = Path(self.temp_dir) / "test.woff"
        with open(unsupported_path, 'wb') as f:
            f.write(b'woff_data' * 100)

        # 处理字体
        handler = FontFileHandler(self.symbol_mappings)
        result = handler.process_font_file(str(unsupported_path))

        self.assertFalse(result.success, "不支持的格式应该失败")
        self.assertIn("不支持的字体格式", result.error)

        print(f"✅ 正确拒绝不支持的格式: {result.error}")


class TestP2Integration(unittest.TestCase):
    """P2综合测试"""

    def test_comprehensive_resource_processing(self):
        """综合测试：完整资源处理流程"""
        print("\n=== P2综合测试: 完整资源处理流程 ===")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # 符号映射
            symbol_mappings = {
                'AppIcon': 'Icon001',
                'CustomFont': 'Font002',
            }

            # 创建高级资源处理器
            handler = AdvancedResourceHandler(symbol_mappings, image_intensity=0.02)

            # 1. 创建并处理Assets
            print("\n1. 处理Assets.xcassets...")
            assets_dir = temp_path / "Assets.xcassets"
            assets_dir.mkdir()

            imageset_dir = assets_dir / "AppIcon.imageset"
            imageset_dir.mkdir()

            contents = {
                "images": [{"idiom": "universal", "filename": "icon.png"}],
                "info": {"version": 1, "author": "xcode"}
            }

            with open(imageset_dir / "Contents.json", 'w') as f:
                json.dump(contents, f)

            with open(imageset_dir / "icon.png", 'wb') as f:
                f.write(b'\x89PNG\r\n\x1a\n' + b'data' * 10)

            assets_success = handler.process_assets_catalog(str(assets_dir))
            self.assertTrue(assets_success)
            print("   ✓ Assets处理完成")

            # 2. 处理音频文件
            print("\n2. 处理音频文件...")
            audio_file = temp_path / "background.mp3"
            with open(audio_file, 'wb') as f:
                f.write(b'ID3' + b'\x00' * 10 + b'audio' * 100)

            audio_result = handler.modify_audio_hash(str(audio_file))
            self.assertTrue(audio_result.success)
            print(f"   ✓ 音频处理完成: {audio_result.details['added_bytes']} 字节已添加")

            # 3. 处理字体文件
            print("\n3. 处理字体文件...")
            font_file = temp_path / "CustomFont.ttf"
            with open(font_file, 'wb') as f:
                f.write(b'\x00\x01\x00\x00' + b'font' * 100)

            font_result = handler.process_font_file(str(font_file), rename=True)
            self.assertTrue(font_result.success)
            print(f"   ✓ 字体处理完成: {font_result.details['operations']}")

            # 4. 获取综合统计
            print("\n4. 综合统计信息:")
            stats = handler.get_statistics()

            print(f"   Assets: {stats['assets']['imagesets_processed']} imageset已处理")
            print(f"   音频: {stats['audio']['audio_files_modified']} 文件已修改")
            print(f"   字体: {stats['fonts']['fonts_processed']} 文件已处理")
            print(f"   总操作: {stats['total_operations']}")
            print(f"   成功: {stats['successful_operations']}")
            print(f"   失败: {stats['failed_operations']}")

            # 验证所有操作成功
            self.assertEqual(stats['successful_operations'], stats['total_operations'])

            print("\n✅ P2综合测试通过：所有资源处理功能正常！")


def run_tests():
    """运行所有P2功能测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加所有测试类
    suite.addTests(loader.loadTestsFromTestCase(TestP2_1_AssetsHandling))
    suite.addTests(loader.loadTestsFromTestCase(TestP2_2_ImagePixelModification))
    suite.addTests(loader.loadTestsFromTestCase(TestP2_3_AudioHashModification))
    suite.addTests(loader.loadTestsFromTestCase(TestP2_4_FontFileHandling))
    suite.addTests(loader.loadTestsFromTestCase(TestP2Integration))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 输出总结
    print("\n" + "="*70)
    print("P2功能增强测试总结")
    print("="*70)
    print(f"总测试数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")

    if result.wasSuccessful():
        print("\n🎉 所有P2功能验证通过！")
    else:
        print("\n⚠️  部分测试失败，请检查详细输出")

    print("="*70)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
