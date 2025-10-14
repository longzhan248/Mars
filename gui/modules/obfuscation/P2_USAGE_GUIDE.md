# iOS代码混淆P2高级功能使用指南

## 概述

P2高级功能为iOS代码混淆模块提供了两个强大的混淆增强工具：
1. **垃圾代码生成** (Garbage Code Generation) - 生成无用但合法的类、方法、属性以增加逆向工程难度
2. **字符串加密** (String Encryption) - 加密代码中的字符串常量，防止明文泄露敏感信息

这两个功能可以单独使用，也可以组合使用，为您的iOS应用提供更强的代码保护。

## 功能特性

### 垃圾代码生成

**作用**：向项目中插入大量无用但合法的代码，增加代码复杂度，误导静态分析工具。

**特点**：
- ✅ 支持Objective-C和Swift两种语言
- ✅ 三种复杂度级别（simple/moderate/complex）
- ✅ 生成的代码语法正确，能通过编译
- ✅ 不影响应用原有功能
- ✅ 可配置生成数量和命名前缀
- ✅ 确定性生成（支持固定种子）

**生成内容**：
- 类 (Classes): 包含属性和方法的完整类定义
- 属性 (Properties): 各种类型的属性声明
- 方法 (Methods): 从简单到复杂的方法实现
  - Simple: 基本返回语句
  - Moderate: 包含条件语句和循环
  - Complex: 嵌套循环、switch语句、多层逻辑

### 字符串加密

**作用**：加密代码中的字符串常量，防止通过静态分析获取敏感信息。

**特点**：
- ✅ 四种加密算法（XOR/Base64/Shift/ROT13）
- ✅ 支持Objective-C和Swift
- ✅ 自动生成解密宏/函数
- ✅ 智能过滤（白名单、最小长度）
- ✅ 完整Unicode支持（中文、emoji）
- ✅ 可配置加密密钥

**加密示例**：
```objective-c
// 原始代码
NSString *message = @"Hello World";

// 加密后（XOR算法）
#define DECRYPT_STRING(str) /* 解密宏定义 */
NSString *message = DECRYPT_STRING(@"1c001f1824452e5e405f30");
```

## GUI使用指南

### 1. 打开混淆标签页

启动Mars日志分析器主程序，切换到"代码混淆"标签页。

### 2. 配置P2选项

#### 方式一：使用预设模板

在"配置模板"下拉框中选择：
- **最小化** (minimal): 禁用所有P2功能，适合快速测试
- **标准** (standard): 启用垃圾代码(20类/中等复杂度)，禁用字符串加密
- **激进** (aggressive): 启用垃圾代码(20类/高复杂度) + 字符串加密(XOR)

#### 方式二：自定义配置

**垃圾代码配置**：
1. 勾选"插入垃圾代码 🆕"复选框
2. 配置参数：
   - **垃圾类数**: 5-100（默认20）
     - 说明：生成多少个无用类文件
     - 建议值：小项目10-20，中项目20-30，大项目30-50
     - 影响：数量越多混淆越强，但编译时间会增加（每个类约1-5KB）
     - 示例：设置为20，会生成GCClass1.h/m ~ GCClass20.h/m共40个文件

   - **复杂度**: simple/moderate/complex
     - **simple** (简单):
       - 生成基础类和方法，只包含简单返回语句
       - 编译快速，适合快速开发阶段
       - 示例：`return @"result";` 或 `return YES;`

     - **moderate** (中等):
       - 包含条件语句（if/else）和循环（for/while）
       - 平衡混淆效果和编译时间，适合测试阶段
       - 示例：包含5-10行逻辑代码，带循环和条件判断

     - **complex** (复杂):
       - 嵌套循环、switch语句、多层逻辑
       - 最强混淆效果但编译较慢，适合正式发布
       - 示例：包含10-20行代码，多重嵌套结构

