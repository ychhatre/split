import logging
from minio import Minio
from minio.error import S3Error
from app.config import minio_config

logger = logging.getLogger(__name__)


class MinIOClient:
    """MinIO client wrapper for file operations"""
    
    def __init__(self):
        self.client = Minio(
            minio_config.endpoint,
            access_key=minio_config.access_key,
            secret_key=minio_config.secret_key,
            secure=minio_config.secure
        )
    
    def ensure_bucket_exists(self, bucket_name: str = None):
        """Ensure the bucket exists, create if it doesn't"""
        bucket = bucket_name or minio_config.bucket
        if not self.client.bucket_exists(bucket):
            self.client.make_bucket(bucket)
            logger.info(f"Created bucket: {bucket}")
    
    def upload_file(
        self,
        object_name: str,
        file_data: bytes,
        content_type: str,
        bucket_name: str = None
    ) -> str:
        """
        Upload a file to MinIO and return the full URL.
        
        Args:
            object_name: The object name in MinIO (e.g., "session123/receipt.jpg")
            file_data: The file content as bytes
            content_type: The MIME type of the file
            bucket_name: Optional bucket name (defaults to config)
        
        Returns:
            The full URL to the uploaded file
        """
        bucket = bucket_name or minio_config.bucket
        
        # Ensure bucket exists
        self.ensure_bucket_exists(bucket)
        
        # Upload file
        try:
            from io import BytesIO
            self.client.put_object(
                bucket,
                object_name,
                BytesIO(file_data),
                length=len(file_data),
                content_type=content_type
            )
            logger.info(f"Uploaded to MinIO: {object_name}")
        except S3Error as e:
            logger.error(f"MinIO upload error: {e}")
            raise
        
        # Return the full URL
        return minio_config.get_object_url(object_name)


# Global client instance
minio_client = MinIOClient()
