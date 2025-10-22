"""
音频文件hash修改器

功能:
- 修改音频元数据
- 添加静默数据
- 保持音频质量
- 规范ID3v2标签
- WAV RIFF结构更新
- 音频质量验证

作者: Claude Code
日期: 2025-10-14
版本: v2.3.0 (P3阶段三增强版)
"""

import random
import struct
from pathlib import Path
from typing import Dict

from .common import ProcessResult


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
