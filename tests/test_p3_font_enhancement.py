"""
测试P3阶段四：字体文件处理增强

测试内容:
1. TrueType/OpenType字体name表提取和修改
2. 字体校验和重新计算
3. 字体文件完整性验证
4. 完整处理流程

作者: Claude Code
日期: 2025-10-14
"""

import unittest
import tempfile
import struct
from pathlib import Path
import sys
import os

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from gui.modules.obfuscation.advanced_resource_handler import FontFileHandler


class TestFontNameTableModification(unittest.TestCase):
    """测试字体name表修改"""

    def setUp(self):
        """设置测试环境"""
        self.handler = FontFileHandler(
            symbol_mappings={'TestFont': 'ModifiedFont'}
        )
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """清理测试环境"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_minimal_ttf(self, font_name: str = "TestFont") -> bytes:
        """
        创建一个最小化的TrueType字体文件（仅包含必要的表）

        Args:
            font_name: 字体名称

        Returns:
            bytes: 字体文件数据
        """
        data = bytearray()

        # 1. Offset Table (12 bytes)
        data.extend(b'\x00\x01\x00\x00')  # sfntVersion (TrueType)
        num_tables = 2  # head + name 表
        data.extend(struct.pack('>H', num_tables))  # numTables
        data.extend(b'\x00\x10')  # searchRange
        data.extend(b'\x00\x01')  # entrySelector
        data.extend(b'\x00\x00')  # rangeShift

        # 2. Table Directory (16 bytes per table)
        # 字符串数据（UTF-16BE编码）- 提前计算因为需要确定name表大小
        font_name_utf16 = font_name.encode('utf-16-be')

        # 2.1 head表
        head_offset = 12 + num_tables * 16  # Offset Table (12) + Table Directory (2*16)
        head_length = 62  # Correct size: not 54!
        data.extend(b'head')  # tag
        data.extend(struct.pack('>I', 0))  # checkSum (临时)
        data.extend(struct.pack('>I', head_offset))  # offset
        data.extend(struct.pack('>I', head_length))  # length

        # 2.2 name表
        name_offset = head_offset + head_length
        # name表结构: header(6) + name_records(2*12) + string_storage
        name_records_count = 2
        name_header_size = 6
        name_records_size = name_records_count * 12  # 24
        string_storage_size = len(font_name_utf16) * 2  # nameID 1 和 4 各一份

        # stringOffset is relative to the start of name table
        stringOffset_value = name_header_size + name_records_size  # 6 + 24 = 30
        name_length = stringOffset_value + string_storage_size  # 30 + (字体名*2)

        data.extend(b'name')  # tag
        data.extend(struct.pack('>I', 0))  # checkSum (临时)
        data.extend(struct.pack('>I', name_offset))  # offset
        data.extend(struct.pack('>I', name_length))  # length

        # 3. head表数据 (54 bytes)
        head_data = bytearray()
        head_data.extend(b'\x00\x01\x00\x00')  # version
        head_data.extend(b'\x00\x01\x00\x00')  # fontRevision
        head_data.extend(b'\x00\x00\x00\x00')  # checkSumAdjustment (待计算)
        head_data.extend(b'\x5F\x0F\x3C\xF5')  # magicNumber
        head_data.extend(b'\x00\x00')  # flags
        head_data.extend(b'\x04\x00')  # unitsPerEm = 1024
        head_data.extend(b'\x00' * 16)  # created + modified
        head_data.extend(b'\x00' * 16)  # bounding box
        head_data.extend(b'\x00\x00')  # macStyle
        head_data.extend(b'\x00\x08')  # lowestRecPPEM
        head_data.extend(b'\x00\x02')  # fontDirectionHint
        head_data.extend(b'\x00\x00')  # indexToLocFormat
        head_data.extend(b'\x00\x00')  # glyphDataFormat
        data.extend(head_data)

        # 4. name表数据
        name_data = bytearray()

        # name表头部 (6 bytes)
        name_data.extend(struct.pack('>H', 0))  # format
        name_data.extend(struct.pack('>H', name_records_count))  # count
        name_data.extend(struct.pack('>H', stringOffset_value))  # stringOffset

        # name记录1: nameID=1 (Font Family)
        name_data.extend(struct.pack('>H', 3))  # platformID (Windows)
        name_data.extend(struct.pack('>H', 1))  # encodingID (Unicode)
        name_data.extend(struct.pack('>H', 0x0409))  # languageID (en-US)
        name_data.extend(struct.pack('>H', 1))  # nameID (Font Family)
        name_data.extend(struct.pack('>H', len(font_name_utf16)))  # length
        name_data.extend(struct.pack('>H', 0))  # offset (relative to stringOffset)

        # name记录2: nameID=4 (Full Font Name)
        name_data.extend(struct.pack('>H', 3))  # platformID
        name_data.extend(struct.pack('>H', 1))  # encodingID
        name_data.extend(struct.pack('>H', 0x0409))  # languageID
        name_data.extend(struct.pack('>H', 4))  # nameID (Full Font Name)
        name_data.extend(struct.pack('>H', len(font_name_utf16)))  # length
        name_data.extend(struct.pack('>H', len(font_name_utf16)))  # offset (after first string)

        # 字符串存储
        name_data.extend(font_name_utf16)  # nameID 1
        name_data.extend(font_name_utf16)  # nameID 4

        data.extend(name_data)

        return bytes(data)

    def test_find_name_table(self):
        """测试查找name表"""
        font_data = self._create_minimal_ttf()
        result = self.handler._find_table(bytearray(font_data), b'name')

        self.assertIsNotNone(result, "应该找到name表")
        offset, length = result
        self.assertGreater(offset, 0, "name表偏移量应大于0")
        self.assertGreater(length, 0, "name表长度应大于0")

    def test_find_head_table(self):
        """测试查找head表"""
        font_data = self._create_minimal_ttf()
        result = self.handler._find_table(bytearray(font_data), b'head')

        self.assertIsNotNone(result, "应该找到head表")
        offset, length = result
        self.assertEqual(length, 62, "head表长度应为62字节")

    def test_modify_font_names(self):
        """测试修改字体名称"""
        font_data = bytearray(self._create_minimal_ttf("TestFont"))

        # 修改字体名称
        modified_data, changed = self.handler._modify_font_names(font_data, "TestFont")

        self.assertTrue(changed, "应该发生修改")
        self.assertIsInstance(modified_data, bytearray, "返回的应该是bytearray")

        # 验证新名称存在于修改后的数据中
        # 注意: "ModifiedFont"(24字节)比"TestFont"(16字节)长，会被截断为"Modified"(16字节)
        new_name = "ModifiedFont"
        truncated_name = "Modified"  # 截断后的名称
        truncated_name_utf16 = truncated_name.encode('utf-16-be')
        self.assertIn(truncated_name_utf16, bytes(modified_data), "修改后的数据应包含新字体名称（截断版）")


class TestFontChecksumRecalculation(unittest.TestCase):
    """测试字体校验和重新计算"""

    def setUp(self):
        """设置测试环境"""
        self.handler = FontFileHandler()

    def test_calculate_checksum_basic(self):
        """测试基础校验和计算"""
        # 简单的4字节数据
        data = bytearray(b'\x00\x01\x00\x00')
        checksum = self.handler._calculate_checksum(data)

        self.assertIsInstance(checksum, int, "校验和应该是整数")
        self.assertEqual(checksum, 0x00010000, "校验和计算应该正确")

    def test_calculate_checksum_padding(self):
        """测试带填充的校验和计算"""
        # 非4字节对齐的数据（需要自动填充）
        data = bytearray(b'\x00\x01\x00')  # 3 bytes
        checksum = self.handler._calculate_checksum(data)

        self.assertIsInstance(checksum, int)
        # 填充后应为 \x00\x01\x00\x00
        self.assertEqual(checksum, 0x00010000)

    def test_recalculate_checksums(self):
        """测试重新计算校验和"""
        # 创建简单的字体数据
        font_data = bytearray()

        # Offset Table
        font_data.extend(b'\x00\x01\x00\x00')  # sfntVersion
        font_data.extend(struct.pack('>H', 1))  # numTables
        font_data.extend(b'\x00\x10\x00\x01\x00\x00')  # searchRange等

        # head表目录项
        head_offset = 12 + 16
        head_length = 54
        font_data.extend(b'head')  # tag
        font_data.extend(struct.pack('>I', 0))  # checkSum
        font_data.extend(struct.pack('>I', head_offset))  # offset
        font_data.extend(struct.pack('>I', head_length))  # length

        # head表数据 (54 bytes)
        head_data = bytearray(b'\x00' * 54)
        # 在offset+8位置设置checkSumAdjustment为非0（应被重新计算）
        head_data[8:12] = b'\xFF\xFF\xFF\xFF'
        font_data.extend(head_data)

        # 重新计算校验和
        result = self.handler._recalculate_font_checksums(font_data)

        # 验证checkSumAdjustment被修改了
        actual_adjustment = struct.unpack('>I', result[head_offset+8:head_offset+12])[0]
        self.assertNotEqual(actual_adjustment, 0xFFFFFFFF, "checkSumAdjustment应该被重新计算")

        # 验证魔数公式：整个文件校验和应该等于0xB1B0AFBA
        # （当checkSumAdjustment正确时）
        file_checksum = self.handler._calculate_checksum(result)
        self.assertEqual(file_checksum, 0xB1B0AFBA, "整个文件校验和应该等于魔数")


class TestFontProcessingIntegration(unittest.TestCase):
    """测试字体处理完整流程"""

    def setUp(self):
        """设置测试环境"""
        self.handler = FontFileHandler(
            symbol_mappings={'MyFont': 'ObfuscatedFont'}
        )
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """清理测试环境"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_test_ttf_file(self, filename: str, font_name: str) -> Path:
        """创建测试用的TTF文件"""
        font_path = Path(self.temp_dir) / filename

        # 创建最小化的TrueType字体
        font_data = bytearray()

        # Offset Table
        font_data.extend(b'\x00\x01\x00\x00')  # sfntVersion
        font_data.extend(struct.pack('>H', 2))  # numTables (head + name)
        font_data.extend(b'\x00\x20\x00\x01\x00\x00')

        # head表目录
        head_offset = 12 + 32  # offset table + 2 table entries
        head_length = 54
        font_data.extend(b'head')
        font_data.extend(struct.pack('>I', 0))  # checkSum
        font_data.extend(struct.pack('>I', head_offset))
        font_data.extend(struct.pack('>I', head_length))

        # name表目录
        name_offset = head_offset + head_length
        font_name_utf16 = font_name.encode('utf-16-be')
        name_length = 6 + 12 + len(font_name_utf16)  # header + 1 record + string
        font_data.extend(b'name')
        font_data.extend(struct.pack('>I', 0))  # checkSum
        font_data.extend(struct.pack('>I', name_offset))
        font_data.extend(struct.pack('>I', name_length))

        # head表数据
        head_data = bytearray(b'\x00' * 54)
        head_data[0:4] = b'\x00\x01\x00\x00'  # version
        head_data[12:16] = b'\x5F\x0F\x3C\xF5'  # magicNumber
        font_data.extend(head_data)

        # name表数据
        font_data.extend(struct.pack('>H', 0))  # format
        font_data.extend(struct.pack('>H', 1))  # count
        font_data.extend(struct.pack('>H', 18))  # stringOffset (6 + 12)

        # name记录 (nameID=1, Font Family)
        font_data.extend(struct.pack('>H', 3))  # platformID
        font_data.extend(struct.pack('>H', 1))  # encodingID
        font_data.extend(struct.pack('>H', 0x0409))  # languageID
        font_data.extend(struct.pack('>H', 1))  # nameID
        font_data.extend(struct.pack('>H', len(font_name_utf16)))  # length
        font_data.extend(struct.pack('>H', 0))  # offset

        # 字符串存储
        font_data.extend(font_name_utf16)

        # 写入文件
        with open(font_path, 'wb') as f:
            f.write(font_data)

        return font_path

    def test_process_ttf_file_complete(self):
        """测试完整的TTF文件处理流程"""
        # 创建测试字体文件
        font_file = self._create_test_ttf_file("MyFont.ttf", "MyFont")

        # 处理字体文件
        output_file = Path(self.temp_dir) / "output.ttf"
        result = self.handler.process_font_file(
            str(font_file),
            str(output_file),
            rename=True,
            modify_internal_names=True,
            recalculate_checksum=True
        )

        # 验证处理结果
        self.assertTrue(result.success, f"处理应该成功: {result.error}")
        self.assertEqual(result.operation, "font_process")

        # 验证操作列表
        operations = result.details['operations']
        self.assertIn('name_table_modified', operations, "应该修改了name表")
        self.assertIn('checksum_recalculated', operations, "应该重新计算了校验和")

        # 验证输出文件存在
        self.assertTrue(output_file.exists(), "输出文件应该存在")

        # 验证文件大小合理
        self.assertGreater(result.details['new_size'], 0, "文件大小应大于0")

    def test_process_otf_file(self):
        """测试OTF文件处理"""
        font_file = self._create_test_ttf_file("MyFont.otf", "MyFont")

        result = self.handler.process_font_file(str(font_file))

        self.assertTrue(result.success, "OTF文件应该能正常处理")

    def test_process_unsupported_format(self):
        """测试不支持的字体格式"""
        # 创建一个.woff文件（不支持）
        woff_file = Path(self.temp_dir) / "test.woff"
        woff_file.write_bytes(b'woff_data')

        result = self.handler.process_font_file(str(woff_file))

        self.assertFalse(result.success, "不支持的格式应该处理失败")
        self.assertIn("不支持", result.error, "错误信息应该提示不支持")

    def test_file_rename_only(self):
        """测试仅重命名文件"""
        font_file = self._create_test_ttf_file("MyFont.ttf", "MyFont")

        result = self.handler.process_font_file(
            str(font_file),
            rename=True,
            modify_internal_names=False,
            recalculate_checksum=False
        )

        self.assertTrue(result.success)

        # 验证输出路径包含新名称
        output_path = result.details['output_path']
        self.assertIn('ObfuscatedFont', output_path, "输出路径应包含新名称")

    def test_statistics(self):
        """测试统计信息"""
        font_file = self._create_test_ttf_file("MyFont.ttf", "MyFont")

        # 处理多个字体文件
        for i in range(3):
            test_file = self._create_test_ttf_file(f"Font{i}.ttf", f"Font{i}")
            self.handler.process_font_file(str(test_file))

        stats = self.handler.get_statistics()

        self.assertEqual(stats['fonts_processed'], 3, "应该处理了3个字体")
        self.assertGreater(stats['name_tables_modified'], 0, "应该修改了name表")
        self.assertGreater(stats['checksums_recalculated'], 0, "应该重新计算了校验和")


