"""
代码解析器 - 向后兼容接口

此文件保持向后兼容性，重定向到parsers子模块。
原始1242行代码已拆分为5个独立模块：
- parsers/common.py (数据模型)
- parsers/string_protector.py (字符串保护)
- parsers/objc_parser.py (Objective-C解析)
- parsers/swift_parser.py (Swift解析)
- parsers/parser_coordinator.py (协调器)

重构日期: 2025-10-23
"""

# 重新导出所有公共API，保持100%向后兼容
from .parsers import (
    CodeParser,
    ObjCParser,
    ParsedFile,
    StringLiteralProtector,
    SwiftParser,
    Symbol,
    SymbolType,
)

__all__ = [
    'Symbol',
    'SymbolType',
    'ParsedFile',
    'StringLiteralProtector',
    'ObjCParser',
    'SwiftParser',
    'CodeParser',
]


# 保留原始测试代码，供参考和验证
if __name__ == "__main__":
    # 测试代码
    print("=== 代码解析器测试 ===\n")

    # 创建测试文件
    test_objc_header = """
#import <UIKit/UIKit.h>
#import "MyProtocol.h"

@class MyDelegate;

@protocol MyProtocolDelegate <NSObject>
- (void)didFinish;
@end

@interface MyViewController : UIViewController <MyProtocolDelegate>

@property (nonatomic, strong) NSString *userName;
@property (nonatomic, assign) NSInteger userId;

- (instancetype)initWithFrame:(CGRect)frame;
- (void)loadDataWithCompletion:(void (^)(BOOL success))completion;
+ (instancetype)sharedInstance;

@end

@interface MyViewController (Private)
- (void)privateMethod;
@end

typedef enum {
    StatusIdle,
    StatusRunning,
    StatusFinished
} MyStatus;

#define kMaxRetryCount 3
#define kAPIBaseURL @"https://api.example.com"
"""

    test_swift_file = """
import UIKit
import Foundation

protocol MyDelegate {
    func didFinish()
}

class MyViewController: UIViewController, MyDelegate {

    var userName: String = ""
    let userId: Int = 0

    func loadData() {
        // Implementation
    }

    func didFinish() {
        // Protocol implementation
    }
}

extension MyViewController {
    func extensionMethod() {
        // Extension method
    }
}

enum NetworkStatus {
    case idle
    case loading
    case success
    case failure
}

struct User {
    var name: String
    var age: Int
}
"""

    # 保存测试文件
    import os
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        objc_path = os.path.join(tmpdir, "test.h")
        swift_path = os.path.join(tmpdir, "test.swift")

        with open(objc_path, 'w') as f:
            f.write(test_objc_header)

        with open(swift_path, 'w') as f:
            f.write(test_swift_file)

        # 测试Objective-C解析
        print("1. Objective-C解析测试:")
        parser = CodeParser()
        objc_result = parser.parse_file(objc_path)

        print(f"  文件: {objc_result.file_path}")
        print(f"  语言: {objc_result.language}")
        print(f"  导入: {len(objc_result.imports)} 个")
        print(f"  符号: {len(objc_result.symbols)} 个")

        # 按类型统计
        groups = parser.group_symbols_by_type(objc_result.symbols)
        for symbol_type, symbols in groups.items():
            print(f"    {symbol_type.value}: {len(symbols)} 个")
            for s in symbols[:2]:  # 只显示前2个
                print(f"      - {s.name} (行{s.line_number})")

        # 测试Swift解析
        print("\n2. Swift解析测试:")
        swift_result = parser.parse_file(swift_path)

        print(f"  文件: {swift_result.file_path}")
        print(f"  语言: {swift_result.language}")
        print(f"  导入: {len(swift_result.imports)} 个")
        print(f"  符号: {len(swift_result.symbols)} 个")

        groups = parser.group_symbols_by_type(swift_result.symbols)
        for symbol_type, symbols in groups.items():
            print(f"    {symbol_type.value}: {len(symbols)} 个")
            for s in symbols[:2]:
                print(f"      - {s.name} (行{s.line_number})")

    print("\n=== 测试完成 ===")
