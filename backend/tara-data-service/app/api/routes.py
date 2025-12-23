"""
API路由定义
"""
import io
import json
from typing import List
from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..common.database import get_db
from ..common.minio_client import get_minio_client
from ..common.models import ReportImage
from ..config import settings
from ..repositories.report import ReportRepository
from ..services.data import DataService

router = APIRouter()

# 临时图片存储（用于在创建报告前上传图片）
temp_images_db: dict = {}


def get_data_service(db: Session = Depends(get_db)) -> DataService:
    """获取数据服务实例"""
    repo = ReportRepository(db)
    return DataService(repo)


@router.get("/")
async def root():
    """API根路径"""
    return {
        "name": "TARA Data Service",
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
    
    return {
        "status": "healthy" if db_status == "healthy" and minio_status == "healthy" else "degraded",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "database": db_status,
            "minio": minio_status
        }
    }


@router.post("/api/images/upload")
async def upload_image(
    file: UploadFile = File(...),
    image_type: str = Form(..., description="图片类型: item_boundary, system_architecture, software_architecture, dataflow, attack_tree"),
    db: Session = Depends(get_db)
):
    """
    上传图片（临时存储）
    """
    # 验证文件类型
    allowed_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg'}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式。支持的格式: {', '.join(allowed_extensions)}"
        )
    
    # 验证图片类型
    valid_types = ['item_boundary', 'system_architecture', 'software_architecture', 'dataflow', 'attack_tree']
    if image_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"无效的图片类型。有效类型: {', '.join(valid_types)}"
        )
    
    # 生成图片ID
    image_id = DataService.generate_image_id()
    
    # 读取文件内容
    content = await file.read()
    
    # 上传到MinIO（使用临时目录）
    minio = get_minio_client()
    object_name = f"temp/{image_id}{file_ext}"
    
    try:
        minio.upload_bytes(
            settings.BUCKET_IMAGES,
            object_name,
            content,
            file.content_type or "image/png"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")
    
    # 记录临时图片信息
    temp_images_db[image_id] = {
        'id': image_id,
        'type': image_type,
        'filename': f"{image_id}{file_ext}",
        'minio_path': object_name,
        'original_name': file.filename,
        'content_type': file.content_type,
        'file_size': len(content),
        'created_at': datetime.now().isoformat()
    }
    
    return {
        "success": True,
        "message": "图片上传成功",
        "image_id": image_id,
        "image_url": f"/api/images/{image_id}",
        "image_type": image_type
    }


@router.get("/api/images/{image_id}")
async def get_image(image_id: str, db: Session = Depends(get_db)):
    """获取图片"""
    minio = get_minio_client()
    
    # 先从临时存储查找
    if image_id in temp_images_db:
        image_info = temp_images_db[image_id]
        try:
            content = minio.download_file(settings.BUCKET_IMAGES, image_info['minio_path'])
            return StreamingResponse(
                io.BytesIO(content),
                media_type=image_info.get('content_type', 'image/png')
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"获取图片失败: {str(e)}")
    
    # 从数据库查找
    image = db.query(ReportImage).filter(ReportImage.image_id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="图片不存在")
    
    try:
        content = minio.download_file(image.minio_bucket, image.minio_path)
        return StreamingResponse(
            io.BytesIO(content),
            media_type=image.content_type or "image/png"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取图片失败: {str(e)}")


@router.post("/api/reports/upload")
async def upload_report_data(
    json_file: UploadFile = File(None, description="JSON数据文件"),
    json_data: str = Form(None, description="JSON数据字符串"),
    item_boundary_image: UploadFile = File(None),
    system_architecture_image: UploadFile = File(None),
    software_architecture_image: UploadFile = File(None),
    dataflow_image: UploadFile = File(None),
    attack_tree_images: List[UploadFile] = File(None),
    service: DataService = Depends(get_data_service)
):
    """
    上传JSON参数和图片，生成报告ID
    """
    # 解析JSON数据
    report_data = None
    if json_file and json_file.filename:
        try:
            content = await json_file.read()
            report_data = json.loads(content.decode('utf-8'))
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"JSON文件格式错误: {str(e)}")
    elif json_data:
        try:
            report_data = json.loads(json_data)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"JSON数据格式错误: {str(e)}")
    else:
        raise HTTPException(status_code=400, detail="请提供JSON文件或JSON数据")
    
    # 上传报告数据
    result = await service.upload_report_data(
        report_data=report_data,
        item_boundary_image=item_boundary_image,
        system_architecture_image=system_architecture_image,
        software_architecture_image=software_architecture_image,
        dataflow_image=dataflow_image,
        attack_tree_images=attack_tree_images
    )
    
    return {
        "success": True,
        "message": "数据上传成功",
        "report_id": result['report_id'],
        "statistics": result['statistics']
    }


