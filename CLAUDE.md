# CLAUDE.md

此文件为 Claude Code (claude.ai/code) 在此代码库中工作时提供指导。

## 项目用途
此代码库包含用于解码 Mars xlog 文件的工具 - Mars 是腾讯的日志框架，xlog 是其使用的压缩和加密日志文件格式。
现已包含完整的GUI日志分析系统，支持批量解析、统计分析和可视化。

## 核心组件

### 解码脚本
- `decode_mars_nocrypt_log_file.py` - 原始 Python 2 版本解码脚本
- `decode_mars_nocrypt_log_file_py3.py` - Python 3 兼容版本
  - 支持多种压缩格式（MAGIC_COMPRESS_START、MAGIC_NO_COMPRESS_START 等）
  - 支持加密（4字节或64字节密钥）和非加密日志格式
  - 使用 zlib 进行解压缩
  - 验证日志缓冲区完整性并优雅处理损坏的数据

### GUI分析系统
- `mars_log_analyzer.py` - 主GUI应用程序
  - 基于tkinter的图形界面
  - 支持批量解析多个xlog文件
  - 日志级别统计（ERROR、WARNING、INFO、DEBUG）
  - 时间分布分析和可视化
  - 关键词搜索和过滤功能
  - 导出TXT/JSON格式报告

### 辅助文件
- `run_analyzer.sh` - 启动脚本（自动创建虚拟环境和安装依赖）
- `setup.py` - py2app打包配置（可选，用于创建Mac应用）

## 使用命令

### 启动GUI分析系统（推荐）：
```bash
# 使用启动脚本（自动处理依赖）
./run_analyzer.sh

# 或直接运行（需手动安装matplotlib）
python3 mars_log_analyzer.py
```

### 命令行解码单个 xlog 文件：
```bash
# Python 3版本
python3 decode_mars_nocrypt_log_file_py3.py mizhua_20250915.xlog

# Python 2版本（如果需要）
python2 decode_mars_nocrypt_log_file.py mizhua_20250915.xlog
```

### 命令行批量解码：
```bash
# 解码当前目录下所有xlog文件
python3 decode_mars_nocrypt_log_file_py3.py

# 解码指定目录
python3 decode_mars_nocrypt_log_file_py3.py /path/to/xlog/directory/
```

## 重要说明
- GUI系统需要 Python 3.6+和matplotlib库
- 原始脚本需要 Python 2，已提供Python 3兼容版本
- 脚本会验证序列号以检测丢失的日志条目
- 支持不同魔数字节的各种 Mars 日志格式版本
- 对于真正加密（而非仅压缩）的日志，需要使用不同的解码器
- GUI系统会在首次运行时自动创建虚拟环境并安装依赖

## 日志格式详情
- 魔数字节表示压缩和加密状态：
  - 0x03, 0x04, 0x05：4字节密钥格式
  - 0x06, 0x07, 0x08, 0x09：64字节密钥格式
- 头部结构：magic_start (1字节) + seq (2字节) + begin_hour (1字节) + end_hour (1字节) + length (4字节) + crypt_key
- 每个日志条目以 MAGIC_END (0x00) 结尾