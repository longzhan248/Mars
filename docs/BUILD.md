# Mars Log Analyzer - 打包使用指南

## 概述

使用 PyInstaller 将 Mars Log Analyzer 打包成独立的 Mac 应用程序，无需 Python 环境即可在其他 Mac 电脑上运行。

## 系统要求

### 开发机器（打包）
- macOS 10.13 或更高版本
- Python 3.8 或更高版本
- 已安装项目依赖（通过 `requirements.txt`）

### 目标机器（运行）
- macOS 10.13 或更高版本
- **无需安装 Python**
- **无需安装任何依赖**

## 快速开始

### 一键打包

```bash
cd /path/to/project
./scripts/build_app.sh
```

脚本会自动完成：
1. ✅ 检查并激活虚拟环境
2. ✅ 安装 PyInstaller
3. ✅ 清理旧的构建文件
4. ✅ 执行打包流程
5. ✅ 生成独立应用

### 打包结果

打包成功后，应用位于：
```
dist/MarsLogAnalyzer.app
```

## 手动打包步骤

### 1. 准备环境

```bash
# 进入项目目录
cd /path/to/project

# 激活虚拟环境
source venv/bin/activate

# 安装 PyInstaller
pip install pyinstaller
```

### 2. 执行打包

```bash
# 使用配置文件打包
pyinstaller --clean MarsLogAnalyzer.spec

# 或者直接命令行打包（更简单但配置少）
pyinstaller --windowed --name MarsLogAnalyzer gui/mars_log_analyzer_modular.py
```

### 3. 测试应用

```bash
# 运行打包的应用
open dist/MarsLogAnalyzer.app
```

## 配置文件说明

### MarsLogAnalyzer.spec

这是 PyInstaller 的配置文件，包含以下关键配置：

#### 路径配置
```python
pathex=[
    project_root,
    os.path.join(project_root, 'gui'),
    os.path.join(project_root, 'gui/modules'),
    os.path.join(project_root, 'gui/components'),
    os.path.join(project_root, 'decoders'),
    os.path.join(project_root, 'tools'),
    os.path.join(project_root, 'push_tools'),
]
```
确保所有模块都能被找到。

#### 隐式导入
```python
hiddenimports = [
    'tkinter',
    'matplotlib',
    'cryptography',
    'httpx',
    'h2',
    'jwt',
    ...
]
```
列出所有动态导入的模块。

#### 应用信息
```python
info_plist={
    'CFBundleName': 'Mars Log Analyzer',
    'CFBundleDisplayName': 'Mars Log Analyzer',
    'CFBundleVersion': '1.0.0',
    'NSHighResolutionCapable': True,
    ...
}
```
设置应用的显示名称、版本等信息。

## 分发应用

### 方法1: 直接分享 .app 文件

```bash
# 压缩应用
cd dist
zip -r MarsLogAnalyzer.zip MarsLogAnalyzer.app

# 分享 zip 文件给其他用户
```

### 方法2: 创建 DMG 镜像（推荐）

```bash
# 创建 DMG 镜像
hdiutil create -volname "Mars Log Analyzer" \
    -srcfolder dist/MarsLogAnalyzer.app \
    -ov -format UDZO \
    MarsLogAnalyzer.dmg
```

用户下载 DMG 后：
1. 双击打开 DMG
2. 将应用拖到 Applications 文件夹
3. 弹出 DMG
4. 从 Applications 文件夹运行应用

## 安全和权限

### macOS Gatekeeper

由于应用未经过 Apple 签名，用户首次运行时会遇到安全提示：

#### 解决方法1: 右键打开（推荐）
1. 右键点击应用
2. 选择"打开"
3. 点击"打开"按钮

#### 解决方法2: 移除隔离属性
```bash
xattr -cr /Applications/MarsLogAnalyzer.app
```

#### 解决方法3: 系统设置
1. 打开"系统偏好设置"
2. 进入"安全性与隐私"
3. 点击"仍要打开"

