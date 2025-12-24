"""
Enums and constants
"""
from enum import Enum


class ImageType(str, Enum):
    """Image types"""
    ITEM_BOUNDARY = "item_boundary"
    SYSTEM_ARCHITECTURE = "system_architecture"
    SOFTWARE_ARCHITECTURE = "software_architecture"
    DATAFLOW = "dataflow"
    ATTACK_TREE = "attack_tree"


class ReportStatus(str, Enum):
    """Report status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# Allowed file extensions for images
ALLOWED_IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg'}

# Valid image types
VALID_IMAGE_TYPES = [
    ImageType.ITEM_BOUNDARY.value,
    ImageType.SYSTEM_ARCHITECTURE.value,
    ImageType.SOFTWARE_ARCHITECTURE.value,
    ImageType.DATAFLOW.value,
    ImageType.ATTACK_TREE.value
]
