#!/usr/bin/env python3
"""
PlanCast Startup Script for Railway Deployment

This script handles the proper startup of the FastAPI application
with Railway-specific configuration and environment variables.
"""

import os
import sys
import uvicorn
from pathlib import Path

def main():
    """Start the PlanCast FastAPI application."""
    
    # Add the project root to Python path
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    # Railway deployment configuration
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    # Environment-specific settings
    debug = os.getenv("DEBUG", "false").lower() == "true"
    log_level = os.getenv("LOG_LEVEL", "info")
    
    print(f"🚀 Starting PlanCast API on {host}:{port}")
    print(f"📊 Debug mode: {debug}")
    print(f"📝 Log level: {log_level}")
    
    # Create necessary directories
    os.makedirs("output/generated_models", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # Start the FastAPI application
    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=debug,
        log_level=log_level,
        access_log=True
    )

if __name__ == "__main__":
    main()
