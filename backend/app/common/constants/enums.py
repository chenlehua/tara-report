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


class StrideModel(str, Enum):
    """STRIDE威胁模型枚举"""
    SPOOFING = "S欺骗"
    TAMPERING = "T篡改"
    REPUDIATION = "R抵赖"
    INFORMATION_DISCLOSURE = "I信息泄露"
    DENIAL_OF_SERVICE = "D拒绝服务"
    ELEVATION_OF_PRIVILEGE = "E权限提升"


class AttackVector(str, Enum):
    """攻击向量枚举"""
    NETWORK = "网络"
    ADJACENT = "邻居"
    LOCAL = "本地"
    PHYSICAL = "物理"


class AttackComplexity(str, Enum):
    """攻击复杂度枚举"""
    LOW = "低"
    HIGH = "高"


class PrivilegesRequired(str, Enum):
    """权限要求枚举"""
    NONE = "无"
    LOW = "低"
    HIGH = "高"


class UserInteraction(str, Enum):
    """用户交互枚举"""
    NOT_REQUIRED = "不需要"
    REQUIRED = "需要"


class ImpactLevel(str, Enum):
    """影响等级枚举"""
    NEGLIGIBLE = "可忽略不计的"
    MODERATE = "中等的"
    MAJOR = "重大的"
    SEVERE = "严重的"


class RiskLevel(str, Enum):
    """风险等级枚举"""
    QM = "QM"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"
