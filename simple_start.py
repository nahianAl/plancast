#!/usr/bin/env python3
"""
Simple Startup Script for PlanCast

This script starts the server without model preloading to test basic functionality.
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def main():
    """Main startup function."""
    print("🚀 PlanCast Simple Startup")
    print("=" * 30)
    
    # Start the main application without model preloading
    print("🚀 Starting PlanCast API server...")
    from api.main import socketio_app
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    print(f"📡 Server will start on port {port}")
    
    uvicorn.run(
        socketio_app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )

if __name__ == "__main__":
    main()
