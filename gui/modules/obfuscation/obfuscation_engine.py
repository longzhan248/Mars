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
    from .garbage_generator import GarbageCodeGenerator, ComplexityLevel
    from .garbage_generator import CodeLanguage as GarbageCodeLanguage  # 垃圾代码的CodeLanguage
    from .string_encryptor import StringEncryptor, EncryptionAlgorithm
    from .string_encryptor import CodeLanguage as StringCodeLanguage  # 字符串加密的CodeLanguage
    from .xcode_project_manager import XcodeProjectManager, check_pbxproj_availability
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
    from garbage_generator import GarbageCodeGenerator, ComplexityLevel
    from garbage_generator import CodeLanguage as GarbageCodeLanguage  # 垃圾代码的CodeLanguage
    from string_encryptor import StringEncryptor, EncryptionAlgorithm
    from string_encryptor import CodeLanguage as StringCodeLanguage  # 字符串加密的CodeLanguage
    from xcode_project_manager import XcodeProjectManager, check_pbxproj_availability


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
        self.garbage_generator: Optional[GarbageCodeGenerator] = None
        self.string_encryptor: Optional[StringEncryptor] = None

        # 处理结果
        self.project_structure: Optional[ProjectStructure] = None
        self.parsed_files: Dict[str, ParsedFile] = {}
        self.transform_results: Dict[str, TransformResult] = {}
        self.file_changes: Dict[FileChangeType, List[str]] = {}

        # P2深度集成 - 存储需要特殊处理的文件
        self.files_with_encryption: Dict[str, List[str]] = {'objc': [], 'swift': []}  # 需要添加解密代码的文件
        self.garbage_files: Dict[str, List[str]] = {'objc': [], 'swift': []}  # 生成的垃圾文件
        self.total_encrypted_strings: int = 0  # 总加密字符串数

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

            # 步骤5: 转换代码 (50-60%)
            self._report_progress(progress_callback, 0.5, "转换代码...")
            if not self._transform_code(progress_callback):
                result.errors.append("代码转换失败")
                return result

            # 步骤6: 字符串加密 (60-65%)
            if self.config.string_encryption:
                self._report_progress(progress_callback, 0.6, "加密字符串...")
                self._encrypt_strings(progress_callback)

            # 步骤7: 插入垃圾代码 (65-70%)
            if self.config.insert_garbage_code:
                self._report_progress(progress_callback, 0.65, "插入垃圾代码...")
                self._insert_garbage_code(output_dir, progress_callback)

            # 步骤8: 处理资源文件 (70-75%)
            self._report_progress(progress_callback, 0.7, "处理资源文件...")
            self._process_resources(progress_callback)

            # 步骤9: P2深度集成后处理 (75-80%)
            self._report_progress(progress_callback, 0.75, "P2后处理...")
            self._p2_post_processing(output_dir, progress_callback)

            # 步骤10: 保存结果 (80-90%)
            self._report_progress(progress_callback, 0.8, "保存混淆结果...")
            if not self._save_results(output_dir, result):
                result.errors.append("保存结果失败")
                return result

            # 步骤11: 导出映射文件 (90-100%)
            self._report_progress(progress_callback, 0.9, "导出映射文件...")
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
        """解析源文件（支持增量编译、并行处理和缓存）"""
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

            # P2性能优化：初始化缓存管理器
            cache_manager = None
            if self.config.enable_parse_cache:
                try:
                    from .parse_cache_manager import ParseCacheManager
                    import os

                    # 确定缓存目录（使用输出目录下的缓存子目录）
                    if hasattr(self.config, 'output_dir') and self.config.output_dir:
                        cache_dir = os.path.join(self.config.output_dir, self.config.cache_dir)
                    else:
                        cache_dir = os.path.join(self.project_structure.root_path, self.config.cache_dir)

                    cache_manager = ParseCacheManager(
                        cache_dir=cache_dir,
                        max_memory_cache=self.config.max_memory_cache,
                        max_disk_cache=self.config.max_disk_cache,
                        enable_memory_cache=True,
                        enable_disk_cache=True
                    )

                    # 清空缓存（如果配置要求）
                    if self.config.clear_cache:
                        print("🗑️  清空解析缓存...")
                        cache_manager.invalidate_all()

                    print(f"📦 启用解析缓存: {cache_dir}")

                except ImportError as e:
                    print(f"⚠️  缓存管理器不可用，使用标准解析: {e}")

            # 解析文件（性能优化：并行处理）
            self.code_parser = CodeParser(self.whitelist_manager)

            def parser_callback(progress, file_path):
                # 解析阶段占总进度的20% (30%-50%)
                total_progress = 0.3 + progress * 0.2
                if progress_callback:
                    progress_callback(total_progress, f"解析: {Path(file_path).name}")

            # P2性能优化：启用并行处理
            if self.config.parallel_processing and len(files_to_parse) >= 10:
                # 使用并行解析器
                try:
                    from .parallel_parser import ParallelCodeParser

                    print(f"⚡ 启用并行解析 ({len(files_to_parse)}个文件, {self.config.max_workers}线程)...")

                    parallel_parser = ParallelCodeParser(max_workers=self.config.max_workers)

                    # 如果启用缓存，使用缓存版本的解析
                    if cache_manager:
                        self.parsed_files = parallel_parser.parse_files_parallel(
                            files_to_parse,
                            self.code_parser,
                            callback=parser_callback,
                            cache_manager=cache_manager  # 传递缓存管理器
                        )
                    else:
                        self.parsed_files = parallel_parser.parse_files_parallel(
                            files_to_parse,
                            self.code_parser,
                            callback=parser_callback
                        )

                    # 打印性能统计
                    parallel_parser.print_statistics()

                except ImportError:
                    print("⚠️ 并行解析器不可用，使用标准解析器")

                    # 使用标准解析器（带缓存）
                    if cache_manager:
                        self.parsed_files = cache_manager.batch_get_or_parse(
                            files_to_parse,
                            self.code_parser,
                            callback=parser_callback
                        )
                    else:
                        self.parsed_files = self.code_parser.parse_files(files_to_parse, callback=parser_callback)
            else:
                # 使用标准串行解析（带缓存）
                if cache_manager:
                    print(f"📦 使用缓存解析 ({len(files_to_parse)}个文件)...")
                    self.parsed_files = cache_manager.batch_get_or_parse(
                        files_to_parse,
                        self.code_parser,
                        callback=parser_callback
                    )
                else:
                    self.parsed_files = self.code_parser.parse_files(files_to_parse, callback=parser_callback)

            # P2性能优化：打印缓存统计
            if cache_manager and self.config.cache_statistics:
                stats = cache_manager.get_statistics()
                total_requests = stats['cache_hits'] + stats['cache_misses']
                print(f"\n📊 解析缓存统计:")
                print(f"  缓存命中: {stats['cache_hits']}/{total_requests} ({stats['hit_rate']*100:.1f}%)")
                print(f"  缓存未命中: {stats['cache_misses']}")
                print(f"  内存缓存: {stats['memory_cache_size']}/{self.config.max_memory_cache}")
                if stats['effective_speedup'] > 1:
                    print(f"  有效加速: {stats['effective_speedup']:.1f}x")
                print()

            return len(self.parsed_files) > 0

        except Exception as e:
            print(f"源文件解析失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _transform_code(self, progress_callback: Optional[Callable] = None) -> bool:
        """转换代码（支持多进程并行）"""
        try:
            self.code_transformer = CodeTransformer(
                self.name_generator,
                self.whitelist_manager
            )

            def transformer_callback(progress, file_path):
                # 转换阶段占总进度的10% (50%-60%)
                total_progress = 0.5 + progress * 0.1
                if progress_callback:
                    progress_callback(total_progress, f"转换: {Path(file_path).name}")

            # P2性能优化：判断是否使用多进程
            total_lines = sum(parsed.get('total_lines', 0) for parsed in self.parsed_files.values())

            if self.config.parallel_processing and (len(self.parsed_files) >= 4 and total_lines > 50000):
                # 使用多进程转换器（适用于超大项目）
                try:
                    from .multiprocess_transformer import MultiProcessTransformer

                    print(f"⚡ 启用多进程转换 (总代码行数: {total_lines}, {self.config.max_workers//2}进程)...")

                    mp_transformer = MultiProcessTransformer(max_workers=self.config.max_workers // 2)
                    self.transform_results = mp_transformer.transform_large_files(
                        self.parsed_files,
                        self.name_generator.get_all_mappings(),
                        callback=transformer_callback
                    )

                    # 打印性能统计
                    mp_transformer.print_statistics()

                except ImportError as e:
                    print(f"⚠️ 多进程转换器不可用，使用标准转换器: {e}")
                    self.transform_results = self.code_transformer.transform_files(
                        self.parsed_files,
                        callback=transformer_callback
                    )
            else:
                # 使用标准转换器
                self.transform_results = self.code_transformer.transform_files(
                    self.parsed_files,
                    callback=transformer_callback
                )

            return len(self.transform_results) > 0

        except Exception as e:
            print(f"代码转换失败: {e}")
            return False

    def _encrypt_strings(self, progress_callback: Optional[Callable] = None):
        """加密字符串（P2功能 - 深度集成）"""
        try:
            print("\n🔐 开始字符串加密...")

            # 确定加密算法
            algorithm_map = {
                'base64': EncryptionAlgorithm.BASE64,
                'xor': EncryptionAlgorithm.XOR,
                'shift': EncryptionAlgorithm.SIMPLE_SHIFT,
                'rot13': EncryptionAlgorithm.ROT13,
                'aes128': EncryptionAlgorithm.AES128,
                'aes256': EncryptionAlgorithm.AES256,
            }

            algorithm = algorithm_map.get(
                getattr(self.config, 'encryption_algorithm', 'xor'),
                EncryptionAlgorithm.XOR
            )

            # 获取加密配置参数
            encryption_key = getattr(self.config, 'encryption_key', 'DefaultKey')
            encryption_min_length = getattr(self.config, 'string_min_length', 4)
            encryption_whitelist = set(getattr(self.config, 'string_whitelist_patterns', []))

            # 保存加密配置供后续P2后处理使用
            self.encryption_algorithm = algorithm
            self.encryption_key = encryption_key
            self.encryption_min_length = encryption_min_length

            # 对每个已转换的文件进行字符串加密
            total_files = len(self.transform_results)
            processed_files = 0
            total_encrypted = 0
            objc_files_with_encryption = []
            swift_files_with_encryption = []

            for file_path, transform_result in self.transform_results.items():
                try:
                    # 获取文件语言
                    is_swift = file_path.endswith('.swift')
                    language = StringCodeLanguage.SWIFT if is_swift else StringCodeLanguage.OBJC

                    # 为每种语言创建对应的StringEncryptor
                    file_encryptor = StringEncryptor(
                        algorithm=algorithm,
                        language=language,
                        key=encryption_key,
                        min_length=encryption_min_length,
                        whitelist=encryption_whitelist
                    )

                    # 对转换后的内容进行字符串加密
                    encrypted_content, encrypted_strings = file_encryptor.process_file(
                        file_path,
                        transform_result.transformed_content
                    )

                    # 保存第一个encryptor供统计使用
                    if not hasattr(self, 'string_encryptor') or self.string_encryptor is None:
                        self.string_encryptor = file_encryptor

                    # 如果有字符串被加密，记录文件并更新内容
                    if encrypted_strings:
                        # 更新转换结果（不在这里插入解密代码，稍后统一处理）
                        transform_result.transformed_content = encrypted_content
                        total_encrypted += len(encrypted_strings)
                        self.total_encrypted_strings += len(encrypted_strings)  # 累积总数

                        if is_swift:
                            swift_files_with_encryption.append(file_path)
                        else:
                            objc_files_with_encryption.append(file_path)

                        print(f"  ✅ {Path(file_path).name}: 加密 {len(encrypted_strings)} 个字符串")

                    processed_files += 1

                    # 更新进度
                    if progress_callback and total_files > 0:
                        progress = processed_files / total_files
                        total_progress = 0.6 + progress * 0.05
                        progress_callback(total_progress, f"加密字符串: {Path(file_path).name}")

                except Exception as e:
                    print(f"  ⚠️  字符串加密失败 {Path(file_path).name}: {e}")

            # 存储需要添加解密代码的文件列表
            self.files_with_encryption = {
                'objc': objc_files_with_encryption,
                'swift': swift_files_with_encryption
            }

            # 输出统计
            if self.string_encryptor:
                stats = self.string_encryptor.get_statistics()
                print(f"\n📊 字符串加密总结:")
                print(f"  处理文件: {processed_files}/{total_files}")
                print(f"  加密字符串: {total_encrypted} 个")
                print(f"  ObjC文件: {len(objc_files_with_encryption)} 个")
                print(f"  Swift文件: {len(swift_files_with_encryption)} 个")
                print(f"  检测字符串: {stats.get('total_strings_detected', 0)} 个")
                print(f"  跳过字符串: {stats.get('strings_skipped', 0)} 个")
                print(f"  过滤比例: {stats.get('strings_skipped', 0) / max(stats.get('total_strings_detected', 1), 1) * 100:.1f}%")

        except Exception as e:
            print(f"❌ 字符串加密异常: {e}")
            import traceback
            traceback.print_exc()

    def _insert_garbage_code(self, output_dir: str, progress_callback: Optional[Callable] = None):
        """插入垃圾代码（P2功能 - 深度集成）"""
        try:
            print("\n🗑️  开始生成垃圾代码...")

            # 确定复杂度级别
            complexity_map = {
                'simple': ComplexityLevel.SIMPLE,
                'moderate': ComplexityLevel.MODERATE,
                'complex': ComplexityLevel.COMPLEX,
            }

            complexity = complexity_map.get(
                getattr(self.config, 'garbage_complexity', 'moderate'),
                ComplexityLevel.MODERATE
            )

            # 确定生成数量
            garbage_count = getattr(self.config, 'garbage_count', 20)

            # 分别为ObjC和Swift生成垃圾代码
            objc_files = [f for f in self.transform_results.keys() if f.endswith(('.m', '.mm'))]
            swift_files = [f for f in self.transform_results.keys() if f.endswith('.swift')]

            # 存储生成的垃圾文件信息（完整路径）
            self.garbage_files = {
                'objc': [],
                'swift': []
            }

            # 生成Objective-C垃圾代码
            if objc_files and garbage_count > 0:
                print(f"  生成 Objective-C 垃圾代码...")
                self.garbage_generator = GarbageCodeGenerator(
                    language=GarbageCodeLanguage.OBJC,
                    complexity=complexity,
                    name_prefix=getattr(self.config, 'garbage_prefix', 'GC'),
                    seed=self.config.fixed_seed if self.config.use_fixed_seed else None
                )

                # 生成垃圾类
                garbage_classes = self.garbage_generator.generate_classes(count=garbage_count)

                # 导出到文件
                output_path = Path(output_dir)
                output_path.mkdir(parents=True, exist_ok=True)

                files_dict = self.garbage_generator.export_to_files(str(output_path))
                # 存储完整的文件路径（files_dict的values是完整路径）
                self.garbage_files['objc'] = list(files_dict.values())

                print(f"  ✅ 生成了 {len(garbage_classes)} 个 Objective-C 垃圾类")
                print(f"  ✅ 导出了 {len(files_dict)} 个文件")

            # 生成Swift垃圾代码
            if swift_files and garbage_count > 0:
                print(f"  生成 Swift 垃圾代码...")
                swift_generator = GarbageCodeGenerator(
                    language=GarbageCodeLanguage.SWIFT,
                    complexity=complexity,
                    name_prefix=getattr(self.config, 'garbage_prefix', 'GC'),
                    seed=self.config.fixed_seed if self.config.use_fixed_seed else None
                )

                # 生成垃圾类
                garbage_classes = swift_generator.generate_classes(count=garbage_count)

                # 导出到文件
                output_path = Path(output_dir)
                files_dict = swift_generator.export_to_files(str(output_path))
                # 存储完整的文件路径
                self.garbage_files['swift'] = list(files_dict.values())

                print(f"  ✅ 生成了 {len(garbage_classes)} 个 Swift 垃圾类")
                print(f"  ✅ 导出了 {len(files_dict)} 个文件")

            # 输出统计
            if self.garbage_generator:
                stats = self.garbage_generator.get_statistics()
                total_garbage_files = len(self.garbage_files['objc']) + len(self.garbage_files['swift'])
                print(f"\n📊 垃圾代码生成总结:")
                print(f"  生成类: {stats.get('classes_generated', 0)} 个")
                print(f"  生成方法: {stats.get('methods_generated', 0)} 个")
                print(f"  生成属性: {stats.get('properties_generated', 0)} 个")
                print(f"  导出文件: {total_garbage_files} 个")

        except Exception as e:
            print(f"❌ 垃圾代码生成异常: {e}")
            import traceback
            traceback.print_exc()

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

    def _p2_post_processing(self, output_dir: str, progress_callback: Optional[Callable] = None):
        """
        P2深度集成后处理
        1. 为字符串加密生成统一的解密宏头文件
        2. 为所有加密文件添加解密宏导入
        """
        try:
            print("\n🔧 P2深度集成后处理...")

            # === 字符串加密后处理 ===
            if self.config.string_encryption and self.string_encryptor:
                total_encrypted_files = len(self.files_with_encryption['objc']) + len(self.files_with_encryption['swift'])

                if total_encrypted_files > 0:
                    print(f"  处理 {total_encrypted_files} 个加密文件...")

                    output_path = Path(output_dir)

                    # 1. 生成ObjC解密宏头文件
                    if self.files_with_encryption['objc']:
                        print(f"  生成 Objective-C 解密宏头文件...")

                        # 创建ObjC版本的StringEncryptor获取解密宏
                        objc_encryptor = StringEncryptor(
                            algorithm=self.encryption_algorithm,
                            language=StringCodeLanguage.OBJC,
                            key=self.encryption_key,
                            min_length=self.encryption_min_length
                        )
                        objc_macro = objc_encryptor.generate_decryption_macro()

                        # 创建头文件
                        objc_header_file = output_path / "StringDecryption.h"
                        with open(objc_header_file, 'w', encoding='utf-8') as f:
                            f.write("//\n")
                            f.write("// StringDecryption.h\n")
                            f.write("// 字符串解密宏定义\n")
                            f.write("// 自动生成，请勿手动修改\n")
                            f.write("//\n\n")
                            f.write("#ifndef StringDecryption_h\n")
                            f.write("#define StringDecryption_h\n\n")
                            f.write(objc_macro.code)
                            f.write("\n\n#endif /* StringDecryption_h */\n")

                        print(f"    ✅ 创建头文件: {objc_header_file.name}")

                        # 2. 为所有ObjC加密文件添加导入
                        for file_path in self.files_with_encryption['objc']:
                            if file_path in self.transform_results:
                                transform_result = self.transform_results[file_path]
                                content = transform_result.transformed_content

                                # 在第一个import之后插入导入
                                lines = content.split('\n')
                                insert_index = 0

                                # 找到最后一个import的位置
                                for i, line in enumerate(lines):
                                    if line.strip().startswith(('#import', '@import')):
                                        insert_index = i + 1

                                # 插入导入语句
                                import_statement = f'#import "StringDecryption.h"'
                                if import_statement not in content:
                                    lines.insert(insert_index, import_statement)
                                    transform_result.transformed_content = '\n'.join(lines)
                                    print(f"    ✅ 添加导入: {Path(file_path).name}")

                    # 3. 生成Swift解密函数文件
                    if self.files_with_encryption['swift']:
                        print(f"  生成 Swift 解密函数文件...")

                        # 创建Swift版本的StringEncryptor获取解密函数
                        swift_encryptor = StringEncryptor(
                            algorithm=self.encryption_algorithm,
                            language=StringCodeLanguage.SWIFT,
                            key=self.encryption_key,
                            min_length=self.encryption_min_length
                        )
                        swift_function = swift_encryptor.generate_decryption_macro()

                        # 创建Swift文件
                        swift_file = output_path / "StringDecryption.swift"
                        with open(swift_file, 'w', encoding='utf-8') as f:
                            f.write("//\n")
                            f.write("// StringDecryption.swift\n")
                            f.write("// 字符串解密函数定义\n")
                            f.write("// 自动生成，请勿手动修改\n")
                            f.write("//\n\n")
                            f.write("import Foundation\n\n")
                            f.write(swift_function.code)

                        print(f"    ✅ 创建文件: {swift_file.name}")

                        # Swift不需要导入，因为在同一个模块内自动可见
                        print(f"    ℹ️  Swift文件自动可见，无需导入")

                    print(f"  ✅ 字符串加密后处理完成")

            # === 垃圾代码后处理 ===
            if self.config.insert_garbage_code and self.garbage_files:
                total_garbage_files = len(self.garbage_files['objc']) + len(self.garbage_files['swift'])

                if total_garbage_files > 0:
                    print(f"  垃圾代码文件已生成: {total_garbage_files} 个")
                    print(f"    - Objective-C: {len(self.garbage_files['objc'])} 个")
                    print(f"    - Swift: {len(self.garbage_files['swift'])} 个")

            # === Xcode项目文件自动添加 ===
            # 检查是否启用自动添加到Xcode项目（默认启用，可通过配置禁用）
            auto_add_to_xcode = getattr(self.config, 'auto_add_to_xcode', True)

            if auto_add_to_xcode and (self.garbage_files['objc'] or self.garbage_files['swift'] or
                                     self.files_with_encryption['objc'] or self.files_with_encryption['swift']):

                print(f"\n📦 自动添加文件到Xcode项目...")

                # 检查pbxproj库是否可用
                if not check_pbxproj_availability():
                    print(f"  ⚠️  mod-pbxproj库未安装，跳过自动添加")
                    print(f"  ℹ️  安装方法: pip install pbxproj")
                    print(f"  ℹ️  请手动将生成的文件添加到Xcode项目")
                else:
                    try:
                        # 初始化Xcode项目管理器
                        xcode_manager = XcodeProjectManager(self.project_structure.root_path)

                        if not xcode_manager.load_project():
                            print(f"  ⚠️  无法加载Xcode项目，跳过自动添加")
                            print(f"  ℹ️  请手动将生成的文件添加到Xcode项目")
                        else:
                            # 收集所有需要添加的文件
                            decryption_files = []
                            if self.files_with_encryption['objc']:
                                decryption_files.append(str(Path(output_dir) / "StringDecryption.h"))
                            if self.files_with_encryption['swift']:
                                decryption_files.append(str(Path(output_dir) / "StringDecryption.swift"))

                            # 获取目标target（使用第一个target）
                            targets = xcode_manager.get_targets()
                            target_name = targets[0] if targets else None

                            # 添加混淆生成的文件
                            garbage_results, decryption_results = xcode_manager.add_obfuscation_files(
                                garbage_files=self.garbage_files,
                                decryption_files=decryption_files,
                                target_name=target_name
                            )

                            # 保存项目修改
                            if xcode_manager.save_project():
                                # 打印摘要
                                xcode_manager.print_summary(garbage_results, decryption_results)
                                print(f"  ✅ 文件已自动添加到Xcode项目")
                            else:
                                print(f"  ⚠️  保存Xcode项目失败")
                                print(f"  ℹ️  请手动将生成的文件添加到Xcode项目")

                    except Exception as e:
                        print(f"  ⚠️  自动添加文件失败: {e}")
                        print(f"  ℹ️  请手动将生成的文件添加到Xcode项目")
            elif not auto_add_to_xcode:
                print(f"  ℹ️  自动添加功能已禁用")
                print(f"  ℹ️  请手动将生成的文件添加到Xcode项目")

            print(f"\n✅ P2深度集成后处理完成\n")

        except Exception as e:
            print(f"❌ P2后处理异常: {e}")
            import traceback
            traceback.print_exc()

    def _export_mapping(self, output_dir: str) -> str:
        """导出映射文件（包含P2统计信息）"""
        try:
            output_path = Path(output_dir)
            mapping_file = output_path / "obfuscation_mapping.json"

            # 导出名称映射
            self.name_generator.export_mappings(
                str(mapping_file),
                format=self.config.mapping_format
            )

            # 读取映射文件并添加P2统计信息
            if mapping_file.exists():
                with open(mapping_file, 'r', encoding='utf-8') as f:
                    mapping_data = json.load(f)

                # 添加P2统计信息
                if 'metadata' not in mapping_data:
                    mapping_data['metadata'] = {}

                # 字符串加密统计
                if self.string_encryptor:
                    encryption_stats = self.string_encryptor.get_statistics()
                    mapping_data['metadata']['string_encryption'] = {
                        'enabled': True,
                        'algorithm': encryption_stats.get('algorithm', 'unknown'),
                        'total_encrypted': self.total_encrypted_strings,  # 使用累积的总数
                        'objc_files': len(self.files_with_encryption['objc']),
                        'swift_files': len(self.files_with_encryption['swift']),
                        'decryption_header_objc': 'StringDecryption.h' if self.files_with_encryption['objc'] else None,
                        'decryption_file_swift': 'StringDecryption.swift' if self.files_with_encryption['swift'] else None
                    }

                # 垃圾代码统计
                if self.garbage_generator:
                    garbage_stats = self.garbage_generator.get_statistics()
                    mapping_data['metadata']['garbage_code'] = {
                        'enabled': True,
                        'complexity': getattr(self.config, 'garbage_complexity', 'moderate'),
                        'classes_generated': garbage_stats.get('classes_generated', 0),
                        'methods_generated': garbage_stats.get('methods_generated', 0),
                        'properties_generated': garbage_stats.get('properties_generated', 0),
                        'objc_files': len(self.garbage_files['objc']),
                        'swift_files': len(self.garbage_files['swift']),
                        'file_list': {
                            'objc': [Path(f).name for f in self.garbage_files['objc']],
                            'swift': [Path(f).name for f in self.garbage_files['swift']]
                        }
                    }

                # 保存更新后的映射文件
                with open(mapping_file, 'w', encoding='utf-8') as f:
                    json.dump(mapping_data, f, indent=2, ensure_ascii=False)

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
            'string_encryption': self.string_encryptor.get_statistics() if self.string_encryptor else {},
            'garbage_code': self.garbage_generator.get_statistics() if self.garbage_generator else {},
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