**字符串加密配置**：
1. 勾选"字符串加密 🆕"复选框
2. 配置参数：
   - **加密算法**: xor/base64/shift/rot13
     - **xor** (异或加密，推荐):
       - 安全性和性能平衡好，常用于敏感信息
       - 示例：`@"Hello"` → `@"1c001f1824452e5e"`
       - 适用场景：API密钥、密码、敏感URL

     - **base64** (Base64编码):
       - 轻量级编码（非加密），适合混淆但不敏感的字符串
       - 示例：`@"Hello"` → `@"SGVsbG8="`
       - 适用场景：日志消息、提示文本

     - **shift** (移位加密):
       - 简单快速的字符移位
       - 示例：`@"Hello"` → `@"Ifmmp"`（每个字符+1）
       - 适用场景：大量普通字符串

     - **rot13** (ROT13编码):
       - 最简单的旋转编码
       - 示例：`@"Hello"` → `@"Uryyb"`
       - 适用场景：仅需简单混淆的非敏感信息

   - **最小长度**: 1-20（默认4）
     - 说明：只加密长度大于等于此值的字符串
     - 推荐值：
       - **1**: 加密所有字符串（包括"Yes"、"No"等），用于敏感信息保护
       - **4-6**: 平衡性能和效果，跳过"OK"、"Yes"等超短字符串
       - **8-10**: 只加密较长字符串，减少性能开销
     - 示例：设置为4时，"Hi"(2字符)不加密，"Hello"(5字符)会加密
     - 性能影响：值越小加密越多字符串，解密开销越大

### 3. 运行混淆

1. 选择iOS项目路径
2. 选择输出目录
3. 点击"开始混淆"按钮
4. 观察进度条和日志输出

### 4. 查看结果

混淆完成后：
- **垃圾代码文件**: 输出目录中会生成 `GCClassN.h` 和 `GCClassN.m` 文件
- **字符串加密**: 原始代码中的字符串被替换为加密形式，并生成解密宏
- **映射文件**: 点击"查看映射"按钮查看详细的混淆映射

## 命令行使用指南

### 基础用法

```bash
# 启用垃圾代码（使用默认配置）
python -m gui.modules.obfuscation.obfuscation_cli \
    --project /path/to/project \
    --output /path/to/output \
    --insert-garbage-code

# 启用字符串加密（使用默认配置）
python -m gui.modules.obfuscation.obfuscation_cli \
    --project /path/to/project \
    --output /path/to/output \
    --string-encryption
```

### 自定义配置

```bash
# 完整P2配置示例
python -m gui.modules.obfuscation.obfuscation_cli \
    --project /path/to/project \
    --output /path/to/output \
    --insert-garbage-code \
    --garbage-count 30 \
    --garbage-complexity complex \
    --garbage-prefix "JUNK" \
    --string-encryption \
    --encryption-algorithm xor \
    --encryption-key "MySecretKey123" \
    --string-min-length 5
```

### 使用配置文件

```bash
# 创建配置文件 config.json
{
  "insert_garbage_code": true,
  "garbage_count": 25,
  "garbage_complexity": "moderate",
  "garbage_prefix": "GC",
  "string_encryption": true,
  "encryption_algorithm": "xor",
  "encryption_key": "ProjectKey",
  "string_min_length": 4
}

# 使用配置文件
python -m gui.modules.obfuscation.obfuscation_cli \
    --project /path/to/project \
    --output /path/to/output \
    --config-file config.json
```

## Python API使用指南

### 垃圾代码生成

```python
from gui.modules.obfuscation.garbage_generator import (
    GarbageCodeGenerator,
    CodeLanguage,
    ComplexityLevel
)

# 1. 创建生成器
generator = GarbageCodeGenerator(
    language=CodeLanguage.OBJC,      # 或 CodeLanguage.SWIFT
    complexity=ComplexityLevel.MODERATE,  # SIMPLE, MODERATE, COMPLEX
    name_prefix="GC",                 # 类名前缀
    seed="my_project_v1.0"           # 可选：确定性生成
)

# 2. 生成垃圾类
classes = generator.generate_classes(
    count=20,              # 生成20个类
    min_properties=2,      # 每个类最少2个属性
    max_properties=5,      # 每个类最多5个属性
    min_methods=3,         # 每个类最少3个方法
    max_methods=8          # 每个类最多8个方法
)

print(f"生成了 {len(classes)} 个垃圾类")

# 3. 导出到文件
output_dir = "/path/to/output"
files_dict = generator.export_to_files(output_dir)

# 4. 查看统计信息
stats = generator.get_statistics()
print(f"生成类: {stats['classes_generated']}")
print(f"生成属性: {stats['properties_generated']}")
print(f"生成方法: {stats['methods_generated']}")
print(f"导出文件: {stats['files_exported']}")

# 5. 查看生成的代码（预览）
for gc in classes[:2]:  # 查看前两个类
    if generator.language == CodeLanguage.OBJC:
        header, impl = gc.generate_code()
        print(f"=== {gc.name}.h ===")
        print(header[:500])  # 显示头文件前500字符
    else:
        code = gc.generate_code()
        print(f"=== {gc.name}.swift ===")
        print(code[:500])
```

