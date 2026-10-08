"""Measurement calculation service for geospatial features."""

import geopandas as gpd
from shapely.geometry import LineString, Point, Polygon

from app.core.logging import get_logger
from app.schemas.file import FeatureMeasurement, Measurement

logger = get_logger(__name__)


def calculate_measurements(
    gdf: gpd.GeoDataFrame, measurement_crs: str | None
) -> list[FeatureMeasurement]:
    """
    Calculate measurements for all features in a GeoDataFrame.

    Args:
        gdf: GeoDataFrame with geometries (should already be transformed to measurement CRS)
        measurement_crs: CRS string used for measurements

    Returns:
        List of FeatureMeasurement objects
    """
    measurements = []

    for idx, row in gdf.iterrows():
        geometry = row.geometry
        properties = row.drop("geometry").to_dict()

        # Clean up properties - convert numpy types to Python types
        properties = _clean_properties(properties)

        feature_measurement = _calculate_feature_measurement(
            feature_id=int(idx),
            geometry=geometry,
            properties=properties,
        )

        measurements.append(feature_measurement)

    logger.info(f"Calculated measurements for {len(measurements)} features")
    return measurements


def _calculate_feature_measurement(
    feature_id: int, geometry, properties: dict
) -> FeatureMeasurement:
    """
    Calculate measurement for a single feature.

    Args:
        feature_id: Feature index
        geometry: Shapely geometry object
        properties: Feature properties

    Returns:
        FeatureMeasurement object
    """
    geometry_type = geometry.geom_type

    # Handle empty or None geometries
    if geometry is None or geometry.is_empty:
        return FeatureMeasurement(
            feature_id=feature_id,
            geometry_type=geometry_type if geometry else "Unknown",
            measurement=None,
            measurement_status="EMPTY_GEOMETRY",
            properties=properties,
        )

    # Polygon - calculate area
    if isinstance(geometry, Polygon):
        try:
            area = float(geometry.area)  # Explicitly convert to Python float
            return FeatureMeasurement(
                feature_id=feature_id,
                geometry_type=geometry_type,
                measurement=Measurement(type="area", value=round(area, 2), unit="m²"),
                properties=properties,
            )
        except Exception as e:
            logger.warning(f"Failed to calculate area for feature {feature_id}: {e}")
            return FeatureMeasurement(
                feature_id=feature_id,
                geometry_type=geometry_type,
                measurement=None,
                measurement_status="CALCULATION_ERROR",
                properties=properties,
            )

    # LineString - calculate length
    elif isinstance(geometry, LineString):
        try:
            length = float(geometry.length)  # Explicitly convert to Python float
            return FeatureMeasurement(
                feature_id=feature_id,
                geometry_type=geometry_type,
                measurement=Measurement(type="length", value=round(length, 2), unit="m"),
                properties=properties,
            )
        except Exception as e:
            logger.warning(f"Failed to calculate length for feature {feature_id}: {e}")
            return FeatureMeasurement(
                feature_id=feature_id,
                geometry_type=geometry_type,
                measurement=None,
                measurement_status="CALCULATION_ERROR",
                properties=properties,
            )

    # Point - no measurement
    elif isinstance(geometry, Point):
        return FeatureMeasurement(
            feature_id=feature_id,
            geometry_type=geometry_type,
            measurement=None,
            properties=properties,
        )

    # Unsupported geometry types (MultiPolygon, MultiLineString, GeometryCollection, etc.)
    else:
        logger.info(f"Unsupported geometry type for feature {feature_id}: {geometry_type}")
        return FeatureMeasurement(
            feature_id=feature_id,
            geometry_type=geometry_type,
            measurement=None,
            measurement_status="UNSUPPORTED_GEOMETRY",
            properties=properties,
        )


def _clean_properties(properties: dict) -> dict:
    """
    Clean feature properties by converting numpy types to Python types.

    Args:
        properties: Raw properties dictionary

    Returns:
        Cleaned properties dictionary
    """
    import json
    import numpy as np
    
    cleaned = {}
    for key, value in properties.items():
        # Skip None values
        if value is None:
            cleaned[key] = None
            continue

        # Convert numpy types to Python types
        if isinstance(value, (np.integer, np.floating)):
            cleaned[key] = value.item()
        elif isinstance(value, np.ndarray):
            cleaned[key] = value.tolist()
        elif hasattr(value, "item"):
            try:
                cleaned[key] = value.item()
            except (AttributeError, ValueError):
                cleaned[key] = str(value)
        else:
            cleaned[key] = value
    
    # Force everything through JSON to ensure all types are JSON-safe
    try:
        return json.loads(json.dumps(cleaned))
    except (TypeError, ValueError):
        # If JSON serialization fails, convert everything to strings
        return {k: str(v) if v is not None else None for k, v in cleaned.items()}
