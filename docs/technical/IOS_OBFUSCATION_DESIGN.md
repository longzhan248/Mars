# iOS代码混淆功能设计文档

## 文档信息
- **创建日期**: 2025-10-13
- **版本**: v1.0.0
- **参考项目**: WHC_ConfuseSoftware
- **目标**: 为Mars日志分析工具添加iOS原生项目混淆功能

---

## 一、项目背景

### 1.1 WHC_ConfuseSoftware 核心功能分析

根据对WHC_ConfuseSoftware项目的分析，该商业混淆软件提供以下核心功能：

#### iOS原生混淆能力
1. **文件名混淆** - 修改.h/.m/.swift文件名
2. **类名混淆** - 修改Objective-C和Swift类名
3. **函数名混淆** - 修改方法签名
4. **属性名混淆** - 修改属性和变量名
5. **资源文件混淆** - 修改图片、音频等资源文件名
6. **垃圾代码插入** - 生成并插入无用代码
7. **字符串加密** - 加密硬编码字符串
8. **UIColor值混淆** - 修改颜色值
9. **Xib/Storyboard混淆** - 修改控件ID
10. **函数顺序打乱** - 改变函数定义顺序
11. **协议名称混淆** - 修改Protocol名称
12. **宏定义混淆** - 修改宏名称
13. **枚举混淆** - 修改枚举类型和值
14. **局部变量混淆** - 修改函数内局部变量名

#### 高级功能
- **函数拆分** - 将函数拆分成多个子函数
- **代码格式化** - 重新格式化代码结构
- **项目克隆** - 创建项目副本并修改标识
- **固定混淆** - 保持混淆结果一致性（用于版本迭代）
- **注释清理** - 移除代码注释

### 1.2 适用场景
- **应用上架审核** - 解决代码重复问题（4.3、2.1等审核问题）
- **代码保护** - 防止逆向工程
- **版本迭代** - 持续混淆而不影响功能

---

## 二、功能设计

### 2.1 目标定位

**阶段一目标（当前）**：
- 专注于iOS原生项目（Objective-C/Swift）
- 实现基础但实用的混淆功能
- 模块化架构，便于后续扩展
- 暂不涉及Flutter、Unity3D等跨平台框架

**功能优先级**：
```
P0 (必须实现):
  - 文件名混淆
  - 类名混淆
  - 函数名混淆
  - 属性名混淆
  - 资源文件混淆（图片）

P1 (重要):
  - 垃圾代码插入
  - 字符串加密
  - 注释清理

P2 (可选):
  - 函数顺序打乱
  - 协议名混淆
  - 枚举混淆
  - UIColor混淆
```

### 2.2 核心模块设计

#### 模块结构
```
gui/modules/obfuscation/
├── __init__.py                   # 模块初始化
├── obfuscation_tab.py           # GUI标签页（主入口）
├── obfuscation_cli.py           # 命令行工具（新增）
├── project_analyzer.py          # 项目分析器
├── name_generator.py            # 名称生成器
├── code_parser.py               # 代码解析器
├── code_transformer.py          # 代码转换器
├── resource_handler.py          # 资源文件处理器
├── garbage_generator.py         # 垃圾代码生成器
├── string_encryptor.py          # 字符串加密器
├── config_manager.py            # 配置管理器
├── whitelist_manager.py         # 白名单管理器
├── obfuscation_engine.py        # 混淆引擎（核心调度）
└── CLAUDE.md                    # 模块技术文档

scripts/
├── obfuscate.sh                 # Shell脚本封装（新增）
└── obfuscate.py                 # Python CLI入口（新增）
```

### 2.3 数据流设计

```
用户操作 → GUI界面(obfuscation_tab.py)
    ↓
配置加载(config_manager.py) + 白名单加载(whitelist_manager.py)
    ↓
项目分析(project_analyzer.py)
    ├→ 扫描项目结构
    ├→ 识别代码文件
    ├→ 识别资源文件
    └→ 识别配置文件
    ↓
代码解析(code_parser.py)
    ├→ 解析Objective-C代码
    ├→ 解析Swift代码
    ├→ 提取类、函数、属性
    └→ 构建依赖关系图
    ↓
名称生成(name_generator.py)
    ├→ 生成混淆后的类名
    ├→ 生成混淆后的函数名
    ├→ 生成混淆后的属性名
    └→ 生成混淆后的文件名
    ↓
代码转换(code_transformer.py)
    ├→ 替换类名
    ├→ 替换函数名
    ├→ 替换属性名
    ├→ 插入垃圾代码
    ├→ 加密字符串
    └→ 清理注释
    ↓
资源处理(resource_handler.py)
    ├→ 修改图片文件名
    ├→ 同步代码中的引用
    └→ 修改资源配置文件
    ↓
混淆引擎调度(obfuscation_engine.py)
    ├→ 协调各模块执行
    ├→ 进度监控
    ├→ 错误处理
    └→ 日志记录
    ↓
输出结果
    ├→ 混淆后的代码
    ├→ 混淆映射表
    └→ 混淆报告
```

---

## 三、详细功能设计

### 3.1 项目分析器 (project_analyzer.py)

**功能**：
- 扫描项目目录结构
- 识别.xcodeproj/.xcworkspace文件
- 提取源代码文件(.h/.m/.swift)
- 提取资源文件(.png/.jpg/.xcassets等)
- 提取配置文件(.plist/.strings等)
- 分析项目依赖（CocoaPods、Swift Package Manager）

**接口设计**：
```python
class ProjectAnalyzer:
    def __init__(self, project_path: str):
        """初始化项目分析器"""

    def scan_project(self) -> ProjectStructure:
        """扫描项目结构"""

    def get_source_files(self, language: str = 'all') -> List[str]:
        """获取源代码文件列表"""

    def get_resource_files(self) -> List[str]:
        """获取资源文件列表"""

    def get_dependencies(self) -> Dict[str, List[str]]:
        """获取项目依赖关系"""

    def validate_project(self) -> Tuple[bool, str]:
        """验证项目是否可混淆"""
```

**数据模型**：
```python
@dataclass
class ProjectStructure:
    project_path: str
    project_name: str
    source_files: List[SourceFile]
    resource_files: List[ResourceFile]
    config_files: List[ConfigFile]
    dependencies: Dict[str, List[str]]

@dataclass
class SourceFile:
    path: str
    name: str
    language: str  # 'objc', 'swift'
    type: str      # 'header', 'implementation'
```

### 3.2 代码解析器 (code_parser.py)

**功能**：
- 解析Objective-C代码（使用正则表达式或AST）
- 解析Swift代码（使用正则表达式或SwiftSyntax）
- 提取类定义、函数定义、属性定义
- 构建符号表和依赖图

