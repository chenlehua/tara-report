"""
API路由定义
"""
import io
import httpx
from datetime import datetime
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..common.database import get_db
from ..common.minio_client import get_minio_client
from ..config import settings
from ..repositories.report import ReportRepository
from ..services.report import ReportService

router = APIRouter()


def get_report_service(db: Session = Depends(get_db)) -> ReportService:
    """获取报告服务实例"""
    repo = ReportRepository(db)
    return ReportService(repo)


@router.get("/")
async def root():
    """API根路径"""
    return {
        "name": "TARA Report Service",
        "version": "1.0.0",
        "status": "running"
    }


@router.get("/api/health")
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
            resp = await client.get(f"{settings.DATA_SERVICE_URL}/api/health")
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


@router.post("/api/reports/{report_id}/generate")
async def generate_report(
    report_id: str,
    format: str = "xlsx",
    service: ReportService = Depends(get_report_service)
):
    """生成报告"""
    try:
        result = await service.generate_report(report_id, format)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/reports/{report_id}/download/{format}")
async def download_report_with_format(
    report_id: str,
    format: str,
    service: ReportService = Depends(get_report_service)
):
    """下载报告（格式作为路径参数）"""
    try:
        content, filename, content_type = service.download_report(report_id, format)
        encoded_filename = quote(filename, safe='')
        return StreamingResponse(
            io.BytesIO(content),
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/api/reports/{report_id}/download")
async def download_report(
    report_id: str,
    format: str = "xlsx",
    service: ReportService = Depends(get_report_service)
):
    """下载报告（格式作为查询参数）"""
    try:
        content, filename, content_type = service.download_report(report_id, format)
        encoded_filename = quote(filename, safe='')
        return StreamingResponse(
            io.BytesIO(content),
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/api/reports/{report_id}/preview")
async def preview_report(
    report_id: str,
    service: ReportService = Depends(get_report_service)
):
    """获取报告预览数据"""
    try:
        return await service.get_preview_data(report_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/reports/{report_id}/status")
async def get_report_status(
    report_id: str,
    db: Session = Depends(get_db)
):
    """获取报告状态"""
    repo = ReportRepository(db)
    report = repo.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    generated_files = repo.get_generated_reports(report_id)
    
    return {
        "report_id": report_id,
        "status": report.status,
        "created_at": report.created_at.isoformat(),
        "generated_files": [
            {
                "type": gf.file_type,
                "size": gf.file_size,
                "generated_at": gf.generated_at.isoformat() if gf.generated_at else None
            }
            for gf in generated_files
        ]
    }
