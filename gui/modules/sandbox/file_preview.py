#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件预览模块
负责各种文件类型的预览显示
"""

import os
import re
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


class FilePreview:
    """文件预览管理器"""

    def __init__(self, parent_tab):
        """初始化文件预览管理器

        Args:
            parent_tab: 父标签页对象
        """
        self.parent = parent_tab

    def preview_selected(self):
        """预览选中的文件"""
        item = self.parent.tree.selection()
        if not item:
            messagebox.showwarning("提示", "请先选择要预览的文件")
            return

        item_id = item[0]
        tags = self.parent.tree.item(item_id, "tags")

        if "placeholder" in tags:
            messagebox.showwarning("提示", "请先展开目录")
            return

        if "directory" in tags:
            messagebox.showinfo("提示", "无法预览目录")
            return

        path = self.parent.tree.set(item_id, "path")
        if not path:
            messagebox.showwarning("提示", "无效的文件路径")
            return

        # 清理文件名
        name = self.parent.tree.item(item_id, "text").replace("📄 ", "")
        if "search_result" in tags:
            name = re.sub(r'\s*\[.*?\]$', '', name)

        threading.Thread(target=self._preview_file_async, args=(path, name), daemon=True).start()

    def _preview_file_async(self, remote_path, filename):
        """异步预览文件"""
        try:
            self.parent.parent.after(0, lambda path=remote_path:
                                     self.parent.update_status(f"正在加载: {path}"))

            # 使用 get_file_contents 读取文件，失败时尝试重新连接
            try:
                data = self.parent.afc_client.get_file_contents(remote_path)
            except Exception as e:
                # 判断是否需要重新连接
                error_type = type(e).__name__
                error_str = str(e).lower()

                # 需要重连的错误类型：
                # 1. AFC状态错误（magic/parsing）
                # 2. 连接中断错误（ConnectionAbortedError/ConnectionTerminatedError）
                # 3. Const错误（ConstError）
                should_reconnect = (
                    "magic" in error_str or
                    "parsing" in error_str or
                    "connectionaborted" in error_type.lower() or
                    "connectionterminated" in error_type.lower() or
                    "consterror" in error_type.lower() or
                    "connection" in error_str
                )

                if should_reconnect:
                    # 连接已断开，重新加载应用（会刷新整个UI）
                    info_msg = (
                        "连接已断开，正在自动重新加载...\n\n"
                        "文件树将被刷新（目录会折叠）"
                    )
                    self.parent.parent.after(0, lambda msg=info_msg:
                        messagebox.showinfo("提示", msg))

                    # 重新加载整个沙盒（会重建连接并刷新UI）
                    if hasattr(self.parent, 'file_browser'):
                        threading.Thread(target=self.parent.file_browser.load_sandbox_async, daemon=True).start()
                        self.parent.parent.after(0, lambda:
                            self.parent.update_status("已重新加载应用"))

                    return
                else:
                    raise

            file_ext = os.path.splitext(filename)[1].lower()

            # 文本文件
            if file_ext in ['.txt', '.log', '.json', '.xml', '.plist', '.html', '.css', '.js',
                           '.py', '.md', '.sh', '.h', '.m', '.swift', '.c', '.cpp']:
                try:
                    text_content = data.decode('utf-8')
                    self.parent.parent.after(0, lambda name=filename, content=text_content:
                                             self._show_text_preview(name, content))
                except:
                    try:
                        text_content = data.decode('gbk')
                        self.parent.parent.after(0, lambda name=filename, content=text_content:
                                                 self._show_text_preview(name, content))
                    except:
                        self.parent.parent.after(0, lambda:
                                                 messagebox.showwarning("提示", "无法解码文本文件"))
                        return
            # 图片文件
            elif file_ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico']:
                self.parent.parent.after(0, lambda name=filename, img_data=data:
                                         self._show_image_preview(name, img_data))
            # 数据库文件
            elif file_ext in ['.db', '.sqlite', '.sqlite3']:
                self.parent.parent.after(0, lambda name=filename, size=len(data):
                    messagebox.showinfo("提示", f"SQLite数据库文件\n文件名: {name}\n大小: {size} 字节\n\n建议导出后使用专业工具查看"))
            # 其他文件显示十六进制
            else:
                hex_preview = self._format_hex(data[:512])
                self.parent.parent.after(0, lambda name=filename, content=hex_preview, size=len(data):
                                         self._show_hex_preview(name, content, size))

            self.parent.parent.after(0, lambda: self.parent.update_status("预览完成"))

        except Exception as e:
            error_msg = str(e)
            self.parent.parent.after(0, lambda msg=error_msg:
                                     messagebox.showerror("错误", f"预览失败: {msg}"))
            self.parent.parent.after(0, lambda msg=error_msg:
                                     self.parent.update_status(f"预览失败: {msg}"))

    def _show_text_preview(self, filename, content):
        """显示文本预览"""
        preview_window = tk.Toplevel(self.parent.parent)
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
            import io

            from PIL import Image, ImageTk

            preview_window = tk.Toplevel(self.parent.parent)
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
        preview_window = tk.Toplevel(self.parent.parent)
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
