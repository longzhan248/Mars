# CLAUDE.md - LinkMap分析模块技术文档

## 模块概述

LinkMap文件分析工具，用于解析Xcode生成的Link Map文件，统计iOS应用的二进制大小，分析符号占用和未使用的代码（Dead Code）。模块采用解析-分析-格式化的三层架构，实现了高内聚低耦合的代码组织。

## 目录结构

```
linkmap/
├── __init__.py              # 模块导出
├── linkmap_parser.py        # 解析模块
├── linkmap_analyzer.py      # 分析模块
├── linkmap_formatter.py     # 格式化模块
└── CLAUDE.md               # 技术文档（本文件）
```

## 核心模块详解

### 1. linkmap_parser.py - 解析模块

**职责**：
- 解析LinkMap文件格式
- 提取对象文件映射
- 提取符号信息和大小
- 提取死代码信息

**核心类**：`LinkMapParser`

**关键方法**：

```python
def check_format(self, content):
    """检查LinkMap文件格式是否有效"""
    # 验证必需的段标识符
    required_sections = ["# Object files:", "# Symbols:"]

def extract_app_name(self, content, file_path):
    """从文件内容或路径中提取应用名称"""
    # 从第一行或文件名提取应用名

def parse_object_files(self, content):
    """解析对象文件段
    格式: [ 0] /path/to/file.o
    """

def parse_symbols(self, content):
    """解析符号段
    格式: 0x1000 0x100 [ 0] _symbol_name
    返回: {文件路径: 总大小}
    """

def parse_dead_symbols(self, content):
    """解析死代码段
    格式: <<dead>> 0x100 [ 0] _symbol_name
    返回: {文件路径: 总大小}
    """

def parse_all(self, content):
    """一次性解析所有内容
    返回: {
        'object_files': 对象文件映射,
        'symbols': 符号映射,
        'dead_symbols': 死代码映射
    }
    """
```

**解析流程**：
1. 定位各段标识符（Object files / Symbols / Dead Stripped Symbols）
2. 解析对象文件索引和路径的映射关系
3. 解析符号大小并累加到对应文件
4. 解析死代码大小并累加到对应文件

**数据结构**：
- 对象文件映射：`{[索引]: 文件路径}`
- 符号映射：`{文件路径: 总大小(字节)}`

---

### 2. linkmap_analyzer.py - 分析模块

**职责**：
- 数据过滤和搜索
- 大小排序和统计
- 按库分组
- 数据分析和汇总

**核心类**：`LinkMapAnalyzer`

**关键方法**：

```python
def filter_by_keyword(self, symbol_map, keyword):
    """按关键词过滤符号
    支持大小写不敏感的路径匹配
    """

def sort_by_size(self, symbol_map, reverse=True):
    """按大小排序
    返回: [(文件路径, 大小), ...]
    """

def group_by_library(self, symbol_map):
    """按库分组统计
    自动识别:
    - Framework (.framework)
    - 静态库 (.a)
    - 项目文件 (.o)
    返回: {库名: 总大小}
    """

def calculate_total_size(self, symbol_map):
    """计算总大小（字节）"""

def get_top_n(self, symbol_map, n=10):
    """获取前N大的符号"""

def calculate_percentage(self, size, total_size):
    """计算百分比（0-100）"""

def analyze_distribution(self, symbol_map):
    """分析大小分布
    返回: {
        'total_files': 文件总数,
        'total_size': 总大小,
        'avg_size': 平均大小,
        'max_size': 最大文件,
        'min_size': 最小文件
    }
    """

def find_duplicates(self, symbol_map):
    """查找可能重复的符号
    返回: {文件名: [完整路径列表]}
    """

def simplify_path(self, path):
    """简化路径显示
    移除DerivedData、Build等中间路径
    """
```

**库名提取规则**：
- Framework: 提取 `name.framework`
- 静态库: 提取 `libname.a`
- 项目文件: 提取文件名（去除.o）

**路径简化规则**：
- 移除 `Build/Intermediates.noindex/...`
- 移除 `DerivedData/...`
- 移除SDK路径
- 用 `../` 替代

---

### 3. linkmap_formatter.py - 格式化模块

**职责**：
- 大小格式化（字节 → K/M）
- 列表格式化输出
- 报告生成
- LinkMap文件美化

**核心类**：`LinkMapFormatter`

**关键方法**：

