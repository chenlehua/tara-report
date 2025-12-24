"""
Report Service database models
报告服务专用数据模型
使用 rs_ 前缀的表，与 data-service 的表分离
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.common.database.mysql import Base


class RSReport(Base):
    """
    报告主表
    用于报告列表展示和基本信息管理
    """
    __tablename__ = "rs_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(String(50), unique=True, index=True, nullable=False, comment="报告ID")
    project_name = Column(String(200), comment="项目名称")
    report_title = Column(String(200), comment="报告标题")
    report_title_en = Column(String(200), comment="报告英文标题")
    data_level = Column(String(50), comment="数据等级")
    document_number = Column(String(100), comment="文档编号")
    version = Column(String(50), comment="版本号")
    status = Column(String(20), default="pending", comment="状态: pending, processing, completed, failed")
    source_type = Column(String(20), default="upload", comment="来源类型: upload, sync")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    
    # Relationships
    cover = relationship("RSReportCover", back_populates="report", uselist=False, cascade="all, delete-orphan")
    definitions = relationship("RSReportDefinitions", back_populates="report", uselist=False, cascade="all, delete-orphan")
    assets = relationship("RSReportAsset", back_populates="report", cascade="all, delete-orphan")
    attack_trees = relationship("RSReportAttackTree", back_populates="report", cascade="all, delete-orphan")
    tara_results = relationship("RSReportTARAResult", back_populates="report", cascade="all, delete-orphan")
    images = relationship("RSReportImage", back_populates="report", cascade="all, delete-orphan")
    statistics = relationship("RSReportStatistics", back_populates="report", uselist=False, cascade="all, delete-orphan")
    generated_files = relationship("RSGeneratedFile", back_populates="report", cascade="all, delete-orphan")
    generation_history = relationship("RSGenerationHistory", back_populates="report", cascade="all, delete-orphan")


class RSReportCover(Base):
    """
    报告封面信息表
    存储报告封面的详细信息
    """
    __tablename__ = "rs_report_covers"
    
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(String(50), ForeignKey("rs_reports.report_id", ondelete="CASCADE"), nullable=False)
    
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
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    
    report = relationship("RSReport", back_populates="cover")


class RSReportDefinitions(Base):
    """
    报告定义信息表
    存储报告相关定义，包括功能描述、架构图路径、假设条件和术语表
    """
    __tablename__ = "rs_report_definitions"
    
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(String(50), ForeignKey("rs_reports.report_id", ondelete="CASCADE"), nullable=False)
    
    title = Column(String(200), comment="定义标题/系统名称")
    functional_description = Column(Text, comment="功能描述")
    item_boundary_image = Column(String(500), comment="项目边界图MinIO路径")
    system_architecture_image = Column(String(500), comment="系统架构图MinIO路径")
    software_architecture_image = Column(String(500), comment="软件架构图MinIO路径")
    dataflow_image = Column(String(500), comment="数据流图MinIO路径")
    assumptions = Column(JSON, comment="假设条件JSON数组")
    terminology = Column(JSON, comment="术语表JSON数组")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    
    report = relationship("RSReport", back_populates="definitions")


class RSReportAsset(Base):
    """
    报告资产表
    存储报告中的资产列表及其安全属性
    """
    __tablename__ = "rs_report_assets"
    
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(String(50), ForeignKey("rs_reports.report_id", ondelete="CASCADE"), nullable=False)
    
    asset_id = Column(String(50), comment="资产ID")
    name = Column(String(200), comment="资产名称")
    category = Column(String(100), comment="资产分类")
    remarks = Column(Text, comment="备注说明")
    authenticity = Column(Boolean, default=False, comment="真实性")
    integrity = Column(Boolean, default=False, comment="完整性")
    non_repudiation = Column(Boolean, default=False, comment="不可否认性")
    confidentiality = Column(Boolean, default=False, comment="机密性")
    availability = Column(Boolean, default=False, comment="可用性")
    authorization = Column(Boolean, default=False, comment="授权性")
    sort_order = Column(Integer, default=0, comment="排序顺序")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    
    report = relationship("RSReport", back_populates="assets")


class RSReportAttackTree(Base):
    """
    报告攻击树表
    存储报告中的攻击树信息
    """
    __tablename__ = "rs_report_attack_trees"
    
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(String(50), ForeignKey("rs_reports.report_id", ondelete="CASCADE"), nullable=False)
    
    asset_id = Column(String(50), comment="关联资产ID")
    asset_name = Column(String(200), comment="资产名称")
    title = Column(String(300), comment="攻击树标题")
    image = Column(String(500), comment="攻击树图MinIO路径")
    sort_order = Column(Integer, default=0, comment="排序顺序")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    
    report = relationship("RSReport", back_populates="attack_trees")


class RSReportTARAResult(Base):
    """
    TARA分析结果表
    存储威胁分析和风险评估结果
    """
    __tablename__ = "rs_report_tara_results"
    
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(String(50), ForeignKey("rs_reports.report_id", ondelete="CASCADE"), nullable=False)
    
    # 资产识别
    asset_id = Column(String(50), comment="资产ID")
    asset_name = Column(String(200), comment="资产名称")
    subdomain1 = Column(String(100), comment="子领域一（系统级）")
    subdomain2 = Column(String(100), comment="子领域二（模块级）")
    subdomain3 = Column(String(100), comment="子领域三（组件级）")
    category = Column(String(100), comment="资产分类")
    
    # 威胁场景
    security_attribute = Column(String(100), comment="安全属性")
    stride_model = Column(String(50), comment="STRIDE威胁模型分类")
    threat_scenario = Column(Text, comment="潜在威胁场景描述")
    attack_path = Column(Text, comment="攻击路径描述")
    wp29_mapping = Column(String(200), comment="WP.29法规条款映射")
    
    # 威胁分析（CVSS相关）
    attack_vector = Column(String(50), comment="攻击向量")
    attack_complexity = Column(String(50), comment="攻击复杂度")
    privileges_required = Column(String(50), comment="所需权限")
    user_interaction = Column(String(50), comment="用户交互")
    
    # 影响分析
    safety_impact = Column(String(50), comment="安全影响")
    financial_impact = Column(String(50), comment="财务影响")
    operational_impact = Column(String(50), comment="运营影响")
    privacy_impact = Column(String(50), comment="隐私影响")
    
    # 安全需求
    security_goal = Column(Text, comment="安全目标")
    security_requirement = Column(Text, comment="安全需求/对策")
    
    sort_order = Column(Integer, default=0, comment="排序顺序")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    
    report = relationship("RSReport", back_populates="tara_results")


class RSReportImage(Base):
    """
    报告图片信息表
    存储报告关联的图片信息
    """
    __tablename__ = "rs_report_images"
    
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(String(50), ForeignKey("rs_reports.report_id", ondelete="CASCADE"), nullable=False)
    
    image_id = Column(String(50), unique=True, index=True, comment="图片ID")
    image_type = Column(String(50), comment="图片类型")
    original_name = Column(String(255), comment="原始文件名")
    minio_path = Column(String(500), comment="MinIO存储路径")
    minio_bucket = Column(String(100), comment="MinIO桶名")
    file_size = Column(Integer, comment="文件大小（字节）")
    content_type = Column(String(100), comment="MIME类型")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    
    report = relationship("RSReport", back_populates="images")


class RSReportStatistics(Base):
    """
    报告统计信息表
    缓存报告的统计信息，用于快速展示报告列表
    """
    __tablename__ = "rs_report_statistics"
    
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(String(50), ForeignKey("rs_reports.report_id", ondelete="CASCADE"), nullable=False, unique=True)
    
    assets_count = Column(Integer, default=0, comment="资产数量")
    threats_count = Column(Integer, default=0, comment="威胁数量")
    high_risk_count = Column(Integer, default=0, comment="高风险数量")
    measures_count = Column(Integer, default=0, comment="安全措施数量")
    attack_trees_count = Column(Integer, default=0, comment="攻击树数量")
    images_count = Column(Integer, default=0, comment="图片数量")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    
    report = relationship("RSReport", back_populates="statistics")


class RSGeneratedFile(Base):
    """
    生成报告文件表
    存储已生成的报告文件信息（Excel/PDF）
    """
    __tablename__ = "rs_generated_files"
    
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(String(50), ForeignKey("rs_reports.report_id", ondelete="CASCADE"), nullable=False)
    
    file_type = Column(String(20), comment="文件类型: xlsx, pdf")
    file_name = Column(String(255), comment="文件名")
    minio_path = Column(String(500), comment="MinIO存储路径")
    minio_bucket = Column(String(100), comment="MinIO桶名")
    file_size = Column(Integer, comment="文件大小（字节）")
    generated_at = Column(DateTime, default=datetime.now, comment="生成时间")
    
    report = relationship("RSReport", back_populates="generated_files")


class RSGenerationHistory(Base):
    """
    报告生成历史表
    记录报告生成的历史记录，用于审计和追踪
    """
    __tablename__ = "rs_generation_history"
    
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(String(50), ForeignKey("rs_reports.report_id", ondelete="CASCADE"), nullable=False)
    
    file_type = Column(String(20), comment="文件类型: xlsx, pdf")
    status = Column(String(20), comment="生成状态: pending, processing, success, failed")
    error_message = Column(Text, comment="错误信息")
    file_size = Column(Integer, comment="文件大小（字节）")
    generation_time_ms = Column(Integer, comment="生成耗时（毫秒）")
    started_at = Column(DateTime, comment="开始时间")
    completed_at = Column(DateTime, comment="完成时间")
    created_at = Column(DateTime, default=datetime.now, comment="记录创建时间")
    
    report = relationship("RSReport", back_populates="generation_history")


# ================================================================
# Backward Compatibility Aliases
# 为了向后兼容，保留原有类名作为别名
# ================================================================

# Report aliases
Report = RSReport
ReportCover = RSReportCover
ReportDefinitions = RSReportDefinitions
ReportAsset = RSReportAsset
ReportAttackTree = RSReportAttackTree
ReportTARAResult = RSReportTARAResult
ReportImage = RSReportImage
GeneratedReport = RSGeneratedFile
