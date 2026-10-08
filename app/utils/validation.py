"""File validation utilities."""

from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Allowed file extensions
ALLOWED_EXTENSIONS = {".kml", ".zip"}

# Allowed MIME types
ALLOWED_MIME_TYPES = {
    "application/vnd.google-earth.kml+xml",
    "application/xml",
    "text/xml",
    "application/zip",
    "application/x-zip-compressed",
}


def validate_file_extension(filename: str) -> str:
    """
    Validate file extension.

    Args:
        filename: Name of the file

    Returns:
        File extension (lowercase with dot)

    Raises:
        HTTPException: If extension is not allowed
    """
    file_path = Path(filename)
    extension = file_path.suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        logger.warning(f"Unsupported file extension: {extension}")
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Only .kml and .zip files are supported.",
        )

    return extension


def validate_file_size(file: UploadFile) -> None:
    """
    Validate file size.

    Args:
        file: Uploaded file

    Raises:
        HTTPException: If file is too large
    """
    # Read file size by seeking to end
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning

    max_size = settings.max_upload_size_bytes

    if file_size > max_size:
        logger.warning(f"File too large: {file_size} bytes (max: {max_size})")
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE_MB}MB.",
        )

    logger.info(f"File size: {file_size} bytes")


def validate_upload_file(file: UploadFile) -> str:
    """
    Validate uploaded file.

    Args:
        file: Uploaded file

    Returns:
        File type ("KML" or "Shapefile")

    Raises:
        HTTPException: If file is invalid
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    # Validate extension
    extension = validate_file_extension(file.filename)

    # Validate size
    validate_file_size(file)

    # Determine file type
    if extension == ".kml":
        file_type = "KML"
    elif extension == ".zip":
        file_type = "Shapefile"
    else:
        file_type = "Unknown"

    logger.info(f"File validated: {file.filename} (type: {file_type})")
    return file_type


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal and other issues.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Get just the filename, removing any directory components
    safe_name = Path(filename).name

    # Remove any remaining dangerous characters
    safe_name = safe_name.replace("..", "").replace("/", "").replace("\\", "")

    return safe_name
