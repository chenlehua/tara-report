"""
报告管理端点
"""
import io
import os
import json
import uuid
import tempfile
from datetime import datetime
from typing import Optional, List
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.common.database import get_db, get_minio_client, BUCKET_IMAGES, BUCKET_REPORTS
from app.common.models import (
    Report, ReportCover, ReportDefinitions, ReportAsset,
    ReportAttackTree, ReportTARAResult, ReportImage, GeneratedReport
)
from app.generators import generate_tara_excel_from_json, generate_tara_pdf_from_json

router = APIRouter()


def generate_report_id() -> str:
    """生成报告ID"""
    return f"RPT-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"


def generate_image_id() -> str:
    """生成图片ID"""
    return f"IMG-{uuid.uuid4().hex[:12]}"


# ==================== 报告数据上传端点 ====================

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
    上传JSON参数和图片，生成报告ID
    """
    # 1. 解析JSON数据
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
    
    # 2. 生成报告ID
    report_id = generate_report_id()
    minio = get_minio_client()
    
    # 3. 创建报告记录
    report = Report(report_id=report_id, status="pending")
    db.add(report)
    db.flush()
    
    # 4. 上传图片到MinIO并记录
    async def save_image(upload_file: UploadFile, image_type: str) -> Optional[str]:
        if not upload_file or not upload_file.filename:
            return None
        
        image_id = generate_image_id()
        file_ext = Path(upload_file.filename).suffix.lower()
        object_name = f"{report_id}/{image_type}/{image_id}{file_ext}"
        
        content = await upload_file.read()
        minio.upload_bytes(
            BUCKET_IMAGES,
            object_name,
            content,
            upload_file.content_type or "image/png"
        )
        
        # 记录图片信息
        image_record = ReportImage(
            report_id=report_id,
            image_id=image_id,
            image_type=image_type,
            original_name=upload_file.filename,
            minio_path=object_name,
            minio_bucket=BUCKET_IMAGES,
            file_size=len(content),
            content_type=upload_file.content_type
        )
        db.add(image_record)
        
        return object_name
    
    # 保存各类图片
    item_boundary_path = await save_image(item_boundary_image, "item_boundary")
    system_arch_path = await save_image(system_architecture_image, "system_architecture")
    software_arch_path = await save_image(software_architecture_image, "software_architecture")
    dataflow_path = await save_image(dataflow_image, "dataflow")
    
    # 保存攻击树图片
    attack_tree_paths = []
    if attack_tree_images:
        for i, img in enumerate(attack_tree_images):
            if img and img.filename:
                path = await save_image(img, f"attack_tree_{i}")
                if path:
                    attack_tree_paths.append(path)
    
    # 5. 解析并保存封面数据
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
    
    # 6. 解析并保存相关定义
    definitions_data = report_data.get('definitions', {})
    definitions = ReportDefinitions(
        report_id=report_id,
        title=definitions_data.get('title', ''),
        functional_description=definitions_data.get('functional_description', ''),
        item_boundary_image=item_boundary_path,
        system_architecture_image=system_arch_path,
        software_architecture_image=software_arch_path,
        dataflow_image=dataflow_path,
        assumptions=definitions_data.get('assumptions', []),
        terminology=definitions_data.get('terminology', [])
    )
    db.add(definitions)
    
    # 7. 解析并保存资产列表
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
    
    # 8. 解析并保存攻击树
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
    
    # 9. 解析并保存TARA分析结果
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
    
    # 更新报告状态
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


# ==================== 报告查询端点 ====================

@router.get("/reports")
async def list_reports(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    """获取报告列表"""
    offset = (page - 1) * page_size
    
    total = db.query(Report).count()
    reports = db.query(Report).order_by(Report.created_at.desc()).offset(offset).limit(page_size).all()
    
    result = []
    for report in reports:
        cover = db.query(ReportCover).filter(ReportCover.report_id == report.report_id).first()
        
        # 统计信息
        assets_count = db.query(ReportAsset).filter(ReportAsset.report_id == report.report_id).count()
        tara_count = db.query(ReportTARAResult).filter(ReportTARAResult.report_id == report.report_id).count()
        attack_trees_count = db.query(ReportAttackTree).filter(ReportAttackTree.report_id == report.report_id).count()
        
        # 计算高风险项数量
        high_risk_count = db.query(ReportTARAResult).filter(
            ReportTARAResult.report_id == report.report_id,
            ReportTARAResult.operational_impact.in_(['重大的', '严重的'])
        ).count()
        
        # 获取已生成的报告文件信息
        generated_files = db.query(GeneratedReport).filter(
            GeneratedReport.report_id == report.report_id
        ).all()
        
        downloads = {}
        for gf in generated_files:
            downloads[gf.file_type] = {
                "url": f"/api/v1/reports/{report.report_id}/download?format={gf.file_type}",
                "file_size": gf.file_size,
                "generated_at": gf.generated_at.isoformat() if gf.generated_at else None
            }
        
        result.append({
            "id": report.report_id,
            "report_id": report.report_id,
            "name": cover.report_title if cover else "TARA报告",
            "project_name": cover.project_name if cover else "",
            "report_title": cover.report_title if cover else "",
            "status": report.status,
            "created_at": report.created_at.isoformat(),
            "file_path": "",
            "statistics": {
                "assets_count": assets_count,
                "threats_count": tara_count,
                "high_risk_count": high_risk_count,
                "measures_count": tara_count,
                "attack_trees_count": attack_trees_count
            },
            "downloads": downloads
        })
    
    return {
        "success": True,
        "total": total,
        "page": page,
        "page_size": page_size,
        "reports": result
    }


@router.get("/reports/{report_id}")
async def get_report_info(report_id: str, db: Session = Depends(get_db)):
    """获取报告完整信息"""
    report = db.query(Report).filter(Report.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    # 获取封面信息
    cover = db.query(ReportCover).filter(ReportCover.report_id == report_id).first()
    
    # 获取定义信息
    definitions = db.query(ReportDefinitions).filter(ReportDefinitions.report_id == report_id).first()
    
    # 获取资产列表
    assets = db.query(ReportAsset).filter(ReportAsset.report_id == report_id).all()
    
    # 获取攻击树
    attack_trees = db.query(ReportAttackTree).filter(
        ReportAttackTree.report_id == report_id
    ).order_by(ReportAttackTree.sort_order).all()
    
    # 获取TARA结果
    tara_results = db.query(ReportTARAResult).filter(
        ReportTARAResult.report_id == report_id
    ).order_by(ReportTARAResult.sort_order).all()
    
    # 构建图片URL
    def build_image_url(minio_path):
        if not minio_path:
            return None
        return f"/api/v1/reports/{report_id}/image-by-path?path={minio_path}"
    
    # 构建资产列表
    assets_list = [
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
    
    # 构建攻击树列表
    attack_trees_list = [
        {
            "asset_id": tree.asset_id,
            "asset_name": tree.asset_name,
            "title": tree.title,
            "image": tree.image,
            "image_url": build_image_url(tree.image)
        }
        for tree in attack_trees
    ]
    
    # 构建TARA结果列表
    tara_results_list = [
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
        for r in tara_results
    ]
    
    # 统计信息
    statistics = {
        'assets_count': len(assets_list),
        'threats_count': len(tara_results_list),
        'high_risk_count': sum(1 for r in tara_results_list if r.get('operational_impact') in ['重大的', '严重的']),
        'measures_count': len(tara_results_list),
        'attack_trees_count': len(attack_trees_list)
    }
    
    # 获取已生成的报告文件信息
    generated_files = db.query(GeneratedReport).filter(
        GeneratedReport.report_id == report_id
    ).all()
    
    downloads = {}
    for gf in generated_files:
        downloads[gf.file_type] = {
            "url": f"/api/v1/reports/{report_id}/download?format={gf.file_type}",
            "file_size": gf.file_size,
            "generated_at": gf.generated_at.isoformat() if gf.generated_at else None
        }
    
    return {
        "id": report.report_id,
        "report_id": report.report_id,
        "name": cover.report_title if cover else "TARA报告",
        "project_name": cover.project_name if cover else "",
        "status": report.status,
        "created_at": report.created_at.isoformat(),
        "updated_at": report.updated_at.isoformat() if report.updated_at else None,
        "file_path": "",
        "statistics": statistics,
        "downloads": downloads,
        "cover": {
            "report_title": cover.report_title if cover else "",
            "report_title_en": cover.report_title_en if cover else "",
            "project_name": cover.project_name if cover else "",
            "data_level": cover.data_level if cover else "",
            "document_number": cover.document_number if cover else "",
            "version": cover.version if cover else "",
            "author_date": cover.author_date if cover else "",
            "review_date": cover.review_date if cover else "",
            "sign_date": cover.sign_date if cover else "",
            "approve_date": cover.approve_date if cover else ""
        } if cover else {},
        "definitions": {
            "title": definitions.title if definitions else "",
            "functional_description": definitions.functional_description if definitions else "",
            "item_boundary_image": build_image_url(definitions.item_boundary_image) if definitions else None,
            "system_architecture_image": build_image_url(definitions.system_architecture_image) if definitions else None,
            "software_architecture_image": build_image_url(definitions.software_architecture_image) if definitions else None,
            "assumptions": definitions.assumptions if definitions else [],
            "terminology": definitions.terminology if definitions else []
        } if definitions else {},
        "assets": {
            "title": "资产列表",
            "assets": assets_list,
            "dataflow_image": build_image_url(definitions.dataflow_image) if definitions and definitions.dataflow_image else None
        },
        "attack_trees": {
            "title": "攻击树分析",
            "attack_trees": attack_trees_list
        },
        "tara_results": {
            "title": "TARA分析结果",
            "results": tara_results_list
        }
    }


@router.get("/reports/{report_id}/cover")
async def get_report_cover(report_id: str, db: Session = Depends(get_db)):
    """获取报告封面信息"""
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
    """获取报告相关定义"""
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
    """获取报告资产列表"""
    definitions = db.query(ReportDefinitions).filter(ReportDefinitions.report_id == report_id).first()
    dataflow_image = getattr(definitions, 'dataflow_image', None) if definitions else None
    
    assets = db.query(ReportAsset).filter(ReportAsset.report_id == report_id).all()
    
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
    """获取报告攻击树"""
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
    """获取TARA分析结果"""
    results = db.query(ReportTARAResult).filter(
        ReportTARAResult.report_id == report_id
    ).order_by(ReportTARAResult.sort_order).all()
    
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


# ==================== 图片端点 ====================

@router.get("/reports/{report_id}/images/{image_id}")
async def get_report_image(report_id: str, image_id: str, db: Session = Depends(get_db)):
    """获取图片"""
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
    """根据MinIO路径获取图片"""
    try:
        minio = get_minio_client()
        if "/" in path and not path.startswith(report_id):
            bucket, object_name = path.split("/", 1)
        else:
            bucket = BUCKET_IMAGES
            object_name = path
        
        content = minio.download_file(bucket, object_name)
        
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


# ==================== 报告生成和下载端点 ====================

async def prepare_report_data(report_id: str, db: Session) -> dict:
    """准备报告数据"""
    # 获取封面
    cover = db.query(ReportCover).filter(ReportCover.report_id == report_id).first()
    cover_data = {
        "report_title": cover.report_title if cover else "",
        "report_title_en": cover.report_title_en if cover else "",
        "project_name": cover.project_name if cover else "",
        "data_level": cover.data_level if cover else "",
        "document_number": cover.document_number if cover else "",
        "version": cover.version if cover else "",
        "author_date": cover.author_date if cover else "",
        "review_date": cover.review_date if cover else "",
        "sign_date": cover.sign_date if cover else "",
        "approve_date": cover.approve_date if cover else ""
    } if cover else {}
    
    # 获取定义
    definitions = db.query(ReportDefinitions).filter(ReportDefinitions.report_id == report_id).first()
    
    # 下载图片到临时文件
    async def download_image_to_temp(minio_path: str) -> Optional[str]:
        if not minio_path:
            return None
        try:
            minio = get_minio_client()
            if "/" in minio_path and not minio_path.startswith(report_id):
                bucket, object_name = minio_path.split("/", 1)
            else:
                bucket = BUCKET_IMAGES
                object_name = minio_path
            
            content = minio.download_file(bucket, object_name)
            ext = Path(object_name).suffix or '.png'
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
            temp_file.write(content)
            temp_file.close()
            return temp_file.name
        except Exception as e:
            print(f"Failed to download image {minio_path}: {e}")
            return None
    
    definitions_data = {}
    if definitions:
        definitions_data = {
            "title": definitions.title,
            "functional_description": definitions.functional_description,
            "item_boundary_image": await download_image_to_temp(definitions.item_boundary_image),
            "system_architecture_image": await download_image_to_temp(definitions.system_architecture_image),
            "software_architecture_image": await download_image_to_temp(definitions.software_architecture_image),
            "assumptions": definitions.assumptions or [],
            "terminology": definitions.terminology or []
        }
    
    # 获取资产
    assets = db.query(ReportAsset).filter(ReportAsset.report_id == report_id).all()
    assets_data = {
        "title": f"{cover.project_name if cover else 'TARA'} - 资产列表 Asset List",
        "dataflow_image": await download_image_to_temp(definitions.dataflow_image) if definitions else None,
        "assets": [
            {
                "id": a.asset_id,
                "name": a.name,
                "category": a.category,
                "remarks": a.remarks,
                "authenticity": a.authenticity,
                "integrity": a.integrity,
                "non_repudiation": a.non_repudiation,
                "confidentiality": a.confidentiality,
                "availability": a.availability,
                "authorization": a.authorization
            }
            for a in assets
        ]
    }
    
    # 获取攻击树
    attack_trees = db.query(ReportAttackTree).filter(
        ReportAttackTree.report_id == report_id
    ).order_by(ReportAttackTree.sort_order).all()
    
    attack_trees_list = []
    for tree in attack_trees:
        attack_trees_list.append({
            "asset_id": tree.asset_id,
            "asset_name": tree.asset_name,
            "title": tree.title,
            "image": await download_image_to_temp(tree.image)
        })
    
    attack_trees_data = {
        "title": "攻击树分析 Attack Tree Analysis",
        "attack_trees": attack_trees_list
    }
    
    # 获取TARA结果
    tara_results = db.query(ReportTARAResult).filter(
        ReportTARAResult.report_id == report_id
    ).order_by(ReportTARAResult.sort_order).all()
    
    tara_results_data = {
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
            for r in tara_results
        ]
    }
    
    return {
        "cover": cover_data,
        "definitions": definitions_data,
        "assets": assets_data,
        "attack_trees": attack_trees_data,
        "tara_results": tara_results_data
    }


def cleanup_temp_files(data: dict):
    """清理临时文件"""
    paths_to_clean = []
    
    definitions = data.get('definitions', {})
    for key in ['item_boundary_image', 'system_architecture_image', 'software_architecture_image']:
        if definitions.get(key) and os.path.exists(definitions[key]):
            paths_to_clean.append(definitions[key])
    
    assets = data.get('assets', {})
    if assets.get('dataflow_image') and os.path.exists(assets['dataflow_image']):
        paths_to_clean.append(assets['dataflow_image'])
    
    attack_trees = data.get('attack_trees', {})
    for tree in attack_trees.get('attack_trees', []):
        if tree.get('image') and os.path.exists(tree['image']):
            paths_to_clean.append(tree['image'])
    
    for path in paths_to_clean:
        try:
            os.unlink(path)
        except:
            pass


@router.post("/reports/{report_id}/generate")
async def generate_report(
    report_id: str,
    format: str = "xlsx",
    db: Session = Depends(get_db)
):
    """生成报告"""
    report = db.query(Report).filter(Report.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    # 准备数据
    try:
        data = await prepare_report_data(report_id, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取报告数据失败: {str(e)}")
    
    # 创建临时文件
    if format.lower() == "pdf":
        suffix = ".pdf"
        generator = generate_tara_pdf_from_json
    else:
        suffix = ".xlsx"
        generator = generate_tara_excel_from_json
    
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    temp_path = temp_file.name
    temp_file.close()
    
    try:
        generator(temp_path, data)
        
        with open(temp_path, 'rb') as f:
            file_content = f.read()
        
        # 上传到MinIO
        minio = get_minio_client()
        object_name = f"{report_id}/{report_id}{suffix}"
        content_type = "application/pdf" if format.lower() == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        
        minio.upload_bytes(BUCKET_REPORTS, object_name, file_content, content_type)
        
        # 记录到数据库
        existing = db.query(GeneratedReport).filter(
            GeneratedReport.report_id == report_id,
            GeneratedReport.file_type == format.lower()
        ).first()
        
        if existing:
            existing.minio_path = object_name
            existing.file_size = len(file_content)
            existing.generated_at = datetime.now()
        else:
            generated = GeneratedReport(
                report_id=report_id,
                file_type=format.lower(),
                minio_path=object_name,
                minio_bucket=BUCKET_REPORTS,
                file_size=len(file_content)
            )
            db.add(generated)
        
        db.commit()
        
        cleanup_temp_files(data)
        
        cover = db.query(ReportCover).filter(ReportCover.report_id == report_id).first()
        project_name = cover.project_name if cover else "TARA报告"
        
        return {
            "success": True,
            "message": "报告生成成功",
            "report_id": report_id,
            "format": format.lower(),
            "file_size": len(file_content),
            "download_url": f"/api/v1/reports/{report_id}/download?format={format.lower()}",
            "file_name": f"{project_name}_{report_id}{suffix}"
        }
        
    except Exception as e:
        cleanup_temp_files(data)
        raise HTTPException(status_code=500, detail=f"报告生成失败: {str(e)}")
    finally:
        try:
            os.unlink(temp_path)
        except:
            pass


async def _do_download_report(report_id: str, format: str, db: Session):
    """内部下载报告逻辑"""
    generated = db.query(GeneratedReport).filter(
        GeneratedReport.report_id == report_id,
        GeneratedReport.file_type == format.lower()
    ).first()
    
    if not generated:
        raise HTTPException(status_code=404, detail="报告文件不存在，请先生成报告")
    
    try:
        minio = get_minio_client()
        content = minio.download_file(generated.minio_bucket, generated.minio_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载报告失败: {str(e)}")
    
    cover = db.query(ReportCover).filter(ReportCover.report_id == report_id).first()
    project_name = cover.project_name if cover else "TARA报告"
    
    suffix = ".pdf" if format.lower() == "pdf" else ".xlsx"
    content_type = "application/pdf" if format.lower() == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    filename = f"{project_name}_{report_id}{suffix}"
    
    encoded_filename = quote(filename, safe='')
    
    return StreamingResponse(
        io.BytesIO(content),
        media_type=content_type,
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
        }
    )


@router.get("/reports/{report_id}/download/{format}")
async def download_report_with_format(
    report_id: str,
    format: str,
    db: Session = Depends(get_db)
):
    """下载报告（格式作为路径参数）"""
    return await _do_download_report(report_id, format, db)


@router.get("/reports/{report_id}/download")
async def download_report(
    report_id: str,
    format: str = "xlsx",
    db: Session = Depends(get_db)
):
    """下载报告（格式作为查询参数）"""
    return await _do_download_report(report_id, format, db)


@router.get("/reports/{report_id}/preview")
async def preview_report(report_id: str, db: Session = Depends(get_db)):
    """获取报告预览数据"""
    return await get_report_info(report_id, db)


@router.get("/reports/{report_id}/status")
async def get_report_status(report_id: str, db: Session = Depends(get_db)):
    """获取报告状态"""
    report = db.query(Report).filter(Report.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    generated_files = db.query(GeneratedReport).filter(
        GeneratedReport.report_id == report_id
    ).all()
    
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


@router.delete("/reports/{report_id}")
async def delete_report(report_id: str, db: Session = Depends(get_db)):
    """删除报告"""
    report = db.query(Report).filter(Report.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    minio = get_minio_client()
    
    # 删除MinIO中的图片
    images = db.query(ReportImage).filter(ReportImage.report_id == report_id).all()
    for image in images:
        try:
            minio.delete_file(image.minio_bucket, image.minio_path)
        except:
            pass
    
    # 删除MinIO中的生成报告文件
    generated_files = db.query(GeneratedReport).filter(GeneratedReport.report_id == report_id).all()
    for gf in generated_files:
        try:
            minio.delete_file(gf.minio_bucket, gf.minio_path)
        except:
            pass
    
    db.delete(report)
    db.commit()
    
    return {"success": True, "message": "报告已删除"}
