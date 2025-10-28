#!/bin/bash
#
# 查找Claude Code命令路径
# 用于帮助用户配置打包后的app
#

echo "==========================================="
echo "查找Claude Code命令路径"
echo "==========================================="
echo ""

# 方法1: 通过which查找
echo "方法1: 使用which命令查找..."
CLAUDE_PATH=$(which claude 2>/dev/null)
if [ -n "$CLAUDE_PATH" ]; then
    echo "✓ 找到: $CLAUDE_PATH"

    # 验证是否可执行
    if [ -x "$CLAUDE_PATH" ]; then
        echo "✓ 可执行"

        # 测试版本
        VERSION=$($CLAUDE_PATH --version 2>&1)
        echo "  版本: $VERSION"
    fi
else
    echo "✗ 未找到"
fi

echo ""

# 方法2: 检查常见路径
echo "方法2: 检查常见安装位置..."
COMMON_PATHS=(
    "$HOME/.local/bin/claude"
    "$HOME/.npm/bin/claude"
    "$HOME/.nvm/versions/node/v20.18.1/bin/claude"
    "$HOME/.nvm/versions/node/v20.18.0/bin/claude"
    "/usr/local/bin/claude"
    "/opt/homebrew/bin/claude"
)

for path in "${COMMON_PATHS[@]}"; do
    if [ -f "$path" ]; then
        echo "✓ 找到: $path"
    fi
done

echo ""

# 方法3: 搜索所有nvm版本
echo "方法3: 搜索nvm安装的所有Node版本..."
if [ -d "$HOME/.nvm/versions/node" ]; then
    find "$HOME/.nvm/versions/node" -name "claude" -type f 2>/dev/null | while read -r path; do
        echo "✓ 找到: $path"
    done
else
    echo "  未安装nvm或nvm路径不存在"
fi

echo ""
echo "==========================================="
echo "配置说明:"
echo "==========================================="
echo "1. 将上面找到的claude路径复制"
echo "2. 打开应用的设置对话框"
echo "3. 在'Claude命令路径'输入框中粘贴路径"
echo "4. 点击'测试连接'验证"
echo "5. 保存设置"
echo ""
