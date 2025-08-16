'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { 
  ArrowLeft, 
  Download, 
  Eye, 
  FileText, 
  CheckCircle,
  AlertCircle,
  Loader2
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import ThreeViewer from '@/components/viewer/ThreeViewer';
import { getJobStatus } from '@/lib/api/floorplan';
import { downloadAndSave } from '@/lib/api/download';
import { config, type ExportFormat } from '@/lib/config';
import type { ProcessingJob } from '@/lib/api';
import type { GLTF } from 'three/addons/loaders/GLTFLoader.js';

export default function PreviewPage() {
  const params = useParams();
  const router = useRouter();
  const jobId = params.jobId as string;

  const [job, setJob] = useState<ProcessingJob | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isDownloading, setIsDownloading] = useState<Record<ExportFormat, boolean>>({
    glb: false,
    obj: false,
    stl: false,
    skp: false,
    fbx: false,
    dwg: false
  });
  const [downloadProgress, setDownloadProgress] = useState<Record<ExportFormat, number>>({
    glb: 0,
    obj: 0,
    stl: 0,
    skp: 0,
    fbx: 0,
    dwg: 0
  });

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

  useEffect(() => {
    if (jobId) {
      loadJobStatus();
    }
  }, [jobId, loadJobStatus]);

  const handleDownload = async (format: ExportFormat) => {
    if (!job) return;

    try {
      setIsDownloading(prev => ({ ...prev, [format]: true }));
      setDownloadProgress(prev => ({ ...prev, [format]: 0 }));

      // Simulate download progress
      const progressInterval = setInterval(() => {
        setDownloadProgress(prev => ({
          ...prev,
          [format]: Math.min(prev[format] + Math.random() * 20, 90)
        }));
      }, 100);

      await downloadAndSave(jobId, format);
      
      clearInterval(progressInterval);
      setDownloadProgress(prev => ({ ...prev, [format]: 100 }));
      
      // Reset progress after a delay
      setTimeout(() => {
        setDownloadProgress(prev => ({ ...prev, [format]: 0 }));
      }, 2000);

    } catch (err) {
      console.error(`Download failed for ${format}:`, err);
      setError(`Failed to download ${format.toUpperCase()} file`);
    } finally {
      setIsDownloading(prev => ({ ...prev, [format]: false }));
    }
  };

  const handleModelLoad = (model: GLTF) => {
    console.log('3D model loaded successfully:', model);
  };

  const handleModelError = (error: string) => {
    setError(`3D model error: ${error}`);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-blue-500 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading job details...</p>
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
                  <Loader2 className="w-4 h-4 mr-2" />
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

  if (job.status !== 'completed') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 py-12">
        <div className="container mx-auto px-4 max-w-2xl">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-yellow-500" />
                Job Not Ready
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-700 mb-4">
                This job is not yet completed. Current status: <strong>{job.status}</strong>
              </p>
              <div className="flex gap-3">
                <Button onClick={() => router.back()} variant="outline">
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Go Back
                </Button>
                <Button onClick={() => router.push(`/convert/status/${jobId}`)}>
                  <Eye className="w-4 h-4 mr-2" />
                  Check Status
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                onClick={() => router.back()}
                variant="ghost"
                size="sm"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back
              </Button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  3D Model Preview
                </h1>
                <p className="text-gray-600">Job ID: {jobId}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="default" className="bg-green-100 text-green-800">
                <CheckCircle className="w-3 h-3 mr-1" />
                Completed
              </Badge>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-6">
        <div className="grid lg:grid-cols-4 gap-6">
          {/* 3D Viewer */}
          <div className="lg:col-span-3">
            <Card className="h-[600px]">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Eye className="w-5 h-5" />
                  3D Model Viewer
                </CardTitle>
                <CardDescription>
                  Interactive 3D preview of your converted floor plan
                </CardDescription>
              </CardHeader>
              <CardContent className="p-0 h-full">
                <ThreeViewer
                  jobId={jobId}
                  onModelLoad={handleModelLoad}
                  onError={handleModelError}
                />
              </CardContent>
            </Card>
          </div>

          {/* Download Panel */}
          <div className="space-y-6">
            {/* Job Info */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Job Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <p className="text-sm font-medium text-gray-700">Filename</p>
                  <p className="text-sm text-gray-900">{job.filename}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-700">Created</p>
                  <p className="text-sm text-gray-900">
                    {job.created_at && new Date(job.created_at).toLocaleDateString()}
                  </p>
                </div>
                {job.processing_metadata && (
                  <div>
                    <p className="text-sm font-medium text-gray-700">Processing Time</p>
                    <p className="text-sm text-gray-900">
                      {job.processing_metadata.processing_time_seconds.toFixed(1)}s
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Export Options */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Export Options</CardTitle>
                <CardDescription>
                  Download your 3D model in different formats
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {Object.entries(config.exportFormats).map(([key, format]) => {
                  const isCurrentlyDownloading = isDownloading[format];
                  const progress = downloadProgress[format];
                  
                  return (
                    <div key={format} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <FileText className="w-4 h-4 text-gray-500" />
                          <span className="text-sm font-medium">{key.toUpperCase()}</span>
                        </div>
                        <Button
                          onClick={() => handleDownload(format)}
                          disabled={isCurrentlyDownloading}
                          size="sm"
                          variant="outline"
                          className="w-20"
                        >
                          {isCurrentlyDownloading ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                          ) : (
                            <Download className="w-4 h-4" />
                          )}
                        </Button>
                      </div>
                      
                      {isCurrentlyDownloading && progress > 0 && (
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                            style={{ width: `${progress}%` }}
                          />
                        </div>
                      )}
                      
                      {progress === 100 && (
                        <div className="flex items-center gap-2 text-green-600 text-sm">
                          <CheckCircle className="w-4 h-4" />
                          Downloaded successfully
                        </div>
                      )}
                    </div>
                  );
                })}
              </CardContent>
            </Card>

            {/* Model Statistics */}
            {job.processing_metadata && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Model Statistics</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="font-medium text-gray-700">Rooms</p>
                      <p className="text-gray-900">{job.processing_metadata.rooms_detected}</p>
                    </div>
                    <div>
                      <p className="font-medium text-gray-700">Walls</p>
                      <p className="text-gray-900">{job.processing_metadata.walls_generated}</p>
                    </div>
                    <div>
                      <p className="font-medium text-gray-700">Vertices</p>
                      <p className="text-gray-900">
                        {job.processing_metadata.mesh_vertices.toLocaleString()}
                      </p>
                    </div>
                    <div>
                      <p className="font-medium text-gray-700">Faces</p>
                      <p className="text-gray-900">
                        {job.processing_metadata.mesh_faces.toLocaleString()}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
