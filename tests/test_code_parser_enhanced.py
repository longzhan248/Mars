#!/usr/bin/env python3
"""
代码解析器增强测试

测试CodeParser的所有功能，包括边界情况和错误处理
"""

import sys
import os
from pathlib import Path
import unittest
import tempfile
import shutil

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from gui.modules.obfuscation.code_parser import (
    CodeParser,
    SymbolType,
    Symbol
)
from gui.modules.obfuscation.whitelist_manager import WhitelistManager


class TestCodeParserObjC(unittest.TestCase):
    """Objective-C代码解析测试"""

    def setUp(self):
        """测试准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.whitelist = WhitelistManager(self.temp_dir)
        self.parser = CodeParser(self.whitelist)

    def tearDown(self):
        """清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _parse_objc_code(self, code, filename="test.h"):
        """辅助方法：解析ObjC代码"""
        test_file = os.path.join(self.temp_dir, filename)
        with open(test_file, 'w') as f:
            f.write(code)
        result = self.parser.parse_file(test_file)
        return result.symbols

    def test_parse_simple_class(self):
        """测试解析简单类定义"""
        code = '''
@interface MyViewController : UIViewController
@property (nonatomic, strong) NSString *customTitle;
- (void)customMethod;
@end
'''
        symbols = self._parse_objc_code(code)

        # 验证类名
        class_symbols = [s for s in symbols if s.type == SymbolType.CLASS]
        self.assertEqual(len(class_symbols), 1)
        self.assertEqual(class_symbols[0].name, "MyViewController")

        # 验证属性
        property_symbols = [s for s in symbols if s.type == SymbolType.PROPERTY]
        self.assertEqual(len(property_symbols), 1)
        self.assertEqual(property_symbols[0].name, "customTitle")

        # 验证方法
        method_symbols = [s for s in symbols if s.type == SymbolType.METHOD]
        self.assertEqual(len(method_symbols), 1)
        self.assertEqual(method_symbols[0].name, "customMethod")

    def test_parse_category(self):
        """测试解析Category"""
        code = '''
@interface NSString (MyAdditions)
- (NSString *)reverse;
- (BOOL)isEmpty;
@end
'''
        symbols = self._parse_objc_code(code)

        # Category中的方法应该被识别
        method_symbols = [s for s in symbols if s.type == SymbolType.METHOD]
        self.assertEqual(len(method_symbols), 2)
        method_names = {s.name for s in method_symbols}
        self.assertIn("reverse", method_names)
        self.assertIn("isEmpty", method_names)

    def test_parse_protocol(self):
        """测试解析Protocol"""
        code = '''
@protocol MyDelegate <NSObject>
@required
- (void)didFinishWithResult:(id)result;
@optional
- (void)didCancelWithError:(NSError *)error;
@end
'''
        symbols = self._parse_objc_code(code)

        # 验证协议名
        protocol_symbols = [s for s in symbols if s.type == SymbolType.PROTOCOL]
        self.assertEqual(len(protocol_symbols), 1)
        self.assertEqual(protocol_symbols[0].name, "MyDelegate")

        # 验证方法
        method_symbols = [s for s in symbols if s.type == SymbolType.METHOD]
        self.assertEqual(len(method_symbols), 2)

    def test_parse_enum(self):
        """测试解析枚举"""
        code = '''
typedef NS_ENUM(NSInteger, MyStatus) {
    MyStatusUnknown = 0,
    MyStatusSuccess,
    MyStatusFailed
};
'''
        symbols = self._parse_objc_code(code)

        # 验证枚举名
        enum_symbols = [s for s in symbols if s.type == SymbolType.ENUM]
        self.assertEqual(len(enum_symbols), 1)
        self.assertEqual(enum_symbols[0].name, "MyStatus")

    def test_parse_macro_define(self):
        """测试解析宏定义"""
        code = '''
#define MY_CONSTANT 100
#define MY_STRING @"Hello"
#define MAX(a, b) ((a) > (b) ? (a) : (b))
'''
        symbols = self._parse_objc_code(code)

        # 验证宏
        macro_symbols = [s for s in symbols if s.type == SymbolType.MACRO]
        self.assertEqual(len(macro_symbols), 3)
        macro_names = {s.name for s in macro_symbols}
        self.assertIn("MY_CONSTANT", macro_names)
        self.assertIn("MY_STRING", macro_names)
        self.assertIn("MAX", macro_names)

    def test_parse_property_formats(self):
        """测试解析各种属性格式"""
        code = '''
@interface TestClass : NSObject
@property (nonatomic, strong) NSString *userName;
@property (nonatomic, assign) NSInteger userAge;
@property (nonatomic, copy) NSArray *dataItems;
@property (nonatomic) BOOL isEnabled;
@property NSString* pageTitle;
@property NSString * pageSubtitle;
@property NSString*pageDescription;
@property (nonatomic, copy) void (^completionBlock)(BOOL success);
@end
'''
        symbols = self._parse_objc_code(code)

        # 验证所有属性
        property_symbols = [s for s in symbols if s.type == SymbolType.PROPERTY]
        self.assertEqual(len(property_symbols), 8)

        property_names = {s.name for s in property_symbols}
        self.assertIn("userName", property_names)
        self.assertIn("userAge", property_names)
        self.assertIn("dataItems", property_names)
        self.assertIn("isEnabled", property_names)
        self.assertIn("pageTitle", property_names)
        self.assertIn("pageSubtitle", property_names)
        self.assertIn("pageDescription", property_names)
        self.assertIn("completionBlock", property_names)

    def test_parse_method_with_parameters(self):
        """测试解析带参数的方法"""
        code = '''
@interface TestClass : NSObject
- (void)setName:(NSString *)name;
- (void)updateUser:(NSString *)name age:(NSInteger)age;
- (instancetype)initWithTitle:(NSString *)title subtitle:(NSString *)subtitle;
@end
'''
        symbols = self._parse_objc_code(code)

        method_symbols = [s for s in symbols if s.type == SymbolType.METHOD]
        self.assertEqual(len(method_symbols), 3)

        method_names = {s.name for s in method_symbols}
        self.assertIn("setName:", method_names)
        self.assertIn("updateUser:age:", method_names)
        self.assertIn("initWithTitle:subtitle:", method_names)

    def test_parse_multiline_comment(self):
        """测试多行注释处理"""
        code = '''
/*
 This is a multiline comment
 @interface FakeClass : NSObject
 @end
*/
@interface RealClass : NSObject
@property NSString *name;
@end
'''
        symbols = self._parse_objc_code(code)

        # 只应该识别RealClass
        class_symbols = [s for s in symbols if s.type == SymbolType.CLASS]
        self.assertEqual(len(class_symbols), 1)
        self.assertEqual(class_symbols[0].name, "RealClass")

    def test_parse_string_literal(self):
        """测试字符串字面量处理"""
        code = '''
@interface TestClass : NSObject
- (void)test;
@end

@implementation TestClass
- (void)test {
    NSString *str = @"@interface FakeClass : NSObject";
    // This is a comment with @property fake;
}
@end
'''
        symbols = self._parse_objc_code(code, "test.m")

        # 字符串中的@interface不应该被识别为类
        class_symbols = [s for s in symbols if s.type == SymbolType.CLASS]
        self.assertEqual(len(class_symbols), 1)
        self.assertEqual(class_symbols[0].name, "TestClass")

    def test_whitelist_filtering(self):
        """测试白名单过滤"""
        code = '''
@interface UIViewController (MyCategory)
- (void)myMethod;
@end

@interface MyCustomViewController : UIViewController
- (void)viewDidLoad;
- (void)customMethod;
@end
'''
        symbols = self._parse_objc_code(code)

        # UIViewController是系统类，应该被过滤
        # viewDidLoad是系统方法，应该被过滤
        # customMethod应该保留
        method_symbols = [s for s in symbols if s.type == SymbolType.METHOD]
        method_names = {s.name for s in method_symbols}

        self.assertNotIn("viewDidLoad", method_names)
        self.assertIn("myMethod", method_names)
        self.assertIn("customMethod", method_names)


