"""
数据服务 - TARA报告数据管理
负责上传JSON和图片、生成报告ID、保存数据到MySQL和MinIO
"""
import os
import sys
import json
import uuid
import httpx
from datetime import datetime
from typing import Optional, List
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session
import io

# 报告服务地址
REPORT_SERVICE_URL = os.getenv("REPORT_SERVICE_URL", "http://report-service:8002")

# 添加共享模块路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.database import get_db, init_db, engine, Base
from shared.models import (
    Report, ReportCover, ReportDefinitions, ReportAsset,
    ReportAttackTree, ReportTARAResult, ReportImage
)
from shared.minio_client import get_minio_client, BUCKET_IMAGES

# 创建FastAPI应用
app = FastAPI(
    title="TARA Data Service",
    description="TARA报告数据管理服务 - 负责数据上传、解析和存储",
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
def generate_report_id() -> str:
    """生成报告ID"""
    return f"RPT-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"


def generate_image_id() -> str:
    """生成图片ID"""
    return f"IMG-{uuid.uuid4().hex[:12]}"


# 临时图片存储（用于在创建报告前上传图片）
temp_images_db: dict = {}


# ==================== API端点 ====================

@app.get("/")
async def root():
    """API根路径"""
    return {
        "name": "TARA Data Service",
        "version": "1.0.0",
        "status": "running"
    }


@app.post("/api/images/upload")
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
        "image_url": f"/api/images/{image_id}",
        "image_type": image_type
    }


@app.get("/api/images/{image_id}")
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


@app.get("/api/health")
async def health_check(db: Session = Depends(get_db)):
    """健康检查"""
    from sqlalchemy import text
    try:
        # 检查数据库连接
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    try:
        # 检查MinIO连接
        minio = get_minio_client()
        minio_status = "healthy"
    except Exception as e:
        minio_status = f"unhealthy: {str(e)}"
    
    return {
        "status": "healthy" if db_status == "healthy" and minio_status == "healthy" else "degraded",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "database": db_status,
            "minio": minio_status
        }
    }


