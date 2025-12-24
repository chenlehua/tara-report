"""
TARA报告生成API服务
提供TARA Excel报告的生成、预览和下载功能
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.common.config import settings
from app.api.v1.router import api_router

# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册API路由
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    """API根路径"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "api_docs": "/docs",
        "api_v1": settings.API_V1_PREFIX
    }


# ==================== 启动函数 ====================
def run_server():
    """启动服务器"""
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )


if __name__ == "__main__":
    run_server()
