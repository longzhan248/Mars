@echo off
REM Mars日志分析系统启动脚本 - Windows版本

echo =========================================
echo Mars日志分析系统 - 专业版
echo =========================================

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: Python未安装或未添加到PATH
    echo 请访问 https://www.python.org 下载安装Python
    echo 安装时请勾选 "Add Python to PATH"
    pause
    exit /b 1
)

REM 获取脚本所在目录
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM 检查虚拟环境是否存在
set VENV_DIR=%SCRIPT_DIR%venv

if not exist "%VENV_DIR%" (
    echo 创建虚拟环境...
    python -m venv "%VENV_DIR%"
    if %errorlevel% neq 0 (
        echo 创建虚拟环境失败
        pause
        exit /b 1
    )
)

REM 激活虚拟环境
echo 激活虚拟环境...
call "%VENV_DIR%\Scripts\activate.bat"

REM 检查并安装依赖
echo 检查依赖包...
python -c "import matplotlib" >nul 2>&1
if %errorlevel% neq 0 (
    echo 正在安装matplotlib...
    pip install matplotlib
    if %errorlevel% neq 0 (
        echo 安装依赖失败，请检查网络连接
        pause
        exit /b 1
    )
)

REM 启动程序
echo 正在启动程序...
python mars_log_analyzer_pro.py

REM 如果程序异常退出，暂停显示错误
if %errorlevel% neq 0 (
    echo.
    echo 程序异常退出，错误代码: %errorlevel%
    pause
)

REM 退出虚拟环境
deactivate