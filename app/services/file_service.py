"""File management service."""

import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.models.file import FileStatus, GeospatialFile
from app.services.geospatial_service import (
    GeospatialProcessingError,
    calculate_file_measurements,
    get_file_info,
)

logger = get_logger(__name__)


def generate_file_id() -> str:
    """Generate a unique file identifier."""
    return str(uuid.uuid4())


def get_file_storage_path(file_id: str) -> Path:
    """
    Get the storage directory path for a file.

    Args:
        file_id: Unique file identifier

    Returns:
        Path to the file's storage directory
    """
    storage_path = Path(settings.UPLOAD_DIR) / file_id
    storage_path.mkdir(parents=True, exist_ok=True)
    return storage_path


def save_uploaded_file(file_id: str, filename: str, content: bytes) -> Path:
    """
    Save uploaded file content to disk.

    Args:
        file_id: Unique file identifier
        filename: Original filename
        content: File content

    Returns:
        Path to the saved file
    """
    storage_path = get_file_storage_path(file_id)
    file_path = storage_path / filename

    with open(file_path, "wb") as f:
        f.write(content)

    logger.info(f"Saved file to: {file_path}")
    return file_path


def create_file_record(
    db: Session,
    file_id: str,
    filename: str,
    file_type: str,
    storage_path: str,
) -> GeospatialFile:
    """
    Create a database record for an uploaded file.

    Args:
        db: Database session
        file_id: Unique file identifier
        filename: Original filename
        file_type: File type (KML or Shapefile)
        storage_path: Path to stored file

    Returns:
        Created GeospatialFile instance
    """
    db_file = GeospatialFile(
        id=file_id,
        filename=filename,
        file_type=file_type,
        storage_path=storage_path,
        status=FileStatus.PROCESSING.value,
    )

    db.add(db_file)
    db.commit()
    db.refresh(db_file)

    logger.info(f"Created file record: {file_id}")
    return db_file


def update_file_status(
    db: Session,
    file_id: str,
    status: FileStatus,
    feature_count: int | None = None,
    crs: str | None = None,
    error_message: str | None = None,
) -> GeospatialFile | None:
    """
    Update file processing status.

    Args:
        db: Database session
        file_id: File identifier
        status: New status
        feature_count: Number of features (optional)
        crs: CRS string (optional)
        error_message: Error message if failed (optional)

    Returns:
        Updated GeospatialFile or None if not found
    """
    db_file = db.query(GeospatialFile).filter(GeospatialFile.id == file_id).first()

    if db_file:
        db_file.status = status.value
        if feature_count is not None:
            db_file.feature_count = feature_count
        if crs is not None:
            db_file.crs = crs
        if error_message is not None:
            db_file.error_message = error_message

        db.commit()
        db.refresh(db_file)
        logger.info(f"Updated file {file_id} status to {status.value}")

    return db_file


def get_file_by_id(db: Session, file_id: str) -> GeospatialFile | None:
    """
    Retrieve a file record by ID.

    Args:
        db: Database session
        file_id: File identifier

    Returns:
        GeospatialFile instance or None
    """
    return db.query(GeospatialFile).filter(GeospatialFile.id == file_id).first()


def process_uploaded_file(db: Session, file_id: str, file_path: Path) -> None:
    """
    Process an uploaded geospatial file.

    This function extracts metadata and updates the database record.

    Args:
        db: Database session
        file_id: File identifier
        file_path: Path to the uploaded file
    """
    try:
        # Get file information
        feature_count, crs = get_file_info(file_path)

        # Update database record
        update_file_status(
            db=db,
            file_id=file_id,
            status=FileStatus.COMPLETED,
            feature_count=feature_count,
            crs=crs,
        )

        logger.info(f"Successfully processed file {file_id}")

    except GeospatialProcessingError as e:
        logger.error(f"Processing failed for file {file_id}: {e}")
        update_file_status(
            db=db,
            file_id=file_id,
            status=FileStatus.FAILED,
            error_message=str(e),
        )
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing file {file_id}: {e}")
        update_file_status(
            db=db,
            file_id=file_id,
            status=FileStatus.FAILED,
            error_message=f"Unexpected error: {str(e)}",
        )
        raise
