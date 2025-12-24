"""
健康检查端点
"""
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.common.database import get_db, get_minio_client

router = APIRouter()


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    健康检查
    """
    # 检查数据库连接
    try:
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    # 检查MinIO连接
    try:
        minio = get_minio_client()
        minio_status = "healthy"
    except Exception as e:
        minio_status = f"unhealthy: {str(e)}"
    
    overall_status = "healthy" if db_status == "healthy" and minio_status == "healthy" else "degraded"
    
    return {
        "status": overall_status,
        "timestamp": datetime.now().isoformat(),
        "services": {
            "database": db_status,
            "minio": minio_status
        }
    }
