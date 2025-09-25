#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Mars日志分析系统 - 跨平台启动器
支持Windows、Mac、Linux系统
"""

import os
import sys
import platform
import subprocess
from pathlib import Path

def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 6):
        print("错误：需要Python 3.6或更高版本")
        print(f"当前版本：{sys.version}")
        return False
    print(f"Python版本：{sys.version}")
    return True

def create_venv():
    """创建虚拟环境"""
    venv_path = Path("venv")
    if not venv_path.exists():
        print("创建虚拟环境...")
        try:
            subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
            print("虚拟环境创建成功")
            return True
        except subprocess.CalledProcessError as e:
            print(f"创建虚拟环境失败：{e}")
            return False
    return True

def get_pip_executable():
    """获取pip可执行文件路径"""
    system = platform.system()
    if system == "Windows":
        return Path("venv/Scripts/pip.exe")
    else:
        return Path("venv/bin/pip")

def get_python_executable():
    """获取Python可执行文件路径"""
    system = platform.system()
    if system == "Windows":
        return Path("venv/Scripts/python.exe")
    else:
        return Path("venv/bin/python")

def install_dependencies():
    """安装依赖包"""
    pip_exe = get_pip_executable()

    # 检查matplotlib是否已安装
    python_exe = get_python_executable()
    try:
        subprocess.run([str(python_exe), "-c", "import matplotlib"],
                      check=True, capture_output=True)
        print("依赖包已安装")
        return True
    except subprocess.CalledProcessError:
        print("正在安装依赖包...")

    try:
        # 升级pip
        subprocess.run([str(pip_exe), "install", "--upgrade", "pip"],
                      check=True, capture_output=True)

        # 安装matplotlib
        subprocess.run([str(pip_exe), "install", "matplotlib"], check=True)
        print("依赖包安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"安装依赖包失败：{e}")
        print("请手动运行：pip install matplotlib")
        return False

def run_analyzer():
    """运行主程序"""
    python_exe = get_python_executable()

    print("\n" + "="*50)
    print("Mars日志分析系统 - 专业版")
    print("="*50)
    print("\n正在启动...\n")

    try:
        # 运行主程序
        subprocess.run([str(python_exe), "mars_log_analyzer_pro.py"])
    except FileNotFoundError:
        print("错误：找不到主程序文件 mars_log_analyzer_pro.py")
        print("请确保文件在当前目录下")
    except KeyboardInterrupt:
        print("\n程序已停止")
    except Exception as e:
        print(f"运行出错：{e}")

def main():
    """主函数"""
    print("Mars日志分析系统启动器")
    print(f"操作系统：{platform.system()} {platform.release()}")

    # 切换到脚本所在目录
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    print(f"工作目录：{os.getcwd()}")

    # 检查Python版本
    if not check_python_version():
        input("\n按Enter键退出...")
        return

    # 创建虚拟环境
    if not create_venv():
        input("\n按Enter键退出...")
        return

    # 安装依赖
    if not install_dependencies():
        input("\n按Enter键退出...")
        return

    # 运行程序
    run_analyzer()

    # Windows系统下暂停
    if platform.system() == "Windows":
        input("\n按Enter键退出...")

if __name__ == "__main__":
    main()