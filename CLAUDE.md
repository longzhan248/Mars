# CLAUDE.md

此文件为 Claude Code (claude.ai/code) 在此代码库中工作时提供指导。

## 项目用途
此代码库是**心娱开发助手 (Xinyu DevTools)** - 一站式iOS开发工具集，集成日志分析、崩溃解析、推送测试、沙盒浏览和代码混淆等功能。
核心包含用于解码和分析 Mars xlog 文件的完整工具套件 - Mars 是腾讯的日志框架，xlog 是其使用的压缩和加密日志文件格式。

## 快速开始

### 一键启动（macOS）
```bash
# 1. 下载或克隆项目到任意目录
# 2. 进入项目目录
cd /path/to/project

# 3. 运行启动脚本（自动处理所有环境配置）
./scripts/run_analyzer.sh
```

首次运行会自动：
- ✅ 创建Python虚拟环境
- ✅ 安装所有必要依赖
- ✅ 启动主程序

## 核心功能概览

### 📊 Mars日志分析 + AI智能诊断 🤖
- xlog文件解码和分析
- AI驱动的崩溃分析、性能诊断、问题总结
- 自定义Prompt模板支持
- 智能搜索和跳转功能

### 🔧 iOS开发工具集
- **IPS崩溃解析** - iOS崩溃报告符号化
- **APNS推送测试** - 完整的推送测试工具
- **iOS沙盒浏览** - 设备文件系统浏览
- **dSYM分析** - 崩溃地址符号化
- **LinkMap分析** - 二进制大小分析
- **iOS代码混淆** - App Store审核应对方案

### ⚡ 性能优化
- 倒排索引搜索系统 (搜索性能提升93%)
- 流式文件加载 (支持GB级文件)
- 内存优化 (内存占用减少70%)
- 懒加载UI渲染 (支持百万级日志)

## 近期重要更新

- **2025-10-23**: 超大文件重构完成 ✅ - 5个超大文件全部拆分为35个模块，代码质量大幅提升
- **2025-10-20**: 自定义Prompt功能 📝 - 用户可创建和管理AI提示词模板
- **2025-10-17**: AI助手跳转功能增强 🎯 - 完整的交互式日志导航体验
- **2025-10-16**: AI智能诊断功能完成 🤖 - 多AI服务支持的完整日志分析系统
- **2025-10-14**: iOS代码混淆功能完成 🔐 - 应对App Store审核的完整解决方案
- **2025-10-11**: 性能优化集成完成 🚀 - 搜索和加载性能大幅提升

*详细更新历史请参考 [CHANGELOG.md](CHANGELOG.md)*

## 使用命令

### 启动GUI分析系统（推荐）：
```bash
# 使用启动脚本（推荐，自动处理依赖和环境）
./scripts/run_analyzer.sh

# 或手动启动（需要先激活虚拟环境）
source venv/bin/activate
python3 gui/mars_log_analyzer_modular.py
```

### 独立启动iOS推送工具：
```bash
# 独立启动推送工具GUI
./scripts/run_push_tool.sh

# 或直接运行
python3 push_tools/apns_gui.py
```

### 命令行解码：
```bash
# Python 3版本解码单个文件
python3 decoders/decode_mars_nocrypt_log_file_py3.py mizhua_20250915.xlog

# 批量解码当前目录所有xlog文件
python3 decoders/decode_mars_nocrypt_log_file_py3.py

# 解码指定目录
python3 decoders/decode_mars_nocrypt_log_file_py3.py /path/to/xlog/directory/
```

### iOS代码混淆：
```bash
# GUI使用
./scripts/run_analyzer.sh  # 选择"iOS代码混淆"标签页

# CLI使用
python -m gui.modules.obfuscation.obfuscation_cli \
    --project /path/to/ios/project \
    --output /path/to/obfuscated \
    --template standard
```

## 项目结构概览

```
.
├── decoders/              # 解码器核心模块
├── gui/                   # GUI应用程序
│   ├── modules/           # 模块化组件
│   └── components/        # UI组件
├── push_tools/            # iOS推送测试工具
├── tools/                 # 辅助工具
├── scripts/               # 启动和打包脚本
├── docs/                  # 文档目录
│   ├── technical/         # 技术文档
│   ├── CHANGELOG.md       # 详细更新历史
│   ├── FEATURES.md        # 功能详细说明
│   └── DEVELOPMENT.md     # 开发指南
└── venv/                  # Python虚拟环境
```

## 重要说明

### 系统要求
- Python 3.6+ （推荐3.8+）
- macOS、Linux、Windows
- GUI系统需要 tkinter 和 matplotlib 库

### 环境管理
项目完全可移植，可放置在任何路径下运行：
- 自动创建Python虚拟环境
- 智能依赖检测和安装
- 无硬编码路径设计

### 常见问题

**Q: 提示"No module named 'cryptography'"？**
```bash
# 确保在项目根目录，激活虚拟环境并重新安装依赖
source venv/bin/activate
pip install -r requirements.txt
```

**Q: GUI程序打不开怎么办？**
使用 `./scripts/run_analyzer.sh` 启动，它会自动处理所有依赖。

**Q: 详细功能说明在哪里？**
请参考 [FEATURES.md](FEATURES.md) 获取完整的功能使用说明。

**Q: 如何参与开发？**
请参考 [DEVELOPMENT.md](DEVELOPMENT.md) 获取开发指南。

## 技术文档目录

详细的技术文档存放在 `docs/technical/` 目录下，包含：
- 性能优化分析报告
- AI集成技术文档
- iOS工具开发文档
- Bug修复记录和重构总结
- [超大文件重构总结](docs/technical/REFACTORING_LARGE_FILES.md) - 完整的代码重构记录

## 快速参考

### 主要功能入口
- **主程序**: `gui/mars_log_analyzer_modular.py`
- **启动脚本**: `./scripts/run_analyzer.sh`
- **打包脚本**: `./scripts/build_app.sh`

### 关键配置文件
- **依赖**: `requirements.txt`
- **虚拟环境**: `venv/`
- **自定义规则**: `gui/custom_module_rules.json`
- **AI配置**: `gui/modules/ai_diagnosis/`

### 重要模块
- **数据模型**: `gui/modules/data_models.py`
- **文件操作**: `gui/modules/file_operations.py`
- **AI诊断**: `gui/modules/ai_diagnosis/`
- **iOS混淆**: `gui/modules/obfuscation/`

---

*此文档为项目核心指南，详细说明请参考对应的专门文档。*