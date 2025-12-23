"""
TARA报告生成API服务
提供TARA Excel报告的生成、预览和下载功能
"""
import os
import json
import uuid
import shutil
import aiofiles
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .models import (
    TARAReportData,
    GenerateReportResponse,
    ReportInfo,
    ReportListResponse,
    ImageUploadResponse
)
from .tara_excel_generator import generate_tara_excel_from_json
from .tara_pdf_generator import generate_tara_pdf_from_json

# 创建FastAPI应用
app = FastAPI(
    title="TARA Report Generator API",
    description="威胁分析和风险评估报告生成服务",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境需要限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 存储目录配置
BASE_DIR = Path(__file__).parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
REPORTS_DIR = BASE_DIR / "reports"
IMAGES_DIR = UPLOAD_DIR / "images"

# 确保目录存在
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# 内存中的报告存储（生产环境应使用数据库）
reports_db: Dict[str, Dict[str, Any]] = {}

# 图片存储映射
images_db: Dict[str, Dict[str, str]] = {}


# ==================== 辅助函数 ====================
def generate_report_id() -> str:
    """生成报告ID"""
    return f"RPT-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"


def generate_image_id() -> str:
    """生成图片ID"""
    return f"IMG-{uuid.uuid4().hex[:12]}"


def calculate_statistics(data: Dict[str, Any]) -> Dict[str, int]:
    """计算报告统计信息"""
    assets_count = len(data.get('assets', {}).get('assets', []))
    threats_count = len(data.get('tara_results', {}).get('results', []))
    
    # 计算高风险项（简化逻辑）
    high_risk_count = 0
    for result in data.get('tara_results', {}).get('results', []):
        if result.get('operational_impact') in ['重大的', '严重的']:
            high_risk_count += 1
    
    return {
        'assets_count': assets_count,
        'threats_count': threats_count,
        'high_risk_count': high_risk_count,
        'measures_count': threats_count  # 假设每个威胁有对应措施
    }


# ==================== API端点 ====================

@app.get("/")
async def root():
    """API根路径"""
    return {
        "name": "TARA Report Generator API",
        "version": "1.0.0",
        "status": "running"
    }


@app.post("/api/images/upload", response_model=ImageUploadResponse)
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
    file_path = IMAGES_DIR / filename
    
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
        image_url=f"/api/images/{image_id}",
        image_type=image_type
    )


@app.get("/api/images/{image_id}")
async def get_image(image_id: str):
    """获取图片"""
    if image_id not in images_db:
        raise HTTPException(status_code=404, detail="图片不存在")
    
    image_info = images_db[image_id]
    file_path = Path(image_info['path'])
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="图片文件不存在")
    
    return FileResponse(file_path)


