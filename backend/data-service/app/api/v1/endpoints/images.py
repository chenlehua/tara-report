"""
Image management endpoints
"""
import io
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.common.database import get_db, get_minio_client
from app.common.config.settings import settings
from app.common.models import ReportImage
from app.common.constants.enums import ALLOWED_IMAGE_EXTENSIONS, VALID_IMAGE_TYPES

router = APIRouter()

# Temporary image storage (for images uploaded before creating report)
temp_images_db: dict = {}


def generate_image_id() -> str:
    """Generate image ID"""
    return f"IMG-{uuid.uuid4().hex[:12]}"


@router.post("/images/upload")
async def upload_image(
    file: UploadFile = File(...),
    image_type: str = Form(..., description="图片类型: item_boundary, system_architecture, software_architecture, dataflow, attack_tree"),
    db: Session = Depends(get_db)
):
    """
    Upload image (temporary storage)
    
    Supported image types:
    - item_boundary: Item boundary diagram
    - system_architecture: System architecture diagram
    - software_architecture: Software architecture diagram
    - dataflow: Data flow diagram
    - attack_tree: Attack tree diagram
    """
    # Validate file type
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式。支持的格式: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}"
        )
    
    # Validate image type
    if image_type not in VALID_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"无效的图片类型。有效类型: {', '.join(VALID_IMAGE_TYPES)}"
        )
    
    # Generate image ID
    image_id = generate_image_id()
    
    # Read file content
    content = await file.read()
    
    # Upload to MinIO (using temp directory)
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
    
    # Record temporary image info
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
    """Get image"""
    # First check temporary storage
    if image_id in temp_images_db:
        image_info = temp_images_db[image_id]
        try:
            minio = get_minio_client()
            content = minio.download_file(settings.BUCKET_IMAGES, image_info['minio_path'])
            return StreamingResponse(
                io.BytesIO(content),
                media_type=image_info.get('content_type', 'image/png')
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"获取图片失败: {str(e)}")
    
    # Query from database
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
