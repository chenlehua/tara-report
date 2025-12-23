"""
API模型模块
"""
from .schemas import (
    # Base
    BaseResponse,
    ErrorResponse,
    # Report
    CreateReportResponse,
    ReportInfoResponse,
    # Image
    ImageInfo,
    ImageUploadResponse,
    BatchImageUploadResponse,
    # Cover
    CoverRequest,
    CoverResponse,
    # Definition
    AssumptionItem,
    TerminologyItem,
    DefinitionRequest,
    DefinitionResponse,
    # Asset
    AssetRequest,
    AssetResponse,
    AssetsListResponse,
    # AttackTree
    AttackTreeRequest,
    AttackTreeResponse,
    AttackTreesListResponse,
    # TaraResult
    TaraResultRequest,
    TaraResultResponse,
    TaraResultsListResponse,
    # Full Report
    FullReportDataResponse,
    # JSON Upload
    JsonUploadRequest,
    JsonUploadResponse
)

__all__ = [
    "BaseResponse",
    "ErrorResponse",
    "CreateReportResponse",
    "ReportInfoResponse",
    "ImageInfo",
    "ImageUploadResponse",
    "BatchImageUploadResponse",
    "CoverRequest",
    "CoverResponse",
    "AssumptionItem",
    "TerminologyItem",
    "DefinitionRequest",
    "DefinitionResponse",
    "AssetRequest",
    "AssetResponse",
    "AssetsListResponse",
    "AttackTreeRequest",
    "AttackTreeResponse",
    "AttackTreesListResponse",
    "TaraResultRequest",
    "TaraResultResponse",
    "TaraResultsListResponse",
    "FullReportDataResponse",
    "JsonUploadRequest",
    "JsonUploadResponse"
]
