# CLAUDE.md - dSYM分析模块技术文档

## 模块概述

dSYM文件分析工具，用于iOS崩溃日志符号化。通过解析dSYM文件中的调试符号信息，将崩溃堆栈中的内存地址转换为可读的函数名和源代码位置。模块采用文件管理-UUID解析-符号化的三层架构，实现了高内聚低耦合的代码组织。

## 目录结构

```
dsym/
├── __init__.py              # 模块导出
├── dsym_file_manager.py     # 文件管理模块
├── dsym_uuid_parser.py      # UUID解析模块
├── dsym_symbolizer.py       # 符号化模块
└── CLAUDE.md               # 技术文档（本文件）
```

## 核心模块详解

### 1. dsym_file_manager.py - 文件管理模块

**职责**：
- 加载和管理xcarchive/dSYM文件
- 提供文件选择对话框（macOS原生支持）
- 验证文件有效性
- 从xcarchive中提取dSYM路径

**核心类**：`DSYMFileManager`

**关键方法**：

```python
def load_local_archives(self):
    """加载本地的xcarchive文件
    从 ~/Library/Developer/Xcode/Archives/ 扫描所有.xcarchive文件
    返回: [{'path': str, 'name': str, 'type': str}, ...]
    """

def add_dsym_file(self, file_path):
    """添加dSYM文件
    验证文件格式并添加到列表
    返回: {'path': str, 'name': str, 'type': 'dsym'}
    """

def add_xcarchive_file(self, file_path):
    """添加xcarchive文件
    验证文件格式并添加到列表
    返回: {'path': str, 'name': str, 'type': 'xcarchive'}
    """

def get_dsym_path_from_xcarchive(self, xcarchive_path):
    """从xcarchive中提取dSYM路径
    查找 xcarchive/dSYMs/ 目录下的.dSYM文件
    返回: dSYM文件路径 或 None
    """

def select_file_with_applescript(self):
    """使用AppleScript选择文件（macOS原生对话框）
    支持选择.dSYM和.xcarchive包文件
    返回: 文件路径 或 None
    """

def get_file_type(self, file_path):
    """判断文件类型
    返回: 'dsym' 或 'xcarchive' 或 None
    """
```

**文件验证逻辑**：

dSYM文件需满足以下条件之一：
1. 路径以`.dSYM`结尾
2. 包含`Contents/Info.plist`文件
3. 包含`Contents/Resources/DWARF`目录

**AppleScript对话框优势**：
- 可以直接选择包文件（.dSYM和.xcarchive是macOS包类型）
- 避免tkinter文件对话框无法识别包的问题
- 更符合macOS用户习惯

---

### 2. dsym_uuid_parser.py - UUID解析模块

**职责**：
- 使用dwarfdump工具提取UUID信息
- 解析架构信息（armv7, arm64等）
- 提供默认Slide Address
- UUID格式验证

**核心类**：`DSYMUUIDParser`

**关键方法**：

```python
def get_uuid_info(self, dsym_path):
    """获取dSYM文件的UUID信息
    执行: dwarfdump --uuid <dsym_path>
    返回: [{'uuid': str, 'arch': str, 'path': str}, ...]
    """

def parse_uuid_output(self, output, dsym_path):
    """解析dwarfdump的UUID输出
    格式: UUID: XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX (armv7) path/to/file
    返回: UUID信息列表
    """

def get_default_slide_address(self, arch=None):
    """获取默认的Slide Address
    32位架构(armv7): 0x4000
    64位架构(arm64): 0x104000000
    返回: 十六进制地址字符串
    """

def validate_uuid(self, uuid_string):
    """验证UUID格式
    标准格式: XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
    返回: bool
    """

def find_uuid_by_arch(self, uuid_infos, arch):
    """根据架构查找UUID信息
    在多架构dSYM中查找指定架构
    返回: UUID信息 或 None
    """

def check_dwarfdump_available(self):
    """检查dwarfdump工具是否可用
    返回: bool
    """
```

