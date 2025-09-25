#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
优化的Mars xlog解码器 - 支持多线程并行处理
"""

import os
import struct
import zlib
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from typing import List, Tuple, Optional

# 从原始解码器导入常量
MAGIC_NO_COMPRESS_START = 0x03
MAGIC_NO_COMPRESS_START1 = 0x06
MAGIC_NO_COMPRESS_NO_CRYPT_START = 0x08
MAGIC_COMPRESS_START = 0x04
MAGIC_COMPRESS_START1 = 0x05
MAGIC_COMPRESS_START2 = 0x07
MAGIC_COMPRESS_NO_CRYPT_START = 0x09
MAGIC_END = 0x00

class OptimizedXLogDecoder:
    """优化的xlog解码器"""

    def __init__(self, max_workers=4):
        self.max_workers = max_workers
        self.lastseq = 0
        self.seq_lock = threading.Lock()

    def is_good_log_buffer(self, buffer, offset, count):
        """验证日志缓冲区"""
        if offset == len(buffer):
            return (True, '')

        if offset >= len(buffer):
            return (False, 'offset exceeds buffer length')

        magic_start = buffer[offset]
        if magic_start in [MAGIC_NO_COMPRESS_START, MAGIC_COMPRESS_START, MAGIC_COMPRESS_START1]:
            crypt_key_len = 4
        elif magic_start in [MAGIC_COMPRESS_START2, MAGIC_NO_COMPRESS_START1,
                            MAGIC_NO_COMPRESS_NO_CRYPT_START, MAGIC_COMPRESS_NO_CRYPT_START]:
            crypt_key_len = 64
        else:
            return (False, f'buffer[{offset}]:{buffer[offset]} != MAGIC_NUM_START')

        header_len = 1 + 2 + 1 + 1 + 4 + crypt_key_len

        if offset + header_len + 1 + 1 > len(buffer):
            return (False, f'offset:{offset} > len(buffer):{len(buffer)}')

        length = struct.unpack_from("I", memoryview(buffer[offset+header_len-4-crypt_key_len:offset+header_len-crypt_key_len]))[0]

        if offset + header_len + length + 1 > len(buffer):
            return (False, f'log length:{length}, end pos {offset + header_len + length + 1} > len(buffer):{len(buffer)}')

        if MAGIC_END != buffer[offset + header_len + length]:
            return (False, f'log length:{length}, buffer[{offset + header_len + length}]:{buffer[offset + header_len + length]} != MAGIC_END')

        if count <= 1:
            return (True, '')
        else:
            return self.is_good_log_buffer(buffer, offset+header_len+length+1, count-1)

    def get_log_start_pos(self, buffer, count):
        """查找日志开始位置"""
        offset = 0
        while offset < len(buffer):
            if buffer[offset] in [MAGIC_NO_COMPRESS_START, MAGIC_NO_COMPRESS_START1,
                                 MAGIC_COMPRESS_START, MAGIC_COMPRESS_START1,
                                 MAGIC_COMPRESS_START2, MAGIC_COMPRESS_NO_CRYPT_START,
                                 MAGIC_NO_COMPRESS_NO_CRYPT_START]:
                if self.is_good_log_buffer(buffer, offset, count)[0]:
                    return offset
            offset += 1
        return -1

    def decode_buffer_chunk(self, buffer, start_offset, end_offset) -> List[str]:
        """解码缓冲区的一个块"""
        results = []
        offset = start_offset

        while offset < len(buffer):
            # 如果超过块的结束位置，停止处理
            if offset >= end_offset:
                break

            # 查找下一个有效的日志开始位置
            if not self.is_good_log_buffer(buffer, offset, 1)[0]:
                fixpos = self.get_log_start_pos(buffer[offset:min(offset+1000, len(buffer))], 1)
                if fixpos == -1:
                    break
                results.append(f"[F]decode error at offset {offset}\n")
                offset += fixpos

            if offset >= len(buffer):
                break

            magic_start = buffer[offset]
            if magic_start in [MAGIC_NO_COMPRESS_START, MAGIC_COMPRESS_START, MAGIC_COMPRESS_START1]:
                crypt_key_len = 4
            elif magic_start in [MAGIC_COMPRESS_START2, MAGIC_NO_COMPRESS_START1,
                                MAGIC_NO_COMPRESS_NO_CRYPT_START, MAGIC_COMPRESS_NO_CRYPT_START]:
                crypt_key_len = 64
            else:
                offset += 1
                continue

            header_len = 1 + 2 + 1 + 1 + 4 + crypt_key_len

            if offset + header_len > len(buffer):
                break

            length = struct.unpack_from("I", memoryview(buffer[offset+header_len-4-crypt_key_len:offset+header_len-crypt_key_len]))[0]

            if offset + header_len + length > len(buffer):
                break

            # 如果日志跨越块边界，这个块不处理该日志（留给下一个块处理）
            if offset + header_len + length > end_offset and end_offset < len(buffer):
                break

            # 提取序列号（用于检测丢失）
            seq = struct.unpack_from("H", memoryview(buffer[offset+header_len-4-crypt_key_len-2-2:offset+header_len-4-crypt_key_len-2]))[0]

            with self.seq_lock:
                if seq != 0 and seq != 1 and self.lastseq != 0 and seq != (self.lastseq + 1):
                    results.append(f"[F]log seq:{self.lastseq+1}-{seq-1} is missing\n")
                if seq != 0:
                    self.lastseq = seq

            tmpbuffer = buffer[offset+header_len:offset+header_len+length]

            try:
                # 解压缩
                if magic_start in [MAGIC_COMPRESS_START, MAGIC_COMPRESS_NO_CRYPT_START]:
                    decompressor = zlib.decompressobj(-zlib.MAX_WBITS)
                    tmpbuffer = decompressor.decompress(bytes(tmpbuffer))
                elif magic_start == MAGIC_COMPRESS_START1:
                    decompress_data = bytearray()
                    tmp = bytearray(tmpbuffer)
                    while len(tmp) > 0:
                        single_log_len = struct.unpack_from("H", memoryview(tmp[0:2]))[0]
                        decompress_data.extend(tmp[2:single_log_len+2])
                        tmp = tmp[single_log_len+2:]
                    decompressor = zlib.decompressobj(-zlib.MAX_WBITS)
                    tmpbuffer = decompressor.decompress(bytes(decompress_data))

                # 转换为字符串
                if isinstance(tmpbuffer, bytes):
                    results.append(tmpbuffer.decode('utf-8', errors='ignore'))
                elif isinstance(tmpbuffer, bytearray):
                    results.append(tmpbuffer.decode('utf-8', errors='ignore'))
                else:
                    results.append(str(tmpbuffer))

            except Exception as e:
                results.append(f"[F]decompress error: {e}\n")

            offset += header_len + length + 1

        return results

    def decode_file_parallel(self, filepath: str, progress_callback=None) -> List[str]:
        """并行解码文件"""
        if not os.path.exists(filepath):
            return []

        file_size = os.path.getsize(filepath)

        # 读取整个文件到内存
        with open(filepath, "rb") as fp:
            buffer = bytearray(file_size)
            fp.readinto(buffer)

        # 查找第一个有效的日志位置
        start_pos = self.get_log_start_pos(buffer, 2)
        if start_pos == -1:
            return []

        # 将文件分成多个块进行并行处理
        chunk_size = max(file_size // self.max_workers, 1024 * 1024)  # 至少1MB每块
        chunks = []

        offset = start_pos
        while offset < file_size:
            # 找到块的结束位置
            end_offset = min(offset + chunk_size, file_size)

            # 如果不是最后一个块，找到下一个日志边界
            if end_offset < file_size:
                # 从结束位置开始找下一个日志开始
                next_log_pos = self.get_log_start_pos(buffer[end_offset:min(end_offset+1000, file_size)], 1)
                if next_log_pos != -1:
                    end_offset = end_offset + next_log_pos
                else:
                    # 如果找不到下一个日志，直接使用文件结束
                    end_offset = file_size

            chunks.append((offset, end_offset))
            offset = end_offset

        # 并行解码各个块
        all_results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            for i, (start, end) in enumerate(chunks):
                future = executor.submit(self.decode_buffer_chunk, buffer, start, end)
                futures.append((i, future))

            # 按顺序收集结果
            for i, (chunk_idx, future) in enumerate(sorted(futures, key=lambda x: x[0])):
                try:
                    chunk_results = future.result(timeout=30)
                    all_results.extend(chunk_results)

                    if progress_callback:
                        progress = (i + 1) / len(chunks) * 100
                        progress_callback(progress)

                except Exception as e:
                    all_results.append(f"[F]Error processing chunk {chunk_idx}: {e}\n")

        return all_results

    def decode_files_batch(self, filepaths: List[str], progress_callback=None) -> dict:
        """批量解码多个文件"""
        results = {}
        total_files = len(filepaths)

        for i, filepath in enumerate(filepaths):
            if progress_callback:
                file_progress = i / total_files * 100
                progress_callback(file_progress, f"解析文件: {os.path.basename(filepath)}")

            # 解码单个文件
            file_results = self.decode_file_parallel(
                filepath,
                lambda p: progress_callback(file_progress + p / total_files, None) if progress_callback else None
            )

            results[filepath] = file_results

        if progress_callback:
            progress_callback(100, "解析完成")

        return results