#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iOS沙盒浏览标签页模块
"""

import os
import sys
import re
import platform
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
from datetime import datetime


class SandboxBrowserTab:
    """iOS沙盒浏览标签页"""

    def __init__(self, parent, main_app):
        """初始化沙盒浏览标签页

        Args:
            parent: 父容器
            main_app: 主应用程序实例
        """
        self.parent = parent
        self.main_app = main_app
        self.device_id = None
        self.current_app_id = None
        self.afc_client = None
        self.search_results = []
        self.current_search_text = ""
        self.create_widgets()

    def create_widgets(self):
        """创建iOS沙盒浏览标签页"""
        try:
            from pymobiledevice3.lockdown import LockdownClient
            from pymobiledevice3.services.installation_proxy import InstallationProxyService
            from pymobiledevice3.services.afc import AfcService, AfcShell
            self.has_dependency = True
        except ImportError:
            self.has_dependency = False
            self.show_dependency_error()
            return

        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(top_frame, text="设备:").pack(side=tk.LEFT, padx=(0, 5))
        self.device_combo = ttk.Combobox(top_frame, state="readonly", width=30)
        self.device_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.device_combo.bind("<<ComboboxSelected>>", self.on_device_selected)

        ttk.Button(top_frame, text="刷新设备", command=self.refresh_devices).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(top_frame, text="应用:").pack(side=tk.LEFT, padx=(0, 5))
        self.app_combo = ttk.Combobox(top_frame, state="readonly", width=40)
        self.app_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.app_combo.bind("<<ComboboxSelected>>", self.on_app_selected)

        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)

        tree_frame = ttk.Frame(content_frame)
        tree_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        columns = ("size", "date", "path")
        self.tree = ttk.Treeview(tree_frame, columns=columns, yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.tree.yview)

        self.tree.heading("#0", text="名称")
        self.tree.heading("size", text="大小")
        self.tree.heading("date", text="修改日期")

        self.tree.column("#0", width=300)
        self.tree.column("size", width=100)
        self.tree.column("date", width=150)
        self.tree.column("path", width=0, stretch=False)

        self.tree.bind("<Double-Button-1>", self.on_item_double_click)
        self.tree.bind("<Button-3>", self.show_context_menu)
        self.tree.bind("<<TreeviewOpen>>", self.on_tree_expand)

        self.context_menu = tk.Menu(self.tree, tearoff=0)
        self.context_menu.add_command(label="预览", command=self.preview_selected)
        self.context_menu.add_command(label="导出", command=self.export_selected)
        self.context_menu.add_command(label="打开", command=self.open_selected)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="删除", command=self.delete_selected)
        self.context_menu.add_command(label="刷新", command=self.refresh_current_dir)

        # 搜索框
        search_frame = ttk.Frame(main_frame)
        search_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Label(search_frame, text="搜索:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.search_entry.bind("<Return>", lambda e: self.search_files())

        self.search_type_var = tk.StringVar(value="文件名")
        search_type_combo = ttk.Combobox(search_frame, textvariable=self.search_type_var,
                                         values=["文件名", "文件内容", "所有"],
                                         state="readonly", width=10)
        search_type_combo.pack(side=tk.LEFT, padx=(0, 5))

        self.search_button = ttk.Button(search_frame, text="搜索", command=self.search_files)
        self.search_button.pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(search_frame, text="清除", command=self.clear_search).pack(side=tk.LEFT, padx=(0, 5))

        self.search_status = ttk.Label(search_frame, text="")
        self.search_status.pack(side=tk.LEFT, padx=(10, 0))

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(button_frame, text="预览", command=self.preview_selected).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="导出选中", command=self.export_selected).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="打开文件", command=self.open_selected).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="删除", command=self.delete_selected).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="刷新", command=self.refresh_current_dir).pack(side=tk.LEFT)

        self.status_label = ttk.Label(main_frame, text="请先选择设备和应用", relief=tk.SUNKEN)
        self.status_label.pack(fill=tk.X, pady=(10, 0))

        self.refresh_devices()

    def show_dependency_error(self):
        """显示依赖错误提示"""
        error_frame = ttk.Frame(self.parent)
        error_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        icon_label = ttk.Label(error_frame, text="⚠️", font=("Arial", 48))
        icon_label.pack(pady=(20, 10))

        title_label = ttk.Label(
            error_frame,
            text="iOS沙盒浏览功能需要安装额外依赖",
            font=("Arial", 14, "bold")
        )
        title_label.pack(pady=(0, 20))

        info_text = """
