"""Tests for file validation."""

import io

import pytest
from fastapi import HTTPException, UploadFile

from app.utils.validation import (
    sanitize_filename,
    validate_file_extension,
    validate_upload_file,
)


def test_validate_file_extension_kml():
    """Test KML file extension validation."""
    result = validate_file_extension("test.kml")
    assert result == ".kml"


def test_validate_file_extension_zip():
    """Test ZIP file extension validation."""
    result = validate_file_extension("shapefile.zip")
    assert result == ".zip"


def test_validate_file_extension_case_insensitive():
    """Test that validation is case insensitive."""
    assert validate_file_extension("test.KML") == ".kml"
    assert validate_file_extension("test.ZIP") == ".zip"


def test_validate_file_extension_invalid():
    """Test that invalid extensions are rejected."""
    with pytest.raises(HTTPException) as exc_info:
        validate_file_extension("test.geojson")

    assert exc_info.value.status_code == 400
    assert "Unsupported file type" in exc_info.value.detail


def test_sanitize_filename():
    """Test filename sanitization."""
    # Normal filename
    assert sanitize_filename("test.kml") == "test.kml"

    # Filename with path
    assert sanitize_filename("/path/to/test.kml") == "test.kml"
    assert sanitize_filename("..\\..\\test.kml") == "test.kml"

    # Filename with path traversal attempt
    assert sanitize_filename("../../etc/passwd") == "passwd"

    # Mixed slashes
    assert sanitize_filename("path/to\\file.zip") == "file.zip"


def test_validate_upload_file_kml():
    """Test upload file validation for KML."""
    content = b"<?xml version='1.0' encoding='UTF-8'?><kml></kml>"
    file = UploadFile(
        filename="test.kml",
        file=io.BytesIO(content),
    )

    file_type = validate_upload_file(file)
    assert file_type == "KML"


def test_validate_upload_file_zip():
    """Test upload file validation for ZIP."""
    content = b"PK\x03\x04"  # ZIP file signature
    file = UploadFile(
        filename="shapefile.zip",
        file=io.BytesIO(content),
    )

    file_type = validate_upload_file(file)
    assert file_type == "Shapefile"


def test_validate_upload_file_no_filename():
    """Test that files without filename are rejected."""
    file = UploadFile(
        filename="",
        file=io.BytesIO(b"content"),
    )

    with pytest.raises(HTTPException) as exc_info:
        validate_upload_file(file)

    assert exc_info.value.status_code == 400
    assert "No filename provided" in exc_info.value.detail


def test_validate_upload_file_invalid_extension():
    """Test that invalid extensions are rejected."""
    file = UploadFile(
        filename="test.txt",
        file=io.BytesIO(b"content"),
    )

    with pytest.raises(HTTPException) as exc_info:
        validate_upload_file(file)

    assert exc_info.value.status_code == 400
