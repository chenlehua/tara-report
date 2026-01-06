"""
Report management endpoints
报告管理接口

报告列表和详情数据从 data-service 获取
生成的报告文件信息存储在 report-service 自己的数据库表中
"""
import io
import os
import tempfile
import httpx
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.common.database import get_db, get_minio_client
from app.common.config.settings import settings
from app.common.models import (
    RSReport, RSReportCover, RSGeneratedFile, RSReportStatistics
)
from app.common.utils.calculations import calculate_tara_derived_columns
from app.generators import generate_tara_excel_from_json, generate_tara_pdf_from_json

router = APIRouter()


# ==================== Helper functions ====================

async def fetch_report_list_from_data_service(page: int = 1, page_size: int = 20) -> Dict[str, Any]:
    """
    从 data-service 获取报告列表
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # 获取报告列表（通过查询 data-service 的数据库）
            # 由于 data-service 没有专门的列表接口，我们需要获取所有报告的基本信息
            # 这里我们假设 data-service 有一个列表接口，如果没有则需要添加
            resp = await client.get(
                f"{settings.DATA_SERVICE_URL}/api/v1/reports",
                params={"page": page, "page_size": page_size}
            )
            if resp.status_code == 200:
                return resp.json()
            else:
                return {"success": True, "total": 0, "page": page, "page_size": page_size, "reports": []}
        except Exception as e:
            print(f"Failed to fetch report list from data service: {e}")
            return {"success": True, "total": 0, "page": page, "page_size": page_size, "reports": []}


async def fetch_data_from_service(report_id: str) -> Dict[str, Any]:
    """
    Fetch report data from data service
    从 data-service 获取报告完整数据
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
        
        # Get image paths
        images_resp = await client.get(f"{settings.DATA_SERVICE_URL}/api/v1/reports/{report_id}/images")
        if images_resp.status_code != 200:
            raise HTTPException(status_code=404, detail="无法获取图片路径数据")
        images_data = images_resp.json()
        
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
        "images": images_data,
        "assets": assets_data,
        "attack_trees": attack_trees_data,
        "tara_results": tara_data
    }


