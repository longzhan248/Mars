# 混淆引擎核心模块

## 模块概述
iOS代码混淆引擎的模块化实现，将原始1218行单文件重构为8个职责清晰的处理器。

## 架构设计

```
gui/modules/obfuscation/engine/
├── common.py                 # 数据模型 (23行)
├── project_init.py           # 项目初始化 (120行)
├── source_processor.py       # 源文件处理 (280行)
├── feature_processor.py      # P2功能处理 (277行)
├── resource_processor.py     # 资源处理 (227行)
├── result_export.py          # 结果导出 (403行)
├── engine_coordinator.py     # 主协调器 (270行)
└── __init__.py               # 模块导出 (32行)
```

**向后兼容**: `../obfuscation_engine.py` (81行重定向接口)

## 核心模块

### 1. common.py - 数据模型
定义混淆引擎的核心数据结构。

```python
@dataclass
class ObfuscationResult:
    """混淆结果"""
    success: bool                    # 是否成功
    output_dir: str                  # 输出目录
    project_name: str                # 项目名称
    files_processed: int = 0         # 处理的文件数
    files_failed: int = 0            # 失败的文件数
    total_replacements: int = 0      # 总替换次数
    elapsed_time: float = 0.0        # 耗时（秒）
    mapping_file: str = ""           # 映射文件路径
    errors: List[str] = []           # 错误信息
    warnings: List[str] = []         # 警告信息
```

### 2. project_init.py - 项目初始化
负责项目分析、白名单初始化和名称生成器初始化。

```python
class ProjectInitializer:
    """项目初始化处理器"""

    def analyze_project(project_path, callback) -> bool
        """分析项目结构 (占总进度10%)"""

    def initialize_whitelist(project_path) -> bool
        """初始化白名单（自动检测第三方库）"""

    def initialize_name_generator()
        """初始化名称生成器（支持增量混淆）"""
```

**职责**:
- 项目结构分析 (Objective-C/Swift文件、XIB、Assets等)
- 第三方库自动检测 (CocoaPods/SPM/Carthage)
- 名称生成策略配置 (random/prefix/pattern/dictionary)

### 3. source_processor.py - 源文件处理
负责源代码解析和转换，支持增量编译、并行处理和缓存。

```python
class SourceProcessor:
    """源文件处理器"""

    def parse_source_files(callback) -> bool
        """解析源文件 (占总进度20%, 30%-50%)"""
        # 支持: 增量编译、并行解析、缓存加速

    def transform_code(callback) -> bool
        """转换代码 (占总进度10%, 50%-60%)"""
        # 支持: 多进程并行转换
```

**性能优化**:
- **增量编译**: 仅处理修改的文件
- **并行解析**: 多线程处理 (10+文件自动启用)
- **解析缓存**: 100-300x提升 (可选)
- **多进程转换**: 超大项目 (50k+行) 自动启用

### 4. feature_processor.py - P2功能处理
负责字符串加密和垃圾代码生成。

```python
class FeatureProcessor:
    """P2功能处理器"""

    def encrypt_strings(transform_results, callback)
        """字符串加密 (占总进度5%, 60%-65%)"""
        # 支持: xor/base64/shift/rot13/aes128/aes256

    def insert_garbage_code(transform_results, output_dir, callback)
        """插入垃圾代码 (占总进度5%, 65%-70%)"""
        # 复杂度: simple/moderate/complex
```

**P2深度集成**:
- 字符串加密: 自动生成解密宏/函数
- 垃圾代码: ObjC和Swift独立生成
- 文件追踪: 记录需要后处理的文件

### 5. resource_processor.py - 资源处理
负责Assets、XIB、图片、音频、字体等资源文件处理。

```python
class ResourceProcessor:
    """资源处理器"""

    def process_resources(callback)
        """处理资源文件 (占总进度5%, 70%-75%)"""
```

