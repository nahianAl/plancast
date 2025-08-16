'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { Upload, Settings, ArrowRight, CheckCircle, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import FileUploadZone from '@/components/upload/FileUploadZone';
import { useFileUpload } from '@/hooks/useFileUpload';
import { config, type ExportFormat } from '@/lib/config';
import type { ScaleReference } from '@/lib/api';

export default function UploadPage() {
  const router = useRouter();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [scaleReference, setScaleReference] = useState<ScaleReference>({
    room_name: '',
    width_feet: 0,
    height_feet: 0
  });
  const [exportFormats, setExportFormats] = useState<ExportFormat[]>(['glb']);

  const {
    isUploading,
    uploadProgress,
    currentStep,
    jobId,
    error,
    uploadFile,
    resetUpload
  } = useFileUpload();

  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
    resetUpload();
  };

  const handleClearFile = () => {
    setSelectedFile(null);
    resetUpload();
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    try {
      const jobId = await uploadFile(selectedFile, scaleReference, exportFormats);
      console.log('Upload successful, job ID:', jobId);
    } catch (err) {
      console.error('Upload failed:', err);
    }
  };

  const handleCheckStatus = () => {
    if (jobId) {
      router.push(`/convert/status/${jobId}`);
    }
  };

  const handleGoToPreview = () => {
    if (jobId) {
      router.push(`/convert/preview/${jobId}`);
    }
  };

  const toggleExportFormat = (format: ExportFormat) => {
    setExportFormats(prev => 
      prev.includes(format) 
        ? prev.filter(f => f !== format)
        : [...prev, format]
    );
  };

  const isUploadReady = selectedFile && !isUploading && !jobId;
  const isProcessing = isUploading || (jobId && uploadProgress < 100);
  const isComplete = jobId && uploadProgress === 100;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 py-12">
      <div className="container mx-auto px-4 max-w-4xl">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center mb-12"
        >
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
            Convert Your Floor Plan
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Upload a JPG, PNG, or PDF floor plan and get a professional 3D model in minutes
          </p>
        </motion.div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Main Upload Area */}
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Upload className="w-5 h-5" />
                  Upload Floor Plan
                </CardTitle>
                <CardDescription>
                  Drag and drop your file or click to browse
                </CardDescription>
              </CardHeader>
              <CardContent>
                <FileUploadZone
                  onFileSelect={handleFileSelect}
                  selectedFile={selectedFile}
                  onClearFile={handleClearFile}
                  isUploading={isUploading}
                />
              </CardContent>
            </Card>

            {/* Advanced Options */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Settings className="w-5 h-5" />
                  Advanced Options
                </CardTitle>
                <CardDescription>
                  Optional settings for better accuracy
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Button
                  variant="outline"
                  onClick={() => setShowAdvanced(!showAdvanced)}
                  className="w-full"
                >
                  {showAdvanced ? 'Hide' : 'Show'} Advanced Options
                </Button>

                {showAdvanced && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="space-y-4 pt-4 border-t"
                  >
                    {/* Scale Reference */}
                    <div className="space-y-2">
                      <Label htmlFor="room-name">Room Name for Scale Reference</Label>
                      <Input
                        id="room-name"
                        placeholder="e.g., Living Room, Kitchen"
                        value={scaleReference.room_name}
                        onChange={(e) => setScaleReference(prev => ({ ...prev, room_name: e.target.value }))}
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="width">Width (feet)</Label>
                        <Input
                          id="width"
                          type="number"
                          placeholder="12"
                          value={scaleReference.width_feet || ''}
                          onChange={(e) => setScaleReference(prev => ({ ...prev, width_feet: parseFloat(e.target.value) || 0 }))}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="height">Height (feet)</Label>
                        <Input
                          id="height"
                          type="number"
                          placeholder="15"
                          value={scaleReference.height_feet || ''}
                          onChange={(e) => setScaleReference(prev => ({ ...prev, height_feet: parseFloat(e.target.value) || 0 }))}
                        />
                      </div>
                    </div>

                    {/* Export Formats */}
                    <div className="space-y-2">
                      <Label>Export Formats</Label>
                      <div className="flex flex-wrap gap-2">
                        {Object.entries(config.exportFormats).map(([key, format]) => (
                          <Badge
                            key={format}
                            variant={exportFormats.includes(format) ? 'default' : 'outline'}
                            className={`cursor-pointer ${
                              exportFormats.includes(format) ? 'bg-blue-500' : 'hover:bg-gray-100'
                            }`}
                            onClick={() => toggleExportFormat(format)}
                          >
                            {key.toUpperCase()}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </motion.div>
                )}
              </CardContent>
            </Card>

            {/* Upload Button */}
            {isUploadReady && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4 }}
              >
                <Button
                  onClick={handleUpload}
                  size="lg"
                  className="w-full bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 text-white"
                >
                  Convert to 3D Model
                  <ArrowRight className="ml-2 w-5 h-5" />
                </Button>
              </motion.div>
            )}

            {/* Progress Tracking */}
            {isProcessing && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4 }}
              >
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      {isComplete ? (
                        <CheckCircle className="w-5 h-5 text-green-500" />
                      ) : (
                        <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                      )}
                      {currentStep}
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <Progress value={uploadProgress} className="w-full" />
                    <div className="flex justify-between text-sm text-gray-600">
                      <span>Progress: {uploadProgress}%</span>
                      {jobId && <span>Job ID: {jobId}</span>}
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            )}

            {/* Error Display */}
            {error && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4 }}
              >
                <Card className="border-red-200 bg-red-50">
                  <CardContent className="pt-6">
                    <div className="flex items-center gap-2 text-red-700">
                      <AlertCircle className="w-5 h-5" />
                      <span className="font-medium">Error: {error}</span>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            )}

            {/* Success Actions */}
            {isComplete && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4 }}
                className="space-y-3"
              >
                <Button
                  onClick={handleGoToPreview}
                  size="lg"
                  className="w-full bg-green-500 hover:bg-green-600 text-white"
                >
                  View 3D Model
                  <ArrowRight className="ml-2 w-5 h-5" />
                </Button>
                <Button
                  onClick={handleCheckStatus}
                  variant="outline"
                  className="w-full"
                >
                  Check Job Status
                </Button>
              </motion.div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>How It Works</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex items-start gap-3">
                    <div className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium">
                      1
                    </div>
                    <div>
                      <p className="font-medium text-sm">Upload Floor Plan</p>
                      <p className="text-xs text-gray-500">JPG, PNG, or PDF up to 50MB</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium">
                      2
                    </div>
                    <div>
                      <p className="font-medium text-sm">AI Processing</p>
                      <p className="text-xs text-gray-500">Neural networks analyze and convert</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium">
                      3
                    </div>
                    <div>
                      <p className="font-medium text-sm">Download 3D Model</p>
                      <p className="text-xs text-gray-500">Multiple formats available</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Supported Formats</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm">Input:</span>
                    <span className="text-sm text-gray-600">JPG, PNG, PDF</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm">Output:</span>
                    <span className="text-sm text-gray-600">GLB, OBJ, SKP, STL, FBX</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm">Max Size:</span>
                    <span className="text-sm text-gray-600">50MB</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
