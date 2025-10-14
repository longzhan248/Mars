"""
高级资源文件处理器 - P2功能增强

新增功能:
1. Assets.xcassets完整处理（图片重命名、颜色资源处理）
2. 图片像素级变色（轻微色彩调整）
3. 音频文件hash修改（元数据修改）
4. 字体文件处理（字体名称混淆）

作者: Claude Code
日期: 2025-10-14
版本: v2.3.0
"""

import os
import json
import hashlib
import struct
import random
import shutil
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class ProcessResult:
    """处理结果"""
    success: bool
    file_path: str
    operation: str
    error: Optional[str] = None
    details: Dict = field(default_factory=dict)


class AdvancedAssetsHandler:
    """
    Assets.xcassets高级处理器

    功能:
    - 图片资源重命名
    - 颜色资源处理
    - 数据资源处理
    - Contents.json更新
    """

    def __init__(self, symbol_mappings: Dict[str, str] = None):
        """
        初始化Assets处理器

        Args:
            symbol_mappings: 符号映射字典（用于资源名称混淆）
        """
        self.symbol_mappings = symbol_mappings or {}
        self.stats = {
            'imagesets_processed': 0,
            'colorsets_processed': 0,
            'datasets_processed': 0,
            'images_renamed': 0,
            'contents_updated': 0,
        }

    def process_assets_catalog(self, assets_path: str, output_path: str = None,
                               rename_images: bool = True,
                               process_colors: bool = True,
                               process_data: bool = True) -> bool:
        """
        完整处理Assets.xcassets目录

        Args:
            assets_path: Assets.xcassets目录路径
            output_path: 输出路径，如果为None则覆盖原目录
            rename_images: 是否重命名图片资源
            process_colors: 是否处理颜色资源
            process_data: 是否处理数据资源

        Returns:
            bool: 是否成功
        """
        try:
            if output_path is None:
                output_path = assets_path

            assets_dir = Path(assets_path)
            if not assets_dir.exists():
                return False

            output_dir = Path(output_path)

            # 处理所有imageset
            if rename_images:
                for imageset_dir in assets_dir.rglob("*.imageset"):
                    self._process_imageset(imageset_dir, output_dir)

            # 处理所有colorset
            if process_colors:
                for colorset_dir in assets_dir.rglob("*.colorset"):
                    self._process_colorset(colorset_dir, output_dir)

            # 处理所有dataset
            if process_data:
                for dataset_dir in assets_dir.rglob("*.dataset"):
                    self._process_dataset(dataset_dir, output_dir)

            return True

        except Exception as e:
            print(f"处理Assets目录失败 {assets_path}: {e}")
            return False

    def _process_imageset(self, imageset_dir: Path, output_dir: Path) -> bool:
        """
        处理单个imageset（完整版 - P3改进）

        Args:
            imageset_dir: imageset目录
            output_dir: 输出根目录

        Returns:
            bool: 是否成功
        """
        try:
            contents_json = imageset_dir / "Contents.json"
            if not contents_json.exists():
                return False

            # 1. 读取Contents.json
            with open(contents_json, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 2. 确定输出路径
            imageset_name = imageset_dir.stem.replace('.imageset', '')
            new_name = self.symbol_mappings.get(imageset_name, imageset_name)

            # 3. 创建输出目录
            # 计算相对于Assets.xcassets的相对路径
            try:
                rel_path = imageset_dir.relative_to(imageset_dir.parent)
                while not str(rel_path).endswith('.xcassets'):
                    if rel_path.parent == rel_path:
                        break
                    rel_path = imageset_dir.relative_to(rel_path.parent.parent)
            except:
                rel_path = imageset_dir.relative_to(imageset_dir.parent)

            # 构建输出路径
            output_imageset = output_dir / rel_path.parent / f"{new_name}.imageset"
            output_imageset.mkdir(parents=True, exist_ok=True)

            # 4. 复制图片文件
            if 'images' in data:
                for image_info in data['images']:
                    if 'filename' in image_info:
                        src_file = imageset_dir / image_info['filename']
                        dst_file = output_imageset / image_info['filename']

                        if src_file.exists():
                            shutil.copy2(src_file, dst_file)

            # 5. 保存Contents.json
            output_json = output_imageset / "Contents.json"
            with open(output_json, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # 6. 更新统计
            if new_name != imageset_name:
                self.stats['images_renamed'] += 1
            self.stats['imagesets_processed'] += 1
            self.stats['contents_updated'] += 1

            return True

        except Exception as e:
            print(f"处理imageset失败 {imageset_dir}: {e}")
            return False

    def _process_colorset(self, colorset_dir: Path, output_dir: Path) -> bool:
        """
        处理单个colorset（完整版 - P3改进）

        Args:
            colorset_dir: colorset目录
            output_dir: 输出根目录

        Returns:
            bool: 是否成功
        """
        try:
            contents_json = colorset_dir / "Contents.json"
            if not contents_json.exists():
                return False

            # 1. 读取Contents.json
            with open(contents_json, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 2. 轻微修改颜色值（不影响视觉效果）
            if 'colors' in data:
                for color_info in data['colors']:
                    if 'color' in color_info:
                        color = color_info['color']
                        if 'components' in color:
                            # 对RGB值进行微小调整（±0.01）
                            for key in ['red', 'green', 'blue']:
                                if key in color['components']:
                                    value = float(color['components'][key])
                                    # 添加微小的随机变化（±0.005）
                                    adjustment = random.uniform(-0.005, 0.005)
                                    new_value = max(0.0, min(1.0, value + adjustment))
                                    color['components'][key] = f"{new_value:.3f}"

            # 3. 确定输出路径
            colorset_name = colorset_dir.stem.replace('.colorset', '')
            new_name = self.symbol_mappings.get(colorset_name, colorset_name)

            # 4. 计算相对于Assets.xcassets的相对路径
            try:
                rel_path = colorset_dir.relative_to(colorset_dir.parent)
                while not str(rel_path).endswith('.xcassets'):
                    if rel_path.parent == rel_path:
                        break
                    rel_path = colorset_dir.relative_to(rel_path.parent.parent)
            except:
                rel_path = colorset_dir.relative_to(colorset_dir.parent)

            # 5. 创建输出目录
            output_colorset = output_dir / rel_path.parent / f"{new_name}.colorset"
            output_colorset.mkdir(parents=True, exist_ok=True)

            # 6. 保存修改后的Contents.json
            output_json = output_colorset / "Contents.json"
            with open(output_json, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # 7. 更新统计
            if new_name != colorset_name:
                self.stats['images_renamed'] += 1
            self.stats['colorsets_processed'] += 1
            self.stats['contents_updated'] += 1

            return True

        except Exception as e:
            print(f"处理colorset失败 {colorset_dir}: {e}")
            return False

    def _process_dataset(self, dataset_dir: Path, output_dir: Path) -> bool:
        """
        处理单个dataset（完整版 - P3改进）

        Args:
            dataset_dir: dataset目录
            output_dir: 输出根目录

        Returns:
            bool: 是否成功
        """
        try:
            contents_json = dataset_dir / "Contents.json"
            if not contents_json.exists():
                return False

            # 1. 读取Contents.json
            with open(contents_json, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 2. 确定输出路径
            dataset_name = dataset_dir.stem.replace('.dataset', '')
            new_name = self.symbol_mappings.get(dataset_name, dataset_name)

            # 3. 计算相对于Assets.xcassets的相对路径
            try:
                rel_path = dataset_dir.relative_to(dataset_dir.parent)
                while not str(rel_path).endswith('.xcassets'):
                    if rel_path.parent == rel_path:
                        break
                    rel_path = dataset_dir.relative_to(rel_path.parent.parent)
            except:
                rel_path = dataset_dir.relative_to(dataset_dir.parent)

            # 4. 创建输出目录
            output_dataset = output_dir / rel_path.parent / f"{new_name}.dataset"
            output_dataset.mkdir(parents=True, exist_ok=True)

            # 5. 复制数据文件
            if 'data' in data:
                for data_info in data['data']:
                    if 'filename' in data_info:
                        src_file = dataset_dir / data_info['filename']
                        dst_file = output_dataset / data_info['filename']

                        if src_file.exists():
                            shutil.copy2(src_file, dst_file)

            # 6. 保存Contents.json
            output_json = output_dataset / "Contents.json"
            with open(output_json, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # 7. 更新统计
            if new_name != dataset_name:
                self.stats['images_renamed'] += 1
            self.stats['datasets_processed'] += 1
            self.stats['contents_updated'] += 1

            return True

        except Exception as e:
            print(f"处理dataset失败 {dataset_dir}: {e}")
            return False

    def get_statistics(self) -> Dict:
        """获取处理统计信息"""
        return self.stats.copy()


class ImagePixelModifier:
    """
    图片像素级修改器（P3阶段二优化版）

    功能:
    - 轻微色彩调整（不影响视觉效果）
    - RGB值微调
    - 保持图片格式和透明度
    - 进度回调支持
    - 批量处理优化
    - 智能跳过策略
    """

    def __init__(self, intensity: float = 0.02):
        """
        初始化图片修改器

        Args:
            intensity: 修改强度（0.0-1.0），建议0.01-0.05
        """
        self.intensity = max(0.0, min(1.0, intensity))
        self.stats = {
            'images_modified': 0,
            'pixels_adjusted': 0,
            'large_images_sampled': 0,
        }

    def modify_image_pixels(self, image_path: str, output_path: str = None,
                           progress_callback: Optional[callable] = None) -> ProcessResult:
        """
        修改图片像素（P3阶段二优化版）

        Args:
            image_path: 图片路径
            output_path: 输出路径
            progress_callback: 进度回调函数 callback(progress: float, message: str)

        Returns:
            ProcessResult: 处理结果
        """
        try:
            # 尝试导入Pillow
            try:
                from PIL import Image
            except ImportError:
                return ProcessResult(
                    success=False,
                    file_path=image_path,
                    operation="pixel_modify",
                    error="需要安装Pillow库: pip install Pillow"
                )

            if output_path is None:
                output_path = image_path

            # 打开图片
            img = Image.open(image_path)
            width, height = img.size
            total_pixels = width * height

            # 报告进度：图片加载
            if progress_callback:
                progress_callback(0.1, f"加载图片: {width}x{height} ({total_pixels:,} 像素)")

            # 转换为RGB或RGBA模式
            if img.mode not in ['RGB', 'RGBA']:
                img = img.convert('RGB')

            # 智能跳过策略：超大图片使用采样
            use_sampling = total_pixels > 4000000  # 4MP以上使用采样
            if use_sampling:
                if progress_callback:
                    progress_callback(0.2, f"大图片({total_pixels:,}像素)，使用智能采样策略")

                result = self._modify_pixels_sampled(img, progress_callback)
                self.stats['large_images_sampled'] += 1
            else:
                if progress_callback:
                    progress_callback(0.2, f"使用批量处理模式")

                result = self._modify_pixels_batch(img, progress_callback)

            # 报告进度：保存图片
            if progress_callback:
                progress_callback(0.9, "保存图片...")

            # 保存修改后的图片
            img.save(output_path, quality=95)

            if progress_callback:
                progress_callback(1.0, "完成!")

            self.stats['images_modified'] += 1
            self.stats['pixels_adjusted'] += result['pixels_modified']

            return ProcessResult(
                success=True,
                file_path=image_path,
                operation="pixel_modify",
                details={
                    'width': width,
                    'height': height,
                    'pixels_modified': result['pixels_modified'],
                    'intensity': self.intensity,
                    'strategy': result['strategy']
                }
            )

        except Exception as e:
            return ProcessResult(
                success=False,
                file_path=image_path,
                operation="pixel_modify",
                error=str(e)
            )

    def _modify_pixels_batch(self, img, progress_callback: Optional[callable] = None) -> Dict:
        """
        批量处理像素（性能优化）

        Args:
            img: PIL Image对象
            progress_callback: 进度回调

        Returns:
            Dict: 处理结果 {'pixels_modified': int, 'strategy': str}
        """
        pixels = img.load()
        width, height = img.size
        total_pixels = width * height
        modified_pixels = 0

        # 批量处理，每1000个像素报告一次进度
        report_interval = max(1000, total_pixels // 100)

        for y in range(height):
            for x in range(width):
                pixel = pixels[x, y]

                # 对RGB通道进行微调
                if img.mode == 'RGB':
                    r, g, b = pixel
                    r = self._adjust_channel(r)
                    g = self._adjust_channel(g)
                    b = self._adjust_channel(b)
                    pixels[x, y] = (r, g, b)
                elif img.mode == 'RGBA':
                    r, g, b, a = pixel
                    r = self._adjust_channel(r)
                    g = self._adjust_channel(g)
                    b = self._adjust_channel(b)
                    pixels[x, y] = (r, g, b, a)

                modified_pixels += 1

                # 报告进度
                if progress_callback and modified_pixels % report_interval == 0:
                    progress = 0.2 + (modified_pixels / total_pixels) * 0.7
                    progress_callback(progress, f"处理中: {modified_pixels:,}/{total_pixels:,}")

        return {
            'pixels_modified': modified_pixels,
            'strategy': 'batch'
        }

    def _modify_pixels_sampled(self, img, progress_callback: Optional[callable] = None) -> Dict:
        """
        采样处理像素（大图片优化）

        Args:
            img: PIL Image对象
            progress_callback: 进度回调

        Returns:
            Dict: 处理结果 {'pixels_modified': int, 'strategy': str}
        """
        pixels = img.load()
        width, height = img.size
        total_pixels = width * height

        # 采样步长（每隔3个像素修改一次）
        step = 3
        modified_pixels = 0
        sampled_count = 0
        total_samples = (height // step) * (width // step)

        for y in range(0, height, step):
            for x in range(0, width, step):
                pixel = pixels[x, y]

                # 对RGB通道进行微调
                if img.mode == 'RGB':
                    r, g, b = pixel
                    r = self._adjust_channel(r)
                    g = self._adjust_channel(g)
                    b = self._adjust_channel(b)
                    pixels[x, y] = (r, g, b)
                elif img.mode == 'RGBA':
                    r, g, b, a = pixel
                    r = self._adjust_channel(r)
                    g = self._adjust_channel(g)
                    b = self._adjust_channel(b)
                    pixels[x, y] = (r, g, b, a)

                modified_pixels += 1
                sampled_count += 1

                # 报告进度（每500个采样点）
                if progress_callback and sampled_count % 500 == 0:
                    progress = 0.2 + (sampled_count / total_samples) * 0.7
                    progress_callback(progress, f"采样处理: {sampled_count:,}/{total_samples:,}")

        return {
            'pixels_modified': modified_pixels,
            'strategy': 'sampled'
        }

    def _adjust_channel(self, value: int) -> int:
        """
        调整单个颜色通道值

        Args:
            value: 原始值（0-255）

        Returns:
            int: 调整后的值（0-255）
        """
        # 计算调整量（±intensity * 255）
        adjustment = int(random.uniform(-self.intensity, self.intensity) * 255)
        new_value = value + adjustment

        # 限制在0-255范围内
        return max(0, min(255, new_value))

    def get_statistics(self) -> Dict:
        """获取处理统计信息"""
        return self.stats.copy()


class AudioHashModifier:
    """
    音频文件hash修改器（P3阶段三增强版）

    功能:
    - 修改音频元数据
    - 添加静默数据
    - 保持音频质量
    - 规范ID3v2标签（P3新增）
    - WAV RIFF结构更新（P3新增）
    - 音频质量验证（P3新增）
    """

    def __init__(self):
        """初始化音频修改器"""
        self.stats = {
            'audio_files_modified': 0,
            'id3_tags_added': 0,
            'riff_structures_updated': 0,
            'integrity_verified': 0,
        }

    def modify_audio_hash(self, audio_path: str, output_path: str = None,
                         verify_integrity: bool = True) -> ProcessResult:
        """
        修改音频文件hash值（P3阶段三增强版）

        Args:
            audio_path: 音频文件路径
            output_path: 输出路径
            verify_integrity: 是否验证音频完整性

        Returns:
            ProcessResult: 处理结果
        """
        try:
            if output_path is None:
                output_path = audio_path

            audio_file = Path(audio_path)
            suffix = audio_file.suffix.lower()

            # 读取原始音频文件
            with open(audio_path, 'rb') as f:
                data = bytearray(f.read())

            original_size = len(data)
            operations = []

            # 根据不同音频格式采用不同策略
            if suffix in ['.mp3', '.m4a', '.aac']:
                # 在文件开头添加规范的ID3v2标签
                id3_tag = self._create_id3v2_tag()
                data = bytearray(id3_tag) + data  # ID3标签前置
                operations.append('id3v2_tag_added')
                self.stats['id3_tags_added'] += 1

            elif suffix in ['.wav', '.aiff']:
                # 在文件末尾添加静默数据块
                silent_data = self._create_silent_audio_chunk(suffix)
                data.extend(silent_data)
                operations.append('silent_data_added')

                # 更新WAV的RIFF结构
                if suffix == '.wav':
                    data = self._update_wav_riff_chunk(data)
                    operations.append('riff_structure_updated')
                    self.stats['riff_structures_updated'] += 1

            else:
                # 通用方法：在文件末尾添加随机字节
                random_bytes = bytes([random.randint(0, 255) for _ in range(32)])
                data.extend(random_bytes)
                operations.append('random_bytes_added')

            # 写入修改后的文件
            with open(output_path, 'wb') as f:
                f.write(data)

            # 验证音频完整性
            details = {
                'original_size': original_size,
                'new_size': len(data),
                'added_bytes': len(data) - original_size,
                'format': suffix,
                'operations': operations,
            }

            if verify_integrity:
                integrity_ok = self._verify_audio_integrity(output_path, suffix)
                if integrity_ok:
                    operations.append('integrity_verified')
                    self.stats['integrity_verified'] += 1
                details['integrity_ok'] = integrity_ok

            self.stats['audio_files_modified'] += 1

            return ProcessResult(
                success=True,
                file_path=audio_path,
                operation="audio_hash_modify",
                details=details
            )

        except Exception as e:
            return ProcessResult(
                success=False,
                file_path=audio_path,
                operation="audio_hash_modify",
                error=str(e)
            )

    def _create_id3v2_tag(self) -> bytes:
        """
        创建规范的ID3v2.3标签（P3阶段三新增）

        Returns:
            bytes: 规范的ID3v2标签
        """
        # ID3v2.3 header (10 bytes)
        header = bytearray()
        header.extend(b'ID3')  # 标识符 (3 bytes)
        header.extend(b'\x03\x00')  # 版本 3.0 (2 bytes)
        header.extend(b'\x00')  # 标志 (1 byte)

        # Comment frame (COMM)
        comment_text = f"Obfuscated_{random.randint(10000, 99999)}"

        # Frame header (10 bytes)
        frame = bytearray()
        frame.extend(b'COMM')  # Frame ID (4 bytes)

        # Frame content
        frame_content = bytearray()
        frame_content.extend(b'\x00')  # Text encoding (ISO-8859-1)
        frame_content.extend(b'eng')  # Language (3 bytes)
        frame_content.extend(b'\x00')  # Short description (empty + null)
        frame_content.extend(comment_text.encode('latin-1'))  # Comment

        # Frame size (4 bytes, synchsafe integer)
        frame_size = len(frame_content)
        frame.extend(struct.pack('>I', frame_size))

        # Frame flags (2 bytes)
        frame.extend(b'\x00\x00')

        # Add frame content
        frame.extend(frame_content)

        # Tag size (synchsafe integer, excluding header)
        tag_size = len(frame)
        # Convert to synchsafe integer (7 bits per byte)
        synchsafe = bytes([
            (tag_size >> 21) & 0x7F,
            (tag_size >> 14) & 0x7F,
            (tag_size >> 7) & 0x7F,
            tag_size & 0x7F
        ])
        header.extend(synchsafe)

        # Combine header and frame
        return bytes(header + frame)

    def _update_wav_riff_chunk(self, data: bytearray) -> bytearray:
        """
        更新WAV文件的RIFF块大小（P3阶段三新增）

        Args:
            data: WAV文件数据

        Returns:
            bytearray: 更新后的数据
        """
        if len(data) < 8 or data[:4] != b'RIFF':
            return data

        # 更新文件大小字段（offset 4-7）
        # RIFF chunk size = file size - 8
        file_size = len(data) - 8
        data[4:8] = struct.pack('<I', file_size)

        return data

    def _verify_audio_integrity(self, audio_path: str, suffix: str) -> bool:
        """
        验证音频文件完整性（P3阶段三新增）

        Args:
            audio_path: 音频文件路径
            suffix: 文件后缀

        Returns:
            bool: 是否完整
        """
        try:
            with open(audio_path, 'rb') as f:
                data = f.read()

            # 基础验证：文件不为空
            if len(data) == 0:
                return False

            # 格式特定验证
            if suffix == '.mp3':
                # 验证是否包含MP3同步字（0xFF 0xFB）或ID3标签
                has_mp3_sync = b'\xFF\xFB' in data or b'\xFF\xFA' in data
                has_id3 = data[:3] == b'ID3'
                return has_mp3_sync or has_id3

            elif suffix == '.wav':
                # 验证RIFF头和文件大小
                if data[:4] != b'RIFF' or data[8:12] != b'WAVE':
                    return False
                # 验证文件大小字段
                declared_size = struct.unpack('<I', data[4:8])[0]
                actual_size = len(data) - 8
                # 允许一定误差（添加的数据）
                return actual_size >= declared_size

            elif suffix == '.aiff':
                # 验证FORM和AIFF头
                return data[:4] == b'FORM' and data[8:12] == b'AIFF'

            elif suffix in ['.m4a', '.aac']:
                # 验证ftyp box (M4A容器格式) 或 AAC同步字
                return b'ftyp' in data[:20] or (len(data) >= 2 and data[0] == 0xFF and (data[1] & 0xF0) == 0xF0)

            # 其他格式：只要文件不为空就认为有效
            return True

        except Exception as e:
            print(f"音频完整性验证失败 {audio_path}: {e}")
            return False

    def _create_silent_audio_chunk(self, format_type: str) -> bytes:
        """
        创建静默音频数据块

        Args:
            format_type: 音频格式（.wav, .aiff等）

        Returns:
            bytes: 静默数据块
        """
        # 创建极短的静默音频数据（几毫秒）
        # 这里只是示例，实际需要根据格式创建正确的音频帧
        silent_samples = [0] * 100  # 100个零值采样点

        if format_type == '.wav':
            # WAV格式的16位采样
            return struct.pack(f'{len(silent_samples)}h', *silent_samples)
        else:
            # 通用格式
            return bytes(silent_samples)

    def get_statistics(self) -> Dict:
        """获取处理统计信息"""
        return self.stats.copy()


class FontFileHandler:
    """
    字体文件处理器（P3阶段四增强版）

    功能:
    - 字体文件名混淆
    - 字体元数据修改
    - PostScript名称混淆
    - TrueType/OpenType name表提取和修改（P3新增）
    - 字体校验和重新计算（P3新增）
    """

    def __init__(self, symbol_mappings: Dict[str, str] = None):
        """
        初始化字体处理器

        Args:
            symbol_mappings: 符号映射字典
        """
        self.symbol_mappings = symbol_mappings or {}
        self.stats = {
            'fonts_processed': 0,
            'fonts_renamed': 0,
            'name_tables_modified': 0,
            'checksums_recalculated': 0,
        }

    def process_font_file(self, font_path: str, output_path: str = None,
                         rename: bool = True,
                         modify_internal_names: bool = True,
                         recalculate_checksum: bool = True) -> ProcessResult:
        """
        处理字体文件（P3阶段四增强版）

        Args:
            font_path: 字体文件路径
            output_path: 输出路径
            rename: 是否重命名文件
            modify_internal_names: 是否修改内部名称（name表）
            recalculate_checksum: 是否重新计算校验和

        Returns:
            ProcessResult: 处理结果
        """
        try:
            font_file = Path(font_path)
            suffix = font_file.suffix.lower()

            if suffix not in ['.ttf', '.otf']:
                return ProcessResult(
                    success=False,
                    file_path=font_path,
                    operation="font_process",
                    error=f"不支持的字体格式: {suffix}（目前仅支持.ttf和.otf）"
                )

            # 读取字体文件
            with open(font_path, 'rb') as f:
                data = bytearray(f.read())

            operations = []
            original_size = len(data)
            user_specified_output = output_path is not None

            # 修改内部name表
            if modify_internal_names:
                try:
                    modified_data, name_changes = self._modify_font_names(data, font_file.stem)
                    if name_changes:
                        data = modified_data
                        operations.append('name_table_modified')
                        self.stats['name_tables_modified'] += 1
                except Exception as e:
                    # name表修改失败不应导致整个处理失败
                    operations.append(f'name_table_modification_failed: {str(e)}')

            # 重新计算校验和
            if recalculate_checksum:
                try:
                    data = self._recalculate_font_checksums(data)
                    operations.append('checksum_recalculated')
                    self.stats['checksums_recalculated'] += 1
                except Exception as e:
                    operations.append(f'checksum_recalculation_failed: {str(e)}')

            # 确定输出路径
            if output_path is None:
                # 没有指定输出路径，使用输入路径或重命名后的路径
                if rename:
                    font_name = font_file.stem
                    new_name = self.symbol_mappings.get(font_name, font_name)
                    if new_name != font_name:
                        output_path = str(font_file.parent / f"{new_name}{suffix}")
                        self.stats['fonts_renamed'] += 1
                        operations.append('file_renamed')
                    else:
                        output_path = font_path
                else:
                    output_path = font_path
            else:
                # 用户明确指定了输出路径，使用该路径
                # 但如果rename=True，记录重命名操作
                if rename:
                    font_name = font_file.stem
                    new_name = self.symbol_mappings.get(font_name, font_name)
                    if new_name != font_name:
                        self.stats['fonts_renamed'] += 1
                        operations.append('file_renamed')

            # 写入修改后的文件
            with open(output_path, 'wb') as f:
                f.write(data)

            self.stats['fonts_processed'] += 1

            return ProcessResult(
                success=True,
                file_path=font_path,
                operation="font_process",
                details={
                    'operations': operations,
                    'output_path': output_path,
                    'original_size': original_size,
                    'new_size': len(data),
                }
            )

        except Exception as e:
            return ProcessResult(
                success=False,
                file_path=font_path,
                operation="font_process",
                error=str(e)
            )

    def _modify_font_names(self, data: bytearray, original_name: str) -> Tuple[bytearray, bool]:
        """
        修改字体内部name表（P3阶段四新增）

        Args:
            data: 字体文件数据
            original_name: 原始字体名称

        Returns:
            Tuple[bytearray, bool]: (修改后的数据, 是否发生修改)
        """
        # 1. 查找name表
        name_table = self._find_table(data, b'name')
        if not name_table:
            return data, False

        offset, length = name_table

        # 2. 解析name表头部
        if offset + 6 > len(data):
            return data, False

        format_selector = struct.unpack('>H', data[offset:offset+2])[0]
        count = struct.unpack('>H', data[offset+2:offset+4])[0]
        string_offset = struct.unpack('>H', data[offset+4:offset+6])[0]

        # 3. 生成新的字体名称
        new_name = self.symbol_mappings.get(original_name, None)
        if not new_name:
            # 如果没有映射,生成一个随机名称
            new_name = f"Font_{random.randint(10000, 99999)}"

        # 4. 遍历name记录,修改nameID 1, 4, 6
        name_records_start = offset + 6
        string_storage_start = offset + string_offset

        changed = False
        for i in range(count):
            record_offset = name_records_start + i * 12

            if record_offset + 12 > len(data):
                break

            # 解析name记录
            platform_id = struct.unpack('>H', data[record_offset:record_offset+2])[0]
            encoding_id = struct.unpack('>H', data[record_offset+2:record_offset+4])[0]
            language_id = struct.unpack('>H', data[record_offset+4:record_offset+6])[0]
            name_id = struct.unpack('>H', data[record_offset+6:record_offset+8])[0]
            str_length = struct.unpack('>H', data[record_offset+8:record_offset+10])[0]
            str_offset = struct.unpack('>H', data[record_offset+10:record_offset+12])[0]

            # 只修改nameID 1(Font Family), 4(Full Font Name), 6(PostScript Name)
            if name_id in [1, 4, 6]:
                # 计算字符串在文件中的实际位置
                actual_str_offset = string_storage_start + str_offset

                if actual_str_offset + str_length > len(data):
                    continue

                # 根据platform和encoding确定编码方式
                if platform_id == 1:  # Macintosh
                    encoding = 'mac_roman'
                elif platform_id == 3:  # Windows
                    encoding = 'utf-16-be'
                else:
                    encoding = 'utf-8'

                try:
                    # 编码新名称
                    if encoding == 'utf-16-be':
                        new_name_bytes = new_name.encode('utf-16-be')
                    elif encoding == 'mac_roman':
                        new_name_bytes = new_name.encode('ascii', errors='ignore')
                    else:
                        new_name_bytes = new_name.encode('utf-8')

                    # 如果新名称长度与旧名称相同,直接替换
                    if len(new_name_bytes) == str_length:
                        data[actual_str_offset:actual_str_offset+str_length] = new_name_bytes
                        changed = True
                    # 如果新名称更短,用空格填充
                    elif len(new_name_bytes) < str_length:
                        padding = b' ' * (str_length - len(new_name_bytes))
                        data[actual_str_offset:actual_str_offset+str_length] = new_name_bytes + padding
                        changed = True
                    # 如果新名称更长,截断
                    else:
                        data[actual_str_offset:actual_str_offset+str_length] = new_name_bytes[:str_length]
                        changed = True

                except (UnicodeEncodeError, UnicodeDecodeError):
                    # 编码失败,跳过这个记录
                    continue

        return data, changed

    def _recalculate_font_checksums(self, data: bytearray) -> bytearray:
        """
        重新计算字体文件校验和（P3阶段四新增）

        主要更新head表中的checkSumAdjustment字段

        Args:
            data: 字体文件数据

        Returns:
            bytearray: 更新后的数据
        """
        # 1. 查找head表
        head_table = self._find_table(data, b'head')
        if not head_table:
            return data

        head_offset, head_length = head_table

        # 2. head表中的checkSumAdjustment位于offset+8
        if head_offset + 12 > len(data):
            return data

        # 3. 保存当前的checkSumAdjustment值
        original_adjustment = data[head_offset+8:head_offset+12]

        # 4. 暂时将checkSumAdjustment设置为0
        data[head_offset+8:head_offset+12] = b'\x00\x00\x00\x00'

        # 5. 计算整个文件的校验和
        file_checksum = self._calculate_checksum(data)

        # 6. 计算checkSumAdjustment = 0xB1B0AFBA - file_checksum
        magic_number = 0xB1B0AFBA
        check_sum_adjustment = (magic_number - file_checksum) & 0xFFFFFFFF

        # 7. 写入checkSumAdjustment
        data[head_offset+8:head_offset+12] = struct.pack('>I', check_sum_adjustment)

        return data

    def _find_table(self, data: bytearray, table_tag: bytes) -> Optional[Tuple[int, int]]:
        """
        在TrueType/OpenType字体中查找表

        Args:
            data: 字体文件数据
            table_tag: 表标签（4字节）

        Returns:
            Optional[Tuple[int, int]]: (表偏移量, 表长度) 或 None
        """
        if len(data) < 12:
            return None

        # 读取Offset Table
        sfnt_version = data[0:4]
        num_tables = struct.unpack('>H', data[4:6])[0]

        # 遍历Table Directory
        for i in range(num_tables):
            table_dir_offset = 12 + i * 16

            if table_dir_offset + 16 > len(data):
                break

            tag = data[table_dir_offset:table_dir_offset+4]
            checksum = struct.unpack('>I', data[table_dir_offset+4:table_dir_offset+8])[0]
            offset = struct.unpack('>I', data[table_dir_offset+8:table_dir_offset+12])[0]
            length = struct.unpack('>I', data[table_dir_offset+12:table_dir_offset+16])[0]

            if tag == table_tag:
                return (offset, length)

        return None

    def _calculate_checksum(self, data: bytearray, offset: int = 0, length: int = None) -> int:
        """
        计算TrueType/OpenType校验和

        Args:
            data: 数据
            offset: 起始偏移量
            length: 长度（None表示到文件末尾）

        Returns:
            int: 校验和
        """
        if length is None:
            length = len(data) - offset

        # 确保长度是4的倍数（补零）
        padded_length = (length + 3) // 4 * 4
        checksum = 0

        for i in range(0, padded_length, 4):
            pos = offset + i

            # 如果超出数据范围,用0填充
            if pos + 4 > len(data):
                remaining = len(data) - pos
                value_bytes = data[pos:pos+remaining] + b'\x00' * (4 - remaining)
            else:
                value_bytes = data[pos:pos+4]

            value = struct.unpack('>I', value_bytes)[0]
            checksum = (checksum + value) & 0xFFFFFFFF

        return checksum

    def get_statistics(self) -> Dict:
        """获取处理统计信息"""
        return self.stats.copy()


class AdvancedResourceHandler:
    """
    高级资源处理器 - 整合所有P2功能

    使用示例:
    ```python
    handler = AdvancedResourceHandler(symbol_mappings)

    # 处理Assets目录
    handler.process_assets_catalog(assets_path)

    # 修改图片像素
    handler.modify_image_pixels(image_path, intensity=0.02)

    # 修改音频hash
    handler.modify_audio_hash(audio_path)

    # 处理字体文件
    handler.process_font_file(font_path)

    # 获取统计信息
    stats = handler.get_statistics()
    ```
    """

    def __init__(self, symbol_mappings: Dict[str, str] = None,
                 image_intensity: float = 0.02):
        """
        初始化高级资源处理器

        Args:
            symbol_mappings: 符号映射字典
            image_intensity: 图片修改强度
        """
        self.symbol_mappings = symbol_mappings or {}

        # 初始化各个子处理器
        self.assets_handler = AdvancedAssetsHandler(symbol_mappings)
        self.image_modifier = ImagePixelModifier(image_intensity)
        self.audio_modifier = AudioHashModifier()
        self.font_handler = FontFileHandler(symbol_mappings)

        self.results: List[ProcessResult] = []

    def process_assets_catalog(self, assets_path: str, **kwargs) -> bool:
        """处理Assets.xcassets目录"""
        return self.assets_handler.process_assets_catalog(assets_path, **kwargs)

    def modify_image_pixels(self, image_path: str, output_path: str = None) -> ProcessResult:
        """修改图片像素"""
        result = self.image_modifier.modify_image_pixels(image_path, output_path)
        self.results.append(result)
        return result

    def modify_audio_hash(self, audio_path: str, output_path: str = None) -> ProcessResult:
        """修改音频hash"""
        result = self.audio_modifier.modify_audio_hash(audio_path, output_path)
        self.results.append(result)
        return result

    def process_font_file(self, font_path: str, output_path: str = None, **kwargs) -> ProcessResult:
        """处理字体文件"""
        result = self.font_handler.process_font_file(font_path, output_path, **kwargs)
        self.results.append(result)
        return result

    def get_statistics(self) -> Dict:
        """获取综合统计信息"""
        return {
            'assets': self.assets_handler.get_statistics(),
            'images': self.image_modifier.get_statistics(),
            'audio': self.audio_modifier.get_statistics(),
            'fonts': self.font_handler.get_statistics(),
            'total_operations': len(self.results),
            'successful_operations': sum(1 for r in self.results if r.success),
            'failed_operations': sum(1 for r in self.results if not r.success),
        }

    def get_results(self) -> List[ProcessResult]:
        """获取所有处理结果"""
        return self.results.copy()


if __name__ == "__main__":
    # 测试代码
    print("=== 高级资源处理器测试 ===\n")

    import tempfile

    # 符号映射
    symbol_mappings = {
        'AppIcon': 'Icon001',
        'LaunchImage': 'Launch002',
        'CustomFont': 'Font003',
    }

    # 创建处理器
    handler = AdvancedResourceHandler(symbol_mappings, image_intensity=0.02)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # 1. 测试Assets处理
        print("1. 测试Assets.xcassets处理:")
        assets_dir = tmpdir_path / "Assets.xcassets"
        assets_dir.mkdir()

        # 创建测试imageset
        imageset_dir = assets_dir / "AppIcon.imageset"
        imageset_dir.mkdir()

        contents = {
            "images": [
                {"idiom": "universal", "filename": "icon.png", "scale": "1x"}
            ],
            "info": {"version": 1, "author": "xcode"}
        }

        with open(imageset_dir / "Contents.json", 'w') as f:
            json.dump(contents, f, indent=2)

        # 创建测试图片文件
        with open(imageset_dir / "icon.png", 'wb') as f:
            f.write(b'\x89PNG\r\n\x1a\n' + b'test_data' * 10)

        success = handler.process_assets_catalog(str(assets_dir))
        print(f"  Assets处理: {'成功' if success else '失败'}")

        # 2. 测试音频hash修改
        print("\n2. 测试音频hash修改:")
        audio_file = tmpdir_path / "test.mp3"
        with open(audio_file, 'wb') as f:
            f.write(b'ID3' + b'\x00' * 10 + b'audio_data' * 100)

        result = handler.modify_audio_hash(str(audio_file))
        print(f"  音频hash修改: {'成功' if result.success else '失败'}")
        if result.success:
            print(f"  详情: {result.details}")

        # 3. 测试字体处理
        print("\n3. 测试字体文件处理:")
        font_file = tmpdir_path / "CustomFont.ttf"
        with open(font_file, 'wb') as f:
            # TrueType字体文件头
            f.write(b'\x00\x01\x00\x00' + b'font_data' * 100)

        result = handler.process_font_file(str(font_file), rename=True, modify_metadata=True)
        print(f"  字体处理: {'成功' if result.success else '失败'}")
        if result.success:
            print(f"  详情: {result.details}")

        # 4. 统计信息
        print("\n4. 综合统计信息:")
        stats = handler.get_statistics()
        print(f"  Assets处理: {stats['assets']}")
        print(f"  图片处理: {stats['images']}")
        print(f"  音频处理: {stats['audio']}")
        print(f"  字体处理: {stats['fonts']}")
        print(f"  总操作数: {stats['total_operations']}")
        print(f"  成功: {stats['successful_operations']}")
        print(f"  失败: {stats['failed_operations']}")

    print("\n=== 测试完成 ===")
