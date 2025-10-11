#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iOS应用管理模块
负责应用列表的加载、过滤和选择
"""

from tkinter import messagebox
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import time


class AppManager:
    """iOS应用管理器"""

    def __init__(self, parent_tab):
        """初始化应用管理器

        Args:
            parent_tab: 父标签页对象
        """
        self.parent = parent_tab
        self.app_map = {}  # 应用显示名到应用信息的映射

    def _check_app_accessibility(self, device_id, bundle_id, app_info, timeout=2):
        """检测单个应用的访问权限（带超时）

        Args:
            device_id: 设备ID
            bundle_id: 应用Bundle ID
            app_info: 应用信息
            timeout: 超时时间（秒）

        Returns:
            dict or None: 可访问返回应用信息，否则返回None
        """
        try:
            from pymobiledevice3.lockdown import create_using_usbmux
            from pymobiledevice3.services.house_arrest import HouseArrestService

            # 使用超时机制
            result = [None]

            def check():
                try:
                    lockdown = create_using_usbmux(serial=device_id)
                    HouseArrestService(lockdown=lockdown, bundle_id=bundle_id)
                    result[0] = True
                except Exception:
                    result[0] = False

            thread = threading.Thread(target=check, daemon=True)
            thread.start()
            thread.join(timeout=timeout)

            if result[0]:
                app_name = app_info.get('CFBundleDisplayName', bundle_id)
                display_name = f"{app_name} ({bundle_id})"
                return {
                    'display_name': display_name,
                    'bundle_id': bundle_id,
                    'name': app_name,
                    'info': app_info
                }
            else:
                return None

        except Exception:
            return None

    def load_apps_async(self):
        """异步加载应用列表，并使用多线程并发检测访问权限"""
        try:
            from pymobiledevice3.lockdown import create_using_usbmux
            from pymobiledevice3.services.installation_proxy import InstallationProxyService

            device_id = self.parent.device_id
            if not device_id:
                return

            lockdown = create_using_usbmux(serial=device_id)
            install_proxy = InstallationProxyService(lockdown=lockdown)

            apps = install_proxy.get_apps(application_type='User')

            # 更新状态：开始检测可访问的应用
            total_apps = len(apps)
            self.parent.parent.after(0, lambda: self.parent.update_status(
                f"正在检测 {total_apps} 个应用的访问权限..."))

            # 使用线程锁保护共享数据
            lock = threading.Lock()
            app_list = []
            self.app_map = {}
            checked_count = [0]  # 使用列表以便在闭包中修改
            accessible_count = [0]

            # 并发检测（最多同时检测5个应用）
            max_workers = 5
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 提交所有检测任务
                future_to_bundle = {
                    executor.submit(self._check_app_accessibility, device_id, bundle_id, app_info): bundle_id
                    for bundle_id, app_info in apps.items()
                }

                # 边检测边更新UI
                for future in as_completed(future_to_bundle):
                    with lock:
                        checked_count[0] += 1
                        current_checked = checked_count[0]

                    # 获取检测结果
                    result = future.result()
                    if result:
                        with lock:
                            accessible_count[0] += 1
                            current_accessible = accessible_count[0]

                            # 添加到应用列表
                            app_list.append(result['display_name'])
                            self.app_map[result['display_name']] = {
                                'bundle_id': result['bundle_id'],
                                'name': result['name'],
                                'info': result['info']
                            }

                        # 实时更新进度（显示已找到的可访问应用数）
                        self.parent.parent.after(0, lambda count=current_checked, total=total_apps, acc=current_accessible:
                                                 self.parent.update_status(
                                                     f"正在检测... ({count}/{total}) 已找到 {acc} 个可访问应用"))
                    else:
                        # 无法访问的应用，仍更新进度
                        self.parent.parent.after(0, lambda count=current_checked, total=total_apps, acc=accessible_count[0]:
                                                 self.parent.update_status(
                                                     f"正在检测... ({count}/{total}) 已找到 {acc} 个可访问应用"))

            # 排序应用列表
            app_list.sort()

            # 更新状态：显示最终结果
            final_accessible = accessible_count[0]
            filtered_count = total_apps - final_accessible
            if filtered_count > 0:
                self.parent.parent.after(0, lambda acc=final_accessible, flt=filtered_count:
                                         self.parent.update_status(
                                             f"已加载 {acc} 个可访问应用（已过滤 {flt} 个无法访问的应用）"))
            else:
                self.parent.parent.after(0, lambda acc=final_accessible:
                                         self.parent.update_status(f"已加载 {acc} 个应用"))

            self.parent.parent.after(0, self._update_app_combo, app_list)

        except Exception as e:
            error_msg = str(e)
            self.parent.parent.after(0, lambda msg=error_msg:
                                     messagebox.showerror("错误", f"加载应用列表失败: {msg}"))
            self.parent.parent.after(0, lambda msg=error_msg:
                                     self.parent.update_status(f"错误: {msg}"))

    def _update_app_combo(self, app_list):
        """更新应用下拉框

        Args:
            app_list: 应用列表
        """
        if not app_list:
            self.parent.app_combo['values'] = ["未找到可访问的应用"]
            self.parent.app_combo.current(0)
            self.parent.update_status("未找到可访问的应用")
            return

        self.parent.app_combo['values'] = app_list
        self.parent.app_combo.current(0)
        # 自动加载第一个应用（列表中的应用都已验证可访问）
        self.on_app_selected(None)

    def on_app_selected(self, event):
        """应用选择事件处理

        Args:
            event: tkinter事件对象
        """
        if not self.parent.has_dependency:
            return

        app_display = self.parent.app_combo.get()
        if app_display not in self.app_map:
            return

        self.parent.current_app_id = self.app_map[app_display]['bundle_id']
        self.parent.update_status(f"正在连接应用沙盒: {self.parent.current_app_id}")

        # 通知父标签页加载沙盒文件
        if hasattr(self.parent, 'file_browser'):
            import threading
            threading.Thread(target=self.parent.file_browser.load_sandbox_async, daemon=True).start()

    def get_current_app_id(self):
        """获取当前选择的应用ID

        Returns:
            str: 应用Bundle ID，如果未选择则返回None
        """
        return self.parent.current_app_id

    def get_app_info(self, app_display_name):
        """获取应用信息

        Args:
            app_display_name: 应用显示名称

        Returns:
            dict: 应用信息字典，如果不存在则返回None
        """
        return self.app_map.get(app_display_name)
