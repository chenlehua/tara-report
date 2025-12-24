"""
健康检查API端点
"""
from datetime import datetime

from fastapi import APIRouter

from .images import images_db
from .reports import reports_db

router = APIRouter()


@router.get("")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "reports_count": len(reports_db),
        "images_count": len(images_db)
    }
