# Geospatial File Measurement API

A production-quality FastAPI application for processing geospatial files and calculating accurate measurements.

> **💡 Quick Start:** See [QUICKSTART.md](QUICKSTART.md) for simple step-by-step instructions, or use the provided scripts:
> - **Windows**: Run `.\start.ps1` to start the API
> - **Tests**: Run `.\test.ps1` to run all tests

## Overview

This API accepts KML files and Shapefiles (in ZIP format), extracts feature information, and calculates measurements with automatic coordinate system transformation. The system intelligently selects appropriate projected coordinate reference systems (CRS) to ensure accurate area and length calculations.

## Features

- ✅ **KML Support**: Upload and process KML files
- ✅ **Shapefile ZIP Support**: Upload ZIP archives containing Shapefiles
- ✅ **Feature Extraction**: Extract all features with properties and attributes
- ✅ **Polygon Area Calculation**: Calculate areas in square meters (m²)
- ✅ **LineString Length Calculation**: Calculate lengths in meters (m)
- ✅ **Automatic CRS Transformation**: Intelligently selects UTM zones based on data location
- ✅ **Geographic CRS Handling**: Properly transforms EPSG:4326 and other geographic CRS
- ✅ **Error Handling**: Graceful handling of unsupported geometries and invalid files
- ✅ **RESTful API**: Clean, documented REST endpoints
- ✅ **Automated Tests**: Comprehensive test suite
- ✅ **Docker Support**: Containerized deployment

## Architecture

```
Client (Browser/cURL/Postman)
          ↓
    FastAPI Application
          ↓
   Upload Validation
    (extension, size, ZIP structure)
          ↓
   File Storage & Processing
          ↓
    GeoPandas + Fiona
    (Read geospatial data)
          ↓
    CRS Detection & Analysis
          ↓
  Projected CRS Selection
    (UTM zone calculation)
          ↓
  Coordinate Transformation
    (PyProj + Shapely)
          ↓
  Measurement Calculation
    (area/length in meters)
          ↓
   SQLite Metadata Storage
          ↓
    JSON Response to Client
```

## Project Structure

```
geospatial-measurement-api/
│
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application entry point
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── files.py               # File upload and measurement endpoints
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py              # Application configuration
│   │   ├── database.py            # Database setup and session management
│   │   └── logging.py             # Logging configuration
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   └── file.py                # SQLAlchemy database models
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── file.py                # Pydantic request/response schemas
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── crs_service.py         # CRS transformation logic
│   │   ├── file_service.py        # File management operations
│   │   ├── geospatial_service.py  # Geospatial file processing
│   │   └── measurement_service.py # Measurement calculations
│   │
│   └── utils/
│       ├── __init__.py
│       ├── validation.py          # File validation utilities
│       └── zip_utils.py           # ZIP extraction and Shapefile detection
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # Test fixtures and configuration
│   ├── test_crs.py                # CRS transformation tests
│   ├── test_measurements.py       # Measurement calculation tests
│   ├── test_validation.py         # File validation tests
│   └── test_upload.py             # API endpoint tests
│
├── uploads/                        # File storage directory
│   └── .gitkeep
│
├── requirements.txt               # Python dependencies
├── pyproject.toml                 # Project configuration (black, ruff, pytest)
├── .env.example                   # Environment variables template
├── .gitignore                     # Git ignore rules
├── Dockerfile                     # Docker image definition
├── docker-compose.yml             # Docker Compose configuration
└── README.md                      # This file
```

## Setup

### Prerequisites

- Python 3.11 or higher
- pip package manager
- (Optional) Docker and Docker Compose

### Local Development Setup

1. **Clone the repository**

```bash
git clone <repository-url>
cd geospatial-measurement-api
```

2. **Create a virtual environment**

```bash
python -m venv .venv
```

3. **Activate the virtual environment**

**Windows:**
```bash
.venv\Scripts\activate
```

**Linux/macOS:**
```bash
source .venv/bin/activate
```

4. **Install dependencies**

```bash
pip install -r requirements.txt
```

5. **Configure environment variables**

```bash
copy .env.example .env
```

Edit `.env` if you need to customize settings.

6. **Run the application**

```bash
uvicorn app.main:app --reload
```

7. **Access the API**

- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc
- **Health Check**: http://127.0.0.1:8000/health

## Docker Deployment

