# CLAUDE.md - 脚本目录

## 模块概述
自动化脚本和构建配置集合，提供一键式部署和分发解决方案。包括智能启动脚本、打包配置、CI/CD集成等。

## 核心脚本

### run_analyzer.sh - 智能启动脚本
自动处理环境配置和依赖安装的一键启动脚本。

#### 核心功能
- **环境检测**: Python 3.6+版本验证
- **虚拟环境**: 自动创建和管理Python虚拟环境
- **依赖安装**: 智能检测并安装缺失的依赖包
- **跨平台支持**: macOS/Linux/Windows兼容
- **错误处理**: 完善的错误提示和恢复机制

#### 使用方法
```bash
# 一键启动（推荐）
./scripts/run_analyzer.sh
```

#### 脚本流程
```bash
1. 路径检测 → 切换到项目根目录
2. Python验证 → 检查Python 3.6+是否安装
3. 虚拟环境 → 创建/激活 venv
4. 依赖安装 → 检查并安装matplotlib等依赖
5. 启动应用 → 运行 mars_log_analyzer_modular.py
6. 错误处理 → 异常退出时提供调试信息
```

#### 跨平台支持
- **macOS**: Homebrew安装Python，字体自动配置
- **Linux**: apt/yum安装python3-tk等依赖
- **Windows**: Git Bash/WSL环境支持

### setup.py - py2app打包配置
用于创建macOS独立应用的打包配置文件。

#### 配置结构
```python
APP = ['gui/mars_log_analyzer_modular.py']
DATA_FILES = [
    ('decoders', ['decoders/*.py']),
    ('tools', ['tools/*.py']),
    ('gui/components', ['gui/components/*.py'])
]

OPTIONS = {
    'packages': ['matplotlib', 'tkinter'],
    'iconfile': 'icon.icns',
    'plist': {
        'CFBundleName': 'Mars Log Analyzer',
        'CFBundleVersion': '1.0.0',
        'NSHighResolutionCapable': True
    }
}
```

#### 打包流程
```bash
# 1. 安装打包工具
pip install py2app

# 2. 清理旧构建
rm -rf build dist

# 3. 构建应用
python setup.py py2app

# 4. 结果: dist/Mars Log Analyzer.app
```

#### 代码签名和公证
```bash
# 签名应用
codesign --force --deep --sign "Developer ID" "dist/Mars Log Analyzer.app"

# 创建DMG
hdiutil create -volname "Mars Log Analyzer" -srcfolder dist -ov -format UDZO MarsLogAnalyzer.dmg

# 公证（App Store分发）
xcrun altool --notarize-app --file MarsLogAnalyzer.dmg --primary-bundle-id com.marslog.analyzer
```

## 自动化脚本

### 测试脚本
```bash
#!/bin/bash
# test_runner.sh - 自动化测试

python -m pytest tests/ -v
python tests/benchmark.py
python tests/integration_test.py
```

### 部署脚本
```bash
#!/bin/bash
# deploy.sh - 自动化部署

VERSION=$1
# 更新版本号
sed -i "" "s/CFBundleVersion.*$/CFBundleVersion': '$VERSION',/" setup.py
# 构建
python setup.py py2app
# 创建DMG
./create_dmg.sh
# 上传
scp MarsLogAnalyzer-$VERSION.dmg server:/releases/
```

### CI/CD集成
```yaml
# .github/workflows/build.yml
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
```

## 环境配置

### requirements.txt
```txt
# 核心依赖
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
```bash
# 开发环境
DEBUG=1
LOG_LEVEL=DEBUG
MAX_MEMORY=2048

# 生产环境
# DEBUG=0
# LOG_LEVEL=INFO
```

## Shell脚本最佳实践

### 错误处理
```bash
set -euo pipefail  # 严格模式
trap 'echo "Error on line $LINENO"' ERR
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

## 故障排除

### 常见问题

**Q: 权限拒绝？**
```bash
chmod +x scripts/run_analyzer.sh
```

**Q: 找不到Python？**
```bash
# 检查路径
which python3

# 创建软链接（如需）
ln -s /usr/local/bin/python3 /usr/bin/python3
```

**Q: 虚拟环境创建失败？**
```bash
# 安装venv模块
apt-get install python3-venv  # Ubuntu
# 或
pip install virtualenv
virtualenv venv
```

**Q: tkinter缺失？**
```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# CentOS/RHEL
sudo yum install python3-tkinter
```

**Q: py2app打包失败？**
1. 清理缓存：`rm -rf build dist`
2. 更新py2app：`pip install --upgrade py2app`
3. 检查依赖：`pip list`

## 性能优化

### 启动优化
- **预编译**: `python -m compileall gui/ decoders/ tools/`
- **依赖缓存**: 记录已检查的依赖，避免重复检查
- **内存限制**: `ulimit -v 2097152` (2GB限制)

### 打包优化
```python
OPTIONS = {
    'excludes': ['test', 'unittest', 'email'],
    'optimize': 2,      # 字节码优化
    'compressed': True,  # 压缩
    'strip': True       # 去除符号
}
```

## 未来规划

### 短期目标
- Windows批处理脚本支持
- Docker容器化部署
- 自动更新机制
- 崩溃报告收集

### 长期目标
- Electron跨平台打包
- 持续集成/持续部署完善
- 多平台统一构建系统
- 插件系统支持

## 维护指南

### 版本发布流程
1. 更新setup.py中的版本号
2. 更新CHANGELOG.md
3. 创建Git标签
4. 运行构建脚本
5. 测试新版本
6. 发布到GitHub Releases

### 依赖管理
```bash
# 检查过时依赖
pip list --outdated

# 更新依赖
pip install --upgrade -r requirements.txt

# 安全检查
pip install safety
safety check
```

---

*最后更新: 2025-10-21*