@app.post("/api/reports/generate", response_model=GenerateReportResponse)
async def generate_report(
    json_file: UploadFile = File(None, description="JSON数据文件"),
    json_data: str = Form(None, description="JSON数据字符串"),
    item_boundary_image: str = Form(None, description="项目边界图片ID"),
    system_architecture_image: str = Form(None, description="系统架构图片ID"),
    software_architecture_image: str = Form(None, description="软件架构图片ID"),
    dataflow_image: str = Form(None, description="数据流图片ID"),
    attack_tree_images: str = Form(None, description="攻击树图片ID列表(逗号分隔)"),
    attack_trees_data: str = Form(None, description="攻击树数据JSON(用于替换)")
):
    """
    生成TARA报告
    
    可以通过上传JSON文件或直接传递JSON数据来生成报告。
    同时支持关联已上传的图片。
    如果提供了attack_trees_data，将自动替换JSON中的attack_trees字段。
    """
    # 解析JSON数据
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
    
    # 处理图片关联
    def get_image_path(image_id: Optional[str]) -> Optional[str]:
        if image_id and image_id in images_db:
            return images_db[image_id]['path']
        return None
    
    # 更新数据中的图片路径
    if 'definitions' not in report_data:
        report_data['definitions'] = {}
    
    if item_boundary_image:
        report_data['definitions']['item_boundary_image'] = get_image_path(item_boundary_image)
    if system_architecture_image:
        report_data['definitions']['system_architecture_image'] = get_image_path(system_architecture_image)
    if software_architecture_image:
        report_data['definitions']['software_architecture_image'] = get_image_path(software_architecture_image)
    
    if 'assets' not in report_data:
        report_data['assets'] = {}
    if dataflow_image:
        report_data['assets']['dataflow_image'] = get_image_path(dataflow_image)
    
    # 处理攻击树数据替换
    if attack_trees_data:
        try:
            attack_trees_list = json.loads(attack_trees_data)
            if attack_trees_list and len(attack_trees_list) > 0:
                # 使用前端提供的攻击树数据替换JSON中的attack_trees
                new_attack_trees = []
                for tree_data in attack_trees_list:
                    image_id = tree_data.get('image_id')
                    image_path = get_image_path(image_id) if image_id else None
                    new_attack_trees.append({
                        'asset_id': tree_data.get('asset_id', ''),
                        'asset_name': tree_data.get('asset_name', ''),
                        'title': tree_data.get('title', ''),
                        'image': image_path
                    })
                report_data['attack_trees'] = {'attack_trees': new_attack_trees}
        except json.JSONDecodeError:
            pass  # 忽略解析错误，使用原始数据
    elif attack_tree_images:
        # 兼容旧的攻击树图片ID列表方式
        image_ids = [img_id.strip() for img_id in attack_tree_images.split(',') if img_id.strip()]
        if 'attack_trees' not in report_data:
            report_data['attack_trees'] = {'attack_trees': []}
        attack_trees = report_data.get('attack_trees', {}).get('attack_trees', [])
        for i, img_id in enumerate(image_ids):
            if i < len(attack_trees):
                attack_trees[i]['image'] = get_image_path(img_id)
    
    # 生成报告ID和文件路径
    report_id = generate_report_id()
    output_filename = f"{report_id}.xlsx"
    output_path = REPORTS_DIR / output_filename
    
    # 生成Excel报告
    try:
        generate_tara_excel_from_json(str(output_path), report_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"报告生成失败: {str(e)}")
    
    # 计算统计信息
    statistics = calculate_statistics(report_data)
    
    # 获取图片信息用于预览
    images_info = {
        'item_boundary': get_image_path(item_boundary_image),
        'system_architecture': get_image_path(system_architecture_image),
        'software_architecture': get_image_path(software_architecture_image),
        'dataflow': get_image_path(dataflow_image)
    }
    
    # 存储报告信息
    report_info = {
        'id': report_id,
        'name': report_data.get('cover', {}).get('report_title', 'TARA报告'),
        'project_name': report_data.get('cover', {}).get('project_name', '未命名项目'),
        'created_at': datetime.now().isoformat(),
        'status': 'completed',
        'file_path': str(output_path),
        'statistics': statistics,
        'images': images_info,
        'data': report_data  # 保存原始数据用于预览
    }
    reports_db[report_id] = report_info
    
    # 构建预览数据
    preview_data = {
        'cover': report_data.get('cover', {}),
        'definitions': {
            'title': report_data.get('definitions', {}).get('title', ''),
            'functional_description': report_data.get('definitions', {}).get('functional_description', ''),
            'assumptions': report_data.get('definitions', {}).get('assumptions', []),
            'terminology': report_data.get('definitions', {}).get('terminology', [])
        },
        'assets': report_data.get('assets', {}).get('assets', []),
        'attack_trees': report_data.get('attack_trees', {}).get('attack_trees', []),
        'tara_results': report_data.get('tara_results', {}).get('results', []),
        'statistics': statistics,
        'images': {
            'item_boundary': f"/api/images/{item_boundary_image}" if item_boundary_image else None,
            'system_architecture': f"/api/images/{system_architecture_image}" if system_architecture_image else None,
            'software_architecture': f"/api/images/{software_architecture_image}" if software_architecture_image else None,
            'dataflow': f"/api/images/{dataflow_image}" if dataflow_image else None
        }
    }
    
    return GenerateReportResponse(
        success=True,
        message="报告生成成功",
        report_id=report_id,
        download_url=f"/api/reports/{report_id}/download",
        preview_data=preview_data
    )


