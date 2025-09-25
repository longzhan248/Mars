# 项目文件结构说明

## 📁 核心文件

### 主程序文件
- **mars_log_analyzer_pro.py** - 主程序入口，包含GUI界面和所有功能模块
  - 1700+ 行代码
  - 包含所有UI组件和业务逻辑
  - 支持多语言（中文界面）

### 解码器模块
- **decode_mars_nocrypt_log_file_py3.py** - Mars xlog核心解码器
  - 处理压缩和加密格式
  - Python 3 兼容版本
  - 支持多种Magic Number格式

- **fast_decoder.py** - 快速并行解码器
  - 多文件并行处理
  - 线程池管理
  - 进度回调机制

- **optimized_decoder.py** - 优化解码器（实验性）
  - 文件分块处理
  - 内存优化
  - 适合超大文件

### UI组件
- **scrolled_text_with_lazy_load.py** - 懒加载文本组件
  - 按需加载显示
  - 优化大文件显示性能
  - 支持标签样式

## 📜 启动脚本

### 跨平台
- **run_analyzer.py** - Python跨平台启动器
  - 自动检测系统
  - 创建虚拟环境
  - 安装依赖

### 平台特定
- **run_analyzer.sh** - Mac/Linux启动脚本
  - Bash脚本
  - 自动环境配置
  - 依赖检查

- **run_analyzer.bat** - Windows批处理脚本
  - CMD脚本
  - 环境变量设置
  - 错误处理

## 📚 文档文件

### 用户文档
- **README.md** - 项目主页（英文）
- **README_CN.md** - 中文使用文档
- **README_EN.md** - 英文详细文档
- **INSTALL.md** - 安装部署指南
- **PROJECT_STRUCTURE.md** - 本文件

### 技术文档
- **CLAUDE.md** - 技术架构文档
  - API说明
  - 代码结构
  - 扩展指南

### 配置文件
- **requirements.txt** - Python依赖包列表
  - matplotlib (必需)
  - numpy (可选)
  - pandas (可选)

## 🗂️ 生成文件（运行时）

### 虚拟环境
```
venv/
├── bin/           (Mac/Linux)
├── Scripts/       (Windows)
├── lib/
└── include/
```

### 日志文件
```
*.xlog            # 原始Mars日志
*.xlog.log        # 解析后的文本日志
```

### 导出文件
```
module_*.txt      # 模块导出报告
report_*.txt      # 分析报告
filtered_*.txt    # 过滤结果
```

## 🔧 文件功能对照表

| 文件名 | 功能 | 必需 | 大小 |
|--------|------|------|------|
| mars_log_analyzer_pro.py | 主程序 | ✅ | ~80KB |
| decode_mars_nocrypt_log_file_py3.py | 解码器 | ✅ | ~10KB |
| fast_decoder.py | 并行处理 | ✅ | ~5KB |
| scrolled_text_with_lazy_load.py | UI组件 | ✅ | ~5KB |
| run_analyzer.* | 启动脚本 | ⚠️ | ~2KB |
| requirements.txt | 依赖列表 | ⚠️ | <1KB |
| README*.md | 文档 | 📖 | ~20KB |

说明：
- ✅ 必需 - 程序运行必需文件
- ⚠️ 推荐 - 提升使用体验
- 📖 文档 - 帮助和说明文件

## 💾 存储需求

### 最小安装
- 程序文件：~150KB
- Python环境：~50MB
- 依赖包：~50MB
- **总计：~100MB**

### 典型使用
- 程序+环境：~100MB
- 日志文件：取决于xlog大小
- 解析结果：约为xlog的2倍
- **建议预留：500MB+**

## 🚀 部署方式

### 开发环境
```
项目目录/
├── 所有.py文件
├── 所有文档
├── venv/
└── *.log
```

### 生产环境
```
安装目录/
├── mars_log_analyzer_pro.py
├── decode_mars_nocrypt_log_file_py3.py
├── fast_decoder.py
├── scrolled_text_with_lazy_load.py
├── run_analyzer.*
└── venv/
```

### 打包发布
```
dist/
├── MarsLogAnalyzer.exe  (Windows)
├── MarsLogAnalyzer.app  (Mac)
└── MarsLogAnalyzer      (Linux)
```

## 🔄 版本管理

### 版本号规则
- 主版本：重大功能更新
- 次版本：功能增强
- 修订版：Bug修复

### 当前版本
- v1.0.0 - 专业版发布
  - 完整功能实现
  - 跨平台支持
  - 文档完善

### 更新检查
程序启动时不会自动检查更新，需要手动下载新版本。

## 📝 开发说明

### 代码规范
- Python 3.6+ 语法
- UTF-8 编码
- PEP 8 风格指南

### 扩展开发
1. 新增解码器：继承基础解码类
2. 新增UI组件：使用tkinter框架
3. 新增分析功能：在主程序添加方法

### 测试方法
```python
# 单元测试
python -m unittest test_*.py

# 集成测试
python mars_log_analyzer_pro.py --test
```

---

最后更新：2024年1月