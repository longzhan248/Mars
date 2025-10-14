"""
iOS代码混淆CLI工具 - 命令行接口

支持:
1. 完整的命令行参数解析
2. 配置文件和命令行参数组合
3. Jenkins/CI集成支持
4. 结构化日志输出
5. 明确的返回码

使用示例:
    # 基础混淆
    python obfuscation_cli.py --project /path/to/project --output /path/to/output

    # 使用配置模板
    python obfuscation_cli.py --project /path/to/project --output /path/to/output --template standard

    # 自定义配置
    python obfuscation_cli.py --project /path/to/project --output /path/to/output \\
        --class-names --method-names --property-names \\
        --prefix "WHC" --seed "my_seed"

    # 增量混淆
    python obfuscation_cli.py --project /path/to/project --output /path/to/output \\
        --incremental --mapping /path/to/old_mapping.json

    # 只分析不混淆
    python obfuscation_cli.py --project /path/to/project --analyze-only \\
        --report /path/to/report.json
"""

import sys
import os
import argparse
import json
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

try:
    from .config_manager import ObfuscationConfig, ConfigManager
    from .obfuscation_engine import ObfuscationEngine, ObfuscationResult
    from .project_analyzer import ProjectAnalyzer
except ImportError:
    from config_manager import ObfuscationConfig, ConfigManager
    from obfuscation_engine import ObfuscationEngine, ObfuscationResult
    from project_analyzer import ProjectAnalyzer


# 版本信息
__version__ = "2.1.0"
__author__ = "iOS Obfuscation Team"
__license__ = "MIT"

# 返回码定义
EXIT_SUCCESS = 0
EXIT_INVALID_ARGS = 1
EXIT_PROJECT_NOT_FOUND = 2
EXIT_ANALYSIS_FAILED = 3
EXIT_OBFUSCATION_FAILED = 4
EXIT_OUTPUT_FAILED = 5