@app.post("/api/reports/upload")
async def upload_report_data(
    json_file: UploadFile = File(None, description="JSON数据文件"),
    json_data: str = Form(None, description="JSON数据字符串"),
    item_boundary_image: UploadFile = File(None),
    system_architecture_image: UploadFile = File(None),
    software_architecture_image: UploadFile = File(None),
    dataflow_image: UploadFile = File(None),
    attack_tree_images: List[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    上传JSON参数和图片，生成报告ID
    
    1. 生成报告ID
    2. 保存图片到MinIO
    3. 解析JSON并保存到数据库
    4. 返回报告ID
    """
    # 1. 解析JSON数据
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
    
    # 2. 生成报告ID
    report_id = generate_report_id()
    minio = get_minio_client()
    
    # 3. 创建报告记录
    report = Report(report_id=report_id, status="pending")
    db.add(report)
    db.flush()
    
    # 4. 上传图片到MinIO并记录
    async def save_image(upload_file: UploadFile, image_type: str) -> Optional[str]:
        if not upload_file or not upload_file.filename:
            return None
        
        image_id = generate_image_id()
        file_ext = Path(upload_file.filename).suffix.lower()
        object_name = f"{report_id}/{image_type}/{image_id}{file_ext}"
        
        content = await upload_file.read()
        minio_path = minio.upload_bytes(
            BUCKET_IMAGES,
            object_name,
            content,
            upload_file.content_type or "image/png"
        )
        
        # 记录图片信息
        image_record = ReportImage(
            report_id=report_id,
            image_id=image_id,
            image_type=image_type,
            original_name=upload_file.filename,
            minio_path=object_name,
            minio_bucket=BUCKET_IMAGES,
            file_size=len(content),
            content_type=upload_file.content_type
        )
        db.add(image_record)
        
        return object_name
    
    # 保存各类图片
    item_boundary_path = await save_image(item_boundary_image, "item_boundary")
    system_arch_path = await save_image(system_architecture_image, "system_architecture")
    software_arch_path = await save_image(software_architecture_image, "software_architecture")
    dataflow_path = await save_image(dataflow_image, "dataflow")
    
    # 保存攻击树图片
    attack_tree_paths = []
    if attack_tree_images:
        for i, img in enumerate(attack_tree_images):
            if img and img.filename:
                path = await save_image(img, f"attack_tree_{i}")
                if path:
                    attack_tree_paths.append(path)
    
    # 5. 解析并保存封面数据
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
    
    # 6. 解析并保存相关定义
    definitions_data = report_data.get('definitions', {})
    definitions = ReportDefinitions(
        report_id=report_id,
        title=definitions_data.get('title', ''),
        functional_description=definitions_data.get('functional_description', ''),
        item_boundary_image=item_boundary_path,
        system_architecture_image=system_arch_path,
        software_architecture_image=software_arch_path,
        assumptions=definitions_data.get('assumptions', []),
        terminology=definitions_data.get('terminology', [])
    )
    db.add(definitions)
    
    # 7. 解析并保存资产列表
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
    
    # 更新定义中的数据流图路径
    if dataflow_path:
        definitions.dataflow_image = dataflow_path
        db.add(definitions)
    
    # 8. 解析并保存攻击树
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
    
    # 9. 解析并保存TARA分析结果
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
    
    return {
        "success": True,
        "message": "数据上传成功",
        "report_id": report_id,
        "statistics": {
            "assets_count": len(assets_data.get('assets', [])),
            "attack_trees_count": len(trees),
            "tara_results_count": len(tara_data.get('results', [])),
            "images_count": len([p for p in [item_boundary_path, system_arch_path, software_arch_path, dataflow_path] + attack_tree_paths if p])
        }
    }


@app.get("/api/reports/{report_id}")
async def get_report_info(report_id: str, db: Session = Depends(get_db)):
    """获取报告完整信息（用于预览）"""
    report = db.query(Report).filter(Report.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    # 获取封面信息
    cover = db.query(ReportCover).filter(ReportCover.report_id == report_id).first()
    
    # 获取定义信息
    definitions = db.query(ReportDefinitions).filter(ReportDefinitions.report_id == report_id).first()
    
    # 获取资产列表
    assets = db.query(ReportAsset).filter(ReportAsset.report_id == report_id).all()
    
    # 获取攻击树
    attack_trees = db.query(ReportAttackTree).filter(
        ReportAttackTree.report_id == report_id
    ).order_by(ReportAttackTree.sort_order).all()
    
    # 获取TARA结果
    tara_results = db.query(ReportTARAResult).filter(
        ReportTARAResult.report_id == report_id
    ).order_by(ReportTARAResult.sort_order).all()
    
    # 构建图片URL
    def build_image_url(minio_path):
        if not minio_path:
            return None
        return f"/api/reports/{report_id}/image-by-path?path={minio_path}"
    
    # 构建资产列表
    assets_list = [
        {
            "id": asset.asset_id,
            "name": asset.name,
            "category": asset.category,
            "remarks": asset.remarks,
            "authenticity": asset.authenticity,
            "integrity": asset.integrity,
            "non_repudiation": asset.non_repudiation,
            "confidentiality": asset.confidentiality,
            "availability": asset.availability,
            "authorization": asset.authorization
        }
        for asset in assets
    ]
    
    # 构建攻击树列表
    attack_trees_list = [
        {
            "asset_id": tree.asset_id,
            "asset_name": tree.asset_name,
            "title": tree.title,
            "image": tree.image,
            "image_url": build_image_url(tree.image)
        }
        for tree in attack_trees
    ]
    
    # 构建TARA结果列表
    tara_results_list = [
        {
            "asset_id": r.asset_id,
            "asset_name": r.asset_name,
            "subdomain1": r.subdomain1,
            "subdomain2": r.subdomain2,
            "subdomain3": r.subdomain3,
            "category": r.category,
            "security_attribute": r.security_attribute,
            "stride_model": r.stride_model,
            "threat_scenario": r.threat_scenario,
            "attack_path": r.attack_path,
            "wp29_mapping": r.wp29_mapping,
            "attack_vector": r.attack_vector,
            "attack_complexity": r.attack_complexity,
            "privileges_required": r.privileges_required,
            "user_interaction": r.user_interaction,
            "safety_impact": r.safety_impact,
            "financial_impact": r.financial_impact,
            "operational_impact": r.operational_impact,
            "privacy_impact": r.privacy_impact,
            "security_goal": r.security_goal,
            "security_requirement": r.security_requirement
        }
        for r in tara_results
    ]
    
    # 统计信息
    statistics = {
        'assets_count': len(assets_list),
        'threats_count': len(tara_results_list),
        'high_risk_count': sum(1 for r in tara_results_list if r.get('operational_impact') in ['重大的', '严重的']),
        'measures_count': len(tara_results_list),
        'attack_trees_count': len(attack_trees_list)
    }
    
    return {
        "report_id": report.report_id,
        "status": report.status,
        "created_at": report.created_at.isoformat(),
        "updated_at": report.updated_at.isoformat() if report.updated_at else None,
        "report_info": {
            "id": report.report_id,
            "name": cover.report_title if cover else "TARA报告",
            "project_name": cover.project_name if cover else "",
            "version": cover.version if cover else "1.0",
            "created_at": report.created_at.isoformat(),
            "statistics": statistics
        },
        "cover": {
            "report_title": cover.report_title if cover else "",
            "report_title_en": cover.report_title_en if cover else "",
            "project_name": cover.project_name if cover else "",
            "data_level": cover.data_level if cover else "",
            "document_number": cover.document_number if cover else "",
            "version": cover.version if cover else "",
            "author_date": cover.author_date if cover else "",
            "review_date": cover.review_date if cover else "",
            "sign_date": cover.sign_date if cover else "",
            "approve_date": cover.approve_date if cover else ""
        } if cover else {},
        "definitions": {
            "title": definitions.title if definitions else "",
            "functional_description": definitions.functional_description if definitions else "",
            "item_boundary_image": build_image_url(definitions.item_boundary_image) if definitions else None,
            "system_architecture_image": build_image_url(definitions.system_architecture_image) if definitions else None,
            "software_architecture_image": build_image_url(definitions.software_architecture_image) if definitions else None,
            "assumptions": definitions.assumptions if definitions else [],
            "terminology": definitions.terminology if definitions else []
        } if definitions else {},
        "assets": assets_list,
        "dataflow_image": build_image_url(definitions.dataflow_image) if definitions and definitions.dataflow_image else None,
        "attack_trees": attack_trees_list,
        "tara_results": tara_results_list,
        "statistics": statistics
    }


@app.get("/api/reports/{report_id}/cover")
async def get_report_cover(report_id: str, db: Session = Depends(get_db)):
    """获取报告封面信息"""
    cover = db.query(ReportCover).filter(ReportCover.report_id == report_id).first()
    if not cover:
        raise HTTPException(status_code=404, detail="封面信息不存在")
    
    return {
        "report_title": cover.report_title,
        "report_title_en": cover.report_title_en,
        "project_name": cover.project_name,
        "data_level": cover.data_level,
        "document_number": cover.document_number,
        "version": cover.version,
        "author_date": cover.author_date,
        "review_date": cover.review_date,
        "sign_date": cover.sign_date,
        "approve_date": cover.approve_date
    }


@app.get("/api/reports/{report_id}/definitions")
async def get_report_definitions(report_id: str, db: Session = Depends(get_db)):
    """获取报告相关定义"""
    definitions = db.query(ReportDefinitions).filter(ReportDefinitions.report_id == report_id).first()
    if not definitions:
        raise HTTPException(status_code=404, detail="相关定义不存在")
    
    return {
        "title": definitions.title,
        "functional_description": definitions.functional_description,
        "item_boundary_image": definitions.item_boundary_image,
        "system_architecture_image": definitions.system_architecture_image,
        "software_architecture_image": definitions.software_architecture_image,
        "dataflow_image": definitions.dataflow_image,
        "assumptions": definitions.assumptions or [],
        "terminology": definitions.terminology or []
    }


@app.get("/api/reports/{report_id}/assets")
async def get_report_assets(report_id: str, db: Session = Depends(get_db)):
    """获取报告资产列表"""
    # 获取definitions中的dataflow_image
    definitions = db.query(ReportDefinitions).filter(ReportDefinitions.report_id == report_id).first()
    dataflow_image = getattr(definitions, 'dataflow_image', None) if definitions else None
    
    assets = db.query(ReportAsset).filter(ReportAsset.report_id == report_id).all()
    
    # 获取报告封面信息用于title
    cover = db.query(ReportCover).filter(ReportCover.report_id == report_id).first()
    title_prefix = cover.project_name if cover and cover.project_name else "报告"
    
    return {
        "title": f"{title_prefix} - 资产列表 Asset List",
        "dataflow_image": dataflow_image,
        "assets": [
            {
                "id": asset.asset_id,
                "name": asset.name,
                "category": asset.category,
                "remarks": asset.remarks,
                "authenticity": asset.authenticity,
                "integrity": asset.integrity,
                "non_repudiation": asset.non_repudiation,
                "confidentiality": asset.confidentiality,
                "availability": asset.availability,
                "authorization": asset.authorization
            }
            for asset in assets
        ]
    }


@app.get("/api/reports/{report_id}/attack-trees")
async def get_report_attack_trees(report_id: str, db: Session = Depends(get_db)):
    """获取报告攻击树"""
    trees = db.query(ReportAttackTree).filter(
        ReportAttackTree.report_id == report_id
    ).order_by(ReportAttackTree.sort_order).all()
    
    return {
        "title": "攻击树分析 Attack Tree Analysis",
        "attack_trees": [
            {
                "asset_id": tree.asset_id,
                "asset_name": tree.asset_name,
                "title": tree.title,
                "image": tree.image
            }
            for tree in trees
        ]
    }


@app.get("/api/reports/{report_id}/tara-results")
async def get_report_tara_results(report_id: str, db: Session = Depends(get_db)):
    """获取TARA分析结果"""
    results = db.query(ReportTARAResult).filter(
        ReportTARAResult.report_id == report_id
    ).order_by(ReportTARAResult.sort_order).all()
    
    return {
        "title": "TARA分析结果 TARA Analysis Results",
        "results": [
            {
                "asset_id": r.asset_id,
                "asset_name": r.asset_name,
                "subdomain1": r.subdomain1,
                "subdomain2": r.subdomain2,
                "subdomain3": r.subdomain3,
                "category": r.category,
                "security_attribute": r.security_attribute,
                "stride_model": r.stride_model,
                "threat_scenario": r.threat_scenario,
                "attack_path": r.attack_path,
                "wp29_mapping": r.wp29_mapping,
                "attack_vector": r.attack_vector,
                "attack_complexity": r.attack_complexity,
                "privileges_required": r.privileges_required,
                "user_interaction": r.user_interaction,
                "safety_impact": r.safety_impact,
                "financial_impact": r.financial_impact,
                "operational_impact": r.operational_impact,
                "privacy_impact": r.privacy_impact,
                "security_goal": r.security_goal,
                "security_requirement": r.security_requirement
            }
            for r in results
        ]
    }


@app.get("/api/reports/{report_id}/images/{image_id}")
async def get_image(report_id: str, image_id: str, db: Session = Depends(get_db)):
    """获取图片"""
    image = db.query(ReportImage).filter(
        ReportImage.report_id == report_id,
        ReportImage.image_id == image_id
    ).first()
    
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


@app.get("/api/reports/{report_id}/image-by-path")
async def get_image_by_path(report_id: str, path: str, db: Session = Depends(get_db)):
    """根据MinIO路径获取图片"""
    try:
        minio = get_minio_client()
        # 路径格式: bucket/object_name 或直接是 object_name
        if "/" in path and not path.startswith(report_id):
            bucket, object_name = path.split("/", 1)
        else:
            bucket = BUCKET_IMAGES
            object_name = path
        
        content = minio.download_file(bucket, object_name)
        
        # 根据文件扩展名确定content_type
        ext = Path(object_name).suffix.lower()
        content_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.svg': 'image/svg+xml',
            '.bmp': 'image/bmp'
        }
        content_type = content_types.get(ext, 'image/png')
        
        return StreamingResponse(
            io.BytesIO(content),
            media_type=content_type
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取图片失败: {str(e)}")


@app.get("/api/reports")
async def list_reports(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    """获取报告列表"""
    offset = (page - 1) * page_size
    
    total = db.query(Report).count()
    reports = db.query(Report).order_by(Report.created_at.desc()).offset(offset).limit(page_size).all()
    
    result = []
    for report in reports:
        cover = db.query(ReportCover).filter(ReportCover.report_id == report.report_id).first()
        
        # 统计信息
        assets_count = db.query(ReportAsset).filter(ReportAsset.report_id == report.report_id).count()
        tara_count = db.query(ReportTARAResult).filter(ReportTARAResult.report_id == report.report_id).count()
        attack_trees_count = db.query(ReportAttackTree).filter(ReportAttackTree.report_id == report.report_id).count()
        
        result.append({
            "id": report.report_id,
            "report_id": report.report_id,
            "name": cover.report_title if cover else "TARA报告",
            "project_name": cover.project_name if cover else "",
            "report_title": cover.report_title if cover else "",
            "status": report.status,
            "created_at": report.created_at.isoformat(),
            "file_path": "",
            "statistics": {
                "assets_count": assets_count,
                "threats_count": tara_count,
                "high_risk_count": 0,
                "measures_count": tara_count,
                "attack_trees_count": attack_trees_count
            }
        })
    
    return {
        "success": True,
        "total": total,
        "page": page,
        "page_size": page_size,
        "reports": result
    }


@app.delete("/api/reports/{report_id}")
async def delete_report(report_id: str, db: Session = Depends(get_db)):
    """删除报告"""
    report = db.query(Report).filter(Report.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    # 删除MinIO中的图片
    minio = get_minio_client()
    images = db.query(ReportImage).filter(ReportImage.report_id == report_id).all()
    for image in images:
        try:
            minio.delete_file(image.minio_bucket, image.minio_path)
        except:
            pass
    
    # 删除数据库记录（级联删除）
    db.delete(report)
    db.commit()
    
    return {"success": True, "message": "报告已删除"}


@app.post("/api/upload/batch")
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
    
    这个端点同时接收JSON数据文件和所有图片文件，
    自动处理图片保存和路径关联，然后保存到数据库。
    返回报告ID，可用于后续生成Excel/PDF报告。
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
    
    # 自动调用报告服务生成Excel报告
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            generate_resp = await client.post(
                f"{REPORT_SERVICE_URL}/api/reports/{report_id}/generate",
                params={"format": "xlsx"}
            )
            if generate_resp.status_code == 200:
                print(f"Report {report_id} generated successfully")
            else:
                print(f"Failed to generate report {report_id}: {generate_resp.text}")
    except Exception as e:
        print(f"Failed to call report service: {e}")
        # 不阻止返回，让用户可以手动生成
    
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
        'download_url': f"/api/reports/{report_id}/download",
        'preview_url': f"/api/reports/{report_id}/preview"
    }


# ==================== 启动函数 ====================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )
