#!/usr/bin/env python3
"""
Test script for PlanCast database setup.

This script tests the database connection, models, and basic operations
to ensure everything is working correctly.
"""

import os
import sys
import time
from datetime import datetime, timedelta

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_database_connection():
    """Test basic database connection."""
    print("🔌 Testing database connection...")
    
    try:
        from models.database_connection import test_connection, get_database_info
        
        # Test connection
        if test_connection():
            print("✅ Database connection successful")
            
            # Get database info
            info = get_database_info()
            print(f"📊 Database info: {info}")
            return True
        else:
            print("❌ Database connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Error testing connection: {e}")
        return False

def test_database_models():
    """Test database model creation and basic operations."""
    print("\n🗄️  Testing database models...")
    
    try:
        from models.database import Base, User, Project, UsageLog, Team
        from models.database_connection import create_tables, get_db_session
        from models.repository import UserRepository, ProjectRepository, UsageRepository
        
        # Create tables
        print("📋 Creating database tables...")
        create_tables()
        print("✅ Tables created successfully")
        
        # Test user creation
        print("👤 Testing user creation...")
        with get_db_session() as session:
            # Create test user
            test_user = UserRepository.create_user(
                session=session,
                email="test@plancast.com",
                password_hash="test_hash_123",
                first_name="Test",
                last_name="User",
                company="Test Company"
            )
            print(f"✅ Test user created: {test_user.email}")
            
            # Test user retrieval
            retrieved_user = UserRepository.get_user_by_email(session, "test@plancast.com")
            if retrieved_user:
                print(f"✅ User retrieved: {retrieved_user.email}")
            else:
                print("❌ User retrieval failed")
                return False
            
            # Test project creation
            print("📁 Testing project creation...")
            test_project = ProjectRepository.create_project(
                session=session,
                user_id=test_user.id,
                filename="test_floorplan.jpg",
                original_filename="test_floorplan.jpg",
                input_file_path="/temp/test_file.jpg",
                file_size_mb=2.5,
                file_format="jpg"
            )
            print(f"✅ Test project created: {test_project.filename}")
            
            # Test project status update
            updated_project = ProjectRepository.update_project_status(
                session=session,
                project_id=test_project.id,
                status="processing",
                current_step="ai_analysis",
                progress_percent=25
            )
            if updated_project and updated_project.status == "processing":
                print(f"✅ Project status updated: {updated_project.status}")
            else:
                print("❌ Project status update failed")
                return False
            
            # Test usage logging
            print("📊 Testing usage logging...")
            usage_log = UsageRepository.log_usage(
                session=session,
                user_id=test_user.id,
                action_type="upload",
                api_endpoint="/convert",
                project_id=test_project.id,
                file_size_mb=2.5,
                processing_time=1.2
            )
            print(f"✅ Usage logged: {usage_log.action_type}")
            
            # Test project retrieval
            retrieved_project = ProjectRepository.get_project_by_id(session, test_project.id)
            if retrieved_project and retrieved_project.user:
                print(f"✅ Project retrieved with user: {retrieved_project.user.email}")
            else:
                print("❌ Project retrieval failed")
                return False
            
            # Test project statistics
            stats = ProjectRepository.get_project_stats(session, test_user.id)
            print(f"✅ Project stats: {stats}")
            
            # Test usage summary
            usage_summary = UsageRepository.get_usage_summary(session, test_user.id, days=30)
            print(f"✅ Usage summary: {usage_summary}")
            
            # Clean up test data
            print("🧹 Cleaning up test data...")
            session.delete(test_project)
            session.delete(usage_log)
            session.delete(test_user)
            session.commit()
            print("✅ Test data cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing models: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_health():
    """Test database health check."""
    print("\n🏥 Testing database health check...")
    
    try:
        from models.database_connection import check_database_health
        
        health = check_database_health()
        print(f"📊 Health status: {health}")
        
        if health['status'] == 'healthy':
            print("✅ Database health check passed")
            return True
        else:
            print("❌ Database health check failed")
            return False
            
    except Exception as e:
        print(f"❌ Error checking health: {e}")
        return False

def test_migrations():
    """Test database migrations."""
    print("\n🔄 Testing database migrations...")
    
    try:
        import subprocess
        
        # Check if alembic is available
        result = subprocess.run(["alembic", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Alembic is available")
            
            # Check current migration status
            result = subprocess.run(["alembic", "current"], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"📋 Current migration: {result.stdout.strip()}")
            else:
                print("⚠️  No migrations applied yet")
            
            return True
        else:
            print("❌ Alembic not available")
            return False
            
    except Exception as e:
        print(f"❌ Error testing migrations: {e}")
        return False

def main():
    """Main test function."""
    print("🧪 PlanCast Database Setup Test")
    print("=" * 40)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Database Models", test_database_models),
        ("Database Health", test_database_health),
        ("Database Migrations", test_migrations),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            success = test_func()
            results.append((test_name, success))
            if success:
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*50)
    print("📊 TEST RESULTS SUMMARY")
    print("="*50)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Database setup is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
