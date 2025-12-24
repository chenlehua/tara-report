"""
Report management endpoints
"""
import io
import os
import tempfile
import httpx
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.common.database import get_db, get_minio_client
from app.common.config.settings import settings
from app.common.models import (
    Report, ReportCover, GeneratedReport, ReportAsset,
    ReportTARAResult, ReportAttackTree, ReportDefinitions, ReportImage
)
from app.generators import generate_tara_excel_from_json, generate_tara_pdf_from_json

router = APIRouter()


# ==================== Helper functions ====================

async def fetch_data_from_service(report_id: str) -> Dict[str, Any]:
    """
    Fetch report data from data service
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Get cover data
        cover_resp = await client.get(f"{settings.DATA_SERVICE_URL}/api/v1/reports/{report_id}/cover")
        if cover_resp.status_code != 200:
            raise HTTPException(status_code=404, detail="无法获取封面数据")
        cover_data = cover_resp.json()
        
        # Get definitions data
        definitions_resp = await client.get(f"{settings.DATA_SERVICE_URL}/api/v1/reports/{report_id}/definitions")
        if definitions_resp.status_code != 200:
            raise HTTPException(status_code=404, detail="无法获取定义数据")
        definitions_data = definitions_resp.json()
        
        # Get assets data
        assets_resp = await client.get(f"{settings.DATA_SERVICE_URL}/api/v1/reports/{report_id}/assets")
        if assets_resp.status_code != 200:
            raise HTTPException(status_code=404, detail="无法获取资产数据")
        assets_data = assets_resp.json()
        
        # Get attack trees data
        attack_trees_resp = await client.get(f"{settings.DATA_SERVICE_URL}/api/v1/reports/{report_id}/attack-trees")
        if attack_trees_resp.status_code != 200:
            raise HTTPException(status_code=404, detail="无法获取攻击树数据")
        attack_trees_data = attack_trees_resp.json()
        
        # Get TARA results data
        tara_resp = await client.get(f"{settings.DATA_SERVICE_URL}/api/v1/reports/{report_id}/tara-results")
        if tara_resp.status_code != 200:
            raise HTTPException(status_code=404, detail="无法获取TARA结果数据")
        tara_data = tara_resp.json()
    
    return {
        "cover": cover_data,
        "definitions": definitions_data,
        "assets": assets_data,
        "attack_trees": attack_trees_data,
        "tara_results": tara_data
    }


async def download_image_from_minio(minio_path: str, report_id: str) -> Optional[str]:
    """
    Download image from MinIO to temporary file
    """
    if not minio_path:
        return None
    
    try:
        minio = get_minio_client()
        
        # Parse path
        if "/" in minio_path and not minio_path.startswith(report_id):
            bucket, object_name = minio_path.split("/", 1)
        else:
            bucket = settings.BUCKET_IMAGES
            object_name = minio_path
        
        content = minio.download_file(bucket, object_name)
        
        # Create temporary file
        ext = Path(object_name).suffix or '.png'
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
        temp_file.write(content)
        temp_file.close()
        
        return temp_file.name
    except Exception as e:
        print(f"Failed to download image {minio_path}: {e}")
        return None


async def prepare_report_data(report_id: str) -> Dict[str, Any]:
    """
    Prepare report data, including downloading images to local temp files
    """
    # Get data
    data = await fetch_data_from_service(report_id)
    
    # Download images and replace paths
    definitions = data.get('definitions', {})
    
    # Download definition images
    if definitions.get('item_boundary_image'):
        local_path = await download_image_from_minio(definitions['item_boundary_image'], report_id)
        definitions['item_boundary_image'] = local_path
    
    if definitions.get('system_architecture_image'):
        local_path = await download_image_from_minio(definitions['system_architecture_image'], report_id)
        definitions['system_architecture_image'] = local_path
    
    if definitions.get('software_architecture_image'):
        local_path = await download_image_from_minio(definitions['software_architecture_image'], report_id)
        definitions['software_architecture_image'] = local_path
    
    # Download dataflow image from assets
    assets = data.get('assets', {})
    if assets.get('dataflow_image'):
        local_path = await download_image_from_minio(assets['dataflow_image'], report_id)
        assets['dataflow_image'] = local_path
    
    # Download attack tree images
    attack_trees = data.get('attack_trees', {})
    for tree in attack_trees.get('attack_trees', []):
        if tree.get('image'):
            local_path = await download_image_from_minio(tree['image'], report_id)
            tree['image'] = local_path
    
    return data


def cleanup_temp_files(data: Dict[str, Any]):
    """Clean up temporary files"""
    paths_to_clean = []
    
    # Collect all temporary file paths
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
    
    # Delete temporary files
    for path in paths_to_clean:
        try:
            os.unlink(path)
        except:
            pass


# ==================== API endpoints ====================

@router.get("/reports")
async def list_reports(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    """
    Get report list
    
    Args:
        page: Page number
        page_size: Page size
    """
    offset = (page - 1) * page_size
    
    total = db.query(Report).count()
    reports = db.query(Report).order_by(Report.created_at.desc()).offset(offset).limit(page_size).all()
    
    result = []
    for report in reports:
        cover = db.query(ReportCover).filter(ReportCover.report_id == report.report_id).first()
        
        # Statistics
        assets_count = db.query(ReportAsset).filter(ReportAsset.report_id == report.report_id).count()
        tara_count = db.query(ReportTARAResult).filter(ReportTARAResult.report_id == report.report_id).count()
        attack_trees_count = db.query(ReportAttackTree).filter(ReportAttackTree.report_id == report.report_id).count()
        
        # Count high risk items
        high_risk_count = db.query(ReportTARAResult).filter(
            ReportTARAResult.report_id == report.report_id,
            ReportTARAResult.operational_impact.in_(['重大的', '严重的'])
        ).count()
        
        # Get generated file info
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
    """
    Get complete report information (for preview)
    
    Args:
        report_id: Report ID
    """
    report = db.query(Report).filter(Report.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    # Get cover info
    cover = db.query(ReportCover).filter(ReportCover.report_id == report_id).first()
    
    # Get definitions
    definitions = db.query(ReportDefinitions).filter(ReportDefinitions.report_id == report_id).first()
    
    # Get assets
    assets = db.query(ReportAsset).filter(ReportAsset.report_id == report_id).all()
    
    # Get attack trees
    attack_trees = db.query(ReportAttackTree).filter(
        ReportAttackTree.report_id == report_id
    ).order_by(ReportAttackTree.sort_order).all()
    
    # Get TARA results
    tara_results = db.query(ReportTARAResult).filter(
        ReportTARAResult.report_id == report_id
    ).order_by(ReportTARAResult.sort_order).all()
    
    # Build image URL
    def build_image_url(minio_path):
        if not minio_path:
            return None
        return f"/api/v1/reports/{report_id}/image-by-path?path={minio_path}"
    
    # Build assets list
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
    
    # Build attack trees list
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
    
    # Build TARA results list
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
    
    # Statistics
    statistics = {
        'assets_count': len(assets_list),
        'threats_count': len(tara_results_list),
        'high_risk_count': sum(1 for r in tara_results_list if r.get('operational_impact') in ['重大的', '严重的']),
        'measures_count': len(tara_results_list),
        'attack_trees_count': len(attack_trees_list)
    }
    
    # Get generated file info
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
    
    # Return format consistent with before refactoring
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


@router.delete("/reports/{report_id}")
async def delete_report(report_id: str, db: Session = Depends(get_db)):
    """
    Delete report and all related resources
    
    Args:
        report_id: Report ID
    """
    report = db.query(Report).filter(Report.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    # Delete images from MinIO
    minio = get_minio_client()
    images = db.query(ReportImage).filter(ReportImage.report_id == report_id).all()
    for image in images:
        try:
            minio.delete_file(image.minio_bucket, image.minio_path)
        except:
            pass
    
    # Delete generated report files from MinIO
    generated_files = db.query(GeneratedReport).filter(GeneratedReport.report_id == report_id).all()
    for gf in generated_files:
        try:
            minio.delete_file(gf.minio_bucket, gf.minio_path)
        except:
            pass
    
    # Delete database records (cascade delete)
    db.delete(report)
    db.commit()
    
    return {"success": True, "message": "报告已删除"}


@router.post("/reports/{report_id}/generate")
async def generate_report(
    report_id: str,
    format: str = "xlsx",
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    Generate report
    
    Args:
        report_id: Report ID
        format: Report format (xlsx or pdf)
    """
    # Check if report exists
    report = db.query(Report).filter(Report.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    # Prepare data
    try:
        data = await prepare_report_data(report_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取报告数据失败: {str(e)}")
    
    # Create temporary file
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
        # Generate report
        generator(temp_path, data)
        
        # Read generated file
        with open(temp_path, 'rb') as f:
            file_content = f.read()
        
        # Upload to MinIO
        minio = get_minio_client()
        object_name = f"{report_id}/{report_id}{suffix}"
        content_type = "application/pdf" if format.lower() == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        
        minio.upload_bytes(settings.BUCKET_REPORTS, object_name, file_content, content_type)
        
        # Record to database
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
                minio_bucket=settings.BUCKET_REPORTS,
                file_size=len(file_content)
            )
            db.add(generated)
        
        db.commit()
        
        # Clean up temporary image files
        cleanup_temp_files(data)
        
        # Get project name for filename
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
        # Delete temporary report file
        try:
            os.unlink(temp_path)
        except:
            pass


async def _do_download_report(report_id: str, format: str, db: Session):
    """
    Internal download report logic
    
    Args:
        report_id: Report ID
        format: Report format (xlsx or pdf)
    """
    # Find generated report
    generated = db.query(GeneratedReport).filter(
        GeneratedReport.report_id == report_id,
        GeneratedReport.file_type == format.lower()
    ).first()
    
    if not generated:
        raise HTTPException(status_code=404, detail="报告文件不存在，请先生成报告")
    
    # Download from MinIO
    try:
        minio = get_minio_client()
        content = minio.download_file(generated.minio_bucket, generated.minio_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载报告失败: {str(e)}")
    
    # Get project name for filename
    cover = db.query(ReportCover).filter(ReportCover.report_id == report_id).first()
    project_name = cover.project_name if cover else "TARA报告"
    
    suffix = ".pdf" if format.lower() == "pdf" else ".xlsx"
    content_type = "application/pdf" if format.lower() == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    filename = f"{project_name}_{report_id}{suffix}"
    
    # URL encode filename for Chinese characters
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
    """
    Download report (format as path parameter)
    
    Args:
        report_id: Report ID
        format: Report format (xlsx or pdf)
    """
    return await _do_download_report(report_id, format, db)


@router.get("/reports/{report_id}/download")
async def download_report(
    report_id: str,
    format: str = "xlsx",
    db: Session = Depends(get_db)
):
    """
    Download report (format as query parameter)
    
    Args:
        report_id: Report ID
        format: Report format (xlsx or pdf)
    """
    return await _do_download_report(report_id, format, db)


@router.get("/reports/{report_id}/preview")
async def preview_report(report_id: str, db: Session = Depends(get_db)):
    """
    Get report preview data
    """
    # Get data from data service
    try:
        data = await fetch_data_from_service(report_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取报告数据失败: {str(e)}")
    
    # Get generated file info
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
    
    # Get report basic info
    report = db.query(Report).filter(Report.report_id == report_id).first()
    cover = db.query(ReportCover).filter(ReportCover.report_id == report_id).first()
    
    # Parse data to expected format
    definitions_data = data.get('definitions', {})
    assets_data = data.get('assets', {})
    attack_trees_data = data.get('attack_trees', {})
    tara_results_data = data.get('tara_results', {})
    
    # Build image URL
    def build_image_url(minio_path):
        if not minio_path:
            return None
        return f"/api/v1/reports/{report_id}/image-by-path?path={minio_path}"
    
    # Process attack trees, add image_url
    attack_trees = []
    for tree in attack_trees_data.get('attack_trees', []):
        tree_copy = dict(tree)
        if tree.get('image'):
            tree_copy['image_url'] = build_image_url(tree['image'])
        attack_trees.append(tree_copy)
    
    # Calculate statistics
    assets_list = assets_data.get('assets', [])
    tara_results_list = tara_results_data.get('results', [])
    
    statistics = {
        'assets_count': len(assets_list),
        'threats_count': len(tara_results_list),
        'high_risk_count': sum(1 for r in tara_results_list if r.get('operational_impact') in ['重大的', '严重的']),
        'measures_count': len(tara_results_list),
        'attack_trees_count': len(attack_trees)
    }
    
    # Build preview data (matching old API format)
    preview_data = {
        'id': report_id,
        'report_id': report_id,
        'name': cover.report_title if cover else 'TARA报告',
        'project_name': cover.project_name if cover else '',
        'status': report.status if report else 'completed',
        'created_at': report.created_at.isoformat() if report else '',
        'file_path': '',
        'statistics': statistics,
        'report_info': {
            'id': report_id,
            'name': cover.report_title if cover else 'TARA报告',
            'project_name': cover.project_name if cover else '',
            'version': cover.version if cover else '1.0',
            'created_at': report.created_at.isoformat() if report else '',
            'file_path': '',
            'file_size': 0,
            'statistics': statistics
        },
        'cover': data.get('cover', {}),
        'definitions': {
            **definitions_data,
            'item_boundary_image': build_image_url(definitions_data.get('item_boundary_image')),
            'system_architecture_image': build_image_url(definitions_data.get('system_architecture_image')),
            'software_architecture_image': build_image_url(definitions_data.get('software_architecture_image'))
        },
        'assets': {
            'title': '资产列表',
            'assets': assets_list,
            'dataflow_image': build_image_url(assets_data.get('dataflow_image'))
        },
        'attack_trees': {
            'title': '攻击树分析',
            'attack_trees': attack_trees
        },
        'tara_results': {
            'title': 'TARA分析结果',
            'results': tara_results_list
        },
        'downloads': downloads
    }
    
    return preview_data


@router.get("/reports/{report_id}/status")
async def get_report_status(report_id: str, db: Session = Depends(get_db)):
    """
    Get report status
    """
    report = db.query(Report).filter(Report.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    # Get generated files
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
