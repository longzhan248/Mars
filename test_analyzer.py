#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试Mars日志分析系统的基本功能
"""

import sys
import os

def test_import():
    """测试导入模块"""
    try:
        print("测试导入解码模块...")
        from decode_mars_nocrypt_log_file_py3 import ParseFile
        print("✓ 解码模块导入成功")

        print("\n测试导入GUI模块...")
        import tkinter
        print("✓ tkinter导入成功")

        print("\n测试matplotlib（可能需要安装）...")
        try:
            import matplotlib
            print("✓ matplotlib导入成功")
        except ImportError:
            print("✗ matplotlib未安装，请运行: pip3 install matplotlib")
            return False

        return True
    except Exception as e:
        print(f"✗ 导入失败: {e}")
        return False

def test_decode():
    """测试解码功能"""
    try:
        print("\n测试解码功能...")
        from decode_mars_nocrypt_log_file_py3 import ParseFile

        # 查找xlog文件
        xlog_files = [f for f in os.listdir('.') if f.endswith('.xlog')]
        if xlog_files:
            test_file = xlog_files[0]
            print(f"使用测试文件: {test_file}")

            output_file = test_file + ".test.log"
            ParseFile(test_file, output_file)

            if os.path.exists(output_file):
                size = os.path.getsize(output_file)
                print(f"✓ 解码成功，输出文件大小: {size} bytes")

                # 清理测试文件
                os.remove(output_file)
                return True
            else:
                print("✗ 解码失败，未生成输出文件")
                return False
        else:
            print("⚠ 未找到xlog文件，跳过解码测试")
            return True

    except Exception as e:
        print(f"✗ 解码测试失败: {e}")
        return False

def main():
    print("="*50)
    print("Mars日志分析系统测试")
    print("="*50)

    success = True

    # 测试导入
    if not test_import():
        success = False

    # 测试解码
    if not test_decode():
        success = False

    print("\n" + "="*50)
    if success:
        print("✓ 所有测试通过！")
        print("\n现在可以运行: ./run_analyzer.sh 启动GUI系统")
    else:
        print("✗ 部分测试失败，请检查错误信息")
    print("="*50)

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())