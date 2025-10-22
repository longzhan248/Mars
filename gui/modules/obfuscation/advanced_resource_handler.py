"""
高级资源文件处理器 - 重定向模块

本文件已拆分为多个子模块，位于 resource_handlers/ 目录。
为保持向后兼容，此文件提供统一的导入接口。

新架构:
- resource_handlers/common.py - 通用数据结构
- resource_handlers/assets_handler.py - Assets.xcassets处理 (300行)
- resource_handlers/image_modifier.py - 图片像素修改 (259行)
- resource_handlers/audio_modifier.py - 音频hash修改 (282行)
- resource_handlers/font_handler.py - 字体文件处理 (367行)
- resource_handlers/resource_coordinator.py - 资源协调器 (124行)

拆分日期: 2025-10-22
原始文件: 1322行 → 6个模块 1374行 (包含文档)
版本: v2.3.1
"""

# 导出所有公共接口，保持向后兼容
from .resource_handlers import (
    ProcessResult,
    AdvancedAssetsHandler,
    ImagePixelModifier,
    AudioHashModifier,
    FontFileHandler,
    AdvancedResourceHandler,
)

__all__ = [
    'ProcessResult',
    'AdvancedAssetsHandler',
    'ImagePixelModifier',
    'AudioHashModifier',
    'FontFileHandler',
    'AdvancedResourceHandler',
]

__version__ = 'v2.3.1'

# 使用示例保持不变:
# from gui.modules.obfuscation.advanced_resource_handler import AdvancedResourceHandler
# handler = AdvancedResourceHandler(symbol_mappings)
# handler.process_assets_catalog(assets_path)