**UUID格式示例**：
```
UUID: 12345678-1234-5678-1234-567812345678 (arm64) /path/to/YourApp
UUID: 87654321-4321-8765-4321-876543218765 (armv7) /path/to/YourApp
```

**Slide Address说明**：
- **Slide Address（基址）**：应用加载到内存时的起始地址
- **32位iOS**: 默认 `0x4000`
- **64位iOS**: 早期 `0x100000000`，后期 `0x104000000`
- **获取方式**：
  1. 从崩溃日志中的Binary Images段读取
  2. 使用`image list`命令（lldb调试时）
  3. 使用默认值（如果不确定）

---

### 3. dsym_symbolizer.py - 符号化模块

**职责**：
- 使用atos工具进行地址符号化
- 批量符号化多个地址
- 格式化输出结果
- IPA导出功能

**核心类**：`DSYMSymbolizer`

**关键方法**：

```python
def symbolicate_address(self, dsym_path, arch, slide_address, error_address):
    """符号化崩溃地址
    执行: xcrun atos -arch <arch> -o <dsym_path> -l <slide_address> <error_address>
    返回: {
        'success': bool,
        'output': str,
        'command': str,
        'error': str (可选)
    }
    """

def symbolicate_multiple_addresses(self, dsym_path, arch, slide_address, addresses):
    """批量符号化多个地址
    用于符号化整个堆栈跟踪
    返回: 符号化结果列表
    """

def format_symbolication_result(self, arch, uuid, slide_address, error_address, output, command):
    """格式化符号化结果为可读文本
    返回格式:
    =====================================
    架构: arm64
    UUID: 12345678-...
    基址: 0x104000000
    错误地址: 0x10400abcd
    =====================================

    符号化结果:
    -[YourClass methodName:] (in YourApp) (YourFile.m:123)

    命令: xcrun atos ...
    """

def validate_address(self, address):
    """验证内存地址格式
    必须以0x开头的十六进制
    返回: bool
    """

def export_ipa(self, xcarchive_path, output_dir):
    """从xcarchive导出IPA文件
    使用xcodebuild -exportArchive命令
    返回: {
        'success': bool,
        'output_path': str (成功时),
        'error': str (失败时)
    }
    """

def check_atos_available(self):
    """检查atos工具是否可用
    返回: bool
    """
```

**atos命令格式**：
```bash
xcrun atos -arch arm64 \
  -o YourApp.app.dSYM/Contents/Resources/DWARF/YourApp \
  -l 0x104000000 \
  0x10400abcd
```

**符号化输出示例**：
```
-[ViewController viewDidLoad] (in MyApp) (ViewController.m:42)
```

**IPA导出选项**：
- `method`: development / app-store / ad-hoc / enterprise
- `compileBitcode`: 是否编译Bitcode
- `uploadBitcode`: 是否上传Bitcode
- `uploadSymbols`: 是否上传符号文件

---

## 使用示例

### 基础使用

```python
from gui.modules.dsym import DSYMFileManager, DSYMUUIDParser, DSYMSymbolizer

# 1. 文件管理
file_manager = DSYMFileManager()

# 加载本地Archives
archives = file_manager.load_local_archives()
print(f"找到 {len(archives)} 个xcarchive文件")

# 添加dSYM文件
file_info = file_manager.add_dsym_file("/path/to/YourApp.app.dSYM")

# 从xcarchive提取dSYM
dsym_path = file_manager.get_dsym_path_from_xcarchive(xcarchive_path)

# 2. UUID解析
uuid_parser = DSYMUUIDParser()

# 获取UUID信息
uuid_infos = uuid_parser.get_uuid_info(dsym_path)
for info in uuid_infos:
    print(f"架构: {info['arch']}, UUID: {info['uuid']}")

# 获取默认基址
default_slide = uuid_parser.get_default_slide_address('arm64')
print(f"默认基址: {default_slide}")

# 3. 符号化
symbolizer = DSYMSymbolizer()

# 符号化单个地址
result = symbolizer.symbolicate_address(
    dsym_path=uuid_infos[0]['path'],
    arch=uuid_infos[0]['arch'],
    slide_address='0x104000000',
    error_address='0x10400abcd'
)

if result['success']:
    print(result['output'])
else:
    print(f"符号化失败: {result['error']}")
```

