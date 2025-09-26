# CLAUDE.md - 脚本目录技术指南

## 模块概述
自动化脚本和构建配置集合，包括启动脚本、打包配置等。提供一键式部署和分发解决方案。

## 核心脚本

### run_analyzer.sh
智能启动脚本，自动处理环境配置和依赖安装。

#### 脚本架构
```bash
#!/bin/bash
1. 环境检测
2. Python版本验证
3. 虚拟环境管理
4. 依赖安装
5. 应用启动
6. 错误处理
```

#### 关键功能

##### 1. 路径管理
```bash
# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 获取项目根目录（重要：整理后的新路径）
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 切换到项目根目录
cd "$PROJECT_ROOT"
```

##### 2. Python环境检测
```bash
# 检查Python 3
if ! command -v python3 &> /dev/null; then
    echo "错误: Python 3未安装"
    # 提供安装指导
    exit 1
fi

# 版本检查（至少3.6）
python3 -c "import sys; exit(0 if sys.version_info >= (3, 6) else 1)"
```

##### 3. 虚拟环境管理
```bash
# 虚拟环境路径（项目根目录下）
VENV_DIR="$PROJECT_ROOT/venv"

# 创建虚拟环境
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi

# 激活虚拟环境
source "$VENV_DIR/bin/activate"

# 使用虚拟环境的Python
PYTHON_CMD="$VENV_DIR/bin/python3"
PIP_CMD="$VENV_DIR/bin/pip3"
```

##### 4. 依赖管理
```bash
# 升级pip
"$PIP_CMD" install --upgrade pip 2>/dev/null

# 检查并安装依赖
"$PYTHON_CMD" -c "import matplotlib" 2>/dev/null
if [ $? -ne 0 ]; then
    "$PIP_CMD" install matplotlib
fi
```

##### 5. 应用启动
```bash
# 启动GUI程序（注意新路径）
"$PYTHON_CMD" "$PROJECT_ROOT/gui/mars_log_analyzer_pro.py"

# 错误处理
if [ $? -ne 0 ]; then
    echo "程序异常退出，按Enter键关闭..."
    read
fi
```

#### 跨平台兼容性

##### macOS
```bash
# Homebrew安装Python
brew install python3

# 字体支持
# 自动使用 Arial Unicode MS
```

##### Linux
```bash
# Ubuntu/Debian
sudo apt-get install python3 python3-pip python3-venv python3-tk

# CentOS/RHEL
sudo yum install python3 python3-tkinter
```

##### Windows (Git Bash/WSL)
```bash
# 需要Python Windows安装包
# tkinter通常已包含
```

#### 故障排除

##### 常见错误
1. **Python未找到**
   - 解决：安装Python 3.6+

2. **venv模块缺失**
   - 解决：`apt-get install python3-venv`

3. **tkinter缺失**
   - 解决：`apt-get install python3-tk`

4. **权限错误**
   - 解决：`chmod +x run_analyzer.sh`

### setup.py
py2app打包配置，用于创建macOS独立应用。

#### 配置结构
```python
from setuptools import setup

APP = ['gui/mars_log_analyzer_pro.py']  # 注意新路径
DATA_FILES = [
    ('decoders', ['decoders/*.py']),
    ('tools', ['tools/*.py']),
    ('components', ['gui/components/*.py'])
]

OPTIONS = {
    'argv_emulation': True,
    'packages': ['matplotlib', 'tkinter'],
    'iconfile': 'icon.icns',  # 应用图标
    'plist': {
        'CFBundleName': 'Mars Log Analyzer',
        'CFBundleDisplayName': 'Mars Log Analyzer Pro',
        'CFBundleVersion': '1.0.0',
        'CFBundleIdentifier': 'com.marslog.analyzer',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.14.0'
    }
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
```

#### 打包流程

##### 1. 准备环境
```bash
# 安装py2app
pip install py2app

# 清理旧构建
rm -rf build dist
```

##### 2. 构建应用
```bash
# 开发模式（快速测试）
python setup.py py2app -A

# 发布模式（独立应用）
python setup.py py2app

# 结果在 dist/Mars Log Analyzer.app
```

##### 3. 代码签名
```bash
# 签名应用
codesign --force --deep --sign "Developer ID" "dist/Mars Log Analyzer.app"

# 验证签名
codesign --verify --verbose "dist/Mars Log Analyzer.app"
```

##### 4. 公证（Notarization）
```bash
# 创建DMG
hdiutil create -volname "Mars Log Analyzer" -srcfolder dist -ov -format UDZO MarsLogAnalyzer.dmg

# 提交公证
xcrun altool --notarize-app --file MarsLogAnalyzer.dmg --primary-bundle-id com.marslog.analyzer

# 装订票据
xcrun stapler staple MarsLogAnalyzer.dmg
```

#### 打包优化

##### 减小体积
```python
OPTIONS = {
    'excludes': ['test', 'unittest', 'email', 'http'],
    'optimize': 2,  # 优化字节码
    'compressed': True,  # 压缩
    'strip': True,  # 去除符号
}
```

##### 包含资源
```python
DATA_FILES = [
    ('resources', ['resources/*']),
    ('docs', ['docs/*.md']),
    ('examples', ['examples/*.xlog'])
]
```

##### 处理依赖
```python
# 显式包含隐式依赖
OPTIONS = {
    'includes': ['queue', 'threading', 'subprocess'],
    'packages': ['matplotlib.backends.backend_tkagg']
}
```

