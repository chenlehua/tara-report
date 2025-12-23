"""
API请求和响应模型(Pydantic)
"""
from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field


# ==================== 通用响应模型 ====================
class BaseResponse(BaseModel):
    """基础响应模型"""
    success: bool = Field(description="是否成功")
    message: str = Field(default="", description="消息")


class ErrorResponse(BaseResponse):
    """错误响应模型"""
    success: bool = False
    error_code: Optional[str] = Field(default=None, description="错误码")
    details: Optional[Dict[str, Any]] = Field(default=None, description="详细信息")


# ==================== 报告相关模型 ====================
class CreateReportResponse(BaseResponse):
    """创建报告响应"""
    report_id: str = Field(description="报告ID")


class ReportInfoResponse(BaseModel):
    """报告信息响应"""
    id: str = Field(description="报告ID")
    name: Optional[str] = Field(default=None, description="报告名称")
    status: str = Field(description="报告状态")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")


# ==================== 图片相关模型 ====================
class ImageInfo(BaseModel):
    """图片信息"""
    id: str = Field(description="图片ID")
    image_type: str = Field(description="图片类型")
    original_name: Optional[str] = Field(default=None, description="原始文件名")
    minio_path: str = Field(description="MinIO路径")
    file_size: Optional[int] = Field(default=None, description="文件大小")
    content_type: Optional[str] = Field(default=None, description="内容类型")
    url: Optional[str] = Field(default=None, description="图片URL")
    created_at: datetime = Field(description="创建时间")


class ImageUploadResponse(BaseResponse):
    """图片上传响应"""
    image_id: str = Field(description="图片ID")
    image_url: str = Field(description="图片URL")
    image_type: str = Field(description="图片类型")
    file_size: int = Field(description="文件大小")


class BatchImageUploadResponse(BaseResponse):
    """批量图片上传响应"""
    report_id: str = Field(description="报告ID")
    images: List[ImageInfo] = Field(default_factory=list, description="上传的图片列表")


# ==================== 封面相关模型 ====================
class CoverRequest(BaseModel):
    """封面请求模型"""
    report_title: str = Field(default="威胁分析和风险评估报告", description="报告标题")
    report_title_en: str = Field(default="Threat Analysis And Risk Assessment Report", description="报告英文标题")
    project_name: Optional[str] = Field(default=None, description="项目名称")
    data_level: str = Field(default="秘密", description="数据等级")
    document_number: Optional[str] = Field(default=None, description="文档编号")
    version: str = Field(default="V1.0", description="版本")
    author_date: Optional[str] = Field(default=None, description="编制/日期")
    review_date: Optional[str] = Field(default=None, description="审核/日期")
    sign_date: Optional[str] = Field(default=None, description="会签/日期")
    approve_date: Optional[str] = Field(default=None, description="批准/日期")


class CoverResponse(BaseModel):
    """封面响应模型"""
    id: str = Field(description="封面ID")
    report_id: str = Field(description="报告ID")
    report_title: str = Field(description="报告标题")
    report_title_en: str = Field(description="报告英文标题")
    project_name: Optional[str] = Field(default=None, description="项目名称")
    data_level: str = Field(description="数据等级")
    document_number: Optional[str] = Field(default=None, description="文档编号")
    version: str = Field(description="版本")
    author_date: Optional[str] = Field(default=None, description="编制/日期")
    review_date: Optional[str] = Field(default=None, description="审核/日期")
    sign_date: Optional[str] = Field(default=None, description="会签/日期")
    approve_date: Optional[str] = Field(default=None, description="批准/日期")


# ==================== 项目定义相关模型 ====================
class AssumptionItem(BaseModel):
    """假设条目"""
    id: str = Field(description="假设编号")
    description: str = Field(description="假设描述")


class TerminologyItem(BaseModel):
    """术语条目"""
    abbreviation: str = Field(description="缩写")
    english: str = Field(description="英文全称")
    chinese: str = Field(description="中文名称")


class DefinitionRequest(BaseModel):
    """项目定义请求模型"""
    title: str = Field(default="TARA分析报告 - 相关定义", description="标题")
    functional_description: Optional[str] = Field(default=None, description="功能描述")
    item_boundary_image_id: Optional[str] = Field(default=None, description="项目边界图片ID")
    system_architecture_image_id: Optional[str] = Field(default=None, description="系统架构图片ID")
    software_architecture_image_id: Optional[str] = Field(default=None, description="软件架构图片ID")
    assumptions: List[AssumptionItem] = Field(default_factory=list, description="假设列表")
    terminology: List[TerminologyItem] = Field(default_factory=list, description="术语表")


