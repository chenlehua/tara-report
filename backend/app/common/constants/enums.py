"""
枚举常量定义
"""
from enum import Enum


class ImageType(str, Enum):
    """图片类型枚举"""
    ITEM_BOUNDARY = "item_boundary"
    SYSTEM_ARCHITECTURE = "system_architecture"
    SOFTWARE_ARCHITECTURE = "software_architecture"
    DATAFLOW = "dataflow"
    ATTACK_TREE = "attack_tree"


class ReportStatus(str, Enum):
    """报告状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
