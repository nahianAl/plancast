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
  }, [currentUpdate, onStatusChange, onComplete, onError]);

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

    // Only fetch if there's no status or the status is not final
    if (jobStatus && ['completed', 'failed'].includes(jobStatus.status)) {
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const { apiClient } = await import('@/lib/api/client');
      const response = await apiClient.get(`/jobs/${jobId}/status`);
      
      const data = response.data;
      const nowIso = new Date().toISOString();
      const status: JobStatus = {
        jobId: data.job_id,
        status: data.status,
        progress: data.progress_percent || 0,
        message: data.message,
        result: data.result,
        createdAt: data.created_at ? new Date(data.created_at * 1000).toISOString() : nowIso,
        updatedAt: nowIso,
      };

      setJobStatus(status);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      onError?.(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [jobId, jobStatus, onError]);

  // Initial fetch
  useEffect(() => {
    fetchJobStatus();
  }, [fetchJobStatus]);

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
