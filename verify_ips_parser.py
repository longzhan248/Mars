#!/usr/bin/env python3
"""
验证IPS解析器功能完整性
"""

from ips_parser import IPSParser, IPSSymbolicator


def create_test_ips():
    """创建测试IPS文件"""
    content = '''{"app_name":"TestApp","timestamp":"2025-09-21 20:00:00.00 +0800","app_version":"2.0.1","slice_uuid":"test-app-uuid","build_version":"201","platform":2,"bundleID":"com.test.application","os_version":"iPhone OS 17.0","incident_id":"INCIDENT-2025"}
{
  "uptime": 5000,
  "procRole": "Foreground",
  "incident": "INCIDENT-2025",
  "pid": 9999,
  "procName": "TestApp",
  "procPath": "/private/var/containers/Bundle/Application/UUID/TestApp.app/TestApp",
  "bundleInfo": {"CFBundleIdentifier":"com.test.application"},
  "exception": {
    "type": "EXC_BAD_ACCESS",
    "codes": "0x0000000000000001, 0x0000000000000000",
    "signal": "SIGSEGV"
  },
  "termination": {
    "indicator": "Segmentation fault: 11"
  },
  "faultingThread": 0,
  "threads": [
    {
      "triggered": true,
      "id": 1,
      "frames": [
        {"imageOffset": 1024, "symbol": "crashMethod", "symbolLocation": 16, "imageIndex": 0},
        {"imageOffset": 2048, "symbol": "-[ViewController buttonPressed:]", "symbolLocation": 32, "imageIndex": 0},
        {"imageOffset": 3072, "symbol": "-[UIControl sendAction:to:forEvent:]", "symbolLocation": 48, "imageIndex": 1},
        {"imageOffset": 4096, "symbol": "UIApplicationMain", "symbolLocation": 64, "imageIndex": 1},
        {"imageOffset": 5120, "symbol": "main", "symbolLocation": 80, "imageIndex": 0, "sourceFile": "main.m", "sourceLine": 15}
      ]
    },
    {
      "id": 2,
      "name": "com.apple.NSURLSession",
      "frames": [
        {"imageOffset": 6144, "symbol": "mach_msg_trap", "symbolLocation": 8, "imageIndex": 2}
      ]
    }
  ],
  "usedImages": [
    {
      "base": 4295000064,
      "size": 524288,
      "uuid": "test-app-uuid",
      "path": "/private/var/containers/Bundle/Application/UUID/TestApp.app/TestApp",
      "name": "TestApp",
      "arch": "arm64"
    },
    {
      "base": 6442450944,
      "size": 33554432,
      "uuid": "uikit-uuid",
      "path": "/System/Library/Frameworks/UIKit.framework/UIKit",
      "name": "UIKit",
      "arch": "arm64e"
    },
    {
      "base": 6576668672,
      "size": 196608,
      "uuid": "kernel-uuid",
      "path": "/usr/lib/system/libsystem_kernel.dylib",
      "name": "libsystem_kernel.dylib",
      "arch": "arm64e"
    }
  ]
}'''
    return content


def run_tests():
    """运行功能验证测试"""
    print("=" * 60)
    print("IPS 解析器功能验证")
    print("=" * 60)

    # 测试1: 基本解析
    print("\n测试 1: 基本解析功能")
    print("-" * 40)

    parser = IPSParser()
    test_content = create_test_ips()

    if parser.parse_content(test_content):
        print("✅ 解析成功")

        info = parser.get_crash_info()
        assert info['app_name'] == 'TestApp', "应用名称错误"
        assert info['app_version'] == '2.0.1', "版本号错误"
        assert info['bundle_id'] == 'com.test.application', "Bundle ID错误"
        assert info['crashed_thread'] == 0, "崩溃线程错误"
        assert info['exception_type'] == 'EXC_BAD_ACCESS', "异常类型错误"
        print("✅ 基本信息提取正确")
    else:
        print("❌ 解析失败")
        return False

    # 测试2: 堆栈帧提取
    print("\n测试 2: 堆栈帧提取")
    print("-" * 40)

    frames = parser.get_crashed_thread_frames()
    assert len(frames) == 5, f"堆栈帧数量错误: {len(frames)}"
    assert frames[0].symbol == 'crashMethod', "第一帧符号错误"
    assert frames[4].source_file == 'main.m', "源文件信息丢失"
    assert frames[4].source_line == 15, "源代码行号错误"
    print(f"✅ 成功提取 {len(frames)} 个堆栈帧")

    # 测试3: 二进制分类
    print("\n测试 3: 应用/系统库分类")
    print("-" * 40)

    for frame in frames:
        is_app = parser._is_app_binary(frame.binary_name, 'com.test.application')
        if frame.binary_name == 'TestApp':
            assert is_app == True, f"{frame.binary_name} 应该是应用库"
            print(f"✅ {frame.binary_name}: 应用库")
        else:
            assert is_app == False, f"{frame.binary_name} 应该是系统库"
            print(f"✅ {frame.binary_name}: 系统库")

    # 测试4: 格式转换
    print("\n测试 4: 格式转换")
    print("-" * 40)

    # 不带标签
    crash_format = parser.to_crash_format(with_tags=False)
    assert '[APP]' not in crash_format, "不应包含标签"
    assert '[SYS]' not in crash_format, "不应包含标签"
    print("✅ 无标签格式正确")

    # 带标签
    tagged_format = parser.to_crash_format(with_tags=True)
    assert '[APP]' in tagged_format, "应包含应用标签"
    assert '[SYS]' in tagged_format, "应包含系统标签"

    app_count = tagged_format.count('[APP]')
    sys_count = tagged_format.count('[SYS]')
    print(f"✅ 带标签格式正确 (应用: {app_count}, 系统: {sys_count})")

    # 测试5: 二进制映像
    print("\n测试 5: 二进制映像信息")
    print("-" * 40)

    assert len(parser.binary_images) == 3, "二进制映像数量错误"
    test_app = parser.binary_images[0]
    assert test_app.name == 'TestApp', "应用名称错误"
    assert test_app.uuid == 'test-app-uuid', "UUID错误"
    assert test_app.arch == 'arm64', "架构错误"
    print(f"✅ 成功解析 {len(parser.binary_images)} 个二进制映像")

    # 测试6: 线程信息
    print("\n测试 6: 线程信息")
    print("-" * 40)

    assert len(parser.threads) == 2, "线程数量错误"
    assert parser.threads[0].get('triggered') == True, "崩溃线程标记错误"
    assert parser.threads[1].get('name') == 'com.apple.NSURLSession', "线程名称错误"
    print(f"✅ 成功解析 {len(parser.threads)} 个线程")

    print("\n" + "=" * 60)
    print("所有测试通过！✅")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)