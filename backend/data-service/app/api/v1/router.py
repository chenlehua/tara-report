"""
API v1 router
"""
from fastapi import APIRouter

from app.api.v1.endpoints import health, images, reports, upload

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router, tags=["health"])
api_router.include_router(images.router, tags=["images"])
api_router.include_router(reports.router, tags=["reports"])
api_router.include_router(upload.router, tags=["upload"])
