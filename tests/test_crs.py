"""Tests for CRS service."""

import pytest
from pyproj import CRS

from app.services.crs_service import (
    _calculate_utm_zone,
    get_measurement_crs,
    is_crs_suitable_for_measurement,
)


def test_calculate_utm_zone():
    """Test UTM zone calculation."""
    # Test known locations
    assert _calculate_utm_zone(0) == 31  # Prime meridian
    assert _calculate_utm_zone(77.6) == 43  # Bangalore, India
    assert _calculate_utm_zone(-122.4) == 10  # San Francisco, USA
    assert _calculate_utm_zone(180) == 60  # Edge case
    assert _calculate_utm_zone(-180) == 1  # Edge case


def test_get_measurement_crs_geographic(sample_polygon_gdf):
    """Test measurement CRS selection for geographic CRS."""
    # Input is EPSG:4326 (geographic)
    result_crs = get_measurement_crs(sample_polygon_gdf)

    assert result_crs is not None
    assert result_crs.is_projected
    assert "UTM" in result_crs.name or "32643" in result_crs.to_string()


def test_get_measurement_crs_projected():
    """Test measurement CRS selection for already projected CRS."""
    import geopandas as gpd
    from shapely.geometry import Polygon

    # Create a polygon in UTM zone 43N (EPSG:32643)
    polygon = Polygon([(0, 0), (1000, 0), (1000, 1000), (0, 1000), (0, 0)])
    gdf = gpd.GeoDataFrame({"geometry": [polygon]}, crs="EPSG:32643")

    result_crs = get_measurement_crs(gdf)

    assert result_crs is not None
    assert result_crs.is_projected
    # Should use the same CRS since it's already projected with meters
    assert result_crs.to_epsg() == 32643


def test_get_measurement_crs_no_crs():
    """Test measurement CRS selection when no CRS is defined."""
    import geopandas as gpd
    from shapely.geometry import Point

    # Create GeoDataFrame without CRS
    gdf = gpd.GeoDataFrame({"geometry": [Point(0, 0)]})

    result_crs = get_measurement_crs(gdf)

    assert result_crs is None


def test_is_crs_suitable_for_measurement():
    """Test CRS suitability check."""
    # Geographic CRS - not suitable
    geographic_crs = CRS.from_epsg(4326)
    assert not is_crs_suitable_for_measurement(geographic_crs)

    # Projected CRS with meters - suitable
    utm_crs = CRS.from_epsg(32643)
    assert is_crs_suitable_for_measurement(utm_crs)

    # None - not suitable
    assert not is_crs_suitable_for_measurement(None)


def test_utm_zone_northern_hemisphere(sample_polygon_gdf):
    """Test that northern hemisphere gets correct UTM zone."""
    # Bangalore is in northern hemisphere
    result_crs = get_measurement_crs(sample_polygon_gdf)

    assert result_crs is not None
    # EPSG:32643 is UTM zone 43N
    assert result_crs.to_epsg() == 32643


def test_utm_zone_southern_hemisphere():
    """Test that southern hemisphere gets correct UTM zone."""
    import geopandas as gpd
    from shapely.geometry import Point

    # Create point in southern hemisphere (Sydney, Australia)
    point = Point(151.2, -33.9)
    gdf = gpd.GeoDataFrame({"geometry": [point]}, crs="EPSG:4326")

    result_crs = get_measurement_crs(gdf)

    assert result_crs is not None
    assert result_crs.is_projected
    # Should be in 327xx range (southern hemisphere)
    epsg = result_crs.to_epsg()
    assert 32700 <= epsg <= 32760