async def fetch_report_basic_info(report_id: str) -> Optional[Dict[str, Any]]:
    """
    从 data-service 获取报告基本信息
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            cover_resp = await client.get(f"{settings.DATA_SERVICE_URL}/api/v1/reports/{report_id}/cover")
            if cover_resp.status_code == 200:
                return cover_resp.json()
        except Exception as e:
            print(f"Failed to fetch report basic info: {e}")
    return None


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
    
    # Get image paths from images endpoint
    images = data.get('images', {})
    definitions = data.get('definitions', {})
    assets = data.get('assets', {})
    
    # Download definition images from images data
    if images.get('item_boundary_image'):
        local_path = await download_image_from_minio(images['item_boundary_image'], report_id)
        definitions['item_boundary_image'] = local_path
    
    if images.get('system_architecture_image'):
        local_path = await download_image_from_minio(images['system_architecture_image'], report_id)
        definitions['system_architecture_image'] = local_path
    
    if images.get('software_architecture_image'):
        local_path = await download_image_from_minio(images['software_architecture_image'], report_id)
        definitions['software_architecture_image'] = local_path
    
    # Download dataflow image from images data
    if images.get('dataflow_image'):
        local_path = await download_image_from_minio(images['dataflow_image'], report_id)
        assets['dataflow_image'] = local_path
    
    # Download attack tree images
    attack_trees = data.get('attack_trees', {})
    for tree in attack_trees.get('attack_trees', []):
        if tree.get('image'):
            local_path = await download_image_from_minio(tree['image'], report_id)
            tree['image'] = local_path
    
    # Add calculated columns to TARA results for report generation
    tara_results = data.get('tara_results', {})
    tara_results['results'] = [
        calculate_tara_derived_columns(result) 
        for result in tara_results.get('results', [])
    ]
    
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


def get_generated_files_info(report_id: str, db: Session) -> Dict[str, Any]:
    """
    获取报告已生成的文件信息
    """
    generated_files = db.query(RSGeneratedFile).filter(
        RSGeneratedFile.report_id == report_id
    ).all()
    
    downloads = {}
    for gf in generated_files:
        downloads[gf.file_type] = {
            "url": f"/api/v1/reports/{report_id}/download?format={gf.file_type}",
            "file_size": gf.file_size,
            "generated_at": gf.generated_at.isoformat() if gf.generated_at else None
        }
    return downloads


# ==================== API endpoints ====================

@router.get("/reports")
async def list_reports(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    """
    获取报告列表
    
    从 data-service 获取报告数据，并补充本地的生成文件信息
    """
    # 从 data-service 获取报告列表
    data_service_result = await fetch_report_list_from_data_service(page, page_size)
    
    # 如果 data-service 返回了数据，补充生成文件信息
    reports = data_service_result.get("reports", [])
    for report in reports:
        report_id = report.get("report_id")
        if report_id:
            # 获取本地存储的生成文件信息
            downloads = get_generated_files_info(report_id, db)
            report["downloads"] = downloads
    
    return {
        "success": True,
        "total": data_service_result.get("total", 0),
        "page": page,
        "page_size": page_size,
        "reports": reports
    }


@router.get("/reports/{report_id}")
async def get_report_info(report_id: str, db: Session = Depends(get_db)):
    """
    获取报告完整信息（用于预览）
    
    从 data-service 获取报告数据
    """
    # 从 data-service 获取报告数据
    try:
        data = await fetch_data_from_service(report_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取报告数据失败: {str(e)}")
    
    cover_data = data.get('cover', {})
    definitions_data = data.get('definitions', {})
    images_data = data.get('images', {})
    assets_data = data.get('assets', {})
    attack_trees_data = data.get('attack_trees', {})
    tara_results_data = data.get('tara_results', {})
    
    # Build image URL
    def build_image_url(minio_path):
        if not minio_path:
            return None
        return f"/api/v1/reports/{report_id}/image-by-path?path={minio_path}"
    
    # Process assets
    assets_list = assets_data.get('assets', [])
    
    # Process attack trees, add image_url
    attack_trees_list = []
    for tree in attack_trees_data.get('attack_trees', []):
        tree_copy = dict(tree)
        if tree.get('image'):
            tree_copy['image_url'] = build_image_url(tree['image'])
        attack_trees_list.append(tree_copy)
    
    # Process TARA results - add calculated columns
    tara_results_list = [
        calculate_tara_derived_columns(result) 
        for result in tara_results_data.get('results', [])
    ]
    
    # Statistics
    statistics = {
        'assets_count': len(assets_list),
        'threats_count': len(tara_results_list),
        'high_risk_count': sum(1 for r in tara_results_list if r.get('operational_impact') in ['重大的', '严重的']),
        'measures_count': len(tara_results_list),
        'attack_trees_count': len(attack_trees_list)
    }
    
    # 获取本地存储的生成文件信息
    downloads = get_generated_files_info(report_id, db)
    
    # Return format consistent with before refactoring
    return {
        "id": report_id,
        "report_id": report_id,
        "name": cover_data.get('report_title', 'TARA报告'),
        "project_name": cover_data.get('project_name', ''),
        "status": "completed",
        "created_at": datetime.now().isoformat(),
        "updated_at": None,
        "file_path": "",
        "statistics": statistics,
        "downloads": downloads,
        "cover": cover_data,
        "definitions": {
            **definitions_data,
            'item_boundary_image': build_image_url(images_data.get('item_boundary_image')),
            'system_architecture_image': build_image_url(images_data.get('system_architecture_image')),
            'software_architecture_image': build_image_url(images_data.get('software_architecture_image'))
        },
        "assets": {
            "title": assets_data.get('title', '资产列表'),
            "assets": assets_list,
            "dataflow_image": build_image_url(images_data.get('dataflow_image'))
        },
        "attack_trees": {
            "title": attack_trees_data.get('title', '攻击树分析'),
            "attack_trees": attack_trees_list
        },
        "tara_results": {
            "title": tara_results_data.get('title', 'TARA分析结果'),
            "results": tara_results_list
        }
    }


@router.delete("/reports/{report_id}")
async def delete_report(report_id: str, db: Session = Depends(get_db)):
    """
    删除报告及其所有关联资源
    
    通过调用 data-service 的删除接口删除报告数据
    同时删除本地存储的生成文件信息
    """
    # 调用 data-service 删除报告
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.delete(f"{settings.DATA_SERVICE_URL}/api/v1/reports/{report_id}")
            if resp.status_code == 404:
                raise HTTPException(status_code=404, detail="报告不存在")
            elif resp.status_code != 200:
                raise HTTPException(status_code=500, detail="删除报告失败")
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"无法连接到数据服务: {str(e)}")
    
    # 删除本地存储的生成文件
    minio = get_minio_client()
    generated_files = db.query(RSGeneratedFile).filter(RSGeneratedFile.report_id == report_id).all()
    for gf in generated_files:
        try:
            minio.delete_file(gf.minio_bucket, gf.minio_path)
        except:
            pass
        db.delete(gf)
    
    # 删除本地报告记录（如果有）
    local_report = db.query(RSReport).filter(RSReport.report_id == report_id).first()
    if local_report:
        db.delete(local_report)
    
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
    生成报告
    
    从 data-service 获取数据，生成报告文件后上传到 MinIO
    生成文件信息存储到本地数据库
    """
    # Prepare data from data-service
    try:
        data = await prepare_report_data(report_id)
    except HTTPException:
        raise
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
        
        # 确保本地有报告记录（用于关联生成文件）
        local_report = db.query(RSReport).filter(RSReport.report_id == report_id).first()
        if not local_report:
            cover_data = data.get('cover', {})
            local_report = RSReport(
                report_id=report_id,
                project_name=cover_data.get('project_name', ''),
                report_title=cover_data.get('report_title', 'TARA报告'),
                report_title_en=cover_data.get('report_title_en', ''),
                status='completed',
                source_type='sync'
            )
            db.add(local_report)
            db.flush()
        
        # Record to database
        existing = db.query(RSGeneratedFile).filter(
            RSGeneratedFile.report_id == report_id,
            RSGeneratedFile.file_type == format.lower()
        ).first()
        
        cover_data = data.get('cover', {})
        project_name = cover_data.get('project_name', 'TARA报告')
        file_name = f"{project_name}_{report_id}{suffix}"
        
        if existing:
            existing.minio_path = object_name
            existing.file_size = len(file_content)
            existing.file_name = file_name
            existing.generated_at = datetime.now()
        else:
            generated = RSGeneratedFile(
                report_id=report_id,
                file_type=format.lower(),
                file_name=file_name,
                minio_path=object_name,
                minio_bucket=settings.BUCKET_REPORTS,
                file_size=len(file_content)
            )
            db.add(generated)
        
        db.commit()
        
        # Clean up temporary image files
        cleanup_temp_files(data)
        
        return {
            "success": True,
            "message": "报告生成成功",
            "report_id": report_id,
            "format": format.lower(),
            "file_size": len(file_content),
            "download_url": f"/api/v1/reports/{report_id}/download?format={format.lower()}",
            "file_name": file_name
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
    """
    # Find generated report
    generated = db.query(RSGeneratedFile).filter(
        RSGeneratedFile.report_id == report_id,
        RSGeneratedFile.file_type == format.lower()
    ).first()
    
    if not generated:
        raise HTTPException(status_code=404, detail="报告文件不存在，请先生成报告")
    
    # Download from MinIO
    try:
        minio = get_minio_client()
        content = minio.download_file(generated.minio_bucket, generated.minio_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载报告失败: {str(e)}")
    
    # Get filename
    filename = generated.file_name
    if not filename:
        # Fallback to getting from data-service
        cover_data = await fetch_report_basic_info(report_id)
        project_name = cover_data.get('project_name', 'TARA报告') if cover_data else 'TARA报告'
        suffix = ".pdf" if format.lower() == "pdf" else ".xlsx"
        filename = f"{project_name}_{report_id}{suffix}"
    
    content_type = "application/pdf" if format.lower() == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    
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
    下载报告（格式作为路径参数）
    """
    return await _do_download_report(report_id, format, db)


@router.get("/reports/{report_id}/download")
async def download_report(
    report_id: str,
    format: str = "xlsx",
    db: Session = Depends(get_db)
):
    """
    下载报告（格式作为查询参数）
    """
    return await _do_download_report(report_id, format, db)


@router.get("/reports/{report_id}/preview")
async def preview_report(report_id: str, db: Session = Depends(get_db)):
    """
    获取报告预览数据
    """
    # Get data from data service
    try:
        data = await fetch_data_from_service(report_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取报告数据失败: {str(e)}")
    
    # 获取本地存储的生成文件信息
    downloads = get_generated_files_info(report_id, db)
    
    # Parse data to expected format
    cover_data = data.get('cover', {})
    definitions_data = data.get('definitions', {})
    images_data = data.get('images', {})
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
    # Add calculated columns to TARA results
    tara_results_list = [
        calculate_tara_derived_columns(result) 
        for result in tara_results_data.get('results', [])
    ]
    
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
        'name': cover_data.get('report_title', 'TARA报告'),
        'project_name': cover_data.get('project_name', ''),
        'status': 'completed',
        'created_at': datetime.now().isoformat(),
        'file_path': '',
        'statistics': statistics,
        'report_info': {
            'id': report_id,
            'name': cover_data.get('report_title', 'TARA报告'),
            'project_name': cover_data.get('project_name', ''),
            'version': cover_data.get('version', '1.0'),
            'created_at': datetime.now().isoformat(),
            'file_path': '',
            'file_size': 0,
            'statistics': statistics
        },
        'cover': cover_data,
        'definitions': {
            **definitions_data,
            'item_boundary_image': build_image_url(images_data.get('item_boundary_image')),
            'system_architecture_image': build_image_url(images_data.get('system_architecture_image')),
            'software_architecture_image': build_image_url(images_data.get('software_architecture_image'))
        },
        'assets': {
            'title': assets_data.get('title', '资产列表'),
            'assets': assets_list,
            'dataflow_image': build_image_url(images_data.get('dataflow_image'))
        },
        'attack_trees': {
            'title': attack_trees_data.get('title', '攻击树分析'),
            'attack_trees': attack_trees
        },
        'tara_results': {
            'title': tara_results_data.get('title', 'TARA分析结果'),
            'results': tara_results_list
        },
        'downloads': downloads
    }
    
    return preview_data


@router.get("/reports/{report_id}/status")
async def get_report_status(report_id: str, db: Session = Depends(get_db)):
    """
    获取报告状态
    """
    # 先尝试从 data-service 获取基本信息
    cover_data = await fetch_report_basic_info(report_id)
    if not cover_data:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    # 获取生成文件信息
    generated_files = db.query(RSGeneratedFile).filter(
        RSGeneratedFile.report_id == report_id
    ).all()
    
    return {
        "report_id": report_id,
        "status": "completed",
        "created_at": datetime.now().isoformat(),
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
    """
    根据 MinIO 路径获取图片
    """
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