@router.post("/api/upload/batch")
async def upload_batch(
    json_file: UploadFile = File(..., description="JSON数据文件"),
    item_boundary_image: UploadFile = File(None, description="项目边界图"),
    system_architecture_image: UploadFile = File(None, description="系统架构图"),
    software_architecture_image: UploadFile = File(None, description="软件架构图"),
    dataflow_image: UploadFile = File(None, description="数据流图"),
    attack_tree_images: List[UploadFile] = File(None, description="攻击树图片列表"),
    service: DataService = Depends(get_data_service)
):
    """
    批量上传JSON和图片文件，一键生成报告
    """
    # 解析JSON数据
    try:
        content = await json_file.read()
        report_data = json.loads(content.decode('utf-8'))
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"JSON文件格式错误: {str(e)}")
    
    # 上传报告数据
    result = await service.upload_report_data(
        report_data=report_data,
        item_boundary_image=item_boundary_image,
        system_architecture_image=system_architecture_image,
        software_architecture_image=software_architecture_image,
        dataflow_image=dataflow_image,
        attack_tree_images=attack_tree_images
    )
    
    # 触发报告生成
    await service.trigger_report_generation(result['report_id'])
    
    return {
        'success': True,
        'message': '报告生成成功',
        'report_id': result['report_id'],
        'report_info': {
            'id': result['report_id'],
            'name': result['cover_data'].get('report_title', 'TARA报告'),
            'project_name': result['cover_data'].get('project_name', ''),
            'version': result['cover_data'].get('version', '1.0'),
            'created_at': datetime.now().isoformat(),
            'file_path': '',
            'file_size': 0,
            'statistics': result['statistics']
        },
        'download_url': f"/api/reports/{result['report_id']}/download",
        'preview_url': f"/api/reports/{result['report_id']}/preview"
    }


@router.get("/api/reports")
async def list_reports(
    page: int = 1,
    page_size: int = 20,
    service: DataService = Depends(get_data_service)
):
    """获取报告列表"""
    return service.list_reports(page, page_size)


@router.get("/api/reports/{report_id}")
async def get_report_info(
    report_id: str,
    service: DataService = Depends(get_data_service)
):
    """获取报告完整信息（用于预览）"""
    result = service.get_report_info(report_id)
    if not result:
        raise HTTPException(status_code=404, detail="报告不存在")
    return result


@router.get("/api/reports/{report_id}/cover")
async def get_report_cover(
    report_id: str,
    db: Session = Depends(get_db)
):
    """获取报告封面信息"""
    repo = ReportRepository(db)
    cover = repo.get_report_cover(report_id)
    if not cover:
        raise HTTPException(status_code=404, detail="封面信息不存在")
    
    return {
        "report_title": cover.report_title,
        "report_title_en": cover.report_title_en,
        "project_name": cover.project_name,
        "data_level": cover.data_level,
        "document_number": cover.document_number,
        "version": cover.version,
        "author_date": cover.author_date,
        "review_date": cover.review_date,
        "sign_date": cover.sign_date,
        "approve_date": cover.approve_date
    }


@router.get("/api/reports/{report_id}/definitions")
async def get_report_definitions(
    report_id: str,
    db: Session = Depends(get_db)
):
    """获取报告相关定义"""
    repo = ReportRepository(db)
    definitions = repo.get_report_definitions(report_id)
    if not definitions:
        raise HTTPException(status_code=404, detail="相关定义不存在")
    
    return {
        "title": definitions.title,
        "functional_description": definitions.functional_description,
        "item_boundary_image": definitions.item_boundary_image,
        "system_architecture_image": definitions.system_architecture_image,
        "software_architecture_image": definitions.software_architecture_image,
        "dataflow_image": definitions.dataflow_image,
        "assumptions": definitions.assumptions or [],
        "terminology": definitions.terminology or []
    }