### 字符串加密

```python
from gui.modules.obfuscation.string_encryptor import (
    StringEncryptor,
    EncryptionAlgorithm,
    CodeLanguage as StringLanguage
)

# 1. 创建加密器
encryptor = StringEncryptor(
    algorithm=EncryptionAlgorithm.XOR,  # XOR, BASE64, SIMPLE_SHIFT, ROT13
    key="MySecretKey",                   # 加密密钥
    language=StringLanguage.OBJC,        # 或 StringLanguage.SWIFT
    min_length=4,                        # 最小字符串长度
    whitelist=["NSLog", "UILabel"]       # 白名单（不加密这些字符串）
)

# 2. 处理单个文件
file_path = "MyViewController.m"
with open(file_path, 'r', encoding='utf-8') as f:
    original_code = f.read()

# 加密字符串
encrypted_code, encrypted_list = encryptor.process_file(file_path, original_code)

print(f"加密了 {len(encrypted_list)} 个字符串")
for enc_str in encrypted_list[:5]:  # 显示前5个
    print(f"  '{enc_str.original}' -> '{enc_str.encrypted}'")

# 3. 生成解密宏/函数
decryption_macro = encryptor.generate_decryption_macro()
print(f"\n解密宏名称: {decryption_macro.name}")
print(f"算法: {decryption_macro.algorithm}")
print(f"语言: {decryption_macro.language}")
print("\n解密宏代码:")
print(decryption_macro.code)

# 4. 保存加密后的代码
with open(file_path + ".encrypted", 'w', encoding='utf-8') as f:
    # 先写入解密宏
    f.write(decryption_macro.code + "\n\n")
    # 再写入加密后的代码
    f.write(encrypted_code)

# 5. 查看统计信息
stats = encryptor.get_statistics()
print(f"\n加密统计:")
print(f"  总加密字符串: {stats['total_encrypted']}")
print(f"  算法: {stats['algorithm']}")
print(f"  语言: {stats['language']}")
print(f"  密钥: {stats['key']}")
```

### 批量处理多个文件

```python
import os
from pathlib import Path

# 初始化加密器
encryptor = StringEncryptor(
    algorithm=EncryptionAlgorithm.XOR,
    key="ProjectKey",
    language=StringLanguage.OBJC
)

# 生成解密宏（只需一次）
decryption_macro = encryptor.generate_decryption_macro()

# 创建专门存放解密宏的头文件
macro_header_path = "/path/to/output/StringDecryption.h"
with open(macro_header_path, 'w', encoding='utf-8') as f:
    f.write(decryption_macro.code)

# 批量处理所有.m文件
project_dir = Path("/path/to/project")
output_dir = Path("/path/to/output")

total_encrypted = 0
for m_file in project_dir.glob("**/*.m"):
    # 跳过第三方库
    if "Pods/" in str(m_file):
        continue

    # 读取原始文件
    with open(m_file, 'r', encoding='utf-8') as f:
        original_code = f.read()

    # 加密字符串
    encrypted_code, encrypted_list = encryptor.process_file(str(m_file), original_code)
    total_encrypted += len(encrypted_list)

    # 保存到输出目录（保持目录结构）
    relative_path = m_file.relative_to(project_dir)
    output_path = output_dir / relative_path
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        # 在文件开头导入解密宏头文件
        f.write('#import "StringDecryption.h"\n\n')
        f.write(encrypted_code)

    print(f"处理 {m_file.name}: {len(encrypted_list)} 个字符串")

print(f"\n总共加密 {total_encrypted} 个字符串")
```

