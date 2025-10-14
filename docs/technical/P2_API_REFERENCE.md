# P2高级资源处理 - API参考文档

**版本**: v1.0.0
**日期**: 2025-10-14
**模块**: `gui.modules.obfuscation.advanced_resource_handler`

---

## 目录

- [核心数据类](#核心数据类)
  - [ProcessResult](#processresult)
- [主要类](#主要类)
  - [AdvancedAssetsHandler](#advancedassetshandler)
  - [ImagePixelModifier](#imagepixelmodifier)
  - [AudioHashModifier](#audiohashmodifier)
  - [FontFileHandler](#fontfilehandler)
  - [AdvancedResourceHandler](#advancedresourcehandler)
- [使用示例](#使用示例)
- [错误处理](#错误处理)
- [性能考虑](#性能考虑)

---

## 核心数据类

### ProcessResult

处理结果的统一数据结构。

#### 定义

```python
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class ProcessResult:
    """处理结果数据类"""
    success: bool
    message: str
    error: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
```

#### 字段说明

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `success` | `bool` | 是 | 处理是否成功 |
| `message` | `str` | 是 | 简短的处理消息 |
| `error` | `Optional[str]` | 否 | 错误信息（失败时） |
| `details` | `Optional[Dict[str, Any]]` | 否 | 详细信息字典 |

#### 示例

```python
# 成功结果
result = ProcessResult(
    success=True,
    message="图片处理成功",
    details={
        'original_hash': 'a1b2c3d4...',
        'new_hash': 'e5f6g7h8...',
        'pixels_modified': 1024000
    }
)

# 失败结果
result = ProcessResult(
    success=False,
    message="处理失败",
    error="文件不存在: /path/to/image.png"
)
```

---

## 主要类

### AdvancedAssetsHandler

处理iOS Assets.xcassets目录的所有资源类型。

#### 构造函数

```python
def __init__(self, symbol_mappings: Dict[str, str] = None)
```

**参数**:
- `symbol_mappings` (Dict[str, str], 可选): 符号名称映射字典
  - 键: 原始符号名
  - 值: 混淆后的符号名
  - 默认: `{}`

**示例**:
```python
handler = AdvancedAssetsHandler(symbol_mappings={
    'UserAvatar': 'WHC001',
    'AppLogo': 'WHC002'
})
```

#### 方法

##### process_assets_catalog

处理整个Assets.xcassets目录。

```python
def process_assets_catalog(
    self,
    assets_path: str,
    output_path: str = None,
    rename_images: bool = True,
    process_colors: bool = True,
    process_data: bool = True
) -> bool
```

**参数**:
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `assets_path` | `str` | - | Assets.xcassets目录路径 |
| `output_path` | `str` | `None` | 输出目录路径（None表示原地修改） |
| `rename_images` | `bool` | `True` | 是否重命名imageset |
| `process_colors` | `bool` | `True` | 是否处理colorset |
| `process_data` | `bool` | `True` | 是否处理dataset |

**返回值**: `bool` - 处理是否成功

**异常**:
- `FileNotFoundError`: Assets目录不存在
- `PermissionError`: 没有读写权限
- `json.JSONDecodeError`: Contents.json格式错误

**示例**:
```python
success = handler.process_assets_catalog(
    assets_path="/path/to/Assets.xcassets",
    output_path="/path/to/output",
    rename_images=True,
    process_colors=True,
    process_data=True
)

if success:
    print("Assets处理完成")
else:
    print("Assets处理失败")
```

**处理流程**:
1. 遍历Assets目录
2. 识别资源类型（imageset/colorset/dataset）
3. 解析Contents.json
4. 应用符号映射重命名
5. 更新JSON文件引用
6. 复制到输出目录

##### process_imageset

处理单个imageset。

```python
def process_imageset(
    self,
    imageset_path: str,
    output_path: str = None
) -> ProcessResult
```

**参数**:
- `imageset_path` (str): imageset目录路径
- `output_path` (str, 可选): 输出路径

**返回值**: `ProcessResult` - 处理结果

**示例**:
```python
result = handler.process_imageset(
    imageset_path="/path/to/UserAvatar.imageset",
    output_path="/path/to/output"
)

if result.success:
    print(f"处理成功: {result.details['new_name']}")
```

##### process_colorset

处理单个colorset。

```python
def process_colorset(
    self,
    colorset_path: str,
    output_path: str = None
) -> ProcessResult
```

**参数**:
- `colorset_path` (str): colorset目录路径
- `output_path` (str, 可选): 输出路径

**返回值**: `ProcessResult` - 处理结果

##### process_dataset

处理单个dataset。

```python
def process_dataset(
    self,
    dataset_path: str,
    output_path: str = None
) -> ProcessResult
```

**参数**:
- `dataset_path` (str): dataset目录路径
- `output_path` (str, 可选): 输出路径

**返回值**: `ProcessResult` - 处理结果

---

### ImagePixelModifier

图片像素级修改器，改变图片hash但保持视觉一致性。

#### 构造函数

```python
def __init__(
    self,
    intensity: float = 0.02,
    seed: Optional[int] = None
)
```

**参数**:
- `intensity` (float): 修改强度，范围[0.0, 1.0]
  - 0.01: 极微小（几乎不可见）
  - 0.02: 微小（推荐值）
  - 0.05: 轻微（可察觉）
  - 0.10: 显著（明显偏移）
- `seed` (int, 可选): 随机种子（确定性修改）

**示例**:
```python
# 标准修改器
modifier = ImagePixelModifier(intensity=0.02)

# 确定性修改器
modifier = ImagePixelModifier(intensity=0.02, seed=12345)
```

#### 方法

##### modify_image_pixels

修改图片像素。

```python
def modify_image_pixels(
    self,
    image_path: str,
    output_path: str = None
) -> ProcessResult
```

**参数**:
- `image_path` (str): 输入图片路径
- `output_path` (str, 可选): 输出图片路径（None表示覆盖原文件）

**返回值**: `ProcessResult` - 包含以下details:
```python
{
    'original_hash': str,      # 原始MD5哈希
    'new_hash': str,           # 新MD5哈希
    'pixels_modified': int,    # 修改的像素数
    'size': tuple,             # 图片尺寸(width, height)
    'format': str              # 图片格式(PNG/JPEG/GIF)
}
```

**异常**:
- `FileNotFoundError`: 图片文件不存在
- `PIL.UnidentifiedImageError`: 无法识别的图片格式
- `ImportError`: Pillow库未安装

**示例**:
```python
result = modifier.modify_image_pixels(
    image_path="/path/to/icon.png",
    output_path="/path/to/modified_icon.png"
)

if result.success:
    print(f"原始hash: {result.details['original_hash']}")
    print(f"新hash: {result.details['new_hash']}")
    print(f"修改像素: {result.details['pixels_modified']}")
else:
    print(f"修改失败: {result.error}")
```

**支持的格式**:
- PNG
- JPEG/JPG
- GIF
- BMP
- TIFF

**算法原理**:
```python
# 对每个像素的RGB通道:
for pixel in image.pixels:
    r, g, b = pixel

    # 生成随机偏移
    r_offset = random.uniform(-intensity, +intensity) * 255
    g_offset = random.uniform(-intensity, +intensity) * 255
    b_offset = random.uniform(-intensity, +intensity) * 255

    # 应用偏移并钳制到[0, 255]
    new_r = clamp(r + r_offset, 0, 255)
    new_g = clamp(g + g_offset, 0, 255)
    new_b = clamp(b + b_offset, 0, 255)

    pixel = (new_r, new_g, new_b)
```

##### verify_modification

验证图片是否已修改。

```python
def verify_modification(
    self,
    original_path: str,
    modified_path: str
) -> Dict[str, Any]
```

**参数**:
- `original_path` (str): 原始图片路径
- `modified_path` (str): 修改后图片路径

**返回值**: 字典包含:
```python
{
    'hash_changed': bool,         # hash是否改变
    'original_hash': str,         # 原始hash
    'modified_hash': str,         # 修改后hash
    'visual_similarity': float    # 视觉相似度(0.0-1.0)
}
```

---

### AudioHashModifier

音频文件hash修改器，保持音频可播放性。

#### 构造函数

```python
def __init__(self)
```

无参数，创建默认修改器。

**示例**:
```python
modifier = AudioHashModifier()
```

#### 方法

##### modify_audio_hash

修改音频文件hash。

```python
def modify_audio_hash(
    self,
    audio_path: str,
    output_path: str = None
) -> ProcessResult
```

**参数**:
- `audio_path` (str): 输入音频路径
- `output_path` (str, 可选): 输出音频路径

**返回值**: `ProcessResult` - 包含以下details:
```python
{
    'format': str,              # 音频格式(MP3/WAV/M4A/AIFF)
    'original_size': int,       # 原始大小(字节)
    'new_size': int,            # 新大小(字节)
    'bytes_added': int,         # 添加的字节数
    'modification_type': str    # 修改类型(metadata/silent_samples)
}
```

**异常**:
- `FileNotFoundError`: 音频文件不存在
- `ImportError`: mutagen库未安装
- `ValueError`: 不支持的音频格式

**示例**:
```python
result = modifier.modify_audio_hash(
    audio_path="/path/to/sound.mp3",
    output_path="/path/to/modified_sound.mp3"
)

if result.success:
    print(f"格式: {result.details['format']}")
    print(f"添加字节: {result.details['bytes_added']}")
    print(f"修改类型: {result.details['modification_type']}")
```

**支持的格式和策略**:

| 格式 | 策略 | 描述 | 字节增加 |
|------|------|------|---------|
| MP3 | ID3标签 | 添加TXXX自定义标签 | ~128字节 |
| M4A | 元数据 | 添加隐藏注释 | ~64字节 |
| AAC | 容器标签 | 修改容器元数据 | ~100字节 |
| WAV | 静音采样 | 追加静音采样 | ~400字节 |
| AIFF | 静音采样 | 追加静音采样 | ~400字节 |

##### _add_mp3_metadata

添加MP3元数据（内部方法）。

```python
def _add_mp3_metadata(self, audio_path: str, output_path: str) -> int
```

**参数**:
- `audio_path` (str): 输入MP3路径
- `output_path` (str): 输出MP3路径

**返回值**: `int` - 添加的字节数

**实现细节**:
```python
from mutagen.id3 import ID3, TXXX

# 读取或创建ID3标签
audio = ID3(audio_path)

# 添加自定义标签
audio.add(TXXX(
    encoding=3,
    desc='OBF_METADATA',
    text=f'Modified at {timestamp}'
))

# 保存
audio.save(output_path)
```

##### _add_wav_silent_samples

添加WAV静音采样（内部方法）。

```python
def _add_wav_silent_samples(
    self,
    audio_path: str,
    output_path: str,
    num_samples: int = 100
) -> int
```

**参数**:
- `audio_path` (str): 输入WAV路径
- `output_path` (str): 输出WAV路径
- `num_samples` (int): 静音采样数量

**返回值**: `int` - 添加的字节数

---

### FontFileHandler

字体文件处理器，支持重命名和元数据修改。

#### 构造函数

```python
def __init__(self, symbol_mappings: Dict[str, str] = None)
```

**参数**:
- `symbol_mappings` (Dict[str, str], 可选): 字体名称映射

**示例**:
```python
handler = FontFileHandler(symbol_mappings={
    'MyCustomFont': 'WHC_Font_001',
    'AppFont-Bold': 'WHC_Font_002'
})
```

#### 方法

##### process_font_file

处理字体文件。

```python
def process_font_file(
    self,
    font_path: str,
    output_path: str = None,
    rename: bool = True,
    modify_metadata: bool = True
) -> ProcessResult
```

**参数**:
- `font_path` (str): 输入字体路径
- `output_path` (str, 可选): 输出目录路径
- `rename` (bool): 是否重命名文件
- `modify_metadata` (bool): 是否修改元数据

**返回值**: `ProcessResult` - 包含以下details:
```python
{
    'format': str,              # 字体格式(TTF/OTF/TTC)
    'original_name': str,       # 原始文件名
    'new_name': str,            # 新文件名
    'output_file': str,         # 输出文件路径
    'metadata_modified': bool   # 元数据是否修改
}
```

**异常**:
- `FileNotFoundError`: 字体文件不存在
- `ImportError`: fonttools库未安装
- `ValueError`: 不支持的字体格式

**示例**:
```python
result = handler.process_font_file(
    font_path="/path/to/MyCustomFont.ttf",
    output_path="/path/to/output",
    rename=True,
    modify_metadata=True
)

if result.success:
    print(f"原始名称: {result.details['original_name']}")
    print(f"新名称: {result.details['new_name']}")
    print(f"输出文件: {result.details['output_file']}")
```

**支持的格式**:
- TTF (TrueType Font)
- OTF (OpenType Font)
- TTC (TrueType Collection)

##### _modify_font_metadata

修改字体元数据（内部方法）。

```python
def _modify_font_metadata(self, font_path: str, output_path: str) -> bool
```

**修改的Name表条目**:
| ID | 名称 | 说明 |
|----|------|------|
| 1 | Family Name | 字体家族名 |
| 4 | Full Name | 完整名称 |
| 6 | PostScript Name | PostScript名称 |

---

### AdvancedResourceHandler

统一的高级资源处理接口，整合所有P2功能。

#### 构造函数

```python
def __init__(
    self,
    symbol_mappings: Dict[str, str] = None,
    image_intensity: float = 0.02
)
```

**参数**:
- `symbol_mappings` (Dict[str, str], 可选): 符号映射字典
- `image_intensity` (float): 图片修改强度

**示例**:
```python
handler = AdvancedResourceHandler(
    symbol_mappings={
        'UserAvatar': 'WHC001',
        'MyFont': 'WHC002'
    },
    image_intensity=0.02
)
```

#### 方法

##### process_assets

处理Assets.xcassets目录。

```python
def process_assets(
    self,
    assets_path: str,
    output_path: str = None
) -> ProcessResult
```

**参数**:
- `assets_path` (str): Assets目录路径
- `output_path` (str, 可选): 输出路径

**返回值**: `ProcessResult`

**示例**:
```python
result = handler.process_assets(
    "/path/to/Assets.xcassets",
    "/path/to/output"
)
```

##### modify_image

修改图片。

```python
def modify_image(
    self,
    image_path: str,
    output_path: str = None
) -> ProcessResult
```

**参数**:
- `image_path` (str): 图片路径
- `output_path` (str, 可选): 输出路径

**返回值**: `ProcessResult`

##### modify_audio

修改音频。

```python
def modify_audio(
    self,
    audio_path: str,
    output_path: str = None
) -> ProcessResult
```

**参数**:
- `audio_path` (str): 音频路径
- `output_path` (str, 可选): 输出路径

**返回值**: `ProcessResult`

##### process_font

处理字体。

```python
def process_font(
    self,
    font_path: str,
    output_path: str = None
) -> ProcessResult
```

**参数**:
- `font_path` (str): 字体路径
- `output_path` (str, 可选): 输出路径

**返回值**: `ProcessResult`

##### get_statistics

获取处理统计。

```python
def get_statistics(self) -> Dict[str, Any]
```

**返回值**: 统计信息字典
```python
{
    'files_processed': int,         # 处理文件总数
    'success_count': int,           # 成功数量
    'failure_count': int,           # 失败数量
    'assets_processed': int,        # Assets处理数
    'images_modified': int,         # 图片修改数
    'audios_modified': int,         # 音频修改数
    'fonts_processed': int,         # 字体处理数
    'total_bytes_modified': int,    # 总修改字节数
    'processing_time': float        # 处理时间(秒)
}
```

**示例**:
```python
stats = handler.get_statistics()
print(f"处理: {stats['files_processed']} 文件")
print(f"成功: {stats['success_count']}")
print(f"失败: {stats['failure_count']}")
print(f"耗时: {stats['processing_time']:.2f}秒")
```

##### reset_statistics

重置统计信息。

```python
def reset_statistics(self) -> None
```

---

## 使用示例

### 基础使用

```python
from gui.modules.obfuscation.advanced_resource_handler import (
    AdvancedResourceHandler
)

# 1. 创建处理器
handler = AdvancedResourceHandler(
    symbol_mappings={
        'UserAvatar': 'WHC001',
        'AppLogo': 'WHC002'
    },
    image_intensity=0.02
)

# 2. 处理不同类型资源
handler.process_assets("/path/to/Assets.xcassets", "/output")
handler.modify_image("/path/to/icon.png", "/output/icon.png")
handler.modify_audio("/path/to/sound.mp3", "/output/sound.mp3")
handler.process_font("/path/to/font.ttf", "/output")

# 3. 获取统计
stats = handler.get_statistics()
print(f"处理完成: {stats['success_count']}/{stats['files_processed']}")
```

### 批量处理

```python
import os
from pathlib import Path

# 批量处理图片
image_dir = Path("/path/to/images")
output_dir = Path("/path/to/output")

handler = AdvancedResourceHandler(image_intensity=0.02)

for image_file in image_dir.glob("*.png"):
    result = handler.modify_image(
        str(image_file),
        str(output_dir / image_file.name)
    )

    if result.success:
        print(f"✅ {image_file.name}")
    else:
        print(f"❌ {image_file.name}: {result.error}")

# 查看统计
stats = handler.get_statistics()
print(f"\n总结: {stats['images_modified']} 张图片已修改")
```

### 错误处理

```python
def safe_process_resource(handler, path, output):
    """安全的资源处理"""
    try:
        result = handler.modify_image(path, output)

        if result.success:
            return result
        else:
            print(f"处理失败: {result.error}")
            return None

    except FileNotFoundError:
        print(f"文件不存在: {path}")
        return None
    except PermissionError:
        print(f"权限不足: {path}")
        return None
    except Exception as e:
        print(f"未知错误: {e}")
        return None
```

### 进度追踪

```python
from typing import List
import os

def process_with_progress(
    handler: AdvancedResourceHandler,
    file_list: List[str],
    output_dir: str
):
    """带进度显示的批量处理"""
    total = len(file_list)

    for i, file_path in enumerate(file_list, 1):
        # 显示进度
        progress = (i / total) * 100
        print(f"\r处理进度: {progress:.1f}% ({i}/{total})", end='')

        # 处理文件
        ext = os.path.splitext(file_path)[1].lower()
        output_path = os.path.join(output_dir, os.path.basename(file_path))

        if ext in ['.png', '.jpg', '.jpeg']:
            handler.modify_image(file_path, output_path)
        elif ext in ['.mp3', '.wav', '.m4a']:
            handler.modify_audio(file_path, output_path)
        elif ext in ['.ttf', '.otf']:
            handler.process_font(file_path, output_path)

    print()  # 换行

    # 显示统计
    stats = handler.get_statistics()
    print(f"完成: {stats['success_count']} 成功, {stats['failure_count']} 失败")
```

---

## 错误处理

### 常见异常

#### FileNotFoundError
```python
try:
    result = handler.modify_image("/nonexistent/image.png")
except FileNotFoundError as e:
    print(f"文件不存在: {e}")
```

#### ImportError
```python
try:
    modifier = ImagePixelModifier()
except ImportError as e:
    print("请安装Pillow库: pip install Pillow")
```

#### ValueError
```python
try:
    result = handler.process_font("unsupported.woff")
except ValueError as e:
    print(f"不支持的格式: {e}")
```

### 推荐的错误处理模式

```python
def robust_process(handler, file_path, output_path):
    """健壮的处理流程"""
    # 检查输入
    if not os.path.exists(file_path):
        return ProcessResult(
            success=False,
            message="文件不存在",
            error=f"File not found: {file_path}"
        )

    # 检查权限
    if not os.access(file_path, os.R_OK):
        return ProcessResult(
            success=False,
            message="无读取权限",
            error=f"Permission denied: {file_path}"
        )

    # 处理
    try:
        result = handler.modify_image(file_path, output_path)
        return result

    except ImportError as e:
        return ProcessResult(
            success=False,
            message="缺少依赖库",
            error=f"Missing dependency: {e}"
        )

    except Exception as e:
        return ProcessResult(
            success=False,
            message="处理失败",
            error=f"Unexpected error: {e}"
        )
```

---

## 性能考虑

### 内存使用

```python
# 对于大图片，使用流式处理
def process_large_image(image_path, output_path):
    """处理大图片时的内存优化"""
    # 分块读取
    # 逐块处理
    # 避免一次性加载整个图片
    pass
```

### 并行处理

```python
from concurrent.futures import ThreadPoolExecutor

def parallel_process(file_list, handler, output_dir):
    """并行处理多个文件"""
    def process_single(file_path):
        output_path = os.path.join(output_dir, os.path.basename(file_path))
        return handler.modify_image(file_path, output_path)

    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(process_single, file_list))

    return results
```

### 缓存优化

```python
import hashlib
import json

class CachedHandler:
    """带缓存的资源处理器"""
    def __init__(self, handler):
        self.handler = handler
        self.cache = self._load_cache()

    def process_with_cache(self, file_path, output_path):
        # 计算文件hash
        file_hash = self._get_file_hash(file_path)

        # 检查缓存
        if file_hash in self.cache:
            print(f"使用缓存: {file_path}")
            return self.cache[file_hash]

        # 处理文件
        result = self.handler.modify_image(file_path, output_path)

        # 更新缓存
        self.cache[file_hash] = result
        self._save_cache()

        return result
```

---

## 版本历史

### v1.0.0 (2025-10-14)
- ✅ 初始发布
- ✅ 完整的P2功能API
- ✅ 100%文档覆盖

---

## 相关文档

- [P2功能增强完成报告](./P2_ADVANCED_RESOURCES_REPORT.md)
- [iOS代码混淆模块指南](../gui/modules/obfuscation/CLAUDE.md)
- [测试文档](../../tests/test_p2_advanced_resources.py)

---

**文档版本**: v1.0.0
**最后更新**: 2025-10-14
**维护者**: Claude Code
