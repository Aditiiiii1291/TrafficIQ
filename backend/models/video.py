"""SQLAlchemy model for uploaded video logs."""

import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from backend.database.database import Base

class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True, nullable=False)
    upload_time = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    status = Column(String, default="uploaded", nullable=False)  # e.g., uploaded, processing, completed, failed
    duration = Column(Float, nullable=True)
    processing_time = Column(Float, nullable=True)

    processing_results = relationship("ProcessingResult", back_populates="video", cascade="all, delete-orphan")
