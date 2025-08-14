"""
Production logging configuration for PlanCast.

Provides structured logging with different levels for development and production.
Essential for debugging CubiCasa5K issues and monitoring 24/7 operations.
"""

import logging
import logging.handlers
import sys
import structlog
from pathlib import Path
from typing import Optional, Dict, Any
import json
from datetime import datetime


class PlanCastLogger:
    """
    Production-ready logging system for PlanCast.
    
    Features:
    - Structured logging with JSON output
    - Different configurations for dev/prod
    - File rotation for production
    - Performance monitoring
    - Error tracking integration
    """
    
    def __init__(self, 
                 environment: str = "development",
                 log_level: str = "INFO",
                 log_dir: Optional[str] = None):
        """
        Initialize logging system.
        
        Args:
            environment: "development" or "production"
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
            log_dir: Directory for log files (production only)
        """
        self.environment = environment
        self.log_level = getattr(logging, log_level.upper())
        self.log_dir = Path(log_dir) if log_dir else Path("logs")
        
        # Create log directory
        if environment == "production":
            self.log_dir.mkdir(exist_ok=True)
        
        self._setup_logging()
    
    def _setup_logging(self):
        """Configure logging based on environment."""
        if self.environment == "development":
            self._setup_development_logging()
        else:
            self._setup_production_logging()
    
    def _setup_development_logging(self):
        """Setup colorful, human-readable logging for development."""
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.StackInfoRenderer(),
                structlog.dev.set_exc_info,
                structlog.processors.TimeStamper(fmt="ISO"),
                structlog.dev.ConsoleRenderer(colors=True)
            ],
            wrapper_class=structlog.make_filtering_bound_logger(self.log_level),
            logger_factory=structlog.WriteLoggerFactory(),
            cache_logger_on_first_use=True,
        )
        
        # Configure standard library logging
        logging.basicConfig(
            format="%(message)s",
            stream=sys.stdout,
            level=self.log_level,
        )
        
        # Reduce noise from third-party libraries
        logging.getLogger("PIL").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("requests").setLevel(logging.WARNING)
    
    def _setup_production_logging(self):
        """Setup JSON logging with file rotation for production."""
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.TimeStamper(fmt="ISO"),
                structlog.processors.JSONRenderer()
            ],
            wrapper_class=structlog.make_filtering_bound_logger(self.log_level),
            logger_factory=structlog.WriteLoggerFactory(),
            cache_logger_on_first_use=True,
        )
        
        # Setup file handlers with rotation
        self._setup_file_handlers()
        
        # Reduce third-party noise
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("PIL").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    def _setup_file_handlers(self):
        """Setup rotating file handlers for production."""
        # Main application log
        app_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "plancast.log",
            maxBytes=50 * 1024 * 1024,  # 50MB
            backupCount=10
        )
        app_handler.setLevel(self.log_level)
        
        # Error-only log
        error_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "errors.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        
        # Performance log
        perf_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "performance.log",
            maxBytes=20 * 1024 * 1024,  # 20MB
            backupCount=5
        )
        perf_handler.setLevel(logging.INFO)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)
        root_logger.addHandler(app_handler)
        root_logger.addHandler(error_handler)
        
        # Configure performance logger
        perf_logger = logging.getLogger("performance")
        perf_logger.addHandler(perf_handler)
        perf_logger.propagate = False


