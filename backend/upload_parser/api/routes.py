"""
上传解析模块API路由
"""
import json
from typing import Optional, List
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db, ImageType
from ..storage import get_minio_storage, MinioStorageService
from ..models import (
    BaseResponse, CreateReportResponse, ImageUploadResponse, BatchImageUploadResponse,
    CoverRequest, CoverResponse, DefinitionRequest, DefinitionResponse,
    AssetRequest, AssetResponse, AssetsListResponse,
    AttackTreeRequest, AttackTreeResponse, AttackTreesListResponse,
    TaraResultRequest, TaraResultResponse, TaraResultsListResponse,
    FullReportDataResponse, JsonUploadResponse, ImageInfo
)
from .services import ReportParserService
from ..config import settings


# 创建路由
router = APIRouter(prefix="/api/upload-parser", tags=["上传解析模块"])


# ==================== 报告管理 ====================

@router.post("/reports", response_model=CreateReportResponse)
async def create_report(
    name: Optional[str] = Form(None, description="报告名称"),
    db: AsyncSession = Depends(get_db)
):
    """
    创建新报告
    
    自动生成报告ID并返回
    """
    service = ReportParserService(db)
    report = await service.create_report(name)
    
    return CreateReportResponse(
        success=True,
        message="报告创建成功",
        report_id=report.id
    )


