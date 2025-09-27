# CLAUDE.md

此文件为 Claude Code (claude.ai/code) 在此代码库中工作时提供指导。

## 项目用途
此代码库包含用于解码和分析 Mars xlog 文件的完整工具套件 - Mars 是腾讯的日志框架，xlog 是其使用的压缩和加密日志文件格式。
项目提供了从基础解码到高级分析的全方位解决方案，包括命令行工具、专业级GUI应用、IPS崩溃分析和iOS推送测试工具。

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

## 最新更新 (2025-09-27)
- **集成iOS推送测试功能** - 完整的APNS推送测试工具已集成到主程序
- **统一的GUI界面** - Mars日志分析、IPS崩溃解析、iOS推送测试三合一
- **智能依赖管理** - 自动检测和安装所有必要的依赖包
- **完全可移植** - 项目可放置在任何路径下运行
- **时间过滤增强** - 支持带时区的时间格式，Enter键快速应用过滤

## 核心组件

### 解码器系列
- `decode_mars_nocrypt_log_file.py` - 原始 Python 2 版本解码脚本
- `decode_mars_nocrypt_log_file_py3.py` - Python 3 兼容版本
  - 支持多种压缩格式（MAGIC_COMPRESS_START、MAGIC_NO_COMPRESS_START 等）
  - 支持加密（4字节或64字节密钥）和非加密日志格式
  - 使用 zlib 进行解压缩
  - 验证日志缓冲区完整性并优雅处理损坏的数据
- `fast_decoder.py` - 高性能解码器
  - 优化的解码算法，提升解析速度
  - 减少内存占用
  - 适合批量处理大文件
- `optimized_decoder.py` - 优化版解码器
  - 改进的错误处理机制
  - 更好的内存管理
  - 支持流式处理

### GUI分析系统
- `mars_log_analyzer_pro.py` - 专业版GUI应用程序（最新版）
  - 高性能文本渲染组件
  - 支持百万级日志条目的流畅浏览
  - 高级搜索和过滤功能（支持正则表达式）
  - 实时统计分析
  - 多标签页界面
  - 导出多种格式（TXT/JSON/CSV）
  - 时间线可视化
  - 日志级别分布图表
  - 支持大文件懒加载
  - **集成iOS推送测试功能**（新增）
  - **IPS崩溃日志解析功能**
  - **增强的时间过滤**
    - 支持多种时间格式（YYYY-MM-DD HH:MM:SS、HH:MM等）
    - 支持带时区的日志格式（如 2025-09-21 +8.0 13:09:49.038）
    - Enter键快速应用过滤
    - 级别和模块选择自动触发过滤

### UI组件
- `scrolled_text_with_lazy_load.py` - 懒加载滚动文本组件
  - 虚拟滚动技术
  - 仅渲染可见区域
  - 支持百万级数据行
- `improved_lazy_text.py` - 改进版懒加载文本组件
  - 优化的滚动性能
  - 智能缓存策略
  - 减少内存占用

### 辅助工具
- `ips_parser.py` - IPS崩溃日志解析器
  - 解析iOS崩溃报告
  - 符号化堆栈跟踪
  - 提取关键崩溃信息
- `run_analyzer.sh` - 启动脚本（自动创建虚拟环境和安装依赖）
- `setup.py` - py2app打包配置（可选，用于创建Mac应用）

### iOS推送测试工具
- `push_tools/` - iOS APNS推送测试模块（**已集成到主程序**）
  - `apns_push.py` - 推送核心逻辑实现
    - 证书管理（支持.p12/.pem/.cer格式）
    - HTTP/2推送发送
    - 推送历史记录
    - 沙盒和生产环境支持
  - `apns_gui.py` - 推送测试GUI界面
    - 友好的图形界面
    - Payload模板快速选择
    - 实时日志和历史记录
    - **可独立运行或嵌入主程序标签页**
  - `test_push.py` - 功能测试脚本
  - `requirements.txt` - 推送工具依赖
- `scripts/run_push_tool.sh` - iOS推送工具独立启动脚本

### 文档
- `README_CN.md` - 中文说明文档
- `README_EN.md` - 英文说明文档

## 使用命令

### 启动GUI分析系统（推荐）：
```bash
# 使用启动脚本（推荐，自动处理依赖和环境）
./scripts/run_analyzer.sh

# 或手动启动（需要先激活虚拟环境）
source venv/bin/activate
python3 gui/mars_log_analyzer_pro.py
```

