'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import { ArrowLeft, Download, Eye, Settings, Share2, RotateCcw } from 'lucide-react'
import Link from 'next/link'
import ThreeViewer from '@/components/viewer/ThreeViewer'

interface JobStatus {
  id: string
  status: 'processing' | 'completed' | 'failed'
  progress: number
  message: string
  created_at: string
  completed_at?: string
  output_files?: {
    glb?: string
    obj?: string
    stl?: string
    skp?: string
    fbx?: string
  }
  error?: string
}

const processingSteps = [
  'Uploading file...',
  'Analyzing floor plan...',
  'Generating 3D geometry...',
  'Creating room meshes...',
  'Building wall structures...',
  'Optimizing for export...',
  'Finalizing model...'
]

export default function PreviewPage() {
  const params = useParams()
  const jobId = params.jobId as string
  
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedFormat, setSelectedFormat] = useState('glb')
  const [isExporting, setIsExporting] = useState(false)

  // Mock job status for now - will be replaced with real API calls
  useEffect(() => {
    // Simulate API call to get job status
    const fetchJobStatus = async () => {
      try {
        // TODO: Replace with real API call
        // const response = await fetch(`/api/jobs/${jobId}/status`)
        // const data = await response.json()
        
        // Mock data for development
        const mockStatus: JobStatus = {
          id: jobId,
          status: 'completed',
          progress: 100,
          message: 'Model generation completed successfully',
          created_at: new Date().toISOString(),
          completed_at: new Date().toISOString(),
          output_files: {
            glb: '/api/jobs/mock/glb',
            obj: '/api/jobs/mock/obj',
            stl: '/api/jobs/mock/stl',
            skp: '/api/jobs/mock/skp',
            fbx: '/api/jobs/mock/fbx'
          }
        }
        
        setJobStatus(mockStatus)
        setIsLoading(false)
      } catch (err) {
        setError('Failed to load job status')
        setIsLoading(false)
      }
    }

    fetchJobStatus()
  }, [jobId])

  const handleExport = async (format: string) => {
    setIsExporting(true)
    try {
      // TODO: Implement real export functionality
      console.log(`Exporting in ${format} format...`)
      
      // Simulate export delay
      await new Promise(resolve => setTimeout(resolve, 2000))
      
      // Mock download
      const link = document.createElement('a')
      link.href = `#` // Will be replaced with real download URL
      link.download = `floorplan.${format}`
      link.click()
      
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
                {jobStatus.status === 'completed' ? (
                  <ThreeViewer 
                    modelUrl="/api/jobs/mock/glb" // Will be replaced with real model URL
                    onLoadComplete={() => console.log('3D model loaded')}
                  />
                ) : (
                  <div className="flex items-center justify-center h-full">
                    <div className="text-center">
                      <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
                      <p className="text-gray-600 dark:text-gray-300">
                        {jobStatus.message || 'Processing your model...'}
                      </p>
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
                <div>
                  <div className="flex items-center justify-between text-sm mb-2">
                    <span className="text-gray-600 dark:text-gray-300">Progress</span>
                    <span className="text-gray-900 dark:text-white font-medium">
                      {jobStatus.progress}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${jobStatus.progress}%` }}
                    ></div>
                  </div>
                </div>
                
                <div className="text-sm">
                  <p className="text-gray-600 dark:text-gray-300 mb-1">Status</p>
                  <p className="text-gray-900 dark:text-white font-medium">
                    {jobStatus.status === 'completed' ? '✅ Completed' : 
                     jobStatus.status === 'processing' ? '🔄 Processing' : '❌ Failed'}
                  </p>
                </div>
                
                <div className="text-sm">
                  <p className="text-gray-600 dark:text-gray-300 mb-1">Created</p>
                  <p className="text-gray-900 dark:text-white">
                    {new Date(jobStatus.created_at).toLocaleDateString()}
                  </p>
                </div>
                
                {jobStatus.completed_at && (
                  <div className="text-sm">
                    <p className="text-gray-600 dark:text-gray-300 mb-1">Completed</p>
                    <p className="text-gray-900 dark:text-white">
                      {new Date(jobStatus.completed_at).toLocaleDateString()}
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* Export Options */}
            {jobStatus.status === 'completed' && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  Export Model
                </h3>
                
                <div className="space-y-3">
                  {Object.entries(jobStatus.output_files || {}).map(([format, url]) => (
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
                    <span className="text-gray-900 dark:text-white">24' × 32'</span>
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
