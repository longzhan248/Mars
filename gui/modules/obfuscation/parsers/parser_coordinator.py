"""
代码解析器协调器 - 统一的解析接口
"""

from pathlib import Path
from typing import Callable, Dict, List, Optional

from .common import ParsedFile, Symbol, SymbolType
from .objc_parser import ObjCParser
from .swift_parser import SwiftParser


class CodeParser:
    """统一的代码解析器接口"""

    def __init__(self, whitelist_manager=None):
        """
        初始化代码解析器

        Args:
            whitelist_manager: 白名单管理器
        """
        self.objc_parser = ObjCParser(whitelist_manager)
        self.swift_parser = SwiftParser(whitelist_manager)

    def parse_file(self, file_path: str) -> ParsedFile:
        """
        解析代码文件（自动检测语言）

        Args:
            file_path: 文件路径

        Returns:
            ParsedFile: 解析结果
        """
        path = Path(file_path)

        if path.suffix in ['.h', '.m', '.mm']:
            return self.objc_parser.parse_file(file_path)
        elif path.suffix == '.swift':
            return self.swift_parser.parse_file(file_path)
        else:
            raise ValueError(f"不支持的文件类型: {path.suffix}")

    def parse_files(self, file_paths: List[str], callback: Optional[Callable] = None) -> Dict[str, ParsedFile]:
        """
        批量解析文件

        Args:
            file_paths: 文件路径列表
            callback: 进度回调 callback(progress, file_path)

        Returns:
            Dict[str, ParsedFile]: {文件路径: 解析结果}
        """
        results = {}
        total = len(file_paths)

        for i, file_path in enumerate(file_paths, 1):
            try:
                parsed = self.parse_file(file_path)
                results[file_path] = parsed

                if callback:
                    callback(i / total, file_path)

            except Exception as e:
                print(f"解析文件失败 {file_path}: {e}")
                continue

        return results

    def get_all_symbols(self, parsed_files: Dict[str, ParsedFile]) -> List[Symbol]:
        """获取所有符号"""
        all_symbols = []
        for parsed in parsed_files.values():
            all_symbols.extend(parsed.symbols)
        return all_symbols

    def get_symbols_by_type(self, parsed_files: Dict[str, ParsedFile],
                           symbol_type: SymbolType) -> List[Symbol]:
        """按类型获取符号"""
        symbols = []
        for parsed in parsed_files.values():
            symbols.extend([s for s in parsed.symbols if s.type == symbol_type])
        return symbols

    def group_symbols_by_type(self, symbols: List[Symbol]) -> Dict[SymbolType, List[Symbol]]:
        """按类型分组符号"""
        groups = {}
        for symbol in symbols:
            if symbol.type not in groups:
                groups[symbol.type] = []
            groups[symbol.type].append(symbol)
        return groups
