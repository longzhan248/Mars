#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iOS设备管理模块
负责设备列表的刷新、选择和管理
"""

from tkinter import messagebox


class DeviceManager:
    """iOS设备管理器"""

    def __init__(self, parent_tab):
        """初始化设备管理器

        Args:
            parent_tab: 父标签页对象，用于访问UI组件和状态
        """
        self.parent = parent_tab
        self.device_map = {}  # 设备名称到UDID的映射

    def refresh_devices(self):
        """刷新设备列表"""
        if not self.parent.has_dependency:
            return

        try:
            from pymobiledevice3.lockdown import create_using_usbmux
            from pymobiledevice3.usbmux import list_devices

            devices = list_devices()
            if not devices:
                self.parent.device_combo['values'] = ["未检测到设备"]
                self.parent.device_combo.current(0)
                self.parent.update_status("未检测到iOS设备")
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

            self.parent.device_combo['values'] = device_list
            if device_list:
                self.parent.device_combo.current(0)
                self.on_device_selected(None)

        except Exception as e:
            messagebox.showerror("错误", f"刷新设备列表失败: {str(e)}")
            self.parent.update_status(f"错误: {str(e)}")

    def on_device_selected(self, event):
        """设备选择事件处理

        Args:
            event: tkinter事件对象
        """
        if not self.parent.has_dependency:
            return

        device_name = self.parent.device_combo.get()
        if device_name not in self.device_map:
            return

        self.parent.device_id = self.device_map[device_name]
        self.parent.update_status(f"已选择设备: {self.parent.device_id[:8]}...")

        # 通知父标签页加载应用列表
        if hasattr(self.parent, 'app_mgr'):
            import threading
            threading.Thread(target=self.parent.app_mgr.load_apps_async, daemon=True).start()

    def get_device_id(self):
        """获取当前选择的设备ID

        Returns:
            str: 设备UDID，如果未选择则返回None
        """
        return self.parent.device_id
