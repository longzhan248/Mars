"""
结果导出器

负责保存混淆结果、P2后处理和映射文件导出
"""

import json
from pathlib import Path
from typing import Callable, Dict, List, Optional

try:
    from .common import ObfuscationResult
    from ..code_transformer import CodeTransformer, TransformResult
    from ..config_manager import ObfuscationConfig
    from ..incremental_manager import FileChangeType, IncrementalManager
    from ..name_generator import NameGenerator
    from ..project_analyzer import ProjectStructure
    from ..string_encryptor import CodeLanguage as StringCodeLanguage
    from ..string_encryptor import EncryptionAlgorithm, StringEncryptor
    from ..xcode_project_manager import XcodeProjectManager, check_pbxproj_availability
except ImportError:
    from common import ObfuscationResult
    from code_transformer import CodeTransformer, TransformResult
    from config_manager import ObfuscationConfig
    from incremental_manager import FileChangeType, IncrementalManager
    from name_generator import NameGenerator
    from project_analyzer import ProjectStructure
    from string_encryptor import CodeLanguage as StringCodeLanguage
    from string_encryptor import EncryptionAlgorithm, StringEncryptor
    from xcode_project_manager import XcodeProjectManager, check_pbxproj_availability


class ResultExporter:
    """结果导出器"""

    def __init__(self, config: ObfuscationConfig,
                 project_structure: ProjectStructure,
                 code_transformer: CodeTransformer,
                 name_generator: NameGenerator,
                 incremental_manager: Optional[IncrementalManager] = None):
        """
        初始化

        Args:
            config: 混淆配置
            project_structure: 项目结构
            code_transformer: 代码转换器
            name_generator: 名称生成器
            incremental_manager: 增量管理器
        """
        self.config = config
        self.project_structure = project_structure
        self.code_transformer = code_transformer
        self.name_generator = name_generator
        self.incremental_manager = incremental_manager

    def save_results(self, output_dir: str,
                    transform_results: Dict[str, TransformResult],
                    file_changes: Dict[FileChangeType, List[str]],
                    result: ObfuscationResult) -> bool:
        """
        保存混淆结果

        Args:
            output_dir: 输出目录
            transform_results: 转换结果
            file_changes: 文件变更
            result: 混淆结果对象

        Returns:
            bool: 是否成功
        """
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            # 保存源代码文件
            saved_count = 0
            failed_count = 0

            for file_path, transform_result in transform_results.items():
                if transform_result.errors:
                    failed_count += 1
                    continue

                try:
                    # 文件名同步重命名逻辑
                    original_path = Path(file_path)
                    file_stem = original_path.stem  # 文件名（不含扩展名）
                    file_suffix = original_path.suffix  # 扩展名（如 .m, .swift）

                    # 检查文件名（不含扩展名）是否是一个被混淆的类名
                    if file_stem in self.code_transformer.symbol_mappings:
                        # 使用混淆后的名称
                        obfuscated_stem = self.code_transformer.symbol_mappings[file_stem]
                        file_name = f"{obfuscated_stem}{file_suffix}"
                        print(f"  文件名同步: {original_path.name} -> {file_name}")
                    else:
                        # 保持原有的文件名
                        file_name = original_path.name

                    output_file = output_path / file_name

                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(transform_result.transformed_content)

                    saved_count += 1
                    result.total_replacements += transform_result.replacements

                except Exception as e:
                    print(f"保存文件失败 {file_path}: {e}")
                    failed_count += 1

            result.files_processed = saved_count
            result.files_failed = failed_count

            print(f"成功保存 {saved_count} 个文件，失败 {failed_count} 个")

            # P1增强：更新增量编译缓存
            if self.config.enable_incremental and self.incremental_manager:
                processed_files = list(transform_results.keys())
                deleted_files = file_changes.get(FileChangeType.DELETED, [])

                if self.incremental_manager.finalize(processed_files, deleted_files):
                    print("增量编译缓存已更新")
                else:
                    print("警告: 缓存更新失败")

            return saved_count > 0

        except Exception as e:
            print(f"保存结果失败: {e}")
            return False

    def p2_post_processing(self, output_dir: str,
                          transform_results: Dict[str, TransformResult],
                          files_with_encryption: Dict[str, List[str]],
                          garbage_files: Dict[str, List[str]],
                          encryption_algorithm: EncryptionAlgorithm,
                          encryption_key: str,
                          encryption_min_length: int,
                          progress_callback: Optional[Callable] = None):
        """
        P2深度集成后处理
        1. 为字符串加密生成统一的解密宏头文件
        2. 为所有加密文件添加解密宏导入
        3. 自动添加文件到Xcode项目

        Args:
            output_dir: 输出目录
            transform_results: 转换结果
            files_with_encryption: 需要加密的文件列表
            garbage_files: 垃圾文件列表
            encryption_algorithm: 加密算法
            encryption_key: 加密密钥
            encryption_min_length: 最小加密长度
            progress_callback: 进度回调
        """
        try:
            print("\n🔧 P2深度集成后处理...")

            # === 字符串加密后处理 ===
            if self.config.string_encryption:
                total_encrypted_files = len(files_with_encryption['objc']) + len(files_with_encryption['swift'])

                if total_encrypted_files > 0:
                    print(f"  处理 {total_encrypted_files} 个加密文件...")

                    output_path = Path(output_dir)

                    # 1. 生成ObjC解密宏头文件
                    if files_with_encryption['objc']:
                        print(f"  生成 Objective-C 解密宏头文件...")

                        # 创建ObjC版本的StringEncryptor获取解密宏
                        objc_encryptor = StringEncryptor(
                            algorithm=encryption_algorithm,
                            language=StringCodeLanguage.OBJC,
                            key=encryption_key,
                            min_length=encryption_min_length
                        )
                        objc_macro = objc_encryptor.generate_decryption_macro()

                        # 创建头文件
                        objc_header_file = output_path / "StringDecryption.h"
                        with open(objc_header_file, 'w', encoding='utf-8') as f:
                            f.write("//\n")
                            f.write("// StringDecryption.h\n")
                            f.write("// 字符串解密宏定义\n")
                            f.write("// 自动生成，请勿手动修改\n")
                            f.write("//\n\n")
                            f.write("#ifndef StringDecryption_h\n")
                            f.write("#define StringDecryption_h\n\n")
                            f.write(objc_macro.code)
                            f.write("\n\n#endif /* StringDecryption_h */\n")

                        print(f"    ✅ 创建头文件: {objc_header_file.name}")

                        # 2. 为所有ObjC加密文件添加导入
                        for file_path in files_with_encryption['objc']:
                            if file_path in transform_results:
                                transform_result = transform_results[file_path]
                                content = transform_result.transformed_content

                                # 在第一个import之后插入导入
                                lines = content.split('\n')
                                insert_index = 0

                                # 找到最后一个import的位置
                                for i, line in enumerate(lines):
                                    if line.strip().startswith(('#import', '@import')):
                                        insert_index = i + 1

                                # 插入导入语句
                                import_statement = f'#import "StringDecryption.h"'
                                if import_statement not in content:
                                    lines.insert(insert_index, import_statement)
                                    transform_result.transformed_content = '\n'.join(lines)
                                    print(f"    ✅ 添加导入: {Path(file_path).name}")

                    # 3. 生成Swift解密函数文件
                    if files_with_encryption['swift']:
                        print(f"  生成 Swift 解密函数文件...")

                        # 创建Swift版本的StringEncryptor获取解密函数
                        swift_encryptor = StringEncryptor(
                            algorithm=encryption_algorithm,
                            language=StringCodeLanguage.SWIFT,
                            key=encryption_key,
                            min_length=encryption_min_length
                        )
                        swift_function = swift_encryptor.generate_decryption_macro()

                        # 创建Swift文件
                        swift_file = output_path / "StringDecryption.swift"
                        with open(swift_file, 'w', encoding='utf-8') as f:
                            f.write("//\n")
                            f.write("// StringDecryption.swift\n")
                            f.write("// 字符串解密函数定义\n")
                            f.write("// 自动生成，请勿手动修改\n")
                            f.write("//\n\n")
                            f.write("import Foundation\n\n")
                            f.write(swift_function.code)

                        print(f"    ✅ 创建文件: {swift_file.name}")

                        # Swift不需要导入，因为在同一个模块内自动可见
                        print(f"    ℹ️  Swift文件自动可见，无需导入")

                    print(f"  ✅ 字符串加密后处理完成")

            # === 垃圾代码后处理 ===
            if self.config.insert_garbage_code and garbage_files:
                total_garbage_files = len(garbage_files['objc']) + len(garbage_files['swift'])

                if total_garbage_files > 0:
                    print(f"  垃圾代码文件已生成: {total_garbage_files} 个")
                    print(f"    - Objective-C: {len(garbage_files['objc'])} 个")
                    print(f"    - Swift: {len(garbage_files['swift'])} 个")

            # === Xcode项目文件自动添加 ===
            # 检查是否启用自动添加到Xcode项目（默认启用，可通过配置禁用）
            auto_add_to_xcode = getattr(self.config, 'auto_add_to_xcode', True)

            if auto_add_to_xcode and (garbage_files['objc'] or garbage_files['swift'] or
                                     files_with_encryption['objc'] or files_with_encryption['swift']):

                print(f"\n📦 自动添加文件到Xcode项目...")

                # 检查pbxproj库是否可用
                if not check_pbxproj_availability():
                    print(f"  ⚠️  mod-pbxproj库未安装，跳过自动添加")
                    print(f"  ℹ️  安装方法: pip install pbxproj")
                    print(f"  ℹ️  请手动将生成的文件添加到Xcode项目")
                else:
                    try:
                        # 初始化Xcode项目管理器
                        xcode_manager = XcodeProjectManager(self.project_structure.root_path)

                        if not xcode_manager.load_project():
                            print(f"  ⚠️  无法加载Xcode项目，跳过自动添加")
                            print(f"  ℹ️  请手动将生成的文件添加到Xcode项目")
                        else:
                            # 收集所有需要添加的文件
                            decryption_files = []
                            if files_with_encryption['objc']:
                                decryption_files.append(str(Path(output_dir) / "StringDecryption.h"))
                            if files_with_encryption['swift']:
                                decryption_files.append(str(Path(output_dir) / "StringDecryption.swift"))

                            # 获取目标target（使用第一个target）
                            targets = xcode_manager.get_targets()
                            target_name = targets[0] if targets else None

                            # 添加混淆生成的文件
                            garbage_results, decryption_results = xcode_manager.add_obfuscation_files(
                                garbage_files=garbage_files,
                                decryption_files=decryption_files,
                                target_name=target_name
                            )

                            # 保存项目修改
                            if xcode_manager.save_project():
                                # 打印摘要
                                xcode_manager.print_summary(garbage_results, decryption_results)
                                print(f"  ✅ 文件已自动添加到Xcode项目")
                            else:
                                print(f"  ⚠️  保存Xcode项目失败")
                                print(f"  ℹ️  请手动将生成的文件添加到Xcode项目")

                    except Exception as e:
                        print(f"  ⚠️  自动添加文件失败: {e}")
                        print(f"  ℹ️  请手动将生成的文件添加到Xcode项目")
            elif not auto_add_to_xcode:
                print(f"  ℹ️  自动添加功能已禁用")
                print(f"  ℹ️  请手动将生成的文件添加到Xcode项目")

            print(f"\n✅ P2深度集成后处理完成\n")

        except Exception as e:
            print(f"❌ P2后处理异常: {e}")
            import traceback
            traceback.print_exc()

    def export_mapping(self, output_dir: str,
                      files_with_encryption: Dict[str, List[str]],
                      garbage_files: Dict[str, List[str]],
                      total_encrypted_strings: int,
                      string_encryptor,
                      garbage_generator) -> str:
        """
        导出映射文件（包含P2统计信息）

        Args:
            output_dir: 输出目录
            files_with_encryption: 加密文件列表
            garbage_files: 垃圾文件列表
            total_encrypted_strings: 总加密字符串数
            string_encryptor: 字符串加密器
            garbage_generator: 垃圾代码生成器

        Returns:
            str: 映射文件路径
        """
        try:
            output_path = Path(output_dir)
            mapping_file = output_path / "obfuscation_mapping.json"

            # 导出名称映射
            self.name_generator.export_mappings(
                str(mapping_file),
                format=self.config.mapping_format
            )

            # 读取映射文件并添加P2统计信息
            if mapping_file.exists():
                with open(mapping_file, 'r', encoding='utf-8') as f:
                    mapping_data = json.load(f)

                # 添加P2统计信息
                if 'metadata' not in mapping_data:
                    mapping_data['metadata'] = {}

                # 字符串加密统计
                if string_encryptor:
                    encryption_stats = string_encryptor.get_statistics()
                    mapping_data['metadata']['string_encryption'] = {
                        'enabled': True,
                        'algorithm': encryption_stats.get('algorithm', 'unknown'),
                        'total_encrypted': total_encrypted_strings,  # 使用累积的总数
                        'objc_files': len(files_with_encryption['objc']),
                        'swift_files': len(files_with_encryption['swift']),
                        'decryption_header_objc': 'StringDecryption.h' if files_with_encryption['objc'] else None,
                        'decryption_file_swift': 'StringDecryption.swift' if files_with_encryption['swift'] else None
                    }

                # 垃圾代码统计
                if garbage_generator:
                    garbage_stats = garbage_generator.get_statistics()
                    mapping_data['metadata']['garbage_code'] = {
                        'enabled': True,
                        'complexity': getattr(self.config, 'garbage_complexity', 'moderate'),
                        'classes_generated': garbage_stats.get('classes_generated', 0),
                        'methods_generated': garbage_stats.get('methods_generated', 0),
                        'properties_generated': garbage_stats.get('properties_generated', 0),
                        'objc_files': len(garbage_files['objc']),
                        'swift_files': len(garbage_files['swift']),
                        'file_list': {
                            'objc': [Path(f).name for f in garbage_files['objc']],
                            'swift': [Path(f).name for f in garbage_files['swift']]
                        }
                    }

                # 保存更新后的映射文件
                with open(mapping_file, 'w', encoding='utf-8') as f:
                    json.dump(mapping_data, f, indent=2, ensure_ascii=False)

            print(f"映射文件已导出: {mapping_file}")
            return str(mapping_file)

        except Exception as e:
            print(f"导出映射失败: {e}")
            return ""
