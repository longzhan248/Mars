"""
混淆引擎通用数据模型

包含所有引擎模块共享的数据结构
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class ObfuscationResult:
    """混淆结果"""
    success: bool                               # 是否成功
    output_dir: str                             # 输出目录
    project_name: str                           # 项目名称
    files_processed: int = 0                    # 处理的文件数
    files_failed: int = 0                       # 失败的文件数
    total_replacements: int = 0                 # 总替换次数
    elapsed_time: float = 0.0                   # 耗时（秒）
    mapping_file: str = ""                      # 映射文件路径
    errors: List[str] = field(default_factory=list)  # 错误信息
    warnings: List[str] = field(default_factory=list)  # 警告信息
