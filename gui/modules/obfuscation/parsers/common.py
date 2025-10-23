"""
代码解析器通用数据模型
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set


class SymbolType(Enum):
    """符号类型"""
    CLASS = "class"                     # 类
    PROTOCOL = "protocol"               # 协议
    CATEGORY = "category"               # 分类
    EXTENSION = "extension"             # 扩展
    STRUCT = "struct"                   # 结构体
    ENUM = "enum"                       # 枚举
    METHOD = "method"                   # 方法
    PROPERTY = "property"               # 属性
    IVAR = "ivar"                       # 实例变量
    PARAMETER = "parameter"             # 参数
    LOCAL_VAR = "local_var"             # 局部变量
    CONSTANT = "constant"               # 常量
    MACRO = "macro"                     # 宏定义
    TYPEDEF = "typedef"                 # 类型定义


@dataclass
class Symbol:
    """符号信息"""
    name: str                           # 符号名称
    type: SymbolType                    # 符号类型
    file_path: str                      # 所在文件
    line_number: int                    # 行号
    original_line: str = ""             # 原始行内容
    parent: Optional[str] = None        # 父级符号（类名、方法名等）
    access_modifier: str = "public"     # 访问修饰符
    is_static: bool = False             # 是否静态
    return_type: str = ""               # 返回类型（方法）
    parameters: List[str] = field(default_factory=list)  # 参数列表
    references: Set[str] = field(default_factory=set)    # 引用的其他符号


@dataclass
class ParsedFile:
    """解析后的文件信息"""
    file_path: str                      # 文件路径
    language: str                       # 语言（objc/swift）
    symbols: List[Symbol] = field(default_factory=list)
    imports: Set[str] = field(default_factory=set)       # 导入的模块
    forward_declarations: Set[str] = field(default_factory=set)  # 前置声明
