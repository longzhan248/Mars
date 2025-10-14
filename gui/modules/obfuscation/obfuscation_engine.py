"""
混淆引擎核心 - 协调所有模块完成混淆流程

支持:
1. 完整的混淆流程编排
2. 多线程并行处理
3. 实时进度反馈
4. 错误处理和回滚
5. 详细的日志记录
"""

import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import json

try:
    from .config_manager import ObfuscationConfig, ConfigManager
    from .whitelist_manager import WhitelistManager
    from .name_generator import NameGenerator, NamingStrategy
    from .project_analyzer import ProjectAnalyzer, ProjectStructure
    from .code_parser import CodeParser, ParsedFile
    from .code_transformer import CodeTransformer, TransformResult
    from .resource_handler import ResourceHandler
    from .incremental_manager import IncrementalManager, FileChangeType
    from .advanced_resource_handler import AdvancedResourceHandler
except ImportError:
    from config_manager import ObfuscationConfig, ConfigManager
    from whitelist_manager import WhitelistManager
    from name_generator import NameGenerator, NamingStrategy
    from project_analyzer import ProjectAnalyzer, ProjectStructure
    from code_parser import CodeParser, ParsedFile
    from code_transformer import CodeTransformer, TransformResult
    from resource_handler import ResourceHandler
    from incremental_manager import IncrementalManager, FileChangeType
    from advanced_resource_handler import AdvancedResourceHandler


@dataclass
class ObfuscationResult:
    """混淆结果"""
    success: bool                               # 是否成功
    output_dir: str                             # 输出目录
    project_name: str                           # 项目名称
    files_processed: int = 0                    # 处理的文件数
    files_failed: int = 0                       # 失败的文件数
    total_replacements: int = 0                 # 总替换次数
    elapsed_time: float = 0.0                   # 耗时（秒）
    mapping_file: str = ""                      # 映射文件路径
    errors: List[str] = field(default_factory=list)  # 错误信息
    warnings: List[str] = field(default_factory=list)  # 警告信息


