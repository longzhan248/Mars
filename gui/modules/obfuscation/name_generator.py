"""
名称生成器 - 负责生成混淆后的名称

支持:
1. 多种命名策略(随机/前缀/模式/词典)
2. 确定性混淆(固定种子)
3. 名称唯一性保证
4. 名称长度控制
5. 名称映射管理
6. 增量混淆支持
"""

import random
import string
import hashlib
from typing import Dict, Set, Optional, List, Tuple
from enum import Enum
from dataclasses import dataclass, field
import json


class NamingStrategy(Enum):
    """命名策略"""
    RANDOM = "random"           # 随机生成
    PREFIX = "prefix"           # 前缀+随机
    PATTERN = "pattern"         # 模式替换
    DICTIONARY = "dictionary"   # 词典生成


@dataclass
class NameMapping:
    """名称映射"""
    original: str               # 原始名称
    obfuscated: str            # 混淆后名称
    type: str                   # 类型: class/method/property/parameter
    source_file: str = ""       # 来源文件
    line_number: int = 0        # 行号
    confidence: float = 1.0     # 映射置信度

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'original': self.original,
            'obfuscated': self.obfuscated,
            'type': self.type,
            'source_file': self.source_file,
            'line_number': self.line_number,
            'confidence': self.confidence
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'NameMapping':
        """从字典创建"""
        return cls(
            original=data['original'],
            obfuscated=data['obfuscated'],
            type=data['type'],
            source_file=data.get('source_file', ''),
            line_number=data.get('line_number', 0),
            confidence=data.get('confidence', 1.0)
        )


