"""Geospatial file database model."""

from datetime import datetime
from enum import Enum

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.core.database import Base


class FileStatus(str, Enum):
    """File processing status."""

    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class GeospatialFile(Base):
    """Geospatial file metadata model."""

    __tablename__ = "geospatial_files"

    id = Column(String, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    feature_count = Column(Integer, nullable=True)
    crs = Column(String, nullable=True)
    status = Column(String, nullable=False, default=FileStatus.PROCESSING.value)
    storage_path = Column(String, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<GeospatialFile(id={self.id}, filename={self.filename}, status={self.status})>"
