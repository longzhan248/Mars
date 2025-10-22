"""
资源处理器通用数据结构
"""

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class ProcessResult:
    """处理结果"""
    success: bool
    file_path: str
    operation: str
    error: Optional[str] = None
    details: Dict = field(default_factory=dict)
