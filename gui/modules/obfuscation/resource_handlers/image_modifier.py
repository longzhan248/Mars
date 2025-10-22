"""
图片像素级修改器

功能:
- 轻微色彩调整（不影响视觉效果）
- RGB值微调
- 保持图片格式和透明度
- 进度回调支持
- 批量处理优化
- 智能跳过策略

作者: Claude Code
日期: 2025-10-14
版本: v2.3.0 (P3阶段二优化版)
"""

import random
from typing import Dict, Optional

from .common import ProcessResult


class ImagePixelModifier:
    """
    图片像素级修改器（P3阶段二优化版）

    功能:
    - 轻微色彩调整（不影响视觉效果）
    - RGB值微调
    - 保持图片格式和透明度
    - 进度回调支持
    - 批量处理优化
    - 智能跳过策略
    """

    def __init__(self, intensity: float = 0.02):
        """
        初始化图片修改器

        Args:
            intensity: 修改强度（0.0-1.0），建议0.01-0.05
        """
        self.intensity = max(0.0, min(1.0, intensity))
        self.stats = {
            'images_modified': 0,
            'pixels_adjusted': 0,
            'large_images_sampled': 0,
        }

    def modify_image_pixels(self, image_path: str, output_path: str = None,
                          progress_callback: Optional[callable] = None) -> ProcessResult:
        """
        修改图片像素（P3阶段二优化版）

        Args:
            image_path: 图片路径
            output_path: 输出路径
            progress_callback: 进度回调函数 callback(progress: float, message: str)

        Returns:
            ProcessResult: 处理结果
        """
        try:
            # 尝试导入Pillow
            try:
                from PIL import Image
            except ImportError:
                return ProcessResult(
                    success=False,
                    file_path=image_path,
                    operation="pixel_modify",
                    error="需要安装Pillow库: pip install Pillow"
                )

            if output_path is None:
                output_path = image_path

            # 打开图片
            img = Image.open(image_path)
            width, height = img.size
            total_pixels = width * height

            # 报告进度：图片加载
            if progress_callback:
                progress_callback(0.1, f"加载图片: {width}x{height} ({total_pixels:,} 像素)")

            # 转换为RGB或RGBA模式
            if img.mode not in ['RGB', 'RGBA']:
                img = img.convert('RGB')

            # 智能跳过策略：超大图片使用采样
            use_sampling = total_pixels > 4000000  # 4MP以上使用采样
            if use_sampling:
                if progress_callback:
                    progress_callback(0.2, f"大图片({total_pixels:,}像素)，使用智能采样策略")

                result = self._modify_pixels_sampled(img, progress_callback)
                self.stats['large_images_sampled'] += 1
            else:
                if progress_callback:
                    progress_callback(0.2, f"使用批量处理模式")

                result = self._modify_pixels_batch(img, progress_callback)

            # 报告进度：保存图片
            if progress_callback:
                progress_callback(0.9, "保存图片...")

            # 保存修改后的图片
            img.save(output_path, quality=95)

            if progress_callback:
                progress_callback(1.0, "完成!")

            self.stats['images_modified'] += 1
            self.stats['pixels_adjusted'] += result['pixels_modified']

            return ProcessResult(
                success=True,
                file_path=image_path,
                operation="pixel_modify",
                details={
                    'width': width,
                    'height': height,
                    'pixels_modified': result['pixels_modified'],
                    'intensity': self.intensity,
                    'strategy': result['strategy']
                }
            )

        except Exception as e:
            return ProcessResult(
                success=False,
                file_path=image_path,
                operation="pixel_modify",
                error=str(e)
            )

    def _modify_pixels_batch(self, img, progress_callback: Optional[callable] = None) -> Dict:
        """
        批量处理像素（性能优化）

        Args:
            img: PIL Image对象
            progress_callback: 进度回调

        Returns:
            Dict: 处理结果 {'pixels_modified': int, 'strategy': str}
        """
        pixels = img.load()
        width, height = img.size
        total_pixels = width * height
        modified_pixels = 0

        # 批量处理，每1000个像素报告一次进度
        report_interval = max(1000, total_pixels // 100)

        for y in range(height):
            for x in range(width):
                pixel = pixels[x, y]

                # 对RGB通道进行微调
                if img.mode == 'RGB':
                    r, g, b = pixel
                    r = self._adjust_channel(r)
                    g = self._adjust_channel(g)
                    b = self._adjust_channel(b)
                    pixels[x, y] = (r, g, b)
                elif img.mode == 'RGBA':
                    r, g, b, a = pixel
                    r = self._adjust_channel(r)
                    g = self._adjust_channel(g)
                    b = self._adjust_channel(b)
                    pixels[x, y] = (r, g, b, a)

                modified_pixels += 1

                # 报告进度
                if progress_callback and modified_pixels % report_interval == 0:
                    progress = 0.2 + (modified_pixels / total_pixels) * 0.7
                    progress_callback(progress, f"处理中: {modified_pixels:,}/{total_pixels:,}")

        return {
            'pixels_modified': modified_pixels,
            'strategy': 'batch'
        }

    def _modify_pixels_sampled(self, img, progress_callback: Optional[callable] = None) -> Dict:
        """
        采样处理像素（大图片优化）

        Args:
            img: PIL Image对象
            progress_callback: 进度回调

        Returns:
            Dict: 处理结果 {'pixels_modified': int, 'strategy': str}
        """
        pixels = img.load()
        width, height = img.size
        total_pixels = width * height

        # 采样步长（每隔3个像素修改一次）
        step = 3
        modified_pixels = 0
        sampled_count = 0
        total_samples = (height // step) * (width // step)

        for y in range(0, height, step):
            for x in range(0, width, step):
                pixel = pixels[x, y]

                # 对RGB通道进行微调
                if img.mode == 'RGB':
                    r, g, b = pixel
                    r = self._adjust_channel(r)
                    g = self._adjust_channel(g)
                    b = self._adjust_channel(b)
                    pixels[x, y] = (r, g, b)
                elif img.mode == 'RGBA':
                    r, g, b, a = pixel
                    r = self._adjust_channel(r)
                    g = self._adjust_channel(g)
                    b = self._adjust_channel(b)
                    pixels[x, y] = (r, g, b, a)

                modified_pixels += 1
                sampled_count += 1

                # 报告进度（每500个采样点）
                if progress_callback and sampled_count % 500 == 0:
                    progress = 0.2 + (sampled_count / total_samples) * 0.7
                    progress_callback(progress, f"采样处理: {sampled_count:,}/{total_samples:,}")

        return {
            'pixels_modified': modified_pixels,
            'strategy': 'sampled'
        }

    def _adjust_channel(self, value: int) -> int:
        """
        调整单个颜色通道值

        Args:
            value: 原始值（0-255）

        Returns:
            int: 调整后的值（0-255）
        """
        # 计算调整量（±intensity * 255）
        adjustment = int(random.uniform(-self.intensity, self.intensity) * 255)
        new_value = value + adjustment

        # 限制在0-255范围内
        return max(0, min(255, new_value))

    def get_statistics(self) -> Dict:
        """获取处理统计信息"""
        return self.stats.copy()
