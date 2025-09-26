# CLAUDE.md - 工具脚本技术指南

## 模块概述
专业工具脚本集合，提供iOS崩溃日志分析、符号化等高级功能。基于Apple开发工具链，支持完整的崩溃分析工作流。

## 核心工具

### ips_parser.py
iOS崩溃报告（IPS格式）解析和符号化工具，基于MacSymbolicator的设计理念。

#### 架构设计

##### 类层次结构
```
IPSParser (解析器)
├── BinaryImage (二进制映像)
├── StackFrame (堆栈帧)
└── LogEntry (日志条目)

IPSSymbolicator (符号化器)
├── 依赖 IPSParser
├── dSYM处理
└── atos集成
```

#### 核心类详解

##### BinaryImage
```python
@dataclass
class BinaryImage:
    base: int          # 基地址
    size: int          # 大小
    uuid: str          # UUID标识符
    path: str          # 文件路径
    name: str          # 二进制名称
    arch: str          # 架构(arm64/arm64e/x86_64)

    @property
    def end_address(self) -> int:
        # 计算结束地址
        return self.base + self.size
```

##### StackFrame
```python
@dataclass
class StackFrame:
    index: int         # 帧索引
    binary_name: str   # 二进制名称
    address: int       # 地址
    symbol: str        # 符号名（可选）
    offset: int        # 偏移量（可选）
    source_file: str   # 源文件（可选）
    source_line: int   # 源代码行（可选）
```

##### IPSParser
主解析器类，负责IPS文件的解析和信息提取。

###### 关键方法
- `parse_file(filepath)`: 解析IPS文件
- `parse_content(content)`: 解析IPS内容
- `get_crash_info()`: 获取崩溃摘要
- `get_crashed_thread_frames()`: 获取崩溃线程堆栈
- `to_crash_format(with_tags)`: 转换为传统格式

###### IPS文件格式
```json
// 第一行：摘要JSON
{
  "app_name": "AppName",
  "app_version": "1.0.0",
  "build_version": "100",
  "bundle_id": "com.company.app",
  "incident_id": "UUID",
  "os_version": "iOS 17.0"
}
// 第二行：详细JSON
{
  "pid": 1234,
  "modelCode": "iPhone14,2",
  "threads": [...],
  "usedImages": [...],
  "exception": {...}
}
```

##### IPSSymbolicator
符号化器类，使用dSYM文件和Apple工具进行符号化。

###### 关键方法
- `set_dsym(dsym_path)`: 设置dSYM文件
- `symbolicate(with_tags)`: 执行符号化
- `_extract_dsym_uuids()`: 提取dSYM UUID
- `_symbolicate_addresses()`: 符号化地址
- `_update_symbols()`: 更新符号信息

###### 符号化流程
```python
1. 加载dSYM文件
2. 提取UUID映射
3. 匹配二进制映像
4. 收集需要符号化的地址
5. 调用atos进行符号化
6. 更新堆栈帧信息
7. 生成符号化报告
```

#### 依赖工具

##### 系统命令
1. **dwarfdump**: 提取dSYM UUID
   ```bash
   dwarfdump --uuid /path/to/dSYM
   ```

2. **atos**: 地址符号化
   ```bash
   atos -arch arm64 -o binary -l load_address address1 address2
   ```

3. **symbols**: 符号提取（可选）
   ```bash
   symbols -arch arm64 -o output.txt binary
   ```

##### Python依赖
```python
import json         # JSON解析
import re          # 正则表达式
import subprocess  # 系统命令
import tempfile    # 临时文件
import os          # 文件操作
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
```

#### 使用指南

##### 基础用法
```python
# 解析IPS文件
parser = IPSParser()
if parser.parse_file("crash.ips"):
    info = parser.get_crash_info()
    print(f"Crashed: {info['process_name']}")

    # 获取崩溃堆栈
    frames = parser.get_crashed_thread_frames()
    for frame in frames:
        print(f"{frame.index}: {frame.binary_name} - {frame.symbol or '0x%x' % frame.address}")
```

##### 符号化
```python
# 创建符号化器
symbolicator = IPSSymbolicator(parser)

# 设置dSYM文件
if symbolicator.set_dsym("MyApp.app.dSYM"):
    # 执行符号化
    symbolicated_report = symbolicator.symbolicate()
    print(symbolicated_report)
```

##### 集成到GUI
```python
# GUI中的导入修复
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'tools'))
from ips_parser import IPSParser, IPSSymbolicator
```

#### 崩溃类型识别

##### 异常类型
```python
EXCEPTION_TYPES = {
    'EXC_CRASH': '应用崩溃',
    'EXC_BAD_ACCESS': '内存访问错误',
    'EXC_BAD_INSTRUCTION': '非法指令',
    'EXC_ARITHMETIC': '算术异常',
    'EXC_BREAKPOINT': '断点异常',
    'EXC_RESOURCE': '资源限制',
    'EXC_GUARD': '保护页面违规'
}
```

##### 终止原因
```python
TERMINATION_REASONS = {
    'Namespace SPRINGBOARD': '系统终止',
    'Namespace ASSERTIOND': '断言失败',
    'Namespace JETSAM': '内存压力',
    'Namespace WATCHDOG': '看门狗超时',
    'Namespace THERMAL': '过热保护'
}
```

