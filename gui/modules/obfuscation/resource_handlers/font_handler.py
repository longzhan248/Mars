"""
字体文件处理器

功能:
- 字体文件名混淆
- 字体元数据修改
- PostScript名称混淆
- TrueType/OpenType name表提取和修改
- 字体校验和重新计算

作者: Claude Code
日期: 2025-10-14
版本: v2.3.0 (P3阶段四增强版)
"""

import random
import struct
from pathlib import Path
from typing import Dict, Optional, Tuple

from .common import ProcessResult


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
