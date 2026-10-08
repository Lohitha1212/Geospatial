# Quick Start Guide

## Prerequisites
- Python 3.13 installed
- Virtual environment already set up (`.venv` directory exists)

## Running the API

### Step 1: Activate Virtual Environment

**PowerShell (Windows):**
```powershell
.venv\Scripts\Activate.ps1
```

**If you get an execution policy error, run this first:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Step 2: Verify Installation

Check that packages are installed:
```powershell
python -m pip list | Select-String "geopandas|fastapi"
```

You should see:
- geopandas 1.0.1
- fastapi (version)

### Step 3: Run the API Server

```powershell
uvicorn app.main:app --reload
```

The API will start at: **http://127.0.0.1:8000**

### Step 4: Test the API

Open your browser and visit:
- **API Documentation**: http://127.0.0.1:8000/docs
- **Health Check**: http://127.0.0.1:8000/health

## Running Tests

With virtual environment activated:
```powershell
pytest -v
```

Expected result: **35 passed**

## Using the API

### Upload a KML File

```powershell
# Example using curl (if available)
curl -X POST "http://127.0.0.1:8000/api/files/" `
  -F "file=@path/to/your/file.kml"
```

Or use the interactive API docs at http://127.0.0.1:8000/docs

### Get Measurements

After uploading, use the returned `file_id`:
```powershell
curl "http://127.0.0.1:8000/api/files/{file_id}/measurements/"
```

## Creating Test Data

You can create a simple test KML file:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <Placemark>
      <name>Test Polygon</name>
      <Polygon>
        <outerBoundaryIs>
          <LinearRing>
            <coordinates>
              77.595,12.995,0
              77.605,12.995,0
              77.605,13.005,0
              77.595,13.005,0
              77.595,12.995,0
            </coordinates>
          </LinearRing>
        </outerBoundaryIs>
      </Polygon>
    </Placemark>
  </Document>
</kml>
```

Save this as `test.kml` and upload it through the API.

## Stopping the Server

Press `CTRL+C` in the terminal where uvicorn is running.

## Deactivating Virtual Environment

```powershell
deactivate
```

## Troubleshooting

### "Module not found" errors
- Make sure virtual environment is activated (you should see `(.venv)` in your prompt)
- Reinstall dependencies: `pip install -r requirements.txt`

### Port already in use
- Change the port: `uvicorn app.main:app --reload --port 8001`

### Database locked errors
- Stop any running instances of the API
- Delete `geospatial.db` if it exists

## Docker (Alternative)

**Note:** Docker is not installed on your system. To use Docker:

1. Install Docker Desktop for Windows
2. Run: `docker-compose up --build`

The API will be available at http://localhost:8000

## Next Steps

- Read the full README.md for detailed documentation
- Explore the API using the interactive docs at /docs
- Check out the test files in `tests/` for usage examples
