"""CRS (Coordinate Reference System) transformation service."""

import math

import geopandas as gpd
from pyproj import CRS
from shapely.geometry import Point

from app.core.logging import get_logger

logger = get_logger(__name__)


def get_measurement_crs(gdf: gpd.GeoDataFrame) -> CRS | None:
    """
    Determine the appropriate CRS for measurements.

    For geographic CRS (like EPSG:4326), selects an appropriate UTM zone.
    For projected CRS with linear units, uses the existing CRS.
    For missing CRS, returns None.

    Args:
        gdf: GeoDataFrame with geometries

    Returns:
        CRS object suitable for measurements, or None if CRS cannot be determined
    """
    if gdf.crs is None:
        logger.warning("GeoDataFrame has no CRS defined")
        return None

    source_crs = gdf.crs

    # Check if CRS is geographic (lat/lon)
    if source_crs.is_geographic:
        logger.info(f"Source CRS {source_crs.to_string()} is geographic, selecting UTM zone")
        return _get_utm_crs_from_gdf(gdf)

    # Check if CRS is projected with linear units
    if source_crs.is_projected:
        # Verify it has linear units (meters, feet, etc.)
        axis_info = source_crs.axis_info
        if axis_info and len(axis_info) >= 2:
            unit = axis_info[0].unit_name.lower()
            if "meter" in unit or "metre" in unit or "foot" in unit or "feet" in unit:
                logger.info(f"Source CRS {source_crs.to_string()} is already projected with linear units")
                return source_crs

    # Fallback: try to determine UTM from centroid
    logger.info(f"CRS {source_crs.to_string()} type unclear, attempting UTM selection")
    return _get_utm_crs_from_gdf(gdf)


def _get_utm_crs_from_gdf(gdf: gpd.GeoDataFrame) -> CRS:
    """
    Determine appropriate UTM CRS based on GeoDataFrame centroid.

    Args:
        gdf: GeoDataFrame with geometries

    Returns:
        UTM CRS object
    """
    # Ensure we're working with geographic coordinates
    if gdf.crs and not gdf.crs.is_geographic:
        # Transform to WGS84 to get lat/lon
        gdf_wgs84 = gdf.to_crs("EPSG:4326")
    else:
        gdf_wgs84 = gdf

    # Calculate centroid of all geometries
    centroid = gdf_wgs84.geometry.unary_union.centroid
    lon, lat = centroid.x, centroid.y

    logger.info(f"Dataset centroid: lat={lat:.4f}, lon={lon:.4f}")

    # Calculate UTM zone
    utm_zone = _calculate_utm_zone(lon)
    is_northern = lat >= 0

    # Construct EPSG code
    # Northern hemisphere: EPSG:326xx
    # Southern hemisphere: EPSG:327xx
    if is_northern:
        epsg_code = 32600 + utm_zone
    else:
        epsg_code = 32700 + utm_zone

    utm_crs = CRS.from_epsg(epsg_code)
    logger.info(
        f"Selected UTM zone {utm_zone}{'N' if is_northern else 'S'} (EPSG:{epsg_code})"
    )

    return utm_crs


def _calculate_utm_zone(longitude: float) -> int:
    """
    Calculate UTM zone from longitude.

    Args:
        longitude: Longitude in degrees

    Returns:
        UTM zone number (1-60)
    """
    # UTM zones are 6 degrees wide, starting at -180
    # Zone 1 is -180 to -174, Zone 31 is 0 to 6, etc.
    zone = int((longitude + 180) / 6) + 1

    # Handle edge case at 180/-180
    if zone > 60:
        zone = 60
    elif zone < 1:
        zone = 1

    return zone


def is_crs_suitable_for_measurement(crs: CRS | None) -> bool:
    """
    Check if a CRS is suitable for direct measurement.

    Args:
        crs: CRS object to check

    Returns:
        True if CRS can be used for measurements, False otherwise
    """
    if crs is None:
        return False

    if not crs.is_projected:
        return False

    # Check for linear units
    axis_info = crs.axis_info
    if axis_info and len(axis_info) >= 2:
        unit = axis_info[0].unit_name.lower()
        return "meter" in unit or "metre" in unit or "foot" in unit or "feet" in unit

    return False
