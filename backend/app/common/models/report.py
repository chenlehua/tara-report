"""
数据库模型定义 (SQLAlchemy ORM)
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.common.database.mysql import Base


class Report(Base):
    """报告主表"""
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(String(50), unique=True, index=True, nullable=False, comment="报告ID")
    status = Column(String(20), default="pending", comment="状态: pending, processing, completed, failed")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    
    # 关联
    cover = relationship("ReportCover", back_populates="report", uselist=False, cascade="all, delete-orphan")
    definitions = relationship("ReportDefinitions", back_populates="report", uselist=False, cascade="all, delete-orphan")
    assets = relationship("ReportAsset", back_populates="report", cascade="all, delete-orphan")
    attack_trees = relationship("ReportAttackTree", back_populates="report", cascade="all, delete-orphan")
    tara_results = relationship("ReportTARAResult", back_populates="report", cascade="all, delete-orphan")
    images = relationship("ReportImage", back_populates="report", cascade="all, delete-orphan")
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


class ReportDefinitions(Base):
    """报告相关定义"""
    __tablename__ = "report_definitions"
    
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(String(50), ForeignKey("reports.report_id", ondelete="CASCADE"), nullable=False)
    
    title = Column(String(200), comment="定义标题")
    functional_description = Column(Text, comment="功能描述")
    item_boundary_image = Column(String(500), comment="项目边界图MinIO路径")
    system_architecture_image = Column(String(500), comment="系统架构图MinIO路径")
    software_architecture_image = Column(String(500), comment="软件架构图MinIO路径")
    dataflow_image = Column(String(500), comment="数据流图MinIO路径")
    assumptions = Column(JSON, comment="相关项假设JSON")
    terminology = Column(JSON, comment="术语表JSON")
    
    report = relationship("Report", back_populates="definitions")


class ReportAsset(Base):
    """报告资产"""
    __tablename__ = "report_assets"
    
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(String(50), ForeignKey("reports.report_id", ondelete="CASCADE"), nullable=False)
    
    asset_id = Column(String(50), comment="资产ID")
    name = Column(String(200), comment="资产名称")
    category = Column(String(100), comment="分类")
    remarks = Column(Text, comment="备注")
    authenticity = Column(Boolean, default=False, comment="真实性")
    integrity = Column(Boolean, default=False, comment="完整性")
    non_repudiation = Column(Boolean, default=False, comment="不可抵赖性")
    confidentiality = Column(Boolean, default=False, comment="机密性")
    availability = Column(Boolean, default=False, comment="可用性")
    authorization = Column(Boolean, default=False, comment="权限")
    
    report = relationship("Report", back_populates="assets")


class ReportAttackTree(Base):
    """报告攻击树"""
    __tablename__ = "report_attack_trees"
    
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(String(50), ForeignKey("reports.report_id", ondelete="CASCADE"), nullable=False)
    
    asset_id = Column(String(50), comment="关联资产ID")
    asset_name = Column(String(200), comment="资产名称")
    title = Column(String(300), comment="攻击树标题")
    image = Column(String(500), comment="攻击树图MinIO路径")
    sort_order = Column(Integer, default=0, comment="排序")
    
    report = relationship("Report", back_populates="attack_trees")


class ReportTARAResult(Base):
    """TARA分析结果"""
    __tablename__ = "report_tara_results"
    
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(String(50), ForeignKey("reports.report_id", ondelete="CASCADE"), nullable=False)
    
    # 资产识别
    asset_id = Column(String(50), comment="资产ID")
    asset_name = Column(String(200), comment="资产名称")
    subdomain1 = Column(String(100), comment="子领域一")
    subdomain2 = Column(String(100), comment="子领域二")
    subdomain3 = Column(String(100), comment="子领域三")
    category = Column(String(100), comment="分类")
    
    # 威胁场景
    security_attribute = Column(String(100), comment="安全属性")
    stride_model = Column(String(50), comment="STRIDE模型")
    threat_scenario = Column(Text, comment="潜在威胁场景")
    attack_path = Column(Text, comment="攻击路径")
    wp29_mapping = Column(String(200), comment="WP29威胁映射")
    
    # 威胁分析
    attack_vector = Column(String(50), comment="攻击向量")
    attack_complexity = Column(String(50), comment="攻击复杂度")
    privileges_required = Column(String(50), comment="权限要求")
    user_interaction = Column(String(50), comment="用户交互")
    
    # 影响分析
    safety_impact = Column(String(50), comment="安全影响")
    financial_impact = Column(String(50), comment="经济影响")
    operational_impact = Column(String(50), comment="操作影响")
    privacy_impact = Column(String(50), comment="隐私影响")
    
    # 安全需求
    security_goal = Column(Text, comment="安全目标")
    security_requirement = Column(Text, comment="安全需求")
    
    sort_order = Column(Integer, default=0, comment="排序")
    
    report = relationship("Report", back_populates="tara_results")


class ReportImage(Base):
    """报告图片"""
    __tablename__ = "report_images"
    
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(String(50), ForeignKey("reports.report_id", ondelete="CASCADE"), nullable=False)
    
    image_id = Column(String(50), unique=True, index=True, comment="图片ID")
    image_type = Column(String(50), comment="图片类型")
    original_name = Column(String(255), comment="原始文件名")
    minio_path = Column(String(500), comment="MinIO存储路径")
    minio_bucket = Column(String(100), comment="MinIO桶名")
    file_size = Column(Integer, comment="文件大小")
    content_type = Column(String(100), comment="内容类型")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    
    report = relationship("Report", back_populates="images")


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