#### 功能说明
主程序包含三个标签页：
1. **Mars日志分析** - 解码和分析xlog文件
2. **IPS崩溃解析** - 解析iOS崩溃报告
3. **iOS推送测试** - APNS推送测试工具

### 独立启动iOS推送工具：
```bash
# 独立启动推送工具GUI
./scripts/run_push_tool.sh

# 或直接运行
python3 push_tools/apns_gui.py

# 命令行使用
python3 push_tools/apns_push.py --cert cert.p12 --token "device_token" --message "测试消息" --sandbox
```

### 命令行解码：

#### 基础解码
```bash
# Python 3版本解码单个文件
python3 decoders/decode_mars_nocrypt_log_file_py3.py mizhua_20250915.xlog

# 批量解码当前目录所有xlog文件
python3 decoders/decode_mars_nocrypt_log_file_py3.py

# 解码指定目录
python3 decoders/decode_mars_nocrypt_log_file_py3.py /path/to/xlog/directory/
```

#### 高性能解码
```bash
# 使用快速解码器（大文件推荐）
python3 decoders/fast_decoder.py input.xlog

# 使用优化解码器（内存优化）
python3 decoders/optimized_decoder.py input.xlog
```

### IPS崩溃日志分析：
```bash
# 解析iOS崩溃报告
python3 tools/ips_parser.py crash.ips
```

## 重要说明

### 系统要求
- Python 3.6+ （推荐3.8+）
- GUI系统需要 tkinter 和 matplotlib 库
- 原始脚本支持 Python 2，但推荐使用 Python 3 版本

### 性能建议
- 小文件（<10MB）：使用基础解码器即可
- 大文件（>10MB）：推荐使用 `fast_decoder.py` 或 `optimized_decoder.py`
- 批量处理：使用 `mars_log_analyzer_pro.py` GUI工具
- 内存限制环境：使用 `optimized_decoder.py` 的流式处理

### 技术特性
- 自动检测并处理各种 Mars 日志格式版本
- 验证序列号以检测丢失的日志条目
- 支持压缩和加密日志的解码
- GUI系统采用懒加载技术，可处理GB级日志文件
- 所有解码器都具有完善的错误处理机制

## 日志格式详情

### Mars xlog 格式规范
- 魔数字节表示压缩和加密状态：
  - 0x03, 0x04, 0x05：4字节密钥格式
  - 0x06, 0x07, 0x08, 0x09：64字节密钥格式
- 头部结构：magic_start (1字节) + seq (2字节) + begin_hour (1字节) + end_hour (1字节) + length (4字节) + crypt_key
- 每个日志条目以 MAGIC_END (0x00) 结尾

### 支持的日志级别
- ERROR: 错误日志
- WARNING: 警告日志
- INFO: 信息日志
- DEBUG: 调试日志
- VERBOSE: 详细日志

## 环境管理

### 项目可移植性
项目设计为完全可移植，可以放置在任何路径下运行：
- **无硬编码路径** - 所有路径都是相对于项目根目录
- **自动环境管理** - 启动脚本自动处理虚拟环境
- **智能依赖检测** - 自动检查并安装缺失的依赖

### 虚拟环境
项目使用Python虚拟环境隔离依赖：
```bash
# 自动方式（推荐）
./scripts/run_analyzer.sh  # 自动创建venv并安装依赖

# 手动方式
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 依赖管理
所有项目依赖都在`requirements.txt`中定义：
- **matplotlib** - 图表绘制
- **cryptography** - 证书处理
- **httpx** - HTTP/2客户端
- **pyjwt** - JWT处理
- **h2** - HTTP/2协议

### 常见问题

#### Q: 提示"No module named 'cryptography'"？
**解决方案**：
1. 确保在项目根目录（包含venv文件夹的目录）
2. 激活虚拟环境：`source venv/bin/activate`
3. 重新安装依赖：`pip install -r requirements.txt`

#### Q: 虚拟环境路径混乱？
**解决方案**：
```bash
# 删除旧的虚拟环境
rm -rf venv

# 重新创建
python3 -m venv venv

