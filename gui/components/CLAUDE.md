# CLAUDE.md - UI组件模块

## 模块概述
高性能GUI组件集合，专门为处理大规模日志数据设计。核心特性是懒加载和虚拟滚动，可流畅处理百万级日志条目。

## 核心组件

### improved_lazy_text.py - 改进版懒加载文本
当前主要使用的高性能文本显示组件。

#### 核心特性
- **虚拟滚动**: 只渲染可见区域，支持百万级数据
- **懒加载**: 按需加载内容，减少内存占用
- **LRU缓存**: 智能缓存管理，10,000行缓存
- **批量渲染**: 避免逐行更新，提升性能
- **防抖动**: 滚动事件50ms延迟，减少UI更新

#### 关键API
```python
# 基础使用
widget = ImprovedLazyText(parent_frame)
widget.set_content(log_lines)
widget.scroll_to_line(1000)

# 搜索功能
results = widget.search("ERROR")
widget.highlight_line(line_num, 'red')
```

#### 性能指标
| 数据量 | 加载时间 | 内存占用 | 滚动FPS |
|--------|---------|---------|---------|
| 100K行 | <0.5s | 50MB | 60 |
| 1M行 | <2s | 200MB | 45-60 |
| 10M行 | <10s | 500MB | 30-45 |

### scrolled_text_with_lazy_load.py - 基础版懒加载
备用方案，适合中等数据量场景。

#### 组件对比
| 特性 | ImprovedLazyText | LazyLoadText |
|------|-----------------|--------------|
| 虚拟滚动 | 高级实现 | 基础实现 |
| 缓存策略 | LRU缓存 | FIFO |
| 适用规模 | >1M行 | <100K行 |
| 兼容性 | Python 3.6+ | 兼容更广 |

## 技术实现

### 虚拟滚动原理
```python
# 计算可见区域
visible_lines = viewport_height / line_height
render_start = max(0, current_line - buffer_size)
render_end = min(total_lines, current_line + visible_lines + buffer_size)
```

### 缓存机制
```python
# LRU缓存实现
cache = OrderedDict()
cache_size = 10000

def get_line(line_number):
    if line_number in cache:
        cache.move_to_end(line_number)  # 最近使用
        return cache[line_number]
    # 加载并缓存，清理旧条目
```

### 性能优化
- **批量渲染**: 一次性插入多行
- **异步加载**: 后台线程处理数据
- **防抖动**: 滚动事件延迟处理
- **内存管理**: 及时释放不需要的数据

## 使用方法

### 基础集成
```python
# 优先使用改进版
try:
    from improved_lazy_text import ImprovedLazyText as LazyLoadText
except ImportError:
    from scrolled_text_with_lazy_load import LazyLoadText

# 创建和使用
widget = LazyLoadText(parent_frame)
widget.pack(fill='both', expand=True)
widget.set_content(log_lines)
```

### 自定义扩展
```python
class CustomLazyText(ImprovedLazyText):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bind('<Control-f>', self.quick_search)
        self.bind('<Control-g>', self.goto_line)
```

## 配置参数
```python
# 性能配置
BUFFER_SIZE = 50      # 缓冲区大小
CACHE_SIZE = 10000    # 缓存行数
UPDATE_DELAY = 50     # 更新延迟(ms)
CHUNK_SIZE = 1000     # 批处理大小

# 显示配置
LINE_HEIGHT = 20      # 行高(像素)
FONT_FAMILY = 'Consolas'
FONT_SIZE = 10
```

## 常见问题

**Q: 滚动卡顿？**
- 检查缓冲区大小设置
- 优化渲染批次大小
- 确保使用异步加载

**Q: 内存占用过高？**
- 减少CACHE_SIZE缓存大小
- 及时清理不需要的数据
- 使用基础版组件

**Q: 搜索太慢？**
- 建立搜索索引
- 使用正则表达式优化
- 在后台线程执行搜索

**Q: 兼容性问题？**
- Python 3.6+: 使用改进版
- 较老版本: 使用基础版
- 检查tkinter版本兼容性

## 平台支持
- **macOS**: 完全支持，触控板优化
- **Linux**: 需要安装等宽字体
- **Windows**: 支持高DPI显示

## 依赖管理
```python
# 核心依赖
tkinter >= 8.6
threading (标准库)
collections (标准库)

# 可选依赖
numpy  # 性能优化
pillow  # 图像渲染
```

---

*最后更新: 2025-10-21*