@app.get("/api/reports", response_model=ReportListResponse)
async def list_reports():
    """获取报告列表"""
    reports = []
    for report_id, report_info in reports_db.items():
        reports.append(ReportInfo(
            id=report_info['id'],
            name=report_info['name'],
            project_name=report_info['project_name'],
            created_at=datetime.fromisoformat(report_info['created_at']),
            status=report_info['status'],
            file_path=report_info['file_path'],
            statistics=report_info['statistics'],
            images={k: f"/api/images/{v.split('/')[-1].split('.')[0]}" if v else None 
                   for k, v in report_info.get('images', {}).items()}
        ))
    
    # 按创建时间倒序排列
    reports.sort(key=lambda x: x.created_at, reverse=True)
    
    return ReportListResponse(
        success=True,
        reports=reports,
        total=len(reports)
    )


@app.get("/api/reports/{report_id}")
async def get_report(report_id: str):
    """获取报告详情"""
    if report_id not in reports_db:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    report_info = reports_db[report_id]
    report_data = report_info.get('data', {})
    
    # 构建预览数据
    preview_data = {
        'id': report_id,
        'name': report_info['name'],
        'project_name': report_info['project_name'],
        'created_at': report_info['created_at'],
        'status': report_info['status'],
        'statistics': report_info['statistics'],
        'cover': report_data.get('cover', {}),
        'definitions': report_data.get('definitions', {}),
        'assets': report_data.get('assets', {}),
        'attack_trees': report_data.get('attack_trees', {}),
        'tara_results': report_data.get('tara_results', {}),
        'download_url': f"/api/reports/{report_id}/download"
    }
    
    return JSONResponse(content=preview_data)


@app.get("/api/reports/{report_id}/download")
async def download_report(report_id: str):
    """下载报告"""
    if report_id not in reports_db:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    report_info = reports_db[report_id]
    file_path = Path(report_info['file_path'])
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="报告文件不存在")
    
    # 使用项目名称作为下载文件名
    download_name = f"{report_info['project_name']}_TARA报告_{report_id}.xlsx"
    
    return FileResponse(
        path=file_path,
        filename=download_name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@app.get("/api/reports/{report_id}/download/pdf")
async def download_report_pdf(report_id: str):
    """下载PDF格式报告"""
    if report_id not in reports_db:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    report_info = reports_db[report_id]
    report_data = report_info.get('data', {})
    
    # PDF文件路径
    pdf_filename = f"{report_id}.pdf"
    pdf_path = REPORTS_DIR / pdf_filename
    
    # 如果PDF不存在，生成它
    if not pdf_path.exists():
        try:
            generate_tara_pdf_from_json(str(pdf_path), report_data)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"PDF生成失败: {str(e)}")
    
    # 使用项目名称作为下载文件名
    download_name = f"{report_info['project_name']}_TARA报告_{report_id}.pdf"
    
    return FileResponse(
        path=pdf_path,
        filename=download_name,
        media_type="application/pdf"
    )


@app.post("/api/reports/{report_id}/generate-pdf")
async def generate_report_pdf(report_id: str):
    """
    为指定报告生成PDF版本
    """
    if report_id not in reports_db:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    report_info = reports_db[report_id]
    report_data = report_info.get('data', {})
    
    # PDF文件路径
    pdf_filename = f"{report_id}.pdf"
    pdf_path = REPORTS_DIR / pdf_filename
    
    try:
        generate_tara_pdf_from_json(str(pdf_path), report_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF生成失败: {str(e)}")
    
    # 获取文件大小
    file_size = pdf_path.stat().st_size if pdf_path.exists() else 0
    
    return {
        "success": True,
        "message": "PDF报告生成成功",
        "pdf_path": str(pdf_path),
        "file_size": file_size,
        "download_url": f"/api/reports/{report_id}/download/pdf"
    }


@app.delete("/api/reports/{report_id}")
async def delete_report(report_id: str):
    """删除报告"""
    if report_id not in reports_db:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    report_info = reports_db[report_id]
    
    # 删除文件
    file_path = Path(report_info['file_path'])
    if file_path.exists():
        file_path.unlink()
    
    # 从数据库删除
    del reports_db[report_id]
    
    return {"success": True, "message": "报告已删除"}


@app.post("/api/upload/batch")
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
        file_path = IMAGES_DIR / filename
        
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
                        # 创建新的攻击树条目
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
    output_path = REPORTS_DIR / output_filename
    
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
        'data': report_data  # 保存原始数据用于预览
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
        'download_url': f"/api/reports/{report_id}/download",
        'preview_url': f"/api/reports/{report_id}/preview"
    }


