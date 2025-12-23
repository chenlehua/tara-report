"""
MinIO存储服务
负责图片上传和获取
"""
import io
import uuid
from datetime import datetime, timedelta
from typing import Optional, Tuple, BinaryIO
from pathlib import Path

from minio import Minio
from minio.error import S3Error

from ..config import settings


class MinioStorageService:
    """MinIO存储服务"""
    
    def __init__(self):
        self.client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self.bucket_name = settings.MINIO_BUCKET
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """确保存储桶存在"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                # 设置存储桶公开读取策略(可选)
                policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {"AWS": "*"},
                            "Action": ["s3:GetObject"],
                            "Resource": [f"arn:aws:s3:::{self.bucket_name}/*"]
                        }
                    ]
                }
                import json
                self.client.set_bucket_policy(self.bucket_name, json.dumps(policy))
        except S3Error as e:
            print(f"MinIO bucket initialization error: {e}")
            raise
    
    def generate_object_path(self, report_id: str, image_type: str, filename: str) -> str:
        """
        生成MinIO对象路径
        格式: reports/{report_id}/{image_type}/{timestamp}_{filename}
        """
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        safe_filename = filename.replace(' ', '_')
        return f"reports/{report_id}/{image_type}/{timestamp}_{safe_filename}"
    
    async def upload_image(
        self,
        file_data: bytes,
        report_id: str,
        image_type: str,
        filename: str,
        content_type: str = "image/png"
    ) -> Tuple[str, int]:
        """
        上传图片到MinIO
        
        Args:
            file_data: 文件二进制数据
            report_id: 报告ID
            image_type: 图片类型
            filename: 原始文件名
            content_type: 内容类型
            
        Returns:
            (对象路径, 文件大小)
        """
        object_path = self.generate_object_path(report_id, image_type, filename)
        file_size = len(file_data)
        
        try:
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_path,
                data=io.BytesIO(file_data),
                length=file_size,
                content_type=content_type
            )
            return object_path, file_size
        except S3Error as e:
            print(f"MinIO upload error: {e}")
            raise
    
    def upload_image_sync(
        self,
        file_data: bytes,
        report_id: str,
        image_type: str,
        filename: str,
        content_type: str = "image/png"
    ) -> Tuple[str, int]:
        """同步上传图片到MinIO"""
        object_path = self.generate_object_path(report_id, image_type, filename)
        file_size = len(file_data)
        
        try:
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_path,
                data=io.BytesIO(file_data),
                length=file_size,
                content_type=content_type
            )
            return object_path, file_size
        except S3Error as e:
            print(f"MinIO upload error: {e}")
            raise
    
    def get_image_url(self, object_path: str, expires: int = 3600) -> str:
        """
        获取图片的预签名URL
        
        Args:
            object_path: 对象路径
            expires: URL有效期(秒)
            
        Returns:
            预签名URL
        """
        try:
            url = self.client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=object_path,
                expires=timedelta(seconds=expires)
            )
            return url
        except S3Error as e:
            print(f"MinIO get URL error: {e}")
            raise
    
    def get_image_data(self, object_path: str) -> bytes:
        """
        获取图片数据
        
        Args:
            object_path: 对象路径
            
        Returns:
            图片二进制数据
        """
        try:
            response = self.client.get_object(
                bucket_name=self.bucket_name,
                object_name=object_path
            )
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            print(f"MinIO get data error: {e}")
            raise
    
    def delete_image(self, object_path: str) -> bool:
        """
        删除图片
        
        Args:
            object_path: 对象路径
            
        Returns:
            是否删除成功
        """
        try:
            self.client.remove_object(
                bucket_name=self.bucket_name,
                object_name=object_path
            )
            return True
        except S3Error as e:
            print(f"MinIO delete error: {e}")
            return False
    
    def delete_report_images(self, report_id: str) -> int:
        """
        删除报告的所有图片
        
        Args:
            report_id: 报告ID
            
        Returns:
            删除的图片数量
        """
        prefix = f"reports/{report_id}/"
        deleted_count = 0
        
        try:
            objects = self.client.list_objects(
                bucket_name=self.bucket_name,
                prefix=prefix,
                recursive=True
            )
            
            for obj in objects:
                self.client.remove_object(
                    bucket_name=self.bucket_name,
                    object_name=obj.object_name
                )
                deleted_count += 1
            
            return deleted_count
        except S3Error as e:
            print(f"MinIO batch delete error: {e}")
            return deleted_count
    
    def get_public_url(self, object_path: str) -> str:
        """
        获取图片的公开URL(需要桶设置为公开读取)
        
        Args:
            object_path: 对象路径
            
        Returns:
            公开URL
        """
        protocol = "https" if settings.MINIO_SECURE else "http"
        return f"{protocol}://{settings.MINIO_ENDPOINT}/{self.bucket_name}/{object_path}"


# 全局存储服务实例
minio_storage: Optional[MinioStorageService] = None


def get_minio_storage() -> MinioStorageService:
    """获取MinIO存储服务实例"""
    global minio_storage
    if minio_storage is None:
        minio_storage = MinioStorageService()
    return minio_storage


def init_minio_storage() -> MinioStorageService:
    """初始化MinIO存储服务"""
    global minio_storage
    minio_storage = MinioStorageService()
    return minio_storage
