"""
Report data management endpoints
"""
import io
import json
import uuid
import httpx
from datetime import datetime
from typing import Optional, List
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.common.database import get_db, get_minio_client
from app.common.config.settings import settings
from app.common.models import (
    Report, ReportCover, ReportDefinitions, ReportAsset,
    ReportAttackTree, ReportTARAResult, ReportImage
)
from app.common.constants.enums import ALLOWED_IMAGE_EXTENSIONS
from app.common.utils.calculations import calculate_tara_derived_columns

router = APIRouter()


@router.get("/reports")
async def list_reports(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    """
    获取报告列表
    
    Args:
        page: 页码
        page_size: 每页数量
    """
    offset = (page - 1) * page_size
    
    # 查询总数
    total = db.query(Report).count()
    
    # 查询报告列表
    reports = db.query(Report).order_by(Report.created_at.desc()).offset(offset).limit(page_size).all()
    
    result = []
    for report in reports:
        # 获取封面信息
        cover = db.query(ReportCover).filter(ReportCover.report_id == report.report_id).first()
        
        # 统计信息
        assets_count = db.query(ReportAsset).filter(ReportAsset.report_id == report.report_id).count()
        tara_count = db.query(ReportTARAResult).filter(ReportTARAResult.report_id == report.report_id).count()
        attack_trees_count = db.query(ReportAttackTree).filter(ReportAttackTree.report_id == report.report_id).count()
        
        # 统计高风险项
        high_risk_count = db.query(ReportTARAResult).filter(
            ReportTARAResult.report_id == report.report_id,
            ReportTARAResult.operational_impact.in_(['重大的', '严重的'])
        ).count()
        
        result.append({
            "id": report.report_id,
            "report_id": report.report_id,
            "name": cover.report_title if cover else "TARA报告",
            "project_name": cover.project_name if cover else "",
            "report_title": cover.report_title if cover else "",
            "status": report.status,
            "created_at": report.created_at.isoformat() if report.created_at else "",
            "file_path": "",
            "statistics": {
                "assets_count": assets_count,
                "threats_count": tara_count,
                "high_risk_count": high_risk_count,
                "measures_count": tara_count,
                "attack_trees_count": attack_trees_count
            },
            "downloads": {}  # 由 report-service 补充
        })
    
    return {
        "success": True,
        "total": total,
        "page": page,
        "page_size": page_size,
        "reports": result
    }


@router.delete("/reports/{report_id}")
async def delete_report(report_id: str, db: Session = Depends(get_db)):
    """
    删除报告及其所有关联资源
    
    Args:
        report_id: 报告ID
    """
    report = db.query(Report).filter(Report.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    # 删除 MinIO 中的图片
    minio = get_minio_client()
    images = db.query(ReportImage).filter(ReportImage.report_id == report_id).all()
    for image in images:
        try:
            minio.delete_file(image.minio_bucket, image.minio_path)
        except:
            pass
    
    # 删除数据库记录（级联删除）
    db.delete(report)
    db.commit()
    
    return {"success": True, "message": "报告已删除"}


def generate_report_id() -> str:
    """Generate report ID"""
    return f"RPT-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"


def generate_image_id() -> str:
    """Generate image ID"""
    return f"IMG-{uuid.uuid4().hex[:12]}"


@router.post("/reports/upload")
async def upload_report_data(
    json_file: UploadFile = File(None, description="JSON数据文件"),
    json_data: str = Form(None, description="JSON数据字符串"),
    item_boundary_image: UploadFile = File(None),
    system_architecture_image: UploadFile = File(None),
    software_architecture_image: UploadFile = File(None),
    dataflow_image: UploadFile = File(None),
    attack_tree_images: List[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Upload JSON parameters and images, generate report ID
    
    1. Generate report ID
    2. Save images to MinIO
    3. Parse JSON and save to database
    4. Return report ID
    """
    # 1. Parse JSON data
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
    
    # 2. Generate report ID
    report_id = generate_report_id()
    minio = get_minio_client()
    
    # 3. Create report record
    report = Report(report_id=report_id, status="pending")
    db.add(report)
    db.flush()
    
    # 4. Upload images to MinIO and record
    async def save_image(upload_file: UploadFile, image_type: str) -> Optional[str]:
        if not upload_file or not upload_file.filename:
            return None
        
        image_id = generate_image_id()
        file_ext = Path(upload_file.filename).suffix.lower()
        object_name = f"{report_id}/{image_type}/{image_id}{file_ext}"
        
        content = await upload_file.read()
        minio.upload_bytes(
            settings.BUCKET_IMAGES,
            object_name,
            content,
            upload_file.content_type or "image/png"
        )
        
        # Record image info
        image_record = ReportImage(
            report_id=report_id,
            image_id=image_id,
            image_type=image_type,
            original_name=upload_file.filename,
            minio_path=object_name,
            minio_bucket=settings.BUCKET_IMAGES,
            file_size=len(content),
            content_type=upload_file.content_type
        )
        db.add(image_record)
        
        return object_name
    
    # Save various images
    item_boundary_path = await save_image(item_boundary_image, "item_boundary")
    system_arch_path = await save_image(system_architecture_image, "system_architecture")
    software_arch_path = await save_image(software_architecture_image, "software_architecture")
    dataflow_path = await save_image(dataflow_image, "dataflow")
    
    # Save attack tree images
    attack_tree_paths = []
    if attack_tree_images:
        for i, img in enumerate(attack_tree_images):
            if img and img.filename:
                path = await save_image(img, f"attack_tree_{i}")
                if path:
                    attack_tree_paths.append(path)
    
    # 5. Parse and save cover data
    cover_data = report_data.get('cover', {})
    cover = ReportCover(
        report_id=report_id,
        report_title=cover_data.get('report_title', '威胁分析和风险评估报告'),
        report_title_en=cover_data.get('report_title_en', 'Threat Analysis And Risk Assessment Report'),
        project_name=cover_data.get('project_name', ''),
        data_level=cover_data.get('data_level', '秘密'),
        document_number=cover_data.get('document_number', ''),
        version=cover_data.get('version', ''),
        author_date=cover_data.get('author_date', ''),
        review_date=cover_data.get('review_date', ''),
        sign_date=cover_data.get('sign_date', ''),
        approve_date=cover_data.get('approve_date', '')
    )
    db.add(cover)
    
    # 6. Parse and save definitions
    definitions_data = report_data.get('definitions', {})
    definitions = ReportDefinitions(
        report_id=report_id,
        title=definitions_data.get('title', ''),
        functional_description=definitions_data.get('functional_description', ''),
        item_boundary_image=item_boundary_path,
        system_architecture_image=system_arch_path,
        software_architecture_image=software_arch_path,
        assumptions=definitions_data.get('assumptions', []),
        terminology=definitions_data.get('terminology', [])
    )
    db.add(definitions)
    
    # 7. Parse and save assets
    assets_data = report_data.get('assets', {})
    for asset in assets_data.get('assets', []):
        asset_record = ReportAsset(
            report_id=report_id,
            asset_id=asset.get('id', ''),
            name=asset.get('name', ''),
            category=asset.get('category', ''),
            remarks=asset.get('remarks', ''),
            authenticity=asset.get('authenticity', False),
            integrity=asset.get('integrity', False),
            non_repudiation=asset.get('non_repudiation', False),
            confidentiality=asset.get('confidentiality', False),
            availability=asset.get('availability', False),
            authorization=asset.get('authorization', False)
        )
        db.add(asset_record)
    
    # Update definitions dataflow image path
    if dataflow_path:
        definitions.dataflow_image = dataflow_path
        db.add(definitions)
    
    # 8. Parse and save attack trees
    attack_trees_data = report_data.get('attack_trees', {})
    trees = attack_trees_data.get('attack_trees', [])
    for i, tree in enumerate(trees):
        tree_record = ReportAttackTree(
            report_id=report_id,
            asset_id=tree.get('asset_id', ''),
            asset_name=tree.get('asset_name', ''),
            title=tree.get('title', f'攻击树 {i+1}'),
            image=attack_tree_paths[i] if i < len(attack_tree_paths) else tree.get('image', ''),
            sort_order=i
        )
        db.add(tree_record)
    
    # 9. Parse and save TARA results
    tara_data = report_data.get('tara_results', {})
    for i, result in enumerate(tara_data.get('results', [])):
        tara_record = ReportTARAResult(
            report_id=report_id,
            asset_id=result.get('asset_id', ''),
            asset_name=result.get('asset_name', ''),
            subdomain1=result.get('subdomain1', ''),
            subdomain2=result.get('subdomain2', ''),
            subdomain3=result.get('subdomain3', ''),
            category=result.get('category', ''),
            security_attribute=result.get('security_attribute', ''),
            stride_model=result.get('stride_model', ''),
            threat_scenario=result.get('threat_scenario', ''),
            attack_path=result.get('attack_path', ''),
            wp29_mapping=result.get('wp29_mapping', ''),
            attack_vector=result.get('attack_vector', ''),
            attack_complexity=result.get('attack_complexity', ''),
            privileges_required=result.get('privileges_required', ''),
            user_interaction=result.get('user_interaction', ''),
            safety_impact=result.get('safety_impact', ''),
            financial_impact=result.get('financial_impact', ''),
            operational_impact=result.get('operational_impact', ''),
            privacy_impact=result.get('privacy_impact', ''),
            security_goal=result.get('security_goal', ''),
            security_requirement=result.get('security_requirement', ''),
            sort_order=i
        )
        db.add(tara_record)
    
    # Update report status
    report.status = "completed"
    db.commit()
    
    return {
        "success": True,
        "message": "数据上传成功",
        "report_id": report_id,
        "statistics": {
            "assets_count": len(assets_data.get('assets', [])),
            "attack_trees_count": len(trees),
            "tara_results_count": len(tara_data.get('results', [])),
            "images_count": len([p for p in [item_boundary_path, system_arch_path, software_arch_path, dataflow_path] + attack_tree_paths if p])
        }
    }


@router.get("/reports/{report_id}/cover")
async def get_report_cover(report_id: str, db: Session = Depends(get_db)):
    """Get report cover information"""
    cover = db.query(ReportCover).filter(ReportCover.report_id == report_id).first()
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


@router.get("/reports/{report_id}/definitions")
async def get_report_definitions(report_id: str, db: Session = Depends(get_db)):
    """Get report definitions"""
    definitions = db.query(ReportDefinitions).filter(ReportDefinitions.report_id == report_id).first()
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


@router.get("/reports/{report_id}/assets")
async def get_report_assets(report_id: str, db: Session = Depends(get_db)):
    """Get report assets"""
    # Get dataflow_image from definitions
    definitions = db.query(ReportDefinitions).filter(ReportDefinitions.report_id == report_id).first()
    dataflow_image = getattr(definitions, 'dataflow_image', None) if definitions else None
    
    assets = db.query(ReportAsset).filter(ReportAsset.report_id == report_id).all()
    
    # Get cover info for title
    cover = db.query(ReportCover).filter(ReportCover.report_id == report_id).first()
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


@router.get("/reports/{report_id}/attack-trees")
async def get_report_attack_trees(report_id: str, db: Session = Depends(get_db)):
    """Get report attack trees"""
    trees = db.query(ReportAttackTree).filter(
        ReportAttackTree.report_id == report_id
    ).order_by(ReportAttackTree.sort_order).all()
    
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


@router.get("/reports/{report_id}/tara-results")
async def get_report_tara_results(report_id: str, db: Session = Depends(get_db)):
    """Get TARA analysis results with calculated columns"""
    results = db.query(ReportTARAResult).filter(
        ReportTARAResult.report_id == report_id
    ).order_by(ReportTARAResult.sort_order).all()
    
    # 构建结果列表，包含计算列
    results_with_calculations = []
    for r in results:
        # 基础数据
        base_data = {
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
        
        # 添加计算列
        result_with_calcs = calculate_tara_derived_columns(base_data)
        results_with_calculations.append(result_with_calcs)
    
    return {
        "title": "TARA分析结果 TARA Analysis Results",
        "results": results_with_calculations
    }


@router.get("/reports/{report_id}/images/{image_id}")
async def get_report_image(report_id: str, image_id: str, db: Session = Depends(get_db)):
    """Get image"""
    image = db.query(ReportImage).filter(
        ReportImage.report_id == report_id,
        ReportImage.image_id == image_id
    ).first()
    
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


@router.get("/reports/{report_id}/image-by-path")
async def get_image_by_path(report_id: str, path: str, db: Session = Depends(get_db)):
    """Get image by MinIO path"""
    try:
        minio = get_minio_client()
        # Path format: bucket/object_name or just object_name
        if "/" in path and not path.startswith(report_id):
            bucket, object_name = path.split("/", 1)
        else:
            bucket = settings.BUCKET_IMAGES
            object_name = path
        
        content = minio.download_file(bucket, object_name)
        
        # Determine content_type based on file extension
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
