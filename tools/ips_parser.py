#!/usr/bin/env python3
"""
IPS (iOS Crash Report) Parser
Based on MacSymbolicator's approach for parsing and symbolicating iOS crash reports
"""

import json
import re
import subprocess
import tempfile
import os
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class BinaryImage:
    """表示二进制映像信息"""
    base: int
    size: int
    uuid: str
    path: str
    name: str
    arch: str

    @property
    def end_address(self) -> int:
        return self.base + self.size

@dataclass
class StackFrame:
    """表示堆栈帧"""
    index: int
    binary_name: str
    address: int
    symbol: Optional[str] = None
    offset: Optional[int] = None
    source_file: Optional[str] = None
    source_line: Optional[int] = None

class IPSParser:
    """IPS崩溃报告解析器"""

    def __init__(self):
        self.summary = {}
        self.detail = {}
        self.binary_images = []
        self.threads = []
        self.crashed_thread = None

    def parse_file(self, filepath: str) -> bool:
        """解析IPS文件"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().strip()

            return self.parse_content(content)
        except Exception:
            return False

    def parse_content(self, content: str) -> bool:
        """解析IPS内容"""
        lines = content.strip().split('\n', 1)

        if not lines:
            return False

        try:
            # IPS格式：第一行是摘要JSON，第二行开始是详细JSON
            if lines[0].startswith('{') and lines[0].endswith('}'):
                self.summary = json.loads(lines[0])

                if len(lines) > 1:
                    # 解析详细JSON
                    self.detail = json.loads(lines[1])
                else:
                    # 只有摘要
                    return True
            else:
                # 尝试整个内容作为JSON
                data = json.loads(content)
                if 'app_name' in data:
                    self.summary = data
                else:
                    self.detail = data

            # 提取关键信息
            self._extract_info()
            return True

        except json.JSONDecodeError:
            return False

    def _extract_info(self):
        """从JSON中提取关键信息"""
        # 提取二进制映像
        if 'usedImages' in self.detail:
            for img in self.detail['usedImages']:
                binary = BinaryImage(
                    base=img.get('base', 0),
                    size=img.get('size', 0),
                    uuid=img.get('uuid', ''),
                    path=img.get('path', ''),
                    name=img.get('name', ''),
                    arch=img.get('arch', '')
                )
                self.binary_images.append(binary)

        # 提取线程信息
        if 'threads' in self.detail:
            self.threads = self.detail['threads']

            # 找出崩溃线程
            for i, thread in enumerate(self.threads):
                if thread.get('triggered', False):
                    self.crashed_thread = i
                    break

    def _is_app_binary(self, binary_name: str, bundle_id: str) -> bool:
        """判断是否为应用的二进制文件

        Args:
            binary_name: 二进制文件名
            bundle_id: 应用的bundle ID

        Returns:
            是否为应用二进制
        """
        # 缓存属性避免重复访问
        if not hasattr(self, '_app_name'):
            self._app_name = self.summary.get('app_name', '')

        # 应用名称通常与二进制名称相同
        if self._app_name and binary_name == self._app_name:
            return True

        # 建立二进制名称到路径的映射（缓存）
        if not hasattr(self, '_binary_map'):
            self._binary_map = {img.name: img.path for img in self.binary_images}

        path = self._binary_map.get(binary_name, '')
        if not path:
            return False

        # 快速路径检查
        if bundle_id in path:
            return True
        if '/System/' in path or '/usr/' in path:
            return False
        if '/var/containers/' in path or '/Applications/' in path:
            return True

        return False

    def get_crash_info(self) -> Dict[str, Any]:
        """获取崩溃摘要信息"""
        info = {}

        # 从summary获取
        info['app_name'] = self.summary.get('app_name', 'Unknown')
        info['app_version'] = self.summary.get('app_version', 'Unknown')
        info['bundle_id'] = self.summary.get('bundleID', 'Unknown')
        info['timestamp'] = self.summary.get('timestamp', 'Unknown')
        info['os_version'] = self.summary.get('os_version', 'Unknown')

        # 从detail补充
        if self.detail:
            info['process_name'] = self.detail.get('procName', info['app_name'])
            info['process_path'] = self.detail.get('procPath', '')
            info['incident_id'] = self.detail.get('incident', '')

            # 异常信息
            if 'exception' in self.detail:
                exc = self.detail['exception']
                info['exception_type'] = exc.get('type', '')
                info['exception_codes'] = exc.get('codes', '')
                info['exception_signal'] = exc.get('signal', '')

            # 终止信息
            if 'termination' in self.detail:
                term = self.detail['termination']
                info['termination_reason'] = term.get('indicator', '')

        info['crashed_thread'] = self.crashed_thread

        return info

    def get_crashed_thread_frames(self) -> List[StackFrame]:
        """获取崩溃线程的堆栈帧"""
        frames = []

        if self.crashed_thread is None or not self.threads:
            return frames

        crashed = self.threads[self.crashed_thread]

        for i, frame_data in enumerate(crashed.get('frames', [])):
            # 获取二进制映像
            image_index = frame_data.get('imageIndex', -1)
            binary_name = 'Unknown'

            if 0 <= image_index < len(self.binary_images):
                binary_name = self.binary_images[image_index].name

            frame = StackFrame(
                index=i,
                binary_name=binary_name,
                address=frame_data.get('imageOffset', 0),
                symbol=frame_data.get('symbol'),
                offset=frame_data.get('symbolLocation')
            )

            # 如果有源文件信息
            if 'sourceFile' in frame_data:
                frame.source_file = frame_data['sourceFile']
            if 'sourceLine' in frame_data:
                frame.source_line = frame_data['sourceLine']

            frames.append(frame)

        return frames

    def to_crash_format(self, with_tags=False) -> str:
        """转换为传统crash格式

        Args:
            with_tags: 是否包含标记信息用于GUI显示
        """
        lines = []
        info = self.get_crash_info()

        # 头部信息
        lines.append(f"Incident Identifier: {info.get('incident_id', 'Unknown')}")
        lines.append(f"Hardware Model: {self.detail.get('modelCode', 'Unknown')}")
        lines.append(f"Process: {info['process_name']} [{self.detail.get('pid', '?')}]")
        lines.append(f"Path: {info['process_path']}")
        lines.append(f"Identifier: {info['bundle_id']}")
        lines.append(f"Version: {info['app_version']} ({self.summary.get('build_version', '?')})")
        lines.append(f"OS Version: {info['os_version']}")
        lines.append("")

        # 异常信息
        if 'exception_type' in info:
            lines.append(f"Exception Type: {info['exception_type']}")
            lines.append(f"Exception Codes: {info['exception_codes']}")
            if 'exception_signal' in info:
                lines.append(f"Exception Signal: {info['exception_signal']}")
            lines.append("")

        # 终止原因
        if 'termination_reason' in info:
            lines.append(f"Termination Reason: {info['termination_reason']}")
            lines.append("")

        # 崩溃线程
        if self.crashed_thread is not None:
            lines.append(f"Crashed Thread: {self.crashed_thread}")
            lines.append("")

            # 崩溃线程堆栈
            lines.append(f"Thread {self.crashed_thread} Crashed:")
            frames = self.get_crashed_thread_frames()

            for frame in frames:
                # 判断是否为应用符号
                is_app_symbol = self._is_app_binary(frame.binary_name, info['bundle_id'])

                if with_tags and is_app_symbol:
                    tag = "[APP]"
                elif with_tags:
                    tag = "[SYS]"
                else:
                    tag = ""

                if frame.symbol:
                    if frame.offset is not None:
                        lines.append(f"{tag}{frame.index:3d} {frame.binary_name:<30} 0x{frame.address:016x} {frame.symbol} + {frame.offset}")
                    else:
                        lines.append(f"{tag}{frame.index:3d} {frame.binary_name:<30} 0x{frame.address:016x} {frame.symbol}")
                else:
                    lines.append(f"{tag}{frame.index:3d} {frame.binary_name:<30} 0x{frame.address:016x} 0x{frame.address:x}")

            lines.append("")

        # 其他线程
        for i, thread in enumerate(self.threads):
            if i == self.crashed_thread:
                continue

            thread_name = thread.get('name', '')
            if thread_name:
                lines.append(f"Thread {i} name: {thread_name}")
            lines.append(f"Thread {i}:")

            for j, frame_data in enumerate(thread.get('frames', [])):
                image_index = frame_data.get('imageIndex', -1)
                binary_name = 'Unknown'

                if 0 <= image_index < len(self.binary_images):
                    binary_name = self.binary_images[image_index].name

                address = frame_data.get('imageOffset', 0)
                symbol = frame_data.get('symbol', '')

                if symbol:
                    offset = frame_data.get('symbolLocation', 0)
                    lines.append(f"{j:3d} {binary_name:<30} 0x{address:016x} {symbol} + {offset}")
                else:
                    lines.append(f"{j:3d} {binary_name:<30} 0x{address:016x} 0x{address:x}")

            lines.append("")

        # 二进制映像
        lines.append("Binary Images:")
        for img in self.binary_images:
            lines.append(f"0x{img.base:x} - 0x{img.end_address:x} {img.name} {img.arch} <{img.uuid}> {img.path}")

        return '\n'.join(lines)


class IPSSymbolicator:
    """IPS崩溃报告符号化器"""

    def __init__(self, ips_parser: IPSParser):
        self.parser = ips_parser
        self.dsym_path = None
        self.dsym_uuids = {}

    def set_dsym(self, dsym_path: str) -> bool:
        """设置dSYM文件路径"""
        if not os.path.exists(dsym_path):
            return False

        self.dsym_path = dsym_path
        self._extract_dsym_uuids()
        return True

    def _extract_dsym_uuids(self):
        """提取dSYM的UUID信息"""
        if not self.dsym_path:
            return

        try:
            # 查找dSYM中的二进制文件
            dwarf_dir = os.path.join(self.dsym_path, 'Contents', 'Resources', 'DWARF')
            if os.path.exists(dwarf_dir):
                for binary_name in os.listdir(dwarf_dir):
                    binary_path = os.path.join(dwarf_dir, binary_name)

                    # 使用dwarfdump获取UUID
                    result = subprocess.run(
                        ['dwarfdump', '--uuid', binary_path],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )

                    if result.returncode == 0:
                        # 解析UUID输出
                        for line in result.stdout.split('\n'):
                            if 'UUID:' in line:
                                parts = line.split()
                                if len(parts) >= 2:
                                    uuid = parts[1]
                                    arch = parts[2].strip('()') if len(parts) > 2 else 'unknown'
                                    self.dsym_uuids[uuid.lower()] = {
                                        'path': binary_path,
                                        'arch': arch,
                                        'name': binary_name
                                    }

        except Exception:
            pass  # 静默处理错误

    def symbolicate(self, with_tags=True) -> str:
        """符号化崩溃报告

        Args:
            with_tags: 是否包含标记信息用于GUI显示
        """
        if not self.dsym_path or not self.dsym_uuids:
            return self.parser.to_crash_format(with_tags=with_tags)

        # 获取需要符号化的地址
        symbolication_tasks = self._prepare_symbolication_tasks()

        if not symbolication_tasks:
            return self.parser.to_crash_format(with_tags=with_tags)

        # 执行符号化
        symbolicated_frames = {}

        for uuid, task in symbolication_tasks.items():
            if uuid.lower() not in self.dsym_uuids:
                continue

            dsym_info = self.dsym_uuids[uuid.lower()]
            results = self._symbolicate_addresses(
                dsym_info['path'],
                task['arch'],
                task['load_address'],
                task['addresses']
            )

            if results:
                for addr, symbol in zip(task['addresses'], results):
                    symbolicated_frames[addr] = symbol

        # 更新符号信息
        self._update_symbols(symbolicated_frames)

        return self.parser.to_crash_format(with_tags=with_tags)

    def _prepare_symbolication_tasks(self) -> Dict[str, Dict]:
        """准备符号化任务"""
        tasks = {}

        # 处理崩溃线程
        if self.parser.crashed_thread is not None:
            crashed = self.parser.threads[self.parser.crashed_thread]

            for frame in crashed.get('frames', []):
                image_index = frame.get('imageIndex', -1)

                if 0 <= image_index < len(self.parser.binary_images):
                    img = self.parser.binary_images[image_index]

                    if img.uuid not in tasks:
                        tasks[img.uuid] = {
                            'arch': img.arch,
                            'load_address': img.base,
                            'addresses': []
                        }

                    # 计算实际地址
                    offset = frame.get('imageOffset', 0)
                    actual_address = img.base + offset
                    tasks[img.uuid]['addresses'].append(actual_address)

        return tasks

    def _symbolicate_addresses(self, binary_path: str, arch: str, load_address: int, addresses: List[int]) -> List[str]:
        """使用atos符号化地址"""
        if not addresses:
            return []

        try:
            # 准备atos命令
            cmd = ['atos', '-arch', arch, '-o', binary_path, '-l', hex(load_address)]

            # 添加地址
            for addr in addresses:
                cmd.append(hex(addr))

            # 执行atos
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                # 解析结果
                lines = result.stdout.strip().split('\n')
                return lines

        except Exception:
            pass

        return []

    def _update_symbols(self, symbolicated_frames: Dict[int, str]):
        """更新堆栈帧的符号信息"""
        if self.parser.crashed_thread is not None:
            crashed = self.parser.threads[self.parser.crashed_thread]

            for frame in crashed.get('frames', []):
                image_index = frame.get('imageIndex', -1)

                if 0 <= image_index < len(self.parser.binary_images):
                    img = self.parser.binary_images[image_index]
                    offset = frame.get('imageOffset', 0)
                    actual_address = img.base + offset

                    if actual_address in symbolicated_frames:
                        symbol_info = symbolicated_frames[actual_address]

                        # 解析符号信息（格式: function_name (in binary) (file:line) 或 function_name (in binary) + offset）
                        match = re.match(r'(.*?)\s+\(in\s+.*?\)\s+(?:\((.*?):(\d+)\)|(?:\+\s*(\d+)))?', symbol_info)

                        if match:
                            frame['symbol'] = match.group(1)

                            if match.group(2):  # 有源文件信息
                                frame['sourceFile'] = match.group(2)
                                frame['sourceLine'] = int(match.group(3))
                            elif match.group(4):  # 有偏移
                                frame['symbolLocation'] = int(match.group(4))


def main():
    """测试用主函数"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python ips_parser.py <ips_file> [dsym_file]")
        sys.exit(1)

    ips_file = sys.argv[1]
    dsym_file = sys.argv[2] if len(sys.argv) > 2 else None

    # 解析IPS文件
    parser = IPSParser()
    if not parser.parse_file(ips_file):
        print("Failed to parse IPS file")
        sys.exit(1)

    # 打印基本信息
    info = parser.get_crash_info()
    print("=== Crash Info ===")
    for key, value in info.items():
        print(f"{key}: {value}")
    print()

    # 如果提供了dSYM，进行符号化
    if dsym_file:
        symbolicator = IPSSymbolicator(parser)
        if symbolicator.set_dsym(dsym_file):
            print("=== Symbolicated Report ===")
            print(symbolicator.symbolicate())
        else:
            print("Failed to load dSYM file")
    else:
        # 否则只输出转换后的格式
        print("=== Crash Report ===")
        print(parser.to_crash_format())


if __name__ == '__main__':
    main()