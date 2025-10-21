# CLAUDE.md - dSYM分析模块

## 模块概述
iOS崩溃日志符号化工具，通过解析dSYM文件中的调试符号信息，将崩溃堆栈中的内存地址转换为可读的函数名和源代码位置。采用文件管理-UUID解析-符号化的三层架构。

## 核心功能

### 符号化流程
1. **文件管理**: 加载xcarchive/dSYM文件，验证有效性
2. **UUID解析**: 提取UUID和架构信息，获取基址
3. **地址符号化**: 使用atos工具将地址转换为函数名

### 支持的操作
- **xcarchive加载**: 自动扫描本地Xcode Archives
- **dSYM文件管理**: AppleScript原生文件选择
- **批量符号化**: 一次处理整个崩溃堆栈
- **IPA导出**: 从xcarchive导出IPA文件

## 目录结构
```
dsym/
├── dsym_file_manager.py    # 文件管理（xcarchive/dSYM）
├── dsym_uuid_parser.py     # UUID解析（dwarfdump）
├── dsym_symbolizer.py      # 符号化（atos）
└── CLAUDE.md              # 技术文档
```

## 核心模块

### 1. DSYMFileManager - 文件管理
```python
def load_local_archives(self):
    """扫描 ~/Library/Developer/Xcode/Archives/ """

def add_dsym_file(self, file_path):
    """添加并验证dSYM文件"""

def get_dsym_path_from_xcarchive(self, xcarchive_path):
    """从xcarchive提取dSYM路径"""

def select_file_with_applescript(self):
    """macOS原生文件选择对话框"""
```

**文件验证条件**:
- 路径以`.dSYM`结尾
- 包含`Contents/Info.plist`文件
- 包含`Contents/Resources/DWARF`目录

### 2. DSYMUUIDParser - UUID解析
```python
def get_uuid_info(self, dsym_path):
    """执行 dwarfdump --uuid 获取UUID"""

def get_default_slide_address(self, arch):
    """获取默认基址: arm64=0x104000000, armv7=0x4000"""

def validate_uuid(self, uuid_string):
    """验证UUID格式: XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"""
```

**UUID格式示例**:
```
UUID: 12345678-1234-5678-1234-567812345678 (arm64) /path/to/YourApp
```

### 3. DSYMSymbolizer - 符号化
```python
def symbolicate_address(self, dsym_path, arch, slide_address, error_address):
    """使用atos符号化单个地址"""

def symbolicate_multiple_addresses(self, dsym_path, arch, slide_address, addresses):
    """批量符号化崩溃堆栈"""

def export_ipa(self, xcarchive_path, output_dir):
    """从xcarchive导出IPA文件"""
```

**atos命令格式**:
```bash
xcrun atos -arch arm64 -o dsym_path -l 0x104000000 0x10400abcd
```

**符号化输出**:
```
-[ViewController viewDidLoad] (in MyApp) (ViewController.m:42)
```

## 使用方法

### 基础符号化
```python
from gui.modules.dsym import DSYMFileManager, DSYMUUIDParser, DSYMSymbolizer

# 1. 文件管理
file_manager = DSYMFileManager()
archives = file_manager.load_local_archives()
dsym_path = file_manager.get_dsym_path_from_xcarchive(xcarchive_path)

# 2. UUID解析
uuid_parser = DSYMUUIDParser()
uuid_infos = uuid_parser.get_uuid_info(dsym_path)

# 3. 符号化
symbolizer = DSYMSymbolizer()
result = symbolizer.symbolicate_address(
    dsym_path=uuid_infos[0]['path'],
    arch=uuid_infos[0]['arch'],
    slide_address='0x104000000',
    error_address='0x10400abcd'
)

if result['success']:
    print(result['output'])
```

### 批量符号化
```python
addresses = ['0x10400abcd', '0x10400beef', '0x10400cafe']
results = symbolizer.symbolicate_multiple_addresses(
    dsym_path=dsym_path,
    arch='arm64',
    slide_address='0x104000000',
    addresses=addresses
)

for result in results:
    print(f"{result['address']}: {result['output']}")
```

### IPA导出
```python
result = symbolizer.export_ipa(
    xcarchive_path='/path/to/YourApp.xcarchive',
    output_dir='/path/to/output'
)

if result['success']:
    print(f"IPA已导出到: {result['output_path']}")
```

## 技术架构

### 数据流
```
文件加载 → UUID解析 → 符号化 → 格式化输出
```

### 依赖工具
- **dwarfdump**: 提取UUID信息 (`xcode-select --install`)
- **atos**: 地址符号化
- **xcodebuild**: IPA导出
- **osascript**: macOS原生对话框

### 支持架构
- **32位**: armv7, armv7s
- **64位**: arm64, arm64e
- **模拟器**: x86_64, arm64 (M1 Mac)

## 常见问题

**Q: dwarfdump命令找不到？**
A: 安装Xcode命令行工具: `xcode-select --install`

**Q: atos符号化失败返回地址本身？**
A: 检查:
1. dSYM文件与崩溃应用是否匹配
2. Slide Address是否正确
3. 架构选择是否正确

**Q: 如何获取正确的Slide Address？**
A: 从崩溃日志的Binary Images段获取第一列地址:
```
Binary Images:
0x104000000 - 0x104ffffff YourApp arm64 <UUID>
```

**Q: xcarchive导出IPA失败？**
A: 检查证书、配置文件、磁盘空间和权限设置

## 性能优化

### 已实现优化
- **UUID缓存**: 避免重复dwarfdump调用
- **批量符号化**: 一次atos处理多个地址
- **异步处理**: 后台线程执行耗时操作
- **超时控制**: dwarfdump(10s)、atos(10s)、xcodebuild(300s)

### 内存占用
- 文件列表: ~100字节/文件
- UUID信息: ~80字节/架构
- 总内存: 通常 < 1MB

## 版本历史
- **v1.0.0**: 模块化重构，拆分为3个功能模块，保持100%兼容

---

*最后更新: 2025-10-11*
