"""
报告服务 - TARA报告生成和下载
负责根据报告ID生成Excel和PDF报告，并提供下载功能
"""
import os
import sys
import io
import tempfile
import httpx
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.orm import Session

# 添加共享模块路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.database import get_db, engine, Base
from shared.models import Report, ReportCover, GeneratedReport
from shared.minio_client import get_minio_client, BUCKET_REPORTS, BUCKET_IMAGES

from tara_excel_generator import generate_tara_excel_from_json
from tara_pdf_generator import generate_tara_pdf_from_json

# 数据服务地址
DATA_SERVICE_URL = os.getenv("DATA_SERVICE_URL", "http://data-service:8001")

# 创建FastAPI应用
app = FastAPI(
    title="TARA Report Service",
    description="TARA报告生成服务 - 负责生成Excel和PDF报告",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    """启动时初始化数据库"""
    print("Initializing database...")
    Base.metadata.create_all(bind=engine)
    print("Database initialized.")


# ==================== 辅助函数 ====================

async def fetch_data_from_service(report_id: str) -> Dict[str, Any]:
    """
    从数据服务获取报告数据
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 获取封面数据
        cover_resp = await client.get(f"{DATA_SERVICE_URL}/api/reports/{report_id}/cover")
        if cover_resp.status_code != 200:
            raise HTTPException(status_code=404, detail="无法获取封面数据")
        cover_data = cover_resp.json()
        
        # 获取定义数据
        definitions_resp = await client.get(f"{DATA_SERVICE_URL}/api/reports/{report_id}/definitions")
        if definitions_resp.status_code != 200:
            raise HTTPException(status_code=404, detail="无法获取定义数据")
        definitions_data = definitions_resp.json()
        
        # 获取资产数据
        assets_resp = await client.get(f"{DATA_SERVICE_URL}/api/reports/{report_id}/assets")
        if assets_resp.status_code != 200:
            raise HTTPException(status_code=404, detail="无法获取资产数据")
        assets_data = assets_resp.json()
        
        # 获取攻击树数据
        attack_trees_resp = await client.get(f"{DATA_SERVICE_URL}/api/reports/{report_id}/attack-trees")
        if attack_trees_resp.status_code != 200:
            raise HTTPException(status_code=404, detail="无法获取攻击树数据")
        attack_trees_data = attack_trees_resp.json()
        
        # 获取TARA结果数据
        tara_resp = await client.get(f"{DATA_SERVICE_URL}/api/reports/{report_id}/tara-results")
        if tara_resp.status_code != 200:
            raise HTTPException(status_code=404, detail="无法获取TARA结果数据")
        tara_data = tara_resp.json()
    
    return {
        "cover": cover_data,
        "definitions": definitions_data,
        "assets": assets_data,
        "attack_trees": attack_trees_data,
        "tara_results": tara_data
    }


async def download_image_from_minio(minio_path: str, report_id: str) -> Optional[str]:
    """
    从MinIO下载图片到临时文件
    """
    if not minio_path:
        return None
    
    try:
        minio = get_minio_client()
        
        # 解析路径
        if "/" in minio_path and not minio_path.startswith(report_id):
            bucket, object_name = minio_path.split("/", 1)
        else:
            bucket = BUCKET_IMAGES
            object_name = minio_path
        
        content = minio.download_file(bucket, object_name)
        
        # 创建临时文件
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
    准备报告数据，包括下载图片到本地临时文件
    """
    # 获取数据
    data = await fetch_data_from_service(report_id)
    
    # 下载图片并替换路径
    definitions = data.get('definitions', {})
    
    # 下载定义中的图片
    if definitions.get('item_boundary_image'):
        local_path = await download_image_from_minio(definitions['item_boundary_image'], report_id)
        definitions['item_boundary_image'] = local_path
    
    if definitions.get('system_architecture_image'):
        local_path = await download_image_from_minio(definitions['system_architecture_image'], report_id)
        definitions['system_architecture_image'] = local_path
    
    if definitions.get('software_architecture_image'):
        local_path = await download_image_from_minio(definitions['software_architecture_image'], report_id)
        definitions['software_architecture_image'] = local_path
    
    # 下载资产数据中的数据流图
    assets = data.get('assets', {})
    if assets.get('dataflow_image'):
        local_path = await download_image_from_minio(assets['dataflow_image'], report_id)
        assets['dataflow_image'] = local_path
    
    # 下载攻击树图片
    attack_trees = data.get('attack_trees', {})
    for tree in attack_trees.get('attack_trees', []):
        if tree.get('image'):
            local_path = await download_image_from_minio(tree['image'], report_id)
            tree['image'] = local_path
    
    return data


def cleanup_temp_files(data: Dict[str, Any]):
    """清理临时文件"""
    import os
    
    paths_to_clean = []
    
    # 收集所有临时文件路径
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
    
    # 删除临时文件
    for path in paths_to_clean:
        try:
            os.unlink(path)
        except:
            pass


# ==================== API端点 ====================

@app.get("/")
async def root():
    """API根路径"""
    return {
        "name": "TARA Report Service",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/api/health")
async def health_check(db: Session = Depends(get_db)):
    """健康检查"""
    from sqlalchemy import text
    try:
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    try:
        minio = get_minio_client()
        minio_status = "healthy"
    except Exception as e:
        minio_status = f"unhealthy: {str(e)}"
    
    # 检查数据服务连接
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{DATA_SERVICE_URL}/api/health")
            data_service_status = "healthy" if resp.status_code == 200 else "unhealthy"
    except Exception as e:
        data_service_status = f"unhealthy: {str(e)}"
    
    return {
        "status": "healthy" if all(s == "healthy" for s in [db_status, minio_status, data_service_status]) else "degraded",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "database": db_status,
            "minio": minio_status,
            "data_service": data_service_status
        }
    }


@app.post("/api/reports/{report_id}/generate")
async def generate_report(
    report_id: str,
    format: str = "xlsx",
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    一键生成报告
    
    Args:
        report_id: 报告ID
        format: 报告格式 (xlsx 或 pdf)
    """
    # 检查报告是否存在
    report = db.query(Report).filter(Report.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    # 准备数据
    try:
        data = await prepare_report_data(report_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取报告数据失败: {str(e)}")
    
    # 创建临时文件
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
        # 生成报告
        generator(temp_path, data)
        
        # 读取生成的文件
        with open(temp_path, 'rb') as f:
            file_content = f.read()
        
        # 上传到MinIO
        minio = get_minio_client()
        object_name = f"{report_id}/{report_id}{suffix}"
        content_type = "application/pdf" if format.lower() == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        
        minio.upload_bytes(BUCKET_REPORTS, object_name, file_content, content_type)
        
        # 记录到数据库
        existing = db.query(GeneratedReport).filter(
            GeneratedReport.report_id == report_id,
            GeneratedReport.file_type == format.lower()
        ).first()
        
        if existing:
            existing.minio_path = object_name
            existing.file_size = len(file_content)
            existing.generated_at = datetime.now()
        else:
            generated = GeneratedReport(
                report_id=report_id,
                file_type=format.lower(),
                minio_path=object_name,
                minio_bucket=BUCKET_REPORTS,
                file_size=len(file_content)
            )
            db.add(generated)
        
        db.commit()
        
        # 清理临时图片文件
        cleanup_temp_files(data)
        
        # 获取项目名称用于文件名
        cover = db.query(ReportCover).filter(ReportCover.report_id == report_id).first()
        project_name = cover.project_name if cover else "TARA报告"
        
        return {
            "success": True,
            "message": "报告生成成功",
            "report_id": report_id,
            "format": format.lower(),
            "file_size": len(file_content),
            "download_url": f"/api/reports/{report_id}/download?format={format.lower()}",
            "file_name": f"{project_name}_{report_id}{suffix}"
        }
        
    except Exception as e:
        cleanup_temp_files(data)
        raise HTTPException(status_code=500, detail=f"报告生成失败: {str(e)}")
    finally:
        # 删除临时报告文件
        try:
            os.unlink(temp_path)
        except:
            pass


@app.get("/api/reports/{report_id}/download")
async def download_report(
    report_id: str,
    format: str = "xlsx",
    db: Session = Depends(get_db)
):
    """
    下载报告
    
    Args:
        report_id: 报告ID
        format: 报告格式 (xlsx 或 pdf)
    """
    # 查找已生成的报告
    generated = db.query(GeneratedReport).filter(
        GeneratedReport.report_id == report_id,
        GeneratedReport.file_type == format.lower()
    ).first()
    
    if not generated:
        raise HTTPException(status_code=404, detail="报告文件不存在，请先生成报告")
    
    # 从MinIO下载
    try:
        minio = get_minio_client()
        content = minio.download_file(generated.minio_bucket, generated.minio_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载报告失败: {str(e)}")
    
    # 获取项目名称用于文件名
    cover = db.query(ReportCover).filter(ReportCover.report_id == report_id).first()
    project_name = cover.project_name if cover else "TARA报告"
    
    suffix = ".pdf" if format.lower() == "pdf" else ".xlsx"
    content_type = "application/pdf" if format.lower() == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    filename = f"{project_name}_{report_id}{suffix}"
    
    return StreamingResponse(
        io.BytesIO(content),
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@app.get("/api/reports/{report_id}/preview")
async def preview_report(report_id: str, db: Session = Depends(get_db)):
    """
    获取报告预览数据
    """
    # 从数据服务获取数据
    try:
        data = await fetch_data_from_service(report_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取报告数据失败: {str(e)}")
    
    # 获取已生成的报告信息
    generated_files = db.query(GeneratedReport).filter(
        GeneratedReport.report_id == report_id
    ).all()
    
    downloads = {}
    for gf in generated_files:
        downloads[gf.file_type] = {
            "url": f"/api/reports/{report_id}/download?format={gf.file_type}",
            "file_size": gf.file_size,
            "generated_at": gf.generated_at.isoformat() if gf.generated_at else None
        }
    
    # 获取报告基本信息
    report = db.query(Report).filter(Report.report_id == report_id).first()
    cover = db.query(ReportCover).filter(ReportCover.report_id == report_id).first()
    
    # 解析数据为前端期望的格式
    definitions_data = data.get('definitions', {})
    assets_data = data.get('assets', {})
    attack_trees_data = data.get('attack_trees', {})
    tara_results_data = data.get('tara_results', {})
    
    # 构建图片URL
    def build_image_url(minio_path):
        if not minio_path:
            return None
        return f"/api/reports/{report_id}/image-by-path?path={minio_path}"
    
    # 处理攻击树，添加image_url
    attack_trees = []
    for tree in attack_trees_data.get('attack_trees', []):
        tree_copy = dict(tree)
        if tree.get('image'):
            tree_copy['image_url'] = build_image_url(tree['image'])
        attack_trees.append(tree_copy)
    
    # 计算统计信息
    assets_list = assets_data.get('assets', [])
    tara_results_list = tara_results_data.get('results', [])
    
    statistics = {
        'assets_count': len(assets_list),
        'threats_count': len(tara_results_list),
        'high_risk_count': sum(1 for r in tara_results_list if r.get('operational_impact') in ['重大的', '严重的']),
        'measures_count': len(tara_results_list),
        'attack_trees_count': len(attack_trees)
    }
    
    # 构建预览数据（匹配旧API格式）
    preview_data = {
        'id': report_id,
        'report_id': report_id,
        'name': cover.report_title if cover else 'TARA报告',
        'project_name': cover.project_name if cover else '',
        'status': report.status if report else 'completed',
        'created_at': report.created_at.isoformat() if report else '',
        'file_path': '',
        'statistics': statistics,
        'report_info': {
            'id': report_id,
            'name': cover.report_title if cover else 'TARA报告',
            'project_name': cover.project_name if cover else '',
            'version': cover.version if cover else '1.0',
            'created_at': report.created_at.isoformat() if report else '',
            'file_path': '',
            'file_size': 0,
            'statistics': statistics
        },
        'cover': data.get('cover', {}),
        'definitions': {
            **definitions_data,
            'item_boundary_image': build_image_url(definitions_data.get('item_boundary_image')),
            'system_architecture_image': build_image_url(definitions_data.get('system_architecture_image')),
            'software_architecture_image': build_image_url(definitions_data.get('software_architecture_image'))
        },
        'assets': {
            'title': '资产列表',
            'assets': assets_list,
            'dataflow_image': build_image_url(assets_data.get('dataflow_image'))
        },
        'attack_trees': {
            'title': '攻击树分析',
            'attack_trees': attack_trees
        },
        'tara_results': {
            'title': 'TARA分析结果',
            'results': tara_results_list
        },
        'downloads': downloads
    }
    
    return preview_data


@app.get("/api/reports/{report_id}/status")
async def get_report_status(report_id: str, db: Session = Depends(get_db)):
    """
    获取报告状态
    """
    report = db.query(Report).filter(Report.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    # 获取已生成的文件
    generated_files = db.query(GeneratedReport).filter(
        GeneratedReport.report_id == report_id
    ).all()
    
    return {
        "report_id": report_id,
        "status": report.status,
        "created_at": report.created_at.isoformat(),
        "generated_files": [
            {
                "type": gf.file_type,
                "size": gf.file_size,
                "generated_at": gf.generated_at.isoformat() if gf.generated_at else None
            }
            for gf in generated_files
        ]
    }


# ==================== 启动函数 ====================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,
        reload=True
    )
