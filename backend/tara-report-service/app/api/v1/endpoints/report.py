"""
报告生成与下载端点
"""
import io
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ....common.database import get_db
from ....repositories.report import ReportRepository
from ....services.report import ReportService

router = APIRouter()


def get_report_service(db: Session = Depends(get_db)) -> ReportService:
    """获取报告服务实例"""
    repo = ReportRepository(db)
    return ReportService(repo)


@router.post("/reports/{report_id}/generate")
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


@router.get("/reports/{report_id}/download/{format}")
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


@router.get("/reports/{report_id}/download")
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


@router.get("/reports/{report_id}/preview")
async def preview_report(
    report_id: str,
    service: ReportService = Depends(get_report_service)
):
    """获取报告预览数据"""
    try:
        return await service.get_preview_data(report_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/{report_id}/status")
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