### 批量符号化堆栈

```python
# 崩溃堆栈地址列表
addresses = [
    '0x10400abcd',
    '0x10400beef',
    '0x10400cafe'
]

# 批量符号化
results = symbolizer.symbolicate_multiple_addresses(
    dsym_path=dsym_path,
    arch='arm64',
    slide_address='0x104000000',
    addresses=addresses
)

# 打印结果
for result in results:
    print(f"{result['address']}: {result['output']}")
```

### 导出IPA

```python
result = symbolizer.export_ipa(
    xcarchive_path='/path/to/YourApp.xcarchive',
    output_dir='/path/to/output'
)

if result['success']:
    print(f"IPA已导出到: {result['output_path']}")
else:
    print(f"导出失败: {result['error']}")
```

---

## 架构设计

### 设计原则

- **单一职责**：每个模块只负责一项功能
- **低耦合**：模块间通过数据传递交互，无直接依赖
- **高内聚**：相关功能集中在同一模块
- **易测试**：每个模块可独立测试

### 数据流

```
文件加载 (DSYMFileManager)
    ↓
xcarchive/dSYM文件路径
    ↓
UUID解析 (DSYMUUIDParser)
    ↓
{uuid, arch, path} 信息
    ↓
符号化 (DSYMSymbolizer)
    ↓
函数名和源代码位置
```

### 扩展性

**添加新的文件类型支持**：
```python
# 在 DSYMFileManager 中添加新方法
def add_custom_file(self, file_path):
    """添加自定义文件类型"""
    # 实现验证和添加逻辑
    pass
```

**添加新的符号化工具**：
```python
# 在 DSYMSymbolizer 中添加新方法
def symbolicate_with_lldb(self, dsym_path, arch, address):
    """使用lldb进行符号化"""
    # 实现lldb符号化逻辑
    pass
```

**添加崩溃日志解析**：
```python
# 创建新模块 dsym_crash_parser.py
class DSYMCrashParser:
    """崩溃日志解析器"""
    def parse_crash_log(self, crash_log_path):
        """解析崩溃日志，提取地址和基址"""
        pass
```

---

## 性能优化

### 优化策略

1. **缓存UUID信息**：避免重复调用dwarfdump
2. **批量符号化**：一次atos调用处理多个地址
3. **异步处理**：耗时操作在后台线程执行
4. **超时控制**：防止工具挂起

### 超时设置

- **dwarfdump**: 10秒
- **atos**: 10秒
- **xcodebuild**: 300秒（5分钟）

### 内存管理

- 文件列表：约 N * 100字节（N为文件数）
- UUID信息：约 M * 80字节（M为架构数）
- 总内存占用：通常 < 1MB

---

## 常见问题

### Q: dwarfdump命令找不到？
**A**: dwarfdump是Xcode命令行工具的一部分，需要先安装：
```bash
xcode-select --install
```

### Q: atos符号化失败返回地址本身？
**A**: 可能原因：
1. **UUID不匹配**：dSYM文件与崩溃应用不对应
2. **基址错误**：Slide Address不正确
3. **地址超出范围**：错误地址不在应用代码段内
4. **架构不匹配**：选择了错误的架构

验证UUID匹配：
```bash
# 查看dSYM的UUID
dwarfdump --uuid YourApp.app.dSYM

# 查看IPA中可执行文件的UUID
dwarfdump --uuid YourApp.app/YourApp
```

### Q: 如何获取正确的Slide Address？
**A**: 从崩溃日志的Binary Images段获取：
```
Binary Images:
0x104000000 - 0x104ffffff YourApp arm64  <12345678-1234-5678-1234-567812345678>
```
第一列的地址即为Slide Address: `0x104000000`

