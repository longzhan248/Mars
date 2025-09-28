#!/bin/bash
# Mars Log Analyzer - PyInstaller打包脚本
# 用于创建独立的Mac应用程序

set -e  # 遇到错误立即退出

echo "================================================"
echo "  Mars Log Analyzer - PyInstaller打包工具"
echo "================================================"
echo ""

# 获取脚本所在目录的父目录（项目根目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo "📁 项目根目录: $PROJECT_ROOT"
echo ""

# 检查虚拟环境
VENV_DIR="$PROJECT_ROOT/venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "❌ 错误: 未找到虚拟环境目录: $VENV_DIR"
    echo "请先运行 ./scripts/run_analyzer.sh 创建虚拟环境"
    exit 1
fi

echo "✅ 找到虚拟环境"

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source "$VENV_DIR/bin/activate"

# 检查PyInstaller
if ! command -v pyinstaller &> /dev/null; then
    echo "📦 安装PyInstaller..."
    pip install pyinstaller
else
    echo "✅ PyInstaller已安装"
fi

# 清理旧的构建文件
echo ""
echo "🧹 清理旧的构建文件..."
rm -rf build dist
echo "✅ 清理完成"

# 开始打包
echo ""
echo "🚀 开始打包应用程序..."
echo "这可能需要几分钟时间，请耐心等待..."
echo ""

pyinstaller --clean MarsLogAnalyzer.spec

# 检查打包结果
APP_PATH="$PROJECT_ROOT/dist/MarsLogAnalyzer.app"
if [ -d "$APP_PATH" ]; then
    echo ""
    echo "================================================"
    echo "  ✅ 打包成功！"
    echo "================================================"
    echo ""
    echo "应用程序位置: $APP_PATH"
    echo ""

    # 获取应用大小
    APP_SIZE=$(du -sh "$APP_PATH" | cut -f1)
    echo "📦 应用大小: $APP_SIZE"
    echo ""

    echo "📝 使用说明:"
    echo "1. 将应用拖到 /Applications 文件夹"
    echo "2. 双击打开即可使用"
    echo "3. 首次打开可能需要在系统偏好设置中允许运行"
    echo ""

    # 提示如何处理安全警告
    echo "💡 如果遇到 \"无法打开，因为无法验证开发者\" 错误:"
    echo "   在终端运行: xattr -cr \"$APP_PATH\""
    echo "   或者: 右键点击应用 -> 选择\"打开\" -> 点击\"打开\"按钮"
    echo ""

    # 询问是否打开应用所在文件夹
    read -p "是否在Finder中显示应用? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        open "$PROJECT_ROOT/dist"
    fi

else
    echo ""
    echo "================================================"
    echo "  ❌ 打包失败"
    echo "================================================"
    echo ""
    echo "请查看上方的错误信息"
    exit 1
fi

echo ""
echo "🎉 完成！"