class DefinitionResponse(BaseModel):
    """项目定义响应模型"""
    id: str = Field(description="定义ID")
    report_id: str = Field(description="报告ID")
    title: str = Field(description="标题")
    functional_description: Optional[str] = Field(default=None, description="功能描述")
    item_boundary_image: Optional[ImageInfo] = Field(default=None, description="项目边界图片")
    system_architecture_image: Optional[ImageInfo] = Field(default=None, description="系统架构图片")
    software_architecture_image: Optional[ImageInfo] = Field(default=None, description="软件架构图片")
    assumptions: List[AssumptionItem] = Field(default_factory=list, description="假设列表")
    terminology: List[TerminologyItem] = Field(default_factory=list, description="术语表")


# ==================== 资产相关模型 ====================
class AssetRequest(BaseModel):
    """资产请求模型"""
    asset_id: str = Field(description="资产ID(业务ID)")
    name: str = Field(description="资产名称")
    category: Optional[str] = Field(default=None, description="分类")
    remarks: Optional[str] = Field(default=None, description="备注")
    authenticity: bool = Field(default=False, description="真实性")
    integrity: bool = Field(default=False, description="完整性")
    non_repudiation: bool = Field(default=False, description="不可抵赖性")
    confidentiality: bool = Field(default=False, description="机密性")
    availability: bool = Field(default=False, description="可用性")
    authorization: bool = Field(default=False, description="权限")


class AssetResponse(BaseModel):
    """资产响应模型"""
    id: str = Field(description="资产数据库ID")
    report_id: str = Field(description="报告ID")
    asset_id: str = Field(description="资产ID(业务ID)")
    name: str = Field(description="资产名称")
    category: Optional[str] = Field(default=None, description="分类")
    remarks: Optional[str] = Field(default=None, description="备注")
    authenticity: bool = Field(description="真实性")
    integrity: bool = Field(description="完整性")
    non_repudiation: bool = Field(description="不可抵赖性")
    confidentiality: bool = Field(description="机密性")
    availability: bool = Field(description="可用性")
    authorization: bool = Field(description="权限")
    dataflow_image: Optional[ImageInfo] = Field(default=None, description="数据流图片")


class AssetsListResponse(BaseModel):
    """资产列表响应模型"""
    report_id: str = Field(description="报告ID")
    title: str = Field(default="资产列表 Asset List", description="标题")
    dataflow_image: Optional[ImageInfo] = Field(default=None, description="数据流图片")
    assets: List[AssetResponse] = Field(default_factory=list, description="资产列表")


# ==================== 攻击树相关模型 ====================
class AttackTreeRequest(BaseModel):
    """攻击树请求模型"""
    asset_id: Optional[str] = Field(default=None, description="关联资产ID")
    asset_name: Optional[str] = Field(default=None, description="资产名称")
    title: Optional[str] = Field(default=None, description="攻击树标题")
    description: Optional[str] = Field(default=None, description="攻击树描述")


class AttackTreeResponse(BaseModel):
    """攻击树响应模型"""
    id: str = Field(description="攻击树ID")
    report_id: str = Field(description="报告ID")
    asset_id: Optional[str] = Field(default=None, description="关联资产ID")
    asset_name: Optional[str] = Field(default=None, description="资产名称")
    title: Optional[str] = Field(default=None, description="攻击树标题")
    description: Optional[str] = Field(default=None, description="攻击树描述")
    image: Optional[ImageInfo] = Field(default=None, description="攻击树图片")


class AttackTreesListResponse(BaseModel):
    """攻击树列表响应模型"""
    report_id: str = Field(description="报告ID")
    attack_trees: List[AttackTreeResponse] = Field(default_factory=list, description="攻击树列表")


