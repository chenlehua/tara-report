"""
API v1 路由器
"""
from fastapi import APIRouter

from app.api.v1.endpoints import health, images, reports, upload

api_router = APIRouter()

# 健康检查
api_router.include_router(health.router, tags=["health"])

# 图片管理
api_router.include_router(images.router, tags=["images"])

# 报告管理
api_router.include_router(reports.router, tags=["reports"])

# 批量上传
api_router.include_router(upload.router, tags=["upload"])
