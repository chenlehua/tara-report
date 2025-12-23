"""
健康检查端点
"""
import httpx
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from ....common.database import get_db
from ....common.minio_client import get_minio_client
from ....config import settings

router = APIRouter()


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """健康检查"""
    try:
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    try:
        minio = get_minio_client()
        minio_status = "healthy"
    except Exception as e:
        minio_status = f"unhealthy: {str(e)}"
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.DATA_SERVICE_URL}/api/v1/health")
            data_service_status = "healthy" if resp.status_code == 200 else "unhealthy"
    except Exception as e:
        data_service_status = f"unhealthy: {str(e)}"
    
    return {
        "status": "healthy" if all(s == "healthy" for s in [db_status, minio_status, data_service_status]) else "degraded",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "database": db_status,
            "minio": minio_status,
            "data_service": data_service_status
        }
    }
