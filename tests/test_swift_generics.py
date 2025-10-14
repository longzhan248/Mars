#!/usr/bin/env python3
"""
Swift泛型解析测试

测试增强后的Swift解析器对泛型语法的支持
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path
import unittest

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from gui.modules.obfuscation.code_parser import CodeParser, SymbolType


class TestSwiftGenerics(unittest.TestCase):
    """Swift泛型解析测试"""

    def setUp(self):
        """测试准备"""
        self.parser = CodeParser()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """清理临时文件"""
        shutil.rmtree(self.temp_dir)

    def test_generic_class(self):
        """测试泛型类解析"""
        swift_code = '''
class DataManager<T> {
    var data: T?

    func store(_ value: T) {
        data = value
    }
}
'''
        temp_file = Path(self.temp_dir) / "GenericClass.swift"
        temp_file.write_text(swift_code)

        parsed = self.parser.parse_file(str(temp_file))
        symbol_names = [s.name for s in parsed.symbols]

        # 验证类名被提取（忽略泛型参数）
        self.assertIn("DataManager", symbol_names, "泛型类名应该被提取")

        # 验证属性和方法被提取
        self.assertIn("data", symbol_names, "泛型类的属性应该被提取")
        self.assertIn("store", symbol_names, "泛型类的方法应该被提取")

    def test_generic_struct(self):
        """测试泛型结构体解析"""
        swift_code = '''
struct Result<Value, Error> {
    let value: Value?
    let error: Error?

    var isSuccess: Bool {
        return error == nil
    }
}
'''
        temp_file = Path(self.temp_dir) / "GenericStruct.swift"
        temp_file.write_text(swift_code)

        parsed = self.parser.parse_file(str(temp_file))
        symbol_names = [s.name for s in parsed.symbols]

        # 验证结构体名被提取
        self.assertIn("Result", symbol_names, "泛型结构体名应该被提取")

        # 验证属性被提取
        self.assertIn("value", symbol_names)
        self.assertIn("error", symbol_names)
        self.assertIn("isSuccess", symbol_names)

    def test_generic_enum(self):
        """测试泛型枚举解析"""
        swift_code = '''
enum Optional<Wrapped> {
    case none
    case some(Wrapped)

    func map<U>(_ transform: (Wrapped) -> U) -> Optional<U> {
        switch self {
        case .none: return .none
        case .some(let value): return .some(transform(value))
        }
    }
}
'''
        temp_file = Path(self.temp_dir) / "GenericEnum.swift"
        temp_file.write_text(swift_code)

        parsed = self.parser.parse_file(str(temp_file))
        symbol_names = [s.name for s in parsed.symbols]

        # 验证枚举名被提取
        self.assertIn("Optional", symbol_names, "泛型枚举名应该被提取")

        # 验证case被提取
        self.assertIn("none", symbol_names)
        self.assertIn("some", symbol_names)

        # 验证泛型方法被提取
        self.assertIn("map", symbol_names, "泛型方法应该被提取")

    def test_generic_extension(self):
        """测试泛型扩展解析"""
        swift_code = '''
extension Array<Int> {
    func sum() -> Int {
        return self.reduce(0, +)
    }
}

extension Dictionary<String, Int> {
    func sortedKeys() -> [String] {
        return self.keys.sorted()
    }
}
'''
        temp_file = Path(self.temp_dir) / "GenericExtension.swift"
        temp_file.write_text(swift_code)

        parsed = self.parser.parse_file(str(temp_file))
        symbol_names = [s.name for s in parsed.symbols]

        # 验证扩展的方法被提取
        self.assertIn("sum", symbol_names, "泛型扩展中的方法应该被提取")
        self.assertIn("sortedKeys", symbol_names)

    def test_generic_method(self):
        """测试泛型方法解析"""
        swift_code = '''
class APIClient {
    func request<T: Codable>(_ endpoint: String) -> T? {
        return nil
    }

    func process<Input, Output>(_ input: Input, transform: (Input) -> Output) -> Output {
        return transform(input)
    }
}
'''
        temp_file = Path(self.temp_dir) / "GenericMethod.swift"
        temp_file.write_text(swift_code)

        parsed = self.parser.parse_file(str(temp_file))
        symbol_names = [s.name for s in parsed.symbols]

        # 验证类名和方法被提取
        self.assertIn("APIClient", symbol_names)
        self.assertIn("request", symbol_names, "带泛型约束的方法应该被提取")
        self.assertIn("process", symbol_names, "多泛型参数的方法应该被提取")

    def test_complex_generic_constraints(self):
        """测试复杂泛型约束"""
        swift_code = '''
class DataStore<T: Codable & Equatable> {
    var items: [T] = []

    func add(_ item: T) {
        items.append(item)
    }

    func contains(_ item: T) -> Bool {
        return items.contains(item)
    }
}
'''
        temp_file = Path(self.temp_dir) / "ComplexGeneric.swift"
        temp_file.write_text(swift_code)

        parsed = self.parser.parse_file(str(temp_file))
        symbol_names = [s.name for s in parsed.symbols]

        # 验证类名被提取（忽略复杂的泛型约束）
        self.assertIn("DataStore", symbol_names)
        self.assertIn("items", symbol_names)
        self.assertIn("add", symbol_names)
        self.assertIn("contains", symbol_names)

    def test_generic_property_types(self):
        """测试带泛型的属性类型"""
        swift_code = '''
class Container<T> {
    var items: Array<T> = []
    var dict: Dictionary<String, T> = [:]
    var optional: Optional<T>?

    func getItems() -> [T] {
        return items
    }
}
'''
        temp_file = Path(self.temp_dir) / "GenericProperty.swift"
        temp_file.write_text(swift_code)

        parsed = self.parser.parse_file(str(temp_file))
        symbol_names = [s.name for s in parsed.symbols]

        # 验证类和属性都被提取
        self.assertIn("Container", symbol_names, "泛型类应该被提取")
        self.assertIn("items", symbol_names, "Array<T>类型的属性应该被提取")
        self.assertIn("dict", symbol_names, "Dictionary<K, V>类型的属性应该被提取")
        self.assertIn("optional", symbol_names, "Optional<T>类型的属性应该被提取")
        self.assertIn("getItems", symbol_names, "返回泛型类型的方法应该被提取")


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestSwiftGenerics)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result


if __name__ == '__main__':
    print("=" * 70)
    print("Swift泛型解析测试")
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
        print("\n🎉 所有测试通过！Swift泛型解析功能正常")
        sys.exit(0)
    else:
        print(f"\n⚠️  {len(result.failures) + len(result.errors)} 个测试未通过")
        sys.exit(1)
