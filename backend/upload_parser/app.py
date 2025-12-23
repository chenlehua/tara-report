"""
上传解析模块主应用
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import init_db, close_db
from .storage import init_minio_storage
from .api import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    print("Initializing database...")
    await init_db()
    print("Database initialized.")
    
    print("Initializing MinIO storage...")
    init_minio_storage()
    print("MinIO storage initialized.")
    
    yield
    
    # 关闭时清理
    print("Closing database connections...")
    await close_db()
    print("Database connections closed.")


def create_app() -> FastAPI:
    """创建FastAPI应用"""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="TARA报告上传解析服务 - 提供文件上传、JSON解析和数据存储功能",
        lifespan=lifespan
    )
    
    # CORS配置
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 注册路由
    app.include_router(router)
    
    # 健康检查
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION
        }
    
    @app.get("/")
    async def root():
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "docs": "/docs",
            "redoc": "/redoc"
        }
    
    return app


# 创建应用实例
app = create_app()


def run_server():
    """启动服务器"""
    import uvicorn
    uvicorn.run(
        "upload_parser.app:app",
        host="0.0.0.0",
        port=8001,
        reload=settings.DEBUG
    )


if __name__ == "__main__":
    run_server()
