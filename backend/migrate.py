#!/usr/bin/env python3
"""
Database migration script for RDS.
Run this script before deploying to Lambda to ensure RDS is up to date.
"""

import os
import sys
from alembic.config import Config
from alembic import command
from app.database import SQLALCHEMY_DATABASE_URL

def run_migrations():
    """Run all pending migrations on the RDS database."""
    print(f"Running migrations on database: {SQLALCHEMY_DATABASE_URL}")
    
    # Create Alembic configuration
    alembic_cfg = Config("alembic.ini")
    
    # Set the database URL
    alembic_cfg.set_main_option("sqlalchemy.url", SQLALCHEMY_DATABASE_URL)
    
    try:
        # Check current revision
        print("Checking current database state...")
        command.current(alembic_cfg)
        
        # Run migrations
        print("Running migrations...")
        command.upgrade(alembic_cfg, "head")
        
        print("✅ Migrations completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_migrations()
