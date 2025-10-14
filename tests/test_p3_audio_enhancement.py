"""
P3阶段三测试 - 音频hash修改增强
测试ID3v2标签、WAV RIFF结构更新和音频完整性验证

作者: Claude Code
日期: 2025-10-14
版本: v1.0.0
"""

import unittest
import tempfile
import os
from pathlib import Path

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from gui.modules.obfuscation.advanced_resource_handler import AudioHashModifier


class TestP3AudioEnhancement(unittest.TestCase):
    """P3阶段三 - 音频hash修改增强测试"""

    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.modifier = AudioHashModifier()

    def tearDown(self):
        """测试后清理"""
        import shutil
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    # ==================== ID3v2标签测试 ====================

    def test_id3v2_tag_structure(self):
        """测试ID3v2标签结构"""
        print("\n=== 测试ID3v2标签结构 ===")

        tag = self.modifier._create_id3v2_tag()

        # 验证标签不为空
        self.assertGreater(len(tag), 0, "ID3v2标签不应为空")

        # 验证标签头部（前10字节）
        self.assertEqual(tag[0:3], b'ID3', "应以'ID3'开头")
        self.assertEqual(tag[3], 3, "主版本号应为3")
        self.assertEqual(tag[4], 0, "次版本号应为0")
        self.assertEqual(tag[5], 0, "标志位应为0")

        # 验证synchsafe整数（字节6-9）
        size_bytes = tag[6:10]
        self.assertTrue(all(b < 128 for b in size_bytes), "大小字节应使用synchsafe整数")

        # 验证COMM帧存在
        self.assertIn(b'COMM', tag, "应包含COMM帧")

        print(f"  标签大小: {len(tag)} 字节")
        print(f"  标签头部: {tag[0:10].hex()}")
        print(f"✅ ID3v2标签结构测试通过")

    def test_id3v2_tag_synchsafe_encoding(self):
        """测试synchsafe整数编码"""
        print("\n=== 测试synchsafe整数编码 ===")

        tag = self.modifier._create_id3v2_tag()

        # 提取synchsafe整数
        size_bytes = tag[6:10]
        synchsafe_size = (
            (size_bytes[0] << 21) |
            (size_bytes[1] << 14) |
            (size_bytes[2] << 7) |
            size_bytes[3]
        )

        # 实际内容大小应为总大小减去头部10字节
        actual_size = len(tag) - 10

        self.assertEqual(synchsafe_size, actual_size, "synchsafe编码应匹配实际大小")

        print(f"  Synchsafe大小: {synchsafe_size} 字节")
        print(f"  实际大小: {actual_size} 字节")
        print(f"✅ Synchsafe整数编码测试通过")

    def test_mp3_id3_tag_addition(self):
        """测试MP3文件添加ID3标签"""
        print("\n=== 测试MP3文件添加ID3标签 ===")

        # 创建模拟MP3文件（以MP3同步字节开头）
        mp3_path = Path(self.temp_dir) / "test.mp3"
        original_data = b'\xFF\xFB' + b'\x00' * 100  # MP3同步字节 + 数据
        mp3_path.write_bytes(original_data)

        # 修改音频hash
        result = self.modifier.modify_audio_hash(str(mp3_path), verify_integrity=True)

        self.assertTrue(result.success, "MP3处理应成功")
        self.assertIn("id3v2_tag_added", result.details['operations'], "应包含ID3v2标签操作")
        self.assertTrue(result.details['integrity_ok'], "修改后应通过完整性验证")

        # 验证ID3标签被添加
        modified_data = mp3_path.read_bytes()
        self.assertTrue(modified_data.startswith(b'ID3'), "修改后应以ID3标签开头")

        # 验证原始数据仍存在
        self.assertIn(b'\xFF\xFB', modified_data, "原始MP3数据应保留")

        # 验证统计
        stats = self.modifier.get_statistics()
        self.assertEqual(stats['id3_tags_added'], 1, "应记录1个ID3标签添加")

        print(f"  原始大小: {len(original_data)} 字节")
        print(f"  修改后大小: {len(modified_data)} 字节")
        print(f"  ID3标签大小: {len(modified_data) - len(original_data)} 字节")
        print(f"✅ MP3 ID3标签添加测试通过")

    def test_m4a_id3_tag_addition(self):
        """测试M4A文件添加ID3标签"""
        print("\n=== 测试M4A文件添加ID3标签 ===")

        # 创建模拟M4A文件（以ftyp box开头）
        m4a_path = Path(self.temp_dir) / "test.m4a"
        original_data = (
            b'\x00\x00\x00\x20'  # box大小
            b'ftyp'               # box类型
            b'M4A '               # 主品牌
            b'\x00\x00\x00\x00'  # 次版本
            + b'\x00' * 100
        )
        m4a_path.write_bytes(original_data)

        # 修改音频hash
        result = self.modifier.modify_audio_hash(str(m4a_path), verify_integrity=True)

        self.assertTrue(result.success, "M4A处理应成功")
        self.assertIn("id3v2_tag_added", result.details['operations'], "应包含ID3v2标签操作")

        # 验证ID3标签被添加
        modified_data = m4a_path.read_bytes()
        self.assertTrue(modified_data.startswith(b'ID3'), "修改后应以ID3标签开头")

        # 验证统计
        stats = self.modifier.get_statistics()
        self.assertGreater(stats['id3_tags_added'], 0, "应记录ID3标签添加")

        print(f"  原始大小: {len(original_data)} 字节")
        print(f"  修改后大小: {len(modified_data)} 字节")
        print(f"✅ M4A ID3标签添加测试通过")

    # ==================== WAV RIFF结构测试 ====================

    def test_wav_riff_structure_update(self):
        """测试WAV RIFF结构更新"""
        print("\n=== 测试WAV RIFF结构更新 ===")

        # 创建模拟WAV文件
        wav_path = Path(self.temp_dir) / "test.wav"
        original_data = (
            b'RIFF'               # RIFF标识
            b'\x24\x00\x00\x00'  # 文件大小-8（36字节）
            b'WAVE'               # WAVE标识
            b'fmt '               # fmt chunk
            b'\x10\x00\x00\x00'  # fmt chunk大小
            + b'\x00' * 16        # fmt数据
            + b'data'             # data chunk
            + b'\x00' * 20        # data数据
        )
        wav_path.write_bytes(original_data)

        # 修改音频hash
        result = self.modifier.modify_audio_hash(str(wav_path), verify_integrity=True)

        self.assertTrue(result.success, "WAV处理应成功")
        self.assertIn("riff_structure_updated", result.details['operations'], "应包含RIFF结构更新操作")
        self.assertTrue(result.details['integrity_ok'], "修改后应通过完整性验证")

        # 验证RIFF大小被更新
        modified_data = wav_path.read_bytes()
        new_size = int.from_bytes(modified_data[4:8], byteorder='little')
        expected_size = len(modified_data) - 8

        self.assertEqual(new_size, expected_size, "RIFF大小应正确更新")

        # 验证统计
        stats = self.modifier.get_statistics()
        self.assertEqual(stats['riff_structures_updated'], 1, "应记录1个RIFF结构更新")

        print(f"  原始大小: {len(original_data)} 字节")
        print(f"  修改后大小: {len(modified_data)} 字节")
        print(f"  RIFF大小字段: {new_size} (应为 {expected_size})")
        print(f"✅ WAV RIFF结构更新测试通过")

    def test_riff_chunk_update_edge_cases(self):
        """测试RIFF chunk更新边界情况"""
        print("\n=== 测试RIFF chunk更新边界情况 ===")

        # 测试1: 最小WAV文件
        min_wav = bytearray(b'RIFF\x00\x00\x00\x00WAVE')
        updated = self.modifier._update_wav_riff_chunk(min_wav)
        expected_size = len(updated) - 8
        actual_size = int.from_bytes(updated[4:8], byteorder='little')
        self.assertEqual(actual_size, expected_size, "最小WAV大小应正确")

        # 测试2: 大型WAV文件（>4KB）
        large_wav = bytearray(b'RIFF\x00\x00\x00\x00WAVE' + b'\x00' * 5000)
        updated = self.modifier._update_wav_riff_chunk(large_wav)
        expected_size = len(updated) - 8
        actual_size = int.from_bytes(updated[4:8], byteorder='little')
        self.assertEqual(actual_size, expected_size, "大型WAV大小应正确")

        # 测试3: 非WAV文件应返回原数据
        non_wav = bytearray(b'NOT_RIFF')
        updated = self.modifier._update_wav_riff_chunk(non_wav)
        self.assertEqual(updated, non_wav, "非WAV文件应不修改")

        print(f"  最小WAV: {len(min_wav)} → 大小字段: {actual_size}")
        print(f"  大型WAV: {len(large_wav)} → 大小字段: {actual_size}")
        print(f"  非WAV: 不修改 ✓")
        print(f"✅ RIFF chunk边界情况测试通过")

    # ==================== 音频完整性验证测试 ====================

    def test_mp3_integrity_verification(self):
        """测试MP3完整性验证"""
        print("\n=== 测试MP3完整性验证 ===")

        # 有效的MP3文件
        valid_mp3 = Path(self.temp_dir) / "valid.mp3"
        valid_mp3.write_bytes(b'\xFF\xFB' + b'\x00' * 100)
        self.assertTrue(
            self.modifier._verify_audio_integrity(str(valid_mp3), '.mp3'),
            "有效MP3应通过验证"
        )

        # 有ID3标签的MP3
        id3_mp3 = Path(self.temp_dir) / "id3.mp3"
        id3_mp3.write_bytes(b'ID3' + b'\x00' * 100)
        self.assertTrue(
            self.modifier._verify_audio_integrity(str(id3_mp3), '.mp3'),
            "有ID3标签的MP3应通过验证"
        )

        # 无效的MP3
        invalid_mp3 = Path(self.temp_dir) / "invalid.mp3"
        invalid_mp3.write_bytes(b'INVALID' + b'\x00' * 100)
        self.assertFalse(
            self.modifier._verify_audio_integrity(str(invalid_mp3), '.mp3'),
            "无效MP3应未通过验证"
        )

        print(f"  有效MP3: ✓")
        print(f"  ID3标签MP3: ✓")
        print(f"  无效MP3: ✗")
        print(f"✅ MP3完整性验证测试通过")

    def test_wav_integrity_verification(self):
        """测试WAV完整性验证"""
        print("\n=== 测试WAV完整性验证 ===")

        # 有效的WAV文件
        valid_wav = Path(self.temp_dir) / "valid.wav"
        valid_data = (
            b'RIFF'
            b'\x24\x00\x00\x00'
            b'WAVE'
            + b'\x00' * 50
        )
        valid_wav.write_bytes(valid_data)
        self.assertTrue(
            self.modifier._verify_audio_integrity(str(valid_wav), '.wav'),
            "有效WAV应通过验证"
        )

        # 大小字段错误的WAV
        size_error_wav = Path(self.temp_dir) / "size_error.wav"
        size_error_data = (
            b'RIFF'
            b'\xFF\xFF\xFF\xFF'  # 错误的大小
            b'WAVE'
            + b'\x00' * 50
        )
        size_error_wav.write_bytes(size_error_data)
        self.assertFalse(
            self.modifier._verify_audio_integrity(str(size_error_wav), '.wav'),
            "大小错误的WAV应未通过验证"
        )

        # 无效的WAV
        invalid_wav = Path(self.temp_dir) / "invalid.wav"
        invalid_wav.write_bytes(b'INVALID' + b'\x00' * 100)
        self.assertFalse(
            self.modifier._verify_audio_integrity(str(invalid_wav), '.wav'),
            "无效WAV应未通过验证"
        )

        print(f"  有效WAV: ✓")
        print(f"  大小错误WAV: ✗")
        print(f"  无效WAV: ✗")
        print(f"✅ WAV完整性验证测试通过")

    def test_aiff_integrity_verification(self):
        """测试AIFF完整性验证"""
        print("\n=== 测试AIFF完整性验证 ===")

        # 有效的AIFF文件
        valid_aiff = Path(self.temp_dir) / "valid.aiff"
        valid_aiff.write_bytes(
            b'FORM'                 # FORM标识
            b'\x00\x00\x00\x64'    # chunk大小（100字节）
            b'AIFF'                 # AIFF标识
            + b'\x00' * 100
        )
        self.assertTrue(
            self.modifier._verify_audio_integrity(str(valid_aiff), '.aiff'),
            "有效AIFF应通过验证"
        )

        # 无效的AIFF
        invalid_aiff = Path(self.temp_dir) / "invalid.aiff"
        invalid_aiff.write_bytes(b'INVALID' + b'\x00' * 100)
        self.assertFalse(
            self.modifier._verify_audio_integrity(str(invalid_aiff), '.aiff'),
            "无效AIFF应未通过验证"
        )

        print(f"  有效AIFF: ✓")
        print(f"  无效AIFF: ✗")
        print(f"✅ AIFF完整性验证测试通过")

    def test_m4a_integrity_verification(self):
        """测试M4A完整性验证"""
        print("\n=== 测试M4A完整性验证 ===")

        # 有效的M4A文件（ftyp box）
        valid_m4a = Path(self.temp_dir) / "valid.m4a"
        valid_m4a.write_bytes(
            b'\x00\x00\x00\x20'
            b'ftyp'
            b'M4A '
            + b'\x00' * 100
        )
        self.assertTrue(
            self.modifier._verify_audio_integrity(str(valid_m4a), '.m4a'),
            "有效M4A应通过验证"
        )

        # 无效的M4A
        invalid_m4a = Path(self.temp_dir) / "invalid.m4a"
        invalid_m4a.write_bytes(b'INVALID' + b'\x00' * 100)
        self.assertFalse(
            self.modifier._verify_audio_integrity(str(invalid_m4a), '.m4a'),
            "无效M4A应未通过验证"
        )

        print(f"  有效M4A: ✓")
        print(f"  无效M4A: ✗")
        print(f"✅ M4A完整性验证测试通过")

    # ==================== 集成测试 ====================

    def test_complete_workflow_mp3(self):
        """测试MP3完整工作流程"""
        print("\n=== 测试MP3完整工作流程 ===")

        # 创建MP3文件
        mp3_path = Path(self.temp_dir) / "workflow.mp3"
        mp3_path.write_bytes(b'\xFF\xFB' + b'\x00' * 200)

        # 执行修改（启用完整性验证）
        result = self.modifier.modify_audio_hash(str(mp3_path), verify_integrity=True)

        # 验证结果
        self.assertTrue(result.success, "修改应成功")
        self.assertTrue(result.details['integrity_ok'], "应通过完整性验证")
        self.assertIn('id3v2_tag_added', result.details['operations'], "应包含ID3v2标签操作")

        # 验证统计
        stats = self.modifier.get_statistics()
        self.assertGreater(stats['audio_files_modified'], 0, "应记录文件修改")
        self.assertGreater(stats['id3_tags_added'], 0, "应记录ID3标签添加")
        self.assertGreater(stats['integrity_verified'], 0, "应记录完整性验证")

        print(f"  成功: {result.success}")
        print(f"  操作: {', '.join(result.details['operations'])}")
        print(f"  完整性: {'通过' if result.details['integrity_ok'] else '失败'}")
        print(f"✅ MP3完整工作流程测试通过")

    def test_complete_workflow_wav(self):
        """测试WAV完整工作流程"""
        print("\n=== 测试WAV完整工作流程 ===")

        # 创建WAV文件
        wav_path = Path(self.temp_dir) / "workflow.wav"
        wav_data = (
            b'RIFF'
            b'\x24\x00\x00\x00'
            b'WAVE'
            b'fmt '
            b'\x10\x00\x00\x00'
            + b'\x00' * 16
            + b'data'
            + b'\x00' * 20
        )
        wav_path.write_bytes(wav_data)

        # 执行修改
        result = self.modifier.modify_audio_hash(str(wav_path), verify_integrity=True)

        # 验证结果
        self.assertTrue(result.success, "修改应成功")
        self.assertTrue(result.details['integrity_ok'], "应通过完整性验证")
        self.assertIn('silent_data_added', result.details['operations'], "应包含静音数据操作")
        self.assertIn('riff_structure_updated', result.details['operations'], "应包含RIFF结构更新操作")

        # 验证统计
        stats = self.modifier.get_statistics()
        self.assertGreater(stats['riff_structures_updated'], 0, "应记录RIFF结构更新")

        print(f"  成功: {result.success}")
        print(f"  操作: {', '.join(result.details['operations'])}")
        print(f"  完整性: {'通过' if result.details['integrity_ok'] else '失败'}")
        print(f"✅ WAV完整工作流程测试通过")

    def test_statistics_tracking(self):
        """测试统计信息追踪"""
        print("\n=== 测试统计信息追踪 ===")

        # 处理多个文件
        mp3_path = Path(self.temp_dir) / "stat.mp3"
        mp3_path.write_bytes(b'\xFF\xFB' + b'\x00' * 100)
        self.modifier.modify_audio_hash(str(mp3_path), verify_integrity=True)

        wav_path = Path(self.temp_dir) / "stat.wav"
        wav_path.write_bytes(b'RIFF\x24\x00\x00\x00WAVE' + b'\x00' * 50)
        self.modifier.modify_audio_hash(str(wav_path), verify_integrity=True)

        # 获取统计
        stats = self.modifier.get_statistics()

        # 验证统计信息
        self.assertEqual(stats['audio_files_modified'], 2, "应处理2个文件")
        self.assertGreater(stats['id3_tags_added'], 0, "应有ID3标签添加记录")
        self.assertGreater(stats['riff_structures_updated'], 0, "应有RIFF更新记录")
        self.assertEqual(stats['integrity_verified'], 2, "应验证2个文件")

        print(f"  处理文件数: {stats['audio_files_modified']}")
        print(f"  ID3标签添加: {stats['id3_tags_added']}")
        print(f"  RIFF结构更新: {stats['riff_structures_updated']}")
        print(f"  完整性验证: {stats['integrity_verified']}")
        print(f"✅ 统计信息追踪测试通过")

    def test_verify_integrity_parameter(self):
        """测试verify_integrity参数控制"""
        print("\n=== 测试verify_integrity参数控制 ===")

        # 创建MP3文件
        mp3_path = Path(self.temp_dir) / "verify_test.mp3"
        mp3_path.write_bytes(b'\xFF\xFB' + b'\x00' * 100)

        # 不启用验证
        result1 = self.modifier.modify_audio_hash(str(mp3_path), verify_integrity=False)
        self.assertTrue(result1.success)
        self.assertIsNone(result1.details.get('integrity_ok'), "不应有完整性验证结果")

        # 重新创建文件
        mp3_path.write_bytes(b'\xFF\xFB' + b'\x00' * 100)

        # 启用验证
        result2 = self.modifier.modify_audio_hash(str(mp3_path), verify_integrity=True)
        self.assertTrue(result2.success)
        self.assertIsNotNone(result2.details.get('integrity_ok'), "应有完整性验证结果")
        self.assertTrue(result2.details['integrity_ok'], "应通过验证")

        print(f"  未启用验证: integrity_ok = {result1.details.get('integrity_ok')}")
        print(f"  启用验证: integrity_ok = {result2.details.get('integrity_ok')}")
        print(f"✅ verify_integrity参数控制测试通过")


if __name__ == '__main__':
    # 运行测试
    suite = unittest.TestLoader().loadTestsFromTestCase(TestP3AudioEnhancement)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 输出测试总结
    print("\n" + "="*70)
    print("P3阶段三测试总结")
    print("="*70)
    print(f"总测试数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")

    if result.wasSuccessful():
        print("\n✅ 所有测试通过!")
        sys.exit(0)
    else:
        print("\n❌ 测试失败!")
        sys.exit(1)