### Q: xcarchive导出IPA失败？
**A**: 可能原因：
1. **证书过期**：检查签名证书是否有效
2. **配置文件不匹配**：确认Provisioning Profile
3. **权限不足**：检查export options plist配置
4. **磁盘空间不足**：确保有足够空间

### Q: 支持哪些iOS架构？
**A**: 支持所有Xcode生成的架构：
- **32位**: armv7, armv7s
- **64位**: arm64, arm64e
- **模拟器**: x86_64, arm64（M1 Mac）

---

## 测试要点

### 单元测试

```python
def test_file_manager():
    """测试文件管理器"""
    manager = DSYMFileManager()

    # 测试加载Archives
    archives = manager.load_local_archives()
    assert isinstance(archives, list)

    # 测试文件类型判断
    assert manager.get_file_type('/path/to/App.dSYM') == 'dsym'
    assert manager.get_file_type('/path/to/App.xcarchive') == 'xcarchive'

def test_uuid_parser():
    """测试UUID解析器"""
    parser = DSYMUUIDParser()

    # 测试UUID格式验证
    assert parser.validate_uuid('12345678-1234-5678-1234-567812345678') == True
    assert parser.validate_uuid('invalid-uuid') == False

    # 测试默认基址
    assert parser.get_default_slide_address('arm64') == '0x104000000'
    assert parser.get_default_slide_address('armv7') == '0x4000'

def test_symbolizer():
    """测试符号化器"""
    symbolizer = DSYMSymbolizer()

    # 测试地址验证
    assert symbolizer.validate_address('0x104000000') == True
    assert symbolizer.validate_address('invalid') == False

    # 测试格式化输出
    result = symbolizer.format_symbolication_result(
        arch='arm64',
        uuid='12345678-...',
        slide_address='0x104000000',
        error_address='0x10400abcd',
        output='-[Class method]',
        command='xcrun atos ...'
    )
    assert '架构: arm64' in result
    assert 'UUID: 12345678' in result
```

---

## 工具依赖

### macOS系统工具

1. **dwarfdump**
   - 路径: `/usr/bin/dwarfdump`
   - 用途: 提取dSYM中的UUID和架构信息
   - 检查: `which dwarfdump`

2. **atos**
   - 路径: `/usr/bin/xcrun atos`
   - 用途: 地址符号化
   - 检查: `xcrun atos -h`

3. **xcodebuild**
   - 路径: `/usr/bin/xcodebuild`
   - 用途: 导出IPA
   - 检查: `xcodebuild -version`

4. **osascript**
   - 路径: `/usr/bin/osascript`
   - 用途: 执行AppleScript，显示原生文件选择对话框
   - 检查: `which osascript`

### Python依赖

- `subprocess`: 执行外部命令
- `re`: 正则表达式解析
- `os`, `pathlib`: 文件路径操作
- `tempfile`: 临时文件创建
- `plistlib`: plist文件处理

---

## 版本历史

### v1.0.0 (2025-10-11) - 模块化重构
- ✅ 将508行单文件拆分为3个模块
- ✅ 文件管理、UUID解析、符号化职责分离
- ✅ 保持100%功能兼容
- ✅ dsym_tab.py 从508行缩减到392行
- ✅ 代码可读性和可维护性大幅提升
- ✅ AppleScript原生文件对话框支持

---

## 参考资料

- [Symbolication官方文档](https://developer.apple.com/library/archive/technotes/tn2151/_index.html)
- [Understanding and Analyzing Application Crash Reports](https://developer.apple.com/documentation/xcode/understanding-and-analyzing-application-crash-reports)
- [dSYM文件格式](https://pewpewthespells.com/blog/dsym.html)
- [DWARF调试信息格式](https://dwarfstd.org/)

---

**文档维护者**: Claude Code
**最后更新**: 2025-10-11
**模块版本**: v1.0.0