@router.get("/api/reports/{report_id}/assets")
async def get_report_assets(
    report_id: str,
    db: Session = Depends(get_db)
):
    """获取报告资产列表"""
    repo = ReportRepository(db)
    definitions = repo.get_report_definitions(report_id)
    dataflow_image = getattr(definitions, 'dataflow_image', None) if definitions else None
    
    assets = repo.get_report_assets(report_id)
    cover = repo.get_report_cover(report_id)
    title_prefix = cover.project_name if cover and cover.project_name else "报告"
    
    return {
        "title": f"{title_prefix} - 资产列表 Asset List",
        "dataflow_image": dataflow_image,
        "assets": [
            {
                "id": asset.asset_id,
                "name": asset.name,
                "category": asset.category,
                "remarks": asset.remarks,
                "authenticity": asset.authenticity,
                "integrity": asset.integrity,
                "non_repudiation": asset.non_repudiation,
                "confidentiality": asset.confidentiality,
                "availability": asset.availability,
                "authorization": asset.authorization
            }
            for asset in assets
        ]
    }


@router.get("/api/reports/{report_id}/attack-trees")
async def get_report_attack_trees(
    report_id: str,
    db: Session = Depends(get_db)
):
    """获取报告攻击树"""
    repo = ReportRepository(db)
    trees = repo.get_report_attack_trees(report_id)
    
    return {
        "title": "攻击树分析 Attack Tree Analysis",
        "attack_trees": [
            {
                "asset_id": tree.asset_id,
                "asset_name": tree.asset_name,
                "title": tree.title,
                "image": tree.image
            }
            for tree in trees
        ]
    }


@router.get("/api/reports/{report_id}/tara-results")
async def get_report_tara_results(
    report_id: str,
    db: Session = Depends(get_db)
):
    """获取TARA分析结果"""
    repo = ReportRepository(db)
    results = repo.get_report_tara_results(report_id)
    
    return {
        "title": "TARA分析结果 TARA Analysis Results",
        "results": [
            {
                "asset_id": r.asset_id,
                "asset_name": r.asset_name,
                "subdomain1": r.subdomain1,
                "subdomain2": r.subdomain2,
                "subdomain3": r.subdomain3,
                "category": r.category,
                "security_attribute": r.security_attribute,
                "stride_model": r.stride_model,
                "threat_scenario": r.threat_scenario,
                "attack_path": r.attack_path,
                "wp29_mapping": r.wp29_mapping,
                "attack_vector": r.attack_vector,
                "attack_complexity": r.attack_complexity,
                "privileges_required": r.privileges_required,
                "user_interaction": r.user_interaction,
                "safety_impact": r.safety_impact,
                "financial_impact": r.financial_impact,
                "operational_impact": r.operational_impact,
                "privacy_impact": r.privacy_impact,
                "security_goal": r.security_goal,
                "security_requirement": r.security_requirement
            }
            for r in results
        ]
    }


@router.get("/api/reports/{report_id}/images/{image_id}")
async def get_report_image(
    report_id: str,
    image_id: str,
    db: Session = Depends(get_db)
):
    """获取报告图片"""
    repo = ReportRepository(db)
    images = repo.get_report_images(report_id)
    image = next((img for img in images if img.image_id == image_id), None)
    
    if not image:
        raise HTTPException(status_code=404, detail="图片不存在")
    
    try:
        minio = get_minio_client()
        content = minio.download_file(image.minio_bucket, image.minio_path)
        return StreamingResponse(
            io.BytesIO(content),
            media_type=image.content_type or "image/png"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取图片失败: {str(e)}")


@router.get("/api/reports/{report_id}/image-by-path")
async def get_image_by_path(
    report_id: str,
    path: str,
    db: Session = Depends(get_db)
):
    """根据MinIO路径获取图片"""
    try:
        minio = get_minio_client()
        # 路径格式: bucket/object_name 或直接是 object_name
        if "/" in path and not path.startswith(report_id):
            bucket, object_name = path.split("/", 1)
        else:
            bucket = settings.BUCKET_IMAGES
            object_name = path
        
        content = minio.download_file(bucket, object_name)
        
        # 根据文件扩展名确定content_type
        ext = Path(object_name).suffix.lower()
        content_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.svg': 'image/svg+xml',
            '.bmp': 'image/bmp'
        }
        content_type = content_types.get(ext, 'image/png')
        
        return StreamingResponse(
            io.BytesIO(content),
            media_type=content_type
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取图片失败: {str(e)}")


@router.delete("/api/reports/{report_id}")
async def delete_report(
    report_id: str,
    service: DataService = Depends(get_data_service)
):
    """删除报告"""
    result = service.delete_report(report_id)
    if not result:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    return {"success": True, "message": "报告已删除"}
