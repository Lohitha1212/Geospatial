"""Tests for measurement calculations."""

import geopandas as gpd
import pytest
from shapely.geometry import GeometryCollection, LineString, MultiPolygon, Point, Polygon

from app.services.measurement_service import (
    _calculate_feature_measurement,
    calculate_measurements,
)


def test_polygon_area_calculation():
    """Test area calculation for polygons."""
    # Create a simple square polygon (100m x 100m) in a projected CRS
    polygon = Polygon([(0, 0), (100, 0), (100, 100), (0, 100), (0, 0)])
    gdf = gpd.GeoDataFrame({"geometry": [polygon]}, crs="EPSG:32643")

    measurements = calculate_measurements(gdf, "EPSG:32643")

    assert len(measurements) == 1
    assert measurements[0].geometry_type == "Polygon"
    assert measurements[0].measurement is not None
    assert measurements[0].measurement.type == "area"
    assert measurements[0].measurement.unit == "m²"
    # Area should be approximately 10,000 m²
    assert 9900 <= measurements[0].measurement.value <= 10100


def test_linestring_length_calculation():
    """Test length calculation for linestrings."""
    # Create a simple line (1000m) in a projected CRS
    line = LineString([(0, 0), (1000, 0)])
    gdf = gpd.GeoDataFrame({"geometry": [line]}, crs="EPSG:32643")

    measurements = calculate_measurements(gdf, "EPSG:32643")

    assert len(measurements) == 1
    assert measurements[0].geometry_type == "LineString"
    assert measurements[0].measurement is not None
    assert measurements[0].measurement.type == "length"
    assert measurements[0].measurement.unit == "m"
    # Length should be approximately 1000m
    assert 990 <= measurements[0].measurement.value <= 1010


def test_point_no_measurement():
    """Test that points have no measurement."""
    point = Point(100, 100)
    gdf = gpd.GeoDataFrame({"geometry": [point]}, crs="EPSG:32643")

    measurements = calculate_measurements(gdf, "EPSG:32643")

    assert len(measurements) == 1
    assert measurements[0].geometry_type == "Point"
    assert measurements[0].measurement is None


def test_unsupported_geometry():
    """Test handling of unsupported geometry types."""
    # MultiPolygon
    poly1 = Polygon([(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)])
    poly2 = Polygon([(20, 20), (30, 20), (30, 30), (20, 30), (20, 20)])
    multi_polygon = MultiPolygon([poly1, poly2])

    gdf = gpd.GeoDataFrame({"geometry": [multi_polygon]}, crs="EPSG:32643")

    measurements = calculate_measurements(gdf, "EPSG:32643")

    assert len(measurements) == 1
    assert measurements[0].geometry_type == "MultiPolygon"
    assert measurements[0].measurement is None
    assert measurements[0].measurement_status == "UNSUPPORTED_GEOMETRY"


def test_empty_geometry():
    """Test handling of empty geometries."""
    empty_polygon = Polygon()
    gdf = gpd.GeoDataFrame({"geometry": [empty_polygon]}, crs="EPSG:32643")

    measurements = calculate_measurements(gdf, "EPSG:32643")

    assert len(measurements) == 1
    assert measurements[0].measurement is None
    assert measurements[0].measurement_status == "EMPTY_GEOMETRY"


def test_mixed_geometries(sample_mixed_gdf):
    """Test processing of mixed geometry types."""
    # Transform to projected CRS
    gdf_projected = sample_mixed_gdf.to_crs("EPSG:32643")

    measurements = calculate_measurements(gdf_projected, "EPSG:32643")

    assert len(measurements) == 3

    # First should be polygon with area
    assert measurements[0].geometry_type == "Polygon"
    assert measurements[0].measurement is not None
    assert measurements[0].measurement.type == "area"
    assert measurements[0].measurement.value > 0

    # Second should be linestring with length
    assert measurements[1].geometry_type == "LineString"
    assert measurements[1].measurement is not None
    assert measurements[1].measurement.type == "length"
    assert measurements[1].measurement.value > 0

    # Third should be point with no measurement
    assert measurements[2].geometry_type == "Point"
    assert measurements[2].measurement is None


def test_feature_properties():
    """Test that feature properties are preserved."""
    polygon = Polygon([(0, 0), (100, 0), (100, 100), (0, 100), (0, 0)])
    gdf = gpd.GeoDataFrame(
        {"name": ["Test Area"], "type": ["residential"], "geometry": [polygon]},
        crs="EPSG:32643",
    )

    measurements = calculate_measurements(gdf, "EPSG:32643")

    assert len(measurements) == 1
    assert "name" in measurements[0].properties
    assert measurements[0].properties["name"] == "Test Area"
    assert "type" in measurements[0].properties
    assert measurements[0].properties["type"] == "residential"


def test_geographic_to_projected_transformation(sample_polygon_gdf):
    """Test that geographic coordinates are properly transformed."""
    # Original is in EPSG:4326
    gdf_projected = sample_polygon_gdf.to_crs("EPSG:32643")

    measurements = calculate_measurements(gdf_projected, "EPSG:32643")

    assert len(measurements) == 1
    assert measurements[0].measurement is not None
    # Area should be in reasonable range (roughly 1 km²)
    # With 0.01 degree offset, area should be around 1 km²
    assert measurements[0].measurement.value > 100000  # More than 0.1 km²
    assert measurements[0].measurement.value < 2000000  # Less than 2 km²