@app.get("/api/reports/{report_id}/preview")
async def get_report_preview(report_id: str):
    """获取报告预览数据"""
    if report_id not in reports_db:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    report_info = reports_db[report_id]
    report_data = report_info.get('data', {})
    image_paths = report_info.get('image_paths', {})
    
    # 辅助函数：将文件路径转换为API URL
    def path_to_url(file_path: Optional[str]) -> Optional[str]:
        if not file_path:
            return None
        # 从images_db中查找对应的image_id
        for img_id, img_info in images_db.items():
            if img_info['path'] == file_path:
                return f"/api/images/{img_id}"
        return None
    
    # 构建图片URL映射
    images_urls = {
        'item_boundary': path_to_url(image_paths.get('item_boundary')),
        'system_architecture': path_to_url(image_paths.get('system_architecture')),
        'software_architecture': path_to_url(image_paths.get('software_architecture')),
        'dataflow': path_to_url(image_paths.get('dataflow'))
    }
    
    # 处理攻击树数据，添加图片URL
    attack_trees = []
    for tree in report_data.get('attack_trees', {}).get('attack_trees', []):
        tree_copy = dict(tree)
        if tree.get('image'):
            tree_copy['image_url'] = path_to_url(tree['image'])
        attack_trees.append(tree_copy)
    
    # 构建预览数据
    preview_data = {
        'report_info': {
            'id': report_id,
            'name': report_info['name'],
            'version': report_info.get('version', '1.0'),
            'created_at': report_info['created_at'],
            'file_path': report_info['file_path'],
            'file_size': report_info.get('file_size', 0),
            'statistics': report_info['statistics']
        },
        'cover': report_data.get('cover', {}),
        'definitions': {
            **report_data.get('definitions', {}),
            'item_boundary_image': images_urls['item_boundary'],
            'system_architecture_image': images_urls['system_architecture'],
            'software_architecture_image': images_urls['software_architecture']
        },
        'assets': report_data.get('assets', {}).get('assets', []),
        'dataflow_image': images_urls['dataflow'],
        'attack_trees': attack_trees,
        'tara_results': report_data.get('tara_results', {}).get('results', []),
        'statistics': report_info['statistics']
    }
    
    return JSONResponse(content=preview_data)