class TestEdgeCases(unittest.TestCase):
    """测试边界情况"""

    def setUp(self):
        """设置测试环境"""
        self.handler = FontFileHandler()

    def test_empty_font_data(self):
        """测试空字体数据"""
        empty_data = bytearray()

        result = self.handler._find_table(empty_data, b'name')
        self.assertIsNone(result, "空数据应该返回None")

    def test_corrupted_font_data(self):
        """测试损坏的字体数据"""
        # 创建不完整的字体数据（缺少表目录）
        corrupted_data = bytearray(b'\x00\x01\x00\x00' + b'\x00\x05')  # 声称有5个表但没有实际数据

        result = self.handler._find_table(corrupted_data, b'name')
        self.assertIsNone(result, "损坏的数据应该返回None")

    def test_font_without_name_table(self):
        """测试没有name表的字体"""
        # 创建只有head表的字体
        font_data = bytearray()
        font_data.extend(b'\x00\x01\x00\x00')  # sfntVersion
        font_data.extend(struct.pack('>H', 1))  # numTables
        font_data.extend(b'\x00\x10\x00\x01\x00\x00')

        # head表目录
        font_data.extend(b'head')
        font_data.extend(struct.pack('>I', 0))
        font_data.extend(struct.pack('>I', 28))
        font_data.extend(struct.pack('>I', 54))

        # head表数据
        font_data.extend(b'\x00' * 54)

        # 尝试修改name表（应该失败但不抛出异常）
        modified_data, changed = self.handler._modify_font_names(font_data, "Test")
        self.assertFalse(changed, "没有name表时不应该修改")


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加所有测试类
    suite.addTests(loader.loadTestsFromTestCase(TestFontNameTableModification))
    suite.addTests(loader.loadTestsFromTestCase(TestFontChecksumRecalculation))
    suite.addTests(loader.loadTestsFromTestCase(TestFontProcessingIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 返回是否全部通过
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
