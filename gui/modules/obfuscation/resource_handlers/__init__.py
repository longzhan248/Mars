"""
资源处理器模块

包含iOS资源文件的高级处理功能：
- Assets.xcassets处理
- 图片像素修改
- 音频hash修改
- 字体文件处理
"""

from .assets_handler import AdvancedAssetsHandler
from .image_modifier import ImagePixelModifier
from .audio_modifier import AudioHashModifier
from .font_handler import FontFileHandler
from .resource_coordinator import AdvancedResourceHandler, ProcessResult

__all__ = [
    'AdvancedAssetsHandler',
    'ImagePixelModifier',
    'AudioHashModifier',
    'FontFileHandler',
    'AdvancedResourceHandler',
    'ProcessResult',
]

__version__ = 'v2.3.1'
