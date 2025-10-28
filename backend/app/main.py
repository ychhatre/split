from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import receipts, sessions
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Database tables will be created on first use, not on startup
# This prevents Lambda initialization timeouts and connection errors

app = FastAPI(
    title="Split - Receipt Splitting API",
    # Exclude venv from reload
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add startup event to create tables (optional)
@app.on_event("startup")
async def startup_event():
    """Create database tables on startup if they don't exist"""
    from app.database import init_database
    success = init_database()
    if success:
        logging.info("Database tables created successfully")
    else:
        logging.warning("Database tables could not be created - will be created on first use")

# Configure CORS - Allow specific origins for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://split-eight-nu.vercel.app",  # Production frontend
        "http://localhost:3000",  # Local development
        "http://127.0.0.1:3000",  # Local development alternative
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers
app.include_router(receipts.router)
app.include_router(sessions.router)


@app.get("/")
async def root():
    return {"message": "Split API - Receipt Splitting Service"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/debug")
async def debug_info():
    """Debug endpoint to check configuration"""
    import os
    return {
        "status": "debug",
        "environment": {
            "OPENAI_API_KEY": "SET" if os.getenv("OPENAI_API_KEY") else "MISSING",
            "AWS_REGION": os.getenv("AWS_REGION", "NOT_SET"),
            "S3_BUCKET": os.getenv("S3_BUCKET", "NOT_SET"),
            "ENVIRONMENT": os.getenv("ENVIRONMENT", "NOT_SET"),
        },
        "aws_credentials": {
            "AWS_ACCESS_KEY_ID": "SET" if os.getenv("AWS_ACCESS_KEY_ID") else "MISSING",
            "AWS_SECRET_ACCESS_KEY": "SET" if os.getenv("AWS_SECRET_ACCESS_KEY") else "MISSING",
        }
    }
