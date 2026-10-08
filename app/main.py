"""Main FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.files import router as files_router
from app.core.config import settings
from app.core.database import init_db
from app.core.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    setup_logging()
    init_db()
    yield
    # Shutdown
    pass


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    Upload and process geospatial files to extract measurements.
    
    ## Features
    
    * **KML Support**: Upload KML files for processing
    * **Shapefile Support**: Upload ZIP files containing Shapefiles
    * **Automatic CRS Transformation**: Intelligently selects appropriate projected CRS
    * **Area Measurement**: Calculate polygon areas in square meters
    * **Length Measurement**: Calculate linestring lengths in meters
    * **Feature Extraction**: Extract all feature properties and attributes
    
    ## Supported Formats
    
    * `.kml` - Keyhole Markup Language files
    * `.zip` - ZIP archives containing Shapefiles (.shp, .shx, .dbf, .prj)
    
    ## Measurements
    
    * **Polygons**: Area in m²
    * **LineStrings**: Length in m
    * **Points**: No measurement
    * **Other geometries**: Marked as unsupported
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(files_router)


@app.get("/", tags=["health"])
def root():
    """Root endpoint - API health check."""
    return {
        "status": "healthy",
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/health", tags=["health"])
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
