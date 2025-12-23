"""
存储模块
"""
from .minio_service import (
    MinioStorageService,
    get_minio_storage,
    init_minio_storage
)

__all__ = [
    "MinioStorageService",
    "get_minio_storage",
    "init_minio_storage"
]
