"""
第三方库检测器
检测项目中的第三方库文件，避免混淆
"""

from pathlib import Path
from typing import Set


class ThirdPartyDetector:
    """第三方库检测器"""

    # 第三方库目录特征
    THIRD_PARTY_DIRS = {
        'Pods',
        'Carthage',
        '.build',
        'Packages',
        'node_modules',
        'vendor',
        'ThirdParty',
        'External',
        'Dependencies',
        'Frameworks'
    }

    # 知名第三方库文件名模式
    KNOWN_LIBRARIES = {
        'AFNetworking',
        'Alamofire',
        'SDWebImage',
        'Kingfisher',
        'Masonry',
        'SnapKit',
        'ReactiveCocoa',
        'RxSwift',
        'YYKit',
        'MJRefresh',
        'FMDB',
        'Realm',
        'Firebase',
        'GoogleAnalytics',
        'Flurry',
        'Crashlytics',
        'MBProgressHUD',
        'SVProgressHUD',
        'IQKeyboardManager',
        'CocoaLumberjack',
        'JSONModel',
        'Mantle',
        'ObjectMapper',
        'SwiftyJSON',
        'PromiseKit',
        'Bolts',
        'Charts',
        'lottie-ios',
        'PopupDialog',
        'Material',
        'MaterialComponents',
        'ComponentKit',
        'Texture',
        'IGListKit',
        'Nimbus',
        'Three20',
        'RestKit',
        'SSZipArchive',
        'ZipArchive',
        'CocoaAsyncSocket',
        'SocketRocket',
        'Starscream',
        'KeychainAccess',
        'SAMKeychain',
        'UICKeyChainStore',
    }

    def __init__(self, project_path: str):
        """
        初始化检测器

        Args:
            project_path: 项目根目录路径
        """
        self.project_path = Path(project_path)
        self._third_party_cache: Set[Path] = set()

    def is_third_party_file(self, file_path: Path) -> bool:
        """
        判断文件是否属于第三方库

        Args:
            file_path: 文件路径

        Returns:
            bool: 是否为第三方库文件
        """
        # 使用缓存提高性能
        if file_path in self._third_party_cache:
            return True

        # 转换为相对路径
        try:
            rel_path = file_path.relative_to(self.project_path)
        except ValueError:
            # 不在项目目录内
            return True

        # 检查是否在第三方目录中
        parts = rel_path.parts
        for part in parts:
            if part in self.THIRD_PARTY_DIRS:
                self._third_party_cache.add(file_path)
                return True

        # 检查是否匹配知名库名称
        file_name = file_path.stem  # 不含扩展名的文件名
        for library in self.KNOWN_LIBRARIES:
            if library.lower() in file_name.lower():
                self._third_party_cache.add(file_path)
                return True

        # 检查目录名
        parent_name = file_path.parent.name
        for library in self.KNOWN_LIBRARIES:
            if library.lower() in parent_name.lower():
                self._third_party_cache.add(file_path)
                return True

        return False

    def get_third_party_directories(self) -> Set[Path]:
        """
        获取项目中所有第三方库目录

        Returns:
            Set[Path]: 第三方库目录集合
        """
        third_party_dirs = set()

        for dir_name in self.THIRD_PARTY_DIRS:
            dir_path = self.project_path / dir_name
            if dir_path.exists() and dir_path.is_dir():
                third_party_dirs.add(dir_path)

        return third_party_dirs

    def clear_cache(self):
        """清空缓存"""
        self._third_party_cache.clear()
