"""
数据库模型定义（报告服务仅需要部分模型）
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base


class Report(Base):
    """报告主表"""
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(String(50), unique=True, index=True, nullable=False, comment="报告ID")
    status = Column(String(20), default="pending", comment="状态: pending, processing, completed, failed")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    
    # 关联
    cover = relationship("ReportCover", back_populates="report", uselist=False)
    generated_files = relationship("GeneratedReport", back_populates="report", cascade="all, delete-orphan")


class ReportCover(Base):
    """报告封面信息"""
    __tablename__ = "report_covers"
    
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(String(50), ForeignKey("reports.report_id", ondelete="CASCADE"), nullable=False)
    
    report_title = Column(String(200), comment="报告标题")
    report_title_en = Column(String(200), comment="报告英文标题")
    project_name = Column(String(200), comment="项目名称")
    data_level = Column(String(50), comment="数据等级")
    document_number = Column(String(100), comment="文档编号")
    version = Column(String(50), comment="版本")
    author_date = Column(String(100), comment="编制日期")
    review_date = Column(String(100), comment="审核日期")
    sign_date = Column(String(100), comment="会签日期")
    approve_date = Column(String(100), comment="批准日期")
    
    report = relationship("Report", back_populates="cover")


class GeneratedReport(Base):
    """已生成的报告文件"""
    __tablename__ = "generated_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(String(50), ForeignKey("reports.report_id", ondelete="CASCADE"), nullable=False)
    
    file_type = Column(String(20), comment="文件类型: xlsx, pdf")
    minio_path = Column(String(500), comment="MinIO存储路径")
    minio_bucket = Column(String(100), comment="MinIO桶名")
    file_size = Column(Integer, comment="文件大小")
    generated_at = Column(DateTime, default=datetime.now, comment="生成时间")
    
    report = relationship("Report", back_populates="generated_files")
