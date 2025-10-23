"""
P2功能处理器

负责字符串加密和垃圾代码生成（P2深度集成功能）
"""

from pathlib import Path
from typing import Callable, Dict, List, Optional

try:
    from ..code_transformer import TransformResult
    from ..config_manager import ObfuscationConfig
    from ..garbage_generator import (
        CodeLanguage as GarbageCodeLanguage,
        ComplexityLevel,
        GarbageCodeGenerator,
    )
    from ..string_encryptor import (
        CodeLanguage as StringCodeLanguage,
        EncryptionAlgorithm,
        StringEncryptor,
    )
except ImportError:
    from code_transformer import TransformResult
    from config_manager import ObfuscationConfig
    from garbage_generator import (
        CodeLanguage as GarbageCodeLanguage,
        ComplexityLevel,
        GarbageCodeGenerator,
    )
    from string_encryptor import (
        CodeLanguage as StringCodeLanguage,
        EncryptionAlgorithm,
        StringEncryptor,
    )


class FeatureProcessor:
    """P2功能处理器"""

    def __init__(self, config: ObfuscationConfig):
        """
        初始化

        Args:
            config: 混淆配置
        """
        self.config = config
        self.string_encryptor: Optional[StringEncryptor] = None
        self.garbage_generator: Optional[GarbageCodeGenerator] = None

        # P2深度集成 - 存储需要特殊处理的文件
        self.files_with_encryption: Dict[str, List[str]] = {'objc': [], 'swift': []}
        self.garbage_files: Dict[str, List[str]] = {'objc': [], 'swift': []}
        self.total_encrypted_strings: int = 0

        # 保存加密配置供后续P2后处理使用
        self.encryption_algorithm = None
        self.encryption_key = None
        self.encryption_min_length = None

    def encrypt_strings(self, transform_results: Dict[str, TransformResult],
                       progress_callback: Optional[Callable] = None):
        """
        加密字符串（P2功能 - 深度集成）

        Args:
            transform_results: 代码转换结果
            progress_callback: 进度回调
        """
        try:
            print("\n🔐 开始字符串加密...")

            # 确定加密算法
            algorithm_map = {
                'base64': EncryptionAlgorithm.BASE64,
                'xor': EncryptionAlgorithm.XOR,
                'shift': EncryptionAlgorithm.SIMPLE_SHIFT,
                'rot13': EncryptionAlgorithm.ROT13,
                'aes128': EncryptionAlgorithm.AES128,
                'aes256': EncryptionAlgorithm.AES256,
            }

            algorithm = algorithm_map.get(
                getattr(self.config, 'encryption_algorithm', 'xor'),
                EncryptionAlgorithm.XOR
            )

            # 获取加密配置参数
            encryption_key = getattr(self.config, 'encryption_key', 'DefaultKey')
            encryption_min_length = getattr(self.config, 'string_min_length', 4)
            encryption_whitelist = set(getattr(self.config, 'string_whitelist_patterns', []))

            # 保存加密配置供后续P2后处理使用
            self.encryption_algorithm = algorithm
            self.encryption_key = encryption_key
            self.encryption_min_length = encryption_min_length

            # 对每个已转换的文件进行字符串加密
            total_files = len(transform_results)
            processed_files = 0
            total_encrypted = 0
            objc_files_with_encryption = []
            swift_files_with_encryption = []

            for file_path, transform_result in transform_results.items():
                try:
                    # 获取文件语言
                    is_swift = file_path.endswith('.swift')
                    language = StringCodeLanguage.SWIFT if is_swift else StringCodeLanguage.OBJC

                    # 为每种语言创建对应的StringEncryptor
                    file_encryptor = StringEncryptor(
                        algorithm=algorithm,
                        language=language,
                        key=encryption_key,
                        min_length=encryption_min_length,
                        whitelist=encryption_whitelist
                    )

                    # 对转换后的内容进行字符串加密
                    encrypted_content, encrypted_strings = file_encryptor.process_file(
                        file_path,
                        transform_result.transformed_content
                    )

                    # 保存第一个encryptor供统计使用
                    if self.string_encryptor is None:
                        self.string_encryptor = file_encryptor

                    # 如果有字符串被加密，记录文件并更新内容
                    if encrypted_strings:
                        # 更新转换结果（不在这里插入解密代码，稍后统一处理）
                        transform_result.transformed_content = encrypted_content
                        total_encrypted += len(encrypted_strings)
                        self.total_encrypted_strings += len(encrypted_strings)  # 累积总数

                        if is_swift:
                            swift_files_with_encryption.append(file_path)
                        else:
                            objc_files_with_encryption.append(file_path)

                        print(f"  ✅ {Path(file_path).name}: 加密 {len(encrypted_strings)} 个字符串")

                    processed_files += 1

                    # 更新进度
                    if progress_callback and total_files > 0:
                        progress = processed_files / total_files
                        total_progress = 0.6 + progress * 0.05
                        progress_callback(total_progress, f"加密字符串: {Path(file_path).name}")

                except Exception as e:
                    print(f"  ⚠️  字符串加密失败 {Path(file_path).name}: {e}")

            # 存储需要添加解密代码的文件列表
            self.files_with_encryption = {
                'objc': objc_files_with_encryption,
                'swift': swift_files_with_encryption
            }

            # 输出统计
            if self.string_encryptor:
                stats = self.string_encryptor.get_statistics()
                print(f"\n📊 字符串加密总结:")
                print(f"  处理文件: {processed_files}/{total_files}")
                print(f"  加密字符串: {total_encrypted} 个")
                print(f"  ObjC文件: {len(objc_files_with_encryption)} 个")
                print(f"  Swift文件: {len(swift_files_with_encryption)} 个")
                print(f"  检测字符串: {stats.get('total_strings_detected', 0)} 个")
                print(f"  跳过字符串: {stats.get('strings_skipped', 0)} 个")
                print(f"  过滤比例: {stats.get('strings_skipped', 0) / max(stats.get('total_strings_detected', 1), 1) * 100:.1f}%")

        except Exception as e:
            print(f"❌ 字符串加密异常: {e}")
            import traceback
            traceback.print_exc()

    def insert_garbage_code(self, transform_results: Dict[str, TransformResult],
                           output_dir: str,
                           progress_callback: Optional[Callable] = None):
        """
        插入垃圾代码（P2功能 - 深度集成）

        Args:
            transform_results: 代码转换结果
            output_dir: 输出目录
            progress_callback: 进度回调
        """
        try:
            print("\n🗑️  开始生成垃圾代码...")

            # 确定复杂度级别
            complexity_map = {
                'simple': ComplexityLevel.SIMPLE,
                'moderate': ComplexityLevel.MODERATE,
                'complex': ComplexityLevel.COMPLEX,
            }

            complexity = complexity_map.get(
                getattr(self.config, 'garbage_complexity', 'moderate'),
                ComplexityLevel.MODERATE
            )

            # 确定生成数量
            garbage_count = getattr(self.config, 'garbage_count', 20)

            # 分别为ObjC和Swift生成垃圾代码
            objc_files = [f for f in transform_results.keys() if f.endswith(('.m', '.mm'))]
            swift_files = [f for f in transform_results.keys() if f.endswith('.swift')]

            # 存储生成的垃圾文件信息（完整路径）
            self.garbage_files = {
                'objc': [],
                'swift': []
            }

            # 生成Objective-C垃圾代码
            if objc_files and garbage_count > 0:
                print(f"  生成 Objective-C 垃圾代码...")
                self.garbage_generator = GarbageCodeGenerator(
                    language=GarbageCodeLanguage.OBJC,
                    complexity=complexity,
                    name_prefix=getattr(self.config, 'garbage_prefix', 'GC'),
                    seed=self.config.fixed_seed if self.config.use_fixed_seed else None
                )

                # 生成垃圾类
                garbage_classes = self.garbage_generator.generate_classes(count=garbage_count)

                # 导出到文件
                output_path = Path(output_dir)
                output_path.mkdir(parents=True, exist_ok=True)

                files_dict = self.garbage_generator.export_to_files(str(output_path))
                # 存储完整的文件路径（files_dict的values是完整路径）
                self.garbage_files['objc'] = list(files_dict.values())

                print(f"  ✅ 生成了 {len(garbage_classes)} 个 Objective-C 垃圾类")
                print(f"  ✅ 导出了 {len(files_dict)} 个文件")

            # 生成Swift垃圾代码
            if swift_files and garbage_count > 0:
                print(f"  生成 Swift 垃圾代码...")
                swift_generator = GarbageCodeGenerator(
                    language=GarbageCodeLanguage.SWIFT,
                    complexity=complexity,
                    name_prefix=getattr(self.config, 'garbage_prefix', 'GC'),
                    seed=self.config.fixed_seed if self.config.use_fixed_seed else None
                )

                # 生成垃圾类
                garbage_classes = swift_generator.generate_classes(count=garbage_count)

                # 导出到文件
                output_path = Path(output_dir)
                files_dict = swift_generator.export_to_files(str(output_path))
                # 存储完整的文件路径
                self.garbage_files['swift'] = list(files_dict.values())

                print(f"  ✅ 生成了 {len(garbage_classes)} 个 Swift 垃圾类")
                print(f"  ✅ 导出了 {len(files_dict)} 个文件")

            # 输出统计
            if self.garbage_generator:
                stats = self.garbage_generator.get_statistics()
                total_garbage_files = len(self.garbage_files['objc']) + len(self.garbage_files['swift'])
                print(f"\n📊 垃圾代码生成总结:")
                print(f"  生成类: {stats.get('classes_generated', 0)} 个")
                print(f"  生成方法: {stats.get('methods_generated', 0)} 个")
                print(f"  生成属性: {stats.get('properties_generated', 0)} 个")
                print(f"  导出文件: {total_garbage_files} 个")

        except Exception as e:
            print(f"❌ 垃圾代码生成异常: {e}")
            import traceback
            traceback.print_exc()
