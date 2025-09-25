#!/usr/bin/env python3
"""
测试IPS解析器
"""

import os
import sys
from ips_parser import IPSParser, IPSSymbolicator

def test_ips_parser():
    """测试IPS解析器基本功能"""

    # 创建一个示例IPS内容（基于MacSymbolicator的测试文件格式）
    test_ips_content = '''{"app_name":"TestApp","timestamp":"2025-09-21 10:00:00.00 +0800","app_version":"1.0","slice_uuid":"12345678-1234-1234-1234-123456789012","build_version":"1","platform":2,"bundleID":"com.test.app","share_with_app_devs":1,"is_first_party":0,"bug_type":"309","os_version":"iPhone OS 16.0 (20A362)","roots_installed":0,"name":"TestApp","incident_id":"TEST-INCIDENT-ID"}
{
  "uptime" : 100,
  "procRole" : "Foreground",
  "version" : 2,
  "userID" : 501,
  "deployVersion" : 210,
  "modelCode" : "iPhone14,2",
  "coalitionID" : 625,
  "osVersion" : {
    "isEmbedded" : true,
    "train" : "iPhone OS 16.0",
    "releaseType" : "User",
    "build" : "20A362"
  },
  "captureTime" : "2025-09-21 10:00:00.0000 +0800",
  "incident" : "TEST-INCIDENT-ID",
  "pid" : 1234,
  "cpuType" : "ARM-64",
  "roots_installed" : 0,
  "bug_type" : "309",
  "procLaunch" : "2025-09-21 09:59:00.0000 +0800",
  "procStartAbsTime" : 1000000000,
  "procExitAbsTime" : 2000000000,
  "procName" : "TestApp",
  "procPath" : "/private/var/containers/Bundle/Application/TEST-UUID/TestApp.app/TestApp",
  "bundleInfo" : {"CFBundleShortVersionString":"1.0","CFBundleVersion":"1","CFBundleIdentifier":"com.test.app"},
  "storeInfo" : {"deviceIdentifierForVendor":"DEVICE-UUID","thirdParty":true},
  "parentProc" : "launchd",
  "parentPid" : 1,
  "coalitionName" : "com.test.app",
  "crashReporterKey" : "CRASH-KEY",
  "basebandVersion" : "1.00.00",
  "exception" : {"codes":"0x0000000000000001, 0x000000018a98520c","rawCodes":[1,6620205580],"type":"EXC_BREAKPOINT","signal":"SIGTRAP"},
  "termination" : {"flags":0,"code":5,"namespace":"SIGNAL","indicator":"Trace/BPT trap: 5","byProc":"exc handler","byPid":1234},
  "os_fault" : {"process":"TestApp"},
  "faultingThread" : 0,
  "threads" : [
    {
      "triggered": true,
      "id": 1001,
      "threadState": {
        "x": [{"value":0}, {"value":1}, {"value":2}],
        "flavor": "ARM_THREAD_STATE64",
        "lr": {"value": 6620205580},
        "cpsr": {"value": 1610616832},
        "fp": {"value": 6136057520},
        "sp": {"value": 6136057392},
        "esr": {"value": 4060086273, "description": "(Breakpoint) brk 1"},
        "pc": {"value": 6620205580, "matchesCrashFrame": 1},
        "far": {"value": 8187073608}
      },
      "queue": "com.apple.main-thread",
      "frames": [
        {
          "imageOffset": 100,
          "symbol": "crashFunction",
          "symbolLocation": 10,
          "imageIndex": 0
        },
        {
          "imageOffset": 200,
          "symbol": "callerFunction",
          "symbolLocation": 20,
          "imageIndex": 0
        },
        {
          "imageOffset": 300,
          "symbol": "main",
          "symbolLocation": 30,
          "imageIndex": 0
        }
      ]
    },
    {
      "id": 1002,
      "frames": [
        {
          "imageOffset": 400,
          "symbol": "backgroundWork",
          "symbolLocation": 40,
          "imageIndex": 1
        }
      ]
    }
  ],
  "usedImages" : [
    {
      "source" : "P",
      "arch" : "arm64",
      "base" : 4330815488,
      "size" : 32768,
      "uuid" : "12345678-1234-1234-1234-123456789012",
      "path" : "/private/var/containers/Bundle/Application/TEST-UUID/TestApp.app/TestApp",
      "name" : "TestApp"
    },
    {
      "source" : "P",
      "arch" : "arm64e",
      "base" : 6620205580,
      "size" : 1000000,
      "uuid" : "87654321-4321-4321-4321-210987654321",
      "path" : "/System/Library/Frameworks/UIKit.framework/UIKit",
      "name" : "UIKit"
    }
  ]
}'''

    # 创建临时测试文件
    test_file = "/tmp/test.ips"
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_ips_content)

    print("=== 测试IPS解析器 ===\n")

    # 测试解析
    parser = IPSParser()
    if parser.parse_file(test_file):
        print("✅ IPS文件解析成功\n")

        # 获取崩溃信息
        info = parser.get_crash_info()
        print("崩溃摘要:")
        print(f"  应用: {info['app_name']} v{info['app_version']}")
        print(f"  Bundle ID: {info['bundle_id']}")
        print(f"  系统: {info['os_version']}")
        print(f"  崩溃线程: {info['crashed_thread']}")

        if 'exception_type' in info:
            print(f"  异常类型: {info['exception_type']}")
            print(f"  异常代码: {info['exception_codes']}")

        print("")

        # 获取崩溃线程堆栈
        frames = parser.get_crashed_thread_frames()
        print(f"崩溃线程堆栈 ({len(frames)} 帧):")
        for frame in frames:
            if frame.symbol:
                print(f"  {frame.index}: {frame.binary_name} - {frame.symbol} + {frame.offset}")
            else:
                print(f"  {frame.index}: {frame.binary_name} - 0x{frame.address:x}")

        print("")

        # 测试转换为crash格式
        print("转换为crash格式:")
        print("-" * 60)
        crash_format = parser.to_crash_format()
        # 只显示前20行
        lines = crash_format.split('\n')
        for line in lines[:20]:
            print(line)
        if len(lines) > 20:
            print(f"... ({len(lines) - 20} 行省略)")

    else:
        print("❌ IPS文件解析失败")

    # 清理临时文件
    if os.path.exists(test_file):
        os.remove(test_file)

    print("\n测试完成！")


if __name__ == "__main__":
    test_ips_parser()