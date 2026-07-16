"""Database connection setup for TrafficIQ."""

import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base

# Load environment variables from .env file
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

# Default to a local SQLite database if no DATABASE_URL is configured
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./trafficiq.db")

# For SQLite databases, we need to disable same-thread enforcement
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(DATABASE_URL, connect_args=connect_args)

Base = declarative_base()