## 自动化脚本开发

### 测试脚本
创建 `test_runner.sh`:
```bash
#!/bin/bash
# 自动化测试脚本

# 运行单元测试
python -m pytest tests/ -v

# 性能测试
python tests/benchmark.py

# 集成测试
python tests/integration_test.py
```

### 部署脚本
创建 `deploy.sh`:
```bash
#!/bin/bash
# 自动化部署脚本

VERSION=$1
if [ -z "$VERSION" ]; then
    echo "Usage: ./deploy.sh <version>"
    exit 1
fi

# 更新版本号
sed -i "" "s/CFBundleVersion.*$/CFBundleVersion': '$VERSION',/" setup.py

# 构建
python setup.py py2app

# 创建DMG
./create_dmg.sh

# 上传到服务器
scp MarsLogAnalyzer-$VERSION.dmg server:/releases/
```

### CI/CD集成
创建 `.github/workflows/build.yml`:
```yaml
name: Build and Test

on: [push, pull_request]

jobs:
  build:
    runs-on: macos-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install py2app
    - name: Run tests
      run: pytest tests/
    - name: Build app
      run: python setup.py py2app
    - name: Upload artifact
      uses: actions/upload-artifact@v2
      with:
        name: MarsLogAnalyzer
        path: dist/*.app
```

## 环境配置

### requirements.txt
```txt
matplotlib>=3.5.0
# tkinter (系统自带)
# 开发依赖
pytest>=7.0.0
pytest-cov>=3.0.0
black>=22.0.0
pylint>=2.12.0
# 打包依赖
py2app>=0.28.0
```

### .env配置
创建 `.env` 文件：
```bash
# 开发环境配置
DEBUG=1
LOG_LEVEL=DEBUG
MAX_MEMORY=2048

# 生产环境配置
# DEBUG=0
# LOG_LEVEL=INFO
# MAX_MEMORY=4096
```

### 配置加载
```python
# config.py
import os
from dotenv import load_dotenv

load_dotenv()

DEBUG = os.getenv('DEBUG', '0') == '1'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
MAX_MEMORY = int(os.getenv('MAX_MEMORY', '2048'))
```

## Shell脚本最佳实践

### 错误处理
```bash
set -euo pipefail  # 严格模式
trap 'echo "Error on line $LINENO"' ERR
```

### 日志记录
```bash
LOG_FILE="$PROJECT_ROOT/logs/startup.log"
exec 1> >(tee -a "$LOG_FILE")
exec 2>&1
```

### 参数处理
```bash
while getopts "hdv" opt; do
    case $opt in
        h) show_help; exit 0 ;;
        d) DEBUG=1 ;;
        v) VERBOSE=1 ;;
        ?) echo "Invalid option"; exit 1 ;;
    esac
done
```

### 函数封装
```bash
function check_dependency() {
    local cmd=$1
    if ! command -v "$cmd" &> /dev/null; then
        echo "Missing dependency: $cmd"
        return 1
    fi
    return 0
}
```

## 故障排除

### 启动脚本问题

#### Q: 权限拒绝？
```bash
chmod +x scripts/run_analyzer.sh
```

#### Q: 找不到Python？
```bash
# 检查Python路径
which python3

# 创建软链接
ln -s /usr/local/bin/python3 /usr/bin/python3
```

#### Q: 虚拟环境创建失败？
```bash
# 手动创建
python3 -m venv venv

# 或使用virtualenv
pip install virtualenv
virtualenv venv
```

### 打包问题

#### Q: py2app失败？
1. 清理缓存：`rm -rf build dist`
2. 更新py2app：`pip install --upgrade py2app`
3. 检查依赖：`pip list`

#### Q: 应用无法启动？
1. 查看控制台日志
2. 检查权限：`ls -la dist/*.app`
3. 验证签名：`codesign -dv dist/*.app`

## 性能优化

### 启动优化
```bash
# 预编译Python文件
python -m compileall gui/ decoders/ tools/

# 缓存依赖检查结果
DEPS_CHECKED_FILE="$VENV_DIR/.deps_checked"
if [ ! -f "$DEPS_CHECKED_FILE" ]; then
    check_and_install_deps
    touch "$DEPS_CHECKED_FILE"
fi
```

### 内存优化
```bash
# 限制内存使用
ulimit -v 2097152  # 2GB限制

# 监控内存
while true; do
    ps aux | grep python | grep -v grep
    sleep 5
done
```

## 未来规划

### 短期改进
- [ ] Windows批处理脚本
- [ ] Docker容器支持
- [ ] 自动更新机制
- [ ] 崩溃报告收集

### 中期目标
- [ ] Electron打包
- [ ] Linux AppImage
- [ ] Windows MSI安装包
- [ ] 自动化测试套件

### 长期目标
- [ ] 持续集成完善
- [ ] 自动发布流程
- [ ] 多平台统一构建
- [ ] 插件系统支持

## 维护指南

### 版本更新
1. 更新setup.py中的版本号
2. 更新CHANGELOG.md
3. 创建Git标签
4. 运行构建脚本
5. 测试新版本
6. 发布到GitHub Releases

### 依赖更新
```bash
# 检查过时依赖
pip list --outdated

# 更新依赖
pip install --upgrade -r requirements.txt

# 冻结版本
pip freeze > requirements.lock
```

### 安全检查
```bash
# 检查安全漏洞
pip install safety
safety check

# 代码审计
pip install bandit
bandit -r . -f json
```