**支持的资源**:
- **Assets.xcassets**: 图片集/颜色集/数据集
- **XIB/Storyboard**: 类名同步更新 (待完善)
- **图片文件**: 像素微调 (PNG/JPG/JPEG)
- **音频文件**: Hash修改 (MP3/M4A/WAV/AIFF)
- **字体文件**: 处理 (TTF/OTF/TTC)

### 6. result_export.py - 结果导出
负责保存混淆结果、P2后处理和映射文件导出。

```python
class ResultExporter:
    """结果导出器"""

    def save_results(output_dir, transform_results, file_changes, result) -> bool
        """保存混淆结果 (占总进度5%, 75%-80%)"""
        # 支持: 文件名同步重命名、增量缓存更新

    def p2_post_processing(output_dir, ...)
        """P2后处理 (占总进度10%, 80%-90%)"""
        # 1. 生成解密宏/函数文件
        # 2. 自动添加到Xcode项目

    def export_mapping(output_dir, ...) -> str
        """导出映射文件 (占总进度10%, 90%-100%)"""
        # 包含: 符号映射 + P2统计信息
```

**P2后处理流程**:
1. 为ObjC生成 `StringDecryption.h` (解密宏)
2. 为Swift生成 `StringDecryption.swift` (解密函数)
3. 为加密文件自动添加导入语句
4. 自动添加文件到Xcode项目 (需要pbxproj库)

### 7. engine_coordinator.py - 主协调器
整合所有处理器，协调完整的混淆流程。

```python
class ObfuscationEngine:
    """混淆引擎主协调器"""

    def obfuscate(project_path, output_dir, callback) -> ObfuscationResult
        """执行完整混淆流程"""
        # 步骤1: 初始化项目 (0-25%)
        # 步骤2: 源文件处理 (25-60%)
        # 步骤3: P2功能处理 (60-70%)
        # 步骤4: 资源处理 (70-75%)
        # 步骤5: 保存和导出 (75-100%)

    def get_statistics() -> Dict
        """获取详细统计信息"""
```

**流程编排**:
```
初始化 → 源处理 → 功能增强 → 资源处理 → 结果导出
  ↓         ↓          ↓           ↓           ↓
分析      解析      字符串      Assets      保存
白名单    转换      垃圾代码    图片        P2后处理
名称生成              音频        映射导出
                      字体
```

## 使用示例

### 基础使用
```python
from gui.modules.obfuscation.engine import ObfuscationEngine, ObfuscationResult
from gui.modules.obfuscation.config_manager import ConfigManager

# 1. 创建配置
config_manager = ConfigManager()
config = config_manager.get_template("standard")

# 2. 创建引擎
engine = ObfuscationEngine(config)

# 3. 定义进度回调
def progress_callback(progress, message):
    print(f"[{progress*100:.0f}%] {message}")

# 4. 执行混淆
result = engine.obfuscate(
    project_path="/path/to/ios/project",
    output_dir="/path/to/output",
    progress_callback=progress_callback
)

# 5. 检查结果
if result.success:
    print(f"✅ 混淆成功!")
    print(f"   处理文件: {result.files_processed}")
    print(f"   耗时: {result.elapsed_time:.2f}秒")
    print(f"   映射文件: {result.mapping_file}")
else:
    print(f"❌ 混淆失败:")
    for error in result.errors:
        print(f"   {error}")
```

### 向后兼容使用
```python
# 旧代码依然可用
from gui.modules.obfuscation.obfuscation_engine import ObfuscationEngine

engine = ObfuscationEngine()
result = engine.obfuscate(project_path, output_dir)
```

### 独立使用处理器
```python
from gui.modules.obfuscation.engine import ProjectInitializer, SourceProcessor

# 仅项目分析
initializer = ProjectInitializer(config)
if initializer.analyze_project("/path/to/project"):
    print(f"项目: {initializer.project_structure.project_name}")
    print(f"文件数: {initializer.project_structure.total_files}")

# 仅源文件处理
source_processor = SourceProcessor(config, project_structure, ...)
source_processor.parse_source_files()
source_processor.transform_code()
```

