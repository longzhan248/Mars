#!/usr/bin/env python3
"""
测试GUI中的IPS解析功能
"""

import tkinter as tk
from tkinter import messagebox
import os
import sys

# 确保能导入主程序
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_gui():
    """创建简单的测试GUI"""
    root = tk.Tk()
    root.title("IPS解析功能测试")
    root.geometry("800x600")

    # 创建一个测试IPS文件
    test_ips_path = "/tmp/test_gui.ips"
    create_test_ips_file(test_ips_path)

    # 导入主GUI程序
    try:
        from mars_log_analyzer_pro import MarsLogAnalyzerPro

        # 创建分析器实例
        analyzer = MarsLogAnalyzerPro(root)

        # 设置测试文件路径
        analyzer.ips_file_var.set(test_ips_path)

        # 自动触发解析
        root.after(1000, lambda: analyzer.analyze_ips_crash())

        # 5秒后自动关闭
        root.after(5000, root.quit)

        # 显示提示
        label = tk.Label(root, text="正在测试IPS解析功能...\n文件: " + test_ips_path,
                        font=("Arial", 14))
        label.pack(pady=20)

        root.mainloop()

        # 清理测试文件
        if os.path.exists(test_ips_path):
            os.remove(test_ips_path)

        print("✅ GUI测试完成")

    except Exception as e:
        print(f"❌ GUI测试失败: {e}")
        import traceback
        traceback.print_exc()

def create_test_ips_file(filepath):
    """创建测试IPS文件"""
    content = '''{"app_name":"心娱","timestamp":"2025-09-21 17:00:00.00 +0800","app_version":"5.8.0","slice_uuid":"abcd1234-5678-90ab-cdef-1234567890ab","build_version":"580","platform":2,"bundleID":"com.xinyue.app","share_with_app_devs":1,"is_first_party":0,"bug_type":"309","os_version":"iPhone OS 17.0 (21A329)","roots_installed":0,"name":"心娱","incident_id":"XY-2025-09-21-001"}
{
  "uptime" : 3600,
  "procRole" : "Foreground",
  "version" : 2,
  "userID" : 501,
  "deployVersion" : 210,
  "modelCode" : "iPhone15,2",
  "osVersion" : {
    "isEmbedded" : true,
    "train" : "iPhone OS 17.0",
    "releaseType" : "User",
    "build" : "21A329"
  },
  "captureTime" : "2025-09-21 17:00:00.0000 +0800",
  "incident" : "XY-2025-09-21-001",
  "pid" : 5678,
  "cpuType" : "ARM-64",
  "procName" : "心娱",
  "procPath" : "/private/var/containers/Bundle/Application/XY-UUID/心娱.app/心娱",
  "bundleInfo" : {"CFBundleShortVersionString":"5.8.0","CFBundleVersion":"580","CFBundleIdentifier":"com.xinyue.app"},
  "exception" : {
    "codes":"0x0000000000000001, 0x00000001a1234567",
    "type":"EXC_BAD_ACCESS",
    "signal":"SIGSEGV",
    "subtype":"KERN_INVALID_ADDRESS at 0x0000000000000000"
  },
  "termination" : {
    "flags":0,
    "code":11,
    "namespace":"SIGNAL",
    "indicator":"Segmentation fault: 11",
    "byProc":"exc handler",
    "byPid":5678
  },
  "faultingThread" : 0,
  "threads" : [
    {
      "triggered": true,
      "id": 2001,
      "queue": "com.apple.main-thread",
      "frames": [
        {
          "imageOffset": 12345,
          "symbol": "-[RoomViewController viewDidLoad]",
          "symbolLocation": 123,
          "imageIndex": 0
        },
        {
          "imageOffset": 23456,
          "symbol": "-[UIViewController loadViewIfRequired]",
          "symbolLocation": 456,
          "imageIndex": 1
        },
        {
          "imageOffset": 34567,
          "symbol": "UIApplicationMain",
          "symbolLocation": 789,
          "imageIndex": 1
        },
        {
          "imageOffset": 45678,
          "symbol": "main",
          "symbolLocation": 100,
          "imageIndex": 0,
          "sourceFile": "main.m",
          "sourceLine": 14
        }
      ]
    }
  ],
  "usedImages" : [
    {
      "source" : "P",
      "arch" : "arm64",
      "base" : 4295000000,
      "size" : 5000000,
      "uuid" : "abcd1234-5678-90ab-cdef-1234567890ab",
      "path" : "/private/var/containers/Bundle/Application/XY-UUID/心娱.app/心娱",
      "name" : "心娱"
    },
    {
      "source" : "P",
      "arch" : "arm64e",
      "base" : 6700000000,
      "size" : 25000000,
      "uuid" : "uikit-uuid-1234-5678-90ab",
      "path" : "/System/Library/Frameworks/UIKit.framework/UIKit",
      "name" : "UIKit"
    }
  ]
}'''

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"创建测试IPS文件: {filepath}")


if __name__ == "__main__":
    print("=== 测试GUI中的IPS解析功能 ===\n")

    # 简单测试：只测试IPS解析器本身
    print("1. 测试IPS解析器...")
    from ips_parser import IPSParser

    test_file = "/tmp/simple_test.ips"
    create_test_ips_file(test_file)

    parser = IPSParser()
    if parser.parse_file(test_file):
        info = parser.get_crash_info()
        print(f"   ✅ 解析成功: {info['app_name']} v{info['app_version']}")
        print(f"   异常类型: {info.get('exception_type', 'N/A')}")
        print(f"   崩溃线程: {info.get('crashed_thread', 'N/A')}")
    else:
        print("   ❌ 解析失败")

    if os.path.exists(test_file):
        os.remove(test_file)

    print("\n2. 测试GUI集成...")
    print("   注意: GUI测试将打开一个窗口并在5秒后自动关闭")

    # 运行GUI测试
    test_gui()

    print("\n=== 测试完成 ===")