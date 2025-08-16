"""
Configuration settings for PlanCast application.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings

# File upload limits
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB in bytes
MAX_EXPORT_SIZE = 100 * 1024 * 1024  # 100MB in bytes

# Default export formats
DEFAULT_EXPORT_FORMATS = ["glb", "obj", "stl"]

# Default units
DEFAULT_UNITS = "feet"

# API settings
API_VERSION = "1.0.0"
API_TITLE = "PlanCast API"

# Processing settings
DEFAULT_WALL_HEIGHT_FEET = 9.0
DEFAULT_WALL_THICKNESS_FEET = 0.5
DEFAULT_FLOOR_THICKNESS_FEET = 0.25

# Database Configuration
class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    
    # PostgreSQL connection
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "plancast"
    POSTGRES_USER: str = "plancast_user"
    POSTGRES_PASSWORD: str = "plancast_password"
    
    # Connection pool settings
    POSTGRES_POOL_SIZE: int = 10
    POSTGRES_MAX_OVERFLOW: int = 20
    POSTGRES_POOL_TIMEOUT: int = 30
    POSTGRES_POOL_RECYCLE: int = 3600
    
    # SSL settings (for Railway/production)
    POSTGRES_SSL_MODE: str = "prefer"
    POSTGRES_SSL_CERT: Optional[str] = None
    POSTGRES_SSL_KEY: Optional[str] = None
    POSTGRES_SSL_ROOT_CERT: Optional[str] = None
    
    @property
    def database_url(self) -> str:
        """Generate database URL from settings."""
        if os.getenv("DATABASE_URL"):
            # Use Railway/Heroku DATABASE_URL if available
            return os.getenv("DATABASE_URL")
        
        # Build URL from individual components
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    @property
    def async_database_url(self) -> str:
        """Generate async database URL from settings."""
        if os.getenv("DATABASE_URL"):
            # Convert to async format
            url = os.getenv("DATABASE_URL")
            if url.startswith("postgresql://"):
                return url.replace("postgresql://", "postgresql+asyncpg://", 1)
            return url
        
        # Build async URL from individual components
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

# Initialize database settings
db_settings = DatabaseSettings()

# Environment detection
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
IS_PRODUCTION = ENVIRONMENT == "production"
IS_DEVELOPMENT = ENVIRONMENT == "development"

# Security settings
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Rate limiting
RATE_LIMIT_PER_MINUTE = 60
RATE_LIMIT_PER_HOUR = 1000

# File storage
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "temp/uploads")
EXPORT_DIR = os.getenv("EXPORT_DIR", "output/generated_models")
MAX_FILE_AGE_HOURS = 24  # Clean up old files after 24 hours
