"""
项目初始化处理器

负责项目分析、白名单初始化和名称生成器初始化
"""

from typing import Callable, Optional

try:
    from ..config_manager import ObfuscationConfig
    from ..name_generator import NameGenerator, NamingStrategy
    from ..project_analyzer import ProjectAnalyzer, ProjectStructure
    from ..whitelist_manager import WhitelistManager, WhitelistType
except ImportError:
    from config_manager import ObfuscationConfig
    from name_generator import NameGenerator, NamingStrategy
    from project_analyzer import ProjectAnalyzer, ProjectStructure
    from whitelist_manager import WhitelistManager, WhitelistType


class ProjectInitializer:
    """项目初始化处理器"""

    def __init__(self, config: ObfuscationConfig):
        """
        初始化

        Args:
            config: 混淆配置
        """
        self.config = config
        self.project_analyzer: Optional[ProjectAnalyzer] = None
        self.whitelist_manager: Optional[WhitelistManager] = None
        self.name_generator: Optional[NameGenerator] = None
        self.project_structure: Optional[ProjectStructure] = None

    def analyze_project(self, project_path: str,
                       progress_callback: Optional[Callable] = None) -> bool:
        """
        分析项目结构

        Args:
            project_path: 项目路径
            progress_callback: 进度回调

        Returns:
            bool: 是否成功
        """
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

    def initialize_whitelist(self, project_path: str) -> bool:
        """
        初始化白名单

        Args:
            project_path: 项目路径

        Returns:
            bool: 是否成功
        """
        try:
            self.whitelist_manager = WhitelistManager(project_path=project_path)

            # 自动检测第三方库
            if self.config.auto_detect_third_party:
                detected = self.whitelist_manager.auto_detect_third_party()
                print(f"自动检测到 {detected} 个第三方库")

            # 添加自定义白名单
            for item in self.config.custom_whitelist:
                self.whitelist_manager.add_custom(item, WhitelistType.CUSTOM)

            return True

        except Exception as e:
            print(f"白名单初始化失败: {e}")
            return False

    def initialize_name_generator(self):
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
