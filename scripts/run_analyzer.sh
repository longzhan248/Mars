#!/bin/bash

# 心娱开发助手 (Xinyu DevTools) 启动脚本 - macOS版本

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 获取项目根目录（脚本在scripts子目录中）
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 切换到项目根目录
cd "$PROJECT_ROOT"

echo "========================================="
echo "心娱开发助手 (Xinyu DevTools) - 专业版"
echo "========================================="
echo "项目路径: $PROJECT_ROOT"

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
VENV_DIR="$PROJECT_ROOT/venv"

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

# 确保使用虚拟环境中的python3和pip3（使用完整路径）
PYTHON_CMD="$VENV_DIR/bin/python3"
PIP_CMD="$VENV_DIR/bin/pip3"

# 如果虚拟环境的Python不存在，使用系统Python
if [ ! -f "$PYTHON_CMD" ]; then
    echo "警告: 虚拟环境Python不存在，使用系统Python"
    PYTHON_CMD="python3"
    PIP_CMD="pip3"
fi

# 升级pip到最新版本
"$PIP_CMD" install --upgrade pip 2>/dev/null

# 检查是否有requirements.txt文件
REQUIREMENTS_FILE="$PROJECT_ROOT/requirements.txt"
DEPS_CHECK_FILE="$VENV_DIR/.deps_installed"

# 如果requirements.txt存在且比依赖检查标记文件新，则安装/更新依赖
if [ -f "$REQUIREMENTS_FILE" ]; then
    if [ ! -f "$DEPS_CHECK_FILE" ] || [ "$REQUIREMENTS_FILE" -nt "$DEPS_CHECK_FILE" ]; then
        echo "检查并安装项目依赖..."
        "$PIP_CMD" install -r "$REQUIREMENTS_FILE" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "项目依赖安装成功"
            touch "$DEPS_CHECK_FILE"
        else
            echo "警告: 部分依赖安装失败，某些功能可能不可用"
        fi
    else
        echo "项目依赖已是最新"
    fi
else
    # 旧版兼容：如果没有requirements.txt，手动检查关键依赖
    echo "检查关键依赖..."

    # 检查matplotlib
    "$PYTHON_CMD" -c "import matplotlib" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "正在安装matplotlib..."
        "$PIP_CMD" install matplotlib
    fi

    # 检查iOS推送工具依赖
    PUSH_DEPS_MISSING=0
    "$PYTHON_CMD" -c "import cryptography" 2>/dev/null || PUSH_DEPS_MISSING=1
    "$PYTHON_CMD" -c "import httpx" 2>/dev/null || PUSH_DEPS_MISSING=1
    "$PYTHON_CMD" -c "import jwt" 2>/dev/null || PUSH_DEPS_MISSING=1

    if [ $PUSH_DEPS_MISSING -ne 0 ]; then
        echo "安装iOS推送工具依赖..."
        "$PIP_CMD" install cryptography httpx pyjwt h2 2>/dev/null
    fi
fi

# 启动日志分析系统
echo "========================================="
echo "心娱开发助手 (Xinyu DevTools) - 专业版（模块化版本）"
echo "========================================="
echo "正在启动..."
# 使用模块化版本（已修复filter_logs问题）
"$PYTHON_CMD" "$PROJECT_ROOT/gui/mars_log_analyzer_modular.py"

# 如果程序异常退出，等待用户按键
if [ $? -ne 0 ]; then
    echo ""
    echo "程序异常退出，按Enter键关闭..."
    read
fi