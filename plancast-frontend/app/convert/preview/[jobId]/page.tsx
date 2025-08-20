'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import { ArrowLeft, Download, Eye, Settings, Share2, RotateCcw } from 'lucide-react'
import Link from 'next/link'
import dynamic from 'next/dynamic'
import { useJobStatus } from '@/hooks/useJobStatus'
import { JobStatusIndicator } from '@/components/common/JobStatusIndicator'
import { Progress } from '@/components/ui/progress'


const ThreeViewer = dynamic(() => import('@/components/viewer/ThreeViewer'), {
  ssr: false,
  loading: () => <p>Loading 3D viewer...</p>
})


export default function PreviewPage() {
  const params = useParams()
  const jobId = params.jobId as string
  
  const [selectedFormat] = useState('glb')
  const [isExporting, setIsExporting] = useState(false)
  
  // Use real-time job status hook
  const {
    jobStatus,
    isLoading,
    error,
    isCompleted,

    isProcessing,
    isPending,
    progress,
  } = useJobStatus({
    jobId,
    autoSubscribe: true,
    onComplete: (result) => {
      console.log('Job completed:', result)
    },
    onError: (errorMessage) => {
      console.error('Job failed:', errorMessage)
    },
  })



  type JobResult = {
    model_url?: string;
    formats?: string[];
    output_files?: Record<string, string>;
  };

  const handleExport = async (format: string) => {
    if (!isCompleted || !jobStatus?.result) return
    
    setIsExporting(true)
    try {
      // Prefer exact format URL from backend output_files mapping if available
      const files: Record<string, string> | undefined = (jobStatus.result as JobResult).output_files
      const downloadUrl = (files && files[format]) 
        ? files[format]
        : (jobStatus.result.model_url || '')
      if (!downloadUrl) {
        throw new Error('No download URL available')
      }
      
      console.log(`Exporting in ${format} format from:`, downloadUrl)
      
      // Create download link
      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = `floor-plan-3d.${format}`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      
    } catch (err) {
      console.error('Export failed:', err)
    } finally {
      setIsExporting(false)
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center">
            <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
            <h2 className="mt-4 text-xl font-semibold text-gray-900 dark:text-white">
              Loading your 3D model...
            </h2>
          </div>
        </div>
      </div>
    )
  }

  if (error || !jobStatus) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-red-600 dark:text-red-400 mb-4">
              Error Loading Model
            </h2>
            <p className="text-gray-600 dark:text-gray-300 mb-6">
              {error || 'Failed to load job information'}
            </p>
            <Link
              href="/convert"
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Upload
            </Link>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Link
                href="/convert"
                className="inline-flex items-center text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back to Upload
              </Link>
              <div className="h-6 w-px bg-gray-300 dark:bg-gray-600"></div>
              <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
                Job #{jobId.slice(0, 8)}
              </h1>
            </div>
            
            <div className="flex items-center space-x-3">
              <button className="p-2 text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
                <Share2 className="w-5 h-5" />
              </button>
              <button className="p-2 text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
                <Settings className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* TEMPORARY: Test Pipeline Notice */}
        <div className="mb-6 p-4 bg-orange-50 border border-orange-200 rounded-lg">
          <div className="flex items-center space-x-2">
            <span className="text-orange-600 font-medium">⚠️ Test Pipeline Active</span>
            <span className="text-sm text-orange-600">
              Running simplified pipeline (no coordinate scaling or door/window cutouts)
            </span>
          </div>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* 3D Viewer - Main Content */}
          <div className="lg:col-span-2">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg overflow-hidden">
              <div className="p-4 border-b border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                    3D Model Preview
                  </h2>
                  <div className="flex items-center space-x-2">
                    <button className="p-2 text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
                      <RotateCcw className="w-4 h-4" />
                    </button>
                    <button className="p-2 text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
                      <Eye className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
              
              <div className="h-96 lg:h-[600px] bg-gray-100 dark:bg-gray-900">
                {isCompleted && jobStatus?.result && jobStatus.result.model_url ? (
                  <ThreeViewer 
                    modelUrl={jobStatus.result.model_url}
                    onLoadComplete={() => console.log('3D model loaded')}
                  />
                ) : (
                  <div className="flex items-center justify-center h-full">
                    <div className="text-center space-y-4">
                      <JobStatusIndicator 
                        status={jobStatus?.status || 'pending'}
                        progress={progress}
                        message={jobStatus?.message}
                        size="lg"
                      />
                      {(isProcessing || isPending) && (
                        <div className="max-w-md">
                          <Progress value={progress} className="h-3" />
                          <p className="text-sm text-gray-600 dark:text-gray-300 mt-2">
                            {jobStatus?.message || 'Processing your model...'}
                          </p>
                        </div>
                      )}
                      {isCompleted && (!jobStatus?.result || !jobStatus.result.model_url) && (
                        <div className="max-w-md">
                          <p className="text-sm text-red-600 dark:text-red-400 mt-2">
                            Model URL not available. Please try refreshing the page.
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Sidebar - Job Info & Export Options */}
          <div className="space-y-6">
            {/* Job Status */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Job Status
              </h3>
              
              <div className="space-y-4">
                <JobStatusIndicator 
                  status={jobStatus?.status || 'pending'}
                  progress={progress}
                  message={jobStatus?.message}
                  showProgress={true}
                  size="md"
                />
                
                <div className="text-sm space-y-3 pt-4 border-t border-gray-200 dark:border-gray-600">
                  <div>
                    <p className="text-gray-600 dark:text-gray-300 mb-1">Job ID</p>
                    <p className="text-gray-900 dark:text-white font-mono text-xs">
                      {jobId}
                    </p>
                  </div>
                  
                  <div>
                    <p className="text-gray-600 dark:text-gray-300 mb-1">Created</p>
                    <p className="text-gray-900 dark:text-white">
                      {jobStatus?.createdAt ? new Date(jobStatus.createdAt).toLocaleDateString() : 'Unknown'}
                    </p>
                  </div>
                  
                  {jobStatus?.updatedAt && (
                    <div>
                      <p className="text-gray-600 dark:text-gray-300 mb-1">Last Updated</p>
                      <p className="text-gray-900 dark:text-white">
                        {new Date(jobStatus.updatedAt).toLocaleString()}
                      </p>
                    </div>
                  )}

                  {isCompleted && jobStatus?.result && (
                    <div>
                      <p className="text-gray-600 dark:text-gray-300 mb-1">Processing Time</p>
                      <p className="text-gray-900 dark:text-white">
                        {jobStatus.result.processing_time || 'Unknown'}s
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Export Options */}
            {isCompleted && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  Export Model
                </h3>
                
                <div className="space-y-3">
                  {(jobStatus?.result?.formats || ['glb', 'obj', 'stl']).map((format: string) => (
                    <button
                      key={format}
                      onClick={() => handleExport(format)}
                      disabled={isExporting}
                      className="w-full flex items-center justify-between p-3 border border-gray-200 dark:border-gray-600 rounded-lg hover:border-blue-500 dark:hover:border-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <div className="flex items-center space-x-3">
                        <Download className="w-4 h-4 text-gray-600 dark:text-gray-300" />
                        <span className="text-gray-900 dark:text-white font-medium">
                          {format.toUpperCase()}
                        </span>
                      </div>
                      <span className="text-sm text-gray-500 dark:text-gray-400">
                        {isExporting && selectedFormat === format ? 'Exporting...' : 'Download'}
                      </span>
                    </button>
                  ))}
                </div>
                
                <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                  <p className="text-sm text-blue-800 dark:text-blue-200">
                    💡 <strong>GLB</strong> is recommended for web viewing and 3D applications.
                    <strong>OBJ</strong> and <strong>STL</strong> are great for 3D printing and CAD software.
                  </p>
                </div>
              </div>
            )}

            {/* Model Information */}
            {jobStatus.status === 'completed' && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  Model Information
                </h3>
                
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-300">File Type</span>
                    <span className="text-gray-900 dark:text-white">Floor Plan</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-300">Scale</span>
                    <span className="text-gray-900 dark:text-white">1:100</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-300">Dimensions</span>
                    <span className="text-gray-900 dark:text-white">24&apos; × 32&apos;</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-300">Rooms</span>
                    <span className="text-gray-900 dark:text-white">6</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
