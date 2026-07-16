"""Prediction service for TrafficIQ."""

from pathlib import Path
from typing import Any
from backend.core.config import CONGESTION_PREDICTOR_PATH
from backend.core.logger import logger
from ml.prediction.congestion_predictor import load_model, predict_congestion

class CongestionPredictionService:
    """Service to load congestion prediction models and perform inference."""

    def __init__(self, model_path: Path = CONGESTION_PREDICTOR_PATH):
        self.model_path = model_path
        self._model = None

    def load_predictor(self) -> bool:
        """Load prediction model from file if it exists."""
        if not self.model_path.exists():
            logger.warning(f"Congestion predictor model file not found at: {self.model_path}")
            return False
        try:
            self._model = load_model(self.model_path)
            logger.info(f"Successfully loaded congestion predictor from: {self.model_path}")
            return True
        except Exception as error:
            logger.error(f"Failed to load congestion predictor from {self.model_path}: {error}")
            return False

    def predict(self, features: dict[str, Any]) -> str:
        """Run congestion prediction using loaded model. Returns fallback string if model not loaded."""
        if self._model is None:
            # Try lazy loading
            if not self.load_predictor():
                return "Model not trained"
        try:
            return predict_congestion(self._model, features)
        except Exception as error:
            logger.error(f"Congestion prediction query failed: {error}")
            return "Prediction error"
