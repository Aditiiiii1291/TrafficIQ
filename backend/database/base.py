"""Declarative Base importing all model classes for Alembic migrations."""

from backend.database.database import Base
from backend.models.video import Video
from backend.models.processing import ProcessingResult
from backend.models.detection import VehicleDetection
from backend.models.analytics import AnalyticsSummary
from backend.models.user import User
