"""
API v1 路由聚合
"""
from fastapi import APIRouter

from .endpoints import health, image, report

api_router = APIRouter()

# 注册各模块路由
api_router.include_router(health.router, tags=["health"])
api_router.include_router(image.router, tags=["images"])
api_router.include_router(report.router, tags=["reports"])
