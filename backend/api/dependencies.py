"""FastAPI API dependencies for TrafficIQ."""

from backend.core.logger import logger

def get_logger():
    """Dependency injection provider for the central logger."""
    return logger