请运行以下命令安装必要的依赖:

pip install pymobiledevice3

或者使用项目根目录的requirements.txt:

pip install -r requirements.txt

安装完成后重启程序即可使用iOS沙盒浏览功能。
        """

        info_label = ttk.Label(error_frame, text=info_text, justify=tk.LEFT)
        info_label.pack(padx=20)

    def refresh_devices(self):
        """刷新设备列表"""
        if not self.has_dependency:
            return

        try:
            from pymobiledevice3.usbmux import list_devices
            from pymobiledevice3.lockdown import create_using_usbmux

            devices = list_devices()
            if not devices:
                self.device_combo['values'] = ["未检测到设备"]
                self.device_combo.current(0)
                self.update_status("未检测到iOS设备")
                return

            device_list = []
            self.device_map = {}
            for device in devices:
                udid = device.serial
                try:
                    lockdown = create_using_usbmux(serial=udid)
                    device_name_full = lockdown.get_value(key='DeviceName')
                    product_type = lockdown.get_value(key='ProductType')
                    device_name = f"{device_name_full} ({product_type}) - {udid[:8]}..."
                except:
                    device_name = f"{udid[:8]}..."
                device_list.append(device_name)
                self.device_map[device_name] = udid

            self.device_combo['values'] = device_list
            if device_list:
                self.device_combo.current(0)
                self.on_device_selected(None)

        except Exception as e:
            messagebox.showerror("错误", f"刷新设备列表失败: {str(e)}")
            self.update_status(f"错误: {str(e)}")

    def on_device_selected(self, event):
        """设备选择事件"""
        if not self.has_dependency:
            return

        device_name = self.device_combo.get()
        if device_name not in self.device_map:
            return

        self.device_id = self.device_map[device_name]
        self.update_status(f"已选择设备: {self.device_id[:8]}...")

        threading.Thread(target=self._load_apps_async, daemon=True).start()

    def _load_apps_async(self):
        """异步加载应用列表，并过滤无法访问的应用"""
        try:
            from pymobiledevice3.lockdown import create_using_usbmux
            from pymobiledevice3.services.installation_proxy import InstallationProxyService
            from pymobiledevice3.services.house_arrest import HouseArrestService

            lockdown = create_using_usbmux(serial=self.device_id)
            install_proxy = InstallationProxyService(lockdown=lockdown)

            apps = install_proxy.get_apps(application_type='User')

            # 更新状态：开始检测可访问的应用
            total_apps = len(apps)
            self.parent.after(0, lambda: self.update_status(f"正在检测 {total_apps} 个应用的访问权限..."))

            app_list = []
            self.app_map = {}
            checked_count = 0
            accessible_count = 0

            for bundle_id, app_info in apps.items():
                checked_count += 1
                app_name = app_info.get('CFBundleDisplayName', bundle_id)

                # 更新检测进度
                self.parent.after(0, lambda count=checked_count, total=total_apps:
                                 self.update_status(f"正在检测应用访问权限... ({count}/{total})"))

                # 尝试连接应用沙盒以检测是否可访问
                try:
                    lockdown_temp = create_using_usbmux(serial=self.device_id)
                    house_arrest_test = HouseArrestService(lockdown=lockdown_temp, bundle_id=bundle_id)
                    # 如果成功创建 HouseArrestService，说明可以访问
                    accessible_count += 1

                    display_name = f"{app_name} ({bundle_id})"
                    app_list.append(display_name)
                    self.app_map[display_name] = {
                        'bundle_id': bundle_id,
                        'name': app_name,
                        'info': app_info
                    }
                except Exception:
                    # 无法访问的应用，跳过不添加到列表
                    pass

            app_list.sort()

            # 更新状态：显示过滤结果
            filtered_count = total_apps - accessible_count
            if filtered_count > 0:
                self.parent.after(0, lambda acc=accessible_count, flt=filtered_count:
                                 self.update_status(f"已加载 {acc} 个可访问应用（已过滤 {flt} 个无法访问的应用）"))
            else:
                self.parent.after(0, lambda acc=accessible_count:
                                 self.update_status(f"已加载 {acc} 个应用"))

            self.parent.after(0, self._update_app_combo, app_list)

        except Exception as e:
            error_msg = str(e)
            self.parent.after(0, lambda msg=error_msg: messagebox.showerror("错误", f"加载应用列表失败: {msg}"))
            self.parent.after(0, lambda msg=error_msg: self.update_status(f"错误: {msg}"))

    def _update_app_combo(self, app_list):
        """更新应用下拉框"""
        if not app_list:
            self.app_combo['values'] = ["未找到可访问的应用"]
            self.app_combo.current(0)
            self.update_status("未找到可访问的应用")
            return

        self.app_combo['values'] = app_list
        self.app_combo.current(0)
        # 自动加载第一个应用（列表中的应用都已验证可访问）
        self.on_app_selected(None)

    def on_app_selected(self, event):
        """应用选择事件"""
        if not self.has_dependency:
            return

        app_display = self.app_combo.get()
        if app_display not in self.app_map:
            return

        self.current_app_id = self.app_map[app_display]['bundle_id']
        self.update_status(f"正在连接应用沙盒: {self.current_app_id}")

        threading.Thread(target=self._load_sandbox_async, daemon=True).start()

    def _load_sandbox_async(self):
        """异步加载沙盒文件"""
        try:
            from pymobiledevice3.lockdown import create_using_usbmux
            from pymobiledevice3.services.house_arrest import HouseArrestService

            lockdown = create_using_usbmux(serial=self.device_id)
            house_arrest = HouseArrestService(lockdown=lockdown, bundle_id=self.current_app_id)

            self.afc_client = house_arrest

            self.parent.after(0, lambda: self.tree.delete(*self.tree.get_children()))

            self._list_directory(".", "")

            self.parent.after(0, lambda app_id=self.current_app_id: self.update_status(f"已加载应用沙盒: {app_id}"))

        except Exception as e:
            error_msg = str(e)
            self.parent.after(0, lambda msg=error_msg: messagebox.showerror("错误", f"连接应用沙盒失败: {msg}"))
            self.parent.after(0, lambda msg=error_msg: self.update_status(f"错误: {msg}"))

            # 清空文件树
            self.parent.after(0, lambda: self.tree.delete(*self.tree.get_children()))

    def _list_directory(self, path, parent_item):
        """列出目录内容"""
        try:
            items = self.afc_client.listdir(path)

            items_data = []
            for item in items:
                if item in [".", "..", ".com.apple.mobile_container_manager.metadata.plist"]:
                    continue

                item_path = f"{path}/{item}" if path != "." else item

                try:
                    info = self.afc_client.stat(item_path)
                    is_dir = info['st_ifmt'] == 'S_IFDIR'
                    size = info.get('st_size', 0)
                    mtime = info.get('st_mtime')

                    if mtime and hasattr(mtime, 'strftime'):
                        date_str = mtime.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        date_str = ""

                    size_str = self._format_size(size) if not is_dir else ""

                    items_data.append({
                        'name': item,
                        'path': item_path,
                        'is_dir': is_dir,
                        'size': size_str,
                        'date': date_str
                    })

                except Exception as e:
                    continue

            self.parent.after(0, self._insert_tree_items, parent_item, items_data)

        except Exception as e:
            pass

    def _insert_tree_items(self, parent, items_data):
        """批量插入树形项"""
        for item_data in items_data:
            self._insert_tree_item(
                parent,
                item_data['name'],
                item_data['path'],
                item_data['is_dir'],
                item_data['size'],
                item_data['date']
            )

    def _insert_tree_item(self, parent, name, path, is_dir, size, date):
        """插入树形项"""
        icon = "📁" if is_dir else "📄"
        display_name = f"{icon} {name}"

        item_id = self.tree.insert(parent, "end", text=display_name,
                                    values=(size, date, path),
                                    tags=("directory" if is_dir else "file",))

        if is_dir:
            self.tree.insert(item_id, "end", text="", values=("", "", ""), tags=("placeholder",))

    def on_tree_expand(self, event):
        """树形节点展开事件"""
        item_id = self.tree.focus()
        if not item_id:
            return

        tags = self.tree.item(item_id, "tags")

        if "directory" in tags:
            children = self.tree.get_children(item_id)
            if children:
                first_child = children[0]
                first_tags = self.tree.item(first_child, "tags")
                if "placeholder" in first_tags:
                    self.tree.delete(first_child)
                    path = self.tree.set(item_id, "path")
                    threading.Thread(target=self._list_directory, args=(path, item_id), daemon=True).start()

    def on_item_double_click(self, event):
        """双击事件处理"""
        item = self.tree.selection()
        if not item:
            return

        item_id = item[0]
        tags = self.tree.item(item_id, "tags")

        if "placeholder" in tags:
            return

        if "file" in tags:
            self.preview_selected()

    def show_context_menu(self, event):
        """显示右键菜单"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def export_selected(self):
        """导出选中的文件/目录"""
        item = self.tree.selection()
        if not item:
            messagebox.showwarning("提示", "请先选择要导出的文件或目录")
            return

        item_id = item[0]
        tags = self.tree.item(item_id, "tags")

        if "placeholder" in tags:
            messagebox.showwarning("提示", "请先展开目录")
            return

        path = self.tree.set(item_id, "path")
        if not path:
            messagebox.showwarning("提示", "无效的路径")
            return

        # 清理文件名，移除图标和搜索标记
        name = self.tree.item(item_id, "text")
        name = name.replace("📁 ", "").replace("📄 ", "")
        # 如果是搜索结果，移除匹配类型标记
        if "search_result" in tags:
            # 移除 [文件名] 或 [文件内容] 标记
            name = re.sub(r'\s*\[.*?\]$', '', name)

        if "directory" in tags:
            save_path = filedialog.askdirectory(title="选择保存目录")
            if save_path:
                dest_path = os.path.join(save_path, name)
                threading.Thread(target=self._export_directory_async,
                                 args=(path, dest_path), daemon=True).start()
        else:
            save_path = filedialog.asksaveasfilename(
                title="保存文件",
                initialfile=name,
                defaultextension=os.path.splitext(name)[1]
            )
            if save_path:
                threading.Thread(target=self._export_file_async,
                                 args=(path, save_path), daemon=True).start()

    def _export_file_async(self, remote_path, local_path):
        """异步导出文件"""
        try:
            self.parent.after(0, lambda path=remote_path: self.update_status(f"正在导出: {path}"))

            data = self.afc_client.get_file_contents(remote_path)

            with open(local_path, 'wb') as f:
                f.write(data)

            self.parent.after(0, lambda path=local_path: self.update_status(f"导出成功: {path}"))
            self.parent.after(0, lambda path=local_path: messagebox.showinfo("成功", f"文件已导出到: {path}"))

        except Exception as e:
            error_msg = str(e)
            self.parent.after(0, lambda msg=error_msg: messagebox.showerror("错误", f"导出失败: {msg}"))
            self.parent.after(0, lambda msg=error_msg: self.update_status(f"导出失败: {msg}"))

    def _export_directory_async(self, remote_path, local_path):
        """异步导出目录"""
        try:
            self.parent.after(0, lambda path=remote_path: self.update_status(f"正在导出目录: {path}"))

            os.makedirs(local_path, exist_ok=True)

            self._export_directory_recursive(remote_path, local_path)

            self.parent.after(0, lambda path=local_path: self.update_status(f"导出成功: {path}"))
            self.parent.after(0, lambda path=local_path: messagebox.showinfo("成功", f"目录已导出到: {path}"))

        except Exception as e:
            error_msg = str(e)
            self.parent.after(0, lambda msg=error_msg: messagebox.showerror("错误", f"导出失败: {msg}"))
            self.parent.after(0, lambda msg=error_msg: self.update_status(f"导出失败: {msg}"))

    def _export_directory_recursive(self, remote_path, local_path):
        """递归导出目录"""
        items = self.afc_client.listdir(remote_path)

        for item in items:
            if item in [".", "..", ".com.apple.mobile_container_manager.metadata.plist"]:
                continue

            remote_item = f"{remote_path}/{item}"
            local_item = os.path.join(local_path, item)

            try:
                info = self.afc_client.stat(remote_item)
                is_dir = info['st_ifmt'] == 'S_IFDIR'

                if is_dir:
                    os.makedirs(local_item, exist_ok=True)
                    self._export_directory_recursive(remote_item, local_item)
                else:
                    data = self.afc_client.get_file_contents(remote_item)
                    with open(local_item, 'wb') as f:
                        f.write(data)

            except Exception as e:
                print(f"导出失败: {remote_item}, {e}")
                continue

    def open_selected(self):
        """打开选中的文件"""
        item = self.tree.selection()
        if not item:
            messagebox.showwarning("提示", "请先选择要打开的文件")
            return

        item_id = item[0]
        tags = self.tree.item(item_id, "tags")

        if "placeholder" in tags:
            messagebox.showwarning("提示", "请先展开目录")
            return

        if "directory" in tags:
            messagebox.showinfo("提示", "无法直接打开目录,请导出后查看")
            return

        path = self.tree.set(item_id, "path")
        if not path:
            messagebox.showwarning("提示", "无效的文件路径")
            return

        # 清理文件名，移除图标和搜索标记
        name = self.tree.item(item_id, "text").replace("📄 ", "")
        if "search_result" in tags:
            # 移除 [文件名] 或 [文件内容] 标记
            import re
            name = re.sub(r'\s*\[.*?\]$', '', name)

        import tempfile
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, name)

        threading.Thread(target=self._open_file_async,
                         args=(path, temp_path), daemon=True).start()

    def _open_file_async(self, remote_path, local_path):
        """异步打开文件"""
        try:
            self.parent.after(0, lambda path=remote_path: self.update_status(f"正在下载: {path}"))

            data = self.afc_client.get_file_contents(remote_path)

            with open(local_path, 'wb') as f:
                f.write(data)

            # 获取文件扩展名
            file_ext = os.path.splitext(local_path)[1].lower()

            # 对于特殊文件类型，使用预览功能而不是系统打开
            if file_ext in ['.db', '.sqlite', '.sqlite3', '.realm']:
                # 数据库文件，显示提示
                self.parent.after(0, lambda: messagebox.showinfo("提示",
                    f"数据库文件已下载到:\n{local_path}\n\n"
                    "您可以使用专门的数据库工具（如SQLiteStudio、DB Browser等）打开此文件"))
                self.parent.after(0, lambda: self.update_status("数据库文件已下载"))
                return
            elif file_ext in ['.plist']:
                # plist文件，尝试用文本编辑器打开
                if platform.system() == 'Darwin':
                    # macOS上用TextEdit打开
                    os.system(f'open -a TextEdit "{local_path}"')
                else:
                    # 其他系统使用默认方式
                    self._try_open_file(local_path)
            else:
                # 其他文件类型，使用系统默认程序打开
                self._try_open_file(local_path)

            self.parent.after(0, lambda: self.update_status("文件已打开"))

        except Exception as e:
            error_msg = str(e)
            self.parent.after(0, lambda msg=error_msg: messagebox.showerror("错误", f"打开失败: {msg}"))
            self.parent.after(0, lambda msg=error_msg: self.update_status(f"打开失败: {msg}"))

    def _try_open_file(self, file_path):
        """尝试打开文件"""
        try:
            if platform.system() == 'Darwin':
                # macOS
                result = subprocess.run(['open', file_path], capture_output=True, text=True)
                if result.returncode != 0:
                    # 如果打开失败，显示文件位置
                    subprocess.run(['open', '-R', file_path])  # 在Finder中显示文件
                    self.parent.after(0, lambda: messagebox.showinfo("提示",
                        f"文件已下载到:\n{file_path}\n\n系统无法自动打开此文件类型"))
            elif platform.system() == 'Windows':
                os.startfile(file_path)
            else:
                # Linux
                subprocess.run(['xdg-open', file_path])
        except Exception as e:
            # 如果无法打开，至少显示文件位置
            self.parent.after(0, lambda: messagebox.showinfo("提示",
                f"文件已下载到:\n{file_path}\n\n错误: {str(e)}"))

    def delete_selected(self):
        """删除选中的文件/目录"""
        item = self.tree.selection()
        if not item:
            messagebox.showwarning("提示", "请先选择要删除的文件或目录")
            return

        item_id = item[0]
        tags = self.tree.item(item_id, "tags")

        if "placeholder" in tags:
            messagebox.showwarning("提示", "请先展开目录")
            return

        path = self.tree.set(item_id, "path")
        if not path:
            messagebox.showwarning("提示", "无效的路径")
            return

        name = self.tree.item(item_id, "text")

        result = messagebox.askyesno("确认删除", f"确定要删除 {name} 吗?\n\n此操作不可恢复!")
        if not result:
            return

        threading.Thread(target=self._delete_item_async,
                         args=(path, item_id), daemon=True).start()

    def _delete_item_async(self, remote_path, item_id):
        """异步删除文件/目录"""
        try:
            self.parent.after(0, lambda path=remote_path: self.update_status(f"正在删除: {path}"))

            self.afc_client.rm(remote_path)

            self.parent.after(0, lambda id=item_id: self.tree.delete(id))
            self.parent.after(0, lambda: self.update_status("删除成功"))
            self.parent.after(0, lambda: messagebox.showinfo("成功", "删除成功"))

        except Exception as e:
            error_msg = str(e)
            self.parent.after(0, lambda msg=error_msg: messagebox.showerror("错误", f"删除失败: {msg}"))
            self.parent.after(0, lambda msg=error_msg: self.update_status(f"删除失败: {msg}"))

    def refresh_current_dir(self):
        """刷新当前目录"""
        if not self.current_app_id:
            messagebox.showwarning("提示", "请先选择应用")
            return

        self.on_app_selected(None)

    def preview_selected(self):
        """预览选中的文件"""
        item = self.tree.selection()
        if not item:
            messagebox.showwarning("提示", "请先选择要预览的文件")
            return

        item_id = item[0]
        tags = self.tree.item(item_id, "tags")

        if "placeholder" in tags:
            messagebox.showwarning("提示", "请先展开目录")
            return

        if "directory" in tags:
            messagebox.showinfo("提示", "无法预览目录")
            return

        path = self.tree.set(item_id, "path")
        if not path:
            messagebox.showwarning("提示", "无效的文件路径")
            return

        # 清理文件名，移除图标和搜索标记
        name = self.tree.item(item_id, "text").replace("📄 ", "")
        if "search_result" in tags:
            # 移除 [文件名] 或 [文件内容] 标记
            import re
            name = re.sub(r'\s*\[.*?\]$', '', name)

        threading.Thread(target=self._preview_file_async, args=(path, name), daemon=True).start()

    def _preview_file_async(self, remote_path, filename):
        """异步预览文件"""
        try:
            self.parent.after(0, lambda path=remote_path: self.update_status(f"正在加载: {path}"))

            data = self.afc_client.get_file_contents(remote_path)

            file_ext = os.path.splitext(filename)[1].lower()

            if file_ext in ['.txt', '.log', '.json', '.xml', '.plist', '.html', '.css', '.js', '.py', '.md', '.sh', '.h', '.m', '.swift', '.c', '.cpp']:
                try:
                    text_content = data.decode('utf-8')
                    self.parent.after(0, lambda name=filename, content=text_content: self._show_text_preview(name, content))
                except:
                    try:
                        text_content = data.decode('gbk')
                        self.parent.after(0, lambda name=filename, content=text_content: self._show_text_preview(name, content))
                    except:
                        self.parent.after(0, lambda: messagebox.showwarning("提示", "无法解码文本文件"))
                        return
            elif file_ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico']:
                self.parent.after(0, lambda name=filename, img_data=data: self._show_image_preview(name, img_data))
            elif file_ext in ['.db', '.sqlite', '.sqlite3']:
                self.parent.after(0, lambda: messagebox.showinfo("提示", f"SQLite数据库文件\n文件名: {filename}\n大小: {len(data)} 字节\n\n建议导出后使用专业工具查看"))
            else:
                hex_preview = self._format_hex(data[:512])
                self.parent.after(0, lambda name=filename, content=hex_preview, size=len(data): self._show_hex_preview(name, content, size))

            self.parent.after(0, lambda: self.update_status("预览完成"))

        except Exception as e:
            error_msg = str(e)
            self.parent.after(0, lambda msg=error_msg: messagebox.showerror("错误", f"预览失败: {msg}"))
            self.parent.after(0, lambda msg=error_msg: self.update_status(f"预览失败: {msg}"))

    def _show_text_preview(self, filename, content):
        """显示文本预览"""
        preview_window = tk.Toplevel(self.parent)
        preview_window.title(f"预览: {filename}")
        preview_window.geometry("800x600")

        toolbar = ttk.Frame(preview_window)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(toolbar, text=f"文件: {filename}  |  大小: {len(content)} 字符").pack(side=tk.LEFT)

        def save_as():
            save_path = filedialog.asksaveasfilename(
                title="另存为",
                initialfile=filename,
                defaultextension=os.path.splitext(filename)[1]
            )
            if save_path:
                with open(save_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("成功", "保存成功")

        ttk.Button(toolbar, text="另存为", command=save_as).pack(side=tk.RIGHT)

        text_frame = ttk.Frame(preview_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        scrollbar_y = ttk.Scrollbar(text_frame)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)

        scrollbar_x = ttk.Scrollbar(text_frame, orient=tk.HORIZONTAL)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        text_widget = tk.Text(text_frame, wrap=tk.NONE,
                              yscrollcommand=scrollbar_y.set,
                              xscrollcommand=scrollbar_x.set,
                              font=("Courier", 11))
        text_widget.pack(fill=tk.BOTH, expand=True)

        scrollbar_y.config(command=text_widget.yview)
        scrollbar_x.config(command=text_widget.xview)

        text_widget.insert("1.0", content)
        text_widget.config(state=tk.DISABLED)

    def _show_image_preview(self, filename, image_data):
        """显示图片预览"""
        try:
            from PIL import Image, ImageTk
            import io

            preview_window = tk.Toplevel(self.parent)
            preview_window.title(f"预览: {filename}")

            toolbar = ttk.Frame(preview_window)
            toolbar.pack(fill=tk.X, padx=5, pady=5)

            img = Image.open(io.BytesIO(image_data))
            ttk.Label(toolbar, text=f"文件: {filename}  |  尺寸: {img.width}x{img.height}  |  大小: {len(image_data)} 字节").pack(side=tk.LEFT)

            def save_as():
                save_path = filedialog.asksaveasfilename(
                    title="另存为",
                    initialfile=filename,
                    defaultextension=os.path.splitext(filename)[1]
                )
                if save_path:
                    with open(save_path, 'wb') as f:
                        f.write(image_data)
                    messagebox.showinfo("成功", "保存成功")

            ttk.Button(toolbar, text="另存为", command=save_as).pack(side=tk.RIGHT)

            canvas_frame = ttk.Frame(preview_window)
            canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

            canvas = tk.Canvas(canvas_frame, bg='gray')
            scrollbar_y = ttk.Scrollbar(canvas_frame, command=canvas.yview)
            scrollbar_x = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=canvas.xview)

            canvas.config(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

            scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
            scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
            canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            max_width, max_height = 800, 600
            if img.width > max_width or img.height > max_height:
                img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

            photo = ImageTk.PhotoImage(img)
            canvas.create_image(0, 0, anchor=tk.NW, image=photo)
            canvas.image = photo
            canvas.config(scrollregion=canvas.bbox(tk.ALL))

            window_width = min(img.width + 20, 820)
            window_height = min(img.height + 80, 680)
            preview_window.geometry(f"{window_width}x{window_height}")

        except ImportError:
            messagebox.showwarning("提示", "图片预览需要安装Pillow库\n\n运行: pip install Pillow")
        except Exception as e:
            messagebox.showerror("错误", f"图片预览失败: {str(e)}")

    def _show_hex_preview(self, filename, hex_content, total_size):
        """显示十六进制预览"""
        preview_window = tk.Toplevel(self.parent)
        preview_window.title(f"预览 (十六进制): {filename}")
        preview_window.geometry("800x600")

        toolbar = ttk.Frame(preview_window)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(toolbar, text=f"文件: {filename}  |  大小: {total_size} 字节  |  显示前512字节").pack(side=tk.LEFT)

        text_frame = ttk.Frame(preview_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        text_widget = tk.Text(text_frame, wrap=tk.NONE,
                              yscrollcommand=scrollbar.set,
                              font=("Courier", 10))
        text_widget.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=text_widget.yview)

        text_widget.insert("1.0", hex_content)
        text_widget.config(state=tk.DISABLED)

    @staticmethod
    def _format_hex(data):
        """格式化十六进制数据"""
        lines = []
        for i in range(0, len(data), 16):
            chunk = data[i:i+16]
            hex_part = ' '.join(f'{b:02X}' for b in chunk)
            ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
            lines.append(f"{i:08X}  {hex_part:<48}  {ascii_part}")
        return '\n'.join(lines)

    def search_files(self):
        """搜索文件"""
        if not self.afc_client:
            messagebox.showwarning("提示", "请先选择应用")
            return

        search_text = self.search_entry.get().strip()
        if not search_text:
            messagebox.showwarning("提示", "请输入搜索内容")
            return

        search_type = self.search_type_var.get()
        self.search_results = []
        self.search_status.config(text="正在搜索...")

        # 禁用搜索按钮
        self.search_button.config(state=tk.DISABLED)

        # 在新线程中执行搜索
        threading.Thread(target=self._do_search,
                        args=(search_text, search_type),
                        daemon=True).start()

    def _do_search(self, search_text, search_type):
        """执行搜索"""
        try:
            results = []
            total_files = 0
            searched_files = 0

            # 递归搜索所有文件
            def search_directory(path):
                nonlocal total_files, searched_files
                try:
                    items = self.afc_client.listdir(path)

                    for item in items:
                        if item in ['.', '..']:
                            continue

                        # 构建完整路径
                        if path == '.':
                            item_path = item
                        else:
                            item_path = f"{path}/{item}"

                        # 搜索文件名
                        if search_type in ["文件名", "所有"]:
                            if search_text.lower() in item.lower():
                                try:
                                    stat = self.afc_client.stat(item_path)
                                    is_dir = stat.get('st_ifmt') == 'S_IFDIR'
                                    result = {
                                        'path': item_path,
                                        'name': item,
                                        'type': 'directory' if is_dir else 'file',
                                        'size': stat.get('st_size', 0) if not is_dir else 0,
                                        'match_type': '文件名'
                                    }
                                    results.append(result)
                                except Exception:
                                    pass

                        # 检查是否为目录，递归搜索
                        try:
                            stat = self.afc_client.stat(item_path)
                            # 检查是否为目录
                            is_dir = stat.get('st_ifmt') == 'S_IFDIR'
                            if is_dir:  # 是目录
                                search_directory(item_path)
                            elif search_type in ["文件内容", "所有"]:
                                # 搜索文件内容（仅文本文件）
                                file_ext = os.path.splitext(item.lower())[1]
                                if file_ext in ['.txt', '.log', '.json', '.xml', '.plist', '.html',
                                              '.css', '.js', '.py', '.md', '.sh', '.h', '.m',
                                              '.swift', '.c', '.cpp', '.yml', '.yaml', '.ini',
                                              '.cfg', '.conf', '.properties']:
                                    try:
                                        # 读取文件前512KB
                                        with self.afc_client.open(item_path, 'rb') as f:
                                            content = f.read(524288)  # 512KB
                                            text_content = content.decode('utf-8', errors='ignore')
                                            if search_text.lower() in text_content.lower():
                                                results.append({
                                                    'path': item_path,
                                                    'name': item,
                                                    'type': 'file',
                                                    'size': stat.get('st_size', 0),
                                                    'match_type': '文件内容'
                                                })
                                    except Exception:
                                        # 忽略无法读取的文件
                                        pass

                            searched_files += 1
                            total_files += 1

                            # 更新搜索状态
                            if searched_files % 20 == 0:
                                self.parent.after(0, lambda count=searched_files:
                                                 self.search_status.config(
                                    text=f"正在搜索... (已搜索 {count} 个文件)"))

                        except Exception:
                            # 忽略无法访问的项目
                            pass

                except Exception:
                    pass

            # 从根目录开始搜索
            search_directory('.')

            # 在主线程中更新结果
            self.parent.after(0, lambda: self._show_search_results(results, search_text))

        except Exception as e:
            self.parent.after(0, lambda msg=str(e): messagebox.showerror("搜索错误", f"搜索失败: {msg}"))
        finally:
            # 重新启用搜索按钮
            self.parent.after(0, lambda: self.search_button.config(state=tk.NORMAL))

    def _show_search_results(self, results, search_text):
        """显示搜索结果"""
        # 清空树形控件
        self.tree.delete(*self.tree.get_children())

        if not results:
            self.search_status.config(text=f"未找到 '{search_text}' 相关的文件")
            return

        # 保存搜索结果和原始搜索词
        self.search_results = results
        self.current_search_text = search_text

        # 按路径排序
        results.sort(key=lambda x: x['path'])

        # 添加搜索结果到树形控件
        for result in results:
            icon = "📁" if result['type'] == 'directory' else "📄"
            size = "" if result['type'] == 'directory' else self._format_size(result['size'])

            # 高亮显示匹配类型
            match_info = f" [{result['match_type']}]"

            item = self.tree.insert('', 'end',
                                   text=f"{icon} {result['name']}{match_info}",
                                   values=(size, "", result['path']))  # 添加空的date值

            # 标记搜索结果项和类型
            tags = ['search_result']
            if result['type'] == 'directory':
                tags.append('directory')
            else:
                tags.append('file')
            self.tree.item(item, tags=tuple(tags))

            # 如果是目录，添加占位符（允许展开）
            if result['type'] == 'directory':
                self.tree.insert(item, 'end', text='', values=('', '', ''), tags=('placeholder',))

        # 配置搜索结果标签样式（可选）
        self.tree.tag_configure('search_result', foreground='blue')

        self.search_status.config(
            text=f"找到 {len(results)} 个匹配项 (搜索: '{search_text}')")

    def clear_search(self):
        """清除搜索结果"""
        self.search_entry.delete(0, tk.END)
        self.search_results = []
        self.current_search_text = ""
        self.search_status.config(text="")

        # 刷新应用内容（恢复正常浏览）
        if self.afc_client:
            # 清空树形控件
            self.tree.delete(*self.tree.get_children())
            # 重新加载根目录
            self._list_directory('.', '')

    def update_status(self, message):
        """更新状态栏"""
        self.status_label.config(text=message)

    @staticmethod
    def _format_size(size):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"