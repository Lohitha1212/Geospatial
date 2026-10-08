"""File-related Pydantic schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class FileResponse(BaseModel):
    """Response model for file information."""

    id: str = Field(..., description="Unique file identifier")
    filename: str = Field(..., description="Original filename")
    file_type: str = Field(..., description="File type (KML or Shapefile)")
    feature_count: int | None = Field(None, description="Number of features in the file")
    crs: str | None = Field(None, description="Coordinate Reference System")
    status: str = Field(..., description="Processing status")
    created_at: datetime = Field(..., description="Upload timestamp")

    class Config:
        from_attributes = True


class Measurement(BaseModel):
    """Measurement information for a feature."""

    type: str = Field(..., description="Measurement type (area or length)")
    value: float = Field(..., description="Measurement value")
    unit: str = Field(..., description="Measurement unit")


class FeatureMeasurement(BaseModel):
    """Feature measurement information."""

    feature_id: int = Field(..., description="Feature index")
    geometry_type: str = Field(..., description="Geometry type")
    measurement: Measurement | None = Field(None, description="Measurement data if applicable")
    measurement_status: str | None = Field(
        None, description="Status when measurement cannot be computed"
    )
    properties: dict[str, Any] = Field(default_factory=dict, description="Feature properties")
    
    model_config = {"arbitrary_types_allowed": True}


class MeasurementResponse(BaseModel):
    """Response model for file measurements."""

    file_id: str = Field(..., description="File identifier")
    crs: str | None = Field(None, description="Original CRS")
    measurement_crs: str | None = Field(None, description="CRS used for measurements")
    features: list[FeatureMeasurement] = Field(
        default_factory=list, description="Feature measurements"
    )