**接口设计**：
```python
class CodeParser:
    def __init__(self):
        """初始化代码解析器"""

    def parse_objc_file(self, file_path: str) -> ParsedFile:
        """解析Objective-C文件"""

    def parse_swift_file(self, file_path: str) -> ParsedFile:
        """解析Swift文件"""

    def extract_classes(self, parsed_file: ParsedFile) -> List[ClassInfo]:
        """提取类信息"""

    def extract_methods(self, parsed_file: ParsedFile) -> List[MethodInfo]:
        """提取方法信息"""

    def extract_properties(self, parsed_file: ParsedFile) -> List[PropertyInfo]:
        """提取属性信息"""
```

**数据模型**：
```python
@dataclass
class ParsedFile:
    file_path: str
    language: str
    imports: List[str]
    classes: List[ClassInfo]
    protocols: List[ProtocolInfo]
    enums: List[EnumInfo]

@dataclass
class ClassInfo:
    name: str
    super_class: str
    protocols: List[str]
    methods: List[MethodInfo]
    properties: List[PropertyInfo]
    line_start: int
    line_end: int

@dataclass
class MethodInfo:
    name: str
    return_type: str
    parameters: List[Parameter]
    is_class_method: bool
    line_start: int
    line_end: int
```

### 3.3 名称生成器 (name_generator.py)

**功能**：
- 生成混淆后的名称（类名、函数名、属性名）
- 支持多种命名策略（随机、前缀、模式）
- 避免与系统API冲突
- 保证名称唯一性

**命名策略**：
```python
class NamingStrategy:
    RANDOM = 'random'          # 完全随机: Abc123Def
    PREFIX = 'prefix'          # 前缀模式: XY_OriginalName
    PATTERN = 'pattern'        # 模式匹配: CapitalWord
    DICTIONARY = 'dictionary'  # 词典模式: 使用真实单词
```

**接口设计**：
```python
class NameGenerator:
    def __init__(self, strategy: str = NamingStrategy.RANDOM):
        """初始化名称生成器"""

    def generate_class_name(self, original_name: str = None) -> str:
        """生成类名"""

    def generate_method_name(self, original_name: str = None) -> str:
        """生成方法名"""

    def generate_property_name(self, original_name: str = None) -> str:
        """生成属性名"""

    def generate_file_name(self, original_name: str = None) -> str:
        """生成文件名"""

    def is_name_available(self, name: str) -> bool:
        """检查名称是否可用"""

    def add_to_blacklist(self, names: List[str]):
        """添加到黑名单"""
```

### 3.4 代码转换器 (code_transformer.py)

**功能**：
- 执行代码替换（类名、函数名、属性名）
- 同步修改头文件和实现文件
- 同步修改Xib/Storyboard引用
- 保持代码可编译性

**接口设计**：
```python
class CodeTransformer:
    def __init__(self, mapping: NameMapping):
        """初始化代码转换器"""

    def transform_file(self, file_path: str) -> bool:
        """转换单个文件"""

    def transform_class_names(self, file_path: str) -> bool:
        """转换类名"""

    def transform_method_names(self, file_path: str) -> bool:
        """转换方法名"""

    def transform_property_names(self, file_path: str) -> bool:
        """转换属性名"""

    def remove_comments(self, file_path: str) -> bool:
        """移除注释"""

    def backup_file(self, file_path: str) -> str:
        """备份文件"""
```

**数据模型**：
```python
@dataclass
class NameMapping:
    """名称映射表"""
    class_mappings: Dict[str, str]      # 原类名 -> 新类名
    method_mappings: Dict[str, str]     # 原方法名 -> 新方法名
    property_mappings: Dict[str, str]   # 原属性名 -> 新属性名
    file_mappings: Dict[str, str]       # 原文件名 -> 新文件名
```

### 3.5 垃圾代码生成器 (garbage_generator.py)

**功能**：
- 生成无用但合法的代码
- 生成垃圾方法
- 生成垃圾属性
- 自动调用垃圾代码

**接口设计**：
```python
class GarbageGenerator:
    def __init__(self, language: str = 'objc'):
        """初始化垃圾代码生成器"""

    def generate_garbage_method(self) -> str:
        """生成垃圾方法"""

    def generate_garbage_property(self) -> str:
        """生成垃圾属性"""

    def generate_garbage_class(self, class_name: str) -> str:
        """生成垃圾类"""

    def insert_garbage_code(self, file_path: str, count: int = 5) -> bool:
        """插入垃圾代码到文件"""
```

### 3.6 字符串加密器 (string_encryptor.py)

**功能**：
- 加密硬编码字符串
- 生成解密函数
- 替换原字符串为解密调用

**接口设计**：
```python
class StringEncryptor:
    def __init__(self, algorithm: str = 'base64'):
        """初始化字符串加密器"""

    def encrypt_string(self, text: str) -> str:
        """加密字符串"""

    def generate_decrypt_function(self, language: str) -> str:
        """生成解密函数"""

    def replace_strings_in_file(self, file_path: str) -> int:
        """替换文件中的字符串"""
```

### 3.7 资源文件处理器 (resource_handler.py)

**功能**：
- 修改图片文件名
- 修改Assets.xcassets中的资源名称
- 同步代码中的资源引用
- 修改Info.plist等配置文件

**接口设计**：
```python
class ResourceHandler:
    def __init__(self, project_path: str):
        """初始化资源处理器"""

    def rename_image_files(self, mapping: Dict[str, str]) -> bool:
        """重命名图片文件"""

    def update_assets_catalog(self, mapping: Dict[str, str]) -> bool:
        """更新Assets目录"""

    def sync_code_references(self, mapping: Dict[str, str]) -> bool:
        """同步代码中的引用"""

    def update_plist_files(self, mapping: Dict[str, str]) -> bool:
        """更新plist文件"""
```

### 3.8 白名单管理器 (whitelist_manager.py)

**功能**：
- 管理不可混淆的名称
- 加载和保存白名单配置
- 系统API自动过滤

**接口设计**：
```python
class WhitelistManager:
    def __init__(self, config_path: str = None):
        """初始化白名单管理器"""

    def load_whitelist(self, file_path: str) -> bool:
        """加载白名单"""

    def save_whitelist(self, file_path: str) -> bool:
        """保存白名单"""

    def add_class(self, class_name: str):
        """添加类到白名单"""

    def add_method(self, method_name: str):
        """添加方法到白名单"""

    def is_whitelisted(self, name: str, type: str) -> bool:
        """检查是否在白名单中"""

    def get_system_apis(self) -> Set[str]:
        """获取系统API列表"""
```

