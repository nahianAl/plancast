// Export all API modules
export * from './client';
export * from './floorplan';

// Re-export types for convenience
export type {
  ProcessingJob,
  JobStatus,
  ScaleReference,
  JobResponse,
  JobStatusResponse,
  ErrorResponse,
  HealthResponse,
  Vertex3D,
  Face,
  Room3D,
  Wall3D,
  Building3D,
  WebPreviewData,
  MeshExportResult,
  FileUploadData,
  UploadRequest,
  ApiResponse,
  PaginationParams,
  SortParams,
  JobListParams,
} from '@/types/api';

// Export configuration
export { config } from '@/lib/config';
export type {
  SupportedFormat,
  SupportedExtension,
  JobProgressStep,
} from '@/lib/config';
