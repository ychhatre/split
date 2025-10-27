import logging
from app.config import s3_config

logger = logging.getLogger(__name__)


class S3Client:
    """S3 client for file operations"""
    
    def __init__(self):
        self.config = s3_config
        self._client = None
    
    @property
    def client(self):
        """Lazy initialization of the S3 client"""
        if self._client is None:
            self._client = self._create_s3_client()
        return self._client
    
    def _create_s3_client(self):
        """Create S3 client"""
        try:
            import boto3
            
            # Create S3 client
            if self.config.access_key and self.config.secret_key:
                # Use explicit credentials
                s3_client = boto3.client(
                    's3',
                    region_name=self.config.region,
                    aws_access_key_id=self.config.access_key,
                    aws_secret_access_key=self.config.secret_key
                )
            else:
                # Use IAM role or environment credentials
                s3_client = boto3.client('s3', region_name=self.config.region)
            
            return s3_client
        except ImportError:
            logger.error("boto3 library not installed. Install with: pip install boto3")
            raise
    
    def ensure_bucket_exists(self, bucket_name: str = None):
        """Ensure the bucket exists, create if it doesn't"""
        bucket = bucket_name or self.config.bucket
        
        try:
            from botocore.exceptions import ClientError
            
            self.client.head_bucket(Bucket=bucket)
            logger.info(f"S3 bucket exists: {bucket}")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                # Bucket doesn't exist, create it
                try:
                    if self.config.region == 'us-east-1':
                        # us-east-1 doesn't need LocationConstraint
                        self.client.create_bucket(Bucket=bucket)
                    else:
                        # Other regions need LocationConstraint
                        self.client.create_bucket(
                            Bucket=bucket,
                            CreateBucketConfiguration={'LocationConstraint': self.config.region}
                        )
                    logger.info(f"Created S3 bucket: {bucket}")
                except ClientError as create_error:
                    logger.error(f"Failed to create S3 bucket: {create_error}")
                    raise
            else:
                logger.error(f"Error checking S3 bucket: {e}")
                raise
    
    def upload_file(
        self,
        object_name: str,
        file_data: bytes,
        content_type: str,
        bucket_name: str = None
    ) -> str:
        """
        Upload a file to S3 and return the full URL.
        
        Args:
            object_name: The object name in S3 (e.g., "session123/receipt.jpg")
            file_data: The file content as bytes
            content_type: The MIME type of the file
            bucket_name: Optional bucket name (defaults to config)
        
        Returns:
            The full URL to the uploaded file
        """
        bucket = bucket_name or self.config.bucket
        
        # Ensure bucket exists
        self.ensure_bucket_exists(bucket)
        
        # Upload file
        try:
            from botocore.exceptions import ClientError
            
            self.client.put_object(
                Bucket=bucket,
                Key=object_name,
                Body=file_data,
                ContentType=content_type
            )
            
            logger.info(f"Uploaded to S3: {object_name}")
        except ClientError as e:
            logger.error(f"S3 upload error: {e}")
            raise
        
        # Return the full URL
        return self.config.get_object_url(object_name)
    
    def delete_file(self, object_name: str, bucket_name: str = None) -> bool:
        """
        Delete a file from S3.
        
        Args:
            object_name: The object name in S3
            bucket_name: Optional bucket name (defaults to config)
        
        Returns:
            True if successful, False otherwise
        """
        bucket = bucket_name or self.config.bucket
        
        try:
            from botocore.exceptions import ClientError
            
            self.client.delete_object(Bucket=bucket, Key=object_name)
            
            logger.info(f"Deleted from S3: {object_name}")
            return True
        except ClientError as e:
            logger.error(f"S3 delete error: {e}")
            return False
    
    def get_file_url(self, object_name: str, bucket_name: str = None, expires_in: int = 3600) -> str:
        """
        Get a presigned URL for a file.
        
        Args:
            object_name: The object name in S3
            bucket_name: Optional bucket name (defaults to config)
            expires_in: URL expiration time in seconds
        
        Returns:
            The URL to access the file
        """
        bucket = bucket_name or self.config.bucket
        
        try:
            from botocore.exceptions import ClientError
            
            url = self.client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket, 'Key': object_name},
                ExpiresIn=expires_in
            )
            return url
        except ClientError as e:
            logger.error(f"S3 presigned URL error: {e}")
            # Fallback to direct URL
            return self.config.get_object_url(object_name)


# Global client instance
s3_client = S3Client()