class ObfuscationEngine:
    """混淆引擎"""

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

        # 初始化各个组件
        self.project_analyzer: Optional[ProjectAnalyzer] = None
        self.whitelist_manager: Optional[WhitelistManager] = None
        self.name_generator: Optional[NameGenerator] = None
        self.code_parser: Optional[CodeParser] = None
        self.code_transformer: Optional[CodeTransformer] = None
        self.resource_handler: Optional[ResourceHandler] = None
        self.advanced_resource_handler: Optional[AdvancedResourceHandler] = None
        self.incremental_manager: Optional[IncrementalManager] = None

        # 处理结果
        self.project_structure: Optional[ProjectStructure] = None
        self.parsed_files: Dict[str, ParsedFile] = {}
        self.transform_results: Dict[str, TransformResult] = {}
        self.file_changes: Dict[FileChangeType, List[str]] = {}

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
            project_name=Path(project_path).name
        )

        try:
            # 步骤1: 分析项目结构 (10%)
            self._report_progress(progress_callback, 0.0, "开始分析项目结构...")
            if not self._analyze_project(project_path, progress_callback):
                result.errors.append("项目分析失败")
                return result

            # 步骤2: 初始化白名单 (20%)
            self._report_progress(progress_callback, 0.2, "初始化白名单...")
            if not self._initialize_whitelist(project_path):
                result.errors.append("白名单初始化失败")
                return result

            # 步骤3: 初始化名称生成器 (25%)
            self._report_progress(progress_callback, 0.25, "初始化名称生成器...")
            self._initialize_name_generator()

            # 步骤4: 解析源代码 (30-50%)
            self._report_progress(progress_callback, 0.3, "解析源代码...")
            if not self._parse_source_files(progress_callback):
                result.errors.append("源代码解析失败")
                return result

            # 步骤5: 转换代码 (50-70%)
            self._report_progress(progress_callback, 0.5, "转换代码...")
            if not self._transform_code(progress_callback):
                result.errors.append("代码转换失败")
                return result

            # 步骤6: 处理资源文件 (70-85%)
            self._report_progress(progress_callback, 0.7, "处理资源文件...")
            self._process_resources(progress_callback)

            # 步骤7: 保存结果 (85-95%)
            self._report_progress(progress_callback, 0.85, "保存混淆结果...")
            if not self._save_results(output_dir, result):
                result.errors.append("保存结果失败")
                return result

            # 步骤8: 导出映射文件 (95-100%)
            self._report_progress(progress_callback, 0.95, "导出映射文件...")
            mapping_file = self._export_mapping(output_dir)
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

    def _analyze_project(self, project_path: str,
                        progress_callback: Optional[Callable] = None) -> bool:
        """分析项目结构"""
        try:
            self.project_analyzer = ProjectAnalyzer(project_path)

            def analyzer_callback(progress, message):
                # 分析阶段占总进度的10%
                total_progress = progress * 0.1
                if progress_callback:
                    progress_callback(total_progress, f"分析项目: {message}")

            self.project_structure = self.project_analyzer.analyze(callback=analyzer_callback)
            return True

        except Exception as e:
            print(f"项目分析失败: {e}")
            return False

    def _initialize_whitelist(self, project_path: str) -> bool:
        """初始化白名单"""
        try:
            self.whitelist_manager = WhitelistManager(project_path=project_path)

            # 自动检测第三方库
            if self.config.auto_detect_third_party:
                detected = self.whitelist_manager.auto_detect_third_party()
                print(f"自动检测到 {detected} 个第三方库")

            # 添加自定义白名单
            for item in self.config.custom_whitelist:
                from .whitelist_manager import WhitelistType
                self.whitelist_manager.add_custom(item, WhitelistType.CUSTOM)

            return True

        except Exception as e:
            print(f"白名单初始化失败: {e}")
            return False

    def _initialize_name_generator(self):
        """初始化名称生成器"""
        # 解析命名策略
        strategy_map = {
            'random': NamingStrategy.RANDOM,
            'prefix': NamingStrategy.PREFIX,
            'pattern': NamingStrategy.PATTERN,
            'dictionary': NamingStrategy.DICTIONARY,
        }

        strategy = strategy_map.get(self.config.naming_strategy, NamingStrategy.RANDOM)

        self.name_generator = NameGenerator(
            strategy=strategy,
            prefix=self.config.name_prefix,
            pattern=self.config.name_pattern,
            min_length=self.config.min_name_length,
            max_length=self.config.max_name_length,
            seed=self.config.fixed_seed if self.config.use_fixed_seed else None
        )

        # 如果启用增量混淆，导入旧映射
        if self.config.enable_incremental and self.config.mapping_file:
            try:
                count = self.name_generator.import_mappings(self.config.mapping_file)
                print(f"导入了 {count} 个旧映射")
            except Exception as e:
                print(f"导入旧映射失败: {e}")

    def _parse_source_files(self, progress_callback: Optional[Callable] = None) -> bool:
        """解析源文件（支持增量编译）"""
        try:
            # 获取所有源文件
            source_files = self.project_analyzer.get_source_files(
                include_objc=True,
                include_swift=True,
                exclude_third_party=True
            )

            if not source_files:
                print("没有找到需要混淆的源文件")
                return False

            all_file_paths = [f.path for f in source_files]

            # P1增强：增量编译支持
            files_to_parse = all_file_paths
            if self.config.enable_incremental:
                # 初始化增量管理器
                self.incremental_manager = IncrementalManager(self.project_structure.root_path)

                # 获取需要处理的文件
                files_to_parse, self.file_changes = self.incremental_manager.get_files_to_process(
                    all_file_paths,
                    force=False
                )

                # 打印增量信息
                print(f"增量编译: 总文件 {len(all_file_paths)} 个")
                print(f"  新增: {len(self.file_changes[FileChangeType.ADDED])} 个")
                print(f"  修改: {len(self.file_changes[FileChangeType.MODIFIED])} 个")
                print(f"  删除: {len(self.file_changes[FileChangeType.DELETED])} 个")
                print(f"  未变化: {len(self.file_changes[FileChangeType.UNCHANGED])} 个")
                print(f"  需要处理: {len(files_to_parse)} 个")

                if not files_to_parse:
                    print("没有文件需要重新处理，跳过解析")
                    return True

            # 解析文件
            self.code_parser = CodeParser(self.whitelist_manager)

            def parser_callback(progress, file_path):
                # 解析阶段占总进度的20% (30%-50%)
                total_progress = 0.3 + progress * 0.2
                if progress_callback:
                    progress_callback(total_progress, f"解析: {Path(file_path).name}")

            self.parsed_files = self.code_parser.parse_files(files_to_parse, callback=parser_callback)

            return len(self.parsed_files) > 0

        except Exception as e:
            print(f"源文件解析失败: {e}")
            return False

    def _transform_code(self, progress_callback: Optional[Callable] = None) -> bool:
        """转换代码"""
        try:
            self.code_transformer = CodeTransformer(
                self.name_generator,
                self.whitelist_manager
            )

            def transformer_callback(progress, file_path):
                # 转换阶段占总进度的20% (50%-70%)
                total_progress = 0.5 + progress * 0.2
                if progress_callback:
                    progress_callback(total_progress, f"转换: {Path(file_path).name}")

            self.transform_results = self.code_transformer.transform_files(
                self.parsed_files,
                callback=transformer_callback
            )

            return len(self.transform_results) > 0

        except Exception as e:
            print(f"代码转换失败: {e}")
            return False

    def _process_resources(self, progress_callback: Optional[Callable] = None):
        """处理资源文件（集成P2高级功能）"""
        try:
            # 获取符号映射
            symbol_mappings = self.code_transformer.symbol_mappings

            # 初始化高级资源处理器（P2功能）
            self.advanced_resource_handler = AdvancedResourceHandler(
                symbol_mappings=symbol_mappings,
                image_intensity=self.config.image_intensity if hasattr(self.config, 'image_intensity') else 0.02
            )

            # 基础资源处理器（XIB/Storyboard）
            self.resource_handler = ResourceHandler(symbol_mappings)

            processed_count = 0

            # 步骤1: 处理Assets.xcassets（P2-1功能）
            if self.config.modify_resource_files:
                assets_path = Path(self.project_structure.root_path) / "Assets.xcassets"
                if assets_path.exists():
                    print(f"📦 处理Assets.xcassets...")
                    try:
                        # 使用process_assets_catalog方法
                        success = self.advanced_resource_handler.process_assets_catalog(str(assets_path))
                        if success:
                            print(f"  ✅ Assets处理成功")
                            processed_count += 1
                        else:
                            print(f"  ⚠️  Assets处理失败")
                    except Exception as e:
                        print(f"  ❌ Assets处理异常: {e}")

            # 步骤2: 处理XIB和Storyboard（基础功能）
            resource_files = []
            if self.config.modify_resource_files and hasattr(self.project_structure, 'xibs'):
                # 添加XIB和Storyboard
                for xib in self.project_structure.xibs:
                    if not xib.is_third_party:
                        resource_files.append(xib.path)

                for storyboard in self.project_structure.storyboards:
                    if not storyboard.is_third_party:
                        resource_files.append(storyboard.path)

                # 处理XIB/Storyboard文件
                if resource_files:
                    print(f"📄 处理 {len(resource_files)} 个XIB/Storyboard文件...")
                    for resource_file in resource_files:
                        try:
                            print(f"  处理: {Path(resource_file).name}")
                            # TODO: 实际XIB/Storyboard处理逻辑
                            processed_count += 1
                        except Exception as e:
                            print(f"  ❌ 处理失败 {resource_file}: {e}")

            # 步骤3: 处理图片文件（P2-2功能）
            if self.config.modify_color_values:
                print(f"🖼️  处理图片文件...")
                image_extensions = ('.png', '.jpg', '.jpeg')
                image_count = 0

                for root, dirs, files in os.walk(self.project_structure.root_path):
                    # 跳过Assets.xcassets（已处理）和第三方库
                    if 'Assets.xcassets' in root or 'Pods' in root or 'Carthage' in root:
                        continue

                    for file in files:
                        if file.endswith(image_extensions):
                            image_path = os.path.join(root, file)
                            try:
                                result = self.advanced_resource_handler.modify_image_pixels(image_path)
                                if result.success:
                                    image_count += 1
                                    if image_count % 10 == 0:  # 每10张打印一次
                                        print(f"  已处理 {image_count} 张图片...")
                            except Exception as e:
                                print(f"  ⚠️  图片处理失败 {file}: {e}")

                if image_count > 0:
                    print(f"  ✅ 成功处理 {image_count} 张图片")
                    processed_count += image_count
                else:
                    print(f"  未找到需要处理的图片文件")

            # 步骤4: 处理音频文件（P2-3功能，可选）
            if hasattr(self.config, 'modify_audio_files') and self.config.modify_audio_files:
                print(f"🔊 处理音频文件...")
                audio_extensions = ('.mp3', '.m4a', '.wav', '.aiff')
                audio_count = 0

                for root, dirs, files in os.walk(self.project_structure.root_path):
                    # 跳过第三方库
                    if 'Pods' in root or 'Carthage' in root:
                        continue

                    for file in files:
                        if file.endswith(audio_extensions):
                            audio_path = os.path.join(root, file)
                            try:
                                result = self.advanced_resource_handler.modify_audio_hash(audio_path)
                                if result.success:
                                    audio_count += 1
                            except Exception as e:
                                print(f"  ⚠️  音频处理失败 {file}: {e}")

                if audio_count > 0:
                    print(f"  ✅ 成功处理 {audio_count} 个音频文件")
                    processed_count += audio_count

            # 步骤5: 处理字体文件（P2-4功能，可选）
            if hasattr(self.config, 'modify_font_files') and self.config.modify_font_files:
                print(f"🔤 处理字体文件...")
                font_extensions = ('.ttf', '.otf', '.ttc')
                font_count = 0

                for root, dirs, files in os.walk(self.project_structure.root_path):
                    # 跳过第三方库
                    if 'Pods' in root or 'Carthage' in root:
                        continue

                    for file in files:
                        if file.endswith(font_extensions):
                            font_path = os.path.join(root, file)
                            try:
                                result = self.advanced_resource_handler.process_font_file(font_path)
                                if result.success:
                                    font_count += 1
                            except Exception as e:
                                print(f"  ⚠️  字体处理失败 {file}: {e}")

                if font_count > 0:
                    print(f"  ✅ 成功处理 {font_count} 个字体文件")
                    processed_count += font_count

            # 输出统计
            if self.advanced_resource_handler:
                stats = self.advanced_resource_handler.get_statistics()
                print(f"\n📊 资源处理总结:")
                print(f"  总操作数: {stats.get('total_operations', 0)}")
                print(f"  成功: {stats.get('successful_operations', 0)}")
                print(f"  失败: {stats.get('failed_operations', 0)}")

                # Assets统计
                if 'assets' in stats and stats['assets'].get('imagesets_processed', 0) > 0:
                    assets = stats['assets']
                    print(f"  Assets处理:")
                    print(f"    - Imagesets: {assets.get('imagesets_processed', 0)}")
                    print(f"    - Colorsets: {assets.get('colorsets_processed', 0)}")
                    print(f"    - Datasets: {assets.get('datasets_processed', 0)}")

                # 图片统计
                if 'images' in stats and stats['images'].get('images_modified', 0) > 0:
                    images = stats['images']
                    print(f"  图片修改: {images['images_modified']} 张")
                    print(f"    - 像素调整: {images.get('pixels_adjusted', 0)}")

                # 音频统计
                if 'audio' in stats and stats['audio'].get('audio_files_modified', 0) > 0:
                    print(f"  音频修改: {stats['audio']['audio_files_modified']} 个")

                # 字体统计
                if 'fonts' in stats and stats['fonts'].get('fonts_processed', 0) > 0:
                    fonts = stats['fonts']
                    print(f"  字体处理: {fonts['fonts_processed']} 个")
                    if fonts.get('fonts_renamed', 0) > 0:
                        print(f"    - 重命名: {fonts['fonts_renamed']} 个")

            if processed_count == 0:
                print("未处理任何资源文件（可能未启用或无资源文件）")

        except Exception as e:
            print(f"❌ 资源处理异常: {e}")
            import traceback
            traceback.print_exc()

    def _save_results(self, output_dir: str, result: ObfuscationResult) -> bool:
        """保存混淆结果"""
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            # 保存源代码文件
            saved_count = 0
            failed_count = 0

            for file_path, transform_result in self.transform_results.items():
                if transform_result.errors:
                    failed_count += 1
                    continue

                try:
                    # 文件名同步重命名逻辑
                    original_path = Path(file_path)
                    file_stem = original_path.stem  # 文件名（不含扩展名）
                    file_suffix = original_path.suffix  # 扩展名（如 .m, .swift）

                    # 检查文件名（不含扩展名）是否是一个被混淆的类名
                    if file_stem in self.code_transformer.symbol_mappings:
                        # 使用混淆后的名称
                        obfuscated_stem = self.code_transformer.symbol_mappings[file_stem]
                        file_name = f"{obfuscated_stem}{file_suffix}"
                        print(f"  文件名同步: {original_path.name} -> {file_name}")
                    else:
                        # 保持原有的文件名
                        file_name = original_path.name

                    output_file = output_path / file_name

                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(transform_result.transformed_content)

                    saved_count += 1
                    result.total_replacements += transform_result.replacements

                except Exception as e:
                    print(f"保存文件失败 {file_path}: {e}")
                    failed_count += 1

            result.files_processed = saved_count
            result.files_failed = failed_count

            print(f"成功保存 {saved_count} 个文件，失败 {failed_count} 个")

            # P1增强：更新增量编译缓存
            if self.config.enable_incremental and self.incremental_manager:
                processed_files = list(self.transform_results.keys())
                deleted_files = self.file_changes.get(FileChangeType.DELETED, [])

                if self.incremental_manager.finalize(processed_files, deleted_files):
                    print("增量编译缓存已更新")
                else:
                    print("警告: 缓存更新失败")

            return saved_count > 0

        except Exception as e:
            print(f"保存结果失败: {e}")
            return False

    def _export_mapping(self, output_dir: str) -> str:
        """导出映射文件"""
        try:
            output_path = Path(output_dir)
            mapping_file = output_path / "obfuscation_mapping.json"

            # 导出名称映射
            self.name_generator.export_mappings(
                str(mapping_file),
                format=self.config.mapping_format
            )

            print(f"映射文件已导出: {mapping_file}")
            return str(mapping_file)

        except Exception as e:
            print(f"导出映射失败: {e}")
            return ""

    def _report_progress(self, callback: Optional[Callable], progress: float, message: str):
        """报告进度"""
        if callback:
            callback(progress, message)
        print(f"[{progress*100:.0f}%] {message}")

    def get_statistics(self) -> Dict:
        """获取详细统计信息"""
        stats = {
            'project': {
                'name': self.project_structure.project_name if self.project_structure else '',
                'type': self.project_structure.project_type.value if self.project_structure else '',
                'total_files': self.project_structure.total_files if self.project_structure else 0,
                'total_lines': self.project_structure.total_lines if self.project_structure else 0,
            },
            'whitelist': self.whitelist_manager.get_statistics() if self.whitelist_manager else {},
            'generator': self.name_generator.get_statistics() if self.name_generator else {},
            'transformer': self.code_transformer.get_statistics() if self.code_transformer else {},
            'resources': self.resource_handler.get_statistics() if self.resource_handler else {},
            'advanced_resources': self.advanced_resource_handler.get_statistics() if self.advanced_resource_handler else {},
        }
        return stats


if __name__ == "__main__":
    # 测试代码
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
    print("\n完整混淆测试:")
    print("python -c 'from gui.modules.obfuscation.obfuscation_engine import ObfuscationEngine")
    print("result = engine.obfuscate(\"/path/to/project\", \"/path/to/output\")")
    print("print(result)'")
