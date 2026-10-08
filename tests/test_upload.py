"""Tests for file upload API endpoints."""

import io
import zipfile
from pathlib import Path

import geopandas as gpd
import pytest
from shapely.geometry import Polygon


def test_upload_kml_file(client, sample_kml_file):
    """Test uploading a KML file."""
    with open(sample_kml_file, "rb") as f:
        response = client.post(
            "/api/files/",
            files={"file": ("test.kml", f, "application/vnd.google-earth.kml+xml")},
        )

    assert response.status_code == 201
    data = response.json()

    assert "id" in data
    assert data["filename"] == "test.kml"
    assert data["file_type"] == "KML"
    assert data["status"] == "COMPLETED"
    assert data["feature_count"] == 1
    assert data["crs"] is not None


def test_upload_shapefile_zip(client, temp_dir, sample_polygon_gdf):
    """Test uploading a Shapefile ZIP."""
    # Create shapefile
    shp_path = temp_dir / "test.shp"
    sample_polygon_gdf.to_file(shp_path, driver="ESRI Shapefile")

    # Create ZIP with all shapefile components
    zip_path = temp_dir / "shapefile.zip"
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for ext in [".shp", ".shx", ".dbf", ".prj", ".cpg"]:
            component = temp_dir / f"test{ext}"
            if component.exists():
                zipf.write(component, f"test{ext}")

    # Upload ZIP
    with open(zip_path, "rb") as f:
        response = client.post(
            "/api/files/",
            files={"file": ("shapefile.zip", f, "application/zip")},
        )

    assert response.status_code == 201
    data = response.json()

    assert "id" in data
    assert data["filename"] == "shapefile.zip"
    assert data["file_type"] == "Shapefile"
    assert data["status"] == "COMPLETED"
    assert data["feature_count"] == 1


def test_upload_invalid_extension(client):
    """Test that invalid file extensions are rejected."""
    content = io.BytesIO(b"some content")

    response = client.post(
        "/api/files/",
        files={"file": ("test.txt", content, "text/plain")},
    )

    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_upload_invalid_zip(client):
    """Test that invalid ZIP files are rejected."""
    content = io.BytesIO(b"not a zip file")

    response = client.post(
        "/api/files/",
        files={"file": ("test.zip", content, "application/zip")},
    )

    assert response.status_code == 400


def test_upload_zip_without_shapefile(client, temp_dir):
    """Test that ZIP without Shapefile is rejected."""
    # Create ZIP with non-shapefile content
    zip_path = temp_dir / "empty.zip"
    with zipfile.ZipFile(zip_path, "w") as zipf:
        zipf.writestr("readme.txt", "This is not a shapefile")

    with open(zip_path, "rb") as f:
        response = client.post(
            "/api/files/",
            files={"file": ("empty.zip", f, "application/zip")},
        )

    assert response.status_code == 400
    assert "Shapefile" in response.json()["detail"]


def test_get_file_info(client, sample_kml_file):
    """Test getting file information."""
    # First upload a file
    with open(sample_kml_file, "rb") as f:
        upload_response = client.post(
            "/api/files/",
            files={"file": ("test.kml", f, "application/vnd.google-earth.kml+xml")},
        )

    file_id = upload_response.json()["id"]

    # Get file info
    response = client.get(f"/api/files/{file_id}")

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == file_id
    assert data["filename"] == "test.kml"
    assert data["status"] == "COMPLETED"


def test_get_file_info_not_found(client):
    """Test getting info for non-existent file."""
    response = client.get("/api/files/nonexistent-id")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_measurements(client, sample_kml_file):
    """Test getting measurements for a file."""
    # Upload file
    with open(sample_kml_file, "rb") as f:
        upload_response = client.post(
            "/api/files/",
            files={"file": ("test.kml", f, "application/vnd.google-earth.kml+xml")},
        )

    file_id = upload_response.json()["id"]

    # Get measurements
    response = client.get(f"/api/files/{file_id}/measurements/")

    assert response.status_code == 200
    data = response.json()

    assert data["file_id"] == file_id
    assert "crs" in data
    assert "measurement_crs" in data
    assert "features" in data
    assert len(data["features"]) > 0

    # Check first feature
    feature = data["features"][0]
    assert "feature_id" in feature
    assert "geometry_type" in feature
    assert "properties" in feature

    # Should be a polygon with area measurement
    if feature["geometry_type"] == "Polygon":
        assert feature["measurement"] is not None
        assert feature["measurement"]["type"] == "area"
        assert feature["measurement"]["unit"] == "m²"
        assert feature["measurement"]["value"] > 0


def test_get_measurements_not_found(client):
    """Test getting measurements for non-existent file."""
    response = client.get("/api/files/nonexistent-id/measurements/")

    assert response.status_code == 404


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "name" in data
    assert "version" in data