**白名单配置格式**：
```json
{
    "classes": [
        "UIViewController",
        "NSObject",
        "AppDelegate"
    ],
    "methods": [
        "viewDidLoad",
        "viewWillAppear:",
        "applicationDidFinishLaunching:"
    ],
    "properties": [
        "delegate",
        "dataSource"
    ],
    "files": [
        "AppDelegate",
        "SceneDelegate"
    ],
    "directories": [
        "Pods/",
        "Carthage/"
    ]
}
```

### 3.9 配置管理器 (config_manager.py)

**功能**：
- 加载和保存混淆配置
- 管理混淆参数
- 配置验证

**配置项**：
```json
{
    "project_path": "/path/to/project",
    "output_path": "/path/to/output",
    "language": "objc",  // "objc", "swift", "both"

    "obfuscation": {
        "class_names": true,
        "method_names": true,
        "property_names": true,
        "file_names": true,
        "resource_names": true
    },

    "naming": {
        "strategy": "random",  // "random", "prefix", "pattern"
        "prefix": "XY_",
        "min_length": 8,
        "max_length": 16
    },

    "garbage_code": {
        "enabled": true,
        "methods_per_class": 5,
        "properties_per_class": 3
    },

    "string_encryption": {
        "enabled": true,
        "algorithm": "base64",
        "exclude_short": true,
        "min_length": 3
    },

    "cleanup": {
        "remove_comments": true,
        "remove_whitespace": false
    },

    "whitelist_file": "./whitelist.json",
    "backup": true
}
```

### 3.10 混淆引擎 (obfuscation_engine.py)

**功能**：
- 协调所有模块的执行
- 管理混淆流程
- 进度监控和报告
- 错误处理和回滚

**接口设计**：
```python
class ObfuscationEngine:
    def __init__(self, config: ObfuscationConfig):
        """初始化混淆引擎"""

    def start_obfuscation(self, callback: Callable = None) -> ObfuscationResult:
        """开始混淆"""

    def get_progress(self) -> float:
        """获取混淆进度"""

    def pause(self):
        """暂停混淆"""

    def resume(self):
        """恢复混淆"""

    def cancel(self):
        """取消混淆"""

    def rollback(self):
        """回滚混淆"""
```

**数据模型**：
```python
@dataclass
class ObfuscationResult:
    success: bool
    message: str
    stats: ObfuscationStats
    mapping_file: str
    log_file: str

@dataclass
class ObfuscationStats:
    files_processed: int
    classes_obfuscated: int
    methods_obfuscated: int
    properties_obfuscated: int
    resources_obfuscated: int
    garbage_code_inserted: int
    strings_encrypted: int
    duration: float  # 秒
```

### 3.11 GUI标签页 (obfuscation_tab.py)

**功能**：
- 提供用户界面
- 项目选择和加载
- 配置参数设置
- 启动混淆
- 显示进度和结果

