"""
字符串加密器 - 重构版本
使用独立的加密算法模块，简化核心逻辑

功能：
1. 识别代码中的字符串常量
2. 使用多种加密算法加密字符串
3. 生成运行时解密宏/函数
4. 支持白名单机制
"""

import re
import random
import string
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

try:
    from .encryption_algorithms import (
        EncryptionAlgorithm, CodeLanguage,
        EncryptionAlgorithmFactory, BaseEncryptionAlgorithm
    )
except ImportError:
    from encryption_algorithms import (
        EncryptionAlgorithm, CodeLanguage,
        EncryptionAlgorithmFactory, BaseEncryptionAlgorithm
    )


@dataclass
class EncryptedString:
    """加密字符串信息"""
    original: str                      # 原始字符串
    encrypted: str                     # 加密后的字符串
    algorithm: EncryptionAlgorithm     # 加密算法
    key: str                           # 加密密钥
    line_number: int                   # 所在行号
    file_path: str                     # 所在文件


@dataclass
class DecryptionMacro:
    """解密宏/函数"""
    name: str                          # 宏/函数名称
    algorithm: EncryptionAlgorithm     # 对应的加密算法
    code: str                          # 宏/函数代码
    language: CodeLanguage             # 语言


class StringEncryptor:
    """字符串加密器 - 重构版"""

    # 字符串匹配正则
    OBJC_STRING_PATTERN = r'@"([^"\\]*(?:\\.[^"\\]*)*)"'
    SWIFT_STRING_PATTERN = r'"([^"\\]*(?:\\.[^"\\]*)*)"'

    # 需要跳过的字符串模式
    SKIP_PATTERNS = [
        r'^(NS|UI|CA|CG|CF)[A-Z][a-zA-Z0-9]+$',  # 系统类名
        r'^[a-z]+:',              # URL scheme
        r'^\.',                   # 文件扩展名
        r'^/',                    # 路径
    ]

    def __init__(
        self,
        algorithm: EncryptionAlgorithm = EncryptionAlgorithm.XOR,
        language: CodeLanguage = CodeLanguage.OBJC,
        key: Optional[str] = None,
        min_length: int = 3,
        skip_short_strings: bool = True,
        whitelist: Optional[Set[str]] = None
    ):
        """
        初始化字符串加密器

        Args:
            algorithm: 加密算法
            language: 代码语言
            key: 加密密钥（None则随机生成）
            min_length: 最小加密字符串长度
            skip_short_strings: 是否跳过短字符串
            whitelist: 字符串白名单
        """
        self.algorithm = algorithm
        self.language = language
        self.key = key or self._generate_key()
        self.min_length = min_length
        self.skip_short_strings = skip_short_strings
        self.whitelist = whitelist or set()

        # 创建加密算法实例
        self.encryptor = EncryptionAlgorithmFactory.create(
            algorithm, self.key, language
        )

        # 统计信息
        self.stats = {
            'total_strings': 0,
            'encrypted_strings': 0,
            'skipped_strings': 0,
            'files_processed': 0
        }

    def _generate_key(self) -> str:
        """生成随机加密密钥"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=16))

    def _should_encrypt(self, content: str) -> bool:
        """
        判断字符串是否应该加密

        Args:
            content: 字符串内容

        Returns:
            bool: 是否应该加密
        """
        # 空字符串或太短
        if not content or (self.skip_short_strings and len(content) < self.min_length):
            return False

        # 在白名单中
        if content in self.whitelist:
            return False

        # 匹配跳过模式
        for pattern in self.SKIP_PATTERNS:
            if re.match(pattern, content):
                return False

        return True

    def encrypt_string(self, text: str) -> str:
        """
        加密字符串

        Args:
            text: 原始文本

        Returns:
            str: 加密后的文本
        """
        return self.encryptor.encrypt(text)

    def generate_decryption_macro(self) -> DecryptionMacro:
        """
        生成解密宏/函数

        Returns:
            DecryptionMacro: 解密宏
        """
        # 获取解密代码
        decryption_code = self.encryptor.get_decryption_code()

        # 根据算法类型确定宏名称
        algorithm_name = self.algorithm.value.upper()
        macro_name = f"DECRYPT_{algorithm_name}"

        return DecryptionMacro(
            name=macro_name,
            algorithm=self.algorithm,
            code=decryption_code,
            language=self.language
        )

    def process_file(self, file_path: str, content: str) -> Tuple[str, List[EncryptedString]]:
        """
        处理文件，加密其中的字符串

        Args:
            file_path: 文件路径
            content: 文件内容

        Returns:
            Tuple[str, List[EncryptedString]]: (处理后的内容, 加密字符串列表)
        """
        encrypted_strings = []

        # 选择正则模式
        if self.language == CodeLanguage.OBJC:
            pattern = self.OBJC_STRING_PATTERN
        else:
            pattern = self.SWIFT_STRING_PATTERN

        # 查找所有字符串
        lines = content.split('\n')
        new_lines = []

        for line_num, line in enumerate(lines, 1):
            new_line = line

            # 查找该行的所有字符串
            matches = list(re.finditer(pattern, line))
            self.stats['total_strings'] += len(matches)

            # 从后向前替换（避免位置偏移）
            for match in reversed(matches):
                string_content = match.group(1)  # 提取引号内的内容

                # 判断是否应该加密
                if self._should_encrypt(string_content):
                    try:
                        # 加密字符串
                        encrypted = self.encrypt_string(string_content)

                        # 记录加密信息
                        encrypted_strings.append(EncryptedString(
                            original=string_content,
                            encrypted=encrypted,
                            algorithm=self.algorithm,
                            key=self.key,
                            line_number=line_num,
                            file_path=file_path
                        ))

                        # 生成宏名称
                        macro_name = self.generate_decryption_macro().name

                        # 替换为解密宏调用
                        if self.language == CodeLanguage.OBJC:
                            replacement = f'{macro_name}(@"{encrypted}")'
                        else:
                            replacement = f'{macro_name}("{encrypted}")'

                        # 替换原字符串
                        start, end = match.span()
                        new_line = new_line[:start] + replacement + new_line[end:]

                        self.stats['encrypted_strings'] += 1

                    except Exception as e:
                        print(f"加密失败 {file_path}:{line_num} - {e}")
                        self.stats['skipped_strings'] += 1
                else:
                    self.stats['skipped_strings'] += 1

            new_lines.append(new_line)

        self.stats['files_processed'] += 1
        return '\n'.join(new_lines), encrypted_strings

    def get_statistics(self) -> Dict:
        """获取加密统计信息"""
        return self.stats.copy()


# 为了向后兼容，导出原有的类名
__all__ = [
    'StringEncryptor',
    'EncryptedString',
    'DecryptionMacro',
    'EncryptionAlgorithm',
    'CodeLanguage'
]
