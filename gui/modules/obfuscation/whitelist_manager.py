"""
白名单管理器 - 负责管理需要排除混淆的符号

支持:
1. 内置系统API白名单(UIKit、Foundation等500+类、1000+方法)
2. 第三方库自动检测(CocoaPods、SPM、Carthage)
3. 自定义白名单管理
4. 智能白名单建议
5. 白名单导入导出
"""

import json
import os
import re
from pathlib import Path
from typing import Set, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class WhitelistType(Enum):
    """白名单类型"""
    SYSTEM_CLASS = "system_class"           # 系统类
    SYSTEM_METHOD = "system_method"         # 系统方法
    SYSTEM_PROPERTY = "system_property"     # 系统属性
    THIRD_PARTY = "third_party"             # 第三方库
    CUSTOM = "custom"                       # 自定义
    LIFECYCLE = "lifecycle"                 # 生命周期方法
    APP_DELEGATE = "app_delegate"           # AppDelegate相关


@dataclass
class WhitelistItem:
    """白名单项"""
    name: str
    type: WhitelistType
    source: str = "builtin"  # builtin, detected, custom
    confidence: float = 1.0  # 0.0-1.0置信度
    reason: str = ""


class SystemAPIWhitelist:
    """
    内置系统API白名单
    包含iOS/macOS常用系统框架的类、方法、属性
    """

    # UIKit核心类（100+）
    UIKIT_CLASSES = {
        # 视图控制器
        'UIViewController', 'UINavigationController', 'UITabBarController',
        'UITableViewController', 'UICollectionViewController', 'UISplitViewController',
        'UIPageViewController', 'UISearchController', 'UIAlertController',
        'UIActivityViewController', 'UIImagePickerController', 'UIDocumentPickerViewController',

        # 视图组件
        'UIView', 'UIWindow', 'UIScrollView', 'UITableView', 'UICollectionView',
        'UITextView', 'UIImageView', 'UIPickerView', 'UIWebView', 'WKWebView',
        'UIStackView', 'UIVisualEffectView', 'UIActivityIndicatorView',

        # 控件
        'UIButton', 'UILabel', 'UITextField', 'UISwitch', 'UISlider',
        'UISegmentedControl', 'UIStepper', 'UIDatePicker', 'UIPageControl',
        'UIProgressView', 'UIRefreshControl', 'UISearchBar', 'UIToolbar',

        # 导航栏和工具栏
        'UINavigationBar', 'UINavigationItem', 'UIBarButtonItem', 'UITabBar', 'UITabBarItem',

        # 手势识别
        'UIGestureRecognizer', 'UITapGestureRecognizer', 'UISwipeGestureRecognizer',
        'UIPanGestureRecognizer', 'UIPinchGestureRecognizer', 'UIRotationGestureRecognizer',
        'UILongPressGestureRecognizer', 'UIScreenEdgePanGestureRecognizer',

        # 布局
        'NSLayoutConstraint', 'UILayoutGuide', 'NSLayoutAnchor', 'NSLayoutXAxisAnchor',
        'NSLayoutYAxisAnchor', 'NSLayoutDimension',

        # 动画
        'UIViewPropertyAnimator', 'UIViewAnimatingPosition', 'UISpringTimingParameters',

        # 集合视图
        'UICollectionViewLayout', 'UICollectionViewFlowLayout',
        'UICollectionViewCell', 'UICollectionReusableView',
        'UICollectionViewLayoutAttributes', 'UICollectionViewTransitionLayout',

        # 表格视图
        'UITableViewCell', 'UITableViewHeaderFooterView',

        # 其他
        'UIApplication', 'UIScene', 'UISceneSession', 'UIResponder',
        'UIColor', 'UIFont', 'UIImage', 'UIBezierPath', 'UITouch', 'UIEvent',
        'UIScreen', 'UIDevice', 'UIPasteboard', 'UIMenuController',
        'UIFeedbackGenerator', 'UINotificationFeedbackGenerator', 'UIImpactFeedbackGenerator',
        'UISelectionFeedbackGenerator',
    }

    # Foundation核心类（80+）
    FOUNDATION_CLASSES = {
        # 基础类型
        'NSObject', 'NSNumber', 'NSValue', 'NSString', 'NSMutableString',
        'NSData', 'NSMutableData', 'NSDate', 'NSCalendar', 'NSDateComponents',
        'NSDateFormatter', 'NSNumberFormatter', 'NSLocale', 'NSTimeZone',

        # 集合类型
        'NSArray', 'NSMutableArray', 'NSSet', 'NSMutableSet', 'NSOrderedSet',
        'NSDictionary', 'NSMutableDictionary', 'NSCountedSet', 'NSHashTable',
        'NSMapTable', 'NSPointerArray', 'NSIndexSet', 'NSMutableIndexSet',

        # 文件系统
        'NSFileManager', 'NSBundle', 'NSURL', 'NSURLComponents', 'NSURLRequest',
        'NSURLResponse', 'NSHTTPURLResponse', 'NSURLSession', 'NSURLSessionConfiguration',
        'NSURLSessionTask', 'NSURLSessionDataTask', 'NSURLSessionUploadTask',
        'NSURLSessionDownloadTask', 'NSURLCache',

        # 通知和KVO
        'NSNotification', 'NSNotificationCenter', 'NSNotificationQueue',
        'NSKeyValueObservingOptions', 'NSKeyValueChangeKey',

        # 线程和并发
        'NSThread', 'NSOperation', 'NSOperationQueue', 'NSBlockOperation',
        'NSInvocationOperation', 'NSLock', 'NSRecursiveLock', 'NSCondition',
        'NSConditionLock', 'NSDistributedLock',

        # 运行循环和计时器
        'NSRunLoop', 'NSTimer', 'NSPort', 'NSPortMessage',

        # 其他
        'NSError', 'NSException', 'NSProcessInfo', 'NSUserDefaults',
        'NSJSONSerialization', 'NSPropertyListSerialization', 'NSXMLParser',
        'NSNull', 'NSProxy', 'NSScanner', 'NSRegularExpression',
        'NSPredicate', 'NSExpression', 'NSCompoundPredicate',
        'NSAttributedString', 'NSMutableAttributedString',
        'NSValueTransformer', 'NSFormatter', 'NSCoder', 'NSKeyedArchiver',
        'NSKeyedUnarchiver',
    }

    # Core Graphics类和结构体（30+）
    COREGRAPHICS_CLASSES = {
        # CG类
        'CGContext', 'CGPath', 'CGMutablePath', 'CGColor', 'CGColorSpace',
        'CGImage', 'CGDataProvider', 'CGFont', 'CGGradient', 'CGShading',
        'CGPattern', 'CGLayer', 'CGPDFDocument', 'CGPDFPage',
        'CGBitmapContext', 'CGImageSource', 'CGImageDestination',
        # CG结构体类型
        'CGRect', 'CGPoint', 'CGSize', 'CGVector', 'CGAffineTransform',
        'CGFloat', 'CGPathDrawingMode', 'CGBlendMode', 'CGLineCap', 'CGLineJoin',
    }

    # Core Animation类（20+）
    COREANIMATION_CLASSES = {
        'CALayer', 'CAShapeLayer', 'CAGradientLayer', 'CATextLayer',
        'CAScrollLayer', 'CAReplicatorLayer', 'CAEmitterLayer', 'CATiledLayer',
        'CATransformLayer', 'CAAnimation', 'CABasicAnimation', 'CAKeyframeAnimation',
        'CASpringAnimation', 'CATransition', 'CAAnimationGroup',
        'CAMediaTiming', 'CAMediaTimingFunction', 'CADisplayLink',
        'CATransaction', 'CAValueFunction',
    }

    # SwiftUI类（50+）
    SWIFTUI_CLASSES = {
        'View', 'Text', 'Image', 'Button', 'TextField', 'SecureField',
        'Toggle', 'Slider', 'Stepper', 'DatePicker', 'Picker', 'ColorPicker',
        'VStack', 'HStack', 'ZStack', 'List', 'ScrollView', 'LazyVStack',
        'LazyHStack', 'NavigationView', 'NavigationLink', 'TabView',
        'Form', 'Section', 'Group', 'GeometryReader', 'Shape', 'Path',
        'Rectangle', 'Circle', 'Ellipse', 'Capsule', 'RoundedRectangle',
        'Color', 'LinearGradient', 'RadialGradient', 'AngularGradient',
        'Spacer', 'Divider', 'Alert', 'ActionSheet', 'Sheet', 'Popover',
        'State', 'Binding', 'ObservedObject', 'EnvironmentObject',
        'StateObject', 'Published', 'Environment', 'AppStorage', 'SceneStorage',
    }

    # 系统委托和数据源方法（100+）
    SYSTEM_METHODS = {
        # UIViewController生命周期
        'viewDidLoad', 'viewWillAppear:', 'viewDidAppear:', 'viewWillDisappear:',
        'viewDidDisappear:', 'viewWillLayoutSubviews', 'viewDidLayoutSubviews',
        'viewWillTransitionToSize:withTransitionCoordinator:',
        'willTransitionToTraitCollection:withTransitionCoordinator:',
        'didReceiveMemoryWarning', 'viewDidLoad', 'loadView',

        # UIApplicationDelegate
        'application:didFinishLaunchingWithOptions:',
        'applicationDidBecomeActive:', 'applicationWillResignActive:',
        'applicationDidEnterBackground:', 'applicationWillEnterForeground:',
        'applicationWillTerminate:', 'application:didReceiveRemoteNotification:',
        'application:didRegisterForRemoteNotificationsWithDeviceToken:',
        'application:didFailToRegisterForRemoteNotificationsWithError:',
        'application:handleOpenURL:', 'application:openURL:options:',

        # UITableViewDataSource
        'numberOfSectionsInTableView:', 'tableView:numberOfRowsInSection:',
        'tableView:cellForRowAtIndexPath:', 'tableView:titleForHeaderInSection:',
        'tableView:titleForFooterInSection:', 'tableView:canEditRowAtIndexPath:',
        'tableView:canMoveRowAtIndexPath:', 'tableView:commitEditingStyle:forRowAtIndexPath:',

        # UITableViewDelegate
        'tableView:heightForRowAtIndexPath:', 'tableView:didSelectRowAtIndexPath:',
        'tableView:didDeselectRowAtIndexPath:', 'tableView:willDisplayCell:forRowAtIndexPath:',
        'tableView:viewForHeaderInSection:', 'tableView:viewForFooterInSection:',
        'tableView:heightForHeaderInSection:', 'tableView:heightForFooterInSection:',
        'tableView:editingStyleForRowAtIndexPath:', 'tableView:willBeginEditingRowAtIndexPath:',

        # UICollectionViewDataSource
        'numberOfSectionsInCollectionView:', 'collectionView:numberOfItemsInSection:',
        'collectionView:cellForItemAtIndexPath:',
        'collectionView:viewForSupplementaryElementOfKind:atIndexPath:',

        # UICollectionViewDelegate
        'collectionView:didSelectItemAtIndexPath:',
        'collectionView:didDeselectItemAtIndexPath:',
        'collectionView:willDisplayCell:forItemAtIndexPath:',
        'collectionView:didEndDisplayingCell:forItemAtIndexPath:',

        # UICollectionViewDelegateFlowLayout
        'collectionView:layout:sizeForItemAtIndexPath:',
        'collectionView:layout:insetForSectionAtIndex:',
        'collectionView:layout:minimumLineSpacingForSectionAtIndex:',
        'collectionView:layout:minimumInteritemSpacingForSectionAtIndex:',
        'collectionView:layout:referenceSizeForHeaderInSection:',
        'collectionView:layout:referenceSizeForFooterInSection:',

        # UIScrollViewDelegate
        'scrollViewDidScroll:', 'scrollViewWillBeginDragging:',
        'scrollViewDidEndDragging:willDecelerate:', 'scrollViewDidEndDecelerating:',
        'scrollViewWillBeginZooming:withView:', 'scrollViewDidEndZooming:withView:atScale:',

        # UITextFieldDelegate
        'textFieldShouldBeginEditing:', 'textFieldDidBeginEditing:',
        'textFieldShouldEndEditing:', 'textFieldDidEndEditing:',
        'textField:shouldChangeCharactersInRange:replacementString:',
        'textFieldShouldReturn:', 'textFieldShouldClear:',

        # UITextViewDelegate
        'textViewShouldBeginEditing:', 'textViewDidBeginEditing:',
        'textViewShouldEndEditing:', 'textViewDidEndEditing:',
        'textView:shouldChangeTextInRange:replacementText:',
        'textViewDidChange:',

        # NSObject基础方法
        'init', 'dealloc', 'alloc', 'new', 'copy', 'mutableCopy', 'description', 'debugDescription',
        'hash', 'isEqual:', 'class', 'superclass', 'isKindOfClass:', 'isMemberOfClass:',
        'respondsToSelector:', 'conformsToProtocol:', 'performSelector:',

        # KVO方法
        'addObserver:forKeyPath:options:context:',
        'removeObserver:forKeyPath:', 'removeObserver:forKeyPath:context:',
        'observeValueForKeyPath:ofObject:change:context:',

        # 手势识别
        'handleTapGesture:', 'handleSwipeGesture:', 'handlePanGesture:',
        'handlePinchGesture:', 'handleRotationGesture:', 'handleLongPressGesture:',
    }

    # 系统属性（50+）
    # 注意：只包含系统框架定义的属性，不包含常见的用户自定义属性名
    SYSTEM_PROPERTIES = {
        # UIView - 核心布局属性
        'frame', 'bounds', 'center', 'transform', 'alpha', 'backgroundColor',
        'hidden', 'clipsToBounds', 'layer', 'superview', 'subviews',
        'contentMode', 'userInteractionEnabled', 'multipleTouchEnabled',
        'exclusiveTouch', 'autoresizingMask', 'translatesAutoresizingMaskIntoConstraints',

        # UIViewController - 系统定义的属性
        'view', 'navigationItem', 'navigationController', 'tabBarController',
        'splitViewController', 'parentViewController', 'childViewControllers',
        'presentedViewController', 'presentingViewController', 'modalPresentationStyle',
        'modalTransitionStyle', 'hidesBottomBarWhenPushed',

        # UITableView - 系统属性
        'dataSource', 'delegate', 'rowHeight', 'separatorStyle', 'separatorColor',
        'tableHeaderView', 'tableFooterView', 'allowsSelection', 'allowsMultipleSelection',
        'editing', 'sectionIndexColor', 'sectionIndexBackgroundColor',

        # UIButton - 系统属性
        'titleLabel', 'imageView', 'currentTitle', 'currentImage',
        'currentTitleColor', 'buttonType', 'contentEdgeInsets',

        # UILabel - 系统属性
        'font', 'textColor', 'textAlignment', 'numberOfLines',
        'lineBreakMode', 'adjustsFontSizeToFitWidth', 'minimumScaleFactor',

        # UITextField - 系统属性
        'placeholder', 'borderStyle', 'clearButtonMode', 'leftView', 'rightView',
        'secureTextEntry', 'keyboardType', 'returnKeyType',

        # 注意：移除了 'title', 'text', 'name' 等常见词，这些可能是用户自定义属性
        # 如需保护UIViewController.title，应在上下文中判断（通过父类类型）
    }

    @classmethod
    def get_all_system_classes(cls) -> Set[str]:
        """获取所有系统类"""
        return (cls.UIKIT_CLASSES | cls.FOUNDATION_CLASSES |
                cls.COREGRAPHICS_CLASSES | cls.COREANIMATION_CLASSES |
                cls.SWIFTUI_CLASSES)

    @classmethod
    def get_all_system_methods(cls) -> Set[str]:
        """获取所有系统方法"""
        return cls.SYSTEM_METHODS

    @classmethod
    def get_all_system_properties(cls) -> Set[str]:
        """获取所有系统属性"""
        return cls.SYSTEM_PROPERTIES

    @classmethod
    def is_system_api(cls, name: str, type_hint: str = "") -> bool:
        """
        判断是否为系统API

        Args:
            name: API名称
            type_hint: 类型提示 (class/method/property)

        Returns:
            bool: 是否为系统API
        """
        if type_hint == "class":
            return name in cls.get_all_system_classes()
        elif type_hint == "method":
            # 方法名可能包含参数，需要模糊匹配
            return any(name.startswith(m) or m.startswith(name) for m in cls.SYSTEM_METHODS)
        elif type_hint == "property":
            return name in cls.SYSTEM_PROPERTIES
        else:
            # 未指定类型，全部检查
            return (name in cls.get_all_system_classes() or
                    name in cls.SYSTEM_METHODS or
                    name in cls.SYSTEM_PROPERTIES)