**界面布局**：
```
┌─────────────────────────────────────────────────────────┐
│ iOS代码混淆                                              │
├─────────────────────────────────────────────────────────┤
│ 项目路径: [___________________________] [选择项目]      │
│ 输出路径: [___________________________] [选择输出]      │
│                                                          │
│ ┌─ 混淆选项 ──────────────────────────────────────┐    │
│ │ ☑ 类名混淆     ☑ 函数名混淆    ☑ 属性名混淆    │    │
│ │ ☑ 文件名混淆   ☑ 资源文件混淆                   │    │
│ │ ☑ 垃圾代码插入 ☑ 字符串加密    ☑ 注释清理      │    │
│ └─────────────────────────────────────────────────┘    │
│                                                          │
│ ┌─ 命名策略 ──────────────────────────────────────┐    │
│ │ ⦿ 随机命名  ○ 前缀模式  ○ 词典模式             │    │
│ │ 前缀: [XY_]  长度: [8] - [16]                   │    │
│ └─────────────────────────────────────────────────┘    │
│                                                          │
│ ┌─ 高级选项 ──────────────────────────────────────┐    │
│ │ 白名单配置: [whitelist.json] [编辑]             │    │
│ │ ☑ 创建备份  ☑ 生成映射表  ☑ 详细日志           │    │
│ └─────────────────────────────────────────────────┘    │
│                                                          │
│ [开始混淆] [停止] [查看日志] [导出配置]                │
│                                                          │
│ ┌─ 混淆进度 ──────────────────────────────────────┐    │
│ │ [████████████████░░░░░░░░░░] 65%                 │    │
│ │ 正在处理: ViewController.m                       │    │
│ │ 已处理文件: 130/200                              │    │
│ └─────────────────────────────────────────────────┘    │
│                                                          │
│ ┌─ 混淆日志 ──────────────────────────────────────┐    │
│ │ [2025-10-13 10:23:15] 开始分析项目...           │    │
│ │ [2025-10-13 10:23:16] 发现 200 个源文件         │    │
│ │ [2025-10-13 10:23:17] 开始解析代码...           │    │
│ │ [2025-10-13 10:23:20] 生成混淆映射表...         │    │
│ │ [2025-10-13 10:23:25] 正在转换代码...           │    │
│ └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

---

## 四、命令行工具和CI/CD集成 🆕

### 4.1 设计目标

除了GUI界面外，提供命令行工具支持以下场景：
1. **本地调试** - 开发者在本地快速混淆测试
2. **Jenkins集成** - CI/CD流水线自动化混淆
3. **批量处理** - 脚本化批量混淆多个项目
4. **远程执行** - SSH远程调用混淆任务

### 4.2 命令行工具设计 (obfuscation_cli.py)

#### 4.2.1 接口设计

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iOS代码混淆命令行工具
支持本地调试和CI/CD集成
"""

import argparse
import sys
import json
from pathlib import Path
from typing import Optional

from .obfuscation_engine import ObfuscationEngine
from .config_manager import ObfuscationConfig


class ObfuscationCLI:
    """命令行接口"""

    def __init__(self):
        self.parser = self._create_parser()

    def _create_parser(self) -> argparse.ArgumentParser:
        """创建命令行参数解析器"""
        parser = argparse.ArgumentParser(
            prog='ios-obfuscate',
            description='iOS代码混淆工具 - 支持GUI和CLI模式',
            epilog='示例: ios-obfuscate -p /path/to/project -o /path/to/output'
        )

        # 必需参数
        parser.add_argument(
            '-p', '--project',
            required=True,
            help='iOS项目路径 (.xcodeproj 或 .xcworkspace)'
        )

        parser.add_argument(
            '-o', '--output',
            required=True,
            help='混淆输出路径'
        )

        # 可选参数
        parser.add_argument(
            '-c', '--config',
            help='配置文件路径 (JSON格式)'
        )

        parser.add_argument(
            '-w', '--whitelist',
            help='白名单文件路径 (JSON格式)'
        )

        parser.add_argument(
            '-l', '--language',
            choices=['objc', 'swift', 'both'],
            default='both',
            help='目标语言 (默认: both)'
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
            '--file-names',
            action='store_true',
            help='混淆文件名'
        )
        obf_group.add_argument(
            '--resource-names',
            action='store_true',
            help='混淆资源文件名'
        )
        obf_group.add_argument(
            '--all',
            action='store_true',
            help='启用所有混淆选项'
        )

        # 高级选项
        adv_group = parser.add_argument_group('高级选项')
        adv_group.add_argument(
            '--garbage-code',
            action='store_true',
            help='插入垃圾代码'
        )
        adv_group.add_argument(
            '--string-encrypt',
            action='store_true',
            help='加密字符串'
        )
        adv_group.add_argument(
            '--remove-comments',
            action='store_true',
            help='移除注释'
        )

        # 命名策略
        naming_group = parser.add_argument_group('命名策略')
        naming_group.add_argument(
            '--strategy',
            choices=['random', 'prefix', 'pattern', 'dictionary'],
            default='random',
            help='命名策略 (默认: random)'
        )
        naming_group.add_argument(
            '--prefix',
            default='XY_',
            help='前缀模式的前缀 (默认: XY_)'
        )
        naming_group.add_argument(
            '--min-length',
            type=int,
            default=8,
            help='名称最小长度 (默认: 8)'
        )
        naming_group.add_argument(
            '--max-length',
            type=int,
            default=16,
            help='名称最大长度 (默认: 16)'
        )

        # 其他选项
        parser.add_argument(
            '--no-backup',
            action='store_true',
            help='不创建备份'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='详细输出'
        )
        parser.add_argument(
            '--quiet',
            action='store_true',
            help='安静模式，仅输出错误'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='试运行，不实际修改文件'
        )
        parser.add_argument(
            '--export-config',
            help='导出当前配置到文件'
        )

        return parser

    def run(self, args=None) -> int:
        """运行命令行工具"""
        args = self.parser.parse_args(args)

        try:
            # 加载或创建配置
            config = self._load_config(args)

            # 导出配置（如果指定）
            if args.export_config:
                self._export_config(config, args.export_config)
                return 0

            # 试运行模式
            if args.dry_run:
                print("🔍 试运行模式 - 不会修改任何文件")

            # 创建混淆引擎
            engine = ObfuscationEngine(config)

            # 进度回调
            def progress_callback(progress):
                if not args.quiet:
                    print(f"\r进度: {progress:.1f}%", end='', flush=True)

            # 开始混淆
            if not args.quiet:
                print(f"🚀 开始混淆项目: {args.project}")

            result = engine.start_obfuscation(
                callback=progress_callback,
                dry_run=args.dry_run
            )

            if not args.quiet:
                print()  # 换行

            # 输出结果
            if result.success:
                self._print_success(result, args.verbose)
                return 0
            else:
                self._print_error(result)
                return 1

        except KeyboardInterrupt:
            print("\n⚠️  用户中断")
            return 130
        except Exception as e:
            print(f"❌ 错误: {str(e)}", file=sys.stderr)
            if args.verbose:
                import traceback
                traceback.print_exc()
            return 1

    def _load_config(self, args) -> ObfuscationConfig:
        """加载配置"""
        if args.config:
            # 从配置文件加载
            with open(args.config, 'r', encoding='utf-8') as f:
                config_dict = json.load(f)
            config = ObfuscationConfig.from_dict(config_dict)
        else:
            # 从命令行参数创建
            config = ObfuscationConfig(
                project_path=args.project,
                output_path=args.output,
                language=args.language,
                obfuscation={
                    'class_names': args.all or args.class_names,
                    'method_names': args.all or args.method_names,
                    'property_names': args.all or args.property_names,
                    'file_names': args.all or args.file_names,
                    'resource_names': args.all or args.resource_names,
                },
                naming={
                    'strategy': args.strategy,
                    'prefix': args.prefix,
                    'min_length': args.min_length,
                    'max_length': args.max_length,
                },
                garbage_code={
                    'enabled': args.garbage_code,
                },
                string_encryption={
                    'enabled': args.string_encrypt,
                },
                cleanup={
                    'remove_comments': args.remove_comments,
                },
                whitelist_file=args.whitelist,
                backup=not args.no_backup,
            )

        return config

    def _export_config(self, config: ObfuscationConfig, file_path: str):
        """导出配置到文件"""
        config_dict = config.to_dict()
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=2, ensure_ascii=False)
        print(f"✅ 配置已导出到: {file_path}")

    def _print_success(self, result, verbose: bool):
        """打印成功信息"""
        print("✅ 混淆成功！")
        print(f"📊 统计信息:")
        print(f"   - 处理文件: {result.stats.files_processed}")
        print(f"   - 混淆类: {result.stats.classes_obfuscated}")
        print(f"   - 混淆方法: {result.stats.methods_obfuscated}")
        print(f"   - 混淆属性: {result.stats.properties_obfuscated}")
        print(f"   - 混淆资源: {result.stats.resources_obfuscated}")
        if result.stats.garbage_code_inserted > 0:
            print(f"   - 插入垃圾代码: {result.stats.garbage_code_inserted}")
        if result.stats.strings_encrypted > 0:
            print(f"   - 加密字符串: {result.stats.strings_encrypted}")
        print(f"   - 耗时: {result.stats.duration:.2f}秒")
        print(f"📄 映射表: {result.mapping_file}")
        print(f"📝 日志文件: {result.log_file}")

    def _print_error(self, result):
        """打印错误信息"""
        print(f"❌ 混淆失败: {result.message}", file=sys.stderr)


def main():
    """命令行入口"""
    cli = ObfuscationCLI()
    sys.exit(cli.run())


if __name__ == '__main__':
    main()
```

#### 4.2.2 使用示例

**基本使用**：
```bash
# 最简单的使用方式
python3 -m gui.modules.obfuscation.obfuscation_cli \
    -p /path/to/MyApp.xcodeproj \
    -o /path/to/MyApp_obfuscated \
    --all

# 指定具体混淆选项
python3 -m gui.modules.obfuscation.obfuscation_cli \
    -p /path/to/MyApp.xcodeproj \
    -o /path/to/MyApp_obfuscated \
    --class-names \
    --method-names \
    --property-names
```

**使用配置文件**：
```bash
# 创建配置文件
python3 -m gui.modules.obfuscation.obfuscation_cli \
    -p /path/to/MyApp.xcodeproj \
    -o /path/to/MyApp_obfuscated \
    --all \
    --export-config obfuscate_config.json

# 使用配置文件
python3 -m gui.modules.obfuscation.obfuscation_cli \
    -c obfuscate_config.json
```

