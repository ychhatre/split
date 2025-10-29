import os
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

# Database Configuration - Supabase PostgreSQL (both local and production)
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    logger.error("❌ DATABASE_URL not set - please configure Supabase connection string")
    raise ValueError("DATABASE_URL environment variable is required")

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.warning("⚠️  OPENAI_API_KEY not set - receipt parsing will fail")

# Frontend Configuration
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# S3 Bucket Names
PROD_BUCKET = "split-receipts-prod"
DEV_BUCKET = "split-receipts-dev"

class S3Config:
    """S3 configuration for receipt storage"""
    
    def __init__(self):
        # S3 settings
        self.region = os.getenv("AWS_REGION", "us-west-1")
        self.access_key = os.getenv("AWS_ACCESS_KEY_ID")
        self.secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        
        # Determine environment and set appropriate bucket
        self.environment = os.getenv("ENVIRONMENT", "development")
        if self.environment == "production":
            self.bucket = PROD_BUCKET
        else:
            self.bucket = DEV_BUCKET
        
        # Log configuration (without exposing secrets)
        logger.info(f"S3 Config - Region: {self.region}, Environment: {self.environment}, Bucket: {self.bucket}")
        
        if not self.access_key or not self.secret_key:
            logger.warning("⚠️  AWS credentials not fully configured - S3 upload will fail")
    
    @property
    def base_url(self) -> str:
        """Get the base URL for S3"""
        return f"https://{self.bucket}.s3.{self.region}.amazonaws.com"
    
    def get_object_url(self, object_name: str) -> str:
        """Get the full URL for an object in S3"""
        return f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{object_name}"
    
    def is_production(self) -> bool:
        """Check if we're running in production mode"""
        return self.environment == "production"


# Global config instance
s3_config = S3Config()

# Log startup configuration
logger.info(f"Configuration loaded - Environment: {s3_config.environment}")
logger.info(f"Frontend URL: {FRONTEND_URL}")
logger.info(f"Database: PostgreSQL (Supabase)")
