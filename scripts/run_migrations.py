#!/usr/bin/env python3
"""
Run database migrations for PlanCast.
This script is designed to work in Railway's deployment environment.
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def run_migrations():
    """Run Alembic database migrations."""
    try:
        from alembic.config import Config
        from alembic import command
        
        # Set up Alembic configuration
        alembic_cfg = Config(str(project_root / "alembic.ini"))
        
        # Override the database URL from environment
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            print("❌ DATABASE_URL environment variable not found")
            return False
            
        alembic_cfg.set_main_option("sqlalchemy.url", database_url)
        
        print("🔄 Running database migrations...")
        
        # Run migrations
        command.upgrade(alembic_cfg, "head")
        
        print("✅ Database migrations completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_database_connection():
    """Test database connection before running migrations."""
    try:
        from models.database_connection import test_connection
        
        print("🔍 Testing database connection...")
        if test_connection():
            print("✅ Database connection successful")
            return True
        else:
            print("❌ Database connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 PlanCast Database Migration Script")
    
    # Check if we're in Railway environment
    if os.getenv("RAILWAY_ENVIRONMENT"):
        print("🚂 Detected Railway environment")
    
    try:
        # Test database connection
        if not check_database_connection():
            print("❌ Database connection failed, exiting...")
            sys.exit(1)
        
        # Run migrations
        if not run_migrations():
            print("❌ Migrations failed, exiting...")
            sys.exit(1)
        
        print("🎉 All migrations completed successfully!")
        print("🚀 Starting main application...")
        
    except Exception as e:
        print(f"❌ Migration script failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
