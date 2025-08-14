"""
Core data structures for PlanCast.

This module defines the fundamental data structures used throughout
the application, based on actual CubiCasa5K output format and 
our 3D pipeline requirements.
"""

from typing import List, Tuple, Dict, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum
import time


class FileFormat(str, Enum):
    """Supported input file formats."""
    JPG = "jpg"
    JPEG = "jpeg"
    PNG = "png"
    PDF = "pdf"


class ProcessingStatus(str, Enum):
    """Processing job status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ExportFormat(str, Enum):
    """Supported 3D export formats."""
    GLB = "glb"
    OBJ = "obj"
    STL = "stl"
    SKP = "skp"  # SketchUp format


# === CubiCasa5K Data Structures ===
# Based on your actual breakthrough data format

class CubiCasaOutput(BaseModel):
    """
    Raw output from CubiCasa5K model.
    Based on actual data: wall_coords=[(55,49), (60,49)...], room_bbox={...}
    """
    wall_coordinates: List[Tuple[int, int]] = Field(
        ..., 
        description="Wall pixel coordinates [(x,y), (x,y)...] - typically 5000+ points"
    )
    room_bounding_boxes: Dict[str, Dict[str, int]] = Field(
        ..., 
        description="Room bounding boxes {'room_type': {'min_x': 0, 'max_x': 255, ...}}"
    )
    image_dimensions: Tuple[int, int] = Field(
        ..., 
        description="Image width, height in pixels"
    )
    confidence_scores: Dict[str, float] = Field(
        default_factory=dict, 
        description="Room detection confidence scores"
    )
    processing_time: float = Field(
        ..., 
        description="CubiCasa5K processing time in seconds"
    )


# === Scaling and Coordinate Transformation ===

class ScaleReference(BaseModel):
    """
    User-provided scaling reference.
    Example: "Kitchen width is 12 feet" -> calculate scale factor for entire floor plan
    """
    room_type: str = Field(..., description="Room name for scaling (e.g., 'kitchen')")
    dimension_type: str = Field(..., description="'width' or 'length'")
    real_world_feet: float = Field(..., gt=0, description="Real-world measurement in feet")
    pixel_measurement: float = Field(..., gt=0, description="Calculated pixel measurement")
    scale_factor: float = Field(..., gt=0, description="Pixels per foot ratio")

class BuildingDimensions(BaseModel):
    """Building dimensions with metadata."""
    width_feet: float = Field(..., description="Building width in feet")
    length_feet: float = Field(..., description="Building length in feet") 
    area_sqft: float = Field(..., description="Total area in square feet")
    scale_factor: float = Field(..., description="Pixels per foot conversion factor")
    original_width_pixels: int = Field(..., description="Original image width in pixels")
    original_height_pixels: int = Field(..., description="Original image height in pixels")

# Then the existing ScaledCoordinates class follows...


class ScaledCoordinates(BaseModel):
    """
    Coordinates converted to real-world measurements.
    Output of Task 2: Coordinate Scaling System
    """
    walls_feet: List[Tuple[float, float]] = Field(
        ..., 
        description="Wall coordinates in feet [(x_feet, y_feet)...]"
    )
    rooms_feet: Dict[str, Dict[str, float]] = Field(
        ..., 
        description="Room dimensions and positions in feet"
    )
    scale_reference: ScaleReference = Field(
        ..., 
        description="Scale reference used for conversion"
    )
    
    total_building_size: BuildingDimensions = Field(  # Proper typed structure
        ..., 
        description="Overall building dimensions and metadata"
    )


# === 3D Geometry Structures ===

class Vertex3D(BaseModel):
    """
    3D vertex with x, y, z coordinates.
    """
    x: float = Field(..., description="X coordinate in feet")
    y: float = Field(..., description="Y coordinate in feet") 
    z: float = Field(..., description="Z coordinate in feet")


class Face(BaseModel):
    """
    3D face defined by vertex indices.
    """
    indices: List[int] = Field(..., description="Vertex indices forming the face")


class Room3D(BaseModel):
    """
    3D room geometry.
    Output of Task 3: Room Mesh Generator
    """
    name: str = Field(..., description="Room name (kitchen, bedroom, etc.)")
    vertices: List[Vertex3D] = Field(
        ..., 
        description="3D vertices for the room mesh"
    )
    faces: List[Face] = Field(
        ..., 
        description="Triangle faces for the room mesh"
    )
    elevation_feet: float = Field(
        ..., 
        description="Floor elevation in feet (typically 0.0)"
    )
    height_feet: float = Field(
        ..., 
        description="Room height in feet"
    )


class Wall3D(BaseModel):
    """
    3D wall geometry.
    Output of Task 4: Wall Mesh Creator
    """
    id: str = Field(..., description="Unique wall identifier")
    vertices: List[Vertex3D] = Field(
        ..., 
        description="3D vertices for the wall mesh"
    )
    faces: List[Face] = Field(
        ..., 
        description="Triangle faces for the wall mesh"
    )
    height_feet: float = Field(
        ..., 
        description="Wall height in feet"
    )
    thickness_feet: float = Field(
        ..., 
        description="Wall thickness in feet"
    )


class Building3D(BaseModel):
    """
    Complete 3D building model.
    Combines all rooms and walls for export
    """
    rooms: List[Room3D] = Field(..., description="All room geometries")
    walls: List[Wall3D] = Field(..., description="All wall geometries")
    total_vertices: int = Field(..., description="Total vertex count")
    total_faces: int = Field(..., description="Total face count")
    bounding_box: Dict[str, float] = Field(
        ..., 
        description="Building bounds {min_x, max_x, min_y, max_y, min_z, max_z}"
    )
    export_ready: bool = Field(default=False, description="Ready for export")


class WebPreviewData(BaseModel):
    """
    Web preview data for browser-based 3D visualization.
    """
    glb_url: str = Field(..., description="URL to web-optimized GLB file")
    thumbnail_url: str = Field(..., description="URL to preview thumbnail")
    scene_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Scene metadata for Three.js (camera positions, lighting, etc.)"
    )


class MeshExportResult(BaseModel):
    """
    Result of 3D model export operation.
    """
    files: Dict[str, str] = Field(
        ..., 
        description="Export format -> file path mapping"
    )
    preview_data: WebPreviewData = Field(
        ..., 
        description="Web preview data for browser visualization"
    )
    summary: Dict[str, Any] = Field(
        default_factory=dict,
        description="Export summary (file sizes, processing time, etc.)"
    )


# === Job Management ===

class ProcessingJob(BaseModel):
    """
    Main processing job tracking.
    Tracks the entire pipeline from upload to 3D export
    """
    job_id: str = Field(..., description="Unique job identifier")
    filename: str = Field(..., description="Original filename")
    file_format: FileFormat = Field(..., description="Input file format")
    file_size_bytes: int = Field(..., description="File size")
    
    # Processing status
    status: ProcessingStatus = Field(default=ProcessingStatus.PENDING)
    current_step: str = Field(default="upload", description="Current processing step")
    progress_percent: int = Field(default=0, description="Processing progress 0-100")
    
    # Pipeline outputs
    cubicasa_output: Optional[CubiCasaOutput] = None
    scaled_coordinates: Optional[ScaledCoordinates] = None
    building_3d: Optional[Building3D] = None
    
    # Export results
    exported_files: Dict[str, str] = Field(
        default_factory=dict, 
        description="Export format -> file path mapping"
    )
    
    # Error handling
    error_message: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    
    # Timing
    created_at: float = Field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    
    def total_processing_time(self) -> Optional[float]:
        """Calculate total processing time in seconds."""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None
    
    def is_completed(self) -> bool:
        """Check if job is completed successfully."""
        return self.status == ProcessingStatus.COMPLETED and self.building_3d is not None


# === Export Configuration ===

class ExportConfig(BaseModel):
    """
    Configuration for 3D model export.
    Task 5: Export Pipeline settings
    """
    formats: List[ExportFormat] = Field(
        default=[ExportFormat.GLB, ExportFormat.OBJ], 
        description="Export formats to generate"
    )
    include_materials: bool = Field(default=True, description="Include material definitions")
    include_textures: bool = Field(default=False, description="Include texture mapping")
    optimize_mesh: bool = Field(default=True, description="Optimize mesh for file size")
    scale_units: str = Field(default="feet", description="Export units (feet, meters)")


# === API Response Models ===

class UploadResponse(BaseModel):
    """Response from file upload endpoint."""
    job_id: str
    filename: str
    file_size_bytes: int
    message: str = "File uploaded successfully"


class JobStatusResponse(BaseModel):
    """Response from job status endpoint."""
    job_id: str
    status: ProcessingStatus
    current_step: str
    progress_percent: int
    processing_time: Optional[float]
    error_message: Optional[str]


class ScaleInputRequest(BaseModel):
    """Request for user scale input."""
    job_id: str
    room_type: str
    dimension_type: str  # "width" or "length"
    real_world_feet: float


class ExportRequest(BaseModel):
    """Request for 3D model export."""
    job_id: str
    export_config: ExportConfig = Field(default_factory=ExportConfig)


class ExportResponse(BaseModel):
    """Response from export endpoint."""
    job_id: str
    exported_files: Dict[str, str]  # format -> download_url
    file_sizes: Dict[str, int]  # format -> file_size_bytes
    message: str = "Export completed successfully"


