"""File upload and measurement API endpoints."""

from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging import get_logger
from app.schemas.file import FileResponse, MeasurementResponse
from app.services.file_service import (
    create_file_record,
    generate_file_id,
    get_file_by_id,
    process_uploaded_file,
    save_uploaded_file,
)
from app.services.geospatial_service import (
    GeospatialProcessingError,
    calculate_file_measurements,
)
from app.utils.validation import sanitize_filename, validate_upload_file
from app.utils.zip_utils import process_shapefile_zip

logger = get_logger(__name__)

router = APIRouter(prefix="/api/files", tags=["files"])


@router.post("/", response_model=FileResponse, status_code=201)
async def upload_file(
    file: UploadFile = File(..., description="Geospatial file (.kml or .zip with Shapefile)"),
    db: Session = Depends(get_db),
) -> FileResponse:
    """
    Upload and process a geospatial file.

    Accepts:
    - KML files (.kml)
    - ZIP files containing a Shapefile (.zip)

    Returns file information including:
    - Unique file ID
    - Feature count
    - Coordinate Reference System (CRS)
    - Processing status
    """
    logger.info(f"Upload received: {file.filename}")

    # Validate file
    file_type = validate_upload_file(file)

    # Generate unique file ID
    file_id = generate_file_id()

    # Sanitize filename
    safe_filename = sanitize_filename(file.filename or "upload")

    try:
        # Read file content
        content = await file.read()

        # Save uploaded file
        file_path = save_uploaded_file(file_id, safe_filename, content)

        # For ZIP files, extract and find Shapefile
        if file_type == "Shapefile":
            try:
                file_path = process_shapefile_zip(file_path)
                logger.info(f"Extracted Shapefile: {file_path}")
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Failed to process Shapefile ZIP: {e}")
                raise HTTPException(
                    status_code=400,
                    detail="Failed to process Shapefile ZIP.",
                )

        # Create database record
        db_file = create_file_record(
            db=db,
            file_id=file_id,
            filename=safe_filename,
            file_type=file_type,
            storage_path=str(file_path),
        )

        # Process the file (extract metadata)
        try:
            process_uploaded_file(db, file_id, file_path)
            # Refresh to get updated data
            db.refresh(db_file)
        except GeospatialProcessingError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Unexpected error during processing: {e}")
            raise HTTPException(
                status_code=500,
                detail="An unexpected error occurred during file processing.",
            )

        logger.info(f"File processed successfully: {file_id}")
        return FileResponse.model_validate(db_file)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload file: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to upload and process file.",
        )


@router.get("/{file_id}", response_model=FileResponse)
def get_file_info(
    file_id: str,
    db: Session = Depends(get_db),
) -> FileResponse:
    """
    Get information about an uploaded file.

    Returns:
    - File metadata
    - Processing status
    - Feature count
    - CRS information
    """
    logger.info(f"Retrieving file info: {file_id}")

    db_file = get_file_by_id(db, file_id)

    if not db_file:
        logger.warning(f"File not found: {file_id}")
        raise HTTPException(status_code=404, detail="File not found.")

    return FileResponse.model_validate(db_file)


@router.get("/{file_id}/measurements/", response_model=MeasurementResponse)
def get_file_measurements(
    file_id: str,
    db: Session = Depends(get_db),
) -> MeasurementResponse:
    """
    Get measurements for all features in a file.

    Returns measurements for each feature:
    - Polygon: area in square meters (m²)
    - LineString: length in meters (m)
    - Point: no measurement
    - Unsupported geometries: marked as UNSUPPORTED_GEOMETRY

    The API automatically transforms coordinates to an appropriate
    projected CRS (typically UTM) for accurate measurements.
    """
    logger.info(f"Calculating measurements for file: {file_id}")

    # Get file record
    db_file = get_file_by_id(db, file_id)

    if not db_file:
        logger.warning(f"File not found: {file_id}")
        raise HTTPException(status_code=404, detail="File not found.")

    # Check file status
    if db_file.status == "PROCESSING":
        raise HTTPException(
            status_code=400,
            detail="File is still being processed. Please try again later.",
        )

    if db_file.status == "FAILED":
        raise HTTPException(
            status_code=400,
            detail=f"File processing failed: {db_file.error_message or 'Unknown error'}",
        )

    # Calculate measurements
    try:
        file_path = Path(db_file.storage_path)

        if not file_path.exists():
            logger.error(f"File not found on disk: {file_path}")
            raise HTTPException(
                status_code=500,
                detail="File data not found on server.",
            )

        measurements = calculate_file_measurements(file_id, file_path)
        logger.info(f"Successfully calculated measurements for {len(measurements.features)} features")
        return measurements

    except GeospatialProcessingError as e:
        logger.error(f"Failed to calculate measurements: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error calculating measurements: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while calculating measurements.",
        )
