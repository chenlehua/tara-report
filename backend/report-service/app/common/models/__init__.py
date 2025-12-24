"""
Report Service database models
报告服务专用数据模型
"""
from app.common.models.report import (
    # New RS-prefixed models (Report Service specific)
    RSReport,
    RSReportCover,
    RSReportDefinitions,
    RSReportAsset,
    RSReportAttackTree,
    RSReportTARAResult,
    RSReportImage,
    RSReportStatistics,
    RSGeneratedFile,
    RSGenerationHistory,
    # Backward compatible aliases
    Report,
    ReportCover,
    ReportDefinitions,
    ReportAsset,
    ReportAttackTree,
    ReportTARAResult,
    ReportImage,
    GeneratedReport
)

__all__ = [
    # New RS-prefixed models
    "RSReport",
    "RSReportCover",
    "RSReportDefinitions",
    "RSReportAsset",
    "RSReportAttackTree",
    "RSReportTARAResult",
    "RSReportImage",
    "RSReportStatistics",
    "RSGeneratedFile",
    "RSGenerationHistory",
    # Backward compatible aliases
    "Report",
    "ReportCover",
    "ReportDefinitions",
    "ReportAsset",
    "ReportAttackTree",
    "ReportTARAResult",
    "ReportImage",
    "GeneratedReport"
]