### Using Docker Compose (Recommended)

1. **Build and start the container**

```bash
docker compose up --build
```

2. **Access the API**

- **Swagger UI**: http://localhost:8000/docs
- **API**: http://localhost:8000

3. **Stop the container**

```bash
docker compose down
```

### Using Docker directly

```bash
# Build the image
docker build -t geospatial-api .

# Run the container
docker run -d -p 8000:8000 --name geospatial-api geospatial-api

# Stop the container
docker stop geospatial-api
docker rm geospatial-api
```

## API Usage

### 1. Upload a Geospatial File

**Endpoint:** `POST /api/files/`

**Upload KML:**

```bash
curl -X POST "http://127.0.0.1:8000/api/files/" \
  -F "file=@survey.kml"
```

**Upload Shapefile (ZIP):**

```bash
curl -X POST "http://127.0.0.1:8000/api/files/" \
  -F "file=@shapefile.zip"
```

**Response:**

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "filename": "survey.kml",
  "file_type": "KML",
  "feature_count": 120,
  "crs": "EPSG:4326",
  "status": "COMPLETED",
  "created_at": "2026-10-07T12:00:00Z"
}
```

### 2. Get File Information

**Endpoint:** `GET /api/files/{id}/`

```bash
curl -X GET "http://127.0.0.1:8000/api/files/a1b2c3d4-e5f6-7890-abcd-ef1234567890"
```

**Response:**

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "filename": "survey.kml",
  "file_type": "KML",
  "feature_count": 120,
  "crs": "EPSG:4326",
  "status": "COMPLETED",
  "created_at": "2026-10-07T12:00:00Z"
}
```

### 3. Get Measurements

**Endpoint:** `GET /api/files/{id}/measurements/`

```bash
curl -X GET "http://127.0.0.1:8000/api/files/a1b2c3d4-e5f6-7890-abcd-ef1234567890/measurements/"
```

**Response:**

```json
{
  "file_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "crs": "EPSG:4326",
  "measurement_crs": "EPSG:32643",
  "features": [
    {
      "feature_id": 0,
      "geometry_type": "Polygon",
      "measurement": {
        "type": "area",
        "value": 1523.42,
        "unit": "m²"
      },
      "measurement_status": null,
      "properties": {
        "name": "Plot A",
        "type": "residential"
      }
    },
    {
      "feature_id": 1,
      "geometry_type": "LineString",
      "measurement": {
        "type": "length",
        "value": 245.83,
        "unit": "m"
      },
      "measurement_status": null,
      "properties": {
        "name": "Road 1"
      }
    },
    {
      "feature_id": 2,
      "geometry_type": "Point",
      "measurement": null,
      "measurement_status": null,
      "properties": {
        "name": "Survey Point"
      }
    },
    {
      "feature_id": 3,
      "geometry_type": "MultiPolygon",
      "measurement": null,
      "measurement_status": "UNSUPPORTED_GEOMETRY",
      "properties": {
        "name": "Complex Area"
      }
    }
  ]
}
```

## Measurement Logic

### Supported Geometry Types

| Geometry Type | Measurement | Unit | Notes |
|--------------|-------------|------|-------|
| **Polygon** | Area | m² | Calculated after CRS transformation |
| **LineString** | Length | m | Calculated after CRS transformation |
| **Point** | None | - | No measurement applicable |
| **MultiPolygon** | None | - | Marked as `UNSUPPORTED_GEOMETRY` |
| **MultiLineString** | None | - | Marked as `UNSUPPORTED_GEOMETRY` |
| **GeometryCollection** | None | - | Marked as `UNSUPPORTED_GEOMETRY` |

### CRS Strategy

**Why CRS Transformation is Critical:**

Geographic coordinate systems like EPSG:4326 (WGS84) use latitude/longitude in degrees. Calculating area or distance directly in degrees produces meaningless results because:

- 1 degree of longitude ≠ 1 degree of latitude in distance
- The distance varies by latitude
- Results would be in "square degrees" instead of square meters

**Our Solution:**

1. **Detect Source CRS**: Read CRS from the uploaded file
2. **Analyze CRS Type**:
   - If geographic (lat/lon): Calculate appropriate UTM zone
   - If projected with linear units: Use existing CRS
   - If missing: Flag as `CRS_MISSING`
