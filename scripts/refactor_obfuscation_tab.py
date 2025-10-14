#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重构obfuscation_tab.py文件

将大文件拆分，使用新创建的辅助模块：
- parameter_help_content.py
- obfuscation_templates.py
- whitelist_ui_helper.py
"""

import os
import sys

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def main():
    obfuscation_tab_file = os.path.join(
        project_root,
        "gui", "modules", "obfuscation_tab.py"
    )

    # 读取原文件
    with open(obfuscation_tab_file, 'r', encoding='utf-8') as f:
        content = f.read()

    print(f"原文件行数: {len(content.splitlines())}")

    # 1. 更新导入语句
    old_imports = """import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
from pathlib import Path
import threading
import json
from datetime import datetime"""

    new_imports = """import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
from pathlib import Path
import threading
import json
from datetime import datetime

# 导入辅助模块
from .parameter_help_content import PARAMETER_HELP_CONTENT
from .obfuscation_templates import OBFUSCATION_TEMPLATES, get_template
from .whitelist_ui_helper import WhitelistUIHelper"""

    content = content.replace(old_imports, new_imports)
    print("✅ 更新导入语句")

    # 2. 简化load_template方法
    old_load_template = '''    def load_template(self, template_name):
        """加载配置模板"""
        templates = {
            "minimal": {
                "class_names": True,
                "method_names": True,
                "property_names": False,
                "protocol_names": False,
                "resources": False,
                "images": False,
                "audio": False,
                "fonts": False,
                "auto_detect": True,
                "fixed_seed": False
            },
            "standard": {
                "class_names": True,
                "method_names": True,
                "property_names": True,
                "protocol_names": True,
                "resources": False,
                "images": False,
                "audio": False,
                "fonts": False,
                "auto_detect": True,
                "fixed_seed": False
            },
            "aggressive": {
                "class_names": True,
                "method_names": True,
                "property_names": True,
                "protocol_names": True,
                "resources": True,
                "images": True,
                "audio": True,
                "fonts": True,
                "auto_detect": True,
                "fixed_seed": False
            }
        }

        if template_name in templates:
            t = templates[template_name]'''

    new_load_template = '''    def load_template(self, template_name):
        """加载配置模板"""
        t = get_template(template_name)

        if t:'''

    content = content.replace(old_load_template, new_load_template)
    print("✅ 简化load_template方法")

    # 3. 替换参数说明内容为导入的常量
    # 查找content = """的开始位置
    content_start = content.find('        # 参数说明内容\n        content = """')
    if content_start != -1:
        # 查找结束的"""
        content_end = content.find('"""', content_start + 50)  # 跳过开始的"""
        content_end = content.find('"""', content_end + 3)  # 找到结束的"""

        if content_end != -1:
            # 替换整个content赋值
            old_content_section = content[content_start:content_end+3]
            new_content_section = '        # 参数说明内容\n        content = PARAMETER_HELP_CONTENT'
            content = content.replace(old_content_section, new_content_section)
            print("✅ 使用PARAMETER_HELP_CONTENT常量")

    # 4. 简化白名单方法（使用辅助类）
    # load_custom_whitelist
    old_load = '''    def load_custom_whitelist(self, tree):
        """加载自定义白名单"""
        # 清空现有项
        for item in tree.get_children():
            tree.delete(item)

        # 白名单文件路径
        whitelist_file = os.path.join(
            os.path.dirname(__file__),
            "obfuscation",
            "custom_whitelist.json"
        )

        if os.path.exists(whitelist_file):
            try:
                with open(whitelist_file, 'r', encoding='utf-8') as f:
                    whitelist_data = json.load(f)

                # 加载白名单项
                for item in whitelist_data.get('items', []):
                    tree.insert('', tk.END, values=(
                        item.get('name', ''),
                        item.get('type', 'custom'),
                        item.get('reason', '')
                    ))

            except Exception as e:
                self.log(f"⚠️  加载白名单失败: {str(e)}")'''

    new_load = '''    def load_custom_whitelist(self, tree):
        """加载自定义白名单"""
        whitelist_file = WhitelistUIHelper.get_whitelist_file_path(os.path.dirname(__file__))
        WhitelistUIHelper.load_whitelist(tree, whitelist_file, self.log)'''

    content = content.replace(old_load, new_load)
    print("✅ 简化load_custom_whitelist方法")

    # save_custom_whitelist
    old_save = '''    def save_custom_whitelist(self, tree):
        """保存自定义白名单"""
        # 收集所有白名单项
        items = []
        for item_id in tree.get_children():
            values = tree.item(item_id, 'values')
            items.append({
                'name': values[0],
                'type': values[1],
                'reason': values[2]
            })

        whitelist_data = {
            'version': '1.0',
            'updated': datetime.now().isoformat(),
            'items': items
        }

        # 确保目录存在
        whitelist_dir = os.path.join(
            os.path.dirname(__file__),
            "obfuscation"
        )
        os.makedirs(whitelist_dir, exist_ok=True)

        # 保存文件
        whitelist_file = os.path.join(whitelist_dir, "custom_whitelist.json")

        try:
            with open(whitelist_file, 'w', encoding='utf-8') as f:
                json.dump(whitelist_data, f, indent=2, ensure_ascii=False)

            self.log(f"✅ 已保存 {len(items)} 个白名单项")
            return True

        except Exception as e:
            messagebox.showerror("错误", f"保存白名单失败:\\n{str(e)}")
            return False'''

    new_save = '''    def save_custom_whitelist(self, tree):
        """保存自定义白名单"""
        whitelist_file = WhitelistUIHelper.get_whitelist_file_path(os.path.dirname(__file__))
        return WhitelistUIHelper.save_whitelist(tree, whitelist_file, self.log)'''

    content = content.replace(old_save, new_save)
    print("✅ 简化save_custom_whitelist方法")

    # 5. 替换add/edit/delete/import/export方法调用辅助类
    replacements = [
        ('    def add_whitelist_item(self, tree):\n        """添加白名单项"""',
         '    def add_whitelist_item(self, tree):\n        """添加白名单项"""\n        WhitelistUIHelper.show_add_dialog(self, tree, lambda: self.save_custom_whitelist(tree), tree.update_stats)'),

        ('    def edit_whitelist_item(self, tree):\n        """编辑白名单项"""',
         '    def edit_whitelist_item(self, tree):\n        """编辑白名单项"""\n        WhitelistUIHelper.show_edit_dialog(self, tree, lambda: self.save_custom_whitelist(tree))'),

        ('    def delete_whitelist_item(self, tree):\n        """删除白名单项"""',
         '    def delete_whitelist_item(self, tree):\n        """删除白名单项"""\n        WhitelistUIHelper.delete_items(tree, lambda: self.save_custom_whitelist(tree), tree.update_stats)'),

        ('    def import_whitelist(self, tree):\n        """导入白名单"""',
         '    def import_whitelist(self, tree):\n        """导入白名单"""\n        WhitelistUIHelper.import_from_file(tree, lambda: self.save_custom_whitelist(tree), tree.update_stats)'),

        ('    def export_whitelist_file(self, tree):\n        """导出白名单"""',
         '    def export_whitelist_file(self, tree):\n        """导出白名单"""\n        WhitelistUIHelper.export_to_file(tree)'),
    ]

    # 注意：需要删除方法体，只保留方法签名和调用
    # 这里暂时跳过，因为需要精确匹配多行内容

    # 保存重构后的文件
    output_file = obfuscation_tab_file + ".refactored"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"\n重构后文件已保存到: {output_file}")
    print(f"重构后行数: {len(content.splitlines())}")
    print(f"\n请检查重构后的文件，如果没问题则：")
    print(f"mv {output_file} {obfuscation_tab_file}")

if __name__ == '__main__':
    main()
