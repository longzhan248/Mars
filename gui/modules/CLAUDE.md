# CLAUDE.md - 模块化组件技术指南

## 模块概述
Mars日志分析器的核心模块化组件，提供数据模型、文件操作、过滤搜索等基础功能。这些模块从原始的3784行单文件中提取，实现了高内聚低耦合的设计目标。

## 模块架构

### 目录结构
```
modules/
├── __init__.py              # 模块初始化
├── data_models.py           # 数据模型定义
├── file_operations.py       # 文件操作封装
├── filter_search.py         # 过滤搜索管理
├── ips_tab.py              # IPS崩溃分析标签页
├── push_tab.py             # iOS推送测试标签页
└── sandbox_tab.py          # iOS沙盒浏览标签页 🆕
```

## 核心模块详解

### 1. data_models.py - 数据模型模块

#### LogEntry类
日志条目的核心数据结构。

**属性**：
- `raw_line`: 原始日志行
- `source_file`: 来源文件路径
- `level`: 日志级别（INFO/WARNING/ERROR/DEBUG/VERBOSE/FATAL）
- `timestamp`: 时间戳
- `module`: 模块名
- `content`: 日志内容
- `thread_id`: 线程ID
- `is_crash`: 是否为崩溃日志
- `is_stacktrace`: 是否为堆栈信息

**关键方法**：
```python
def __init__(self, raw_line, source_file=""):
    """初始化并自动解析日志行"""

def parse(self):
    """解析日志格式，支持多种格式"""

def _is_crash_content(self, content, location=""):
    """检测崩溃标识，避免误判"""
```

**支持的日志格式**：
1. Mars标准格式：`[级别][时间戳][模块][线程ID] 内容`
2. iOS崩溃格式：`*** Terminating app due to uncaught exception`
3. 堆栈格式：`0 CoreFoundation 0x00000001897c92ec`

#### FileGroup类
文件分组管理，支持多文件合并处理。

**属性**：
- `base_name`: 基础名称
- `files`: 文件路径列表
- `entries`: 合并后的日志条目

**关键方法**：
```python
def add_file(self, filepath):
    """添加文件到组"""

def get_display_name(self):
    """获取显示名称，单文件返回文件名，多文件返回组名"""
```

### 2. file_operations.py - 文件操作模块

#### FileOperations类
统一的文件操作接口。

**核心功能**：
- **文件加载**: 支持.xlog、.log、.txt、.ips格式
- **解码处理**: 自动解码Mars xlog格式
- **导出功能**: 支持TXT、JSON、CSV格式
- **进度回调**: 异步加载时的进度反馈

**关键方法**：
```python
def load_file(self, filepath, callback=None):
    """加载日志文件，支持进度回调"""

def decode_xlog(self, filepath):
    """解码Mars xlog格式文件"""

def export_to_file(self, entries, filepath, format='txt'):
    """导出日志到文件，支持多种格式"""
```

**导出格式说明**：
- **TXT**: 纯文本格式，保持原始日志格式
- **JSON**: 结构化JSON，包含所有字段
- **CSV**: 表格格式，便于Excel分析

### 3. filter_search.py - 过滤搜索管理

#### FilterSearchManager类
统一的过滤和搜索逻辑管理。

**核心功能**：
- **多条件过滤**: 级别、模块、时间、关键词
- **时间解析**: 支持多种时间格式和时区
- **正则搜索**: 完整正则表达式支持
- **性能优化**: 短路求值，提前退出

**关键方法**：
```python
def filter_entries(self, entries, level=None, module=None,
                   keyword=None, start_time=None, end_time=None,
                   search_mode="普通"):
    """统一的过滤入口，支持组合条件"""

def parse_time_string(self, time_str):
    """解析时间字符串，支持时区"""

def compare_log_time(self, log_timestamp, start_time, end_time):
    """时间范围比较，处理时区"""
```

