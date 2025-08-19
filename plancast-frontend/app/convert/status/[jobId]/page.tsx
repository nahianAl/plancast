'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { 
  CheckCircle, 
  Clock, 
  AlertCircle, 
  Download, 
  Eye, 
  ArrowLeft,
  RefreshCw
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { getJobStatus, pollJobProgress } from '@/lib/api/floorplan';
import { config } from '@/lib/config';
import type { ProcessingJob, JobStatus } from '@/types/api';

export default function JobStatusPage() {
  const params = useParams();
  const router = useRouter();
  const jobId = params.jobId as string;

  const [job, setJob] = useState<ProcessingJob | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isPolling, setIsPolling] = useState(false);

  const loadJobStatus = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const jobData = await getJobStatus(jobId);
      setJob(jobData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load job status');
    } finally {
      setIsLoading(false);
    }
  }, [jobId]);

  const startPolling = useCallback(() => {
    if (isPolling) return;
    
    setIsPolling(true);
    pollJobProgress(
      jobId,
      (updatedJob) => {
        setJob(updatedJob);
      },
      (completedJob) => {
        setJob(completedJob);
        setIsPolling(false);
      },
      (err) => {
        setError(err.message);
        setIsPolling(false);
      }
    );
  }, [jobId, isPolling]);

  useEffect(() => {
    if (jobId) {
      loadJobStatus();
    }
  }, [jobId, loadJobStatus]);

  useEffect(() => {
    if (job && job.status === 'processing') {
      startPolling();
    }
    return () => {
      setIsPolling(false);
    };
  }, [job, startPolling]);

  const getStatusIcon = (status: JobStatus) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-6 h-6 text-green-500" />;
      case 'processing':
        return <Clock className="w-6 h-6 text-blue-500 animate-pulse" />;
      case 'failed':
        return <AlertCircle className="w-6 h-6 text-red-500" />;
      case 'pending':
        return <Clock className="w-6 h-6 text-yellow-500" />;
      default:
        return <Clock className="w-6 h-6 text-gray-500" />;
    }
  };

  const getStatusBadge = (status: JobStatus) => {
    const variants = {
      completed: 'bg-green-100 text-green-800',
      processing: 'bg-blue-100 text-blue-800',
      failed: 'bg-red-100 text-red-800',
      pending: 'bg-yellow-100 text-yellow-800',
      cancelled: 'bg-gray-100 text-gray-800'
    };

    return (
      <Badge className={variants[status] || 'bg-gray-100 text-gray-800'}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </Badge>
    );
  };

  const getStepDescription = (progress: number) => {
    if (progress <= 10) return 'Uploading file...';
    if (progress <= 25) return 'AI analyzing floor plan...';
    if (progress <= 40) return 'Scaling coordinates...';
    if (progress <= 55) return 'Generating room meshes...';
    if (progress <= 70) return 'Generating wall meshes...';
    if (progress <= 80) return 'Assembling building...';
    if (progress <= 90) return 'Exporting 3D model...';
    if (progress <= 100) return 'Processing complete!';
    return 'Processing...';
  };

  const getStepIcon = (stepProgress: number, currentProgress: number) => {
    if (currentProgress >= stepProgress) {
      return <CheckCircle className="w-5 h-5 text-green-500" />;
    } else if (currentProgress >= stepProgress - 10) {
      return <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />;
    } else {
      return <div className="w-5 h-5 border-2 border-gray-300 rounded-full" />;
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading job status...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 py-12">
        <div className="container mx-auto px-4 max-w-2xl">
          <Card className="border-red-200 bg-red-50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-red-700">
                <AlertCircle className="w-5 h-5" />
                Error Loading Job
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-red-700 mb-4">{error}</p>
              <div className="flex gap-3">
                <Button onClick={() => router.back()} variant="outline">
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Go Back
                </Button>
                <Button onClick={loadJobStatus}>
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Retry
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 py-12">
        <div className="container mx-auto px-4 max-w-2xl">
          <Card>
            <CardContent className="pt-6 text-center">
              <p className="text-gray-600 mb-4">Job not found</p>
              <Button onClick={() => router.back()} variant="outline">
                <ArrowLeft className="w-4 h-4 mr-2" />
                Go Back
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 py-12">
      <div className="container mx-auto px-4 max-w-4xl">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="mb-8"
        >
          <div className="flex items-center gap-4 mb-6">
            <Button
              onClick={() => router.back()}
              variant="ghost"
              size="sm"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
            <div>
              <h1 className="text-3xl md:text-4xl font-bold text-gray-900">
                Job Status
              </h1>
              <p className="text-gray-600">Job ID: {jobId}</p>
            </div>
          </div>

          {/* Job Overview */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    {getStatusIcon(job.status)}
                    {job.filename}
                  </CardTitle>
                  <CardDescription>
                    {job.created_at && new Date(job.created_at).toLocaleString()}
                  </CardDescription>
                </div>
                {getStatusBadge(job.status)}
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-3 gap-4 text-sm">
                <div>
                  <span className="font-medium text-gray-700">Status:</span>
                  <p className="text-gray-900">{job.status}</p>
                </div>
                <div>
                  <span className="font-medium text-gray-700">Progress:</span>
                  <p className="text-gray-900">{job.progress}%</p>
                </div>
                <div>
                  <span className="font-medium text-gray-700">Export Formats:</span>
                  <p className="text-gray-900">{job.export_formats.join(', ').toUpperCase()}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Progress Tracking */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="mb-8"
        >
          <Card>
            <CardHeader>
              <CardTitle>Processing Progress</CardTitle>
              <CardDescription>
                {getStepDescription(job.progress)}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <Progress value={job.progress} className="w-full" />
              
              {/* Pipeline Steps */}
              <div className="space-y-4">
                <h4 className="font-medium text-gray-900">Pipeline Steps</h4>
                <div className="grid gap-3">
                  {Object.entries(config.job.progressSteps).map(([step, progress]) => (
                    <div key={step} className="flex items-center gap-3">
                      {getStepIcon(progress, job.progress)}
                      <div className="flex-1">
                        <p className="text-sm font-medium text-gray-900">
                          {step.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </p>
                        <p className="text-xs text-gray-500">{progress}%</p>
                      </div>
                      {job.progress >= progress && (
                        <CheckCircle className="w-4 h-4 text-green-500" />
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Processing Details */}
        {job.processing_metadata && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="mb-8"
          >
            <Card>
              <CardHeader>
                <CardTitle>Processing Details</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="font-medium text-gray-700">File Size:</span>
                    <p className="text-gray-900">{job.processing_metadata.file_size_mb.toFixed(2)} MB</p>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Processing Time:</span>
                    <p className="text-gray-900">{job.processing_metadata.processing_time_seconds.toFixed(1)}s</p>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Rooms Detected:</span>
                    <p className="text-gray-900">{job.processing_metadata.rooms_detected}</p>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Walls Generated:</span>
                    <p className="text-gray-900">{job.processing_metadata.walls_generated}</p>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Mesh Vertices:</span>
                    <p className="text-gray-900">{job.processing_metadata.mesh_vertices.toLocaleString()}</p>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Mesh Faces:</span>
                    <p className="text-gray-900">{job.processing_metadata.mesh_faces.toLocaleString()}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Actions */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.6 }}
          className="flex flex-col sm:flex-row gap-4 justify-center"
        >
          {job.status === 'completed' && (
            <>
              <Button
                onClick={() => router.push(`/convert/preview/${jobId}`)}
                size="lg"
                className="bg-blue-500 hover:bg-blue-600 text-white"
              >
                <Eye className="w-5 h-5 mr-2" />
                View 3D Model
              </Button>
              <Button
                onClick={() => router.push(`/convert/export/${jobId}`)}
                size="lg"
                variant="outline"
              >
                <Download className="w-5 h-5 mr-2" />
                Download Files
              </Button>
            </>
          )}

          {job.status === 'processing' && (
            <Button
              onClick={startPolling}
              disabled={isPolling}
              size="lg"
              variant="outline"
            >
              <RefreshCw className={`w-5 h-5 mr-2 ${isPolling ? 'animate-spin' : ''}`} />
              {isPolling ? 'Refreshing...' : 'Refresh Status'}
            </Button>
          )}

          {job.status === 'failed' && (
            <Button
              onClick={() => router.push('/convert/upload')}
              size="lg"
              className="bg-red-500 hover:bg-red-600 text-white"
            >
              Try Again
            </Button>
          )}
        </motion.div>
      </div>
    </div>
  );
}
