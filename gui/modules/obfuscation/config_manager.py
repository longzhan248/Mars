"""
配置管理器 - 负责混淆配置的加载、保存、验证和管理

支持:
1. 配置文件的读写(JSON格式)
2. 内置配置模板(最小化/标准/激进)
3. 配置验证和默认值填充
4. 配置继承和合并
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from enum import Enum


class ObfuscationLevel(Enum):
    """混淆级别"""
    MINIMAL = "minimal"      # 最小化混淆
    STANDARD = "standard"    # 标准混淆
    AGGRESSIVE = "aggressive" # 激进混淆


@dataclass
class ObfuscationConfig:
    """混淆配置数据类"""

    # 基本信息
    name: str = "default"
    description: str = ""
    level: str = "standard"

    # 混淆开关
    class_names: bool = True
    method_names: bool = True
    property_names: bool = True
    parameter_names: bool = True
    local_variable_names: bool = True
    protocol_names: bool = True
    enum_names: bool = True
    constant_names: bool = True

    # 高级混淆
    insert_garbage_code: bool = False
    shuffle_method_order: bool = False
    string_encryption: bool = False
    modify_color_values: bool = False
    modify_resource_files: bool = False

    # 名称生成策略
    naming_strategy: str = "random"  # random, prefix, pattern, dictionary
    name_prefix: str = "WHC"
    name_pattern: str = "{prefix}{type}{index}"
    min_name_length: int = 8
    max_name_length: int = 20

    # 确定性混淆
    use_fixed_seed: bool = False
    fixed_seed: Optional[str] = None

    # 增量混淆
    enable_incremental: bool = False
    mapping_file: Optional[str] = None

    # 白名单
    whitelist_system_api: bool = True
    whitelist_third_party: bool = True
    auto_detect_third_party: bool = True
    custom_whitelist: List[str] = field(default_factory=list)

    # 性能优化
    parallel_processing: bool = True
    max_workers: int = 8
    batch_size: int = 100

    # 输出配置
    output_mapping: bool = True
    mapping_format: str = "json"  # json, csv
    backup_original: bool = True
    output_report: bool = True

    # 文件过滤
    include_patterns: List[str] = field(default_factory=lambda: ["*.h", "*.m", "*.swift"])
    exclude_patterns: List[str] = field(default_factory=lambda: ["Pods/*", "*.framework/*"])
    exclude_directories: List[str] = field(default_factory=lambda: ["Pods", "Carthage", "Build"])

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ObfuscationConfig':
        """从字典创建"""
        # 过滤掉不存在的字段
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)


class ConfigManager:
    """配置管理器"""

    # 内置配置模板
    TEMPLATES = {
        "minimal": {
            "name": "minimal",
            "description": "最小化混淆 - 仅混淆类名和方法名，适合快速调试",
            "level": "minimal",
            "class_names": True,
            "method_names": True,
            "property_names": False,
            "parameter_names": False,
            "local_variable_names": False,
            "protocol_names": False,
            "enum_names": False,
            "constant_names": False,
            "insert_garbage_code": False,
            "shuffle_method_order": False,
            "string_encryption": False,
            "modify_color_values": False,
            "modify_resource_files": False,
            "naming_strategy": "prefix",
            "name_prefix": "WHC",
            "min_name_length": 8,
            "max_name_length": 12,
            "use_fixed_seed": False,  # 默认不使用固定种子
            "whitelist_system_api": True,
            "whitelist_third_party": True,
            "parallel_processing": True,
        },
        "standard": {
            "name": "standard",
            "description": "标准混淆 - 平衡的混淆策略，适合日常开发",
            "level": "standard",
            "class_names": True,
            "method_names": True,
            "property_names": True,
            "parameter_names": True,
            "local_variable_names": False,
            "protocol_names": True,
            "enum_names": True,
            "constant_names": True,
            "insert_garbage_code": True,
            "shuffle_method_order": True,
            "string_encryption": False,
            "modify_color_values": True,
            "modify_resource_files": False,
            "naming_strategy": "random",
            "name_prefix": "WHC",
            "min_name_length": 10,
            "max_name_length": 15,
            "use_fixed_seed": False,  # 标准模板默认不使用固定种子
            "whitelist_system_api": True,
            "whitelist_third_party": True,
            "auto_detect_third_party": True,
            "parallel_processing": True,
            "max_workers": 8,
        },
        "aggressive": {
            "name": "aggressive",
            "description": "激进混淆 - 最强混淆力度，适合正式发布",
            "level": "aggressive",
            "class_names": True,
            "method_names": True,
            "property_names": True,
            "parameter_names": True,
            "local_variable_names": True,
            "protocol_names": True,
            "enum_names": True,
            "constant_names": True,
            "insert_garbage_code": True,
            "shuffle_method_order": True,
            "string_encryption": True,
            "modify_color_values": True,
            "modify_resource_files": True,
            "naming_strategy": "random",
            "name_prefix": "",
            "min_name_length": 12,
            "max_name_length": 20,
            "use_fixed_seed": False,  # 默认不使用固定种子
            "whitelist_system_api": True,
            "whitelist_third_party": True,
            "auto_detect_third_party": True,
            "parallel_processing": True,
            "max_workers": 16,
            "batch_size": 200,
        }
    }

    def __init__(self, config_dir: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            config_dir: 配置文件目录，默认为用户目录下的.ios_obfuscation
        """
        if config_dir is None:
            config_dir = os.path.join(os.path.expanduser("~"), ".ios_obfuscation")

        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.configs_dir = self.config_dir / "configs"
        self.configs_dir.mkdir(exist_ok=True)

        self.current_config: Optional[ObfuscationConfig] = None

    def get_template(self, level: str) -> ObfuscationConfig:
        """
        获取内置模板配置

        Args:
            level: 模板级别 (minimal/standard/aggressive)

        Returns:
            ObfuscationConfig: 配置对象
        """
        if level not in self.TEMPLATES:
            raise ValueError(f"未知的模板级别: {level}，可选: {list(self.TEMPLATES.keys())}")

        template_data = self.TEMPLATES[level].copy()
        return ObfuscationConfig.from_dict(template_data)

    def list_templates(self) -> List[Dict[str, str]]:
        """
        列出所有内置模板

        Returns:
            List[Dict]: 模板信息列表 [{"name": "minimal", "description": "..."}]
        """
        return [
            {
                "name": template["name"],
                "description": template["description"],
                "level": template["level"]
            }
            for template in self.TEMPLATES.values()
        ]

    def load_config(self, config_path: str) -> ObfuscationConfig:
        """
        从文件加载配置

        Args:
            config_path: 配置文件路径

        Returns:
            ObfuscationConfig: 配置对象
        """
        config_file = Path(config_path)

        if not config_file.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            config = ObfuscationConfig.from_dict(data)
            self.current_config = config
            return config

        except json.JSONDecodeError as e:
            raise ValueError(f"配置文件格式错误: {e}")
        except Exception as e:
            raise RuntimeError(f"加载配置失败: {e}")

    def save_config(self, config: ObfuscationConfig, config_path: Optional[str] = None) -> str:
        """
        保存配置到文件

        Args:
            config: 配置对象
            config_path: 保存路径，如果为None则保存到默认位置

        Returns:
            str: 保存的文件路径
        """
        if config_path is None:
            config_path = self.configs_dir / f"{config.name}.json"

        config_file = Path(config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config.to_dict(), f, indent=2, ensure_ascii=False)

            return str(config_file)

        except Exception as e:
            raise RuntimeError(f"保存配置失败: {e}")

    def list_saved_configs(self) -> List[Dict[str, str]]:
        """
        列出所有已保存的配置

        Returns:
            List[Dict]: 配置信息列表 [{"name": "xxx", "path": "...", "description": "..."}]
        """
        configs = []

        for config_file in self.configs_dir.glob("*.json"):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                configs.append({
                    "name": data.get("name", config_file.stem),
                    "path": str(config_file),
                    "description": data.get("description", ""),
                    "level": data.get("level", "custom")
                })
            except Exception:
                continue

        return configs

    def delete_config(self, config_name: str) -> bool:
        """
        删除已保存的配置

        Args:
            config_name: 配置名称

        Returns:
            bool: 是否成功删除
        """
        config_file = self.configs_dir / f"{config_name}.json"

        if config_file.exists():
            config_file.unlink()
            return True

        return False

    def validate_config(self, config: ObfuscationConfig) -> tuple[bool, List[str]]:
        """
        验证配置的有效性

        Args:
            config: 配置对象

        Returns:
            tuple: (是否有效, 错误信息列表)
        """
        errors = []

        # 检查名称生成策略
        valid_strategies = ["random", "prefix", "pattern", "dictionary"]
        if config.naming_strategy not in valid_strategies:
            errors.append(f"无效的命名策略: {config.naming_strategy}，可选: {valid_strategies}")

        # 检查名称长度
        if config.min_name_length < 3:
            errors.append(f"最小名称长度不能小于3: {config.min_name_length}")

        if config.max_name_length < config.min_name_length:
            errors.append(f"最大名称长度不能小于最小名称长度: {config.max_name_length} < {config.min_name_length}")

        # 检查线程数
        if config.max_workers < 1:
            errors.append(f"最大线程数不能小于1: {config.max_workers}")

        # 检查批处理大小
        if config.batch_size < 1:
            errors.append(f"批处理大小不能小于1: {config.batch_size}")

        # 检查映射格式
        valid_formats = ["json", "csv"]
        if config.mapping_format not in valid_formats:
            errors.append(f"无效的映射格式: {config.mapping_format}，可选: {valid_formats}")

        # 检查增量混淆配置
        if config.enable_incremental and not config.mapping_file:
            errors.append("启用增量混淆时必须指定映射文件路径")

        # 检查确定性混淆配置
        if config.use_fixed_seed and not config.fixed_seed:
            errors.append("启用确定性混淆时必须指定固定种子")

        return len(errors) == 0, errors

    def merge_configs(self, base: ObfuscationConfig, override: Dict[str, Any]) -> ObfuscationConfig:
        """
        合并配置（基础配置 + 覆盖配置）

        Args:
            base: 基础配置对象
            override: 覆盖配置字典

        Returns:
            ObfuscationConfig: 合并后的配置对象
        """
        base_dict = base.to_dict()
        base_dict.update(override)
        return ObfuscationConfig.from_dict(base_dict)

    def create_config_from_template(self, template_level: str,
                                   custom_name: str,
                                   overrides: Optional[Dict[str, Any]] = None) -> ObfuscationConfig:
        """
        从模板创建自定义配置

        Args:
            template_level: 模板级别 (minimal/standard/aggressive)
            custom_name: 自定义配置名称
            overrides: 要覆盖的配置项

        Returns:
            ObfuscationConfig: 新配置对象
        """
        config = self.get_template(template_level)
        config.name = custom_name

        if overrides:
            config = self.merge_configs(config, overrides)

        return config

    def export_config_template(self, output_path: str):
        """
        导出配置模板文件（供用户参考）

        Args:
            output_path: 输出文件路径
        """
        template_doc = {
            "templates": self.TEMPLATES,
            "description": "iOS代码混淆配置模板",
            "usage": {
                "1": "选择一个模板复制其内容",
                "2": "修改name和description字段",
                "3": "根据需要调整混淆选项",
                "4": "保存为新的配置文件"
            },
            "options_description": {
                "class_names": "是否混淆类名",
                "method_names": "是否混淆方法名",
                "property_names": "是否混淆属性名",
                "parameter_names": "是否混淆参数名",
                "local_variable_names": "是否混淆局部变量名",
                "protocol_names": "是否混淆协议名",
                "enum_names": "是否混淆枚举名",
                "constant_names": "是否混淆常量名",
                "insert_garbage_code": "是否插入垃圾代码",
                "shuffle_method_order": "是否打乱方法顺序",
                "string_encryption": "是否加密字符串",
                "modify_color_values": "是否修改颜色值",
                "modify_resource_files": "是否修改资源文件",
                "naming_strategy": "命名策略: random(随机)/prefix(前缀)/pattern(模式)/dictionary(词典)",
                "name_prefix": "名称前缀",
                "min_name_length": "最小名称长度",
                "max_name_length": "最大名称长度",
                "use_fixed_seed": "是否使用固定种子(确定性混淆)",
                "fixed_seed": "固定种子值",
                "enable_incremental": "是否启用增量混淆",
                "whitelist_system_api": "是否白名单系统API",
                "whitelist_third_party": "是否白名单第三方库",
                "auto_detect_third_party": "是否自动检测第三方库",
                "parallel_processing": "是否并行处理",
                "max_workers": "最大线程数"
            }
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(template_doc, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    # 测试代码
    manager = ConfigManager()

    # 1. 列出内置模板
    print("内置模板:")
    for template in manager.list_templates():
        print(f"  - {template['name']}: {template['description']}")

    # 2. 获取标准模板
    standard_config = manager.get_template("standard")
    print(f"\n标准配置: {standard_config.name}")
    print(f"  混淆类名: {standard_config.class_names}")
    print(f"  命名策略: {standard_config.naming_strategy}")

    # 3. 创建自定义配置
    custom_config = manager.create_config_from_template(
        "standard",
        "my_project",
        {"name_prefix": "MP", "max_workers": 4}
    )
    print(f"\n自定义配置: {custom_config.name}")
    print(f"  名称前缀: {custom_config.name_prefix}")
    print(f"  最大线程: {custom_config.max_workers}")

    # 4. 验证配置
    is_valid, errors = manager.validate_config(custom_config)
    print(f"\n配置验证: {'通过' if is_valid else '失败'}")
    if errors:
        for error in errors:
            print(f"  - {error}")

    # 5. 保存配置
    saved_path = manager.save_config(custom_config)
    print(f"\n配置已保存到: {saved_path}")

    # 6. 导出模板文档
    template_path = manager.config_dir / "config_template.json"
    manager.export_config_template(str(template_path))
    print(f"模板文档已导出到: {template_path}")