**时间格式支持**：
1. `2025-09-21 13:09:49`
2. `2025-09-21 +8.0 13:09:49.038`
3. `2025-09-21 +08:00 13:09:49`
4. `2025-09-21T13:09:49+08:00`

### 4. ips_tab.py - IPS崩溃分析标签页

#### IPSAnalysisTab类
iOS崩溃报告分析界面。

**核心功能**：
- **IPS解析**: JSON格式崩溃报告解析
- **符号化**: 支持dSYM符号文件
- **堆栈美化**: 格式化堆栈显示
- **结果导出**: 导出分析结果

**界面组件**：
```python
def __init__(self, parent, main_app):
    """初始化IPS分析标签页"""

def create_widgets(self):
    """创建UI组件"""

def load_ips_file(self):
    """加载IPS文件"""

def parse_ips(self, filepath):
    """解析IPS崩溃报告"""
```

**IPS文件结构**：
- `description`: 崩溃描述
- `timestamp`: 崩溃时间
- `exception`: 异常信息
- `threads`: 线程堆栈
- `binaryImages`: 二进制镜像

### 5. push_tab.py - iOS推送测试标签页

#### PushTestTab类
iOS APNS推送测试界面。

**核心功能**：
- **证书管理**: 支持.p12、.pem格式
- **推送发送**: HTTP/2协议实现
- **历史记录**: 保存推送历史
- **Payload模板**: 预设推送模板

**界面组件**：
```python
def __init__(self, parent, main_app):
    """初始化推送测试标签页"""

def create_widgets(self):
    """创建UI组件"""

def send_push(self):
    """发送推送通知"""

def load_certificate(self):
    """加载推送证书"""
```

**推送配置**：
- **环境**: 开发环境/生产环境
- **证书**: P12/PEM格式
- **Token**: 设备令牌
- **Payload**: JSON推送内容

### 6. sandbox_tab.py - iOS沙盒浏览标签页 🆕

#### SandboxBrowserTab类
iOS应用沙盒文件浏览器。

**核心功能**：
- **设备管理**: 自动检测iOS设备，显示设备名称和型号
- **应用列表**: 列出所有用户应用
- **文件浏览**: 树形结构展示应用沙盒文件系统
- **文件预览**: 支持文本、图片、十六进制等多种格式
- **文件操作**: 预览、导出、打开、删除文件
- **搜索功能**: 支持文件名和文件内容搜索，递归遍历所有目录

**界面组件**：
```python
def __init__(self, parent, main_app):
    """初始化沙盒浏览标签页"""

def create_widgets(self):
    """创建UI组件"""

def refresh_devices(self):
    """刷新设备列表"""

def on_tree_expand(self, event):
    """树形节点展开事件"""

def preview_selected(self):
    """预览选中的文件"""

def search_files(self):
    """搜索文件，支持文件名和内容搜索"""

def clear_search(self):
    """清除搜索结果，恢复正常浏览"""
```

**搜索功能**：
- 🔍 **搜索类型**: 文件名、文件内容、所有
- 🚀 **异步搜索**: 不阻塞UI的后台搜索
- 📊 **实时进度**: 显示搜索进度
- 🎯 **结果高亮**: 搜索结果蓝色显示
- 🏷️ **匹配标记**: 显示[文件名]或[文件内容]标签
- 📁 **递归搜索**: 自动搜索所有子目录

**文件预览支持**：
- 📝 **文本文件**: .txt, .log, .json, .xml, .plist, .html, .css, .js, .py, .md, .sh, .h, .m, .swift, .c, .cpp
- 🖼️ **图片文件**: .png, .jpg, .jpeg, .gif, .bmp, .ico（需要Pillow库）
- 🔢 **十六进制**: 其他未识别格式显示hex dump
- 💾 **数据库**: 识别SQLite数据库文件

**技术实现**：
- 使用pymobiledevice3库进行iOS设备通信
- HouseArrestService访问应用沙盒
- AfcService进行文件系统操作
- 异步加载防止UI阻塞
- 占位符机制实现懒加载目录

