# 安装和部署指南

## 快速安装

### 通用方法（所有平台）

```bash
# 使用Python启动器（推荐）
python3 run_analyzer.py
```

### Mac/Linux

```bash
# 使用shell脚本
chmod +x run_analyzer.sh
./run_analyzer.sh
```

### Windows

```cmd
# 方法1：双击 run_analyzer.bat

# 方法2：命令行
run_analyzer.bat

# 方法3：使用Python
python run_analyzer.py
```

## 详细安装步骤

### 1. 安装Python

#### Windows
1. 访问 https://www.python.org/downloads/
2. 下载Python 3.8+（推荐3.10）
3. 运行安装程序
4. **重要**：勾选"Add Python to PATH"
5. 选择"Install Now"

#### Mac
```bash
# 使用Homebrew
brew install python3

# 或者从官网下载
# https://www.python.org/downloads/mac-osx/
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3 python3-pip python3-tk python3-venv
```

#### Linux (CentOS/RHEL/Fedora)
```bash
sudo yum install python3 python3-pip python3-tkinter
```

### 2. 验证安装

```bash
# 检查Python版本
python3 --version
# 或
python --version

# 检查pip
pip3 --version
# 或
pip --version
```

### 3. 安装项目

#### 方法A：下载压缩包
1. 下载项目zip文件
2. 解压到任意目录
3. 进入目录运行启动脚本

#### 方法B：Git克隆
```bash
git clone <repository-url>
cd mars-log-analyzer
```

### 4. 首次运行

选择适合你系统的方法：

```bash
# 通用方法
python3 run_analyzer.py

# Mac/Linux
./run_analyzer.sh

# Windows
run_analyzer.bat
```

程序会自动：
1. 创建虚拟环境
2. 安装依赖包
3. 启动GUI界面

## 手动安装（高级用户）

### 创建虚拟环境

```bash
# 创建
python3 -m venv venv

# 激活 - Linux/Mac
source venv/bin/activate

# 激活 - Windows
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 运行程序
python mars_log_analyzer_pro.py
```

## 依赖包说明

### 必需依赖
- **matplotlib**: 数据可视化，生成图表
- **tkinter**: GUI界面（Python内置）

### 可选依赖
- **numpy**: 提升数值计算性能
- **pandas**: 数据分析功能增强
- **openpyxl**: 导出Excel格式

### 安装可选依赖
```bash
# 性能优化包
pip install numpy

# 数据分析增强
pip install pandas openpyxl
```

## 系统要求

### 最低配置
- CPU: 双核 1.5GHz
- 内存: 2GB RAM
- 磁盘: 100MB可用空间
- 分辨率: 1280x720

### 推荐配置
- CPU: 四核 2.0GHz+
- 内存: 4GB+ RAM
- 磁盘: 500MB可用空间
- 分辨率: 1920x1080

### 操作系统
- Windows 10/11
- macOS 10.12+
- Ubuntu 18.04+
- CentOS 7+
- 其他支持Python 3.6+的系统

## 常见问题

### Q: Windows提示"python不是内部或外部命令"
A: Python未添加到PATH，重新安装时勾选"Add to PATH"

### Q: Mac提示"python3: command not found"
A: 安装Python3：
```bash
brew install python3
```

### Q: Linux提示"No module named 'tkinter'"
A: 安装tkinter：
```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# CentOS/RHEL
sudo yum install python3-tkinter
```

### Q: 提示"No module named 'matplotlib'"
A: 依赖未安装，运行：
```bash
pip install matplotlib
# 或
pip3 install matplotlib
```

### Q: 虚拟环境创建失败
A: 可能的解决方法：
```bash
# 升级pip
python -m pip install --upgrade pip

# 使用系统Python
python3 -m venv venv --system-site-packages
```

### Q: GUI界面显示异常
A: 检查显示设置：
- Windows: 调整DPI缩放至100%或125%
- Mac: 系统偏好设置→显示器→缩放
- Linux: 检查桌面环境的缩放设置

## 卸载方法

### 完全卸载
1. 删除项目文件夹
2. 清理生成的文件：
   - `*.log` 文件（解析结果）
   - `venv/` 目录（虚拟环境）

### 保留数据卸载
1. 备份 `*.log` 文件
2. 删除项目文件夹
3. 保留的log文件可用文本编辑器查看

## 更新方法

### 保留数据更新
```bash
# 1. 备份当前数据
cp *.log backup/

# 2. 更新代码
git pull
# 或下载新版本覆盖

# 3. 更新依赖
pip install -r requirements.txt --upgrade
```

### 全新安装更新
1. 备份需要的log文件
2. 删除旧版本
3. 安装新版本
4. 恢复log文件

## 打包发布

### 创建独立可执行文件

#### Windows (PyInstaller)
```bash
pip install pyinstaller
pyinstaller --onefile --windowed mars_log_analyzer_pro.py
```

#### Mac (py2app)
```bash
pip install py2app
py2applet --make-setup mars_log_analyzer_pro.py
python setup.py py2app
```

#### Linux (PyInstaller)
```bash
pip install pyinstaller
pyinstaller --onefile mars_log_analyzer_pro.py
```

## 网络部署（可选）

### Docker部署
```dockerfile
FROM python:3.10-slim
RUN apt-get update && apt-get install -y python3-tk
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["python", "mars_log_analyzer_pro.py"]
```

### 远程访问（X11转发）
```bash
# SSH with X11
ssh -X user@server
cd mars-log-analyzer
python mars_log_analyzer_pro.py
```

## 技术支持

遇到问题？
1. 查看 [README.md](README.md) 的故障排除章节
2. 提交Issue到项目仓库
3. 发送邮件至技术支持

---
最后更新：2024年1月