"""
资源文件处理器 - 负责处理图片、XIB、Storyboard等资源文件

支持:
1. 图片文件hash值修改
2. XIB/Storyboard类名同步更新
3. Assets.xcassets处理
4. Plist文件处理
"""

import os
import hashlib
import json
import plistlib
from pathlib import Path
from typing import Dict, List, Set, Optional
import xml.etree.ElementTree as ET


class ResourceHandler:
    """资源文件处理器"""

    def __init__(self, symbol_mappings: Dict[str, str]):
        """
        初始化资源处理器

        Args:
            symbol_mappings: 符号映射字典 {原始名: 混淆名}
        """
        self.symbol_mappings = symbol_mappings
        self.stats = {
            'images_modified': 0,
            'xibs_updated': 0,
            'storyboards_updated': 0,
            'plists_updated': 0,
        }

    def modify_image_hash(self, image_path: str, output_path: str = None) -> bool:
        """
        修改图片文件的hash值（在文件末尾添加随机字节）

        Args:
            image_path: 图片路径
            output_path: 输出路径，如果为None则覆盖原文件

        Returns:
            bool: 是否成功
        """
        try:
            if output_path is None:
                output_path = image_path

            # 读取原始图片
            with open(image_path, 'rb') as f:
                data = bytearray(f.read())

            # 在末尾添加一些随机字节（不影响图片显示）
            import random
            random_bytes = bytes([random.randint(0, 255) for _ in range(16)])
            data.extend(random_bytes)

            # 写入修改后的文件
            with open(output_path, 'wb') as f:
                f.write(data)

            self.stats['images_modified'] += 1
            return True

        except Exception as e:
            print(f"修改图片hash失败 {image_path}: {e}")
            return False

    def update_xib(self, xib_path: str, output_path: str = None) -> bool:
        """
        更新XIB文件中的类名引用 - P0修复: 支持更多属性

        Args:
            xib_path: XIB文件路径
            output_path: 输出路径

        Returns:
            bool: 是否成功

        修复:
        - 支持 destinationClass 属性（outlet连接）
        - 支持 placeholder 中的 customClass
        - 支持 segue 中的 customClass
        """
        try:
            if output_path is None:
                output_path = xib_path

            # 解析XML
            tree = ET.parse(xib_path)
            root = tree.getroot()

            replacements = 0

            # 遍历所有元素，更新类名引用
            for elem in root.iter():
                # 1. 更新customClass属性
                # 适用于: view, button, controller等所有自定义组件
                if 'customClass' in elem.attrib:
                    original_class = elem.attrib['customClass']
                    if original_class in self.symbol_mappings:
                        elem.attrib['customClass'] = self.symbol_mappings[original_class]
                        replacements += 1

                # 2. P0修复: 更新destinationClass属性
                # 适用于: <outlet> 标签中的目标类
                # 例如: <outlet property="delegate" destination="..." destinationClass="MyDelegate"/>
                if 'destinationClass' in elem.attrib:
                    original_class = elem.attrib['destinationClass']
                    if original_class in self.symbol_mappings:
                        elem.attrib['destinationClass'] = self.symbol_mappings[original_class]
                        replacements += 1

                # 3. P0修复: 更新userLabel中的类名
                # 某些XIB在userLabel中也包含类名
                if 'userLabel' in elem.attrib:
                    user_label = elem.attrib['userLabel']
                    # 检查userLabel是否是一个类名
                    if user_label in self.symbol_mappings:
                        elem.attrib['userLabel'] = self.symbol_mappings[user_label]
                        replacements += 1

            if replacements > 0:
                # 保存修改后的XIB
                tree.write(output_path, encoding='utf-8', xml_declaration=True)
                self.stats['xibs_updated'] += 1
                return True

            return False

        except Exception as e:
            print(f"更新XIB失败 {xib_path}: {e}")
            return False

    def update_storyboard(self, storyboard_path: str, output_path: str = None) -> bool:
        """
        更新Storyboard文件中的类名引用 - P0修复: 支持更多属性

        Args:
            storyboard_path: Storyboard文件路径
            output_path: 输出路径

        Returns:
            bool: 是否成功

        修复:
        - 支持 destinationClass 属性（segue目标）
        - 支持 segue 中的 customClass
        - 支持 placeholder 中的 customClass
        - 支持 userLabel 中的类名
        """
        try:
            if output_path is None:
                output_path = storyboard_path

            # 解析XML
            tree = ET.parse(storyboard_path)
            root = tree.getroot()

            replacements = 0

            # 遍历所有元素
            for elem in root.iter():
                # 1. 更新customClass属性
                # 适用于: viewController, view, cell等所有自定义组件
                if 'customClass' in elem.attrib:
                    original_class = elem.attrib['customClass']
                    if original_class in self.symbol_mappings:
                        elem.attrib['customClass'] = self.symbol_mappings[original_class]
                        replacements += 1

                # 2. P0修复: 更新destinationClass属性
                # 适用于: <segue> 标签中的目标类
                # 例如: <segue destination="..." kind="show" destinationClass="MyViewController"/>
                if 'destinationClass' in elem.attrib:
                    original_class = elem.attrib['destinationClass']
                    if original_class in self.symbol_mappings:
                        elem.attrib['destinationClass'] = self.symbol_mappings[original_class]
                        replacements += 1

                # 3. 更新storyboardIdentifier
                # 注意: storyboardIdentifier通常是字符串标识符，不一定是类名
                # 只有在映射表中存在时才替换
                if 'storyboardIdentifier' in elem.attrib:
                    original_id = elem.attrib['storyboardIdentifier']
                    if original_id in self.symbol_mappings:
                        elem.attrib['storyboardIdentifier'] = self.symbol_mappings[original_id]
                        replacements += 1

                # 4. 更新reuseIdentifier
                # 注意: reuseIdentifier通常是字符串标识符，不一定是类名
                # 只有在映射表中存在时才替换
                if 'reuseIdentifier' in elem.attrib:
                    original_id = elem.attrib['reuseIdentifier']
                    if original_id in self.symbol_mappings:
                        elem.attrib['reuseIdentifier'] = self.symbol_mappings[original_id]
                        replacements += 1

                # 5. P0修复: 更新userLabel中的类名
                # 某些Storyboard在userLabel中也包含类名（如"File's Owner"）
                if 'userLabel' in elem.attrib:
                    user_label = elem.attrib['userLabel']
                    # 检查userLabel是否是一个类名
                    if user_label in self.symbol_mappings:
                        elem.attrib['userLabel'] = self.symbol_mappings[user_label]
                        replacements += 1

                # 6. P0修复: 更新restorationIdentifier
                # 状态恢复标识符，可能包含类名
                if 'restorationIdentifier' in elem.attrib:
                    restoration_id = elem.attrib['restorationIdentifier']
                    if restoration_id in self.symbol_mappings:
                        elem.attrib['restorationIdentifier'] = self.symbol_mappings[restoration_id]
                        replacements += 1

            if replacements > 0:
                tree.write(output_path, encoding='utf-8', xml_declaration=True)
                self.stats['storyboards_updated'] += 1
                return True

            return False

        except Exception as e:
            print(f"更新Storyboard失败 {storyboard_path}: {e}")
            return False

    def update_assets_catalog(self, assets_path: str, output_path: str = None) -> bool:
        """
        更新Assets.xcassets目录中的Contents.json文件

        Args:
            assets_path: Assets.xcassets目录路径
            output_path: 输出路径

        Returns:
            bool: 是否成功
        """
        try:
            if output_path is None:
                output_path = assets_path

            assets_dir = Path(assets_path)
            if not assets_dir.exists():
                return False

            updated = False

            # 遍历所有.imageset目录
            for imageset_dir in assets_dir.rglob("*.imageset"):
                contents_json = imageset_dir / "Contents.json"
                if contents_json.exists():
                    try:
                        with open(contents_json, 'r', encoding='utf-8') as f:
                            data = json.load(f)

                        # 更新图片文件名引用
                        if 'images' in data:
                            for image in data['images']:
                                if 'filename' in image:
                                    # 这里可以根据需要修改文件名
                                    pass

                        # 暂时不修改，只统计
                        updated = True

                    except Exception as e:
                        print(f"处理Contents.json失败 {contents_json}: {e}")

            return updated

        except Exception as e:
            print(f"更新Assets失败 {assets_path}: {e}")
            return False

    def update_plist(self, plist_path: str, output_path: str = None) -> bool:
        """
        更新Plist文件中的类名引用

        Args:
            plist_path: Plist文件路径
            output_path: 输出路径

        Returns:
            bool: 是否成功
        """
        try:
            if output_path is None:
                output_path = plist_path

            # 读取plist
            with open(plist_path, 'rb') as f:
                plist_data = plistlib.load(f)

            # 递归替换字典中的类名
            replacements = self._replace_in_plist(plist_data)

            if replacements > 0:
                # 保存修改后的plist
                with open(output_path, 'wb') as f:
                    plistlib.dump(plist_data, f)
                self.stats['plists_updated'] += 1
                return True

            return False

        except Exception as e:
            print(f"更新Plist失败 {plist_path}: {e}")
            return False

    def _replace_in_plist(self, obj) -> int:
        """递归替换plist中的值"""
        replacements = 0

        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, str) and value in self.symbol_mappings:
                    obj[key] = self.symbol_mappings[value]
                    replacements += 1
                elif isinstance(value, (dict, list)):
                    replacements += self._replace_in_plist(value)

        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                if isinstance(item, str) and item in self.symbol_mappings:
                    obj[i] = self.symbol_mappings[item]
                    replacements += 1
                elif isinstance(item, (dict, list)):
                    replacements += self._replace_in_plist(item)

        return replacements

    def process_resources(self, resource_files: List[str], output_dir: str,
                         modify_images: bool = True,
                         update_xibs: bool = True,
                         update_storyboards: bool = True,
                         update_plists: bool = True,
                         callback=None) -> Dict[str, bool]:
        """
        批量处理资源文件

        Args:
            resource_files: 资源文件路径列表
            output_dir: 输出目录
            modify_images: 是否修改图片hash
            update_xibs: 是否更新XIB
            update_storyboards: 是否更新Storyboard
            update_plists: 是否更新Plist
            callback: 进度回调

        Returns:
            Dict[str, bool]: {文件路径: 是否成功}
        """
        results = {}
        total = len(resource_files)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        for i, file_path in enumerate(resource_files, 1):
            file_path_obj = Path(file_path)
            output_file = output_path / file_path_obj.name

            success = False

            # 根据文件类型处理
            suffix = file_path_obj.suffix.lower()

            if suffix in ['.png', '.jpg', '.jpeg', '.gif'] and modify_images:
                success = self.modify_image_hash(file_path, str(output_file))

            elif suffix == '.xib' and update_xibs:
                success = self.update_xib(file_path, str(output_file))

            elif suffix == '.storyboard' and update_storyboards:
                success = self.update_storyboard(file_path, str(output_file))

            elif suffix == '.plist' and update_plists:
                success = self.update_plist(file_path, str(output_file))

            results[file_path] = success

            if callback:
                callback(i / total, file_path)

        return results

    def get_statistics(self) -> Dict:
        """获取处理统计信息"""
        return self.stats.copy()