class NameGenerator:
    """名称生成器"""

    # 常用词典（用于词典模式）
    ENGLISH_WORDS = [
        # 动物
        'Tiger', 'Lion', 'Bear', 'Wolf', 'Fox', 'Eagle', 'Hawk', 'Falcon',
        'Panther', 'Jaguar', 'Leopard', 'Cheetah', 'Dragon', 'Phoenix',

        # 自然
        'Mountain', 'River', 'Ocean', 'Forest', 'Desert', 'Valley', 'Peak',
        'Storm', 'Thunder', 'Lightning', 'Cloud', 'Rain', 'Snow', 'Wind',

        # 颜色
        'Red', 'Blue', 'Green', 'Yellow', 'Purple', 'Orange', 'Black', 'White',
        'Silver', 'Golden', 'Crimson', 'Azure', 'Emerald', 'Amber',

        # 动词
        'Run', 'Jump', 'Fly', 'Swim', 'Climb', 'Walk', 'Dance', 'Sing',
        'Fight', 'Defend', 'Attack', 'Guard', 'Protect', 'Build',

        # 形容词
        'Fast', 'Strong', 'Brave', 'Swift', 'Quick', 'Mighty', 'Fierce',
        'Bold', 'Wise', 'Smart', 'Clever', 'Sharp', 'Bright', 'Dark',

        # 其他
        'Master', 'Chief', 'King', 'Queen', 'Lord', 'Lady', 'Knight',
        'Warrior', 'Hunter', 'Ranger', 'Guard', 'Keeper', 'Warden',
    ]

    def __init__(self,
                 strategy: NamingStrategy = NamingStrategy.RANDOM,
                 prefix: str = "WHC",
                 pattern: str = "{prefix}{type}{index}",
                 min_length: int = 8,
                 max_length: int = 20,
                 seed: Optional[str] = None):
        """
        初始化名称生成器

        Args:
            strategy: 命名策略
            prefix: 名称前缀
            pattern: 名称模式
            min_length: 最小长度
            max_length: 最大长度
            seed: 固定种子(用于确定性混淆)
        """
        self.strategy = strategy
        self.prefix = prefix
        self.pattern = pattern
        self.min_length = min_length
        self.max_length = max_length

        # 确定性混淆：使用固定种子
        if seed:
            self.random = random.Random(seed)
            self.seed = seed
        else:
            self.random = random.Random()
            self.seed = None

        # 已生成的名称集合（保证唯一性）
        self.generated_names: Set[str] = set()

        # 名称映射表
        self.mappings: Dict[str, NameMapping] = {}

        # 类型计数器（用于模式生成）
        self.type_counters: Dict[str, int] = {}

        # 词典索引（用于词典模式）
        self.dictionary_index = 0

    def generate(self, original_name: str, name_type: str) -> str:
        """
        生成混淆名称

        Args:
            original_name: 原始名称
            name_type: 类型 (class/method/property/parameter/variable)

        Returns:
            str: 混淆后的名称
        """
        # 检查是否已生成过
        if original_name in self.mappings:
            return self.mappings[original_name].obfuscated

        # 根据策略生成名称
        if self.strategy == NamingStrategy.RANDOM:
            new_name = self._generate_random(name_type)
        elif self.strategy == NamingStrategy.PREFIX:
            new_name = self._generate_with_prefix(name_type)
        elif self.strategy == NamingStrategy.PATTERN:
            new_name = self._generate_with_pattern(original_name, name_type)
        elif self.strategy == NamingStrategy.DICTIONARY:
            new_name = self._generate_from_dictionary(name_type)
        else:
            new_name = self._generate_random(name_type)

        # 保证唯一性
        new_name = self._ensure_unique(new_name)

        # 记录映射
        mapping = NameMapping(
            original=original_name,
            obfuscated=new_name,
            type=name_type
        )
        self.mappings[original_name] = mapping
        self.generated_names.add(new_name)

        return new_name

    def _generate_random(self, name_type: str) -> str:
        """生成随机名称"""
        # 计算目标长度
        length = self.random.randint(self.min_length, self.max_length)

        # 生成字符集：字母+数字
        chars = string.ascii_letters
        if length > 3:  # 允许数字（但不在开头）
            name = self.random.choice(string.ascii_letters)
            name += ''.join(self.random.choices(chars + string.digits, k=length-1))
        else:
            name = ''.join(self.random.choices(chars, k=length))

        # 首字母大写（遵循命名规范）
        if name_type in ['class', 'protocol', 'enum']:
            name = name[0].upper() + name[1:]
        else:
            name = name[0].lower() + name[1:]

        return name

    def _generate_with_prefix(self, name_type: str) -> str:
        """生成带前缀的名称"""
        # 生成随机部分
        random_length = max(self.min_length - len(self.prefix), 4)
        random_part = ''.join(self.random.choices(
            string.ascii_letters + string.digits,
            k=random_length
        ))

        name = self.prefix + random_part

        # 首字母处理
        if name_type in ['class', 'protocol', 'enum']:
            # 类名：首字母大写
            name = name[0].upper() + name[1:]
        else:
            # 方法/属性：首字母小写
            if len(self.prefix) > 0:
                name = self.prefix[0].lower() + self.prefix[1:] + random_part

        return name

    def _generate_with_pattern(self, original_name: str, name_type: str) -> str:
        """使用模式生成名称"""
        # 获取类型计数
        if name_type not in self.type_counters:
            self.type_counters[name_type] = 0
        self.type_counters[name_type] += 1

        # 类型简写
        type_abbr = {
            'class': 'C',
            'method': 'M',
            'property': 'P',
            'parameter': 'A',
            'variable': 'V',
            'protocol': 'T',
            'enum': 'E',
            'constant': 'K',
        }.get(name_type, 'X')

        # 替换模式变量
        name = self.pattern
        name = name.replace('{prefix}', self.prefix)
        name = name.replace('{type}', type_abbr)
        name = name.replace('{index}', str(self.type_counters[name_type]))

        # 如果模式中包含{hash}，使用原名称的哈希
        if '{hash}' in name:
            hash_value = hashlib.md5(original_name.encode()).hexdigest()[:6]
            name = name.replace('{hash}', hash_value)

        # 如果模式中包含{random}，添加随机部分
        if '{random}' in name:
            random_part = ''.join(self.random.choices(string.ascii_letters, k=4))
            name = name.replace('{random}', random_part)

        return name

    def _generate_from_dictionary(self, name_type: str) -> str:
        """从词典生成名称"""
        # 选择一个或多个单词组合
        word_count = self.random.randint(1, 2)
        words = self.random.sample(self.ENGLISH_WORDS, word_count)

        name = ''.join(words)

        # 添加数字后缀以增加唯一性
        if len(name) < self.min_length:
            name += str(self.random.randint(1, 999))

        # 首字母处理
        if name_type in ['class', 'protocol', 'enum']:
            name = name[0].upper() + name[1:]
        else:
            name = name[0].lower() + name[1:]

        return name

    def _ensure_unique(self, name: str, max_retries: int = 100) -> str:
        """
        确保名称唯一性 - P1修复: 增强唯一性验证

        修复:
        - 添加重试次数限制
        - 优化冲突检测性能
        - 提供警告信息

        Args:
            name: 候选名称
            max_retries: 最大重试次数

        Returns:
            str: 唯一的名称

        Raises:
            RuntimeError: 如果无法生成唯一名称
        """
        # 快速路径：名称已经唯一
        if name not in self.generated_names:
            return name

        # P1修复: 记录冲突
        original_name = name
        print(f"⚠️  检测到名称重复: {name}")

        # 策略1: 添加数字后缀（最多100次尝试）
        for counter in range(1, max_retries + 1):
            candidate = f"{name}{counter}"
            if candidate not in self.generated_names:
                if counter <= 3:
                    # 轻微冲突，不打印
                    pass
                else:
                    print(f"   尝试第{counter}次: {candidate}")
                return candidate

        # 策略2: 如果数字后缀用尽，使用随机字符串
        print(f"   ⚠️  数字后缀用尽，切换到随机字符串策略")
        for attempt in range(max_retries):
            random_suffix = ''.join(self.random.choices(string.ascii_letters, k=4))
            candidate = f"{name}_{random_suffix}"
            if candidate not in self.generated_names:
                print(f"   ✅ 使用随机后缀: {candidate}")
                return candidate

        # 策略3: 最后手段 - 使用时间戳
        import time
        timestamp_suffix = str(int(time.time() * 1000))[-8:]
        candidate = f"{name}_{timestamp_suffix}"

        if candidate not in self.generated_names:
            print(f"   ⚠️  使用时间戳后缀: {candidate}")
            return candidate

        # 如果还是失败，抛出异常
        raise RuntimeError(
            f"无法为 '{original_name}' 生成唯一名称，"
            f"已尝试 {max_retries * 2} 次。"
            f"当前已生成 {len(self.generated_names)} 个名称。"
        )

    def reverse_lookup(self, obfuscated_name: str) -> Optional[str]:
        """
        反向查找原始名称

        Args:
            obfuscated_name: 混淆后的名称

        Returns:
            Optional[str]: 原始名称，如果找不到返回None
        """
        for original, mapping in self.mappings.items():
            if mapping.obfuscated == obfuscated_name:
                return original
        return None

    def get_mapping(self, original_name: str) -> Optional[NameMapping]:
        """获取名称映射"""
        return self.mappings.get(original_name)

    def get_all_mappings(self) -> List[NameMapping]:
        """获取所有映射"""
        return list(self.mappings.values())

    def export_mappings(self, filepath: str, format: str = 'json'):
        """
        导出名称映射

        Args:
            filepath: 输出文件路径
            format: 输出格式 (json/csv)
        """
        if format == 'json':
            self._export_json(filepath)
        elif format == 'csv':
            self._export_csv(filepath)
        else:
            raise ValueError(f"不支持的格式: {format}")

    def _export_json(self, filepath: str):
        """导出为JSON格式"""
        data = {
            'metadata': {
                'strategy': self.strategy.value,
                'prefix': self.prefix,
                'seed': self.seed,
                'total_mappings': len(self.mappings)
            },
            'mappings': [m.to_dict() for m in self.mappings.values()]
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _export_csv(self, filepath: str):
        """导出为CSV格式"""
        import csv

        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Original', 'Obfuscated', 'Type', 'SourceFile', 'LineNumber'])

            for mapping in self.mappings.values():
                writer.writerow([
                    mapping.original,
                    mapping.obfuscated,
                    mapping.type,
                    mapping.source_file,
                    mapping.line_number
                ])

    def import_mappings(self, filepath: str) -> int:
        """
        导入名称映射（用于增量混淆）

        Args:
            filepath: 映射文件路径

        Returns:
            int: 导入的映射数量
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            count = 0
            for mapping_dict in data.get('mappings', []):
                mapping = NameMapping.from_dict(mapping_dict)
                self.mappings[mapping.original] = mapping
                self.generated_names.add(mapping.obfuscated)
                count += 1

            return count

        except Exception as e:
            raise RuntimeError(f"导入映射失败: {e}")

    def incremental_mapping(self, old_mapping_file: str,
                          new_symbols: Dict[str, List[str]]) -> Tuple[int, int]:
        """
        增量混淆映射

        Args:
            old_mapping_file: 旧映射文件路径
            new_symbols: 新增符号 {"classes": [...], "methods": [...], ...}

        Returns:
            Tuple[int, int]: (保持的映射数, 新增的映射数)
        """
        # 加载旧映射
        kept_count = self.import_mappings(old_mapping_file)

        # 为新符号生成映射
        new_count = 0
        for symbol_type, symbols in new_symbols.items():
            for symbol in symbols:
                if symbol not in self.mappings:
                    self.generate(symbol, symbol_type.rstrip('s'))  # classes -> class
                    new_count += 1

        return kept_count, new_count

    def get_statistics(self) -> Dict[str, any]:
        """获取生成统计信息"""
        type_counts = {}
        for mapping in self.mappings.values():
            type_counts[mapping.type] = type_counts.get(mapping.type, 0) + 1

        return {
            'total_mappings': len(self.mappings),
            'strategy': self.strategy.value,
            'prefix': self.prefix,
            'has_seed': self.seed is not None,
            'type_distribution': type_counts,
            'average_name_length': sum(len(m.obfuscated) for m in self.mappings.values()) / len(self.mappings) if self.mappings else 0
        }

    def clear(self):
        """清除所有映射和生成的名称"""
        self.generated_names.clear()
        self.mappings.clear()
        self.type_counters.clear()
        self.dictionary_index = 0


class BatchNameGenerator:
    """批量名称生成器（用于并行处理）"""

    def __init__(self, base_generator: NameGenerator):
        """
        基于基础生成器创建批量生成器

        Args:
            base_generator: 基础名称生成器
        """
        self.base_generator = base_generator
        self.batch_mappings: List[NameMapping] = []

    def generate_batch(self, symbols: Dict[str, List[str]]) -> Dict[str, str]:
        """
        批量生成混淆名称

        Args:
            symbols: {"classes": [...], "methods": [...], ...}

        Returns:
            Dict[str, str]: {original: obfuscated}
        """
        result = {}

        for symbol_type, symbol_list in symbols.items():
            # 去掉复数形式: classes -> class
            name_type = symbol_type.rstrip('s')

            for symbol in symbol_list:
                obfuscated = self.base_generator.generate(symbol, name_type)
                result[symbol] = obfuscated

                # 记录批量映射
                mapping = self.base_generator.get_mapping(symbol)
                if mapping:
                    self.batch_mappings.append(mapping)

        return result

    def get_batch_mappings(self) -> List[NameMapping]:
        """获取批量映射记录"""
        return self.batch_mappings


if __name__ == "__main__":
    # 测试代码
    print("=== 名称生成器测试 ===\n")

    # 1. 随机策略测试
    print("1. 随机策略:")
    random_gen = NameGenerator(
        strategy=NamingStrategy.RANDOM,
        min_length=8,
        max_length=12,
        seed="test_seed"  # 固定种子，保证可重现
    )

    test_symbols = [
        ('MyViewController', 'class'),
        ('userName', 'property'),
        ('loadData', 'method'),
        ('index', 'parameter'),
    ]

    for original, symbol_type in test_symbols:
        obfuscated = random_gen.generate(original, symbol_type)
        print(f"  {original} ({symbol_type}) -> {obfuscated}")

    # 2. 前缀策略测试
    print("\n2. 前缀策略:")
    prefix_gen = NameGenerator(
        strategy=NamingStrategy.PREFIX,
        prefix="WHC",
        seed="test_seed"
    )

    for original, symbol_type in test_symbols[:2]:
        obfuscated = prefix_gen.generate(original, symbol_type)
        print(f"  {original} -> {obfuscated}")

    # 3. 模式策略测试
    print("\n3. 模式策略:")
    pattern_gen = NameGenerator(
        strategy=NamingStrategy.PATTERN,
        pattern="{prefix}{type}{index}",
        prefix="APP"
    )

    for original, symbol_type in test_symbols:
        obfuscated = pattern_gen.generate(original, symbol_type)
        print(f"  {original} -> {obfuscated}")

    # 4. 词典策略测试
    print("\n4. 词典策略:")
    dict_gen = NameGenerator(
        strategy=NamingStrategy.DICTIONARY,
        seed="test_seed"
    )

    for original, symbol_type in test_symbols[:3]:
        obfuscated = dict_gen.generate(original, symbol_type)
        print(f"  {original} -> {obfuscated}")

    # 5. 确定性测试（相同种子应产生相同结果）
    print("\n5. 确定性测试:")
    gen1 = NameGenerator(strategy=NamingStrategy.RANDOM, seed="fixed_seed")
    gen2 = NameGenerator(strategy=NamingStrategy.RANDOM, seed="fixed_seed")

    name1_1 = gen1.generate("TestClass", "class")
    name1_2 = gen1.generate("TestMethod", "method")

    name2_1 = gen2.generate("TestClass", "class")
    name2_2 = gen2.generate("TestMethod", "method")

    print(f"  生成器1: TestClass -> {name1_1}, TestMethod -> {name1_2}")
    print(f"  生成器2: TestClass -> {name2_1}, TestMethod -> {name2_2}")
    print(f"  结果一致: {name1_1 == name2_1 and name1_2 == name2_2}")

    # 6. 映射导出测试
    print("\n6. 映射导出:")
    export_file = "/tmp/test_mapping.json"
    random_gen.export_mappings(export_file, format='json')
    print(f"  已导出到: {export_file}")

    # 7. 统计信息
    print("\n7. 生成统计:")
    stats = random_gen.get_statistics()
    print(f"  总映射数: {stats['total_mappings']}")
    print(f"  策略: {stats['strategy']}")
    print(f"  平均名称长度: {stats['average_name_length']:.1f}")
    print(f"  类型分布: {stats['type_distribution']}")

    # 8. 批量生成测试
    print("\n8. 批量生成:")
    batch_gen = BatchNameGenerator(random_gen)
    batch_symbols = {
        'classes': ['UserManager', 'DataService'],
        'methods': ['fetchData', 'saveData'],
        'properties': ['isLoading', 'errorMessage']
    }
    batch_result = batch_gen.generate_batch(batch_symbols)
    print(f"  批量生成了 {len(batch_result)} 个名称")
    for orig, obf in list(batch_result.items())[:3]:
        print(f"    {orig} -> {obf}")

    print("\n=== 测试完成 ===")