3. **UTM Zone Selection**:
   - Calculate dataset centroid
   - Determine UTM zone: `zone = floor((longitude + 180) / 6) + 1`
   - Select hemisphere: Northern (EPSG:326xx) or Southern (EPSG:327xx)
4. **Transform Coordinates**: Use PyProj to transform to projected CRS
5. **Calculate Measurements**: Compute area/length in meters

**Example:**

```
Input: Polygon in EPSG:4326 at (77.6°E, 13.0°N)
↓
UTM Zone Calculation: Zone 43 North
↓
Selected CRS: EPSG:32643 (WGS 84 / UTM zone 43N)
↓
Transform coordinates to meters
↓
Calculate area → 1,523.42 m²
```

## Error Handling

The API provides clear error messages for common issues:

### Unsupported File Type (HTTP 400)

```json
{
  "detail": "Unsupported file type. Only .kml and .zip files are supported."
}
```

### Invalid ZIP File (HTTP 400)

```json
{
  "detail": "Invalid ZIP file."
}
```

### Missing Shapefile (HTTP 400)

```json
{
  "detail": "ZIP file does not contain a Shapefile (.shp file not found)."
}
```

### Incomplete Shapefile (HTTP 400)

```json
{
  "detail": "Incomplete Shapefile. Missing required files: .shx, .dbf"
}
```

### File Not Found (HTTP 404)

```json
{
  "detail": "File not found."
}
```

### File Too Large (HTTP 400)

```json
{
  "detail": "File too large. Maximum size is 50MB."
}
```

## Testing

### Run All Tests

```bash
pytest
```

### Run with Coverage

```bash
pytest --cov=app --cov-report=html
```

### Run Specific Test Files

```bash
pytest tests/test_upload.py
pytest tests/test_measurements.py
pytest tests/test_crs.py
```

### Test Coverage

The test suite includes:

- ✅ File upload validation (extensions, size, MIME types)
- ✅ ZIP extraction and Shapefile detection
- ✅ CRS transformation and UTM zone selection
- ✅ Measurement calculations (area, length)
- ✅ Geometry type handling (Polygon, LineString, Point, unsupported)
- ✅ API endpoint integration tests
- ✅ Error handling and edge cases

## Design Decisions

### Why FastAPI?

- **Modern Python framework** with automatic OpenAPI documentation
- **Type hints and validation** with Pydantic
- **High performance** with async support
- **Easy testing** with TestClient
- **Great developer experience** with interactive API docs

### Why GeoPandas?

- **Industry standard** for geospatial data in Python
- **Unified interface** for reading KML, Shapefiles, and many formats
- **Pandas integration** for data manipulation
- **Shapely geometries** for spatial operations
- **Built-in CRS support** via PyProj

### Why Shapely?

- **Simple geometry operations** (area, length, contains, etc.)
- **Well-tested and reliable** geometry library
- **GEOS backend** for computational geometry
- **Integration** with GeoPandas

### Why PyProj?

- **Accurate coordinate transformations** between CRS
- **PROJ library bindings** (industry standard)
- **Support for all standard CRS** (EPSG, WKT, etc.)

### Why SQLite?

- **Zero configuration** database
- **File-based** persistence
- **Sufficient** for metadata storage
- **Easy to upgrade** to PostgreSQL/PostGIS for production scale

### Why UTM for Measurements?

- **Accurate** for local/regional measurements
- **Conformal projection** preserves angles
- **Minimal distortion** within each zone
- **Metric units** (meters) for easy interpretation
- **Appropriate for most datasets** under ~6° longitude span

### Why Filesystem Storage?

- **Simple and reliable** for proof of concept
- **Easy to implement** file management
- **Suitable for moderate scale** (thousands of files)
- **Clear upgrade path** to S3/object storage for production

### PostGIS for Production

For large-scale production systems, consider PostgreSQL with PostGIS extension:

- **Spatial indexing** for fast queries
- **Spatial queries** (intersects, contains, within, etc.)
- **Larger datasets** with better performance
- **Concurrent access** with ACID guarantees
- **Replication and backup** capabilities

## Limitations

### Current Limitations

1. **Geometry Support**: Only Polygon, LineString, and Point have measurements
2. **File Size**: Limited to 50MB per upload (configurable)
3. **Synchronous Processing**: Files processed immediately (blocking)
4. **Single-file Storage**: Uses local filesystem
5. **No Authentication**: API is open (suitable for internal/demo use)
6. **SQLite Concurrency**: Limited concurrent write performance

