"""
资源处理器

负责处理Assets、XIB、图片、音频、字体等资源文件
"""

import os
from pathlib import Path
from typing import Callable, Dict, Optional

try:
    from ..code_transformer import CodeTransformer
    from ..config_manager import ObfuscationConfig
    from ..project_analyzer import ProjectStructure
    from ..resource_handlers.resource_coordinator import AdvancedResourceHandler
    from ..resource_handler import ResourceHandler
except ImportError:
    from code_transformer import CodeTransformer
    from config_manager import ObfuscationConfig
    from project_analyzer import ProjectStructure
    from resource_handlers.resource_coordinator import AdvancedResourceHandler
    from resource_handler import ResourceHandler


class ResourceProcessor:
    """资源处理器"""

    def __init__(self, config: ObfuscationConfig,
                 project_structure: ProjectStructure,
                 code_transformer: CodeTransformer):
        """
        初始化

        Args:
            config: 混淆配置
            project_structure: 项目结构
            code_transformer: 代码转换器
        """
        self.config = config
        self.project_structure = project_structure
        self.code_transformer = code_transformer

        self.resource_handler: Optional[ResourceHandler] = None
        self.advanced_resource_handler: Optional[AdvancedResourceHandler] = None

    def process_resources(self, progress_callback: Optional[Callable] = None):
        """
        处理资源文件（集成P2高级功能）

        Args:
            progress_callback: 进度回调
        """
        try:
            # 获取符号映射
            symbol_mappings = self.code_transformer.symbol_mappings

            # 初始化高级资源处理器（P2功能）
            self.advanced_resource_handler = AdvancedResourceHandler(
                symbol_mappings=symbol_mappings,
                image_intensity=self.config.image_intensity if hasattr(self.config, 'image_intensity') else 0.02
            )

            # 基础资源处理器（XIB/Storyboard）
            self.resource_handler = ResourceHandler(symbol_mappings)

            processed_count = 0

            # 步骤1: 处理Assets.xcassets（P2-1功能）
            if self.config.modify_resource_files:
                assets_path = Path(self.project_structure.root_path) / "Assets.xcassets"
                if assets_path.exists():
                    print(f"📦 处理Assets.xcassets...")
                    try:
                        # 使用process_assets_catalog方法
                        success = self.advanced_resource_handler.process_assets_catalog(str(assets_path))
                        if success:
                            print(f"  ✅ Assets处理成功")
                            processed_count += 1
                        else:
                            print(f"  ⚠️  Assets处理失败")
                    except Exception as e:
                        print(f"  ❌ Assets处理异常: {e}")

            # 步骤2: 处理XIB和Storyboard（基础功能）
            resource_files = []
            if self.config.modify_resource_files and hasattr(self.project_structure, 'xibs'):
                # 添加XIB和Storyboard
                for xib in self.project_structure.xibs:
                    if not xib.is_third_party:
                        resource_files.append(xib.path)

                for storyboard in self.project_structure.storyboards:
                    if not storyboard.is_third_party:
                        resource_files.append(storyboard.path)

                # 处理XIB/Storyboard文件
                if resource_files:
                    print(f"📄 处理 {len(resource_files)} 个XIB/Storyboard文件...")
                    for resource_file in resource_files:
                        try:
                            print(f"  处理: {Path(resource_file).name}")
                            # 注意: XIB/Storyboard类名同步更新功能待完善
                            # 当前resource_handler.py已有基础实现，需要集成到此处
                            # 参考: gui/modules/obfuscation/resource_handler.py
                            processed_count += 1
                        except Exception as e:
                            print(f"  ❌ 处理失败 {resource_file}: {e}")

            # 步骤3: 处理图片文件（P2-2功能）
            if self.config.modify_color_values:
                print(f"🖼️  处理图片文件...")
                image_extensions = ('.png', '.jpg', '.jpeg')
                image_count = 0

                for root, dirs, files in os.walk(self.project_structure.root_path):
                    # 跳过Assets.xcassets（已处理）和第三方库
                    if 'Assets.xcassets' in root or 'Pods' in root or 'Carthage' in root:
                        continue

                    for file in files:
                        if file.endswith(image_extensions):
                            image_path = os.path.join(root, file)
                            try:
                                result = self.advanced_resource_handler.modify_image_pixels(image_path)
                                if result.success:
                                    image_count += 1
                                    if image_count % 10 == 0:  # 每10张打印一次
                                        print(f"  已处理 {image_count} 张图片...")
                            except Exception as e:
                                print(f"  ⚠️  图片处理失败 {file}: {e}")

                if image_count > 0:
                    print(f"  ✅ 成功处理 {image_count} 张图片")
                    processed_count += image_count
                else:
                    print(f"  未找到需要处理的图片文件")

            # 步骤4: 处理音频文件（P2-3功能，可选）
            if hasattr(self.config, 'modify_audio_files') and self.config.modify_audio_files:
                print(f"🔊 处理音频文件...")
                audio_extensions = ('.mp3', '.m4a', '.wav', '.aiff')
                audio_count = 0

                for root, dirs, files in os.walk(self.project_structure.root_path):
                    # 跳过第三方库
                    if 'Pods' in root or 'Carthage' in root:
                        continue

                    for file in files:
                        if file.endswith(audio_extensions):
                            audio_path = os.path.join(root, file)
                            try:
                                result = self.advanced_resource_handler.modify_audio_hash(audio_path)
                                if result.success:
                                    audio_count += 1
                            except Exception as e:
                                print(f"  ⚠️  音频处理失败 {file}: {e}")

                if audio_count > 0:
                    print(f"  ✅ 成功处理 {audio_count} 个音频文件")
                    processed_count += audio_count

            # 步骤5: 处理字体文件（P2-4功能，可选）
            if hasattr(self.config, 'modify_font_files') and self.config.modify_font_files:
                print(f"🔤 处理字体文件...")
                font_extensions = ('.ttf', '.otf', '.ttc')
                font_count = 0

                for root, dirs, files in os.walk(self.project_structure.root_path):
                    # 跳过第三方库
                    if 'Pods' in root or 'Carthage' in root:
                        continue

                    for file in files:
                        if file.endswith(font_extensions):
                            font_path = os.path.join(root, file)
                            try:
                                result = self.advanced_resource_handler.process_font_file(font_path)
                                if result.success:
                                    font_count += 1
                            except Exception as e:
                                print(f"  ⚠️  字体处理失败 {file}: {e}")

                if font_count > 0:
                    print(f"  ✅ 成功处理 {font_count} 个字体文件")
                    processed_count += font_count

            # 输出统计
            if self.advanced_resource_handler:
                stats = self.advanced_resource_handler.get_statistics()
                print(f"\n📊 资源处理总结:")
                print(f"  总操作数: {stats.get('total_operations', 0)}")
                print(f"  成功: {stats.get('successful_operations', 0)}")
                print(f"  失败: {stats.get('failed_operations', 0)}")

                # Assets统计
                if 'assets' in stats and stats['assets'].get('imagesets_processed', 0) > 0:
                    assets = stats['assets']
                    print(f"  Assets处理:")
                    print(f"    - Imagesets: {assets.get('imagesets_processed', 0)}")
                    print(f"    - Colorsets: {assets.get('colorsets_processed', 0)}")
                    print(f"    - Datasets: {assets.get('datasets_processed', 0)}")

                # 图片统计
                if 'images' in stats and stats['images'].get('images_modified', 0) > 0:
                    images = stats['images']
                    print(f"  图片修改: {images['images_modified']} 张")
                    print(f"    - 像素调整: {images.get('pixels_adjusted', 0)}")

                # 音频统计
                if 'audio' in stats and stats['audio'].get('audio_files_modified', 0) > 0:
                    print(f"  音频修改: {stats['audio']['audio_files_modified']} 个")

                # 字体统计
                if 'fonts' in stats and stats['fonts'].get('fonts_processed', 0) > 0:
                    fonts = stats['fonts']
                    print(f"  字体处理: {fonts['fonts_processed']} 个")
                    if fonts.get('fonts_renamed', 0) > 0:
                        print(f"    - 重命名: {fonts['fonts_renamed']} 个")

            if processed_count == 0:
                print("未处理任何资源文件（可能未启用或无资源文件）")

        except Exception as e:
            print(f"❌ 资源处理异常: {e}")
            import traceback
            traceback.print_exc()
