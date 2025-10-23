"""
混淆引擎模块

模块化架构，将原始1218行obfuscation_engine.py拆分为清晰的处理器

架构说明:
- common.py: 数据模型 (ObfuscationResult)
- project_init.py: 项目初始化 (分析/白名单/名称生成器)
- source_processor.py: 源文件处理 (解析/转换/增量/缓存)
- feature_processor.py: P2功能处理 (字符串加密/垃圾代码)
- resource_processor.py: 资源文件处理 (Assets/图片/音频/字体)
- result_export.py: 结果导出 (保存/P2后处理/映射导出)
- engine_coordinator.py: 主协调器 (ObfuscationEngine)
"""

from .common import ObfuscationResult
from .engine_coordinator import ObfuscationEngine
from .feature_processor import FeatureProcessor
from .project_init import ProjectInitializer
from .resource_processor import ResourceProcessor
from .result_export import ResultExporter
from .source_processor import SourceProcessor

__all__ = [
    'ObfuscationResult',
    'ObfuscationEngine',
    'ProjectInitializer',
    'SourceProcessor',
    'FeatureProcessor',
    'ResourceProcessor',
    'ResultExporter',
]
