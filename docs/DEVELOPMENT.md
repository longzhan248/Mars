# 开发指南 (DEVELOPMENT)

本文档为开发者提供项目开发的详细指南，包括环境搭建、架构设计、开发规范和贡献流程。

## 目录
- [开发环境搭建](#开发环境搭建)
- [项目架构](#项目架构)
- [模块化设计](#模块化设计)
- [开发规范](#开发规范)
- [测试指南](#测试指南)
- [调试技巧](#调试技巧)
- [性能优化](#性能优化)
- [贡献流程](#贡献流程)

## 开发环境搭建

### 系统要求
- Python 3.6+ （推荐3.8+）
- macOS、Linux、Windows
- Git

### 快速开始
```bash
# 1. 克隆项目
git clone <repository-url>
cd mars-log-analyzer

# 2. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate     # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 运行项目
python3 gui/mars_log_analyzer_modular.py
# 或使用启动脚本
./scripts/run_analyzer.sh
```

### 开发工具推荐
- **IDE**: PyCharm, VS Code
- **版本控制**: Git, GitHub Desktop
- **调试工具**: pdb, PyCharm Debugger
- **性能分析**: cProfile, memory_profiler
- **代码质量**: pylint, flake8, black

### IDE配置

#### VS Code配置
```json
// .vscode/settings.json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests/"]
}
```

#### PyCharm配置
1. 设置Python解释器为项目虚拟环境
2. 配置代码风格为PEP 8
3. 启用代码检查和自动格式化
4. 设置运行配置为`gui/mars_log_analyzer_modular.py`

## 项目架构

### 整体架构图
```
Mars Log Analyzer
├── 核心解码引擎 (decoders/)
├── GUI用户界面 (gui/)
│   ├── 主程序窗口
│   ├── 模块化组件
│   └── UI组件库
├── AI诊断系统 (gui/modules/ai_diagnosis/)
├── iOS工具集 (gui/modules/obfuscation/, sandbox/, etc.)
├── 工具脚本 (tools/, scripts/)
└── 文档系统 (docs/)
```

### 核心模块

#### 解码器模块 (decoders/)
```python
# 解码器接口设计
class BaseDecoder:
    def decode(self, file_path: str) -> List[LogEntry]:
        """解码xlog文件"""
        pass

    def validate_format(self, file_path: str) -> bool:
        """验证文件格式"""
        pass
```

#### 数据模型 (gui/modules/data_models.py)
```python
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class LogEntry:
    timestamp: str
    level: str
    module: str
    content: str
    raw_line: str
    file_group: Optional[str] = None

    # 性能优化：使用__slots__减少内存占用
    __slots__ = ['timestamp', 'level', 'module', 'content', 'raw_line', 'file_group']
```

#### 文件操作 (gui/modules/file_operations.py)
```python
class FileOperations:
    @staticmethod
    def load_files(file_paths: List[str]) -> List[LogEntry]:
        """加载并解码文件"""
        pass

    @staticmethod
    def export_logs(logs: List[LogEntry], format: str, output_path: str):
        """导出日志"""
        pass
```

### 模块化设计

### GUI架构
```
mars_log_analyzer_modular.py (主程序)
├── 继承 mars_log_analyzer_pro.py
└── 使用模块化组件
    ├── modules/
    │   ├── data_models.py      # 数据结构
    │   ├── file_operations.py  # 文件处理
    │   ├── filter_search.py    # 过滤逻辑
    │   ├── ai_diagnosis/       # AI诊断模块
    │   └── obfuscation/        # 代码混淆模块
    └── components/
        ├── improved_lazy_text.py
        └── scrolled_text_with_lazy_load.py
```

### 模块设计原则

#### 1. 单一职责原则
每个模块只负责一个特定的功能领域：
- `data_models.py`: 数据结构定义
- `file_operations.py`: 文件读写操作
- `filter_search.py`: 搜索和过滤逻辑
- `ai_diagnosis/`: AI相关功能

#### 2. 依赖倒置原则
高层模块不依赖低层模块，都依赖抽象：
```python
# 抽象接口
class LogFilter(ABC):
    @abstractmethod
    def filter(self, logs: List[LogEntry]) -> List[LogEntry]:
        pass

# 具体实现
class LevelFilter(LogFilter):
    def filter(self, logs: List[LogEntry]) -> List[LogEntry]:
        # 实现级别过滤
        pass
```

#### 3. 开闭原则
对扩展开放，对修改关闭：
```python
# 过滤器注册机制
class FilterRegistry:
    def __init__(self):
        self._filters = {}

    def register(self, name: str, filter_class: Type[LogFilter]):
        self._filters[name] = filter_class

    def create_filter(self, name: str, **kwargs) -> LogFilter:
        return self._filters[name](**kwargs)

# 使用示例
registry = FilterRegistry()
registry.register('level', LevelFilter)
registry.register('time', TimeRangeFilter)
registry.register('module', ModuleFilter)
```

## 开发规范

### 代码风格
遵循PEP 8规范，使用black进行格式化：

```bash
# 安装开发依赖
pip install black pylint flake8

# 格式化代码
black .

# 代码检查
pylint gui/
flake8 gui/
```

### 命名规范

#### 文件命名
- 使用小写字母和下划线：`file_operations.py`
- 模块包使用小写：`gui/modules/`
- 类文件使用驼峰式：`customPromptDialog.py` (GUI相关)

#### 变量命名
```python
# 变量和函数：小写+下划线
log_entries = []
def filter_logs():
    pass

# 类名：驼峰式
class LogAnalyzer:
    pass

# 常量：大写+下划线
MAX_LOG_ENTRIES = 1000000
DEFAULT_TIMEOUT = 30

# 私有变量：前缀下划线
class MyClass:
    def __init__(self):
        self._private_var = "private"
        self.__very_private = "very private"
```

### 注释规范

#### 文档字符串
```python
def decode_mars_log(file_path: str, output_dir: str = None) -> List[LogEntry]:
    """
    解码Mars xlog文件。

    Args:
        file_path: xlog文件路径
        output_dir: 输出目录，默认为文件同目录

    Returns:
        解码后的日志条目列表

    Raises:
        FileNotFoundError: 文件不存在
        ValueError: 文件格式错误

    Example:
        >>> logs = decode_mars_log("app.xlog")
        >>> print(len(logs))
        1000
    """
    pass
```

#### 行内注释
```python
# 检查魔数确定压缩格式
magic_byte = file_header[0]
if magic_byte in [0x03, 0x04, 0x05]:
    # 4字节密钥格式
    key_size = 4
elif magic_byte in [0x06, 0x07, 0x08, 0x09]:
    # 64字节密钥格式
    key_size = 64
else:
    # 无压缩格式
    key_size = 0
```

### 错误处理

#### 异常处理原则
```python
# 1. 具体异常捕获
try:
    result = decode_file(file_path)
except FileNotFoundError:
    logger.error(f"文件不存在: {file_path}")
    return []
except ValueError as e:
    logger.error(f"文件格式错误: {e}")
    return []
except Exception as e:
    logger.error(f"未知错误: {e}")
    return []

# 2. 资源管理
with open(file_path, 'rb') as f:
    data = f.read()
    # 自动文件关闭

# 3. 自定义异常
class DecodingError(Exception):
    """解码错误异常"""
    pass

class InvalidFormatError(DecodingError):
    """无效格式异常"""
    pass
```

#### 日志记录
```python
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def process_logs(file_path: str):
    logger.info(f"开始处理文件: {file_path}")

    try:
        logs = decode_file(file_path)
        logger.info(f"成功解码 {len(logs)} 条日志")
        return logs
    except Exception as e:
        logger.error(f"处理失败: {e}", exc_info=True)
        return []
```

## 测试指南

### 测试结构
```
tests/
├── unit/              # 单元测试
│   ├── test_decoders.py
│   ├── test_filters.py
│   └── test_ai_diagnosis.py
├── integration/       # 集成测试
│   ├── test_gui_integration.py
│   └── test_workflow.py
├── performance/       # 性能测试
│   ├── test_memory_usage.py
│   └── test_search_performance.py
└── fixtures/          # 测试数据
    ├── sample_logs/
    └── test_configs/
```

### 单元测试
```python
import unittest
from gui.modules.filter_search import LogFilter

class TestLogFilter(unittest.TestCase):
    def setUp(self):
        self.filter = LogFilter()
        self.sample_logs = [
            LogEntry("2024-01-01 10:00:00", "ERROR", "ModuleA", "Error message"),
            LogEntry("2024-01-01 10:01:00", "INFO", "ModuleB", "Info message"),
        ]

    def test_filter_by_level(self):
        """测试按级别过滤"""
        error_logs = self.filter.filter_by_level(self.sample_logs, "ERROR")
        self.assertEqual(len(error_logs), 1)
        self.assertEqual(error_logs[0].level, "ERROR")

    def test_filter_by_module(self):
        """测试按模块过滤"""
        module_a_logs = self.filter.filter_by_module(self.sample_logs, "ModuleA")
        self.assertEqual(len(module_a_logs), 1)
        self.assertEqual(module_a_logs[0].module, "ModuleA")

if __name__ == '__main__':
    unittest.main()
```

### 性能测试
```python
import time
import memory_profiler
from gui.modules.log_indexer import LogIndexer

class TestPerformance(unittest.TestCase):
    def setUp(self):
        # 生成大量测试数据
        self.large_log_set = self.generate_test_logs(100000)
        self.indexer = LogIndexer()

    def test_indexing_performance(self):
        """测试索引构建性能"""
        start_time = time.time()
        self.indexer.build_index(self.large_log_set)
        end_time = time.time()

        # 索引构建应该在合理时间内完成
        self.assertLess(end_time - start_time, 5.0)  # 5秒内

    @memory_profiler.profile
    def test_memory_usage(self):
        """测试内存使用"""
        # 测试内存占用不超过限制
        self.indexer.build_index(self.large_log_set)
        # memory_profiler会输出内存使用情况

    def test_search_performance(self):
        """测试搜索性能"""
        self.indexer.build_index(self.large_log_set)

        start_time = time.time()
        results = self.indexer.search("keyword")
        end_time = time.time()

        # 搜索应该非常快
        self.assertLess(end_time - start_time, 0.01)  # 10ms内
```

### 运行测试
```bash
# 运行所有测试
python -m pytest tests/

# 运行特定测试
python -m pytest tests/unit/test_filters.py

# 生成覆盖率报告
python -m pytest tests/ --cov=gui --cov-report=html

# 性能测试
python -m pytest tests/performance/ -v
```

## 调试技巧

### 日志调试
```python
import logging

# 设置详细日志
logging.getLogger().setLevel(logging.DEBUG)

# 在关键位置添加日志
def decode_log_entry(data):
    logger.debug(f"开始解码日志条目，数据长度: {len(data)}")

    try:
        # 解码逻辑
        entry = parse_entry(data)
        logger.debug(f"解码成功: {entry.module} - {entry.level}")
        return entry
    except Exception as e:
        logger.error(f"解码失败: {e}", exc_info=True)
        raise
```

### 断点调试
```python
import pdb

def complex_function(data):
    # 在关键位置设置断点
    pdb.set_trace()  # 程序会在此处暂停

    processed_data = preprocess(data)
    result = analyze(processed_data)
    return result
```

### 性能分析
```python
import cProfile
import pstats

def profile_function():
    pr = cProfile.Profile()
    pr.enable()

    # 要分析的代码
    result = process_large_dataset()

    pr.disable()
    stats = pstats.Stats(pr)
    stats.sort_stats('cumulative')
    stats.print_stats(10)  # 显示前10个最耗时的函数

    return result
```

### 内存调试
```python
import tracemalloc

def debug_memory_usage():
    # 开始内存跟踪
    tracemalloc.start()

    # 执行代码
    process_logs()

    # 获取内存使用情况
    current, peak = tracemalloc.get_traced_memory()
    print(f"当前内存使用: {current / 1024 / 1024:.1f} MB")
    print(f"峰值内存使用: {peak / 1024 / 1024:.1f} MB")

    tracemalloc.stop()
```

## 性能优化

### 内存优化
```python
# 使用__slots__减少内存占用
class OptimizedLogEntry:
    __slots__ = ['timestamp', 'level', 'module', 'content', 'raw_line']

    def __init__(self, timestamp, level, module, content, raw_line):
        self.timestamp = timestamp
        self.level = level
        self.module = module
        self.content = content
        self.raw_line = raw_line

# 使用生成器处理大文件
def process_large_file(file_path):
    with open(file_path, 'r') as f:
        for line in f:
            yield parse_log_line(line)

# 使用弱引用缓存
import weakref
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_pattern(regex_str):
    """缓存编译后的正则表达式"""
    return re.compile(regex_str)
```

### 搜索优化
```python
# 预编译正则表达式
class SearchOptimizer:
    def __init__(self):
        self._compiled_patterns = {}

    def search(self, logs, pattern):
        if pattern not in self._compiled_patterns:
            self._compiled_patterns[pattern] = re.compile(pattern)

        compiled = self._compiled_patterns[pattern]
        return [log for log in logs if compiled.search(log.content)]

# 使用索引加速搜索
class LogIndexer:
    def __init__(self):
        self.word_index = {}
        self.module_index = {}
        self.level_index = {}

    def build_index(self, logs):
        """构建倒排索引"""
        for i, log in enumerate(logs):
            # 词汇索引
            for word in set(log.content.lower().split()):
                if word not in self.word_index:
                    self.word_index[word] = []
                self.word_index[word].append(i)

            # 模块索引
            if log.module not in self.module_index:
                self.module_index[log.module] = []
            self.module_index[log.module].append(i)

            # 级别索引
            if log.level not in self.level_index:
                self.level_index[log.level] = []
            self.level_index[log.level].append(i)
```

### UI渲染优化
```python
# 虚拟滚动实现
class VirtualScrollList:
    def __init__(self, master, total_items, item_height, visible_items):
        self.master = master
        self.total_items = total_items
        self.item_height = item_height
        self.visible_items = visible_items
        self.start_index = 0

        # 只创建可见的控件
        self.visible_widgets = []
        self.create_visible_widgets()

    def on_scroll(self, *args):
        """滚动事件处理"""
        new_start = self.get_start_index()
        if new_start != self.start_index:
            self.start_index = new_start
            self.update_visible_widgets()

    def create_visible_widgets(self):
        """只创建可见范围内的控件"""
        for i in range(self.visible_items):
            widget = self.create_item_widget(i)
            self.visible_widgets.append(widget)

    def update_visible_widgets(self):
        """更新可见控件内容"""
        for i, widget in enumerate(self.visible_widgets):
            item_index = self.start_index + i
            if item_index < self.total_items:
                widget.update_content(self.get_item_data(item_index))
                widget.pack()
            else:
                widget.pack_forget()
```

## 贡献流程

### 1. 分支管理
```bash
# 创建功能分支
git checkout -b feature/new-feature

# 创建修复分支
git checkout -b fix/bug-description

# 创建优化分支
git checkout -b optimize/performance-improvement
```

### 2. 提交规范
```bash
# 提交格式
<type>(<scope>): <subject>

<body>

<footer>
```

#### 提交类型
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式化
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具相关

#### 提交示例
```bash
# 新功能提交
git commit -m "feat(ai): 添加自定义Prompt模板功能

- 支持用户创建和管理自定义Prompt模板
- 实现变量替换和分类管理
- 添加导入/导出功能

Closes #123"

# 修复提交
git commit -m "fix(decoder): 修复大文件解码内存泄漏问题

使用生成器处理大文件，避免一次性加载到内存"

# 文档提交
git commit -m "docs: 更新AI诊断功能使用文档

添加自定义Prompt功能的详细说明和示例"
```

### 3. 代码审查清单

#### 功能性
- [ ] 功能按预期工作
- [ ] 边界条件处理正确
- [ ] 错误处理完善
- [ ] 性能满足要求

#### 代码质量
- [ ] 代码风格符合规范
- [ ] 命名清晰有意义
- [ ] 注释充分准确
- [ ] 没有重复代码

#### 测试
- [ ] 单元测试覆盖主要功能
- [ ] 集成测试通过
- [ ] 性能测试满足要求
- [ ] 手动测试验证

#### 文档
- [ ] README更新
- [ ] API文档更新
- [ ] 注释完善
- [ ] 变更日志更新

### 4. 发布流程
```bash
# 1. 合并到主分支
git checkout main
git merge feature/new-feature

# 2. 更新版本号
# 更新 __version__.py 或 setup.py

# 3. 生成变更日志
# 更新 CHANGELOG.md

# 4. 创建标签
git tag -a v1.2.0 -m "Release version 1.2.0"

# 5. 推送到远程
git push origin main
git push origin v1.2.0

# 6. 创建Release (GitHub)
# 在GitHub上创建Release，包含变更日志
```

### 5. 开发工具配置

#### Git Hooks
```bash
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 22.3.0
    hooks:
      - id: black
        language_version: python3.8

  - repo: https://github.com/pycqa/pylint
    rev: v2.14.0
    hooks:
      - id: pylint
        args: [--disable=C0114,C0115]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v0.950
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

#### 持续集成
```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.6, 3.7, 3.8, 3.9, '3.10']

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt

    - name: Run tests
      run: |
        pytest tests/ --cov=gui --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v1
```

---

## 常见问题

### Q: 如何调试GUI界面问题？
A: 使用日志记录和异常处理，在关键位置添加调试信息：

```python
def on_button_click(self):
    try:
        logger.info("按钮被点击")
        self.process_data()
        logger.info("数据处理完成")
    except Exception as e:
        logger.error(f"按钮点击处理失败: {e}", exc_info=True)
        messagebox.showerror("错误", f"操作失败: {e}")
```

### Q: 如何优化大文件处理性能？
A:
1. 使用流式处理，避免一次性加载大文件
2. 实现懒加载和虚拟滚动
3. 使用索引加速搜索
4. 合理使用缓存

### Q: 如何添加新的AI服务支持？
A: 实现`AIClient`接口：

```python
class CustomAIClient(AIClient):
    def __init__(self, api_key: str, model: str):
        super().__init__(api_key, model)
        self.client = CustomAPI(api_key)

    async def analyze_logs(self, logs: List[LogEntry]) -> str:
        # 实现自定义分析逻辑
        pass

    def test_connection(self) -> bool:
        # 测试连接
        pass
```

### Q: 如何编写好的测试？
A:
1. 遵循AAA模式（Arrange, Act, Assert）
2. 测试边界条件和异常情况
3. 使用有意义的测试数据
4. 保持测试独立和可重复

---

*本文档随项目发展持续更新，请关注最新版本。*