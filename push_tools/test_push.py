#!/usr/bin/env python3
"""
iOS推送功能测试脚本
"""

import json
import os
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from apns_push import APNSManager


def test_certificate_loading():
    """测试证书加载功能"""
    print("\n=== 测试证书加载 ===")

    # 创建管理器
    manager = APNSManager()

    # 测试证书路径（需要替换为实际的证书路径）
    test_cert = Path.home() / "Desktop" / "test.p12"

    if not test_cert.exists():
        print(f"测试证书不存在: {test_cert}")
        print("请放置一个有效的推送证书到桌面，命名为test.p12")
        return False

    # 加载证书
    success = manager.load_certificate(str(test_cert), password="")

    if success:
        print("✅ 证书加载成功")

        # 打印证书信息
        cert = manager.current_cert
        print(f"证书名称: {manager.current_cert_name}")
        print(f"环境: {cert.cert_info.get('environment', 'unknown')}")
        print(f"Bundle ID: {cert.cert_info.get('bundle_id', 'unknown')}")
        print(f"有效期: {cert.days_until_expiry()} 天")

        return True
    else:
        print("❌ 证书加载失败")
        return False


def test_payload_creation():
    """测试Payload创建"""
    print("\n=== 测试Payload创建 ===")

    # 简单消息
    simple = {
        "aps": {
            "alert": "Hello, World!"
        }
    }
    print(f"简单消息: {json.dumps(simple, ensure_ascii=False)}")

    # 带角标
    with_badge = {
        "aps": {
            "alert": "You have new messages",
            "badge": 5
        }
    }
    print(f"带角标: {json.dumps(with_badge, ensure_ascii=False)}")

    # 富文本
    rich = {
        "aps": {
            "alert": {
                "title": "Breaking News",
                "subtitle": "Important Update",
                "body": "This is the detailed message content."
            },
            "sound": "default",
            "mutable-content": 1
        }
    }
    print(f"富文本: {json.dumps(rich, ensure_ascii=False)}")

    # 静默推送
    silent = {
        "aps": {
            "content-available": 1
        }
    }
    print(f"静默推送: {json.dumps(silent, ensure_ascii=False)}")

    return True


def test_push_history():
    """测试推送历史功能"""
    print("\n=== 测试推送历史 ===")

    from apns_push import PushHistory

    history = PushHistory()

    # 添加测试记录
    history.add_record(
        device_token="test_token_123",
        payload={"aps": {"alert": "Test message"}},
        certificate_name="TestCert",
        success=True,
        error_message=None,
        sandbox=True
    )

    history.add_record(
        device_token="test_token_456",
        payload={"aps": {"alert": "Failed message"}},
        certificate_name="TestCert",
        success=False,
        error_message="Invalid token",
        sandbox=True
    )

    # 获取历史记录
    recent = history.get_recent(5)
    print(f"最近 {len(recent)} 条历史记录:")

    for i, record in enumerate(recent, 1):
        status = "✅" if record['success'] else "❌"
        print(f"{i}. {status} {record['timestamp']} - {record['device_token'][:10]}...")

    return True


def test_mock_push():
    """模拟推送发送（不实际发送）"""
    print("\n=== 模拟推送发送 ===")

    _manager = APNSManager()  # 模拟创建，未实际使用

    # 模拟设备Token
    mock_token = "a" * 64  # 64个字符的假Token

    # 模拟payload
    payload = {
        "aps": {
            "alert": "This is a test notification",
            "badge": 1,
            "sound": "default"
        }
    }

    print(f"Device Token: {mock_token[:20]}...")
    print(f"Payload: {json.dumps(payload, ensure_ascii=False)}")
    print("注意: 这只是模拟，不会实际发送推送")

    return True


def main():
    """主测试函数"""
    print("=" * 50)
    print("iOS推送功能测试")
    print("=" * 50)

    tests = [
        ("Payload创建", test_payload_creation),
        ("推送历史", test_push_history),
        ("模拟推送", test_mock_push),
        ("证书加载", test_certificate_loading),
    ]

    results = []

    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"❌ {name} 测试失败: {e}")
            results.append((name, False))

    # 打印总结
    print("\n" + "=" * 50)
    print("测试结果总结:")
    print("=" * 50)

    for name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{name}: {status}")

    # 统计
    passed = sum(1 for _, s in results if s)
    total = len(results)
    print(f"\n总计: {passed}/{total} 测试通过")

    return 0 if passed == total else 1


if __name__ == '__main__':
    sys.exit(main())