## 最佳实践

### 垃圾代码生成

#### 推荐配置

**快速开发阶段**：
- 垃圾类数: 10-15
- 复杂度: simple
- 理由: 快速编译，不影响开发效率

**测试阶段**：
- 垃圾类数: 20-30
- 复杂度: moderate
- 理由: 平衡混淆效果和编译时间

**正式发布**：
- 垃圾类数: 30-50
- 复杂度: complex
- 理由: 最强混淆效果，应对审核

#### 注意事项

1. **编译时间**: 垃圾类数量和复杂度会影响编译时间，建议逐步增加
2. **应用体积**: 垃圾代码会略微增加应用体积（每个类约1-5KB）
3. **固定种子**: 建议使用固定种子，保证版本迭代时的一致性
4. **命名冲突**: 确保垃圾代码前缀与现有代码不冲突

### 字符串加密

#### 推荐配置

**敏感信息**：
- 算法: xor
- 密钥: 使用项目特定密钥
- 最小长度: 1（加密所有字符串）
- 示例: API密钥、密码、敏感URL

**普通字符串**：
- 算法: base64 或 rot13
- 密钥: 使用默认密钥
- 最小长度: 4-8（只加密较长的字符串）
- 示例: 日志消息、提示文本

#### 注意事项

1. **白名单管理**:
   - 系统类名（如 NSLog, UILabel）不应加密
   - 第三方库类名不应加密
   - 使用白名单防止误加密

2. **最小长度设置**:
   - 太小会加密过多短字符串，增加性能开销
   - 太大会遗漏中等长度的敏感信息
   - 推荐值: 4-6

3. **加密算法选择**:
   - **XOR**: 最常用，安全性和性能平衡好
   - **Base64**: 编码而非加密，适合混淆但不敏感的字符串
   - **Shift**: 简单快速，适合大量字符串
   - **ROT13**: 仅用于非敏感信息

4. **Unicode支持**: 所有算法都支持中文、emoji等Unicode字符

### 组合使用

**推荐组合方案**：

```python
# 标准方案（日常开发）
config = {
    "insert_garbage_code": True,
    "garbage_count": 20,
    "garbage_complexity": "moderate",
    "string_encryption": False  # 开发阶段禁用
}

# 强化方案（提审前）
config = {
    "insert_garbage_code": True,
    "garbage_count": 30,
    "garbage_complexity": "complex",
    "string_encryption": True,
    "encryption_algorithm": "xor",
    "encryption_key": "ProjectKey_v1.0",
    "string_min_length": 4
}

# 极致方案（被拒后）
config = {
    "insert_garbage_code": True,
    "garbage_count": 50,
    "garbage_complexity": "complex",
    "string_encryption": True,
    "encryption_algorithm": "xor",
    "encryption_key": "ProjectKey_v1.1_enhanced",
    "string_min_length": 1  # 加密所有字符串
}
```

## 常见问题

### Q1: 垃圾代码会影响应用性能吗？

**答**: 不会。垃圾代码不会在运行时执行，只是增加了代码体积和静态分析难度。

### Q2: 字符串加密会降低运行性能吗？

**答**: 有轻微影响。解密操作会在首次访问字符串时执行，但性能开销很小（微秒级）。对于高频访问的字符串，建议使用白名单排除。

### Q3: 如何确定使用多少垃圾类？

**答**:
- 小型项目（<100个类）: 10-20个
- 中型项目（100-500个类）: 20-30个
- 大型项目（>500个类）: 30-50个

### Q4: 字符串加密后如何调试？

**答**:
1. 开发阶段禁用字符串加密
2. 或在日志输出前解密字符串
3. 混淆后保存映射文件，记录原始字符串

### Q5: 垃圾代码会被编译器优化掉吗？

**答**: 不会。垃圾代码包含真实的类定义和方法实现，会被完整编译到二进制中。即使启用编译器优化，这些代码也会保留。

