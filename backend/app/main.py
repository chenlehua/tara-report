"""
TARA Report Generator API
威胁分析和风险评估报告生成服务
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.common.config import settings
from app.common.database import Base, engine
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


@app.on_event("startup")
async def startup():
    """启动时初始化数据库"""
    print("Initializing database...")
    Base.metadata.create_all(bind=engine)
    print("Database initialized.")


@app.get("/")
async def root():
    """API根路径"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


# 注册API路由
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


def run_server():
    """运行服务器"""
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )


if __name__ == "__main__":
    run_server()
