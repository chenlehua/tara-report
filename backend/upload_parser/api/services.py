"""
报告解析服务
处理JSON解析、数据存储和图片管理
"""
import json
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from ..db import (
    Report, Image, Cover, Definition, Asset, 
    AssetDataflow, AttackTree, TaraResult,
    ImageType, ReportStatus, generate_report_id, generate_image_id
)
from ..storage import get_minio_storage, MinioStorageService
from ..models import (
    ImageInfo, CoverResponse, DefinitionResponse, AssetResponse,
    AssetsListResponse, AttackTreeResponse, AttackTreesListResponse,
    TaraResultResponse, TaraResultsListResponse, FullReportDataResponse,
    AssumptionItem, TerminologyItem
)


class ReportParserService:
    """报告解析服务"""
    
    def __init__(self, db: AsyncSession, minio: Optional[MinioStorageService] = None):
        self.db = db
        self.minio = minio or get_minio_storage()
    
    # ==================== 报告管理 ====================
    
    async def create_report(self, name: Optional[str] = None) -> Report:
        """创建新报告"""
        report = Report(
            id=generate_report_id(),
            name=name,
            status=ReportStatus.PENDING
        )
        self.db.add(report)
        await self.db.flush()
        return report
    
    async def get_report(self, report_id: str) -> Optional[Report]:
        """获取报告"""
        result = await self.db.execute(
            select(Report).where(Report.id == report_id)
        )
        return result.scalar_one_or_none()
    
    async def update_report_status(self, report_id: str, status: ReportStatus) -> bool:
        """更新报告状态"""
        report = await self.get_report(report_id)
        if report:
            report.status = status
            await self.db.flush()
            return True
        return False
    
    async def delete_report(self, report_id: str) -> bool:
        """删除报告及其所有关联数据"""
        report = await self.get_report(report_id)
        if report:
            # 删除MinIO中的图片
            self.minio.delete_report_images(report_id)
            # 删除数据库记录(级联删除)
            await self.db.delete(report)
            await self.db.flush()
            return True
        return False
    
    # ==================== 图片管理 ====================
    
    async def upload_image(
        self,
        report_id: str,
        file_data: bytes,
        filename: str,
        image_type: str,
        content_type: str = "image/png",
        attack_tree_id: Optional[str] = None
    ) -> Image:
        """上传图片"""
        # 验证报告存在
        report = await self.get_report(report_id)
        if not report:
            raise ValueError(f"Report {report_id} not found")
        
        # 上传到MinIO
        minio_path, file_size = self.minio.upload_image_sync(
            file_data=file_data,
            report_id=report_id,
            image_type=image_type,
            filename=filename,
            content_type=content_type
        )
        
        # 保存到数据库
        image = Image(
            id=generate_image_id(),
            report_id=report_id,
            image_type=ImageType(image_type) if image_type in [e.value for e in ImageType] else ImageType.OTHER,
            original_name=filename,
            minio_path=minio_path,
            minio_bucket=self.minio.bucket_name,
            file_size=file_size,
            content_type=content_type,
            attack_tree_id=attack_tree_id
        )
        self.db.add(image)
        await self.db.flush()
        
        return image
    
    async def get_image(self, image_id: str) -> Optional[Image]:
        """获取图片信息"""
        result = await self.db.execute(
            select(Image).where(Image.id == image_id)
        )
        return result.scalar_one_or_none()
    
    async def get_report_images(self, report_id: str, image_type: Optional[str] = None) -> List[Image]:
        """获取报告的图片列表"""
        query = select(Image).where(Image.report_id == report_id)
        if image_type:
            query = query.where(Image.image_type == ImageType(image_type))
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    def get_image_url(self, image: Image) -> str:
        """获取图片URL"""
        return self.minio.get_image_url(image.minio_path)
    
    def image_to_info(self, image: Image) -> ImageInfo:
        """将Image模型转换为ImageInfo"""
        return ImageInfo(
            id=image.id,
            image_type=image.image_type.value,
            original_name=image.original_name,
            minio_path=image.minio_path,
            file_size=image.file_size,
            content_type=image.content_type,
            url=self.get_image_url(image),
            created_at=image.created_at
        )
    
    # ==================== 封面管理 ====================
    
    async def save_cover(self, report_id: str, cover_data: Dict[str, Any]) -> Cover:
        """保存封面数据"""
        # 检查是否已存在
        result = await self.db.execute(
            select(Cover).where(Cover.report_id == report_id)
        )
        cover = result.scalar_one_or_none()
        
        if cover:
            # 更新
            for key, value in cover_data.items():
                if hasattr(cover, key):
                    setattr(cover, key, value)
        else:
            # 创建
            cover = Cover(report_id=report_id, **cover_data)
            self.db.add(cover)
        
        await self.db.flush()
        return cover
    
    async def get_cover(self, report_id: str) -> Optional[CoverResponse]:
        """获取封面数据"""
        result = await self.db.execute(
            select(Cover).where(Cover.report_id == report_id)
        )
        cover = result.scalar_one_or_none()
        
        if not cover:
            return None
        
        return CoverResponse(
            id=cover.id,
            report_id=cover.report_id,
            report_title=cover.report_title,
            report_title_en=cover.report_title_en,
            project_name=cover.project_name,
            data_level=cover.data_level,
            document_number=cover.document_number,
            version=cover.version,
            author_date=cover.author_date,
            review_date=cover.review_date,
            sign_date=cover.sign_date,
            approve_date=cover.approve_date
        )
    
    # ==================== 项目定义管理 ====================
    
    async def save_definition(self, report_id: str, definition_data: Dict[str, Any]) -> Definition:
        """保存项目定义"""
        result = await self.db.execute(
            select(Definition).where(Definition.report_id == report_id)
        )
        definition = result.scalar_one_or_none()
        
        # 处理假设和术语(转换为JSON)
        if 'assumptions' in definition_data and isinstance(definition_data['assumptions'], list):
            definition_data['assumptions'] = [
                {'id': a.get('id', ''), 'description': a.get('description', '')}
                for a in definition_data['assumptions']
            ]
        
        if 'terminology' in definition_data and isinstance(definition_data['terminology'], list):
            definition_data['terminology'] = [
                {'abbreviation': t.get('abbreviation', ''), 'english': t.get('english', ''), 'chinese': t.get('chinese', '')}
                for t in definition_data['terminology']
            ]
        
        if definition:
            for key, value in definition_data.items():
                if hasattr(definition, key):
                    setattr(definition, key, value)
        else:
            definition = Definition(report_id=report_id, **definition_data)
            self.db.add(definition)
        
        await self.db.flush()
        return definition
    
    async def get_definition(self, report_id: str) -> Optional[DefinitionResponse]:
        """获取项目定义(包含图片信息)"""
        result = await self.db.execute(
            select(Definition).where(Definition.report_id == report_id)
        )
        definition = result.scalar_one_or_none()
        
        if not definition:
            return None
        
        # 获取相关图片
        async def get_image_info(image_id: Optional[str]) -> Optional[ImageInfo]:
            if not image_id:
                return None
            image = await self.get_image(image_id)
            if image:
                return self.image_to_info(image)
            return None
        
        item_boundary_image = await get_image_info(definition.item_boundary_image_id)
        system_architecture_image = await get_image_info(definition.system_architecture_image_id)
        software_architecture_image = await get_image_info(definition.software_architecture_image_id)
        
        # 解析假设和术语
        assumptions = []
        if definition.assumptions:
            assumptions = [AssumptionItem(**a) for a in definition.assumptions]
        
        terminology = []
        if definition.terminology:
            terminology = [TerminologyItem(**t) for t in definition.terminology]
        
        return DefinitionResponse(
            id=definition.id,
            report_id=definition.report_id,
            title=definition.title,
            functional_description=definition.functional_description,
            item_boundary_image=item_boundary_image,
            system_architecture_image=system_architecture_image,
            software_architecture_image=software_architecture_image,
            assumptions=assumptions,
            terminology=terminology
        )
    
    # ==================== 资产管理 ====================
    
    async def save_assets(self, report_id: str, assets_data: Dict[str, Any]) -> List[Asset]:
        """保存资产列表"""
        # 删除旧资产
        await self.db.execute(
            delete(Asset).where(Asset.report_id == report_id)
        )
        
        # 保存数据流配置
        dataflow_config = await self.db.execute(
            select(AssetDataflow).where(AssetDataflow.report_id == report_id)
        )
        asset_dataflow = dataflow_config.scalar_one_or_none()
        
        title = assets_data.get('title', '资产列表 Asset List')
        dataflow_image_id = assets_data.get('dataflow_image_id')
        
        if asset_dataflow:
            asset_dataflow.title = title
            asset_dataflow.dataflow_image_id = dataflow_image_id
        else:
            asset_dataflow = AssetDataflow(
                report_id=report_id,
                title=title,
                dataflow_image_id=dataflow_image_id
            )
            self.db.add(asset_dataflow)
        
        # 创建新资产
        assets = []
        for idx, asset_data in enumerate(assets_data.get('assets', [])):
            asset = Asset(
                report_id=report_id,
                asset_id=asset_data.get('id', f'A{idx+1:03d}'),
                name=asset_data.get('name', ''),
                category=asset_data.get('category'),
                remarks=asset_data.get('remarks'),
                authenticity=asset_data.get('authenticity', False),
                integrity=asset_data.get('integrity', False),
                non_repudiation=asset_data.get('non_repudiation', False),
                confidentiality=asset_data.get('confidentiality', False),
                availability=asset_data.get('availability', False),
                authorization=asset_data.get('authorization', False),
                sort_order=idx
            )
            self.db.add(asset)
            assets.append(asset)
        
        await self.db.flush()
        return assets
    
    async def get_assets(self, report_id: str) -> Optional[AssetsListResponse]:
        """获取资产列表(包含图片信息)"""
        # 获取数据流配置
        result = await self.db.execute(
            select(AssetDataflow).where(AssetDataflow.report_id == report_id)
        )
        asset_dataflow = result.scalar_one_or_none()
        
        # 获取资产列表
        result = await self.db.execute(
            select(Asset).where(Asset.report_id == report_id).order_by(Asset.sort_order)
        )
        assets = list(result.scalars().all())
        
        if not assets and not asset_dataflow:
            return None
        
        # 获取数据流图片
        dataflow_image = None
        if asset_dataflow and asset_dataflow.dataflow_image_id:
            image = await self.get_image(asset_dataflow.dataflow_image_id)
            if image:
                dataflow_image = self.image_to_info(image)
        
        # 构建响应
        asset_responses = []
        for asset in assets:
            # 获取资产级别的数据流图片
            asset_dataflow_image = None
            if asset.dataflow_image_id:
                image = await self.get_image(asset.dataflow_image_id)
                if image:
                    asset_dataflow_image = self.image_to_info(image)
            
            asset_responses.append(AssetResponse(
                id=asset.id,
                report_id=asset.report_id,
                asset_id=asset.asset_id,
                name=asset.name,
                category=asset.category,
                remarks=asset.remarks,
                authenticity=asset.authenticity,
                integrity=asset.integrity,
                non_repudiation=asset.non_repudiation,
                confidentiality=asset.confidentiality,
                availability=asset.availability,
                authorization=asset.authorization,
                dataflow_image=asset_dataflow_image
            ))
        
        return AssetsListResponse(
            report_id=report_id,
            title=asset_dataflow.title if asset_dataflow else "资产列表 Asset List",
            dataflow_image=dataflow_image,
            assets=asset_responses
        )
    
    # ==================== 攻击树管理 ====================
    
    async def save_attack_trees(self, report_id: str, attack_trees_data: Dict[str, Any]) -> List[AttackTree]:
        """保存攻击树列表"""
        # 删除旧攻击树
        await self.db.execute(
            delete(AttackTree).where(AttackTree.report_id == report_id)
        )
        
        attack_trees = []
        for idx, tree_data in enumerate(attack_trees_data.get('attack_trees', [])):
            attack_tree = AttackTree(
                report_id=report_id,
                asset_id=tree_data.get('asset_id'),
                asset_name=tree_data.get('asset_name'),
                title=tree_data.get('title'),
                description=tree_data.get('description'),
                sort_order=idx
            )
            self.db.add(attack_tree)
            attack_trees.append(attack_tree)
        
        await self.db.flush()
        return attack_trees
    
    async def get_attack_trees(self, report_id: str) -> Optional[AttackTreesListResponse]:
        """获取攻击树列表(包含图片信息)"""
        result = await self.db.execute(
            select(AttackTree)
            .where(AttackTree.report_id == report_id)
            .order_by(AttackTree.sort_order)
            .options(selectinload(AttackTree.image))
        )
        attack_trees = list(result.scalars().all())
        
        if not attack_trees:
            return None
        
        attack_tree_responses = []
        for tree in attack_trees:
            image_info = None
            if tree.image:
                image_info = self.image_to_info(tree.image)
            
            attack_tree_responses.append(AttackTreeResponse(
                id=tree.id,
                report_id=tree.report_id,
                asset_id=tree.asset_id,
                asset_name=tree.asset_name,
                title=tree.title,
                description=tree.description,
                image=image_info
            ))
        
        return AttackTreesListResponse(
            report_id=report_id,
            attack_trees=attack_tree_responses
        )
    
    # ==================== TARA结果管理 ====================
    
    async def save_tara_results(self, report_id: str, tara_data: Dict[str, Any]) -> List[TaraResult]:
        """保存TARA分析结果"""
        # 删除旧结果
        await self.db.execute(
            delete(TaraResult).where(TaraResult.report_id == report_id)
        )
        
        tara_results = []
        for idx, result_data in enumerate(tara_data.get('results', [])):
            tara_result = TaraResult(
                report_id=report_id,
                asset_id=result_data.get('asset_id', ''),
                asset_name=result_data.get('asset_name', ''),
                subdomain1=result_data.get('subdomain1'),
                subdomain2=result_data.get('subdomain2'),
                subdomain3=result_data.get('subdomain3'),
                category=result_data.get('category'),
                security_attribute=result_data.get('security_attribute'),
                stride_model=result_data.get('stride_model'),
                threat_scenario=result_data.get('threat_scenario'),
                attack_path=result_data.get('attack_path'),
                wp29_mapping=result_data.get('wp29_mapping'),
                attack_vector=result_data.get('attack_vector', '本地'),
                attack_complexity=result_data.get('attack_complexity', '低'),
                privileges_required=result_data.get('privileges_required', '低'),
                user_interaction=result_data.get('user_interaction', '不需要'),
                safety_impact=result_data.get('safety_impact', '中等的'),
                financial_impact=result_data.get('financial_impact', '中等的'),
                operational_impact=result_data.get('operational_impact', '中等的'),
                privacy_impact=result_data.get('privacy_impact', '可忽略不计的'),
                security_requirement=result_data.get('security_requirement'),
                sort_order=idx
            )
            self.db.add(tara_result)
            tara_results.append(tara_result)
        
        await self.db.flush()
        return tara_results
    
    async def get_tara_results(self, report_id: str) -> Optional[TaraResultsListResponse]:
        """获取TARA分析结果"""
        result = await self.db.execute(
            select(TaraResult)
            .where(TaraResult.report_id == report_id)
            .order_by(TaraResult.sort_order)
        )
        tara_results = list(result.scalars().all())
        
        if not tara_results:
            return None
        
        result_responses = []
        for tr in tara_results:
            result_responses.append(TaraResultResponse(
                id=tr.id,
                report_id=tr.report_id,
                asset_id=tr.asset_id,
                asset_name=tr.asset_name,
                subdomain1=tr.subdomain1,
                subdomain2=tr.subdomain2,
                subdomain3=tr.subdomain3,
                category=tr.category,
                security_attribute=tr.security_attribute,
                stride_model=tr.stride_model,
                threat_scenario=tr.threat_scenario,
                attack_path=tr.attack_path,
                wp29_mapping=tr.wp29_mapping,
                attack_vector=tr.attack_vector,
                attack_complexity=tr.attack_complexity,
                privileges_required=tr.privileges_required,
                user_interaction=tr.user_interaction,
                safety_impact=tr.safety_impact,
                financial_impact=tr.financial_impact,
                operational_impact=tr.operational_impact,
                privacy_impact=tr.privacy_impact,
                security_requirement=tr.security_requirement
            ))
        
        return TaraResultsListResponse(
            report_id=report_id,
            title="TARA分析结果 TARA Analysis Results",
            results=result_responses
        )
    
    # ==================== 完整报告数据 ====================
    
    async def get_full_report_data(self, report_id: str) -> Optional[FullReportDataResponse]:
        """获取完整报告数据(用于报告生成)"""
        report = await self.get_report(report_id)
        if not report:
            return None
        
        cover = await self.get_cover(report_id)
        definitions = await self.get_definition(report_id)
        assets = await self.get_assets(report_id)
        attack_trees = await self.get_attack_trees(report_id)
        tara_results = await self.get_tara_results(report_id)
        
        return FullReportDataResponse(
            report_id=report_id,
            cover=cover,
            definitions=definitions,
            assets=assets,
            attack_trees=attack_trees,
            tara_results=tara_results
        )
    
    # ==================== JSON解析和导入 ====================
    
    async def parse_and_save_json(
        self,
        report_id: str,
        json_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """解析JSON数据并保存到数据库"""
        summary = {
            'report_id': report_id,
            'cover': False,
            'definitions': False,
            'assets_count': 0,
            'attack_trees_count': 0,
            'tara_results_count': 0
        }
        
        # 保存封面
        if 'cover' in json_data and json_data['cover']:
            await self.save_cover(report_id, json_data['cover'])
            summary['cover'] = True
        
        # 保存项目定义
        if 'definitions' in json_data and json_data['definitions']:
            await self.save_definition(report_id, json_data['definitions'])
            summary['definitions'] = True
        
        # 保存资产
        if 'assets' in json_data and json_data['assets']:
            assets = await self.save_assets(report_id, json_data['assets'])
            summary['assets_count'] = len(assets)
        
        # 保存攻击树
        if 'attack_trees' in json_data and json_data['attack_trees']:
            attack_trees = await self.save_attack_trees(report_id, json_data['attack_trees'])
            summary['attack_trees_count'] = len(attack_trees)
        
        # 保存TARA结果
        if 'tara_results' in json_data and json_data['tara_results']:
            tara_results = await self.save_tara_results(report_id, json_data['tara_results'])
            summary['tara_results_count'] = len(tara_results)
        
        # 更新报告状态
        await self.update_report_status(report_id, ReportStatus.COMPLETED)
        
        return summary
