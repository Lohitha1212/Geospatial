"""Test configuration and fixtures."""

import tempfile
from pathlib import Path

import geopandas as gpd
import pytest
from fastapi.testclient import TestClient
from shapely.geometry import LineString, Point, Polygon
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.main import app
# Import models at module level to register with Base.metadata
from app.models.file import GeospatialFile  # noqa: F401


@pytest.fixture(scope="function")
def test_engine(tmp_path):
    """Create a test database engine."""
    # Use a temporary file-based SQLite database instead of in-memory
    # This avoids threading issues with TestClient
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}")
    
    # Create tables (models already imported at module level)
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    engine.dispose()
    # Clean up the test database file
    if db_path.exists():
        db_path.unlink()


@pytest.fixture(scope="function")
def test_db(test_engine):
    """Create a temporary test database session."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client(test_engine):
    """Create a test client with database override."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_polygon_gdf():
    """Create a sample GeoDataFrame with a polygon in EPSG:4326."""
    # Create a square polygon around a known location (Bangalore, India)
    # Approximately 1km x 1km
    lon, lat = 77.6, 13.0
    offset = 0.005  # roughly 500m at this latitude

    polygon = Polygon(
        [
            (lon - offset, lat - offset),
            (lon + offset, lat - offset),
            (lon + offset, lat + offset),
            (lon - offset, lat + offset),
            (lon - offset, lat - offset),
        ]
    )

    gdf = gpd.GeoDataFrame(
        {"name": ["Test Polygon"], "geometry": [polygon]}, crs="EPSG:4326"
    )

    return gdf


@pytest.fixture
def sample_linestring_gdf():
    """Create a sample GeoDataFrame with a linestring in EPSG:4326."""
    # Create a line approximately 1km long
    lon, lat = 77.6, 13.0

    line = LineString([(lon, lat), (lon + 0.01, lat + 0.005)])

    gdf = gpd.GeoDataFrame(
        {"name": ["Test Line"], "geometry": [line]}, crs="EPSG:4326"
    )

    return gdf


@pytest.fixture
def sample_point_gdf():
    """Create a sample GeoDataFrame with a point in EPSG:4326."""
    point = Point(77.6, 13.0)

    gdf = gpd.GeoDataFrame(
        {"name": ["Test Point"], "geometry": [point]}, crs="EPSG:4326"
    )

    return gdf


@pytest.fixture
def sample_mixed_gdf():
    """Create a sample GeoDataFrame with mixed geometry types."""
    lon, lat = 77.6, 13.0
    offset = 0.005

    polygon = Polygon(
        [
            (lon - offset, lat - offset),
            (lon + offset, lat - offset),
            (lon + offset, lat + offset),
            (lon - offset, lat + offset),
            (lon - offset, lat - offset),
        ]
    )

    line = LineString([(lon, lat), (lon + 0.01, lat + 0.005)])
    point = Point(lon, lat)

    gdf = gpd.GeoDataFrame(
        {
            "name": ["Polygon Feature", "Line Feature", "Point Feature"],
            "geometry": [polygon, line, point],
        },
        crs="EPSG:4326",
    )

    return gdf


@pytest.fixture
def sample_kml_file(temp_dir, sample_polygon_gdf):
    """Create a sample KML file."""
    kml_path = temp_dir / "test.kml"
    sample_polygon_gdf.to_file(kml_path, driver="KML")
    return kml_path


@pytest.fixture
def sample_shapefile(temp_dir, sample_polygon_gdf):
    """Create a sample Shapefile."""
    shp_path = temp_dir / "test.shp"
    sample_polygon_gdf.to_file(shp_path, driver="ESRI Shapefile")
    return shp_path
