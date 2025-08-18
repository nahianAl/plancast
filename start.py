#!/usr/bin/env python3
"""
PlanCast Startup Script

This script ensures proper initialization of the application,
including persistent storage setup and model pre-loading.
"""

import os
import sys
import time
from pathlib import Path

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def setup_persistent_storage():
    """Setup persistent storage for Railway deployment."""
    # Check if we're on Railway with persistent storage
    railway_persistent = os.getenv("RAILWAY_PERSISTENT_DIR", "/data")
    
    if os.path.exists(railway_persistent):
        print(f"🚀 Setting up Railway persistent storage: {railway_persistent}")
        
        # Create models directory
        models_dir = os.path.join(railway_persistent, "models")
        Path(models_dir).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created models directory: {models_dir}")
        
        # Create other persistent directories
        persistent_dirs = [
            os.path.join(railway_persistent, "output"),
            os.path.join(railway_persistent, "temp"),
            os.path.join(railway_persistent, "logs")
        ]
        
        for dir_path in persistent_dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            print(f"✅ Created directory: {dir_path}")
        
        return True
    else:
        print(f"ℹ️ Railway persistent storage not available, using local storage")
        return False

def preload_cubicasa_model():
    """Preload the CubiCasa model to avoid cold starts."""
    try:
        print("🤖 Preloading CubiCasa model...")
        from services.cubicasa_service import get_cubicasa_service
        
        start_time = time.time()
        service = get_cubicasa_service()
        load_time = time.time() - start_time
        
        print(f"✅ CubiCasa model preloaded successfully in {load_time:.2f}s")
        return True
        
    except Exception as e:
        print(f"❌ Failed to preload CubiCasa model: {e}")
        return False

def main():
    """Main startup function."""
    print("🚀 PlanCast Startup Script")
    print("=" * 50)
    
    # Setup persistent storage
    persistent_available = setup_persistent_storage()
    
    # Preload model
    model_loaded = preload_cubicasa_model()
    
    print("=" * 50)
    print(f"📊 Startup Summary:")
    print(f"   Persistent Storage: {'✅ Available' if persistent_available else '❌ Not Available'}")
    print(f"   Model Preloaded: {'✅ Success' if model_loaded else '❌ Failed'}")
    print("=" * 50)
    
    # Start the main application
    print("🚀 Starting PlanCast API server...")
    from api.main import socketio_app
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        socketio_app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )

if __name__ == "__main__":
    main()