```python
def format_size(self, size):
    """格式化文件大小
    1024*1024+ → "X.XXM"
    1024+       → "X.XXK"
    其他        → "XB"
    """

def format_symbol_list(self, symbol_items, show_simplified_path=True):
    """格式化符号列表输出
    输出格式:
    文件大小        文件名称
    =====================================
    1.50M          ../YourApp/Module.o
    256K           ../Foundation.framework
    ...
    =====================================
    总计: 10.5M (100 个文件)
    """

def format_library_list(self, library_items):
    """格式化库列表输出
    类似format_symbol_list，但针对库统计
    """

def format_analysis_report(self, app_name, file_path, symbol_result, dead_code_result):
    """格式化分析报告
    包含应用信息、符号统计、死代码统计
    """

def format_linkmap_file(self, content):
    """格式化Link Map文件内容
    美化输出:
    - 添加段分隔线
    - 简化路径
    - 格式化大小显示
    """

def format_distribution_stats(self, stats):
    """格式化分布统计信息"""
```

**格式化输出示例**：
```
Link Map 分析报告
应用名称: YourApp
文件路径: /path/to/linkmap.txt
================================================================================

符号统计:
--------------------------------------------------------------------------------
文件大小        文件名称
================================================================================
2.50M          ../CoreFoundation.framework
1.80M          ../UIKit.framework
500K           ../YourApp/ViewController.o
...
================================================================================
总计: 15.5M (150 个文件)
```

---

## 使用示例

### 基础使用

```python
from gui.modules.linkmap import LinkMapParser, LinkMapAnalyzer, LinkMapFormatter

# 读取文件
with open('linkmap.txt', 'r') as f:
    content = f.read()

# 解析
parser = LinkMapParser()
symbols = parser.parse_symbols(content)
dead_code = parser.parse_dead_symbols(content)

# 分析
analyzer = LinkMapAnalyzer()
sorted_symbols = analyzer.sort_by_size(symbols)
top10 = analyzer.get_top_n(symbols, 10)

# 格式化输出
formatter = LinkMapFormatter()
result = formatter.format_symbol_list(sorted_symbols)
print(result)
```

### 按库统计

```python
# 按库分组
grouped = analyzer.group_by_library(symbols)
sorted_libs = analyzer.sort_by_size(grouped)

# 格式化输出
result = formatter.format_library_list(sorted_libs)
print(result)
```

### 搜索和过滤

```python
# 搜索特定关键词
filtered = analyzer.filter_by_keyword(symbols, "YourModule")
result = formatter.format_symbol_list(
    analyzer.sort_by_size(filtered)
)
```

### 生成报告

```python
# 构建完整报告
symbol_result = formatter.format_symbol_list(sorted_symbols)
dead_code_result = formatter.format_symbol_list(sorted_dead_code)

report = formatter.format_analysis_report(
    app_name="YourApp",
    file_path="/path/to/linkmap.txt",
    symbol_result=symbol_result,
    dead_code_result=dead_code_result
)

with open('report.txt', 'w') as f:
    f.write(report)
```

---

## LinkMap文件格式说明

### 文件结构

```
# Path: /path/to/app
# Arch: arm64
# Object files:
[  0] /path/to/file1.o
[  1] /path/to/file2.o
...

# Sections:
# Address    Size       Segment  Section
0x100000000  0x1234     __TEXT   __text
...

# Symbols:
# Address    Size       File  Name
0x100000000  0x100      [  0] _main
0x100000100  0x50       [  1] _func1
...

# Dead Stripped Symbols:
#            Size       File  Name
<<dead>>     0x20       [  0] _unused_func
...
```

### 关键字段

- **Address**: 符号地址（十六进制）
- **Size**: 符号大小（十六进制字节数）
- **File**: 对象文件索引（对应Object files段）
- **Name**: 符号名称

### 计算逻辑

1. 解析Object files段，建立索引→路径映射
2. 解析Symbols段，将Size累加到对应File的路径
3. 解析Dead Stripped Symbols段，统计未使用代码
4. 最终得到每个文件的总大小

---

## 架构设计

### 设计原则

- **单一职责**：每个模块只负责一项功能
- **低耦合**：模块间通过数据传递交互，无直接依赖
- **高内聚**：相关功能集中在同一模块
- **易测试**：每个模块可独立测试

### 数据流

