# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# 项目根目录
project_root = os.path.abspath('.')

# 收集所有数据文件
datas = []

# 收集所有隐式导入
hiddenimports = [
    'tkinter',
    'tkinter.ttk',
    'tkinter.filedialog',
    'tkinter.messagebox',
    'matplotlib',
    'matplotlib.backends.backend_tkagg',
    'matplotlib.figure',
    'matplotlib.pyplot',
    'PIL',
    'PIL._tkinter_finder',
    'cryptography',
    'cryptography.hazmat',
    'cryptography.hazmat.primitives',
    'cryptography.hazmat.backends',
    'httpx',
    'httpx._transports',
    'httpx._transports.default',
    'h2',
    'h2.connection',
    'jwt',
    'json',
    'csv',
    'threading',
    'queue',
    'zlib',
]

# 收集matplotlib数据文件
datas += collect_data_files('matplotlib')

# 分析主程序
a = Analysis(
    ['gui/mars_log_analyzer_modular.py'],
    pathex=[
        project_root,
        os.path.join(project_root, 'gui'),
        os.path.join(project_root, 'gui/modules'),
        os.path.join(project_root, 'gui/components'),
        os.path.join(project_root, 'decoders'),
        os.path.join(project_root, 'tools'),
        os.path.join(project_root, 'push_tools'),
    ],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['runtime_hook_subprocess.py'],  # 添加runtime hook
    excludes=[
        'pytest',
        'black',
        'pylint',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MarsLogAnalyzer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # 改为True以支持subprocess调用
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MarsLogAnalyzer',
)

app = BUNDLE(
    coll,
    name='MarsLogAnalyzer.app',
    icon=None,
    bundle_identifier='com.marslog.analyzer',
    info_plist={
        'CFBundleName': 'Mars Log Analyzer',
        'CFBundleDisplayName': 'Mars Log Analyzer',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundlePackageType': 'APPL',
        'CFBundleSignature': '????',
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
        'LSMinimumSystemVersion': '10.13.0',
        'NSHumanReadableCopyright': 'Copyright © 2025. All rights reserved.',
    },
)