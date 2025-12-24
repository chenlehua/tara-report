"""
API v1 路由器
"""
from fastapi import APIRouter

from app.api.v1.endpoints import images, reports, upload, health

api_router = APIRouter()

# 注册各模块路由
api_router.include_router(images.router, prefix="/images", tags=["images"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(upload.router, prefix="/upload", tags=["upload"])
api_router.include_router(health.router, prefix="/health", tags=["health"])
