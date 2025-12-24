"""
API v1 router
"""
from fastapi import APIRouter

from app.api.v1.endpoints import health, reports

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router, tags=["health"])
api_router.include_router(reports.router, tags=["reports"])
