#!/bin/bash

# iOS推送工具启动脚本

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
PUSH_TOOL_DIR="$PROJECT_ROOT/push_tools"

echo "========================================="
echo "        iOS推送测试工具"
echo "========================================="

# 检查Python版本
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
required_version="3.6"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python版本太低，需要3.6+，当前版本: $python_version"
    exit 1
fi

# 激活虚拟环境（如果存在）
if [ -d "$PROJECT_ROOT/venv" ]; then
    echo "激活虚拟环境..."
    source "$PROJECT_ROOT/venv/bin/activate"
else
    echo "创建虚拟环境..."
    python3 -m venv "$PROJECT_ROOT/venv"
    source "$PROJECT_ROOT/venv/bin/activate"
fi

# 安装依赖
echo "检查依赖..."
pip install -q --upgrade pip

# 安装推送工具依赖
if [ -f "$PUSH_TOOL_DIR/requirements.txt" ]; then
    pip install -q -r "$PUSH_TOOL_DIR/requirements.txt"
fi

# 启动推送工具GUI
echo "启动iOS推送工具..."
cd "$PROJECT_ROOT"
python3 "$PUSH_TOOL_DIR/apns_gui.py"