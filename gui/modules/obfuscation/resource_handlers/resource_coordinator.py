"""
高级资源处理器协调器

整合所有P2资源处理功能：
- Assets.xcassets处理
- 图片像素修改
- 音频hash修改
- 字体文件处理

使用示例:
```python
handler = AdvancedResourceHandler(symbol_mappings)

# 处理Assets目录
handler.process_assets_catalog(assets_path)

# 修改图片像素
handler.modify_image_pixels(image_path, intensity=0.02)

# 修改音频hash
handler.modify_audio_hash(audio_path)

# 处理字体文件
handler.process_font_file(font_path)

# 获取统计信息
stats = handler.get_statistics()
```

作者: Claude Code
日期: 2025-10-14
版本: v2.3.0
"""

from typing import Dict, List

from .common import ProcessResult
from .assets_handler import AdvancedAssetsHandler
from .image_modifier import ImagePixelModifier
from .audio_modifier import AudioHashModifier
from .font_handler import FontFileHandler


class AdvancedResourceHandler:
    """
    高级资源处理器 - 整合所有P2功能

    使用示例:
    ```python
    handler = AdvancedResourceHandler(symbol_mappings)

    # 处理Assets目录
    handler.process_assets_catalog(assets_path)

    # 修改图片像素
    handler.modify_image_pixels(image_path, intensity=0.02)

    # 修改音频hash
    handler.modify_audio_hash(audio_path)

    # 处理字体文件
    handler.process_font_file(font_path)

    # 获取统计信息
    stats = handler.get_statistics()
    ```
    """

    def __init__(self, symbol_mappings: Dict[str, str] = None,
                 image_intensity: float = 0.02):
        """
        初始化高级资源处理器

        Args:
            symbol_mappings: 符号映射字典
            image_intensity: 图片修改强度
        """
        self.symbol_mappings = symbol_mappings or {}

        # 初始化各个子处理器
        self.assets_handler = AdvancedAssetsHandler(symbol_mappings)
        self.image_modifier = ImagePixelModifier(image_intensity)
        self.audio_modifier = AudioHashModifier()
        self.font_handler = FontFileHandler(symbol_mappings)

        self.results: List[ProcessResult] = []

    def process_assets_catalog(self, assets_path: str, **kwargs) -> bool:
        """处理Assets.xcassets目录"""
        return self.assets_handler.process_assets_catalog(assets_path, **kwargs)

    def modify_image_pixels(self, image_path: str, output_path: str = None) -> ProcessResult:
        """修改图片像素"""
        result = self.image_modifier.modify_image_pixels(image_path, output_path)
        self.results.append(result)
        return result

    def modify_audio_hash(self, audio_path: str, output_path: str = None) -> ProcessResult:
        """修改音频hash"""
        result = self.audio_modifier.modify_audio_hash(audio_path, output_path)
        self.results.append(result)
        return result

    def process_font_file(self, font_path: str, output_path: str = None, **kwargs) -> ProcessResult:
        """处理字体文件"""
        result = self.font_handler.process_font_file(font_path, output_path, **kwargs)
        self.results.append(result)
        return result

    def get_statistics(self) -> Dict:
        """获取综合统计信息"""
        return {
            'assets': self.assets_handler.get_statistics(),
            'images': self.image_modifier.get_statistics(),
            'audio': self.audio_modifier.get_statistics(),
            'fonts': self.font_handler.get_statistics(),
            'total_operations': len(self.results),
            'successful_operations': sum(1 for r in self.results if r.success),
            'failed_operations': sum(1 for r in self.results if not r.success),
        }

    def get_results(self) -> List[ProcessResult]:
        """获取所有处理结果"""
        return self.results.copy()
