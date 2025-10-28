"""
PyInstaller runtime hook for subprocess
确保打包后的app能够正常调用外部命令
"""
import os
import sys

# 在打包环境中,确保可以找到系统命令
if getattr(sys, 'frozen', False):
    # 应用被打包,添加常见路径到PATH
    paths_to_add = [
        '/usr/local/bin',
        '/usr/bin',
        '/bin',
        '/opt/homebrew/bin',
        os.path.expanduser('~/.local/bin'),
        os.path.expanduser('~/.npm/bin'),
    ]

    # 添加nvm路径
    nvm_dir = os.path.expanduser('~/.nvm/versions/node')
    if os.path.exists(nvm_dir):
        for version_dir in os.listdir(nvm_dir):
            bin_dir = os.path.join(nvm_dir, version_dir, 'bin')
            if os.path.exists(bin_dir):
                paths_to_add.append(bin_dir)

    # 更新PATH
    current_path = os.environ.get('PATH', '')
    new_paths = [p for p in paths_to_add if p not in current_path]
    if new_paths:
        os.environ['PATH'] = ':'.join(new_paths + [current_path])
        print(f"[Runtime Hook] Added paths to PATH: {new_paths}")
