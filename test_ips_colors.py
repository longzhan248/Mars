#!/usr/bin/env python3
"""
测试IPS解析器的颜色区分功能
"""

from ips_parser import IPSParser

def test_color_tags():
    """测试颜色标签功能"""

    # 创建测试IPS内容
    test_content = '''{"app_name":"MyApp","timestamp":"2025-09-21 18:00:00.00 +0800","app_version":"1.0","slice_uuid":"app-uuid-1234","build_version":"100","platform":2,"bundleID":"com.example.myapp","os_version":"iPhone OS 17.0 (21A329)","incident_id":"TEST-001"}
{
  "uptime": 1000,
  "procRole": "Foreground",
  "incident": "TEST-001",
  "pid": 1234,
  "procName": "MyApp",
  "procPath": "/private/var/containers/Bundle/Application/UUID/MyApp.app/MyApp",
  "bundleInfo": {"CFBundleIdentifier":"com.example.myapp"},
  "exception": {"type":"EXC_CRASH","signal":"SIGABRT"},
  "faultingThread": 0,
  "threads": [
    {
      "triggered": true,
      "id": 1,
      "frames": [
        {"imageOffset": 1000, "symbol": "myAppFunction", "symbolLocation": 10, "imageIndex": 0},
        {"imageOffset": 2000, "symbol": "-[MyViewController viewDidLoad]", "symbolLocation": 20, "imageIndex": 0},
        {"imageOffset": 3000, "symbol": "-[UIViewController loadView]", "symbolLocation": 30, "imageIndex": 1},
        {"imageOffset": 4000, "symbol": "UIApplicationMain", "symbolLocation": 40, "imageIndex": 1},
        {"imageOffset": 5000, "symbol": "_dispatch_queue_override_invoke", "symbolLocation": 50, "imageIndex": 2},
        {"imageOffset": 6000, "symbol": "start", "symbolLocation": 60, "imageIndex": 3}
      ]
    }
  ],
  "usedImages": [
    {
      "base": 4295000000,
      "size": 100000,
      "uuid": "app-uuid-1234",
      "path": "/private/var/containers/Bundle/Application/UUID/MyApp.app/MyApp",
      "name": "MyApp",
      "arch": "arm64"
    },
    {
      "base": 6700000000,
      "size": 1000000,
      "uuid": "uikit-uuid",
      "path": "/System/Library/Frameworks/UIKit.framework/UIKit",
      "name": "UIKit",
      "arch": "arm64e"
    },
    {
      "base": 6800000000,
      "size": 500000,
      "uuid": "dispatch-uuid",
      "path": "/usr/lib/system/libdispatch.dylib",
      "name": "libdispatch.dylib",
      "arch": "arm64e"
    },
    {
      "base": 6900000000,
      "size": 100000,
      "uuid": "dyld-uuid",
      "path": "/usr/lib/dyld",
      "name": "dyld",
      "arch": "arm64e"
    }
  ]
}'''

    print("=== 测试IPS颜色标签功能 ===\n")

    # 解析内容
    parser = IPSParser()
    if parser.parse_content(test_content):
        print("✅ IPS解析成功\n")

        # 生成带标签的输出
        tagged_output = parser.to_crash_format(with_tags=True)

        print("带标签的输出:")
        print("-" * 60)

        # 显示部分输出，高亮显示标签
        lines = tagged_output.split('\n')
        for i, line in enumerate(lines):
            if i > 40:  # 只显示前40行
                print(f"... ({len(lines) - i} 行省略)")
                break

            if line.startswith('[APP]'):
                # 蓝色显示应用符号
                print(f"\033[34;1m{line[5:]}\033[0m  <- 应用符号")
            elif line.startswith('[SYS]'):
                # 灰色显示系统符号
                print(f"\033[90m{line[5:]}\033[0m  <- 系统符号")
            else:
                print(line)

        print("\n" + "-" * 60)

        # 统计标签
        app_count = tagged_output.count('[APP]')
        sys_count = tagged_output.count('[SYS]')

        print(f"\n统计:")
        print(f"  应用符号: {app_count} 个")
        print(f"  系统符号: {sys_count} 个")

        # 验证分类是否正确
        print("\n验证:")
        frames = parser.get_crashed_thread_frames()
        for frame in frames:
            is_app = parser._is_app_binary(frame.binary_name, 'com.example.myapp')
            expected = "应用" if is_app else "系统"
            print(f"  {frame.binary_name}: {expected}库")

    else:
        print("❌ IPS解析失败")

    print("\n测试完成！")


if __name__ == "__main__":
    test_color_tags()