#### 性能优化

##### 缓存策略
```python
class SymbolCache:
    def __init__(self, max_size=1000):
        self.cache = {}
        self.max_size = max_size

    def get(self, address, binary_uuid):
        key = f"{binary_uuid}:{address}"
        return self.cache.get(key)

    def set(self, address, binary_uuid, symbol):
        key = f"{binary_uuid}:{address}"
        if len(self.cache) >= self.max_size:
            # LRU淘汰
            self.cache.pop(next(iter(self.cache)))
        self.cache[key] = symbol
```

##### 批量处理
```python
def batch_symbolicate(addresses, batch_size=100):
    results = []
    for i in range(0, len(addresses), batch_size):
        batch = addresses[i:i+batch_size]
        results.extend(symbolicate_batch(batch))
    return results
```

## 扩展开发

### 添加新的崩溃格式支持

#### 1. Android崩溃（Tombstone）
```python
class TombstoneParser:
    def parse(self, content):
        # 解析Android tombstone格式
        pass
```

#### 2. Windows崩溃（Minidump）
```python
class MinidumpParser:
    def parse(self, filepath):
        # 解析Windows minidump格式
        pass
```

### 符号服务器支持
```python
class SymbolServer:
    def __init__(self, server_url):
        self.server_url = server_url

    def download_symbols(self, uuid):
        # 从服务器下载符号文件
        pass
```

### 自动化分析
```python
class CrashAnalyzer:
    def analyze(self, crash_report):
        # 自动分析崩溃原因
        # 识别常见崩溃模式
        # 提供修复建议
        pass
```

## 测试指南

### 单元测试
```python
# test_ips_parser.py
def test_parse_valid_ips():
    parser = IPSParser()
    assert parser.parse_file("test_data/valid.ips")

def test_parse_invalid_ips():
    parser = IPSParser()
    assert not parser.parse_file("test_data/invalid.txt")

def test_symbolication():
    # 测试符号化功能
    pass
```

### 集成测试
```python
def test_end_to_end():
    # 1. 解析IPS
    # 2. 设置dSYM
    # 3. 符号化
    # 4. 验证输出
    pass
```

### 性能测试
```python
def benchmark_parsing():
    import time
    start = time.time()
    parser = IPSParser()
    parser.parse_file("large_crash.ips")
    print(f"Parsing time: {time.time() - start}s")
```

## 故障排除

### 常见问题

#### Q: 符号化失败？
1. **检查dSYM UUID匹配**
   ```bash
   dwarfdump --uuid MyApp.app.dSYM
   ```
2. **确认架构正确**
   ```bash
   file MyApp.app/MyApp
   ```
3. **验证atos可用**
   ```bash
   which atos
   ```

#### Q: 解析IPS失败？
1. 检查文件格式（必须是JSON）
2. 验证文件完整性
3. 查看错误日志

#### Q: GUI集成问题？
1. 确认路径引用正确
2. 检查sys.path设置
3. 验证模块导入

### 调试技巧
```python
# 启用调试输出
import logging
logging.basicConfig(level=logging.DEBUG)

# 打印解析结果
parser = IPSParser()
if parser.parse_file("crash.ips"):
    print("Summary:", parser.summary)
    print("Detail keys:", parser.detail.keys())
    print("Binary images:", len(parser.binary_images))
    print("Threads:", len(parser.threads))
```

## 维护指南

### 代码规范
1. **类型注解**: 使用typing模块
2. **数据类**: 使用@dataclass
3. **文档字符串**: Google风格
4. **错误处理**: 明确的异常

### 版本兼容
- Python 3.6+: 完全支持
- macOS 10.14+: 需要atos工具
- Xcode 10+: 需要dwarfdump

### 依赖更新
```bash
# 检查系统工具
xcode-select --install

# 更新Python依赖
pip install --upgrade typing dataclasses
```

## 未来规划

### 短期目标
- [ ] 支持symbolication服务器
- [ ] 增加崩溃模式识别
- [ ] 自动下载dSYM
- [ ] 批量处理优化

### 中期目标
- [ ] Android崩溃支持
- [ ] 崩溃聚合分析
- [ ] 机器学习分类
- [ ] Web API服务

### 长期目标
- [ ] 跨平台崩溃分析
- [ ] 实时崩溃监控
- [ ] 自动化修复建议
- [ ] 崩溃预测模型

## 相关资源

### 文档
- [Apple Crash Reporter](https://developer.apple.com/documentation/xcode/diagnosing-issues-using-crash-reports-and-device-logs)
- [Understanding and Analyzing Application Crash Reports](https://developer.apple.com/library/archive/technotes/tn2151/_index.html)
- [dSYM Files](https://developer.apple.com/documentation/xcode/building-your-app-to-include-debugging-information)

### 工具
- [MacSymbolicator](https://github.com/inket/MacSymbolicator)
- [FLEX](https://github.com/FLEXTool/FLEX)
- [PLCrashReporter](https://github.com/microsoft/plcrashreporter)

### 社区
- [iOS Crash Analysis](https://www.objc.io/issues/11-ios7/crash-reporting/)
- [Stack Overflow - iOS Crash](https://stackoverflow.com/questions/tagged/ios-crash)