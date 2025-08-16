'use client'

import { useState, useCallback, useRef } from 'react'
import { Upload, FileImage, FileText, AlertCircle, X } from 'lucide-react'

interface FileUploadZoneProps {
  onFileUpload: (file: File) => void
  isUploading?: boolean
  error?: string | null
}

export function FileUploadZone({ onFileUpload, isUploading = false, error }: FileUploadZoneProps) {
  const [isDragOver, setIsDragOver] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
    
    const files = Array.from(e.dataTransfer.files)
    if (files.length > 0) {
      handleFileSelect(files[0])
    }
  }, [])

  const handleFileSelect = useCallback((file: File) => {
    // Validate file type
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'application/pdf']
    if (!allowedTypes.includes(file.type)) {
      return
    }

    // Validate file size (50MB limit)
    if (file.size > 50 * 1024 * 1024) {
      return
    }

    setSelectedFile(file)
  }, [])

  const handleFileInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    if (files.length > 0) {
      handleFileSelect(files[0])
    }
  }, [handleFileSelect])

  const handleUpload = useCallback(() => {
    if (selectedFile) {
      onFileUpload(selectedFile)
    }
  }, [selectedFile, onFileUpload])

  const handleRemoveFile = useCallback(() => {
    setSelectedFile(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }, [])

  const openFileDialog = useCallback(() => {
    fileInputRef.current?.click()
  }, [])

  const getFileIcon = (file: File) => {
    if (file.type.startsWith('image/')) {
      return <FileImage className="w-8 h-8 text-blue-500" />
    }
    return <FileText className="w-8 h-8 text-green-500" />
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  if (selectedFile) {
    return (
      <div className="text-center">
        <div className="mb-6">
          <div className="inline-flex items-center space-x-3 p-4 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
            {getFileIcon(selectedFile)}
            <div className="text-left">
              <p className="font-medium text-green-900 dark:text-green-100">
                {selectedFile.name}
              </p>
              <p className="text-sm text-green-700 dark:text-green-300">
                {formatFileSize(selectedFile.size)} • {selectedFile.type}
              </p>
            </div>
            <button
              onClick={handleRemoveFile}
              className="p-1 hover:bg-green-200 dark:hover:bg-green-800 rounded-full transition-colors"
            >
              <X className="w-4 h-4 text-green-600 dark:text-green-400" />
            </button>
          </div>
        </div>

        <button
          onClick={handleUpload}
          disabled={isUploading}
          className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-blue-600 to-cyan-600 text-white font-semibold rounded-xl hover:from-blue-700 hover:to-cyan-700 transition-all duration-200 shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Upload className="w-5 h-5 mr-2" />
          {isUploading ? 'Uploading...' : 'Upload & Convert'}
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* File Input */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".jpg,.jpeg,.png,.pdf"
        onChange={handleFileInputChange}
        className="hidden"
      />

      {/* Upload Zone */}
      <div
        className={`upload-zone ${isDragOver ? 'drag-over' : ''} ${isUploading ? 'uploading' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <div className="text-center">
          <div className="mx-auto w-16 h-16 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center mb-4">
            <Upload className="w-8 h-8 text-gray-400" />
          </div>
          
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            {isDragOver ? 'Drop your file here' : 'Upload your floor plan'}
          </h3>
          
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            Drag and drop your file here, or{' '}
            <button
              type="button"
              onClick={openFileDialog}
              className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-medium underline"
            >
              browse files
            </button>
          </p>
          
          <div className="text-sm text-gray-500 dark:text-gray-400">
            <p>Supported formats: JPG, PNG, PDF</p>
            <p>Maximum file size: 50MB</p>
          </div>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="flex items-center space-x-2 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
          <span className="text-red-700 dark:text-red-300 text-sm">{error}</span>
        </div>
      )}

      {/* Upload Instructions */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <h4 className="font-medium text-blue-900 dark:text-blue-100 mb-2">
          💡 Tips for best results:
        </h4>
        <ul className="text-sm text-blue-800 dark:text-blue-200 space-y-1">
          <li>• Use high-resolution images (minimum 800x600 pixels)</li>
          <li>• Ensure good lighting and clear contrast</li>
          <li>• Include room labels and dimensions if possible</li>
          <li>• Avoid heavily cluttered or blurry images</li>
        </ul>
      </div>
    </div>
  )
}