### Not Production-Optimized For

- Very large files (>100MB)
- High concurrent upload volume
- Long-running processing tasks
- Multi-user access control
- Distributed deployment

## Learning

Building this project provided hands-on experience with:

### Geospatial Concepts

- **Coordinate Reference Systems (CRS)**: Understanding geographic vs projected CRS
- **UTM Zones**: How to calculate and select appropriate zones
- **Coordinate Transformations**: Using PyProj for accurate transformations
- **Geometry Types**: Working with Polygon, LineString, Point, and complex types
- **Spatial Measurements**: Calculating area and length in metric units
- **File Formats**: KML structure and Shapefile component requirements

### Python Libraries

- **GeoPandas**: Reading, transforming, and analyzing geospatial data
- **Shapely**: Geometry operations and measurements
- **PyProj**: CRS definitions and coordinate transformations
- **Fiona**: Low-level geospatial file I/O

### FastAPI Development

- **RESTful API design**: Clean endpoint structure and naming
- **Request/response models**: Pydantic schemas for validation
- **File uploads**: Multipart form data handling
- **Error handling**: HTTP status codes and error messages
- **API documentation**: Automatic OpenAPI/Swagger generation
- **Dependency injection**: Database session management

### Software Engineering

- **Clean architecture**: Separation of concerns (routers, services, models)
- **Service layer pattern**: Business logic isolation
- **Input validation**: File type, size, and content validation
- **Security**: Path traversal prevention, file sanitization
- **Testing**: Unit tests, integration tests, fixtures
- **Docker**: Containerization and deployment
- **Documentation**: Comprehensive README and inline comments

## Future Scope

### High Priority

- [ ] **Background Processing**: Celery/RQ for async file processing
- [ ] **Progress Tracking**: Job status and progress endpoints
- [ ] **PostgreSQL + PostGIS**: Scalable spatial database
- [ ] **MultiPolygon/MultiLineString Support**: Handle complex geometries
- [ ] **Authentication & Authorization**: JWT tokens, API keys
- [ ] **Rate Limiting**: Prevent API abuse

### Medium Priority

- [ ] **Object Storage**: S3/MinIO for file storage
- [ ] **Bounding Box Calculation**: Return feature extent
- [ ] **Geometry Validation**: Detect and fix invalid geometries
- [ ] **More File Formats**: GeoJSON, GeoPackage, GML
- [ ] **Measurement Units**: Support feet, kilometers, etc.
- [ ] **File Listing**: Paginated endpoint for uploaded files
- [ ] **File Deletion**: Delete uploaded files and cleanup

### Lower Priority

- [ ] **Advanced CRS Options**: User-specified target CRS
- [ ] **Batch Upload**: Process multiple files at once
- [ ] **Webhooks**: Notify external systems on completion
- [ ] **Caching**: Redis for measurement result caching
- [ ] **Logging**: Centralized logging (ELK stack)
- [ ] **Monitoring**: Prometheus metrics and Grafana dashboards
- [ ] **Kubernetes**: K8s deployment manifests
- [ ] **CI/CD**: GitHub Actions for testing and deployment

## GitHub Checklist

Before pushing to a public repository, verify:

- [ ] No `.env` file committed (only `.env.example`)
- [ ] No database files (`.db`, `.sqlite3`) committed
- [ ] No uploaded files in `uploads/` directory committed
- [ ] No IDE-specific files (`.vscode/`, `.idea/`) committed
- [ ] No `__pycache__` or `.pytest_cache` directories committed
- [ ] `.gitignore` properly configured
- [ ] `requirements.txt` includes all dependencies
- [ ] `README.md` is complete and accurate
- [ ] All tests pass: `pytest`
- [ ] Code is formatted: `black .` (if using Black)
- [ ] Docker build works: `docker compose up --build`
- [ ] API documentation is accessible at `/docs`
- [ ] No hardcoded secrets or credentials in code
- [ ] License file added (if applicable)

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add/update tests
5. Ensure all tests pass
6. Submit a pull request

## License

[Specify your license here - MIT, Apache 2.0, etc.]

## Contact

[Your contact information or organization]

---

**Built with ❤️ using FastAPI, GeoPandas, and Python**
