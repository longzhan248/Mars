"""
字符串加密算法集合
提供多种加密算法的实现和解密代码生成
"""

from enum import Enum
from typing import Tuple
import base64


class EncryptionAlgorithm(Enum):
    """加密算法枚举"""
    BASE64 = "base64"
    XOR = "xor"
    SHIFT = "shift"
    ROT13 = "rot13"
    AES128 = "aes128"
    AES256 = "aes256"


class CodeLanguage(Enum):
    """编程语言"""
    OBJC = "objc"
    SWIFT = "swift"


class BaseEncryptionAlgorithm:
    """加密算法基类"""

    def __init__(self, key: str, language: CodeLanguage):
        """
        初始化加密算法

        Args:
            key: 加密密钥
            language: 目标代码语言
        """
        self.key = key
        self.language = language

    def encrypt(self, text: str) -> str:
        """
        加密文本

        Args:
            text: 原始文本

        Returns:
            str: 加密后的文本
        """
        raise NotImplementedError

    def get_decryption_code(self) -> str:
        """
        获取解密代码

        Returns:
            str: 解密函数代码
        """
        raise NotImplementedError


class Base64Algorithm(BaseEncryptionAlgorithm):
    """Base64加密算法"""

    def encrypt(self, text: str) -> str:
        """Base64编码"""
        return base64.b64encode(text.encode('utf-8')).decode('utf-8')

    def get_decryption_code(self) -> str:
        """生成Base64解密代码"""
        if self.language == CodeLanguage.OBJC:
            return '''
NSString* DecryptBase64(NSString* encrypted) {
    NSData *data = [[NSData alloc] initWithBase64EncodedString:encrypted options:0];
    return [[NSString alloc] initWithData:data encoding:NSUTF8StringEncoding];
}
'''
        else:  # Swift
            return '''
func decryptBase64(_ encrypted: String) -> String? {
    guard let data = Data(base64Encoded: encrypted) else { return nil }
    return String(data: data, encoding: .utf8)
}
'''


class XORAlgorithm(BaseEncryptionAlgorithm):
    """XOR加密算法"""

    def encrypt(self, text: str) -> str:
        """XOR加密"""
        key_bytes = self.key.encode('utf-8')
        text_bytes = text.encode('utf-8')

        encrypted = []
        for i, byte in enumerate(text_bytes):
            encrypted.append(byte ^ key_bytes[i % len(key_bytes)])

        return base64.b64encode(bytes(encrypted)).decode('utf-8')

    def get_decryption_code(self) -> str:
        """生成XOR解密代码"""
        key_hex = ''.join([f'\\x{ord(c):02x}' for c in self.key])

        if self.language == CodeLanguage.OBJC:
            return f'''
NSString* DecryptXOR(NSString* encrypted) {{
    const char key[] = "{key_hex}";
    const NSUInteger keyLen = {len(self.key)};

    NSData *data = [[NSData alloc] initWithBase64EncodedString:encrypted options:0];
    if (!data) return nil;

    NSMutableData *decrypted = [NSMutableData dataWithLength:data.length];
    const unsigned char *dataBytes = data.bytes;
    unsigned char *decryptedBytes = decrypted.mutableBytes;

    for (NSUInteger i = 0; i < data.length; i++) {{
        decryptedBytes[i] = dataBytes[i] ^ key[i % keyLen];
    }}

    return [[NSString alloc] initWithData:decrypted encoding:NSUTF8StringEncoding];
}}
'''
        else:  # Swift
            key_array = ', '.join([f'0x{ord(c):02x}' for c in self.key])
            return f'''
func decryptXOR(_ encrypted: String) -> String? {{
    let key: [UInt8] = [{key_array}]
    guard let data = Data(base64Encoded: encrypted) else {{ return nil }}

    var decrypted = [UInt8]()
    for (i, byte) in data.enumerated() {{
        decrypted.append(byte ^ key[i % key.count])
    }}

    return String(bytes: decrypted, encoding: .utf8)
}}
'''


