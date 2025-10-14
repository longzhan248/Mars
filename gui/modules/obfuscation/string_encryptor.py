"""
字符串加密器 - 加密代码中的字符串常量以防止静态分析

功能：
1. 识别代码中的字符串常量
2. 使用多种加密算法加密字符串
3. 生成运行时解密宏/函数
4. 支持中文、表情符号、特殊字符
5. 防止静态分析工具读取字符串内容

设计目标：
- 支持Objective-C和Swift两种语言
- 多种加密算法可选（Base64、XOR、AES）
- 运行时解密，性能影响最小
- 加密密钥随机生成或固定种子
- 白名单机制，跳过系统API字符串
"""

import re
import base64
import hashlib
import os
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import random
import string

# 导入AES加密库
try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad, unpad
    from Crypto.Random import get_random_bytes
    AES_AVAILABLE = True
except ImportError:
    AES_AVAILABLE = False


class EncryptionAlgorithm(Enum):
    """加密算法"""
    BASE64 = "base64"          # Base64编码
    XOR = "xor"                # XOR异或加密
    SIMPLE_SHIFT = "shift"     # 简单位移加密
    ROT13 = "rot13"            # ROT13加密（字母）
    AES128 = "aes128"          # AES-128加密（需要pycryptodome）
    AES256 = "aes256"          # AES-256加密（需要pycryptodome）


class CodeLanguage(Enum):
    """代码语言"""
    OBJC = "objc"
    SWIFT = "swift"


