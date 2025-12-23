"""
报告服务 - 业务逻辑层
"""
import os
import tempfile
import httpx
from typing import Dict, Any, Optional
from pathlib import Path

from ..config import settings
from ..common.minio_client import get_minio_client
from ..repositories.report import ReportRepository
from ..generators.excel import generate_tara_excel_from_json
from ..generators.pdf import generate_tara_pdf_from_json


class ReportService:
    """报告服务"""
    
    def __init__(self, repo: ReportRepository):
        self.repo = repo
        self.minio = get_minio_client()
    
    async def fetch_data_from_service(self, report_id: str) -> Dict[str, Any]:
        """从数据服务获取报告数据"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            endpoints = {
                'cover': f"{settings.DATA_SERVICE_URL}/api/reports/{report_id}/cover",
                'definitions': f"{settings.DATA_SERVICE_URL}/api/reports/{report_id}/definitions",
                'assets': f"{settings.DATA_SERVICE_URL}/api/reports/{report_id}/assets",
                'attack_trees': f"{settings.DATA_SERVICE_URL}/api/reports/{report_id}/attack-trees",
                'tara_results': f"{settings.DATA_SERVICE_URL}/api/reports/{report_id}/tara-results",
            }
            
            data = {}
            for key, url in endpoints.items():
                resp = await client.get(url)
                if resp.status_code != 200:
                    raise Exception(f"无法获取{key}数据")
                data[key] = resp.json()
        
        return data
    
    async def download_image_from_minio(self, minio_path: str, report_id: str) -> Optional[str]:
        """从MinIO下载图片到临时文件"""
        if not minio_path:
            return None
        
        try:
            # 解析路径
            if "/" in minio_path and not minio_path.startswith(report_id):
                bucket, object_name = minio_path.split("/", 1)
            else:
                bucket = settings.BUCKET_IMAGES
                object_name = minio_path
            
            content = self.minio.download_file(bucket, object_name)
            
            # 创建临时文件
            ext = Path(object_name).suffix or '.png'
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
            temp_file.write(content)
            temp_file.close()
            
            return temp_file.name
        except Exception as e:
            print(f"Failed to download image {minio_path}: {e}")
            return None
    
    async def prepare_report_data(self, report_id: str) -> Dict[str, Any]:
        """准备报告数据，包括下载图片到本地临时文件"""
        data = await self.fetch_data_from_service(report_id)
        
        definitions = data.get('definitions', {})
        
        # 下载定义中的图片
        for key in ['item_boundary_image', 'system_architecture_image', 'software_architecture_image']:
            if definitions.get(key):
                local_path = await self.download_image_from_minio(definitions[key], report_id)
                definitions[key] = local_path
        
        # 下载数据流图
        assets = data.get('assets', {})
        if assets.get('dataflow_image'):
            local_path = await self.download_image_from_minio(assets['dataflow_image'], report_id)
            assets['dataflow_image'] = local_path
        
        # 下载攻击树图片
        attack_trees = data.get('attack_trees', {})
        for tree in attack_trees.get('attack_trees', []):
            if tree.get('image'):
                local_path = await self.download_image_from_minio(tree['image'], report_id)
                tree['image'] = local_path
        
        return data
    
    def cleanup_temp_files(self, data: Dict[str, Any]):
        """清理临时文件"""
        paths_to_clean = []
        
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
        
        for path in paths_to_clean:
            try:
                os.unlink(path)
            except:
                pass
    
    async def generate_report(self, report_id: str, format: str = "xlsx") -> Dict[str, Any]:
        """生成报告"""
        # 检查报告是否存在
        report = self.repo.get_report(report_id)
        if not report:
            raise Exception("报告不存在")
        
        # 准备数据
        data = await self.prepare_report_data(report_id)
        
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
            object_name = f"{report_id}/{report_id}{suffix}"
            content_type = "application/pdf" if format.lower() == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            
            self.minio.upload_bytes(settings.BUCKET_REPORTS, object_name, file_content, content_type)
            
            # 记录到数据库
            self.repo.create_or_update_generated_report(
                report_id=report_id,
                file_type=format.lower(),
                minio_path=object_name,
                minio_bucket=settings.BUCKET_REPORTS,
                file_size=len(file_content)
            )
            self.repo.commit()
            
            # 清理临时文件
            self.cleanup_temp_files(data)
            
            # 获取项目名称
            cover = self.repo.get_report_cover(report_id)
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
            self.cleanup_temp_files(data)
            raise e
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass
    
    def download_report(self, report_id: str, format: str = "xlsx") -> tuple:
        """下载报告，返回 (content, filename, content_type)"""
        generated = self.repo.get_generated_report(report_id, format.lower())
        if not generated:
            raise Exception("报告文件不存在，请先生成报告")
        
        content = self.minio.download_file(generated.minio_bucket, generated.minio_path)
        
        cover = self.repo.get_report_cover(report_id)
        project_name = cover.project_name if cover else "TARA报告"
        
        suffix = ".pdf" if format.lower() == "pdf" else ".xlsx"
        content_type = "application/pdf" if format.lower() == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = f"{project_name}_{report_id}{suffix}"
        
        return content, filename, content_type
    
    async def get_preview_data(self, report_id: str) -> Dict[str, Any]:
        """获取报告预览数据"""
        data = await self.fetch_data_from_service(report_id)
        
        report = self.repo.get_report(report_id)
        cover = self.repo.get_report_cover(report_id)
        generated_files = self.repo.get_generated_reports(report_id)
        
        # 构建下载链接
        downloads = {}
        for gf in generated_files:
            downloads[gf.file_type] = {
                "url": f"/api/reports/{report_id}/download?format={gf.file_type}",
                "file_size": gf.file_size,
                "generated_at": gf.generated_at.isoformat() if gf.generated_at else None
            }
        
        # 构建图片URL
        def build_image_url(minio_path):
            if not minio_path:
                return None
            return f"/api/reports/{report_id}/image-by-path?path={minio_path}"
        
        definitions_data = data.get('definitions', {})
        assets_data = data.get('assets', {})
        attack_trees_data = data.get('attack_trees', {})
        tara_results_data = data.get('tara_results', {})
        
        # 处理攻击树
        attack_trees = []
        for tree in attack_trees_data.get('attack_trees', []):
            tree_copy = dict(tree)
            if tree.get('image'):
                tree_copy['image_url'] = build_image_url(tree['image'])
            attack_trees.append(tree_copy)
        
        assets_list = assets_data.get('assets', [])
        tara_results_list = tara_results_data.get('results', [])
        
        statistics = {
            'assets_count': len(assets_list),
            'threats_count': len(tara_results_list),
            'high_risk_count': sum(1 for r in tara_results_list if r.get('operational_impact') in ['重大的', '严重的']),
            'measures_count': len(tara_results_list),
            'attack_trees_count': len(attack_trees)
        }
        
        return {
            'id': report_id,
            'report_id': report_id,
            'name': cover.report_title if cover else 'TARA报告',
            'project_name': cover.project_name if cover else '',
            'status': report.status if report else 'completed',
            'created_at': report.created_at.isoformat() if report else '',
            'statistics': statistics,
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