```
LinkMap文件 (纯文本)
    ↓
LinkMapParser (解析)
    ↓
symbol_map: {文件路径: 大小}
    ↓
LinkMapAnalyzer (分析)
    ↓
filtered/sorted/grouped数据
    ↓
LinkMapFormatter (格式化)
    ↓
格式化文本输出
```

### 扩展性

**添加新的统计维度**：
```python
# 在 LinkMapAnalyzer 中添加新方法
def group_by_module(self, symbol_map):
    """按模块分组"""
    # 实现分组逻辑
    pass
```

**添加新的输出格式**：
```python
# 在 LinkMapFormatter 中添加新方法
def format_to_json(self, symbol_items):
    """格式化为JSON"""
    import json
    return json.dumps(symbol_items)
```

**添加新的解析段**：
```python
# 在 LinkMapParser 中添加新方法
def parse_sections(self, content):
    """解析Sections段"""
    # 实现解析逻辑
    pass
```

---

## 性能优化

### 优化策略

1. **懒解析**：仅在需要时解析对应段
2. **缓存对象文件映射**：避免重复解析
3. **使用生成器**：大数据集时降低内存占用
4. **正则表达式优化**：预编译常用正则

### 内存管理

- 对象文件映射：约 N * 100字节（N为文件数）
- 符号映射：约 M * 50字节（M为文件数）
- 总内存占用：通常 < 1MB

### 性能指标

- 解析速度：约 1MB/s
- 典型LinkMap文件：10-50MB
- 解析时间：10-50秒

---

## 常见问题

### Q: 为什么同一个文件会有多个大小？
**A**: LinkMap中同一个.o文件的符号会分散在不同地址，我们将它们累加得到文件总大小。

### Q: Dead Stripped Symbols是什么？
**A**: 编译器优化时移除的未使用代码，统计这些可以了解有多少代码实际未被使用。

### Q: 为什么按库统计和按文件统计的总大小不同？
**A**: 可能由于搜索过滤或某些文件无法归类到库导致。

### Q: 如何处理超大LinkMap文件？
**A**:
1. 使用搜索过滤只分析关心的部分
2. 考虑只解析符号段，跳过死代码段
3. 使用生成器模式处理大数据集

### Q: 支持哪些架构的LinkMap？
**A**: 支持所有Xcode生成的LinkMap格式，包括armv7、arm64、x86_64等。

---

## 测试要点

### 单元测试

```python
def test_parser():
    """测试解析器"""
    parser = LinkMapParser()

    # 测试格式检查
    assert parser.check_format(valid_content) == True
    assert parser.check_format(invalid_content) == False

    # 测试符号解析
    symbols = parser.parse_symbols(sample_content)
    assert len(symbols) > 0
    assert all(isinstance(v, int) for v in symbols.values())

def test_analyzer():
    """测试分析器"""
    analyzer = LinkMapAnalyzer()

    # 测试过滤
    filtered = analyzer.filter_by_keyword(symbols, "test")
    assert all("test" in k.lower() for k in filtered.keys())

    # 测试排序
    sorted_items = analyzer.sort_by_size(symbols)
    sizes = [s for _, s in sorted_items]
    assert sizes == sorted(sizes, reverse=True)

def test_formatter():
    """测试格式化器"""
    formatter = LinkMapFormatter()

    # 测试大小格式化
    assert formatter.format_size(1024) == "1.00K"
    assert formatter.format_size(1024*1024) == "1.00M"

    # 测试列表格式化
    result = formatter.format_symbol_list([("file.o", 1024)])
    assert "1.00K" in result
    assert "file.o" in result
```

---

## 版本历史

### v1.0.0 (2025-10-11) - 模块化重构
- ✅ 将651行单文件拆分为3个模块
- ✅ 解析、分析、格式化职责分离
- ✅ 保持100%功能兼容
- ✅ linkmap_tab.py 从651行缩减到360行
- ✅ 代码可读性和可维护性大幅提升

---

## 参考资料

- [Xcode Link Map File Format](https://pewpewthespells.com/blog/buildsettings.html)
- [Understanding iOS App Size](https://developer.apple.com/videos/play/wwdc2018/408/)
- [Dead Code Stripping](https://developer.apple.com/library/archive/technotes/tn2151/_index.html)

---

**文档维护者**: Claude Code
**最后更新**: 2025-10-11
**模块版本**: v1.0.0