class ObfuscationCLI:
    """CLI接口主类"""

    def __init__(self):
        self.logger = self._setup_logger()
        self.config_manager = ConfigManager()

    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger('obfuscation_cli')
        logger.setLevel(logging.INFO)

        # 控制台输出
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        # 格式化
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)

        logger.addHandler(console_handler)
        return logger

    def create_parser(self) -> argparse.ArgumentParser:
        """创建命令行参数解析器"""
        parser = argparse.ArgumentParser(
            description='iOS代码混淆工具 - 命令行接口',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
示例:
  # 基础混淆
  %(prog)s --project /path/to/project --output /path/to/output

  # 使用配置模板
  %(prog)s --project /path/to/project --output /path/to/output --template standard

  # 自定义配置
  %(prog)s --project /path/to/project --output /path/to/output \\
      --class-names --method-names --property-names \\
      --prefix "WHC" --seed "my_seed"

  # 增量混淆
  %(prog)s --project /path/to/project --output /path/to/output \\
      --incremental --mapping /path/to/old_mapping.json

  # 只分析不混淆
  %(prog)s --project /path/to/project --analyze-only \\
      --report /path/to/report.json
            """
        )

        # 版本信息
        parser.add_argument(
            '-v', '--version',
            action='version',
            version=f'%(prog)s {__version__}'
        )

        # 必需参数
        parser.add_argument(
            '--project',
            type=str,
            required=True,
            help='iOS项目路径'
        )

        parser.add_argument(
            '--output',
            type=str,
            help='混淆后的输出目录（分析模式下可选）'
        )

        # 配置选项
        config_group = parser.add_argument_group('配置选项')

        config_group.add_argument(
            '--template',
            type=str,
            choices=['minimal', 'standard', 'aggressive'],
            help='使用配置模板（minimal/standard/aggressive）'
        )

        config_group.add_argument(
            '--config-file',
            type=str,
            help='从JSON文件加载配置'
        )

        # 混淆选项
        obf_group = parser.add_argument_group('混淆选项')

        obf_group.add_argument(
            '--class-names',
            action='store_true',
            help='混淆类名'
        )

        obf_group.add_argument(
            '--method-names',
            action='store_true',
            help='混淆方法名'
        )

        obf_group.add_argument(
            '--property-names',
            action='store_true',
            help='混淆属性名'
        )

        obf_group.add_argument(
            '--protocol-names',
            action='store_true',
            help='混淆协议名'
        )

        obf_group.add_argument(
            '--enum-names',
            action='store_true',
            help='混淆枚举名'
        )

        # 命名策略
        naming_group = parser.add_argument_group('命名策略')

        naming_group.add_argument(
            '--strategy',
            type=str,
            choices=['random', 'prefix', 'pattern', 'dictionary'],
            default='random',
            help='命名策略'
        )

        naming_group.add_argument(
            '--prefix',
            type=str,
            help='名称前缀'
        )

        naming_group.add_argument(
            '--pattern',
            type=str,
            help='命名模式（例如：{prefix}{type}{index}）'
        )

        naming_group.add_argument(
            '--min-length',
            type=int,
            help='最小名称长度'
        )

        naming_group.add_argument(
            '--max-length',
            type=int,
            help='最大名称长度'
        )

        naming_group.add_argument(
            '--seed',
            type=str,
            help='固定种子（确定性混淆）'
        )

        # 增量混淆
        incremental_group = parser.add_argument_group('增量混淆')

        incremental_group.add_argument(
            '--incremental',
            action='store_true',
            help='启用增量混淆'
        )

        incremental_group.add_argument(
            '--mapping',
            type=str,
            help='旧版本的映射文件路径'
        )

        # 白名单
        whitelist_group = parser.add_argument_group('白名单')

        whitelist_group.add_argument(
            '--no-system-api',
            action='store_true',
            help='不自动白名单系统API'
        )

        whitelist_group.add_argument(
            '--no-third-party',
            action='store_true',
            help='不自动白名单第三方库'
        )

        whitelist_group.add_argument(
            '--custom-whitelist',
            type=str,
            nargs='+',
            help='自定义白名单列表'
        )

        # 分析模式
        analysis_group = parser.add_argument_group('分析模式')

        analysis_group.add_argument(
            '--analyze-only',
            action='store_true',
            help='仅分析项目，不执行混淆'
        )

        analysis_group.add_argument(
            '--report',
            type=str,
            help='分析报告输出路径'
        )

        # 输出控制
        output_group = parser.add_argument_group('输出控制')

        output_group.add_argument(
            '--verbose',
            action='store_true',
            help='详细输出'
        )

        output_group.add_argument(
            '--quiet',
            action='store_true',
            help='静默模式，仅输出错误'
        )

        output_group.add_argument(
            '--json',
            action='store_true',
            help='以JSON格式输出结果'
        )

        output_group.add_argument(
            '--log-file',
            type=str,
            help='日志文件路径'
        )

        return parser

    def validate_args(self, args: argparse.Namespace) -> bool:
        """验证命令行参数"""
        # 检查项目路径
        if not os.path.exists(args.project):
            self.logger.error(f"项目路径不存在: {args.project}")
            return False

        if not os.path.isdir(args.project):
            self.logger.error(f"项目路径不是目录: {args.project}")
            return False

        # 检查输出目录（非分析模式必需）
        if not args.analyze_only and not args.output:
            self.logger.error("非分析模式下必须指定 --output 参数")
            return False

        # 检查配置文件
        if args.config_file and not os.path.exists(args.config_file):
            self.logger.error(f"配置文件不存在: {args.config_file}")
            return False

        # 检查映射文件
        if args.incremental and args.mapping:
            if not os.path.exists(args.mapping):
                self.logger.error(f"映射文件不存在: {args.mapping}")
                return False

        # 检查冲突选项
        if args.verbose and args.quiet:
            self.logger.error("--verbose 和 --quiet 不能同时使用")
            return False

        return True

    def build_config(self, args: argparse.Namespace) -> ObfuscationConfig:
        """根据命令行参数构建配置"""
        # 1. 从模板或文件加载基础配置
        if args.config_file:
            self.logger.info(f"从文件加载配置: {args.config_file}")
            config = self.config_manager.load_config(args.config_file)
        elif args.template:
            self.logger.info(f"使用配置模板: {args.template}")
            config = self.config_manager.get_template(args.template)
        else:
            # 默认使用standard模板
            config = self.config_manager.get_template("standard")

        # 2. 应用命令行参数覆盖
        if args.class_names:
            config.class_names = True
        if args.method_names:
            config.method_names = True
        if args.property_names:
            config.property_names = True
        if args.protocol_names:
            config.protocol_names = True
        if args.enum_names:
            config.enum_names = True

        # 命名策略
        if args.strategy:
            config.naming_strategy = args.strategy
        if args.prefix:
            config.name_prefix = args.prefix
        if args.pattern:
            config.name_pattern = args.pattern
        if args.min_length:
            config.min_name_length = args.min_length
        if args.max_length:
            config.max_name_length = args.max_length

        # 确定性混淆
        if args.seed:
            config.use_fixed_seed = True
            config.fixed_seed = args.seed

        # 增量混淆
        if args.incremental:
            config.enable_incremental = True
            if args.mapping:
                config.mapping_file = args.mapping

        # 白名单
        if args.no_system_api:
            config.whitelist_system_api = False
        if args.no_third_party:
            config.whitelist_third_party = False
            config.auto_detect_third_party = False
        if args.custom_whitelist:
            config.custom_whitelist = args.custom_whitelist

        return config

    def setup_logging(self, args: argparse.Namespace):
        """根据参数设置日志级别"""
        if args.verbose:
            self.logger.setLevel(logging.DEBUG)
            for handler in self.logger.handlers:
                handler.setLevel(logging.DEBUG)
        elif args.quiet:
            self.logger.setLevel(logging.ERROR)
            for handler in self.logger.handlers:
                handler.setLevel(logging.ERROR)

        # 添加文件日志
        if args.log_file:
            file_handler = logging.FileHandler(args.log_file)
            file_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter(
                '[%(asctime)s] %(levelname)s: %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def analyze_project(self, project_path: str, report_path: Optional[str] = None) -> bool:
        """分析项目"""
        self.logger.info(f"开始分析项目: {project_path}")

        try:
            analyzer = ProjectAnalyzer(project_path)

            def progress_callback(progress, message):
                self.logger.info(f"[{progress*100:.0f}%] {message}")

            structure = analyzer.analyze(callback=progress_callback)

            # 输出分析结果
            self.logger.info("=" * 60)
            self.logger.info("项目分析完成")
            self.logger.info("=" * 60)
            self.logger.info(f"项目名称: {structure.project_name}")
            self.logger.info(f"项目类型: {structure.project_type.value}")
            self.logger.info(f"ObjC头文件: {len(structure.objc_headers)}")
            self.logger.info(f"ObjC源文件: {len(structure.objc_sources)}")
            self.logger.info(f"Swift文件: {len(structure.swift_files)}")
            self.logger.info(f"总文件数: {structure.total_files}")
            self.logger.info(f"总代码行数: {structure.total_lines}")
            self.logger.info(f"CocoaPods依赖: {len(structure.cocoapods_dependencies)}")
            self.logger.info(f"SPM依赖: {len(structure.spm_dependencies)}")
            self.logger.info("=" * 60)

            # 导出报告
            if report_path:
                analyzer.export_report(report_path)
                self.logger.info(f"分析报告已导出: {report_path}")

            return True

        except Exception as e:
            self.logger.error(f"项目分析失败: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
            return False

    def obfuscate_project(self, project_path: str, output_dir: str, config: ObfuscationConfig) -> ObfuscationResult:
        """执行混淆"""
        self.logger.info("=" * 60)
        self.logger.info("开始混淆流程")
        self.logger.info("=" * 60)
        self.logger.info(f"项目路径: {project_path}")
        self.logger.info(f"输出目录: {output_dir}")
        self.logger.info(f"配置名称: {config.name}")
        self.logger.info(f"命名策略: {config.naming_strategy}")
        self.logger.info("=" * 60)

        # 创建引擎
        engine = ObfuscationEngine(config)

        # 进度回调
        def progress_callback(progress, message):
            self.logger.info(f"[{progress*100:.0f}%] {message}")

        # 执行混淆
        result = engine.obfuscate(
            project_path=project_path,
            output_dir=output_dir,
            progress_callback=progress_callback
        )

        return result

    def print_result(self, result: ObfuscationResult, json_output: bool = False):
        """输出混淆结果"""
        if json_output:
            # JSON格式输出
            result_dict = {
                'success': result.success,
                'project_name': result.project_name,
                'output_dir': result.output_dir,
                'files_processed': result.files_processed,
                'files_failed': result.files_failed,
                'total_replacements': result.total_replacements,
                'elapsed_time': result.elapsed_time,
                'mapping_file': result.mapping_file,
                'errors': result.errors,
                'warnings': result.warnings
            }
            print(json.dumps(result_dict, indent=2, ensure_ascii=False))
        else:
            # 人类可读格式
            self.logger.info("=" * 60)
            if result.success:
                self.logger.info("✅ 混淆完成")
            else:
                self.logger.error("❌ 混淆失败")
            self.logger.info("=" * 60)
            self.logger.info(f"项目名称: {result.project_name}")
            self.logger.info(f"输出目录: {result.output_dir}")
            self.logger.info(f"处理文件: {result.files_processed}")
            self.logger.info(f"失败文件: {result.files_failed}")
            self.logger.info(f"替换次数: {result.total_replacements}")
            self.logger.info(f"耗时: {result.elapsed_time:.2f}秒")

            if result.mapping_file:
                self.logger.info(f"映射文件: {result.mapping_file}")

            if result.errors:
                self.logger.error(f"错误数: {len(result.errors)}")
                for error in result.errors:
                    self.logger.error(f"  - {error}")

            if result.warnings:
                self.logger.warning(f"警告数: {len(result.warnings)}")
                for warning in result.warnings:
                    self.logger.warning(f"  - {warning}")

            self.logger.info("=" * 60)

    def run(self, argv=None) -> int:
        """主执行函数"""
        # 解析参数
        parser = self.create_parser()
        args = parser.parse_args(argv)

        # 设置日志
        self.setup_logging(args)

        # 验证参数
        if not self.validate_args(args):
            return EXIT_INVALID_ARGS

        # 分析模式
        if args.analyze_only:
            success = self.analyze_project(args.project, args.report)
            return EXIT_SUCCESS if success else EXIT_ANALYSIS_FAILED

        # 混淆模式
        try:
            # 构建配置
            config = self.build_config(args)

            # 验证配置
            is_valid, errors = self.config_manager.validate_config(config)
            if not is_valid:
                self.logger.error("配置验证失败:")
                for error in errors:
                    self.logger.error(f"  - {error}")
                return EXIT_INVALID_ARGS

            # 执行混淆
            result = self.obfuscate_project(args.project, args.output, config)

            # 输出结果
            self.print_result(result, args.json)

            # 返回退出码
            if result.success:
                return EXIT_SUCCESS
            else:
                return EXIT_OBFUSCATION_FAILED

        except Exception as e:
            self.logger.error(f"执行失败: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
            return EXIT_OBFUSCATION_FAILED


def main():
    """命令行入口"""
    cli = ObfuscationCLI()
    exit_code = cli.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
