#!/usr/bin/env python3
"""
iOS APNS推送GUI界面
集成到mars_log_analyzer项目的推送测试工具
"""

import json
import os
import sys
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk
from typing import Optional

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from apns_push import APNSManager


class APNSPushGUI(ttk.Frame):
    """iOS推送测试GUI界面"""

    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.parent = parent
        self.manager = APNSManager()
        self.current_cert_path = None
        self.setup_ui()
        self.load_saved_data()

    def setup_ui(self):
        """设置UI界面"""
        self.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 主框架
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 左侧面板 - 配置区域
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # 右侧面板 - 日志区域
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # === 左侧配置区域 ===

        # 证书选择区域
        cert_frame = ttk.LabelFrame(left_frame, text="推送证书", padding=10)
        cert_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(cert_frame, text="证书文件:").grid(row=0, column=0, sticky=tk.W)

        self.cert_path_var = tk.StringVar()
        cert_entry = ttk.Entry(cert_frame, textvariable=self.cert_path_var, width=40)
        cert_entry.grid(row=0, column=1, padx=5)

        ttk.Button(
            cert_frame, text="浏览...",
            command=self.browse_certificate
        ).grid(row=0, column=2)

        ttk.Label(cert_frame, text="密码:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.cert_password_var = tk.StringVar()
        ttk.Entry(
            cert_frame, textvariable=self.cert_password_var,
            show="*", width=20
        ).grid(row=1, column=1, sticky=tk.W, padx=5, pady=(5, 0))

        ttk.Button(
            cert_frame, text="加载证书",
            command=self.load_certificate
        ).grid(row=1, column=2, pady=(5, 0))

        # 证书信息显示
        self.cert_info_label = ttk.Label(cert_frame, text="未加载证书", foreground="gray")
        self.cert_info_label.grid(row=2, column=0, columnspan=3, pady=(10, 0))

        # Device Token输入区域
        token_frame = ttk.LabelFrame(left_frame, text="Device Token", padding=10)
        token_frame.pack(fill=tk.X, pady=(0, 10))

        self.token_text = tk.Text(token_frame, height=3, width=50)
        self.token_text.pack(fill=tk.X)
        self.token_text.insert('1.0', '请输入Device Token...')

        # 环境选择
        env_frame = ttk.LabelFrame(left_frame, text="环境设置", padding=10)
        env_frame.pack(fill=tk.X, pady=(0, 10))

        self.environment_var = tk.StringVar(value="sandbox")
        ttk.Radiobutton(
            env_frame, text="开发环境(Sandbox)",
            variable=self.environment_var, value="sandbox"
        ).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(
            env_frame, text="生产环境(Production)",
            variable=self.environment_var, value="production"
        ).pack(side=tk.LEFT, padx=5)

        # Payload编辑区域
        payload_frame = ttk.LabelFrame(left_frame, text="推送内容(Payload)", padding=10)
        payload_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 快速模板按钮
        template_frame = ttk.Frame(payload_frame)
        template_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(template_frame, text="快速模板:").pack(side=tk.LEFT)

        ttk.Button(
            template_frame, text="简单消息",
            command=lambda: self.set_payload_template('simple')
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            template_frame, text="带角标",
            command=lambda: self.set_payload_template('badge')
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            template_frame, text="带声音",
            command=lambda: self.set_payload_template('sound')
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            template_frame, text="静默推送",
            command=lambda: self.set_payload_template('silent')
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            template_frame, text="富文本",
            command=lambda: self.set_payload_template('rich')
        ).pack(side=tk.LEFT, padx=2)

        # Payload编辑器
        self.payload_text = scrolledtext.ScrolledText(
            payload_frame, height=10, width=50,
            wrap=tk.WORD, font=('Courier', 10)
        )
        self.payload_text.pack(fill=tk.BOTH, expand=True)

        # 设置默认payload
        default_payload = {
            "aps": {
                "alert": "这是一条测试推送消息",
                "badge": 1,
                "sound": "default"
            }
        }
        self.payload_text.insert('1.0', json.dumps(default_payload, indent=2, ensure_ascii=False))

        # 高级选项
        advanced_frame = ttk.LabelFrame(left_frame, text="高级选项", padding=10)
        advanced_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(advanced_frame, text="优先级:").grid(row=0, column=0, sticky=tk.W)
        self.priority_var = tk.StringVar(value="10")
        priority_combo = ttk.Combobox(
            advanced_frame, textvariable=self.priority_var,
            values=["10 (立即)", "5 (省电)"], width=15, state="readonly"
        )
        priority_combo.grid(row=0, column=1, padx=5)

        ttk.Label(advanced_frame, text="推送类型:").grid(row=0, column=2, sticky=tk.W, padx=(20, 0))
        self.push_type_var = tk.StringVar(value="alert")
        push_type_combo = ttk.Combobox(
            advanced_frame, textvariable=self.push_type_var,
            values=["alert", "background", "voip", "complication", "fileprovider", "mdm"],
            width=15, state="readonly"
        )
        push_type_combo.grid(row=0, column=3, padx=5)

        ttk.Label(advanced_frame, text="Topic:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.topic_var = tk.StringVar()
        ttk.Entry(advanced_frame, textvariable=self.topic_var, width=40).grid(
            row=1, column=1, columnspan=3, padx=5, pady=(5, 0)
        )

        # 发送按钮
        button_frame = ttk.Frame(left_frame)
        button_frame.pack(fill=tk.X)

        self.send_button = ttk.Button(
            button_frame, text="发送推送",
            command=self.send_push, style="Accent.TButton"
        )
        self.send_button.pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame, text="验证Payload",
            command=self.validate_payload
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame, text="清空日志",
            command=self.clear_log
        ).pack(side=tk.LEFT, padx=5)

        # === 右侧日志区域 ===

        # 日志标签页
        notebook = ttk.Notebook(right_frame)
        notebook.pack(fill=tk.BOTH, expand=True)

        # 实时日志标签
        log_tab = ttk.Frame(notebook)
        notebook.add(log_tab, text="实时日志")

        self.log_text = scrolledtext.ScrolledText(
            log_tab, height=20, width=50,
            wrap=tk.WORD, font=('Courier', 9)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # 历史记录标签
        history_tab = ttk.Frame(notebook)
        notebook.add(history_tab, text="推送历史")

        # 历史记录列表
        history_frame = ttk.Frame(history_tab)
        history_frame.pack(fill=tk.BOTH, expand=True)

        # 创建Treeview
        columns = ('时间', 'Token', '状态', '消息', '环境')
        self.history_tree = ttk.Treeview(
            history_frame, columns=columns, show='headings', height=15
        )

        # 设置列
        for col in columns:
            self.history_tree.heading(col, text=col)
            if col == '时间':
                self.history_tree.column(col, width=150)
            elif col == 'Token':
                self.history_tree.column(col, width=100)
            elif col == '状态':
                self.history_tree.column(col, width=60)
            else:
                self.history_tree.column(col, width=150)

        # 滚动条
        vsb = ttk.Scrollbar(history_frame, orient="vertical", command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=vsb.set)

        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        # 历史记录按钮
        history_button_frame = ttk.Frame(history_tab)
        history_button_frame.pack(fill=tk.X, pady=5)

        ttk.Button(
            history_button_frame, text="刷新历史",
            command=self.refresh_history
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            history_button_frame, text="清除历史",
            command=self.clear_history
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            history_button_frame, text="重新发送",
            command=self.resend_from_history
        ).pack(side=tk.LEFT, padx=5)

    def browse_certificate(self):
        """浏览选择证书文件"""
        filename = filedialog.askopenfilename(
            title="选择推送证书",
            filetypes=[
                ("证书文件", "*.p12 *.pem *.cer"),
                ("P12文件", "*.p12"),
                ("PEM文件", "*.pem"),
                ("CER文件", "*.cer"),
                ("所有文件", "*.*")
            ]
        )

        if filename:
            self.cert_path_var.set(filename)
            self.log(f"选择证书: {filename}")

    def load_certificate(self):
        """加载证书"""
        cert_path = self.cert_path_var.get()
        if not cert_path:
            messagebox.showwarning("警告", "请先选择证书文件")
            return

        password = self.cert_password_var.get() or None

        try:
            # 在线程中加载证书
            self.log(f"正在加载证书: {cert_path}")

            if self.manager.load_certificate(cert_path, password):
                cert = self.manager.current_cert

                # 显示证书信息
                info_text = f"证书已加载: {self.manager.current_cert_name}\n"
                info_text += f"环境: {cert.cert_info.get('environment', 'unknown')}\n"

                if cert.cert_info.get('bundle_id'):
                    info_text += f"Bundle ID: {cert.cert_info['bundle_id']}\n"
                    # 自动设置topic
                    self.topic_var.set(cert.cert_info['bundle_id'])

                if cert.is_valid():
                    days = cert.days_until_expiry()
                    info_text += f"有效期: 还剩 {days} 天"
                    self.cert_info_label.config(text=info_text, foreground="green")
                else:
                    info_text += "证书已过期!"
                    self.cert_info_label.config(text=info_text, foreground="red")

                self.log("✅ 证书加载成功")
                self.current_cert_path = cert_path
                self.save_data()

            else:
                self.cert_info_label.config(text="证书加载失败", foreground="red")
                self.log("❌ 证书加载失败")

        except Exception as e:
            self.cert_info_label.config(text=f"错误: {str(e)}", foreground="red")
            self.log(f"❌ 加载证书出错: {str(e)}")
            messagebox.showerror("错误", f"加载证书失败:\n{str(e)}")

    def validate_payload(self):
        """验证Payload格式"""
        try:
            payload_text = self.payload_text.get('1.0', tk.END).strip()
            payload = json.loads(payload_text)

            # 格式化显示
            formatted = json.dumps(payload, indent=2, ensure_ascii=False)
            self.payload_text.delete('1.0', tk.END)
            self.payload_text.insert('1.0', formatted)

            # 检查大小
            size = len(payload_text.encode('utf-8'))
            if size > 4096:
                self.log(f"⚠️ Payload太大: {size} bytes (最大4096)")
                messagebox.showwarning("警告", f"Payload太大: {size} bytes\n最大允许4096 bytes")
            else:
                self.log(f"✅ Payload格式正确 ({size} bytes)")
                messagebox.showinfo("成功", f"Payload格式正确\n大小: {size} bytes")

        except json.JSONDecodeError as e:
            self.log(f"❌ Payload格式错误: {str(e)}")
            messagebox.showerror("错误", f"JSON格式错误:\n{str(e)}")

    def set_payload_template(self, template_type: str):
        """设置Payload模板"""
        templates = {
            'simple': {
                "aps": {
                    "alert": "这是一条简单的推送消息"
                }
            },
            'badge': {
                "aps": {
                    "alert": "您有新消息",
                    "badge": 5
                }
            },
            'sound': {
                "aps": {
                    "alert": "叮咚！您有新消息",
                    "sound": "default",
                    "badge": 1
                }
            },
            'silent': {
                "aps": {
                    "content-available": 1
                }
            },
            'rich': {
                "aps": {
                    "alert": {
                        "title": "推送标题",
                        "subtitle": "推送副标题",
                        "body": "这是推送的详细内容，可以包含更多信息。"
                    },
                    "badge": 1,
                    "sound": "default",
                    "mutable-content": 1
                },
                "custom_data": {
                    "image_url": "https://example.com/image.jpg",
                    "action": "open_detail"
                }
            }
        }

        if template_type in templates:
            payload = templates[template_type]
            self.payload_text.delete('1.0', tk.END)
            self.payload_text.insert('1.0', json.dumps(payload, indent=2, ensure_ascii=False))
            self.log(f"已设置模板: {template_type}")

    def send_push(self):
        """发送推送"""
        # 检查证书
        if not self.manager.current_cert:
            messagebox.showwarning("警告", "请先加载证书")
            return

        # 获取device token
        device_token = self.token_text.get('1.0', tk.END).strip()
        if not device_token or device_token == '请输入Device Token...':
            messagebox.showwarning("警告", "请输入Device Token")
            return

        # 获取payload
        try:
            payload_text = self.payload_text.get('1.0', tk.END).strip()
            payload = json.loads(payload_text)
        except json.JSONDecodeError as e:
            messagebox.showerror("错误", f"Payload格式错误:\n{str(e)}")
            return

        # 获取配置
        sandbox = self.environment_var.get() == 'sandbox'
        priority = int(self.priority_var.get().split()[0])
        push_type = self.push_type_var.get()
        topic = self.topic_var.get() or None

        # 禁用发送按钮
        self.send_button.config(state='disabled', text='发送中...')

        # 在线程中发送
        def send_thread():
            try:
                self.log(f"正在发送推送到: {device_token[:10]}...")
                self.log(f"环境: {'Sandbox' if sandbox else 'Production'}")

                success, error = self.manager.send_custom_payload(
                    device_token,
                    payload,
                    sandbox=sandbox,
                    priority=priority,
                    push_type=push_type,
                    topic=topic
                )

                # 更新UI
                self.parent.after(0, self._handle_send_result, success, error)

            except Exception as e:
                self.parent.after(0, self._handle_send_result, False, str(e))

        threading.Thread(target=send_thread, daemon=True).start()

    def _handle_send_result(self, success: bool, error: Optional[str]):
        """处理发送结果"""
        self.send_button.config(state='normal', text='发送推送')

        if success:
            self.log("✅ 推送发送成功!")
            messagebox.showinfo("成功", "推送发送成功!")
        else:
            self.log(f"❌ 推送发送失败: {error}")
            messagebox.showerror("失败", f"推送发送失败:\n{error}")

        # 刷新历史记录
        self.refresh_history()

    def refresh_history(self):
        """刷新历史记录"""
        # 清空现有记录
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)

        # 获取历史记录
        history = self.manager.get_history(50)

        # 添加到列表
        for record in reversed(history):
            timestamp = record['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
            token_short = record['device_token'][:10] + '...' if len(record['device_token']) > 10 else record['device_token']
            status = '✅' if record['success'] else '❌'

            # 提取消息内容
            payload = record['payload']
            message = ''
            if isinstance(payload, dict):
                aps = payload.get('aps', {})
                if isinstance(aps.get('alert'), str):
                    message = aps['alert']
                elif isinstance(aps.get('alert'), dict):
                    message = aps['alert'].get('body', aps['alert'].get('title', ''))

            environment = 'Sandbox' if record['sandbox'] else 'Production'

            self.history_tree.insert('', 'end', values=(
                timestamp, token_short, status, message, environment
            ))

    def resend_from_history(self):
        """从历史记录重新发送"""
        selected = self.history_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请选择要重新发送的记录")
            return

        # TODO: 实现从历史记录重新发送功能
        # 需要从历史记录中获取完整数据（device_token, payload, environment等）
        # 简化处理，提示用户手动复制
        messagebox.showinfo("提示", "请手动复制历史记录中的数据到输入框")

    def clear_history(self):
        """清除历史记录"""
        if messagebox.askyesno("确认", "确定要清除所有推送历史记录吗？"):
            self.manager.history.clear_all()
            self.refresh_history()
            self.log("已清除所有历史记录")

    def clear_log(self):
        """清空日志"""
        self.log_text.delete('1.0', tk.END)

    def log(self, message: str):
        """记录日志"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)

    def save_data(self):
        """保存配置数据"""
        try:
            config = {
                'cert_path': self.cert_path_var.get(),
                'device_token': self.token_text.get('1.0', tk.END).strip(),
                'payload': self.payload_text.get('1.0', tk.END).strip(),
                'environment': self.environment_var.get(),
                'priority': self.priority_var.get(),
                'push_type': self.push_type_var.get(),
                'topic': self.topic_var.get()
            }

            config_file = Path.home() / '.apns_gui_config.json'
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)

        except Exception as e:
            print(f"保存配置失败: {e}")

    def load_saved_data(self):
        """加载保存的配置"""
        try:
            config_file = Path.home() / '.apns_gui_config.json'
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = json.load(f)

                self.cert_path_var.set(config.get('cert_path', ''))

                token = config.get('device_token', '')
                if token and token != '请输入Device Token...':
                    self.token_text.delete('1.0', tk.END)
                    self.token_text.insert('1.0', token)

                payload = config.get('payload', '')
                if payload:
                    self.payload_text.delete('1.0', tk.END)
                    self.payload_text.insert('1.0', payload)

                self.environment_var.set(config.get('environment', 'sandbox'))
                self.priority_var.set(config.get('priority', '10'))
                self.push_type_var.set(config.get('push_type', 'alert'))
                self.topic_var.set(config.get('topic', ''))

                self.log("已加载上次的配置")

        except Exception as e:
            print(f"加载配置失败: {e}")


def create_standalone_window():
    """创建独立窗口"""
    root = tk.Tk()
    root.title("iOS推送测试工具")
    root.geometry("1200x700")

    # 设置样式
    style = ttk.Style()
    style.theme_use('clam')

    # 创建GUI（必须保留引用以防止垃圾回收）
    _app = APNSPushGUI(root)

    # 居中窗口
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")

    return root


if __name__ == '__main__':
    root = create_standalone_window()
    root.mainloop()