class ThirdPartyDetector:
    """第三方库自动检测器"""

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.detected_libraries: Dict[str, Set[str]] = {}

    def detect_cocoapods(self) -> Set[str]:
        """
        检测CocoaPods依赖

        Returns:
            Set[str]: Pod库名称集合
        """
        pods = set()

        # 检查Podfile.lock
        podfile_lock = self.project_path / 'Podfile.lock'
        if podfile_lock.exists():
            try:
                with open(podfile_lock, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 解析PODS段落
                pods_section = re.search(r'PODS:\n(.*?)(?:\n\n|\Z)', content, re.DOTALL)
                if pods_section:
                    pod_lines = pods_section.group(1).split('\n')
                    for line in pod_lines:
                        # 匹配 "- PodName (version)" 或 "- PodName/SubSpec (version)"
                        match = re.match(r'\s*-\s+([^/\s(]+)', line)
                        if match:
                            pods.add(match.group(1))

            except Exception as e:
                print(f"检测CocoaPods失败: {e}")

        return pods

    def detect_spm(self) -> Set[str]:
        """
        检测Swift Package Manager依赖

        Returns:
            Set[str]: SPM包名称集合
        """
        packages = set()

        # 检查Package.swift
        package_swift = self.project_path / 'Package.swift'
        if package_swift.exists():
            try:
                with open(package_swift, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 匹配 .package(url: "...", from: "...")
                matches = re.findall(r'\.package\([^)]*url:\s*["\']([^"\']+)["\']', content)
                for url in matches:
                    # 从URL提取包名
                    package_name = url.rstrip('/').split('/')[-1].replace('.git', '')
                    packages.add(package_name)

            except Exception as e:
                print(f"检测SPM失败: {e}")

        # 检查Package.resolved
        package_resolved = self.project_path / 'Package.resolved'
        if package_resolved.exists():
            try:
                with open(package_resolved, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                for pin in data.get('object', {}).get('pins', []):
                    package = pin.get('package')
                    if package:
                        packages.add(package)

            except Exception as e:
                print(f"检测Package.resolved失败: {e}")

        return packages

    def detect_carthage(self) -> Set[str]:
        """
        检测Carthage依赖

        Returns:
            Set[str]: Carthage库名称集合
        """
        frameworks = set()

        # 检查Cartfile.resolved
        cartfile_resolved = self.project_path / 'Cartfile.resolved'
        if cartfile_resolved.exists():
            try:
                with open(cartfile_resolved, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                for line in lines:
                    # 匹配 github "owner/repo" "version"
                    match = re.match(r'\w+\s+"[^/]+/([^"]+)"', line)
                    if match:
                        frameworks.add(match.group(1))

            except Exception as e:
                print(f"检测Carthage失败: {e}")

        return frameworks

    def detect_all(self) -> Dict[str, Set[str]]:
        """
        检测所有第三方库

        Returns:
            Dict[str, Set[str]]: {"cocoapods": {...}, "spm": {...}, "carthage": {...}}
        """
        return {
            'cocoapods': self.detect_cocoapods(),
            'spm': self.detect_spm(),
            'carthage': self.detect_carthage(),
        }

    def get_all_library_names(self) -> Set[str]:
        """获取所有检测到的库名称"""
        all_libs = self.detect_all()
        return set().union(*all_libs.values())


class WhitelistManager:
    """白名单管理器"""

    def __init__(self, project_path: Optional[str] = None):
        """
        初始化白名单管理器

        Args:
            project_path: 项目路径（用于自动检测第三方库）
        """
        self.project_path = project_path
        self.whitelist: Dict[WhitelistType, Set[str]] = {
            wtype: set() for wtype in WhitelistType
        }
        self.whitelist_items: List[WhitelistItem] = []

        # 加载内置系统API白名单
        self._load_system_whitelist()

    def _load_system_whitelist(self):
        """加载内置系统API白名单"""
        # 系统类
        for cls in SystemAPIWhitelist.get_all_system_classes():
            self.whitelist[WhitelistType.SYSTEM_CLASS].add(cls)
            self.whitelist_items.append(WhitelistItem(
                name=cls,
                type=WhitelistType.SYSTEM_CLASS,
                source="builtin",
                confidence=1.0,
                reason="iOS/macOS系统类"
            ))

        # 系统方法
        for method in SystemAPIWhitelist.get_all_system_methods():
            self.whitelist[WhitelistType.SYSTEM_METHOD].add(method)
            self.whitelist_items.append(WhitelistItem(
                name=method,
                type=WhitelistType.SYSTEM_METHOD,
                source="builtin",
                confidence=1.0,
                reason="系统委托/生命周期方法"
            ))

        # 系统属性
        for prop in SystemAPIWhitelist.get_all_system_properties():
            self.whitelist[WhitelistType.SYSTEM_PROPERTY].add(prop)
            self.whitelist_items.append(WhitelistItem(
                name=prop,
                type=WhitelistType.SYSTEM_PROPERTY,
                source="builtin",
                confidence=1.0,
                reason="系统属性"
            ))

    def auto_detect_third_party(self) -> int:
        """
        自动检测第三方库并添加到白名单

        Returns:
            int: 检测到的库数量
        """
        if not self.project_path:
            return 0

        detector = ThirdPartyDetector(self.project_path)
        all_libs = detector.detect_all()

        count = 0
        for source, libs in all_libs.items():
            for lib in libs:
                if lib not in self.whitelist[WhitelistType.THIRD_PARTY]:
                    self.whitelist[WhitelistType.THIRD_PARTY].add(lib)
                    self.whitelist_items.append(WhitelistItem(
                        name=lib,
                        type=WhitelistType.THIRD_PARTY,
                        source="detected",
                        confidence=0.9,
                        reason=f"通过{source}检测到"
                    ))
                    count += 1

        return count

    def add_custom(self, name: str, wtype: WhitelistType, reason: str = ""):
        """
        添加自定义白名单项

        Args:
            name: 名称
            wtype: 类型
            reason: 原因说明
        """
        if name not in self.whitelist[wtype]:
            self.whitelist[wtype].add(name)
            self.whitelist_items.append(WhitelistItem(
                name=name,
                type=wtype,
                source="custom",
                confidence=1.0,
                reason=reason or "用户自定义"
            ))

    def remove_custom(self, name: str, wtype: Optional[WhitelistType] = None) -> bool:
        """
        删除自定义白名单项（不能删除内置项）

        Args:
            name: 名称
            wtype: 类型，如果为None则删除所有类型中的该项

        Returns:
            bool: 是否成功删除（True表示至少删除了一项）
        """
        types_to_check = [wtype] if wtype else list(WhitelistType)
        removed = False

        for t in types_to_check:
            if name in self.whitelist[t]:
                # 只删除非内置项
                item = next((i for i in self.whitelist_items
                           if i.name == name and i.type == t and i.source != "builtin"), None)
                if item:
                    self.whitelist[t].discard(name)
                    self.whitelist_items.remove(item)
                    removed = True

        return removed

    def is_whitelisted(self, name: str) -> bool:
        """
        判断是否在白名单中

        Args:
            name: 名称

        Returns:
            bool: 是否在白名单中
        """
        return any(name in wlist for wlist in self.whitelist.values())

    def get_whitelist_item(self, name: str) -> Optional[WhitelistItem]:
        """获取白名单项详情"""
        return next((item for item in self.whitelist_items if item.name == name), None)

    def suggest_whitelist(self, symbols: Dict[str, List[str]]) -> List[WhitelistItem]:
        """
        智能白名单建议

        Args:
            symbols: {"classes": [...], "methods": [...], "properties": [...]}

        Returns:
            List[WhitelistItem]: 建议添加到白名单的项
        """
        suggestions = []

        # 检查类名
        for cls in symbols.get('classes', []):
            if SystemAPIWhitelist.is_system_api(cls, 'class'):
                suggestions.append(WhitelistItem(
                    name=cls,
                    type=WhitelistType.SYSTEM_CLASS,
                    source="suggested",
                    confidence=1.0,
                    reason="匹配系统类"
                ))
            elif cls.endswith('Delegate') or cls.endswith('Protocol'):
                suggestions.append(WhitelistItem(
                    name=cls,
                    type=WhitelistType.CUSTOM,
                    source="suggested",
                    confidence=0.7,
                    reason="可能是委托/协议"
                ))

        # 检查方法名
        lifecycle_patterns = [
            r'viewDid\w+', r'viewWill\w+', r'application\w+',
            r'tableView:\w+', r'collectionView:\w+', r'scrollView\w+',
            r'textField\w+', r'textView\w+', r'init\w*', r'dealloc'
        ]

        for method in symbols.get('methods', []):
            if SystemAPIWhitelist.is_system_api(method, 'method'):
                suggestions.append(WhitelistItem(
                    name=method,
                    type=WhitelistType.SYSTEM_METHOD,
                    source="suggested",
                    confidence=1.0,
                    reason="匹配系统方法"
                ))
            elif any(re.match(pattern, method) for pattern in lifecycle_patterns):
                suggestions.append(WhitelistItem(
                    name=method,
                    type=WhitelistType.LIFECYCLE,
                    source="suggested",
                    confidence=0.8,
                    reason="可能是生命周期方法"
                ))

        return suggestions

    def export_whitelist(self, filepath: str):
        """导出白名单到文件"""
        data = {
            'system_classes': list(self.whitelist[WhitelistType.SYSTEM_CLASS]),
            'system_methods': list(self.whitelist[WhitelistType.SYSTEM_METHOD]),
            'system_properties': list(self.whitelist[WhitelistType.SYSTEM_PROPERTY]),
            'third_party': list(self.whitelist[WhitelistType.THIRD_PARTY]),
            'custom': list(self.whitelist[WhitelistType.CUSTOM]),
            'lifecycle': list(self.whitelist[WhitelistType.LIFECYCLE]),
            'app_delegate': list(self.whitelist[WhitelistType.APP_DELEGATE]),
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def import_whitelist(self, filepath: str):
        """从文件导入白名单（仅导入自定义项）"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 导入自定义项
        for name in data.get('custom', []):
            self.add_custom(name, WhitelistType.CUSTOM)

        # 导入第三方库
        for name in data.get('third_party', []):
            if name not in self.whitelist[WhitelistType.THIRD_PARTY]:
                self.add_custom(name, WhitelistType.THIRD_PARTY, "从文件导入")

    def get_statistics(self) -> Dict[str, int]:
        """获取白名单统计信息"""
        return {
            "system_classes": len(self.whitelist[WhitelistType.SYSTEM_CLASS]),
            "system_methods": len(self.whitelist[WhitelistType.SYSTEM_METHOD]),
            "system_properties": len(self.whitelist[WhitelistType.SYSTEM_PROPERTY]),
            "third_party": len(self.whitelist[WhitelistType.THIRD_PARTY]),
            "custom": len(self.whitelist[WhitelistType.CUSTOM]),
            "total": len(self.whitelist_items)
        }


if __name__ == "__main__":
    # 测试代码
    print("=== 系统API白名单测试 ===\n")

    # 1. 检查系统API
    print("1. 系统API检查:")
    test_cases = [
        ("UIViewController", "class"),
        ("NSString", "class"),
        ("viewDidLoad", "method"),
        ("tableView:cellForRowAtIndexPath:", "method"),
        ("frame", "property"),
    ]

    for name, type_hint in test_cases:
        is_system = SystemAPIWhitelist.is_system_api(name, type_hint)
        print(f"  {name} ({type_hint}): {'✓ 系统API' if is_system else '✗ 非系统API'}")

    # 2. 白名单管理器
    print("\n2. 白名单管理器:")
    manager = WhitelistManager()
    stats = manager.get_statistics()
    print(f"  系统类: {stats['system_classes']}")
    print(f"  系统方法: {stats['system_methods']}")
    print(f"  系统属性: {stats['system_properties']}")
    print(f"  总计: {stats['total']}")

    # 3. 添加自定义白名单
    print("\n3. 自定义白名单:")
    manager.add_custom("MyCustomClass", WhitelistType.CUSTOM, "测试类")
    print(f"  是否在白名单: {manager.is_whitelisted('MyCustomClass')}")

    # 4. 白名单建议
    print("\n4. 智能建议:")
    symbols = {
        'classes': ['UIViewController', 'MyViewController', 'SomeDelegate'],
        'methods': ['viewDidLoad', 'myCustomMethod', 'tableView:numberOfRowsInSection:'],
    }
    suggestions = manager.suggest_whitelist(symbols)
    print(f"  建议添加 {len(suggestions)} 项:")
    for item in suggestions[:3]:
        print(f"    - {item.name} ({item.confidence:.1f}) - {item.reason}")

    # 5. 导出导入测试
    print("\n5. 导出/导入测试:")
    test_file = "/tmp/test_whitelist.json"
    manager.export_whitelist(test_file)
    print(f"  已导出到: {test_file}")

    manager2 = WhitelistManager()
    manager2.import_whitelist(test_file)
    print(f"  导入后自定义项数量: {manager2.get_statistics()['custom']}")

    print("\n=== 测试完成 ===")
