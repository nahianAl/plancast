'use client';

import { useCallback, useState } from 'react';
import { useDropzone, type FileRejection } from 'react-dropzone';
import { Upload, X, FileImage, FileText, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { config } from '@/lib/config';

interface FileUploadZoneProps {
  onFileSelect: (file: File) => void;
  selectedFile: File | null;
  onClearFile: () => void;
  isUploading?: boolean;
}

export default function FileUploadZone({ 
  onFileSelect, 
  selectedFile, 
  onClearFile, 
  isUploading = false 
}: FileUploadZoneProps) {
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback((acceptedFiles: File[], rejectedFiles: FileRejection[]) => {
    setError(null);
    
    if (rejectedFiles.length > 0) {
      const rejection = rejectedFiles[0];
      if (rejection.errors[0]?.code === 'file-too-large') {
        setError(config.errors.fileTooLarge);
      } else if (rejection.errors[0]?.code === 'file-invalid-type') {
        setError(config.errors.unsupportedFormat);
      } else {
        setError('File rejected. Please try again.');
      }
      return;
    }

    if (acceptedFiles.length > 0) {
      onFileSelect(acceptedFiles[0]);
    }
  }, [onFileSelect]);

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: {
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/png': ['.png'],
      'application/pdf': ['.pdf']
    },
    maxSize: config.upload.maxFileSize,
    maxFiles: 1,
    disabled: isUploading
  });

  const getFileIcon = (file: File) => {
    if (file.type.startsWith('image/')) {
      return <FileImage className="w-8 h-8 text-blue-500" />;
    } else if (file.type === 'application/pdf') {
      return <FileText className="w-8 h-8 text-red-500" />;
    }
    return <FileText className="w-8 h-8 text-gray-500" />;
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (selectedFile) {
    return (
      <div className="w-full">
        <div className="border-2 border-dashed border-green-200 bg-green-50 rounded-lg p-6 text-center">
          <div className="flex items-center justify-center space-x-3 mb-4">
            {getFileIcon(selectedFile)}
            <div className="text-left">
              <p className="font-medium text-gray-900">{selectedFile.name}</p>
              <p className="text-sm text-gray-500">{formatFileSize(selectedFile.size)}</p>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClearFile}
              disabled={isUploading}
              className="ml-auto"
            >
              <X className="w-4 h-4" />
            </Button>
          </div>
          
          {selectedFile.type.startsWith('image/') && (
            <div className="mt-4">
              <img
                src={URL.createObjectURL(selectedFile)}
                alt="Preview"
                className="max-h-48 mx-auto rounded-lg shadow-sm"
              />
            </div>
          )}
          
          {selectedFile.type === 'application/pdf' && (
            <div className="mt-4 p-4 bg-white rounded-lg">
              <FileText className="w-12 h-12 text-red-500 mx-auto mb-2" />
              <p className="text-sm text-gray-600">PDF file selected</p>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="w-full">
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all duration-200
          ${isDragActive && !isDragReject
            ? 'border-blue-400 bg-blue-50'
            : isDragReject
            ? 'border-red-400 bg-red-50'
            : 'border-gray-300 bg-gray-50 hover:border-gray-400 hover:bg-gray-100'
          }
          ${isUploading ? 'opacity-50 cursor-not-allowed' : ''}
        `}
      >
        <input {...getInputProps()} />
        
        <div className="space-y-4">
          <Upload className={`w-12 h-12 mx-auto ${isDragActive ? 'text-blue-500' : 'text-gray-400'}`} />
          
          <div>
            <p className="text-lg font-medium text-gray-900">
              {isDragActive ? 'Drop your file here' : 'Drag & drop your floor plan here'}
            </p>
            <p className="text-sm text-gray-500 mt-1">
              or click to browse files
            </p>
          </div>
          
          <div className="text-xs text-gray-400 space-y-1">
            <p>Supported formats: {config.upload.supportedExtensions.join(', ')}</p>
            <p>Maximum size: {(config.upload.maxFileSize / (1024 * 1024)).toFixed(0)}MB</p>
          </div>
        </div>
      </div>
      
      {error && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 text-red-500" />
          <span className="text-sm text-red-700">{error}</span>
        </div>
      )}
    </div>
  );
}