# ==================== TARA结果相关模型 ====================
class TaraResultRequest(BaseModel):
    """TARA结果请求模型"""
    asset_id: str = Field(description="资产ID")
    asset_name: str = Field(description="资产名称")
    subdomain1: Optional[str] = Field(default=None, description="子域1")
    subdomain2: Optional[str] = Field(default=None, description="子域2")
    subdomain3: Optional[str] = Field(default=None, description="子域3")
    category: Optional[str] = Field(default=None, description="分类")
    security_attribute: Optional[str] = Field(default=None, description="安全属性")
    stride_model: Optional[str] = Field(default=None, description="STRIDE模型")
    threat_scenario: Optional[str] = Field(default=None, description="威胁场景")
    attack_path: Optional[str] = Field(default=None, description="攻击路径")
    wp29_mapping: Optional[str] = Field(default=None, description="WP29映射")
    attack_vector: str = Field(default="本地", description="攻击向量")
    attack_complexity: str = Field(default="低", description="攻击复杂度")
    privileges_required: str = Field(default="低", description="权限要求")
    user_interaction: str = Field(default="不需要", description="用户交互")
    safety_impact: str = Field(default="中等的", description="安全影响")
    financial_impact: str = Field(default="中等的", description="经济影响")
    operational_impact: str = Field(default="中等的", description="操作影响")
    privacy_impact: str = Field(default="可忽略不计的", description="隐私影响")
    security_requirement: Optional[str] = Field(default=None, description="安全需求")


class TaraResultResponse(BaseModel):
    """TARA结果响应模型"""
    id: str = Field(description="结果ID")
    report_id: str = Field(description="报告ID")
    asset_id: str = Field(description="资产ID")
    asset_name: str = Field(description="资产名称")
    subdomain1: Optional[str] = Field(default=None, description="子域1")
    subdomain2: Optional[str] = Field(default=None, description="子域2")
    subdomain3: Optional[str] = Field(default=None, description="子域3")
    category: Optional[str] = Field(default=None, description="分类")
    security_attribute: Optional[str] = Field(default=None, description="安全属性")
    stride_model: Optional[str] = Field(default=None, description="STRIDE模型")
    threat_scenario: Optional[str] = Field(default=None, description="威胁场景")
    attack_path: Optional[str] = Field(default=None, description="攻击路径")
    wp29_mapping: Optional[str] = Field(default=None, description="WP29映射")
    attack_vector: str = Field(description="攻击向量")
    attack_complexity: str = Field(description="攻击复杂度")
    privileges_required: str = Field(description="权限要求")
    user_interaction: str = Field(description="用户交互")
    safety_impact: str = Field(description="安全影响")
    financial_impact: str = Field(description="经济影响")
    operational_impact: str = Field(description="操作影响")
    privacy_impact: str = Field(description="隐私影响")
    security_requirement: Optional[str] = Field(default=None, description="安全需求")


class TaraResultsListResponse(BaseModel):
    """TARA结果列表响应模型"""
    report_id: str = Field(description="报告ID")
    title: str = Field(default="TARA分析结果 TARA Analysis Results", description="标题")
    results: List[TaraResultResponse] = Field(default_factory=list, description="结果列表")


# ==================== 完整报告数据模型 ====================
class FullReportDataResponse(BaseModel):
    """完整报告数据响应模型(用于报告生成)"""
    report_id: str = Field(description="报告ID")
    cover: Optional[CoverResponse] = Field(default=None, description="封面数据")
    definitions: Optional[DefinitionResponse] = Field(default=None, description="项目定义")
    assets: Optional[AssetsListResponse] = Field(default=None, description="资产列表")
    attack_trees: Optional[AttackTreesListResponse] = Field(default=None, description="攻击树列表")
    tara_results: Optional[TaraResultsListResponse] = Field(default=None, description="TARA结果列表")


# ==================== JSON上传解析模型 ====================
class JsonUploadRequest(BaseModel):
    """JSON上传解析请求"""
    cover: Optional[CoverRequest] = Field(default=None, description="封面数据")
    definitions: Optional[DefinitionRequest] = Field(default=None, description="项目定义")
    assets: Optional[Dict[str, Any]] = Field(default=None, description="资产数据")
    attack_trees: Optional[Dict[str, Any]] = Field(default=None, description="攻击树数据")
    tara_results: Optional[Dict[str, Any]] = Field(default=None, description="TARA结果数据")


class JsonUploadResponse(BaseResponse):
    """JSON上传解析响应"""
    report_id: str = Field(description="报告ID")
    parsed_data: Dict[str, Any] = Field(default_factory=dict, description="解析后的数据摘要")
