#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""测试ImprovedLazyText的标签方法"""

import tkinter as tk
from improved_lazy_text import ImprovedLazyText

def test_tag_methods():
    """测试标签相关方法"""
    root = tk.Tk()
    root.title("测试标签方法")
    root.geometry("600x400")

    # 创建ImprovedLazyText
    text_widget = ImprovedLazyText(root)
    text_widget.pack(fill=tk.BOTH, expand=True)

    # 设置测试数据
    test_data = [
        ("这是INFO级别的日志\n", "INFO"),
        ("这是ERROR级别的日志\n", "ERROR"),
        ("这是WARNING级别的日志\n", "WARNING"),
        ("这是包含keyword的日志\n", "INFO"),
        ("这是CRASH级别的日志\n", "CRASH"),
    ]

    # 配置标签样式
    try:
        text_widget.tag_config("INFO", foreground="blue")
        text_widget.tag_config("ERROR", foreground="red", font=("Courier", 12, "bold"))
        text_widget.tag_config("WARNING", foreground="orange")
        text_widget.tag_config("CRASH", foreground="white", background="darkred")
        text_widget.tag_config("HIGHLIGHT", background="yellow")
        print("✅ tag_config方法正常")
    except AttributeError as e:
        print(f"❌ tag_config方法错误: {e}")
        return

    # 设置数据
    text_widget.set_data(test_data)

    # 测试搜索和高亮
    def test_search_highlight():
        keyword = "keyword"
        try:
            # 搜索关键词
            start_idx = "1.0"
            pos = text_widget.search(keyword, start_idx, tk.END, nocase=True)
            if pos:
                end_idx = f"{pos}+{len(keyword)}c"
                # 添加高亮标签
                text_widget.tag_add("HIGHLIGHT", pos, end_idx)
                print("✅ search和tag_add方法正常")
            else:
                print("未找到关键词")
        except AttributeError as e:
            print(f"❌ search或tag_add方法错误: {e}")

    # 添加测试按钮
    test_button = tk.Button(root, text="测试搜索高亮", command=test_search_highlight)
    test_button.pack(pady=5)

    # 显示测试信息
    info_label = tk.Label(root, text="点击按钮测试搜索和高亮功能")
    info_label.pack()

    root.mainloop()

if __name__ == "__main__":
    print("===== 测试ImprovedLazyText标签方法 =====")
    test_tag_methods()