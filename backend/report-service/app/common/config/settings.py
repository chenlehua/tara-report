"""
Application settings
"""
import os


class Settings:
    """Application settings"""
    
    # Service info
    SERVICE_NAME: str = "TARA Report Service"
    SERVICE_VERSION: str = "1.0.0"
    SERVICE_DESCRIPTION: str = "TARA报告生成服务 - 负责生成Excel和PDF报告"
    
    # Data service URL
    DATA_SERVICE_URL: str = os.getenv("DATA_SERVICE_URL", "http://data-service:8001")
    
    # MySQL configuration
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "mysql")
    MYSQL_PORT: str = os.getenv("MYSQL_PORT", "3306")
    MYSQL_USER: str = os.getenv("MYSQL_USER", "tara")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "tara123456")
    MYSQL_DATABASE: str = os.getenv("MYSQL_DATABASE", "tara_db")
    
    # MinIO configuration
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "minio:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "minioadmin123")
    MINIO_SECURE: bool = os.getenv("MINIO_SECURE", "false").lower() == "true"
    
    # MinIO buckets
    BUCKET_IMAGES: str = "tara-images"
    BUCKET_REPORTS: str = "tara-reports"
    
    @property
    def DATABASE_URL(self) -> str:
        """Get database URL"""
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}?charset=utf8mb4"


settings = Settings()
