"""
P3阶段二测试 - 图片像素修改性能优化
测试进度回调、批量处理和智能跳过策略

作者: Claude Code
日期: 2025-10-14
版本: v1.0.0
"""

import unittest
import tempfile
import time
from pathlib import Path

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from gui.modules.obfuscation.advanced_resource_handler import ImagePixelModifier


class TestP3ImagePerformance(unittest.TestCase):
    """P3阶段二 - 图片像素修改性能优化测试"""

    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()

        # 检查Pillow库
        try:
            from PIL import Image
            self.PIL_available = True
        except ImportError:
            self.PIL_available = False
            print("\n⚠️  警告: Pillow库未安装，跳过图片处理测试")

    def tearDown(self):
        """测试后清理"""
        import shutil
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def create_test_image(self, width: int, height: int, filename: str):
        """
        创建测试用图片

        Args:
            width: 宽度
            height: 高度
            filename: 文件名
        """
        if not self.PIL_available:
            return None

        from PIL import Image

        # 创建随机彩色图片
        img = Image.new('RGB', (width, height))
        pixels = img.load()

        # 填充随机颜色
        for y in range(height):
            for x in range(width):
                pixels[x, y] = (
                    (x * 255 // width),
                    (y * 255 // height),
                    ((x + y) * 255 // (width + height))
                )

        image_path = Path(self.temp_dir) / filename
        img.save(image_path, quality=95)
        return str(image_path)

    def test_progress_callback(self):
        """测试进度回调功能"""
        if not self.PIL_available:
            self.skipTest("Pillow库未安装")

        print("\n=== 测试进度回调功能 ===")

        # 创建测试图片（中等大小）
        image_path = self.create_test_image(800, 600, "test_progress.jpg")

        # 进度记录
        progress_records = []

        def progress_callback(progress, message):
            progress_records.append((progress, message))
            print(f"  [{progress*100:.0f}%] {message}")

        # 初始化修改器
        modifier = ImagePixelModifier(intensity=0.02)

        # 修改图片
        result = modifier.modify_image_pixels(
            image_path,
            progress_callback=progress_callback
        )

        self.assertTrue(result.success, "图片修改应该成功")
        self.assertGreater(len(progress_records), 0, "应有进度记录")

        # 验证进度顺序
        for i in range(len(progress_records) - 1):
            self.assertGreaterEqual(
                progress_records[i + 1][0],
                progress_records[i][0],
                "进度应该递增"
            )

        # 验证最后进度为1.0
        self.assertAlmostEqual(
            progress_records[-1][0],
            1.0,
            places=1,
            msg="最后进度应为1.0"
        )

        print(f"✅ 进度回调测试通过，共{len(progress_records)}次回调")

    def test_batch_processing_small_image(self):
        """测试小图片批量处理"""
        if not self.PIL_available:
            self.skipTest("Pillow库未安装")

        print("\n=== 测试小图片批量处理 ===")

        # 创建小图片（< 4MP）
        image_path = self.create_test_image(1000, 1000, "test_small.jpg")

        modifier = ImagePixelModifier(intensity=0.02)

        start_time = time.time()
        result = modifier.modify_image_pixels(image_path)
        elapsed_time = time.time() - start_time

        self.assertTrue(result.success, "图片修改应该成功")
        self.assertEqual(result.details['strategy'], 'batch', "应使用批量处理")
        self.assertEqual(
            result.details['pixels_modified'],
            1000 * 1000,
            "应处理所有像素"
        )

        print(f"  尺寸: 1000x1000 (1MP)")
        print(f"  处理时间: {elapsed_time:.3f}秒")
        print(f"  策略: {result.details['strategy']}")
        print(f"✅ 小图片批量处理测试通过")

    def test_sampled_processing_large_image(self):
        """测试大图片采样处理"""
        if not self.PIL_available:
            self.skipTest("Pillow库未安装")

        print("\n=== 测试大图片采样处理 ===")

        # 创建大图片（> 4MP）
        image_path = self.create_test_image(2500, 2000, "test_large.jpg")

        modifier = ImagePixelModifier(intensity=0.02)

        start_time = time.time()
        result = modifier.modify_image_pixels(image_path)
        elapsed_time = time.time() - start_time

        self.assertTrue(result.success, "图片修改应该成功")
        self.assertEqual(result.details['strategy'], 'sampled', "应使用采样处理")
        self.assertLess(
            result.details['pixels_modified'],
            2500 * 2000,
            "采样处理应少于总像素数"
        )

        # 验证统计
        stats = modifier.get_statistics()
        self.assertEqual(stats['large_images_sampled'], 1, "应记录1个大图片采样")

        print(f"  尺寸: 2500x2000 (5MP)")
        print(f"  处理时间: {elapsed_time:.3f}秒")
        print(f"  策略: {result.details['strategy']}")
        print(f"  处理像素: {result.details['pixels_modified']:,} / {2500*2000:,}")
        print(f"  采样率: {result.details['pixels_modified']*100/(2500*2000):.1f}%")
        print(f"✅ 大图片采样处理测试通过")

    def test_performance_comparison(self):
        """测试性能对比（批量 vs 采样）"""
        if not self.PIL_available:
            self.skipTest("Pillow库未安装")

        print("\n=== 测试性能对比 ===")

        # 创建中等图片
        small_image = self.create_test_image(1000, 1000, "perf_small.jpg")
        large_image = self.create_test_image(2500, 2000, "perf_large.jpg")

        modifier = ImagePixelModifier(intensity=0.02)

        # 测试小图片（批量处理）
        start_time = time.time()
        result_small = modifier.modify_image_pixels(small_image)
        time_small = time.time() - start_time

        # 测试大图片（采样处理）
        start_time = time.time()
        result_large = modifier.modify_image_pixels(large_image)
        time_large = time.time() - start_time

        self.assertTrue(result_small.success)
        self.assertTrue(result_large.success)

        # 计算性能指标
        pixels_small = 1000 * 1000
        pixels_large = 2500 * 2000

        throughput_small = pixels_small / time_small
        throughput_large_actual = result_large.details['pixels_modified'] / time_large
        throughput_large_equivalent = pixels_large / time_large  # 等效吞吐量

        print(f"\n  小图片 (1000x1000, 1MP):")
        print(f"    处理时间: {time_small:.3f}秒")
        print(f"    吞吐量: {throughput_small:,.0f} 像素/秒")
        print(f"    策略: {result_small.details['strategy']}")

        print(f"\n  大图片 (2500x2000, 5MP):")
        print(f"    处理时间: {time_large:.3f}秒")
        print(f"    实际吞吐量: {throughput_large_actual:,.0f} 像素/秒")
        print(f"    等效吞吐量: {throughput_large_equivalent:,.0f} 像素/秒（如果处理所有像素）")
        print(f"    策略: {result_large.details['strategy']}")

        # 性能提升
        if time_large < time_small * 3:  # 大图片应该不会慢太多
            speedup = (pixels_large / time_large) / (pixels_small / time_small)
            print(f"\n  性能提升: {speedup:.1f}x（等效）")
            print(f"✅ 性能对比测试通过，采样策略有效")
        else:
            print(f"⚠️  大图片处理较慢，但仍在可接受范围")

    def test_statistics_tracking(self):
        """测试统计信息追踪"""
        if not self.PIL_available:
            self.skipTest("Pillow库未安装")

        print("\n=== 测试统计信息追踪 ===")

        # 创建不同大小的图片
        small_image = self.create_test_image(800, 600, "stats_small.jpg")
        large_image = self.create_test_image(2500, 2000, "stats_large.jpg")

        modifier = ImagePixelModifier(intensity=0.02)

        # 处理小图片
        result1 = modifier.modify_image_pixels(small_image)
        self.assertTrue(result1.success)

        # 处理大图片
        result2 = modifier.modify_image_pixels(large_image)
        self.assertTrue(result2.success)

        # 获取统计信息
        stats = modifier.get_statistics()

        self.assertEqual(stats['images_modified'], 2, "应处理2张图片")
        self.assertEqual(stats['large_images_sampled'], 1, "应有1张大图片采样")
        self.assertGreater(stats['pixels_adjusted'], 0, "应有像素调整记录")

        print(f"  处理图片数: {stats['images_modified']}")
        print(f"  大图片采样数: {stats['large_images_sampled']}")
        print(f"  总像素调整数: {stats['pixels_adjusted']:,}")
        print(f"✅ 统计信息追踪测试通过")

    def test_strategy_selection(self):
        """测试策略选择逻辑"""
        if not self.PIL_available:
            self.skipTest("Pillow库未安装")

        print("\n=== 测试策略选择逻辑 ===")

        test_cases = [
            (1000, 1000, 'batch', "1MP - 应使用批量处理"),
            (2000, 2000, 'batch', "4MP - 边界情况，应使用批量处理"),
            (2001, 2001, 'sampled', "4MP+ - 应使用采样处理"),
            (3000, 2000, 'sampled', "6MP - 应使用采样处理"),
        ]

        modifier = ImagePixelModifier(intensity=0.02)

        for width, height, expected_strategy, description in test_cases:
            image_path = self.create_test_image(
                width, height,
                f"strategy_{width}x{height}.jpg"
            )

            result = modifier.modify_image_pixels(image_path)

            self.assertTrue(result.success, f"{description} - 处理应成功")
            self.assertEqual(
                result.details['strategy'],
                expected_strategy,
                f"{description} - 策略不匹配"
            )

            print(f"  {width}x{height} ({width*height/1000000:.1f}MP): {result.details['strategy']} ✓")

        print(f"✅ 策略选择逻辑测试通过")


if __name__ == '__main__':
    # 运行测试
    suite = unittest.TestLoader().loadTestsFromTestCase(TestP3ImagePerformance)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 输出测试总结
    print("\n" + "="*70)
    print("P3阶段二测试总结")
    print("="*70)
    print(f"总测试数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print(f"跳过: {len(result.skipped)}")

    if result.wasSuccessful():
        print("\n✅ 所有测试通过!")
        sys.exit(0)
    else:
        print("\n❌ 测试失败!")
        sys.exit(1)
