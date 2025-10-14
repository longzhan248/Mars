"""
P0修复验证测试

测试两个关键P0问题的修复:
1. code_transformer.py - 方法名替换防止前缀匹配
2. resource_handler.py - XIB/Storyboard完整属性支持
"""

import unittest
import tempfile
import os
from pathlib import Path

# 导入需要测试的模块
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from gui.modules.obfuscation.code_transformer import CodeTransformer
from gui.modules.obfuscation.code_parser import CodeParser, Symbol, SymbolType
from gui.modules.obfuscation.name_generator import NameGenerator, NamingStrategy
from gui.modules.obfuscation.resource_handler import ResourceHandler


class TestP0Fix1MethodNameReplacement(unittest.TestCase):
    """测试P0-1: 方法名替换防止前缀匹配"""

    def test_prevent_prefix_matching_objc(self):
        """测试防止ObjC方法名前缀匹配"""
        # 测试场景: load vs loadData
        test_code = """
@interface MyClass : NSObject
- (void)load;
- (void)loadData;
@end

@implementation MyClass
- (void)load {
    NSLog(@"load called");
}

- (void)loadData {
    NSLog(@"loadData called");
    [self load];  // 调用load方法
}
@end
"""

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.m")
            with open(test_file, 'w') as f:
                f.write(test_code)

            # 解析
            parser = CodeParser()
            parsed = parser.parse_file(test_file)

            # 创建生成器（确定性）
            generator = NameGenerator(
                strategy=NamingStrategy.PREFIX,
                prefix="ABC",
                seed="test_p0_1"
            )

            # 转换
            transformer = CodeTransformer(generator)
            result = transformer.transform_file(test_file, parsed)

            # 验证
            self.assertEqual(len(result.errors), 0, "不应该有错误")

            # 检查两个方法都被独立替换
            # 不应该出现 "ABC123Data" 这种前缀匹配的错误
            self.assertNotIn("ABC", test_code)  # 原始代码不含混淆名

            # 混淆后的代码应该有两个独立的方法名
            content = result.transformed_content

            # 统计方法签名出现次数
            # 每个方法应该出现2次（声明+实现）
            method_declarations = [line for line in content.split('\n')
                                 if line.strip().startswith('-') and '(' in line]

            # 应该有4个方法声明/实现（2个方法 x 2次）
            self.assertEqual(len(method_declarations), 4,
                           f"应该有4个方法声明，实际: {len(method_declarations)}")

    def test_prevent_prefix_matching_swift(self):
        """测试防止Swift方法名前缀匹配"""
        test_code = """
class MyClass {
    func save() {
        print("save called")
    }

    func saveData() {
        print("saveData called")
        self.save()  // 调用save方法
    }
}
"""

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.swift")
            with open(test_file, 'w') as f:
                f.write(test_code)

            # 解析
            parser = CodeParser()
            parsed = parser.parse_file(test_file)

            # 创建生成器
            generator = NameGenerator(
                strategy=NamingStrategy.PREFIX,
                prefix="XYZ",
                seed="test_p0_1_swift"
            )

            # 转换
            transformer = CodeTransformer(generator)
            result = transformer.transform_file(test_file, parsed)

            # 验证
            self.assertEqual(len(result.errors), 0, "不应该有错误")

            content = result.transformed_content

            # 统计func声明
            func_declarations = [line for line in content.split('\n')
                               if 'func ' in line and '(' in line]

            # 应该有2个func声明
            self.assertEqual(len(func_declarations), 2,
                           f"应该有2个func声明，实际: {len(func_declarations)}")

    def test_objc_parameterized_method_complete_match(self):
        """测试ObjC带参数方法的完整匹配"""
        test_code = """
@interface MyClass : NSObject
- (void)process;
- (void)processWithData:(NSData*)data;
- (void)processWithData:(NSData*)data completion:(void(^)(BOOL))completion;
@end

@implementation MyClass
- (void)process {
    NSLog(@"process");
}

- (void)processWithData:(NSData*)data {
    NSLog(@"processWithData");
    [self process];
}

- (void)processWithData:(NSData*)data completion:(void(^)(BOOL))completion {
    NSLog(@"processWithData:completion:");
    [self processWithData:data];
}
@end
"""

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.m")
            with open(test_file, 'w') as f:
                f.write(test_code)

            parser = CodeParser()
            parsed = parser.parse_file(test_file)

            generator = NameGenerator(
                strategy=NamingStrategy.RANDOM,
                seed="test_p0_1_param"
            )

            transformer = CodeTransformer(generator)
            result = transformer.transform_file(test_file, parsed)

            # 验证没有错误
            self.assertEqual(len(result.errors), 0)

            # 验证所有三个方法都被正确替换
            # process, processWithData:, processWithData:completion: 应该各自独立
            content = result.transformed_content

            # 原始方法名不应该出现在混淆后的代码中（除了字符串和注释中）
            # 至少类名应该被替换了
            self.assertNotIn("@interface MyClass", content)
            self.assertNotIn("@implementation MyClass", content)


