# CLAUDE.md - 模块化组件

## 模块概述
Mars日志分析器的核心模块化组件，提供数据模型、文件操作、过滤搜索等基础功能。从原始3784行单文件中提取，实现高内聚低耦合设计。

## 核心模块

### 1. data_models.py - 数据模型
统一的数据结构定义，支持多种日志格式。

#### LogEntry类
```python
class LogEntry:
    """日志条目数据结构"""
    raw_line: str      # 原始日志行
    level: str         # 日志级别 (INFO/WARNING/ERROR/DEBUG/VERBOSE/FATAL)
    timestamp: str     # 时间戳
    module: str        # 模块名
    content: str       # 日志内容
    thread_id: str     # 线程ID
    is_crash: bool     # 是否崩溃日志
```

**支持的日志格式**:
- Mars标准: `[级别][时间戳][模块][线程ID] 内容`
- Mars扩展: `[级别][时间戳][线程ID][<标签>]内容`
- iOS崩溃: `*** Terminating app due to uncaught exception`
- 自定义规则: 用户可配置模块分组规则

#### FileGroup类
```python
class FileGroup:
    """文件分组管理"""
    base_name: str      # 基础名称
    files: List[str]    # 文件路径列表
    entries: List[LogEntry]  # 合并后的日志条目
```

### 2. file_operations.py - 文件操作
统一的文件读写和解码接口。

#### FileOperations类
```python
def load_file(self, filepath, callback=None):
    """加载日志文件，支持进度回调"""

def decode_xlog(self, filepath):
    """解码Mars xlog格式文件"""

def export_to_file(self, entries, filepath, format='txt'):
    """导出日志，支持TXT/JSON/CSV格式"""
```

**支持格式**:
- **输入**: .xlog, .log, .txt, .ips
- **输出**: .txt (纯文本), .json (结构化), .csv (表格)

### 3. filter_search.py - 过滤搜索
统一的过滤和搜索逻辑管理。

#### FilterSearchManager类
```python
def filter_entries(self, entries, level=None, module=None, keyword=None):
    """多条件过滤: 级别、模块、关键词"""

def parse_time_string(self, time_str):
    """解析时间字符串，支持时区"""

def compare_log_time(self, log_timestamp, start_time, end_time):
    """时间范围比较"""
```

**时间格式支持**:
- `2025-09-21 13:09:49`
- `2025-09-21 +8.0 13:09:49.038`
- `2025-09-21T13:09:49+08:00`

### 4. ips_tab.py - IPS崩溃分析
iOS崩溃报告分析界面。

#### IPSAnalysisTab类
```python
def load_ips_file(self):
    """加载IPS崩溃文件"""

def parse_ips(self, filepath):
    """解析JSON格式崩溃报告"""

def symbolicate_with_dsym(self, dsym_path):
    """使用dSYM文件符号化"""
```

**IPS文件结构**:
- `description`: 崩溃描述
- `timestamp`: 崩溃时间
- `exception`: 异常信息
- `threads`: 线程堆栈
- `binaryImages`: 二进制镜像

### 5. push_tab.py - iOS推送测试
APNS推送测试界面。

#### PushTestTab类
```python
def send_push(self):
    """发送APNS推送通知"""

def load_certificate(self):
    """加载.p12/.pem格式证书"""

def save_payload_template(self):
    """保存Payload模板"""
```

**推送配置**:
- **环境**: 开发/生产环境
- **证书**: P12/PEM格式
- **设备Token**: 目标设备令牌
- **Payload**: JSON推送内容

### 6. sandbox_tab.py - iOS沙盒浏览
iOS应用沙盒文件浏览器。

#### SandboxBrowserTab类
```python
def refresh_devices(self):
    """刷新iOS设备列表"""

def load_apps_async(self):
    """异步加载应用，智能过滤权限"""

def search_files(self, keyword, search_type):
    """递归搜索文件名和内容"""
```

**核心功能**:
- **智能应用过滤**: 预先检测访问权限，只显示可访问应用
- **文件浏览**: 树形结构展示沙盒文件系统
- **文件预览**: 支持文本、图片、十六进制格式
- **搜索功能**: 文件名和内容递归搜索

**文件预览支持**:
- **文本**: .txt, .log, .json, .xml, .plist, .html, .css, .js, .py, .md, .sh, .h, .m, .swift, .c, .cpp
- **图片**: .png, .jpg, .jpeg, .gif, .bmp, .ico (需Pillow库)
- **其他**: 十六进制dump显示

## 模块架构

### 依赖关系
```
mars_log_analyzer_modular.py
├── data_models.py (数据结构)
├── file_operations.py (文件处理)
├── filter_search.py (过滤逻辑)
├── ips_tab.py (IPS界面)
├── push_tab.py (推送界面)
└── sandbox_tab.py (沙盒浏览)
```

### 数据流
1. **加载**: FileOperations → LogEntry → FilterSearchManager
2. **过滤**: UI事件 → FilterSearchManager → 显示更新
3. **导出**: 过滤结果 → FileOperations → 文件系统

### 接口约定
- 统一使用LogEntry数据结构
- 回调函数签名: `callback(progress, message)`
- 过滤器返回: `List[LogEntry]`

## 使用示例

### 基础使用
```python
from gui.modules import LogEntry, FileOperations, FilterSearchManager

# 创建日志条目
entry = LogEntry("[I][2025-09-21 13:09:49][Module] Message")
print(entry.level)  # INFO

# 文件操作
ops = FileOperations()
entries = ops.load_file("app.log")

# 过滤搜索
manager = FilterSearchManager()
filtered = manager.filter_entries(entries, level="ERROR")
```

### 高级功能
```python
# IPS崩溃分析
from gui.modules.ips_tab import IPSAnalysisTab
ips_tab = IPSAnalysisTab(parent, main_app)
ips_tab.load_ips_file()

# APNS推送测试
from gui.modules.push_tab import PushTestTab
push_tab = PushTestTab(parent, main_app)
push_tab.send_push()

# 沙盒浏览
from gui.modules.sandbox_tab import SandboxBrowserTab
sandbox_tab = SandboxBrowserTab(parent, main_app)
sandbox_tab.refresh_devices()
```

## 开发指南

### 添加新功能
```python
# 1. 添加新的日志格式
def parse_new_format(self, raw_line):
    # 实现新格式解析
    pass

# 2. 添加新的过滤条件
def filter_entries(self, entries, new_condition=None):
    # 实现新过滤逻辑
    pass

# 3. 添加新的导出格式
def export_to_file(self, entries, filepath, format='new'):
    # 实现新格式导出
    pass
```

### 性能优化
- **懒加载**: 大文件使用生成器
- **缓存**: 频繁访问数据缓存
- **并行**: CPU密集型任务多线程
- **索引**: 建立时间戳索引

## 版本历史
- **v2.3.0**: iOS沙盒浏览智能过滤
- **v2.2.0**: 自定义模块分组规则
- **v2.1.0**: 模块分组增强，崩溃检测优化
- **v2.0.0**: 模块化重构完成
- **v1.0.0**: 原始单文件实现

## 最佳实践
- 使用类型注解
- 添加文档字符串
- 遵循PEP 8规范
- 保持向后兼容
- 编写单元测试

---

*最后更新: 2025-10-21*