class TestCodeParserSwift(unittest.TestCase):
    """Swift代码解析测试"""

    def setUp(self):
        """测试准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.whitelist = WhitelistManager(self.temp_dir)
        self.parser = CodeParser(self.whitelist)

    def tearDown(self):
        """清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _parse_swift_code(self, code, filename="test.swift"):
        """辅助方法：解析Swift代码"""
        test_file = os.path.join(self.temp_dir, filename)
        with open(test_file, 'w') as f:
            f.write(code)
        result = self.parser.parse_file(test_file)
        return result.symbols

    def test_parse_simple_class(self):
        """测试解析简单类"""
        code = '''
class MyViewController: UIViewController {
    var customTitle: String = ""

    func customSetup() {
        // Custom implementation
    }
}
'''
        symbols = self._parse_swift_code(code)

        # 验证类名
        class_symbols = [s for s in symbols if s.type == SymbolType.CLASS]
        self.assertEqual(len(class_symbols), 1)
        self.assertEqual(class_symbols[0].name, "MyViewController")

        # 验证属性
        property_symbols = [s for s in symbols if s.type == SymbolType.PROPERTY]
        self.assertEqual(len(property_symbols), 1)
        self.assertEqual(property_symbols[0].name, "customTitle")

        # 验证方法
        method_symbols = [s for s in symbols if s.type == SymbolType.METHOD]
        self.assertEqual(len(method_symbols), 1)
        self.assertEqual(method_symbols[0].name, "customSetup")

    def test_parse_struct(self):
        """测试解析结构体"""
        code = '''
struct User {
    var name: String = ""
    var age: Int = 0

    func isAdult() -> Bool {
        return age >= 18
    }
}
'''
        symbols = self._parse_swift_code(code)

        # 验证结构体
        struct_symbols = [s for s in symbols if s.type == SymbolType.STRUCT]
        self.assertEqual(len(struct_symbols), 1)
        self.assertEqual(struct_symbols[0].name, "User")

        # 验证属性
        property_symbols = [s for s in symbols if s.type == SymbolType.PROPERTY]
        self.assertEqual(len(property_symbols), 2)

        # 验证方法
        method_symbols = [s for s in symbols if s.type == SymbolType.METHOD]
        self.assertEqual(len(method_symbols), 1)

    def test_parse_enum(self):
        """测试解析枚举"""
        code = '''
enum Status {
    case unknown
    case success
    case failed

    func description() -> String {
        return "Status"
    }
}
'''
        symbols = self._parse_swift_code(code)

        # 验证枚举
        enum_symbols = [s for s in symbols if s.type == SymbolType.ENUM]
        self.assertEqual(len(enum_symbols), 1)
        self.assertEqual(enum_symbols[0].name, "Status")

        # 验证枚举case
        constant_symbols = [s for s in symbols if s.type == SymbolType.CONSTANT]
        self.assertEqual(len(constant_symbols), 3)

    def test_parse_protocol(self):
        """测试解析协议"""
        code = '''
protocol MyDelegate {
    func didFinish(result: Any)
    func didCancel(error: Error?)
}
'''
        symbols = self._parse_swift_code(code)

        # 验证协议
        protocol_symbols = [s for s in symbols if s.type == SymbolType.PROTOCOL]
        self.assertEqual(len(protocol_symbols), 1)
        self.assertEqual(protocol_symbols[0].name, "MyDelegate")

        # 验证方法
        method_symbols = [s for s in symbols if s.type == SymbolType.METHOD]
        self.assertEqual(len(method_symbols), 2)

    def test_parse_extension(self):
        """测试解析扩展"""
        code = '''
extension String {
    func reversed() -> String {
        return String(self.reversed())
    }

    var isEmpty: Bool {
        return self.count == 0
    }
}
'''
        symbols = self._parse_swift_code(code)

        # 扩展中的方法和属性应该被识别
        method_symbols = [s for s in symbols if s.type == SymbolType.METHOD]
        property_symbols = [s for s in symbols if s.type == SymbolType.PROPERTY]

        self.assertEqual(len(method_symbols), 1)
        self.assertEqual(len(property_symbols), 1)

    def test_parse_property_formats(self):
        """测试解析各种属性格式"""
        code = '''
class TestClass {
    var name: String = ""
    let id: Int = 0
    var items: [String] = []
    var dict: [String: Any] = [:]
    lazy var data: Data = Data()
    private var secret: String = ""
    static var shared: TestClass = TestClass()
}
'''
        symbols = self._parse_swift_code(code)

        property_symbols = [s for s in symbols if s.type == SymbolType.PROPERTY]
        self.assertEqual(len(property_symbols), 7)

        property_names = {s.name for s in property_symbols}
        self.assertIn("name", property_names)
        self.assertIn("id", property_names)
        self.assertIn("items", property_names)
        self.assertIn("dict", property_names)
        self.assertIn("data", property_names)
        self.assertIn("secret", property_names)
        self.assertIn("shared", property_names)

    def test_parse_method_with_parameters(self):
        """测试解析带参数的方法"""
        code = '''
class TestClass {
    func setName(_ name: String) {
    }

    func updateUser(name: String, age: Int) {
    }

    func fetch(completion: @escaping (Result<Data, Error>) -> Void) {
    }
}
'''
        symbols = self._parse_swift_code(code)

        method_symbols = [s for s in symbols if s.type == SymbolType.METHOD]
        self.assertEqual(len(method_symbols), 3)

        method_names = {s.name for s in method_symbols}
        self.assertIn("setName", method_names)
        self.assertIn("updateUser", method_names)
        self.assertIn("fetch", method_names)

    def test_parse_nested_types(self):
        """测试解析嵌套类型"""
        code = '''
class OuterClass {
    class InnerClass {
        var value: Int = 0
    }

    struct Config {
        var option: String = ""
    }
}
'''
        symbols = self._parse_swift_code(code)

        # 应该识别所有类型
        class_symbols = [s for s in symbols if s.type == SymbolType.CLASS]
        struct_symbols = [s for s in symbols if s.type == SymbolType.STRUCT]

        self.assertEqual(len(class_symbols), 2)
        self.assertEqual(len(struct_symbols), 1)

    def test_parse_multiline_comment(self):
        """测试多行注释处理"""
        code = '''
/*
 This is a comment
 class FakeClass {
 }
*/
class RealClass {
    var name: String = ""
}
'''
        symbols = self._parse_swift_code(code)

        # 只应该识别RealClass
        class_symbols = [s for s in symbols if s.type == SymbolType.CLASS]
        self.assertEqual(len(class_symbols), 1)
        self.assertEqual(class_symbols[0].name, "RealClass")

    def test_parse_string_literal(self):
        """测试字符串字面量处理"""
        code = '''
class TestClass {
    func test() {
        let str = "class FakeClass { }"
        // This is a comment with class fake
    }
}
'''
        symbols = self._parse_swift_code(code)

        # 字符串中的class不应该被识别
        class_symbols = [s for s in symbols if s.type == SymbolType.CLASS]
        self.assertEqual(len(class_symbols), 1)
        self.assertEqual(class_symbols[0].name, "TestClass")