**高级功能**：
```bash
# 完整功能混淆
python3 -m gui.modules.obfuscation.obfuscation_cli \
    -p /path/to/MyApp.xcodeproj \
    -o /path/to/MyApp_obfuscated \
    -w whitelist.json \
    --all \
    --garbage-code \
    --string-encrypt \
    --remove-comments \
    --strategy random \
    --verbose

# 试运行（不实际修改文件）
python3 -m gui.modules.obfuscation.obfuscation_cli \
    -p /path/to/MyApp.xcodeproj \
    -o /path/to/MyApp_obfuscated \
    --all \
    --dry-run
```

### 4.3 Shell脚本封装 (scripts/obfuscate.sh)

为了更方便的使用，提供Shell脚本封装：

```bash
#!/bin/bash
# iOS代码混淆Shell脚本
# 用法: ./scripts/obfuscate.sh <项目路径> <输出路径> [选项]

set -e  # 遇到错误立即退出

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查Python环境
check_python() {
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 未安装"
        exit 1
    fi

    # 检查虚拟环境
    if [ ! -d "$PROJECT_ROOT/venv" ]; then
        log_warn "虚拟环境不存在，正在创建..."
        python3 -m venv "$PROJECT_ROOT/venv"
    fi

    # 激活虚拟环境
    source "$PROJECT_ROOT/venv/bin/activate"

    # 安装依赖
    if ! python3 -c "import gui.modules.obfuscation" &> /dev/null; then
        log_warn "正在安装依赖..."
        pip install -r "$PROJECT_ROOT/requirements.txt" -q
    fi
}

# 显示帮助
show_help() {
    cat << EOF
iOS代码混淆工具

用法:
    $0 <项目路径> <输出路径> [选项]

示例:
    # 基本使用
    $0 /path/to/MyApp.xcodeproj /path/to/output --all

    # 使用配置文件
    $0 --config obfuscate_config.json

    # 指定白名单
    $0 /path/to/MyApp.xcodeproj /path/to/output \\
        --all --whitelist whitelist.json

    # 完整功能
    $0 /path/to/MyApp.xcodeproj /path/to/output \\
        --all --garbage-code --string-encrypt --remove-comments

选项:
    --config FILE          使用配置文件
    --whitelist FILE       使用白名单文件
    --all                  启用所有混淆选项
    --class-names          混淆类名
    --method-names         混淆方法名
    --property-names       混淆属性名
    --file-names           混淆文件名
    --resource-names       混淆资源文件名
    --garbage-code         插入垃圾代码
    --string-encrypt       加密字符串
    --remove-comments      移除注释
    --strategy STRATEGY    命名策略 (random/prefix/pattern/dictionary)
    --no-backup            不创建备份
    --verbose              详细输出
    --quiet                安静模式
    --dry-run              试运行
    --help                 显示帮助

EOF
}

# 主函数
main() {
    # 检查参数
    if [ $# -eq 0 ] || [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
        show_help
        exit 0
    fi

    log_info "初始化环境..."
    check_python

    log_info "启动混淆..."

    # 调用Python CLI
    python3 -m gui.modules.obfuscation.obfuscation_cli "$@"

    # 检查返回值
    if [ $? -eq 0 ]; then
        log_info "混淆完成！"
    else
        log_error "混淆失败！"
        exit 1
    fi
}

# 执行
main "$@"
```

**使用方法**：
```bash
# 添加执行权限
chmod +x scripts/obfuscate.sh

# 基本使用
./scripts/obfuscate.sh /path/to/MyApp.xcodeproj /path/to/output --all

# 使用配置文件
./scripts/obfuscate.sh --config obfuscate_config.json
```

### 4.4 Python CLI入口 (scripts/obfuscate.py)