if __name__ == "__main__":
    # 测试代码
    print("=== 资源文件处理器测试 ===\n")

    import tempfile

    # 创建测试XIB内容
    test_xib = """<?xml version="1.0" encoding="UTF-8"?>
<document type="com.apple.InterfaceBuilder3.CocoaTouch.XIB" version="3.0">
    <objects>
        <view customClass="MyCustomView" id="1">
            <subviews>
                <button customClass="MyButton" id="2"/>
            </subviews>
        </view>
        <placeholder customClass="MyViewController" id="3"/>
    </objects>
</document>
"""

    # 创建测试Storyboard内容
    test_storyboard = """<?xml version="1.0" encoding="UTF-8"?>
<document type="com.apple.InterfaceBuilder3.CocoaTouch.Storyboard.XIB" version="3.0">
    <scenes>
        <scene>
            <objects>
                <viewController customClass="MyViewController" storyboardIdentifier="MyVC" id="1">
                    <tableView>
                        <tableViewCell reuseIdentifier="MyCell" id="2"/>
                    </tableView>
                </viewController>
            </objects>
        </scene>
    </scenes>
</document>
"""

    # 符号映射
    symbol_mappings = {
        'MyCustomView': 'ABC123View',
        'MyButton': 'ABC456Button',
        'MyViewController': 'ABC789Controller',
        'MyCell': 'ABC000Cell',
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        # 1. 测试XIB更新
        print("1. 测试XIB更新:")
        xib_path = Path(tmpdir) / "test.xib"
        with open(xib_path, 'w') as f:
            f.write(test_xib)

        handler = ResourceHandler(symbol_mappings)
        success = handler.update_xib(str(xib_path))
        print(f"  更新XIB: {'成功' if success else '失败'}")

        if success:
            with open(xib_path, 'r') as f:
                updated_content = f.read()
            print("  更新后的部分内容:")
            for line in updated_content.split('\n')[2:6]:
                print(f"    {line}")

        # 2. 测试Storyboard更新
        print("\n2. 测试Storyboard更新:")
        storyboard_path = Path(tmpdir) / "test.storyboard"
        with open(storyboard_path, 'w') as f:
            f.write(test_storyboard)

        success = handler.update_storyboard(str(storyboard_path))
        print(f"  更新Storyboard: {'成功' if success else '失败'}")

        if success:
            with open(storyboard_path, 'r') as f:
                updated_content = f.read()
            print("  更新后包含的类名:")
            for mapping in symbol_mappings.items():
                if mapping[1] in updated_content:
                    print(f"    {mapping[0]} -> {mapping[1]} ✓")

        # 3. 测试图片hash修改
        print("\n3. 测试图片hash修改:")
        # 创建一个简单的测试图片文件（实际上是文本）
        image_path = Path(tmpdir) / "test.png"
        with open(image_path, 'wb') as f:
            f.write(b'\x89PNG\r\n\x1a\n' + b'test_image_data' * 10)

        original_hash = hashlib.md5(open(image_path, 'rb').read()).hexdigest()

        success = handler.modify_image_hash(str(image_path))
        print(f"  修改图片hash: {'成功' if success else '失败'}")

        if success:
            modified_hash = hashlib.md5(open(image_path, 'rb').read()).hexdigest()
            print(f"  原始hash: {original_hash}")
            print(f"  修改后hash: {modified_hash}")
            print(f"  hash已改变: {original_hash != modified_hash}")

        # 4. 统计信息
        print("\n4. 统计信息:")
        stats = handler.get_statistics()
        for key, value in stats.items():
            print(f"  {key}: {value}")

    print("\n=== 测试完成 ===")
