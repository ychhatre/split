from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_database, check_database_connection
from app.routers import receipts, sessions
import logging
import sys

# Configure logging for Render (stdout/stderr)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Split - Receipt Splitting API",
    description="API for splitting restaurant bills by item with receipt scanning",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this based on your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize database and check connections on startup"""
    logger.info("=" * 50)
    logger.info("🚀 Starting Split API")
    logger.info("=" * 50)
    
    # Check database connection
    if check_database_connection():
        logger.info("✓ Database connection verified")
    else:
        logger.error("✗ Database connection failed - check DATABASE_URL")
    
    # Create tables if they don't exist
    if init_database():
        logger.info("✓ Database tables ready")
    else:
        logger.warning("⚠️  Database initialization had issues")
    
    logger.info("=" * 50)

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("👋 Shutting down Split API")

# Include routers
app.include_router(receipts.router)
app.include_router(sessions.router)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Split API - Receipt Splitting Service",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for Render"""
    import os
    
    health_status = {
        "status": "healthy",
        "service": "split-api",
        "environment": os.getenv("ENVIRONMENT", "development")
    }
    
    # Check database connection
    try:
        if check_database_connection():
            health_status["database"] = "connected"
        else:
            health_status["database"] = "disconnected"
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"
    
    return health_status

@app.get("/debug")
async def debug_info():
    """Debug endpoint to check configuration (use with caution in production)"""
    import os
    return {
        "status": "debug",
        "environment": {
            "ENVIRONMENT": os.getenv("ENVIRONMENT", "NOT_SET"),
            "OPENAI_API_KEY": "SET" if os.getenv("OPENAI_API_KEY") else "MISSING",
            "DATABASE_URL": "SET" if os.getenv("DATABASE_URL") else "MISSING",
            "AWS_REGION": os.getenv("AWS_REGION", "NOT_SET"),
            "FRONTEND_URL": os.getenv("FRONTEND_URL", "NOT_SET"),
        },
        "aws_credentials": {
            "AWS_ACCESS_KEY_ID": "SET" if os.getenv("AWS_ACCESS_KEY_ID") else "MISSING",
            "AWS_SECRET_ACCESS_KEY": "SET" if os.getenv("AWS_SECRET_ACCESS_KEY") else "MISSING",
        }
    }
