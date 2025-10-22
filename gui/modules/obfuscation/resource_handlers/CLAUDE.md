# 资源处理器模块

## 模块概述
iOS资源文件高级处理模块，支持Assets、图片、音频、字体的混淆和修改。

## 架构设计

### 模块结构 (v2.3.1)
```
resource_handlers/
├── common.py (16行)              # ProcessResult数据结构
├── assets_handler.py (300行)    # Assets.xcassets处理
├── image_modifier.py (259行)    # 图片像素修改
├── audio_modifier.py (282行)    # 音频hash修改
├── font_handler.py (367行)      # 字体文件处理
└── resource_coordinator.py (124) # 资源协调器
```

**设计模式**: 协调器模式 - `AdvancedResourceHandler`统一管理所有子处理器

**拆分历史**: 2025-10-22从1322行单文件拆分为6个独立模块

## 核心组件

### ProcessResult (common.py)
```python
@dataclass
class ProcessResult:
    success: bool          # 处理是否成功
    file_path: str         # 文件路径
    operation: str         # 操作类型
    error: Optional[str]   # 错误信息
    details: Dict          # 详细信息
```

### AdvancedAssetsHandler
处理Assets.xcassets资源目录

**功能**:
- `.imageset` - 图片资源重命名
- `.colorset` - 颜色微调(±0.005 RGB)
- `.dataset` - 数据资源处理
- `Contents.json` - 元数据更新

**用法**:
```python
handler = AdvancedAssetsHandler({'OldName': 'NewName'})
handler.process_assets_catalog('path/to/Assets.xcassets')
```

### ImagePixelModifier
图片像素级轻微修改（不影响视觉）

**策略**:
- 小图片(<4MP): 批量处理
- 大图片(≥4MP): 采样处理(step=3)
- RGB调整: ±intensity * 255 (默认0.02)

**用法**:
```python
modifier = ImagePixelModifier(intensity=0.02)
result = modifier.modify_image_pixels('icon.png')
```

### AudioHashModifier
音频文件hash修改（保持可播放）

**支持格式**:
- `.mp3/.m4a/.aac` - 添加ID3v2标签
- `.wav/.aiff` - 添加静默数据 + RIFF更新
- 其他 - 添加随机字节

**用法**:
```python
modifier = AudioHashModifier()
result = modifier.modify_audio_hash('sound.mp3', verify_integrity=True)
```

### FontFileHandler
字体文件内部名称混淆

**支持格式**: `.ttf`, `.otf`

**操作**:
- 修改`name`表(nameID 1/4/6)
- 重新计算校验和(checkSumAdjustment)
- 文件重命名

**用法**:
```python
handler = FontFileHandler({'OldFont': 'NewFont'})
result = handler.process_font_file('Custom.ttf', rename=True)
```

### AdvancedResourceHandler (协调器)
统一入口，整合所有子处理器

**用法**:
```python
# 初始化
handler = AdvancedResourceHandler(
    symbol_mappings={'Icon': 'Img01'},
    image_intensity=0.02
)

# 处理Assets
handler.process_assets_catalog('Assets.xcassets')

# 修改图片
handler.modify_image_pixels('logo.png')

# 修改音频
handler.modify_audio_hash('bgm.mp3')

# 处理字体
handler.process_font_file('CustomFont.ttf')

# 获取统计
stats = handler.get_statistics()
# {'assets': {...}, 'images': {...}, 'audio': {...}, 'fonts': {...}}
```

## 导入方式

### 向后兼容（推荐）
```python
from gui.modules.obfuscation.advanced_resource_handler import AdvancedResourceHandler
handler = AdvancedResourceHandler(mappings)
```

### 直接导入
```python
from gui.modules.obfuscation.resource_handlers import (
    AdvancedResourceHandler,
    ImagePixelModifier,
    AudioHashModifier,
    FontFileHandler,
)
```

## 统计信息

每个处理器提供`get_statistics()`方法:

```python
# Assets统计
{'imagesets_processed': 10, 'images_renamed': 5, ...}

# 图片统计
{'images_modified': 20, 'pixels_adjusted': 5000000, ...}

# 音频统计
{'audio_files_modified': 8, 'id3_tags_added': 5, ...}

# 字体统计
{'fonts_processed': 3, 'name_tables_modified': 3, ...}
```

## 性能特性

### 图片处理
- **小图片**: 批量处理全部像素
- **大图片**: 采样处理(每隔3像素)
- **进度回调**: 支持实时进度更新

### 音频处理
- **完整性验证**: 可选的格式验证
- **最小修改**: 仅添加元数据/静默数据
- **格式兼容**: 保持音频可播放

### 字体处理
- **安全修改**: 仅修改name表
- **校验和更新**: 自动重新计算
- **容错处理**: 失败不影响整体流程

## 错误处理

所有方法返回`ProcessResult`，统一错误处理:

```python
result = handler.process_font_file('font.ttf')
if not result.success:
    print(f"错误: {result.error}")
else:
    print(f"成功: {result.details}")
```

## 依赖项

- **核心**: `pathlib`, `json`, `struct`, `random`
- **图片**: `PIL` (Pillow) - 可选,图片处理需要
- **音频/字体**: 无额外依赖

## 最佳实践

1. **符号映射**: 提前准备完整的映射字典
2. **进度回调**: 大批量处理建议启用进度回调
3. **完整性验证**: 音频处理建议开启验证
4. **错误处理**: 检查`ProcessResult.success`
5. **统计监控**: 定期获取统计信息

## 注意事项

- 图片处理需要安装Pillow: `pip install Pillow`
- 字体处理仅支持`.ttf`和`.otf`格式
- 音频修改不改变播放内容,仅修改hash
- Assets处理会递归处理所有子目录

---

**版本**: v2.3.1
**更新**: 2025-10-22
**作者**: Claude Code
**重构**: 从1322行单文件拆分为6个模块
