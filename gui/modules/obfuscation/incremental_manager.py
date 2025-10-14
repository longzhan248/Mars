"""
增量编译管理器 - 检测和管理文件变化，支持增量混淆

功能：
1. 文件变化检测（新增、修改、删除）
2. 文件缓存管理（哈希、元数据）
3. 解析结果缓存
4. 增量构建策略
"""

import os
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum


class FileChangeType(Enum):
    """文件变化类型"""
    ADDED = "added"           # 新增文件
    MODIFIED = "modified"     # 修改文件
    DELETED = "deleted"       # 删除文件
    UNCHANGED = "unchanged"   # 未变化


@dataclass
class FileMetadata:
    """文件元数据"""
    path: str                           # 文件路径
    md5_hash: str                       # MD5哈希
    modified_time: float                # 修改时间戳
    size: int                           # 文件大小
    last_checked: str                   # 上次检查时间
    change_type: FileChangeType = FileChangeType.UNCHANGED

    def to_dict(self):
        """转换为字典"""
        d = asdict(self)
        d['change_type'] = self.change_type.value
        return d

    @staticmethod
    def from_dict(d: dict) -> 'FileMetadata':
        """从字典创建"""
        d['change_type'] = FileChangeType(d['change_type'])
        return FileMetadata(**d)


@dataclass
class IncrementalCache:
    """增量编译缓存"""
    project_path: str                                   # 项目路径
    last_build_time: str                                # 上次构建时间
    file_metadata: Dict[str, FileMetadata] = field(default_factory=dict)
    total_files: int = 0
    cache_version: str = "1.0"

    def to_dict(self):
        """转换为字典"""
        return {
            'project_path': self.project_path,
            'last_build_time': self.last_build_time,
            'file_metadata': {k: v.to_dict() for k, v in self.file_metadata.items()},
            'total_files': self.total_files,
            'cache_version': self.cache_version
        }

    @staticmethod
    def from_dict(d: dict) -> 'IncrementalCache':
        """从字典创建"""
        cache = IncrementalCache(
            project_path=d['project_path'],
            last_build_time=d['last_build_time'],
            total_files=d['total_files'],
            cache_version=d.get('cache_version', '1.0')
        )
        cache.file_metadata = {
            k: FileMetadata.from_dict(v)
            for k, v in d['file_metadata'].items()
        }
        return cache


