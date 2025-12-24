"""
Enums and constants
"""
from enum import Enum


class ReportFormat(str, Enum):
    """Report format types"""
    XLSX = "xlsx"
    PDF = "pdf"


class ReportStatus(str, Enum):
    """Report status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
