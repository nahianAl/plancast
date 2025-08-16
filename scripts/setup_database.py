#!/usr/bin/env python3
"""
Database setup script for PlanCast.

This script sets up the PostgreSQL database, creates the necessary user,
and runs initial migrations. It can be run locally or in production.
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import subprocess

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import db_settings

def create_database_and_user():
    """Create database and user if they don't exist."""
    try:
        # Connect to PostgreSQL as superuser (current system user on macOS)
        superuser_conn = psycopg2.connect(
            host=db_settings.POSTGRES_HOST,
            port=db_settings.POSTGRES_PORT,
            user=os.getenv("POSTGRES_SUPERUSER", os.getenv("USER", "jjc4")),
            password=os.getenv("POSTGRES_SUPERUSER_PASSWORD", ""),
            database="postgres"
        )
        superuser_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        superuser_cursor = superuser_conn.cursor()
        
        print("🔌 Connected to PostgreSQL as superuser")
        
        # Check if user exists
        superuser_cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (db_settings.POSTGRES_USER,))
        user_exists = superuser_cursor.fetchone()
        
        if not user_exists:
            print(f"👤 Creating user: {db_settings.POSTGRES_USER}")
            superuser_cursor.execute(
                f"CREATE USER {db_settings.POSTGRES_USER} WITH PASSWORD '{db_settings.POSTGRES_PASSWORD}'"
            )
            print(f"✅ User {db_settings.POSTGRES_USER} created successfully")
        else:
            print(f"👤 User {db_settings.POSTGRES_USER} already exists")
        
        # Check if database exists
        superuser_cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_settings.POSTGRES_DB,))
        db_exists = superuser_cursor.fetchone()
        
        if not db_exists:
            print(f"🗄️  Creating database: {db_settings.POSTGRES_DB}")
            superuser_cursor.execute(f"CREATE DATABASE {db_settings.POSTGRES_DB}")
            print(f"✅ Database {db_settings.POSTGRES_DB} created successfully")
        else:
            print(f"🗄️  Database {db_settings.POSTGRES_DB} already exists")
        
        # Grant privileges to user
        print(f"🔑 Granting privileges to {db_settings.POSTGRES_USER}")
        superuser_cursor.execute(f"GRANT ALL PRIVILEGES ON DATABASE {db_settings.POSTGRES_DB} TO {db_settings.POSTGRES_USER}")
        superuser_cursor.execute(f"GRANT ALL ON SCHEMA public TO {db_settings.POSTGRES_USER}")
        print(f"✅ Privileges granted successfully")
        
        superuser_cursor.close()
        superuser_conn.close()
        
        return True
        
    except psycopg2.OperationalError as e:
        if "authentication failed" in str(e).lower():
            print("❌ Authentication failed. You may need to:")
            print("   1. Set POSTGRES_SUPERUSER_PASSWORD environment variable")
            print("   2. Use password authentication for local PostgreSQL")
            print("   3. Run as a user with PostgreSQL access")
            return False
        else:
            print(f"❌ PostgreSQL connection error: {e}")
            return False
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False

def test_connection():
    """Test connection to the new database."""
    try:
        conn = psycopg2.connect(
            host=db_settings.POSTGRES_HOST,
            port=db_settings.POSTGRES_PORT,
            user=db_settings.POSTGRES_USER,
            password=db_settings.POSTGRES_PASSWORD,
            database=db_settings.POSTGRES_DB
        )
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        print(f"✅ Database connection successful!")
        print(f"📊 PostgreSQL version: {version}")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        return False

def run_migrations():
    """Run database migrations using Alembic."""
    try:
        print("🔄 Running database migrations...")
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        if result.returncode == 0:
            print("✅ Migrations completed successfully")
            return True
        else:
            print(f"❌ Migration failed: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("❌ Alembic not found. Please install it with: pip install alembic")
        return False
    except Exception as e:
        print(f"❌ Error running migrations: {e}")
        return False

def create_initial_data():
    """Create initial data (admin user, etc.)."""
    try:
        print("📝 Creating initial data...")
        
        # Import database models and connection
        from models.database import User
        from models.database_connection import get_db_session
        import hashlib
        import secrets
        
        # Create admin user if it doesn't exist
        with get_db_session() as session:
            admin_user = session.query(User).filter(User.email == "admin@plancast.com").first()
            
            if not admin_user:
                # Generate secure password hash
                admin_password = "admin123"  # Change this in production!
                password_hash = hashlib.sha256(admin_password.encode()).hexdigest()
                
                # Generate API key
                api_key = secrets.token_urlsafe(32)
                
                admin_user = User(
                    email="admin@plancast.com",
                    password_hash=password_hash,
                    first_name="Admin",
                    last_name="User",
                    subscription_tier="enterprise",
                    api_key=api_key,
                    is_active=True,
                    is_verified=True
                )
                
                session.add(admin_user)
                session.commit()
                print("✅ Admin user created successfully")
                print(f"   Email: admin@plancast.com")
                print(f"   Password: admin123")
                print(f"   API Key: {api_key}")
            else:
                print("👤 Admin user already exists")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating initial data: {e}")
        return False

def main():
    """Main setup function."""
    print("🚀 PlanCast Database Setup")
    print("=" * 40)
    
    # Check if we're in production (Railway)
    if os.getenv("DATABASE_URL"):
        print("🌐 Production environment detected (Railway)")
        print("   Using DATABASE_URL environment variable")
        
        # Test connection
        if test_connection():
            print("✅ Production database connection successful")
            
            # Run migrations
            if run_migrations():
                print("✅ Production database setup complete!")
                return True
            else:
                print("❌ Production database setup failed")
                return False
        else:
            print("❌ Production database connection failed")
            return False
    
    # Local development setup
    print("💻 Local development environment")
    
    # Create database and user
    if not create_database_and_user():
        print("❌ Failed to create database and user")
        return False
    
    # Test connection
    if not test_connection():
        print("❌ Database connection test failed")
        return False
    
    # Run migrations
    if not run_migrations():
        print("❌ Migration failed")
        return False
    
    # Create initial data
    if not create_initial_data():
        print("❌ Failed to create initial data")
        return False
    
    print("✅ Database setup completed successfully!")
    print("\n📋 Next steps:")
    print("   1. Start your application")
    print("   2. Test the API endpoints")
    print("   3. Check the database tables")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
