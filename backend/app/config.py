import os
from typing import Optional


# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://split_user:split_pass@localhost:5432/split_db")

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Frontend Configuration
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


class MinIOConfig:
    """MinIO configuration settings"""
    
    def __init__(self):
        self.endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
        self.access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        self.secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
        self.secure = os.getenv("MINIO_SECURE", "false").lower() == "true"
        self.bucket = os.getenv("MINIO_BUCKET", "receipts")
    
    @property
    def base_url(self) -> str:
        """Get the base URL for MinIO"""
        protocol = "https" if self.secure else "http"
        return f"{protocol}://{self.endpoint}"
    
    def get_object_url(self, object_name: str) -> str:
        """Get the full URL for an object in MinIO"""
        return f"{self.base_url}/{self.bucket}/{object_name}"


# Global config instance
minio_config = MinIOConfig()
