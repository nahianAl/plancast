'use client'

import { useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { Upload, FileImage, FileText, CheckCircle, Loader2 } from 'lucide-react'
import FileUploadZone from '@/components/upload/FileUploadZone'
import { NotificationBanner } from '@/components/common/NotificationBanner'
import { config } from '@/lib/config'

interface UploadedFile {
  file: File
  preview: string
  size: string
  type: string
}

export default function ConvertPage() {
  const router = useRouter()
  const [uploadedFile, setUploadedFile] = useState<UploadedFile | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)

  const startConversion = useCallback(async (file: File) => {
    try {
      console.log('🚀 Starting conversion for file:', file.name, 'Size:', file.size)
      console.log('📡 API URL:', `${config.api.baseUrl}/convert`)
      
      const formData = new FormData()
      formData.append('file', file)
      formData.append('export_formats', 'glb,obj,stl')

      console.log('📤 Sending request to API...')

      // Use the configured API base URL
      const response = await fetch(`${config.api.baseUrl}/convert`, {
        method: 'POST',
        body: formData
      })

      console.log('📥 Response status:', response.status)
      console.log('📥 Response ok:', response.ok)

      if (!response.ok) {
        const errorText = await response.text()
        console.error('❌ API Error:', errorText)
        throw new Error(`Conversion failed: ${response.status} - ${errorText}`)
      }

      const result = await response.json()
      console.log('✅ Conversion started successfully:', result)
      
      // Redirect to preview page
      console.log('🔄 Redirecting to:', `/convert/preview/${result.job_id}`)
      router.push(`/convert/preview/${result.job_id}`)

    } catch (err) {
      console.error('💥 Conversion error:', err)
      setError(`Failed to start conversion: ${err instanceof Error ? err.message : 'Unknown error'}`)
      setIsUploading(false)
    }
  }, [router])

  const handleFileUpload = useCallback(async (file: File) => {
    setError(null)
    setIsUploading(true)
    setUploadProgress(0)

    try {
      // Validate file type
      const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'application/pdf']
      if (!allowedTypes.includes(file.type)) {
        throw new Error('Please upload a JPG, PNG, or PDF file')
      }

      // Validate file size (50MB limit)
      if (file.size > 50 * 1024 * 1024) {
        throw new Error('File size must be less than 50MB')
      }

      // Create preview for images
      let preview = ''
      if (file.type.startsWith('image/')) {
        preview = URL.createObjectURL(file)
      }

      const uploadedFile: UploadedFile = {
        file,
        preview,
        size: formatFileSize(file.size),
        type: file.type
      }

      setUploadedFile(uploadedFile)

      // Simulate upload progress
      for (let i = 0; i <= 100; i += 10) {
        setUploadProgress(i)
        await new Promise(resolve => setTimeout(resolve, 100))
      }

      // Start conversion process
      await startConversion(file)

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
      setIsUploading(false)
      setUploadProgress(0)
    }
  }, [startConversion])

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const resetUpload = () => {
    setUploadedFile(null)
    setIsUploading(false)
    setUploadProgress(0)
    setError(null)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-cyan-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 dark:text-white mb-4">
            Convert Your Floor Plan
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
            Upload your floor plan and our AI will transform it into a stunning 3D model. 
            Support for JPG, PNG, and PDF formats.
          </p>
        </div>

        {/* Notification Banner */}
        <NotificationBanner />

        {/* Upload Zone */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 p-8">
          {!uploadedFile ? (
            <FileUploadZone
              onFileUpload={handleFileUpload}
              isUploading={isUploading}
              error={error}
            />
          ) : (
            <div className="text-center">
              {/* File Preview */}
              <div className="mb-6">
                {uploadedFile.preview ? (
                  <div className="relative inline-block">
                    <img
                      src={uploadedFile.preview}
                      alt="Floor plan preview"
                      className="max-w-full h-64 object-contain rounded-lg border border-gray-200 dark:border-gray-600"
                    />
                    <div className="absolute top-2 right-2 bg-green-500 text-white px-2 py-1 rounded-full text-xs font-medium">
                      <CheckCircle className="w-3 h-3 inline mr-1" />
                      Valid
                    </div>
                  </div>
                ) : (
                  <div className="w-64 h-64 mx-auto bg-gray-100 dark:bg-gray-700 rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-600 flex items-center justify-center">
                    <FileText className="w-16 h-16 text-gray-400" />
                  </div>
                )}
              </div>

              {/* File Info */}
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                  {uploadedFile.file.name}
                </h3>
                <div className="flex items-center justify-center space-x-4 text-sm text-gray-600 dark:text-gray-400">
                  <span>Size: {uploadedFile.size}</span>
                  <span>Type: {uploadedFile.type}</span>
                </div>
              </div>

              {/* Upload Progress */}
              {isUploading && (
                <div className="mb-6">
                  <div className="flex items-center justify-center space-x-2 mb-2">
                    <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
                    <span className="text-gray-700 dark:text-gray-300">
                      {uploadProgress === 100 ? 'Starting conversion...' : 'Uploading...'}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    {uploadProgress}% complete
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                {!isUploading && (
                  <>
                    <button
                      onClick={() => startConversion(uploadedFile.file)}
                      className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-blue-600 to-cyan-600 text-white font-semibold rounded-xl hover:from-blue-700 hover:to-cyan-700 transition-all duration-200 shadow-lg hover:shadow-xl"
                    >
                      <Upload className="w-5 h-5 mr-2" />
                      Start Conversion
                    </button>
                    <button
                      onClick={resetUpload}
                      className="inline-flex items-center px-6 py-3 border-2 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 font-semibold rounded-xl hover:border-blue-500 hover:text-blue-600 dark:hover:border-blue-400 dark:hover:text-blue-400 transition-all duration-200"
                    >
                      Choose Different File
                    </button>
                  </>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Features */}
        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="text-center">
            <div className="w-16 h-16 bg-blue-100 dark:bg-blue-900/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <Upload className="w-8 h-8 text-blue-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              Easy Upload
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Drag and drop your floor plan or click to browse. We support all major formats.
            </p>
          </div>

          <div className="text-center">
            <div className="w-16 h-16 bg-green-100 dark:bg-green-900/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <CheckCircle className="w-8 h-8 text-green-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              AI Processing
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Our advanced AI analyzes your floor plan and generates accurate 3D models.
            </p>
          </div>

          <div className="text-center">
            <div className="w-16 h-16 bg-purple-100 dark:bg-purple-900/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <FileImage className="w-8 h-8 text-purple-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              Multiple Formats
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Export in GLB, OBJ, or STL formats for use in any 3D software.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