### 代码签名（可选）

如果你有 Apple Developer 账号，可以签名应用：

```bash
# 签名应用
codesign --force --deep --sign "Developer ID Application: Your Name" \
    dist/MarsLogAnalyzer.app

# 验证签名
codesign --verify --verbose dist/MarsLogAnalyzer.app

# 显示签名信息
codesign -dv dist/MarsLogAnalyzer.app
```

### 公证（Notarization）

签名后可以提交公证：

```bash
# 打包为 zip
ditto -c -k --keepParent dist/MarsLogAnalyzer.app MarsLogAnalyzer.zip

# 提交公证
xcrun notarytool submit MarsLogAnalyzer.zip \
    --apple-id "your@email.com" \
    --team-id "TEAM_ID" \
    --password "app-specific-password" \
    --wait

# 装订票据
xcrun stapler staple dist/MarsLogAnalyzer.app
```

## 故障排除

### 常见问题

#### Q1: 打包失败，提示模块找不到？
**原因**: hiddenimports 配置不完整

**解决**:
```python
# 在 MarsLogAnalyzer.spec 中添加缺失的模块
hiddenimports = [
    'missing_module',  # 添加缺失的模块
    ...
]
```

#### Q2: 应用启动失败，没有错误提示？
**原因**: console 模式被禁用

**调试**:
```python
# 在 MarsLogAnalyzer.spec 中临时启用控制台
exe = EXE(
    ...
    console=True,  # 改为 True 查看错误
    ...
)
```

#### Q3: 应用体积太大？
**原因**: 包含了不必要的依赖

**优化**:
```python
# 在 MarsLogAnalyzer.spec 中排除模块
excludes=[
    'pytest',
    'black',
    'pylint',
    'test',
    'tests',
],
```

#### Q4: matplotlib 图表显示异常？
**原因**: 缺少数据文件

**解决**:
```python
# 在 MarsLogAnalyzer.spec 中添加
datas += collect_data_files('matplotlib')
```

#### Q5: 用户反馈无法打开应用？
**原因**: macOS Gatekeeper 阻止

**提供给用户的解决方案**:
```bash
# 方法1: 移除隔离属性
xattr -cr /Applications/MarsLogAnalyzer.app

# 方法2: 右键点击应用，选择"打开"
```

### 调试技巧

#### 查看详细错误
```bash
# 从终端启动应用
./dist/MarsLogAnalyzer.app/Contents/MacOS/MarsLogAnalyzer

# 查看系统日志
log stream --predicate 'process == "MarsLogAnalyzer"' --level debug
```

#### 检查应用结构
```bash
# 查看应用内容
tree dist/MarsLogAnalyzer.app

# 查看 Python 字节码
ls -lh dist/MarsLogAnalyzer.app/Contents/MacOS/
```

#### 测试依赖
```bash
# 在虚拟环境中测试导入
python -c "import tkinter; import matplotlib; print('OK')"
```

## 应用大小优化

### 当前大小
- 完整应用: 约 100-150MB
- 主要占用: matplotlib (50%), Python runtime (30%), 其他依赖 (20%)

### 优化建议

#### 1. 使用 UPX 压缩
```python
# 在 MarsLogAnalyzer.spec 中
exe = EXE(
    ...
    upx=True,  # 启用 UPX 压缩
    ...
)
```

#### 2. 排除不必要的文件
```python
excludes=[
    'test',
    'tests',
    'unittest',
    'email',
    'http.server',
    'xmlrpc',
]
```

#### 3. 使用轻量级依赖
- 考虑用 Pillow 替代完整的图像库
- 移除未使用的 matplotlib 后端

## 持续集成

### GitHub Actions 示例

创建 `.github/workflows/build.yml`:

