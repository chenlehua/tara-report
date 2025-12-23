"""
配置模块
"""
import os


class Settings:
    """应用配置"""
    # 数据库配置
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "mysql")
    MYSQL_PORT: str = os.getenv("MYSQL_PORT", "3306")
    MYSQL_USER: str = os.getenv("MYSQL_USER", "tara")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "tara123456")
    MYSQL_DATABASE: str = os.getenv("MYSQL_DATABASE", "tara_db")
    
    # MinIO配置
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "minio:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "minioadmin123")
    MINIO_SECURE: bool = os.getenv("MINIO_SECURE", "false").lower() == "true"
    
    # 桶名称
    BUCKET_IMAGES: str = "tara-images"
    BUCKET_REPORTS: str = "tara-reports"
    
    # 服务配置
    REPORT_SERVICE_URL: str = os.getenv("REPORT_SERVICE_URL", "http://report-service:8002")
    
    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}?charset=utf8mb4"


settings = Settings()