提供独立的Python脚本入口：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iOS代码混淆Python CLI入口
独立脚本，可直接运行
"""

import sys
import os

# 添加项目根目录到Python路径
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

# 导入CLI
from gui.modules.obfuscation.obfuscation_cli import main

if __name__ == '__main__':
    main()
```

**使用方法**：
```bash
# 添加执行权限
chmod +x scripts/obfuscate.py

# 直接运行
./scripts/obfuscate.py -p /path/to/project -o /path/to/output --all
```

### 4.5 Jenkins集成

#### 4.5.1 Jenkinsfile示例

```groovy
pipeline {
    agent any

    environment {
        PROJECT_PATH = '/path/to/MyApp.xcodeproj'
        OUTPUT_PATH = "${WORKSPACE}/obfuscated"
        OBFUSCATE_CONFIG = "${WORKSPACE}/obfuscate_config.json"
    }

    stages {
        stage('Checkout') {
            steps {
                // 检出代码
                checkout scm
            }
        }

        stage('Setup') {
            steps {
                sh '''
                    # 创建虚拟环境
                    python3 -m venv venv
                    source venv/bin/activate

                    # 安装依赖
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Obfuscate') {
            steps {
                sh '''
                    source venv/bin/activate

                    # 执行混淆
                    python3 -m gui.modules.obfuscation.obfuscation_cli \
                        -p ${PROJECT_PATH} \
                        -o ${OUTPUT_PATH} \
                        -c ${OBFUSCATE_CONFIG} \
                        --verbose
                '''
            }
        }

        stage('Build') {
            steps {
                sh '''
                    # 构建混淆后的项目
                    cd ${OUTPUT_PATH}
                    xcodebuild -project MyApp.xcodeproj \
                        -scheme MyApp \
                        -configuration Release \
                        clean build
                '''
            }
        }

        stage('Archive') {
            steps {
                // 归档混淆映射表
                archiveArtifacts artifacts: '**/obfuscation_mapping.json', fingerprint: true

                // 归档混淆日志
                archiveArtifacts artifacts: '**/obfuscation.log', fingerprint: true

                // 归档IPA
                archiveArtifacts artifacts: '**/*.ipa', fingerprint: true
            }
        }
    }

    post {
        always {
            // 清理工作空间
            cleanWs()
        }
        success {
            echo '✅ 混淆和构建成功！'
        }
        failure {
            echo '❌ 混淆或构建失败！'
        }
    }
}
```

#### 4.5.2 配置文件模板

创建 `obfuscate_config.json` 配置文件：

```json
{
    "project_path": "${PROJECT_PATH}",
    "output_path": "${OUTPUT_PATH}",
    "language": "both",

    "obfuscation": {
        "class_names": true,
        "method_names": true,
        "property_names": true,
        "file_names": true,
        "resource_names": true
    },

    "naming": {
        "strategy": "random",
        "prefix": "XY_",
        "min_length": 8,
        "max_length": 16
    },

    "garbage_code": {
        "enabled": true,
        "methods_per_class": 5,
        "properties_per_class": 3
    },

    "string_encryption": {
        "enabled": true,
        "algorithm": "base64",
        "exclude_short": true,
        "min_length": 3
    },

    "cleanup": {
        "remove_comments": true,
        "remove_whitespace": false
    },

    "whitelist_file": "./whitelist.json",
    "backup": true
}
```

### 4.6 GitLab CI/CD集成

#### 4.6.1 .gitlab-ci.yml示例

```yaml
stages:
  - setup
  - obfuscate
  - build
  - deploy

variables:
  PROJECT_PATH: "/path/to/MyApp.xcodeproj"
  OUTPUT_PATH: "$CI_PROJECT_DIR/obfuscated"

setup:
  stage: setup
  script:
    - python3 -m venv venv
    - source venv/bin/activate
    - pip install -r requirements.txt
  artifacts:
    paths:
      - venv/
    expire_in: 1 hour

obfuscate:
  stage: obfuscate
  dependencies:
    - setup
  script:
    - source venv/bin/activate
    - |
      python3 -m gui.modules.obfuscation.obfuscation_cli \
        -p $PROJECT_PATH \
        -o $OUTPUT_PATH \
        -c obfuscate_config.json \
        --verbose
  artifacts:
    paths:
      - obfuscated/
      - obfuscation_mapping.json
      - obfuscation.log
    expire_in: 1 week

build:
  stage: build
  dependencies:
    - obfuscate
  script:
    - cd $OUTPUT_PATH
    - xcodebuild -project MyApp.xcodeproj -scheme MyApp -configuration Release clean build
  artifacts:
    paths:
      - "**/*.ipa"
    expire_in: 1 month

deploy:
  stage: deploy
  dependencies:
    - build
  script:
    - echo "部署到App Store或企业分发平台"
  only:
    - main
```

### 4.7 GitHub Actions集成

#### 4.7.1 workflow示例

创建 `.github/workflows/obfuscate-and-build.yml`：

```yaml
name: Obfuscate and Build

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  workflow_dispatch:

jobs:
  obfuscate:
    runs-on: macos-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v3

    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt

    - name: Run obfuscation
      run: |
        python -m gui.modules.obfuscation.obfuscation_cli \
          -p /path/to/MyApp.xcodeproj \
          -o ./obfuscated \
          -c obfuscate_config.json \
          --verbose

    - name: Upload obfuscation mapping
      uses: actions/upload-artifact@v3
      with:
        name: obfuscation-mapping
        path: obfuscation_mapping.json

    - name: Upload obfuscation log
      uses: actions/upload-artifact@v3
      with:
        name: obfuscation-log
        path: obfuscation.log

    - name: Build project
      run: |
        cd obfuscated
        xcodebuild -project MyApp.xcodeproj \
          -scheme MyApp \
          -configuration Release \
          clean build

    - name: Upload IPA
      uses: actions/upload-artifact@v3
      with:
        name: app-ipa
        path: "**/*.ipa"
```

### 4.8 本地调试脚本示例

#### 4.8.1 快速混淆脚本

创建 `quick_obfuscate.sh` 用于本地快速测试：

```bash
#!/bin/bash
# 快速混淆脚本 - 用于本地开发调试

PROJECT_PATH="/path/to/MyApp.xcodeproj"
OUTPUT_PATH="./obfuscated_$(date +%Y%m%d_%H%M%S)"

echo "🚀 开始快速混淆..."
echo "项目: $PROJECT_PATH"
echo "输出: $OUTPUT_PATH"

# 执行混淆
./scripts/obfuscate.sh \
    "$PROJECT_PATH" \
    "$OUTPUT_PATH" \
    --all \
    --garbage-code \
    --string-encrypt \
    --verbose

# 检查结果
if [ $? -eq 0 ]; then
    echo "✅ 混淆成功！"
    echo "📁 输出目录: $OUTPUT_PATH"

    # 可选：自动打开输出目录
    open "$OUTPUT_PATH"
else
    echo "❌ 混淆失败！"
    exit 1
fi
```

#### 4.8.2 批量混淆脚本

创建 `batch_obfuscate.sh` 用于批量处理多个项目：

```bash
#!/bin/bash
# 批量混淆脚本

# 项目列表
PROJECTS=(
    "/path/to/Project1.xcodeproj"
    "/path/to/Project2.xcodeproj"
    "/path/to/Project3.xcodeproj"
)

OUTPUT_ROOT="./obfuscated_batch_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUTPUT_ROOT"

echo "🚀 开始批量混淆 ${#PROJECTS[@]} 个项目..."

for PROJECT in "${PROJECTS[@]}"; do
    PROJECT_NAME=$(basename "$PROJECT" .xcodeproj)
    OUTPUT_PATH="$OUTPUT_ROOT/$PROJECT_NAME"

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "混淆项目: $PROJECT_NAME"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    ./scripts/obfuscate.sh \
        "$PROJECT" \
        "$OUTPUT_PATH" \
        --all \
        --garbage-code \
        --string-encrypt

    if [ $? -eq 0 ]; then
        echo "✅ $PROJECT_NAME 混淆成功"
    else
        echo "❌ $PROJECT_NAME 混淆失败"
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 批量混淆完成！"
echo "📁 输出目录: $OUTPUT_ROOT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
```

### 4.9 返回码定义

为了便于CI/CD集成，定义标准返回码：

```python
class ExitCode:
    """命令行工具返回码"""
    SUCCESS = 0              # 成功
    GENERAL_ERROR = 1        # 一般错误
    INVALID_ARGS = 2         # 无效参数
    PROJECT_NOT_FOUND = 3    # 项目不存在
    CONFIG_ERROR = 4         # 配置错误
    PARSE_ERROR = 5          # 解析错误
    TRANSFORM_ERROR = 6      # 转换错误
    IO_ERROR = 7             # 文件操作错误
    USER_INTERRUPT = 130     # 用户中断 (Ctrl+C)
```

### 4.10 日志输出格式

为便于CI/CD解析，提供结构化日志输出：

```python
import logging
import json

class StructuredLogger:
    """结构化日志记录器"""

    def __init__(self, log_file: str = None):
        self.log_file = log_file
        self.events = []

    def log_event(self, event_type: str, data: dict):
        """记录事件"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'data': data
        }
        self.events.append(event)

        if self.log_file:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(event) + '\n')

    def get_summary(self) -> dict:
        """获取摘要"""
        return {
            'total_events': len(self.events),
            'events_by_type': self._count_by_type(),
            'duration': self._calculate_duration()
        }

    def _count_by_type(self) -> dict:
        """按类型统计事件"""
        counts = {}
        for event in self.events:
            event_type = event['type']
            counts[event_type] = counts.get(event_type, 0) + 1
        return counts
```

---

## 五、技术实现细节

### 4.1 Objective-C代码解析

**类名提取**：
```python
# 提取@interface定义
class_pattern = r'@interface\s+(\w+)\s*:\s*(\w+)'

