'use client';

import { useState, useEffect, useCallback } from 'react';
import { useWebSocketContext } from '@/lib/websocket-context';
import { JobStatusUpdate } from './useWebSocket';

export interface JobStatus {
  jobId: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  message?: string;
  result?: any;
  createdAt: string;
  updatedAt: string;
}

interface UseJobStatusOptions {
  jobId: string;
  autoSubscribe?: boolean;
  onStatusChange?: (status: JobStatusUpdate) => void;
  onComplete?: (result: any) => void;
  onError?: (error: string) => void;
}

export const useJobStatus = (options: UseJobStatusOptions) => {
  const {
    jobId,
    autoSubscribe = true,
    onStatusChange,
    onComplete,
    onError,
  } = options;

  const { jobUpdates, subscribeToJob, unsubscribeFromJob, isConnected } = useWebSocketContext();
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Get current job status from WebSocket updates
  const currentUpdate = jobUpdates.get(jobId);

  // Update local job status when WebSocket updates arrive
  useEffect(() => {
    if (currentUpdate) {
      const newStatus: JobStatus = {
        jobId: currentUpdate.jobId,
        status: currentUpdate.status,
        progress: currentUpdate.progress,
        message: currentUpdate.message,
        result: currentUpdate.result,
        createdAt: jobStatus?.createdAt || new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };

      setJobStatus(newStatus);
      setIsLoading(false);
      setError(null);

      // Call callbacks
      onStatusChange?.(currentUpdate);

      if (currentUpdate.status === 'completed') {
        onComplete?.(currentUpdate.result);
      } else if (currentUpdate.status === 'failed') {
        onError?.(currentUpdate.message || 'Job failed');
        setError(currentUpdate.message || 'Job failed');
      }
    }
  }, [currentUpdate, jobStatus?.createdAt, onStatusChange, onComplete, onError]);

  // Subscribe to job updates
  useEffect(() => {
    if (autoSubscribe && isConnected && jobId) {
      subscribeToJob(jobId);

      return () => {
        unsubscribeFromJob(jobId);
      };
    }
  }, [autoSubscribe, isConnected, jobId, subscribeToJob, unsubscribeFromJob]);

  // Fetch initial job status from API
  const fetchJobStatus = useCallback(async () => {
    if (!jobId) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/jobs/${jobId}/status`);
      if (!response.ok) {
        throw new Error('Failed to fetch job status');
      }

      const data = await response.json();
      const status: JobStatus = {
        jobId: data.job_id,
        status: data.status,
        progress: data.progress || 0,
        message: data.message,
        result: data.result,
        createdAt: data.created_at,
        updatedAt: data.updated_at,
      };

      setJobStatus(status);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      onError?.(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [jobId, onError]);

  // Manual refresh function
  const refresh = useCallback(() => {
    fetchJobStatus();
  }, [fetchJobStatus]);

  // Subscribe/unsubscribe manually
  const subscribe = useCallback(() => {
    if (isConnected && jobId) {
      subscribeToJob(jobId);
    }
  }, [isConnected, jobId, subscribeToJob]);

  const unsubscribe = useCallback(() => {
    if (jobId) {
      unsubscribeFromJob(jobId);
    }
  }, [jobId, unsubscribeFromJob]);

  return {
    jobStatus,
    isLoading,
    error,
    isConnected,
    refresh,
    subscribe,
    unsubscribe,
    // Convenience getters
    isCompleted: jobStatus?.status === 'completed',
    isFailed: jobStatus?.status === 'failed',
    isProcessing: jobStatus?.status === 'processing',
    isPending: jobStatus?.status === 'pending',
    progress: jobStatus?.progress || 0,
  };
};

export default useJobStatus;