## 配置选项

### 基础混淆
```python
config.class_names = True          # 混淆类名
config.method_names = True         # 混淆方法名
config.property_names = True       # 混淆属性名
config.protocol_names = True       # 混淆协议名
```

### P2功能
```python
config.string_encryption = True    # 字符串加密
config.encryption_algorithm = 'xor'  # xor/base64/shift/rot13/aes128/aes256
config.encryption_key = 'MyKey'
config.string_min_length = 4

config.insert_garbage_code = True
config.garbage_complexity = 'moderate'  # simple/moderate/complex
config.garbage_count = 20
```

### 性能优化
```python
config.enable_incremental = True   # 增量编译
config.parallel_processing = True  # 并行处理
config.max_workers = 8             # 线程/进程数

config.enable_parse_cache = True   # 解析缓存
config.max_memory_cache = 100      # 内存缓存数量
config.max_disk_cache = 1000       # 磁盘缓存数量
config.clear_cache = False         # 是否清空缓存
```

### 资源处理
```python
config.modify_resource_files = True   # 处理XIB/Storyboard
config.modify_color_values = True     # 处理图片
config.modify_audio_files = True      # 处理音频
config.modify_font_files = True       # 处理字体
config.image_intensity = 0.02         # 图片修改强度
```

## 重构成果

### 量化指标
- **原始**: 1218行单文件
- **重构**: 8个模块，1632行
- **模块化提升**: 800% (1文件 → 9文件)
- **最大文件降低**: -67% (1218行 → 403行)
- **平均文件大小**: 204行

### 技术优势
1. **清晰分层**: 职责分离，易于理解
2. **可维护性**: 单个模块易于定位和修改
3. **可扩展性**: 便于添加新处理器
4. **可测试性**: 每个模块可独立测试
5. **向后兼容**: 100%保持原接口

### 性能特性
- **增量编译**: 仅处理变更文件
- **并行处理**: 多线程/多进程加速
- **智能缓存**: 100-300x解析提速
- **流式处理**: 支持超大项目

## 开发指南

### 添加新处理器
```python
# 1. 创建新处理器
class CustomProcessor:
    def __init__(self, config):
        self.config = config

    def process(self, data, callback=None):
        # 实现处理逻辑
        pass

# 2. 在engine_coordinator.py中集成
class ObfuscationEngine:
    def obfuscate(...):
        custom_processor = CustomProcessor(self.config)
        custom_processor.process(data, callback)
```

### 扩展P2功能
```python
# 在feature_processor.py中添加新方法
class FeatureProcessor:
    def new_feature(self, ...):
        """新的代码混淆功能"""
        pass
```

### 调试技巧
```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 单独测试处理器
initializer = ProjectInitializer(config)
initializer.analyze_project(project_path)
print(initializer.project_structure)
```

## 常见问题

**Q: 如何禁用某个功能？**
```python
config.string_encryption = False
config.insert_garbage_code = False
```

**Q: 如何查看详细统计？**
```python
stats = engine.get_statistics()
print(stats['project'])      # 项目信息
print(stats['transformer'])  # 转换统计
print(stats['string_encryption'])  # 加密统计
```

**Q: 缓存存放在哪里？**
```python
# 默认在输出目录下
output_dir/.obfuscation_cache/
```

**Q: 如何强制重新解析？**
```python
config.clear_cache = True
# 或禁用缓存
config.enable_parse_cache = False
```

## 版本历史

- **v5.0** (2025-10-23): Phase 5重构完成，模块化架构
- **v4.0** (2025-10-21): P2深度集成，性能优化
- **v3.0** (2025-10-15): 垃圾代码和字符串加密
- **v2.0** (2025-10-10): 增量编译和并行处理
- **v1.0** (2025-09-20): 初始版本

---

**文档版本**: v1.0
**最后更新**: 2025-10-23
**重构状态**: ✅ Phase 5完成
**总代码**: 1632行 (8个模块)