class ShiftAlgorithm(BaseEncryptionAlgorithm):
    """移位加密算法"""

    def __init__(self, key: str, language: CodeLanguage, shift: int = 3):
        """
        初始化移位加密

        Args:
            key: 加密密钥（用于计算移位量）
            language: 目标代码语言
            shift: 移位量（默认3）
        """
        super().__init__(key, language)
        self.shift = shift if shift else (sum(ord(c) for c in key) % 26)

    def encrypt(self, text: str) -> str:
        """移位加密"""
        encrypted = []
        for char in text:
            if char.isalpha():
                # 字母移位
                base = ord('A') if char.isupper() else ord('a')
                shifted = (ord(char) - base + self.shift) % 26
                encrypted.append(chr(base + shifted))
            else:
                # 其他字符不变
                encrypted.append(char)

        return ''.join(encrypted)

    def get_decryption_code(self) -> str:
        """生成移位解密代码"""
        if self.language == CodeLanguage.OBJC:
            return f'''
NSString* DecryptShift(NSString* encrypted) {{
    const int shift = {self.shift};
    NSMutableString *result = [NSMutableString string];

    for (NSUInteger i = 0; i < encrypted.length; i++) {{
        unichar c = [encrypted characterAtIndex:i];

        if ((c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z')) {{
            unichar base = (c >= 'a') ? 'a' : 'A';
            c = (c - base - shift + 26) % 26 + base;
        }}

        [result appendFormat:@"%C", c];
    }}

    return result;
}}
'''
        else:  # Swift
            return f'''
func decryptShift(_ encrypted: String) -> String {{
    let shift = {self.shift}
    var result = ""

    for char in encrypted {{
        var c = char
        if char.isLetter {{
            let base: Unicode.Scalar = char.isUppercase ? "A" : "a"
            let shifted = (Int(char.unicodeScalars.first!.value) - Int(base.value) - shift + 26) % 26
            c = Character(Unicode.Scalar(Int(base.value) + shifted)!)
        }}
        result.append(c)
    }}

    return result
}}
'''


class ROT13Algorithm(BaseEncryptionAlgorithm):
    """ROT13加密算法（移位13）"""

    def encrypt(self, text: str) -> str:
        """ROT13加密"""
        encrypted = []
        for char in text:
            if char.isalpha():
                base = ord('A') if char.isupper() else ord('a')
                shifted = (ord(char) - base + 13) % 26
                encrypted.append(chr(base + shifted))
            else:
                encrypted.append(char)

        return ''.join(encrypted)

    def get_decryption_code(self) -> str:
        """生成ROT13解密代码（ROT13是对称的）"""
        if self.language == CodeLanguage.OBJC:
            return '''
NSString* DecryptROT13(NSString* encrypted) {
    NSMutableString *result = [NSMutableString string];

    for (NSUInteger i = 0; i < encrypted.length; i++) {
        unichar c = [encrypted characterAtIndex:i];

        if ((c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z')) {
            unichar base = (c >= 'a') ? 'a' : 'A';
            c = (c - base + 13) % 26 + base;
        }

        [result appendFormat:@"%C", c];
    }

    return result;
}
'''
        else:  # Swift
            return '''
func decryptROT13(_ encrypted: String) -> String {
    var result = ""

    for char in encrypted {
        var c = char
        if char.isLetter {
            let base: Unicode.Scalar = char.isUppercase ? "A" : "a"
            let shifted = (Int(char.unicodeScalars.first!.value) - Int(base.value) + 13) % 26
            c = Character(Unicode.Scalar(Int(base.value) + shifted)!)
        }
        result.append(c)
    }

    return result
}
'''


class EncryptionAlgorithmFactory:
    """加密算法工厂"""

    @staticmethod
    def create(algorithm: EncryptionAlgorithm,
               key: str,
               language: CodeLanguage) -> BaseEncryptionAlgorithm:
        """
        创建加密算法实例

        Args:
            algorithm: 算法类型
            key: 加密密钥
            language: 目标语言

        Returns:
            BaseEncryptionAlgorithm: 算法实例

        Raises:
            ValueError: 不支持的算法类型
        """
        if algorithm == EncryptionAlgorithm.BASE64:
            return Base64Algorithm(key, language)
        elif algorithm == EncryptionAlgorithm.XOR:
            return XORAlgorithm(key, language)
        elif algorithm == EncryptionAlgorithm.SHIFT:
            return ShiftAlgorithm(key, language)
        elif algorithm == EncryptionAlgorithm.ROT13:
            return ROT13Algorithm(key, language)
        elif algorithm == EncryptionAlgorithm.AES128:
            # AES需要额外的依赖，这里暂时抛出异常
            raise ValueError("AES128 加密需要安装 cryptography 库")
        elif algorithm == EncryptionAlgorithm.AES256:
            raise ValueError("AES256 加密需要安装 cryptography 库")
        else:
            raise ValueError(f"不支持的加密算法: {algorithm}")
