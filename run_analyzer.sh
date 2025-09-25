#!/bin/bash

# Mars日志分析系统启动脚本

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 切换到脚本目录
cd "$SCRIPT_DIR"

# 检查Python 3是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: Python 3未安装"
    echo "请先安装Python 3"
    echo "macOS: brew install python3"
    echo "Ubuntu/Debian: sudo apt-get install python3 python3-pip python3-venv"
    echo "CentOS/RHEL: sudo yum install python3"
    exit 1
fi

# 获取Python3版本
PYTHON3_VERSION=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
if [ -z "$PYTHON3_VERSION" ]; then
    PYTHON3_VERSION=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
fi
echo "检测到Python版本: $PYTHON3_VERSION"

# 检查Python版本是否满足要求(至少3.6)
# 使用Python自己来比较版本
python3 -c "import sys; exit(0 if sys.version_info >= (3, 6) else 1)" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "错误: Python版本过低，需要Python 3.6或更高版本"
    exit 1
fi

# 检查虚拟环境是否存在
VENV_DIR="$SCRIPT_DIR/venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "创建虚拟环境..."
    python3 -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo "错误: 无法创建虚拟环境"
        echo "请确保安装了python3-venv包"
        echo "Ubuntu/Debian: sudo apt-get install python3-venv"
        exit 1
    fi
fi

# 激活虚拟环境
source "$VENV_DIR/bin/activate"

# 确保使用虚拟环境中的python3和pip3
PYTHON_CMD="$VENV_DIR/bin/python3"
PIP_CMD="$VENV_DIR/bin/pip3"

# 升级pip到最新版本
"$PIP_CMD" install --upgrade pip 2>/dev/null

# 检查matplotlib是否安装
"$PYTHON_CMD" -c "import matplotlib" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "正在安装matplotlib..."
    "$PIP_CMD" install matplotlib
    if [ $? -ne 0 ]; then
        echo "错误: matplotlib安装失败"
        echo "请尝试手动安装: pip3 install matplotlib"
        exit 1
    fi
fi

# 启动日志分析系统
echo "========================================="
echo "Mars日志分析系统 - 专业版"
echo "========================================="
echo "正在启动..."
"$PYTHON_CMD" mars_log_analyzer_pro.py

# 如果程序异常退出，等待用户按键
if [ $? -ne 0 ]; then
    echo ""
    echo "程序异常退出，按Enter键关闭..."
    read
fi