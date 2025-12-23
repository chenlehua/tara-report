"""
TARA数据服务入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .common.database import Base, engine
from .api import api_router

# 创建FastAPI应用
app = FastAPI(
    title="TARA Data Service",
    description="TARA报告数据管理服务 - 负责数据上传、解析和存储",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册API v1路由
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """根端点"""
    return {
        "service": "TARA Data Service",
        "version": "1.0.0",
        "api_version": "v1"
    }


@app.on_event("startup")
async def startup():
    """启动时初始化数据库"""
    print("Initializing database...")
    Base.metadata.create_all(bind=engine)
    print("Database initialized.")


# ==================== 启动函数 ====================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )
