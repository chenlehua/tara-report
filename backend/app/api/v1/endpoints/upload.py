"""
批量上传API端点
"""
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

import aiofiles
from fastapi import APIRouter, HTTPException, UploadFile, File

from app.common.config import settings
from app.generators import generate_tara_excel_from_json
from .images import images_db
from .reports import reports_db, calculate_statistics, generate_report_id

router = APIRouter()


def generate_image_id() -> str:
    """生成图片ID"""
    return f"IMG-{uuid.uuid4().hex[:12]}"


@router.post("/batch")
async def upload_batch(
    json_file: UploadFile = File(..., description="JSON数据文件"),
    item_boundary_image: UploadFile = File(None, description="项目边界图"),
    system_architecture_image: UploadFile = File(None, description="系统架构图"),
    software_architecture_image: UploadFile = File(None, description="软件架构图"),
    dataflow_image: UploadFile = File(None, description="数据流图"),
    attack_tree_images: List[UploadFile] = File(None, description="攻击树图片列表")
):
    """
    批量上传JSON和图片文件，一键生成报告
    
    这个端点同时接收JSON数据文件和所有图片文件，
    自动处理图片保存和路径关联，然后生成Excel报告。
    支持上传多张攻击树图片。
    """
    # 解析JSON数据
    try:
        content = await json_file.read()
        report_data = json.loads(content.decode('utf-8'))
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"JSON文件格式错误: {str(e)}")
    
    # 确保definitions和assets存在
    if 'definitions' not in report_data:
        report_data['definitions'] = {}
    if 'assets' not in report_data:
        report_data['assets'] = {}
    if 'attack_trees' not in report_data:
        report_data['attack_trees'] = {'attack_trees': []}
    
    # 辅助函数：保存上传的图片并返回路径
    async def save_uploaded_image(upload_file: UploadFile, image_type: str) -> Optional[str]:
        if not upload_file or not upload_file.filename:
            return None
        
        file_ext = Path(upload_file.filename).suffix.lower()
        if file_ext not in {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg'}:
            return None
        
        image_id = generate_image_id()
        filename = f"{image_id}{file_ext}"
        file_path = settings.IMAGES_DIR / filename
        
        try:
            async with aiofiles.open(file_path, 'wb') as f:
                img_content = await upload_file.read()
                await f.write(img_content)
            
            # 记录图片信息
            images_db[image_id] = {
                'id': image_id,
                'type': image_type,
                'filename': filename,
                'path': str(file_path),
                'original_name': upload_file.filename,
                'created_at': datetime.now().isoformat()
            }
            
            return str(file_path)
        except Exception as e:
            print(f"Failed to save image {upload_file.filename}: {e}")
            return None
    
    # 保存各类图片并更新JSON数据中的路径
    image_paths = {}
    
    if item_boundary_image and item_boundary_image.filename:
        path = await save_uploaded_image(item_boundary_image, 'item_boundary')
        if path:
            report_data['definitions']['item_boundary_image'] = path
            image_paths['item_boundary'] = path
    
    if system_architecture_image and system_architecture_image.filename:
        path = await save_uploaded_image(system_architecture_image, 'system_architecture')
        if path:
            report_data['definitions']['system_architecture_image'] = path
            image_paths['system_architecture'] = path
    
    if software_architecture_image and software_architecture_image.filename:
        path = await save_uploaded_image(software_architecture_image, 'software_architecture')
        if path:
            report_data['definitions']['software_architecture_image'] = path
            image_paths['software_architecture'] = path
    
    if dataflow_image and dataflow_image.filename:
        path = await save_uploaded_image(dataflow_image, 'dataflow')
        if path:
            report_data['assets']['dataflow_image'] = path
            image_paths['dataflow'] = path
    
    # 处理攻击树图片
    attack_tree_paths = []
    if attack_tree_images:
        existing_trees = report_data.get('attack_trees', {}).get('attack_trees', [])
        
        for i, attack_img in enumerate(attack_tree_images):
            if attack_img and attack_img.filename:
                path = await save_uploaded_image(attack_img, f'attack_tree_{i}')
                if path:
                    attack_tree_paths.append(path)
                    
                    # 更新或创建攻击树条目
                    if i < len(existing_trees):
                        existing_trees[i]['image'] = path
                    else:
                        existing_trees.append({
                            'asset_id': f'AT{i+1:03d}',
                            'asset_name': f'攻击树 {i+1}',
                            'title': f'攻击树分析 {i+1}',
                            'image': path
                        })
        
        report_data['attack_trees']['attack_trees'] = existing_trees
        image_paths['attack_trees'] = attack_tree_paths
    
    # 生成报告ID和文件路径
    report_id = generate_report_id()
    output_filename = f"{report_id}.xlsx"
    output_path = settings.REPORTS_DIR / output_filename
    
    # 生成Excel报告
    try:
        generate_tara_excel_from_json(str(output_path), report_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"报告生成失败: {str(e)}")
    
    # 计算统计信息
    statistics = calculate_statistics(report_data)
    
    # 获取文件大小
    file_size = output_path.stat().st_size if output_path.exists() else 0
    
    # 存储报告信息
    report_info = {
        'id': report_id,
        'name': report_data.get('cover', {}).get('report_title', 'TARA报告'),
        'project_name': report_data.get('cover', {}).get('project_name', '未命名项目'),
        'version': report_data.get('cover', {}).get('version', '1.0'),
        'created_at': datetime.now().isoformat(),
        'status': 'completed',
        'file_path': str(output_path),
        'file_size': file_size,
        'statistics': statistics,
        'image_paths': image_paths,
        'data': report_data
    }
    reports_db[report_id] = report_info
    
    # 构建响应
    return {
        'success': True,
        'message': '报告生成成功',
        'report_info': {
            'id': report_id,
            'name': report_info['name'],
            'version': report_info['version'],
            'created_at': report_info['created_at'],
            'file_path': report_info['file_path'],
            'file_size': file_size,
            'statistics': statistics
        },
        'download_url': f"/api/v1/reports/{report_id}/download",
        'preview_url': f"/api/v1/reports/{report_id}/preview"
    }