### Q6: 可以只对部分文件使用P2功能吗？

**答**: 可以。使用Python API单独处理特定文件，或配置白名单排除不需要混淆的目录。

### Q7: 字符串加密支持国际化字符串吗？

**答**: 支持。所有加密算法都完整支持Unicode，包括中文、日文、emoji等。

### Q8: 如何验证P2功能生效？

**答**:
1. **垃圾代码**: 检查输出目录中的 `GCClassN.h/m` 文件
2. **字符串加密**: 搜索 `DECRYPT_STRING` 宏或加密后的十六进制字符串

## 进阶用法

### 自定义垃圾代码生成器

```python
class CustomGarbageGenerator(GarbageCodeGenerator):
    """自定义垃圾代码生成器"""

    def generate_method_name(self):
        """生成与项目命名风格一致的方法名"""
        # 使用项目特定的方法名词汇
        project_prefixes = ["fetch", "update", "process", "handle"]
        project_suffixes = ["DataModel", "Configuration", "Service"]
        prefix = random.choice(project_prefixes)
        suffix = random.choice(project_suffixes)
        return f"{prefix}{suffix}"

    def generate_class_name(self):
        """生成与项目命名风格一致的类名"""
        # 使用项目特定的类名模式
        return f"{self.name_prefix}{random.choice(['Manager', 'Helper', 'Service'])}{self.class_name_index}"

# 使用自定义生成器
custom_gen = CustomGarbageGenerator(
    language=CodeLanguage.OBJC,
    complexity=ComplexityLevel.MODERATE
)
classes = custom_gen.generate_classes(count=20)
```

### 自定义字符串加密算法

```python
from gui.modules.obfuscation.string_encryptor import EncryptionAlgorithm

class CustomEncryptor(StringEncryptor):
    """自定义字符串加密器"""

    def encrypt_string(self, text, key):
        """自定义加密算法"""
        # 实现您自己的加密逻辑
        # 例如：结合XOR和Base64
        xor_result = self._xor_encrypt(text, key)
        return base64.b64encode(xor_result.encode()).decode()

    def generate_decryption_code(self, language):
        """生成对应的解密代码"""
        if language == "objc":
            return """
// Custom decryption macro
#define CUSTOM_DECRYPT_STRING(str) DecryptCustomString(str, @"key")
static inline NSString* DecryptCustomString(NSString *encrypted, NSString *key) {
    // 实现解密逻辑
    NSData *base64Data = [[NSData alloc] initWithBase64EncodedString:encrypted options:0];
    // ... XOR解密
    return decryptedString;
}
"""
        else:
            return """
// Custom decryption function
func customDecryptString(_ encrypted: String, key: String) -> String {
    // 实现解密逻辑
    guard let base64Data = Data(base64Encoded: encrypted) else { return "" }
    // ... XOR解密
    return decryptedString
}
"""

# 使用自定义加密器
custom_encryptor = CustomEncryptor(
    algorithm=EncryptionAlgorithm.XOR,  # 作为基础算法
    key="CustomKey"
)
```

## 总结

P2高级功能为iOS代码混淆提供了强大的辅助工具：
- ✅ **垃圾代码生成**: 增加代码复杂度，误导静态分析
- ✅ **字符串加密**: 保护敏感信息，防止明文泄露
- ✅ **灵活配置**: GUI和CLI两种接口，满足不同需求
- ✅ **确定性混淆**: 支持固定种子，版本迭代一致
- ✅ **完整测试**: 39个单元测试 + 5个集成测试，质量有保障

建议根据项目阶段和需求选择合适的配置方案，逐步增强混淆力度，最终通过机器审核！

## 相关资源

- [主文档](CLAUDE.md) - iOS代码混淆模块完整技术文档
- [垃圾代码生成器](garbage_generator.py) - 垃圾代码生成核心实现
- [字符串加密器](string_encryptor.py) - 字符串加密核心实现
- [P2集成测试](../../tests/test_obfuscation_integration_p2.py) - P2功能集成测试

## 支持与反馈

如有问题或建议，请提交Issue或联系开发团队。
