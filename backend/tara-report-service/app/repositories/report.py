"""
报告数据仓库
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from ..common.models import Report, ReportCover, GeneratedReport


class ReportRepository:
    """报告数据仓库"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_report(self, report_id: str) -> Optional[Report]:
        """获取报告"""
        return self.db.query(Report).filter(Report.report_id == report_id).first()
    
    def get_report_cover(self, report_id: str) -> Optional[ReportCover]:
        """获取报告封面"""
        return self.db.query(ReportCover).filter(ReportCover.report_id == report_id).first()
    
    def get_generated_reports(self, report_id: str) -> List[GeneratedReport]:
        """获取已生成的报告文件"""
        return self.db.query(GeneratedReport).filter(GeneratedReport.report_id == report_id).all()
    
    def get_generated_report(self, report_id: str, file_type: str) -> Optional[GeneratedReport]:
        """获取指定类型的已生成报告"""
        return self.db.query(GeneratedReport).filter(
            GeneratedReport.report_id == report_id,
            GeneratedReport.file_type == file_type
        ).first()
    
    def create_or_update_generated_report(
        self,
        report_id: str,
        file_type: str,
        minio_path: str,
        minio_bucket: str,
        file_size: int
    ) -> GeneratedReport:
        """创建或更新已生成的报告记录"""
        existing = self.get_generated_report(report_id, file_type)
        
        if existing:
            existing.minio_path = minio_path
            existing.file_size = file_size
            existing.generated_at = datetime.now()
            return existing
        else:
            generated = GeneratedReport(
                report_id=report_id,
                file_type=file_type,
                minio_path=minio_path,
                minio_bucket=minio_bucket,
                file_size=file_size
            )
            self.db.add(generated)
            return generated
    
    def commit(self):
        """提交事务"""
        self.db.commit()
