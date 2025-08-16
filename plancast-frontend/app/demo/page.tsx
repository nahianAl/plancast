'use client'

import { useState } from 'react'
import Link from 'next/link'
import { ArrowLeft, Play, Pause, RotateCcw, Download, Share2 } from 'lucide-react'
import ThreeViewer from '@/components/viewer/ThreeViewer'

export default function DemoPage() {
  const [isPlaying, setIsPlaying] = useState(false)
  const [showControls, setShowControls] = useState(true)

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Link
                href="/"
                className="inline-flex items-center text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back to Home
              </Link>
              <div className="h-6 w-px bg-gray-300 dark:bg-gray-600"></div>
              <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
                Interactive Demo
              </h1>
            </div>
            
            <div className="flex items-center space-x-3">
              <button className="p-2 text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
                <Share2 className="w-5 h-5" />
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
                    Sample 3D Model
                  </h2>
                  <div className="flex items-center space-x-2">
                    <button 
                      onClick={() => setIsPlaying(!isPlaying)}
                      className="p-2 text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                      title={isPlaying ? 'Pause animation' : 'Play animation'}
                    >
                      {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                    </button>
                    <button className="p-2 text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
                      <RotateCcw className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
              
              <div className="h-96 lg:h-[600px] bg-gray-100 dark:bg-gray-900">
                <ThreeViewer 
                  modelUrl="/api/demo/model" // Will be replaced with real demo model URL
                  onLoadComplete={() => console.log('Demo model loaded')}
                  showGrid={true}
                />
              </div>
            </div>
          </div>

          {/* Sidebar - Demo Info & Features */}
          <div className="space-y-6">
            {/* Demo Information */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Demo Model
              </h3>
              
              <div className="space-y-4">
                <div className="text-sm">
                  <p className="text-gray-600 dark:text-gray-300 mb-1">Model Type</p>
                  <p className="text-gray-900 dark:text-white font-medium">Sample Floor Plan</p>
                </div>
                
                <div className="text-sm">
                  <p className="text-gray-600 dark:text-gray-300 mb-1">Dimensions</p>
                  <p className="text-gray-900 dark:text-white">20' × 30'</p>
                </div>
                
                <div className="text-sm">
                  <p className="text-gray-600 dark:text-gray-300 mb-1">Rooms</p>
                  <p className="text-gray-900 dark:text-white">4 bedrooms, 2 bathrooms</p>
                </div>
                
                <div className="text-sm">
                  <p className="text-gray-600 dark:text-gray-300 mb-1">Features</p>
                  <p className="text-gray-900 dark:text-white">Kitchen, living room, garage</p>
                </div>
              </div>
            </div>

            {/* Interactive Features */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Try These Features
              </h3>
              
              <div className="space-y-3 text-sm">
                <div className="flex items-center space-x-3">
                  <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                  <span className="text-gray-700 dark:text-gray-300">Click and drag to rotate the model</span>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                  <span className="text-gray-700 dark:text-gray-300">Scroll to zoom in/out</span>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                  <span className="text-gray-700 dark:text-gray-300">Right-click and drag to pan</span>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                  <span className="text-gray-700 dark:text-gray-300">Double-click to reset view</span>
                </div>
              </div>
            </div>

            {/* Get Started */}
            <div className="bg-gradient-to-br from-blue-50 to-cyan-50 dark:from-blue-900/20 dark:to-cyan-900/20 rounded-lg p-6 border border-blue-200 dark:border-blue-800">
              <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-100 mb-3">
                Ready to Try Your Own?
              </h3>
              <p className="text-blue-800 dark:text-blue-200 text-sm mb-4">
                Upload your own floor plan and see the magic happen in real-time.
              </p>
              <Link
                href="/convert"
                className="inline-flex items-center w-full justify-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Start Converting Now
              </Link>
            </div>

            {/* Export Options */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Export Formats
              </h3>
              
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 border border-gray-200 dark:border-gray-600 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <Download className="w-4 h-4 text-gray-600 dark:text-gray-300" />
                    <span className="text-gray-900 dark:text-white font-medium">GLB</span>
                  </div>
                  <span className="text-sm text-gray-500 dark:text-gray-400">Web & 3D Apps</span>
                </div>
                
                <div className="flex items-center justify-between p-3 border border-gray-200 dark:border-gray-600 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <Download className="w-4 h-4 text-gray-600 dark:text-gray-300" />
                    <span className="text-gray-900 dark:text-white font-medium">OBJ</span>
                  </div>
                  <span className="text-sm text-gray-500 dark:text-gray-400">3D Printing</span>
                </div>
                
                <div className="flex items-center justify-between p-3 border border-gray-200 dark:border-gray-600 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <Download className="w-4 h-4 text-gray-600 dark:text-gray-300" />
                    <span className="text-gray-900 dark:text-white font-medium">STL</span>
                  </div>
                  <span className="text-sm text-gray-500 dark:text-gray-400">CAD Software</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
