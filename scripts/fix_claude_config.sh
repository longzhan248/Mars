#!/bin/bash
#
# 自动修复Claude Code配置
# 解决"无法连接到Claude Code"的问题
#

echo "==========================================="
echo "自动修复Claude Code配置"
echo "==========================================="
echo ""

# 查找claude路径
echo "1. 查找claude命令..."
CLAUDE_PATH=$(which claude 2>/dev/null)

if [ -z "$CLAUDE_PATH" ]; then
    echo "  ✗ 未找到claude命令"
    echo ""
    echo "请先安装Claude Code:"
    echo "  npm install -g @anthropic-ai/claude-code"
    exit 1
fi

echo "  ✓ 找到: $CLAUDE_PATH"

# 验证是否可执行
if [ ! -x "$CLAUDE_PATH" ]; then
    echo "  ✗ 文件不可执行"
    exit 1
fi

# 测试版本
VERSION=$($CLAUDE_PATH --version 2>&1)
echo "  版本: $VERSION"
echo ""

# 更新配置
echo "2. 更新配置文件..."

python3 << EOF
import json
import os

config_file = 'gui/ai_config.json'

# 读取或创建配置
if os.path.exists(config_file):
    with open(config_file, 'r') as f:
        config = json.load(f)
    print('  ✓ 读取现有配置')
else:
    config = {
        "ai_service": "ClaudeCode",
        "auto_detect": False,
        "auto_summary": False,
        "privacy_filter": True,
        "max_tokens": 10000,
        "timeout": 60,
        "context_size": "标准",
        "show_ai_panel": True,
        "ai_panel_width": 350,
        "show_token_usage": True,
        "project_dirs": []
    }
    print('  ✓ 创建新配置')

# 更新claude_path
config['claude_path'] = '$CLAUDE_PATH'
config['ai_service'] = 'ClaudeCode'

# 保存
with open(config_file, 'w') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print('  ✓ 配置已保存')
print(f'  claude_path: {config["claude_path"]}')
EOF

echo ""

# 验证配置
echo "3. 验证配置..."
if grep -q "claude_path" gui/ai_config.json 2>/dev/null; then
    echo "  ✓ claude_path字段已添加"
else
    echo "  ✗ 配置更新失败"
    exit 1
fi

echo ""

# 测试连接
echo "4. 测试连接..."
python3 << 'EOF'
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

try:
    from gui.modules.ai_diagnosis.config import AIConfig
    from gui.modules.ai_diagnosis.ai_client import AIClientFactory

    config = AIConfig.load()
    claude_path = config.get('claude_path', '')

    client = AIClientFactory.create(service='ClaudeCode', claude_path=claude_path)
    response = client.ask("测试连接,请简单回复OK")

    print('  ✓ 连接成功!')
    print(f'  响应: {response[:50]}...')

except Exception as e:
    print(f'  ✗ 连接失败: {e}')
    import traceback
    traceback.print_exc()
    exit(1)
EOF

echo ""
echo "==========================================="
echo "✓ 修复完成!"
echo "==========================================="
echo ""
echo "现在可以启动应用了:"
echo "  ./scripts/run_analyzer.sh"
echo ""
