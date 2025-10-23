"""
源文件处理器

负责源代码解析和转换，支持增量编译、并行处理和缓存
"""

import os
from pathlib import Path
from typing import Callable, Dict, List, Optional

try:
    from ..code_parser import CodeParser, ParsedFile
    from ..code_transformer import CodeTransformer, TransformResult
    from ..config_manager import ObfuscationConfig
    from ..incremental_manager import FileChangeType, IncrementalManager
    from ..name_generator import NameGenerator
    from ..project_analyzer import ProjectStructure
    from ..whitelist_manager import WhitelistManager
except ImportError:
    from code_parser import CodeParser, ParsedFile
    from code_transformer import CodeTransformer, TransformResult
    from config_manager import ObfuscationConfig
    from incremental_manager import FileChangeType, IncrementalManager
    from name_generator import NameGenerator
    from project_analyzer import ProjectStructure
    from whitelist_manager import WhitelistManager


class SourceProcessor:
    """源文件处理器"""

    def __init__(self, config: ObfuscationConfig,
                 project_structure: ProjectStructure,
                 whitelist_manager: WhitelistManager,
                 name_generator: NameGenerator):
        """
        初始化

        Args:
            config: 混淆配置
            project_structure: 项目结构
            whitelist_manager: 白名单管理器
            name_generator: 名称生成器
        """
        self.config = config
        self.project_structure = project_structure
        self.whitelist_manager = whitelist_manager
        self.name_generator = name_generator

        self.code_parser: Optional[CodeParser] = None
        self.code_transformer: Optional[CodeTransformer] = None
        self.incremental_manager: Optional[IncrementalManager] = None

        self.parsed_files: Dict[str, ParsedFile] = {}
        self.transform_results: Dict[str, TransformResult] = {}
        self.file_changes: Dict[FileChangeType, List[str]] = {}

    def parse_source_files(self, progress_callback: Optional[Callable] = None) -> bool:
        """
        解析源文件（支持增量编译、并行处理和缓存）

        Args:
            progress_callback: 进度回调

        Returns:
            bool: 是否成功
        """
        try:
            # 获取所有源文件
            from ..project_analyzer import ProjectAnalyzer
            project_analyzer = ProjectAnalyzer(self.project_structure.root_path)
            project_analyzer.project_structure = self.project_structure  # 复用已分析的结构

            source_files = project_analyzer.get_source_files(
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
                    from ..parse_cache_manager import ParseCacheManager

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
                    from ..parallel_parser import ParallelCodeParser

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

    def transform_code(self, progress_callback: Optional[Callable] = None) -> bool:
        """
        转换代码（支持多进程并行）

        Args:
            progress_callback: 进度回调

        Returns:
            bool: 是否成功
        """
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
                    from ..multiprocess_transformer import MultiProcessTransformer

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