class IncrementalManager:
    """增量编译管理器"""

    CACHE_FILENAME = ".obfuscation_cache.json"

    def __init__(self, project_path: str):
        """
        初始化增量编译管理器

        Args:
            project_path: 项目根目录路径
        """
        self.project_path = Path(project_path).resolve()
        self.cache_file = self.project_path / self.CACHE_FILENAME
        self.cache: Optional[IncrementalCache] = None

    def load_cache(self) -> bool:
        """
        加载缓存文件

        Returns:
            bool: 是否成功加载
        """
        if not self.cache_file.exists():
            return False

        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.cache = IncrementalCache.from_dict(data)
                return True
        except Exception as e:
            print(f"加载缓存失败: {e}")
            return False

    def save_cache(self) -> bool:
        """
        保存缓存文件

        Returns:
            bool: 是否成功保存
        """
        if not self.cache:
            return False

        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache.to_dict(), f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存缓存失败: {e}")
            return False

    def compute_file_hash(self, file_path: str) -> str:
        """
        计算文件MD5哈希

        Args:
            file_path: 文件路径

        Returns:
            str: MD5哈希值
        """
        md5 = hashlib.md5()
        try:
            with open(file_path, 'rb') as f:
                # 分块读取，避免大文件内存占用
                for chunk in iter(lambda: f.read(8192), b''):
                    md5.update(chunk)
            return md5.hexdigest()
        except Exception as e:
            print(f"计算文件哈希失败 {file_path}: {e}")
            return ""

    def get_file_metadata(self, file_path: str) -> Optional[FileMetadata]:
        """
        获取文件元数据

        Args:
            file_path: 文件路径

        Returns:
            FileMetadata: 文件元数据，如果文件不存在则返回None
        """
        path = Path(file_path)
        if not path.exists():
            return None

        try:
            stat = path.stat()
            return FileMetadata(
                path=str(path),
                md5_hash=self.compute_file_hash(str(path)),
                modified_time=stat.st_mtime,
                size=stat.st_size,
                last_checked=datetime.now().isoformat()
            )
        except Exception as e:
            print(f"获取文件元数据失败 {file_path}: {e}")
            return None

    def detect_changes(self, current_files: List[str]) -> Dict[FileChangeType, List[str]]:
        """
        检测文件变化

        Args:
            current_files: 当前项目中的所有源文件路径列表

        Returns:
            Dict[FileChangeType, List[str]]: 按变化类型分组的文件列表
        """
        changes = {
            FileChangeType.ADDED: [],
            FileChangeType.MODIFIED: [],
            FileChangeType.DELETED: [],
            FileChangeType.UNCHANGED: []
        }

        # 如果没有缓存，所有文件都是新增的
        if not self.cache:
            changes[FileChangeType.ADDED] = current_files
            return changes

        current_set = set(current_files)
        cached_set = set(self.cache.file_metadata.keys())

        # 1. 检测新增文件
        added_files = current_set - cached_set
        changes[FileChangeType.ADDED].extend(added_files)

        # 2. 检测删除文件
        deleted_files = cached_set - current_set
        changes[FileChangeType.DELETED].extend(deleted_files)

        # 3. 检测修改文件
        common_files = current_set & cached_set
        for file_path in common_files:
            current_metadata = self.get_file_metadata(file_path)
            if not current_metadata:
                continue

            cached_metadata = self.cache.file_metadata[file_path]

            # 比较哈希值判断是否修改
            if current_metadata.md5_hash != cached_metadata.md5_hash:
                changes[FileChangeType.MODIFIED].append(file_path)
            else:
                changes[FileChangeType.UNCHANGED].append(file_path)

        return changes

    def update_cache(self, files_to_update: List[str]) -> None:
        """
        更新缓存中的文件信息

        Args:
            files_to_update: 需要更新的文件路径列表
        """
        if not self.cache:
            self.cache = IncrementalCache(
                project_path=str(self.project_path),
                last_build_time=datetime.now().isoformat()
            )

        for file_path in files_to_update:
            metadata = self.get_file_metadata(file_path)
            if metadata:
                self.cache.file_metadata[file_path] = metadata

        # 更新总文件数和构建时间
        self.cache.total_files = len(self.cache.file_metadata)
        self.cache.last_build_time = datetime.now().isoformat()

    def remove_deleted_files(self, deleted_files: List[str]) -> None:
        """
        从缓存中移除已删除的文件

        Args:
            deleted_files: 已删除的文件路径列表
        """
        if not self.cache:
            return

        for file_path in deleted_files:
            if file_path in self.cache.file_metadata:
                del self.cache.file_metadata[file_path]

        self.cache.total_files = len(self.cache.file_metadata)

    def should_rebuild_all(self, force: bool = False) -> bool:
        """
        判断是否需要完整重新构建

        Args:
            force: 是否强制重新构建

        Returns:
            bool: 是否需要完整构建
        """
        if force:
            return True

        if not self.cache:
            return True

        # 检查缓存版本
        if self.cache.cache_version != "1.0":
            print("缓存版本不匹配，执行完整构建")
            return True

        return False

    def get_files_to_process(self, all_files: List[str], force: bool = False) -> Tuple[List[str], Dict[FileChangeType, List[str]]]:
        """
        获取需要处理的文件列表

        Args:
            all_files: 项目中的所有源文件
            force: 是否强制重新处理所有文件

        Returns:
            Tuple[List[str], Dict]: (需要处理的文件列表, 变化详情)
        """
        # 加载缓存
        if not force:
            self.load_cache()

        # 判断是否需要完整构建
        if self.should_rebuild_all(force):
            changes = {
                FileChangeType.ADDED: all_files,
                FileChangeType.MODIFIED: [],
                FileChangeType.DELETED: [],
                FileChangeType.UNCHANGED: []
            }
            return all_files, changes

        # 增量构建：检测变化
        changes = self.detect_changes(all_files)

        # 需要处理的文件 = 新增 + 修改
        files_to_process = (
            changes[FileChangeType.ADDED] +
            changes[FileChangeType.MODIFIED]
        )

        return files_to_process, changes

    def finalize(self, processed_files: List[str], deleted_files: List[str] = None) -> bool:
        """
        完成增量构建，更新缓存

        Args:
            processed_files: 已处理的文件列表
            deleted_files: 已删除的文件列表

        Returns:
            bool: 是否成功保存缓存
        """
        # 更新已处理文件的缓存
        self.update_cache(processed_files)

        # 移除已删除的文件
        if deleted_files:
            self.remove_deleted_files(deleted_files)

        # 保存缓存
        return self.save_cache()

    def clear_cache(self) -> bool:
        """
        清除缓存文件

        Returns:
            bool: 是否成功清除
        """
        try:
            if self.cache_file.exists():
                self.cache_file.unlink()
            self.cache = None
            return True
        except Exception as e:
            print(f"清除缓存失败: {e}")
            return False

    def get_statistics(self) -> Dict:
        """
        获取缓存统计信息

        Returns:
            Dict: 统计信息
        """
        if not self.cache:
            return {
                'has_cache': False,
                'total_files': 0,
                'last_build_time': None
            }

        return {
            'has_cache': True,
            'total_files': self.cache.total_files,
            'last_build_time': self.cache.last_build_time,
            'cache_version': self.cache.cache_version
        }


