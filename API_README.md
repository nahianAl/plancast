# PlanCast API Documentation

## Overview

PlanCast is an AI-powered floor plan to 3D model conversion service. This FastAPI application provides RESTful endpoints for uploading floor plans, processing them through the AI pipeline, and downloading the resulting 3D models.

## Features

- **File Upload**: Support for JPG, PNG, and PDF floor plans
- **AI Processing**: CubiCasa5K neural network for intelligent floor plan analysis
- **3D Generation**: Automatic conversion to 3D models with rooms and walls
- **Multiple Export Formats**: GLB, OBJ, STL, FBX, SKP
- **Real-time Progress**: Job status tracking with progress updates
- **Background Processing**: Asynchronous file processing
- **Production Ready**: Comprehensive error handling and logging

## Quick Start

### Local Development

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the server**:
   ```bash
   python start.py
   ```

3. **Access the API**:
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Railway Deployment

The application is configured for Railway deployment with:
- Automatic PORT environment variable handling
- Production-optimized settings
- Health check endpoints

## API Endpoints

### Health Check

```http
GET /health
```

**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "pipeline_ready": true,
  "timestamp": 1703123456.789
}
```

### File Upload & Conversion

```http
POST /convert
```

**Parameters**:
- `file`: Floor plan file (JPG, PNG, PDF)
- `scale_reference` (optional): JSON string with scaling information
- `export_formats` (optional): Comma-separated list of formats (default: "glb,obj,stl")

**Example**:
```bash
curl -X POST "http://localhost:8000/convert" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@floorplan.jpg" \
  -F "export_formats=glb,obj,stl" \
  -F 'scale_reference={"room_type": "kitchen", "dimension_type": "width", "real_world_feet": 12.0, "pixel_measurement": 240.0}'
```

**Response**:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "message": "Upload successful",
  "filename": "floorplan.jpg",
  "file_size_bytes": 245760
}
```

### Job Status

```http
GET /jobs/{job_id}/status
```

**Response**:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "current_step": "export",
  "progress_percent": 100,
  "processing_time": 15.23,
  "error_message": null
}
```

### Download 3D Model

```http
GET /download/{job_id}/{format}
```

**Supported formats**: `glb`, `obj`, `stl`, `fbx`, `skp`

**Example**:
```bash
curl -O -J "http://localhost:8000/download/550e8400-e29b-41d4-a716-446655440000/glb"
```

### Job Results

```http
GET /jobs/{job_id}/results
```

**Response**:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "filename": "floorplan.jpg",
  "exported_files": {
    "glb": "output/generated_models/floorplan_glb.glb",
    "obj": "output/generated_models/floorplan_obj.obj",
    "stl": "output/generated_models/floorplan_stl.stl"
  },
  "processing_time": 15.23,
  "completed_at": 1703123471.012,
  "warnings": []
}
```

### List Jobs

```http
GET /jobs?limit=50&offset=0
```

**Response**:
```json
{
  "jobs": [
    {
      "job_id": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "floorplan.jpg",
      "status": "completed",
      "created_at": 1703123456.789,
      "progress_percent": 100
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

### Delete Job

```http
DELETE /jobs/{job_id}
```

**Response**:
```json
{
  "message": "Job 550e8400-e29b-41d4-a716-446655440000 deleted successfully"
}
```

## Processing Pipeline

The PlanCast pipeline consists of 7 main steps:

1. **File Processing** (10%) - Validate and prepare uploaded file
2. **AI Analysis** (25%) - CubiCasa5K neural network analysis
3. **Coordinate Scaling** (40%) - Convert pixels to real-world measurements
4. **Room Generation** (55%) - Create 3D room meshes
5. **Wall Generation** (70%) - Create 3D wall meshes
6. **Building Assembly** (80%) - Combine rooms and walls
7. **Export** (90-100%) - Generate 3D model files

## Error Handling

The API provides comprehensive error handling:

- **400 Bad Request**: Invalid file format, missing parameters
- **404 Not Found**: Job not found, file not found
- **500 Internal Server Error**: Processing errors, system failures

**Error Response Format**:
```json
{
  "error": "File format not supported",
  "message": "File format not supported",
  "job_id": null,
  "timestamp": 1703123456.789
}
```

## File Format Support

### Input Formats
- **JPG/JPEG**: Standard image format
- **PNG**: Lossless image format
- **PDF**: Single-page PDF documents

### Output Formats
- **GLB**: Binary glTF (recommended for web)
- **OBJ**: Wavefront OBJ (universal 3D format)
- **STL**: Stereolithography (3D printing)
- **FBX**: Autodesk FBX (animation/game engines)
- **SKP**: SketchUp format (architecture software)

## Scale Reference

For accurate 3D models, you can provide scaling information:

```json
{
  "room_type": "kitchen",
  "dimension_type": "width",
  "real_world_feet": 12.0,
  "pixel_measurement": 240.0
}
```

This tells the system: "The kitchen width is 12 feet and measures 240 pixels in the image."

## Testing

Run the test suite:

```bash
python test_api.py
```

This will test all endpoints and verify the API is working correctly.

## Configuration

### Environment Variables

- `PORT`: Server port (default: 8000)
- `HOST`: Server host (default: 0.0.0.0)
- `DEBUG`: Enable debug mode (default: false)
- `LOG_LEVEL`: Logging level (default: info)

### File Size Limits

- **Maximum upload size**: 50MB
- **Supported file types**: JPG, PNG, PDF
- **Processing timeout**: 300 seconds

## Production Deployment

### Railway

1. Connect your repository to Railway
2. Set environment variables if needed
3. Deploy automatically

### Docker

```bash
docker build -t plancast-api .
docker run -p 8000:8000 plancast-api
```

### Manual Deployment

1. Install dependencies: `pip install -r requirements.txt`
2. Start the server: `python start.py`
3. Configure reverse proxy (nginx/Apache) if needed

## Monitoring

### Health Checks

Monitor the `/health` endpoint for service availability.

### Logging

The application uses structured logging with:
- Request/response logging
- Error tracking
- Performance metrics
- Processing pipeline events

### Metrics

Key metrics to monitor:
- Upload success rate
- Processing time
- Error rates
- File format distribution

## Security

- File upload validation
- MIME type checking
- Path traversal prevention
- Size limits enforcement
- CORS configuration

## Support

For issues and questions:
1. Check the API documentation at `/docs`
2. Review error messages in logs
3. Test with the provided test suite
4. Contact the development team

## License

PlanCast API is proprietary software. All rights reserved.