class TestCodeParserEdgeCases(unittest.TestCase):
    """边界情况测试"""

    def setUp(self):
        """测试准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.whitelist = WhitelistManager(self.temp_dir)
        self.parser = CodeParser(self.whitelist)

    def tearDown(self):
        """清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _parse_code(self, code, filename):
        """辅助方法：解析代码"""
        test_file = os.path.join(self.temp_dir, filename)
        with open(test_file, 'w') as f:
            f.write(code)
        result = self.parser.parse_file(test_file)
        return result.symbols

    def test_empty_file(self):
        """测试空文件"""
        symbols = self._parse_code("", "test.h")
        self.assertEqual(len(symbols), 0)

        symbols = self._parse_code("", "test.swift")
        self.assertEqual(len(symbols), 0)

    def test_only_comments(self):
        """测试只有注释的文件"""
        code = '''
// This is a comment
/* This is another comment */
'''
        symbols = self._parse_code(code, "test.h")
        self.assertEqual(len(symbols), 0)

    def test_invalid_syntax(self):
        """测试语法错误（应该跳过）"""
        code = '''
@interface ValidClass : NSObject
@property NSString *name;
@end

@interface InvalidClass
// Missing inheritance and end
'''
        symbols = self._parse_code(code, "test.h")

        # 应该至少识别ValidClass
        class_symbols = [s for s in symbols if s.type == SymbolType.CLASS]
        self.assertGreaterEqual(len(class_symbols), 1)

    def test_very_long_names(self):
        """测试非常长的名称"""
        long_name = "VeryLongClassNameThatExceedsNormalLengthLimits" * 3
        code = f'''
@interface {long_name} : NSObject
@end
'''
        symbols = self._parse_code(code, "test.h")

        class_symbols = [s for s in symbols if s.type == SymbolType.CLASS]
        self.assertEqual(len(class_symbols), 1)

    def test_special_characters_in_comments(self):
        """测试注释中的特殊字符"""
        code = '''
// Comment with special chars: @interface, @property, class, func
@interface TestClass : NSObject
@end
'''
        symbols = self._parse_code(code, "test.h")

        # 注释中的关键字不应该被识别
        class_symbols = [s for s in symbols if s.type == SymbolType.CLASS]
        self.assertEqual(len(class_symbols), 1)
        self.assertEqual(class_symbols[0].name, "TestClass")