# 提取@implementation定义
impl_pattern = r'@implementation\s+(\w+)'

# 提取Category
category_pattern = r'@interface\s+(\w+)\s*\((\w+)\)'
```

**方法名提取**：
```python
# 实例方法
instance_method_pattern = r'^\s*-\s*\(([\w\s\*]+)\)\s*(\w+)'

# 类方法
class_method_pattern = r'^\s*\+\s*\(([\w\s\*]+)\)\s*(\w+)'

# 带参数的方法
parameterized_method_pattern = r'(\w+):\s*\([\w\s\*]+\)\s*\w+'
```

**属性名提取**：
```python
# @property声明
property_pattern = r'@property\s*\([^)]*\)\s*([\w\s\*]+)\s+(\w+)'

# 实例变量
ivar_pattern = r'\{\s*([\w\s\*]+)\s+(\w+)\s*;'
```

### 4.2 Swift代码解析

**类名提取**：
```python
# class定义
class_pattern = r'class\s+(\w+)\s*:\s*([\w\s,]+)?'

# struct定义
struct_pattern = r'struct\s+(\w+)\s*:\s*([\w\s,]+)?'

# extension定义
extension_pattern = r'extension\s+(\w+)'
```

**方法名提取**：
```python
# 函数定义
func_pattern = r'func\s+(\w+)\s*\('

# init方法
init_pattern = r'init\s*\('
```

**属性名提取**：
```python
# 变量声明
var_pattern = r'var\s+(\w+)\s*:\s*([\w\?!]+)'

# 常量声明
let_pattern = r'let\s+(\w+)\s*:\s*([\w\?!]+)'
```

### 4.3 名称生成算法

**随机命名**：
```python
import random
import string

def generate_random_name(prefix='', length=10):
    """生成随机名称"""
    chars = string.ascii_letters
    name = prefix + ''.join(random.choice(chars) for _ in range(length))
    # 确保首字母大写（类名）
    return name[0].upper() + name[1:]
```

**模式命名**：
```python
def generate_pattern_name(pattern='CapitalWord'):
    """生成模式名称"""
    syllables = ['Ab', 'Cd', 'Ef', 'Gh', 'Ij', 'Kl', 'Mn']
    name = ''.join(random.sample(syllables, 3))
    return name
```

**词典命名**：
```python
def generate_dictionary_name(word_list):
    """使用真实单词生成名称"""
    words = random.sample(word_list, 2)
    return ''.join(word.capitalize() for word in words)
```

### 4.4 代码替换策略

**多阶段替换**：
```python
def transform_code(content, mappings):
    """多阶段代码转换"""

    # 第1阶段：替换类名（最长的先替换）
    for old_name, new_name in sorted(mappings.class_mappings.items(),
                                      key=lambda x: len(x[0]),
                                      reverse=True):
        content = replace_with_word_boundary(content, old_name, new_name)

    # 第2阶段：替换方法名
    for old_name, new_name in mappings.method_mappings.items():
        content = replace_method_name(content, old_name, new_name)

    # 第3阶段：替换属性名
    for old_name, new_name in mappings.property_mappings.items():
        content = replace_property_name(content, old_name, new_name)

    return content

def replace_with_word_boundary(content, old_name, new_name):
    """使用单词边界替换（避免误替换）"""
    pattern = r'\b' + re.escape(old_name) + r'\b'
    return re.sub(pattern, new_name, content)
```

### 4.5 垃圾代码模板

**Objective-C垃圾方法**：
```objc
- (void)garbageMethod{random_suffix} {
    NSInteger var1 = arc4random() % 100;
    NSInteger var2 = arc4random() % 100;
    NSInteger result = var1 + var2;

    if (result > 50) {
        NSLog(@"Result: %ld", (long)result);
    } else {
        NSLog(@"Result: %ld", (long)result);
    }
}
```

**Swift垃圾方法**：
```swift
func garbageMethod{random_suffix}() {
    let var1 = Int.random(in: 0..<100)
    let var2 = Int.random(in: 0..<100)
    let result = var1 + var2

    if result > 50 {
        print("Result: \(result)")
    } else {
        print("Result: \(result)")
    }
}
```

### 4.6 字符串加密

**Base64加密**：
```python
import base64

def encrypt_string(text):
    """Base64加密"""
    encoded = base64.b64encode(text.encode('utf-8')).decode('utf-8')
    return encoded

def generate_decrypt_function_objc():
    """生成OC解密函数"""
    return '''
- (NSString *)decryptString:(NSString *)encrypted {
    NSData *data = [[NSData alloc] initWithBase64EncodedString:encrypted options:0];
    return [[NSString alloc] initWithData:data encoding:NSUTF8StringEncoding];
}
'''

def replace_string_literal(content):
    """替换字符串字面量"""
    pattern = r'@"([^"]+)"'

    def replacer(match):
        original = match.group(1)
        encrypted = encrypt_string(original)
        return f'[self decryptString:@"{encrypted}"]'

    return re.sub(pattern, replacer, content)
```

**XOR加密**：
```python
def xor_encrypt(text, key=0x5A):
    """XOR加密"""
    encrypted = ''.join(chr(ord(c) ^ key) for c in text)
    return base64.b64encode(encrypted.encode()).decode()

def generate_xor_decrypt_function():
    """生成XOR解密函数"""
    return '''
- (NSString *)decryptXOR:(NSString *)encrypted {
    NSData *data = [[NSData alloc] initWithBase64EncodedString:encrypted options:0];
    NSMutableData *decrypted = [data mutableCopy];
    uint8_t *bytes = decrypted.mutableBytes;
    for (NSInteger i = 0; i < decrypted.length; i++) {
        bytes[i] ^= 0x5A;
    }
    return [[NSString alloc] initWithData:decrypted encoding:NSUTF8StringEncoding];
}
'''
```

---

## 五、实施计划

### 5.1 开发阶段

#### 第一阶段：基础框架（1-2天）
- [x] 创建模块目录结构
- [ ] 实现项目分析器 (project_analyzer.py)
- [ ] 实现配置管理器 (config_manager.py)
- [ ] 实现白名单管理器 (whitelist_manager.py)
- [ ] 实现名称生成器 (name_generator.py)
- [ ] 创建GUI基础界面 (obfuscation_tab.py)

#### 第二阶段：核心功能（2-3天）
- [ ] 实现代码解析器 (code_parser.py)
  - [ ] Objective-C解析
  - [ ] Swift解析
- [ ] 实现代码转换器 (code_transformer.py)
  - [ ] 类名替换
  - [ ] 方法名替换
  - [ ] 属性名替换
- [ ] 实现资源处理器 (resource_handler.py)
  - [ ] 图片文件重命名
  - [ ] 代码引用同步

#### 第三阶段：高级功能（1-2天）
- [ ] 实现垃圾代码生成器 (garbage_generator.py)
- [ ] 实现字符串加密器 (string_encryptor.py)
- [ ] 实现混淆引擎 (obfuscation_engine.py)
- [ ] 完善GUI界面功能

#### 第四阶段：测试和优化（1-2天）
- [ ] 单元测试
- [ ] 集成测试
- [ ] 性能优化
- [ ] 文档完善

### 5.2 测试计划

#### 单元测试
```python
# tests/test_name_generator.py
def test_generate_class_name():
    generator = NameGenerator()
    name = generator.generate_class_name()
    assert len(name) >= 8
    assert name[0].isupper()
    assert name.isalnum()

