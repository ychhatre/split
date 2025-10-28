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
            print("[S3] Creating S3 client...")
            self._client = self._create_s3_client()
            print("[S3] S3 client created successfully")
        return self._client
    
    def _create_s3_client(self):
        """Create S3 client"""
        try:
            import boto3
            from botocore.config import Config
            
            print(f"[S3] Region: {self.config.region}")
            print(f"[S3] Access Key present: {bool(self.config.access_key)}")
            print(f"[S3] Secret Key present: {bool(self.config.secret_key)}")
            
            # Configure with timeouts to prevent hanging
            config = Config(
                connect_timeout=3,  # 3 seconds to establish connection
                read_timeout=5,      # 5 seconds to read response
                retries={'max_attempts': 1}  # Retry once (total 2 attempts)
            )
            
            # Create S3 client - always use explicit credentials if set
            print("[S3] Using explicit credentials from environment variables")
            s3_client = boto3.client(
                's3',
                region_name=self.config.region,
                aws_access_key_id=self.config.access_key,
                aws_secret_access_key=self.config.secret_key,
                config=config
            )
            
            print("[S3] boto3 client object created")
            return s3_client
        except ImportError:
            print("[S3] boto3 not installed!")
            logger.error("boto3 library not installed. Install with: pip install boto3")
            raise
        except Exception as e:
            print(f"[S3] Error creating client: {e}")
            raise
    
    def ensure_bucket_exists(self, bucket_name: str = None):
        """Ensure the bucket exists, create if it doesn't"""
        bucket = bucket_name or self.config.bucket
        print(f"[S3] ensure_bucket_exists called for: {bucket}")
        
        try:
            from botocore.exceptions import ClientError, EndpointConnectionError, ReadTimeoutError, ConnectTimeoutError
            import time
            
            print(f"[S3] Calling head_bucket...")
            start_time = time.time()
            try:
                self.client.head_bucket(Bucket=bucket)
                elapsed = time.time() - start_time
                print(f"[S3] head_bucket completed in {elapsed:.2f}s")
                print(f"[S3] Bucket exists: {bucket}")
                logger.info(f"S3 bucket exists: {bucket}")
            except Exception as api_error:
                elapsed = time.time() - start_time
                print(f"[S3] head_bucket failed after {elapsed:.2f}s: {type(api_error).__name__}: {api_error}")
                raise
        except (ConnectTimeoutError, ReadTimeoutError) as e:
            print(f"[S3] Timeout error: {e}")
            logger.error(f"S3 timeout error: {e}")
            raise Exception(f"AWS S3 connection timeout. Check your network and AWS credentials.")
        except EndpointConnectionError as e:
            print(f"[S3] Connection error: {e}")
            logger.error(f"S3 connection error: {e}")
            raise Exception(f"Cannot connect to AWS S3. Check your network connection.")
        except ClientError as e:
            print(f"[S3] ClientError in head_bucket: {e}")
            error_code = e.response['Error']['Code']
            if error_code == '404':
                # Bucket doesn't exist, create it
                print(f"[S3] Bucket not found, creating...")
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
                    print(f"[S3] Bucket created: {bucket}")
                    logger.info(f"Created S3 bucket: {bucket}")
                except ClientError as create_error:
                    print(f"[S3] Failed to create bucket: {create_error}")
                    logger.error(f"Failed to create S3 bucket: {create_error}")
                    raise
            else:
                print(f"[S3] Error code {error_code}: {e}")
                logger.error(f"Error checking S3 bucket: {e}")
                raise
        except Exception as e:
            print(f"[S3] Unexpected error in ensure_bucket_exists: {type(e).__name__}: {e}")
            logger.error(f"S3 unexpected error: {e}")
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
        print(f"[S3] Starting upload_file for {object_name}")
        bucket = bucket_name or self.config.bucket
        print(f"[S3] Using bucket: {bucket}")
        
        # Upload file (assuming bucket exists)
        try:
            from botocore.exceptions import ClientError
            
            print(f"[S3] Starting put_object call...")
            self.client.put_object(
                Bucket=bucket,
                Key=object_name,
                Body=file_data,
                ContentType=content_type
            )
            
            print(f"[S3] Upload successful")
            logger.info(f"Uploaded to S3: {object_name}")
        except ClientError as e:
            print(f"[S3] ClientError: {e}")
            raise
        
        # Return the full URL
        url = self.config.get_object_url(object_name)
        print(f"[S3] Generated URL: {url}")
        return url
    
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