if __name__ == "__main__":
    # 测试代码
    print("=== 增量编译管理器测试 ===\n")

    import tempfile
    import time

    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建测试项目
        project_path = Path(tmpdir) / "TestProject"
        project_path.mkdir()

        # 创建测试文件
        file1 = project_path / "File1.swift"
        file2 = project_path / "File2.swift"
        file3 = project_path / "File3.swift"

        file1.write_text("class MyClass {}")
        file2.write_text("struct MyStruct {}")

        all_files = [str(file1), str(file2)]

        # 1. 首次构建（无缓存）
        print("1. 首次构建测试:")
        manager = IncrementalManager(str(project_path))
        files_to_process, changes = manager.get_files_to_process(all_files)

        print(f"  需要处理: {len(files_to_process)} 个文件")
        print(f"  新增: {len(changes[FileChangeType.ADDED])} 个")
        assert len(files_to_process) == 2, "首次构建应该处理所有文件"

        # 完成构建并保存缓存
        manager.finalize(files_to_process)
        print("  ✅ 缓存已保存")

        # 2. 无变化的增量构建
        print("\n2. 无变化增量构建测试:")
        manager2 = IncrementalManager(str(project_path))
        files_to_process, changes = manager2.get_files_to_process(all_files)

        print(f"  需要处理: {len(files_to_process)} 个文件")
        print(f"  未变化: {len(changes[FileChangeType.UNCHANGED])} 个")
        assert len(files_to_process) == 0, "无变化时不应处理任何文件"
        print("  ✅ 正确跳过未变化文件")

        # 3. 修改文件
        print("\n3. 文件修改检测测试:")
        time.sleep(0.01)  # 确保修改时间不同
        file1.write_text("class MyClass { func newMethod() {} }")

        manager3 = IncrementalManager(str(project_path))
        files_to_process, changes = manager3.get_files_to_process(all_files)

        print(f"  需要处理: {len(files_to_process)} 个文件")
        print(f"  修改: {len(changes[FileChangeType.MODIFIED])} 个")
        print(f"  未变化: {len(changes[FileChangeType.UNCHANGED])} 个")
        assert len(files_to_process) == 1, "应该只处理修改的文件"
        assert str(file1) in files_to_process, "File1应该被标记为修改"
        print("  ✅ 正确检测文件修改")

        # 4. 新增文件
        print("\n4. 新增文件检测测试:")
        file3.write_text("enum MyEnum {}")
        all_files_with_new = all_files + [str(file3)]

        manager4 = IncrementalManager(str(project_path))
        files_to_process, changes = manager4.get_files_to_process(all_files_with_new)

        print(f"  需要处理: {len(files_to_process)} 个文件")
        print(f"  新增: {len(changes[FileChangeType.ADDED])} 个")
        assert str(file3) in changes[FileChangeType.ADDED], "File3应该被检测为新增"
        print("  ✅ 正确检测新增文件")

        # 5. 删除文件
        print("\n5. 删除文件检测测试:")
        all_files_after_delete = [str(file1)]

        manager5 = IncrementalManager(str(project_path))
        files_to_process, changes = manager5.get_files_to_process(all_files_after_delete)

        print(f"  删除: {len(changes[FileChangeType.DELETED])} 个")
        assert len(changes[FileChangeType.DELETED]) >= 1, "应该检测到删除的文件"
        print("  ✅ 正确检测删除文件")

        # 6. 统计信息
        print("\n6. 缓存统计信息:")
        stats = manager5.get_statistics()
        print(f"  总文件数: {stats['total_files']}")
        print(f"  上次构建: {stats['last_build_time']}")
        print(f"  缓存版本: {stats['cache_version']}")

    print("\n=== 测试完成 ===")
