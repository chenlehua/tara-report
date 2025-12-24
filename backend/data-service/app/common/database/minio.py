"""
MinIO client configuration
"""
import io
from typing import Optional, BinaryIO
from datetime import timedelta

from minio import Minio
from minio.error import S3Error

from app.common.config.settings import settings


class MinIOClient:
    """MinIO client wrapper"""
    
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self._ensure_buckets()
    
    def _ensure_buckets(self):
        """Ensure buckets exist"""
        for bucket in [settings.BUCKET_IMAGES, settings.BUCKET_REPORTS]:
            try:
                if not self.client.bucket_exists(bucket):
                    self.client.make_bucket(bucket)
                    print(f"Created bucket: {bucket}")
            except S3Error as e:
                print(f"Error creating bucket {bucket}: {e}")
    
    def upload_file(
        self,
        bucket: str,
        object_name: str,
        data: BinaryIO,
        length: int,
        content_type: str = "application/octet-stream"
    ) -> str:
        """
        Upload file to MinIO
        
        Args:
            bucket: Bucket name
            object_name: Object name (path)
            data: File data stream
            length: File size
            content_type: Content type
        
        Returns:
            str: MinIO object path
        """
        try:
            self.client.put_object(
                bucket,
                object_name,
                data,
                length,
                content_type=content_type
            )
            return f"{bucket}/{object_name}"
        except S3Error as e:
            raise Exception(f"Failed to upload file to MinIO: {e}")
    
    def upload_bytes(
        self,
        bucket: str,
        object_name: str,
        data: bytes,
        content_type: str = "application/octet-stream"
    ) -> str:
        """
        Upload bytes data to MinIO
        """
        data_stream = io.BytesIO(data)
        return self.upload_file(bucket, object_name, data_stream, len(data), content_type)
    
    def download_file(self, bucket: str, object_name: str) -> bytes:
        """
        Download file from MinIO
        
        Returns:
            bytes: File content
        """
        response = None
        try:
            response = self.client.get_object(bucket, object_name)
            return response.read()
        except S3Error as e:
            raise Exception(f"Failed to download file from MinIO: {e}")
        finally:
            if response:
                response.close()
                response.release_conn()
    
    def get_presigned_url(
        self,
        bucket: str,
        object_name: str,
        expires: timedelta = timedelta(hours=1)
    ) -> str:
        """
        Get presigned URL
        """
        try:
            return self.client.presigned_get_object(bucket, object_name, expires=expires)
        except S3Error as e:
            raise Exception(f"Failed to get presigned URL: {e}")
    
    def delete_file(self, bucket: str, object_name: str) -> bool:
        """
        Delete file
        """
        try:
            self.client.remove_object(bucket, object_name)
            return True
        except S3Error as e:
            print(f"Failed to delete file from MinIO: {e}")
            return False
    
    def file_exists(self, bucket: str, object_name: str) -> bool:
        """
        Check if file exists
        """
        try:
            self.client.stat_object(bucket, object_name)
            return True
        except S3Error:
            return False


# Global client instance
_minio_client: Optional[MinIOClient] = None


def get_minio_client() -> MinIOClient:
    """Get MinIO client instance"""
    global _minio_client
    if _minio_client is None:
        _minio_client = MinIOClient()
    return _minio_client
