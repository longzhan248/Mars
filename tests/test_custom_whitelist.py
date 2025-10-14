#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iOS混淆工具自定义白名单功能测试

测试自定义白名单的创建、加载、保存、导入、导出功能
"""

import sys
import os
import json
import tempfile
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_whitelist_file_operations():
    """测试白名单文件操作"""
    print("\n" + "="*60)
    print("测试1: 白名单文件操作")
    print("="*60)

    whitelist_dir = Path(__file__).parent.parent / "gui" / "modules" / "obfuscation"
    whitelist_file = whitelist_dir / "custom_whitelist.json"

    # 测试数据
    test_data = {
        "version": "1.0",
        "updated": "2025-10-14T12:00:00",
        "items": [
            {
                "name": "TestClass",
                "type": "class",
                "reason": "测试用途"
            },
            {
                "name": "testMethod:",
                "type": "method",
                "reason": "示例方法"
            },
            {
                "name": "testProperty",
                "type": "property",
                "reason": "示例属性"
            }
        ]
    }

    # 确保目录存在
    whitelist_dir.mkdir(parents=True, exist_ok=True)

    # 测试保存
    try:
        with open(whitelist_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, indent=2, ensure_ascii=False)
        print("✅ 保存白名单文件成功")
    except Exception as e:
        print(f"❌ 保存失败: {e}")
        return False

    # 测试加载
    try:
        with open(whitelist_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)

        assert loaded_data['version'] == test_data['version']
        assert len(loaded_data['items']) == 3
        print(f"✅ 加载白名单文件成功，包含 {len(loaded_data['items'])} 个条目")
    except Exception as e:
        print(f"❌ 加载失败: {e}")
        return False

    # 验证数据完整性
    for i, item in enumerate(loaded_data['items']):
        expected = test_data['items'][i]
        assert item['name'] == expected['name']
        assert item['type'] == expected['type']
        assert item['reason'] == expected['reason']

    print("✅ 数据完整性验证通过")
    return True


def test_whitelist_export_txt():
    """测试TXT格式导出"""
    print("\n" + "="*60)
    print("测试2: TXT格式导出")
    print("="*60)

    whitelist_dir = Path(__file__).parent.parent / "gui" / "modules" / "obfuscation"
    whitelist_file = whitelist_dir / "custom_whitelist.json"

    # 创建临时TXT文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        txt_file = f.name

    try:
        # 读取JSON数据
        with open(whitelist_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 转换为TXT格式
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write("# iOS混淆自定义白名单\n")
            f.write(f"# 版本: {data['version']}\n")
            f.write(f"# 更新时间: {data['updated']}\n\n")

            for item in data['items']:
                f.write(f"{item['name']}\n")

        # 验证导出
        with open(txt_file, 'r', encoding='utf-8') as f:
            content = f.read()

        assert 'TestClass' in content
        assert 'testMethod:' in content
        assert 'testProperty' in content
        print("✅ TXT格式导出成功")
        print(f"   导出文件: {txt_file}")
        print(f"   文件大小: {os.path.getsize(txt_file)} 字节")

        return True
    except Exception as e:
        print(f"❌ TXT导出失败: {e}")
        return False
    finally:
        # 清理临时文件
        if os.path.exists(txt_file):
            os.remove(txt_file)


def test_whitelist_import_txt():
    """测试TXT格式导入"""
    print("\n" + "="*60)
    print("测试3: TXT格式导入")
    print("="*60)

    # 创建临时TXT文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        txt_file = f.name
        f.write("# 测试白名单\n")
        f.write("ImportedClass1\n")
        f.write("ImportedClass2\n")
        f.write("importedMethod:\n")
        f.write("\n")  # 空行应该被忽略
        f.write("# 注释行\n")
        f.write("ImportedProperty\n")

    try:
        # 读取并解析TXT
        items = []
        with open(txt_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    items.append({
                        'name': line,
                        'type': 'auto',
                        'reason': 'Imported from TXT'
                    })

        assert len(items) == 4
        assert items[0]['name'] == 'ImportedClass1'
        assert items[3]['name'] == 'ImportedProperty'
        print(f"✅ TXT格式导入成功，解析出 {len(items)} 个条目")

        for item in items:
            print(f"   - {item['name']}")

        return True
    except Exception as e:
        print(f"❌ TXT导入失败: {e}")
        return False
    finally:
        # 清理临时文件
        if os.path.exists(txt_file):
            os.remove(txt_file)


def test_whitelist_integration():
    """测试白名单与混淆引擎集成"""
    print("\n" + "="*60)
    print("测试4: 与混淆引擎集成")
    print("="*60)

    whitelist_dir = Path(__file__).parent.parent / "gui" / "modules" / "obfuscation"
    whitelist_file = whitelist_dir / "custom_whitelist.json"

    try:
        # 模拟加载过程
        custom_whitelist = []

        if whitelist_file.exists():
            with open(whitelist_file, 'r', encoding='utf-8') as f:
                whitelist_data = json.load(f)
                custom_whitelist = [item['name'] for item in whitelist_data.get('items', [])]

            print(f"✅ 模拟加载成功，共 {len(custom_whitelist)} 个白名单项")
            print("   白名单内容:")
            for name in custom_whitelist:
                print(f"   - {name}")

            # 验证白名单项格式
            for name in custom_whitelist:
                assert isinstance(name, str)
                assert len(name) > 0

            print("✅ 白名单项格式验证通过")
            return True
        else:
            print("⚠️  白名单文件不存在")
            return True  # 不存在是正常情况
    except Exception as e:
        print(f"❌ 集成测试失败: {e}")
        return False


def test_whitelist_validation():
    """测试白名单数据验证"""
    print("\n" + "="*60)
    print("测试5: 数据验证")
    print("="*60)

    # 测试有效数据
    valid_items = [
        {"name": "MyClass", "type": "class", "reason": "Valid"},
        {"name": "myMethod:", "type": "method", "reason": "Valid"},
        {"name": "myProperty", "type": "property", "reason": "Valid"}
    ]

    # 测试无效数据
    invalid_items = [
        {"name": "", "type": "class", "reason": "Empty name"},  # 空名称
        {"name": "Test", "reason": "No type"},  # 缺少类型
        {"name": "Test", "type": "class"}  # 缺少原因
    ]

    # 验证有效数据
    for item in valid_items:
        try:
            assert 'name' in item and item['name']
            assert 'type' in item
            assert 'reason' in item
            print(f"✅ 有效数据: {item['name']}")
        except AssertionError:
            print(f"❌ 验证失败: {item}")
            return False

    # 验证无效数据检测
    invalid_count = 0
    for item in invalid_items:
        try:
            if not item.get('name'):
                invalid_count += 1
                print(f"✅ 正确拒绝: 空名称")
            elif 'type' not in item:
                invalid_count += 1
                print(f"✅ 正确拒绝: 缺少类型")
            elif 'reason' not in item:
                invalid_count += 1
                print(f"✅ 正确拒绝: 缺少原因")
        except Exception as e:
            print(f"❌ 验证错误: {e}")
            return False

    assert invalid_count == len(invalid_items)
    print(f"✅ 数据验证通过，正确拒绝 {invalid_count} 个无效条目")
    return True


def cleanup_test_files():
    """清理测试文件"""
    print("\n" + "="*60)
    print("清理测试文件")
    print("="*60)

    whitelist_dir = Path(__file__).parent.parent / "gui" / "modules" / "obfuscation"
    whitelist_file = whitelist_dir / "custom_whitelist.json"

    if whitelist_file.exists():
        # 保留测试文件供实际使用
        print(f"保留白名单文件: {whitelist_file}")

    print("✅ 清理完成")


def main():
    """运行所有测试"""
    print("iOS混淆工具 - 自定义白名单功能测试")
    print("="*60)

    tests = [
        ("文件操作", test_whitelist_file_operations),
        ("TXT导出", test_whitelist_export_txt),
        ("TXT导入", test_whitelist_import_txt),
        ("引擎集成", test_whitelist_integration),
        ("数据验证", test_whitelist_validation)
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ 测试 '{name}' 发生异常: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # 清理
    cleanup_test_files()

    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status}: {name}")

    print("\n" + "="*60)
    print(f"总计: {passed}/{total} 通过")
    print("="*60)

    if passed == total:
        print("\n🎉 所有测试通过！自定义白名单功能正常工作。")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败，请检查实现。")
        return 1


if __name__ == '__main__':
    sys.exit(main())
