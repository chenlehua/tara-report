"""
图片管理API端点
"""
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict

import aiofiles
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse

from app.common.config import settings
from app.common.schemas import ImageUploadResponse

router = APIRouter()

# 图片存储映射（内存存储，生产环境应使用数据库）
images_db: Dict[str, Dict[str, str]] = {}


def generate_image_id() -> str:
    """生成图片ID"""
    return f"IMG-{uuid.uuid4().hex[:12]}"


@router.post("/upload", response_model=ImageUploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    image_type: str = Form(..., description="图片类型: item_boundary, system_architecture, software_architecture, dataflow, attack_tree")
):
    """
    上传图片
    
    支持的图片类型:
    - item_boundary: 项目边界图
    - system_architecture: 系统架构图
    - software_architecture: 软件架构图
    - dataflow: 数据流图
    - attack_tree: 攻击树图
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
    
    # 生成图片ID和保存路径
    image_id = generate_image_id()
    filename = f"{image_id}{file_ext}"
    file_path = settings.IMAGES_DIR / filename
    
    # 保存文件
    try:
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")
    
    # 记录图片信息
    images_db[image_id] = {
        'id': image_id,
        'type': image_type,
        'filename': filename,
        'path': str(file_path),
        'original_name': file.filename,
        'created_at': datetime.now().isoformat()
    }
    
    return ImageUploadResponse(
        success=True,
        message="图片上传成功",
        image_id=image_id,
        image_url=f"/api/v1/images/{image_id}",
        image_type=image_type
    )


@router.get("/{image_id}")
async def get_image(image_id: str):
    """获取图片"""
    if image_id not in images_db:
        raise HTTPException(status_code=404, detail="图片不存在")
    
    image_info = images_db[image_id]
    file_path = Path(image_info['path'])
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="图片文件不存在")
    
    return FileResponse(file_path)


def get_image_path(image_id: str) -> str:
    """获取图片路径（供其他模块使用）"""
    if image_id and image_id in images_db:
        return images_db[image_id]['path']
    return None


def get_images_db() -> Dict[str, Dict[str, str]]:
    """获取图片数据库（供其他模块使用）"""
    return images_db
