import { downloadModel as downloadModelFromFloorplan } from './floorplan';
import type { ExportFormat } from '@/lib/config';

// Rename the function to avoid conflicts
const downloadModelFromAPI = downloadModelFromFloorplan;

/**
 * Download API for 3D models
 * Handles model downloads in various formats
 */
export class DownloadAPI {
  /**
   * Download a 3D model in the specified format
   * @param jobId - The job ID to download
   * @param format - The export format (GLB, OBJ, STL, SKP, FBX)
   * @returns Promise<Blob> - The model file as a blob
   */
  static async downloadModel(jobId: string, format: ExportFormat): Promise<Blob> {
    try {
      return await downloadModelFromAPI(jobId, format);
    } catch (error) {
      console.error(`Failed to download model in ${format} format:`, error);
      throw error;
    }
  }

  /**
   * Trigger browser download of a blob
   * @param blob - The file blob to download
   * @param filename - The filename for the download
   */
  static triggerDownload(blob: Blob, filename: string): void {
    // Create a temporary URL for the blob
    const url = window.URL.createObjectURL(blob);
    
    // Create a temporary link element
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    
    // Append to DOM, click, and cleanup
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    // Clean up the URL object
    window.URL.revokeObjectURL(url);
  }

  /**
   * Download and trigger browser download for a model
   * @param jobId - The job ID to download
   * @param format - The export format
   * @param filename - Optional custom filename
   */
  static async downloadAndSave(jobId: string, format: ExportFormat, filename?: string): Promise<void> {
    try {
      const blob = await this.downloadModel(jobId, format);
      
      // Generate filename if not provided
      const defaultFilename = `plancast-model-${jobId}.${format}`;
      const finalFilename = filename || defaultFilename;
      
      this.triggerDownload(blob, finalFilename);
    } catch (error) {
      console.error('Download failed:', error);
      throw error;
    }
  }

  /**
   * Get the MIME type for a given export format
   * @param format - The export format
   * @returns string - The MIME type
   */
  static getMimeType(format: ExportFormat): string {
    const mimeTypes: Record<ExportFormat, string> = {
      glb: 'model/gltf-binary',
      obj: 'text/plain',
      stl: 'application/sla',
      skp: 'application/octet-stream',
      fbx: 'application/octet-stream',
      dwg: 'application/acad'
    };
    
    return mimeTypes[format] || 'application/octet-stream';
  }

  /**
   * Get the file extension for a given export format
   * @param format - The export format
   * @returns string - The file extension
   */
  static getFileExtension(format: ExportFormat): string {
    return `.${format}`;
  }

  /**
   * Format file size in human-readable format
   * @param bytes - File size in bytes
   * @returns string - Formatted file size
   */
  static formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }
}

// Export individual functions for convenience
export const {
  triggerDownload,
  downloadAndSave,
  getMimeType,
  getFileExtension,
  formatFileSize
} = DownloadAPI;

export default DownloadAPI;
