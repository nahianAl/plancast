#!/usr/bin/env python3
"""
Debug Startup Script for PlanCast

This script helps identify startup issues that might be causing
Railway healthcheck failures.
"""

import os
import sys
import time
import traceback
from pathlib import Path

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_imports():
    """Test if all required modules can be imported."""
    print("🔍 Testing imports...")
    
    try:
        print("  - Testing FastAPI imports...")
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
        print("    ✅ FastAPI imports successful")
        
        print("  - Testing database imports...")
        from models.database_connection import get_db_session, test_connection
        print("    ✅ Database imports successful")
        
        print("  - Testing service imports...")
        from services.coordinate_scaler import CoordinateScaler
        print("    ✅ Service imports successful")
        
        print("  - Testing main app import...")
        from api.main import app
        print("    ✅ Main app import successful")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Import failed: {e}")
        traceback.print_exc()
        return False

def test_database_connection():
    """Test database connection."""
    print("🔍 Testing database connection...")
    
    try:
        from models.database_connection import test_connection, check_database_health
        
        # Test basic connection
        connection_ok = test_connection()
        print(f"  - Basic connection: {'✅ OK' if connection_ok else '❌ Failed'}")
        
        # Test health check
        health = check_database_health()
        print(f"  - Health check: {health}")
        
        return connection_ok
        
    except Exception as e:
        print(f"    ❌ Database test failed: {e}")
        traceback.print_exc()
        return False

def test_health_endpoint():
    """Test the health endpoint directly."""
    print("🔍 Testing health endpoint...")
    
    try:
        from api.main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        response = client.get("/health")
        
        print(f"  - Status code: {response.status_code}")
        print(f"  - Response: {response.json()}")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"    ❌ Health endpoint test failed: {e}")
        traceback.print_exc()
        return False

def test_cubicasa_service():
    """Test CubiCasa service initialization."""
    print("🔍 Testing CubiCasa service...")
    
    try:
        from services.cubicasa_service import CubiCasaService
        
        # Just test if we can create the service (don't load the model)
        service = CubiCasaService()
        print("    ✅ CubiCasa service created successfully")
        
        # Test health check
        health = service.health_check()
        print(f"    - Health check: {health}")
        
        return True
        
    except Exception as e:
        print(f"    ❌ CubiCasa service test failed: {e}")
        traceback.print_exc()
        return False

def test_environment():
    """Test environment variables and configuration."""
    print("🔍 Testing environment...")
    
    # Check critical environment variables
    critical_vars = [
        "DATABASE_URL",
        "POSTGRES_DB",
        "POSTGRES_USER", 
        "POSTGRES_PASSWORD"
    ]
    
    for var in critical_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if "password" in var.lower():
                print(f"  - {var}: {'*' * len(value)}")
            else:
                print(f"  - {var}: {value}")
        else:
            print(f"  - {var}: ❌ Not set")
    
    # Check Railway-specific variables
    railway_vars = [
        "RAILWAY_PERSISTENT_DIR",
        "PORT",
        "ENVIRONMENT"
    ]
    
    for var in railway_vars:
        value = os.getenv(var)
        print(f"  - {var}: {value or 'Not set'}")
    
    return True

def main():
    """Run all debug tests."""
    print("🚀 PlanCast Startup Debug")
    print("=" * 50)
    
    tests = [
        ("Environment", test_environment),
        ("Imports", test_imports),
        ("Database", test_database_connection),
        ("CubiCasa Service", test_cubicasa_service),
        ("Health Endpoint", test_health_endpoint),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} test...")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            traceback.print_exc()
            results[test_name] = False
    
    print("\n" + "=" * 50)
    print("📊 Debug Results:")
    
    all_passed = True
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All tests passed! The application should start successfully.")
    else:
        print("⚠️ Some tests failed. Check the output above for issues.")
    
    return all_passed

if __name__ == "__main__":
    main()
