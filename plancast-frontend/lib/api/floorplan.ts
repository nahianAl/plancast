import { api, ApiError } from './client';
import { config, type ExportFormat, type SupportedFormat } from '@/lib/config';
import type { AxiosError } from 'axios';
import type {
  ProcessingJob,
  JobResponse,
  JobStatusResponse,
  ScaleReference,
  HealthResponse,
} from '@/types/api';

/**
 * FloorPlan Conversion API Client
 * Matches backend endpoints from plan.md
 */
export class FloorPlanAPI {
  private baseUrl: string;

  constructor() {
    this.baseUrl = config.api.baseUrl;
  }

  /**
   * Check API health status
   * Maps to backend GET /health endpoint
   */
  async checkHealth(): Promise<HealthResponse> {
    try {
      const response = await api.get<HealthResponse>('/health');
      return response.data;
    } catch (error) {
      throw ApiError.fromAxiosError(error as AxiosError);
    }
  }

  /**
   * Upload and convert floor plan
   * Maps to backend POST /convert endpoint
   */
  async uploadAndConvert(
    file: File,
    scaleReference?: ScaleReference,
    exportFormats: ExportFormat[] = ['glb']
  ): Promise<ProcessingJob> {
    try {
      // Validate file
      this.validateFile(file);

      // Create form data matching backend multipart/form-data requirements
      const formData = new FormData();
      formData.append('file', file);
      
      if (scaleReference) {
        formData.append('scale_reference', JSON.stringify(scaleReference));
      }
      
      if (exportFormats.length > 0) {
        formData.append('export_formats', JSON.stringify(exportFormats));
      }

      const response = await api.postForm<JobResponse>('/convert', formData);
      
      if (!response.data.success) {
        throw new ApiError(400, 'Upload failed', response.data.message);
      }

      return response.data.job;
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      throw ApiError.fromAxiosError(error as AxiosError);
    }
  }

  /**
   * Get job status and progress
   * Maps to backend GET /jobs/{job_id}/status endpoint
   */
  async getJobStatus(jobId: string): Promise<ProcessingJob> {
    try {
      const response = await api.get<JobStatusResponse>(`/jobs/${jobId}/status`);
      
      // Backend returns job data directly, not wrapped in success/job structure
      return response.data as ProcessingJob;
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      throw ApiError.fromAxiosError(error as AxiosError);
    }
  }

  /**
   * Download generated 3D model
   * Maps to backend GET /download/{job_id}/{format} endpoint
   */
  async downloadModel(jobId: string, format: ExportFormat): Promise<Blob> {
    try {
      const response = await api.get<Blob>(`/download/${jobId}/${format}`, {
        responseType: 'blob',
      });

      return response.data;
    } catch (error) {
      throw ApiError.fromAxiosError(error as AxiosError);
    }
  }

  /**
   * Get job list with filtering and pagination
   * Future endpoint for dashboard
   */
  async getJobList(params?: {
    status?: string;
    page?: number;
    limit?: number;
  }): Promise<{ jobs: ProcessingJob[]; total: number }> {
    try {
      const queryParams = new URLSearchParams();
      if (params?.status) queryParams.append('status', params.status);
      if (params?.page) queryParams.append('page', params.page.toString());
      if (params?.limit) queryParams.append('limit', params.limit.toString());

      const response = await api.get<{ jobs: ProcessingJob[]; total: number }>(`/jobs?${queryParams.toString()}`);
      return response.data;
    } catch (error) {
      throw ApiError.fromAxiosError(error as AxiosError);
    }
  }

  /**
   * Cancel a processing job
   * Future endpoint for job management
   */
  async cancelJob(jobId: string): Promise<boolean> {
    try {
      const response = await api.delete(`/jobs/${jobId}`);
      return response.status === 200;
    } catch (error) {
      throw ApiError.fromAxiosError(error as AxiosError);
    }
  }

  /**
   * Get processing progress with real-time updates
   * Utility function for progress tracking
   */
  async pollJobProgress(
    jobId: string,
    onProgress?: (job: ProcessingJob) => void,
    onComplete?: (job: ProcessingJob) => void,
    onError?: (error: Error) => void
  ): Promise<ProcessingJob> {
    let attempts = 0;
    const maxAttempts = config.job.maxPollingAttempts;
    const interval = config.job.statusPollingInterval;

    return new Promise((resolve, reject) => {
      const poll = async () => {
        try {
          attempts++;
          const job = await this.getJobStatus(jobId);

          // Call progress callback
          if (onProgress) {
            onProgress(job);
          }

          // Check if job is complete
          if (job.status === 'completed') {
            if (onComplete) {
              onComplete(job);
            }
            resolve(job);
            return;
          }

          // Check if job failed
          if (job.status === 'failed') {
            const error = new Error(job.error_message || 'Job processing failed');
            if (onError) {
              onError(error);
            }
            reject(error);
            return;
          }

          // Check if job was cancelled
          if (job.status === 'cancelled') {
            const error = new Error('Job was cancelled');
            if (onError) {
              onError(error);
            }
            reject(error);
            return;
          }

          // Continue polling if still processing
          if (job.status === 'processing' && attempts < maxAttempts) {
            setTimeout(poll, interval);
          } else {
            const error = new Error('Job polling timeout');
            if (onError) {
              onError(error);
            }
            reject(error);
          }
        } catch (error) {
          if (onError) {
            onError(error as Error);
          }
          reject(error);
        }
      };

      // Start polling
      poll();
    });
  }

  /**
   * Validate uploaded file
   */
  private validateFile(file: File): void {
    // Check file size
    if (file.size > config.upload.maxFileSize) {
      throw new Error(config.errors.fileTooLarge);
    }

    // Check file type
    const isValidType = config.upload.supportedFormats.includes(file.type as SupportedFormat);
    if (!isValidType) {
      throw new Error(config.errors.unsupportedFormat);
    }
  }

  /**
   * Get supported export formats
   */
  getSupportedFormats(): ExportFormat[] {
    return Object.values(config.exportFormats);
  }

  /**
   * Get file size limit in MB
   */
  getMaxFileSizeMB(): number {
    return config.upload.maxFileSize / (1024 * 1024);
  }

  /**
   * Get supported file types for display
   */
  getSupportedFileTypes(): string {
    return config.upload.supportedExtensions.join(', ');
  }
}

// Export singleton instance
export const floorPlanAPI = new FloorPlanAPI();

// Export individual functions for convenience
export const {
  checkHealth,
  uploadAndConvert,
  getJobStatus,
  downloadModel,
  getJobList,
  cancelJob,
  pollJobProgress,
} = floorPlanAPI;

export default floorPlanAPI;
