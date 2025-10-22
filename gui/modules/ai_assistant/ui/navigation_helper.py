"""
日志导航辅助类
提供日志跳转、预览和历史导航功能
"""

import tkinter as tk
from tkinter import ttk


class NavigationHelper:
    """日志导航辅助类"""

    def __init__(self, panel):
        self.panel = panel
        self.jump_history = []
        self.jump_history_index = -1
        self.preview_window = None

    def jump_to_log(self, log_index: int, add_to_history: bool = True):
        """
        跳转到指定日志并高亮显示

        Args:
            log_index: 日志索引
            add_to_history: 是否添加到历史记录
        """
        try:
            # 验证索引范围
            if log_index < 0 or log_index >= len(self.panel.main_app.log_entries):
                self.panel.set_status(f"日志索引超出范围: {log_index}")
                return

            # 添加到历史记录
            if add_to_history:
                # 如果当前不是在历史末尾，删除后面的历史
                if self.jump_history_index < len(self.jump_history) - 1:
                    self.jump_history = self.jump_history[:self.jump_history_index + 1]

                # 添加新记录
                self.jump_history.append(log_index)
                self.jump_history_index = len(self.jump_history) - 1

                # 更新按钮状态
                self._update_jump_buttons()

            # 切换到"全部日志"标签页（假设是第一个）
            if hasattr(self.panel.main_app, 'notebook'):
                try:
                    self.panel.main_app.notebook.select(0)
                except:
                    pass

            # 在日志列表中选中该行
            if hasattr(self.panel.main_app, 'log_text'):
                text_widget = self.panel.main_app.log_text

                # 计算行号（从1开始）
                line_num = log_index + 1

                # 滚动到目标行
                text_widget.see(f"{line_num}.0")

                # 清除之前的选择
                text_widget.tag_remove("sel", "1.0", tk.END)

                # 选中目标行
                text_widget.tag_add("sel", f"{line_num}.0", f"{line_num}.end")

                # 应用渐变高亮动画
                self._animate_highlight(text_widget, line_num)

            # 更新状态
            entry = self.panel.main_app.log_entries[log_index]
            self.panel.set_status(f"已跳转到第 {log_index + 1} 行: [{entry.level}] {entry.content[:50]}...")

        except Exception as e:
            print(f"跳转失败: {str(e)}")
            self.panel.set_status(f"跳转失败: {str(e)}")

    def jump_to_timestamp(self, timestamp: str):
        """
        根据时间戳跳转到日志并高亮

        Args:
            timestamp: 日志时间戳
        """
        try:
            # 在日志列表中查找匹配的时间戳
            log_index = None
            for i, entry in enumerate(self.panel.main_app.log_entries):
                if entry.timestamp == timestamp:
                    log_index = i
                    break

            if log_index is None:
                # 尝试模糊匹配（去除时区、毫秒等）
                timestamp_short = timestamp.split('.')[0].split('+')[0].strip()
                for i, entry in enumerate(self.panel.main_app.log_entries):
                    if entry.timestamp and entry.timestamp.startswith(timestamp_short):
                        log_index = i
                        break

            if log_index is not None:
                self.jump_to_log(log_index)
            else:
                self.panel.set_status(f"未找到时间戳为 {timestamp} 的日志")

        except Exception as e:
            print(f"跳转失败: {str(e)}")
            self.panel.set_status(f"跳转失败: {str(e)}")

    def jump_to_line_number(self, line_number: str):
        """
        根据行号跳转到日志

        Args:
            line_number: 行号字符串（如"123"）
        """
        try:
            # 转换为整数（行号从1开始，索引从0开始）
            log_index = int(line_number) - 1

            # 验证行号范围
            if log_index < 0 or log_index >= len(self.panel.main_app.log_entries):
                self.panel.set_status(f"行号 #{line_number} 超出范围（1-{len(self.panel.main_app.log_entries)}）")
                return

            # 调用通用跳转方法
            self.jump_to_log(log_index)

        except ValueError:
            self.panel.set_status(f"无效的行号: #{line_number}")
        except Exception as e:
            print(f"行号跳转失败: {str(e)}")
            self.panel.set_status(f"行号跳转失败: {str(e)}")

    def jump_to_module(self, module_name: str):
        """
        根据模块名跳转到该模块的第一条日志

        Args:
            module_name: 模块名（如"NetworkModule"）
        """
        try:
            # 查找该模块的第一条日志
            log_index = None
            for i, entry in enumerate(self.panel.main_app.log_entries):
                if entry.module == module_name:
                    log_index = i
                    break

            if log_index is not None:
                # 切换到模块分组标签页
                if hasattr(self.panel.main_app, 'notebook'):
                    # 假设模块分组是第2个标签页（索引为1）
                    try:
                        self.panel.main_app.notebook.select(1)
                    except:
                        pass

                # 如果有模块列表，尝试选中该模块
                if hasattr(self.panel.main_app, 'module_listbox'):
                    # 查找模块在列表中的位置
                    for idx in range(self.panel.main_app.module_listbox.size()):
                        item_text = self.panel.main_app.module_listbox.get(idx)
                        if module_name in item_text:
                            self.panel.main_app.module_listbox.selection_clear(0, tk.END)
                            self.panel.main_app.module_listbox.selection_set(idx)
                            self.panel.main_app.module_listbox.see(idx)
                            # 触发选择事件
                            if hasattr(self.panel.main_app, 'on_module_select'):
                                self.panel.main_app.on_module_select(None)
                            break

                self.panel.set_status(f"已跳转到模块 @{module_name} 的第一条日志（第 {log_index + 1} 行）")
            else:
                self.panel.set_status(f"未找到模块 @{module_name} 的日志")

        except Exception as e:
            print(f"模块跳转失败: {str(e)}")
            self.panel.set_status(f"模块跳转失败: {str(e)}")

    def show_preview(self, event, value, link_type):
        """
        显示日志预览窗口

        Args:
            event: 鼠标事件
            value: 链接值（时间戳、行号或模块名）
            link_type: 链接类型
        """
        # 设置手型光标
        if hasattr(self.panel, 'chat_panel') and hasattr(self.panel.chat_panel, 'chat_text'):
            self.panel.chat_panel.chat_text.config(cursor="hand2")

        # 查找对应的日志
        log_index = None
        preview_lines = []

        if link_type == 'timestamp':
            # 根据时间戳查找
            for i, entry in enumerate(self.panel.main_app.log_entries):
                if entry.timestamp == value or (entry.timestamp and entry.timestamp.startswith(value.split('.')[0].split('+')[0].strip())):
                    log_index = i
                    break
        elif link_type == 'line_number':
            # 直接使用行号
            try:
                log_index = int(value) - 1
            except:
                pass
        elif link_type == 'module_name':
            # 查找模块的第一条日志
            for i, entry in enumerate(self.panel.main_app.log_entries):
                if entry.module == value:
                    log_index = i
                    break

        if log_index is not None and 0 <= log_index < len(self.panel.main_app.log_entries):
            # 获取上下文（前后各2行）
            start = max(0, log_index - 2)
            end = min(len(self.panel.main_app.log_entries), log_index + 3)

            for i in range(start, end):
                entry = self.panel.main_app.log_entries[i]
                prefix = "➤ " if i == log_index else "  "
                preview_lines.append(f"{prefix}#{i+1}: [{entry.level}] {entry.content[:80]}...")

        if preview_lines:
            # 创建预览窗口
            self.preview_window = tk.Toplevel(self.panel.main_app.root)
            self.preview_window.wm_overrideredirect(True)  # 无边框窗口
            self.preview_window.wm_attributes("-topmost", True)  # 置顶

            # 设置窗口位置（鼠标附近）
            x = event.x_root + 10
            y = event.y_root + 10
            self.preview_window.wm_geometry(f"+{x}+{y}")

            # 创建预览内容
            preview_frame = tk.Frame(self.preview_window, bg="#FFFFCC", relief=tk.SOLID, borderwidth=1)
            preview_frame.pack()

            preview_text = tk.Text(
                preview_frame,
                wrap=tk.WORD,
                width=80,
                height=len(preview_lines),
                font=("Monaco", 9),
                bg="#FFFFCC",
                fg="#000000",
                relief=tk.FLAT
            )
            preview_text.pack(padx=5, pady=5)

            # 插入预览内容
            for line in preview_lines:
                if line.startswith("➤"):
                    preview_text.insert(tk.END, line + "\n", "highlight")
                else:
                    preview_text.insert(tk.END, line + "\n")

            # 配置高亮样式
            preview_text.tag_config("highlight", background="#FFFF99", font=("Monaco", 9, "bold"))

            preview_text.config(state=tk.DISABLED)

    def hide_preview(self):
        """隐藏日志预览窗口"""
        # 恢复默认光标
        if hasattr(self.panel, 'chat_panel') and hasattr(self.panel.chat_panel, 'chat_text'):
            self.panel.chat_panel.chat_text.config(cursor="")

        # 销毁预览窗口
        if self.preview_window:
            try:
                self.preview_window.destroy()
                self.preview_window = None
            except:
                pass

    def _animate_highlight(self, text_widget, line_num, duration=2000, steps=20):
        """
        渐变高亮动画

        Args:
            text_widget: 文本组件
            line_num: 行号
            duration: 动画总时长（毫秒）
            steps: 动画步数
        """
        # 高亮颜色（从亮黄色渐变到无色）
        colors = [
            "#FFFF00",  # 亮黄色
            "#FFFF33",
            "#FFFF66",
            "#FFFF99",
            "#FFFFCC",
            "#FFFFEE",
            "#FFFFFF",  # 白色（透明）
        ]

        interval = duration // len(colors)

        def apply_color(index):
            """应用渐变高亮颜色的递归函数"""
            if index < len(colors):
                # 配置当前颜色
                text_widget.tag_config("ai_highlight",
                    background=colors[index],
                    foreground="#000000")

                # 添加/更新高亮
                text_widget.tag_remove("ai_highlight", "1.0", "end")
                text_widget.tag_add("ai_highlight", f"{line_num}.0", f"{line_num}.end")

                # 调度下一步
                self.panel.main_app.root.after(interval, lambda: apply_color(index + 1))
            else:
                # 动画结束，移除高亮
                text_widget.tag_remove("ai_highlight", "1.0", "end")

        # 开始动画
        apply_color(0)

    def _update_jump_buttons(self):
        """更新前进/后退按钮的状态"""
        # 更新后退按钮
        back_enabled = self.jump_history_index > 0
        forward_enabled = self.jump_history_index < len(self.jump_history) - 1

        # 委托给toolbar更新按钮状态
        if hasattr(self.panel, 'toolbar'):
            self.panel.toolbar.update_navigation_buttons(back_enabled, forward_enabled)

    def jump_back(self):
        """后退到历史中的上一个位置"""
        if self.jump_history_index > 0:
            self.jump_history_index -= 1
            log_index = self.jump_history[self.jump_history_index]

            # 跳转（不添加到历史）
            self.jump_to_log(log_index, add_to_history=False)

            # 更新按钮状态
            self._update_jump_buttons()

            # 更新状态
            self.panel.set_status(f"后退到第 {log_index + 1} 行 (历史 {self.jump_history_index + 1}/{len(self.jump_history)})")

    def jump_forward(self):
        """前进到历史中的下一个位置"""
        if self.jump_history_index < len(self.jump_history) - 1:
            self.jump_history_index += 1
            log_index = self.jump_history[self.jump_history_index]

            # 跳转（不添加到历史）
            self.jump_to_log(log_index, add_to_history=False)

            # 更新按钮状态
            self._update_jump_buttons()

            # 更新状态
            self.panel.set_status(f"前进到第 {log_index + 1} 行 (历史 {self.jump_history_index + 1}/{len(self.jump_history)})")