```yaml
name: Build macOS App

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: macos-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pyinstaller

    - name: Build app
      run: |
        pyinstaller --clean MarsLogAnalyzer.spec

    - name: Create DMG
      run: |
        hdiutil create -volname "Mars Log Analyzer" \
          -srcfolder dist/MarsLogAnalyzer.app \
          -ov -format UDZO \
          MarsLogAnalyzer.dmg

    - name: Upload artifact
      uses: actions/upload-artifact@v3
      with:
        name: MarsLogAnalyzer
        path: MarsLogAnalyzer.dmg

    - name: Release
      uses: softprops/action-gh-release@v1
      with:
        files: MarsLogAnalyzer.dmg
```

## 用户安装指南

### 安装步骤

1. **下载应用**
   - 从 GitHub Releases 下载 `MarsLogAnalyzer.app.zip` 或 `MarsLogAnalyzer.dmg`

2. **解压（如果是 zip）**
   - 双击 zip 文件自动解压

3. **安装应用**
   - 将 `MarsLogAnalyzer.app` 拖到 `应用程序` 文件夹

4. **首次运行**
   - 打开 `应用程序` 文件夹
   - 右键点击 `MarsLogAnalyzer.app`
   - 选择"打开"
   - 点击"打开"按钮

5. **后续运行**
   - 直接双击打开，或从 Spotlight 搜索

### 系统要求
- macOS 10.13 (High Sierra) 或更高版本
- 约 200MB 可用磁盘空间
- 无需安装 Python 或其他依赖

## 版本管理

### 更新版本号

修改 `MarsLogAnalyzer.spec`:
```python
info_plist={
    'CFBundleVersion': '1.1.0',  # 更新版本
    'CFBundleShortVersionString': '1.1.0',
}
```

### 版本命名规范
- **主版本**: 1.0.0 → 2.0.0 (重大变更)
- **次版本**: 1.0.0 → 1.1.0 (新功能)
- **修订版本**: 1.0.0 → 1.0.1 (Bug修复)

## 最佳实践

### 打包前检查清单
- [ ] 所有功能测试通过
- [ ] 虚拟环境依赖最新
- [ ] 清理了 `__pycache__` 和 `.pyc` 文件
- [ ] 更新了版本号
- [ ] 更新了 CHANGELOG

### 打包后测试清单
- [ ] 应用能正常启动
- [ ] 所有功能正常工作
- [ ] 文件加载正常
- [ ] 导出功能正常
- [ ] IPS 解析正常
- [ ] iOS 推送功能正常

### 发布清单
- [ ] 创建 Git 标签
- [ ] 编写 Release Notes
- [ ] 上传到 GitHub Releases
- [ ] 通知用户更新

## 支持

### 问题反馈
- GitHub Issues: 提交 Bug 和功能请求
- 邮件: 技术支持联系方式

### 文档
- [使用文档](README.md)
- [开发文档](CLAUDE.md)
- [更新日志](CHANGELOG.md)

## 附录

### PyInstaller 命令参考

```bash
# 基础打包
pyinstaller script.py

# 单文件模式
pyinstaller --onefile script.py

# 窗口模式（无控制台）
pyinstaller --windowed script.py

# 指定图标
pyinstaller --icon=icon.icns script.py

# 指定名称
pyinstaller --name MyApp script.py

# 添加数据文件
pyinstaller --add-data "src:dst" script.py

# 添加二进制文件
pyinstaller --add-binary "src:dst" script.py

# 隐式导入
pyinstaller --hidden-import module script.py

# 清理构建
pyinstaller --clean script.py
```

### 常用 macOS 命令

```bash
# 查看应用信息
mdls MarsLogAnalyzer.app

# 查看应用签名
codesign -dv MarsLogAnalyzer.app

# 移除隔离属性
xattr -cr MarsLogAnalyzer.app

# 创建 DMG
hdiutil create -srcfolder app.app -volname "App" app.dmg

# 验证 DMG
hdiutil verify app.dmg
```

---

**更新日期**: 2025-09-28
**文档版本**: 1.0.0