# 安装依赖
source venv/bin/activate
pip install -r requirements.txt
```

#### Q: iOS推送功能无法加载？
**解决方案**：
使用`./scripts/run_analyzer.sh`启动，它会自动处理所有依赖。

## 开发指南

### 项目结构
```
.
├── decoders/                                 # 解码器核心模块
│   ├── decode_mars_nocrypt_log_file_py3.py  # 基础解码器
│   ├── decode_mars_nocrypt_log_file.py      # Python 2版解码器
│   ├── fast_decoder.py                       # 高性能解码器
│   └── optimized_decoder.py                  # 优化解码器
├── gui/                                      # GUI应用程序
│   ├── mars_log_analyzer_pro.py              # 专业版GUI主程序（集成所有功能）
│   └── components/                           # GUI组件
│       ├── scrolled_text_with_lazy_load.py   # 懒加载滚动文本组件
│       └── improved_lazy_text.py             # 改进版懒加载文本组件
├── push_tools/                               # iOS推送测试工具（新增）
│   ├── __init__.py                           # 模块初始化
│   ├── apns_push.py                          # 推送核心逻辑
│   ├── apns_gui.py                           # 推送GUI界面
│   ├── test_push.py                          # 功能测试脚本
│   ├── requirements.txt                      # 推送工具依赖
│   └── README.md                             # 推送工具文档
├── tools/                                    # 工具脚本
│   └── ips_parser.py                         # IPS崩溃日志解析器
├── scripts/                                  # 启动和打包脚本
│   ├── run_analyzer.sh                       # 主程序启动脚本
│   ├── run_push_tool.sh                      # 推送工具启动脚本
│   └── setup.py                              # py2app打包配置
├── docs/                                     # 文档目录
│   ├── README_CN.md                          # 中文文档
│   ├── README_EN.md                          # 英文文档
│   └── CLAUDE.md                              # 项目指南（本文件）
└── venv/                                     # Python虚拟环境（自动生成）
```

### 贡献指南
1. 保持代码风格一致性
2. 添加适当的错误处理
3. 新功能需要更新相应文档
4. 性能优化需要提供基准测试结果

## 功能使用说明

### 时间过滤功能
GUI提供强大的时间过滤功能，支持多种时间格式输入：

#### 支持的时间格式
- **完整格式**: `2025-09-21 14:00:00` - 精确到秒
- **日期格式**: `2025-09-21` - 过滤整天的日志
- **时间格式**: `14:00:00` 或 `14:00` - 跨天过滤特定时间段
- **留空**: 开始时间留空表示从最早，结束时间留空表示到最后

#### 使用方法
1. 在时间范围输入框中输入开始和结束时间
2. 按Enter键或点击"应用过滤"按钮
3. 切换日志级别或模块会自动应用所有过滤条件

#### 支持的日志时间戳格式
- 带时区：`[2025-09-21 +8.0 13:09:49.038]`
- 无时区：`[2025-09-21 13:09:49.038]`
- 标准格式：`2025-09-21 13:09:49`

### 搜索功能
- **普通搜索**: 输入关键词进行字符串匹配
- **正则搜索**: 切换到"正则"模式使用正则表达式
- **快捷键**: 在搜索框按Enter键立即搜索
- **高亮显示**: 搜索结果自动高亮显示

## 常见问题

### Q: 解码后的文件在哪里？
A: 默认保存在原xlog文件同目录，文件名添加.log后缀

### Q: 如何处理加密的日志？
A: 当前工具主要处理非加密或标准加密格式，特殊加密需要提供密钥

### Q: GUI程序打不开怎么办？
A: 使用 run_analyzer.sh 脚本，它会自动安装所需依赖

### Q: 支持哪些操作系统？
A: macOS、Linux、Windows（需要Python环境）

### Q: iOS推送功能如何使用？
A: 有两种方式：
1. 在主程序中点击"iOS推送测试"标签页
2. 独立运行`./scripts/run_push_tool.sh`

### Q: 推送证书如何获取？
A: 从Apple开发者中心下载，导出为.p12格式（包含私钥）

## 集成架构说明

### 模块化设计
项目采用模块化设计，各功能模块可独立运行或集成使用：

```
mars_log_analyzer_pro.py (主程序)
    ├── Mars日志分析模块
    │   ├── 解码器 (decoders/)
    │   └── 日志分析引擎
    ├── IPS崩溃解析模块
    │   └── ips_parser.py
    └── iOS推送测试模块
        ├── apns_push.py (核心)
        └── apns_gui.py (界面)
```

### 集成优势
1. **统一界面** - 所有iOS开发工具在一个窗口
2. **共享环境** - 统一的虚拟环境和依赖管理
3. **灵活使用** - 既可集成使用，也可独立运行
4. **易于维护** - 模块分离，便于单独更新

### 扩展开发
如需添加新功能模块：
1. 在独立目录创建模块（如`new_tool/`）
2. 在主程序中添加新标签页
3. 使用延迟导入避免启动依赖
4. 更新requirements.txt添加新依赖