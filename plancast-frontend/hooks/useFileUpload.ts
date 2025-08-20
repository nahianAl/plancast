import { useState, useCallback } from 'react';
import { uploadAndConvert, pollJobProgress } from '@/lib/api/floorplan';
import type { ProcessingJob, ScaleReference } from '@/lib/api';
import type { ExportFormat } from '@/lib/config';

interface UseFileUploadReturn {
  isUploading: boolean;
  uploadProgress: number;
  currentStep: string;
  jobId: string | null;
  error: string | null;
  uploadFile: (file: File, scaleReference?: ScaleReference, exportFormats?: ExportFormat[]) => Promise<string>;
  resetUpload: () => void;
}

export function useFileUpload(): UseFileUploadReturn {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState('');
  const [jobId, setJobId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const uploadFile = useCallback(async (
    file: File, 
    scaleReference?: ScaleReference, 
    exportFormats: ExportFormat[] = ['glb']
  ): Promise<string> => {
    try {
      setIsUploading(true);
      setError(null);
      setUploadProgress(0);
      setCurrentStep('Uploading file...');

      // Upload file to Railway backend
      const job = await uploadAndConvert(file, scaleReference, exportFormats);
      setJobId(job.job_id);
      setCurrentStep('File uploaded successfully! Processing...');

      try {
        // Poll job progress until completion (using correct field names)
        await pollJobProgress(
          job.job_id,
          (updatedJob) => {
            setUploadProgress(updatedJob.progress);
            setCurrentStep(getStepDescription(updatedJob.progress));
          },
          (completedJob) => {
            setUploadProgress(100);
            setCurrentStep('Processing complete!');
            setIsUploading(false);
          },
          (err) => {
            setError(err.message);
            setIsUploading(false);
          }
        );
      } catch (pollError) {
        const errorMessage = pollError instanceof Error ? pollError.message : 'Polling failed';
        setError(errorMessage);
        setIsUploading(false);
        throw pollError;
      }

      return job.job_id;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Upload failed';
      setError(errorMessage);
      setIsUploading(false);
      throw err;
    }
  }, []);

  const resetUpload = useCallback(() => {
    setIsUploading(false);
    setUploadProgress(0);
    setCurrentStep('');
    setJobId(null);
    setError(null);
  }, []);

  return {
    isUploading,
    uploadProgress,
    currentStep,
    jobId,
    error,
    uploadFile,
    resetUpload,
  };
}

// Helper function to get step description based on progress
function getStepDescription(progress: number): string {
  if (progress <= 10) return 'Uploading file...';
  if (progress <= 25) return 'AI analyzing floor plan...';
  if (progress <= 40) return 'Scaling coordinates...';
  if (progress <= 55) return 'Generating room meshes...';
  if (progress <= 70) return 'Generating wall meshes...';
  if (progress <= 80) return 'Assembling building...';
  if (progress <= 90) return 'Exporting 3D model...';
  if (progress <= 100) return 'Processing complete!';
  return 'Processing...';
}
