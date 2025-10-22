"""
聊天面板UI组件
提供对话显示、输入和管理功能
"""

import tkinter as tk
from tkinter import scrolledtext, ttk, filedialog, messagebox
from datetime import datetime
import re


class ChatPanel(ttk.Frame):
    """聊天显示和输入面板"""

    def __init__(self, parent, panel):
        """
        初始化聊天面板

        Args:
            parent: 父容器
            panel: AIAssistantPanel实例（用于访问主应用）
        """
        super().__init__(parent)
        self.panel = panel
        self.chat_text = None
        self.question_var = None
        self.search_var = None
        self.search_result_var = None

        self.create_widgets()

    def create_widgets(self):
        """创建聊天UI"""
        # 对话历史区域
        chat_frame = ttk.LabelFrame(self, text="对话历史", padding="5")
        chat_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        # 搜索框区域
        search_frame = ttk.Frame(chat_frame)
        search_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(search_frame, text="🔍").pack(side=tk.LEFT, padx=(0, 2))

        self.search_var = tk.StringVar()
        self.search_var.trace_add('write', lambda *args: self.search_chat())
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))

        # 清除搜索按钮
        ttk.Button(
            search_frame,
            text="×",
            width=3,
            command=self.clear_search
        ).pack(side=tk.LEFT, padx=(0, 2))

        # 搜索结果计数
        self.search_result_var = tk.StringVar(value="")
        ttk.Label(
            search_frame,
            textvariable=self.search_result_var,
            font=("Arial", 9),
            foreground="#666666"
        ).pack(side=tk.LEFT)

        # 对话显示区域（使用ScrolledText）
        self.chat_text = scrolledtext.ScrolledText(
            chat_frame,
            wrap=tk.WORD,
            width=50,
            height=20,
            state=tk.DISABLED,
            font=("Arial", 11)
        )
        self.chat_text.pack(fill=tk.BOTH, expand=True)

        # 配置文本标签
        self.chat_text.tag_config("user", foreground="#0066CC", font=("Arial", 11, "bold"))
        self.chat_text.tag_config("assistant", foreground="#2E7D32", font=("Arial", 11, "bold"))
        self.chat_text.tag_config("system", foreground="#FF6B35", font=("Arial", 11, "italic"))
        self.chat_text.tag_config("timestamp", foreground="#666666", font=("Arial", 9))
        self.chat_text.tag_config("content", foreground="#000000", font=("Arial", 11))
        self.chat_text.tag_config("search_highlight", background="#FFFF00")  # 黄色高亮

        # 问题输入区域
        input_frame = ttk.Frame(self)
        input_frame.pack(fill=tk.X)

        ttk.Label(input_frame, text="问题:").pack(side=tk.LEFT, padx=(0, 5))

        self.question_var = tk.StringVar()
        question_entry = ttk.Entry(input_frame, textvariable=self.question_var)
        question_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        question_entry.bind('<Return>', lambda e: self.panel.ask_question())

        # 自定义Prompt快捷按钮
        ttk.Button(
            input_frame,
            text="📝▼",
            width=4,
            command=self.panel.show_prompt_selector
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            input_frame,
            text="发送",
            command=self.panel.ask_question
        ).pack(side=tk.LEFT)

    def append_chat(self, role: str, message: str):
        """
        添加对话到历史（增强版：支持日志跳转）

        Args:
            role: 角色（"user", "assistant", "system"）
            message: 消息内容
        """
        timestamp = datetime.now().strftime("%H:%M:%S")

        self.panel.chat_history.append({
            'role': role,
            'message': message,
            'timestamp': timestamp
        })

        # 更新UI
        self.chat_text.config(state=tk.NORMAL)

        # 添加时间戳
        self.chat_text.insert(tk.END, f"[{timestamp}] ", "timestamp")

        # 添加角色标签
        role_labels = {
            "user": "用户",
            "assistant": "AI助手",
            "system": "系统"
        }
        label = role_labels.get(role, role)
        self.chat_text.insert(tk.END, f"{label}: ", role)

        # 解析消息中的日志引用并创建可点击链接
        if role == "assistant":
            self._insert_message_with_links(message)
        else:
            # 普通消息
            self.chat_text.insert(tk.END, f"{message}\n\n", "content")

        self.chat_text.config(state=tk.DISABLED)
        self.chat_text.see(tk.END)  # 滚动到底部

    def _insert_message_with_links(self, message: str):
        """
        插入带日志跳转链接的消息

        支持的格式：
        - [时间戳]: [2025-09-21 13:09:49]
        - #行号: #123
        - @模块名: @NetworkModule
        """
        # 定义所有匹配模式（优先级从高到低）
        patterns = [
            # 时间戳格式: [2025-09-21 13:09:49] 或 [2025-09-21 +8.0 13:09:49.038]
            (r'\[([\d\-: +\.]+)\]', 'timestamp'),
            # 行号格式: #123
            (r'#(\d+)', 'line_number'),
            # 模块名格式: @ModuleName (支持中英文、下划线、数字)
            (r'@([\w\u4e00-\u9fa5]+)', 'module_name')
        ]

        # 收集所有匹配项
        all_matches = []
        for pattern, link_type in patterns:
            for match in re.finditer(pattern, message):
                all_matches.append({
                    'start': match.start(),
                    'end': match.end(),
                    'type': link_type,
                    'value': match.group(1),
                    'display': match.group(0)
                })

        # 按位置排序并去重（重叠部分保留第一个）
        all_matches.sort(key=lambda x: x['start'])
        filtered_matches = []
        last_end = 0
        for match in all_matches:
            if match['start'] >= last_end:
                filtered_matches.append(match)
                last_end = match['end']

        # 构建parts列表
        parts = []
        last_end = 0

        for match in filtered_matches:
            # 添加匹配前的文本
            if match['start'] > last_end:
                parts.append(('text', message[last_end:match['start']]))

            # 添加链接
            parts.append(('link', match['type'], match['value'], match['display']))
            last_end = match['end']

        # 添加剩余文本
        if last_end < len(message):
            parts.append(('text', message[last_end:]))

        # 插入到Text组件
        for part in parts:
            if part[0] == 'text':
                self.chat_text.insert(tk.END, part[1], "content")
            elif part[0] == 'link':
                link_type, value, display_text = part[1], part[2], part[3]

                # 创建唯一tag
                tag_name = f"link_{id(part)}"

                # 插入链接文本
                self.chat_text.insert(tk.END, display_text, ("content", "log_link", tag_name))

                # 根据链接类型绑定不同的点击事件
                if link_type == 'timestamp':
                    self.chat_text.tag_bind(
                        tag_name,
                        "<Button-1>",
                        lambda e, ts=value: self.panel.navigation.jump_to_timestamp(ts)
                    )
                elif link_type == 'line_number':
                    self.chat_text.tag_bind(
                        tag_name,
                        "<Button-1>",
                        lambda e, ln=value: self.panel.navigation.jump_to_line_number(ln)
                    )
                elif link_type == 'module_name':
                    self.chat_text.tag_bind(
                        tag_name,
                        "<Button-1>",
                        lambda e, mn=value: self.panel.navigation.jump_to_module(mn)
                    )

                # 设置链接样式
                self.chat_text.tag_config(tag_name,
                    foreground="#0066CC",
                    underline=True,
                    font=("Arial", 11, "bold"))

                # 设置鼠标悬停效果
                if link_type == 'timestamp':
                    self.chat_text.tag_bind(tag_name, "<Enter>",
                        lambda e, tag=tag_name, ts=value: self.panel.navigation.show_preview(e, ts, 'timestamp'))
                elif link_type == 'line_number':
                    self.chat_text.tag_bind(tag_name, "<Enter>",
                        lambda e, tag=tag_name, ln=value: self.panel.navigation.show_preview(e, ln, 'line_number'))
                elif link_type == 'module_name':
                    self.chat_text.tag_bind(tag_name, "<Enter>",
                        lambda e, tag=tag_name, mn=value: self.panel.navigation.show_preview(e, mn, 'module_name'))

                self.chat_text.tag_bind(tag_name, "<Leave>",
                    lambda e: self.panel.navigation.hide_preview())

        self.chat_text.insert(tk.END, "\n\n")

    def clear_chat(self):
        """清空对话历史"""
        self.panel.chat_history = []
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.delete('1.0', tk.END)
        self.chat_text.config(state=tk.DISABLED)

        # 重置Token统计
        self.panel.total_input_tokens = 0
        self.panel.total_output_tokens = 0

    def export_chat(self):
        """导出对话历史"""
        if not self.panel.chat_history:
            messagebox.showinfo("提示", "对话历史为空，无需导出")
            return

        # 弹出文件保存对话框
        filename = filedialog.asksaveasfilename(
            title="导出对话历史",
            defaultextension=".md",
            filetypes=[
                ("Markdown文件", "*.md"),
                ("文本文件", "*.txt"),
                ("所有文件", "*.*")
            ]
        )

        if not filename:
            return

        try:
            # 判断文件格式
            is_markdown = filename.endswith('.md')

            if is_markdown:
                content = self._export_as_markdown()
            else:
                content = self._export_as_text()

            # 写入文件
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)

            messagebox.showinfo("成功", f"对话历史已导出到:\n{filename}")

        except Exception as e:
            messagebox.showerror("导出失败", f"无法导出对话历史:\n{str(e)}")

    def _export_as_markdown(self) -> str:
        """导出为Markdown格式"""
        lines = []
        lines.append("# AI助手对话历史\n")
        lines.append(f"## 导出时间\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        lines.append("## 对话记录\n")

        role_names = {
            "user": "用户",
            "assistant": "AI助手",
            "system": "系统"
        }

        for chat in self.panel.chat_history:
            role = role_names.get(chat['role'], chat['role'])
            lines.append(f"### [{chat['timestamp']}] {role}\n")
            lines.append(f"{chat['message']}\n")

        return '\n'.join(lines)

    def _export_as_text(self) -> str:
        """导出为纯文本格式"""
        lines = []
        lines.append("AI助手对话历史")
        lines.append(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 50)
        lines.append("")

        role_names = {
            "user": "用户",
            "assistant": "AI助手",
            "system": "系统"
        }

        for chat in self.panel.chat_history:
            role = role_names.get(chat['role'], chat['role'])
            lines.append(f"[{chat['timestamp']}] {role}: {chat['message']}")
            lines.append("")

        return '\n'.join(lines)

    def search_chat(self):
        """搜索对话历史"""
        keyword = self.search_var.get().strip()

        # 移除之前的高亮
        self.chat_text.tag_remove("search_highlight", "1.0", tk.END)

        if not keyword:
            self.search_result_var.set("")
            return

        # 搜索并高亮
        match_count = 0
        start_pos = "1.0"

        while True:
            # 不区分大小写搜索
            pos = self.chat_text.search(
                keyword,
                start_pos,
                tk.END,
                nocase=True
            )

            if not pos:
                break

            # 计算匹配文本的结束位置
            end_pos = f"{pos}+{len(keyword)}c"

            # 添加高亮标签
            self.chat_text.tag_add("search_highlight", pos, end_pos)

            match_count += 1
            start_pos = end_pos

        # 更新搜索结果计数
        if match_count > 0:
            self.search_result_var.set(f"找到 {match_count} 处")

            # 滚动到第一个匹配位置
            first_match = self.chat_text.search(
                keyword,
                "1.0",
                tk.END,
                nocase=True
            )
            if first_match:
                self.chat_text.see(first_match)
        else:
            self.search_result_var.set("无匹配")

    def clear_search(self):
        """清除搜索"""
        self.search_var.set("")
        self.chat_text.tag_remove("search_highlight", "1.0", tk.END)
        self.search_result_var.set("")
