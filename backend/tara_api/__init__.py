"""
TARA API - 威胁分析和风险评估报告生成服务
"""
from .main import app
from .models import TARAReportData, GenerateReportResponse

__version__ = "1.0.0"
__all__ = ["app", "TARAReportData", "GenerateReportResponse"]
