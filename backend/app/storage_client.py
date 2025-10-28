import logging
from app.config import s3_config

logger = logging.getLogger(__name__)


class S3Client:
    """S3 client for receipt file storage"""
    
    def __init__(self):
        self.config = s3_config
        self._client = None
    
    @property
    def client(self):
        """Lazy initialization of the S3 client"""
        if self._client is None:
            logger.info("Initializing S3 client...")
            self._client = self._create_s3_client()
            logger.info("✓ S3 client initialized")
        return self._client
    
    def _create_s3_client(self):
        """Create and configure S3 client"""
        try:
            import boto3
            from botocore.config import Config
            
            logger.debug(f"S3 Region: {self.config.region}")
            logger.debug(f"S3 Bucket: {self.config.bucket}")
            
            # Configure with timeouts to prevent hanging
            config = Config(
                connect_timeout=5,
                read_timeout=10,
                retries={'max_attempts': 2}
            )
            
            # Create S3 client with explicit credentials
            s3_client = boto3.client(
                's3',
                region_name=self.config.region,
                aws_access_key_id=self.config.access_key,
                aws_secret_access_key=self.config.secret_key,
                config=config
            )
            
            return s3_client
        except ImportError:
            logger.error("boto3 library not installed. Install with: pip install boto3")
            raise
        except Exception as e:
            logger.error(f"Failed to create S3 client: {e}")
            raise
    
    def ensure_bucket_exists(self, bucket_name: str = None):
        """Ensure the S3 bucket exists, create if it doesn't"""
        bucket = bucket_name or self.config.bucket
        logger.debug(f"Checking if bucket exists: {bucket}")
        
        try:
            from botocore.exceptions import ClientError, EndpointConnectionError, ReadTimeoutError, ConnectTimeoutError
            
            try:
                self.client.head_bucket(Bucket=bucket)
                logger.info(f"✓ S3 bucket exists: {bucket}")
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == '404':
                    # Bucket doesn't exist, create it
                    logger.info(f"Creating S3 bucket: {bucket}")
                    try:
                        if self.config.region == 'us-east-1':
                            self.client.create_bucket(Bucket=bucket)
                        else:
                            self.client.create_bucket(
                                Bucket=bucket,
                                CreateBucketConfiguration={'LocationConstraint': self.config.region}
                            )
                        logger.info(f"✓ Created S3 bucket: {bucket}")
                    except ClientError as create_error:
                        logger.error(f"Failed to create S3 bucket: {create_error}")
                        raise
                else:
                    logger.error(f"S3 bucket check failed: {e}")
                    raise
        except (ConnectTimeoutError, ReadTimeoutError) as e:
            logger.error(f"S3 connection timeout: {e}")
            raise Exception(f"AWS S3 connection timeout. Check your network and AWS credentials.")
        except EndpointConnectionError as e:
            logger.error(f"Cannot connect to AWS S3: {e}")
            raise Exception(f"Cannot connect to AWS S3. Check your network connection.")
        except Exception as e:
            logger.error(f"Unexpected error checking S3 bucket: {e}")
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
        logger.info(f"Uploading file to S3: {object_name} ({len(file_data)} bytes)")
        
        try:
            from botocore.exceptions import ClientError
            
            self.client.put_object(
                Bucket=bucket,
                Key=object_name,
                Body=file_data,
                ContentType=content_type
            )
            
            url = self.config.get_object_url(object_name)
            logger.info(f"✓ File uploaded successfully: {url}")
            return url
            
        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            raise
    
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
            logger.info(f"✓ Deleted from S3: {object_name}")
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
            logger.debug(f"Generated presigned URL for: {object_name}")
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            # Fallback to direct URL
            return self.config.get_object_url(object_name)


# Global client instance
s3_client = S3Client()
