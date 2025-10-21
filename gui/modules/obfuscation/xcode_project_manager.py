"""
Xcode项目管理器
用于自动修改.xcodeproj文件，将混淆生成的文件添加到项目中
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    from pbxproj import XcodeProject
    PBXPROJ_AVAILABLE = True
except ImportError:
    PBXPROJ_AVAILABLE = False
    print("警告: mod-pbxproj 库未安装，Xcode项目自动修改功能将不可用")
    print("安装方法: pip install pbxproj")


@dataclass
class FileAddResult:
    """文件添加结果"""
    file_path: str
    success: bool
    error: Optional[str] = None
    target_name: Optional[str] = None


class XcodeProjectManager:
    """
    Xcode项目管理器

    功能:
    1. 自动查找.xcodeproj文件
    2. 添加文件到项目和指定target
    3. 创建分组（group）组织文件
    4. 批量添加多个文件
    """

    def __init__(self, project_path: str):
        """
        初始化Xcode项目管理器

        Args:
            project_path: 项目路径，可以是:
                - .xcodeproj 文件路径
                - 包含.xcodeproj的项目根目录
                - project.pbxproj 文件路径
        """
        self.project_path = Path(project_path)
        self.pbxproj_path: Optional[Path] = None
        self.project: Optional[XcodeProject] = None
        self.is_loaded = False

        # 查找项目文件
        self._find_project_file()

    def _find_project_file(self) -> bool:
        """
        查找.xcodeproj中的project.pbxproj文件

        Returns:
            bool: 是否找到项目文件
        """
        # 情况1: 直接传入project.pbxproj路径
        if self.project_path.name == 'project.pbxproj' and self.project_path.exists():
            self.pbxproj_path = self.project_path
            return True

        # 情况2: 传入.xcodeproj路径
        if self.project_path.suffix == '.xcodeproj' and self.project_path.exists():
            pbxproj = self.project_path / 'project.pbxproj'
            if pbxproj.exists():
                self.pbxproj_path = pbxproj
                return True

        # 情况3: 传入项目根目录，查找第一个.xcodeproj
        if self.project_path.is_dir():
            for item in self.project_path.iterdir():
                if item.suffix == '.xcodeproj' and item.is_dir():
                    pbxproj = item / 'project.pbxproj'
                    if pbxproj.exists():
                        self.pbxproj_path = pbxproj
                        return True

        return False

    def load_project(self) -> bool:
        """
        加载Xcode项目

        Returns:
            bool: 是否加载成功
        """
        if not PBXPROJ_AVAILABLE:
            print("❌ mod-pbxproj 库未安装")
            return False

        if not self.pbxproj_path:
            print(f"❌ 未找到项目文件: {self.project_path}")
            return False

        try:
            self.project = XcodeProject.load(str(self.pbxproj_path))
            self.is_loaded = True
            print(f"✅ 成功加载项目: {self.pbxproj_path.parent.name}")
            return True
        except Exception as e:
            print(f"❌ 加载项目失败: {e}")
            return False

    def save_project(self) -> bool:
        """
        保存项目修改

        Returns:
            bool: 是否保存成功
        """
        if not self.is_loaded or not self.project:
            print("❌ 项目未加载")
            return False

        try:
            self.project.save()
            print(f"✅ 项目已保存: {self.pbxproj_path.parent.name}")
            return True
        except Exception as e:
            print(f"❌ 保存项目失败: {e}")
            return False

    def get_targets(self) -> List[str]:
        """
        获取项目中所有target名称

        Returns:
            List[str]: target名称列表
        """
        if not self.is_loaded or not self.project:
            return []

        try:
            # 获取所有native targets
            targets = []
            for target in self.project.objects.get_targets():
                if hasattr(target, 'name'):
                    targets.append(target.name)
            return targets
        except Exception as e:
            print(f"❌ 获取targets失败: {e}")
            return []

    def get_or_create_group(self, group_name: str, parent: Optional[str] = None) -> Optional[object]:
        """
        获取或创建分组

        Args:
            group_name: 分组名称
            parent: 父分组名称，None表示根分组

        Returns:
            分组对象，失败返回None
        """
        if not self.is_loaded or not self.project:
            return None

        try:
            # 如果指定了父分组，先获取父分组
            if parent:
                parent_group = self.project.get_or_create_group(parent)
                return self.project.get_or_create_group(group_name, parent=parent_group)
            else:
                return self.project.get_or_create_group(group_name)
        except Exception as e:
            print(f"❌ 获取/创建分组失败: {e}")
            return None

    def add_file_to_project(
        self,
        file_path: str,
        group_name: Optional[str] = None,
        target_name: Optional[str] = None,
        force: bool = False
    ) -> FileAddResult:
        """
        添加文件到项目

        Args:
            file_path: 文件路径（相对于项目根目录或绝对路径）
            group_name: 分组名称，None表示添加到根目录
            target_name: target名称，None表示添加到所有targets
            force: 是否强制添加（即使文件已存在）

        Returns:
            FileAddResult: 添加结果
        """
        if not self.is_loaded or not self.project:
            return FileAddResult(
                file_path=file_path,
                success=False,
                error="项目未加载"
            )

        try:
            # 获取或创建分组
            parent_group = None
            if group_name:
                parent_group = self.get_or_create_group(group_name)
                if not parent_group:
                    return FileAddResult(
                        file_path=file_path,
                        success=False,
                        error=f"无法创建分组: {group_name}"
                    )

            # 添加文件
            # 注意: pbxproj库期望相对于项目根目录的路径
            file_path_obj = Path(file_path)
            if file_path_obj.is_absolute():
                # 如果是绝对路径，尝试转换为相对路径
                project_root = self.pbxproj_path.parent.parent
                try:
                    relative_path = file_path_obj.relative_to(project_root)
                    file_path = str(relative_path)
                except ValueError:
                    # 无法转换为相对路径，使用绝对路径
                    pass

            # 添加文件到项目
            self.project.add_file(
                file_path,
                parent=parent_group,
                target_name=target_name,
                force=force
            )

            return FileAddResult(
                file_path=file_path,
                success=True,
                target_name=target_name
            )

        except Exception as e:
            return FileAddResult(
                file_path=file_path,
                success=False,
                error=str(e),
                target_name=target_name
            )

    def add_files_batch(
        self,
        file_paths: List[str],
        group_name: Optional[str] = None,
        target_name: Optional[str] = None,
        force: bool = False
    ) -> List[FileAddResult]:
        """
        批量添加文件到项目

        Args:
            file_paths: 文件路径列表
            group_name: 分组名称
            target_name: target名称
            force: 是否强制添加

        Returns:
            List[FileAddResult]: 添加结果列表
        """
        results = []

        for file_path in file_paths:
            result = self.add_file_to_project(
                file_path=file_path,
                group_name=group_name,
                target_name=target_name,
                force=force
            )
            results.append(result)

        return results

    def add_obfuscation_files(
        self,
        garbage_files: Dict[str, List[str]],
        decryption_files: List[str],
        target_name: Optional[str] = None
    ) -> Tuple[List[FileAddResult], List[FileAddResult]]:
        """
        添加混淆生成的文件到项目

        Args:
            garbage_files: 垃圾文件字典 {'objc': [...], 'swift': [...]}
            decryption_files: 解密文件列表 ['StringDecryption.h', 'StringDecryption.swift']
            target_name: target名称

        Returns:
            Tuple[List[FileAddResult], List[FileAddResult]]:
                (垃圾文件添加结果, 解密文件添加结果)
        """
        garbage_results = []
        decryption_results = []

        # 1. 添加垃圾代码文件
        if garbage_files:
            # 创建垃圾代码分组
            objc_group = "Obfuscation/GarbageCode/ObjC"
            swift_group = "Obfuscation/GarbageCode/Swift"

            # 添加ObjC垃圾文件
            if garbage_files.get('objc'):
                print(f"📁 添加 {len(garbage_files['objc'])} 个 ObjC 垃圾文件...")
                objc_results = self.add_files_batch(
                    file_paths=garbage_files['objc'],
                    group_name=objc_group,
                    target_name=target_name,
                    force=False
                )
                garbage_results.extend(objc_results)

            # 添加Swift垃圾文件
            if garbage_files.get('swift'):
                print(f"📁 添加 {len(garbage_files['swift'])} 个 Swift 垃圾文件...")
                swift_results = self.add_files_batch(
                    file_paths=garbage_files['swift'],
                    group_name=swift_group,
                    target_name=target_name,
                    force=False
                )
                garbage_results.extend(swift_results)

        # 2. 添加解密文件
        if decryption_files:
            print(f"📁 添加 {len(decryption_files)} 个解密文件...")
            decryption_group = "Obfuscation/StringDecryption"

            decryption_results = self.add_files_batch(
                file_paths=decryption_files,
                group_name=decryption_group,
                target_name=target_name,
                force=False
            )

        return garbage_results, decryption_results

    def print_summary(
        self,
        garbage_results: List[FileAddResult],
        decryption_results: List[FileAddResult]
    ):
        """
        打印添加结果摘要

        Args:
            garbage_results: 垃圾文件添加结果
            decryption_results: 解密文件添加结果
        """
        total_files = len(garbage_results) + len(decryption_results)
        success_count = sum(1 for r in garbage_results + decryption_results if r.success)
        fail_count = total_files - success_count

        print("\n" + "=" * 60)
        print("📊 Xcode项目文件添加摘要")
        print("=" * 60)
        print(f"  总文件数: {total_files}")
        print(f"  成功: {success_count} ✅")
        print(f"  失败: {fail_count} ❌")

        if fail_count > 0:
            print("\n失败文件列表:")
            for result in garbage_results + decryption_results:
                if not result.success:
                    print(f"  ❌ {result.file_path}")
                    if result.error:
                        print(f"     错误: {result.error}")

        print("=" * 60 + "\n")


def check_pbxproj_availability() -> bool:
    """
    检查mod-pbxproj库是否可用

    Returns:
        bool: 是否可用
    """
    return PBXPROJ_AVAILABLE


def install_pbxproj_hint():
    """打印安装mod-pbxproj的提示"""
    print("\n" + "=" * 60)
    print("📦 mod-pbxproj 库未安装")
    print("=" * 60)
    print("该功能需要 mod-pbxproj 库来修改 Xcode 项目文件")
    print("\n安装方法:")
    print("  pip install pbxproj")
    print("\n或者在虚拟环境中安装:")
    print("  source venv/bin/activate")
    print("  pip install pbxproj")
    print("=" * 60 + "\n")
