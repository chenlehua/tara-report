"""
数据库模型定义
包含资产表、项目定义表、封面表、攻击树表、TARA分析结果表
"""
import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, String, Text, Boolean, Integer, DateTime, 
    ForeignKey, JSON, Enum as SQLEnum, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import LONGTEXT
import enum

Base = declarative_base()


def generate_uuid():
    """生成UUID"""
    return str(uuid.uuid4())


def generate_report_id():
    """生成报告ID"""
    return f"RPT-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"


def generate_image_id():
    """生成图片ID"""
    return f"IMG-{uuid.uuid4().hex[:12]}"


class ImageType(str, enum.Enum):
    """图片类型枚举"""
    ITEM_BOUNDARY = "item_boundary"
    SYSTEM_ARCHITECTURE = "system_architecture"
    SOFTWARE_ARCHITECTURE = "software_architecture"
    DATAFLOW = "dataflow"
    ATTACK_TREE = "attack_tree"
    OTHER = "other"


class ReportStatus(str, enum.Enum):
    """报告状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ==================== 报告主表 ====================
class Report(Base):
    """报告主表"""
    __tablename__ = "reports"
    
    id = Column(String(50), primary_key=True, default=generate_report_id)
    name = Column(String(255), nullable=True, comment="报告名称")
    status = Column(SQLEnum(ReportStatus), default=ReportStatus.PENDING, comment="报告状态")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关联关系
    cover = relationship("Cover", back_populates="report", uselist=False, cascade="all, delete-orphan")
    definition = relationship("Definition", back_populates="report", uselist=False, cascade="all, delete-orphan")
    assets = relationship("Asset", back_populates="report", cascade="all, delete-orphan")
    attack_trees = relationship("AttackTree", back_populates="report", cascade="all, delete-orphan")
    tara_results = relationship("TaraResult", back_populates="report", cascade="all, delete-orphan")
    images = relationship("Image", back_populates="report", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_report_status', 'status'),
        Index('idx_report_created_at', 'created_at'),
    )


# ==================== 图片表 ====================
class Image(Base):
    """图片表"""
    __tablename__ = "images"
    
    id = Column(String(50), primary_key=True, default=generate_image_id)
    report_id = Column(String(50), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, comment="报告ID")
    image_type = Column(SQLEnum(ImageType), nullable=False, comment="图片类型")
    original_name = Column(String(255), nullable=True, comment="原始文件名")
    minio_path = Column(String(500), nullable=False, comment="MinIO存储路径")
    minio_bucket = Column(String(100), nullable=False, comment="MinIO桶名")
    file_size = Column(Integer, nullable=True, comment="文件大小(字节)")
    content_type = Column(String(100), nullable=True, comment="内容类型")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    
    # 关联关系
    report = relationship("Report", back_populates="images")
    
    # 攻击树关联(可选)
    attack_tree_id = Column(String(50), ForeignKey("attack_trees.id", ondelete="SET NULL"), nullable=True)
    attack_tree = relationship("AttackTree", back_populates="image", foreign_keys=[attack_tree_id])
    
    __table_args__ = (
        Index('idx_image_report_id', 'report_id'),
        Index('idx_image_type', 'image_type'),
    )


# ==================== 封面表 ====================
class Cover(Base):
    """封面表"""
    __tablename__ = "covers"
    
    id = Column(String(50), primary_key=True, default=generate_uuid)
    report_id = Column(String(50), ForeignKey("reports.id", ondelete="CASCADE"), unique=True, nullable=False, comment="报告ID")
    
    report_title = Column(String(255), default="威胁分析和风险评估报告", comment="报告标题")
    report_title_en = Column(String(255), default="Threat Analysis And Risk Assessment Report", comment="报告英文标题")
    project_name = Column(String(255), nullable=True, comment="项目名称")
    data_level = Column(String(50), default="秘密", comment="数据等级")
    document_number = Column(String(100), nullable=True, comment="文档编号")
    version = Column(String(50), default="V1.0", comment="版本")
    author_date = Column(String(100), nullable=True, comment="编制/日期")
    review_date = Column(String(100), nullable=True, comment="审核/日期")
    sign_date = Column(String(100), nullable=True, comment="会签/日期")
    approve_date = Column(String(100), nullable=True, comment="批准/日期")
    
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关联关系
    report = relationship("Report", back_populates="cover")


# ==================== 项目定义表 ====================
class Definition(Base):
    """项目定义表"""
    __tablename__ = "definitions"
    
    id = Column(String(50), primary_key=True, default=generate_uuid)
    report_id = Column(String(50), ForeignKey("reports.id", ondelete="CASCADE"), unique=True, nullable=False, comment="报告ID")
    
    title = Column(String(255), default="TARA分析报告 - 相关定义", comment="标题")
    functional_description = Column(LONGTEXT, nullable=True, comment="功能描述")
    
    # 图片ID引用
    item_boundary_image_id = Column(String(50), nullable=True, comment="项目边界图片ID")
    system_architecture_image_id = Column(String(50), nullable=True, comment="系统架构图片ID")
    software_architecture_image_id = Column(String(50), nullable=True, comment="软件架构图片ID")
    
    # 假设和术语以JSON格式存储
    assumptions = Column(JSON, nullable=True, comment="假设列表 [{id, description}]")
    terminology = Column(JSON, nullable=True, comment="术语表 [{abbreviation, english, chinese}]")
    
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关联关系
    report = relationship("Report", back_populates="definition")


# ==================== 资产表 ====================
class Asset(Base):
    """资产表"""
    __tablename__ = "assets"
    
    id = Column(String(50), primary_key=True, default=generate_uuid)
    report_id = Column(String(50), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, comment="报告ID")
    
    asset_id = Column(String(50), nullable=False, comment="资产ID(业务ID)")
    name = Column(String(255), nullable=False, comment="资产名称")
    category = Column(String(100), nullable=True, comment="分类")
    remarks = Column(Text, nullable=True, comment="备注")
    
    # 安全属性
    authenticity = Column(Boolean, default=False, comment="真实性")
    integrity = Column(Boolean, default=False, comment="完整性")
    non_repudiation = Column(Boolean, default=False, comment="不可抵赖性")
    confidentiality = Column(Boolean, default=False, comment="机密性")
    availability = Column(Boolean, default=False, comment="可用性")
    authorization = Column(Boolean, default=False, comment="权限")
    
    # 数据流图片ID(资产级别可以有专属数据流图)
    dataflow_image_id = Column(String(50), nullable=True, comment="数据流图片ID")
    
    sort_order = Column(Integer, default=0, comment="排序顺序")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关联关系
    report = relationship("Report", back_populates="assets")
    
    __table_args__ = (
        Index('idx_asset_report_id', 'report_id'),
        Index('idx_asset_asset_id', 'asset_id'),
    )


# ==================== 资产数据流图片关联表(用于存储报告级别的数据流图) ====================
class AssetDataflow(Base):
    """资产数据流配置表(报告级别)"""
    __tablename__ = "asset_dataflows"
    
    id = Column(String(50), primary_key=True, default=generate_uuid)
    report_id = Column(String(50), ForeignKey("reports.id", ondelete="CASCADE"), unique=True, nullable=False, comment="报告ID")
    title = Column(String(255), default="资产列表 Asset List", comment="标题")
    dataflow_image_id = Column(String(50), nullable=True, comment="数据流图片ID")
    
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")


# ==================== 攻击树表 ====================
class AttackTree(Base):
    """攻击树表"""
    __tablename__ = "attack_trees"
    
    id = Column(String(50), primary_key=True, default=generate_uuid)
    report_id = Column(String(50), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, comment="报告ID")
    
    asset_id = Column(String(50), nullable=True, comment="关联资产ID")
    asset_name = Column(String(255), nullable=True, comment="资产名称")
    title = Column(String(255), nullable=True, comment="攻击树标题")
    description = Column(Text, nullable=True, comment="攻击树描述")
    
    # 攻击树图片通过Image表的attack_tree_id关联
    
    sort_order = Column(Integer, default=0, comment="排序顺序")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关联关系
    report = relationship("Report", back_populates="attack_trees")
    image = relationship("Image", back_populates="attack_tree", uselist=False, 
                        foreign_keys="Image.attack_tree_id")
    
    __table_args__ = (
        Index('idx_attack_tree_report_id', 'report_id'),
    )


# ==================== TARA分析结果表 ====================
class TaraResult(Base):
    """TARA分析结果表"""
    __tablename__ = "tara_results"
    
    id = Column(String(50), primary_key=True, default=generate_uuid)
    report_id = Column(String(50), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, comment="报告ID")
    
    # 资产信息
    asset_id = Column(String(50), nullable=False, comment="资产ID")
    asset_name = Column(String(255), nullable=False, comment="资产名称")
    
    # 子域
    subdomain1 = Column(String(255), nullable=True, comment="子域1")
    subdomain2 = Column(String(255), nullable=True, comment="子域2")
    subdomain3 = Column(String(255), nullable=True, comment="子域3")
    
    # 分类和安全属性
    category = Column(String(100), nullable=True, comment="分类")
    security_attribute = Column(String(100), nullable=True, comment="安全属性")
    stride_model = Column(String(100), nullable=True, comment="STRIDE模型")
    
    # 威胁场景和攻击路径
    threat_scenario = Column(Text, nullable=True, comment="威胁场景")
    attack_path = Column(Text, nullable=True, comment="攻击路径")
    wp29_mapping = Column(String(255), nullable=True, comment="WP29映射")
    
    # CVSS评估
    attack_vector = Column(String(50), default="本地", comment="攻击向量")
    attack_complexity = Column(String(50), default="低", comment="攻击复杂度")
    privileges_required = Column(String(50), default="低", comment="权限要求")
    user_interaction = Column(String(50), default="不需要", comment="用户交互")
    
    # 影响评估
    safety_impact = Column(String(50), default="中等的", comment="安全影响")
    financial_impact = Column(String(50), default="中等的", comment="经济影响")
    operational_impact = Column(String(50), default="中等的", comment="操作影响")
    privacy_impact = Column(String(50), default="可忽略不计的", comment="隐私影响")
    
    # 安全需求
    security_requirement = Column(Text, nullable=True, comment="安全需求")
    
    sort_order = Column(Integer, default=0, comment="排序顺序")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关联关系
    report = relationship("Report", back_populates="tara_results")
    
    __table_args__ = (
        Index('idx_tara_result_report_id', 'report_id'),
        Index('idx_tara_result_asset_id', 'asset_id'),
    )
