"""
用于将Mars日志分析系统打包成Mac应用的配置文件
使用方法：
1. pip3 install py2app
2. python3 setup.py py2app
"""

from setuptools import setup

APP = ['mars_log_analyzer.py']
DATA_FILES = ['decode_mars_nocrypt_log_file_py3.py']
OPTIONS = {
    'argv_emulation': True,
    'packages': ['tkinter', 'matplotlib'],
    'iconfile': None,  # 可以添加.icns图标文件
    'plist': {
        'CFBundleName': 'Mars日志分析系统',
        'CFBundleDisplayName': 'Mars Log Analyzer',
        'CFBundleGetInfoString': "Mars xlog文件分析工具",
        'CFBundleIdentifier': "com.marsloganalyzer.app",
        'CFBundleVersion': "1.0.0",
        'CFBundleShortVersionString': "1.0.0",
        'NSHumanReadableCopyright': u"Copyright © 2025, All Rights Reserved"
    }
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)