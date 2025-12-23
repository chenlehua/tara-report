"""
上传解析模块集成服务
用于从上传解析模块获取报告数据
"""
import os
import httpx
from typing import Optional, Dict, Any
from pathlib import Path

# 上传解析服务地址
UPLOAD_PARSER_URL = os.getenv("UPLOAD_PARSER_URL", "http://localhost:8001")


class UploadParserClient:
    """上传解析模块客户端"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or UPLOAD_PARSER_URL
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=30.0
        )
    
    async def close(self):
        """关闭客户端"""
        await self.client.aclose()
    
    async def get_cover(self, report_id: str) -> Optional[Dict[str, Any]]:
        """获取封面数据"""
        try:
            response = await self.client.get(f"/api/upload-parser/reports/{report_id}/cover")
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Failed to get cover: {e}")
            return None
    
    async def get_definitions(self, report_id: str) -> Optional[Dict[str, Any]]:
        """获取项目定义"""
        try:
            response = await self.client.get(f"/api/upload-parser/reports/{report_id}/definitions")
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Failed to get definitions: {e}")
            return None
    
    async def get_assets(self, report_id: str) -> Optional[Dict[str, Any]]:
        """获取资产列表"""
        try:
            response = await self.client.get(f"/api/upload-parser/reports/{report_id}/assets")
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Failed to get assets: {e}")
            return None
    
    async def get_attack_trees(self, report_id: str) -> Optional[Dict[str, Any]]:
        """获取攻击树列表"""
        try:
            response = await self.client.get(f"/api/upload-parser/reports/{report_id}/attack-trees")
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Failed to get attack trees: {e}")
            return None
    
    async def get_tara_results(self, report_id: str) -> Optional[Dict[str, Any]]:
        """获取TARA分析结果"""
        try:
            response = await self.client.get(f"/api/upload-parser/reports/{report_id}/tara-results")
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Failed to get TARA results: {e}")
            return None
    
    async def get_full_report_data(self, report_id: str) -> Optional[Dict[str, Any]]:
        """获取完整报告数据"""
        try:
            response = await self.client.get(f"/api/upload-parser/reports/{report_id}/full-data")
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Failed to get full report data: {e}")
            return None
    
    async def get_image_info(self, image_id: str) -> Optional[Dict[str, Any]]:
        """获取图片信息"""
        try:
            response = await self.client.get(f"/api/upload-parser/images/{image_id}/info")
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Failed to get image info: {e}")
            return None
    
    async def download_image(self, image_id: str) -> Optional[bytes]:
        """下载图片数据"""
        try:
            response = await self.client.get(f"/api/upload-parser/images/{image_id}")
            if response.status_code == 200:
                return response.content
            return None
        except Exception as e:
            print(f"Failed to download image: {e}")
            return None
    
    def convert_to_report_format(self, full_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        将上传解析模块返回的数据转换为报告生成模块所需的格式
        """
        report_data = {}
        
        # 转换封面数据
        if full_data.get('cover'):
            cover = full_data['cover']
            report_data['cover'] = {
                'report_title': cover.get('report_title', '威胁分析和风险评估报告'),
                'report_title_en': cover.get('report_title_en', 'Threat Analysis And Risk Assessment Report'),
                'project_name': cover.get('project_name', ''),
                'data_level': cover.get('data_level', '秘密'),
                'document_number': cover.get('document_number', ''),
                'version': cover.get('version', 'V1.0'),
                'author_date': cover.get('author_date', ''),
                'review_date': cover.get('review_date', ''),
                'sign_date': cover.get('sign_date', ''),
                'approve_date': cover.get('approve_date', '')
            }
        
        # 转换定义数据
        if full_data.get('definitions'):
            definitions = full_data['definitions']
            report_data['definitions'] = {
                'title': definitions.get('title', 'TARA分析报告 - 相关定义'),
                'functional_description': definitions.get('functional_description', ''),
                'assumptions': definitions.get('assumptions', []),
                'terminology': definitions.get('terminology', [])
            }
            
            # 处理图片路径
            if definitions.get('item_boundary_image'):
                report_data['definitions']['item_boundary_image'] = definitions['item_boundary_image'].get('url')
            if definitions.get('system_architecture_image'):
                report_data['definitions']['system_architecture_image'] = definitions['system_architecture_image'].get('url')
            if definitions.get('software_architecture_image'):
                report_data['definitions']['software_architecture_image'] = definitions['software_architecture_image'].get('url')
        
        # 转换资产数据
        if full_data.get('assets'):
            assets = full_data['assets']
            report_data['assets'] = {
                'title': assets.get('title', '资产列表 Asset List'),
                'assets': []
            }
            
            # 处理数据流图片
            if assets.get('dataflow_image'):
                report_data['assets']['dataflow_image'] = assets['dataflow_image'].get('url')
            
            for asset in assets.get('assets', []):
                report_data['assets']['assets'].append({
                    'id': asset.get('asset_id', ''),
                    'name': asset.get('name', ''),
                    'category': asset.get('category', ''),
                    'remarks': asset.get('remarks', ''),
                    'authenticity': asset.get('authenticity', False),
                    'integrity': asset.get('integrity', False),
                    'non_repudiation': asset.get('non_repudiation', False),
                    'confidentiality': asset.get('confidentiality', False),
                    'availability': asset.get('availability', False),
                    'authorization': asset.get('authorization', False)
                })
        
        # 转换攻击树数据
        if full_data.get('attack_trees'):
            attack_trees = full_data['attack_trees']
            report_data['attack_trees'] = {'attack_trees': []}
            
            for tree in attack_trees.get('attack_trees', []):
                tree_data = {
                    'asset_id': tree.get('asset_id', ''),
                    'asset_name': tree.get('asset_name', ''),
                    'title': tree.get('title', '')
                }
                
                if tree.get('image'):
                    tree_data['image'] = tree['image'].get('url')
                
                report_data['attack_trees']['attack_trees'].append(tree_data)
        
        # 转换TARA结果数据
        if full_data.get('tara_results'):
            tara_results = full_data['tara_results']
            report_data['tara_results'] = {
                'title': tara_results.get('title', 'TARA分析结果 TARA Analysis Results'),
                'results': []
            }
            
            for result in tara_results.get('results', []):
                report_data['tara_results']['results'].append({
                    'asset_id': result.get('asset_id', ''),
                    'asset_name': result.get('asset_name', ''),
                    'subdomain1': result.get('subdomain1', ''),
                    'subdomain2': result.get('subdomain2', ''),
                    'subdomain3': result.get('subdomain3', ''),
                    'category': result.get('category', ''),
                    'security_attribute': result.get('security_attribute', ''),
                    'stride_model': result.get('stride_model', ''),
                    'threat_scenario': result.get('threat_scenario', ''),
                    'attack_path': result.get('attack_path', ''),
                    'wp29_mapping': result.get('wp29_mapping', ''),
                    'attack_vector': result.get('attack_vector', '本地'),
                    'attack_complexity': result.get('attack_complexity', '低'),
                    'privileges_required': result.get('privileges_required', '低'),
                    'user_interaction': result.get('user_interaction', '不需要'),
                    'safety_impact': result.get('safety_impact', '中等的'),
                    'financial_impact': result.get('financial_impact', '中等的'),
                    'operational_impact': result.get('operational_impact', '中等的'),
                    'privacy_impact': result.get('privacy_impact', '可忽略不计的'),
                    'security_requirement': result.get('security_requirement', '')
                })
        
        return report_data


# 全局客户端实例
_upload_parser_client: Optional[UploadParserClient] = None


def get_upload_parser_client() -> UploadParserClient:
    """获取上传解析客户端实例"""
    global _upload_parser_client
    if _upload_parser_client is None:
        _upload_parser_client = UploadParserClient()
    return _upload_parser_client


async def close_upload_parser_client():
    """关闭上传解析客户端"""
    global _upload_parser_client
    if _upload_parser_client is not None:
        await _upload_parser_client.close()
        _upload_parser_client = None
