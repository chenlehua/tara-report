"""
报告管理API端点
"""
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

import aiofiles
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse

from app.common.config import settings
from app.common.schemas import GenerateReportResponse, ReportInfo, ReportListResponse
from app.generators import generate_tara_excel_from_json, generate_tara_pdf_from_json
from .images import get_image_path, get_images_db, images_db

router = APIRouter()

# 内存中的报告存储（生产环境应使用数据库）
reports_db: Dict[str, Dict[str, Any]] = {}


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


@router.post("/generate", response_model=GenerateReportResponse)
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
            pass
    elif attack_tree_images:
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
    output_path = settings.REPORTS_DIR / output_filename
    
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
        'data': report_data
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
            'item_boundary': f"/api/v1/images/{item_boundary_image}" if item_boundary_image else None,
            'system_architecture': f"/api/v1/images/{system_architecture_image}" if system_architecture_image else None,
            'software_architecture': f"/api/v1/images/{software_architecture_image}" if software_architecture_image else None,
            'dataflow': f"/api/v1/images/{dataflow_image}" if dataflow_image else None
        }
    }
    
    return GenerateReportResponse(
        success=True,
        message="报告生成成功",
        report_id=report_id,
        download_url=f"/api/v1/reports/{report_id}/download",
        preview_data=preview_data
    )


@router.get("", response_model=ReportListResponse)
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
            images={k: f"/api/v1/images/{v.split('/')[-1].split('.')[0]}" if v else None 
                   for k, v in report_info.get('images', {}).items()}
        ))
    
    # 按创建时间倒序排列
    reports.sort(key=lambda x: x.created_at, reverse=True)
    
    return ReportListResponse(
        success=True,
        reports=reports,
        total=len(reports)
    )


@router.get("/{report_id}")
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
        'download_url': f"/api/v1/reports/{report_id}/download"
    }
    
    return JSONResponse(content=preview_data)


@router.get("/{report_id}/download")
async def download_report(report_id: str):
    """下载报告"""
    if report_id not in reports_db:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    report_info = reports_db[report_id]
    file_path = Path(report_info['file_path'])
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="报告文件不存在")
    
    download_name = f"{report_info['project_name']}_TARA报告_{report_id}.xlsx"
    
    return FileResponse(
        path=file_path,
        filename=download_name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@router.get("/{report_id}/download/pdf")
async def download_report_pdf(report_id: str):
    """下载PDF格式报告"""
    if report_id not in reports_db:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    report_info = reports_db[report_id]
    report_data = report_info.get('data', {})
    
    pdf_filename = f"{report_id}.pdf"
    pdf_path = settings.REPORTS_DIR / pdf_filename
    
    if not pdf_path.exists():
        try:
            generate_tara_pdf_from_json(str(pdf_path), report_data)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"PDF生成失败: {str(e)}")
    
    download_name = f"{report_info['project_name']}_TARA报告_{report_id}.pdf"
    
    return FileResponse(
        path=pdf_path,
        filename=download_name,
        media_type="application/pdf"
    )


@router.post("/{report_id}/generate-pdf")
async def generate_report_pdf(report_id: str):
    """为指定报告生成PDF版本"""
    if report_id not in reports_db:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    report_info = reports_db[report_id]
    report_data = report_info.get('data', {})
    
    pdf_filename = f"{report_id}.pdf"
    pdf_path = settings.REPORTS_DIR / pdf_filename
    
    try:
        generate_tara_pdf_from_json(str(pdf_path), report_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF生成失败: {str(e)}")
    
    file_size = pdf_path.stat().st_size if pdf_path.exists() else 0
    
    return {
        "success": True,
        "message": "PDF报告生成成功",
        "pdf_path": str(pdf_path),
        "file_size": file_size,
        "download_url": f"/api/v1/reports/{report_id}/download/pdf"
    }


@router.delete("/{report_id}")
async def delete_report(report_id: str):
    """删除报告"""
    if report_id not in reports_db:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    report_info = reports_db[report_id]
    
    file_path = Path(report_info['file_path'])
    if file_path.exists():
        file_path.unlink()
    
    del reports_db[report_id]
    
    return {"success": True, "message": "报告已删除"}


@router.get("/{report_id}/preview")
async def get_report_preview(report_id: str):
    """获取报告预览数据"""
    if report_id not in reports_db:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    report_info = reports_db[report_id]
    report_data = report_info.get('data', {})
    image_paths = report_info.get('image_paths', {})
    
    def path_to_url(file_path: Optional[str]) -> Optional[str]:
        if not file_path:
            return None
        for img_id, img_info in images_db.items():
            if img_info['path'] == file_path:
                return f"/api/v1/images/{img_id}"
        return None
    
    images_urls = {
        'item_boundary': path_to_url(image_paths.get('item_boundary')),
        'system_architecture': path_to_url(image_paths.get('system_architecture')),
        'software_architecture': path_to_url(image_paths.get('software_architecture')),
        'dataflow': path_to_url(image_paths.get('dataflow'))
    }
    
    attack_trees = []
    for tree in report_data.get('attack_trees', {}).get('attack_trees', []):
        tree_copy = dict(tree)
        if tree.get('image'):
            tree_copy['image_url'] = path_to_url(tree['image'])
        attack_trees.append(tree_copy)
    
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
