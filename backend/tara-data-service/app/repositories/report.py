"""
报告数据仓库
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from ..common.models import (
    Report, ReportCover, ReportDefinitions, ReportAsset,
    ReportAttackTree, ReportTARAResult, ReportImage
)


class ReportRepository:
    """报告数据仓库"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_report(self, report_id: str, status: str = "pending") -> Report:
        """创建报告记录"""
        report = Report(report_id=report_id, status=status)
        self.db.add(report)
        self.db.flush()
        return report
    
    def get_report(self, report_id: str) -> Optional[Report]:
        """获取报告"""
        return self.db.query(Report).filter(Report.report_id == report_id).first()
    
    def get_report_cover(self, report_id: str) -> Optional[ReportCover]:
        """获取报告封面"""
        return self.db.query(ReportCover).filter(ReportCover.report_id == report_id).first()
    
    def get_report_definitions(self, report_id: str) -> Optional[ReportDefinitions]:
        """获取报告定义"""
        return self.db.query(ReportDefinitions).filter(ReportDefinitions.report_id == report_id).first()
    
    def get_report_assets(self, report_id: str) -> List[ReportAsset]:
        """获取报告资产列表"""
        return self.db.query(ReportAsset).filter(ReportAsset.report_id == report_id).all()
    
    def get_report_attack_trees(self, report_id: str) -> List[ReportAttackTree]:
        """获取报告攻击树"""
        return self.db.query(ReportAttackTree).filter(
            ReportAttackTree.report_id == report_id
        ).order_by(ReportAttackTree.sort_order).all()
    
    def get_report_tara_results(self, report_id: str) -> List[ReportTARAResult]:
        """获取TARA分析结果"""
        return self.db.query(ReportTARAResult).filter(
            ReportTARAResult.report_id == report_id
        ).order_by(ReportTARAResult.sort_order).all()
    
    def get_report_images(self, report_id: str) -> List[ReportImage]:
        """获取报告图片"""
        return self.db.query(ReportImage).filter(ReportImage.report_id == report_id).all()
    
    def get_image_by_id(self, image_id: str) -> Optional[ReportImage]:
        """根据ID获取图片"""
        return self.db.query(ReportImage).filter(ReportImage.image_id == image_id).first()
    
    def create_cover(self, report_id: str, data: Dict[str, Any]) -> ReportCover:
        """创建报告封面"""
        cover = ReportCover(
            report_id=report_id,
            report_title=data.get('report_title', '威胁分析和风险评估报告'),
            report_title_en=data.get('report_title_en', 'Threat Analysis And Risk Assessment Report'),
            project_name=data.get('project_name', ''),
            data_level=data.get('data_level', '秘密'),
            document_number=data.get('document_number', ''),
            version=data.get('version', ''),
            author_date=data.get('author_date', ''),
            review_date=data.get('review_date', ''),
            sign_date=data.get('sign_date', ''),
            approve_date=data.get('approve_date', '')
        )
        self.db.add(cover)
        return cover
    
    def create_definitions(self, report_id: str, data: Dict[str, Any], image_paths: Dict[str, str] = None) -> ReportDefinitions:
        """创建报告定义"""
        image_paths = image_paths or {}
        definitions = ReportDefinitions(
            report_id=report_id,
            title=data.get('title', ''),
            functional_description=data.get('functional_description', ''),
            item_boundary_image=image_paths.get('item_boundary'),
            system_architecture_image=image_paths.get('system_architecture'),
            software_architecture_image=image_paths.get('software_architecture'),
            dataflow_image=image_paths.get('dataflow'),
            assumptions=data.get('assumptions', []),
            terminology=data.get('terminology', [])
        )
        self.db.add(definitions)
        return definitions
    
    def create_asset(self, report_id: str, data: Dict[str, Any]) -> ReportAsset:
        """创建资产记录"""
        asset = ReportAsset(
            report_id=report_id,
            asset_id=data.get('id', ''),
            name=data.get('name', ''),
            category=data.get('category', ''),
            remarks=data.get('remarks', ''),
            authenticity=data.get('authenticity', False),
            integrity=data.get('integrity', False),
            non_repudiation=data.get('non_repudiation', False),
            confidentiality=data.get('confidentiality', False),
            availability=data.get('availability', False),
            authorization=data.get('authorization', False)
        )
        self.db.add(asset)
        return asset
    
    def create_attack_tree(self, report_id: str, data: Dict[str, Any], sort_order: int, image_path: str = None) -> ReportAttackTree:
        """创建攻击树记录"""
        tree = ReportAttackTree(
            report_id=report_id,
            asset_id=data.get('asset_id', ''),
            asset_name=data.get('asset_name', ''),
            title=data.get('title', f'攻击树 {sort_order + 1}'),
            image=image_path or data.get('image', ''),
            sort_order=sort_order
        )
        self.db.add(tree)
        return tree
    
    def create_tara_result(self, report_id: str, data: Dict[str, Any], sort_order: int) -> ReportTARAResult:
        """创建TARA分析结果"""
        result = ReportTARAResult(
            report_id=report_id,
            asset_id=data.get('asset_id', ''),
            asset_name=data.get('asset_name', ''),
            subdomain1=data.get('subdomain1', ''),
            subdomain2=data.get('subdomain2', ''),
            subdomain3=data.get('subdomain3', ''),
            category=data.get('category', ''),
            security_attribute=data.get('security_attribute', ''),
            stride_model=data.get('stride_model', ''),
            threat_scenario=data.get('threat_scenario', ''),
            attack_path=data.get('attack_path', ''),
            wp29_mapping=data.get('wp29_mapping', ''),
            attack_vector=data.get('attack_vector', ''),
            attack_complexity=data.get('attack_complexity', ''),
            privileges_required=data.get('privileges_required', ''),
            user_interaction=data.get('user_interaction', ''),
            safety_impact=data.get('safety_impact', ''),
            financial_impact=data.get('financial_impact', ''),
            operational_impact=data.get('operational_impact', ''),
            privacy_impact=data.get('privacy_impact', ''),
            security_goal=data.get('security_goal', ''),
            security_requirement=data.get('security_requirement', ''),
            sort_order=sort_order
        )
        self.db.add(result)
        return result
    
    def create_image(self, report_id: str, image_id: str, image_type: str,
                     original_name: str, minio_path: str, minio_bucket: str,
                     file_size: int, content_type: str) -> ReportImage:
        """创建图片记录"""
        image = ReportImage(
            report_id=report_id,
            image_id=image_id,
            image_type=image_type,
            original_name=original_name,
            minio_path=minio_path,
            minio_bucket=minio_bucket,
            file_size=file_size,
            content_type=content_type
        )
        self.db.add(image)
        return image
    
    def update_report_status(self, report_id: str, status: str) -> None:
        """更新报告状态"""
        report = self.get_report(report_id)
        if report:
            report.status = status
    
    def delete_report(self, report_id: str) -> bool:
        """删除报告"""
        report = self.get_report(report_id)
        if report:
            self.db.delete(report)
            return True
        return False
    
    def list_reports(self, page: int = 1, page_size: int = 20) -> tuple:
        """获取报告列表"""
        offset = (page - 1) * page_size
        total = self.db.query(Report).count()
        reports = self.db.query(Report).order_by(Report.created_at.desc()).offset(offset).limit(page_size).all()
        return reports, total
    
    def count_assets(self, report_id: str) -> int:
        """统计资产数量"""
        return self.db.query(ReportAsset).filter(ReportAsset.report_id == report_id).count()
    
    def count_tara_results(self, report_id: str) -> int:
        """统计TARA结果数量"""
        return self.db.query(ReportTARAResult).filter(ReportTARAResult.report_id == report_id).count()
    
    def count_attack_trees(self, report_id: str) -> int:
        """统计攻击树数量"""
        return self.db.query(ReportAttackTree).filter(ReportAttackTree.report_id == report_id).count()
    
    def commit(self):
        """提交事务"""
        self.db.commit()
