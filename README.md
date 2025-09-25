# Mars xLog Analyzer Tool Suite

用于解码和分析 Mars xlog 文件的完整工具套件

## 快速开始

```bash
# 使用启动脚本（推荐）
./scripts/run_analyzer.sh

# 或直接运行GUI
python3 gui/mars_log_analyzer_pro.py
```

## 项目结构

```
.
├── decoders/           # 解码器核心模块
├── gui/                # GUI应用程序
├── tools/              # 工具脚本
├── scripts/            # 启动和打包脚本
├── docs/               # 文档目录
└── venv/               # Python虚拟环境
```

## 详细文档

- [中文文档](docs/README_CN.md)
- [English Documentation](docs/README_EN.md)
- [开发指南](docs/CLAUDE.md)