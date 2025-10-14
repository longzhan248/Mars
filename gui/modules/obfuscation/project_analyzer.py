"""
项目分析器 - 负责扫描iOS项目结构并收集符号信息

支持:
1. 项目结构分析（Xcode项目、CocoaPods等）
2. 源文件收集（.h、.m、.swift）
3. 资源文件收集（.xib、.storyboard、Assets.xcassets等）
4. 依赖关系分析
5. 符号提取（类、方法、属性等）
6. 项目统计信息
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import plistlib


class ProjectType(Enum):
    """项目类型"""
    XCODE = "xcode"                 # Xcode项目
    COCOAPODS = "cocoapods"         # CocoaPods项目
    SPM = "spm"                     # Swift Package Manager
    CARTHAGE = "carthage"           # Carthage
    MIXED = "mixed"                 # 混合项目


class FileType(Enum):
    """文件类型"""
    OBJC_HEADER = ".h"             # Objective-C头文件
    OBJC_SOURCE = ".m"             # Objective-C源文件
    OBJC_MM = ".mm"                # Objective-C++ 源文件
    SWIFT = ".swift"               # Swift源文件
    XIB = ".xib"                   # XIB界面文件
    STORYBOARD = ".storyboard"     # Storyboard界面文件
    XCASSETS = ".xcassets"         # 资源目录
    PLIST = ".plist"               # 属性列表文件
    STRINGS = ".strings"           # 本地化字符串文件


@dataclass
class SourceFile:
    """源文件信息"""
    path: str                       # 文件路径
    filename: str                   # 文件名
    filetype: FileType              # 文件类型
    size: int                       # 文件大小（字节）
    lines: int = 0                  # 代码行数
    encoding: str = "utf-8"         # 文件编码
    is_third_party: bool = False    # 是否第三方库
    relative_path: str = ""         # 相对项目的路径


@dataclass
class ProjectStructure:
    """项目结构信息"""
    root_path: str                          # 项目根路径
    project_name: str                       # 项目名称
    project_type: ProjectType               # 项目类型

    # 源文件
    objc_headers: List[SourceFile] = field(default_factory=list)
    objc_sources: List[SourceFile] = field(default_factory=list)
    swift_files: List[SourceFile] = field(default_factory=list)

    # 资源文件
    xibs: List[SourceFile] = field(default_factory=list)
    storyboards: List[SourceFile] = field(default_factory=list)
    assets: List[str] = field(default_factory=list)
    plists: List[SourceFile] = field(default_factory=list)

    # 项目配置
    xcodeproj_path: Optional[str] = None    # .xcodeproj路径
    xcworkspace_path: Optional[str] = None  # .xcworkspace路径
    podfile_path: Optional[str] = None      # Podfile路径
    package_swift_path: Optional[str] = None # Package.swift路径

    # 依赖信息
    cocoapods_dependencies: Set[str] = field(default_factory=set)
    spm_dependencies: Set[str] = field(default_factory=set)
    carthage_dependencies: Set[str] = field(default_factory=set)

    # 统计信息
    total_files: int = 0
    total_lines: int = 0
    objc_percentage: float = 0.0
    swift_percentage: float = 0.0


class ProjectAnalyzer:
    """项目分析器"""

    # 需要排除的目录
    EXCLUDE_DIRS = {
        'Pods',
        'Carthage',
        'Build',
        'DerivedData',
        '.git',
        '.svn',
        'node_modules',
        'build',
        '.build',
        'xcuserdata',
        'xcshareddata',
    }

    # 第三方库特征目录
    THIRD_PARTY_INDICATORS = {
        'Pods/',
        'Carthage/',
        'ThirdParty/',
        'Vendor/',
        'External/',
        'Libraries/',
        '.framework/',
        '.bundle/',
    }

    def __init__(self, project_path: str):
        """
        初始化项目分析器

        Args:
            project_path: 项目根路径
        """
        self.project_path = Path(project_path)

        if not self.project_path.exists():
            raise FileNotFoundError(f"项目路径不存在: {project_path}")

        if not self.project_path.is_dir():
            raise ValueError(f"项目路径不是目录: {project_path}")

        self.structure = ProjectStructure(
            root_path=str(self.project_path),
            project_name=self.project_path.name,
            project_type=self._detect_project_type()
        )

    def _detect_project_type(self) -> ProjectType:
        """检测项目类型"""
        has_xcodeproj = any(self.project_path.glob("*.xcodeproj"))
        has_xcworkspace = any(self.project_path.glob("*.xcworkspace"))
        has_podfile = (self.project_path / "Podfile").exists()
        has_package_swift = (self.project_path / "Package.swift").exists()
        has_cartfile = (self.project_path / "Cartfile").exists()

        types = []
        if has_xcodeproj or has_xcworkspace:
            types.append(ProjectType.XCODE)
        if has_podfile:
            types.append(ProjectType.COCOAPODS)
        if has_package_swift:
            types.append(ProjectType.SPM)
        if has_cartfile:
            types.append(ProjectType.CARTHAGE)

        if len(types) == 0:
            return ProjectType.XCODE  # 默认
        elif len(types) == 1:
            return types[0]
        else:
            return ProjectType.MIXED

    def analyze(self, callback=None) -> ProjectStructure:
        """
        分析项目结构

        Args:
            callback: 进度回调函数 callback(progress, message)

        Returns:
            ProjectStructure: 项目结构信息
        """
        total_steps = 6
        current_step = 0

        def report_progress(message):
            nonlocal current_step
            current_step += 1
            if callback:
                callback(current_step / total_steps, message)

        # 1. 查找项目配置文件
        report_progress("查找项目配置文件...")
        self._find_project_configs()

        # 2. 扫描源文件
        report_progress("扫描源代码文件...")
        self._scan_source_files()

        # 3. 扫描资源文件
        report_progress("扫描资源文件...")
        self._scan_resource_files()

        # 4. 分析依赖关系
        report_progress("分析项目依赖...")
        self._analyze_dependencies()

        # 5. 计算统计信息
        report_progress("计算统计信息...")
        self._calculate_statistics()

        # 6. 完成
        report_progress("分析完成")

        return self.structure

    def _find_project_configs(self):
        """查找项目配置文件"""
        # 查找 .xcodeproj
        xcodeprojs = list(self.project_path.glob("*.xcodeproj"))
        if xcodeprojs:
            self.structure.xcodeproj_path = str(xcodeprojs[0])

        # 查找 .xcworkspace
        xcworkspaces = list(self.project_path.glob("*.xcworkspace"))
        if xcworkspaces:
            self.structure.xcworkspace_path = str(xcworkspaces[0])

        # 查找 Podfile
        podfile = self.project_path / "Podfile"
        if podfile.exists():
            self.structure.podfile_path = str(podfile)

        # 查找 Package.swift
        package_swift = self.project_path / "Package.swift"
        if package_swift.exists():
            self.structure.package_swift_path = str(package_swift)

    def _scan_source_files(self):
        """扫描源代码文件"""
        for file_path in self._walk_directory(self.project_path):
            # 判断是否是第三方库文件
            is_third_party = self._is_third_party_file(file_path)
            relative_path = str(file_path.relative_to(self.project_path))

            # 获取文件信息
            try:
                file_size = file_path.stat().st_size

                # 创建SourceFile对象
                source_file = SourceFile(
                    path=str(file_path),
                    filename=file_path.name,
                    filetype=self._get_file_type(file_path),
                    size=file_size,
                    is_third_party=is_third_party,
                    relative_path=relative_path
                )

                # 计算代码行数（仅非第三方库）
                if not is_third_party:
                    source_file.lines = self._count_lines(file_path)

                # 分类存储
                if file_path.suffix == '.h':
                    self.structure.objc_headers.append(source_file)
                elif file_path.suffix in ['.m', '.mm']:
                    self.structure.objc_sources.append(source_file)
                elif file_path.suffix == '.swift':
                    self.structure.swift_files.append(source_file)

            except Exception as e:
                print(f"处理文件失败 {file_path}: {e}")
                continue

    def _scan_resource_files(self):
        """扫描资源文件"""
        for file_path in self._walk_directory(self.project_path):
            is_third_party = self._is_third_party_file(file_path)
            relative_path = str(file_path.relative_to(self.project_path))

            try:
                file_size = file_path.stat().st_size

                source_file = SourceFile(
                    path=str(file_path),
                    filename=file_path.name,
                    filetype=self._get_file_type(file_path),
                    size=file_size,
                    is_third_party=is_third_party,
                    relative_path=relative_path
                )

                if file_path.suffix == '.xib':
                    self.structure.xibs.append(source_file)
                elif file_path.suffix == '.storyboard':
                    self.structure.storyboards.append(source_file)
                elif file_path.suffix == '.plist':
                    self.structure.plists.append(source_file)
                elif file_path.name.endswith('.xcassets'):
                    self.structure.assets.append(str(file_path))

            except Exception:
                continue

    def _analyze_dependencies(self):
        """分析项目依赖"""
        # 分析CocoaPods依赖
        if self.structure.podfile_path:
            self._analyze_cocoapods()

        # 分析SPM依赖
        if self.structure.package_swift_path:
            self._analyze_spm()

        # 分析Carthage依赖
        cartfile = self.project_path / "Cartfile.resolved"
        if cartfile.exists():
            self._analyze_carthage()

    def _analyze_cocoapods(self):
        """分析CocoaPods依赖"""
        podfile_lock = self.project_path / "Podfile.lock"
        if not podfile_lock.exists():
            return

        try:
            with open(podfile_lock, 'r', encoding='utf-8') as f:
                content = f.read()

            # 解析PODS段落
            pods_section = re.search(r'PODS:\n(.*?)(?:\n\n|\Z)', content, re.DOTALL)
            if pods_section:
                pod_lines = pods_section.group(1).split('\n')
                for line in pod_lines:
                    match = re.match(r'\s*-\s+([^/\s(]+)', line)
                    if match:
                        self.structure.cocoapods_dependencies.add(match.group(1))

        except Exception as e:
            print(f"分析CocoaPods失败: {e}")

    def _analyze_spm(self):
        """分析SPM依赖"""
        package_resolved = self.project_path / "Package.resolved"
        if not package_resolved.exists():
            return

        try:
            with open(package_resolved, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for pin in data.get('object', {}).get('pins', []):
                package = pin.get('package')
                if package:
                    self.structure.spm_dependencies.add(package)

        except Exception as e:
            print(f"分析SPM失败: {e}")

    def _analyze_carthage(self):
        """分析Carthage依赖"""
        cartfile = self.project_path / "Cartfile.resolved"

        try:
            with open(cartfile, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for line in lines:
                match = re.match(r'\w+\s+"[^/]+/([^"]+)"', line)
                if match:
                    self.structure.carthage_dependencies.add(match.group(1))

        except Exception as e:
            print(f"分析Carthage失败: {e}")

    def _calculate_statistics(self):
        """计算统计信息"""
        # 总文件数
        self.structure.total_files = (
            len(self.structure.objc_headers) +
            len(self.structure.objc_sources) +
            len(self.structure.swift_files)
        )

        # 总代码行数（仅非第三方）
        self.structure.total_lines = sum(
            f.lines for f in (
                self.structure.objc_headers +
                self.structure.objc_sources +
                self.structure.swift_files
            ) if not f.is_third_party
        )

        # 语言占比
        objc_lines = sum(
            f.lines for f in (
                self.structure.objc_headers + self.structure.objc_sources
            ) if not f.is_third_party
        )

        swift_lines = sum(
            f.lines for f in self.structure.swift_files
            if not f.is_third_party
        )

        if self.structure.total_lines > 0:
            self.structure.objc_percentage = (objc_lines / self.structure.total_lines) * 100
            self.structure.swift_percentage = (swift_lines / self.structure.total_lines) * 100

    def _walk_directory(self, directory: Path):
        """递归遍历目录，跳过排除的目录"""
        try:
            for item in directory.iterdir():
                # 跳过排除的目录
                if item.is_dir():
                    if item.name in self.EXCLUDE_DIRS:
                        continue
                    yield from self._walk_directory(item)
                else:
                    # 只处理我们关心的文件类型
                    if item.suffix in ['.h', '.m', '.mm', '.swift', '.xib',
                                      '.storyboard', '.plist'] or \
                       item.name.endswith('.xcassets'):
                        yield item
        except PermissionError:
            pass

    def _is_third_party_file(self, file_path: Path) -> bool:
        """
        判断是否为第三方库文件 - P1修复: 增加内容特征检测

        修复:
        - 添加路径特征检测（快速路径）
        - 添加文件内容特征检测（慢速路径）
        - 提高第三方库识别准确性

        Args:
            file_path: 文件路径

        Returns:
            bool: 是否为第三方库文件
        """
        path_str = str(file_path)

        # P1修复: 快速路径 - 路径特征检测
        for indicator in self.THIRD_PARTY_INDICATORS:
            if indicator in path_str:
                return True

        # P1修复: 慢速路径 - 文件内容特征检测（仅检查头文件）
        # 只对头文件进行内容检测，避免性能影响
        if file_path.suffix == '.h':
            try:
                # 只读取前1000字节进行检测
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(1000)

                # 第三方库常见特征
                third_party_signatures = [
                    # 版权声明
                    'Copyright ©',
                    'Copyright (c)',
                    'Copyright (C)',
                    '©',

                    # 开源协议
                    'Licensed under',
                    'MIT License',
                    'Apache License',
                    'BSD License',
                    'GNU General Public',

                    # 协议标准文本
                    'Permission is hereby granted',
                    'THE SOFTWARE IS PROVIDED "AS IS"',
                    'THIS SOFTWARE IS PROVIDED BY',
                    'WITHOUT WARRANTY OF ANY KIND',

                    # CocoaPods生成的文件
                    '// Pods Target Support Files',
                    'Generated by CocoaPods',

                    # 常见第三方库标识
                    'AFNetworking',
                    'SDWebImage',
                    'Masonry',
                    'Alamofire',
                    'SnapKit',
                    'RxSwift',
                    'Kingfisher',

                    # 作者声明（常见于第三方库）
                    '@author',
                    'Created by',  # 注意：这个可能误判，需谨慎
                ]

                # 检查是否包含第三方库特征
                # 使用权重评分：多个特征匹配则更可能是第三方库
                match_count = sum(1 for sig in third_party_signatures if sig in content)

                # 如果匹配3个或以上特征，判定为第三方库
                if match_count >= 3:
                    return True

                # 如果包含明确的协议声明（MIT/Apache/BSD），直接判定
                license_keywords = ['MIT License', 'Apache License', 'BSD License',
                                   'GNU General Public']
                if any(keyword in content for keyword in license_keywords):
                    return True

                # 如果包含"Permission is hereby granted"（MIT协议标准文本），直接判定
                if 'Permission is hereby granted' in content:
                    return True

            except Exception:
                # 文件读取失败，忽略内容检测
                pass

        return False

    def _get_file_type(self, file_path: Path) -> FileType:
        """获取文件类型"""
        suffix = file_path.suffix
        if suffix == '.h':
            return FileType.OBJC_HEADER
        elif suffix == '.m':
            return FileType.OBJC_SOURCE
        elif suffix == '.mm':
            return FileType.OBJC_MM
        elif suffix == '.swift':
            return FileType.SWIFT
        elif suffix == '.xib':
            return FileType.XIB
        elif suffix == '.storyboard':
            return FileType.STORYBOARD
        elif suffix == '.plist':
            return FileType.PLIST
        elif suffix == '.strings':
            return FileType.STRINGS
        elif file_path.name.endswith('.xcassets'):
            return FileType.XCASSETS
        else:
            return FileType.OBJC_HEADER  # 默认

    def _count_lines(self, file_path: Path) -> int:
        """计算文件行数"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return sum(1 for _ in f)
        except Exception:
            return 0

    def get_source_files(self,
                        include_objc: bool = True,
                        include_swift: bool = True,
                        exclude_third_party: bool = True) -> List[SourceFile]:
        """
        获取源文件列表

        Args:
            include_objc: 是否包含ObjC文件
            include_swift: 是否包含Swift文件
            exclude_third_party: 是否排除第三方库

        Returns:
            List[SourceFile]: 源文件列表
        """
        files = []

        if include_objc:
            files.extend(self.structure.objc_headers)
            files.extend(self.structure.objc_sources)

        if include_swift:
            files.extend(self.structure.swift_files)

        if exclude_third_party:
            files = [f for f in files if not f.is_third_party]

        return files

    def export_report(self, output_path: str):
        """导出分析报告"""
        report = {
            'project_name': self.structure.project_name,
            'project_type': self.structure.project_type.value,
            'root_path': self.structure.root_path,

            'files': {
                'objc_headers': len(self.structure.objc_headers),
                'objc_sources': len(self.structure.objc_sources),
                'swift_files': len(self.structure.swift_files),
                'xibs': len(self.structure.xibs),
                'storyboards': len(self.structure.storyboards),
                'assets': len(self.structure.assets),
                'total': self.structure.total_files,
            },

            'code': {
                'total_lines': self.structure.total_lines,
                'objc_percentage': round(self.structure.objc_percentage, 2),
                'swift_percentage': round(self.structure.swift_percentage, 2),
            },

            'dependencies': {
                'cocoapods': list(self.structure.cocoapods_dependencies),
                'spm': list(self.structure.spm_dependencies),
                'carthage': list(self.structure.carthage_dependencies),
            },

            'configs': {
                'xcodeproj': self.structure.xcodeproj_path,
                'xcworkspace': self.structure.xcworkspace_path,
                'podfile': self.structure.podfile_path,
                'package_swift': self.structure.package_swift_path,
            }
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    # 测试代码（需要一个真实的iOS项目路径）
    import sys

    if len(sys.argv) > 1:
        project_path = sys.argv[1]
    else:
        # 默认测试路径（如果存在）
        test_paths = [
            "/Volumes/long/心娱/Github/WHC_ConfuseSoftware",
            "."
        ]
        project_path = next((p for p in test_paths if Path(p).exists()), None)

    if not project_path:
        print("用法: python project_analyzer.py <项目路径>")
        sys.exit(1)

    print(f"=== 项目分析器测试 ===")
    print(f"分析项目: {project_path}\n")

    # 创建分析器
    analyzer = ProjectAnalyzer(project_path)

    # 执行分析（带进度回调）
    def progress_callback(progress, message):
        print(f"[{progress*100:.0f}%] {message}")

    structure = analyzer.analyze(callback=progress_callback)

    # 输出结果
    print(f"\n项目信息:")
    print(f"  名称: {structure.project_name}")
    print(f"  类型: {structure.project_type.value}")
    print(f"  路径: {structure.root_path}")

    print(f"\n文件统计:")
    print(f"  ObjC头文件: {len(structure.objc_headers)}")
    print(f"  ObjC源文件: {len(structure.objc_sources)}")
    print(f"  Swift文件: {len(structure.swift_files)}")
    print(f"  XIB文件: {len(structure.xibs)}")
    print(f"  Storyboard: {len(structure.storyboards)}")
    print(f"  Assets: {len(structure.assets)}")
    print(f"  总计: {structure.total_files}")

    print(f"\n代码统计:")
    print(f"  总行数: {structure.total_lines}")
    print(f"  ObjC占比: {structure.objc_percentage:.1f}%")
    print(f"  Swift占比: {structure.swift_percentage:.1f}%")

    print(f"\n依赖信息:")
    print(f"  CocoaPods: {len(structure.cocoapods_dependencies)} 个")
    if structure.cocoapods_dependencies:
        for pod in list(structure.cocoapods_dependencies)[:5]:
            print(f"    - {pod}")
    print(f"  SPM: {len(structure.spm_dependencies)} 个")
    print(f"  Carthage: {len(structure.carthage_dependencies)} 个")

    # 导出报告
    report_path = "/tmp/project_analysis_report.json"
    analyzer.export_report(report_path)
    print(f"\n分析报告已导出到: {report_path}")

    print("\n=== 测试完成 ===")
