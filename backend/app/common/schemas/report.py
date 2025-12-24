"""
Pydantic Schema 定义
"""
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
from datetime import datetime


# ==================== 封面数据模型 ====================
class CoverData(BaseModel):
    """封面数据"""
    report_title: str = Field(default="威胁分析和风险评估报告", description="报告标题")
    report_title_en: str = Field(default="Threat Analysis And Risk Assessment Report", description="报告英文标题")
    project_name: str = Field(default="", description="项目名称")
    data_level: str = Field(default="秘密", description="数据等级")
    document_number: str = Field(default="", description="文档编号")
    version: str = Field(default="V1.0", description="版本")
    author_date: str = Field(default="", description="编制/日期")
    review_date: str = Field(default="", description="审核/日期")
    sign_date: str = Field(default="", description="会签/日期")
    approve_date: str = Field(default="", description="批准/日期")


# ==================== 相关定义数据模型 ====================
class Assumption(BaseModel):
    """假设条目"""
    id: str = Field(description="假设编号")
    description: str = Field(description="假设描述")


class Terminology(BaseModel):
    """术语条目"""
    abbreviation: str = Field(description="缩写")
    english: str = Field(description="英文全称")
    chinese: str = Field(description="中文名称")


class DefinitionsData(BaseModel):
    """相关定义数据"""
    title: str = Field(default="TARA分析报告 - 相关定义", description="标题")
    functional_description: str = Field(default="", description="功能描述")
    item_boundary_image: Optional[str] = Field(default=None, description="项目边界图片路径")
    system_architecture_image: Optional[str] = Field(default=None, description="系统架构图片路径")
    software_architecture_image: Optional[str] = Field(default=None, description="软件架构图片路径")
    assumptions: List[Assumption] = Field(default_factory=list, description="假设列表")
    terminology: List[Terminology] = Field(default_factory=list, description="术语表")


# ==================== 资产列表数据模型 ====================
class Asset(BaseModel):
    """资产条目"""
    id: str = Field(description="资产ID")
    name: str = Field(description="资产名称")
    category: str = Field(description="分类")
    remarks: str = Field(default="", description="备注")
    authenticity: bool = Field(default=False, description="真实性")
    integrity: bool = Field(default=False, description="完整性")
    non_repudiation: bool = Field(default=False, description="不可抵赖性")
    confidentiality: bool = Field(default=False, description="机密性")
    availability: bool = Field(default=False, description="可用性")
    authorization: bool = Field(default=False, description="权限")


class AssetsData(BaseModel):
    """资产列表数据"""
    title: str = Field(default="资产列表 Asset List", description="标题")
    dataflow_image: Optional[str] = Field(default=None, description="数据流图片路径")
    assets: List[Asset] = Field(default_factory=list, description="资产列表")


# ==================== 攻击树数据模型 ====================
class AttackTree(BaseModel):
    """攻击树条目"""
    asset_id: str = Field(default="", description="资产ID")
    asset_name: str = Field(default="", description="资产名称")
    title: str = Field(default="", description="攻击树标题")
    image: Optional[str] = Field(default=None, description="攻击树图片路径")
    image_url: Optional[str] = Field(default=None, description="攻击树图片URL")


class AttackTreesData(BaseModel):
    """攻击树数据"""
    title: str = Field(default="攻击树分析 Attack Tree Analysis", description="标题")
    attack_trees: List[AttackTree] = Field(default_factory=list, description="攻击树列表")


# ==================== TARA结果数据模型 ====================
class TARAResult(BaseModel):
    """TARA分析结果条目"""
    asset_id: str = Field(description="资产ID")
    asset_name: str = Field(description="资产名称")
    subdomain1: str = Field(default="", description="子域1")
    subdomain2: str = Field(default="", description="子域2")
    subdomain3: str = Field(default="", description="子域3")
    category: str = Field(description="分类")
    security_attribute: str = Field(description="安全属性")
    stride_model: str = Field(description="STRIDE模型")
    threat_scenario: str = Field(description="威胁场景")
    attack_path: str = Field(description="攻击路径")
    wp29_mapping: str = Field(default="", description="WP29映射")
    attack_vector: str = Field(default="本地", description="攻击向量")
    attack_complexity: str = Field(default="低", description="攻击复杂度")
    privileges_required: str = Field(default="低", description="权限要求")
    user_interaction: str = Field(default="不需要", description="用户交互")
    safety_impact: str = Field(default="中等的", description="安全影响")
    financial_impact: str = Field(default="中等的", description="经济影响")
    operational_impact: str = Field(default="中等的", description="操作影响")
    privacy_impact: str = Field(default="可忽略不计的", description="隐私影响")
    security_requirement: str = Field(default="", description="安全需求")


class TARAResultsData(BaseModel):
    """TARA分析结果数据"""
    title: str = Field(default="TARA分析结果 TARA Analysis Results", description="标题")
    results: List[TARAResult] = Field(default_factory=list, description="TARA结果列表")


# ==================== 完整报告数据模型 ====================
class TARAReportData(BaseModel):
    """完整的TARA报告数据"""
    cover: CoverData = Field(default_factory=CoverData, description="封面数据")
    definitions: DefinitionsData = Field(default_factory=DefinitionsData, description="相关定义数据")
    assets: AssetsData = Field(default_factory=AssetsData, description="资产列表数据")
    attack_trees: AttackTreesData = Field(default_factory=AttackTreesData, description="攻击树数据")
    tara_results: TARAResultsData = Field(default_factory=TARAResultsData, description="TARA分析结果数据")


# ==================== API响应模型 ====================
class GenerateReportResponse(BaseModel):
    """生成报告响应"""
    success: bool = Field(description="是否成功")
    message: str = Field(description="消息")
    report_id: Optional[str] = Field(default=None, description="报告ID")
    download_url: Optional[str] = Field(default=None, description="下载URL")
    preview_data: Optional[Dict[str, Any]] = Field(default=None, description="预览数据")


class ReportInfo(BaseModel):
    """报告信息"""
    id: str = Field(description="报告ID")
    name: str = Field(description="报告名称")
    project_name: str = Field(description="项目名称")
    created_at: datetime = Field(description="创建时间")
    status: str = Field(default="completed", description="状态")
    file_path: Optional[str] = Field(default=None, description="文件路径")
    statistics: Dict[str, int] = Field(default_factory=dict, description="统计信息")
    images: Dict[str, Optional[str]] = Field(default_factory=dict, description="图片信息")


class ReportListResponse(BaseModel):
    """报告列表响应"""
    success: bool = Field(description="是否成功")
    reports: List[ReportInfo] = Field(default_factory=list, description="报告列表")
    total: int = Field(default=0, description="总数")


class ImageUploadResponse(BaseModel):
    """图片上传响应"""
    success: bool = Field(description="是否成功")
    message: str = Field(description="消息")
    image_id: Optional[str] = Field(default=None, description="图片ID")
    image_url: Optional[str] = Field(default=None, description="图片URL")
    image_type: Optional[str] = Field(default=None, description="图片类型")
