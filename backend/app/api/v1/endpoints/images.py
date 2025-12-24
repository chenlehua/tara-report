"""
图片管理端点
"""
import io
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.common.database import get_db, get_minio_client, BUCKET_IMAGES
from app.common.models import ReportImage

router = APIRouter()

# 临时图片存储（用于在创建报告前上传图片）
temp_images_db: dict = {}


def generate_image_id() -> str:
    """生成图片ID"""
    return f"IMG-{uuid.uuid4().hex[:12]}"


@router.post("/images/upload")
async def upload_image(
    file: UploadFile = File(...),
    image_type: str = Form(..., description="图片类型: item_boundary, system_architecture, software_architecture, dataflow, attack_tree"),
    db: Session = Depends(get_db)
):
    """
    上传图片（临时存储）
    
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
    
    # 生成图片ID
    image_id = generate_image_id()
    
    # 读取文件内容
    content = await file.read()
    
    # 上传到MinIO（使用临时目录）
    minio = get_minio_client()
    object_name = f"temp/{image_id}{file_ext}"
    
    try:
        minio.upload_bytes(
            BUCKET_IMAGES,
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
        "image_url": f"/api/v1/images/{image_id}",
        "image_type": image_type
    }


@router.get("/images/{image_id}")
async def get_image(image_id: str, db: Session = Depends(get_db)):
    """获取图片"""
    # 先从临时存储查找
    if image_id in temp_images_db:
        image_info = temp_images_db[image_id]
        try:
            minio = get_minio_client()
            content = minio.download_file(BUCKET_IMAGES, image_info['minio_path'])
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
        minio = get_minio_client()
        content = minio.download_file(image.minio_bucket, image.minio_path)
        return StreamingResponse(
            io.BytesIO(content),
            media_type=image.content_type or "image/png"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取图片失败: {str(e)}")
