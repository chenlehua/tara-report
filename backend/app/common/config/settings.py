"""
应用配置
"""
import os
from pathlib import Path


class Settings:
    """应用配置类"""
    
    # 应用信息
    APP_NAME: str = "TARA Report Generator API"
    APP_DESCRIPTION: str = "威胁分析和风险评估报告生成服务"
    APP_VERSION: str = "1.0.0"
    
    # API配置
    API_V1_PREFIX: str = "/api/v1"
    
    # 数据库配置
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "mysql")
    MYSQL_PORT: str = os.getenv("MYSQL_PORT", "3306")
    MYSQL_USER: str = os.getenv("MYSQL_USER", "tara")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "tara123456")
    MYSQL_DATABASE: str = os.getenv("MYSQL_DATABASE", "tara_db")
    
    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}?charset=utf8mb4"
    
    # MinIO配置
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "minio:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "minioadmin123")
    MINIO_SECURE: bool = os.getenv("MINIO_SECURE", "false").lower() == "true"
    
    # 存储目录配置
    BASE_DIR: Path = Path(__file__).parent.parent.parent.parent
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    REPORTS_DIR: Path = BASE_DIR / "reports"
    IMAGES_DIR: Path = UPLOAD_DIR / "images"
    
    # CORS配置
    CORS_ORIGINS: list = ["*"]
    
    def __init__(self):
        # 确保目录存在
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        self.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        self.IMAGES_DIR.mkdir(parents=True, exist_ok=True)


settings = Settings()
