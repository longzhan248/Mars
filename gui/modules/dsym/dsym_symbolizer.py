#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dSYM符号化模块
负责使用atos工具进行崩溃地址符号化
"""

import os
import plistlib
import subprocess
import tempfile


class DSYMSymbolizer:
    """dSYM符号化器"""

    def __init__(self):
        """初始化符号化器"""

    def symbolicate_address(self, dsym_path, arch, slide_address, error_address):
        """符号化崩溃地址

        Args:
            dsym_path: dSYM文件路径
            arch: 架构名称（如 arm64, armv7）
            slide_address: Slide Address（基址）
            error_address: 错误内存地址

        Returns:
            dict: 符号化结果 {
                'success': bool,
                'output': str,
                'command': str,
                'error': str (可选)
            }
        """
        # 构建atos命令
        cmd = [
            'xcrun', 'atos',
            '-arch', arch,
            '-o', dsym_path,
            '-l', slide_address,
            error_address
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            output = result.stdout if result.stdout else result.stderr
            command_str = ' '.join(cmd)

            return {
                'success': result.returncode == 0 and bool(output),
                'output': output.strip(),
                'command': command_str,
                'error': result.stderr if result.returncode != 0 else None
            }

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'output': '',
                'command': ' '.join(cmd),
                'error': 'atos命令超时'
            }
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'command': ' '.join(cmd),
                'error': str(e)
            }

    def symbolicate_multiple_addresses(self, dsym_path, arch, slide_address, addresses):
        """批量符号化多个地址

        Args:
            dsym_path: dSYM文件路径
            arch: 架构名称
            slide_address: Slide Address
            addresses: 地址列表

        Returns:
            list: 符号化结果列表
        """
        results = []
        for address in addresses:
            result = self.symbolicate_address(dsym_path, arch, slide_address, address)
            result['address'] = address
            results.append(result)

        return results

    def format_symbolication_result(self, arch, uuid, slide_address, error_address, output, command):
        """格式化符号化结果为可读文本

        Args:
            arch: 架构名称
            uuid: UUID
            slide_address: Slide Address
            error_address: 错误地址
            output: atos输出
            command: 执行的命令

        Returns:
            str: 格式化后的结果文本
        """
        lines = [
            "分析结果:",
            "=" * 80,
            f"架构: {arch}",
            f"UUID: {uuid}",
            f"基址: {slide_address}",
            f"错误地址: {error_address}",
            "=" * 80,
            "",
            "符号化结果:",
            output,
            "",
            f"命令: {command}"
        ]

        return '\n'.join(lines)

    def validate_address(self, address):
        """验证内存地址格式

        Args:
            address: 内存地址字符串

        Returns:
            bool: 是否为有效格式
        """
        # 支持 0x 开头的十六进制地址
        if not address.startswith('0x'):
            return False

        try:
            int(address, 16)
            return True
        except ValueError:
            return False

    def check_atos_available(self):
        """检查atos工具是否可用

        Returns:
            bool: 是否可用
        """
        try:
            result = subprocess.run(
                ['xcrun', 'atos', '-h'],
                capture_output=True,
                text=True
            )
            return result.returncode == 0 or result.returncode == 1  # atos -h 返回1但输出帮助
        except Exception:
            return False

    def export_ipa(self, xcarchive_path, output_dir):
        """从xcarchive导出IPA文件

        Args:
            xcarchive_path: xcarchive文件路径
            output_dir: 输出目录

        Returns:
            dict: 导出结果 {
                'success': bool,
                'output_path': str (成功时),
                'error': str (失败时)
            }
        """
        try:
            # 创建导出选项plist
            export_options_path = self._create_export_options()

            # 执行导出命令
            cmd = [
                '/usr/bin/xcodebuild',
                '-exportArchive',
                '-archivePath', xcarchive_path,
                '-exportPath', output_dir,
                '-exportOptionsPlist', export_options_path
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )

            # 清理临时文件
            os.remove(export_options_path)

            if result.returncode == 0:
                # 查找生成的IPA文件
                ipa_files = [f for f in os.listdir(output_dir) if f.endswith('.ipa')]
                if ipa_files:
                    ipa_path = os.path.join(output_dir, ipa_files[0])
                    return {
                        'success': True,
                        'output_path': ipa_path
                    }

            return {
                'success': False,
                'error': result.stderr or 'IPA导出失败'
            }

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': '导出超时（超过5分钟）'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _create_export_options(self):
        """创建导出选项plist文件

        Returns:
            str: plist文件路径
        """
        options = {
            'method': 'development',  # 或 'app-store', 'ad-hoc', 'enterprise'
            'teamID': '',  # 可选
            'compileBitcode': False,
            'uploadBitcode': False,
            'uploadSymbols': False
        }

        fd, path = tempfile.mkstemp(suffix='.plist')
        with open(path, 'wb') as f:
            plistlib.dump(options, f)
        os.close(fd)

        return path
