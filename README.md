# Mars xLog Analyzer Tool Suite

用于解码和分析 Mars xlog 文件的完整工具套件，包含命令行工具、GUI应用、IPS崩溃分析和iOS推送测试功能。

## ✨ 特性

- 🚀 **高性能解码** - 支持多种Mars xlog格式
- 📊 **可视化分析** - 强大的GUI分析工具
- 🔍 **智能搜索** - 支持正则表达式和多条件过滤
- 📱 **iOS工具集** - 集成IPS崩溃分析和APNS推送测试
- 📦 **独立应用** - 可打包为无需Python环境的.app文件
- 🎯 **模块化设计** - 清晰的代码结构，易于扩展

## 快速开始

### 开发模式（需要Python环境）

```bash
# 使用启动脚本（推荐，自动处理依赖）
./scripts/run_analyzer.sh

# 或手动启动GUI
source venv/bin/activate
python3 gui/mars_log_analyzer_modular.py
```

### 独立应用（无需Python环境）

```bash
# 打包成独立应用
./scripts/build_app.sh

# 打包后的应用位于
# dist/MarsLogAnalyzer.app
```

## 核心功能

### 1. Mars日志分析
- 解码各种格式的xlog文件
- 可视化日志级别分布
- 时间线分析和统计
- 多条件过滤和搜索

### 2. IPS崩溃分析
- 解析iOS崩溃报告
- 符号化堆栈跟踪
- 提取关键崩溃信息

### 3. iOS推送测试
- APNS推送发送测试
- 支持沙盒和生产环境
- 证书管理和历史记录

## 项目结构

```
.
├── decoders/                    # 解码器核心模块
├── gui/                         # GUI应用程序
│   ├── modules/                 # 功能模块
│   └── components/              # UI组件
├── push_tools/                  # iOS推送测试工具
├── tools/                       # 工具脚本
├── scripts/                     # 启动和打包脚本
│   ├── run_analyzer.sh          # 启动脚本
│   └── build_app.sh             # 打包脚本
├── docs/                        # 文档目录
│   ├── BUILD.md                 # 打包指南
│   └── CLAUDE.md                # 开发指南
├── MarsLogAnalyzer.spec         # PyInstaller配置
└── requirements.txt             # 项目依赖
```

## 系统要求

### 开发/运行Python版本
- macOS / Linux / Windows
- Python 3.8 或更高版本
- tkinter (Python自带)

### 运行独立应用
- macOS 10.13 或更高版本
- **无需Python环境**
- **无需任何依赖**

## 详细文档

- 📘 [中文文档](docs/README_CN.md) - 完整使用说明
- 📗 [English Documentation](docs/README_EN.md) - Full documentation
- 📙 [打包指南](docs/BUILD.md) - 应用打包和分发
- 📕 [开发指南](CLAUDE.md) - 项目架构和开发

## 更新日志

### 2025-09-28
- ✅ 添加PyInstaller打包支持
- ✅ 一键打包脚本
- ✅ 完整打包文档

### 2025-09-27
- ✅ 模块化重构完成
- ✅ 集成iOS推送测试
- ✅ 统一GUI界面

## 许可证

本项目仅供学习和研究使用。

## 贡献

欢迎提交Issue和Pull Request！