"""
Report Service - TARA Report Generation and Download
Responsible for generating Excel and PDF reports based on report ID, and providing download functionality
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.common.config.settings import settings
from app.common.database.mysql import Base, engine
from app.api.v1.router import api_router

# Create FastAPI application
app = FastAPI(
    title=settings.SERVICE_NAME,
    description=settings.SERVICE_DESCRIPTION,
    version=settings.SERVICE_VERSION
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    """Initialize database on startup"""
    print("Initializing database...")
    Base.metadata.create_all(bind=engine)
    print("Database initialized.")


@app.get("/")
async def root():
    """API root path"""
    return {
        "name": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "status": "running"
    }


# Include API router with /api prefix
app.include_router(api_router, prefix="/api")


# ==================== Startup function ====================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8002,
        reload=True
    )