# tests/test_code_parser.py
def test_parse_objc_class():
    parser = CodeParser()
    code = '''
    @interface MyClass : NSObject
    @property (nonatomic, strong) NSString *name;
    - (void)myMethod;
    @end
    '''
    parsed = parser.parse_objc_code(code)
    assert len(parsed.classes) == 1
    assert parsed.classes[0].name == 'MyClass'
```

#### 集成测试
```python
# tests/test_obfuscation_engine.py
def test_obfuscate_simple_project():
    engine = ObfuscationEngine(test_config)
    result = engine.start_obfuscation()
    assert result.success
    assert result.stats.classes_obfuscated > 0
```

### 5.3 部署计划

#### 集成到主程序
1. 在`gui/mars_log_analyzer_modular.py`中添加新标签页
2. 导入`obfuscation_tab.py`
3. 创建"iOS混淆"标签页实例
4. 测试标签页切换和功能

#### 文档更新
1. 更新主`CLAUDE.md`
2. 创建模块`CLAUDE.md`
3. 更新`README_CN.md`
4. 添加使用示例

---

## 六、风险和限制

### 6.1 技术风险

**风险1：代码解析不完整**
- **问题**：正则表达式可能无法处理所有语法情况
- **缓解**：逐步完善正则规则，添加特殊情况处理
- **备选方案**：使用clang AST或SwiftSyntax进行更精确的解析

**风险2：混淆后编译失败**
- **问题**：名称替换可能导致编译错误
- **缓解**：完善白名单机制，测试更多项目
- **备选方案**：提供回滚功能

**风险3：性能问题**
- **问题**：大型项目处理缓慢
- **缓解**：使用多线程处理，优化算法
- **备选方案**：分批处理文件

### 6.2 功能限制

**当前版本限制**：
1. 仅支持iOS原生项目（Objective-C/Swift）
2. 不支持跨平台框架（Flutter、Unity3D、React Native）
3. 不支持C++混淆（游戏引擎）
4. 不支持函数拆分等高级功能
5. 白名单需要手动配置

**未来扩展方向**：
1. 支持更多语言和框架
2. AI辅助白名单生成
3. 智能识别系统API
4. 云端混淆服务
5. 版本对比和增量混淆

---

## 七、使用示例

### 7.1 基本使用流程

```python
# 1. 创建配置
config = ObfuscationConfig(
    project_path='/path/to/MyApp.xcodeproj',
    output_path='/path/to/MyApp_obfuscated',
    language='objc',
    obfuscation={
        'class_names': True,
        'method_names': True,
        'property_names': True
    }
)

# 2. 初始化引擎
engine = ObfuscationEngine(config)

# 3. 开始混淆
result = engine.start_obfuscation(
    callback=lambda progress: print(f"Progress: {progress}%")
)

# 4. 查看结果
if result.success:
    print(f"混淆成功！")
    print(f"处理文件: {result.stats.files_processed}")
    print(f"混淆类: {result.stats.classes_obfuscated}")
    print(f"映射表: {result.mapping_file}")
else:
    print(f"混淆失败: {result.message}")
```

### 7.2 GUI使用流程

1. 打开"iOS混淆"标签页
2. 选择项目路径（.xcodeproj或.xcworkspace）
3. 选择输出路径
4. 配置混淆选项（勾选需要的功能）
5. 选择命名策略和参数
6. 加载或编辑白名单配置
7. 点击"开始混淆"
8. 查看实时进度和日志
9. 混淆完成后查看结果和映射表

---

## 八、附录

### 8.1 系统API白名单（部分）

**UIKit框架**：
```
UIViewController, UIView, UIButton, UILabel, UITableView, UICollectionView,
viewDidLoad, viewWillAppear:, viewDidAppear:, viewWillDisappear:,
tableView:numberOfRowsInSection:, tableView:cellForRowAtIndexPath:,
delegate, dataSource, frame, bounds, center
```

**Foundation框架**：
```
NSObject, NSString, NSArray, NSDictionary, NSData, NSError,
init, dealloc, description, isEqual:, hash, copy
```

**Swift标准库**：
```
String, Array, Dictionary, Int, Double, Bool,
init, deinit, description
```

### 8.2 混淆映射表示例

```json
{
    "timestamp": "2025-10-13T10:30:00",
    "project": "MyApp",
    "version": "1.0.0",

    "mappings": {
        "classes": {
            "ViewController": "Abc123Def",
            "UserModel": "Xyz456Ghi",
            "NetworkManager": "Jkl789Mno"
        },
        "methods": {
            "loadData": "pqr012Stu",
            "saveData:": "vwx345Yza",
            "fetchUserInfo:completion:": "bcd678Efg"
        },
        "properties": {
            "userName": "hij901Klm",
            "userAge": "nop234Qrs"
        },
        "files": {
            "ViewController.h": "Abc123Def.h",
            "ViewController.m": "Abc123Def.m"
        },
        "resources": {
            "icon_home.png": "tuv567Wxy.png",
            "background.jpg": "zab890Cde.jpg"
        }
    }
}
```

### 8.3 参考资料

- **Objective-C Runtime**: https://developer.apple.com/documentation/objectivec/objective-c_runtime
- **Swift Language Guide**: https://docs.swift.org/swift-book/
- **Xcode Project Format**: https://developer.apple.com/documentation/xcode
- **代码混淆最佳实践**: 商业混淆软件案例研究

---

## 九、总结

本文档详细设计了一个iOS代码混淆功能模块，主要特点：

1. **模块化架构** - 清晰的职责分离，便于维护和扩展
2. **功能完整** - 覆盖核心混淆需求（P0/P1优先级）
3. **可扩展性** - 预留接口支持未来功能扩展
4. **用户友好** - 直观的GUI界面和详细的日志
5. **安全可靠** - 备份、回滚机制保证安全性

下一步将按照实施计划逐步实现各个模块，首先从基础框架开始，逐步构建核心功能。

---

**文档版本**: v1.0.0
**最后更新**: 2025-10-13
**作者**: Claude Code
**状态**: 设计阶段完成，待开发实施
