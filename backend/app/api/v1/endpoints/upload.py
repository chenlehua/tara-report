"""
批量上传端点
"""
import json
import uuid
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from sqlalchemy.orm import Session

from app.common.database import get_db, get_minio_client, BUCKET_IMAGES
from app.common.models import (
    Report, ReportCover, ReportDefinitions, ReportAsset,
    ReportAttackTree, ReportTARAResult, ReportImage, GeneratedReport
)
from app.generators import generate_tara_excel_from_json, generate_tara_pdf_from_json
from app.common.database import BUCKET_REPORTS

router = APIRouter()


def generate_report_id() -> str:
    """生成报告ID"""
    return f"RPT-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"


def generate_image_id() -> str:
    """生成图片ID"""
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
    批量上传JSON和图片文件，一键生成报告
    """
    # 解析JSON数据
    try:
        content = await json_file.read()
        report_data = json.loads(content.decode('utf-8'))
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"JSON文件格式错误: {str(e)}")
    
    # 生成报告ID
    report_id = generate_report_id()
    minio = get_minio_client()
    
    # 创建报告记录
    report = Report(report_id=report_id, status="pending")
    db.add(report)
    db.flush()
    
    # 辅助函数：保存上传的图片到MinIO
    async def save_image_to_minio(upload_file: UploadFile, image_type: str) -> Optional[str]:
        if not upload_file or not upload_file.filename:
            return None
        
        file_ext = Path(upload_file.filename).suffix.lower()
        if file_ext not in {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg'}:
            return None
        
        image_id = generate_image_id()
        object_name = f"{report_id}/{image_type}/{image_id}{file_ext}"
        
        try:
            img_content = await upload_file.read()
            minio.upload_bytes(
                BUCKET_IMAGES,
                object_name,
                img_content,
                upload_file.content_type or "image/png"
            )
            
            # 记录图片信息到数据库
            image_record = ReportImage(
                report_id=report_id,
                image_id=image_id,
                image_type=image_type,
                original_name=upload_file.filename,
                minio_path=object_name,
                minio_bucket=BUCKET_IMAGES,
                file_size=len(img_content),
                content_type=upload_file.content_type
            )
            db.add(image_record)
            
            return object_name
        except Exception as e:
            print(f"Failed to save image {upload_file.filename}: {e}")
            return None
    
    # 保存各类图片
    item_boundary_path = await save_image_to_minio(item_boundary_image, "item_boundary")
    system_arch_path = await save_image_to_minio(system_architecture_image, "system_architecture")
    software_arch_path = await save_image_to_minio(software_architecture_image, "software_architecture")
    dataflow_path = await save_image_to_minio(dataflow_image, "dataflow")
    
    # 保存攻击树图片
    attack_tree_paths = []
    if attack_tree_images:
        for i, img in enumerate(attack_tree_images):
            if img and img.filename:
                path = await save_image_to_minio(img, f"attack_tree_{i}")
                if path:
                    attack_tree_paths.append(path)
    
    # 保存封面数据
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
    
    # 保存相关定义
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
    
    # 保存资产列表
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
    
    # 保存攻击树
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
    
    # 保存TARA分析结果
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
    
    # 计算统计信息
    statistics = {
        'assets_count': len(assets_data.get('assets', [])),
        'attack_trees_count': len(trees),
        'tara_results_count': len(tara_data.get('results', [])),
        'images_count': len([p for p in [item_boundary_path, system_arch_path, software_arch_path, dataflow_path] + attack_tree_paths if p])
    }
    
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