class TestCodeParserPerformance(unittest.TestCase):
    """性能测试"""

    def setUp(self):
        """测试准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.whitelist = WhitelistManager(self.temp_dir)
        self.parser = CodeParser(self.whitelist)

    def tearDown(self):
        """清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_large_file_parsing(self):
        """测试解析大文件"""
        # 生成100个类的代码（减少数量以加快测试）
        classes = []
        for i in range(100):
            classes.append(f'''
@interface TestClass{i} : NSObject
@property NSString *property{i};
- (void)method{i};
@end
''')
        code = '\n'.join(classes)

        test_file = os.path.join(self.temp_dir, "test.h")
        with open(test_file, 'w') as f:
            f.write(code)

        result = self.parser.parse_file(test_file)
        symbols = result.symbols

        # 验证所有符号都被识别
        class_symbols = [s for s in symbols if s.type == SymbolType.CLASS]
        property_symbols = [s for s in symbols if s.type == SymbolType.PROPERTY]
        method_symbols = [s for s in symbols if s.type == SymbolType.METHOD]

        self.assertEqual(len(class_symbols), 100)
        self.assertEqual(len(property_symbols), 100)
        self.assertEqual(len(method_symbols), 100)

    def test_deep_nesting(self):
        """测试深度嵌套"""
        code = '''
@interface Level1 : NSObject
@end

@implementation Level1
- (void)method1 {
    if (true) {
        if (true) {
            if (true) {
                NSLog(@"Deep nesting");
            }
        }
    }
}
@end
'''
        test_file = os.path.join(self.temp_dir, "test.m")
        with open(test_file, 'w') as f:
            f.write(code)

        result = self.parser.parse_file(test_file)
        symbols = result.symbols

        # 应该正常处理深度嵌套
        class_symbols = [s for s in symbols if s.type == SymbolType.CLASS]
        self.assertEqual(len(class_symbols), 1)


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加所有测试类
    suite.addTests(loader.loadTestsFromTestCase(TestCodeParserObjC))
    suite.addTests(loader.loadTestsFromTestCase(TestCodeParserSwift))
    suite.addTests(loader.loadTestsFromTestCase(TestCodeParserEdgeCases))
    suite.addTests(loader.loadTestsFromTestCase(TestCodeParserPerformance))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result


if __name__ == '__main__':
    print("=" * 70)
    print("代码解析器增强测试")
    print("=" * 70)
    print()

    result = run_tests()

    print()
    print("=" * 70)
    print("测试总结:")
    print("=" * 70)
    print(f"运行测试数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")

    if result.wasSuccessful():
        print("\n✅ 所有测试通过！代码解析器功能正常")
        sys.exit(0)
    else:
        print(f"\n❌ {len(result.failures) + len(result.errors)} 个测试未通过")
        sys.exit(1)