@router.delete("/reports/{report_id}", response_model=BaseResponse)
async def delete_report(
    report_id: str,
    db: AsyncSession = Depends(get_db)
):
    """删除报告及其所有关联数据"""
    service = ReportParserService(db)
    success = await service.delete_report(report_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    return BaseResponse(success=True, message="报告删除成功")


# ==================== 图片上传 ====================

@router.post("/reports/{report_id}/images", response_model=ImageUploadResponse)
async def upload_image(
    report_id: str,
    file: UploadFile = File(..., description="图片文件"),
    image_type: str = Form(..., description="图片类型: item_boundary, system_architecture, software_architecture, dataflow, attack_tree, other"),
    attack_tree_id: Optional[str] = Form(None, description="攻击树ID(当image_type为attack_tree时)"),
    db: AsyncSession = Depends(get_db)
):
    """
    上传图片
    
    图片将保存至MinIO，元数据存储至MySQL
    """
    # 验证文件类型
    file_ext = Path(file.filename).suffix.lower() if file.filename else ''
    if file_ext not in settings.ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式。支持的格式: {', '.join(settings.ALLOWED_IMAGE_EXTENSIONS)}"
        )
    
    # 验证图片类型
    valid_types = ['item_boundary', 'system_architecture', 'software_architecture', 'dataflow', 'attack_tree', 'other']
    if image_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"无效的图片类型。有效类型: {', '.join(valid_types)}"
        )
    
    # 读取文件内容
    file_data = await file.read()
    if len(file_data) > settings.MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"文件过大。最大允许: {settings.MAX_IMAGE_SIZE // 1024 // 1024}MB"
        )
    
    # 上传图片
    service = ReportParserService(db)
    try:
        image = await service.upload_image(
            report_id=report_id,
            file_data=file_data,
            filename=file.filename or "image",
            image_type=image_type,
            content_type=file.content_type or "image/png",
            attack_tree_id=attack_tree_id
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图片上传失败: {str(e)}")
    
    return ImageUploadResponse(
        success=True,
        message="图片上传成功",
        image_id=image.id,
        image_url=service.get_image_url(image),
        image_type=image_type,
        file_size=image.file_size or 0
    )


@router.post("/reports/{report_id}/images/batch", response_model=BatchImageUploadResponse)
async def batch_upload_images(
    report_id: str,
    files: List[UploadFile] = File(..., description="图片文件列表"),
    image_types: str = Form(..., description="图片类型列表(逗号分隔)"),
    db: AsyncSession = Depends(get_db)
):
    """批量上传图片"""
    types_list = [t.strip() for t in image_types.split(',')]
    
    if len(files) != len(types_list):
        raise HTTPException(
            status_code=400,
            detail="文件数量与类型数量不匹配"
        )
    
    service = ReportParserService(db)
    images = []
    
    for file, image_type in zip(files, types_list):
        file_ext = Path(file.filename).suffix.lower() if file.filename else ''
        if file_ext not in settings.ALLOWED_IMAGE_EXTENSIONS:
            continue
        
        file_data = await file.read()
        if len(file_data) > settings.MAX_IMAGE_SIZE:
            continue
        
        try:
            image = await service.upload_image(
                report_id=report_id,
                file_data=file_data,
                filename=file.filename or "image",
                image_type=image_type,
                content_type=file.content_type or "image/png"
            )
            images.append(service.image_to_info(image))
        except Exception as e:
            print(f"Failed to upload {file.filename}: {e}")
            continue
    
    return BatchImageUploadResponse(
        success=True,
        message=f"成功上传 {len(images)} 张图片",
        report_id=report_id,
        images=images
    )


@router.get("/images/{image_id}")
async def get_image(
    image_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取图片(返回图片数据)"""
    service = ReportParserService(db)
    image = await service.get_image(image_id)
    
    if not image:
        raise HTTPException(status_code=404, detail="图片不存在")
    
    try:
        minio = get_minio_storage()
        image_data = minio.get_image_data(image.minio_path)
        
        return StreamingResponse(
            iter([image_data]),
            media_type=image.content_type or "image/png",
            headers={
                "Content-Disposition": f"inline; filename={image.original_name or 'image'}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取图片失败: {str(e)}")


@router.get("/images/{image_id}/info", response_model=ImageInfo)
async def get_image_info(
    image_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取图片信息"""
    service = ReportParserService(db)
    image = await service.get_image(image_id)
    
    if not image:
        raise HTTPException(status_code=404, detail="图片不存在")
    
    return service.image_to_info(image)


# ==================== 封面管理 ====================

@router.get("/reports/{report_id}/cover", response_model=CoverResponse)
async def get_cover(
    report_id: str,
    db: AsyncSession = Depends(get_db)
):
    """根据报告ID获取封面"""
    service = ReportParserService(db)
    cover = await service.get_cover(report_id)
    
    if not cover:
        raise HTTPException(status_code=404, detail="封面不存在")
    
    return cover


# ==================== 项目定义管理 ====================

@router.get("/reports/{report_id}/definitions", response_model=DefinitionResponse)
async def get_definition(
    report_id: str,
    db: AsyncSession = Depends(get_db)
):
    """根据报告ID获取项目定义"""
    service = ReportParserService(db)
    definition = await service.get_definition(report_id)
    
    if not definition:
        raise HTTPException(status_code=404, detail="项目定义不存在")
    
    return definition


# ==================== 资产管理 ====================

@router.get("/reports/{report_id}/assets", response_model=AssetsListResponse)
async def get_assets(
    report_id: str,
    db: AsyncSession = Depends(get_db)
):
    """根据报告ID获取资产信息"""
    service = ReportParserService(db)
    assets = await service.get_assets(report_id)
    
    if not assets:
        raise HTTPException(status_code=404, detail="资产信息不存在")
    
    return assets


# ==================== 攻击树管理 ====================

@router.get("/reports/{report_id}/attack-trees", response_model=AttackTreesListResponse)
async def get_attack_trees(
    report_id: str,
    db: AsyncSession = Depends(get_db)
):
    """根据报告ID获取攻击树"""
    service = ReportParserService(db)
    attack_trees = await service.get_attack_trees(report_id)
    
    if not attack_trees:
        raise HTTPException(status_code=404, detail="攻击树不存在")
    
    return attack_trees


# ==================== TARA结果管理 ====================

@router.get("/reports/{report_id}/tara-results", response_model=TaraResultsListResponse)
async def get_tara_results(
    report_id: str,
    db: AsyncSession = Depends(get_db)
):
    """根据报告ID获取TARA分析结果"""
    service = ReportParserService(db)
    tara_results = await service.get_tara_results(report_id)
    
    if not tara_results:
        raise HTTPException(status_code=404, detail="TARA分析结果不存在")
    
    return tara_results


# ==================== 完整报告数据 ====================

@router.get("/reports/{report_id}/full-data", response_model=FullReportDataResponse)
async def get_full_report_data(
    report_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    根据报告ID获取完整报告数据
    
    用于报告生成模块调用
    """
    service = ReportParserService(db)
    full_data = await service.get_full_report_data(report_id)
    
    if not full_data:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    return full_data


# ==================== JSON上传解析 ====================

@router.post("/reports/{report_id}/parse-json", response_model=JsonUploadResponse)
async def parse_json_data(
    report_id: str,
    json_file: UploadFile = File(None, description="JSON数据文件"),
    json_data: str = Form(None, description="JSON数据字符串"),
    db: AsyncSession = Depends(get_db)
):
    """
    解析JSON参数并存储
    
    支持上传JSON文件或直接传递JSON字符串
    """
    # 解析JSON
    parsed_data = None
    
    if json_file and json_file.filename:
        try:
            content = await json_file.read()
            parsed_data = json.loads(content.decode('utf-8'))
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"JSON文件格式错误: {str(e)}")
    elif json_data:
        try:
            parsed_data = json.loads(json_data)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"JSON数据格式错误: {str(e)}")
    else:
        raise HTTPException(status_code=400, detail="请提供JSON文件或JSON数据")
    
    # 解析并保存
    service = ReportParserService(db)
    
    # 验证报告存在
    report = await service.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    try:
        summary = await service.parse_and_save_json(report_id, parsed_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"解析保存失败: {str(e)}")
    
    return JsonUploadResponse(
        success=True,
        message="JSON解析并保存成功",
        report_id=report_id,
        parsed_data=summary
    )


@router.post("/upload-complete", response_model=JsonUploadResponse)
async def upload_complete(
    json_file: UploadFile = File(None, description="JSON数据文件"),
    json_data: str = Form(None, description="JSON数据字符串"),
    item_boundary_image: UploadFile = File(None, description="项目边界图片"),
    system_architecture_image: UploadFile = File(None, description="系统架构图片"),
    software_architecture_image: UploadFile = File(None, description="软件架构图片"),
    dataflow_image: UploadFile = File(None, description="数据流图片"),
    attack_tree_images: List[UploadFile] = File(None, description="攻击树图片列表"),
    db: AsyncSession = Depends(get_db)
):
    """
    完整上传接口
    
    一次性上传JSON参数和所有图片，自动创建报告并解析保存
    """
    # 解析JSON
    parsed_data = None
    
    if json_file and json_file.filename:
        try:
            content = await json_file.read()
            parsed_data = json.loads(content.decode('utf-8'))
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"JSON文件格式错误: {str(e)}")
    elif json_data:
        try:
            parsed_data = json.loads(json_data)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"JSON数据格式错误: {str(e)}")
    else:
        raise HTTPException(status_code=400, detail="请提供JSON文件或JSON数据")
    
    service = ReportParserService(db)
    
    # 创建报告
    report_name = parsed_data.get('cover', {}).get('report_title', 'TARA报告')
    report = await service.create_report(report_name)
    report_id = report.id
    
    # 辅助函数：上传图片
    async def upload_single_image(file: UploadFile, image_type: str) -> Optional[str]:
        if not file or not file.filename:
            return None
        
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in settings.ALLOWED_IMAGE_EXTENSIONS:
            return None
        
        file_data = await file.read()
        if len(file_data) > settings.MAX_IMAGE_SIZE:
            return None
        
        try:
            image = await service.upload_image(
                report_id=report_id,
                file_data=file_data,
                filename=file.filename,
                image_type=image_type,
                content_type=file.content_type or "image/png"
            )
            return image.id
        except Exception as e:
            print(f"Failed to upload {file.filename}: {e}")
            return None
    
    # 上传图片并更新JSON中的图片ID
    if 'definitions' not in parsed_data:
        parsed_data['definitions'] = {}
    if 'assets' not in parsed_data:
        parsed_data['assets'] = {}
    
    # 上传项目边界图
    if item_boundary_image:
        image_id = await upload_single_image(item_boundary_image, 'item_boundary')
        if image_id:
            parsed_data['definitions']['item_boundary_image_id'] = image_id
    
    # 上传系统架构图
    if system_architecture_image:
        image_id = await upload_single_image(system_architecture_image, 'system_architecture')
        if image_id:
            parsed_data['definitions']['system_architecture_image_id'] = image_id
    
    # 上传软件架构图
    if software_architecture_image:
        image_id = await upload_single_image(software_architecture_image, 'software_architecture')
        if image_id:
            parsed_data['definitions']['software_architecture_image_id'] = image_id
    
    # 上传数据流图
    if dataflow_image:
        image_id = await upload_single_image(dataflow_image, 'dataflow')
        if image_id:
            parsed_data['assets']['dataflow_image_id'] = image_id
    
    # 上传攻击树图片
    if attack_tree_images:
        attack_trees_list = parsed_data.get('attack_trees', {}).get('attack_trees', [])
        
        for i, attack_img in enumerate(attack_tree_images):
            if attack_img and attack_img.filename:
                # 先保存攻击树数据以获取ID
                if 'attack_trees' not in parsed_data:
                    parsed_data['attack_trees'] = {'attack_trees': []}
                
                # 创建或更新攻击树条目
                if i >= len(attack_trees_list):
                    attack_trees_list.append({
                        'asset_id': f'AT{i+1:03d}',
                        'asset_name': f'攻击树 {i+1}',
                        'title': f'攻击树分析 {i+1}'
                    })
                
                parsed_data['attack_trees']['attack_trees'] = attack_trees_list
    
    # 解析并保存JSON数据
    try:
        summary = await service.parse_and_save_json(report_id, parsed_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"解析保存失败: {str(e)}")
    
    # 上传攻击树图片(需要在攻击树创建后)
    if attack_tree_images:
        attack_trees = await service.get_attack_trees(report_id)
        if attack_trees:
            for i, attack_img in enumerate(attack_tree_images):
                if attack_img and attack_img.filename and i < len(attack_trees.attack_trees):
                    tree = attack_trees.attack_trees[i]
                    
                    file_ext = Path(attack_img.filename).suffix.lower()
                    if file_ext in settings.ALLOWED_IMAGE_EXTENSIONS:
                        file_data = await attack_img.read()
                        if len(file_data) <= settings.MAX_IMAGE_SIZE:
                            try:
                                await service.upload_image(
                                    report_id=report_id,
                                    file_data=file_data,
                                    filename=attack_img.filename,
                                    image_type='attack_tree',
                                    content_type=attack_img.content_type or "image/png",
                                    attack_tree_id=tree.id
                                )
                            except Exception as e:
                                print(f"Failed to upload attack tree image: {e}")
    
    return JsonUploadResponse(
        success=True,
        message="上传解析完成",
        report_id=report_id,
        parsed_data=summary
    )