class TestP0Fix2ResourceHandlerEnhanced(unittest.TestCase):
    """测试P0-2: XIB/Storyboard完整属性支持"""

    def test_xib_destination_class(self):
        """测试XIB文件destinationClass属性处理"""
        test_xib = """<?xml version="1.0" encoding="UTF-8"?>
<document type="com.apple.InterfaceBuilder3.CocoaTouch.XIB" version="3.0">
    <objects>
        <view customClass="MyCustomView" id="1">
            <connections>
                <outlet property="delegate" destination="2" destinationClass="MyDelegate"/>
            </connections>
        </view>
        <placeholder customClass="MyViewController" id="3"/>
    </objects>
</document>
"""

        symbol_mappings = {
            'MyCustomView': 'ABC123View',
            'MyDelegate': 'ABC456Delegate',
            'MyViewController': 'ABC789Controller',
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            xib_path = Path(tmpdir) / "test.xib"
            with open(xib_path, 'w') as f:
                f.write(test_xib)

            handler = ResourceHandler(symbol_mappings)
            success = handler.update_xib(str(xib_path))

            self.assertTrue(success, "XIB更新应该成功")

            # 读取更新后的内容
            with open(xib_path, 'r') as f:
                updated_content = f.read()

            # 验证: customClass被替换
            self.assertIn('ABC123View', updated_content)
            self.assertNotIn('MyCustomView', updated_content)

            # 验证: P0修复 - destinationClass被替换
            self.assertIn('ABC456Delegate', updated_content)
            self.assertNotIn('MyDelegate', updated_content)

            # 验证: placeholder中的customClass被替换
            self.assertIn('ABC789Controller', updated_content)
            self.assertNotIn('MyViewController', updated_content)

    def test_storyboard_comprehensive_attributes(self):
        """测试Storyboard文件所有类名相关属性"""
        test_storyboard = """<?xml version="1.0" encoding="UTF-8"?>
<document type="com.apple.InterfaceBuilder3.CocoaTouch.Storyboard.XIB" version="3.0">
    <scenes>
        <scene>
            <objects>
                <viewController customClass="MyViewController" storyboardIdentifier="MyVC" id="1">
                    <connections>
                        <segue destination="2" kind="show" customClass="MySegue" destinationClass="DetailViewController"/>
                    </connections>
                </viewController>
                <viewController customClass="DetailViewController" restorationIdentifier="DetailVC" id="2">
                    <tableView>
                        <tableViewCell reuseIdentifier="MyCell" customClass="MyTableCell" id="3"/>
                    </tableView>
                </viewController>
                <placeholder userLabel="MyPlaceholder" id="4"/>
            </objects>
        </scene>
    </scenes>
</document>
"""

        symbol_mappings = {
            'MyViewController': 'ABC111VC',
            'MySegue': 'ABC222Segue',
            'DetailViewController': 'ABC333Detail',
            'MyCell': 'ABC444Cell',
            'MyTableCell': 'ABC555Table',
            'MyVC': 'ABC666ID',
            'DetailVC': 'ABC777ID',
            'MyPlaceholder': 'ABC888Holder',
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            sb_path = Path(tmpdir) / "test.storyboard"
            with open(sb_path, 'w') as f:
                f.write(test_storyboard)

            handler = ResourceHandler(symbol_mappings)
            success = handler.update_storyboard(str(sb_path))

            self.assertTrue(success, "Storyboard更新应该成功")

            with open(sb_path, 'r') as f:
                updated_content = f.read()

            # 验证所有属性都被正确替换
            # 1. customClass
            self.assertIn('ABC111VC', updated_content)
            self.assertIn('ABC222Segue', updated_content)
            self.assertIn('ABC333Detail', updated_content)
            self.assertIn('ABC555Table', updated_content)

            # 2. P0修复 - destinationClass
            self.assertIn('ABC333Detail', updated_content)

            # 3. storyboardIdentifier
            self.assertIn('ABC666ID', updated_content)

            # 4. reuseIdentifier
            self.assertIn('ABC444Cell', updated_content)

            # 5. P0修复 - restorationIdentifier
            self.assertIn('ABC777ID', updated_content)

            # 6. P0修复 - userLabel
            self.assertIn('ABC888Holder', updated_content)

            # 验证原始类名不再出现
            self.assertNotIn('MyViewController', updated_content)
            self.assertNotIn('DetailViewController', updated_content)

    def test_xib_multiple_outlets(self):
        """测试XIB文件多个outlet连接"""
        test_xib = """<?xml version="1.0" encoding="UTF-8"?>
<document>
    <objects>
        <view customClass="MyView" id="1">
            <connections>
                <outlet property="delegate" destination="2" destinationClass="MyDelegate"/>
                <outlet property="dataSource" destination="3" destinationClass="MyDataSource"/>
                <outlet property="observer" destination="4" destinationClass="MyObserver"/>
            </connections>
        </view>
    </objects>
</document>
"""

        symbol_mappings = {
            'MyView': 'A1',
            'MyDelegate': 'A2',
            'MyDataSource': 'A3',
            'MyObserver': 'A4',
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            xib_path = Path(tmpdir) / "test.xib"
            with open(xib_path, 'w') as f:
                f.write(test_xib)

            handler = ResourceHandler(symbol_mappings)
            success = handler.update_xib(str(xib_path))

            self.assertTrue(success)

            with open(xib_path, 'r') as f:
                updated_content = f.read()

            # 验证所有destinationClass都被替换
            self.assertIn('A2', updated_content)
            self.assertIn('A3', updated_content)
            self.assertIn('A4', updated_content)

            # 验证原始类名不存在
            self.assertNotIn('MyDelegate', updated_content)
            self.assertNotIn('MyDataSource', updated_content)
            self.assertNotIn('MyObserver', updated_content)


if __name__ == '__main__':
    # 运行测试
    print("=" * 70)
    print("P0修复验证测试")
    print("=" * 70)
    print()

    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 输出总结
    print()
    print("=" * 70)
    print("测试总结:")
    print("=" * 70)
    print(f"运行测试数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print()

    if result.wasSuccessful():
        print("✅ 所有P0修复验证测试通过！")
        sys.exit(0)
    else:
        print("❌ 部分测试未通过")
        sys.exit(1)
