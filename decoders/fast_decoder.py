#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
快速Mars xlog解码器 - 使用多线程优化文件读取和解码
"""

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional, Tuple

from decode_mars_nocrypt_log_file_py3 import ParseFile


class FastXLogDecoder:
    """快速xlog解码器 - 使用多文件并行处理"""

    def __init__(self, max_workers=4):
        self.max_workers = max_workers

    def decode_single_file(self, filepath: str) -> Tuple[str, List[str], Optional[str]]:
        """解码单个文件"""
        try:
            # 验证文件格式
            if not filepath.lower().endswith('.xlog'):
                return (filepath, [], "不支持的文件格式，只能解析.xlog文件")

            output_file = filepath + ".log"

            # 使用原始解码器确保准确性
            ParseFile(filepath, output_file)

            # 读取解析结果
            results = []
            if os.path.exists(output_file):
                with open(output_file, 'r', encoding='utf-8', errors='ignore') as f:
                    results = f.readlines()

            return (filepath, results, None)
        except Exception as e:
            return (filepath, [], str(e))

    def decode_files_parallel(self, filepaths: List[str], progress_callback=None) -> dict:
        """并行解码多个文件"""
        results = {}
        total_files = len(filepaths)
        completed_files = 0

        # 使用线程池并行处理多个文件
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有文件解码任务
            futures = {executor.submit(self.decode_single_file, filepath): filepath
                      for filepath in filepaths}

            # 收集结果
            for future in as_completed(futures):
                filepath = futures[future]
                try:
                    file_path, decoded_lines, error = future.result(timeout=60)

                    if error:
                        results[file_path] = {'error': error, 'lines': []}
                    else:
                        results[file_path] = {'error': None, 'lines': decoded_lines}

                    completed_files += 1

                    # 更新进度
                    if progress_callback:
                        progress = (completed_files / total_files) * 100
                        progress_callback(progress, f"完成 {os.path.basename(file_path)}")

                except Exception as e:
                    results[filepath] = {'error': str(e), 'lines': []}
                    completed_files += 1

                    if progress_callback:
                        progress = (completed_files / total_files) * 100
                        progress_callback(progress, f"失败 {os.path.basename(filepath)}")

        return results

    def decode_files_batch(self, filepaths: List[str], progress_callback=None) -> dict:
        """批量解码文件 - 使用并行处理优化速度"""
        if len(filepaths) <= 2:
            # 文件较少时使用单线程
            results = {}
            for i, filepath in enumerate(filepaths):
                if progress_callback:
                    progress = (i / len(filepaths)) * 100
                    progress_callback(progress, f"正在解析 {os.path.basename(filepath)}")

                file_path, lines, error = self.decode_single_file(filepath)
                results[file_path] = {'error': error, 'lines': lines}

                if progress_callback:
                    progress = ((i + 1) / len(filepaths)) * 100
                    progress_callback(progress, f"完成 {os.path.basename(filepath)}")

            return results
        else:
            # 文件较多时使用并行处理
            return self.decode_files_parallel(filepaths, progress_callback)