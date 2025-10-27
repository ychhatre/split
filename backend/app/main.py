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

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Split - Receipt Splitting API",
    # Exclude venv from reload
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS - Allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
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