class PerformanceLogger:
    """
    Performance monitoring for critical operations.
    Essential for monitoring CubiCasa5K processing times and 3D generation performance.
    """
    
    def __init__(self):
        self.logger = structlog.get_logger("performance")
    
    def log_processing_time(self, 
                          operation: str, 
                          duration_seconds: float,
                          job_id: str,
                          metadata: Optional[Dict[str, Any]] = None):
        """
        Log processing time for operations.
        
        Args:
            operation: Operation name (e.g., "cubicasa_processing", "3d_generation")
            duration_seconds: Time taken in seconds
            job_id: Processing job ID
            metadata: Additional metadata (file_size, dimensions, etc.)
        """
        log_data = {
            "operation": operation,
            "duration_seconds": duration_seconds,
            "job_id": job_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if metadata:
            log_data.update(metadata)
        
        # Determine log level based on performance
        if operation == "cubicasa_processing":
            # CubiCasa5K should complete in < 30 seconds
            if duration_seconds > 30:
                self.logger.warning("Slow CubiCasa5K processing", **log_data)
            elif duration_seconds > 60:
                self.logger.error("Very slow CubiCasa5K processing", **log_data)
            else:
                self.logger.info("CubiCasa5K processing completed", **log_data)
        
        elif operation == "3d_generation":
            # 3D generation should complete in < 10 seconds
            if duration_seconds > 10:
                self.logger.warning("Slow 3D generation", **log_data)
            elif duration_seconds > 30:
                self.logger.error("Very slow 3D generation", **log_data)
            else:
                self.logger.info("3D generation completed", **log_data)
        
        else:
            self.logger.info(f"{operation} completed", **log_data)
    
    def log_error(self, 
                  operation: str, 
                  error: str,
                  job_id: str,
                  metadata: Optional[Dict[str, Any]] = None):
        """
        Log processing errors.
        
        Args:
            operation: Operation that failed
            error: Error message
            job_id: Processing job ID
            metadata: Additional error context
        """
        log_data = {
            "operation": operation,
            "error": error,
            "job_id": job_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if metadata:
            log_data.update(metadata)
        
        self.logger.error(f"{operation} failed", **log_data)


class CubiCasaLogger:
    """
    Specialized logger for CubiCasa5K operations.
    Critical for debugging dependency issues and model performance.
    """
    
    def __init__(self):
        self.logger = structlog.get_logger("cubicasa")
        self.perf_logger = PerformanceLogger()
    
    def log_model_loading(self, success: bool, load_time: float, error: Optional[str] = None):
        """Log CubiCasa5K model loading."""
        if success:
            self.logger.info(
                "CubiCasa5K model loaded successfully",
                load_time_seconds=load_time,
                model_status="ready"
            )
        else:
            self.logger.error(
                "CubiCasa5K model loading failed",
                load_time_seconds=load_time,
                error=error,
                model_status="failed"
            )
    
    def log_dependency_check(self, dependencies: Dict[str, Any]):
        """Log dependency versions for debugging."""
        self.logger.info(
            "CubiCasa5K dependencies",
            **dependencies
        )
    
    def log_processing_start(self, job_id: str, image_dimensions: tuple, file_size: int):
        """Log start of CubiCasa5K processing."""
        self.logger.info(
            "Starting CubiCasa5K processing",
            job_id=job_id,
            image_width=image_dimensions[0],
            image_height=image_dimensions[1],
            file_size_bytes=file_size
        )
    
    def log_processing_result(self, 
                            job_id: str, 
                            success: bool,
                            processing_time: float,
                            wall_points: int = 0,
                            rooms_detected: int = 0,
                            error: Optional[str] = None):
        """Log CubiCasa5K processing results."""
        if success:
            self.logger.info(
                "CubiCasa5K processing successful",
                job_id=job_id,
                processing_time_seconds=processing_time,
                wall_points_detected=wall_points,
                rooms_detected=rooms_detected
            )
            
            # Log performance metrics
            self.perf_logger.log_processing_time(
                "cubicasa_processing",
                processing_time,
                job_id,
                {
                    "wall_points": wall_points,
                    "rooms_detected": rooms_detected
                }
            )
        else:
            self.logger.error(
                "CubiCasa5K processing failed",
                job_id=job_id,
                processing_time_seconds=processing_time,
                error=error
            )
            
            # Log error
            self.perf_logger.log_error(
                "cubicasa_processing",
                error or "Unknown error",
                job_id
            )


# Global logger instances
plancast_logger: Optional[PlanCastLogger] = None
performance_logger = PerformanceLogger()
cubicasa_logger = CubiCasaLogger()


def setup_logging(environment: str = "development", 
                 log_level: str = "INFO",
                 log_dir: Optional[str] = None):
    """
    Setup global logging configuration.
    
    Args:
        environment: "development" or "production"
        log_level: Logging level
        log_dir: Log directory for production
    """
    global plancast_logger
    plancast_logger = PlanCastLogger(environment, log_level, log_dir)


def get_logger(name: str = None):
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (optional)
        
    Returns:
        Structured logger
    """
    return structlog.get_logger(name)


# Convenience functions
def log_job_start(job_id: str, operation: str, metadata: Optional[Dict] = None):
    """Log the start of a processing job."""
    logger = get_logger("jobs")
    log_data = {"job_id": job_id, "operation": operation, "status": "started"}
    if metadata:
        log_data.update(metadata)
    logger.info(f"Job started: {operation}", **log_data)


def log_job_complete(job_id: str, operation: str, duration: float, metadata: Optional[Dict] = None):
    """Log the completion of a processing job."""
    logger = get_logger("jobs")
    log_data = {
        "job_id": job_id, 
        "operation": operation, 
        "status": "completed",
        "duration_seconds": duration
    }
    if metadata:
        log_data.update(metadata)
    logger.info(f"Job completed: {operation}", **log_data)


def log_job_error(job_id: str, operation: str, error: str, metadata: Optional[Dict] = None):
    """Log a processing job error."""
    logger = get_logger("jobs")
    log_data = {
        "job_id": job_id, 
        "operation": operation, 
        "status": "failed",
        "error": error
    }
    if metadata:
        log_data.update(metadata)
    logger.error(f"Job failed: {operation}", **log_data)


# Initialize with development settings by default
setup_logging()