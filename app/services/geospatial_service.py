"""Geospatial file processing service."""

from pathlib import Path

import geopandas as gpd

from app.core.logging import get_logger
from app.schemas.file import MeasurementResponse
from app.services.crs_service import get_measurement_crs
from app.services.measurement_service import calculate_measurements

logger = get_logger(__name__)


class GeospatialProcessingError(Exception):
    """Exception raised when geospatial processing fails."""

    pass


def process_geospatial_file(file_path: Path) -> tuple[gpd.GeoDataFrame, str | None]:
    """
    Read and validate a geospatial file.

    Args:
        file_path: Path to the geospatial file

    Returns:
        Tuple of (GeoDataFrame, original_crs_string)

    Raises:
        GeospatialProcessingError: If file cannot be read or is invalid
    """
    try:
        logger.info(f"Reading geospatial file: {file_path}")

        # Read the file using GeoPandas
        # GeoPandas can handle KML and Shapefiles
        gdf = gpd.read_file(file_path)

        if gdf.empty:
            raise GeospatialProcessingError("File contains no features")

        # Get original CRS
        original_crs = gdf.crs.to_string() if gdf.crs else None
        logger.info(f"Detected CRS: {original_crs or 'None'}")
        logger.info(f"Loaded {len(gdf)} features")

        return gdf, original_crs

    except Exception as e:
        logger.error(f"Failed to process geospatial file {file_path}: {e}")
        raise GeospatialProcessingError(f"Failed to read geospatial file: {str(e)}")


def calculate_file_measurements(
    file_id: str, file_path: Path
) -> MeasurementResponse:
    """
    Calculate measurements for all features in a geospatial file.

    Args:
        file_id: Unique file identifier
        file_path: Path to the geospatial file

    Returns:
        MeasurementResponse with all feature measurements

    Raises:
        GeospatialProcessingError: If processing fails
    """
    try:
        # Read the file
        gdf, original_crs = process_geospatial_file(file_path)

        # Determine measurement CRS
        measurement_crs_obj = get_measurement_crs(gdf)

        if measurement_crs_obj is None:
            logger.warning("Could not determine measurement CRS, measurements may be unavailable")
            measurement_crs_str = None
            # Use original GeoDataFrame without transformation
            gdf_transformed = gdf
        else:
            measurement_crs_str = measurement_crs_obj.to_string()
            logger.info(f"Selected measurement CRS: {measurement_crs_str}")

            # Transform to measurement CRS if different from original
            if gdf.crs is None or gdf.crs != measurement_crs_obj:
                logger.info("Transforming geometries to measurement CRS")
                if gdf.crs is None:
                    # Cannot transform without source CRS
                    logger.warning("Cannot transform - source CRS is missing")
                    gdf_transformed = gdf
                    measurement_crs_str = None
                else:
                    gdf_transformed = gdf.to_crs(measurement_crs_obj)
            else:
                gdf_transformed = gdf

        # Calculate measurements
        logger.info("Calculating measurements for features")
        measurements = calculate_measurements(gdf_transformed, measurement_crs_str)

        return MeasurementResponse(
            file_id=file_id,
            crs=original_crs,
            measurement_crs=measurement_crs_str,
            features=measurements,
        )

    except GeospatialProcessingError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error calculating measurements: {e}")
        raise GeospatialProcessingError(f"Failed to calculate measurements: {str(e)}")


def get_file_info(file_path: Path) -> tuple[int, str | None]:
    """
    Get basic information about a geospatial file.

    Args:
        file_path: Path to the geospatial file

    Returns:
        Tuple of (feature_count, crs_string)

    Raises:
        GeospatialProcessingError: If file cannot be read
    """
    try:
        gdf, original_crs = process_geospatial_file(file_path)
        return len(gdf), original_crs
    except Exception as e:
        raise GeospatialProcessingError(f"Failed to get file info: {str(e)}")
