# CLAUDE.md - 工具脚本模块

## 模块概述
专业工具脚本集合，提供iOS崩溃日志分析、符号化等功能。

## 核心工具

### ips_parser.py
iOS崩溃报告（IPS格式）解析和符号化工具。

#### 核心类
- **IPSParser**: 解析IPS文件，提取崩溃信息
- **IPSSymbolicator**: 使用dSYM文件进行符号化
- **BinaryImage**: 二进制映像信息
- **StackFrame**: 堆栈帧数据结构

#### 基础用法
```python
# 解析IPS文件
parser = IPSParser()
if parser.parse_file("crash.ips"):
    info = parser.get_crash_info()
    frames = parser.get_crashed_thread_frames()

# 符号化
symbolicator = IPSSymbolicator(parser)
if symbolicator.set_dsym("MyApp.app.dSYM"):
    report = symbolicator.symbolicate()
```

#### IPS文件格式
- 第一行：摘要JSON（app_name, version, bundle_id等）
- 第二行：详细JSON（pid, threads, usedImages, exception等）

#### 依赖工具
- **dwarfdump**: 提取dSYM UUID
- **atos**: 地址符号化
- **Python依赖**: json, re, subprocess, tempfile

## 使用场景

### GUI集成
```python
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'tools'))
from ips_parser import IPSParser, IPSSymbolicator
```

### 崩溃类型识别
- EXC_BAD_ACCESS: 内存访问错误
- EXC_CRASH: 应用崩溃
- EXC_BREAKPOINT: 断点异常
- Namespace JETSAM: 内存压力
- Namespace WATCHDOG: 看门狗超时

## 常见问题

### 符号化失败
1. 检查dSYM UUID匹配: `dwarfdump --uuid MyApp.app.dSYM`
2. 确认架构正确: `file MyApp.app/MyApp`
3. 验证atos可用: `which atos`

### 解析失败
1. 检查文件格式（必须为JSON）
2. 验证文件完整性
3. 查看错误日志

## 开发注意

### 性能优化
- 使用符号缓存减少重复调用
- 批量地址符号化
- LRU淘汰策略

### 错误处理
- 损坏数据跳过处理
- 明确的异常类型
- 详细的错误信息

### 代码规范
- 使用类型注解
- @dataclass数据结构
- Google风格文档字符串

## 测试要求
- 单元测试覆盖核心功能
- 集成测试验证端到端流程
- 性能测试确保解析速度

---

*详细实现请参考源码和Apple官方文档。*