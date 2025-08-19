import { ExportFormat } from '@/lib/config';

// Backend ProcessingJob model (matching core/floorplan_processor.py)
export interface ProcessingJob {
  job_id: string;
  filename: string;
  status: JobStatus;
  progress: number; // 0-100 percentage
  created_at: string; // ISO 8601 timestamp
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  scale_reference?: ScaleReference;
  export_formats: ExportFormat[];
  input_file_path: string;
  output_files?: Record<ExportFormat, string>; // format -> file path
  processing_metadata?: {
    file_size_mb: number;
    processing_time_seconds: number;
    rooms_detected: number;
    walls_generated: number;
    mesh_vertices: number;
    mesh_faces: number;
  };
}

// Job status enum (matching backend status values)
export type JobStatus = 
  | 'pending'      // Job created, waiting to start
  | 'processing'   // Currently being processed
  | 'completed'    // Successfully completed
  | 'failed'       // Processing failed
  | 'cancelled';   // Job was cancelled

// Scale reference for coordinate scaling (matching backend coordinate_scaler.py)
export interface ScaleReference {
  room_name: string;
  width_feet: number;
  height_feet: number;
  confidence?: number; // AI confidence score (0-1)
}

// API Response types - Backend returns job data directly, not wrapped
export interface JobResponse {
  success: boolean;
  job: ProcessingJob;
  message?: string;
}

// Backend JobStatusResponse matches the actual backend response structure
export interface JobStatusResponse {
  job_id: string;
  status: JobStatus; // Use the proper JobStatus type
  current_step: string;
  progress_percent: number;
  message: string;
  created_at: number; // Unix timestamp
  started_at?: number | null; // Unix timestamp
  completed_at?: number | null; // Unix timestamp
  result?: Record<string, any> | null;
}

export interface ErrorResponse {
  success: false;
  error: string;
  details?: string;
  code?: string;
}

export interface HealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  components: {
    file_processor: 'healthy' | 'degraded' | 'unhealthy';
    cubicasa_service: 'healthy' | 'degraded' | 'unhealthy';
    coordinate_scaler: 'healthy' | 'degraded' | 'unhealthy';
    room_generator: 'healthy' | 'degraded' | 'unhealthy';
    wall_generator: 'healthy' | 'degraded' | 'unhealthy';
    mesh_exporter: 'healthy' | 'degraded' | 'unhealthy';
  };
  version: string;
  uptime_seconds: number;
}

// Backend 3D data structures (matching models/data_structures.py)
export interface Vertex3D {
  x: number;
  y: number;
  z: number;
}

export interface Face {
  indices: number[];
}

export interface Room3D {
  name: string;
  vertices: Vertex3D[];
  faces: Face[];
  elevation_feet: number;
  height_feet: number;
}

export interface Wall3D {
  id: string;
  vertices: Vertex3D[];
  faces: Face[];
  height_feet: number;
  thickness_feet: number;
}

export interface Building3D {
  rooms: Room3D[];
  walls: Wall3D[];
  units: string;
  metadata: Record<string, any>;
}

// Web preview data (matching backend WebPreviewData)
export interface WebPreviewData {
  glb_url: string;
  thumbnail_url: string;
  scene_metadata: {
    camera_position: [number, number, number];
    bounding_box: {
      min: [number, number, number];
      max: [number, number, number];
    };
    room_count: number;
    wall_count: number;
    total_vertices: number;
    total_faces: number;
  };
}

// Mesh export result (matching backend MeshExportResult)
export interface MeshExportResult {
  files: Record<ExportFormat, string>; // format -> file path
  preview_data: WebPreviewData;
  summary: {
    export_time_seconds: number;
    file_sizes: Record<ExportFormat, number>;
    compression_ratio?: number;
  };
}

// File upload types
export interface FileUploadData {
  file: File;
  scale_reference?: ScaleReference;
  export_formats?: ExportFormat[];
}

// API request types
export interface UploadRequest {
  file: File;
  scale_reference?: ScaleReference;
  export_formats?: ExportFormat[];
}

// Utility types
export type ApiResponse<T> = T | ErrorResponse;

export interface PaginationParams {
  page?: number;
  limit?: number;
  offset?: number;
}

export interface SortParams {
  sort_by?: 'created_at' | 'filename' | 'status' | 'progress';
  sort_order?: 'asc' | 'desc';
}

export interface JobListParams extends PaginationParams, SortParams {
  status?: JobStatus;
  created_after?: string;
  created_before?: string;
}