@app.post("/api/reports/generate-by-id/{report_id}")
async def generate_report_by_id(
    report_id: str,
    format: str = "xlsx"
):
    """
    根据报告ID生成报告
    
    该接口从上传解析模块获取数据，然后生成报告文件。
    
    Args:
        report_id: 报告ID(来自上传解析模块)
        format: 报告格式 (xlsx 或 pdf)
    """
    from .upload_parser_client import get_upload_parser_client
    
    client = get_upload_parser_client()
    
    # 从上传解析模块获取完整报告数据
    full_data = await client.get_full_report_data(report_id)
    
    if not full_data:
        raise HTTPException(status_code=404, detail="报告数据不存在或获取失败")
    
    # 转换为报告生成格式
    report_data = client.convert_to_report_format(full_data)
    
    # 生成报告文件
    output_filename = f"{report_id}.{format}"
    output_path = REPORTS_DIR / output_filename
    
    try:
        if format == "pdf":
            generate_tara_pdf_from_json(str(output_path), report_data)
        else:
            generate_tara_excel_from_json(str(output_path), report_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"报告生成失败: {str(e)}")
    
    # 计算统计信息
    statistics = calculate_statistics(report_data)
    
    # 获取文件大小
    file_size = output_path.stat().st_size if output_path.exists() else 0
    
    # 存储到本地报告数据库
    report_info = {
        'id': report_id,
        'name': report_data.get('cover', {}).get('report_title', 'TARA报告'),
        'project_name': report_data.get('cover', {}).get('project_name', '未命名项目'),
        'created_at': datetime.now().isoformat(),
        'status': 'completed',
        'file_path': str(output_path),
        'file_size': file_size,
        'statistics': statistics,
        'data': report_data
    }
    reports_db[report_id] = report_info
    
    return {
        'success': True,
        'message': '报告生成成功',
        'report_info': {
            'id': report_id,
            'name': report_info['name'],
            'project_name': report_info['project_name'],
            'created_at': report_info['created_at'],
            'file_path': report_info['file_path'],
            'file_size': file_size,
            'statistics': statistics
        },
        'download_url': f"/api/reports/{report_id}/download" + ("/pdf" if format == "pdf" else ""),
        'preview_url': f"/api/reports/{report_id}/preview"
    }


@app.get("/api/upload-parser/reports/{report_id}/cover")
async def proxy_get_cover(report_id: str):
    """代理获取封面(通过上传解析模块)"""
    from .upload_parser_client import get_upload_parser_client
    
    client = get_upload_parser_client()
    cover = await client.get_cover(report_id)
    
    if not cover:
        raise HTTPException(status_code=404, detail="封面不存在")
    
    return cover


@app.get("/api/upload-parser/reports/{report_id}/definitions")
async def proxy_get_definitions(report_id: str):
    """代理获取项目定义(通过上传解析模块)"""
    from .upload_parser_client import get_upload_parser_client
    
    client = get_upload_parser_client()
    definitions = await client.get_definitions(report_id)
    
    if not definitions:
        raise HTTPException(status_code=404, detail="项目定义不存在")
    
    return definitions


@app.get("/api/upload-parser/reports/{report_id}/assets")
async def proxy_get_assets(report_id: str):
    """代理获取资产信息(通过上传解析模块)"""
    from .upload_parser_client import get_upload_parser_client
    
    client = get_upload_parser_client()
    assets = await client.get_assets(report_id)
    
    if not assets:
        raise HTTPException(status_code=404, detail="资产信息不存在")
    
    return assets


@app.get("/api/upload-parser/reports/{report_id}/attack-trees")
async def proxy_get_attack_trees(report_id: str):
    """代理获取攻击树(通过上传解析模块)"""
    from .upload_parser_client import get_upload_parser_client
    
    client = get_upload_parser_client()
    attack_trees = await client.get_attack_trees(report_id)
    
    if not attack_trees:
        raise HTTPException(status_code=404, detail="攻击树不存在")
    
    return attack_trees


@app.get("/api/upload-parser/reports/{report_id}/tara-results")
async def proxy_get_tara_results(report_id: str):
    """代理获取TARA分析结果(通过上传解析模块)"""
    from .upload_parser_client import get_upload_parser_client
    
    client = get_upload_parser_client()
    tara_results = await client.get_tara_results(report_id)
    
    if not tara_results:
        raise HTTPException(status_code=404, detail="TARA分析结果不存在")
    
    return tara_results


@app.get("/api/upload-parser/reports/{report_id}/full-data")
async def proxy_get_full_data(report_id: str):
    """代理获取完整报告数据(通过上传解析模块)"""
    from .upload_parser_client import get_upload_parser_client
    
    client = get_upload_parser_client()
    full_data = await client.get_full_report_data(report_id)
    
    if not full_data:
        raise HTTPException(status_code=404, detail="报告数据不存在")
    
    return full_data


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "reports_count": len(reports_db),
        "images_count": len(images_db)
    }


# ==================== 启动函数 ====================
def run_server():
    """启动服务器"""
    import uvicorn
    uvicorn.run(
        "tara_api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )


if __name__ == "__main__":
    run_server()
