#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI分析结果缓存系统

避免重复分析相同日志,提升响应速度并节省API成本。

核心功能:
1. 基于日志内容哈希的智能缓存
2. LRU淘汰策略 (最近最少使用)
3. 持久化存储 (JSON格式)
4. 相似日志匹配 (模糊查找)
5. 缓存统计与管理
"""

import hashlib
import json
import os
from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict, field


@dataclass
class CacheEntry:
    """缓存条目"""
    query_hash: str                 # 查询哈希
    query_text: str                 # 原始查询文本 (用于调试)
    ai_response: str                # AI响应结果
    problem_type: str = ""          # 问题类型
    timestamp: datetime = field(default_factory=datetime.now)  # 创建时间
    hit_count: int = 0              # 命中次数
    last_accessed: datetime = field(default_factory=datetime.now)  # 最后访问时间
    metadata: Dict = field(default_factory=dict)  # 额外元数据

    def to_dict(self) -> Dict:
        """转换为字典 (用于JSON序列化)"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['last_accessed'] = self.last_accessed.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> 'CacheEntry':
        """从字典创建 (用于JSON反序列化)"""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        data['last_accessed'] = datetime.fromisoformat(data['last_accessed'])
        return cls(**data)


class AnalysisCache:
    """
    AI分析结果缓存管理器

    使用示例:
        cache = AnalysisCache(max_size=100)

        # 查询缓存
        result = cache.get("分析这条日志...")
        if result:
            print("缓存命中!")
        else:
            # 调用AI
            result = ai_client.ask("分析这条日志...")
            # 保存到缓存
            cache.put("分析这条日志...", result, problem_type="崩溃")

        # 持久化
        cache.save_to_file("ai_cache.json")
    """

    def __init__(self, max_size: int = 200, cache_file: str = None):
        """
        初始化缓存管理器

        Args:
            max_size: 最大缓存条目数 (LRU淘汰)
            cache_file: 持久化文件路径 (可选)
        """
        self.max_size = max_size
        self.cache_file = cache_file

        # 使用OrderedDict实现LRU缓存
        # key: query_hash, value: CacheEntry
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()

        # 统计信息
        self.stats = {
            'total_queries': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'evictions': 0,
        }

        # 如果提供了缓存文件,尝试加载
        if cache_file and os.path.exists(cache_file):
            self.load_from_file(cache_file)

    def get(self, query: str, similarity_threshold: float = 0.9) -> Optional[str]:
        """
        从缓存获取结果

        Args:
            query: 查询文本
            similarity_threshold: 相似度阈值 (0-1),用于模糊匹配

        Returns:
            AI响应结果,如果不存在返回None
        """
        self.stats['total_queries'] += 1

        # 计算查询哈希
        query_hash = self._compute_hash(query)

        # 精确匹配
        if query_hash in self.cache:
            entry = self.cache[query_hash]
            entry.hit_count += 1
            entry.last_accessed = datetime.now()

            # 移动到末尾 (LRU)
            self.cache.move_to_end(query_hash)

            self.stats['cache_hits'] += 1
            return entry.ai_response

        # 模糊匹配 (可选)
        if similarity_threshold < 1.0:
            similar_entry = self._find_similar(query, similarity_threshold)
            if similar_entry:
                similar_entry.hit_count += 1
                similar_entry.last_accessed = datetime.now()
                self.stats['cache_hits'] += 1
                return similar_entry.ai_response

        # 未命中
        self.stats['cache_misses'] += 1
        return None

    def put(self, query: str, response: str, problem_type: str = "", **metadata):
        """
        添加到缓存

        Args:
            query: 查询文本
            response: AI响应结果
            problem_type: 问题类型
            **metadata: 额外元数据
        """
        query_hash = self._compute_hash(query)

        # 创建缓存条目
        entry = CacheEntry(
            query_hash=query_hash,
            query_text=query[:200],  # 截断保存
            ai_response=response,
            problem_type=problem_type,
            metadata=metadata
        )

        # 添加到缓存
        self.cache[query_hash] = entry
        self.cache.move_to_end(query_hash)

        # LRU淘汰
        if len(self.cache) > self.max_size:
            evicted_key, _ = self.cache.popitem(last=False)
            self.stats['evictions'] += 1

    def invalidate(self, query: str):
        """
        使缓存失效

        Args:
            query: 查询文本
        """
        query_hash = self._compute_hash(query)
        if query_hash in self.cache:
            del self.cache[query_hash]

    def clear(self):
        """清空缓存"""
        self.cache.clear()
        self.stats['evictions'] += len(self.cache)

    def cleanup_expired(self, max_age_hours: int = 24):
        """
        清理过期缓存

        Args:
            max_age_hours: 最大保留时间 (小时)
        """
        now = datetime.now()
        expired_keys = []

        for key, entry in self.cache.items():
            age = now - entry.timestamp
            if age > timedelta(hours=max_age_hours):
                expired_keys.append(key)

        for key in expired_keys:
            del self.cache[key]
            self.stats['evictions'] += 1

        return len(expired_keys)

    def save_to_file(self, filepath: str = None):
        """
        持久化缓存到文件

        Args:
            filepath: 文件路径 (如果为None,使用初始化时的cache_file)
        """
        filepath = filepath or self.cache_file
        if not filepath:
            return

        try:
            data = {
                'version': '1.0',
                'saved_at': datetime.now().isoformat(),
                'stats': self.stats,
                'entries': [entry.to_dict() for entry in self.cache.values()]
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            print(f"✓ 缓存已保存: {len(self.cache)}条 → {filepath}")

        except Exception as e:
            print(f"✗ 保存缓存失败: {e}")

    def load_from_file(self, filepath: str):
        """
        从文件加载缓存

        Args:
            filepath: 文件路径
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 加载统计信息
            if 'stats' in data:
                self.stats.update(data['stats'])

            # 加载缓存条目
            if 'entries' in data:
                for entry_dict in data['entries']:
                    entry = CacheEntry.from_dict(entry_dict)
                    self.cache[entry.query_hash] = entry

            print(f"✓ 缓存已加载: {len(self.cache)}条 ← {filepath}")

        except Exception as e:
            print(f"✗ 加载缓存失败: {e}")

    def get_stats(self) -> Dict:
        """
        获取缓存统计信息

        Returns:
            {
                'total_queries': 总查询数,
                'cache_hits': 缓存命中数,
                'cache_misses': 缓存未命中数,
                'hit_rate': 命中率,
                'size': 当前缓存大小,
                'evictions': 淘汰次数,
            }
        """
        total = self.stats['total_queries']
        hits = self.stats['cache_hits']
        hit_rate = (hits / total * 100) if total > 0 else 0

        return {
            **self.stats,
            'hit_rate': f"{hit_rate:.1f}%",
            'size': len(self.cache),
        }

    def get_top_queries(self, limit: int = 10) -> List[Dict]:
        """
        获取最常查询的问题

        Args:
            limit: 返回数量

        Returns:
            [{query, hit_count, problem_type}] 列表
        """
        sorted_entries = sorted(
            self.cache.values(),
            key=lambda e: e.hit_count,
            reverse=True
        )

        return [{
            'query': entry.query_text,
            'hit_count': entry.hit_count,
            'problem_type': entry.problem_type,
            'last_accessed': entry.last_accessed.isoformat(),
        } for entry in sorted_entries[:limit]]

    def _compute_hash(self, text: str) -> str:
        """
        计算文本哈希

        使用SHA256并截断为16位,平衡性能和冲突率。
        """
        # 归一化: 去除空白、转小写
        normalized = ''.join(text.split()).lower()

        # SHA256哈希
        hash_obj = hashlib.sha256(normalized.encode('utf-8'))

        # 返回前16位十六进制
        return hash_obj.hexdigest()[:16]

    def _find_similar(self, query: str, threshold: float) -> Optional[CacheEntry]:
        """
        查找相似查询 (简单实现,基于共同词数量)

        Args:
            query: 查询文本
            threshold: 相似度阈值

        Returns:
            相似的缓存条目,如果不存在返回None
        """
        query_words = set(query.lower().split())

        best_match = None
        best_score = 0.0

        for entry in self.cache.values():
            entry_words = set(entry.query_text.lower().split())

            # 计算Jaccard相似度
            intersection = len(query_words & entry_words)
            union = len(query_words | entry_words)

            if union == 0:
                continue

            similarity = intersection / union

            if similarity >= threshold and similarity > best_score:
                best_score = similarity
                best_match = entry

        return best_match


# 全局缓存实例 (可选)
_global_cache: Optional[AnalysisCache] = None


def get_global_cache(cache_file: str = None) -> AnalysisCache:
    """
    获取全局缓存实例 (单例模式)

    Args:
        cache_file: 缓存文件路径 (首次调用时设置)

    Returns:
        全局缓存实例
    """
    global _global_cache

    if _global_cache is None:
        # 默认缓存文件路径
        if cache_file is None:
            import tempfile
            cache_dir = os.path.join(tempfile.gettempdir(), 'xinyu_devtools')
            os.makedirs(cache_dir, exist_ok=True)
            cache_file = os.path.join(cache_dir, 'ai_analysis_cache.json')

        _global_cache = AnalysisCache(max_size=200, cache_file=cache_file)

    return _global_cache


# 便捷装饰器
def cached_analysis(cache: AnalysisCache = None):
    """
    缓存装饰器 - 自动缓存AI分析函数的结果

    使用示例:
        @cached_analysis()
        def analyze_log(log_text):
            return ai_client.ask(log_text)

        # 第一次调用AI
        result = analyze_log("某条日志")

        # 第二次直接从缓存返回
        result = analyze_log("某条日志")  # 命中缓存!
    """
    if cache is None:
        cache = get_global_cache()

    def decorator(func):
        def wrapper(query: str, *args, **kwargs):
            # 尝试从缓存获取
            cached_result = cache.get(query)
            if cached_result:
                print(f"✓ 缓存命中: {func.__name__}")
                return cached_result

            # 调用原函数
            result = func(query, *args, **kwargs)

            # 保存到缓存
            cache.put(query, result)

            return result

        return wrapper

    return decorator


# 测试代码
if __name__ == "__main__":
    print("=== AI分析缓存系统测试 ===\n")

    # 创建缓存
    cache = AnalysisCache(max_size=5)

    # 添加一些测试数据
    test_queries = [
        ("分析这条崩溃日志: Exception in thread", "这是一个空指针异常...", "崩溃"),
        ("为什么网络请求失败?", "可能是网络超时...", "网络"),
        ("内存泄漏分析", "检测到内存持续增长...", "内存"),
    ]

    for query, response, ptype in test_queries:
        cache.put(query, response, problem_type=ptype)
        print(f"✓ 已缓存: {ptype} - {query[:30]}...")

    print(f"\n当前缓存大小: {len(cache.cache)}")

    # 测试查询
    print("\n--- 测试缓存查询 ---")
    result = cache.get("分析这条崩溃日志: Exception in thread")
    print(f"精确匹配: {'✓ 命中' if result else '✗ 未命中'}")

    result = cache.get("分析崩溃日志 Exception")
    print(f"模糊匹配: {'✓ 命中' if result else '✗ 未命中'}")

    # 统计信息
    print("\n--- 缓存统计 ---")
    stats = cache.get_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")

    # 持久化测试
    print("\n--- 持久化测试 ---")
    import tempfile
    temp_file = os.path.join(tempfile.gettempdir(), 'test_cache.json')
    cache.save_to_file(temp_file)

    # 加载测试
    cache2 = AnalysisCache()
    cache2.load_from_file(temp_file)
    print(f"加载后缓存大小: {len(cache2.cache)}")

    print("\n✓ 所有测试完成!")
