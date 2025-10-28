from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import DATABASE_URL
import logging

logger = logging.getLogger(__name__)


# Determine if local or production based on URL
is_local = "localhost" in DATABASE_URL or "127.0.0.1" in DATABASE_URL

# Create engine with appropriate settings
if is_local:
    # Local development - simpler settings
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        echo=False  # Set to True for SQL debugging
    )
    logger.info("✓ Using LOCAL PostgreSQL database")
else:
    # Production (Supabase) - optimized settings
    engine = create_engine(
        DATABASE_URL + "?sslmode=require",
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=5,
        max_overflow=10,
        echo=False,
        connect_args={
            "connect_timeout": 10,
            "options": "-c timezone=utc"
        }
    )
    logger.info("✓ Using PRODUCTION PostgreSQL database (Supabase)")

SQLALCHEMY_DATABASE_URL = DATABASE_URL

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Database dependency for FastAPI routes"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_database():
    """Initialize database tables safely"""
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✓ Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"✗ Error creating database tables: {e}", exc_info=True)
        return False

def check_database_connection():
    """Check if database connection is healthy"""
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✓ Database connection is healthy")
        return True
    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")
        return False
