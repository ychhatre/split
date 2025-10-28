import os
from dotenv import load_dotenv

load_dotenv()

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://split_user:split_pass@localhost:5432/split_db")

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Frontend Configuration
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


class S3Config:
    """S3 configuration settings"""
    
    def __init__(self):
        # S3 settings
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.access_key = os.getenv("AWS_ACCESS_KEY_ID")
        self.secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        
        # Determine environment and set appropriate bucket
        self.environment = os.getenv("ENVIRONMENT", "development")
        if self.environment == "production":
            self.bucket = os.getenv("S3_BUCKET", "split-receipts-prod")
        else:
            self.bucket = os.getenv("S3_BUCKET", "split-receipts-dev")
    
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
