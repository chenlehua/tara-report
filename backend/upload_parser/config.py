"""
上传解析模块配置
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用设置
    APP_NAME: str = "TARA Upload Parser"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # MySQL配置
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER: str = os.getenv("MYSQL_USER", "tara_user")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "tara_password")
    MYSQL_DATABASE: str = os.getenv("MYSQL_DATABASE", "tara_db")
    
    @property
    def MYSQL_URL(self) -> str:
        return f"mysql+aiomysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
    
    @property
    def MYSQL_URL_SYNC(self) -> str:
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
    
    # MinIO配置
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    MINIO_BUCKET: str = os.getenv("MINIO_BUCKET", "tara-images")
    MINIO_SECURE: bool = os.getenv("MINIO_SECURE", "false").lower() == "true"
    
    # 上传配置
    MAX_IMAGE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_IMAGE_EXTENSIONS: set = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.webp'}
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