@dataclass
class EncryptedString:
    """加密字符串"""
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
    """字符串加密器"""

    # 字符串匹配正则（使用非捕获组避免嵌套捕获）
    OBJC_STRING_PATTERN = r'@"([^"\\]*(?:\\.[^"\\]*)*)"'
    SWIFT_STRING_PATTERN = r'"([^"\\]*(?:\\.[^"\\]*)*)"'

    # 需要跳过的字符串模式（系统API相关）
    SKIP_PATTERNS = [
        r'^(NS|UI|CA|CG|CF)[A-Z][a-zA-Z0-9]+$',  # 明确的系统类名前缀
        r'^[a-z]+:',              # URL scheme (http:, https:, file: etc.)
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
            language: 目标语言
            key: 加密密钥（None则自动生成）
            min_length: 最小加密长度
            skip_short_strings: 是否跳过短字符串
            whitelist: 字符串白名单（不加密）
        """
        self.algorithm = algorithm
        self.language = language
        self.min_length = min_length
        self.skip_short_strings = skip_short_strings
        self.whitelist = whitelist or set()
        self.encrypted_strings: List[EncryptedString] = []

        # 生成或使用密钥
        if key:
            self.key = key
        else:
            self.key = self._generate_key()

    def _generate_key(self) -> str:
        """生成随机密钥"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=16))

    def _should_encrypt(self, content: str) -> bool:
        """
        判断是否应该加密该字符串

        Args:
            content: 字符串内容

        Returns:
            bool: 是否应该加密
        """
        # 空字符串
        if not content:
            return False

        # 长度过短
        if self.skip_short_strings and len(content) < self.min_length:
            return False

        # 在白名单中
        if content in self.whitelist:
            return False

        # 匹配跳过模式
        for pattern in self.SKIP_PATTERNS:
            if re.match(pattern, content):
                return False

        return True

    def _encrypt_base64(self, text: str) -> str:
        """Base64加密"""
        return base64.b64encode(text.encode('utf-8')).decode('utf-8')

    def _decrypt_base64_code(self) -> str:
        """生成Base64解密代码"""
        if self.language == CodeLanguage.OBJC:
            return '''
#define DECRYPT_STRING_B64(str) ({ \\
    NSData *data = [[NSData alloc] initWithBase64EncodedString:str options:0]; \\
    [[NSString alloc] initWithData:data encoding:NSUTF8StringEncoding]; \\
})
'''
        else:  # Swift
            return '''
func decryptStringB64(_ str: String) -> String {
    guard let data = Data(base64Encoded: str),
          let result = String(data: data, encoding: .utf8) else {
        return ""
    }
    return result
}
'''

    def _encrypt_xor(self, text: str) -> str:
        """XOR加密"""
        key_bytes = self.key.encode('utf-8')
        text_bytes = text.encode('utf-8')

        encrypted_bytes = []
        for i, byte in enumerate(text_bytes):
            key_byte = key_bytes[i % len(key_bytes)]
            encrypted_bytes.append(byte ^ key_byte)

        # 转换为十六进制字符串
        return ''.join(f'{b:02x}' for b in encrypted_bytes)

    def _decrypt_xor_code(self) -> str:
        """生成XOR解密代码"""
        # 生成密钥的十六进制表示
        key_hex = ''.join(f'{ord(c):02x}' for c in self.key)

        if self.language == CodeLanguage.OBJC:
            return f'''
#define XOR_KEY @"{key_hex}"

NSString* decryptStringXOR(NSString *encrypted) {{
    if (!encrypted || encrypted.length == 0) return @"";

    // 解析密钥
    NSMutableData *keyData = [NSMutableData data];
    for (int i = 0; i < XOR_KEY.length; i += 2) {{
        NSString *hexByte = [XOR_KEY substringWithRange:NSMakeRange(i, 2)];
        unsigned int byte;
        [[NSScanner scannerWithString:hexByte] scanHexInt:&byte];
        uint8_t b = byte;
        [keyData appendBytes:&b length:1];
    }}

    // 解析加密字符串
    NSMutableData *encryptedData = [NSMutableData data];
    for (int i = 0; i < encrypted.length; i += 2) {{
        NSString *hexByte = [encrypted substringWithRange:NSMakeRange(i, 2)];
        unsigned int byte;
        [[NSScanner scannerWithString:hexByte] scanHexInt:&byte];
        uint8_t b = byte;
        [encryptedData appendBytes:&b length:1];
    }}

    // XOR解密
    uint8_t *keyBytes = (uint8_t *)keyData.bytes;
    uint8_t *encBytes = (uint8_t *)encryptedData.bytes;
    NSMutableData *decrypted = [NSMutableData dataWithLength:encryptedData.length];
    uint8_t *decBytes = (uint8_t *)decrypted.mutableBytes;

    for (int i = 0; i < encryptedData.length; i++) {{
        decBytes[i] = encBytes[i] ^ keyBytes[i % keyData.length];
    }}

    return [[NSString alloc] initWithData:decrypted encoding:NSUTF8StringEncoding];
}}

#define DECRYPT_STRING_XOR(str) decryptStringXOR(str)
'''
        else:  # Swift
            return f'''
let XOR_KEY = "{key_hex}"

func decryptStringXOR(_ encrypted: String) -> String {{
    guard !encrypted.isEmpty else {{ return "" }}

    // 解析密钥
    var keyBytes: [UInt8] = []
    var index = XOR_KEY.startIndex
    while index < XOR_KEY.endIndex {{
        let nextIndex = XOR_KEY.index(index, offsetBy: 2)
        let hexByte = String(XOR_KEY[index..<nextIndex])
        if let byte = UInt8(hexByte, radix: 16) {{
            keyBytes.append(byte)
        }}
        index = nextIndex
    }}

    // 解析加密字符串
    var encryptedBytes: [UInt8] = []
    index = encrypted.startIndex
    while index < encrypted.endIndex {{
        let nextIndex = encrypted.index(index, offsetBy: 2)
        let hexByte = String(encrypted[index..<nextIndex])
        if let byte = UInt8(hexByte, radix: 16) {{
            encryptedBytes.append(byte)
        }}
        index = nextIndex
    }}

    // XOR解密
    var decryptedBytes: [UInt8] = []
    for (i, byte) in encryptedBytes.enumerated() {{
        let keyByte = keyBytes[i % keyBytes.count]
        decryptedBytes.append(byte ^ keyByte)
    }}

    return String(bytes: decryptedBytes, encoding: .utf8) ?? ""
}}
'''

    def _encrypt_shift(self, text: str) -> str:
        """简单位移加密"""
        shift = int(self.key[:2], 16) % 256  # 使用密钥的前2位确定位移量
        encrypted_bytes = []

        for char in text:
            code = ord(char)
            encrypted_code = (code + shift) % 65536  # Unicode范围
            encrypted_bytes.append(f'{encrypted_code:04x}')

        return ''.join(encrypted_bytes)

    def _decrypt_shift_code(self) -> str:
        """生成位移解密代码"""
        shift = int(self.key[:2], 16) % 256

        if self.language == CodeLanguage.OBJC:
            return f'''
#define SHIFT_KEY {shift}

NSString* decryptStringShift(NSString *encrypted) {{
    if (!encrypted || encrypted.length == 0) return @"";

    NSMutableString *decrypted = [NSMutableString string];

    for (int i = 0; i < encrypted.length; i += 4) {{
        NSString *hexCode = [encrypted substringWithRange:NSMakeRange(i, 4)];
        unsigned int code;
        [[NSScanner scannerWithString:hexCode] scanHexInt:&code];

        unichar original = (code - SHIFT_KEY + 65536) % 65536;
        [decrypted appendFormat:@"%C", original];
    }}

    return [decrypted copy];
}}

#define DECRYPT_STRING_SHIFT(str) decryptStringShift(str)
'''
        else:  # Swift
            return f'''
let SHIFT_KEY: Int = {shift}

func decryptStringShift(_ encrypted: String) -> String {{
    guard !encrypted.isEmpty else {{ return "" }}

    var decrypted = ""
    var index = encrypted.startIndex

    while index < encrypted.endIndex {{
        let nextIndex = encrypted.index(index, offsetBy: 4, limitedBy: encrypted.endIndex) ?? encrypted.endIndex
        let hexCode = String(encrypted[index..<nextIndex])

        if let code = Int(hexCode, radix: 16) {{
            let original = (code - SHIFT_KEY + 65536) % 65536
            if let scalar = UnicodeScalar(original) {{
                decrypted.append(Character(scalar))
            }}
        }}

        index = nextIndex
    }}

    return decrypted
}}
'''

    def _encrypt_aes128(self, text: str) -> str:
        """AES-128加密"""
        if not AES_AVAILABLE:
            raise ImportError("PyCryptodome库未安装，请运行: pip install pycryptodome")

        # 生成16字节密钥（AES-128）
        key_bytes = self.key.encode('utf-8')
        key = hashlib.md5(key_bytes).digest()  # 16字节

        # 生成随机IV
        iv = get_random_bytes(AES.block_size)

        # 创建AES加密器
        cipher = AES.new(key, AES.MODE_CBC, iv)

        # 填充并加密
        plaintext = text.encode('utf-8')
        ciphertext = cipher.encrypt(pad(plaintext, AES.block_size))

        # 返回 IV + 密文 的十六进制表示
        return (iv + ciphertext).hex()

    def _encrypt_aes256(self, text: str) -> str:
        """AES-256加密"""
        if not AES_AVAILABLE:
            raise ImportError("PyCryptodome库未安装，请运行: pip install pycryptodome")

        # 生成32字节密钥（AES-256）
        key_bytes = self.key.encode('utf-8')
        key = hashlib.sha256(key_bytes).digest()  # 32字节

        # 生成随机IV
        iv = get_random_bytes(AES.block_size)

        # 创建AES加密器
        cipher = AES.new(key, AES.MODE_CBC, iv)

        # 填充并加密
        plaintext = text.encode('utf-8')
        ciphertext = cipher.encrypt(pad(plaintext, AES.block_size))

        # 返回 IV + 密文 的十六进制表示
        return (iv + ciphertext).hex()

    def _decrypt_aes128_code(self) -> str:
        """生成AES-128解密代码"""
        # 生成密钥（与加密时相同）
        key_bytes = self.key.encode('utf-8')
        key_hex = hashlib.md5(key_bytes).hexdigest()

        if self.language == CodeLanguage.OBJC:
            return f'''
#import <CommonCrypto/CommonCrypto.h>

#define AES128_KEY @"{key_hex}"

NSString* decryptStringAES128(NSString *encrypted) {{
    if (!encrypted || encrypted.length == 0) return @"";

    // 解析密钥
    NSMutableData *keyData = [NSMutableData data];
    for (int i = 0; i < AES128_KEY.length; i += 2) {{
        NSString *hexByte = [AES128_KEY substringWithRange:NSMakeRange(i, 2)];
        unsigned int byte;
        [[NSScanner scannerWithString:hexByte] scanHexInt:&byte];
        uint8_t b = byte;
        [keyData appendBytes:&b length:1];
    }}

    // 解析加密数据（十六进制）
    NSMutableData *encryptedData = [NSMutableData data];
    for (int i = 0; i < encrypted.length; i += 2) {{
        NSString *hexByte = [encrypted substringWithRange:NSMakeRange(i, 2)];
        unsigned int byte;
        [[NSScanner scannerWithString:hexByte] scanHexInt:&byte];
        uint8_t b = byte;
        [encryptedData appendBytes:&b length:1];
    }}

    // 提取IV（前16字节）
    NSData *iv = [encryptedData subdataWithRange:NSMakeRange(0, kCCBlockSizeAES128)];
    NSData *ciphertext = [encryptedData subdataWithRange:NSMakeRange(kCCBlockSizeAES128, encryptedData.length - kCCBlockSizeAES128)];

    // 解密
    size_t bufferSize = ciphertext.length + kCCBlockSizeAES128;
    void *buffer = malloc(bufferSize);
    size_t numBytesDecrypted = 0;

    CCCryptorStatus cryptStatus = CCCrypt(kCCDecrypt,
                                          kCCAlgorithmAES128,
                                          kCCOptionPKCS7Padding,
                                          keyData.bytes,
                                          keyData.length,
                                          iv.bytes,
                                          ciphertext.bytes,
                                          ciphertext.length,
                                          buffer,
                                          bufferSize,
                                          &numBytesDecrypted);

    if (cryptStatus == kCCSuccess) {{
        NSData *decryptedData = [NSData dataWithBytes:buffer length:numBytesDecrypted];
        free(buffer);
        return [[NSString alloc] initWithData:decryptedData encoding:NSUTF8StringEncoding];
    }}

    free(buffer);
    return @"";
}}

#define DECRYPT_STRING_AES128(str) decryptStringAES128(str)
'''
        else:  # Swift
            return f'''
import CommonCrypto

let AES128_KEY = "{key_hex}"

func decryptStringAES128(_ encrypted: String) -> String {{
    guard !encrypted.isEmpty else {{ return "" }}

    // 解析密钥
    var keyBytes: [UInt8] = []
    var index = AES128_KEY.startIndex
    while index < AES128_KEY.endIndex {{
        let nextIndex = AES128_KEY.index(index, offsetBy: 2)
        let hexByte = String(AES128_KEY[index..<nextIndex])
        if let byte = UInt8(hexByte, radix: 16) {{
            keyBytes.append(byte)
        }}
        index = nextIndex
    }}

    // 解析加密数据
    var encryptedBytes: [UInt8] = []
    index = encrypted.startIndex
    while index < encrypted.endIndex {{
        let nextIndex = encrypted.index(index, offsetBy: 2)
        let hexByte = String(encrypted[index..<nextIndex])
        if let byte = UInt8(hexByte, radix: 16) {{
            encryptedBytes.append(byte)
        }}
        index = nextIndex
    }}

    // 提取IV和密文
    let ivSize = kCCBlockSizeAES128
    guard encryptedBytes.count > ivSize else {{ return "" }}

    let iv = Array(encryptedBytes[0..<ivSize])
    let ciphertext = Array(encryptedBytes[ivSize...])

    // 解密
    var decryptedBytes = [UInt8](repeating: 0, count: ciphertext.count + kCCBlockSizeAES128)
    var numBytesDecrypted = 0

    let cryptStatus = CCCrypt(
        CCOperation(kCCDecrypt),
        CCAlgorithm(kCCAlgorithmAES128),
        CCOptions(kCCOptionPKCS7Padding),
        keyBytes, keyBytes.count,
        iv,
        ciphertext, ciphertext.count,
        &decryptedBytes, decryptedBytes.count,
        &numBytesDecrypted
    )

    guard cryptStatus == kCCSuccess else {{ return "" }}

    let decryptedData = Data(bytes: decryptedBytes, count: numBytesDecrypted)
    return String(data: decryptedData, encoding: .utf8) ?? ""
}}
'''

    def _decrypt_aes256_code(self) -> str:
        """生成AES-256解密代码"""
        # 生成密钥（与加密时相同）
        key_bytes = self.key.encode('utf-8')
        key_hex = hashlib.sha256(key_bytes).hexdigest()

        if self.language == CodeLanguage.OBJC:
            return f'''
#import <CommonCrypto/CommonCrypto.h>

#define AES256_KEY @"{key_hex}"

NSString* decryptStringAES256(NSString *encrypted) {{
    if (!encrypted || encrypted.length == 0) return @"";

    // 解析密钥
    NSMutableData *keyData = [NSMutableData data];
    for (int i = 0; i < AES256_KEY.length; i += 2) {{
        NSString *hexByte = [AES256_KEY substringWithRange:NSMakeRange(i, 2)];
        unsigned int byte;
        [[NSScanner scannerWithString:hexByte] scanHexInt:&byte];
        uint8_t b = byte;
        [keyData appendBytes:&b length:1];
    }}

    // 解析加密数据（十六进制）
    NSMutableData *encryptedData = [NSMutableData data];
    for (int i = 0; i < encrypted.length; i += 2) {{
        NSString *hexByte = [encrypted substringWithRange:NSMakeRange(i, 2)];
        unsigned int byte;
        [[NSScanner scannerWithString:hexByte] scanHexInt:&byte];
        uint8_t b = byte;
        [encryptedData appendBytes:&b length:1];
    }}

    // 提取IV（前16字节）
    NSData *iv = [encryptedData subdataWithRange:NSMakeRange(0, kCCBlockSizeAES128)];
    NSData *ciphertext = [encryptedData subdataWithRange:NSMakeRange(kCCBlockSizeAES128, encryptedData.length - kCCBlockSizeAES128)];

    // 解密
    size_t bufferSize = ciphertext.length + kCCBlockSizeAES128;
    void *buffer = malloc(bufferSize);
    size_t numBytesDecrypted = 0;

    CCCryptorStatus cryptStatus = CCCrypt(kCCDecrypt,
                                          kCCAlgorithmAES,
                                          kCCOptionPKCS7Padding,
                                          keyData.bytes,
                                          keyData.length,
                                          iv.bytes,
                                          ciphertext.bytes,
                                          ciphertext.length,
                                          buffer,
                                          bufferSize,
                                          &numBytesDecrypted);

    if (cryptStatus == kCCSuccess) {{
        NSData *decryptedData = [NSData dataWithBytes:buffer length:numBytesDecrypted];
        free(buffer);
        return [[NSString alloc] initWithData:decryptedData encoding:NSUTF8StringEncoding];
    }}

    free(buffer);
    return @"";
}}

#define DECRYPT_STRING_AES256(str) decryptStringAES256(str)
'''
        else:  # Swift
            return f'''
import CommonCrypto

let AES256_KEY = "{key_hex}"

func decryptStringAES256(_ encrypted: String) -> String {{
    guard !encrypted.isEmpty else {{ return "" }}

    // 解析密钥
    var keyBytes: [UInt8] = []
    var index = AES256_KEY.startIndex
    while index < AES256_KEY.endIndex {{
        let nextIndex = AES256_KEY.index(index, offsetBy: 2)
        let hexByte = String(AES256_KEY[index..<nextIndex])
        if let byte = UInt8(hexByte, radix: 16) {{
            keyBytes.append(byte)
        }}
        index = nextIndex
    }}

    // 解析加密数据
    var encryptedBytes: [UInt8] = []
    index = encrypted.startIndex
    while index < encrypted.endIndex {{
        let nextIndex = encrypted.index(index, offsetBy: 2)
        let hexByte = String(encrypted[index..<nextIndex])
        if let byte = UInt8(hexByte, radix: 16) {{
            encryptedBytes.append(byte)
        }}
        index = nextIndex
    }}

    // 提取IV和密文
    let ivSize = kCCBlockSizeAES128
    guard encryptedBytes.count > ivSize else {{ return "" }}

    let iv = Array(encryptedBytes[0..<ivSize])
    let ciphertext = Array(encryptedBytes[ivSize...])

    // 解密
    var decryptedBytes = [UInt8](repeating: 0, count: ciphertext.count + kCCBlockSizeAES128)
    var numBytesDecrypted = 0

    let cryptStatus = CCCrypt(
        CCOperation(kCCDecrypt),
        CCAlgorithm(kCCAlgorithmAES),
        CCOptions(kCCOptionPKCS7Padding),
        keyBytes, keyBytes.count,
        iv,
        ciphertext, ciphertext.count,
        &decryptedBytes, decryptedBytes.count,
        &numBytesDecrypted
    )

    guard cryptStatus == kCCSuccess else {{ return "" }}

    let decryptedData = Data(bytes: decryptedBytes, count: numBytesDecrypted)
    return String(data: decryptedData, encoding: .utf8) ?? ""
}}
'''

    def _encrypt_rot13(self, text: str) -> str:
        """ROT13加密（仅对字母）"""
        result = []
        for char in text:
            if 'a' <= char <= 'z':
                result.append(chr((ord(char) - ord('a') + 13) % 26 + ord('a')))
            elif 'A' <= char <= 'Z':
                result.append(chr((ord(char) - ord('A') + 13) % 26 + ord('A')))
            else:
                result.append(char)
        # 对非字母字符使用Base64
        return base64.b64encode(''.join(result).encode('utf-8')).decode('utf-8')

    def _decrypt_rot13_code(self) -> str:
        """生成ROT13解密代码"""
        if self.language == CodeLanguage.OBJC:
            return '''
NSString* decryptStringROT13(NSString *encrypted) {{
    NSData *data = [[NSData alloc] initWithBase64EncodedString:encrypted options:0];
    NSString *decoded = [[NSString alloc] initWithData:data encoding:NSUTF8StringEncoding];

    NSMutableString *result = [NSMutableString string];
    for (int i = 0; i < decoded.length; i++) {{
        unichar ch = [decoded characterAtIndex:i];
        if (ch >= 'a' && ch <= 'z') {{
            [result appendFormat:@"%C", (unichar)((ch - 'a' + 13) % 26 + 'a')];
        }} else if (ch >= 'A' && ch <= 'Z') {{
            [result appendFormat:@"%C", (unichar)((ch - 'A' + 13) % 26 + 'A')];
        }} else {{
            [result appendFormat:@"%C", ch];
        }}
    }}

    return [result copy];
}}

#define DECRYPT_STRING_ROT13(str) decryptStringROT13(str)
'''
        else:  # Swift
            return '''
func decryptStringROT13(_ encrypted: String) -> String {{
    guard let data = Data(base64Encoded: encrypted),
          let decoded = String(data: data, encoding: .utf8) else {{
        return ""
    }}

    var result = ""
    for char in decoded {{
        if let ascii = char.asciiValue {{
            if ascii >= 97 && ascii <= 122 {{ // a-z
                result.append(Character(UnicodeScalar(((ascii - 97 + 13) % 26) + 97)))
            }} else if ascii >= 65 && ascii <= 90 {{ // A-Z
                result.append(Character(UnicodeScalar(((ascii - 65 + 13) % 26) + 65)))
            }} else {{
                result.append(char)
            }}
        }} else {{
            result.append(char)
        }}
    }}

    return result
}}
'''

    def encrypt_string(self, text: str) -> str:
        """
        加密字符串

        Args:
            text: 原始字符串

        Returns:
            str: 加密后的字符串
        """
        if self.algorithm == EncryptionAlgorithm.BASE64:
            return self._encrypt_base64(text)
        elif self.algorithm == EncryptionAlgorithm.XOR:
            return self._encrypt_xor(text)
        elif self.algorithm == EncryptionAlgorithm.SIMPLE_SHIFT:
            return self._encrypt_shift(text)
        elif self.algorithm == EncryptionAlgorithm.ROT13:
            return self._encrypt_rot13(text)
        elif self.algorithm == EncryptionAlgorithm.AES128:
            return self._encrypt_aes128(text)
        elif self.algorithm == EncryptionAlgorithm.AES256:
            return self._encrypt_aes256(text)
        else:
            return text

    def generate_decryption_macro(self) -> DecryptionMacro:
        """
        生成解密宏/函数

        Returns:
            DecryptionMacro: 解密宏
        """
        if self.algorithm == EncryptionAlgorithm.BASE64:
            code = self._decrypt_base64_code()
            name = "DECRYPT_STRING_B64" if self.language == CodeLanguage.OBJC else "decryptStringB64"
        elif self.algorithm == EncryptionAlgorithm.XOR:
            code = self._decrypt_xor_code()
            name = "DECRYPT_STRING_XOR" if self.language == CodeLanguage.OBJC else "decryptStringXOR"
        elif self.algorithm == EncryptionAlgorithm.SIMPLE_SHIFT:
            code = self._decrypt_shift_code()
            name = "DECRYPT_STRING_SHIFT" if self.language == CodeLanguage.OBJC else "decryptStringShift"
        elif self.algorithm == EncryptionAlgorithm.ROT13:
            code = self._decrypt_rot13_code()
            name = "DECRYPT_STRING_ROT13" if self.language == CodeLanguage.OBJC else "decryptStringROT13"
        elif self.algorithm == EncryptionAlgorithm.AES128:
            code = self._decrypt_aes128_code()
            name = "DECRYPT_STRING_AES128" if self.language == CodeLanguage.OBJC else "decryptStringAES128"
        elif self.algorithm == EncryptionAlgorithm.AES256:
            code = self._decrypt_aes256_code()
            name = "DECRYPT_STRING_AES256" if self.language == CodeLanguage.OBJC else "decryptStringAES256"
        else:
            code = ""
            name = ""

        return DecryptionMacro(
            name=name,
            algorithm=self.algorithm,
            code=code,
            language=self.language
        )

    def process_file(self, file_path: str, content: str) -> Tuple[str, List[EncryptedString]]:
        """
        处理文件中的字符串

        Args:
            file_path: 文件路径
            content: 文件内容

        Returns:
            Tuple[str, List[EncryptedString]]: (处理后的内容, 加密字符串列表)
        """
        pattern = self.OBJC_STRING_PATTERN if self.language == CodeLanguage.OBJC else self.SWIFT_STRING_PATTERN

        encrypted_strings = []
        processed_content = content

        # 查找所有字符串
        matches = list(re.finditer(pattern, content))

        # 从后往前替换，避免位置偏移
        for match in reversed(matches):
            string_content = match.group(1)

            # 判断是否需要加密
            if not self._should_encrypt(string_content):
                continue

            # 加密字符串
            encrypted = self.encrypt_string(string_content)

            # 生成替换代码
            if self.language == CodeLanguage.OBJC:
                if self.algorithm == EncryptionAlgorithm.BASE64:
                    replacement = f'DECRYPT_STRING_B64(@"{encrypted}")'
                elif self.algorithm == EncryptionAlgorithm.XOR:
                    replacement = f'DECRYPT_STRING_XOR(@"{encrypted}")'
                elif self.algorithm == EncryptionAlgorithm.SIMPLE_SHIFT:
                    replacement = f'DECRYPT_STRING_SHIFT(@"{encrypted}")'
                elif self.algorithm == EncryptionAlgorithm.ROT13:
                    replacement = f'DECRYPT_STRING_ROT13(@"{encrypted}")'
                elif self.algorithm == EncryptionAlgorithm.AES128:
                    replacement = f'DECRYPT_STRING_AES128(@"{encrypted}")'
                elif self.algorithm == EncryptionAlgorithm.AES256:
                    replacement = f'DECRYPT_STRING_AES256(@"{encrypted}")'
                else:
                    replacement = f'@"{encrypted}"'
            else:  # Swift
                if self.algorithm == EncryptionAlgorithm.BASE64:
                    replacement = f'decryptStringB64("{encrypted}")'
                elif self.algorithm == EncryptionAlgorithm.XOR:
                    replacement = f'decryptStringXOR("{encrypted}")'
                elif self.algorithm == EncryptionAlgorithm.SIMPLE_SHIFT:
                    replacement = f'decryptStringShift("{encrypted}")'
                elif self.algorithm == EncryptionAlgorithm.ROT13:
                    replacement = f'decryptStringROT13("{encrypted}")'
                elif self.algorithm == EncryptionAlgorithm.AES128:
                    replacement = f'decryptStringAES128("{encrypted}")'
                elif self.algorithm == EncryptionAlgorithm.AES256:
                    replacement = f'decryptStringAES256("{encrypted}")'
                else:
                    replacement = f'"{encrypted}"'

            # 替换
            start = match.start()
            end = match.end()
            processed_content = processed_content[:start] + replacement + processed_content[end:]

            # 记录
            line_number = content[:start].count('\n') + 1
            encrypted_strings.append(EncryptedString(
                original=string_content,
                encrypted=encrypted,
                algorithm=self.algorithm,
                key=self.key,
                line_number=line_number,
                file_path=file_path
            ))

        self.encrypted_strings.extend(encrypted_strings)
        return processed_content, encrypted_strings

    def get_statistics(self) -> Dict:
        """
        获取加密统计信息

        Returns:
            Dict: 统计信息
        """
        return {
            'total_encrypted': len(self.encrypted_strings),
            'algorithm': self.algorithm.value,
            'language': self.language.value,
            'key': self.key,
            'files': len(set(e.file_path for e in self.encrypted_strings))
        }


if __name__ == "__main__":
    print("=== 字符串加密器测试 ===\n")

    # 测试Objective-C XOR加密
    print("1. 测试Objective-C XOR加密:")
    objc_code = '''
@implementation MyClass

- (void)testMethod {
    NSString *message = @"Hello World";
    NSString *title = @"Test Title";
    NSLog(@"Debug: %@", @"Some message");
}

@end
'''

    encryptor = StringEncryptor(
        algorithm=EncryptionAlgorithm.XOR,
        language=CodeLanguage.OBJC,
        key="TestKey123"
    )

    processed, encrypted_list = encryptor.process_file("MyClass.m", objc_code)
    print(f"加密字符串数: {len(encrypted_list)}")
    for e in encrypted_list:
        print(f"  行{e.line_number}: '{e.original}' -> '{e.encrypted[:20]}...'")

    print("\n解密宏:")
    macro = encryptor.generate_decryption_macro()
    print(macro.code[:200] + "...")

    # 测试Swift Base64加密
    print("\n2. 测试Swift Base64加密:")
    swift_code = '''
class MyClass {
    func testMethod() {
        let message = "Hello Swift"
        let url = "https://example.com"
        print("Debug: \\(message)")
    }
}
'''

    swift_encryptor = StringEncryptor(
        algorithm=EncryptionAlgorithm.BASE64,
        language=CodeLanguage.SWIFT
    )

    processed_swift, encrypted_swift = swift_encryptor.process_file("MyClass.swift", swift_code)
    print(f"加密字符串数: {len(encrypted_swift)}")
    for e in encrypted_swift:
        print(f"  行{e.line_number}: '{e.original}' -> '{e.encrypted}'")

    # 测试白名单
    print("\n3. 测试白名单功能:")
    whitelist_encryptor = StringEncryptor(
        algorithm=EncryptionAlgorithm.XOR,
        language=CodeLanguage.OBJC,
        whitelist={"Hello World", "Test Title"}
    )

    _, encrypted_whitelist = whitelist_encryptor.process_file("Test.m", objc_code)
    print(f"使用白名单后加密字符串数: {len(encrypted_whitelist)}")

    # 测试统计
    print("\n4. 统计信息:")
    stats = encryptor.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\n=== 测试完成 ===")
