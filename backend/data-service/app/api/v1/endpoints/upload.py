"""
Batch upload endpoints
"""
import json
import uuid
import httpx
from datetime import datetime
from typing import Optional, List
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session

from app.common.database import get_db, get_minio_client
from app.common.config.settings import settings
from app.common.models import (
    Report, ReportCover, ReportDefinitions, ReportAsset,
    ReportAttackTree, ReportTARAResult, ReportImage
)
from app.common.constants.enums import ALLOWED_IMAGE_EXTENSIONS

router = APIRouter()


def generate_report_id() -> str:
    """Generate report ID"""
    return f"RPT-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"


def generate_image_id() -> str:
    """Generate image ID"""
    return f"IMG-{uuid.uuid4().hex[:12]}"


@router.post("/upload/batch")
async def upload_batch(
    json_file: UploadFile = File(..., description="JSON数据文件"),
    item_boundary_image: UploadFile = File(None, description="项目边界图"),
    system_architecture_image: UploadFile = File(None, description="系统架构图"),
    software_architecture_image: UploadFile = File(None, description="软件架构图"),
    dataflow_image: UploadFile = File(None, description="数据流图"),
    attack_tree_images: List[UploadFile] = File(None, description="攻击树图片列表"),
    db: Session = Depends(get_db)
):
    """
    Batch upload JSON and image files, generate report in one step
    
    This endpoint accepts JSON data file and all image files,
    automatically processes image saving and path association,
    then saves to database.
    Returns report ID for subsequent Excel/PDF report generation.
    """
    # Parse JSON data
    try:
        content = await json_file.read()
        report_data = json.loads(content.decode('utf-8'))
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"JSON文件格式错误: {str(e)}")
    
    # Generate report ID
    report_id = generate_report_id()
    minio = get_minio_client()
    
    # Create report record
    report = Report(report_id=report_id, status="pending")
    db.add(report)
    db.flush()
    
    # Helper function: save uploaded image to MinIO
    async def save_image_to_minio(upload_file: UploadFile, image_type: str) -> Optional[str]:
        if not upload_file or not upload_file.filename:
            return None
        
        file_ext = Path(upload_file.filename).suffix.lower()
        if file_ext not in ALLOWED_IMAGE_EXTENSIONS:
            return None
        
        image_id = generate_image_id()
        object_name = f"{report_id}/{image_type}/{image_id}{file_ext}"
        
        try:
            img_content = await upload_file.read()
            minio.upload_bytes(
                settings.BUCKET_IMAGES,
                object_name,
                img_content,
                upload_file.content_type or "image/png"
            )
            
            # Record image info to database
            image_record = ReportImage(
                report_id=report_id,
                image_id=image_id,
                image_type=image_type,
                original_name=upload_file.filename,
                minio_path=object_name,
                minio_bucket=settings.BUCKET_IMAGES,
                file_size=len(img_content),
                content_type=upload_file.content_type
            )
            db.add(image_record)
            
            return object_name
        except Exception as e:
            print(f"Failed to save image {upload_file.filename}: {e}")
            return None
    
    # Save various images
    item_boundary_path = await save_image_to_minio(item_boundary_image, "item_boundary")
    system_arch_path = await save_image_to_minio(system_architecture_image, "system_architecture")
    software_arch_path = await save_image_to_minio(software_architecture_image, "software_architecture")
    dataflow_path = await save_image_to_minio(dataflow_image, "dataflow")
    
    # Save attack tree images
    attack_tree_paths = []
    if attack_tree_images:
        for i, img in enumerate(attack_tree_images):
            if img and img.filename:
                path = await save_image_to_minio(img, f"attack_tree_{i}")
                if path:
                    attack_tree_paths.append(path)
    
    # Save cover data
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
    
    # Save definitions
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
    
    # Save assets
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
    
    # Save attack trees
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
    
    # Save TARA results
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
    
    # Calculate statistics
    statistics = {
        'assets_count': len(assets_data.get('assets', [])),
        'attack_trees_count': len(trees),
        'tara_results_count': len(tara_data.get('results', [])),
        'images_count': len([p for p in [item_boundary_path, system_arch_path, software_arch_path, dataflow_path] + attack_tree_paths if p])
    }
    
    # Automatically call report service to generate Excel and PDF reports
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            # Generate Excel report
            excel_resp = await client.post(
                f"{settings.REPORT_SERVICE_URL}/api/v1/reports/{report_id}/generate",
                params={"format": "xlsx"}
            )
            if excel_resp.status_code == 200:
                print(f"Excel report {report_id} generated successfully")
            else:
                print(f"Failed to generate Excel report {report_id}: {excel_resp.text}")
            
            # Generate PDF report
            pdf_resp = await client.post(
                f"{settings.REPORT_SERVICE_URL}/api/v1/reports/{report_id}/generate",
                params={"format": "pdf"}
            )
            if pdf_resp.status_code == 200:
                print(f"PDF report {report_id} generated successfully")
            else:
                print(f"Failed to generate PDF report {report_id}: {pdf_resp.text}")
    except Exception as e:
        print(f"Failed to call report service: {e}")
        # Don't block return, let user manually generate
    
    return {
        'success': True,
        'message': '报告生成成功',
        'report_id': report_id,
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
        'download_url': f"/api/v1/reports/{report_id}/download",
        'preview_url': f"/api/v1/reports/{report_id}/preview"
    }
