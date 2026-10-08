"""ZIP file handling utilities."""

import zipfile
from pathlib import Path

from fastapi import HTTPException

from app.core.logging import get_logger

logger = get_logger(__name__)

# Required Shapefile extensions
SHAPEFILE_REQUIRED_EXTENSIONS = {".shp", ".shx", ".dbf"}
SHAPEFILE_OPTIONAL_EXTENSIONS = {".prj", ".cpg", ".sbn", ".sbx", ".shp.xml"}


def validate_zip_file(zip_path: Path) -> None:
    """
    Validate that a file is a valid ZIP archive.

    Args:
        zip_path: Path to the ZIP file

    Raises:
        HTTPException: If ZIP file is invalid
    """
    if not zipfile.is_zipfile(zip_path):
        logger.warning(f"Invalid ZIP file: {zip_path}")
        raise HTTPException(status_code=400, detail="Invalid ZIP file.")


def extract_zip_safely(zip_path: Path, extract_to: Path) -> None:
    """
    Safely extract ZIP file, preventing path traversal attacks.

    Args:
        zip_path: Path to the ZIP file
        extract_to: Directory to extract to

    Raises:
        HTTPException: If extraction fails or contains malicious paths
    """
    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            # Check all file paths for safety
            for member in zip_ref.namelist():
                # Prevent path traversal
                member_path = Path(extract_to) / member
                if not str(member_path.resolve()).startswith(str(extract_to.resolve())):
                    logger.error(f"Potentially malicious path in ZIP: {member}")
                    raise HTTPException(
                        status_code=400,
                        detail="ZIP file contains invalid paths.",
                    )

            # Extract all files
            zip_ref.extractall(extract_to)
            logger.info(f"Extracted ZIP to: {extract_to}")

    except zipfile.BadZipFile:
        logger.error(f"Bad ZIP file: {zip_path}")
        raise HTTPException(status_code=400, detail="Corrupted ZIP file.")
    except Exception as e:
        logger.error(f"Failed to extract ZIP: {e}")
        raise HTTPException(status_code=400, detail="Failed to extract ZIP file.")


def find_shapefile_in_directory(directory: Path) -> Path:
    """
    Find the main Shapefile (.shp) in a directory.

    Args:
        directory: Directory to search

    Returns:
        Path to the .shp file

    Raises:
        HTTPException: If no valid Shapefile is found
    """
    # Find all .shp files (recursively)
    shp_files = list(directory.rglob("*.shp"))

    if not shp_files:
        logger.warning(f"No .shp file found in {directory}")
        raise HTTPException(
            status_code=400,
            detail="ZIP file does not contain a Shapefile (.shp file not found).",
        )

    if len(shp_files) > 1:
        logger.info(f"Multiple .shp files found, using first: {shp_files[0]}")

    shp_file = shp_files[0]

    # Validate required components exist
    validate_shapefile_components(shp_file)

    return shp_file


def validate_shapefile_components(shp_path: Path) -> None:
    """
    Validate that required Shapefile components exist.

    Args:
        shp_path: Path to the .shp file

    Raises:
        HTTPException: If required components are missing
    """
    base_path = shp_path.with_suffix("")
    missing_components = []

    for ext in SHAPEFILE_REQUIRED_EXTENSIONS:
        component_path = base_path.with_suffix(ext)
        if not component_path.exists():
            missing_components.append(ext)

    if missing_components:
        logger.warning(f"Missing Shapefile components: {missing_components}")
        raise HTTPException(
            status_code=400,
            detail=f"Incomplete Shapefile. Missing required files: {', '.join(missing_components)}",
        )

    # Check for .prj (optional but recommended)
    prj_path = base_path.with_suffix(".prj")
    if not prj_path.exists():
        logger.warning(f"Shapefile missing .prj file: {shp_path}")

    logger.info(f"Validated Shapefile components for: {shp_path}")


def process_shapefile_zip(zip_path: Path) -> Path:
    """
    Process a ZIP file containing a Shapefile.

    Args:
        zip_path: Path to the ZIP file

    Returns:
        Path to the main .shp file

    Raises:
        HTTPException: If ZIP is invalid or doesn't contain a valid Shapefile
    """
    # Validate ZIP
    validate_zip_file(zip_path)

    # Create extraction directory
    extract_dir = zip_path.parent / "extracted"
    extract_dir.mkdir(exist_ok=True)

    # Extract safely
    extract_zip_safely(zip_path, extract_dir)

    # Find and validate Shapefile
    shp_file = find_shapefile_in_directory(extract_dir)

    logger.info(f"Successfully processed Shapefile ZIP: {shp_file}")
    return shp_file
