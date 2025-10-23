"""
混淆引擎主协调器

整合所有处理器，协调完整的混淆流程
"""

from datetime import datetime
from typing import Callable, Optional

try:
    from .common import ObfuscationResult
    from .feature_processor import FeatureProcessor
    from .project_init import ProjectInitializer
    from .resource_processor import ResourceProcessor
    from .result_export import ResultExporter
    from .source_processor import SourceProcessor
    from ..config_manager import ConfigManager, ObfuscationConfig
except ImportError:
    from common import ObfuscationResult
    from feature_processor import FeatureProcessor
    from project_init import ProjectInitializer
    from resource_processor import ResourceProcessor
    from result_export import ResultExporter
    from source_processor import SourceProcessor
    from config_manager import ConfigManager, ObfuscationConfig


class ObfuscationEngine:
    """混淆引擎主协调器"""

    def __init__(self, config: ObfuscationConfig = None):
        """
        初始化混淆引擎

        Args:
            config: 混淆配置，如果为None则使用默认配置
        """
        if config is None:
            config_manager = ConfigManager()
            config = config_manager.get_template("standard")

        self.config = config

        # 初始化各个处理器
        self.project_initializer: Optional[ProjectInitializer] = None
        self.source_processor: Optional[SourceProcessor] = None
        self.feature_processor: Optional[FeatureProcessor] = None
        self.resource_processor: Optional[ResourceProcessor] = None
        self.result_exporter: Optional[ResultExporter] = None

    def obfuscate(self, project_path: str, output_dir: str,
                  progress_callback: Optional[Callable[[float, str], None]] = None) -> ObfuscationResult:
        """
        执行完整的混淆流程

        Args:
            project_path: 项目路径
            output_dir: 输出目录
            progress_callback: 进度回调 callback(progress, message)

        Returns:
            ObfuscationResult: 混淆结果
        """
        start_time = datetime.now()

        result = ObfuscationResult(
            success=False,
            output_dir=output_dir,
            project_name=project_path.split('/')[-1]
        )

        try:
            # ===== 步骤1: 初始化项目 (0-25%) =====
            self._report_progress(progress_callback, 0.0, "开始分析项目结构...")

            # 创建项目初始化器
            self.project_initializer = ProjectInitializer(self.config)

            # 分析项目结构 (0-10%)
            if not self.project_initializer.analyze_project(project_path, progress_callback):
                result.errors.append("项目分析失败")
                return result

            # 初始化白名单 (10-20%)
            self._report_progress(progress_callback, 0.1, "初始化白名单...")
            if not self.project_initializer.initialize_whitelist(project_path):
                result.errors.append("白名单初始化失败")
                return result

            # 初始化名称生成器 (20-25%)
            self._report_progress(progress_callback, 0.2, "初始化名称生成器...")
            self.project_initializer.initialize_name_generator()

            # ===== 步骤2: 源文件处理 (25-60%) =====
            self._report_progress(progress_callback, 0.25, "开始处理源代码...")

            # 创建源文件处理器
            self.source_processor = SourceProcessor(
                self.config,
                self.project_initializer.project_structure,
                self.project_initializer.whitelist_manager,
                self.project_initializer.name_generator
            )

            # 解析源文件 (25-50%)
            if not self.source_processor.parse_source_files(progress_callback):
                result.errors.append("源代码解析失败")
                return result

            # 转换代码 (50-60%)
            if not self.source_processor.transform_code(progress_callback):
                result.errors.append("代码转换失败")
                return result

            # ===== 步骤3: P2功能处理 (60-70%) =====
            self.feature_processor = FeatureProcessor(self.config)

            # 字符串加密 (60-65%)
            if self.config.string_encryption:
                self._report_progress(progress_callback, 0.6, "加密字符串...")
                self.feature_processor.encrypt_strings(
                    self.source_processor.transform_results,
                    progress_callback
                )

            # 插入垃圾代码 (65-70%)
            if self.config.insert_garbage_code:
                self._report_progress(progress_callback, 0.65, "插入垃圾代码...")
                self.feature_processor.insert_garbage_code(
                    self.source_processor.transform_results,
                    output_dir,
                    progress_callback
                )

            # ===== 步骤4: 资源文件处理 (70-75%) =====
            self._report_progress(progress_callback, 0.7, "处理资源文件...")

            self.resource_processor = ResourceProcessor(
                self.config,
                self.project_initializer.project_structure,
                self.source_processor.code_transformer
            )
            self.resource_processor.process_resources(progress_callback)

            # ===== 步骤5: 保存和导出 (75-100%) =====
            self._report_progress(progress_callback, 0.75, "保存混淆结果...")

            # 创建结果导出器
            self.result_exporter = ResultExporter(
                self.config,
                self.project_initializer.project_structure,
                self.source_processor.code_transformer,
                self.project_initializer.name_generator,
                self.source_processor.incremental_manager
            )

            # 保存结果 (75-80%)
            if not self.result_exporter.save_results(
                output_dir,
                self.source_processor.transform_results,
                self.source_processor.file_changes,
                result
            ):
                result.errors.append("保存结果失败")
                return result

            # P2后处理 (80-90%)
            self._report_progress(progress_callback, 0.8, "P2后处理...")
            self.result_exporter.p2_post_processing(
                output_dir,
                self.source_processor.transform_results,
                self.feature_processor.files_with_encryption,
                self.feature_processor.garbage_files,
                self.feature_processor.encryption_algorithm,
                self.feature_processor.encryption_key,
                self.feature_processor.encryption_min_length,
                progress_callback
            )

            # 导出映射文件 (90-100%)
            self._report_progress(progress_callback, 0.9, "导出映射文件...")
            mapping_file = self.result_exporter.export_mapping(
                output_dir,
                self.feature_processor.files_with_encryption,
                self.feature_processor.garbage_files,
                self.feature_processor.total_encrypted_strings,
                self.feature_processor.string_encryptor,
                self.feature_processor.garbage_generator
            )
            result.mapping_file = mapping_file

            # 完成
            result.success = True
            result.elapsed_time = (datetime.now() - start_time).total_seconds()

            self._report_progress(progress_callback, 1.0, "混淆完成！")

        except Exception as e:
            result.errors.append(f"混淆过程异常: {str(e)}")
            import traceback
            result.errors.append(traceback.format_exc())

        return result

    def _report_progress(self, callback: Optional[Callable], progress: float, message: str):
        """报告进度"""
        if callback:
            callback(progress, message)
        print(f"[{progress*100:.0f}%] {message}")

    def get_statistics(self):
        """获取详细统计信息"""
        stats = {}

        if self.project_initializer:
            stats['project'] = {
                'name': self.project_initializer.project_structure.project_name if self.project_initializer.project_structure else '',
                'type': self.project_initializer.project_structure.project_type.value if self.project_initializer.project_structure else '',
                'total_files': self.project_initializer.project_structure.total_files if self.project_initializer.project_structure else 0,
                'total_lines': self.project_initializer.project_structure.total_lines if self.project_initializer.project_structure else 0,
            }
            stats['whitelist'] = self.project_initializer.whitelist_manager.get_statistics() if self.project_initializer.whitelist_manager else {}
            stats['generator'] = self.project_initializer.name_generator.get_statistics() if self.project_initializer.name_generator else {}

        if self.source_processor:
            stats['transformer'] = self.source_processor.code_transformer.get_statistics() if self.source_processor.code_transformer else {}

        if self.resource_processor:
            stats['resources'] = self.resource_processor.resource_handler.get_statistics() if self.resource_processor.resource_handler else {}
            stats['advanced_resources'] = self.resource_processor.advanced_resource_handler.get_statistics() if self.resource_processor.advanced_resource_handler else {}

        if self.feature_processor:
            stats['string_encryption'] = self.feature_processor.string_encryptor.get_statistics() if self.feature_processor.string_encryptor else {}
            stats['garbage_code'] = self.feature_processor.garbage_generator.get_statistics() if self.feature_processor.garbage_generator else {}

        return stats


# 测试代码
if __name__ == "__main__":
    print("=== 混淆引擎测试 ===\n")
    print("注意: 完整测试需要真实的iOS项目")
    print("这里仅展示引擎初始化和配置验证\n")

    # 1. 测试配置加载
    print("1. 测试配置:")
    config_manager = ConfigManager()
    config = config_manager.get_template("standard")
    print(f"  配置名称: {config.name}")
    print(f"  命名策略: {config.naming_strategy}")
    print(f"  混淆类名: {config.class_names}")
    print(f"  混淆方法名: {config.method_names}")

    # 2. 测试引擎初始化
    print("\n2. 测试引擎初始化:")
    engine = ObfuscationEngine(config)
    print(f"  引擎已创建")
    print(f"  配置: {engine.config.name}")

    # 3. 测试进度回调
    print("\n3. 测试进度回调:")

    def test_callback(progress, message):
        print(f"  进度回调: [{progress*100:.0f}%] {message}")

    # 模拟进度
    for i in range(0, 101, 20):
        engine._report_progress(test_callback, i/100, f"处理步骤 {i//20 + 1}")

    print("\n=== 测试完成 ===")