**事件处理**：
- `<<TreeviewOpen>>`: 展开目录时加载子目录
- 双击文件：打开预览窗口
- 右键菜单：显示操作选项

## 模块间交互

### 依赖关系
```
mars_log_analyzer_modular.py
    ├── data_models.py (数据结构)
    ├── file_operations.py (文件处理)
    ├── filter_search.py (过滤逻辑)
    ├── ips_tab.py (IPS界面)
    ├── push_tab.py (推送界面)
    └── sandbox_tab.py (沙盒浏览界面) 🆕
```

### 数据流向
1. **加载流程**: FileOperations → LogEntry → FilterSearchManager
2. **过滤流程**: UI事件 → FilterSearchManager → 显示更新
3. **导出流程**: 过滤结果 → FileOperations → 文件系统

### 接口约定
- 所有模块使用统一的LogEntry数据结构
- 回调函数签名：`callback(progress, message)`
- 过滤器返回：`List[LogEntry]`

## 开发指南

### 添加新的日志格式
1. 在`LogEntry.parse()`中添加格式匹配
2. 更新`LEVEL_MAP`映射表
3. 添加相应的测试用例

### 添加新的过滤条件
1. 在`FilterSearchManager.filter_entries()`添加参数
2. 实现过滤逻辑
3. 更新UI绑定

### 添加新的导出格式
1. 在`FileOperations.export_to_file()`添加格式分支
2. 实现格式化逻辑
3. 更新文件对话框过滤器

### 性能优化建议
1. **懒加载**: 大文件使用生成器
2. **缓存**: 频繁访问的数据缓存
3. **并行**: CPU密集型任务多线程
4. **索引**: 建立时间戳索引

## 测试要求

### 单元测试
```python
# 测试LogEntry解析
entry = LogEntry("[I][2025-09-21 +8.0 13:09:49][Module] Message")
assert entry.level == "INFO"
assert entry.module == "Module"

# 测试FileGroup
group = FileGroup("test")
group.add_file("test.log")
assert group.get_display_name() == "test.log"

# 测试过滤器
manager = FilterSearchManager()
filtered = manager.filter_entries(entries, level="ERROR")
assert all(e.level == "ERROR" for e in filtered)
```

### 集成测试
1. 加载各种格式文件
2. 组合过滤条件测试
3. 导出格式验证
4. UI交互测试

## 故障排查

### 常见问题

#### Q: 日志解析失败？
- 检查日志格式是否支持
- 查看`LogEntry.parse()`中的正则匹配
- 确认字符编码（UTF-8）

#### Q: 过滤不生效？
- 验证过滤条件格式
- 检查时间字符串解析
- 确认`filter_logs()`重写

#### Q: 导出失败？
- 检查文件权限
- 验证导出格式
- 查看错误日志

#### Q: 内存占用高？
- 使用懒加载模式
- 限制缓存大小
- 及时清理临时数据

## 版本历史

### v2.0.0 (2025-09-27)
- 完成模块化重构
- 从单文件3784行拆分为5个模块
- 修复`filter_logs()`方法问题
- 统一过滤逻辑路径

### v1.0.0 (原始版本)
- 单文件实现
- 所有功能耦合
- 维护困难

## 未来规划

### 短期改进
- [ ] 添加模块单元测试
- [ ] 优化导入路径处理
- [ ] 完善错误处理

### 中期目标
- [ ] 插件化架构
- [ ] 配置管理模块
- [ ] 主题系统支持

### 长期规划
- [ ] 微服务拆分
- [ ] RESTful API
- [ ] Web版本支持

## 维护指南

### 代码规范
- 使用类型注解
- 添加文档字符串
- 遵循PEP 8规范
- 保持向后兼容

### 发布流程
1. 运行测试套件
2. 更新版本号
3. 更新CHANGELOG
4. 创建Git标签

### 贡献指南
1. Fork项目
2. 创建特性分支
3. 提交Pull Request
4. 代码审查