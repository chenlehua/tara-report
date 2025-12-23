"""
数据服务 - 业务逻辑层
"""
import uuid
import httpx
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
from fastapi import UploadFile

from ..config import settings
from ..common.minio_client import get_minio_client
from ..repositories.report import ReportRepository


class DataService:
    """数据服务"""
    
    def __init__(self, repo: ReportRepository):
        self.repo = repo
        self.minio = get_minio_client()
    
    @staticmethod
    def generate_report_id() -> str:
        """生成报告ID"""
        return f"RPT-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    
    @staticmethod
    def generate_image_id() -> str:
        """生成图片ID"""
        return f"IMG-{uuid.uuid4().hex[:12]}"
    
    async def save_image_to_minio(
        self,
        upload_file: UploadFile,
        report_id: str,
        image_type: str
    ) -> Optional[str]:
        """保存图片到MinIO"""
        if not upload_file or not upload_file.filename:
            return None
        
        file_ext = Path(upload_file.filename).suffix.lower()
        if file_ext not in {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg'}:
            return None
        
        image_id = self.generate_image_id()
        object_name = f"{report_id}/{image_type}/{image_id}{file_ext}"
        
        try:
            content = await upload_file.read()
            self.minio.upload_bytes(
                settings.BUCKET_IMAGES,
                object_name,
                content,
                upload_file.content_type or "image/png"
            )
            
            # 记录图片信息
            self.repo.create_image(
                report_id=report_id,
                image_id=image_id,
                image_type=image_type,
                original_name=upload_file.filename,
                minio_path=object_name,
                minio_bucket=settings.BUCKET_IMAGES,
                file_size=len(content),
                content_type=upload_file.content_type
            )
            
            return object_name
        except Exception as e:
            print(f"Failed to save image {upload_file.filename}: {e}")
            return None
    
    async def upload_report_data(
        self,
        report_data: Dict[str, Any],
        item_boundary_image: UploadFile = None,
        system_architecture_image: UploadFile = None,
        software_architecture_image: UploadFile = None,
        dataflow_image: UploadFile = None,
        attack_tree_images: List[UploadFile] = None
    ) -> Dict[str, Any]:
        """上传报告数据"""
        # 生成报告ID
        report_id = self.generate_report_id()
        
        # 创建报告记录
        self.repo.create_report(report_id, status="pending")
        
        # 保存图片
        image_paths = {}
        if item_boundary_image:
            image_paths['item_boundary'] = await self.save_image_to_minio(
                item_boundary_image, report_id, "item_boundary"
            )
        if system_architecture_image:
            image_paths['system_architecture'] = await self.save_image_to_minio(
                system_architecture_image, report_id, "system_architecture"
            )
        if software_architecture_image:
            image_paths['software_architecture'] = await self.save_image_to_minio(
                software_architecture_image, report_id, "software_architecture"
            )
        if dataflow_image:
            image_paths['dataflow'] = await self.save_image_to_minio(
                dataflow_image, report_id, "dataflow"
            )
        
        # 保存攻击树图片
        attack_tree_paths = []
        if attack_tree_images:
            for i, img in enumerate(attack_tree_images):
                if img and img.filename:
                    path = await self.save_image_to_minio(img, report_id, f"attack_tree_{i}")
                    if path:
                        attack_tree_paths.append(path)
        
        # 保存封面数据
        cover_data = report_data.get('cover', {})
        self.repo.create_cover(report_id, cover_data)
        
        # 保存相关定义
        definitions_data = report_data.get('definitions', {})
        self.repo.create_definitions(report_id, definitions_data, image_paths)
        
        # 保存资产列表
        assets_data = report_data.get('assets', {})
        for asset in assets_data.get('assets', []):
            self.repo.create_asset(report_id, asset)
        
        # 保存攻击树
        attack_trees_data = report_data.get('attack_trees', {})
        trees = attack_trees_data.get('attack_trees', [])
        for i, tree in enumerate(trees):
            image_path = attack_tree_paths[i] if i < len(attack_tree_paths) else None
            self.repo.create_attack_tree(report_id, tree, i, image_path)
        
        # 保存TARA分析结果
        tara_data = report_data.get('tara_results', {})
        for i, result in enumerate(tara_data.get('results', [])):
            self.repo.create_tara_result(report_id, result, i)
        
        # 更新报告状态
        self.repo.update_report_status(report_id, "completed")
        self.repo.commit()
        
        # 统计信息
        statistics = {
            'assets_count': len(assets_data.get('assets', [])),
            'attack_trees_count': len(trees),
            'tara_results_count': len(tara_data.get('results', [])),
            'images_count': len([p for p in list(image_paths.values()) + attack_tree_paths if p])
        }
        
        return {
            'report_id': report_id,
            'statistics': statistics,
            'cover_data': cover_data
        }
    
    async def trigger_report_generation(self, report_id: str):
        """触发报告生成服务"""
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                # 生成Excel报告
                excel_resp = await client.post(
                    f"{settings.REPORT_SERVICE_URL}/api/reports/{report_id}/generate",
                    params={"format": "xlsx"}
                )
                if excel_resp.status_code == 200:
                    print(f"Excel report {report_id} generated successfully")
                else:
                    print(f"Failed to generate Excel report {report_id}: {excel_resp.text}")
                
                # 生成PDF报告
                pdf_resp = await client.post(
                    f"{settings.REPORT_SERVICE_URL}/api/reports/{report_id}/generate",
                    params={"format": "pdf"}
                )
                if pdf_resp.status_code == 200:
                    print(f"PDF report {report_id} generated successfully")
                else:
                    print(f"Failed to generate PDF report {report_id}: {pdf_resp.text}")
        except Exception as e:
            print(f"Failed to call report service: {e}")
    
    def get_report_info(self, report_id: str) -> Dict[str, Any]:
        """获取报告完整信息"""
        report = self.repo.get_report(report_id)
        if not report:
            return None
        
        cover = self.repo.get_report_cover(report_id)
        definitions = self.repo.get_report_definitions(report_id)
        assets = self.repo.get_report_assets(report_id)
        attack_trees = self.repo.get_report_attack_trees(report_id)
        tara_results = self.repo.get_report_tara_results(report_id)
        
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
            "id": report.report_id,
            "report_id": report.report_id,
            "name": cover.report_title if cover else "TARA报告",
            "project_name": cover.project_name if cover else "",
            "status": report.status,
            "created_at": report.created_at.isoformat(),
            "updated_at": report.updated_at.isoformat() if report.updated_at else None,
            "file_path": "",
            "statistics": statistics,
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
            "assets": {
                "title": "资产列表",
                "assets": assets_list,
                "dataflow_image": build_image_url(definitions.dataflow_image) if definitions and definitions.dataflow_image else None
            },
            "attack_trees": {
                "title": "攻击树分析",
                "attack_trees": attack_trees_list
            },
            "tara_results": {
                "title": "TARA分析结果",
                "results": tara_results_list
            }
        }
    
    def list_reports(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """获取报告列表"""
        reports, total = self.repo.list_reports(page, page_size)
        
        result = []
        for report in reports:
            cover = self.repo.get_report_cover(report.report_id)
            assets_count = self.repo.count_assets(report.report_id)
            tara_count = self.repo.count_tara_results(report.report_id)
            attack_trees_count = self.repo.count_attack_trees(report.report_id)
            
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
    
    def delete_report(self, report_id: str) -> bool:
        """删除报告"""
        # 删除MinIO中的图片
        images = self.repo.get_report_images(report_id)
        for image in images:
            try:
                self.minio.delete_file(image.minio_bucket, image.minio_path)
            except:
                pass
        
        # 删除数据库记录
        result = self.repo.delete_report(report_id)
        if result:
            self.repo.commit()
        return result
    
    def get_image_content(self, bucket: str, object_name: str) -> bytes:
        """获取图片内容"""
        return self.minio.download_file(bucket, object_name)
