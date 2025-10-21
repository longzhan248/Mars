#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件操作模块
处理文件加载、解码、导出等操作
"""

import json
import os
import sys
from collections import defaultdict
from datetime import datetime
from typing import Callable, List, Optional

# 添加解码器路径
decoders_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'decoders')
if decoders_path not in sys.path:
    sys.path.insert(0, decoders_path)

from .data_models import FileGroup, LogEntry
from .exceptions import (
    DecodingError,
    FileOperationError,
    ImportError,
    LogParsingError,
    handle_exceptions,
    get_global_error_collector
)


class FileOperations:
    """文件操作类"""

    def __init__(self):
        pass

    @staticmethod
    def group_files(files: List[str]) -> List[FileGroup]:
        """将多个文件按基础名称分组"""
        groups = defaultdict(list)

        # 支持多种日志文件命名模式
        # 1. mizhua_20250915_123456.xlog -> mizhua
        # 2. app_2025-09-15_12-34-56.log -> app
        # 3. debug.1.log, debug.2.log -> debug
        # 4. system_1.xlog.log -> system

        for filepath in files:
            filename = os.path.basename(filepath)

            # 移除所有扩展名
            base = filename
            for ext in ['.xlog.log', '.xlog', '.log', '.txt']:
                if base.endswith(ext):
                    base = base[:-len(ext)]
                    break

            # 提取基础名称（移除日期、时间、序号等后缀）
            import re

            # 模式1: name_20250915 或 name_20250915_123456
            pattern1 = r'^(.+?)_\d{8}(?:_\d+)?$'
            # 模式2: name_2025-09-15 或 name_2025-09-15_12-34-56
            pattern2 = r'^(.+?)_\d{4}-\d{2}-\d{2}(?:_[\d-]+)?$'
            # 模式3: name.数字 (如 debug.1)
            pattern3 = r'^(.+?)\.\d+$'
            # 模式4: name_数字 (如 system_1)
            pattern4 = r'^(.+?)_\d+$'

            for pattern in [pattern1, pattern2, pattern3, pattern4]:
                match = re.match(pattern, base)
                if match:
                    base = match.group(1)
                    break

            groups[base].append(filepath)

        # 创建FileGroup对象
        file_groups = []
        for base_name, filepaths in groups.items():
            group = FileGroup(base_name)
            # 按文件名排序，确保顺序一致
            for filepath in sorted(filepaths):
                group.add_file(filepath)
            file_groups.append(group)

        return file_groups

    @staticmethod
    def decode_xlog_files(files: List[str], callback: Optional[Callable[[int, int, str], None]] = None) -> List[str]:
        """解码多个xlog文件

        Args:
            files: 文件路径列表
            callback: 进度回调函数 callback(current, total, message)

        Returns:
            解码后的文件路径列表
        """
        decoded_files = []
        total = len(files)

        for i, filepath in enumerate(files):
            if callback:
                callback(i, total, f"正在解码: {os.path.basename(filepath)}")

            # 检查是否是xlog文件
            if not filepath.endswith('.xlog'):
                decoded_files.append(filepath)
                continue

            # 解码xlog文件
            try:
                decoded_path = FileOperations.decode_single_xlog(filepath)
                if decoded_path:
                    decoded_files.append(decoded_path)
            except Exception as e:
                print(f"解码失败 {filepath}: {e}")
                # 解码失败时仍然添加原始文件，让后续处理决定
                decoded_files.append(filepath)

        if callback:
            callback(total, total, "解码完成")

        return decoded_files

    @staticmethod
    @handle_exceptions(DecodingError, reraise=False, default_return=None)
    def decode_single_xlog(xlog_path: str) -> Optional[str]:
        """解码单个xlog文件"""
        try:
            # 优先使用快速解码器
            from fast_decoder import FastMarsDecoder

            output_path = xlog_path + '.log'
            decoder = FastMarsDecoder()

            if decoder.decode_file(xlog_path, output_path):
                return output_path
            else:
                # 快速解码器失败，尝试标准解码器
                return FileOperations.decode_with_standard(xlog_path)

        except ImportError as e:
            # 快速解码器不可用，使用标准解码器
            raise DecodingError(
                message=f"快速解码器不可用，将使用标准解码器",
                decoder_type="FastMarsDecoder",
                filepath=xlog_path,
                cause=e
            )
        except Exception as e:
            # 快速解码器执行失败
            raise DecodingError(
                message=f"快速解码器执行失败，将尝试标准解码器: {str(e)}",
                decoder_type="FastMarsDecoder",
                filepath=xlog_path,
                cause=e
            )

    @staticmethod
    @handle_exceptions(DecodingError, reraise=False, default_return=None)
    def decode_with_standard(xlog_path: str) -> Optional[str]:
        """使用标准解码器"""
        try:
            # 使用标准Python 3解码器
            from decode_mars_nocrypt_log_file_py3 import ParseMarsFile

            output_path = xlog_path + '.log'
            parser = ParseMarsFile(xlog_path, output_path)
            parser.decode()

            if os.path.exists(output_path):
                return output_path
            else:
                raise DecodingError(
                    message="解码完成但未生成输出文件",
                    decoder_type="StandardDecoder",
                    filepath=xlog_path
                )
        except Exception as e:
            raise DecodingError(
                message=f"标准解码器失败: {str(e)}",
                decoder_type="StandardDecoder",
                filepath=xlog_path,
                cause=e
            )

    @staticmethod
    @handle_exceptions(FileOperationError, reraise=False, default_return=[])
    def load_log_file(filepath: str) -> List[str]:
        """加载日志文件内容

        Returns:
            日志行列表
        """
        if not os.path.exists(filepath):
            raise FileOperationError(
                message=f"文件不存在: {filepath}",
                filepath=filepath,
                operation="文件加载",
                user_message="指定的文件不存在，请检查文件路径"
            )

        if not os.path.isfile(filepath):
            raise FileOperationError(
                message=f"不是有效文件: {filepath}",
                filepath=filepath,
                operation="文件加载",
                user_message="指定的路径不是有效文件"
            )

        # 自动检测编码
        encodings = ['utf-8', 'gb2312', 'gbk', 'gb18030', 'latin-1']
        last_error = None

        for encoding in encodings:
            try:
                with open(filepath, 'r', encoding=encoding) as f:
                    lines = f.readlines()
                return lines
            except UnicodeDecodeError as e:
                last_error = e
                continue
            except Exception as e:
                raise FileOperationError(
                    message=f"读取文件失败 (编码: {encoding}): {str(e)}",
                    filepath=filepath,
                    operation="文件读取",
                    user_message=f"读取文件失败: {os.path.basename(filepath)}",
                    cause=e
                )

        # 如果所有编码都失败，使用二进制模式
        try:
            with open(filepath, 'rb') as f:
                content = f.read()
                # 尝试忽略错误解码
                lines = content.decode('utf-8', errors='ignore').splitlines(keepends=True)
            return lines
        except Exception as e:
            raise FileOperationError(
                message=f"所有编码尝试均失败，最后错误: {str(last_error)}",
                filepath=filepath,
                operation="编码检测",
                user_message=f"文件编码格式不支持: {os.path.basename(filepath)}",
                cause=last_error or e
            )

    @staticmethod
    @handle_exceptions(LogParsingError, reraise=False, default_return=[])
    def parse_log_lines(lines: List[str], source_file: str = "") -> List[LogEntry]:
        """解析日志行为LogEntry对象

        Args:
            lines: 日志行列表
            source_file: 来源文件名

        Returns:
            LogEntry对象列表
        """
        if not lines:
            return []

        entries = []
        error_count = 0
        max_errors = 100  # 限制最大错误数量，避免内存溢出

        for line_num, line in enumerate(lines, 1):
            try:
                line = line.strip()
                if not line:
                    continue

                entry = LogEntry(line, source_file)
                entries.append(entry)

                # 重置错误计数器
                error_count = 0

            except Exception as e:
                error_count += 1
                if error_count <= max_errors:
                    # 只记录前100个错误，避免日志泛滥
                    error = LogParsingError(
                        message=f"解析日志行失败: {str(e)}",
                        line_number=line_num,
                        line_content=line,
                        parsing_format="Mars",
                        source_file=source_file,
                        cause=e
                    )
                    get_global_error_collector().add_exception(error)

                if error_count > max_errors + 10:  # 超过限制后10行就停止
                    raise LogParsingError(
                        message=f"解析错误过多 ({error_count}个)，停止处理",
                        line_number=line_num,
                        source_file=source_file
                    )

        return entries

    @staticmethod
    @handle_exceptions(ImportError, reraise=False, default_return=False)
    def export_to_file(entries: List[LogEntry], filepath: str, format: str = 'txt') -> bool:
        """导出日志条目到文件

        Args:
            entries: LogEntry对象列表
            filepath: 输出文件路径
            format: 导出格式 (txt, json, csv)
        """
        if not entries:
            raise ImportError(
                message="没有可导出的数据",
                format_type=format,
                user_message="没有找到可导出的日志条目"
            )

        # 检查输出目录是否存在
        output_dir = os.path.dirname(filepath)
        if output_dir and not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir, exist_ok=True)
            except Exception as e:
                raise ImportError(
                    message=f"无法创建输出目录: {output_dir}",
                    format_type=format,
                    user_message="无法创建输出目录，请检查权限",
                    cause=e
                )

        # 检查写入权限
        if os.path.exists(filepath) and not os.access(filepath, os.W_OK):
            raise ImportError(
                message=f"文件不可写: {filepath}",
                format_type=format,
                user_message="目标文件不可写，请检查文件权限"
            )

        try:
            if format == 'json':
                FileOperations.export_to_json(entries, filepath)
            elif format == 'csv':
                FileOperations.export_to_csv(entries, filepath)
            else:  # txt
                FileOperations.export_to_txt(entries, filepath)
            return True
        except Exception as e:
            raise ImportError(
                message=f"导出数据失败: {str(e)}",
                format_type=format,
                filepath=filepath,
                user_message=f"导出文件失败: {os.path.basename(filepath)}",
                cause=e
            )

    @staticmethod
    def export_to_txt(entries: List[LogEntry], filepath: str) -> None:
        """导出为文本格式"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# Mars日志导出\n")
            f.write(f"# 导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# 总计: {len(entries)} 条日志\n")
            f.write("-" * 80 + "\n\n")

            for entry in entries:
                f.write(entry.raw_line + '\n')

    @staticmethod
    def export_to_json(entries: List[LogEntry], filepath: str) -> None:
        """导出为JSON格式"""
        data = {
            'export_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_count': len(entries),
            'entries': []
        }

        for entry in entries:
            data['entries'].append({
                'level': entry.level,
                'timestamp': entry.timestamp,
                'module': entry.module,
                'thread_id': entry.thread_id,
                'content': entry.content,
                'raw': entry.raw_line,
                'source_file': entry.source_file,
                'is_crash': entry.is_crash
            })

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @staticmethod
    def export_to_csv(entries: List[LogEntry], filepath: str) -> None:
        """导出为CSV格式"""
        import csv

        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)

            # 写入头部
            writer.writerow(['时间戳', '级别', '模块', '线程ID', '内容', '来源文件', '是否崩溃'])

            # 写入数据
            for entry in entries:
                writer.writerow([
                    entry.timestamp or '',
                    entry.level or '',
                    entry.module or '',
                    entry.thread_id or '',
                    entry.content or entry.raw_line,
                    entry.source_file or '',
                    '是' if entry.is_crash else '否'
                ])