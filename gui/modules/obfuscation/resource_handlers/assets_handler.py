"""
Assets.xcassets高级处理器

功能:
- 图片资源重命名
- 颜色资源处理
- 数据资源处理
- Contents.json更新

作者: Claude Code
日期: 2025-10-14
版本: v2.3.0
"""

import json
import random
import shutil
from pathlib import Path
from typing import Dict


class AdvancedAssetsHandler:
    """
    Assets.xcassets高级处理器

    功能:
    - 图片资源重命名
    - 颜色资源处理
    - 数据资源处理
    - Contents.json更新
    """

    def __init__(self, symbol_mappings: Dict[str, str] = None):
        """
        初始化Assets处理器

        Args:
            symbol_mappings: 符号映射字典（用于资源名称混淆）
        """
        self.symbol_mappings = symbol_mappings or {}
        self.stats = {
            'imagesets_processed': 0,
            'colorsets_processed': 0,
            'datasets_processed': 0,
            'images_renamed': 0,
            'contents_updated': 0,
        }

    def process_assets_catalog(self, assets_path: str, output_path: str = None,
                              rename_images: bool = True,
                              process_colors: bool = True,
                              process_data: bool = True) -> bool:
        """
        完整处理Assets.xcassets目录

        Args:
            assets_path: Assets.xcassets目录路径
            output_path: 输出路径，如果为None则覆盖原目录
            rename_images: 是否重命名图片资源
            process_colors: 是否处理颜色资源
            process_data: 是否处理数据资源

        Returns:
            bool: 是否成功
        """
        try:
            if output_path is None:
                output_path = assets_path

            assets_dir = Path(assets_path)
            if not assets_dir.exists():
                return False

            output_dir = Path(output_path)

            # 处理所有imageset
            if rename_images:
                for imageset_dir in assets_dir.rglob("*.imageset"):
                    self._process_imageset(imageset_dir, output_dir)

            # 处理所有colorset
            if process_colors:
                for colorset_dir in assets_dir.rglob("*.colorset"):
                    self._process_colorset(colorset_dir, output_dir)

            # 处理所有dataset
            if process_data:
                for dataset_dir in assets_dir.rglob("*.dataset"):
                    self._process_dataset(dataset_dir, output_dir)

            return True

        except Exception as e:
            print(f"处理Assets目录失败 {assets_path}: {e}")
            return False

    def _process_imageset(self, imageset_dir: Path, output_dir: Path) -> bool:
        """
        处理单个imageset（完整版 - P3改进）

        Args:
            imageset_dir: imageset目录
            output_dir: 输出根目录

        Returns:
            bool: 是否成功
        """
        try:
            contents_json = imageset_dir / "Contents.json"
            if not contents_json.exists():
                return False

            # 1. 读取Contents.json
            with open(contents_json, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 2. 确定输出路径
            imageset_name = imageset_dir.stem.replace('.imageset', '')
            new_name = self.symbol_mappings.get(imageset_name, imageset_name)

            # 3. 创建输出目录
            # 计算相对于Assets.xcassets的相对路径
            try:
                rel_path = imageset_dir.relative_to(imageset_dir.parent)
                while not str(rel_path).endswith('.xcassets'):
                    if rel_path.parent == rel_path:
                        break
                    rel_path = imageset_dir.relative_to(rel_path.parent.parent)
            except:
                rel_path = imageset_dir.relative_to(imageset_dir.parent)

            # 构建输出路径
            output_imageset = output_dir / rel_path.parent / f"{new_name}.imageset"
            output_imageset.mkdir(parents=True, exist_ok=True)

            # 4. 复制图片文件
            if 'images' in data:
                for image_info in data['images']:
                    if 'filename' in image_info:
                        src_file = imageset_dir / image_info['filename']
                        dst_file = output_imageset / image_info['filename']

                        if src_file.exists():
                            shutil.copy2(src_file, dst_file)

            # 5. 保存Contents.json
            output_json = output_imageset / "Contents.json"
            with open(output_json, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # 6. 更新统计
            if new_name != imageset_name:
                self.stats['images_renamed'] += 1
            self.stats['imagesets_processed'] += 1
            self.stats['contents_updated'] += 1

            return True

        except Exception as e:
            print(f"处理imageset失败 {imageset_dir}: {e}")
            return False

    def _process_colorset(self, colorset_dir: Path, output_dir: Path) -> bool:
        """
        处理单个colorset（完整版 - P3改进）

        Args:
            colorset_dir: colorset目录
            output_dir: 输出根目录

        Returns:
            bool: 是否成功
        """
        try:
            contents_json = colorset_dir / "Contents.json"
            if not contents_json.exists():
                return False

            # 1. 读取Contents.json
            with open(contents_json, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 2. 轻微修改颜色值（不影响视觉效果）
            if 'colors' in data:
                for color_info in data['colors']:
                    if 'color' in color_info:
                        color = color_info['color']
                        if 'components' in color:
                            # 对RGB值进行微小调整（±0.01）
                            for key in ['red', 'green', 'blue']:
                                if key in color['components']:
                                    value = float(color['components'][key])
                                    # 添加微小的随机变化（±0.005）
                                    adjustment = random.uniform(-0.005, 0.005)
                                    new_value = max(0.0, min(1.0, value + adjustment))
                                    color['components'][key] = f"{new_value:.3f}"

            # 3. 确定输出路径
            colorset_name = colorset_dir.stem.replace('.colorset', '')
            new_name = self.symbol_mappings.get(colorset_name, colorset_name)

            # 4. 计算相对于Assets.xcassets的相对路径
            try:
                rel_path = colorset_dir.relative_to(colorset_dir.parent)
                while not str(rel_path).endswith('.xcassets'):
                    if rel_path.parent == rel_path:
                        break
                    rel_path = colorset_dir.relative_to(rel_path.parent.parent)
            except:
                rel_path = colorset_dir.relative_to(colorset_dir.parent)

            # 5. 创建输出目录
            output_colorset = output_dir / rel_path.parent / f"{new_name}.colorset"
            output_colorset.mkdir(parents=True, exist_ok=True)

            # 6. 保存修改后的Contents.json
            output_json = output_colorset / "Contents.json"
            with open(output_json, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # 7. 更新统计
            if new_name != colorset_name:
                self.stats['images_renamed'] += 1
            self.stats['colorsets_processed'] += 1
            self.stats['contents_updated'] += 1

            return True

        except Exception as e:
            print(f"处理colorset失败 {colorset_dir}: {e}")
            return False

    def _process_dataset(self, dataset_dir: Path, output_dir: Path) -> bool:
        """
        处理单个dataset（完整版 - P3改进）

        Args:
            dataset_dir: dataset目录
            output_dir: 输出根目录

        Returns:
            bool: 是否成功
        """
        try:
            contents_json = dataset_dir / "Contents.json"
            if not contents_json.exists():
                return False

            # 1. 读取Contents.json
            with open(contents_json, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 2. 确定输出路径
            dataset_name = dataset_dir.stem.replace('.dataset', '')
            new_name = self.symbol_mappings.get(dataset_name, dataset_name)

            # 3. 计算相对于Assets.xcassets的相对路径
            try:
                rel_path = dataset_dir.relative_to(dataset_dir.parent)
                while not str(rel_path).endswith('.xcassets'):
                    if rel_path.parent == rel_path:
                        break
                    rel_path = dataset_dir.relative_to(rel_path.parent.parent)
            except:
                rel_path = dataset_dir.relative_to(dataset_dir.parent)

            # 4. 创建输出目录
            output_dataset = output_dir / rel_path.parent / f"{new_name}.dataset"
            output_dataset.mkdir(parents=True, exist_ok=True)

            # 5. 复制数据文件
            if 'data' in data:
                for data_info in data['data']:
                    if 'filename' in data_info:
                        src_file = dataset_dir / data_info['filename']
                        dst_file = output_dataset / data_info['filename']

                        if src_file.exists():
                            shutil.copy2(src_file, dst_file)

            # 6. 保存Contents.json
            output_json = output_dataset / "Contents.json"
            with open(output_json, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # 7. 更新统计
            if new_name != dataset_name:
                self.stats['images_renamed'] += 1
            self.stats['datasets_processed'] += 1
            self.stats['contents_updated'] += 1

            return True

        except Exception as e:
            print(f"处理dataset失败 {dataset_dir}: {e}")
            return False

    def get_statistics(self) -> Dict:
        """获取处理统计信息"""
        return self.stats.copy()
